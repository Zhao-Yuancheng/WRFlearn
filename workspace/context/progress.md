# Progress — 当前状态（可重写）

时间锚点: 2026-10-12（code_17 补录完成——**文库齐账 29/29**，等待用户验收）
阶段: **《WRF 源码精读》全部完成**——六批 + code_17 补录，doc\code\ 共 33 个文件、480 个保真块 ALL PASS（指涉 44 文件缺失 0）。code_17 补录中确认本地副本的 module_sf_urban.F 含 urban-nbs 扩展（树冠/绿屋顶/2026-01 活注释，教材 ch17 引用需按本地口径核对）。教材延伸阅读回填按用户裁决不逐章执行（README §二映射表承载）。工具链：code_extract.py（栈式配对+CRLF 归一化）、acceptance.py v2、fp_files.py、check_quotes.py。待办仅剩教材侧：复核清单 13 项 + 五组集群实验裁决。

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
16. **（ch21 + 附录 + index）**：① ch21"十四站"走读的详略取舍（长实参表省略为 `…`、小步长精讲集中在 21.3）是否合意；② ~~**微物理调用时刻的表述**是否需要在 ch13 补一句交叉注~~ **已办结（批次 5）**：ch13 §13.6.1 已补交叉注（详见 verify_log 批次 5 段修订清单①）；③ 案例库案 28–35 的选案（SKEBS/WRF-CMAQ/WRF-Fire/MAD-WRF/use_theta_m/WENO/极区滤波/IEVA）与"文献未核条目显式标注"的口径；④ ch21 只做轻轨时间步进账本实验、未加集群内核审计（如按 ch08 口径分档计时小步长成本）——是否需要补；⑤ 附录 a 常数表"偏差列"（如 g=9.81 vs 书 9.80665）的呈现方式；⑥ app_d 文献三级标记（核验/通行/线索）的分级口径是否接受；⑦ index.md 的阅读路径建议（系统学习/只改 WRF/只跑个例/城市热岛四条）是否合意。

## 集群状态
- ch20 全链作业 COMPLETED：重建 v3=439963（五二进制）、运行=439976（六跑 rc=0）、抽取=440034/440037（24 stage 文件）+ 手工补抽 L3 2d；`ch20_stage_all_v2.tar.gz`（142.8 MB）已拉回本地 `workspace/data/ch20/stage`
- ch19 全部作业 COMPLETED：439806/439809–439815/439817/439819/439822/439825/439828/439866（含诊断与三跑）
- ch19 三跑结果目录：`ch19_exp/{sf0,sf1,sf3}`（各 5 天两域 SUCCESS）；stage 子集已拉回本地 `workspace/data/ch19/stage`
- ch12 预留（radt/ghg/o3）、ch13 预留（mp=6 vs 8）、ch14 预留（PBL 三方案）、ch15 预留（cu=1 vs 16）、ch16 预留（slab vs Noah）与 ch17 预留（sf_urban_physics=0 vs 1）——**ch17 的意图已在 ch19 以 =0/=1/=3 三跑兑现**；其余五组仍未执行（见复核清单第 7③/8④/9③/10④/11⑥）

## 状态文件
- notes.md（含批次 2 ch10–ch20 收官段）；verify_log.md（ch10–ch20 全记录，ch20 段含构建/运行/抽取/诊断四节）；chapter_map.md（ch10–ch20 条目已补）；workspace/context/ch1{8,9,20}_material.md（素材与实验底稿）；本文件

## 下一步（批次 5 已收官 → 等用户复核）
- **批次 5 全书校阅已完成**（2026-10-12 凌晨）：五路清查 + 13 处修订，详见文末"批次 5 校阅记录"、notes.md 与 verify_log 对应段
- **新立项：《WRF 源码精读》配套文库**（2026-10-12 用户批准）：方案底稿 `workspace/outline/code_library_plan.md`；doc\code\ 29 篇、依赖拓扑编号（L0 底座→L1 方案→L2 驱动器→L3 枢纽→L4 框架→L5 solve_em 导航页）；六批生产

### 源码文库批 2 交付记录（2026-10-12）✅
- **code_10**（MYNN-SFC，5060 行/52 块，多源六文件）：关键事实——WRF 运行线=surface_driver CASE(5) → mynnsfc_driver（WRF wrapper，xland/雪深 5 cm/xice 三路分派，ψ 表实参传入）→ mynnsfc_land/_water/_ice；module_sf_mynnsfc.F90 是 CCPP-FV3 孪生线（注释最全，作主讲底本）；选项编号双轨表（sf_mynn_sfcflux_land/water vs iz0tlnd/isftcflx）；tests/ 黄金文件回归
- **code_22**（PBL driver，2604 行/27 块）：Registry 方案号全表（1/2/3/4/5/7/8/9/10/11/12/16/17/99）；触发节拍四测试；u_phytmp 移动嵌套参考系；idiff=0 休眠的 Martilli diff3d；MYNN 16 项守卫+SPP 包裹+scalar_tend 回填；风机/GWD/雾沉降/AHE 附加模块；AHE 双口径（=1 RTHBLTEN vs =2 HFX）
- **code_14a/14b**（bep_bem 共享底座，3086+3166 行/36 块）：ind_* 索引折叠表=论文 2「标量→场」先例；三处厚度数组一致性红线；flux_flat_ground 休眠；upward_rad 硬 stop 哨兵；NEW CDRAG；绿屋顶/水力参数/PV 单元
- **code_15**（bep 单独版，3770 行/28 块）：与底座同源单元给差异注记；cdrag=0.4 常数；angle 未调用；跨模块疑点核销（无隐性依赖）
- **code_16**（bem，3009 行/27 块，论文 2 主改造对象）：六面房间约定；室内 6×6 辐射系统；wall 系数缓存=场化第一性能陷阱；恒温恒湿「一步拉回+限速」；air_cond COP 账本
- **code_24**（surface driver，1817 行/5 块）：两族 CASE 选段+收尾（OML/Lake/Q2 双限幅/AHE=2）+MYNN seaice wrapper 全文
- 工具：code_extract.py **v1.2**（{{CODE:<WRF根相对路径>:key}} 多源 assemble）；新增 fp_files.py（指纹表）；PowerShell heredoc 不可用教训
- 验收：acceptance.py 全量 **315 块 ALL PASS**、11 篇引号干净、指涉缺失 0（含 code_15/16 交叉引用闭合）

### 源码文库批 3 交付记录（2026-10-12）✅
- **code_12a/12b**（noahlsm 4759 行/32 块，A 级拆两全 31 单元）：SFLX 十二站走读（ZSOIL 负深→REDPRM→绿度插值→降水分型→SNFRAC+ALCALC→雪平面平行导热→SNOWZ0→PENMAN→CANRES→NOPAC/SNOPAC→能量换算→水量诊断）；关键点——urban 硬参数（SHDFAC=0.05/RSMIN=400/SMC 四值/DF1=3.24/CSOIL_LOC=3e6）、雪导热 ×2.0 翻倍、雪层三均值实际按 SNCOVR 线性混合、**收尾 DO K=1,4 四层硬编码陷阱**、IRRIGATION_CHANNEL 透传链、fasdas 全线、SFCDIF_off 休眠（CH 由面层传入）
- **code_13**（noahdrv 5447 行/14 块，B+C）：ICE 三分支（海冰 CYCLE 跳过 LSM/冰川 SFLX_GLACIAL 外部文件/普通陆地 SFLX 全参）；FFROZP 双口径；NOAHRES 能量残差式；UCM 前处理（NATURAL 重定义+IRI 灌溉+AOASIS，仅限单层 UCM）；BEP/BEM 聚合四步；TBL 读取双段式+LCZ 校验；LSMINIT 的 FRH2O 初值化；lsm_mosaic 双件 C 注（折叠存储）
- **code_11**（ntiedtke 533 行/5 块，A 级全文）：~~physics_mmm 缺席~~ **订正（2026-10-12 用户指出）：实体在 phys/physics_mmm/cu_ntiedtke.F90（3594 行/15 单元），code_11 §二/§八 已改为实体对照注记（单元地图+接口契约+订正记录）**；pre/post_run 的 k↔zz 垂直翻转模板；omg=−0.5·grav·ρ·(w+w+1) ω 口径；状态差分式倾向输出；每步 cu_ntiedtke_init 常数注入；CU_ACT_FLAG 恒 true
- **code_23**（cumulus driver 1902 行/12 块，B 级全 CASE）：四测试门控（cudt 语义）；G3/NTIEDTKE 前期倾向组装（RTHFTEN+RTHRATEN+RTHBLTEN 再 ×pi）；全 CASE 差异注记（SAS 系禁自适应 dt、G3 后处理 cu_physics==5 硬编码+spread3d、KFCUP 手工 tmppratec=raincv/DT、CAMZM 强制 f_qi）；aer_time_int/aer_p_int 全文（Dec–Jan 环绕插值、top-down 翻转）
- 验收：acceptance.py 全量 **378 块 ALL PASS**（17 篇）、批 3 五篇引号 0 违例、指涉 26 文件缺失 0（12a/12b→code_13 前向引用闭合）

### 源码文库批 4 交付记录（2026-10-12）✅
- **code_11 订正**：physics_mmm 实体在 phys/physics_mmm/cu_ntiedtke.F90（3594 行/15 单元/cumastrn 744 行主实体）——§二/§八 改实体对照注记（skel+成稿手改、未重组装）
- **code_20**（radiation_driver 5710 行/26 块）：radt 四测试（ra_call_offset 语义）；云量三案全解（Xu-Randall/二值/Thompson 尺度感知）；气溶胶三通道（aer_opt=1/2/3）；LW 案 RTHRATEN 占用 vs SW 案叠加的调用序依赖；水物质备份恢复链；ACC 通量累积+CLDT 随机重叠诊断；SPP 加减对；pre_radiation_driver 地形阴影（跨 patch 迭代 niter）；swint 幂律插值两件；FARMs 通道
- **code_05**（rrtmg_lw 14633 行/8 块）：k 分布全套数据结构（KA 四角插值/laytrop/次要气体比率/自外连续谱）；taugb1 样本（corradj 修正）；cldprmc 云光学四选；rtrnmc 变扩散角+自认误差 1-4 W/m²；McICA 种子 150；LW 气溶胶只吸收；OLR 取 TOA；lwcldpr 休眠；85 单元分组总表
- **code_06**（rrtmg_sw 12786 行/11 块）：parrrsw（14 波段/112 g 点/scon 1368.22）；**SW 不自带 parkind（依赖 LW 文件）**；CO2 年增长函数+CO2MULT 355 ppm 机制；cldprmc_sw 尾段 delta-M 标定全解；spcvmc_sw（Barker 两流 kmodts 三选）；反照率谱段归属与 SSiB 四分量；WRF_CHEM 气溶胶 Angstrom 展开+AOD>6 钳位；swaerpr 六类表全文；62 单元分组总表
- **code_60**（ra_aerosol 1470 行/3 块 C 级）：AOD@550 谱展开器（Goddard 11 波段/RRTMG 14 波段）；aer_type 三类+RH 参数化；10 单元接口索引
- **工具升级**：code_extract.py 扫描器栈式配对（F90 CONTAINS 嵌套）；回归 noahlsm/code_12a 通过
- 验收：acceptance.py 全量 **426 块 ALL PASS**（21 篇）、指涉 31 文件缺失 0、批 4 五篇引号 0 违例

### 源码文库批 5 交付记录（2026-10-12）✅
- **code_01**（module_model_constants 159 行/1 块 A 轻全文）：逐常数注释——双口径并存清单（cliq/cice、XLV/XLS/XLF、SVP 群 vs Murray 群）、p1000mb 名实之差、defc/defm 被关闭、ECCENTRICITY 定义而未用、行星框架遗迹
- **code_31**（part1 2027 行/10 块全调用段）：五大驱动器完整实参表；fire 三选（0/CFBM/fire_driver_em_step）；convtrans_prep 在 cumulus 后（辐射用上一步积云云量）；pre_radiation_driver=非局地阴影专用；surface 605 行实参分拣（灌溉全家桶/Noah-MP opt 22/SSiB 40/BEP 源项）
- **code_32**（part2 1132 行/11 块）：两段记账（calculate_phy_tend→update_phy_ten）；HALO_EM_PHYS_CU 八方案名单=带动量倾向的积云（与 code_23 交叉印证）；随机五连（SKEBS/SPPT/multi_perturb/spp×3）；PLANET damptop 故意断编译彩蛋；垂直扩散仅 bl_pbl=0 时做；km_opt=5 隐式
- **code_30**（big_step 6758 行/6 块）：calc_p_rho_phi 全文（ch10 公式本体——hypsometric 1/2 双式、静力积分含水重、cvpm 口径）；phy_prep 全文（rho=1/alt·(1+qv)、p8w 顶 ln(p) 外插、p_hyd 静水积分）；rhs_ph 头（φ 方程 advective form+gw 项）；43 单元分组总表
- **code_40**（initialize_real 9214 行/7 块基态段）：p_surf hypsometric 反解；两段式基态温度（t00+A·ln / tiso+A_strat·ln）；初值同源原则（「similar to what the model does」）；500 hPa 高度调整迭代（adjust_heights）
- **code_41**（nest_init_utils 1184 行/2 块）：hybrid_opt 四式（Klemp 多项式五系数/sin²）；c1..c4 生成与单调性校验（reduce etac FATAL）；compute_eta（silly levels 估 ztop、max_dz FATAL「Add more levels for e_vert」）
- **code_50**（solve_em 5197 行 C 级导航页/0 块）：主循环 mermaid 地图+六锚点行号索引（L812/L850/L1284/L1397/L1504/L3881）
- 验收：acceptance.py 全量 **463 块 ALL PASS**（28 篇）、指涉 39 文件缺失 0（修复 code_40 漏组装与 ch07 引用名笔误）、批 5 七篇引号 0 违例

### 源码文库批 6 交付记录（2026-10-12）✅ 文库主体收官
- **code_08**（dust+gocart，189+39 行/2 块 C）：bulk_dust_emis 头段+GOCART 数据底座全文；**输出 nifa2d 数浓度直接进 QNIFA**（免 chem_opt 的沙尘→CCN→辐射轻链条）；porosity 19 类表与 noahlsm MAXSMC 同值不同源；主体 L56–L187 注记
- **code_61**（海冰两件+glacial_only，502+1291+1280 行/3 块 C）：三件头部+同源差异注记表——**常数/求解器经 USE noahlsm 导入的单点维护样板**；雪导热 ×2 翻倍只在陆地件；seaice_noah 的五选项与分值冰判据；SFLX_GLACIAL 只有 RUNOFF1
- **code_62**（shallowcu/fire/fdda，767+149+626 行/3 块 C）：shallowcu 签名（rainsh 账本/CAM 诊断/SPP 对）；**fire WRF 包装层 149 行全文**（irun 1/2 init、3..6 step、rthfrten/rqvfrten 倾向出口=part2「fire」数组的来源）；fddagd 双时刻场+六倾向出口（含 RMUNDGDTEN）
- **code_00**（README 总纲）：双轨读法（依赖拓扑/教材章序）、29 篇目总表（28✅+code_17 待补）、体例约定、工具链、四条阅读路径（内核/改方案/只跑个例/城市专题）
- **工具升级**：code_extract.py load_lines CRLF/CR 归一化（gocart 唯一 CRLF 文件；诊断→定位→修复全程 20 分钟）；临时诊断脚本已清理
- 验收：acceptance.py 全量 **471 块 ALL PASS**（32 文件）、指涉 43 文件缺失 0、批 6 四篇引号 0 违例

- 用户复核清单第 15、16 条待回复（16② 已办结，余 13 项）；第 7③/8④/9③/10④/11⑥ 的五组预留集群实验是否执行待裁决
- ch13–ch15 考点节待第 6 章 PPT 到货校准（ch16 已按 PPT 4 内容页口径定稿）
- 集群侧：439019（用户自己的 FDS 作业，勿动）；本教材全部作业已 COMPLETED

### ch21 + 附录 + index 交付记录（2026-10-11 晚，批次 4）
- `doc\ch21_solve_em_dynamics.md`：十四站走读（solve_em 5197 行全实测）；RK3+声波小步长机制；物理调用时刻精确到子程序（part1/2 仅 rk_step==1；微物理在 RK 循环后）；21.6 时间步进账本实验（d01 8000 步/d02 24000 步与 439419 逐位吻合）；案例库案 28–35；依赖树 mermaid
- `doc\app_a_symbols_constants.md`：三列对照 + `module_model_constants.F` 全常数 vs 书附录 C 偏差表
- `doc\app_b_terminology.md`：九类中英术语汇编
- `doc\app_c_troubleshooting.md`：c.0 万能诊断五步 + 七段速查 + 兼容守门员六条
- `doc\app_d_references.md`：三级标记文献清单（核验/通行/线索）+ 数据源致谢
- `doc\index.md`：总目录 + 使用说明 + 页码换算规则（印刷页 N → page_{N+14}）+ 阅读路径
- 脚本：ch21_timestep_audit.py（实验）、ch21_recon.py（侦察）、ch21_extract_appendix_src.py（附录汇编底稿）、ch21_check_quotes.py（引号自查）；日志 ch21_timestep_audit.log
- `_fix_quotes.py` 六文件全过（ch21 转 118 处；附录 46 处；围栏外英文引号 0）

### ch20 交付记录（2026-10-11 下午）
- `doc\ch20_modifying_wrf.md`（三级实战 + 事故链七条 + §20.7.1 案例总索引 27 案；9 处待填全部回填；3 图）
- 全链实测：重建 439963（五二进制）→ 运行 439976（六跑 rc=0，L1a/L1b/L2a/L2b 各 ~610 s、L3off/L3on 各 322 s）→ 抽取 24 文件 → 诊断 3 图（L1 位级非扰动铁证；L2 域均 PBLH 1199/1635/1902 m 单调；L3 东组 −2.85 K/正午 −6.67 K、西组对照 −0.089 K）
- 全书同日补充：ch01/ch02 交付；ch03–ch19 三类专栏（案例库/依赖树/核心代码）
- `doc\ch19_lanzhou_heatwave.md` 追加 §19.8（探针法/三重约束链方法论）；`doc\ch18_ideal_cases.md` 追加 §18.8/18.9

### 批次 5 校阅记录（2026-10-12 凌晨）✅
- **工具**：`workspace/scripts/batch5_linkcheck.py`（26 文件交叉引用+死链审计；报告 `workspace/logs/batch5_linkcheck.md`）——扫得章引用 1237/§小节 475/链接 99/路径 79/文件 35/表 18/附录 13/书页换算 4；源码锚点缺失 0、书页缺失 0、表缺失 0
- **修订 13 处（六文件）**：ch13（微物理时刻交叉注→ch21 §21.2.14；"图 13.1"×2 改体例内表述；埃玛图图注补 q_s/r_s 口径注）；ch14（part1 枚举补"积云"；"每步多次调用"误表述改写——solve_em.F:588 `dtm=grid%dt` 实证；E1 补 θse/θe 判据量口径注）；ch16（考点标签改"PPT 4 内容页归纳"——原"课件未到"系笔误，PPT 4 在案且无显式考点页）；ch21（两处 file:/// 链接改反引号体例）；app_a（假日志指涉改 ch11 §11.6+脚本；补 κ_d 泊松常数行并与 KARMAN 互注）；index（§1.2 考点体系说明订正为 ch13–ch15 待校准；修订记录补批次 5 行）
- **三源事实核验**：solve_em.F 微物理 DT 实证；书 p168（page_0182.jpg）证实 ch15 书图 10.9/10.18 引用准确；书 p143（page_0157.jpg）证实埃玛图 (6.4.4)/(2.2.12b) 引据一致；PPT 4 slides 17–20 证实 §4.3 覆盖
- **符号统一结论**：θse/ε/p00/g0/扰动位温全书一致；κ 双义已公证互注
- **全角引号**：26 文件复跑全 converted=0（围栏外 0）
- **误报甄别**（勿重复追查）：ch16 方程 \tag 号、源码树 doc/README.*、ch15 书图引用、ch14"条件性不稳定"（书 (6.8.14) 原词）
- chapter_map.md 无需更新；复核清单 16② 办结