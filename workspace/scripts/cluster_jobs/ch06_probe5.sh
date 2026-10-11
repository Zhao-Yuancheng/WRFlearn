#!/bin/bash
# ch06 勘察：共享目录全貌 + GEOG 自定义数据 + 作业进度
echo '===LIUYL17-SHARE-ROOT==='
ls /data/groups/lzu_public/home/share/liuyl17/ 2>/dev/null | head -40
echo '===ERA5-DIR-ALL==='
ls /data/groups/lzu_public/home/share/liuyl17/ERA5_2025/ | tail -20
echo '===Y2050-IN-GEOG==='
ls /opt/app/wrf/WPS_GEOG/ | grep -i 'y2050\|urban' | head
echo '===GEOG-FIRST-40==='
ls /opt/app/wrf/WPS_GEOG/ | head -40
echo '===JOB-439342==='
sacct -j 439342 --format=JobID,JobName,State,Elapsed,ExitCode 2>/dev/null | head -5
squeue -u zhyuancheng2025 2>/dev/null | head -4
tail -8 /users/zhyuancheng2025/IceLake/ch05_exp/SUMMARY.txt 2>/dev/null
echo '===DONE==='