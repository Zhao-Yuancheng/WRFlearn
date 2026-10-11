#!/bin/bash
# ch04 勘察：Registry 记录类型统计（本地源码）
cd /d/Code/Learn/WRF/source/WRFv4.8.0/WRFV4.8.0/Registry || exit 1
export LANG=C.UTF-8
echo '=== record-type counts in Registry.EM_COMMON ==='
awk '{print $1}' Registry.EM_COMMON | sort | uniq -c | sort -rn | head -18
echo '=== record-type counts in Registry.EM ==='
awk '{print $1}' Registry.EM | sort | uniq -c | sort -rn | head -8
echo '=== line counts ==='
wc -l Registry.EM_COMMON Registry.EM registry.dimspec registry.io_boilerplate registry.em_shared_collection
echo '=== count of Registry/* files ==='
ls | wc -l