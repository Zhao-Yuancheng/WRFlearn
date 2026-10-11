#!/usr/bin/env bash
# ch03 巡览：集群编译产物只读实录
B=/users/zhyuancheng2025/IceLake/wrf-4.8/build/WRF
echo '===== main/*.exe ====='
ls -la $B/main/*.exe
echo '===== version_decl ====='
head -12 $B/inc/version_decl 2>/dev/null || find $B -maxdepth 2 -name version_decl | head -3
echo '===== run 常用文件（程序族运行目录样例） ====='
ls $B/run | head -50
echo '===== run 文件总数 ====='
ls $B/run | wc -l
echo '===== ldd wrf.exe（前 25 行） ====='
ldd $B/main/wrf.exe | head -25
echo '===== 顶层目录 ====='
ls $B