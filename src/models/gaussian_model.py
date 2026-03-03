"""
3D/4D Gaussian Splatting 模型
"""

import torch
import torch.nn as nn
import numpy as np
from typing import Dict, Optional, Tuple


class GaussianModel(nn.Module):
    """3D Gaussian Splatting 模型"""
    
    def __init__(
        self,
        num_gaussians: int = 100000,
        sh_degree: int = 3,
        use_4d: bool = False
    ):
        """
        Args:
            num_gaussians: 高斯点数量
            sh_degree: 球谐函数阶数
            use_4d: 是否使用 4D（时序）扩展
        """
        super().__init__()
        
        self.num_gaussians = num_gaussians
        self.sh_degree = sh_degree
        self.use_4d = use_4d
        
        # 高斯点属性
        self._xyz = nn.Parameter(torch.zeros(num_gaussians, 3))  # 位置
        self._rotation = nn.Parameter(torch.zeros(num_gaussians, 4))  # 旋转（四元数）
        self._scaling = nn.Parameter(torch.zeros(num_gaussians, 3))  # 缩放
        self._opacity = nn.Parameter(torch.zeros(num_gaussians, 1))  # 不透明度
        
        # 球谐系数（用于颜色）
        num_sh_coeffs = (sh_degree + 1) ** 2
        self._features_dc = nn.Parameter(torch.zeros(num_gaussians, 1, 3))  # DC 分量
        self._features_rest = nn.Parameter(torch.zeros(num_gaussians, num_sh_coeffs - 1, 3))  # 其他分量
        
        # 4D 扩展：时间相关属性
        if use_4d:
            self._time_offset = nn.Parameter(torch.zeros(num_gaussians, 1))
            self._velocity = nn.Parameter(torch.zeros(num_gaussians, 3))
        
        self._initialize_parameters()
    
    def _initialize_parameters(self):
        """初始化参数"""
        # 位置：随机初始化在单位球内
        self._xyz.data.uniform_(-1, 1)
        
        # 旋转：初始化为单位四元数
        self._rotation.data[:, 0] = 1.0
        
        # 缩放：初始化为小值
        self._scaling.data.fill_(-2.0)  # log scale
        
        # 不透明度：初始化为中等值
        self._opacity.data.fill_(0.1)
        
        # 颜色：初始化为灰色
        self._features_dc.data.fill_(0.5)
    
    @property
    def xyz(self) -> torch.Tensor:
        """获取位置"""
        return self._xyz
    
    @property
    def rotation(self) -> torch.Tensor:
        """获取旋转（归一化后的四元数）"""
        return torch.nn.functional.normalize(self._rotation, dim=-1)
    
    @property
    def scaling(self) -> torch.Tensor:
        """获取缩放（指数化）"""
        return torch.exp(self._scaling)
    
    @property
    def opacity(self) -> torch.Tensor:
        """获取不透明度（sigmoid）"""
        return torch.sigmoid(self._opacity)
    
    @property
    def features(self) -> torch.Tensor:
        """获取球谐特征"""
        return torch.cat([self._features_dc, self._features_rest], dim=1)
    
    def get_xyz_at_time(self, time: float) -> torch.Tensor:
        """
        获取指定时间的位置（4D）
        
        Args:
            time: 时间戳
            
        Returns:
            xyz: [N, 3] 位置
        """
        if not self.use_4d:
            return self.xyz
        
        # 线性运动模型
        xyz = self.xyz + self._velocity * (time - self._time_offset)
        return xyz
    
    def densify(self, grad_threshold: float = 0.0002):
        """
        根据梯度密集化高斯点
        
        Args:
            grad_threshold: 梯度阈值
        """
        # 计算位置梯度
        if self._xyz.grad is None:
            return
        
        grads = torch.norm(self._xyz.grad, dim=-1)
        
        # 选择需要分裂的点
        split_mask = grads > grad_threshold
        
        if split_mask.sum() == 0:
            return
        
        # 分裂高斯点
        new_xyz = self._xyz[split_mask] + torch.randn_like(self._xyz[split_mask]) * 0.01
        new_rotation = self._rotation[split_mask]
        new_scaling = self._scaling[split_mask] - 0.5  # 缩小
        new_opacity = self._opacity[split_mask]
        new_features_dc = self._features_dc[split_mask]
        new_features_rest = self._features_rest[split_mask]
        
        # 添加新点
        self._xyz = nn.Parameter(torch.cat([self._xyz, new_xyz], dim=0))
        self._rotation = nn.Parameter(torch.cat([self._rotation, new_rotation], dim=0))
        self._scaling = nn.Parameter(torch.cat([self._scaling, new_scaling], dim=0))
        self._opacity = nn.Parameter(torch.cat([self._opacity, new_opacity], dim=0))
        self._features_dc = nn.Parameter(torch.cat([self._features_dc, new_features_dc], dim=0))
        self._features_rest = nn.Parameter(torch.cat([self._features_rest, new_features_rest], dim=0))
        
        self.num_gaussians = self._xyz.shape[0]
    
    def prune(self, opacity_threshold: float = 0.005):
        """
        剪枝低不透明度的高斯点
        
        Args:
            opacity_threshold: 不透明度阈值
        """
        opacity = self.opacity.squeeze()
        keep_mask = opacity > opacity_threshold
        
        if keep_mask.sum() == 0:
            return
        
        self._xyz = nn.Parameter(self._xyz[keep_mask])
        self._rotation = nn.Parameter(self._rotation[keep_mask])
        self._scaling = nn.Parameter(self._scaling[keep_mask])
        self._opacity = nn.Parameter(self._opacity[keep_mask])
        self._features_dc = nn.Parameter(self._features_dc[keep_mask])
        self._features_rest = nn.Parameter(self._features_rest[keep_mask])
        
        if self.use_4d:
            self._time_offset = nn.Parameter(self._time_offset[keep_mask])
            self._velocity = nn.Parameter(self._velocity[keep_mask])
        
        self.num_gaussians = self._xyz.shape[0]
    
    def save(self, path: str):
        """保存模型"""
        state = {
            'num_gaussians': self.num_gaussians,
            'sh_degree': self.sh_degree,
            'use_4d': self.use_4d,
            'xyz': self._xyz.data.cpu(),
            'rotation': self._rotation.data.cpu(),
            'scaling': self._scaling.data.cpu(),
            'opacity': self._opacity.data.cpu(),
            'features_dc': self._features_dc.data.cpu(),
            'features_rest': self._features_rest.data.cpu()
        }
        
        if self.use_4d:
            state['time_offset'] = self._time_offset.data.cpu()
            state['velocity'] = self._velocity.data.cpu()
        
        torch.save(state, path)
    
    def load(self, path: str):
        """加载模型"""
        state = torch.load(path)
        
        self.num_gaussians = state['num_gaussians']
        self.sh_degree = state['sh_degree']
        self.use_4d = state['use_4d']
        
        self._xyz = nn.Parameter(state['xyz'])
        self._rotation = nn.Parameter(state['rotation'])
        self._scaling = nn.Parameter(state['scaling'])
        self._opacity = nn.Parameter(state['opacity'])
        self._features_dc = nn.Parameter(state['features_dc'])
        self._features_rest = nn.Parameter(state['features_rest'])
        
        if self.use_4d:
            self._time_offset = nn.Parameter(state['time_offset'])
            self._velocity = nn.Parameter(state['velocity'])
