#!/bin/bash
# ch05 勘察 2：构建状态与工具可用性
cd /users/zhyuancheng2025/IceLake/wrf-4.8/build/WRF || exit 1
echo '===compile.log head/tail==='
head -6 compile.log 2>/dev/null
grep -n 'build started\|build completed' compile.log 2>/dev/null | head -4
tail -4 compile.log 2>/dev/null
echo '===tools==='
which tcsh; which mpirun; which ifx
echo '===timestamps==='
ls -la Registry/Registry frame/module_state_description.F main/wrf.exe phys/module_ra_rrtmg_lw.F phys/module_ra_rrtmg_lw.o 2>&1
echo '===hill2d case files==='
ls test/em_hill2d_x/ | head -20
echo '===em_real test dir links==='
ls -la test/em_real/ | grep -E 'wrf.exe|real.exe|ideal.exe|namelist' | head -8
echo '===DONE==='