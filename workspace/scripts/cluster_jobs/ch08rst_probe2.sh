#!/bin/bash
# 探查 2：rst_case 完整 rsl 头 + short/canonical 差异（修正路径）
CASE=/users/zhyuancheng2025/IceLake/wrf-4.8/cases/lanzhou2025/wrf
EXP=/users/zhyuancheng2025/IceLake/ch08_exp
RSTC=$EXP/rst_case
echo '=== diff canonical vs short ==='
diff $CASE/namelist.canonical $EXP/namelist.input.short
echo
echo '=== rst_case namelist.input 的 &domains 段 ==='
sed -n '/&domains/,/^\//p' $RSTC/namelist.input | head -40
echo
echo '=== rst_case rsl.out.0000 全文 ==='
cat $RSTC/rsl.out.0000
echo
echo '=== rst_case rsl.error.0000（前 60 行）==='
head -60 $RSTC/rsl.error.0000