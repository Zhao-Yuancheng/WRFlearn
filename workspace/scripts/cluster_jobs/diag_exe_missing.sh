#!/bin/bash
# 诊断：exe 缺失原因 + 容器/glibc 环境
cd /users/zhyuancheng2025/IceLake/wrf-4.8/build/WRF || exit 1
echo '===MAIN-DIR==='
ls -la main/ | head -20
echo '===EXE-CHECK==='
ls -la main/*.exe 2>&1
echo '===LIBWRFLIB==='
ls -la main/libwrflib.a 2>&1
echo '===ZAP in compile==='
grep -n 'ZAP' compile | head
echo '===A1 log: link/error lines==='
grep -nE 'ld: |Error|error:|undefined|cannot find' /users/zhyuancheng2025/IceLake/ch05_exp/A1_compile.log | head -30
echo '===A1 log tail 40==='
tail -40 /users/zhyuancheng2025/IceLake/ch05_exp/A1_compile.log
echo '===B2 log tail 30==='
tail -30 /users/zhyuancheng2025/IceLake/ch05_exp/B2_compile.log
echo '===GLIBC-LOGIN==='
ldd --version | head -2
echo '===OPT-INTEL==='
ls /opt/intel 2>&1 | head -5
echo '===SINGULARITY==='
which singularity apptainer 2>&1
echo '===IMAGE-STAGE==='
ls -la /users/zhyuancheng2025/IceLake/wrf-4.8/image-stage/ 2>/dev/null | head -20
echo '===DONE==='