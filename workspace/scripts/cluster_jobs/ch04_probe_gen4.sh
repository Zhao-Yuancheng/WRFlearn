#!/bin/bash
# ch04 勘察 4：实际调用命令行与参数（只读）
cd /users/zhyuancheng2025/IceLake/wrf-4.8/build/WRF || exit 1
echo '=== COREDEFS in configure.wrf ==='
grep -n 'COREDEFS' configure.wrf | head -8
echo '=== registry invocation in compile.log ==='
grep -n 'tools/registry' compile.log 2>/dev/null | head -5
echo '=== grep registry in configure.log ==='
grep -n 'registry\|Registry' configure.log 2>/dev/null | head -12
echo '=== count args in actual_new_args.inc ==='
grep -o 'grid%[A-Za-z0-9_]*' inc/actual_new_args.inc | wc -l
echo '=== count args in actual_args.inc ==='
grep -o 'grid%[A-Za-z0-9_]*' inc/actual_args.inc | wc -l
echo '=== actual_args.inc head 6 ==='
head -6 inc/actual_args.inc
echo '=== gen_comms source file presence ==='
ls -l tools/gen_comms.c 2>/dev/null; grep -c 'HALO' tools/gen_comms.c 2>/dev/null
echo '=== DONE ==='