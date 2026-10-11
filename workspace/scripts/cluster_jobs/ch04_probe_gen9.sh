#!/bin/bash
# ch04 勘察 9：i1 变量最终形态核对
cd /users/zhyuancheng2025/IceLake/wrf-4.8/build/WRF || exit 1
echo '=== allocs_23.F around ru_tendf ==='
grep -n -B3 -A8 'ru_tendf' inc/allocs_23.F | head -40
echo '=== state_struct.inc / state_subtypes.inc mention ru_tendf? ==='
grep -n 'ru_tendf' inc/state_struct.inc inc/state_subtypes.inc 2>/dev/null | head -5
echo '=== solve_em.F lines 160..175 ==='
sed -n '160,175p' dyn_em/solve_em.F
echo '=== i1 count in i1_decl.inc ==='
grep -c '::' inc/i1_decl.inc
echo '=== DONE ==='