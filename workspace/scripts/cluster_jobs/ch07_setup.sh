#!/bin/bash
# ch07 运行目录搭建（登录节点执行，轻量操作）：符号链接版标准 em_real 运行目录
set -e
WRFB=/users/zhyuancheng2025/IceLake/wrf-4.8/build/WRF
CASE=/users/zhyuancheng2025/IceLake/wrf-4.8/cases/lanzhou2025
WRF=$CASE/wrf
WPS=$CASE/wps
EXP=/users/zhyuancheng2025/IceLake/ch07_exp
mkdir -p "$WRF" "$EXP"
cd "$WRF"

# 1) 辅助数据文件：镜像 build/WRF/run 为符号链接（跳过模板、代码与文本文件）
for f in "$WRFB"/run/*; do
  b=$(basename "$f")
  case "$b" in
    namelist.input*|*.f90*|*.F|*.f|*.c|CMakeLists.txt|README*|*.txt) continue ;;
  esac
  ln -sf "$f" "./$b"
done

# 2) 可执行文件（构建树 main/ 下）
ln -sf "$WRFB/main/real.exe" ./real.exe
ln -sf "$WRFB/main/wrf.exe"  ./wrf.exe

# 3) 初始/边界数据：链接到 wps 目录的 met_em（避免 700 MB 级重复复制）
rm -f met_em.d01.* met_em.d02.* 2>/dev/null || true
for f in "$WPS"/met_em.d01.*.nc "$WPS"/met_em.d02.*.nc; do
  [ -e "$f" ] && ln -sf "$f" "./$(basename "$f")"
done

# 4) namelist.input（从 EXP 上传件复制）
cp -f "$EXP/namelist.input" ./namelist.input

echo "=== setup done ==="
echo "met_em count: $(ls met_em* 2>/dev/null | wc -l)"
ls -la real.exe wrf.exe namelist.input wrfinput_d01 2>&1 | tail -5
ls *.TBL 2>/dev/null | head -12