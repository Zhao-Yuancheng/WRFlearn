"""
最终导出：宽度超 1750px 的 drawio（原内部 x_max）用 --width 3400 压缩；
其余用 --scale 2 自然放大。
"""
import pathlib, subprocess, time
import xml.etree.ElementTree as ET
from PIL import Image

DRAWIO_EXE = r"C:\Program Files\draw.io\draw.io.exe"
DRAWIO_DIR = pathlib.Path(r"d:\Code\Learn\WRF\workspace\tmp\mermaid\drawio")
PNG_DIR = pathlib.Path(r"d:\Code\Learn\WRF\doc\figs\mermaid")
SCALE2_THRESHOLD = 1750  # 内部 x_max 超过此值 → 用 --width 3400；否则 --scale 2

def get_x_max(drawio_path):
    """读 drawio XML，算所有 vertex 的 x+width 最大值"""
    text = drawio_path.read_text(encoding="utf-8")
    root = ET.fromstring(text)
    x_max = 0
    for cell in root.iter('mxCell'):
        if cell.get('vertex') != '1':
            continue
        g = cell.find('mxGeometry')
        if g is None:
            continue
        try:
            x = float(g.get('x', '0'))
            w = float(g.get('width', '0'))
            x_max = max(x_max, x + w)
        except:
            pass
    return x_max

print(f"阈值：内部 x_max > {SCALE2_THRESHOLD} → --width 3400；否则 --scale 2\n")

files = sorted(DRAWIO_DIR.glob("*.drawio"))
ok = fail = 0
compressed = []
scaled = []

for i, drawio in enumerate(files):
    x_max = get_x_max(drawio)
    png = PNG_DIR / f"{drawio.stem}.png"
    
    if x_max > SCALE2_THRESHOLD:
        # 内部超宽 → 用 --width 压缩
        cmd = [DRAWIO_EXE, "-x", "--timeout", "60", "-f", "png",
               "--border", "10", "--width", "3400",
               "-o", str(png), str(drawio)]
        method = "--width 3400"
        compressed.append(drawio.stem)
    else:
        # 内部正常 → --scale 2 自然放大
        cmd = [DRAWIO_EXE, "-x", "--timeout", "60", "-f", "png",
               "--border", "10", "--scale", "2",
               "-o", str(png), str(drawio)]
        method = "--scale 2"
        scaled.append(drawio.stem)
    
    subprocess.run(cmd, capture_output=True, text=True, timeout=120)
    time.sleep(0.3)
    
    try:
        w, h = Image.open(png).size if png.exists() else (0, 0)
        sz = png.stat().st_size // 1024
        flag = "⚠" if w > 3500 else " "
        print(f"{flag} [{i+1:>2}] {drawio.stem:<48} x_max={x_max:>6.0f} → {method:<14} {w:>5}×{h:<5} ({sz:>4}KB)")
        ok += 1
    except:
        print(f"✗ [{i+1:>2}] {drawio.stem:<48} FAILED")
        fail += 1

# 汇总
print(f"\n{'='*60}")
print(f"压缩导出：{len(compressed)} 张（内部超宽）")
print(f"  {', '.join(compressed)}")
print(f"自然放大：{len(scaled)} 张")
print(f"成功：{ok}  失败：{fail}")

# 最终尺寸检查
print(f"\n最终 PNG 尺寸分布：")
print(f"  最大宽度：", end="")
max_w = 0
for png in sorted(PNG_DIR.glob("*.png")):
    try:
        w, h = Image.open(png).size
        max_w = max(max_w, w)
    except:
        pass
print(f"{max_w}px")
