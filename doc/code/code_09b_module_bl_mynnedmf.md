# 文库 code_09b：module_bl_mynnedmf.F90 下半——倾向驱动、质量通量与辅助函数族

<!-- 本文件为骨架：CODE 占位符由 workspace/scripts/code_extract.py 注入保真块。
     组装命令：
     D:\Code\miniforge3\envs\WRFlearn\python.exe workspace\scripts\code_extract.py assemble source\WRFv4.8.0\WRFV4.8.0\phys\MYNN-EDMF\module_bl_mynnedmf.F90 workspace\code_library\skel_code_09b.md doc\code\code_09b_module_bl_mynnedmf.md -->

## 09b.0 版本指纹与阅读说明

- **源文件**：`phys/MYNN-EDMF/module_bl_mynnedmf.F90`（WRF 4.8.0），本篇覆盖 L3923–L8776——`mynn_tendencies` 倾向驱动（1574 行）、负值修复、化学/标量混合、三对角求解器族、`GET_PBLH`、上升流谱积分 `DMP_mf`（1345 行）、下沉流 `ddmp_mf`（546 行）、灰区函数 `SCALE_AWARE`、饱和混合函数族、新相似函数 `phim/phih`、云顶辐射冷却解析源 `topdown_cloudrad`。模块声明与闭合主体见 code_09a。
- **保真承诺**：同 code_09a（v1.1 行号显示层，剥离后与源逐位一致）。
- **教材锚点**：ch14（MYNN-EDMF 精读、dmp/ddmp_mf、get_pblh 全文、BouLac 亲缘）、ch21（倾向回写主环）。

## 09b.1 `mynn_tendencies`：九变量倾向的三对角装配

 主入口（code_09a §09a.4.8）把扩散系数（dfm/dfh）、逆梯度项（tcd/qcd）、质量通量通量（s_aw*/sd_aw*）与环境修正（sub_*/det_*）备齐后，`mynn_tendencies` 逐变量解三对角方程——**每个变量一段完全同构的 a/b/c/d 装配**，读完 u 的方程其余就是复制。分段走读：

<!-- code_extract code_extract.py v1.1
source: phys/MYNN-EDMF/module_bl_mynnedmf.F90
ranges: L3923-L4190
file_lines: 8776
file_md5: ec93fee9745a3e0b25be55a61b5aff8a
display: line-numbered (strip L-prefix and !file: line to restore)
range_md5: 1bee4d87ee88384ce155a525e17c737e
seg_lines: 268
-->

```fortran
!file: phys/MYNN-EDMF/module_bl_mynnedmf.F90    L3923-L4190
L03923    SUBROUTINE mynn_tendencies(kts,kte,i,       &
L03924         &delt,dz,zw,xland,pblh,rho,            &
L03925         &u,v,th,tk,qv,qc,qi,qs,qnc,qni,        &
L03926         &psfc,p,exner,                         &
L03927         &thl,sqv,sqc,sqi,sqs,sqw,              &
L03928         &thl_tot1,qc_tot1,qi_tot1,             &
L03929         &qnwfa,qnifa,qnbca,ozone,              &
L03930         &ust,flt,flq,flqv,flqc,wspd,           &
L03931         &uoce,voce,                            &
L03932         &tsq,qsq,cov,                          &
L03933         &tcd,qcd,                              &
L03934         &dfm,dfh,dfq,                          &
L03935         &Du,Dv,Dth,Dqv,Dqc,Dqi,Dqs,Dqnc,Dqni,  &
L03936         &Dqnwfa,Dqnifa,Dqnbca,Dozone,          &
L03937         &diss_heat,                            &
L03938         &s_aw1,s_awthl1,                       &
L03939         &s_awqt1,s_awqv1,s_awqc1,              &
L03940         &s_awu1,s_awv1,                        &
L03941         &s_awqnc1,s_awqni1,                    &
L03942         &s_awqnwfa1,s_awqnifa1,s_awqnbca1,     &
L03943         &sd_aw1,sd_awthl1,sd_awqt1,sd_awqv1,   &
L03944         &sd_awqc1,sd_awqi1,                    &
L03945         &sd_awqnc1,sd_awqni1,                  &
L03946         &sd_awqnwfa1,sd_awqnifa1,              &
L03947         &sd_awu1,sd_awv1,                      &
L03948         &sub_thl,sub_sqv,                      &
L03949         &sub_u,sub_v,                          &
L03950         &det_thl,det_sqv,det_sqc,              &
L03951         &det_u,det_v,                          &
L03952         &FLAG_QC,FLAG_QI,FLAG_QNC,FLAG_QNI,    &
L03953         &FLAG_QS,                              &
L03954         &FLAG_QNWFA,FLAG_QNIFA,FLAG_QNBCA,     &
L03955         &FLAG_OZONE,                           &
L03956         &cldfra_bl1,                           &
L03957         &bl_mynn_cloudmix,                     &
L03958         &bl_mynn_mixqt,                        &
L03959         &bl_mynn_edmf,                         &
L03960         &bl_mynn_edmf_mom,                     &
L03961         &bl_mynn_mixscalars,                   &
L03962         &bl_mynn_mixaerosols,                  &
L03963         &bl_mynn_mixnumcon,                    &
L03964         &upwind                                )
L03965  
L03966  !-------------------------------------------------------------------
L03967      use module_bl_mynnedmf_common, only: r_d,p608,grav,xlvcp,xlscp,       &
L03968           wfa_max,wfa_min,ifa_max,ifa_min,wfa_ht,ifa_ht,zero,one,          &
L03969           p333,p5,kind_phys
L03970      
L03971      integer, intent(in) :: kts,kte,i
L03972  
L03973  #ifdef HARDCODE_VERTICAL
L03974  # define kts 1
L03975  # define kte HARDCODE_VERTICAL
L03976  #endif
L03977  
L03978      integer, intent(in) :: bl_mynn_cloudmix,bl_mynn_mixqt,                &
L03979                             bl_mynn_edmf,bl_mynn_edmf_mom,                 &
L03980                             bl_mynn_mixscalars,bl_mynn_mixaerosols,        &
L03981                             bl_mynn_mixnumcon
L03982      logical, intent(in) :: FLAG_QI,FLAG_QNI,FLAG_QC,FLAG_QS,              &
L03983           &FLAG_QNC,FLAG_QNWFA,FLAG_QNIFA,FLAG_QNBCA,FLAG_OZONE
L03984  
L03985  ! thl - liquid water potential temperature
L03986  ! qw - total water
L03987  ! dfm,dfh,dfq - diffusivities i.e., dfh(k) = elq*sh(k) / dzk
L03988  ! flt - surface flux of thl
L03989  ! flq - surface flux of qw
L03990  
L03991  ! mass-flux plumes
L03992      real(kind_phys), dimension(kts:kte+1), intent(in) :: s_aw1,            &
L03993           &s_awthl1,s_awqt1,s_awqnc1,s_awqni1,s_awqv1,s_awqc1,s_awu1,s_awv1,&
L03994           &s_awqnwfa1,s_awqnifa1,s_awqnbca1,                                &
L03995           &sd_aw1,sd_awthl1,sd_awqt1,sd_awqv1,sd_awqc1,sd_awqi1,            &
L03996           &sd_awqnc1,sd_awqni1,sd_awqnwfa1,sd_awqnifa1,sd_awu1,sd_awv1
L03997  ! tendencies from mass-flux environmental subsidence and detrainment
L03998      real(kind_phys), dimension(kts:kte), intent(in) :: sub_thl,sub_sqv,   &
L03999           &sub_u,sub_v,det_thl,det_sqv,det_sqc,det_u,det_v
L04000      real(kind_phys), dimension(kts:kte), intent(in) :: u,v,th,tk,qv,qc,qi,&
L04001           &qs,qni,qnc,rho,p,exner,dfq,dz,zw,tsq,qsq,cov,tcd,qcd,           &
L04002           &cldfra_bl1,diss_heat,thl_tot1,qc_tot1,qi_tot1
L04003      real(kind_phys), dimension(kts:kte), intent(inout) :: thl,sqw,sqv,sqc,&
L04004           &sqi,sqs,qnwfa,qnifa,qnbca,ozone,dfm,dfh
L04005      real(kind_phys), dimension(kts:kte), intent(inout) :: du,dv,dth,dqv,  &
L04006           &dqc,dqi,dqs,dqni,dqnc,dqnwfa,dqnifa,dqnbca,dozone
L04007      real(kind_phys), intent(in) :: flt,flq,flqv,flqc,uoce,voce
L04008      real(kind_phys), intent(in) :: ust,delt,psfc,wspd,xland,pblh,upwind
L04009      !debugging
L04010      real(kind_phys):: wsp,wsp2,tk2,th2
L04011      logical :: problem
L04012      integer :: kproblem
L04013  
L04014  !    real(kind_phys), intent(in) :: gradu_top,gradv_top,gradth_top,gradqv_top
L04015  
L04016  !local vars
L04017  
L04018      real(kind_phys), dimension(kts:kte) :: dtz,dfhc,dfmc,delp
L04019      real(kind_phys), dimension(kts:kte) :: sqv2,sqc2,sqi2,sqs2,sqw2,      &
L04020            &qni2,qnc2,qnwfa2,qnifa2,qnbca2,ozone2
L04021      real(kind_phys), dimension(kts:kte) :: zfac,plumeKh,rhoinv
L04022      real(kind_phys), dimension(kts:kte) :: upcont,dncont ! updraft/downdraft contribution to fluxes for explicit calculation
L04023      real(kind_phys), dimension(kts:kte) :: a,b,c,d,x
L04024      real(kind_phys), dimension(kts:kte+1) :: rhoz,                        & !rho on model interface
L04025            &khdz,kmdz
L04026      real(kind_phys):: rhs,gfluxm,gfluxp,dztop,maxdfh,mindfh,maxcf,maxKh
L04027      real(kind_phys):: t,esat,qsl,onoff,kh,km,dzk,rhosfc,ustovwsp
L04028      real(kind_phys):: qvflux,aero_min,aero_max
L04029      real(kind_phys):: th_new,portion_qc,portion_qi,condensate,qsat
L04030      integer :: k,kk
L04031  
L04032      !Activate nonlocal mixing from the mass-flux scheme for
L04033      !number concentrations and aerosols (0.0 = no; 1.0 = yes)
L04034      real(kind_phys), parameter :: nonloc  = 1.0
L04035      real(kind_phys), parameter :: nc_min  = 100.0
L04036      real(kind_phys), parameter :: ni_min  = 1e-6
L04037      real(kind_phys) :: wfa_max2, wt
L04038  
L04039      dztop=p5*(dz(kte)+dz(kte-1))
L04040  
L04041      ! REGULATE THE MOMENTUM MIXING FROM THE MASS-FLUX SCHEME (on or off)
L04042      ! Note that s_awu and s_awv already come in as 0.0 if bl_mynn_edmf_mom == 0, so
L04043      ! we only need to zero-out the MF term
L04044      IF (bl_mynn_edmf_mom == 0) THEN
L04045         onoff=zero
L04046      ELSE
L04047         onoff=one
L04048      ENDIF
L04049  
L04050      ! USTAR/WSPD make sure it does not blow up when WSPD = 0.
L04051      IF (wspd .le. 1e-6) THEN
L04052         ustovwsp=zero
L04053      ELSE 
L04054         ustovwsp=ust/wspd
L04055      ENDIF
L04056      
L04057      !Prepare "constants" for diffusion equation.
L04058      !khdz = rho*Kh/dz = rho*dfh
L04059      rhosfc     = psfc/(R_d*(tk(kts)+p608*qv(kts)))
L04060      dtz(kts)   = delt/dz(kts)
L04061      rhoz(kts)  = rho(kts)
L04062      rhoinv(kts)= one/rho(kts)
L04063      khdz(kts)  = rhoz(kts)*dfh(kts)
L04064      kmdz(kts)  = rhoz(kts)*dfm(kts)
L04065      DO k=kts+1,kte
L04066         dtz(k)   = delt/dz(k)
L04067         rhoz(k)  = (rho(k)*dz(k-1) + rho(k-1)*dz(k))/(dz(k-1)+dz(k))
L04068         rhoz(k)  =  MAX(rhoz(k),1E-4_kind_phys)
L04069         rhoinv(k)= one/MAX(rho(k),1E-4_kind_phys)
L04070         dzk      = p5 *( dz(k)+dz(k-1) )
L04071         khdz(k)  = rhoz(k)*dfh(k)
L04072         kmdz(k)  = rhoz(k)*dfm(k)
L04073      ENDDO
L04074      rhoz(kte+1)= rhoz(kte)
L04075      khdz(kte+1)= rhoz(kte+1)*dfh(kte)
L04076      kmdz(kte+1)= rhoz(kte+1)*dfm(kte)
L04077  
L04078      !delta-p for the moisture check
L04079      !delp(kts)  = psfc - (p(kts+1)*dz(kts) + p(kts)*dz(kts+1))/(dz(kts)+dz(kts+1))
L04080      DO k=kts,kte !kts+1,kte-1
L04081         !delp(k)  = (p(k)*dz(k-1) + p(k-1)*dz(k))/(dz(k)+dz(k-1)) - &
L04082         !           (p(k+1)*dz(k) + p(k)*dz(k+1))/(dz(k)+dz(k+1))
L04083         delp(k) = rho(k)*grav*dz(k)
L04084      ENDDO
L04085      !delp(kte)  =delp(kte-1)
L04086      if ( delp(kts) < p333*delp(kts+1) )delp(kts)=p333*delp(kts+1)
L04087  
L04088      !stability criteria for implicit mf
L04089      if (bl_mynn_edmf == 1) then
L04090         DO k=kts+1,kte-1
L04091            khdz(k) = max(khdz(k),  p5*(s_aw1(k) +sd_aw1(k)))
L04092            khdz(k) = max(khdz(k), -p5*(s_aw1(k) -s_aw1(k+1))  &
L04093                                   -p5*(sd_aw1(k)-sd_aw1(k+1)) )
L04094            kmdz(k) = max(kmdz(k),  p5*(s_aw1(k) +sd_aw1(k)))
L04095            kmdz(k) = max(kmdz(k), -p5*(s_aw1(k) -s_aw1(k+1))  &
L04096                                   -p5*(sd_aw1(k)-sd_aw1(k+1)) )
L04097         ENDDO
L04098      endif
L04099  
L04100      dth(kts:kte) = zero  ! must initialize for moisture_check routine
L04101  
L04102  !!============================================
L04103  !! u
L04104  !!============================================
L04105   if (bl_mynn_edmf > 1) then
L04106  
L04107      do k=kts+1,kte-1
L04108         upcont(k)=onoff*(s_awu1(k) - s_aw1(k)*(u(k)*upwind+u(k-1)*(one-upwind)))
L04109         dncont(k)=onoff*(sd_awu1(k)-sd_aw1(k)*(u(k)*upwind+u(k-1)*(one-upwind)))
L04110      enddo
L04111      ! no flux at the top of the atmosphere
L04112      upcont(kte)=zero
L04113      dncont(kte)=zero
L04114      ! upcont(1) and dncont(1) are not used so they don't need to be set
L04115  
L04116      k=kts
L04117      a(1)=zero
L04118      b(1)=one + dtz(k)*(kmdz(k+1)+rhosfc*ust*ustovwsp)*rhoinv(k) 
L04119      c(1)=    - dtz(k)*kmdz(k+1)*rhoinv(k)
L04120      d(1)=u(k)+ dtz(k)*uoce*ust**2/wspd*rho(k)                      &
L04121               - dtz(k)*(upcont(k+1)+dncont(k+1))
L04122  
L04123      DO k=kts+1,kte-1
L04124         a(k)=   - dtz(k)*kmdz(k)*rhoinv(k)
L04125         b(k)=one+ dtz(k)*(kmdz(k)+kmdz(k+1))*rhoinv(k) 
L04126         c(k)=   - dtz(k)*kmdz(k+1)*rhoinv(k)
L04127         d(k)=u(k) -dtz(k)*(upcont(k+1)-upcont(k)+dncont(k+1)-dncont(k)) &
L04128             &  + sub_u(k)*delt + det_u(k)*delt
L04129      ENDDO
L04130  
L04131   else !implicit
L04132      
L04133      k=kts
L04134      !rho-weighted (drag in b-vector):
L04135      a(k)=  -dtz(k)*kmdz(k)*rhoinv(k)
L04136      b(k)=one+dtz(k)*(kmdz(k+1)+rhosfc*ust*ustovwsp)*rhoinv(k)      &
L04137             & - p5*dtz(k)*rhoinv(k)*s_aw1(k+1)*onoff                &
L04138             & - p5*dtz(k)*rhoinv(k)*sd_aw1(k+1)*onoff
L04139      c(k)=  -dtz(k)*kmdz(k+1)*rhoinv(k)                             &
L04140             & - p5*dtz(k)*rhoinv(k)*s_aw1(k+1)*onoff                &
L04141             & - p5*dtz(k)*rhoinv(k)*sd_aw1(k+1)*onoff
L04142      d(k)=u(k)  + dtz(k)*uoce*ust**2/wspd                           &
L04143             & - dtz(k)*rhoinv(k)*s_awu1(k+1)*onoff                  &
L04144             & + dtz(k)*rhoinv(k)*sd_awu1(k+1)*onoff                 &
L04145             & + sub_u(k)*delt + det_u(k)*delt
L04146  
L04147      do k=kts+1,kte-1
L04148         a(k)=  -dtz(k)*kmdz(k)*rhoinv(k)                            &
L04149             &  + p5*dtz(k)*rhoinv(k)*s_aw1(k)*onoff                 &
L04150             &  + p5*dtz(k)*rhoinv(k)*sd_aw1(k)*onoff
L04151         b(k)=one+ dtz(k)*(kmdz(k)+kmdz(k+1))*rhoinv(k)              &
L04152             &  + p5*dtz(k)*rhoinv(k)*(s_aw1(k)-s_aw1(k+1))*onoff    &
L04153             &  + p5*dtz(k)*rhoinv(k)*(sd_aw1(k)-sd_aw1(k+1))*onoff
L04154         c(k)=  - dtz(k)*kmdz(k+1)*rhoinv(k)                         &
L04155             &  - p5*dtz(k)*rhoinv(k)*s_aw1(k+1)*onoff               &
L04156             &  - p5*dtz(k)*rhoinv(k)*sd_aw1(k+1)*onoff
L04157         d(k)=u(k) + dtz(k)*rhoinv(k)*(s_awu1(k)-s_awu1(k+1))*onoff  &
L04158             &  - dtz(k)*rhoinv(k)*(sd_awu1(k)-sd_awu1(k+1))*onoff   &
L04159             &  + sub_u(k)*delt + det_u(k)*delt
L04160      enddo
L04161  
L04162   endif
L04163   
L04164  !! no flux at the top
L04165  !    a(kte)=-1.
L04166  !    b(kte)=1.
L04167  !    c(kte)=0.
L04168  !    d(kte)=0.
L04169  
L04170  !! specified gradient at the top 
L04171  !    a(kte)=-1.
L04172  !    b(kte)=1.
L04173  !    c(kte)=0.
L04174  !    d(kte)=gradu_top*dztop
L04175  
L04176  !! prescribed value
L04177      a(kte)=zero
L04178      b(kte)=one
L04179      c(kte)=zero
L04180      d(kte)=u(kte)
L04181  
L04182  !    CALL tridiag(kte,a,b,c,d)
L04183      CALL tridiag2(kte,a,b,c,d,x)
L04184  !    CALL tridiag3(kte,a,b,c,d,x)
L04185  
L04186      DO k=kts,kte
L04187  !       du(k)=(d(k-kts+1)-u(k))/delt
L04188         du(k)=(x(k)-u(k))/delt
L04189      ENDDO
L04190  
```

> - **准备段**：`khdz/kmdz = ρ·K/dz` 界面通量系数（与 `mym_predict` 同构）；`delp = ρ·g·dz`（层气压厚度，负值修复用）；底层 `delp(kts) < (1/3)·delp(kts+1)` 时抬高——**表层过薄时限制修复强度**。
> - **u 方程的两种耦合**（`bl_mynn_edmf`）：
>   - **显式 MF**（>1）：MF 输运进右端 `upcont/dncont = s_awu − s_aw·(u 上风插值)`；
>   - **隐式 MF**（=1）：MF 进左端 a/b/c（`±0.5·dtz·s_aw`）与右端（`(s_awu(k)−s_awu(k+1))`）——**与 TKE 方程同一数学形态**。
> - **表面边界**：`b(kts)` 含 `rhosfc·u*²/wspd`——**摩擦拖曳直接进对角元**（bulk 公式的隐式化）；右端 `uoce·u*²/wspd` 是**洋流修正的海面应力**（海流不抵消风应力）。`sub_u/det_u·delt` 是环境下沉/夹带倾向。
> - **顶边界**：prescribed value（`d(kte)=u(kte)`——不混合顶层）；被注释的 no-flux/指定梯度两种历史方案。
> - **`onoff = bl_mynn_edmf_mom`**：MF 动量输运总开关（L4041 注释：s_awu 已在 DMP_mf 里按开关清零，这里只是双保险）。
> - 解出 `x(k)` 后 `du = (x−u)/delt`——**WRF 的物理层只交倾向，不交新状态**。

<!-- code_extract code_extract.py v1.1
source: phys/MYNN-EDMF/module_bl_mynnedmf.F90
ranges: L4191-L4462
file_lines: 8776
file_md5: ec93fee9745a3e0b25be55a61b5aff8a
display: line-numbered (strip L-prefix and !file: line to restore)
range_md5: 13fa87ebb3f96a71b0f52f26223478fc
seg_lines: 272
-->

```fortran
!file: phys/MYNN-EDMF/module_bl_mynnedmf.F90    L4191-L4462
L04191  !!============================================
L04192  !! v
L04193  !!============================================
L04194  
L04195   if (bl_mynn_edmf > 1) then
L04196  
L04197      DO k=kts+1,kte-1
L04198         upcont(k)=onoff*(s_awv1(k)-s_aw1(k)*(v(k)*upwind+v(k-1)*(one-upwind)))
L04199         dncont(k)=onoff*(sd_awv1(k)-sd_aw1(k)*(v(k)*upwind+v(k-1)*(one-upwind)))
L04200      ENDDO
L04201      ! no flux at the top of the atmosphere
L04202      upcont(kte)=0.
L04203      dncont(kte)=0.
L04204      ! upcont(1) and dncont(1) are not used so they don't need to be set
L04205  
L04206      k=kts
L04207      a(1)=zero
L04208      b(1)=one + dtz(k)*(kmdz(k+1)+rhosfc*ust*ustovwsp)*rhoinv(k)
L04209      c(1)=    - dtz(k)*kmdz(k+1)*rhoinv(k)
L04210      d(1)=v(k)+ dtz(k)*voce*ust**2/wspd*rho(k)                      &
L04211               - dtz(k)*(upcont(k+1)+dncont(k+1))
L04212  
L04213      DO k=kts+1,kte-1
L04214         a(k)=   - dtz(k)*kmdz(k)*rhoinv(k)
L04215         b(k)=one+ dtz(k)*(kmdz(k)+kmdz(k+1))*rhoinv(k)
L04216         c(k)=   - dtz(k)*kmdz(k+1)*rhoinv(k)
L04217         d(k)=v(k) -dtz(k)*(upcont(k+1)-upcont(k)+dncont(k+1)-dncont(k)) &
L04218             &  + sub_v(k)*delt + det_v(k)*delt
L04219      ENDDO
L04220  
L04221   else !implicit
L04222  
L04223      k=kts
L04224      !rho-weighted (drag in b-vector):
L04225      a(k)=  -dtz(k)*kmdz(k)*rhoinv(k)
L04226      b(k)=one+dtz(k)*(kmdz(k+1) + rhosfc*ust**2/wspd)*rhoinv(k)    &
L04227          &  - p5*dtz(k)*rhoinv(k)*s_aw1(k+1)*onoff                 &
L04228          &  - p5*dtz(k)*rhoinv(k)*sd_aw1(k+1)*onoff
L04229      c(k)=  -dtz(k)*kmdz(k+1)*rhoinv(k)                            &
L04230          &  - p5*dtz(k)*rhoinv(k)*s_aw1(k+1)*onoff                 &
L04231          &  - p5*dtz(k)*rhoinv(k)*sd_aw1(k+1)*onoff
L04232      d(k)=v(k)  + dtz(k)*voce*ust**2/wspd                          &
L04233          &  - dtz(k)*rhoinv(k)*s_awv1(k+1)*onoff                   &
L04234          &  + dtz(k)*rhoinv(k)*sd_awv1(k+1)*onoff                  &
L04235          &  + sub_v(k)*delt + det_v(k)*delt
L04236  
L04237      do k=kts+1,kte-1
L04238         a(k)=  -dtz(k)*kmdz(k)*rhoinv(k)                           &
L04239           & + p5*dtz(k)*rhoinv(k)*s_aw1(k)*onoff                   &
L04240           & + p5*dtz(k)*rhoinv(k)*sd_aw1(k)*onoff
L04241         b(k)=one+dtz(k)*(kmdz(k)+kmdz(k+1))*rhoinv(k)              &
L04242           & + p5*dtz(k)*rhoinv(k)*(s_aw1(k)-s_aw1(k+1))*onoff      &
L04243           & + p5*dtz(k)*rhoinv(k)*(sd_aw1(k)-sd_aw1(k+1))*onoff
L04244         c(k)=  -dtz(k)*kmdz(k+1)*rhoinv(k)                         &
L04245           & - p5*dtz(k)*rhoinv(k)*s_aw1(k+1)*onoff                 &
L04246           & - p5*dtz(k)*rhoinv(k)*sd_aw1(k+1)*onoff
L04247         d(k)=v(k) + dtz(k)*rhoinv(k)*(s_awv1(k)-s_awv1(k+1))*onoff &
L04248           & - dtz(k)*rhoinv(k)*(sd_awv1(k)-sd_awv1(k+1))*onoff     &
L04249           & + sub_v(k)*delt + det_v(k)*delt
L04250      enddo
L04251   endif
L04252  !! no flux at the top
L04253  !    a(kte)=-1.
L04254  !    b(kte)=one
L04255  !    c(kte)=zero
L04256  !    d(kte)=zero
L04257  
L04258  !! specified gradient at the top
L04259  !    a(kte)=-1.
L04260  !    b(kte)=one
L04261  !    c(kte)=zero
L04262  !    d(kte)=gradv_top*dztop
L04263  
L04264  !! prescribed value
L04265      a(kte)=zero
L04266      b(kte)=one
L04267      c(kte)=zero
L04268      d(kte)=v(kte)
L04269  
L04270  !    CALL tridiag(kte,a,b,c,d)
L04271      CALL tridiag2(kte,a,b,c,d,x)
L04272  !    CALL tridiag3(kte,a,b,c,d,x)
L04273  
L04274      DO k=kts,kte
L04275  !       dv(k)=(d(k-kts+1)-v(k))/delt
L04276         dv(k)=(x(k)-v(k))/delt
L04277      ENDDO
L04278  
L04279  !!============================================
L04280  !! thl tendency
L04281  !!============================================
L04282   if (bl_mynn_edmf > 1) then
L04283  
L04284      DO k=kts+1,kte-1
L04285         upcont(k)= s_awthl1(k)- s_aw1(k)*(thl(k)*upwind+thl(k-1)*(one-upwind))
L04286         dncont(k)=sd_awthl1(k)-sd_aw1(k)*(thl(k)*upwind+thl(k-1)*(one-upwind))
L04287      ENDDO
L04288      ! no flux at the top of the atmosphere
L04289      upcont(kte)=zero
L04290      dncont(kte)=zero
L04291      ! upcont(1) and dncont(1) are not used so they don't need to be set
L04292  
L04293      k=kts
L04294      a(1)=zero
L04295      b(1)=one + dtz(k)*khdz(k+1)*rhoinv(k)
L04296      c(1)=    - dtz(k)*khdz(k+1)*rhoinv(k)
L04297      d(1)=thl(k)+dtz(k)*rhosfc*flt*rhoinv(k) + tcd(k)*delt              &
L04298           - dtz(k)*(upcont(k+1)+dncont(k+1))                            &
L04299           + diss_heat(k)*delt + sub_thl(k)*delt + det_thl(k)*delt
L04300  
L04301      DO k=kts+1,kte-1
L04302         a(k)=   - dtz(k)*khdz(k)*rhoinv(k)
L04303         b(k)=one+ dtz(k)*(khdz(k)+khdz(k+1))*rhoinv(k)
L04304         c(k)=   - dtz(k)*khdz(k+1)*rhoinv(k)
L04305         d(k)=thl(k)-dtz(k)*(upcont(k+1)-upcont(k)+dncont(k+1)-dncont(k)) &
L04306             &  + diss_heat(k)*delt + sub_thl(k)*delt + det_thl(k)*delt
L04307      ENDDO
L04308  
L04309   else !implicit
L04310      
L04311      k=kts
L04312  !rho-weighted: rhosfc*x*rhoinv(k)
L04313      a(k)=  -dtz(k)*khdz(k)*rhoinv(k)
L04314      b(k)=1.+dtz(k)*(khdz(k+1)+khdz(k))*rhoinv(k)             &
L04315         &   - p5*dtz(k)*rhoinv(k)*s_aw1(k+1)                  &
L04316         &   - p5*dtz(k)*rhoinv(k)*sd_aw1(k+1)
L04317      c(k)=  -dtz(k)*khdz(k+1)*rhoinv(k)                       &
L04318         &   - p5*dtz(k)*rhoinv(k)*s_aw1(k+1)                  &
L04319         &   - p5*dtz(k)*rhoinv(k)*sd_aw1(k+1)
L04320      d(k)=thl(k) + dtz(k)*rhosfc*flt*rhoinv(k) + tcd(k)*delt  &
L04321  !    d(k)=thl_tot1(k) + dtz(k)*rhosfc*flt*rhoinv(k) + tcd(k)*delt  &
L04322         &   - dtz(k)*rhoinv(k)*s_awthl1(k+1)                  &
L04323         &   + dtz(k)*rhoinv(k)*sd_awthl1(k+1)                 &
L04324         &   + diss_heat(k)*delt + sub_thl(k)*delt + det_thl(k)*delt
L04325  
L04326      do k=kts+1,kte-1
L04327         a(k)= -dtz(k)*khdz(k)*rhoinv(k)                       &
L04328         &   + p5*dtz(k)*rhoinv(k)*s_aw1(k)                    &
L04329         &   + p5*dtz(k)*rhoinv(k)*sd_aw1(k)
L04330         b(k)=1.+dtz(k)*(khdz(k)+khdz(k+1))*rhoinv(k)          &
L04331         &   + p5*dtz(k)*rhoinv(k)*(s_aw1(k)-s_aw1(k+1))       &
L04332         &   + p5*dtz(k)*rhoinv(k)*(sd_aw1(k)-sd_aw1(k+1))
L04333         c(k)= -dtz(k)*khdz(k+1)*rhoinv(k)                     &
L04334         &   - p5*dtz(k)*rhoinv(k)*s_aw1(k+1)                  &
L04335         &   - p5*dtz(k)*rhoinv(k)*sd_aw1(k+1)
L04336         d(k)=thl(k) + tcd(k)*delt                             &
L04337  !       d(k)=thl_tot1(k) + tcd(k)*delt                             &
L04338         &   + dtz(k)*rhoinv(k)*(s_awthl1(k)-s_awthl1(k+1))    &
L04339         &   - dtz(k)*rhoinv(k)*(sd_awthl1(k)-sd_awthl1(k+1))  &
L04340         &   +     diss_heat(k)*delt                           &
L04341         &   +     sub_thl(k)*delt + det_thl(k)*delt
L04342      enddo
L04343   endif
L04344  !! no flux at the top
L04345  !    a(kte)=-1.
L04346  !    b(kte)=1.
L04347  !    c(kte)=0.
L04348  !    d(kte)=0.
L04349  
L04350  !! specified gradient at the top
L04351  !assume gradthl_top=gradth_top
L04352  !    a(kte)=-1.
L04353  !    b(kte)=1.
L04354  !    c(kte)=0.
L04355  !    d(kte)=gradth_top*dztop
L04356  
L04357  !! prescribed value
L04358      a(kte)=zero
L04359      b(kte)=one
L04360      c(kte)=zero
L04361      d(kte)=thl(kte)
L04362  
L04363  !    CALL tridiag(kte,a,b,c,d)
L04364      CALL tridiag2(kte,a,b,c,d,x)
L04365  !    CALL tridiag3(kte,a,b,c,d,x)
L04366  
L04367      DO k=kts,kte
L04368         !thl(k)=d(k-kts+1)
L04369         thl(k)=x(k)
L04370      ENDDO
L04371  
L04372  IF (bl_mynn_mixqt > 0) THEN
L04373   !============================================
L04374   ! MIX total water (sqw = sqc + sqv + sqi)
L04375   ! NOTE: no total water tendency is output; instead, we must calculate
L04376   !       the saturation specific humidity and then 
L04377   !       subtract out the moisture excess (sqc & sqi)
L04378   !============================================
L04379   if (bl_mynn_edmf > 1) then
L04380  
L04381      DO k=kts+1,kte-1
L04382         upcont(k)= s_awqt1(k)- s_aw1(k)*(sqw(k)*upwind+sqw(k-1)*(one-upwind))
L04383         dncont(k)=sd_awqt1(k)-sd_aw1(k)*(sqw(k)*upwind+sqw(k-1)*(one-upwind))
L04384      ENDDO
L04385      ! no flux at the top of the atmosphere
L04386      upcont(kte)=zero
L04387      dncont(kte)=zero
L04388      ! upcont(1) and dncont(1) are not used so they don't need to be set
L04389  
L04390      k=kts
L04391      a(1)=zero
L04392      b(1)=one + dtz(k)*khdz(k+1)*rhoinv(k)
L04393      c(1)=    - dtz(k)*khdz(k+1)*rhoinv(k)
L04394      d(1)=sqw(k)+dtz(k)*rhosfc*flq*rhoinv(k) + qcd(k)*delt              &
L04395           - dtz(k)*(upcont(k+1)+dncont(k+1))                            &
L04396           + sub_sqv(k)*delt + det_sqv(k)*delt
L04397  
L04398      DO k=kts+1,kte-1
L04399         a(k)=   - dtz(k)*khdz(k)*rhoinv(k)
L04400         b(k)=one+ dtz(k)*(khdz(k)+khdz(k+1))*rhoinv(k)
L04401         c(k)=   - dtz(k)*khdz(k+1)*rhoinv(k)
L04402         d(k)=sqw(k)-dtz(k)*(upcont(k+1)-upcont(k)+dncont(k+1)-dncont(k)) &
L04403             &  + sub_sqv(k)*delt + det_sqv(k)*delt
L04404      ENDDO
L04405  
L04406   else !implicit
L04407  
L04408      k=kts
L04409      !rho-weighted:
L04410      a(k)=  -dtz(k)*khdz(k)*rhoinv(k)
L04411      b(k)=one+dtz(k)*(khdz(k+1)+khdz(k))*rhoinv(k)         &
L04412         & - p5*dtz(k)*rhoinv(k)*s_aw1(k+1)                 &
L04413         & - p5*dtz(k)*rhoinv(k)*sd_aw1(k+1)
L04414      c(k)=  -dtz(k)*khdz(k+1)*rhoinv(k)                    &
L04415         & - p5*dtz(k)*rhoinv(k)*s_aw1(k+1)                 &
L04416         & - p5*dtz(k)*rhoinv(k)*sd_aw1(k+1)
L04417      d(k)=sqw(k)  + dtz(k)*rhosfc*flq*rhoinv(k) + qcd(k)*delt &
L04418         &  - dtz(k)*rhoinv(k)*s_awqt1(k+1)                 &
L04419         &  + dtz(k)*rhoinv(k)*sd_awqt1(k+1)
L04420  
L04421      do k=kts+1,kte-1
L04422         a(k)=  -dtz(k)*khdz(k)*rhoinv(k)                   &
L04423         & + p5*dtz(k)*rhoinv(k)*s_aw1(k)                   &
L04424         & + p5*dtz(k)*rhoinv(k)*sd_aw1(k)
L04425         b(k)=one+dtz(k)*(khdz(k)+khdz(k+1))*rhoinv(k)      &
L04426         & + p5*dtz(k)*rhoinv(k)*(s_aw1(k)-s_aw1(k+1))      &
L04427         & + p5*dtz(k)*rhoinv(k)*(sd_aw1(k)-sd_aw1(k+1))
L04428         c(k)=  -dtz(k)*khdz(k+1)*rhoinv(k)                 &
L04429         & - p5*dtz(k)*rhoinv(k)*s_aw1(k+1)                 &
L04430         & - p5*dtz(k)*rhoinv(k)*sd_aw1(k+1)
L04431         d(k)=sqw(k) + qcd(k)*delt                          &
L04432         & + dtz(k)*rhoinv(k)*(s_awqt1(k)-s_awqt1(k+1))     &
L04433         & - dtz(k)*rhoinv(k)*(sd_awqt1(k)-sd_awqt1(k+1))
L04434      enddo
L04435  endif
L04436  !! no flux at the top
L04437  !    a(kte)=-1.
L04438  !    b(kte)=1.
L04439  !    c(kte)=0.
L04440  !    d(kte)=0.
L04441  !! specified gradient at the top
L04442  !assume gradqw_top=gradqv_top
L04443  !    a(kte)=-1.
L04444  !    b(kte)=1.
L04445  !    c(kte)=0.
L04446  !    d(kte)=gradqv_top*dztop
L04447  !! prescribed value
L04448      a(kte)=zero
L04449      b(kte)=one
L04450      c(kte)=zero
L04451      d(kte)=sqw(kte)
L04452  
L04453  !    CALL tridiag(kte,a,b,c,d)
L04454      CALL tridiag2(kte,a,b,c,d,sqw2)
L04455  !    CALL tridiag3(kte,a,b,c,d,sqw2)
L04456  
L04457  !    DO k=kts,kte
L04458  !       sqw2(k)=d(k-kts+1)
L04459  !    ENDDO
L04460  ELSE
L04461      sqw2=sqw
L04462  ENDIF
```

> - **v 方程**：与 u 完全同构（`voce` 洋流 v 分量）。
> - **θ_l 方程**：右端多四项——表面通量 `rhosfc·flt`、逆梯度 `tcd·delt`、**TKE 耗散加热 `diss_heat·delt`**（code_09a §09a.4.7 算出的 7.2 K/h 上限量）、环境项 `sub_thl/det_thl`。**θ_l 是被推进的变量**（液水位温），位温趋势稍后由凝结量重建。
> - **总水 sqw 方程**（`bl_mynn_mixqt > 0`）：同构三对角解出 `sqw2`——注释明说“不输出总水倾向；稍后从饱和检查里拆出 sqv/sqc/sqi”。**混合总水 vs 分相混合**（mixqt=0 时分别推 sqc/sqv）是该方案水分处理的两条路线：总水路线在饱和拆分处统一凝结构造，物理上更自洽（凝结不改变总水）。

<!-- code_extract code_extract.py v1.1
source: phys/MYNN-EDMF/module_bl_mynnedmf.F90
ranges: L4464-L4780
file_lines: 8776
file_md5: ec93fee9745a3e0b25be55a61b5aff8a
display: line-numbered (strip L-prefix and !file: line to restore)
range_md5: af51f47aa86a8b1600b7f6eb56d8a781
seg_lines: 317
-->

```fortran
!file: phys/MYNN-EDMF/module_bl_mynnedmf.F90    L4464-L4780
L04464  IF (bl_mynn_mixqt == 0) THEN
L04465  !============================================
L04466  ! cloud water ( sqc ). If mixing total water (bl_mynn_mixqt > 0),
L04467  ! then sqc will be backed out of saturation check (below).
L04468  !============================================
L04469   IF (bl_mynn_cloudmix > 0 .AND. FLAG_QC) THEN
L04470  
L04471     if (bl_mynn_edmf > 1) then
L04472  
L04473        DO k=kts+1,kte-1
L04474           upcont(k)= s_awqc1(k)- s_aw1(k)*(sqc(k)*upwind+sqc(k-1)*(one-upwind))
L04475           dncont(k)=sd_awqc1(k)-sd_aw1(k)*(sqc(k)*upwind+sqc(k-1)*(one-upwind))
L04476        ENDDO
L04477        ! no flux at the top of the atmosphere
L04478        upcont(kte)=zero
L04479        dncont(kte)=zero
L04480        ! upcont(1) and dncont(1) are not used so they don't need to be set
L04481  
L04482        k=kts
L04483        a(1)=zero
L04484        b(1)=one + dtz(k)*khdz(k+1)*rhoinv(k)
L04485        c(1)=    - dtz(k)*khdz(k+1)*rhoinv(k)
L04486        d(1)=sqc(k)+dtz(k)*rhosfc*flqc*rhoinv(k) + qcd(k)*delt             &
L04487            &    - dtz(k)*(upcont(k+1)+dncont(k+1))                        &
L04488            &    + det_sqc(k)*delt
L04489      
L04490        DO k=kts+1,kte-1
L04491           a(k)=   - dtz(k)*khdz(k)*rhoinv(k)
L04492           b(k)=one+ dtz(k)*(khdz(k)+khdz(k+1))*rhoinv(k)
L04493           c(k)=   - dtz(k)*khdz(k+1)*rhoinv(k)
L04494           d(k)=sqc(k)-dtz(k)*(upcont(k+1)-upcont(k)+dncont(k+1)-dncont(k)) &
L04495               &  + det_sqc(k)*delt
L04496        ENDDO
L04497  
L04498      else !implicit
L04499  
L04500         k=kts
L04501         !rho-weighted:
L04502         a(k)=  -dtz(k)*khdz(k)*rhoinv(k)
L04503         b(k)=one+dtz(k)*(khdz(k+1)+khdz(k))*rhoinv(k)        &
L04504         &  - p5*dtz(k)*rhoinv(k)*s_aw1(k+1)                  &
L04505         &  - p5*dtz(k)*rhoinv(k)*sd_aw1(k+1)
L04506         c(k)=  -dtz(k)*khdz(k+1)*rhoinv(k)                   &
L04507         &  - p5*dtz(k)*rhoinv(k)*s_aw1(k+1)                  &
L04508         &  - p5*dtz(k)*rhoinv(k)*sd_aw1(k+1)
L04509         d(k)=sqc(k)  + dtz(k)*rhosfc*flqc*rhoinv(k) + qcd(k)*delt &
L04510         &  - dtz(k)*rhoinv(k)*s_awqc1(k+1)                   &
L04511         &  + dtz(k)*rhoinv(k)*sd_awqc1(k+1)                  &
L04512         &  + det_sqc(k)*delt
L04513  
L04514         do k=kts+1,kte-1
L04515            a(k)=  -dtz(k)*khdz(k)*rhoinv(k)                  &
L04516            & + p5*dtz(k)*rhoinv(k)*s_aw1(k)                  &
L04517            & + p5*dtz(k)*rhoinv(k)*sd_aw1(k)
L04518            b(k)=one+dtz(k)*(khdz(k)+khdz(k+1))*rhoinv(k)     &
L04519            & + p5*dtz(k)*rhoinv(k)*(s_aw1(k)-s_aw1(k+1))     &
L04520            & + p5*dtz(k)*rhoinv(k)*(sd_aw1(k)-sd_aw1(k+1))
L04521            c(k)=  -dtz(k)*khdz(k+1)*rhoinv(k)                &
L04522            & - p5*dtz(k)*rhoinv(k)*s_aw1(k+1)                &
L04523            & - p5*dtz(k)*rhoinv(k)*sd_aw1(k+1)
L04524            d(k)=sqc(k) + qcd(k)*delt                         &
L04525            & + dtz(k)*rhoinv(k)*(s_awqc1(k)-s_awqc1(k+1))    &
L04526            & - dtz(k)*rhoinv(k)*(sd_awqc1(k)-sd_awqc1(k+1))  &
L04527            & + det_sqc(k)*delt
L04528         enddo
L04529      endif
L04530      
L04531  ! prescribed value
L04532      a(kte)=zero
L04533      b(kte)=one
L04534      c(kte)=zero
L04535      d(kte)=sqc(kte)
L04536  
L04537  !    CALL tridiag(kte,a,b,c,d)
L04538      CALL tridiag2(kte,a,b,c,d,sqc2)
L04539  !    CALL tridiag3(kte,a,b,c,d,sqc2)
L04540  
L04541  !    DO k=kts,kte
L04542  !       sqc2(k)=d(k-kts+1)
L04543  !    ENDDO
L04544    ELSE
L04545      !If not mixing clouds, set "updated" array equal to original array
L04546      sqc2=sqc
L04547    ENDIF
L04548  ENDIF
L04549  
L04550  IF (bl_mynn_mixqt == 0) THEN
L04551    !============================================
L04552    ! MIX WATER VAPOR ONLY ( sqv ). If mixing total water (bl_mynn_mixqt > 0),
L04553    ! then sqv will be backed out of saturation check (below).
L04554    !============================================
L04555  
L04556     k=kts
L04557     !limit unreasonably large negative fluxes:
L04558     qvflux = flqv
L04559     if (qvflux < zero) then
L04560        !do not allow specified surface flux to reduce qv below 1e-8 kg/kg
L04561        qvflux = max(qvflux, (min(0.9*sqv(kts) - 1e-8, zero)/dtz(kts)))
L04562     endif
L04563  
L04564     if (bl_mynn_edmf > 1) then
L04565  
L04566        DO k=kts+1,kte-1
L04567           upcont(k)= s_awqv1(k)- s_aw1(k)*(sqv(k)*upwind+sqv(k-1)*(one-upwind))
L04568           dncont(k)=sd_awqv1(k)-sd_aw1(k)*(sqv(k)*upwind+sqv(k-1)*(one-upwind))
L04569        ENDDO
L04570        ! no flux at the top of the atmosphere
L04571        upcont(kte)=zero
L04572        dncont(kte)=zero
L04573        ! upcont(1) and dncont(1) are not used so they don't need to be set
L04574  
L04575        k=kts
L04576        a(1)=zero
L04577        b(1)=one + dtz(k)*khdz(k+1)*rhoinv(k)
L04578        c(1)=    - dtz(k)*khdz(k+1)*rhoinv(k)
L04579        d(1)=sqv(k)+dtz(k)*rhosfc*qvflux*rhoinv(k) + qcd(k)*delt             &
L04580            &    - dtz(k)*(upcont(k+1)+dncont(k+1))			   &    
L04581            &    + sub_sqv(k)*delt + det_sqv(k)*delt
L04582  
L04583        DO k=kts+1,kte-1
L04584           a(k)=   - dtz(k)*khdz(k)*rhoinv(k)
L04585           b(k)=one+ dtz(k)*(khdz(k)+khdz(k+1))*rhoinv(k)
L04586           c(k)=   - dtz(k)*khdz(k+1)*rhoinv(k)
L04587           d(k)=sqv(k)-dtz(k)*(upcont(k+1)-upcont(k)+dncont(k+1)-dncont(k)) &
L04588               &   + sub_sqv(k)*delt + det_sqv(k)*delt
L04589        ENDDO
L04590  
L04591     else !implicit 
L04592  
L04593        k=kts
L04594        !rho-weighted:
L04595        a(k)=  -dtz(k)*khdz(k)*rhoinv(k)
L04596        b(k)=one+dtz(k)*(khdz(k+1)+khdz(k))*rhoinv(k)        &
L04597        & - p5*dtz(k)*rhoinv(k)*s_aw1(k+1)                   &
L04598        & - p5*dtz(k)*rhoinv(k)*sd_aw1(k+1)
L04599        c(k)=  -dtz(k)*khdz(k+1)*rhoinv(k)                   &
L04600        & - p5*dtz(k)*rhoinv(k)*s_aw1(k+1)                   &
L04601        & - p5*dtz(k)*rhoinv(k)*sd_aw1(k+1)
L04602        d(k)=sqv(k)  + dtz(k)*rhosfc*qvflux*rhoinv(k) + qcd(k)*delt &
L04603        & - dtz(k)*rhoinv(k)*s_awqv1(k+1)                    &
L04604        & + dtz(k)*rhoinv(k)*sd_awqv1(k+1)                   &
L04605        & + sub_sqv(k)*delt + det_sqv(k)*delt
L04606  
L04607        do k=kts+1,kte-1
L04608           a(k)=  -dtz(k)*khdz(k)*rhoinv(k)                  &
L04609           & + p5*dtz(k)*rhoinv(k)*s_aw1(k)                  &
L04610           & + p5*dtz(k)*rhoinv(k)*sd_aw1(k)
L04611           b(k)=one+dtz(k)*(khdz(k)+khdz(k+1))*rhoinv(k)     &
L04612           & + p5*dtz(k)*rhoinv(k)*(s_aw1(k)-s_aw1(k+1))     &
L04613           & + p5*dtz(k)*rhoinv(k)*(sd_aw1(k)-sd_aw1(k+1))
L04614           c(k)=  -dtz(k)*khdz(k+1)*rhoinv(k)                &
L04615           & - p5*dtz(k)*rhoinv(k)*s_aw1(k+1)                &
L04616           & - p5*dtz(k)*rhoinv(k)*sd_aw1(k+1)
L04617           d(k)=sqv(k) + qcd(k)*delt                         &
L04618           & + dtz(k)*rhoinv(k)*(s_awqv1(k)-s_awqv1(k+1))    &
L04619           & - dtz(k)*rhoinv(k)*(sd_awqv1(k)-sd_awqv1(k+1))  &
L04620           & + sub_sqv(k)*delt + det_sqv(k)*delt
L04621        enddo
L04622     endif
L04623     
L04624  ! no flux at the top
L04625  !    a(kte)=-1.
L04626  !    b(kte)=1.
L04627  !    c(kte)=0.
L04628  !    d(kte)=0.
L04629  
L04630  ! specified gradient at the top
L04631  ! assume gradqw_top=gradqv_top
L04632  !    a(kte)=-1.
L04633  !    b(kte)=1.
L04634  !    c(kte)=0.
L04635  !    d(kte)=gradqv_top*dztop
L04636  
L04637  ! prescribed value
L04638      a(kte)=zero
L04639      b(kte)=one
L04640      c(kte)=zero
L04641      d(kte)=sqv(kte)
L04642  
L04643  !    CALL tridiag(kte,a,b,c,d)
L04644      CALL tridiag2(kte,a,b,c,d,sqv2)
L04645  !    CALL tridiag3(kte,a,b,c,d,sqv2)
L04646  
L04647  !    DO k=kts,kte
L04648  !       sqv2(k)=d(k-kts+1)
L04649  !    ENDDO
L04650  ELSE
L04651      sqv2=sqv
L04652  ENDIF
L04653  
L04654  !============================================
L04655  ! MIX CLOUD ICE ( sqi )                      
L04656  !============================================
L04657  IF (bl_mynn_cloudmix > 0 .AND. FLAG_QI) THEN
L04658  
L04659     if (bl_mynn_edmf > 1) then
L04660  
L04661        DO k=kts+1,kte-1
L04662           upcont(k)= zero !s_awqi1(k)- s_aw1(k)*(sqi(k)*upwind+sqi(k-1)*(one-upwind))
L04663           dncont(k)=sd_awqi1(k)-sd_aw1(k)*(sqi(k)*upwind+sqi(k-1)*(one-upwind))
L04664        ENDDO
L04665        ! no flux at the top of the atmosphere
L04666        upcont(kte)=zero
L04667        dncont(kte)=zero
L04668        ! upcont(1) and dncont(1) are not used so they don't need to be set
L04669  
L04670        k=kts
L04671        a(1)=zero
L04672        b(1)=one + dtz(k)*khdz(k+1)*rhoinv(k)
L04673        c(1)=    - dtz(k)*khdz(k+1)*rhoinv(k)
L04674        d(1)=sqi(k)                                         &
L04675            &    - dtz(k)*(upcont(k+1)+dncont(k+1))
L04676  
L04677        DO k=kts+1,kte-1
L04678           a(k)=   - dtz(k)*khdz(k)*rhoinv(k)
L04679           b(k)=one+ dtz(k)*(khdz(k)+khdz(k+1))*rhoinv(k)
L04680           c(k)=   - dtz(k)*khdz(k+1)*rhoinv(k)
L04681           d(k)=sqi(k)-dtz(k)*(upcont(k+1)-upcont(k)+dncont(k+1)-dncont(k))
L04682        ENDDO
L04683  
L04684     else !implicit
L04685        
L04686        k=kts
L04687        a(k)=  -dtz(k)*khdz(k)*rhoinv(k)
L04688        b(k)=one+dtz(k)*(khdz(k+1)+khdz(k))*rhoinv(k)      &
L04689  !      &  - p5*dtz(k)*rhoinv(k)*s_aw1(k+1)               &
L04690        &  - p5*dtz(k)*rhoinv(k)*sd_aw1(k+1)
L04691        c(k)=  -dtz(k)*khdz(k+1)*rhoinv(k)                 &
L04692  !      &  - p5*dtz(k)*rhoinv(k)*s_aw1(k+1)               &
L04693        &  - p5*dtz(k)*rhoinv(k)*sd_aw1(k+1)
L04694        d(k)=sqi(k)                                        &
L04695  !      &  - dtz(k)*rhoinv(k)*s_awqi1(k+1)                &
L04696        &  + dtz(k)*rhoinv(k)*sd_awqi1(k+1)
L04697  
L04698        do k=kts+1,kte-1
L04699           a(k)=  -dtz(k)*khdz(k)*rhoinv(k)                &
L04700  !         & + p5*dtz(k)*rhoinv(k)*s_aw1(k)               &
L04701           & + p5*dtz(k)*rhoinv(k)*sd_aw1(k)
L04702           b(k)=one+dtz(k)*(khdz(k)+khdz(k+1))*rhoinv(k)   &
L04703  !         & + p5*dtz(k)*rhoinv(k)*(s_aw1(k)-s_aw1(k+1))  &
L04704           & + p5*dtz(k)*rhoinv(k)*(sd_aw1(k)-sd_aw1(k+1))
L04705           c(k)=  -dtz(k)*khdz(k+1)*rhoinv(k)              &
L04706  !         & - p5*dtz(k)*rhoinv(k)*s_aw1(k+1)             &
L04707           & - p5*dtz(k)*rhoinv(k)*sd_aw1(k+1)
L04708           d(k)=sqi(k)                                     &
L04709  !         & + dtz(k)*rhoinv(k)*(s_awqi1(k)-s_awqi1(k+1)) &
L04710           & - dtz(k)*rhoinv(k)*(sd_awqi1(k)-sd_awqi1(k+1))
L04711        enddo
L04712     endif
L04713  
L04714  !! no flux at the top
L04715  !    a(kte)=-1.       
L04716  !    b(kte)=1.        
L04717  !    c(kte)=0.        
L04718  !    d(kte)=0.        
L04719  
L04720  !! specified gradient at the top
L04721  !assume gradqw_top=gradqv_top
L04722  !    a(kte)=-1.
L04723  !    b(kte)=1.
L04724  !    c(kte)=0.
L04725  !    d(kte)=gradqv_top*dztop
L04726  
L04727  !! prescribed value
L04728      a(kte)=zero
L04729      b(kte)=one
L04730      c(kte)=zero
L04731      d(kte)=sqi(kte)
L04732  
L04733  !    CALL tridiag(kte,a,b,c,d)
L04734      CALL tridiag2(kte,a,b,c,d,sqi2)
L04735  !    CALL tridiag3(kte,a,b,c,d,sqi2)
L04736  
L04737  !    DO k=kts,kte
L04738  !       sqi2(k)=d(k-kts+1)
L04739  !    ENDDO
L04740  ELSE
L04741     sqi2=sqi
L04742  ENDIF
L04743  
L04744  !============================================
L04745  ! MIX SNOW ( sqs )
L04746  !============================================
L04747  !hard-code to not mix snow
L04748  IF (bl_mynn_cloudmix > 0 .AND. .false.) THEN
L04749  
L04750      k=kts
L04751  !rho-weighted:
L04752      a(k)=  -dtz(k)*khdz(k)*rhoinv(k)
L04753      b(k)=one+dtz(k)*(khdz(k+1)+khdz(k))*rhoinv(k)
L04754      c(k)=  -dtz(k)*khdz(k+1)*rhoinv(k)
L04755      d(k)=sqs(k)
L04756  
L04757      DO k=kts+1,kte-1
L04758         a(k)=  -dtz(k)*khdz(k)*rhoinv(k)
L04759         b(k)=one+dtz(k)*(khdz(k)+khdz(k+1))*rhoinv(k)
L04760         c(k)=  -dtz(k)*khdz(k+1)*rhoinv(k)
L04761         d(k)=sqs(k)
L04762      ENDDO
L04763  
L04764  !! prescribed value
L04765      a(kte)=zero
L04766      b(kte)=one
L04767      c(kte)=zero
L04768      d(kte)=sqs(kte)
L04769  
L04770  !    CALL tridiag(kte,a,b,c,d)
L04771      CALL tridiag2(kte,a,b,c,d,sqs2)
L04772  !    CALL tridiag3(kte,a,b,c,d,sqs2)
L04773  
L04774  !    DO k=kts,kte
L04775  !       sqs2(k)=d(k-kts+1)
L04776  !    ENDDO
L04777  ELSE
L04778     sqs2=sqs
L04779  ENDIF
L04780  
```

> - **sqc 方程**（`bl_mynn_cloudmix > 0 .AND. FLAG_QC` 且 mixqt=0）：右端含 `flqc`（海盐/雾沉降通量，当前恒零）与 `det_sqc`。**不混合云时 `sqc2=sqc` 原样传过**。
> - **sqv 方程**：表面通量加了**负通量保护**（L4557–L4562）：`qvflux = max(flqv, (min(0.9·sqv(kts)−1e-8, 0))/dtz)`——**蒸发不许把最底层比湿抽到 1e-8 以下**（每步最多抽走 90%）。
> - **sqi 方程**：MF 侧只有下沉流贡献（`upcont ≡ 0` 被注释清零——**上升流不携带冰**，冰相在上升流中由 condensation_edmf 归零）；implicit 分支里 s_aw 项全被注释、只留 sd_aw——**上升流的冰通量从倾向方程中显式剔除**。
> - **sqs（雪）**：`IF (bl_mynn_cloudmix > 0 .AND. .false.)`——**硬编码关闭**（注释 “hard-code to not mix snow”）。边界层不混合雪：与 `sqw1` 定义（不含雪）一致的方案级决策。

<!-- code_extract code_extract.py v1.1
source: phys/MYNN-EDMF/module_bl_mynnedmf.F90
ranges: L4782-L5250
file_lines: 8776
file_md5: ec93fee9745a3e0b25be55a61b5aff8a
display: line-numbered (strip L-prefix and !file: line to restore)
range_md5: 7b7ce5bfb3a6c49c593fd2057c4a0a1c
seg_lines: 469
-->

```fortran
!file: phys/MYNN-EDMF/module_bl_mynnedmf.F90    L4782-L5250
L04782  !! cloud ice number concentration (qni)
L04783  !!============================================
L04784  IF (bl_mynn_cloudmix > 0 .AND. FLAG_QNI .AND. &
L04785        bl_mynn_mixnumcon > 0) THEN
L04786  
L04787     DO k=kts,kte
L04788        qni2(k)=max(qni(k), zero)
L04789        !enforce minimum number concentration
L04790        if (sqi(k) .gt. 1e-12)qni2(k)=max(qni2(k), ni_min)
L04791     ENDDO
L04792  
L04793     if (bl_mynn_edmf > 1) then
L04794  
L04795        DO k=kts+1,kte-1
L04796           upcont(k)= s_awqni1(k)- s_aw1(k)*(qni2(k)*upwind+qni2(k-1)*(one-upwind))
L04797           dncont(k)=sd_awqni1(k)-sd_aw1(k)*(qni2(k)*upwind+qni2(k-1)*(one-upwind))
L04798        ENDDO
L04799        ! no flux at the top of the atmosphere
L04800        upcont(kte)=zero
L04801        dncont(kte)=zero
L04802        ! upcont(1) and dncont(1) are not used so they don't need to be set
L04803  
L04804        k=kts
L04805        a(1)=zero
L04806        b(1)=one + dtz(k)*khdz(k+1)*rhoinv(k)
L04807        c(1)=    - dtz(k)*khdz(k+1)*rhoinv(k)
L04808        d(1)=qni2(k)                                       &
L04809            &    - dtz(k)*(upcont(k+1)+dncont(k+1))
L04810  
L04811        DO k=kts+1,kte-1
L04812           a(k)=   - dtz(k)*khdz(k)*rhoinv(k)
L04813           b(k)=one+ dtz(k)*(khdz(k)+khdz(k+1))*rhoinv(k)
L04814           c(k)=   - dtz(k)*khdz(k+1)*rhoinv(k)
L04815           d(k)=qni2(k)-dtz(k)*(upcont(k+1)-upcont(k)+dncont(k+1)-dncont(k))
L04816        ENDDO
L04817  
L04818     else !implicit
L04819        
L04820        k=kts
L04821        a(k)=  -dtz(k)*khdz(k)*rhoinv(k)
L04822        b(k)=one+dtz(k)*(khdz(k+1)+khdz(k))*rhoinv(k)        &
L04823        &  - p5*dtz(k)*rhoinv(k)*s_aw1(k+1)                  &
L04824        &  - p5*dtz(k)*rhoinv(k)*sd_aw1(k+1)
L04825        c(k)=  -dtz(k)*khdz(k+1)*rhoinv(k)                   &
L04826        &  - p5*dtz(k)*rhoinv(k)*s_aw1(k+1)                  &
L04827        &  - p5*dtz(k)*rhoinv(k)*sd_aw1(k+1)
L04828        d(k)=qni2(k)                                         &
L04829        &  - dtz(k)*rhoinv(k)*s_awqni1(k+1)                  &
L04830        &  + dtz(k)*rhoinv(k)*sd_awqni1(k+1)
L04831  
L04832        do k=kts+1,kte-1
L04833           a(k)=  -dtz(k)*khdz(k)*rhoinv(k)                  &
L04834           & + p5*dtz(k)*rhoinv(k)*s_aw1(k)                  &
L04835           & + p5*dtz(k)*rhoinv(k)*sd_aw1(k)
L04836           b(k)=one+dtz(k)*(khdz(k)+khdz(k+1))*rhoinv(k)     &
L04837           & + p5*dtz(k)*rhoinv(k)*(s_aw1(k)-s_aw1(k+1))     &
L04838           & + p5*dtz(k)*rhoinv(k)*(sd_aw1(k)-sd_aw1(k+1))
L04839           c(k)=  -dtz(k)*khdz(k+1)*rhoinv(k)                &
L04840           & - p5*dtz(k)*rhoinv(k)*s_aw1(k+1)                &
L04841           & - p5*dtz(k)*rhoinv(k)*sd_aw1(k+1)
L04842           d(k)=qni2(k)                                      &
L04843           & + dtz(k)*rhoinv(k)*(s_awqni1(k)-s_awqni1(k+1))  &
L04844           & - dtz(k)*rhoinv(k)*(sd_awqni1(k)-sd_awqni1(k+1))
L04845        enddo
L04846     endif
L04847     
L04848  !! prescribed value
L04849      a(kte)=zero
L04850      b(kte)=one
L04851      c(kte)=zero
L04852      d(kte)=qni2(kte)
L04853  
L04854  !    CALL tridiag(kte,a,b,c,d)
L04855      CALL tridiag2(kte,a,b,c,d,x)
L04856  !    CALL tridiag3(kte,a,b,c,d,x)
L04857  
L04858      DO k=kts,kte
L04859         !qni2(k)=d(k-kts+1)
L04860         qni2(k)=x(k)
L04861         !enforce minimum number concentration
L04862         if (sqi2(k) .gt. 1e-12)qni2(k)=max(qni2(k), ni_min)
L04863      ENDDO
L04864  
L04865  ELSE
L04866      qni2=qni
L04867  ENDIF
L04868  
L04869  !!============================================
L04870  !! cloud water number concentration (qnc)     
L04871  !! include non-local transport                
L04872  !!============================================
L04873  IF (bl_mynn_cloudmix > 0 .AND. FLAG_QNC .AND. &
L04874      bl_mynn_mixnumcon > 0) THEN
L04875  
L04876     DO k=kts,kte
L04877        qnc2(k)=max(qnc(k),zero)
L04878        !enforce minimum number concentration
L04879        if (sqc(k) .gt. 1e-12)qnc2(k)=max(qnc2(k), nc_min)
L04880     ENDDO
L04881  
L04882     if (bl_mynn_edmf > 1) then
L04883  
L04884        DO k=kts+1,kte-1
L04885           upcont(k)= s_awqnc1(k)- s_aw1(k)*(qnc2(k)*upwind+qnc2(k-1)*(one-upwind))
L04886           dncont(k)=sd_awqnc1(k)-sd_aw1(k)*(qnc2(k)*upwind+qnc2(k-1)*(one-upwind))
L04887        ENDDO
L04888        ! no flux at the top of the atmosphere
L04889        upcont(kte)=zero
L04890        dncont(kte)=zero
L04891        ! upcont(1) and dncont(1) are not used so they don't need to be set
L04892  
L04893        k=kts
L04894        a(1)=zero
L04895        b(1)=one + dtz(k)*khdz(k+1)*rhoinv(k)
L04896        c(1)=    - dtz(k)*khdz(k+1)*rhoinv(k)
L04897        d(1)=qnc2(k)                                       &
L04898            &    - dtz(k)*(upcont(k+1)+dncont(k+1))
L04899  
L04900        DO k=kts+1,kte-1
L04901           a(k)=   - dtz(k)*khdz(k)*rhoinv(k)
L04902           b(k)=one+ dtz(k)*(khdz(k)+khdz(k+1))*rhoinv(k)
L04903           c(k)=   - dtz(k)*khdz(k+1)*rhoinv(k)
L04904           d(k)=qnc2(k)-dtz(k)*(upcont(k+1)-upcont(k)+dncont(k+1)-dncont(k))
L04905        ENDDO
L04906  
L04907     else !implicit
L04908      
L04909        k=kts
L04910        a(k)=  -dtz(k)*khdz(k)*rhoinv(k)
L04911        b(k)=one+dtz(k)*(khdz(k+1)+khdz(k))*rhoinv(k)        &
L04912        &  - p5*dtz(k)*rhoinv(k)*s_aw1(k+1)                  &
L04913        &  - p5*dtz(k)*rhoinv(k)*sd_aw1(k+1)
L04914        c(k)=  -dtz(k)*khdz(k+1)*rhoinv(k)                   &
L04915        &  - p5*dtz(k)*rhoinv(k)*s_aw1(k+1)                  &
L04916        &  - p5*dtz(k)*rhoinv(k)*sd_aw1(k+1)
L04917        d(k)=qnc2(k)                                         &
L04918        &  - dtz(k)*rhoinv(k)*s_awqnc1(k+1)                  &
L04919        &  + dtz(k)*rhoinv(k)*sd_awqnc1(k+1)
L04920  
L04921        do k=kts+1,kte-1
L04922           a(k)=  -dtz(k)*khdz(k)*rhoinv(k)                  &
L04923           & + p5*dtz(k)*rhoinv(k)*s_aw1(k)                  &
L04924           & + p5*dtz(k)*rhoinv(k)*sd_aw1(k)
L04925           b(k)=one+dtz(k)*(khdz(k)+khdz(k+1))*rhoinv(k)     &
L04926           & + p5*dtz(k)*rhoinv(k)*(s_aw1(k)-s_aw1(k+1))     &
L04927           & + p5*dtz(k)*rhoinv(k)*(sd_aw1(k)-sd_aw1(k+1))
L04928           c(k)=  -dtz(k)*khdz(k+1)*rhoinv(k)                &
L04929           & - p5*dtz(k)*rhoinv(k)*s_aw1(k+1)                &
L04930           & - p5*dtz(k)*rhoinv(k)*sd_aw1(k+1)
L04931           d(k)=qnc2(k)                                      &
L04932           & + dtz(k)*rhoinv(k)*(s_awqnc1(k)-s_awqnc1(k+1))  &
L04933           & - dtz(k)*rhoinv(k)*(sd_awqnc1(k)-sd_awqnc1(k+1))
L04934        enddo
L04935     endif
L04936  
L04937  !! prescribed value
L04938      a(kte)=zero
L04939      b(kte)=one
L04940      c(kte)=zero
L04941      d(kte)=qnc2(kte)
L04942  
L04943  !    CALL tridiag(kte,a,b,c,d)
L04944      CALL tridiag2(kte,a,b,c,d,x)
L04945  !    CALL tridiag3(kte,a,b,c,d,x)
L04946  
L04947      DO k=kts,kte
L04948         !qnc2(k)=d(k-kts+1)
L04949         qnc2(k)=x(k)
L04950         !enforce a minimum number concentration
L04951         if (sqc2(k) .gt. 1e-12)qnc2(k)=max(qnc2(k), nc_min)
L04952      ENDDO
L04953  
L04954  ELSE
L04955      qnc2=qnc
L04956  ENDIF
L04957  
L04958  !============================================
L04959  ! Water-friendly aerosols ( qnwfa ).
L04960  !============================================
L04961  IF (FLAG_QNWFA .AND. bl_mynn_mixaerosols > 0) THEN
L04962  
L04963     do k=kts,kte
L04964        qnwfa2(k)=max(qnwfa(k),zero)
L04965     enddo
L04966  
L04967     if (bl_mynn_edmf > 1) then
L04968  
L04969        DO k=kts+1,kte-1
L04970           upcont(k)= s_awqnwfa1(k)- s_aw1(k)*(qnwfa2(k)*upwind+qnwfa2(k-1)*(one-upwind))
L04971           dncont(k)=sd_awqnwfa1(k)-sd_aw1(k)*(qnwfa2(k)*upwind+qnwfa2(k-1)*(one-upwind))
L04972        ENDDO
L04973        ! no flux at the top of the atmosphere
L04974        upcont(kte)=zero
L04975        dncont(kte)=zero
L04976        ! upcont(1) and dncont(1) are not used so they don't need to be set
L04977  
L04978        k=kts
L04979        a(1)=zero
L04980        b(1)=one + dtz(k)*khdz(k+1)*rhoinv(k)
L04981        c(1)=    - dtz(k)*khdz(k+1)*rhoinv(k)
L04982        d(1)=qnwfa2(k)                                       &
L04983            &    - dtz(k)*(upcont(k+1)+dncont(k+1))
L04984  
L04985        DO k=kts+1,kte-1
L04986           a(k)=   - dtz(k)*khdz(k)*rhoinv(k)
L04987           b(k)=one+ dtz(k)*(khdz(k)+khdz(k+1))*rhoinv(k)
L04988           c(k)=   - dtz(k)*khdz(k+1)*rhoinv(k)
L04989           d(k)=qnwfa2(k)-dtz(k)*(upcont(k+1)-upcont(k)+dncont(k+1)-dncont(k))
L04990        ENDDO
L04991  
L04992     else !implicit
L04993        
L04994        k=kts
L04995        a(k)=  -dtz(k)*khdz(k)*rhoinv(k)
L04996        b(k)=one+dtz(k)*(khdz(k+1)+khdz(k))*rhoinv(k)            &
L04997        &  - p5*dtz(k)*rhoinv(k)*s_aw1(k+1)                      &
L04998        &  - p5*dtz(k)*rhoinv(k)*sd_aw1(k+1)
L04999        c(k)=  -dtz(k)*khdz(k+1)*rhoinv(k)                       &
L05000        &  - p5*dtz(k)*rhoinv(k)*s_aw1(k+1)                      &
L05001        &  - p5*dtz(k)*rhoinv(k)*sd_aw1(k+1)
L05002        d(k)=qnwfa2(k)                                           &
L05003        &  - dtz(k)*rhoinv(k)*s_awqnwfa1(k+1)                    &
L05004        &  + dtz(k)*rhoinv(k)*sd_awqnwfa1(k+1)
L05005  
L05006        do k=kts+1,kte-1
L05007           a(k)=  -dtz(k)*khdz(k)*rhoinv(k)                      &
L05008           & + p5*dtz(k)*rhoinv(k)*s_aw1(k)                      &
L05009           & + p5*dtz(k)*rhoinv(k)*sd_aw1(k)
L05010           b(k)=one+dtz(k)*(khdz(k)+khdz(k+1))*rhoinv(k)         &
L05011           & + p5*dtz(k)*rhoinv(k)*(s_aw1(k)-s_aw1(k+1))         &
L05012           & + p5*dtz(k)*rhoinv(k)*(sd_aw1(k)-sd_aw1(k+1))
L05013           c(k)=  -dtz(k)*khdz(k+1)*rhoinv(k)                    &
L05014           & - p5*dtz(k)*rhoinv(k)*s_aw1(k+1)                    &
L05015           & - p5*dtz(k)*rhoinv(k)*sd_aw1(k+1)
L05016           d(k)=qnwfa2(k)                                        &
L05017           & + dtz(k)*rhoinv(k)*(s_awqnwfa1(k)-s_awqnwfa1(k+1))  &
L05018           & - dtz(k)*rhoinv(k)*(sd_awqnwfa1(k)-sd_awqnwfa1(k+1))
L05019        enddo
L05020     endif
L05021        
L05022  ! prescribed value
L05023      a(kte)=zero
L05024      b(kte)=one
L05025      c(kte)=zero
L05026      d(kte)=qnwfa2(kte)
L05027  
L05028  !    CALL tridiag(kte,a,b,c,d)
L05029      call tridiag2(kte,a,b,c,d,x)
L05030  !    call tridiag3(kte,a,b,c,d,x)
L05031  
L05032      do k=kts,kte
L05033         !qnwfa2(k)=d(k)
L05034         qnwfa2(k)=max(x(k),zero)
L05035      enddo
L05036  
L05037      !apply liberal bounds
L05038      do k=kts,kte
L05039         !patch for high wfa over water (useful for cold starts)
L05040         if ((xland-1.5).ge.0)then   ! water
L05041            wt       = min(one, max(zero, zw(k)-100._kind_phys)/max(200._kind_phys, pblh)) !0 below 100 m, 1 above 300 m
L05042            wfa_max2 = (one - wt)*6.e8_kind_phys + wt*wfa_max
L05043         else                        ! land
L05044            wfa_max2 = wfa_max
L05045         endif
L05046         aero_min = wfa_min * exp(-zw(k)/wfa_ht)
L05047         aero_max = wfa_max2* exp(-zw(k)/wfa_ht)
L05048         qnwfa2(k)= min(max(aero_min, qnwfa2(k)), aero_max)
L05049      enddo
L05050  else
L05051      !if not mixing aerosols, set "updated" array equal to original array
L05052      qnwfa2=qnwfa
L05053  endif
L05054  
L05055  !============================================
L05056  ! Ice-friendly aerosols ( qnifa ).
L05057  !============================================
L05058  IF (FLAG_QNIFA .AND. bl_mynn_mixaerosols > 0) THEN
L05059  
L05060     do k=kts,kte
L05061        qnifa2(k)=max(qnifa(k),zero)
L05062     enddo
L05063  
L05064     if (bl_mynn_edmf > 1) then
L05065  
L05066        DO k=kts+1,kte-1
L05067           upcont(k)= s_awqnifa1(k)- s_aw1(k)*(qnifa2(k)*upwind+qnifa2(k-1)*(one-upwind))
L05068           dncont(k)=sd_awqnifa1(k)-sd_aw1(k)*(qnifa2(k)*upwind+qnifa2(k-1)*(one-upwind))
L05069        ENDDO
L05070        ! no flux at the top of the atmosphere
L05071        upcont(kte)=zero
L05072        dncont(kte)=zero
L05073  
L05074        k=kts
L05075        a(1)=zero
L05076        b(1)=one + dtz(k)*khdz(k+1)*rhoinv(k)
L05077        c(1)=    - dtz(k)*khdz(k+1)*rhoinv(k)
L05078        d(1)=qnifa2(k)                                       &
L05079            &    - dtz(k)*(upcont(k+1)+dncont(k+1))
L05080  
L05081        DO k=kts+1,kte-1
L05082           a(k)=   - dtz(k)*khdz(k)*rhoinv(k)
L05083           b(k)=one+ dtz(k)*(khdz(k)+khdz(k+1))*rhoinv(k)
L05084           c(k)=   - dtz(k)*khdz(k+1)*rhoinv(k)
L05085           d(k)=qnifa2(k)-dtz(k)*(upcont(k+1)-upcont(k)+dncont(k+1)-dncont(k))
L05086        ENDDO
L05087  
L05088     else !implicit
L05089      
L05090        k=kts
L05091        a(k)=  -dtz(k)*khdz(k)*rhoinv(k)
L05092        b(k)=one+dtz(k)*(khdz(k+1)+khdz(k))*rhoinv(k)            &
L05093        &  - p5*dtz(k)*rhoinv(k)*s_aw1(k+1)                      &
L05094        &  - p5*dtz(k)*rhoinv(k)*sd_aw1(k+1)
L05095        c(k)=  -dtz(k)*khdz(k+1)*rhoinv(k)                       &
L05096        &  - p5*dtz(k)*rhoinv(k)*s_aw1(k+1)                      &
L05097        &  - p5*dtz(k)*rhoinv(k)*sd_aw1(k+1)
L05098        d(k)=qnifa2(k)                                           &
L05099        &  - dtz(k)*rhoinv(k)*s_awqnifa1(k+1)                    &
L05100        &  + dtz(k)*rhoinv(k)*sd_awqnifa1(k+1)
L05101  
L05102        do k=kts+1,kte-1
L05103           a(k)=  -dtz(k)*khdz(k)*rhoinv(k)                      &
L05104           & + p5*dtz(k)*rhoinv(k)*s_aw1(k)                      &
L05105           & + p5*dtz(k)*rhoinv(k)*sd_aw1(k)
L05106           b(k)=one+dtz(k)*(khdz(k)+khdz(k+1))*rhoinv(k)         &
L05107           & + p5*dtz(k)*rhoinv(k)*(s_aw1(k)-s_aw1(k+1))         &
L05108           & + p5*dtz(k)*rhoinv(k)*(sd_aw1(k)-sd_aw1(k+1))
L05109           c(k)=  -dtz(k)*khdz(k+1)*rhoinv(k)                    &
L05110           & - p5*dtz(k)*rhoinv(k)*s_aw1(k+1)                    &
L05111           & - p5*dtz(k)*rhoinv(k)*sd_aw1(k+1)
L05112           d(k)=qnifa2(k)                                        &
L05113           & + dtz(k)*rhoinv(k)*(s_awqnifa1(k)-s_awqnifa1(k+1))  &
L05114           & - dtz(k)*rhoinv(k)*(sd_awqnifa1(k)-sd_awqnifa1(k+1))
L05115        enddo
L05116     endif
L05117     
L05118  ! prescribed value
L05119      a(kte)=zero
L05120      b(kte)=one
L05121      c(kte)=zero
L05122      d(kte)=qnifa2(kte)
L05123  
L05124  !    CALL tridiag(kte,a,b,c,d)
L05125      CALL tridiag2(kte,a,b,c,d,x)
L05126  !    CALL tridiag3(kte,a,b,c,d,x)
L05127  
L05128      DO k=kts,kte
L05129         !qnifa2(k)=d(k-kts+1)
L05130         qnifa2(k)=max(x(k),zero)
L05131      ENDDO
L05132  
L05133      !apply bounds
L05134      DO k=kts,kte
L05135         aero_min = ifa_min * exp(-zw(k)/ifa_ht)
L05136         aero_max = ifa_max * exp(-zw(k)/ifa_ht)
L05137         qnifa2(k)= min(max(aero_min, qnifa2(k)), aero_max)
L05138      ENDDO
L05139      
L05140  ELSE
L05141      !If not mixing aerosols, set "updated" array equal to original array
L05142      qnifa2=qnifa
L05143  ENDIF
L05144  
L05145  !============================================
L05146  ! Black-carbon aerosols ( qnbca ).           
L05147  !============================================
L05148  IF (FLAG_QNBCA .AND. bl_mynn_mixaerosols > 0) THEN
L05149  
L05150     if (bl_mynn_edmf > 1) then
L05151  
L05152        DO k=kts+1,kte-1
L05153           upcont(k)= s_awqnbca1(k)- s_aw1(k)*(qnbca(k)*upwind+qnbca(k-1)*(one-upwind))
L05154           dncont(k)=zero !sd_awqnbca1(k)-sd_aw1(k)*(qnbca(k)*upwind+qnbca(k-1)*(one-upwind))
L05155        ENDDO
L05156        ! no flux at the top of the atmosphere
L05157        upcont(kte)=zero
L05158        dncont(kte)=zero
L05159  
L05160        k=kts
L05161        a(1)=zero
L05162        b(1)=one + dtz(k)*khdz(k+1)*rhoinv(k)
L05163        c(1)=    - dtz(k)*khdz(k+1)*rhoinv(k)
L05164        d(1)=qnbca(k)                                       &
L05165            &    - dtz(k)*(upcont(k+1)+dncont(k+1))
L05166  
L05167        DO k=kts+1,kte-1
L05168           a(k)=   - dtz(k)*khdz(k)*rhoinv(k)
L05169           b(k)=one+ dtz(k)*(khdz(k)+khdz(k+1))*rhoinv(k)
L05170           c(k)=   - dtz(k)*khdz(k+1)*rhoinv(k)
L05171           d(k)=qnbca(k)-dtz(k)*(upcont(k+1)-upcont(k)+dncont(k+1)-dncont(k))
L05172        ENDDO
L05173  
L05174     else !implicit
L05175     
L05176        k=kts
L05177        a(k)=  -dtz(k)*khdz(k)*rhoinv(k)
L05178        b(k)=one+dtz(k)*(khdz(k) + khdz(k+1))*rhoinv(k)          &
L05179        & - p5*dtz(k)*rhoinv(k)*s_aw1(k+1)*nonloc
L05180        c(k)=  -dtz(k)*khdz(k+1)*rhoinv(k)                       &
L05181        & - p5*dtz(k)*rhoinv(k)*s_aw1(k+1)*nonloc
L05182        d(k)=qnbca(k)  - dtz(k)*rhoinv(k)*s_awqnbca1(k+1)*nonloc
L05183  
L05184        do k=kts+1,kte-1
L05185           a(k)=  -dtz(k)*khdz(k)*rhoinv(k)                      &
L05186           & + p5*dtz(k)*rhoinv(k)*s_aw1(k)*nonloc
L05187           b(k)=one+dtz(k)*(khdz(k)+khdz(k+1))*rhoinv(k)         &
L05188           & + p5*dtz(k)*rhoinv(k)*(s_aw1(k)-s_aw1(k+1))*nonloc
L05189           c(k)=  -dtz(k)*khdz(k+1)*rhoinv(k)                    &
L05190           & - p5*dtz(k)*rhoinv(k)*s_aw1(k+1)*nonloc
L05191           d(k)=qnbca(k) + dtz(k)*rhoinv(k)*(s_awqnbca1(k)-s_awqnbca1(k+1))*nonloc
L05192        enddo
L05193     endif
L05194     
L05195  ! prescribed value
L05196      a(kte)=zero
L05197      b(kte)=one
L05198      c(kte)=zero
L05199      d(kte)=qnbca(kte)
L05200  
L05201  !    CALL tridiag(kte,a,b,c,d)
L05202     CALL tridiag2(kte,a,b,c,d,x)
L05203  !    CALL tridiag3(kte,a,b,c,d,x)
L05204  
L05205      DO k=kts,kte
L05206         !qnbca2(k)=d(k-kts+1)
L05207         qnbca2(k)=max(zero, x(k))
L05208      ENDDO
L05209  
L05210  ELSE
L05211      !If not mixing aerosols, set "updated" array equal to original array
L05212      qnbca2=qnbca
L05213  ENDIF
L05214  
L05215  !============================================
L05216  ! Ozone - local mixing only
L05217  !============================================
L05218  IF (FLAG_OZONE) THEN
L05219      k=kts
L05220  
L05221  !rho-weighted:
L05222      a(k)=  -dtz(k)*khdz(k)*rhoinv(k)
L05223      b(k)=one+dtz(k)*(khdz(k+1)+khdz(k))*rhoinv(k)
L05224      c(k)=  -dtz(k)*khdz(k+1)*rhoinv(k)
L05225      d(k)=ozone(k)
L05226  
L05227      DO k=kts+1,kte-1
L05228         a(k)=  -dtz(k)*khdz(k)*rhoinv(k)
L05229         b(k)=one+dtz(k)*(khdz(k)+khdz(k+1))*rhoinv(k)
L05230         c(k)=  -dtz(k)*khdz(k+1)*rhoinv(k)
L05231         d(k)=ozone(k)
L05232      ENDDO
L05233  
L05234  ! prescribed value
L05235      a(kte)=zero
L05236      b(kte)=one
L05237      c(kte)=zero
L05238      d(kte)=ozone(kte)
L05239  
L05240  !    CALL tridiag(kte,a,b,c,d)
L05241      CALL tridiag2(kte,a,b,c,d,x)
L05242  !    CALL tridiag3(kte,a,b,c,d,x)
L05243  
L05244      DO k=kts,kte
L05245         !ozone2(k)=d(k-kts+1)
L05246         dozone(k)=(max(x(k),zero) - ozone(k))/delt
L05247      ENDDO
L05248  ELSE
L05249      dozone(:)=zero
L05250  ENDIF
```

> - **数浓度与气溶胶**（结构再次同构）：qni/qnc（`bl_mynn_mixnumcon > 0` 时）用 `nc_min=100/ni_min=1e-6` 保底（`sqi>1e-12` 时强制最小数浓度）；qnwfa/qnifa/qnbca（`bl_mynn_mixaerosols > 0`）混合后做**指数廓线钳位**：`aero_min/max = wfa_min/max·exp(−z/wfa_ht)`——气溶胶被约束在气候廓线附近（水面另加 100–300 m 高度过渡的 6e8 冷启动补丁）。`nonloc=1.0` 参数控制黑碳的非局地输运（L5179 起 implicit 分支用 `nonloc` 加权）。
> - **臭氧**：`FLAG_OZONE` 时**只做局地扩散**（无 MF 项），输出 `dozone` 倾向并做非负修复（`Dozone·delt+ozone<0` 时取 `-0.99·ozone/delt`）。

<!-- code_extract code_extract.py v1.1
source: phys/MYNN-EDMF/module_bl_mynnedmf.F90
ranges: L5252-L5496
file_lines: 8776
file_md5: ec93fee9745a3e0b25be55a61b5aff8a
display: line-numbered (strip L-prefix and !file: line to restore)
range_md5: f77f653b5d53e0393452ea8bdd8fd984
seg_lines: 245
-->

```fortran
!file: phys/MYNN-EDMF/module_bl_mynnedmf.F90    L5252-L5496
L05252  !!============================================
L05253  !! Compute tendencies and convert to mixing ratios for WRF.
L05254  !! Note that the momentum tendencies are calculated above.
L05255  !!============================================
L05256  
L05257     IF (bl_mynn_mixqt > 0) THEN 
L05258        DO k=kts,kte
L05259           !compute updated theta using updated thl and old condensate
L05260           th_new = thl(k) + xlvcp/exner(k)*sqc(k) &
L05261             &             + xlscp/exner(k)*sqi(k)
L05262  
L05263           t  = th_new*exner(k)
L05264           qsat = qsat_blend(t,p(k)) 
L05265           !SATURATED VAPOR PRESSURE
L05266           !esat=esat_blend(t)
L05267           !SATURATED SPECIFIC HUMIDITY
L05268           !qsl=ep_2*esat/(p(k)-ep_3*esat)
L05269           !qsl=ep_2*esat/max(1.e-4,(p(k)-ep_3*esat))
L05270  
L05271           IF (sqc(k) > zero .or. sqi(k) > zero) THEN !initially saturated
L05272              sqv2(k) = MIN(sqw2(k),qsat)
L05273              portion_qc = sqc(k)/(sqc(k) + sqi(k))
L05274              portion_qi = sqi(k)/(sqc(k) + sqi(k))
L05275              condensate = MAX(sqw2(k) - qsat, zero)
L05276              sqc2(k) = condensate*portion_qc
L05277              sqi2(k) = condensate*portion_qi
L05278           ELSE                     ! initially unsaturated -----
L05279              sqv2(k) = sqw2(k)     ! let microphys decide what to do
L05280              sqi2(k) = zero         ! if sqw2 > qsat 
L05281              sqc2(k) = zero
L05282           ENDIF
L05283        ENDDO
L05284     ENDIF
L05285  
L05286  
L05287      !=====================
L05288      ! WATER VAPOR TENDENCY
L05289      !=====================
L05290      DO k=kts,kte
L05291         Dqv(k)=(sqv2(k) - sqv(k))/delt
L05292         !if (sqv2(k) < zero)print*,"neg qv:",sqv2(k),k
L05293      ENDDO
L05294  
L05295      IF (bl_mynn_cloudmix > 0) THEN
L05296        !=====================
L05297        ! CLOUD WATER TENDENCY
L05298        !=====================
L05299        !print*,"FLAG_QC:",FLAG_QC
L05300        IF (FLAG_QC) THEN
L05301           DO k=kts,kte
L05302              Dqc(k)=(sqc2(k) - sqc(k))/delt
L05303              !if (sqc2(k) < zero)print*,"neg qc:",sqc2(k),k
L05304           ENDDO
L05305        ELSE
L05306           DO k=kts,kte
L05307             Dqc(k) = 0.
L05308           ENDDO
L05309        ENDIF
L05310  
L05311        !===================
L05312        ! CLOUD WATER NUM CONC TENDENCY
L05313        !===================
L05314        IF (FLAG_QNC .AND. bl_mynn_mixnumcon > 0) THEN
L05315           DO k=kts,kte
L05316             Dqnc(k) = (qnc2(k)-qnc(k))/delt
L05317             !IF(Dqnc(k)*delt + qnc(k) < 0.)Dqnc(k)=-qnc(k)/delt
L05318           ENDDO 
L05319        ELSE
L05320           DO k=kts,kte
L05321             Dqnc(k) = 0.
L05322           ENDDO
L05323        ENDIF
L05324  
L05325        !===================
L05326        ! CLOUD ICE TENDENCY
L05327        !===================
L05328        IF (FLAG_QI) THEN
L05329           DO k=kts,kte
L05330             Dqi(k)=(sqi2(k) - sqi(k))/delt
L05331             !if (sqi2(k) < zero)print*,"neg qi:",sqi2(k),k
L05332           ENDDO
L05333        ELSE
L05334           DO k=kts,kte
L05335             Dqi(k) = 0.
L05336           ENDDO
L05337        ENDIF
L05338  
L05339        !===================
L05340        ! CLOUD SNOW TENDENCY
L05341        !===================
L05342        IF (.false.) THEN !disabled
L05343           DO k=kts,kte
L05344             Dqs(k)=(sqs2(k) - sqs(k))/delt
L05345           ENDDO
L05346        ELSE
L05347           DO k=kts,kte
L05348             Dqs(k) = 0.
L05349           ENDDO
L05350        ENDIF
L05351  
L05352        !===================
L05353        ! CLOUD ICE NUM CONC TENDENCY
L05354        !===================
L05355        IF (FLAG_QNI .AND. bl_mynn_mixnumcon > 0) THEN
L05356           DO k=kts,kte
L05357             Dqni(k)=(qni2(k)-qni(k))/delt
L05358             !IF(Dqni(k)*delt + qni(k) < 0.)Dqni(k)=-qni(k)/delt
L05359           ENDDO
L05360        ELSE
L05361           DO k=kts,kte
L05362             Dqni(k)=0.
L05363           ENDDO
L05364        ENDIF
L05365      ELSE !-MIX CLOUD SPECIES?
L05366        !CLOUDS ARE NOT NIXED (when bl_mynn_cloudmix == 0)
L05367        DO k=kts,kte
L05368           Dqc(k) =0.
L05369           Dqnc(k)=0.
L05370           Dqi(k) =0.
L05371           Dqni(k)=0.
L05372           Dqs(k) =0.
L05373        ENDDO
L05374      ENDIF
L05375  
L05376      !ensure non-negative moist species
L05377      CALL moisture_check(kte, delt, delp, exner,        &
L05378                          sqv2, sqc2, sqi2, sqs2, thl,   &
L05379                          dqv, dqc, dqi, dqs, dth        )
L05380  
L05381      !=====================
L05382      ! OZONE TENDENCY CHECK
L05383      !=====================
L05384      DO k=kts,kte
L05385         IF(Dozone(k)*delt + ozone(k) < 0.) THEN
L05386           Dozone(k)=-ozone(k)*0.99/delt
L05387         ENDIF
L05388      ENDDO
L05389  
L05390      !===================
L05391      ! THETA TENDENCY
L05392      !===================
L05393      IF (FLAG_QI) THEN
L05394        DO k=kts,kte
L05395           Dth(k)=(thl(k) + xlvcp/exner(k)*sqc(k)          &
L05396             &            + xlscp/exner(k)*(sqi(k))        & !+sqs2(k)) &
L05397             &            - th(k))/delt
L05398           !Dth(k)=(thl(k) + xlvcp/exner(k)*qc_tot1(k)       &
L05399           !  &            + xlscp/exner(k)*qi_tot1(k)       &
L05400           !  &            - th(k))/delt
L05401           !Use form from Tripoli and Cotton (1981) with their
L05402           !suggested min temperature to improve accuracy:
L05403           !Dth(k)=(thl(k)*(one+xlvcp/MAX(tk(k),TKmin)*sqc(k)  &
L05404           !  &               + xlscp/MAX(tk(k),TKmin)*sqi(k)) &
L05405           !  &               - th(k))/delt
L05406        ENDDO
L05407      ELSE
L05408        DO k=kts,kte
L05409           Dth(k)=(thl(k)+xlvcp/exner(k)*sqc2(k) - th(k))/delt
L05410           !Use form from Tripoli and Cotton (1981) with their
L05411           !suggested min temperature to improve accuracy.
L05412           !Dth(k)=(thl(k)*(one+xlvcp/MAX(tk(k),TKmin)*sqc(k))  &
L05413           !&               - th(k))/delt
L05414        ENDDO
L05415      ENDIF
L05416  
L05417      !===================
L05418      ! AEROSOL TENDENCIES
L05419      !===================
L05420      IF (FLAG_QNWFA .AND. FLAG_QNIFA .AND. &
L05421          bl_mynn_mixaerosols > 0) THEN
L05422         DO k=kts,kte
L05423            !=====================
L05424            ! WATER-friendly aerosols
L05425            !=====================
L05426            Dqnwfa(k)=(qnwfa2(k) - qnwfa(k))/delt
L05427            !=====================
L05428            ! Ice-friendly aerosols
L05429            !=====================
L05430            Dqnifa(k)=(qnifa2(k) - qnifa(k))/delt
L05431         ENDDO
L05432      ELSE
L05433         DO k=kts,kte
L05434            Dqnwfa(k)=0.
L05435            Dqnifa(k)=0.
L05436         ENDDO
L05437      ENDIF
L05438  
L05439      !========================
L05440      ! BLACK-CARBON TENDENCIES
L05441      !========================
L05442      IF (FLAG_QNBCA .AND. bl_mynn_mixaerosols > 0) THEN
L05443         DO k=kts,kte
L05444            Dqnbca(k)=(qnbca2(k) - qnbca(k))/delt
L05445         ENDDO
L05446      ELSE
L05447         DO k=kts,kte
L05448            Dqnbca(k)=0.
L05449         ENDDO
L05450      ENDIF
L05451  
L05452      !ensure non-negative moist species
L05453      !note: if called down here, dth needs to be updated, but
L05454      !      if called before the theta-tendency calculation, do not compute dth
L05455      !CALL moisture_check(kte, delt, delp, exner,     &
L05456      !                    sqv, sqc, sqi, thl,         &
L05457      !                    dqv, dqc, dqi, dth )
L05458  
L05459      if (debug_code) then
L05460         problem = .false.
L05461         do k=kts,kte
L05462            wsp  = sqrt(u(k)**2 + v(k)**2)
L05463            wsp2 = sqrt((u(k)+du(k)*delt)**2 + (v(k)+du(k)*delt)**2)
L05464            th2  = th(k) + Dth(k)*delt
L05465            tk2  = th2*exner(k)
L05466            if (wsp2 > 200. .or. tk2 > 360. .or. tk2 < 160.) then
L05467               problem = .true.
L05468               print*,"After tendencies problem at: i=",i," k=",k
L05469               print*," wsp=",wsp," updated wsp=",wsp2
L05470               print*," T=",th(k)*exner(k)," updated T:",tk2
L05471               print*," du=",du(k)*delt," dv=",dv(k)*delt," dth=",dth(k)*delt
L05472               print*," km=",kmdz(k)*dz(k)," kh=",khdz(k)*dz(k)
L05473               print*," u*=",ust," wspd=",wspd
L05474               print*," rhosfc=",rhosfc," delp=",delp(k)
L05475               print*," LH=",flq*rhosfc*1004.," HFX=",flt*rhosfc*1004.
L05476               print*," flq=",flq," flt=",flt," exner=",exner(k)
L05477               print*," drag term=",ust**2/wspd*dtz(k)*rhosfc/rho(kts)
L05478               kproblem = k
L05479            endif
L05480         enddo
L05481         if (problem) then
L05482            print*,"==thl:",thl(max(kproblem-3,1):min(kproblem+3,kte))
L05483            print*,"===qv:",sqv2(max(kproblem-3,1):min(kproblem+3,kte))
L05484            print*,"===qc:",sqc2(max(kproblem-3,1):min(kproblem+3,kte))
L05485            print*,"===qi:",sqi2(max(kproblem-3,1):min(kproblem+3,kte))
L05486            print*,"====u:",u(max(kproblem-3,1):min(kproblem+3,kte))
L05487            print*,"====v:",v(max(kproblem-3,1):min(kproblem+3,kte))
L05488         endif
L05489      endif
L05490  
L05491  #ifdef HARDCODE_VERTICAL
L05492  # undef kts
L05493  # undef kte
L05494  #endif
L05495  
L05496    END SUBROUTINE mynn_tendencies
```

> - **总水拆分**（mixqt>0，L5257–L5284）：先用旧凝结量重建 `th_new` 与 `qsat`；**初始饱和**的层：`sqv2 = min(sqw2, qsat)`，凝结增量 `condensate = max(sqw2−qsat, 0)` 按旧 qc/qi 份额分给 sqc2/sqi2——**凝结产物按相态比例继承**；**初始未饱和**：全部给 sqv2（注释 “let microphys decide”——微物理层处理饱和）。
> - **倾向输出**：全部 `(新−旧)/delt`；`moisture_check` 统一修复负值（下节）；θ 趋势由 `thl + xlvcp/ex·sqc + xlscp/ex·sqi − th` 重建（**液水位温还原成位温**，FLAG_QI 时用旧凝结量、否则用新 sqc2——两个分支对应“冰是否参与”的口径差）。
> - **出口体检**（debug_code）：更新后风速>200 m/s 或温度出 [160,360] K 打印完整诊断（含拖曳项、通量、km/kh）。

## 09b.2 `moisture_check`：负值修复与柱水量守恒

<!-- code_extract code_extract.py v1.1
source: phys/MYNN-EDMF/module_bl_mynnedmf.F90
ranges: L5499-L5588
file_lines: 8776
file_md5: ec93fee9745a3e0b25be55a61b5aff8a
display: line-numbered (strip L-prefix and !file: line to restore)
range_md5: 40c23403c31557d5e8427c10b924e972
seg_lines: 90
-->

```fortran
!file: phys/MYNN-EDMF/module_bl_mynnedmf.F90    L5499-L5588
L05499    SUBROUTINE moisture_check(kte, delt, dp, exner,   &
L05500                              qv, qc, qi, qs, th,     &
L05501                              dqv, dqc, dqi, dqs, dth )
L05502  
L05503    ! This subroutine was adopted from the CAM-UW ShCu scheme and 
L05504    ! adapted for use here.
L05505    !
L05506    ! If qc < qcmin, qi < qimin, or qv < qvmin happens in any layer,
L05507    ! force them to be larger than minimum value by (1) condensating 
L05508    ! water vapor into liquid or ice, and (2) by transporting water vapor 
L05509    ! from the very lower layer.
L05510    ! 
L05511    ! We then update the final state variables and tendencies associated
L05512    ! with this correction. If any condensation happens, update theta too.
L05513    ! Note that (qv,qc,qi,th) are the final state variables after
L05514    ! applying corresponding input tendencies and corrective tendencies.
L05515      use module_bl_mynnedmf_common, only: xlvcp,xlscp,zero,two,p5,kind_phys
L05516      
L05517      implicit none
L05518      integer,         intent(in)     :: kte
L05519      real(kind_phys), intent(in)     :: delt
L05520      real(kind_phys), dimension(kte), intent(in)     :: dp, exner
L05521      real(kind_phys), dimension(kte), intent(inout)  :: qv, qc, qi, qs, th
L05522      real(kind_phys), dimension(kte), intent(inout)  :: dqv, dqc, dqi, dqs, dth
L05523      integer:: k
L05524      real(kind_phys)::  dqc2, dqi2, dqs2, dqv2, sum, aa, dum
L05525      real(kind_phys), parameter :: qvmin = 1e-20,       &
L05526                                    qcmin = zero,         &
L05527                                    qimin = zero
L05528  
L05529      do k = kte, 1, -1  ! From the top to the surface
L05530         dqc2 = max(zero, qcmin-qc(k)) !qc deficit (>=0)
L05531         dqi2 = max(zero, qimin-qi(k)) !qi deficit (>=0)
L05532         dqs2 = max(zero, qimin-qs(k)) !qs deficit (>=0)
L05533  
L05534         !fix tendencies
L05535         dqc(k) = dqc(k) +  dqc2/delt
L05536         dqi(k) = dqi(k) +  dqi2/delt
L05537         dqs(k) = dqs(k) +  dqs2/delt
L05538         dqv(k) = dqv(k) - (dqc2+dqi2+dqs2)/delt
L05539         dth(k) = dth(k) + xlvcp/exner(k)*(dqc2/delt) + &
L05540                           xlscp/exner(k)*((dqi2+dqs2)/delt)
L05541         !update species
L05542         qc(k)  = qc(k)  +  dqc2
L05543         qi(k)  = qi(k)  +  dqi2
L05544         qs(k)  = qs(k)  +  dqs2
L05545         qv(k)  = qv(k)  -  dqc2 - dqi2 - dqs2
L05546         th(k)  = th(k)  +  xlvcp/exner(k)*dqc2 + &
L05547                            xlscp/exner(k)*(dqi2+dqs2)
L05548  
L05549         !then fix qv
L05550         dqv2   = max(zero, qvmin-qv(k)) !qv deficit (>=0)
L05551         dqv(k) = dqv(k) + dqv2/delt
L05552         qv(k)  = qv(k)  + dqv2
L05553         if ( k .ne. 1 ) then
L05554            !print*,k,"dqv2=",dqv2," dp(k)/dp(k-1)=",dp(k)/dp(k-1)
L05555            qv(k-1)   = qv(k-1)  - dqv2*dp(k)/dp(k-1)
L05556            dqv(k-1)  = dqv(k-1) - dqv2*dp(k)/dp(k-1)/delt
L05557         endif
L05558         qv(k) = max(qv(k),qvmin)
L05559         qc(k) = max(qc(k),qcmin)
L05560         qi(k) = max(qi(k),qimin)
L05561         qs(k) = max(qs(k),qimin)
L05562      end do
L05563      ! Extra moisture used to satisfy 'qv(1)>=qvmin' is proportionally
L05564      ! extracted from all the layers that has 'qv > 2*qvmin'. This fully
L05565      ! preserves column moisture.
L05566      if( dqv2 .gt. 1.e-20 ) then
L05567          sum = zero
L05568          do k = 1, kte
L05569             if( qv(k) .gt. two*qvmin ) sum = sum + qv(k)*dp(k)
L05570          enddo
L05571          aa = dqv2*dp(1)/max(1.e-20_kind_phys,sum)
L05572          if( aa .lt. p5 ) then
L05573              do k = 1, kte
L05574                 if( qv(k) .gt. two*qvmin ) then
L05575                     dum    = aa*qv(k)
L05576                     qv(k)  = qv(k) - dum
L05577                     dqv(k) = dqv(k) - dum/delt
L05578                 endif
L05579              enddo
L05580          else
L05581          ! For testing purposes only (not yet found in any output):
L05582          !    write(*,*) 'Full moisture conservation is impossible'
L05583          endif
L05584      endif
L05585  
L05586      return
L05587  
L05588    END SUBROUTINE moisture_check
```

> - **来源**：CAM-UW ShCu 方案移植（头注释）。**自顶向下**扫描（`do k = kte, 1, -1`）：凝结物亏空（qc/qi/qs < 0）先由同层水汽**凝结**补足（`dqv −= 缺量`、`dth += 潜热`），水汽亏空再从**下一层抽取**（`qv(k−1) −= dqv2·dp(k)/dp(k−1)`——按气压厚度加权）。
> - **柱守恒兜底**（L5563–L5584）：最底层为满足 `qv≥1e-20` 额外用的水分，按 `qv·dp` 比例从全柱 `qv > 2·qvmin` 的层**等比回收**——注释自承“完全保持柱水量”。`aa < 0.5` 的保护（回收比例不许超 50%）。
> - **与 Thompson 的守恒段对照**：微物理用“等比例缩放源汇”，边界层用“逐层借贷+柱回收”——两个方案面对同一问题（负水汽）的不同解法，教材 ch13 §13.7.5 与本节可对读。

## 09b.3 `mynn_mix_chem` / `mynn_mix_scalars`：化学与标量的边界层混合

<!-- code_extract code_extract.py v1.1
source: phys/MYNN-EDMF/module_bl_mynnedmf.F90
ranges: L5592-L5751
file_lines: 8776
file_md5: ec93fee9745a3e0b25be55a61b5aff8a
display: line-numbered (strip L-prefix and !file: line to restore)
range_md5: 4591187c6f9986fc2957daefc5298e6d
seg_lines: 160
-->

```fortran
!file: phys/MYNN-EDMF/module_bl_mynnedmf.F90    L5592-L5751
L05592  SUBROUTINE mynn_mix_chem(kts,kte,i,     &
L05593       delt,dz,pblh,                      &
L05594       nchem, ndvel,                      &
L05595       chem1, vd1, settle1,               &
L05596       rho,                               &
L05597       flt, tcd, qcd,                     &
L05598       dfh,                               &
L05599       s_aw1, s_awchem1,                  &
L05600       emis_ant_no, frp,                  &
L05601       enh_mix,                           &
L05602       bl_mynn_edmf, upwind               )
L05603  
L05604  !-------------------------------------------------------------------
L05605    use module_bl_mynnedmf_common, only: zero,one,two,p5,kind_phys
L05606    
L05607  integer, intent(in) :: kts,kte,i,bl_mynn_edmf
L05608  real(kind_phys), dimension(kts:kte), intent(in) :: dfh,dz,tcd,qcd
L05609  real(kind_phys), dimension(kts:kte), intent(in) :: rho
L05610  real(kind_phys), intent(in)    :: flt
L05611  real(kind_phys), intent(in)    :: delt,pblh,upwind
L05612  integer, intent(in) :: nchem, ndvel
L05613  real(kind_phys), dimension( kts:kte+1), intent(in) :: s_aw1
L05614  real(kind_phys), dimension( kts:kte, nchem ), intent(inout) :: chem1
L05615  real(kind_phys), dimension( kts:kte, nchem ), intent(in) :: settle1
L05616  real(kind_phys), dimension( kts:kte+1,nchem), intent(in) :: s_awchem1
L05617  real(kind_phys), dimension( ndvel ), intent(in) :: vd1
L05618  real(kind_phys), intent(in) :: emis_ant_no,frp
L05619  logical, intent(in) :: enh_mix
L05620  !local vars
L05621  real(kind_phys), dimension(kts:kte) :: dtz,upcont,dncont
L05622  real(kind_phys), dimension(kts:kte) :: a,b,c,d,x
L05623  real(kind_phys):: rhs,dztop
L05624  real(kind_phys):: t,dzk
L05625  real(kind_phys):: hght 
L05626  real(kind_phys):: khdz_old, khdz_back
L05627  integer :: k,kk,kmaxfire                         ! JLS 12/21/21
L05628  integer :: ic  ! Chemical array loop index
L05629      
L05630  integer, SAVE :: icall
L05631  
L05632  real(kind_phys), dimension(kts:kte) :: rhoinv
L05633  real(kind_phys), dimension(kts:kte+1) :: rhoz,khdz
L05634  real(kind_phys), parameter :: NO_threshold    = 0.1      ! For anthropogenic sources
L05635  real(kind_phys), parameter :: frp_threshold   = 10.0     ! RAR 02/11/22: I increased the frp threshold to enhance mixing over big fires
L05636  real(kind_phys), parameter :: pblh_threshold  = 100.0
L05637  
L05638  dztop=.5*(dz(kte)+dz(kte-1))
L05639  
L05640  DO k=kts,kte
L05641     dtz(k)=delt/dz(k)
L05642  ENDDO
L05643  
L05644  !Prepare "constants" for diffusion equation.
L05645  !khdz = rho*Kh/dz = rho*dfh
L05646  rhoz(kts)  =rho(kts)
L05647  rhoinv(kts)=one/rho(kts)
L05648  khdz(kts)  =rhoz(kts)*dfh(kts)
L05649  
L05650  DO k=kts+1,kte
L05651     rhoz(k)  =(rho(k)*dz(k-1) + rho(k-1)*dz(k))/(dz(k-1)+dz(k))
L05652     rhoz(k)  =  MAX(rhoz(k),1E-4_kind_phys)
L05653     rhoinv(k)=one/MAX(rho(k),1E-4_kind_phys)
L05654     dzk      = p5  *( dz(k)+dz(k-1) )
L05655     khdz(k)  = rhoz(k)*dfh(k)
L05656  ENDDO
L05657  rhoz(kte+1)=rhoz(kte)
L05658  khdz(kte+1)=rhoz(kte+1)*dfh(kte)
L05659  
L05660  if (bl_mynn_edmf == 1) then
L05661     !stability criteria for mf
L05662     DO k=kts+1,kte-1
L05663        khdz(k) = MAX(khdz(k),  p5*s_aw1(k))
L05664        khdz(k) = MAX(khdz(k), -p5*(s_aw1(k)-s_aw1(k+1)))
L05665     ENDDO
L05666  endif
L05667  
L05668  !Enhanced mixing over fires
L05669  IF ( enh_mix ) THEN
L05670     DO k=kts+1,kte-1
L05671        khdz_old  = khdz(k)
L05672        khdz_back = pblh * 0.15_kind_phys / dz(k)
L05673        !Modify based on anthropogenic emissions of NO and FRP
L05674        IF ( pblh < pblh_threshold ) THEN
L05675           IF ( emis_ant_no > NO_threshold ) THEN
L05676              khdz(k) = MAX(1.1*khdz(k),sqrt((emis_ant_no / NO_threshold)) / dz(k) * rhoz(k)) ! JLS 12/21/21
L05677  !            khdz(k) = MAX(khdz(k),khdz_back)
L05678           ENDIF
L05679           IF ( frp > frp_threshold ) THEN
L05680              kmaxfire = ceiling(log(frp))
L05681              khdz(k) = MAX(1.1*khdz(k), (one - k/(kmaxfire*two)) * ((log(frp))**2 - two*log(frp)) / dz(k)*rhoz(k)) ! JLS 12/21/21
L05682  !            khdz(k) = MAX(khdz(k),khdz_back)
L05683           ENDIF
L05684        ENDIF
L05685     ENDDO
L05686  ENDIF
L05687  
L05688  !============================================
L05689  ! Patterned after mixing of water vapor in mynn_tendencies.
L05690  !============================================
L05691  
L05692  DO ic = 1,nchem
L05693  
L05694     if (bl_mynn_edmf > 1) then
L05695  
L05696        DO k=kts+1,kte-1
L05697           upcont(k)= s_awchem1(k,ic)- s_aw1(k)*(chem1(k,ic)*upwind+chem1(k-1,ic)*(one-upwind))
L05698           dncont(k)= zero !sd_awchem1(k,ic)-sd_aw1(k)*(chem1(k,ic)*upwind+chem1(k-1,ic)*(one-upwind))
L05699        ENDDO
L05700        ! no flux at the top of the atmosphere
L05701        upcont(kte)=zero
L05702        dncont(kte)=zero
L05703  
L05704        k=kts
L05705        a(1)=zero
L05706        b(1)=one + dtz(k)*khdz(k+1)*rhoinv(k)
L05707        c(1)=    - dtz(k)*khdz(k+1)*rhoinv(k)
L05708        d(1)=chem1(k,ic)                                       &
L05709            &    - dtz(k)*(upcont(k+1)+dncont(k+1))
L05710  
L05711        DO k=kts+1,kte-1
L05712           a(k)=   - dtz(k)*khdz(k)*rhoinv(k)
L05713           b(k)=one+ dtz(k)*(khdz(k)+khdz(k+1))*rhoinv(k)
L05714           c(k)=   - dtz(k)*khdz(k+1)*rhoinv(k)
L05715           d(k)=chem1(k,ic)-dtz(k)*(upcont(k+1)-upcont(k)+dncont(k+1)-dncont(k))
L05716        ENDDO
L05717  
L05718     else !implicit
L05719        
L05720        k=kts
L05721        a(k)=   -dtz(k)*khdz(k)*rhoinv(k)
L05722        b(k)=one+dtz(k)*(khdz(k+1)+khdz(k))*rhoinv(k) - p5*dtz(k)*rhoinv(k)*s_aw1(k+1)
L05723        c(k)=   -dtz(k)*khdz(k+1)*rhoinv(k)           - p5*dtz(k)*rhoinv(k)*s_aw1(k+1)
L05724        d(k)=chem1(k,ic) & !dtz(k)*flt  !neglecting surface sources 
L05725             & - dtz(k)*vd1(ic)*chem1(k,ic) &
L05726             & - dtz(k)*rhoinv(k)*s_awchem1(k+1,ic)
L05727  
L05728        DO k=kts+1,kte-1
L05729           a(k)=   -dtz(k)*khdz(k)*rhoinv(k)     + p5*dtz(k)*rhoinv(k)*s_aw1(k)
L05730           b(k)=one+dtz(k)*(khdz(k)+khdz(k+1))*rhoinv(k) + &
L05731              &    p5*dtz(k)*rhoinv(k)*(s_aw1(k)-s_aw1(k+1))
L05732           c(k)=   -dtz(k)*khdz(k+1)*rhoinv(k) - p5*dtz(k)*rhoinv(k)*s_aw1(k+1)
L05733           d(k)=chem1(k,ic) + dtz(k)*rhoinv(k)*(s_awchem1(k,ic)-s_awchem1(k+1,ic))
L05734        ENDDO
L05735     endif
L05736  
L05737     ! prescribed value at top
L05738     a(kte)=zero
L05739     b(kte)=one
L05740     c(kte)=zero
L05741     d(kte)=chem1(kte,ic)
L05742  
L05743     CALL tridiag3(kte,a,b,c,d,x)
L05744  
L05745     DO k=kts,kte
L05746        chem1(k,ic)=x(k) + settle1(k,ic)
L05747     ENDDO
L05748  
L05749  ENDDO
L05750  
L05751  END SUBROUTINE mynn_mix_chem
```

> - **火点增强混合**（`enh_mix`，L5668–L5686）：PBLH<100 m 且（人为 NO 排放>0.1 或火辐射功率 FRP>10）时，`khdz` 强制放大——NO 按根号排放比放大、FRP 按**对数剖面**（`kmaxfire = ceil(log(frp))`，高度衰减 `(1−k/(2·kmaxfire))·((ln FRP)²−2·ln FRP)`）——**烟羽抬升的参数化替代**（JLS 12/21/21 注释）。
> - **沉降**：隐式分支右端 `−dtz·vd1(ic)·chem1`（干沉降速度一阶衰减）；解出后加 `settle1(k,ic)`（重力沉降倾向）。
> - 求解用 **tridiag3**（区别于倾向主环的 tridiag2——见 §09b.6 的语义差异）。

<!-- code_extract code_extract.py v1.1
source: phys/MYNN-EDMF/module_bl_mynnedmf.F90
ranges: L5755-L5877
file_lines: 8776
file_md5: ec93fee9745a3e0b25be55a61b5aff8a
display: line-numbered (strip L-prefix and !file: line to restore)
range_md5: bf54d7547e02b7b5c2cb2a0ea69800ad
seg_lines: 123
-->

```fortran
!file: phys/MYNN-EDMF/module_bl_mynnedmf.F90    L5755-L5877
L05755  SUBROUTINE mynn_mix_scalars(            &
L05756       kts,kte,i,                         &
L05757       delt,dz,                           &
L05758       nscalars, scalars,                 &
L05759       rho,                               &
L05760       flt, tcd, qcd,                     &
L05761       dfh,                               &
L05762       s_aw1, s_awscalars1,               &
L05763       bl_mynn_edmf, upwind               )
L05764  
L05765  !-------------------------------------------------------------------
L05766    use module_bl_mynnedmf_common, only: zero,one,p5,kind_phys
L05767    
L05768  integer, intent(in) :: kts,kte,i,bl_mynn_edmf
L05769  real(kind_phys), dimension(kts:kte), intent(in) :: dfh,dz,tcd,qcd
L05770  real(kind_phys), dimension(kts:kte), intent(in) :: rho
L05771  real(kind_phys), intent(in)    :: flt
L05772  real(kind_phys), intent(in)    :: delt,upwind
L05773  integer, intent(in) :: nscalars
L05774  real(kind_phys), dimension( kts:kte+1), intent(in) :: s_aw1
L05775  real(kind_phys), dimension( kts:kte, nscalars ), intent(inout) :: scalars
L05776  real(kind_phys), dimension( kts:kte+1,nscalars), intent(in) :: s_awscalars1
L05777  !local vars
L05778  real(kind_phys), dimension(kts:kte) :: dtz,upcont,dncont
L05779  real(kind_phys), dimension(kts:kte) :: a,b,c,d,x
L05780  real(kind_phys):: rhs,dztop
L05781  real(kind_phys):: dzk 
L05782  integer :: k,ns  !loop indecies
L05783  
L05784  real(kind_phys), dimension(kts:kte) :: rhoinv
L05785  real(kind_phys), dimension(kts:kte+1) :: rhoz,khdz
L05786  
L05787  dztop=p5*(dz(kte)+dz(kte-1))
L05788      
L05789  DO k=kts,kte
L05790     dtz(k)=delt/dz(k)
L05791  ENDDO
L05792  
L05793  !Prepare "constants" for diffusion equation.
L05794  !khdz = rho*Kh/dz = rho*dfh
L05795  rhoz(kts)  =rho(kts)
L05796  rhoinv(kts)=one/rho(kts)
L05797  khdz(kts)  =rhoz(kts)*dfh(kts)
L05798  
L05799  DO k=kts+1,kte
L05800     rhoz(k)  =(rho(k)*dz(k-1) + rho(k-1)*dz(k))/(dz(k-1)+dz(k))
L05801     rhoz(k)  =   MAX(rhoz(k),1E-4_kind_phys)
L05802     rhoinv(k)=one/MAX(rho(k),1E-4_kind_phys)
L05803     dzk      = p5*( dz(k)+dz(k-1) )
L05804     khdz(k)  = rhoz(k)*dfh(k)
L05805  ENDDO
L05806  rhoz(kte+1)=rhoz(kte)
L05807  khdz(kte+1)=rhoz(kte+1)*dfh(kte)
L05808  
L05809  if (bl_mynn_edmf == 1) then
L05810     !stability criteria for mf
L05811     DO k=kts+1,kte-1
L05812        khdz(k) = MAX(khdz(k),  p5*s_aw1(k))
L05813        khdz(k) = MAX(khdz(k), -p5*(s_aw1(k)-s_aw1(k+1)))
L05814     ENDDO
L05815  endif
L05816  
L05817  !============================================
L05818  ! Patterned after mixing of water vapor in mynn_tendencies.
L05819  !============================================
L05820  
L05821  DO ns = 1,nscalars
L05822  
L05823     if (bl_mynn_edmf > 1) then
L05824  
L05825        DO k=kts+1,kte-1
L05826           upcont(k)= s_awscalars1(k,ns)- s_aw1(k)*(scalars(k,ns)*upwind+scalars(k-1,ns)*(one-upwind))
L05827           dncont(k)=zero !sd_awscalars1(k,ns)-sd_aw1(k)*(scalars(k,ns)*upwind+scalars(k-1,ns)*(one-upwind))
L05828        ENDDO
L05829        ! no flux at the top of the atmosphere
L05830        upcont(kte)=zero
L05831        dncont(kte)=zero
L05832  
L05833        k=kts
L05834        a(1)=zero
L05835        b(1)=one + dtz(k)*khdz(k+1)*rhoinv(k)
L05836        c(1)=    - dtz(k)*khdz(k+1)*rhoinv(k)
L05837        d(1)=scalars(k,ns)                                       &
L05838            &    - dtz(k)*(upcont(k+1)+dncont(k+1))
L05839  
L05840        DO k=kts+1,kte-1
L05841           a(k)=   - dtz(k)*khdz(k)*rhoinv(k)
L05842           b(k)=one+ dtz(k)*(khdz(k)+khdz(k+1))*rhoinv(k)
L05843           c(k)=   - dtz(k)*khdz(k+1)*rhoinv(k)
L05844           d(k)=scalars(k,ns)-dtz(k)*(upcont(k+1)-upcont(k)+dncont(k+1)-dncont(k))
L05845        ENDDO
L05846  
L05847     else !implicit 
L05848  
L05849        k=kts
L05850        a(k)=   -dtz(k)*khdz(k)*rhoinv(k)
L05851        b(k)=one+dtz(k)*(khdz(k+1)+khdz(k))*rhoinv(k) - p5*dtz(k)*rhoinv(k)*s_aw1(k+1)
L05852        c(k)=   -dtz(k)*khdz(k+1)*rhoinv(k)           - p5*dtz(k)*rhoinv(k)*s_aw1(k+1)
L05853        d(k)=scalars(k,ns) - dtz(k)*rhoinv(k)*s_awscalars1(k+1,ns)
L05854  
L05855        DO k=kts+1,kte-1
L05856           a(k)=   -dtz(k)*khdz(k)*rhoinv(k)     + p5*dtz(k)*rhoinv(k)*s_aw1(k)
L05857           b(k)=one+dtz(k)*(khdz(k)+khdz(k+1))*rhoinv(k) + &
L05858               &    p5*dtz(k)*rhoinv(k)*(s_aw1(k)-s_aw1(k+1))
L05859           c(k)=   -dtz(k)*khdz(k+1)*rhoinv(k) - p5*dtz(k)*rhoinv(k)*s_aw1(k+1)
L05860           d(k)=scalars(k,ns) + dtz(k)*rhoinv(k)*(s_awscalars1(k,ns)-s_awscalars1(k+1,ns))
L05861        ENDDO
L05862     endif
L05863  
L05864     ! prescribed value at top
L05865     a(kte)=zero
L05866     b(kte)=one
L05867     c(kte)=zero
L05868     d(kte)=scalars(kte,ns)
L05869  
L05870     CALL tridiag3(kte,a,b,c,d,x)
L05871  
L05872     DO k=kts,kte
L05873        scalars(k,ns)=max(1e-12_kind_phys, x(k))
L05874     ENDDO
L05875  ENDDO
L05876  
L05877  END SUBROUTINE mynn_mix_scalars
```

> `mynn_mix_scalars` 与 mix_chem 完全同构（无沉降/火点项），`scalars` 数组按 `nscalars` 维循环——**通用标量的接入通道**。

## 09b.4 `retrieve_exchange_coeffs` 与三对角求解器三兄弟

<!-- code_extract code_extract.py v1.1
source: phys/MYNN-EDMF/module_bl_mynnedmf.F90
ranges: L5881-L5907
file_lines: 8776
file_md5: ec93fee9745a3e0b25be55a61b5aff8a
display: line-numbered (strip L-prefix and !file: line to restore)
range_md5: e47675d5eb26d2969a421239d5d9389d
seg_lines: 27
-->

```fortran
!file: phys/MYNN-EDMF/module_bl_mynnedmf.F90    L5881-L5907
L05881    SUBROUTINE retrieve_exchange_coeffs(kts,kte,dfm,dfh,dz,km1,kh1)
L05882  
L05883  !-------------------------------------------------------------------
L05884      use module_bl_mynnedmf_common, only: zero,p5,kind_phys
L05885      
L05886      integer , intent(in) :: kts,kte
L05887  
L05888      real(kind_phys), dimension(kts:kte), intent(in)  :: dz,dfm,dfh
L05889      real(kind_phys), dimension(kts:kte), intent(out) :: km1, kh1
L05890  
L05891  
L05892      integer :: k
L05893      real(kind_phys):: dzk
L05894  
L05895      km1(kts)=zero
L05896      kh1(kts)=zero
L05897  
L05898      do k=kts+1,kte
L05899         dzk   = p5 *( dz(k)+dz(k-1) )
L05900         km1(k)=dfm(k)*dzk
L05901         kh1(k)=dfh(k)*dzk
L05902      enddo
L05903  
L05904  !    km1(kte+1)=0.
L05905  !    kh1(kte+1)=0.
L05906  
L05907    END SUBROUTINE retrieve_exchange_coeffs
```

> `km1 = dfm·dzk`、`kh1 = dfh·dzk`——把“除以 dz”的扩散系数还原成真实量纲（m²/s）输出给 driver/历史。底层零（表面层用相似律另行处理）。

<!-- code_extract code_extract.py v1.1
source: phys/MYNN-EDMF/module_bl_mynnedmf.F90
ranges: L5911-L5943
file_lines: 8776
file_md5: ec93fee9745a3e0b25be55a61b5aff8a
display: line-numbered (strip L-prefix and !file: line to restore)
range_md5: 82562aa62c52ac5452ca3fa90928cdd1
seg_lines: 33
-->

```fortran
!file: phys/MYNN-EDMF/module_bl_mynnedmf.F90    L5911-L5943
L05911    SUBROUTINE tridiag(n,a,b,c,d)
L05912  
L05913  !! to solve system of linear eqs on tridiagonal matrix n times n
L05914  !! after Peaceman and Rachford, 1955
L05915  !! a,b,c,d - are vectors of order n 
L05916  !! a,b,c - are coefficients on the LHS
L05917  !! d - is initially RHS on the output becomes a solution vector
L05918  !-------------------------------------------------------------------
L05919      use module_bl_mynnedmf_common, only: zero,one,kind_phys
L05920      
L05921      integer, intent(in):: n
L05922      real(kind_phys), dimension(n), intent(in) :: a,b
L05923      real(kind_phys), dimension(n), intent(inout) :: c,d
L05924      
L05925      integer :: i
L05926      real(kind_phys):: p
L05927      real(kind_phys), dimension(n) :: q
L05928      
L05929      c(n)=zero
L05930      q(1)=-c(1)/b(1)
L05931      d(1)=d(1)/b(1)
L05932      
L05933      DO i=2,n
L05934         p=one/(b(i)+a(i)*q(i-1))
L05935         q(i)=-c(i)*p
L05936         d(i)=(d(i)-a(i)*d(i-1))*p
L05937      ENDDO
L05938      
L05939      DO i=n-1,1,-1
L05940         d(i)=d(i)+q(i)*d(i+1)
L05941      ENDDO
L05942  
L05943    END SUBROUTINE tridiag
```

> **tridiag**：Peaceman & Rachford (1955) 经典追赶法——**就地覆盖 d**（输入右端、输出解向量，c/d 声明 inout）。`q` 数组存消元系数。

<!-- code_extract code_extract.py v1.1
source: phys/MYNN-EDMF/module_bl_mynnedmf.F90
ranges: L5947-L5980
file_lines: 8776
file_md5: ec93fee9745a3e0b25be55a61b5aff8a
display: line-numbered (strip L-prefix and !file: line to restore)
range_md5: 79dfcf1f3751f37adb659a07786cf0ee
seg_lines: 34
-->

```fortran
!file: phys/MYNN-EDMF/module_bl_mynnedmf.F90    L5947-L5980
L05947        subroutine tridiag2(kte,a,b,c,d,x)
L05948  
L05949  !      a - sub-diagonal (means it is the diagonal below the main diagonal)
L05950  !      b - the main diagonal
L05951  !      c - sup-diagonal (means it is the diagonal above the main diagonal)
L05952  !      d - right part
L05953  !      x - the answer
L05954  !      kte - number of unknowns (levels)
L05955          use module_bl_mynnedmf_common, only: zero,one,kind_phys
L05956          
L05957          integer,intent(in) :: kte
L05958          real(kind_phys), dimension(kte), intent(in) :: a,b,c,d
L05959          real(kind_phys), dimension(kte), intent(out):: x
L05960          real(kind_phys), dimension(kte)  :: cp1,dp1
L05961          real(kind_phys):: m
L05962          integer :: k
L05963  
L05964          ! initialize c-prime and d-prime
L05965          cp1(1) = c(1)/b(1)
L05966          dp1(1) = d(1)/b(1)
L05967          ! solve for vectors c-prime and d-prime
L05968          do k = 2,kte
L05969             m = b(k)-cp1(k-1)*a(k)
L05970             cp1(k) = c(k)/m
L05971             dp1(k) = (d(k)-dp1(k-1)*a(k))/m
L05972          enddo
L05973          ! initialize x
L05974          x(kte) = dp1(kte)
L05975          ! solve for x from the vectors c-prime and d-prime
L05976          do k = kte-1, 1, -1
L05977             x(k) = dp1(k)-cp1(k)*x(k+1)
L05978          end do
L05979  
L05980      end subroutine tridiag2
```

> **tridiag2**：Thomas 算法的“教科书形态”——前向消元构造 c'/d'（cp1/dp1），回代得 x。**输入 a/b/c/d 全部保留（intent(in)）**、解写进独立输出 x——这是倾向主环统一采用的版本（安全：同组 a/b/c/d 可复用）。

<!-- code_extract code_extract.py v1.1
source: phys/MYNN-EDMF/module_bl_mynnedmf.F90
ranges: L5983-L6018
file_lines: 8776
file_md5: ec93fee9745a3e0b25be55a61b5aff8a
display: line-numbered (strip L-prefix and !file: line to restore)
range_md5: bea29c1500bbaf2a6bb51fe51b45201b
seg_lines: 36
-->

```fortran
!file: phys/MYNN-EDMF/module_bl_mynnedmf.F90    L5983-L6018
L05983         subroutine tridiag3(kte,a,b,c,d,x)
L05984  
L05985  !ccccccccccccccccccccccccccccccc                                                                   
L05986  ! Aim: Inversion and resolution of a tridiagonal matrix                                            
L05987  !          A X = D                                                                                 
L05988  ! Input:                                                                                           
L05989  !  a(*) lower diagonal (Ai,i-1)                                                                  
L05990  !  b(*) principal diagonal (Ai,i)                                                                
L05991  !  c(*) upper diagonal (Ai,i+1)                                                                  
L05992  !  d                                                                                               
L05993  ! Output                                                                                           
L05994  !  x     results                                                                                   
L05995  !ccccccccccccccccccccccccccccccc                                                                   
L05996          use module_bl_mynnedmf_common, only: zero,one,kind_phys
L05997           
L05998          integer,intent(in)   :: kte
L05999          integer, parameter   :: kts=1
L06000          real(kind_phys), dimension(kte) :: a,b,c,d
L06001          real(kind_phys), dimension(kte), intent(out) :: x
L06002          integer :: k
L06003  
L06004          do k=kte-1,kts,-1
L06005             d(k)=d(k)-c(k)*d(k+1)/b(k+1)
L06006             b(k)=b(k)-c(k)*a(k+1)/b(k+1)
L06007          enddo
L06008  
L06009          do k=kts+1,kte
L06010             d(k)=d(k)-a(k)*d(k-1)/b(k-1)
L06011          enddo
L06012  
L06013          do k=kts,kte
L06014             x(k)=d(k)/b(k)
L06015          enddo
L06016  
L06017          return
L06018          end subroutine tridiag3
```

> **tridiag3**：另一种就地消元（先上行消 c、再下行消 a、最后除主对角）——**会修改输入的 b/c/d**（无 intent 声明按默认 inout）。被 mix_chem/mix_scalars 采用。**三个求解器数学等价、接口语义不同**——改造时换求解器要检查输入是否被复用。

## 09b.5 `GET_PBLH`：混合型边界层高度诊断

<!-- code_extract code_extract.py v1.1
source: phys/MYNN-EDMF/module_bl_mynnedmf.F90
ranges: L6022-L6175
file_lines: 8776
file_md5: ec93fee9745a3e0b25be55a61b5aff8a
display: line-numbered (strip L-prefix and !file: line to restore)
range_md5: 6f57121f1927c651a9fe8a6ec27d9933
seg_lines: 154
-->

```fortran
!file: phys/MYNN-EDMF/module_bl_mynnedmf.F90    L6022-L6175
L06022  !! This subroutine calculates hybrid diagnotic boundary-layer height (PBLH).
L06023  !!
L06024  !! NOTES ON THE PBLH FORMULATION:
L06025  !!Two different diagnostics are calculated, each of them specialized for a
L06026  !!distinct regime (stbale and unstable). The two diagnostics are then blended
L06027  !!according to low-level stability, where the magnitude of the of the unstable
L06028  !!pbl height is used as a proxy for the low-level stability. The unstable pblh uses
L06029  !!the delta-theta-increase method, which defines the pbl height as the level at
L06030  !!which the potential temperature first exceeds the minimum potential
L06031  !!!temperature within the boundary layer by some specified delta (about 1.5 K).
L06032  !!When applied to observed temperatures, this method has been shown to produce PBL-
L06033  !!height estimates that are unbiased relative to profiler-based
L06034  !!estimates (Nielsen-Gammon et al. 2008\cite Nielsen_Gammon_2008),
L06035  !!but it can be biased in stable conditions. Two options 
L06036  !!are now available for the stable pblh diagnostic, selectable by the
L06037  !!stable_method internal parameter. Option 0 uses a TKE-based PBL height,
L06038  !!which has been shown by Banta and Pichugina (2008) \cite Pichugina_2008 to be a good estimate of
L06039  !!the PBL height in stable LLJ conditions. Option 1 selects a friction-velocity method of
L06040  !!Koracin and Berkowicz (1988\cite Koracin_Berkowicz_1988), which is a very simple one-line
L06041  !!diagnostic that has been shown to be very reliable strictly within the stable regime
L06042  !!(Steeneveld et al. 2007\cite Steeneveld_et_al_2007). Therefore, a blending (hybrid)
L06043  !!method is implemented that uses both methods, weighting each higher in their
L06044  !!respective specialized regime. 
L06045  !>\section gen_get_pblh  GSD get_pblh General Algorithm
L06046  !> @{
L06047  SUBROUTINE GET_PBLH(KTS,KTE,pblh,thv1,qke1,ust,zw1,dz1,landsea,kpbl)
L06048  
L06049  !---------------------------------------------------------------
L06050    use module_bl_mynnedmf_common, only: zero,one,ten,hundred,p5,kind_phys
L06051    
L06052  integer,intent(in) :: KTS,KTE
L06053  
L06054  #ifdef HARDCODE_VERTICAL
L06055  # define kts 1
L06056  # define kte HARDCODE_VERTICAL
L06057  #endif
L06058  
L06059  real(kind_phys), intent(out) :: pblh
L06060  real(kind_phys), intent(in) :: landsea,ust
L06061  real(kind_phys), dimension(kts:kte), intent(in) :: thv1, qke1, dz1
L06062  real(kind_phys), dimension(kts:kte+1), intent(in) :: zw1
L06063  !local variables
L06064  real(kind_phys):: pblh_stable,qtke,qtkem1,wt,maxqke,TKEeps,minthv,cpblh
L06065  real(kind_phys):: delt_thv   !delta theta-v; dependent on land/sea point
L06066  real(kind_phys), parameter :: sbl_lim  = 200. !below this height (m), the stable PBLH method will dominate the blending.
L06067  real(kind_phys), parameter :: sbl_damp = 170. !transition length for blending (m).
L06068  integer :: i,j,k,kthv,ktke,kpbl
L06069  integer, parameter :: stable_method=1 !0: TKE-based PBLH, 1: ust*700
L06070  
L06071  !Initialize kpbl
L06072  kpbl = 2
L06073  
L06074  !> - FIND MIN THETAV IN THE LOWEST 200 M AGL
L06075  k = kts+1
L06076  kthv = 1
L06077  minthv = 9.E9_kind_phys
L06078  do while (zw1(k) .le. 200.)
L06079     if (minthv > thv1(k)) then
L06080        minthv = thv1(k)
L06081        kthv = k
L06082     endif
L06083     k = k+1
L06084  enddo
L06085  
L06086  !> - FIND THETAV-BASED PBLH (BEST FOR DAYTIME).
L06087  pblh=zero
L06088  k = kthv+1
L06089  if ((landsea-1.5) .ge. zero) then
L06090     ! WATER
L06091     delt_thv = 0.75_kind_phys
L06092  else
L06093     ! LAND
L06094     delt_thv = 1.25_kind_phys
L06095  endif
L06096  
L06097  pblh=zero
L06098  k = kthv+1
L06099  do k=kts+1,kte-1
L06100     if (thv1(k) .ge. (minthv + delt_thv)) then
L06101        pblh = zw1(k) - dz1(k-1)* &
L06102        & min((thv1(k)-(minthv + delt_thv))/ &
L06103        & max(thv1(k)-thv1(k-1),1E-6_kind_phys),one)
L06104     endif
L06105     if (k .EQ. kte-1) pblh = zw1(kts+1) !EXIT SAFEGUARD
L06106     if (pblh .gt. zero) exit
L06107  enddo
L06108  !print*,"IN GET_PBLH:",thsfc,pblh
L06109  
L06110  if (stable_method == 0) then
L06111     !> - for stable boundary layers, use tke method to complement the
L06112     !! thetav-based definition (when the theta-v based pblh is below ~0.5 km).
L06113     !!the tanh weighting function will make the tke-based definition negligible 
L06114     !!when the theta-v-based definition is above ~1 km.
L06115     ktke   = 1
L06116     maxqke = max(qke1(kts),zero)
L06117     !use 5% of tke max (kosovic and curry, 2000; jas)
L06118     !tkeeps = maxtke/20. = maxqke/40.
L06119     tkeeps = maxqke/40._kind_phys
L06120     tkeeps = max(tkeeps,0.01_kind_phys) !0.025) 
L06121     pblh_stable=zero
L06122  
L06123     k = ktke+1
L06124     do k=kts+1,kte-1
L06125        qtke  =max(p5*qke1(k)  , zero)
L06126        qtkem1=max(p5*qke1(k-1), zero)
L06127        if (qtke .le. tkeeps) then
L06128           pblh_stable = zw1(k) - dz1(k-1)* &
L06129           & min((tkeeps-qtke)/max(qtkem1-qtke, 1e-6_kind_phys), one)
L06130           !in case of near zero tke, set pblh = lowest level.
L06131           pblh_stable = max(pblh_stable,zw1(kts+1))
L06132           !print *,"pblh_stable:",i,pblh_stable, qke1(k)/2., zw1(kts+1)
L06133        endif
L06134        !k = k+1
L06135        if (k .eq. kte-1) pblh_stable = zw1(kts+1) !exit safeguard
L06136        if (pblh_stable .ne. zero) exit
L06137     enddo
L06138     !> - the tke-based pblh can (rarely) become very large 
L06139     !! in grid points with deep convection (> 8 km!),
L06140     !! so a limit is imposed to not let pblh_stable exceed the
L06141     !! theta_v-based pbl height +/- 350 m.
L06142     !! this has no impact on 99% of the domain.
L06143     pblh_stable = min(pblh_stable,pblh+350._kind_phys)
L06144     pblh_stable = max(pblh_stable,max(pblh-350._kind_phys, ten))
L06145     !if in old pool situation, default to theta_v-based def
L06146     if (maxqke <= tkeeps) pblh_stable = pblh
L06147  else
L06148     !> - Method based on Koracin and Berkowicz (1988):
L06149     wt          = p5*TANH((pblh - hundred)/hundred) + p5
L06150     cpblh       = 400._kind_phys*(one-wt) + 700._kind_phys*wt
L06151     pblh_stable = max(ust*cpblh, ten)
L06152     !Even though this estimate will dominate in stable conditions, it should
L06153     !be liberally bounded:
L06154     pblh_stable = max(pblh_stable, pblh-sbl_lim)
L06155     pblh_stable = min(pblh_stable, pblh+sbl_lim)
L06156  endif
L06157  
L06158  !blend the stable and unstable pblh heights
L06159  wt=p5*TANH((pblh - sbl_lim)/sbl_damp) + p5
L06160  pblh=pblh_stable*(one-wt) + pblh*wt
L06161  
L06162  !Compute kpbl
L06163  do k=kts+1,kte-1
L06164     if ( zw1(k) >= pblh) then
L06165        kpbl = k-1
L06166        exit
L06167     endif
L06168  enddo
L06169  
L06170  #ifdef HARDCODE_VERTICAL
L06171  # undef kts
L06172  # undef kte
L06173  #endif
L06174  
L06175  END SUBROUTINE GET_PBLH
```

> - **设计哲学**（头注释 L6022–L6046 原文）：两个专用诊断按稳定度混合——**不稳定侧用 θ_v 增量法**（Nielsen-Gammon 2008：θ_v 首次超过 PBL 内最小值 + Δ 的层；观测对比无偏）、**稳定侧两选一**（`stable_method=0`：TKE 阈值法，Banta & Pichugina 2008——低空急流稳定层的可靠估计；`=1`（现行默认）：Koracin & Berkowicz (1988) 摩擦速度法 `u*×400~700`，一行诊断、稳定段极可靠（Steeneveld 2007））。**tanh 权重按不稳定 PBLH 混合**（200 m 以下稳定法主导、170 m 过渡带）。
> - **θ_v 增量法细节**：最小 θ_v 只在**最低 200 m** 内找（`minthv`）；Δθ_v **水面 0.75 K / 陆地 1.25 K**（海面湍流弱、阈值低）；层内线性插值落点；`kte−1` 兜底（PBL 顶到模式顶时回退最低层）。
> - **TKE 法细节**（stable_method=0）：阈值 `tkeeps = maxqke/40`（Kosovic & Curry 2000 的 5% TKE：qke=2TKE，5%=1/20 TKE=1/40 qke）；诊断出的稳定 PBLH **钳在 θ_v 法 ±350 m 内**（防深对流格点 PBLH 冲到 8 km——注释自承“99% 的域不受影响”）。
> - **kpbl**：`zw(k) ≥ pblh` 的首层前一索引——staggered 的 PBL 顶索引，供 DMP_mf/ddmp_mf 定位。

## 09b.6 `DMP_mf`：八羽谱积分上升流（EDMF 核心）

<!-- code_extract code_extract.py v1.1
source: phys/MYNN-EDMF/module_bl_mynnedmf.F90
ranges: L6197-L6404
file_lines: 8776
file_md5: ec93fee9745a3e0b25be55a61b5aff8a
display: line-numbered (strip L-prefix and !file: line to restore)
range_md5: f7dbc7e821467ee8bc4d5d23e840ff06
seg_lines: 208
-->

```fortran
!file: phys/MYNN-EDMF/module_bl_mynnedmf.F90    L6197-L6404
L06197    SUBROUTINE DMP_mf(i,j,                           &
L06198                   & kts,kte,dt,zw1,dz1,pres1,rho1,  &
L06199                   & momentum_opt,                   &
L06200                   & tke_opt,                        &
L06201                   & scalar_opt,                     &
L06202                   & aerosol_opt, numcon_opt,        &
L06203                   & bl_mynn_closure,                &
L06204                   & u1,v1,w1,th1,thl1,thv1,tk1,     &
L06205                   & qt1,qv1,qc1,qke1,qsq1,          &
L06206                   & qnc1,qni1,qnwfa1,qnifa1,qnbca1, &
L06207                   & ex1,vt1,vq1,sgm1,               &
L06208                   & ust,flt,fltv,flq,flqv,          &
L06209                   & pblh,kpbl,dx,landsea,ts,        &
L06210              ! outputs - updraft properties   
L06211                   & edmf_a1,edmf_w1,                &
L06212                   & edmf_qt1,edmf_thl1,             &
L06213                   & edmf_ent1,edmf_qc1,             &
L06214                   & edmf_qv1,edmf_u1,edmf_v1,       &
L06215              ! outputs - variables needed for solver 
L06216                   & s_aw1,s_awthl1,s_awqt1,         &
L06217                   & s_awqv1,s_awqc1,                &
L06218                   & s_awu1,s_awv1,s_awqke1,s_awqsq1,&
L06219                   & s_awqnc1,s_awqni1,              &
L06220                   & s_awqnwfa1,s_awqnifa1,          &
L06221                   & s_awqnbca1,                     &
L06222                   & sub_thl1,sub_sqv1,              &
L06223                   & sub_u1,sub_v1,                  &
L06224                   & det_thl1,det_sqv1,det_sqc1,     &
L06225                   & det_u1,det_v1,                  &
L06226              ! chem/smoke
L06227                   & nchem,chem1,s_awchem1,          &
L06228                   & mix_chem,                       &
L06229              ! generic scalar array
L06230                   & nscalars,scalars,s_awscalars1,  &                 
L06231              ! in/outputs - subgrid scale clouds
L06232                   & qc_bl1,cldfra_bl1,              &
L06233                   & qc_bl1_old,cldfra_bl1_old,      &
L06234              ! inputs - flags for moist arrays
L06235                   & F_QC,F_QI,                      &
L06236                   & F_QNC,F_QNI,                    &
L06237                   & F_QNWFA,F_QNIFA,F_QNBCA,        &
L06238                   & Psig_shcu,                      &
L06239              ! output info
L06240                   & maxwidth,ktop,maxmf,ztop,       &
L06241                   & excess_h,excess_q,              &
L06242              ! inputs for stochastic perturbations
L06243                   & spp_pbl,pattern_spp_pbl1,       &
L06244                   & tkeprod_up,el1                  )
L06245  
L06246      use module_bl_mynnedmf_common, only: gtr,p608,grav,xlvcp,ep_2,  &
L06247           ep_3,r_v,cp,cpv,tv0,b1,                                    &
L06248           zero,one,two,three,four,five,thirty,hundred,               &
L06249           p2,p3,p333,p4,p5,kind_phys
L06250  
L06251  #ifdef HARDCODE_VERTICAL
L06252  # define kts 1
L06253  # define kte HARDCODE_VERTICAL
L06254  #endif
L06255  
L06256  ! configuration inputs:
L06257   integer, intent(in) ::                                            &
L06258        kts,                kte,                  kpbl,              &
L06259        momentum_opt,       tke_opt,              scalar_opt,        &
L06260        aerosol_opt,        numcon_opt,                              &
L06261        spp_pbl,            i,                    j
L06262   real(kind_phys), intent(in):: bl_mynn_closure
L06263   real(kind_phys), dimension(kts:kte), intent(in)  ::               &
L06264        pattern_spp_pbl1
L06265  ! state variables
L06266   real(kind_phys), dimension(kts:kte), intent(in)  ::               &
L06267        &u1,v1,w1,th1,thl1,tk1,qt1,qv1,qc1,                          &
L06268        &ex1,dz1,thv1,pres1,rho1,qke1,qsq1,qnc1,qni1,                &
L06269        &qnwfa1,qnifa1,qnbca1,el1
L06270   real(kind_phys),dimension(kts:kte+1), intent(in) ::               &
L06271        &zw1
L06272   real(kind_phys), intent(in)                      ::               &
L06273        &flt,fltv,flq,flqv,Psig_shcu,                                &
L06274        &landsea,ts,dx,dt,ust,pblh
L06275   logical, optional :: F_QC,F_QI,F_QNC,F_QNI,F_QNWFA,F_QNIFA,F_QNBCA
L06276  
L06277   ! outputs - updraft properties
L06278   real(kind_phys),dimension(kts:kte), intent(inout) ::              &
L06279        &edmf_a1,edmf_w1,edmf_qt1,edmf_thl1,edmf_ent1,edmf_qc1,      &
L06280        &edmf_u1,edmf_v1,edmf_qv1
L06281   ! add one local edmf variable:
L06282    real(kind_phys),dimension(kts:kte) :: edmf_th1
L06283   ! output
L06284   integer,         intent(inout) :: ktop
L06285   real(kind_phys), intent(inout) :: maxmf,ztop,maxwidth,            &
L06286        &excess_h,excess_q
L06287   ! outputs - variables needed for solver: sum ai*rho*wis_awphi
L06288   real(kind_phys),dimension(kts:kte+1), intent(inout) ::            &
L06289        &s_aw1,s_awthl1,s_awqt1,s_awqv1,s_awqc1,s_awqnc1,s_awqni1,   &
L06290        &s_awqnwfa1,s_awqnifa1,s_awqnbca1,s_awu1,s_awv1,             &
L06291        &s_awqke1,s_awqsq1
L06292   real(kind_phys),dimension(kts:kte+1) :: s_aw2
L06293  
L06294   real(kind_phys),dimension(kts:kte), intent(inout) ::              &
L06295        &qc_bl1,cldfra_bl1,qc_bl1_old,cldfra_bl1_old,tkeprod_up
L06296   integer, parameter :: nup=8, debug_mf=0
L06297   real(kind_phys)    :: nup2
L06298  
L06299   !------------- local variables -------------------
L06300   ! updraft properties defined on interfaces (k=1 is the top of the
L06301   ! first model layer
L06302   real(kind_phys),dimension(kts:kte+1,1:NUP) ::                     &
L06303        &UPW,UPTHL,UPQT,UPQC,UPQV,                                   &
L06304        &UPA,UPU,UPV,UPTHV,UPQKE,UPQSQ,UPQNC,                        &
L06305        &UPQNI,UPQNWFA,UPQNIFA,UPQNBCA
L06306   ! entrainment defined as the mass-layer mean
L06307   real(kind_phys),dimension(kts:kte,1:NUP) :: ENT
L06308   ! internal variables
L06309   integer :: k,ip,k50
L06310   real(kind_phys):: fltv2,wstar,qstar,thstar,sigmaW,sigmaQT,        &
L06311        &sigmaTH,z0,pwmin,pwmax,wmin,wmax,wlv,Psig_w,maxw,maxqc,wpbl
L06312   real(kind_phys):: B,QTn,THLn,THVn,QCn,Un,Vn,QKEn,QSQn,QNCn,QNIn,  &
L06313        &  QNWFAn,QNIFAn,QNBCAn,upak,                                &
L06314        &  Wn2,Wn,EntEXP,EntEXM,EntW,BCOEFF,THVkm1,THVk,Pk,rho_int
L06315  
L06316   ! w parameters-used in the original entrainment form
L06317   real(kind_phys), parameter ::                                     &
L06318        &Wa=2./3.,      Wb=0.002,      Wc=1.5 
L06319  
L06320   ! Parameters/variables for regulating plumes:
L06321   real(kind_phys), parameter :: Atot = 0.10 ! Maximum total fractional area of all updrafts
L06322   real(kind_phys), parameter :: lmax = 1000.! diameter of largest plume (absolute maximum, can be smaller)
L06323   real(kind_phys), parameter :: lmin = 300. ! diameter of smallest plume (absolute minimum, can be larger)
L06324   real(kind_phys), parameter :: dlmin = 0.  ! delta increase in the diameter of smallest plume (large fltv) 
L06325   real(kind_phys)            :: minwidth    ! actual width of smallest plume
L06326   real(kind_phys)            :: dl          ! variable increment of plume size
L06327   real(kind_phys), parameter :: dcut = 1.2  ! max diameter of plume to parameterize relative to dx (km)
L06328   real(kind_phys)::  d     != -2.3 to -1.7  ;=-1.9 in Neggers paper; power law exponent for number density (N=Cl^d).
L06329        ! Note that changing d to -2.0 makes each size plume equally contribute to the total coverage of all plumes.
L06330        ! Note that changing d to -1.7 doubles the area coverage of the largest plumes relative to the smallest plumes.
L06331   real(kind_phys):: cn,c,l,n,an2,hux,wspd_pbl,cloud_base,           &
L06332        maxwidth_dx,maxwidth_pbl,maxwidth_cld,maxwidth_flx
L06333  
L06334   ! chem/smoke
L06335   integer, intent(in) :: nchem
L06336   real(kind_phys),dimension(kts:kte,   nchem)       :: chem1
L06337   real(kind_phys),dimension(kts:kte+1, nchem)       :: s_awchem1
L06338   real(kind_phys),dimension(nchem)                  :: chemn
L06339   real(kind_phys),dimension(kts:kte+1,1:NUP, nchem) :: UPCHEM
L06340   integer :: ic,cb_check
L06341   real(kind_phys),dimension(kts:kte,   nchem)       :: edmf_chem
L06342   logical, intent(in) :: mix_chem
L06343   !generic scalars
L06344   integer, intent(in) :: nscalars
L06345   real(kind_phys),dimension(kts:kte,   nscalars)    :: scalars
L06346   real(kind_phys),dimension(kts:kte+1, nscalars)    :: s_awscalars1
L06347   real(kind_phys),dimension(nscalars)               :: scalarsn
L06348   real(kind_phys),dimension(kts:kte+1,1:NUP,nscalars) :: upscalars
L06349   !local ktop for each plume
L06350   integer,dimension(1:NUP) :: ktop_plume
L06351   logical :: superadiabatic
L06352  
L06353   ! Varaibles for mass flux cloud fraction
L06354   real(kind_phys),dimension(kts:kte), intent(inout) :: vt1, vq1, sgm1
L06355   real(kind_phys):: sigq,xl,rsl,cpm,a,qmq,Aup,Q1,diffqt,qsat_tk,     &
L06356           Fng,qww,alpha,beta,bb,f,pt,t,q2p,b9,satvp,rhgrid,entfac,   &
L06357           cf_strat,qc_strat,cf_mf,qc_mf,qc_mf_min,pct_mf,wt2,        &
L06358           dqwdz,tauc,mf_at_cb,qcfac,sigqfac,cffac
L06359   real(kind_phys), parameter :: cf_thresh = 0.5 ! only overwrite stratus CF less than this value
L06360  
L06361   ! Variables interpolated to interface levels
L06362   real(kind_phys),dimension(kts:kte) :: exneri,dzi,rhoi,qti
L06363   ! Variables for plume interpolation/saturation check 
L06364   real(kind_phys):: THp, QTp, QCp, QCs, esat, qsl
L06365   real(kind_phys):: csigma,acfac,ac_wsp
L06366  
L06367   !plume overshoot
L06368   integer :: overshoot
L06369   real(kind_phys):: bvf, Frz, dzp
L06370  
L06371   !Flux limiter: not let mass-flux of heat between k=1&2 exceed (fluxportion)*(surface heat flux).
L06372   !This limiter makes adjustments to the entire column.
L06373   real(kind_phys):: adjustment, flx1, flt2
L06374   real(kind_phys), parameter :: fluxportion=0.75 ! set liberally, so has minimal impact. Note that
L06375                                       ! 0.5 starts to have a noticeable impact
L06376                                       ! over land (decrease maxMF by 10-20%), but no impact over water.
L06377   !----- environmental subsidence--------------------------------------
L06378   !Option to activate environmental subsidence in mass-flux scheme
L06379   logical,parameter:: env_subs   = .false.
L06380   real(kind_phys),dimension(kts:kte) :: sub_thl1,sub_sqv1,         &
L06381           sub_u1,sub_v1,det_thl1,det_sqv1,det_sqc1,det_u1,det_v1,  &  !tendencied due to detrainment
L06382           envm_a,envm_w,envm_thl,envm_sqv,envm_sqc,                &
L06383           envm_u,envm_v                  !environmental variables defined at middle of layer
L06384   real(kind_phys),dimension(kts:kte+1) ::  envi_a,envi_w !environmental variables defined at model interface
L06385   real(kind_phys):: temp,sublim,qc_ent,qv_ent,qt_ent,thl_ent,detrate, &
L06386           detrateUV,oow,exc_fac,aratio,detturb,qc_grid,qc_sgs,        &
L06387           qc_plume,exc_heat,exc_moist,tk_int,tvs,dthvdz,zagl
L06388   real(kind_phys), parameter :: Cdet   = 1./45.
L06389   real(kind_phys), parameter :: dzpmax = 300. !limit dz used in detrainment - can be excessing in thick layers
L06390   !parameter "Csub" determines the propotion of upward vertical velocity that contributes to
L06391   !environmenatal subsidence. Some portion is expected to be compensated by downdrafts instead of
L06392   !gentle environmental subsidence. 1.0 assumes all upward vertical velocity in the mass-flux scheme
L06393   !is compensated by "gentle" environmental subsidence.
L06394   real(kind_phys), parameter :: Csub=0.25
L06395  
L06396   !Factor for the pressure gradient effects on momentum transport
L06397   real(kind_phys), parameter :: pgfac = 0.00  ! Zhang and Wu showed 0.4 is more appropriate for lower troposphere
L06398   real(kind_phys):: Uk,Ukm1,Vk,Vkm1,dxsa
L06399  
L06400   ! WA TEST 12/23/24 Vars for PBL-average QKE
L06401   real(kind_phys):: qkebl
L06402  
L06403   !set for debugging at specific point
L06404   !integer, parameter::idbg = 452, jdbg = 272
```

> - **签名**：60+ 实参（主入口 §09a.4.6 的装配表是它的镜像）；四个“opt”开关（momentum/tke/scalar/aerosol/numcon）逐项控制 MF 对各变量的输运。
> - **关键常数**（全部 PARAMETER，注释自带出处）：
>   - `nup = 8`——**八个不同直径的羽流**（谱积分，区别于单羽 EDMF）；
>   - `Atot = 0.10`——全部上升流面积分数上限；
>   - `lmin=300/lmax=1000` m——羽流直径上下限；`dcut=1.2` km——超过它参数化失效（dx 相关）；
>   - `d = −1.9`——数密度幂律 `N = C·l^d` 的指数（Neggers 2015, JAMES 建议；注释：改 −2.0 则每档羽流等贡献面积、改 −1.7 则大羽流面积加倍）；
>   - `fluxportion = 0.75`——通量限制器（首层 MF 热通量不得超过地表通量的 75%；0.5 会在陆地减 10–20% maxMF）；
>   - `env_subs = .false.`——环境下沉补偿**关闭**（Csub=0.25、Cdet=1/45 是参数）；
>   - `pgfac = 0.00`——动量的气压梯度项系数（注释：Zhang & Wu 认为 0.4 更合适）——**待启用的物理**。

<!-- code_extract code_extract.py v1.1
source: phys/MYNN-EDMF/module_bl_mynnedmf.F90
ranges: L6406-L6610
file_lines: 8776
file_md5: ec93fee9745a3e0b25be55a61b5aff8a
display: line-numbered (strip L-prefix and !file: line to restore)
range_md5: 591e5abadb05a16f6993c98f17b9b1a5
seg_lines: 205
-->

```fortran
!file: phys/MYNN-EDMF/module_bl_mynnedmf.F90    L6406-L6610
L06406  ! Inititialize 2d ouput
L06407   ktop      =0    !integer
L06408   ztop      =zero
L06409   maxmf     =zero
L06410   maxwidth  =zero
L06411   excess_h  =zero
L06412   excess_q  =zero
L06413   ! Initialize individual updraft properties
L06414   upw       =zero
L06415   upthl     =zero
L06416   upthv     =zero
L06417   upqt      =zero
L06418   upa       =zero
L06419   upu       =zero
L06420   upv       =zero
L06421   upqc      =zero
L06422   upqv      =zero
L06423   upqke     =zero
L06424   upqsq     =zero
L06425   upqnc     =zero
L06426   upqni     =zero
L06427   upqnwfa   =zero
L06428   upqnifa   =zero
L06429   upqnbca   =zero
L06430   if ( mix_chem ) then
L06431      upchem(kts:kte+1,1:nup,1:nchem)=zero
L06432   endif
L06433   if ( scalar_opt > 0 ) then
L06434      upscalars(kts:kte+1,1:nup,1:nscalars)=zero
L06435   endif
L06436   ent       =0.001_kind_phys
L06437   ! Initialize mean updraft properties
L06438   edmf_a1   =zero
L06439   edmf_w1   =zero
L06440   edmf_qt1  =zero
L06441   edmf_thl1 =zero
L06442   edmf_ent1 =zero
L06443   edmf_qc1  =zero
L06444   edmf_qv1  =zero
L06445   edmf_u1   =zero
L06446   edmf_v1   =zero
L06447   if ( mix_chem ) then
L06448      edmf_chem(kts:kte,1:nchem) = zero
L06449   endif
L06450   ! Initialize the variables needed for implicit solver
L06451   s_aw1     =zero
L06452   s_awthl1  =zero
L06453   s_awqt1   =zero
L06454   s_awqv1   =zero
L06455   s_awqc1   =zero
L06456   s_awu1    =zero
L06457   s_awv1    =zero
L06458   s_awqke1  =zero
L06459   s_awqsq1  =zero
L06460   s_awqnc1  =zero
L06461   s_awqni1  =zero
L06462   s_awqnwfa1=zero
L06463   s_awqnifa1=zero
L06464   s_awqnbca1=zero
L06465   if ( mix_chem ) then
L06466      s_awchem1(kts:kte+1,1:nchem) = zero
L06467   endif
L06468   if ( scalar_opt > 0 ) then
L06469      s_awscalars1(kts:kte+1,1:nscalars) = zero
L06470   endif
L06471   ! Initialize explicit tendencies for subsidence & detrainment
L06472   sub_thl1 = zero
L06473   sub_sqv1 = zero
L06474   sub_u1   = zero
L06475   sub_v1   = zero
L06476   det_thl1 = zero
L06477   det_sqv1 = zero
L06478   det_sqc1 = zero
L06479   det_u1   = zero
L06480   det_v1   = zero
L06481   nup2     = nup !start with nup, but set to zero if activation criteria fails
L06482   tkeprod_up = zero
L06483  
L06484   if (debug_mf == 1 .and. i==idbg .and. j==jdbg) then
L06485      print*,"===incoming forcing in mf component:"
L06486      print*,"  flt=",flt," fltv=",fltv
L06487      print*,"  Psig_shcu=",Psig_shcu," wspd=",sqrt(max(u1(kts)**2 + v1(kts)**2, 0.01_kind_phys))
L06488   endif
L06489        
L06490   ! Taper off MF scheme when significant resolved-scale motions
L06491   ! are present This function needs to be asymetric...
L06492   maxw        = zero
L06493   cloud_base  = 9000.0_kind_phys
L06494   qkebl       = zero
L06495   do k=1,kte-1
L06496      zagl = zw1(k) + p5*dz1(k)
L06497      if (zagl > (pblh + 500.)) exit
L06498  
L06499      wpbl = w1(k)
L06500      if (w1(k) < zero)wpbl = two*w1(k)
L06501      maxw = max(maxw,abs(wpbl))
L06502  
L06503      !Find highest k-level below 50m AGL
L06504      if (zagl <= 50.)k50=k
L06505  
L06506      !Establish mean tke in pbl for entrainment
L06507      if (k <= kpbl) then
L06508         qkebl = qkebl + qke1(k)
L06509      endif
L06510  
L06511      !Search for cloud base
L06512      qc_sgs = max(qc1(k), qc_bl1(k))
L06513      if ((qc_sgs > 1E-5) .and. (cldfra_bl1(k) .ge. p5) .and. cloud_base == 9000.0) then
L06514         cloud_base = zw1(k) !height at interface below cloud mass level
L06515      endif
L06516   enddo
L06517   qkebl = qkebl / real(kpbl, kind=kind_phys)
L06518   
L06519   !do nothing for small w (< 1 m/s), but linearly taper off for w > 1.0 m/s
L06520   maxw = max(zero, maxw - one)
L06521   Psig_w = max(zero, one - maxw)
L06522   Psig_w = min(Psig_w, Psig_shcu)
L06523  
L06524   !Completely shut off MF scheme for strong resolved-scale vertical velocities.
L06525   fltv2 = fltv
L06526   if (Psig_w < 1e-2_kind_phys .and. fltv > zero) fltv2 = -1.*fltv
L06527  
L06528   if (debug_mf == 1 .and. i==idbg .and. j==jdbg) then
L06529      print*,"===criteria for small w in pbl:"
L06530      print*,"maxw=",maxw," Psig_w=",Psig_w," k50=",k50
L06531   endif
L06532        
L06533   ! If surface buoyancy is positive we do integration, otherwise no.
L06534   ! Also, ensure that it is at least slightly superadiabatic up through 50 m
L06535   superadiabatic = .false.
L06536   if ((landsea-1.5).ge.zero) then
L06537      hux = -0.0024  ! WATER   ! dTHv/dz must be < -0.24 K per 100 m.
L06538   else
L06539      hux = -0.0030  ! LAND    ! dTHv/dz must be < -0.30 K per 100 m.
L06540   endif
L06541   tvs    = ts*(one+p608*qv1(kts))
L06542   if ((thv1(kts)-tvs)/(p5*dz1(kts)) < hux) then
L06543      !if superadiabatic at the surface, continue checking all layers below 50 m:
L06544      superadiabatic = .true.
L06545      do k=2,max(2,k50)
L06546         hux = -0.0018  !allow for smaller superadiabatic layers above the surface
L06547         dthvdz = (thv1(k)-thv1(k-1))/(p5*(dz1(k)+dz1(k-1)))
L06548         if (dthvdz < hux) then
L06549            superadiabatic = .true.
L06550         else
L06551            superadiabatic = .false.
L06552            exit
L06553         endif
L06554      enddo
L06555   endif
L06556  
L06557   if (debug_mf == 1 .and. i==idbg .and. j==jdbg) then
L06558      print*," superadiatic=",superadiabatic," hux=",hux
L06559   endif
L06560  
L06561   ! Determine the numer of updrafts/plumes in the grid column:
L06562   ! Some of these criteria may be a little redundant but useful for bullet-proofing.
L06563   !   (1) largest plume = 1.2 * dx.
L06564   !   (2) Apply a scale-break, assuming no plumes with diameter larger than 1.1*PBLH can exist.
L06565   !   (3) max plume size beneath clouds deck approx = 0.5 * cloud_base.
L06566   !   (4) add wspd-dependent limit, when plume model breaks down. (hurricanes)
L06567   !   (5) limit to reduce max plume sizes in weakly forced conditions. This is only
L06568   !       meant to "soften" the activation of the mass-flux scheme.
L06569   ! Criteria (1)
L06570   maxwidth_dx = min(dx*dcut, lmax)
L06571   !Criteria (2)
L06572   maxwidth_pbl = min(1.1_kind_phys*pblh, lmax) 
L06573   ! Criteria (3)
L06574   if ((landsea-1.5) .lt. zero) then  !land
L06575      maxwidth_cld = min(lmax, max(0.5_kind_phys*cloud_base, 300._kind_phys))
L06576   else                               !water
L06577      maxwidth_cld = min(lmax, max(0.8_kind_phys*cloud_base, 300._kind_phys))
L06578   endif
L06579   ! Criteria (4)
L06580   wspd_pbl=sqrt(max(u1(kts)**2 + v1(kts)**2, 0.01_kind_phys))
L06581   !Note: area fraction (acfac) is modified below
L06582   ! Criteria (5) - function of fltv
L06583   if ((landsea-1.5) .lt. zero) then  !land
L06584      maxwidth_flx = MAX(MIN(1000.*(0.6*tanh((fltv - 0.040)/0.04) + p5),1000._kind_phys), zero)
L06585   else                             !water
L06586      maxwidth_flx = MAX(MIN(1000.*(0.6*tanh((fltv - 0.007)/0.02) + p5),1000._kind_phys), zero)
L06587      !width_flx = MAX(MIN(1000.*(0.6*tanh((fltv - 0.010)/0.025) + .5),1000._kind_phys), zero)
L06588   endif
L06589   maxwidth = MIN(maxwidth_dx, maxwidth_pbl)
L06590   maxwidth = MIN(maxwidth,    maxwidth_cld)
L06591   maxwidth = MIN(maxwidth,    maxwidth_flx)      
L06592   minwidth = lmin
L06593  
L06594   if (debug_mf == 1 .and. i==idbg .and. j==jdbg) then  !land
L06595      print*,"===limiting factors on plume width:"
L06596      print*,"maxwidth_dx= ",maxwidth_dx," dx=",dx
L06597      print*,"maxwidth_pbl=",maxwidth_pbl," pblh=",pblh
L06598      print*,"maxwidth_cld=",maxwidth_cld," cldbase=",cloud_base
L06599      print*,"maxwidth_flx=",maxwidth_flx," fltv=",fltv
L06600      print*,"===final check for activation criteria:"
L06601      print*,"fltv2=",fltv2," superadiatic=",superadiabatic
L06602      print*,"maxwidth=",maxwidth," minwidth=",minwidth
L06603   endif
L06604  
L06605   if (maxwidth .le. minwidth) then ! deactivate MF component
L06606      nup2 = 0
L06607      maxwidth = zero
L06608   endif
L06609  
L06610   !Begin plume processing if passes criteria
```

> - **清零族**：所有 UP*/edmf_*/s_aw*/sub/det 输出清零——无状态。
> - **触发条件之①（解析运动衰减）**：PBL+500 m 以下网格尺度 w 的最大值 `maxw`，>1 m/s 线性衰减 `Psig_w = 1−(maxw−1)`、再与 `Psig_shcu`（灰区函数）取小——**可分辨运动强时 MF 退出**；`Psig_w < 1e-2` 且浮力通量为正时干脆把 `fltv2 = −fltv`（负浮力→羽流必死）。
> - **触发条件之②（超绝热判据）**：表面层 `dθ_v/dz < −0.0024（水）/−0.0030（陆）` K/m（即 −0.24/−0.30 K/100 m）且 50 m 内持续超绝热（`hux = −0.0018` 上层放宽）——**热泡生成的大气条件**。
> - **触发条件之③（羽流尺寸五判据）**：`maxwidth = min(dx·1.2, 1.1·PBLH, 0.5(陆)/0.8(水)·云底, fltv 的 tanh 函数, lmax)`——网格可容纳、PBL 深度可容纳、云底以下可容纳、浮力通量足够；`maxwidth ≤ 300 m（minwidth）` 时 `nup2=0` 关闭 MF。

<!-- code_extract code_extract.py v1.1
source: phys/MYNN-EDMF/module_bl_mynnedmf.F90
ranges: L6611-L6790
file_lines: 8776
file_md5: ec93fee9745a3e0b25be55a61b5aff8a
display: line-numbered (strip L-prefix and !file: line to restore)
range_md5: 09d5564a354639c028fb6838de5981aa
seg_lines: 180
-->

```fortran
!file: phys/MYNN-EDMF/module_bl_mynnedmf.F90    L6611-L6790
L06611   if ( flt > zero .AND. fltv2 > 0.008 .AND. (maxwidth > minwidth) .AND. superadiabatic) then
L06612  
L06613      ! Find coef C for number size density N
L06614      cn = zero
L06615      d  =-1.9_kind_phys  !set d to value suggested by Neggers 2015 (JAMES).
L06616      dl = (maxwidth - minwidth)/real(nup-1,kind=kind_phys)
L06617      do ip=1,NUP
L06618         ! diameter of plume
L06619         l = minwidth + dl*real(ip-1,kind=kind_phys)
L06620         cn = cn + l**d * (l*l)/(dx*dx) * dl  ! sum fractional area of each plume
L06621      enddo
L06622      C = Atot/cn   !Normalize C according to the defined total fraction (Atot)
L06623  
L06624      ! Make updraft area (UPA) a function of the buoyancy flux
L06625      if ((landsea-1.5) .lt. zero) then  !land
L06626         acfac = p5*tanh((fltv2 - 0.02_kind_phys)/0.05_kind_phys) + p5
L06627      else
L06628         acfac = p5*tanh((fltv2 - 0.012_kind_phys)/0.03_kind_phys) + p5
L06629      endif
L06630        
L06631      !For hurricane tuning, add a windspeed-dependent adjustment to acfac that tapers off
L06632      !the mass-flux scheme linearly above sfc wind speeds of 13 m/s.
L06633      ac_wsp = one - min((max(wspd_pbl - 13.0_kind_phys, zero))/12._kind_phys, one)
L06634      acfac  = min(acfac, ac_wsp)
L06635  
L06636      ! Find the portion of the total fraction (Atot) of each plume size:
L06637      An2 = zero
L06638      do ip=1,nup
L06639         ! diameter of plume
L06640         l  = minwidth + dl*real(ip-1,kind=kind_phys)
L06641         N  = C*l**d                           ! number density of plume n
L06642         UPA(1,ip) = N*l*l/(dx*dx) * dl        ! fractional area of plume n
L06643  
L06644         UPA(1,ip) = UPA(1,ip)*acfac
L06645         An2 = An2 + UPA(1,ip)                 ! total fractional area of all plumes
L06646         !if (upa(i,i)<zero)print*,"Neg plume area: plume size=",l," dl=",dl,&
L06647         !    " area=",UPA(1,I),"; total=",An2," acfac=",acfac," N=",N
L06648      end do
L06649  
L06650      if (debug_mf == 1 .and. i==idbg .and. j==jdbg) then
L06651         print*,"===limiting factors on fractional area coverage:"
L06652         print*,"total araa frac=",An2," atot=",atot
L06653         print*,"upa=",UPA(1,1:nup)
L06654         print*,"acfac fluxes=",acfac," fltv=",fltv
L06655         print*,"acfac wspd=",ac_wsp," wspd_pbl=",wspd_pbl
L06656      endif
L06657      
L06658      ! set initial conditions for updrafts
L06659      z0    =50._kind_phys
L06660      pwmin =0.1_kind_phys    ! was 0.5
L06661      pwmax =0.4_kind_phys    ! was 3.0
L06662  
L06663      wstar =max(1.E-2_kind_phys,(gtr*fltv2*pblh)**(p333))
L06664      qstar =max(flq,1e-5_kind_phys)/wstar
L06665      thstar=flt/wstar
L06666  
L06667      csigma=1.34_kind_phys
L06668  
L06669      if (env_subs) then
L06670         exc_fac = zero
L06671      else
L06672         if ((landsea-1.5).GE.zero) then
L06673            !water: increase factor to compensate for decreased pwmin/pwmax
L06674            !0.58*25 = 14.5
L06675            !0.58*20 = 11.6
L06676            !0.58*16 = 9.28
L06677            !0.58*10 = 5.8
L06678            !0.58*5  = 2.9
L06679            exc_fac = 9.28_kind_phys
L06680         else
L06681            !land: no need to increase factor - already sufficiently large superadiabatic layers
L06682            exc_fac = 0.58_kind_phys
L06683         endif
L06684      endif
L06685      !decrease excess for large wind speeds
L06686      exc_fac = exc_fac * ac_wsp
L06687  
L06688      !Note: sigmaW is typically about 0.5*wstar
L06689      sigmaW =csigma*wstar*(z0/pblh)**(p333)*(one - 0.8_kind_phys*z0/pblh)
L06690      sigmaQT=csigma*qstar*(z0/pblh)**(p333)
L06691      sigmaTH=csigma*thstar*(z0/pblh)**(p333)
L06692  
L06693      !Note: Given the pwmin & pwmax set above, these max/mins are
L06694      !      rarely exceeded. 
L06695      wmin=MIN(sigmaW*pwmin,0.1_kind_phys)
L06696      wmax=MIN(sigmaW*pwmax,0.5_kind_phys)
L06697  
L06698      if (debug_mf == 1 .and. i==idbg .and. j==jdbg) then
L06699         print*,"===excess components:"
L06700         print*,"wstar=",wstar,"qstar=",qstar,"thstar=",thstar
L06701         print*,"csigma=",csigma,"exc_fac=",exc_fac,"wmin=",wmin
L06702         print*,"sigmaw=",sigmaw,"sigmaqt=",sigmaqt,"sigmath=",sigmath
L06703      endif
L06704  
L06705      !SPECIFY UPDRAFT PROPERTIES AT MODEL INTERFACE BETWEEN K = 1 & 2
L06706      do ip=1,NUP
L06707         wlv=wmin+(wmax-wmin)/real(NUP2,kind=kind_phys)*real(ip-1,kind=kind_phys)
L06708         UPA(2,ip)    =UPA(1,ip)
L06709         !SURFACE UPDRAFT VERTICAL VELOCITY
L06710         UPW(2,ip)    =wmin + real(ip,kind=kind_phys)/real(NUP)*(wmax-wmin)
L06711         UPU(2,ip)    =(u1(kts)    *dz1(kts+1)+u1(kts+1)    *dz1(kts))/(dz1(kts)+dz1(kts+1))
L06712         UPV(2,ip)    =(v1(kts)    *dz1(kts+1)+v1(kts+1)    *dz1(kts))/(dz1(kts)+dz1(kts+1))
L06713         UPQC(2,ip)   =zero
L06714         !UPQC(1,ip)  =(qc1(kts)*dz1(kts+1)+qc1(kts+1)*dz1(kts))/(dz1(kts)+dz1(kts+1))
L06715  
L06716         exc_heat     =exc_fac*UPW(2,ip)*sigmaTH/sigmaW
L06717         UPTHV(2,ip)  =(thv1(kts)  *dz1(kts+1)+thv1(kts+1)  *dz1(kts))/(dz1(kts)+dz1(kts+1)) &
L06718             &        + exc_heat
L06719         UPTHL(2,ip)  =(thl1(kts)  *dz1(kts+1)+thl1(kts+1)  *dz1(kts))/(dz1(kts)+dz1(kts+1)) &
L06720             &        + exc_heat
L06721         !calculate exc_moist by use of surface fluxes
L06722         exc_moist    =exc_fac*UPW(2,ip)*sigmaQT/sigmaW
L06723         UPQT(2,ip)   =(qt1(kts)   *dz1(kts+1)+qt1(kts+1)   *dz1(kts))/(dz1(kts)+dz1(kts+1))&
L06724              &       + exc_moist
L06725         UPQKE(2,ip)  =(qke1(kts)  *dz1(kts+1)+qke1(kts+1)  *dz1(kts))/(dz1(kts)+dz1(kts+1))
L06726         UPQSQ(2,ip)  =(qsq1(kts)  *dz1(kts+1)+qsq1(kts+1)  *dz1(kts))/(dz1(kts)+dz1(kts+1))
L06727         UPQNC(2,ip)  =(qnc1(kts)  *dz1(kts+1)+qnc1(kts+1)  *dz1(kts))/(dz1(kts)+dz1(kts+1))
L06728         UPQNI(2,ip)  =(qni1(kts)  *dz1(kts+1)+qni1(kts+1)  *dz1(kts))/(dz1(kts)+dz1(kts+1))
L06729         UPQNWFA(2,ip)=(qnwfa1(kts)*dz1(kts+1)+qnwfa1(kts+1)*dz1(kts))/(dz1(kts)+dz1(kts+1))
L06730         UPQNIFA(2,ip)=(qnifa1(kts)*dz1(kts+1)+qnifa1(kts+1)*dz1(kts))/(dz1(kts)+dz1(kts+1))
L06731         UPQNBCA(2,ip)=(qnbca1(kts)*dz1(kts+1)+qnbca1(kts+1)*dz1(kts))/(dz1(kts)+dz1(kts+1))
L06732      enddo
L06733  
L06734      if ( mix_chem ) then
L06735        do ip=1,NUP
L06736          do ic = 1,nchem
L06737            UPCHEM(2,ip,ic)=(chem1(kts,ic)*dz1(kts+1)+chem1(kts+1,ic)*dz1(kts))/(dz1(kts)+dz1(kts+1))
L06738          enddo
L06739        enddo
L06740      endif
L06741      if ( scalar_opt > 0 ) then
L06742        do ip=1,NUP
L06743          do ic = 1,nscalars
L06744            upscalars(2,ip,ic)=(scalars(kts,ic)*dz1(kts+1)+scalars(kts+1,ic)*dz1(kts))/(dz1(kts)+dz1(kts+1))
L06745          enddo
L06746        enddo
L06747     endif
L06748     
L06749      !Initialize environmental variables which can be modified by detrainment
L06750      envm_thl(kts:kte)=thl1(kts:kte)
L06751      envm_sqv(kts:kte)=qv1(kts:kte)
L06752      envm_sqc(kts:kte)=qc1(kts:kte)
L06753      envm_u(kts:kte)  =u1(kts:kte)
L06754      envm_v(kts:kte)  =v1(kts:kte)
L06755      !Interpolate some mass-layer variables to interface variables
L06756      rhoi(kts)   = rho1(kts)
L06757      dzi(kts)    = p5*dz1(kts)
L06758      exneri(kts) = ex1(kts)
L06759      do k=kts+1,kte
L06760         rhoi(k)  = (rho1(k-1)*dz1(k)+rho1(k)*dz1(k-1))/(dz1(k-1)+dz1(k))
L06761         dzi(k)   = (dz1(k-1)*dz1(k)+dz1(k)*dz1(k-1))/(dz1(k-1)+dz1(k))
L06762         exneri(k)= (ex1(k-1)*dz1(k)+ex1(k)*dz1(k-1))/(dz1(k-1)+dz1(k))
L06763      enddo
L06764     
L06765      !dxsa is scale-adaptive factor governing the pressure-gradient term of the momentum transport
L06766      dxsa = one - MIN(MAX((12000.0_kind_phys-dx)/(12000.0_kind_phys-3000.0_kind_phys), zero), one)
L06767  
L06768      ktop_plume = 0
L06769      ! do integration  updraft
L06770      do ip=1,NUP
L06771         QCn = zero
L06772         overshoot = 0 !int
L06773         l  = minwidth + dl*real(ip-1,kind=kind_phys)    ! diameter of plume
L06774         do k=kts+1,kte-2
L06775            zagl = zw1(k) + p5*dz1(k)
L06776            !Entrainment from Tian and Kuang (2016)
L06777            !ENT(k,ip) = 0.35/(MIN(MAX(UPW(K-1,ip),0.75),1.9)*l)
L06778            wmin   = p3 + l*0.0005_kind_phys
L06779            !ENT(k,ip) = 0.33_kind_phys/(MIN(MAX(UPW(k,ip),wmin),one)*l)
L06780            !ENT(k,ip) = (0.20*sqrt(qkebl))/(MIN(MAX(UPW(K-1,ip),wmin),one)*l)
L06781            ! 0.34 ~ 1.62
L06782            ! 0.33 ~ 1.57
L06783            ! 0.30 ~ 1.43
L06784            ! 0.28 ~ 1.33
L06785            ! 0.26 ~ 1.24
L06786            entfac = 0.21_kind_phys * min(1.57_kind_phys, max(1.30_kind_phys, sqrt(qkebl)))
L06787            !entfac = 0.33_kind_phys
L06788            !make entfac tend to original value (0.33) above the pblh:
L06789            wt2    = min(one, max(zero, zagl - pblh)/500._kind_phys) !0 in pbl, 1 aloft
L06790            entfac = entfac*(one-wt2) + wt2*0.33_kind_phys
```

> - **谱分配**：直径从 minwidth 到 maxwidth 均分 8 档（`dl`）；数密度 `N = C·l^d`，C 由总面积 = Atot 归一（L6614–L6622）；**面积分数再乘 `acfac`**——浮力通量的 tanh 函数（陆地阈值 0.02、水面 0.012 K·m/s），并叠加飓风衰减 `ac_wsp`（表面风>13 m/s 线性关断，12 m/s 跨度）。
> - **羽流初值**（50 m 参考高度 `z0`）：`wstar = (g/θ·fltv·PBLH)^(1/3)`（对流速度尺度）、`qstar/thstar = 通量/wstar`（Deardorff 尺度）；σ 因子 `csigma=1.34`、`(z0/PBLH)^(1/3)·(1−0.8·z0/PBLH)` 剖面；**超绝热过量 `exc_fac`**——水面 9.28 / 陆地 0.58（注释列出 0.58×{25,20,16,10,5} 的演化史）——**羽流在 50 m 处的 θ/Qt 超量** = 环境值 + exc_fac·w·σθ/σw。
> - **八个羽流的 w 分布**：`wmin~wmax`（σw 的 0.1~0.4 倍，钳 [0.1, 0.5] m/s）均分——**每羽流初始 w 不同，速度快的大羽流升得高**。
> - **卷入率**（Tian & Kuang 2016）：`ENT = entfac/(max(w, wmin)·l)`，`entfac = 0.21·f(sqrt(qkebl))∈[1.30,1.57]`（PBL 内）向 0.33 过渡（PBL 上 500 m 内）——**卷入反比于速度×直径**（大而快的羽流卷入少）；另有高层增强（>PBL+1500 m 线性加 5e-6·dz）、SPP 扰动、上限 0.9/dz。被注释的 Neggers (2015) 幂律形式（`0.02·l^−0.35`）保留考古。

<!-- code_extract code_extract.py v1.1
source: phys/MYNN-EDMF/module_bl_mynnedmf.F90
ranges: L6791-L7030
file_lines: 8776
file_md5: ec93fee9745a3e0b25be55a61b5aff8a
display: line-numbered (strip L-prefix and !file: line to restore)
range_md5: 617b72c9b2c3661c5c2fc9532e7940dd
seg_lines: 240
-->

```fortran
!file: phys/MYNN-EDMF/module_bl_mynnedmf.F90    L6791-L7030
L06791            ENT(k,ip) = entfac/(MIN(MAX(UPW(K-1,ip),wmin),one)*l)
L06792            
L06793            !Entrainment from Negggers (2015, JAMES)
L06794            !ENT(k,ip) = 0.02*l**-0.35 - 0.0009
L06795            !ENT(k,ip) = 0.04*l**-0.50 - 0.0009   !more plume diversity
L06796            !ENT(k,ip) = 0.04*l**-0.495 - 0.0009  !"neg1+"
L06797  
L06798            !Minimum background entrainment 
L06799            ENT(k,ip) = max(ENT(k,ip),0.0003_kind_phys)
L06800            !ENT(k,ip) = max(ENT(k,ip),0.05/zw1(k))  !not needed for Tian and Kuang
L06801  
L06802            !increase entrainment for plumes extending very high.
L06803            IF(zw1(k) >= MIN(pblh+1500., 4000.))THEN
L06804              ENT(k,ip)=ENT(k,ip) + (zw1(k)-MIN(pblh+1500.,4000.))*5.0E-6
L06805            ENDIF
L06806  
L06807            !SPP
L06808            ENT(k,ip) = ENT(k,ip) * (one - pattern_spp_pbl1(k))
L06809  
L06810            ENT(k,ip) = min(ENT(k,ip), 0.9_kind_phys/dz1(k))
L06811  
L06812            ! Define environment U & V at the model interface levels
L06813            Uk     =(u1(k)*dz1(k+1)+u1(k+1)*dz1(k))/(dz1(k+1)+dz1(k))
L06814            Ukm1   =(u1(k-1)*dz1(k)+u1(k)*dz1(k-1))/(dz1(k-1)+dz1(k))
L06815            Vk     =(v1(k)*dz1(k+1)+v1(k+1)*dz1(k))/(dz1(k+1)+dz1(k))
L06816            Vkm1   =(v1(k-1)*dz1(k)+v1(k)*dz1(k-1))/(dz1(k-1)+dz1(k))
L06817  
L06818            ! Linear entrainment:
L06819            EntExp =ENT(k,ip)*dz1(k)
L06820            EntExm =EntExp*p333    !reduce entrainment for momentum
L06821            QTn    =UPQT(k,IP)   *(one-EntExp) + qt1(k)*EntExp
L06822            THLn   =UPTHL(k,IP)  *(one-EntExp) + thl1(k)*EntExp
L06823            Un     =UPU(k,IP)    *(one-EntExm) + u1(k)*EntExm + dxsa*pgfac*(Uk - Ukm1)
L06824            Vn     =UPV(k,IP)    *(one-EntExm) + v1(k)*EntExm + dxsa*pgfac*(Vk - Vkm1)
L06825            QKEn   =UPQKE(k,IP)  *(one-EntExp) + qke1(k)*EntExp
L06826            QSQn   =UPQSQ(k,IP)  *(one-EntExp) + qsq1(k)*EntExp
L06827            QNCn   =UPQNC(k,IP)  *(one-EntExp) + qnc1(k)*EntExp
L06828            QNIn   =UPQNI(k,IP)  *(one-EntExp) + qni1(k)*EntExp
L06829            QNWFAn =UPQNWFA(k,IP)*(one-EntExp) + qnwfa1(k)*EntExp
L06830            QNIFAn =UPQNIFA(k,IP)*(one-EntExp) + qnifa1(k)*EntExp
L06831            QNBCAn =UPQNBCA(k,IP)*(one-EntExp) + qnbca1(k)*EntExp
L06832  
L06833            !capture the updated qc, qt & thl modified by entranment alone,
L06834            !since they will be modified later if condensation occurs.
L06835            qc_ent =QCn
L06836            qt_ent =QTn
L06837            thl_ent=THLn
L06838  
L06839            ! Exponential Entrainment:
L06840            !EntExp= exp(-ENT(K,IP)*(zw1(k)-zw1(k-1)))
L06841            !QTn =qt1(K) *(1-EntExp)+UPQT(K-1,IP)*EntExp
L06842            !THLn=thl1(K)*(1-EntExp)+UPTHL(K-1,IP)*EntExp
L06843            !Un  =u1(K)  *(1-EntExp)+UPU(K-1,IP)*EntExp
L06844            !Vn  =v1(K)  *(1-EntExp)+UPV(K-1,IP)*EntExp
L06845            !QKEn=qke1(k)*(1-EntExp)+UPQKE(K-1,ip)*EntExp
L06846  
L06847            if ( mix_chem ) then
L06848              do ic = 1,nchem
L06849                ! Exponential Entrainment:
L06850                !chemn(ic) = chem(k,ic)*(1-EntExp)+UPCHEM(K-1,ip,ic)*EntExp
L06851                ! Linear entrainment:
L06852                chemn(ic)=UPCHEM(k,ip,ic)*(one-EntExp) + chem1(k,ic)*EntExp
L06853              enddo
L06854            endif
L06855            if ( scalar_opt > 0 ) then
L06856              do ic = 1,nscalars
L06857                scalarsn(ic)=upscalars(k,ip,ic)*(one-EntExp) + scalars(k,ic)*EntExp
L06858              enddo
L06859            endif
L06860            
L06861            ! Define pressure at model interface we just integrated to (k+1).
L06862            Pk    =(pres1(k)*dz1(k+1)+pres1(k+1)*dz1(k))/(dz1(k)+dz1(k+1))
L06863            ! Compute plume properties thvn and qcn
L06864            call condensation_edmf(QTn,THLn,Pk,zw1(k+1),THVn,QCn)
L06865  
L06866            ! Define environment THV at the model interface levels k & k+1
L06867            THVk  =(thv1(k)*dz1(k+1)+thv1(k+1)*dz1(k))/(dz1(k+1)+dz1(k))
L06868            THVkm1=(thv1(k-1)*dz1(k)+thv1(k)*dz1(k-1))/(dz1(k-1)+dz1(k))
L06869  
L06870  !          B=g*(0.5*(THVn+UPTHV(k-1,ip))/thv1(k-1) - one)
L06871            B=grav*(THVn/THVk - one)
L06872            IF(B>0.)THEN
L06873              BCOEFF = 0.15        !w typically stays < 2.5, so doesnt hit the limits nearly as much
L06874            ELSE
L06875              BCOEFF = 0.2 !0.33
L06876            ENDIF
L06877  
L06878            ! Original StEM with exponential entrainment
L06879            !EntW=exp(-2.*(Wb+Wc*ENT(K,ip))*(zw1(k)-zw1(k-1)))
L06880            !Wn2=UPW(K-1,ip)**2*EntW + (1.-EntW)*0.5*Wa*B/(Wb+Wc*ENT(K,ip))
L06881            ! Original StEM with linear entrainment
L06882            !Wn2=UPW(K-1,ip)**2*(1.-EntExp) + EntExp*0.5*Wa*B/(Wb+Wc*ENT(K,ip))
L06883            !Wn2=MAX(Wn2,zero)
L06884            !WA: TEMF form
L06885            !IF (B>zero .AND. UPW(K-1,ip) < 0.2 ) THEN
L06886            IF (UPW(K-1,ip) < 0.2 ) THEN
L06887               Wn = UPW(k,ip) + (-2. * ENT(k,ip) * UPW(k,ip) + BCOEFF*B / MAX(UPW(k,ip),0.2)) * MIN(dz1(k), 250.)
L06888            ELSE
L06889               Wn = UPW(k,ip) + (-2. * ENT(k,ip) * UPW(k,ip) + BCOEFF*B / UPW(k,ip)) * MIN(dz1(k), 250.)
L06890            ENDIF
L06891            !Do not allow a parcel to accelerate more than 1.25 m/s over 200 m.
L06892            !Add max increase of 2.0 m/s for coarse vertical resolution.
L06893            IF(Wn > UPW(k,ip) + MIN(1.25*dz1(k)/200., two) ) THEN
L06894               Wn = UPW(k,ip) + MIN(1.25*dz1(k)/200., two)
L06895            ENDIF
L06896            !Add symmetrical max decrease in w
L06897            IF(Wn < UPW(k,ip) - MIN(1.25*dz1(k)/200., two) ) THEN
L06898               Wn = UPW(k,ip) - MIN(1.25*dz1(k)/200., two)
L06899            ENDIF
L06900            Wn = MIN(MAX(Wn, zero), 3.0_kind_phys)
L06901  
L06902            !Check to make sure that the plume made it up at least one level.
L06903            !if it failed, then set nup2=0 and exit the mass-flux portion.
L06904            if (k==kts+1 .and. wn < 1e-8) then
L06905               nup2=0
L06906               exit
L06907            endif
L06908  
L06909            if (debug_mf == 1 .and. i==idbg .and. j==jdbg) then
L06910              if (wn .ge. 3.0) then
L06911                ! surface values
L06912                print *," **** SUSPICIOUSLY LARGE W:"
L06913                print *,' QCn:',QCn,' ENT=',ENT(k,ip),' Nup2=',Nup2
L06914                print *,'pblh:',pblh,' Wn:',Wn,' UPW(k)=',UPW(k,ip)
L06915                print *,'K=',k,' B=',B,' dz=',dz1(k)
L06916              ENDIF
L06917            ENDIF
L06918  
L06919            !Allow strongly forced plumes to overshoot if KE is sufficient
L06920            IF (Wn <= zero .AND. overshoot == 0) THEN
L06921               overshoot = 1
L06922               IF ( THVk-THVkm1 .GT. zero ) THEN
L06923                  bvf = SQRT( gtr*(THVk-THVkm1)/dz1(k) )
L06924                  !vertical Froude number
L06925                  Frz = UPW(k,ip)/(bvf*dz1(k))
L06926                  !IF ( Frz >= 0.5 ) Wn =  MIN(Frz,one)*UPW(K-1,I)
L06927                  dzp = dz1(k)*MAX(MIN(Frz,one),zero) ! portion of highest layer the plume penetrates
L06928               ENDIF
L06929            ELSE
L06930               dzp = dz1(k)
L06931            ENDIF
L06932  
L06933            !minimize the plume penetratration in stratocu-topped PBL
L06934            !IF (fltv2 < 0.06) THEN
L06935            !   IF(ZW(k+1) >= pblh-200. .AND. qc1(k) > 1e-5 .AND. ip > 4) Wn=zero
L06936            !ENDIF
L06937  
L06938            !Modify environment variables (representative of the model layer - envm*)
L06939            !following the updraft dynamical detrainment of Asai and Kasahara (1967, JAS).
L06940            !Reminder: w is limited to be non-negative (above)
L06941            aratio   = MIN(UPA(k,IP)/(one-UPA(k,IP)), p5) !limit should never get hit
L06942            detturb  = 0.00008
L06943            oow      = -0.060/MAX(one,(0.5*(Wn+UPW(k,IP))))   !coef for dynamical detrainment rate
L06944            detrate  = MIN(MAX(oow*(Wn-UPW(k,IP))/dz1(k), detturb), .0002) ! dynamical detrainment rate (m^-1)
L06945            detrateUV= MIN(MAX(oow*(Wn-UPW(k,IP))/dz1(k), detturb), .0001) ! dynamical detrainment rate (m^-1) 
L06946            envm_thl(k)=envm_thl(k) + (p5*(thl_ent + UPTHL(k,IP)) - thl1(k))*detrate*aratio*MIN(dzp,dzpmax)
L06947            qv_ent = p5*(MAX(qt_ent-qc_ent,zero) + MAX(UPQT(k,IP)-UPQC(k,IP),zero))
L06948            envm_sqv(k)=envm_sqv(k) + (qv_ent-qv1(K))*detrate*aratio*MIN(dzp,dzpmax)
L06949            IF (UPQC(k,IP) > 1E-8) THEN
L06950               IF (qc1(k) > 1E-6) THEN
L06951                  qc_grid = qc1(k)
L06952               ELSE
L06953                  qc_grid = qc_bl1(K)
L06954               ENDIF
L06955               envm_sqc(k)=envm_sqc(k) + MAX(UPA(k,IP)*p5*(QCn + UPQC(k,IP)) - qc_grid, zero)*detrate*aratio*MIN(dzp,dzpmax)
L06956            ENDIF
L06957            envm_u(k)  =envm_u(k)   + (p5*(Un + UPU(k,IP)) - u1(K))*detrateUV*aratio*MIN(dzp,dzpmax)
L06958            envm_v(k)  =envm_v(k)   + (p5*(Vn + UPV(k,IP)) - v1(K))*detrateUV*aratio*MIN(dzp,dzpmax)
L06959  
L06960            IF (Wn > 0.) THEN
L06961               !Update plume variables at the k+1 index we just integrated to.
L06962               UPW(k+1,IP)=Wn  !sqrt(Wn2)
L06963               UPTHV(k+1,IP)=THVn
L06964               UPTHL(k+1,IP)=THLn
L06965               UPQT(k+1,IP)=QTn
L06966               UPQC(k+1,IP)=QCn
L06967               UPU(k+1,IP)=Un
L06968               UPV(k+1,IP)=Vn
L06969               UPQKE(k+1,IP)=QKEn
L06970               UPQSQ(k+1,IP)=QSQn
L06971               UPQNC(k+1,IP)=QNCn
L06972               UPQNI(k+1,IP)=QNIn
L06973               UPQNWFA(k+1,IP)=QNWFAn
L06974               UPQNIFA(K+1,IP)=QNIFAn
L06975               UPQNBCA(k+1,IP)=QNBCAn
L06976               UPA(k+1,IP)=UPA(K,IP)
L06977               if ( mix_chem ) then
L06978                 do ic = 1,nchem
L06979                   UPCHEM(k+1,ip,ic) = chemn(ic)
L06980                 enddo
L06981               endif
L06982               if ( scalar_opt > 0 ) then
L06983                 do ic = 1,nscalars
L06984                   upscalars(k+1,ip,ic) = scalarsn(ic)
L06985                 enddo
L06986               endif
L06987               ktop = MAX(ktop,k)
L06988            ELSE
L06989               if (debug_mf == 1 .and. i==idbg .and. j==jdbg) then
L06990                  print*,"plume #:",ip," ktop=",ktop
L06991                  print*,"area=",UPA(1:ktop,ip)
L06992                  print*,"w=",UPW(1:ktop,ip)
L06993               endif
L06994               exit  !exit k-loop
L06995            END IF
L06996         ENDDO !end k-loop
L06997  
L06998         IF (debug_mf == 1 .and. i==idbg .and. j==jdbg) THEN
L06999            IF (MAXVAL(UPW(:,IP)) > 10.0 .OR. MINVAL(UPA(:,IP)) < zero .OR. &
L07000                MAXVAL(UPA(:,IP)) > Atot .OR. NUP2 > 10) THEN
L07001               ! surface values
L07002               print *,'flq:',flq,' fltv:',fltv2,' Nup2=',Nup2
L07003               print *,'pblh:',pblh,' wstar:',wstar,' ktop=',ktop
L07004               print *,'sigmaW=',sigmaW,' sigmaTH=',sigmaTH,' sigmaQT=',sigmaQT
L07005               ! means
L07006               print *,'u:',u1
L07007               print *,'v:',v1
L07008               print *,'thl:',thl1
L07009               print *,'UPA:',UPA(:,IP)
L07010               print *,'UPW:',UPW(:,IP)
L07011               print *,'UPTHL:',UPTHL(:,IP)
L07012               print *,'UPQT:',UPQT(:,IP)
L07013               print *,'ENT:',ENT(:,ip)
L07014            ENDIF
L07015         ENDIF
L07016         ktop_plume(ip)=k !index where each individual plume stopped rising.
L07017         excess_h =max(excess_h,exc_heat)
L07018         excess_q =max(excess_q,exc_moist)
L07019      ENDDO !end plume # loop
L07020   ELSE
L07021      !At least one of the conditions was not met for activating the MF scheme.
L07022      NUP2=0.
L07023   END IF !end criteria check for mass-flux scheme
L07024  
L07025   ktop=MIN(ktop,KTE-1)
L07026   IF (ktop == 0) THEN
L07027      ztop = zero
L07028   ELSE
L07029      ztop = zw1(ktop)
L07030   ENDIF
```

> - **逐层积分**（每羽流独立）：线性卷入 `EntExp = ENT·dz`，`QTn/THLn/QKEn/… = UP·(1−EntExp) + 环境·EntExp`；**动量卷入只取 1/3**（`EntExm = EntExp^(1/3)`——气压梯度与扰动压强使动量混合弱于标量）；动量另有 `dxsa·pgfac·du` 气压梯度项（pgfac=0 关闭）。
> - **干湿判定**：`condensation_edmf(QTn, THLn, P, z, →THVn, QCn)`——羽流的饱和调整（§09b.7）。
> - **垂直速度方程**（TEMF 形式）：`Wn = w + (−2·ENT·w + BCOEFF·B/w)·min(dz,250)`——卷入减速 + 浮力加速；低速羽流（w<0.2）改用 `BCOEFF·B/max(w,0.2)` 防除零（BCOEFF 浮力>0 取 0.15、<0 取 0.2——**负浮力羽流减速更快**）；单层加速限 ±1.25 m/s per 200 m（粗网格放宽到 2.0）；`Wn` 钳 [0, 3]。
> - **羽流穿越（overshoot）**：w≤0 且首次出现时算 **Froude 数** `Frz = w/(bv·dz)`，羽流以 `dzp = dz·min(Frz,1)` 的份额穿入稳定层——**动能换位能的层内穿透**。
> - **动力夹带/环境修正**（Asai & Kasahara 1967）：`detrate = clamp(−0.06/w̄·(Wn−w_prev)/dz, 8e-5, 2e-4)`——羽流减速时把“羽流-环境差”按夹带率注入环境状态 `envm_*`（供 det 倾向用）；动量夹带率减半（detrateUV ≤ 1e-4）。
> - **羽流终止**：`Wn ≤ 0` 后退出 k 循环（记录 `ktop_plume(ip)`）；首层即死（w<1e-8）则整个 MF 关闭（nup2=0）。

<!-- code_extract code_extract.py v1.1
source: phys/MYNN-EDMF/module_bl_mynnedmf.F90
ranges: L7032-L7494
file_lines: 8776
file_md5: ec93fee9745a3e0b25be55a61b5aff8a
display: line-numbered (strip L-prefix and !file: line to restore)
range_md5: 7dcc9ed42ad3003bc8f1d0886c2802cb
seg_lines: 463
-->

```fortran
!file: phys/MYNN-EDMF/module_bl_mynnedmf.F90    L7032-L7494
L07032   IF (nup2 > 0) THEN
L07033      !Calculate the fluxes for each variable
L07034      !All s_aw* variable are == 0 at k=1
L07035      DO ip=1,NUP
L07036         DO k=kts,kte-1
L07037            s_aw1(k)   = s_aw1(k)    + rhoi(k)*UPA(K,ip)*UPW(K,ip)*Psig_w
L07038            s_awthl1(k)= s_awthl1(k) + rhoi(k)*UPA(K,ip)*UPW(K,ip)*UPTHL(K,ip)*Psig_w
L07039            s_awqt1(k) = s_awqt1(k)  + rhoi(k)*UPA(K,ip)*UPW(K,ip)*UPQT(K,ip)*Psig_w
L07040            !to conform to grid mean properties, move qc to qv in grid mean
L07041            !saturated layers, so total water fluxes are preserved but 
L07042            !negative qc fluxes in unsaturated layers is reduced.
L07043  !         if (qc1(k) > 1e-12 .or. qc1(k+1) > 1e-12) then
L07044               qc_plume = UPQC(K,ip)
L07045  !         else
L07046  !            qc_plume = zero
L07047  !         endif
L07048            s_awqc1(k) = s_awqc1(k)  + rhoi(k)*UPA(K,ip)*UPW(K,ip)*qc_plume*Psig_w
L07049            s_awqv1(k) = s_awqt1(k)  - s_awqc1(k)
L07050         ENDDO
L07051      ENDDO
L07052      !momentum
L07053      if (momentum_opt > 0) then
L07054         do ip=1,nup
L07055            do k=kts,kte-1
L07056               s_awu1(k) = s_awu1(k)   + rhoi(k)*UPA(K,ip)*UPW(K,ip)*UPU(K,ip)*Psig_w
L07057               s_awv1(k) = s_awv1(k)   + rhoi(k)*UPA(K,ip)*UPW(K,ip)*UPV(K,ip)*Psig_w
L07058            enddo
L07059         enddo
L07060      endif
L07061      !tke
L07062      if (tke_opt > 0) then
L07063         do ip=1,nup
L07064            do k=kts,kte-1
L07065               s_awqke1(k)= s_awqke1(k) + rhoi(k)*UPA(K,ip)*UPW(K,ip)*UPQKE(K,ip)*Psig_w
L07066            enddo
L07067         enddo
L07068         !qsq
L07069         if (bl_mynn_closure > 2.5) then
L07070            do ip=1,nup
L07071               do k=kts,kte-1
L07072                  s_awqsq1(k)= s_awqsq1(k) + rhoi(k)*UPA(K,ip)*UPW(K,ip)*UPQSQ(K,ip)*Psig_w
L07073               enddo
L07074            enddo
L07075         endif
L07076      endif
L07077      !chem
L07078      if ( mix_chem ) then
L07079         do k=kts,kte-1
L07080            do ip=1,nup
L07081               do ic = 1,nchem
L07082                  s_awchem1(k,ic) = s_awchem1(k,ic) + rhoi(k)*UPA(K,ip)*UPW(K,ip)*UPCHEM(K,ip,ic)*Psig_w
L07083               enddo
L07084            enddo
L07085         enddo
L07086      endif
L07087      !scalars
L07088      if ( scalar_opt > 0 ) then
L07089         do k=kts,kte-1
L07090            do ip=1,nup
L07091               do ic = 1,nscalars
L07092                  s_awscalars1(k,ic) = s_awscalars1(k,ic) + rhoi(k)*UPA(K,ip)*UPW(K,ip)*upscalars(k,ip,ic)*Psig_w
L07093               enddo
L07094            enddo
L07095         enddo
L07096      endif
L07097      if (numcon_opt > 0) then
L07098         do ip=1,nup
L07099            do k=kts,kte-1
L07100               s_awqnc1(k)  = s_awqnc1(k)   + rhoi(k)*UPA(K,ip)*UPW(K,ip)*UPQNC(K,ip)*Psig_w
L07101               s_awqni1(k)  = s_awqni1(k)   + rhoi(k)*UPA(K,ip)*UPW(K,ip)*UPQNI(K,ip)*Psig_w
L07102            enddo
L07103         enddo
L07104      endif
L07105      if (aerosol_opt > 0) then
L07106         do ip=1,nup
L07107            do k=kts,kte-1
L07108               s_awqnwfa1(k)= s_awqnwfa1(k) + rhoi(k)*UPA(K,ip)*UPW(K,ip)*UPQNWFA(K,ip)*Psig_w
L07109               s_awqnifa1(k)= s_awqnifa1(k) + rhoi(k)*UPA(K,ip)*UPW(K,ip)*UPQNIFA(K,ip)*Psig_w
L07110               s_awqnbca1(k)= s_awqnbca1(k) + rhoi(k)*UPA(K,ip)*UPW(K,ip)*UPQNBCA(K,ip)*Psig_w
L07111            enddo
L07112         enddo
L07113      endif
L07114  
L07115     !Flux limiter: Check ratio of heat flux at top of first model layer
L07116     !and at the surface. Make sure estimated flux out of the top of the
L07117     !layer is < fluxportion*surface_heat_flux
L07118     IF (abs(s_aw1(kts+1)) > 1e-8_kind_phys) THEN
L07119        flx1 = max(s_aw1(kts+1)*(thv1(kts)-thv1(kts+1))/dzi(kts+1),1.0e-6_kind_phys)
L07120     ELSE
L07121        flx1 = zero
L07122        !print*,"ERROR: s_aw(kts+1) == 0, NUP=",NUP," NUP2=",NUP2,&
L07123        !       " superadiabatic=",superadiabatic," KTOP=",KTOP
L07124     ENDIF
L07125     adjustment=one
L07126     flt2=max(fltv,zero)
L07127     !Print*,"Flux limiter in MYNN-EDMF, adjustment=",fluxportion*flt/dz(kts)/flx1
L07128     !Print*,"flt/dz=",flt/dz(kts)," flx1=",flx1," s_aw(kts+1)=",s_aw(kts+1)
L07129     IF (flx1 > fluxportion*flt2/dz1(kts) .AND. flx1>zero) THEN
L07130        adjustment = max(0.01, fluxportion*flt2/dz1(kts)/flx1)
L07131        s_aw1      = s_aw1*adjustment
L07132        s_awthl1   = s_awthl1*adjustment
L07133        s_awqt1    = s_awqt1*adjustment
L07134        s_awqc1    = s_awqc1*adjustment
L07135        s_awqv1    = s_awqv1*adjustment
L07136        if (numcon_opt > 0) then
L07137           s_awqnc1   = s_awqnc1*adjustment
L07138           s_awqni1   = s_awqni1*adjustment
L07139        endif
L07140        if (aerosol_opt > 0) then
L07141           s_awqnwfa1 = s_awqnwfa1*adjustment
L07142           s_awqnifa1 = s_awqnifa1*adjustment
L07143           s_awqnbca1 = s_awqnbca1*adjustment
L07144        endif
L07145        IF (momentum_opt > 0) THEN
L07146           s_awu1  = s_awu1*adjustment
L07147           s_awv1  = s_awv1*adjustment
L07148        ENDIF
L07149        IF (tke_opt > 0) THEN
L07150           s_awqke1= s_awqke1*adjustment
L07151           if (bl_mynn_closure>2.5) s_awqsq1= s_awqsq1*adjustment
L07152        ENDIF
L07153        IF ( mix_chem ) THEN
L07154           s_awchem1 = s_awchem1*adjustment
L07155        ENDIF
L07156        IF ( scalar_opt > 0 ) THEN
L07157           s_awscalars1 = s_awscalars1*adjustment
L07158        ENDIF
L07159        UPA = UPA*adjustment
L07160     ENDIF
L07161     if (debug_mf == 1 .and. i==idbg .and. j==jdbg) then
L07162        print*,"Flux adjustment:"
L07163        print*,"adjustment=",adjustment," fluxportion=",fluxportion
L07164        print*,"flt2=",flt2," flx1=",flx1
L07165     endif
L07166        
L07167     !Calculate mean updraft properties for output:
L07168     !all edmf_* variables are interpolated plume quantities to mass levels
L07169     k=kts !at first mass level, can not interpolate--use first interface values
L07170     do ip=1,nup
L07171        edmf_a1(k)  =edmf_a1(k)  +upa(k+1,ip)
L07172        edmf_w1(k)  =edmf_w1(k)  +upa(k+1,ip)*p5*UPW(k+1,ip)
L07173        edmf_qt1(k) =edmf_qt1(k) +upa(k+1,ip)*UPQT(k+1,ip)
L07174        edmf_thl1(k)=edmf_thl1(k)+upa(k+1,ip)*UPTHL(k+1,ip)
L07175        edmf_ent1(k)=edmf_ent1(k)+upa(k+1,ip)*ENT(k+1,ip)
L07176        edmf_qc1(k) =edmf_qc1(k) +upa(k+1,ip)*UPQC(k+1,ip)
L07177     enddo
L07178     do ip=1,nup
L07179        do k=kts+1,ktop_plume(ip)-1  !within the plume, we can interpolate:
L07180           upak        =(upa(k+1,ip)*dzi(k) + upa(k,ip)*dzi(k+1))/(dzi(k+1)+dzi(k))
L07181           edmf_a1(k)  =edmf_a1(k)  +upak
L07182           edmf_w1(k)  =edmf_w1(k)  +upak*(upw(k+1,ip)*dzi(k)  + upw(k,ip)*dzi(k+1))/(dzi(k+1)+dzi(k))
L07183           edmf_qt1(k) =edmf_qt1(k) +upak*(upqt(k+1,ip)*dzi(k) + upqt(k,ip)*dzi(k+1))/(dzi(k+1)+dzi(k))
L07184           edmf_thl1(k)=edmf_thl1(k)+upak*(upthl(k+1,ip)*dzi(k)+ upthl(k,ip)*dzi(k+1))/(dzi(k+1)+dzi(k))
L07185           edmf_ent1(k)=edmf_ent1(k)+upak*(ent(k+1,ip)*dzi(k)  + ent(k,ip)*dzi(k+1))/(dzi(k+1)+dzi(k))
L07186           if (abs(upqc(k,ip)) < 1e-10_kind_phys .and. upqc(k+1,ip) > zero) then
L07187              !mass at cloud base is kept equal to the interface value
L07188              edmf_qc1(k) =edmf_qc1(k) +upak*upqc(k+1,ip)
L07189           else
L07190              edmf_qc1(k) =edmf_qc1(k) +upak*(upqc(k+1,ip)*dzi(k) + upqc(k,ip)*dzi(k+1))/(dzi(k+1)+dzi(k))
L07191           endif
L07192        enddo
L07193     enddo
L07194     !Now use a single level at the top of the plume so there is no averaging with zeros above:
L07195     do ip=1,nup
L07196        k=ktop_plume(ip)
L07197        edmf_a1(k)  =edmf_a1(k)  +upa(k,ip)
L07198        edmf_w1(k)  =edmf_w1(k)  +upa(k,ip)*upw(k,ip)
L07199        edmf_qt1(k) =edmf_qt1(k) +upa(k,ip)*upqt(k,ip)
L07200        edmf_thl1(k)=edmf_thl1(k)+upa(k,ip)*upthl(k,ip)
L07201        edmf_ent1(k)=edmf_ent1(k)+upa(k,ip)*ent(k,ip)
L07202        edmf_qc1(k) =edmf_qc1(k) +upa(k,ip)*upqc(k,ip)
L07203     enddo
L07204     do k=kts,kte-1
L07205        !Note that only edmf_a1 is multiplied by Psig_w. This helps with the scale/regime-awareness.
L07206        if (edmf_a1(k)>0.) then
L07207           edmf_w1(k)  =edmf_w1(k)/edmf_a1(k)
L07208           edmf_qt1(k) =edmf_qt1(k)/edmf_a1(k)
L07209           edmf_thl1(k)=edmf_thl1(k)/edmf_a1(k)
L07210           edmf_ent1(k)=edmf_ent1(k)/edmf_a1(k)
L07211           edmf_qc1(k) =edmf_qc1(k)/edmf_a1(k)
L07212           edmf_a1(k)  =edmf_a1(k)*Psig_w
L07213        endif
L07214     enddo ! end k                                                                                                                                                                                     
L07215     do k=kts,kte-1
L07216        !FIND MAXIMUM MASS-FLUX IN THE COLUMN:
L07217        if(edmf_a1(k)*edmf_w1(k) > maxmf) maxmf = edmf_a1(k)*edmf_w1(k)
L07218        !tke production by udrafts
L07219        !instead of dTKE/dt = 1/2 w^3, multiply by 2 for QKE.
L07220        tkeprod_up(k)=(abs(edmf_w1(k))**3)*edmf_a1(k)/(b1*max(p5*(el1(k)+el1(k+1)),0.1)) 
L07221     enddo
L07222  
L07223     !smoke/chem
L07224     if ( mix_chem ) then
L07225        do k=kts,kte-1
L07226          do ip=1,nup
L07227            do ic = 1,nchem
L07228              upak 	    =(upa(k+1,ip)*dzi(k) + upa(k,ip)*dzi(k+1))/(dzi(k+1)+dzi(k))
L07229              edmf_chem(k,ic) = edmf_chem(k,ic) + upak*(upchem(k+1,ip,ic)*dzi(k) + upchem(k,ip,ic)*dzi(k+1))/(dzi(k+1)+dzi(k))
L07230            enddo
L07231          enddo
L07232        enddo
L07233        do k=kts,kte-1
L07234           if (edmf_a1(k)>0.) then
L07235              do ic = 1,nchem
L07236                 edmf_chem(k,ic) = edmf_chem(k,ic)/edmf_a1(k)
L07237              enddo
L07238           endif
L07239        enddo
L07240     endif
L07241     
L07242     !Calculate the effects environmental subsidence.
L07243     !All envi_*variables are valid at the interfaces, like the edmf_* variables
L07244     IF (env_subs) THEN
L07245        DO k=kts+1,kte-1
L07246           !First, smooth the profiles of w & a, since sharp vertical gradients
L07247           !in plume variables are not likely extended to env variables
L07248           !Note1: w is treated as negative further below
L07249           !Note2: both w & a will be transformed into env variables further below
L07250           envi_w(k) = p333*(edmf_w1(k-1)+edmf_w1(k)+edmf_w1(k+1))
L07251           envi_a(k) = p333*(edmf_a1(k-1)+edmf_a1(k)+edmf_a1(k+1))*adjustment
L07252        ENDDO
L07253        !define env variables at k=1 (top of first model layer)
L07254        envi_w(kts) = edmf_w1(kts)
L07255        envi_a(kts) = edmf_a1(kts)
L07256        !define env variables at k=kte
L07257        envi_w(kte) = zero
L07258        envi_a(kte) = edmf_a1(kte)
L07259        !define env variables at k=kte+1
L07260        envi_w(kte+1) = zero
L07261        envi_a(kte+1) = edmf_a1(kte)
L07262        !Add limiter for very long time steps (i.e. dt > 300 s)
L07263        !Note that this is not a robust check - only for violations in
L07264        !   the first model level.
L07265        IF (envi_w(kts) > 0.9*dz1(kts)/dt) THEN
L07266           sublim = 0.9*dz1(kts)/dt/envi_w(kts)
L07267        ELSE
L07268           sublim = one
L07269        ENDIF
L07270        !Transform w & a into env variables
L07271        DO k=kts,kte
L07272           temp=envi_a(k)
L07273           envi_a(k)=one-temp
L07274           envi_w(k)=csub*sublim*envi_w(k)*temp/(1.-temp)
L07275        ENDDO
L07276        !calculate tendencies from subsidence and detrainment valid at the middle of
L07277        !each model layer. The lowest model layer uses an assumes w=0 at the surface.
L07278        sub_thl1(kts)= 0.5*envi_w(kts)*envi_a(kts)*                               &
L07279                       (rho1(kts+1)*thl1(kts+1)-rho1(kts)*thl1(kts))/dzi(kts)/rhoi(kts)
L07280        sub_sqv1(kts)= 0.5*envi_w(kts)*envi_a(kts)*                               &
L07281                       (rho1(kts+1)*qv1(kts+1)-rho1(kts)*qv1(kts))/dzi(kts)/rhoi(kts)
L07282        DO k=kts+1,kte-1
L07283           dzi(k)     = 0.5*(dz1(k)+dz1(k+1))
L07284           sub_thl1(k)= 0.5*(envi_w(k)+envi_w(k-1))*0.5*(envi_a(k)+envi_a(k-1)) * &
L07285                        (rho1(k+1)*thl1(k+1)-rho1(k)*thl1(k))/dzi(k)/rhoi(k)
L07286           sub_sqv1(k)= 0.5*(envi_w(k)+envi_w(k-1))*0.5*(envi_a(k)+envi_a(k-1)) * &
L07287                        (rho1(k+1)*qv1(k+1)-rho1(k)*qv1(k))/dzi(k)/rhoi(k)
L07288        ENDDO
L07289  
L07290        DO k=kts,KTE-1
L07291           det_thl1(k)=Cdet*(envm_thl(k)-thl1(k))*envi_a(k)*Psig_w
L07292           det_sqv1(k)=Cdet*(envm_sqv(k)-qv1(k))*envi_a(k)*Psig_w
L07293           det_sqc1(k)=Cdet*(envm_sqc(k)-qc1(k))*envi_a(k)*Psig_w
L07294        ENDDO
L07295  
L07296        IF (momentum_opt > 0) THEN
L07297           sub_u1(kts)=0.5*envi_w(kts)*envi_a(kts)*                               &
L07298                       (rho1(kts+1)*u1(kts+1)-rho1(kts)*u1(kts))/dzi(kts)/rhoi(kts)
L07299           sub_v1(kts)=0.5*envi_w(kts)*envi_a(kts)*                               &
L07300                       (rho1(kts+1)*v1(kts+1)-rho1(kts)*v1(kts))/dzi(kts)/rhoi(kts)
L07301           DO k=kts+1,kte-1
L07302              sub_u1(k)=0.5*(envi_w(k)+envi_w(k-1))*0.5*(envi_a(k)+envi_a(k-1)) * &
L07303                         (rho1(k+1)*u1(k+1)-rho1(k)*u1(k))/dzi(k)/rhoi(k)
L07304              sub_v1(k)=0.5*(envi_w(k)+envi_w(k-1))*0.5*(envi_a(k)+envi_a(k-1)) * &
L07305                         (rho1(k+1)*v1(k+1)-rho1(k)*v1(k))/dzi(k)/rhoi(k)
L07306           ENDDO
L07307  
L07308           DO k=kts,KTE-1
L07309             det_u1(k) = Cdet*(envm_u(k)-u1(k))*envi_a(k)*Psig_w
L07310             det_v1(k) = Cdet*(envm_v(k)-v1(k))*envi_a(k)*Psig_w
L07311           ENDDO
L07312         ENDIF
L07313     ENDIF !end subsidence/env detranment
L07314  
L07315     !First, compute plume theta & total water at interfaces (qti)
L07316     !These values do not need to be defined at k=kte (unused level).
L07317     DO k=kts,kte-1
L07318        edmf_th1(k)= edmf_thl1(k) + xlvcp/ex1(k)*edmf_qc1(K)
L07319        qti(k+1)   =(qt1(k)*dz1(k+1)+qt1(k+1)*dz1(k))/(dz1(k+1)+dz1(k))
L07320     ENDDO
L07321     qti(kts)=qt1(kts)
L07322     
L07323  !update CLDFRA_bl1, qc_bl1. They have already been defined in
L07324  !     mym_condensation. Here, a shallow-cu component is added, but no cumulus
L07325  !     clouds can be added at k=1 (start loop at k=2).
L07326     cb_check = 0
L07327     do k=kts+1,kte-2
L07328        if (k > KTOP) exit
L07329        if (edmf_qc1(k) > zero ) then !.and. (cldfra_bl1(k) < cf_thresh))THEN
L07330           if (cb_check == 0) then
L07331              mf_at_cb = edmf_a1(k)*edmf_w1(k)
L07332              cb_check = 1
L07333            endif
L07334            !plume properties within mass layers.
L07335            Aup = edmf_a1(k)
L07336            THp = edmf_th1(k)
L07337            QTp = edmf_qt1(k)
L07338            QCp = edmf_qc1(k)
L07339            dqwdz = (qti(k)-qti(k+1))/dz1(k) !pos = decreasing upward
L07340            !convert TH to T
L07341            !t = THp*exner(k)
L07342            !SATURATED VAPOR PRESSURE
L07343            esat = esat_blend(tk1(k))
L07344            !SATURATED SPECIFIC HUMIDITY
L07345            qsl=ep_2*esat/max(1.e-7_kind_phys,(pres1(k)-ep_3*esat)) 
L07346  
L07347            !COMPUTE CLDFRA & QC_BL FROM MASS-FLUX SCHEME and recompute vt & vq
L07348            xl = xl_blend(tk1(k))               ! obtain blended heat capacity
L07349            qsat_tk = qsat_blend(tk1(k),pres1(k))! get saturation water vapor mixing ratio
L07350                                                !   at t and p
L07351            rsl = xl*qsat_tk / (r_v*tk1(k)**2)  ! slope of C-C curve at t (abs temp)
L07352                                                ! CB02, Eqn. 4
L07353            cpm = cp + qt1(k)*cpv               ! CB02, sec. 2, para. 1
L07354            a   = one/(one + xl*rsl/cpm)        ! CB02 variable "a"
L07355            b9  = a*rsl                         ! CB02 variable "b" 
L07356  
L07357            q2p = xlvcp/ex1(k)
L07358            pt  = thl1(k) +q2p*QCp*Aup ! potential temp (env + plume)
L07359            bb  = b9*tk1(k)/pt ! bb is "b9" in BCMT95.  Their "b9" differs from
L07360                               ! "b9" in CB02 by a factor
L07361                               ! of T/theta.  Strictly, b9 above is formulated in
L07362                               ! terms of sat. mixing ratio, but bb in BCMT95 is
L07363                               ! cast in terms of sat. specific humidity.  The
L07364                               ! conversion is neglected here.
L07365            qww   = one+p608*qt1(k)
L07366            alpha = p608*pt
L07367            beta  = pt*xl/(tk1(k)*cp) - 1.61_kind_phys*pt
L07368            !Buoyancy flux terms have been moved to the end of this section...
L07369  
L07370            !Now calculate convective component of the cloud fraction:
L07371            if (a > zero) then
L07372               f = MIN(one/a, four)      ! f is vertical profile scaling function (CB2005)
L07373            else
L07374               f = one
L07375            endif
L07376  
L07377            !---CB form:
L07378            !sigq = 3.5E-3 * Aup * edmf_w1(k) * f  ! convective component of sigma (CB2005)
L07379            !sigq = SQRT(sigq**2 + sgm1(k)**2)     ! combined conv + stratus components
L07380  
L07381            !---Per S.DeRoode 2009?
L07382            !sigq = nine * Aup * (QTp - qt1(k))
L07383  
L07384            !---Extended CB form, tauc is timescale similar to the eddy turnover timescale.
L07385            tauc = 1800._kind_phys
L07386            sigq = five * Aup * edmf_w1(k) * max(4e-3_kind_phys, tauc*max(zero, dqwdz))
L07387  
L07388            !constrain sigq wrt saturation:
L07389            !sigq = max(sigq, qsat_tk*0.03_kind_phys)
L07390            !constrain sigq wrt moisture excess in the updraft (deRoode)
L07391            sigq = max(sigq, three * Aup * (QTp - qt1(k)))
L07392            !sigq = SQRT(sigq**2 + sgm1(k)**2)     ! combined conv + stratus components
L07393            !sigq = max(sigq, sgm1(k))             ! use max of conv + stratus components
L07394  
L07395            !qmq = a * (qt1(k) - qsat_tk)          ! saturation deficit/excess;
L07396            qmq = qt1(k) - qsat_tk                ! saturation deficit/excess;
L07397            if (qmq > zero) sigq = min(qsat_tk*0.015_kind_phys, sigq)
L07398            Q1  = qmq/sigq                        !   the numerator of Q1
L07399  
L07400            if ((landsea-1.5).GE.zero) then   ! WATER
L07401               !modified form from LES
L07402               !cf_mf = min(max(0.5 + 0.36 * atan(1.20*(Q1+0.2)),0.01),0.6)
L07403               !Original CB
L07404               !cf_mf = min(max(p5 + 0.36_kind_phys * atan(1.55*Q1),0.01_kind_phys),0.8_kind_phys)
L07405               !increase cf in cases of large mf at cloudbase
L07406               cffac = min(max(zero, mf_at_cb - 0.05_kind_phys)/0.05_kind_phys, one)
L07407               cf_mf = min(max(p5 + 0.36_kind_phys * atan(1.8_kind_phys*(Q1+p2+cffac)),0.01_kind_phys), one)
L07408               cf_mf = max(cf_mf, 1.2_kind_phys * Aup)
L07409               !cf_mf = max(cf_mf, 1.8_kind_phys * Aup)
L07410               !cf_mf = min(cf_mf, 5.0 * Aup)
L07411            else                              ! LAND
L07412               !LES form
L07413               !cf_mf = min(max(0.5 + 0.36 * atan(1.20*(Q1+0.4)),0.01),0.6)
L07414               !Original CB
L07415               !cf_mf = min(max(p5 + 0.36_kind_phys * atan(1.55*Q1),0.01_kind_phys),0.8_kind_phys
L07416               cf_mf = min(max(p5 + 0.36_kind_phys * atan(1.8_kind_phys*(Q1+p2)),0.01_kind_phys), one)
L07417               cf_mf = max(cf_mf, 1.8_kind_phys * Aup)
L07418               !cf_mf = min(cf_mf, 5.0 * Aup)
L07419            endif
L07420  
L07421            !if ( debug_mf == 1 .and. i==idbg .and. j==jdbg) then
L07422            !   print*,"In MYNN-MF, macrophysics component"
L07423            !   print*," env qt=",qt1(k)," qsat=",qsat_tk
L07424            !   print*," k=",k," satdef=",QTp - qsat_tk," sgm=",sgm1(k)
L07425            !   print*," sigq=",sigq," qmq=",qmq," tk=",tk1(k)
L07426            !   print*," cf_mf=",cf_mf," cldfra_bl=",cldfra_bl1(k)," edmf_a1=",edmf_a1(k)
L07427            !endif
L07428  
L07429            !Update cloud fractions and specific humidities in grid cells
L07430            !where the mass-flux scheme is active. The specific humidities
L07431            !are converted to grid means (not in-cloud quantities).
L07432            qcfac = 1.20_kind_phys + 1.0_kind_phys*min(max(zero, mf_at_cb - 0.04_kind_phys)/0.05_kind_phys, one)
L07433            if ((landsea-1.5).GE.zero) then  ! water
L07434               !if (QCp * Aup > 5e-5) then
L07435               !   qc_mf     = 1.86_kind_phys * (QCp * Aup) - 2.2e-5_kind_phys
L07436               !else
L07437               !   qc_mf     = 1.20_kind_phys * (QCp * Aup)
L07438               !endif
L07439               qc_mf     = qcfac * (QCp * Aup) 
L07440            else                             ! land
L07441               if (QCp * Aup > 5e-5) then
L07442                  qc_mf     = 1.86_kind_phys * (QCp * Aup) - 2.2e-5_kind_phys
L07443               else
L07444                  qc_mf     = 1.20_kind_phys * (QCp * Aup)
L07445               endif
L07446            endif
L07447              !In the condition of very large cloud fractions, where the instantaneous
L07448              !condensed water in the plume is not a reasonable estimate of the
L07449              !mixing ratio in a larger cloud, we must rely on a background estimate based
L07450              !off of environmental qsat.
L07451              wt2          = one - min(one, max(zero, (cf_mf - thirty))/(hundred-thirty))  !=1 for low cf_mf, =0 for cf_mf = 1.0
L07452              qc_mf_min    = wt2*qsat_tk*0.01_kind_phys*cf_mf + (one-wt2)*qsat_tk*0.025_kind_phys*cf_mf
L07453              qc_mf        = max(qc_mf, qc_mf_min)
L07454              !Then blend with the stratus component:
L07455              cf_strat     = cldfra_bl1(k)
L07456              qc_strat     = qc_bl1(k)
L07457              cldfra_bl1(k)= max(cf_mf, cf_strat)
L07458              pct_mf       = cf_mf/cldfra_bl1(k)
L07459              qc_bl1(k)    = qc_mf*pct_mf + (one-pct_mf)*qc_strat
L07460  
L07461              !Now recalculate the terms for the buoyancy flux for mass-flux clouds:
L07462              !See mym_condensation for details on these formulations.
L07463              !Use Bechtold and Siebesma (1998) piecewise estimation of Fng with 
L07464              !limits ,since they really should be recalculated after all the other changes...:
L07465              !Only overwrite vt & vq in non-stratus condition
L07466              !if ((landsea-1.5).GE.zero) then      ! WATER
L07467                 Q1=max(Q1,-2.25)
L07468              !else
L07469              !   Q1=max(Q1,-2.0)
L07470              !endif
L07471  
L07472              if (Q1 .ge. one) then
L07473                 Fng = one
L07474              elseif (Q1 .ge. -1.7 .and. Q1 .lt. one) then
L07475                 Fng = EXP(-p4*(Q1-one))
L07476              elseif (Q1 .ge. -2.5 .and. Q1 .lt. -1.7) then
L07477                 Fng = three + EXP(-3.8*(Q1+1.7))
L07478              else
L07479                 Fng = min(23.9 + EXP(-1.6*(Q1+2.5)), 60.)
L07480              endif
L07481  
L07482              !link the buoyancy flux function to active clouds only (c*Aup):
L07483              vt1(k) = qww   - (1.5*Aup)*beta*bb*Fng - one
L07484              vq1(k) = alpha + (1.5*Aup)*beta*a*Fng  - tv0
L07485           endif !check for (qc in plume) .and. (cldfra_bl < threshold)
L07486        enddo !k-loop
L07487  
L07488  ENDIF  !end nup2 > 0
L07489  
L07490  !modify output (negative: dry plume, positive: moist plume)
L07491  if (ktop > 0) then
L07492     maxqc = maxval(edmf_qc1(1:ktop)) 
L07493     if ( maxqc < 1.E-8) maxmf = -1.*maxmf
L07494  endif
```

> - **通量装配**：`s_awφ(k) = Σ_ip ρ·a·w·φ·Psig_w`——**八个羽流的加权和就是隐式求解器需要的“非局地通量系数”**（回到 code_09a §09a.10 的 a/b/c 项）；qc/qv 通量的拆法保证总水守恒（`s_awqv = s_awqt − s_awqc`）。
> - **通量限制器**（L7115–L7160）：首层 MF 热通量 `flx1 = s_aw(kts+1)·Δθ_v/dzi` 超过 `0.75·fltv/dz` 时**整柱所有 s_aw*（含面积 UPA）乘同一 adjustment**——等比缩放保结构（与 Thompson 守恒段同一思想）。
> - **平均上升流属性**（输出诊断 edmf_a1/w1/qt1/thl1/ent1/qc1）：羽流内插值到质量层（面密度加权）、云底特殊处理（`UPQC(k)<1e-10` 时用界面值防零平均）、顶用单层防与零平均；`edmf_a1` 单独乘 Psig_w（注释：只有面积乘，属性不乘——**尺度感知只作用在权重上**）。
> - **TKE 生产**：`tkeprod_up = w³·a/(b1·el)`——注释：dTKE/dt = ½w³（对流 TKE 通量的经典标度）乘 2 换成 QKE 口径。
> - **MF 云量宏物理**（L7323–L7459，`nup2>0` 时）：在羽流有 qc 的层——①σ 的 MF 分量 `sigq = 5·a·w·max(4e-3, 1800·dqwdz)`（扩展 CB05：1800 s 涡翻转时间 × 总水梯度），下限 `3·a·(QTp−qt)`（S. de Roode 建议的羽流过饱和度）；②云量 `cf_mf = 0.5+0.36·atan(1.8·(Q1+0.5+cffac))`（水面 cffac 由云底 MF 增强）、下限 `1.2(水)/1.8(陆)·Aup`；③云水 `qc_mf = qcfac·(QCp·Aup)`（陆面大值区 1.86 倍线性式）、下限 `qsat·(1~2.5%)·cf_mf`（大云量时靠环境饱和比的背景估计）；④与层云分量**取大合并云量、按份额加权云水**；⑤**vt/vq 重算**（Fng 分段函数再现，系数改 1.5·Aup 权重）。
> - **干羽流标记**：`maxqc < 1e-8` 时 `maxmf = −maxmf`（输出负号=干羽流，诊断用）。

## 09b.7 `condensation_edmf` 三件：羽流的饱和调整

<!-- code_extract code_extract.py v1.1
source: phys/MYNN-EDMF/module_bl_mynnedmf.F90
ranges: L7545-L7601
file_lines: 8776
file_md5: ec93fee9745a3e0b25be55a61b5aff8a
display: line-numbered (strip L-prefix and !file: line to restore)
range_md5: 9b036fbbac14d04d43474f507b5b41e8
seg_lines: 57
-->

```fortran
!file: phys/MYNN-EDMF/module_bl_mynnedmf.F90    L7545-L7601
L07545  subroutine condensation_edmf(QT,THL,P,zagl,THV,QC)
L07546  !
L07547  ! zero or one condensation for edmf: calculates THV and QC
L07548  !
L07549    use module_bl_mynnedmf_common, only: p1000mb,xlvcp,rcp,rvovrd,&
L07550         zero,one,p5,kind_phys
L07551    
L07552  real(kind_phys),intent(in)   :: QT,THL,P,zagl
L07553  real(kind_phys),intent(inout):: THV
L07554  real(kind_phys),intent(inout):: QC
L07555  
L07556  integer :: niter,ni
L07557  real(kind_phys):: diff,exn,t,th,qs,qcold
L07558  
L07559  ! constants used from module_model_constants.F
L07560  ! p1000mb
L07561  ! rcp ... Rd/cp
L07562  ! xlv ... latent heat for water (2.5e6)
L07563  ! cp
L07564  ! rvord .. r_v/r_d  (1.6) 
L07565  
L07566  ! number of iterations
L07567    niter=50
L07568  ! minimum difference (usually converges in < 8 iterations with diff = 2e-5)
L07569    diff=1.e-6_kind_phys
L07570  
L07571    EXN=(P/p1000mb)**rcp
L07572    QC=zero  !better first guess QC is incoming from lower level, do not set to zero
L07573    do ni=1,NITER
L07574       T=EXN*THL + xlvcp/EXN*QC
L07575       QS=qsat_blend(T,P)
L07576       QCOLD=QC
L07577       QC=p5*QC + p5*MAX((QT-QS),zero)
L07578       if (abs(QC-QCOLD)<Diff) exit
L07579    enddo
L07580  
L07581    T=EXN*THL + xlvcp/EXN*QC
L07582    QS=qsat_blend(T,P)
L07583    QC=max(QT-QS,zero)
L07584  
L07585    !Do not allow saturation below 100 m
L07586    if(zagl < 100.)QC=zero
L07587  
L07588    !THV=(THL+xlv/cp*QC).*(1+(1-rvovrd)*(QT-QC)-QC);
L07589    THV=(THL+xlvcp/EXN*QC)*(one+QT*(rvovrd-one)-rvovrd*QC)
L07590  
L07591  !  IF (QC > zero) THEN
L07592  !    PRINT*,"EDMF SAT, p:",p," iterations:",ni
L07593  !    PRINT*," T=",T," THL=",THL," THV=",THV
L07594  !    PRINT*," QS=",QS," QT=",QT," QC=",QC,"ratio=",qc/qs
L07595  !  ENDIF
L07596  
L07597    !THIS BASICALLY GIVES THE SAME RESULT AS THE PREVIOUS LINE
L07598    !TH = THL + xlvcp/EXN*QC
L07599    !THV= TH*(1. + p608*QT - QC)
L07600  
L07601  end subroutine condensation_edmf
```

> - **不动点迭代**（非牛顿）：`T = exn·THL + xlvcp/exn·QC` → `QS = qsat_blend(T,P)` → `QC = ½·QC + ½·max(QT−QS, 0)`——**半隐式松弛**（比直接 `QC = QT−QS` 稳定），50 次上限、收敛 1e-6（注释：<8 次收敛）；迭代后再做一次显式步定稿。
> - **100 m 以下禁饱和**（`zagl<100 → QC=0`）——贴地层云的数值卫生。
> - **虚位温重建**：`THV = (THL + xlvcp/exn·QC)·(1 + QT·(rvovrd−1) − rvovrd·QC)`——** rvovrd = 1.6**（Rv/Rd），书 (2.2.10) 虚温订正的位温形态（对照：`1+0.608qv−qc` 的比湿版本）。

<!-- code_extract code_extract.py v1.1
source: phys/MYNN-EDMF/module_bl_mynnedmf.F90
ranges: L7604-L7678
file_lines: 8776
file_md5: ec93fee9745a3e0b25be55a61b5aff8a
display: line-numbered (strip L-prefix and !file: line to restore)
range_md5: 684d7a2543ec7c0a0cb60aaad84ff170
seg_lines: 75
-->

```fortran
!file: phys/MYNN-EDMF/module_bl_mynnedmf.F90    L7604-L7678
L07604  subroutine condensation_ddmf(qt,thl,p,zagl,thv,qc,qi,debug_dd)
L07605  !
L07606  ! zero or one condensation for edmf: calculates thv, qc, and qi
L07607  !
L07608    use module_bl_mynnedmf_common, only: p1000mb,xlvcp,xlscp,rcp, &
L07609         rvovrd,p608,zero,one,p5,kind_phys
L07610    
L07611  real(kind_phys),intent(in)   :: qt,thl,p,zagl
L07612  real(kind_phys),intent(inout):: thv,qc,qi
L07613  
L07614  integer :: niter,ni,debug_dd
L07615  real(kind_phys):: diff,exn,t,th,qs,qx,qxold,frac_ice,frac_liq,thvin
L07616  
L07617  ! number of iterations
L07618    niter=50
L07619  ! minimum difference (usually converges in < 8 iterations with diff = 2e-5)
L07620    diff=1.e-6
L07621  
L07622    if ((qi+qc) .gt. zero) then
L07623       frac_ice = qi/(qi+qc)
L07624       frac_liq = one - frac_ice
L07625    else
L07626       frac_ice = zero
L07627       frac_liq = zero
L07628    endif
L07629  
L07630    if (debug_dd == 1) then
L07631       thvin = thv
L07632       print*,"------- in consensation_ddmf-------------"
L07633       print*,"input qc=",qc," qi=",qi," frac_liq=",frac_liq
L07634    endif
L07635  
L07636    exn=(p/p1000mb)**rcp
L07637    do ni=1,niter
L07638       t=exn*thl + xlvcp/exn*qc + xlscp/exn*qi
L07639       qs=qsat_blend(t,p)
L07640       qxold=qc+qi
L07641       qx=qc+qi
L07642       qx=p5*qx + p5*max((qt-qs),zero)
L07643       qc=frac_liq*qx
L07644       qi=frac_ice*qx
L07645       if (abs(qx-qxold)<diff) exit
L07646    enddo
L07647  
L07648    t=exn*thl + xlvcp/exn*qc + xlscp/exn*qi
L07649    qs=qsat_blend(t,p)
L07650    qx=max(qt-qs,zero)
L07651    qc=frac_liq*qx
L07652    qi=frac_ice*qx
L07653  
L07654    !thv=(thl+xlv/cp*qc).*(1+(1-rvovrd)*(qt-qc)-qc)
L07655  !was this: thv=(thl+xlvcp*qc)*(1.+qt*(rvovrd-1.)-rvovrd*qc)
L07656    !thv=(thl + xlvcp*qc + xlscp*qi)*(1. + qt*(rvovrd-1.)-rvovrd*qc)
L07657    thv=(thl + xlvcp/exn*qc + xlscp/exn*qi)*(one + p608*(qt-qx) - qx)
L07658  
L07659  !  if (qc > zero) then
L07660  !    print*,"edmf sat, p:",p," iterations:",ni
L07661  !    print*," t=",t," thl=",thl," thv=",thv
L07662  !    print*," qs=",qs," qt=",qt," qc=",qc,"ratio=",qc/qs
L07663  !  endif
L07664  
L07665    !this basically give the same result as the previous line
L07666    !th = thl + xlv/cp/exn*qc
L07667    !thv= th*(1. + p608*qt)
L07668  
L07669    !print *,'t,p,qt,qs,qc'
L07670    !print *,t,p,qt,qs,qc
L07671  
L07672    if (debug_dd == 1) then
L07673       print*,"output qc=",qc," qi=",qi," frac_liq=",frac_liq
L07674       print*,"input thv=",thvin," out thv=",thv," diff=",thv-thvin
L07675       print*,"------- exiting consensation_ddmf----------"
L07676    endif
L07677  
L07678  end subroutine condensation_ddmf
```

> **_ddmf**（下沉流版）：混合相——冰/液份额由入场 qc/qi 比例冻结（`frac_ice`），总凝结 `qx` 按 50/50 松弛迭代后按份额分拆；虚位温式含冰（`xlscp/exn·qi` 项）与降水物订正（`(qt−qx)`）。

<!-- code_extract code_extract.py v1.1
source: phys/MYNN-EDMF/module_bl_mynnedmf.F90
ranges: L7682-L7718
file_lines: 8776
file_md5: ec93fee9745a3e0b25be55a61b5aff8a
display: line-numbered (strip L-prefix and !file: line to restore)
range_md5: e16a2a31accd7b4be72ffc0eef2468af
seg_lines: 37
-->

```fortran
!file: phys/MYNN-EDMF/module_bl_mynnedmf.F90    L7682-L7718
L07682  subroutine condensation_edmf_r(QT,THL,P,zagl,THV,QC)
L07683  !                                                                                                
L07684  ! zero or one condensation for edmf: calculates THL and QC                                       
L07685  ! similar to condensation_edmf but with different inputs                                         
L07686  !
L07687    use module_bl_mynnedmf_common, only: p1000mb,rcp,rvovrd,xlvcp,&
L07688         one,zero,kind_phys
L07689    
L07690  real(kind_phys),intent(in)   :: QT,THV,P,zagl
L07691  real(kind_phys),intent(inout):: THL, QC
L07692  
L07693  integer :: niter,ni
L07694  real(kind_phys):: diff,exn,t,th,qs,qcold
L07695  
L07696  ! number of iterations                                                                           
L07697    niter=50
L07698  ! minimum difference                                                                             
L07699    diff=2.e-5_kind_phys
L07700  
L07701    EXN=(P/p1000mb)**rcp
L07702    ! assume first that th = thv                                                                   
L07703    T = THV*EXN
L07704    !QS = qsat_blend(T,P)                                                                          
L07705    !QC = QS - QT                                                                                  
L07706  
L07707    QC=zero
L07708  
L07709    do ni=1,NITER
L07710       QCOLD = QC
L07711       T = EXN*THV/(one+QT*(rvovrd-one)-rvovrd*QC)
L07712       QS=qsat_blend(T,P)
L07713       QC= MAX((QT-QS), zero)
L07714       if (abs(QC-QCOLD)<Diff) exit
L07715    enddo
L07716    THL = (T - xlvcp*QC)/EXN
L07717  
L07718  end subroutine condensation_edmf_r
```

> **_r**（反解版）：输入 THV/QT 反解 THL/QC——被注释掉的调用可见于 ddmp_mf 初始化（现行用显式 def_th 扰动替代）。同样 50 次不动点。

## 09b.8 `ddmp_mf`：辐射冷却驱动的下沉流

<!-- code_extract code_extract.py v1.1
source: phys/MYNN-EDMF/module_bl_mynnedmf.F90
ranges: L7720-L7838
file_lines: 8776
file_md5: ec93fee9745a3e0b25be55a61b5aff8a
display: line-numbered (strip L-prefix and !file: line to restore)
range_md5: d5558d0ae12ce6fdc80135fd7502e914
seg_lines: 119
-->

```fortran
!file: phys/MYNN-EDMF/module_bl_mynnedmf.F90    L7720-L7838
L07720  !===============================================================
L07721  ! ddmp_mf is a downdraft mass flux scheme - analogous to the updrafts but
L07722  ! flipped upsidedown and revised to be more specific for turbulence
L07723  ! driven by radiative cooling at cloud tops. this scheme has been primarily
L07724  ! designed for stratocumulus cloud conditions. This is based off of a
L07725  ! combination of the original scheme [Wu et al. (2020, MWR)] but several
L07726  ! modifications were made to better fit it in the MYNN-EDMF and to
L07727  ! help the coupling to the Thompson microphysics scheme. Some of the
L07728  ! primary design changes include:
L07729  !                                                                                                                                                                      
L07730  ! 1) the spectral plume design, similar to the MYNNs updraft scheme
L07731  ! 2) generalized to any cloud, not just PBL-topped clouds
L07732  ! 3) always initialized at the cloud top
L07733  ! 4) can penetrate all the way to the surface
L07734  ! 5) generalized for mixed-phase clouds
L07735  ! 6) mixes number concentration for double moment schemes
L07736  ! 7) mixes aerosols
L07737  ! 8) revised the conection to the solver
L07738  
L07739  subroutine ddmp_mf(kts,kte,dt,dx,zw,dz,p,            &
L07740                &u,v,th,thl,thv,tk,qt,qv,qc,qi,        &
L07741                &qnc,qni,qnwfa,qnifa,                  &
L07742                &qke,rho,exner,                        &
L07743                &qc_bl1,qi_bl1,cldfra_bl1,             &
L07744                &ust,flt,flq,fltv,pblh,kpbl,           &
L07745                &edmf_a_dd,edmf_w_dd, edmf_qt_dd,      &
L07746                &edmf_thl_dd,edmf_ent_dd,edmf_qc_dd,   &
L07747                &sd_aw,sd_awthl,sd_awqt,               &
L07748                &sd_awqv,sd_awqc,sd_awqi,              &
L07749                &sd_awqnc,sd_awqni,                    &
L07750                &sd_awqnwfa,sd_awqnifa,                &
L07751                &sd_awu,sd_awv,sd_awqke,               &
L07752                &tkeprod_dn,el,                        &
L07753                &rthraten,psig,                        &
L07754                &maxmf_dd,maxwidth_dd                  )
L07755  
L07756    use module_bl_mynnedmf_common, only: cp,grav,p608, &
L07757         xlvcp,b1,one,two,zero,eight,p1,p2,p333,p5,    &
L07758         p666,kind_phys
L07759  
L07760          integer, intent(in) :: kts,kte,kpbl
L07761          real(kind_phys), dimension(kts:kte), intent(in) ::            &
L07762              u,v,th,thl,tk,qt,qv,qc,qi,thv,p,qke,rho,exner,            &
L07763              qnc,qni,qnwfa,qnifa,dz,qc_bl1,qi_bl1,cldfra_bl1,el
L07764          real(kind_phys), dimension(kts:kte), intent(in) :: rthraten
L07765          ! zw .. heights of the downdraft levels (edges of boxes)
L07766          real(kind_phys), dimension(kts:kte+1), intent(in) :: zw
L07767          real(kind_phys), intent(in)  :: flt,flq,fltv
L07768          real(kind_phys), intent(in)  :: dt,dx,ust,pblh,psig
L07769     !outputs - downdraft properties
L07770          real(kind_phys), dimension(kts:kte), intent(inout) ::         &
L07771          edmf_a_dd,   edmf_w_dd,   edmf_qt_dd,  edmf_thl_dd,           &
L07772          edmf_ent_dd, edmf_qc_dd,  tkeprod_dn
L07773     !outputs - variables needed for solver (sd_aw - sum ai*wi, sd_awphi - sum ai*wi*phii)
L07774          real(kind_phys), dimension(kts:kte+1) ::                      &
L07775              sd_aw, sd_awthl, sd_awu, sd_awv,                          &
L07776              sd_awqt, sd_awqc, sd_awqv, sd_awqi, sd_awqnc, sd_awqni,   &
L07777              sd_awqnwfa, sd_awqnifa, sd_awqke, sd_aw2
L07778     !outputs - diagnostics
L07779          real(kind_phys), intent(inout) :: maxmf_dd,maxwidth_dd
L07780  
L07781     !downdraft properties
L07782          integer, parameter::                &
L07783              & ndd            = 5,           &  !number of downdrafts
L07784              & kmin           = 3               !lowest k-level where downdrafts can start
L07785          real(kind_phys),parameter ::        &
L07786              & minddd         = 100.,        &  !min downdraft diameter (m)
L07787              & maxddd         = 500.,        &  !max downdraft diameter (m)
L07788              & zmin           = 50.,         &  !lowest height where downdrafts can start
L07789              & dz200          = 200.,        &  !depth over which other parameters are normalized to
L07790              & cooling_thresh = -0.00010        !activation threshold of downdrafts
L07791                                !-0.000116 is ~ -10 C cooling at cloud top per day
L07792                                !-0.000093 is ~  -8 C cooling at cloud top per day
L07793                                !-0.000069 is ~  -6 C cooling at cloud top per day
L07794          real(kind_phys)::                   &
L07795              & maxdd2,                       &  !variable max downdraft diameter (m)
L07796              &    ddd,                       &  !downdraft diameter
L07797              &     dl,                       &  !diameter increment
L07798              &    add,                       &  !total area of downdrafts
L07799              & minexc,                       &  !minimum init downdraft temp pert
L07800              & maxexc                           !maximum init downdraft temp pert
L07801    ! k-index of downdraft starting height
L07802          integer,         dimension(1:ndd) :: dd_initk
L07803    ! downdraft column properties
L07804          real(kind_phys), dimension(kts:kte+1,1:ndd) ::                &
L07805              downw,downthl,downqt,downqc,downa,downu,downv,downthv,    &
L07806              downqi,downqnc,downqni,downqnwfa,downqnifa
L07807    ! entrainment variables
L07808          real(kind_phys), dimension(kts:kte+1,1:ndd) :: ent
L07809    ! internal variables
L07810          real(kind_phys), dimension(kts:kte):: massflux
L07811          integer :: k,i,ki,qltop,qlbase
L07812          real(kind_phys):: qstar,thstar,sigmaw,sigmaqt,                &
L07813              sigmath,z0,pwmin,pwmax,wmin,wmax,went,mindownw
L07814          real(kind_phys):: qtn,thln,thvn,qcn,un,vn,qken,wn2,wn,        &
L07815              qin,qncn,qnin,qnwfan,qnifan,                              &
L07816              thvk,pk,entexp,entw,beta_dm,entexm,rho_int
L07817          real(kind_phys):: jump_thv,jump_qt,jump_thetal,               &
L07818              refthl,refthv,refthlv,refqt,refqc,refqi,refqnc,refqni,    &
L07819              refqnwfa,refqnifa,refu,refv,refqke,refqt2,reftk,refp,     &
L07820              qx_k,qx_km1,refthvm1,cftop,crate,ac_wsp,wspd_pbl,         &
L07821              maxcooling
L07822          real(kind_phys):: dthvx,tmp1,rcldb,ent_eff
L07823  
L07824    ! dd specific internal variables
L07825          real(kind_phys):: radflux, f0, wstar_rad, dz_ent
L07826          logical :: cloudflg
L07827          logical :: singlelayer             !check for single or multi-layer clouds
L07828          real(kind_phys):: sigq,xl,rsl,cpm,a,diffqt,dp,                &
L07829              fng,qww,alpha,beta,bb,f,pt,t,q2p,b9,satvp,rhgrid,         &
L07830              def_th,def_qt,frac_liq,frac_ice,qs1,qs2
L07831  
L07832    ! w parameters
L07833          real(kind_phys),parameter ::                                  &
L07834              &wa=1., wb=1.5, z00=100.
L07835          real(kind_phys) :: buoy,bcoeff,ecoeff
L07836  
L07837    ! additional printouts for debugging
L07838          integer, parameter :: debug_dd=0   !0:no debugging, 1:detailed output, 2:output for strange values only
```

> **头注释的八条设计声明**（原文 L7721–L7737）——下沉流相对 Wu et al. (2020, MWR) 原始方案的改造：①谱羽流设计（同上升流）；②推广到任意云（不限于 PBL 顶盖）；③永远从云顶初始化；④可直达地面；⑤混合相推广；⑥双矩方案的数浓度；⑦气溶胶混合；⑧求解器接口重设计。**`ndd = 5` 个下沉羽流**、`cooling_thresh = −1e-4` K/s（注释折算：约 −10 °C/天 的云顶冷却——三档历史阈值 6/8/10 °C 并列注释）。

<!-- code_extract code_extract.py v1.1
source: phys/MYNN-EDMF/module_bl_mynnedmf.F90
ranges: L7840-L8087
file_lines: 8776
file_md5: ec93fee9745a3e0b25be55a61b5aff8a
display: line-numbered (strip L-prefix and !file: line to restore)
range_md5: e5a445e1dc49cb0a2a95c343eba4b19c
seg_lines: 248
-->

```fortran
!file: phys/MYNN-EDMF/module_bl_mynnedmf.F90    L7840-L8087
L07840    ! =================================================================
L07841    ! initialize downdraft properties
L07842     downw      =zero
L07843     downthl    =zero
L07844     downthv    =zero
L07845     downqt     =zero
L07846     downa      =zero
L07847     downu      =zero
L07848     downv      =zero
L07849     downqc     =zero
L07850     downqi     =zero
L07851     downqnc    =zero
L07852     downqni    =zero
L07853     downqnwfa  =zero
L07854     downqnifa  =zero
L07855     ent        =zero
L07856     dd_initk   =0
L07857  
L07858     edmf_a_dd  =zero
L07859     edmf_w_dd  =zero
L07860     edmf_qt_dd =zero
L07861     edmf_thl_dd=zero
L07862     edmf_ent_dd=zero
L07863     edmf_qc_dd =zero
L07864  
L07865     sd_aw      =zero
L07866     sd_awthl   =zero
L07867     sd_awqt    =zero
L07868     sd_awqv    =zero
L07869     sd_awqc    =zero
L07870     sd_awqi    =zero
L07871     sd_awqnc   =zero
L07872     sd_awqni   =zero
L07873     sd_awqnwfa =zero
L07874     sd_awqnifa =zero
L07875     sd_awu     =zero
L07876     sd_awv     =zero
L07877     sd_awqke   =zero
L07878  
L07879     ! first, check for cloud tops. if more than one, find the one with maximum cooling at the cloud top.
L07880     cloudflg   =.false.
L07881     singlelayer=.false.
L07882     qltop      =1     !initialize
L07883     qlbase     =1     !initialize
L07884     crate      =zero
L07885     do k = max(kmin,kpbl-5),min(kpbl+20,kte-1)
L07886        maxcooling = minval(rthraten(k-1:k+1))
L07887        !---------------------------------criteria for downdraft activation:
L07888        if ((cldfra_bl1(k).gt.p5 .and. cldfra_bl1(k+1).lt.p5) .and. &  !1) stratocu cloud top exists
L07889            (maxcooling  .lt. cooling_thresh)) then                    !2) significant radiative cooling
L07890           ! found sc cloud with significant radiative cooling
L07891           cloudflg =.true.
L07892           if (maxcooling < crate) then
L07893              qltop    =k               !index for sc cloud top
L07894              cftop    =cldfra_bl1(k)
L07895              crate    =maxcooling      !maximum cooling rate at cloud top
L07896              if (cldfra_bl1(k-1).lt.p2)singlelayer=.true.
L07897           endif
L07898        endif
L07899     enddo
L07900  
L07901     ! determine maximum downdraft width and increments
L07902     maxdd2  = min(maxddd, 1.2_kind_phys*dx)                                       !1) grid-scale dependence
L07903     maxdd2  = min(maxdd2, -100._kind_phys*crate*3600._kind_phys + 200._kind_phys) !2) function of cloud top cooling rate
L07904     maxdd2  = min(maxdd2, 80._kind_phys + p666*zw(qltop+1))                       !3) limited for low cloud-top heights
L07905     maxwidth_dd = maxdd2
L07906     dl      = max(maxdd2-minddd, zero)/real(ndd-1)
L07907     
L07908     !found sc cloud with conditions for downdrafts; compute downdrafts
L07909     if (cloudflg .and. ( dl .gt. zero)) then
L07910        do k = qltop, kts, -1
L07911           qx_k =max(qt(k), qc_bl1(k) +qi_bl1(k))     !total cloud water and ice at k
L07912           if (qx_k .gt. 1e-6_kind_phys) then
L07913              qlbase = k ! index for sc cloud base
L07914           endif
L07915        enddo
L07916  
L07917        do i=1,ndd
L07918           ! downdraft starts at the first layer interface below the cloud top
L07919           dd_initk(i) = qltop
L07920        enddo
L07921  
L07922        ! loop radflux
L07923        f0 = zero
L07924        do k = max(kmin,qltop-2), qltop+1
L07925           radflux = rthraten(k) * exner(k)     ! converts theta/s to temperature/s
L07926           dp      = p5 * (( p(k) - p(k+1) ) + ( p(k-1) - p(k) ))
L07927           radflux = radflux * cp / grav * dp   ! converts k/s to w/m^2
L07928           if ( radflux < zero ) f0 = abs(radflux) + f0
L07929        enddo
L07930        f0 = min(max(f0, one), 200._kind_phys)  !total radiative cooling (w/m2)
L07931  
L07932        !allow the total fractional area of the downdrafts (add) to be proportional
L07933        !to the radiative forcing:
L07934        !for  50 w/m2, add = 0.10
L07935        !for 100 w/m2, add = 0.20
L07936        !for 150 w/m2, add = 0.30
L07937        add      = min( f0*0.003, 0.3_kind_phys)
L07938        !taper off area for high wind speeds
L07939        wspd_pbl = sqrt(max(u(kts)**2 + v(kts)**2, 0.01_kind_phys))
L07940        ac_wsp   = one - min(max(zero, wspd_pbl - 10._kind_phys)/15._kind_phys, one)
L07941        add      = add * min(ac_wsp, psig)
L07942  
L07943        !find inversion strength across cloud top entrainment zone--normalized to 200 m vertical grid spacing
L07944        dz_ent      = p5 * (dz(qltop+1) + dz(qltop))
L07945        jump_thv    = (thv(qltop+1) - thv(qltop)) / dz_ent * dz200
L07946        jump_qt     = (qt(qltop+1)  - qt(qltop))	/ dz_ent * dz200
L07947        jump_thetal = (thl(qltop+1) - thl(qltop))	/ dz_ent * dz200
L07948  
L07949        ki = qltop  !index of cloud top
L07950        if (singlelayer) then !initialize dd with cloud properties (not using info from above)
L07951           refthl  = thl(ki)
L07952           refthlv = refthl*(1.+p608*qv(ki))
L07953           refthv  = thv(ki)
L07954           refthvm1= thv(ki-1)
L07955           reftk   = tk(ki)
L07956           refqt   = qt(ki)
L07957           refqc   = qc(ki)
L07958           refqi   = qi(ki)
L07959           refqnc  = qnc(ki)
L07960           refqni  = qni(ki)
L07961           refqnwfa= qnwfa(ki)
L07962           refqnifa= qnifa(ki)
L07963           refu    = u(ki)
L07964           refv    = v(ki)
L07965           refqke  = qke(ki)
L07966           refp    = p(ki)
L07967        else                  !initialize dd with avg of in-cloud properties (at & below) cloud top 
L07968           refthl  = (thl(ki-1)*dz(ki)   + thl(ki)*dz(ki-1))  /(dz(ki)+dz(ki-1))
L07969           refthlv = refthl*(1.+p608*(qv(ki-1)*dz(ki) + qv(ki)*dz(ki-1))/(dz(ki)+dz(ki-1)))
L07970           refthv  = (thv(ki-1)*dz(ki)   + thv(ki)*dz(ki-1))  /(dz(ki)+dz(ki-1))
L07971           refthvm1= (thv(ki-2)*dz(ki-1) + thv(ki-1)*dz(ki-2))/(dz(ki-1)+dz(ki-2)) 
L07972           reftk   = (tk(ki-1)*dz(ki)    + tk(ki)*dz(ki-1))   /(dz(ki)+dz(ki-1))
L07973           refqt   = (qt(ki-1)*dz(ki)    + qt(ki)*dz(ki-1))   /(dz(ki)+dz(ki-1))
L07974           refqc   = (qc(ki-1)*dz(ki)    + qc(ki)*dz(ki-1))   /(dz(ki)+dz(ki-1))
L07975           refqi   = (qi(ki-1)*dz(ki)    + qi(ki)*dz(ki-1))   /(dz(ki)+dz(ki-1))
L07976           refqnc  = (qnc(ki-1)*dz(ki)   + qnc(ki)*dz(ki-1))  /(dz(ki)+dz(ki-1))
L07977           refqni  = (qni(ki-1)*dz(ki)   + qni(ki)*dz(ki-1))  /(dz(ki)+dz(ki-1))
L07978           refqnwfa= (qnwfa(ki-1)*dz(ki) + qnwfa(ki)*dz(ki-1))/(dz(ki)+dz(ki-1))
L07979           refqnifa= (qnifa(ki-1)*dz(ki) + qnifa(ki)*dz(ki-1))/(dz(ki)+dz(ki-1))
L07980           refu    = (u(ki-1)*dz(ki)     + u(ki)*dz(ki-1))    /(dz(ki)+dz(ki-1))
L07981           refv    = (v(ki-1)*dz(ki)     + v(ki)*dz(ki-1))    /(dz(ki)+dz(ki-1))
L07982           refqke  = (qke(ki-1)*dz(ki)   + qke(ki)*dz(ki-1))  /(dz(ki)+dz(ki-1))
L07983           refp    = (p(ki-1)*dz(ki)     + p(ki)*dz(ki-1))    /(dz(ki)+dz(ki-1))
L07984        endif
L07985  
L07986        ! w* from radiative forcing (m/s)
L07987        !wstar_rad =    ( grav * dz_ent * f0 / (refthl * rho(ki) * cp) ) **p333
L07988        wstar_rad = 1.25_kind_phys * ( grav*dz200 * f0 / (refthl * rho(ki) * cp) ) **p333
L07989        wstar_rad = min(max(wstar_rad, p1), 1.5_kind_phys)      ! (m/s)
L07990  
L07991        !entrainment efficiency
L07992        dthvx     = (thl(ki+2) + th(ki+2)*p608*qt(ki+2)) - &
L07993                    (thl(ki)   + th(ki)  *p608*qt(ki))
L07994        dthvx     = dthvx * dz200/dz_ent  !normalized gradient
L07995        dthvx     = max(dthvx, p1)
L07996        rcldb     = max(refqc+refqi, qc_bl1(ki)+qi_bl1(ki))  !any type of cloud water (sgs or resolved) 
L07997        tmp1      = xlvcp * rcldb/(exner(ki)*dthvx)
L07998        !entrainment efficiency: originally from Nichols and Turton (1986), where a2 = 60, but lowered
L07999        !here to 8, as in Grenier and Bretherton (2001).
L08000        ent_eff   = max(zero, min(one, p2 + p2*eight*tmp1))
L08001  
L08002        went      = p333 * ent_eff * wstar_rad
L08003        qstar     = went * jump_qt / wstar_rad
L08004        thstar    = -f0/rho(ki)/cp/wstar_rad - went*jump_thv/wstar_rad
L08005  
L08006        sigmaw    = 0.2 * wstar_rad   ! 0.8*wstar_rad ! tuning parameter ! 0.5 was good
L08007        sigmaqt   = 50. * abs(qstar)  ! 50 was good
L08008        sigmath   = 1.5 * abs(thstar) ! 0.5 was good
L08009  
L08010        pwmin     = -1. ! drawing from the negative tail -3sigma to -1sigma
L08011        pwmax     = -3.
L08012        wmin      = max(min(sigmaw*pwmin, -0.1), -0.2)
L08013        wmax      = max(min(sigmaw*pwmax, -0.2), -0.5)
L08014  
L08015        !initialize downdraft temperature deficit def_th
L08016        minexc = min(-0.06     , 0.5*(refthvm1 - refthv)) !increase prob to go down 1 level
L08017        maxexc = min(minexc-0.1, -0.6          )
L08018        maxexc = max(maxexc    , thv(1) - refthlv)        !init parcel temp >= thv_sfc
L08019        def_th = max(min(0.05*(-0.3)*sigmath/sigmaw, minexc), maxexc)
L08020  
L08021        !initialize downdraft moisture deficit def_qt (consistent with def_th)
L08022        qs1    = qsat_blend(reftk       ,refp)
L08023        qs2    = qsat_blend(reftk+def_th,refp)
L08024        refqt2 = refqt*qs2/qs1
L08025        !def_qt = min(refqt2 - refqt, zero) !small negative moisture perturbation
L08026        def_qt = min(qs2 - qs1,  -0.33*(refqc+refqi)) !small negative moisture perturbation
L08027        !def_qt = 0.5*(-0.3)*sigmaqt/sigmaw
L08028  
L08029        if (refqc+refqi > zero) then
L08030           frac_liq = refqc/(refqc+refqi)
L08031           frac_ice = one - frac_liq
L08032        else
L08033           frac_liq = zero
L08034           frac_ice = zero
L08035        endif
L08036  
L08037        if (debug_dd .eq. 1) then
L08038           print*,"-------------------------------------"
L08039           print*,"found conditions for downdraft mixing"
L08040           print*,"qltop=",qltop," qlbase=",qlbase
L08041           print*,"q*=",qstar," theta*=",thstar," went=",went
L08042           print*,"f0=",f0," jump_thv=",jump_thv,"w*rad=",wstar_rad
L08043           print*,"u*=",ust," jump_qt=",jump_qt," fltv=",fltv
L08044           print*,"grav=",grav," pblh=",pblh," thv(1)=",thv(1)
L08045           print*,"p(1)=",p(1)," jump_thetal=",jump_thetal
L08046           print*,"sigmaw=",sigmaw," wmin=",wmin," wmax=",wmax
L08047        endif
L08048  
L08049        !intialize downdrafts
L08050        !as of now, all downdrafts start at the same height
L08051        do i=1,ndd
L08052           ki = dd_initk(i)
L08053  
L08054           !initialize a negative (downward) vertical velocity
L08055           downw(ki,i)=wmin-(abs(wmax)-abs(wmin))/real(ndd-1)*(i-1)
L08056  
L08057           !perhaps multiply downa by cloud fraction, so it's impact will diminish if
L08058           !clouds are mixed away over the course of the longer radiation time step(?)
L08059           downa(ki,i)     = add/real(ndd)
L08060           downu(ki,i)     = refu
L08061           downv(ki,i)     = refv
L08062           downqc(ki,i)    = max(refqc + def_qt*frac_liq, zero)
L08063           downqi(ki,i)    = max(refqi + def_qt*frac_ice, zero)
L08064           downqnc(ki,i)   = refqnc
L08065           downqni(ki,i)   = refqni
L08066           downqnwfa(ki,i) = refqnwfa
L08067           downqnifa(ki,i) = refqnifa
L08068           downqt(ki,i)    = refqt  + def_qt
L08069           downthv(ki,i)   = refthv + def_th*real(i)/real(ndd)
L08070           downthl(ki,i)   = refthl + def_th*real(i)/real(ndd)
L08071  
L08072           !input :: qt,thv,p,zagl,  output :: thl, qc
L08073  !         pk  =(p(ki-1)*dz(ki)+p(ki)*dz(ki-1))/(dz(ki)+dz(ki-1))
L08074  !         call condensation_edmf_r(downqt(ki,i),   &
L08075  !              &        downthl(ki,i),pk,zw(ki),   &
L08076  !              &     downthv(ki,i),downqc(ki,i)    )
L08077        enddo
L08078  
L08079        if (debug_dd .eq. 1) then
L08080           print*,"=====initialized downdraft properties===="
L08081           print*,"downw=",downw(ki,:)
L08082           print*,"downa=",downa(ki,:)
L08083           print*,"downthv=",downthv(ki,:)
L08084           print*,"def_qt=",def_qt," def_th=",def_th," tot area=",add
L08085           print*,"begin integration of downdrafts (smallest to largest):"
L08086        endif
L08087  
```

> - **云顶搜索**：PBL 顶 −5 ~ +20 层内找“层云顶”（`cldfra(k)>0.5 且 cldfra(k+1)<0.5`）且最大冷却率 < 阈值；多顶取冷却最强者记录 `qltop/crate/cftop`；上方云量 < 0.2 时 `singlelayer=.true.`（决定初始化用云顶值还是云内平均）。
> - **宽度三判据**：`maxdd2 = min(500, 1.2dx, −100·crate·3600+200, 80+(2/3)·zw(qltop))`——网格尺度、冷却率越强羽流越宽、云顶越低羽流越窄。
> - **辐射强迫积分**：云顶附近三层 `radflux = rthraten·exn·cp/g·Δp`（K/s → W/m²），负值累加 `f0`，钳 [1, 200] W/m²。
> - **面积**：`add = min(0.003·f0, 0.3)`——**50 W/m² → 15%、100 → 30%**（注释给了换算表）；风衰减（>10 m/s 线性）与 `psig` 相乘。
> - **云顶逆温强度**：`jump_thv/qt/thetal` 按 200 m 归一化（分辨率无关）。
> - **参考态与过冷扰动**：`ref*` 用云顶（singlelayer）或云内平均；`wstar_rad = 1.25·(g·dz200·f0/(θ·ρ·cp))^(1/3)` 钳 [0.1, 1.5] m/s；**卷入效率 `ent_eff`**（Nichols & Turton 1986 系数 a2=60 → 8，Grenier & Bretherton 2001）：`ent_eff = min(1, 1+8·xlvcp·qc/(exn·dθv))`——**液水越多、云顶混合越强**（云顶凝结-辐射耦合）；`went = (1/3)·ent_eff·wstar_rad`。
> - **下沉扰动初始化**：w 从负尾采样（pwmin=−1/pwmax=−3 σw）；`def_th`（温度亏损）与 `def_qt`（水汽亏损 = min(饱和差, −⅓·凝结物)）——**下沉羽流=冷的干羽流**。

<!-- code_extract code_extract.py v1.1
source: phys/MYNN-EDMF/module_bl_mynnedmf.F90
ranges: L8088-L8283
file_lines: 8776
file_md5: ec93fee9745a3e0b25be55a61b5aff8a
display: line-numbered (strip L-prefix and !file: line to restore)
range_md5: ee33199a12e32a49b9e5a1eacad695a0
seg_lines: 196
-->

```fortran
!file: phys/MYNN-EDMF/module_bl_mynnedmf.F90    L8088-L8283
L08088        do i=1,ndd
L08089           ddd  = minddd + dl*real(i-1) !downdraft diameter
L08090           !initialize input into condensation routine
L08091           thvn = downthv(ki,i)
L08092           qcn  = downqc(ki,i)
L08093           qin  = downqi(ki,i)
L08094           do k=dd_initk(i)-1,kts+1,-1
L08095              !entrainment from tian and kuang (2016), with constraints
L08096              wmin = p1 + ddd*0.0005
L08097              !ent(k,i) = 0.33/(min(max(abs(downw(k+1,i)),wmin),0.9)*ddd)
L08098              !ent(k,i) = 0.53/(min(max(abs(downw(k+1,i)),wmin),0.6)*ddd)
L08099              !was       0.26  before reducing downdraft sizes
L08100              ent(k,i) = 0.18/(min(max(abs(downw(k+1,i)),wmin),0.6)*ddd)
L08101              
L08102              !minimum background entrainment and 1/z enhancement near surface
L08103              ent(k,i) = max(ent(k,i),0.0003)
L08104              ent(k,i) = max(ent(k,i),0.06/zw(k))
L08105              ent(k,i) = min(ent(k,i),0.9/dz(k)) ! liberal check for numerical stability
L08106  
L08107              !starting at the first interface level below cloud top
L08108              !entexp=exp(-ent(k,i)*dz(k))
L08109              !entexp_m=exp(-ent(k,i)/3.*dz(k))
L08110              entexp  =ent(k,i)*dz(k)        !for all scalars
L08111              entexm  =ent(k,i)*dz(k)*p5     !for momentum
L08112  
L08113              qtn     =downqt(k+1,i)   *(one-entexp) + qt(k)*entexp
L08114              thln    =downthl(k+1,i)  *(one-entexp) + thl(k)*entexp
L08115              qncn    =downqnc(k+1,i)  *(one-entexp) + qnc(k)*entexp
L08116              qnin    =downqni(k+1,i)  *(one-entexp) + qni(k)*entexp
L08117              qnwfan  =downqnwfa(k+1,i)*(one-entexp) + qnwfa(k)*entexp
L08118              qnifan  =downqnifa(k+1,i)*(one-entexp) + qnifa(k)*entexp
L08119              un      =downu(k+1,i)    *(one-entexm) + u(k)*entexm
L08120              vn      =downv(k+1,i)    *(one-entexm) + v(k)*entexm
L08121              !qken=downqke(k-1,i)*(1.-entexp) + qke(k)*entexp
L08122  !            qtn =downqt(k+1,i) +(qt(k) -downqt(k+1,i)) *(1.-entexp)
L08123  !            thln=downthl(k+1,i)+(thl(k)-downthl(k+1,i))*(1.-entexp)
L08124  !            un  =downu(k+1,i)  +(u(k)  -downu(k+1,i))*(1.-entexp_m)
L08125  !            vn  =downv(k+1,i)  +(v(k)  -downv(k+1,i))*(1.-entexp_m)
L08126  
L08127              ! given new p & z, solve for thvn, qcn, and qin
L08128              pk  =(p(k-1)*dz(k)+p(k)*dz(k-1))/(dz(k)+dz(k-1))
L08129              call condensation_ddmf(qtn,thln,pk,zw(k),thvn,qcn,qin,debug_dd)
L08130  
L08131              !calculate buoyancy
L08132              thvk =(thv(k-1)*dz(k)+thv(k)*dz(k-1))/(dz(k)+dz(k-1))
L08133              buoy =grav*(thvn/thvk - one)
L08134              !downdraft decelleration to limit large tendencies at the surface
L08135              if (buoy > zero) then
L08136                 bcoeff =  0.2  !0.15 = same as in updrafts
L08137                 ecoeff = -2.0
L08138              else
L08139                 !for numerical stability reasons, apply brakes near the surface.
L08140                 bcoeff = 0.2*(one - exp(-zw(k)/(0.15_kind_phys*pblh)))
L08141                 ecoeff = -2.0_kind_phys - exp(-zw(k)/(0.15_kind_phys*pblh))
L08142                 buoy   = buoy*(one - exp(-zw(k)/(0.15_kind_phys*pblh)))
L08143              endif
L08144              if (k==kts+2) buoy=max(buoy,0.01)
L08145              if (k==kts+1) buoy=max(buoy,0.05)
L08146  
L08147  !            beta_dm = 2*wb*ent(k,i) + 0.5/(zw(k)-dz(k)) * &
L08148  !                 &    max(1. - exp((zw(k) -dz(k))/z00 - 1. ) , 0.)
L08149  !            entw=exp(-beta_dm * dz(k))
L08150  !            entw=entexp
L08151  !            if (beta_dm >0) then
L08152  !               wn2=downw(k+1,i)**2*entw - wa*buoy/beta_dm * (1. - entw)
L08153  !            else
L08154  !               wn2=downw(k+1,i)**2      - 2.*wa*buoy*dz(k)
L08155  !            end if
L08156  
L08157              mindownw = min(downw(k+1,i),-0.2_kind_phys)
L08158              wn = downw(k+1,i) + (ecoeff*ent(k,i)*downw(k+1,i)        &
L08159                                - bcoeff*buoy/mindownw)*min(dz(k), 250.)
L08160  
L08161              !do not allow a parcel to accelerate more than 1.25 m/s over 200 m.
L08162              !add max acceleration of -2.0 m/s for coarse vertical resolution.
L08163              if (wn < downw(k+1,i) - min(1.25*dz(k)/200., 2.0))then
L08164                  wn = downw(k+1,i) - min(1.25*dz(k)/200., 2.0)
L08165              endif
L08166              !add symmetrical max decrease in velocity (less negative)
L08167              if (wn > downw(k+1,i) + min(1.25*dz(k)/200., 2.0))then
L08168                  wn = downw(k+1,i) + min(1.25*dz(k)/200., 2.0)
L08169              endif
L08170              wn = max(min(wn,zero), -2.0_kind_phys)
L08171  
L08172              if (debug_dd .eq.1) then
L08173                 print *, "downdraft #:", i," diameter:",ddd,"==========="
L08174                 print *, "  k       =",      k,      " z    =", zw(k)
L08175                 print *, "  ent     =",ent(k,i),     " bouy =", buoy
L08176                 print *, "  downthv =",   thvn,      " thvk =", thvk
L08177                 print *, "  downthl =",   thln,      " thl  =", thl(k)
L08178                 print *, "  downqt  =",   qtn ,      " qt   =", qt(k)
L08179                 print *, "  downqc  =",   qcn ,      " qc   =", qc(k)
L08180                 print *, "  downw+1 =",downw(k+1,i), " wn2  =", wn
L08181              endif
L08182  
L08183              if (wn .lt. 0.) then !terminate when velocity is too small
L08184                 downw(k,i)     = wn !-sqrt(wn2)
L08185                 downthv(k,i)   = thvn
L08186                 downthl(k,i)   = thln
L08187                 downqt(k,i)    = qtn
L08188                 downqc(k,i)    = qcn
L08189                 downqi(k,i)    = qin
L08190                 downqnc(k,i)   = qncn
L08191                 downqni(k,i)   = qnin
L08192                 downqnwfa(k,i) = qnwfan
L08193                 downqnifa(k,i) = qnifan
L08194                 downu(k,i)     = un
L08195                 downv(k,i)     = vn
L08196                 downa(k,i)     = downa(k+1,i)
L08197              else
L08198                 !downdrafts must go at least 2 levels
L08199  !               if (dd_initk(i) - k .lt. 2) then
L08200  !                  downw(:,i)  = zero
L08201  !                  downthv(:,i)= zero
L08202  !                  downthl(:,i)= zero
L08203  !                  downqt(:,i) = zero
L08204  !                  downqc(:,i) = zero
L08205  !                  downu(:,i)  = zero
L08206  !                  downv(:,i)  = zero
L08207  !               endif
L08208                 exit
L08209              endif
L08210           enddo
L08211        enddo
L08212  
L08213        downw(1,:) = zero !make sure downdrafts do not penetrate the surface
L08214        downa(1,:) = zero
L08215  
L08216        !
L08217        ! combine all downdrafts into one averaged downdraft
L08218        !
L08219        do k=qltop,kts,-1
L08220           do i=1,ndd
L08221              edmf_a_dd(k)  =edmf_a_dd(k)  +downa(k,i)
L08222              edmf_w_dd(k)  =edmf_w_dd(k)  +downa(k,i)*downw(k,i)
L08223              edmf_qt_dd(k) =edmf_qt_dd(k) +downa(k,i)*downqt(k,i)
L08224              edmf_thl_dd(k)=edmf_thl_dd(k)+downa(k,i)*downthl(k,i)
L08225              edmf_ent_dd(k)=edmf_ent_dd(k)+downa(k,i)*ent(k,i)
L08226              edmf_qc_dd(k) =edmf_qc_dd(k) +downa(k,i)*downqc(k,i)
L08227           enddo
L08228  
L08229           if (edmf_a_dd(k) > 0.) then
L08230              edmf_w_dd(k)  =edmf_w_dd(k)  /edmf_a_dd(k)
L08231              edmf_qt_dd(k) =edmf_qt_dd(k) /edmf_a_dd(k)
L08232              edmf_thl_dd(k)=edmf_thl_dd(k)/edmf_a_dd(k)
L08233              edmf_ent_dd(k)=edmf_ent_dd(k)/edmf_a_dd(k)
L08234              edmf_qc_dd(k) =edmf_qc_dd(k) /edmf_a_dd(k)
L08235           endif
L08236           !instead of dTKE/dt = 1/2 w^3, multiply by 1 for QKE.
L08237           tkeprod_dn(k)=(abs(edmf_w_dd(k))**3)*edmf_a_dd(k)/(b1*max(el(k),p5))
L08238           tkeprod_dn(k)=min(0.0004_kind_phys, tkeprod_dn(k))
L08239        enddo
L08240        ! add tke source for entrainment at layer above cloud. use same area
L08241        ! above cloud as used in the initialized downdraft area.
L08242        tkeprod_dn(qltop+1)=went**3*edmf_a_dd(qltop)/(b1*max(el(qltop+1),p5))
L08243        massflux = edmf_a_dd * edmf_w_dd
L08244        maxmf_dd = abs(minval(massflux))
L08245  
L08246        if (debug_dd .eq. 2) then
L08247           do k=kts,kte
L08248              if (tkeprod_dn(k) > 0.0004_kind_phys .or. edmf_w_dd(k) < -two) then
L08249                 print*,"-------------------------------------"
L08250                 print*,"found strange behavior in downdrafts at",k
L08251                 print*,"qltop=",qltop," qlbase=",qlbase," a(top)=",edmf_a_dd(qltop)
L08252                 print*,"q*=",qstar," theta*=",thstar," went=",went
L08253                 print*,"f0=",f0," jump_thv=",jump_thv,"w*rad=",wstar_rad
L08254                 print*,"u*=",ust," jump_qt=",jump_qt," fltv=",fltv
L08255                 print*,"grav=",grav," pblh=",pblh," thv(1)=",thv(1)
L08256                 print*,"p(1)=",p(1)," jump_thl=",jump_thetal," ent_eff=",ent_eff
L08257                 print*,"sigmaw=",sigmaw," wmin=",wmin," wmax=",wmax
L08258                 print*,"tke prod=",tkeprod_dn(k)," w=",edmf_w_dd(k)," a(k)=",edmf_a_dd(k)
L08259              endif
L08260           enddo
L08261        endif
L08262        ! compute variables needed for solver
L08263        !
L08264        do k=kts,qltop
L08265           rho_int = (rho(k)*dz(k+1)+rho(k+1)*dz(k))/(dz(k+1)+dz(k))
L08266           do i=1,ndd
L08267              sd_aw(k)   =sd_aw(k)   +rho_int*downa(k,i)*abs(downw(k,i))
L08268              sd_awthl(k)=sd_awthl(k)+rho_int*downa(k,i)*downw(k,i)*downthl(k,i)
L08269              sd_awqt(k) =sd_awqt(k) +rho_int*downa(k,i)*downw(k,i)*downqt(k,i)
L08270              sd_awqc(k) =sd_awqc(k) +rho_int*downa(k,i)*downw(k,i)*downqc(k,i)
L08271              sd_awqi(k) =sd_awqi(k) +rho_int*downa(k,i)*downw(k,i)*downqi(k,i)
L08272              sd_awqnc(k)=sd_awqnc(k)+rho_int*downa(k,i)*downw(k,i)*downqnc(k,i)
L08273              sd_awqni(k)=sd_awqni(k)+rho_int*downa(k,i)*downw(k,i)*downqni(k,i)
L08274              sd_awqnwfa(k)=sd_awqnwfa(k)+rho_int*downa(k,i)*downw(k,i)*downqnwfa(k,i)
L08275              sd_awqnifa(k)=sd_awqnifa(k)+rho_int*downa(k,i)*downw(k,i)*downqnifa(k,i)
L08276              sd_awu(k)  =sd_awu(k)  +rho_int*downa(k,i)*downw(k,i)*downu(k,i)
L08277              sd_awv(k)  =sd_awv(k)  +rho_int*downa(k,i)*downw(k,i)*downv(k,i)
L08278           enddo
L08279           sd_awqv(k) = sd_awqt(k)  - sd_awqc(k) - sd_awqi(k)
L08280        enddo
L08281  
L08282     endif ! end cloud flag
L08283  
```

> - **逐层下沉积分**：卷入率 `ent = 0.18/(max(|w|, wmin)·ddd)`（系数 0.18——上升流 0.21 的下沉版）；近地面 **1/z 增强**（`max(ent, 0.06/zw)`）与稳定性钳位。
> - **近地面刹车**（L8135–L8145）：负浮力（下沉遇暖层）时 `bcoeff/ecoeff/buoy` 都乘 `(1−exp(−zw/(0.15·PBLH)))`——**越近地面越温和**，防止地表强迫过大；`kts+1/kts+2` 两层强制最小正浮力（0.05/0.01）。
> - **速度更新与终止**：`wn = w + (ecoeff·ent·w − bcoeff·buoy/min(w,−0.2))·min(dz,250)`（注意负 w 的符号处理 `mindownw = min(w,−0.2)`）；加速度限对称 ±1.25 m/s per 200 m；`wn ≥ 0` 时终止（至少下沉 2 层的检查被注释）。
> - **合并与输出**：五羽流加权平均成 `edmf_*_dd`；`tkeprod_dn = w³·a/(b1·el)` **≤ 4e-4**（与 topdown 同一上限）；云顶上一层附加 `went³·a` 的 TKE 源（**云顶卷入区的湍流生成**）；`sd_aw*` 界面通量族（隐式求解器用，`|w|` 取绝对值——**通量方向由符号约定定**）。

## 09b.9 `SCALE_AWARE`：灰区网格自适应函数

<!-- code_extract code_extract.py v1.1
source: phys/MYNN-EDMF/module_bl_mynnedmf.F90
ranges: L8286-L8361
file_lines: 8776
file_md5: ec93fee9745a3e0b25be55a61b5aff8a
display: line-numbered (strip L-prefix and !file: line to restore)
range_md5: 7c73568b4ad5c12dbbc5f57dfc47e106
seg_lines: 76
-->

```fortran
!file: phys/MYNN-EDMF/module_bl_mynnedmf.F90    L8286-L8361
L08286  
L08287  SUBROUTINE SCALE_AWARE(dx,pblh,Psig_bl,Psig_shcu)
L08288  
L08289      !---------------------------------------------------------------
L08290      !             NOTES ON SCALE-AWARE FORMULATION
L08291      !
L08292      !     scale-aware factor (Psig) here, taken from Honnert et al. (2011,
L08293      !     JAS) and/or from Hyeyum Hailey Shin and Song-You Hong (2013, JAS)
L08294      !
L08295      ! Psig_bl tapers local mixing
L08296      ! Psig_shcu tapers nonlocal mixing
L08297  
L08298    use module_bl_mynnedmf_common, only: zero,one,ten,kind_phys
L08299    
L08300      real(kind_phys), intent(in)  :: dx,pblh
L08301      real(kind_phys), intent(out) :: Psig_bl,Psig_shcu
L08302      real(kind_phys)              :: dxdh
L08303  
L08304      Psig_bl=one
L08305      Psig_shcu=one
L08306      dxdh=MAX(2.5_kind_phys*dx,ten)/MIN(PBLH,3000._kind_phys)
L08307      ! Honnert et al. 2011, TKE in PBL  *** original form used until 201605
L08308      !Psig_bl= ((dxdh**2) + 0.07*(dxdh**0.667))/((dxdh**2) + &
L08309      !         (3./21.)*(dxdh**0.67) + (3./42.))
L08310      ! Honnert et al. 2011, TKE in entrainment layer
L08311      !Psig_bl= ((dxdh**2) + (4./21.)*(dxdh**0.667))/((dxdh**2) + &
L08312       !        (3./20.)*(dxdh**0.67) + (7./21.))
L08313      ! New form to preseve parameterized mixing - only down 5% at dx = 750 m
L08314      Psig_bl= ((dxdh**2) + 0.106_kind_phys*(dxdh**0.667_kind_phys))/((dxdh**2) + &
L08315           0.066_kind_phys*(dxdh**0.667_kind_phys) + 0.071_kind_phys)
L08316  
L08317      !assume a 500 m cloud depth for shallow-cu clods
L08318      dxdh=MAX(2.5_kind_phys*dx,ten)/MIN(PBLH+500._kind_phys,3500._kind_phys)
L08319      ! Honnert et al. 2011, TKE in entrainment layer *** original form used until 201605
L08320      !Psig_shcu= ((dxdh**2) + (4./21.)*(dxdh**0.667))/((dxdh**2) + &
L08321      !         (3./20.)*(dxdh**0.67) + (7./21.))
L08322  
L08323      ! Honnert et al. 2011, TKE in cumulus
L08324      !Psig(i)= ((dxdh**2) + 1.67*(dxdh**1.4))/((dxdh**2) +1.66*(dxdh**1.4) +
L08325      !0.2)
L08326  
L08327      ! Honnert et al. 2011, w'q' in PBL
L08328      !Psig(i)= 0.5 + 0.5*((dxdh**2) + 0.03*(dxdh**1.4) -
L08329      !(4./13.))/((dxdh**2) + 0.03*(dxdh**1.4) + (4./13.))
L08330      ! Honnert et al. 2011, w'q' in cumulus
L08331      !Psig(i)= ((dxdh**2) - 0.07*(dxdh**1.4))/((dxdh**2) -0.07*(dxdh**1.4) +
L08332      !0.02)
L08333  
L08334      ! Honnert et al. 2011, q'q' in PBL
L08335      !Psig(i)= 0.5 + 0.5*((dxdh**2) + 0.25*(dxdh**0.667) -0.73)/((dxdh**2)
L08336      !-0.03*(dxdh**0.667) + 0.73)
L08337      ! Honnert et al. 2011, q'q' in cumulus
L08338      !Psig(i)= ((dxdh**2) - 0.34*(dxdh**1.4))/((dxdh**2) - 0.35*(dxdh**1.4)
L08339      !+ 0.37)
L08340  
L08341      ! Hyeyum Hailey Shin and Song-You Hong 2013, TKE in PBL (same as Honnert's above)
L08342      !Psig_shcu= ((dxdh**2) + 0.070*(dxdh**0.667))/((dxdh**2)
L08343      !+0.142*(dxdh**0.667) + 0.071)
L08344      ! Hyeyum Hailey Shin and Song-You Hong 2013, TKE in entrainment zone  *** switch to this form 201605
L08345      Psig_shcu= ((dxdh**2) + 0.145_kind_phys*(dxdh**0.667_kind_phys))/((dxdh**2) + &
L08346           0.172_kind_phys*(dxdh**0.667_kind_phys) + 0.170_kind_phys)
L08347  
L08348      ! Hyeyum Hailey Shin and Song-You Hong 2013, w'theta' in PBL
L08349      !Psig(i)= 0.5 + 0.5*((dxdh**2) -0.098)/((dxdh**2) + 0.106) 
L08350      ! Hyeyum Hailey Shin and Song-You Hong 2013, w'theta' in entrainment zone
L08351      !Psig(i)= 0.5 + 0.5*((dxdh**2) - 0.112*(dxdh**0.25) -0.071)/((dxdh**2)
L08352      !+ 0.054*(dxdh**0.25) + 0.10)
L08353  
L08354      !print*,"in scale_aware; dx, dxdh, Psig(i)=",dx,dxdh,Psig(i)
L08355      !If(Psig_bl(i) < 0.0 .OR. Psig(i) > 1.)print*,"dx, dxdh, Psig(i)=",dx,dxdh,Psig_bl(i) 
L08356      If(Psig_bl > one) Psig_bl=one
L08357      If(Psig_bl < zero) Psig_bl=zero
L08358  
L08359      If(Psig_shcu > one) Psig_shcu=one
L08360      If(Psig_shcu < zero) Psig_shcu=zero
L08361  
```

> - **两个因子**：`Psig_bl`（衰减局地混合）与 `Psig_shcu`（衰减非局地混合）——出处 Honnert et al. (2011, JAS) 与 Shin & Hong (2013, JAS)，自变量 `dxdh = 2.5·dx/min(PBLH, 3000)`（**网格距与边界层厚度之比**）。
> - **函数考古**（注释保留六代形式）：Honnert TKE-PBL/TKE-夹带层/w'q'/q'q'、Shin-Hong TKE/w'theta'——**现行选择**：Psig_bl 用“保参数化混合”版（dx=750 m 只降 5%）、Psig_shcu 用 Shin-Hong 夹带层版（201605 切换）。**这是 WRF 灰区模拟（convection-permitting 到 LES 之间）的教科书实现**——教材 ch14 §14.4 的延伸阅读指向。

## 09b.10 blend 饱和函数族：与 Thompson 同源的“相位混合”

<!-- code_extract code_extract.py v1.1
source: phys/MYNN-EDMF/module_bl_mynnedmf.F90
ranges: L8371-L8414
file_lines: 8776
file_md5: ec93fee9745a3e0b25be55a61b5aff8a
display: line-numbered (strip L-prefix and !file: line to restore)
range_md5: 00ae3a84fe877cc9d73253dc9b604652
seg_lines: 44
-->

```fortran
!file: phys/MYNN-EDMF/module_bl_mynnedmf.F90    L8371-L8414
L08371  !! the module (replacing "svp").
L08372    FUNCTION esat_blend(t) 
L08373  
L08374        use module_bl_mynnedmf_common, only: t0c,tice,one,kind_phys
L08375        
L08376        real(kind_phys), intent(in):: t
L08377        real(kind_phys):: esat_blend,XC,ESL,ESI,chi
L08378        !liquid
L08379        real(kind_phys), parameter:: J0= .611583699E03
L08380        real(kind_phys), parameter:: J1= .444606896E02
L08381        real(kind_phys), parameter:: J2= .143177157E01
L08382        real(kind_phys), parameter:: J3= .264224321E-1
L08383        real(kind_phys), parameter:: J4= .299291081E-3
L08384        real(kind_phys), parameter:: J5= .203154182E-5
L08385        real(kind_phys), parameter:: J6= .702620698E-8
L08386        real(kind_phys), parameter:: J7= .379534310E-11
L08387        real(kind_phys), parameter:: J8=-.321582393E-13
L08388        !ice
L08389        real(kind_phys), parameter:: K0= .609868993E03
L08390        real(kind_phys), parameter:: K1= .499320233E02
L08391        real(kind_phys), parameter:: K2= .184672631E01
L08392        real(kind_phys), parameter:: K3= .402737184E-1
L08393        real(kind_phys), parameter:: K4= .565392987E-3
L08394        real(kind_phys), parameter:: K5= .521693933E-5
L08395        real(kind_phys), parameter:: K6= .307839583E-7
L08396        real(kind_phys), parameter:: K7= .105785160E-9
L08397        real(kind_phys), parameter:: K8= .161444444E-12
L08398  
L08399        XC=MAX(-80._kind_phys, t - t0c) !note t0c = 273.15, tice is set in module mynn_common to 240
L08400  
L08401  ! For 240 < t < 268.16 K, the vapor pressures are "blended" as a function of temperature, 
L08402  ! using the approach similar to Chaboureau and Bechtold (2002), JAS, p. 2363.  The resulting 
L08403  ! values are returned from the function.
L08404        IF (t .GE. (t0c-6._kind_phys)) THEN
L08405            esat_blend = J0+XC*(J1+XC*(J2+XC*(J3+XC*(J4+XC*(J5+XC*(J6+XC*(J7+XC*J8))))))) 
L08406        ELSE IF (t .LE. tice) THEN
L08407            esat_blend = K0+XC*(K1+XC*(K2+XC*(K3+XC*(K4+XC*(K5+XC*(K6+XC*(K7+XC*K8)))))))
L08408        ELSE
L08409            ESL = J0+XC*(J1+XC*(J2+XC*(J3+XC*(J4+XC*(J5+XC*(J6+XC*(J7+XC*J8)))))))
L08410            ESI = K0+XC*(K1+XC*(K2+XC*(K3+XC*(K4+XC*(K5+XC*(K6+XC*(K7+XC*K8)))))))
L08411            chi = ((t0c-6._kind_phys) - t)/((t0c-6._kind_phys) - tice)
L08412            esat_blend = (one-chi)*ESL  + chi*ESI
L08413        END IF
L08414  
```

> `esat_blend`：**JAYMES 2015-04-22 加入**，头注释明说“Separate ice and liquid functions are used (**identical to those in module_mp_thompson.F, v3.6**)”——**与 Thompson 的 RSLF/RSIF 同一 Flatau 多项式**（J0–J8/K0–K8 系数逐位一致，文库 code_07b §07b.4）；温度混合区间 **240 K（tice）~267.15 K（t0c−6）**：`chi = (267.15−T)/(267.15−240)` 线性插值液/冰面饱和压——**Chaboureau & Bechtold (2002) 的相位混合思想**。

<!-- code_extract code_extract.py v1.1
source: phys/MYNN-EDMF/module_bl_mynnedmf.F90
ranges: L8423-L8471
file_lines: 8776
file_md5: ec93fee9745a3e0b25be55a61b5aff8a
display: line-numbered (strip L-prefix and !file: line to restore)
range_md5: 3e2da751c572da11361873896893ce58
seg_lines: 49
-->

```fortran
!file: phys/MYNN-EDMF/module_bl_mynnedmf.F90    L8423-L8471
L08423    FUNCTION qsat_blend(t, P)
L08424  
L08425        use module_bl_mynnedmf_common, only: t0c,tice,one,kind_phys
L08426  
L08427        real(kind_phys), intent(in):: t, P
L08428        real(kind_phys):: qsat_blend,XC,ESL,ESI,RSLF,RSIF,chi
L08429        !liquid
L08430        real(kind_phys), parameter:: J0= .611583699E03
L08431        real(kind_phys), parameter:: J1= .444606896E02
L08432        real(kind_phys), parameter:: J2= .143177157E01
L08433        real(kind_phys), parameter:: J3= .264224321E-1
L08434        real(kind_phys), parameter:: J4= .299291081E-3
L08435        real(kind_phys), parameter:: J5= .203154182E-5
L08436        real(kind_phys), parameter:: J6= .702620698E-8
L08437        real(kind_phys), parameter:: J7= .379534310E-11
L08438        real(kind_phys), parameter:: J8=-.321582393E-13
L08439        !ice
L08440        real(kind_phys), parameter:: K0= .609868993E03
L08441        real(kind_phys), parameter:: K1= .499320233E02
L08442        real(kind_phys), parameter:: K2= .184672631E01
L08443        real(kind_phys), parameter:: K3= .402737184E-1
L08444        real(kind_phys), parameter:: K4= .565392987E-3
L08445        real(kind_phys), parameter:: K5= .521693933E-5
L08446        real(kind_phys), parameter:: K6= .307839583E-7
L08447        real(kind_phys), parameter:: K7= .105785160E-9
L08448        real(kind_phys), parameter:: K8= .161444444E-12
L08449  
L08450        XC=MAX(-80._kind_phys,t - t0c)
L08451  
L08452        IF (t .GE. (t0c-6._kind_phys)) THEN
L08453            ESL  = J0+XC*(J1+XC*(J2+XC*(J3+XC*(J4+XC*(J5+XC*(J6+XC*(J7+XC*J8)))))))
L08454            ESL  = min(ESL, P*0.15_kind_phys) ! Even with P=1050mb and T=55C, the sat. vap. pres only contributes to ~15% of total pres.
L08455            qsat_blend = 0.622_kind_phys*ESL/max(P-ESL, 1e-5_kind_phys) 
L08456        ELSE IF (t .LE. tice) THEN
L08457            ESI  = K0+XC*(K1+XC*(K2+XC*(K3+XC*(K4+XC*(K5+XC*(K6+XC*(K7+XC*K8)))))))
L08458            ESI  = min(ESI, P*0.15_kind_phys)
L08459            qsat_blend = 0.622*ESI/max(P-ESI, 1e-5_kind_phys)
L08460        ELSE
L08461            ESL  = J0+XC*(J1+XC*(J2+XC*(J3+XC*(J4+XC*(J5+XC*(J6+XC*(J7+XC*J8)))))))
L08462            ESL  = min(ESL, P*0.15_kind_phys)
L08463            ESI  = K0+XC*(K1+XC*(K2+XC*(K3+XC*(K4+XC*(K5+XC*(K6+XC*(K7+XC*K8)))))))
L08464            ESI  = min(ESI, P*0.15_kind_phys)
L08465            RSLF = 0.622_kind_phys*ESL/max(P-ESL, 1e-5_kind_phys)
L08466            RSIF = 0.622_kind_phys*ESI/max(P-ESI, 1e-5_kind_phys)
L08467  !          chi  = (268.16-t)/(268.16-240.)
L08468            chi  = ((t0c-6._kind_phys) - t)/((t0c-6._kind_phys) - tice) 
L08469            qsat_blend = (one-chi)*RSLF + chi*RSIF
L08470        END IF
L08471  
```

> `qsat_blend`：同一混合逻辑应用到饱和混合比（es→q 换算含 `min(es, 0.15·P)` 钳位与 `max(P−es, 1e-5)` 防零——**Thompson 的两处保护在这里重现**）。**跨方案一致性**：边界层的饱和计算与微物理层用同一口径，消除了“边界层云量与微物理云水判据打架”的隐患。

<!-- code_extract code_extract.py v1.1
source: phys/MYNN-EDMF/module_bl_mynnedmf.F90
ranges: L8481-L8501
file_lines: 8776
file_md5: ec93fee9745a3e0b25be55a61b5aff8a
display: line-numbered (strip L-prefix and !file: line to restore)
range_md5: 0fffc49a4756d468b07c5a88b2f7c3ec
seg_lines: 21
-->

```fortran
!file: phys/MYNN-EDMF/module_bl_mynnedmf.F90    L8481-L8501
L08481    FUNCTION xl_blend(t)
L08482  
L08483      use module_bl_mynnedmf_common, only: xlv,xls,cpv,cliq,cice,t0c,tice,&
L08484           one,kind_phys
L08485  
L08486        real(kind_phys), intent(in):: t
L08487        real(kind_phys):: xl_blend,xlvt,xlst,chi
L08488        !note: t0c = 273.15, tice is set in mynn_common
L08489  
L08490        IF (t .GE. t0c) THEN
L08491            xl_blend = xlv + (cpv-cliq)*(t-t0c)  !vaporization/condensation
L08492        ELSE IF (t .LE. tice) THEN
L08493            xl_blend = xls + (cpv-cice)*(t-t0c)  !sublimation/deposition
L08494        ELSE
L08495            xlvt = xlv + (cpv-cliq)*(t-t0c)  !vaporization/condensation
L08496            xlst = xls + (cpv-cice)*(t-t0c)  !sublimation/deposition
L08497  !          chi  = (273.16-t)/(273.16-240.)
L08498            chi  = (t0c - t)/(t0c - tice)
L08499            xl_blend = (one-chi)*xlvt + chi*xlst     !blended
L08500        END IF
L08501  
```

> `xl_blend`：潜热的温度混合（Kircchoff 线性式 `xlv + (cpv−cliq)·(T−T0)` / `xls + (cpv−cice)·(T−T0)` 按 chi 插值）——与 Thompson 主实体的 `lvap(T)`（code_07a §07a.8.3）同思想但区间不同（这里 240–273.15 K 全混）。

## 09b.11 `phim` / `phih`：Puhales (2020) 新相似函数

<!-- code_extract code_extract.py v1.1
source: phys/MYNN-EDMF/module_bl_mynnedmf.F90
ranges: L8506-L8603
file_lines: 8776
file_md5: ec93fee9745a3e0b25be55a61b5aff8a
display: line-numbered (strip L-prefix and !file: line to restore)
range_md5: 371aa3c76b7da2f3edab88e8c602641c
seg_lines: 98
-->

```fortran
!file: phys/MYNN-EDMF/module_bl_mynnedmf.F90    L8506-L8603
L08506    FUNCTION phim(zet)
L08507       ! New stability function parameters for momentum (Puhales, 2020, WRF 4.2.1)
L08508       ! The forms in unstable conditions (z/L < 0) use Grachev et al. (2000), which are a blend of 
L08509       ! the classical (Kansas) forms (i.e., Paulson 1970, Dyer and Hicks 1970), valid for weakly 
L08510       ! unstable conditions (-1 < z/L < 0). The stability functions for stable conditions use an
L08511       ! updated form taken from Cheng and Brutsaert (2005), which extends the validity into very
L08512       ! stable conditions [z/L ~ O(10)].
L08513        use module_bl_mynnedmf_common, only: cphm_unst,zero,one,two,p333,p5,p666,kind_phys
L08514  
L08515        real(kind_phys), intent(in):: zet
L08516        real(kind_phys):: dummy_0,dummy_1,dummy_11,dummy_2,dummy_22,dummy_3,dummy_33,dummy_4,dummy_44,dummy_psi
L08517        real(kind_phys), parameter :: am_st=6.1, bm_st=2.5, rbm_st=1./bm_st
L08518        real(kind_phys), parameter :: ah_st=5.3, bh_st=1.1, rbh_st=1./bh_st
L08519        real(kind_phys), parameter :: am_unst=10., ah_unst=34.
L08520        real(kind_phys):: phi_m,phim
L08521  
L08522        if ( zet >= zero ) then
L08523           dummy_0 = one+zet**bm_st
L08524           dummy_1 = zet+dummy_0**(rbm_st)
L08525           dummy_11= one+dummy_0**(rbm_st-1)*zet**(bm_st-one)
L08526           dummy_2 = (-am_st/dummy_1)*dummy_11
L08527           phi_m   = one-zet*dummy_2
L08528        else
L08529           dummy_0 = (one-cphm_unst*zet)**0.25
L08530           phi_m   = one/dummy_0
L08531           dummy_psi = two*log(p5*(one+dummy_0))+log(p5*(one+dummy_0**2))-two*atan(dummy_0)+1.570796
L08532  
L08533           dummy_0 = (one-am_unst*zet)          ! parentesis arg
L08534           dummy_1 = dummy_0**p333          ! y
L08535           dummy_11=-p333*am_unst*dummy_0**(-p666) ! dy/dzet
L08536           dummy_2 = p333*(dummy_1**2+dummy_1+one)      ! f
L08537           dummy_22= p333*dummy_11*(two*dummy_1+one)    ! df/dzet
L08538           dummy_3 = 0.57735*(two*dummy_1+one)  ! g
L08539           dummy_33= 1.1547*dummy_11            ! dg/dzet
L08540           dummy_4 = 1.5*log(dummy_2)-1.73205*atan(dummy_3)+1.813799364 !psic
L08541           dummy_44= (1.5/dummy_2)*dummy_22-1.73205*dummy_33/(one+dummy_3**2)! dpsic/dzet
L08542  
L08543           dummy_0 = zet**2
L08544           dummy_1 = one/(one+dummy_0) ! denon
L08545           dummy_11= two*zet         ! denon/dzet
L08546           dummy_2 = ((one-phi_m)/zet+dummy_11*dummy_4+dummy_0*dummy_44)*dummy_1
L08547           dummy_22= -dummy_11*(dummy_psi+dummy_0*dummy_4)*dummy_1**2
L08548  
L08549           phi_m = one-zet*(dummy_2+dummy_22)
L08550        end if
L08551  
L08552        !phim = phi_m - zet
L08553        phim = phi_m
L08554  
L08555    END FUNCTION phim
L08556  ! ===================================================================
L08557  
L08558    FUNCTION phih(zet)
L08559      ! New stability function parameters for heat (Puhales, 2020, WRF 4.2.1)
L08560      ! The forms in unstable conditions (z/L < 0) use Grachev et al. (2000), which are a blend of
L08561      ! the classical (Kansas) forms (i.e., Paulson 1970, Dyer and Hicks 1970), valid for weakly
L08562      ! unstable conditions (-1 < z/L < 0). The stability functions for stable conditions use an
L08563      ! updated form taken from Cheng and Brutsaert (2005), which extends the validity into very
L08564      ! stable conditions [z/L ~ O(10)].
L08565        use module_bl_mynnedmf_common, only: cphh_unst,zero,one,two,p333,p5,p666,kind_phys
L08566  
L08567        real(kind_phys), intent(in):: zet
L08568        real(kind_phys):: dummy_0,dummy_1,dummy_11,dummy_2,dummy_22,dummy_3,dummy_33,dummy_4,dummy_44,dummy_psi
L08569        real(kind_phys), parameter :: am_st=6.1, bm_st=2.5, rbm_st=1./bm_st
L08570        real(kind_phys), parameter :: ah_st=5.3, bh_st=1.1, rbh_st=1./bh_st
L08571        real(kind_phys), parameter :: am_unst=10., ah_unst=34.
L08572        real(kind_phys):: phh,phih
L08573  
L08574        if ( zet >= zero ) then
L08575           dummy_0 = one+zet**bh_st
L08576           dummy_1 = zet+dummy_0**(rbh_st)
L08577           dummy_11= one+dummy_0**(rbh_st-one)*zet**(bh_st-one)
L08578           dummy_2 = (-ah_st/dummy_1)*dummy_11
L08579           phih    = one-zet*dummy_2
L08580        else
L08581           dummy_0 = (one-cphh_unst*zet)**p5
L08582           phh     = one/dummy_0
L08583           dummy_psi = two*log(p5*(one+dummy_0))
L08584  
L08585           dummy_0 = (one-ah_unst*zet)         ! parenthesis arg
L08586           dummy_1 = dummy_0**p333         ! y
L08587           dummy_11=-p333*ah_unst*dummy_0**(-p666) ! dy/dzet
L08588           dummy_2 = p333*(dummy_1**2+dummy_1+one)      ! f
L08589           dummy_22= p333*dummy_11*(two*dummy_1+one)    ! df/dzet
L08590           dummy_3 = 0.57735*(two*dummy_1+one) ! g
L08591           dummy_33= 1.1547*dummy_11           ! dg/dzet
L08592           dummy_4 = 1.5*log(dummy_2)-1.73205*atan(dummy_3)+1.813799364 !psic
L08593           dummy_44= (1.5/dummy_2)*dummy_22-1.73205*dummy_33/(one+dummy_3**2)! dpsic/dzet
L08594  
L08595           dummy_0 = zet**2
L08596           dummy_1 = one/(one+dummy_0)         ! denon
L08597           dummy_11= two*zet                   ! ddenon/dzet
L08598           dummy_2 = ((one-phh)/zet+dummy_11*dummy_4+dummy_0*dummy_44)*dummy_1
L08599           dummy_22= -dummy_11*(dummy_psi+dummy_0*dummy_4)*dummy_1**2
L08600  
L08601           phih = one-zet*(dummy_2+dummy_22)
L08602        end if
L08603  
```

> - **设计**（头注释）：稳定侧用 **Cheng & Brutsaert (2005)**（`am_st=6.1, bm_st=2.5` 幂律有理式——把稳定函数的有效性延到 z/L ~ O(10) 强稳定）；不稳定侧用 **Grachev et al. (2000)**（Kansas（Paulson/Dyer-Hicks）与 Businger-Dyer 形式的混合，适用 −1<z/L<0），实现是一套 `dummy_0…dummy_44` 的链式求导（ψ 函数及其导数）——**复杂度高但光滑**。
> - **调用位**：主入口 `bl_mynn_stfunc=1` 时（§09a.4.5）以及 `phi_m = phim(zet)`（TKE 收支底边界）——**默认路径仍走 Kansas 分支**，新函数待命。

## 09b.12 `topdown_cloudrad`：云顶辐射冷却的解析 TKE 源

<!-- code_extract code_extract.py v1.1
source: phys/MYNN-EDMF/module_bl_mynnedmf.F90
ranges: L8605-L8770
file_lines: 8776
file_md5: ec93fee9745a3e0b25be55a61b5aff8a
display: line-numbered (strip L-prefix and !file: line to restore)
range_md5: a6b00569be08e2edd5f00c9766f4eb37
seg_lines: 166
-->

```fortran
!file: phys/MYNN-EDMF/module_bl_mynnedmf.F90    L8605-L8770
L08605  ! ==================================================================
L08606   subroutine topdown_cloudrad(kts,kte,                         &
L08607                 &dz1,zw,fltv,u1,v1,xland,kpbl,pblh,            &
L08608                 &sqc,sqi,sqw,thl,th1,ex1,pres1,rho1,thv,       &
L08609                 &cldfra_bl1,qc_bl,qi_bl,rthraten,              &
L08610                 &tkeprod_dn,psig,                              &
L08611                 &maxtkeprod,cldtop_cooling,ent_eff)
L08612  
L08613     use module_bl_mynnedmf_common, only: cp,ep_2,xlv,r_d,p608, &
L08614          xlvcp,grav,zero,one,two,three,eight,p1,p2,p25,p3,     &
L08615          p333,p5,kind_phys
L08616     
L08617      !input
L08618      integer,         intent(in) :: kte,kts
L08619      real(kind_phys), dimension(kts:kte), intent(in) :: dz1,sqc,sqi,sqw,&
L08620            thl,th1,ex1,pres1,rho1,thv,cldfra_bl1,qc_bl,qi_bl
L08621      real(kind_phys), dimension(kts:kte), intent(in) :: rthraten
L08622      real(kind_phys), dimension(kts:kte+1), intent(in) :: zw
L08623      real(kind_phys), intent(in) :: pblh,fltv,u1,v1,psig
L08624      real(kind_phys), intent(in) :: xland
L08625      integer        , intent(in) :: kpbl
L08626      !output - production of tke from cloud-top radiative cooling
L08627      real(kind_phys), dimension(kts:kte), intent(inout) :: tkeprod_dn
L08628      real(kind_phys), intent(inout) :: maxtkeprod
L08629      real(kind_phys), intent(inout) :: cldtop_cooling
L08630      real(kind_phys), intent(inout) :: ent_eff
L08631      !local
L08632      real(kind_phys),parameter:: dz500   = 500.  !scale height for pbl
L08633      real(kind_phys),parameter:: dz200   = 200.  !scale height for entrainment layer
L08634      real(kind_phys),parameter:: cooling_thresh = -0.000069  !activation threshold of turbulence
L08635                                                  !-0.000116 is ~ -10 C cooling at cloud top per day
L08636                                                  !-0.000093 is ~  -8 C cooling at cloud top per day
L08637                                                  !-0.000069 is ~  -6 C cooling at cloud top per day
L08638      real(kind_phys), dimension(kts:kte) :: zfac,zfacent,tkeprodorig
L08639      real(kind_phys) :: dthvx,tmp1,zfacent_max,zagl
L08640      real(kind_phys) :: temps,templ,zl1,zb1,dz_ent,wstar_rad,maxcooling
L08641      real(kind_phys) :: f0,radflux,went,rcldb,rvls,minrad,zminrad,dp
L08642      real(kind_phys) :: wspd_pbl,ac_wsp
L08643      real(kind_phys), parameter :: pfac =2.0, zfmin = 0.01, phifac=8.0
L08644      integer :: k,kk,kminrad
L08645      logical :: cloudflg
L08646      logical,parameter:: debug=.false.
L08647  
L08648      cloudflg       = .false.
L08649      minrad         = zero
L08650      kminrad        = kpbl
L08651      zminrad        = pblh
L08652      !save the tke production from the downdraft scheme for comparison
L08653      tkeprodorig(kts:kte)=tkeprod_dn(kts:kte)
L08654      
L08655      !check for stratocumulus- or fog-tops with cooling at top
L08656      do k = 1,min(kpbl+10,kte-1)
L08657         maxcooling = minval(rthraten(max(kts,k-1):k+1))
L08658         !---------------------------------criteria for downdraft activa tion:
L08659         if ((cldfra_bl1(k).gt.p5 .and. cldfra_bl1(k+1).lt.p5) .and. &  !1) stratocu cloud top exists
L08660             (maxcooling  .lt. cooling_thresh)) then                    !2) significant radiative cooling
L08661            ! found sc cloud with significant radiative cooling
L08662            cloudflg =.true.
L08663            if (maxcooling < minrad) then
L08664               minrad    =maxcooling      !maximum cooling rate at cloud top
L08665               kminrad  = k
L08666               zminrad  = zw(k) + p5*dz1(k) !Best estimate of height of TKE source (top of downdrafts)
L08667            endif
L08668         endif
L08669      enddo
L08670  
L08671      if (cloudflg) then
L08672         zl1     = p25*dz1(kts)
L08673         k       = kminrad
L08674  
L08675         templ   = thl(k)*ex1(k)
L08676         !rvls is ws at full level
L08677         rvls    = 100.*6.112*EXP(17.67*(templ-273.16)/(templ-29.65))*(ep_2/pres1(k+1))
L08678         temps   = templ + (sqw(k)-rvls)/(cp/xlv  +  ep_2*xlv*rvls/(r_d*templ**2))
L08679         rvls    = 100.*6.112*EXP(17.67*(temps-273.15)/(temps-29.65))*(ep_2/pres1(k+1))
L08680         rcldb   = max(sqw(k)-rvls,zero)         !resolved cloud water
L08681         rcldb   = max(rcldb, qc_bl(k)+qi_bl(k)) !any type of cloud water (sgs or resolved)
L08682  
L08683         !entrainment efficiency
L08684         dthvx   = (thl(k+2) + th1(k+2)*p608*sqw(k+2)) - &
L08685                   (thl(k)   + th1(k)  *p608*sqw(k))
L08686         !reduce vertical resolution sensitivity; normalize to 200 m depth
L08687         dz_ent  = (dz1(k  )*dz1(k+1)+dz1(k+1)*dz1(k  ))/(dz1(k+1)+dz1(k)) + &
L08688                   (dz1(k+1)*dz1(k+2)+dz1(k+2)*dz1(k+1))/(dz1(k+1)+dz1(k+2)) 
L08689         dthvx   = dthvx * dz200/dz_ent  !normalized gradient
L08690         dthvx   = max(dthvx, p1)
L08691         tmp1    = xlvcp * rcldb/(ex1(k)*dthvx)
L08692         !entrainment efficiency: originally from Nichols and Turton (1986), where a2 = 60, but lowered
L08693         !here to 8, as in Grenier and Bretherton (2001).
L08694         ent_eff = min(two, p2 + p2*eight*tmp1)
L08695  
L08696         f0      = zero
L08697         do kk = max(kts,kminrad-1),kminrad+1
L08698            radflux = rthraten(kk)*ex1(kk)             !converts theta/s to temp/s
L08699            dp      = rho1(k)*grav*dz1(k)
L08700            radflux = radflux * cp / grav * dp         !converts temp/s to w/m^2 over layer
L08701            if (radflux < zero ) then
L08702               f0   = abs(radflux)+f0                  !sum of cooling (w/m^2) over relevant layers
L08703            endif
L08704         enddo
L08705  
L08706         !more strict limits over land to reduce stable-layer mixouts
L08707         if ((xland-1.5).ge.zero) then     ! water
L08708            f0     = min(f0, 150.0_kind_phys)
L08709         else                              ! land - limited considerably
L08710            f0     = min(p25*f0, 30._kind_phys)
L08711         endif
L08712         cldtop_cooling = abs(minrad) * 3600.   ! (K/hr) max cooling 
L08713         
L08714         !entrainment from pbl top thermals
L08715         wstar_rad = 1.25_kind_phys * ( grav/thv(k) * dz200 * f0 / (rho1(k) * cp) ) **p333
L08716         wstar_rad = min(max(wstar_rad, p1), three)
L08717         dthvx     = max(thv(k+1)-thv(k), p1)
L08718         went      = p333*ent_eff*wstar_rad     !entrainment velocity (m/s)
L08719  
L08720         !compute normalized analytical profiles (max=1). constrain the profile of tke production to not
L08721         !always go to the surface if forcing isnt strong enough, i.e., depth ~ wstar * Timescale of descent
L08722         zb1       = max(zl1, zminrad - wstar_rad*800._kind_phys)
L08723         do k = kts,kminrad+3
L08724            !for fog at k=1, make min height above ground (zagl) larger than first model deptk
L08725            zagl       = zw(k) + p5*dz1(k)
L08726            if (k==kts .and. kminrad==kts) zagl = 0.4_kind_phys * dz1(kts)
L08727            !analytic vertical profile
L08728            zfac(k)    = min(max((one - max(zero,zagl-zb1)/(zminrad-zl1)), zfmin), one)
L08729            zfacent(k) = max((zminrad-zagl)/zminrad, zero)*(one-zfac(k))**3
L08730         enddo
L08731         zfacent_max = maxval(zfacent(kts:kminrad+3))
L08732         zfacent     = zfacent/max(zfacent_max, 1e-5_kind_phys)  !normalize zfacent
L08733  
L08734         !calculate tke production
L08735         do k = kts,kminrad+3
L08736            tkeprod_dn(k) = max(tkeprod_dn(k), p3*ent_eff*wstar_rad**3/dz500*zfacent(k))
L08737            tkeprod_dn(k) = max(tkeprod_dn(k), zero)
L08738            tkeprod_dn(k) = min(0.0004_kind_phys, tkeprod_dn(k))
L08739         enddo
L08740         !make sure there is some TKE source at the max cooling level
L08741         tkeprod_dn(kminrad)=max(tkeprod_dn(kminrad), p333*tkeprod_dn(max(kts,kminrad-1)))
L08742         !make sure there is a small TKE source above the max cooling level
L08743         tkeprod_dn(kminrad+1)=max(tkeprod_dn(kminrad+1), min(p5,ent_eff)*tkeprod_dn(max(kts,kminrad)))
L08744         
L08745         !taper off tke production in high-wind conditions and at high resolutions
L08746         wspd_pbl   = sqrt(max(u1**2 + v1**2, 0.01_kind_phys))
L08747         ac_wsp     = one - min(max(zero, wspd_pbl - 10._kind_phys)/15._kind_phys, one)
L08748         tkeprod_dn = tkeprod_dn * min(ac_wsp, psig)
L08749      endif !end cloud check
L08750  
L08751      !calculate the maximum tke production in the profile and convert to an hourly rate.
L08752      maxtkeprod = maxval(tkeprod_dn)*3600.
L08753      
L08754      if (cloudflg .and. debug) then
L08755         !debug printouts
L08756         print *, '-----------------------------------------------------------------'
L08757         if ((xland-1.5).ge.zero) then
L08758            print *, ' over water, kminrad=',kminrad
L08759         else
L08760            print *, ' over land, kminrad=',kminrad
L08761         endif
L08762         print *, ' ctop cooling (K/hr)=',minrad*3600.,' rad cooling (W/m^2)=',f0
L08763         print *, ' ent_eff=',ent_eff,' went=',went,' w*rad=',wstar_rad
L08764         print *, '  k    cldfra   dT/dt(hr)  dTKE/dt_orig dTKE/dt(hr)  zfacent'
L08765         print *, '-----------------------------------------------------------------'
L08766         do k = kminrad+3,kts,-1
L08767            print '(I4,5F11.5)', k, cldfra_bl1(k), rthraten(k)*3600., tkeprodorig(k)*3600., tkeprod_dn(k)*3600.,  zfacent(k) 
L08768         enddo
L08769      endif
L08770      
```

> - **触发**：与 ddmp_mf 相同的云顶判据（层云顶 + 冷却 < −6 °C/天）——**它是 ddmp_mf 的伴生通道**（主入口里先后调用，本函数保证“MF 不适用时仍有 TKE 源”）。返回三个诊断：`maxtkeprod/cldtop_cooling/ent_eff`。
> - **强迫强度 f0**：云顶附近辐射冷却的垂直积分（W/m²），**水面限 150、陆地限 0.25·f0 且 ≤30 W/m²**（注释：“more strict limits over land to reduce stable-layer mixouts”——陆地层云混合过强是历史偏差）。
> - **解析剖面**：`zfac` 线性衰减（从云顶到 `zb1 = max(0.25dz, zminrad − w*·800)`——**下沉穿透深度 = w*×时间尺度 800 s**）、`zfacent` 三次方卷入剖面（归一化）。
> - **TKE 生产**：`tkeprod_dn = max(orig, 0.3·ent_eff·w*³/dz500·zfacent)` ≤ 4e-4——**w*³ 标度（对流 TKE 通量）× ent_eff（云顶效率）× 解析形状**；云顶处保底 1/3 邻层值、其上保底 min(0.5, ent_eff) 倍。
> - **衰减**：风衰减 `ac_wsp`（>10 m/s 线性）× `psig`（灰区）——**三重一致性**（与 ddmp_mf 面积、DMP_mf 触发共用同一对衰减函数）。

## 09b.13 改造入口（→ 教材 ch20/ch21 案索引）

| 想改什么 | 动哪里 | 注意 |
|---|---|---|
| 羽流数/尺寸谱 | `DMP_mf` 的 nup/lmin/lmax/d | d 的幂律敏感性注释在侧 |
| 卷入率 | `DMP_mf` entfac（Tian & Kuang） | 注释保留 Neggers/TEMF 备选 |
| 下沉流触发 | `ddmp_mf` cooling_thresh | 注释三档阈值折算 K/天 |
| 灰区行为 | `SCALE_AWARE` 两因子 | 六代函数考古可对比 |
| 负值修复策略 | `moisture_check` | 与 Thompson 守恒段口径对读 |
| 饱和口径 | blend 三函数 | 与 Thompson RSLF/RSIF 系数同源 |
| PBLH 判据 | `GET_PBLH` stable_method/delt_thv | 水陆阈值分开 |
| 教材案 | ch21 案（BouLac 对比/虚拟温度） | — |

## 09b.14 上下游链接

- **上游（本模块内）**：code_09a——主入口调用序列、闭合常数（module_bl_mynnedmf_common 的 b1/b2/a1/a2）、`mym_turbulence/mym_predict` 的求解器对接。
- **外部对接**：`module_mp_thompson.F`（blend 函数族同源、`rthraten` 来自辐射方案的耦合——ddmp_mf/topdown 的输入）；`module_pbl_driver.F`（code_22，CASE 分发）。
- **教材**：ch14（MYNN-EDMF 精读：qke=2TKE、dmp/ddmp_mf、get_pblh 全文、BouLac 亲缘）、ch15（对流速度尺度 w* 与夹卷的积云对应）、ch21（solve_em 的 PBL 调用位）。
