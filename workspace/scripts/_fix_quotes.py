# -*- coding: utf-8 -*-
"""一次性：把章文正文中的 ASCII 双引号转全角（跳过 fenced code 块，保 mermaid 语法）。
用法: python _fix_quotes.py <md 路径>"""
import sys

p = sys.argv[1]
with open(p, encoding="utf-8") as f:
    text = f.read()
lines = text.split("\n")
out = []
in_code = False
open_q = True
n_conv = 0
for ln in lines:
    if ln.strip().startswith("```"):
        in_code = not in_code
        out.append(ln)
        continue
    if in_code:
        out.append(ln)
        continue
    res = []
    for ch in ln:
        if ch == '"':
            res.append("\u201c" if open_q else "\u201d")
            open_q = not open_q
            n_conv += 1
        else:
            res.append(ch)
    out.append("".join(res))
new = "\n".join(out)
with open(p, "w", encoding="utf-8") as f:
    f.write(new)
print("converted:", n_conv, "remaining ascii quotes:", new.count('"'))