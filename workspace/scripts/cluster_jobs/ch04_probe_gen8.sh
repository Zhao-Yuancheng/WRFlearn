#!/bin/bash
# ch04 勘察 8：收尾核对（i1 声明形态、actual_args 使用范围）
cd /users/zhyuancheng2025/IceLake/wrf-4.8/build/WRF || exit 1
echo '=== inc/i1_decl.inc head 12 ==='
head -12 inc/i1_decl.inc
echo '=== ru_tendf in allocs pieces? ==='
grep -l "ru_tendf" inc/allocs_*.F | head -3
echo "=== t2 in actual_args.inc (old variant) ==="
grep -o 'grid%t2[^,]*' inc/actual_args.inc | head -3
echo '=== who includes actual_args.inc (build tree) ==='
grep -rln 'actual_args.inc' frame share dyn_em phys main external hydro wrftladj 2>/dev/null | head -8
echo '=== solve_em.int? find interface files ==='
ls share/*.int 2>/dev/null | head -12
echo '=== DONE ==='