#!/usr/bin/env bash
# 提交 conda 库检查作业并查询队列
cd /users/zhyuancheng2025/IceLake/scripts_staging || exit 1
sbatch condalib_check.sbatch
sleep 2
squeue -u zhyuancheng2025 -h
