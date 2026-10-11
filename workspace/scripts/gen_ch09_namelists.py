# -*- coding: utf-8 -*-
"""生成 ch09 IO 实验所用 namelist 变体（基于 namelist.input.short，仅改 io_form_history / quilt）。"""
import re
from pathlib import Path

base = Path(r"d:\Code\Learn\WRF\workspace\cases\lanzhou2025\namelist.input.short")
src = base.read_text(encoding="utf-8")


def set_io(text, val):
    new, n = re.subn(r"(^[ \t]*io_form_history[ \t]*=[ \t]*)\d+([ \t]*)$",
                     lambda m: m.group(1) + str(val) + m.group(2), text, flags=re.M)
    assert n == 1, f"io_form_history 替换次数 = {n}"
    return new


def set_quilt(text, n_task):
    new, n = re.subn(r"(^[ \t]*nio_tasks_per_group[ \t]*=[ \t]*)\d+",
                     lambda m: m.group(1) + str(n_task), text, flags=re.M)
    assert n == 1, f"nio_tasks_per_group 替换次数 = {n}"
    return new


def add_classic(text):
    """在 &time_control 的 debug_level 行后插入 use_netcdf_classic（registry.io_boilerplate 的 namelist 项）。"""
    new, n = re.subn(r"(^[ \t]*debug_level[ \t]*=[ \t]*\d+[ \t]*$)",
                     r"\1\n use_netcdf_classic                  = .true.,",
                     text, count=1, flags=re.M)
    assert n == 1, f"debug_level 插入次数 = {n}"
    return new


out_dir = base.parent
variants = {
    "namelist.input.io2": set_io(src, 2),
    "namelist.input.io11": set_io(src, 11),
    "namelist.input.io102": set_io(src, 102),
    "namelist.input.io2q": set_quilt(set_io(src, 2), 1),
    "namelist.input.io2c": add_classic(set_io(src, 2)),
}
for name, text in variants.items():
    (out_dir / name).write_text(text, encoding="utf-8")

# 自检
for name in variants:
    t = (out_dir / name).read_text(encoding="utf-8")
    io = re.search(r"io_form_history[ \t]*=[ \t]*(\d+)", t).group(1)
    nq = re.search(r"nio_tasks_per_group[ \t]*=[ \t]*(\d+)", t).group(1)
    diff = sum(1 for a, b in zip(src.splitlines(), t.splitlines()) if a != b)
    print(f"{name}: io_form_history={io} nio_tasks={nq} 与基线差异行数={diff}")