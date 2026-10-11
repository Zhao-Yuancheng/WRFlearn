#!/bin/bash
#SBATCH -J ch07_real
#SBATCH -p cpu
#SBATCH -N 1
#SBATCH -n 1
#SBATCH -c 8
#SBATCH -t 01:00:00
#SBATCH -o /users/zhyuancheng2025/IceLake/ch07_exp/slurm-%j.out

exec singularity exec --bind /users:/users,/data:/data \
  /users/zhyuancheng2025/oneapi.sif \
  /bin/bash /users/zhyuancheng2025/IceLake/ch07_exp/ch07_real_inner.sh