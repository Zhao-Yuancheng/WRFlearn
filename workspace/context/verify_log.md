# Verify Log — 查证留痕（追加式）

> 格式：日期 ｜ 主题 ｜ 来源 ｜ 一句话结论
> 本文件是"事实核验协议"（方案 v2 §4.1）的留痕，供后续章节复用，避免重复查证。

## 2026-10-10（ch03 写作轮）

### 调用链（全部源码实测，`source\WRFv4.8.0\WRFV4.8.0\`）
- `main/wrf.F` → `PROGRAM wrf`：调用顺序 wrf_init → wrf_dfi → wrf_run → wrf_finalize（都来自 module_wrf_top）
- `main/module_wrf_top.F` → `wrf_run` 仅做 `CALL integrate(head_grid)`
- `frame/module_integrate.F` → `integrate` 是递归子程序；骨架：IF not stoptime → DO WHILE not stopsubtime → med_setup_step → 开嵌套域循环(nests_to_open/alloc_and_configure_domain/Setup_Timekeeping/med_nest_initial) → med_before_solve_io → 对 siblings 循环: solve_interface + domain_clockadvance → med_calc_model_time → med_after_solve_io → 子域循环: med_nest_force + 递归 integrate + med_nest_feedback → med_endup_step → 最后 med_last_solve_io
- `share/solve_interface.F` → `solve_interface`（80 行，文件头 `!WRF:MEDIATION_LAYER:ADT_BARRIER`）：model_to_grid_config_rec → set_scalar_indices_from_config → solve_em（实参经 `actual_new_args.inc` 展开）
- `dyn_em/solve_em.F` → `SUBROUTINE solve_em`（第 3 行）… `END`（第 5197 行），约 5200 行
- `main/module_wrf_top.F` wrf_init 六步：program_name 设置 → init_modules(1) → WRFU_Initialize(WRFU_CAL_GREGORIAN) → init_modules(2) → initial_config（dmpar 时 monitor 读 + get_config_as_buffer/bcast/set_config_as_buffer）→ setup_physics_suite/set_derived_rconfigs/check_nml_consistency/set_physics_rconfigs → wrf_dm_initialize → …（后续 domain 分配）

### PROGRAM 名实测（main/*.F）
- `wrf.F`=wrf ｜ `real_em.F`=**real_data** ｜ `tc_em.F`=**tc_data** ｜ `ndown_em.F`=ndown_em ｜ `ideal_em.F`=ideal ｜ `convert_em.F`=convert_data ｜ `real_nmm.F`=real_data（同名）｜ `ideal_nmm.F`=ideal_nmm
- 结论：real/tc 的程序名与文件名不同（易错点，已写进教材）

### 版本机制
- `inc/version_decl`：`CHARACTER (LEN=*), PARAMETER :: release_version = 'V4.8.0'`
- module_wrf_top 里 `program_name = "WRF " // TRIM(release_version) // " MODEL"`

### 中介层（mediation）
- 接口声明在 `frame/module_integrate.F`（INTERFACE block），实现在 `share/mediation_integrate.F`
- `share/mediation_integrate.F` 子程序表（42 个）：med_calc_model_time / med_before_solve_io / med_after_solve_io / med_last_solve_io / med_pre_nest_initial / med_nest_initial / med_interp_domain / med_nest_feedback / med_nest_force / med_setup_step / med_endup_step / med_hist_out / med_auxinput_in / med_fddaobs_in 等
- `share/mediation_wrfmain.F`：med_initialdata_input(_ptr) / med_shutdown_io( 递归 _recurse) / med_add_config_info_to_grid

### 目录树与产物（本地实测）
- 顶层目录：arch chem cmake dyn_em external frame hydro inc main phys Registry run share test tools var wrftladj confcheck（+构建脚本 configure/compile/configure_new/compile_new/clean 等）
- `test/` 15 个算例目录：em_b_wave em_convrad em_esmf_exp em_fire em_grav2d_x em_heldsuarez em_hill2d_x em_les em_quarter_ss em_real em_scm_xy em_seabreeze2d_x em_squall2d_x em_squall2d_y em_tropical_cyclone
- `test/em_real/` 含 namelist.input 及变体（.4km/.chem/.fire/.global/.ndown_1-3/.pbl-les/.IEVA.4km 等）+ examples.namelist + run_{1way,2way,restart}.tar
- `test/em_les/` 含 input_sounding 系列 + namelist.input(.SGP/.shalconv)
- `run/` 93 文件：namelist.input、README.namelist、TBL 系（VEGPARM/SOILPARM/LANDUSE/GENPARM/URBPARM*.TBL/NoahmpTable.TBL/HLC.TBL）、辐射数据（RRTMG_*_DATA/RRTM_DATA/CAM_ABS_DATA）、微物理查找表（p3_lookupTable_*/ETAMPNEW_DATA/ishmael-*）、rsl.out/error.0000 样例、wrf.exe/real.exe 拷贝等
- `arch/`：Config.pl、configure.defaults、configure_reader.py、preamble、postamble、noopt_exceptions(_f)、md_calls.inc、Externals.cfg 等
- `cmake/`：modules/、template/、wrf_case_setup.cmake、wrf_get_version.cmake、confcheck.cmake 等
- 构建脚本：`configure`(sh, 调 arch/Config.pl 读 configure.defaults)→`configure.wrf`；`compile`(csh)；`configure_new`(CMake, 支持 -p/-x/-d/-i/-- 选项)→`compile_new`（默认 `_build/` 目录，跑 cmake+make install）

### 集群实测（`/users/zhyuancheng2025/IceLake/wrf-4.8/build/WRF`，2026-10-04 构建）
- main/*.exe：wrf.exe 82647976 ｜ ndown.exe 69930960 ｜ real.exe 53715896 ｜ tc.exe 52305920
- **`ldd main/wrf.exe` 报 "not a dynamic executable"（登录节点误报）**；`file` 报 dynamically linked；`readelf -d` NEEDED：libnetcdff.so.7 / libnetcdf.so.19 / libpnetcdf.so.7 / libimf.so / libm.so.6 等 39 条 → 动态链接、启用 PnetCDF（io_form=11 可用）
- `configure.wrf` 实测行：FCOPTIM = `-O3 -xCORE-AVX512 -mprefer-vector-width=512`；FCBASEOPTS_NO_G 含 `-finline-functions -fp-model precise -w -ftz -align all -fno-alias`；LDFLAGS_LOCAL = `-xCORE-AVX512`；无 -static
- run/ 目录含 rsl.out.0000/rsl.error.0000（曾在 run/ 内执行过 wrf.exe）

### 待办核验（后续章节）
- [x] Registry 生成物在集群构建目录里的实际位置与形式（ch04 实测用）→ 已完成（见下节）
- [ ] `frame/module_domain.F` 的 domain 类型字段全景（ch21 用；ch04 已核验 state_struct.inc 由 module_domain_type.F include）
- [ ] `init_modules` 的实现位置与机制（ch09 用）
- [ ] `wrf_dm_initialize` / quilt 进程分配详情（ch09 用）

## 2026-10-10（ch04 写作轮）

### 记录结构与统计（本地源码）
- Registry.EM_COMMON 3727 行；起首 token 计数：state≈1678、rconfig≈799、package 280、halo 83、typedef 52、i1 43、period 33、xpose 14；Registry.EM 48 行；registry.dimspec 100 条 dimspec
- state 表格式（文件头注释）：`<Table> <Type> <Sym> <Dims> <Use> <NumTLev> <Stagger> <IO> <DNAME> <DESCRIP> <UNITS>`；维度串末尾 b/f/t 为修饰符（注释原文）
- 顺序陷阱注释：LU_INDEX 须先于掩膜插值变量；znu/znw/dzs/zs 须先于任何 3D 场（GRIB 输出依赖）
- rconfig 字段（reg_parse.c 的 RCNF_* 定义）：type/sym/howset/nentries/default/io/dname/descrip/units；`namelist,<组>` 决定 NAMELIST 组；max_domains 生成数组 + 越界检查
- package 记录：`package thompson mp_physics==8 - moist:qv,...;scalar:qni,qnr;state:...`；生成 module_state_description.F 的包常量（thompson=8 等）
- 4D 数组族：`state real - ikjftb tracer 1 - -` 定义族（名取 Use 列），成员记录 Use 填族名（Registry.EM 的 tracer/tr17_* 实测）

### IO 语法（reg_parse.c + inc/streams.h + 生成物）
- 解析：i/h 后跟数字或{unitid}设位（INPUT_STREAM=HISTORY_STREAM+MAX_HISTORY）；r→RESTART_STREAM 位 + restart 标志；b→BOUNDARY_STREAM；f/d/u/s→FORCE_DOWN/INTERP_DOWN/SMOOTH_UP/INTERP_UP，可 `=(fcn:aux)`
- inc/streams.h：HISTORY_STREAM=0、INPUT_STREAM=+MAX_HISTORY、MAX_STREAMS=2*MH+2、BOUNDARY_STREAM=2*MH+1、RESTART_STREAM=2*MH+2、IO_MASK_SIZE
- arch/preamble：MAX_HISTORY=25；集群 configure.wrf 实测该值进入 tools 编译宏（-DMAX_HISTORY）
- 生成物 inc/switches_and_alarms.inc：history_only=1、auxhist1_only=2…auxhist24_only=25、input_only=26、auxinput1_only=27…auxinput24_only=50（frame/module_streams.F 定义 restart_only=2*MH+1、boundary_only=2*MH+2）
- auxhist22/23 身份：share/module_check_a_mundo.F 报错文案 "z_lev_diags requires auxhist22"/"p_lev_diags requires auxhist23"；run/README.namelist 注明 auxhist[1-24]/auxinput[2-24]
- T2 记录 `i01rh01{22}{23}du` 全解（含 Q2/U10/V10/XLAT/XLONG 同族）

### 生成链路（本地脚本 + 集群构建树实测）
- configure.wrf：`REGISTRY = Registry`；ARCHFLAGS=COREDEFS(-DEM_CORE/-DNMM_CORE/-DDA_CORE/-DWRFPLUS)+IWORDSIZE 等；ENVCOMPDEFS 为空
- compile 脚本（EM+非DA/Chem 分支）：从 Registry.EM 合成 Registry/Registry（首行 '## WARNING: this file is autogenerated from Registry/Registry.EM. Changes may be lost' + cat）；含 mtime 过期检查
- frame/Makefile：`module_state_description.F : ../Registry/$(REGISTRY)` → `( cd .. ; tools/registry $(ARCHFLAGS) $(ENVCOMPDEFS) -DNEW_BDYS Registry/Registry ; true )`
- cmake：tools/CMakeLists.txt 行 `${CMAKE_BINARY_DIR}/tools/registry ${REGISTRY_DEFS} -DNEW_BDYS ${REGISTRY_FILE} > registry.log`
- registry.c main 流水线顺序（pre_parse→reg_parse→check_dimspecs→gen_* 系列）；选项：-DDM_PARALLEL/-DNEW_BDYS/-DWRF_CHEM/-DLIMIT_ARGS/-DDEREF_KLUDGE 等；obsolete 选项打印警告继续
- gen_io_boilerplate 先生成 io_boilerplate_temporary.inc（被 registry.io_boilerplate include）
- 生成物数量（集群 build/WRF）：inc/*.inc=480；allocs_0..31.F（32 片）+ allocs.inc + allocs_calls.inc；deallocs_0..11.F（12 片）；nl_config.inc（32663 行、2330 对 nl_get/nl_set 唯一名）；frame/module_state_description.F（包常量行 + 4D 常量 PARAM_NUM_moist=13、PARAM_tr17_1=3、PARAM_FIRST_SCALAR=2）
- nl 访问器分片：nl_config.inc 的 #ifdef NL_get_ROUTINES/#if (NNN==0) 机制；frame/Makefile 用 cpp -DNNN=0..7 生成 8+8 片；源码树与构建树的 frame/nl_get_0_routines.F 均为 `dummy; make needs this to be happy` 占位
- gen_comms 来源：tools/Makefile 有 gen_comms.c:gen_comms.stub 兜底；arch/postamble gen_comms_rsllite 规则拼接 tools/gen_comms_warning + external/RSL_LITE/gen_comms.c（集群 tools/gen_comms.c=14 万余字节）
- 生成物防伪：misc.c print_warning/close_the_file → STARTOF/ENDOFREGISTRYGENERATEDINCLUDE + "by use_registry"（历史名）
- 生成物 include 点实测：module_domain_type.F（state_subtypes.inc/state_struct.inc）、module_driver_constants.F（model_data_order.inc）、module_domain.F 的 alloc_space_field（allocs.inc/allocs_calls.inc）与 dealloc_space_field（deallocs.inc）、solve_em.F（i1_decl.inc）、solve_interface.F/dfi.F/mediation_*.F（actual_new_args.inc）、wrf_bdyin.F/wrf_bdyout.F（wrf_bdyin.inc/wrf_bdyout.inc）
- 实参文件：gen_args.c 注释 "only generate actual args for the 4d arrays"（*_new 版 only4d）+ "short circuit any field that is not state"（i1 短路）；实测 actual_new_args=59、actual_args=2749（EM 主路径未发现 actual_args.inc 的 include 点）
- 状态表元数据样板：allocs_23.F 的 ru_tendf_stoch（VarName/DataName/Units/MemoryOrder/Stagger/Ntl/Ndim/Restart/rfield_3d/streams(*) 位/sd1..）——ch09 伏笔
- t2 分配样板在 allocs_1.F（in_use_for_config(id,'t2') 守卫 + 字节统计）；state_struct.inc 实测 `real ,DIMENSION(:,:) ,POINTER :: t2`
- in_use_for_config 机制：module_configure.F 按首字母分发 26 个生成文件；样例 in_use_for_config_q.inc（qnwfa2d ↔ mp_physics(id).EQ.28）

### 勘误与同步
- ch03 第 3.2.5 节的两处表述已修正（actual_new_args 实为 59 项附加实参；"上千参数"对应旧 actual_args.inc），ch03 生成物表同步更新

## 2026-10-10（ch05 写作轮 + ch06 素材轮）

### ch05 编译体系（本地源码 + 集群 dry-run/编译实测）
- `compile`（tcsh）命令行分发：`em_real`→ZAP＝4 个 exe；`em_*`→ZAP＝wrf.exe+ideal.exe；构建前 `/bin/rm -f $ZAP`（先删后建，失败即空窗）
- Registry 合成段：只比较 **Registry.EM** 的 mtime（`grep -w 'Registry\.EM' | grep -v 'Registry.EM.'` + `ls -1tr` 序号比较）；`em_time > rg_time` 才重写 `Registry/Registry`（首行 warning + `cat Registry.EM`）
- include 链：`Registry.EM` → `registry.dimspec` + `registry.em_shared_collection` → 后者首行 `include Registry.EM_COMMON`（+io_boilerplate/fire/avgflx/stoch/les/cam/clm/lake/ssib/noahmp/sbm/polrad/afwa/rasm_diag/elec/bdy_perturb）
- configure.wrf 实测：`REGISTRY = Registry`；`SFC = ifx`；`FC = $(DM_FC)`
- 触发陷阱实测（集群 dry-run，`make -n -i -r em_real`）：仅改 Registry.EM_COMMON → dry-run 中 tools/registry 命令数 **0**；`touch Registry/Registry` 后 → 非 0（命令行在 dry-run 输出第 57304 行）
- 顶层 Makefile：`em_real : wrf` 目标（删 main/ 四 exe → cd main 构建 → test/em_real 符号链接）
- A1（rrtmg_lw.F 加注释）：81 s、12 对象重编（rrtmg_lw/radiation_driver/physics_init/cu_kfcup/microphysics_driver/mixactivate/rrtmg_sw/madwrf/cumulus_driver/first_rk_step_part1/start_em/solve_em）、.o 与 4 个 exe md5 全同基线
- A2（还原）：45 s、4 对象重编（madwrf/cumulus_driver/first_rk_step_part1/solve_em）、exe md5 全同
- B1（touch+T2_PEAK）：649 s、224 对象；证据：state_struct.inc `t2_peak` 指针、allocs_14.F `in_use_for_config(id,'t2_peak')` 与 `DataName='T2_PEAK'`；exe md5 变化（be8d09e4…）
- B2（还原）：649 s、224 对象；4 个 exe 与 4 个抽查生成物（state_struct.inc/allocs_1.F/module_state_description.F/i1_decl.inc）md5 全同原始
- cmake 路线（本地源码）：configure_new(sh) 调 `arch/configure_reader.py -c arch/configure.defaults -t cmake/template/arch_config.cmake -o _build/wrf_config.cmake` → `cmake .. -DCMAKE_INSTALL_PREFIX=<install> -DCMAKE_TOOLCHAIN_FILE=<build>/wrf_config.cmake`；产物无 .exe 后缀、安装到 install/bin 与 install/test/<case>
- CMakeLists.txt 选项全集：WRF_CORE{ARW,CONVERT,DA,DA_4D_VAR,PLUS}、WRF_NESTING{NONE,BASIC,MOVES,VORTEX}、WRF_CASE{EM_REAL 默认+EM_FIRE/SCM_XY/TROPICAL_CYCLONE/HELDSUAREZ/B_WAVE/GRAV2D_X/HILL2D_X/LES/QUARTER_SS/SEABREEZE2D_X/CONVRAD/SQUALL2D_X/SQUALL2D_Y/NONE}；USE_* 8 个（DOUBLE/MPI/OPENMP/HDF5/JASPER/PIO/IPO/PNETCDF）；ENABLE_* 12 个；MAX_DOMAINS_F=21、CONFIG_BUF_LEN=65536、MAX_HISTORY=25；cmake≥3.20；netCDF 走 `nc-config`/`*_ROOT`
- test/em 全表：15 目录（14 算例含 namelist.input + em_esmf_exp 耦合包）；em_fire 时步=0+1/2（分数时步语法）；各算例 dx/dim/dt/时长/物理开关全量提取（入 ch05 表）
- **物理套装机制**：`share/module_check_a_mundo.F` 的 `setup_physics_suite`——`physics_suite='CONUS'` 时把仍为 -1 的项替换（cu=Tiedtke/mp=Thompson/ra=RRTMG×2/pbl=MYJ/sfclay=MYJ/surface=Noah）；'tropical'（cu=NTiedtke/mp=WSM6/bl=YSU/sfclay=revMM5）；'none' 直用；未识别→fatal

### WPS 4.7.0（本地源码 + 集群两轮实录）
- ungrib 窗口机制：`ungrib/src/read_namelist.F` 读 `&share` 的 start_date(1)/end_date(1)（start_date 优先于 start_year 多变量方式）；校验 interval 整除 (hend−hstart)；`ntimes=idts/interval+1`；`ungrib.F` 主循环 `hdate>hend` 提前退出（ordered_by_date=.TRUE.）→ 整月 4.3 GB GRIB 仅解码窗口内 21 时刻；收尾 `datint.F` 对缺失时次时间插值补齐（必打印 "Subroutine DATINT…"，勿误判为错）
- 中间文件（FILE:）格式：Fortran 无格式顺序记录；版本号=5（WPS）/[4=SI/3=MM5]；主记录 `hdate(24) xfcst map_source(32) field(9) units(25) desc(46) xlvl nx ny iproj`；投影记录含 r_earth（lat-lon: startloc+lat1+lon1+dy+dx+r_earth）；写出在 ungrib/src/output.F 与 datint.F
- **非气压类层号编码（200100）**：`rd_grib1.F` 对 ktype∈{1,105,111,112,116} 令 `level=200000+iprty`；`parse_table.F` 默认 `iprty=100`（105/118/116 按行计数）→ 地面/土层/高度类字段在中间文件中层号=**200100**；故 METGRID.TBL 的 `fill_lev = 7 : ST000007(200100)` 中括号数字=源字段层号（`get_fill_src_level` 实证 "level in source field must be an integer"）；output.F 跳过 (200100,200200) 区间层（低优先高度层）
- METGRID.TBL 结构：`name/z_dim_name/derived=yes/fill_lev（目标层:源字段(源层)）/interp_option/mask/flag_in_output`；派生字段 ST/SM/SW 的 IF/ELSE IF 分支对应不同驱动集（GFS 4 层/ECMWF 4 层=7,28,100,289/3 层/2 层）
- GEOGRID.TBL.ARW：`name/priority/dest_type/interp_option=<source>:<方法>/rel_path=<source>:<目录>`；geog_data_res 按 source 关键字选（default 关键字已解析）；城市字段：URB_PARAM（priority1→NUDAPT44_1km、priority2→gloucp2020_30s）、FRC_URB2D（nlcd2011→gaia2020_30s）；geo_em 含 `num_urb_params=132` 维
- Vtable.ECMWF 全表：气压层 129=GEOPT/156=HGT/130=TT/131=UU/132=VV/157=RH；地面 165/166=10m 风、167=2m T、168=2m Td、172=LANDSEA、134=PSFC、151=PMSL、235=SKINTEMP、31=SEAICE、34=SST、141=SNOW；土层 112 型：139/170/183/236=ST 四层、39/40/41/42=SM 四层（注释指明 snow 单位换算在 rrpr.F）
- 兰州个例 WPS 实录（两轮）：v1 域 120×100/250×220 弃用（与论文2 不符）；**v2 域 d01 90×90@9km + d02 112×112@3km（truelat 35/45）**：geogrid 16 s、ungrib 42 s、metgrid（mpirun -np 8）94 s；42 个 met_em（21 时刻×2 域）；geo_em.d01 89×89、met_em `num_metgrid_levels=32`、`num_st_layers=4`、`num_sm_layers=4`
- ERA5 源数据：liuyl17/ERA5_2025（ERA5202507.grib 4.35 GB + ERA5_surface.202507.grib 443 MB，均为整月、00/06/12/18Z、区域 [65N,60E]-[0N,150E]）

### 参考个例 haidian2024（liuyl17，模板用）
- namelist.input：4 域（77²@3km+64²@1km+121²@1km+101²@200m）、e_vert=41、**显式 eta_levels（41 值，1.000→0.000，首 Δη=0.002≈16 m）**、p_top=5000、num_metgrid_levels=32（同 32 层 ERA5）、dt=18 s、physics_suite='CONUS' 但各项显式（mp=3/cu=1/ra=1,1/bl=1/sfclay=1/surface=1）、num_land_cat=20、hybrid_opt=2、diff_opt=1/km_opt=4
- wrfout 体量标定：76×76×40 域 33 帧=1.01 GB（≈30 MB/帧）→ 用于 ch08 输出规划

### ch07 个例配置（本教材定稿，2026-10-10）
- namelist.input：两域 90²@9km + 112²@3km、e_vert=50、**eta_levels 50 值（Δη0=0.002→首层≈16 m、growth 1.12、cap 0.030556≈249 m，脚本 workspace/scripts/gen_eta_levels.py）**、p_top=5000、dt=54 s（1:3）、物理 mp=8(Thompson)/ra=4,4(RRTMG)/sfclay=5(revMYNN)/surface=2(Noah)/bl=5(MYNN2.5)/cu=1,0(KF 仅 d01)、sf_urban=0、hybrid_opt=2、damp_opt=3、gwd_opt=0、history 180/60 min、frames 1000/25
- 运行目录：`cases/lanzhou2025/wrf/`（exe 与 run/ 数据文件全符号链接、met_em 链接自 wps/）；作业 ch07_real=439395

## 2026-10-10（ch08 写作轮：5 天生产 + restart 实验 + 排错重案）

### 生产运行 439419（全部实测）
- rc=0、elapsed=2913 s（48.5 min）；`SUCCESS COMPLETE WRF` 在 rsl.out.0000 第 32348 行；d01 8000 步（mean 0.361 / min 0.264 / max 7.13 首步）、d02 24000 步（mean 0.0838）；主循环步时与墙钟 8000×0.361≈2888 s 自洽
- 写盘计时：d01 41 次（0.73–0.80 s）、d02 121 次（1.05–1.2 s，滚动换文件 4 次 ≈2.5 s：07-13_01/07-14_02/07-15_03/07-16_04）；边界处理 20 次
- 产物：wrfout_d01 单文件 940,481,422 B（41 帧追加）；wrfout_d02 五文件 817,310,734/842,950,907/846,945,591/866,780,489/753,151,068 B；case 5.2 GB；64 核×0.809 h≈52 核时
- **无 wrfrst**：restart_interval=86400（分钟制）=60 天 → 闹钟未响（见下）

### restart 语义与实验（源码 + 实测）
- `Registry/registry.io_boilerplate`：`rconfig restart_interval … "MINUTES"`；`restart_interval_d/_h/_m/_s`（D/H/M/S 分量，_m 缺省回落）；`set_timekeeping.F` 注释 "means minutes"；闹钟创建 = `domain_alarm_create(grid, RESTART_ALARM, interval)`（RingInterval 模式）
- 写盘入口：`mediate_integrate.F` 的 `med_before_solve_io`（EM 分支）/`med_last_solve_io` 查铃响 → `grid%id==1` 才 `med_restart_out`；后者**递归**子域（源码注释 "call recursively for children"）
- 事故 A（439398）：restart=.true. 无 rst → rc=1、25 s、FATAL "error opening wrfrst_d01_2025-07-12_00:00:00 for reading"（留档 ch08_exp/rsl.error.failed_restart.0000）
- 单位对照（439460）：rst1（_s=300）与 rst1b（interval=5 min）产物完全一致 → wrfrst_d01_2025-07-12_00:05:24（76,219,056 B）与 _00:10:48（76,103,701 B）；写 rst 计时 3.41/3.38 s（rst1）、3.10/2.72 s（rst1b）；**rst 时间戳对齐步长**（00:05:00 闹钟 → 00:05:24 落盘）
- rst 解剖（本地 netCDF4 拉回）：660 变量（U_1/U_2、THM_1/THM_2 双时间层；TSLB 4 层）；属性 FLAG_RESTART=1、SIMULATION_START_DATE、方案配置（DT/MP_PHYSICS=8/BL=5…）、**闹钟元数据** MAX_WRF_ALARMS=55 + WRF_ALARM_ISRINGING_NN/WRF_ALARM_SECS_TIL_NEXT_RING_NN（RESTART_ALARM=51 号：ISRINGING=1、NEXT_RING=276 s；未用闹钟=1700000000≈54 年=forever）；写入/读回代码在 share/output_wrf.F 与 share/input_wrf.F
- 续跑（439483，np8）：restart=.true. + start=00:05:24 + 双值 end_minute → rc=0、48 s；日志含 "RESTART run: opening…"/"RESTART: nest, opening wrfrst_d02…"、读盘 1.75/2.19 s、LBC 时段核对成功、SUCCESS；**续跑仍写 rst**（00:10:48 两域，2.75/4.50 s，与闹钟元数据 276 s 推算完全吻合）

### 短测代表性事故（重大发现，源码 + 实测）
- 现象：全部 10 分钟短测 rsl 中 domain 2 行数=0（未跑嵌套域）
- 根因：`frame/module_nesting.F` `nests_to_open`：激活条件 `nest_start ≤ now` 且 **`nest_stop > now`**，时间取该域 end_* 数组；短测 namelist 的 `end_minute=10` 单值 → d02 的 end_minute 默认 0 → nest_stop=起报时刻 → 永不激活
- 修复实验（439479）：`end_minute = 10, 10` 后 np64 真两域短测 rc=0、62 s（d02 36 步、双域 wrfout+rst）；np8 对照 61 s；np64 段错误（439402，addr2line→radiation_driver）此后未复现

## 2026-10-10（ch09 写作轮：IO 实验全部实测）

### io_form 编码与包清单（源码）
- `frame/module_io.F`：函数头注释三前缀 wrf_/ext_/wrf_quilt_；`use_package=MOD(io_form,100)`；`multi_files=(io_form≥100 且 <200)`（+100=每进程一文件、读回需同进程数、不能配 quilt；+200=单文件但禁 IO 服务器）
- 包号清单 = `Registry/Registry.EM_COMMON` package 块（io_intio=1/io_netcdf=2/io_hdf=3/io_phdf5=4/io_grib1=5/io_esmf=7/io_yyy=8/io_zzz=9/io_grib2=10/io_pnetcdf=11/io_pio=12/io_netcdfpar=13/io_adios2=14；注释 "Placeholders…HDF has not been implemented"）→ 生成小写常量到 `frame/module_state_description.F` → md_calls `USE module_state_description`
- `use_netcdf_classic` = &time_control rconfig（registry.io_boilerplate，默认 .false.）；module_io.F 存入 SysDepInfo 传给包

### 五写法对照实验（439442+439455，np8、10 min、d01）
| 变体 | 首写/二写 | 产物 | 魔数 | 大小 |
|---|---|---|---|---|
| io2 | 1.92/0.685 s | 1 文件（2 帧） | 89 48 44 46 | 34,685,623 |
| io11 | 2.23/2.08 s | 1 文件（名-冒号→下划线） | 43 44 46 02 | 93,673,384 |
| io102 | 1.89/0.102 s | 8 补丁 _0000.._0007 | 89 48 44 46 | 合计≈43.0 MB |
| io2q | 1.52/0.0237 s | 1 文件；"1 groups of 1 I/O tasks"；分解 1×7 | 89 48 44 46 | 34,685,623 |
| io2c | 0.251/0.0666 s | 1 文件 | 43 44 46 02 | 93,673,228 |

### 源码机制（io_netcdf / io_pnetcdf）
- ext_ncd_open_for_write_begin：USE_NETCDF4_FEATURES 下默认 `create_mode=nf_netcdf4` + NF_SET_CHUNK_CACHE(32000000,37,100)；classic→IOR(NF_CLOBBER,NF_64BIT_OFFSET)
- ext_ncd_write_field：NF_DEF_VAR_CHUNKING + **NF_DEF_VAR_DEFLATE(NCID,VarID,1,1,compression_level=2)**（zlib-2+shuffle）
- io_pnetcdf：文件名 ':'→'_'（'-' 改写已注释掉的"; 注释 'Remove the dash/underscore change…'）；NFMPI_CREATE(…,NF_64BIT_OFFSET)=CDF-2；NFMPI_SET_FILL(NF_NOFILL)
- quilt：&namelist_quilt 自读（module_io_quilt_old.F NAMELIST 语句，默认 nio_tasks_per_group=0=关；README.namelist 同）；头注：重叠输出、1 个服务器常够、nio_groups 必须 1、PHDF5/MCEL 不支持

### 本地解剖（四样本，WRFlearn netCDF4 1.7.4）
- 全网格文件：218 变量；Time=2（Times=2025-07-12_00:00:00 / 00:10:48）；bt=49/bt_stag=50/we=sn=89/soil=4/DateStrLen=19；TITLE/START_DATE/GRID_ID/DX/MAP_PROJ=1；T2 filters zlib+shuffle+complevel2，chunking [1,45,45]
- 净数据 2 帧×46.81 MB：classic 93.67 MB（≈零开销）vs netCDF4 34.69 MB（压缩省 63%）
- io102 补丁：44×22、WEST-EAST_PATCH_START_UNSTAG=46、chunking [1,11,22]

## 2026-10-10（ch10 写作轮：批次 2 首章，全部实测）

### 书页核对（扫描页直读，符号/公式编号按书）
- 目录页：第三章 p30–46（3.1 p30、3.1.2 p31、3.1.3 p32、3.2 p33–35、3.3 p35、3.4 p37、3.5 p41）；第四章 p48–60（4.1 p48–55、4.2 p55、4.3 p56）
- 关键公式实录：3.1.1 −(1/ρ)∂p/∂z=g；3.1.2 ∂p/∂z=−ρg；3.1.3 dp/dz=−ρg；3.1.4 dp/p=−g/(RdTv)dz；3.1.5 Gz≈3.42p/Tv；3.1.6 −dz/dp≈8000(1+αtv)/p；3.1.7 压高积分；3.1.8 z差积分；3.1.9 p=∫ρgdz；3.1.10/11 标高定义；3.1.13 Hp=29.27Tv；3.1.14/15；等温 3.2.1–3.2.4（含拉普拉斯 18410）；多元 3.2.6–3.2.10（上界 Tv0/Γ）；均质 3.2.11–3.2.12（H=p0/ρg；Γ=g/R=34.2）；3.3.6–3.3.14（dΦ=g0dZ、Z 公式、优点①②）；4.2.1–4.2.3（m0=p0/g=10044 kg/m²@g=9.8,p0=985hPa；总质量 5.12×10¹⁵ t；占 3/4 于对流层）；表 3.1（1000hPa 0℃→8.0 m/hPa 等）
- 例 3.1（本站气压→海平面订正，拉普拉斯方程应用，p33–34）；对流层顶判据 2 K/km；匀和层 Md=28.964e-3 kg/mol

### 源码核对（全部本地）
- `dyn_em/module_initialize_real.F`：`p_surf=p00*EXP(−t00/a+√((t00/a)²−2g·ht/(a·Rd)))`；`pb=c3h*(p_surf−p_top)+c4h+p_top`；`temp=MAX(tiso, t00+A*LOG(pb/p00))`（p<p_strat 分支 tiso+A_strat*LOG(pb/p_strat)）；`alb=(r_d/p1000mb)*(t_init+t0)*(pb/p1000mb)**cvpm`；`phb(k)=phb(k−1)+alb(k−1)*phm*LOG(pfd/pfu)`（hypsometric_opt=2 对数气压形式；opt=1 为 dnw*(c1h*mub+c2h)*alb 形式）；注释 "Integrate base geopotential…exact hydrostatic balance"；`const_module_initialize` 读 6 项；`t0=300` 位温参考常数（另处定义）；η 系数段 3689–3760（znu=0.5(znw(k+1)+znw(k))、dn/dnw/fnp/fnm、cf1–cf3、"Scads of vertical coefficients"）
- `dyn_em/nest_init_utils.F`：`compute_vcoord_1d_coeffs`——hybrid_opt=0/1 时 c3f=znw；=2 时 Klemp 多项式（B1…B5 含 etac，znw<etac 段 c3f=0，端点强制 1/0）；=3 sin² 形式；c4f=(znw−c3f)(p1000−ptop)；c3h/c4h/c1f/c2f/c1h/c2h；单调性检查（报错提示"reduce etac"）；p_surf 解析式同源
- `Registry/registry.hyb_coord`：文件头 Pd 公式与 C1–C4 定义；state c1h…c4f/c4h/pcb/pc；rconfig hybrid_opt（0=原/1=地形跟随 hybrid/2=Klemp cubic with etac，默认 2）、etac（默认 0.2）
- `Registry.EM_COMMON`：base_pres=100000（"do not change"）、base_temp=290、base_lapse=50（"do not change"）、iso_temp=200、base_pres_strat=0、base_lapse_strat=−11（均 "real only"）
- `share/module_compute_geop.F`：compute_500mb_height（按 p 面插值位势 → 500 hPa 高度）

### 实验最终数字（workspace/scripts/ch10_experiment.py；数据 workspace/data/ch10/）
- η：(44,44) 兰州点 HT=1664.5 m p_top=5000；znu 恒等式偏差 0.0；首层 dz=15.38 m
- 基态：T0 实测 vs 解析最大偏差 0.0001 K；200K 封顶阈值 16530 Pa（4 层）；p_surf 81903.711 vs MUB+p_top 81903.703 Pa；重演 phb 残差 0.039 m²/s²（2×10⁻⁷ 量程）；dz vs αΔp/g 中位 7.6e-5
- 位势高度：+0.57 m @1672 m、+4.23 m @12394 m
- ERA5：逐层差分（30 段）中位 +0.76 m、最大 11.2 m；**地形口径差 +284 m**（ERA5 柱 PSFC≈1948 m vs geog HGT_M=1665 m）；met_em 结构=表面行(k=0: PSFC,geog 高度)+31 个 ERA5 气压层
- 标高/质量：Hp=8605 m（Tv=294K）；m0=10051 kg/m²、总质量 5.125×10¹⁵ t（书 10044/5.12×10¹⁵）
- 图：doc/figs/ch10_base_state_profiles.png（三联：T0 对照/气压-高度四曲线/η 分布）

## ch11 大气成分、水汽与气溶胶 —— 已核验（2026-10-10，批次 2 第二章）
交付：doc/ch11_composition_moisture_aerosol.md（八段式，863 行，含 2 个 mermaid）

### 书页扫描直读（17 页；印刷页 6、12–15、18 未直读，臭氧细部与 2.2 引文经 PPT 覆盖）
- 印刷页 7（page_0021）表 2.1/2.2：N₂ 78.084/75.52%、O₂ 20.948/23.15%、Ar 0.934/1.28%、CO₂ 0.033/0.05%；次要成分 Ne 18.18、He 5.24、Kr 1.14、Xe 0.087 ppmv
- 印刷页 8（page_0022）：温室气体段（CO₂ 贡献约 55%）、(2.1.1)(2.1.2)、Md=28.9644e-3、Rd=287.05、(2.1.3)
- 印刷页 9（page_0023）：(2.1.4) 比热加权、cpd=1004/cvd=717；CO₂ 光合/呼吸；海洋源汇分纬
- 印刷页 10（page_0024）：图 2.1、CH₄ 1.625 ppmv(1984)/0.6~0.8(古代)、CFC-11/12=氟里昂
- 印刷页 11（page_0025）：表 2.3 六气体台账；臭氧 10~50 km/极大 20~30 km/0.2~0.29 μm/(2.1.5)(2.1.6)(2.1.7)/<0.24 μm/离解峰 42 km/地面降温 1~2℃
- 印刷页 16（page_0030）：硫 80~90% 在 SO₂/H₂S、pH 5.6、海洋 2~4 倍/陆地 4~15 倍；奇氮
- 印刷页 17（page_0031）：NH₃ 中和/铵盐凝结核；2.1.6 逃逸（400~500 km、能量守恒、H 0.576/0.552 ppmv）
- 印刷页 19（page_0033）：表 2.4（海洋 97.57%、大气 0.001%）；(2.2.1)(2.2.2)
- 印刷页 20（page_0034）：(2.2.3)(2.2.4)(2.2.5)、ε=0.622、表 2.5a/b、e<60 hPa、(2.2.6)
- 印刷页 21（page_0035）：(2.2.7)；Goff-Gratch 水/冰；(2.2.8a)；(2.2.9a/b)；(2.2.10) 水 7.5/237.3 冰 9.5/265.5；(2.2.11)；图 2.6
- 印刷页 22（page_0036）：(2.2.12a/b)(2.2.13)(2.2.14)(2.2.15)(2.2.16)；图 2.7；三相点降 0.0098K/误差<1%
- 印刷页 23（page_0037）：表 2.6；(2.2.17)–(2.2.20) 虚温
- 印刷页 24（page_0038）：ΔTv=0.608qT=0.378(e/p)T；(2.2.21)(2.2.22)；2.2.3 分布（Sharjah 34℃/35 g/kg、Vostok 1e-4 g/kg、90%在500hPa下/50%在850hPa下、平流层 1~3 ppmv）
- 印刷页 25（page_0039）：气溶胶定义；爱根核/大粒子/巨粒子；离子 0.005 μm；数密度 1e3/1e4/1e5；Junge (2.3.1)；雷暴 1%→+1 ppmv
- 印刷页 26（page_0040）：(2.3.2)；ν 2~4/大陆≈3；Γ 谱三型；降水清除 80~90%；荣格层 20 km/火山后 10 倍
- 印刷页 27（page_0041）：来源 6 类及数字（(10~20)×10⁸ t、Pinatubo 3 周环球、海沫 >2 μm/0.3 μm、宇宙尘 550 t/天）；作用(1)
- 印刷页 28（page_0042）：作用(2)~(5)；Pinatubo 1992 最冷/平流层 +2℃；能见度 50~100 m；逆温 7~10 时电场极大；光化学烟雾专栏；书习题 1、2

### 源码锚点（已实测）
- `share/module_model_constants.F`：r_d=287./cp=7*r_d/2/r_v=461.6/cv/cpv=4*r_v/cliq=4190/cice=2106/psat=610.78/mwdry=28.966；SVP1=0.6112,SVP2=17.67,SVP3=29.65,SVPT0=273.15；EP_1=rv/r_d−1、EP_2=r_d/r_v、p608、rvovrd=1.608；pq0=379.90516,a2=17.2693882,a3=273.16,a4=35.86；cm1=2937.4,cm2=4.9283,cm3=23.5518；XLV/XLS/XLF；XLV0=3.15e6,XLV1=2370,XLS0=2.905e6,XLS1=259.532（L=A−BT 约定）；rhoair0=1.28
- `phys/module_sf_sfclay.F`：E1=SVP1*EXP(SVP2*(TGDSA−SVPT0)/(TGDSA−SVP3))；SALINITY_FACTOR（海面 es −2%）；QSFC=EP2*E1/(PSFC−E1)；QGH（最低层，PL=p/1000）；TVCON=(1+EP1*QX)、THVX=THX*TVCON；CPM=CP*(1+0.8QX)；RHOX=PSFC*1000/(R*SCR4)；内部 kPa（PSFC(I)=PSFCPA(I)/1000）
- `phys/module_diag_functions.F`：calc_rh（pq0/a2-a4；先 q=qv/(1+qv)）；VirtualTemperature/SaturationMixingRatio/TLCL/Thetae/Pwat
- `phys/physics_mmm/mp_wsm6.F90`（4.8 薄壳：module_mp_wsm6.F 仅切片→mp_wsm6_run）：fpvs 内联（ttp=t0c+0.01、xa=−(cpv−cliq)/rv、xb=xa+hvap/(rv·ttp)、qsat=psat·exp(xa ln tr)·exp(xb(1−tr))、qsat=ep2·es/(p−es)、rh=q/qs；冰面用 cice/xls）；xlcal=xlv0−xlv1(x−t0c)，xlv1=cl−cpv（Kirchhoff）
- `phys/module_mp_thompson.F`：RSLF/RSIF 八阶多项式（X=max(−80,T−273.16)、ESL=min(ESL,0.15P)、.622*ESL/(P−ESL)）；注释替代 Bolton 612.2*EXP(17.67X/(T−29.65)) 与 Murphy-Koop 2005；密度式 0.622*p/(R*T*(qv+0.622))
- `dyn_em/module_initialize_real.F`：rh_to_mxrat1（A0..A6/Bolton 混合相/Goff-Gratch 冰面 C1=9.09718,C2=3.56654,C3=0.876793,EIS=6.1071,TF=273.16）；默认分支 es=.01*rh*svp1*10*EXP(...)、q=MAX(eps*es/(p/100−es),1e-6)；q1=mw_vap*ew/(mw_vap*ew+mw_air*(p/100−ew))、q=q1/(1−q1)（=书 (2.2.2) 之逆）；Registry：rh2qv_method 默认 1、rh2qv_wrt_liquid 默认 .true.、use_sh_qv 默认 .false.
- `Registry/Registry.EM_COMMON`：moist 块 qv/qc/qr/qi/qi2/qi3/qs/qg/qh（QVAPOR…QHAIL，kg kg-1）；dfi_moist；QNWFA2D/QNIFA2D/QNBCA2D（auxinput17）、QNOCBB2D/QNBCBB2D；RE_CLOUD/RE_ICE/RE_SNOW；aer_opt/aer_type/aer_aod550_val=0.12；包 aeropt1/aeropt2
- `phys/module_ra_aerosol.F`：calc_aerosol_goddard_sw（11 段）、calc_aerosol_rrtmg_sw；aer_*_opt 语义（3=类型+RH）
- `phys/module_radiation_driver.F`：aer_opt=1/2/3；gt_aod(...,qnwfa,qnifa,qnbca,...)（aer_opt=3）
- `phys/module_ra_rrtmg_lw.F`：ghg_input=1→read_CAMgases；else co2=(280+90exp(0.02(yr−2000)))e−6、ch4=1774e−9、n2o=319e−9、cfc11=0.251e−9、cfc12=0.538e−9（=书表 2.3 2005 列，逐位一致）；h2ovmr=qv*amdw

### 实验（workspace/scripts/ch11_experiment.py；图 3 张）
- A 闭合：r→q→r=0、e→r→e=0、q→e→q=1.45e-16；(25℃,1000,q12)：r=12.146/e=19.153/ρv=13.9/Td=16.828（es(Td)=e 逐位）；U：e/es=60.468、q/qs=60.180、(2.2.16)=60.468
- B es 对照：水面各实现最大差 3.44%（−40℃）、0–40℃ ≤0.7%；冰 −12℃：书 2.167/WSM6 2.159/Thompson 2.173；**贝吉龙 Δes 最大 −11.7℃（0.266 hPa）**（书称 −12℃ ✓）
- C：ΔTv(30℃,q20)=3.689 K；密度近似差 ≤0.0006%；cp 书 1021.78/sfclay 1020.57/严格 1021.34
- D 实测（met_em d01 2025-07-12_00，兰州 36.0N/103.75E，j=i=43）：k=0 地面伪层、k=1..8 低于地形；复现 real 路径 18 层 dq RMS 0.0711 g/kg（max 0.2437）；**T2/Q2 与 met_em 地面层逐位一致**（20.57℃/13.310 g/kg）；PSFC 口径差 791.63 vs 798.96 hPa；wrfinput 柱 RH max 98.67%、0 超饱和
- 图：doc/figs/ch11_es_curves.png、ch11_real_data_check.png、ch11_virtual_temp.png；PPT 原图 6 张 → doc/figs/ppt/ch11_ppt_*（臭氧 DU/廓线/季节纬度、水分循环、CH₄-H₂O、气溶胶垂直分布）

### 勘误/口径记录（ch11）
- 书 (2.2.9b) 冰面参考温度按书表 2.5(b) 反推为 273.16 K（扫描字迹近似 276.16，不可采信）
- WRF 虚温把混合比代入 (1+0.608q)（书用比湿），q≈12 g/kg 时 ΔTv 差 ~0.03 K
- Thompson 密度式与书 (2.2.19) 差 (1+r) 因子（~1% @ 12 g/kg）——口径不同，非“矛盾”

---

## ch12 辐射过程族 —— 已核验（2026-10-10，批次 2 第三章）

交付：`doc\ch12_radiation_family.md`（1331 行；含 1 个 mermaid + 3 张自算图 + 6 张 PPT 原图）

### 书页扫描直读（54 页；印刷页 62–121，未读 73-75、80、99、108、122）
- 公式编号全按书：(5.1.1)–(5.1.10)、(5.2.1)–(5.2.13)、(5.3.1)–(5.3.35)、(5.4.1)–(5.4.41)、(5.5.1)–(5.5.22)、(5.6.1)–(5.6.28)
- 表 5.1–5.17 全部核对；例题 5.1/5.2/5.3、思考题 7、习题 1–15 原件录入并改造（教材 12.10）
- 第 5 章范围：印刷页 62（5.1）–122（参考文献）；5.3.2=p76、5.4=p84、5.5=p103、5.6=p109（目录 page_0008-0011 实读）

### 源码锚点（全部本地实测）
- `phys/module_radiation_driver.F`：radiation_driver 四触发（itimestep=1 / radt=0 或 stepra=1 / MOD(itimestep,stepra)=1+ra_call_offset / 自适应 radtacttime）；radconst（OBECL=23.5°；SXLONG=DPD*(J−80)；ECCFAC=Paltridge&Platt 1.000110+0.034221+0.001280+0.000719+0.000077；SOLCON=1370×ECCFAC）；calc_coszen（eot×229.18；hrang=15(tloctm−12)；coszen=sinφsinδ+cosφcosδcosω=书 (5.4.3a)；调用时刻 xtime+radt*0.5；限幅）；ozn_time_int/ozn_p_int（4864/4971 起）；DPD=360/365（module_model_constants.F）
- `phys/module_ra_rrtmg_lw.F`：nbndlw=16，wavenum1/2=(10,350,...,2600)→(350,...,3250)；GHG 分支（ghg_input=1→read_CAMgases；else 2005 常量+co2 年函数）；云光学 inflglw=2/3/4/5、iceflglw=3/4/5、P3 特例；o3input=0→inirad 兜底并回写 O33D
- `phys/module_ra_rrtmg_sw.F`：nbndsw=14，wavenum1/2=(2600,...,38000,820)→(3250,...,50000,2600)；rrsw_scon=1368.22；solvar=scon/rrsw_scon；earth_sun=Iqbal 1.2.1（默认 dyofyr=0、adjes=1 不重复订正）；scon=solcon(1−obscur)
- `phys/module_ra_effective_radius.F`：effectRad（re_qc=clamp(3/λc,2.51,50)；re_qi=clamp(0.75×0.163×11.9√(rqi/ni),10.01,125)；re_qs=clamp(0.5/λs,25,999)+霰加权；n0s=2e6·exp(0.12ΔT)）
- `phys/module_ra_cam_support.F`：oznini 读 run/ozone.formatted（12×64×59）+ozone_lat/ozone_plev
- `phys/module_ra_clWRF_support.F`：read_CAMgases 读 CAMtr_volume_mixing_ratio（缺文件 wrf_error_fatal）
- Registry.EM_COMMON：ra_lw/sw=-1 必设；radt=0；ghg_input=1；o3input=2；aer_opt=0；swint_opt=0；slope_rad/topo_shading=0；方案号 LW:1/3/4/5/7/14/31/99、SW:1/2/3/4/5/7/14/99；package 行列出状态量
- 个例 namelist（workspace/cases/lanzhou2025）：ra_lw/sw=4,4；radt=30,15；icloud=1；o3input/ghg_input/aer_opt 未设→默认 2/1/0

### 实验（workspace/scripts/ch12_experiment.py；日志 workspace/logs/ch12_experiment.log；图 3 张）
- A 四定律：σ(c1,c2)=5.671416e−8（书 5.6696e−8，0.032%）；∫F_B dλ vs σT⁴ 0.011–0.032%（5 温度）；数值 λmax=2897.8/T 精确、与书表 ≤26 nm；B(λmax) 与书表 10/11 行 ≤0.03%（300K 行 1.04%）
- C 闭环（wrfrst_d01_2025-07-12_00_05_24.nc）：**julian=192（ESMF 零基日序）**→ΔDECLIN 9.9e−9 rad、ΔSOLCON 1e−4（1324.575）；**xtime+radt*0.5=15 min**→全 89×89 格点 max|ΔCOSZEN|=8.9e−8、max|ΔHRANG|=0（0 min 假说差 5e−2/6.5e−2）
- D 相对大气质量：Kasten (5.4.22) 复现书表 5.5 该列逐位（1.0148…10.3231）；δ_R(0.52μm)=0.1244（书 0.124）
- E Qd 夏至：赤道 34.452、90N 47.057（10⁶ J·m⁻²·d⁻¹），比值 1.366（书 1.37）；兰州昼长 14.256 h
- F 温室：基准 278.6/247.7 逐位；Te=254.8（书 255）；S0(1−R)/4=239.05 逐位；**表 5.16 敏感性 6 行与 (5.6.4) 复算不符（勘误候选：R+0.02→276.2 vs 书 278.3；Al+0.02→279.8 vs 283.2；As+0.01→278.0 vs 276.0）**
- F2 CAMtr：2005 行（378.907/319.130/1783.360/250.915/542.146）与 RRTMG 常量支路一致；2025 行（429.030/335.980/1960.651/204.429/471.673）为个例实际取值
- F3 O3RAD（wrfrst 兰州柱，VMR）：837 hPa 4.10e−8 → 64.5 hPa 1.27e−6；与 CAM 气候学 7 月 log-p 插值中位差 5.3%；P_TOP=50 hPa、49 层
- 图：doc/figs/ch12_planck_bands.png、ch12_solar_geometry.png、ch12_ozone_ghg.png；PPT 原图 6 张 → doc/figs/ppt/ch12_ppt_*（三定律组合、整层吸收谱、米散射效率、太阳谱、太阳常数、温室模式）

### 勘误/口径记录（ch12）
- 书 表 5.16 敏感性六行无法由 (5.6.4) 复现（见上）——教材已标注，考试计算以 (5.6.4) 为准
- 书 表 5.2 的 300 K 行 B_λmax=9.852 与复算 9.954 差 1.04%（书取整偏粗；其余行 ≤0.03%）
- 书与源码常数口径差：黄赤交角 23°27′ vs 23.5°；太阳常数 1366/1367 vs 1370（RRTMG 参考谱基准 1368.22）
- PPT 5-5 全部为 WMF 矢量图（无法转位图嵌入）、5-2 slide7 为 EMF——ch12 未嵌 5-5 原图（公式推导以书为准）

## ch13 微物理方案族 —— 已核验（2026-10-10，批次 2 第四章）

交付：`doc\ch13_microphysics_family.md`（1321 行；含 2 个 mermaid + 3 张自算图；PPT 未到，考点节自拟标注"待 PPT 校准"）

### 书页扫描直读（33 页；印刷页 123–153 + 168–169）
- 公式编号全按书：(6.1.1)–(6.1.72)、(6.2.1)–(6.2.23)、(6.3.1)–(6.3.13)、(6.4.1)–(6.4.10)、(6.5.1)–(6.5.7)、(6.6.1)–(6.6.8)、(6.7.1)–(6.7.6)
- 第六章结构（目录 page_0009 实读）：6.1=p123、6.2=p134、6.3=p138、6.4=p142、6.5=p147、6.6=p149、6.7=p150、6.8=p154、6.9=p164、6.10=p167、思考题=p168、习题=p169；**6.1–6.7 本章用；6.8→ch14、6.9→ch15**
- 思考题 7 题、习题 8 题原文全录并全解（教材 13.10，含数值答案）
- 三处重点核验通过：① (6.1.46) 记号（rt=rv+rw 总水质物混合比、rs 饱和混合比）；② **(6.3.5) 分母含 ε 因子**（εLv²rs/(cpdRdT²)，数值积分逐点吻合 0.1–1%，**非勘误**——若漏 ε 会使 γs 偏低约 30%）；③ 图 6.15 关系句：Tsw<Tw<T<Te<Tse、θsw<θ<θse

### 源码锚点（全部本地实测）
- `dyn_em/solve_em.F`：微物理调用链 moist_physics_prep_em → microphysics_driver（DT=dtm、TH=th_phy、P=p_phy、PI_PHY、DZ8W、RHO；SR 调用前置零）→ moist_physics_finish_em；mp=28 另有 bulk_dust_emis 前置
- `phys/module_microphysics_driver.F`：micro_select SELECT CASE(mp_physics) 约 39 个 CASE 全录；THOMPSON CASE 参数实录（NI/NR 数浓度、re_*、has_re*；无 nc/nwfa = mp8）；WSM6 CASE 参数实录（常数全显式传入 CPD/CPV/RD/RV/XLV0/XLS/CLIQ/CICE/PSAT…）；PRESENT() 变量契约自检 + wrf_error_fatal
- `phys/module_mp_thompson.F`：结构（thompson_init / mp_gt_driver 单巨子程序 ~1070–5250 / calc_effectRad / RSLF / RSIF / GAMMCF / GSER）；常数区（Nt_c=100E6、Nt_c_max=1999E6、naIN0/1、naCCN0/1、naBC0/1、rho_g 9 档 50–800、Field 雪谱 mu_s=0.6357/Kap0=490.6/Kap1=17.46/Lam0=20.78/Lam1=3.29、质量/落速幂律、C_cube=0.5/C_sqrd=0.15、Ef_*=0.05/0.95/0.75/0.95、R1=1E-12/R2=1E-6、HGFR=235.16、xm0i=1E-12）；**饱和调整 3 次牛顿**（clap=(qv−qvs)/(1+lvt2·qvs)，F=qs·e^{lvt2·Δ}−qv+Δ；lvt2=Lv²·ocp/(RvT²)，lvap=2.5e6−2112t；更新 prw_vcd→qvten/qcten/tten+=lvap·ocp·prw_vcd）；**冰核化三来源**（Bigg 1953 查表+HGFR 均质冻结；Cooper xnc=MIN(250E3, 5·e^{0.304(273.15−T)}) 或 DeMott 2010（dustyIce）；Koop 2001：T<238 & ssati≥0.4 & xni≤999E3）；守恒五物种限幅（"Ensure we do not deplete…"段）；尺寸/数浓度硬约束（云水 1–50μm & ≤1999E6；冰 5–300μm & ≤999/L；雨 MVD 37μm–2.5mm）；温度倾向 lsub/lfus 双分支；calc_effectRad 闭环（RE_QC_BG=2.49E-6/RE_QI_BG=4.99E-6/RE_QS_BG=9.99E-6、帽 50/125/999μm）
- WSM6 双层：`phys/module_mp_wsm6.F`（薄壳 use mp_wsm6/mp_wsm6_effectRad）→ `phys/physics_mmm/mp_wsm6.F90`（实体 mp_wsm6_init/run、fpvs、slope_*、nislfv_rain_plm/plm6、refl10cm_wsm6）；句函数 cpmcal/xlcal（**xlv1=cliq−cpv=2343.6**）、diffus/viscos/xka、**conden(a,b,c,d,e)=(max(b,qmin)−c)/(1+d²/(rv·e)·c/a²)**；饱和调整单步解析（pcond 限幅 + T+=pcond·xl/cpm·dt）；fpvs 常数 xa=5.077/xb=24.904/xai=0.562/xbi=23.165；wrftladj TL/AD 旁证
- `Registry/Registry.EM_COMMON`：mp_physics rconfig；package 族（8 thompson qni,qnr；28 thompsonaero +qnc,qnwfa,qnifa,qnbca,+qnwfa2d 等；6 wsm6scheme；齐全 0–106）；moist/scalar/state 三组变量差异表（教材 13.6.4）
- `run/README.namelist`：mp_physics 0–106 用户表（含 30/32 HUJI、38 thompsongh、88 TEMPO、95/96/97）+ hail_opt/mp_zero_out/wif_input_opt/num_wif_levels/use_aero_icbc
- `share/module_model_constants.F`：RE_QC_BG=2.49E-6、RE_QI_BG=4.99E-6、RE_QS_BG=9.99E-6、RE_QC_MAX=50E-6、RE_QI_MAX=125E-6、XLV=2.5E6、XLS=2.85E6、cliq=4190、cice=2106、psat=610.78、r_v=461.6、XLV1=2370（旧线性化）

### 实验（workspace/scripts/ch13_experiment.py、ch13_exercises.py；日志 workspace/logs/ch13_{experiment,exercises}.log；图 3 张）
- A 埃玛图（书习题 7 探空）：LCL 精确 942.9 hPa/18.06℃/506 m vs (6.2.23) 估算 492 m（+2.8%）；LFC 343.8 hPa（z≈7972 m）；正能区 +711 J/kg、负能区 −1330 J/kg；对流温度 30.8℃（CCL 842.6 hPa）
- B γs 闭式（含 ε）vs 数值微分：1000/850/700/500/300 hPa → 9.740/9.740、4.204/4.165、3.890/3.846、3.411/3.360、2.847/2.788 K/km（γd=9.77）；θse 假绝热积分漂移 ≤0.54%（335.08→336.89 K）；**习题 8：w=24.1 m/s（未订正）/26.5 m/s（虚温订正）**，ΔT=7.55 K
- C 饱和调整三法：Thompson 3 牛顿残差 ≤2.1e−5 kg/kg、ΔT 误差 ≤8.0e−3 K；WSM6 conden 残差 ≤2.6e−5、ΔT 误差 ≤1.15e−2 K；残差 ~ss² 标度；真值=阻尼定点迭代（0.25）；代表值（25℃/1000hPa/ss=0.02）：ΔT 0.2479/0.2496/0.2436 K
- D wrfinput_d01 剖面（35.98N,103.73E，49 层，最低层 p=790.9 hPa）：θ（T+300）与 θse 复算
- 习题 1–8 全解数值：习题 1（q=3.4 g/kg、Td=−2.1℃、θ=282.3 K、Tv=278.7 K）；习题 3（RH 34.2%→69.2%）；习题 4（雾、≈1.5 g/m³）；习题 5（510 hPa θ=313.9 K；LCL 748 hPa、θ=301.5 K；θse 双端 322.0 K）；习题 6（焚风：背风 950 hPa T=20.0℃、q=5.7 g/kg、θ=297.5 K、**θse=312.3 K 与迎风守恒**）；习题 7 全问；习题 8
- 图：doc/figs/ch13_emagram.png、ch13_theta_se.png、ch13_satadj.png

### 勘误/口径记录（ch13）
- 书 (6.3.5) 分母 ε 因子经数值积分验证（漏 ε → γs 偏低 ~30%；非勘误）
- Lv(T) 三口径并存：书 −2323 / WSM6 xlcal −2343.6 / Thompson lvap −2112（差 ≤0.5%；教材 13.9.2 列表）
- 思考题 4 的 θ′=Cθ：严格形式 θ′=C^κ·θ（教材已注明幂次口径，κ=0.288）
- 习题 6 的 θse 须用实测比湿口径 θ·exp(Lv q/(cpd T)) 计算（饱和口径会高估；脚本已修正）
- 习题 7 的 CCL：用"地面 q 的等饱和比湿线（Tsat(p)）与环境温度层结曲线交点"口径（842.6 hPa）

## ch14 边界层方案族 —— 已核验（2026-10-10，批次 2 第五章）

交付：`doc\ch14_pbl_family.md`（854 行；含 2 个 mermaid + 3 张自算图；PPT 未到，考点节自拟并标注）

### 书页扫描直读（10 页；印刷页 154–163）
- 6.8 全节三段：判据（154–156）/条件性不稳定（157–161）/薄层法（161–163）；公式 (6.8.1)–(6.8.21) 全按书号；图 6.15–6.23、表 6.1、烟云五型（图 6.18）
- 6.9/6.10 → ch15/后文；书第 8–9 章课程范围外（14.4 以"模式视角"补齐 TKE/闭合/相似理论）

### 源码锚点（全部本地实测）
- 调用链：solve_em → first_rk_step_part1 →（顺序）radiation_driver → surface_driver → pbl_driver（BENCH pbl_driver_tim）→ shallowcu_driver；PBL 每时间步一次（bldt=0）；微物理在 solve_em 直调（对照）
- `phys/module_pbl_driver.F`：CASE 全录（YSU/MYNN/BouLac/MYJ/QNSE/ACM2/Shin-Hong/GBM/TEMF/CAMUW/MRF/GFS/EEPS/KEPS/SURFDRAG/fitch/mav）；另有 `SELECT CASE(sf_urban_physics)` 置 flag_bep（BEPSCHEME/BEP_BEMSCHEME 联络名——非独立 PBL 分支）；BOULAC 调用实录（BEP 数组 a_u_bep…b_e_bep、dlg/sf/vl、tke_pbl/el_pbl、wu_tur…）；MYNN 调用实录（qke/qke_adv、sh3d/sm3d、tsq/qsq/cov、cldfra_bl/qc_bl/qi_bl、edmf_a/w/qt/thl/ent、bl_mynn_* 组、tke_budget）
- `phys/MYNN-EDMF/`：编译实体（Makefile 符号链接；主体 module_bl_mynnedmf.F90 + WRF/module_bl_mynnedmf_common.F90 + WRF/module_bl_mynnedmf_driver.F90）；physics_mmm/bl_mynn.F90 = CCPP 副本；版本史 V1.0(V3.0–3.4.1/HRRRv1)→V4.0(V4.0–4.4/HRRRv4)→V5.0(V4.5–4.7)→V6.0(V4.8/CCPP/MPAS)；头部内容清单与变量约定（中心/界面；qke=2TKE）；主链 mym_initialize→mym_condensation→ddmp_mf→mym_turbulence→mym_predict；boulac_length 注释原文（"taken from the BouLac scheme…"）；**get_pblh 全文**（最低 200 m 找 min θv；Δθv 陆 1.25 K/水 0.75 K；stable_method=1 默认 Koracin & Berkowicz u*×400/700 m；blend wt=½tanh((pblh−200)/170)+½；stable_method=0 TKE 5% max qke、±350 m 限）；常数表（tref=300、TKmin=253、tice/tliq、ep_3=0.378、gtr、tv0=0.608·tref、xlscp、wfa 上下限、svp1-3 Bolton）；dmp_mf 功能清单（scale-aware tapering、TKE 输运、Chaboureau–Bechtold 云量、数值限制）
- `phys/module_bl_boulac.F`：直接模块；常数 ck_b=0.4/ceps_b=1/1.4/vk=0.4/temin=1e-4；注释"TKE IS NOT ADVECTED!!"；链路 boulac→boulac1D/pbl_height/length_bougeault/cdtur_bougeault/tke_bougeault/shear/buoy/diff；耗散组装 td=−ceps·√te/dls（a_e 隐式/b_e 源项）；dls=√(dlu·dld)、dlk=min（BEP 时与 dl_u 调和 1/l←1/l+1/l_u）；exch=ck_b·dlk_m·√te_m、下限 0.1；pbl_height：θv(sfc)+0.5 K（注释"similar to MYNN"）；wstar=(g·wts·pblh/θ0)^{1/3}；方差廓线 t2/w2（1.8 系数）；igamma 三选（1=Troen-Mahrt 默认）
- YSU 双层：薄壳 module_bl_ysu.F → 实体 physics_mmm/bl_ysu.F90（bl_ysu_run，CCPP 风格，NEED_B4B_DURING_CCPP_TESTING）；常数 brcr_ub=0.0/brcr_sb=0.25/brcr_sbro=min(0.16(1e-7Ross)^−0.18,0.3)/cori=1e-4；wstar3=govrth·bfx0·hpbl；wscale=(ust3+phifac·karman·wstar3·0.5)^{1/3}；topdown：qc+qi>0.01e-3 云层增强 wstar3_2、wm3=wstar3+5ust3、prfac2=15.9(...)；BEP 数组在 run 参数内
- `Registry/Registry.EM_COMMON`：bl_pbl_physics package 族 0/1/2/3/4/5/7/8/9/10/11/12/16/17/99 与状态量（myj：tke_pbl/el_pbl；mynn：qke/sh3d/sm3d/tsq/qsq/cov/cldfra_bl/qc_bl/qi_bl/el_pbl/tke_pbl；boulac：el_pbl/tke_pbl/wu_tur/wv_tur/wt_tur/wq_tur）
- `run/README.namelist`：bl_pbl 0–99 表；**option 6 于 4.5 移除 → bl_mynn_closure（2.5/2.6 默认/2.7 TTE/3.0）**；bldt/tke_budget/bl_mynn_tkeadvect/icloud_bl/bl_mynn_cloudmix/ysu_topdown_pblmix/topo_wind/grav_settling/mfshconv；**sf_urban_physics 2/3 兼容清单原文"works only with YSU, MYJ and BouLac PBL"（MYNN 不在列）**

### 实验（workspace/scripts/ch14_experiment.py；日志 workspace/logs/ch14_experiment.log；图 3 张）
- E1 判据表（书习题 7 探空；γd=9.77）：9 层 Γ/γs/θ/θe/∂θ∂z/∂θe∂z 双判据全出；850–800 超绝热（Γ=9.80）绝对不稳定；600 以上全稳定；**1000–900 两判据分歧**（Γ=2.75 → 气块判据绝对稳定；∂θe/∂z=−7.11 → 条件性不稳定，指向 6.9.2）
- E2 虚温订正 CAPE/CIN：LCL 942.9 hPa；LFC 807.7 hPa（1827 m）；EL 340.4 hPa（8491 m）；CAPE=815 J/kg、CIN=−128 J/kg（对照 ch13 未订正：+711/−1330、LFC 343.8 hPa）
- E3 wrfinput 兰州柱（35.98N,103.73E；z0=2092 m）分段质量加权 θ：0–500 m 312.25 K；0–1000 m 313.21 K；0–2000 m 316.90 K；近地 300 m ∂θ/∂z ∈ [−0.0069,+0.0020] K/m（清晨弱层结）
- E4 薄层法 (6.8.21)：Γ=6.0/γs=4.2 → 0.477 临界；A1/A2=0.1/0.3 不稳定、0.5/1/2/5 稳定（"积云密度自调节"数值演示）
- 图：doc/figs/ch14_stability.png、ch14_cape.png、ch14_mixed_layer.png

### 勘误/口径记录（ch14）
- BEP/BEM 兼容清单口径校准：README 原文为三方案（YSU/MYJ/BouLac），非"仅 BouLac"——教材按原文表述（MYNN 不在列）
- MYNN 编译实体口径：phys/MYNN-EDMF/（非 physics_mmm/bl_mynn.F90 副本）——防"读错文件"，教材 14.6.1 已注明
- 书图 6.21（Wood Ward 1960 热泡照片）为书内引用照片，未嵌入；正文文字转述
- 6.8 书内习题（习题 7 第 2/4 问、习题 8）已在 ch13 全解；本章仅"口径升级"点评（E1 双判据/E2 虚温订正）
- 考点节自拟待 PPT 校准（同 ch12/ch13 口径）

## ch15 积云参数化族 —— 已核验（2026-10-10 夜，批次 2 第六章）

交付：`doc\ch15_cumulus_family.md`（约 936 行；含 2 个 mermaid + 4 张自算图；PPT 未到，考点节自拟并标注）

### 书页直读（扫描页 → 印刷页换算 已核验）
- 6.9 正文 p164–166（page_0178–0180）：6.9.1 未饱和/下沉逆温（(6.9.1)–(6.9.3)、图 6.27、例题 6.2 含 (6.9.4)）；6.9.2 对流性不稳定（图 6.28、(6.9.5)、"Δp 恒定"假定）
- 6.9 末段全局结论 + 6.10 逆温层 p167（page_0181）：图 6.28 两联图；五类逆温（辐射/下沉/地形/平流/锋面）；阻塞层
- 6.10 续 + 思考题 p168（page_0182）：图 6.29（Eagleman 1985）；思考题 1–6
- 思考题 7 + 习题 8 题（p169，page_0183）+ 参考文献 10 条
- **答案页**：印刷页 546（page_0560）第六章习题答案全抄：1（3.4 g/kg、−2.5℃、278.7 K、9.1℃）、3（34.5%/69.6%）、4（有雾；1.49 或 1.45 g/m³）、5（740 hPa；315.5/302 K）、6（20.5℃/0.0057/25℃/44℃ 不变）、7（9/17 g/kg、53%；LCL 950/CCL 850/LFC 800；真潜不稳定；30.5℃；θse 68→60℃ 对流性不稳定）、8（24.2/26.7 m/s）

### 源码锚点核验
- 调用链：`dyn_em/module_first_rk_step_part1.F`（radiation→surface→pbl→**cumulus_driver**→shallowcu_driver；microphysics 在 `solve_em` 后段）
- `phys/module_cumulus_driver.F`：17 方案 SELECT CASE（KFSCHEME…NTIEDTKESCHEME…DUCU）+ DEFAULT 报错；四条调用节律（itimestep==1 / cudt==0 或 stepcu==1 / MOD / 自适应 cudtacttime）；**G3 与 NTiedtke 的倾向并入**（RTHFTEN+=RTHRATEN+RTHBLTEN 乘 pi；RQVFTEN+=RQVBLTEN）；HALO 四方案；KF "DON'T JUDGE TIME STEP HERE"；tmppratec 中转；cudtacttime 回写
- `phys/module_physics_init.F` 的 `cu_init`：`STEPCU=nint(CUDT*60./DT); STEPCU=max(STEPCU,1)`；倾向清零 + 各方案 init 分发（kfinit/kf_eta_init/ntiedtkeinit…）；`shcu_init` 同构
- `Registry/Registry.EM_COMMON` cu_physics package 全表（0/1/2/3/4/5/6/7/10/11/14/16/93/94/95/96/99；**16 的 package 行为空**）；shcu_physics（1/2/3/4/5）；cu_diag/cu_used 包
- `run/README.namelist`：cu_physics 官方说明；physics_suite='CONUS'（mp8/cu6/bl2）与 'tropical'（mp6/cu16/bl1/sfclay91）；嵌套 -1/0 覆写；cu_rad_feedback 仅 GF/G3/GD/KF 且需 cu_diag=1；kfeta_trigger 1/2/3；cudt 分钟；cugd_avedx；kf_edrates
- **New Tiedtke**：`phys/module_cu_ntiedtke.F`（cu_ntiedtke_driver/ntiedtkeinit/pre_run/post_run）+ `phys/physics_mmm/cu_ntiedtke.F90`（cu_ntiedtke_common/ cu_ntiedtke_run/cumastrn/cuinin/cutypen/cuascn/cudlfsn/cuddrafn/cuflxn/cudtdqn/cududvn/cuadjtqn/cubasmcn/cuentrn/foealfa/foeewm/foelhm/foedem/foeldcpm）
  - 头注释六项更新（Jakob&Siebesma 2003；Bechtold 2004/2008/2014；Sundqvist 1978；Gregory 1997；Wu&Yanai 1994）与两套使用建议
  - pre_run：delt=dt·stepcu；slimsk=|xland−2|；垂直翻转；ω=−0.5gρ(w_k+w_{k+1})；itimestep==1 倾向清零
  - post_run：raincv=rn/stepcu；pratec=rn/(stepcu·dt)；倾向=(新−旧)/delt（温度再除 exner）
  - 尺度因子：dxref=15 km；<15 km 为 (1.06133+ln(15/dx))³（scale_fac2=√）；≥15 km 为 1+1.33e-5·dx；深 τ×scale_fac、浅 M/√scale_fac2
  - cumastrn 十步（zcons/zcons2=1,3 /(g·dt)；cuinin；cutypen；首猜质量通量；cuascn；下沉气流；闭合；cuflxn；cudtdqn；cududvn+耗散加热）
  - cutypen：浅测试气块由 hfx/qfx 起动（Jakob 2003：w*=1.2(0.001−p1p2)^(1/3)；ΔT=1.5H/(ρcp w*)；Δq=1.5E/(ρw*)；ε_test=0.8/z+2e-4）；深测试气块多出发层（60 hPa 混合层/单层；+0.2 K、+1e-4；动能 0.5；ε_test=1.75e-3·min(1,qs/qs_base)³）；云厚 ≥/≤ zdnoprc=200 hPa 定深/浅；出发层限 350 hPa 内
  - 闭合：深 τ_c=(z_top−z_base)/(2+min(15,wup)) 钳位 [360,10800]×scale_fac；zheat/zcape1（含 −ql 水负载与 0.608 湿效应）；nonequil 扣 zcape2（τ_bl≤300 s 的 PBL 生成项；CAPE≤5000）；M=CAPE·M_guess/(zheat·τ)；浅 zdhpbl/zdh/√scale_fac2；中层 M=max(cmfcmin,−ω/g)≤cmfcmax（cubasmcn：q>0.8qs、0.5–10 km）；缩放 zfac/zmfs
  - 卷入/卷出：zoentr 云底 1.75e-3·[1−min(1,q/qs)]·dz；云内 1.75e-3·[0.3+(1−min(1,q/qs))]·(qs/qs_base)³·dz；封顶 0.4·M；卷出 0.75e-4·(1.6−min(1,q/qs))·dz·M；浅 ε 加倍 δ=ε；cuentrn 的 pdmfen 被 zoentr 覆盖（实测）
  - 降水：阈值 zdshrd=0.5e-3（陆）/0.3e-3（海）；zprcon=(cprcon/g)/(0.75·zwu)；z_cbf=1+0.5√(zdt)（T<−5℃）；指数解；z_cldmax=5e-3；落速 21.18·r^0.2；z_cwifrac=0.5
  - 饱和比湿：foeewm=c2es·[α·e_w+(1−α)·e_i]，c2es=c1es·Rd/Rv；qs=zqs/(1−vtmpc1·zqs)；Tetens c1es=610.78、c3les=17.2693882、c4les=35.86、c3ies=21.875、c4ies=7.66、tmelt=273.16；foealfa 二次斜坡（250.16–273.16 K）
  - 常数：zdnoprc=2.0e4、cprcon=1.4e-3、cmfcmax=1.0、cmfcmin=1e-10、cmfdeps=0.30、entrdd=2e-4、pgcoef=0.7、momtrans=2、nonequil=.true.、lmfpen/lmfmid/lmfscv/lmfdd/lmfdudv=.true.
- **KFeta**：`phys/module_cu_kfeta.F`：W0AVG=(W0AVG·(TST−1)+W0)/TST、TST=2·STEPCU（自适应另有版本）；触发 DTLCL=4.64·WKL^0.33（Kain 2004；WKL=W0AVG·dx/25km−WKLCL；WKLCL=0.02z/2km）；trigger=2 湿度平流（Ma&Tan 2009，9 点邻域 TPART_H/V）；trigger=3 DTRH（U00=0.75，Narita&Ohmori）；WLCL=1+0.5√(2gΔT·500/Tven)≤3；闭合 ABE 迭代 AINC≤10 次移除 ≥90%（FABE 收敛带 ±0.05；couplet 增 CAPE 则禁对流）；TIMEC=DX/VCONV 钳位 [1800,3600]（浅 2400）；PEF 切变多项式 + 云底高度订正；子程序 TPMIX2/DTFRZNEW/CONDLOAD/PROF5/ENVIRTHT
- `phys/module_shallowcu_driver.F` scps_select：CAMUWSHCU/GRIMS（需 wstar）/NSCV/DENG（MYJ 限定）

### 实验（workspace/scripts/ch15_experiment.py；日志 workspace/logs/ch15_experiment.log；图 4 张）
- E1 例题 6.2：Γ1=3.2138 K/km；临界 无辐散书答案 467.7 / 复算 469.5（书公式含精确 Γ1）/ 469.3（60 层等熵离散模型）；辐散 20% 为 390 / 391.3 / 391.1——~1 hPa 差源于 Γ1 两位有效数字取整；(6.9.3) 的 θ2≈θ1 近似影响 <0.5 hPa
- E2 习题 7：900 hPa q=9.12/qs=16.83 g/kg、Uw=54.4%（书 9/17/53）；LCL 942.8（书 950）、CCL 842.7（书 850）、LFC 807.5（书 800；未订正 792.5）、EL 345；CAPE 790/CIN −124（虚温；未订正 694/−165；与 ch14 E2 的 815/−128 一致 ±3%）；真潜不稳定 ✓；对流温度 30.8（书 30.5）；θse：62.1→56.2℃（书 68→60，结论一致）；850–800 近中性（53.5→53.6）；气块-环境 ΔTv 表（800 hPa 转正 = LFC）
- E3 习题 8：未订正 23.9（书 24.2）；虚温订正 26.5（书 26.7）；订正增益 ~11%（书 10.5%）
- E4：夹卷率-云顶表（0.2→16e-4 对应云顶 275→793 hPa）；M(z)/Mb（深 5.75 / 浅 1.00 / 仅夹卷 2.72）；scale_fac 表（27→1 km：1.36→53.56；3 km=19.05）；浅对流闭合 zdhpbl/zdh=0.0727（再除 √scale_fac2）
- 图：doc/figs/ch15_layer_subsidence.png、ch15_sounding_stability.png、ch15_parcel_velocity.png、ch15_massflux_scaleaware.png

### 勘误/口径记录（ch15）
- **印刷符号勘误**：书印刷页 167 结论②"相当位温梯度的负值区（∂θe/∂z＞0）"——括注与"负值区"及 (6.9.5) 矛盾；2 倍放大复核（workspace/tmp/ch15_p0181_bottom.png）确认印刷如此；按"负值区"（∂θe/∂z＜0）自洽读数处理，教材已注明
- 例题 6.2 与复算的 ~1 hPa 差 = Γ1 取整（0.0032，两位有效数字）；作"口径"记录（非勘误）
- θse 绝对值口径差（本复算 vs 书答案 2–6 K）：(6.3.8)+精确 LCL vs 埃玛图读图；判据符号一致
- 习题 8 虚温订正的环境湿度口径：书按"环境干空气"理解（q_e=0 → 26.5 接近书 26.7；若 q_e=qs900 只有 23.1）
- 考点节自拟待 PPT 校准（同 ch12–ch14 口径）
- E4 夹卷柱的饱和调整必须用牛顿迭代（朴素不动点因 Lv/cp·dqs/dT≈3>1 发散）——ch13 教训的复现，已写入教材 15.8.4

## ch16 陆面过程族 —— 已核验（2026-10-11 凌晨，批次 2 第七章）

交付：`doc\ch16_land_surface_family.md`（816 行；3 个 mermaid + 3 张自算图；PPT 未到，考点节自拟并标注）

### 书页直读（扫描页 → 印刷页换算 已核验）
- 4.2 大气质量及其垂直分布 p55–56（page_0069–0070）：(4.2.1) m0=∫ρdz=p0/g（g=9.8、p0=985 hPa → 10044 kg/m²；标注取常数 g 低估）；R_E=6.37×10⁸ cm；总质量 5.12×10¹⁵ t；固体 6.0×10²¹ t、海洋 1.40×10¹⁸ t；**气圈≈水圈 1/273、不及陆圈 1/10⁵**；(4.2.2) m=(p1−p2)/g、(4.2.3) 占比=(p1−p2)/p0；**表 4.1**（11 km 77.6%/226.4 hPa；30 km 98.8%/11.97；50 km 99.92%/0.8；90 km 99.999%/1.8e-5）；"薄壳"引语
- 4.3 引言 + 4.3.1 p56（page_0070）：海洋 3.6×10⁸ km²/71%/均深 3800 m；水汽主要来源=副热带海洋蒸发；最大热源/缓冲器；海流工具；气团源地；ENSO；盐度 3.47%；密度 1.0255–1.0285 t/m³ ≈空气 800 倍；**总质量 267×大气、比热 4×、热容 3120×、上层 3 m=整个大气**；日变化 <0.1℃、年变化几度；三层（季节变化层 ~100 m/主跃层 1000–1500 m/下均匀层）；季节性温度跃层（图 4.6 B/D 线）；**90% 太阳辐射被约 10 m 吸收 → 周日温度跃层**
- 4.3.1 续 p57（page_0071，ch15 轮直读已录）：水温随深度（1000 m→4–5℃、2000→2–3、3000→1–2；全球均温 3.5℃、75% 在 0–6℃）；**50% 太阳辐射到达地表、海洋吸收大部分；海洋温度日变化达 15–20 m 深、年变化 200–300 m 深（土壤 ~0.1 m / 2–3 m）**；大气热源主要是地球表面、海洋最重要
- 4.3.2 + 图 4.8 p57–58（page_0071–0072）：海流五因素；风海流；速率比气流小 2 个数量级；暖/冷洋流与环流方向；墨西哥湾暖流/黑潮；"若无海流…温差将更大"；图 4.8 三要点
- 第四章习题 p59–60（page_0073–0074）；**答案页 p545（page_0559）**：3.(1) 5.4 g/kg、284.08 K、1.23 kg/m³；3.(2) 1351.4 gpm；3.(3) 8.3 kg/m²、0.83 cm；4. 6.66×10¹⁰ t；5. 8179 kg/m²、80%

### 源码锚点核验（本轮全部实核；补出 ch15 轮未定的全部数值细节）
- `phys/module_surface_driver.F`：`sfclay_select`（1 SFCLAYREV/2 MYJSFC/3 GFSSFC/4 QNSESFC/5 MYNNSFC/7 PXSFC/10 TEMFSFC/89 IDEALSCMSFC/91 SFCLAY）与 `sfc_select`（1 SLAB/2 LSM=Noah/3 RUC/4 Noah-MP/5 CLM4/6 CTSM/7 PX/8 SSiB）双 SELECT CASE；Noah/slab 以 **DTBL** 步进；**ZLVL=0.5·DZ8W(i,1,j)**；`ICE==-1`→SFLX_GLACIAL；urban 初始化链路（urban_param_init/urban_var_init）；NLCD40 时 IVGTYP 23/25→24
- `phys/module_sf_noahlsm.F`：
  - **PENMAN 逐式实测**：`T24 = SFCTMP**4`（线性化参考=气温，非皮温）；`RR = EMISSI*T24*6.48E-8/(SFCPRS*CH) + 1 + 降水项`（6.48e-8=4σRd/cp，可改写为 1+4εσT³/RCH）；`DELTA = ELCP1*DQSDT2`；`FNET = FDOWN - EMISSI*SIGMA*T24 - SSOIL`；`RAD = FNET/RCH + TH2 - SFCTMP`；`A = ELCP1*(Q2SAT-Q2)`；`EPSCA = (A*RR + RAD*DELTA)/(DELTA+RR)`；`ETP = EPSCA*RCH/LVS`；ELCP=2.4888e3、LSUBC=2.501e6、LSUBS=2.83e6
  - **NOPAC 皮肤温度线性化**：`YYNUM = FDOWN - EMISSI*SIGMA*T24`；`YY = SFCTMP + (YYNUM/RCH + TH2 - SFCTMP - BETA*EPSCA)/RR`；`ZZ1 = DF1/(-0.5*ZSOIL(1)*RCH*RR) + 1`；`T1 = (YY + (ZZ1-1)*STC(1))/ZZ1`；`SSOIL = DF1*(STC(1)-T1)/(0.5*ZSOIL(1))`（等价 2λ1(STC1−T1)/DZS1）
  - BETA 诊断（SFLX 末：ETP≤0→BETA=0；ETP<0→BETA=1；否则 BETA=ETA/ETP）
  - TDFCND：THKQTZ=7.7/THKO=2.0/THKW=0.57/THKICE=2.2；THKS=THKQTZ^QZ·THKO^(1−QZ)；XU=XUNFROZ·SMCMAX；THKSAT=THKS^(1−SMCMAX)·THKICE^(SMCMAX−XU)·THKW^XU；GAMMD=(1−SMCMAX)·2700；THKDRY=(0.135GAMMD+64.7)/(2700−0.947GAMMD)；AKE 冻结混合（AKEI=SATRATIO；AKEL=log10(SATRATIO)+1 当 >0.1）；DF=AKE(THKSAT−THKDRY)+THKDRY；OPT_THCND=2 对 SOILTYP 3/4 走 McCumber-Pielke（PSIF=PSISAT·100·(SMCMAX/SMC)^BEXP；PF≤5.1→420e^−(PF+2.7) 否则 0.1744）
  - HRT：HCPCT=SH2O·4.2e6+(1−SMCMAX)·CSOIL_LOC+(SMCMAX−SMC)·1004+(SMC−SH2O)·2.106e6（urban CSOIL_LOC=3.0e6）；CI/BI/AI 三对角与 RHSTS；底部 DENOM=0.5(ZSOIL(3)+ZSOIL(4))−ZBOT=6.5 m、DTSDZ2=(STC(4)−TBOT)/DENOM；SHFLX 末尾同式给出 SSOIL
  - NOPAC 顺序确认：EVAPO→SMFLX→BETA→TDFCND→DF1*=EXP(SBETA*SHDFAC)（SBETA=−2.0）→YY/ZZ1→SHFLX(HRT+HSTEP)
  - 城市特例：NOPAC 内 `IF (VEGTYP == ISURBAN) DF1=3.24`；SFLX 内 ISURBAN 覆盖 SHDFAC=0.05/RSMIN=400/SMCMAX=0.45/SMCREF=0.42/SMCWLT=0.40/SMCDRY=0.40
  - REDPRM：SATDW/F11/REFSMC/WLTSMC 四式**全部为注释**（紧接 "NOTE: SATDW = BB*SATDK*..." 的注释块）；KDT=REFKDT·DKSAT/REFDK；SLOPE=SLOPE_DATA(SLOPETYP)；FRZFACT；SLOPETYP 定义 1/2/3/4/5/6/7/9（0–8/8–30/>30/0–30/0–8&>30/8–30&>30/全/冰川）
- `phys/module_sf_noahdrv.F`：**DQSDT2=Q2SAT*A23M4/(SFCTMP−A4)²，A2=17.67、A3=273.15、A4=29.65、A23M4=A2(A3−A4)**（Bolton 1980 式）；Q2SAT=QGH/(1+QGH)；雪面 E2SAT=611.2·exp(6174(1/273.15−1/T))、DQSDT2 雪支 6174/T²
- `share/module_soil_pre.F`：init_soil_depth_2 → DZS=(0.1,0.3,0.6,1.0)（ZS 层中 0.05/0.25/0.70/1.50；ZSOIL 界面 −0.1/−0.4/−1.0/−2.0）；非 4 层致命
- 三张 TBL 实读 + WPS GEOGRID.TBL 条目（LANDUSEF/SOILCTOP/SOILCTEMP 系）与 namelist 全条目（详教材 16.4/16.6 表）
- 其余方案文件逐一打开（slab/ruc/noahmp/clm/ctsm/px/ssib 与面层族）

### 实验（workspace/scripts/ch16_experiment.py；日志 workspace/logs/ch16_experiment.log；图 3 张）
- E1 能量平衡日循环（loam，CH=0.008，LWDN=285，spin-up 3 天 + 记录 1 天，全显式土层 + brentq 精确皮温）：
  - 湿土 θ=0.30：白天均 Rn/H/LE/G=316.4/20.6/214.6/81.1；夜间 −72.5/−46.8/+54.3/−80.0；白天蒸发份额 0.911；T1 28.1/8.3℃；夜间逆温 5.80 K
  - 干土 θ=0.15：白天 284.6/71.2/132.8/80.5；夜间 −79.3/−34.1/+25.5/−70.6；份额 0.650；T1 35.5/9.3℃；逆温 4.84 K
  - 闭合：瞬时 max|Rn−H−LE−G|=2.0e-11 W/m²；日累计失配 3.6e-14 MJ/m²；柱收支 telescoping 差 4e-9%（湿）/2e-10%（干）
  - **线性化解体检**：同公式口径 max|T1_lin−T1_noah_exact|=0.0387 K（湿）/0.2591 K（干）；残差 ≤1.636/9.002 W/m²；公式口径差（Penman-BETA vs 精确 qsat(T1)）max 0.773/3.094 K（正午 +0.757/+3.005）
- E2 阻尼深度（隐式三对角 + 解析初值；末周期单频拟合）：
  - 六例数值 vs 解析：偏差 −0.54%/−0.55%/−1.07%/−0.06%/−0.10%/−0.22%（土壤日/纯水日/海洋日/土壤年/纯水年/海洋年）；相位斜率与 1/D 逐例吻合
  - 土壤（λ=1.337、C=2.382e6 → κ=5.61e-7）：D日=0.124、D年=2.37 m（对书 0.1/2–3 m）；纯水分子（1.4e-7）：0.062/1.19 m；海洋有效（8.5e-3）：15.29/292.1 m（对书 15–20/200–300 m）
  - 书值反演 κ_eff：17.5 m→1.11e-2、250 m→6.23e-3 m²/s；海洋滞后 15 m=3.75 h、30 m=7.49 h（1/e 深度=T/2π=3.82 h）
- E3 SOILPARM：四式全表互核（常规类最大偏差 F11=0.60（SILT 表 0.162 vs 式 0.764；SANDY CLAY LOAM −1.491 vs −1.534）、REFSMC=0.062（BEDROCK 0.17 vs 0.108）、WLTSMC=5e-4；SATDW 相对 0.4438%；特殊类 17–19：F11=8.33/REFSMC=0.062/WLTSMC=0.108）；类间表（θ=0.25：SAND β=1.000/λ=2.614/KDT=69.9；CLAY 0.409/1.020/1.46；D日 0.110–0.174 m）；可行水量 19.4–39.2 mm
- E4 书习题复算：q=5.44 g/kg、Tv=284.09 K、ρ=1.2263（书 5.4/284.08/1.23）；**Z=1351.4 gpm 逐位（g=9.80665；9.78 则 1355.1）**；水汽 8.32 kg/m²、0.832 cm（书 8.3/0.83）；习题 5：8180 kg/m²、79.0%（书 8179/~80%）
- 图：doc/figs/ch16_energy_balance.png、ch16_soil_diffusion.png、ch16_soilparam.png

### 勘误/口径记录（ch16）
- 书"海洋质量/大气质量"两处口径：4.2 的 1/273（5.12e15 t 口径）与 4.3.1 的 267 倍（5.27e15 t 口径）——同一比值的两种大气总质量估计（详教材 16.1.2）
- 表 4.1 的 77.6% 由 p0=985 hPa 与 1013.25 两个口径混用（教材 16.9.2 第 2 题）
- 习题 3(2) 必须 T_v + g=9.80665 才逐位对台 1351.4（T 或 g=9.78 都差 3–4 m；作"口径"记录）
- SOILPARM 表内三处表-式不符（SILT 5 F11、SANDY CLAY LOAM 7 F11、BEDROCK 15 REFSMC）+ PLAYA/LAVA/WHITE SAND 三类人工特设——"信表不疑式"，教材 16.6.1/16.8.3 已注明
- F11/SATDW/REFSMC/WLTSMC 四式在 4.8.0 全为注释（读表直接用列值）；F11 在计算链中已不再被使用（仅保留读入）
- 考点节自拟待 PPT 校准（同 ch12–ch15 口径）
- 两处"命名混淆"提示：`module_sf_noahlsm.F` 的变量名 DF1 实为热传导率（W/m/K，非扩散率）；`module_soil_pre.F` 的 ZSOIL 为层底界面（负值）——教材已按源码口径写明

## ch17 城市冠层专章 —— 已核验（2026-10-11 凌晨，批次 2 第八章）

交付：`doc\ch17_urban_canopy.md`（405 行；2 个 mermaid + 2 张自算图；六段式 + "论文2 对接"节替代考点透视——书前 6 章无城市考点）

### 源码核验（全部本地实核）
- 分发真入口在 `phys/module_sf_noahdrv.F`：`IF (SF_URBAN_PHYSICS == 1)` → `CALL urban(...)`（三处：lsm 主体/mosaic 等）；`== 2` → `CALL BEP_BEM(…)`（BEP 数组：trb/tw1/tw2/tgb、sfw/sfr/sfg、a/b 系数）；`== 3` → `CALL BEP_BEM(…)`（追加 BEM：tlev/qlev、tw1lev/tw2lev、tglev、tflev、sf_ac/lf_ac/cm_ac、ep_pv/t_pv、sfvent/lfvent、sfwin、绿屋顶 sfrv/lfrv/dgr、drain 系）；`module_sf_clm.F` 另有自己的 CALL urban
- `module_surface_driver.F`：实参表携带全部 urban 数组（sh/lh/g/rn/ts_urb2d、frc/utype_urb2d、trl/tbl/tgl_urb3d、urb_map_*、num_urban_hi/ndm 等）
- `module_physics_init.F`：`IF (SF_URBAN_PHYSICS==1/2/3)` → `CALL urban_param_init(DZR,DZB,DZG,num_soil_layers,sf_urban_physics,use_wudapt_lcz,…)` + `CALL urban_var_init(…LCZ_1..LCZ_11…)`；LCZ 守卫 fatal："USING URBPARM_LCZ.TBL WITH OLD 3 URBAN CLASSES. SET USE_WUDAPT_LCZ=0"
- **SLUCM**（`module_sf_urban.F`）：血统 1999 Kusaka→2001→2003→2005 Chen/Tewari→2014 Jiachuan Yang→2024/2025 Yuqi Huang/Chenghao Wang（urban-NbS）；CGS 单位（CP=0.24/EL=583/SIG=8.17e-11）；`urban` 60+ 实参；`bisection` 求皮温（TSP,PS,S,EPS,RX,SIG,RHO,CP,CH,UA,QA,TA,EL,BET,AKS,TSL,DZ,TS）；`multi_layer`（KM,BOUND,G0,CAP,AKS,TSL,DZ,DELT→TSLEND）/`force_restore`（TS_SCHEME=1/2）；`CH_SCHEME=2`（Narita 1997）/1（M-O，`mos`）；`SFCDIF_URB` 含 AKANDA_URBAN=1.29；`louis79/82` 备用；内嵌 Noah 土壤链（DIREVAP/TRANSP/SMFLX/SRT/SSTEP/WDFCND/ROSR12/SHFLX/HRT/HSTEP/TBND/TDFCND）；NbS 群（kanda_kawai_svf/SHADOW_TREE/STOMATAL/LELEAF/force_restore_tree/ROOT_UPTAKE/VF_TREE_ANALYTICAL）
- **BEP**（`module_sf_bep_bem.F`）：`BEP_BEM`→逐格 `BEP1D`；子程序 param/interpol/averaging_temp/modif_rad/surf_temp/roof_temp_veg/buildings/urban_meso/interp_length/shadow_mas/shade_wall/long_rad/short_rad_dd/gaussj/soil_moist/soil_temp(_veg)/invert；常量 nbui_max=15（须 ≤nz_um）；视角因子 fww(nz_um,nz_um,ndm,nurbm)/fwg/fgw/fsw/fws/fsg（BLM 2002 附录 A）；`roof_frac=FRC_URB2D·bs/(bs+ws)`（实测）；urban_map_* 尺寸校验 fatal（下限公式 nbui_max*nz_um*ndm*max(nwr_u,ng_u) 等）
- **BEM**（`module_sf_bem.F`）：BEM 主控（长实参表：albrof/emrof/krof/csrof/dzrof、albwal/emwal/kwal/cswal/dzwal、dzflo/csflo/kflo、dzgrd/csgrd/kgrd、pwin/cop/beta/sw_cond/timeon/timeoff/targtemp/gaptemp/targhum/gaphum/perflo、gr_frac_roof/pv_frac_roof）；子程序 hsfluxpv/wall(_gr)/wall_coeff/hsinsflux/int_rsrad/int_rlrad/algebra_short/algebra_long/fluxroo/phirat/phiequ/fluxeqocc/fluxvent/fluxcond/regtemp/reghum/air_cond；**模块级标量参数实测**：emins=0.9、albins=0.3、thickwin=0.006、cswin=2.268e6、temp_rat=0.001、hum_rat=1e-6、effpv=0.19
- **`module_bep_bem_helper.F` 勘正**：实为 3 行小模块（`integer, save :: nurbm`）——方案 v2 原文预期（街谷几何/TKE 在此）不成立；几何/TKE 均在 `module_sf_bep_bem.F`
- 兼容矩阵源码实证：`module_bl_boulac.F`（`flag_bep` + a_u_bep 实参 + 内部 if(flag_bep) 塞三对角）、`module_bl_keps.F`、`module_bl_shinhong.F` 收 a_u_bep；README 白名单=YSU(1)/MYJ(2)/BouLac(8)；`b_q_bep` 仅 ==3 参与（noahdrv 内预置 0）
- Registry：`MH_URB2D`（i01r）、`FRC_URB2D`、`UTYPE_URB2D`；ch06 轮已录 URB_PARAM 维数 132

### 表与数据链路核验
- `run/URBPARM.TBL`（USGS 首段 3 类，逐字段实读）：ZR 5/7.5/10；SIGMA_ZED 1/3/4；ROOF_WIDTH=ROAD_WIDTH 8.3/9.4/10；AH 20/50/90；ALH 20/25/40；AKANDA_URBAN 1.29；DDZR/B 0.05×4、DDZG 0.05/0.25/0.50/0.75；BOUND* 1；CH_SCHEME 2；TS_SCHEME 1；AHOPTION/ALHOPTION 0；**AHDIUPRF 24 值（01h 起，峰 1.00@17h、谷 0.07@04h）**；ALHSEASON 0.43/1.00/0.54/0.40；ALHDIUPRF 48 值；OASIS 1.0；IMP_SCHEME 1；PORIMP 0.45；DENGIMP 0.001/0.0002/0.001；IRI_SCHEME 0；GROPTION 0；FGR 0；DZGR 0.05/0.10/0.15/0.20；FVG 0.2；TREEOPTION 0；表面物性 ALBR/B/G=0.20、EPSR/B=0.90、EPSG=0.95、CAPR/B=1.0e6、CAPG=1.4e6、AKSR/B=0.67、AKSG=0.4004、Z0R/G=0.01、Z0B=1e-4、TRL/B/GLEND=293
- WPS `geogrid/GEOGRID.TBL`：URB_PARAM（NUDAPT44_1km/gloucp2020_30s，num_urb_params 维）、FRC_URB2D（urbfrac_nlcd2011/gaia2020）、IMPERV（nlcd2011_imp/gaia2020）、CANFRA（nlcd2011_can）、**MH_URB2D/ZD_URB2D/Z0_URB2D/BUILD_AREA_FRACTION/LF_URB2D_S（y2010_urb/y2050_urb，slucm/urban_params/20XX/{H_avg,d,z_0,lambda_p,lambda_f}/）、AHE（y2010_ahe/y2050_ahe，slucm/AHE_2010s/2_bytes/）**
- README.namelist：sf_urban_physics 0/1/2/3（Noah/Noah-MP only；2/3 仅 YSU/MYJ/BouLac）；num_urban_* 默认 1、BEP/BEM 值 2/10/10/18（BEM 加 10/10/15）；use_wudapt_lcz 0/1；slucm_distributed_drag（仅 =1，需 3 个额外 2D 场）；distributed_ahe_opt 0/1/2

### 实验（workspace/scripts/ch17_experiment.py；日志 workspace/logs/ch17_experiment.log；图 2 张）
- E1 城市等效表面 vs 乡村（同强迫、CH=0.008 微风）：城市白天 Rn/H/LE/G=227.7/168.6/**0.0**/59.1、夜间 −76.3/−25.6/0.0/−50.6；T_s 最高 51.3℃/最低 10.1℃；乡村（loam θ=0.30）白天 315.8/21.6/216.4/77.9、夜间 −74.7/−42.6/+59.4/−91.5、T_s 28.1/8.8℃；**城市−乡村 T_s：白天 +15.5 K、夜间 +1.8 K（最大 +23.2 K@12.8h）→ 表皮温差"昼强夜弱"**；夜间 G 差 +40.9；CH×2 敏感性：峰值降 9.6 K（51.3→41.8℃）
- E2 人为热（AHOPTION=1）：20/50/90 W/m² → ΔT_s 日均 +0.68/+1.69/+3.03 K（白天均 +0.91/+2.27/+4.08，夜间均 +0.45/+1.11/+2.00）——ΔT≈AH(t)/有效导纳（~28 W/m²K）；绿量（FVG=0.2→β_eff=0.18）：白天 −6.67 K、夜间 −1.61 K
- E3 URBPARM 实读段与 AH 日剖面图（峰/谷、双峰结构、默认开关全关）
- 图：doc/figs/ch17_urban_energy.png、ch17_ah_profile.png
- **（预留）集群双跑**：兰州 d02 sf_urban_physics=0 vs 1，24 h A/B（T2/HFX/TSK 城市格点）——未执行，入复核清单第 12 条

### 口径/勘正记录（ch17）
- `module_bep_bem_helper.F` 内容勘正（仅 nurbm 一行变量）——见上
- 表皮温度口径 vs 2 m 气温口径的"昼强夜弱/夜强昼弱"差异：本章实验只含辐射-表面过程（无稳定度反馈），教材 17.1.3/17.6 明写，2 m 口径留 ch19 集群双跑
- 城市"等效表面"简化（三表面压缩为单柱、无街谷辐射）为本章轻轨实验的口径声明
- AHOPTION/ALHOPTION 默认全关 → 城市模拟必须显式打开（教材 17.2.3 提示；AHE 数据与 AH 表值双计的风险在 17.7.3 提示）
- 修正了一个 Python 脚本内字符串引号与语法问题（ascii 引号嵌套）；正文最终经 `workspace/scripts/_fix_quotes.py` 全角化（57/57 配对；mermaid 代码块内 34 个 ASCII 引号保留）

---

## 2026-10-11（ch18 写作轮：理想实验入门 + 集群三算例实跑）

### 源码核验（全部本地实核，`source\WRFv4.8.0\WRFV4.8.0\`）
- `test/` 下 EM 相关目录共 **15 个**：em_b_wave / em_convrad / em_esmf_exp / em_fire / em_grav2d_x / em_heldsuarez / em_hill2d_x / em_les / em_quarter_ss / em_real / em_scm_xy / em_seabreeze2d_x / em_squall2d_x / em_squall2d_y / em_tropical_cyclone
- **编译期钥匙**（顶层 `Makefile` 各 `em_*` 规则实测）：`IDEAL_CASE=ideal` → hill2d_x/quarter_ss/convrad/squall2d_x/squall2d_y/grav2d_x/b_wave/seabreeze2d_x/**les**（9 个）；`=fire`→em_fire；`=heldsuarez`→em_heldsuarez；`=scm_xy`→em_scm_xy；`=tropical_cyclone`→em_tropical_cyclone；`=real`→em_real（含 ndown/tc）
- **链接行**（`main/Makefile` 原文）：`$(SOLVER)_ideal : module_initialize ideal_$(SOLVER).o` → `$(LD) -o ideal.exe … ../dyn_$(SOLVER)/module_initialize_$(IDEAL_CASE).o`；`$(SOLVER)_real` 目标复用同一 `IDEAL_CASE`；**`wrf.exe`（`wrf` 目标）不链接任何 `module_initialize_*.o`** → 同 IDEAL_CASE 家族共享同一二进制
- **运行期钥匙**（Registry）：`Registry.EM_COMMON` 记 `rconfig integer ideal_case namelist,ideal 1 0 rh`（默认 0）；package 行 10 条 `realcase=ideal_case==0 … hill2d_x==1 … les==9`（3452–3461 行）；生成物 `frame/module_state_description.F` 实测含 `INTEGER, PARAMETER :: realcase = 0 / hill2d_x = 1 / … / les = 9`
- **`dyn_em/module_initialize_ideal.F`**（2252 行，入口 init_domain→init_domain_rk；尾部 init_module_initialize/get_sounding(1767–1925)/get_sounding_b_wave(1969–2113)/read_input_jet(2200–2249)）：12 处 `SELECT CASE(ideal_case)` 分发（ideal_constants / ideal_landmap / ideal_levels / ideal_sounding / ideal_terrain / ideal_pert / ideal_surfacet / trajectories / tracers 等）
  - levels 三策略：指数拉伸（`z_scale=8000/ztop`，hill2d/quarter_ss/squall/grav2d/b_wave）；读 namelist `eta_levels`（convrad/seabreeze，校验首 1.0/末 0.0/单调递减）；**均匀**（les，`stretch_grid=.false.` → `znw=1−(k−1)/(kde−1)`，40 层/2000 m → dz≈51 m）
  - landmap：各分支 `CALL nl_set_map_proj(1,0)` + `msf*≡1` + `sina=0/cosa=1/e=0`；**f 值实测**：hill2d/quarter_ss/squall/grav2d=0；b_wave=1e-4；les=1e-4；convrad=2.5e-5（xlat=10，全海洋 lu=16）；seabreeze=0（xlat=30，陆 50 点）
  - terrain：hill2d_x `ht=hm/(1+((i−icm)/xa)²)`（hm=100/xa=5）；les 预留编译期 MTN/EW_RIDGE/NS_RIDGE（500 m、中心 7×7）
  - pert：quarter_ss 暖泡 +3 K（水平 10 km、垂直中心 1.5 km/半径 1.5 km、`cos²(½πRAD)`）；grav2d_x **冷泡 −15 ℃**（x 半径 4 km、垂直中心 3 km/半径 2 km、帽函数 `(cos(πRAD)+1)/2`，注释引 Straka 1993）；les `0.1K×(rand−0.5)` 最低 4 层；每扰动后 rebalance hydrostatically
  - surfacet 三口径：default 前三层外推 `tsk=cf1T1+cf2T2+cf3T3`；convrad/les `tsk=θ_surf·(p_surf/1000mb)^κ`；`tmn=tsk−0.5`
  - 基态/全态链：`p_top=interp(p_in,ztop)` → c3/c4/c1/c2（hybrid_opt 0/1/2/3 分支）→ 每列 `MUB=pd_surf−p_top`、`pb`、`t_init`、`alb`、`phb`（"exact hydrostatic"注释）→ 湿探空二插 → `MU_1/MU_2/MU0` → 顶向下积分 `p` → `al/alt`、`ph_1`
  - `get_sounding`：qv g/kg→g/g、p mb→Pa；ρ_surf 含虚温 `(1+0.608qv)`；**湿探空自下而上 10 次迭代** `pm(k)=pm(k−1)−½Δz(ρ(k)+ρ(k−1))g·qvf1`；**干探空自顶向下** `p(k)=p(k+1)+½Δz(ρ(k)+ρ(k+1))g`
  - `read_input_jet`：二进制 unformatted，头 `ny_in,nz_in`（须 =80/64），随后 u/θ(t)/ρ 三个 `ny×nz` 场，`zk=125+250(k−1)`
  - `main/ideal_em.F`：`PROGRAM ideal` → `alloc_and_configure_domain` → `this_is_an_ideal_run=.TRUE.` → `med_initialdata_output` → `construct_filename1('wrfinput')` → `output_input`；**仅 `specified` 时写 wrfbdy**；打印 `SUCCESS COMPLETE IDEAL INIT`
- **run_* 优先于 end_***（`share/set_timekeeping.F` 实测）：`run_days/hours/minutes/seconds` 任一 >0 即用 `run_*` 构造 run_length，忽略 `end_*`（quarter_ss 的 `run_minutes=60` 覆盖 `end_minute=120`，实跑 60 min 印证）
- `compile` 脚本：`-j` 只接受 2–20（源码字符串比较 `second_word >= "2" && <= "20"`），超限 echo "badly formed -j option…" 并回退 `-j 2`；`setenv A2DCASE/A1DCASE`（名字含 2d / scm）在 4.8.0 全树（排除 var/）无消费者（考证注记）
- `registry.io_boilerplate`：`history_interval_m` 单位 = MINUTES（4.x 的 `_d/_h/_m/_s` 族）
- 各算例 README 实读：README.les（tke_heat_flux=0.24、f=1e-4、c_s/c_k 非默认、shalconv 变体）、README.quarter_ss（Weisman-Klemp 1982 探空、diff_opt/km_opt=1 为常系数）、README.grav2d_x（Straka 1993 密度流基准、um=0/20 两探空、100/200/400 m 三分辨率）、README.convrad（1 km、101²、35 层、WSM6+RRTMG+slab+YSU、bucket）、README.seabreeze（陆 50 点、lm 可改、8 tracer、日循环）、README.heldsuarez（HS94、1000 天）、README.scm_xy（3×3、auxinput3=force_ideal.nc、input_soil 格式）、README.tropical_cyclone（Jordan 1958 探空、Rotunno-Emanuel 1987 涡旋、f=5e-5、SST=28℃、rad_nudge=1）、README.fire（create_links.sh 多场景）

### 集群实测（`cpu` 分区，singularity + oneAPI 2026 ifx，dmpar 构建）
- **作业 439699（cpu104，第一轮）**：整树 `cp -a build/WRF → ch18_exp/WRF-ideal`（8432 文件/1.3 GB/**约 17 min**，≈8 文件/秒，NFS 元数据瓶颈）；`tcsh ./compile em_les -j 64` → `-j` 被拒回退 `-j 2`，**rc=0 / 69 s**（树内已有全部 `.o`，实为增量重链接）；产物 `main/wrf.exe`（md5 **e81b501625f9587635de53dfc0470a0e**）、`main/ideal.exe`（md5 **3b4cf57cc4da0143a17839199a350f4d**）；real/ndown/tc.exe 时间戳未变
  - 首轮 em_les（np=4）**段错误**（4 rank 同 SIGSEGV，rc=255），已写 t=0 一帧
  - 首轮 em_quarter_ss / em_b_wave：**rc=127**，`execvp error on file ./ideal.exe (No such file or directory)` —— `./compile em_les` 只装配了 em_les 目录
  - 旁证：`Max map factor in domain 1 = 0.00` 打印来自 `dyn_em/start_em.F` 读 `grid%msft`（MAPFAC_M；hill2d/quarter_ss/squall/grav2d/b_wave/les 分支只设 msftx/msfty 家族、不设 msft）→ 正常现象；`couple_momentum` 哑元 msft 的实参为 msfty（`module_em.F` 调用处）
- **作业 439708（cpu128，第二轮）**：三目录 `ln -sf ../../main/{wrf,ideal}.exe` 后全部跑通
  - `em_les` np=4 **113 s**（3600 步、0.0183 s/步）/ np=2 **129 s** / np=1 **192 s**（1→4 核仅 1.7×）
  - `em_quarter_ss` np=4 **51 s**（300 步、0.0194 s/步）
  - `em_b_wave` np=4 **86 s**（720 步、0.0506 s/步）
  - 三条 SUCCESS 行：`d01 0001-01-01_01:00:00 wrf: SUCCESS COMPLETE WRF`（les、qss）；`d01 0001-01-06_00:00:00 wrf: SUCCESS COMPLETE WRF`（b_wave）
  - **md5 交叉证据**：ch18 的 `main/wrf.exe` md5 与 `ch05_exp/E_md5_exe_baseline.txt`（em_real 基线）**逐位相同** → em_real 与 em_les 同二进制；real/ndown/tc md5 亦一致
  - mpirun = Intel MPI 2021.18.0

### 诊断（轻轨，`workspace/scripts/ch18_diagnose.py`；日志 `workspace/logs/ch18_diagnose.log`；图 3 张）
- **em_les**（2 帧）：域平均 HFX 0 → **278.6 W/m²**（对 `ρcp·0.24≈289` 同量级，口径差异已说明）；近地 θ 300.00 → 301.50 K；CBL 顶（最大 dθ/dz）1004 → 1059 m
- **em_quarter_ss**（3 帧）：W max 0 / 30.18 / **43.29 m/s**；最低层 θ′ min 0.40 / −2.35 / **−7.18 K**（冷池增强）；RAINNC max 0 / 7.94 / **36.61 mm**；θ′ 全场 max ≈189–191 K（高空位温，非错误）
- **em_b_wave**（21 帧，每 6 h）：地面 P′ 极值带 ±0.1 → **−69.65 / +22.79 hPa**（斜压不稳定指数增长，e 折≈1 天）；|u| max 67.3 → 72.0 m/s
- **重要发现（教学点）**：`PSFC`/`T2` 在 em_quarter_ss 与 em_b_wave 中**全域全时次恒为 0** —— 两算例物理全关（`sf_sfclay_physics=0`、`sf_surface_physics=0`），该类诊断量无方案填写。诊断物理全关算例只能用动力学量（W/T/U/P+PB/QVAPOR）与微物理量（RAINC/RAINNC）
- **`frames_per_outfile=1000` 行为实证**：多帧写同一文件、文件名取首帧时刻 —— em_les 1 文件 2 帧（2.45 MB）、em_quarter_ss 1 文件 3 帧（4.03 MB）、em_b_wave 1 文件 21 帧（83.6 MB）
- 图：`doc/figs/ch18_les_profiles.png`、`ch18_qss_storm.png`、`ch18_bwave.png`

### 口径/勘正记录（ch18）
- **勘正一**：`em_grav2d_x` = 二维**密度流**（Straka 1993 基准，冷泡 −15 ℃ 触发），非"重力波"——ch05 表已改（重力波基准由 `em_hill2d_x` 承担）
- **勘正二**：`em_bubbling` 在 4.8.0 `test/` 中**不存在**（15 个目录无此名）
- **勘正三**：`em_b_wave` 是 **x 周期 + y 对称**（通道模型），非"双向周期"——ch05 表已改
- **勘正四**：`em_esmf_exp` 是 ESMF 海温耦合实验包（需 `ESMF_COUPLING`），非单机算例
- 2D 算例（grav2d/hill2d/squall2d_x/y/seabreeze）官方口径需 **serial + 无嵌套** 构建（窄向仅 3 点）
- `./compile em_xx` 的真实作用 = "重链接 + 装配运行目录"（同 IDEAL_CASE 家族几乎零成本）——ch05 §5.6 速查表新增两条（`-j` 上限 20；"几十秒完成"的原因与核实方法）
- 间歇性段错误（ch18 首轮 np=4、ch08 的 np=64）按"重跑即好、无稳定复现"归档，不作机理定论
- 正文经 `workspace/scripts/_fix_quotes.py` 全角化（182 处转换；余 14 个 ASCII 引号在代码块内，按规则保留）

---

## 2026-10-11（ch19 写作轮：兰州真实个例全流程 + 城市冠层三跑实录）

### 源码核验（本地实核）
- `phys/module_physics_init.F`（`pbl_select` 守卫全表）：YSU 要求 `isfc∈{1,91}`；BouLac 要求 `isfc∈{1,2}`；MYNN 要求 `isfc∈{5,1,2}` 且**显式禁止 BEP/BEM**（`IF ((SF_URBAN_PHYSICS.eq.2).OR.(3)) fatal 'use ysu/myj/boulac with BEP/BEM urban scheme'`）→ 结论：唯一同时容纳 =0/1/3 的组合是 **YSU(1)+sf_sfclay=1**
- `phys/module_sf_noahdrv.F`：`UTYPE_URB = UTYPE_URB2D(I,J)` → `CALL urban(..., UTYPE_URB, ...)`；`ZA_URB = ZLVL = 0.5*DZ8W(i,1,j)`（首层高度=半层厚）
- `phys/module_sf_urban.F`：`read_param(UTYPE, ...)` 全部为 `*_TBL(UTYPE)` 表查找（`ZR/ZDC/Z0C/SVF/R/HGT/...`）；`urban` 内检查 `IF (ZDC+Z0C+2. >= ZA) FATAL_ERROR(...)`；`urban_var_init` 对**普通城市格点硬编码 `UTYPE_URB2D = 2`（"for default. high-intensity"）**，仅 `use_wudapt_lcz=1` 走 LCZ 分支、`slucm_distributed_drag=1` 走分布式分支
- `Registry.EM_COMMON`：`UTYPE_URB2D` 的流标志为 `rd=(interp_fcni)u=(copy_fcni)`（**无 `i`**）→ 实测 `wrfinput_d02` 中**不存在**该变量 → 无法用改输入文件的方式注入；`slucm_distributed_drag` 默认 `.false.`
- `phys/module_sf_bep_bem.F`：`param` 在 `hgt_urb<=0 .OR. lp_urb<=0 .OR. lb_urb<=0` 时回退表值 `ws_u(id,iurb)/bs_u(id,iurb)`（u 类无需 SLUCM 的 ZA 检查）；`icBEPHI_XY` 对 `hi_urb1D` 归一化（`dtot>0`）；`dz_u=5 m`、`nbui_max=15`
- `dyn_em/module_initialize_real.F`：`sf_urban_physics∈{1,2,3}` 时 `FRC_URB2D==0` 且 ivgtyp 城市 → `FRC_URB2D=0.9`（实测 sf1/sf3 wrfinput 中 max=0.9 ✓）
- `share/set_timekeeping.F`：短测必须同时写 `run_*` 与该域 `end_*`（ch08 修正 2 的再次应用）

### 数据可用性实测（ch19 关键发现）
- `GEOGRID.TBL` 有 `URB_PARAM/FRC_URB2D/IMPERV/CANFRA` 条目，但 `/opt/app/wrf/WPS_GEOG` **只有 `NUDAPT44_1km`**（无 `urbfrac_*`/`impfrac_*`/`nlcd2011_*`/`gloucp2020_30s`）
- `geo_em.d02`：`URB_PARAM`(132 维)**全为 0**；`FRC_URB2D` **变量不存在** → 兰州（非美国区）城市参数全面缺位

### 排错链（全部实测，四条）
1. **栈限制**：计算节点 `ulimit -s = 8192`（8 MB）→ `solve_em` 栈溢出 SIGSEGV（作业 439729 对照：默认栈 27 s 崩 / unlimited 后 301 步正常）
2. **方案兼容链**：=3 用 MYNN → fatal（1）；改 BouLac → fatal（2，面层不兼容）→ 定案 YSU(1)+sfclay(1)
3. **城市类型缺失**：=1 报 `ZDC + Z0C + 2m is larger than the 1st WRF level`；探针（439819）实测 `UTYPE=2, ZR=7.5, ZDC=5.718, Z0C=0.333, ZA=8.046` → `ZDC+Z0C+2 = 8.051` 与 `ZA≈8.05` **卡在阈值**；且探针显示 UTYPE=2 说明 `urban_var_init` 的硬编码覆盖了任何回退
4. **运行中改脚本**：`sed -i` 替换正在执行的作业脚本 → `Stale file handle` → exp2 侥幸跑完（SUCCESS 在前）、exp3 被砍在第 4.5 天（439815）→ 重跑 439866

### 最小补丁与三跑
- 沙箱树 `ch18_exp/WRF-ideal` 单行补丁：`module_sf_urban.F` 普通城市格点 `UTYPE_URB2D = 2` → `= 1`（附注释）；`compile em_real -j 8` 增量重建 → `wrf_class1.exe`（md5 **941ba403a1488291da7ddd2102c7a93c**）；200 s 验证 1222 步零 fatal
- 三跑（np=32，5 天两域）：exp1 439828（=1+MYNN，class1）**4202 s**；exp2 439810（=0+YSU）≈3640 s；exp3 439866（=3+YSU，class1）**3086 s**；全部 `SUCCESS COMPLETE WRF`（d01 2025-07-17_00:00:00）
- 基线对照：ch08 439419（=0+MYNN）5 天 2913 s @64 核，CFL 告警 0 条、d01 最大步 7.13 s、d02 最大 3.05 s

### 诊断（workspace/scripts/ch19_diagnose.py；日志 workspace/logs/ch19_diagnose.log；4 图）
- 掩膜：城市 59 格点（FRC>0.5）/乡村 748 格点（FRC≤0 且 LU∈{10,12,14}），d02 中心 31×31 窗口；UTC+7
- **热岛强度**：CTRL-A 3.58/3.73 K（夜/昼）、CTRL-B 3.59/3.20、SLUCM 3.46/3.46、BEP+BEM 3.52/3.34
- **方案净效应**：SLUCM−CTRL-A：夜 −0.113 K / 昼 −0.265 K（最大 3.46 K）；BEP+BEM−CTRL-B：夜 −0.071 K / 昼 **+0.138 K**（最大 1.712 K）
- **空间**：夜 04 LT −3.03…+2.33 K；午后 14 LT −2.69…**+14.58 K**（个别格点，提示不可用局地极值下结论）
- **T-lnP**（07-16 06 UTC=14 LT，城市点，地表 828.6 hPa）：θ=315.95 K、T=26.3 ℃、qv=12.8 g/kg、**LCL=LFC=699 hPa、EL=139 hPa、CAPE=2522 J/kg、CIN=0**
- **T2 vs ERA5**（城市格点日最高）：ERA5 33.1/33.8/34.4/35.0（07-13→16）；CTRL-A 34.5/35.4/36.4/34.4；CTRL-B 34.3/34.7/35.9/35.2；SLUCM 34.3/35.1/36.3/34.6；BEP+BEM 34.2/34.7/35.9/35.2
- **诊断脚本坑三处（已修）**：① 子集丢了 `Times`（改为抽取时带 `Times,XTIME`）② WRF `T` 是**扰动位温**（`θ=T+base_temp`，本例 base_temp=290），直接当温度会得到 LCL≈485 hPa 的荒唐解 ③ MetPy 新版的 `cape_cin` 需位置参数 `parcel_profile`
- **抽取管线坑两处**：① ncks 不能合并"正在写"的 wrfout（只用已关闭文件；已按 SUCCESS 判定）② 城市变量不在 wrfout（`FRC_URB2D` 无 `h` 标志）→ 掩膜取自 `wrfinput_d02`

### 口径与结论（ch19 章）
- 诚实结论：无本地城市参数（FRC 均一 0.9、形态取通用表值、AH 关闭）时，城市冠层方案对 2 m 温度的净效应**小量级（域均 |Δ|<0.3 K）、空间非均匀、日最高几乎不变**；夜间主导因子（人为热）未入场 → 直接指向论文 2 的参数场路线
- 三档统一 class 1 + 三对单变量对照；补丁物理含义与代价写入 19.5.4；教材亦记录"约束驱动设计"三重约束（PBL 兼容 / 面层兼容 / ZLVL vs 城市形态）
- 正文 408 行 + 4 图；`_fix_quotes.py` 全角化 84 处（余 16 在代码块内）

## ch20 段（2026-10-11 下午，改造三级实战：全链实测）
### 构建（干净重建 v3 = 作业 439963，cpu44，12:28→13:07）
- v2 失败根因两处（教材事故⑤⑥）：容器缺 m4 → `frame/md_calls.inc` 0 字节 → `module_io.o` 语法错无 wrf.exe（官方回退 `cp arch/md_calls.inc frame/`）；只改 Registry.EM_COMMON 不触发 `tools/registry`（`REGISTRY = Registry` 拼装文件才是规则先决条件）→ 处置 `touch Registry/Registry.EM`
- 五二进制全部有效：base 720s `9693677383da45cb95d1a4b06810665d`；L1 697s `4cf82c53ec89f732c454d86630df852c`（六点自检全中：state_struct `t2_peak`、allocs_1 `in_use_for_config`、三件生成物 md5 与基线逐位同）；L2a 67s `b967eb5c…` / L2b 58s `74da264f…`（`module_bl_mynnedmf.o` md5 与首轮独立构建逐位同——.o 可复现、exe 不可）；L3 706s `4fe7e09e…`（albrof_2d=1、bem_switch=8）
### 运行（runall = 作业 439976，cpu16，13:07→13:59，np=64）
- **六跑全部 rc=0**：L1a 610s / L1b 610s / L2a 607s / L2b 610s（A 组 24h，输入 ch19 sf0）；L3off 322s / L3on 322s（B 组 12h，注入输入）；L1b `SUCCESS COMPLETE WRF` 实证（重建前 SIGSEGV 通知为旧调试任务残留）
- 输入指纹：A 组 wrfinput_d01=73e20895…/d02=179a2275…/wrfbdy=fd0714be…；B 组 1bd0b65b…/046bdcb5…/27c2f960…
### 抽取（事故⑦：容器内 ncks 静默失败 → stderr 落盘定位 → 两步修复）
- ① 容器内 ncks 全 FAIL（错误被 /dev/null 吞）→ 处置=独立容器外作业（extract2 440034）+ stderr 落盘；② 容器外仍失败：`libnco-4.7.5.so not found`（登录节点系统自带 nco 侥幸成功，计算节点无）→ 修复=所有 ncks 加 `env LD_LIBRARY_PATH=lz_case/lib`；③ L3 2d 再失败：`TS_URB2D not in file`——**Registry DataName 是 `TS_URB`**（TS_URB2D 是 Registry 变量名）；h 位补丁本身有效（`rhd=(interp_fcnm)u=(copy_fcnm)` 合法、ALBROF_2D 成功入 wrfout）
- 终版 stage 24 文件 + `ch20_stage_all_v2.tar.gz` 142.8 MB → 本地 `workspace/data/ch20/stage/`
### 诊断（workspace/scripts/ch20_diagnose.py；日志 workspace/logs/ch20_diagnose.log；3 图）
- **L1**：单调性负步 0/295704；gap(PEAK−逐时max) min 0.0000/max 4.5949 K/域均 0.0599 K、违例 0/308025；**L1a↔L1b 十二变量 max|Δ|=0（位级非扰动铁证）**
- **L2**：域均 PBLH 日最大 1199.4/1635.1/1902.4 m（0.5/1.25/2.5，单调）、时均 474.9/711.9/904.0 m；逐点违例 0.83%/3.10%（min −2527.6/−1592.1 m，源于稳定层混合与 ±200/350 m 约束——"改一行要读全公式"实证）；ΔT2 域均 ±0.1 K 内（时均 −0.000/+0.012 K）
- **L3**：注入场东 44 格 0.8/西 60 格 0.2、on/off 输入一致（max|Δ|=0）；`TS_URB` 开−关东组时均 **−2.846 K**（峰值 −4.114；正午 13 LT 域内 min **−6.67 K**）、西组 −0.089 K（表值对照≈0）；SWDOWN 885 W/m²、RAINNC 19.7 mm、T2 11.4 K、TSK 15.2 K 的差=云-降水-环流非线性反馈（判据二改为三级"应当不变"检验：注入场位级/对照组零效应/RAINC 位级）
### 章节交付
- `doc\ch20_modifying_wrf.md`：正文 + 事故链七条表 + §20.7.1 全书改造案例总索引（27 案）；9 处待填全部回填；图 3 张（ch20_L1_diag/L2_pblh/L3_albedo）；`_fix_quotes.py` 两轮
- 全书补充（同日）：ch01/ch02 新交付；ch03–ch19 补三类专栏（依赖树 10 棵 + 案例库）；ch20 §20.7.1 总索引

## ch21 + 附录 + index 段（2026-10-11 晚，批次 4 收官）
### solve_em.F 结构侦察（全实测，WRF 4.8.0 本地源码）
- 文件规模：`dyn_em/solve_em.F` 5197 行（内含 CMAQ_DRIVER 局部子程序）；part1 2027 行 / part2 1132 行 / small_step 1961 行 / big_step 6758 行 / advect 13046 行 / diffusion 8482 行 / bc_em 1747 行 / em 3165 行 / module_em 之外 ieva 9 子程序（WW_SPLIT/TRIDIAG/advect_*_implicit 等）；solve_em 全 CALL 图 426 条抽取至 `workspace/tmp/ch21_solve_em_F_calls.txt`
- 时间分裂实测：rk_ord 默认 3（Registry rconfig）；time_step_sound 默认 0 → 自动式 `max(2*(int(300*dt/dx-0.01)+1),4)`；rk3 三 stage 步长表（dt/3·1 小步；dt/2·n/2；dt·n）来自 solve_em 装配分支原文；rk_ord==1 分支 fatal "leapfrog removed"
- **物理调用时刻（验收答案）**：`first_rk_step_part1/2` 只在 rk_step==1 执行；part1 内序 = init_zero_tendency→phy_prep→pre_radiation→radiation→surface→pbl→[fire]→cumulus→convtrans_prep→shallowcu→[scm]→fddagd（call map 逐条实测）；part2 内序 = RAND_PERT_UPDATE→calculate_phy_tend→compute_diff_metrics→cal_deform_and_div→cal_helicity→nonlocal_flux/free_atmos_length/meso_length_scale→calculate_km_kh→phy_bc→sfs_driver→update_phy_ten→update_stoch_ten→damptop→tke_rhs→fddaobs→conv_t_tendf_to_moist→vertical_diffusion_implicit/2→horizontal_diffusion_2
- **微物理时刻**：`moist_physics_prep_em→(bulk_dust)→microphysics_driver→moist_physics_finish_em` 在 **Runge_Kutta_loop 结束之后**（L3615 END DO 之后、set_w_surface/after_all_rk_steps 之前）——每时间步一次；修正"微物理在 RK 循环内"的直觉
- rk_tendency（module_em.F）内部 14 步装配序实测：WW_SPLIT→calculate_full/calc_mut_new/calc_mu_uv_1→advect u/v/w/t（weno/显式/implicit 三分支）→set_tend(RTHFTEN)→rhs_ph→horizontal_pressure_gradient→pg_buoy_w→w_damp→perturbation_coriolis/coriolis/curvature→held_suarez_damp→horizontal_diffusion×4→vertical_diffusion×4→sixth_order_diffusion×4→rk_rayleigh_damp→theta_relaxation
- 小步长注释锚点：advance_uv 注释 "x/y pressure gradient: ADT eqn 44/45"；advance_mu_t 注释 "ADT eqn 47" + "mu is not coupled... ww IS coupled"；calc_coef_w 垂直隐式系数 a/alpha/gamma；positive_definite_slab 逐行读（行内守恒重分配）
- 21.6 实验交叉验证：`workspace/scripts/ch21_timestep_audit.py` 重演公式，d01 8000 步 / d02 24000 步与 439419 实测逐位吻合；每步 1+2+4=7 个声波小步；日志 `workspace/logs/ch21_timestep_audit.log`
### 案例库文献核验（ch21 案 28–35）
- SKEBS：`module_stoch.F` 头注原文 = 作者 Judith Berner (NCAR, Apr 2014) + 文献 Berner, Ha, Hacker, Fournier, Snyder 2011, MWR 139, 1972–1995【核验：源码头注】
- WRF-CMAQ：solve_em 末段 aqprep/CMAQ_DRIVER/FEEDBACK_READ + 编译宏 WRF_CMAQ；文献 Wong, Pleim, Mathur et al. 2012 GMD 5【核验：条目经检索证实；页码未核，已在 app_d 标注】
- WENO：`advect_scalar_weno` 头注原文 "5th-order WENO adapted from COMMAS. See Jiang and Shu 1996 JCP 126:202-223; Shu 2003; Bryan 2005 MWR"【核验：源码头注】
- MAD-WRF：`phys/module_madwrf.F` 头注 = 作者 Pedro A. Jimenez；Registry 包 madwrf_mp(mp_physics==96)/madwrf(madwrf_opt==2→tr_qc/qi/qs)/cldinit；solve_em 挂点 cloud_tracer_nudge【核验：源码+Registry；论文条目未核已标注】
- use_theta_m：Registry rconfig 默认 **1**（"theta_m = theta (1 + 1.61 Qv)"）；big_step 9 处分支 + module_bc_em theta_and_thetam_lbc_only【核验】
- Registry 其余核验：damp_opt 默认 3、w_damping 0、epssm 0.1、spec_bdy_width 5/spec_zone 1/relax_zone 4、use_adaptive_time_step .false.；WW_SPLIT 位于 module_ieva_em.F
### 附录与 index
- app_a：`module_model_constants.F` 全常数逐行重读（g=9.81/r_d=287./cp=7r_d/2=1004.5/SVP1=0.6112 kPa/STBOLT=5.67051e-8/KARMAN=0.4/EOMEG=7.2921e-5/OBLIQUITY=23.5/ECCENTRICITY=0.014 等），对照 ch11 §11.4.1 底稿与书附录 C 偏差表
- app_b：ch10–ch17+ch21 术语表汇编 + 工程术语补充（九类）；app_c：全书速查表汇编制（c.0 万能诊断五步 + c.1–c.8 + 改造检查单）；app_d：文献三级标记（核验/通行/线索）+ 数据源致谢（liuyl17 ERA5、WPS_GEOG）
- index.md：全书 21 章+4 附录目录（文件名经 Glob 核对）、使用说明、页码换算规则、阅读路径、修订记录
- `_fix_quotes.py` 六文件全跑（ch21 转 118 处；附录 a–d/index 共 46 处；残余均在代码块内，ch21_check_quotes.py 验证六文件围栏外为 0）

## 批次 5 全书校阅段（2026-10-12 凌晨）
### 交叉引用与死链清查（`workspace/scripts/batch5_linkcheck.py`，全 26 文件）
- WRF_ROOT=source\WRFv4.8.0\WRFV4.8.0、WPS_ROOT=source\WPSv4.7.0 运行时实测解析；扫描统计：章引用 1237（另 35 处书章引用按"书"前缀豁免）、§小节引用 475、markdown 链接 99、反引号路径 79、文件引用 35、跨章表引用 18、附录引用 13、书页换算 4
- 全零项：章缺失/章号异常/文件缺失/附录缺失/书页缺失/换算不符/**源码锚点缺失 0**（phys|dyn_em|main|share|frame|external|Registry|run|test 前缀反引号路径全部命中实际文件）/跨章表缺失 0
- 报告落盘：`workspace\logs\batch5_linkcheck.md`；误报甄别（ch16 方程 \tag 号、源码树 doc/README.*、ch15 书图 10.9/10.18）见 notes.md 批次 5 段
### 事实核验（本轮三源实证）
- 微物理步长：`dyn_em/solve_em.F` L588 `dtm = grid%dt` → microphysics_driver 的 DT 即主步长、每时间步一次（RK 循环后）——据此改写 ch14 §14.5.1"每步多次调用"误表述
- 书 p168（page_0182.jpg）直读：6.10 逆温五类原文含"形成谷地逆温(参见图 10.9)""(参见图 10.18)"——ch15 两处书图引用准确无误
- 书 p143（page_0157.jpg）直读：6.4.2 埃玛图构造——等饱和比湿线由 (2.2.12b)+(2.2.9a) 积分绘制（工作式 (6.4.4) 双曲线），能量证明 a=R∮T d ln(p00/p) 含 p00——ch13 埃玛图节公式引据与书一致；本轮为图注补 q_s/r_s 口径注
- PPT 4《大气分层》直读（workspace\ppt_text\4*.md）：slides 17–20 覆盖 §4.3（海水密度 800 倍/总质量 267 倍/热容量 3120 倍/海洋成层/环流/SST）；全讲无"重点/掌握要点/思考题"页——ch16 §16.0.2 考点标签改"内容页归纳"口径（原"第 4 章课件未到"系笔误）
### 修订清单（13 处，落 ch13/ch14/ch16/ch21/app_a/index 六文件）
- ch13：§13.6.1 补微物理时刻交叉注（→ch21 §21.2.14；落实复核清单 16②）；"图 13.1"两处改"本节末埃玛图"（全书图题无编号体例）；埃玛图图注补 q/r 口径注
- ch14：§14.5.1 part1 枚举补"积云"、微物理位置改"RK 循环之后"；"每步多次调用"句改写（真对比=辐射 radt 低频）；§14.8.1 补"判据量口径"注（书 (6.8.14) 正式量 θse，E1 以 θe 代用、ch15 E2 θse 复算）
- ch16：§16.0.2 标题改"PPT 4《大气分层》§4.3 内容页归纳 + 模式侧自拟"、说明句改"课件在案、无显式考点页"
- ch21：§21.6 两处 file:/// 绝对链接改反引号相对路径体例（两目标文件均在案）
- app_a：a.6 假日志指涉（workspace/logs/ch11_experiment.log 不存在）改指 ch11 §11.6 + `workspace/scripts/ch11_experiment.py`；a.2 补泊松常数 κ_d=R_d/c_pd 行（287/1004.5=0.2857，偏差 0.07%）并与 KARMAN 行互注撞名
- index：§1.2 考点体系说明改实际节名（考点清单+章尾习题节）、"ch13–ch16 待校准"改"ch13–ch15"（ch16 归书第 4 章口径）；§四 修订记录补批次 5 行
### 全角引号终查
- `_fix_quotes.py` 26 文件复跑：全部 converted=0——围栏外 ASCII 引号 0；残余全在 fenced code 内（ch04=96/ch11=50/ch20=30/ch08=22 等均为代码/Registry/日志语法，按约定保留）
### 符号统一横向扫结论
- θse 全书 $\theta_{se}$ 统一、ε 统一 \varepsilon、p_0/p_{00}（初压 vs 标准气压）与 g/g_0（一般 vs 书公式直引）均按书忠实区分、扰动位温警示 ch02/ch10/ch19/app_a/app_c/ch21 六处一致；κ 双义（泊松 0.286 vs 卡门 0.4）经 app_a 公证处互注消除歧义