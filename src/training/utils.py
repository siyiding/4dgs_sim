"""
训练工具函数
"""

import torch
import numpy as np
from typing import Dict
import time


def compute_psnr(img_pred: torch.Tensor, img_gt: torch.Tensor) -> float:
    """
    计算 PSNR
    
    Args:
        img_pred: 预测图像 [C, H, W]
        img_gt: 真实图像 [C, H, W]
        
    Returns:
        PSNR 值
    """
    mse = torch.mean((img_pred - img_gt) ** 2)
    if mse < 1e-10:
        return 100.0
    psnr = 20 * torch.log10(1.0 / torch.sqrt(mse))
    return psnr.item()


def compute_ssim(img_pred: torch.Tensor, img_gt: torch.Tensor, window_size: int = 11) -> float:
    """
    计算 SSIM（简化版）
    
    Args:
        img_pred: 预测图像 [C, H, W]
        img_gt: 真实图像 [C, H, W]
        window_size: 窗口大小
        
    Returns:
        SSIM 值
    """
    # 简化实现：使用均值和方差
    mu1 = img_pred.mean()
    mu2 = img_gt.mean()
    
    sigma1 = img_pred.var()
    sigma2 = img_gt.var()
    sigma12 = ((img_pred - mu1) * (img_gt - mu2)).mean()
    
    C1 = 0.01 ** 2
    C2 = 0.03 ** 2
    
    ssim = ((2 * mu1 * mu2 + C1) * (2 * sigma12 + C2)) / \
           ((mu1 ** 2 + mu2 ** 2 + C1) * (sigma1 + sigma2 + C2))
    
    return ssim.item()


class TrainingLogger:
    """训练日志记录器"""
    
    def __init__(self, log_file: str = None):
        self.log_file = log_file
        self.metrics = []
        self.start_time = time.time()
        
    def log(self, epoch: int, metrics: Dict):
        """记录指标"""
        metrics['epoch'] = epoch
        metrics['time'] = time.time() - self.start_time
        self.metrics.append(metrics)
        
        # 打印
        log_str = f"Epoch {epoch}: "
        log_str += ", ".join([f"{k}={v:.4f}" for k, v in metrics.items() if k != 'epoch'])
        print(log_str)
        
        # 写入文件
        if self.log_file:
            with open(self.log_file, 'a') as f:
                f.write(log_str + '\n')
    
    def get_best_epoch(self, metric: str = 'loss', mode: str = 'min') -> int:
        """获取最佳 epoch"""
        if not self.metrics:
            return 0
        
        values = [m[metric] for m in self.metrics if metric in m]
        if mode == 'min':
            best_idx = np.argmin(values)
        else:
            best_idx = np.argmax(values)
        
        return self.metrics[best_idx]['epoch']


class EarlyStopping:
    """早停机制"""
    
    def __init__(self, patience: int = 10, min_delta: float = 0.0):
        self.patience = patience
        self.min_delta = min_delta
        self.counter = 0
        self.best_loss = None
        self.early_stop = False
        
    def __call__(self, loss: float) -> bool:
        if self.best_loss is None:
            self.best_loss = loss
        elif loss > self.best_loss - self.min_delta:
            self.counter += 1
            if self.counter >= self.patience:
                self.early_stop = True
        else:
            self.best_loss = loss
            self.counter = 0
        
        return self.early_stop


def save_checkpoint(
    model,
    optimizer,
    epoch: int,
    loss: float,
    path: str,
    **kwargs
):
    """保存检查点"""
    checkpoint = {
        'epoch': epoch,
        'model_state_dict': model.state_dict(),
        'optimizer_state_dict': optimizer.state_dict(),
        'loss': loss,
    }
    checkpoint.update(kwargs)
    torch.save(checkpoint, path)


def load_checkpoint(path: str, model, optimizer=None):
    """加载检查点"""
    checkpoint = torch.load(path)
    model.load_state_dict(checkpoint['model_state_dict'])
    
    if optimizer is not None:
        optimizer.load_state_dict(checkpoint['optimizer_state_dict'])
    
    return checkpoint['epoch'], checkpoint['loss']
