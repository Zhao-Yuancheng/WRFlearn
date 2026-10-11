#!/usr/bin/env bash
# 检验集群 miniforge3 修复状态（只读）
M=/users/zhyuancheng2025/miniforge3

echo '--- base bin ---'
ls $M/bin 2>/dev/null | grep -E '^(conda|mamba|python3?)$'
echo '--- base python ---'
$M/bin/python -V 2>&1
echo '--- condarc（镜像配置） ---'
cat ~/.condarc 2>/dev/null || echo '(无 ~/.condarc)'
echo '--- envs 列表 ---'
ls $M/envs 2>/dev/null
echo '--- envs 内 python ---'
for e in $($M/bin/conda env list 2>/dev/null | awk 'NR>2 {print $1}' | grep -v '^#'); do
  P=$M/envs/$e/bin/python
  if [ -x "$P" ]; then
    echo "[$e] $($P -V 2>&1)"
  else
    echo "[$e] python: 无二进制"
  fi
done
echo '--- conda 版本 ---'
$M/bin/conda --version 2>&1
$M/bin/mamba --version 2>&1 | head -1
