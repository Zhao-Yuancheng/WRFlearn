#!/bin/bash
# ch04 勘察 7：分配代码与实际调用点
cd /users/zhyuancheng2025/IceLake/wrf-4.8/build/WRF || exit 1
echo '=== where allocs_calls.inc / allocs.inc are included ==='
grep -rn 'allocs_calls.inc\|inc/allocs.inc\|allocs.inc' frame share dyn_em main 2>/dev/null | grep -v '\.o:' | head -10
echo '=== where deallocs included ==='
grep -rn 'deallocs' frame share dyn_em 2>/dev/null | grep -v '\.o:' | head -12
echo "=== t2 allocation sample in allocs_*.F ==="
grep -l "in_use_for_config(id,'t2')" inc/allocs_*.F | head -3
grep -n -A6 "in_use_for_config(id,'t2')" inc/allocs_*.F | head -18
echo '=== allocs_calls.inc head 20 ==='
head -20 inc/allocs_calls.inc
echo '=== pieces count ==='
ls inc/allocs_*.F | wc -l
ls inc/deallocs_*.F | wc -l
echo '=== DONE ==='