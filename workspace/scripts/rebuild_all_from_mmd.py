"""
干净重导全流程：.mmd → .drawio（干净） → restyle（一次） → PNG
背景：之前多次 restyle 叠加导致 mxGraphModel 属性重复（background="#ffffff"×4），
      draw.io 渲染器遇到无效 XML 就输出空白画布。
策略：从 .mmd 源重新生成 .drawio，整条流水线只跑一次。
"""
import pathlib, re, subprocess, json, time, xml.etree.ElementTree as ET

ROOT = pathlib.Path(r"d:\Code\Learn\WRF")
MMD_DIR = ROOT / "workspace" / "tmp" / "mermaid"
CLEAN_DRAWIO = ROOT / "workspace" / "tmp" / "mermaid" / "drawio_clean"
FINAL_DRAWIO = ROOT / "workspace" / "tmp" / "mermaid" / "drawio_final"
PNG_DIR = ROOT / "doc" / "figs" / "mermaid"
DRAWIO_EXE = r"C:\Program Files\draw.io\draw.io.exe"

CLEAN_DRAWIO.mkdir(parents=True, exist_ok=True)
FINAL_DRAWIO.mkdir(parents=True, exist_ok=True)

# 先 restyle 导入（已最终定稿的样式参数）
import sys
sys.path.insert(0, str(ROOT / "workspace" / "scripts"))
import importlib.util
spec = importlib.util.spec_from_file_location("restyle", ROOT / "workspace" / "scripts" / "restyle_drawio.py")
restyle = importlib.util.module_from_spec(spec)
spec.loader.exec_module(restyle)

print("=" * 60)
print("阶段 1: 从 .mmd 干净转换为 .drawio")
print("=" * 60)

mmd_files = sorted(MMD_DIR.glob("*.mmd"))
for i, mmd in enumerate(mmd_files):
    clean = CLEAN_DRAWIO / f"{mmd.stem}.drawio"
    if clean.exists():
        continue  # 已经转换过就跳过
    cmd = [DRAWIO_EXE, "-x", "--timeout", "60", "-f", "xml",
           "-o", str(clean), str(mmd)]
    subprocess.run(cmd, capture_output=True, text=True, timeout=120)
    time.sleep(0.5)
    print(f"  [{i+1}/{len(mmd_files)}] {mmd.stem} → clean.drawio", end="")
    if clean.exists() and clean.stat().st_size > 500:
        print(f" ({clean.stat().st_size}B) ✓")
    else:
        print(" ✗ FAIL")

print(f"\n干净 .drawio 数：{len(list(CLEAN_DRAWIO.glob('*.drawio')))}")

print("\n" + "=" * 60)
print("阶段 2: restyle（最终版样式，只跑一次）")
print("=" * 60)

for i, clean in enumerate(sorted(CLEAN_DRAWIO.glob("*.drawio"))):
    text = clean.read_text(encoding="utf-8")
    new_text = restyle.restyle_drawio(text)
    # 额外保险：把 mxGraphModel 上重复的 background 属性清掉
    # （restyle_drawio 可能也加了，这次彻底修）
    def fix_graphmodel(m):
        attrs = m.group(1)
        # 删掉所有 background=... 属性
        attrs = re.sub(r'\s+background="[^"]*"', '', attrs)
        return '<mxGraphModel' + attrs + '>'
    new_text = re.sub(r'<mxGraphModel([^>]*)>', fix_graphmodel, new_text)

    final = FINAL_DRAWIO / clean.name
    final.write_text(new_text, encoding="utf-8")

    # 验证：background 只能有 0 个（我们不要它，draw.io 会自动给白底）
    bg_count = new_text[:500].count('background=')
    print(f"  [{i+1}] {clean.stem}: bg_count={bg_count}", end="")
    print(" ✓" if bg_count <= 1 else " ✗ bg重复!")

print("\n" + "=" * 60)
print("阶段 3: 导出 PNG（只用 --scale 2，无 --width）")
print("=" * 60)

ok = fail = 0
for i, final in enumerate(sorted(FINAL_DRAWIO.glob("*.drawio"))):
    png = PNG_DIR / f"{final.stem}.png"
    cmd = [DRAWIO_EXE, "-x", "--timeout", "60", "-f", "png",
           "--border", "10", "--scale", "2",
           "-o", str(png), str(final)]
    r = subprocess.run(cmd, capture_output=True, text=True, timeout=120)
    time.sleep(0.5)
    sz = png.stat().st_size // 1024 if png.exists() else 0
    status = "✓" if (png.exists() and sz > 100) else "✗ EMPTY"
    print(f"  [{i+1}/{len(list(FINAL_DRAWIO.glob('*.drawio')))}] {final.stem}: {status} ({sz}KB)")
    if png.exists() and sz > 100:
        ok += 1
    else:
        fail += 1

print(f"\n{'='*60}")
print(f"最终结果：{ok} 成功，{fail} 失败")
print(f"干净 drawio → {CLEAN_DRAWIO}")
print(f"restyled drawio → {FINAL_DRAWIO}")
print(f"PNG → {PNG_DIR}")
print(f"\n验证：打开一张干净 .drawio 看 vertex 属性：")
sample = next(FINAL_DRAWIO.glob("*.drawio"))
text = sample.read_text(encoding="utf-8")
v = re.search(r'<mxGraphModel[^>]*>', text)
print(f"  {v.group() if v else 'NOT FOUND'}")
