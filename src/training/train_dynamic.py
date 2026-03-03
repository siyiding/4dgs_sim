"""
动态场景训练脚本（4D Gaussian Splatting）
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
from models.deformation_network import DeformationNetwork
from models.renderer import GaussianRenderer
from data.dataset import create_dataset


class DynamicSceneTrainer:
    """动态场景训练器（4D）"""
    
    def __init__(self, config: dict):
        self.config = config
        self.device = torch.device('cuda' if torch.cuda.is_available() else 'cpu')
        
        # 创建 4D 高斯模型
        self.gaussian_model = GaussianModel(
            num_gaussians=config['model']['num_gaussians'],
            sh_degree=config['model']['sh_degree'],
            use_4d=True
        ).to(self.device)
        
        # 创建形变网络
        self.deformation_net = DeformationNetwork(
            input_dim=3,
            hidden_dim=config['deformation']['hidden_dim'],
            num_layers=config['deformation']['num_layers'],
            use_time_encoding=config['deformation']['use_time_encoding']
        ).to(self.device)
        
        # 创建渲染器
        self.renderer = GaussianRenderer(
            image_size=tuple(config['data']['image_size']),
            background_color=tuple(config['render']['background_color'])
        ).to(self.device)
        
        # 优化器
        self.optimizer = optim.Adam([
            {'params': self.gaussian_model._xyz, 'lr': config['training']['lr_xyz']},
            {'params': self.gaussian_model._rotation, 'lr': config['training']['lr_rotation']},
            {'params': self.gaussian_model._scaling, 'lr': config['training']['lr_scaling']},
            {'params': self.gaussian_model._opacity, 'lr': config['training']['lr_opacity']},
            {'params': self.gaussian_model._features_dc, 'lr': config['training']['lr_features']},
            {'params': self.gaussian_model._features_rest, 'lr': config['training']['lr_features'] / 20.0},
            {'params': self.deformation_net.parameters(), 'lr': config['training']['lr_deformation']}
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
            batch_size=1,
            shuffle=True,
            num_workers=config['data']['num_workers']
        )
        
        # 输出目录
        self.output_dir = Path(config['training']['output_dir'])
        self.output_dir.mkdir(parents=True, exist_ok=True)
        
    def apply_deformation(self, xyz, time):
        """应用形变"""
        delta_xyz, delta_rotation, delta_scaling = self.deformation_net(xyz, time)
        
        # 应用位置偏移
        xyz_deformed = xyz + delta_xyz
        
        return xyz_deformed, delta_rotation, delta_scaling
    
    def train_epoch(self, epoch: int):
        """训练一个 epoch"""
        self.gaussian_model.train()
        self.deformation_net.train()
        
        total_loss = 0
        pbar = tqdm(self.train_loader, desc=f'Epoch {epoch}')
        
        for batch_idx, batch in enumerate(pbar):
            # 数据移到设备
            image_gt = batch['image'].to(self.device)
            intrinsics = batch['camera_intrinsics'].to(self.device)
            extrinsics = batch['camera_extrinsics'].to(self.device)
            timestamp = batch['timestamp'].to(self.device)
            
            # 获取形变后的高斯点
            xyz_deformed, delta_rot, delta_scale = self.apply_deformation(
                self.gaussian_model.xyz,
                timestamp
            )
            
            # 渲染
            rendered = self.renderer(
                xyz=xyz_deformed,
                rotation=self.gaussian_model.rotation,
                scaling=self.gaussian_model.scaling,
                opacity=self.gaussian_model.opacity,
                features=self.gaussian_model.features,
                camera_intrinsics=intrinsics.squeeze(0),
                camera_extrinsics=extrinsics.squeeze(0)
            )
            
            image_pred = rendered['image']
            
            # 计算损失
            loss_l1 = self.l1_loss(image_pred, image_gt.squeeze(0))
            loss_mse = self.mse_loss(image_pred, image_gt.squeeze(0))
            
            # 时序一致性损失（相邻帧的形变应该平滑）
            loss_temporal = 0.0
            if batch_idx > 0:
                # 简化：使用形变幅度作为正则化
                loss_temporal = torch.mean(delta_rot ** 2) + torch.mean(delta_scale ** 2)
            
            loss = (
                self.config['training']['lambda_l1'] * loss_l1 +
                self.config['training']['lambda_mse'] * loss_mse +
                self.config['training']['lambda_temporal'] * loss_temporal
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
                'temporal': f'{loss_temporal:.4f}' if isinstance(loss_temporal, torch.Tensor) else '0.0000'
            })
            
            # 自适应密度控制
            if batch_idx % self.config['training']['densify_interval'] == 0:
                self.gaussian_model.densify(grad_threshold=self.config['training']['densify_grad_threshold'])
                self.gaussian_model.prune(opacity_threshold=self.config['training']['prune_opacity_threshold'])
        
        return total_loss / len(self.train_loader)
    
    def train(self):
        """完整训练流程"""
        print(f"Training 4D Gaussian Splatting on device: {self.device}")
        print(f"Number of Gaussians: {self.gaussian_model.num_gaussians}")
        print(f"Training dataset size: {len(self.train_dataset)}")
        
        for epoch in range(self.config['training']['num_epochs']):
            avg_loss = self.train_epoch(epoch)
            
            print(f"Epoch {epoch}: Average Loss = {avg_loss:.4f}")
            
            # 保存检查点
            if (epoch + 1) % self.config['training']['save_interval'] == 0:
                checkpoint_path = self.output_dir / f'checkpoint_epoch_{epoch+1}.pth'
                self.save_checkpoint(str(checkpoint_path))
                print(f"Saved checkpoint to {checkpoint_path}")
        
        # 保存最终模型
        final_path = self.output_dir / 'final_model.pth'
        self.save_checkpoint(str(final_path))
        print(f"Training completed. Final model saved to {final_path}")
    
    def save_checkpoint(self, path: str):
        """保存检查点"""
        torch.save({
            'gaussian_model': self.gaussian_model.state_dict(),
            'deformation_net': self.deformation_net.state_dict(),
            'optimizer': self.optimizer.state_dict()
        }, path)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--config', type=str, required=True, help='Path to config file')
    args = parser.parse_args()
    
    # 加载配置
    with open(args.config, 'r') as f:
        config = yaml.safe_load(f)
    
    # 创建训练器
    trainer = DynamicSceneTrainer(config)
    
    # 开始训练
    trainer.train()


if __name__ == '__main__':
    main()
