#!/bin/bash
# ch06 勘察：GRIB 版本字节 + GEOGRID.TBL 默认项 + 案例目录准备检查
F=/data/groups/lzu_public/home/share/liuyl17/ERA5_2025/ERA5202507.grib
echo '===GRIB edition byte (8th byte: 1=GRIB1, 2=GRIB2) ==='
od -An -tu1 -j7 -N1 "$F"
echo '===GRIB magic ==='
head -c 8 "$F" | od -An -tc
echo '===GEOGRID.TBL default (first entries) ==='
grep -n -A4 'name=LANDUSEF' /users/zhyuancheng2025/IceLake/wrf-4.8/build/WPS/geogrid/GEOGRID.TBL | head -12
grep -n 'rel_path' /users/zhyuancheng2025/IceLake/wrf-4.8/build/WPS/geogrid/GEOGRID.TBL | head -20
echo '===METGRID.TBL head==='
grep -n -m6 'name=' /users/zhyuancheng2025/IceLake/wrf-4.8/build/WPS/metgrid/METGRID.TBL
echo '===DONE==='