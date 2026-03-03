#!/bin/bash
# KITTI 数据集下载脚本

DATA_DIR="./data/kitti"
mkdir -p $DATA_DIR

echo "Downloading KITTI dataset..."
echo "Please download manually from: http://www.cvlibs.net/datasets/kitti/"
echo ""
echo "Required files:"
echo "  - Raw data (synced+rectified)"
echo "  - Calibration files"
echo ""
echo "Extract to: $DATA_DIR"
echo ""
echo "Expected structure:"
echo "  data/kitti/"
echo "    ├── 0001/"
echo "    │   ├── image_02/data/"
echo "    │   └── calib.txt"
echo "    └── ..."
