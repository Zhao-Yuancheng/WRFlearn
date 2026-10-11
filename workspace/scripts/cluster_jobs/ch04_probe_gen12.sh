#!/bin/bash
# ch04 勘察 12：nl_get 重名核查
cd /users/zhyuancheng2025/IceLake/wrf-4.8/build/WRF || exit 1
echo 'top duplicated nl_get names:'
grep -o 'SUBROUTINE nl_get_[A-Za-z0-9_]*' inc/nl_config.inc | sort | uniq -c | sort -rn | head -6
echo 'sample duplicated definition context:'
grep -n 'SUBROUTINE nl_get_mp_physics' inc/nl_config.inc | head -4
grep -n -A2 'SUBROUTINE nl_get_mp_physics' inc/nl_config.inc | head -12
echo 'DONE'