#!/bin/bash
#SBATCH -J wps_lz
#SBATCH -p cpu
#SBATCH -N 1
#SBATCH -n 1
#SBATCH -c 8
#SBATCH -t 02:00:00
#SBATCH -o /users/zhyuancheng2025/IceLake/ch06_exp/slurm-%j.out

# ch06 兰州个例 WPS：geogrid → ungrib → metgrid（d01 9km + d02 3km）
set +u
export ME=IceLake
source /users/zhyuancheng2025/IceLake/wrf-4.8/env-wrf-oneapi.sh
set -u
WPS=/users/zhyuancheng2025/IceLake/wrf-4.8/build/WPS
CASE=/users/zhyuancheng2025/IceLake/wrf-4.8/cases/lanzhou2025/wps
EXP=/users/zhyuancheng2025/IceLake/ch06_exp
mkdir -p "$CASE" "$EXP"
cd "$CASE" || exit 1
log(){ echo "[$(date +%F' '%H:%M:%S)] $*" >> "$EXP/SUMMARY.txt"; }

log "=========== WPS LZ JOB START ==========="
cp -f "$EXP/namelist.wps" ./namelist.wps || { log "namelist.wps missing"; exit 1; }

# 1) 表格与 Vtable
ln -sf "$WPS/geogrid/GEOGRID.TBL" ./GEOGRID.TBL
ln -sf "$WPS/metgrid/METGRID.TBL" ./METGRID.TBL
ln -sf "$WPS/ungrib/Variable_Tables/Vtable.ECMWF" ./Vtable

# 2) GRIB 链接
rm -f GRIBFILE.*
"$WPS/link_grib.csh" \
  /data/groups/lzu_public/home/share/liuyl17/ERA5_2025/ERA5202507.grib \
  /data/groups/lzu_public/home/share/liuyl17/ERA5_2025/ERA5_surface.202507.grib >> "$EXP/SUMMARY.txt" 2>&1
log "GRIBFILE count: $(ls GRIBFILE.* 2>/dev/null | wc -l)"

# 3) geogrid
t0=$(date +%s)
"$WPS/geogrid.exe" > geogrid.log 2>&1
rc=$?; t1=$(date +%s)
log "geogrid rc=$rc elapsed=$((t1-t0))s"

# 4) ungrib（整月解码，metgrid 仅取 &share 窗口内 21 个时刻）
t0=$(date +%s)
"$WPS/ungrib.exe" > ungrib.log 2>&1
rc=$?; t1=$(date +%s)
log "ungrib rc=$rc elapsed=$((t1-t0))s"
log "FILE count: $(ls FILE:* 2>/dev/null | wc -l)"
grep -iE 'cannot find|missing|not found' ungrib.log | head -10 >> "$EXP/SUMMARY.txt"

# 5) metgrid（8 进程）
t0=$(date +%s)
mpirun -np 8 "$WPS/metgrid.exe" > metgrid.log 2>&1
rc=$?; t1=$(date +%s)
log "metgrid rc=$rc elapsed=$((t1-t0))s"

# 6) 证据
log "geo_em: $(ls geo_em*.nc 2>/dev/null | tr '\n' ' ')"
log "met_em count: $(ls met_em* 2>/dev/null | wc -l)"
ls -la geo_em*.nc 2>/dev/null >> "$EXP/SUMMARY.txt"
ls met_em* 2>/dev/null | sort | head -50 >> "$EXP/SUMMARY.txt"
du -sh "$CASE" >> "$EXP/SUMMARY.txt" 2>&1
ncdump -h geo_em.d01.nc 2>/dev/null | head -40 >> "$EXP/SUMMARY.txt"
log "ncdump geo_em.d02 corner_lat:"; ncdump -v corner_lat,corner_lon geo_em.d02.nc 2>/dev/null | tail -15 >> "$EXP/SUMMARY.txt"
log "=========== WPS JOB DONE ==========="