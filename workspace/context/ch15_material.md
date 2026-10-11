# ch15 素材底稿 — 积云参数化族（书 6.9/6.10 + 源码 + 答案页）

> 生成：2026-10-10 夜（自主会话）。写作 ch15《积云参数化族》用。
> 书页换算：印刷页 N → `book\page_{N+14:04d}.jpg`。

## 0. 章节定位

- 承接：ch14 E1（1000–900 hPa 层"气块判据绝对稳定 vs θe 判据条件性不稳定"，∂θe/∂z=−7.11 K/km）与 14.3"积云密度自调节"（薄层法 0.477 判据）
- 物理底：书 6.9 整层气层升降时稳定度的变化（6.9.1 未饱和/下沉逆温；6.9.2 对流性不稳定）+ 6.10 逆温层 + 6.8.2 夹卷结尾
- 源码：分发链（cumulus_driver）→ New Tiedtke（16）精读 → KFeta（1）对照 → 浅对流独立驱动（shcu_physics）
- 答案页：印刷 p546（page_0560）第六章习题答案，实验可对照

## 1. 书页直读记录

### 6.8.2 夹卷结尾（p164 顶部，page_0178）
- 图 6.25 薄层法判据中的条件不稳定型与条件稳定型（(a)(b) 两联图）
- 图 6.26 夹卷作用对积云温度及云底、云顶的影响（埃玛图，含假绝热线/云内温度变化曲线/温度层结曲线/LCL）
- 夹卷两类：
  - **湍流夹卷**：通过云顶和侧边界，云内外热量、动量、水分和质量的湍流交换
  - **动力夹卷**：云内气流加速上升 → 质量连续性 → 四周空气流入云中补偿
- 飞机观测：淡积云和中积云**下部**动力夹卷与湍流夹卷强度相当；**中上部以湍流夹卷为主**
- "这些过程的严谨讨论已有多种云雾数值模式（参见后面第十三章）"（书第十三章=积云动力学与云模式 → ch15 延伸）
- ⚠ 接口：6.8.2 的条件性不稳定 + 真潜/假潜（ch14 已解）→ 6.9.2 的"整层抬升型"不稳定是另一家族

### 6.9 整层气层升降时稳定度的变化（p164–166，page_0178–0180）
开篇设定（p164）：大范围升降运动，水平范围几百千米，持续几小时到几天，垂直升降速度 cm/s 量级，由天气系统引起；讨论假设：**绝热、总质量不变、无湍流混合、气层内各部分相对位置不变**。

**6.9.1 未饱和情况及下沉逆温**
- 图 6.27 未饱和气层的下降（p165）：p1→p2、厚度 Δz1/Δz2、面积 A1/A2、密度 ρ1/ρ2
- 质量守恒：ρ1A1Δz1 = ρ2A2Δz2
- (6.9.1) Δz1/Δz2 = ρ2A2/(ρ1A1) = p2A2Tv1/(p1A1Tv2)
- 位温上下界差守恒：(∂θ/∂z)1Δz1 = (∂θ/∂z)2Δz2
- (6.9.2) (∂θ/∂z)2 = (∂θ/∂z)1·(p2A2Tv1)/(p1A1Tv2)
- (6.9.3) Γv2 = γd − (γd−Γv1)(p2A2)/(p1A1)，即 Γv2 = Γv1 + (γd−Γv1)(1 − p2A2/(p1A1))；Γv1 为初始垂直减温率
- 讨论：
  - (1) Γv1<γd 为常态；决定升降中减温率变化的是 1 − p2A2/(p1A1)
  - 下沉＋水平辐散（p2A2>p1A1）→ Γv2<Γv1 → 趋于稳定，甚至 Γv2<0 成逆温（例 6.2）
  - 抬升＋水平辐合（图 6.27 相反，p2A2<p1A1）→ Γv2>Γv1 → 稳定性减小
  - p2/p1 与 A2/A1 变化相反 → 作用抵消，需具体分析
  - 大尺度气旋/反气旋（北半球）：气旋环流逆时针、气流向内向上辐合 → 上升 → 稳定性变小；反气旋顺时针、下沉压缩增温 → 甚至逆温 → 稳定晴朗
  - (2) Γv1=γd → Γv2=γd（升降保持干绝热率）
  - (3) Γv1>γd → 结论相反；绝对不稳定气层实际很少见
- **例题 6.2**（p166）：330–300 hPa 未饱和气层，底部 −49℃、顶部 −51℃。
  - 解：高空湿度小，不作虚温订正；逆温即 Γ2<0，由 (6.9.3) 必有 **p2 > [γd/(γd−Γ1)]·(A1/A2)·p1**（(6.9.4)）
  - Γ1 ≈ 0.0032 K/m（T̄1=223 K、p1=315 hPa、ΔT1=−2 K、Δp1=−30 hPa）
  - (1) 无辐散 A1/A2=1 → p2 > 467.7 hPa 才出现逆温
  - (2) 辐散后面积增 20% → p2 > 390 hPa 即出现逆温
  - 核对：γd/(γd−Γ1) = 0.0098/0.0066 = 1.4848 → ×315 = 467.7 ✓；×0.8333 → 389.8 ✓

**6.9.2 对流性不稳定（位势不稳定）**（p166）
- 图 6.28 整层气层抬升时稳定度的变化：(a) 对流性不稳定（下湿上干：下部先饱和、饱和后沿假绝热上升，层结曲线 A1B1→A2B2，Γ 变得大于 γs → 不稳定层结）；(b) 对流性稳定（上湿下干：上部先饱和，Γ 变小甚至逆温 → 更稳定）
- 大气水汽源于地表 → 常为低层湿、高层干 → 大范围抬升时下部先饱和（第一种情况）
- 定义：原稳定的未饱和气层，由于整层被抬升到一定高度以上而变为不稳定 → **对流性不稳定或位势不稳定**；反之为对流性稳定
- 气层是否对流性不稳定，不仅和温度层结有关，还取决于湿度条件，特别是低层水汽状况
- 判据（6.7.3 假相当位温 + 6.3.2）：下部 θse 比上部高 → 对流性不稳定；**判据 (6.9.5)**：∂θse/∂z ＞0 对流性稳定；=0 中性；＜0 对流性不稳定（假湿球位温同样可用）
- p167（page_0181）：对流性稳定气层整层抬升 → 层状云；对流性不稳定 → 积状云（对流云），甚至对流性降水
- 观测：最可能产生强对流的 = 低层暖湿、高层干燥、具有条件性不稳定层结、T/Td 曲线呈"喇叭口"形状
- "潜在不稳定"：气层本身稳定时，需外加抬升力作为"触发机制"，潜在不稳定才转化为真实不稳定；对流性不稳定的实现要求大范围抬升（天气系统如锋面配合或大地形）→ 对流性天气强烈、范围大；6.8.2 的条件性不稳定只需局地热对流或动力因子 → 局地雷雨
- 全球结论（据图 6.2）：① 对流层平均位温随高度增加（∂θ/∂z>0）→ 干空气/未饱和湿空气平均状态稳定（不排除局地不稳定）；② 热带对流层中低层（约 700 hPa 以下）存在相当位温梯度的**负值区** → 该处大气经常处于条件性/对流性不稳定状态
  - ⚠ 扫描页括注符号待复核（见 §4）

### 6.10 逆温层（p167–168，page_0181–0182）
- 定义：Γ<0（温度随高度增加）→ 绝对稳定层结；对上下空气对流起削弱抑制作用
- 低空逆温像"盖子"：烟尘、杂质、有害气体难以穿过 → 空气质量下降、能见度恶化 → 也称**阻塞层**；伦敦烟雾、光化学烟雾等严重污染事件与其有关
- 图 6.29 晴天低层大气和土壤表层温度廓线日变化（Eagleman 1985）：白天辐射增温→低层递减率大；夜间辐射降温→逆温；厚度几米到几百米，凌晨最强、日出后消失；**最有利于形成逆温的是晴朗无风的夜晚**（无云利于地面辐射向上发散，无风使上层热量难以湍流下传）
- 五类成因：
  1. **辐射逆温**（图 6.29）
  2. **下沉逆温**：空气下沉增温（见 6.9.1）；高气压区、范围广、厚度大、常不接地；相当于近地面层上空一个盖子，极不利于污染物扩散
  3. **地形逆温**：盆地/谷地（夜间山坡空气辐射冷却、沿坡下沉、暖空气被挤上升浮在冷空气上，图 10.9）、山脉背风侧
  4. **平流逆温**：较暖空气流经较冷地面/水面；冬季沿海（海上暖空气流到大陆）；厚度不大、水平范围广；城市夜间弱递减率 → 农村厚逆温层随气流移到城市上空形成空中逆温（图 10.18）；下风方向农村再建立逆温 → 城市烟气带到地面逆温层
  5. **锋面逆温**：锋面倾斜，暖空气总在冷空气之上 → 冷空气区观测到逆温；快速移动的锋影响不大
- 实际逆温常由几种原因共同造成，需具体分析

### 思考题（p168–169，7 题）
1. 若地球大气由氧组成，则干绝热减温率仍是 9.8℃/km 吗？（提示：氧的 Cv = 21.06 J/(mol·K)）
2. 分析一个空气块在绝热（干绝热、饱和绝热和假绝热）的升降过程中哪些量是保守的？哪些变大？变小？
3. 云团（含凝结水滴的饱和气块）在绝热下沉过程中，温度、压强、比湿、露点、相对湿度、位温及假相当位温将如何变化？
4. 证明：埃玛图上每条干绝热线的位温 θ 与括号内位温 θ′ 的关系 θ′=Cθ，C=p/p′（κ=0.288）
5. 由 q_s=0.622e_s/p 能否用埃玛图估计饱和水汽压？（提示：p=622 hPa 时 e_s 与 q_s 数值关系）
6. 以绝热气块模型作为积云的原始模型，分析云内温度、上升气流速度和含水量的垂直分布特点
7. 什么情况下可用抬升凝结高度估算对流云云底高度？什么情况用对流凝结高度？自由对流高度有什么物理意义？

### 习题（p169，8 题）
1. p=950 hPa、T=5℃、Uw=60%：用埃玛图求比湿、露点、虚温、位温
2. 证明干绝热上升时 e^χ·T⁻¹ 之值不变（χ 记号按书）
3. 一团湿空气 p=1000 hPa、t=20℃、q=5 g/kg，干绝热升至 850 hPa：上升前后相对湿度？
4. p=1000 hPa、t=25℃、RH=80%；日落后降温 5℃：是否产生雾？含水量？
5. 气团 q=0.007，升到凝结高度后继续升到 510 hPa 时 q=0.0025：求凝结高度前及 510 hPa 处的位温
6. p=950 hPa 时 t=14℃、q=0.008；过山（山顶 700 hPa），凝结水 70% 途中降落：求背风面 950 hPa 的温度、比湿、位温、假相当位温
7. 探空（p: 1000/900/850/800/700/600/500/400/300/200；t: 23.0/20.5/17.0/12.0/4.5/−4.0/−12.1/−23.0/−32.5/−45.3；td: 19.0/11.0/7.6/6.8/−1.1/−8.5/−19.2/−29.5/−45.0/−59.5）：
   (1) 900 hPa 比湿、饱和比湿、相对湿度；(2) 标 LCL、CCL、LFC，分析不稳定能量分布，定稳定度类型；(3) 热雷雨所需最高气温；(4) 判 900–1000 与 800–850 hPa 对流性稳定性
8. 环境 Γ=γd，气块在 900 hPa 处 T=280 K 且已饱和，受扰上升得正浮力连续上升（忽略阻力、凝结水）：按未作/作虚温订正分别计算 700 hPa 处速度

### 书答案（印刷 p546，page_0560）—— 对照表
| 题 | 答案 |
|---|---|
| 1 | q=3.4 g/kg；Td=−2.5℃；Tv=278.7 K；θ=9.1℃ |
| 3 | 上升前 34.5%；850 hPa 时 69.6% |
| 4 | 产生雾；含水量 1.49 g/m³（或由 (6.6.7) 估 1.45 g/m³） |
| 5 | 凝结高度 740 hPa；凝结前 θ=315.5 K；510 hPa 处 θ=302 K |
| 6 | 背风面 950 hPa：T=20.5℃；q=0.0057；θ=25℃；θse=44℃（不变） |
| 7 | (1) q=9 g/kg；qs=17 g/kg；Uw=53%；(2) LCL=950 hPa、CCL=850 hPa、LFC=800 hPa；**真潜不稳定**；(3) 最高气温须达 30.5℃；(4) 1000–900 hPa 对流性不稳定（θse：1000 hPa 68℃ → 900 hPa 60℃，随高度减小） |
| 8 | (1) 未订正 24.2 m/s；(2) 虚温订正 26.7 m/s |

## 2. 源码素材

### 2.1 调用链与节律
- 物理序列（dyn_em/module_first_rk_step_part1.F）：radiation_driver（行~270，内部 RADT 节拍）→ surface_driver（~603）→ pbl_driver（~1164）→ **cumulus_driver（~1562）** → shallowcu_driver（~1755）；微物理在 solve_em 后段（~3850）
- 调用节律（module_cumulus_driver.F）：四判据——itimestep==1 / cudt==0 或 stepcu==1 / MOD(itimestep,stepcu)==0 / 自适应步长（curr_secs ≥ cudtacttime）；cu_physics=0 直接 RETURN
- stepcu = max(nint(cudt*60/dt),1)（module_physics_init.F 的 cu_init 内；cudt 单位=分钟）
- **倾向并入**（仅 G3 与 New Tiedtke）：调用前 RTHFTEN ← RTHFTEN + (RTHRATEN+RTHBLTEN)·π；RQVFTEN ← RQVFTEN + RQVBLTEN（积云方案看到的大尺度倾向含辐射+边界层贡献——闭合里要用）
- HALO（G3/GFL/KFeta/MSKF）：HALO_CUP_G3_IN/OUT；KF 系列自带 W 场累积（"DON'T JUDGE TIME STEP HERE"）
- 接口要点：CUTOP/CUBOT（htop/hbot）、NCA、CU_ACT_FLAG（格点是否激活对流）、W0AVG、cudtacttime 回写、pratec 经 tmppratec 中转；KFCUP 方案 raincv→pratec 后处理
- cu_init（module_physics_init.F）：STEPCU 计算 + 全部积云倾向清零（各方案 init：kfinit / bmjinit / kf_eta_init / mskf_init / … / ntiedtkeinit）

### 2.2 方案表（Registry.EM_COMMON 包 + README.namelist）
- cu_physics：0 无；1 KF(new Eta)；2 BMJ；3 GFL；4 尺度感知 SAS；5 G3；6 Tiedtke(修改版)；7 CAM ZM；10 KF-CuP；11 MSKF；14 KSAS；16 **New Tiedtke**；93 GD；94/95/96 SAS 系；99 旧 KF
- 相关 namelist：cu_rad_feedback（只对 GF/G3/GD/KF，且需 cu_diag=1）、bmj_rad_feedback、cudt（分钟内插）、kfeta_trigger（1/2/3）、cugd_avedx、ishallow（GFL/G3）、cu_diag、kf_edrates（cu=1/11/99）
- 浅对流独立开关 shcu_physics：1 G3(占位) / 2 CAM-UW / 3 GRIMS / 4 NSCV / 5 Deng（module_shallowcu_driver.F：camuwshcu_driver、grims、shcu_nscv、deng_shcu_driver）
- physics_suite：'CONUS' → mp=8、cu=6、RRTMG、bl=2、sfclay=2、sf_surface=2；'tropical' → mp=6、cu=16、RRTMG、bl=1(YSU)、sfclay=91、sf_surface=2；嵌套可覆盖（-1=沿用套件，0=关）
- 方案号→源码文件：1 module_cu_kfeta.F（KF_eta_CPS）｜16 module_cu_ntiedtke.F + physics_mmm/cu_ntiedtke.F90｜5 module_cu_g3.F（G3DRV）｜93 module_cu_gd.F（GRELLDRV）｜2 module_cu_bmj.F｜7 module_cu_camzm_driver.F｜6 module_cu_tiedtke.F｜14/96 module_cu_ksas.F/nsas.F

### 2.3 New Tiedtke（cu_physics=16）精读要点
- **双层结构**：phys/module_cu_ntiedtke.F = 薄包装（cu_ntiedtke_driver / ntiedtkeinit / cu_ntiedtke_pre_run / cu_ntiedtke_post_run）；实体在 phys/physics_mmm/cu_ntiedtke.F90（CCPP 风格：module cu_ntiedtke_common + module cu_ntiedtke）——与 ch13 WSM6 双层结构同构
- 血统：Tiedtke (1989, MWR 117, 1779–1800)；新版差异（代码注释自列）(a) 深/浅新触发函数（Jakob & Siebesma 2003；Bechtold et al. 2004/2008/2014）(b) 深对流非平衡闭合 (c) 新对流时间尺度 (d) 新卷入卷出率 (e) Sundqvist (1978) 云水→雨转换 (f) 云尺度气压梯度（Gregory 1997；Wu & Yanai 1994）
- 命名（ECHAM 血统）：cumastrn 主控 / cuinin 初始化 / **cutypen** 云型判决 / **cuascn** 上升气流 / cudlfsn 下沉气流起点 / cuddrafn 下沉气流 / **cuflxn** 通量整合 / cudtdqn、cududvn 倾向 / cuadjtqn 饱和调整 / **cubasmcn** 中层对流云底 / **cuentrn** 卷入卷出
- **pre_run**：delt = dt·stepcu（整段累积时间）；slimsk = |xland−2|（陆=1 海=0）；全部场垂直翻转（WRF 底→上 ⇒ 方案顶→底）；ω = −0.5·g·ρ·(w_k+w_{k+1})；RTHFTEN/RQVFTEN 传入（itimestep=1 清零）
- **post_run**：raincv = rn/stepcu；pratec = rn/(stepcu·dt)；倾向 = (新−旧)/delt（温度倾向再除 exner 转位温）
- **尺度依赖因子**（run 内、逐列）：dxref=15 km；dx<15 km：scale_fac = (1.06133+ln(15/dx))³、scale_fac2 = √scale_fac；dx≥15 km：scale_fac = 1+1.33e-5·dx、scale_fac2 = 1。用法：深对流 τ ← τ·scale_fac；浅对流 M_base ← M_base/√scale_fac2
- **cumastrn 十步**：①常数（zcons=1/(g·dt)、zcons2=3/(g·dt)——最大质量通量=3 倍层质量/时步）②cuinin ③cutypen ④首猜云底质量通量 ⑤cuascn（先不计下沉气流）⑥下沉气流（cudlfsn→cuddrafn）⑦闭合（重算云底质量通量+按比例缩放全部通量）⑧cuflxn（最终通量+云底以下雨蒸发）⑨cudtdqn（T/q 倾向）⑩cududvn（u/v 倾向）+ 动能耗散加热
- 三类对流 ktype：1 深（penetrative）｜2 浅（stratocumulus）｜3 中层（mid-level）；云厚 < zdnoprc=200 hPa 的深型改判浅型；浅云厚 >200 hPa 不成立
- **cutypen 触发（两类测试气块）**：
  - 浅测试：从最低模式层出发，**由地面通量起动**（Jakob 2003：w* = 1.2·(0.001−part1·part2)^(1/3)，part1=1.5·0.4·z/T…；ΔT = 1.5hfx/(ρcp w*)；Δq = 1.5qfx/(ρw*)；初始动能 ½w*²）；测试卷入率 ε_test = 0.8/z + 2e-4；沿途 cuadjtqn 饱和调整（云底=首次饱和处，用 dqs/dT 线性插值精确定位）；动能 kup 隐式积分 kup=(atop1·kup(k+1)+2dz·b)/(1+2coef)，kup<0 定云顶
  - 深测试：**逐层搜索出发层**（levels 从 klevm1−1 下探到 klev/2+1；出发层距地面 ≤350 hPa）；出发层为 60 hPa 混合层（近地面时）或单层，扰动 +0.2 K、+1e-4 kg/kg、初始动能 0.5 m²/s²；测试卷入率 ε_test = 1.75e-3·min(1, qs(z)/qs(base))³（湿度依赖，Bechtold 2008）；云厚 ≥ zdnoprc=200 hPa → ktype=1
- **首猜云底质量通量**（cumastrn 之 3b）：zmfmax = (p_bot−p_{bot−1})·zcons2；深：0.1·zmfmax；浅：MSE 收支 zdhpbl/zdh（zdhpbl=Σ(alv·q倾向+cpd·T倾向)Δp 的 PBL 累积；z≤0 → 关浅对流）
- **卷入/卷出**（cuentrn + cuascn 实测）：
  - 云底"组织化卷入"：zoentr = 1.75e-3·[1−min(1, q/qs)]·dz，≤0.4·M
  - 云内：ε = 1.75e-3·[0.3 + (1−min(1, q/qs))]·(qs/qs_base)³·dz，≤0.4·M；深型另有 [(3/8)·0.506/0.2] 阻力形（z_cwdrag）与动能耗散
  - 卷出基线：δ = 0.75e-4·dz·M × [1.6−min(1, q/qs)]；浅对流 ε 加倍、δ=ε（质量通量近守恒）
  - cuentrn 返回的 pdmfen 会被 zoentr 覆盖（写作时以 cuascn 内实现为准）
- **闭合**：
  - 深（ktype=1，Bechtold 2014）：τ_c = (z_top−z_base)/(2+min(15, w_up))，钳位 [360, 10800] s；τ = τ_c·scale_fac；zheat = Σ[(Δθ/θ)…]·g·M（加热积分）；zcape1 = Σ[(ΔTv/Tv) − ql]·Δp（浮力积分）；**非平衡**：zcape = max(0, min(zcape1 − zcape2, 5000))，zcape2 = Σ τ_bl·[(1+0.608q)·θ倾向 + 0.608·T·q倾向]·Δp（τ_bl≤300 s 的 PBL 生成项）；M_base = zcape·M_guess/(zheat·τ)，≥1e-3、≤zmfmax
  - 浅（ktype=2）：M_base = zdhpbl/zdh / √scale_fac2；下沉气流修正（zeps 项）
  - 中层（ktype=3，cubasmcn）：出发层 0.5–10 km 且 q>0.8·qs；M_base = max(cmfcmin, −ω/g)，≤cmfcmax=1（大尺度上升驱动）
  - 重算后：下沉气流按 zfac、上冲气流按 zmfs 等比缩放全部通量
- **降水（cuascn 内，Sundqvist）**：阈值 ql>0.5 g/kg（陆）/0.3（海）；zwu = min(15, √(2·kup))；转换率 = cprcon/(0.75·zwu)/g；T<−5℃ Bergerón 增强 zcbf = 1+0.5√(zdt)；指数解 zlnew = zl_old·e^{−zd} + zc/zd·(1−e^{−zd})；z_cldmax = 5e-3；雨滴落速 21.18·r^0.2；冰/雪比 z_cwifrac=0.5
- **饱和调整 cuadjtqn**：kcall=0 环境 qs / 1 云内凝结 / 2 下沉蒸发；常数 c1es=610.78、c3les=17.2693882、c4les=35.86、c3ies=21.875、c4ies=7.66、tmelt=273.16
- **饱和比湿**：foeewm(T) = c2es·[α·e_w(T)+(1−α)·e_i(T)]，c2es = c1es·Rd/Rv（即 ε·es 标度）；zqs = foeewm/p；qs = zqs/(1−vtmpc1·zqs)，vtmpc1 = Rv/Rd−1 = 0.608（实为"混合比→比湿"精确换算）
- **液相分数 foealfa** = [(min(273.16, max(250.16, T)) − 250.16)/(273.16−250.16)]²（−23℃~0℃ 二次斜坡）——与 ch13 calc_effectRad/psi 族一致；foelhm = α·alv+(1−α)·als
- 动量：momtrans=2 → 云尺度气压梯度（pgcoef=0.7，Gregory 1997）；动能耗散 ztdis 加热
- 参数表（common）：zdnoprc=2e4 Pa、cprcon=1.4e-3、cmfdeps=0.30、entrdd=2e-4、cmfcmax=1.0、cmfcmin=1e-10；开关全开：nonequil/lmfpen/lmfmid/lmfscv/lmfdd/lmfdudv=.true.；momtrans=2
- 注释建议：TC 气候模拟 @20 km 用 YSU+RRTMG+WSM6、momtrans=2、pgcoef 0.7–1.0、nonequil=.false.；陆上日循环降水 nonequil=.true.

### 2.4 KFeta（cu_physics=1）对照要点
- W0AVG 累积：W0 = 0.5·(w_k+w_{k+1})；W0AVG = (W0AVG·(TST−1)+W0)/TST，TST = 2·STEPCU（自适应步长另有版本）
- **触发**（Fritsch-Chappell / Kain & Fritsch 1992；Kain 2004）：混合层气块抬至 LCL；判据 TLCL+DTLCL+DTRH ≥ TENV：
  - DTLCL = 4.64·WKL^0.33（Kain 2004 Eq.1），WKL = 插值 W0AVG·(DX/25km) − WKLCL；WKLCL = 0.02·z/2km（z<2 km）或 0.02 m/s（校正到 25 km 网格的经验关系）
  - trigger=2：DTLCL = max(TPART_H+TPART_V, 0)（Ma & Tan 2009：9 点湿度平流极值归一化 → 温度扰动）
  - trigger=3：DTRH 按 LCL 处 RH（U00=0.75；Narita & Ohmori 2007）
  - 初始 W：WLCL = 1+0.5·√(2g·ΔT·500/TVEN)，≤3 m/s
- **闭合**：ABE（含上冲/下沉耦合的 CAPE）在 TIMEC 内移除 ≥90% → 迭代质量通量因子 AINC（≤10 次）；收敛 |FABE−1|≤0.05；上冲/下沉组合若增加 CAPE → 禁止对流
- TIMEC = DX/VCONV（LCL 与中层平均风速），钳位 [1800, 3600] s；浅对流 2400 s；取整为 DT 整数倍
- 降水效率：PEF = 风切变多项式（0.2–0.9）+ 云底高度订正 PEFCBH
- kf_edrates 输出 UDR/DDR/UER/DER/TIMEC（诊断）

### 2.5 与 NTiedtke 的对照点（写作骨架）
| 维度 | KFeta(1) | New Tiedtke(16) |
|---|---|---|
| 触发 | 单条混合层气块+W0AVG 扰动（或湿度平流/RH 变体） | 浅：地面通量起动；深：多出发层测试气块+湿度依赖卷入 |
| 闭合 | 迭代到"TIMEC 内移除 ≥90% CAPE" | 解析式 M=CAPE/(τ·work)，非平衡扣 PBL 生成项 |
| 时间尺度 | TIMEC=DX/V，30–60 min | τ=Δz/(2+min(15,w))，360–10800 s ×scale_fac |
| 尺度感知 | kfeta_trigger/nsas_dx_factor 等间接 | scale_fac 显式（<15 km 立方增长） |
| 降水 | PEF 效率型（切变+云底高度） | Sundqvist 微物理型（ql→qr 指数转换+B-F） |
| 浅对流 | 由同一方案内 ishallow 分支或独立 shcu | 方案内 ktype=2（MSE 闭合）+独立 shcu_physics |

## 3. 实验（轻轨）设计
- E1 整层升降稳定度（书 6.9.1/例 6.2）：Γ2(p2) 曲线；判据 (6.9.4) 复算 467.7/390 hPa；再以"等熵厚气层"离散模型精确对照
- E2 习题 7 全解：900 hPa 湿度三量；LCL/CCL/LFC 定位；对流温度（对照 30.5℃）；层结稳定度类型；1000–900 与 800–850 对流性不稳定判据（θse 剖面，对照 68/60℃）
- E3 习题 8：700 hPa 气块速度（对照 24.2 / 26.7 m/s）
- E4 质量通量概念：卷入率→云顶敏感性；M(z)=M_b·exp(∫(ε−δ)dz) 通量廓线；τ(dx) 尺度因子表（27/12/9/4/3/1 km）；浅对流闭合 zdhpbl/zdh 数值
- 图：ch15_layer_subsidence.png、ch15_sounding_stability.png、ch15_plume_massflux.png（+1）

## 4. 待复核/缺口
- ⚠ 6.9.2 末段热带结论括注符号（"负值区（∂θse/∂z＞0）"字面矛盾）→ 放大复核（ch15_crop_check.py）
- 图 6.28 两联图细节以书页为准（(a)(b) 均画 T–lnp 坐标、θse 判据文字引用）
- 思考题 1（氧大气）与思考题 4（埃玛图 θ′=Cθ）属通用题，ch13 已全解 → 本章以 6/7 与习题 6/7/8 为"积云视角"复现
- 集群对照实验（cu=1 vs 16，d01 24 h）预留（ch15 复核清单项）