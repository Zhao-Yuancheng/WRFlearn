#!/bin/bash
# 定位 IO 包常量/use_package 定义（ch09 勘察）
cd /users/zhyuancheng2025/IceLake/wrf-4.8/build/WRF || exit 1
echo "=== A: use_package in external/ ==="
grep -rln 'use_package' external/ 2>/dev/null | head -20
echo "=== B: IO_NETCDF in external/ ==="
grep -rn 'IO_NETCDF' external/ 2>/dev/null | head -10
echo "=== C: files in external/io_netcdf ==="
ls external/io_netcdf/
echo "=== D: find *io_pkg* ==="
find . -name '*io_pkg*' 2>/dev/null | head -10
echo "=== E: use_package in main|frame|share|hydro|dyn_em (files) ==="
grep -rln 'use_package' main/ frame/ share/ hydro/ dyn_em/ 2>/dev/null | head -20
echo "=== F: INTEGER FUNCTION use_package anywhere (text files) ==="
grep -rn 'FUNCTION use_package' main/ frame/ share/ hydro/ dyn_em/ external/ arch/ tools/ 2>/dev/null | head -10