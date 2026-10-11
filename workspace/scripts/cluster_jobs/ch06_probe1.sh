#!/bin/bash
# ch05/ch06 勘察：作业状态 + ERA5 数据 + WPS 目录
echo '===JOB-STATUS==='
squeue -j 439339 2>/dev/null
echo '===ERA5-202507==='
ls /data/groups/lzu_public/home/share/liuyl17/ERA5_2025/ | head -20
echo '---'
ls -la /data/groups/lzu_public/home/share/liuyl17/ERA5_2025/202507/ 2>/dev/null | head -40
echo '===ERA5-SIZE-SUM==='
du -sh /data/groups/lzu_public/home/share/liuyl17/ERA5_2025/202507/ 2>/dev/null
echo '===WPS-BUILD==='
ls /users/zhyuancheng2025/IceLake/wrf-4.8/build/WPS/ | head -30
echo '---exe---'
ls -la /users/zhyuancheng2025/IceLake/wrf-4.8/build/WPS/*.exe 2>/dev/null
echo '===WPS-TABLES==='
ls /users/zhyuancheng2025/IceLake/wrf-4.8/build/WPS/geogrid/*.TBL 2>/dev/null | head
ls /users/zhyuancheng2025/IceLake/wrf-4.8/build/WPS/metgrid/*.TBL 2>/dev/null | head
ls /users/zhyuancheng2025/IceLake/wrf-4.8/build/WPS/ungrib/Variable_Tables/ 2>/dev/null | head -20
echo '===GEOG==='
ls /opt/app/wrf/WPS_GEOG/ 2>/dev/null | head -30
echo '===DONE==='