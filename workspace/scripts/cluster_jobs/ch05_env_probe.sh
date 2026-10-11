#!/bin/bash
# ch05 勘察 1：构建环境与队列状态
echo '===ENV-WRF==='
cat /users/zhyuancheng2025/IceLake/env-wrf-oneapi.sh
echo '===ENV-DEPS==='
cat /users/zhyuancheng2025/IceLake/env-deps-oneapi.sh
echo '===QUEUE==='
squeue -p cpu 2>/dev/null | head -10
echo '===SINFO==='
sinfo -p cpu -h -o '%P %t %D' 2>/dev/null | head -10
echo '===DF-USERS==='
df -h /users/zhyuancheng2025 2>/dev/null | tail -2
echo '===DONE==='