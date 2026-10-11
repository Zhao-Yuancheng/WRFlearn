#!/usr/bin/env bash
# 从 conda-meta 扫描各 env 已装包版本（纯文件读取，无需 import，登录节点可跑）
M=/users/zhyuancheng2025/miniforge3
for e in mklpy P312 RdFlood sam2; do
  echo "===== $e ====="
  ls $M/envs/$e/conda-meta/*.json 2>/dev/null | while read -r f; do
    b=$(basename "$f")
    case "$b" in
      numpy-*|scipy-*|pandas-*|matplotlib-*|netcdf4-*|xarray-*|metpy-*|wrf-python-*|python-3*|setuptools-*)
        echo "  ${b%.json}"
        ;;
    esac
  done
done
