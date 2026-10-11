#!/bin/bash
# 容器内载荷：ch08 辐射崩溃诊断（三连短测，每次 10 分钟）
set +u
export ME=IceLake
source /users/zhyuancheng2025/IceLake/wrf-4.8/env-wrf-oneapi.sh
set -u
ulimit -s unlimited 2>/dev/null || true
CASE=/users/zhyuancheng2025/IceLake/wrf-4.8/cases/lanzhou2025/wrf
EXP=/users/zhyuancheng2025/IceLake/ch08_exp
cd "$CASE" || exit 1
log(){ echo "[$(date +%F' '%H:%M:%S)] $*" >> "$EXP/SUMMARY.txt"; }

log "=========== DIAG JOB START (container) ==========="
cp -f namelist.input ./namelist.input.canonical.bak

run_case(){
  local name=$1 nml=$2 np=$3 t0 t1 rc
  cp -f "$nml" ./namelist.input
  t0=$(date +%s)
  mpirun -np "$np" ./wrf.exe > "wrf_${name}.log" 2>&1
  rc=$?; t1=$(date +%s)
  {
    echo "### ${name}: np=${np} rc=${rc} elapsed=$((t1-t0))s"
    echo "--- rsl.out.0000 tail ---"
    tail -8 rsl.out.0000 2>/dev/null
    echo "--- SUCCESS grep ---"
    grep -c "SUCCESS COMPLETE WRF" rsl.out.0000 2>/dev/null
  } >> "$EXP/SUMMARY.txt"
  cp -f rsl.error.0000 "$EXP/${name}_rsl.error.0000" 2>/dev/null
  log "diag[${name}] rc=${rc} elapsed=$((t1-t0))s"
}

# A: 旧辐射 RRTM/Dudhia（ra=1），np=64
run_case expA_ra1 "$EXP/namelist.input.exp1" 64

# B: RRTMG（ra=4）单进程，np=1
run_case expB_rrtmg_np1 "$EXP/namelist.input.short" 1

# C: RRTMG（ra=4）16 进程，np=16
run_case expC_rrtmg_np16 "$EXP/namelist.input.short" 16

# 还原 canonical
cp -f ./namelist.input.canonical.bak ./namelist.input
log "=========== DIAG JOB DONE ==========="