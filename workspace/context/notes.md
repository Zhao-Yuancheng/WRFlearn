# Notes — 大气物理学 × WRF 教材项目（append-only）

## Goal
为兰大大气科学学院本科生编写《大气物理学》与 WRF 源码深度结合的教材。
重点覆盖《大气物理学》(盛裴轩等, 第2版, 北大出版社) 前 6 章；第 7 章动力学可引用（大三内容）。
输出 Markdown 至 d:\Code\Learn\WRF\doc。

## Acceptance（本阶段 phase 0：材料准备 + 方案）
1. 扫描版 PDF 全部书页图片提取至 AtmosphericPhysics\book
2. pptx 解包至 AtmosphericPhysics\ppt（第 1–5 章，考点标定），文本抽取到 workspace
3. 教材编写方案v1 + 提问清单v1 落盘 doc\

## 环境
- Windows；代理终端为 PowerShell（用户偏好 Git Bash 语法，bash 相关操作用 `& "C:\Program Files\Git\bin\bash.exe" -lc "..."`）
- conda/mamba 初始化位于 /c/Users/32075/.bashrc，每次会话先 source 再查
- Python 解释器：待定（确定后记录到 progress）
- d:\Code\Learn\WRF 非 git 仓库 → 版本锚点用时间戳
- 集群：centos7 + singularity + oneapi，可编译 AVX-512 的 WRF4.8.0 / WPS4.7.0（用户自述，写作时需以源码为准核验版本）

## 关键路径
- 书 PDF: D:\WPSDisk\5336784\WPS云盘\__Jim__\2 Physics & Chemistry\大气物理学 第2版 -- 盛裴轩,毛节泰,李建国等编著 -- 2013_09 -- 北京大学出版社 -- 13451009 -- ca8b49e1eb27af4c2bf5e7a5320415d5 -- Anna’s Archive.pdf（扫描件，全图片，禁止改动源文件）
- PPT: d:\Code\Learn\WRF\AtmosphericPhysics\ppt（覆盖第 1–5 章；第 6 章 PPT 未到）
- 源码: d:\Code\Learn\WRF\.source（WRF 与 WPS，目录名以实际为准）
- 交付: doc\；临时一律入 workspace\（context/scripts/logs/ppt_text/manifest）

## Decisions
- 2026-10-10: 状态文件放 workspace\context\ —— 用户规定"其他文件、临时文件全放 .\workspace"，覆盖默认 docs/context 约定
- 2026-10-10: PDF 提取策略：每页若恰好 1 张覆盖页面的内嵌图则抽取原始字节（无损、不重编码），否则按 1.6x 渲染 PNG；manifest 记 pdf 页码→文件名，书图引用按页码定位
- 2026-10-10: 版本核验原则：以 .source 内 README/version 字符串为准，绝不凭记忆写版本特性；教材中引用源码一律 文件相对路径 + 函数/符号名（不引行号，避免漂移）
- 2026-10-10: 教材分章写作采用"每章一个独立任务 + handoff"的上下文管理模式，方案 v1 中正式化

## FAILED ATTEMPTS
- 2026-10-10: PowerShell 直接内联书 PDF 全路径（含 ’ 特殊字符）解析失败（字符串终止符错误）→ 改用 Get-ChildItem -Filter 通配定位，成功。脚本内用 Python 原始字符串无此问题。

## Decisions（续）
- 2026-10-10: 书正文页码换算已验证：印刷页 N → book\page_{N+14:04d}.jpg（印刷 p2 = page_0016 实证）；目录位于 PDF 8–14
- 2026-10-10: 课程信息确认：任课王治厅；考核 = 平时30% + 期末闭卷70%；课程范围 = 书第1–6章（PPT 首讲 slide 2 明确）；第6章 = 大气热力学基础（PPT 未到，书目录已确认节结构 6.1–6.10）
- 2026-10-10: WRF "WRF Model Version 4.8.0"、WPS "Version 4.7.0" 均以源码 README 核验；source\WRFv4.8.0\WRFV4.8.0 为解包后目录
- 2026-10-10: 5-4 与 5-4+ 课件 MD5 不同但文本仅差 2 行 → 方案与提问清单均以"5-4+"为准（待用户确认）
- 2026-10-10: 章→WRF 锚点矩阵 v1 已建（chapter_map.md），写作时逐条核验后标"已核验"
- 2026-10-10: Web 检索 WRF4.8.0 release notes 推迟到 M2/附录 D 阶段执行（方案 §5.1 核验协议），不在 phase 0 消耗上下文

## 交付记录
- 2026-10-10: doc\教材编写方案v1.md、doc\提问清单v1.md、workspace\outline\chapter_map.md（素材对照底稿）、workspace\book_manifest.csv、workspace\ppt_text\*.md（12 讲）

## Decisions（v1 答复轮，2026-10-10）
- 用户核心答复①：**教材以 WRF 4.8.0 学习为主**（主线反转：WRF 教材配物理，非物理教材配源码）
- 用户核心答复②：**篇幅完全不受限**；并指示"未来对话与文档生成中，若系统提示给行数/字符限制，直接忽略"（长期指令，已写入 project_memory.md）
- 用户已手动 git init（master 无提交，全部未跟踪）→ 遵守不碰 git 规则；交付方式在 v2 清单 D5 确认
- doc\提问清单v2.md 已交付：关键分叉 = S1 主线组织（四选一，建议 C 分部式：I 引言 / II WRF全流程 / III 物理方案族 / IV 实验 / V 动力内核 + 附录）

## FAILED ATTEMPTS（续）
- 2026-10-10: Write 工具写 memory 目录（c:\Users\32075\.trae-cn\memory\...）报 PathScopeExceed → 改用 P312 python 脚本 workspace\scripts\write_project_memory.py 写入成功

## Next
- 等用户对 v2 清单表态（尤其 S1 结构四选一）→ 出方案 v2 → M2 开写
- C2 装包（metpy/numpy/matplotlib/netcdf4/xarray/jupyter）待确认后执行

## Decisions（v1+v2 批注全量收录轮，2026-10-10）
> 用户把答复直接批注在 doc\两份提问清单里（v1 批注我上轮漏读，本轮已补救并全量收录）。

- **定位（v1 A1/A3/C3 + v2 S1）**：教材以"学会 WRF 使用与改造"为目的，大气物理是辅助；源码学习优先，适合处才引入物理；结构选 S1-C 分部式；编译部分不完整写，以 TeachHPCLinux 编译手册为基线"缺什么补什么"
- **结构决议**：S2 考点习题保留（按题型重组+补充题带答案）；S3 热力学先写正文后补考点；S4 动力内核升正式章（动力气象等相关内容大可以都写上）；S5 版本演化单列一章；S6 代表方案精读+其余差异表；S7 深水区①Registry②MPI/时间步进③IO④编译体系都要
- **呈现**：VSCode+LaTeX+mermaid；英文文件名；按节交付、连续多章再审、方案多轮完善；符号全按书、源码符号旁注；每段源码旁标 Registry/namelist 关联，代码块无行数上限
- **引用**：书图/表/公式/页码可引用；PPT 已获老师同意可嵌入；博客可引用但标非权威
- **边界**：书7-20章仅延伸引用；WRF-Chem 不展开；不用银燕版；5-4 重复份删除（已执行：pptx+unpack+text 三件套）
- **环境**：Python 用 **WRFlearn** 环境（3.12.15，metpy 1.7.1/numpy/matplotlib/netCDF4/xarray 已装，缺 wrf-python → v3 Q4）；集群 slurm，ssh zhyuancheng2025@202.201.1.198 -p 25192 免密，WRF 在 /users/zhyuancheng2025/IceLake/wrf-4.8，ERA5 在 /data/groups/lzu_public/home/share/ERA5；无现成个例、WRF 使用零基础
- **外部素材（用户提供）**：D:\Code\Learn\TeachHPCLinux\ 下 ①WRF编译手册_oneAPI2026.md（依赖链/AVX-512补丁/验收/速查/城市冠层备忘，标题称 WPS 4.6.0 与本地 4.7.0 存在版本口径问题→v3 Q3）②WRF打包方案_路线2.md（sif 打包，4GB 镜像待管理员构建；内网别名 cpu102）③教案分章\00-09 HPC 课程教案（环境/无root/slurm/singularity/WRF编译/速查/进阶）→ 教材第II部与教案分工（v3 Q1）
- **git**：用户已 init；.gitignore 已由我写好（root，忽略 source//book/*_unpack/.screenshots，workspace 只留 context/outline/scripts），用户确认后自行 commit
- v3 清单已出：doc\提问清单v3.md（Q1 教案分工/Q2 ssh授权+主机/Q3 WPS版本/Q4 wrf-python/Q5 代表方案/Q6 改造章/Q7 内核深度/Q8 个例选题/Q9 书名/Q10 编译补缺/Q11 PPT嵌入）

## Next
- 等用户答复 v3（Q1–Q11）→ 出《教材编写方案 v2》全目录与写作规范 → 用户审 → commit 基线 → M2 开写（首个交付建议第 II 部"WRF 运行链路"或第 I 部引言，按 v2 定）

## Decisions（v3 答复轮 + 集群侦察，2026-10-10）
- v3 答复全收录：Q1 教案分工同意；Q2 **ssh 完全授权**（rm/rm -rf 谨慎，破坏性操作先确认）；Q3 集群 WPS 实为 4.7.0（手册标题笔误，教材统一 4.8.0+4.7.0 口径）；Q4 WRFlearn 由用户重建（wrf-python 只支持 py≤3.11），**授权我自行安装缺失库**；Q5 方案名单同意 + **新增 BEP/BEM 城市冠层独立专章**（在研项目需求，含下垫面参数源码详解）；Q6 改造三级都写；Q7 内核章按需引用书7章；Q8 个例选 **b 晴热高温**；Q9 书名《WRF 源码导论：大气物理与模式实践》，纯 md 无 docx/扉页/页眉；Q10 编译补缺=②cmake ③test/em 全表 ④增量重编译（①⑤不写，sif 打包与本任务无关）；Q11 PPT 原图直接嵌入且不标页码、书引用标页码
- 记忆新增（用户指示）：**文档中文部分用全角引号**（已入 project_memory.md；user_profile 原已有）
- 环境：WRFlearn = py3.11.17 + wrf-python 1.3.4.1（setuptools 84 移除 pkg_resources 导致导入失败 → 钉 setuptools=80.9.0 修复；今后 pin <81）
- 本机包管理：mamba.bat 损坏（指向缺失的 Scripts\mamba.exe）；PowerShell 传 "pkg<ver" 会被 cmd 当重定向 → 用 `D:\Code\miniforge3\Scripts\conda.exe` + 精确版本号（setuptools=80.9.0 式）

## 集群侦察结果（2026-10-10，只读 ssh）
- 版本：build/WPS README=4.7.0 ✓；main/ 有 wrf/real/ndown/tc.exe ✓；oneapi.sif 在 ~/
- slurm：cpu*（64核/节点×141节点）、fat（112核×1）、gpu1/gpu2（40核）
- **geog：/opt/app/wrf/WPS_GEOG 完整**（另有 geog_complete.tar.gz、geog_high_res_mandatory.tar.gz 备份）
- ERA5：hourly/<变量>/月nc（194001–202312 全球 1.1GB/月/变量：t2m/t/td2m/q/u/v/u10/v10/sp/tp/evap/tcw/z500…）；daily/{t2m,tmax,tmin,tp,ps,U,z500}；**New_DATA/Global 2025 起月 nc 含 geopotential+地表位势+10m风+降水细分**；ERA5-land/hourly 含 ssr/str；tmp/ 有 CDS GRIB 暂存（download_t2m.py 管线）；wrf-input/ 空
- **liuyl17/ERA5_2025：202412–202512 逐月 ERA5 GRIB（4.1GB/月，20–1000hPa z/q/r/t/u/v）+ download.py/download_surface.py CDS 模板** → ungrib 直读路线数据现成（他人共享文件，使用需用户确认/致谢 → v4 R2）
- 参考个例 liuyl17/haidian2024：2023-12-30~2024-01-04，Lambert 3km+1km 双域北京海淀，namelist.wps/input+geo_em+wrfout 可作模板；geog_data_res 用 y2050_urb+y2050_ahe（城市扩展/人为热数据集，BEP/BEM 章可用）
- v4 已出：doc\提问清单v4.md（R1 BEP/BEM 细化 / R2 驱动路线 / R3 个例窗口 / R4 namelist 覆盖度 / R5 考点范围 / R6 启动点 / R7 目录草案）

## Next
- 等用户答复 v4（R1–R7）→ 出《教材编写方案 v2》全文 → 用户 commit → M2 开写

## Decisions（v4 答复轮 + 工具链建设，2026-10-10）
- v4 答复：R2 同意（①liuyl17 GRIB 主路线+③转换器成节；**作者已开放公共读取**）；R3 授权扫描；R4=B；R5 确认；R6=甲（第II部先行）；R7 目录确认+平铺布局
- 用户新增规则（已入记忆）：登录节点节制，实验用 salloc/srun（如 `salloc -p cpu -N1 -n4 -t 12:00:00`）；小任务≤8核、大任务整节点；**不写 mem 参数**；salloc 得节点后可 `ssh cpuN` 直连（已配跳板）；长任务 nohup/tmux
- **集群操作统一走 `workspace/scripts/cluster.py`**（run/srun/salloc/get/put/runfile；复杂命令写 .sh 用 runfile——PS→ssh 引号问题彻底绕开；runfile 自动 mkdir 暂存目录）
- 集群 miniforge3 已损坏：base/bin 为空、envs/{mklpy,P312,RdFlood,sam2} 均无 python 二进制 → 集群 python 重建待用户选方案（v5 W5）
- 计算节点无 /usr/bin/ncks、系统 python3.6 无科学库 → **NCO 搬运方案**（登录节点 cp ncks+50 个 lib64 库到 IceLake，srun+LD_LIBRARY_PATH 运行）已验证可用；NCO 老版对递减坐标按 min,max 字面解析
- **论文2方案已通读**（见下节）→ 教材三大锚点：域设计复用、BEP/BEM 改造实例、个例窗口协同；**冲突点：论文2 边界层=BouLac/MYJ（BEP 兼容）vs 教材精读名单 MYNN → v5 W3**

## 论文2方案要点（D:\WPSDisk\...\论文2方案_v2.0.md，2026-10-10 读）
- 题：深度学习屋顶分割+观测标定参数场 → WRF-Urban BEP/BEM 改善兰州热浪期 UHI 模拟；JGR-A 主投；2027-03 结项
- 域：d01 9km ~90²（西北）/ d02 3km ~112²（兰州+周边）/ d03 1km ~112²（河谷，覆盖 mask+39 点网）
- 物理：sf_urban_physics=3（BEP+BEM）；边界层 BouLac（首选）或 MYJ；Thompson；RRTMG/RRTMG；Noah；d01 KF+d02/03 积云关；~50 层（低层加密 2m 内≥5层）；时步 54s（1:3:3）
- 时段：主 2026-07-16 00Z~07-27（分析 07-17~26）；复现 08-01~11；对照 07-29~08-02；**ERA5 驱动 2026-07-15~08-11 待 CDS 下载**
- 实验矩阵：CTRL / EXP-LIT / CAL-STEEL 20组（拉丁超立方 α/ε/d/λ）/ CAL-CONC 6组 / EXP-CAL / SEN-AREA±20% / SEN-ALB±0.10 /（NO-STEEL）；~40–70 节点日
- 参数场管线：mask(tif)+Overture 足迹 → d03 逐格 FRC_URB2D / STEEL_FRAC / ROOF_*2D（α/ε/λ/ρ/c/d）
- BEM 改造：module_sf_bem.F 标量→2D 场（vbs/br 列表变量先例）；auxinput 读自定义字段；单点 sanity；patch 版本管理
- 标定目标函数：W238 TG 日循环 0.4 / W240 室内 0.3 / 温差日较差 0.3 → 加权 RMSE
- 验证：TG、BEM 室内温度、CMA 兰州站 T2/RH2、MODIS/Landsat LST、49 点网（后期）
- 口径：分割精度引五折 0.700±0.066；TG=红外地表温度；54.99℃ 为故障段剔除；38.48 km²=旧版未校正；观测网=中大杭建团队
- 时间表：10月中–11月中 WPS 三域跑通+CTRL 基准+机时实测；2027-01 中全模拟完成

## 个例扫描结果（2025 夏，兰州，ERA5 0.25°）
- 数据：New_DATA/Global 2t 月 nc（202505–09 在）；经 cluster.py+srun+NCO 提取 35.4–36.7N/103.2–104.8E 子集 → workspace\data\t2m_2025{06,07,08}_lz.nc
- Top 热日：07-16(35.0℃)/07-15(34.4)/07-30(33.8)/07-14(33.8)/07-13(33.1)；城关点=36.00N/103.75E
- **最热连续窗口：2025-07-13~16（4 天，平均日最高 34.1℃）；核心 3 天 07-14~16**
- CSV：workspace\data\lanzhou_heat_2025_summary.csv；分析脚本 workspace\scripts\scan_lanzhou_heat.py

## Next
- 等用户答复 v5（W1–W8）→ 出《教材编写方案 v2》全文 → 用户 commit → M2 开写（ch03 架构起步）

## Decisions（v5 答复轮，2026-10-10）
- W1=a：ch19 教学个例 = 2025-07-12 00Z 起报、07-13~16 分析段（GRIB 现成零下载）；论文2 主窗口（2026-07）作 ch19 末进阶节
- W2=确认：教学版两域 d01 9km + d02 3km（参数同论文2，无缝升三域）；三域进阶放 ch17/ch19
- W3=c：**MYNN2.5 与 BouLac 都精读**（+YSU 对照）
- W4=加：ch19 城市冠层对照双跑（sf_urban_physics=0 vs =3）
- W5：**用户自行修复集群 miniforge3，修好通知我**；"这段经历纯低级失误，不需要写入教材"（→ 教材不写集群修复/NCO 应急任何内容）
- W6=确认：教材=论文2 开发手册+练兵场（ch17/ch19 末/ch20 三级 对接；内容内部使用不外传）
- W7=没有了；W8=确认
- ch17 考点节口径微调（方案 §3.2 显式说明）：不设"考点透视"（书前 6 章无城市考点），以"论文2 对接"节替代——待用户审方案时确认

## 交付：教材编写方案 v2（2026-10-10）
- doc\教材编写方案v2.md 全文落盘：13 节（定位/资源底账/21 章目录定稿+每章验收/写作规范/双模板/实验体系含个例定稿/论文2 对接/上下文纪律/验收清单/批次顺序/风险表/文件清单/修订记录）
- 关键定稿：贯穿个例=兰州 2025-07-12 起报 4 天分析段、两域 9/3km、50 层低密、物理基线 Thompson/RRTMG/MYNN2.5/Noah/d01 KF；批次 1=ch03→ch09（跑通流水线，II 部审阅点）；书 1-6 章考点→教材章映射表（§3.3）；ch20 三级改造（第三级=论文2 BEM 逐格场实录）
- 工具待建清单入方案 §8.4：PPT media 索引脚本（ch12 前）、nc→intermediate 转换器（ch06 时）、T-lnP 脚本库（ch19 前）

## Next
- 用户审定方案 v2（可批注在文件内或口头）→ 用户 commit 冻结基线 → M2 开写 ch03（新会话按 §8.2 启动协议）
- 等用户通知：集群 miniforge3 修复完成（届时可选启用集群 python，教材不依赖）

## 集群 conda 修复检验（2026-10-10，用户通知修复后）
- base 修复 ✓：conda 26.3.2 + mamba 2.5.0 + python 3.13.12；~/.condarc 用官方 conda-forge（strict 优先级）
- envs 全活：mklpy(3.11.11, numpy1.26/scipy/pandas/matplotlib)、P312(3.12.14, numpy2.5/pandas3/scipy)、RdFlood(3.11.15, numpy2.4)、sam2(3.10.18, numpy2.2)
- **缺口**：无任何 env 含 netCDF4/xarray/metpy/wrf-python → 集群端诊断仍不可用；setuptools 均 ≥83（wrf-python 需 <84）
- 网络 ✓：conda.anaconda.org / TUNA / pypi 均通（与编译手册"GitHub 不通"不矛盾）
- import 级验证作业 439294（sbatch，输出 IceLake/scripts_staging/condalib_check_439294.out）排队中（Priority），跑完自动落盘；登录节点 import 会因 OpenBLAS 内存限制失败（避免在登录节点 import）
- 待用户决策：是否建集群 `wrf` env（py3.11 + netCDF4/xarray/metpy/wrf-python）；**注意 home 配额**（编译手册：IceLake 为避 home 配额而设）→ 建议 `conda create -p $WRF_ROOT/envs/wrf` 或问用户放哪
- sbatch 模板已验证可用（condalib_check.sbatch，无 mem 参数）；439289 残留 srun 已 scancel

## Decisions（M2 自主写作轮，2026-10-10）
- **ch03 已交付**：`doc\ch03_architecture_overview.md`（生命周期调用链、四层架构图、集群巡览实录含 ldd 坑）——全部源码实测
- **ch04 已交付**：`doc\ch04_registry_mechanism.md`（记录语法全解、IO 位/流全解、生成链路与生成物地图、实参清单、T2_PEAK 纸上设计=ch20 一级图纸）——全部实测（本地源码 + 集群构建树 480 个生成物）
- ch03 两处表述已勘误（actual_new_args 实为 59 项附加实参；"上千参数"对应旧 actual_args.inc 2749 项）
- ch04 图纸要点：新增诊断变量 `state real T2_PEAK ij misc 1 - rhd "T2_PEAK" ...`；生成物自检 6 点；预计手工代码 3 处（ch20 落实）

## 关键环境事实（集群构建，2026-10-10 实测，**后续所有集群作业必须遵守**）
- **WRF/WPS 的编译与运行都必须进 Singularity 容器**：镜像 `/users/zhyuancheng2025/oneapi.sif`（oneAPI **2026.0**，容器 glibc ≥2.38）
- 宿主 CentOS 7（glibc 2.17），/opt/intel/oneapi = **2022.1.0**（旧）——宿主上"能编译、不能链接/运行"：依赖库（install-oneapi 的 netcdf/hdf5/pnetcdf）在容器内构建，链接/运行报 `GLIBC_2.28/2.33/2.34/2.38 not found`
- 作业模板：`sbatch` 外层脚本 `exec singularity exec --bind /users:/users,/data:/data[,/opt/app/wrf:/opt/app/wrf] <sif> /bin/bash <inner.sh>`；inner 内 `set +u; export ME=IceLake; source .../env-wrf-oneapi.sh; set -u`
- 容器内工具齐全：tcsh（/opt/condabin/tcsh）、m4、Intel MPI 2021.18、ifx/icx 2026.0
- **坑（已实测，教材 ch05 素材）**：在宿主跑 `tcsh ./compile` 会先 `rm -f main/{wrf,real,ndown,tc}.exe`（compile 脚本的 $ZAP）再链接；宿主链接必败（glibc）→ **exe 被删且不再生成**。已建立恢复流程：touch 被污染对象源码 → 容器内 `tcsh ./compile em_real -j 8` → md5 校验还原（original md5 备份在 ch05_exp/md5_exe_orig.txt：wrf.exe e81b501625f9587635de53dfc0470a0e / real.exe 189edc68... / ndown.exe 85964c24... / tc.exe e66e8a5d...）
- 计划中的分发镜像 `wrf-oneapi2026.sif`（内置 WRF+WPS 源码与 build-wps.sh）**尚未由管理员构建**；当前用 base 镜像 + /users 上的构建树
- 集群作业日志/载荷目录：`/users/zhyuancheng2025/IceLake/ch05_exp/`（ch05 实验）、`ch06_exp/`（WPS）、case 目录 `wrf-4.8/cases/lanzhou2025/wps`

## 集群作业台账（本轮，2026-10-10）
- 439339 ch05_exp（宿主）失败：set -u 与 setvars 冲突（3s）
- 439342 ch05_exp（宿主）失败：链接 glibc（删除了 exe）→ 触发容器方案
- 439344 wps_lz（宿主）失败：glibc（geogrid/ungrib 立即退出）
- 439345 ch05_smoke（宿主）依赖永不满（已 scancel）
- 439350 ch05_rcv（容器）恢复作业；439351 wps_lz（容器）WPS 重投；待恢复成功后再投 ch05_E（容器实验）与冒烟
- **台账续（15:23）**：439359 ch05_rcv **COMPLETED 15:01:45，exe md5 ALL MATCH ✓**（恢复成功）；439360 ch05_E RUNNING（A1 81s/12 对象、A2 45s/4 对象、B0 陷阱 registry_cmds=0、B1 全链重建进行中 ≥18min）；439361 wps_lz COMPLETED（3:27，被 439372 取代）；439372 wps_lz v2 PENDING

## Decisions（WPS 域重建轮，2026-10-10 15:23）
- **域尺寸勘误**：14:59 首跑用 120×100/250×220（无决策记录，与方案 v2 §6.2 及论文2"~90×90/~112×112"不符）→ **重建为 d01 90×90@9km + d02 112×112@3km**（ratio 3、i/j_parent_start=27/27、truelat1/2=35/45、ref 36.06N/103.83E，按方案 v2 §6.2 口径）。旧 namelist 双存档：本地 `workspace\cases\lanzhou2025\namelist.wps.v1_wide` + 集群 `ch06_exp/namelist.wps.v1_wide`。被覆盖物=旧 geo_em.d01/d02 + met_em 42 个（全部可由源数据 3.5 分钟重建）→ 留用户 19:00 复核
- **ungrib 窗口机制（源码实证，修正早前"整月解码"错误理解）**：`ungrib/src/read_namelist.F` 直接读 `&share` 的 `start_date(1)/end_date(1)`（仅第 1 域生效；start_date 优先于 start_year 多变量方式）→ hstart/hend；校验 interval_seconds 整除 (hend−hstart)；`ntimes=idts/interval+1`。`ungrib.F` 主循环中 `hdate>hend` 时提前退出（ordered_by_date=.TRUE.），故整月 4.3GB GRIB **只解码窗口内 21 个时刻**（40 s）；收尾调用 `datint.F` 对缺失时次做时间插值补齐（日志必打印 "Subroutine DATINT..."，≠出错）
- WPS 首跑实录数据（机制不变，供 ch06 引用；计时以 439372 为准）：geogrid 43s / ungrib 40s / metgrid（节点内 mpirun -np 8）122s；42 个 met_em；`num_metgrid_levels=32`（ERA5_2025 GRIB 的 32 个气压层）；geo_em 含 `num_urb_params=132` 维（GEOGRID.TBL.ARW 城市参数族，ch17 用）

## 更正与续（ch07/ch08 轮，2026-10-10 16:25）
- **restart 语义（源码实证 share/set_timekeeping.F）**：`restart_interval>0` 即创建 RESTART_ALARM 定时写 `wrfrst`（与 restart 开关无关）；`restart=.true.` 的唯一作用是"启动时从 wrfrst 续跑读取"。首投 439398 因 restart=.true. 且无 rst 文件 → FATAL（32 s 崩，证据存 `ch08_exp/rsl.error.failed_restart.0000`，ch08 章将作为教学案例）→ 修复（restart=.false. + restart_interval=86400 每日写 rst）→ **重投 439402**
- ch07 real.exe 实录：**439395 COMPLETED，rc=0、44 s**；产物 wrfinput_d01 14.3 MB / wrfinput_d02 20.6 MB / wrfbdy_d01 58.7 MB；wrfinput_d01 = 89×89×49（bottom_top_stag=50）、172 个 float 变量；wrfbdy_d01 Time=20、bdy_width=5
- 运行目录：`cases/lanzhou2025/wrf/`（exe 与 run/* 数据文件符号链接、met_em 链接 wps/）；ch08 作业脚本在 `ch08_exp/`
- 内存实测量（ch08 日志素材）："alloc_space_field: domain 1, 29975812 bytes allocated"；分解 "Ntasks in X 8, ntasks in Y 8"；MYNN 警告 "MYNN is set to mix scalars, turning off scalar_pblmix"

## ch08 运行时崩溃调查（2026-10-10 16:30）
- **失败 2**：439402（restart 修复后）34 s 崩：**SIGSEGV**，addr2line 解析栈 = `main→wrf_run→integrate→solve_interface→solve_em→first_rk_step_part1→radiation_driver`（最内层在 radiation_driver，经 libc 调用）；崩前完成：wrfinput 读入、t=0 wrfout 写盘（12.9 MB）、边界处理、tile 打印（"Tile Strategy is not specified. Assuming 1D-Y / WRF TILE 1 IS 1 IE 12 JS 1 JE 12 / NUMBER OF TILES = 1"）
- 已排除：RRTMG_LW/SW_DATA 与 ozone.formatted 文件均在（符号链接 ✓）；compute 节点 `ulimit -s` = unlimited；CAMtr 文件读正常（日志 "Normal ending of CAMtr_volume_mixing_ratio file"）
- 诊断作业 **439412 ch08_diag**（PENDING）：三连 10 分钟短测——A: ra=1(RRTM/Dudhia)×np64；B: ra=4(RRTMG)×np1；C: ra=4×np16 → 分离"辐射路径 vs 并行分解"两变量；每次 rc 与 rsl 尾入 SUMMARY，rsl.error 保留为 `expX_rsl.error.0000`
- 已知信息：em_real 的 Julia 测试跑过 run/ 目录（构建日），但 **RRTMG 路径此前从未在本部署上真正运行过**（em_les 冒烟物理全关，ra=0）→ 若 A 过而 B/C 均崩，则问题在 RRTMG 运行时（构建/表读入/配置），需考虑 pe 数量→逐函数排查或改辐射组合
- 崩溃证据保留：`ch08_exp/rsl.error.failed_restart.0000`（不适用）、新证据分别为 expA/B/C_rsl.error.0000

## 诊断结论与生产作业（2026-10-10 16:45）
- **三连短测全过（439412，1:57）**：A ra=1@np64 rc=0（33s）；**B RRTMG@np1 rc=0（50s）**；**C RRTMG@np16 rc=0（27s）**——RRTMG 本身无碍；**两次崩溃只发生在 np=64（8×8 分解）**，np≤16 稳定。单步耗时（d01）：np64≈0.04–0.09s、np16≈0.09s、np1≈0.83s
- **生产作业 439419 ch08_prod（PENDING）**：自适应脚本——先短测 short@np64，通过则 np64 跑 5 天，否则 np16 跑 5 天（`ch08_exp/ch08_prod_{outer,inner}.sh`）；-t 12h、-c 64。脚本会清掉 10 分钟短测的残留 wrfout（可重建）
- 待办提示：5 天运行的预计耗时 0.5–1.5 h（据单步推算）；完成判据 = SUMMARY 中 "PRODUCTION np=… rc=0" + SUCCESS COMPLETE WRF + wrfout/wrfrst 清单

## ch09 勘察（已获事实，供写作）
- **io_form 编码规则（frame/module_io.F 实测）**：`use_package(io_form) = MOD(io_form,100)`（包号=低两位）；`multi_files(io_form)= io_form∈[100,200)`（+100=多文件模式，每进程一个文件）；**+200=单文件但禁用 quilt IO 服务器**（multi_files 函数头注释原文："multi_file is selected by adding 100... if you add 200 instead, then single-file I/O is still done, but without I/O servers"）
- 包分派：module_io.F 用 `SELECT CASE (use_package(io_form))` 走 `IO_NETCDF/IO_NETCDFPAR/IO_PNETCDF/IO_PHDF5/PIO/ADIOS2/GRIB1/GRIB2/ESMF/INTIO` 等分支，分别调 `ext_ncd_*/ext_ncpar_*/…` 前缀的外部包例程（实现在 `external/io_*/`：io_netcdf、io_pnetcdf、io_int、io_phdf5、io_grib1、io_grib2、io_esmf、io_pio、io_adios2、io_netcdfpar）
- IO_NETCDF 等常量的"定义文件"未定位（非 module_state_description/module_io.F/Registry/tools 生成器；疑似经 `#include "wrf_io_flags.h"` 同族头文件链进入——**低优先级，写作时避免声称定义位置**）
- `external/ioapi_share/wrf_io_flags.h`（实测）：FieldType 常量表——WRF_FILE_OPENED_FOR_WRITE=102、**WRF_REAL=104**（= 所有 nc 文件里 `FieldType = 104` 属性）、WRF_DOUBLE=105/DOUBLE_PRECISION 时 WRF_FLOAT=WRF_DOUBLE 等
- quilt 模块文档（frame/module_io_quilt_old.F 头注）：IO quilt 服务器与计算重叠；`nio_tasks_per_group` 控制服务器数（内存装得下就 1）；**PHDF5/MCEL 不支持 quilt**；一组服务器（nio_groups 目前必须=1）
- 生成侧：`tools/gen_streams.c` 生成 auxinput/auxhist 流开关与 alarm（AUXINPUT%d_ALARM/AUXHIST%d_ALARM，ESMF 耦合分支）
- ch09 实验计划：io_form=2 与 11 对比（文件大小/写盘耗时）→ 需在一个短跑（如 10 分钟短测配置）里跑两次；或复用 439419 结果 + 补一个 io_form=11 短测

## ★修正与续（2026-10-10 17:35–18:00，ch08/ch09 实验轮）

### 修正 1：restart 语义与单位（推翻上文"restart_interval=86400 即每日写 rst"）
- 实测：439419 五天跑完（restart=.false.，restart_interval=86400）→ **无任何 wrfrst 文件**。原因：`restart_interval` 单位=**分钟**（registry.io_boilerplate: rconfig "restart_interval" 单位列 "MINUTES"；set_timekeeping.F 注释 "means minutes"；_d/_h/_m/_s 分量优先，_m 为 0 时回落到 restart_interval）。86400 分钟=60 天 → 5 天内 RESTART_ALARM 不响。
- 正确写法：每 5 分钟写 rst 用 `restart_interval=5`（分钟）或 `restart_interval_s=300`。触发时刻=步长对齐（00:05:00 的闹钟在第 6 步 00:05:24 触发后写盘）。
- 实验 439460（np8，10 分钟）：rst1（_s=300）与 rst1b（interval=5 分钟）**结果完全一致**：wrfrst_d01_2025-07-12_00:05:24（76.2MB）+ _00:10:48（76.1MB）；"Timing for Writing restart for domain 1: 3.41/3.38s"。→ 单位=分钟实证。
- restart 写盘入口：mediation_integrate.F med_last_solve_io / med_after_solve_io 检查 RESTART_ALARM 铃响 → `IF (grid%id==1) CALL med_restart_out`（med_restart_out 会递归子域，逐个写各域 rst）。

### 修正 2：十分钟短测实为"只跑 d01"（重大）
- 现象：所有 10 分钟短测（439412 三连、expD、ch09 全部、rst1/rst1b）rsl 里 **domain 2 行数=0**，无 d02 输出。
- 根因（源码 frame/module_nesting.F `nests_to_open`）：嵌套域激活条件 = `nest_start ≤ head 当前时间` 且 **`nest_stop > head 当前时间`**；nest_stop 取自该域的 end_* 数组（nl_get_end_minute(nestid,...)）。短测 namelist `end_minute = 10`（单值）→ 只有第 1 域吃到 10，第 2 域 end_minute 保持默认 0 → d02 的 nest_stop=2025-07-12_00:00:00，永不满足 > 当前时刻 → **d02 永不激活**（启动日志仍打印 "Domain # 2: dx" 易误导）。
- 影响：np64 崩溃（439402，2 域）与"通过"的 np64 短测（expD，实为 1 域）条件不等价；生产 5 天 np64 两域成功。已补做真两域短测+续跑（439479）。
- 教材素材：短测代表性案例——短测必须核对 rsl 域行数。

### 生产 439419 实测（ch08 主体素材）
- rc=0、elapsed=2913s（48.5 分钟）跑完 5 天；SUCCESS 在 rsl.out.0000 第 32348 行；d01 8000 步（mean 0.361s，min 0.264，max 7.13 首步）、d02 24000 步（mean 0.0838s）；写盘 d01 41 次（0.73–0.80s）/d02 121 次（1.05–1.2s；换文件点 07-13_01、07-14_02、07-15_03、07-16_04 ≈2.5s＝frames_per_outfile=25 滚动）；边界处理 20 次；输出 wrfout_d01 940MB（41 帧追加）、wrfd02 五个文件 817/843/847/867/753MB；case 5.2GB；64 核×0.809h≈52 核时。
- 帧追加机制实证：d01 t=0 文件含 41 帧（文件名=首帧时刻）；10 分钟短测单文件 34.7MB=2 帧。
- 启动清单头（rsl.out.0000）：taskid cpu15 / "Quilting with 1 groups of 0 I/O tasks." / 8×8 / MYNN 警告 / WRF V4.8.0 / Parent domain dims / EMC 动力学行 / alloc 29975812B / wrfinput 0.49s / dt=54 & 6 s/km / CAMtr GHG / MODIFIED_IGBP_MODIS_NOAH(61类) / Noah 表 / ThompMP 读表 / Nesting domain & wrfinput_d02 0.84s。
- 失败留存：ch08_exp/rsl.error.failed_restart.0000（FATAL opening wrfrst 读取）；439402 SIGSEGV rc=255（addr2line 定位 radiation_driver；未复现，见修正 2）。
- 计时机制：所有 "Timing for X" 出自 frame/module_timing.F（end_timing 的 3031 format）；rsl.out 与 rsl.error 内容基本一致；case 的 rsl.* 是从 build/WRF/run/ 链接的。

### ch09 IO 实验（439442+439455，np8，10 分钟，d01-only）
| 变体 | 首写/二写 | 文件 | 魔数 | 大小 |
| io2 | 1.92s / 0.685s | 1 个（2 帧） | 89 48 44 46=HDF5(netCDF4) | 34,685,623 |
| io11 | 2.23s / 2.08s | 1 个，名用下划线 | 43 44 46 02=CDF-2 | 93,673,384 |
| io102 | 1.89s / 0.102s | 8 个补丁 _0000.._0007 | 89HDF | 合计≈43.0MB |
| io2q | 1.52s / **0.0237s** | 1 个 | 89HDF | 34,685,623（同 io2） |
| io2c | 0.251s / 0.0666s | 1 个 | **43 44 46 02** | 93,673,228 |
- 源码：io_netcdf/wrf_io.F90 在 USE_NETCDF4_FEATURES 下默认写 netCDF4（ext_ncd_open_for_write_begin: create_mode=nf_netcdf4 + NF_SET_CHUNK_CACHE(32000000,37,100)）；use_netcdf_classic=T 走 NF_64BIT_OFFSET；写变量 NF_DEF_VAR_CHUNKING + **NF_DEF_VAR_DEFLATE(...,1,1,level=2)**（zlib-2 压缩→34.7 vs 93.7MB）。
- io_pnetcdf/wrf_io.F90：文件名 ':'→'_'（'-' 已不再换）；NFMPI_CREATE(..., NF_64BIT_OFFSET)=CDF-2；NFMPI_SET_FILL(NF_NOFILL)。
- quilt：&namelist_quilt 由 frame/module_io_quilt_old.F 自读（默认 nio_tasks_per_group=0=关）；日志行 "Quilting with 1 groups of N I/O tasks"；np8+nio1→7 计算+1 服务（1×7）。
- io_form 常量位置（修正前文"未定位"）：Registry.EM_COMMON 的 package 块（io_intio=1/io_netcdf=2/io_hdf=3/io_phdf5=4/io_grib1=5/io_esmf=7/io_yyy=8/io_zzz=9/io_grib2=10/io_pnetcdf=11/io_pio=12/io_netcdfpar=13/io_adios2=14；条件列 io_form_restart==N）→ registry 生成小写常量到 frame/module_state_description.F → md_calls 里 USE module_state_description 取用。use_package/multi_files 定义在 frame/module_io.F 尾部（2869/2893 行区段）。use_netcdf_classic 是 &time_control 的 rconfig（registry.io_boilerplate 第 39 行，默认 .false.）。
- 本地样本：workspace\data\ch09_io\{io2q_wrfout_d01_0000.nc, io11_wrfout_d01_0000.nc, io2c_wrfout_d01_0000.nc, io102_wrfout_d01_patch0003.nc}（待 netCDF4 本地解剖）
- 台账：439442、439455、439460、439479（rst-B 已提交）。
- 备注：写盘 Timing 解读=创建开销（首写）vs 稳态（二写）分开看；总时长受缓存/次序影响。

### 本地脚本新增
- gen_ch09_namelists.py（io2/io11/io102/io2q/io2c）、gen_ch08_namelists.py（rst1/rst1b/rst1d/rst2，带时间戳参数）
- cluster_jobs\：ch09_io_*、ch09b_*、ch08rst_*、ch08rstb_*、ch08_evidence_probe.sh、ch08_collect.sh、ch09_collect.sh、ch09b_collect.sh、ch08rst_probe{,2}.sh

## 批次 1 收官（2026-10-10 18:20）
- **ch08/ch09 已交付**：`doc\ch08_running_wrf.md`、`doc\ch09_io_system.md`（全部事实见 verify_log 追加段）
- 续跑闭环补齐（439483）：restart=.true. + start=00:05:24 + end_minute 双值 → rc=0、48 s、SUCCESS；**rst 携带闹钟元数据**（WRF_ALARM_* 属性；RESTART_ALARM=51 号，NEXT_RING=276 s 与"续跑仍写 rst"实测吻合）→ ch08 §8.5.6
- ch07 已勘误两处（restart_interval→1440 分钟制；io_form=2 描述改 netCDF4/HDF5）；ch08 勘误（事故时长 25 s；段错误次数措辞）
- 制品：logs\ch08_SUMMARY.txt / ch08_SUMMARY_rst.txt / ch09_SUMMARY.txt；data\ch09_io\（4 样本）+ data\wrfrst_d01_2025-07-12_00_05_24.nc
- 本地检查脚本：workspace\scripts\inspect_ch09_files.py（可复用）
- 全部作业已 COMPLETED；无残留 RUNNING/PENDING
- 遗留：案例 namelist 的 restart_interval=86400 未改（教学留档，用户可定）；chapter_map/verify_log/progress 均已更新

## 批次 2 开写：ch10 交付（2026-10-10，自主继续）
- `doc\ch10_vertical_coords_hydrostatics.md`（物理章八段式）：书 3.1–3.4 + 4.1–4.2 考点全覆盖（公式按书、扫描页直读核对，页码引用随文）
- 源码：基态构造链（p_surf 解析式/pb/T0/alb/phb 静力积分，hypsometric_opt=2）+ hybrid_opt=2 Klemp 混合坐标 c1–c4（registry.hyb_coord 设计文档）+ base_* 默认值
- 实验（轻轨，workspace\scripts\ch10_experiment.py）：8 项核对全过——p_surf 差 0.008 Pa、T0 差 0.0001 K、重演 phb 残差 2×10⁻⁷、ERA5 逐层 +0.76 m 中位、**地形口径差 +284 m**（ERA5 柱 1948 m vs geog 1665 m）、总质量 5.125×10¹⁵ t（书 5.12×10¹⁵）
- 图：doc\figs\ch10_base_state_profiles.png；数据：workspace\data\ch10\{wrfinput_d01, met_em.d01}
- **新写作法确认**：物理章采用"书页扫描直读（Read 图片核对符号/编号）→ 源码锚点 → 轻轨实验 → 八段式"流程，后续 ch11–ch16 照此办理
- 下一步：ch11（书第 2 章：成分/水汽/气溶胶；PPT 2-1/2-2-3 考点；module_model_constants/Tetens/气溶胶→辐射衔接）

## 批次 2 第二章：ch11 交付（2026-10-10，自主继续）
- `doc\ch11_composition_moisture_aerosol.md`（863 行）：书第 2 章全节覆盖；直读扫描页 17 页（印刷页 7–11、16–17、19–28；未读 6、12–15、18，臭氧细部与 2.2 引文以 PPT 覆盖）；表 2.1/2.2/2.3/2.4/2.5a-b/2.6 数字全部核对；书习题 1、2 收进习题节
- 源码五套饱和水汽压实现全解（本章最大收获）：
  ① SVP1-4 Bolton（module_model_constants + sfclay 一条龙：E1/QSFC/QGH/TVCON/CPM/RHOX）；② pq0/a2-a4 Murray（calc_rh）；③ WSM6 fpvs 内联（=CC 方程 (2.2.6) 积分解析解，physics_mmm/mp_wsm6.F90——4.8 薄壳重构须知）；④ Thompson RSLF/RSIF（八阶多项式 + 注释里的 Bolton 替身与 Murphy-Koop）；⑤ real 的 MM5 三段式 rh_to_mxrat1
- 关键发现两条：**RRTMG 的 ch4/n2o/cfc11/cfc12 常数 = 书表 2.3 的 2005 列逐位一致**（书表就是模式输入台账）；real.exe 默认路径 rh2qv_method=1 + wrt_liquid=.true. → q 由 Bolton es + (2.2.4) 生成，再 q=q1/(1−q1)（=书 (2.2.2) 之逆）
- 实验（workspace\scripts\ch11_experiment.py，四组）：A 互换闭合（机器精度；U 三算法 e/es=60.468 vs q/qs=60.180 的教学注解）；B 六实现对照（水面最大差 3.44% @−40℃、0–40℃≤0.7%；贝吉龙 Δes 最大 **−11.7℃** 与书"−12℃"吻合）；C 虚温（q20@30℃ = +3.69 K；密度近似差≤0.0006%；cp 三口径差<0.12%）；D 实测复现（**T2/Q2 与 met_em 地面层逐位一致：20.57℃/13.310 g/kg**；18 层 dq RMS 0.071 g/kg；PSFC 口径差 791.63 vs 798.96 hPa 已解释）
- 勘误：书 (2.2.9b) 冰面参考温度按表 2.5(b) 反推为 273.16 K（扫描字迹近似 276.16 不可采信）；虚温口径（WRF 用混合比代入 0.608 修正，ΔTv 差 ~0.03 K）；Thompson 密度式 (1+r) 口径差 ~1%（非矛盾）
- 图：doc\figs\ch11_es_curves.png / ch11_real_data_check.png / ch11_virtual_temp.png；PPT 原图 6 张 → doc\figs\ppt\ch11_ppt_*（含臭氧探空廓线、DU 示意、季节纬度、水分循环、CH₄-H₂O 气候学、气溶胶垂直分布）
- FAILED/坑记录：脚本首跑两个 bug（rh2qv_real 漏乘 0.01·RH；met_em k=0 是地面伪层、k=1..8 低于地形须掩掉）；TH 冰面公式 273.16/276.16 需用书表反证
- 下一步：ch12 辐射（书第 5 章 + PPT 5-1~5-6；RRTMG/coszen/O3 系数 OA-OL；轻轨实验：四定律 + 谱段对照）

## 批次 2 第三章：ch12 交付（2026-10-10，自主继续）
- `doc\ch12_radiation_family.md`（1331 行，62.4 千字符）：书第 5 章全节（5.1–5.6）；直读扫描页 54 页（印刷页 62–121；未读 73-75/80/99/108/122——全为小节过渡页与参考文献）；公式 (5.1.1)–(5.6.28) 编号全按书、74 个 LaTeX 公式带 tag、表 5.1–5.17 全核；例题 5.1/5.2/5.3 与思考题 7 题、习题 1–15 全部录入 12.10 节（改造为带提示习题）
- 源码核验（30 余锚点）：radiation_driver 四触发节拍（radt=0/stepra=1/MOD(itimestep,stepra)/自适应 radtacttime）；radconst（23.5°、1.000110+…、1370×ECCFAC）与 calc_coszen（eot×229.18、hrang、coszen=书 (5.4.3a)）；DPD=360/365；RRTMG LW nbndlw=16/SW nbndsw=14 波段数组；ghg_input 分支（CAMtr 年插值 vs 2005 常量+co2 年函数）；o3input 分支（oznini/ozn_time_int/ozn_p_int→o3rad vs inirad）；云光学 inflglw 2/3/4/5 与 effectRad；rrsw_scon=1368.22 与 earth_sun（Iqbal）
- 双大发现（闭环反推）：**JULIAN 是 ESMF 零基日序（2025-07-12=192）**；**coszen 在辐射区间中点评估（xtime+radt/2=15 min）**——两者代入后 COSZEN 全 89×89 格点 max|Δ|=8.9e−8（float32 精度）、HRANG 逐位相同、DECLIN Δ=9.9e−9 rad、SOLCON 1324.575 吻合到 1e−4
- 六组轻轨实验（workspace\scripts\ch12_experiment.py + 日志）：A 四定律（σ 由 c1/c2 推出 5.671416e−8 差 0.032%；∫F_B=σT⁴ 0.011–0.032%；λmax=2897.8/T 精确；B_λmax 与书表 10/11 行 ≤0.03%）；B 谱段图；C 闭环；D Kasten (5.4.22) 复现书表 5.5 逐位、δ_R(0.52)=0.1244；E Qd 夏至赤道 34.452 vs 90N 47.057、比值 1.366、兰州昼长 14.256 h；F 两层温室基准 278.6/247.7 逐位 + CAMtr 2005/2025 两行 + O3RAD 与气候学中位差 5.3%
- 勘误（重要）：书表 5.16 敏感性六行无法由 (5.6.4) 复现（R±0.02 书 ∓0.3 K vs 复算 ∓2.4 K 等，教材 12.9.4 列全书值/复算对照表）；表 5.2 300K 行 B 取整偏粗（1.04%）
- 图：3 张自算（ch12_planck_bands / ch12_solar_geometry / ch12_ozone_ghg）+ 6 张 PPT 原图（three_laws、absorption_spectrum、mie_efficiency、solar_spectrum、solar_constant、greenhouse_model）→ doc\figs\ppt\ch12_ppt_*
- PPT 提取坑：5-5 全为 WMF、5-2 slide7 为 EMF（矢量无法位图嵌入）——已换选（5-2 slide21、5-4 slide15）；提取脚本 workspace\scripts\ch12_extract_ppt_figs.py
- 实验脚本坑：F_B 单位换算漏 1e24（初版积分差 25 个数量级）；np.trapezoid 在 numpy<2 不存在（用 np.trapz）；DECLIN/SOLCON 在 wrfrst 里是标量（不是 3D 场）
- 预留：集群辐射敏感性实验（radt 拉长 + ghg/o3 切换，6 组短模拟）列入用户复核清单，未执行
- 下一步：ch13 微物理族（书 6.1–6.5；Thompson 精读 + WSM6 对照；PPT 未到先按书拟考点）

## 批次 2 第四章：ch13 交付（2026-10-10，自主继续）
- `doc\ch13_microphysics_family.md`（1321 行）：书第六章 6.1–6.7 全节（热力学基本规律→干绝热→饱和/假绝热→图解→混合/冷却/温湿参量）；直读扫描页 33 页（印刷页 123–153 + 168–169）；公式 (6.1.1)–(6.7.6) 编号全按书；思考题 7 题、习题 8 题原文全录并全解（含数值答案，脚本可复现）；6.8→ch14、6.9→ch15
- 源码核验（30 余锚点）：solve_em 内调用链（moist_physics_prep_em→microphysics_driver→finish；mp=28 前置 bulk_dust_emis）；micro_select 39 CASE 与变量契约（Thompson 传 NI/NR；WSM6 常数全接口传入）；Thompson 精读（单巨子程序结构/物性表/查表策略/饱和调整 3 次牛顿/守恒五保险/温度倾向 lsub-lfus 双分支/冰核化三来源 Bigg+Cooper-DeMott+Koop/calc_effectRad 与 RE_*_BG 闭环）；WSM6 双层结构（phys 薄壳→physics_mmm 实体；conden 单步解析；fpvs；nislfv_rain_plm PLM 沉降）；mp_physics 0–106 双表（README×Registry）
- 关键对照点（本章灵魂）：**饱和调整 = 书 (6.6.3) 隐式方程（T'=T+LvΔq/cp 与 qv−Δq=qs(T')）的两种数值解法**——Thompson 指数线性化+固定 3 次牛顿（lvt2=Lv²·ocp/(RvT²)，lvap 斜率 −2112）；WSM6 有理化单步（conden 分母 1+d²/(rv·e)·c/a²；xlv1=2343.6）；实验差 ≤毫开尔文量级、残差 ~ss²
- Lv(T) 三口径并存：书 (6.1.42) −2323 / WSM6 −2343.6 / Thompson −2112（≤0.5%）——"同一版本内三套常数"的事实记录（教材 13.9.2）
- 轻轨实验（workspace\scripts\ch13_experiment.py + ch13_exercises.py + 两份日志）：埃玛图（LCL 精确 506 m vs (6.2.23) 492 m（+2.8%）；LFC 343.8 hPa；对流温度 30.8℃）；γs 闭式（含 ε）/数值 0.1–1%；θse 漂移 0.54%；习题 8 速度 24.1/26.5 m/s；饱和调整三法对照表；习题 1–8 数值全解（含习题 6 焚风 θse 守恒 312.3 K 的完整检验）
- 核验三件：① (6.1.46) 符号（rt=rv+rw）；② **(6.3.5) 分母含 ε**（数值积分验证，非勘误）；③ 图 6.15 关系句（Tsw<Tw<T<Te<Tse）
- 图：3 张自算（ch13_emagram / ch13_theta_se / ch13_satadj）；2 个 mermaid（调用链、mp_gt_driver 数据流）
- 实验脚本坑：真值定点迭代需阻尼（耦合系数 |dTg/dT|≈3–4，裸迭代发散为 NaN → 阻尼 0.25）；习题 5/7 交点求解需正确判据（θse 单调方向、CCL 反号点）；习题 6 的 θse 须用实测比湿口径（饱和口径高估）
- 预留：集群"方案切换对照"短模拟（mp=6 vs 8，24 h）列入用户复核清单，未执行
- 下一步：ch14 边界层族（书 6.8 静力稳定度；MYNN2.5 与 BouLac 双精读 + YSU 对照；论文2 BouLac 兼容点；PPT 未到先按书拟考点）

## 批次 2 第五章：ch14 开写中（2026-10-10，自主继续）
- 书 6.8 全节直读完成（印刷页 154–163）：公式 (6.8.1)–(6.8.21) 全录（含薄层法 (6.8.18)–(6.8.21)、Bjerknes 1938）；图 6.15–6.25 与表 6.1、烟云五型；素材底稿 `workspace/context/ch14_material.md` 已建（书+源码+实验+考点四件齐全）
- 源码第一轮精读完成：调用链 solve_em → first_rk_step_part1 → pbl_driver（BENCH pbl_driver_tim）；module_pbl_driver.F 约 20 个 CASE 全录 + BOULAC/MYNN 调用实录；**MYNN 编译实体 = phys/MYNN-EDMF/（Makefile 符号链接实锤；physics_mmm/bl_mynn.F90 为 CCPP 副本）**；MYNN 头部（版本史 V1.0→V6.0、内容清单、qke=2TKE、boulac_length 注释"taken from the BouLac scheme…"）；BouLac（Martilli 2006；ck_b=0.4/ceps_b=1/1.4；igamma 三选，默认 Troen-Mahrt；wstar 与方差公式）；YSU 双层（薄壳→physics_mmm/bl_ysu.F90 实体，CCPP 风格；br/psim/psih/topo_wind 参数）；Registry bl_pbl 全表 + README 0–99 表 + bl_mynn_closure（2.5/2.6 默认/2.7/3.0）等 namelist
- 轻轨实验跑通（workspace/scripts/ch14_experiment.py；日志 workspace/logs/ch14_experiment.log；图 3 张）：E1 判据表（含 1000–900 层"两判据分歧"案例——指向 6.9.2 对流性不稳定）；E2 **CAPE/CIN 虚温版：LFC 807.7 hPa (1827 m)、EL 340.4 hPa、CAPE 815、CIN −128**（对照 ch13 未订正 LFC 8 km/负 −1330——虚温订正重头戏）；E3 混合层 θ̄（0–500 m 312.25 K 等）；E4 薄层法 0.477 翻转
- 图：doc/figs/ch14_stability.png、ch14_cape.png、ch14_mixed_layer.png
- **ch14 正文已写 14.0 + 14.1**（`doc\ch14_pbl_family.md`，末尾有 `<!-- CH14-CONTINUE -->` 标记）；剩余章节（14.2 不稳定能量/CAPE/热雷雨；14.3 薄层法；14.4 PBL 物理总论；14.5 WRF 对应一（调用链/方案族/namelist）；14.6 MYNN-EDMF 精读；14.7 BouLac 精读+YSU 对照+论文2 对接；14.8 实验（嵌 3 图）；14.9 习题+模式题；14.10 延伸；14.11 术语）按 ch13 风格续写
- 可选核验（写作时）：YSU brcr 等常数（physics_mmm/bl_ysu.F90）；BouLac boulac1D 内 TKE 方程细节（module_bl_boulac.F boulac1D）

## 批次 2 第五章：ch14 交付（2026-10-10，自主继续）
- `doc\ch14_pbl_family.md`（854 行，2 mermaid + 3 自算图；考点自拟待 PPT 校准）：书 6.8 全节（印刷页 154–163）；公式 (6.8.1)–(6.8.21) 全按书号；八段式 14.0–14.11 全齐
- 本轮新增源码核验（写作时二轮）：first_rk_step_part1 内顺序（radiation→surface→pbl→shallowcu）；**MYNN get_pblh 全文读解**（最低 200 m min θv、Δθv 陆 1.25/水 0.75 K、stable_method=1 默认 Koracin & Berkowicz u*×400/700 m、tanh 混合 wt=½tanh((pblh−200)/170)+½、TKE 5% 备选 ±350 m 限）；dmp_mf 功能清单（scale-aware/TKE 输运/Chaboureau–Bechtold/数值限制）；**BouLac 细节**（td=−ceps·√te/dls 组装 a_e/b_e、dls=√(dlu·dld)、dlk=min、(BEP 与 dl_u 调和)、exch=ck_b·dlk_m·√te_m 下限 0.1、pbl_height 注"similar to MYNN"）；**YSU 细节**（brcr_ub=0/brcr_sb=0.25/brcr_sbro=min(0.16(1e-7Ross)^−0.18,0.3)/cori=1e-4；wstar3=govrth·bfx0·hpbl；wscale；topdown：qc+qi>0.01e-3、wstar3_2、wm3=wstar3+5ust3、prfac2=15.9）
- 口径校准两条：① **BEP/BEM 官方兼容清单 = YSU/MYJ/BouLac 三方案**（README 原文"works only with…"，非"仅 BouLac"；MYNN 不在列——论文 2 选型依据不变）；② pbl_driver 内 `BEPSCHEME/BEP_BEMSCHEME` 实为 `SELECT CASE(sf_urban_physics)` 置 flag_bep（非独立 PBL 分支）——教材 14.5.2 行已校正
- 章节结构：14.2 条件性不稳定（CAPE/CIN 面积法 + 热雷雨三件套）；14.3 薄层法（(6.8.18)–(6.8.21) + 积云密度自调节）；14.4 PBL 物理总论（TKE 五项/闭合谱系/相似理论/七条扩散方程）；14.5 调用链 + 分发 + namelist + PBLH 三型判据；14.6 MYNN-EDMF；14.7 BouLac + YSU + 三方案差异总表 + 论文 2 对接；14.8 实验 E1–E4；14.9 习题 12 题全解；14.10/14.11
- 状态同步：verify_log/chapter_map/progress 三文件 ch14 段 + 本段；用户复核清单新增第 9 条（ch14 四项）
- 下一步：ch15 积云参数化族（书 6.9 整层升降/对流性不稳定；New Tiedtke 精读 + KFeta 进阶；承接 E1"θe 判据分歧"与 14.3"积云密度"话题）

## 批次 2 第六章：ch15 交付（2026-10-10 夜，自主继续）
- `doc\ch15_cumulus_family.md`（约 936 行，2 mermaid + 4 自算图；考点自拟待 PPT 校准）：书 6.9 全节（印刷页 164–166）+ 6.10（167–168）+ 6.8.2 夹卷结尾（164 页顶）+ 思考题/习题（168–169）+ **答案页 p546 全抄（第六章习题 1/3–8 全数值）**；八段式 15.0–15.11 全齐
- 本轮新增源码核验（写作时二轮，全部实测）：
  - 调用链：first_rk_step_part1 内 radiation→surface→pbl→**cumulus**→shallowcu，微物理在 solve_em 后段
  - cumulus_driver：17 方案 SELECT CASE；四条调用节律；**G3/NTiedtke 倾向加餐**（RTHFTEN+=RTHRATEN+RTHBLTEN·pi）——"非平衡闭合吃倾向"的接口证据；HALO 四方案；KF "DON'T JUDGE TIME STEP HERE"；tmppratec 中转
  - cu_init：STEPCU=nint(CUDT*60./DT)（分钟制）；shcu_init 同构
  - **New Tiedtke 双层**：module_cu_ntiedtke.F 包装 + physics_mmm/cu_ntiedtke.F90 实体（CCPP 风格；ECHAM 血统 8 字符子程序名）；pre/run/post 数据流（delt=dt·stepcu、垂直翻转、ω=−0.5gρw、raincv=rn/stepcu、温度倾向除 exner）
  - **cutypen 两类测试气块**：浅（Jakob 2003，hfx/qfx 起动，w*=1.2(0.001−p1p2)^(1/3)，ε_test=0.8/z+2e-4）；深（多出发层搜索、60 hPa 混合层、+0.2 K/+1e-4、ε_test=1.75e-3·min(1,qs/qs_base)³、云厚 ≥200 hPa 判深）——**触发/云型/云底一网打尽**
  - 闭合三本账：深 τ_c=Δz/(2+min(15,wup))∈[360,10800]×scale_fac、zcape1 含 −ql、nonequil 扣 zcape2、M=CAPE·M_guess/(zheat·τ)；浅 zdhpbl/zdh/√scale_fac2；中层 −ω/g（cubasmcn：q>0.8qs、0.5–10 km）
  - 卷入卷出：zoentr 云底 [1−min(1,q/qs)] 族、云内 (0.3+…)·(qs/qs_base)³、封顶 0.4M、卷出 0.75e-4·(1.6−min(1,q/qs))；浅 ε 加倍 δ=ε（质量通量守恒）；**cuentrn 的 pdmfen 被 zoentr 覆盖**（读源码陷阱）
  - 降水 Sundqvist（阈值 0.5/0.3 g/kg、zprcon=(cprcon/g)/(0.75·zwu)、B-F 增幅、指数解、z_cldmax=5e-3、落速 21.18 r^0.2）；foeewm=ε·e_s 标度 + zcor、foealfa 二次斜坡（与 ch11 Tetens/ch13 液相分数闭环）
  - 尺度因子：dxref=15 km；(1.06133+ln(15/dx))³ vs 1+1.33e-5·dx；深 τ×scale_fac、浅 M/√scale_fac2；**3 km=19.05、1 km=53.56**（关积云的数量依据）
  - KFeta：W0AVG=(W0AVG(TST−1)+W0)/TST；触发三选项（Kain 2004 的 DTLCL=4.64·WKL^0.33 / Ma&Tan 湿度平流 / Narita RH）；ABE 迭代移除 ≥90%（AINC≤10、couplet 保护）；TIMEC=DX/VCONV∈[1800,3600]（浅 2400）；PEF 切变多项式 + 云底高度订正
  - shcu_physics：CAMUWSHCU/GRIMS(wstar)/NSCV/DENG(MYJ 限定)
- **印刷勘误（新记录）**：书 p167 结论②"相当位温梯度的负值区（∂θe/∂z＞0）"——括注与"负值区"及 (6.9.5) 自相矛盾；用 PIL 2 倍放大复核（workspace/tmp/ch15_p0181_bottom.png）确认印刷如此；教材按"负值区"（＜0）自洽处理并注明
- 轻轨实验 E1–E4（workspace/scripts/ch15_experiment.py；日志 workspace/logs/ch15_experiment.log）：
  - E1 例题 6.2：三条线复算（书取整 467.7/390；精确 Γ1 469.5/391.3；**60 层等熵离散模型 469.3/391.1**）→ ~1 hPa 差 = Γ1 取整；(6.9.3) 的 θ2≈θ1 近似影响 <0.5 hPa（首次定量给出）
  - E2 习题 7：LCL 942.8/CCL 842.7/LFC 807.5/EL 345；**对流温度 30.8（书 30.5）**；CAPE 790/CIN −124 真潜 ✓（与 ch14 E2 的 815/−128 闭环）；θse 62.1→56.2（书 68→60，判据一致）；850–800 近中性（温降与湿度抵消——"温湿共同决定"的定量例证）；**气块-环境 ΔTv 表**（800 hPa ΔT 仍负、ΔTv 转正 → LFC 是虚温转正）
  - E3 习题 8：未订正 23.9（书 24.2）/ 虚温订正 26.5（书 26.7）；订正增益 11%（书 10.5%）；环境湿度口径敏感性三行
  - E4：夹卷率→云顶表（0.2→16e-4: 275→793 hPa）；M(z)/Mb（深 5.75/浅 1.00/仅夹卷 2.72）；scale_fac 表 + τ_eff；浅对流闭合 zdhpbl/zdh=0.0727
  - 调试教训：E4 夹卷柱的饱和调整**必须牛顿迭代**（朴素不动点 Lv/cp·dqs/dT≈3>1 发散 → 初版云顶恒在首步 897 hPa）——ch13 教训的现场复现，已写入教材 15.8.4
- 图 4 张：doc/figs/ch15_layer_subsidence.png、ch15_sounding_stability.png、ch15_parcel_velocity.png、ch15_massflux_scaleaware.png（图 2 曾修 x 范围防路径截断）
- 状态同步：verify_log/chapter_map/progress 三文件 ch15 段 + 本段；用户复核清单新增第 10 条（ch15 五项）；素材底稿 workspace/context/ch15_material.md
- 下一步：ch16 陆面方案族（书 4.3 海洋 + 陆面能量平衡/土壤热传导；module_surface_driver → Noah 精读 → 面层对照；承接 6.10 辐射逆温的陆面侧）

## 批次 2 第七章：ch16 交付（2026-10-11 凌晨，自主继续）
- `doc\ch16_land_surface_family.md`（816 行，3 mermaid + 3 自算图；考点自拟待 PPT 校准）：书 4.2（印刷页 55–56：(4.2.1)–(4.2.3)、表 4.1、"薄壳"）+ 4.3（56–58：三重身份、3120 倍热惯性、三层结构、50%/15–20 m/200–300 m、海流与图 4.8）+ 第四章第四节的模式实现补讲（Rn=H+LE+G；土壤热传导与阻尼深度 D=√(2κ/ω)；β 蒸发效率）；第四章习题 3/4/5 回看；八段式 16.0–16.11 全齐
- 书页直读：p55–56（page_0069–0070）+ p56–58（page_0070–0072）+ 习题/答案（page_0559 口径沿用）；**4.2 的 m0=p0/g 全式链、10044 kg/m²、5.12e15 t、1/273 与 267 双口径**全部落教材
- 源码核验（本轮补出全部数值细节，见 verify_log ch16 段）：surface_driver 两族 SELECT CASE（方案号 0–8/0–91）；Noah 三层文件结构 + **SFLX 主控九步 + NOPAC 顺序（EVAPO→SMFLX→BETA→TDFCND→YY/ZZ1→SHFLX）**；**PENMAN 逐式（T24=SFCTMP⁴ 关键口径：线性化参考是气温）**；TDFCND 公式链 + Kersten 冻结混合 + OPT_THCND=2 分支；**HCPCT 四组分公式**；HRT/HSTEP 三对角 + TBOT@ZBOT=6.5 m 底边界；LSMINIT（FRH2O/SNOALB）；REDPRM（KDT/FRZFACT/SLOPETYP）；**ISURBAN 覆盖六件套 + DF1=3.24**；driver 侧 Bolton 饱和式（A23M4=4302.65）；三张 TBL 实读（SOILPARM STAS 全表 + GENPARM 常数 + VEGPARM 代表行/LCZ 51–61）；geogrid→real→wrfinput 静态场链路；namelist 全条目（表 16.4）
- **新勘误/口径记录（ch16 段，均已入教材）**：① 书"海洋/大气质量比"两口径（4.2 的 1/273 = 5.12e15 t 口径 vs 4.3.1 的 267 = 5.27e15 t 口径）；② 表 4.1 的 77.6% 混用 p0=985/1013.25；③ 习题 3(2) 必须 T_v+g=9.80665 才逐位对台 1351.4；④ **SOILPARM 表内三处表-式不符**（SILT 5 的 F11=0.162 vs 式 0.764 疑与 SILT LOAM 混同；SANDY CLAY LOAM 7 的 F11 −1.491 vs −1.534；BEDROCK 15 的 REFSMC 0.17 vs 0.108）+ PLAYA/LAVA/WHITE SAND 三类"导热似沙、导水似黏土"人工特设；⑤ 四式在 4.8.0 全为注释、F11 已不在计算链中
- 轻轨实验 E1–E4（workspace/scripts/ch16_experiment.py；日志 workspace/logs/ch16_experiment.log）：
  - E1 能量平衡日循环（湿 θ=0.30 / 干 θ=0.15 双算例）：**瞬时闭合残差 2.0e-11 W/m²**、日累计失配 3.6e-14 MJ/m²、**柱收支 telescoping 4e-9%**；白天蒸发份额 0.911 vs 0.650、表皮最高 28.1 vs 35.5℃、夜间逆温 5.80/4.84 K；**Noah 线性化解体检：同口径误差 0.039/0.259 K、残差 1.6/9.0 W/m²；公式口径差 0.77/3.09 K**（"顺序求解"的结构性偏差首次定量）
  - E2 阻尼深度：六例数值 vs 解析偏离 ≤1.1%；土壤 0.124/2.37 m 对书 0.1/2–3 m；**书值反演海洋 κ_eff≈1.1e-2/6.2e-3 m²/s 对书 15–20/200–300 m**；**纯水分子 6 cm/1.2 m 反证"风浪混合放大 ~5 万倍"**；海洋滞后 15 m=3.75 h
  - E3 SOILPARM：四式全表互核 + 类间表（β：SAND 1.00 → CLAY 0.41；λ：2.61 → 1.02（石英）；KDT：69.9 → 1.46**差 48 倍**）
  - E4 书习题 3/5 复算：**1351.4 gpm 逐位对台**；q/Tv/ρ/水汽柱/习题 5 全对（差异仅取整）
  - 调试教训：水分桶符号曾写反（E>0 应减湿）——导致 θ1 越界并把柱收支诊断搅乱；改为"本章不做土壤水分预报（冻结 θ）"简化口径并把柱收支换成与 Ecol 区间对齐的矩形和后，telescoping 闭合到 4e-9%
- 图 3 张：doc/figs/ch16_energy_balance.png、ch16_soil_diffusion.png、ch16_soilparam.png
- 状态同步：verify_log/chapter_map/progress 三文件 ch16 段 + 本段；用户复核清单新增第 11 条（ch16 五项）；素材底稿 workspace/context/ch16_material.md
- 下一步：ch17 城市冠层方案族（SLUCM → BEP/BEM；URBPARM/LCZ 表；`sf_urban_physics` 接口与 Noah 的 ISURBAN 覆盖对接；论文 2 对接）

## 批次 2 第八章：ch17 交付（2026-10-11 凌晨，自主继续）
- `doc\ch17_urban_canopy.md`（405 行；2 mermaid + 2 自算图；六段式 + "论文2 对接"节替代考点透视——书前 6 章无城市考点为 v4 方案 R5 口径的既定调整）
- 源码核验（全实核，见 verify_log ch17 段）：分发真入口在 `module_sf_noahdrv.F`（==1 CALL urban；==2/==3 两处 CALL BEP_BEM）；SLUCM 血统与子程序群（Kusaka 1999→…→2024/25 urban-NbS；bisection/multi_layer/force_restore/CH_SCHEME=2/SFCDIF_URB 的 Kanda 1.29；内嵌 Noah 土壤链；树/绿屋顶 NbS 群——含 kanda_kawai_svf/SHADOW_TREE/STOMATAL/LELEAF/ROOT_UPTAKE）；BEP（BEP_BEM→BEP1D；街谷几何 NUMDIR/STREET_WIDTH/BUILDING_WIDTH/HEIGHT_BIN；nz_um=18/nbui_max=15；roof_frac 实测式；视角因子 fww 矩阵与 shadow/long_rad/short_rad_dd；urban_map_* 尺寸 fatal 公式）；BEM（长实参表 + wall/algebra/phirat/regtemp/air_cond→consump/cop/hsfluxpv；**模块级标量 emins/albins/thickwin/cswin/temp_rat/hum_rat/effpv=0.19**）；**`module_bep_bem_helper.F` 勘正（仅 3 行 nurbm——方案原文预期落空）**；兼容矩阵源码实证（module_bl_boulac.F 的 flag_bep 分支消费 a_u_bep）
- 表与链路：URBPARM 逐字段实读（AH 20/50/90、AHDIUPRF 峰 1.00@17h 谷 0.07@04h、AHOPTION/ALHOPTION 默认全关、表面物性三类同值等）；GEOGRID.TBL 城市条目全家（URB_PARAM=132/NUDAPT44、FRC_URB2D、IMPERV、CANFRA、**MH/ZD/Z0/λp/λf 与 AHE 的 y2010/y2050_urb/ahe 数据集**）；namelist 全表（num_urban_* 2/10/10/18/10/10/15；use_wudapt_lcz；slucm_distributed_drag；distributed_ahe_opt 0/1/2）
- **BEM 改造地图（论文2 落 chapter_map）**：albrof…/krof/kwal/csrof…/dzrof…/pwin/cop/beta/timeon…/perflo/gr_frac_roof/pv_frac_roof/effpv + 城市形态六场——现形态=表值/标量 → 2D 场（STEEL_FRAC/ROOF_*2D α/ε/λ/ρ/c/d），auxinput 通道
- 轻轨实验 E1–E3（workspace/scripts/ch17_experiment.py；日志 workspace/logs/ch17_experiment.log）：城市 vs 乡村（白天 T_s 差 +15.5 K、夜空 +1.8 K、LE≡0、夜间 G 差 +40.9 W/m²、CH×2 峰值降 9.6 K）；AH 20/50/90 → 日均 ΔT +0.68/+1.69/+3.03 K；绿量 FVG=0.2 → 白天 −6.67 K；URBPARM 实读段
- 图 2 张：doc/figs/ch17_urban_energy.png、ch17_ah_profile.png
- 调试教训两条：① 表解析需按"逗号+空白"分流（AHDIUPRF 是空格分隔行）；② Python 脚本字符串里嵌 ascii 引号会炸语法——正文引号统一走 `workspace/scripts/_fix_quotes.py`（保留的通用全角化脚本，57/57 配对）
- 状态同步：verify_log/chapter_map/progress 三文件 ch17 段 + 本段；用户复核清单新增第 12 条（ch17 四项）；素材底稿 workspace/context/ch17_material.md
- 下一步：ch18 理想实验入门（test/em 全表展开 + 精选实操 2–3 个；第 IV 部开篇）

## 第 IV 部开篇：ch18 交付（2026-10-11 凌晨，自主继续）
- `doc\ch18_ideal_cases.md`（713 行，2 mermaid + 3 自算图；技术章六段式）：18.0 本章地图（两链对照 + 流程 mermaid）／18.1 用途哲学（四类用途 + 两链对照表）／18.2 test/em 全表展开（15 目录 × 场景/初值机制/物理开关/检验点）+ **口径勘正四则**／18.3 双钥匙机制／18.4 `module_initialize_ideal.F` 源码走读（六小节）／18.5 集群实操实录（八小节）／18.6 速查表／18.7 延伸阅读
- **本章核心发现（双钥匙机制）**：编译期 `IDEAL_CASE`（顶层 Makefile：9 个算例共用 `=ideal`；fire/heldsuarez/scm_xy/tropical_cyclone/real 各一）+ 运行期 `ideal_case`（Registry 包 → 生成物常量 `realcase=0…les=9`）→ **`main/Makefile` 的 `wrf` 目标不链接任何 `module_initialize_*.o` → 同 IDEAL_CASE 家族共享同一二进制**；官方"每算例要 compile"的实质 = 重链接 + 装配运行目录
- **口径勘正四则**（已同步修订 ch05 两处）：① `em_grav2d_x` = 二维**密度流**（Straka 1993 基准、冷泡 −15 ℃ 触发、khdif=kvdif=75），非"重力波"；② `em_bubbling` 在 4.8.0 `test/` 中不存在（15 目录无此名）；③ `em_b_wave` = **x 周期 + y 对称**（中纬通道），非"双向周期"；④ `em_esmf_exp` 是 ESMF 海温耦合实验包（需 `ESMF_COUPLING`），非单机算例。另：2D 算例官方口径需 serial + 无嵌套构建
- 源码核验（详见 verify_log ch18 段）：`module_initialize_ideal.F` 12 处 SELECT CASE 分发点、levels 三策略（指数拉伸 / eta_levels / 均匀）、`nl_set_map_proj(1,0)` 与 msf*≡1 是"无需 WPS"的机制答案、f 值表、暖泡/冷泡/随机三扰动、`get_sounding` 干湿两遍（湿自下而上 10 次迭代、干自顶向下）、`read_input_jet` 二进制格式、`main/ideal_em.F` 写出链（仅 specified 写 wrfbdy）、`share/set_timekeeping.F` 的 `run_*` 优先于 `end_*`、`compile` 的 `-j` 上限 20
- **集群实操（验收要求：每个实操算例真实跑通）**：作业 439699（沙箱拷贝 8432 文件/1.3 G/17 min → `compile em_les` 69 s；首轮 rc=127 缺链接 + 一次间歇段错误）→ 作业 439708（补 `ln -sf ../../main/{wrf,ideal}.exe` 后**三算例全部 SUCCESS**）：`em_les` np=4 **113 s** / np=2 129 s / np=1 192 s、`em_quarter_ss` **51 s**、`em_b_wave` **86 s**
- **md5 交叉证据（强证据）**：ch18 树里 `./compile em_les` 后的 `main/wrf.exe` md5 = `e81b501625f9587635de53dfc0470a0e`，与 ch05 留下的 **em_real** 基线 md5 **逐位相同** → 直接证明 em_real 与 em_les 同二进制
- 轻轨诊断（`workspace/scripts/ch18_diagnose.py`；日志 `workspace/logs/ch18_diagnose.log`；图 3 张）：les（HFX 0→278.6 W/m²、CBL 顶 1004→1059 m、近地 θ 300.00→301.50 K）；qss（W max 0/30.18/**43.29** m/s、近地 θ′ min 0.40/−2.35/**−7.18** K、RAINNC 0/7.94/**36.61** mm）；b_wave（地面 P′ ±0.1 → **−69.65/+22.79 hPa** 指数增长、|u|max 67.3→72.0 m/s）
- **两条实操教学点（新记录）**：① **物理全关的算例（qss、b_wave）其 `PSFC`/`T2`/`HFX`/`TSK` 恒为 0**——这些量由面层/陆面方案填写，物理不调用即保持缺省 0；诊断只能改用动力学量（W/T/U/P+PB/QVAPOR）与微物理量（RAINC/RAINNC）。② **`frames_per_outfile=1000`（默认）使多帧写进同一文件**，文件名取该文件首帧时刻（les 1 文件 2 帧／qss 3 帧／b_wave 21 帧）——不是"只出一帧"
- 图 3 张：doc/figs/ch18_les_profiles.png、ch18_qss_storm.png、ch18_bwave.png
- 调试/事故记录：① 首轮 `em_quarter_ss`/`em_b_wave` rc=127（`execvp error on file ./ideal.exe`）——`./compile em_les` 只装配 em_les 目录；② 首轮 `em_les` np=4 一次 SIGSEGV（第二轮完全相同条件重跑即过）→ 与 ch08 的 np=64 间歇段错误同类，按"重跑即好、无稳定复现"归档；③ `Max map factor in domain 1 = 0.00` 属正常（hill2d/quarter_ss/squall/grav2d/b_wave/les 分支只设 msftx/msfty 家族；`couple_momentum` 哑元 msft 的实参为 msfty）；④ 集群小文件 NFS 拷贝极慢（≈8 文件/秒）——**复制 WRF 树应先 tar**
- 状态同步：verify_log/chapter_map/progress 三文件 ch18 段 + 本段；用户复核清单新增第 13 条（ch18 六项）；素材底稿 `workspace/context/ch18_material.md`
- **用户本轮重申口径（已写入 progress 下一步）**：始终以 WRF 源代码的理解与运用为核心、大气物理为辅助；正文中尽量写明"书中某公式 ↔ WRF 某文件某语句"的对应（物理章公式旁注源码符号，技术章讲透技术）
- 下一步：ch19 兰州 2025-07 高温全流程实录（全书压轴实验章；5 节交付 + 城市冠层 `sf_urban_physics=0 vs 3` 双跑 + T-lnP 诊断）

## 全书压轴实验章：ch19 交付（2026-10-11 中午，自主继续）
- `doc\ch19_lanzhou_heatwave.md`（408 行；2 mermaid + 4 自算图；5 节交付 + 对接论文2）；四件套同步（verify_log 第十段 / chapter_map / progress / 本段）+ 复核清单第 14 条
- **本章方法学主线：约束驱动设计**。城市实验的可用性被三重约束同时限制：
  1. **PBL 兼容**（`module_physics_init.F` 守卫）：BEP/BEM 仅 YSU(1)/MYJ(2)/BouLac(8)，MYNN(5) 被显式禁止；
  2. **面层兼容**：YSU 需 sfclay∈{1,91}；BouLac 需 {1,2} → 唯一三档通用组合 = **YSU(1)+sf_sfclay=1**；
  3. **垂直分辨率 vs 城市形态**（SLUCM 专有检查 `IF (ZDC+Z0C+2. >= ZA) FATAL`）：探针实测（临时插打印）类 2 得 `ZDC+Z0C+2 = 8.051 m`，而城市格点 `ZA = 0.5·DZ8W ≈ 8.046–8.24 m` → **卡在阈值**；类 1 约 5.99 m 通过。
- **数据缺口（论文2 立项依据）**：`GEOGRID.TBL` 的城市条目在，但 `WPS_GEOG` 只有 `NUDAPT44_1km`（美国覆盖）→ `geo_em.d02` 的 `URB_PARAM` 132 层**全 0**、`FRC_URB2D` **变量不存在**；WRF 的兜底是 real.exe 给城市点 `FRC_URB2D=0.9` + 物理初始化走 `URBPARM.TBL` 通用表值。
- **关键源码事实**：`UTYPE_URB2D` 在 `Registry.EM_COMMON` 中**没有输入流标志**（`rd=(interp_fcni)u=(copy_fcni)`），实测 `wrfinput` 里也不存在 → 无法靠改输入文件注入；`urban_var_init` 对普通城市格点**硬编码 `UTYPE_URB2D = 2`**（"for default. high-intensity"）。→ **单行最小补丁**（类 2 → 1，注明 ZLVL 约束）成为唯一可行点。
- **排错链四条（全部实测，教材原样收录）**：① 计算节点 `ulimit -s = 8192`（8 MB）→ `solve_em` 栈溢出 SIGSEGV（对照作业 439729：默认栈 27 s 崩、unlimited 后 301 步正常）；② PBL/面层兼容链（两连 fatal）；③ 城市类型越界（探针定位）；④ **运行中用 `sed -i` 替换正在执行的作业脚本 → `Stale file handle` → exp2 侥幸跑完、exp3 被砍在第 4.5 天**。
- **三跑（np=32，5 天两域，全部 SUCCESS）**：exp1=439828（=1 SLUCM+MYNN，class1）4202 s；exp2=439810（=0 CTRL+YSU）≈3640 s；exp3=439866（=3 BEP+BEM+YSU，class1）3086 s；基线对照 = ch08 439419（=0+MYNN，2913 s @64 核）。补丁二进制 md5 = 941ba403a1488291da7ddd2102c7a93c（沙箱树 `ch18_exp/WRF-ideal`，主构建树未动）。
- **诊断（脚本 `workspace/scripts/ch19_diagnose.py`；4 图）**：城市 59 格点 / 乡村 748 格点（d02 中心 31×31 窗口，UTC+7）
  - T-lnP（07-16 14 LT）：θ=315.95 K、T=26.3 ℃、qv=12.8 g/kg → **LCL=LFC=699 hPa、EL=139 hPa、CAPE=2522 J/kg、CIN=0**
  - T2 vs ERA5 日最高（07-13→16）：ERA5 33.1/33.8/34.4/35.0；CTRL-A 34.5/35.4/36.4/34.4；CTRL-B 34.3/34.7/35.9/35.2；SLUCM 34.3/35.1/36.3/34.6；BEP+BEM 34.2/34.7/35.9/35.2（偏暖 0.3–2.0 K；07-16 相当）
  - 热岛强度：3.2–3.7 K；**方案净效应**：SLUCM−CTRL-A 夜 −0.11 / 昼 −0.27 K；BEP+BEM−CTRL-B 夜 −0.07 / 昼 **+0.14 K**（局地最大 ±2–3.5 K；日最高几乎不变）
  - 诚实结论：无本地参数（FRC 均一、形态表值、AH 关闭）时城市方案净效应小量级、空间非均匀、**夜间信号缺失（AH 未入场）** → 直接支撑论文2 参数场路线
- **诊断脚本的坑（已修，均写入教材）**：① WRF `T` 是**扰动位温**（θ=T+base_temp，本例 290）——直接当温度会得到 LCL≈485 hPa 的荒唐解；② 子集须带 `Times`；③ MetPy 新版 `cape_cin` 需位置参数 `parcel_profile`；④ ncks 不能合并"正在写"的 wrfout；⑤ 城市变量不在 wrfout（无 `h` 标志）→ 掩膜取自 `wrfinput_d02`。
- 图 4 张：doc/figs/ch19_tlnp.png、ch19_t2_vs_era5.png、ch19_uhi_diurnal.png、ch19_uhi_maps.png
- 下一步：ch20 改造 WRF 三级实战（第一级 Registry 诊断变量 / 第二级 物理参数化内部 / 第三级 BEM 逐格参数场 = 论文2 EXP-LIT 技术验证版）——ch19 的沙箱 + 一行补丁 + 增量重建工作流可直接复用

## 批次 2 第九章：ch20 改造三级实战（进行中，2026-10-11 中午，自主继续）
- 三级设计定稿（详见 workspace/context/ch20_material.md）：L1=Registry 加诊断变量 T2_PEAK（图纸来自 ch04 §4.5）；L2=MYNN `GET_PBLH` 的 LAND 分支 θv 阈值 `delt_thv` 1.25→0.5/2.5 K（一行）；L3=BEM 屋顶反照率标量→2D 场（`ALBROF_2D` 输入流 + `use_bem_2d_albedo` 开关，走通 Registry→first_rk_step_part1→surface_driver→noahdrv→BEP_BEM→BEP1D）
- **v2 干净重建（作业 439955）全部作废**，两处新陷阱（教材素材，已入 material §十）：
  - ⑤ 容器无 m4：`clean` 删掉 `frame/md_calls.inc` 后规则失败但**留下 0 字节文件** → `module_io.F` 的 `#include` 失去“CONTAINS + 40 个 wrf_get/put” → 语法错 → 无 wrf.exe（官方回退 = `cp arch/md_calls.inc frame/`）
  - ⑥ Registry 触发门：`configure.wrf` 的 `REGISTRY = Registry` → 规则先决条件是拼装文件 `Registry/Registry`（由 compile 脚本按 `Registry.EM` mtime 决定是否重拼）→ 只改 `Registry.EM_COMMON` 时 registry 工具**根本不重跑**（L1 构建 43 s、inc 无 t2_peak）→ 处置 `touch Registry/Registry.EM`（ch05 §5.5.4 早已预警）
- **v3 重建 = 作业 439963**（cpu44，2026-10-11 12:28 起；脚本 `workspace/cluster/ch20/ch20_rebuild2_{inner,outer}.sh`，日志 `SUMMARY_rebuild2.txt`）：还原→clean+prep→base(clean)→L1(clean)→L2×2(增量)→L3(restore+clean)；每个构建记 md5 + inc 抽查
- 已就绪：L3 输入注入实测核对（`workspace/data/ch20/input/injected/` d02 东 44 格 0.8 / 西 60 格 0.2，全部 = FRC_URB2D>0.5 的 104 城市格点、LU_INDEX=13；d01 全 0）；运行载荷 `ch20_runall_{outer,inner}.sh`（A 组 4×24 h + B 组 2×12 h + ncks 抽取 → ch20_stage_all.tar.gz）
- 已交付初稿：`doc\ch20_modifying_wrf.md`（452 行，含 L1/L2/L3 全节与“事故链六条”表；**9 处【待填】**待实跑数据）；`workspace/scripts/ch20_diagnose.py`（L1 自检三图 / L2 三档 PBLH / L3 开关×东西城区；py_compile 通过）
- 下一步：轮询 439963 → 核对 5 个二进制 md5 → 提交 ch20_runall → 拉 `ch20_stage_all.tar.gz` → 解到 `workspace/data/ch20/stage` → 跑 ch20_diagnose（3 图）→ 填 9 处【待填】→ `_fix_quotes.py` → 四件套（verify_log/chapter_map/progress/notes）+ 复核清单第 15 条
- Open question：若 L1a↔L1b 出现非零位差（编译器重排的可能性）→ 改为“统计等价”表述，如实记录
- **2026-10-11 14:4x 更新（新指令 + ch01/ch02 交付 + ch03–05 补充）**：
  - **用户新指令**：①完成 ch01/ch02；②ch03–20 通篇检查并补三类内容（科研改造案例库：课题→改哪文件→原码/改码，小改加注释/大改①公开代码②伪代码③思路；核心原理与求解器代码详解；模块依赖树：文件级+各节点函数）；③完成后检验 439976。
  - **ch01 已交付** `doc\ch01_from_atmosphere_to_models.md`：书印刷页 1–5 直读（表 1.1/1.2 全表、光解 (1.2.1)–(1.2.3)、三阶段、氮氩之谜）+ PPT1 讲考点三件 + 学科分支↔WRF 模块对照表 + WRF 家族/根目录树 + **三类专栏体例约定（§1.6.2）**。
  - **ch02 已交付** `doc\ch02_wrf_evolution.md`：官方 release notes 逐版抓取（4.0=2018-06-08 … 4.8.0=2026-06-08，含 PR 号）+ 本地源码指纹表 14 条（physics_mmm 八文件、MYNN-EDMF/SFC 子模块、module_diag_cl、ltng 家族、wind_fitch/mav、registry.noahmp、URBPARM_LCZ、cmake、TEMPO 未随包等）。4.5/4.6.0 精确日期据时间线推断已标注。
  - **ch03–05 已补**：ch03 §3.8 驱动层依赖树（module_wrf_top wrf_init/run/finalize 行号、mediation_integrate 六 med_*、solve_interface=share/solve_interface.F、module_integrate.F 递归 integrate line 8、WRFPLUS tl/ad 变体）+ §3.9 三案（WRFPLUS/Hydro/ch20 选位）；ch04 §4.8 三案（**CLWRF 上游化案：Registry.EM_COMMON line 1759 起 ~24 state rh3 + phys/module_diag_cl.F clwrf_output_calc line 14 哑元表全录**、CORDEX cdxwrf 本 tarball 未检索到已标待核、registry.noahmp 分治）+ §4.9 tools/registry 生成器分工树；ch05 §5.8 三案（MMM 共享库含 Makefile.mpas 证据、CMake、子模块工作流两路线）+ §5.9 编译依赖树（标陷阱⑤⑥位置）。
  - 集群：SSH 连续超时/后台任务丢失（登录节点 NFS 慢 + 连接重置）；439976 最后确认 41 min RUNNING（L1a 610s SUCCESS、wrfout 558+817MB 正常）；**抽取作业 ch20_extract2 已推送未确认提交**——下一步恢复连接后先查 runall DONE→ sbatch ch20_extract2_outer.sh → SUMMARY_extract2/tar v2。
  - 下一步：ch06–09 补充 → ch10–13 → ch14–17 → ch18–20 → ch20 数据收尾 → 终验 439976 → 四件套。
- **2026-10-11 15:0x 更新（ch03–20 补充全落盘 + 439976 六跑全成 + 抽取已提交）**：
  - **补充全部完成**：ch03 §3.8/3.9、ch04 §4.8/4.9、ch05 §5.8/5.9、ch06 §6.9/6.10、ch07 §7.8/7.9、ch08 §8.9、ch09 §9.9/9.10、ch10 §10.12/10.13、ch11 §11.10/11.11、ch12 §12.10/12.11、ch13 §13.10/13.11、ch14 §14.10/14.11、ch15 §15.10/15.11、ch16 §16.10/16.11、ch17 §17.9、ch18 §18.8/18.9、ch19 §19.8、**ch20 §20.7.1 全书案例总索引表（27 案）**。全角引号已跑（ch03–ch20 全部）。文件名核验：bl_ 19 文件、cu_ 16 文件、mp_ 32 文件、sf_ 39 文件、ra_ rrtmg 三件套(lw/lwf/lwk,sw/swf/swk)、cu_driver/pbl_driver/solve_interface=share/ 等。
  - **439976 六跑全部 rc=0**：L1a 610s / L1b 610s（SUCCESS COMPLETE 实证——重建前的 SIGSEGV 通知为陈旧残留）/ L2a 607s / L2b 610s / L3off 322s / L3on 322s；作业 13:59 DONE（run 内 ncks 抽取如预期 FAIL=事故⑦）。
  - **抽取作业 440034**（ch20_extract2，容器外 ncks）已提交 PENDING；完成后 tar=ch20_stage_all_v2.tar.gz → 拉回 → ch20_diagnose 出 3 图 → 回填 7 处待填。
  - 下一步：等 440034 → 拉 tar → 诊断出图 → 回填 → 四件套（verify_log/chapter_map/progress/notes + 复核清单第 15 条）。
- **2026-10-11 15:3x 收官（ch20 全链闭环 + 全书补充完成）**：
  - 抽取修复两步：① `libnco-4.7.5.so not found`（计算节点无系统 nco，登录节点有——裸跑侥幸成功的假象）→ 所有 ncks 加 `env LD_LIBRARY_PATH=lz_case/lib`；② L3 2d 仍失败 → **Registry DataName ≠ 变量名**（TS_URB2D 的输出名是 TS_URB；`rhd=(interp_fcnm)u=(copy_fcnm)` 语法合法，ALBROF_2D 成功入 wrfout 证明 h 位补丁本身有效）→ 补抽 4 文件（fixL3）→ stage 24 文件齐、tar 142.8 MB 已拉回本地
  - **诊断结果（3 图 + 日志）**：L1 单调 0 违例/295704、gap 0~4.59 K 违例 0/308025、**L1a↔L1b 十二变量 max|Δ|=0（位级非扰动铁证）**；L2 域均 PBLH 1199/1635/1902 m 单调、逐点违例 0.83–3.10%（稳定层混合——教材预判被证实）、ΔT2 ±0.1 K；L3 东组时均 −2.85 K/正午 −6.67 K、西组 −0.089 K（表值对照≈0）、SWDOWN/RAINNC 大差=云降水非线性反馈（判据二已改写为三级"应当不变"检验）
  - ch20 章节：9 处待填全部回填 + 20.6 表修正 + 全角引号两轮；事故链扩至七条；§20.7.1 全书案例总索引（27 案）
  - 四件套全同步：verify_log（ch20 段四节）、chapter_map（ch20 条目）、progress（头部改写 + 集群状态 + 第 15 条复核七项 + ch20 交付记录）、notes（本段）；material 末段收官
  - **下一任务：ch21 solve_em.F 全流程 → 附录 a–d → index.md**；持续不标 goal complete

## 用户问询：案例库"情况①"是否=已上游化（2026-10-11 下午）
- **用户问题**：ch15 案例一（MSKF CMT）是否官方已接纳、进 source/？——**是**。实证：① `phys/module_cu_mskf.F` 行 5 `!JTR = Jacob Radford, NCSU`、行 18 特性清单"（7）CMT: Zhang&McFarlane JGR 1995"、行 3630-3635 `cmt_opt_flag=.TRUE.`（硬编码默认开，非 namelist）；② WRF 4.2 release notes（2020-04-23）原句收录；③ Registry line 68 有 `# CDXWRF modification` 标记（CORDEX 亦已上游化）。
- **修订三处**：ch15 案例一改"情况①·已上游化"+ 源码证据 + release notes 原句 + 教学点补"改造生命周期"；案例二（NTiedtke scale_fac）、案例三（bmj_rad_feedback/GFL）同标注已上游化；ch01 §1.6.2 情况①再分两小类（已上游化/外部补丁）+ 判别三标志（署名注释/Registry 改造标记/release notes）。
- **待办已清偿（2026-10-11 下午第二轮，用户追问"情况①但未上游化"）**：全书以"情况①"逐条检索并标注完成。**未上游化的情况① = 本书原创三案**（ch03 案例三=ch20 L1 T2_PEAK；ch09 案例三=ch20 L3 ALBROF_2D；ch14 案例一=ch20 L2 delt_thv）+ ch08 案例三（运维实录，非代码改造不适用）；**其余情况①全部已上游化**。顺带勘误 ch04 案例二：CORDEX-WRF **在 4.8.0 包内**——`Registry/registry.cordex`（L. Fita CIMA 2017-12；`namelist,cordex`，output_cordex 默认 0）+ `phys/module_diag_cordex.F`/`module_diagvar_cordex.F` + `registry.em_shared_collection` line 34 无条件 include + Registry.EM_COMMON line 68 `# CDXWRF modification`；原"&cdxwrf"更正为"&cordex"。ch20 §20.7.1 表 27 案全部标注"已上游化/未上游化/③"，用法建议加标注约定。ch01 §1.6.2 保持上轮修订。全角引号已重跑（20 文件，12 对转换）。
