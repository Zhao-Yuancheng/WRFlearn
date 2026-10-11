# ch18 素材与实验底稿（理想实验入门）

时间锚点：2026-10-11 凌晨（自主会话）
章节文件：doc\ch18_ideal_cases.md（六段式，已落 18.0–18.4+18.6/18.7；18.5 实践节待回填）

## 一、本地源码调研（已核验）

### 1. test/em 目录族（15 个）
em_b_wave, em_convrad, em_esmf_exp, em_fire, em_grav2d_x, em_heldsuarez, em_hill2d_x, em_les,
em_quarter_ss, em_real, em_scm_xy, em_seabreeze2d_x, em_squall2d_x, em_squall2d_y, em_tropical_cyclone

### 2. 双钥匙机制（编译期 IDEAL_CASE 全表，顶层 Makefile 实证）
- IDEAL_CASE=ideal：hill2d_x / quarter_ss / convrad / squall2d_x / squall2d_y / grav2d_x / b_wave / seabreeze2d_x / les（9 个）
- IDEAL_CASE=fire → em_fire；=heldsuarez → em_heldsuarez；=scm_xy → em_scm_xy；=tropical_cyclone → em_tropical_cyclone；=real → em_real（含 ndown/tc）
- main/Makefile：`$(SOLVER)_ideal : module_initialize ideal_$(SOLVER).o` → 链接 `module_initialize_$(IDEAL_CASE).o`
- wrf.exe 不链接任何 initialize 模块 → 3D 理想族共用同一份 ideal.exe/wrf.exe

### 3. ideal_case 包机制（Registry 实证）
- Registry.EM_COMMON：`rconfig integer ideal_case namelist,ideal 1 0 rh`（默认 0）
- package 行：realcase=ideal_case==0 … hill2d_x==1 … les==9（10 行，位于 3452–3461）
- 生成物 frame/module_state_description.F（集群实证）：`INTEGER, PARAMETER :: realcase = 0 / hill2d_x = 1 / … / les = 9`

### 4. module_initialize_ideal.F（2252 行）结构
- init_domain（薄封装）→ init_domain_rk（全部逻辑）；尾部：init_module_initialize / get_sounding（1767–1925）/ get_sounding_b_wave（1969–2113）/ read_input_jet（2200–2249）
- 分发点（12 处 SELECT CASE）：ideal_constants / ideal_landmap / ideal_levels / ideal_sounding / ideal_terrain / ideal_pert / ideal_surfacet / trajectories / tracers
- 关键常数：z_scale=8000/ztop；les 用 stretch_grid=.false. → znw 均匀（dz≈51 m）
- ideal_landmap：`CALL nl_set_map_proj(1,0)`；msf*≡1；sina=0/cosa=1/e=0
- f 值：hill2d/quarter_ss/squall/grav2d=0；b_wave=1e-4；les=1e-4；convrad=2.5e-5（xlat=10，全海洋 lu=16）；seabreeze=0（xlat=30，陆 50 点）
- 扰动：quarter_ss 暖泡 +3K（水平 10 km，垂直中心 1.5 km/半径 1.5 km）；grav2d 冷泡 −15℃（x 半径 4 km，垂直中心 3 km/半径 2 km）；les 随机 0.1K×(rand−0.5) 最低 4 层；squall 线状；每扰动后 rebalance hydrostatically
- 表面温度：default 前三层外推 tsk=cf1T1+cf2T2+cf3T3；convrad/les：tsk=θ_surf·(p_surf/1000mb)^κ；tmn=tsk−0.5
- 地形：hill2d_x ht=hm/(1+((i−icm)/xa)²)，hm=100/xa=5；les 预留 MTN/EW_RIDGE/NS_RIDGE（编译期）
- 混合坐标：hybrid_opt=0 → c3=η、c4=0、c1=1、c2=0；另有 1/2/3 分支（ch10 呼应）
- 探空：read_sounding 读 ASCII（首行 p/θ/qv；各行 z/θ(qv g/kg,u,v)）；get_sounding 干湿两遍（湿自下而上 10 次迭代；干自顶向下）；ρ_surf 含虚温 1+0.608qv
- b_wave：read_input_jet 读二进制 input_jet（头 ny_in/nz_in；u/t/ρ 三个 ny×nz 场；zk=125+250(k−1)）；get_sounding_b_wave 中列基态、逐列重构
- ideal_em.F：med_initialdata_output → construct_filename1('wrfinput') → output_input；仅 specified 时写 wrfbdy；`this_is_an_ideal_run=.TRUE.`；打印 SUCCESS COMPLETE IDEAL INIT

### 5. 口径勘正（已写入 ch18 §18.2.2，另修 ch05 表 grav2d_x 行）
- grav2d_x = 密度流（Straka 1993），非"重力波"（已改 ch05 第 386 行）
- em_bubbling 不存在（4.8 test/ 无此目录）
- em_esmf_exp 是耦合实验包，非单机算例
- 2D 算例官方口径 serial+无嵌套（窄向 3 点）
- run_* 优先于 end_*（share/set_timekeeping.F 实证：run_days/hours/minutes/seconds>0 则用 run_*；quarter_ss 的 end_minute=120 被忽略，实际 60 分钟）

### 6. 其他速查素材
- history_interval_m 单位 = MINUTES（Registry/registry.io_boilerplate；4.x 新增 _d/_h/_m/_s）
- compile 脚本 setenv A2DCASE/A1DCASE 但全树无消费者（考证注记）
- ideal_constants CASE DEFAULT 报错原文：'Need to choose valid non-zero ideal_case:  ideal_case = …'
- eta_levels 三条校验（首 1.0 / 末 0.0 / 单调递减）的 fatal 原文
- read_input_jet 维度不符报错：'error in input jet dimensions'
- get_sounding 负压致命错误：'Integrated pressure has gone negative - too cold for chosen height'

## 二、集群实操（执行中）

### 资源布局（侦察）
- IceLake/：ch05_exp ch06_exp ch07_exp ch08_exp ch09_exp lz_case scripts_staging wrf-4.8
- wrf-4.8/：build cases configure.log env-deps-oneapi.sh env-wrf-oneapi.sh image-stage install-oneapi log.rebuild-wps scripts sources tools
- 构建树 build/WRF（em_real 构建；对象已清空=0；exe 4 个在 main/，Oct 10 15:27）
- 参考模板：ch08_exp/ch08_wrf_outer.sh + inner（sbatch -c64 → exec singularity exec --bind /users,/data oneapi.sif bash inner）
- env-wrf-oneapi.sh：source oneapi setvars；NETCDF/PNETCDF/GRIB2/JASPERLIB 等；I_MPI_* 用 ifx
- 速率教训：小文件多的 NFS 拷贝极慢（8432 文件 ~17 分钟，~8 files/s）

### ch18 作业 1（439699，cpu104）——第一轮：编译成功、运行链路修复过程
- 脚本：ch18_exp/ch18_outer.sh + ch18_inner.sh（本地 staging：workspace\cluster\ch18\）
- 流程：cp -a build/WRF → ch18_exp/WRF-ideal（03:26:45 完成，1.3G，8432 文件）→ tcsh ./compile em_les -j 64 → 顺序跑三算例
- **重要事实修正#1：源树本就带全部 .o**（此前"对象已清空"为路径笔误假象）→ 拷贝后 `compile em_les` 实为"重链接级增量"：**69 s**，产物 main/wrf.exe（Oct 11 03:27，md5 e81b501625f9587635de53dfc0470a0e）+ main/ideal.exe（3b4cf57cc4da0143a17839199a350f4d）；real/ndown/tc.exe 未动
- **重要事实修正#2：4.8 的 compile 脚本 -j 上限 20**：`-j 64` 被拒（echo "badly formed -j option ... above 20"）→ 回退 `-j 2`（compile 源码实证）。正是"真正编译的新对象很少"才让 69 s 成立
- **重要事实修正#3：跨算例"装目录"证据**：`./compile em_les` 只在 test/em_les/ 建可执行链接；test/em_quarter_ss、test/em_b_wave 目录**没有** ideal.exe/wrf.exe → 首轮 quarter_ss/b_wave 报 `execvp error on file ./ideal.exe (No such file or directory)`、rc=127。→ 官方"每算例要 compile"的真实作用确认为"装配目录"，与 §18.3 结论吻合（第二轮手动 ln -sf 后全部可跑）
- 首轮 em_les：ideal rc=0、wrf rc=255，**np=4 段错误（所有 4 个 rank 同时在起步后崩溃）**，已写 wrfout t=0 一帧
  - 旁证两则：① `Max map factor in domain 1 = 0.00` 打印来自 dyn_em/start_em.F 读 `grid%msft`（MAPFAC_M），hill2d/quarter_ss/squall/grav2d/b_wave/**les** 分支都只设 msftx/msfty 家族、不设 msft（仅 convrad/seabreeze/scm_xy/tropical_cyclone 设）——**属正常现象**；且 couple_momentum 的哑元 msft 实参为 msfty（module_em.F 调用处实证），动力学不受影响 ② 与 ch08 记录的"np64 间歇段错误"同类

### ch18 作业 2（439708，cpu128）——第二轮：链接修复 + np 扫描
- 脚本：ch18_exp/ch18_outer2.sh + ch18_inner2.sh
- 三目录链接（readlink 实证）：wrf.exe→../../main/wrf.exe、ideal.exe→../../main/ideal.exe
- **em_les np=4 重跑：成功！** ideal rc=0  wrf rc=0  elapsed=113s；SUCCESS 行 `d01 0001-01-01_01:00:00 wrf: SUCCESS COMPLETE WRF`；步进 ~0.0183 s/步（np4，3600 步）；输出 wrfout t=0 与 t=1h + 末帧 restart（restart_interval_m=60 命中）
- mpirun=Intel MPI 2021.18.0
- （待填：les np=1/np=2、quarter_ss np=4、b_wave np=4 结果）

### 待办（回填 18.5）
- [x] 编译耗时与产物（69s、rc=0、md5、-j 上限 20 修正）
- [x] em_les：SUCCESS + 113s（np4）
- [ ] em_quarter_ss、em_b_wave 结果（第二轮作业中）
- [ ] 跨算例同一二进制证据（链接 readlink + md5）
- [ ] 拉取产物到本地 → 诊断图（doc/figs/ch18_*.png）
- [ ] 机时账表
- [ ] 18.5.2 文字修正：不写" -j 64"，写 -j 上限与回退事实；说明本树自带对象导致 69 s 增量