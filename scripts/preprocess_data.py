#!/usr/bin/env python3
"""
数据预处理脚本
"""

import argparse
from pathlib import Path
import sys

sys.path.append(str(Path(__file__).parent.parent / 'src'))

from data.dataset import create_dataset
from data.preprocessor import DataPreprocessor


def main():
    parser = argparse.ArgumentParser(description='Preprocess dataset')
    parser.add_argument('--dataset', type=str, required=True, choices=['kitti', 'nuscenes'])
    parser.add_argument('--data_root', type=str, required=True)
    parser.add_argument('--scene', type=str, required=True)
    parser.add_argument('--output', type=str, default='./data/preprocessed')
    args = parser.parse_args()
    
    print(f"Preprocessing {args.dataset} dataset...")
    print(f"Scene: {args.scene}")
    
    # 创建数据集
    dataset = create_dataset(
        dataset_type=args.dataset,
        data_root=args.data_root,
        scene_id=args.scene
    )
    
    print(f"Dataset size: {len(dataset)}")
    
    # 创建预处理器
    preprocessor = DataPreprocessor(
        image_size=(1024, 768),
        normalize=True,
        augment=False
    )
    
    # 预处理数据
    images = []
    cameras = []
    
    for i in range(len(dataset)):
        data = dataset[i]
        
        # 预处理图像
        image = data['image'].permute(1, 2, 0).numpy()
        image = preprocessor.preprocess_image(image)
        images.append(image)
        
        # 相机参数
        cameras.append({
            'intrinsics': data['camera_intrinsics'].numpy(),
            'extrinsics': data['camera_extrinsics'].numpy()
        })
        
        if (i + 1) % 10 == 0:
            print(f"Processed {i + 1}/{len(dataset)} frames")
    
    # 保存
    output_dir = Path(args.output) / args.dataset / args.scene
    preprocessor.save_preprocessed_data(
        output_dir,
        images,
        cameras,
        {'dataset': args.dataset, 'scene': args.scene}
    )
    
    print(f"Preprocessing completed! Output: {output_dir}")


if __name__ == '__main__':
    main()
