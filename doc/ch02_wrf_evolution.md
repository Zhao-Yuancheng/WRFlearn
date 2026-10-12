# 第 2 章 WRF 4.x → 4.8.0：模式演化与新特性

> **本章任务**：把“我们用的 WRF 4.8.0”放到时间轴上——4.x 系列每一代带来了什么、4.8.0 相对 4.6/4.7 新增了什么、WPS 4.7.0 如何同步。**写作纪律**：每个“新特性”陈述都给出处（GitHub 官方 release notes 的 Pull Request 编号，或本地源码指纹）；查不到确切出处的，显式标注“待核”而不是含糊带过。
> **材料来源**：WRF 源码包自带 `README`（内嵌 3.x 及更早版本沿革，并指明 4.0 起的官方发布页 `github.com/wrf-model/WRF/releases`）＋ 4.0–4.8.0 各版 release notes（本教材写作时逐版抓取核对）＋ 本地源码树 `source/WRFv4.8.0/WRFV4.8.0/` 的文件级证据。

---

## 2.0 本章地图

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



- **2.1** 时间线总览表（全部有官方日期）；
- **2.2** 各代里程碑选讲（只讲“对本书读者有用”的，且每条标注与本书哪一章对接）；
- **2.3** 4.8.0 相对 4.6/4.7 的新特性精讲（本章重点）；
- **2.4** WPS 4.7.0 同步与跨包依赖；
- **2.5** 本地源码指纹核验表（每条特性 → 一个能 `ls` 出来的证据）；
- **2.6** 版本口径对本书的三条影响。

---

## 2.1 版本时间线总览

| 版本 | 发布日期（官方） | 一句话主题 | 阶段 |
|---|---|---|---|
| **4.0** | **2018-06-08** | 混合 σ-p 垂直坐标成为默认；湿位温变量默认化 | 4.x 起点 |
| 4.0.1–4.0.3 | 2018 | 维护版 | |
| **4.1** | **2019-04-12** | Goddard 4ICE、WSM7/WDM7、ISHMAEL、Goddard 辐射接入 | 微物理大年 |
| 4.1.2–4.1.5 | 2019–2020 | 维护版 | |
| **4.2** | **2020-04-23** | SMS-3DTKE（km_opt=5）、Noah 灌溉三选项、FARMS 太阳辐射 | 次网格湍流/能源 |
| 4.2.1–4.2.2 | 2020–2021 | 维护版 | |
| **4.3** | **2021-05-10** | BEP/BEM 接入 YSU PBL；EEPS（bl_pbl_physics=17）；光伏板参数化；NoahMP 动态灌溉 | 城市与精细 PBL |
| 4.3.1–4.3.3 | 2021–2022 | 维护版 | |
| **4.4** | **2022-04-26** | **NoahMP 移为 git 子模块**；RRTMG 云重叠 cldovrlp=5（指数-随机+去相关长度）；浅水粗糙度 | 构建体系转折 |
| 4.4.1–4.4.2 | 2022 | 维护（**LCZ 编号改 51–61**） | |
| **4.5** | **2023-04**（据 GitHub 时间线；4.5.1=2023-07-25、4.5.2=2023-12-22） | Thompson 二矩冰雹（mp=38）；k-ε-θ² PBL；New Tiedtke 尺度自适应（<15 km 自动生效） | 对流与精细尺度 |
| **4.6** | **2024-05**（据 GitHub 时间线；4.6.1=2024-10-16） | **CMake 构建路线**；YSU/WSM6/NTiedtke/GWDO/修订 MM5 面层**移入 MMM 共享物理库**；SLUCM 分布式拖曳与 AHE；三个新风电场参数化 | 共享化元年 |
| **4.7** | **2025-04-25**（4.7.1=2025-06-02） | **MYNN-EDMF 子模块化**（`__mynn_`→`__mynnedmf_`）；UFS 双矩 7 类（mp=27）；RCON 暖雨方案；manage_externals | 子模块化第二年 |
| **4.8** | **2026-06-08** | **TEMPO 微物理；GFL 积云；MYNN-SFC 子模块；NoahMP v5.1.2；UCM 城市树木（NbS）；动态闪电方案** | 本书基线 |

> **查法**：任意 4.x 版本的 notes 都可在 `https://github.com/wrf-model/WRF/releases/tag/v<版本号>` 页面找到；源码包 `README` 里只内嵌到 3.9.1.1 的沿革（2017-08-28 起新版本指向 GitHub）。3.x 及更早的历史（V3.0 2006 → V3.9.1.1 2017）在 README 中按时间倒序排列，可作族谱速查。

---

## 2.2 各代里程碑选讲（只讲与本书相关的）

### 2.2.1 WRF 4.0（2018-06）：两处“默认值”的变更最值得记住

- **混合垂直坐标成为默认**（4.0 notes 原文：*The hybrid sigma-pressure vertical coordinate introduced in V3.9 is now the default*；关掉用 `hybrid_opt=0`）。→ 本书 ch07 的 namelist 逐项、ch10 的坐标推导都按 `hybrid_opt=2` 讲；
- **温度变量默认为湿位温**（*Temperature variable is now moist theta by default*，`use_theta_m`）。→ 这就是 ch19 诊断时“T 不是温度而是扰动位温”那个著名坑的根源；
- 微物理：P3 双冰类选项（mp=52）、Thompson-Eidhammer 加扬尘方案（`dust_emis=1`）；积云：CESM 气溶胶-MSKF/Morrison 交互（`aercu_opt`）；NoahMP 变量**拆出独立的 `Registry/registry.noahmp`**（本地树已核，见 §2.5）。

### 2.2.2 WRF 4.1（2019-04）：微物理“大扩容”

- **Goddard 4ICE**（mp=7，取代旧 Goddard）、**WSM7**（mp=24）/ **WDM7**（mp=26，新增雹类）、**ISHMAEL**（mp=55，预报冰晶形状演化）；
- **Goddard 辐射**（ra_lw/sw=5）与 4ICE 配套（HITRAN2012 + 散射库）；
- MYNN 更新（bl_mynn_cloudpdf=2 的非高斯浮力通量、TKE 耗散加热）、BEM 空调范围表（BLDAC_FRC/COOLED_FRC）、BEP/BEM 内存重排（BEM 内存占用降 64%）；
- 修复 CAM 臭氧插值错一个月的 bug（o3input=2，RRTMG）——ch12 讲臭氧输入时的历史注脚。

### 2.2.3 WRF 4.2（2020-04）：次网格湍流与能源气象的信号

- **SMS-3DTKE**（km_opt=5，上海局地气象台 Zhang et al. 2018 MWR）：把 TKE 次网格混合从 LES 延伸到中尺度——要求 `bl_pbl_physics=0`、`diff_opt=2`；
- Noah LSM **灌溉三选项**（Valmassoi et al. 2020：Channel/Drip/Sprinkler）——“人类活动进入陆面模式”的代表案例，ch16 的延伸阅读；
- **FARMS** 快速全天候地表短波（swint_opt=2，WRF-Solar 套件）与太阳诊断包（solar_diagnostics=1）。

### 2.2.4 WRF 4.3（2021-05）：城市与精细 PBL（本书第 III 部的两位主角入场）

- **BEP/BEM 接入 YSU PBL**（Hendricks et al. 2020 JAMC）——在此之前多层城市方案只配 MYJ。→ ch17 城市兼容矩阵、ch19 城市对照实验（`sf_urban_physics=3` + YSU）的制度基础；
- **EEPS**（k-ε PBL，Zhang et al. 2020，bl_pbl_physics=17）；
- 光伏板参数化（PVP，4.3.1 修复为预报方程版）——BEM 屋顶光伏的物理来源（ch17 BEM 节）；
- NoahMP **动态灌溉**（sprinkler/micro/surface flooding）。

### 2.2.5 WRF 4.4（2022-04）：构建体系转折点

- **NoahMP 改为 git 子模块**（编译期自动拉取；离线编译需 `git submodule update --init --recursive`）。→ 从 4.4 起，“下载 tar.gz 但不选 Source Code 下载”成为官方反复强调的注意事项（release notes 的 NOTE 条目）；4.8.0 沿用此制（顶层 Makefile 里有 NoahMP/MYNN-EDMF/MYNN-SFC 的“子模块就位”硬检查，ch05 会引用）；
- RRTMG **云重叠 cldovrlp=5**（指数-随机 + 去相关长度 idcor）——ch12 云重叠机制的当代选项；
- 浅水粗糙度（shalwater_z0=1）、16 类物理倾向累计输出（acc_phy_tend=1，ch15 “倾向加餐”用得到）。

### 2.2.6 WRF 4.4.2（2022）：LCZ 编号改版

城市局地气候分区（LCZ）编号从 31–41 改为 **51–61**，以避开 NLCD 土地类型（改 VEGPARM/LANDUSE/MPTABLE 三表）。→ ch17 的 landuse 四体系表、“51–61 = LCZ_1..11” 口径的由来。

### 2.2.7 WRF 4.5（2023-04）：对流与精细尺度

- **Thompson 二矩霰/雹 + 预报密度**（mp=38，Jensen et al.；需数据文件 qr_acr_qg_mp38V1.dat）；
- **k-ε-θ² PBL**（Zonato et al. 2022 MWR，精细网格设计；4.7 里其相似度函数还有一次 z0 订正）；
- **New Tiedtke 尺度自适应选项**（基于 Wang 2022，格距 <15 km 自动生效）→ ch15 精读 NTiedtke 时讲的 scale_fac 表就是这条线的产物；
- MYNN-EDMF “universalization”（子程序重组、bl_pbl_physics=6 退出、`bl_mynn_closure` 可选 2.5/2.6/3.0）→ ch14 版本史 V1.0→V6.0 的中间一环；
- 4.5.2 顺手修了 **WDM6/WDM7 自 4.0 起云水自动转化率差 600 倍**的 bug（个别试验降水翻倍）——“版本口径影响结果”的教科书案例。

### 2.2.8 WRF 4.6（2024-05）：MMM 共享物理库与 CMake

- **CMake 构建路线**（em_real/em_ideal 起步，后逐步覆盖 chem/wrfplus/hydro）→ ch05 双构建体系之 CMake 轨；
- **五件套移入 MMM 共享物理库**（release notes 原文均标注 *from the future shared MMM-physics repository*）：修订 MM5 面层、**New Tiedtke 积云**、**WSM6 微物理**、**YSU PBL**、**GWDO（gwd_opt=1）**；4.7 又移入 Shin-Hong。本地指纹：`phys/physics_mmm/` 下 bl_ysu.F90、bl_shinhong.F90、bl_mynn.F90、bl_gwdo.F90、cu_ntiedtke.F90、mp_wsm6.F90、mp_radar.F90（§2.5）；
- **SLUCM 分布式参数**（`slucm_distributed_drag`：建筑高度/迎风面积比/粗糙度/零平面位移可空间变化）＋（`distributed_ahe_opt` 人为热三种模式）→ **ch20 第三级补丁的“官方式样”就抄这两个开关**（`model_config_rec%…` 的读取链）；
- 三个**新风电场参数化**及集合（次网格尾流）；本地树有 `phys/module_wind_fitch.F`（经典 Fitch 方案）与 `phys/module_wind_mav.F`（新家族成员）；
- NSSL 三矩选项（mp=18，雨/霰/雹）。

### 2.2.9 WRF 4.7（2025-04）：第二个物理子模块年

- **MYNN-EDMF 子模块化**（`https://github.com/NCAR/MYNN-EDMF`；模块名 `__mynn_`→`__mynnedmf_` 以解决 MPAS 冲突；k-only 重构提速 10–15%）→ **ch14 精读的 `phys/MYNN-EDMF/module_bl_mynnedmf.F90` 就是这个子模块**；本地树中其目录下同时有 `WRF/`、`MPAS/`、`tests/` 三个子目录（§2.5）；
- **UFS 双矩 7 类微物理**（mp=27，Songyou Hong；in-cloud 微物理概念 + CCN 友好气溶胶 + 半拉格朗日沉降）；
- **RCON 暖雨微物理**（Conrick et al. 2023 MWR；对数正态云滴谱替代 Γ 谱 + 云水低层沉降成毛雨模态）；
- NoahMP LCZ 类别引用修复（此前 LCZ 在 NoahMP 里被忽略——“新特性≠能用”的又一例）；
- `manage_externals` 工具引入（管理物理子模块；本教材所用 tarball 树中未见该目录，各子模块已直接随包提供）。

---

## 2.3 WRF 4.8.0 相对 4.6/4.7 的新特性精讲

> 以下逐条来自官方 4.8.0 release notes（2026-06-08，含 PR 编号），并注明本书对接章节。这是读者“拿到手的第一天”最该知道的一节。

### 2.3.1 物理侧

| # | 新特性 | 要点 | 对接 |
|---|---|---|---|
| 1 | **动态闪电方案**（Lynn et al. 2012） | 预报“体积极电能量”的时间演化（prognostic LPI），`dyn_lightning_option=1`；含尺度感知的充电强度调整。本地树 `phys/module_ltng_lpi.F`（另有 strokes/iccg/pe/crmpr92/cpmpr92z 五个既有闪电诊断模块） | ch12 侧记 |
| 2 | **Shin-Hong PBL 新版并入 YSU** | 取代 bl_pbl_physics=11；新选项 shinhong_scu_mixing（云顶向下混合，默认关）、shinhong_nonlocal_flux（γ(f) 或质量通量，默认开）、shinhong_ke_dissipation（默认关）；代码移入 `phys/physics_mmm/`（本地 `bl_shinhong.F90`） | ch14 |
| 3 | **地形重力波拖曳更新**（gwd_opt=1） | 新增 gwd_dx_factor=2（有效格距）、gwd_if_nonhyd=.true.（非静力效应）；**需 WPS 配套更新提供地形场（WPS #281）** | ch14 侧记 |
| 4 | **尺度感知地形形状拖曳 kim_tofd** | 修订 MM5 面层内新增，默认关；同样需 WPS #281 的 var2 场 | ch14 侧记 |
| 5 | **Noah-MP v5.1.2** | 重构版耦合（4.7.1 为 v4.7）；新增若干选项 | ch16 |
| 6 | **SLUCM 城市自然解决方案（NbS）** | 城市地面植被与街道树木进入单层 UCM（依据 Huang/Wang/He 两篇在撰论文，PR #2272）→ 本地 `module_sf_urban.F` 已含树冠视角因子（kanda_kawai_svf）、树影（SHADOW_TREE）、气孔（STOMATAL）、叶面蒸散（LELEAF）、根系吸水（ROOT_UPTAKE）等子程序（ch17 精读过） | ch17/20 |
| 7 | **MYNN-EDMF 子模块更新**（对齐 NOAA Tech Note） | 次网格云 bl_mynn_cloudpdf=2 改进低云；下沉气流物理与尺度感知改进；稳定边界层低空急流调优（WFIP3）；人为气溶胶混合新开关 bl_mynn_mixaerosols/mixnumcon/mixscalars（官方建议配合 scalar_pblmix=0） | ch14/20（**本教材 L2 实战改的就是这一版**） |
| 8 | **MYNN 面层子模块化（MYNN-SFC）** | 新仓库 `NCAR/MYNN-SFC`，拆为 land/water/ice 三模块；新开关 sf_mynnsfc_sfcflux_land/water 取代含义混用的 iz0tlnd/isftcflx | ch14/16 |
| 9 | **社区火行为模式耦合**（Jimenez et al. 2024, GMD） | WRF-Fire 的火行为替换 | 不展开 |
| 10 | **Grell–Freitas→GFL 积云** | 跨 WRF/MPAS/CCPP 一致实现；气溶胶-对流交互改进、冷池参数化简化、下沉扩展的尺度感知 | ch15 |
| 11 | **TEMPO 微物理**（Thompson-Eidhammer Microphysics for Operations） | NCAR 仓库 v3.0.0；namelist `tempo_aerosolaware=1`/`tempo_hailaware=1`（默认均关）；需查表 ccn_activate.bin（已入 `run/`）。**注意：本教材所用 tarball 的 `phys/` 下没有 TEMPO 源文件**（顶层 Makefile 对 NoahMP/MYNN-EDMF/MYNN-SFC 是“缺失即退出”的硬检查，对 TEMPO 只是警告）——使用需单独拉取 | ch13 侧记 |

### 2.3.2 诊断与软件侧

- **CORDEX-WRF 诊断模块 v3**（Fita et al. 2019 GMD 的持续更新）：约 150 个诊断量、新 namelist 节 `&cdxwrf`、三个输出文件（auxhist19 主文件 / auxhist18 高频 / auxhist23 气压层插值）——**ch20 讲 CLWRF 诊断（T2MAX/T2MIN）时的“近亲”又多了一位**；
- 时间序列输出修复（solar_diagnostics 激活时第 55 个变量错位独立记录）；
- 软件层两个“critical bug fix”：① 内核未初始化值导致未定义行为（常见表现：**首次写 restart 时模式挂起**）；② 释放 data handle 未清空（常见表现：**读 auxinput 时突然崩溃**）——后者恰是 ch20 论文2 参数场 auxinput 通道的“前车之鉴”，做参数场实验前先确认基线版本含此修复（4.8.0 已含）。

---

## 2.4 WPS 4.7.0 同步与跨包依赖

- 本教材基线 **WPS 4.7.0**（2025-04-25 随 WRF 4.7.0 发布；本地源码 `source/WPSv4.7.0/README` 首行核验：*WRF Pre-Processing System Version 4.7.0*）；
- WPS 与 WRF 的**大版本同步发布**（4.4 notes 明确 *The WRF Pre-processing System (WPS) has been updated to Version 4.4*，其后各代同惯例），小版本（bug-fix）不一定跟进——选 WPS 4.7.0 配 WRF 4.8.0 是社区常见且可用的组合，本教材实测链路全通（ch06–08）；
- **已知跨包依赖（4.8.0 → WPS）**：gwd_opt=1 更新与 kim_tofd 需要 WPS #281 提供的额外地形场（var2）。本书个例不启用这两个选项，WPS 4.7.0 完全够用；若读者要用，请自行更新 WPS 到含 #281 的版本；
- ch17 用到的 GEOGRID.TBL 城市条目（URB_PARAM=132 维、FRC_URB2D、y2010/y2050_urb、ahe 数据集）在 WPS 4.7.0 的 `GEOGRID.TBL` 与 `/opt/app/wrf/WPS_GEOG` 中均可核（兰州个例的 URB_PARAM 全零问题见 ch19——那是数据覆盖问题，不是版本问题）。

---

## 2.5 本地源码指纹核验表

> “官方说有”不等于“我手里有”。下表把 §2.2–2.3 的关键陈述逐一落到本地源码树（`source/WRFv4.8.0/WRFV4.8.0/`），全部为写作时实测：

| 特性（版本） | 本地证据 | 核验结果 |
|---|---|---|
| 混合坐标默认（4.0） | `doc/README.hybrid_vert_coord`；namelist `hybrid_opt=2` 默认 | ✓ |
| NoahMP 独立 Registry（4.0） | `Registry/registry.noahmp` | ✓ |
| 闪电诊断家族 + 动态方案（4.8） | `phys/module_ltng_{lpi,strokes,iccg,pe,crmpr92,cpmpr92z}.F` | ✓ |
| MMM 共享物理库（4.6–4.7 移入） | `phys/physics_mmm/`：`bl_ysu.F90`、`bl_shinhong.F90`、`bl_mynn.F90`、`bl_gwdo.F90`、`cu_ntiedtke.F90`、`mp_wsm6.F90`、`mp_radar.F90`、`mynn_shared.F90` | ✓ |
| MYNN-EDMF 子模块（4.7） | `phys/MYNN-EDMF/`：`module_bl_mynnedmf.F90` + `WRF/`、`MPAS/`、`tests/` 子目录（同一方案跨 Dycore） | ✓ |
| MYNN-SFC 子模块（4.8） | `phys/MYNN-SFC/WRF/`：`module_sf_mynnsfc_common.F90`、`module_sf_mynnsfc_driver.F90`（land/water/ice 在编译期由符号链接装配，顶层 Makefile 有五件套硬检查） | ✓ |
| 子模块硬检查（4.4 起的构建新制） | 顶层 `Makefile`：NoahMP / MYNN-EDMF / MYNN-SFC 文件缺失 → `exit 31`；TEMPO 缺失 → 仅警告 | ✓ |
| TEMPO 随包状态 | 本 tarball `phys/` 下无 `module_mp_tempo_*.F90`（需另行拉取 NCAR/TEMPO） | ✓（未随包） |
| CMake 路线（4.6） | `cmake/`：`confcheck.cmake`、`wrf_case_setup.cmake` 等；`doc/README.cmake_build` | ✓ |
| LCZ 51–61（4.4.2） | `run/URBPARM_LCZ.TBL`；`VEGPARM.TBL`/`LANDUSE.TBL` 的 51–61 行 | ✓ |
| SLUCM 分布式参数（4.6） | `Registry.EM_COMMON` 的 `rconfig slucm_distributed_drag`、`distributed_ahe_opt`；`module_sf_urban.F` 消费 | ✓ |
| UCM NbS 城市树木（4.8） | `module_sf_urban.F` 内 `kanda_kawai_svf`/`SHADOW_TREE`/`STOMATAL`/`LELEAF`/`ROOT_UPTAKE` 等子程序 | ✓ |
| 风电场参数化（4.6 三新） | `phys/module_wind_fitch.F`（经典）+ `phys/module_wind_mav.F`（新家族） | ✓ |
| WPS 4.7.0 | `source/WPSv4.7.0/README` 首行版本串 | ✓ |

> **核验方法论**（比结论更值钱）：release notes 说的是“这个版本加入了什么”，本地树验证的是“我手里的包里真的有/没有什么”。两者对不上时优先怀疑**打包方式**（tar.gz 不含子模块/需单独拉取）而不是官方撒谎——TEMPO 与 manage_externals 就是两例。

---

## 2.6 版本口径对本书的三条影响

1. **物理方案号与选项表以 4.8.0 为准**：书中 mp/cu/pbl/sf 方案号表均按 4.8.0 源码与 README.namelist 核对（如 bl_pbl_physics=5 在 4.7 后只对应 MYNN-EDMF 子模块版，=6 已于 4.5 退出；bl_pbl_physics=11 在 4.8 被 Shin-Hong 新版取代）。**旧教程的方案号表若与本书冲突，先查对方基于哪个版本**；
2. **构建纪律来自 4.4 的子模块制**：ch05 的编译章会讲“顶层 Makefile 的三个 `exit 31`”——那是 4.4 起子模块化的产物；同样，`clean` 后需要 `arch/md_calls.inc` 回退（容器缺 m4 时），这类“构建环境考古”详见 ch05/ch20；
3. **本书两大实战直接受益于 4.6–4.8**：ch20 第一级改的 MYNN-EDMF 是 4.7 子模块化后的代码（`GET_PBLH` 的 θv 阈值）；第三级抄的开关式样是 4.6 的 `slucm_distributed_drag`。**“读新版史”不是科普，是给改造实验找官方样板。**

---

## 2.7 本章速查

1. 4.x 时间线：4.0（2018-06）→ 4.1（2019-04）→ 4.2（2020-04）→ 4.3（2021-05）→ 4.4（2022-04）→ 4.5（2023-04）→ 4.6（2024-05）→ 4.7（2025-04）→ **4.8（2026-06-08，本书基线）**；
2. 4.0 两大默认值：混合坐标默认（hybrid_opt=2）、湿位温默认（use_theta_m）——分别埋了 ch10 的坐标与 ch19 的“T 是扰动位温”两个坑；
3. 4.4 起 NoahMP 子模块化 → 4.7 MYNN-EDMF → 4.8 MYNN-SFC：物理“子模块化”三连，tar.gz 下载要选带版本号的包；
4. 4.6 共享物理库 `phys/physics_mmm/`（YSU/WSM6/NTiedtke/Shin-Hong/GWDO/修订 MM5）+ CMake 路线；
5. 4.8 五大新件：TEMPO（mp）、GFL（cu）、MYNN-SFC（sfc）、NoahMP v5.1.2、UCM 城市树木；外加动态闪电（dyn_lightning_option=1）与 CORDEX 诊断；
6. 查新特性：`github.com/wrf-model/WRF/releases`（各版带 PR 编号可回溯代码）；本地核验：本教材 §2.5 指纹表的方法论可复制到任何版本。

**延伸阅读**：各版 release notes 原文（GitHub Releases 页）；WRF 用户页 known-problems 清单；ch05（构建体系如何吃下这些特性）。