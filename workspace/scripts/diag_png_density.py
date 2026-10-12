"""PNG 全分辨率内容分布：非白像素真实包围盒 + 按高度 20 段的密度分布。"""
import pathlib, sys
import numpy as np
from PIL import Image

ROOT = pathlib.Path(r"d:\Code\Learn\WRF")
PNG_DIR = ROOT / "doc" / "figs" / "mermaid"

for stem in sys.argv[1:]:
    img = np.asarray(Image.open(PNG_DIR / f"{stem}.png").convert("RGB")).astype(int)
    H, W = img.shape[:2]
    nonwhite = (img.min(axis=2) < 240)
    ys, xs = np.nonzero(nonwhite)
    print(f"=== {stem}: {W}x{H} ===")
    if len(xs) == 0:
        print("  全白！")
        continue
    print(f"  非白包围盒 x {xs.min()}~{xs.max()} ({(xs.max()-xs.min())/W*100:.0f}% 宽), y {ys.min()}~{ys.max()} ({(ys.max()-ys.min())/H*100:.0f}% 高)")
    print(f"  非白像素总数 {len(xs)} ({len(xs)/(W*H)*100:.1f}%)")
    dens = [nonwhite[i*H//20:(i+1)*H//20].sum() for i in range(20)]
    print("  高度 20 段密度:", " ".join(f"{d//1000}" if d else "." for d in dens))
    densx = [nonwhite[:, i*W//20:(i+1)*W//20].sum() for i in range(20)]
    print("  宽度 20 段密度:", " ".join(f"{d//1000}" if d else "." for d in densx))
    print()
