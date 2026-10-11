#!/bin/bash
# 容器内载荷：兰州个例 WPS（geogrid → ungrib → metgrid）
set +u
export ME=IceLake
source /users/zhyuancheng2025/IceLake/wrf-4.8/env-wrf-oneapi.sh
export PATH=/users/zhyuancheng2025/IceLake/wrf-4.8/tools/tcsh-extract/bin:$PATH   # 离线解包的 tcsh
set -u
WPS=/users/zhyuancheng2025/IceLake/wrf-4.8/build/WPS
CASE=/users/zhyuancheng2025/IceLake/wrf-4.8/cases/lanzhou2025/wps
EXP=/users/zhyuancheng2025/IceLake/ch06_exp
mkdir -p "$CASE" "$EXP"
cd "$CASE" || exit 1
log(){ echo "[$(date +%F' '%H:%M:%S)] $*" >> "$EXP/SUMMARY.txt"; }

log "=========== WPS LZ JOB START (container) ==========="
cp -f "$EXP/namelist.wps" ./namelist.wps || { log "namelist.wps missing"; exit 1; }

ln -sf "$WPS/geogrid/GEOGRID.TBL.ARW" ./GEOGRID.TBL
ln -sf "$WPS/metgrid/METGRID.TBL.ARW" ./METGRID.TBL
ln -sf "$WPS/ungrib/Variable_Tables/Vtable.ECMWF" ./Vtable

rm -f GRIBFILE.*
ln -sf /data/groups/lzu_public/home/share/liuyl17/ERA5_2025/ERA5202507.grib        ./GRIBFILE.AAA
ln -sf /data/groups/lzu_public/home/share/liuyl17/ERA5_2025/ERA5_surface.202507.grib ./GRIBFILE.AAB
log "GRIBFILE count: $(ls GRIBFILE.* 2>/dev/null | wc -l)"

t0=$(date +%s)
"$WPS/geogrid.exe" > geogrid.log 2>&1
rc=$?; t1=$(date +%s)
log "geogrid rc=$rc elapsed=$((t1-t0))s"

t0=$(date +%s)
"$WPS/ungrib.exe" > ungrib.log 2>&1
rc=$?; t1=$(date +%s)
log "ungrib rc=$rc elapsed=$((t1-t0))s"
log "FILE count: $(ls FILE:* 2>/dev/null | wc -l)"
grep -iE 'cannot find|missing|not found' ungrib.log | head -12 >> "$EXP/SUMMARY.txt"

t0=$(date +%s)
mpirun -np 8 "$WPS/metgrid.exe" > metgrid.log 2>&1
rc=$?; t1=$(date +%s)
log "metgrid rc=$rc elapsed=$((t1-t0))s"

log "geo_em: $(ls geo_em*.nc 2>/dev/null | tr '\n' ' ')"
log "met_em count: $(ls met_em* 2>/dev/null | wc -l)"
ls -la geo_em*.nc 2>/dev/null >> "$EXP/SUMMARY.txt"
ls met_em* 2>/dev/null | sort | head -60 >> "$EXP/SUMMARY.txt"
du -sh "$CASE" >> "$EXP/SUMMARY.txt" 2>&1
head -60 metgrid.log >> "$EXP/SUMMARY.txt" 2>&1
ncdump -h geo_em.d01.nc 2>/dev/null | head -45 >> "$EXP/SUMMARY.txt"
ncdump -h met_em.d01.2025-07-12_00:00:00.nc 2>/dev/null | head -70 >> "$EXP/SUMMARY.txt"
log "=========== WPS JOB DONE ==========="