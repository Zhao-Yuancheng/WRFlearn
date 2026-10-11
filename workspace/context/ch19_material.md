# ch19 素材与实验底稿（兰州 2025-07 高温全流程 + 城市冠层双跑）

时间锚点：2026-10-11 凌晨（自主会话）
章节文件：doc\ch19_lanzhou_heatwave.md（待写；方案 §3.2 定 5 节交付）

## 一、个例定稿（方案 §6.2，已在 ch06–ch08 落地）
- 窗口：2025-07-12 00Z 起报（spin-up）→ 07-13~16 分析段（4 天）；`run_days=5`（至 07-17_00Z）
- 两域：d01 9 km ~90×90（西北区域）+ d02 3 km ~112×112（兰州河谷+周边）；Lambert，ref 36.06N/103.83E，truelat 35/45
- 垂直：50 层（eta_levels 显式给出 1.000000→0.000000，低层加密）；p_top_requested=5000；num_metgrid_levels=32
- 驱动：liuyl17 ERA5 月 GRIB 202507（Vtable.ECMWF，零下载）→ WPS 三步已跑通（geogrid 43s / ungrib 40s / metgrid 122s；42 个 met_em）
- 物理（CTRL，与论文2 同构）：Thompson(8) / RRTMG(4,4) / MYNN 面层(5) / Noah 陆面(2) / MYNN2.5 PBL(5) / d01 KF(1) + d02 关(0)；num_land_cat=21；hybrid_opt=2；damp_opt=3
- 时步：d01 54 s（parent_time_step_ratio=1:3）
- 实测（ch08 作业 439419）：5 天两域 rc=0 / 2913 s（48.5 min @64 核）≈ 52 核时；d01 8000 步 mean 0.361 s、d02 24000 步 mean 0.0838 s；输出 wrfout_d01 940 MB（41 帧）、d02 五文件 817–867 MB

## 二、集群资源（ch08 已建）
- 案例目录：`/users/zhyuancheng2025/IceLake/wrf-4.8/cases/lanzhou2025/{wps,wrf}`
  - `wps/`：geo_em.d01/d02.nc、GEOGRID.TBL、42 个 met_em.d0{1,2}.*、FILE:*（21 个时次的 ungrib 中间文件）、geogrid.log
  - `wrf/`：namelist.input、wrfinput_d01/d02、wrfbdy_d01、wrf.exe 符号链接、run/* 数据文件符号链接、URBPARM.TBL 等三张城市表
  - `wrf/wrfout_d01_2025-07-12_00:00:00`（940 MB，41 帧）+ `wrfout_d02_*`（5 个，817–867 MB）——**=0 的 5 天基线结果仍在，可作 ch19 CTRL 素材**
- 构建树：`build/WRF/main/{wrf,real,ndexp,tc}.exe`；`build/WRF/run/`（静态数据表全集）

## 三、城市冠层双跑的前置侦察（本轮新结论，**ch19 关键素材**）

### 3.1 数据可用性的硬事实
| 项 | 实测 | 含义 |
|---|---|---|
| `GEOGRID.TBL` 的 `FRC_URB2D` 条目 | 存在（priority 1: `urbfrac_nlcd2011/`；priority 2: `urbfrac_gaia2020_30s/`），`optional=yes` | 条目在，但数据不在 |
| `/opt/app/wrf/WPS_GEOG/` 是否有上述目录 | **都没有**（只有 `NUDAPT44_1km`、`nlcd2006_ll_30s` 等 72 个目录） | → geo_em 里**没有** `FRC_URB2D` 变量 |
| `geo_em.d02.nc` 变量 | 57 个；有 `URB_PARAM`（132 层）、`LANDUSEF`、`LANDMASK`；**无** `FRC_URB2D` | 城市分数缺失 |
| `URB_PARAM` 数值 | **132 层全部为 0**（min=max=0） | NUDAPT44 仅覆盖美国，兰州不在范围 → `fill_missing=0.` |
| `LU_INDEX` | 取值 {1..7,9,10,12,13,14,16,21}；==13（城市）104 个格点（d02，111×111） | 有城市格点 |
| `LANDUSEF[13]` | min 0 / max 1.0 / mean 0.009；262 个非零格点 | 城市面积分数信息**存在于 LANDUSEF 里** |

**结论**：以现有 geog 数据，**无法直接生成官方口径的 `FRC_URB2D`**；`URB_PARAM`（含建筑高度等形态参数）在兰州全为 0。

### 3.2 WRF 内置的三重回退（源码实证 → 决定了双跑可行性）
`module_initialize_real.F`（`sf_urban_physics ∈ {1,2,3}` 时）：
1. 若 `FRC_URB2D ≥ 0.5` 且 `ivgtyp` 非城市 → 强制 `ivgtyp = 13`（MODIS/NLCD40）
2. **若 `FRC_URB2D == 0` 且 `ivgtyp ∈ {13,24,25,26}` → `FRC_URB2D = 0.9`**（回退）
3. `LP/LB/HGT_URB2D = URB_PARAM(91/95/94)`、`MH/STDH_URB2D = URB_PARAM(92/93)`（SLUCM）、`HI_URB2D(k)=URB_PARAM(117+k)`（BEP，k=1..15）

`phys/module_sf_urban.F`（`urban_param_init`，`SWITCH_URB==1` 分支）：
- `HGT_URB2D ≤ 0` → 打印 **`USING DEFAULT URBAN MORPHOLOGY`**，把 LP/LB/HGT/MH/STDH/LF（或 HI）归零 → 转向 `URBPARM.TBL` 的**通用默认形态**
- `FRC_URB2D == 0` → 打印 **`WARNING, FRC_URB2D = 0 BUT IVGTYP IS URBAN`** + **`THE URBAN FRACTION WILL BE READ FROM URBPARM.TBL`** → `FRC_URB2D = FRC_URB_TBL(UTYPE_URB)`
- `UTYPE_URB = UTYPE_URB2D(I,J)`；`UTYPE_URB2D` 在 `Registry.EM_COMMON` 里是 `state integer ... rd=`（**无默认值**）→ 若输入文件没有它，保持 0 → 索引 `*_TBL(0)` 有越界风险（需实测确认）

**推论**：
- `sf_urban_physics=1`（SLUCM）**有望可行**：靠 URBPARM.TBL 的 3 类通用参数 + real 的回退 0.9
- `sf_urban_physics=3`（BEP+BEM）**风险高**：BEP 的建筑高度分布 `HI_URB2D` 依赖 `URB_PARAM`（全 0）→ 形态退化
- **这正好是论文2 立项的技术理由**：国内做 WRF-Urban 必须自建参数场（ch20 第三级 + 论文2 §4.3）

### 3.3 实验设计（阶段 1 = 可行性短测，作业 439719）
- 新实验根：`/users/zhyuancheng2025/IceLake/ch19_exp/`；三目录 `sf0/ sf1/ sf3/`
- 每个目录：链接 `build/WRF/run/*` 静态数据 + 可执行 + `met_em.d0{1,2}.*`（21+21 个）
- 流程：`real.exe`（用 5 天 namelist，**必须重跑**——`FRC_URB2D` 回退赋值只在 `sf_urban_physics>0` 时执行）→ 10 分钟短测 `wrf.exe`（np=16）
- 短测 namelist 要点：`run_days=0 / run_minutes=10` **且** `end_day=12,12 / end_hour=00,00 / end_minute=10,10`（ch08 修正 2：d02 的 nest_stop 取自该域 end_*，单值会让 d02 永不激活）
- 生成器：`workspace/scripts/ch19_gen_namelists.py`（产出 `nml10_sf{0,1,3}` / `nml5d_sf{0,1,3}`）
- 判据：rc、`SUCCESS COMPLETE WRF`、`domain   2` 行数（确认 d02 激活）、两条 urban 提示日志是否出现
- 作业脚本：`workspace/cluster/ch19/ch19_short_{outer,inner}.sh`

### 3.4 阶段 1 实测结果（作业 439719，cpu8；2026-10-11 03:59–04:03）

**real.exe 三档全部成功**（run_days=5 的 namelist）：

| 档 | sf_urban_physics | rc | 耗时 | wrfinput_d01 / d02 | wrfbdy_d01 |
|---|---|---|---|---|---|
| sf0 | 0 | 0 | 39 s | 14,330,915 / 20,573,408 | 58,724,166 |
| sf1 | 1 | 0 | 34 s | 14,426,926 / 20,701,684（**+96 KB / +128 KB** ← 城市场写入） | 58,724,166 |
| sf3 | 3 | 0 | 32 s | 14,352,089 / 20,596,617 | 58,724,166 |

（=1/=3 的 wrfinput 略大，与 `FRC_URB2D` 等城市场被回退赋值后写入一致）

**wrf.exe 10 分钟短测：三档全部失败，但失败原因不同**

| 档 | rc | 耗时 | 现象 |
|---|---|---|---|
| sf0（=0） | 255 | 39 s | **SIGSEGV**（写完 t=0 wrfout + 读完 wrfbdy 之后） |
| sf1（=1） | 255 | 38 s | **SIGSEGV**（同上，位置完全一致） |
| sf3（=3） | 1 | 22 s | **FATAL：`module_physics_init: use ysu (option1), myj (option 2), or boulac (option 8) with BEP/BEM urban scheme`** |

**发现 A（新结论，教科书级实证）：`sf_urban_physics=3`（BEP+BEM）要求边界层方案 ∈ {1 YSU, 2 MYJ, 8 BouLac}。**
本案例基线用 `bl_pbl_physics=5`（MYNN2.5）→ 直接 fatal。这**逐字印证了 ch14 章的结论**（BEP/BEM 官方兼容清单 = YSU/MYJ/BouLac，MYNN 不在列）。
→ 要在 ch19 做 =3 的对照，必须把 `bl_pbl_physics` 改为 8（BouLac，论文2 首选）或 1（YSU）；且为保持**单变量对照**，三档应统一用同一 PBL 方案。

**发现 B（待查）：sf0（=0，与 ch08 成功配置相同）在 10 分钟两域短测下 SIGSEGV。**
ch08 的 439419（np64、5 天、两域、同物理）成功；ch08 的 expC（np16、RRTMG、**仅 d01**）也成功。
本次用 `end_minute=10,10`（**双值，d02 会激活**）+ np16 → 崩。
→ 已提交 np 对照作业 **439720**（sf0 分别用 np=16 / 1 / 64 跑 10 分钟），用于区分"并行分解相关"与"间歇性/配置问题"。

> 注意：`urban_param_init` 的两条提示（`USING DEFAULT URBAN MORPHOLOGY`、`URBAN FRACTION WILL BE READ FROM URBPARM.TBL`）在本次日志里**未出现**——因为 sf1 尚未进入物理初始化就崩了，sf3 在 physics_init 的 PBL 检查处就 fatal 了。

### 3.6 阶段 2 设计（据阶段 1 修订）
- 城市对照的**边界层方案统一改为 YSU(1) + sf_sfclay_physics=1**（BEP/BEM 只兼容 bl_pbl∈{1,2,8}；YSU 面层要求 1/91）
- 对照档位改为三跑（两对单变量对照）：
  - **exp1**：`sf_urban_physics=1`（SLUCM）+ MYNN 套装（bl=5, sfclay=5）→ 对照 = **ch08 439419 的 =0 基线（同套装，已有产物）**
  - **exp2**：`sf_urban_physics=0`（CTRL）+ YSU 套装（bl=1, sfclay=1）
  - **exp3**：`sf_urban_physics=3`（BEP+BEM）+ YSU 套装 → 与 exp2 单变量配对
- 生成器：`workspace/scripts/ch19_gen_main.py` → `nml_exp1/exp2/exp3`

---

## 四、排错全记录（ch19 写作的核心素材，全部实测）

### 4.1 事故链与根因（按发现顺序）

| # | 现象 | 根因（证据） | 处置 |
|---|---|---|---|
| 1 | 三个 5 天作业 30 s 内全部退出 | **计算节点默认 `ulimit -s = 8192`（8 MB）** → WRF `solve_em` 的自动数组栈溢出 → SIGSEGV（U 组对照：默认栈崩、`ulimit -s unlimited` 后 U2/U3 正常步进 301/18 步） | 作业脚本加 `ulimit -s unlimited` |
| 2 | `=3` 作业 fatal | `module_physics_init: use ysu (option1), myj (option 2), or boulac (option 8) with BEP/BEM urban scheme`——本案例基线 `bl_pbl_physics=5`（MYNN）不在列 | 改 YSU(1)（或 BouLac(8)） |
| 3 | 改 BouLac(8) 后仍 fatal | `module_physics_init: use sfclay or myjsfc scheme for this pbl option`（BouLac 要求 sf_sfclay∈{1,2}，本案例为 5） | 弃 BouLac，用 **YSU(1)+sf_sfclay(1)** |
| 4 | `=1`（SLUCM）作业 rc=1，rank 34 报 | `ZDC + Z0C + 2m is larger than the 1st WRF level - Stop in subroutine urban` | 见 4.2 |
| 5 | 上述 fatal 的根因 | `urban_var_init`（`phys/module_sf_urban.F`）把 **`UTYPE_URB2D(I,J)=0` 强制置零**（唯一例外：`slucm_distributed_drag` 分布式空气动力学模式会设 2）→ `read_param(UTYPE)` 里 `ZDC_TBL(UTYPE)`/`Z0C_TBL(UTYPE)` 用索引 0 查表 → **越界读** → 垃圾值触发 fatal。且 `UTYPE_URB2D` 在 `Registry.EM_COMMON` 里**没有 `i`（输入）流标志**（`rd=(interp_fcni)u=(copy_fcni)`），实测 wrfinput 里确实**不存在**该变量 → 无法用"改输入文件"绕过 | 采用**沙箱最小补丁**（见 4.3） |

**教材价值**：第 1 条是"环境/资源类"故障（隐藏最深、最费时）；第 2–3 条是方案兼容链（ch14 已埋的伏笔在 ch19 兑现）；第 4–5 条是"数据缺口 + 源码缺陷"的复合体，直接构成论文2 的立项理由。

### 4.2 关键源码锚点（精确）
- `phys/module_physics_init.F`：`pbl_select: SELECT CASE(bl_pbl_physics)`——YSU 要求 `isfc∈{1,91}`；BouLac 要求 `isfc∈{1,2}`；**MYNN(5) 要求 isfc∈{5,1,2} 并显式禁止 BEP/BEM**（`IF (SF_URBAN_PHYSICS.eq.2).OR.(3) CALL wrf_error_fatal(...)`）；SHINHONG/MRF/ACM/GFS/QNSE 等也各自带同类守卫
- `phys/module_sf_noahdrv.F`：`UTYPE_URB = UTYPE_URB2D(I,J)` → `CALL urban(..., UTYPE_URB, ...)`
- `phys/module_sf_urban.F`：`urban`→`read_param(UTYPE, ZR, SIGMA_ZED, Z0C, Z0HC, ZDC, SVF, R, ...)`（表值取用）；`read_param` 里逐字段 `ZR=ZR_TBL(UTYPE)`、`ZDC=ZDC_TBL(UTYPE)`…；`ZDC_TBL(LC)` 由 Macdonald(1998) 式在 `urban_param_init` 预计算；检查在 `IF (ZDC+Z0C+2. >= ZA) FATAL_ERROR(...)`
- `phys/module_sf_bep_bem.F`：`param` 子程序 `if ((hgt_urb<=0.).OR.(lp_urb<=0.).OR.(lb_urb<=0.))` → 回退表值 `ws_u(id,iurb)/bs_u(id,iurb)`；`icBEPHI_XY` 对高度直方图 `hi_urb1D` 做归一化（`dtot>0` 才归一，否则跳默认）
- `urban_var_init`（module_sf_urban.F）：`SWITCH_URB==1` 时若 `HGT_URB2D<=0` → 打印 **`USING DEFAULT URBAN MORPHOLOGY`** 并把形态场清零 → 下游全部走 URBPARM 表值（"默认城市形态"路径）
- `dyn_em/module_initialize_real.F`：`sf_urban_physics∈{1,2,3}` 时若 `FRC_URB2D==0` 且 `ivgtyp` 为城市 → **`FRC_URB2D=0.9`**（回退）；实测 sf1/sf3 的 wrfinput 中 `FRC_URB2D.max()=0.9` ✓

### 4.3 最小补丁（沙箱树 `ch18_exp/WRF-ideal`，一行）
```fortran
! 改前（module_sf_urban.F 的 urban_var_init 内）
      UTYPE_URB2D(I,J)=0
! 改后
      UTYPE_URB2D(I,J)=2   ! ch19 patched: fallback to URBPARM class 2 (no urban-type dataset)
```
- 语义：兰州（及中国多数区域）无城市类型数据 → 回退到 `URBPARM.TBL` 的 2 号类（高密度住宅，ZR=7.5 m）
- 只改**沙箱树**（不动主构建树 `build/WRF`），重建 `compile em_real`（增量：module_sf_urban.o + 依赖 + 重链接）
- 产物：`ch19_exp/bin/wrf_urbanpatched.exe`（md5 记录在 `SUMMARY_patch.txt`）；三个运行目录的 `wrf.exe` 均指向它
- 原文件备份：`ch19_exp/module_sf_urban.F.orig_*`

### 4.4 数据可用性硬结论（论文2 立项依据）
- `geo_em.d02` 有 `URB_PARAM`(132 维) 但**全为 0**（NUDAPT44 只覆盖美国）；`FRC_URB2D` 变量不存在（geog 缺 `urbfrac_*` 数据集，`/opt/app/wrf/WPS_GEOG` 只有 72 个目录，无 urbfrac/imp/can）
- 因此**兰州无法用官方数据路径获得城市分数/形态/类型**；WRF 对"无数据"的兜底只有 `FRC_URB2D=0.9`（real）+ 表值形态（物理初始化），**城市类型必须靠代码/输入通道补**——这正是论文2 §4.3（参数场管线）与 ch20 第三级的现实动因

### 4.6 探针裁决（作业 439819，决定性数据）
在 `module_sf_urban.F` 的检查前插探针打印（`ch19probe UTYPE,ZR,ZDC,Z0C,ZA,R,HGT`），实测（np=32）：

```text
ch19probe UTYPE,ZR,ZDC,Z0C,ZA,R,HGT =  2  7.500000  5.718321  3.329077E-01  8.045776  0.5000000  3.989362E-01
（ZA 随格点 8.046 → 8.24 变化）
```

**裁决结论**：
1. 表类 2（ZR=7.5 m）的 `ZDC + Z0C + 2 = 5.718 + 0.333 + 2 = 8.051 m`，而城市格点的 `ZA = 0.5·DZ8W ≈ 8.05–8.24 m` → **正好压在阈值上**：p_surf 高（ZA 小）的格点越界 → fatal。这不是"数据错误"，而是"垂直分辨率与城市参数不匹配"的硬边界。
2. **UTYPE 探针值为 2 而非 1**：patch2 的 `sed` 替换未生效（模式串未匹配；具体原因见 SUMMARY_patch2 的 grep 记录）→ 需要用 Python 正则精确改写。
3. 表类 1（ZR=5 m）推算值：`ZDC = 5×(1+4.43^(−0.5)×(0.5−1)) = 3.813`；`Z0C = 5×(1−0.7626)×exp(−(3.75×0.2374×0.3012)^(−0.5)) ≈ 0.17` → `ZDC+Z0C+2 ≈ 5.99 m` **远低于 ZA=8.05** → 可通过（待 patch3 验证）。

### 4.7 补丁版本账（沙箱树）
| 版本 | 内容 | md5 | 用途 |
|---|---|---|---|
| baseline | 未改动 | e81b501625f9587635de53dfc0470a0e | ch08 基线 / 对照 |
| patch1 | UTYPE 0→2 | 57436cd4165ef29941827d9475d761da | 验证 0 越界假设（类2 仍卡阈值） |
| patch2 | （sed 未生效，实际= patch1） | 45d09b91be822e28f2e0903fb39a85c6 | —— |
| probe | patch1 + 探针打印 | f06a9402e78e91f5aa1eab3483b530c2 | 取得 4.6 的数值 |
| **patch3** | **UTYPE 0→1 + 去探针** | 见 SUMMARY_fix.txt | **exp1/exp3 正式运行用** |

### 4.8 关键"约束驱动设计"结论（教材主线之一）
城市方案的可用性受**三重约束**同时限制：
1. **PBL 兼容**（BEP/BEM 仅 YSU/MYJ/BouLac）→ 决定物理套装；
2. **面层兼容**（YSU 需 sfclay=1；BouLac 需 1/2）→ 决定面层方案；
3. **垂直分辨率 vs 城市形态**（`ZDC+Z0C+2 < ZA`，SLUCM 专有检查）→ 决定可用 URBPARM 类别：本案例 ZA≈8.05 m → 只能用类 1（ZR=5 m）；类 2（7.5 m）恰好越界。
   → **论文 2 的低层加密（2 m 内 ≥5 层）正是为解除第 3 条约束**（ZA 变小会让约束更紧，故论文 2 需同时保证首层足够厚——这正是需要在设计阶段算清楚的量）。

### 4.9 待办
- [x] patch4：仅改 `module_sf_urban.F` 一行（普通城市格点默认类别 2→1）→ md5 941ba403a1488291da7ddd2102c7a93c，200 s 验证 1222 步无 fatal
- [x] 三跑启动：exp1(439828, =1+MYNN, class1) / exp2(439810, =0+YSU, 已完成 SUCCESS) / exp3(439815, =3+YSU class2 → 被 stale-file-handle 砍在 4.5 天) → **exp3 重跑 439866（=3+YSU, 改用 class1 二进制统一类别）**
- [x] 抽取管线：`ch19_exp/extract_stage.sh`（ncks 逐文件、域中心 31×31 小窗；surf 全时次 + prof 每 6 帧）；教训：ncks 不能合并"正在写"的 wrfout（只用已关闭文件）；stage.tar.gz 已可拉回
- [x] 本地诊断脚本 `workspace/scripts/ch19_diagnose.py`（管线验证通过；已修 Times 缺失/MetPy 参数/负号字形三处）
- [ ] 待 exp1（~25 min）+ exp3b（~50 min）完成后：最终抽取 → 拉回 → 诊断出图 → 回填 19.4/19.5.6
- [ ] 四件套同步（verify_log/chapter_map/progress/notes）+ 复核清单第 14 条

### 4.10 事故与教训（三条，均已写入教材）
1. **栈限制**：计算节点 `ulimit -s = 8192`（8 MB）→ solve_em 栈溢出 SIGSEGV；作业脚本必须 `ulimit -s unlimited`（对照作业 439729 实证）。
2. **方案兼容链**：BEP/BEM 需 bl_pbl∈{1,2,8}；BouLac 需 sfclay∈{1,2}；YSU 需 sfclay∈{1,91} → 唯一三档通用 = YSU(1)+sfclay(1)。
3. **运行中改脚本**：`sed -i` 替换正在执行的作业脚本 → `Stale file handle` → exp2 侥幸跑完、exp3 被砍在 4.5 天。**作业运行期间不得改动其脚本。**
4. （数据侧）`UTYPE_URB2D` 在 Registry 中无输入流标志、wrfinput 里不存在 → 只能改源码；而 WRF 默认给普通城市格点硬编码"高密度（类 2）"，恰好越过本案例 `ZLVL≈8.05 m` 的阈值 → 一行补丁降到类 1。

### 4.11 诊断口径（已定，待数据）
- 城市掩膜 = `FRC_URB2D > 0.5`（取自 wrfinput_d02，窗口裁剪 39:70/44:75）
- 乡村掩膜 = `FRC_URB2D ≤ 0` 且 `LU_INDEX ∈ {10,12,14}`（草地/农田）
- 地方时 = UTC + 7；分析段 07-13～16
- 三条诊断线：T-lnP（MetPy：LCL/LFC/EL/CAPE/CIN）、T2 日最高 vs ERA5、城市-乡村 ΔT2 与 =3 相对 =0 的增量