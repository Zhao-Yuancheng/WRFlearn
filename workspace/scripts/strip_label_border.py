"""去掉 drawio 边线标签的灰色描边框（labelBorderColor=#cccccc）。
白色 labelBackgroundColor 保留——用于遮住标签下方的连线，白底在白页上不可见。
先统计样式值分布，再统一替换，避免误伤手动加的其他样式。
"""
import pathlib, re, collections

DRAWIO_DIR = pathlib.Path(r"d:\Code\Learn\WRF\workspace\tmp\mermaid\drawio")

vals = collections.Counter()
changed = 0
for f in sorted(DRAWIO_DIR.glob("*.drawio")):
    t = f.read_text(encoding="utf-8")
    vals.update(re.findall(r"labelBorderColor=(#[0-9a-fA-F]+|none)", t))
    vals.update(re.findall(r"labelBackgroundColor=(#[0-9a-fA-F]+|none)", t))
    new, n = re.subn(r"labelBorderColor=#cccccc;?", "", t)
    if n:
        f.write_text(new, encoding="utf-8")
        changed += 1
        print(f"{f.name}: {n} 处")

print(f"\n共改 {changed} 个文件")
print("label*Color 值分布:", dict(vals))
