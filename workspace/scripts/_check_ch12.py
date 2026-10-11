"""检查 ch12 章节：行数、图片链接有效性、公式引用计数、疑似问题扫描。"""
import re
from pathlib import Path

DOC = Path(r"d:\Code\Learn\WRF\doc")
f = DOC / "ch12_radiation_family.md"
txt = f.read_text(encoding="utf-8")
lines = txt.splitlines()
print("总行数:", len(lines), " 字符数:", len(txt))
print("中文引号检查（半角双引号数量，应为 0）:", txt.count('"'))

# 图片链接
links = re.findall(r"\]\((figs/[^)]+)\)", txt)
for l in sorted(set(links)):
    p = DOC / l
    print(("OK  " if p.exists() else "MISS"), l)

# 公式编号引用计数
tags = re.findall(r"\\tag\{([^}]+)\}", txt)
print("带 \\tag 的公式数:", len(tags))
print("公式编号示例:", tags[:8], "...", tags[-4:])

# 扫描可能的遗留问题
for pat, name in [(r"TODO|待补|FIXME", "占位符"),
                  (r"　", "全角空格"),
                  (r"？\?", "双问号")]:
    hits = [(i + 1, l) for i, l in enumerate(lines) if re.search(pat, l)]
    print(f"{name}: {len(hits)}", [h[0] for h in hits[:10]])

# 章节标题
for l in lines:
    if l.startswith("## "):
        print(l)