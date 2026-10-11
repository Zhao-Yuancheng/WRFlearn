#!/bin/bash
# 诊断 4：容器内工具路径 + WPS 第二次结果
echo '===CONTAINER-TOOLS==='
singularity exec --bind /users:/users,/data:/data /users/zhyuancheng2025/oneapi.sif /bin/bash -c 'echo PATH=$PATH; ls /opt/ 2>&1 | head; echo ---; ls /opt/condabin 2>&1 | head; echo ---; which tcsh m4 2>&1; ls /bin/*csh /usr/bin/*csh 2>&1'
echo '===CONTAINER-LOGIN-SHELL==='
singularity exec /users/zhyuancheng2025/oneapi.sif /bin/bash -lc 'echo PATH=$PATH; which tcsh; tcsh --version | head -1' 2>&1 | head -8
echo '===WPS-SUMMARY-2ND==='
head -50 /users/zhyuancheng2025/IceLake/ch06_exp/SUMMARY.txt 2>/dev/null
echo '===WPS-CASE-DIR==='
ls -la /users/zhyuancheng2025/IceLake/wrf-4.8/cases/lanzhou2025/wps/ 2>/dev/null | head -30
echo '===GEOGRID-LOG-TAIL==='
tail -25 /users/zhyuancheng2025/IceLake/wrf-4.8/cases/lanzhou2025/wps/geogrid.log 2>/dev/null
echo '===UNGRID-LOG-TAIL==='
tail -15 /users/zhyuancheng2025/IceLake/wrf-4.8/cases/lanzhou2025/wps/ungrib.log 2>/dev/null
echo '===METGRID-LOG-HEAD==='
head -30 /users/zhyuancheng2025/IceLake/wrf-4.8/cases/lanzhou2025/wps/metgrid.log 2>/dev/null
echo '===DONE==='