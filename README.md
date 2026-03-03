# 4DGS Autonomous Driving Simulation

基于 4D Gaussian Splatting 的自动驾驶仿真系统

## 项目概述

本项目旨在构建一个基于 4D Gaussian Splatting 技术的自动驾驶场景仿真系统，支持：
- 动态场景重建
- 场景编辑和变体生成
- 批量测试和评估

## POC 计划（3周）

### Week 1: 技术调研与环境搭建 ✅ 进行中
- [x] 技术调研
- [x] 架构设计
- [ ] 环境搭建
- [ ] 数据准备

### Week 2: 核心功能开发
- [ ] 静态场景重建
- [ ] 动态物体建模

### Week 3: 集成验证
- [ ] 场景编辑功能
- [ ] 端到端测试

## 技术栈

- **深度学习**: PyTorch 2.1+, CUDA 12.1+
- **渲染**: gsplat, diff-gaussian-rasterization
- **3D 视觉**: COLMAP, Open3D, OpenCV
- **数据**: KITTI, nuScenes

## 项目结构

```
4dgs_sim/
├── docs/              # 文档
├── src/               # 源代码
│   ├── data/         # 数据处理
│   ├── models/       # 模型定义
│   ├── training/     # 训练管道
│   ├── rendering/    # 渲染引擎
│   └── editing/      # 场景编辑
├── scripts/          # 脚本工具
├── configs/          # 配置文件
├── data/             # 数据目录
└── outputs/          # 输出结果
```

## 快速开始

### 环境配置

```bash
# 创建虚拟环境
conda create -n 4dgs python=3.10
conda activate 4dgs

# 安装依赖
pip install torch torchvision --index-url https://download.pytorch.org/whl/cu121
pip install -r requirements.txt
```

### 数据准备

```bash
# 下载 KITTI 数据集
bash scripts/download_kitti.sh

# 预处理数据
python scripts/preprocess_data.py --dataset kitti --scene 0001
```

### 训练

```bash
# 训练静态场景
python src/training/train_static.py --config configs/static.yaml

# 训练动态场景
python src/training/train_dynamic.py --config configs/dynamic.yaml
```

## 参考资料

- [DrivingGaussian](https://github.com/VDIGPKU/DrivingGaussian)
- [CoDa-4DGS](https://github.com/Chenwei-Liang/CoDa-4DGS)
- [3D Gaussian Splatting](https://github.com/graphdeco-inria/gaussian-splatting)

## 进度追踪

查看 [docs/week1_tech_research.md](docs/week1_tech_research.md) 了解详细进度。

---

**项目启动日期**: 2026-03-03  
**预计完成日期**: 2026-03-24 (3周)
