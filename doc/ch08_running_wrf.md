# 第 8 章 运行 WRF：从起报到产出

> **本章定位**：第 II 部收官之战。WPS 备好了边界场（第 6 章）、real 造好了初值（第 7 章），现在把 `wrf.exe` 真正点燃：本章带你把兰州个例**完整跑完 5 天**，并回答“跑起来之后”的全部事故：日志怎么看、输出怎么管、断点怎么续、崩溃怎么查。
> 学完本章，你将能够：独立完成一次真实个例的**生产级运行**（含输出体量与机时估算）；用 `rsl.out/rsl.error` 定位任何运行期问题；把 restart（断点重启）从“知道有这回事”变成“写—读—续跑全闭环并理解其时钟机制”；并掌握一套“间歇性故障”的排查方法论——本章的两起真实事故（restart 误用、高核数段错误）就是你的疫苗。
> 本章所有结论均以本地源码（`source\WRFv4.8.0\WRFV4.8.0\`）与兰州个例实测（2026-10-10，5 天模拟一次成功，48.5 分钟）核验；事故记录原样归档于实验目录。

---

## 8.0 本章地图

### 你将在本章学会

1. **运行目录的“最后一公里”**：可执行文件、静态表、输入文件三件套齐备；
2. **读日志**：`rsl.out.0000` 启动清单逐段解读、主循环计时体系、`SUCCESS COMPLETE WRF` 的判读，以及失败长什么样（FATAL 三段式 / 段错误 / MPI_Abort）；
3. **管输出**：`history_interval` 与 `frames_per_outfile` 的真实机制（帧追加、滚动换文件）、输出体量与磁盘/机时估算；
4. **restart 全闭环**：`restart_interval` 的**分钟制**陷阱、rst 文件何时写/写什么/怎么读、断点续跑完整流程，以及“闹钟时刻表随文件旅行”的深水区机制；
5. **排错方法论**：从一次真实的高核数段错误事件里提炼“证据固定 → 变量隔离 → 短测代表性核查 → 自适应回退”四步法。

### 源码锚点总表（本章全部实测核验）

| 主题 | 文件 | 关键符号/片段 |
|---|---|---|
| 主循环与嵌套激活 | `frame/module_integrate.F`、`frame/module_nesting.F` | `integrate` 步循环；`nests_to_open` 的激活条件 |
| 计时体系 | `frame/module_timing.F` | `start_timing`/`end_timing`（“Timing for …” 格式串） |
| 重启闹钟 | `share/set_timekeeping.F` | `RESTART_ALARM` 创建；`restart_interval` 单位注释 |
| 重启读写 | `share/mediation_integrate.F` | `med_restart_out`（递归子域）、`med_last_solve_io` 铃响检查 |
| 闹钟元数据 | `share/output_wrf.F`、`share/input_wrf.F` | `WRF_ALARM_ISRINGING_NN` / `WRF_ALARM_SECS_TIL_NEXT_RING_NN` 属性 |
| namelist 项出处 | `Registry/registry.io_boilerplate` | `restart`、`restart_interval`（单位 MINUTES）、`_d/_h/_m/_s` 分量 |
| restart 变量清单 | `Registry/Registry.EM_COMMON` | rst 流的 `r` 标记（第 4 章查表法） |
| 实测产物 | `cases/lanzhou2025/wrf/` | wrfout/wrfrst、rsl.out/error、SUMMARY 归档 |

### 读者前置

- 第 3 章 `integrate` 调用链、第 4 章流与 Registry、第 6/7 章的输入文件——本章直接吃它们；
- 会看基本 Linux 命令与 slurm 作业提交（集群环境手册另有专册，本章不重复环境搭建）。

---

## 8.1 起跑线：运行目录的最后一公里

### 8.1.1 三件套：wrf.exe 需要什么才能跑

| 类别 | 内容 | 缺了会怎样 |
|---|---|---|
| 可执行文件 | `wrf.exe`（构建目录 `main/wrf.exe`） | 直接报“找不到命令” |
| 静态表与数据文件 | `run/` 下的查找表：`LANDUSE.TBL`、`VEGPARM.TBL`、`SOILPARM.TBL`、`GENPARM.TBL`、辐射数据（`RRTMG_LW_DATA`、`RRTMG_SW_DATA`）、Thompson 微物理查找表、`CAMtr_volume_mixing_ratio`（温室气体）等 | 启动或物理初始化阶段 `FATAL`（报“打不开/读不到”） |
| 输入数据 | `wrfinput_d0N`（初值）、`wrfbdy_d01`（侧边界） | 启动读入阶段 `FATAL` |
| 控制面板 | `namelist.input` | 无 → 用编译期默认值（几乎肯定不是你要的） |

我们的运行目录（`cases/lanzhou2025/wrf/`）用**符号链接**把 `wrf.exe` 与 `run/` 全部表文件挂进来，输入文件由 real.exe 直接产出在本目录，`met_em*` 链接自 WPS 目录（运行期并不需要 met_em，留在这里只是图个“全链路同屏”）。这是一种推荐但不唯一的组织法；本节只强调：**表文件必须在运行目录里找得到**——这是新手第一课。

### 8.1.2 启动命令与容器事实

```text
# 容器内（本项目集群的统一姿势：WPS/real/wrf 都要进同一容器）
mpirun -np 64 ./wrf.exe
```

> 环境细节（编译器、容器、模块加载）引用配套《WRF 编译手册》与本项目实录，本章不重复；你只需要记住运行侧的三个约定：①进容器；②`ulimit -s unlimited`；③长任务用 `sbatch` 提交、不写内存参数（见 §8.3.4 机时台账）。

### 8.1.3 slurm 实战：作业三件套与四个命令

生产运行一律走 slurm（登录节点只做“投递”）。本项目的标准姿势是**“外层脚本 + 内层载荷”**两件套：

```bash
# 外层：交给 slurm 的脚本（sbatch 提交），只负责"进容器 + 调内层"
#!/bin/bash
#SBATCH -J wrf_5day          # 作业名
#SBATCH -p cpu               # 分区
#SBATCH -N 1                 # 节点数
#SBATCH -n 1                 # 任务数
#SBATCH -c 64                # 每任务核数（= MPI 进程数）
#SBATCH -t 12:00:00          # 墙钟上限
#SBATCH -o /users/…/slurm-%j.out
exec singularity exec --bind /users:/users,/data:/data \
  /users/…/oneapi.sif /bin/bash /users/…/payload_inner.sh
```

```bash
# 内层：真正的计算载荷（在容器内执行）
set +u; export ME=…; source …/env-wrf-oneapi.sh; set -u
ulimit -s unlimited
cd /users/…/cases/lanzhou2025/wrf
mpirun -np 64 ./wrf.exe > wrf_prod_np64.log 2>&1
```

四条排班命令（本节每个案例都用过）：

| 命令 | 用途 | 实例 |
|---|---|---|
| `sbatch 脚本` | 提交作业，回显 `Submitted batch job 439419` | `sbatch ch08_prod_outer.sh` |
| `squeue -u $USER` | 看排队/运行状态 | 确认 PENDING→RUNNING |
| `scancel 作业号` | 撤销作业 | 参数写错时立即止损 |
| `sacct -j 作业号 --format=JobID,State,Elapsed` | 事后审计（成功/失败/耗时） | 本章所有“rc/耗时”数据都出自它 |

> 三条纪律（方案 v2 与项目约定）：**不写 `mem` 参数**（让调度器按核数分配）；**小任务 ≤8 核、大任务整节点**；**长任务必须 `sbatch`**。本章最短的 10 分钟短测也从 8 核起步——把“资源礼貌”变成肌肉记忆。

---

## 8.2 启动清单：把 `rsl.out.0000` 读成“体检报告”

wrf.exe 的 stdout（`wrf.log`）只有零星几行“starting wrf task N of M”——**真正的日志在 `rsl.out.NNNN` / `rsl.error.NNNN`**（NNNN=0000…0063，每 MPI 秩一份；判读主看 0000 号）。两条流内容几乎一致，排障时优先 `rsl.error.0000`（致命错误都会在此留痕）。

下面按“出场顺序”把 5 天生产运行（np64）的启动清单逐段拆解——这 40 行读懂了，你就拿到了运行期的“仪表盘”。

### 8.2.1 身份与并行布局

```text
taskid: 0 hostname: cpu15
Quilting with   1 groups of   0 I/O tasks.
 Ntasks in X            8 , ntasks in Y            8
  Domain # 1: dx =  9000.000 m
  Domain # 2: dx =  3000.000 m
--- WARNING: MYNN is set to mix scalars, turning off scalar_pblmix
```

- **`taskid/hostname`**：这一份日志属于哪个进程、跑在哪台节点；
- **`Quilting with 1 groups of 0 I/O tasks.`**：IO quilt（I/O 服务器）状态——`0 I/O tasks` 表示**本运行未启用 quilt**（`nio_tasks_per_group=0`，第 9 章详展）；这一行每次启动都会打印，是 quilting 的“开关灯”；
- **`Ntasks in X 8, ntasks in Y 8`**：域分解为 8×8 补丁（np=64 的二维分解）。**进程分配概念**：标准运行里所有域共用同一个 MPI 进程组，每个域都按同一套进程做分解（嵌套并不额外“给”子域分配进程），父子域的推进靠域间通信而非进程分工；若启用 quilt，则服务器进程从总进程数里“挖走”一部分（第 9 章）；
- **`Domain #`**：每个域的网格距——**注意：此行只说明配置里有几个域、网格距多少，不代表嵌套域一定会被激活**！本章事故二（§8.6）就栽在这一点上；
- **MYNN 警告**：`MYNN is set to mix scalars, turning off scalar_pblmix`——边界层方案（bl_pbl_physics=5，MYNN2.5）对“标量混合”选项的一个自动调整告知，**不是错误**。日志里这类“WARNING/告知”要与非 FATAL 区分开：判据只有一个——有没有 `FATAL CALLED` 或进程非零退出。

### 8.2.2 网格与内存

```text
 Parent domain
 ids,ide,jds,jde            1          90           1          90
 ims,ime,jms,jme           -4          19          -4          19
 ips,ipe,jps,jpe            1          12           1          12
 *************************************
DYNAMICS OPTION: Eulerian Mass Coordinate
   alloc_space_field: domain            1 ,               29975812  bytes allocated
```

三层索引（第 3 章的概念在此落地）：

- `ids/ide…`：**域**（整个 d01 是 1‥90）；
- `ips/ipe…`：**本进程补丁**（0 号进程负责 1‥12）；
- `ims/ime…`：**补丁+光晕**（-4‥19，halo=4 含在负数侧）——为什么是 -4？因为 `spec_bdy_width=5` 的边界带与 halo/tile 的对齐共同决定（交界处的细节属于并行章，先记住“ims 出现负数=光晕/边界区”）；
- `alloc_space_field: domain 1, 29975812 bytes`：本域第一个大块的动态分配量（约 28.6 MB）——**内存视角的第一笔账**。留意：同一域换分解（np64→np8）这个数会变（补丁越大、离散对象越多），§8.6 的实验里 800 万 → 8600 万字节的对比即在眼前。

### 8.2.3 输入读取与时间系统

```text
  med_initialdata_input: calling input_input
   Input data is acceptable to use: wrfinput_d01
 CURRENT DATE          = 2025-07-12_00:00:00
 SIMULATION START DATE = 2025-07-12_00:00:00
Timing for processing wrfinput file (stream 0) for domain        1:    0.49488 elapsed seconds
 D01: Time step                              =    54.00000      (s)
 D01: Grid Distance                          =    9.000000      (km)
 D01: Grid Distance Ratio dt/dx              =    6.000000      (s/km)
 D01: Ratio Including Maximum Map Factor     =    6.028852      (s/km)
 D01: NML defined reasonable_time_step_ratio =    6.000000
```

- `med_initialdata_input → input_input`：中介层读取初值，做**域维核对**；“Input data is acceptable to use”=核对通过；
- `CURRENT DATE` vs `SIMULATION START DATE`：新起报时二者相同；**续跑时前者是断点时刻、后者是最初起报时刻**（形成完整的时间账本）；
- 时间步自检：WRF 用 `dt/dx`（6 s/km）自查时间步是否合理——你写 dt=54 s 与 dx=9 km 恰好 6.0，与内置经验值一致（注意最大地图因子修正后 6.03）；
- **读初值 0.49 s、读 d02 初值 0.84 s**（后者出现在嵌套初始化段）——这是启动成本的一部分。

### 8.2.4 物理初始化：读表大会

```text
INPUT LandUse = "MODIFIED_IGBP_MODIS_NOAH"
 LANDUSE TYPE = "MODIFIED_IGBP_MODIS_NOAH" FOUND  61  CATEGORIES  2  SEASONS ...
INITIALIZE THREE Noah LSM RELATED TABLES
Skipping over LUTYPE = USGS
 LANDUSE TYPE = MODIFIED_IGBP_MODIS_NOAH FOUND  20  CATEGORIES
 INPUT SOIL TEXTURE CLASSIFICATION = STAS
ThompMP: read qr_acr_qg_V4.dat     instead of computing
ThompMP: read qr_acr_qsV2.dat instead of computing
ThompMP: read freezeH2O.dat instead of computing
```

Noah 陆面读入土地分类/土壤参数表；Thompson 微物理干脆读**预计算的查找表**（三种文件）替代现场求解——“读表成功”这几行就是 §8.1 三件套的验收章。温室气体块（`CAMtr_volume_mixing_ratio`，输出“Normal ending …”）同理。

### 8.2.5 嵌套域初始化

```text
 Nesting domain
 ids,ide,jds,jde            1         112           1         112
 ...
 INTERMEDIATE domain
 ids,ide,jds,jde           25          67          25          67
 ...
d01 2025-07-12_00:00:00 *** Initializing nest domain # 2 from an input file. ***
d01 2025-07-12_00:00:00  Input data is acceptable to use: wrfinput_d02
```

`Nesting domain`=子域网格；`INTERMEDIATE domain`=父子域的**重叠过渡区**（父网格索引 25‥67）；随后从 `wrfinput_d02` 初始化子域（0.84 s）。**这一整段只在嵌套域被激活时才出现**——圈起来，事故二要用（§8.6）。

### 8.2.6 边界处理与瓦片策略

```text
d01 2025-07-12_00:00:00  Input data is acceptable to use: wrfbdy_d01
Timing for processing lateral boundary for domain        1:    0.55478 elapsed seconds
 Tile Strategy is not specified. Assuming 1D-Y
WRF TILE   1 IS      1 IE     12 JS      1 JE     12
WRF NUMBER OF TILES =   1
```

侧边界读入（本个例全程共 20 次，对应 `wrfbdy` 的 `Time=20` 个 6 h 区段）；`Tile Strategy` 是共享内存并行（OpenMP）的瓦片划分——我们纯 MPI 运行，一行瓦片、无实际影响，但作为“日志解释器”你要认识它。

---

## 8.3 主循环与计时体系：每一步都留下账本

### 8.3.1 计时行从哪来

所有 `Timing for …: … elapsed seconds` 都出自 `frame/module_timing.F` 的 `end_timing`——本质是 `start_timing`/`end_timing` 一对括号加高精度计时器（`hires_timer`），格式串在 `end_timing` 内定义。因此日志里的三种典型行：

| 行样式 | 计量对象 | 我们的实测（np64，5 天） |
|---|---|---|
| `Timing for main: time <时刻> on domain d: …` | 该域**单步积分**耗时 | d01 8000 步，均值 0.361 s；d02 24000 步，均值 0.0838 s |
| `Timing for Writing <文件> for domain d: …` | 该域一次**写盘**耗时 | d01 41 次（≈0.73–0.80 s）；d02 121 次（≈1.05–1.2 s） |
| `Timing for processing lateral boundary…` | 边界读入处理 | 20 次（每 6 h 一次） |

把 d01 的 8000 步加起来：8000×0.361 s ≈ 2888 s ≈ 48 min——**与墙钟 48.5 min 吻合**（缺口是初始化与收尾）。这就是“用计时行审计墙钟”的基本功。

### 8.3.2 读时序的三条经验

1. **首步是“冷启动”**：d01 第一步 7.13 s（是稳态的 20 倍）、d02 第一步 2.56 s——物理方案首次调用、各类缓存首次触达所致。**估算耗时请从第 10 步以后取均值**，别被第一步吓到（也别拿它做外推）。
2. **写盘会让某几步变慢**：把 `Timing for main` 与该时刻的 `Timing for Writing` 对照读，能看到“输出步”比邻步多 0.7–1.2 s。
3. **滚动换文件更贵**：d02 输出文件每装 25 帧就开新文件（`frames_per_outfile=25`），换文件那几次写盘 ≈2.5 s（是常规的 2 倍）——文件名滚动点（07-13_01、07-14_02、…）与写盘尖峰一一对应，§8.4 展开。

### 8.3.3 收尾与成败判据

```text
Timing for main: time 2025-07-17_00:00:00 on domain   1:    1.50278 elapsed seconds
Timing for Writing wrfout_d01_2025-07-17_00:00:00 for domain        1:    0.74503 elapsed seconds
d01 2025-07-17_00:00:00 wrf: SUCCESS COMPLETE WRF
```

- **成功判据**：每个域都打印 `wrf: SUCCESS COMPLETE WRF` 且进程退出码为 0。注意最后一步（1.5 s）含收尾开销；
- **失败判据**（三种典型脸谱，都会在 `rsl.error.0000` 昭示）：

| 脸谱 | 形态 | 例子（本章归档） |
|---|---|---|
| FATAL 三段式 | `-------------- FATAL CALLED ---------------` + 来源行 + 一句话原因 | `program wrf: error opening wrfrst_… for reading`（§8.5.2） |
| 段错误 | 进程码 255，日志可能带调用栈（addr2line 可符号化） | 高核数下 `radiation_driver` 段错误（§8.6） |
| MPI_Abort | `Abort(1) on node 0 … MPI_Abort(MPI_COMM_WORLD, 1)` | FATAL 后的并行收尸动作，非独立病因 |

### 8.3.4 机时台账：把模拟变成账单

- 本次 5 天模拟：墙钟 48.5 min × 64 核 ≈ **52 核时**（核时=核数×墙钟，集群计费口径以此为准）；
- 粗估公式（新个例先估再投）：**核时 ≈ 步数 × 单步均耗 × 核数**；步数 = 模拟时长 / dt（本例 120 h / 54 s = 8000 步，d02 ×3）。单步均耗必须用“同规模、同域数、同核数”的短测测得——本章事故二正是在教你这句话的份量。
- 并行效率提示：单域 10 分钟短测里 d01 单步从 np1 的 0.83 s 降到 np64 的 0.04–0.09 s；但**双域生产的 d01 步均耗是 0.361 s**——因为生产步里含着嵌套推进与周期性输出等全部成本。**短测外推必须加“实况修正”**，否则机时估算会离谱。

---

## 8.4 输出管理：文件名、帧与磁盘

### 8.4.1 输出节奏由 alarm 控制（与第 4 章接轨）

`history_interval`（分钟，按域）在本构建里经注册表生成 **HISTORY_ALARM 定时器**（第 4 章的流系统）；每次报警写一帧。本个例：d01 每 180 min 一帧（5 天共 41 帧）、d02 每 60 min 一帧（121 帧），与日志计数逐一吻合（§8.3.1 表）。

### 8.4.2 `frames_per_outfile`：帧是“追加”进文件的（实测机制）

这是很多新手会误解的一处，我们用实测证据说清：

- **文件名取第一帧的时刻**，此后每帧**追加**进同一个文件，直到装满 `frames_per_outfile` 帧，下一个帧才另起新文件；
- 实测 1：d01 设 `frames_per_outfile=1000` → 全程只产出一个文件 `wrfout_d01_2025-07-12_00:00:00`，内含 **41 帧**（940 MB）；用任何 netCDF 工具打开都会看到 `Time` 维=41；
- 实测 2：d02 设 25 → 产出 5 个文件（817 MB / 843 MB / 847 MB / 867 MB / 753 MB），对应时刻 07-12_00、07-13_01、07-14_02、07-15_03、07-16_04——**看文件名就知道该文件的第一帧**；
- 实测 3（短测放大镜）：10 分钟短测里 d01 日志出现 2 次写盘、却只有一个文件——第二次写就是**追加**（该文件 `Time=2`）。

给论文/归档的建议：单文件别超 1–2 GB（有些工具与并行文件系统对大文件不友好），用 `frames_per_outfile` 把“大时间序列”切成“每文件一天”，同时也把写盘尖峰控制住。

### 8.4.3 体量与磁盘的账

| 产物 | 数量 | 单件 | 合计 |
|---|---|---|---|
| wrfout_d01（41 帧一文件） | 1 | 940 MB | 0.94 GB |
| wrfout_d02（25 帧/文件） | 5 | 0.75–0.87 GB | 4.13 GB |
| 输入（wrfinput×2 + wrfbdy） | 3 | 14/21/59 MB | ≈94 MB |
| 本例 5 天总占用（含日志） | — | — | **5.2 GB** |

推算口诀：**单帧字节 ≈ 变量数 × 网格点数 × 4 B（再乘压缩率）**。本例 d01 单帧净数据 ≈46.8 MB，压缩后存盘 ≈23 MB（第 9 章解密：本构建默认 netCDF4 + zlib 压缩）。跑长个例前先算 `帧数 × 单帧 × 域数`，再核对 quota——这是集群上“跑一半磁盘爆”的头号预防针。

### 8.4.4 打开你的第一帧：初步诊断三件套

跑完不看一眼数据，等于白跑。三件工具从轻到重，按需取用（**以下示例在本项目环境实测通过**）：

1. **`ncdump` / Python `netCDF4`（看骨架）**：`ncdump -h wrfout_d01_2025-07-12_00:00:00` 或本书第 9 章式解剖——先确认 `Time` 帧数、变量数、投影属性；
2. **Panoply（看场，NetCDF 图形化查看器）**：打开 wrfout → 直接画 `T2`/`RAINC` 的平面图，三分钟出“这模拟活没活”的第一印象；
3. **xarray + metpy（能算的诊断，可脚本化）**：

```python
import xarray as xr
import metpy.calc as mpcalc
from metpy.units import units

ds = xr.open_dataset("wrfout_d01_2025-07-12_00:00:00")   # xarray 直接读
print(dict(ds.sizes))          # {'Time':2, ..., 'bottom_top':49, ...}

t2c = ds["T2"][0] - 273.15                              # 2 m 气温（℃）
psfc = ds["PSFC"][0].values * units.Pa                  # 地面气压
q2 = ds["Q2"][0].values * units("kg/kg")                # 2 m 比湿
td = mpcalc.dewpoint_from_specific_humidity(psfc, q2)   # metpy 算露点

print("T2 max (C):", round(float(t2c.max()), 2))        # 本例 28.2
print("Td max (C):", round(float(td.max().to("degC").m), 2))   # 本例 22.1
```

> wrf-python（`wrf.getvar` 一行取 slp 等诊断量）是 WRF 社区的常用高层库，但对 xarray/netCDF4 的版本配套较敏感（本项目环境实测遇到兼容性问题）；教材的诊断主线因此放在“xarray+metpy 通用路线”，wrf-python 在第 19 章按需引入并给出环境栈建议。**初学时“能稳定跑通”比“函数短”更重要**。

---

## 8.5 restart 实战：写、读、续跑的全闭环

> 本节是第 7 章 §7.2.1 埋下的实战续集：那里我们只说了“`restart=.true.` 是读、不是开关”；这里把整条链路打通，并附三次真实事故/实验记录。

### 8.5.1 语义与数据流（源码级）

```mermaid
flowchart LR
    A["运行中：RESTART_ALARM 到点"] --> B["med_last_solve_io / med_after_solve_io 检查铃响"]
    B -->|"grid%id==1 才发起"| C["med_restart_out：写本域 rst 并递归写所有子域"]
    C --> D["wrfrst_d01_… / wrfrst_d02_…"]
    D --> E["续跑：restart=.true. + 起点时间对齐"]
    E --> F["input_wrf 读 rst：状态 + 闹钟时刻表"]
    F --> G["从断点继续积分"]
```

三条源码事实（`share/set_timekeeping.F`、`share/mediation_integrate.F`）：

1. **“写”由闹钟驱动**：`restart_interval` 系列非零即创建 `RESTART_ALARM`；铃响时**只有父域（id=1）发起** `med_restart_out`，后者写完本域后**递归**写全部子域（保证各域 rst 时间戳一致）；
2. **“读”由开关驱动**：`restart=.true.` 只决定启动时去读 `wrfrst_d0N_<起点时刻>`；
3. **单位是分钟**：`Registry/registry.io_boilerplate` 里 `restart_interval` 的单位列写明 **MINUTES**；另有 `restart_interval_d/_h/_m/_s` 四个分量（`_m` 缺省时回落到裸 `restart_interval`）——这是本节第一起事故的病根。

### 8.5.2 事故复盘 ①：把 `restart=.true.` 当“开关”（25 秒速死）

首次五天作业把 `restart` 误设为 `.true.`，25 秒后进程退出（rc=1），`rsl.error.0000` 全文：

```text
 RESTART run: opening wrfrst_d01_2025-07-12_00:00:00 for reading
-------------- FATAL CALLED ---------------
FATAL CALLED FROM FILE:  <stdin>  LINE:     242
program wrf: error opening   wrfrst_d01_2025-07-12_00:00:00 for reading
-------------------------------------------
```

读法：模式把自己声明为“续跑”，于是按“起点时刻”去找 `wrfrst_d01_2025-07-12_00:00:00`——**新起报哪来的 rst**？找不到 → FATAL。教训：`restart` 是“读取者开关”，**新起报永远 `.false.`**；要“定期落 rst”，写的是 `restart_interval`。

### 8.5.3 事故复盘 ②：单位陷阱（86400 ≠ 一天）

改回 `restart=.false.` 后，5 天生产**一次成功**——但翻产物清单时发现：**一个 `wrfrst` 文件都没有**！对照源码头注释（`set_timekeeping.F`：`! restart_interval … means minutes`）真相大白：我们写的 `restart_interval=86400` 被解释为 **86400 分钟 = 60 天**，闹钟在 5 天里根本没响。

两个对照实验（同一 10 分钟配置，各跑一次）：

| 试验 | 写法 | 语义 | 结果 |
|---|---|---|---|
| rst1 | `restart_interval=0` + `restart_interval_s=300` | 300 秒 | 产出 `wrfrst_d01_2025-07-12_00:05:24` 与 `_00:10:48` |
| rst1b | `restart_interval=5` | 5 分钟 | 与 rst1 **逐字节等价的产物与时刻** |

正确写法互译表：

| 想要 | 分钟制 | 分量制 |
|---|---|---|
| 每 5 分钟 | `restart_interval=5` | `restart_interval_m=5` 或 `_s=300` |
| 每天 00:00 附近 | `restart_interval=1440` | `restart_interval_d=1` |

另注意：**rst 的时间戳对齐步长**——闹钟定在 00:05:00，但模式在“首个时刻≥它的步”（00:05:24）落盘，文件名即该时刻。续跑时起点必须用**这个文件名里的时刻**对准。

### 8.5.4 rst 里面装了什么（解剖实测）

拉回一份 `wrfrst_d01_2025-07-12_00:05:24` 解剖（76 MB）：

| 观察项 | 实测 | 说明 |
|---|---|---|
| 变量数 | **660** | 远多于 wrfout 的 218：restart 要把“时间层”完整保存 |
| 时间层变量 | `U_1/U_2`、`THM_1/THM_2`、`PH_1/PH_2`… | 每变量带**两个时间层**（Leapfrog 历史量），wrfout 只输出“合成后”的场 |
| 状态族 | `T`、`QVAPOR`、`TSLB`（4 层土壤）… | 大气+陆面全状态 |
| 全局属性 `FLAG_RESTART=1` | 标记本文件是重启文件 | |
| 配置属性 | `DT`、`MP_PHYSICS=8`、`BL_PBL_PHYSICS=5`… | **方案与参数随文件走**，续跑做一致性核对 |
| 闹钟属性 | `MAX_WRF_ALARMS=55` + 每个闹钟的 `WRF_ALARM_ISRINGING_NN` / `WRF_ALARM_SECS_TIL_NEXT_RING_NN` | 见 8.5.6 深水区 |

### 8.5.5 续跑闭环（实测成功）

流程（全部亲测）：

1. **确认 rst 与起点**：目录里有 `wrfrst_d01_2025-07-12_00:05:24`（含 d02）；
2. **namelist 三处对齐**：`restart=.true.`；`start_*` 设为**与 rst 时间戳完全一致**（含 `start_minute=05, start_second=24`，按域给两个值）；`end_*` 指向续跑终点；
3. **不要再触发 rst 写**（本次实验把 interval 归零，专心验证读取）；
4. 运行，观察日志：

```text
 RESTART run: opening wrfrst_d01_2025-07-12_00:05:24 for reading
Timing for processing restart file for domain        1:    1.74806 elapsed seconds
 RESTART: nest, opening wrfrst_d02_2025-07-12_00:05:24 for reading
Timing for processing restart file for domain        2:    2.18821 elapsed seconds
d01 2025-07-12_00:05:24 WRF restart, LBC starts at 2025-07-12_00:00:00 and restart starts at 2025-07-12_00:05:24
 LBC for restart: Found the correct bounding LBC time periods
…
d01 2025-07-12_00:16:12 wrf: SUCCESS COMPLETE WRF
```

要点：①子域 rst 被“`RESTART: nest`”字样单独读出（1.75 s/2.19 s）；②**LBC（侧边界）需要覆盖续跑窗口**——`wrfbdy` 从 00:00 起、续跑窗口 00:05:24–00:16:12 落在第一段 6 h 内，日志明说“找到了正确的边界时段”；③续跑到终点 SUCCESS。

**顺带踩坑（值得当镜子）**：第一次搭实验脚本时，我在“续跑之前”顺手清了一遍输出目录（习惯动作 `rm wrfout_* wrfrst_*`），把刚生成的 rst 一并删了——于是又收获一次 §8.5.2 同款 FATAL。教训：**续跑目录里，rst 是输入不是输出**，清理脚本要精确到文件型别。

### 8.5.6 深水区：闹钟时刻表随文件旅行

续跑实验还有一个意外发现：namelist 明明把 rst 写盘间隔归零，续跑运行**仍然在 00:10:48 又写了一份 rst**（两域各一，2.7 s/4.5 s）。追查到底：

- 解剖 rst 的全局属性时看到 `WRF_ALARM_ISRINGING_51 = 1`、`WRF_ALARM_SECS_TIL_NEXT_RING_51 = 276`——**51 号正是 RESTART_ALARM**：rst 文件不仅装大气状态，还把**全部 55 个闹钟的“是否在响 / 距下次响还有几秒”存成元数据**；
- 这些属性由 `share/output_wrf.F` 写入、`share/input_wrf.F` 读回（`set_timekeeping.F` 里也有“写入 restart 元数据”的相关注释）；未启用的闹钟以 `1700000000` 秒（≈54 年）表示“永不”——即调度系统里的“forever”；
- 于是续跑的逻辑一目了然：读回“RESTART_ALARM 距下次响还有 276 秒”→ 从 00:05:24 再走 276 s = 00:10:00 → 首个时刻≥它的步 00:10:48 落盘。**与实测完全吻合**。

这条冷知识在工程上很有用：**rst 恢复的不只是流场，还有“日程本”**——续跑后输出/重启节奏会无缝延续，不会因为改短了 interval 就乱套。

---

## 8.6 排错实战：np64 段错误与“短测代表性”事故

> 本节是全书第一个“重案组”式案例：一起未复现的段错误 + 一条被我们的短测方式掩盖的事实。它教的方法论比结论本身更值钱。

### 8.6.1 案发：高核数下的一次段错误

修好 restart 开关后，五天生产以 np=64（8×8 分解）重投，运行 33 秒后进程 rc=255（段错误）。日志显示它已读完初值、写完 t=0 的 wrfout、处理完边界，在**第一步积分**内崩掉；对 rsl.error 里的调用栈做符号化（addr2line），落点是：

```text
main → wrf_run → integrate → solve_interface → solve_em → first_rk_step_part1 → radiation_driver
```

### 8.6.2 隔离变量：三连短测

一次崩溃含两个可疑变量：**辐射方案**（RRTMG）与**并行分解**（np64）。设计三连短测逐个排除（每次 10 分钟、其余配置相同）：

| 试验 | 辐射 | np | 结果 |
|---|---|---|---|
| A | 旧方案 RRTM（ra_lw=1） | 64 | ✅ rc=0，33 s |
| B | RRTMG | 1 | ✅ rc=0，50 s |
| C | RRTMG | 16 | ✅ rc=0，27 s |

结论：RRTMG 本身无碍；段错误只在高核数段出现过一次（改对 restart 后的那次 np64 五连天作业），随后在短测与生产中都**没再复现**——但注意，此时我们还不知道这些短测有一个致命前提问题（下一节）。

### 8.6.3 转折：短测在测什么？（代表性核查）

生产（np64）后来**一次成功、跑满 5 天**，段错误没再出现（“间歇性”苗头）。收尾复查短测日志时发现惊人细节：**所有 10 分钟短测里，“domain 2”的行数为 0**——它们**根本没跑嵌套域**！追根到源码 `frame/module_nesting.F` 的 `nests_to_open`：

```text
嵌套域激活条件：nest_start ≤ 当前时刻 且 nest_stop > 当前时刻
其中 nest_start/nest_stop 逐域读取 namelist 的 start_*/end_* 数组
```

我们的短测 namelist 把 `end_minute` 写成了**单值** `10`（其他 end_* 都是 `x, x` 两值）。Fortran namelist 对数组赋单值只填第一个元素 → **d02 的 end_minute 保持默认 0** → d02 的“终止时刻”=起报时刻 00:00:00 → `nest_stop > 当前时刻` 永远为假 → **d02 永不激活**。而启动清单里“Domain # 2: dx = 3000”照常打印（§8.2.1 的警告），极具迷惑性。

修复 = 给两个域都写全：`end_minute = 10, 10`。修复后复测（真·两域短测，np64）：

| 试验 | 配置 | 结果 |
|---|---|---|
| 真两域@np64 | end_minute 双值 | ✅ rc=0，62 s；d02 跑满 36 步；产出 d01/d02 的 wrfout 与 rst |
| 真两域@np8 | 同上 | ✅ rc=0，61 s（对照组） |

### 8.6.4 结案与教训

- **事实层面**：那次段错误在随后的 5 天生产、真两域短测（np64/np8）中**均未复现**——按“间歇性故障”归档（可能是特定内存布局下的偶发越界；本个例以自适应回退策略兜底：短测不过就改用 np16）。它已经被**完整留证**（rc、栈、日志、作业号），未来如再发可对比。
- **方法论层面**（本章真正要你带走的）：

| 教训 | 具体动作 |
|---|---|
| 证据先于结论 | 崩溃当场保存 `rsl.error`、作业号、调用栈；表述区分“事实 / 推断 / 未知” |
| 一次只动一个变量 | 三连短测矩阵（辐射×核数）是标准姿势 |
| **短测代表性核查** | 短测后核对日志：域行数、步数、输出文件数——**你以为在测两域，可能只跑了一域** |
| 对外推保持怀疑 | 单域步时 ÷ 双域生产步时 ≈ 1/3（0.14 s vs 0.36 s）——规模外推要验证 |
| 预备回退方案 | 生产脚本写成“短测通过则 np64，否则 np16”的自适应结构，无人值守也不慌 |

---

## 8.7 运行期速查表（症状 → 定位 → 处理）

| 症状 | 大概率根因 | 第一步动作 |
|---|---|---|
| FATAL `error opening wrfinput_*` | 输入缺/域号或时刻不匹配 | 核对文件名与 `start_*`；确认 real 产物在本目录 |
| FATAL `error opening wrfrst_*` + `RESTART run` 字样 | `restart=.true.` 缺 rst / rst 时刻与起点不符 | 新起报改 `.false.`；续跑则用 rst 文件名时刻对齐 `start_*` |
| FATAL 报某个 TBL/DATA 打不开 | 表文件没链接进运行目录 | 补齐 §8.1 三件套 |
| 启动后秒退、无输出 | 未进容器 / glibc / 动态库 | 按环境手册排查；先看 `rsl.error.0000` 首屏 |
| 跑完没有 wrfout | `history_interval`/时刻设置错；或短测长度 < 第一个输出间隔 | 查日志 `Timing for Writing` 有无；核对 end 时刻 |
| **没有 wrfrst** | `restart_interval` 单位是分钟（写 86400=60 天） | 按 §8.5.3 换算；或看 rst 属性里的闹钟秒数 |
| **某个域完全没动**（日志无该域步数） | 嵌套激活条件未满足（end_minute/end_* 单值陷阱） | `end_*` 按域写全（§8.6.3）；grep `domain   2` 计数自检 |
| 跑到一半进程消失、rc=255 | 段错误（内存/并行偶发） | 存 rsl、查栈；重投+回退核数；比对是否可复现 |
| 磁盘爆 | 输出体量估算失误 | §8.4.3 口诀预估；`frames_per_outfile` 切小；清理旧帧 |
| `mpirun` 报进程数不符 | quilt 任务数计入（第 9 章）/ `-np` 与分解不匹配 | 读日志 `Ntasks in X…` 与 quilt 行 |

---

## 8.8 延伸阅读

- `run/README.namelist`——`restart_interval_d/_h/_m/_s`、`write_hist_at_0h_rst`（续跑时刻是否补写历史）等项的官方释义；
- `share/mediation_integrate.F`——`med_restart_out`（含递归子域）、`med_last_solve_io`（铃响检查）与 `med_hist_out`；
- `frame/module_nesting.F`——`nests_to_open` 全文只有 70 行，值得逐行读：**你未来所有“域没动”的怪事都会回到这里**；
- 第 9 章——`io_form`、压缩与 quilt：本章 `wrfout` 的“940 MB 从哪来、又为何被压缩”将在那里结账；
- 附录实验记录——本章所有事故的原始日志与作业台账。

## 本章小结

1. **运行 = 三件套 + 一个控制面板**；`rsl.out/error.0000` 是仪表盘，启动清单逐段有含义，成功判据是 `SUCCESS COMPLETE WRF` 且 rc=0；
2. **计时体系**（`module_timing.F`）让你能审计每一步：冷启动效应、写盘开销、滚动换文件尖峰，都能量化；机时=核数×墙钟，估算必须用“同配置”短测；
3. **输出管理**的两把抓手：`history_interval`（多久一帧）与 `frames_per_outfile`（每文件几帧，帧是追加的）；体量先算后跑；
4. **restart 闭环**：写由 `restart_interval`（**分钟！**）闹钟驱动、父域递归写全子域；读由 `restart=.true.` 触发、起点时刻与 rst 文件名严格对齐、边界文件需覆盖续跑窗口；rst 连“闹钟时刻表”都随身携带；
5. **排错四步法**：留证据 → 单变量隔离短测 → **核查短测代表性**（域/步数/文件数） → 预备回退；本案例中的 np64 段错误按“间歇性故障”归档，原样留证备查。

---

## 8.9 补充专栏【科研改造案例库】：运行层三案

### 案例一　DFI（数字滤波初始化）：驱动层预留的“第四种跑法”

- **课题**：初始化高侧噪声抑制（对高分辨率、陡地形个例尤其重要——本书兰州个例的 9/3 km 双域就属于此类敏感配置）；
- **源码证据**（本地 `main/module_wrf_top.F`，ch03 §3.8 之树）：`wrf_dfi_write_initialized_state` / `wrf_dfi_startfwd_init` / `wrf_dfi_startbck_init` / `wrf_dfi_bck_init` / `wrf_dfi_fwd_init` 五个接口与 `frame/module_integrate.F` 的 `jcdfi_*`（数字滤波强阻尼）接口——**驱动层为 DFI 预留了完整的平行节拍**，namelist 侧由 `&dfi_control` 驱动；
- **收录方式**：情况③（思路级）——DFI 涉及 filter 前后向积分编排，超出本书范围；
- **教学点**：读 `module_wrf_top.F` 时别把 `wrf_run` 当唯一入口——**“模式怎么跑”是由 namelist 决定的一族路径**；这也是 ch03“三段式驱动”的深意。

### 案例二　4.8.0 的两个“critical bug fix”：restart 与 auxinput

- **课题**：官方在 4.8.0 修复的两个软件级缺陷（release notes Software 节）：
  ① *model hangs during first restart write*——内核未初始化值导致的未定义行为；
  ② *sudden model crash when reading auxinput data*——释放 data handle 未清空；
- **与本书的关系**：② 正是 ch20 论文2 参数场路线（auxinput 通道）的“前车之鉴”——若读者把参数场搬到 auxinput 流上，**先确认基线 ≥4.8.0**；① 解释了一些“挂在重启”的历史悬案；
- **教学点**：运行期“灵异现象”分三类：物理（stack/段错误）、软件（bug，查 known problems 页）、环境（LD_LIBRARY_PATH、容器，ch20 事故①⑤⑦）——先分类再动手。

### 案例三　本书双实录：栈上限与“运行中改脚本”

- **课题**：本书 ch19 的两条教训（此处提炼为运行层通则）：
  ① **`ulimit -s` 无限**：计算节点默认栈 8 MB → `solve_em` 栈溢出 SIGSEGV（对照实测：默认栈 27 s 崩、unlimited 后 301 步正常）；
  ② **作业运行中禁改脚本**：`sed -i` 替换正在执行的 sbatch 脚本 → NFS `Stale file handle` → 五天积分砍在第 4.5 天；
- **收录方式**：情况①（本书实录——**运维级案例，非代码改造，不适用“上游化”**；完整证据链在 ch19 §19.3/§19.5）；
- **教学点**：slurm 作业务必在脚本头部 `ulimit -s unlimited`；任何“作业活着就别动它的工作目录”（WRF 运行中替换 namelist/脚本 = 自杀式运维）。