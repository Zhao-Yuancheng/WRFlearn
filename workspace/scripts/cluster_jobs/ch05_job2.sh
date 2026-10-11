#!/bin/bash
#SBATCH -J ch05_smoke
#SBATCH -p cpu
#SBATCH -N 1
#SBATCH -n 1
#SBATCH -c 8
#SBATCH -t 01:00:00
#SBATCH -o /users/zhyuancheng2025/IceLake/ch05_exp/slurm-%j.out

# ch05 集群实测 Job2：em_hill2d_x 理想算例冒烟（build → ideal → wrf → restore em_real）
set +u
export ME=IceLake
source /users/zhyuancheng2025/IceLake/wrf-4.8/env-wrf-oneapi.sh
set -u
WRF=/users/zhyuancheng2025/IceLake/wrf-4.8/build/WRF
EXP=/users/zhyuancheng2025/IceLake/ch05_exp
cd "$WRF" || exit 1
log(){ echo "[$(date +%F' '%H:%M:%S)] $*" >> "$EXP/SUMMARY.txt"; }

log "=========== SMOKE JOB START ==========="
md5sum main/wrf.exe > "$EXP/md5_before_smoke.txt"

# 1) 构建 em_hill2d_x（理想算例：wrf + ideal）
t0=$(date +%s)
tcsh ./compile em_hill2d_x -j 8 > "$EXP/C_compile.log" 2>&1
rc=$?; t1=$(date +%s)
log "compile[em_hill2d_x] rc=$rc elapsed=$((t1-t0))s"
ls -la main/ideal.exe main/wrf.exe >> "$EXP/SUMMARY.txt" 2>&1

# 2) 运行
cd test/em_hill2d_x || exit 1
ulimit -s unlimited
t0=$(date +%s)
./ideal.exe > "$EXP/C_ideal.log" 2>&1
rc=$?; t1=$(date +%s)
log "ideal.exe rc=$rc elapsed=$((t1-t0))s"
ls -la wrfinput_d01 >> "$EXP/SUMMARY.txt" 2>&1

t0=$(date +%s)
mpirun -np 4 ./wrf.exe > "$EXP/C_wrf.log" 2>&1
rc=$?; t1=$(date +%s)
log "wrf.exe rc=$rc elapsed=$((t1-t0))s"

grep -n 'SUCCESS COMPLETE WRF' rsl.out.0000 >> "$EXP/SUMMARY.txt" 2>&1
ls -la wrfout_d01_* >> "$EXP/SUMMARY.txt" 2>&1
cp -f rsl.out.0000 "$EXP/C_rsl.out.0000" 2>/dev/null
ncdump -h wrfout_d01_* 2>/dev/null | head -45 >> "$EXP/SUMMARY.txt"
grep -E 'Timing for main|d01 2025' "$EXP/C_rsl.out.0000" 2>/dev/null | head -8 >> "$EXP/SUMMARY.txt"

# 3) 还原 em_real 构建
cd "$WRF" || exit 1
t0=$(date +%s)
tcsh ./compile em_real -j 8 > "$EXP/C_restore.log" 2>&1
rc=$?; t1=$(date +%s)
log "restore[em_real] rc=$rc elapsed=$((t1-t0))s"
md5sum main/wrf.exe >> "$EXP/SUMMARY.txt"
md5sum -c "$EXP/md5_exe_orig.txt" >> "$EXP/SUMMARY.txt" 2>&1 || log "restore: exe md5 differs from origin"
log "=========== SMOKE JOB DONE ==========="