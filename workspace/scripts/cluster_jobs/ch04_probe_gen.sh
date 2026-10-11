#!/bin/bash
# ch04 勘察：集群构建树生成物实测（只读）
cd /users/zhyuancheng2025/IceLake/wrf-4.8/build/WRF || exit 1
echo '===INC-*.inc==='
ls inc/*.inc | xargs -n1 basename
echo '===FRAME-NAME-FILTER==='
ls frame/ | grep -E 'nl_|_config|state|namelist|streams|_interp|_order|module_domain' | head -80
echo '===CONFIGURE.WRF-REGISTRY==='
grep -n 'REGISTRY' configure.wrf
echo '===FRAME-MAKEFILE-REGISTRY-RULE==='
grep -n -A3 'module_state_description.F' frame/Makefile
echo '===STATE-DESC-HEAD-60==='
head -60 frame/module_state_description.F
echo '===ACTUAL-NEW-ARGS-HEAD-25==='
head -25 inc/actual_new_args.inc
echo '===ACTUAL-NEW-ARGS-TAIL-8==='
tail -8 inc/actual_new_args.inc
echo '===STATE-STRUCT-HEAD-40==='
head -40 inc/state_struct.inc 2>/dev/null || echo '(no state_struct.inc)'
echo '===DONE==='