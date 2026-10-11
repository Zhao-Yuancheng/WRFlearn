#!/bin/bash
# 容器内载荷：ch08 restart 输出实验 A 段（rst1 秒制 vs rst1b 分钟制）
set +u
export ME=IceLake
source /users/zhyuancheng2025/IceLake/wrf-4.8/env-wrf-oneapi.sh
set -u
ulimit -s unlimited 2>/dev/null || true
CASE=/users/zhyuancheng2025/IceLake/wrf-4.8/cases/lanzhou2025/wrf
EXP=/users/zhyuancheng2025/IceLake/ch08_exp
RUN=$EXP/rst_case
EXP_SUM=$EXP/SUMMARY_rst.txt
mkdir -p "$RUN"
cd "$CASE" || exit 1
excl='namelist* wrfout_* wrfrst_* rsl* *.log slurm-* core.* *.out *.canonical'
for f in *; do
  [ -e "$f" ] || continue
  skip=0
  for p in $excl; do case "$f" in $p) skip=1 ;; esac; done
  [ "$skip" -eq 1 ] && continue
  if [ -L "$f" ]; then ln -sf "$(readlink -f "$f")" "$RUN/$f"
  else ln -sf "$CASE/$f" "$RUN/$f"; fi
done
cd "$RUN" || exit 1
log(){ echo "[$(date +%F' '%H:%M:%S)] $*" >> "$EXP_SUM"; }
log "=========== CH08 RST-A JOB START (container) ==========="

run_case(){
  local name=$1 nml=$2 np=$3 t0 t1 rc
  cp -f "$EXP/$nml" ./namelist.input
  rm -f wrfout_* wrfrst_* 2>/dev/null || true
  t0=$(date +%s)
  mpirun -np "$np" ./wrf.exe > "wrf_${name}.log" 2>&1
  rc=$?; t1=$(date +%s)
  mkdir -p "$EXP/files_${name}"
  cp -f wrfrst_* "$EXP/files_${name}/" 2>/dev/null || true
  {
    echo "### ${name}: np=${np} rc=${rc} elapsed=$((t1-t0))s"
    echo "--- SUCCESS count ---"; grep -c "SUCCESS COMPLETE WRF" rsl.out.0000 2>/dev/null
    echo "--- restart 相关行 ---"; grep -i "restart" rsl.out.0000 2>/dev/null | head -8
    echo "--- wrfrst 清单 ---"; ls -la wrfrst_* 2>/dev/null
    echo "--- wrfout 清单 ---"; ls -la wrfout_* 2>/dev/null
    echo "--- 尾部 main Timing ---"; grep "Timing for main" rsl.out.0000 2>/dev/null | tail -3
  } >> "$EXP_SUM" 2>&1
  cp -f rsl.error.0000 "$EXP/rsl.${name}.error.0000" 2>/dev/null || true
  log "rst[${name}] rc=${rc} elapsed=$((t1-t0))s"
}

run_case rst1  namelist.input.rst1  8
run_case rst1b namelist.input.rst1b 8

log "=========== CH08 RST-A JOB DONE ==========="