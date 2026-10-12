"""
从 doc/*.md 中提取隐藏在 HTML 注释里的 mermaid 源码。

md 中的结构：
  ![label](figs/mermaid/label.png)

  <details><summary>原始 Mermaid 源码（可点击展开）</summary>

  <!--
  ```mermaid
  ...源码...
  ```
  -->

  </details>

处理后：
  1. 源码存入 workspace/mermaid/<label>.mmd（与 tmp 区分，长期存档）
  2. md 里的 details 块替换为一行干净引用注释：
     <!-- Mermaid 源码 → workspace/mermaid/<label>.mmd -->
  3. 生成 workspace/mermaid/index.json 做 label → md_file / 源码路径 / PNG 路径 映射
"""
import pathlib, re, json, csv

ROOT = pathlib.Path(r"d:\Code\Learn\WRF")
DOC = ROOT / "doc"
OUT = ROOT / "workspace" / "mermaid"
OUT.mkdir(parents=True, exist_ok=True)

# 匹配整段：<details>...<!-- ```mermaid ... ``` -->...</details>
# 用 re.DOTALL 跨行
BLOCK_PAT = re.compile(
    r'(<details><summary>原始 Mermaid 源码.*?</summary>\s*\n*)'
    r'<!--\s*\n'
    r'```mermaid\n'
    r'(.*?)'
    r'```\s*\n'
    r'-->\s*\n*'
    r'</details>',
    re.DOTALL
)

# 反向从 mmd 文件名拿 label → md 文件 映射
MMD_TMP = ROOT / "workspace" / "tmp" / "mermaid"
MAP = {}
if (MMD_TMP / "map.json").exists():
    MAP = json.loads((MMD_TMP / "map.json").read_text(encoding="utf-8"))
label_to_md = {}
for md_name, entries in MAP.items():
    for e in entries:
        label_to_md[e["label"]] = md_name

summary = []  # 最终汇总

md_files = sorted(DOC.glob("ch*.md")) + sorted(DOC.glob("app*.md")) + [DOC / "index.md"]
md_files = [f for f in md_files if f.exists()]

print(f"扫描 {len(md_files)} 个 md 文件...\n")

total_extracted = 0
for md_path in md_files:
    text = md_path.read_text(encoding="utf-8")
    original_len = len(text)

    def extract_and_replace(m):
        global total_extracted
        mermaid_src = m.group(2).rstrip("\n")
        # 从 mermaid 源码推断 label（不一定可靠，用 label_to_md 或从上下文拿）
        # 先看前一行有没有 ![xxx](figs/mermaid/xxx.png)
        before = text[:m.start()]
        img_match = re.findall(r'!\[([^\]]*)\]\(figs/mermaid/([a-zA-Z0-9_]+)\.png\)', before)
        label = img_match[-1][1] if img_match else "unknown"

        # 写 mmd
        mmd_path = OUT / f"{label}.mmd"
        mmd_path.write_text(mermaid_src + "\n", encoding="utf-8")

        md_name = label_to_md.get(label, md_path.name)
        png_rel = f"figs/mermaid/{label}.png"

        total_extracted += 1
        summary.append({
            "label": label,
            "md_file": md_name,
            "mmd_file": f"workspace/mermaid/{label}.mmd",
            "png_rel": png_rel,
            "diagram_type": mermaid_src.strip().split("\n")[0].split()[0] if mermaid_src.strip() else "?",
            "source_lines": len(mermaid_src.split("\n")),
        })

        # 替换成干净的 HTML 注释标记（单行，不污染正文）
        return f"<!-- Mermaid 源码 → workspace/mermaid/{label}.mmd -->"

    new_text, count = BLOCK_PAT.subn(extract_and_replace, text)

    if count > 0:
        md_path.write_text(new_text, encoding="utf-8")
        print(f"✓ {md_path.name}: 提取 {count} 个 mermaid 块")
    # 如果 count==0，说明这个 md 没 mermaid 源码 details 块（可能已被替换为文本或本来就没有）

print(f"\n{'='*60}")
print(f"共提取 {total_extracted} 个 mermaid 源码块 → {OUT}")

# 写汇总 index.json
index = {
    "extract_time": "2026-10-11",
    "total": total_extracted,
    "md_base": "doc/",
    "mmd_base": "workspace/mermaid/",
    "items": summary,
}
(OUT / "index.json").write_text(json.dumps(index, ensure_ascii=False, indent=2), encoding="utf-8")

# 也写一个 CSV 方便筛选
with open(OUT / "index.csv", "w", encoding="utf-8-sig", newline="") as f:
    w = csv.writer(f)
    w.writerow(["label", "md_file", "mmd_file", "png_rel", "diagram_type", "source_lines"])
    for row in summary:
        w.writerow([row[k] for k in ["label", "md_file", "mmd_file", "png_rel", "diagram_type", "source_lines"]])

print(f"索引：{OUT / 'index.json'}")
print(f"索引：{OUT / 'index.csv'}")

# 打印各 md 剩余的 mermaid 源码来源情况
print(f"\n{'='*60}")
print("各 md 保留状态：")
for s in summary:
    print(f"  {s['label']:<40} ← {s['md_file']:<35} ({s['diagram_type']}, {s['source_lines']} 行)")
