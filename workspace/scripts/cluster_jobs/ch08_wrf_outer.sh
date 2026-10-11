#!/bin/bash
#SBATCH -J ch08_wrf
#SBATCH -p cpu
#SBATCH -N 1
#SBATCH -n 1
#SBATCH -c 64
#SBATCH -t 12:00:00
#SBATCH -o /users/zhyuancheng2025/IceLake/ch08_exp/slurm-%j.out

exec singularity exec --bind /users:/users,/data:/data \
  /users/zhyuancheng2025/oneapi.sif \
  /bin/bash /users/zhyuancheng2025/IceLake/ch08_exp/ch08_wrf_inner.sh