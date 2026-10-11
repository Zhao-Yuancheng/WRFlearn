# -*- coding: utf-8 -*-
"""ch19 城市对照正式（5 天）namelist 生成器（第二阶段）。

三档（均 5 天两域，其余参数完全相同 = 单变量对照）：
  exp1  sf_urban_physics=1（SLUCM）+ bl_pbl_physics=5（MYNN，与 ch08 基线一致）
  exp2  sf_urban_physics=0（CTRL）+ bl_pbl_physics=8（BouLac）
  exp3  sf_urban_physics=3（BEP+BEM）+ bl_pbl_physics=8（BouLac，论文2 首选）

依据（源码实测，见 workspace/context/ch19_material.md）：
  * BEP/BEM 只兼容 bl_pbl_physics ∈ {1 YSU, 2 MYJ, 8 BouLac}
    （module_physics_init 的 fatal：use ysu/my,j/boulac with BEP/BEM urban scheme）
  * exp2/exp3 同用 BouLac 以保证单变量对照
  * CTRL 基线另有 ch08 的 439419（=0 + MYNN + 5 天）可直接用作 exp1 的对照
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


def gen(tag, sf_urban, pbl):
    t = base
    t = set_line(t, "sf_urban_physics",
                 " sf_urban_physics                    = %d,     %d," % (sf_urban, sf_urban))
    t = set_line(t, "bl_pbl_physics",
                 " bl_pbl_physics                      = %d,     %d," % (pbl, pbl))
    return t


SPECS = [
    ("exp1", 1, 5, 5),   # SLUCM(=1) + MYNN(5) + MYNN 面层(5)；CTRL = ch08 439419（同套装, =0）
    ("exp2", 0, 1, 1),   # CTRL(=0) + YSU(1) + sfclay(1)（BEP/BEM 兼容套装）
    ("exp3", 3, 1, 1),   # BEP+BEM(=3) + YSU(1) + sfclay(1)；与 exp2 单变量配对
]


def gen(tag, sf_urban, pbl, sfclay):
    t = base
    t = set_line(t, "sf_urban_physics",
                 " sf_urban_physics                    = %d,     %d," % (sf_urban, sf_urban))
    t = set_line(t, "bl_pbl_physics",
                 " bl_pbl_physics                      = %d,     %d," % (pbl, pbl))
    t = set_line(t, "sf_sfclay_physics",
                 " sf_sfclay_physics                   = %d,     %d," % (sfclay, sfclay))
    return t


for tag, sf, pbl, sfc in SPECS:
    p = os.path.join(OUT, "nml_%s" % tag)
    with open(p, "w", encoding="utf-8") as f:
        f.write(gen(tag, sf, pbl, sfc))
    print("wrote", os.path.basename(p), "sf_urban=%d bl_pbl=%d sf_sfclay=%d" % (sf, pbl, sfc))

print()
for tag, sf, pbl, sfc in SPECS:
    txt = open(os.path.join(OUT, "nml_%s" % tag), encoding="utf-8").read()
    vals = []
    for k in ["run_days", "sf_urban_physics", "bl_pbl_physics", "sf_sfclay_physics",
              "sf_surface_physics", "mp_physics", "cu_physics"]:
        m = re.search(r"^[ \t]*" + k + r"[ \t]*=(.*)$", txt, re.M)
        vals.append("%s=%s" % (k, m.group(1).strip() if m else "MISSING"))
    print("%-10s %s" % (tag, " | ".join(vals)))