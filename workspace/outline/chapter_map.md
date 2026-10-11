# 素材扫描底稿：课程—教材—WRF 对照图

> 生成：2026-10-10，phase 0 材料准备。本文件是后续每章写作的"底图"，
> 后续会话只需读本文件 + notes/progress，不必重读全部 PPT 与书页。

## 1. 课程信息（来自 PPT 首讲）

- 课程：大气物理学（兰州大学大气科学学院本科课程，任课教师：王治厅）
- 考核：平时作业/小测/出勤 30% + 期末闭卷笔试 70%（第 19~20 周）
- 课程范围 = 教材第 1~6 章（PPT 首讲 slide 2 明确列出）
- 参考书：华莱士《大气科学概观》、徐绍祖《大气物理学基础》、徐玉貌《大气科学概论》
- PPT 每讲自带"重 点/掌握要点/思考题"页 → 已判定为考点来源

## 2. 教材（《大气物理学》第 2 版，盛裴轩等，北大出版社 2013）

- 扫描 PDF：566 个 PDF 页；图片已全部提取至 `AtmosphericPhysics\book\page_NNNN.jpg`（565 嵌入图 + 1 渲染页；manifest 见 `workspace\book_manifest.csv`）
- **页码换算：正文印刷页 N → `book\page_{N+14:04d}.jpg`（已抽验：印刷 p2 = page_0016 ✓）；目录在 PDF 8–14；无文本层（纯扫描）**
- 书末资源：部分习题答案（印刷 p545 起）、附录 表A 特征数 / 表B 符号 / 表C 常用物理常数（印刷 p549–550）
- 全书 20 章 5 篇；第 1~6 章（重点）：
  - 第一章 行星大气和地球大气的演化（1.1 行星大气；1.2 地球大气的演化）
  - 第二章 地球大气的成分及分布（2.1 干洁大气；2.2 水汽；2.3 气溶胶）
  - 第三章 大气压力（3.1 静力学方程与压高公式；3.2 大气模式；3.3 气压-位势高度；3.4 标准大气；3.5 气压时空分布）
  - 第四章 大气的分层和结构（4.1 分层；4.2 大气质量；4.3 海洋）
  - 第五章 地面和大气中的辐射过程（5.1 基本概念；5.2 物理规律；5.3 大气与辐射相互作用；5.4 太阳辐射传输；5.5 长波辐射；5.6 辐射平衡）
  - 第六章 大气热力学基础（6.1 热力学基本规律；6.2 干绝热；6.3 饱和/假绝热；6.4 热力学图解；6.5 绝热混合；6.6 等压冷却；6.7 温湿参量；6.8 静力稳定度；6.9 整层升降；6.10 逆温层）
  - 第七章 大气动力学（p170 起）——大三内容，教材中仅作"展望/引用"
- 第 7~20 章：湍流(8)、边界层(9)、非均匀下垫面(10)、云雾宏观(11)、云降水微物理(12)、积云动力学与云模式(13)、人工影响天气(14)、大气电学(15)、散射(16)、光学现象(17)、折射(18)、GPS气象(19)、声学(20)——可在相应章节"延伸阅读"引用

## 3. PPT 清单（12 个 pptx，解包于 `AtmosphericPhysics\ppt\*_unpack`；文本抽取于 `workspace\ppt_text\`）

| 讲 | 文件 | 页数 | PPT 自标考点（原句摘要） |
|---|---|---|---|
| 1 | 1 行星大气和地球大气的演化 | 28 | 掌握主要行星大气特点；地球大气形成演化过程；各演化阶段组成（原始H2/He/CO→次生CO2/CH4/NH3→现代N2/O2） |
| 2-1 | 2-1 干洁大气 | 27 | 干/湿空气状态方程；成分三分类（浓度法/寿命法）；CO2、CH4、CFCs、O3(DU、Chapman、臭氧洞)、硫/氮化合物；干空气状态方程推导 |
| 2-2-3 | 2-2-3 水汽和气溶胶 | 36 | 湿度表示法（r,q,e,ρv,U,Td,Tf）及互换；Tetens 公式（水面/冰面）；Kelvin 公式(参考)；虚温与湿空气状态方程；气溶胶分类/Junge谱/Γ谱/来源/五种作用；气溶胶直接-间接-半直接辐射效应 |
| 3 | 3 大气压力 | 46 | **静力学方程、压高公式、大气模式（等温/多元/均质）**；大气标高；位势高度 gpm 与气压-位势公式；标准大气(1976美国/国军标)；气压场五型式；海平面冬夏气压系统；气压日变化 |
| 4 | 4 大气分层 | 23 | **对流层/平流层/中间层特征；大气总质量估算及垂直分布**；四种分层法（热力/化学/电磁/气压）；对流层顶定义(2 K/km)；匀和层/非匀和层；海洋物理特性（热容量 3120×大气） |
| 5-1 | 5-1 辐射的基本概念 | 26 | 辐射通量Φ/辐亮度L/辐照度E 及立体角；各向同性/均匀/定常；E–L 积分关系；净辐照度；点源/平行辐射；朗伯体与朗伯定律 |
| 5-2 | 5-2 辐射的物理规律 | 29 | 吸收率/反射率/透射率、黑体/灰体；**普朗克/斯特藩-玻尔兹曼/维恩位移/基尔霍夫四定律**；有效温度(5777K)与色温；短波/长波以 4 μm 分界；太阳与地球辐射相对大小 |
| 5-3 | 5-3 地球大气与辐射的相互作用 | 51 | **吸收光谱、散射特征、比尔定律**；选择吸收（分子能级 E=Ee+Ev+Er）；H2O 6.3μm/转动带、CO2 15μm/4.3μm/2.7μm、O3 9.6μm/Hartley；8–12μm 大气窗；谱线增宽(压力/多普勒)；瑞利 vs 米散射（尺度参数 α）；天空颜色四问；光学厚度/光学质量/订正因子 |
| 5-4 | 5-4+ 太阳辐射在地球大气中的传输 | 64 | **太阳常数、太阳辐射光谱、大气上界辐射能**；太阳赤纬/时角/天顶角/方位角/时差；大气上界日总量 Qd；地面直接辐射五项削弱；相对大气质量；Ångström 浑浊度；长法测谱；阳伞效应（Pinatubo）；地面/云/行星反照率；NDVI；冰雪-反照率正反馈 |
| 5-5 | 5-5 地球-大气系统的长波辐射 | 20 | 地面长波灰体(0.82–0.99)；长波传输三特点（漫射、忽略散射、吸收+放射）；**施瓦茨恰尔德方程及解**；漫射因子 1.66；OLR 推导 |
| 5-6 | 5-6 地球-大气系统的辐射平衡 | 24 | **净辐射（辐射差额）概念**；温室效应辐射平衡模式（Al/As/R→Tg=278.6K, Ta=247.7K）；地面/大气/地气系统辐射差额；大气逆辐射、有效辐射；变温率；观测辐射平衡 |

- 备注：`5-4太阳辐射…` 与 `5-4+太阳辐射…` 原为重复课件（仅差 2 行），**重复份已于 2026-10-10 按用户指示删除**，现仅存"5-4+"版
- PPT 中公式多为图片，文本抽取不含公式 → 写作时需按页读幻灯片截图（`ppt\<讲>\_unpack\ppt\media\`）或按书页核对公式；PPT 已获老师同意可嵌入教材

## 4. WRF / WPS 源码（已解包，版本字符串核验）

- `source\WRFv4.8.0\WRFV4.8.0\`：README 首行 "WRF Model Version 4.8.0" ✓（含 phys/ dyn_em/ share/ chem/ var/ hydro/ Registry/ run/ test/ 等）
- `source\WPSv4.7.0\`：README 首行 "WRF Pre-Processing System Version 4.7.0" ✓（geogrid/ ungrib/ metgrid/ util/）
- 版本较新，网上中文资料少 → 写作时以源码+UCAR官方英文文档为准，禁止凭记忆写特性

### 章→WRF 锚点映射（v1，写作时逐条核验后引用"文件+子程序名"）

| 章 | WRF/WPS 锚点（已确认文件存在） |
|---|---|
| 1 行星大气/演化 | 模式总体架构（frame/ share/ main/ ndown 嵌套）；WPS 三程序与静态场（geogrid 地形/土壤/植被）；ideal 理想个例（test/）；行星大气对照可提 MarsWRF 等（延伸） |
| 2 成分/湿度 | `share/module_model_constants.F`（Rd, Rv, ε, cp, Lv…）；Registry 水汽变量 QVAPOR/QSH? (QVAPOR 确认)；饱和水汽压：微物理方案内 sat adjustment（`phys/module_mp_wsm6.F`、`module_mp_thompson.F`）；气溶胶：`module_ra_aerosol.F`、Thompson aerosol-aware、RRTMG 气溶胶光学 |
| 3 大气压力/静力学 | `dyn_em/module_initialize_real.F`（base state：znu/znw/pb/ρb/p_top）；η 坐标；压高/位势：`share/module_compute_geop.F`；real.exe 垂直插值；namelist e_vert/p_top_requested |
| 4 分层/结构 | 垂直分层与模式顶（namelist）；`phys/module_sf_oml.F`、`module_sf_lake.F`、`module_sf_clm/ctsm`（4.3 海洋下垫面）；landuse 分类（WPS geogrid GEOGRID.TBL） |
| 5 辐射 | `phys/module_radiation_driver.F`；RRTMG：`module_ra_rrtmg_lw.F`/`module_ra_rrtmg_sw.F`；备选 ra_cam/gfdleta/goddard/gsfcsw/hs/flg；云光学 `module_ra_effective_radius.F`；气溶胶光学 aer_opt；太阳天顶角/日地距离（radiation driver 内 coszen、julian）→ 与 5.4 公式直接对应；radt 调用频率；OLR 诊断输出 |
| 6 热力学 | 位温/相当位温：微物理饱和调整与 `phys/module_bl_mynn?`(待核) 等；LCL/CAPE：积云方案触发（`module_cu_kf.F` 等）；T-lnP 图：WRF 输出 p/t/td + MetPy 绘制；静力稳定度↔边界层/对流触发判据 |
| 7 动力学(展望) | `dyn_em/solve_em.F`、`module_small_step_em.F`、`module_advect_em.F`（RK分裂、声波、平流） |

### 其他确认

- `Registry/Registry.EM_COMMON`（变量总表）、`registry.dimspec`、`registry.hyb_coord`（混合坐标——第3章可提）
- P312 环境（D:\Code\miniforge3\envs\P312\python.exe）已有 PyMuPDF 1.28.2；`import pymupdf` 新 API
- 工作区非 git 仓库 → 时间戳为锚

## 核验进度（随写作更新）

### ch03 架构总览 —— 已核验（2026-10-10）
交付：`doc\ch03_architecture_overview.md`
已核验锚点（详见 `workspace\context\verify_log.md`）：
- 主链：`main/wrf.F`(PROGRAM wrf) → `main/module_wrf_top.F`(wrf_init/wrf_dfi/wrf_run/wrf_finalize) → `frame/module_integrate.F`(integrate，递归) → `share/solve_interface.F`(solve_interface) → `dyn_em/solve_em.F`(solve_em，~5200 行)
- med_* 中介：接口在 frame/module_integrate.F，实现在 share/mediation_integrate.F（+ mediation_wrfmain.F）
- PROGRAM 名实测：real_em.F=real_data、tc_em.F=tc_data（与文件名不同，易错点）
- 版本：inc/version_decl = 'V4.8.0'
- 目录树/构建双轨/run(93文件)/test(15算例) 全部实测；集群巡览含 ldd 误报坑（file+readelf 才准）
- 教材包含：mermaid 生命周期图×2 + 四层架构图（改造导航图）+ 集群实录 4 小节 + 速查表

### ch04 Registry 机制 —— 已核验（2026-10-10）
交付：`doc\ch04_registry_mechanism.md`
已核验锚点（详见 `workspace\context\verify_log.md`）：
- 记录统计：Registry.EM_COMMON 3727 行（state≈1678、rconfig≈799、package 280、i1 43、halo 83、typedef 52、period 33、xpose 14）；registry.dimspec 100 条；Registry.EM 48 行；Registry/ 下 40 余文件
- state 11 列格式 + 顺序陷阱（LU_INDEX、znu/znw/dzs/zs 头部注释原文）；4D 数组族（"-"记录 + 成员 + package）；T2/PSFC/RAINC/SST_INPUT 案例
- IO 语法（reg_parse.c：i/h+数字或{n}、r、b、f/d/u/s=(fcn:aux)）；位定义 inc/streams.h；MAX_HISTORY=25（arch/preamble）；运行期流号 switches_and_alarms.inc（history_only=1…auxinput24_only=50、restart_only=51、boundary_only=52）
- T2 全解 `i01rh01{22}{23}du`：{22}{23}=auxhist22/23=z/p 层诊断（module_check_a_mundo.F 报错文案 + README.namelist 实证）
- 生成链：configure.wrf(REGISTRY=Registry、COREDEFS) → compile 脚本合成 Registry/Registry（4810B、警告首行）→ frame/Makefile 规则 → tools/registry；cmake 等价行（tools/CMakeLists.txt）
- 生成物地图 20+ 项（含使用者）；inc/*.inc=480；allocs 32 片 + deallocs 12 片；nl_config.inc 2330 对访问器（cpp 8+8 片）；nl_get_0_routines.F=dummy 桩（实测）
- 实景样本：allocs_calls.inc / allocs_23.F（ru_tendf_stoch 状态表元数据含 streams 位）/ t2 在 allocs_1.F / state_struct.inc 域字段 / i1_decl.inc 自动数组（solve_em.F 注释）
- 实参：actual_new_args 59 / actual_args 2749（gen_args.c "only 4D" 注释）→ ch03 已同步勘误
- 图纸：ch04 §4.5 = 给 WRF 加诊断变量 T2_PEAK（ch20 一级实战按此实施）

### ch05 编译体系与增量重编译 —— 已核验（2026-10-10）
交付：`doc\ch05_build_and_dev_loop.md`
- `compile`（tcsh）分发逻辑（em_real→4 exe；先删后建）；Registry 合成仅比较 Registry.EM mtime（实测陷阱：只改 EM_COMMON 不触发 registry）
- configure.wrf 实测（SFC=ifx、REGISTRY=Registry、MAX_HISTORY 宏）；cmake 路线（configure_new/compile_new、_build/）
- test/em 15 算例全表（em_real 的 namelist 变体清单）；增量重编译实测 A 组（81 s/12 对象；45 s/4 对象，.o+exe md5 全同）、B 组全链（649 s×2）
- 集群构建实测：wrf.exe 82.6 MB 等 4 个 exe、readelf NEEDED 39 条（含 PnetCDF）、AVX-512 选项实录

### ch06 WPS 流水线 —— 已核验（2026-10-10）
交付：`doc\ch06_wps_pipeline.md`
- WPSv4.7.0 源码（geogrid/ungrib/metgrid）与三表系统（GEOGRID.TBL/Vtable/GRIB2 表）
- 兰州个例实录：geogrid 16 s、ungrib 42 s（窗口机制实证：只解 21 时次 + DATINT 插值）、metgrid 94 s → 42 个 met_em（21 时刻×2 域）
- `num_metgrid_levels=32`（ERA5）；geo_em 城市参数族 `num_urb_params=132`（ch17 伏笔）

### ch07 real.exe 与 namelist —— 已核验（2026-10-10）
交付：`doc\ch07_real_namelist.md`
- real 三步工作（垂直插值/基态构造/边界加工）源码锚点（module_initialize_real.F 的 init_domain_rk、module_compute_geop.F）
- 兰州个例 real 实录：rc=0、44 s；wrfinput_d01/d02、wrfbdy_d01（Time=20）；wrfinput 172 变量 7 组表、wrfbdy 边值/倾向族
- eta_levels 50 层设计与生成脚本；物理方案选择纪律；**已勘误**：restart_interval 实为分钟制（884 行"86400=60 天"案例第 8 章复盘）

### ch08 运行 WRF —— 已核验（2026-10-10）
交付：`doc\ch08_running_wrf.md`
- 5 天生产实测：rc=0、2913 s（48.5 min）、SUCCESS 在 rsl.out.0000 第 32348 行；d01 8000 步（均 0.361 s）/d02 24000 步（0.0838 s）；写盘 41/121 次；输出 940 MB+四文件 3.3 GB；52 核时
- 启动清单逐段解读、module_timing.F 计时体系、frames_per_outfile 帧追加机制
- restart 全闭环：FATAL 事故（rsl.error.failed_restart.0000）、单位陷阱实验（rst1/rst1b 逐字节等价）、rst 解剖（660 变量 + 闹钟元数据属性）、续跑实测 SUCCESS（LBC 时段核对）
- 教学重案：np64 段错误（addr2line→radiation_driver）与**短测代表性事故**（end_minute 单值 → nests_to_open 条件 → d02 未激活；修复后 np64 双域短测 62 s 通过）

### ch09 IO 体系 —— 已核验（2026-10-10）
交付：`doc\ch09_io_system.md`
- io_form 编码（use_package=MOD(io_form,100)、multi_files=+100/+200 文档原文）；包号清单出自 Registry.EM_COMMON package 块 → module_state_description.F 小写常量
- 五写法对照实验（io2/io11/io102/io2q/io2c）：魔数（HDF5 vs CDF-2）、PnetCDF 冒号改下划线、多文件 _0000.._0007、quilt 写盘 0.024 s
- 压缩实证：ext_ncd_write_field 的 NF_DEF_VAR_DEFLATE(level=2)+chunking；34.7 vs 93.7 MB（净数据 2 帧×46.8 MB）
- wrfout 档案解剖（218 变量/Time 帧/Times/FieldType=104/全局属性/补丁属性）

### 待核验（后续批次）
- ch10+ 按《教材编写方案 v2》批次推进；ch17/19/20 与论文2 对接点时回读本篇笔记

### ch10 垂直坐标与静力平衡 —— 已核验（2026-10-10，批次 2 首章）
交付：`doc\ch10_vertical_coords_hydrostatics.md`（物理章八段式）
- 书 3.1–3.4 + 4.1–4.2 考点全覆盖（静力学方程三式、压高公式、标高、三种大气模式与上界、位势高度、标准大气、分层四法、质量估算 5.12×10¹⁵ t）；公式编号取书（扫描页直读：3.1 p30–33、3.2 p33–35、3.3 p35–37、4.1 p48–55、4.2 p55）
- 源码：基态构造链全解（p_surf 解析式/pb/T0/alb/静力积分 phb）+ hybrid_opt=2 Klemp 混合坐标与 c1–c4 系数（registry.hyb_coord 设计文档引用）+ base_* namelist 默认值
- 实验（轻轨）：手算压高公式 vs real 基态 8 项核对全过（0.008 Pa / 0.0001 K / 0.039 m²/s² / 284 m 地形口径差案例）→ 图 doc/figs/ch10_base_state_profiles.png
- 脚本：workspace/scripts/ch10_experiment.py（可复现）

### ch11 大气成分、水汽与气溶胶 —— 已核验（2026-10-10，批次 2 第二章）
交付：`doc\ch11_composition_moisture_aerosol.md`（863 行，含 2 个 mermaid + 3 张自算图 + 6 张 PPT 原图）
- 书第 2 章全节覆盖（2.1 干洁大气/2.2 水汽/2.3 气溶胶）；公式编号全按书（扫描页直读 17 页：印刷页 7–11、16–17、19–28）；表 2.1/2.2/2.3/2.4/2.5a-b/2.6 数字全部核对
- 源码五套饱和水汽压实现全解：SVP1-4（Bolton，module_model_constants + sfclay 全链条）、pq0/a2-a4（Murray，calc_rh）、WSM6 fpvs 内联（CC 积分，physics_mmm/mp_wsm6.F90）、Thompson RSLF/RSIF（多项式 + 注释里的 Bolton/Murphy-Koop）、real 的 MM5 三段式（rh_to_mxrat1）
- 关键发现：real.exe 默认 rh2qv_method=1（e=0.01·RH·Bolton → q=εe/(p−e) → 混合比）；**RRTMG 的 ch4/n2o/cfc11/cfc12 常数 = 书表 2.3 的 2005 列逐位一致**；co2 为年变化函数（2005 年 = 379.5 ppmv）
- 实验（轻轨，无需集群）：四组核对（闭合/六实现对照/虚温密度/实测复现）；**地面 T2/Q2 与 met_em 地面层逐位一致**；18 层 dq RMS 0.071 g/kg；贝吉龙 Δes 最大 −11.7℃（书称 −12℃ ✓）
- 图：doc/figs/ch11_es_curves.png、ch11_real_data_check.png、ch11_virtual_temp.png、figs/ppt/ch11_ppt_*.{png,jpeg}
- 脚本：workspace/scripts/ch11_experiment.py（可复现）
- 勘误记录：书 (2.2.9b) 冰面参考温度以表 2.5(b) 反推为 273.16 K（扫描字迹近似 276.16 不可采信）

### ch12 辐射过程族 —— 已核验（2026-10-10，批次 2 第三章）
交付：`doc\ch12_radiation_family.md`（1331 行，含 1 个 mermaid + 3 张自算图 + 6 张 PPT 原图）
- 书第 5 章全节覆盖（5.1 基本概念/5.2 四定律/5.3 相互作用/5.4 太阳辐射/5.5 长波/5.6 辐射平衡）；公式编号全按书（扫描页直读 54 页：印刷页 62–121）；表 5.1–5.17、例题 5.1–5.3、思考题 7 题、习题 1–15 全部核对录入
- 源码：radiation_driver 四触发节拍（radt/radtacttime/stepra/ra_call_offset）；**radconst+calc_coszen 与书 (5.4.2)/(5.4.3a) 逐符号一致**；RRTMG LW 16 段/SW 14 段波段表；ghg_input 两分支（CAMtr 年插值 vs 2005 常量）；o3input 两分支（CAM 气候学 o3rad vs inirad）；云光学 inflglw 旗标与 effectRad 有效半径；SOLCON=1370×ECCFAC、rrsw_scon=1368.22 二元口径
- 关键发现：**WRF 的 JULIAN 为零基日序（2025-07-12=192）**；coszen 评估在辐射区间中点（xtime+radt/2）；`ghg_input`/`o3input` Registry 默认 1/2（个例未设→默认走 CAMtr+CAM 臭氧）
- 实验（轻轨，无需集群，六组）：**太阳几何逐格闭环**（全 89×89 格点 max|ΔCOSZEN|=8.9e−8、max|ΔHRANG|=0）；四定律数值核验（σ 推导 0.032%、∫F_B=σT⁴ 0.011–0.032%、λmax=2897.8/T 精确）；Kasten (5.4.22) 复现书表 5.5 逐位；Qd 夏至比 1.366（书 1.37）；两层温室基准 278.6/247.7 逐位
- 图：doc/figs/ch12_planck_bands.png、ch12_solar_geometry.png、ch12_ozone_ghg.png、figs/ppt/ch12_ppt_*.{png,jpeg}
- 脚本：workspace/scripts/ch12_experiment.py、ch12_extract_ppt_figs.py（可复现）
- 勘误记录：**书表 5.16 敏感性六行无法由 (5.6.4) 复现**（教材 12.9.4 已列对照表）；表 5.2 的 300 K 行取整偏粗（1.04%）

### ch13 微物理方案族 —— 已核验（2026-10-10，批次 2 第四章）
交付：`doc\ch13_microphysics_family.md`（1321 行，含 2 个 mermaid + 3 张自算图；PPT 未到，考点节自拟）
- 书第六章 6.1–6.7 全节覆盖（印刷页 123–153；直读 33 页含思考题/习题 p168–169）；公式 (6.1.1)–(6.7.6) 全按书号；思考题 7 题、习题 8 题全解（含数值答案，脚本可复现）
- 源码：微物理调用链（solve_em → moist_physics_prep_em → microphysics_driver → 方案 → finish）；39 个 CASE 分发 + 变量契约；**Thompson 精读**（预报量/谱与幂律/查表策略/饱和调整 3 次牛顿/守恒五保险/冰核化三来源/calc_effectRad 闭环）；**WSM6 对照**（physics_mmm 双层结构、conden 单步解析、fpvs、PLM 沉降）；mp_physics 0–106 方案号表（README×Registry 双表）
- 关键对照点：**饱和调整 = 书 (6.6.3) 隐式方程的两种数值解法**（Thompson 牛顿 vs WSM6 单步，实验差 ≤毫开尔文量级）；Lv(T) 三口径并存（−2323/−2343.6/−2112）记录
- 实验（轻轨）：埃玛图+A/B/C/D 四组 + 习题解答；LCL 506 m vs 492 m；γs 闭式/数值 0.1–1%；θse 漂移 0.54%；饱和调整残差 ~ss²；习题 6 焚风 θse 守恒 312.3 K
- 图：doc/figs/ch13_emagram.png、ch13_theta_se.png、ch13_satadj.png
- 脚本：workspace/scripts/ch13_experiment.py、ch13_exercises.py（可复现）
- 下一章：ch14 边界层方案族（书 6.8 静力稳定度；MYNN2.5 与 BouLac 双精读 + YSU 对照）

### ch14 边界层方案族 —— 已核验（2026-10-10，批次 2 第五章）
交付：`doc\ch14_pbl_family.md`（854 行，含 2 个 mermaid + 3 张自算图；PPT 未到，考点节自拟）
- 书 6.8 全节覆盖（印刷页 154–163；公式 (6.8.1)–(6.8.21) 全按书号；判据/CAPE-CIN/薄层法三段；烟云五型表；6.9/6.10→ch15）
- 源码：调用链（first_rk_step_part1 → surface→pbl→shallowcu；BENCH pbl_driver_tim；bldt=0 每步）；pbl_driver 全 CASE + BEP flag_bep 段；**MYNN-EDMF 精读**（phys/MYNN-EDMF/ 实体、版本史 V1.0→V6.0、qke=2TKE、boulac_length 亲缘注释、get_pblh 全文、dmp/ddmp_mf 羽流、常数模块、输出四组）；**BouLac 精读**（Martilli 2006；ck_b/ceps_b、"TKE IS NOT ADVECTED!!"、双长度 dlu/dld、igamma 三选、BEP 全链、exch 下限 0.1）；**YSU 对照**（薄壳→physics_mmm 实体、brcr 家族、topdown 云顶混合、topo_wind）；Registry bl_pbl 全表 + README 0–99 + bl_mynn_closure 等 namelist
- 关键对照点：**PBLH 三型判据**（Ri 数 / θv 阈值 / TKE 阈值）——书 6.8 判据的代码化；**BouLac↔MYNN 混合长亲缘**（boulac_length）；**BEP/BEM 官方清单 = YSU/MYJ/BouLac 三方案**（论文 2 选型依据；MYNN 不在列）
- 实验（轻轨）：E1 双判据表（1000–900 分歧案例→6.9.2 伏笔）；E2 虚温订正 CAPE/CIN（LFC 8 km→1.8 km、CIN −1330→−128）；E3 混合层 θ 守恒（兰州柱）；E4 薄层法 0.477 扫描
- 图：doc/figs/ch14_stability.png、ch14_cape.png、ch14_mixed_layer.png
- 脚本：workspace/scripts/ch14_experiment.py（可复现）
- 下一章：ch15 积云参数化族（书 6.9 整层升降/对流性不稳定；New Tiedtke 精读 + KFeta 对照）

### ch15 积云参数化族 —— 已核验（2026-10-10 夜，批次 2 第六章）
交付：`doc\ch15_cumulus_family.md`（含 2 个 mermaid + 4 张自算图；PPT 未到，考点节自拟）
- 书 6.9/6.10 全节覆盖（6.9.1 印刷页 164–165、6.9.2 p166、6.10 p167–168、思考题 p168–169、习题 p169、答案 p546；公式 (6.9.1)–(6.9.5) 全按书号；例题 6.2 全解；五类逆温表；6.8.2 夹卷结尾 p164 页顶）
- 源码：调用链（first_rk_step_part1：辐射→surface→pbl→**cumulus**→shallowcu；微物理在 solve_em 后段）；**cumulus_driver 全 CASE**（17 方案 + DUCU；四条调用节律；`stepcu=max(nint(cudt*60/dt),1)` from `cu_init`；G3/NTiedtke 的 RTHFTEN/RQVFTEN 加餐；HALO 四方案；KF 内部时间步管理）；Registry cu_physics 全表 + README（physics_suite CONUS/tropical；shcu_physics 0–5；cu_rad_feedback 约束）；**New Tiedtke 精读**（双层结构 module_cu_ntiedtke.F + physics_mmm/cu_ntiedtke.F90；pre/run/post 数据流；cumastrn 十步；cutypen 两类测试气块；三类闭合；卷入/卷出公式与 0.4 封顶；Sundqvist 降水；foealfa/foeewm；scale_fac 15 km 分界；momtrans=2）；**KFeta 对照**（W0AVG 滑动平均；KF 触发三选项 DTLCL/湿度平流/RH；TIMEC=DX/V 钳位 1800–3600；90% CAPE 迭代闭合；PEF）
- 关键对照点：**两大闭合流派**（"CAPE/(τ·功)+非平衡"解析 vs "TIMEC 内移除 90%"迭代）；**scale_fac 表**（3 km 达 19 倍→关积云的数量依据）；`zdnoprc=200 hPa` 深/浅分界；浅云质量通量守恒（ε=δ）
- 勘误：6.9.2 末段（印刷页 167）热带结论②括注"（∂θe/∂z＞0）"与"负值区"及 (6.9.5) 矛盾——放大复核确认印刷如此，按"负值区"（＜0）表述（详 verify_log）
- 实验（轻轨）：E1 例题 6.2 复算（467.7/390 vs 469.3/391.1，60 层等熵模型，差 <1 hPa 源于 Γ1 取整）；E2 习题 7 全解（LCL 942.8/CCL 842.7/LFC 807.5；对流温度 30.8 vs 书 30.5；CAPE 790/CIN −124 真潜；θse 62.1→56.2 对流性不稳定 vs 书 68→60）；E3 习题 8（23.9/26.5 m/s vs 书 24.2/26.7）；E4 夹卷-云顶表、M(z) 廓线、scale_fac 表、浅对流闭合算例
- 图：doc/figs/ch15_layer_subsidence.png、ch15_sounding_stability.png、ch15_parcel_velocity.png、ch15_massflux_scaleaware.png
- 脚本：workspace/scripts/ch15_experiment.py（可复现；日志 workspace/logs/ch15_experiment.log）
- 下一章：ch16 陆面方案族（书 4.3 海洋 + 陆面/面层相关；`module_surface_driver` 与 `module_sf_*` 家族）

### ch16 陆面过程族 —— 已核验（2026-10-11 凌晨，批次 2 第七章）
交付：`doc\ch16_land_surface_family.md`（3 个 mermaid + 3 张自算图；PPT 未到，考点节自拟）
- 书 4.2/4.3 全节覆盖（4.2 印刷页 55–56：(4.2.1)–(4.2.3) + 表 4.1 + "薄壳"；4.3 p56–58：引言三重身份、4.3.1 物理特性（3120 倍/三层结构/50%/15–20 m/200–300 m）、4.3.2 海流与图 4.8；第四章习题 p59 + 答案 p545；第四章第四节（能量平衡/土壤热传导）为模式实现补讲）
- 源码：`module_surface_driver.F` 两族 SELECT CASE（sfclay 1/2/3/4/5/7/10/89/91；surface 1 SLAB/2 Noah/3 RUC/4 Noah-MP/5 CLM4/6 CTSM/7 PX/8 SSiB；DTBL 节拍；ZLVL=0.5·DZ8W；ICE/urban 分支）；**Noah 精读**（三层文件结构；SFLX 主控九步；EVAPO→SMFLX→BETA=ETA/ETP→TDFCND→YY/ZZ1→SHFLX；PENMAN 逐式（T24=SFCTMP⁴、RR=1+4εσT³/RCH、DELTA/A/EPSCA/ETP）；TDFCND 公式链（7.7/2.0/0.57/2.2、Kersten）；HCPCT 四组分；HRT+HSTEP 隐式三对角；TBOT@ZBOT=−8 m；LSMINIT（FRH2O 冻土、SNOALB）；REDPRM（KDT/FRZFACT/SLOPE）；ISURBAN 覆盖（SHDFAC=0.05、SMCMAX=0.45、DF1=3.24）；Bolton 饱和式（A2=17.67/A3=273.15/A4=29.65/A23M4=4302.65；雪面 6174/T²））；**三张 TBL 实读**（SOILPARM STAS 四式互核；GENPARM 全常数；VEGPARM 代表行 + LCZ 51–61）；geogrid→real→wrfinput 静态场链路（LANDUSEF/SOILCTOP/SOILTEMP/GREENFRAC→IVGTYP/ISLTYP/TMN/VEGFRA；init_soil_depth_2 的 DZS=0.1/0.3/0.6/1.0）；namelist 全条目
- 关键对照点：两族方案（面层 vs 陆面）分工；"先水分后能量"松耦合（vs Noah-MP/CLM 联立）；线性化误差现场体检（E1：湿 0.039 K/1.6 W/m²，干 0.26 K/9.0 W/m²）；TBL 表-式一致性（常规类吻合；SILT F11 与 BEDROCK REFSMC 两处表内例外 + PLAYA/LAVA/WHITE SAND 人工特设）
- 勘误/口径：书"大气总质量"两处口径（267 vs 1/273 = p₀ 985/g 9.8 与 1013.25/9.80665 之差）；表 4.1 的 77.6% 与 p₀ 口径；习题 3(2) 需 T_v + g=9.80665 才逐位对台 1351.4
- 实验（轻轨）：E1 能量平衡日循环（湿/干双算例；闭合残差 2e-11 W/m²；柱收支 telescoping <1e-8 相对；夜间逆温 5.8 K）；E2 阻尼深度（数值验证六例 ≤1.1%；土壤 0.124/2.37 m 对书 0.1/2–3 m；海洋反演 κ_eff≈1e-2 对书 15–20/200–300 m；纯水分子 6 cm/1.2 m 反证风浪混合）；E3 SOILPARM（全表互核 + 类间表：β/λ/κ/D/KDT）；E4 书习题 3/5 复算（1351.4 gpm 逐位）
- 图：doc/figs/ch16_energy_balance.png、ch16_soil_diffusion.png、ch16_soilparam.png
- 脚本：workspace/scripts/ch16_experiment.py（可复现；日志 workspace/logs/ch16_experiment.log）
- 下一章：ch17 城市冠层方案族（SLUCM→BEP/BEM；URBPARM/LCZ 表；与 `sf_urban_physics` 接口）

### ch17 城市冠层专章 —— 已核验（2026-10-11 凌晨，批次 2 第八章；六段式 + 论文2 对接节替代考点透视）
交付：`doc\ch17_urban_canopy.md`（405 行；2 个 mermaid + 2 张自算图）
- 定位：书前 6 章无城市考点（书第 10 章仅延伸引用，不考核）→ 不设考点节，以 17.7 论文2 对接替代（v4 方案 R5 口径）
- 源码：**SLUCM 精读**（`module_sf_urban.F`：Kusaka 1999→2001→2005→2014→2024/25 NbS 血统；CGS 单位制；`urban` 60+ 实参；`bisection` 皮温；`multi_layer`/`force_restore` 两法（TS_SCHEME=1）；CH_SCHEME=2 Narita；Kanda 修正 AKANDA_URBAN=1.29；内嵌 Noah 土壤链；树/绿屋顶 NbS 群）；**BEP**（`module_sf_bep_bem.F`：`BEP_BEM`→`BEP1D`；街谷几何 NUMDIR/STREET_WIDTH/BUILDING_WIDTH/HEIGHT_BIN；nz_um=18/nbui_max=15；roof_frac=FRC_URB·bs/(bs+ws) 实测式；视角因子矩阵 fww/fwg/fsw…；shadow/rad 链；a/b 隐式系数回路）；**BEM**（`module_sf_bem.F`：BEM 主控→wall/wall_coeff、algebra_short/long、phirat/phiequ/fluxeqocc、fluxvent/fluxcond、regtemp/reghum、air_cond→consump/cop、hsfluxpv）；`module_bep_bem_helper.F` 勘正（仅 3 行 nurbm）；分发在 `module_sf_noahdrv.F`（==1 CALL urban / ==2、==3 两处 CALL BEP_BEM 实参表差）；初始化 `module_physics_init.F` + LCZ 守卫 fatal
- 兼容矩阵（源码实证）：BEP/BEM 仅 YSU/MYJ/BouLac（README）；a_u_bep 消费者 = `module_bl_boulac.F`（flag_bep 分支）/keps/shinHong（不在白名单）
- **BEM 改造地图（论文2；chapter_map 落盘版）**：albrof/albwal/albg（α）←ALBR；emrof/emwal（ε）←EPSR/B；krof/kwal（λ）←AKSR/B=0.67；csrof/cswal/csflo/csgrd（ρc）←CAPR/B=1.0e6；dzrof/dzwal/dzflo/dzgrd（d）←DDZR/B/G；pwin/cop/beta/sw_cond/timeon/timeoff/targtemp/gaptemp/targhum/gaphum/perflo ←URBPARM；gr_frac_roof/pv_frac_roof + effpv=0.19（模块级）←0/标量；城市形态 MH_URB2D/ZD/Z0/λp/λf/AHE ←geogrid y20xx 数据集。现形态=表值/标量 → 目标=2D 场（STEEL_FRAC/ROOF_*2D α/ε/λ/ρ/c/d），走 auxinput（ch09）
- 数据链路：landuse 四套体系（USGS 31-33 / MODIS 13 / NLCD40 / LCZ 51-61=LCZ_1..11）；GEOGRID.TBL 城市条目全表（URB_PARAM=132 维/NUDAPT44、FRC_URB2D、IMPERV、CANFRA、MH/ZD/Z0/BUILD_AREA_FRACTION/LF_URB2D_S（y2010/y2050_urb）、AHE（y20xx_ahe））；namelist 全表（sf_urban_physics/num_urban_*（2/10/10/18/10/10/15）/use_wudapt_lcz/slucm_distributed_drag/distributed_ahe_opt 0/1/2）
- 实验（轻轨 E1–E3；集群双跑预留）：城市等效表面 vs 乡村（白天 T_s 差 +15.5 K、夜空 +1.8 K；LE≡0；夜间 G 差 +40.9 W/m²）；AH：20/50/90 → 日均 +0.68/+1.69/+3.03 K（会导纳 ~28 W/m²K）；绿量 FVG=0.2 → 白天 −6.67 K；通风敏感性 CH×2 → 峰值降 9.6 K；URBPARM 实读（AHDIUPRF 峰 1.00@17h 谷 0.07@04h；AHOPTION/ALHOPTION 默认全关）
- 图：doc/figs/ch17_urban_energy.png、ch17_ah_profile.png
- 脚本：workspace/scripts/ch17_experiment.py（可复现；日志 workspace/logs/ch17_experiment.log）
- 下一章：ch18 理想实验入门（test/em 全表展开 + 精选实操 2–3 个；第 IV 部开篇）

### ch18 理想实验入门 —— 已核验（2026-10-11 凌晨，第 IV 部开篇；技术章六段式）
交付：`doc\ch18_ideal_cases.md`（713 行；2 个 mermaid + 3 张自算图 + 集群实跑实录）
- 定位：第 IV 部开篇；把 ch05 的 test/em 全表展开为"场景/初值机制/物理开关/检验点"四维表；三条机制线索（双钥匙、初始化源码、集群实跑）
- **双钥匙机制**（本章核心发现）：编译期 `IDEAL_CASE`（顶层 Makefile：9 个算例共用 `=ideal`；fire/heldsuarez/scm_xy/tropical_cyclone/real 各一）+ 运行期 `ideal_case`（Registry 包 + `frame/module_state_description.F` 常量 `realcase=0…les=9`）→ `wrf.exe` 不链接任何 initialize 模块 → **同 IDEAL_CASE 家族共享同一二进制**；官方"每算例要 compile"的实质 = 装配运行目录
- 源码：`dyn_em/module_initialize_ideal.F`（2252 行）精读 —— init_domain→init_domain_rk，12 处 SELECT CASE 分发（constants/landmap/levels/sounding/terrain/pert/surfacet/…）；levels 三策略（指数拉伸/eta_levels/均匀）；`nl_set_map_proj(1,0)` 与 msf≡1（"无需 WPS"的机制答案）；f 值表；地形与扰动（quarter_ss 暖泡 +3K、grav2d_x 冷泡 −15℃、les 随机 0.1K）；get_sounding 干湿两遍（湿自下而上 10 次迭代、干自顶向下）；read_input_jet 二进制格式；`main/ideal_em.F` 写出链（仅 specified 写 wrfbdy）
- 口径勘正四则：grav2d_x=密度流（非重力波）；`em_bubbling` 不存在；b_wave=x 周期+y 对称（非双向周期）；em_esmf_exp 是耦合包非算例。另：2D 算例需 serial 构建；`run_*` 优先于 `end_*`（set_timekeeping.F）；`history_interval_m` 单位=分钟
- **集群实操（三个算例全部真跑通，SUCCESS 原文入文）**：沙箱拷贝 8432 文件/1.3G/17 min → `compile em_les` 69 s（`-j` 上限 20 实测）→ em_les np=4 **113 s**/np=2 129 s/np=1 192 s、em_quarter_ss 51 s、em_b_wave 86 s；**md5 交叉证据**：ch18 wrf.exe md5 = ch05 em_real 基线 md5（e81b5016…）逐位相同；首轮 rc=127（缺链接）与段错误（间歇性）如实入文
- 诊断（轻轨，`workspace/scripts/ch18_diagnose.py`）：les（HFX 0→278.6 W/m²、CBL 顶 1004→1059 m、近地 θ 300→301.5 K）；qss（W max 0/30.18/43.29 m/s、θ′ 近地 min 0.40/−2.35/−7.18 K、RAINNC 0/7.94/36.61 mm）；b_wave（地面 P′ ±0.1→−69.7/+22.8 hPa 指数增长、|u|max 67.3→72.0）
- **重要教学点**：物理全关算例（qss、b_wave）的 `PSFC`/`T2` 恒为 0 → 只能诊断动力学量/微物理量；`frames_per_outfile=1000` 使多帧写同一文件（les 2 帧/qss 3 帧/b_wave 21 帧）
- 同轮修订 ch05：表内 em_grav2d_x 场景与 em_b_wave 边界勘正；§5.6 速查表新增两条（`-j` 上限 20；"几十秒完成"的原因与重编量核实法）
- 图：doc/figs/ch18_les_profiles.png、ch18_qss_storm.png、ch18_bwave.png
- 脚本：workspace/scripts/ch18_diagnose.py；集群脚本 workspace/cluster/ch18/*.sh（四件）；日志 workspace/logs/ch18_diagnose.log
- 下一章：ch19 真实个例全流程实录：兰州 2025-07 高温（全书压轴实验章；含 sf_urban_physics=0 vs 3 双跑）

### ch19 真实个例全流程实录（兰州 2025-07 高温）—— 已核验（2026-10-11，全书压轴实验章）
交付：`doc\ch19_lanzhou_heatwave.md`（408 行；2 mermaid + 4 自算图 + 三跑实录与排错全记录）
- 19.1 个例设计定稿（窗口 2025-07-13~16 的扫描依据；两域 9/3 km 与论文2 同构；CTRL-T 与"城市实验套装"两套物理，含**源码约束驱动设计**）
- 19.2 驱动数据与 WPS 回顾（ERA5 月 GRIB 21 时次；geogrid 43 s / ungrib 40 s / metgrid 122 s；`geog_data_res='default'` 是城市数据缺口的来源）
- 19.3 完整模拟与质控（ch08 439419 基线：2913 s/52 核时、CFL 0 告警、d01 8000 步 mean 0.361 s；**6 条质控清单** + 两条排错教训：栈限制、运行中改脚本）
- 19.4 诊断分析：T-lnP（**修掉"T 是扰动位温"的换算坑**：θ=315.95 K → LCL=LFC=699 hPa、CAPE 2522 J/kg、CIN 0）；T2 vs ERA5（模式偏暖 0.3–2.0 K、07-16 相当）；热岛（3.2–3.7 K）
- **19.5 城市冠层对照实验（本章压轴）**：
  - 数据缺口实测（`URB_PARAM` 全 0、`FRC_URB2D` 不存在、geog 缺 `urbfrac_*`）
  - **三重约束**：① BEP/BEM 仅兼容 bl_pbl∈{1,2,8} ② YSU 需 sfclay=1、BouLac 需 {1,2}（唯一三档通用 = YSU+sfclay1）③ SLUCM 专有检查 `ZDC+Z0C+2 < ZA`，探针实测 类2 = 8.051 m vs ZA 8.046 m **卡阈值**
  - `UTYPE_URB2D` 无输入流标志、默认硬编码类 2 → **单行最小补丁**（类 2→1）→ 沙箱重建 → 200 s 验证 1222 步通过
  - 三跑全部 SUCCESS（439828 =1 / 439810 =0 / 439866 =3）与**两对单变量对照**
  - 差异分析：热岛 3.2–3.7 K；方案净效应域均 |Δ|<0.3 K、局地 ±2–3.5 K、日最高几乎不变；AH 关闭导致"夜间信号缺失"→ 诚实结论指向论文2 参数场
- 19.6 对接论文2（7 维差距表 + 升级路线）；19.7 速查 7 条 + 延伸阅读
- 图：doc/figs/ch19_tlnp.png、ch19_t2_vs_era5.png、ch19_uhi_diurnal.png、ch19_uhi_maps.png
- 脚本：workspace/scripts/ch19_diagnose.py、ch19_gen_main.py、ch19_gen_namelists.py、ch19_probe_urb.py；集群脚本 workspace/cluster/ch19/*.sh（十余件）；日志 workspace/logs/ch19_diagnose.log
- 素材底稿：workspace/context/ch19_material.md（含排错链、补丁版本账、探针数据）
- 下一章：ch20 改造 WRF 三级实战（第三级 = 论文2 BEM 逐格参数场实录；本章的一行补丁正是引子）

### ch20 改造 WRF 三级实战 —— 已核验（2026-10-11）
交付：`doc\ch20_modifying_wrf.md`（含 §20.7.1 全书改造案例总索引 27 案）
- 三级全链实测（构建 439963 → 运行 439976 六跑 rc=0 → 抽取 24 文件 → 诊断 3 图；详见 verify_log ch20 段）
- L1：Registry+start_em+solve_em 三处补丁（T2_PEAK=rhd）；**L1a↔L1b 十二变量位级一致**（非扰动铁证）；ch04 §4.5 六点自检全中
- L2：MYNN GET_PBLH 的 delt_thv 一行（0.5/1.25/2.5）；域均 PBLH 1199/1635/1902 m 单调；逐点违例 0.83–3.10%（稳定层混合）
- L3：ALBROF_2D（i0rh）+ use_bem_2d_albedo 开关 + 五文件传参链（Registry→first_rk_step_part1→surface_driver→noahdrv→bep_bem→BEP1D）；TS_URB 东组开−关时均 −2.85 K（正午 min −6.67 K）、西组（=表值对照）−0.089 K
- 事故链七条（①LD_LIBRARY_PATH 全局污染 ②lsm/lsm_mosaic 锚点 ③陈旧对象 ④Noah-MP 调用点 ⑤容器缺 m4 ⑥Registry 触发门 ⑦容器内 ncks 静默失败 + libnco + DataName=TS_URB）
- 关键方法论沉淀：**Registry DataName ≠ 变量名**（wrfout 用 DataName）；IO 字母串 `rhd=(...)u=(...)` 语法合法；"应当不变"三级检验设计
- 图：doc/figs/ch20_L1_diag.png、ch20_L2_pblh.png、ch20_L3_albedo.png
- 脚本：workspace/scripts/ch20_diagnose.py、ch20_inject_albrof.py；集群脚本 workspace/cluster/ch20/*.sh（patch×3/rebuild2/runall/extract2/fixL3 等）；日志 workspace/logs/ch20_diagnose.log
- 素材底稿：workspace/context/ch20_material.md（三级设计、事故链、输入指纹、构建 v2/v3 全账）
- 同日全书补充：ch01/ch02 交付；ch03–ch19 三类专栏（科研改造案例库/模块依赖树/核心代码）；ch20 §20.7.1 案例总索引
- 下一章：ch21 solve_em.F 全流程（第 V 部）；随后附录 a–d 与 index.md

### ch21 solve_em.F 全流程 —— 已核验（2026-10-11，第 V 部收官章）
交付：`doc\ch21_solve_em_dynamics.md`（技术章六段式 + 三类专栏；3 mermaid；轻轨实验 1 组）
- 源码锚点（全部当次 Read/Grep 实测）：solve_em 5197 行、十四站走读；rk_step_prep/rk_tendency（module_em，14 步装配序）；first_rk_step_part1/2 调用序逐条（物理调用时刻=验收答案）；small_steps 循环五件套（advance_uv/advance_mu_t/advance_w/calc_p_rho/sumflux）；标量四循环；RK 后段（microphysics 在 RK 循环之后——关键修正）；after_all_rk_steps→diagnostics_driver
- 公式↔语句：ADT eqn 44/45（advance_uv 注释）、ADT eqn 47（advance_mu_t 注释）、垂直半隐式（calc_coef_w/advance_w）、状态方程（calc_p_rho/calc_p_rho_phi）；正定修正（positive_definite_slab 逐行读）；WENO（advect_scalar_weno 头注=Jiang & Shu 1996）
- 案例库案 28–35：SKEBS（module_stoch.F 头注=Berner 2011 MWR）、WRF-CMAQ（Wong 2012 GMD）、WRF-Fire（part1 挂点）、MAD-WRF（Registry 包 mp_physics==96 + cloud_tracer_nudge）、use_theta_m（默认 1，big_step 9 分支）、WENO 平流、Polar 滤波（module_polarfft）、IEVA（module_ieva_em）
- 实验：ch21_timestep_audit.py——重演 num_sound_steps 公式与 RK3 步长装配，d01 8000 步/d02 24000 步与 439419 逐位吻合；每步 7 个声波小步
- 依赖树：dyn_em 内核文件级 mermaid（12 文件 + 代表函数清单）；公式↔语句总表（ADT 式号系）
- 图：mermaid ×3（调用链位置/RK3 时序/物理调用序）；脚本 workspace/scripts/ch21_timestep_audit.py、ch21_recon.py；日志 workspace/logs/ch21_timestep_audit.log

### 附录 a–d + index.md —— 已核验（2026-10-11，批次 4 收官）
- app_a：三列对照（书符号↔WRF 代码↔Registry/输出名）+ `module_model_constants.F` 全常数 vs 书附录 C 偏差表（g=9.81 vs 书 9.80665 等）
- app_b：九类术语汇编（ch10–ch17/ch21 术语表 + 工程术语）
- app_c：c.0 万能诊断五步 + c.1–c.8（编译/WPS/real/运行/IO/内核/改造/后处理）+ 兼容性守门员六条；改编自全书各章速查（汇总底稿 workspace/tmp/app_extract_*.md）
- app_d：文献三级标记（核验/通行/线索）+ 数据源（ERA5 致谢 liuyl17、WPS_GEOG）+ 工程资产索引
- index.md：21 章+4 附录总目录（文件名 Glob 核对）、使用说明、三类专栏体例指引、页码换算规则（印刷页 N → page_{N+14}）、阅读路径建议、修订记录
- 全书结构至此完整：第 I–V 部 21 章 + 附录 4 件 + index
