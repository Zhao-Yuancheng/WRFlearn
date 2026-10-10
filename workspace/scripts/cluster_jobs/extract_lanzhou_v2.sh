#!/usr/bin/env bash
# 兰州 2025 夏 2m 温度提取 v2：ncks + 动态库整体搬运
B=/users/zhyuancheng2025/IceLake/lz_case
mkdir -p $B/bin $B/lib $B/out
cp -f /usr/bin/ncks $B/bin/

echo '--- ldd ncks ---'
ldd /usr/bin/ncks | tee $B/ldd.txt

for so in $(ldd /usr/bin/ncks | awk '{for(i=1;i<=NF;i++) if ($i ~ /^\//) print $i}'); do
  case "$so" in /usr/lib64/*|/lib64/*|/usr/lib/*) cp -aL "$so" $B/lib/ 2>/dev/null || true ;; esac
done
echo '--- 搬运的库 ---'
ls $B/lib | head -24

export LD_LIBRARY_PATH=$B/lib:$LD_LIBRARY_PATH
echo '--- 计算节点试运行 v2 ---'
if $B/bin/ncks -h >/dev/null 2>&1; then
  echo NCKS_OK
else
  echo NCKS_FAIL
  $B/bin/ncks -h 2>&1 | head -3
  exit 9
fi

echo '--- 提取 2025-06/07/08 ---'
for m in 202506 202507 202508; do
  $B/bin/ncks -O -v t2m -d latitude,36.7,35.4 -d longitude,103.2,104.8 \
    /data/groups/lzu_public/home/share/ERA5/hourly/New_DATA/Global/2m_temperature/2m_temperature_$m.nc \
    $B/out/t2m_${m}_lz.nc
  echo "done $m"
done
ls -lh $B/out
echo '--- 子集结构 ---'
ncdump -h $B/out/t2m_202507_lz.nc | head -12
