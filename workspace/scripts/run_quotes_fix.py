"""对 doc/*.md 跑 _fix_quotes.py"""
import subprocess, pathlib, sys
ROOT = pathlib.Path(r"d:\Code\Learn\WRF")
FIX = ROOT / "workspace" / "scripts" / "_fix_quotes.py"
DOC = ROOT / "doc"

md_files = sorted(DOC.glob("ch*.md")) + sorted(DOC.glob("app*.md")) + [DOC / "index.md"]
md_files = [f for f in md_files if f.exists()]

print(f"对 {len(md_files)} 个 md 文件跑 _fix_quotes.py\n")
for f in md_files:
    r = subprocess.run(
        [sys.executable, str(FIX), str(f)],
        capture_output=True, text=True, timeout=30
    )
    line = r.stdout.strip().split("\n")[-1] if r.stdout.strip() else "(no output)"
    print(f"  {f.name}: {line[:100]}")
