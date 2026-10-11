#!/usr/bin/env bash
# 核实 wrf.exe 链接方式 + run/ 中的 namelist 模板 + configure.wrf 关键行
B=/users/zhyuancheng2025/IceLake/wrf-4.8/build/WRF
echo '===== file wrf.exe ====='
file $B/main/wrf.exe
echo '===== readelf 动态段检查 ====='
readelf -d $B/main/wrf.exe 2>&1 | head -8
echo '===== configure.wrf 链接标志 ====='
grep -nE '^(LDFLAGS|LDOPTIM|FC|FCOPTIM|FCFLAGS_LONG|CFLAGS_LOCAL)' $B/configure.wrf | head -12
echo '===== grep -static ====='
grep -n 'static' $B/configure.wrf | head -8
echo '===== run/ 中的 namelist ====='
ls $B/run | grep -iE 'namelist|rsl|README'
echo '===== run/ 剩余文件（51-93） ====='
ls $B/run | sed -n '51,93p'