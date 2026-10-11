#!/bin/bash
# 容器内载荷：恢复被宿主编译破坏的构建树（重编被宿主污染的 16 个对象 + 重链接 exe）
set +u
export ME=IceLake
source /users/zhyuancheng2025/IceLake/wrf-4.8/env-wrf-oneapi.sh
export PATH=/users/zhyuancheng2025/IceLake/wrf-4.8/tools/tcsh-extract/bin:$PATH   # 离线解包的 tcsh
set -u
command -v tcsh >/dev/null || { echo "tcsh missing" >> /users/zhyuancheng2025/IceLake/ch05_exp/SUMMARY_RECOVER.txt; exit 9; }
tcsh --version 2>&1 | head -1 >> /users/zhyuancheng2025/IceLake/ch05_exp/SUMMARY_RECOVER.txt
WRF=/users/zhyuancheng2025/IceLake/wrf-4.8/build/WRF
EXP=/users/zhyuancheng2025/IceLake/ch05_exp
cd "$WRF" || exit 1
log(){ echo "[$(date +%F' '%H:%M:%S)] $*" >> "$EXP/SUMMARY_RECOVER.txt"; }

log "RECOVER START (container)"
{
  echo "ifx: $(which ifx)"
  ifx --version 2>/dev/null | head -1
} >> "$EXP/SUMMARY_RECOVER.txt" 2>&1

# 1) 生成物已 md5 验证为原始内容；把 Registry/Registry 时间设为旧，避免本轮重生成
touch -d '2026-10-04 01:44:00' Registry/Registry

# 2) 把宿主污染过的对象对应源码 touch 一遍（强制容器内重编）
cat "$EXP/A1_objects.txt" "$EXP/B1_objects.txt" "$EXP/B2_objects.txt" 2>/dev/null \
  | sed 's|^\./||' | sort -u > "$EXP/objlist.txt"
n=0
while read -r o; do
  [ -z "$o" ] && continue
  base="${o%.o}"
  for ext in F f90 F90 c; do
    if [ -f "$base.$ext" ]; then touch "$base.$ext"; n=$((n+1)); fi
  done
done < "$EXP/objlist.txt"
log "touched sources: $n (from $(wc -l < "$EXP/objlist.txt") objects)"

# 3) 容器内重编 + 重链接
t0=$(date +%s)
tcsh ./compile em_real -j 8 > "$EXP/recover_compile.log" 2>&1
rc=$?; t1=$(date +%s)
log "recover compile rc=$rc elapsed=$((t1-t0))s"

# 4) 一致性验证
ls -la main/*.exe >> "$EXP/SUMMARY_RECOVER.txt" 2>&1
md5sum main/*.exe >> "$EXP/SUMMARY_RECOVER.txt" 2>&1
md5sum -c "$EXP/md5_exe_orig.txt" >> "$EXP/SUMMARY_RECOVER.txt" 2>&1 \
  && log "exe md5: ALL MATCH original" || log "exe md5: MISMATCH"
grep -c 'undefined reference' "$EXP/recover_compile.log" >> "$EXP/SUMMARY_RECOVER.txt" 2>&1
log "RECOVER DONE"