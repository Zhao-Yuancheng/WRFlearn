#!/bin/bash
# ch08 生产结果收集（只读）
CASE=/users/zhyuancheng2025/IceLake/wrf-4.8/cases/lanzhou2025/wrf
EXP=/users/zhyuancheng2025/IceLake/ch08_exp
echo '=== CH08 PROD SUMMARY section ==='
sed -n '/PROD JOB START/,$p' "$EXP/SUMMARY.txt"
echo
echo '=== wrfout/wrfrst 全清单 ==='
ls -la $CASE/wrfout_* $CASE/wrfrst_* 2>/dev/null
echo
echo '=== SUCCESS line ==='
grep -n "SUCCESS COMPLETE WRF" $CASE/rsl.out.0000 | head -3
echo '=== 主循环步数统计 ==='
for d in 1 2; do
  grep "on domain   $d:" $CASE/rsl.out.0000 | awk '{print $NF}' | awk -v d=$d '{s+=$1; n++; if(n==1||$1<mn)mn=$1; if($1>mx)mx=$1} END{printf "domain %s: n=%d min=%.4f max=%.4f mean=%.4f\n", d, n, mn, mx, s/n}'
done
echo '=== 写盘 Timing 行（全部）==='
grep "Timing for Writing" $CASE/rsl.out.0000
echo '=== 边界处理 Timing 行数 ==='
grep -c "Timing for processing lateral boundary" $CASE/rsl.out.0000
echo '=== 顶部 main Timing（前 6 行）==='
grep "Timing for main" $CASE/rsl.out.0000 | head -6
echo '=== wrf_prod_np64.log 尾部 ==='
tail -3 $CASE/wrf_prod_np64.log 2>/dev/null
echo '=== rsl 文件数量与大小 ==='
ls -la $CASE/rsl.out.0000 $CASE/rsl.error.0000 2>/dev/null
ls $CASE/rsl.out.* 2>/dev/null | wc -l
echo '=== 磁盘 ==='
du -sh "$CASE"