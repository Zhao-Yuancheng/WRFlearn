# 《WRF 源码导论：大气物理与模式实践》——总目录与使用说明

> **版本口径**：WRF 4.8.0 + WPS 4.7.0（本地源码 `source/WRFv4.8.0/WRFV4.8.0/` 与 `source/WPSv4.7.0/`，集群部署一致）。所有陈述以本地源码为第一事实源，写作当次核验，留痕于 `workspace/context/verify_log.md`。
> **贯穿个例**：兰州 2025-07 高温（2025-07-12 00Z 起报、07-13～16 分析段；两域 9/3 km；集群全程实录）。
> **配套底本**：《大气物理学》（盛裴轩等，第 2 版）——物理底蕴；书第 7 章动力学按需引用。

## 一、使用说明

### 1.1 这本书怎么读

- **以 WRF 源码为主、大气物理为辅**：每章的“源码走读”是主干，物理概念在需要处引入；书中公式 ↔ WRF 源码语句的对应关系随文标注（文件 + 子程序名，不写行号——行号会漂移，符号不会）。
- **三类专栏**（体例约定见 ch01 §1.6.2，全书 35 案索引见 ch20 §20.7.1 与 ch21 §21.8.1）：
  1. **科研改造案例库**——课题 → 改哪个文件 → 原码/改码（小改旁注，大改按“公开代码/伪代码/思路”三档收录）；
  2. **核心代码精讲**——模块基本原理、公式与核心求解器的逐段注释；
  3. **模块依赖树**——文件级依赖 + 各节点提供的函数。
- **动手实验两轨**：轻轨=本地 python（WRFlearn 环境）公式复现与诊断；重轨=集群 slurm 实录（WPS/real/wrf/改造）。每章实验脚本在 `workspace/scripts/chNN_*.py`，日志在 `workspace/logs/`。
- **阅读路径建议**：
  - 系统学习：第 I 部 → 第 II 部（照做流水线）→ 第 III 部 → 第 IV 部 → 第 V 部；
  - 只想改造 WRF：ch04 → ch05 → ch20 → ch21，回查对应物理章；
  - 只想跑个例：ch06 → ch07 → ch08 → ch19；
  - 城市热岛方向：ch17 → ch19 §19.5 → ch20 第三级 → ch16。

### 1.2 版式约定

- 中文部分一律全角引号；代码块标语言；LaTeX 公式；mermaid 流程图（VSCode 可渲染）。
- 源码引用格式：`相对路径 + 子程序名`（如 `dyn_em/solve_em.F: rk_tendency`），每段源码旁标注 Registry 变量与 namelist 关联。
- 物理章的考点体系 = §N.0.2“考点清单” + 章尾“习题/思考题（含答案）”节（题型四分类 + 书习题 + 模式视角补充题带答案）；书第 6 章 PPT 未到货的 ch13–ch15 考点节为自拟版，待 PPT 到货校准（ch16 承载书第 4 章，PPT 4《大气分层》在案、按内容页归纳）。
- 勘误与口径分歧（书页印刷错误、常数双口径等）随文注明，不改原文只加注。

### 1.3 书页换算规则

《大气物理学》扫描件无文本层，引用一律带印刷页码，定位方法：

```text
印刷页 N  →  AtmosphericPhysics/book/page_{N+14:04d}.jpg
（例：印刷页 128 → page_0142.jpg；PDF 目录页在 page_0008–0014）
```

底账：`workspace/book_manifest.csv`。书图引用格式：“书 图 X.Y（印刷页 N）”。

### 1.4 状态与复现

- 事实核验：`workspace/context/verify_log.md`（日期｜主题｜来源｜结论）；
- 章—源码锚点：`workspace/outline/chapter_map.md`（随核验标“已核验”）；
- 集群作业台账与原始日志：verify_log 各章段 + `workspace/logs/`；
- 全部实验可复现入口：各章“动手实操”节 + `workspace/scripts/`。

## 二、总目录

### 第 I 部　引言与世界观

| 章 | 文件 | 一句话 |
|---|---|---|
| 1 从行星大气到数值模式 | [ch01](ch01_from_atmosphere_to_models.md) | 书第 1 章全考点；WRF 家族与根目录树；三类专栏体例约定 |
| 2 WRF 4.x → 4.8.0 演化 | [ch02](ch02_wrf_evolution.md) | 逐版 release notes + 本地源码指纹表（14 条） |

### 第 II 部　WRF 全流程实战（贯穿个例：兰州 2025-07）

| 章 | 文件 | 一句话 |
|---|---|---|
| 3 架构总览 | [ch03](ch03_architecture_overview.md) | 一次预报的完整生命周期；四层架构；驱动层依赖树 |
| 4 Registry 机制 | [ch04](ch04_registry_mechanism.md) | 声明式变量中枢；IO 串语法；代码生成链；T2_PEAK 纸上设计 |
| 5 编译体系与增量重编译 | [ch05](ch05_build_and_dev_loop.md) | cmake 双轨；test/em 全表；增量循环实测；Registry 触发门 |
| 6 WPS：geogrid→ungrib→metgrid | [ch06](ch06_wps_pipeline.md) | namelist.wps 逐项；Vtable；兰州个例三步实录 |
| 7 real.exe 与 namelist.input | [ch07](ch07_real_namelist.md) | 基态构造；η 坐标初步；物理方案号表；wrfinput 解读 |
| 8 运行 wrf.exe | [ch08](ch08_running_wrf.md) | slurm 实战；rsl 解读；restart 语义（分钟制！）；短测代表性事故 |
| 9 IO 体系 | [ch09](ch09_io_system.md) | io_form 五写法实测；quilt 服务器；auxinput 机制 |

### 第 III 部　物理过程族

| 章 | 文件 | 一句话 |
|---|---|---|
| 10 垂直坐标与静力平衡 | [ch10](ch10_vertical_coords_hydrostatics.md) | 书第 3 章+4.1–4.2；η/hybrid 基态构造；压高公式实验 |
| 11 大气成分、水汽与气溶胶 | [ch11](ch11_composition_moisture_aerosol.md) | 书第 2 章；常数表核对；五套饱和水汽压实现 |
| 12 辐射过程族 | [ch12](ch12_radiation_family.md) | 书第 5 章全考点；RRTMG 精读；太阳几何逐格闭环 |
| 13 微物理方案族 | [ch13](ch13_microphysics_family.md) | 书 6.1–6.7；Thompson 精读；饱和调整=书 (6.6.3) 的两种解法 |
| 14 边界层方案族 | [ch14](ch14_pbl_family.md) | 书 6.8；MYNN-EDMF 与 BouLac 双精读；PBLH 三型判据 |
| 15 积云参数化族 | [ch15](ch15_cumulus_family.md) | 书 6.9；New Tiedtke 精读；触发/闭合/夹卷三件套 |
| 16 陆面过程族 | [ch16](ch16_land_surface_family.md) | 书 4.2–4.3+模式补讲；Noah 精读；SOILPARM 表核 |
| 17 城市冠层专章 | [ch17](ch17_urban_canopy.md) | SLUCM→BEP/BEM；URBPARM 逐字段；BEM 改造地图（论文 2） |

### 第 IV 部　实验与改造

| 章 | 文件 | 一句话 |
|---|---|---|
| 18 理想实验入门 | [ch18](ch18_ideal_cases.md) | test/em 全表；双钥匙机制；三算例集群实录 |
| 19 真实个例全流程实录 | [ch19](ch19_lanzhou_heatwave.md) | 兰州高温质控六条；城市冠层三跑（=0/1/3）；三重约束链 |
| 20 改造 WRF 三级实战 | [ch20](ch20_modifying_wrf.md) | 诊断变量/参数化内部/namelist 开关+BEM 逐格场；事故链七条 |

### 第 V 部　动力内核入门

| 章 | 文件 | 一句话 |
|---|---|---|
| 21 solve_em.F 全流程 | [ch21](ch21_solve_em_dynamics.md) | RK3+声波小步长十四站走读；物理调用时刻精确到子程序；时间步进账本 |

### 附录

| 附录 | 文件 | 内容 |
|---|---|---|
| A 符号与物理常数对照 | [app_a](app_a_symbols_constants.md) | 书符号 ↔ WRF 变量 ↔ Registry 三列；常数逐项偏差表 |
| B 中英术语对照 | [app_b](app_b_terminology.md) | 九类主题术语表（首现章号） |
| C 常见错误速查 | [app_c](app_c_troubleshooting.md) | 编译/WPS/real/运行/IO/内核/改造七段 + 万能诊断流程 |
| D 参考文献与数据源 | [app_d](app_d_references.md) | 分级文献清单（核验/通行/线索）+ 数据源致谢 |

## 三、全书实验与资产索引

- **实验总表**：方案 v2 §6.3（各章实验、两轨归属、机时实测）；
- **案例总索引**：ch20 §20.7.1（27 案）+ ch21 §21.8.1（案 28–35，动力内核与耦合）；
- **脚本库**：`workspace/scripts/`（cluster.py + 各章实验/诊断/抽取脚本）；
- **集群资源**：`/users/zhyuancheng2025/IceLake/wrf-4.8/`（WRF/WPS 编译树与个例目录）；作业模板规则（无 mem 参数、小任务≤8 核、大任务整节点、`ulimit -s unlimited`）见 ch08 与 app_c；
- **数据致谢**：ERA5 GRIB（liuyl17 共享）、WPS_GEOG（集群公共数据）——详见 app_d §d.7。

## 四、修订记录

| 日期 | 事件 |
|---|---|
| 2026-10-10 | 方案 v2 定稿；批次 1（ch03–ch09）交付，兰州个例 5 天模拟 SUCCESS |
| 2026-10-11 凌晨 | 批次 2（ch10–ch17）交付；批次 3（ch18–ch20）交付 |
| 2026-10-11 下午 | ch20 全链实跑闭环；ch01/ch02 交付；ch03–ch19 三类专栏补齐 |
| 2026-10-11 晚 | **批次 4 交付：ch21 + 附录 a–d + 本 index**——全书 21 章 + 4 附录成书 |
| 2026-10-12 凌晨 | **批次 5 全书校阅**：交叉引用/死链/符号统一/考点覆盖/全角引号五路清查（26 文件、约 2000 处指涉全查），修订 13 处——ch13 补微物理时刻交叉注与 q/r 口径注、ch14 修正 part1 调用序与“每步多次调用”误表述、ch16 考点标签改 PPT 4 口径、app_a 补泊松常数 κ_d 行、index 考点体系说明订正等 |
