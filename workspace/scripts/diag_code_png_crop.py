"""诊断 20 张文库 PNG 的截断/空白问题：
1. drawio 头部 page 属性 + XML 内容包围盒 vs 页面尺寸
2. PNG 非白像素包围盒（四边留白 → 贴边=截断嫌疑）
"""
import pathlib, re

ROOT = pathlib.Path(r"d:\Code\Learn\WRF")
DRAWIO_DIR = ROOT / "workspace" / "tmp" / "mermaid" / "drawio"
PNG_DIR = ROOT / "doc" / "figs" / "mermaid"
from PIL import Image

print(f"{'label':<42} {'page':>4} {'页WxH':>12} {'XML包围盒':>16} {'PNG尺寸':>12} {'内容包围盒':>14} {'贴边':>6}")
for d in sorted(DRAWIO_DIR.glob("code_*.drawio")):
    text = d.read_text(encoding="utf-8")
    model = re.search(r'<mxGraphModel([^>]*)>', text)
    attrs = model.group(1) if model else ""
    page = re.search(r'page="(\d)"', attrs)
    page = page.group(1) if page else "?"
    pw = re.search(r'pageWidth="(\d+)"', attrs)
    ph = re.search(r'pageHeight="(\d+)"', attrs)
    pwv, phv = int(pw.group(1)) if pw else 0, int(ph.group(1)) if ph else 0

    # XML 内容包围盒（顶层坐标近似，容器子节点不计偏移，仅作参考）
    xs, ys, xe, ye = [], [], [], []
    for m in re.finditer(r'<mxGeometry (?:[^>]*?)x="(-?[\d.]+)"(?:[^>]*?)y="(-?[\d.]+)"(?:[^>]*?)width="([\d.]+)"(?:[^>]*?)height="([\d.]+)"', text):
        x, y, w, h = (float(v) for v in m.groups())
        if w > 2000 and h > 2000:   # 容器可疑巨块跳过
            continue
        xs.append(x); ys.append(y); xe.append(x + w); ye.append(y + h)
    bb = f"{min(xs):.0f},{min(ys):.0f}~{max(xe):.0f},{max(ye):.0f}" if xs else "?"

    png = PNG_DIR / f"{d.stem}.png"
    img = Image.open(png).convert("RGB")
    small = img.resize((min(img.width, 800), min(img.height, 1400)))
    px = small.load()
    W, H = small.size
    minx, miny, maxx, maxy = W, H, -1, -1
    for yy in range(H):
        for xx in range(W):
            r, g, b = px[xx, yy]
            if min(r, g, b) < 240:
                if xx < minx: minx = xx
                if xx > maxx: maxx = xx
                if yy < miny: miny = yy
                if yy > maxy: maxy = yy
    content_bb = f"{minx},{miny}~{maxx},{maxy}" if maxx >= 0 else "EMPTY"
    edges = []
    if maxx >= 0:
        if minx <= 2: edges.append("L")
        if miny <= 2: edges.append("T")
        if maxx >= W - 3: edges.append("R")
        if maxy >= H - 3: edges.append("B")
    tag = ",".join(edges) if edges else "ok"

    print(f"{d.stem:<42} {page:>4} {pwv}x{phv:<8} {bb:>16} {img.width}x{img.height:<6} {content_bb:>14} {tag:>6}")
