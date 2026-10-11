# ch14 素材底稿（边界层族）——写作时引用

> 生成 2026-10-10（自主会话）。书页换算：印刷页 N → book\page_{N+14:04d}.jpg。
> 物理范围：书 6.8 大气静力稳定度（印刷页 154–163，直读完成）；6.5 湍流混合（ch13 已述）；书第 8–9 章（湍流/边界层）课程范围外，仅延伸引用。6.9/6.10 留 ch15 与后文。
> PPT 未到 → 考点节自拟（待校准）。方案名单（方案 v2）：MYNN2.5 与 BouLac 双精读 + YSU 对照。

## 1. 书 6.8 公式与要点清单（p154–163，全部直读）

### 6.8 引言（p154）
- 静力稳定度（层结稳定度）定义：气块受动力/热力扰动后偏离平衡的垂直运动能否继续发展，取决于大气层结
- 气块法：微位移判据；三结局（继续发展=不稳定 / 回位=稳定 / 随遇平衡=中性）
- (6.8.1) dw/dt = −(1/ρ)∂p/∂z − g（垂直运动方程）；环境静力平衡 ∂pe/∂z = −ρe·g

### 稳定度判据（p155–156）
- (6.8.2) dw/dt = g(ρe−ρ)/ρ = B（**净阿基米德浮力** B）
- (6.8.3) dw/dt = g(Tv−Tve)/Tve（用虚温差）
- (6.8.4) dw/dt ≈ g(T−Te)/Te（近似式）
- (6.8.5) T−Te = (Γ−γ)dz（气块与环境温差的来源：减温率之差）
- (6.8.6) dw/dt = g(Γ−γ)/Te·dz
- (6.8.7)–(6.8.9) Γ>γ 绝对不稳定；Γ=γ 中性；Γ<γ 绝对稳定（图 6.16）
- (6.8.10)–(6.8.12) **三层判据**：Γ>γd 绝对不稳定；γd>Γ>γs 条件性不稳定；Γ<γs 绝对稳定（图 6.17）
- (6.8.13)–(6.8.15) **位温判据**：∂θ/∂z<0 绝对不稳定；∂θ/∂z>0 且 ∂θse/∂z<0 条件性不稳定；∂θse/∂z>0 绝对稳定（θsw 同为判据）
- 图 6.15 + 表 6.1：温湿参量保守性总表（θse、θsw 在干/饱和/等压/等压蒸发四类过程全保守 C）——与 ch13 保守性呼应
- 【附】大气层结与烟云扩散五型（图 6.18）：扇形/熏烟型/环链型/锥型/屋脊型（对应逆温、脱逆温、不稳定、中性、逆温抬升等层结）

### 6.8.2 条件性不稳定（p157–161）
- 热带到 15 km 平均条件性不稳定；厚气层需"有限位移"分析
- (6.8.16) ½w² − ½w0² = ΔEk = ∫ g(Tv−Tve)/Tve dz（浮力对单位质量空气做功 = 动能增量）
- (6.8.17) ΔEk = Rd·∫(Tv−Tve)d ln(p00/p)（埃玛图面积法，图 6.19：正面积 A+ / 负面积 A−）
- 条件性不稳定三类型（图 6.20）：(a) 潜在不稳定型（正负面积交替；A− → A+ 交点 = **LFC 自由对流高度**；第二交点 D 后减速）；(b) 绝对稳定型（全负）；(c) 绝对不稳定型（全正；夏季午后热雷雨型）
- (a) 细分：真潜不稳定（CAPE>A−）与假潜不稳定（CIN>CAPE，需强抬升）
- **CAPE（对流有效位能）= LFC 到 EL 的正面积；CIN（对流抑制能量）= 地面到 LFC 的负面积**（彭治班等 2001 引文）
- 热雷雨预报（图 6.21 热泡 Wood Ward 1960；图 6.22 晨探空 TveFGH）：定 CCL（低层等饱和比湿 q0 线与层结曲线交点）；从 CCL 沿干绝热线降到地面 = 当天可发生热对流的**下限温度 T**；云顶理论高度（正负面积相等处 N）

### 6.8.3 薄层法与夹卷讨论（p161–163）
- 气块法局限：真实上升气流必有环境补偿下沉（云外下沉速度约云内 25%–50%、范围 1–5 倍云半径）
- 图 6.23 薄层法模型；质量守恒 ρ1A1w1 = ρ2A2w2（ρ 近似相等 → A1w1 = A2w2；dz1/dz2 = w1/w2 = A2/A1）
- (6.8.18) dw/dt = (g/Tv0)[(Γ−γ1) − (γ2−Γ)A1/A2]dz1
- (6.8.19)(6.8.20) 判据（>0 不稳定 / =0 中性 / <0 稳定；可写成含 w2/w1 形式）
- (6.8.21) 饱和上行（γ1=γs）、干下沉（γ2=γd）：(Γ−γs)/(γd−Γ) ≷ A1/A2 = w2/w1
  - **解释：上升区相对面积小、上升速度大 → 层结趋于不稳定（少而强的积云有利发展）；积云数量多 → 趋于稳定**——"条件性不稳定大气中，积云密度自我调节"
- 薄层法为 Bjerknes (1938) 首提；因 A1/A2 难测，天气预报中少用（概念价值大）

## 2. 源码锚点笔记（第一轮精读，写作时扩充）

### 调用链（全部实测）
- `dyn_em/solve_em.F` → `CALL first_rk_step_part1`（L812）→ `CALL pbl_driver`（`dyn_em/module_first_rk_step_part1.F` L1164，BENCH_START(pbl_driver_tim)）
- 与微物理（solve_em 直调）不同：**PBL 在 RK 第一步（first_rk_step_part1）内调用**，每个时间步一次

### module_pbl_driver.F（分发结构）
- CASE 清单（按顺序）：BEPSCHEME(881)、BEP_BEMSCHEME(883)、MYJSFCSCHEME?(890)、TEMFPBLSCHEME(1184)、YSUSCHEME(1232)、SHINHONGSCHEME(1317)、MRFSCHEME(1386)、GFSSCHEME(1435)、MYJPBLSCHEME(1474)、QNSEPBLSCHEME(1549)、ACMPBLSCHEME(1619)、MYNNPBLSCHEME(1663)、EEPSSCHEME(1869)、KEPSSCHEME(1917)、BOULACSCHEME(1949)、CAMUWPBLSCHEME(1972)、GBMPBLSCHEME(2030)、SURFDRAGSCHEME(2064)、fitchscheme(2091)、mavscheme(2132)
- **BOULAC CASE 调用实录**（1953–1970）：FRC_URB2D/IDIFF/FLAG_BEP + BEP 双向数组（a_u_bep…b_e_bep、dlg_bep、dl_u_bep、sf_bep、vl_bep）+ TKE=tke_pbl、DLK=el_pbl、WU/WV/WT/WQ=wu_tur/wv_tur/wt_tur/wq_tur + EXCH_H/M + PBLH
- **MYNN CASE 调用实录**（1694 起）：mynnedmf_driver(initflag/restart/cycling, delt=dtbl, dz, dxc, znt, u/v/w, th, qv/qc/qi/qs, qnc/qni/QNWFA/QNIFA/QNBCA, p/exner/rho/T3D, 2D 地表场, Qke/qke_adv/Sh3d/Sm3d, Tsq/Qsq/Cov, RUBLTEN…, EXCH_H/M, pblh/KPBL, el_pbl, dqke, qWT/qSHEAR/qBUOY/qDISS, qc_bl/qi_bl/cldfra_bl, edmf_a/w/qt/thl/ent/qc, sub/det_thl3D…, maxwidth/maxmf/ztop_plume/maxmf_dd/maxtkeprod/cldtop_cooling/ent_eff, bl_mynn_* 选项组, spp_pbl, tke_budget)
- USE：`module_bl_ysu`、`module_bl_boulac`、`module_bl_mynnedmf_driver`

### YSU（对照方案）
- 双层：`phys/module_bl_ysu.F` 薄壳（`module module_bl_ysu; use bl_ysu`，保留 `subroutine ysu(...)` 老接口）→ `phys/physics_mmm/bl_ysu.F90` 实体（bl_ysu_init/finalize/run，CCPP arg_table 风格；`#define NEED_B4B_DURING_CCPP_TESTING`）
- YSU run 参数：u3d/v3d/t3d/qv3d…、p3d/p3di/pi3d、**br**（总体理查森数）、psim/psih、wstar/delta、u10/v10、**ysu_topdown_pblmix**、**ctopo/ctopo2（topo_wind 用）**、BEP 耦合数组

### MYNN-EDMF（精读主对象）
- **编译实体 = `phys/MYNN-EDMF/`（Makefile L460–466 符号链接实锤）**：`module_bl_mynnedmf.F90`（主体）+ `WRF/module_bl_mynnedmf_common.F90`（常数）+ `WRF/module_bl_mynnedmf_driver.F90`（驱动适配）；`phys/physics_mmm/bl_mynn.F90` 为 CCPP 副本（主编译不走）
- `module_bl_mynnedmf.F90` 头部（1–134）教材级素材：
  - 内容清单：mym_initialize（初始化，含 closure 常数）/ get_pblh / scale_aware（尺度自适应衰减）/ mym_condensation（诊断液水+云量）/ dmp_mf（非局地质量通量）/ ddmp_mf（下沉质量通量）/ mym_level2（Level-2 稳定度函数）/ mym_length（主混合长）/ mym_turbulence（扩散系数与生产项）/ mym_predict（湍流量预报）
  - 变量：tref（参考温度 300）、thl（液水位温）、qw（总水）、ql（液水）、vt/vq（浮力通量函数）、**qke = 2×TKE**、el（混合长）；**变量在格点中心、扩散系数与 el/sh/sm 在界面**
  - 参考文献 7 条（Nakanishi 2001/2004/2006/2009；Olson et al. 2019 NOAA TM 61；Puhales 2020；Olson et al. 2026 GSL-77）
  - **版本史 V1.0（WRFv3.0–3.4.1，HRRRv1）→ V4.0（WRFv4.0–4.4，HRRRv4）→ V5.0（WRFv4.5–4.7）→ V6.0（WRFv4.8/CCPP/MPAS；独立 submodule 仓库 github NCAR/MYNN-EDMF）**
- 主流程实测：单列循环内 call mym_condensation(L752) → ddmp_mf(L825) → mym_turbulence(L874) → mym_predict(L900)；另有 mym_initialize(L548)、mym_length(L1236)
- **boulac_length（L2026/L2186）注释原文**："taken from the BouLac scheme in WRF-ARW and modified for integration into the MYNN PBL scheme"——MYNN 的混合长采用 BouLac 思路（两方案亲缘关系的源码证据）
- 其它：get_pblh(L6047)、DMP_mf(L6197)、ddmp_mf(L7739)、SCALE_AWARE(L8287)、topdown_cloudrad(L8606)；Helfand & Labraga (1989) 稳定判据（L2376 注释）；Level 2.5/3.0 稳定性函数与 counter-gradient（mym_turbulence 内）
- common 常数（WRF/module_bl_mynnedmf_common.F90）：tref=300、TKmin=253（全水转换，Tripoli & Cotton 1981）、tice=238、tliq=269、ep_3=0.378、gtr=g/300、rk=cp/rd、tv0=0.608·tref、xlscp=(xlv+xlf)/cp、wfa_max=800e10/wfa_min=1e6（气溶胶上下限）；svp1/2/3 = 0.6112 kPa/17.67/29.65（Bolton 形式，与 ch11 SVP 家族同源）

### BouLac（精读主对象）
- `phys/module_bl_boulac.F`（直接模块，非薄壳）：Bougeault & Lacarrere 1989 (MWR 117, 1872–1890)；作者 Alberto Martilli（CIEMAT，2006）
- 常数：ck_b=0.4（扩散系数）、ceps_b=1/1.4（耗散）、vk=0.4（von Karman）、temin=1e-4（TKE 下限）；注释"**TKE IS NOT ADVECTED!!**"
- 单 subroutine boulac（列循环 → boulac1D）+ pbl_height 子程序
- 流程要点（列内）：u/v/th/q/qc/tke/rho/θ0/dz 装 1D →（BEP 时混合 dlg/dl_u/sf/vl）→ pbl_height → wstar=(g·wts·pblh/θ0)^{1/3}、t*=wts/w*
  → 方差：t2=1.8·(z/pblh)^{−2/3}·t*²、w2=1.8·(z/pblh)^{2/3}·(1−0.8·z/pblh)²·w*²
  → 逆梯度 gamma 三选：**igamma=1 Troen & Mahrt（默认）**/ 2 Deardorff & Therry-Lacarrere / 3 Holtslag & Moeng
  → boulac1D（TKE 方程 + 长度尺度 dlk/dls + 扩散系数 exch）
- 输出：exch_h/exch_m、wu/wv/wt/wq 湍流通量、dlk、pblh、TKE（tke_pbl）、el_pbl

### Registry × README
- Registry package（bl_pbl_physics==）：0 lesscheme；1 ysuscheme；2 myjpblscheme（state tke_pbl,el_pbl）；3 gfsscheme；4 qnsepblscheme（EDMF 状态量族）；**5 mynnpblscheme（scalar qke_adv；state qke,sh3d,sm3d,tsq,qsq,cov,cldfra_bl,qc_bl,qi_bl,el_pbl,tke_pbl）**；7 acmpbl；**8 boulacscheme（state el_pbl,tke_pbl,wu_tur,wv_tur,wt_tur,wq_tur）**；9 camuwpbl；10 temfpbl；11 shinhong；12 gbmpbl；16 eepsscheme；17 kepsscheme；99 mrfscheme
- README namelist：bl_pbl_physics 0–99 用户表（1 YSU/2 MYJ/3 混合 EDMF GFS/4 EDMF-QNSE/5 MYNN（配 sf_sfclay 1/2/5；**option 6 于 4.5 移除 → 由 bl_mynn_closure 控制**）/7 ACM2/8 BouLac/9 UW-CAM5/10 TEMF/11 Shin-Hong/12 GBM/16 TKE-ε/17 TKE-ε-TPE/99 MRF）
- 相关 namelist：bldt（调用间隔，分钟）；grav_settling；ysu_topdown_pblmix；mfshconv；topo_wind（仅 YSU）；**tke_budget（4.5 新，替换 bl_mynn_tkebudget）**；bl_mynn_closure（**2.5 / 2.6 默认 / 2.7 TTE / 3.0**）；bl_mynn_tkeadvect；icloud_bl（默认 1：MYNN 次网格云耦合辐射）；bl_mynn_cloudmix（默认 1）

## 3. 实验设计（轻轨，本地 python）

- E1 稳定度判据表（书习题 7 探空）：逐层 Γ、γd、γs、∂θ/∂z、∂θse/∂z → (6.8.10)–(6.8.15) 判定；图 ch14_stability.png（θ 与 θse 廓线 + 判定标注）
- E2 CAPE/CIN（浮力积分升级版）：地面气块（23℃/19℃）含虚温订正的浮力积分 → CAPE（正面积）、CIN（负面积）、LFC/EL；对读 ch13 近似值（+711/−1330 J/kg 未订正）；图 ch14_cape.png（气块路径 + 正负面积填色）
- E3 混合层 θ 守恒（模型剖面）：wrfinput/wrfrst 兰州柱 θ 剖面 + (6.5.6) 质量加权平均（分层计算）；图 ch14_mixed_layer.png
- E4 薄层法判据 (6.8.21) 数值演示：条件性不稳定层对 A1/A2（积云密度）的稳定度翻转扫描（表）
- 脚本：workspace/scripts/ch14_experiment.py；日志 workspace/logs/ch14_experiment.log

## 3b. 实验记录（ch14_experiment.py，2026-10-10 跑通）

- E1 判据表（书习题 7）：γd=9.77；逐层 Γ/γs/θ/θe/∂θ∂z/∂θe∂z 双判据列全出：
  - 1000–900（Γ=2.75）气块判据"绝对稳定"而 θe 判据"条件性不稳定"——**两判据在强湿度梯度层的差异案例，指向 6.9.2 对流性不稳定**（教材留伏笔）
  - 850–800（Γ=9.80）超绝热→绝对不稳定；900–850/800–700/700–600 条件性不稳定；600 hPa 以上全稳定（θe 增）
- E2 CAPE/CIN（虚温订正）：LCL 942.9 hPa；**LFC 807.7 hPa（z=1827 m）**；**EL 340.4 hPa（z=8491 m）**；**CAPE=815 J/kg、CIN=−128 J/kg**
  - 关键对照：ch13 未订正口径为 LFC 343.8 hPa/正 711/负 −1330 —— **虚温订正把 LFC 从 8 km 拉回 1.8 km、CIN 缩小一个量级**（云内外湿度差主导浮力）→ 教材 14.x 的实验重头
- E3 混合层：wrfinput（35.98N,103.73E，z0=2092 m）(6.5.6) 质量加权平均 θ：0–500 m 312.25 K、0–1000 m 313.21 K、0–2000 m 316.90 K；近地面 300 m ∂θ/∂z ∈ [−0.0069, +0.0020] K/m（清晨弱层结）
- E4 薄层法（(6.8.21)）：Γ=6.0、γs=4.2 → 比值 0.477；A1/A2<0.477 不稳定、>0.477 稳定——"少而强的积云有利发展"数值演示
- 图：doc/figs/ch14_stability.png、ch14_cape.png、ch14_mixed_layer.png

## 4. 考点自拟（PPT 未到）

- 名词：静力稳定度；绝 对不稳定/条件性不稳定/绝对稳定；净阿基米德浮力；不稳定能量；CAPE；CIN；LFC；对流凝结高度（CCL，ch13 已学）；对流温度；薄层法；补偿下沉
- 简答：气块法三假定与适用性；θ/θse 判据的推导与含义；三类条件性不稳定（潜力/真潜/假潜）；薄层法相对气块法的修正（(6.8.18)–(6.8.21) 的物理读解）；烟云五型与层结对应
- 计算：Γ vs γd/γs 判据计算；浮力加速度与 ΔEk 积分（面积法）；CAPE/CIN 估算；薄层法判据代数
- 模式视角：模式怎样在线判定 PBL 高度（θ 廓线/临界 Richardson 数）；TKE 预报方程（生产/耗散/输运）；为什么 PBL 每步调用而辐射按 radt；MYNN 的 qke=2TKE 与 el 混合长；BouLac 与 MYNN 的亲缘（boulac_length）

## 5. 待办核验

- YSU 常数与核心公式（brcr、wstar/delta、顶卷夹层）在 bl_ysu.F90 中的实测（写作时读）
- Boulac boulac1D 内 TKE 方程与 dlk/dls 长度公式（写作时读）
- get_pblh / SCALE_AWARE 细节（MYNN 的 PBLH 定义与尺度自适应衰减）
- 论文 2 对接点：BouLac + BEP 的耦合现状（driver 已见 BEP 双数组全链）；MYNN（论文2 备选）与 BEP 不兼容的说明要写清