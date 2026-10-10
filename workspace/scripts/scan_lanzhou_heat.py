#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""分析 2025 年 6-8 月兰州区域 ERA5 t2m（本地小区域子集）。
输出：城关/榆中两点逐日最高温的 Top-10 热日、最热连续 3/4 天窗口、CSV。
"""
import csv
from datetime import datetime, timedelta

import netCDF4 as nc
import numpy as np

DATA = r"d:\Code\Learn\WRF\workspace\data"
OUT_CSV = DATA + r"\lanzhou_heat_2025_summary.csv"

MONTHS = ["202506", "202507", "202508"]
URBAN = (36.061, 103.834)   # 城关（约）
RURAL = (35.844, 104.115)   # 榆中方向（约）


def load():
    lats = lons = None
    t2m, times = [], []
    for m in MONTHS:
        ds = nc.Dataset(rf"{DATA}\t2m_{m}_lz.nc")
        if lats is None:
            lats = ds["latitude"][:]
            lons = ds["longitude"][:]
        t2m.append(ds["t2m"][:].filled(np.nan) if hasattr(ds["t2m"][:], "filled") else ds["t2m"][:])
        times.append(ds["valid_time"][:])
        ds.close()
    t2m = np.concatenate(t2m, axis=0)          # (time, lat, lon), K
    times = np.concatenate(times)              # seconds since 1970 (UTC)
    dt = [datetime(1970, 1, 1) + timedelta(seconds=int(s)) for s in times]
    return lats, lons, t2m, dt


def nearest(lats, lons, plat, plon):
    i = int(np.argmin(np.abs(lats - plat)))
    j = int(np.argmin(np.abs(lons - plon)))
    return i, j


def daily_max(t2m_pt, dt):
    """按北京时（UTC+8）分日取最高。返回 [(date, Tmax)]。"""
    buckets = {}
    for v, t in zip(t2m_pt, dt):
        d = (t + timedelta(hours=8)).date()
        buckets.setdefault(d, []).append(v)
    return sorted((d, float(np.nanmax(vv)) - 273.15) for d, vv in buckets.items())


def main():
    lats, lons, t2m, dt = load()
    print("grid:", len(lats), "x", len(lons), "| times:", len(dt),
          "|", dt[0].isoformat(), "->", dt[-1].isoformat())

    series = {}
    for name, (plat, plon) in (("urban", URBAN), ("rural", RURAL)):
        i, j = nearest(lats, lons, plat, plon)
        print(f"{name}: grid lat={lats[i]:.2f} lon={lons[j]:.2f}")
        series[name] = daily_max(t2m[:, i, j], dt)

    # Top-10 热日（按 urban Tmax）
    top = sorted(series["urban"], key=lambda x: -x[1])[:10]
    rural_map = dict(series["rural"])
    print("\n== Top-10 热日（城关点，北京时） ==")
    for d, t in top:
        print(f"{d}  urban {t:5.1f}C   rural {rural_map.get(d, float('nan')):5.1f}C")

    # 最热连续 3/4 天窗口（按 urban 日 Tmax 的滑动均值）
    arr = series["urban"]
    for k in (3, 4):
        best = max(
            (np.mean([v for _, v in arr[p:p + k]]), arr[p][0], arr[p + k - 1][0])
            for p in range(len(arr) - k + 1)
        )
        mean, d0, d1 = best
        print(f"最热连续 {k} 天窗口: {d0} ~ {d1}  urban 平均日最高 {mean:.1f}C")

    with open(OUT_CSV, "w", newline="", encoding="utf-8-sig") as f:
        w = csv.writer(f)
        w.writerow(["date", "urban_tmax_C", "rural_tmax_C"])
        for (d, tu), (_, tr) in zip(series["urban"], series["rural"]):
            w.writerow([d, f"{tu:.2f}", f"{tr:.2f}"])
    print("csv:", OUT_CSV)


if __name__ == "__main__":
    main()
