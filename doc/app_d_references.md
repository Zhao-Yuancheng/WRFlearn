# 附录 D　参考文献与数据源清单

> **分级标记**（与全书事实核验协议一致，方案 v2 §4.1）：
> 【核验】= 写作当次经源码头注、官方 release notes 或网络检索证实（`workspace/context/verify_log.md` 有痕）；
> 【通行】= 领域标准文献，条目本身可靠，但页码/卷期未逐字核对，引用前请自行复核；
> 【线索】= 仅作检索起点，未核验（多为博客/项目页），**不得直接写进论文**。

## d.1　教材底本

- 盛裴轩、毛节泰、李建国等：《大气物理学》（第 2 版），北京大学出版社，2013。——全书物理底本；印刷页 N 的扫描件位于 `AtmosphericPhysics\book\page_{N+14}.jpg`（换算规则见 index.md）；各章引用均带印刷页码。【核验：全书直读】

## d.2　WRF 官方文档与版本

- WRF Model User's Guide（各版，UCAR/NCAR）：`&dynamics`/`&physics` 各 namelist 项的官方释义；源码内 `run/README.namelist` 为同源。【核验】
- Skamarock, W. C., J. B. Klemp, J. Dudhia, et al.: *A Description of the Advanced Research WRF Model*（NCAR/TN-475+STR）——“ADT”，动力内核方程组的权威描述（ch21 式 44/45/47 出处）。【核验：源码注释逐字引用】
- WRF 官方 Releases：`https://github.com/wrf-model/WRF/releases`——4.0（2018-06-08）至 4.8.0（2026-06-08）各版 release notes（含 PR 号）。【核验：ch02 逐版抓取】
- WPS v4.7 User's Guide 与源码内 `namelist.wps.all_options`、`geogrid/GEOGRID.TBL.ARW`、`ungrib/Variable_Tables/README`。【核验：ch06】
- 源码内文档：`doc/README.cmake_build`、`test/*/README.*`（理想算例说明九份）、`external/io_netcdf/WRFIO.doc`。【核验：ch05/ch09/ch18】

## d.3　动力内核与数值方法

- Skamarock, W. C., J. B. Klemp, 2008: A time-split nonhydrostatic atmospheric model for weather research and forecasting applications. *J. Comput. Phys.*, 227, 3465–3485.【核验：ch21】
- Wicker, L. J., W. C. Skamarock, 2002: Time-splitting methods for elastic models using forward time schemes. *Mon. Wea. Rev.*, 130, 2088–2097.【核验：ch21】
- Klemp, J. B., W. C. Skamarock, J. Dudhia, 2007: Conservative split-explicit time integration of the nonhydrostatic equations. *Mon. Wea. Rev.*, 135, 2897 起。【通行：卷期页码引用前复核】
- Klemp, J. B., 2011: A terrain-following coordinate with hybrid generalized terrain-following transformations. *Mon. Wea. Rev.*, 139, 1008 起——hybrid_opt=2（ch10 §10.12 与 `Registry/registry.hyb_coord`）。【核验：ch10】
- Jiang, G.-S., C.-W. Shu, 1996: Efficient implementation of weighted ENO schemes. *J. Comput. Phys.*, 126, 202–223；Shu, 2003, *Int. J. Comput. Fluid Dyn.*, 17, 107–118——WENO（`module_advect_em.F: advect_scalar_weno` 头注原文引用）。【核验：源码头注】
- Held, I. M., A. Y. Suarez, 1994: A proposal for the intercomparison of the dynamical cores of atmospheric general circulation models. *Bull. Amer. Meteor. Soc.*, 75, 1825 起——`em_heldsuarez`（`module_damping_em.F: held_suarez_damp`）。【通行】

## d.4　物理方案文献（按本书第 III 部方案族）

**辐射（ch12）**
- Mlawer, E. J., et al., 1997: Radiative transfer for inhomogeneous atmospheres: RRTM… *J. Geophys. Res.*, 102, 16663 起。【核验：ch12 延伸】
- Iacono, M. J., et al., 2008: Radiative forcing by long-lived greenhouse gases: The RRTMG… *J. Geophys. Res.*, 113, D13103。【核验：ch12】
- Clough, S. A., et al., 2005: Atmospheric radiative transfer modeling: a summary of the AER codes. *J. Quant. Spectrosc. Radiat. Transfer*, 91, 233 起。【核验：ch12】
- Kasten, F., A. T. Young, 1989: Revised optical air mass tables and approximation formula. *Appl. Opt.*, 28, 4735 起。【核验：ch12 式 (5.4.22) 对照】

**微物理（ch13）**
- Thompson, G., P. R. Field, R. M. Rasmussen, W. D. Hall, 2008: Explicit forecasts of winter precipitation using an improved bulk microphysics scheme. Part II. *Mon. Wea. Rev.*, 136, 5095 起。【核验：ch13 源码头注系】
- Thompson, G., T. Eidhammer, 2014: A study of aerosol impacts on clouds and precipitation development in a large winter cyclone. *J. Atmos. Sci.*, 71, 3636 起。【核验：ch13】
- Field, P. R., et al., 2005: Parameterization of ice-particle size distributions… *Q. J. R. Meteorol. Soc.*, 131, 421 起。【核验：ch13】
- Cooper, W. A., 1986（冰核化）；Bigg, E. K., 1953（过冷水冻结）；DeMott, P. J., et al., 2010；Koop, T., et al., 2001, *Nature*（均质冻结）。【核验：ch13 §13.7.6 源码注释系】
- Hong, S.-Y., J.-O. J. Lim, 2006: The WRF single-moment 6-class microphysics scheme (WSM6). *J. Korean Meteor. Soc.*, 42, 129 起。【通行：WSM6 对照（ch13 §13.8）】

**边界层（ch14）**
- Nakanishi, M., H. Niino, 2006/2009: An improved Mellor–Yamada model…（MYNN 系列两篇）。【通行】
- Olson, J. B., et al., 2019: A modified version of MYNN-EDMF… *Mon. Wea. Rev.*（WRF 内版本出处）。【通行：`phys/MYNN-EDMF/` 版本史 V1.0–V6.0 见 ch14 §14.6】
- Bougeault, P., P. Lacarrère, 1989: Parameterization of orography-induced turbulence in a mesobeta-scale model. *Mon. Wea. Rev.*, 117, 1872 起——BouLac。【核验：ch14 §14.7】
- Hong, S.-Y., Y. Noh, J. Dudhia, 2006: A new vertical diffusion package with an explicit treatment of entrainment processes. *Mon. Wea. Rev.*, 134, 2318 起——YSU。【通行：ch14 §14.7 对照】

**积云（ch15）**
- Bechtold, P., et al., 2014: Representing equilibrium and nonequilibrium convection in large-scale models. *J. Atmos. Sci.*, 71, 734 起——New Tiedtke。【核验：ch15 §15.4】
- Kain, J. S., 2004: The Kain–Fritsch convective parameterization scheme: An update. *J. Appl. Meteor.*, 43, 170 起——KF/KFeta。【核验：ch15 §15.7】

**陆面与城市（ch16/ch17）**
- Chen, F., J. Dudhia, 2001: Coupling an advanced land surface–hydrology model with the Penn State–NCAR MM5 modeling system. Part I. *Mon. Wea. Rev.*, 129, 569 起——Noah。【核验：ch16】
- Niu, G.-Y., et al., 2011: The community Noah land surface model with multiparameterization options (Noah-MP). *J. Geophys. Res.*, 116, D12109。【通行】
- Kusaka, H., H. Kondo, Y. Kikegawa, F. Kimura, 2001: A simple single-layer urban canopy model… *Bound.-Layer Meteor.*, 101, 329 起——SLUCM。【核验：ch17】
- Martilli, A., A. Clappier, M. W. Rotach, 2002: An urban surface exchange parameterisation for mesoscale models. *Bound.-Layer Meteor.*, 104, 261 起——BEP。【核验：ch17】
- Salamanca, F., A. Martilli, et al., 2010（BEM 建筑能耗系列）。【通行：ch17 §17.4】

**湿度与饱和水汽压（ch11）**
- Murray, F. W., 1966/1986；Bolton, D., 1980, *Mon. Wea. Rev.*, 108, 1046 起；Goff & Gratch, 1946；Murphy, D. M., T. Koop, 2005, *Q. J. R. Meteorol. Soc.*；Flatau, et al., 1992。【核验：ch11 §11.8】

## d.5　理想算例文献（ch18）

- Straka, J. M., et al., 1993——密度流基准（`em_grav2d_x`）。【核验：ch18】
- Weisman, M. L., J. B. Klemp, 1982——超级单体探空（`em_quarter_ss`）。【核验：ch18】
- Rotunno, R., K. A. Emanuel, 1987；Jordan, C. L., 1958——理想台风（`em_tropical_cyclone`）。【核验：ch18】

## d.6　改造与耦合文献（ch21 案例库）

- Berner, J., S.-Y. Ha, J. P. Hacker, A. Fournier, C. Snyder, 2011: Model uncertainty in a mesoscale ensemble prediction system: Stochastic versus multi-physics representations. *Mon. Wea. Rev.*, 139, 1972–1995——SKEBS（`dyn_em/module_stoch.F` 头注原文）。【核验：源码头注】
- Wong, D., J. Pleim, R. Mathur, et al., 2012: WRF-CMAQ two-way coupled system with aerosol feedback: software development and preliminary results. *Geosci. Model Dev.*, 5.【核验：条目经检索证实；页码未核】
- Mandel, J., J. D. Beezley, A. K. Kochanski, 2011: Coupled atmosphere-wildland fire modeling with WRF 3.3 and SFIRE.【线索：会议条目，引用前检索正式版本】
- MAD-WRF：NCAR RAL 项目（作者 Pedro A. Jimenez，`phys/module_madwrf.F` 头注）。【核验：源码署名；正式论文条目未核】
- Polar WRF：Bromwich 等系列工作。【线索】
- Clark, T. L.（COMMAS 模式）——WENO 平流血统（`advect_scalar_weno` 头注 “adapted from COMMAS”）。【核验：源码头注】

## d.7　数据源

| 数据 | 位置/来源 | 用途与致谢 |
|---|---|---|
| ERA5 月 GRIB（2024-12～2025-12，20–1000 hPa z/q/r/t/u/v + 地面） | 集群 `/data/groups/lzu_public/home/share/liuyl17/ERA5_2025/` | 全书驱动数据（ch06–ch08/ch19）；**感谢 liuyl17 开放公共读取**；官方源：Copernicus CDS |
| ERA5 月 nc（New_DATA/Global，2025 起） | `/data/groups/lzu_public/home/share/ERA5/hourly/New_DATA/Global/` | 个例窗口扫描（ch19）；`workspace/data/t2m_2025*_lz.nc` |
| WPS 静态数据 | `/opt/app/wrf/WPS_GEOG/`（集群完整） | geogrid（ch06）；MODIS/USGS 分类 + 城市参数族 |
| 城市扩展/人为热数据集（y2050_urb/y2050_ahe） | 参考个例 `liuyl17/haidian2024` 的 `geog_data_res` 示例 | ch17 数据链路（本书个例无境外覆盖，缺口实录见 ch19） |
| WRF 自带输入表 | `run/CAMtr_volume_mixing_ratio`、`ozone*.formatted`、`RRTMG_LW/SW_DATA`、各 TBL | ch12/ch16/ch17 的“隐性输入” |
| 论文 2 观测与产品 | 观测网（中大杭建团队）、屋顶分割模型、W238/W240 点 | 仅 ch17/ch19/ch20 对接节提及，教材不依赖 |

## d.8　非权威网络资源（线索用，引用须降级）

- CSDN/知乎/个人博客上的 WRF 教程（含本书检索 WRF-CMAQ 条目时所用 CSDN 页）：**一律标注“非权威”**，仅当检索线索；结论必须回到源码或官方文档复验（方案 §4.1 协议）。
- WRF 论坛（`forum.mmm.ucar.edu`）：官方支持的问答库，比博客可靠但仍以源码为准。

## d.9　本书工程资产索引

- 状态文件：`workspace/context/{notes,progress,verify_log}.md`——全书事实的单一事实源（verify_log 含每个集群作业的日期｜主题｜来源｜结论四列）；
- 章—源码对照：`workspace/outline/chapter_map.md`；
- 实验脚本：`workspace/scripts/ch{NN}_*.py`（各章“动手实操”的复现入口；日志在 `workspace/logs/`）；
- 集群工具：`workspace/scripts/cluster.py`（run/srun/salloc/get/put/runfile）与 `workspace/cluster_jobs/*.sh`；
- 数据子集：`workspace/data/`（ch09 IO 样本、ch10 基态、ch19/ch20 stage 子集等）；
- 页图底账：`workspace/book_manifest.csv`（PDF 页码 → jpg 文件名）。
