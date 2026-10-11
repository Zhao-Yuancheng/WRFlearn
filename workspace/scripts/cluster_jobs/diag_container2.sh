#!/bin/bash
# 诊断 2：容器路径与既有构建脚本
echo '===MD5-ORIG==='
cat /users/zhyuancheng2025/IceLake/ch05_exp/md5_exe_orig.txt 2>/dev/null
cat /users/zhyuancheng2025/IceLake/ch05_exp/md5_before_smoke.txt 2>/dev/null
echo '===A1-LOG-HEAD==='
head -33 /users/zhyuancheng2025/IceLake/ch05_exp/A1_compile.log 2>/dev/null
echo '===HOST-IFX==='
ls /opt/intel/oneapi/ 2>/dev/null | head -10
bash -c 'source /opt/intel/oneapi/setvars.sh >/dev/null 2>&1; which ifx; ifx --version 2>/dev/null | head -2' 2>&1 | head -6
echo '===FIND-SIF==='
find /users/zhyuancheng2025 -maxdepth 4 -name '*.sif' 2>/dev/null | head
ls -la /users/zhyuancheng2025/IceLake/wrf-4.8/*.sif 2>/dev/null
echo '===ADMIN-BUILD-SIF (head 70)==='
head -70 /users/zhyuancheng2025/IceLake/wrf-4.8/image-stage/admin-build-sif.sh 2>/dev/null
echo '===BUILD-WPS.SH==='
cat /users/zhyuancheng2025/IceLake/wrf-4.8/image-stage/build-wps.sh 2>/dev/null
echo '===LOG-REBUILD-WPS==='
head -40 /users/zhyuancheng2025/IceLake/wrf-4.8/log.rebuild-wps 2>/dev/null
echo '===DONE==='