# code_15 — BEP 单独版（module_sf_bep.F 全文精读）

## 一、版本指纹

| 源文件 | 行数 | md5（整文件，按字节） |
|---|---|---|
| phys/module_sf_bep.F | 3536 | 5f74b56a221ca4ec69320a09ad3f9c3e |

- 抽取工具：workspace/scripts/code_extract.py v1.2，2026-10-12；块首指纹注释自带 range_md5。
- 本篇 A 级全文（32 单元全收）。约四分之三单元与共享底座 module_sf_bep_bem.F（[code_14a](code_14a_module_sf_bep_bem.md)/[code_14b](code_14b_module_sf_bep_bem.md)）**逐行同源**——那些单元的讲解给差异注记并回指 14a/14b，正文不重复；BEP 独有部分（主入口、简化柱求解、angle）展开讲。

## 二、定位

一句话：sf_urban_physics=1（BEP 单开、无 BEM）时的城市冠层方案主体——比 bep_bem 少了建筑能量模型（室内温度/空调/通风/窗户/绿屋顶/PV/水分收支），保留双网格拖曳与峡谷辐射的全部骨架。

**谁在调它**：module_sf_urban.F 的 urban（BEPSCHEME 分支）调 BEP；pbl_driver 经 flag_bep 消费 a_*/b_* 源项（[code_22_module_pbl_driver.md](code_22_module_pbl_driver.md)）。教材锚点：[ch17_urban_canopy.md](../ch17_urban_canopy.md)。

**与 bep_bem 的四大差异**（改造前必读）：

| 项 | module_sf_bep.F（本篇） | module_sf_bep_bem.F（14a/14b） |
|---|---|---|
| 拖曳系数 | 模块常数 cdrag=0.4（flux_wall 直接用） | NEW CDRAG：按建筑密度 3.32·alp^0.47 / 1.85 逐点算 |
| 固体温度 | surf_temp 一件管地面+屋顶+墙三面 | 地面 surf_temp；屋顶/墙由 BEM 内部导热管 |
| 水分/室内 | 无（无积水、无 AC、无绿屋顶） | dg/dgr 水量收支 + BEM 全套 |
| 状态数组 | tw1/tw2/trb/tgb 四件 | 另有 trv/qr/tlev/qlev/twlev/tflev/tglev 七件 |

## 三、文件头

<!-- code_extract code_extract.py v1.2
source: phys/module_sf_bep.F
ranges: L1-L61
file_lines: 3536
file_md5: 5f74b56a221ca4ec69320a09ad3f9c3e
display: line-numbered (strip L-prefix and !file: line to restore)
range_md5: db5ecefb5aab5663640e21ef93c7787e
seg_lines: 61
-->

```fortran
!file: phys/module_sf_bep.F    L1-L61
L00001  MODULE module_sf_bep
L00002  #if defined(mpas)
L00003  use mpas_atmphys_utilities, only: physics_error_fatal
L00004  #define FATAL_ERROR(M) call physics_error_fatal( M )
L00005  #else
L00006  use module_wrf_error
L00007  #define FATAL_ERROR(M) call wrf_error_fatal( M)
L00008  !USE module_model_constants
L00009  #endif
L00010   USE module_sf_urban
L00011   USE module_bep_bem_helper, ONLY: nurbm
L00012  
L00013  ! SGClarke 09/11/2008
L00014  ! Access urban_param.tbl values through calling urban_param_init in module_physics_init
L00015  ! for CASE (BEPSCHEME) select sf_urban_physics
L00016  !
L00017  ! -----------------------------------------------------------------------
L00018  !  Dimension for the array used in the BEP module
L00019  ! -----------------------------------------------------------------------
L00020        integer nurbmax         ! Maximum number of urban classes    
L00021        parameter (nurbmax=11)
L00022  
L00023        integer ndm             ! Maximum number of street directions 
L00024        parameter (ndm=2)
L00025  
L00026        integer nz_um           ! Maximum number of vertical levels in the urban grid
L00027        parameter(nz_um=18)
L00028  
L00029        integer ng_u            ! Number of grid levels in the ground
L00030        parameter (ng_u=10)
L00031        integer nwr_u            ! Number of grid levels in the walls or roofs
L00032        parameter (nwr_u=10)
L00033  
L00034        real dz_u                 ! Urban grid resolution
L00035        parameter (dz_u=5.)
L00036  
L00037  ! The change of ng_u, nwr_u should be done in agreement with the block data
L00038  !  in the routine "surf_temp" 
L00039  ! -----------------------------------------------------------------------
L00040  !  Constant used in the BEP module
L00041  ! -----------------------------------------------------------------------
L00042             
L00043        real vk                 ! von Karman constant
L00044        real g_u                  ! Gravity acceleration
L00045        real pi                 !
L00046        real r                  ! Perfect gas constant
L00047        real cp_u                 ! Specific heat at constant pressure
L00048        real rcp_u                !
L00049        real sigma              !
L00050        real p0                 ! Reference pressure at the sea level
L00051        real cdrag              ! Drag force constant
L00052        parameter(vk=0.40,g_u=9.81,pi=3.141592653,r=287.,cp_u=1004.)        
L00053        parameter(rcp_u=r/cp_u,sigma=5.67e-08,p0=1.e+5,cdrag=0.4)
L00054  
L00055  ! -----------------------------------------------------------------------     
L00056  
L00057  
L00058  
L00059  
L00060     CONTAINS
L00061   
```

> 讲解：USE 清单只有 module_sf_urban（TBL 参数库）与 bep_bem_helper（nurbm）——**不 USE module_sf_bem**，这是「BEP 单独版」的编译级证据；维度常数与 bep_bem 相同（nurbmax=11、ndm=2、nz_um=18、dz_u=5 m、ng_u=nwr_u=10）但**没有** BEM 的 nf_u/ngb_u/ngr_u/nbui_max（无楼层/楼下地基/绿屋顶层/建筑型维度）；常数区多一个 cdrag=0.4——街道拖曳系数在此是常数而非参数化。

## 四、主入口 BEP（全文）

<!-- code_extract code_extract.py v1.2
source: phys/module_sf_bep.F
ranges: L62-L585
file_lines: 3536
file_md5: 5f74b56a221ca4ec69320a09ad3f9c3e
display: line-numbered (strip L-prefix and !file: line to restore)
range_md5: 04293c17325d7a139c9d42bf0dcf0751
seg_lines: 524
label: subroutine BEP
-->

```fortran
!file: phys/module_sf_bep.F    L62-L585    (subroutine BEP)
L00062        subroutine BEP(FRC_URB2D,UTYPE_URB2D,itimestep,dz8w,dt,u_phy,v_phy,      &
L00063                        th_phy,rho,p_phy,swdown,glw,                    &
L00064                        gmt,julday,xlong,xlat,                          &
L00065                        declin_urb,cosz_urb2d,omg_urb2d,                &
L00066                        num_urban_ndm,  urban_map_zrd,  urban_map_zwd, urban_map_gd, &
L00067                         urban_map_zd,  urban_map_zdf,   urban_map_bd, urban_map_wd, &
L00068                        urban_map_gbd,  urban_map_fbd,                               &
L00069                         num_urban_hi,                                               &
L00070                        trb_urb4d,tw1_urb4d,tw2_urb4d,tgb_urb4d,        &
L00071                        sfw1_urb3d,sfw2_urb3d,sfr_urb3d,sfg_urb3d,      &
L00072                        lp_urb2d,hi_urb2d,lb_urb2d,hgt_urb2d,           &
L00073                        a_u,a_v,a_t,a_e,b_u,b_v,                        &
L00074                        b_t,b_e,b_q,dlg,dl_u,sf,vl,                     &
L00075                        rl_up,rs_abs,emiss,grdflx_urb,                  &
L00076                        ids,ide, jds,jde, kds,kde,                      &
L00077                        ims,ime, jms,jme, kms,kme,                      &
L00078                        its,ite, jts,jte, kts,kte)                    
L00079  
L00080        implicit none
L00081  
L00082  !------------------------------------------------------------------------
L00083  !     Input
L00084  !------------------------------------------------------------------------
L00085     INTEGER ::                       ids,ide, jds,jde, kds,kde,  &
L00086                                      ims,ime, jms,jme, kms,kme,  &
L00087                                      its,ite, jts,jte, kts,kte,  &
L00088                                      itimestep
L00089   
L00090  
L00091     REAL, DIMENSION( ims:ime, kms:kme, jms:jme )::   DZ8W
L00092     REAL, DIMENSION( ims:ime, kms:kme, jms:jme )::   P_PHY
L00093     REAL, DIMENSION( ims:ime, kms:kme, jms:jme )::   RHO
L00094     REAL, DIMENSION( ims:ime, kms:kme, jms:jme )::   TH_PHY
L00095     REAL, DIMENSION( ims:ime, kms:kme, jms:jme )::   T_PHY
L00096     REAL, DIMENSION( ims:ime, kms:kme, jms:jme )::   U_PHY
L00097     REAL, DIMENSION( ims:ime, kms:kme, jms:jme )::   V_PHY
L00098     REAL, DIMENSION( ims:ime, kms:kme, jms:jme )::   U
L00099     REAL, DIMENSION( ims:ime, kms:kme, jms:jme )::   V
L00100     REAL, DIMENSION( ims:ime , jms:jme )        ::   GLW
L00101     REAL, DIMENSION( ims:ime , jms:jme )        ::   swdown
L00102     REAL, DIMENSION( ims:ime, jms:jme )         ::   UST
L00103     INTEGER, DIMENSION( ims:ime , jms:jme ), INTENT(IN )::   UTYPE_URB2D
L00104     REAL, DIMENSION( ims:ime , jms:jme ), INTENT(IN )::   FRC_URB2D
L00105     REAL, INTENT(IN  )   ::                                   GMT 
L00106     INTEGER, INTENT(IN  ) ::                               JULDAY
L00107     REAL, DIMENSION( ims:ime, jms:jme ),                           &
L00108           INTENT(IN   )  ::                           XLAT, XLONG
L00109     REAL, INTENT(IN) :: DECLIN_URB
L00110     REAL, DIMENSION( ims:ime, jms:jme ), INTENT(IN) :: COSZ_URB2D
L00111     REAL, DIMENSION( ims:ime, jms:jme ), INTENT(IN) :: OMG_URB2D
L00112     INTEGER, INTENT(IN  ) :: num_urban_ndm
L00113     INTEGER, INTENT(IN  ) :: urban_map_zrd
L00114     INTEGER, INTENT(IN  ) :: urban_map_zwd
L00115     INTEGER, INTENT(IN  ) :: urban_map_gd
L00116     INTEGER, INTENT(IN  ) :: urban_map_zd
L00117     INTEGER, INTENT(IN  ) :: urban_map_zdf
L00118     INTEGER, INTENT(IN  ) :: urban_map_bd
L00119     INTEGER, INTENT(IN  ) :: urban_map_wd
L00120     INTEGER, INTENT(IN  ) :: urban_map_gbd
L00121     INTEGER, INTENT(IN  ) :: urban_map_fbd
L00122     INTEGER, INTENT(IN  ) :: num_urban_hi
L00123     REAL, DIMENSION( ims:ime, 1:urban_map_zrd, jms:jme ), INTENT(INOUT) :: trb_urb4d
L00124     REAL, DIMENSION( ims:ime, 1:urban_map_zwd, jms:jme ), INTENT(INOUT) :: tw1_urb4d
L00125     REAL, DIMENSION( ims:ime, 1:urban_map_zwd, jms:jme ), INTENT(INOUT) :: tw2_urb4d
L00126     REAL, DIMENSION( ims:ime, 1:urban_map_gd , jms:jme ), INTENT(INOUT) :: tgb_urb4d
L00127     REAL, DIMENSION( ims:ime, 1:urban_map_wd , jms:jme ), INTENT(INOUT) :: sfw1_urb3d
L00128     REAL, DIMENSION( ims:ime, 1:urban_map_wd , jms:jme ), INTENT(INOUT) :: sfw2_urb3d
L00129     REAL, DIMENSION( ims:ime, 1:urban_map_zdf, jms:jme ), INTENT(INOUT) :: sfr_urb3d
L00130     REAL, DIMENSION( ims:ime, 1:num_urban_ndm, jms:jme ), INTENT(INOUT) :: sfg_urb3d
L00131     REAL, DIMENSION( ims:ime, 1:num_urban_hi, jms:jme ), INTENT(IN) :: hi_urb2d
L00132     REAL, DIMENSION( ims:ime,jms:jme), INTENT(IN) :: lp_urb2d
L00133     REAL, DIMENSION( ims:ime,jms:jme), INTENT(IN) :: lb_urb2d
L00134     REAL, DIMENSION( ims:ime,jms:jme), INTENT(IN) :: hgt_urb2d
L00135  
L00136  !      integer nx,ny,nz              ! Number of points in the mesocsale grid
L00137        real z(ims:ime,kms:kme,jms:jme)            ! Vertical coordinates
L00138        REAL, INTENT(IN )::   DT      ! Time step
L00139  !      real zr(ims:ime,jms:jme)                ! Solar zenith angle
L00140  !      real deltar(ims:ime,jms:jme)            ! Declination of the sun
L00141  !      real ah(ims:ime,jms:jme)                ! Hour angle
L00142  !      real rs(ims:ime,jms:jme)                ! Solar radiation
L00143  !------------------------------------------------------------------------
L00144  !     Output
L00145  !------------------------------------------------------------------------ 
L00146  !      real tsk(ims:ime,jms:jme)           ! Average of surface temperatures (roads and roofs)
L00147  !
L00148  !    Implicit and explicit components of the source and sink terms at each levels,
L00149  !     the fluxes can be computed as follow: FX = A*X + B   example: t_fluxes = a_t * pt + b_t
L00150        real a_u(ims:ime,kms:kme,jms:jme)         ! Implicit component for the momemtum in X-direction (center)
L00151        real a_v(ims:ime,kms:kme,jms:jme)         ! Implicit component for the momemtum in Y-direction (center)
L00152        real a_t(ims:ime,kms:kme,jms:jme)         ! Implicit component for the temperature
L00153        real a_e(ims:ime,kms:kme,jms:jme)         ! Implicit component for the TKE
L00154        real b_u(ims:ime,kms:kme,jms:jme)         ! Explicit component for the momemtum in X-direction (center)
L00155        real b_v(ims:ime,kms:kme,jms:jme)         ! Explicit component for the momemtum in Y-direction (center)
L00156        real b_t(ims:ime,kms:kme,jms:jme)         ! Explicit component for the temperature
L00157        real b_e(ims:ime,kms:kme,jms:jme)         ! Explicit component for the TKE
L00158        real b_q(ims:ime,kms:kme,jms:jme)         ! Explicit component for the humidity
L00159        real dlg(ims:ime,kms:kme,jms:jme)         ! Height above ground (L_ground in formula (24) of the BLM paper). 
L00160        real dl_u(ims:ime,kms:kme,jms:jme)        ! Length scale (lb in formula (22) ofthe BLM paper).
L00161  ! urban surface and volumes        
L00162        real sf(ims:ime,kms:kme,jms:jme)           ! surface of the urban grid cells
L00163        real vl(ims:ime,kms:kme,jms:jme)             ! volume of the urban grid cells
L00164  ! urban fluxes
L00165        real rl_up(its:ite,jts:jte) ! upward long wave radiation
L00166        real rs_abs(its:ite,jts:jte) ! absorbed short wave radiation
L00167        real emiss(its:ite,jts:jte)  ! emissivity averaged for urban surfaces
L00168        real grdflx_urb(its:ite,jts:jte)  ! ground heat flux for urban areas
L00169  !------------------------------------------------------------------------
L00170  !     Local
L00171  !------------------------------------------------------------------------
L00172  !!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!
L00173  
L00174        real hi_urb(its:ite,1:nz_um,jts:jte)    ! Height histograms of buildings
L00175        real hi_urb1D(nz_um)                    ! Height histograms of buildings
L00176        real hb_u(nz_um)                        ! Bulding's heights
L00177        real ss_urb(nz_um)  ! Probability that a building has an height equal to z
L00178        real pb_urb(nz_um)  ! Probability that a building has an height greater or equal to z
L00179        integer nz_urb(nurbmax)                 ! Number of layer in the urban grid
L00180        integer nzurban(nurbmax)                
L00181  
L00182  !    Building parameters      
L00183        real alag_u(nurbmax)                    ! Ground thermal diffusivity [m^2 s^-1]
L00184        real alaw_u(nurbmax)                    ! Wall thermal diffusivity [m^2 s^-1]
L00185        real alar_u(nurbmax)                    ! Roof thermal diffusivity [m^2 s^-1]
L00186        real csg_u(nurbmax)                     ! Specific heat of the ground material [J m^3 K^-1]
L00187        real csw_u(nurbmax)                     ! Specific heat of the wall material [J m^3 K^-1]
L00188        real csr_u(nurbmax)                     ! Specific heat of the roof material [J m^3 K^-1]
L00189        real twini_u(nurbmax)                   ! Initial temperature inside the building's wall [K]
L00190        real trini_u(nurbmax)                   ! Initial temperature inside the building's roof [K]
L00191        real tgini_u(nurbmax)                   ! Initial road temperature
L00192  !
L00193  !   Building materials
L00194  !
L00195        real csg(ng_u)                          ! Specific heat of the ground material [J m^3 K^-1]
L00196        real csr(nwr_u)                         ! Specific heat of the roof material [J m^3 K^-1]
L00197        real csw(nwr_u)                         ! Specific heat of the wall material [J m^3 K^-1]
L00198        real alag(ng_u)                         ! Ground thermal diffusivity [m^2 s^-1]
L00199        real alaw(nwr_u)                        ! Wall thermal diffusivity [m^2 s^-1]
L00200        real alar(nwr_u)                        ! Roof thermal diffusivity [m^2 s^-1]
L00201  !
L00202  ! for twini_u, and trini_u the initial value at the deepest level is kept constant during the simulation
L00203  !
L00204  !    Radiation parameters
L00205        real albg_u(nurbmax)                    ! Albedo of the ground
L00206        real albw_u(nurbmax)                    ! Albedo of the wall
L00207        real albr_u(nurbmax)                    ! Albedo of the roof
L00208        real emg_u(nurbmax)                     ! Emissivity of ground
L00209        real emw_u(nurbmax)                     ! Emissivity of wall
L00210        real emr_u(nurbmax)                     ! Emissivity of roof
L00211  
L00212  !   fww_u,fwg_u,fgw_u,fsw_u,fsg_u are the view factors used to compute the long wave
L00213  !   and the short wave radation. 
L00214        real fww_u(nz_um,nz_um,ndm,nurbmax)       !  from wall to wall
L00215        real fwg_u(nz_um,ndm,nurbmax)             !  from wall to ground
L00216        real fgw_u(nz_um,ndm,nurbmax)             !  from ground to wall
L00217        real fsw_u(nz_um,ndm,nurbmax)             !  from sky to wall
L00218        real fws_u(nz_um,ndm,nurbmax)             !  from sky to wall
L00219        real fsg_u(ndm,nurbmax)                   !  from sky to ground
L00220  
L00221  !    Roughness parameters
L00222        real z0g_u(nurbmax)       ! The ground's roughness length
L00223        real z0r_u(nurbmax)       ! The roof's roughness length
L00224  
L00225  !    Roughness parameters
L00226        real z0(ndm,nz_um)           ! Roughness lengths "profiles"
L00227  
L00228  !    Street parameters
L00229        integer nd_u(nurbmax)     ! Number of street direction for each urban class 
L00230        real strd_u(ndm,nurbmax)  ! Street length (fix to greater value to the horizontal length of the cells)
L00231        real drst_u(ndm,nurbmax)  ! Street direction
L00232        real ws_u(ndm,nurbmax)    ! Street width
L00233        real bs_u(ndm,nurbmax)    ! Building width
L00234        real h_b(nz_um,nurbmax)   ! Bulding's heights
L00235        real d_b(nz_um,nurbmax)   ! Probability that a building has an height h_b
L00236        real ss_u(nz_um,nurbmax)  ! Probability that a building has an height equal to z
L00237        real pb_u(nz_um,nurbmax)  ! Probability that a building has an height greater or equal to z
L00238  !
L00239  !    Street parameters
L00240  !
L00241        real bs(ndm)                 ! Building width 
L00242        real ws(ndm)                 ! Street width
L00243        real drst(ndm)               ! street directions 
L00244        real strd(ndm)               ! Street lengths 
L00245        real ss(nz_um)               ! Probability to have a building with height h
L00246        real pb(nz_um)               ! Probability to have a building with an height equal
L00247  
L00248  !    Grid parameters
L00249  
L00250        integer nz_u(nurbmax)     ! Number of layer in the urban grid
L00251        
L00252        real z_u(nz_um)         ! Height of the urban grid levels
L00253  
L00254  ! 1D array used for the input and output of the routine "urban"
L00255  
L00256        real z1D(kms:kme)               ! vertical coordinates
L00257        real ua1D(kms:kme)                ! wind speed in the x directions
L00258        real va1D(kms:kme)                ! wind speed in the y directions
L00259        real pt1D(kms:kme)                ! potential temperature
L00260        real da1D(kms:kme)                ! air density
L00261        real pr1D(kms:kme)                ! air pressure
L00262        real pt01D(kms:kme)               ! reference potential temperature
L00263        real zr1D                    ! zenith angle
L00264        real deltar1D                ! declination of the sun
L00265        real ah1D                    ! hour angle (it should come from the radiation routine)
L00266        real rs1D                    ! solar radiation
L00267        real rld1D                   ! downward flux of the longwave radiation
L00268  
L00269  
L00270        real tw1D(2*ndm,nz_um,nwr_u)  ! temperature in each layer of the wall
L00271        real tg1D(ndm,ng_u)          ! temperature in each layer of the ground
L00272        real tr1D(ndm,nz_um,nwr_u)  ! temperature in each layer of the roof
L00273        real sfw1D(2*ndm,nz_um)      ! sensible heat flux from walls
L00274        real sfg1D(ndm)              ! sensible heat flux from ground (road)
L00275        real sfr1D(ndm,nz_um)      ! sensible heat flux from roofs
L00276        real sf1D(kms:kme)              ! surface of the urban grid cells
L00277        real vl1D(kms:kme)                ! volume of the urban grid cells
L00278        real a_u1D(kms:kme)               ! Implicit component of the momentum sources or sinks in the X-direction
L00279        real a_v1D(kms:kme)               ! Implicit component of the momentum sources or sinks in the Y-direction
L00280        real a_t1D(kms:kme)               ! Implicit component of the heat sources or sinks
L00281        real a_e1D(kms:kme)               ! Implicit component of the TKE sources or sinks
L00282        real b_u1D(kms:kme)               ! Explicit component of the momentum sources or sinks in the X-direction
L00283        real b_v1D(kms:kme)               ! Explicit component of the momentum sources or sinks in the Y-direction
L00284        real b_t1D(kms:kme)               ! Explicit component of the heat sources or sinks
L00285        real b_e1D(kms:kme)               ! Explicit component of the TKE sources or sinks
L00286        real dlg1D(kms:kme)               ! Height above ground (L_ground in formula (24) of the BLM paper). 
L00287        real dl_u1D(kms:kme)              ! Length scale (lb in formula (22) ofthe BLM paper)
L00288        real time_bep
L00289  ! arrays used to collapse indexes
L00290        integer ind_zwd(nz_um,nwr_u,ndm)
L00291        integer ind_gd(ng_u,ndm)
L00292        integer ind_zd(nz_um,ndm)
L00293  !
L00294        integer ix,iy,iz,iurb,id,iz_u,iw,ig,ir,ix1,iy1,k
L00295        integer it, nint
L00296        integer iii
L00297        real time_h,tempo
L00298        logical first
L00299        character(len=80) :: text
L00300        data first/.true./
L00301        save first,time_bep 
L00302  
L00303        save alag_u,alaw_u,alar_u,csg_u,csw_u,csr_u,                      &
L00304             albg_u,albw_u,albr_u,emg_u,emw_u,emr_u,                      &
L00305             z0g_u,z0r_u, nd_u,strd_u,drst_u,ws_u,bs_u,h_b,d_b,ss_u,pb_u, &
L00306             nz_u,z_u 
L00307  
L00308  !------------------------------------------------------------------------
L00309  !    Calculation of the momentum, heat and turbulent kinetic fluxes
L00310  !     produced by builgings
L00311  !
L00312  ! Reference:
L00313  ! Martilli, A., Clappier, A., Rotach, M.W.:2002, 'AN URBAN SURFACE EXCHANGE
L00314  ! PARAMETERISATION FOR MESOSCALE MODELS', Boundary-Layer Meteorolgy 104:
L00315  ! 261-304
L00316  !------------------------------------------------------------------------
L00317  !prepare the arrays to collapse indexes
L00318  
L00319        if(urban_map_zrd.lt.nz_um*ndm*nwr_u)then
L00320          write(*,*)'urban_map_zrd too small, please increase to at least ', nz_um*ndm*nwr_u
L00321          stop
L00322        endif
L00323        iii=0
L00324        do iz_u=1,nz_um
L00325        do iw=1,nwr_u
L00326        do id=1,ndm
L00327         iii=iii+1
L00328         ind_zwd(iz_u,iw,id)=iii
L00329        enddo
L00330        enddo
L00331        enddo
L00332  
L00333        iii=0
L00334        do ig=1,ng_u
L00335        do id=1,ndm
L00336         iii=iii+1
L00337         ind_gd(ig,id)=iii
L00338        enddo
L00339        enddo
L00340  
L00341        iii=0
L00342        do iz_u=1,nz_um
L00343        do id=1,ndm
L00344         iii=iii+1
L00345         ind_zd(iz_u,id)=iii
L00346        enddo
L00347        enddo
L00348  
L00349        if (num_urban_hi.ge.nz_um)then
L00350            write(*,*)'nz_um too small, please increase to at least ', num_urban_hi+1
L00351            stop         
L00352        endif
L00353  
L00354        do ix=its,ite
L00355            do iy=jts,jte
L00356                do iz_u=1,nz_um
L00357                    hi_urb(ix,iz_u,iy)=0.
L00358                enddo
L00359            enddo
L00360        enddo
L00361        
L00362        do ix=its,ite
L00363        do iy=jts,jte
L00364         z(ix,kts,iy)=0.
L00365         do iz=kts+1,kte+1
L00366          z(ix,iz,iy)=z(ix,iz-1,iy)+dz8w(ix,iz-1,iy)
L00367         enddo !iz
L00368         do iz_u=1,num_urban_hi
L00369            hi_urb(ix,iz_u,iy)= hi_urb2d(ix,iz_u,iy)
L00370         enddo !iz_u
L00371        enddo
L00372        enddo
L00373  
L00374  
L00375        if (first) then                           ! True only on first call
L00376           
L00377           call init_para(alag_u,alaw_u,alar_u,csg_u,csw_u,csr_u,&
L00378                  twini_u,trini_u,tgini_u,albg_u,albw_u,albr_u,emg_u,emw_u,&
L00379                  emr_u,z0g_u,z0r_u,nd_u,strd_u,drst_u,ws_u,bs_u,h_b,d_b)
L00380  
L00381  !      Initialisation of the urban parameters and calculation of the view factors
L00382               
L00383           call icBEP(nd_u,h_b,d_b,ss_u,pb_u,nz_u,z_u)                                  
L00384            
L00385           first=.false.
L00386  
L00387        endif ! first
L00388  
L00389        do ix=its,ite
L00390        do iy=jts,jte
L00391          if (FRC_URB2D(ix,iy).gt.0.) then    ! Calling BEP only for existing urban classes.	
L00392             iurb=UTYPE_URB2D(ix,iy)
L00393  
L00394             hi_urb1D=0.
L00395             do iz_u=1,nz_um
L00396                hi_urb1D(iz_u)=hi_urb(ix,iz_u,iy)
L00397             enddo
L00398  
L00399             call icBEPHI_XY(hb_u,hi_urb1D,ss_urb,pb_urb,    &
L00400                             nz_urb(iurb),z_u)
L00401             
L00402             call param(iurb,nz_u(iurb),nz_urb(iurb),nzurban(iurb),    &
L00403                        nd_u(iurb),csg_u,csg,alag_u,alag,csr_u,csr,    &
L00404                        alar_u,alar,csw_u,csw,alaw_u,alaw,             &
L00405                        ws_u,ws,bs_u,bs,z0g_u,z0r_u,z0,                &
L00406                        strd_u,strd,drst_u,drst,ss_u,ss_urb,ss,pb_u,   &
L00407                        pb_urb,pb,lp_urb2d(ix,iy),                     &
L00408                        lb_urb2d(ix,iy),hgt_urb2d(ix,iy),FRC_URB2D(ix,iy))  
L00409  !
L00410  !We compute the view factors in the icBEP_XY routine
L00411  !           
L00412           
L00413             call icBEP_XY(iurb,fww_u,fwg_u,fgw_u,fsw_u,fws_u,fsg_u,   &
L00414                           nd_u(iurb),strd,ws,nzurban(iurb),z_u)   
L00415  
L00416         do iz= kts,kte
L00417            ua1D(iz)=u_phy(ix,iz,iy)
L00418            va1D(iz)=v_phy(ix,iz,iy)
L00419  	  pt1D(iz)=th_phy(ix,iz,iy)
L00420  	  da1D(iz)=rho(ix,iz,iy)
L00421  	  pr1D(iz)=p_phy(ix,iz,iy)
L00422  !	  pt01D(iz)=th_phy(ix,iz,iy)
L00423  	  pt01D(iz)=300.
L00424  	  z1D(iz)=z(ix,iz,iy)
L00425            a_u1D(iz)=0.
L00426            a_v1D(iz)=0.
L00427            a_t1D(iz)=0.
L00428            a_e1D(iz)=0.
L00429            b_u1D(iz)=0.
L00430            b_v1D(iz)=0.
L00431            b_t1D(iz)=0.
L00432            b_e1D(iz)=0.           
L00433           enddo
L00434  	 z1D(kte+1)=z(ix,kte+1,iy)
L00435  
L00436           do id=1,ndm
L00437           do iz_u=1,nz_um
L00438           do iw=1,nwr_u
L00439  !          tw1D(2*id-1,iz_u,iw)=tw1_u(ix,iy,ind_zwd(iz_u,iw,id))
L00440  !          tw1D(2*id,iz_u,iw)=tw2_u(ix,iy,ind_zwd(iz_u,iw,id))
L00441              if(ind_zwd(iz_u,iw,id).gt.urban_map_zwd)write(*,*)'ind_zwd too big w',ind_zwd(iz_u,iw,id)
L00442            tw1D(2*id-1,iz_u,iw)=tw1_urb4d(ix,ind_zwd(iz_u,iw,id),iy)
L00443            tw1D(2*id,iz_u,iw)=tw2_urb4d(ix,ind_zwd(iz_u,iw,id),iy)
L00444           enddo
L00445           enddo
L00446           enddo
L00447  	
L00448           do id=1,ndm
L00449            do ig=1,ng_u
L00450  !           tg1D(id,ig)=tg_u(ix,iy,ind_gd(ig,id))
L00451              tg1D(id,ig)=tgb_urb4d(ix,ind_gd(ig,id),iy)
L00452            enddo
L00453            do iz_u=1,nz_um
L00454            do ir=1,nwr_u
L00455  !           tr1D(id,iz_u,ir)=tr_u(ix,iy,ind_zwd(iz_u,ir,id))
L00456              if(ind_zwd(iz_u,ir,id).gt.urban_map_zwd)write(*,*)'ind_zwd too big r',ind_zwd(iz_u,ir,id)
L00457              tr1D(id,iz_u,ir)=trb_urb4d(ix,ind_zwd(iz_u,ir,id),iy)
L00458            enddo
L00459            enddo
L00460           enddo
L00461  
L00462           do id=1,ndm
L00463  	 do iz=1,nz_um
L00464  !	  sfw1D(2*id-1,iz)=sfw1(ix,iy,ind_zd(iz,id))
L00465  !	  sfw1D(2*id,iz)=sfw2(ix,iy,ind_zd(iz,id))
L00466  	  sfw1D(2*id-1,iz)=sfw1_urb3d(ix,ind_zd(iz,id),iy)
L00467  	  sfw1D(2*id,iz)=sfw2_urb3d(ix,ind_zd(iz,id),iy)
L00468  	 enddo
L00469  	 enddo
L00470  	 
L00471  	 do id=1,ndm
L00472  !	  sfg1D(id)=sfg(ix,iy,id)
L00473  	  sfg1D(id)=sfg_urb3d(ix,id,iy)
L00474  	 enddo
L00475  	 
L00476  	 do id=1,ndm
L00477  	 do iz=1,nz_um
L00478  !	  sfr1D(id,iz)=sfr(ix,iy,ind_zd(iz,id))
L00479  	  sfr1D(id,iz)=sfr_urb3d(ix,ind_zd(iz,id),iy)
L00480  	 enddo
L00481  	 enddo
L00482  
L00483           
L00484           rs1D=swdown(ix,iy)
L00485           rld1D=glw(ix,iy)
L00486           time_h=(itimestep*dt)/3600.+gmt
L00487  
L00488           zr1D=acos(COSZ_URB2D(ix,iy))
L00489           deltar1D=DECLIN_URB
L00490           ah1D=OMG_URB2D(ix,iy)
L00491  !	 call angle(xlong(ix,iy),xlat(ix,iy),julday,time_h,zr1D,deltar1D,ah1D)
L00492  !        write(*,*) 'entro en BEP1D'
L00493           call BEP1D(iurb,kms,kme,kts,kte,z1D,dt,ua1D,va1D,pt1D,da1D,pr1D,pt01D,  &
L00494                     zr1D,deltar1D,ah1D,rs1D,rld1D,                   & 
L00495                     alag,alaw,alar,csg,csw,csr,                      & 
L00496                     albg_u(iurb),albw_u(iurb),albr_u(iurb),          &
L00497                     emg_u(iurb),emw_u(iurb),emr_u(iurb),             & 
L00498                     fww_u,fwg_u,fgw_u,fsw_u,                         &                    
L00499                     fws_u,fsg_u,z0,                                  &                               
L00500                     nd_u(iurb),strd,drst,ws,bs,ss,pb,                & 
L00501                     nzurban(iurb),z_u,                               & 
L00502                     tw1D,tg1D,tr1D,sfw1D,sfg1D,sfr1D,                & 
L00503                     a_u1D,a_v1D,a_t1D,a_e1D,                         & 
L00504                     b_u1D,b_v1D,b_t1D,b_e1D,                         & 
L00505                     dlg1D,dl_u1D,sf1D,vl1D,rl_up(ix,iy),             &
L00506                     rs_abs(ix,iy),emiss(ix,iy),grdflx_urb(ix,iy))                            
L00507  !        write(*,*) 'salgo de BEP1D'
L00508           do id=1,ndm
L00509  	 do iz=1,nz_um
L00510  	  sfw1_urb3d(ix,ind_zd(iz,id),iy)=sfw1D(2*id-1,iz) 
L00511  	  sfw2_urb3d(ix,ind_zd(iz,id),iy)=sfw1D(2*id,iz) 
L00512  	 enddo
L00513  	 enddo
L00514   
L00515  	 do id=1,ndm
L00516  	  sfg_urb3d(ix,id,iy)=sfg1D(id) 
L00517  	 enddo
L00518  	
L00519  	 do id=1,ndm
L00520  	 do iz=1,nz_um
L00521  	  sfr_urb3d(ix,ind_zd(iz,id),iy)=sfr1D(id,iz)
L00522  	 enddo
L00523  	 enddo
L00524  !
L00525           do id=1,ndm
L00526           do iz_u=1,nz_um
L00527           do iw=1,nwr_u
L00528            tw1_urb4d(ix,ind_zwd(iz_u,iw,id),iy)=tw1D(2*id-1,iz_u,iw)
L00529            tw2_urb4d(ix,ind_zwd(iz_u,iw,id),iy)=tw1D(2*id,iz_u,iw)
L00530           enddo
L00531           enddo
L00532           enddo
L00533          
L00534           do id=1,ndm
L00535            do ig=1,ng_u
L00536             tgb_urb4d(ix,ind_gd(ig,id),iy)=tg1D(id,ig)
L00537            enddo
L00538            do iz_u=1,nz_um
L00539            do ir=1,nwr_u
L00540             trb_urb4d(ix,ind_zwd(iz_u,ir,id),iy)=tr1D(id,iz_u,ir)
L00541            enddo
L00542            enddo
L00543           enddo
L00544          
L00545            sf(ix,kts:kte,iy)=0.
L00546            vl(ix,kts:kte,iy)=0.
L00547            a_u(ix,kts:kte,iy)=0.
L00548            a_v(ix,kts:kte,iy)=0.
L00549            a_t(ix,kts:kte,iy)=0.
L00550            a_e(ix,kts:kte,iy)=0.
L00551            b_u(ix,kts:kte,iy)=0.
L00552            b_v(ix,kts:kte,iy)=0.
L00553            b_t(ix,kts:kte,iy)=0.
L00554            b_e(ix,kts:kte,iy)=0.
L00555            b_q(ix,kts:kte,iy)=0.
L00556            dlg(ix,kts:kte,iy)=0.
L00557            dl_u(ix,kts:kte,iy)=0.
L00558  
L00559          do iz= kts,kte
L00560            sf(ix,iz,iy)=sf1D(iz)
L00561            vl(ix,iz,iy)=vl1D(iz)
L00562            a_u(ix,iz,iy)=a_u1D(iz)
L00563            a_v(ix,iz,iy)=a_v1D(iz)
L00564            a_t(ix,iz,iy)=a_t1D(iz)
L00565            a_e(ix,iz,iy)=a_e1D(iz)
L00566            b_u(ix,iz,iy)=b_u1D(iz)
L00567            b_v(ix,iz,iy)=b_v1D(iz)
L00568            b_t(ix,iz,iy)=b_t1D(iz)
L00569            b_e(ix,iz,iy)=b_e1D(iz)
L00570            dlg(ix,iz,iy)=dlg1D(iz)
L00571            dl_u(ix,iz,iy)=dl_u1D(iz)
L00572           enddo
L00573           sf(ix,kte+1,iy)=sf1D(kte+1)
L00574  !
L00575           endif ! FRC_URB2D
L00576     
L00577        enddo  ! iy
L00578        enddo  ! ix
L00579  
L00580  
L00581          time_bep=time_bep+dt
L00582           
L00583           
L00584        return
L00585        end subroutine BEP
```

> 讲解：与 BEP_BEM 同构但瘦身：①折叠索引表只保 **4 张**（ind_zwd/ind_gd/ind_zd + 墙面通量用 ind_zd）——BEM 的 ind_bd/ind_wd/ind_gbd/ind_fbd 都不需要；②逐点流程：param（含 lp/lb/hgt 反解街道几何，同 14a §六）→ icBEP_XY（逐点视野因子）→ 折叠 tw1/tw2/trb/tgb 与 sfw/sfg/sfr → BEP1D → 写回。③折叠时的越界哨兵（ind_zwd>urban_map_zwd 时 write 提示但不中断——比 bep_bem 的 stop 温和）；④time_bep 累计但基本无用（调试遗留）；⑤注意屋顶温度折叠用 **ind_zwd**（L457/540）而非 bep_bem 的 ind_zrd——两文件的同名维度表编号不同源，改任何一边都不能想当然。

## 五、柱求解器 BEP1D（全文）

<!-- code_extract code_extract.py v1.2
source: phys/module_sf_bep.F
ranges: L589-L905
file_lines: 3536
file_md5: 5f74b56a221ca4ec69320a09ad3f9c3e
display: line-numbered (strip L-prefix and !file: line to restore)
range_md5: 60ebad234f6911d0b2e8cb4f880e3375
seg_lines: 317
label: subroutine BEP1D
-->

```fortran
!file: phys/module_sf_bep.F    L589-L905    (subroutine BEP1D)
L00589        subroutine BEP1D(iurb,kms,kme,kts,kte,z,dt,ua,va,pt,da,pr,pt0,  &  
L00590                        zr,deltar,ah,rs,rld,                            & 
L00591                        alag,alaw,alar,csg,csw,csr,                     & 
L00592                        albg,albw,albr,emg,emw,emr,                     & 
L00593                        fww,fwg,fgw,fsw,fws,fsg,z0,                     &                                             
L00594                        ndu,strd,drst,ws,bs,ss,pb,                      & 
L00595                        nzu,z_u,                                        & 
L00596                        tw,tg,tr,sfw,sfg,sfr,                           & 
L00597                        a_u,a_v,a_t,a_e,                                &
L00598                        b_u,b_v,b_t,b_e,                                & 
L00599                        dlg,dl_u,sf,vl,rl_up,rs_abs,emiss,grdflx_urb)                             
L00600  
L00601  ! ----------------------------------------------------------------------
L00602  ! This routine computes the effects of buildings on momentum, heat and
L00603  !  TKE (turbulent kinetic energy) sources or sinks and on the mixing length.
L00604  ! It provides momentum, heat and TKE sources or sinks at different levels of a
L00605  !  mesoscale grid defined by the altitude of its cell interfaces "z" and
L00606  !  its number of levels "nz".
L00607  ! The meteorological input parameters (wind, temperature, solar radiation)
L00608  !  are specified on the "mesoscale grid".
L00609  ! The inputs concerning the building and street charateristics are defined
L00610  !  on a "urban grid". The "urban grid" is defined with its number of levels
L00611  !  "nz_u" and its space step "dz_u".
L00612  ! The input parameters are interpolated on the "urban grid". The sources or sinks
L00613  !  are calculated on the "urban grid". Finally the sources or sinks are 
L00614  !  interpolated on the "mesoscale grid".
L00615   
L00616  
L00617  !  Mesoscale grid            Urban grid             Mesoscale grid
L00618  !  
L00619  ! z(4)    ---                                               ---
L00620  !          |                                                 |
L00621  !          |                                                 |
L00622  !          |   Interpolation                  Interpolation  |
L00623  !          |            Sources or sinks calculation         |
L00624  ! z(3)    ---                                               ---
L00625  !          | ua               ua_u  ---  uv_a         a_u    |
L00626  !          | va               va_u   |   uv_b         b_u    |
L00627  !          | pt               pt_u  ---  uh_b         a_v    |
L00628  ! z(2)    ---                        |    etc...      etc...---
L00629  !          |                 z_u(1) ---                      |
L00630  !          |                         |                       |
L00631  ! z(1) ------------------------------------------------------------
L00632  
L00633  !     
L00634  ! Reference:
L00635  ! Martilli, A., Clappier, A., Rotach, M.W.:2002, 'AN URBAN SURFACE EXCHANGE
L00636  ! PARAMETERISATION FOR MESOSCALE MODELS', Boundary-Layer Meteorolgy 104:
L00637  ! 261-304
L00638   
L00639  ! ----------------------------------------------------------------------
L00640  
L00641        implicit none
L00642  
L00643   
L00644  
L00645  ! ----------------------------------------------------------------------
L00646  ! INPUT:
L00647  ! ----------------------------------------------------------------------
L00648  
L00649  ! Data relative to the "mesoscale grid"
L00650  
L00651  !      integer nz                 ! Number of vertical levels
L00652        integer kms,kme,kts,kte
L00653        real z(kms:kme)               ! Altitude above the ground of the cell interfaces.
L00654        real ua(kms:kme)                ! Wind speed in the x direction
L00655        real va(kms:kme)                ! Wind speed in the y direction
L00656        real pt(kms:kme)                ! Potential temperature
L00657        real da(kms:kme)                ! Air density
L00658        real pr(kms:kme)                ! Air pressure
L00659        real pt0(kms:kme)               ! Reference potential temperature (could be equal to "pt")
L00660        real dt                    ! Time step
L00661        real zr                    ! Zenith angle
L00662        real deltar                ! Declination of the sun
L00663        real ah                    ! Hour angle
L00664        real rs                    ! Solar radiation
L00665        real rld                   ! Downward flux of the longwave radiation
L00666  
L00667  ! Data relative to the "urban grid"
L00668  
L00669        integer iurb               ! Current urban class
L00670  
L00671  !    Building parameters      
L00672        real alag(ng_u)            ! Ground thermal diffusivity [m^2 s^-1]
L00673        real alaw(nwr_u)           ! Wall thermal diffusivity [m^2 s^-1]
L00674        real alar(nwr_u)           ! Roof thermal diffusivity [m^2 s^-1]
L00675        real csg(ng_u)             ! Specific heat of the ground material [J m^3 K^-1]
L00676        real csw(nwr_u)            ! Specific heat of the wall material [J m^3 K^-1]
L00677        real csr(nwr_u)            ! Specific heat of the roof material [J m^3 K^-1]
L00678  
L00679  !    Radiation parameters
L00680        real albg                  ! Albedo of the ground
L00681        real albw                  ! Albedo of the wall
L00682        real albr                  ! Albedo of the roof
L00683        real emg                   ! Emissivity of ground
L00684        real emw                   ! Emissivity of wall
L00685        real emr                   ! Emissivity of roof
L00686  
L00687  !    fww,fwg,fgw,fsw,fsg are the view factors used to compute the long and 
L00688  !    short wave radation. 
L00689  !    The calculation of these factor is explained in the Appendix A of the BLM paper
L00690        real fww(nz_um,nz_um,ndm,nurbm)  !  from wall to wall
L00691        real fwg(nz_um,ndm,nurbm)        !  from wall to ground
L00692        real fgw(nz_um,ndm,nurbm)        !  from ground to wall
L00693        real fsw(nz_um,ndm,nurbm)        !  from sky to wall
L00694        real fws(nz_um,ndm,nurbm)        !  from wall to sky
L00695        real fsg(ndm,nurbm)              !  from sky to ground
L00696  
L00697  !    Roughness parameters
L00698        real z0(ndm,nz_um)           ! Roughness lengths "profiles"
L00699        
L00700  !    Street parameters
L00701        integer ndu                  ! Number of street direction for each urban class 
L00702        real strd(ndm)               ! Street length (set to a greater value then the horizontal length of the cells)
L00703        real drst(ndm)               ! Street direction
L00704        real ws(ndm)                 ! Street width
L00705        real bs(ndm)                 ! Building width
L00706        real ss(nz_um)               ! The probability that a building has an height equal to "z"
L00707        real pb(nz_um)               ! The probability that a building has an height greater or equal to "z"
L00708          
L00709  !    Grid parameters
L00710        integer nzu                  ! Number of layer in the urban grid
L00711        real z_u(nz_um)              ! Height of the urban grid levels
L00712  
L00713  
L00714  ! ----------------------------------------------------------------------
L00715  ! INPUT-OUTPUT
L00716  ! ----------------------------------------------------------------------
L00717  
L00718  ! Data relative to the "urban grid" which should be stored from the current time step to the next one
L00719  
L00720        real tw(2*ndm,nz_um,nwr_u)  ! Temperature in each layer of the wall [K]
L00721        real tr(ndm,nz_um,nwr_u)  ! Temperature in each layer of the roof [K]
L00722        real tg(ndm,ng_u)          ! Temperature in each layer of the ground [K]
L00723        real sfw(2*ndm,nz_um)      ! Sensible heat flux from walls
L00724        real sfg(ndm)              ! Sensible heat flux from ground (road)
L00725        real sfr(ndm,nz_um)      ! Sensible heat flux from roofs
L00726        real gfg(ndm)             ! Heat flux transferred from the surface of the ground (road) towards the interior
L00727        real gfr(ndm,nz_um)     ! Heat flux transferred from the surface of the roof towards the interior
L00728        real gfw(2*ndm,nz_um)     ! Heat flux transfered from the surface of the walls towards the interior
L00729  ! ----------------------------------------------------------------------
L00730  ! OUTPUT:
L00731  ! ----------------------------------------------------------------------
L00732  
L00733  ! Data relative to the "mesoscale grid"
L00734  
L00735        real sf(kms:kme)             ! Surface of the "mesoscale grid" cells taking into account the buildings
L00736        real vl(kms:kme)               ! Volume of the "mesoscale grid" cells taking into account the buildings
L00737       
L00738  !    Implicit and explicit components of the source and sink terms at each levels,
L00739  !     the fluxes can be computed as follow: FX = A*X + B   example: Heat fluxes = a_t * pt + b_t
L00740        real a_u(kms:kme)              ! Implicit component of the momentum sources or sinks in the X-direction
L00741        real a_v(kms:kme)              ! Implicit component of the momentum sources or sinks in the Y-direction
L00742        real a_t(kms:kme)              ! Implicit component of the heat sources or sinks
L00743        real a_e(kms:kme)              ! Implicit component of the TKE sources or sinks
L00744        real b_u(kms:kme)              ! Explicit component of the momentum sources or sinks in the X-direction
L00745        real b_v(kms:kme)              ! Explicit component of the momentum sources or sinks in the Y-direction
L00746        real b_t(kms:kme)              ! Explicit component of the heat sources or sinks
L00747        real b_e(kms:kme)              ! Explicit component of the TKE sources or sinks
L00748        real dlg(kms:kme)              ! Height above ground (L_ground in formula (24) of the BLM paper). 
L00749        real dl_u(kms:kme)             ! Length scale (lb in formula (22) ofthe BLM paper).
L00750        
L00751  ! ----------------------------------------------------------------------
L00752  ! LOCAL:
L00753  ! ----------------------------------------------------------------------
L00754  
L00755        real dz(kms:kme)               ! vertical space steps of the "mesoscale grid"
L00756  
L00757  ! Data interpolated from the "mesoscale grid" to the "urban grid"
L00758  
L00759        real ua_u(nz_um)          ! Wind speed in the x direction
L00760        real va_u(nz_um)          ! Wind speed in the y direction
L00761        real pt_u(nz_um)          ! Potential temperature
L00762        real da_u(nz_um)          ! Air density
L00763        real pt0_u(nz_um)         ! Reference potential temperature
L00764        real pr_u(nz_um)          ! Air pressure
L00765  
L00766  ! Solar radiation at each level of the "urban grid"
L00767  
L00768        real rsg(ndm)             ! Short wave radiation from the ground
L00769        real rsw(2*ndm,nz_um)     ! Short wave radiation from the walls
L00770        real rlg(ndm)             ! Long wave radiation from the ground
L00771        real rlw(2*ndm,nz_um)     ! Long wave radiation from the walls
L00772  
L00773  ! Potential temperature of the surfaces at each level of the "urban grid"
L00774  
L00775        real ptg(ndm)             ! Ground potential temperatures 
L00776        real ptr(ndm,nz_um)     ! Roof potential temperatures 
L00777        real ptw(2*ndm,nz_um)     ! Walls potential temperatures 
L00778  
L00779   
L00780  ! Explicit and implicit component of the momentum, temperature and TKE sources or sinks on
L00781  !  vertical surfaces (walls) ans horizontal surfaces (roofs and street)
L00782  ! The fluxes can be computed as follow: Fluxes of X = A*X + B
L00783  !  Example: Momentum fluxes on vertical surfaces = uva_u * ua_u + uvb_u
L00784  
L00785        real uhb_u(ndm,nz_um)   ! U (wind component) Horizontal surfaces, B (explicit) term
L00786        real uva_u(2*ndm,nz_um)   ! U (wind component)   Vertical surfaces, A (implicit) term
L00787        real uvb_u(2*ndm,nz_um)   ! U (wind component)   Vertical surfaces, B (explicit) term
L00788        real vhb_u(ndm,nz_um)   ! V (wind component) Horizontal surfaces, B (explicit) term
L00789        real vva_u(2*ndm,nz_um)   ! V (wind component)   Vertical surfaces, A (implicit) term
L00790        real vvb_u(2*ndm,nz_um)   ! V (wind component)   Vertical surfaces, B (explicit) term
L00791        real thb_u(ndm,nz_um)   ! Temperature        Horizontal surfaces, B (explicit) term
L00792        real tva_u(2*ndm,nz_um)   ! Temperature          Vertical surfaces, A (implicit) term
L00793        real tvb_u(2*ndm,nz_um)   ! Temperature          Vertical surfaces, B (explicit) term
L00794        real ehb_u(ndm,nz_um)   ! Energy (TKE)       Horizontal surfaces, B (explicit) term
L00795        real evb_u(2*ndm,nz_um)   ! Energy (TKE)         Vertical surfaces, B (explicit) term
L00796        
L00797  !
L00798        real rs_abs ! solar radiation absorbed by urban surfaces 
L00799        real rl_up ! longwave radiation emitted by urban surface to the atmosphere 
L00800        real emiss ! mean emissivity of the urban surface
L00801        real grdflx_urb ! ground heat flux
L00802        integer iz,id
L00803        integer iw,ix,iy
L00804  
L00805  ! ----------------------------------------------------------------------
L00806  ! END VARIABLES DEFINITIONS
L00807  ! ----------------------------------------------------------------------
L00808  
L00809  ! Fix some usefull parameters for the computation of the sources or sinks
L00810  
L00811        do iz=kts,kte
L00812           dz(iz)=z(iz+1)-z(iz)
L00813        end do
L00814  
L00815  ! Interpolation on the "urban grid"
L00816        call interpol(kms,kme,kts,kte,nzu,z,z_u,ua,ua_u)
L00817        call interpol(kms,kme,kts,kte,nzu,z,z_u,va,va_u)
L00818        call interpol(kms,kme,kts,kte,nzu,z,z_u,pt,pt_u)
L00819        call interpol(kms,kme,kts,kte,nzu,z,z_u,pt0,pt0_u)
L00820        call interpol(kms,kme,kts,kte,nzu,z,z_u,pr,pr_u)
L00821        call interpol(kms,kme,kts,kte,nzu,z,z_u,da,da_u)
L00822  
L00823                     
L00824  ! Compute the modification of the radiation due to the buildings
L00825  
L00826        call modif_rad(iurb,ndu,nzu,z_u,ws,               &
L00827                      drst,strd,ss,pb,                    &
L00828                      tw,tg,albg,albw,emw,emg,            &
L00829                      fww,fwg,fgw,fsw,fsg,                &
L00830                      zr,deltar,ah,                       &
L00831                      rs,rld,rsw,rsg,rlw,rlg)                       
L00832   
L00833  ! calculation of the urban albedo and the upward long wave radiation
L00834         
L00835         call upward_rad(ndu,nzu,ws,bs,                   &
L00836                         sigma,pb,ss,                     &
L00837                         tg,emg,albg,rlg,rsg,sfg,         & 
L00838                         tw,emw,albw,rlw,rsw,sfw,         & 
L00839                         tr,emr,albr,rld,rs,sfr,          & 
L00840                         rs_abs,rl_up,emiss,grdflx_urb)               
L00841          
L00842  ! Compute the surface temperatures
L00843       
L00844  
L00845        call surf_temp(nzu,ndu,pr_u,dt,ss,                & 
L00846                      rs,rld,rsg,rlg,rsw,rlw,             &
L00847                      tg,alag,csg,emg,albg,ptg,sfg,gfg,   &
L00848                      tr,alar,csr,emr,albr,ptr,sfr,gfr,   &
L00849                      tw,alaw,csw,emw,albw,ptw,sfw,gfw)  
L00850        
L00851        
L00852  ! Compute the implicit and explicit components of the sources or sinks on the "urban grid"
L00853         
L00854        call buildings(ndu,nzu,z0,ua_u,va_u,                       & 
L00855                       pt_u,pt0_u,ptg,ptr,da_u,ptw,drst,           &                      
L00856                       uva_u,vva_u,uvb_u,vvb_u,tva_u,tvb_u,evb_u,  & 
L00857                       uhb_u,vhb_u,thb_u,ehb_u,ss,dt)                        
L00858   
L00859           
L00860  ! Calculation of the sensible heat fluxes for the ground, the wall and roof
L00861  ! Sensible Heat Flux = density * Cp_U * ( A* potential temperature + B )
L00862  ! where A and B are the implicit and explicit components of the heat sources or sinks.
L00863  !  
L00864  ! 
L00865   
L00866        do id=1,ndu         
L00867           sfg(id)=-da_u(1)*cp_u*thb_u(id,1)
L00868           do iz=2,nzu
L00869              sfr(id,iz)=-da_u(iz)*cp_u*thb_u(id,iz)
L00870           enddo
L00871           
L00872           do iz=1,nzu
L00873              sfw(2*id-1,iz)=-da_u(iz)*cp_u*(tvb_u(2*id-1,iz)+     &
L00874                  tva_u(2*id-1,iz)*pt_u(iz))
L00875              sfw(2*id,iz)=-da_u(iz)*cp_u*(tvb_u(2*id,iz)+         &
L00876                  tva_u(2*id,iz)*pt_u(iz)) 
L00877           enddo
L00878        enddo
L00879        
L00880  ! calculation of the urban albedo and the upward long wave radiation
L00881            
L00882  !!       call upward_rad(ndu,nzu,ws,bs,                      &
L00883  !!                       sigma,pb,ss,                        &
L00884  !!                       tg,emg,albg,rlg,rsg,sfg,            & 
L00885  !!                       tw,emw,albw,rlw,rsw,sfw,            & 
L00886  !!                       tr,emr,albr,rld,rs,sfr,             & 
L00887  !!                       rs_abs,rl_up,emiss,grdflx_urb)             
L00888  
L00889  ! Interpolation on the "mesoscale grid"
L00890  
L00891        call urban_meso(ndu,kms,kme,kts,kte,nzu,z,dz,z_u,pb,ss,bs,ws,sf, & 
L00892                       vl,uva_u,vva_u,uvb_u,vvb_u,tva_u,tvb_u,evb_u,     &
L00893                       uhb_u,vhb_u,thb_u,ehb_u,                          &
L00894                       a_u,a_v,a_t,a_e,b_u,b_v,b_t,b_e)                    
L00895         
L00896  
L00897  ! computation of the mean road temperature tsk (this value could be used 
L00898  ! to replace the surface temperature in the radiation routines, if needed).
L00899  
L00900  ! Calculation of the length scale taking into account the buildings effects
L00901  
L00902        call interp_length(ndu,kms,kme,kts,kte,nzu,z_u,z,ss,ws,bs,dlg,dl_u)
L00903  
L00904        return
L00905        end subroutine BEP1D
```

> 讲解：文件头的 ASCII 示意图（L589–632）值得一看：左侧模式网格 z(1..4)、右侧城市网格 z_u，中间「interpolation→sources→interpolation back」——整篇 BLM 论文的流程图。执行序六步：①interpol 六个量（比 bep_bem 少 qv——无湿度源项）；②modif_rad（阴影+多次反射，无直射/漫射分拆）；③upward_rad（给辐射方案的等效量）；④**surf_temp 一件管三面**（地面+屋顶+墙的导热全在这一个调用里——对照 14a：BEP_BEM 版把屋顶/墙交给了 BEM）；⑤buildings 源项 + 由 A/B 反算表面感热（sfg=−ρ·cp·thb_u 等——墙面感热公式 tvB+tva·pt_u 就是 A·X+B 的字面实现）；⑥urban_meso + interp_length。没有水量收支、没有 BEM 循环、没有 NEW CDRAG（buildings 用常数 cdrag=0.4）。

## 六、与底座同源的单元（差异注记）

<!-- code_extract code_extract.py v1.2
source: phys/module_sf_bep.F
ranges: L910-L1075
file_lines: 3536
file_md5: 5f74b56a221ca4ec69320a09ad3f9c3e
display: line-numbered (strip L-prefix and !file: line to restore)
range_md5: d6d855588124a4f351649f6d04e2b2f0
seg_lines: 166
label: subroutine param
-->

```fortran
!file: phys/module_sf_bep.F    L910-L1075    (subroutine param)
L00910         subroutine param(iurb,nzu,nzurb,nzurban,ndu,                   &
L00911                         csg_u,csg,alag_u,alag,csr_u,csr,               &
L00912                         alar_u,alar,csw_u,csw,alaw_u,alaw,             &
L00913                         ws_u,ws,bs_u,bs,z0g_u,z0r_u,z0,                &  
L00914                         strd_u,strd,drst_u,drst,ss_u,ss_urb,ss,pb_u,   &
L00915                         pb_urb,pb,lp_urb,lb_urb,hgt_urb,frc_urb)        
L00916  
L00917  ! ----------------------------------------------------------------------
L00918  !    This routine prepare some usefull parameters       
L00919  ! ----------------------------------------------------------------------
L00920  
L00921        implicit none
L00922  
L00923    
L00924  ! ----------------------------------------------------------------------
L00925  ! INPUT:
L00926  ! ----------------------------------------------------------------------
L00927        integer iurb                 ! Current urban class
L00928        integer nzu                  ! Number of vertical urban levels in the current class
L00929        integer nzurb                ! Number of vertical urban levels in the current class
L00930        integer ndu                  ! Number of street direction for the current urban class
L00931        real alag_u(nurbm)           ! Ground thermal diffusivity [m^2 s^-1]
L00932        real alar_u(nurbm)           ! Roof thermal diffusivity [m^2 s^-1]
L00933        real alaw_u(nurbm)           ! Wall thermal diffusivity [m^2 s^-1]
L00934        real bs_u(ndm,nurbm)         ! Building width
L00935        real csg_u(nurbm)            ! Specific heat of the ground material [J m^3 K^-1]
L00936        real csr_u(nurbm)            ! Specific heat of the roof material [J m^3 K^-1]
L00937        real csw_u(nurbm)            ! Specific heat of the wall material [J m^3 K^-1]
L00938        real drst_u(ndm,nurbm)       ! Street direction
L00939        real strd_u(ndm,nurbm)       ! Street length 
L00940        real ws_u(ndm,nurbm)         ! Street width
L00941        real z0g_u(nurbm)            ! The ground's roughness length
L00942        real z0r_u(nurbm)            ! The roof's roughness length
L00943        real ss_u(nz_um,nurbm)     ! The probability that a building has an height equal to "z"
L00944        real pb_u(nz_um,nurbm)     ! The probability that a building has an height greater or equal to "z"
L00945        real ss_urb(nz_um)     ! The probability that a building has an height equal to "z"
L00946        real pb_urb(nz_um)     ! The probability that a building has an height greater or equal to "z"
L00947        real lp_urb                ! Building plan area density
L00948        real lb_urb                ! Building surface area to plan area ratio
L00949        real hgt_urb               ! Average building height weighted by building plan area [m]
L00950        real frc_urb               ! Urban fraction
L00951       
L00952  ! ----------------------------------------------------------------------
L00953  ! OUTPUT:
L00954  ! ----------------------------------------------------------------------
L00955        real alag(ng_u)           ! Ground thermal diffusivity at each ground levels
L00956        real alar(nwr_u)           ! Roof thermal diffusivity at each roof levels
L00957        real alaw(nwr_u)           ! Wall thermal diffusivity at each wall levels
L00958        real csg(ng_u)            ! Specific heat of the ground material at each ground levels
L00959        real csr(nwr_u)            ! Specific heat of the roof material at each roof levels
L00960        real csw(nwr_u)            ! Specific heat of the wall material at each wall levels
L00961        real bs(ndm)              ! Building width for the current urban class
L00962        real drst(ndm)            ! street directions for the current urban class
L00963        real strd(ndm)            ! Street lengths for the current urban class
L00964        real ws(ndm)              ! Street widths of the current urban class
L00965        real z0(ndm,nz_um)      ! Roughness lengths "profiles"
L00966        real ss(nz_um)          ! Probability to have a building with height h
L00967        real pb(nz_um)          ! Probability to have a building with an height equal
L00968        integer nzurban
L00969  
L00970  ! ----------------------------------------------------------------------
L00971  ! LOCAL:
L00972  ! ----------------------------------------------------------------------
L00973        integer id,ig,ir,iw,iz,ihu
L00974  
L00975  ! ----------------------------------------------------------------------
L00976  ! END VARIABLES DEFINITIONS
L00977  ! ----------------------------------------------------------------------     
L00978  !
L00979  !Initialize
L00980  !
L00981        ss=0.
L00982        pb=0.
L00983        csg=0.
L00984        alag=0.
L00985        csr=0.
L00986        alar=0.
L00987        csw=0.
L00988        alaw=0.
L00989        z0=0.
L00990        ws=0.
L00991        bs=0.
L00992        strd=0.
L00993        drst=0.
L00994        nzurban=0
L00995        
L00996        ihu=0
L00997  
L00998         do iz=1,nz_um
L00999            if (ss_urb(iz)/=0.) then
L01000               ihu=1
L01001               exit
L01002            else
L01003               continue
L01004            endif
L01005         enddo
L01006             
L01007         if (ihu==1) then
L01008            do iz=1,nzurb+1
L01009               ss(iz)=ss_urb(iz)
L01010               pb(iz)=pb_urb(iz)
L01011            enddo
L01012            nzurban=nzurb
L01013         else
L01014            do iz=1,nzu+1
L01015               ss(iz)=ss_u(iz,iurb)
L01016               pb(iz)=pb_u(iz,iurb)
L01017            end do 
L01018            nzurban=nzu
L01019         endif
L01020  
L01021         do id=1,ndu
L01022          z0(id,1)=z0g_u(iurb)
L01023          do iz=2,nzurban+1
L01024             z0(id,iz)=z0r_u(iurb)
L01025          enddo
L01026         enddo
L01027                   
L01028         do ig=1,ng_u
L01029          csg(ig)=csg_u(iurb)
L01030          alag(ig)=alag_u(iurb)
L01031         enddo
L01032         
L01033         do ir=1,nwr_u
L01034          csr(ir)=csr_u(iurb)
L01035          alar(ir)=alar_u(iurb)
L01036         enddo
L01037         
L01038         do iw=1,nwr_u
L01039          csw(iw)=csw_u(iurb)
L01040          alaw(iw)=alaw_u(iurb)
L01041         enddo
L01042        
L01043         do id=1,ndu
L01044          strd(id)=strd_u(id,iurb)
L01045          drst(id)=drst_u(id,iurb)     
L01046         enddo
L01047      
L01048         do id=1,ndu
L01049            if ((hgt_urb<=0.).OR.(lp_urb<=0.).OR.(lb_urb<=0.)) then
L01050               ws(id)=ws_u(id,iurb)
L01051               bs(id)=bs_u(id,iurb)
L01052            else if ((lp_urb/frc_urb<1.).and.(lp_urb<lb_urb)) then
L01053                    bs(id)=2.*hgt_urb*lp_urb/(lb_urb-lp_urb)
L01054                    ws(id)=2.*hgt_urb*lp_urb*((frc_urb/lp_urb)-1.)/(lb_urb-lp_urb)
L01055                 else
L01056                    ws(id)=ws_u(id,iurb)
L01057                    bs(id)=bs_u(id,iurb) 
L01058            endif
L01059         enddo
L01060         do id=1,ndu
L01061            if ((bs(id)<=1.).OR.(bs(id)>=150.)) then
L01062  !            write(*,*) 'WARNING, WIDTH OF THE BUILDING WRONG',id,bs(id)
L01063  !            write(*,*) 'WIDTH OF THE STREET',id,ws(id)
L01064               bs(id)=bs_u(id,iurb)
L01065               ws(id)=ws_u(id,iurb)
L01066            endif
L01067            if ((ws(id)<=1.).OR.(ws(id)>=150.)) then
L01068  !            write(*,*) 'WARNING, WIDTH OF THE STREET WRONG',id,ws(id)
L01069  !            write(*,*) 'WIDTH OF THE BUILDING',id,bs(id)
L01070               bs(id)=bs_u(id,iurb)
L01071               ws(id)=ws_u(id,iurb)
L01072            endif
L01073         enddo
L01074         return
L01075         end subroutine param
```

> 与 14a §六差异：无 BEM 材料层（csf/alaf/dzgb/alagb 缺），只展开 csg/csw/csr/alag/alaw/alar 与 dzw/dzr；lp/lb/hgt 反解与 1–150 m 钳位完全相同。

<!-- code_extract code_extract.py v1.2
source: phys/module_sf_bep.F
ranges: L1080-L1128
file_lines: 3536
file_md5: 5f74b56a221ca4ec69320a09ad3f9c3e
display: line-numbered (strip L-prefix and !file: line to restore)
range_md5: 1d8a8b238babbc6d5facb0ce79d1411f
seg_lines: 49
label: subroutine interpol
-->

```fortran
!file: phys/module_sf_bep.F    L1080-L1128    (subroutine interpol)
L01080        subroutine interpol(kms,kme,kts,kte,nz_u,z,z_u,c,c_u)
L01081  
L01082  ! ----------------------------------------------------------------------
L01083  !  This routine interpolate para
L01084  !  meters from the "mesoscale grid" to
L01085  !  the "urban grid".
L01086  !  See p300 Appendix B.1 of the BLM paper.
L01087  ! ----------------------------------------------------------------------
L01088  
L01089        implicit none
L01090  
L01091  ! ----------------------------------------------------------------------
L01092  ! INPUT:
L01093  ! ----------------------------------------------------------------------
L01094  ! Data relative to the "mesoscale grid"
L01095        integer kts,kte,kms,kme            
L01096        real z(kms:kme)          ! Altitude of the cell interface
L01097        real c(kms:kme)            ! Parameter which has to be interpolated
L01098  ! Data relative to the "urban grid"
L01099        integer nz_u          ! Number of levels
L01100  !!    real z_u(nz_u+1)      ! Altitude of the cell interface
L01101        real z_u(nz_um)       ! Altitude of the cell interface
L01102  ! ----------------------------------------------------------------------
L01103  ! OUTPUT:
L01104  ! ----------------------------------------------------------------------
L01105  !!    real c_u(nz_u)        ! Interpolated paramters in the "urban grid"
L01106        real c_u(nz_um)       ! Interpolated paramters in the "urban grid"
L01107  
L01108         
L01109  ! LOCAL:
L01110  ! ----------------------------------------------------------------------
L01111        integer iz_u,iz
L01112        real ctot,dz
L01113  
L01114  ! ----------------------------------------------------------------------
L01115  ! END VARIABLES DEFINITIONS
L01116  ! ----------------------------------------------------------------------
L01117  
L01118         do iz_u=1,nz_u
L01119          ctot=0.
L01120          do iz=kts,kte
L01121           dz=max(min(z(iz+1),z_u(iz_u+1))-max(z(iz),z_u(iz_u)),0.)
L01122           ctot=ctot+c(iz)*dz
L01123          enddo
L01124          c_u(iz_u)=ctot/(z_u(iz_u+1)-z_u(iz_u))
L01125         enddo
L01126         
L01127         return
L01128         end subroutine interpol
```

<!-- code_extract code_extract.py v1.2
source: phys/module_sf_bep.F
ranges: L1133-L1205
file_lines: 3536
file_md5: 5f74b56a221ca4ec69320a09ad3f9c3e
display: line-numbered (strip L-prefix and !file: line to restore)
range_md5: b8e59d766cdfc173fdc12e3d0fd672c9
seg_lines: 73
label: subroutine modif_rad
-->

```fortran
!file: phys/module_sf_bep.F    L1133-L1205    (subroutine modif_rad)
L01133        subroutine modif_rad(iurb,nd,nz_u,z,ws,drst,strd,ss,pb,    &
L01134                            tw,tg,albg,albw,emw,emg,               &
L01135                            fww,fwg,fgw,fsw,fsg,                   &
L01136                            zr,deltar,ah,                          &    
L01137                            rs,rl,rsw,rsg,rlw,rlg)                       
L01138   
L01139  ! ----------------------------------------------------------------------
L01140  ! This routine computes the modification of the short wave and 
L01141  !  long wave radiation due to the buildings.
L01142  ! ----------------------------------------------------------------------
L01143  
L01144        implicit none
L01145   
L01146   
L01147  ! ----------------------------------------------------------------------
L01148  ! INPUT:
L01149  ! ----------------------------------------------------------------------
L01150        integer iurb              ! current urban class
L01151        integer nd                ! Number of street direction for the current urban class
L01152        integer nz_u              ! Number of layer in the urban grid
L01153        real z(nz_um)           ! Height of the urban grid levels
L01154        real ws(ndm)              ! Street widths of the current urban class
L01155        real drst(ndm)            ! street directions for the current urban class
L01156        real strd(ndm)            ! Street lengths for the current urban class
L01157        real ss(nz_um)          ! probability to have a building with height h
L01158        real pb(nz_um)          ! probability to have a building with an height equal
L01159        real tw(2*ndm,nz_um,nwr_u) ! Temperature in each layer of the wall [K]
L01160        real tg(ndm,ng_u)         ! Temperature in each layer of the ground [K]
L01161        real albg                 ! Albedo of the ground for the current urban class
L01162        real albw                 ! Albedo of the wall for the current urban class
L01163        real emg                  ! Emissivity of ground for the current urban class
L01164        real emw                  ! Emissivity of wall for the current urban class
L01165        real fgw(nz_um,ndm,nurbm)       ! View factors from ground to wall
L01166        real fsg(ndm,nurbm)             ! View factors from sky to ground
L01167        real fsw(nz_um,ndm,nurbm)       ! View factors from sky to wall
L01168        real fws(nz_um,ndm,nurbm)       ! View factors from wall to sky
L01169        real fwg(nz_um,ndm,nurbm)       ! View factors from wall to ground
L01170        real fww(nz_um,nz_um,ndm,nurbm) ! View factors from wall to wall
L01171        real ah                   ! Hour angle (it should come from the radiation routine)
L01172        real zr                   ! zenith angle
L01173        real deltar               ! Declination of the sun
L01174        real rs                   ! solar radiation
L01175        real rl                   ! downward flux of the longwave radiation
L01176  ! ----------------------------------------------------------------------
L01177  ! OUTPUT:
L01178  ! ----------------------------------------------------------------------
L01179        real rlg(ndm)             ! Long wave radiation at the ground
L01180        real rlw(2*ndm,nz_um)     ! Long wave radiation at the walls
L01181        real rsg(ndm)             ! Short wave radiation at the ground
L01182        real rsw(2*ndm,nz_um)     ! Short wave radiation at the walls
L01183  
L01184  ! ----------------------------------------------------------------------
L01185  ! LOCAL:
L01186  ! ----------------------------------------------------------------------
L01187  
L01188        integer id,iz
L01189  
L01190  !  Calculation of the shadow effects
L01191  
L01192        call shadow_mas(nd,nz_u,zr,deltar,ah,drst,ws,ss,pb,z,           &
L01193                       rs,rsw,rsg)
L01194  
L01195  ! Calculation of the reflection effects          
L01196        do id=1,nd
L01197           call long_rad(iurb,nz_u,id,emw,emg,                 &
L01198                        fwg,fww,fgw,fsw,fsg,tg,tw,rlg,rlw,rl,pb)
L01199           
L01200           call short_rad(iurb,nz_u,id,albw,albg,fwg,fww,fgw,rsg,rsw,pb)
L01201    
L01202        enddo
L01203        
L01204        return
L01205        end subroutine modif_rad
```

> modif_rad 差异：**无 swddir/swddif 分量**——BEP 单独版把总短波 rs 直接给 shadow_mas（不区分直射漫射），且无窗户混合（alb_av=pwin·albwin+… 一行不存在）。long_rad/short_rad 内部因此少窗户项。对照 14a §八。

<!-- code_extract code_extract.py v1.2
source: phys/module_sf_bep.F
ranges: L1774-L1891
file_lines: 3536
file_md5: 5f74b56a221ca4ec69320a09ad3f9c3e
display: line-numbered (strip L-prefix and !file: line to restore)
range_md5: 9e65d76f0fce9d2651504975478900d8
seg_lines: 118
label: subroutine shadow_mas
-->

```fortran
!file: phys/module_sf_bep.F    L1774-L1891    (subroutine shadow_mas)
L01774        subroutine shadow_mas(nd,nz_u,zr,deltar,ah,drst,ws,ss,pb,z,         &
L01775                             rs,rsw,rsg)
L01776          
L01777  ! ----------------------------------------------------------------------
L01778  !         Modification of short wave radiation to take into account
L01779  !         the shadow produced by the buildings
L01780  ! ----------------------------------------------------------------------
L01781  
L01782        implicit none
L01783       
L01784  ! ----------------------------------------------------------------------
L01785  ! INPUT:
L01786  ! ----------------------------------------------------------------------
L01787        integer nd                ! Number of street direction for the current urban class
L01788        integer nz_u              ! number of vertical layers defined in the urban grid
L01789        real ah                   ! Hour angle (it should come from the radiation routine)
L01790        real deltar               ! Declination of the sun
L01791        real drst(ndm)            ! street directions for the current urban class
L01792        real rs                   ! solar radiation
L01793        real ss(nz_um)          ! probability to have a building with height h
L01794        real pb(nz_um)          ! Probability that a building has an height greater or equal to h
L01795        real ws(ndm)              ! Street width of the current urban class
L01796        real z(nz_um)           ! Height of the urban grid levels
L01797        real zr                   ! zenith angle
L01798  
L01799  ! ----------------------------------------------------------------------
L01800  ! OUTPUT:
L01801  ! ----------------------------------------------------------------------
L01802        real rsg(ndm)             ! Short wave radiation at the ground
L01803        real rsw(2*ndm,nz_um)     ! Short wave radiation at the walls
L01804  
L01805  ! ----------------------------------------------------------------------
L01806  ! LOCAL:
L01807  ! ----------------------------------------------------------------------
L01808        integer id,iz,jz
L01809        real aae,aaw,bbb,phix,rd,rtot,wsd
L01810        
L01811  ! ----------------------------------------------------------------------
L01812  ! END VARIABLES DEFINITIONS
L01813  ! ----------------------------------------------------------------------
L01814  
L01815        if(rs.eq.0.or.sin(zr).eq.1)then
L01816           do id=1,nd
L01817              rsg(id)=0.
L01818              do iz=1,nz_u
L01819                 rsw(2*id-1,iz)=0.
L01820                 rsw(2*id,iz)=0.
L01821              enddo
L01822           enddo
L01823        else            
L01824  !test              
L01825           if(abs(sin(zr)).gt.1.e-10)then
L01826            if(cos(deltar)*sin(ah)/sin(zr).ge.1)then
L01827             bbb=pi/2.
L01828            elseif(cos(deltar)*sin(ah)/sin(zr).le.-1)then
L01829             bbb=-pi/2.
L01830            else
L01831             bbb=asin(cos(deltar)*sin(ah)/sin(zr))
L01832            endif
L01833           else
L01834            if(cos(deltar)*sin(ah).ge.0)then
L01835             bbb=pi/2.
L01836            elseif(cos(deltar)*sin(ah).lt.0)then
L01837             bbb=-pi/2.
L01838            endif
L01839           endif
L01840  
L01841           phix=zr
L01842             
L01843           do id=1,nd
L01844          
L01845              rsg(id)=0.
L01846             
L01847              aae=bbb-drst(id)
L01848              aaw=bbb-drst(id)+pi
L01849                      
L01850              do iz=1,nz_u
L01851                 rsw(2*id-1,iz)=0.
L01852                 rsw(2*id,iz)=0.          
L01853              if(pb(iz+1).gt.0.)then           
L01854                 do jz=1,nz_u                    
L01855                  if(abs(sin(aae)).gt.1.e-10)then
L01856                    call shade_wall(z(iz),z(iz+1),z(jz+1),phix,aae,   &    
L01857                        ws(id),rd)                  
L01858                    rsw(2*id-1,iz)=rsw(2*id-1,iz)+rs*rd*ss(jz+1)/pb(iz+1)
L01859                  endif
L01860                
L01861                  if(abs(sin(aaw)).gt.1.e-10)then
L01862                    call shade_wall(z(iz),z(iz+1),z(jz+1),phix,aaw,   &    
L01863                        ws(id),rd)
L01864                    rsw(2*id,iz)=rsw(2*id,iz)+rs*rd*ss(jz+1)/pb(iz+1)                  
L01865                  endif
L01866                 enddo             
L01867              endif  
L01868              enddo
L01869          if(abs(sin(aae)).gt.1.e-10)then
L01870              wsd=abs(ws(id)/sin(aae))
L01871                
L01872              do jz=1,nz_u           
L01873                 rd=max(0.,wsd-z(jz+1)*tan(phix))
L01874                 rsg(id)=rsg(id)+rs*rd*ss(jz+1)/wsd          
L01875              enddo
L01876              rtot=0.
L01877             
L01878              do iz=1,nz_u
L01879                 rtot=rtot+(rsw(2*id,iz)+rsw(2*id-1,iz))*            &
L01880                           (z(iz+1)-z(iz))
L01881              enddo
L01882              rtot=rtot+rsg(id)*ws(id)
L01883          else
L01884              rsg(id)=rs
L01885          endif
L01886              
L01887           enddo
L01888        endif
L01889           
L01890        return
L01891        end subroutine shadow_mas
```

<!-- code_extract code_extract.py v1.2
source: phys/module_sf_bep.F
ranges: L1896-L1946
file_lines: 3536
file_md5: 5f74b56a221ca4ec69320a09ad3f9c3e
display: line-numbered (strip L-prefix and !file: line to restore)
range_md5: 0965ba89590bd80dd84804911c794452
seg_lines: 51
label: subroutine shade_wall
-->

```fortran
!file: phys/module_sf_bep.F    L1896-L1946    (subroutine shade_wall)
L01896        subroutine shade_wall(z1,z2,hu,phix,aa,ws,rd)
L01897  
L01898  ! ----------------------------------------------------------------------
L01899  ! This routine computes the effects of a shadow induced by a building of 
L01900  ! height hu, on a portion of wall between z1 and z2. See equation A10, 
L01901  ! and correction described below formula A11, and figure A1. Basically rd
L01902  ! is the ratio between the horizontal surface illuminated and the portion
L01903  ! of wall. Referring to figure A1, multiplying radiation flux density on 
L01904  ! a horizontal surface (rs) by x1-x2 we have the radiation energy per 
L01905  ! unit time. Dividing this by z2-z1, we obtain the radiation flux 
L01906  ! density reaching the portion of the wall between z2 and z1 
L01907  ! (everything is assumed in 2D)
L01908  ! ----------------------------------------------------------------------
L01909  
L01910        implicit none
L01911        
L01912  ! ----------------------------------------------------------------------
L01913  ! INPUT:
L01914  ! ----------------------------------------------------------------------
L01915        real aa                   ! Angle between the sun direction and the face of the wall (A12)
L01916        real hu                   ! Height of the building that generates the shadow
L01917        real phix                 ! Solar zenith angle
L01918        real ws                   ! Width of the street
L01919        real z1                   ! Height of the level z(iz)
L01920        real z2                   ! Height of the level z(iz+1)
L01921  
L01922  ! ----------------------------------------------------------------------
L01923  ! OUTPUT:
L01924  ! ----------------------------------------------------------------------
L01925        real rd                   ! Ratio between (x1-x2)/(z2-z1), see Fig. 1A. 
L01926                                  ! Multiplying rd by rs (radiation flux 
L01927                                  ! density on a horizontal surface) gives 
L01928                                  ! the radiation flux density on the 
L01929                                  ! portion of wall between z1 and z2. 
L01930  ! ----------------------------------------------------------------------
L01931  ! LOCAL:
L01932  ! ----------------------------------------------------------------------
L01933        real x1,x2                ! x1,x2 see Fig. A1.
L01934  
L01935  ! ----------------------------------------------------------------------
L01936  ! END VARIABLES DEFINITIONS
L01937  ! ----------------------------------------------------------------------
L01938  
L01939        x1=min((hu-z1)*tan(phix),max(0.,ws/sin(aa)))
L01940        
L01941        x2=max((hu-z2)*tan(phix),0.)
L01942  
L01943        rd=max(0.,sin(aa)*(max(0.,x1-x2))/(z2-z1))
L01944        
L01945        return
L01946        end subroutine shade_wall
```

> 与 14b §三逐行同源（几何推导见彼处）。

<!-- code_extract code_extract.py v1.2
source: phys/module_sf_bep.F
ranges: L1951-L2092
file_lines: 3536
file_md5: 5f74b56a221ca4ec69320a09ad3f9c3e
display: line-numbered (strip L-prefix and !file: line to restore)
range_md5: 71392578bc1876cb0cd6c4dfdaf44593
seg_lines: 142
label: subroutine long_rad
-->

```fortran
!file: phys/module_sf_bep.F    L1951-L2092    (subroutine long_rad)
L01951        subroutine long_rad(iurb,nz_u,id,emw,emg,                  &
L01952                           fwg,fww,fgw,fsw,fsg,tg,tw,rlg,rlw,rl,pb)
L01953  
L01954  ! ----------------------------------------------------------------------
L01955  ! This routine computes the effects of the reflections of long-wave 
L01956  ! radiation in the street canyon by solving the system 
L01957  ! of 2*nz_u+1 eqn. in 2*nz_u+1
L01958  ! unkonwn defined in A4, A5 and A6 of the paper (pages 295 and 296).
L01959  ! The system is solved by solving A X= B,
L01960  ! with A matrix B vector, and X solution. 
L01961  ! ----------------------------------------------------------------------
L01962  
L01963        implicit none
L01964  
L01965    
L01966        
L01967  ! ----------------------------------------------------------------------
L01968  ! INPUT:
L01969  ! ----------------------------------------------------------------------
L01970        real emg                        ! Emissivity of ground for the current urban class
L01971        real emw                        ! Emissivity of wall for the current urban class
L01972        real fgw(nz_um,ndm,nurbm)       ! View factors from ground to wall
L01973        real fsg(ndm,nurbm)             ! View factors from sky to ground
L01974        real fsw(nz_um,ndm,nurbm)       ! View factors from sky to wall
L01975        real fwg(nz_um,ndm,nurbm)       ! View factors from wall to ground
L01976        real fww(nz_um,nz_um,ndm,nurbm) ! View factors from wall to wall
L01977        integer id                      ! Current street direction
L01978        integer iurb                    ! Current urban class
L01979        integer nz_u                    ! Number of layer in the urban grid
L01980        real pb(nz_um)                ! Probability to have a building with an height equal
L01981        real rl                         ! Downward flux of the longwave radiation
L01982        real tg(ndm,ng_u)               ! Temperature in each layer of the ground [K]
L01983        real tw(2*ndm,nz_um,nwr_u)       ! Temperature in each layer of the wall [K]
L01984        
L01985  
L01986  ! ----------------------------------------------------------------------
L01987  ! OUTPUT:
L01988  ! ----------------------------------------------------------------------
L01989        real rlg(ndm)                   ! Long wave radiation at the ground
L01990        real rlw(2*ndm,nz_um)           ! Long wave radiation at the walls
L01991  
L01992  ! ----------------------------------------------------------------------
L01993  ! LOCAL:
L01994  ! ----------------------------------------------------------------------
L01995        integer i,j
L01996        real aaa(2*nz_um+1,2*nz_um+1)   ! terms of the matrix
L01997        real bbb(2*nz_um+1)             ! terms of the vector
L01998  
L01999  ! ----------------------------------------------------------------------
L02000  ! END VARIABLES DEFINITIONS
L02001  ! ----------------------------------------------------------------------
L02002  
L02003  
L02004  ! west wall
L02005         
L02006        do i=1,nz_u
L02007          
L02008          do j=1,nz_u
L02009           aaa(i,j)=0.
L02010          enddo
L02011          
L02012          aaa(i,i)=1.        
L02013         
L02014          do j=nz_u+1,2*nz_u
L02015           aaa(i,j)=-(1.-emw)*fww(j-nz_u,i,id,iurb)*pb(j-nz_u+1)
L02016          enddo
L02017          
L02018  !!      aaa(i,2*nz_u+1)=-(1.-emg)*fgw(i,id,iurb)*pb(i+1)
L02019          aaa(i,2*nz_u+1)=-(1.-emg)*fgw(i,id,iurb)
L02020          
L02021          bbb(i)=fsw(i,id,iurb)*rl+emg*fgw(i,id,iurb)*sigma*tg(id,ng_u)**4
L02022          do j=1,nz_u
L02023           bbb(i)=bbb(i)+pb(j+1)*emw*sigma*fww(j,i,id,iurb)*       &
L02024                 tw(2*id,j,nwr_u)**4+                              &
L02025                 fww(j,i,id,iurb)*rl*(1.-pb(j+1))
L02026          enddo
L02027          
L02028         enddo
L02029         
L02030  ! east wall
L02031  
L02032         do i=1+nz_u,2*nz_u
L02033          
L02034          do j=1,nz_u
L02035           aaa(i,j)=-(1.-emw)*fww(j,i-nz_u,id,iurb)*pb(j+1)
L02036          enddo
L02037          
L02038          do j=1+nz_u,2*nz_u
L02039           aaa(i,j)=0.
L02040          enddo
L02041          
L02042          aaa(i,i)=1.
L02043          
L02044  !!      aaa(i,2*nz_u+1)=-(1.-emg)*fgw(i-nz_u,id,iurb)*pb(i-nz_u+1)
L02045          aaa(i,2*nz_u+1)=-(1.-emg)*fgw(i-nz_u,id,iurb)
L02046          
L02047          bbb(i)=fsw(i-nz_u,id,iurb)*rl+                           &     
L02048                emg*fgw(i-nz_u,id,iurb)*sigma*tg(id,ng_u)**4
L02049  
L02050          do j=1,nz_u
L02051           bbb(i)=bbb(i)+pb(j+1)*emw*sigma*fww(j,i-nz_u,id,iurb)*  &   
L02052                  tw(2*id-1,j,nwr_u)**4+                           &   
L02053                  fww(j,i-nz_u,id,iurb)*rl*(1.-pb(j+1))
L02054          enddo
L02055         
L02056         enddo
L02057  
L02058  ! ground
L02059         do j=1,nz_u
L02060          aaa(2*nz_u+1,j)=-(1.-emw)*fwg(j,id,iurb)*pb(j+1)
L02061         enddo
L02062         
L02063         do j=nz_u+1,2*nz_u
L02064          aaa(2*nz_u+1,j)=-(1.-emw)*fwg(j-nz_u,id,iurb)*pb(j-nz_u+1)
L02065         enddo
L02066         
L02067         aaa(2*nz_u+1,2*nz_u+1)=1.
L02068         
L02069         bbb(2*nz_u+1)=fsg(id,iurb)*rl
L02070         
L02071         do i=1,nz_u
L02072          bbb(2*nz_u+1)=bbb(2*nz_u+1)+emw*sigma*fwg(i,id,iurb)*pb(i+1)*    &
L02073                        (tw(2*id-1,i,nwr_u)**4+tw(2*id,i,nwr_u)**4)+       &
L02074                        2.*fwg(i,id,iurb)*(1.-pb(i+1))*rl                  
L02075         enddo
L02076     
L02077  
L02078       
L02079         call gaussj(aaa,2*nz_u+1,bbb,2*nz_um+1)
L02080  
L02081         do i=1,nz_u
L02082          rlw(2*id-1,i)=bbb(i)
L02083         enddo
L02084         
L02085         do i=nz_u+1,2*nz_u
L02086          rlw(2*id,i-nz_u)=bbb(i)
L02087         enddo
L02088         
L02089         rlg(id)=bbb(2*nz_u+1)
L02090    
L02091         return
L02092         end subroutine long_rad
```

<!-- code_extract code_extract.py v1.2
source: phys/module_sf_bep.F
ranges: L2097-L2205
file_lines: 3536
file_md5: 5f74b56a221ca4ec69320a09ad3f9c3e
display: line-numbered (strip L-prefix and !file: line to restore)
range_md5: 8ff14ade41e517a87413cffe1a0e6e84
seg_lines: 109
label: subroutine short_rad
-->

```fortran
!file: phys/module_sf_bep.F    L2097-L2205    (subroutine short_rad)
L02097         subroutine short_rad(iurb,nz_u,id,albw,                        & 
L02098                             albg,fwg,fww,fgw,rsg,rsw,pb)
L02099  
L02100  ! ----------------------------------------------------------------------
L02101  ! This routine computes the effects of the reflections of short-wave 
L02102  ! (solar) radiation in the street canyon by solving the system 
L02103  ! of 2*nz_u+1 eqn. in 2*nz_u+1
L02104  ! unkonwn defined in A4, A5 and A6 of the paper (pages 295 and 296).
L02105  ! The system is solved by solving A X= B,
L02106  ! with A matrix B vector, and X solution. 
L02107  ! ----------------------------------------------------------------------
L02108  
L02109        implicit none
L02110  
L02111    
L02112        
L02113  ! ----------------------------------------------------------------------
L02114  ! INPUT:
L02115  ! ----------------------------------------------------------------------
L02116        real albg                 ! Albedo of the ground for the current urban class
L02117        real albw                 ! Albedo of the wall for the current urban class
L02118        real fgw(nz_um,ndm,nurbm)       ! View factors from ground to wall
L02119        real fwg(nz_um,ndm,nurbm)       ! View factors from wall to ground
L02120        real fww(nz_um,nz_um,ndm,nurbm) ! View factors from wall to wall
L02121        integer id                ! current street direction 
L02122        integer iurb              ! current urban class
L02123        integer nz_u              ! Number of layer in the urban grid
L02124        real pb(nz_um)          ! probability to have a building with an height equal
L02125  
L02126  ! ----------------------------------------------------------------------
L02127  ! OUTPUT:
L02128  ! ----------------------------------------------------------------------
L02129        real rsg(ndm)             ! Short wave radiation at the ground
L02130        real rsw(2*ndm,nz_um)     ! Short wave radiation at the walls
L02131  
L02132  ! ----------------------------------------------------------------------
L02133  ! LOCAL:
L02134  ! ----------------------------------------------------------------------
L02135        integer i,j
L02136        real aaa(2*nz_um+1,2*nz_um+1)  ! terms of the matrix
L02137        real bbb(2*nz_um+1)            ! terms of the vector
L02138  
L02139  ! ----------------------------------------------------------------------
L02140  ! END VARIABLES DEFINITIONS
L02141  ! ----------------------------------------------------------------------
L02142  
L02143        
L02144  ! west wall
L02145         
L02146        do i=1,nz_u
L02147           do j=1,nz_u
L02148              aaa(i,j)=0.
L02149           enddo
L02150           
L02151           aaa(i,i)=1.        
L02152           
L02153           do j=nz_u+1,2*nz_u
L02154              aaa(i,j)=-albw*fww(j-nz_u,i,id,iurb)*pb(j-nz_u+1)
L02155           enddo
L02156           
L02157           aaa(i,2*nz_u+1)=-albg*fgw(i,id,iurb)
L02158           bbb(i)=rsw(2*id-1,i)
L02159           
L02160        enddo
L02161         
L02162  ! east wall
L02163  
L02164        do i=1+nz_u,2*nz_u
L02165           do j=1,nz_u
L02166              aaa(i,j)=-albw*fww(j,i-nz_u,id,iurb)*pb(j+1)
L02167           enddo
L02168           
L02169           do j=1+nz_u,2*nz_u
L02170              aaa(i,j)=0.
L02171           enddo
L02172           
L02173          aaa(i,i)=1.
L02174          aaa(i,2*nz_u+1)=-albg*fgw(i-nz_u,id,iurb)
L02175          bbb(i)=rsw(2*id,i-nz_u)
L02176          
L02177        enddo
L02178  
L02179  ! ground
L02180  
L02181        do j=1,nz_u
L02182           aaa(2*nz_u+1,j)=-albw*fwg(j,id,iurb)*pb(j+1)
L02183        enddo
L02184         
L02185        do j=nz_u+1,2*nz_u
L02186           aaa(2*nz_u+1,j)=-albw*fwg(j-nz_u,id,iurb)*pb(j-nz_u+1)
L02187        enddo
L02188         
L02189        aaa(2*nz_u+1,2*nz_u+1)=1.
L02190        bbb(2*nz_u+1)=rsg(id)
L02191         
L02192        call gaussj(aaa,2*nz_u+1,bbb,2*nz_um+1)
L02193  
L02194        do i=1,nz_u
L02195           rsw(2*id-1,i)=bbb(i)
L02196        enddo
L02197         
L02198        do i=nz_u+1,2*nz_u
L02199           rsw(2*id,i-nz_u)=bbb(i) 
L02200        enddo
L02201         
L02202        rsg(id)=bbb(2*nz_u+1)
L02203         
L02204        return
L02205        end subroutine short_rad
```

> short_rad（非 _dd）：同一线性系统但**无窗户项**（albw 直接用，无 pwin 混合）；long_rad 同理。gaussj 同 NR 实现。

<!-- code_extract code_extract.py v1.2
source: phys/module_sf_bep.F
ranges: L2211-L2313
file_lines: 3536
file_md5: 5f74b56a221ca4ec69320a09ad3f9c3e
display: line-numbered (strip L-prefix and !file: line to restore)
range_md5: f1a48fe0ebebf89ee0d9b3bbdb55f8f5
seg_lines: 103
label: subroutine gaussj
-->

```fortran
!file: phys/module_sf_bep.F    L2211-L2313    (subroutine gaussj)
L02211        subroutine gaussj(a,n,b,np)
L02212  
L02213  ! ----------------------------------------------------------------------
L02214  ! This routine solve a linear system of n equations of the form
L02215  !              A X = B
L02216  !  where  A is a matrix a(i,j)
L02217  !         B a vector and X the solution
L02218  ! In output b is replaced by the solution     
L02219  ! ----------------------------------------------------------------------
L02220  
L02221        implicit none
L02222  
L02223  ! ----------------------------------------------------------------------
L02224  ! INPUT:
L02225  ! ----------------------------------------------------------------------
L02226        integer np
L02227        real a(np,np)
L02228  
L02229  ! ----------------------------------------------------------------------
L02230  ! OUTPUT:
L02231  ! ----------------------------------------------------------------------
L02232        real b(np)
L02233  
L02234  ! ----------------------------------------------------------------------
L02235  ! LOCAL:
L02236  ! ----------------------------------------------------------------------
L02237        integer nmax
L02238        parameter (nmax=150)
L02239  
L02240        real big,dum
L02241        integer i,icol,irow
L02242        integer j,k,l,ll,n
L02243        integer ipiv(nmax)
L02244        real pivinv
L02245  
L02246  ! ----------------------------------------------------------------------
L02247  ! END VARIABLES DEFINITIONS
L02248  ! ----------------------------------------------------------------------
L02249         
L02250        do j=1,n
L02251           ipiv(j)=0.
L02252        enddo
L02253         
L02254        do i=1,n
L02255           big=0.
L02256           do j=1,n
L02257              if(ipiv(j).ne.1)then
L02258                 do k=1,n
L02259                    if(ipiv(k).eq.0)then
L02260                       if(abs(a(j,k)).ge.big)then
L02261                          big=abs(a(j,k))
L02262                          irow=j
L02263                          icol=k
L02264                       endif
L02265                    elseif(ipiv(k).gt.1)then
L02266                       FATAL_ERROR('singular matrix in gaussj')
L02267                    endif
L02268                 enddo
L02269              endif
L02270           enddo
L02271           
L02272           ipiv(icol)=ipiv(icol)+1
L02273           
L02274           if(irow.ne.icol)then
L02275              do l=1,n
L02276                 dum=a(irow,l)
L02277                 a(irow,l)=a(icol,l)
L02278                 a(icol,l)=dum
L02279              enddo
L02280              
L02281              dum=b(irow)
L02282              b(irow)=b(icol)
L02283              b(icol)=dum
L02284            
L02285           endif
L02286           
L02287           if(a(icol,icol).eq.0) FATAL_ERROR('singular matrix in gaussj')
L02288           
L02289           pivinv=1./a(icol,icol)
L02290           a(icol,icol)=1
L02291           
L02292           do l=1,n
L02293              a(icol,l)=a(icol,l)*pivinv
L02294           enddo
L02295           
L02296           b(icol)=b(icol)*pivinv
L02297           
L02298           do ll=1,n
L02299              if(ll.ne.icol)then
L02300                 dum=a(ll,icol)
L02301                 a(ll,icol)=0.
L02302                 do l=1,n
L02303                    a(ll,l)=a(ll,l)-a(icol,l)*dum
L02304                 enddo
L02305                 
L02306                 b(ll)=b(ll)-b(icol)*dum
L02307                 
L02308              endif
L02309           enddo
L02310        enddo
L02311        
L02312        return
L02313        end subroutine gaussj
```

<!-- code_extract code_extract.py v1.2
source: phys/module_sf_bep.F
ranges: L2318-L2409
file_lines: 3536
file_md5: 5f74b56a221ca4ec69320a09ad3f9c3e
display: line-numbered (strip L-prefix and !file: line to restore)
range_md5: 2f579f392574ab6c4ea1a812a2e9b55b
seg_lines: 92
label: subroutine soil_temp
-->

```fortran
!file: phys/module_sf_bep.F    L2318-L2409    (subroutine soil_temp)
L02318        subroutine soil_temp(nz,dz,temp,pt,ala,cs,                       &
L02319                            rs,rl,press,dt,em,alb,rt,sf,gf)
L02320  
L02321  ! ----------------------------------------------------------------------
L02322  ! This routine solves the Fourier diffusion equation for heat in 
L02323  ! the material (wall, roof, or ground). Resolution is done implicitely.
L02324  ! Boundary conditions are: 
L02325  ! - fixed temperature at the interior
L02326  ! - energy budget at the surface
L02327  ! ----------------------------------------------------------------------
L02328  
L02329        implicit none
L02330  
L02331       
L02332                  
L02333  ! ----------------------------------------------------------------------
L02334  ! INPUT:
L02335  ! ----------------------------------------------------------------------
L02336        integer nz                ! Number of layers
L02337        real ala(nz)              ! Thermal diffusivity in each layers [m^2 s^-1] 
L02338        real alb                  ! Albedo of the surface
L02339        real cs(nz)               ! Specific heat of the material [J m^3 K^-1]
L02340        real dt                   ! Time step
L02341        real em                   ! Emissivity of the surface
L02342        real press                ! Pressure at ground level
L02343        real rl                   ! Downward flux of the longwave radiation
L02344        real rs                   ! Solar radiation
L02345        real sf                   ! Sensible heat flux at the surface
L02346        real temp(nz)             ! Temperature in each layer [K]
L02347        real dz(nz)               ! Layer sizes [m]
L02348  
L02349  
L02350  ! ----------------------------------------------------------------------
L02351  ! OUTPUT:
L02352  ! ----------------------------------------------------------------------
L02353        real gf                   ! Heat flux transferred from the surface toward the interior
L02354        real pt                   ! Potential temperature at the surface
L02355        real rt                   ! Total radiation at the surface (solar+incoming long+outgoing long)
L02356  
L02357  ! ----------------------------------------------------------------------
L02358  ! LOCAL:
L02359  ! ----------------------------------------------------------------------
L02360        integer iz
L02361        real a(nz,3)
L02362        real alpha
L02363        real c(nz)
L02364        real cddz(nz+2)
L02365        real tsig
L02366  
L02367  ! ----------------------------------------------------------------------
L02368  ! END VARIABLES DEFINITIONS
L02369  ! ----------------------------------------------------------------------
L02370         
L02371        tsig=temp(nz)
L02372        alpha=(1.-alb)*rs+em*rl-em*sigma*(tsig**4)+sf
L02373  ! Compute cddz=2*cd/dz  
L02374          
L02375        cddz(1)=ala(1)/dz(1)
L02376        do iz=2,nz
L02377           cddz(iz)=2.*ala(iz)/(dz(iz)+dz(iz-1))
L02378        enddo
L02379  !        cddz(nz+1)=ala(nz+1)/dz(nz)
L02380         
L02381        a(1,1)=0.
L02382        a(1,2)=1.
L02383        a(1,3)=0.
L02384        c(1)=temp(1)
L02385            
L02386        do iz=2,nz-1
L02387           a(iz,1)=-cddz(iz)*dt/dz(iz)
L02388           a(iz,2)=1+dt*(cddz(iz)+cddz(iz+1))/dz(iz)          
L02389           a(iz,3)=-cddz(iz+1)*dt/dz(iz)
L02390           c(iz)=temp(iz)
L02391        enddo          
L02392                       
L02393        a(nz,1)=-dt*cddz(nz)/dz(nz)
L02394        a(nz,2)=1.+dt*cddz(nz)/dz(nz)
L02395        a(nz,3)=0.
L02396        c(nz)=temp(nz)+dt*alpha/cs(nz)/dz(nz)
L02397  
L02398        
L02399        call invert(nz,a,c,temp)
L02400  
L02401             
L02402        pt=temp(nz)*(press/1.e+5)**(-rcp_u)
L02403  
L02404        rt=(1.-alb)*rs+em*rl-em*sigma*(tsig**4)
L02405                          
L02406  !      gf=-cddz(nz)*(temp(nz)-temp(nz-1))*cs(nz)
L02407         gf=(1.-alb)*rs+em*rl-em*sigma*(tsig**4)+sf                                   
L02408        return
L02409        end subroutine soil_temp
```

<!-- code_extract code_extract.py v1.2
source: phys/module_sf_bep.F
ranges: L2414-L2460
file_lines: 3536
file_md5: 5f74b56a221ca4ec69320a09ad3f9c3e
display: line-numbered (strip L-prefix and !file: line to restore)
range_md5: 430c0fbbda4f29d31d44e96921091d0a
seg_lines: 47
label: subroutine invert
-->

```fortran
!file: phys/module_sf_bep.F    L2414-L2460    (subroutine invert)
L02414        subroutine invert(n,a,c,x)
L02415  
L02416  ! ----------------------------------------------------------------------
L02417  !        Inversion and resolution of a tridiagonal matrix
L02418  !                   A X = C
L02419  ! ----------------------------------------------------------------------
L02420  
L02421        implicit none
L02422                  
L02423  ! ----------------------------------------------------------------------
L02424  ! INPUT:
L02425  ! ----------------------------------------------------------------------
L02426         integer n
L02427         real a(n,3)              !  a(*,1) lower diagonal (Ai,i-1)
L02428                                  !  a(*,2) principal diagonal (Ai,i)
L02429                                  !  a(*,3) upper diagonal (Ai,i+1)
L02430         real c(n)
L02431  
L02432  ! ----------------------------------------------------------------------
L02433  ! OUTPUT:
L02434  ! ----------------------------------------------------------------------
L02435         real x(n)    
L02436  
L02437  ! ----------------------------------------------------------------------
L02438  ! LOCAL:
L02439  ! ----------------------------------------------------------------------
L02440         integer i
L02441  
L02442  ! ----------------------------------------------------------------------
L02443  ! END VARIABLES DEFINITIONS
L02444  ! ----------------------------------------------------------------------
L02445                       
L02446         do i=n-1,1,-1                 
L02447            c(i)=c(i)-a(i,3)*c(i+1)/a(i+1,2)
L02448            a(i,2)=a(i,2)-a(i,3)*a(i+1,1)/a(i+1,2)
L02449         enddo
L02450         
L02451         do i=2,n        
L02452            c(i)=c(i)-a(i,1)*c(i-1)/a(i-1,2)
L02453         enddo
L02454          
L02455         do i=1,n
L02456            x(i)=c(i)/a(i,2)
L02457         enddo
L02458  
L02459         return
L02460         end subroutine invert
```

> soil_temp/invert 与 14b §四逐行同源（三处厚度数组一致性警示同样适用：本文件 surf_temp 内的 dzg_u/dzr/dzw 与 param 展开值必须一致）。

<!-- code_extract code_extract.py v1.2
source: phys/module_sf_bep.F
ranges: L2466-L2538
file_lines: 3536
file_md5: 5f74b56a221ca4ec69320a09ad3f9c3e
display: line-numbered (strip L-prefix and !file: line to restore)
range_md5: 8bdaf2234de352db7372386516d788ca
seg_lines: 73
label: subroutine flux_wall
-->

```fortran
!file: phys/module_sf_bep.F    L2466-L2538    (subroutine flux_wall)
L02466        subroutine flux_wall(ua,va,pt,da,ptw,uva,vva,uvb,vvb,            &
L02467                                    tva,tvb,evb,drst,dt)      
L02468         
L02469  ! ----------------------------------------------------------------------
L02470  ! This routine computes the surface sources or sinks of momentum, tke,
L02471  ! and heat from vertical surfaces (walls).   
L02472  ! ----------------------------------------------------------------------
L02473  
L02474        implicit none
L02475  
L02476      
L02477           
L02478  ! INPUT:
L02479  ! -----
L02480        real drst                 ! street directions for the current urban class
L02481        real da                   ! air density
L02482        real pt                   ! potential temperature
L02483        real ptw                  ! Walls potential temperatures 
L02484        real ua                   ! wind speed
L02485        real va                   ! wind speed
L02486  
L02487        real dt                   !time step
L02488  ! OUTPUT:
L02489  ! ------
L02490  ! Explicit and implicit component of the momentum, temperature and TKE sources or sinks on
L02491  ! vertical surfaces (walls).
L02492  ! The fluxes can be computed as follow: Fluxes of X = A*X + B
L02493  !  Example: Momentum fluxes on vertical surfaces = uva_u * ua_u + uvb_u
L02494        real uva                  ! U (wind component)   Vertical surfaces, A (implicit) term
L02495        real uvb                  ! U (wind component)   Vertical surfaces, B (explicit) term
L02496        real vva                  ! V (wind component)   Vertical surfaces, A (implicit) term
L02497        real vvb                  ! V (wind component)   Vertical surfaces, B (explicit) term
L02498        real tva                  ! Temperature          Vertical surfaces, A (implicit) term
L02499        real tvb                  ! Temperature          Vertical surfaces, B (explicit) term
L02500        real evb                  ! Energy (TKE)         Vertical surfaces, B (explicit) term
L02501  
L02502  ! LOCAL:
L02503  ! -----
L02504        real hc
L02505        real u_ort
L02506        real vett
L02507  
L02508  ! -------------------------
L02509  ! END VARIABLES DEFINITIONS
L02510  ! -------------------------
L02511  
L02512        vett=(ua**2+va**2)**.5         
L02513           
L02514        u_ort=abs((cos(drst)*ua-sin(drst)*va))
L02515         
L02516        uva=-cdrag*u_ort/2.*cos(drst)*cos(drst)
L02517        vva=-cdrag*u_ort/2.*sin(drst)*sin(drst)
L02518           
L02519        uvb=cdrag*u_ort/2.*sin(drst)*cos(drst)*va
L02520        vvb=cdrag*u_ort/2.*sin(drst)*cos(drst)*ua
L02521           
L02522        hc=5.678*(1.09+0.23*(vett/0.3048))  
L02523  
L02524        if(hc.gt.da*cp_u/dt)then
L02525          hc=da*cp_u/dt
L02526        endif
L02527           
L02528  !         tvb=hc*ptw/da/cp_u
L02529  !         tva=-hc/da/cp_u
L02530  !!!!!!!!!!!!!!!!!!!!
L02531  ! explicit 
L02532        tvb=hc*ptw/da/cp_u-hc/da/cp_u*pt !c
L02533        tva = 0.                  !c
L02534           
L02535        evb=cdrag*(abs(u_ort)**3.)/2.
L02536                
L02537        return
L02538        end subroutine flux_wall
```

> flux_wall 差异：cdrag 来自**模块常数 0.4**（无 NEW CDRAG 调用链）；无窗户 hcwin 分支（无 sfwin 输出）。其余 hc 分段式与 TKE 源 evb 同 14b §五。

<!-- code_extract code_extract.py v1.2
source: phys/module_sf_bep.F
ranges: L2544-L2663
file_lines: 3536
file_md5: 5f74b56a221ca4ec69320a09ad3f9c3e
display: line-numbered (strip L-prefix and !file: line to restore)
range_md5: cf2c33422a55333b7634b8409bc0097c
seg_lines: 120
label: subroutine flux_flat
-->

```fortran
!file: phys/module_sf_bep.F    L2544-L2663    (subroutine flux_flat)
L02544        subroutine flux_flat(dz,z0,ua,va,pt,pt0,ptg,                     &
L02545                            uhb,vhb,thb,ehb)
L02546                                  
L02547  ! ----------------------------------------------------------------------
L02548  !           Calculation of the flux at the ground 
L02549  !           Formulation of Louis (Louis, 1979)       
L02550  ! ----------------------------------------------------------------------
L02551  
L02552        implicit none
L02553  
L02554       
L02555  
L02556  ! ----------------------------------------------------------------------
L02557  ! INPUT:
L02558  ! ----------------------------------------------------------------------
L02559        real dz                   ! first vertical level
L02560        real pt                   ! potential temperature
L02561        real pt0                  ! reference potential temperature
L02562        real ptg                  ! ground potential temperature
L02563        real ua                   ! wind speed
L02564        real va                   ! wind speed
L02565        real z0                   ! Roughness length
L02566  
L02567  ! ----------------------------------------------------------------------
L02568  ! OUTPUT:
L02569  ! ----------------------------------------------------------------------
L02570  ! Explicit component of the momentum, temperature and TKE sources or sinks on horizontal 
L02571  !  surfaces (roofs and street)
L02572  ! The fluxes can be computed as follow: Fluxes of X = B
L02573  !  Example: Momentum fluxes on horizontal surfaces =  uhb_u
L02574        real uhb                  ! U (wind component) Horizontal surfaces, B (explicit) term
L02575        real vhb                  ! V (wind component) Horizontal surfaces, B (explicit) term
L02576        real thb                  ! Temperature        Horizontal surfaces, B (explicit) term
L02577        real tva                  ! Temperature          Vertical surfaces, A (implicit) term
L02578        real tvb                  ! Temperature          Vertical surfaces, B (explicit) term
L02579        real ehb                  ! Energy (TKE)       Horizontal surfaces, B (explicit) term
L02580  
L02581  
L02582  ! ----------------------------------------------------------------------
L02583  ! LOCAL:
L02584  ! ----------------------------------------------------------------------
L02585        real aa
L02586        real al
L02587        real buu
L02588        real c
L02589        real fbuw
L02590        real fbpt
L02591        real fh
L02592        real fm
L02593        real ric
L02594        real tstar
L02595        real ustar
L02596        real utot
L02597        real wstar
L02598        real zz
L02599        
L02600        real b,cm,ch,rr,tol
L02601        parameter(b=9.4,cm=7.4,ch=5.3,rr=0.74,tol=.001)
L02602  
L02603  ! ----------------------------------------------------------------------
L02604  ! END VARIABLES DEFINITIONS
L02605  ! ----------------------------------------------------------------------
L02606  
L02607  
L02608  ! computation of the ground temperature
L02609           
L02610        utot=(ua**2+va**2)**.5
L02611          
L02612        
L02613  !!!! Louis formulation
L02614  !
L02615  ! compute the bulk Richardson Number
L02616  
L02617        zz=dz/2.
L02618     
L02619  !        if(tstar.lt.0.)then
L02620  !         wstar=(-ustar*tstar*g*hii/pt)**(1./3.)
L02621  !        else
L02622  !         wstar=0.
L02623  !        endif
L02624  !        
L02625  !      if (utot.le.0.7*wstar) utot=max(0.7*wstar,0.00001)
L02626  
L02627        utot=max(utot,0.01)
L02628            
L02629        ric=2.*g_u*zz*(pt-ptg)/((pt+ptg)*(utot**2))
L02630                
L02631        aa=vk/log(zz/z0)
L02632  
L02633  ! determine the parameters fm and fh for stable, neutral and unstable conditions
L02634  
L02635        if(ric.gt.0)then
L02636           fm=1/(1+0.5*b*ric)**2
L02637           fh=fm
L02638        else
L02639           c=b*cm*aa*aa*(zz/z0)**.5
L02640           fm=1-b*ric/(1+c*(-ric)**.5)
L02641           c=c*ch/cm
L02642           fh=1-b*ric/(1+c*(-ric)**.5)
L02643        endif
L02644        
L02645        fbuw=-aa*aa*utot*utot*fm
L02646        fbpt=-aa*aa*utot*(pt-ptg)*fh/rr
L02647                       
L02648        ustar=(-fbuw)**.5
L02649        tstar=-fbpt/ustar
L02650  
L02651        al=(vk*g_u*tstar)/(pt*ustar*ustar)                      
L02652        
L02653        buu=-g_u/pt0*ustar*tstar
L02654         
L02655        uhb=-ustar*ustar*ua/utot
L02656        vhb=-ustar*ustar*va/utot 
L02657        thb=-ustar*tstar       
L02658  !      thb= 0.      
L02659        ehb=buu
L02660  !!!!!!!!!!!!!!!
L02661           
L02662        return
L02663        end subroutine flux_flat
```

> 与 14b 版同源（Louis 1979 全套常数 b=9.4/cm=7.4/ch=5.3/rr=0.74）。

<!-- code_extract code_extract.py v1.2
source: phys/module_sf_bep.F
ranges: L1372-L1481
file_lines: 3536
file_md5: 5f74b56a221ca4ec69320a09ad3f9c3e
display: line-numbered (strip L-prefix and !file: line to restore)
range_md5: 069c7507ff085835f458dd993020ed27
seg_lines: 110
label: subroutine buildings
-->

```fortran
!file: phys/module_sf_bep.F    L1372-L1481    (subroutine buildings)
L01372        subroutine buildings(nd,nz,z0,ua_u,va_u,pt_u,pt0_u,         &
L01373                          ptg,ptr,da_u,ptw,                            &
L01374                          drst,uva_u,vva_u,uvb_u,vvb_u,                &
L01375                          tva_u,tvb_u,evb_u,                           &
L01376                          uhb_u,vhb_u,thb_u,ehb_u,ss,dt)                  
L01377  
L01378  ! ----------------------------------------------------------------------
L01379  ! This routine computes the sources or sinks of the different quantities 
L01380  ! on the urban grid. The actual calculation is done in the subroutines 
L01381  ! called flux_wall, and flux_flat.
L01382  ! ----------------------------------------------------------------------
L01383  
L01384        implicit none
L01385  
L01386          
L01387  ! ----------------------------------------------------------------------
L01388  ! INPUT:
L01389  ! ----------------------------------------------------------------------
L01390        integer nd                ! Number of street direction for the current urban class
L01391        integer nz                ! number of vertical space steps
L01392        real ua_u(nz_um)          ! Wind speed in the x direction on the urban grid
L01393        real va_u(nz_um)          ! Wind speed in the y direction on the urban grid
L01394        real da_u(nz_um)          ! air density on the urban grid
L01395        real drst(ndm)            ! Street directions for the current urban class
L01396        real dz
L01397        real pt_u(nz_um)          ! Potential temperature on the urban grid
L01398        real pt0_u(nz_um)         ! reference potential temperature on the urban grid
L01399        real ptg(ndm)             ! Ground potential temperatures 
L01400        real ptr(ndm,nz_um)     ! Roof potential temperatures 
L01401        real ptw(2*ndm,nz_um)     ! Walls potential temperatures 
L01402        real ss(nz_um)          ! probability to have a building with height h
L01403        real z0(ndm,nz_um)      ! Roughness lengths "profiles"
L01404        real dt ! time step
L01405  
L01406  
L01407  ! ----------------------------------------------------------------------
L01408  ! OUTPUT:
L01409  ! ----------------------------------------------------------------------
L01410  ! Explicit and implicit component of the momentum, temperature and TKE sources or sinks on
L01411  ! vertical surfaces (walls) and horizontal surfaces (roofs and street)
L01412  ! The fluxes can be computed as follow: Fluxes of X = A*X + B
L01413  !  Example: Momentum fluxes on vertical surfaces = uva_u * ua_u + uvb_u
L01414  
L01415        real uhb_u(ndm,nz_um)   ! U (wind component) Horizontal surfaces, B (explicit) term
L01416        real uva_u(2*ndm,nz_um)   ! U (wind component)   Vertical surfaces, A (implicit) term
L01417        real uvb_u(2*ndm,nz_um)   ! U (wind component)   Vertical surfaces, B (explicit) term
L01418        real vhb_u(ndm,nz_um)   ! V (wind component) Horizontal surfaces, B (explicit) term
L01419        real vva_u(2*ndm,nz_um)   ! V (wind component)   Vertical surfaces, A (implicit) term
L01420        real vvb_u(2*ndm,nz_um)   ! V (wind component)   Vertical surfaces, B (explicit) term
L01421        real thb_u(ndm,nz_um)   ! Temperature        Horizontal surfaces, B (explicit) term
L01422        real tva_u(2*ndm,nz_um)   ! Temperature          Vertical surfaces, A (implicit) term
L01423        real tvb_u(2*ndm,nz_um)   ! Temperature          Vertical surfaces, B (explicit) term
L01424        real ehb_u(ndm,nz_um)   ! Energy (TKE)       Horizontal surfaces, B (explicit) term
L01425        real evb_u(2*ndm,nz_um)   ! Energy (TKE)         Vertical surfaces, B (explicit) term
L01426    
L01427  ! ----------------------------------------------------------------------
L01428  ! LOCAL:
L01429  ! ----------------------------------------------------------------------
L01430        integer id,iz
L01431  
L01432  ! ----------------------------------------------------------------------
L01433  ! END VARIABLES DEFINITIONS
L01434  ! ----------------------------------------------------------------------
L01435         dz=dz_u
L01436  
L01437        do id=1,nd
L01438  
L01439  !        Calculation at the ground surfaces
L01440           call flux_flat(dz,z0(id,1),ua_u(1),va_u(1),pt_u(1),pt0_u(1),  &
L01441                         ptg(id),uhb_u(id,1),                            & 
L01442                         vhb_u(id,1),thb_u(id,1),ehb_u(id,1))            
L01443  
L01444  !        Calculation at the roof surfaces    
L01445           do iz=2,nz
L01446              if(ss(iz).gt.0)then
L01447                 call flux_flat(dz,z0(id,iz),ua_u(iz),                  &              
L01448                         va_u(iz),pt_u(iz),pt0_u(iz),                   &   
L01449                         ptr(id,iz),uhb_u(id,iz),                       &   
L01450                         vhb_u(id,iz),thb_u(id,iz),ehb_u(id,iz))        
L01451              else
L01452                 uhb_u(id,iz) = 0.0
L01453                 vhb_u(id,iz) = 0.0
L01454                 thb_u(id,iz) = 0.0
L01455                 ehb_u(id,iz) = 0.0
L01456              endif
L01457           end do
L01458  
L01459  !        Calculation at the wall surfaces         
L01460           do iz=1,nz         
L01461              call flux_wall(ua_u(iz),va_u(iz),pt_u(iz),da_u(iz),     &  
L01462                          ptw(2*id-1,iz),                             &   
L01463                          uva_u(2*id-1,iz),vva_u(2*id-1,iz),          &   
L01464                          uvb_u(2*id-1,iz),vvb_u(2*id-1,iz),          &   
L01465                          tva_u(2*id-1,iz),tvb_u(2*id-1,iz),          &   
L01466                          evb_u(2*id-1,iz),drst(id),dt)                  
L01467                      
L01468              call flux_wall(ua_u(iz),va_u(iz),pt_u(iz),da_u(iz),    &   
L01469                          ptw(2*id,iz),                              &    
L01470                          uva_u(2*id,iz),vva_u(2*id,iz),             &    
L01471                          uvb_u(2*id,iz),vvb_u(2*id,iz),             &    
L01472                          tva_u(2*id,iz),tvb_u(2*id,iz),             &   
L01473                          evb_u(2*id,iz),drst(id),dt) 
L01474  !
L01475         
L01476           end do
L01477           
L01478        end do
L01479                  
L01480        return
L01481        end subroutine buildings
```

> 与 14a §九差异：无积水缩放（wfg/wfr）、无绿屋顶/PV 混合、无 AC/通风源项（tvb_ac 不存在）、动量/温度/TKE 三类源项结构相同但输出少 qhb/qvb。

<!-- code_extract code_extract.py v1.2
source: phys/module_sf_bep.F
ranges: L1487-L1683
file_lines: 3536
file_md5: 5f74b56a221ca4ec69320a09ad3f9c3e
display: line-numbered (strip L-prefix and !file: line to restore)
range_md5: 883204dab798ddbccf03f5e081af886a
seg_lines: 197
label: subroutine urban_meso
-->

```fortran
!file: phys/module_sf_bep.F    L1487-L1683    (subroutine urban_meso)
L01487          subroutine urban_meso(nd,kms,kme,kts,kte,nz_u,z,dz,z_u,pb,ss,bs,ws,sf,vl,    &
L01488                               uva_u,vva_u,uvb_u,vvb_u,tva_u,tvb_u,evb_u, &       
L01489                               uhb_u,vhb_u,thb_u,ehb_u,                   &      
L01490                               a_u,a_v,a_t,a_e,b_u,b_v,b_t,b_e)           
L01491  
L01492  ! ----------------------------------------------------------------------
L01493  !  This routine interpolates the parameters from the "urban grid" to the
L01494  !  "mesoscale grid".
L01495  !  See p300-301 Appendix B.2 of the BLM paper.  
L01496  ! ----------------------------------------------------------------------
L01497  
L01498        implicit none
L01499  
L01500  ! ----------------------------------------------------------------------
L01501  ! INPUT:
L01502  ! ----------------------------------------------------------------------
L01503  ! Data relative to the "mesoscale grid"
L01504        integer kms,kme,kts,kte               
L01505        real z(kms:kme)              ! Altitude above the ground of the cell interface
L01506        real dz(kms:kme)               ! Vertical space steps
L01507  
L01508  ! Data relative to the "uban grid"
L01509        integer nz_u              ! Number of layer in the urban grid
L01510        integer nd                ! Number of street direction for the current urban class
L01511        real bs(ndm)              ! Building widths of the current urban class
L01512        real ws(ndm)              ! Street widths of the current urban class
L01513        real z_u(nz_um)         ! Height of the urban grid levels
L01514        real pb(nz_um)          ! Probability to have a building with an height equal
L01515        real ss(nz_um)          ! Probability to have a building with height h
L01516        real uhb_u(ndm,nz_um)   ! U (x-wind component) Horizontal surfaces, B (explicit) term
L01517        real uva_u(2*ndm,nz_um)   ! U (x-wind component) Vertical surfaces, A (implicit) term
L01518        real uvb_u(2*ndm,nz_um)   ! U (x-wind component) Vertical surfaces, B (explicit) term
L01519        real vhb_u(ndm,nz_um)   ! V (y-wind component) Horizontal surfaces, B (explicit) term
L01520        real vva_u(2*ndm,nz_um)   ! V (y-wind component) Vertical surfaces, A (implicit) term
L01521        real vvb_u(2*ndm,nz_um)   ! V (y-wind component) Vertical surfaces, B (explicit) term
L01522        real thb_u(ndm,nz_um)   ! Temperature        Horizontal surfaces, B (explicit) term
L01523        real tva_u(2*ndm,nz_um)   ! Temperature          Vertical surfaces, A (implicit) term
L01524        real tvb_u(2*ndm,nz_um)   ! Temperature          Vertical surfaces, B (explicit) term
L01525        real ehb_u(ndm,nz_um)   ! Energy (TKE)       Horizontal surfaces, B (explicit) term
L01526        real evb_u(2*ndm,nz_um)   ! Energy (TKE)         Vertical surfaces, B (explicit) term
L01527  
L01528  ! ----------------------------------------------------------------------
L01529  ! OUTPUT:
L01530  ! ----------------------------------------------------------------------
L01531  ! Data relative to the "mesoscale grid"
L01532        real sf(kms:kme)             ! Surface of the "mesoscale grid" cells taking into account the buildings
L01533        real vl(kms:kme)               ! Volume of the "mesoscale grid" cells taking into account the buildings
L01534        real a_u(kms:kme)              ! Implicit component of the momentum sources or sinks in the X-direction
L01535        real a_v(kms:kme)              ! Implicit component of the momentum sources or sinks in the Y-direction
L01536        real a_t(kms:kme)              ! Implicit component of the heat sources or sinks
L01537        real a_e(kms:kme)              ! Implicit component of the TKE sources or sinks
L01538        real b_u(kms:kme)              ! Explicit component of the momentum sources or sinks in the X-direction
L01539        real b_v(kms:kme)              ! Explicit component of the momentum sources or sinks in the Y-direction
L01540        real b_t(kms:kme)              ! Explicit component of the heat sources or sinks
L01541        real b_e(kms:kme)              ! Explicit component of the TKE sources or sinks
L01542        
L01543  ! ----------------------------------------------------------------------
L01544  ! LOCAL:
L01545  ! ----------------------------------------------------------------------
L01546        real dzz
L01547        real fact
L01548        integer id,iz,iz_u
L01549        real se,sr,st,su,sv
L01550        real uet(kms:kme)                ! Contribution to TKE due to walls
L01551        real veb,vta,vtb,vte,vtot,vua,vub,vva,vvb
L01552  
L01553  
L01554  ! ----------------------------------------------------------------------
L01555  ! END VARIABLES DEFINITIONS
L01556  ! ---------------------------------------------------------------------- 
L01557  
L01558  ! initialisation
L01559  
L01560        do iz=kts,kte
L01561           a_u(iz)=0.
L01562           a_v(iz)=0.
L01563           a_t(iz)=0.
L01564           a_e(iz)=0.
L01565           b_u(iz)=0.
L01566           b_v(iz)=0.
L01567           b_e(iz)=0.
L01568           b_t(iz)=0.
L01569           uet(iz)=0.
L01570        end do
L01571              
L01572  ! horizontal surfaces
L01573        do iz=kts,kte
L01574           sf(iz)=0.
L01575           vl(iz)=0.
L01576        enddo
L01577        sf(kte+1)=0. 
L01578        
L01579        do id=1,nd      
L01580           do iz=kts+1,kte+1
L01581              sr=0.
L01582              do iz_u=2,nz_u
L01583                 if(z(iz).lt.z_u(iz_u).and.z(iz).ge.z_u(iz_u-1))then
L01584                    sr=pb(iz_u)
L01585                 endif
L01586              enddo
L01587              sf(iz)=sf(iz)+((ws(id)+(1.-sr)*bs(id))/(ws(id)+bs(id)))/nd
L01588           enddo
L01589        enddo
L01590  
L01591  ! volume      
L01592        do iz=kts,kte
L01593           do id=1,nd
L01594              vtot=0.
L01595              do iz_u=1,nz_u
L01596                 dzz=max(min(z_u(iz_u+1),z(iz+1))-max(z_u(iz_u),z(iz)),0.)
L01597                 vtot=vtot+pb(iz_u+1)*dzz
L01598              enddo
L01599              vtot=vtot/(z(iz+1)-z(iz))
L01600              vl(iz)=vl(iz)+(1.-vtot*bs(id)/(ws(id)+bs(id)))/nd
L01601           enddo
L01602        enddo
L01603        
L01604  ! horizontal surface impact  
L01605  
L01606        do id=1,nd
L01607        
L01608           fact=1./vl(kts)/dz(kts)*ws(id)/(ws(id)+bs(id))/nd
L01609           b_t(kts)=b_t(kts)+thb_u(id,1)*fact
L01610           b_u(kts)=b_u(kts)+uhb_u(id,1)*fact
L01611           b_v(kts)=b_v(kts)+vhb_u(id,1)*fact 
L01612           b_e(kts)=b_e(kts)+ehb_u(id,1)*fact*(z_u(2)-z_u(1))
L01613           
L01614           do iz=kts,kte
L01615              st=0.
L01616              su=0.
L01617              sv=0.
L01618              se=0.
L01619              do iz_u=2,nz_u
L01620                 if(z(iz).le.z_u(iz_u).and.z(iz+1).gt.z_u(iz_u))then
L01621                    st=st+ss(iz_u)*thb_u(id,iz_u)
L01622                    su=su+ss(iz_u)*uhb_u(id,iz_u)
L01623                    sv=sv+ss(iz_u)*vhb_u(id,iz_u)          
L01624                    se=se+ss(iz_u)*ehb_u(id,iz_u)*(z_u(iz_u+1)-z_u(iz_u))
L01625                 endif
L01626              enddo
L01627        
L01628              fact=bs(id)/(ws(id)+bs(id))/vl(iz)/dz(iz)/nd
L01629              b_t(iz)=b_t(iz)+st*fact
L01630              b_u(iz)=b_u(iz)+su*fact
L01631              b_v(iz)=b_v(iz)+sv*fact
L01632              b_e(iz)=b_e(iz)+se*fact
L01633           enddo
L01634        enddo              
L01635  
L01636  ! vertical surface impact
L01637             
L01638        do iz=kts,kte 
L01639           uet(iz)=0.
L01640           do id=1,nd              
L01641              vtb=0.
L01642              vta=0.
L01643              vua=0.
L01644              vub=0.
L01645              vva=0.
L01646              vvb=0.
L01647              veb=0.
L01648  	    vte=0.
L01649              do iz_u=1,nz_u
L01650                 dzz=max(min(z_u(iz_u+1),z(iz+1))-max(z_u(iz_u),z(iz)),0.)
L01651                 fact=dzz/(ws(id)+bs(id))
L01652                 vtb=vtb+pb(iz_u+1)*                                  &        
L01653                      (tvb_u(2*id-1,iz_u)+tvb_u(2*id,iz_u))*fact   
L01654                 vta=vta+pb(iz_u+1)*                                  &        
L01655                     (tva_u(2*id-1,iz_u)+tva_u(2*id,iz_u))*fact
L01656                 vua=vua+pb(iz_u+1)*                                  &        
L01657                      (uva_u(2*id-1,iz_u)+uva_u(2*id,iz_u))*fact
L01658                 vva=vva+pb(iz_u+1)*                                  &        
L01659                      (vva_u(2*id-1,iz_u)+vva_u(2*id,iz_u))*fact
L01660                 vub=vub+pb(iz_u+1)*                                  &        
L01661                      (uvb_u(2*id-1,iz_u)+uvb_u(2*id,iz_u))*fact
L01662                 vvb=vvb+pb(iz_u+1)*                                  &        
L01663                      (vvb_u(2*id-1,iz_u)+vvb_u(2*id,iz_u))*fact
L01664                 veb=veb+pb(iz_u+1)*                                  &        
L01665                      (evb_u(2*id-1,iz_u)+evb_u(2*id,iz_u))*fact
L01666              enddo
L01667             
L01668              fact=1./vl(iz)/dz(iz)/nd
L01669              b_t(iz)=b_t(iz)+vtb*fact
L01670              a_t(iz)=a_t(iz)+vta*fact
L01671              a_u(iz)=a_u(iz)+vua*fact
L01672              a_v(iz)=a_v(iz)+vva*fact
L01673              b_u(iz)=b_u(iz)+vub*fact
L01674              b_v(iz)=b_v(iz)+vvb*fact
L01675              b_e(iz)=b_e(iz)+veb*fact
L01676              uet(iz)=uet(iz)+vte*fact
L01677           enddo              
L01678        enddo
L01679        
L01680  
L01681        
L01682        return
L01683        end subroutine urban_meso
```

<!-- code_extract code_extract.py v1.2
source: phys/module_sf_bep.F
ranges: L1689-L1769
file_lines: 3536
file_md5: 5f74b56a221ca4ec69320a09ad3f9c3e
display: line-numbered (strip L-prefix and !file: line to restore)
range_md5: 545d8d8f737e572f2b8b29104113b1cb
seg_lines: 81
label: subroutine interp_length
-->

```fortran
!file: phys/module_sf_bep.F    L1689-L1769    (subroutine interp_length)
L01689        subroutine interp_length(nd,kms,kme,kts,kte,nz_u,z_u,z,ss,ws,bs,              &
L01690                               dlg,dl_u)
L01691  
L01692  ! ----------------------------------------------------------------------     
L01693  !    Calculation of the length scales
L01694  !    See p272-274 formula (22) and (24) of the BLM paper    
L01695  ! ----------------------------------------------------------------------     
L01696       
L01697        implicit none
L01698  
L01699  
L01700  ! ----------------------------------------------------------------------     
L01701  ! INPUT:
L01702  ! ----------------------------------------------------------------------     
L01703        integer kms,kme,kts,kte                
L01704        real z(kms:kme)              ! Altitude above the ground of the cell interface
L01705        integer nd                ! Number of street direction for the current urban class
L01706        integer nz_u              ! Number of levels in the "urban grid"
L01707        real z_u(nz_um)         ! Height of the urban grid levels
L01708        real bs(ndm)              ! Building widths of the current urban class
L01709        real ss(nz_um)          ! Probability to have a building with height h
L01710        real ws(ndm)              ! Street widths of the current urban class
L01711  
L01712  
L01713  ! ----------------------------------------------------------------------     
L01714  ! OUTPUT:
L01715  ! ----------------------------------------------------------------------     
L01716        real dlg(kms:kme)              ! Height above ground (L_ground in formula (24) of the BLM paper). 
L01717        real dl_u(kms:kme)             ! Length scale (lb in formula (22) ofthe BLM paper).
L01718  
L01719  ! ----------------------------------------------------------------------
L01720  ! LOCAL:
L01721  ! ----------------------------------------------------------------------
L01722        real dlgtmp
L01723        integer id,iz,iz_u
L01724        real sftot
L01725        real ulu,ssl
L01726  
L01727  ! ----------------------------------------------------------------------
L01728  ! END VARIABLES DEFINITIONS
L01729  ! ----------------------------------------------------------------------
L01730     
L01731          do iz=kts,kte
L01732           ulu=0.
L01733           ssl=0.
L01734           do id=1,nd        
L01735            do iz_u=2,nz_u
L01736             if(z_u(iz_u).gt.z(iz))then
L01737              ulu=ulu+ss(iz_u)/z_u(iz_u)/nd
L01738              ssl=ssl+ss(iz_u)/nd
L01739             endif
L01740            enddo
L01741           enddo
L01742  
L01743          if(ulu.ne.0)then
L01744            dl_u(iz)=ssl/ulu
L01745           else
L01746            dl_u(iz)=0.
L01747           endif
L01748          enddo
L01749         
L01750  
L01751          do iz=kts,kte
L01752           dlg(iz)=0.
L01753            do id=1,nd
L01754             sftot=ws(id)  
L01755             dlgtmp=ws(id)/((z(iz)+z(iz+1))/2.)
L01756             do iz_u=1,nz_u
L01757              if((z(iz)+z(iz+1))/2..gt.z_u(iz_u))then
L01758               dlgtmp=dlgtmp+ss(iz_u)*bs(id)/                           &                
L01759                      ((z(iz)+z(iz+1))/2.-z_u(iz_u))
L01760               sftot=sftot+ss(iz_u)*bs(id)
L01761              endif
L01762             enddo
L01763             dlg(iz)=dlg(iz)+dlgtmp/sftot/nd
L01764           enddo
L01765           dlg(iz)=1./dlg(iz)
L01766          enddo
L01767          
L01768         return
L01769         end subroutine interp_length
```

> 与 14b §二同源；urban_meso 少 tvb_ac/b_ac 分账。

<!-- code_extract code_extract.py v1.2
source: phys/module_sf_bep.F
ranges: L2668-L2770
file_lines: 3536
file_md5: 5f74b56a221ca4ec69320a09ad3f9c3e
display: line-numbered (strip L-prefix and !file: line to restore)
range_md5: bbb3655cc13378ef40f6e022b9a0a97a
seg_lines: 103
label: subroutine icBEP
-->

```fortran
!file: phys/module_sf_bep.F    L2668-L2770    (subroutine icBEP)
L02668        subroutine icBEP (nd_u,h_b,d_b,ss_u,pb_u,nz_u,z_u)                               
L02669  
L02670        implicit none       
L02671          
L02672  
L02673  !    Street parameters
L02674        integer nd_u(nurbm)     ! Number of street direction for each urban class
L02675        real h_b(nz_um,nurbm)   ! Bulding's heights [m]
L02676        real d_b(nz_um,nurbm)   ! The probability that a building has an height h_b
L02677  ! -----------------------------------------------------------------------
L02678  !     Output
L02679  !------------------------------------------------------------------------
L02680  
L02681        real ss_u(nz_um,nurbm)     ! The probability that a building has an height equal to z
L02682        real pb_u(nz_um,nurbm)     ! The probability that a building has an height greater or equal to z
L02683          
L02684  !    Grid parameters
L02685        integer nz_u(nurbm)     ! Number of layer in the urban grid
L02686        real z_u(nz_um)       ! Height of the urban grid levels
L02687  
L02688  
L02689  ! -----------------------------------------------------------------------
L02690  !     Local
L02691  !------------------------------------------------------------------------
L02692  
L02693        integer iz_u,id,ilu,iurb
L02694  
L02695        real dtot
L02696        real hbmax
L02697  
L02698  !------------------------------------------------------------------------
L02699       
L02700  
L02701  ! -----------------------------------------------------------------------
L02702  !     This routine initialise the urban paramters for the BEP module
L02703  !------------------------------------------------------------------------
L02704  !
L02705  !Initialize variables
L02706  !
L02707        z_u=0.
L02708        nz_u=0
L02709        ss_u=0.
L02710        pb_u=0.
L02711  
L02712  ! Computation of the urban levels height
L02713  
L02714        z_u(1)=0.
L02715       
L02716        do iz_u=1,nz_um-1
L02717           z_u(iz_u+1)=z_u(iz_u)+dz_u
L02718        enddo
L02719        
L02720  ! Normalisation of the building density
L02721  
L02722        do iurb=1,nurbm
L02723           dtot=0.
L02724           do ilu=1,nz_um
L02725              dtot=dtot+d_b(ilu,iurb)
L02726           enddo
L02727           do ilu=1,nz_um
L02728              d_b(ilu,iurb)=d_b(ilu,iurb)/dtot
L02729           enddo
L02730        enddo      
L02731  
L02732  ! Compute the view factors, pb and ss 
L02733        
L02734        do iurb=1,nurbm         
L02735           hbmax=0.
L02736           nz_u(iurb)=0
L02737           do ilu=1,nz_um
L02738              if(h_b(ilu,iurb).gt.hbmax)hbmax=h_b(ilu,iurb)
L02739           enddo
L02740           
L02741           do iz_u=1,nz_um-1
L02742              if(z_u(iz_u+1).gt.hbmax)go to 10
L02743           enddo
L02744           
L02745   10      continue
L02746           nz_u(iurb)=iz_u+1
L02747  
L02748           do id=1,nd_u(iurb)
L02749  
L02750              do iz_u=1,nz_u(iurb)
L02751                 ss_u(iz_u,iurb)=0.
L02752                 do ilu=1,nz_um
L02753                    if(z_u(iz_u).le.h_b(ilu,iurb)                      &    
L02754                      .and.z_u(iz_u+1).gt.h_b(ilu,iurb))then            
L02755                          ss_u(iz_u,iurb)=ss_u(iz_u,iurb)+d_b(ilu,iurb)
L02756                    endif 
L02757                 enddo
L02758              enddo
L02759  
L02760              pb_u(1,iurb)=1.
L02761              do iz_u=1,nz_u(iurb)
L02762                 pb_u(iz_u+1,iurb)=max(0.,pb_u(iz_u,iurb)-ss_u(iz_u,iurb))
L02763              enddo
L02764  
L02765           enddo
L02766        end do
L02767       
L02768                    
L02769        return       
L02770        end subroutine icBEP
```

<!-- code_extract code_extract.py v1.2
source: phys/module_sf_bep.F
ranges: L2775-L2934
file_lines: 3536
file_md5: 5f74b56a221ca4ec69320a09ad3f9c3e
display: line-numbered (strip L-prefix and !file: line to restore)
range_md5: 79bce6bbbcf58a88cdedebba230242e5
seg_lines: 160
label: subroutine view_factors
-->

```fortran
!file: phys/module_sf_bep.F    L2775-L2934    (subroutine view_factors)
L02775        subroutine view_factors(iurb,nz_u,id,dxy,z,ws,fww,fwg,fgw,fsg,fsw,fws) 
L02776       
L02777        implicit none
L02778  
L02779   
L02780  
L02781  ! -----------------------------------------------------------------------
L02782  !     Input
L02783  !------------------------------------------------------------------------
L02784  
L02785        integer iurb            ! Number of the urban class
L02786        integer nz_u            ! Number of levels in the urban grid
L02787        integer id              ! Street direction number
L02788        real ws                 ! Street width
L02789        real z(nz_um)         ! Height of the urban grid levels
L02790        real dxy                ! Street lenght
L02791  
L02792  
L02793  ! -----------------------------------------------------------------------
L02794  !     Output
L02795  !------------------------------------------------------------------------
L02796  
L02797  !   fww,fwg,fgw,fsw,fsg are the view factors used to compute the long wave
L02798  !   and the short wave radation. They are the part of radiation from a surface
L02799  !   or from the sky to another surface.
L02800  
L02801        real fww(nz_um,nz_um,ndm,nurbm)            !  from wall to wall
L02802        real fwg(nz_um,ndm,nurbm)                  !  from wall to ground
L02803        real fgw(nz_um,ndm,nurbm)                  !  from ground to wall
L02804        real fsw(nz_um,ndm,nurbm)                  !  from sky to wall
L02805        real fws(nz_um,ndm,nurbm)                  !  from wall to sky
L02806        real fsg(ndm,nurbm)                        !  from sky to ground
L02807  
L02808  
L02809  ! -----------------------------------------------------------------------
L02810  !     Local
L02811  !------------------------------------------------------------------------
L02812  
L02813        integer jz,iz
L02814  
L02815        real hut
L02816        real f1,f2,f12,f23,f123,ftot
L02817        real fprl,fnrm
L02818        real a1,a2,a3,a4,a12,a23,a123
L02819  
L02820  ! -----------------------------------------------------------------------
L02821  !     This routine calculates the view factors
L02822  !------------------------------------------------------------------------
L02823          
L02824        hut=z(nz_u+1)
L02825          
L02826        do jz=1,nz_u      
L02827        
L02828  ! radiation from wall to wall
L02829         
L02830           do iz=1,nz_u
L02831       
L02832              call fprls (fprl,dxy,abs(z(jz+1)-z(iz  )),ws)
L02833              f123=fprl
L02834              call fprls (fprl,dxy,abs(z(jz+1)-z(iz+1)),ws)
L02835              f23=fprl
L02836              call fprls (fprl,dxy,abs(z(jz  )-z(iz  )),ws)
L02837              f12=fprl
L02838              call fprls (fprl,dxy,abs(z(jz  )-z(iz+1)),ws)
L02839              f2 = fprl
L02840         
L02841              a123=dxy*(abs(z(jz+1)-z(iz  )))
L02842              a12 =dxy*(abs(z(jz  )-z(iz  )))
L02843              a23 =dxy*(abs(z(jz+1)-z(iz+1)))
L02844              a1  =dxy*(abs(z(iz+1)-z(iz  )))
L02845              a2  =dxy*(abs(z(jz  )-z(iz+1)))
L02846              a3  =dxy*(abs(z(jz+1)-z(jz  )))
L02847         
L02848              ftot=0.5*(a123*f123-a23*f23-a12*f12+a2*f2)/a1
L02849         
L02850              fww(iz,jz,id,iurb)=ftot*a1/a3
L02851  
L02852           enddo 
L02853  
L02854  ! radiation from ground to wall
L02855         
L02856           call fnrms (fnrm,z(jz+1),dxy,ws)
L02857           f12=fnrm
L02858           call fnrms (fnrm,z(jz)  ,dxy,ws)
L02859           f1=fnrm
L02860         
L02861           a1 = ws*dxy
L02862           
L02863           a12= ws*dxy
L02864         
L02865           a4=(z(jz+1)-z(jz))*dxy
L02866         
L02867           ftot=(a12*f12-a12*f1)/a1
L02868                      
L02869           fgw(jz,id,iurb)=ftot*a1/a4
L02870       
L02871  !  radiation from sky to wall
L02872       
L02873           call fnrms(fnrm,hut-z(jz)  ,dxy,ws)
L02874           f12 = fnrm
L02875           call fnrms (fnrm,hut-z(jz+1),dxy,ws)
L02876           f1 =fnrm
L02877         
L02878           a1 = ws*dxy
L02879         
L02880           a12= ws*dxy
L02881                
L02882           a4 = (z(jz+1)-z(jz))*dxy
L02883         
L02884           ftot=(a12*f12-a12*f1)/a1
L02885          
L02886           fsw(jz,id,iurb)=ftot*a1/a4       
L02887        
L02888        enddo
L02889  
L02890  ! radiation from wall to sky      
L02891        do iz=1,nz_u
L02892         call fnrms(fnrm,ws,dxy,hut-z(iz))
L02893         f12=fnrm
L02894         call fnrms(fnrm,ws,dxy,hut-z(iz+1))
L02895         f1=fnrm
L02896         a1 = (z(iz+1)-z(iz))*dxy
L02897         a2 = (hut-z(iz+1))*dxy
L02898         a12= (hut-z(iz))*dxy
L02899         a4 = ws*dxy
L02900         ftot=(a12*f12-a2*f1)/a1
L02901         fws(iz,id,iurb)=ftot*a1/a4 
L02902   
L02903        enddo
L02904  !!!!!!!!!!!!!
L02905  
L02906  
L02907         do iz=1,nz_u
L02908  
L02909  ! radiation from wall to ground
L02910        
L02911           call fnrms (fnrm,ws,dxy,z(iz+1))
L02912           f12=fnrm
L02913           call fnrms (fnrm,ws,dxy,z(iz  ))
L02914           f1 =fnrm
L02915           
L02916           a1= (z(iz+1)-z(iz) )*dxy
L02917         
L02918           a2 = z(iz)*dxy
L02919           a12= z(iz+1)*dxy
L02920           a4 = ws*dxy
L02921  
L02922           ftot=(a12*f12-a2*f1)/a1        
L02923                      
L02924           fwg(iz,id,iurb)=ftot*a1/a4
L02925          
L02926        enddo
L02927  
L02928  ! radiation from sky to ground
L02929        
L02930        call fprls (fprl,dxy,ws,hut)
L02931        fsg(id,iurb)=fprl
L02932  
L02933        return
L02934        end subroutine view_factors
```

<!-- code_extract code_extract.py v1.2
source: phys/module_sf_bep.F
ranges: L2939-L2964
file_lines: 3536
file_md5: 5f74b56a221ca4ec69320a09ad3f9c3e
display: line-numbered (strip L-prefix and !file: line to restore)
range_md5: 8450764fa6fbbf853c194461cff4c148
seg_lines: 26
label: subroutine fprls
-->

```fortran
!file: phys/module_sf_bep.F    L2939-L2964    (subroutine fprls)
L02939        SUBROUTINE fprls (fprl,a,b,c)
L02940  
L02941        implicit none
L02942  
L02943       
L02944              
L02945        real a,b,c
L02946        real x,y
L02947        real fprl
L02948  
L02949  
L02950        x=a/c
L02951        y=b/c
L02952        
L02953        if(a.eq.0.or.b.eq.0.)then
L02954         fprl=0.
L02955        else
L02956         fprl=log( ( (1.+x**2)*(1.+y**2)/(1.+x**2+y**2) )**.5)+  &
L02957             y*((1.+x**2)**.5)*atan(y/((1.+x**2)**.5))+          &  
L02958             x*((1.+y**2)**.5)*atan(x/((1.+y**2)**.5))-          &   
L02959             y*atan(y)-x*atan(x)
L02960         fprl=fprl*2./(pi*x*y)
L02961        endif
L02962        
L02963        return
L02964        end subroutine fprls
```

<!-- code_extract code_extract.py v1.2
source: phys/module_sf_bep.F
ranges: L2969-L2997
file_lines: 3536
file_md5: 5f74b56a221ca4ec69320a09ad3f9c3e
display: line-numbered (strip L-prefix and !file: line to restore)
range_md5: 9fbc43a3b7811126fa69ac91f1b2d631
seg_lines: 29
label: subroutine fnrms
-->

```fortran
!file: phys/module_sf_bep.F    L2969-L2997    (subroutine fnrms)
L02969        SUBROUTINE fnrms (fnrm,a,b,c)
L02970  
L02971        implicit none
L02972  
L02973  
L02974  
L02975        real a,b,c
L02976        real x,y,z,a1,a2,a3,a4,a5,a6
L02977        real fnrm
L02978        
L02979        x=a/b
L02980        y=c/b
L02981        z=x**2+y**2
L02982        
L02983        if(y.eq.0.or.x.eq.0)then
L02984         fnrm=0.
L02985        else
L02986         a1=log( (1.+x*x)*(1.+y*y)/(1.+z) )
L02987         a2=y*y*log(y*y*(1.+z)/z/(1.+y*y) )
L02988         a3=x*x*log(x*x*(1.+z)/z/(1.+x*x) )
L02989         a4=y*atan(1./y)
L02990         a5=x*atan(1./x)
L02991         a6=sqrt(z)*atan(1./sqrt(z))
L02992         fnrm=0.25*(a1+a2+a3)+a4+a5-a6
L02993         fnrm=fnrm/(pi*y)
L02994        endif
L02995        
L02996        return
L02997        end subroutine fnrms
```

<!-- code_extract code_extract.py v1.2
source: phys/module_sf_bep.F
ranges: L3321-L3377
file_lines: 3536
file_md5: 5f74b56a221ca4ec69320a09ad3f9c3e
display: line-numbered (strip L-prefix and !file: line to restore)
range_md5: 370fc3cd6e8bc82119dff234345e152c
seg_lines: 57
label: subroutine icBEP_XY
-->

```fortran
!file: phys/module_sf_bep.F    L3321-L3377    (subroutine icBEP_XY)
L03321        subroutine icBEP_XY(iurb,fww_u,fwg_u,fgw_u,fsw_u,             &
L03322                            fws_u,fsg_u,ndu,strd,ws,nzu,z_u)                               
L03323  
L03324        implicit none       
L03325          
L03326  !    Street parameters
L03327        integer ndu     ! Number of street direction for each urban class
L03328        integer iurb
L03329  
L03330        real strd(ndm)        ! Street length (fix to greater value to the horizontal length of the cells)
L03331        real ws(ndm)          ! Street width [m]
L03332  
L03333  !    Grid parameters
L03334        integer nzu          ! Number of layer in the urban grid
L03335        real z_u(nz_um)       ! Height of the urban grid levels
L03336  ! -----------------------------------------------------------------------
L03337  !     Output
L03338  !------------------------------------------------------------------------
L03339  
L03340  !   fww_u,fwg_u,fgw_u,fsw_u,fsg_u are the view factors used to compute the long wave
L03341  !   and the short wave radation. They are the part of radiation from a surface
L03342  !   or from the sky to another surface.
L03343  
L03344        real fww_u(nz_um,nz_um,ndm,nurbm)         !  from wall to wall
L03345        real fwg_u(nz_um,ndm,nurbm)               !  from wall to ground
L03346        real fgw_u(nz_um,ndm,nurbm)               !  from ground to wall
L03347        real fsw_u(nz_um,ndm,nurbm)               !  from sky to wall
L03348        real fws_u(nz_um,ndm,nurbm)               !  from sky to wall
L03349        real fsg_u(ndm,nurbm)                     !  from sky to ground
L03350  
L03351  ! -----------------------------------------------------------------------
L03352  !     Local
L03353  !------------------------------------------------------------------------
L03354  
L03355        integer id
L03356  
L03357  ! -----------------------------------------------------------------------
L03358  !     This routine compute the view factors
L03359  !------------------------------------------------------------------------
L03360  !
L03361  !Initialize
L03362  !
L03363        fww_u=0.
L03364        fwg_u=0.
L03365        fgw_u=0.
L03366        fsw_u=0.
L03367        fws_u=0.
L03368        fsg_u=0.
L03369        
L03370        do id=1,ndu
L03371  
L03372              call view_factors(iurb,nzu,id,strd(id),z_u,ws(id),  &    
L03373                                fww_u,fwg_u,fgw_u,fsg_u,fsw_u,fws_u) 
L03374        
L03375        enddo               
L03376        return       
L03377        end subroutine icBEP_XY
```

<!-- code_extract code_extract.py v1.2
source: phys/module_sf_bep.F
ranges: L3381-L3497
file_lines: 3536
file_md5: 5f74b56a221ca4ec69320a09ad3f9c3e
display: line-numbered (strip L-prefix and !file: line to restore)
range_md5: 166045ea6a800b28d68e2d494d31cc32
seg_lines: 117
label: subroutine icBEPHI_XY
-->

```fortran
!file: phys/module_sf_bep.F    L3381-L3497    (subroutine icBEPHI_XY)
L03381        subroutine icBEPHI_XY(hb_u,hi_urb1D,ss_u,pb_u,nzu,z_u)
L03382  
L03383        implicit none   
L03384  !-----------------------------------------------------------------------
L03385  !    Inputs
L03386  !-----------------------------------------------------------------------
L03387  !    Street parameters
L03388  !
L03389        real hi_urb1D(nz_um)    ! The probability that a building has an height h_b
L03390  !
L03391  !     Grid parameters
L03392  !
L03393        real z_u(nz_um)         ! Height of the urban grid levels
L03394  ! -----------------------------------------------------------------------
L03395  !     Output
L03396  !------------------------------------------------------------------------
L03397  
L03398        real ss_u(nz_um)   ! The probability that a building has an height equal to z
L03399        real pb_u(nz_um)         ! The probability that a building has an height greater or equal to z
L03400  !        
L03401  !    Grid parameters
L03402  !
L03403        integer nzu                ! Number of layer in the urban grid
L03404  
L03405  ! -----------------------------------------------------------------------
L03406  !     Local
L03407  !------------------------------------------------------------------------
L03408        real hb_u(nz_um)        ! Bulding's heights [m]
L03409        integer iz_u,id,ilu
L03410  
L03411        real dtot
L03412        real hbmax
L03413  
L03414  !------------------------------------------------------------------------
L03415  
L03416  !Initialize variables
L03417  !
L03418        
L03419        nzu=0
L03420        ss_u=0.
L03421        pb_u=0.
L03422        
L03423  ! Normalisation of the building density
L03424  
L03425           dtot=0.
L03426           hb_u=0.
L03427  
L03428           do ilu=1,nz_um
L03429              dtot=dtot+hi_urb1D(ilu)
L03430           enddo
L03431           
L03432           do ilu=1,nz_um
L03433              if (hi_urb1D(ilu)<0.) then
L03434  !              write(*,*) 'WARNING, HI_URB1D(ilu) < 0 IN BEP'
L03435                 go to 20
L03436              endif
L03437           enddo
L03438  
L03439           if (dtot.gt.0.) then
L03440              continue
L03441           else
L03442  !           write(*,*) 'WARNING, HI_URB1D <= 0 IN BEP'
L03443              go to 20
L03444           endif
L03445  
L03446           do ilu=1,nz_um
L03447              hi_urb1D(ilu)=hi_urb1D(ilu)/dtot
L03448           enddo
L03449           
L03450           hb_u(1)=dz_u   
L03451           do ilu=2,nz_um
L03452              hb_u(ilu)=dz_u+hb_u(ilu-1)
L03453           enddo
L03454             
L03455  
L03456  ! Compute pb and ss 
L03457        
L03458              
L03459           hbmax=0.
L03460         
L03461           do ilu=1,nz_um
L03462              if (hi_urb1D(ilu)>0.and.hi_urb1D(ilu)<=1.) then
L03463                  hbmax=hb_u(ilu)
L03464              endif
L03465           enddo
L03466           
L03467           do iz_u=1,nz_um-1
L03468              if(z_u(iz_u+1).gt.hbmax)go to 10
L03469           enddo
L03470  
L03471  10       continue 
L03472          
L03473           nzu=iz_u+1
L03474  
L03475           if ((nzu+1).gt.nz_um) then 
L03476               write(*,*) 'error, nz_um has to be increased to at least',nzu+1
L03477               stop
L03478           endif
L03479  
L03480              do iz_u=1,nzu
L03481                 ss_u(iz_u)=0.
L03482                 do ilu=1,nz_um
L03483                    if(z_u(iz_u).le.hb_u(ilu)                      &    
L03484                      .and.z_u(iz_u+1).gt.hb_u(ilu))then            
L03485                          ss_u(iz_u)=ss_u(iz_u)+hi_urb1D(ilu)
L03486                    endif 
L03487                 enddo
L03488              enddo
L03489  
L03490              pb_u(1)=1.
L03491              do iz_u=1,nzu
L03492                 pb_u(iz_u+1)=max(0.,pb_u(iz_u)-ss_u(iz_u))
L03493              enddo
L03494  
L03495  20    continue    
L03496        return
L03497        end subroutine icBEPHI_XY
```

> 与 14b §六同源；差异同上（无绿屋顶/无 BEM 维度）。icBEP_XY 的 strd 同样固定 1e5 m（无限长峡谷）。

<!-- code_extract code_extract.py v1.2
source: phys/module_sf_bep.F
ranges: L3000-L3108
file_lines: 3536
file_md5: 5f74b56a221ca4ec69320a09ad3f9c3e
display: line-numbered (strip L-prefix and !file: line to restore)
range_md5: 9b6ab35b082253fc4b099f2218e388ae
seg_lines: 109
label: subroutine init_para
-->

```fortran
!file: phys/module_sf_bep.F    L3000-L3108    (subroutine init_para)
L03000        SUBROUTINE init_para(alag_u,alaw_u,alar_u,csg_u,csw_u,csr_u,&
L03001                  twini_u,trini_u,tgini_u,albg_u,albw_u,albr_u,emg_u,emw_u,&
L03002                  emr_u,z0g_u,z0r_u,nd_u,strd_u,drst_u,ws_u,bs_u,h_b,d_b)
L03003  
L03004  ! initialization routine, where the variables from the table are read
L03005  
L03006        implicit none
L03007        
L03008        integer iurb            ! urban class number
L03009  !    Building parameters      
L03010        real alag_u(nurbm)      ! Ground thermal diffusivity [m^2 s^-1]
L03011        real alaw_u(nurbm)      ! Wall thermal diffusivity [m^2 s^-1]
L03012        real alar_u(nurbm)      ! Roof thermal diffusivity [m^2 s^-1]
L03013        real csg_u(nurbm)       ! Specific heat of the ground material [J m^3 K^-1]
L03014        real csw_u(nurbm)       ! Specific heat of the wall material [J m^3 K^-1]
L03015        real csr_u(nurbm)       ! Specific heat of the roof material [J m^3 K^-1]
L03016        real twini_u(nurbm)     ! Temperature inside the buildings behind the wall [K]
L03017        real trini_u(nurbm)     ! Temperature inside the buildings behind the roof [K]
L03018        real tgini_u(nurbm)     ! Initial road temperature
L03019  
L03020  !    Radiation parameters
L03021        real albg_u(nurbm)      ! Albedo of the ground
L03022        real albw_u(nurbm)      ! Albedo of the wall
L03023        real albr_u(nurbm)      ! Albedo of the roof
L03024        real emg_u(nurbm)       ! Emissivity of ground
L03025        real emw_u(nurbm)       ! Emissivity of wall
L03026        real emr_u(nurbm)       ! Emissivity of roof
L03027  
L03028  !    Roughness parameters
L03029        real z0g_u(nurbm)       ! The ground's roughness length      
L03030        real z0r_u(nurbm)       ! The roof's roughness length
L03031  
L03032  !    Street parameters
L03033        integer nd_u(nurbm)     ! Number of street direction for each urban class
L03034  
L03035        real strd_u(ndm,nurbm)  ! Street length (fix to greater value to the horizontal length of the cells)
L03036        real drst_u(ndm,nurbm)  ! Street direction [degree]
L03037        real ws_u(ndm,nurbm)    ! Street width [m]
L03038        real bs_u(ndm,nurbm)    ! Building width [m]
L03039        real h_b(nz_um,nurbm)   ! Bulding's heights [m]
L03040        real d_b(nz_um,nurbm)   ! The probability that a building has an height h_b
L03041  
L03042        integer i,iu
L03043        integer nurb ! number of urban classes used
L03044  
L03045  !
L03046  !Initialize some variables
L03047  !
L03048         
L03049         h_b=0.
L03050         d_b=0.
L03051  
L03052         nurb=ICATE
L03053         do iu=1,nurb                         
L03054            nd_u(iu)=0
L03055         enddo
L03056  
L03057         csw_u=CAPB_TBL / (( 1.0 / 4.1868 ) * 1.E-6)
L03058         csr_u=CAPR_TBL / (( 1.0 / 4.1868 ) * 1.E-6)
L03059         csg_u=CAPG_TBL / (( 1.0 / 4.1868 ) * 1.E-6)
L03060         do i=1,icate
L03061           alaw_u(i)=AKSB_TBL(i) / csw_u(i) / (( 1.0 / 4.1868 ) * 1.E-2)
L03062           alar_u(i)=AKSR_TBL(i) / csr_u(i) / (( 1.0 / 4.1868 ) * 1.E-2)
L03063           alag_u(i)=AKSG_TBL(i) / csg_u(i) / (( 1.0 / 4.1868 ) * 1.E-2)
L03064         enddo
L03065         twini_u=TBLEND_TBL
L03066         trini_u=TRLEND_TBL
L03067         tgini_u=TGLEND_TBL
L03068         albw_u=ALBB_TBL
L03069         albr_u=ALBR_TBL
L03070         albg_u=ALBG_TBL
L03071         emw_u=EPSB_TBL
L03072         emr_u=EPSR_TBL
L03073         emg_u=EPSG_TBL
L03074         z0r_u=Z0R_TBL
L03075         z0g_u=Z0G_TBL
L03076         nd_u=NUMDIR_TBL
L03077         do iu=1,icate
L03078                if(ndm.lt.nd_u(iu))then
L03079                  write(*,*)'ndm too small in module_sf_bep, please increase to at least ', nd_u(iu)
L03080                  write(*,*)'remember also that urban_map_zrd should be equal or greater than nz_um*ndm*nwr-u!'
L03081                  stop
L03082                endif
L03083           do i=1,nd_u(iu)
L03084             drst_u(i,iu)=STREET_DIRECTION_TBL(i,iu) * pi/180.
L03085             ws_u(i,iu)=STREET_WIDTH_TBL(i,iu)
L03086             bs_u(i,iu)=BUILDING_WIDTH_TBL(i,iu)
L03087           enddo
L03088         enddo
L03089         do iu=1,ICATE
L03090            if(nz_um.lt.numhgt_tbl(iu)+3)then
L03091                write(*,*)'nz_um too small in module_sf_bep, please increase to at least ',numhgt_tbl(iu)+3
L03092                write(*,*)'remember also that urban_map_zrd should be equal or greater than nz_um*ndm*nwr-u!'
L03093                stop
L03094            endif
L03095           do i=1,NUMHGT_TBL(iu)
L03096             h_b(i,iu)=HEIGHT_BIN_TBL(i,iu)
L03097             d_b(i,iu)=HPERCENT_BIN_TBL(i,iu)
L03098           enddo
L03099         enddo
L03100  
L03101         do i=1,ndm
L03102          do iu=1,nurbm
L03103           strd_u(i,iu)=100000.
L03104          enddo
L03105         enddo
L03106           
L03107         return
L03108        END SUBROUTINE init_para
```

> 与 14b 版差异：只读 TBL 的 BEP 所需子集——**无任何窗户/BEM 量**（无 albwin_u/emwind_u/cop_u 等；BEP 单独版根本没有窗户辐射成分）；albwindow/foncs 单元只存在于 bep_bem（14b §七），两文件互不调用——「跨模块隐性依赖」的说法不成立，此前的疑点已核销。守卫信息串同源（ndm/nz_um 下限检查）。

<!-- code_extract code_extract.py v1.2
source: phys/module_sf_bep.F
ranges: L3112-L3189
file_lines: 3536
file_md5: 5f74b56a221ca4ec69320a09ad3f9c3e
display: line-numbered (strip L-prefix and !file: line to restore)
range_md5: cbaa9c6591a4944fb905ea34e31c8cd5
seg_lines: 78
label: subroutine angle
-->

```fortran
!file: phys/module_sf_bep.F    L3112-L3189    (subroutine angle)
L03112        subroutine angle(along,alat,day,realt,zr,deltar,ah)
L03113  !     ----------------     
L03114  !      
L03115  !         Computation of the solar angles
L03116  !         schayes (1982,atm.  env. , p1407)
L03117  ! Inputs
L03118  !========================
L03119  ! along=longitud
L03120  ! alat=latitude
L03121  ! day=julian day (from the beginning of the year)
L03122  ! realt= time GMT in hours
L03123  ! Outputs
L03124  !============================
L03125  ! zr=solar zenith angle
L03126  ! deltar=declination angle
L03127  ! ah=hour angle
L03128  !===============================
L03129  
L03130        implicit none
L03131        real along,alat, realt, zr, deltar, ah, arg
L03132        real rad,om,radh,initt, pii, drad, alongt, cphi, sphi
L03133        real c1, c2, c3, s1, s2, s3, delta, rmsr2, cd, sid 
L03134        real et, ahor, chor, coznt 
L03135        integer day 
L03136  
L03137  
L03138        data rad,om,radh,initt/0.0174533,0.0172142,0.26179939,0/
L03139   
L03140         zr=0.
L03141         deltar=0.
L03142         ah=0.
L03143  
L03144         pii = 3.14159265358979312
L03145         drad = pii/180.
L03146        
L03147         alongt=along/15.
L03148         cphi=cos(alat*drad)
L03149         sphi=sin(alat*drad)
L03150  !
L03151  !     declination
L03152  !
L03153         arg=om*day
L03154         c1=cos(arg)
L03155         c2=cos(2.*arg)
L03156         c3=cos(3.*arg)
L03157         s1=sin(arg)
L03158         s2=sin(2.*arg)
L03159         s3=sin(3.*arg)
L03160         delta=0.33281-22.984*c1-0.3499*c2-0.1398*c3+3.7872*s1+0.03205*s2+0.07187*s3
L03161         rmsr2=(1./(1.-0.01673*c1))**2
L03162         deltar=delta*rad
L03163         cd=cos(deltar)
L03164         sid=sin(deltar)
L03165  !
L03166  !     time equation in hours
L03167  !
L03168         et=0.0072*c1-0.0528*c2-0.0012*c3-0.1229*s1-0.1565*s2-0.0041*s3
L03169  !
L03170  !
L03171  !   hour angle  
L03172  !
L03173        
L03174  !      ifh=0
L03175        
L03176   !     ahor=realt-12.+ifh+et+alongt
L03177        ahor=realt-12.+et+alongt
L03178        ah=ahor*radh
L03179        chor=cos(ah)
L03180  !
L03181  !    zenith angle
L03182  !
L03183        coznt=sphi*sid+cphi*cd*chor
L03184        
L03185         zr=acos(coznt)
L03186  
L03187        return
L03188  
L03189        END SUBROUTINE angle
```

> 讲解：Schayes 1982 太阳角计算（Spencer 型 Fourier 级数赤纬 + 时差方程 + 时角 + 天顶角）。**当前未被调用**（BEP 主入口 L491 的调用被注释——太阳几何改由辐射 driver 的 declin_urb/cosz_urb2d/omg_urb2d 统一提供，避免两套日历口径）。保留单元的价值：理想化/离线试验可用；用时注意 along 单位是度、realt 是 GMT 小时。

<!-- code_extract code_extract.py v1.2
source: phys/module_sf_bep.F
ranges: L3194-L3314
file_lines: 3536
file_md5: 5f74b56a221ca4ec69320a09ad3f9c3e
display: line-numbered (strip L-prefix and !file: line to restore)
range_md5: 10be7e2eb733c68f6a673dd266272929
seg_lines: 121
label: subroutine upward_rad
-->

```fortran
!file: phys/module_sf_bep.F    L3194-L3314    (subroutine upward_rad)
L03194        subroutine upward_rad(ndu,nzu,ws,bs,sigma,pb,ss,                     &
L03195                         tg,emg_u,albg_u,rlg,rsg,sfg,                        & 
L03196                         tw,emw_u,albw_u,rlw,rsw,sfw,                        & 
L03197                         tr,emr_u,albr_u,rld,rs, sfr,                        & 
L03198                         rs_abs,rl_up,emiss,grdflx_urb)
L03199  !
L03200  ! IN this surboutine we compute the upward longwave flux, and the albedo
L03201  ! needed for the radiation scheme
L03202  !
L03203                         implicit none
L03204  
L03205  !
L03206  !INPUT VARIABLES
L03207  !
L03208        real rsw(2*ndm,nz_um)        ! Short wave radiation at the wall for a given canyon direction [W/m2]
L03209        real rlw(2*ndm,nz_um)         ! Long wave radiation at the walls for a given canyon direction [W/m2]
L03210        real rsg(ndm)                   ! Short wave radiation at the canyon for a given canyon direction [W/m2]
L03211        real rlg(ndm)                   ! Long wave radiation at the ground for a given canyon direction [W/m2]
L03212        real rs                        ! Short wave radiation at the horizontal surface from the sun [W/m2]  
L03213        real sfw(2*ndm,nz_um)      ! Sensible heat flux from walls [W/m2]
L03214        real sfg(ndm)              ! Sensible heat flux from ground (road) [W/m2]
L03215        real sfr(ndm,nz_um)      ! Sensible heat flux from roofs [W/m2]                      
L03216        real rld                        ! Long wave radiation from the sky [W/m2]
L03217        real albg_u                    ! albedo of the ground/street
L03218        real albw_u                    ! albedo of the walls
L03219        real albr_u                    ! albedo of the roof 
L03220        real ws(ndm)                        ! width of the street
L03221        real bs(ndm)
L03222                          ! building size
L03223        real pb(nz_um)                ! Probability to have a building with an height equal or higher   
L03224        integer nzu
L03225        real ss(nz_um)                ! Probability to have a building of a given height
L03226        real sigma                       
L03227        real emg_u                       ! emissivity of the street
L03228        real emw_u                       ! emissivity of the wall
L03229        real emr_u                       ! emissivity of the roof
L03230        real tw(2*ndm,nz_um,nwr_u)  ! Temperature in each layer of the wall [K]
L03231        real tr(ndm,nz_um,nwr_u)  ! Temperature in each layer of the roof [K]
L03232        real tg(ndm,ng_u)          ! Temperature in each layer of the ground [K]
L03233        integer id ! street direction
L03234        integer ndu ! number of street directions
L03235  !OUTPUT/INPUT
L03236        real rs_abs  ! absrobed solar radiationfor this street direction
L03237        real rl_up   ! upward longwave radiation for this street direction
L03238        real emiss ! mean emissivity
L03239        real grdflx_urb ! ground heat flux 
L03240  !LOCAL
L03241        integer iz,iw
L03242        real rl_inc,rl_emit
L03243        real gfl
L03244        integer ix,iy,iwrong
L03245  
L03246           iwrong=1
L03247        do iz=1,nzu+1
L03248        do id=1,ndu
L03249        do iw=1,nwr_u
L03250          if(tr(id,iz,iw).lt.100.)then
L03251                write(*,*)'in upward_rad ',iz,id,iw,tr(id,iz,iw) 
L03252                iwrong=0
L03253          endif
L03254          if(tw(2*id-1,iz,iw).lt.100.) then
L03255             write(*,*)'in upward_rad ',iz,id,iw,tw(2*id-1,iz,iw) 
L03256             iwrong=0
L03257          endif
L03258          if(tw(2*id,iz,iw).lt.100.) then
L03259             write(*,*)'in upward_rad ',iz,id,iw,tw(2*id,iz,iw) 
L03260             iwrong=0
L03261          endif
L03262        enddo
L03263        enddo
L03264        enddo
L03265        do id=1,ndu
L03266        do iw=1,ng_u
L03267            if(tg(id,iw).lt.100.) then
L03268              write(*,*)'in upward_rad ',id,iw,tg(id,iw) 
L03269              iwrong=0
L03270            endif
L03271        enddo   
L03272        enddo
L03273             if(iwrong.eq.0)stop
L03274  
L03275        rl_up=0.
L03276   
L03277        rs_abs=0.
L03278        rl_inc=0.
L03279        emiss=0.
L03280        rl_emit=0.
L03281        grdflx_urb=0.
L03282        do id=1,ndu          
L03283         rl_emit=rl_emit-( emg_u*sigma*(tg(id,ng_u)**4.)+(1-emg_u)*rlg(id))*ws(id)/(ws(id)+bs(id))/ndu
L03284         rl_inc=rl_inc+rlg(id)*ws(id)/(ws(id)+bs(id))/ndu       
L03285         rs_abs=rs_abs+(1.-albg_u)*rsg(id)*ws(id)/(ws(id)+bs(id))/ndu
L03286           gfl=(1.-albg_u)*rsg(id)+emg_u*rlg(id)-emg_u*sigma*(tg(id,ng_u)**4.)+sfg(id)
L03287           grdflx_urb=grdflx_urb-gfl*ws(id)/(ws(id)+bs(id))/ndu  
L03288   
L03289            do iz=2,nzu
L03290              rl_emit=rl_emit-(emr_u*sigma*(tr(id,iz,nwr_u)**4.)+(1-emr_u)*rld)*ss(iz)*bs(id)/(ws(id)+bs(id))/ndu
L03291              rl_inc=rl_inc+rld*ss(iz)*bs(id)/(ws(id)+bs(id))/ndu            
L03292              rs_abs=rs_abs+(1.-albr_u)*rs*ss(iz)*bs(id)/(ws(id)+bs(id))/ndu
L03293              gfl=(1.-albr_u)*rs+emr_u*rld-emr_u*sigma*(tr(id,iz,nwr_u)**4.)+sfr(id,iz)
L03294              grdflx_urb=grdflx_urb-gfl*ss(iz)*bs(id)/(ws(id)+bs(id))/ndu
L03295           enddo
L03296             
L03297           do iz=1,nzu            
L03298              rl_emit=rl_emit-(emw_u*sigma*( tw(2*id-1,iz,nwr_u)**4.+tw(2*id,iz,nwr_u)**4. )+          &
L03299                 (1-emw_u)*( rlw(2*id-1,iz)+rlw(2*id,iz) ) )*dz_u*pb(iz+1)/(ws(id)+bs(id))/ndu
L03300              rl_inc=rl_inc+(( rlw(2*id-1,iz)+rlw(2*id,iz) ) )*dz_u*pb(iz+1)/(ws(id)+bs(id))/ndu
L03301              rs_abs=rs_abs+((1.-albw_u)*( rsw(2*id-1,iz)+rsw(2*id,iz) ) )*dz_u*pb(iz+1)/(ws(id)+bs(id))/ndu 
L03302              gfl=(1.-albw_u)*(rsw(2*id-1,iz)+rsw(2*id,iz)) +emw_u*( rlw(2*id-1,iz)+rlw(2*id,iz) )   &
L03303               -emw_u*sigma*( tw(2*id-1,iz,nwr_u)**4.+tw(2*id,iz,nwr_u)**4. )+(sfw(2*id-1,iz)+sfw(2*id,iz))            
L03304              grdflx_urb=grdflx_urb-gfl*dz_u*pb(iz+1)/(ws(id)+bs(id))/ndu
L03305           enddo
L03306            
L03307        enddo
L03308          emiss=(emg_u+emw_u+emr_u)/3.
L03309          rl_up=(rl_inc+rl_emit)-rld
L03310         
L03311           
L03312        return
L03313  
L03314        END SUBROUTINE upward_rad
```

> 与 14b §七差异：无 PV/绿屋顶项；<100 K 哨兵扫全部固体温度（同样 write+stop 硬停，生产建议换 wrf_error_fatal）。

<!-- code_extract code_extract.py v1.2
source: phys/module_sf_bep.F
ranges: L3499-L3535
file_lines: 3536
file_md5: 5f74b56a221ca4ec69320a09ad3f9c3e
display: line-numbered (strip L-prefix and !file: line to restore)
range_md5: acc11cbc67b2175936d334b1ab48799d
seg_lines: 37
-->

```fortran
!file: phys/module_sf_bep.F    L3499-L3535
L03499  ! ===6=8===============================================================72
L03500  END MODULE module_sf_bep
L03501  
L03502        FUNCTION bep_nurbm () RESULT (bep_val_nurbm)
L03503           USE module_sf_bep
L03504           IMPLICIT NONE
L03505           INTEGER :: bep_val_nurbm
L03506           bep_val_nurbm = nurbm
L03507        END FUNCTION bep_nurbm
L03508        
L03509        FUNCTION bep_ndm () RESULT (bep_val_ndm)
L03510           USE module_sf_bep
L03511           IMPLICIT NONE
L03512           INTEGER :: bep_val_ndm
L03513           bep_val_ndm = ndm
L03514        END FUNCTION bep_ndm
L03515        
L03516        FUNCTION bep_nz_um () RESULT (bep_val_nz_um)
L03517           USE module_sf_bep
L03518           IMPLICIT NONE
L03519           INTEGER :: bep_val_nz_um
L03520           bep_val_nz_um = nz_um
L03521        END FUNCTION bep_nz_um
L03522        
L03523        FUNCTION bep_ng_u () RESULT (bep_val_ng_u)
L03524           USE module_sf_bep
L03525           IMPLICIT NONE
L03526           INTEGER :: bep_val_ng_u
L03527           bep_val_ng_u = ng_u
L03528        END FUNCTION bep_ng_u
L03529        
L03530        FUNCTION bep_nwr_u () RESULT (bep_val_nwr_u)
L03531           USE module_sf_bep
L03532           IMPLICIT NONE
L03533           INTEGER :: bep_val_nwr_u
L03534           bep_val_nwr_u = nwr_u
L03535        END FUNCTION bep_nwr_u
```

> 讲解：五个宿主关联查询函数（bep_nurbm/ndm/nz_um/ng_u/nwr_u），机制同 14b §七。

## 七、改造入口

1. **BEP 单开实验**（论文 2 对照组候选）：sf_urban_physics=1 配 BouLac/MYJ；注意它没有室内废热——UHI 模拟偏冷，与 BEP+BEM（=3）对照时可量化 BEM 贡献。
2. **两文件同步红线**：本文件与 bep_bem 的同源单元（param/shadow_mas/shade_wall/long_rad/flux_wall/flux_flat/icBEP 族…）是历史分叉拷贝——改其一必须 grep 另一文件同名子程序决定是否同步；surf_temp/flux_flat 在 module_sf_bem.F 还有一份（16 篇确认）。
3. **拖曳系数**：常数 cdrag=0.4 改成 bep_bem 的 NEW CDRAG 是最小改造（把 BEP1D 加 alp 计算传入 buildings）。
4. **太阳几何**：angle 单元可用于 ideal 案例自算太阳角（替代 radiation driver 依赖）。

## 八、上下游链接

- 共享底座全文：[code_14a_module_sf_bep_bem.md](code_14a_module_sf_bep_bem.md)、[code_14b_module_sf_bep_bem.md](code_14b_module_sf_bep_bem.md)
- 同族：[code_16_module_sf_bem.md](code_16_module_sf_bem.md)（BEM 主体）；module_sf_urban（17 篇待交付）
- 驱动链：[code_22_module_pbl_driver.md](code_22_module_pbl_driver.md)；面层 [code_10_module_sf_mynnsfc.md](code_10_module_sf_mynnsfc.md)
- 教材正文：[ch17_urban_canopy.md](../ch17_urban_canopy.md)、[ch20_modifying_wrf.md](../ch20_modifying_wrf.md)、[ch19_lanzhou_heatwave.md](../ch19_lanzhou_heatwave.md)
