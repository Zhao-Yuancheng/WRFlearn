#!/bin/bash
# ch04 勘察 2：生成物内容抽样（只读）
cd /users/zhyuancheng2025/IceLake/wrf-4.8/build/WRF || exit 1
echo '=== Registry symlink ==='
ls -l Registry/Registry 2>&1
echo '=== inc/io_form_for_stream.inc head 40 ==='
head -40 inc/io_form_for_stream.inc
echo '=== inc/allocs.inc head 30 ==='
head -30 inc/allocs.inc
echo '=== inc/state_subtypes.inc head 20 ==='
head -20 inc/state_subtypes.inc
echo '=== frame/nl_get_0_routines.F head 8 ==='
head -8 frame/nl_get_0_routines.F
echo '=== inc/wrf_bdyin.inc head 12 ==='
head -12 inc/wrf_bdyin.inc 2>/dev/null || echo '(no wrf_bdyin.inc)'
echo '=== state_description section comments ==='
grep -n '^  !' frame/module_state_description.F | head -30
echo '=== PARAM_tr17/P_tr17/NUM_tracer/NUM_moist samples ==='
grep -n 'PARAM_tr17_1\|P_tr17_1\|NUM_tracer\|NUM_moist\|PARAM_NUM' frame/module_state_description.F | head -14
echo '=== count: inc/*.inc ==='
ls inc/*.inc | wc -l
echo '=== med_auxinput_in.inc head 20 ==='
head -20 inc/med_auxinput_in.inc
echo '=== DONE ==='