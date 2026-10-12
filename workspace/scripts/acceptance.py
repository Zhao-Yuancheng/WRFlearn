#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""acceptance.py — 《WRF 源码精读》文库验收（v2 自动全量版）：
对 doc/code/ 下全部 code_*.md 的每个指纹块：
1) 按指纹 source 定位源文件（ROOT/source/WRFv4.8.0/WRFV4.8.0/<source>）
2) 剥离显示层（!file: 行 + L{05d} 前缀），校验行号连续覆盖 ranges
3) 与源文件对应行逐字符比对 + range_md5 复核
4) 指涉存在性：文中提到的 code_*.md / chNN_*.md 必须存在于 doc/ 或 doc/code/
"""
import hashlib
import re
from pathlib import Path

ROOT = Path(r"D:\Code\Learn\WRF")
SRCDIR = ROOT / "source/WRFv4.8.0/WRFV4.8.0"
DOCCODE = ROOT / "doc/code"
LN_RE = re.compile(r"^\s*L(\d+)\s\s(.*)$")
BLOCK_RE = re.compile(
    r"<!-- code_extract .*?source: (\S+).*?ranges: (\S+).*?file_md5: ([0-9a-f]+)"
    r".*?range_md5: ([0-9a-f]+).*?-->\s*```fortran\n(.*?)\n```",
    re.DOTALL,
)


def strip_display(block_text: str, s: int, e: int):
    out = []
    for ln in block_text.split("\n"):
        if ln.startswith("!file:"):
            continue
        m = LN_RE.match(ln)
        if not m:
            raise ValueError(f"无行号前缀: {ln[:60]!r}")
        n = int(m.group(1))
        if n != s + len(out):
            raise ValueError(f"行号不连续 {s + len(out)}->{n}")
        out.append(m.group(2))
    if len(out) != e - s + 1:
        raise ValueError(f"行数不符（实 {len(out)}，应 {e - s + 1}）")
    return out


def md5_of(text: str) -> str:
    return hashlib.md5(text.encode("latin-1")).hexdigest()


fails = 0
nblocks = 0
src_cache = {}
for doc in sorted(DOCCODE.glob("code_*.md")):
    text = doc.read_text(encoding="utf-8")
    for (src_rel, rng, file_md5, range_md5, block) in BLOCK_RE.findall(text):
        nblocks += 1
        if src_rel not in src_cache:
            p = SRCDIR / src_rel
            if not p.exists():
                print(f"[FAIL] {doc.name} {rng}: 源文件不存在 {src_rel}")
                fails += 1
                src_cache[src_rel] = None
                continue
            src_cache[src_rel] = p.read_bytes().decode("latin-1").split("\n")
        lines = src_cache[src_rel]
        if lines is None:
            continue
        s, e = [int(x) for x in rng.replace("L", "").split("-")]
        try:
            stripped = strip_display(block, s, e)
        except ValueError as exc:
            print(f"[FAIL] {doc.name} {rng}: {exc}")
            fails += 1
            continue
        srcseg = lines[s - 1 : e]
        bad = [i for i, (a, b) in enumerate(zip(stripped, srcseg)) if a != b.rstrip("\r")]
        if bad or md5_of("".join(x + "\n" for x in stripped)) != range_md5:
            print(f"[FAIL] {doc.name} {rng}: {len(bad)} 行不符，首处 L{s + bad[0] if bad else 'md5'}")
            fails += 1
        else:
            print(f"[OK]   {doc.name:44s} {rng:16s} {e - s + 1:5d} 行")

# 指涉存在性
refs = set()
for doc in sorted(DOCCODE.glob("code_*.md")):
    for m in re.finditer(r"(code_\d+[ab]?_[a-z_]+\.md|ch\d+_[a-z_]+\.md)", doc.read_text(encoding="utf-8")):
        refs.add(m.group(1))
missing = [r for r in sorted(refs) if not (ROOT / "doc" / r).exists() and not (DOCCODE / r).exists()]
print(f"\n指纹块 {nblocks} 个；指涉文件 {len(refs)} 个，缺失 {len(missing)} 个")
for r in missing:
    print(f"  [MISSING] {r}")
    fails += 1

print("\n验收结果:", "FAIL" if fails else "ALL PASS")
