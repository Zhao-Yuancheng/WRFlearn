#!/bin/bash
#SBATCH -p cpu
#SBATCH -N1
#SBATCH -n1
#SBATCH -t 00:10:00
#SBATCH -o /users/zhyuancheng2025/IceLake/scripts_staging/condalib_check_%j.out
# 检查集群各 env 科学库可用性（计算节点；按规则不写 mem 参数）
M=/users/zhyuancheng2025/miniforge3
for e in mklpy P312 RdFlood sam2; do
  P=$M/envs/$e/bin/python
  echo "===== $e ====="
  "$P" - <<'EOF'
import importlib
for m in ("numpy", "scipy", "pandas", "matplotlib", "netCDF4", "xarray", "metpy", "wrf"):
    try:
        mod = importlib.import_module(m)
        print(f"  {m}: {getattr(mod, '__version__', 'OK')}")
    except Exception as ex:
        print(f"  {m}: - ({type(ex).__name__})")
EOF
done
echo "ALL_DONE"
