#!/usr/bin/env bash
# 兰州 2025 夏 2m 温度小区域提取（NCO 搬运路线）+ aifs.sif python 探测
B=/users/zhyuancheng2025/IceLake/lz_case
mkdir -p $B/bin $B/out
cp -f /usr/bin/ncks $B/bin/ncks 2>/dev/null || true

echo '--- ncks 计算节点试运行 ---'
if $B/bin/ncks -h >/dev/null 2>&1; then
  echo 'ncks OK'
else
  echo 'NCKS_FAIL: 计算节点无法运行 ncks（缺库）'
  exit 9
fi

echo '--- 提取 2025-06/07/08 兰州区域 ---'
for m in 202506 202507 202508; do
  $B/bin/ncks -O -v t2m -d latitude,36.7,35.4 -d longitude,103.2,104.8 \
    /data/groups/lzu_public/home/share/ERA5/hourly/New_DATA/Global/2m_temperature/2m_temperature_$m.nc \
    $B/out/t2m_${m}_lz.nc
  echo "done $m"
done
ls -lh $B/out
echo '--- 子集结构 ---'
ncdump -h $B/out/t2m_202507_lz.nc | head -12

echo '--- aifs.sif python 探测（登录侧公共镜像，非致命） ---'
if [ -f /data/groups/lzu_public/home/share/aifs.sif ]; then
  timeout 120 singularity exec /data/groups/lzu_public/home/share/aifs.sif \
    python -c 'import sys; print("py", sys.version.split()[0]); import numpy; print("numpy OK"); import xarray; print("xarray OK")' \
    2>&1 | tail -4 || echo 'aifs probe failed'
else
  echo 'aifs.sif not found'
fi
