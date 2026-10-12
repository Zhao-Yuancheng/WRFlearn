"""
抽取 doc/*.md 中所有 ```mermaid ... ``` 代码块到独立 .mmd 文件。
输出：
  workspace/tmp/mermaid/*.mmd      — 每个图一个文件
  workspace/tmp/mermaid/map.json   — 来源映射（md文件 → 块序号 → 块内容起止）
  workspace/tmp/mermaid/summary.csv — 摘要
"""
import re, json, csv, os, pathlib

ROOT = pathlib.Path(r"d:\Code\Learn\WRF")
DOC = ROOT / "doc"
OUT = ROOT / "workspace" / "tmp" / "mermaid"
OUT.mkdir(parents=True, exist_ok=True)

# 清理旧 .mmd
for f in OUT.glob("*.mmd"):
    f.unlink()

md_files = sorted(DOC.glob("ch*.md")) + sorted(DOC.glob("app*.md")) + [DOC / "index.md"]
md_files = [f for f in md_files if f.exists()]

pat = re.compile(r"```mermaid\n(.*?)```", re.DOTALL)

mapping = {}  # md_filename -> [{idx, start_line, end_line, label, mmd_file}]
summary_rows = []

global_idx = 0
for md in md_files:
    text = md.read_text(encoding="utf-8")
    # 带行号的匹配
    lines = text.split("\n")
    blocks = list(pat.finditer(text))

    if not blocks:
        continue

    md_name = md.name
    mapping[md_name] = []

    for i, m in enumerate(blocks):
        content = m.group(1).rstrip("\n")
        # 确定起止行
        before = text[:m.start()]
        start_line = before.count("\n") + 1  # ```mermaid 所在行
        content_lines = content.count("\n") + 1
        end_line = start_line + content_lines + 1  # ``` 所在行

        # 推断图的类型和简短标签（从第一行非注释）
        first_line = content.strip().split("\n")[0].strip()
        diag_type = first_line.split()[0] if first_line else "unknown"
        # 从 md 文件名 + 块序号生成标签
        stem = md.stem  # e.g. ch21_solve_em_dynamics
        label = f"{stem}_{i+1:02d}"

        mmd_path = OUT / f"{label}.mmd"
        mmd_path.write_text(content + "\n", encoding="utf-8")

        entry = {
            "idx_in_md": i,
            "global_idx": global_idx,
            "label": label,
            "diagram_type": diag_type,
            "start_line": start_line,
            "end_line": end_line,
            "mmd_file": mmd_path.name,
            "content_preview": first_line[:60],
        }
        mapping[md_name].append(entry)
        summary_rows.append([global_idx, md_name, i+1, label, diag_type, start_line, mmd_path.name, first_line[:80]])
        global_idx += 1

(OUT / "map.json").write_text(json.dumps(mapping, ensure_ascii=False, indent=2), encoding="utf-8")

with open(OUT / "summary.csv", "w", encoding="utf-8-sig", newline="") as f:
    w = csv.writer(f)
    w.writerow(["global_idx", "md_file", "idx_in_md", "label", "diagram_type", "start_line", "mmd_file", "preview"])
    w.writerows(summary_rows)

print(f"抽取完成：{global_idx} 个 mermaid 块，来自 {len(mapping)} 个 md 文件")
print(f"输出目录：{OUT}")
print(f"映射表：{OUT / 'map.json'}")
print(f"摘要：{OUT / 'summary.csv'}")

# 打印类型分布
from collections import Counter
types = Counter(r[4] for r in summary_rows)
print(f"\n图类型分布：")
for t, c in types.most_common():
    print(f"  {t}: {c}")
