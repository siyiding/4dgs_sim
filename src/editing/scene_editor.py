"""
场景编辑器 - 支持物体选择、移动、删除、复制
"""

import torch
import numpy as np
from typing import List, Tuple, Optional, Dict
from pathlib import Path


class SceneEditor:
    """场景编辑器"""
    
    def __init__(self, gaussian_model):
        """
        Args:
            gaussian_model: GaussianModel 实例
        """
        self.model = gaussian_model
        self.selection_mask = None
        self.undo_stack = []
        self.max_undo = 10
        
    def select_by_bbox(
        self,
        bbox_min: np.ndarray,
        bbox_max: np.ndarray
    ) -> int:
        """
        通过边界框选择高斯点
        
        Args:
            bbox_min: [3] 边界框最小坐标
            bbox_max: [3] 边界框最大坐标
            
        Returns:
            选中的点数量
        """
        xyz = self.model.xyz.detach().cpu().numpy()
        
        # 检查每个点是否在边界框内
        in_bbox = np.all(
            (xyz >= bbox_min) & (xyz <= bbox_max),
            axis=1
        )
        
        self.selection_mask = torch.from_numpy(in_bbox).to(self.model.xyz.device)
        
        return self.selection_mask.sum().item()
    
    def select_by_sphere(
        self,
        center: np.ndarray,
        radius: float
    ) -> int:
        """
        通过球体选择高斯点
        
        Args:
            center: [3] 球心坐标
            radius: 半径
            
        Returns:
            选中的点数量
        """
        xyz = self.model.xyz.detach().cpu().numpy()
        
        # 计算距离
        distances = np.linalg.norm(xyz - center, axis=1)
        in_sphere = distances <= radius
        
        self.selection_mask = torch.from_numpy(in_sphere).to(self.model.xyz.device)
        
        return self.selection_mask.sum().item()
    
    def select_by_semantic(
        self,
        semantic_labels: torch.Tensor,
        target_label: int
    ) -> int:
        """
        通过语义标签选择高斯点
        
        Args:
            semantic_labels: [N] 语义标签
            target_label: 目标标签
            
        Returns:
            选中的点数量
        """
        self.selection_mask = (semantic_labels == target_label)
        return self.selection_mask.sum().item()
    
    def move_selection(
        self,
        offset: np.ndarray,
        save_undo: bool = True
    ):
        """
        移动选中的高斯点
        
        Args:
            offset: [3] 位移向量
            save_undo: 是否保存到撤销栈
        """
        if self.selection_mask is None or self.selection_mask.sum() == 0:
            print("No selection to move")
            return
        
        # 保存撤销信息
        if save_undo:
            self._save_undo()
        
        # 应用位移
        offset_tensor = torch.from_numpy(offset).float().to(self.model.xyz.device)
        self.model._xyz.data[self.selection_mask] += offset_tensor
    
    def rotate_selection(
        self,
        axis: np.ndarray,
        angle: float,
        center: Optional[np.ndarray] = None,
        save_undo: bool = True
    ):
        """
        旋转选中的高斯点
        
        Args:
            axis: [3] 旋转轴（单位向量）
            angle: 旋转角度（弧度）
            center: [3] 旋转中心，默认为选中点的中心
            save_undo: 是否保存到撤销栈
        """
        if self.selection_mask is None or self.selection_mask.sum() == 0:
            print("No selection to rotate")
            return
        
        if save_undo:
            self._save_undo()
        
        # 计算旋转中心
        if center is None:
            center = self.model.xyz[self.selection_mask].mean(dim=0).cpu().numpy()
        
        # 构建旋转矩阵（Rodrigues 公式）
        axis = axis / np.linalg.norm(axis)
        K = np.array([
            [0, -axis[2], axis[1]],
            [axis[2], 0, -axis[0]],
            [-axis[1], axis[0], 0]
        ])
        R = np.eye(3) + np.sin(angle) * K + (1 - np.cos(angle)) * (K @ K)
        
        # 应用旋转
        xyz = self.model.xyz[self.selection_mask].detach().cpu().numpy()
        xyz_centered = xyz - center
        xyz_rotated = (R @ xyz_centered.T).T + center
        
        self.model._xyz.data[self.selection_mask] = torch.from_numpy(xyz_rotated).float().to(self.model.xyz.device)
    
    def scale_selection(
        self,
        scale_factor: float,
        center: Optional[np.ndarray] = None,
        save_undo: bool = True
    ):
        """
        缩放选中的高斯点
        
        Args:
            scale_factor: 缩放因子
            center: [3] 缩放中心
            save_undo: 是否保存到撤销栈
        """
        if self.selection_mask is None or self.selection_mask.sum() == 0:
            print("No selection to scale")
            return
        
        if save_undo:
            self._save_undo()
        
        # 计算缩放中心
        if center is None:
            center = self.model.xyz[self.selection_mask].mean(dim=0).cpu().numpy()
        
        # 应用缩放
        xyz = self.model.xyz[self.selection_mask].detach().cpu().numpy()
        xyz_centered = xyz - center
        xyz_scaled = xyz_centered * scale_factor + center
        
        self.model._xyz.data[self.selection_mask] = torch.from_numpy(xyz_scaled).float().to(self.model.xyz.device)
        
        # 同时缩放高斯点的尺寸
        self.model._scaling.data[self.selection_mask] += np.log(scale_factor)
    
    def delete_selection(self, save_undo: bool = True):
        """删除选中的高斯点"""
        if self.selection_mask is None or self.selection_mask.sum() == 0:
            print("No selection to delete")
            return
        
        if save_undo:
            self._save_undo()
        
        # 保留未选中的点
        keep_mask = ~self.selection_mask
        
        self.model._xyz = torch.nn.Parameter(self.model._xyz[keep_mask])
        self.model._rotation = torch.nn.Parameter(self.model._rotation[keep_mask])
        self.model._scaling = torch.nn.Parameter(self.model._scaling[keep_mask])
        self.model._opacity = torch.nn.Parameter(self.model._opacity[keep_mask])
        self.model._features_dc = torch.nn.Parameter(self.model._features_dc[keep_mask])
        self.model._features_rest = torch.nn.Parameter(self.model._features_rest[keep_mask])
        
        if self.model.use_4d:
            self.model._time_offset = torch.nn.Parameter(self.model._time_offset[keep_mask])
            self.model._velocity = torch.nn.Parameter(self.model._velocity[keep_mask])
        
        self.model.num_gaussians = self.model._xyz.shape[0]
        self.selection_mask = None
    
    def duplicate_selection(
        self,
        offset: np.ndarray,
        save_undo: bool = True
    ):
        """
        复制选中的高斯点
        
        Args:
            offset: [3] 复制偏移
            save_undo: 是否保存到撤销栈
        """
        if self.selection_mask is None or self.selection_mask.sum() == 0:
            print("No selection to duplicate")
            return
        
        if save_undo:
            self._save_undo()
        
        # 复制选中的点
        xyz_dup = self.model._xyz[self.selection_mask].clone()
        rotation_dup = self.model._rotation[self.selection_mask].clone()
        scaling_dup = self.model._scaling[self.selection_mask].clone()
        opacity_dup = self.model._opacity[self.selection_mask].clone()
        features_dc_dup = self.model._features_dc[self.selection_mask].clone()
        features_rest_dup = self.model._features_rest[self.selection_mask].clone()
        
        # 应用偏移
        offset_tensor = torch.from_numpy(offset).float().to(self.model.xyz.device)
        xyz_dup += offset_tensor
        
        # 添加到模型
        self.model._xyz = torch.nn.Parameter(torch.cat([self.model._xyz, xyz_dup], dim=0))
        self.model._rotation = torch.nn.Parameter(torch.cat([self.model._rotation, rotation_dup], dim=0))
        self.model._scaling = torch.nn.Parameter(torch.cat([self.model._scaling, scaling_dup], dim=0))
        self.model._opacity = torch.nn.Parameter(torch.cat([self.model._opacity, opacity_dup], dim=0))
        self.model._features_dc = torch.nn.Parameter(torch.cat([self.model._features_dc, features_dc_dup], dim=0))
        self.model._features_rest = torch.nn.Parameter(torch.cat([self.model._features_rest, features_rest_dup], dim=0))
        
        if self.model.use_4d:
            time_offset_dup = self.model._time_offset[self.selection_mask].clone()
            velocity_dup = self.model._velocity[self.selection_mask].clone()
            self.model._time_offset = torch.nn.Parameter(torch.cat([self.model._time_offset, time_offset_dup], dim=0))
            self.model._velocity = torch.nn.Parameter(torch.cat([self.model._velocity, velocity_dup], dim=0))
        
        self.model.num_gaussians = self.model._xyz.shape[0]
    
    def clear_selection(self):
        """清除选择"""
        self.selection_mask = None
    
    def _save_undo(self):
        """保存当前状态到撤销栈"""
        state = {
            'xyz': self.model._xyz.data.clone(),
            'rotation': self.model._rotation.data.clone(),
            'scaling': self.model._scaling.data.clone(),
            'opacity': self.model._opacity.data.clone(),
            'features_dc': self.model._features_dc.data.clone(),
            'features_rest': self.model._features_rest.data.clone(),
            'num_gaussians': self.model.num_gaussians
        }
        
        if self.model.use_4d:
            state['time_offset'] = self.model._time_offset.data.clone()
            state['velocity'] = self.model._velocity.data.clone()
        
        self.undo_stack.append(state)
        
        # 限制撤销栈大小
        if len(self.undo_stack) > self.max_undo:
            self.undo_stack.pop(0)
    
    def undo(self):
        """撤销上一次操作"""
        if len(self.undo_stack) == 0:
            print("Nothing to undo")
            return
        
        state = self.undo_stack.pop()
        
        self.model._xyz = torch.nn.Parameter(state['xyz'])
        self.model._rotation = torch.nn.Parameter(state['rotation'])
        self.model._scaling = torch.nn.Parameter(state['scaling'])
        self.model._opacity = torch.nn.Parameter(state['opacity'])
        self.model._features_dc = torch.nn.Parameter(state['features_dc'])
        self.model._features_rest = torch.nn.Parameter(state['features_rest'])
        self.model.num_gaussians = state['num_gaussians']
        
        if self.model.use_4d:
            self.model._time_offset = torch.nn.Parameter(state['time_offset'])
            self.model._velocity = torch.nn.Parameter(state['velocity'])
    
    def get_selection_info(self) -> Dict:
        """获取选择信息"""
        if self.selection_mask is None:
            return {'count': 0}
        
        count = self.selection_mask.sum().item()
        if count == 0:
            return {'count': 0}
        
        xyz = self.model.xyz[self.selection_mask].detach().cpu().numpy()
        
        return {
            'count': count,
            'center': xyz.mean(axis=0),
            'bbox_min': xyz.min(axis=0),
            'bbox_max': xyz.max(axis=0)
        }
