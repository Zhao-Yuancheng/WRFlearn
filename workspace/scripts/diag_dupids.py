"""查 UserObject/mxCell id 重复 + 每个顶点 id 对照渲染缺失区间。"""
import pathlib, sys
import xml.etree.ElementTree as ET
from collections import Counter

ROOT = pathlib.Path(r"d:\Code\Learn\WRF")
DRAWIO_DIR = ROOT / "workspace" / "tmp" / "mermaid" / "drawio"

for stem in sys.argv[1:]:
    p = DRAWIO_DIR / f"{stem}.drawio"
    root = ET.parse(p).getroot()
    ids = []
    for uo in root.iter("UserObject"):
        ids.append(("UO", uo.get("id"), (uo.get("label") or "")[:20].replace("\n", " ")))
    for c in root.iter("mxCell"):
        if c.get("id"):
            ids.append(("cell", c.get("id"), (c.get("value") or "")[:20]))
    cnt = Counter(i[1] for i in ids)
    dups = {k: v for k, v in cnt.items() if v > 1}
    print(f"=== {stem}: 元素 {len(ids)} 个，重复 id: {dups if dups else '无'} ===")
    if dups:
        for kind, i, label in ids:
            if i in dups:
                print(f"  [{kind}] id={i}  {label!r}")
    # 全 id 序列（看编号空洞）
    seq = sorted((i for _, i, _ in ids if i and i.isdigit()), key=int)
    print(f"  数字 id 序列: {seq}")
    print()
