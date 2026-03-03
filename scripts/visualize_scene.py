#!/usr/bin/env python3
"""
场景可视化工具
"""

import argparse
import numpy as np
import matplotlib.pyplot as plt
from mpl_toolkits.mplot3d import Axes3D
from pathlib import Path
import sys

sys.path.append(str(Path(__file__).parent.parent / 'src'))

from models.gaussian_model import GaussianModel


def visualize_gaussians(model_path: str, output_path: str = None):
    """
    可视化高斯点云
    
    Args:
        model_path: 模型路径
        output_path: 输出图像路径（可选）
    """
    # 加载模型
    model = GaussianModel(num_gaussians=100000, sh_degree=3)
    model.load(model_path)
    
    # 获取点云数据
    xyz = model.xyz.detach().cpu().numpy()
    opacity = model.opacity.detach().cpu().numpy().squeeze()
    
    # 过滤低不透明度的点
    visible_mask = opacity > 0.1
    xyz_visible = xyz[visible_mask]
    opacity_visible = opacity[visible_mask]
    
    print(f"Total Gaussians: {len(xyz)}")
    print(f"Visible Gaussians (opacity > 0.1): {len(xyz_visible)}")
    
    # 创建 3D 图
    fig = plt.figure(figsize=(12, 8))
    ax = fig.add_subplot(111, projection='3d')
    
    # 绘制点云
    scatter = ax.scatter(
        xyz_visible[:, 0],
        xyz_visible[:, 1],
        xyz_visible[:, 2],
        c=opacity_visible,
        cmap='viridis',
        s=1,
        alpha=0.6
    )
    
    ax.set_xlabel('X')
    ax.set_ylabel('Y')
    ax.set_zlabel('Z')
    ax.set_title(f'Gaussian Point Cloud ({len(xyz_visible)} points)')
    
    plt.colorbar(scatter, label='Opacity')
    
    if output_path:
        plt.savefig(output_path, dpi=150, bbox_inches='tight')
        print(f"Saved visualization to {output_path}")
    else:
        plt.show()


def main():
    parser = argparse.ArgumentParser(description='Visualize Gaussian scene')
    parser.add_argument('--model', type=str, required=True, help='Path to model file')
    parser.add_argument('--output', type=str, help='Output image path')
    args = parser.parse_args()
    
    visualize_gaussians(args.model, args.output)


if __name__ == '__main__':
    main()
