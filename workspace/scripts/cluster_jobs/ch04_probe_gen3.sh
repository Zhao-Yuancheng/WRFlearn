#!/bin/bash
# ch04 勘察 3：Registry/Registry 文件与 in_use_for_config、nl_config.inc
cd /users/zhyuancheng2025/IceLake/wrf-4.8/build/WRF || exit 1
echo '=== Registry/Registry head 60 ==='
head -60 Registry/Registry
echo '=== Registry/Registry tail 10 ==='
tail -10 Registry/Registry
echo '=== configure.wrf: ARCHFLAGS / ENVCOMPDEFS / REGISTRY ==='
grep -n 'ARCHFLAGS\|ENVCOMPDEFS\|^REGISTRY' configure.wrf
echo '=== inc/nl_config.inc head 25 ==='
head -25 inc/nl_config.inc
echo '=== inc/in_use_for_config_t.inc grep t2 ==='
grep -n "t2" inc/in_use_for_config_t.inc | head -5
echo '=== inc/in_use_for_config_q.inc head 12 ==='
head -12 inc/in_use_for_config_q.inc
echo '=== actual_new_args.inc grep t2 ==='
grep -o 'grid%t2[^,]*' inc/actual_new_args.inc | head -3
echo '=== DONE ==='