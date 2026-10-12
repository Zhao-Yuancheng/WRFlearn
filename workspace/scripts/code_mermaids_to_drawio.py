"""doc/code/code_*.md 内的 mermaid → drawio（套 FDS-UNeXT 样式），供用户手动修改。
本轮只产 drawio，不导 PNG（下一轮用 reexport_pngs.py）。

流程：
  1. 扫 doc/code/code_*.md 提取 ```mermaid 块 → workspace/tmp/mermaid/mmd_code/*.mmd
  2. 校验边标签 |...| 内无半角括号与斜杠（文库硬约束）
  3. draw.io CLI -f xml 转 drawio → workspace/tmp/mermaid/drawio/code_*_NN.drawio
  4. restyle_drawio() 套样式（只处理新文件，不碰教材 35 张）
"""
import pathlib, re, subprocess, sys, time

ROOT = pathlib.Path(r"d:\Code\Learn\WRF")
sys.path.insert(0, str(ROOT / "workspace" / "scripts"))
from restyle_drawio import restyle_drawio  # 仅用纯函数，不跑其 __main__

DOC_CODE = ROOT / "doc" / "code"
MMD_DIR = ROOT / "workspace" / "tmp" / "mermaid" / "mmd_code"
DRAWIO_DIR = ROOT / "workspace" / "tmp" / "mermaid" / "drawio"
DRAWIO_EXE = r"C:\Program Files\draw.io\draw.io.exe"

MMD_DIR.mkdir(parents=True, exist_ok=True)
BLOCK_RE = re.compile(r"^```mermaid\s*\n(.*?)^```\s*$", re.M | re.S)
BAD_EDGE_LABEL = re.compile(r"\|[^|]*[()/][^|]*\|")


def extract_all():
    """返回 [(md_path, seq, mermaid_text)]，并校验边标签。"""
    out, problems = [], []
    for md in sorted(DOC_CODE.glob("code_*.md")):
        text = md.read_text(encoding="utf-8")
        for i, m in enumerate(BLOCK_RE.finditer(text), 1):
            body = m.group(1)
            bad = BAD_EDGE_LABEL.findall(body)
            if bad:
                problems.append((md.name, i, bad[:3]))
            out.append((md, i, body))
    return out, problems


def main():
    blocks, problems = extract_all()
    print(f"提取到 {len(blocks)} 个 mermaid 块（来自 {len(set(b[0] for b in blocks))} 个文件）")
    if problems:
        print("\n[WARN] 边标签含半角括号/斜杠（转换或渲染可能出错，需回改骨架）：")
        for name, i, bad in problems:
            print(f"  {name} #{i}: {bad}")
        print("—继续转换，但请留意以上文件\n")

    ok = fail = 0
    for md, seq, body in blocks:
        stem = f"{md.stem}_{seq:02d}"
        mmd = MMD_DIR / f"{stem}.mmd"
        mmd.write_text(body, encoding="utf-8")
        drawio_out = DRAWIO_DIR / f"{stem}.drawio"
        if drawio_out.exists():
            drawio_out.unlink()  # CLI 不覆盖旧文件时靠这个保证重转
        print(f"[{stem}] 转换中 ...", flush=True)
        r = subprocess.run(
            [DRAWIO_EXE, "-x", "--timeout", "60", "-f", "xml",
             "-o", str(drawio_out), str(mmd)],
            capture_output=True, text=True, timeout=120)
        time.sleep(1.0)
        if not drawio_out.exists() or drawio_out.stat().st_size < 200:
            print(f"  XML_FAIL exit={r.returncode} stderr={r.stderr[:150]}")
            fail += 1
            continue
        # 套样式（新文件独享，一次成型，无叠加风险）
        xml = drawio_out.read_text(encoding="utf-8")
        drawio_out.write_text(restyle_drawio(xml), encoding="utf-8")
        ok += 1
        print(f"  OK ({drawio_out.stat().st_size // 1024}KB, styled)")

    print(f"\n完成：{ok} 成功，{fail} 失败")
    print(f"drawio 输出：{DRAWIO_DIR}")
    print(f"mermaid 中间产物：{MMD_DIR}")


if __name__ == "__main__":
    main()
