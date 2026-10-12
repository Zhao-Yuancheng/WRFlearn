"""
批量把 workspace/tmp/mermaid/*.mmd 转换为 .drawio + .png。
使用 draw.io CLI (C:\Program Files\draw.io\draw.io.exe)。
"""
import subprocess, pathlib, time, json, sys

ROOT = pathlib.Path(r"d:\Code\Learn\WRF")
MMD_DIR = ROOT / "workspace" / "tmp" / "mermaid"
DRAWIO_DIR = ROOT / "workspace" / "tmp" / "mermaid" / "drawio"
PNG_DIR = ROOT / "doc" / "figs" / "mermaid"
DRAWIO_EXE = r"C:\Program Files\draw.io\draw.io.exe"

DRAWIO_DIR.mkdir(parents=True, exist_ok=True)
PNG_DIR.mkdir(parents=True, exist_ok=True)

mmd_files = sorted(MMD_DIR.glob("*.mmd"))
print(f"待转换：{len(mmd_files)} 个 .mmd 文件\n")

results = []
for i, mmd in enumerate(mmd_files):
    stem = mmd.stem  # e.g. ch21_solve_em_dynamics_01
    drawio_out = DRAWIO_DIR / f"{stem}.drawio"
    png_out = PNG_DIR / f"{stem}.png"

    print(f"[{i+1}/{len(mmd_files)}] {stem} ... ", end="", flush=True)

    # Step 1: .mmd -> .drawio (native XML)
    cmd_xml = [DRAWIO_EXE, "-x", "--timeout", "60", "-f", "xml",
               "-o", str(drawio_out), str(mmd)]
    try:
        r1 = subprocess.run(cmd_xml, capture_output=True, text=True, timeout=120)
        # draw.io 是 GUI app，exit code 可能不准，靠文件存在判断
        time.sleep(1.0)
        if not drawio_out.exists() or drawio_out.stat().st_size < 200:
            print(f"XML_FAIL (exit={r1.returncode})")
            results.append({"label": stem, "xml": False, "png": False, "error": r1.stderr[:200]})
            continue
    except subprocess.TimeoutExpired:
        print("XML_TIMEOUT")
        results.append({"label": stem, "xml": False, "png": False, "error": "timeout"})
        continue

    # Step 2: .drawio -> .png (scale 2, embed diagram for roundtrip)
    cmd_png = [DRAWIO_EXE, "-x", "--timeout", "60", "-f", "png",
               "--scale", "2", "--border", "5",
               "-o", str(png_out), str(drawio_out)]
    try:
        r2 = subprocess.run(cmd_png, capture_output=True, text=True, timeout=120)
        time.sleep(0.5)
        png_ok = png_out.exists() and png_out.stat().st_size > 500
        if png_ok:
            print(f"OK ({drawio_out.stat().st_size}B xml, {png_out.stat().st_size}B png)")
        else:
            print(f"PNG_FAIL (exit={r2.returncode})")
    except subprocess.TimeoutExpired:
        print("PNG_TIMEOUT")
        png_ok = False

    results.append({
        "label": stem,
        "xml": drawio_out.exists() and drawio_out.stat().st_size > 200,
        "png": png_ok,
        "xml_size": drawio_out.stat().st_size if drawio_out.exists() else 0,
        "png_size": png_out.stat().st_size if png_out.exists() else 0,
    })

# 汇总
ok = sum(1 for r in results if r["xml"] and r["png"])
fail = sum(1 for r in results if not (r.get("xml") and r.get("png")))
print(f"\n=== 汇总：成功 {ok}/{len(results)}，失败 {fail} ===")
for r in results:
    if not (r.get("xml") and r.get("png")):
        print(f"  FAIL: {r['label']} — {r.get('error', 'unknown')}")

# 保存结果
(MMD_DIR / "convert_results.json").write_text(json.dumps(results, ensure_ascii=False, indent=2))
print(f"\n结果表：{MMD_DIR / 'convert_results.json'}")
print(f"drawio 源：{DRAWIO_DIR}")
print(f"PNG 输出：{PNG_DIR}")
