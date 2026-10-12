"""
回填：把 doc/*.md 里的 ```mermaid``` 代码块替换为 draw.io 导出的 PNG 图片引用。
原始 mermaid 源码保留在 HTML 注释里，方便将来还原。
"""
import re, json, pathlib, shutil

ROOT = pathlib.Path(r"d:\Code\Learn\WRF")
DOC = ROOT / "doc"
MMD_DIR = ROOT / "workspace" / "tmp" / "mermaid"
MAP_PATH = MMD_DIR / "map.json"

mapping = json.loads(MAP_PATH.read_text(encoding="utf-8"))

pat = re.compile(r"```mermaid\n(.*?)```", re.DOTALL)

# 反向映射：label -> block content (用于匹配，确保安全替换)
mmd_content_cache = {}
for mmd_file in MMD_DIR.glob("*.mmd"):
    mmd_content_cache[mmd_file.stem] = mmd_file.read_text(encoding="utf-8").rstrip("\n")

updated = 0
for md_name, entries in mapping.items():
    md_path = DOC / md_name
    if not md_path.exists():
        print(f"SKIP (not found): {md_name}")
        continue

    text = md_path.read_text(encoding="utf-8")

    # 按出现顺序替换所有 mermaid 块
    state = {"idx": 0}
    def replacer(m):
        content = m.group(1).rstrip("\n")
        idx_in_md = state["idx"]
        if idx_in_md >= len(entries):
            return m.group(0)  # 不应发生
        entry = entries[idx_in_md]
        label = entry["label"]
        png_rel = f"figs/mermaid/{label}.png"

        # 验证：抽取的内容应该等于 mmd 文件内容
        expected = mmd_content_cache.get(label, "")
        if content != expected:
            print(f"  MISMATCH in {md_name} block {idx_in_md} (label={label}) — using by-position")

        # 替换：图片引用 + 原始 mermaid 注释
        # HTML 注释包裹 mermaid 源码，防止将来误删
        html_comment = f"<!--\n```mermaid\n{content}\n```\n-->"
        replacement = (
            f"![{label}]({png_rel})\n\n"
            f"<details><summary>原始 Mermaid 源码（可点击展开）</summary>\n\n"
            f"{html_comment}\n\n"
            f"</details>"
        )
        state["idx"] += 1
        return replacement

    new_text, n = pat.subn(replacer, text)
    if n > 0:
        md_path.write_text(new_text, encoding="utf-8")
        updated += 1
        print(f"OK: {md_name} — 替换 {n} 个块")
    else:
        print(f"NOCHANGE: {md_name}")

print(f"\n=== 更新 {updated} 个 md 文件 ===")
