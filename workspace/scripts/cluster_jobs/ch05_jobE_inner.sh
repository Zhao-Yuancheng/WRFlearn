#!/bin/bash
# 容器内载荷：ch05 实验（A1/A2 叶子增量；B0 触发陷阱；B1/B2 T2_PEAK 全链）
set +u
export ME=IceLake
source /users/zhyuancheng2025/IceLake/wrf-4.8/env-wrf-oneapi.sh
export PATH=/users/zhyuancheng2025/IceLake/wrf-4.8/tools/tcsh-extract/bin:$PATH   # 离线解包的 tcsh
set -u
command -v tcsh >/dev/null || { echo "tcsh missing" >> /users/zhyuancheng2025/IceLake/ch05_exp/SUMMARY_E.txt; exit 9; }
WRF=/users/zhyuancheng2025/IceLake/wrf-4.8/build/WRF
EXP=/users/zhyuancheng2025/IceLake/ch05_exp
cd "$WRF" || exit 1
log(){ echo "[$(date +%F' '%H:%M:%S)] $*" >> "$EXP/SUMMARY_E.txt"; }

log "=========== JOB E START (container) ==========="
{ echo "ifx: $(which ifx)"; ifx --version 2>/dev/null | head -1; } >> "$EXP/SUMMARY_E.txt" 2>&1

# 基线（恢复后状态）
cp -p phys/module_ra_rrtmg_lw.F "$EXP/E_rrtmg_lw.F.orig"
cp -p Registry/Registry.EM_COMMON "$EXP/E_EM_COMMON.orig"
md5sum phys/module_ra_rrtmg_lw.o > "$EXP/E_md5_obj_baseline.txt"
md5sum main/wrf.exe main/real.exe main/ndown.exe main/tc.exe > "$EXP/E_md5_exe_baseline.txt"
md5sum -c "$EXP/md5_exe_orig.txt" >> "$EXP/SUMMARY_E.txt" 2>&1 \
  && log "precondition: exe == ORIGINAL md5 (recovery OK)" \
  || log "precondition: exe != ORIGINAL md5 (see above), continue with new baseline"

restore_src(){
  cp -p "$EXP/E_rrtmg_lw.F.orig" phys/module_ra_rrtmg_lw.F
  cp -p "$EXP/E_EM_COMMON.orig" Registry/Registry.EM_COMMON
  log "[restore] source files restored"
}
trap 'restore_src' EXIT TERM

compile(){
  local name=$1 t0 t1 rc nnew
  touch "$EXP/E_stamp_$name"
  t0=$(date +%s)
  tcsh ./compile em_real -j 8 > "$EXP/E_${name}_compile.log" 2>&1
  rc=$?; t1=$(date +%s)
  nnew=$(find . -name '*.o' -newer "$EXP/E_stamp_$name" 2>/dev/null | grep -v '^\./var/' | wc -l)
  log "compile[$name] rc=$rc elapsed=$((t1-t0))s rebuilt_objects=$nnew"
  find . -name '*.o' -newer "$EXP/E_stamp_$name" 2>/dev/null | grep -v '^\./var/' | head -60 > "$EXP/E_${name}_objects.txt"
  grep -c 'undefined reference' "$EXP/E_${name}_compile.log" >> "$EXP/SUMMARY_E.txt" 2>&1
}

log "=========== A1: leaf comment change ==========="
echo "! ch05 experiment comment $(date)" >> phys/module_ra_rrtmg_lw.F
compile A1
md5sum -c "$EXP/E_md5_obj_baseline.txt" >> "$EXP/SUMMARY_E.txt" 2>&1 || log "A1: object md5 differs"
md5sum -c "$EXP/E_md5_exe_baseline.txt" >> "$EXP/SUMMARY_E.txt" 2>&1 || log "A1: exe md5 differs"

log "=========== A2: revert leaf ==========="
cp -p "$EXP/E_rrtmg_lw.F.orig" phys/module_ra_rrtmg_lw.F
compile A2
md5sum -c "$EXP/E_md5_exe_baseline.txt" >> "$EXP/SUMMARY_E.txt" 2>&1 || log "A2: exe md5 differs"

log "=========== B0: dry-run BEFORE touch ==========="
printf '%s\n' 'state    real   T2_PEAK   ij   misc   1   -   rhd   "T2_PEAK"   "2 M TEMPERATURE MAXIMUM SINCE INITIALIZATION"   "K"' >> Registry/Registry.EM_COMMON
make -n -i -r em_real > "$EXP/E_B0_dryrun.log" 2>&1
log "B0: registry_cmds_in_dryrun=$(grep -c 'tools/registry' "$EXP/E_B0_dryrun.log")"

log "=========== B1: touch + real rebuild (T2_PEAK) ==========="
touch Registry/Registry
make -n -i -r em_real > "$EXP/E_B1_dryrun.log" 2>&1
grep -n 'tools/registry' "$EXP/E_B1_dryrun.log" | head -2 > "$EXP/E_B1_registry_cmd.txt" 2>&1
compile B1
{
  echo "--- t2_peak evidence ---"
  grep -n 't2_peak' inc/state_struct.inc | head -3
  grep -rn "in_use_for_config(id,'t2_peak')" inc/allocs_*.F | head -3
  grep -rn "DataName = 'T2_PEAK'" inc/allocs_*.F | head -3
  grep -rn 'T2_PEAK' frame/module_state_description.F | head -3
  md5sum main/wrf.exe
} >> "$EXP/SUMMARY_E.txt" 2>&1

log "=========== B2: revert registry + rebuild ==========="
cp -p "$EXP/E_EM_COMMON.orig" Registry/Registry.EM_COMMON
touch Registry/Registry
compile B2
md5sum -c "$EXP/E_md5_exe_baseline.txt" >> "$EXP/SUMMARY_E.txt" 2>&1 || log "B2: exe md5 differs (vs baseline)"
md5sum -c "$EXP/md5_gen_orig.txt" >> "$EXP/SUMMARY_E.txt" 2>&1 || log "B2: generated md5 differs (vs original)"
log "=========== JOB E DONE ==========="
ls -l --time-style=full-iso main/*.exe >> "$EXP/SUMMARY_E.txt" 2>&1