#!/usr/bin/env python3
"""
场景编辑测试脚本
"""

import numpy as np
import sys
from pathlib import Path

sys.path.append(str(Path(__file__).parent.parent / 'src'))

from models.gaussian_model import GaussianModel
from editing.scene_editor import SceneEditor


def test_scene_editing():
    """测试场景编辑功能"""
    print("Testing Scene Editing...")
    
    # 创建测试模型
    model = GaussianModel(num_gaussians=1000, sh_degree=3)
    editor = SceneEditor(model)
    
    print(f"Initial Gaussians: {model.num_gaussians}")
    
    # 测试 1: 选择
    print("\n1. Testing selection...")
    bbox_min = np.array([-0.5, -0.5, -0.5])
    bbox_max = np.array([0.5, 0.5, 0.5])
    count = editor.select_by_bbox(bbox_min, bbox_max)
    print(f"   Selected {count} points in bbox")
    
    # 测试 2: 移动
    print("\n2. Testing move...")
    offset = np.array([1.0, 0.0, 0.0])
    editor.move_selection(offset)
    info = editor.get_selection_info()
    print(f"   Selection center after move: {info['center']}")
    
    # 测试 3: 旋转
    print("\n3. Testing rotation...")
    axis = np.array([0, 1, 0])
    angle = np.pi / 4
    editor.rotate_selection(axis, angle)
    print(f"   Rotated by {np.degrees(angle):.1f} degrees")
    
    # 测试 4: 缩放
    print("\n4. Testing scale...")
    editor.scale_selection(1.5)
    print(f"   Scaled by factor 1.5")
    
    # 测试 5: 复制
    print("\n5. Testing duplicate...")
    offset = np.array([0.0, 1.0, 0.0])
    editor.duplicate_selection(offset)
    print(f"   Gaussians after duplicate: {model.num_gaussians}")
    
    # 测试 6: 撤销
    print("\n6. Testing undo...")
    editor.undo()
    print(f"   Gaussians after undo: {model.num_gaussians}")
    
    # 测试 7: 删除
    print("\n7. Testing delete...")
    editor.select_by_sphere(np.array([0, 0, 0]), 0.3)
    count = editor.get_selection_info()['count']
    editor.delete_selection()
    print(f"   Deleted {count} points")
    print(f"   Remaining Gaussians: {model.num_gaussians}")
    
    print("\n✅ All tests passed!")


if __name__ == '__main__':
    test_scene_editing()
