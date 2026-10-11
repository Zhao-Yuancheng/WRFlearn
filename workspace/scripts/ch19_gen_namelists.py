# -*- coding: utf-8 -*-
"""ch19 三档城市方案 namelist 生成器。

基准: workspace/data/ch19/namelist.input.base（兰州 2025-07-12_00Z 起报，两域 9/3 km）
输出（写入 workspace/data/ch19/nml/）:
  nml10_sf0 / nml10_sf1 / nml10_sf3   短测 10 分钟（可行性与日志检查）
  nml5d_sf0 / nml5d_sf1 / nml5d_sf3   正式 5 天（07-12_00Z → 07-17_00Z）

改动要点（均以源码/教训为依据）:
  * 短测必须同时设 run_* 与 end_*（双值）：d01 用 run_minutes 构造 run_length，
    d02 的 nest_stop 取自该域 end_*（ch08 修正 2：单值 end_minute 会让 d02 永不激活）
  * sf_urban_physics = 0/1/3；num_urban_* 是 derived（自动派生），namelist 不必给
"""
import os
import re

BASE = r"d:\Code\Learn\WRF\workspace\data\ch19\namelist.input.base"
OUT = r"d:\Code\Learn\WRF\workspace\data\ch19\nml"
os.makedirs(OUT, exist_ok=True)

with open(BASE, encoding="utf-8") as f:
    base = f.read()


def set_line(text, key, new_line):
    pat = re.compile(r"^[ \t]*" + key + r"[ \t]*=.*$", re.M)
    assert pat.search(text), "key not found: " + key
    return pat.sub(new_line, text)


def gen(sf_urban, minutes=None, days=5):
    t = base
    if minutes is None:
        # 正式 5 天：只改城市方案
        t = set_line(t, "sf_urban_physics",
                     " sf_urban_physics                    = %d,     %d," % (sf_urban, sf_urban))
    else:
        # 短测：run_* 与 end_* 同步改为 07-12 00:00 + minutes
        t = set_line(t, "run_days", " run_days                            = 0,")
        t = set_line(t, "run_hours", " run_hours                           = 0,")
        t = set_line(t, "run_minutes", " run_minutes                         = %d," % minutes)
        t = set_line(t, "run_seconds", " run_seconds                         = 0,")
        t = set_line(t, "end_year", " end_year                            = 2025, 2025,")
        t = set_line(t, "end_month", " end_month                           = 07,   07,")
        t = set_line(t, "end_day", " end_day                             = 12,   12,")
        t = set_line(t, "end_hour", " end_hour                            = 00,   00,")
        if re.search(r"^[ \t]*end_minute", t, re.M):
            t = set_line(t, "end_minute", " end_minute                          = %d,   %d," % (minutes, minutes))
        else:
            t = set_line(t, "end_hour",
                         " end_hour                            = 00,   00,\n"
                         " end_minute                          = %d,   %d," % (minutes, minutes))
        t = set_line(t, "end_second", " end_second                          = 00,   00,") \
            if re.search(r"^[ \t]*end_second", t, re.M) else t
        t = set_line(t, "sf_urban_physics",
                     " sf_urban_physics                    = %d,     %d," % (sf_urban, sf_urban))
    return t


for sf in (0, 1, 3):
    p = os.path.join(OUT, "nml10_sf%d" % sf)
    with open(p, "w", encoding="utf-8") as f:
        f.write(gen(sf, minutes=10))
    print("wrote", p)

for sf in (0, 1, 3):
    p = os.path.join(OUT, "nml5d_sf%d" % sf)
    with open(p, "w", encoding="utf-8") as f:
        f.write(gen(sf, minutes=None))
    print("wrote", p)


# ------------------------------------------------------------------
# 定位用：短测时间写法的 A/B/C 三档（均 sf_urban_physics=0）
#   A: 只改 run_*（run_minutes=10），end_* 保持基准（07-17_00）
#   B: run_minutes=10 且 end_* 改为 07-12_00:10（当前已知崩）
#   C: run_* 全 0，纯用 end_* = 07-12_00:10（官方最常用短测写法）
# ------------------------------------------------------------------
def gen_abc(tag):
    t = base
    t = set_line(t, "sf_urban_physics", " sf_urban_physics                    = 0,     0,")
    if tag == "A":
        t = set_line(t, "run_days", " run_days                            = 0,")
        t = set_line(t, "run_minutes", " run_minutes                         = 10,")
    elif tag == "B":
        t = set_line(t, "run_days", " run_days                            = 0,")
        t = set_line(t, "run_minutes", " run_minutes                         = 10,")
        t = set_line(t, "end_day", " end_day                             = 12,   12,")
        t = set_line(t, "end_hour", " end_hour                            = 00,   00,")
        t = set_line(t, "end_hour", " end_hour                            = 00,   00,\n"
                                  " end_minute                          = 10,   10,")
    else:  # C
        t = set_line(t, "run_days", " run_days                            = 0,")
        t = set_line(t, "run_hours", " run_hours                           = 0,")
        t = set_line(t, "run_minutes", " run_minutes                         = 0,")
        t = set_line(t, "end_day", " end_day                             = 12,   12,")
        t = set_line(t, "end_hour", " end_hour                            = 00,   00,\n"
                                  " end_minute                          = 10,   10,")
    return t


for tag in ("A", "B", "C"):
    p = os.path.join(OUT, "nml10_%s" % tag)
    with open(p, "w", encoding="utf-8") as f:
        f.write(gen_abc(tag))
    print("wrote", p)

# 自检：打印关键行
for name in sorted(os.listdir(OUT)):
    with open(os.path.join(OUT, name), encoding="utf-8") as f:
        txt = f.read()
    keys = ["run_days", "run_minutes", "end_day", "end_hour", "end_minute", "sf_urban_physics"]
    vals = []
    for k in keys:
        m = re.search(r"^[ \t]*" + k + r"[ \t]*=(.*)$", txt, re.M)
        vals.append("%s=%s" % (k, m.group(1).strip() if m else "MISSING"))
    print("%-14s %s" % (name, " | ".join(vals)))