#!/bin/bash
# 诊断 3：恢复作业与 WPS 作业失败详情
echo '===RCV-SUMMARY-FULL==='
cat /users/zhyuancheng2025/IceLake/ch05_exp/SUMMARY_RECOVER.txt 2>/dev/null
echo '===RCV-COMPILE-LOG==='
head -40 /users/zhyuancheng2025/IceLake/ch05_exp/recover_compile.log 2>/dev/null
echo '---tail---'
tail -25 /users/zhyuancheng2025/IceLake/ch05_exp/recover_compile.log 2>/dev/null
echo '===OBJLIST==='
head -20 /users/zhyuancheng2025/IceLake/ch05_exp/objlist.txt 2>/dev/null
wc -l /users/zhyuancheng2025/IceLake/ch05_exp/objlist.txt 2>/dev/null
echo '===SLURM-439350==='
cat /users/zhyuancheng2025/IceLake/ch05_exp/slurm-439350.out 2>/dev/null | tail -20
echo '===WPS-SUMMARY-FULL==='
cat /users/zhyuancheng2025/IceLake/ch06_exp/SUMMARY.txt 2>/dev/null | head -60
echo '===WPS-CASE-DIR==='
ls -la /users/zhyuancheng2025/IceLake/wrf-4.8/cases/lanzhou2025/wps/ 2>/dev/null | head -25
echo '===METGRID-TBL-REAL==='
ls -la /users/zhyuancheng2025/IceLake/wrf-4.8/build/WPS/metgrid/*.TBL* 2>/dev/null
ls -la /users/zhyuancheng2025/IceLake/wrf-4.8/build/WPS/geogrid/*.TBL* 2>/dev/null | head
echo '===GEOGRID-LOG==='
tail -15 /users/zhyuancheng2025/IceLake/wrf-4.8/cases/lanzhou2025/wps/geogrid.log 2>/dev/null
echo '===UNGRID-LOG==='
tail -10 /users/zhyuancheng2025/IceLake/wrf-4.8/cases/lanzhou2025/wps/ungrib.log 2>/dev/null
echo '===DONE==='