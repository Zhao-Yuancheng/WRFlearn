#!/usr/bin/env bash
# 取消残留的 bash 作业（439289，此前超时 srun 残留），轮询 439294 输出
scancel 439289 2>/dev/null
OUT=/users/zhyuancheng2025/IceLake/scripts_staging/condalib_check_439294.out
for i in $(seq 1 30); do
  if [ -f "$OUT" ] && grep -q ALL_DONE "$OUT" 2>/dev/null; then
    cat "$OUT"
    exit 0
  fi
  sleep 10
done
echo "TIMEOUT_WAITING"
[ -f "$OUT" ] && cat "$OUT"
squeue -u zhyuancheng2025 -h
