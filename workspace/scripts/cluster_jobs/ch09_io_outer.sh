#!/bin/bash
#SBATCH -J ch09_io
#SBATCH -p cpu
#SBATCH -N 1
#SBATCH -n 1
#SBATCH -c 8
#SBATCH -t 02:00:00
#SBATCH -o /users/zhyuancheng2025/IceLake/ch09_exp/slurm-%j.out

exec singularity exec --bind /users:/users,/data:/data \
  /users/zhyuancheng2025/oneapi.sif \
  /bin/bash /users/zhyuancheng2025/IceLake/ch09_exp/ch09_io_inner.sh