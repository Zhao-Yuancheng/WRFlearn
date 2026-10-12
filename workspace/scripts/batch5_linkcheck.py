# -*- coding: utf-8 -*-
"""批次 5 全书校阅：交叉引用 + 死链清查（扫描 doc\ 26 个教材文件）

检查类别：
  A. markdown 链接/图片 —— 文件存在性（相对 doc\ 解析）
  B. 章节指涉 —— 第 N 章 / chNN / app_x / 附录 x
  C. 小节指涉 —— §N.N(.N) 与全角括号（N.M）—— 对照目标章标题实测
  D. 书页引用 —— book\page_NNNN.jpg 存在性 + 印刷页换算（N+14）
  E. 反引号路径 —— workspace/ doc/ figs/ source 树（WRF/WPS 源码锚点）
  F. 跨章表引用 —— 表 N.M（N in 10..21）目标章字面串核对
  G. 外部链接 —— http(s) 统计（不核验）
代码围栏内内容一律跳过；HTML 注释行保留（其中含 .mmd 源码指引）。
"""
import os, re, glob, sys
from collections import defaultdict

PROJ = r"d:\Code\Learn\WRF"
DOC = os.path.join(PROJ, "doc")
BOOK = os.path.join(PROJ, "AtmosphericPhysics", "book")
OUT = os.path.join(PROJ, "workspace", "logs", "batch5_linkcheck.md")

def find_root(marker_rel, name):
    for cand in ("source", ".source"):
        base = os.path.join(PROJ, cand)
        if not os.path.isdir(base):
            continue
        for sub in sorted(os.listdir(base)):
            m1 = os.path.join(base, sub)
            if os.path.isdir(m1) and os.path.isfile(os.path.join(m1, marker_rel)):
                return m1
            if os.path.isdir(m1):
                for sub2 in sorted(os.listdir(m1)):
                    m2 = os.path.join(m1, sub2)
                    if os.path.isdir(m2) and os.path.isfile(os.path.join(m2, marker_rel)):
                        return m2
    return None

WRF_ROOT = find_root(os.path.join("phys", "module_microphysics_driver.F"), "WRF")
WPS_ROOT = find_root(os.path.join("ungrib", "buildinc"), "WPS")
if WPS_ROOT is None:
    # WPS 标记退化为目录存在
    for cand in ("source", ".source"):
        base = os.path.join(PROJ, cand)
        if os.path.isdir(base):
            for sub in sorted(os.listdir(base)):
                if "WPS" in sub.upper():
                    p = os.path.join(base, sub)
                    if os.path.isdir(os.path.join(p, "ungrib")):
                        WPS_ROOT = p
                        break
        if WPS_ROOT:
            break

# ---------- 收集 26 个教材文件 ----------
ch_files, app_files, other = {}, {}, []
for f in sorted(glob.glob(os.path.join(DOC, "*.md"))):
    b = os.path.basename(f)
    m = re.match(r"ch(\d{2})_", b)
    if m:
        ch_files[int(m.group(1))] = f
        continue
    m = re.match(r"app_([a-d])_", b)
    if m:
        app_files[m.group(1)] = f
        continue
    if b == "index.md":
        other.append(f)
FILES = list(ch_files.values()) + list(app_files.values()) + other
ALL_NAMES = {os.path.basename(f) for f in FILES}

# ---------- 各章小节号实测 ----------
def parse_headings(path):
    secs = set()
    for line in open(path, encoding="utf-8"):
        m = re.match(r"^#{2,5}\s*(\d+(?:\.\d+)*)[\s　]", line)
        if m:
            secs.add(m.group(1))
    return secs

CH_SECS = {n: parse_headings(p) for n, p in ch_files.items()}

report = defaultdict(list)
stats = defaultdict(int)

FENCE = re.compile(r"^\s*```")
LINK = re.compile(r"!?\[([^\]]*)\]\(([^)\s]+)\)")
CODESPAN = re.compile(r"`([^`]*)`")

RE_ZHANG = re.compile(r"第\s*(\d+)\s*章")
RE_SEC = re.compile(r"[§＃]\s?(\d{1,2})(?:\.(\d+))?(?:\.(\d+))?")
RE_SEC_FW = re.compile(r"（(\d{2})(\.\d+)(?:\.\d+)?）")   # 全角括号小节指涉（10–21）
RE_SEC_HW = re.compile(r"\((\d{2})(\.\d+)(?:\.\d+)?\)")   # 半角（同上）
RE_CHREF = re.compile(r"\bch(\d{2})\b(?!_)")
RE_CHFILE = re.compile(r"\b(ch\d{2}_\w+\.md|app_[a-d]_\w+\.md)\b")
RE_APP = re.compile(r"\bapp_([a-d])\b(?!_)")
RE_APPENDIX = re.compile(r"附录\s*([a-dA-D])\b(?!章)")
RE_BOOKPAGE = re.compile(r"page_(\d{4})")
RE_YIN = re.compile(r"印刷页\s*(\d+)")
RE_WS = re.compile(r"\b(workspace[/\\][\w./\\-]+)")
RE_DOCF = re.compile(r"\b(doc[/\\][\w./\\-]+)")
RE_FIGS = re.compile(r"(?<![\w/])(figs/[\w./-]+\.(?:png|jpe?g|svg))")
RE_WRF = re.compile(r"`((?:phys|dyn_em|main|share|frame|external|Registry|run|test|inc|var|arch|cpl)/[\w./-]+)`")
RE_WPS = re.compile(r"`((?:geogrid|ungrib|metgrid)/[\w./-]+)`")
RE_TBL = re.compile(r"表\s*(1\d|2[01])(\.\d+)")
RE_FIG_HI = re.compile(r"图\s*(1\d|2[01])(\.\d+)")
RE_HTTP = re.compile(r"https?://[^\s`\])】】））]+")

def sec_exists(ch, s2, s3):
    if ch not in CH_SECS:
        return False
    secs = CH_SECS[ch]
    if s2 is None:
        return True  # 只指章级 §N，章存在即可
    cand = f"{ch}.{s2}" if s3 is None else f"{ch}.{s2}.{s3}"
    if cand in secs:
        return True
    # 章.0 与章级互认（§13.0 也是标题）
    return f"{ch}.{s2}" in secs

def check_line(fname, ln, text, codespans):
    # A. 链接（在去码span前的原文本上找）
    for m in LINK.finditer(text):
        tgt = m.group(2)
        if tgt.startswith(("http://", "https://")):
            stats["外部链接"] += 1
            continue
        if tgt.startswith("#"):
            continue
        p = os.path.normpath(os.path.join(DOC, tgt))
        if not os.path.exists(p):
            report["A死链"].append(f"{fname}:{ln}: [{m.group(1)[:30]}]({tgt})")
        stats["A链接"] += 1
    # G. http
    for m in RE_HTTP.finditer(text):
        pass  # 已在 LINK 内计；纯文本 URL 不逐一报
    # 去掉行内码 span 后做语义指涉；码 span 单独走路径检查
    stripped = CODESPAN.sub(" ⟦CS⟧ ", text)
    for cs in codespans:
        # E. 码内路径
        for m in RE_WS.finditer(cs):
            rel = m.group(1).replace("\\", "/")
            p = os.path.join(PROJ, rel)
            if not os.path.exists(p):
                report["E路径缺失"].append(f"{fname}:{ln}: `{cs[:80]}` → {rel}")
            stats["E路径"] += 1
        for m in RE_DOCF.finditer(cs):
            p = os.path.join(PROJ, m.group(1).replace("\\", "/"))
            if not os.path.exists(p):
                report["E路径缺失"].append(f"{fname}:{ln}: `{cs[:80]}` → {m.group(1)}")
            stats["E路径"] += 1
        for m in RE_FIGS.finditer(cs):
            p = os.path.join(DOC, m.group(1))
            if not os.path.exists(p):
                report["E路径缺失"].append(f"{fname}:{ln}: `{cs[:80]}` → {m.group(1)}")
            stats["E路径"] += 1
        for m in RE_WRF.finditer(cs):
            if WRF_ROOT:
                p = os.path.join(WRF_ROOT, m.group(1).replace("/", os.sep))
                if not os.path.exists(p):
                    report["E源码锚点缺失"].append(f"{fname}:{ln}: `{m.group(1)}` (WRF_ROOT={os.path.basename(WRF_ROOT)})")
                stats["E源码"] += 1
        for m in RE_WPS.finditer(cs):
            if WPS_ROOT:
                p = os.path.join(WPS_ROOT, m.group(1).replace("/", os.sep))
                if not os.path.exists(p):
                    report["E源码锚点缺失"].append(f"{fname}:{ln}: `{m.group(1)}` (WPS_ROOT={os.path.basename(WPS_ROOT)})")
                stats["E源码"] += 1
        # D. 书页（码内 book\page_NNNN.jpg 为主形态）
        for m in RE_BOOKPAGE.finditer(cs):
            page = int(m.group(1))
            p = os.path.join(BOOK, f"page_{page:04d}.jpg")
            if not os.path.isfile(p):
                report["D书页缺失"].append(f"{fname}:{ln}: page_{page:04d}.jpg 不存在（{cs[:60]}）")
            stats["D书页"] += 1
    # D-换算：整行同时含印刷页与 page_ 且各恰一个
    yins = RE_YIN.findall(text)
    pages = RE_BOOKPAGE.findall(text)
    if len(yins) == 1 and len(pages) == 1:
        if int(pages[0]) != int(yins[0]) + 14:
            report["D换算不符"].append(f"{fname}:{ln}: 印刷页 {yins[0]} ↔ page_{pages[0]}（应为 {int(yins[0])+14:04d}）")
    # B/C. 语义指涉（码 span 之外的正文）
    for m in RE_ZHANG.finditer(stripped):
        n = int(m.group(1))
        if n > 21 or n == 0:
            report["B章号异常"].append(f"{fname}:{ln}: 第 {n} 章")
            continue
        # “书第 N 章/《大气物理学》第 N 章”指书，跳过
        pre = stripped[max(0, m.start()-12):m.start()]
        if "书" in pre or "》" in pre:
            stats["B书章引用(跳过)"] += 1
            continue
        if n not in ch_files:
            report["B章缺失"].append(f"{fname}:{ln}: 第 {n} 章（无对应文件；可能指书——请人工复核）")
        else:
            stats["B章引用"] += 1
    for m in RE_CHREF.finditer(stripped):
        n = int(m.group(1))
        if n not in ch_files:
            report["B章缺失"].append(f"{fname}:{ln}: ch{n:02d}")
        else:
            stats["B章引用"] += 1
    for m in RE_CHFILE.finditer(stripped):
        if m.group(1) not in ALL_NAMES:
            report["B文件缺失"].append(f"{fname}:{ln}: {m.group(1)}")
        stats["B文件引用"] += 1
    for m in RE_CHFILE.finditer(" ".join(codespans)):
        if m.group(1) not in ALL_NAMES:
            report["B文件缺失"].append(f"{fname}:{ln}: `{m.group(1)}`")
        stats["B文件引用"] += 1
    for m in RE_APP.finditer(stripped):
        if m.group(1) not in app_files:
            report["B附录缺失"].append(f"{fname}:{ln}: app_{m.group(1)}")
    for m in RE_APPENDIX.finditer(stripped):
        if m.group(1).lower() not in app_files:
            report["B附录缺失"].append(f"{fname}:{ln}: 附录 {m.group(1)}")
        else:
            stats["B附录引用"] += 1
    for m in RE_SEC.finditer(stripped):
        ch = int(m.group(1))
        if ch > 21 or ch == 0:
            continue  # §3.3 方案等，非教材章
        if ch not in ch_files:
            report["C小节异常"].append(f"{fname}:{ln}: §{m.group(0)} 目标章不存在")
            continue
        if not sec_exists(ch, m.group(2), m.group(3)):
            report["C小节缺失"].append(f"{fname}:{ln}: {m.group(0)} 不在 ch{ch:02d} 标题中")
        stats["C小节引用"] += 1
    for pat, tag in ((RE_SEC_FW, "全角"), (RE_SEC_HW, "半角")):
        for m in pat.finditer(stripped):
            ch = int(m.group(1))
            if not (10 <= ch <= 21):
                continue
            if not sec_exists(ch, m.group(2).lstrip("."), m.group(3).lstrip(".") if False else None):
                # 括号指涉只到 N.M 两级
                pass
            cand = f"{ch}{m.group(2)}"
            if ch in CH_SECS and cand not in CH_SECS[ch] and f"{ch}{m.group(2)}" not in CH_SECS[ch]:
                report["C小节缺失"].append(f"{fname}:{ln}: （{ch}{m.group(2)}）不在 ch{ch:02d} 标题中")
    # F. 跨章表引用
    for m in RE_TBL.finditer(stripped):
        ch = int(m.group(1))
        lit = m.group(0)
        if ch in ch_files:
            body = open(ch_files[ch], encoding="utf-8").read()
            if lit not in body:
                report["F表缺失"].append(f"{fname}:{ln}: “{lit}” 未在 ch{ch:02d} 出现")
            stats["F表引用"] += 1
    for m in RE_FIG_HI.finditer(stripped):
        report["F图号复核"].append(f"{fname}:{ln}: “{m.group(0)}”——我方图未编号，请确认是否误指（书图章号应 ≤6）")

# ---------- 主扫描 ----------
for path in FILES:
    fname = os.path.basename(path)
    fenced = False
    for ln, line in enumerate(open(path, encoding="utf-8"), 1):
        if FENCE.match(line):
            fenced = not fenced
            continue
        if fenced:
            continue
        spans = CODESPAN.findall(line)
        check_line(fname, ln, line, spans)

# ---------- 输出 ----------
os.makedirs(os.path.dirname(OUT), exist_ok=True)
with open(OUT, "w", encoding="utf-8") as f:
    f.write(f"# 批次 5 校阅：交叉引用 + 死链清查报告\n\n")
    f.write(f"- WRF_ROOT = {WRF_ROOT}\n- WPS_ROOT = {WPS_ROOT}\n")
    f.write(f"- 扫描文件：{len(FILES)} 个（ch 21 + app 4 + index）\n\n")
    f.write("## 统计\n\n")
    for k in sorted(stats):
        f.write(f"- {k}: {stats[k]}\n")
    f.write("\n")
    order = ["A死链", "B章缺失", "B章号异常", "B文件缺失", "B附录缺失",
             "C小节缺失", "C小节异常", "D书页缺失", "D换算不符",
             "E路径缺失", "E源码锚点缺失", "F表缺失", "F图号复核"]
    for cat in order:
        items = report.get(cat, [])
        f.write(f"\n## {cat}（{len(items)}）\n\n")
        for it in items:
            f.write(f"- {it}\n")

print(f"WRF_ROOT={WRF_ROOT}")
print(f"WPS_ROOT={WPS_ROOT}")
print("stats:", dict(stats))
for cat in ["A死链", "B章缺失", "B章号异常", "B文件缺失", "B附录缺失",
            "C小节缺失", "C小节异常", "D书页缺失", "D换算不符",
            "E路径缺失", "E源码锚点缺失", "F表缺失", "F图号复核"]:
    print(f"{cat}: {len(report.get(cat, []))}")
print("report ->", OUT)
