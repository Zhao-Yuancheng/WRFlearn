#!/bin/bash
# 容器内载荷：ch09b —— io2c（use_netcdf_classic）补测 + io11 / io102 输出保留副本
set +u
export ME=IceLake
source /users/zhyuancheng2025/IceLake/wrf-4.8/env-wrf-oneapi.sh
set -u
ulimit -s unlimited 2>/dev/null || true
EXP=/users/zhyuancheng2025/IceLake/ch09_exp
RUN=$EXP/case
cd "$RUN" || exit 1
log(){ echo "[$(date +%F' '%H:%M:%S)] $*" >> "$EXP/SUMMARY.txt"; }
log "=========== CH09B JOB START (container) ==========="

run_case(){
  local name=$1 nml=$2 np=$3 t0 t1 rc
  cp -f "$EXP/$nml" ./namelist.input
  rm -f wrfout_* wrfrst_* 2>/dev/null || true
  t0=$(date +%s)
  mpirun -np "$np" ./wrf.exe > "wrf_${name}.log" 2>&1
  rc=$?; t1=$(date +%s)
  mkdir -p "$EXP/files_${name}"
  cp -f wrfout_* "$EXP/files_${name}/" 2>/dev/null || true
  {
    echo "### ${name}: np=${np} rc=${rc} elapsed=$((t1-t0))s"
    echo "--- 分解 ---"; grep -m2 'Ntasks in X' rsl.out.0000 2>/dev/null
    echo "--- SUCCESS count ---"; grep -c "SUCCESS COMPLETE WRF" rsl.out.0000 2>/dev/null
    echo "--- 写盘 Timing ---"; grep "Timing for Writing" rsl.out.0000 2>/dev/null
    echo "--- classic 提示 ---"; grep -i "classic NetCDF" rsl.out.0000 rsl.error.0000 2>/dev/null | head -3
    echo "--- 输出清单 ---"; ls -la wrfout_* 2>/dev/null
    echo "--- 魔数（前 4 字节）---"
    for f in wrfout_*; do
      [ -f "$f" ] && echo "$f : $(head -c 4 "$f" | od -An -tx1)"
    done
  } >> "$EXP/SUMMARY.txt" 2>&1
  cp -f rsl.error.0000 "$EXP/rsl.${name}.error.0000" 2>/dev/null || true
  log "io[${name}] rc=${rc} elapsed=$((t1-t0))s"
}

run_case io2c  namelist.input.io2c  8
run_case io11  namelist.input.io11  8
run_case io102 namelist.input.io102 8

log "=========== CH09B JOB DONE ==========="