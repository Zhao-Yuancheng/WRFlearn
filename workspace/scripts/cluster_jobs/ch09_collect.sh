#!/bin/bash
# ch09 IO 实验素材收集（只读）
echo '=== ch09 SUMMARY (from CH09 marker) ==='
sed -n '/CH09 IO JOB START/,$p' /users/zhyuancheng2025/IceLake/ch09_exp/SUMMARY.txt
echo
echo '=== ch09_exp dir ==='
ls -la /users/zhyuancheng2025/IceLake/ch09_exp/
echo
echo '=== ch09 case wrfout files ==='
ls -la /users/zhyuancheng2025/IceLake/ch09_exp/case/wrfout_* 2>/dev/null | head -40