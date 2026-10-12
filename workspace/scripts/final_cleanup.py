"""收尾清理：.bak 备份 + 孤儿 PNG + 引号验证。"""
import pathlib, shutil, re, json

ROOT = pathlib.Path(r"d:\Code\Learn\WRF")
DOC = ROOT / "doc"
BAK_DIR = ROOT / "workspace" / "tmp" / "backups_textreplace"
PNG_ARCHIVE = DOC / "figs" / "mermaid" / "_archived"

BAK_DIR.mkdir(parents=True, exist_ok=True)
PNG_ARCHIVE.mkdir(parents=True, exist_ok=True)

# --- 1. 移 .bak 文件 ---
bak_files = list(DOC.glob("*.md.bak_before_textreplace"))
for f in bak_files:
    dst = BAK_DIR / f.name
    shutil.move(str(f), str(dst))
print(f"✓ 移动 {len(bak_files)} 个 .bak → {BAK_DIR}")

# --- 2. 找出 md 文件实际仍引用的 figs/mermaid/*.png ---
text = ""
for md in sorted(DOC.glob("ch*.md")) + sorted(DOC.glob("app*.md")) + [DOC / "index.md"]:
    if md.exists():
        text += md.read_text(encoding="utf-8") + "\n"

referenced = set(re.findall(r'figs/mermaid/([a-z0-9_]+\.png)', text))
print(f"\n仍被 md 引用的 PNG: {len(referenced)} 个")
for r in sorted(referenced):
    print(f"  ✓ {r}")

# 全部 PNG
all_pngs = set(p.name for p in (DOC / "figs" / "mermaid").glob("*.png"))
orphans = all_pngs - referenced
print(f"\n孤儿 PNG（不再被引用）: {len(orphans)} 个")
for o in sorted(orphans):
    src = DOC / "figs" / "mermaid" / o
    dst = PNG_ARCHIVE / o
    shutil.move(str(src), str(dst))
    print(f"  → {o}")

print(f"\n✓ 孤儿 PNG 已移至 {PNG_ARCHIVE}")

# --- 3. 最终统计 ---
remaining = sorted(referenced)
print(f"\n{'='*60}")
print(f"最终状态：")
print(f"  保留 draw.io PNG：{len(remaining)} 张（复杂图 / 有菱形分叉 / 有容器子图）")
print(f"  替换为文本：{len(bak_files)} 张（表格 / 列表 / ASCII 箭头链）")
print(f"{'='*60}")
print("保留的 PNG：")
for n in remaining:
    print(f"  {n}")
