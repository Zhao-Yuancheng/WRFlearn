"""量 PNG 尺寸 + 找超宽 + 看对应 drawio 的 mxGeometry 位置分布"""
import pathlib, re, json

ROOT = pathlib.Path(r"d:\Code\Learn\WRF")
PNG_DIR = ROOT / "doc" / "figs" / "mermaid"
DRAWIO_DIR = ROOT / "workspace" / "tmp" / "mermaid" / "drawio"
THRESHOLD = 3500

# 量 PNG 尺寸（PIL）
from PIL import Image
items = []
for png in sorted(PNG_DIR.glob("*.png")):
    try:
        img = Image.open(png)
        w, h = img.size
        items.append((png.stem, w, h, png.stat().st_size // 1024))
    except Exception as e:
        items.append((png.stem, 0, 0, 0))

print(f"{'stem':<48} {'宽':>5} {'高':>5} {'KB':>6} {'状态':>8}")
print("-" * 75)
oversize = []
for stem, w, h, kb in items:
    status = "超宽!" if w > THRESHOLD else ""
    if w > THRESHOLD:
        oversize.append((stem, w, h))
    print(f"{stem:<48} {w:>5} {h:>5} {kb:>6} {status:>8}")

print(f"\n超宽（>{THRESHOLD}px）共 {len(oversize)} 张：")
for stem, w, h in oversize:
    print(f"  {stem}: {w}×{h}")

# 对每张超宽图，分析 drawio mxGeometry 的 x 分布（看节点横向跨度）
print("\n=== 超宽图的 mxGeometry 位置分析 ===")
for stem, w, h in oversize:
    drawio = DRAWIO_DIR / f"{stem}.drawio"
    if not drawio.exists():
        print(f"  {stem}: drawio 不存在")
        continue
    text = drawio.read_text(encoding="utf-8")
    # 抽所有 vertex mxGeometry x,y,width,height
    cells = re.findall(r'<mxCell[^>]*vertex="1"[^>]*id="([^"]+)"[^>]*value="([^"]*)"[^>]*>\s*<mxGeometry[^>]*x="([^"]*)"[^>]*y="([^"]*)"[^>]*width="([^"]*)"[^>]*height="([^"]*)"', text)
    # 还有一种结构：mxCell ... ><mxGeometry x=".." y=".." width=".." height=".."
    if not cells:
        cells = re.findall(r'<mxCell[^>]*vertex="1"[^>]*value="([^"]*)"[^>]*><mxGeometry[^>]*x="([^"]*)"[^>]*y="([^"]*)"[^>]*width="([^"]*)"[^>]*height="([^"]*)"', text)
    
    xs = []; ys = []; widths = []
    for c in cells:
        try:
            if len(c) == 5:
                xs.append(float(c[2])); ys.append(float(c[3])); widths.append(float(c[4]))
            elif len(c) == 4:
                xs.append(float(c[1])); ys.append(float(c[2])); widths.append(float(c[3]))
        except:
            pass
    
    if xs:
        x_min, x_max = min(xs), max(x + wd for x, wd in zip(xs, widths))
        y_min, y_max = min(ys), max(ys)
        span = x_max - x_min
        print(f"\n  {stem}:")
        print(f"    vertex 数={len(cells)}")
        print(f"    x 跨度: {span:.0f}px (从 {x_min:.0f} 到 {x_max:.0f})")
        print(f"    y 跨度: {y_max - y_min:.0f}px")
        print(f"    PNG 尺寸: {w}×{h}")
        print(f"    节点宽均值: {sum(widths)/len(widths):.0f}")
        # 前 3 个节点的值（mermaid label）
        for i, c in enumerate(cells[:3]):
            val = c[1] if len(c) == 5 else c[0]
            val_short = val[:40].replace("&#xa;", " ")
            print(f"    node[{i}]: x={xs[i]:.0f} \"{val_short}\"")
