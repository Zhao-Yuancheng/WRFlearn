#!/bin/bash
# 探查：short vs canonical namelist 差异；rst_case 运行日志的写盘行与 d02 步数
CASE=/users/zhyuancheng2025/IceLake/wrf-4.8/cases/lanzhou2025/wrf
EXP=/users/zhyuancheng2025/IceLake/ch08_exp
RSTC=$EXP/rst_case
echo '=== diff canonical vs short ==='
diff $CASE/namelist.input.canonical $EXP/namelist.input.short
echo
echo '=== rst_case rsl: 所有 Writing 行 ==='
grep -n "Timing for Writing" $RSTC/rsl.out.0000
echo
echo '=== rst_case rsl: domain 2 行数 ==='
grep -c "domain   2" $RSTC/rsl.out.0000
echo '=== domain 2 首 4 行 ==='
grep "domain   2" $RSTC/rsl.out.0000 | head -4
echo '=== domain 2 尾 4 行 ==='
grep "domain   2" $RSTC/rsl.out.0000 | tail -4
echo
echo '=== rst_case namelist.output: history/frames/restart 行 ==='
grep -n "history_interval\|frames_per_outfile\|restart" $RSTC/namelist.output | head -24