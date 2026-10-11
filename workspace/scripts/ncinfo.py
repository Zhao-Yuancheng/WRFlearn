#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""nc 文件快速检查工具（ch20 及以后复用）。

用法:
  python ncinfo.py FILE [FILE2 ...]                 # 变量/维度总览 + 全局属性
  python ncinfo.py FILE -v T2,T2_PEAK -t 0          # 指定变量统计（-t 取第几帧，默认全部）
  python ncinfo.py FILE -v T2 --list                # 只列变量名
"""
import argparse
import sys

import numpy as np
import netCDF4 as nc


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("files", nargs="+")
    ap.add_argument("-v", "--vars", default=None)
    ap.add_argument("-t", "--time", type=int, default=None)
    ap.add_argument("--list", action="store_true")
    args = ap.parse_args()

    for path in args.files:
        with nc.Dataset(path) as ds:
            print("=" * 72)
            print(path)
            if args.list:
                print(", ".join(ds.variables.keys()))
                continue
            if args.vars is None:
                print("dims:", {k: len(v) for k, v in ds.dimensions.items()})
                print("nvars:", len(ds.variables))
                names = list(ds.variables.keys())
                print("vars:", ", ".join(names))
                continue
            for v in args.vars.split(","):
                if v not in ds.variables:
                    print("  [MISSING] %s" % v)
                    continue
                arr = ds.variables[v][:]
                arr = np.ma.filled(np.asarray(arr, dtype=float), np.nan)
                times = None
                if "Time" in ds.variables and arr.ndim >= 3 and ds.variables[v].dimensions[0] == "Time":
                    times = nc.num2date(
                        ds.variables["Time"][:],
                        ds.variables["Time"].units,
                        only_use_cftime_datetimes=False)
                if args.time is not None and arr.ndim >= 3:
                    i = args.time
                    a = arr[i]
                    tstr = (" | %s" % times[i]) if times is not None else ""
                    print("  %-12s frame %d%s  min=%.4f max=%.4f mean=%.4f" % (v, i, tstr, np.nanmin(a), np.nanmax(a), np.nanmean(a)))
                else:
                    print("  %-12s shape=%s  min=%.4f max=%.4f mean=%.4f" % (v, arr.shape, np.nanmin(arr), np.nanmax(arr), np.nanmean(arr)))
                    if times is not None and arr.ndim >= 3:
                        print("    times: %s .. %s (%d frames)" % (times[0], times[-1], len(times)))
            for k in ("TITLE", "START_DATE", "SIMULATION_START_DATE", "WEST-EAST_GRID_DIMENSION", "DT"):
                if k in ds.ncattrs():
                    print("  @%s = %s" % (k, ds.getncattr(k)))


if __name__ == "__main__":
    sys.exit(main())