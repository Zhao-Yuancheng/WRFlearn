# code_61 — Noah 的海冰与冰川件（module_sf_noah_seaice_drv.F + module_sf_noah_seaice.F + module_sf_noahlsm_glacial_only.F：C 级接口索引）

## 一、版本指纹

| 源文件 | 行数 | md5（整文件，按字节） |
|---|---|---|
| phys/module_sf_noah_seaice_drv.F | 502 | 510c4ea03c8ee8d942375581d258ab6b |
| phys/module_sf_noah_seaice.F | 1291 | ca3bee0470b9f9127f8c8c9cd32b033a |
| phys/module_sf_noahlsm_glacial_only.F | 1280 | 8d406e754b11825964f043f359fa2275 |

- 抽取工具：workspace/scripts/code_extract.py v1.2，2026-10-12；块首指纹注释自带 range_md5。
- 收录分级（C）：三件各收头部（模块声明与主入口签名）；内部单元走同源差异注记。上游：[code_12a_module_sf_noahlsm.md](code_12a_module_sf_noahlsm.md)、[code_13_module_sf_noahdrv.md](code_13_module_sf_noahdrv.md)（ICE 三分支的调用侧）。

## 二、定位

一句话：Noah 生态的两个**极地特化件**——海冰件（seaice_drv→seaice：带 5 cm 雪层的固定厚度冰面能量平衡）与冰川件（glacial_only：无土壤水的冰盖能量平衡）；两者都是 noahlsm 的**裁剪孪生**——CSNOW/HRTICE/PENMAN/SHFLX/SNOPAC/SNOWPACK/SNOWZ0/SNOW_NEW 同名单元直接复用或改写 noahlsm 的对应件，但常数经 `USE module_sf_noahlsm` 导入（RD/SIGMA/CPH2O/CPICE/LSUBF/EMISSI_S，seaice 还导入 HSTEP、glacial 导入 ROSR12 与 LVCOEF_DATA）——**三文件常数/求解器单点维护**的样板。

**谁在调它们**：seaice_noah 由 surface_driver 的 OML/海冰分支调（fractional_seaice 选项，code_24 §二）；SFLX_GLACIAL 由 noahdrv 的 ICE=−1 分支调（code_13 §4.4）。

## 三、三件头部

<!-- code_extract code_extract.py v1.2
source: phys/module_sf_noah_seaice.F
ranges: L1-L35
file_lines: 1291
file_md5: ca3bee0470b9f9127f8c8c9cd32b033a
display: line-numbered (strip L-prefix and !file: line to restore)
range_md5: 34b0541dfe37871b812fb3ea8e8c2282
seg_lines: 35
-->

```fortran
!file: phys/module_sf_noah_seaice.F    L1-L35
L00001  MODULE module_sf_noah_seaice
L00002  #if defined(mpas)
L00003  use mpas_atmphys_constants,only: cp,R_D=>R_d,XLF,XLV,RHOWATER=>rho_w,STBOLT
L00004  use mpas_atmphys_utilities, only: physics_error_fatal
L00005  #define FATAL_ERROR(M) call physics_error_fatal( M )
L00006  #else
L00007  use module_model_constants, only : CP, R_D, XLF, XLV, RHOWATER, STBOLT
L00008  use module_wrf_error
L00009  #define FATAL_ERROR(M) call wrf_error_fatal( M )
L00010  #endif
L00011    use module_sf_noahlsm, only : RD, SIGMA, CPH2O, CPICE, LSUBF, EMISSI_S, &
L00012         &                        HSTEP
L00013  
L00014    PUBLIC  SFLX_SEAICE
L00015    PRIVATE CSNOW
L00016    PRIVATE HRTICE
L00017    PRIVATE PENMAN
L00018    PRIVATE SHFLX
L00019    PRIVATE SNOPAC
L00020    PRIVATE SNOWPACK
L00021    PRIVATE SNOWZ0
L00022    PRIVATE SNOW_NEW
L00023  
L00024    INTEGER, PRIVATE :: ILOC
L00025    INTEGER, PRIVATE :: JLOC
L00026  !$omp threadprivate(iloc, jloc)
L00027  
L00028    REAL, PARAMETER, PRIVATE :: TFREEZ = 273.15
L00029  !
L00030  CONTAINS
L00031  !
L00032    SUBROUTINE SFLX_SEAICE (IILOC, JJLOC, SEAICE_ALBEDO_OPT, SEAICE_ALBEDO_DEFAULT, &    !C
L00033         &                  SEAICE_SNOWDEPTH_OPT, SEAICE_SNOWDEPTH_MAX,      &    !C
L00034         &                  SEAICE_SNOWDEPTH_MIN,                            &    !C
L00035         &                  FFROZP,DT,ZLVL,NSOIL,                            &    !C
```

> 讲解：seaice 件头部三件事：①MPAS/WRF 双框架宏（与 noahlsm 同款）；②`use module_sf_noahlsm, only: RD, SIGMA, CPH2O, CPICE, LSUBF, EMISSI_S, HSTEP`——**常数与热推进求解器都从 noahlsm 导入**（HSTEP 指冰内温度层的推进——海冰按 4 层冰+雪层处理但复用 Noah 的三对角推进）；③PUBLIC 只出 SFLX_SEAICE、其余八单元全 PRIVATE；TFREEZ=273.15 自带。主入口签名可见海冰五选项（SEAICE_ALBEDO_OPT/DEFAULT、SEAICE_SNOWDEPTH_OPT/MAX/MIN——namelist &physics 直通）。

<!-- code_extract code_extract.py v1.2
source: phys/module_sf_noah_seaice_drv.F
ranges: L1-L35
file_lines: 502
file_md5: 510c4ea03c8ee8d942375581d258ab6b
display: line-numbered (strip L-prefix and !file: line to restore)
range_md5: 0145d17e8f3b9fe9aa98a468c09df1d4
seg_lines: 35
-->

```fortran
!file: phys/module_sf_noah_seaice_drv.F    L1-L35
L00001  module module_sf_noah_seaice_drv
L00002  #if defined(mpas)
L00003  use mpas_atmphys_utilities, only: physics_message,physics_error_fatal
L00004  #define FATAL_ERROR(M) call physics_error_fatal( M )
L00005  #define WRITE_MESSAGE(M) call physics_message( M )
L00006  #else
L00007  use module_wrf_error
L00008  #define FATAL_ERROR(M) call wrf_error_fatal( M )
L00009  #define WRITE_MESSAGE(M) call wrf_message( M )
L00010  #endif
L00011    use module_sf_noah_seaice
L00012    implicit none
L00013  contains
L00014    subroutine seaice_noah( SEAICE_ALBEDO_OPT, SEAICE_ALBEDO_DEFAULT, SEAICE_THICKNESS_OPT, &
L00015         &                  SEAICE_THICKNESS_DEFAULT, SEAICE_SNOWDEPTH_OPT,               &
L00016         &                  SEAICE_SNOWDEPTH_MAX, SEAICE_SNOWDEPTH_MIN,                   &
L00017         &                  T3D, QV3D, P8W3D, DZ8W, NUM_SOIL_LAYERS, DT, FRPCPN, SR,      &
L00018         &                  GLW, SWDOWN, RAINBL, SNOALB2D, QGH, XICE, XICE_THRESHOLD,     &
L00019         &                  ALBSI, ICEDEPTH, SNOWSI,                                      &
L00020         &                  TSLB, EMISS, ALBEDO, Z02D, TSK, SNOW, SNOWC, SNOWH2D, &
L00021         &                  CHS, CHS2, CQS2,                                              &
L00022         &                  RIB, ZNT, LH, HFX, QFX, POTEVP, GRDFLX, QSFC, ACSNOW,         &
L00023         &                  ACSNOM, SNOPCX, SFCRUNOFF, NOAHRES,                           &
L00024         &                  SF_URBAN_PHYSICS, B_T_BEP, B_Q_BEP, RHO,                      &
L00025         &                  IDS, IDE, JDS, JDE, KDS, KDE,                                 &
L00026         &                  IMS, IME, JMS, JME, KMS, KME,                                 &
L00027         &                  ITS, ITE, JTS, JTE, KTS, KTE  )
L00028  #if defined(wrfmodel)
L00029  #if (NMM_CORE != 1)
L00030      USE module_state_description, ONLY : NOAHUCMSCHEME
L00031      USE module_state_description, ONLY : BEPSCHEME
L00032      USE module_state_description, ONLY : BEP_BEMSCHEME
L00033  #endif
L00034  #endif
L00035      implicit none
```

> 讲解：**海冰驱动层**（seaice_noah，487 行单子程序）：签名即功能——五选项全收 + ICEDEPTH/SNOWSI/ALBSI 三个海冰专用态（冰厚/雪深/反照率，Registry 由 real 初始化 ifndicedepth/ifndalbsi 旗标控制）、XICE/XICE_THRESHOLD 分值冰判据；`#if (NMM_CORE != 1)` 下 USE state_description 的 NOAHUCMSCHEME/BEPSCHEME/BEP_BEMSCHEME——**海冰点在城市方案下的兼容处理**（B_T_BEP/B_Q_BEP 入参：海冰点的 BEP 源项要清零）。内部按格点判 XICE≥threshold 后调 SFLX_SEAICE（逐列）。

<!-- code_extract code_extract.py v1.2
source: phys/module_sf_noahlsm_glacial_only.F
ranges: L1-L40
file_lines: 1280
file_md5: 8d406e754b11825964f043f359fa2275
display: line-numbered (strip L-prefix and !file: line to restore)
range_md5: 2a2b80f56f1e01313aebd99587556357
seg_lines: 40
-->

```fortran
!file: phys/module_sf_noahlsm_glacial_only.F    L1-L40
L00001  MODULE module_sf_noahlsm_glacial_only
L00002  #if defined(mpas)
L00003  use mpas_atmphys_constants
L00004  use mpas_atmphys_utilities, only: physics_error_fatal
L00005  #define FATAL_ERROR(M) call physics_error_fatal( M )
L00006  #else
L00007  use module_model_constants
L00008  use module_wrf_error
L00009  #define FATAL_ERROR(M) call wrf_error_fatal( M )
L00010  #endif
L00011  
L00012    USE module_sf_noahlsm, ONLY : RD, SIGMA, CPH2O, CPICE, LSUBF, EMISSI_S, ROSR12
L00013    USE module_sf_noahlsm, ONLY : LVCOEF_DATA
L00014  
L00015    PRIVATE :: ALCALC
L00016    PRIVATE :: CSNOW
L00017    PRIVATE :: HRTICE
L00018    PRIVATE :: HSTEP
L00019    PRIVATE :: PENMAN
L00020    PRIVATE :: SHFLX
L00021    PRIVATE :: SNOPAC
L00022    PRIVATE :: SNOWPACK
L00023    PRIVATE :: SNOWZ0
L00024    PRIVATE :: SNOW_NEW
L00025  
L00026    integer, private :: iloc, jloc
L00027  !$omp threadprivate(iloc, jloc)
L00028  
L00029  CONTAINS
L00030  
L00031    SUBROUTINE SFLX_GLACIAL (IILOC,JJLOC,ISICE,FFROZP,DT,ZLVL,NSOIL,SLDPTH,     &    !C
L00032         &                   LWDN,SOLNET,SFCPRS,PRCP,SFCTMP,Q2,           &    !F
L00033         &                   TH2,Q2SAT,DQSDT2,                            &    !I
L00034         &                   ALB, SNOALB,TBOT, Z0BRD, Z0, EMISSI, EMBRD,  &    !S
L00035         &                   T1,STC,SNOWH,SNEQV,ALBEDO,CH,                &    !H
L00036  ! ----------------------------------------------------------------------
L00037  ! OUTPUTS, DIAGNOSTICS, PARAMETERS BELOW GENERALLY NOT NECESSARY WHEN
L00038  ! COUPLED WITH E.G. A NWP MODEL (SUCH AS THE NOAA/NWS/NCEP MESOSCALE ETA
L00039  ! MODEL).  OTHER APPLICATIONS MAY REQUIRE DIFFERENT OUTPUT VARIABLES.
L00040  ! ----------------------------------------------------------------------
```

> 讲解：冰川件头部：USE noahlsm 取 RD/SIGMA/CPH2O/CPICE/LSUBF/EMISSI_S + **ROSR12（三对角求解器）+ LVCOEF_DATA（雪反照率老化系数）**——冰内温度层推进与雪反照率全套复用；PRIVATE 十单元、只出 SFLX_GLACIAL。主入口签名比 SFLX 精简一个量级：无土壤水/无蒸腾/无 RUNOFF2（对照 code_13 §4.4 的实参表——只有 RUNOFF1）。

## 四、同源单元差异注记（不重录）

| 单元 | seaice（L544–L1288） | glacial（L412–L1199） | 与 noahlsm 的关系 |
|---|---|---|---|
| CSNOW | 40 行 | 37 行 | 同 Dyachkova 式；冰面不 ×2 翻倍（对照 12a §六——**翻倍系数只在陆地件**） |
| HRTICE | 119 行 | 143 行 | **HRT 的冰面特化**：冰层导热（无对流项、相变在界面） |
| PENMAN | 73 行 | 64 行 | 精简版（无降水热容项的完整处理） |
| SHFLX | 28 行 | 30 行 | 冰内热通量壳（调 HRTICE+HSTEP/自推进） |
| SNOPAC | 265 行 | 218 行 | 雪盖路径裁剪版（无土壤水交互） |
| SNOWPACK/SNOWZ0/SNOW_NEW | 126/30/50 行 | 124/—/— | 与 noahlsm 同构（压密/粗糙度/新雪） |
| ALCALC | — | 37 行 | 雪龄反照率（glacial 带、seaice 用 SEAICE_ALBEDO_OPT 常数表） |
| HSTEP | （USE noahlsm） | 46 行 | seaice 直接复用 noahlsm 的推进件 |

> 讲解：读法建议——先读 noahlsm（code_12a/12b）建立基准，再看两件的差异行即可；**海冰/冰川的能量守恒框架与陆地 Noah 同构**（PENMAN 潜势蒸发→SNOPAC 雪盖→SNOWPACK 压密），差异集中在：无土壤水储池、冰层导热用 HRTICE、雪/冰反照率走 SEAICE_ALBEDO_OPT 表或 ALCALC。

## 五、改造入口

1. **海冰能量平衡升级**（厚冰分类/冰内卤水传导）：SFLX_SEAICE 的固定厚度假设是第一改造点——SEAICE_THICKNESS_OPT 已是挂点。
2. **分值海冰**：seaice_noah 的 XICE_THRESHOLD（0.5/0.02 双口径，code_61 与 lsm_mosaic_init 的取值链）。
3. **冰川物质平衡**：SFLX_GLACIAL 只有 RUNOFF1——融雪出流直接流失，加冰面升华/再冻结账户在此。

## 六、上下游链接

- 调用链：[code_24_module_surface_driver.md](code_24_module_surface_driver.md)（seaice_noah）、[code_13_module_sf_noahdrv.md](code_13_module_sf_noahdrv.md)（SFLX_GLACIAL 的 ICE 分支）
- 同源基准：[code_12a_module_sf_noahlsm.md](code_12a_module_sf_noahlsm.md)、[code_12b_module_sf_noahlsm.md](code_12b_module_sf_noahlsm.md)
- 教材正文：[ch16_land_surface_family.md](../ch16_land_surface_family.md)
