#!/bin/bash
#SBATCH -J ctn_inspect
#SBATCH -p cpu
#SBATCH -N 1
#SBATCH -n 1
#SBATCH -c 2
#SBATCH -t 00:10:00
#SBATCH -o /users/zhyuancheng2025/IceLake/ch06_exp/slurm-%j.out

exec singularity exec --bind /users:/users,/data:/data \
  /users/zhyuancheng2025/oneapi.sif \
  /bin/bash /users/zhyuancheng2025/IceLake/ch06_exp/ch06_container_inspect_inner.sh 2>&1