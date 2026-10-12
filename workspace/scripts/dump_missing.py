"""输出还没看到的候选图内容。"""
import pathlib, json
ROOT = pathlib.Path(r"d:\Code\Learn\WRF")
MMD = ROOT / "workspace" / "tmp" / "mermaid"
MAP = json.loads((MMD / "map.json").read_text(encoding="utf-8"))

missing = [
    "ch15_cumulus_family_01",
    "ch16_land_surface_family_01", "ch16_land_surface_family_02", "ch16_land_surface_family_03",
    "ch17_urban_canopy_01", "ch17_urban_canopy_02",
    "ch19_lanzhou_heatwave_01",
    "ch21_solve_em_dynamics_01", "ch21_solve_em_dynamics_02",
]
label_to_md = {}
for md, entries in MAP.items():
    for e in entries:
        label_to_md[e["label"]] = md

for lbl in missing:
    mmd = MMD / f"{lbl}.mmd"
    text = mmd.read_text(encoding="utf-8")
    md_file = label_to_md.get(lbl, "?")
    print(f"{'='*70}")
    print(f"[{lbl}]  ← {md_file}")
    print(f"{'-'*70}")
    for i, line in enumerate(text.rstrip().split("\n"), 1):
        print(f"  {i:>2}  {line}")
    print()
