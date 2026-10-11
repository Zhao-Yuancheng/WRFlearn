# 附录 C　常见错误速查（运行期扩编版）

> **定位**：编译期问题的系统版在配套《WRF 编译手册（oneAPI 2026）》速查章（本书 ch05 只收编译体系机制性条目）；本附录把全书各章随见随收的**运行期/数据期/改造期**问题汇成一张总表，每条注明“详见章号”以便回到语境。所有条目都出自本教材的实录（作业号与日志在 verify_log 留痕），非二手抄录。

## c.0　万能诊断流程（先背这五步）

```text
1. tail -n 100 rsl.error.0000     ← 90% 的答案在这里（FATAL CALLED 上下文）
2. grep -c "Timing for main" rsl.out.0000   ← 崩在哪个时间步
3. grep "domain" rsl.out.0000 | sort | uniq -c   ← 每个域都动了吗（短测代表性！ch08 §8.6）
4. 作业层：sacct -j <id> 看退出码；ulimit -s unlimited 是否写了
5. 隔离变量：一次只改一处，做三连短测（ch08 §8.6.2）
```

## c.1　编译期（机制性；环境细节见编译手册）

| 症状 | 根因 | 处理 | 详见 |
|---|---|---|---|
| 新增 Registry 变量“编进去了”但生成物没有 | `Registry/Registry` 拼装文件未刷新，`tools/registry` 没重跑 | `touch Registry/Registry.EM` 后重编；`grep` 生成物确认 | ch05 §5.5.4、ch20 事故⑥ |
| 编译失败后 `main/*.exe` 消失 | `compile` 的 `$ZAP` 先删后建 | 修复后重编即恢复；平时备份 exe | ch05 §5.5、notes 2026-10-10 |
| 链接报 `GLIBC_2.xx not found` | 编译环境 ≠ 链接/运行环境（容器 vs 宿主） | 编译、链接、运行全程同一容器 | ch05、编译手册 |
| `tcsh: not found` | compile 是 tcsh 脚本 | 容器内自带 tcsh | ch05、编译手册 |
| 干净重建后无 wrf.exe + `module_io.f90` 语法错 | 容器缺 `m4`，`md_calls.inc` 规则留下 0 字节文件 | `cp arch/md_calls.inc frame/`（时间戳保持新） | ch20 事故⑤ |
| `You set the number of processors above 20` | `./compile -j` 只认 2–20 | 用 `-j 8/12/16` | ch05 §5.3 |
| cmake 版产物找不到 | 产物无 `.exe` 后缀，在 `install/bin/wrf` | 按 cmake 文档目录走 | ch05 §5.4 |
| 链接 `undefined reference`（毫不相干符号） | 某库编译失败被 `make -i` 的 `(ignored)` 掩盖 | `grep “error #\|undefined reference” compile.log`；查库完整性 | ch20 事故④ |

## c.2　WPS 期（ch06）

| 症状 | 根因 | 处理 | 详见 |
|---|---|---|---|
| `Could not open file METGRID.TBL` | 表不在运行目录 | 软链 `METGRID.TBL.ARW` + `opt_metgrid_tbl_path='./'` | ch06 §6.5 |
| `mandatory field TT was not found` | Vtable 不配 / GRIBFILE 未链 / 窗口不重叠 | 三查：Vtable、`ls GRIBFILE.*`、&share 窗口 | ch06 §6.4 |
| `link_grib.csh cannot execute` | 缺 tcsh | 容器内运行 | ch06 |
| ungrib 只解码部分时刻 | 窗口机制（正常行为） | 扩 &share 窗口即得全量 | ch06 §6.4.3 |
| 日志出现 `DATINT: Interpolating…` | 恒打印的流程通告（非错误） | 若其后有真实插值行，说明 GRIB 缺时次 | ch06 §6.4.4 |
| geo_em 城市字段全零/缺失 | geog 数据无 NUDAPT 等境外覆盖 | 正常回退；要真实形态需自建参数场 | ch17/ch19 |

## c.3　real.exe 期（ch07）

| 症状 | 根因 | 处理 | 详见 |
|---|---|---|---|
| `error opening wrfrst_d0N_…` + `RESTART run` | `restart=.true.` 被误当“输出开关” | 新起报设 `.false.` | ch07 §7.2.1、ch08 事故① |
| 维度不符（e_we/e_sn） | namelist 与 met_em 不同步 | 逐项对齐 | ch07 |
| `eta_levels` 报错 | 个数 ≠ e_vert 或非单调 | 重生成层表 | ch07 §7.2.2 |
| `p_top_requested` 报错 | 顶压低于驱动数据最高层 | 调大（如 5000 Pa） | ch07 |
| `interval_seconds` 不一致 | 两套 namelist 忘同步 | 保持 21600 | ch07 |
| 方案组合 fatal（PBL/面层/城市） | 兼容矩阵不满足 | BEP/BEM 仅 YSU/MYJ/BouLac + 指定面层 | ch19 §19.5、ch14 |

## c.4　wrf.exe 运行期（ch08 + ch18/ch19）

| 症状 | 根因 | 处理 | 详见 |
|---|---|---|---|
| FATAL `error opening wrfinput_*` | 文件缺/域号/时刻不匹配 | 核对文件名与 start_* | ch08 §8.7 |
| 25–34 s 秒退（RESTART 字样） | 同 c.3 第一条 | `restart=.false.` | ch08 §8.5.2 |
| **没有 wrfrst** | `restart_interval` 单位是**分钟**（86400=60 天） | 分钟制或 `_d/_h/_m/_s` 分量制 | ch08 §8.5.3 |
| **某个域完全没动** | `end_minute` 等写了单值（只填第 1 域） | `end_*` 按域写全；grep 域行数自检 | ch08 §8.6.3 |
| 跑 30 s 内全灭、SIGSEGV、与 np 无关 | 计算节点 `ulimit -s` 8 MB 爆栈 | 作业脚本 `ulimit -s unlimited` | ch19 §19.3 |
| 高核数偶发段错误（未复现） | 内存布局偶发越界 | 存证（rc/栈/日志）→ 重投 + 回退核数自适应 | ch08 §8.6 |
| 跑完没 wrfout | history_interval/帧设置；或长度小于首个输出间隔 | 查 `Timing for Writing` 行 | ch08 §8.7 |
| 磁盘爆 | 输出体量估算失误 | 口诀预估 + `frames_per_outfile` 切小 | ch08 §8.4 |
| `wrfout` 只有一帧 | `frames_per_outfile=1000` 默认多帧同文件 | 正常；用 `Times` 索引帧 | ch18 §18.5.7 |
| `PSFC/T2/HFX/TSK` 恒为 0 | 物理全关（面层/陆面未启用） | 诊断改用动力学量 | ch18 §18.5.7 |
| rc=127 `execvp error on ./ideal.exe` | `./compile em_xx` 只装配了 xx 目录 | `ln -sf ../../main/{ideal,wrf}.exe .` | ch18 §18.5.6 |
| `Need to choose valid non-zero ideal_case` | 缺 `&ideal ideal_case=N` | 补段 | ch18 §18.6 |
| 二维算例 dmpar 下异常 | 官方要求 2D 用 serial + 无嵌套构建 | 按 ch18 附注构建 | ch18 §18.2.2 |

## c.5　IO 期（ch09）

| 症状 | 根因 | 处理 | 详见 |
|---|---|---|---|
| 读回多文件产物维度错 | io_form=10x 每进程一文件 | 同进程数读或改单文件 | ch09 §9.3 |
| 找不到 PnetCDF 输出 | 文件名 `:`→`_` | 通配匹配 | ch09 §9.3 |
| wrfout 突然大 2–3 倍 | `use_netcdf_classic` 打开（无压缩） | 按需取舍 | ch09 §9.3.1 |
| 开 quilt 后计算域变小 | mpirun -np 没算服务器进程 | 总数=计算+服务器 | ch09 §9.4 |
| 辅助流不产出 | 三件套没配齐（interval/frames/io_form） | 全配 | ch09 §9.5 |
| PHDF5 + quilt 报错 | 不支持 | 二选一 | ch09 §9.4 |

## c.6　内核数值期（ch21）

| 症状 | 根因 | 处理 | 详见 |
|---|---|---|---|
| `leapfrog removed, error exit` | `rk_ord` 设为 1 | 改回 3 | ch21 §21.2.5 |
| 数步内 NaN/爆掉 | dt 过大；`time_step_sound` 手动过小 | 自动（=0）；`w_damping=1`；自适应时步 | ch21 §21.7 |
| 湿度负值/数浓度异常 | 平流选项非正定 | `moist_adv_opt` 正定族 | ch21 §21.4.2 |
| 高纬棋盘噪声 | 极区滤波未开 | `polar=.true.` + `fft_filter_lat` | ch21 §21.4.3 |
| 低层被阻尼 | `zdamp` 过深 | ≤5000 m | ch21 §21.4.3 |
| 边界反射波 | spec/relax 区太窄 | 加大 `spec_bdy_width` | ch21 §21.5 |

## c.7　改造期事故链（ch20 §20.5 全表浓缩）

| # | 一句话根因 | 铁律 |
|---|---|---|
| ① | `LD_LIBRARY_PATH` 全局 export 污染（GLIBC_2.34 not found） | 环境变量最小作用域（`env LD_LIBRARY_PATH=… cmd`） |
| ② | 补丁锚点命中 2 处（重复语句） | 多行锚点 + 断言唯一 |
| ③ | Registry 改动 + 增量编译 → 688/914 个旧 `.o` 按旧布局访问 `grid%` 必崩 | 碰 Registry 默认干净重建；`find -newermt` 查旧对象 |
| ④ | 加非可选哑元漏了 Noah-MP 调用点 | 加形参前 grep 全部调用点；`OPTIONAL + PRESENT` |
| ⑤ | 容器缺 m4 → 0 字节 `md_calls.inc` | clean 后清点工具（m4/tcsh）；`(ignored)` 是真错误 |
| ⑥ | 只改 `Registry.EM_COMMON` → registry 工具根本没重跑 | `touch Registry/Registry.EM`；验证生成物而非返回码 |
| ⑦ | 容器内 ncks 静默失败 + stderr 被吞 | 后处理 stderr 落盘；复用已成功过的环境 |

**改造检查单（8 条）**：定位（grep 全树数调用点）→ 备份（`.orig_`）→ 代价档（Registry？touch+重建）→ 清点环境 → 先验生成物再验 md5 → 单变量对照 + “应当不变”位级核验 → 产物带 md5 入档 → 后处理 stderr 落盘。

## c.8　数据与后处理

| 症状 | 根因 | 处理 | 详见 |
|---|---|---|---|
| ncks 合并“正在写”的 wrfout 得空文件 | 输入含未关闭文件 | 排除最新一个 | ch19 §19.7 |
| 计算节点 ncks 报 `libnco-*.so not found` | 计算节点无 NCO 库 | `env LD_LIBRARY_PATH=<lib> ncks …` 或在登录节点跑 | ch20 §20.5 |
| 抽取的变量不存在 | **Registry DataName ≠ 变量名**（如 `TS_URB2D` 输出名 `TS_URB`） | 用 wrfout 里实际名字 | ch20 事故⑦ |
| `ncl`/python 读 `T` 得到荒唐温度 | `T` 是扰动位温（需 +base 或换算） | 读 wrfinput `T00`/属性或按 a.3 换算 | ch19 §19.4 |
| MetPy `cape_cin` 报错 | 新版需位置参数 `parcel_profile` | 按新版签名调用 | ch19 §19.4 |

## c.9　兼容性守门员（组合纪律）

1. `sf_urban_physics=2/3` ⇔ `bl_pbl_physics ∈ {1(YSU), 2(MYJ), 8(BouLac)}`（`module_physics_init.F` 守卫；MYNN 明确不允许）——ch14/ch19；
2. BouLac/MRF ⇔ `sf_sfclay_physics ∈ {1,2}`；YSU ⇔ {1,91}——ch19 三重约束链；
3. `sf_urban_physics>0` 仅 Noah 与 Noah-MP 支持——ch17 §17.5；
4. `num_soil_layers=4`（Noah 硬约束）、`num_land_cat` 与 TBL 一致——ch16 §16.4.4；
5. WENO 标量选项下更新推迟到最后一个 RK 步——ch21 §21.2.12；
6. `cu_rad_feedback` 需 `cu_diag=1` 且方案支持（GF/G3/GD/KF）——ch15 §15.5.4。
