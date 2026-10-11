# -*- coding: utf-8 -*-
"""生成 ch08 restart 实验 namelist（基于 namelist.input.short）：
- rst1 : restart_interval=0 + restart_interval_s=300（秒制写法，等价 5 分钟）
- rst1b: restart_interval=5（分钟制写法；与 rst1 行为应一致 → 实证单位为分钟）
- rst2 : 续跑（restart=.true.，起点取 rst 文件名时间戳），用法：
         python gen_ch08_namelists.py <Y> <M> <D> <h> <m> <s>
"""
import re
import sys
from pathlib import Path

base = Path(r"d:\Code\Learn\WRF\workspace\cases\lanzhou2025\namelist.input.short")
src = base.read_text(encoding="utf-8")


def set_line(text, key, value, comma=True):
    pat = rf"(^[ \t]*{key}[ \t]*=[ \t]*)([^!\n]*?)([ \t]*)$"
    new, n = re.subn(pat, lambda m: m.group(1) + value + ("," if comma else ""), text, flags=re.M)
    assert n == 1, f"{key} 替换次数 = {n}"
    return new


def insert_after(text, key, newline):
    pat = rf"(^[ \t]*{key}[ \t]*=.*$)"
    new, n = re.subn(pat, lambda m: m.group(1) + "\n" + newline, text, count=1, flags=re.M)
    assert n == 1, f"{key} 插入次数 = {n}"
    return new


out_dir = base.parent

# rst1：秒制；先把 restart_interval 归零，避免分钟字段兜底
rst1 = set_line(src, "restart_interval", "0")
rst1 = insert_after(rst1, "restart_interval", " restart_interval_s                  = 300,")
(out_dir / "namelist.input.rst1").write_text(rst1, encoding="utf-8")

# rst1b：分钟制（restart_interval 单位=分钟，5 分钟应与 rst1 的 300 秒等效）
rst1b = set_line(src, "restart_interval", "5")
(out_dir / "namelist.input.rst1b").write_text(rst1b, encoding="utf-8")
print("rst1 / rst1b written")

# rst1d：两域齐活版（end_minute 必须按域给两个值，否则嵌套域永不激活）
rst1d = set_line(rst1, "end_minute", "10, 10")
(out_dir / "namelist.input.rst1d").write_text(rst1d, encoding="utf-8")
print("rst1d written (end_minute = 10, 10)")

# rst2：续跑（可选，需给定 rst 文件时间戳）
if len(sys.argv) == 7:
    Y, Mo, D, H, Mi, S = sys.argv[1:]
    rst2 = set_line(rst1d, "restart", ".true.")
    rst2 = set_line(rst2, "restart_interval_s", "0")
    rst2 = set_line(rst2, "start_year", f"{Y}, {Y}")
    rst2 = set_line(rst2, "start_month", f"{Mo}, {Mo}")
    rst2 = set_line(rst2, "start_day", f"{D}, {D}")
    rst2 = set_line(rst2, "start_hour", f"{H}, {H}")
    rst2 = insert_after(rst2, "start_hour", f" start_minute                          = {Mi}, {Mi},")
    rst2 = insert_after(rst2, "start_minute", f" start_second                          = {S}, {S},")
    rst2 = set_line(rst2, "end_minute", "12, 12")
    rst2 = set_line(rst2, "history_interval", "5,     5")
    (out_dir / "namelist.input.rst2").write_text(rst2, encoding="utf-8")
    print(f"rst2 written: start={Y}-{Mo}-{D}_{H}:{Mi}:{S}")
else:
    print("(未生成 rst2：需要 6 个参数 Y M D h m s，来自 rst 文件名时间戳)")

# 自检
for name in ("namelist.input.rst1", "namelist.input.rst1b", "namelist.input.rst1d"):
    t = (out_dir / name).read_text(encoding="utf-8")
    ri = re.search(r"restart_interval[ \t]*=[ \t]*(\S+)", t).group(1)
    ris = re.search(r"restart_interval_s[ \t]*=[ \t]*(\d+)", t)
    rf = re.search(r"restart[ \t]*=[ \t]*(\S+)", t).group(1)
    em = re.search(r"end_minute[ \t]*=[ \t]*(\S+)", t).group(1)
    print(f"{name}: restart={rf} restart_interval={ri} restart_interval_s={ris.group(1) if ris else '-'} end_minute={em}")