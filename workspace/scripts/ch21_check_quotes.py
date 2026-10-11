# -*- coding: utf-8 -*-
"""检查 markdown 代码块（``` 围栏）之外的残余英文双引号。"""
import io
import sys

for p in sys.argv[1:]:
    inblk = False
    hits = 0
    with io.open(p, encoding='utf-8', errors='replace') as f:
        for i, l in enumerate(f, 1):
            if l.strip().startswith('```'):
                inblk = not inblk
                continue
            if '"' in l and not inblk:
                hits += 1
                print(p.split('/')[-1], i, l.rstrip()[:110])
    print(p.split('/')[-1], 'outside-code ascii quotes:', hits)
