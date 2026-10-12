"""扫描所有 .mmd，按节点数和边数粗估复杂度。"""
import pathlib, re, json
ROOT = pathlib.Path(r"d:\Code\Learn\WRF")
MMD = ROOT / "workspace" / "tmp" / "mermaid"
DRAWIO = MMD / "drawio"

results = []
for f in sorted(MMD.glob("*.mmd")):
    text = f.read_text(encoding="utf-8")
    lines = text.strip().split("\n")
    # 节点：任何被 --> 指向或发出的 [..] / "(..)" / "{..}" / "...
    # 粗略： --> 出现次数
    edges = len(re.findall(r'-->', text))
    # 节点：方括号/圆括号/花括号包裹的 label
    nodes = len(re.findall(r'["\[（\{][^"\]\)\}]{2,}["\]\)\}]', text))
    # 也数子图
    subgraphs = len(re.findall(r'subgraph', text)) + len(re.findall(r'sub_graph', text))
    # 类型
    dtype = lines[0].split()[0] if lines else "?"

    # 读 map.json 里的 md 来源
    label = f.stem  # e.g. ch02_wrf_evolution_01

    # 简单性判据：edges ≤ 10 AND nodes ≤ 12 AND subgraphs == 0
    simple = edges <= 8 and nodes <= 10 and subgraphs == 0

    results.append({
        "label": label,
        "diagram_type": dtype,
        "nodes_est": nodes,
        "edges": edges,
        "subgraphs": subgraphs,
        "simple": simple,
        "first_line": lines[0][:60] if lines else "",
    })

print(f"{'label':<45} {'type':<16} {'nodes':>5} {'edges':>6} {'sg':>3} {'simple':>7}")
print("-" * 90)
for r in results:
    mark = " ★★★" if r["simple"] else ""
    print(f"{r['label']:<45} {r['diagram_type']:<16} {r['nodes_est']:>5} {r['edges']:>6} {r['subgraphs']:>3} {'YES'+mark if r['simple'] else 'no':>7}")

print(f"\n简单图（★★★，可用文本替代）共 {sum(1 for r in results if r['simple'])} / {len(results)}")
# 显示最简单的候选（线性链，edges≈nodes-1）
print("\n候选★★★（edges ≤ 8 且 nodes ≤ 10）：")
for r in results:
    if r["simple"]:
        print(f"  {r['label']}: {r['diagram_type']}, nodes≈{r['nodes_est']}, edges={r['edges']}")
