"""精确解析 drawio 的 mxGeometry（属性顺序无关），输出内容包围盒与远离主体的散落元素。"""
import pathlib, re, sys, xml.etree.ElementTree as ET

ROOT = pathlib.Path(r"d:\Code\Learn\WRF")
DRAWIO_DIR = ROOT / "workspace" / "tmp" / "mermaid" / "drawio"

for stem in sys.argv[1:] or ["code_50_solve_em_01", "code_32_module_first_rk_step_part2_01"]:
    p = DRAWIO_DIR / f"{stem}.drawio"
    tree = ET.parse(p)
    root = tree.getroot()
    # 收集所有元素：id -> (label, x, y, w, h, parent, vertex/edge)
    cells = {}
    for uo in root.iter("UserObject"):
        c = uo.find("mxCell")
        if c is not None:
            g = c.find("mxGeometry")
            cells[uo.get("id")] = {
                "label": uo.get("label", "")[:30].replace("\n", " "),
                "x": float(g.get("x", 0)) if g is not None else None,
                "y": float(g.get("y", 0)) if g is not None else None,
                "w": float(g.get("width", 0)) if g is not None else 0,
                "h": float(g.get("height", 0)) if g is not None else 0,
                "vertex": c.get("vertex") == "1",
            }
    for c in root.iter("mxCell"):
        if c.get("id") not in cells:
            g = c.find("mxGeometry")
            cells[c.get("id")] = {
                "label": c.get("value", "")[:30].replace("\n", " "),
                "x": float(g.get("x", 0)) if g is not None else None,
                "y": float(g.get("y", 0)) if g is not None else None,
                "w": float(g.get("width", 0)) if g is not None else 0,
                "h": float(g.get("height", 0)) if g is not None else 0,
                "vertex": c.get("vertex") == "1",
            }

    # 计算「含父偏移」的全局包围盒
    def global_pos(cid, _seen=None):
        it = cells.get(cid)
        if it is None or it["x"] is None:
            return None
        par = None
        for c in root.iter("mxCell"):
            if c.get("id") == cid:
                par = c.get("parent")
                break
        px = py = 0.0
        if par and par not in ("0", "1"):
            pp = global_pos(par)
            if pp:
                px, py = pp
        return it["x"] + px, it["y"] + py

    xs, ys, xe, ye = [], [], [], []
    outliers = []
    for cid, it in cells.items():
        if not it["vertex"] or it["x"] is None:
            continue
        gp = global_pos(cid)
        if gp is None:
            continue
        gx, gy = gp
        xs.append(gx); ys.append(gy); xe.append(gx + it["w"]); ye.append(gy + it["h"])
        # 离群：距主体包围盒中心超 1.5 倍主体尺寸
        if it["w"] > 0 and (gx > 3000 or gy > 3000 or gx < -1000 or gy < -1000):
            outliers.append((cid, it["label"], gx, gy, it["w"], it["h"]))

    if xs:
        print(f"=== {stem} ===")
        print(f"  顶点数 {sum(1 for c in cells.values() if c['vertex'])}，全局包围盒 x {min(xs):.0f}~{max(xe):.0f}，y {min(ys):.0f}~{max(ye):.0f}")
        print(f"  → 逻辑尺寸 {max(xe)-min(xs):.0f} x {max(ye)-min(ys):.0f}（PNG 高 8135 = 逻辑 {8135/2:.0f}）")
    if outliers:
        print(f"  离群元素 {len(outliers)} 个：")
        for cid, label, gx, gy, w, h in outliers[:12]:
            print(f"    id={cid} ({gx:.0f},{gy:.0f}) {w:.0f}x{h:.0f}  {label!r}")
    else:
        print("  无离群元素")
    print()
