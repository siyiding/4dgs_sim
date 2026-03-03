"""
轨迹编辑器 - 用于编辑动态物体的运动轨迹
"""

import torch
import numpy as np
from typing import List, Tuple, Optional
from scipy.interpolate import CubicSpline


class TrajectoryEditor:
    """轨迹编辑器"""
    
    def __init__(self, gaussian_model, deformation_network=None):
        """
        Args:
            gaussian_model: GaussianModel 实例（4D）
            deformation_network: DeformationNetwork 实例（可选）
        """
        self.model = gaussian_model
        self.deformation_net = deformation_network
        
        if not self.model.use_4d:
            raise ValueError("TrajectoryEditor requires 4D Gaussian Model")
    
    def set_linear_trajectory(
        self,
        selection_mask: torch.Tensor,
        start_pos: np.ndarray,
        end_pos: np.ndarray,
        start_time: float = 0.0,
        end_time: float = 1.0
    ):
        """
        设置线性轨迹
        
        Args:
            selection_mask: 选中的高斯点掩码
            start_pos: [3] 起始位置
            end_pos: [3] 结束位置
            start_time: 起始时间
            end_time: 结束时间
        """
        # 计算速度
        velocity = (end_pos - start_pos) / (end_time - start_time)
        
        # 更新选中点的速度
        velocity_tensor = torch.from_numpy(velocity).float().to(self.model._velocity.device)
        self.model._velocity.data[selection_mask] = velocity_tensor
        
        # 更新时间偏移
        self.model._time_offset.data[selection_mask] = start_time
        
        # 更新初始位置
        start_pos_tensor = torch.from_numpy(start_pos).float().to(self.model._xyz.device)
        self.model._xyz.data[selection_mask] = start_pos_tensor
    
    def set_bezier_trajectory(
        self,
        selection_mask: torch.Tensor,
        control_points: List[np.ndarray],
        time_points: List[float]
    ):
        """
        设置贝塞尔曲线轨迹
        
        Args:
            selection_mask: 选中的高斯点掩码
            control_points: 控制点列表 [[3], [3], ...]
            time_points: 时间点列表
        """
        if len(control_points) != len(time_points):
            raise ValueError("control_points and time_points must have same length")
        
        # 使用三次样条插值
        control_points = np.array(control_points)
        time_points = np.array(time_points)
        
        # 为每个维度创建样条
        splines = [
            CubicSpline(time_points, control_points[:, i])
            for i in range(3)
        ]
        
        # 计算初始速度（在 t=0 处的导数）
        velocity = np.array([spline.derivative()(time_points[0]) for spline in splines])
        
        # 更新模型参数
        velocity_tensor = torch.from_numpy(velocity).float().to(self.model._velocity.device)
        self.model._velocity.data[selection_mask] = velocity_tensor
        
        start_pos_tensor = torch.from_numpy(control_points[0]).float().to(self.model._xyz.device)
        self.model._xyz.data[selection_mask] = start_pos_tensor
        
        self.model._time_offset.data[selection_mask] = time_points[0]
    
    def set_circular_trajectory(
        self,
        selection_mask: torch.Tensor,
        center: np.ndarray,
        radius: float,
        angular_velocity: float,
        axis: np.ndarray = np.array([0, 1, 0]),
        start_angle: float = 0.0
    ):
        """
        设置圆周运动轨迹
        
        Args:
            selection_mask: 选中的高斯点掩码
            center: [3] 圆心
            radius: 半径
            angular_velocity: 角速度（弧度/秒）
            axis: [3] 旋转轴
            start_angle: 起始角度
        """
        # 归一化旋转轴
        axis = axis / np.linalg.norm(axis)
        
        # 计算初始位置（在圆周上）
        # 选择一个垂直于旋转轴的向量
        if abs(axis[0]) < 0.9:
            perp = np.cross(axis, np.array([1, 0, 0]))
        else:
            perp = np.cross(axis, np.array([0, 1, 0]))
        perp = perp / np.linalg.norm(perp)
        
        # 旋转到起始角度
        cos_a = np.cos(start_angle)
        sin_a = np.sin(start_angle)
        start_offset = radius * (cos_a * perp + sin_a * np.cross(axis, perp))
        start_pos = center + start_offset
        
        # 初始速度（切向）
        velocity = angular_velocity * radius * np.cross(axis, start_offset / radius)
        
        # 更新模型参数
        start_pos_tensor = torch.from_numpy(start_pos).float().to(self.model._xyz.device)
        velocity_tensor = torch.from_numpy(velocity).float().to(self.model._velocity.device)
        
        self.model._xyz.data[selection_mask] = start_pos_tensor
        self.model._velocity.data[selection_mask] = velocity_tensor
        self.model._time_offset.data[selection_mask] = 0.0
    
    def modify_speed(
        self,
        selection_mask: torch.Tensor,
        speed_factor: float
    ):
        """
        修改运动速度
        
        Args:
            selection_mask: 选中的高斯点掩码
            speed_factor: 速度缩放因子
        """
        self.model._velocity.data[selection_mask] *= speed_factor
    
    def reverse_trajectory(self, selection_mask: torch.Tensor):
        """反转轨迹方向"""
        self.model._velocity.data[selection_mask] *= -1
    
    def get_trajectory_at_time(
        self,
        selection_mask: torch.Tensor,
        time: float
    ) -> np.ndarray:
        """
        获取指定时间的位置
        
        Args:
            selection_mask: 选中的高斯点掩码
            time: 时间
            
        Returns:
            positions: [N, 3] 位置
        """
        xyz = self.model.xyz[selection_mask]
        velocity = self.model._velocity[selection_mask]
        time_offset = self.model._time_offset[selection_mask]
        
        # 线性运动模型
        positions = xyz + velocity * (time - time_offset)
        
        return positions.detach().cpu().numpy()
    
    def visualize_trajectory(
        self,
        selection_mask: torch.Tensor,
        num_samples: int = 100,
        time_range: Tuple[float, float] = (0.0, 1.0)
    ) -> np.ndarray:
        """
        可视化轨迹
        
        Args:
            selection_mask: 选中的高斯点掩码
            num_samples: 采样点数
            time_range: 时间范围
            
        Returns:
            trajectory: [num_samples, N, 3] 轨迹点
        """
        times = np.linspace(time_range[0], time_range[1], num_samples)
        trajectory = []
        
        for t in times:
            positions = self.get_trajectory_at_time(selection_mask, t)
            trajectory.append(positions)
        
        return np.array(trajectory)
    
    def apply_physics_constraints(
        self,
        selection_mask: torch.Tensor,
        ground_height: float = 0.0,
        gravity: float = -9.8
    ):
        """
        应用物理约束（如重力、地面碰撞）
        
        Args:
            selection_mask: 选中的高斯点掩码
            ground_height: 地面高度
            gravity: 重力加速度
        """
        xyz = self.model.xyz[selection_mask]
        velocity = self.model._velocity[selection_mask]
        
        # 检查是否在地面以下
        below_ground = xyz[:, 1] < ground_height
        
        if below_ground.any():
            # 将位置限制在地面以上
            xyz[below_ground, 1] = ground_height
            
            # 反弹或停止垂直速度
            velocity[below_ground, 1] = torch.abs(velocity[below_ground, 1]) * 0.5  # 弹性系数 0.5
            
            # 更新模型
            self.model._xyz.data[selection_mask] = xyz
            self.model._velocity.data[selection_mask] = velocity
