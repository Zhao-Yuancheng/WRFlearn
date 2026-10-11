#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""check_ascii_art.py — 检查教材 doc/ch*.md 中"字符图"的显示宽度对齐。

用法:
  python check_ascii_art.py                # 扫描 doc/ 全部 ch*.md
  python check_ascii_art.py <file.md> ...  # 指定文件

检查规则:
  R1 右边框对齐: 围栏代码块内, 连续"行尾是右边框字符(│┐┘┤...)"的行视为一个箱体,
     比较行尾右边框字符的显示宽度列(CJK/全角=2, 其余=1); 组内列不一致 → 报错。
     树形图(├──/└──, 行尾是文字)天然不参与, 无误报。
  R2 混用半角竖线: 图块内同时出现全角 │ 和半角 | 连接线 → 提示人工复核。
  只检查无语言标注或 ```text 的围栏块; ```mermaid / ```fortran 等一律跳过。
"""
import re
import sys
import unicodedata
from pathlib import Path

DOC = Path(__file__).resolve().parents[2] / "doc"
RIGHT = set("│┐┑┒┓┘┙┚┛┤┥┦┧┨┩┪╢╡╖╕╣║┃")
BOX = set("│┃┌┐└┘├┤┬┴┼─═║╔╗╚╝╠╣╦╩╬┆┇┊┋╭╮╰╯")


def dw(s: str) -> int:
    """显示宽度: 全角/CJK 记 2, 其余记 1。"""
    return sum(2 if unicodedata.east_asian_width(c) in ("W", "F") else 1 for c in s)


def fenced_blocks(lines):
    """产出 (lang, 起始行号1基, 内容行列表)。"""
    i, out = 0, []
    while i < len(lines):
        if re.match(r"^\s*```", lines[i]):
            lang = lines[i].strip().lstrip("`").strip()
            j = i + 1
            while j < len(lines) and not re.match(r"^\s*```\s*$", lines[j]):
                j += 1
            out.append((lang, i + 2, lines[i + 1:j]))
            i = j + 1
        else:
            i += 1
    return out


def check(path: Path):
    issues = []
    text = path.read_text(encoding="utf-8")
    for lang, start, body in fenced_blocks(text.splitlines()):
        if lang not in ("", "text"):
            continue
        if sum(1 for l in body if any(c in BOX for c in l)) < 3:
            continue  # 不是图
        # R2 混用半角竖线
        has_full = any("│" in l for l in body)
        has_half = any(re.search(r"\S \| |\|\S", l) for l in body)
        if has_full and has_half:
            issues.append(f"{path.name}:{start}: [R2] 图块内疑似混用半角 | 与全角 │, 请人工复核")
        # R1 右边框列一致
        group, prev_k = [], None

        def flush():
            if len(group) >= 2:
                cols = {}
                for ln, col in group:
                    cols.setdefault(col, []).append(ln)
                if len(cols) > 1:
                    main = max(cols.items(), key=lambda kv: len(kv[1]))[0]
                    for col, lns in sorted(cols.items()):
                        if col != main:
                            for ln in lns:
                                issues.append(
                                    f"{path.name}:{ln}: [R1] 右边框显示列={col}, 组主列={main}"
                                )

        for k, l in enumerate(body):
            stripped = l.rstrip()
            if stripped and stripped[-1] in RIGHT:
                col = None
                for idx, ch in enumerate(stripped):
                    if ch in RIGHT:
                        col = dw(stripped[:idx + 1])
                if prev_k is not None and k == prev_k + 1:
                    group.append((start + k, col))
                else:
                    flush()
                    group = [(start + k, col)]
                prev_k = k
            else:
                flush()
                group, prev_k = [], None
        flush()
    return issues


def main():
    targets = [Path(a) for a in sys.argv[1:]] or sorted(DOC.glob("ch*.md"))
    total = 0
    for p in targets:
        for s in check(p):
            print(s)
        total += len(check(p))
    print(f"== 共 {total} 处待复核 ==")


if __name__ == "__main__":
    main()
