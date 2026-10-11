# ch20 素材与实验底稿（改造 WRF 三级实战）

**收官状态（2026-10-11 15:3x）**：三级全链闭环（构建 439963 → 运行 439976 六跑 rc=0 → 抽取 24 文件 → 诊断 3 图）→ 章节交付并回填全部待填 → 四件套同步。本文其余段落为过程账（事故链/输入指纹/构建序列），供 ch21 与论文2 复用。诊断终值见 verify_log ch20 段与 doc/figs/ch20_*.png。

时间锚点：2026-10-11 下午（自主会话）
章节文件：doc\ch20_modifying_wrf.md（已交付）

## 十、干净重建 v2 失败 → v3 修复（2026-10-11 12:05–12:50 实测，两处新陷阱）

**作业 439955（v2）结果**：base 构建 661 s、rc=0 但**无 wrf.exe**；L1 构建仅 43 s（40 次 mpif90）、inc/state_struct.inc 无 t2_peak（自检 grep = 0）→ 全部产物无效，已 scancel。两处陷阱：

**陷阱⑤ 容器缺 m4 → 空 md_calls.inc → module_io.o 编译失败**
- 证据链：`compile_re_base.log`: `make[2]: [Makefile:217: md_calls.inc] Error 127 (ignored)` + `/bin/sh: 4: m4: not found`；随后 `module_io.f90(53) error #6218 … (55) dummy argument name is required [DATASET]`。
- 机制：`frame/Makefile`: `md_calls.inc : md_calls.m4` → `if [ "$(M4)" = NA ]`（configure.wrf 里 `M4 = m4`）→ `m4 md_calls.m4 > md_calls.inc`；m4 不存在 → **重定向先建 0 字节文件** → `frame/module_io.F` 第 51 行 `#include "md_calls.inc"` 失去"CONTAINS 声明 + 40 个 wrf_get/put 子程序"（module_io.F 注释原文：*note that this file also includes the CONTAINS declaration for the module*）→ 后续 `INTEGER FUNCTION io_form_…` 被当成说明语句 → 报错。
- 为何现在才犯：clean 删掉了 frame/md_calls.inc（此前树里的是旧构建留下的成品）。
- 处置（官方回退）：clean 后 `cp -f arch/md_calls.inc frame/md_calls.inc && touch`（arch/md_calls.inc 371 KB，与 md_calls.m4 同为 release 时间戳 Jun 9）→ make 视作最新，不再调 m4。

**陷阱⑥ Registry 触发门：只改 Registry.EM_COMMON 不会触发 registry 工具重跑**
- 机制：`configure.wrf: REGISTRY = Registry` → `frame/Makefile`: `module_state_description.F : ../Registry/Registry`；而 `Registry/Registry` 是 compile 脚本拼出来的（警告行 + `Registry.EM`；Registry.EM → include registry.dimspec + registry.em_shared_collection → 后者 include Registry.EM_COMMON）。compile 脚本只在 **Registry.EM 比 Registry 新**（mtime 序位比较）或 Registry 缺失时重拼。
- 本次：补丁把 Registry.EM_COMMON 改到 12:16，而 Registry 停在 11:40（Registry.EM 是 Jun 9）→ 不重拼 → registry 工具**整个没运行**（L1 日志无 `opening Registry` 行；inc/ 全部停留在 12:05）→ L1 白编。
- 处置：clean 后 `touch Registry/Registry.EM`（且 Registry 被 clean 删除 → 编译脚本必然重拼）→ registry 工具重跑 → inc/ 全量刷新。
- 关键理解（可入正文）：registry 工具读 Registry 时会**从磁盘重新 include Registry.EM_COMMON**，所以"门"只是时间戳问题——439915 那次 `touch Registry/Registry` 之所以生效，是打开了下游门（Registry 新于 module_state_description.F），工具重跑即读到已打补丁的 EM_COMMON。**改 Registry 后的规范动作 = 让 Registry/Registry 变新（touch Registry/Registry 或 touch Registry.EM 后由 compile 重拼）**。
- 副作用（有价值）：registry 工具重跑会刷新全部 inc/*.inc 的 mtime → 依赖它们的大量 .o 随之重编 → 这就是 439915 里"touch → 695 s 全树重编"的真正机制。

**v3 作业 439963（已成功，2026-10-11 12:28 → 13:07，cpu44）**：脚本 `ch20_rebuild2_{inner,outer}.sh`；序列 = 还原 → clean+prep → base（clean 全建）→ L1（clean 全建，Registry 级改动必须全量）→ L2×2（增量）→ restore 掉 L1 + L3 补丁 → L3（clean 全建）。日志 `SUMMARY_rebuild2.txt`。

**v3 实测结果（全部有效，五个二进制）**：

| 构建 | 耗时 | wrf.exe md5 | inc 抽查 |
|---|---|---|---|
| base（干净基线） | 720 s | 9693677383da45cb95d1a4b06810665d | t2_peak=0（正确） |
| L1（T2_PEAK） | 697 s | 4cf82c53ec89f732c454d86630df852c | **t2_peak=1** ✓ |
| L2a（thv 0.5） | 67 s | b967eb5c60ddbbc7c52627bdce5695c4 | `module_bl_mynnedmf.o` = cd8cd514…（与首轮独立构建逐位同） |
| L2b（thv 2.5） | 58 s | 74da264f9a47c16b0f5ae0076ab84744 | .o = b60c70a2…（同上） |
| L3（BEM 2D） | 706 s | 4fe7e09e34822bde5e0495ddab71e603 | **albrof_2d=1、bem_switch=8** ✓ |

- L1 六点自检实测：`inc/state_struct.inc` 有 `real ,DIMENSION(:,:) ,POINTER :: t2_peak`；`inc/allocs_1.F` 有 `IF(okay_to_alloc.AND.in_use_for_config(id,'t2_peak'))THEN`；三件 md5 = b1f2b385cdfe045311b650026d5cf28f / 0e97a9147c74015afc036039cca7dff3 / 9edf5f593504bb2a05c1965ae2ce967c（与基线构建及首轮独立构建**逐位相同**）。
- 教训补充：**“脏构建 vs 干净构建”的 L2 .o md5 可逐位复现**；而 wrf.exe md5 因链接的其余对象来源不同而不同 → 判断“哪些对象真重编了”要看 .o，不要看 exe。

**运行作业 439976（ch20_runall，2026-10-11 13:07 起，cpu16，np=64）**：A 组 4×24 h（L1a=base / L1b=t2peak / L2a=thv05 / L2b=thv25，输入 `ch19_exp/sf0`）+ B 组 2×12 h（L3off/L3on，输入 `ch20_exp/input` 注入场）+ ncks 抽取 → `ch20_stage_all.tar.gz`。宿主检查：`ulimit -s = unlimited` ✓。预期 ~1 h。

**输入指纹（已实测入档）**：
- A 组（`ch19_exp/sf0`）：`wrfinput_d01` = 73e20895eac94ddba8ddffbc3dfce50d、`wrfinput_d02` = 179a22754f97427471d0b0d5d9c08fba、`wrfbdy_d01` = fd0714be375b95247381a3862efe2154；与 `ch19_exp/sf0b`（MYNN 套装目录）的同名文件**逐位相同**；sf0 的 namelist 为 YSU，但输入文件本身是 real.exe 的原始产物，可用于 MYNN 运行（num_land_cat=21 / e_vert=50 / soil_levels=4 三项与 ch20_nml24h 一致，已核）。
- B 组（`ch20_exp/input/`，注入版）：`wrfinput_d01` = 1bd0b65ba096416640dd88090ede8057、`wrfinput_d02` = 046bdcb50830fefa5a39c11d3ab612dd（本地 `workspace/data/ch20/input/injected/` 与集群副本逐位一致）、`wrfbdy_d01` = 27c2f9602227a47d72438fe8ebdfdcc4（= `ch19_exp/sf3` 的副本）。
- 注意：ch19 各目录的 `wrfbdy_d01` 内容互不相同（sf0 fd0714be / sf1 4603751d / sf3 27c2f960，大小同为 58724166），原因未深究；**只要每组内部一致**即满足单变量对照要求（A 组四跑同源 sf0、B 组两跑同源 ch20_exp/input）。

**事故⑦（抽取环节）容器内 ncks 失败**：
- 现象：runall 作业（singularity 容器内）里 6 跑 × 2 域的 2D/3D 抽取**全部 FAIL**（时间戳显示每次尝试 ~1 s 即返回；输出被 `>/dev/null 2>&1` 抑制）；而 wrfout 本身正常写出（L1a: 558 MB + 817 MB）。
- 对照实测：**同一命令在登录节点 rc=0**（`env LD_LIBRARY_PATH=$LZ $NC -4 -L 1 -O -v Times,T2,PBLH,HFX,TSK wrfout_d01… /tmp/t1.nc` → 2.3 MB）；甚至**不设 LD_LIBRARY_PATH 也 rc=0**。登录节点上 `singularity exec` 不能复现（`runtime/cgo: pthread_create failed: Resource temporarily unavailable` → SIGABRT，登录节点有线程/进程数限制）。
- 归因：未能完全定位（容器内 ncks 的库解析差异是首选假设，但缺容器内实测证据）。
- 处置：`ch20_extract2_{inner,outer}.sh` —— **抽取改到"无 singularity 包裹"的独立作业**（ch19 `extract_stage.sh` 同款路径），脚本内先试裸 `$NC`、失败再退回 `env LD_LIBRARY_PATH=$LZ $NC`，并把 stderr 收进 `extract2_errors.log`。
- 教材口径：并入 ch20 事故表（与事故①同族：**环境/容器差异导致的"静默失败"**），强调两点——① 抽取步要把 stderr 落盘，别一路 `>/dev/null`；② 能用"和成功先例相同的运行环境"（容器外）就不要另起炉灶。

**教材"改造五步"的检查单**：① 改 Registry 后必须验证 inc/ 真被刷新（grep 新符号），别只看 make 返回码；② clean 之后要确认环境缺什么工具（m4/tcsh）；③ 构建日志里 `Error 127 (ignored)`、"No such file"、`make -i` 的 ignored 标记都可能是真错误；④ 二进制清单必须带 md5 与时间戳，防止"旧文件冒名顶替"。

## 〇、三级设计（定稿）

| 级 | 内容 | 二进制 | 运行 | 单一变量对照 |
|---|---|---|---|---|
| L1 | Registry 加诊断变量 `T2_PEAK`（初始化以来 2m 气温最大值） | wrf_t2peak.exe | 24 h ×1 | L1a(基线 wrf_class1.exe) vs L1b(加变量) —— **非扰动验证** |
| L2 | MYNN PBLH θv 阈值 `delt_thv` 1.25 K → 0.5 / 2.5 K | wrf_thv05/thv25.exe | 24 h ×2 | L1b(1.25) vs L2a(0.5) vs L2b(2.5) —— 单变量（仅一行） |
| L3 | BEM 屋顶参数标量→2D 场 + namelist 开关 + auxinput（论文2 EXP-LIT 技术验证版） | 待定 | 短测 | 开关 on/off |

**为什么要这样配对**：L1b 同时是 L2 的对照；L1a↔L1b 只差诊断变量（应逐位一致或机器精度级），证明"加诊断不扰动物理"（ch04 §4.5.5 承诺的验证）。

## 一、L1 设计（承接 ch04 §4.5 图纸，**已核验**）

- Registry 行（Registry.EM_COMMON 紧邻 T2 之后，io 串 `rhd`）：
  `state    real   T2_PEAK          ij     misc        1         -     rhd      "T2_PEAK"              "2 M TEMPERATURE MAXIMUM SINCE INITIALIZATION"  "K"`
- **清零点**：`dyn_em/start_em.F`（share/start_domain.F 是分发器，EM 实体在 start_domain_em）—— `IF ( .NOT. config_flags%restart ) THEN` 块首（唯一锚点，行 ~1574）。
  - 依据：`share/mediation_wrfmain.F` 的 med_initialdata_input：**先读 wrfinput（T2 经 i01 流载入）→ 再 CALL start_domain**（两分支均如此）→ T2 在 start_domain 时有效（实测：wrfinput T2 = 282.6–298.8 K）。
  - 重启保护：restart 时 input_restart 已读回 T2_PEAK，`.NOT. restart` 守卫避免清零。
- **更新点**：`dyn_em/solve_em.F` 紧随 `CALL first_rk_step_part1(...)`（行 ~842，rk_step==1 每步一次）之后，标准 tile 循环 `MAX`。
  - 依据：T2 的生产者在 first_rk_step_part1 → `CALL surface_driver`（module_first_rk_step_part1.F 行 ~603）。
- 官方"近亲"（写入正文用）：CLWRF 诊断 `output_diagnostics==1` → `T2MAX/T2MIN`（`phys/module_diagnostics_driver.F` → `clwrf_output_calc`，auxhist3，**每输出区间重置**；本变量是"自初始化以来不重置"版）。

## 二、L2 设计（**已核验**）

- 目标：`phys/MYNN-EDMF/module_bl_mynnedmf.F90` 的 `GET_PBLH`（行 ~6047）——θv 阈值判据：`delt_thv = 1.25_kind_phys`（LAND）/ 0.75（WATER）。
- 修改锚点（唯一）：`   ! LAND` 下一行 `   delt_thv = 1.25_kind_phys`。
- 语义：PBLH = 首个满足 θv ≥ minθv(最低200m) + Δ 的高度；Δ↑ → PBLH↑（更深夹卷）。0.5/2.5 K 为敏感性双极。
- 编译实体确认：沙箱 `phys/module_bl_mynnedmf.o` 存在（对应 MYNN-EDMF/module_bl_mynnedmf.F90；misc/ 与 physics_mmm 副本未编译）。bl_pbl_physics=5 → `mynnedmf_driver`。
- 物理映射：ch14 的"PBLH 三型判据（Ri / θv 阈值 / TKE 阈值）"→ ch20 实改其中之一。

## 三、L3 设计（论文2 对接，**图纸待细化**）

- 目标链（已定位）：`BEP_BEM`（module_sf_bep_bem.F 行 95；行 712 `iurb=UTYPE_URB2D(ix,iy)`；行 ~929 传 `albr_u(iurb)` 给 BEP1D）→ `BEP1D`（行 1167）→ `call BEM`（行 1712，scalar `albw,albwin,albr,emr,...`）。
- 最小可行改造：在 BEP1D 调用点把 `albr_u(iurb)` 换成"2D 覆盖值"（开关开时取 `albrof_2d(ix,iy)`）；Registry 增 `ALBROF_2D`（auxinput 流）+ rconfig 开关；namelist 传参链沿用官方 `slucm_distributed_drag` 模式（config_flags → surface_driver → noahdrv → BEP_BEM）。
- sanity：城市格点（W238 附近）屋顶温度 `tr_urb2d`/`trof` 日循环对照。
- 待办：确定 auxinput 流号与 interval 语义（查 README.namelist）；确认 albr 是否唯一消费点（BEP1D 内 modif_rad/long_rad 是否需要同改）。

## 四、集群资产与作业

- 沙箱树：`ch18_exp/WRF-ideal`（含 ch19 patch4；wrf.exe md5 = 941ba403…= 基线对照二进制，已复制为 ch19_exp/bin/wrf_class1.exe）
- 新实验根：`ch20_exp/`（bin/ stage/ SUMMARY_*.txt）
- 运行目录：L1a/L1b/L2a/L2b；wrfinput/wrfbdy 取 `ch19_exp/sf0`（=0 套装，MYNN 全套）；namelist = ch20_nml24h（24 h，见下）
- 作业：ch20_build_*.sh（构建 L1+L2×2）→ ch20_run_*.sh（4×24 h + ncks 抽取）
- 抽取：ncks（lz_case/bin，LD_LIBRARY_PATH=lz_case/lib）；2D 全时次 + 3D 单帧（Time,12）

## 五、namelist（ch20_nml24h，基于 ch19 nml5d_sf0）

- run_days=0 / run_hours=24；end_day=13,13 end_hour=00,00
- history_interval=60,60；frames_per_outfile=1000,1000；restart_interval=1440
- 物理不变：mp8/RRTMG4/sfclay5/Noah2/MYNN5/KF(d01)+关(d02)；sf_urban=0

## 六、进度记录

- [x] 侦察：沙箱状态、作业模板、namelist、锚点唯一性（全部实测）
- [x] **L1+L2 构建（作业 439915，COMPLETED 15:20）**：
  - L1：补丁 3 处（Registry/start_em/solve_em）→ touch Registry/Registry → `compile em_real -j 12` **695 s**（Registry 触发全树重编）；wrf.exe md5 **d8be381b825f86fd1143c4ed8b3e8ca0**
  - **ch04 §4.5.3 六点自检全部实测命中**：state_struct.inc:`real ,DIMENSION(:,:) ,POINTER :: t2_peak`（行 2794）；allocs_1.F:`in_use_for_config(id,'t2_peak')` + `ALLOCATE(grid%t2_peak(...))`；deallocs_9.F；**actual_new_args/nl_config/module_state_description 三件 md5 不变**（b1f2b385/0e97a914/9edf5f59）
  - L2：delt_thv→0.5 编译 **67 s**（md5 8d1d33da…，module_bl_mynnedmf.o cd8cd514…）；→2.5 编译 **57 s**（md5 a4313abf…，.o b60c70a2…）→ **纯物理一行改动 ≈ 1 分钟增量**（vs Registry 级 12 分钟）
  - 沙箱收尾：MYNN 已还原（diff 空）；树 = L1 状态
- [x] **L3 补丁脚本 v2（锚点修正）**：lsm_mosaic 与 lsm 调用同尾（带 `! fasdas` 注释区分）；已修正
- [x] **输入场注入**：`workspace/scripts/ch20_inject_albrof.py` —— d02 城市格点 104 个（东 44 个=0.8 处理组 / 西 60 个=0.2 域内对照）；d01 全 0；已推送 ch20_exp/input/
- [ ] 运行作业 439932（L1a/L1b/L2a/L2b 四跑 24 h + 抽取）——**首轮失败教训：脚本顶部全局 `export LD_LIBRARY_PATH=lz_case/lib` 含旧 libc → mkdir/ls/tar 全坏（"GLIBC_2.34 not found"）→ 已改为只给 ncks 单命令加 env**
- [ ] L3 构建作业 439933（并行跑）
- [ ] 本地诊断出图（ch20_diagnose.py）
- [ ] L3 双跑（L3off/L3on）+ 单点 sanity
- [ ] 成文 + 四件套 + 复核清单第 15 条

## 八、事故链记录（教材素材，全部实测）

| # | 现象 | 根因 | 处置 | 证据 |
|---|---|---|---|---|
| 1 | run 作业 1 秒退出，`chdir FAIL`，ls/tar/mkdir 报 `GLIBC_2.34 not found` | 脚本顶部 `export LD_LIBRARY_PATH=lz_case/lib`（为 ncks 准备）——该目录含**旧版 libc.so.6**，被全脚本继承 | 改为 `env LD_LIBRARY_PATH="$LZ" "$NC" ...` 仅 ncks 单命令生效 | SUMMARY_run.txt 首段 |
| 2 | L3 补丁 rc=1：`surface_driver lsm call tail: anchor count=2` | lsm_mosaic 调用结尾与 lsm 相同（差 `! fasdas` 注释） | 锚点升级为双行 | SUMMARY_buildL3.txt |
| 3 | **L1b/L2a/L2b 在 `alloc_space_field: domain 1` 后 SIGSEGV（22 s）；同节点基线二进制 1736 步无碍（rc=124 超时）** | **陈旧对象**：Registry 改动改变了域类型布局，但增量重编只覆盖了部分单元——**688/914 个 .o 早于重编时刻**（含 `main/wrf.o`、`module_wrf_top.o`＝Oct 4；`phys/*` 159 个），陈旧单元按旧偏移访问 `grid%` → 内存错乱 | `tcsh ./clean` + 全量重建（本次重建序列） | addr2line：崩溃 PC=0x658241 → `set_scalar_indices_from_config_`（frame/module_configure.F）；`find -newermt` 统计 688/914 |
| 4 | L3 构建链接失败：`undefined reference to 'bep_ndm_' / 'module_microphysics_driver_...'` | L3 补丁给 **BEP_BEM 加了"非可选"哑元**，而 `phys/noahmp/drivers/wrf/NoahmpUrbanDriverMainMod` 也调用 BEP_BEM → 该单元编译失败 → **phys 库不完整** → 链接缺符号（make -i 把错误标成 "(ignored)"，最终只报 "Problems building executables"） | 哑元改 `OPTIONAL` + 嵌套 `PRESENT(ALBROF_2D)` 守卫（同时避免对未传入实参求值） | compile_L3.log:1483 与 1680-1693 |

**教学点（拟入正文）**：
1. 加哑元前先 `grep` 全部调用点（本项目 BEP_BEM 有 2 个调用方：Noah 驱动 + **Noah-MP 驱动**）；不确定就 OPTIONAL + PRESENT。
2. **Registry 级改动（新增 state）＝域类型布局改动，必须确保全量重建**：增量构建在"时间戳不可靠的树"（如拷贝保留 mtime 的沙箱）上会漏编 → 运行期崩溃；遇到"启动期莫名的 SIGSEGV + 崩在状态索引类例程"→ 先 `./clean` 全量重建排除陈旧对象。
3. 链接错误的定位：`grep -n "error #\|undefined reference" compile.log` + 注意 make -i 的 "(ignored)" 会掩盖真错误。

## 九、干净重建序列（作业 439955）

`ch20_rebuild_inner.sh`：还原（patch4 基线）→ `tcsh ./clean`（.o 914→<10）→ 5 连建：
- `wrf_base_cl20.exe`（干净基线，代 ch19 的 941ba403 作 L1a 对照，消除"构建血统"差异）
- `wrf_t2peak.exe`（L1）
- `wrf_thv05/25.exe`（L2 两变体）
- `wrf_bem2d.exe`（L3，含 OPTIONAL 修正）
随后 `ch20_runall`（1 作业 6 跑：A 组 4×24 h + B 组 2×12 h + 抽取）。

## 七、风险与备选

- 若 L1a↔L1b 出现 >机器精度差异：如实记录（编译器重排的可能），改为"统计等价"表述。
- 若 L2 信号过小/过大：两个变体互为参照，如实报告。
- 若 MYNN 文件非编译实体（.o 不更新）：查 phys/Makefile 依赖，必要时用 `make -f Makefile` 定点重编。