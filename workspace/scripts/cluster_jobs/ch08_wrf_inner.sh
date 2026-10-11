#!/bin/bash
# 容器内载荷：兰州个例 5 天模拟（2025-07-12_00Z → 07-17_00Z，两域，64 进程）
set +u
export ME=IceLake
source /users/zhyuancheng2025/IceLake/wrf-4.8/env-wrf-oneapi.sh
set -u
CASE=/users/zhyuancheng2025/IceLake/wrf-4.8/cases/lanzhou2025/wrf
EXP=/users/zhyuancheng2025/IceLake/ch08_exp
cd "$CASE" || exit 1
mkdir -p "$EXP"
log(){ echo "[$(date +%F' '%H:%M:%S)] $*" >> "$EXP/SUMMARY.txt"; }

log "=========== CH08 WRF JOB START (container) ==========="
log "inputs: wrfinput=$(ls -la wrfinput_d01 | awk '{print $5}') wrfbdy=$(ls -la wrfbdy_d01 | awk '{print $5}')"
log "namelist restart flag: $(grep '^ restart' namelist.input | head -1 | tr -d ' ')"

t0=$(date +%s)
mpirun -np 64 ./wrf.exe > wrf.log 2>&1
rc=$?; t1=$(date +%s)
log "wrf rc=$rc elapsed=$((t1-t0))s"

{
  echo "--- SUCCESS line check ---"
  grep -l "SUCCESS COMPLETE WRF" rsl.out.* 2>/dev/null | head -5
  echo "--- rsl.out.0000 tail ---"
  tail -12 rsl.out.0000 2>/dev/null
  echo "--- timing from rsl (tail) ---"
  grep -iE "Timing for main|wrf: SUCCESS" rsl.out.0000 2>/dev/null | tail -8
  echo "--- wrfout / restart files ---"
  ls -la wrfout_d01_* wrfout_d02_* wrfrst_d01_* wrfrst_d02_* 2>&1 | head -20
  echo "--- disk usage ---"
  du -sh "$CASE" 2>/dev/null
} >> "$EXP/SUMMARY.txt" 2>&1

log "=========== CH08 WRF JOB DONE ==========="