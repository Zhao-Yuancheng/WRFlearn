#!/bin/bash
# ch06 勘察：WPS 选项与 GRIB 子集工具
echo '===NAMELIST-WPS-ALL-OPTIONS (ungrib 段) ==='
sed -n '/&ungrib/,/^\//p' /users/zhyuancheng2025/IceLake/wrf-4.8/build/WPS/namelist.wps.all_options 2>/dev/null | head -40
echo '===NAMELIST-WPS-DEFAULT==='
cat /users/zhyuancheng2025/IceLake/wrf-4.8/build/WPS/namelist.wps 2>/dev/null
echo '===CONDA-ENVS==='
ls ~/miniforge3/envs/ 2>/dev/null
echo '===GRIB-TOOLS-IN-ENVS==='
ls ~/miniforge3/envs/*/bin/grib_copy ~/miniforge3/envs/*/bin/wgrib2 ~/miniforge3/envs/*/bin/cdo 2>/dev/null
find ~/miniforge3 -maxdepth 4 -name 'grib_copy' -o -maxdepth 4 -name 'wgrib2' 2>/dev/null | head
echo '===VTABLE-ECMWF-HEAD==='
head -30 /users/zhyuancheng2025/IceLake/wrf-4.8/build/WPS/ungrib/Variable_Tables/Vtable.ECMWF
echo '===DONE==='