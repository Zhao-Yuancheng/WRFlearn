#!/bin/bash
#SBATCH -J ch05_rcv
#SBATCH -p cpu
#SBATCH -N 1
#SBATCH -n 1
#SBATCH -c 8
#SBATCH -t 01:30:00
#SBATCH -o /users/zhyuancheng2025/IceLake/ch05_exp/slurm-%j.out

# 外层：在 Singularity 容器内执行恢复载荷
exec singularity exec --bind /users:/users,/data:/data \
  /users/zhyuancheng2025/oneapi.sif \
  /bin/bash /users/zhyuancheng2025/IceLake/ch05_exp/ch05_recover_inner.sh