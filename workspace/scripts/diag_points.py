"""列出 drawio 全部顶点（label, 全局坐标）+ 全部 mxPoint 坐标分布，找撑爆包围盒的元素。"""
import sys, xml.etree.ElementTree as ET, pathlib

ROOT = pathlib.Path(r"d:\Code\Learn\WRF")
DRAWIO_DIR = ROOT / "workspace" / "tmp" / "mermaid" / "drawio"

for stem in sys.argv[1:]:
    p = DRAWIO_DIR / f"{stem}.drawio"
    root = ET.parse(p).getroot()
    print(f"=== {stem} ===")

    # id -> cell 元素
    all_cells = {}
    for c in root.iter("mxCell"):
        all_cells[c.get("id")] = c

    print("-- 顶点 --")
    for c in root.iter("mxCell"):
        if c.get("vertex") != "1":
            continue
        g = c.find("mxGeometry")
        x = float(g.get("x", 0)) if g is not None else 0
        y = float(g.get("y", 0)) if g is not None else 0
        w = float(g.get("width", 0)) if g is not None else 0
        h = float(g.get("height", 0)) if g is not None else 0
        label = (c.get("value") or "")[:28].replace("\n", " ")
        par = c.get("parent")
        print(f"  id={str(c.get('id')):>4} par={str(par):>3} ({x:>6.0f},{y:>6.0f}) {w:>4.0f}x{h:<4.0f} {label!r}")

    print("-- 边端点（source/target 固定点，>1500 = 异常）--")
    n_bad = 0
    for c in root.iter("mxCell"):
        if c.get("edge") != "1":
            continue
        g = c.find("mxGeometry")
        if g is None:
            continue
        pts = []
        for m in g.iter("mxPoint"):
            px, py = float(m.get("x", 0)), float(m.get("y", 0))
            if abs(px) > 1500 or abs(py) > 1500:
                pts.append((m.get("as"), px, py))
        if pts:
            n_bad += 1
            label = (c.get("value") or "")[:20].replace("\n", " ")
            src = c.get("source") or "-"
            tgt = c.get("target") or "-"
            print(f"  edge id={c.get('id')} {src}->{tgt} {label!r}: {pts}")
    if not n_bad:
        print("  （无远端点）")
    print()
