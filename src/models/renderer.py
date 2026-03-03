"""
高斯点云渲染器
"""

import torch
import torch.nn as nn
import numpy as np
from typing import Dict, Optional


class GaussianRenderer(nn.Module):
    """高斯点云渲染器（简化版，实际需要 CUDA 实现）"""
    
    def __init__(
        self,
        image_size: tuple = (800, 600),
        background_color: tuple = (0, 0, 0)
    ):
        """
        Args:
            image_size: 图像尺寸 (width, height)
            background_color: 背景颜色 RGB
        """
        super().__init__()
        
        self.width, self.height = image_size
        self.background_color = torch.tensor(background_color, dtype=torch.float32)
    
    def forward(
        self,
        xyz: torch.Tensor,
        rotation: torch.Tensor,
        scaling: torch.Tensor,
        opacity: torch.Tensor,
        features: torch.Tensor,
        camera_intrinsics: torch.Tensor,
        camera_extrinsics: torch.Tensor
    ) -> Dict[str, torch.Tensor]:
        """
        渲染高斯点云
        
        Args:
            xyz: [N, 3] 高斯点位置
            rotation: [N, 4] 旋转（四元数）
            scaling: [N, 3] 缩放
            opacity: [N, 1] 不透明度
            features: [N, K, 3] 球谐特征
            camera_intrinsics: [3, 3] 相机内参
            camera_extrinsics: [4, 4] 相机外参
            
        Returns:
            dict: {
                'image': [3, H, W] 渲染图像
                'depth': [1, H, W] 深度图
                'alpha': [1, H, W] Alpha 通道
            }
        """
        device = xyz.device
        
        # 投影到相机坐标系
        xyz_cam = self.world_to_camera(xyz, camera_extrinsics)
        
        # 投影到图像平面
        xyz_screen = self.camera_to_screen(xyz_cam, camera_intrinsics)
        
        # 深度
        depths = xyz_cam[:, 2]
        
        # 过滤视锥外的点
        valid_mask = (
            (xyz_screen[:, 0] >= 0) & (xyz_screen[:, 0] < self.width) &
            (xyz_screen[:, 1] >= 0) & (xyz_screen[:, 1] < self.height) &
            (depths > 0)
        )
        
        if valid_mask.sum() == 0:
            # 返回背景
            bg = self.background_color.to(device).view(3, 1, 1).expand(3, self.height, self.width)
            return {
                'image': bg,
                'depth': torch.zeros(1, self.height, self.width, device=device),
                'alpha': torch.zeros(1, self.height, self.width, device=device)
            }
        
        # 简化渲染：使用 splatting
        # 注意：实际实现需要 CUDA 加速的可微分光栅化
        image = self.splat_gaussians(
            xyz_screen[valid_mask],
            depths[valid_mask],
            opacity[valid_mask],
            features[valid_mask, 0, :],  # 使用 DC 分量
            scaling[valid_mask],
            rotation[valid_mask]
        )
        
        return image
    
    def world_to_camera(
        self,
        xyz: torch.Tensor,
        extrinsics: torch.Tensor
    ) -> torch.Tensor:
        """世界坐标转相机坐标"""
        # 齐次坐标
        xyz_homo = torch.cat([xyz, torch.ones_like(xyz[:, :1])], dim=-1)
        
        # 变换
        T_inv = torch.inverse(extrinsics)
        xyz_cam = (T_inv @ xyz_homo.T).T[:, :3]
        
        return xyz_cam
    
    def camera_to_screen(
        self,
        xyz_cam: torch.Tensor,
        intrinsics: torch.Tensor
    ) -> torch.Tensor:
        """相机坐标转屏幕坐标"""
        # 投影
        xyz_screen = (intrinsics @ xyz_cam.T).T
        
        # 归一化
        xyz_screen = xyz_screen[:, :2] / xyz_screen[:, 2:3]
        
        return xyz_screen
    
    def splat_gaussians(
        self,
        positions: torch.Tensor,
        depths: torch.Tensor,
        opacities: torch.Tensor,
        colors: torch.Tensor,
        scalings: torch.Tensor,
        rotations: torch.Tensor
    ) -> Dict[str, torch.Tensor]:
        """
        Splat 高斯点到图像
        
        注意：这是简化实现，实际需要 CUDA 加速
        """
        device = positions.device
        
        # 初始化图像
        image = self.background_color.to(device).view(3, 1, 1).expand(3, self.height, self.width).clone()
        depth_map = torch.zeros(1, self.height, self.width, device=device)
        alpha_map = torch.zeros(1, self.height, self.width, device=device)
        
        # 按深度排序
        sorted_indices = torch.argsort(depths, descending=True)
        
        # Splat 每个高斯点
        for idx in sorted_indices:
            pos = positions[idx]
            depth = depths[idx]
            opacity = opacities[idx]
            color = colors[idx]
            
            # 简化：使用固定半径的圆形 splat
            radius = 3
            x, y = int(pos[0].item()), int(pos[1].item())
            
            for dy in range(-radius, radius + 1):
                for dx in range(-radius, radius + 1):
                    px, py = x + dx, y + dy
                    
                    if 0 <= px < self.width and 0 <= py < self.height:
                        # 高斯权重
                        dist = (dx ** 2 + dy ** 2) ** 0.5
                        weight = torch.exp(torch.tensor(-dist ** 2 / 2.0, device=device))
                        alpha = opacity * weight
                        
                        # Alpha 混合
                        current_alpha = alpha_map[0, py, px]
                        image[:, py, px] = image[:, py, px] * (1 - alpha) + color * alpha
                        alpha_map[0, py, px] = current_alpha + alpha * (1 - current_alpha)
                        
                        if depth_map[0, py, px] == 0 or depth < depth_map[0, py, px]:
                            depth_map[0, py, px] = depth
        
        return {
            'image': image,
            'depth': depth_map,
            'alpha': alpha_map
        }
