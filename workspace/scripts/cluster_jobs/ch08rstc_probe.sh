#!/bin/bash
RUN=/users/zhyuancheng2025/IceLake/ch08_exp/rst_case
echo '=== rst_case wrfrst/wrfout ==='
ls -la $RUN/wrfrst_* $RUN/wrfout_* 2>/dev/null
echo
echo '=== namelist.output 实际读入的 restart 项 ==='
grep -n "restart" $RUN/namelist.output | head -14
echo
echo '=== rsl 中 restart 写盘上下文（前后各 3 行）==='
grep -n -B3 -A3 "Writing restart" $RUN/rsl.out.0000 | head -40