# Progress — 当前状态（可重写）

时间锚点: 2026-10-11 下午（自主会话继续推进）
阶段: **ch20（改造 WRF 三级实战）已交付且全链实跑验证；ch01/ch02 已交付；ch03–ch19 三类专栏补充完成。下一章 ch21（solve_em.F 全流程，第 V 部），随后附录 a–d 与 index.md**

## 已完成

### 批次 1（ch03→ch09，II 部审阅点）✅
- ch03 架构 / ch04 Registry / ch05 编译 / ch06 WPS / ch07 real+namelist / ch08 运行 WRF / ch09 IO —— 全部落盘 `doc\`
- 兰州个例链路全绿（WPS→real→wrf 5 天 SUCCESS）；实验与事故全部留档（见 verify_log 三段）

### 批次 2（物理族）进行中
- [x] **ch10 垂直坐标与静力平衡** → [ch10_vertical_coords_hydrostatics.md](computer://d:\Code\Learn\WRF\doc\ch10_vertical_coords_hydrostatics.md)
- [x] **ch11 大气成分、水汽与气溶胶** → [ch11_composition_moisture_aerosol.md](computer://d:\Code\Learn\WRF\doc\ch11_composition_moisture_aerosol.md)
- [x] **ch12 辐射过程族** → [ch12_radiation_family.md](computer://d:\Code\Learn\WRF\doc\ch12_radiation_family.md)
  - 书第 5 章 54 页直读；公式 (5.1.1)–(5.6.28) 与表 5.1–5.17 全核；PPT 5-1~5-6 六讲考点全覆盖
  - 源码：radiation_driver 节拍 + radconst/calc_coszen（与书 (5.4.3a) 逐符号一致）+ RRTMG 16/14 波段 + ghg_input/o3input 双分支 + effectRad
  - 轻轨实验六组：**太阳几何逐格闭环**（COSZEN max|Δ|=8.9e−8、HRANG=0）、四定律核验、Kasten 逐位复现、Qd 比值 1.366、两层温室基准逐位
  - 重要发现：JULIAN 零基日序（192）；coszen 用区间中点；`ghg_input`/`o3input` 默认 1/2
  - 勘误：书表 5.16 敏感性六行与 (5.6.4) 复算不符（教材已列对照表）
- [x] **ch13 微物理方案族** → [ch13_microphysics_family.md](computer://d:\Code\Learn\WRF\doc\ch13_microphysics_family.md)
  - 书第六章 6.1–6.7 全节直读（印刷页 123–153 + 思考题/习题 p168–169）；公式 (6.1.1)–(6.7.6) 全按书号；思考题 7 题、习题 8 题**全解含数值答案**
  - 源码：solve_em 调用链 + 39 CASE 分发 + **Thompson 精读**（饱和调整 3 次牛顿 / 守恒五保险 / 冰核化三来源 / calc_effectRad 闭环）+ **WSM6 对照**（physics_mmm 双层、conden 单步、PLM 沉降）+ mp_physics 0–106 双表
  - 核心对照点：**饱和调整 = 书 (6.6.3) 隐式方程的两种解法**（差 ≤毫开尔文）；Lv(T) 三口径并存（−2323/−2343.6/−2112）
  - 轻轨实验：埃玛图（LCL 506 m vs 492 m；LFC 343.8 hPa；对流温度 30.8℃）+ γs/θse + 饱和调整三法 + 习题 6 焚风 θse 守恒 312.3 K
  - 核验：(6.3.5) 分母含 ε（非勘误，(6.1.46) 符号、图 6.15 关系句）三件通过
  - 图 3 张自算 + 2 mermaid
- [x] **ch14 边界层方案族** → [ch14_pbl_family.md](computer://d:\Code\Learn\WRF\doc\ch14_pbl_family.md)
  - 书 6.8 静力稳定度全节直读（印刷页 154–163）；(6.8.1)–(6.8.21) 全按书号；CAPE/CIN、薄层法与"积云密度自调节"、烟云五型
  - 源码：调用链与分发（~20 CASE + `SELECT CASE(sf_urban_physics)` 置 flag_bep）；**MYNN-EDMF 精读**（phys/MYNN-EDMF/ 编译实体、版本史 V1.0→V6.0、qke=2TKE、get_pblh 全文、dmp/ddmp_mf、boulac_length 亲缘）；**BouLac 精读**（双长度 dlu/dld、igamma 三选、"TKE IS NOT ADVECTED!!"、BEP 全链）；**YSU 对照**（brcr 家族、topdown 云顶混合、topo_wind）
  - 关键对照：PBLH 三型判据（Ri / θv 阈值 / TKE 阈值）；BouLac↔MYNN 混合长亲缘；**BEP/BEM 官方清单 = YSU/MYJ/BouLac**（论文 2 依据；MYNN 不在列）
  - 轻轨实验 E1–E4（虚温订正 CAPE：LFC 8 km→1.8 km、CIN −1330→−128）；习题 12 题全解（含 6 道模式题）；2 mermaid + 3 图
- [x] **ch15 积云参数化族** → [ch15_cumulus_family.md](computer://d:\Code\Learn\WRF\doc\ch15_cumulus_family.md)
  - 书 6.9 整层升降（(6.9.1)–(6.9.5)、例题 6.2）+ 6.10 逆温层五类 + 6.8.2 夹卷结尾全节直读（印刷页 164–168 + 思考题/习题 + **答案页 p546 全抄**）
  - 源码：cumulus_driver 全 CASE + 调用节律 + 倾向加餐；**New Tiedtke 精读**（双层结构、cumastrn 十步、cutypen 两类测试气块、三类闭合、卷入卷出、Sundqvist 降水、scale_fac）；**KFeta 对照**（W0AVG、触发三选项、90% CAPE 迭代、TIMEC）；shcu_physics 独立浅对流
  - 重案：**印刷勘误**（p167 结论②括注 ∂θe/∂z＞0 与"负值区"矛盾，放大复核后按＜0 处理）
  - 轻轨实验 E1–E4：例题 6.2 复算（467.7/390 vs 469.3/391.1，60 层等熵模型）；习题 7 全解（对流温度 30.8 vs 书 30.5；CAPE 790/CIN −124 真潜；θse 62.1→56.2 对流性不稳定）；习题 8（23.9/26.5 vs 书 24.2/26.7）；夹卷-云顶表 + scale_fac 表（3 km=19.05）
  - 图 4 张自算 + 2 mermaid
- [x] **ch16 陆面过程族** → [ch16_land_surface_family.md](computer://d:\Code\Learn\WRF\doc\ch16_land_surface_family.md)（新）
  - 书 4.2（印刷页 55–56：(4.2.1)–(4.2.3)、表 4.1、"薄壳"）+ 4.3（56–58：三重身份、热惯性 3120×、三层结构、50%/15–20 m/200–300 m、海流与图 4.8）+ **模式实现补讲**（Rn=H+LE+G；土壤热传导与阻尼深度 D=√(2κ/ω)；β 蒸发效率）+ 第四章习题 3/4/5 回看
  - 源码：surface_driver 两族 SELECT CASE；**Noah 精读**（SFLX 九步 + NOPAC 顺序 EVAPO→SMFLX→BETA→TDFCND→YY/ZZ1→SHFLX；PENMAN 逐式（**T24=SFCTMP⁴** 关键口径）；TDFCND 公式链与 Kersten；HCPCT 四组分；HRT/HSTEP 三对角 + TBOT@ZBOT=6.5 m；LSMINIT/REDPRM；ISURBAN 六件套 + DF1=3.24）；**三张 TBL 实读**（含 SOILPARM 四式全表互核）；geogrid→real→wrfinput 静态场链路；namelist 全条目
  - 轻轨实验 E1–E4：**能量平衡闭合 2e-11 W/m²**、柱收支 telescoping 4e-9%；湿/干对比（份额 0.911/0.650、皮温 28.1/35.5℃、逆温 5.80/4.84 K）；**Noah 线性化体检 0.039/0.259 K**；阻尼深度（土壤 0.124/2.37 m 对书 0.1/2–3 m；海洋反演 κ_eff≈1e-2 对书 15–20/200–300 m；纯水分子 6 cm 反证风浪混合）；SOILPARM 类间表（KDT 差 48 倍）；书习题 3(2) **1351.4 gpm 逐位**
  - 新勘误/口径 5 条（书双口径、表 4.1、习题 3 口径、SOILPARM 三处表-式不符、四式全为注释）——见 verify_log ch16 段
  - 图 3 张自算 + 3 mermaid
- [x] **ch17 城市冠层专章** → [ch17_urban_canopy.md](computer://d:\Code\Learn\WRF\doc\ch17_urban_canopy.md)（新）
  - 定位：书前 6 章无城市考点 → 六段式 + **"论文2 对接"节替代考点透视**（v4 方案 R5 口径）
  - 源码：**SLUCM 精读**（`module_sf_urban.F`：Kusaka 血统至 2024/25 urban-NbS；bisection/multi_layer/force_restore/CH_SCHEME=2；内嵌 Noah 土壤链；树/绿屋顶 NbS 群）；**BEP**（`module_sf_bep_bem.F`：BEP1D、街谷几何、视角因子矩阵、a/b 隐式系数回路）；**BEM**（`module_sf_bem.F`：墙体多层、室内、air_cond→consump/cop、光伏）；`module_bep_bem_helper.F` **勘正（仅 3 行 nurbm）**；兼容矩阵源码实证（boulac 的 flag_bep/a_u_bep）
  - 数据链路：landuse 四体系（USGS/MODIS/NLCD40/LCZ）；GEOGRID.TBL 城市条目全家（URB_PARAM=132、MH/ZD/Z0/λp/λf/AHE 的 y2010/y2050 数据集）；namelist 全表（num_urban_* 2/10/10/18/10/10/15 等）
  - **BEM 改造地图（论文2）已落 chapter_map**（α/ε/λ/ρc/d 与空调日程/占用率 → 2D 场；auxinput 通道）
  - 轻轨实验 E1–E3：城市 vs 乡村（白天 T_s 差 +15.5 K、夜空 +1.8 K、LE≡0）；AH 20/50/90 → 日均 +0.68/+1.69/+3.03 K；绿量 FVG=0.2 → 白天 −6.67 K；URBPARM 实读（AHDIUPRF 峰 1.00@17h）
  - 图 2 张自算 + 2 mermaid
- [x] **ch18 理想实验入门**（第 IV 部开篇，技术章六段式）→ [ch18_ideal_cases.md](computer://d:\Code\Learn\WRF\doc\ch18_ideal_cases.md)（新，713 行）
  - 定位：把 ch05 的 test/em 全表展开为"场景/初值机制/物理开关/检验点"四维表；**三条机制线索**（双钥匙 / 初始化源码 / 集群实跑）
  - **双钥匙机制（本章核心）**：编译期 `IDEAL_CASE`（顶层 Makefile；9 个算例共用 `=ideal`）+ 运行期 `ideal_case`（Registry 包 → `frame/module_state_description.F` 常量 `realcase=0…les=9`）→ **`wrf.exe` 不链接任何 initialize 模块 → 同家族共享同一二进制**；官方"每算例要 compile"的实质 = 装配运行目录（§18.5.6 以 md5 + rc=127 失败日志 + 补链接实跑三重实证）
  - 源码：`dyn_em/module_initialize_ideal.F`（2252 行）精读（12 处 SELECT CASE 分发；levels 三策略；`nl_set_map_proj(1,0)` 与 msf≡1；f 值表；暖泡/冷泡/随机三扰动；`get_sounding` 干湿两遍；`read_input_jet` 二进制格式）；`main/ideal_em.F` 写出链；`share/set_timekeeping.F` 的 run_* 优先于 end_*
  - **口径勘正四则**：grav2d_x=密度流（非重力波）、`em_bubbling` 不存在、b_wave=x 周期+y 对称、em_esmf_exp 是耦合包非算例（ch05 表已同步修订两处 + §5.6 速查表新增两条）
  - **集群实操（三算例全部 SUCCESS，原文入文）**：沙箱拷贝 8432 文件/1.3G/17 min；`compile em_les` 69 s（实测 `-j` 上限 20）；em_les np=4 **113 s** / np=2 129 s / np=1 192 s、em_quarter_ss **51 s**、em_b_wave **86 s**；**md5 交叉证据**：ch18 的 wrf.exe md5 与 ch05 的 em_real 基线（e81b5016…）逐位相同
  - 轻轨诊断（`workspace/scripts/ch18_diagnose.py`，3 图）：les（HFX 0→278.6 W/m²、CBL 顶 1004→1059 m、近地 θ 300→301.5 K）；qss（W max 0/30.18/43.29 m/s、θ′ 近地 min 0.40/−2.35/−7.18 K、RAINNC 0/7.94/36.61 mm）；b_wave（地面 P′ ±0.1→−69.7/+22.8 hPa 指数增长、|u|max 67.3→72.0）
  - **重要教学点**：物理全关算例的 `PSFC`/`T2` 恒为 0（诊断须改用动力学/微物理量）；`frames_per_outfile=1000` 使多帧写同一文件
  - 图 3 张自算 + 2 mermaid
- [x] **ch19 真实个例全流程实录：兰州 2025-07 高温** → [ch19_lanzhou_heatwave.md](computer://d:\Code\Learn\WRF\doc\ch19_lanzhou_heatwave.md)（新，408 行，全书压轴实验章）
  - 19.1 设计定稿（窗口扫描依据、两域 9/3 km、两套物理套装）；19.2 WPS 回顾（21 时次、43/40/122 s）
  - 19.3 基线 + **质控六条** + 两条教训（节点栈 8 MB → SIGSEGV；运行中 `sed -i` 脚本 → Stale file handle 砍掉 exp3 第 4.5 天）
  - 19.4 诊断三条线：T-lnP（**"T 是扰动位温"换算纠正** → LCL=LFC=699 hPa、CAPE 2522、CIN 0）、T2 vs ERA5（偏暖 0.3–2.0 K）、热岛（3.2–3.7 K）
  - **19.5 城市冠层对照（压轴）**：数据缺口实测 → **三重约束链**（PBL 兼容 / 面层兼容 / `ZDC+Z0C+2<ZA`）→ 探针实测（类2 8.051 m vs ZA 8.046 m）→ `UTYPE_URB2D` 无输入流标志 → **单行补丁（类2→1）** → 三跑全部 SUCCESS（439828/439810/439866）→ 两对单变量对照
  - 差异：热岛 3.2–3.7 K；方案净效应 域均 |Δ|<0.3 K、局地 ±2–3.5 K、日最高几乎不变；AH 关闭 → 诚实结论指向论文2 参数场
  - 19.6 对接论文2（7 维差距表）；19.7 速查 7 条 + 延伸
  - 图 4 张：ch19_tlnp / ch19_t2_vs_era5 / ch19_uhi_diurnal / ch19_uhi_maps

## 用户复核清单（更新）
1. WPS 域重建（90×90 + 112×112）确认；
2. 案例 namelist 的 `restart_interval=86400` 留档 or 改 1440；
3. ch17 考点节口径（"论文2 对接"替代）；
4. np64 段错误按间歇归档；
5. ch10/ch11/ch12 的"书页扫描直读"写作方式与八段式结构是否合意（后续物理章照此办理）。
6. ch11 中 PPT 原图直接嵌入（不标页码）的 6 张是否合意；两处"书页字迹反证"（冰面 Tetens 273.16）的勘误口径是否接受。
7. **（ch12）**：① 表 5.16 敏感性六行的勘误口径；② 默认 `ghg_input=1`/`o3input=2` 的"隐性输入"提示是否在个例方法学展开；③ 集群辐射敏感性实验（radt/ghg/o3）是否执行。
8. **（ch13）**：① 考点节自拟版（第 6 章 PPT 未到）"待 PPT 校准"的口径是否接受；② (6.2.4) 幂次/（6.3.5）ε、思考题 4 的幂次说明是否保留在正文；③ Lv(T) 三口径对照（13.9.2）呈现在正文是否合适；④ ch13 预留的集群"方案切换对照"（mp=6 vs 8，24 h）是否执行。
9. **（ch14）**：① 考点节自拟版（第 6 章 PPT 未到）"待 PPT 校准"口径；② BEP/BEM 兼容清单按 README 原文校准为"YSU/MYJ/BouLac"三方案（MYNN 不在列）；③ 预留集群"MYNN(5) vs BouLac(8) vs YSU(1) 对照"（24 h）是否执行；④ 14.9 的 12 道自拟题（含 6 道模式视角题）口径是否合意。
10. **（ch15）**：① 书 p167 结论②括注"（∂θe/∂z＞0）"按印刷勘误处理（教材 15.2.4 注明，与"负值区"及 (6.9.5) 自洽读作 ＜0）——口径是否接受；② 例题 6.2 复算 ~1 hPa 差（源自 Γ1=0.0032 取整）作"口径记录"处理是否合适；③ θse 绝对值 vs 书答案 68/60℃ 的 2–6 K 口径差（判据符号一致）如何表述；④ 预留集群"cu=1 vs 16 对照（d01，24 h）"是否执行；⑤ 15.9.2 的 12 道自拟题（含 6 道模式视角题）口径是否合意。
11. **（ch16）**：① 书"海洋/大气质量比"两口径（4.2 的 1/273 vs 4.3.1 的 267）按"两种大气总质量估计"处理（教材 16.1.2）——口径是否接受；② 表 4.1 的 77.6% 与 p0=985/1013.25 混用按"表内 p0 口径题"处理（16.9.2 第 2 题）是否合适；③ **SOILPARM 表内三处表-式不符 + 三类人工特设**按"信表不疑式、式是设计图纸"处理（16.6.1/16.8.3）是否接受；④ E1 的两项"线性化体检"（同口径 0.039/0.259 K；公式口径差 0.77/3.09 K）与"冻结 θ 不做水分预报"的简化口径是否合意；⑤ 16.9.2 的 12 道自拟题（含 6 道模式视角题）口径是否合意；⑥ 预留集群"sf_surface=1 vs 2（slab vs Noah，d01，24 h）对照"是否执行。
12. **（ch17）**：① `module_bep_bem_helper.F` 内容勘正（仅 3 行 nurbm；方案 v2 原文预期落空）与"六段式 + 论文2 对接节替代考点透视"的章法定稿；② BEM 改造地图（表 17.3/chapter_map 落盘版）的字段切分是否符合论文2 §4.3 的改造预期（α/ε/λ/ρc/d 与空调日程/占用率/光伏效率）；③ 轻轨实验的"城市等效表面"简化口径（三表面压缩单柱、无街谷辐射/稳定度反馈）与"表皮昼强夜弱 vs 2m 夜强昼弱"的表述是否合意；④ **预留集群双跑**（兰州 d02 `sf_urban_physics=0 vs 1`，24 h，T2/HFX/TSK 单点）是否执行（为 ch19 的 =0 vs =3 双跑铺垫）；⑤ AHOPTION/ALHOPTION 默认全关、AHE 数据与 AH 表值双计风险的两处提示是否保留在正文。
13. **（ch18）**：① `em_grav2d_x`"重力波→密度流"、`em_b_wave`"双向周期→x 周期+y 对称"两处 ch05 表勘正口径；② 口径勘正四则（另两条：`em_bubbling` 不存在、`em_esmf_exp` 是耦合包）是否接受；③ 章法定稿：技术章六段式 + 三条机制线索（双钥匙/初始化源码/集群实跑）+ 18.5 全实录（含首轮 rc=127 缺链接与间歇段错误的诚实记录）；④ **ch18 实测附带发现**："物理全关算例的 `PSFC`/`T2` 恒为 0"与"`frames_per_outfile=1000` 多帧同文件"两条是否入正文（现已在 18.5.7/18.6）；⑤ **ch17 预留的集群双跑**（sf_urban_physics=0 vs 1，d02，24 h）是否在 ch19 起步前补做，或直接并入 ch19 的 =0 vs =3 双跑；⑥ ch12–ch16 的五组预留集群实验（radt/ghg/o3、mp=6vs8、PBL 三方案、cu=1vs16、slab vs Noah）是否借 ch18 已建好的"理想算例快速回归"路径一并清偿。
14. **（ch19）**：① **单行源码补丁**（`module_sf_urban.F` 普通城市格点默认类别 2→1）作为"最小改造"写进教材是否合意——它使三档城市实验得以跑通，但城市效应被系统性低估；② **"三重约束"叙事**（PBL 兼容 / 面层兼容 / `ZDC+Z0C+2<ZA`）与探针数值（类2 8.051 m vs ZA 8.046 m）是否作为本章核心发现保留；③ **诚实结论**（无本地参数时城市方案净效应 <0.3 K、"夜间信号缺失"归因于 AH 关闭）是否接受，还是希望补做"开 AH（AHOPTION=1）"的第四跑以补上夜间信号（成本约 1 节点·时 + 数据抽取与诊断）；④ 诊断口径：城市格点均值 vs ERA5 0.25° 面平均的 1 K 量级代表性问题、T-lnP 用"LCL=LFC=699 hPa"表述是否合适；⑤ 三跑资产（ch19_exp 下 sf0/sf1/sf3 各 ~5 GB wrfout + stage 子集）的保留/清理政策（教材只需 stage 子集与图，原始 wrfout 可清）；⑥ `workspace/data/ch19/wrfinput/*_patched.nc`（早期"改 wrfinput 注入 UTYPE"路线的废弃副本，共 4 个 ~70 MB）可删否。
15. **（ch20 + 全书补充）**：① ch20 三级实战的**实测结论口径**——L1"十二变量位级一致（非扰动铁证）"、L2"域均单调 + 0.83–3.10% 逐点负值归因稳定层混合"、L3"东组 −2.85 K/正午 −6.67 K、西组 −0.089 K（表值对照）"是否接受；② L3 判据二的改写（SWDOWN/RAINNC 的大差定性为**云-降水非线性反馈**而非"必须不变量"，"应当不变"改为三级检验：注入场位级/对照组零效应/RAINC 位级）是否合意；③ **事故链七条**（新增⑤容器缺 m4、⑥Registry 触发门、⑦容器内 ncks 静默失败+libnco+DataName=TS_URB）全部入正文是否合适——⑦ 的"Registry DataName ≠ 变量名"是新增方法论点；④ ch02 的 **4.5/4.6.0 精确发布日期按 GitHub 时间线推断**（其余均有官方日期）的诚实标注口径是否接受；⑤ **三类专栏体例**（科研改造案例库/核心代码精讲/模块依赖树）与 ch01 §1.6.2 的约定、ch20 §20.7.1 的 27 案总索引是否合意；各章案例的详略（官方上游化案例收录较详、纯思路案例较简）是否均衡；⑥ ch01 的 WRF 家族图与"学科分支↔WRF 模块对照表"是否合意；⑦ 全书补充采用**章尾追加专栏**（不打乱原章节编号）的方式是否接受，还是希望把专栏内容编织进各章正文。

## 集群状态
- ch20 全链作业 COMPLETED：重建 v3=439963（五二进制）、运行=439976（六跑 rc=0）、抽取=440034/440037（24 stage 文件）+ 手工补抽 L3 2d；`ch20_stage_all_v2.tar.gz`（142.8 MB）已拉回本地 `workspace/data/ch20/stage`
- ch19 全部作业 COMPLETED：439806/439809–439815/439817/439819/439822/439825/439828/439866（含诊断与三跑）
- ch19 三跑结果目录：`ch19_exp/{sf0,sf1,sf3}`（各 5 天两域 SUCCESS）；stage 子集已拉回本地 `workspace/data/ch19/stage`
- ch12 预留（radt/ghg/o3）、ch13 预留（mp=6 vs 8）、ch14 预留（PBL 三方案）、ch15 预留（cu=1 vs 16）、ch16 预留（slab vs Noah）与 ch17 预留（sf_urban_physics=0 vs 1）——**ch17 的意图已在 ch19 以 =0/=1/=3 三跑兑现**；其余五组仍未执行（见复核清单第 7③/8④/9③/10④/11⑥）

## 状态文件
- notes.md（含批次 2 ch10–ch20 收官段）；verify_log.md（ch10–ch20 全记录，ch20 段含构建/运行/抽取/诊断四节）；chapter_map.md（ch10–ch20 条目已补）；workspace/context/ch1{8,9,20}_material.md（素材与实验底稿）；本文件

## 下一步（ch20 已收官 → ch21 + 附录）
- **ch21 solve_em.F 全流程**（第 V 部收官章）：rk 循环/蚀small-step/耦合器/边界——与 ch03 §3.8 驱动树、ch18 §18.9 初始化链、ch10 §10.12 基态树对接
- 附录 a（符号与物理常数对照：书 ↔ WRF 变量 ↔ Registry；ch11 常数表为底稿）→ b（中英术语）→ c（常见错误速查扩编）→ d（参考文献与数据源）
- index.md（全书目录 + 使用说明 + 页码换算规则）+ ch01/ch02 交叉链接补全
- 用户复核清单第 15 条（七项口径）待回复；第 7③/8④/9③/10④/11⑥ 的五组预留集群实验仍未执行

### ch20 交付记录（2026-10-11 下午）
- `doc\ch20_modifying_wrf.md`（三级实战 + 事故链七条 + §20.7.1 案例总索引 27 案；9 处待填全部回填；3 图）
- 全链实测：重建 439963（五二进制）→ 运行 439976（六跑 rc=0，L1a/L1b/L2a/L2b 各 ~610 s、L3off/L3on 各 322 s）→ 抽取 24 文件 → 诊断 3 图（L1 位级非扰动铁证；L2 域均 PBLH 1199/1635/1902 m 单调；L3 东组 −2.85 K/正午 −6.67 K、西组对照 −0.089 K）
- 全书同日补充：ch01/ch02 交付；ch03–ch19 三类专栏（案例库/依赖树/核心代码）
- `doc\ch19_lanzhou_heatwave.md` 追加 §19.8（探针法/三重约束链方法论）；`doc\ch18_ideal_cases.md` 追加 §18.8/18.9