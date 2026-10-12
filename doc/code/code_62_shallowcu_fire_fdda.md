# code_62 — 次级驱动器三件头部（shallowcu_driver + module_fr_fire_driver_wrf.F + fddagd_driver：C 级接口索引）

## 一、版本指纹

| 源文件 | 行数 | md5（整文件，按字节） |
|---|---|---|
| phys/module_shallowcu_driver.F | 767 | 8b7d55b57a824915f5e32a3aa0e1955c |
| phys/module_fr_fire_driver_wrf.F | 149 | 8db0ddd868c46e10e1b02d060a617554 |
| phys/module_fddagd_driver.F | 626 | e068c0b8151240276176f2c08d5eaa96 |

- 抽取工具：workspace/scripts/code_extract.py v1.2，2026-10-12；块首指纹注释自带 range_md5。
- 收录分级（C）：三件头部（模块声明与主入口签名段）+ 单元索引；fire 包装层全文（149 行全收——它本身薄）。教材锚点：[ch15_cumulus_family.md](../ch15_cumulus_family.md)（独立浅对流）、[ch21_solve_em_dynamics.md](../ch21_solve_em_dynamics.md)（调用位置）。

## 二、定位

一句话：part1 总装层里三个**次级驱动器**的接口索引——独立浅对流（shcu_physics，与主积云并行的第二积云通道）、火模式 WRF 包装层（ifire=2 的 fire_driver_em_step 与 rthfrten/rqvfrten 倾向出口）、格点 nudging（fddagd_driver，fdda3d/fdda2d 与 ndg_old/new 双时刻场的消费者）。

**谁在调它们**：first_rk_step_part1（[code_31_module_first_rk_step_part1.md](code_31_module_first_rk_step_part1.md) §九/§十/§十一——调用序在此三段的末三站）。

## 三、独立浅对流 shallowcu_driver

<!-- code_extract code_extract.py v1.2
source: phys/module_shallowcu_driver.F
ranges: L1-L55
file_lines: 767
file_md5: 8b7d55b57a824915f5e32a3aa0e1955c
display: line-numbered (strip L-prefix and !file: line to restore)
range_md5: 601e2a5ea4e13991952026c0e04e9346
seg_lines: 55
-->

```fortran
!file: phys/module_shallowcu_driver.F    L1-L55
L00001  !WRF:MEDIATION_LAYER:PHYSICS
L00002  !
L00003  
L00004  MODULE module_shallowcu_driver
L00005  
L00006    implicit none
L00007  
L00008    real, private, parameter :: QCLOUD_MIN = 0.0
L00009    real, private, parameter :: QVAPOR_MIN = 0.0
L00010  
L00011  CONTAINS
L00012     SUBROUTINE shallowcu_driver(                                       &
L00013                   ! Order dependent args for domain, mem, and tile dims
L00014                        ids,ide, jds,jde, kds,kde                       &
L00015                       ,ims,ime, jms,jme, kms,kme                       &
L00016                       ,ips,ipe, jps,jpe, kps,kpe                       &
L00017                       ,i_start,i_end,j_start,j_end,kts,kte,num_tiles   &
L00018                   ! Order independent args (use VAR= in call)
L00019                   ! --Prognostic
L00020                       ,u,v,th,t                                        &
L00021                       ,p,pi,rho,moist                                  &
L00022                   ! --Other arguments
L00023                       ,num_moist                                       &
L00024                       ,itimestep,dt,dx,dx2d,area2d                     &
L00025                       ,cudt,curr_secs,adapt_step_flag                  &
L00026                       ,rainsh,pratesh,nca,rainshv                      &
L00027                       ,z,z_at_w,dz8w,mavail,pblh,p8w                   &
L00028                       ,tke_pbl                                         &
L00029                       ,cldfra,cldfra_old,cldfra_old_mp,cldfra_conv     &
L00030                       ,cldfrash                                        &
L00031                       ,htop,hbot                                       &
L00032                   ! Package selection variables
L00033                       ,shcu_physics                                    &
L00034                   ! Optional moisture tracers 
L00035                       ,qv_curr, qc_curr, qr_curr                       &
L00036                       ,qi_curr, qs_curr, qg_curr                       & 
L00037                       ,qnc_curr,qni_curr                               &
L00038  #if ( WRF_CHEM == 1 )
L00039                       ,chem, chem_opt                                  &
L00040  #endif
L00041                   ! Optional output arguments for CAMZM scheme
L00042                       ,dlf, rliq, rliq2,dlf2  &
L00043                       ,cmfmc, cmfmc2       &
L00044                   ! Optional output arguments for CAMUW scheme
L00045                       ,cush, snowsh, icwmrsh, rprdsh, cbmf, cmfsl      &
L00046                       ,cmflq, evapcsh                                  &
L00047                   ! Optional moisture and other tendencies
L00048                       ,rqvshten,rqcshten,rqrshten                      &
L00049                       ,rqishten,rqsshten,rqgshten                      &
L00050                       ,rqcnshten,rqinshten                             &
L00051                       ,rqvblten,rqvften                                &
L00052                       ,rushten,rvshten                                 &
L00053                       ,rthshten,rthraten,rthblten,rthften              &
L00054                   ! Optional moisture tracer flags 
L00055                       ,f_qv,f_qc,f_qr                                  &
```

> 讲解：与 cumulus_driver 同族的调度器（682 行单子程序 + SPP 加/减对两件）：①**签名差异即语义差异**——rainsh/pratesh/rainshv（浅对流降水独立账本）、cldfrash（浅对流云量）、htop/hbot 共用积云的云顶底数组；②CAMZM/CAMUW 专属输出（dlf/rliq/cmfmc 与 cush/snowsh/icwmrsh/cbmf/cmfsl/cmflq/evapcsh——CAM 浅对流诊断全家）经 OPTIONAL 传入；③倾向出口 rqvshten/rqcshten/rqrshten/rqishten 系（**浅对流带雨/冰倾向**——比主积云的若干方案更全）；④QCLOUD_MIN/QVAPOR_MIN 模块级钳位。**与主积云的关系**：shcu_physics 与 cu_physics 可同时开（双积云并行的物理风险见 code_23 §九），G3 的内嵌浅对流与这里的独立浅对流是两条线。SPP 对（Add/Remove_multi_perturb_shcu，L695–L765）与 radiation_driver 的同名件同构（code_20 §八）。

## 四、火模式 WRF 包装层 module_fr_fire_driver_wrf.F（全文）

<!-- code_extract code_extract.py v1.2
source: phys/module_fr_fire_driver_wrf.F
ranges: L1-L149
file_lines: 149
file_md5: 8db0ddd868c46e10e1b02d060a617554
display: line-numbered (strip L-prefix and !file: line to restore)
range_md5: 8db0ddd868c46e10e1b02d060a617554
seg_lines: 149
-->

```fortran
!file: phys/module_fr_fire_driver_wrf.F    L1-L149
L00001  ! WRF:MEDIATION_LAYER:FIRE_MODEL
L00002  
L00003  
L00004  #define DEBUG_OUT
L00005  
L00006  module module_fr_fire_driver_wrf
L00007  ! wrf-specific driver
L00008  
L00009  use module_fr_fire_driver
L00010  use module_fr_fire_atm
L00011  implicit none
L00012  
L00013  contains
L00014  
L00015  subroutine fire_driver_em_init (grid , config_flags               & 
L00016              ,ids,ide, kds,kde, jds,jde                              &
L00017              ,ims,ime, kms,kme, jms,jme                              &
L00018              ,ips,ipe, kps,kpe, jps,jpe)
L00019  
L00020      ! stub to call fire_driver_em with irun=0 and omit last 3 args
L00021  
L00022      USE module_domain , only: domain , get_ijk_from_subgrid
L00023      USE module_configure , only : grid_config_rec_type
L00024      implicit none
L00025  
L00026      TYPE(domain) , TARGET          :: grid   ! data
L00027      TYPE (grid_config_rec_type) , INTENT(IN)          :: config_flags
L00028      integer, intent(in):: &
L00029               ids,ide, kds,kde, jds,jde                              &
L00030              ,ims,ime, kms,kme, jms,jme                              &
L00031              ,ips,ipe, kps,kpe, jps,jpe
L00032  
L00033      ! local
L00034      integer :: &  ! fire mesh sizes
L00035               ifds,ifde, kfds,kfde, jfds,jfde,                              &
L00036               ifms,ifme, kfms,kfme, jfms,jfme,                              &
L00037               ifps,ifpe, kfps,kfpe, jfps,jfpe                              
L00038      ! dummies
L00039  
L00040      real,dimension(1,1,1)::rho,z_at_w,dz8w
L00041      
L00042      call message('fire_driver_em_init: FIRE initialization start')
L00043  
L00044      ! get fire mesh dimensions
L00045      CALL get_ijk_from_subgrid (  grid ,                   &
L00046                              ifds,ifde, jfds,jfde,kfds,kfde,                        &
L00047                              ifms,ifme, jfms,jfme,kfms,kfme,                        &
L00048                              ifps,ifpe, jfps,jfpe,kfps,kfpe) 
L00049  
L00050      call fire_driver_em ( grid , config_flags               & 
L00051              ,1,2,0                        & ! ifun start, end, test steps
L00052              ,ids,ide, kds,kde, jds,jde                              &
L00053              ,ims,ime, kms,kme, jms,jme                              &
L00054              ,ips,ipe, kps,kpe, jps,jpe                              &
L00055              ,ifds,ifde, jfds,jfde                                   &
L00056              ,ifms,ifme, jfms,jfme                                   &
L00057              ,ifps,ifpe, jfps,jfpe                                   &
L00058              ) 
L00059  
L00060      call message('fire_driver_em_init: FIRE initialization complete')
L00061  
L00062  end subroutine fire_driver_em_init
L00063  
L00064  !
L00065  !***
L00066  !
L00067  
L00068  subroutine fire_driver_em_step (grid , config_flags               & 
L00069              ,ids,ide, kds,kde, jds,jde                              &
L00070              ,ims,ime, kms,kme, jms,jme                              &
L00071              ,ips,ipe, kps,kpe, jps,jpe                              &
L00072              ,rho,z_at_w,dz8w ) 
L00073  
L00074      ! stub to call fire_driver_em 
L00075  
L00076      USE module_domain, only: domain , get_ijk_from_subgrid
L00077      USE module_configure , only : grid_config_rec_type
L00078      USE module_fr_fire_util, only : fire_test_steps
L00079      implicit none
L00080  
L00081      TYPE(domain) , TARGET          :: grid   ! data
L00082      TYPE (grid_config_rec_type) , INTENT(IN)          :: config_flags
L00083      integer, intent(in):: &
L00084               ids,ide, kds,kde, jds,jde                              &
L00085              ,ims,ime, kms,kme, jms,jme                              &
L00086              ,ips,ipe, kps,kpe, jps,jpe
L00087      real,dimension(ims:ime, kms:kme, jms:jme),intent(in)::rho,z_at_w,dz8w
L00088  
L00089      ! local
L00090      integer :: &  ! fire mesh sizes
L00091               ifds,ifde, kfds,kfde, jfds,jfde,                              &
L00092               ifms,ifme, kfms,kfme, jfms,jfme,                              &
L00093               ifps,ifpe, kfps,kfpe, jfps,jfpe                              
L00094      integer :: its,ite,jts,jte,kts,kte            ! atm tile
L00095      integer:: ij 
L00096  
L00097      call message('fire_driver_em_step: FIRE step start')
L00098  
L00099      ! get fire mesh dimensions
L00100      CALL get_ijk_from_subgrid (  grid ,                   &
L00101                              ifds,ifde, jfds,jfde,kfds,kfde,                        &
L00102                              ifms,ifme, jfms,jfme,kfms,kfme,                        &
L00103                              ifps,ifpe, jfps,jfpe,kfps,kfpe) 
L00104  
L00105      call fire_driver_em ( grid , config_flags               & 
L00106              ,3,6,fire_test_steps                                &
L00107              ,ids,ide, kds,kde, jds,jde                              &
L00108              ,ims,ime, kms,kme, jms,jme                              &
L00109              ,ips,ipe, kps,kpe, jps,jpe                              &
L00110              ,ifds,ifde, jfds,jfde                                   &
L00111              ,ifms,ifme, jfms,jfme                                   &
L00112              ,ifps,ifpe, jfps,jfpe                                   &
L00113              ,rho,z_at_w,dz8w                                        &
L00114              )
L00115   
L00116  
L00117      ! --- add heat and moisture fluxes to tendency variables by postulated decay
L00118      do ij=1,grid%num_tiles
L00119         ! FIRE works on domain by 1 smaller, in last row&col winds are not set properly
L00120         its = grid%i_start(ij)             ! start atmospheric tile in i
L00121         ite = min(grid%i_end(ij),ide-1)    ! end atmospheric tile in i
L00122         jts = grid%j_start(ij)             ! start atmospheric tile in j
L00123         jte = min(grid%j_end(ij),jde-1)    ! end atmospheric tile in j
L00124         kts=kds
L00125         kte=kde
L00126  
L00127         call fire_tendency(                 &
L00128              ids,ide-1, kds,kde, jds,jde-1, & ! domain dimensions
L00129              ims,ime, kms,kme, jms,jme,      &
L00130              its,ite, kts,kte, jts,jte,      & ! 
L00131              grid%grnhfx,grid%grnqfx,grid%canhfx,grid%canqfx,        & ! fluxes on atm grid 
L00132              config_flags%fire_ext_grnd,config_flags%fire_ext_crwn,config_flags%fire_crwn_hgt,                &
L00133              config_flags%fire_sfc_flx,config_flags%fire_heat_peak,config_flags%fire_tg_ub, &
L00134              grid%ht,z_at_w,dz8w,grid%mut,grid%c1h,grid%c2h,rho,          &
L00135              grid%rthfrten,grid%rqvfrten)                ! out
L00136  
L00137       enddo
L00138  
L00139         ! debug print to compare
L00140  
L00141         call print_3d_stats(its,ite,kts,kte,jts,jte,ims,ime,kms,kme,jms,jme,grid%rthfrten,'fire_driver_phys:rthfrten')
L00142         call print_3d_stats(its,ite,kts,kte,jts,jte,ims,ime,kms,kme,jms,jme,grid%rqvfrten,'fire_driver_phys:rqvfrten')
L00143  
L00144      call message('fire_driver_em_step: FIRE step complete')
L00145              
L00146  end subroutine fire_driver_em_step
L00147  
L00148  end module module_fr_fire_driver_wrf
L00149  
```

> 讲解：**只有 149 行的薄包装**——WRF 大气与理想火模式（module_fr_fire_driver，77 KB 实体）之间的全部接口：①fire_driver_em_init：stub 调 fire_driver_em(irun=1,2,0)——**ifun 1/2 是初始化段**（火网格 ifds..ifpe 三层子格索引由 get_ijk_from_subgrid 取——火模式有自己的比大气更细的网格）；②fire_driver_em_step：stub 调 fire_driver_em(**irun=3,6**,fire_test_steps)——3–6 号任务步每步执行，入参只要 rho/z_at_w/dz8w 三个大气场；③段尾 **fire_tendency**：把火面热通量（grnhfx 地表/grnqfx/canhfx 树冠/canqfx）按 fire_ext_grnd/fire_ext_crwn/fire_crwn_hgt/fire_sfc_flx/fire_heat_peak/fire_tg_ub 六个 namelist 参数的「假定衰减廓线」注入 **grid%rthfrten/rqvfrten**——这就是 part2 的 update_phy_ten 实参表里 rthfrten/rqvfrten（注释「fire」）的来源（code_32 §八）；④「FIRE works on domain by 1 smaller」——火网格边界一圈风场不可用的诚实注释。火物理本体（理想火蔓延、Level-Set/CFBM）在 module_fr_fire_driver.F，不在文库范围（ch20 案例库引用）。

## 五、格点 nudging fddagd_driver

<!-- code_extract code_extract.py v1.2
source: phys/module_fddagd_driver.F
ranges: L1-L45
file_lines: 626
file_md5: e068c0b8151240276176f2c08d5eaa96
display: line-numbered (strip L-prefix and !file: line to restore)
range_md5: e6389bd0f2c5e1965e432c15efef01fc
seg_lines: 45
-->

```fortran
!file: phys/module_fddagd_driver.F    L1-L45
L00001  !WRF:MEDIATION_LAYER:PHYSICS
L00002  !
L00003  
L00004  MODULE module_fddagd_driver
L00005  CONTAINS
L00006  
L00007  !------------------------------------------------------------------
L00008     SUBROUTINE fddagd_driver(itimestep,dt,xtime,                   &
L00009                    curr_mins2, id,  &
L00010                    RUNDGDTEN,RVNDGDTEN,RTHNDGDTEN,                 &
L00011                    RPHNDGDTEN,RQVNDGDTEN,RMUNDGDTEN,               &
L00012                    SDA_HFX, SDA_QFX,                               & !fasdas
L00013                    HFX_FDDA,                                       & !fasdas
L00014                    u_ndg_old,v_ndg_old,t_ndg_old,ph_ndg_old,       &
L00015                    q_ndg_old,mu_ndg_old,       &
L00016                    u_ndg_new,v_ndg_new,t_ndg_new,ph_ndg_new,       &
L00017                    q_ndg_new,mu_ndg_new,       &
L00018                    u3d,v3d,th_phy,ph,rho,moist,                    &
L00019                    p_phy,pi_phy,p8w,t_phy,dz8w,z,z_at_w,           &
L00020                    grid,config_flags,DX,n_moist,                   &
L00021                    STEPFG,                                         &
L00022                    pblh,ht,regime,znt,                             &
L00023                    ids,ide, jds,jde, kds,kde,                      &
L00024                    ims,ime, jms,jme, kms,kme,                      &
L00025                    i_start,i_end, j_start,j_end, kts,kte, num_tiles, &
L00026                    u10, v10, th2, q2, &
L00027                    u10_ndg_old, v10_ndg_old, t2_ndg_old, th2_ndg_old, q2_ndg_old,  &
L00028                    rh_ndg_old, psl_ndg_old, ps_ndg_old, tob_ndg_old, odis_ndg_old, &
L00029                    u10_ndg_new, v10_ndg_new, t2_ndg_new, th2_ndg_new, q2_ndg_new,  &
L00030                    rh_ndg_new, psl_ndg_new, ps_ndg_new, tob_ndg_new, odis_ndg_new, &
L00031                    ips,ipe,jps,jpe,kps,kpe,                          &
L00032                    imsx,imex,jmsx,jmex,kmsx,kmex,                    &
L00033                    ipsx,ipex,jpsx,jpex,kpsx,kpex,                    &
L00034                    imsy,imey,jmsy,jmey,kmsy,kmey,                    &
L00035                    ipsy,ipey,jpsy,jpey,kpsy,kpey                     )
L00036  !------------------------------------------------------------------
L00037     USE module_configure
L00038     USE module_state_description
L00039     USE module_model_constants
L00040     USE module_domain, ONLY : domain
L00041  
L00042  ! *** add new modules of schemes here
L00043  
L00044     USE module_fdda_psufddagd
L00045     USE module_fdda_spnudging
```

> 讲解：单子程序 618 行的 nudging 总装：①**双时刻场对**（u_ndg_old/new 五组 3D + u10_ndg_old/new 等十组 2D）——nudging 的分析场以 old/new 两时刻输入、时间线性插值到当前 xtime（fdda 前处理生成， Registry 态）；②**倾向出口六件** RUNDGDTEN/RVNDGDTEN/RTHNDGDTEN/RPHNDGDTEN/RQVNDGDTEN/RMUNDGDTEN（mu 的 nudging 倾向都有）——经 calculate_phy_tend/update_phy_ten 进总账（code_32 §五/§八）；③SDA_HFX/SDA_QFX/HFX_FDDA（fasdas 同化与 nudging 的感热交互）；④STEPFG（nudging 自身的时间门控步长，与 grid_fdda 系 namelist 配套）；⑤wind/temp/moist/geo-p/sfc 五通道各自的开关与系数在 config_flags（grid_fdda/i/e 系）——内部按通道分派的散代码未录。

## 六、改造入口

1. **双积云叠加风险**：shcu+cu 同时开的对照实验（浅对流云量 cldfrash 是否与 cldfra_dp/sh 双计）。
2. **火-大气耦合强度**：fire_sfc_flx/fire_heat_peak 六参数与 rthfrten 注入廓线（fire_tendency 内）——火灾天气实验的强度旋钮。
3. **nudging 通道**：五通道开关/系数/时间窗——再分析拉回实验（ch19 的 ERA5 对照可扩展为 nudging 版）。

## 七、上下游链接

- 调用层：[code_31_module_first_rk_step_part1.md](code_31_module_first_rk_step_part1.md)；记账：[code_32_module_first_rk_step_part2.md](code_32_module_first_rk_step_part2.md)
- 同族：[code_23_module_cumulus_driver.md](code_23_module_cumulus_driver.md)（主积云对照）
- 教材正文：[ch15_cumulus_family.md](../ch15_cumulus_family.md)、[ch21_solve_em_dynamics.md](../ch21_solve_em_dynamics.md)
