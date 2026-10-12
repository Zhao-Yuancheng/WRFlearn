"""把 doc/code/code_*.md 里的 ```mermaid 块替换为 PNG 引用（图在 doc/figs/mermaid/）。
体例与教材正文一致：图片 + <details> 折叠的 HTML 注释源码。可重复运行（幂等）：
只匹配未注释的 mermaid 围栏，已回填的文件再次运行为 NOCHANGE。
"""
import re, pathlib

ROOT = pathlib.Path(r"d:\Code\Learn\WRF")
DOC_CODE = ROOT / "doc" / "code"
PNG_DIR = ROOT / "doc" / "figs" / "mermaid"

pat = re.compile(r"```mermaid\n(.*?)```", re.DOTALL)

updated = 0
for md in sorted(DOC_CODE.glob("code_*.md")):
    text = md.read_text(encoding="utf-8")
    if "```mermaid" not in text:
        continue

    state = {"idx": 0}
    problems = []

    def replacer(m):
        idx = state["idx"] + 1
        state["idx"] += 1
        label = f"{md.stem}_{idx:02d}"
        png_rel = f"../figs/mermaid/{label}.png"
        if not (PNG_DIR / f"{label}.png").exists():
            problems.append(f"{label}.png 不存在，该块保留原样")
            return m.group(0)
        content = m.group(1).rstrip("\n")
        return (
            f"![{label}]({png_rel})\n\n"
            f"<details><summary>原始 Mermaid 源码（可点击展开）</summary>\n\n"
            f"<!--\n```mermaid\n{content}\n```\n-->\n\n"
            f"</details>"
        )

    new_text, n = pat.subn(replacer, text)
    if problems:
        for p in problems:
            print(f"[WARN] {md.name}: {p}")
    if n > 0 and not problems:
        md.write_text(new_text, encoding="utf-8")
        updated += 1
        print(f"OK: {md.name} — 回填 {n} 块")
    elif n == 0:
        print(f"NOCHANGE: {md.name}")

print(f"\n=== 更新 {updated} 个 md 文件 ===")

# 复查：不应再有未注释的 mermaid 围栏
left = 0
for md in sorted(DOC_CODE.glob("code_*.md")):
    t = md.read_text(encoding="utf-8")
    # 去掉 HTML 注释后仍含 mermaid 围栏 = 漏网
    stripped = re.sub(r"<!--.*?-->", "", t, flags=re.S)
    if "```mermaid" in stripped:
        left += 1
        print(f"[遗漏] {md.name} 仍有未注释 mermaid 块")
print(f"漏网检查：{left} 个文件")
