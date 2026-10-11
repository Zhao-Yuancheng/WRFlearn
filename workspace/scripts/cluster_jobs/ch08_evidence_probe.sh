#!/bin/bash
# ch08 写作素材提取（只读）：失败证据 + 启动清单头部
echo '=== restart FATAL rsl ==='
cat /users/zhyuancheng2025/IceLake/ch08_exp/rsl.error.failed_restart.0000
echo
echo '=== slurm-439398.out ==='
cat /users/zhyuancheng2025/IceLake/ch08_exp/slurm-439398.out
echo
echo '=== slurm-439402.out ==='
cat /users/zhyuancheng2025/IceLake/ch08_exp/slurm-439402.out
echo
echo '=== rsl.out.0000 head 130（生产运行）==='
sed -n '1,130p' /users/zhyuancheng2025/IceLake/wrf-4.8/cases/lanzhou2025/wrf/rsl.out.0000 | cut -c1-230
echo
echo '=== SUMMARY diag 段（自 expA 起）==='
sed -n '/expA_ra1/,$p' /users/zhyuancheng2025/IceLake/ch08_exp/SUMMARY.txt | head -80