#!/bin/bash
# ch09b 结果收集 + 生产 rsl 步时统计（修正版）
EXP=/users/zhyuancheng2025/IceLake/ch09_exp
CASE=/users/zhyuancheng2025/IceLake/wrf-4.8/cases/lanzhou2025/wrf
echo '=== ch09 SUMMARY（CH09B 段）==='
sed -n '/CH09B JOB START/,$p' $EXP/SUMMARY.txt
echo
echo '=== 保留文件目录 ==='
ls -la $EXP/files_io2c $EXP/files_io11 $EXP/files_io102 2>/dev/null | head -40
echo
echo '=== 生产 rsl 步时统计（修正：取倒数第 3 字段）==='
for d in 1 2; do
  grep "on domain   $d:" $CASE/rsl.out.0000 | awk '{v=$(NF-2)+0; s+=v; n++; if(n==1||v<mn)mn=v; if(v>mx)mx=v} END{printf "domain %s: n=%d min=%.4f max=%.4f mean=%.4f\n", d, n, mn, mx, s/n}'
done
echo '=== 写盘行计数 ==='
echo -n "d01 writes: "; grep -c "Timing for Writing wrfout_d01" $CASE/rsl.out.0000
echo -n "d02 writes: "; grep -c "Timing for Writing wrfout_d02" $CASE/rsl.out.0000
echo '=== rsl.out.0000 头 6 行 ==='
head -6 $CASE/rsl.out.0000