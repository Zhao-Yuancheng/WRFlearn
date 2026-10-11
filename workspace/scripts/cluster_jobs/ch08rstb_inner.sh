#!/bin/bash
# 容器内载荷：ch08 rst-B 段 —— ①两域短测 np64（崩溃复查）②两域 rst 演示 np8 ③断点续跑 np8
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
log "=========== CH08 RST-B JOB START (container) ==========="

run_case(){
  local name=$1 nml=$2 np=$3 t0 t1 rc
  cp -f "$EXP/$nml" ./namelist.input
  rm -f wrfout_* wrfrst_* 2>/dev/null || true
  t0=$(date +%s)
  mpirun -np "$np" ./wrf.exe > "wrf_${name}.log" 2>&1
  rc=$?; t1=$(date +%s)
  mkdir -p "$EXP/files_${name}"
  cp -f wrfrst_* wrfout_* "$EXP/files_${name}/" 2>/dev/null || true
  {
    echo "### ${name}: np=${np} rc=${rc} elapsed=$((t1-t0))s"
    echo "--- 嵌套激活行 ---"; grep -E "Nesting domain|Initializing nest domain|Domain # 2" rsl.out.0000 2>/dev/null | head -6
    echo "--- d02 步数 ---"; grep -c "domain   2" rsl.out.0000 2>/dev/null
    echo "--- SUCCESS count ---"; grep -c "SUCCESS COMPLETE WRF" rsl.out.0000 2>/dev/null
    echo "--- 写盘/重启 Timing ---"; grep "Timing for Writing" rsl.out.0000 2>/dev/null
    echo "--- wrfrst 清单 ---"; ls -la wrfrst_* 2>/dev/null
    echo "--- wrfout 清单 ---"; ls -la wrfout_* 2>/dev/null
    if [ "$rc" -ne 0 ]; then
      echo "--- 失败 rsl.error.0000 尾部 40 行 ---"
      tail -40 rsl.error.0000 2>/dev/null
    fi
  } >> "$EXP_SUM" 2>&1
  cp -f rsl.error.0000 "$EXP/rsl.${name}.error.0000" 2>/dev/null || true
  log "rst[${name}] rc=${rc} elapsed=$((t1-t0))s"
}

# ① 两域短测 np64（修复 end_minute 后；复查 np64 是否复现段错误）
run_case r2dom64 namelist.input.rst1d 64

# ② 两域 rst 演示 np8（应产出 d01+d02 的 wrfrst）
run_case r1dom8 namelist.input.rst1d 8

# ③ 断点续跑 np8（起点 = rst 时间戳 00:05:24）
log "在前置检查: $(ls wrfrst_d01_* wrfrst_d02_* 2>/dev/null | tr '\n' ' ')"
run_case r3restart8 namelist.input.rst2 8

log "=========== CH08 RST-B JOB DONE ==========="