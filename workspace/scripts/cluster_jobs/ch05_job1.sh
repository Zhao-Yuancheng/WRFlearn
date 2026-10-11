#!/bin/bash
#SBATCH -J ch05_exp
#SBATCH -p cpu
#SBATCH -N 1
#SBATCH -n 1
#SBATCH -c 8
#SBATCH -t 02:30:00
#SBATCH -o /users/zhyuancheng2025/IceLake/ch05_exp/slurm-%j.out

# ch05 集群实测 Job1：
#   A1/A2 叶子模块注释级改动 → 增量重编译计时 + 二进制一致性
#   B0    演示"改 EM_COMMON 但 make 不知情"的触发陷阱（dry-run）
#   B1    加 T2_PEAK（ch04 图纸）→ 真实重编译计时 + 生成物证据
#   B2    还原 → 重编译计时 + 全部 md5 还原验证
set +u
export ME=IceLake
source /users/zhyuancheng2025/IceLake/wrf-4.8/env-wrf-oneapi.sh
set -u
WRF=/users/zhyuancheng2025/IceLake/wrf-4.8/build/WRF
EXP=/users/zhyuancheng2025/IceLake/ch05_exp
mkdir -p "$EXP"
cd "$WRF" || exit 1

log(){ echo "[$(date +%F' '%H:%M:%S)] $*" >> "$EXP/SUMMARY.txt"; }

# ---------- 备份 ----------
cp -p phys/module_ra_rrtmg_lw.F "$EXP/rrtmg_lw.F.orig"
cp -p phys/module_ra_rrtmg_lw.o "$EXP/rrtmg_lw.o.orig"
cp -p Registry/Registry.EM_COMMON "$EXP/EM_COMMON.orig"
md5sum main/wrf.exe main/real.exe main/ndown.exe main/tc.exe > "$EXP/md5_exe_orig.txt"
md5sum inc/state_struct.inc inc/allocs_1.F frame/module_state_description.F inc/i1_decl.inc > "$EXP/md5_gen_orig.txt"
md5sum phys/module_ra_rrtmg_lw.o > "$EXP/md5_obj_orig.txt"
ls -l --time-style=full-iso frame/module_state_description.F Registry/Registry main/wrf.exe > "$EXP/mtime_before.txt"

restore_src(){
  cp -p "$EXP/rrtmg_lw.F.orig" phys/module_ra_rrtmg_lw.F
  cp -p "$EXP/EM_COMMON.orig" Registry/Registry.EM_COMMON
  log "[restore] source files restored to original content"
}
trap 'restore_src' EXIT TERM

compile(){
  local name=$1
  local t0 t1 rc nnew
  touch "$EXP/stamp_$name"
  t0=$(date +%s)
  tcsh ./compile em_real -j 8 > "$EXP/${name}_compile.log" 2>&1
  rc=$?
  t1=$(date +%s)
  nnew=$(find . -name '*.o' -newer "$EXP/stamp_$name" 2>/dev/null | grep -v '^\./var/' | wc -l)
  log "compile[$name] rc=$rc elapsed=$((t1-t0))s rebuilt_objects=$nnew"
  find . -name '*.o' -newer "$EXP/stamp_$name" 2>/dev/null | grep -v '^\./var/' | head -40 > "$EXP/${name}_objects.txt"
  grep -iE '\berror\b|Error 1' "$EXP/${name}_compile.log" | grep -v ignored | head -5 >> "$EXP/SUMMARY.txt"
}

log "=========== EXP A1: leaf module comment change ==========="
echo "! ch05 experiment: harmless comment appended $(date)" >> phys/module_ra_rrtmg_lw.F
compile A1
md5sum phys/module_ra_rrtmg_lw.o main/wrf.exe >> "$EXP/SUMMARY.txt"
md5sum -c "$EXP/md5_obj_orig.txt" >> "$EXP/SUMMARY.txt" 2>&1 || log "A1: object md5 differs"
md5sum -c "$EXP/md5_exe_orig.txt" >> "$EXP/SUMMARY.txt" 2>&1 || log "A1: exe md5 differs"

log "=========== EXP A2: revert leaf module ==========="
cp -p "$EXP/rrtmg_lw.F.orig" phys/module_ra_rrtmg_lw.F
compile A2
md5sum phys/module_ra_rrtmg_lw.o main/wrf.exe >> "$EXP/SUMMARY.txt"
md5sum -c "$EXP/md5_exe_orig.txt" >> "$EXP/SUMMARY.txt" 2>&1 || log "A2: exe md5 differs"

log "=========== EXP B0: dry-run BEFORE touch (trigger pitfall) ==========="
printf '%s\n' 'state    real   T2_PEAK   ij   misc   1   -   rhd   "T2_PEAK"   "2 M TEMPERATURE MAXIMUM SINCE INITIALIZATION"   "K"' >> Registry/Registry.EM_COMMON
make -n -i -r em_real > "$EXP/B0_dryrun.log" 2>&1
log "B0: registry_cmds_in_dryrun=$(grep -c 'tools/registry' "$EXP/B0_dryrun.log")"

log "=========== EXP B1: touch + real rebuild (T2_PEAK) ==========="
touch Registry/Registry
make -n -i -r em_real > "$EXP/B1a_dryrun.log" 2>&1
grep -n 'tools/registry' "$EXP/B1a_dryrun.log" | head -3 >> "$EXP/SUMMARY.txt"
compile B1
log "B1 evidence:"
grep -n 't2_peak' inc/state_struct.inc 2>/dev/null | head -3 >> "$EXP/SUMMARY.txt"
grep -rn "in_use_for_config(id,'t2_peak')" inc/allocs_*.F 2>/dev/null | head -3 >> "$EXP/SUMMARY.txt"
grep -rn "DataName = 'T2_PEAK'" inc/allocs_*.F 2>/dev/null | head -3 >> "$EXP/SUMMARY.txt"
grep -rn 'T2_PEAK' frame/module_state_description.F 2>/dev/null | head -3 >> "$EXP/SUMMARY.txt"

log "=========== EXP B2: revert registry + rebuild ==========="
cp -p "$EXP/EM_COMMON.orig" Registry/Registry.EM_COMMON
touch Registry/Registry
compile B2
md5sum -c "$EXP/md5_gen_orig.txt" >> "$EXP/SUMMARY.txt" 2>&1 || log "B2: generated md5 mismatch"
md5sum -c "$EXP/md5_exe_orig.txt" >> "$EXP/SUMMARY.txt" 2>&1 || log "B2: exe md5 mismatch"

log "=========== JOB1 DONE ==========="
ls -l --time-style=full-iso main/*.exe >> "$EXP/SUMMARY.txt"