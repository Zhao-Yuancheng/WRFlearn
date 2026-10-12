# code_01 — 模型常数层（share/module_model_constants.F：全书共用常数的唯一权威定义）

## 一、版本指纹

| 源文件 | 行数 | md5（整文件，按字节） |
|---|---|---|
| share/module_model_constants.F | 159 | 60664d7df258a193d01cbbd1eeec51db |

- 抽取工具：workspace/scripts/code_extract.py v1.2，2026-10-12；块首指纹注释自带 range_md5。
- 本篇 A 级轻量全文（159 行全收）。与书附录 C 的逐常数偏差对照已在教材 [app_a_symbols_constants.md](../app_a_symbols_constants.md) 建表，本篇只补模块内口径注记，不重复偏差表。

## 二、定位

一句话：**WRF 全模式的常数底座**——动力核、五大物理驱动器、初始化件全部从这一个模块取常数（文库内 code_05/06/07/09/10/12/14/20/21/23 等所有篇目的 USE 常数最终汇到这里）；无任何外部依赖，天然是依赖拓扑的 01 号。

**谁在调它**：几乎一切物理与动力模块（grep `USE module_model_constants` 全树数百处）；教材锚点：[app_a_symbols_constants.md](../app_a_symbols_constants.md)（三列对照表）、[ch11_composition_moisture_aerosol.md](../ch11_composition_moisture_aerosol.md)（常数物理背景）。

## 三、全文（逐段注记）

<!-- code_extract code_extract.py v1.2
source: share/module_model_constants.F
ranges: L1-L159
file_lines: 159
file_md5: 60664d7df258a193d01cbbd1eeec51db
display: line-numbered (strip L-prefix and !file: line to restore)
range_md5: 60664d7df258a193d01cbbd1eeec51db
seg_lines: 159
-->

```fortran
!file: share/module_model_constants.F    L1-L159
L00001  !WRF:MODEL_LAYER:CONSTANTS
L00002  !
L00003  
L00004   MODULE module_model_constants
L00005  
L00006     !  2. Following are constants for use in defining real number bounds.
L00007  
L00008     !  A really small number.
L00009  
L00010     REAL    , PARAMETER :: epsilon         = 1.E-15
L00011  
L00012     !  4. Following is information related to the physical constants.
L00013  
L00014     !  These are the physical constants used within the model.
L00015  
L00016  ! JM NOTE -- can we name this grav instead?
L00017     REAL    , PARAMETER :: g = 9.81  ! acceleration due to gravity (m {s}^-2)
L00018  
L00019     REAL    , PARAMETER :: r_d          = 287.       ! gas constant of dry air (J deg^-1 kg^-1)
L00020     REAL    , PARAMETER :: cp           = 7.*r_d/2.  ! 
L00021  
L00022     REAL    , PARAMETER :: r_v          = 461.6      ! gas constant for water vapor (J deg^-1 kg^-1)
L00023     REAL    , PARAMETER :: cv           = cp-r_d     ! Specific heat of air at contant volume (J deg^-1 kg^-1)
L00024     REAL    , PARAMETER :: cpv          = 4.*r_v
L00025     REAL    , PARAMETER :: cvv          = cpv-r_v    ! 
L00026     REAL    , PARAMETER :: cvpm         = -cv/cp
L00027     REAL    , PARAMETER :: cliq         = 4190.      ! specific heat of liquid water at 0^oC
L00028     REAL    , PARAMETER :: cice         = 2106.      ! specific heat of ice at 0^oC
L00029     REAL    , PARAMETER :: psat         = 610.78
L00030     REAL    , PARAMETER :: rcv          = r_d/cv     ! 
L00031     REAL    , PARAMETER :: rcp          = r_d/cp
L00032     REAL    , PARAMETER :: rovg         = r_d/g
L00033     REAL    , PARAMETER :: c2           = cp * rcv
L00034     real    , parameter :: mwdry        = 28.966     ! molecular weight of dry air (g/mole)
L00035  
L00036     REAL    , PARAMETER :: p1000mb      = 100000.    ! pressure at 1000 hPa (pa)
L00037     REAL    , PARAMETER :: t0           = 300.       ! base state tempertaure (K) 
L00038     REAL    , PARAMETER :: p0           = p1000mb    ! base state surface pressure (pa)
L00039     REAL    , PARAMETER :: cpovcv       = cp/(cp-r_d)
L00040     REAL    , PARAMETER :: cvovcp       = 1./cpovcv
L00041     REAL    , PARAMETER :: rvovrd       = r_v/r_d
L00042  
L00043     REAL    , PARAMETER :: reradius     = 1./6370.0e03  ! reciprocal of earth radius (m^-1) 
L00044  
L00045     REAL    , PARAMETER :: asselin      = .025
L00046  !   REAL    , PARAMETER :: asselin      = .0
L00047     REAL    , PARAMETER :: cb           = 25.
L00048  
L00049     REAL    , PARAMETER :: XLV0         = 3.15E6       !  constant defined for calculation of latent heating 
L00050     REAL    , PARAMETER :: XLV1         = 2370.        !  constant defined for calculation of latent heating 
L00051     REAL    , PARAMETER :: XLS0         = 2.905E6      !  constant defined for calculation of latent heating
L00052     REAL    , PARAMETER :: XLS1         = 259.532      !  constant defined for calculation of latent heating
L00053  
L00054     REAL    , PARAMETER :: XLS          = 2.85E6      ! latent heat of sublimation of water at 0^oC (J kg^-1) 
L00055     REAL    , PARAMETER :: XLV          = 2.5E6       ! latent heat of vaporization of water at 0^oC (J kg^-1)
L00056     REAL    , PARAMETER :: XLF          = 3.50E5      ! latent heat of fusion of water at 0^oC (J kg^-1)
L00057  
L00058     REAL    , PARAMETER :: rhowater     = 1000.       ! density of liquid water at 0^oC (kg m^-3)
L00059     REAL    , PARAMETER :: rhosnow      = 100.        ! density of snow (kg m^-3)
L00060     REAL    , PARAMETER :: rhoair0      = 1.28        ! density of dry air at 0^oC and 1000mb pressure (kg m^-3)
L00061  
L00062     REAL    , PARAMETER :: RE_QC_BG     = 2.49E-6     ! effective radius of cloud for background (m)
L00063     REAL    , PARAMETER :: RE_QI_BG     = 4.99E-6     ! effective radius of ice for background (m)
L00064     REAL    , PARAMETER :: RE_QS_BG     = 9.99E-6     ! effective radius of snow for background (m)
L00065     REAL    , PARAMETER :: RE_QC_MAX    =  50.E-6     ! max effective radius of cloud allowed
L00066     REAL    , PARAMETER :: RE_QI_MAX    = 125.E-6     ! max effective radius of ice allowed
L00067     REAL    , PARAMETER :: RE_QS_MAX    = 999.E-6     ! max effective radius of snow allowed
L00068  !
L00069  ! Now namelist-specified parameter: ccn_conc - RAS
L00070  !   REAL    , PARAMETER :: n_ccn0       = 1.0E8
L00071  !
L00072     REAL    , PARAMETER :: piconst      = 3.1415926535897932384626433    ! constant of PI
L00073     REAL    , PARAMETER :: DEGRAD       = piconst/180.                   ! radians per degree
L00074     REAL    , PARAMETER :: DPD          = 360./365.
L00075  
L00076     REAL    , PARAMETER ::  SVP1=0.6112      ! constant for saturation vapor pressure calculation (dimensionless)
L00077     REAL    , PARAMETER ::  SVP2=17.67       ! constant for saturation vapor pressure calculation (dimensionless)
L00078     REAL    , PARAMETER ::  SVP3=29.65       ! constant for saturation vapor pressure calculation (K)
L00079     REAL    , PARAMETER ::  SVPT0=273.15     ! constant for saturation vapor pressure calculation (K)
L00080     REAL    , PARAMETER ::  EP_1=R_v/R_d-1.  !  constant for virtual temperature (r_v/r_d - 1) (dimensionless)
L00081     REAL    , PARAMETER ::  EP_2=R_d/R_v     ! constant for specific humidity calculation (dimensionless)
L00082     REAL    , PARAMETER ::  KARMAN=0.4               ! von Karman constant
L00083     REAL    , PARAMETER ::  EOMEG=7.2921E-5          ! angular velocity of rotation (rad^-1)
L00084     REAL    , PARAMETER ::  STBOLT=5.67051E-8        ! Stefan-Boltzmann constant (W m^-2 deg^-4) 
L00085  
L00086     REAL    , PARAMETER ::  prandtl = 1./3.0   ! prandtl's mixing length (m) 
L00087                                                ! constants for w-damping option
L00088     REAL    , PARAMETER ::  w_alpha = 0.3      ! strength m/s/s
L00089     REAL    , PARAMETER ::  w_beta  = 1.0      ! activation cfl number
L00090  
L00091         REAL , PARAMETER ::  pq0=379.90516     ! 
L00092         REAL , PARAMETER ::  epsq2=0.2         ! initial TKE for camuw PBL scheme (m2 s^-2) 
L00093         REAL , PARAMETER ::  a2=17.2693882
L00094         REAL , PARAMETER ::  a3=273.16
L00095         REAL , PARAMETER ::  a4=35.86
L00096         REAL , PARAMETER ::  epsq=1.e-12      ! threshold specified for SPECIFIC HUMIDITY calculation in BMJ cumulus scheme (kg kg^-1)
L00097         REAL , PARAMETER ::  p608=rvovrd-1.
L00098         REAL , PARAMETER ::  climit=1.e-20
L00099         REAL , PARAMETER ::  cm1=2937.4
L00100         REAL , PARAMETER ::  cm2=4.9283
L00101         REAL , PARAMETER ::  cm3=23.5518
L00102  !       REAL , PARAMETER ::  defc=8.0
L00103  !       REAL , PARAMETER ::  defm=32.0
L00104         REAL , PARAMETER ::  defc=0.0
L00105         REAL , PARAMETER ::  defm=99999.0
L00106         REAL , PARAMETER ::  epsfc=1./1.05
L00107         REAL , PARAMETER ::  epswet=0.0
L00108         REAL , PARAMETER ::  fcdif=1./3.
L00109         REAL , PARAMETER ::  fcm=0.00003
L00110         REAL , PARAMETER ::  gma=-r_d*(1.-rcp)*0.5
L00111         REAL , PARAMETER ::  p400=40000.0
L00112         REAL , PARAMETER ::  phitp=15000.0
L00113         REAL , PARAMETER ::  pi2=2.*3.1415926, pi1=3.1415926
L00114         REAL , PARAMETER ::  plbtm=105000.0
L00115         REAL , PARAMETER ::  plomd=64200.0
L00116         REAL , PARAMETER ::  pmdhi=35000.0
L00117         REAL , PARAMETER ::  q2ini=0.50
L00118         REAL , PARAMETER ::  rfcp=0.25/cp
L00119         REAL , PARAMETER ::  rhcrit_land=0.75
L00120         REAL , PARAMETER ::  rhcrit_sea=0.80
L00121         REAL , PARAMETER ::  rlag=14.8125
L00122         REAL , PARAMETER ::  rlx=0.90
L00123         REAL , PARAMETER ::  scq2=50.0
L00124         REAL , PARAMETER ::  slopht=0.001
L00125         REAL , PARAMETER ::  tlc=2.*0.703972477
L00126         REAL , PARAMETER ::  wa=0.15
L00127         REAL , PARAMETER ::  wght=0.35
L00128         REAL , PARAMETER ::  wpc=0.075
L00129         REAL , PARAMETER ::  z0land=0.10    ! surface roughness length over land (m)
L00130         REAL , PARAMETER ::  z0max=0.008    !  maximum roughness length (m)
L00131         REAL , PARAMETER ::  z0sea=0.001   ! roughness length over ocean (m)
L00132  
L00133  
L00134     !  Earth
L00135  
L00136     !  The value for P2SI *must* be set to 1.0 for Earth
L00137     !  Although, now we may not need this declaration here (see above)
L00138     !REAL    , PARAMETER :: P2SI         = 1.0
L00139  
L00140     !  Orbital constants:
L00141  
L00142     INTEGER , PARAMETER :: PLANET_YEAR = 365   ! number of days in a calendar year
L00143     REAL , PARAMETER :: OBLIQUITY = 23.5       ! solar obliquity (degree)
L00144     REAL , PARAMETER :: ECCENTRICITY = 0.014   ! Orbital eccentricity 
L00145     REAL , PARAMETER :: SEMIMAJORAXIS = 1.0    ! Ratio of semi-major axis of planet / semi-major axis of earth
L00146     REAL , PARAMETER :: zero_date = 0.0        ! Time of perihelion passage
L00147     REAL , PARAMETER :: EQUINOX_FRACTION= 0.0  ! Fraction into the year (from perhelion) of the occurrence of the Northern Spring Equinox
L00148  
L00149  ! 2012103
L00150  #if (EM_CORE == 1)
L00151  ! for calls to set_tiles
L00152     INTEGER, PARAMETER :: ZONE_SOLVE_EM = 1
L00153     INTEGER, PARAMETER :: ZONE_SFS = 2
L00154  #endif
L00155  
L00156   CONTAINS
L00157     SUBROUTINE init_module_model_constants
L00158     END SUBROUTINE init_module_model_constants
L00159   END MODULE module_model_constants
```

> 讲解（按段走读，行号见显示层前缀）：①**实数界与重力**——epsilon=1e-15；**g=9.81**（书 9.80665 的圆整，JM 留言「can we name this grav instead」——与局部变量 g 重名的老问题）。②**气体与比热群**——r_d=287（书 287.05）；**cp=7·r_d/2=1004.5**（干空气定压比热的理论关系式，非独立常数）；r_v=461.6；cv=cp−r_d=717.5；**cpv=4·r_v=1846.4**（水汽比热同为理论关系）；cvv、cvpm=−cv/cp（位温方程里的负 cv/cp 项，微物理饱和调整用）；cliq=4190/cice=2106（0°C 液水/冰比热，与 noahlsm 自带的 4218/2106 微差——**两套口径并存**，见 code_12a §三）；psat=610.78 Pa（0°C 饱和水汽压）；rcv/rcp/rovg/c2、mwdry=28.966。③**基态群**——p1000mb=100000 Pa（**名实之差：变量名写 1000mb，值是 1e5 Pa**）；t0=300（基态温度，注意不是 0°C 的 273.15）；p0=p1000mb；cpovcv/cvovcp/rvovrd。④**几何与滤波**——reradius=1/6370e3（地球半径倒数）；**asselin=0.025**（Asselin-Robert 时间滤波系数，动力核用；0 的备选注释=关滤波实验）；cb=25。⑤**旧 eta 系潜热线性式四件**——XLV0/XLV1/XLS0/XLS1（BMJ 等 Janjic 谱系方案的 Lv(T)/Ls(T) 线性式系数，与书 (4.x) 多项式口径不同——**教材 13.9.2 的 Lv(T) 三口径议题在此再加一条**）；⑥**0°C 潜热三常数**——XLS=2.85e6/XLV=2.5e6/XLF=3.50e5（书 2.834e6/2.5e6/3.336e5 的 WRF 圆整，noahlsm 用 2.83e6/2.501e6/3.335e5——又是并存口径）。⑦**密度三件**——rhowater=1000/rhosnow=100/rhoair0=1.28。⑧**辐射有效半径六件**——RE_QC/QI/QS_BG（2.49/4.99/9.99 μm 的背景值）与 MAX（50/125/999 μm 上限）——微物理不供有效半径时辐射云光学的默认。⑨**角度与历法**——piconst（18 位精度）、DEGRAD、**DPD=360/365（度/儒略日）**——radconst 的太阳黄经就吃它。⑩**饱和水汽压与虚拟温**——SVP1=0.6112/SVP2=17.67/SVP3=29.65（Tetens/Bolton 系；cal_cldfra1 的 Murray 1966 系数 17.2693882/35.86 是另一套，两套并存）；SVPT0=273.15；EP_1/EP_2；KARMAN=0.4；EOMEG=7.2921e-5（地球自转角速度）；STBOLT=5.67051e-8（Stefan-Boltzmann）。⑪**边界层杂项**——prandtl=1/3、w_alpha=0.3/w_beta=1.0（垂直速度阻尼选项）。⑫**BMJ/eta 遗产系数群**（pq0 至 z0sea 约 40 个）——pq0=379.90516、a2/a3/a4（饱和比湿 Tetens）、epsq（BMJ 比湿阈值）、cm1..3、**defc/defm 被从 8.0/32.0 改成 0.0/99999.0（原对流触发尺度判据被关闭）**、rhcrit_land/sea=0.75/0.80、z0land=0.10/z0max=0.008/z0sea=0.001（注意 z0max 名实：是**最小粗糙度**口径还是最大——注释写 maximum，值 8mm 比 land 10cm 小，实为旧 eta 的 z0 低限，勿按名取义）。⑬**行星常数群**——PLANET_YEAR=365、OBLIQUITY=23.5（与 radconst 的 OBECL 同值不同名）、**ECCENTRICITY=0.014（定义了但 radconst 不用它——radconst 走 Paltridge-Platt 谐波式）**、SEMIMAJORAXIS、EQUINOX_FRACTION——行星通用框架的遗迹（火星 WRF 用同一模块）。⑭**tile 分区常数**——ZONE_SOLVE_EM/ZONE_SFS（set_tiles 的分区编号，仅 EM_CORE）。⑮空壳 init 子程序——框架要求每个模块有 init 入口的仪式性实现。

## 四、改造入口

1. **常数敏感性实验**（g/r_d/cp 微调）只动本文件——全模式生效，注意 cp=7·r_d/2 的联动关系不是独立参数。
2. **Asselin 滤波开关**：asselin=0 备选注释。
3. **双口径并存清单**（改常数前先查）：cliq/cice vs noahlsm 自带；XLV/XLS/XLF vs LSUBC/LSUBS/LSUBF 系；SVP 群 vs Murray 群 vs noahlsm 的 ELCP 口径——**只改本文件不影响自带副本**（code_10/12a 已标注的同名拷贝问题同源）。
4. **行星框架**：OBLIQUITY/ECCENTRICITY 群——理想行星实验（如火星）的入口，但 radconst 的太阳几何不走这组。

## 五、上下游链接

- 消费方：文库全部方案篇（code_05/06/07/09/10/12/14/20/21/22/23）；动力核导航：[code_50_solve_em.md](code_50_solve_em.md)
- 教材正文：[app_a_symbols_constants.md](../app_a_symbols_constants.md)（偏差对照权威表）、[ch11_composition_moisture_aerosol.md](../ch11_composition_moisture_aerosol.md)
