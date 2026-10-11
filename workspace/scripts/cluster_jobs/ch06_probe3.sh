#!/bin/bash
# 作业失败后状态核查 + 参考个例抓取
echo '===CH05EXP-DIR==='
ls -la /users/zhyuancheng2025/IceLake/ch05_exp/ 2>/dev/null
echo '===TREE-STATE==='
cd /users/zhyuancheng2025/IceLake/wrf-4.8/build/WRF
ls -la --time-style=full-iso Registry/Registry.EM_COMMON phys/module_ra_rrtmg_lw.F main/wrf.exe 2>&1
md5sum Registry/Registry.EM_COMMON
echo '===HAIDIAN-NAMELIST-WPS==='
cat /data/groups/lzu_public/home/share/liuyl17/haidian2024/namelist.wps
echo '===HAIDIAN-NAMELIST-INPUT-HEAD==='
head -80 /data/groups/lzu_public/home/share/liuyl17/haidian2024/namelist.input
echo '===DONE==='