#!/usr/bin/env bash
# [登录节点] 准备 ncks 二进制与动态库
B=/users/zhyuancheng2025/IceLake/lz_case
mkdir -p $B/bin $B/lib $B/out
cp -f /usr/bin/ncks $B/bin/
for so in $(ldd /usr/bin/ncks | awk '{for(i=1;i<=NF;i++) if ($i ~ /^\//) print $i}'); do
  case "$so" in /usr/lib64/*|/lib64/*|/usr/lib/*) cp -aL "$so" $B/lib/ 2>/dev/null || true ;; esac
done
echo "libs copied: $(ls $B/lib | wc -l)"
ls $B/lib | head -24
