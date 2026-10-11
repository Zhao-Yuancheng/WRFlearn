# ch17 素材底稿 — 城市冠层专章（SLUCM → BEP/BEM，对接论文2）

> 生成：2026-10-11 凌晨。写作 ch17《城市冠层专章》用。方案位置：§3.2 ch17（六段式 + "论文2 对接"节替代考点透视；4 节交付）。
> 说明：书前 6 章无城市考点（书第 10 章"非均匀下垫面"不在考核范围），本章为项目实战章。

## 1. 源码核验（全部本地实核）

### 1.1 分发与调用链
- `module_surface_driver.F`：两族方案的实参表里携带全部 urban 数组（tr_urb2d/tb_urb2d/tg_urb2d/tc_urb2d/qc_urb2d/uc_urb2d、xxxr/b/g/c_urb2d、cmcr_urb2d、tgr/tgrl、smr、flxhumr/b/g、tvg/tt/xxxvg/tvgl/smg/cmcg/flxhumvg/t、trl/tbl/tgl_urb3d、sh/lh/g/rn/ts_urb2d、frc_urb2d、utype_urb2d）+ BEP 参数（sf_urban_physics、urban_map_*、num_urban_hi、num_urban_ndm）
- **真正的城市方案入口在 `module_sf_noahdrv.F`**（Noah 驱动内，乡村通量算完后）：
  - `IF (SF_URBAN_PHYSICS == 1)` → `CALL urban(...)`（SLUCM；三处调用：lsm 主体、mosaic 分支等）
  - `IF (SF_URBAN_PHYSICS == 2)` → `CALL BEP_BEM(...)`（无 BEM 附加数组版：trb/tw1/tw2/tgb_urb4d、sfw1/2、sfr/sfg、a_*_bep/b_*_bep/dlg/dl_u/sf/vl、rl_up/rs_abs/emiss/grdflx）
  - `IF (SF_URBAN_PHYSICS == 3)` → `CALL BEP_BEM(...)`（带 BEM 附加：tlev/qlev_urb3d、tw1lev/tw2lev、tglev、tflev、sf_ac/lf_ac/cm_ac_urb3d、ep_pv/t_pv_urb3d、sfvent/lfvent、sfwin1/2、sfrv/lfrv/dgr/dg/lfr/lfg（绿屋顶）、drain 系）
  - `module_sf_clm.F` 也有自己的 `CALL urban`（CLM 路径）
- `module_physics_init.F`：`IF (SF_URBAN_PHYSICS==1/2/3)` → `CALL urban_param_init(DZR,DZB,DZG,num_soil_layers,sf_urban_physics,use_wudapt_lcz,...)` + `CALL urban_var_init(...)`；LCZ 一致性守卫：fatal "USING URBPARM_LCZ.TBL WITH OLD 3 URBAN CLASSES. SET USE_WUDAPT_LCZ=0"

### 1.2 SLUCM（`module_sf_urban.F`）
- 头注释参考文献：Kusaka & Kimura (2004) JAM 43; Kusaka & Kimura (2004) JMSJ 82; Kusaka et al. (2001) BLM 101（=原始 SLUCM）；历史：1999 Tsukuba LCM → 2001 WRF 移植 → 2005 F. Chen/M. Tewari → 2014 Jiachuan Yang → **2024/2025 Yuqi Huang & Chenghao Wang（urban-NbS：城市树木 + 绿屋顶 + 植被地面）**
- 主 `SUBROUTINE urban(LSOLAR, num_roof_layers, num_wall_layers, num_road_layers, DZR,DZB,DZG, UTYPE, TA,QA,UA,U1,V1,SSG,SSGD,SSGQ,LLG,RAIN,RHOO, ZA,DECLIN,COSZ,OMG,XLAT,DELT,ZNT, CHS,CHS2, TR,TB,TG,TC,QC,UC, TRL,TBL,TGL, XXXR,XXXB,XXXG,XXXC, TS,QS,SH,LH,LH_KINEMATIC, SW,ALB,LW,G,RN,PSIM,PSIH, GZ1OZ0, CMR_URB,CHR_URB,CMC_URB,CHC_URB, U10,V10,TH2,Q2,UST, mh_urb,stdh_urb,lf_urb, lp_urb,hgt_urb,frc_urb,lb_urb,zo_check, CMCR,TGR,TGRL,SMR,CMGR_URB,CHGR_URB,jmonth, DRELR,DRELB,DRELG, FLXHUMR/B/G, TVG,TT,XXXVG,TVGL,SMG,CMCG,FLXHUMVG,FLXHUMT, lf_urb_s, z0_urb, vegfrac_in )`
- 内部单位：CGS（CP=0.24 cal/g/K、EL=583 cal/g、SIG=8.17e-11 cal/cm²/min/K⁴、SIG_SI=5.67e-8）；TETENA=7.5/TETENB=237.3（Tetens）；SRATIO=0.75（直/总辐射比）
- 子程序群：`mos`（M-O 相似理论交换系数）、`louis79/louis82`、`multi_layer`（多层热传导：KM 层、G0/CAP/AKS/TSL/DZ/DELT→TSLEND）、`force_restore`（力-恢复法）、`bisection`（表皮温度二分求解：TSP,PS,S,EPS,RX,SIG,RHO,CP,CH,UA,QA,TA,EL,BET,AKS,TSL,DZ,TS）、`SFCDIF_URB`（面层交换 Kanda 修正：AKANDA_URBAN）、`read_param`（URBPARM 表读取）、`urban_param_init`（含 LCZ 分支）、`urban_var_init`（IVGTYP→UTYPE_URB2D：USGS 31/32/33 或 LCZ_1..11）、嵌入的 Noah 土壤链（DIREVAP/TRANSP/SMFLX/SRT/SSTEP/WDFCND/ROSR12/SHFLX/HRT/HSTEP/TBND/TDFCND —— 供城市植被/绿屋顶土壤柱用）、urban-NbS 群（kanda_kawai_svf 天空视角因子、SHADOW_TREE 树影、STOMATAL/LELEAF 叶片气孔/潜热、force_restore_tree、ROOT_UPTAKE 根系吸水、VF_TREE_ANALYTICAL 查表视角因子）
- 三种表面：R 屋顶 / B 墙 / G 路面；各自 T（TR/TB/TG，n 层 TRL/TBL/TGL）+ 内部量 XXXR/B/G（M-O）、CMCR/TGR/TGRL/SMR（路面下方水土，承 TDFCND/HCPCT 链）
- 路面/墙的 Ch：`CH_SCHEME`（1 M-O；2 Narita et al. 1997 经验式，推荐/默认）

### 1.3 BEP/BEM（`module_sf_bep_bem.F` + `module_sf_bem.F` + `module_bep_bem_helper.F`）
- **`module_bep_bem_helper.F` 实为 3 行小模块**（仅 `integer, save :: nurbm`）——方案 v2 原文以为它含街谷几何/TKE 项，**勘正**（几何/TKE 都在 `module_sf_bep_bem.F` 的 BEP1D/param 里）
- `module_sf_bep_bem.F`：`SUBROUTINE BEP_BEM`（入口，大实参表）→ 逐格 `BEP1D`（每城市格 1D 柱）；子程序：`param`（从 URBPARM 表值再装配：nzu/nz_um、dz_u 网格、bs/ws、ar 比、方向循环）、`interpol`（模式层→城市网格插值）、`averaging_temp`、`modif_rad`（街谷辐射修正）、`surf_temp`（地面/道路表面温度：二分/牛顿）、`roof_temp_veg`（绿屋顶多层）、`buildings`（建筑内/墙壁，含 BEM 调用）、`urban_meso`（城市网格→中尺度格网的通量与 a/b 隐式系数：a_u/a_v/a_t/a_e、b_u/b_v/b_t/b_ac/b_e/b_q、dlg/dl_u/sf/vl/rl_up/rs_abs/emiss/grdflx）、`interp_length`、`shadow_mas`/`shade_wall`（街谷阴影）、`long_rad`（nz_um×nz_um 墙-墙视角因子矩阵 fww + fwg/fgw/fsw/fws/fsg）、`short_rad_dd`（直射/散射遮蔽）、`gaussj`（高斯消元）、`soil_moist`/`soil_temp`/`soil_temp_veg`/`invert`
- 常量：`nbui_max=15`（建筑类型数上限，"must be <= nz_um"）；`nz_um=18`（城市网格最大层）；街谷几何三件套（NUMDIR 方向数、STREET_DIRECTION、STREET_WIDTH、BUILDING_WIDTH、HEIGHT_BIN/HPERCENT_BIN 高度分箱）——来自 URBPARM 的 "for BEP" 字段
- 城市网格：nz_u 由建筑高度/街宽自适应；z_u(nz_um) 高度层；roof_frac=FRC_URB2D·bs/(bs+ws)（实测表达式，bs 建筑宽 ws 街宽）
- `module_sf_bem.F`：`SUBROUTINE BEM(nzcanm,nlev,nhourday,dt,bw,bl,dzlev,nwal,nflo,nrof,ngrd, hswalout,gswal,hswinout,hsrof,lsrof,gsrof,hspv, latent,sigma, albwal,albwin,albrof, emrof,emwal,emwin, rswal,rlwal,rair,cp, rhoout,tout,humout,press, rs,swddif,rl, dzwal,cswal,kwal,pwin,cop,beta,sw_cond, timeon,timeoff,targtemp,gaptemp,targhum,gaphum, perflo, gr_frac_roof,pv_frac_roof,gr_flag, uout,vout, hsesf,hsequip,dzflo, csflo,kflo,dzgrd,csgrd,kgrd,dzrof,csrof,krof, tlev,shumlev,twal,twin,tflo,tgrd,trof, hsout,hlout,consump,eppv,tpv,hsvent,hlvent,hfgr, tr_av,tpv_print,sfpv,sfr_indoor)`
- BEM 子程序群：`hsfluxpv`（屋顶光伏）、`wall_gr`/`wall`/`wall_coeff`（1D 墙体热传导三对角系数）、`hsinsflux`/`int_rsrad`/`int_rlrad`（室内短/长波）、`algebra_short`/`algebra_long`（窗-墙辐射代数）、`fluxroo`（屋顶通量）、`phirat`/`phiequ`/`fluxeqocc`/`fluxvent`/`fluxcond`（占空比/设备/通风/传导）、`regtemp`（室内温度回归：swcond,nhourday,dt,Qb,hsroo→tlev）、`reghum`（室内湿度）、`air_cond`（空调：hsneed/hlneed→hsout/hlout/consump/cop）
- **BEM 模块级标量参数（论文2 改造地图的"室内侧"锚点，实测）**：`emins=0.9`（内墙发射率）、`albins=0.3`（内墙反照率）、`thickwin=0.006 m`（窗厚）、`cswin=2.268e6 J/m³K`（窗热容）、`temp_rat=0.001 K/s`（空调调温速率）、`hum_rat=1e-6 (kg/kg)/s`（调湿速率）、`effpv=0.19`（光伏效率，典型 0.10–0.15）
- BEM 的"逐类/逐层"参数（albrof/emrof/krof/csrof/dzrof、albwal/emwal/kwal/cswal/dzwal、dzflo/csflo/kflo、dzgrd/csgrd/kgrd、pwin/cop/beta/sw_cond/timeon/timeoff/targtemp/gaptemp/targhum/gaphum/perflo、gr_frac_roof/pv_frac_roof）——**BEM 目标改造对象：URBPARM 表值/标量 → 2D 场**
- 空调/日程：`phirat`（占用率 hourly 24）、`hsesf`/`hsequip`（显热/设备）、`perflo`（楼层人数）
- 兼容矩阵（README 原文）：`sf_urban_physics=2/3` "works only with YSU, MYJ and BouLac PBL"；源码实证：PBL 方案消费 a_*_bep/b_*_bep（module_bl_boulac.F 的 `flag_bep`+a_u_bep；module_bl_keps.F；module_bl_shinhong.F 亦收但不在 README 白名单）；BEP 侧 `b_q_bep` 仅 sf_urban_physics==3 置零初始化（noahdrv 实测）——BEM 才走水汽通道
- 相关 PBL：`module_bl_boulac.F`（boulac 实参含 frc_urb2d/flag_bep/a_u_bep…）、`module_bl_mynn` 不带（ch14 已核）

### 1.4 表与静态场链路
- `run/URBPARM.TBL`：首行注释"参数因城市而异，默认值对任何城市都不合适，用户应按城市适配"；USGS 段 3 类（Low-dens Res / Hi-dens Res / Commercial）；另有多段（MODIS/NLCD40/LCZ 段——URBPARM_LCZ.TBL 单独文件）
  - 关键字段实测：ZR=5.0/7.5/10.0 m；SIGMA_ZED=1/3/4 m；ROOF_WIDTH=ROAD_WIDTH=8.3/9.4/10 m；**AH=20/50/90 W/m²**；**ALH=20/25/40 W/m²**；AKANDA_URBAN=1.29；DDZR=DDZB=0.05×4；DDZG=0.05/0.25/0.50/0.75；BOUNDR/B/G=1（零通量）；CH_SCHEME=2（Narita）；TS_SCHEME=1（4 层）；**AHOPTION=0**；**AHDIUPRF（24 值，01h 起）=0.16 0.13 0.08 0.07 0.08 0.26 0.67 0.99 0.89 0.79 0.74 0.73 0.75 0.76 0.82 0.90 1.00 0.95 0.68 0.61 0.53 0.35 0.21 0.18**（峰值 17h=1.00，谷 04h=0.07）；ALHOPTION=0；ALHSEASON（MAM/JJA/SON/DJF）=0.43/1.00/0.54/0.40；ALHDIUPRF（48 半时值）；OASIS=1.0；IMP_SCHEME=1；PORIMP=0.45；DENGIMP=0.001/0.0002/0.001；IRI_SCHEME=0；GROPTION=0；FGR=0.0；DZGR=0.05/0.10/0.15/0.20（绿屋顶 4 层）；**FVG=0.2**；TREEOPTION=0；TTscheme=0
  - 表面物性（三类同值）：**CAPR=CAPB=1.0e6、CAPG=1.4e6 J/m³K；AKSR=AKSB=0.67、AKSG=0.4004 W/mK；ALBR=ALBB=ALBG=0.20；EPSR=EPSB=0.90、EPSG=0.95；Z0R=Z0G=0.01、Z0B=0.0001 m；TRLEND=TBLEND=TGLEND=293 K**
- `run/URBPARM_LCZ.TBL` 存在（WUDAPT 11 类）；`URBPARM_UZE.TBL`（城市分区/树）
- 数据链路（WPS `geogrid/GEOGRID.TBL` 实测条目）：
  - **URB_PARAM**（num_urb_params 维；priority1 NUDAPT44_1km；priority2 gloucp2020_30s）
  - **FRC_URB2D**（urbfrac_nlcd2011 / urbfrac_gaia2020_30s）
  - **IMPERV**（nlcd2011_imp_ll_9s / impfrac_gaia2020_30s）；**CANFRA**（nlcd2011_can_ll_9s）
  - **MH_URB2D**（y2010_urb/y2050_urb：slucm/urban_params/20XX/H_avg/）；**ZD_URB2D**（…/d/）；**Z0_URB2D**（…/z_0/）；**BUILD_AREA_FRACTION**（…/lambda_p/）；**LF_URB2D_S**（…/lambda_f/）；**AHE**（y2010_ahe/y2050_ahe：slucm/AHE_2010s/2_bytes/）
- Registry：`MH_URB2D` state（i01r，可从未 wrfinput 读入）、`FRC_URB2D`、`UTYPE_URB2D`；ch06 轮已录 URB_PARAM=132 参数维
- namelist（README 实测）：`sf_urban_physics=0/1/2/3`（**Noah/Noah-MP only**）；`num_urban_ndm=1(=2 BEP/BEM)`、`num_urban_ng=1(=10)`、`num_urban_nwr=1(=10)`、`num_urban_nz=1(=18)`、`num_urban_ngb=1(=10 BEM)`、`num_urban_nf=1(=10 BEM)`、`num_urban_nbui=1(=15 BEM)`；`use_wudapt_lcz=0/1`（LCZ 类 31–33 替换；数据 wudapt.org）；`slucm_distributed_drag=.false.`（**仅单层 =1；需 wrfinput 3 个额外 2D 场**：零平面位移/动量粗糙度/前沿面积——与 GEOGRID 的 MH/ZD/Z0/LF 数据集对应）；`distributed_ahe_opt=0/1/2`（AHE 数据：0 不用/1 加给第一层温度倾向/2 加给地表感热）

## 2. 论文2 对接要点（D:\WPSDisk\…\论文2方案_v2.0.md；要点来自 notes 2026-10-10 通读）
- 题：深度学习屋顶分割 + 观测标定参数场 → WRF-Urban BEP/BEM 改善兰州热浪期 UHI（JGR-A；2027-03 结项）
- 域：d01 9 km ~90² / d02 3 km ~112² / d03 1 km ~112²；物理：**sf_urban_physics=3（BEP+BEM）**、BouLac（首选）/MYJ、Thompson、RRTMG、Noah；d01 KF、d02/03 关积云；~50 层；dt 54 s（1:3:3）
- 实验矩阵：CTRL / EXP-LIT / CAL-STEEL 20 组（拉丁超立方 α/ε/d/λ）/ CAL-CONC 6 组 / EXP-CAL / SEN-AREA±20% / SEN-ALB±0.10 / NO-STEEL
- **BEM 改造 = module_sf_bem.F 标量→2D 场**（走 auxinput 读自定义字段；单点 sanity；patch 管理）；参数场管线：mask(tif)+Overture 足迹 → d03 逐格 FRC_URB2D / STEEL_FRAC / ROOF_*2D（α/ε/λ/ρ/c/d）
- 标定目标：W238 TG 日循环 0.4 / W240 室内温度 0.3 / 温差日较差 0.3 加权 RMSE；验证：TG、BEM 室内、CMA 站、MODIS/LST、49 点网
- 教材对接：ch17 §④"论文2 对接"节 + BEM 改造地图（chapter_map 落盘）；ch19 双跑（=0 vs =3）；ch20 三级实战第③级

## 3. 实验设计
### 3.1 轻轨（本机，ch17_experiment.py）
- E1 城市等效表面日循环（SLUCM 口径参数：ALB=0.20/EPS=0.90/CAPG=1.4e6/AKSG=0.4004）vs 乡村 loam（ch16 框架）：同强迫下 T_s、H、LE、G、Rn 对比；城市 = 不透水面（β→0）+ 多层路面柱 + AH(t)=AH×AHDIUPRF
- E2 人为热与"夜间热岛"：AH on/off 的 ΔT_s(t)；分离"白天储热-夜间放热"（G 的昼夜积分）与 AH 直接贡献；ALH 的潜热通道对照
- E3 URBPARM 敏感性：三类城市（Low/Hi/Commercial）的 AH/ALH/ZR/FVG/z0 表值与温度响应；AH 日剖面图（AHDIUPRF×AH：谷/峰）；绿屋顶/树木（FGR/TREEOPTION=0 默认）作为开关提示
- 图：ch17_urban_energy.png、ch17_ah_profile.png
### 3.2 集群（方案要求）
- 兰州个例 d02 开 SLUCM（=1）单点对比（为 ch19 的 =0 vs =3 双跑铺垫）：24 h A/B 双跑（sf_urban_physics=0 vs 1，其余同）；城市格点 T2/HFX/TSK 日循环与夜景对比
- 失败/受阻则记"预留"清单（同 ch12–ch16 口径）

## 4. 待复核/缺口
- SVF/Z0C/Z0HC/ZDC/R/RW/HGT 等表值未逐行读全（写作时按需补；已读字段足够支撑实验与正文）
- BEM 的 cop/pwin/beta/sw_cond 等表值来源（URBPARM 各段）只作"来源=表"叙述，不逐值展开
- 集群双跑结果（若执行）补入 verify_log 与本章实验节