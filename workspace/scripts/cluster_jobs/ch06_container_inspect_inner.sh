#!/bin/bash
# 容器内检查：tcsh 位置/thirdparty/容器环境
echo '=== PATH ==='
echo "$PATH"
echo '=== /opt ==='
ls /opt/ 2>&1 | head
echo '=== find tcsh/csh ==='
find / -maxdepth 4 -name 'tcsh*' -o -maxdepth 4 -name 'csh' 2>/dev/null | head -20
echo '=== /opt/condabin ==='
ls /opt/condabin 2>&1 | head
echo '=== base tools ==='
which m4 perl tcsh dpkg dpkg-deb 2>&1
echo '=== thirdparty ==='
ls -la /users/zhyuancheng2025/IceLake/wrf-4.8/image-stage/thirdparty/ 2>&1
echo '=== tmp dir ==='
ls -la /users/zhyuancheng2025/IceLake/wrf-4.8/tmp/ 2>&1 | head
echo '=== try extract tcsh deb ==='
D=/users/zhyuancheng2025/IceLake/wrf-4.8/tools
mkdir -p "$D"
DEB=$(ls /users/zhyuancheng2025/IceLake/wrf-4.8/image-stage/thirdparty/*tcsh*.deb 2>/dev/null | head -1)
echo "deb: $DEB"
if [ -n "$DEB" ]; then
  dpkg-deb -x "$DEB" "$D/tcsh-extract" && ls -la "$D/tcsh-extract/usr/bin/" 2>&1 | head
  "$D/tcsh-extract/usr/bin/tcsh" --version 2>&1 | head -2
fi
echo '=== geo_em check ==='
ncdump -h /users/zhyuancheng2025/IceLake/wrf-4.8/cases/lanzhou2025/wps/geo_em.d01.nc 2>/dev/null | head -12
ncdump -h /users/zhyuancheng2025/IceLake/wrf-4.8/cases/lanzhou2025/wps/geo_em.d02.nc 2>/dev/null | head -12
echo '=== DONE ==='