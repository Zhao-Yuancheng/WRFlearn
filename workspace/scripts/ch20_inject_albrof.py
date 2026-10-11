#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""ch20 第三级：把 2D 屋顶反照率场（ALBROF_2D）注入 wrfinput 副本。

设计（单变量对照 + 域内对照）：
  d01: 全 0            → 不覆盖（=3 的城市格点继续用 URBPARM 表值）
  d02: 城市格点（FRC_URB2D>0.5）按经度劈半：
        经度 >  103.83E → 0.8（"高反照屋顶"处理组）
        经度 <= 103.83E → 0.2（与表值 ALBR=0.20 相同 → 域内对照组）
       非城市格点 → 0

用法: python ch20_inject_albrof.py <in_d01> <in_d02> <out_dir>
"""
import os
import shutil
import sys

import numpy as np
from netCDF4 import Dataset

SPLIT_LON = 103.83


def _mkvar(ds):
    if "ALBROF_2D" in ds.variables:
        return ds.variables["ALBROF_2D"]
    v = ds.createVariable("ALBROF_2D", "f4", ("Time", "south_north", "west_east"))
    v.FieldType = np.int32(104)
    v.MemoryOrder = "XY "
    v.description = "2D ROOF ALBEDO FROM INPUT (ch20-L3)"
    v.units = "dimensionless"
    v.stagger = ""
    v.coordinates = "XLONG XLAT XTIME"
    return v


def patch(src, dst, dom):
    shutil.copyfile(src, dst)
    with Dataset(dst, "r+") as ds:
        v = _mkvar(ds)
        vals = np.zeros(v.shape, dtype="f4")
        if dom == "d02":
            frc = np.asarray(ds.variables["FRC_URB2D"][:], dtype="f4")
            lon = np.asarray(ds.variables["XLONG"][:], dtype="f4")
            urb = frc > 0.5
            east = urb & (lon > SPLIT_LON)
            west = urb & (lon <= SPLIT_LON)
            vals[east] = 0.8
            vals[west] = 0.2
            print("  d02: 城市格点=%d  东(0.8)=%d  西(0.2)=%d"
                  % (int(urb.sum()), int(east.sum()), int(west.sum())))
        v[:] = vals
        print("  写出: %s  ALBROF_2D shape=%s min=%.2f max=%.2f"
              % (dst, v.shape, float(vals.min()), float(vals.max())))


def main():
    in_d01, in_d02, out_dir = sys.argv[1], sys.argv[2], sys.argv[3]
    os.makedirs(out_dir, exist_ok=True)
    patch(in_d01, os.path.join(out_dir, "wrfinput_d01"), "d01")
    patch(in_d02, os.path.join(out_dir, "wrfinput_d02"), "d02")


if __name__ == "__main__":
    main()