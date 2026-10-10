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
