#!/usr/bin/env bash
# [计算节点] 用搬运来的 ncks 提取兰州区域 2025-06/07/08 逐时 t2m
B=/users/zhyuancheng2025/IceLake/lz_case
export LD_LIBRARY_PATH=$B/lib:$LD_LIBRARY_PATH

echo '--- ncks 试运行 ---'
if $B/bin/ncks --version >/dev/null 2>&1; then
  echo NCKS_OK
else
  echo NCKS_FAIL
  $B/bin/ncks --version 2>&1 | head -3
  exit 9
fi

echo '--- 提取 2025-06/07/08 ---'
for m in 202506 202507 202508; do
  $B/bin/ncks -O -v t2m -d latitude,35.4,36.7 -d longitude,103.2,104.8 \
    /data/groups/lzu_public/home/share/ERA5/hourly/New_DATA/Global/2m_temperature/2m_temperature_$m.nc \
    $B/out/t2m_${m}_lz.nc
  echo "done $m"
done
ls -lh $B/out
echo '--- 子集结构 ---'
ncdump -h $B/out/t2m_202507_lz.nc | head -12
