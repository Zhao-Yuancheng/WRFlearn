# ch16 素材底稿 — 陆面过程族（书 4.2/4.3 + surface 驱动 + Noah）

> 生成：2026-10-11 凌晨。写作 ch16《陆面过程族》用。
> 书页换算：印刷页 N → `book\page_{N+14:04d}.jpg`。
> 方案 §2.3 规格：物理=书 4.2–4.3（大气质量垂直分布、海洋热力特性——海表/陆表作为下边界）+ 地表能量平衡 Rn=H+LE+G 的模式实现；源码=module_surface_driver 分发 + Noah 精读（module_sf_noahlsm.F 四层土壤/皮肤温度/roughness；module_sf_noahdrv.F）+ slab/px/CLM/Noah-MP 差异表 + sf_surface_physics 号表 + VEGPARM/SOILPARM.TBL；实验=SOILPARM 敏感性（为 ch17 下垫面定制打样）；验收=Noah 结构与能量平衡闭合核验 + TBL 与 geogrid 静态场链路讲清。

## 1. 书页直读记录

### 目录核验（`book\page_0008.jpg` 实读）
- 第四章 大气的分层和结构（p48）：4.1 大气分层 48（4.1.1 热力结构 49 / 4.1.2 化学成分 52 / 4.1.3 外大气层 53 / 4.1.4 电磁特性 53）；**4.2 大气质量及其垂直分布 55**；**4.3 大气的主要下边界——海洋 56**（4.3.1 海洋的物理特性 56 / 4.3.2 海流 57）；习题 59；参考文献 60；第五章 62 起
- 对应扫描页：4.3 = page_0070–0072；习题 = page_0073–0074；答案页（部分习题答案）第四章题 = 印刷 p545（page_0559）

### 表 4.1（印刷页 56 顶，page_0070 顶；ch10 已引，ch16 可再引"下边界视角"）
高度 11 km 以下 77.6%；30 km 98.8%；50 km 99.92%；90 km 99.999%（对应气压 226.4/11.97/0.8/1.8e-5 hPa）

### 4.3 大气的主要下边界面——海洋（印刷页 56–58；page_0070–0072）
- 全球海洋面积约 3.6×10⁸ km²（3.6 亿 km²），占地球表面总面积 71%，平均水深约 3800 m
- 大气水汽的主要来源=海洋表面蒸发，**特别是副热带海洋的蒸发**；海洋还是**最大的热源**，是气候变化的缓冲器和调节器；海流是低纬向高纬输送能量的重要工具；**全球均匀的洋面是气团形成的源地之一**
- 大气对海洋的影响：改变海水的流动；海洋对大气的影响：改变空气的温湿特性。大规模海气作用最引人注目的：**热带南太平洋与大气之间的厄尔尼诺南方涛动**
- 4.3.1 物理特性：
  - 海水含盐/钠等 80 多种元素；盐度平均约 3.47%；密度一般 1.0255–1.0285 t·m⁻³，**约为海面附近空气密度的 800 倍**
  - **海水总质量约为大气的 267 倍，比热容又比空气大 4 倍**；据估计，**海洋热容量是大气热容量的 3120 倍，海洋上层 3 m 厚海水的热容量就相当于整个大气的热容量**
  - 巨大热惯性 → 夏升温/冬降温缓慢得多；估计年变化只有几度；**海水温度的日变化不到 0.1 ℃** → 沿海产生特殊气象过程（如海陆风环流）
  - 垂直三层（图 4.6）：**季节变化层**（约 100 m，因风浪搅拌又称**上混合层**；中纬度春夏出现**季节性温度跃层**；太阳辐射能量 90% 被海面约 10 m 水层吸收→周日温度跃层）→ **主（温）跃层**（过渡层厚约 1000–1500 m，温/密/盐陡变；大洋热力结构重要组成，强度纬向/经向变化）→ **下均匀层**（温/密/盐垂直变化很小）
  - 水温随深度增加而降低（密度相反）：低纬海区比高纬高、温差达 30 ℃；热带/温带主跃层中水温迅速下降，1000 m→4–5 ℃、2000 m→2–3 ℃、3000 m→1–2 ℃；深层海水温度几乎不受表面水温和季节/纬度影响；**全球海洋平均温度约 3.5 ℃**，75% 海水温度在 0–6 ℃
  - 能量收支：大气能量来源=太阳辐射能；大气仅吸收太阳短波辐射的 20%；经大气吸收、散射和地面反射后，**50% 太阳辐射能到达地球表面**，大部分被海洋吸收；海水透明度适中→太阳辐射影响到相当深的水层，**海洋温度日变化达 15–20 m 深、年变化达 200–300 m 深**（对比土壤只有 ~0.1 m / 2–3 m，ch16 实验 E2 用）；海洋是**巨大的太阳能储库**，通过红外辐射、湍流输送感热和水汽蒸发潜热向大气输送能量；**大气的热源主要是地球表面（海洋和陆地），海洋是最重要的热源**
- 4.3.2 海流：海流（洋流）=海水以相对稳定速度沿一定途径的大规模流动；影响因素：盛行风、海水密度不均匀、地转偏向力、海底地形、海岸线轮廓和岛屿
  - 表层海流由**风对海面的摩擦作用**产生→**风海流**；北半球副热带高压下明显顺时针环流（南半球相反）；**海流速率比气流速率平均约小 2 个数量级**；海气相互作用中动能由大气向海洋输送
  - 低纬：北半球顺时针——大陆东岸低纬→中高纬**暖洋流**（黑潮、墨西哥湾暖流），大陆西岸中高纬→低纬**冷洋流**（加利福尼亚流、秘鲁海流）；中高纬：北半球逆时针（大陆东岸冷流如堪察加冷流、西岸暖流如阿拉斯加暖流），南半球西风盛行→**南极环极流**
  - **暖流区提供热量、对大气有加热作用；冷流区从大气获得热量**；墨西哥湾暖流分支（北大西洋漂流）使西北欧温和湿润、挪威高纬最暖且沿海冬季不结冰；黑潮使日本气候温和湿润，太平洋东西两岸温差约 10 ℃；**"如果没有海流输送热量和调节作用，极地和赤道间的温差将更大，地球上的大气运动与天气现象将会更加剧烈"**
  - 图 4.8 全球海平面平均气温分布：等温线不与纬线平行（地形/海陆/地表性质），大陆边缘等温线多与海岸平行；1 月北半球大陆寒冷、海洋温暖（西伯利亚东北部与格陵兰两个最冷中心），西欧/美洲西岸比同纬度亚洲东部/美洲东部高；7 月大陆比海洋热得多，15–35°N 有 >30 ℃ 高温带，撒哈拉最热接近 40 ℃；南半球等温线多与纬圈平行（辽阔海洋），1 月最暖中心在大陆；赤道附近年变化不显著

### 第四章习题（印刷页 59–60；page_0073–0074）
1. 支配地球大气中气体成分随高度分布的因素？地面上大气与 500 km 高空以上大气有何不同？
2. 地球具有哪些独特条件，使它成为太阳系中唯一存在生命的星球？
3. 已知地面 p=1000 hPa、t=10℃、td=5℃：(1) 求 q、Tv、ρ；(2) 温度/比湿不随高度变，求 850 hPa 等压面离地高度 Z(gpm)；(3) 850–1000 hPa 层比湿不随高度变化，底面积 1 m² 气柱中水汽总质量 m（kg·m⁻²），全部凝结为液态水落至地面则水层多厚（cm）？
4. 已知大气中氘的平均浓度 18 ppmv，计算大气中氘的总质量
5. 假设地面气压 1000 hPa、对流层顶 200 hPa，求对流层内单位截面积气柱质量，并估计对流层内空气质量占整个大气质量的百分数（g=9.78 m/s²）
- 答案（印刷 p545，page_0559 已读）：3.(1) 5.4 g/kg、284.08 K、1.23 kg·m⁻³；(2) 1351.4 gpm；(3) 8.3 kg·m⁻²、0.83 cm（提示：先求空气柱总质量）；4. 6.66×10¹⁰ t；5. 8179 kg·m⁻²、80%
- 参考文献 p60：NOAA 标准大气（1976）、王衍明《大气物理学》、王永生等、王明星、许绍祖、中国大百科全书（海洋科学卷 1987）、周秀骥等、Banks & Kockarts、Bolton 1980、Dutsch 1971、Houghton 1986、Iribarne & Cho 1980、Iribarne & Godson 1981、Lydolph 1985、Murray 1967、Peixoto & Oort 1992、Stolarski 1988、Wallace & Hobbs 1977

## 2. 源码素材（全部实测）

### 2.1 调用链与分发（phys/module_surface_driver.F，SUBROUTINE surface_driver）
- **一个 driver 装两族方案**：
  - `sfclay_select: SELECT CASE(sf_sfclay_physics)`（面层/相似理论）：1 SFCLAYREV（`module_sf_sfclayrev.F`）、2 MYJSFC、3 GFSSFC、4 QNSESFC、5 MYNNSFC、7 PXSFC、10 TEMFSFC、89 IDEALSCMSFC、91 SFCLAY（旧 MM5，`module_sf_sfclay.F`）；0=无
  - `sfc_select: SELECT CASE(sf_surface_physics)`（陆面）：1 SLAB（`module_sf_slab.F`）、2 LSM=**Noah**（`module_sf_noahdrv.F`→`lsm`→`module_sf_noahlsm.F`→`SFLX`）、3 RUC（`module_sf_ruclsm.F`）、4 Noah-MP（`module_sf_noahmpdrv.F`）、5 CLM4（`module_sf_clm.F`）、6 CTSM（`module_sf_ctsm.F`）、7 PX（`module_sf_pxlsm.F`）、8 SSiB（`module_sf_ssib.F`）；0=无
- 调用链：first_rk_step_part1 的 surface_driver（辐射之后、PBL 之前）
- **时间步**：Noah 以 **DTBL**（bldt 节拍）步进（surface_driver 内 CALL lsm 实参为 dtbl）；slab 同样用 dtbl（SFCEVP+=QFX*DTBL）
- **强迫高度**：`ZLVL = 0.5*DZ8W(i,1,j)`（最低模式层的层中高度）——Noah 的大气强迫取在最低层中点
- 城市接口（ch17）：sf_urban_physics=1/2/3 → `module_sf_urban` / BEP / BEM；module_physics_init.F 的 LSMSCHEME 分支内调 `urban_param_init`+`urban_var_init`；NLCD40 输入时 IVGTYP 23/25→24（城市类合并）
- 融冰：`ICE==-1`（glacial）分支调 `SFLX_GLACIAL`（`module_sf_noahlsm_glacial_only.F`）；`ICE==0` 常规 SFLX
- Registry sf_sfclay 包：0 无/1 sfclayrev/2 myjsfc(tke_pbl,u10e,v10e)/3 gfs/4 qnse/5 mynnsfc/7 px/10 temf(wm_temf)/89 ideal/91 sfclay
- README sf_surface_physics：0 无/1 热扩散/2 统一 Noah/3 RUC/4 Noah-MP/5 CLM4/6 CTSM/7 PX/8 SSiB；**sf_urban_physics=1 SLUCM/2 BEP/3 BEM（BEP/BEM 仅 YSU/MYJ/BouLac PBL）**；num_urban_* 参数（ndm/ng/nwr/nz/ngb/nf/nbui 缺省 1，激活时 2/10/10/18/10/10/15）

### 2.2 Noah 精读要点
- **文件三层**：`module_sf_noahdrv.F`（WRF 驱动层：`lsm`、`LSMINIT`、`lsm_mosaic`、`SOIL_VEG_GEN_PARM` 读表）→ `module_sf_noahlsm.F`（物理层：`SFLX` 主控 + 30 个子程序）→ 表文件
- **SFLX 主控流程**（实测行序）：参数组装 REDPRM → 雪状态（SNOW_NEW/CSNOW/SNFRAC）→ 反照率发射率 ALCALC → 土壤热传导 TDFCND → 雪面粗糙度 SNOWZ0 → **PENMAN 算潜在蒸发 ETP** → 分叉 NOPAC（无雪）/SNOPAC（有雪）
- **NOPAC 内的收支链**：EVAPO（蒸发划分：EDIR 裸土直接蒸发/EC 冠层蒸发/ET1 逐层蒸腾）→ SMFLX（土壤湿度：SRT+SSTEP 三对角隐式，Kalnay & Kanamitsu 1988 "time scheme F" 双调用防 2ΔT 振荡；RUNOFF1/2/3 与 DRIP）→ **BETA = ETA/ETP**（蒸发比）→ TDFCND 得 DF1 → **城市特例 DF1=3.24** → DF1*=EXP(SBETA*SHDFAC)（植被削减因子，SBETA=−2.0）→ **皮肤温度线性化解**：`YYNUM=FDOWN−EMISSI·σ·T24`；`YY=SFCTMP+(YYNUM/RCH+TH2−SFCTMP−BETA·EPSCA)/RR`；`ZZ1=DF1/(−0.5·ZSOIL(1)·RCH·RR)+1` → SHFLX（HRT 右端项 + HSTEP 隐式步 → STC 更新；**T1=(YY+(ZZ1−1)·STC(1))/ZZ1；SSOIL=DF1·(STC(1)−T1)/(0.5·ZSOIL(1))**）→ FLX1=CPH2O·PRCP·(T1−SFCTMP)（雨水热通量）、FLX2（冻雨）、FLX3（雪面）
- **PENMAN**（实测）：RCH=ρ·cp·CH；RR=EMISSI·T24·6.48e-8/(SFCPRS·CH)+1+(降水潜热项)；FNET=FDOWN−EMISSI·σ·T24−SSOIL；RAD=FNET/RCH+TH2−SFCTMP；A=ELCP1·(Q2SAT−Q2)；**EPSCA=(A·RR+RAD·Δ)/(Δ+RR)**；**ETP=EPSCA·RCH/LVS**；冻雨 FLX2=−LSUBF·PRCP
- **TDFCND**（热传导，Peters-Lidard et al. 1998，改自 Johansen 1975）：THKQTZ=7.7、THKO=2.0、THKW=0.57、THKICE=2.2 W/m/K；THKS=7.7^QZ·2.0^(1−QZ)；THKSAT=THKS^(1−SMCMAX)·THKICE^(SMCMAX−XU)·THKW^XU；GAMMD=(1−SMCMAX)·2700（干密度 kg/m³）；THKDRY=(0.135·GAMMD+64.7)/(2700−0.947·GAMMD)；Kersten 数（frozen/unfrozen）→ 最终 DF（OPT_THCND：1=Johansen/P-L，2=对 silt loam/sandy loam 用 McCumber & Pielke）
- **SMFLX**（实测）：冠层水 RHSCT=SHDFAC·PRCP1−EC；EXCESS>CMCMAX→DRIP；PCPDRP=(1−SHDFAC)·PRCP1+DRIP/DT；SICE=SMC−SH2O；SRT/SSTEP 三对角；FAC2/FLIMIT 稳定性约束
- **土壤层结构**（share/module_soil_pre.F 的 `init_soil_depth_2`，Noah/Noah-MP 专用）：**DZS=(0.1, 0.3, 0.6, 1.0) m**，ZS（层中）=0.05/0.25/0.70/1.50 m，总深 2.0 m；非 4 层报致命错误" The Noah and NoahMP LSMs use 4 layers"
  - 对照：init_soil_depth_1（slab，5 层，0.01 倍增：0.01/0.02/0.04/0.08/0.16）；_3（RUC，6/9 层界面 zs=0/0.05/0.2/0.4/1.6/3.0 或 0/0.01/0.04/0.1/0.3/0.6/1.0/1.6/3.0）；_7（PX，2 层 0.01/0.99）；_8（SSiB，0.05/1.00）
- **LSMINIT**（module_sf_noahdrv.F）：SNOALB=MAXALB(IVGTYP)·0.01（未用 rdmaxalb 时）；**SH2O 初始化**：TSLB<273.149 K 时用 Koren et al. 1999 显式首猜 + `FRH2O` 迭代解（液态水含量）；否则 SH2O=SMOIS；ISLTYP<1 报致命错误；雪高初始化
- **REDPRM**（参数组装，实测）：
  - SOILPARM 字段（按序）：BB、DRYSMC、F11、MAXSMC、REFSMC、SATPSI、SATDK、SATDW、WLTSMC、QTZ（+ BEP/MP 扩展列 BVIC/AXAJ/BXAJ/XXAJ/BDVIC/BBVIC/GDVIC）
  - 派生关系（源码注释）：SATDW=BB·SATDK·(SATPSI/MAXSMC)；F11=log10(SATPSI)+BB·log10(MAXSMC)+2；REFSMC1=MAXSMC·(5.79e-9/SATDK)^(1/(2BB+3))（5.79e-9 m/s=0.5 mm/d 通量）：REFSMC=REFSMC1+(1/3)(MAXSMC−REFSMC1)；WLTSMC1=MAXSMC·(200/SATPSI)^(−1/BB)、WLTSMC=WLTSMC1−0.5·WLTSMC1（Wetzel & Chang）
  - GENPARM：SLOPE_DATA(9 类) / SBETA=−2.0 / FXEXP=2.0 / CSOIL=2.0e6 J·m⁻³·K⁻¹ / SALP=2.6 / REFDK=2.0e-6 / REFKDT=3.0 / FRZK=0.15 / ZBOT=−8.0 / CZIL=0.1 / SMLOW=0.5 / SMHIGH=3.0 / LVCOEF=0.5
  - 派生：**KDT=REFKDT·DKSAT/REFDK**（入渗参数按土壤类型缩放）；SLOPE=SLOPE_DATA(SLOPETYP)（Zobler 坡度类 1:0–8%、2:8–30%、3:>30%…）；**FRZFACT=(SMCMAX/SMCREF)·(0.412/0.468)**；TOPT=298 K；CMCMAX=0.5e-3 m；RSMAX=5000 s/m；BARE=19、NATURAL=5、CROP=3（USGS 类号）
  - SLOPETYP 定义（源码注释）：1 0–8%；2 8–30%；3 >30%；4 0–30%；5 0–8 & >30；6 8–30 & >30；7 全；9 冰川；空=海
- **SOILPARM.TBL**（run/，两节：STAS 与 STAS-RUC；Noah 用 STAS，19 类）：代表性数值——SAND(1): BB=2.79、DRYSMC=0.010、MAXSMC=0.339、REFSMC=0.192、SATPSI=0.069、SATDK=4.66e-5、WLTSMC=0.010、QTZ=0.92；LOAM(6): 5.25/0.066/0.439/0.329/0.355/3.38e-6/0.066/0.40；CLAY(12): **11.55**/0.138/0.468/0.412/0.468/9.74e-7/0.138/0.25；WATER(14): MAXSMC=1.0、SATPSI=0、SATDK=0；ORGANIC(13): 5.25…、QTZ=0.05；BEDROCK(15): MAXSMC=0.20、SATDK=1.41e-4
  - 读表逻辑：头两行→分类名（MMINSL，如 STAS）；第 3 行 SLCATS,IINDEX；逐类读 10（+7）字段；分类不匹配→致命错误；wrf_dm_bcast 广播到各进程
- **VEGPARM.TBL**（run/，USGS 27 类）：字段 SHDFAC、NROOT、RS、RGL、HS、SNUP、MAXALB、LAIMIN、LAIMAX、EMISSMIN、EMISSMAX、ALBEDOMIN、ALBEDOMAX、Z0MIN、Z0MAX、ZTOPV、ZBOTV；代表值——Urban(1): SHDFAC=0.10、NROOT=1、RS=200、MAXALB=46、Z0=0.50；Grassland(7): SHDFAC=0.80、RS=40、Z0=0.10–0.12；Shrubland(8): Z0=0.01–0.05；Savanna(10): Z0=0.15；Evergreen Needleleaf(14): LAIMAX=6.40、Z0=0.50、ZTOPV=17；**Water(16): SHDFAC=0、NROOT=0、RS=100、MAXALB=70、ALBEDO=0.08、Z0=0.0001**；Barren(19): RS=999、ALBEDO=0.38、MAXALB=75；Snow/Ice(24): NROOT=1、RS=999、MAXALB=82、ALBEDO=0.55–0.70、Z0=0.001；Lava(26)/White Sand(27): RS=999
  - 尾部数据块：TOPT_DATA=298.0、CMCMAX_DATA=0.5E-3、CFACTR_DATA=0.5、RSMAX_DATA=5000.0、BARE=19、NATURAL=5、CROP=3、**LCZ_1…LCZ_11 = 51…61**（WUDAPT 局地气候区，ch17）
  - 读表逻辑（SOIL_VEG_GEN_PARM）：按 LANDUSEC（USGS/MODIS/NLCD40）选节；低/高密度居住区与工业类必须存在（NLCD40 新表需求，旧表报错）

### 2.3 geogrid→real→Noah 静态场链路（讲清"TBL 与 geogrid 链路"）
- WPS `geogrid/GEOGRID.TBL`（实测条目）：
  - `LANDUSEF`（land_cat 分类）→ **dominant = LU_INDEX**（Noah 的 IVGTYP）
  - `SOILCTOP`（soil_cat 分类）→ **dominant = SCT_DOM**（Noah 的 ISLTYP 顶层）；SOILCBOT→SCB_DOM
  - `SOILTEMP`（连续，masked=water，fill_missing=0）→ TMN（年均深层土壤温度）
  - `GREENFRAC`（连续）→ VEGFRA（植被覆盖度）；`LAI12M`（连续）→ 月 LAI（rdlai2d=.true. 时用）
- real.exe 侧：`share/module_soil_pre.F` 完成 WPS 土层→模式 4 层插值（init_soil_depth_2 定 DZS；init_soil_2_real 等建 TSLB/SMOIS）；wrfinput 携带 ZS/DZS（Registry state，流 Z）
- namelist 联动：num_soil_layers（README 默认 5，**Noah 必须设 4**）；surface_input_source=3；num_land_cat=21（USGS 24→实际类别数依数据）；default_soiltype=8（缺省 silty clay loam 填海陆不明处）；sst_update/auxinput4（wrflowinp 时变 SST，配 usemonalb）；usemonalb（月反照率）；rdmaxalb（雪反照率来自 geogrid）；rdlai2d；ifsnow；sf_surface_mosaic/mosaic_cat=3；sst_skin；lagday=150（TMN 由 150 天皮肤温度平均更新）；sf_surf_irr_scheme（1 渠道/2 滴灌，仅 Noah）；opt_thcnd（1 Johansen；2 McCumber/Pielke）；default_soiltype

### 2.4 差异表素材（sf_surface_physics 0–8）
| # | 方案 | 土壤层 | 湿度过程 | 雪 | 备注 |
|---|---|---|---|---|---|
| 0 | 无 | — | 无 | — | 无地表温度预报 |
| 1 | SLAB 热扩散 | 5（0.01 倍增） | 无（固定湿度） | 简单 | `module_sf_slab.F`；仅温度扩散 |
| 2 | **Noah** | **4（0.1/0.3/0.6/1.0 m）** | 有（SMC/SH2O，冻土 FRH2O） | 显式雪层（SNOPAC） | 本章主角；TBL 三件套 |
| 3 | RUC | 6 或 9 | 有（多层）+ 次网格 | 多层雪 | 需 flag_sm_adj 等 |
| 4 | Noah-MP | 4（可配） | 多物理选项（含地下水、动态植被） | 多层 | `&noah_mp` namelist |
| 5 | CLM4 | ~10 | 完整陆面过程 | 多层 | 来自 CAM |
| 6 | CTSM | ~ | 完整 | 多层 | 见 doc/README.CTSM |
| 7 | PX | 2（0.01/0.99） | 有+间接 nudging | 简单 | 需配 PX 面层 |
| 8 | SSiB | 2（0.05/1.00） | 有 | 简单 | 需 Dudhia/RRTM/CAM/RRTMG |

### 2.5 书与源码的对照点（写作骨架）
| 书 | 代码 |
|---|---|
| 海洋热容量 3120×大气、日变化<0.1℃、日变化深 15–20 m | 水点走 ISLTYP=14（WATER：MAXSMC=1.0、SATPSI=SATDK=0）；SST 由 sst_update/auxinput4 或 slab 预设；E2 实验对比阻尼深度 |
| 地表能量平衡（Sky 辐射驱动的下边界） | FDOWN（净短波+净长波）→ PENMAN/EPMAN；Rn=H+LE+G 由 SSOIL/ETA/SHEAT 收口（BETA 蒸发比） |
| 土壤热传导（第 16 章新增；书未展开） | TDFCND（P-L 1998）+ HRT/HSTEP 隐式三对角 |
| 辐射逆温（6.10）的陆面侧 | 夜间 Rn<0 → SSOIL 向土壤放热、T1 降；SMFLX/DEVAP 关断 → BETA→0 |
| 图 4.8 海陆温差 | 同一强迫下"海洋 vs 土壤"的阻尼深度差（E2） |
| 过量降水/径流（非书） | SMFLX：RUNOFF1 超渗、RUNOFF2 基流、RUNOFF3 深层 |

## 3. 实验（轻轨）设计（待写脚本 ch16_experiment.py）
- E1 地表能量平衡日循环：理想化太阳角日循环 + 简单陆面（表皮温度线性化解，仿 Noah 的 YY/ZZ1）+ 土壤四层热传导；输出 Rn/H/LE/G 与 T1/Ts、BETA 日变化；核验 Rn≈H+LE+G 闭合
- E2 土壤热传导阻尼深度：一维热扩散数值解（正弦强迫）→ 阻尼深度 D=√(2κ/ω)；日循环 vs 年循环；土壤（κ≈4e-7 m²/s → D≈0.1 m / ~2 m）vs 海洋（有效 κ 更大 → 日 15–20 m / 年 200–300 m，书 4.3）；相位滞后
- E3 SOILPARM 敏感性：读实际 SOILPARM.TBL，比较 沙/壤/黏土 的 BB/MAXSMC/SATPSI/SATDK/WLTSMC；用简化公式展示对蒸发（BETA）与土壤湿度记忆的影响（为 ch17 下垫面参数定制打样）
- 图：ch16_energy_balance.png、ch16_soil_diffusion.png、ch16_soilparam.png

## 4. 待复核/缺口
- Noah 的 TBOT/ZBOT 语义（TBOT 来自 wrfinput 的 TMN？ZBOT=−8℃ 深部参考）写作时以 SFLX 实参名（TBOT："bottom soil temperature"）+ 源码注释为准，别过度解释
- OPT_THCND 选项 2 的细节（对 soil type 3/4 用 McCumber-Pielke）在 TDFCND 内分支，写作时核对
- RUC/CLM/CTSM 的层数只作差异表用，不再深读
- SST 路径（sst_update + auxinput4 + sst_skin）与 slab 海温预设的差异，写作时用 README 原文口径