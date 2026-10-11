#!/bin/bash
# ch04 勘察 6：流编号常量表与分配代码样本
cd /users/zhyuancheng2025/IceLake/wrf-4.8/build/WRF || exit 1
echo '=== configure.wrf lines 20..34 ==='
sed -n '20,34p' configure.wrf
echo '=== MAX_HISTORY / IWORDSIZE in configure.wrf ==='
grep -n 'MAX_HISTORY\|IWORDSIZE' configure.wrf | head -8
echo '=== inc/switches_and_alarms.inc head 60 ==='
head -60 inc/switches_and_alarms.inc
echo '=== auxhist2x in switches ==='
grep -n 'auxhist2[0-9]_only\|auxinput2[0-9]_only' inc/switches_and_alarms.inc | head -10
echo '=== allocs.inc: t2 allocation sample ==='
grep -n -A4 "in_use_for_config(id,'t2')" inc/allocs.inc | head -12
echo '=== deallocs.inc: t2 sample ==='
grep -n -A3 "in_use_for_config(id,'t2')" inc/deallocs.inc | head -10
echo '=== DONE ==='