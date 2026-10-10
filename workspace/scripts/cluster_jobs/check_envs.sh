#!/usr/bin/env bash
# 检查集群 miniforge3 各 env 的 python 与科学库可用性
for e in mklpy P312 RdFlood sam2; do
  P=/users/zhyuancheng2025/miniforge3/envs/$e/bin/python
  echo "== $e =="
  if [ -x "$P" ]; then
    "$P" -c 'import sys; print("python", sys.version.split()[0])'
    "$P" -c 'import numpy; print("numpy", numpy.__version__)' 2>/dev/null || echo "numpy: NO"
    "$P" -c 'import netCDF4; print("netCDF4", netCDF4.__version__)' 2>/dev/null || echo "netCDF4: NO"
    "$P" -c 'import xarray; print("xarray", xarray.__version__)' 2>/dev/null || echo "xarray: NO"
  else
    echo "python: NO"
  fi
done
