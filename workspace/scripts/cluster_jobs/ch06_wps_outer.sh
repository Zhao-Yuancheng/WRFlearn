#!/bin/bash
#SBATCH -J wps_lz
#SBATCH -p cpu
#SBATCH -N 1
#SBATCH -n 1
#SBATCH -c 8
#SBATCH -t 02:00:00
#SBATCH -o /users/zhyuancheng2025/IceLake/ch06_exp/slurm-%j.out

exec singularity exec --bind /users:/users,/data:/data,/opt/app/wrf:/opt/app/wrf \
  /users/zhyuancheng2025/oneapi.sif \
  /bin/bash /users/zhyuancheng2025/IceLake/ch06_exp/ch06_wps_inner.sh