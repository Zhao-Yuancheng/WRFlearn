"""列出指定 slide 的全部媒体文件，便于挑选位图版本。"""
import re
from pathlib import Path

PPT_DIR = Path(r"d:\Code\Learn\WRF\AtmosphericPhysics\ppt")

def find_unpack(prefix):
    return [p for p in PPT_DIR.iterdir() if p.is_dir() and p.name.startswith(prefix)
            and p.name.endswith("_unpack")][0]

def show(prefix, slides):
    up = find_unpack(prefix)
    print("=" * 60, "\n", up.name)
    for n in slides:
        rels = up / "ppt" / "slides" / "_rels" / f"slide{n}.xml.rels"
        if not rels.exists():
            print(f"  slide{n}: no rels"); continue
        txt = rels.read_text(encoding="utf-8", errors="ignore")
        tg = re.findall(r'Target="\.\./media/([^"]+)"', txt)
        print(f"  slide{n}:")
        for t in tg:
            p = up / "ppt" / "media" / t
            sz = p.stat().st_size / 1024 if p.exists() else -1
            print(f"    {t}  {sz:.0f} KB")

show("5-2 辐射的物理规律", [6, 7, 11, 15, 21])
show("5-4+太阳辐射在地球大气中的传输", [13, 15, 16, 20, 24, 31])
show("5-5地球-大气系统的长波辐射", [7, 8, 11, 15])