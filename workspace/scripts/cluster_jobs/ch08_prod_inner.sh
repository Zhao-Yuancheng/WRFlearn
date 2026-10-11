#!/bin/bash
# 容器内载荷：ch08 生产作业（自适应核数）：先短测 np64，通过则 np64 跑 5 天；否则 np16 跑 5 天
set +u
export ME=IceLake
source /users/zhyuancheng2025/IceLake/wrf-4.8/env-wrf-oneapi.sh
set -u
ulimit -s unlimited 2>/dev/null || true
CASE=/users/zhyuancheng2025/IceLake/wrf-4.8/cases/lanzhou2025/wrf
EXP=/users/zhyuancheng2025/IceLake/ch08_exp
cd "$CASE" || exit 1
log(){ echo "[$(date +%F' '%H:%M:%S)] $*" >> "$EXP/SUMMARY.txt"; }

log "=========== PROD JOB START (container) ==========="
cp -p namelist.input ./namelist.canonical

# 清理 10 分钟短测的残留输出（可重建的实验产物）
rm -f wrfout_d01_2025-07-12_00:10* wrfout_d02_2025-07-12_00:10* 2>/dev/null || true

# 阶段 1：短测 np=64（定位 64 核分解是否复发）
cp -f "$EXP/namelist.input.short" ./namelist.input
t0=$(date +%s)
mpirun -np 64 ./wrf.exe > wrf_expD_np64.log 2>&1
rcd=$?; t1=$(date +%s)
grep -c "SUCCESS COMPLETE WRF" rsl.out.0000 2>/dev/null >> "$EXP/SUMMARY.txt"
log "expD(short@np64) rc=$rcd elapsed=$((t1-t0))s"

# 阶段 2：生产运行（按短测结果选核数）
cp -f ./namelist.canonical ./namelist.input
if [ "$rcd" -eq 0 ]; then NP=64; else NP=16; fi
log "PRODUCTION RUN with np=$NP (1) 5 天模拟开始"
t0=$(date +%s)
mpirun -np "$NP" ./wrf.exe > "wrf_prod_np${NP}.log" 2>&1
rcp=$?; t1=$(date +%s)
log "PRODUCTION np=$NP rc=$rcp elapsed=$((t1-t0))s"

{
  echo "--- SUCCESS check (np=$NP) ---"
  grep -c "SUCCESS COMPLETE WRF" rsl.out.0000 2>/dev/null
  echo "--- rsl.out tail ---"
  tail -6 rsl.out.0000 2>/dev/null
  echo "--- vtune-style timing block ---"
  grep -A20 "Timing for main: time 2025-07-16_23" rsl.out.0000 2>/dev/null | tail -12
  echo "--- outputs ---"
  ls -la wrfout_d01_* wrfout_d02_* wrfrst_d01_* wrfrst_d02_* 2>&1 | head -25
  echo "--- disk ---"
  du -sh "$CASE"
} >> "$EXP/SUMMARY.txt" 2>&1

log "=========== PROD JOB DONE ==========="