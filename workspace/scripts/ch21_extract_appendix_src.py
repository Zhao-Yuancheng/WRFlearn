# -*- coding: utf-8 -*-
"""ch21 收官：从 doc/chNN_*.md 抽取 术语速查 / 常见错误·速查 / 延伸阅读 三类段落，
供附录 b/c/d 汇编。输出 workspace/tmp/app_extract_{terms,errors,refs}.md。
"""
import io
import os
import re

DOC = r'd:/Code/Learn/WRF/doc'
TMP = r'd:/Code/Learn/WRF/workspace/tmp'
os.makedirs(TMP, exist_ok=True)

PATTERNS = {
    'terms': re.compile(r'^#{1,4}\s.*(术语速查|中英术语|术语对照)'),
    'errors': re.compile(r'^#{1,4}\s.*(常见错误|速查|事故|排错|坑)'),
    'refs': re.compile(r'^#{1,4}\s.*(延伸阅读|参考文献|References)'),
}

def chapter_sort_key(fn):
    m = re.match(r'ch(\d+)', fn)
    return (0, int(m.group(1))) if m else (1, fn)

def extract(kind, pattern):
    out = ['# 抽取：%s' % kind, '']
    for fn in sorted(os.listdir(DOC), key=chapter_sort_key):
        if not re.match(r'ch\d+.*\.md$', fn):
            continue
        path = os.path.join(DOC, fn)
        with io.open(path, encoding='utf-8', errors='replace') as f:
            lines = f.readlines()
        i = 0
        while i < len(lines):
            if pattern.match(lines[i]):
                # 取到下一个同级或更高级标题
                lvl = len(re.match(r'^(#+)', lines[i]).group(1))
                j = i + 1
                buf = [lines[i]]
                while j < len(lines):
                    s = lines[j]
                    m = re.match(r'^(#+)', s)
                    if m and len(m.group(1)) <= lvl:
                        break
                    buf.append(s)
                    j += 1
                out.append('<!-- from %s -->' % fn)
                out.extend(buf)
                out.append('')
                i = j
            else:
                i += 1
    return out

if __name__ == '__main__':
    for kind, pat in PATTERNS.items():
        body = extract(kind, pat)
        outp = os.path.join(TMP, 'app_extract_%s.md' % kind)
        with io.open(outp, 'w', encoding='utf-8') as f:
            f.write('\n'.join(body))
        print(kind, '->', outp, '(%d lines)' % len(body))
