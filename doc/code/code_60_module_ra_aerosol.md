# code_60 — 短波气溶胶光学预处理器（module_ra_aerosol.F：AOD@550 展开成方案波段）

## 一、版本指纹

| 源文件 | 行数 | md5（整文件，按字节） |
|---|---|---|
| phys/module_ra_aerosol.F | 1470 | e253705336af00334f01b6a1a8af8f49 |

- 抽取工具：workspace/scripts/code_extract.py v1.2，2026-10-12；块首指纹注释自带 range_md5。
- 收录分级（C）：头部注记 + 两个主入口签名头段；十个单元的接口索引见 §四。WRF-CMAQ/化学路线的气溶胶光学不在此文件（见 code_06 §五的 RRTMG_SWRAD 内嵌段）。

## 二、定位

一句话：**aer_opt=2 路线的谱展开器**——把「550 nm AOD + Angstrom 指数 + SSA + 不对称因子」四个（多为 2D 的）输入量，按气溶胶类型与相对湿度展开成 Goddard 11 波段或 RRTMG_SW 14 波段的 3D 光学（tauaer/ssaaer/asyaer）；作者 Jose A. Ruiz-Arias（2012-11 起，2013-12 并入 WRF v3.6 正式版）。

**谁在调它**：radiation_driver 的 swrad_aerosol_select/swrad_aerosol_select2 两处（[code_20_module_radiation_driver.md](code_20_module_radiation_driver.md) §五），只服务 GODDARD_SW 与 RRTMG_SW 系方案。

## 三、头部注记与两个主入口头段

<!-- code_extract code_extract.py v1.2
source: phys/module_ra_aerosol.F
ranges: L1-L64
file_lines: 1470
file_md5: e253705336af00334f01b6a1a8af8f49
display: line-numbered (strip L-prefix and !file: line to restore)
range_md5: 94804d75437b668ea06098afab22c1da
seg_lines: 64
-->

```fortran
!file: phys/module_ra_aerosol.F    L1-L64
L00001  ! Aerosol optical properties from AOD at 550 nm, aerosol type and relative humidity
L00002  ! Author: Jose A. Ruiz-Arias
L00003  ! Init date: 11/2012
L00004  !
L00005  ! Changes:
L00006  !    12/2012, jararias: re-inception using aer_*_opt and aer_*_val options
L00007  ! 16/07/2013, jararias: Angstrom exponent limited to values greater than -0.3. Personal
L00008  !                       communication con Chris Gueymard
L00009  ! 16/07/2013, jararias: Added generation of mean values of angexp, ssa and asy between 0.4 um
L00010  !                       and 1 um to be promoted to the wrfout when parameterization is used (*_opt=3)
L00011  ! 12/2013, jararias: integration in the official WRFv3.6
L00012  
L00013  module module_ra_aerosol
L00014  
L00015  ! global variables
L00016  
L00017  contains
L00018  
L00019  
L00020  !--------------------------------------------------------------
L00021  !       INDICES CONVENTION
L00022  !--------------------------------------------------------------       
L00023  !       kms:kme define the range for full-level indices
L00024  !       kts:kte define the range for half-level indices
L00025  !       
L00026  !       kms=1 is the first full level at surface
L00027  !       kts=1 is the first half level at surface
L00028  !       
L00029  !       kme is the last full level at toa
L00030  !       kte is the last half level at toa
L00031  !       
L00032  !       There is one more full level than half levels.
L00033  !       Therefore, kme=kte+1. I checked it in one of my
L00034  !       simulations:
L00035  !       
L00036  !         namelist.input:
L00037  !              s_vert=1  e_vert=28        
L00038  !         code:
L00039  !              kms= 1    kts= 1
L00040  !              kms=28    kte=27
L00041  !       
L00042  !       In the vertical dimension there is no tiling for
L00043  !       parallelization as in the horizontal dimensions.
L00044  !       For i-dim and j-dim, the t-indices define the
L00045  !       range of indices over which each tile runs.
L00046  !--------------------------------------------------------------
L00047  !
L00048  !  namelist options:
L00049  !    aer_aod550_opt = [1,2] : 
L00050  !        1 = input constant value for AOD at 550 nm from namelist. 
L00051  !            In this case, the value is read from aer_aod550_val; 
L00052  !        2 = input value from auxiliary input 15. It is a time-varying 2D grid in netcdf wrf-compatible 
L00053  !            format. The default operation is aer_aod550_opt=1 and aer_aod550_val=0.12
L00054  !    aer_angexp_opt = [1,2,3] : 
L00055  !        1 = input constant value for Angstrom exponent from namelist. In this case, the value is read 
L00056  !            from aer_angexp_val; 
L00057  !        2 = input value from auxiliary input 15, as in aer_aod550_opt; 
L00058  !        3 = Angstrom exponent value estimated from the aerosol type defined in aer_type, and modulated 
L00059  !            with the RH in WRF. Default operation is aer_angexp_opt = 1, and aer_angexp_val=1.3.
L00060  !    aer_ssa_opt and aer_asy_opt are similar to aer_angexp_opt.
L00061  !
L00062  !    aer_type = [1,2,3] : 1 for rural, 2 is urban and 3 is maritime.
L00063  !--------------------------------------------------------------
L00064  
```

> 讲解：①头部变更史即功能史：Angstrom 指数下限 −0.3（Gueymard 私人通信——负 Angstrom 意味着消光随波长增大，物理上罕见）、_opt=3 时把 angexp/ssa/asy 的 0.4–1 μm 均值提升到 wrfout（太阳能应用的验证通道）；②**垂直索引约定自查段**（kms/kme 整层 vs kts/kte 半层，kme=kte+1）——作者留了 e_vert=28 的实测验证，是 WRF 垂直索引教学的好例子；③namelist 全景：aer_aod550_opt=1（常数，默认 0.12）/2（auxinput15 时变 2D 场）、aer_angexp_opt/ssa_opt/asy_opt 三选（1 常数/2 auxinput/3 按类型+RH 参数化）、**aer_type=1 农村/2 城市/3 海洋**——aer_type 只在 opt=3 的参数化分支用。

<!-- code_extract code_extract.py v1.2
source: phys/module_ra_aerosol.F
ranges: L65-L115
file_lines: 1470
file_md5: e253705336af00334f01b6a1a8af8f49
display: line-numbered (strip L-prefix and !file: line to restore)
range_md5: 264963db87aeb9226a2c574265e8a92a
seg_lines: 51
-->

```fortran
!file: phys/module_ra_aerosol.F    L65-L115
L00065  subroutine calc_aerosol_goddard_sw(ht,dz8w,p,t3d,qv3d,aer_type,                               &
L00066                                     aer_aod550_opt, aer_angexp_opt, aer_ssa_opt, aer_asy_opt,  &
L00067                                     aer_aod550_val, aer_angexp_val, aer_ssa_val, aer_asy_val,  &
L00068                                     aod5502d, angexp2d, aerssa2d, aerasy2d,                    &
L00069                                     ims,ime,jms,jme,kms,kme,its,ite,jts,jte,kts,kte,           &
L00070                                     tauaer, ssaaer, asyaer                                     )
L00071  
L00072      USE module_wrf_error , ONLY : wrf_err_message
L00073      
L00074      implicit none
L00075  
L00076      ! constants
L00077      integer, parameter :: N_BANDS=11
L00078  
L00079      ! mid-band wavelength / 550. nm
L00080      real :: lower_wvl(N_BANDS),upper_wvl(N_BANDS)
L00081      integer :: kk
L00082      data (lower_wvl(kk),kk=1,N_BANDS) /0.175,0.225,0.245,0.280,0.295,0.310,0.325,0.400,0.700,1.220,2.270/
L00083      data (upper_wvl(kk),kk=1,N_BANDS) /0.225,0.245,0.280,0.295,0.310,0.325,0.400,0.700,1.220,2.270,10.00/
L00084  
L00085      ! I/O variables
L00086      integer, intent(in) :: ims,ime,jms,jme,kms,kme, &
L00087                             its,ite,jts,jte,kts,kte
L00088      real, dimension(ims:ime, kms:kme, jms:jme), intent(in) :: p,     & ! pressure (Pa)
L00089                                                                t3d,   & ! temperature (K)
L00090                                                                dz8w,  & ! dz between full levels (m)
L00091                                                                qv3d     ! water vapor mixing ratio (kg/kg)
L00092      integer, intent(in) :: aer_type
L00093      integer, intent(in) :: aer_aod550_opt, aer_angexp_opt, aer_ssa_opt, aer_asy_opt
L00094      real, intent(in)    :: aer_aod550_val, aer_angexp_val, aer_ssa_val, aer_asy_val
L00095  
L00096      real, dimension(ims:ime, jms:jme),                     intent(in)    :: ht
L00097      real, dimension(ims:ime, jms:jme),           optional, intent(inout) :: aod5502d, angexp2d, aerssa2d, aerasy2d
L00098      real, dimension(ims:ime, kms:kme, jms:jme, 1:N_BANDS), intent(inout) :: tauaer, ssaaer, asyaer
L00099  
L00100      ! local variables
L00101      integer :: i,j,k,nb
L00102      real :: aod_rate,angexp_val,x,xy,xx
L00103      real, dimension(ims:ime, jms:jme, 1:N_BANDS) :: aod550spc
L00104      real, dimension(ims:ime, kms:kme, jms:jme)   :: rh  ! relative humidity
L00105  
L00106      call calc_relative_humidity(p,t3d,qv3d,                 &
L00107                                  ims,ime,jms,jme,kms,kme,    &
L00108                                  its,ite,jts,jte,kts,kte,    &
L00109                                  rh                          )
L00110  
L00111      aer_aod550_opt_select: select case(aer_aod550_opt)
L00112         !case(0)
L00113         ! reserved for climatology
L00114         case(1)
L00115            if (aer_aod550_val .lt. 0 ) then
```

> 讲解：Goddard 短波入口头段：N_BANDS=11 与波段边界表（0.175–10 μm 的 11 段划分）；第一步统一调 calc_relative_humidity（从 p/t/qv 算 RH——RH 用于 opt=3 的吸湿增长参数化）；aer_aod550_opt 分派起点（case(1) 负值报错）。tauaer/ssaaer/asyaer 维度 (ims:ime, kms:kme, jms:jme, 1:11)——注意第四维起点是 1 不是 0，与 radiation_driver 的 allocate (…,1:11) 一致。

<!-- code_extract code_extract.py v1.2
source: phys/module_ra_aerosol.F
ranges: L397-L472
file_lines: 1470
file_md5: e253705336af00334f01b6a1a8af8f49
display: line-numbered (strip L-prefix and !file: line to restore)
range_md5: 75d43fa5b4ed9caf917f0b6f07f16bb7
seg_lines: 76
-->

```fortran
!file: phys/module_ra_aerosol.F    L397-L472
L00397  subroutine calc_aerosol_rrtmg_sw(ht,dz8w,p,t3d,qv3d,aer_type,                               &
L00398                                   aer_aod550_opt, aer_angexp_opt, aer_ssa_opt, aer_asy_opt,  &
L00399                                   aer_aod550_val, aer_angexp_val, aer_ssa_val, aer_asy_val,  &
L00400                                   aod5502d, angexp2d, aerssa2d, aerasy2d,                    &
L00401                                   ims,ime,jms,jme,kms,kme,its,ite,jts,jte,kts,kte,           &
L00402                                   tauaer, ssaaer, asyaer, aod5503d                           )
L00403  
L00404      USE module_wrf_error , ONLY : wrf_err_message
L00405      
L00406      implicit none
L00407  
L00408      ! constants
L00409      integer, parameter :: N_BANDS=14
L00410      ! local index variables
L00411      integer :: i,j,k,nb
L00412  
L00413      real :: lower_wvl(N_BANDS),upper_wvl(N_BANDS)
L00414      data (lower_wvl(i),i=1,N_BANDS) /3.077,2.500,2.150,1.942,1.626,1.299,1.242,0.7782,0.6250,0.4415,0.3448,0.2632,0.2000,3.846/
L00415      data (upper_wvl(i),i=1,N_BANDS) /3.846,3.077,2.500,2.150,1.942,1.626,1.299,1.2420,0.7782,0.6250,0.4415,0.3448,0.2632,12.195/
L00416  
L00417      ! I/O variables
L00418      real, dimension(ims:ime, kms:kme, jms:jme), intent(in) :: p,     & ! pressure (Pa)
L00419                                                                t3d,   & ! temperature (K)
L00420                                                                dz8w,  & ! dz between full levels (m)
L00421                                                                qv3d     ! water vapor mixing ratio (kg/kg)
L00422      integer, intent(in) :: ims,ime,jms,jme,kms,kme, &
L00423                             its,ite,jts,jte,kts,kte
L00424      integer, intent(in) :: aer_type
L00425      integer, intent(in) :: aer_aod550_opt, aer_angexp_opt, aer_ssa_opt, aer_asy_opt
L00426      real, intent(in)    :: aer_aod550_val, aer_angexp_val, aer_ssa_val, aer_asy_val
L00427  
L00428      real, dimension(ims:ime, jms:jme), intent(in)    :: ht
L00429      real, dimension(ims:ime, jms:jme), optional, intent(inout) :: aod5502d, angexp2d, aerssa2d, aerasy2d
L00430      real, dimension(ims:ime, kms:kme, jms:jme, 1:N_BANDS), intent(inout) :: tauaer, ssaaer, asyaer
L00431  
L00432      real, dimension(ims:ime, kms:kme, jms:jme), optional, intent(in) :: aod5503d   ! trude
L00433  
L00434      ! local variables
L00435      real :: angexp_val,aod_rate,x,xy,xx
L00436      real, dimension(ims:ime, jms:jme, 1:N_BANDS) :: aod550spc
L00437      real, dimension(ims:ime, kms:kme, jms:jme, 1:N_BANDS) :: aod550spc3d    !  trude
L00438      real, dimension(ims:ime, kms:kme, jms:jme)   :: rh  ! relative humidity
L00439  
L00440      call calc_relative_humidity(p,t3d,qv3d,                 &
L00441                                  ims,ime,jms,jme,kms,kme,    &
L00442                                  its,ite,jts,jte,kts,kte,    &
L00443                                  rh                          )
L00444  
L00445      aer_aod550_opt_select: select case(aer_aod550_opt)
L00446         !case(0)
L00447         ! reserved for climatology
L00448         case(1)
L00449            if (aer_aod550_val .lt. 0) then
L00450               write(wrf_err_message,'("aer_aod550_val must be positive. Negative value ",F7.4," found")') aer_aod550_val
L00451               call wrf_error_fatal(wrf_err_message)
L00452            end if
L00453            write( wrf_err_message, '("aer_aod550_opt=",I1,": AOD@550 nm fixed to value ",F6.3)') aer_aod550_opt,aer_aod550_val
L00454            call wrf_debug(100, wrf_err_message )
L00455            do j=jts,jte
L00456               do i=its,ite
L00457                  aod5502d(i,j)=aer_aod550_val
L00458               end do
L00459            end do
L00460  
L00461         case(2) 
L00462            if (.not.(present(aod5502d))) then
L00463               write(wrf_err_message,*) 'Expected gridded total AOD@550 nm, but it is not in the radiation driver'
L00464               call wrf_error_fatal(wrf_err_message)
L00465            end if
L00466            if (minval(aod5502d) .lt. 0) then
L00467               call wrf_error_fatal('AOD@550 must be positive. Negative value(s) found in auxinput')
L00468            end if
L00469            write( wrf_err_message, '("aer_aod550_opt=",I1,": AOD@550 nm read from auxinput (min=",F6.3," max=",F6.3,")")') &
L00470                                    aer_aod550_opt,minval(aod5502d),maxval(aod5502d)
L00471            call wrf_debug(100, wrf_err_message )
L00472  
```

> 讲解：RRTMG 短波入口头段：N_BANDS=14 与波段边界表（3.077–12.195 μm 的 14 段——即 RRTMG 波段 16–29 的波长界，逆序排列从长波端开始）；多一个 **aod5503d 可选入参（trude）**——aer_opt=3 的 3D AOD 通道（来自 gt_aod 的 QNWFA/QNIFA 预报，见 code_20 §五），有它时 550 nm AOD 逐层给定而不用 2D 场；case(1)/case(2) 的输入校验（负值/缺失 auxinput 都 wrf_error_fatal）并打印 min/max 诊断。

## 四、单元接口索引（10 单元）

| 单元 | 行段 | 功能 |
|---|---|---|
| calc_aerosol_goddard_sw | L65–L394 | 11 波段展开（Goddard SW 配套） |
| calc_aerosol_rrtmg_sw | L397–L766 | 14 波段展开（RRTMG_SW 配套，多 aod5503d 入口） |
| calc_spectral_aod_goddard_sw | L769–L851 | 谱 AOD：Angstrom 律按波段中点波长展开 |
| calc_spectral_ssa_goddard_sw | L853–L935 | 谱 SSA：按类型查表+RH 吸湿修正 |
| calc_spectral_asy_goddard_sw | L937–L1019 | 谱不对称因子：同上 |
| calc_spectral_aod_rrtmg_sw | L1021–L1166 | 14 波段版谱 AOD（多 3D 入口） |
| calc_spectral_ssa_rrtmg_sw | L1168–L1274 | 14 波段版谱 SSA |
| calc_spectral_asy_rrtmg_sw | L1276–L1382 | 14 波段版谱不对称因子 |
| aod_profiler | L1384–L1435 | AOD 的垂直廓线分配（指数衰减型） |
| calc_relative_humidity | L1437–L1467 | 由 p/t/qv 算 RH |

> 讲解：结构高度对称——两个主入口各自调三个 calc_spectral_*（AOD/SSA/ASY）与 aod_profiler；SSA/ASY 的「类型查表+RH 修正」是 opt=3 的核心（rural/urban/maritime 三套表内嵌在 calc_spectral_ 系里）；aod_profiler 把柱 AOD 分配到层（气溶胶集中在边界层的指数型假设）。

## 五、改造入口

1. **加气溶胶类型**：aer_type 的三套谱表内嵌在 calc_spectral_ssa/asy 系——加第四类（如沙尘）改表+分支。
2. **换垂直廓线**：aod_profiler 的指数型——用观测/模式气溶胶廓线替换的入口。
3. **谱展开律**：calc_spectral_aod_* 的 Angstrom 律与 −0.3 下限——用实测谱或 Winnokower 型参数化的挂点。
4. **aer_opt=3 联动**：aod5503d 入口与 radiation_driver 的 gt_aod（QNWFA/QNIFA）链路——沙尘/烟雾预报实验的通道。

## 六、上下游链接

- 上游驱动：[code_20_module_radiation_driver.md](code_20_module_radiation_driver.md)（swrad_aerosol_select 两处挂点、gt_aod 的 3D AOD）
- 下游方案：[code_06_module_ra_rrtmg_sw.md](code_06_module_ra_rrtmg_sw.md)（tauaer_sw 14 波段消费方）、Goddard SW（11 波段）
- 教材正文：[ch12_radiation_family.md](../ch12_radiation_family.md)、[ch20_modifying_wrf.md](../ch20_modifying_wrf.md)
