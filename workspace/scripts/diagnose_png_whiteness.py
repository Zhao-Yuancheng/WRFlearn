"""诊断 drawio 样式 + PNG 实际内容"""
import pathlib, re, struct, zlib

ROOT = pathlib.Path(r"d:\Code\Learn\WRF")
DRAWIO_DIR = ROOT / "workspace" / "tmp" / "mermaid" / "drawio"
PNG_DIR = ROOT / "doc" / "figs" / "mermaid"
ARCHIVE = PNG_DIR / "_archived"

# 对比：当前 PNG vs 归档 PNG（上一次 restyle 前的版本）
print("=== PNG 文件大小对比（当前 vs 归档）===")
print(f"{'label':<45} {'当前KB':>8} {'归档KB':>8} {'差':>6}")
for f in sorted(PNG_DIR.glob("*.png")):
    archived = ARCHIVE / f.name
    cur = f.stat().st_size // 1024
    arc = archived.stat().st_size // 1024 if archived.exists() else -1
    diff = cur - arc if arc > 0 else "?"
    print(f"{f.stem:<45} {cur:>8} {arc:>8} {diff:>6}")

# 检查 drawio XML 里的实际样式
print("\n=== drawio XML 实际样式抽查 ===")
for drawio in sorted(DRAWIO_DIR.glob("*.drawio"))[:3]:
    text = drawio.read_text(encoding="utf-8")
    # 抽所有 vertex mxCell 的 style
    vertex_styles = re.findall(r'<mxCell[^>]*vertex="1"[^>]*style="([^"]+)"', text)
    edge_styles = re.findall(r'<mxCell[^>]*edge="1"[^>]*style="([^"]+)"', text)
    print(f"\n--- {drawio.name} ---")
    print(f"  vertex 数: {len(vertex_styles)}")
    print(f"  edge 数:   {len(edge_styles)}")
    # 前 2 个 vertex 的 style 关键属性
    for i, s in enumerate(vertex_styles[:3]):
        fill = re.search(r'fillColor=([^;]+)', s)
        stroke = re.search(r'strokeColor=([^;]+)', s)
        font = re.search(r'fontSize=(\d+)', s)
        shadow = re.search(r'shadow=(\d+)', s)
        rhombus = "rhombus" in s
        print(f"  vertex[{i}]: fill={fill.group(1) if fill else '?'}, stroke={stroke.group(1) if stroke else '?'}, fontSize={font.group(1) if font else '?'}, shadow={shadow.group(1) if shadow else '?'}, rhombus={rhombus}")

# 直接检查 PNG 里有没有像素数据（不是全白）
print("\n=== PNG 像素采样（非零像素数）===")
try:
    from PIL import Image
    for f in sorted(PNG_DIR.glob("*.png"))[:5]:
        img = Image.open(f)
        arr = list(img.getdata())
        total = len(arr)
        # 非白像素（R/G/B 任一 < 250）
        nonwhite = sum(1 for px in arr if isinstance(px, tuple) and (min(px[:3]) < 245))
        pct = 100 * nonwhite / total if total > 0 else 0
        print(f"  {f.name}: {img.size[0]}x{img.size[1]}, total={total}, nonwhite={nonwhite} ({pct:.1f}%)")
except ImportError:
    print("PIL 未安装，跳过像素检查")
