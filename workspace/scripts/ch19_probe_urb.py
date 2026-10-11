# -*- coding: utf-8 -*-
"""ch19 侦察：geo_em.d02 的 URB_PARAM（NUDAPT44, 132 层）是否含"城市分数"
与 LANDUSEF 城市类别（MODIS 13）对照，为构造/确认 FRC_URB2D 提供依据。
用法: python ch19_probe_urb.py
"""
import numpy as np
from netCDF4 import Dataset

P = r"d:\Code\Learn\WRF\workspace\data\ch19\geo_em.d02.nc"
d = Dataset(P)

lu = d.variables["LU_INDEX"][0]
landuse = d.variables["LANDUSEF"][0]        # (num_land_cat, sn, we)
urb = d.variables["URB_PARAM"][0]           # (num_urb_params, sn, we)
ncat = urb.shape[0]

print("dimensions:", {k: len(v) for k, v in d.dimensions.items()})
print("URB_PARAM shape:", urb.shape, " LANDUSEF shape:", landuse.shape)
print("LU_INDEX 取值:", sorted(set(lu.astype(int).ravel().tolist())))
n_urban = int((lu == 13).sum())
print("LU_INDEX==13 格点数:", n_urban, "/", lu.size)

# 城市类别的分数：LANDUSEF 里第 13 类（索引 12）
fr_landuse = landuse[12]
print("\nLANDUSEF[13] 统计: min=%.3f max=%.3f mean=%.3f  非零格点=%d"
      % (fr_landuse.min(), fr_landuse.max(), fr_landuse.mean(), int((fr_landuse > 0).sum())))

# 找 URB_PARAM 中最像"城市分数"的层
print("\nURB_PARAM 各层与 LANDUSEF[13] 的对照（按平均绝对差排序，取前 12）：")
rows = []
for k in range(ncat):
    a = urb[k].astype(float)
    diff = np.abs(a - fr_landuse)
    corr = np.corrcoef(a.ravel(), fr_landuse.ravel())[0, 1] if a.std() > 0 else np.nan
    rows.append((float(diff.mean()), float(corr), k, float(a.min()), float(a.max()), float(a.mean())))
rows.sort(key=lambda r: r[0])
for md, corr, k, mn, mx, mean in rows[:12]:
    print("  layer %3d : MAD=%.4f  corr=%+.4f  min=%.3f max=%.3f mean=%.3f"
          % (k, md, corr, mn, mx, mean))

print("\n结论提示：MAD 最小且 min/max 落在 [0,1] 的层最可能是 urban fraction。")
d.close()