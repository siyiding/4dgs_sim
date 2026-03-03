"""
形变网络 - 用于动态场景建模
"""

import torch
import torch.nn as nn
from typing import Tuple


class DeformationNetwork(nn.Module):
    """形变网络 - 预测高斯点的时序形变"""
    
    def __init__(
        self,
        input_dim: int = 3,
        hidden_dim: int = 128,
        num_layers: int = 4,
        use_time_encoding: bool = True
    ):
        """
        Args:
            input_dim: 输入维度（位置）
            hidden_dim: 隐藏层维度
            num_layers: 网络层数
            use_time_encoding: 是否使用时间编码
        """
        super().__init__()
        
        self.input_dim = input_dim
        self.hidden_dim = hidden_dim
        self.use_time_encoding = use_time_encoding
        
        # 时间编码维度
        self.time_encoding_dim = 16 if use_time_encoding else 1
        
        # 位置编码
        self.pos_encoder = PositionalEncoding(input_dim, num_freqs=6)
        pos_encoding_dim = self.pos_encoder.output_dim
        
        # MLP 网络
        layers = []
        in_dim = pos_encoding_dim + self.time_encoding_dim
        
        for i in range(num_layers):
            out_dim = hidden_dim if i < num_layers - 1 else 3 + 4 + 3  # xyz + rotation + scaling
            layers.append(nn.Linear(in_dim, out_dim))
            
            if i < num_layers - 1:
                layers.append(nn.ReLU(inplace=True))
            
            in_dim = out_dim
        
        self.mlp = nn.Sequential(*layers)
        
        # 初始化为小值，避免初始形变过大
        for m in self.mlp.modules():
            if isinstance(m, nn.Linear):
                nn.init.xavier_uniform_(m.weight, gain=0.01)
                nn.init.zeros_(m.bias)
    
    def encode_time(self, time: torch.Tensor) -> torch.Tensor:
        """
        时间编码
        
        Args:
            time: [N] 时间戳
            
        Returns:
            encoded: [N, time_encoding_dim] 编码后的时间
        """
        if not self.use_time_encoding:
            return time.unsqueeze(-1)
        
        # 傅里叶时间编码
        freqs = 2.0 ** torch.linspace(0, 7, self.time_encoding_dim // 2, device=time.device)
        time_encoded = time.unsqueeze(-1) * freqs.unsqueeze(0)
        time_encoded = torch.cat([torch.sin(time_encoded), torch.cos(time_encoded)], dim=-1)
        
        return time_encoded
    
    def forward(
        self,
        xyz: torch.Tensor,
        time: torch.Tensor
    ) -> Tuple[torch.Tensor, torch.Tensor, torch.Tensor]:
        """
        前向传播
        
        Args:
            xyz: [N, 3] 高斯点位置
            time: [N] 或 [1] 时间戳
            
        Returns:
            delta_xyz: [N, 3] 位置偏移
            delta_rotation: [N, 4] 旋转偏移（四元数）
            delta_scaling: [N, 3] 缩放偏移
        """
        # 位置编码
        xyz_encoded = self.pos_encoder(xyz)
        
        # 时间编码
        if time.dim() == 0:
            time = time.unsqueeze(0).expand(xyz.shape[0])
        elif time.shape[0] == 1:
            time = time.expand(xyz.shape[0])
        
        time_encoded = self.encode_time(time)
        
        # 拼接输入
        x = torch.cat([xyz_encoded, time_encoded], dim=-1)
        
        # MLP 预测
        output = self.mlp(x)
        
        # 分割输出
        delta_xyz = output[:, :3]
        delta_rotation = output[:, 3:7]
        delta_scaling = output[:, 7:10]
        
        # 限制形变幅度
        delta_xyz = torch.tanh(delta_xyz) * 0.1
        delta_rotation = torch.tanh(delta_rotation) * 0.1
        delta_scaling = torch.tanh(delta_scaling) * 0.1
        
        return delta_xyz, delta_rotation, delta_scaling


class PositionalEncoding(nn.Module):
    """位置编码（傅里叶特征）"""
    
    def __init__(self, input_dim: int, num_freqs: int = 10):
        """
        Args:
            input_dim: 输入维度
            num_freqs: 频率数量
        """
        super().__init__()
        
        self.input_dim = input_dim
        self.num_freqs = num_freqs
        self.output_dim = input_dim * (2 * num_freqs + 1)
        
        # 频率
        freq_bands = 2.0 ** torch.linspace(0, num_freqs - 1, num_freqs)
        self.register_buffer('freq_bands', freq_bands)
    
    def forward(self, x: torch.Tensor) -> torch.Tensor:
        """
        Args:
            x: [N, input_dim] 输入
            
        Returns:
            encoded: [N, output_dim] 编码后的输入
        """
        # 原始输入
        encoded = [x]
        
        # 傅里叶特征
        for freq in self.freq_bands:
            encoded.append(torch.sin(x * freq))
            encoded.append(torch.cos(x * freq))
        
        return torch.cat(encoded, dim=-1)
