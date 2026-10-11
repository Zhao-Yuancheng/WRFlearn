# 附录 A　符号与物理常数对照

> **三张表的用法**：本附录是全书的“符号公证处”——正文中每当你怀疑“书里的 $\theta$ 对应代码里哪个名字”，来这里查。三列约定：**书符号**（《大气物理学》第 2 版）/ **WRF 代码符号**（源码变量，标出定义文件）/ **输出与 Registry 名**（wrfout 变量名或 Registry 记录名）。表 a.2 的常数全部以 `share/module_model_constants.F` 原文为准（写作时逐行 Read 核对）；与书附录 C 的差异逐条给出相对偏差，来源为 ch11 §11.4.1 的实测核对（`workspace/scripts/ch11_experiment.py`）。

## a.1　总约定

| 约定 | 内容 |
|---|---|
| 气压 | 书与正文用 hPa；WRF 内部状态为 Pa（`p1000mb=100000.`），wrfout 输出 PB/P 亦是 Pa——画图时换算 |
| 比湿/混合比 | 模式**只存混合比**（kg kg⁻¹）；wrfout 的 `QVAPOR` 就是 $r$；比湿需 $q=r/(1+r)$ 自行换算（ch11 §11.4.2） |
| 温度 | wrfout 的 `T` 是**扰动位温**（$T=\theta-T_0'$，$T_0'$ 见 wrfinput 属性，ch19 的教训）；诊断气温用 $\theta\,(p/p_0)^{R_d/c_p}$ |
| 底层顺序 | k=1 为最低层（书与模式一致）；`znu/znw` 自上而下递减 |
| 时间 | 模式内 UTC；本教材分析用 UTC+7（ch19 口径） |

## a.2　物理常数对照表：书附录 C ↔ `module_model_constants.F`

| 书符号（书值） | WRF 符号 | 源码值（4.8.0 实测） | 相对偏差 | 用途（首现章） |
|---|---|---|---|---|
| $g=9.80665\ \mathrm{m\,s^{-2}}$ | `g` | 9.81 | 0.034% | 重力（ch10 习题口径：逐位复算需用书值 9.80665） |
| $M_d=28.9644\ \mathrm{g\,mol^{-1}}$ | `mwdry` | 28.966 | 0.006% | 干空气摩尔质量 |
| $R_d=287.05\ \mathrm{J\,kg^{-1}K^{-1}}$ | `r_d` | 287. | 0.017% | 干空气气体常数 |
| $c_{pd}=1004$ | `cp` | 7·r_d/2 = 1004.5 | 0.05% | 定压比热 |
| $c_{vd}=717$ | `cv` | cp−r_d = 717.5 | 0.07% | 定容比热 |
| $R_v=461.5$（由 ε 反推） | `r_v` | 461.6 | 0.02% | 水汽气体常数 |
| $c_{pv}$（≈1846.4） | `cpv` | 4·r_v = 1846.4 | — | 水汽定压比热（书 (2.2.21)） |
| $\varepsilon=0.622$ | `EP_2` | r_d/r_v = 0.622 | — | 混合比换算（书 (2.2.4)） |
| 0.608（虚温系数） | `EP_1`（=`p608`） | r_v/r_d−1 = 0.608 | — | 虚温（书 (2.2.20)、(6.1.46)） |
| $e_s(0\,℃)=6.1078\ \mathrm{hPa}$ | `psat` | 610.78 Pa | — | Tetens 前端常数 |
| Tetens/Bolton 常数 | `SVP1/SVP2/SVP3/SVPT0` | 0.6112（kPa!）/17.67/29.65 K/273.15 K | — | 饱和水汽压（书 (2.2.11)；SVP1 单位是 kPa） |
| Murray 式常数 | `pq0/a2/a3/a4` | 379.90516/17.2693882/273.16/35.86 | — | 饱和混合比（书 (2.2.9a) 系） |
| Magnus 式常数 | `cm1/cm2/cm3` | 2937.4/4.9283/23.5518 | — | 马格纳斯式（书 (2.2.8a) 系） |
| $L_v=2.5\times10^6$ | `XLV` | 2.5E6 | — | 凝结潜热（0 ℃） |
| $L_s=2.85\times10^6$ | `XLS` | 2.85E6 | — | 升华潜热 |
| $L_f=3.5\times10^5$ | `XLF` | 3.50E5 | — | 融解潜热 |
| $L(T)=A-BT$ 线性化 | `XLV0/XLV1/XLS0/XLS1` | 3.15E6/2370/2.905E6/259.532 | — | 温度修正潜热（Lv(T) 三口径之一，ch13 §13.9.2） |
| $\rho_w=1000$ | `rhowater` | 1000 | — | 液水密度 |
| $\rho_{snow}=100$ | `rhosnow` | 100 | — | 雪密度 |
| $\sigma=5.67\times10^{-8}$ | `STBOLT` | 5.67051E-8 | 0.009% | 斯特藩–玻尔兹曼常数（ch12） |
| κ≈0.4 | `KARMAN` | 0.4 | — | 冯·卡门常数（ch14） |
| $\Omega=7.292\times10^{-5}$ | `EOMEG` | 7.2921E-5 | — | 地转角速度（书第 7 章 f） |
| $R_{\oplus}=6370\ \mathrm{km}$ | `reradius`（倒数） | 1/6370.0e3 | — | 地球半径（ch12 太阳几何） |
| 黄赤交角 23.5° | `OBLIQUITY` | 23.5 | — | 赤纬公式（书 (5.4.1) 系） |
| 偏心率 ≈0.0167 | `ECCENTRICITY` | 0.014 | — | 日地距离订正（书 (5.4.2) 的 1.000110 族在 radconst 内） |
| 1 年 = 365 d | `PLANET_YEAR` | 365 | — | `DPD=360/365` 赤经日变（ch12） |

> **使用纪律**：写代码/脚本一律用**源码值**；与书对照时按本表换算（偏差 ≤0.07%）。“复现实验对不上数”的第一排查项就是常数口径（ch16 习题 3 的 9.80665 陷阱即此）。

## a.3　热力学与湿度变量

| 书符号（含义） | WRF 代码符号 | 输出名/Registry 名 | 备注 |
|---|---|---|---|
| $T$（气温） | `t_phy`（物理诊断） | `T`（wrfout=扰动位温）+ `P`/`PB` | 气温须由位温换算（phys 驱动内做） |
| $\theta$（位温） | `t_2/t_1`（状态）、`th_phy` | `T`（+base） | 湿位温口径见 `use_theta_m`（ch21 §21.1.3） |
| $\theta_v$（虚位温） | `thv`（各方案内） | — | $\theta_v=\theta(1+0.608q_v-q_c-q_i)$（ch20 §20.4） |
| $T_v$（虚温） | `tvm`/`TVP` | — | ch11 §11.6 C 组 |
| $e$（水汽压） | `E`（diag_functions） | — | ch11 五套饱和实现 |
| $e_s$（饱和水汽压） | `es`（各处局部量） | — | SVP1–4 / pq0 / fpvs / RSLF |
| $T_d$（露点） | `TD`（diag） | `TD2` | 2 m 露点 |
| $r$/q（混合比） | `qv`（moist 分量） | `QVAPOR` | Registry: state real qv ikjftb moist |
| $q_c$（云水） | `qc` | `QCLOUD` | 同上 |
| $q_r$（雨水） | `qr` | `QRAIN` | 同上 |
| $q_i$（云冰） | `qi` | `QICE` | 同上 |
| $q_s$（雪） | `qs` | `QSNOW` | 同上 |
| $q_g$（霰） | `qg` | `QGRAUP` | 同上 |
| $U$（相对湿度） | `rh`（diag/calc_rh） | `RH` | 计算途径见 ch11 §11.5.2 |
| $\rho_v$（绝对湿度） | 无（换算量） | — | $\rho_v=e/(R_vT)$ |
| $\rho$（湿空气密度） | `rho`/`alt`(=1/ρ 全量) | `ALT`、`AL`（扰动） | 状态方程回代（ch21 §21.3.4） |
| $p$（气压） | `p + pb` | `P`/`PB`（Pa） | `pb`=基态（real 构造，ch07） |
| $\theta_{se}$（假相当位温） | 无（诊断计算） | — | ch13/ch15 实验 |

## a.4　动力学变量（ch21）

| 书/ADT 符号（含义） | WRF 代码符号 | 输出名 | 备注 |
|---|---|---|---|
| $\mu$（干空气质量柱） | `mu_1/mu_2`、`mub`、`mut` | `MU`/`MUB` | `mut=mub+mu`；`muu/muv` 速度点 |
| $\dot\eta$（η 面通量） | `ww`（μ 耦合） | `WW` | ≠ 垂直速度；垂直速度是 `w_2`（输出 `W`） |
| $u,v,w$（速度） | `u_2/v_2/w_2`（+通量 `ru/rv/rw`） | `U/V/W` | `ru=μ·m·u` 型耦合 |
| $\phi,\phi_b$（位势） | `ph_2/phb` | `PH/PHB` | `php` 扰动半层量 |
| η（坐标面） | `znu/znw` + `c1h…c4f` | — | hybrid_opt=2（ch10 §10.12） |
| 地图因子 $m$ | `msftx/msfty/msfux/...` | `MAPFAC_M` 等 | ch21 §21.1.3 |
| 科氏参数 $f$ | `f`（+`e`、`sina/cosa` 曲率族） | — | ch21 §21.2.9 |
| 湍流系数 $K_m/K_h$ | `xkmh/xkhh/xkmv/xkhv` | — | ch14/ch21 §21.4.4 |
| TKE | `tke_1/tke_2` | `TKE`（PBL 方案产出） | qke=2e（ch14） |
| PBL 高度 | `pblh` | `PBLH` | 三型判据（ch14 §14.5.5） |
| 2 m 诊断 | `t2/q2/u10/v10` | `T2/Q2/U10/V10` | 面层方案填（物理全关=0，ch18） |

## a.5　陆面、城市与辐射接口量

| 书符号（含义） | WRF 代码符号 | 输出名/表字段 | 备注 |
|---|---|---|---|
| $R_n$（净辐射） | `radflux`（Noah 内）/`SWDOWN+GLW` | `SWDOWN/GLW` | ch16 (16.1)、ch17 BEM 语句 |
| $H$（感热） | `hfx`/`SHEAT` | `HFX` | |
| $LE$（潜热） | `qfx×L_v`/`ETA` | `LH` | |
| $G$（地热通量） | `ssoil` | `GRDFLX` | 向下为正 |
| $T_s$（皮肤温度） | `tsk/t1` | `TSK` | |
| $\alpha,\varepsilon$（反照率/发射率） | `albbck/alb`、`emiss` | `ALBEDO/EMISS`；URBPARM `ALBR/EPSR` | ch17 改造地图 |
| 土壤温度/湿度 | `tslb/SMOIS` | `TSLB/SMOIL` | 四层（Noah） |
| 城市分数 | `frc_urb2d` | `FRC_URB2D`（无 h 流，ch19） | |
| 建筑形态 | `mh_urb2d/zd_urb2d/λp/λf` | `MH_URB2D/ZD_URB2D/...` | GEOGRID.TBL 城市条目 |
| 人为热 | `akhs_ah`（表 `AH`） | URBPARM `AH/AHDIUPRF` | ch17 §17.2.3 |
| 云光学有效半径 | `re_cloud…`（driver 内） | `RE_CLOUD/RE_ICE/RE_SNOW` | ch12/ch13 接口 |
| 臭氧/温室气体 | `o3rad`、CAMtr 读入 | — | ghg_input/o3input（ch12） |

## a.6　本章（附录）维护说明

- 本表随全书 21 章“已核验”锚点生成；后续若 WRF 版本升级，先跑 `module_model_constants.F` 的重读，再对照 ch11 §11.6 的实验脚本回归。
- 常数差异的判定方法（书值 vs 源码值）与三组实测量化，见 ch11 §11.4.1 与 `workspace/logs/ch11_experiment.log`。
