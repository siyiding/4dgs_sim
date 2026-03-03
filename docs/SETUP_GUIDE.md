# 4DGS 仿真系统 - 环境搭建指南

## 系统要求

### 硬件要求
- **GPU**: NVIDIA RTX 3090 / 4090 / A100 (24GB+ 显存)
- **CPU**: 8 核以上
- **内存**: 32GB+
- **存储**: 500GB+ SSD

### 软件要求
- **操作系统**: Ubuntu 20.04 / 22.04
- **CUDA**: 12.1+
- **Python**: 3.10+
- **Conda**: 推荐使用

---

## 快速安装

### 1. 克隆仓库
```bash
git clone https://github.com/siyiding/4dgs_sim.git
cd 4dgs_sim
```

### 2. 创建虚拟环境
```bash
conda create -n 4dgs python=3.10 -y
conda activate 4dgs
```

### 3. 安装 PyTorch
```bash
pip install torch==2.1.0 torchvision==0.16.0 --index-url https://download.pytorch.org/whl/cu121
```

### 4. 安装依赖
```bash
pip install -r requirements.txt
```

### 5. 验证安装
```bash
python -c "import torch; print(f'PyTorch: {torch.__version__}'); print(f'CUDA: {torch.cuda.is_available()}')"
```

---

## 数据准备

### KITTI 数据集

#### 下载
访问 http://www.cvlibs.net/datasets/kitti/raw_data.php

下载以下文件：
- Raw data (synced+rectified)
- Calibration files

#### 目录结构
```
data/kitti/
├── 0001/
│   ├── image_02/
│   │   └── data/
│   │       ├── 0000000000.png
│   │       └── ...
│   └── calib.txt
└── ...
```

#### 预处理
```bash
python scripts/preprocess_data.py \
  --dataset kitti \
  --data_root ./data/kitti \
  --scene 0001 \
  --output ./data/preprocessed
```

---

## 训练

### 静态场景
```bash
python src/training/train_static.py --config configs/static.yaml
```

### 动态场景
```bash
python src/training/train_dynamic.py --config configs/dynamic.yaml
```

### 监控训练
```bash
tensorboard --logdir outputs/
```

---

## 场景编辑

### 测试编辑功能
```bash
python scripts/test_editing.py
```

### 可视化场景
```bash
python scripts/visualize_scene.py --model outputs/static/final_model.pth
```

---

## 常见问题

### Q1: CUDA out of memory
**解决方案**:
- 减少 `num_gaussians` (configs/*.yaml)
- 减少 `image_size`
- 使用梯度累积

### Q2: 训练不收敛
**解决方案**:
- 调整学习率
- 增加训练轮数
- 检查数据质量

### Q3: 渲染速度慢
**解决方案**:
- 当前是简化实现
- 需要集成 CUDA 加速渲染器
- 参考 gsplat 或 diff-gaussian-rasterization

---

## 性能优化

### GPU 优化
```python
# 使用混合精度训练
torch.cuda.amp.autocast()

# 梯度检查点
torch.utils.checkpoint.checkpoint()
```

### 内存优化
```python
# 减少点云数量
num_gaussians = 50000  # 默认 100000

# 分批处理
batch_size = 1
```

---

## 开发环境

### VS Code 配置
```json
{
  "python.defaultInterpreterPath": "~/anaconda3/envs/4dgs/bin/python",
  "python.linting.enabled": true,
  "python.formatting.provider": "black"
}
```

### 调试
```bash
# 使用 pdb
python -m pdb src/training/train_static.py --config configs/static.yaml

# 使用 ipdb
pip install ipdb
```

---

## 下一步

1. 阅读 [README.md](../README.md)
2. 查看 [Week 1 总结](week1_summary.md)
3. 运行测试脚本
4. 开始训练

---

**更新时间**: 2026-03-03  
**版本**: 1.0
