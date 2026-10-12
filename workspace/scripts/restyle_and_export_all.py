"""对 drawio 目录里保留的 20 张重 restyle + 重导。"""
import sys, pathlib
sys.path.insert(0, r"d:\Code\Learn\WRF\workspace\scripts")
from restyle_drawio import process_file, export_png

DRAWIO_DIR = pathlib.Path(r"d:\Code\Learn\WRF\workspace\tmp\mermaid\drawio")
PNG_DIR = pathlib.Path(r"d:\Code\Learn\WRF\doc\figs\mermaid")

files = sorted(DRAWIO_DIR.glob("*.drawio"))
print(f"重 restyle + 重导 {len(files)} 张\n")
ok = fail = 0
for i, f in enumerate(files):
    out = process_file(f, DRAWIO_DIR)  # --overwrite 模式：覆盖原文件
    png = PNG_DIR / f"{out.stem}.png"
    r = export_png(out, png)
    sz = png.stat().st_size // 1024 if png.exists() else 0
    status = "OK" if r else "FAIL"
    print(f"[{i+1}/{len(files)}] {f.stem}: {status} ({sz}KB)")
    if r: ok += 1
    else: fail += 1
print(f"\n完成：{ok} 成功，{fail} 失败")
