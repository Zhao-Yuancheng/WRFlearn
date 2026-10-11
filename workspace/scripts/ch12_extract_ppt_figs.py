"""ch12 PPT 原图提取：按 slide → media 映射（读 ppt/slides/_rels/slideN.xml.rels）。

为 5-1..5-6 六讲选定的幻灯片抽取最大图片，另存 doc/figs/ppt/ch12_ppt_*.EXT。
"""
import re
import shutil
from pathlib import Path

ROOT = Path(r"d:\Code\Learn\WRF")
PPT_DIR = ROOT / "AtmosphericPhysics" / "ppt"
OUT = ROOT / "doc" / "figs" / "ppt"
OUT.mkdir(parents=True, exist_ok=True)

# (pptx 子目录前缀, slide 号, 输出名)：slide 号为 PPT 内 slideN.xml 的 N
PICKS = [
    ("5-2 辐射的物理规律", 21, "ch12_ppt_three_laws"),
    ("5-3 地球大气与辐射的相互作用", 21, "ch12_ppt_absorption_spectrum"),
    ("5-3 地球大气与辐射的相互作用", 34, "ch12_ppt_mie_efficiency"),
    ("5-4+太阳辐射在地球大气中的传输", 13, "ch12_ppt_solar_spectrum"),
    ("5-4+太阳辐射在地球大气中的传输", 15, "ch12_ppt_solar_constant"),
    ("5-6地球-大气系统的辐射平衡", 5, "ch12_ppt_greenhouse_model"),
]

def find_unpack(prefix):
    """定位解包目录（文件名可能含中文与空格）。"""
    cands = [p for p in PPT_DIR.iterdir() if p.is_dir() and p.name.startswith(prefix)
             and p.name.endswith("_unpack")]
    if not cands:
        raise FileNotFoundError(prefix)
    return cands[0]

def slide_images(unpack, n):
    rels = unpack / "ppt" / "slides" / "_rels" / f"slide{n}.xml.rels"
    if not rels.exists():
        return []
    txt = rels.read_text(encoding="utf-8", errors="ignore")
    targets = re.findall(r'Target="\.\./media/([^"]+)"', txt)
    imgs = []
    for t in targets:
        p = unpack / "ppt" / "media" / t
        if p.exists():
            imgs.append(p)
    return imgs

for prefix, n, outname in PICKS:
    try:
        unpack = find_unpack(prefix)
        imgs = slide_images(unpack, n)
        if not imgs:
            print(f"[MISS] {prefix} slide{n}: no image")
            continue
        big = max(imgs, key=lambda p: p.stat().st_size)
        dst = OUT / f"{outname}{big.suffix.lower()}"
        shutil.copy2(big, dst)
        print(f"[OK] {prefix} slide{n} -> {dst.name} ({big.stat().st_size/1024:.0f} KB, "
              f"from {big.name}; slide 共 {len(imgs)} 图)")
    except Exception as e:
        print(f"[ERR] {prefix} slide{n}: {e}")