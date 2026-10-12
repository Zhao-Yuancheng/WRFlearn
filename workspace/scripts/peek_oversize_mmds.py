"""看 9 张超宽图的 mermaid 源码，理解布局后决定怎么改"""
import pathlib

MMD_DIR = pathlib.Path(r"d:\Code\Learn\WRF\workspace\tmp\mermaid")
OVERSIZE = [
    "ch02_wrf_evolution_01",      # 6196×204, WRF 版本演进
    "ch03_architecture_overview_02", # 3946×1642
    "ch04_registry_mechanism_02",  # 3578×982
    "ch06_wps_pipeline_01",        # 4628×590
    "ch08_running_wrf_01",         # 5284×166
    "ch15_cumulus_family_02",      # 3544×904
    "ch17_urban_canopy_01",        # 3902×696
    "ch17_urban_canopy_02",        # 4388×450
    "ch21_solve_em_dynamics_05",   # 11266×814  最夸张
]

for stem in OVERSIZE:
    mmd = MMD_DIR / f"{stem}.mmd"
    if not mmd.exists():
        print(f"⚠ {stem}: .mmd 不存在")
        continue
    text = mmd.read_text(encoding="utf-8")
    lines = text.strip().split("\n")
    print(f"\n{'='*60}")
    print(f"{stem}  ({len(lines)} 行)")
    print(f"{'='*60}")
    for l in lines:
        print(f"  {l}")
