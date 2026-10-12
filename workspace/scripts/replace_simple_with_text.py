"""
批量处理 21 张"简单图"的 md 替换。
策略：
  1. 线性时间链 → Markdown 表格（版本|日期|亮点）
  2. 串行流程链 → 有序列表或 ASCII 箭头
  3. 两列对照 → Markdown 表格
  4. 主干+分支 → 嵌套列表
脚本逐张处理，先备份再替换。
"""
import pathlib, re, json, shutil

ROOT = pathlib.Path(r"d:\Code\Learn\WRF")
DOC = ROOT / "doc"
MMD = ROOT / "workspace" / "tmp" / "mermaid"
PNG_DIR = DOC / "figs" / "mermaid"
MAP = json.loads((MMD / "map.json").read_text(encoding="utf-8"))

# 反向映射：label → md 文件名 + 块序号
label_to_entry = {}
for md_name, entries in MAP.items():
    for e in entries:
        label_to_entry[e["label"]] = (md_name, e)


# ============================================================
# 每张图的文本替代内容（按 label 给出）
# ============================================================

REPLACEMENTS = {

    # ---- ch02: 用户指定的线性时间线 ----
    "ch02_wrf_evolution_01": r"""
**WRF 4.x 版本演进时间线**（完整条目见 §2.1 正式表格）：

| 版本 | 发布日期 | 核心亮点 |
|---|---|---|
| 4.0 | 2018-06 | 混合 σ-p 坐标默认化 |
| 4.1 | 2019-04 | Goddard 4ICE / WSM7 / WDM7 |
| 4.2 | 2020-04 | SMS-3DTKE / FARMS |
| 4.3 | 2021-05 | BEP+BEM 接入 YSU / EEPS |
| 4.4 | 2022-04 | NoahMP 子模块化 / `cldovrlp=5` |
| 4.5 | 2023-04 | Thompson mp38 / k-e-θ² / NTiedtke 尺度自适应 |
| 4.6 | 2024-05 | MMM 共享物理库 / CMake / 风电场三新 |
| 4.7 | 2025-04 | MYNN-EDMF 子模块化 / UDM / RCON |
| **4.8** | **2026-06** | TEMPO / GFL / MYNN-SFC / NoahMP v5.1.2 / 城市树木 |
""".strip(),

    # ---- ch21_02: sequenceDiagram 时间步分解 ----
    "ch21_solve_em_dynamics_02": r"""
**一个时间步内的 Runge-Kutta 与声波小步长编排**（`rk_ord=3`，`dt=54s`）：

| RK 步 | dt_rk | 执行内容 | 声波小步长 |
|---|---|---|---|
| `rk_step=1` | 18 s | 物理 part1+part2 + 动力 | 1 × 18 s |
| `rk_step=2` | 27 s | 动力 | 2 × 13.5 s |
| `rk_step=3` | 54 s | 动力 | 4 × 13.5 s |

> 微物理 `microphysics_driver` 在 RK 循环**全部结束后**、每时间步执行一次。
""".strip(),

    # ---- ch21_01: main → integrate → solve_em → 四子模块 ----
    "ch21_solve_em_dynamics_01": r"""
**从 `main` 到 `solve_em` 的调用链**（详见 ch21 §21.1-21.2 走读）：

```text
main/wrf.F :: wrf_run
 └─ share/mediation_integrate.F :: integrate
     └─ frame/module_integrate.F :: integrate（递归所有嵌套域）
         └─ share/solve_interface.F :: solve_interface（actual_new_args.inc 展开实参）
             └─ dyn_em/solve_em.F :: solve_em  ◀── 本章主角
                 ├─ dyn_em/module_first_rk_step_part1.F  —— 辐射/陆面/PBL/积云
                 ├─ dyn_em/module_small_step_em.F        —— 声波小步长
                 ├─ phys/module_microphysics_driver.F    —— 微物理（RK 循环后）
                 └─ dyn_em/module_after_all_rk_steps.F   —— 诊断输出
```
""".strip(),

    # ---- ch04_01: Registry 一行 → 6 类代码生成物 ----
    "ch04_registry_mechanism_01": r"""
**Registry 中一行条目触发的六类代码生成**（详见 ch04 §4.2）：

| 编号 | 生成物 | 对应路径 |
|---|---|---|
| ① 域类型字段 | `inc/state_struct.inc` | `inc/` |
| ② 内存分配/释放 | `inc/allocs_N.F`、`deallocs_N.F` | `inc/` |
| ③ 运行期状态表 + IO 位掩码 | `tail_statevars`（嵌入 allocs 代码） | `frame/` |
| ④ 嵌套插值/反馈 | `inc/nest_*.inc` + IO 字母 `f/d/u/s` | `inc/` |
| ⑤ 通信代码 | `inc/HALO_*.inc`、`PERIOD_BDY_*.inc` | `inc/` |
| ⑥ rconfig 专属 namelist 读写 | `inc/namelist_*.inc`、`nl_config.inc` | `inc/` |

**原始条目示例**：`state real T2 ij misc 1 - i01rh01{22}{23}du ...`
""".strip(),

    # ---- ch04_03: configure/compile → registry → 生成物 ----
    "ch04_registry_mechanism_03": r"""
**Configure/Compile → Registry → 生成物的构建链**：

```text
./configure  ──→  configure.wrf（REGISTRY = Registry）
                   │
                   ▼
./compile  ──→  Registry/Registry（含过期检查）
                   │
                   ▼
          make → frame/Makefile 规则
                   │
                   ▼
          tools/registry -D... -DNEW_BDYS  Registry/Registry
                   │
                   ▼
          inc/ 与 frame/ 代码生成物
```
""".strip(),

    # ---- ch04_04: namelist → 配置读取 → 物理分发 ----
    "ch04_registry_mechanism_04": r"""
**`mp_physics` 从 namelist 到物理驱动的完整链**：

```text
namelist.input:
  &physics mp_physics = 6
      │
      ▼
inc/namelist_statements.inc:
  NAMELIST /physics/ mp_physics
      │
      ▼
frame/module_configure.F:
  config_reads.inc 的 READ 循环
      │
      ▼
  model_config_rec%mp_physics(1) = 6
      │
      ├──→ nl_get_mp_physics(1, val)          （inc/nl_config.inc 生成）
      │      └──→ in_use_for_config 判定       （wsm6scheme=6 ↔ 变量开关）
      │
      └──→ model_to_grid_config_rec           （config_assigns.inc）
             └──→ config_flags%mp_physics
                   └──→ module_physics_driver  按 config_flags%mp_physics 分发
```
""".strip(),

    # ---- ch07: real.exe 输入输出 ----
    "ch07_real_namelist_01": r"""
**`real.exe` 输入与产物**（详见 ch07 §7.1）：

```text
met_em.d01/d02.*.nc ──┐
（42 个：21 时刻 × 2 域）├──→  real.exe  ──→  wrfinput_d01（14.3 MB）
namelist.input ───────┘          │           wrfinput_d02（20.6 MB）
（域/物理/动力学全配置）          └──→  wrfbdy_d01（58.7 MB）
```
""".strip(),

    # ---- ch08: 重启续跑流程 ----
    "ch08_running_wrf_01": r"""
**RESTART 续跑流程**（详见 ch08 §8.3）：

1. `RESTART_ALARM` 到达触发时刻 → `med_last_solve_io / med_after_solve_io` 检查铃响
2. `grid%id==1`（根域）发起 `med_restart_out`：写本域 rst 并递归所有子域
3. 产出 `wrfrst_d01_… / wrfrst_d02_…`
4. 续跑：`restart=.true.` + 起点时间对齐 → `input_wrf` 读 rst（状态 + 闹钟时刻表）
5. 从断点继续积分
""".strip(),

    # ---- ch09: IO 接口分层 ----
    "ch09_io_system_01": r"""
**`wrf_*` 无关接口 → 多后端实现的路由**：

| 接口层（`frame/module_io.F`） | 路由 | 实现包 |
|---|---|---|
| `mediation` / `output_wrf` / `input_wrf` | `io_form % 100` | — |
| | 1 | `external/io_netcdf`（`ext_ncd_*`）|
| | 2 | `external/io_pnetcdf`（`ext_pnc_*`）|
| | 其他 | `io_int` / `io_phdf5` / `io_grib1/2` / `io_esmf` / `io_pio` / `io_netcdfpar` / `io_adios2` … |
| | 启用 quilt | `module_wrf_quilt`（独立 I/O 服务器）|
""".strip(),

    # ---- ch11_01: 大气成分两列对照 ----
    "ch11_composition_moisture_aerosol_01": r"""
**干洁大气成分：两种分类体系对照**（详见 ch11 §11.1，书 2.2）：

| 浓度法（ppmv） | 代表成分 | 停留时间法 | 代表成分 |
|---|---|---|---|
| 主要成分 >300 | N₂ · O₂ · Ar · CO₂ | 准定常 >1000 a | N₂ · O₂ · Ar · He · Ne · Kr · Xe |
| 微量成分 1–20 | CH₄ | 可变 几年–几十年 | CO₂ · CH₄ · N₂O · CFCs |
| 痕量成分 <1 | O₃ · H₂ · NOx · SO₂ … | 快变 <1 a | O₃ · OH · 碳/硫/氮化合物 |
""".strip(),

    # ---- ch13_02: Thompson 微物理逐阶段 ----
    "ch13_microphysics_family_02": r"""
**Thompson 方案 `module_mp_thompson.F` 逐阶段**（详见 ch13 §13.7）：

1. **变量装入**：3D → 逐列 1D 数组（`temp/pres/qv1d…`），由 θ·π 还原 T、由 ρ 与 qv 还原 ρ
2. **热力学准备**：`qvs=RSLF(p,T)`、`ssatw=qv/qvs−1`；更新扩散率 `diffu`、粘度 `visco`、`Lv(T)`、`ocp`、`lvt2`
3. **过程速率段**（多个 `do k` 循环）：① 冰核化/冻结（Bigg、Cooper/DeMott、Koop）② 沉积/升华增长（冰、雪、霰）③ 云水凝结/蒸发（饱和调整）④ 碰并收集（雨-云、雪-云、霰-云、雨-冰…）⑤ 自动转化（云水→雨、冰→雪）⑥ 融化/冻结/淞附
4. **守恒约束**：五物种逐一限幅 + 成对项强制
5. **倾向装配** + 尺寸/数浓度硬约束（云水 1–50 μm、冰 5–300 μm、雨 MVD 范围…）
6. **更新 T/ρ/qv/qvs** → 饱和调整的守恒核对 → `calc_effectRad`（有效半径）
7. **下沉 sedimentation** + 地面降水通量 → `pcp_ra/pcp_sn/pcp_gr/pcp_ic` → `RAINNC` 等
8. **可选**：`REFL_10CM` 雷达反射率（`module_mp_radar`）
""".strip(),

    # ---- ch14_02: MYNN-EDMF 子例程链 ----
    "ch14_pbl_family_02": r"""
**MYNN-EDMF `mynnedmf` 主例程的子例程调用链**（详见 ch14 §14.6）：

```text
mynnedmf（列循环）
 ├─ mym_initialize      初始化 TKE、长度尺度、稳定度函数
 ├─ mym_condensation    诊断液水 ql 与云量
 ├─ ddmp_mf             下沉质量通量（downdraft）
 ├─ mym_turbulence      混合长 + 稳定度函数 + 扩散系数 + 各生产项
 ├─ mym_predict         推进 qke、θl、qw 等预报量，组装倾向
 └─ get_pblh / SCALE_AWARE / topdown_cloudrad  等诊断
```
""".strip(),

    # ---- ch15_01: 物理驱动链 ----
    "ch15_cumulus_family_01": r"""
**非时间分裂物理驱动的调用顺序**（`rk_step==1` 时执行一次；详见 ch13–ch16 + ch21）：

`radiation_driver → surface_driver → pbl_driver → cumulus_driver → shallowcu_driver`

微物理 `microphysics_driver` 在 RK 循环全部结束后执行（独立链）。
""".strip(),

    # ---- ch16_01: 同上 + 章节号 ----
    "ch16_land_surface_family_01": r"""
**物理驱动链与章节对照**：

`radiation_driver（第 12 章） → surface_driver（本章） → pbl_driver（第 14 章） → cumulus_driver（第 15 章）`

`microphysics_driver` 在 `solve_em` RK 循环后单独执行。
""".strip(),

    # ---- ch16_03: Penman 流程 ----
    "ch16_land_surface_family_03": r"""
**Noah Land Surface 土壤蒸发（Penman-Monteith 路线）**：

```text
REDPRM 参数
  → PENMAN（ETP + RR + EPSCA）
    → EVAPO（EDIR/EC/ET）
      → SMFLX（SMC/SH2O 三对角 + 径流）
        → BETA = ETA/ETP（水侧诊断）
          → TDFCND（lambda(SMC,SH2O,QZ)）
            → YY / ZZ1（把 BETA 与 lambda 装进线性化方程）
              → SHFLX（HRT+HSTEP 隐式土层步）
                  T1 = (YY + (ZZ1-1)·STC1) / ZZ1；SSOIL
```
""".strip(),

    # ---- ch19: WPS 预处理数据流 ----
    "ch19_lanzhou_heatwave_01": r"""
**兰州个例 WPS 预处理数据流**：

```text
ERA5 月 GRIB ──→ link_grib.csh ──→ ungrib.exe（Vtable.ECMWF）
（liuyl17 共享区）                   └── FILE: YYYY-MM-DD_HH（21 个时次）

WPS_GEOG 静态数据 ──→ geogrid.exe（GEOGRID.TBL.ARW） ──→ geo_em.d01/d02.nc
（/opt/app/wrf/WPS_GEOG）

geo_em.d01/d02.nc ──┐
FILE:YYYY-MM-DD_HH ─┴──→ metgrid.exe ──→ met_em.d01/d02.*（42 个文件）
```
""".strip(),
}


# ============================================================
# 执行替换
# ============================================================

def replace_in_md(md_path: pathlib.Path, label: str, new_content: str):
    """把 md 文件中 `![label](figs/mermaid/label.png) + <details>...</details>` 块替换为 new_content"""
    text = md_path.read_text(encoding="utf-8")

    # 模式：![label](figs/mermaid/label.png) 可选换行 <details>...</details>
    # details 可能跨多行
    pat = re.compile(
        rf'!\[{re.escape(label)}\]\(figs/mermaid/{re.escape(label)}\.png\)'
        r'(?:\s*\n)*'
        r'<details>.*?</details>',
        re.DOTALL
    )

    m = pat.search(text)
    if not m:
        print(f"  ✗ 未找到 ![{label}](figs/mermaid/{label}.png) + details 块")
        return False

    # 构建替换内容：新文本 + 原来的空行保护
    replacement = new_content + "\n\n"

    new_text = text[:m.start()] + replacement + text[m.end():]
    md_path.write_text(new_text, encoding="utf-8")
    print(f"  ✓ 替换成功")
    return True


def main():
    print("=" * 60)
    print(f"开始替换 {len(REPLACEMENTS)} 张简单图为文本形式")
    print("=" * 60)

    ok = fail = 0
    for label, new_content in REPLACEMENTS.items():
        if label not in label_to_entry:
            print(f"\n[{label}] ✗ map.json 中找不到")
            fail += 1
            continue

        md_name, entry = label_to_entry[label]
        md_path = DOC / md_name
        print(f"\n[{label}]  ← {md_name}")

        # 备份
        bak = md_path.with_suffix(md_path.suffix + ".bak_before_textreplace")
        if not bak.exists():
            shutil.copy2(md_path, bak)

        if replace_in_md(md_path, label, new_content):
            ok += 1
        else:
            fail += 1

    print("\n" + "=" * 60)
    print(f"完成：{ok} 成功，{fail} 失败")
    print(f"备份在 {DOC}/*.md.bak_before_textreplace")


if __name__ == "__main__":
    main()
