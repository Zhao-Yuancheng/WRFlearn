# -*- coding: utf-8 -*-
"""ch19 修补 wrfinput 的城市类型场。

背景（full 源码实证，见 workspace/context/ch19_material.md）：
  * 兰州 geog 数据缺 FRC_URB2D / URB_PARAM（NUDAPT44 只覆盖美国）
  * real.exe 的 FRC_URB2D 回退（0.9）在 sf_urban_physics>0 时生效 ✓
  * 但 UTYPE_URB2D（城市类型索引）没有任何数据源 → 保持 0
  * module_sf_urban.F 的 read_param 用 ZDC_TBL(UTYPE) 等表查找，UTYPE=0 越界
    → 触发 "ZDC + Z0C + 2m is larger than the 1st WRF level" fatal（sf1 实测）
  * module_sf_bep_bem.F 的 param 在 hgt_urb<=0 时回退表值 ws_u/bs_u(id,iurb)
    → 同样需要合法 iurb

本脚本：把 UTYPE_URB2D 置为 2（URBPARM.TBL 3 类中的"高密度住宅"），
其余形态场保持 0 → 由 WRF 内置的"默认城市形态"路径（URBPARM 表值）驱动。

用法: python ch19_patch_wrfinput.py <in.nc> <out.nc>
"""
import sys
import numpy as np
from netCDF4 import Dataset

UTYPE_NEW = 2


def main(src, dst):
    d = Dataset(src, "r")
    print("== %s ==" % src)
    names = list(d.variables)
    print("UTYPE_URB2D 存在:", "UTYPE_URB2D" in names,
          "| FRC_URB2D 存在:", "FRC_URB2D" in names)
    for v in ["UTYPE_URB2D", "FRC_URB2D", "MH_URB2D", "HGT_URB2D", "LP_URB2D",
              "LB_URB2D", "STDH_URB2D", "HI_URB2D", "IVGTYP", "LU_INDEX"]:
        if v in names:
            var = d.variables[v]
            a = np.asarray(var[:])
            print("  %-12s %-14s %-22s min=%s max=%s" %
                  (v, str(var.dtype), str(var.dimensions), a.min(), a.max()))
    d.close()

    # 复制并修补
    import shutil
    shutil.copyfile(src, dst)
    d = Dataset(dst, "r+")
    ut = d.variables["UTYPE_URB2D"]
    old = np.asarray(ut[:]).copy()
    ut[:] = UTYPE_NEW
    print("  UTYPE_URB2D: %s -> %d（全格点）" % (sorted(set(old.ravel().tolist())), UTYPE_NEW))

    # 若存在 FRC_URB2D，报告城市格点数（其余保持原值不动）
    if "FRC_URB2D" in names:
        frc = np.asarray(d.variables["FRC_URB2D"][:])
        print("  FRC_URB2D>0 的格点数: %d（其中≥0.5: %d）"
              % (int((frc > 0).sum()), int((frc >= 0.5).sum())))
    d.close()
    print("  写出: %s" % dst)


if __name__ == "__main__":
    main(sys.argv[1], sys.argv[2])