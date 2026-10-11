#!/bin/bash
# ch04 勘察 10：T2 的最终生成形态（域类型声明与释放代码）
cd /users/zhyuancheng2025/IceLake/wrf-4.8/build/WRF || exit 1
echo '=== state_struct.inc: t2 ==='
grep -n ':: t2$\|:: t2 ' inc/state_struct.inc | head -4
echo '=== deallocs: t2 ==='
grep -n -A4 "in_use_for_config(id,'t2')" inc/deallocs_*.F | head -14
echo '=== nl_get count sample: total subroutines ==='
grep -c 'SUBROUTINE nl_get' inc/nl_config.inc
grep -c 'SUBROUTINE nl_set' inc/nl_config.inc
echo '=== DONE ==='