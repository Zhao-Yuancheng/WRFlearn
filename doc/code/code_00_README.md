# code_00 — 《WRF 源码精读》文库总纲（README）

> 版本锁定：WRF 4.8.0（`source/WRFv4.8.0/WRFV4.8.0/`）；所有代码块由 `workspace/scripts/code_extract.py` 从源码逐位抽取并附 md5 指纹（acceptance.py 全量校验）。2026-10-12 建成，**29/29 篇全部交付，文库齐账**。

## 一、文库是什么

与教材（`doc\chNN_*.md`）**硬切**：教材回答「为什么这样写、物理对应、方案脉络」（节选+导读），文库回答「这段代码在做什么、每个变量是谁、完整上下文」（保真源码+行段中文讲解，独立可读）。两向导航：教材各章「延伸阅读」指向文库篇，文库每篇开头给「谁在调它」与教材锚点。

## 二、双轨读法

- **依赖拓扑序**（默认编号）：被依赖者在前——读任何一篇时它用到的下层概念已读过。L0 底座（01）→ L1 方案本体（05–17）→ L2 驱动器（20–24）→ L3 动力枢纽（30–32）→ L4 初始化（40–41）→ L5 内核导航（50）→ C 段外围（60–62）。
- **教材章序**：ch10 坐标→code_41/30；ch12 辐射→code_20/05/06/60；ch13 微物理→code_21/07a/07b/08；ch14 PBL→code_22/09a/09b/10；ch15 积云→code_23/11/62；ch16 陆面→code_24/13/12a/12b/61；ch17 城市→code_14a/14b/15/16；ch21 内核→code_50/31/32/30；ch20 改造→各篇「改造入口」节。

## 三、篇目总表

| 编号 | 文件 | 级 | 交付 | 教材锚点 |
|---|---|---|---|---|
| 01 | code_01_module_model_constants.md | A轻 | ✅ | app_a/ch11 |
| 05 | code_05_module_ra_rrtmg_lw.md | B | ✅ | ch12 |
| 06 | code_06_module_ra_rrtmg_sw.md | B | ✅ | ch12 |
| 07 | code_07a/07b_module_mp_thompson.md | A | ✅ 拆两 | ch13 |
| 08 | code_08_module_dust_emis.md | C | ✅ | ch13/ch20 |
| 09 | code_09a/09b_module_bl_mynnedmf.md | A | ✅ 拆两 | ch14 |
| 10 | code_10_module_sf_mynnsfc.md | B | ✅ | ch14 |
| 11 | code_11_module_cu_ntiedtke.md | A | ✅ | ch15 |
| 12 | code_12a/12b_module_sf_noahlsm.md | A | ✅ 拆两 | ch16 |
| 13 | code_13_module_sf_noahdrv.md | B | ✅ | ch16 |
| 14 | code_14a/14b_module_sf_bep_bem.md | A | ✅ 拆两 | ch17 |
| 15 | code_15_module_sf_bep.md | A | ✅ | ch17 |
| 16 | code_16_module_sf_bem.md | A | ✅ | ch17 |
| 17 | code_17_module_sf_urban.md | B | ✅ | ch17 |
| 20 | code_20_module_radiation_driver.md | B | ✅ | ch12 |
| 21 | code_21_module_microphysics_driver.md | B | ✅ | ch13 |
| 22 | code_22_module_pbl_driver.md | B | ✅ | ch14 |
| 23 | code_23_module_cumulus_driver.md | B | ✅ | ch15 |
| 24 | code_24_module_surface_driver.md | B | ✅ | ch16/17 |
| 30 | code_30_module_big_step_utilities_em.md | B | ✅ | ch21/ch10 |
| 31 | code_31_module_first_rk_step_part1.md | B | ✅ | ch21 |
| 32 | code_32_module_first_rk_step_part2.md | B | ✅ | ch21 |
| 40 | code_40_module_initialize_real.md | B | ✅ | ch07/ch10 |
| 41 | code_41_nest_init_utils.md | B | ✅ | ch10 |
| 50 | code_50_solve_em.md | C | ✅ | ch21 |
| 60 | code_60_module_ra_aerosol.md | C | ✅ | ch11/12 |
| 61 | code_61_noah_seaice_glacial.md | C | ✅ | ch16 |
| 62 | code_62_shallowcu_fire_fdda.md | C | ✅ | ch15/ch21 |

> 不收录（plan §三取舍）：`phys/noahmp/`（248 文件独立库）、module_dm/IO/通用工具、TEMPO 与 physics_mmm 目录（physics_mmm 的 cu_ntiedtke 实体已按对照注记收进 code_11 §八）、module_ra_cam*（CAM 辐射旧系）。

## 四、体例约定

1. **八段模板**：版本指纹→定位→文件头→逐段保真块+讲解→单元总表→改造入口→上下游链接。
2. **保真红线**：代码一律脚本抽取（显示层=块首 `!file:` 标记 + 逐行 `L{05d}` 行号前缀），md5 对原始内容；acceptance.py 自动全量。
3. **讲解规范**：中文全角引号；源码符号不译；书公式只给指针（「书 (6.8.14) → ch14 §14.8」式）；mermaid 边标签禁半角括号与斜杠。
4. **A 级 >5000 行拆 _a/_b**；B 级同源单元用「差异注记+回指」不重录。

## 五、工具链

- `workspace/scripts/code_extract.py`（v1.2，扫描器栈式配对支持 F90 CONTAINS 嵌套）：list/full/sub/lines/verify/assemble；多源占位符语法为双花括号内「CODE 前缀 + 冒号 + WRF 根相对路径 + 冒号 + full 或子程序名或行段」。
- `workspace/scripts/acceptance.py`：全量指纹校验（glob doc/code/code_*.md，按指纹定位源、剥离显示层比对）。
- `workspace/scripts/fp_files.py`：篇首指纹表；`check_quotes.py`：全角引号检查。
- 骨架（可再组装的源稿）在 `workspace/code_library/skel_code_*.md`。

## 六、阅读路径建议

1. **系统学 WRF 内核**：01 → 30 → 50（地图）→ 31 → 32 → 41 → 40，配教材 ch21/ch10。
2. **改一个物理方案**：先读对应驱动器（20/21/22/23/24）的 CASE 分派，再读本体的方案篇，最后照「改造入口」动手，配 ch20。
3. **只跑个例不改码**：40/41（初值从哪来）+ 13/24（陆面/海冰分支）+ 21（降水从哪来）。
4. **城市热岛专题**（论文 2 路线）：14a→14b→16→15→12a/12b（背景场）→31 的 surface 段→ch17/ch19。
