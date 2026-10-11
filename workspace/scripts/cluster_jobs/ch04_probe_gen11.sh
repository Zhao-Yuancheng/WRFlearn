#!/bin/bash
# ch04 勘察 11：nl_config.inc 子程序数核对
cd /users/zhyuancheng2025/IceLake/wrf-4.8/build/WRF || exit 1
echo 'unique nl_get names:'
grep -o 'SUBROUTINE nl_get_[A-Za-z0-9_]*' inc/nl_config.inc | sort -u | wc -l
echo 'unique nl_set names:'
grep -o 'SUBROUTINE nl_set_[A-Za-z0-9_]*' inc/nl_config.inc | sort -u | wc -l
echo 'total lines of nl_config.inc:'
wc -l inc/nl_config.inc
echo 'DONE'