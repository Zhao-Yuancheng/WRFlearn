#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
code_extract.py — 《WRF 源码精读》文库保真抽取工具 (v1.2)

原则：禁手抄。所有进入 doc/code/*.md 的代码块必须由本脚本从源文件按字节抽取，
并附带可复核的 md5 指纹。

v1.1 显示层约定（内容保真不变）：
  - 每个代码块首行为插入的文件标记注释：!file: <源相对路径>    L<起>-L<止>    (<label>)
  - 源行逐行前缀行号：L{05d}  <原行>（如 L00424  SUBROUTINE ...）
  - md5 指纹始终对"原始内容"（无前缀、无 file 行）计算；verify 剥离显示层后比对。

子命令:
  list  <src>                        列出全部子程序/函数边界（名、起止、行数）
  full  <src> <out>                  全文抽取 -> 保真 markdown 代码块 + 指纹
  sub   <src> <out> <name> [name...] 抽取指定子程序/函数（各段独立 fence + 指纹）
  lines <src> <out> <start> <end>    原始行段抽取（含两端，1-based）
  verify <src> <out>                 校验 out 中所有指纹块与源文件逐位一致
  assemble <src> <skel> <out>        骨架文件占位符注入保真块后写 out
                                     {{CODE:full}} / {{CODE:subname}} / {{CODE:L123-L456}}
                                     v1.2 多源：{{CODE:<WRF根相对路径>:full|subname|Ls-Le}}
"""
import hashlib
import re
import sys
from pathlib import Path

TOOL = "code_extract.py v1.2"
LN_RE = re.compile(r"^\s*L(\d+)\s\s(.*)$")  # 显示层行号前缀

START_RE = re.compile(
    r"^\s*(?:recursive|pure|elemental|real|double\s+precision|integer|logical)\s+"
    r"?(subroutine|function)\s+([a-z][a-z0-9_]*)",
    re.IGNORECASE,
)
START_RE2 = re.compile(r"^\s*(subroutine|function)\s+([a-z][a-z0-9_]*)", re.IGNORECASE)
END_RE = re.compile(r"^\s*end\s+(subroutine|function)\b\s*([a-z][a-z0-9_]*)?", re.IGNORECASE)
BARE_END_RE = re.compile(r"^\s*end\s*$", re.IGNORECASE)  # F77 风格裸 end（仅 FUNCTION 回退用）


def load_lines(src: Path):
    data = src.read_bytes()
    text = data.decode("latin-1")  # Fortran 源码按字节保真，不做编码转换
    text = text.replace("\r\n", "\n").replace("\r", "\n")  # CRLF/CR 行尾归一化（gocart 等个别文件为 CRLF）
    lines = text.split("\n")
    if lines and lines[-1] == "":
        lines.pop()
    return lines


def md5_of(text: str) -> str:
    return hashlib.md5(text.encode("latin-1")).hexdigest()


def is_free_format(src: Path) -> bool:
    return src.suffix.lower() in (".f90", ".f95", ".f03", ".f08")


def is_comment_line(raw: str, free_format: bool = False) -> bool:
    if not raw:
        return False
    if raw[0] == "!":
        return True
    if not free_format and raw[0] in "Cc*":  # 固定格式首列注释（自由格式 C 开头是标识符）
        return True
    return False


def scan_units(src: Path):
    """扫描子程序/函数边界（栈式，支持 F90 CONTAINS 嵌套）。
    返回 [(name, kind, start, end)]（1-based 行号）；嵌套时内层单元先入表。"""
    lines = load_lines(src)
    ff = is_free_format(src)
    units = []
    stack = []  # (name, kind, start)
    i = 0
    n = len(lines)
    while i < n:
        raw = lines[i]
        if is_comment_line(raw, ff):
            i += 1
            continue
        if stack:
            name, kind, start = stack[-1]
            em = END_RE.match(raw)
            if em and em.group(1).lower() == kind:
                ename = em.group(2)
                if ename and ename.lower() != name.lower():
                    sys.exit(
                        f"[FATAL] {src}: END 配对名不符: "
                        f"{name}(L{start}) vs {ename}(L{i+1})"
                    )
                units.append((name, kind, start, i + 1))
                stack.pop()
                i += 1
                continue
            if kind == "function" and BARE_END_RE.match(raw):
                units.append((name, kind, start, i + 1))  # F77 风格裸 end
                stack.pop()
                i += 1
                continue
        m = START_RE.match(raw) or START_RE2.match(raw)
        if m:
            stack.append((m.group(2), m.group(1).lower(), i + 1))
        i += 1
    if stack:
        name, kind, start = stack[-1]
        sys.exit(
            f"[FATAL] {src}: 未找到 END {kind} 与 {name}(L{start}) 配对"
        )
    return units


def fence(lines_seg, start=None, filemark=None, label=None):
    """生成显示层代码块：可选 !file: 首行 + 逐行 L{05d} 行号前缀。"""
    body = []
    if filemark and start:
        hdr = f"!file: {filemark}    L{start}-L{start + len(lines_seg) - 1}"
        if label:
            hdr += f"    ({label})"
        body.append(hdr)
    for i, ln in enumerate(lines_seg):
        n = start + i if start else 0
        body.append(f"L{n:05d}  " + ln if start else ln)
    content = "\n".join(body)
    if "```" in content:
        sys.exit("[FATAL] 源码片段含 ``` 序列，围栏冲突，需人工处理")
    return "```fortran\n" + content + "\n```"


def header_comment(source_rel: str, ranges, file_lines: int, file_md5: str, extra=""):
    rs = ", ".join(ranges)
    return (
        f"<!-- code_extract {TOOL}\n"
        f"source: {source_rel}\n"
        f"ranges: {rs}\n"
        f"file_lines: {file_lines}\n"
        f"file_md5: {file_md5}\n"
        f"display: line-numbered (strip L-prefix and !file: line to restore)\n"
        f"{extra}-->"
    )


def cmd_list(src: Path):
    units = scan_units(src)
    lines = load_lines(src)
    print(f"{src}  总行数 {len(lines)}  子程序/函数 {len(units)} 个")
    prev_end = 0
    for name, kind, s, e in units:
        gap = s - prev_end - 1
        gapnote = f"   （与上一单元间隔 {gap} 行）" if prev_end else ""
        print(f"  L{s:5d}-L{e:5d}  {e - s + 1:5d} 行  {kind:10s} {name}{gapnote}")
        prev_end = e
    if len(lines) > prev_end:
        print(f"  L{prev_end + 1:5d}-L{len(lines):5d}  {len(lines) - prev_end:5d} 行  （末尾间隙）")


def extract_ranges(src: Path, ranges, source_rel: str):
    lines = load_lines(src)
    raw_all = "\n".join(lines) + "\n"
    file_md5 = md5_of(raw_all)
    out = []
    for (s, e, label) in ranges:
        seg = [ln + "\n" for ln in lines[s - 1 : e]]
        seg_md5 = md5_of("".join(seg))
        extra = f"range_md5: {seg_md5}\nseg_lines: {e - s + 1}\n"
        if label:
            extra += f"label: {label}\n"
        out.append(header_comment(source_rel, [f"L{s}-L{e}"], len(lines), file_md5, extra))
        out.append(fence([ln.rstrip("\n") for ln in seg], start=s, filemark=source_rel, label=label))
    return out


def resolve_units(src: Path, names):
    units = scan_units(src)
    index = {u[0].lower(): u for u in units}
    chosen = []
    for nm in names:
        key = nm.lower()
        if key not in index:
            sys.exit(f"[FATAL] 子程序 {nm} 不在 {src} 中。可用: {', '.join(u[0] for u in units)}")
        chosen.append(index[key])
    return chosen


def cmd_sub(src: Path, out: Path, names, source_rel: str):
    chosen = resolve_units(src, names)
    ranges = [(s, e, f"{kind} {name}") for name, kind, s, e in chosen]
    parts = extract_ranges(src, ranges, source_rel)
    out.write_text("\n\n".join(parts) + "\n", encoding="utf-8")
    print(f"[OK] {len(ranges)} 段 -> {out}")


def cmd_lines(src: Path, out: Path, s: int, e: int, source_rel: str):
    parts = extract_ranges(src, [(s, e, "")], source_rel)
    out.write_text("\n\n".join(parts) + "\n", encoding="utf-8")
    print(f"[OK] L{s}-L{e} -> {out}")


def cmd_full(src: Path, out: Path, source_rel: str):
    lines = load_lines(src)
    raw_all = "\n".join(lines) + "\n"
    file_md5 = md5_of(raw_all)
    body = fence(lines, start=1, filemark=source_rel, label=None)
    doc = header_comment(source_rel, ["L1-L%d" % len(lines)], len(lines), file_md5) + "\n\n" + body + "\n"
    out.write_text(doc, encoding="utf-8")
    print(f"[OK] 全文 {len(lines)} 行 md5={file_md5} -> {out}")


def strip_display(block_text: str, ranges: str):
    """剥离显示层（!file: 行 + L{05d} 前缀），还原原始内容并校验行号连续。"""
    s, e = [int(x) for x in ranges.replace("L", "").split("-")]
    out = []
    for ln in block_text.split("\n"):
        if ln.startswith("!file:"):
            continue
        m = LN_RE.match(ln)
        if not m:
            sys.exit(f"[FATAL] 显示层剥离失败（无行号前缀）: {ln[:60]!r}")
        n = int(m.group(1))
        if n != s + len(out):
            sys.exit(f"[FATAL] 行号不连续: 期望 {s + len(out)} 实得 {n}")
        out.append(m.group(2))
    if len(out) != e - s + 1:
        sys.exit(f"[FATAL] 行数与指纹 ranges {ranges} 不符（实际 {len(out)} 行）")
    return "".join(x + "\n" for x in out)


def cmd_verify(src: Path, out: Path):
    """重读 out 中每个指纹块，剥离显示层后按 ranges 重新抽取并比对 range_md5。"""
    text = out.read_text(encoding="utf-8")
    blocks = re.findall(
        r"<!-- code_extract .*?source: (\S+).*?ranges: (\S+).*?range_md5: ([0-9a-f]+).*?-->\s*```fortran\n(.*?)\n```",
        text,
        re.DOTALL,
    )
    if not blocks:
        sys.exit("[FATAL] 未找到任何指纹块")
    lines = load_lines(src)
    bad = 0
    for (srcname, rng, md5v, block) in blocks:
        seg = strip_display(block, rng)
        if md5_of(seg) != md5v:
            print(f"[FAIL] {rng} md5 不符")
            bad += 1
    if bad:
        sys.exit(f"[FATAL] {bad} 段校验失败")
    print(f"[OK] {len(blocks)} 段全部与源文件逐位一致")


PH_RE = re.compile(r"\{\{CODE:(?:([^:{}]+):)?(full|[A-Za-z_][A-Za-z0-9_]*|L\d+-L\d+)\}\}")


class SourceBook:
    """多源缓存：按 WRFV4.8.0 根相对路径懒加载行表、单元索引与文件指纹。"""

    def __init__(self, default_src: Path):
        self.default = default_src
        self.cache = {}

    def _root(self) -> Path:
        p = self.default.resolve()
        for anc in [p] + list(p.parents):
            if anc.name == "WRFV4.8.0":
                return anc
        sys.exit(f"[FATAL] 无法从 {self.default} 定位 WRFV4.8.0 根")

    def get(self, rel: str | None):
        """rel=None -> CLI 默认源；否则相对 WRFV4.8.0 根的路径。返回 (src_path, lines, units, index, file_md5)。"""
        key = rel or "__default__"
        if key not in self.cache:
            src = self.default if rel is None else self._root() / rel
            if not src.exists():
                sys.exit(f"[FATAL] 占位符源文件不存在: {src}")
            lines = load_lines(src)
            units = scan_units(src)
            file_md5 = md5_of("".join(ln + "\n" for ln in lines))
            self.cache[key] = (src, lines, units, {u[0].lower(): u for u in units}, file_md5)
        return self.cache[key]


def cmd_assemble(src: Path, skel: Path, out: Path, source_rel: str):
    book = SourceBook(src)
    text = skel.read_text(encoding="utf-8")

    def block_for(rel, src_path, lines, file_lines, file_md5, s, e, label=None):
        seg = lines[s - 1 : e]
        md5v = md5_of("".join(ln + "\n" for ln in seg))
        srcrel = source_rel if rel is None else str(src_path).replace("\\", "/").split("WRFV4.8.0/", 1)[1]
        extra = f"range_md5: {md5v}\nseg_lines: {e - s + 1}\n"
        if label:
            extra += f"label: {label}\n"
        hdr = header_comment(srcrel, [f"L{s}-L{e}"], file_lines, file_md5, extra)
        return hdr + "\n\n" + fence(seg, start=s, filemark=srcrel, label=label)

    def repl(m):
        rel, key = m.group(1), m.group(2)
        src_path, lines, units, index, file_md5 = book.get(rel)
        if key == "full":
            return block_for(rel, src_path, lines, len(lines), file_md5, 1, len(lines))
        mm = re.match(r"^L(\d+)-L(\d+)$", key)
        if mm:
            s, e = int(mm.group(1)), int(mm.group(2))
            return block_for(rel, src_path, lines, len(lines), file_md5, s, e)
        u = index.get(key.lower())
        if u is None:
            sys.exit(f"[FATAL] 占位符 {{CODE:{key}}}: 无此子程序（源 {src_path.name}）。可用: {', '.join(x[0] for x in units)}")
        name, kind, s, e = u
        return block_for(rel, src_path, lines, len(lines), file_md5, s, e, label=f"{kind} {name}")

    result = PH_RE.sub(repl, text)
    if "{{CODE:" in result:
        bad = re.findall(r"\{\{CODE:[^}]*\}\}", result)
        sys.exit(f"[FATAL] 未解析的占位符: {bad}")
    out.write_text(result, encoding="utf-8")
    nblocks = len(re.findall(r"<!-- code_extract", result))
    print(f"[OK] assemble {nblocks} 个保真块 -> {out}")


def main():
    if len(sys.argv) < 3:
        print(__doc__)
        sys.exit(2)
    cmd = sys.argv[1]
    src = Path(sys.argv[2])
    # 源相对路径（以 WRFV4.8.0 根为基准，自动从绝对路径推断）
    root = "WRFV4.8.0"
    p = str(src).replace("\\", "/")
    source_rel = p[p.find(root) + len(root) + 1 :] if root + "/" in p else src.name

    if cmd == "list":
        cmd_list(src)
    elif cmd == "full":
        cmd_full(src, Path(sys.argv[3]), source_rel)
    elif cmd == "sub":
        cmd_sub(src, Path(sys.argv[3]), sys.argv[4:], source_rel)
    elif cmd == "lines":
        cmd_lines(src, Path(sys.argv[3]), int(sys.argv[4]), int(sys.argv[5]), source_rel)
    elif cmd == "verify":
        cmd_verify(src, Path(sys.argv[3]))
    elif cmd == "assemble":
        cmd_assemble(src, Path(sys.argv[3]), Path(sys.argv[4]), source_rel)
    else:
        print(__doc__)
        sys.exit(2)


if __name__ == "__main__":
    main()
