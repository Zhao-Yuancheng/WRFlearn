# -*- coding: utf-8 -*-
"""ch15 书页符号复核：裁剪放大 page_0181（印刷 p167）底部"热带结论"区与
page_0180（p166）(6.9.5) 判据区，供逐字复核。输出至 workspace/tmp/。"""
import os
from PIL import Image

BOOK = r"d:\Code\Learn\WRF\AtmosphericPhysics\book"
OUT = r"d:\Code\Learn\WRF\workspace\tmp"
os.makedirs(OUT, exist_ok=True)

jobs = [
    # (源页, 上边比例, 下边比例, 输出名, 放大倍数)
    ("page_0181.jpg", 0.55, 1.00, "ch15_p0181_bottom.png", 2),
    ("page_0180.jpg", 0.55, 1.00, "ch15_p0180_bottom.png", 2),
]

for src, f0, f1, out, scale in jobs:
    im = Image.open(os.path.join(BOOK, src))
    w, h = im.size
    box = (0, int(h * f0), w, int(h * f1))
    crop = im.crop(box)
    crop = crop.resize((crop.width * scale, crop.height * scale), Image.LANCZOS)
    dst = os.path.join(OUT, out)
    crop.save(dst)
    print(f"{src}: {im.size} -> crop({box}) x{scale} -> {dst} {crop.size}")