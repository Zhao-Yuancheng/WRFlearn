"""code_50 画布撑爆源查找：多页/隐藏元素/全部 mxPoint 极值/UserObject 结构。"""
import pathlib, xml.etree.ElementTree as ET

ROOT = pathlib.Path(r"d:\Code\Learn\WRF")
p = ROOT / "workspace" / "tmp" / "mermaid" / "drawio" / "code_50_solve_em_01.drawio"
root = ET.parse(p).getroot()

print("mxfile 子元素:", [(ch.tag, dict(ch.attrib)) for ch in root if ch.tag != "diagram"][:5])
diagrams = [ch for ch in root if ch.tag == "diagram"]
print(f"diagram 页数: {len(diagrams)}")
for d in diagrams:
    model = d.find(".//mxGraphModel")
    n_uo = len(list(model.iter("UserObject")))
    n_cell = len(list(model.iter("mxCell")))
    print(f"  page {d.get('name')!r}: UserObject={n_uo}, mxCell={n_cell}")

for di, d in enumerate(diagrams):
    print(f"\n--- 第 {di+1} 页元素 ---")
    for c in d.iter("mxCell"):
        style = c.get("style") or ""
        hidden = 'visible=0' in style or 'opacity=0' in style or c.get("visible") == "0"
        g = c.find("mxGeometry")
        pts = [(m.get("as"), m.get("x"), m.get("y")) for m in g.iter("mxPoint")] if g is not None else []
        far = [t for t in pts if t[1] and (abs(float(t[1])) > 1300 or abs(float(t[2] or 0)) > 1300)]
        if hidden or far or c.get("vertex") == "1" or c.get("edge") == "1":
            tag = "HIDDEN " if hidden else ""
            geo = ""
            if g is not None:
                geo = f"geo=({g.get('x')},{g.get('y')},{g.get('width')},{g.get('height')})"
            print(f"  {tag}{c.tag} id={c.get('id')} v={c.get('vertex')} e={c.get('edge')} {geo} pts={pts if far else ''}")
