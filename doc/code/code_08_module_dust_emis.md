# code_08 — 尘排放简易方案（module_dust_emis.F + module_data_gocart_dust.F：bulk_dust_emis 与 GOCART 五_bins 数据）

## 一、版本指纹

| 源文件 | 行数 | md5（整文件，按字节） |
|---|---|---|
| phys/module_dust_emis.F | 189 | 07741bb134983bc2e445f0132bc6bbda |
| phys/module_data_gocart_dust.F | 39 | 936c5881e15ea3b0e99f677aec11f984 |

- 抽取工具：workspace/scripts/code_extract.py v1.2，2026-10-12；块首指纹注释自带 range_md5。
- 收录分级（C）：dust_emis 头段 + gocart 数据模块全文；bulk_dust_emis 主体（L56–L187，GOCART 排放公式的实现）注记不录。教材锚点：[ch13_microphysics_family.md](../ch13_microphysics_family.md)（Thompson-aero 的前置件）、[ch20_modifying_wrf.md](../ch20_modifying_wrf.md)。

## 二、定位

一句话：**化学开关之外的简易起尘方案**——bulk_dust_emis（Mei Xu 2017-01 从 mosaic_dust_gocartemis 改写 + G. Thompson 2017-09 增补）从风速/土壤湿度/可蚀性直接算尘排放**数浓度**（#/kg/s），经 nifa2d 更新 QNIFA（NIFA 预报量），再被辐射的 aer_opt=3 链路消费（code_20 §五 gt_aod）——**不用 chem_opt 也能做沙尘辐射效应**的轻量通道。

**谁在调它**：module_surface_driver（thompson 方案配套的 dustrt 选项分支）；数据底座 module_data_gocart_dust 与 WRF_CHEM 的 gocart 共用（radiation_driver 的 USE 清单里就有它，code_13 §三）。

## 三、头部与数据底座

<!-- code_extract code_extract.py v1.2
source: phys/module_dust_emis.F
ranges: L1-L55
file_lines: 189
file_md5: 07741bb134983bc2e445f0132bc6bbda
display: line-numbered (strip L-prefix and !file: line to restore)
range_md5: 29976c39255af2614939fe67f3c4ea90
seg_lines: 55
-->

```fortran
!file: phys/module_dust_emis.F    L1-L55
L00001  !WRF:MEDIATION_LAYER:PHYSICS
L00002  ! *** add new modules of schemes here
L00003  !
L00004  MODULE module_dust_emis
L00005  CONTAINS
L00006  
L00007  !====================================================================================
L00008  ! simple dust emission scheme outside of WRF_CHEM
L00009  !       revised from s/r mosaic_dust_gocartemis
L00010  !         Mei Xu 2017Jan31 and additions by G. Thompson 2017Sep19
L00011  !====================================================================================
L00012    subroutine bulk_dust_emis (ktau,dt,num_soil_layers,u_phy,v_phy,          &
L00013           rho_phy,alt,u10,v10,p8w,dz8w,smois,erod,                          &
L00014           ivgtyp,isltyp,vegfra,albbck,xland,dx,g,                           &
L00015           nifa2d,                                                           &
L00016           ids,ide, jds,jde, kds,kde,                                        &
L00017           ims,ime, jms,jme, kms,kme,                                        &
L00018           its,ite, jts,jte, kts,kte                                         )
L00019  !====================================================================================
L00020  ! INPUT:
L00021  ! ktau          - simulation time
L00022  ! dt            - size of timestep
L00023  ! u_phy,v_phy   - state variables of wind
L00024  ! rho_phy,alt   - state variable of density and inverse of density
L00025  ! dz8w,p8w      - model layer depth 
L00026  ! ivgtyp,isltyp - dominant vegetation, soil type
L00027  ! vegfra        - vegetation fraction (0-100)
L00028  ! albbck        - background sfc albedo used to increase erod where desert-like
L00029  ! xland         - land mask (1: land, 2: water)
L00030  ! dx, g         - model grid increment, gravity constant
L00031  ! smois         - soil moisture
L00032  ! erod          - fraction of erodible grid cell, for 1: Sand, 2: Silt, 3: Clay
L00033  !               - read in from wrfinput
L00034  ! OUTPUT:
L00035  ! nifa2d        - dust generation in #/kg/s - to be used to update QNIFA (# kg-1)
L00036  !------------------------------------------------------------------------------------
L00037  ! Local variables:
L00038  ! nmx           - number of dust size bins
L00039  ! ilwi          - land/water flag
L00040  ! bems          - binned dust emission in kg/timestep/cell 
L00041  ! totalemis     - dust emission from 0.1-10 um in radius, in ug/m2/s
L00042  ! erodin        - fraction of erodible grid cel,
L00043  ! w10m          - total wind speed at 10 m
L00044  ! gwet          - volumetric soil moisture over porosity
L00045  ! dxy           - model grid box area
L00046  ! airmas        - grid box air mass
L00047  ! airden        - air density
L00048  ! DSRC          - source of each dust type           (kg/timestep/cell)
L00049  ! 
L00050  ! USED from module_data_gocart_dust:
L00051  ! porosity      -
L00052  ! ch_dust       - Constant to fudge the total emission of dust  (s2/m2)
L00053  ! frac_s        - mass fraction of dust
L00054  !====================================================================================
L00055  
```

> 讲解：①**入参即物理**：u10/v10（10 m 风）、smois/erod（土壤湿度与可蚀性分数——**erod 从 wrfinput 读入**，按沙/粉/黏三类）、vegfra/albbck（植被遮蔽与背景反照率——反照率用于识别沙漠样格点放大可蚀性）、dx/g（格距与重力）；②输出只有一个标量场 **nifa2d——尘排放以数浓度为单位（#/kg/s）直接进 QNIFA**（Thompson 的凝结核预报量），这是「沙尘→CCN→微物理→辐射」全链条的入口；③局部量注释给出完整账本（bems 逐 bin 排放、totalemis 0.1–10 μm 半径段 μg/m²/s、gwet=土壤湿度/孔隙度）；④依赖 module_data_gocart_dust 的 porosity/ch_dust/frac_s。

<!-- code_extract code_extract.py v1.2
source: phys/module_data_gocart_dust.F
ranges: L1-L39
file_lines: 39
file_md5: bff8d04c034536cbe8fac7b882533d43
display: line-numbered (strip L-prefix and !file: line to restore)
range_md5: bff8d04c034536cbe8fac7b882533d43
seg_lines: 39
-->

```fortran
!file: phys/module_data_gocart_dust.F    L1-L39
L00001  Module module_data_gocart_dust
L00002    INTEGER, PARAMETER :: ndust=5,ndcls=3,ndsrc=1,maxstypes=100
L00003    INTEGER, PARAMETER :: ngsalt=9
L00004  ! GAC-->
L00005  ! 20130219 - Drypoint no longer needed.  Use NOAA porosity for all schemes to
L00006  ! allow use of AFWA dust scheme by all LSMs, not just NOAA and RUC.
L00007  !  real, dimension (maxstypes) :: drypoint
L00008  !  real, dimension (maxstypes) :: porosity
L00009    real, dimension (19), PARAMETER :: porosity=(/0.339, 0.421, 0.434, 0.476, 0.476, 0.439, &
L00010                                                  0.404, 0.464, 0.465, 0.406, 0.468, 0.468, &
L00011                                                  0.439, 1.000, 0.200, 0.421, 0.468, 0.200, &
L00012                                                  0.339/)
L00013  ! <--GAC
L00014  
L00015    REAL :: ch_dust(ndust,12)
L00016    REAL,    PARAMETER :: dyn_visc = 1.5E-5
L00017  !  real*8, DIMENSION (5), PARAMETER :: den_dust(5)=(/2500.,2650.,2650.,2650.,2650./)
L00018    real*8, DIMENSION (5)            :: den_dust(5)=(/2500.,2650.,2650.,2650.,2650./)
L00019    real*8, DIMENSION (5), PARAMETER :: reff_dust(5)=(/0.73D-6,1.4D-6,2.4D-6,4.5D-6,8.0D-6/)
L00020    INTEGER, DIMENSION (5), PARAMETER :: ipoint(5)=(/3,2,2,2,2/)
L00021    REAL, DIMENSION (5), PARAMETER :: frac_s(5)=(/0.1,0.25,0.25,0.25,0.25/)
L00022  
L00023    real*8, DIMENSION (ngsalt), PARAMETER :: reff_salt=(/0.71D-6,1.37D-6,2.63D-6,5.00D-6,9.50D-6,18.1D-6,34.5D-6,65.5D-6,125.D-6/)
L00024    real*8, DIMENSION (ngsalt), PARAMETER :: den_salt=(/2500.,2650.,2650.,2650.,2650.,2650.,2650.,2650.,2650./)
L00025    INTEGER, DIMENSION (ngsalt), PARAMETER :: spoint=(/1,2,2,2,2,2,3,3,3/)  ! 1 Clay, 2 Silt, 3 Sand
L00026    real*8, DIMENSION (ngsalt), PARAMETER :: frac_salt=(/1.,0.2,0.2,0.2,0.2,0.2,0.333,0.333,0.333/)
L00027  
L00028    real*8, DIMENSION (ndust), PARAMETER :: distr_dust=(/1.074D-1,1.012D-1,2.078D-1,4.817D-1,1.019D-1/)
L00029  ! real*8, DIMENSION (ndust), PARAMETER :: lo_dust=(/0.1D-6,1.0D-6,1.8D-6,3.0D-6,6.0D-6/)
L00030  ! real*8, DIMENSION (ndust), PARAMETER :: up_dust=(/1.0D-6,1.8D-6,3.0D-6,6.0D-6,10.0D-6/)
L00031  
L00032    !GOCART bins radii ranges
L00033    real*8, DIMENSION (5), PARAMETER :: ra_dust(5)=(/1.d-1,1.0d0,1.8d0,3.0d0,6.0d0/)
L00034    real*8, DIMENSION (5), PARAMETER :: rb_dust(5)=(/1.0d0,1.8d0,3.0d0,6.0d0,10.0d0/)
L00035  
L00036  
L00037  END Module module_data_gocart_dust
L00038  
L00039  
```

> 讲解：GOCART 数据底座全文（39 行；**本文件是文库 32 个源文件中唯一的 CRLF 行尾**——归一化后抽取，字节 md5 936c5881e15ea3b0e99f677aec11f984 为 fp_files 按原始字节计，块指纹为归一化口径）：①**五 bins 尘**（ndust=5）：有效半径 reff 0.73–8.0 μm、密度 2500/2650 kg/m³、质量分数 frac_s 0.1/0.25×4、半径区间 ra/rb（0.1–10 μm）、谱分布 distr_dust；②**孔隙度 19 类表**（porosity，对应 STAS 土壤类；2013-02-19 注：drypoint 废弃、统一用 NOAA 孔隙度让 AFWA 尘方案适配所有 LSM——**与 noahlsm 的 MAXSMC 表同值不同源**，改土壤参数时两处同步）；③ch_dust(ndust,12) 逐月风蚀系数（可调经验常数）、dyn_visc 空气动力粘滞；④**海盐九 bins（ngsalt=9）**：reff 0.71–125 μm、按 Clay/Silt/Sand 三类源指针——尘模块顺带携带海盐参数（AFWA 起尘方案家族）；⑤ndcls=3（沙/粉/黏三类源类型）、maxstypes=100。

## 四、主体与改造入口

1. **bulk_dust_emis 主体（L56–L187，未录）**：GOCART 型排放公式——w10m=|V10|+风阵性订正、阈值摩擦速度、gw 湿度抑制、逐 bin 谱分配（distr_dust）、逐格质量守恒换算 #/kg/s；改起尘物理（如 MB97 替代 GOCART）就在这一段。
2. **erod 场**：wrfinput 输入——换可蚀性数据集（如高分辨率土壤格点）走 geogrid→real 链（ch07）。
3. **与化学路线分流**：本方案输出 QNIFA（数浓度），WRF_CHEM 的 gocart 输出质量混合比（chem 数组）——两条沙尘线不能混读。

## 五、上下游链接

- 下游：[code_21_module_microphysics_driver.md](code_21_module_microphysics_driver.md)（QNIFA 演变）、[code_20_module_radiation_driver.md](code_20_module_radiation_driver.md)（aer_opt=3 的 gt_aod）
- 教材正文：[ch13_microphysics_family.md](../ch13_microphysics_family.md)
