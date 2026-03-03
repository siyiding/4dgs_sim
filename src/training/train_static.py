"""
静态场景训练脚本
"""

import torch
import torch.nn as nn
import torch.optim as optim
from torch.utils.data import DataLoader
from pathlib import Path
import argparse
from tqdm import tqdm
import yaml

import sys
sys.path.append(str(Path(__file__).parent.parent))

from models.gaussian_model import GaussianModel
from models.renderer import GaussianRenderer
from data.dataset import create_dataset


class StaticSceneTrainer:
    """静态场景训练器"""
    
    def __init__(self, config: dict):
        self.config = config
        self.device = torch.device('cuda' if torch.cuda.is_available() else 'cpu')
        
        # 创建模型
        self.model = GaussianModel(
            num_gaussians=config['model']['num_gaussians'],
            sh_degree=config['model']['sh_degree'],
            use_4d=False
        ).to(self.device)
        
        # 创建渲染器
        self.renderer = GaussianRenderer(
            image_size=tuple(config['data']['image_size']),
            background_color=tuple(config['render']['background_color'])
        ).to(self.device)
        
        # 优化器
        self.optimizer = optim.Adam([
            {'params': self.model._xyz, 'lr': config['training']['lr_xyz']},
            {'params': self.model._rotation, 'lr': config['training']['lr_rotation']},
            {'params': self.model._scaling, 'lr': config['training']['lr_scaling']},
            {'params': self.model._opacity, 'lr': config['training']['lr_opacity']},
            {'params': self.model._features_dc, 'lr': config['training']['lr_features']},
            {'params': self.model._features_rest, 'lr': config['training']['lr_features'] / 20.0}
        ])
        
        # 损失函数
        self.l1_loss = nn.L1Loss()
        self.mse_loss = nn.MSELoss()
        
        # 数据加载器
        self.train_dataset = create_dataset(
            dataset_type=config['data']['dataset_type'],
            data_root=config['data']['data_root'],
            scene_id=config['data']['scene_id'],
            split='train'
        )
        
        self.train_loader = DataLoader(
            self.train_dataset,
            batch_size=1,  # 每次处理一帧
            shuffle=True,
            num_workers=config['data']['num_workers']
        )
        
        # 输出目录
        self.output_dir = Path(config['training']['output_dir'])
        self.output_dir.mkdir(parents=True, exist_ok=True)
        
    def train_epoch(self, epoch: int):
        """训练一个 epoch"""
        self.model.train()
        
        total_loss = 0
        pbar = tqdm(self.train_loader, desc=f'Epoch {epoch}')
        
        for batch_idx, batch in enumerate(pbar):
            # 数据移到设备
            image_gt = batch['image'].to(self.device)
            intrinsics = batch['camera_intrinsics'].to(self.device)
            extrinsics = batch['camera_extrinsics'].to(self.device)
            
            # 渲染
            rendered = self.renderer(
                xyz=self.model.xyz,
                rotation=self.model.rotation,
                scaling=self.model.scaling,
                opacity=self.model.opacity,
                features=self.model.features,
                camera_intrinsics=intrinsics.squeeze(0),
                camera_extrinsics=extrinsics.squeeze(0)
            )
            
            image_pred = rendered['image']
            
            # 计算损失
            loss_l1 = self.l1_loss(image_pred, image_gt.squeeze(0))
            loss_mse = self.mse_loss(image_pred, image_gt.squeeze(0))
            
            loss = (
                self.config['training']['lambda_l1'] * loss_l1 +
                self.config['training']['lambda_mse'] * loss_mse
            )
            
            # 反向传播
            self.optimizer.zero_grad()
            loss.backward()
            self.optimizer.step()
            
            total_loss += loss.item()
            
            # 更新进度条
            pbar.set_postfix({
                'loss': f'{loss.item():.4f}',
                'l1': f'{loss_l1.item():.4f}',
                'mse': f'{loss_mse.item():.4f}'
            })
            
            # 自适应密度控制
            if batch_idx % self.config['training']['densify_interval'] == 0:
                self.model.densify(grad_threshold=self.config['training']['densify_grad_threshold'])
                self.model.prune(opacity_threshold=self.config['training']['prune_opacity_threshold'])
        
        return total_loss / len(self.train_loader)
    
    def train(self):
        """完整训练流程"""
        print(f"Training on device: {self.device}")
        print(f"Number of Gaussians: {self.model.num_gaussians}")
        print(f"Training dataset size: {len(self.train_dataset)}")
        
        for epoch in range(self.config['training']['num_epochs']):
            avg_loss = self.train_epoch(epoch)
            
            print(f"Epoch {epoch}: Average Loss = {avg_loss:.4f}")
            
            # 保存检查点
            if (epoch + 1) % self.config['training']['save_interval'] == 0:
                checkpoint_path = self.output_dir / f'checkpoint_epoch_{epoch+1}.pth'
                self.model.save(str(checkpoint_path))
                print(f"Saved checkpoint to {checkpoint_path}")
        
        # 保存最终模型
        final_path = self.output_dir / 'final_model.pth'
        self.model.save(str(final_path))
        print(f"Training completed. Final model saved to {final_path}")


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--config', type=str, required=True, help='Path to config file')
    args = parser.parse_args()
    
    # 加载配置
    with open(args.config, 'r') as f:
        config = yaml.safe_load(f)
    
    # 创建训练器
    trainer = StaticSceneTrainer(config)
    
    # 开始训练
    trainer.train()


if __name__ == '__main__':
    main()
