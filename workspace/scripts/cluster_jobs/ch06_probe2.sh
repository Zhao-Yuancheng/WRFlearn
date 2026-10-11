#!/bin/bash
# ch05/06 勘察：作业进度 + GRIB 工具 + 参考个例
echo '===SACCT-439339==='
sacct -j 439339 --format=JobID,JobName,State,Elapsed,ExitCode 2>/dev/null | head -6
echo '===MY-QUEUE==='
squeue -u zhyuancheng2025 2>/dev/null | head -6
echo '===JOB-LOG==='
tail -6 /users/zhyuancheng2025/IceLake/ch05_exp/slurm-439339.out 2>/dev/null
tail -12 /users/zhyuancheng2025/IceLake/ch05_exp/SUMMARY.txt 2>/dev/null
echo '===GRIB-TOOLS==='
which wgrib2 2>/dev/null; which cdo 2>/dev/null; which grib_copy 2>/dev/null; which wgrib 2>/dev/null
echo '===GRIB-SIZES==='
ls -la /data/groups/lzu_public/home/share/liuyl17/ERA5_2025/ERA5202507.grib /data/groups/lzu_public/home/share/liuyl17/ERA5_2025/ERA5_surface.202507.grib 2>&1
echo '===HAIDIAN==='
ls /data/groups/lzu_public/home/share/liuyl17/haidian2024/ 2>/dev/null | head -30
echo '===GEOG-TAIL==='
ls /opt/app/wrf/WPS_GEOG/ | tail -30
echo '===DONE==='