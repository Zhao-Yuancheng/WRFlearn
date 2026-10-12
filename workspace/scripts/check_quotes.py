#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""check_quotes.py — 检查文库 md：围栏外不得出现引号（代码块内允许）。
豁免：贴着字母的撇号（O'Gorman 人名、c'/d' 与 w'q' 等数学 prime 记号）。"""
import re
import sys
from pathlib import Path

for p in sys.argv[1:]:
    lines = Path(p).read_text(encoding="utf-8").split("\n")
    infence = False
    bad = []
    for i, ln in enumerate(lines, 1):
        s = ln.strip()
        if s.startswith("```"):
            infence = not infence
            continue
        if infence:
            continue
        if '"' in ln:
            bad.append((i, ln[:90]))
            continue
        for m in re.finditer(r"'", ln):
            before = ln[m.start() - 1] if m.start() > 0 else ""
            after = ln[m.start() + 1] if m.start() + 1 < len(ln) else ""
            if not (before.isalpha() or after.isalpha()):
                bad.append((i, ln[:90]))
                break
    print(f"{p}: total {len(lines)} lines, bad-quote lines {len(bad)}")
    for i, ln in bad[:12]:
        print(f"  L{i}: {ln}")
