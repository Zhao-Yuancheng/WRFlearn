#!/bin/bash
# 容器内载荷：ch09 IO 实验（10 分钟短测 × 4 变体：io_form 2 / 11 / 102 + quilt 对照）
# 独立性：在 ch09_exp/case 内运行，符号链接复用原 case 的 exe/表文件/输入，避免与生产作业竞争
set +u
export ME=IceLake
source /users/zhyuancheng2025/IceLake/wrf-4.8/env-wrf-oneapi.sh
set -u
ulimit -s unlimited 2>/dev/null || true
CASE=/users/zhyuancheng2025/IceLake/wrf-4.8/cases/lanzhou2025/wrf
EXP=/users/zhyuancheng2025/IceLake/ch09_exp
RUN=$EXP/case
mkdir -p "$RUN"
cd "$CASE" || exit 1

# 建立独立运行目录：链接原 case 的所有符号链接（数据/表格/met_em）与真实输入文件；
# 排除日志/输出/namelist 等运行产物，绝不触碰生产作业的产物
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
log(){ echo "[$(date +%F' '%H:%M:%S)] $*" >> "$EXP/SUMMARY.txt"; }
log "=========== CH09 IO JOB START (container) ==========="

run_case(){
  local name=$1 nml=$2 np=$3 t0 t1 rc
  cp -f "$EXP/$nml" ./namelist.input
  rm -f wrfout_* wrfrst_* 2>/dev/null || true
  t0=$(date +%s)
  mpirun -np "$np" ./wrf.exe > "wrf_${name}.log" 2>&1
  rc=$?; t1=$(date +%s)
  {
    echo "### ${name}: np=${np} rc=${rc} elapsed=$((t1-t0))s"
    echo "--- 分解 ---"; grep -m3 'Ntasks in X' rsl.out.0000 2>/dev/null
    echo "--- SUCCESS count ---"; grep -c "SUCCESS COMPLETE WRF" rsl.out.0000 2>/dev/null
    echo "--- 写盘 Timing ---"; grep "Timing for Writing" rsl.out.0000 2>/dev/null
    echo "--- 尾部 main Timing ---"; grep "Timing for main" rsl.out.0000 2>/dev/null | tail -3
    echo "--- quilt 相关行 ---"; grep -i "quilt\|server task" rsl.out.0000 2>/dev/null | head -5
    echo "--- 输出清单 ---"; ls -la wrfout_* 2>/dev/null
    echo "--- 输出文件数 ---"; ls wrfout_* 2>/dev/null | wc -l
    echo "--- 魔数（前 4 字节）---"
    for f in wrfout_*; do
      [ -f "$f" ] && echo "$f : $(head -c 4 "$f" | od -An -tx1)"
    done
  } >> "$EXP/SUMMARY.txt" 2>&1
  cp -f rsl.error.0000 "$EXP/rsl.${name}.error.0000" 2>/dev/null || true
  log "io[${name}] rc=${rc} elapsed=$((t1-t0))s"
}

run_case io2   namelist.input.io2   8
run_case io11  namelist.input.io11  8
run_case io102 namelist.input.io102 8
run_case io2q  namelist.input.io2q  8

log "=========== CH09 IO JOB DONE ==========="
echo "--- final RUN dir ---" >> "$EXP/SUMMARY.txt"
ls -la "$RUN" | head -20 >> "$EXP/SUMMARY.txt" 2>&1