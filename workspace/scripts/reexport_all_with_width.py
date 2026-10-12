"""统一用 --width 3400（≤3500 阈值）重新导出所有 36 张 drawio"""
import pathlib, subprocess, time
from PIL import Image

DRAWIO_EXE = r"C:\Program Files\draw.io\draw.io.exe"
DRAWIO_DIR = pathlib.Path(r"d:\Code\Learn\WRF\workspace\tmp\mermaid\drawio")
PNG_DIR = pathlib.Path(r"d:\Code\Learn\WRF\doc\figs\mermaid")
TARGET_W = 3400  # 最终 PNG 宽度，draw.io 会按比例缩放保持纵横比

print(f"统一导出：--width {TARGET_W}px（保持纵横比）\n")

files = sorted(DRAWIO_DIR.glob("*.drawio"))
ok = fail = 0
results = []

for i, drawio in enumerate(files):
    png = PNG_DIR / f"{drawio.stem}.png"
    cmd = [DRAWIO_EXE, "-x", "--timeout", "60", "-f", "png",
           "--border", "10",
           "--width", str(TARGET_W),
           "-o", str(png), str(drawio)]
    r = subprocess.run(cmd, capture_output=True, text=True, timeout=120)
    time.sleep(0.3)
    
    status = "✓" if (png.exists() and png.stat().st_size > 100) else "✗"
    sz = png.stat().st_size // 1024 if png.exists() else 0
    
    # 实际 PNG 尺寸
    try:
        w, h = Image.open(png).size if png.exists() else (0, 0)
    except:
        w, h = 0, 0
    
    flag = "⚠" if w > 3500 else " "
    results.append((drawio.stem, w, h, sz))
    print(f"{flag} [{i+1:>2}/{len(files)}] {drawio.stem:<48} {w:>5}×{h:<5} ({sz:>4}KB)")
    
    if status == "✓": ok += 1
    else: fail += 1

# 汇总
oversize = [(s,w,h,kb) for s,w,h,kb in results if w > 3500]
print(f"\n{'='*60}")
print(f"完成：{ok} 成功，{fail} 失败")
print(f"超宽 (>3500px)：{len(oversize)} 张")
for s,w,h,kb in oversize:
    print(f"  {s}: {w}×{h} ({kb}KB)")
