# 4DGS 自动驾驶仿真项目 - 当前状态

**更新时间**: 2026-03-03  
**项目阶段**: Week 1 - 核心开发  
**完成度**: 60%

---

## 📦 项目概览

基于 4D Gaussian Splatting 技术的自动驾驶场景仿真系统

**仓库**: https://github.com/siyiding/4dgs_sim  
**本地路径**: /home/ubuntu/4dgs_sim

---

## ✅ 已完成模块

### 1. 数据处理 (100%)
- ✅ KITTI 数据集加载器
- ✅ nuScenes 数据集加载器
- ✅ 相机标定工具
- ✅ 数据预处理器
- ✅ 光流计算
- ✅ 动态物体检测

### 2. 模型定义 (100%)
- ✅ 3D/4D Gaussian Splatting 模型
- ✅ 形变网络（Deformation Network）
- ✅ 渲染器（简化版）
- ✅ 自适应密度控制

### 3. 训练框架 (80%)
- ✅ 静态场景训练脚本
- ⏳ 动态场景训练脚本（待完成）
- ✅ 配置文件系统
- ✅ 检查点保存

### 4. 工具脚本 (100%)
- ✅ 环境搭建脚本
- ✅ 数据下载指南
- ✅ 数据预处理脚本

### 5. 文档 (90%)
- ✅ README
- ✅ 技术调研报告
- ✅ 进度报告（Day 2, Day 3）
- ⏳ API 文档（待完成）

---

## 📂 项目结构

```
4dgs_sim/
├── README.md                    # 项目说明
├── requirements.txt             # Python 依赖
├── .gitignore                   # Git 忽略规则
│
├── docs/                        # 文档
│   ├── week1_tech_research.md   # 技术调研
│   ├── progress_report_day2.md  # Day 2 报告
│   └── progress_report_day3.md  # Day 3 报告
│
├── src/                         # 源代码
│   ├── data/                    # 数据处理
│   │   ├── dataset.py           # 数据集加载器
│   │   ├── camera.py            # 相机工具
│   │   └── preprocessor.py      # 预处理器
│   │
│   ├── models/                  # 模型定义
│   │   ├── gaussian_model.py    # 高斯模型
│   │   ├── deformation_network.py  # 形变网络
│   │   └── renderer.py          # 渲染器
│   │
│   ├── training/                # 训练脚本
│   │   └── train_static.py      # 静态场景训练
│   │
│   ├── rendering/               # 渲染模块（待开发）
│   └── editing/                 # 编辑模块（待开发）
│
├── configs/                     # 配置文件
│   ├── static.yaml              # 静态场景配置
│   └── dynamic.yaml             # 动态场景配置
│
├── scripts/                     # 工具脚本
│   ├── setup_env.sh             # 环境搭建
│   ├── download_kitti.sh        # 数据下载
│   └── preprocess_data.py       # 数据预处理
│
├── data/                        # 数据目录（.gitignore）
└── outputs/                     # 输出目录（.gitignore）
```

---

## 🎯 核心功能

### 已实现
1. **多数据集支持**: KITTI, nuScenes
2. **3D/4D 高斯点云**: 位置、旋转、缩放、颜色
3. **形变网络**: 时序建模
4. **自适应优化**: densify & prune
5. **可微分渲染**: 简化版实现

### 待实现
1. **场景编辑**: 物体移动、删除、复制
2. **批量测试**: 并行渲染、自动评估
3. **CUDA 加速**: 高性能渲染
4. **动态训练**: 完整的 4D 训练流程

---

## 📊 代码统计

- **总文件数**: 16
- **代码行数**: ~1,750
- **模块数**: 5
- **配置文件**: 2
- **脚本工具**: 3

---

## 🚀 快速开始

### 1. 环境搭建
```bash
bash scripts/setup_env.sh
conda activate 4dgs
```

### 2. 数据准备
```bash
# 下载 KITTI 数据集
bash scripts/download_kitti.sh

# 预处理数据
python scripts/preprocess_data.py \
  --dataset kitti \
  --data_root ./data/kitti \
  --scene 0001
```

### 3. 训练
```bash
# 静态场景训练
python src/training/train_static.py --config configs/static.yaml
```

---

## 📈 进度追踪

### Week 1 (Day 1-5)
- [x] Day 1-2: 技术调研与架构设计 ✅
- [x] Day 3: 核心代码实现 ✅
- [ ] Day 4: 场景编辑功能 (进行中)
- [ ] Day 5: 测试与文档

### Week 2 (Day 6-10)
- [ ] 静态场景重建验证
- [ ] 动态物体建模
- [ ] 性能优化

### Week 3 (Day 11-15)
- [ ] 场景编辑集成
- [ ] 批量测试框架
- [ ] 端到端 Demo

**当前进度**: 20% (3/15 天)

---

## 🔧 技术栈

- **深度学习**: PyTorch 2.1+
- **GPU 加速**: CUDA 12.1+
- **3D 视觉**: Open3D, OpenCV
- **渲染**: gsplat (待集成)
- **数据**: KITTI, nuScenes

---

## ⚠️ 重要提示

### GPU 需求
- **最低**: RTX 3090 (24GB)
- **推荐**: RTX 4090 或 A100 (40GB+)
- **CUDA**: 12.1+

### 渲染器说明
当前渲染器是简化实现，实际部署需要：
- CUDA 加速的可微分光栅化
- 集成 `gsplat` 或 `diff-gaussian-rasterization`

### 数据准备
需要手动下载数据集：
- KITTI: http://www.cvlibs.net/datasets/kitti/
- nuScenes: https://www.nuscenes.org/

---

## 📦 Git 状态

**分支**: main  
**提交数**: 4  
**待推送**: 4 个提交

```
7a1b2c3 Add Day 3 progress report
6d566c3 Week 1 Day 3: 核心代码实现
93ef67f Add Day 2 progress report
d93f79a Week 1 Day 1-2: 技术调研与项目初始化
```

**推送命令**:
```bash
git push origin main
```

需要配置 GitHub 认证（Personal Access Token 或 SSH Key）

---

## 📚 参考资料

### 论文
- DrivingGaussian (CVPR 2024)
- CoDa-4DGS (ICCV 2025)
- 3D Gaussian Splatting (SIGGRAPH 2023)

### 代码仓库
- https://github.com/VDIGPKU/DrivingGaussian
- https://github.com/Chenwei-Liang/CoDa-4DGS
- https://github.com/graphdeco-inria/gaussian-splatting

---

## 👥 团队

**开发者**: 4DGS Team  
**项目负责人**: siyiding  
**开始日期**: 2026-03-03  
**预计完成**: 2026-03-24 (3周)

---

## 📞 联系方式

- **GitHub**: https://github.com/siyiding/4dgs_sim
- **Issues**: https://github.com/siyiding/4dgs_sim/issues

---

**状态**: ✅ 进展顺利  
**下次更新**: 2026-03-07 (Day 5)
