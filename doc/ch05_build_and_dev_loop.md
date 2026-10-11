# 第 5 章 编译体系与增量重编译：从整树到单点的开发循环

> **本章定位**：第 II 部第三站。第 3 章给了你调用链与目录树，第 4 章给了你 Registry 的生成链；本章回答一个工程问题——**代码怎么变成可执行文件，以及改一行代码之后，你要等多久、怎么等得更聪明**。
> 学完本章，你将能够：说清 `configure`/`compile` 每一步在做什么（包括它悄悄删掉你 `main/` 下四个 exe 的那一步）；完整掌握源码中并存的第二套构建体系——cmake 路线；拿着本书整理的 `test/em` 理想算例全表按需选例；并用实测数据建立对"增量重编译成本"的直觉——**改一个叶节点约 1~2 分钟，改一次 Registry 约 11 分钟**——这是第 20 章"改造 WRF"的预算基础。
> **与配套手册的分工**：环境准备、依赖链编译、AVX-512 相关 stanza 修改、容器化提交等"从零到能编译"的内容，已由配套《WRF 编译手册（oneAPI 2026）》完整覆盖，本章**不重写**，只在需要处引用。本章只写手册没有的三件事：① cmake 路线；② `test/em` 全表；③ 增量重编译开发循环的实测与陷阱。
> 本章所有结论均以本地源码（`source\WRFv4.8.0\WRFV4.8.0\`）与集群实际构建树（`IceLake/wrf-4.8/build/WRF/`）实测核验。

---

## 5.0 本章地图

### 你将在本章学会

1. **两套构建体系的全景与分工**：传统 `configure` + `compile`（就地构建）与 `configure_new` + `compile_new` + cmake（树外构建）并存一树，各自的产物、目录与清理方式；
2. **`compile` 脚本逐步源码走读**：命令行分发（`em_real` 与 `em_*` 的 `$ZAP` 差异）、Registry 合成、先删 exe 再链接的全过程；
3. **编译依赖图的本质**：Fortran module 依赖如何决定"改一个文件要重编几个对象"，`main/depend.common` 的角色；
4. **Registry 触发链的第三个环节**（第 4 章续）：改 `Registry.EM_COMMON` 后为什么直接编译会"静默失效"，如何用一个 `touch` 解开——以及 dry-run 实测证据；
5. **cmake 路线的完整工作流**：`configure_new` 的交互设计与全部命令行选项、`wrf_config.cmake`/toolchain 机制、`CMakeLists.txt` 的选项全集（core/nesting/case/布尔开关）、`compile_new`、"安装目录"式产物布局、`cleanCMake.sh`；
6. **`test/em` 理想算例全表**：15 个目录、14 个可运行算例的场景、分辨率、域规模、时步与时长——理想实验的选例指南；
7. **增量重编译实测**：A 组（叶节点改动 81 s / 还原 45 s）与 B 组（Registry 全链 649 s × 2）的完整数据、md5 判据与生成的 `t2_peak` 证据。

### 源码锚点总表（本章全部实测核验）

| 主题 | 文件 | 关键符号/片段 |
|---|---|---|
| 传统配置入口 | `configure`（根目录） | 交互式 stanza 选择（配套手册详述） |
| 编译器段库 | `arch/configure.defaults` | `#ARCH` 分隔的 stanza 块；`DESCRIPTION`、`SFC`/`SCC`、`CONFIGURE_FC` 占位符 |
| 传统构建驱动 | `compile`（根目录，tcsh） | `set ZAP = ...`；`/bin/rm -f $ZAP`；`make $arglist A2DCASE=... WRF_SRC_ROOT_DIR=...`；Registry 合成段（`auto-generated from Registry/Registry.EM`） |
| 构建变量产物 | `configure.wrf`（构建树内生成） | `SFC`、`FC = $(DM_FC)`、`ARCHFLAGS`、`REGISTRY = Registry` |
| 顶层构建目标 | `Makefile`（根目录） | `em_real : wrf`（删 exe→ `cd main` 构建 → 建 test/em_real 链接） |
| Registry 触发规则 | `frame/Makefile` | `module_state_description.F : ../Registry/$(REGISTRY)` → 调 `tools/registry` |
| Registry 装配清单 | `Registry/Registry.EM`、`Registry/registry.em_shared_collection` | `include` 链：EM → dimspec + em_shared_collection → `Registry.EM_COMMON` 等 20 余文件 |
| 对象级依赖清单 | `main/depend.common` | 每个 `.o` 的先决对象列表 |
| cmake 配置入口 | `configure_new`（sh） | `-p/-x/-d/-i/--`；调 `arch/configure_reader.py` → `$buildDirectory/wrf_config.cmake`；`cmake .. -DCMAKE_INSTALL_PREFIX=... -DCMAKE_TOOLCHAIN_FILE=...` |
| cmake 构建入口 | `compile_new` | 默认构建目录 `_build`，安装到 `install/` |
| cmake 工程本体 | `CMakeLists.txt`（根目录） | `WRF_CORE_OPTIONS`/`WRF_NESTING_OPTIONS`/`WRF_CASE_OPTIONS`；全部 `USE_*`/`ENABLE_*` 开关；`MAX_DOMAINS_F=21`、`CONFIG_BUF_LEN=65536`、`MAX_HISTORY=25` |
| cmake 辅助脚本 | `cmake/*.cmake` | `confcheck.cmake`、`wrf_case_setup.cmake`、`gitinfo.cmake`、`target_source_properties.cmake` 等 |
| cmake 使用文档 | `doc/README.cmake_build` | 工作流、`*_ROOT` 变量清单、`cleanCMake.sh` 用法 |
| cmake 清理工具 | `cleanCMake.sh` | `-c/-b/-f/-a` + `-d/-i` |
| 理想算例 | `test/em_*/`（15 个目录） | 各算例 `namelist.input` 与 `README.*` |
| 本章实验日志 | 集群 `ch05_exp/` | `SUMMARY_E.txt`、`E_*_compile.log`、`E_*_objects.txt`、`md5_gen_orig.txt` |

### 读者前置

- 第 3 章（目录树与程序族）与第 4 章（Registry 生成链）——本章的 B 组实验直接续在它们上面；
- 能看懂 Makefile 的基本规则（target、prerequisite、mtime 判定）与 Fortran module（`.mod` 文件）的概念；
- 一套已经能成功编译 WRF 的环境（搭建过程见配套手册）。

---

## 5.1 两套构建体系全景

### 5.1.1 一个源码树，两套体系

打开 WRF 4.8.0 源码根目录，你会看到两组名字成对的入口脚本：

```text
WRFV4.8.0/
├── configure          ← 传统路线：交互选 stanza → 生成 configure.wrf
├── compile            ← 传统路线：tcsh 驱动 make，就地构建
├── configure_new      ← cmake 路线：交互选 stanza + 选项 → 生成 _build/wrf_config.cmake
├── compile_new        ← cmake 路线：驱动 cmake --build，树外构建到 _build，安装到 install/
├── cleanCMake.sh      ← cmake 路线的清理工具（传统路线的清理见 ./clean）
├── CMakeLists.txt     ← cmake 工程本体（传统路线没有等价物，配置分散在 arch/ 下）
├── arch/              ← 传统路线的配置段库（configure.defaults 等）
├── cmake/             ← cmake 路线的脚本库（confcheck/wrf_case_setup/template 等）
└── doc/README.cmake_build  ← cmake 路线的官方使用说明
```

两条路线**共享同一份源码与同一套 stanza 库**（cmake 路线的 stanza 仍然从 `arch/configure.defaults` 里读），但配置的"形态"完全不同：传统路线把一切塞进一个手写风格的 `configure.wrf`（make 变量表），cmake 路线把 stanza 翻译成 CMake 工具链文件 `wrf_config.cmake`。这也是为什么同一台机器上两条路线的编译选项能保持口径一致——它们的源头是同一份 `configure.defaults`。

### 5.1.2 对照表

| 维度 | 传统路线（configure + compile） | cmake 路线（configure_new + compile_new） |
|---|---|---|
| 配置产物 | `configure.wrf`（make 变量表，约 540 行） | `_build/wrf_config.cmake`（toolchain 文件） |
| 配置方式 | 交互选 stanza 编号 | 交互按**描述**选 stanza（编号会变，描述稳定）；只列出本机编译器可用的段；SM/DM 拆成 y/n 提问 |
| 构建位置 | **就地**：对象、模块文件散布在 `main/`、`phys/`、`dyn_em/` 等各目录 | **树外**：一切在 `_build*/` 下，源码目录保持干净 |
| 可执行文件 | `main/wrf.exe`、`real.exe`、`ndown.exe`、`tc.exe`（带 `.exe` 后缀） | `install/bin/wrf`、`real` 等（**无** `.exe` 后缀）；并复制到 `install/test/<case>/` |
| 运行目录 | `test/em_real/` 等通过符号链接指向 `main/` 的可执行文件 | `install/test/<case>/`（自带可执行与输入文件副本） |
| 多配置并存 | 不便（就地构建互相覆盖） | 支持：`-d` 指定多个 `_build*` 目录、`-i` 指定多个安装目录 |
| 清理 | `./clean`、`./clean -a` | `./cleanCMake.sh -c/-b/-f/-a`（含指定 `-d/-i` 的变体） |
| 现状 | 用户群最大、配套手册与教程默认 | 较新，正在补齐（如 ideal case 中 em_ideal 在 cmake 里被备注为"技术上可行但未暴露为选项"） |

> **本教材的实操默认**：用传统路线（与配套手册、与你的集群构建树一致）。cmake 路线在 §5.3 完整讲清、但本章不把它作为实验载体——它的实验价值（树外构建、多配置并存）在你将来"同时维护多个改造版本"时会回来找你。

### 5.1.3 WPS 侧的对应关系

WPS 4.7.0 同样出现 cmake 化痕迹：源码树里有 `cmake/` 目录，`geogrid/`、`metgrid/`、`ungrib/` 下各有一份 `CMakeLists.txt`（传统路线仍是 `./configure` + `./compile`）。第 6 章的实操沿用传统路线，理由同上。

---

## 5.2 传统路线剖析：compile 脚本到底做了什么

> 从"选 stanza"到"编译成功"的完整操作步骤、依赖库准备、stanza 修改（AVX-512 等），见配套《WRF 编译手册》。本节只做**源码级解剖**：那些手册不写、但你迟早要懂的机制。

### 5.2.1 配置阶段：stanza 与 configure.wrf

`arch/configure.defaults` 是一本"编译器配方库"，由 `#ARCH` 注释行分隔成若干 **stanza（段）**。每一段长这样（以 GNU 段为例）：

```text
#ARCH    Linux i486 i586 i686 armv7l aarch64, gfortran compiler with gcc #serial smpar dmpar dm+sm
DESCRIPTION     =       GNU ($SFC/$SCC)
DMPARALLEL      =       # 1
SFC             =       gfortran
SCC             =       gcc
DM_FC           =       mpif90 -f90=$(SFC)
FC              =       CONFIGURE_FC
RWORDSIZE       =       CONFIGURE_RWORDSIZE
ARCH_LOCAL      =       -DNONSTANDARD_SYSTEM_SUBR  CONFIGURE_D_CTSM
...
```

要点：

- `DESCRIPTION` 是段的"人类可读名"；传统 `configure` 交互时显示编号 + 描述（编号随环境变化，描述不变——cmake 路线索性只认描述）；
- `CONFIGURE_FC`、`CONFIGURE_D_CTSM` 这类**占位符**由 `configure` 在交互问答中替换（比如问你是否用 MPI，决定 `FC` 填 `mpif90` 还是 `gfortran`）；
- 选中之后，整段 + 你的问答结果被写进 `configure.wrf`——它是后续一切 make 的变量来源。

在集群构建树上实测，`configure.wrf` 中与本章直接相关的几行是：

```text
SFC             =       ifx
FC              =       $(DM_FC)          # 模型源码用 MPI 包装器（ifx 为底）
ARCHFLAGS       =       $(COREDEFS) -DIWORDSIZE=$(IWORDSIZE) -DDWORDSIZE=$(DWORDSIZE) ...
REGISTRY        =       Registry
```

最后一行是钥匙：`$(REGISTRY) = Registry`——第 4 章见到的 `frame/Makefile` 触发规则 `module_state_description.F : ../Registry/$(REGISTRY)`，展开后就是 `../Registry/Registry`。半个触发陷阱就藏在这里（§5.2.4）。

### 5.2.2 构建阶段：`compile` 脚本逐步解剖

`compile` 是一个 tcsh 脚本（这也是为什么缺少 tcsh 的环境需要先解决 tcsh）。按执行顺序看你在终端敲下 `./compile em_real` 之后发生的事：

**第一步：命令行分发与 `$ZAP` 设定。** 脚本逐个检查参数。当它认出 `em_real` 时：

```text
set ZAP = ( main/wrf.exe main/real.exe main/ndown.exe main/tc.exe )
```

当参数以 `em_` 开头（理想算例）时：

```text
set ZAP = ( main/wrf.exe main/ideal.exe )
```

`$ZAP` 是"本次构建要产出的可执行文件清单"。

**第二步：Registry 合成段。** 脚本检查 `Registry/Registry`（构建用的"总装注册表"）是否存在、以及是否落后于 `Registry/Registry.EM`——注意比较对象**只是 `Registry.EM`**：

```text
if ( ! -f Registry/Registry ) then
  set overwrite=1
else
  ...
  set em_time=`ls -1tr Registry | cat -n | grep -w 'Registry\.EM' | grep -v 'Registry.EM.' | awk '{print $1}'`
  set rg_time=`ls -1tr Registry | cat -n | grep -w 'Registry' | grep -v 'Registry.' | awk '{print $1}'`
  if ( $em_time > $rg_time ) set overwrite=1
endif
if ( $overwrite ) then
  echo '## WARNING: this file is autogenerated from Registry/Registry.EM. Changes may be lost' > Registry/Registry
  /bin/cat Registry/Registry.EM >> Registry/Registry
endif
```

也就是说：`Registry/Registry` 是**自动生成的副本**，内容 = 一行警告 + `Registry.EM` 全文。而 `Registry.EM` 本身是一张"装配清单"——开头只有两句 include 指令，指向真正的数据：

```text
#  Registry file, EM
#INCLUDES
include registry.dimspec
include registry.em_shared_collection
```

而 `registry.em_shared_collection` 的第一行就是：

```text
include Registry.EM_COMMON
```

于是第 4 章的 include 树完整长这样：**`Registry.EM_COMMON`（你写变量声明的地方）→ `registry.em_shared_collection` → `Registry.EM` → `Registry/Registry`（构建期的总装文件）**。

**第三步：删除旧可执行文件。** 在调用 make 之前：

```text
/bin/rm -f $ZAP >& /dev/null
make $arglist A2DCASE="$A2DCASE" WRF_SRC_ROOT_DIR="$WRF_SRC_ROOT_DIR"
```

**这一步请记住：`compile` 从不"增量保留"可执行文件——它先把 `main/` 下本次相关的 exe 全部删掉，再让 make 重建。** 后果是：如果后续链接失败，你手里就没有旧 exe 可用了（排查时请先把现有 exe 的 md5 存一份）。

**第四步：make 的执行。** `$arglist` 里带着 `em_real` 目标传给顶层 Makefile。以顶层 `Makefile` 的 `em_real` 目标为例：它依次（1）删除 `main/` 下四个 exe、（2）进入 `main/` 构建 `wrf.exe`、（3）在 `test/em_real/` 重建指向 `main/` 的符号链接。构建顺序由顶层 make 调度：先 `frame`（含 Registry 触发规则）、`external`、`share`，再 `phys`、`dyn_em`，最后 `main` 链接出 exe——第 3 章的程序族地图，就是这条顺序的产物。

### 5.2.3 依赖图的本质：为什么"改一个文件"≠"编一个文件"

传统路线是标准 make 增量构建：每个 `.o` 有"先决条件清单"，写在一个由构建系统维护的集中文件 `main/depend.common` 中。里面每条记录都是这个形状（节选）：

```text
module_ra_rrtmg_sw.o: \
	../share/module_model_constants.o \
	module_ra_clWRF_support.o \
	../frame/module_wrf_error.o \
	module_ra_rrtmg_aero_optical_util_cmaq.o \
	module_ra_rrtmg_lw.o
```

Fortran 的模块依赖会把"传播面"放大：一个 `.F` 文件被编译时，如果它含 `MODULE m`，编译产物除了 `.o` 还有 `m.mod`；**所有 `USE m` 的编译单元都必须在 `.mod` 之后编译**。因此"改了叶节点的几行代码"的真实代价 = 该文件自身 + 所有直接/间接引用其模块的编译单元。这在 §5.5 的实测里会给出精确数字（12 个对象）。

另一半代价在**链接**：任何一个参与 `wrf.exe` 的对象变了，`main/wrf.exe` 都要重新链接一次；而 WRF 的 `wrf.exe` 是 80 MB 量级的庞然大物——链接本身也要时间。

> **工程常识**：改造 WRF 时，改动位置越"根"（被越多模块引用），重编面越大。这解释了为什么老手总把"诊断小改动"优先放在叶子模块里（如某个物理方案文件），而不是 `frame/` 或 `share/` 里的公共模块。

### 5.2.4 Registry 触发链与"静默失效"陷阱（第 4 章续）

第 4 章讲了生成物怎么来，这里补上**触发条件**——完整链条有三个环节：

1. **`make` 规则**：`frame/Makefile` 里只有一条触发路径：

   ```text
   module_state_description.F : ../Registry/$(REGISTRY)
   	  ( cd .. ; tools/registry $(ARCHFLAGS) $(ENVCOMPDEFS) -DNEW_BDYS Registry/$(REGISTRY) ; true ) ;
   ```

   即：只有当 `Registry/Registry` **比** `frame/module_state_description.F` 新时，make 才会重新运行 `tools/registry`，进而重写 `inc/` 下几百个生成物。

2. **`compile` 的合成段**（§5.2.2 第二步）只在 `Registry.EM` 变化时刷新 `Registry/Registry`。

3. **你改的是 `Registry.EM_COMMON`**——它既不是 `Registry.EM`，也不是 `Registry/Registry`。

三个环节叠加的后果是一个隐蔽陷阱：**在 `Registry.EM_COMMON` 里加了变量，直接 `./compile`，编译能成功，但新变量根本不进生成物——静默丢失，无报错**。

我们在集群上用 dry-run 做了两次对照（`make -n -i -r em_real`，`-n` 只打印不执行）：

| 操作 | dry-run 中 `tools/registry` 命令数 |
|---|---|
| 仅向 `Registry.EM_COMMON` 追加一行 `state ... T2_PEAK ...` | **0**（陷阱） |
| 再 `touch Registry/Registry` 后 | **非 0**（命令出现在 dry-run 输出的第 57304 行，见 §5.5.4） |

**解法**（三选一，效果相同）：

- `touch Registry/Registry` 之后再编译（最小动作，本章实验采用）；
- 删除 `Registry/Registry` 让其重新生成；
- 重新跑 `./configure`（会连带重建 `Registry/Registry`）。

修正后的完整心智模型是：

> **改 `Registry.EM_COMMON` →（必须让 `Registry/Registry` 变新：touch/重配置）→ `./compile` 触发 `tools/registry` → 生成物重写 → 依赖它们的对象重编 → 重链 exe。**

这个陷阱与解法构成了 §5.5 B 组实验的核心。

---

## 5.3 cmake 路线（手册缺项之一）

### 5.3.1 设计哲学：树外构建、工具链文件、安装目录

cmake 路线与传统路线最本质的差别是**构建的位置与"安装"的概念**：

- **树外构建（out-of-source）**：配置与编译全部发生在源码树旁的 `_build/` 目录（可用 `-d` 改名，官方建议保留 `_build*` 前缀以表明"可安全整体删除"）。源码树里不再散落 `.o`/`.mod`——想做多个实验版本时，多开几个 `_build*` 即可互不干扰；
- **工具链文件**：stanza 信息被 `configure_new` 翻译成 `_build/wrf_config.cmake`，再作为 `-DCMAKE_TOOLCHAIN_FILE=` 传给 cmake——CMake 用它来认识编译器；
- **安装目录**：构建产物**安装**到 `install/`（默认 `$PWD/install`，可 `-i` 指定）：可执行文件进 `install/bin/`（无 `.exe` 后缀），并复制到 `install/test/<case>/`；连带输入文件也从源码 `test/<case>` 复制过来。运行在 `install/` 下进行，源码树始终只读般干净。

### 5.3.2 工作流（`doc/README.cmake_build` 要点）

```text
# 1) 配置（交互）
./configure_new
#    - 第一步选 stanza：只显示本机编译器可用的段；部分支持的段会带 "!!" 标记
#      （对比：传统 configure 显示全部段的编号列表）
#    - SM（OpenMP）/ DM（MPI）不再是 stanza 编号的一部分，改为独立的 y/n 提问
#    - target（case）、core、nesting 在配置阶段选定
#    - 其余开关走 "Configure additional options?" 问答
#    产物：_build/wrf_config.cmake

# 2) 编译
./compile_new -j 12
#    产物：install/bin/{wrf,real,...} 与 install/test/<case>/
#    注意：可执行文件没有 .exe 后缀

# 3) 运行（进入安装目录里的 test 目录）
cd install/test/em_real
./real     # 真实个例：先放好 met_em.*  → 产出 wrfinput_d01、wrfbdy_d01
./wrf      # 再运行
#    理想算例：./ideal 产生 wrfinput_d01（或类似初值），然后 ./wrf

# 4) 并行运行
mpirun -np <N> wrf
```

### 5.3.3 高级用法与 `*_ROOT` 变量

```text
./configure_new [options] [-- <CMake configuration options>]
  -p                  Preselect a stanza configuration with matching description
  -x                  Skip CMake options prompt（配合 -- 直传选项使用）
  -d directory        Use as alternate build directory
  -i directory        Use as alternate install directory
  -- <CMake options>  直接透传给 cmake 配置
  -h                  Print this message
```

官方给的完整示例——不交互、一句话完成配置：

```text
./configure_new -p GNU -x -- -DWRF_CORE=ARW -DWRF_NESTING=BASIC -DWRF_CASE=EM_REAL
```

依赖定位：cmake 路线**不要求你设环境变量**，它先用 PATH 里的 `nc-config` 找 netCDF；要指定具体库位置，用 `*_ROOT` 变量（大小写敏感，拼写与 `find_package` 调用逐字一致）：

| 类别 | 变量 |
|---|---|
| 总是用到 | `netCDF_ROOT`、`netCDF-Fortran_ROOT`、`ZLIB_ROOT` |
| 按配置用到 | `MPI_ROOT`、`OpenMP_ROOT`、`HDF5_ROOT`、`Jasper_ROOT`、`RPC_ROOT`、`BISON_ROOT`、`FLEX_ROOT` |

> 文档明确提示：WRF 要求的最低 CMake 版本是 **3.20**（根 `CMakeLists.txt` 首行 `cmake_minimum_required( VERSION 3.20 )`），即便你装了更新的 cmake，包的查找行为也按 3.20 的语义走。

### 5.3.4 选项系统：`CMakeLists.txt` 选项全集

cmake 路线把"选择"结构化成了三组枚举 + 两组布尔开关（均以集群源码实测列出）。

**三组枚举：**

| 选项 | 取值 | 默认 |
|---|---|---|
| `WRF_CORE` | `ARW`、`CONVERT`、`DA`、`DA_4D_VAR`、`PLUS`（注：CONVERT 只存在于 compile 脚本，不在 configure） | `ARW` |
| `WRF_NESTING` | `NONE`、`BASIC`、`MOVES`、`VORTEX` | `NONE` |
| `WRF_CASE` | `EM_REAL`（默认）、`EM_FIRE`、`EM_SCM_XY`、`EM_TROPICAL_CYCLONE`、`EM_HELDSUAREZ`、`EM_B_WAVE`、`EM_GRAV2D_X`、`EM_HILL2D_X`、`EM_LES`、`EM_QUARTER_SS`、`EM_SEABREEZE2D_X`、`EM_CONVRAD`、`EM_SQUALL2D_X`、`EM_SQUALL2D_Y`、`NONE` | `EM_REAL` |

**布尔开关（`USE_*`，全部默认 OFF）：** `USE_DOUBLE`、`USE_MPI`、`USE_OPENMP`、`USE_HDF5`、`USE_JASPER`、`USE_PIO`、`USE_IPO`、`USE_PNETCDF`。

**功能开关（`ENABLE_*`，全部默认 OFF）：** `ENABLE_PNETCDF_QUILT`、`ENABLE_CHEM`、`ENABLE_CMAQ`、`ENABLE_CFBM`、`ENABLE_CTSM`、`ENABLE_DFI_RADAR`、`ENABLE_HYDRO`、`ENABLE_KPP`、`ENABLE_MARS`、`ENABLE_TERRAIN`、`ENABLE_TITAN`、`ENABLE_VENUS`。（其中 `ENABLE_KPP` 若未同时开 `ENABLE_CHEM`，配置会警告并强制关闭。）

**行为开关：** `WRFIO_NCD_NO_LARGE_FILE_SUPPORT`、`FORCE_NETCDF_CLASSIC`、`BUILD_RRTMG_FAST`、`BUILD_RRTMK`、`BUILD_SBM_FAST`（默认 ON）、`SHOW_ALL_VARS_USED`、`CDXWRF`（CORDEX 诊断，取值 0 起）。

**固定项（源码中写死，不属于用户选择）：** `USE_ALLOCATABLES`、`wrfmodel`、`GRIB1`、`INTIO`、`KEEP_INT_AROUND`、`LIMIT_ARGS`、`ENABLE_CRTM`、`ENABLE_WAVELET`、`ENABLE_BUFR`（均 ON）；`MAX_DOMAINS_F = 21`、`CONFIG_BUF_LEN = 65536`、`MAX_HISTORY = 25`、`IWORDSIZE=4 / DWORDSIZE=8 / LWORDSIZE=4`（这些常量在第 4 章的生成物里都出现过——两套体系喂给 `tools/registry` 的编译宏必须一致）。

**配置期的自检**（`CMakeLists.txt` 中实测）：`WRF_CORE`/`WRF_NESTING`/`WRF_CASE` 取值不属于枚举时报 `FATAL_ERROR`；非 ARW 核强制 `USE_ALLOCATABLES=OFF`；`WRF_CASE` 在列表中位于 `EM_B_WAVE` 之前的算"专用理想案"，之后的是"通用理想算例"——这会影响 ideal 初值模块的组织方式。

### 5.3.5 清理与"原地复活"

`cleanCMake.sh` 的四档清理（对传统 `./clean` 的对应）：

| 命令 | 动作 | 用途 |
|---|---|---|
| `./cleanCMake.sh`（默认 `-c`） | 进 `_build` 执行 `make clean` | 只删对象，保留配置 |
| `-b` | 按 `_build/install_manifest.txt` 删安装文件 | "安装被弄乱了"时只重装不重编 |
| `-f` | 直接删 `_build` 与 `install/` | 配置坏了（cmake 缓存顽疾）时的彻底重置 |
| `-a` | 依次 `-c` → `-b` → `-f` | 有序全清 |

`-d/-i` 可与上述组合指定"操作哪一个构建/安装目录"；文档给了一个很好的例子：改乱了 `install/test/em_real/namelist.input` 又忘了原值——`./cleanCMake.sh -b && ./compile_new` 即可在不重编的前提下拿回一份原装安装。

### 5.3.6 两条路线的取舍

| 场景 | 推荐 |
|---|---|
| 第一次编译、跟手册/教程走 | 传统路线 |
| 只维护一个改动版 | 传统路线（改动即编，行为可预期） |
| 同时维护多个改造版本（ch20 场景） | cmake 路线（多 `_build*` 并存） |
| 想"重置一切"不污染源码 | cmake 路线 |
| 需要 `.exe` 后缀、脚本/集群习惯 | 传统路线 |

---

## 5.4 `test/em` 理想算例全表（手册缺项之二）

### 5.4.1 目录全貌

`test/` 下的 15 个目录（实测清单）：

| 类型 | 目录 |
|---|---|
| 真实个例 | `em_real` |
| 理想算例（含 `namelist.input`） | `em_b_wave`、`em_convrad`、`em_grav2d_x`、`em_heldsuarez`、`em_hill2d_x`、`em_les`、`em_quarter_ss`、`em_scm_xy`、`em_seabreeze2d_x`、`em_squall2d_x`、`em_squall2d_y`、`em_tropical_cyclone`、`em_fire`（另有 3 个变体 namelist） |
| 耦合实验包 | `em_esmf_exp`（内含 `WRF_CPL_SST.tar.gz` 与两个 namelist 模板 `namelist.input.jan00.ESMFSST/NETCDFSST`，README 说明是 ESMF 海温耦合实验，不是单机算例） |

其中 9 个算例带官方说明文档（README）：`em_convrad`、`em_grav2d_x`、`em_heldsuarez`、`em_les`、`em_quarter_ss`、`em_scm_xy`、`em_seabreeze2d_x`、`em_tropical_cyclone`、`em_fire`（另 `em_real` 有 FDDA 两份 README）。

### 5.4.2 算例参数全表

以下数据逐个从各算例 `namelist.input` 的 `&time_control`、`&domains`、`&physics`、`&dynamics`、`&bdy_control` 段实测提取（取 d01）：

| 算例 | 场景 | dx | e_we × e_sn | e_vert | 时步 | 时长 | 特征 |
|---|---|---|---|---|---|---|---|
| `em_b_wave` | 斜压波（中纬通道） | 100 km | 41 × 81 | 65 | 600 s | 5 天 | **x 周期 + y 对称**（通道模型；ch18 勘正："双向周期"有误）；物理全关（纯动力学） |
| `em_convrad` | 辐射—对流平衡 | 1 km | 101 × 101 | 35 | 5 s | 1 小时 | WSM6 + RRTMG×2 + YSU + slab 陆面（对流—辐射耦合） |
| `em_grav2d_x` | 二维密度流（x-z，Straka 1993 基准；冷泡触发） | 100 m | 513 × 3 | 65 | 1 s | 15 分钟 | 二维；物理全关；固定粘性 khdif=kvdif=75 m²/s（ch18 勘正："重力波"旧称有误） |
| `em_heldsuarez` | 保持—苏亚雷斯全球环流 | ≈625 km × 556 km | 65 × 37 | 41 | 1800 s | 1000 天 | 全球通道；长波走 Held-Suarez 型强迫（ra_lw=31），其余物理关 |
| `em_hill2d_x` | 二维山波 | 2 km | 202 × 3 | 41 | 20 s | 10 小时 | 物理全关；地形激励重力波 |
| `em_les` | 大涡模拟 | 100 m | 40 × 40 | 40 | 1 s | 1 小时 | 仅地面层方案开启；km_opt=2（3D 湍流闭合）+ 周期边界 |
| `em_quarter_ss` | 四分之一超级单体 | 2 km | 42 × 42 | 41 | 12 s | 1 小时 | Kessler 微物理；无辐射/边界层（经典对流个例） |
| `em_real` | 真实个例模板 | 15 km | 150 × 130 | 48 | 90 s | 36 小时 | 我们全程使用的正主（需 WPS 输入）；物理走物理套装预设（见下注） |
| `em_scm_xy` | 单柱模式 | 4 km | 3 × 3 | 60 | 60 s | 59 小时 | 3×3 极小域；Lin + RRTM/Dudhia + YSU + Noah（单柱强迫驱动） |
| `em_seabreeze2d_x` | 海风环流 | 2 km | 202 × 3 | 35 | 15 s | 12 小时 | 海陆热力差异；Thompson + RRTM/Dudhia + YSU + slab |
| `em_squall2d_x` | 飑线（x-z） | 250 m | 202 × 3 | 81 | 3 s | 1 小时 | Lin 微物理；其余物理关 |
| `em_squall2d_y` | 飑线（y-z） | 250 m | 3 × 202 | 81 | 3 s | 1 小时 | 同上，旋转 90°（检验 y 方向通量格式） |
| `em_tropical_cyclone` | 理想台风 | 15 km | 201 × 201 | 21 | 60 s | 6 天 | Kessler + YSU + slab；无辐射/积云；轴对称涡旋初始化 |
| `em_fire` | 火灾蔓延 | 50 m | 103 × 103 | 51 | **0.5 s** | 1 小时 | 火模型（`&fire` 段 + 网格细化 `sr_x/sr_y`） |

> **表注（`em_real` 与物理套装机制）**：`em_real` 模板里七个物理方案号都写着 `-1`，同时有一行 `physics_suite = 'CONUS'`——这是 WRF 4.x 的**物理套装**特性：`share/module_check_a_mundo.F` 的 `setup_physics_suite` 会在启动检查阶段把仍为 `-1` 的项替换为套装预设值（CONUS：cu=Tiedtke、mp=Thompson、ra=RRTMG×2、pbl/sfclay=MYJ、surface=Noah）；你若把某一项写了具体数字，就覆盖套装值。所以"模板能不能直接跑"的答案是：能，但跑的是 CONUS 预设而非你的意愿——正式使用前按第 7 章方式显式填写。

关于 `em_fire` 的时步一栏值得单独说明：它的 `namelist.input` 写的是

```text
time_step                           = 0,
time_step_fract_num                 = 1,
time_step_fract_den                 = 2,
```

WRF 的时步支持"整数 + 分数"表示：总时步 = `time_step + time_step_fract_num/time_step_fract_den` = 0 + 1/2 = **0.5 s**。其余算例都是整数时步。`em_fire` 还有 `namelist.input_hill_simple`、`namelist.input_rain`、`namelist.input_two_fires` 三个场景变体与配套的 `namelist.fire*`，是本章表中"一个算例多种玩法"的唯一特例。

### 5.4.3 启动一个理想算例的完整流程

以 `em_quarter_ss` 为例（与配套手册中 em_les 冒烟的流程同构）：

```text
# 1) 以上一步成功配置的构建树，编译该算例（ZAP 变为 wrf.exe + ideal.exe）
tcsh ./compile em_quarter_ss

# 2) 进入算例目录运行 ideal.exe 生成初始场
cd test/em_quarter_ss
./ideal.exe            # 产出 wrfinput_d01

# 3) 运行模式
mpirun -np <N> ./wrf.exe
```

要点：

- 理想算例**不需要 WPS、不需要外部数据**——初始场由 `ideal.exe` 按算例内置的解析式（如热泡、山体、飑线理论廓线）构造。这就是它们对"验证改造"的价值：**验证一个编译期改动是否破坏了模式，最快的路径是跑一个理想算例**（第 18 章会精选实操）；
- 部分算例依赖 `input_sounding`（探空廓线文件，如各类对流算例）——它也在算例目录里，可编辑；
- 切换算例需要重新 `./compile em_xx`（会重编 `ideal.exe` 与相关对象）——所以"跑多个理想算例"意味着多次编译，选例时心里有数。

### 5.4.4 选例指南

| 你要验证什么 | 用哪个算例 | 理由 |
|---|---|---|
| 编译刚改完，能不能跑起来（最快冒烟） | `em_les`（配套手册用法）或 `em_grav2d_x`（15 分钟、纯动力） | 域小、时步小、不需要输入数据 |
| 改动物理方案（辐射/微物理） | `em_convrad`（辐射）、`em_quarter_ss`（深对流） | 有解析初值 + 完整物理路径 |
| 改动动力学/通量格式 | `em_b_wave`、`em_hill2d_x`、`em_squall2d_x/y` | 标准测试床，对比解析解 |
| 改动陆面/城市（第 III 部） | `em_les`、`em_seabreeze2d_x` | 有陆面过程开关的简化场景 |
| 改动火模型 | `em_fire` | 唯一入口 |

---

## 5.5 增量重编译实测（手册缺项之三，本章核心实验）

### 5.5.1 实验设计

目标：把"改代码 → 编译 → 验证"的循环成本量化成秒级数据，并验证 §5.2.4 的 Registry 陷阱。实验在集群构建树（`build/WRF`，em_real，容器内 oneAPI 2026 `ifx`，`-j 8`）上执行，分两组：

| 编号 | 操作 | 判据 |
|---|---|---|
| **A1** | 向叶节点 `phys/module_ra_rrtmg_lw.F` **追加一行注释**（无逻辑变化）→ 编译 | 耗时、重建对象数、`.o` 与 exe 的 md5 |
| **A2** | 还原该文件 → 再编译 | 同上（检验"还原"路径） |
| **B0** | 向 `Registry.EM_COMMON` 追加 `T2_PEAK` 声明（**不** touch）→ dry-run | dry-run 中的 `tools/registry` 命令数（陷阱判据） |
| **B1** | `touch Registry/Registry` → 全树编译 | 耗时、重建对象数、`t2_peak` 生成物证据、exe md5 |
| **B2** | 还原 `Registry.EM_COMMON` → `touch` → 再全树编译 | 同 B1（验证完全还原） |

基线口径：执行前四个 exe 的 md5 已备份（`ch05_exp/md5_exe_orig.txt`，原始 `wrf.exe` 为 `e81b501625f9587635de53dfc0470a0e`）；生成物的原始 md5 亦已备份（`md5_gen_orig.txt`）。

### 5.5.2 A 组结果：叶节点改动的真实代价

**A1（改注释）**：

```text
[15:01:48] =========== A1: leaf comment change ===========
[15:03:10] compile[A1] rc=0 elapsed=81s rebuilt_objects=12
# md5 校验：
phys/module_ra_rrtmg_lw.o: OK
main/wrf.exe: OK
main/real.exe: OK
main/ndown.exe: OK
main/tc.exe: OK
```

- **81 秒**完成"重编 + 重链四个 exe"全流程（含 12 个对象重编）；
- 重编的 12 个对象（实测清单）：

```text
phys/module_ra_rrtmg_lw.o          # 被改文件自身
phys/module_ra_rrtmg_sw.o
phys/module_radiation_driver.o
phys/module_physics_init.o
phys/module_mixactivate.o
phys/module_microphysics_driver.o
phys/module_cu_kfcup.o
phys/module_madwrf.o
phys/module_cumulus_driver.o
dyn_em/module_first_rk_step_part1.o
dyn_em/start_em.o
dyn_em/solve_em.o
```

- **一个反直觉的事实**：哪怕只加了一行注释（逻辑零变化），重编的对象**逐字节一致**——`module_ra_rrtmg_lw.o` 的 md5 与基线相同，四个 exe 的 md5 也全部相同。两层含义：① `ifx` 不会把注释或时间戳烙进目标文件（构建是"内容确定"的）；② 因此 **md5 就是"改动是否引入行为差异"的免费判据**——这是改造 WRF 时的第一条安全带。

- **传播面的启示**：改动面看着"只是辐射模块"，波及面却包含 `microphysics_driver`、`cumulus_driver`、`solve_em` 等 12 个对象——它们通过 Fortran module 引用链与顶层调用者关联（§5.2.3）。改动位置越"根"，重编面越大。

**A2（还原文件）**：

```text
[15:03:58] compile[A2] rc=0 elapsed=45s rebuilt_objects=4
# md5 校验：四个 exe 全部 OK
```

- **45 秒**，触发了 4 个对象的残余重编（`module_madwrf`、`module_cumulus_driver`、`module_first_rk_step_part1`、`solve_em`——都是 A1 重编集合的子集）。这类"残余重编"是 make 时间戳判定在大规模并行构建中的正常现象；
- 无论重编了几个对象，**四个 exe 的 md5 与基线完全一致**——两次编译之间，可执行行为零漂移。

### 5.5.3 B 组结果：Registry 全链的代价与陷阱

**B0（陷阱判定，dry-run 不执行任何编译）**：

```text
[15:04:58] B0: registry_cmds_in_dryrun=0
```

仅修改 `Registry.EM_COMMON` 时，整树 dry-run（`make -n -i -r em_real`）里**没有任何** `tools/registry` 命令——陷阱成立（§5.2.4 机制）。

**B1（touch + 全链重编）**：dry-run 中重新出现 registry 命令（位于 dry-run 输出第 57304 行），全文如下——这就是"一行 Registry 声明"引发的实际动作：

```text
( cd .. ; tools/registry -DEM_CORE= -DNMM_CORE= -DNMM_MAX_DIM=2600 -DDA_CORE= -DWRFPLUS= \
  -DIWORDSIZE=4 -DDWORDSIZE=8 -DRWORDSIZE=4 -DLWORDSIZE=4 -DNONSTANDARD_SYSTEM_FUNC \
  -DWRF_USE_CLM -DUSE_NETCDF4_FEATURES -DWRFIO_NCD_LARGE_FILE_SUPPORT -DDM_PARALLEL \
  -DNETCDF -DPNETCDF -DLANDREAD_STUB=1 -DUSE_ALLOCATABLES -Dwrfmodel -DGRIB1 -DINTIO \
  -DKEEP_INT_AROUND -DLIMIT_ARGS -DBUILD_RRTMG_FAST=0 -DBUILD_RRTMK=0 -DBUILD_SBM_FAST=1 \
  -DSHOW_ALL_VARS_USED=0 -DCONFIG_BUF_LEN=65536 -DMAX_DOMAINS_F=21 -DMAX_HISTORY=25 \
  -DNMM_NEST= -DNEW_BDYS Registry/Registry ; true )
```

编译结果：

```text
[15:16:48] compile[B1] rc=0 elapsed=649s rebuilt_objects=224
--- t2_peak evidence ---
inc/state_struct.inc: real ,DIMENSION(:,:) ,POINTER :: t2_peak          # 域类型里出现了字段
inc/allocs_14.F: IF(okay_to_alloc.AND.in_use_for_config(id,'t2_peak'))THEN   # 分配代码生成
inc/allocs_14.F: grid%tail_statevars%DataName = 'T2_PEAK'               # 运行期状态表登记
be8d09e4d23b333785621e5c4a309ced  main/wrf.exe                          # 新 exe（md5 已变）
```

- **649 秒（≈10.8 分钟）**、**224 个对象**重编、四个 exe 全部重链——这是"注册一个新变量"的完整代价；
- `t2_peak` 在生成物中的三处落地证据齐备（域字段、分配代码、状态表登记——第 4 章"一行声明，六处生成"的实证）。**注意**：B1 只增加了声明，还没有任何计算或赋值的 Fortran 代码——所以此时的 `T2_PEAK` 虽然被分配、被登记，值恒为未初始化。给它"生命"（赋值逻辑 + 输出验证）是第 20 章一级实战的内容。

**B2（完全还原）**：

```text
[15:27:39] compile[B2] rc=0 elapsed=649s rebuilt_objects=224
main/wrf.exe: OK      # 四个 exe md5 全部回到原始值
inc/state_struct.inc: OK
inc/allocs_1.F: OK
frame/module_state_description.F: OK
inc/i1_decl.inc: OK
```

- 还原 + 全链重编同样 **649 秒 / 224 个对象**，四个 exe 与四个抽查生成物的 md5 **全部**回到原始值——改造实验的"回归基线"操作流程由此闭环。

### 5.5.4 实测数字汇总与预算直觉

| 改动类型 | 重编对象 | 耗时（-j 8） | 相对成本 |
|---|---|---|---|
| 叶节点（改一行注释/局部代码） | 12 | **81 s** | 1× |
| 叶节点还原 | 4 | **45 s** | 0.6× |
| Registry 声明改动（全链） | **224** | **649 s** | 8× |

由此建立三条预算直觉（用于第 20 章与论文2 开发循环）：

1. **诊断类小改动的循环是"分钟级"**：改叶节点 → 1~2 分钟拿到新 exe（含链接时间）；一天做几十次迭代完全可行；
2. **碰 Registry 的改动是"十几分钟级"**：一旦引入新变量（无论是否为它写代码），每次迭代都要付 224 对象 + 10 分钟的代价。"变量已注册"后继续改 Fortran 代码，如果不动 Registry 本身、也不必重生成……**注意**：`touch Registry/Registry` 一旦执行就会全链重编；反之只要 Registry 没被动过，后续改的 Fortran 文件都只走增量路径；
3. **时间花在哪里**：链接四个 50~80 MB 的 exe 及并行调度占大头；`-j` 越大收益越接近饱和（节点内存与磁盘 I/O 是上限）。

### 5.5.5 开发循环自查清单

每次改完代码，按此清单走（本书后续所有改造实验都照此办理）：

1. **保存基线**：改动前 `md5sum main/*.exe > baseline.txt`（被改动的源文件也存一份 `cp -p` 备份）；
2. **改代码**：只动你要动的文件；
3. **判断是否碰了 Registry**：碰了 → 先 `touch Registry/Registry`（或按 §5.2.4），准备好 ~11 分钟；没碰 → 直接下一步；
4. **编译**：`tcsh ./compile em_real -j 8`（本教材口径）；
5. **核对对象与耗时**：从日志确认重编面（`find . -name '*.o' -newer <stamp>` 的用法见实验脚本）；
6. **verification**：至少跑一个**不需要外部数据**的理想算例冒烟（§5.4），再用 md5/诊断量确认行为差异方向——"零差异改动"（如注释、重构）应当出现 exe md5 相同或数值完全相同的结果；
7. **回归**：还原源文件 + `touch Registry/Registry`（若动过）→ 重编 → 校验 exe md5 回到基线（B2 流程）。

---

## 5.6 常见错误与速查（编译类）

| 症状 | 根因 | 处理 |
|---|---|---|
| 新增的 Registry 变量在生成物里找不到、编译却不报错 | §5.2.4 触发陷阱：`Registry/Registry` 没变新，`tools/registry` 根本没跑 | `touch Registry/Registry` 后重编（dry-run 验证：`make -n -i -r em_real \| grep tools/registry`） |
| 编译中途失败后 `main/*.exe` 不见了 | `compile` 的 `$ZAP` 机制：先删后建，失败即空窗 | 事先备份 exe；修复后重编即恢复（还原被污染对象的方法：touch 对应源文件再编） |
| 链接期报 `GLIBC_2.xx not found` 类错误 | 编译环境与运行/链接环境不一致（如工具链来自更新的容器、却在旧宿主上链接） | 见配套手册"容器"节：编译与链接必须在同一环境内完成 |
| `./compile` 报 `tcsh: not found` | `compile` 是 tcsh 脚本 | 安装/解包 tcsh（配套手册有离线方案） |
| cmake 路线编译后找不到 `wrf.exe` | cmake 产物**无 `.exe` 后缀**且安装在 `install/bin/` | 去 `install/bin/wrf`；运行在 `install/test/<case>/` |
| 同一棵树先传统后 cmake，行为混乱 | 两套体系的对象/生成物规则不同，混用会互相污染 | 一次一种；cmake 路线用独立 `_build*` 目录 |
| 改了一个"小文件"却重编很多对象 | Fortran module 依赖传播（§5.2.3） | 属正常现象；用 `main/depend.common` 预判传播面；把改动尽量放叶节点 |
| `./compile` 打印"You set the number of processors above 20"并回退为 `-j 2` | `compile` 脚本对 `-j` 只接受 2–20（源码实测：`second_word >= "2" && <= "20"`） | 用 `-j 8`/`-j 16` 这类**≤20** 的值；更细的并行控制交给 `make` 或 cmake 路线。想真正提速就别靠 `-j` 数字堆高——见下条 |
| 以为要等很久，结果 `./compile em_xx` 几十秒就完成 | 该树里已有上一次构建留下的全部 `.o`，`./compile em_xx` 只做"重链接 + 装目录"（IDEAL_CASE 相同的算例之间几乎无新编译） | 属正常；用 `ls -l main/*.exe` 的时间戳与 `find . -name '*.o' -newer <stamp> \| wc -l` 核实实际重编量（ch05 §5.3 的方法） |

> 注：以上速查只收编译体系相关的机制性条目；具体到本集群的环境配置错误（含 glibc/tcsh/容器相关）已在配套手册"速查"章覆盖，本书不重复。

---

## 5.7 延伸阅读

- `doc/README.cmake_build`（源码内）——cmake 路线官方说明全文；本章 §5.3 是其精编 + 选项表实测补充；
- `arch/configure.defaults`——读一遍你所用段（如 Intel/oneAPI 或 GNU 段）的每个变量，配合配套手册的 stanza 修改说明食用；
- `test/em_quarter_ss/README.quarter_ss` 与各算例 README——理想算例的官方使用说明；
- 配套《WRF 编译手册（oneAPI 2026）》——环境、依赖链、AVX-512 补丁与容器化提交；
- 第 18 章——从本章的算例全表中精选 2~3 个做完整实操（含结果诊断）；
- 第 20 章——改造 WRF 三级实战，全部建立在本章的开发循环与预算直觉之上；一级实战（`T2_PEAK`）的 Registry 部分已在本章 B 组实验中完成全链验证。

---

## 附：本章实验的可复现性档案

| 文件（集群 `IceLake/ch05_exp/`） | 内容 |
|---|---|
| `SUMMARY_E.txt` | A1/A2/B0/B1/B2 全过程时间戳、耗时、重建对象数、md5 校验结果 |
| `E_A1_compile.log` / `E_A2_compile.log` / `E_B1_compile.log` | 三次编译完整日志（含 `mpif90 -f90=ifx -o ... -O3 -xCORE-AVX512 ...` 命令行） |
| `E_A1_objects.txt` / `E_A2_objects.txt` | 重建对象清单 |
| `E_B0_dryrun.log` / `E_B1_dryrun.log` | 两次 `make -n` 全树 dry-run 输出 |
| `E_B1_registry_cmd.txt` | dry-run 中 `tools/registry` 命令行原文 |
| `md5_exe_orig.txt` / `md5_gen_orig.txt` | exe 与生成物的原始 md5 基线 |
| `E_rrtmg_lw.F.orig` / `E_EM_COMMON.orig` | 实验前源文件备份（还原用） |