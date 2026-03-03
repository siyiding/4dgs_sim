#!/bin/bash
# 环境搭建脚本

echo "Setting up 4DGS Simulation environment..."

# 创建虚拟环境
conda create -n 4dgs python=3.10 -y
conda activate 4dgs

# 安装 PyTorch
pip install torch torchvision --index-url https://download.pytorch.org/whl/cu121

# 安装基础依赖
pip install -r requirements.txt

# 克隆 DrivingGaussian（可选）
# git clone https://github.com/VDIGPKU/DrivingGaussian.git external/DrivingGaussian

echo "Environment setup completed!"
echo "Activate with: conda activate 4dgs"
