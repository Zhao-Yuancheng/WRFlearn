"""打印所有简单图的 mermaid 源码 + 文件来源。"""
import json, pathlib
ROOT = pathlib.Path(r"d:\Code\Learn\WRF")
MMD = ROOT / "workspace" / "tmp" / "mermaid"
MAP = json.loads((MMD / "map.json").read_text(encoding="utf-8"))

simple_labels = [
    "ch01_from_atmosphere_to_models_01", "ch01_from_atmosphere_to_models_02",
    "ch02_wrf_evolution_01",
    "ch04_registry_mechanism_01", "ch04_registry_mechanism_03", "ch04_registry_mechanism_04",
    "ch07_real_namelist_01", "ch08_running_wrf_01", "ch09_io_system_01",
    "ch11_composition_moisture_aerosol_01",
    "ch13_microphysics_family_02", "ch14_pbl_family_02", "ch15_cumulus_family_01",
    "ch16_land_surface_family_01", "ch16_land_surface_family_02", "ch16_land_surface_family_03",
    "ch17_urban_canopy_01", "ch17_urban_canopy_02",
    "ch19_lanzhou_heatwave_01",
    "ch21_solve_em_dynamics_01", "ch21_solve_em_dynamics_02",
]

# 反向建 label -> md_file 映射
label_to_md = {}
for md, entries in MAP.items():
    for e in entries:
        label_to_md[e["label"]] = md

for lbl in simple_labels:
    mmd = MMD / f"{lbl}.mmd"
    text = mmd.read_text(encoding="utf-8")
    md_file = label_to_md.get(lbl, "?")
    print(f"{'='*70}")
    print(f"[{lbl}]  ← {md_file}")
    print(f"{'-'*70}")
    for i, line in enumerate(text.rstrip().split("\n"), 1):
        print(f"  {i:>2}  {line}")
    print()
