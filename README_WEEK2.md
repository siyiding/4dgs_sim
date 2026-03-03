# Week 2 开始 - 核心算法验证

## 🎯 本周目标

### 静态场景重建 (Day 6-8)
验证 3D Gaussian Splatting 在自动驾驶场景的重建能力

**目标**: PSNR > 28dB, SSIM > 0.85

### 动态物体建模 (Day 9-10)
实现 4D 扩展，支持动态场景

**目标**: 时序一致性良好，动态物体可渲染

---

## 📅 详细计划

### Day 6: 数据准备与初步训练
- 准备 KITTI 数据
- 数据预处理
- 初步训练（10 epochs）

### Day 7: 模型调优
- 超参数调优
- 增加训练轮数（50-100 epochs）
- PSNR > 25dB

### Day 8: 质量优化
- 精细调优
- 达到 PSNR > 28dB
- 完整评估

### Day 9: 4D 扩展
- 实现 4D Gaussian Splatting
- 形变网络训练
- 动态渲染

### Day 10: 时序优化
- 时序一致性优化
- 运动平滑
- Week 2 总结

---

## 📊 评估指标

| 指标 | 目标 | 优秀 |
|------|------|------|
| PSNR | > 28dB | > 30dB |
| SSIM | > 0.85 | > 0.90 |
| 渲染速度 | > 10 FPS | > 30 FPS |

---

## 🚀 快速开始

```bash
# 数据预处理
python scripts/preprocess_data.py \
  --dataset kitti \
  --data_root ./data/kitti \
  --scene 0001

# 静态场景训练
python src/training/train_static.py --config configs/static.yaml

# 动态场景训练
python src/training/train_dynamic.py --config configs/dynamic.yaml
```

---

**Week 1**: ✅ 100% 完成  
**Week 2**: 🚀 进行中  
**POC 进度**: 33% (5/15 天)
