#!/bin/bash
# 容器内载荷：兰州个例 real.exe（2 域，met_em → wrfinput/wrfbdy）
set +u
export ME=IceLake
source /users/zhyuancheng2025/IceLake/wrf-4.8/env-wrf-oneapi.sh
set -u
CASE=/users/zhyuancheng2025/IceLake/wrf-4.8/cases/lanzhou2025/wrf
EXP=/users/zhyuancheng2025/IceLake/ch07_exp
cd "$CASE" || exit 1
log(){ echo "[$(date +%F' '%H:%M:%S)] $*" >> "$EXP/SUMMARY.txt"; }

log "=========== CH07 REAL JOB START (container) ==========="
log "met_em count: $(ls met_em* 2>/dev/null | wc -l) | cwd=$(pwd)"

t0=$(date +%s)
mpirun -np 8 ./real.exe > real.log 2>&1
rc=$?; t1=$(date +%s)
log "real rc=$rc elapsed=$((t1-t0))s"

{
  echo "--- outputs ---"
  ls -la wrfinput_d01 wrfinput_d02 wrfbdy_d01 2>&1
  echo "--- real.log tail ---"
  tail -30 real.log
  echo "--- errors in real.log (if any) ---"
  grep -iE "error|fatal|fail" real.log | head -20
  echo "--- ncdump -h wrfinput_d01 (head) ---"
  ncdump -h wrfinput_d01 2>&1 | head -55
} >> "$EXP/SUMMARY.txt" 2>&1

log "=========== CH07 REAL JOB DONE ==========="