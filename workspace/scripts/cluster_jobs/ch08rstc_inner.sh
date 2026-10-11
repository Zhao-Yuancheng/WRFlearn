#!/bin/bash
# 容器内载荷：ch08 rst-C —— 断点续跑（恢复 r1dom8 的 rst 文件后 restart=.true. 读回，不清 rst）
set +u
export ME=IceLake
source /users/zhyuancheng2025/IceLake/wrf-4.8/env-wrf-oneapi.sh
set -u
ulimit -s unlimited 2>/dev/null || true
EXP=/users/zhyuancheng2025/IceLake/ch08_exp
RUN=$EXP/rst_case
EXP_SUM=$EXP/SUMMARY_rst.txt
cd "$RUN" || exit 1
log(){ echo "[$(date +%F' '%H:%M:%S)] $*" >> "$EXP_SUM"; }
log "=========== CH08 RST-C JOB START (read rst, continue) ==========="

# 恢复 rst 文件（来自 r1dom8 备份，4 个文件），清除旧输出（不动 rst）
cp -f "$EXP"/files_r1dom8/wrfrst_d0* .
rm -f wrfout_* 2>/dev/null || true
cp -f "$EXP/namelist.input.rst2" ./namelist.input
{
  echo "--- 续跑前现场（rst 文件）---"
  ls -la wrfrst_* 2>/dev/null
  grep -E "restart|start_minute|start_second|end_minute" ./namelist.input | head -8
} >> "$EXP_SUM" 2>&1

t0=$(date +%s)
mpirun -np 8 ./wrf.exe > wrf_r3restart8b.log 2>&1
rc=$?; t1=$(date +%s)
{
  echo "### r3restart8b: np=8 rc=${rc} elapsed=$((t1-t0))s"
  echo "--- RESTART 读取相关行 ---"; grep -i "restart" rsl.out.0000 2>/dev/null | head -8
  echo "--- 嵌套激活行 ---"; grep -E "Nesting domain|Initializing nest domain|Domain # 2" rsl.out.0000 2>/dev/null | head -6
  echo "--- d02 步数 ---"; grep -c "domain   2" rsl.out.0000 2>/dev/null
  echo "--- SUCCESS count ---"; grep -c "SUCCESS COMPLETE WRF" rsl.out.0000 2>/dev/null
  echo "--- 写盘 Timing ---"; grep "Timing for Writing" rsl.out.0000 2>/dev/null
  echo "--- 首 3 行 main Timing ---"; grep "Timing for main" rsl.out.0000 2>/dev/null | head -3
  echo "--- 尾 3 行 main Timing ---"; grep "Timing for main" rsl.out.0000 2>/dev/null | tail -3
  echo "--- wrfout 清单 ---"; ls -la wrfout_* 2>/dev/null
} >> "$EXP_SUM" 2>&1
cp -f rsl.error.0000 "$EXP/rsl.r3restart8b.error.0000" 2>/dev/null || true
mkdir -p "$EXP/files_r3restart8b"
cp -f wrfout_* "$EXP/files_r3restart8b/" 2>/dev/null || true
log "rst[r3restart8b] rc=${rc} elapsed=$((t1-t0))s"
log "=========== CH08 RST-C JOB DONE ==========="