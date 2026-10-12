# code_22 — PBL 驱动器（module_pbl_driver.F 全 CASE 走读）

## 一、版本指纹

| 源文件 | 行数 | md5（整文件，按字节） |
|---|---|---|
| phys/module_pbl_driver.F | 2887 | 1c4ca2a3bd7baa4c31b48527e60a4cad |

- 抽取工具：workspace/scripts/code_extract.py v1.2，2026-10-12；块首指纹注释自带 range_md5 可逐块复核。
- 本篇 B 级「全 CASE 走读」：pbl_driver 主入口的参数清单（L11–L828，纯哑元声明）不收录——各方案的完整实参表就是每个 CASE 分支里的 CALL 语句本身；其余执行路径全收。

## 二、定位

一句话：五大 physics driver 之一——把 bl_pbl_physics 的整型开关翻译成对具体 PBL 方案子程序的调用，自己不含一行业务物理。

**谁在调它**：动力侧 `dyn_em/module_first_rk_step_part1.F` 在每个时间步的 RK 循环开头调用 pbl_driver（物理调用链：surface driver → pbl driver，见 [ch21_solve_em_dynamics.md](../ch21_solve_em_dynamics.md) 的非时间分裂物理节拍）；本篇的直接下游是 14 个 PBL 方案入口——MYNN-EDMF 的方案实体已在 [code_09a_module_bl_mynnedmf.md](code_09a_module_bl_mynnedmf.md)、[code_09b_module_bl_mynnedmf.md](code_09b_module_bl_mynnedmf.md) 全文精读，面层侧对应 [code_10_module_sf_mynnsfc.md](code_10_module_sf_mynnsfc.md)。

**Registry 方案号对照**（bl_pbl_physics，实测自 Registry.EM_COMMON package 行）：

| 值 | package | 方案 | Registry 挂载的 state |
|---|---|---|---|
| 0 | — | 关闭 | — |
| 1 | ysuscheme | YSU | — |
| 2 | myjpblscheme | MYJ（TKE 闭合 1.5 阶） | tke_pbl, el_pbl |
| 3 | gfsscheme | GFS（旧版局部扩散） | — |
| 4 | qnsepblscheme | QNSE | tke_pbl, el_pbl, massflux_EDKF 等 13 项 |
| 5 | mynnpblscheme | MYNN-EDMF（2.5/3 共用入口） | qke, tsq, qsq, cov, cldfra_bl, el_pbl 等 + scalar qke_adv |
| 7 | acmpblscheme | ACM2 | — |
| 8 | boulacscheme | BouLac（论文 2 边界层首选） | el_pbl, tke_pbl, wu/wv/wt/wq_tur |
| 9 | camuwpblscheme | CAMUW | tauresx2d 等 9 项 |
| 10 | temfpblscheme | TEMF | te_temf 等 17 项 |
| 11 | shinhongscheme | ShinHong（YSU 扩展） | el_pbl, tke_pbl |
| 12 | gbmpblscheme | GBM | exch_tke, el_pbl, tke_pbl |
| 16 | eepsscheme | EEPS（集合型 PBL） | pek_pbl, pep_pbl + scalar pek_adv/pep_adv |
| 17 | kepsscheme | k-ε（BEP 配套） | tpe/diss/tke_pbl, pr_pbl, w*_tur 等 |
| 99 | mrfscheme | MRF（遗留） | — |

> **警示**：切换 bl_pbl_physics 到一个「挂载 state 不同」的方案（如 1→5），wrfout 输入历史里没有 qke/tsq/cov 等新 state——必须从 WPS 重跑 real 重新生成 wrfinput（[ch08_running_wrf.md](../ch08_running_wrf.md)）； namelist 改了但 state 缺失会在初始化时报 Registry 缺变量。源码注释里的方案编号表（本文件 L223–240）把 TEMF 写成 10、keps 写成 17，与 Registry 一致；「mynnpbl2/3」是历史名称，4.8.0 里只有一个 MYNNPBLSCHEME（=5）。

## 三、主入口 pbl_driver

### 3.1 USE 清单与方案点名册

<!-- code_extract code_extract.py v1.2
source: phys/module_pbl_driver.F
ranges: L166-L242
file_lines: 2887
file_md5: 1c4ca2a3bd7baa4c31b48527e60a4cad
display: line-numbered (strip L-prefix and !file: line to restore)
range_md5: 46e34e41714cbd726699640ad840fdea
seg_lines: 77
-->

```fortran
!file: phys/module_pbl_driver.F    L166-L242
L00166  !------------------------------------------------------------------
L00167  #if (EM_CORE==1)
L00168     USE module_state_description, ONLY :                            &
L00169                     YSUSCHEME,MRFSCHEME,GFSSCHEME,MYJPBLSCHEME,ACMPBLSCHEME,&
L00170                     QNSEPBLSCHEME,MYNNPBLSCHEME,BOULACSCHEME,         &
L00171                     CAMUWPBLSCHEME,BEPSCHEME,BEP_BEMSCHEME,MYJSFCSCHEME, &
L00172                     FITCHSCHEME,SHINHONGSCHEME,                       &
L00173                     TEMFPBLSCHEME,GBMPBLSCHEME,EEPSSCHEME,KEPSSCHEME,                  &
L00174                     MAVSCHEME,  & ! Yulong add for WLM
L00175                     CAMMGMPSCHEME,p_qi,p_qni,p_qnc,param_first_scalar,& !CAMMGMPSCHEME, p_qni,p_qnc is used for camuwpbl scheme
L00176                     p_qnwfa,p_qnifa,p_qnbca
L00177  #if ( WRFPLUS == 1 )
L00178     USE module_state_description, ONLY : SURFDRAGSCHEME
L00179  #endif
L00180  #else
L00181     USE module_state_description, ONLY :                            &
L00182                     YSUSCHEME,MRFSCHEME,GFSSCHEME,MYJPBLSCHEME,ACMPBLSCHEME &
L00183                     , QNSEPBLSCHEME, p_qi,param_first_scalar &
L00184                     , TEMFPBLSCHEME, GFSEDMFSCHEME           &
L00185                     , CAMUWPBLSCHEME                                       &
L00186                     , FITCHSCHEME, SHINHONGSCHEME                          &
L00187                     , MAVSCHEME  ! Yulong add for WLM
L00188                     , GBMPBLSCHEME, MYJSFCSCHEME
L00189  #endif
L00190  
L00191     USE module_model_constants
L00192  
L00193  ! *** add new modules of schemes here
L00194  
L00195     USE module_bl_myjpbl
L00196     USE module_bl_qnsepbl
L00197     USE module_bl_ysu
L00198     USE module_bl_shinhong
L00199     USE module_bl_mrf
L00200     USE module_bl_gfs
L00201     USE module_bl_acm
L00202     USE module_bl_gwdo
L00203     USE module_bl_gwdo_gsl
L00204     USE module_bl_myjurb
L00205     USE module_bl_boulac
L00206  #if ( WRFPLUS == 1 )
L00207     USE module_bl_surface_drag
L00208  #endif
L00209     USE module_bl_camuwpbl_driver, only:CAMUWPBL
L00210     USE module_bl_temf
L00211     USE module_bl_mfshconvpbl
L00212     USE module_bl_gbmpbl
L00213  #if (EM_CORE==1)
L00214     USE module_bl_mynnedmf_driver
L00215     USE module_bl_eeps
L00216     USE module_bl_keps
L00217     USE module_bl_fogdes
L00218     USE module_wind_fitch
L00219     USE module_wind_mav ! Yulong add for WLM
L00220  #endif
L00221     use module_ra_gfdleta, only: cal_mon_day
L00222  
L00223     !  This driver calls subroutines for the PBL parameterizations.
L00224     !
L00225     !  pbl scheme:
L00226     !      1. ysupbl
L00227     !      2. myjpbl
L00228     !      4. qnsepbl
L00229     !      5. mynnpbl2
L00230     !      6. mynnpbl3
L00231     !      7. acmpbl
L00232     !      8. boulacpbl
L00233     !      9. camuwpbl
L00234     !      10. temfpbl
L00235     !      11. shinhongpbl
L00236     !      17. kepsstpe
L00237     !      98. surface_drag
L00238     !      99. mrfpbl
L00239     !      12. gbmpbl
L00240     !
L00241  !------------------------------------------------------------------
L00242     IMPLICIT NONE
```

> 讲解：①方案常量全部来自 module_state_description——它们是 Registry package 语句生成的整型符号，不是硬编码数字（ch04 的机制）；②EM 核下 USE 了一张扩展名单：mynnedmf_driver、eeps、keps、fogdes、wind_fitch（风机）、wind_mav（风机变体）；③紧随其后的网格结构注释（kms 在底、kme 在顶、半层/整层交错）是所有 physics driver 共用的约定声明——方案作者最容易踩的 k 方向坑。

### 3.2 局部变量与方案前置旗标

<!-- code_extract code_extract.py v1.2
source: phys/module_pbl_driver.F
ranges: L844-L907
file_lines: 2887
file_md5: 1c4ca2a3bd7baa4c31b48527e60a4cad
display: line-numbered (strip L-prefix and !file: line to restore)
range_md5: 4f0859fd3df4d8eddb617b6b375cfd36
seg_lines: 64
-->

```fortran
!file: phys/module_pbl_driver.F    L844-L907
L00844  
L00845     REAL    :: DTMIN,DTBL
L00846  !
L00847     INTEGER :: initflag
L00848  !
L00849     INTEGER :: i,J,K,NK,jj,ij,its,ite,jts,jte
L00850     LOGICAL :: radiation
L00851     LOGICAL :: flag_bep
L00852     LOGICAL :: flag_myjsfc
L00853     LOGICAL :: flag_qv, flag_qc, flag_qr, flag_qi, flag_qs, flag_qg, &
L00854                flag_qnc,flag_qni, flag_qnwfa, flag_qnifa, flag_qnbca
L00855     CHARACTER*256 :: message
L00856     REAL    :: next_bl_time
L00857     LOGICAL :: run_param , doing_adapt_dt , decided
L00858     LOGICAL :: do_adapt
L00859     integer iu_bep,iurb,idiff
L00860     real seamask,thsk,zzz,unew,vnew,tnew,qnew,umom,vmom
L00861     REAL :: z0,z1,z2,w1,w2
L00862     REAL, DIMENSION( ims:ime, kms:kme, jms:jme ) :: TKE_windfarm ! Yulong add for WLM
L00863     INTEGER :: ihour, jmonth, jday
L00864  !
L00865  ! FASDAS
L00866  !
L00867     REAL, DIMENSION( ims:ime, jms:jme ) , INTENT(  OUT) , OPTIONAL ::   QNORM
L00868     INTEGER, INTENT(IN   )                                         ::   fasdas
L00869     REAL                                                           ::   scrp1
L00870  !
L00871  ! END FASDAS
L00872  !
L00873  ! To accommodate shared physics
L00874     character*256 :: errmsg
L00875     integer :: errflg
L00876  !
L00877  !------------------------------------------------------------------
L00878  !
L00879  !!!!!!!if using BEP set flag_bep to true
L00880      SELECT CASE(sf_urban_physics)
L00881        CASE (BEPSCHEME)
L00882          flag_bep=.true.
L00883        CASE (BEP_BEMSCHEME)
L00884          flag_bep=.true.
L00885        CASE DEFAULT
L00886          flag_bep=.false.
L00887      END SELECT
L00888  
L00889      SELECT CASE(sf_sfclay_physics)
L00890        CASE (MYJSFCSCHEME)
L00891           flag_myjsfc=.true.
L00892        CASE DEFAULT
L00893           flag_myjsfc=.false.
L00894      END SELECT
L00895  !
L00896    flag_qv = .FALSE. ; IF ( PRESENT( F_QV ) ) flag_qv = F_QV
L00897    flag_qc = .FALSE. ; IF ( PRESENT( F_QC ) ) flag_qc = F_QC
L00898    flag_qr = .FALSE. ; IF ( PRESENT( F_QR ) ) flag_qr = F_QR
L00899    flag_qi = .FALSE. ; IF ( PRESENT( F_QI ) ) flag_qi = F_QI
L00900    flag_qs = .FALSE. ; IF ( PRESENT( F_QS ) ) flag_qs = F_QS
L00901    flag_qg = .FALSE. ; IF ( PRESENT( F_QG ) ) flag_qg = F_QG
L00902    flag_qnc = .FALSE. ; IF ( PRESENT( F_QNC ) ) flag_qnc = F_QNC !Used in CAMUWPBL
L00903    flag_qni = .FALSE. ; IF ( PRESENT( F_QNI ) ) flag_qni = F_QNI !Used in CAMUWPBL
L00904    flag_qnwfa = .FALSE. ; IF ( PRESENT( F_QNWFA ) ) flag_qnwfa = F_QNWFA
L00905    flag_qnifa = .FALSE. ; IF ( PRESENT( F_QNIFA ) ) flag_qnifa = F_QNIFA
L00906    flag_qnbca = .FALSE. ; IF ( PRESENT( F_QNBCA ) ) flag_qnbca = F_QNBCA
L00907  
```

> 讲解：①flag_bep 由 sf_urban_physics∈{BEPSCHEME, BEP_BEMSCHEME} 决定——BEP 感知是「城市冠层方案是否在场」的唯一判据，与 bl_pbl_physics 无关（MYJ、BouLac、ShinHong、KEPS 都会被传入 a_*_bep 族数组）；②flag_myjsfc 只影响 MYJ 配套面层的 ck/cd 诊断回传；③flag_qv…flag_qnbca 是水汽/云水/冰/气溶胶数浓度等示踪物的「在场」标志——WRF 变量按需实例化（param_first_scalar 机制），方案必须先探测再写入；④bl_pbl_physics=0 直接 return。

### 3.3 触发节拍与 PBL 时间步

<!-- code_extract code_extract.py v1.2
source: phys/module_pbl_driver.F
ranges: L909-L1035
file_lines: 2887
file_md5: 1c4ca2a3bd7baa4c31b48527e60a4cad
display: line-numbered (strip L-prefix and !file: line to restore)
range_md5: f3c89c62b8fa5ccf413bce36a83f6e1d
seg_lines: 127
-->

```fortran
!file: phys/module_pbl_driver.F    L909-L1035
L00909  
L00910  ! RAINBL in mm (Accumulation between PBL calls)
L00911  !
L00912     doing_adapt_dt = .FALSE.
L00913     IF ( PRESENT(adapt_step_flag) ) THEN
L00914        IF ( adapt_step_flag ) THEN
L00915           doing_adapt_dt = .TRUE.
L00916           IF ( bldtacttime .eq. 0. ) THEN
L00917              bldtacttime = CURR_SECS + bldt*60.
L00918           END IF
L00919        END IF
L00920     END IF
L00921  
L00922  !  Do we run through this scheme or not?
L00923  
L00924  !    Test 1:  If this is the initial model time, then yes.
L00925  !                ITIMESTEP=1
L00926  !    Test 2:  If the user asked for the pbl to be run every time step, then yes.
L00927  !                BLDT=0 or STEPBL=1
L00928  !    Test 3:  If not adaptive dt, and this is on the requested pbl frequency, then yes.
L00929  !                MOD(ITIMESTEP,STEPBL)=0
L00930  !    Test 4:  If using adaptive dt and the current time is past the last requested activate pbl time, then yes.
L00931  !                CURR_SECS >= BLDTACTTIME
L00932  
L00933  !  If we do run through the scheme, we set the flag run_param to TRUE and we set the decided flag
L00934  !  to TRUE.  The decided flag says that one of these tests was able to say "yes", run the scheme.
L00935  !  We only proceed to other tests if the previous tests all have left decided as FALSE.
L00936  
L00937  !  If we set run_param to TRUE and this is adaptive time stepping, we set the time to the next
L00938  !  pbl run.
L00939  
L00940     run_param = .FALSE.
L00941     decided = .FALSE.
L00942     IF ( ( .NOT. decided ) .AND. &
L00943          ( itimestep .EQ. 1 ) ) THEN
L00944        run_param   = .TRUE.
L00945        decided     = .TRUE.
L00946     END IF
L00947  
L00948     IF ( PRESENT(bldt) )THEN
L00949        IF ( ( .NOT. decided ) .AND. &
L00950             ( ( bldt .EQ. 0. ) .OR. ( stepbl .EQ. 1 ) ) ) THEN
L00951           run_param   = .TRUE.
L00952           decided     = .TRUE.
L00953        END IF
L00954     ELSE
L00955        IF ( ( .NOT. decided ) .AND. &
L00956                                     ( stepbl .EQ. 1 )   ) THEN
L00957           run_param   = .TRUE.
L00958           decided     = .TRUE.
L00959        END IF
L00960     END IF
L00961  
L00962     IF ( ( .NOT. decided ) .AND. &
L00963          ( .NOT. doing_adapt_dt ) .AND. &
L00964          ( MOD(itimestep,stepbl) .EQ. 0 ) ) THEN
L00965        run_param   = .TRUE.
L00966        decided     = .TRUE.
L00967     END IF
L00968  
L00969     IF ( ( .NOT. decided ) .AND. &
L00970          ( doing_adapt_dt ) .AND. &
L00971          ( curr_secs .GE. bldtacttime ) ) THEN
L00972        run_param   = .TRUE.
L00973        decided     = .TRUE.
L00974        bldtacttime = curr_secs + bldt*60
L00975     END IF
L00976  
L00977  
L00978   IF (run_param) THEN
L00979    radiation = .false.
L00980    IF (ra_lw_physics .gt. 0) radiation = .true.
L00981  
L00982  !---- 
L00983  ! CALCULATE CONSTANT
L00984   
L00985     DTMIN=DT/60.
L00986  ! PBL schemes need PBL time step for updates
L00987  
L00988      if (PRESENT(adapt_step_flag)) then
L00989         if (adapt_step_flag) then
L00990            do_adapt = .TRUE.
L00991         else
L00992            do_adapt = .FALSE.
L00993         endif
L00994      else
L00995         do_adapt = .FALSE.
L00996      endif
L00997  
L00998     if (PRESENT(BLDT)) then
L00999        if (bldt .eq. 0) then
L01000           DTBL = dt
L01001        ELSE
L01002           if (do_adapt) then
L01003              IF ( curr_secs .LT. 2. * dt ) THEN
L01004                 call wrf_message("WARNING: When using an adaptive time-step the boundary layer"// &
L01005                                  " time-step should be 0 (i.e., equivalent to model time-step).  ")
L01006                 call wrf_message("In order to proceed, for boundary layer calculations, the "// &
L01007                                  "boundary layer time-step "// &
L01008                                  "will be rounded to the nearest minute," )
L01009                 call wrf_message("possibly resulting in innacurate results.")
L01010              END IF
L01011              DTBL=bldt*60
L01012           else
L01013              DTBL=DT*STEPBL
L01014           endif
L01015        endif
L01016     else
L01017        DTBL=DT*STEPBL
L01018     endif
L01019  
L01020  !!Alberto. If idiff=1, then compute the tendencies at the end in the routine diff3d
L01021  !!Alberto. If idiff=0, then compute the tendencies in each PBL routine (standard version).
L01022         idiff=0
L01023  
L01024     IF ( idiff .EQ. 1 ) THEN
L01025       ALLOCATE (a_u(ims:ime,kms:kme,jms:jme))       ! Implicit component for the momemtum in X-direction
L01026       ALLOCATE (a_v(ims:ime,kms:kme,jms:jme))       ! Implicit component for the momemtum in Y-direction
L01027       ALLOCATE (a_t(ims:ime,kms:kme,jms:jme))       ! Implicit component for the Pot. Temp.
L01028       ALLOCATE (a_q(ims:ime,kms:kme,jms:jme))       ! Implicit component for the water vapor
L01029       ALLOCATE (b_u(ims:ime,kms:kme,jms:jme))       ! Explicit component for the momemtum in X-direction
L01030       ALLOCATE (b_v(ims:ime,kms:kme,jms:jme))       ! Explicit component for the momemtum in Y-direction
L01031       ALLOCATE (b_t(ims:ime,kms:kme,jms:jme))       ! Explicit component for the Pot. Temp.
L01032       ALLOCATE (b_q(ims:ime,kms:kme,jms:jme))       ! Explicit component for the water vapor
L01033       ALLOCATE (sf(ims:ime,kms:kme,jms:jme) )       ! surfaces
L01034       ALLOCATE (vl(ims:ime,kms:kme,jms:jme) )       ! volumes
L01035     ENDIF
```

> 讲解：①四个测试依序决定本步是否运行 PBL：首步必跑；bldt=0（随每步）或 stepbl=1；非自适应步长下 mod(itimestep, stepbl)=0；自适应步长下 curr_secs≥bldtacttime（到点后把下次触发时间顺延 bldt 分钟）。bldt 单位是分钟——PBL 允许隔步运行以省算力，与辐射的 bldt 机制同构；②DTBL：bldt=0 时取模式步长，自适应时直接取 bldt·60（并警告精度损失），否则 DT·STEPBL——方案内部的积分时长与模式时间步解耦；③idiff 在 L1021 被无条件写 0（Alberto 注释保留）：idiff=1 的「driver 统一隐式扩散」路径目前是休眠代码，详见 3.6。

### 3.4 状态保存、倾向清零与 a/b/sf/vl 预备

<!-- code_extract code_extract.py v1.2
source: phys/module_pbl_driver.F
ranges: L1036-L1171
file_lines: 2887
file_md5: 1c4ca2a3bd7baa4c31b48527e60a4cad
display: line-numbered (strip L-prefix and !file: line to restore)
range_md5: 62a19881c66e88600ee51245c7bc293e
seg_lines: 136
-->

```fortran
!file: phys/module_pbl_driver.F    L1036-L1171
L01036     
L01037  ! SAVE OLD VALUES
L01038  
L01039     !$OMP PARALLEL DO   &
L01040     !$OMP PRIVATE ( ij,i,j,k )
L01041  
L01042     DO ij = 1 , num_tiles
L01043        DO j=j_start(ij),j_end(ij)
L01044        DO i=i_start(ij),i_end(ij)
L01045           TSKOLD(i,j)=TSK(i,j)
L01046           USTOLD(i,j)=UST(i,j)
L01047           ZNTOLD(i,j)=ZNT(i,j)
L01048           HPBL_HOLD(i,j)=PBLH(i,j)
L01049  
L01050           DO k=kts,kte
L01051              v_phytmp(i,k,j)=v_phy(i,k,j)+v_frame
L01052              u_phytmp(i,k,j)=u_phy(i,k,j)+u_frame
L01053           ENDDO
L01054  
L01055  ! PSFC : in Pa
L01056  
L01057           PSFC(I,J)=p8w(I,kms,J)
L01058  
L01059           DO k=kts,min(kte+1,kde)
L01060              RTHBLTEN(I,K,J)=0.
L01061              RUBLTEN(I,K,J)=0.
L01062              RVBLTEN(I,K,J)=0.
L01063              IF ( PRESENT( RQCBLTEN )) RQCBLTEN(I,K,J)=0.
L01064              IF ( PRESENT( RQVBLTEN )) RQVBLTEN(I,K,J)=0.
L01065           ENDDO
L01066  
L01067           IF (flag_QI .AND. PRESENT(RQIBLTEN) ) THEN
L01068              DO k=kts,min(kte+1,kde)
L01069                 RQIBLTEN(I,K,J)=0.
L01070              ENDDO
L01071           ENDIF
L01072           !Following if condition is added for CAMUWPBL scheme
L01073           IF (flag_QNI .AND. PRESENT(RQNIBLTEN) ) THEN
L01074              DO k=kts,min(kte+1,kde)
L01075                 RQNIBLTEN(I,K,J)=0.
L01076              ENDDO
L01077           ENDIF
L01078        ENDDO
L01079        ENDDO
L01080  
L01081        IF (bl_pbl_physics .EQ. QNSEPBLSCHEME ) THEN
L01082  ! use u_phytmp instead of wthv_mf, and v_phytmp instead of lm_bl89
L01083             DO j=j_start(ij),j_end(ij)
L01084             DO i=i_start(ij),i_end(ij)
L01085             DO k=kms,kme
L01086                u_phytmp(i,k,j)=0.
L01087                v_phytmp(i,k,j)=0.
L01088             ENDDO
L01089             ENDDO
L01090             ENDDO
L01091        ENDIF
L01092  
L01093        IF ( idiff.eq.1 ) THEN
L01094  !Alberto
L01095  ! Here we should put a switch: 
L01096  ! if we do not use BEP, just initialize the values of the a, and b to zero, except for the lowest model level, 
L01097  ! where the heat and momentum fluxes are introduced         
L01098  ! if we use BEP, use the values computed by BEP weigthed by the urban fraction.
L01099  ! for the moment I put a simple "if" but it should be changed to a more elegant way after(using the CASE, maybe?)
L01100  !!!!!!!!!!!!!!
L01101  ! This is the more general way to go, however some of these variables (e. g. a_t, a_q) may be zero nearly all time. 
L01102  ! if we need to be as tight as possible for the memory we can think how to reduce the storage.
L01103  !!!!!!!!!!!!!!!!!!
L01104  ! This stuff is becoming large, probably better to put in a subroutine
L01105  !!!!!!!!!!!!!!!!!!!
L01106  ! preparing the a, b, sf, and vl terms
L01107           
L01108           IF (flag_bep) THEN    
L01109             do j=j_start(ij),j_end(ij)
L01110             do i=i_start(ij),i_end(ij)            
L01111             do k=kts,kte
L01112               a_u(i,k,j)=a_u_bep(i,k,j)
L01113               a_v(i,k,j)=a_v_bep(i,k,j)
L01114               a_t(i,k,j)=a_t_bep(i,k,j)
L01115               a_q(i,k,j)=a_q_bep(i,k,j)
L01116               b_u(i,k,j)=b_u_bep(i,k,j)
L01117               b_v(i,k,j)=b_v_bep(i,k,j)
L01118               b_t(i,k,j)=b_t_bep(i,k,j)
L01119               b_q(i,k,j)=b_q_bep(i,k,j)
L01120               vl(i,k,j)=vl_bep(i,k,j)
L01121               sf(i,k,j)=sf_bep(i,k,j)
L01122             enddo
L01123             sf(i,kte+1,j)=1.
L01124             enddo
L01125             enddo
L01126           ELSE
L01127             do j=j_start(ij),j_end(ij)
L01128             do i=i_start(ij),i_end(ij)
L01129             do k=kts,kte
L01130               a_u(i,k,j)=0.
L01131               a_v(i,k,j)=0.
L01132               a_t(i,k,j)=0.
L01133               a_q(i,k,j)=0.
L01134               b_u(i,k,j)=0.
L01135               b_v(i,k,j)=0.
L01136               b_t(i,k,j)=0.
L01137               b_q(i,k,j)=0.
L01138               vl(i,k,j)=1.
L01139               sf(i,k,j)=1.
L01140             enddo
L01141             sf(i,kte+1,j)=1.
L01142  ! fix the values for the surface fluxes (source/sink terms)
L01143  ! here for momentum the resolution is done implicitely
L01144  ! while for heat and moisture is done explicitely 
L01145              a_u(i,1,j)=(-ust(I,J)*ust(I,J))/dz8w(i,1,j)/((u_phy(i,1,j)**2+v_phy(i,1,j)**2.)**.5)           
L01146              a_v(i,1,j)=(-ust(I,J)*ust(I,J))/dz8w(i,1,j)/((u_phy(i,1,j)**2+v_phy(i,1,j)**2.)**.5)
L01147              b_t(i,1,j)=hfx(i,j)/rho(i,1,j)/CP/dz8w(i,1,j)
L01148              b_q(i,1,j)=qfx(i,j)/rho(i,1,j)/dz8w(i,1,j)
L01149  !! if you want to solve also the heat and moisture fluxes implicitely, uncomment the following lines.
L01150  !! (of course you will need the values of thz0,qz0,akhs).
L01151  !             b_t(i,1,j)=akhs(i,j)*(thz0(I,J))/dz8w(i,1,j)
L01152  !             b_q(i,1,j)=akhs(i,j)*(qz0(I,J))/dz8w(i,1,j)
L01153  !             a_t(i,1,j)=-1.*akhs(i,j)/dz8w(i,1,j)
L01154  !             a_q(i,1,j)=-1.*akhs(i,j)/dz8w(i,1,j)
L01155  !!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!
L01156             enddo
L01157             enddo
L01158             
L01159           ENDIF
L01160  
L01161          endif      
L01162                                             
L01163       
L01164   
L01165  !Alberto. From this point if some PBL scheme has a non local term 
L01166  ! (not dependent on the local values of the variable)
L01167  ! this can be added to b_t, b_q, or b_u, b_v.
L01168  !!!!!!!!!!!!!!!!!!!           
L01169   
L01170     ENDDO
L01171     !$OMP END PARALLEL DO
```

> 讲解：①TSKOLD/USTOLD/ZNTOLD/HPBL_HOLD 存旧值——面层方案在 PBL 之后用这些差分更新诊断量；②u_phytmp=u_phy+v_frame——**移动嵌套参考系**：所有方案拿到的是加上框架速度的风场（嵌套随大域风平移时物理风需要还原）；QNSE 方案把这两个 tmp 数组另用作 WTHV_MF/LM_BL89 传送带（L1081–1091 特意清零），是驱动层「借用」数组的罕见案例；③倾向数组清零到 kte+1；④idiff=1 时的 a/b/sf/vl 预备：BEP 在场时把 a_u_bep 等建筑拖曳系数搬进来，否则只有最低层放地表通量（a_u=−u*²/(dz·|V|) 动量隐式源、b_t=HFX/(ρ·cp·dz) 显式热源）——这套通用化设计（Martilli 2008）服务 BEP 的「建筑体积内源」需求。

### 3.5 方案分派 CASE 全走读

tile 循环开启，SELECT CASE(bl_pbl_physics)：

<!-- code_extract code_extract.py v1.2
source: phys/module_pbl_driver.F
ranges: L1173-L1231
file_lines: 2887
file_md5: 1c4ca2a3bd7baa4c31b48527e60a4cad
display: line-numbered (strip L-prefix and !file: line to restore)
range_md5: 6d86e2b35a336404f4a0b582fbf9ea18
seg_lines: 59
-->

```fortran
!file: phys/module_pbl_driver.F    L1173-L1231
L01173    !$OMP PARALLEL DO   &
L01174    !$OMP PRIVATE ( ij, i,j,k, its, ite, jts, jte, z0, z1, z2, w1, w2, message, initflag )
L01175    DO ij = 1 , num_tiles
L01176  
L01177     its = i_start(ij)
L01178     ite = i_end(ij)
L01179     jts = j_start(ij)
L01180     jte = j_end(ij)
L01181  
L01182     pbl_select: SELECT CASE(bl_pbl_physics)
L01183  
L01184        CASE (TEMFPBLSCHEME)
L01185  ! WA Test
L01186         ! WRITE( message , * ) 'Calling TEMF PBL scheme, timestep = ', itimestep
L01187         ! CALL wrf_message ( message )
L01188         ! print *,'Calling TEMF PBL scheme'
L01189          CALL wrf_debug(100,'in TEMF PBL')
L01190             IF ( PRESENT( qv_curr )  .AND. PRESENT( qc_curr )  .AND. &
L01191                  PRESENT( qi_curr )                            .AND. &
L01192                  PRESENT( rqvblten ) .AND. PRESENT( rqcblten ) .AND. &
L01193                  PRESENT( rqiblten )                           .AND. &
L01194                  PRESENT( te_temf ) .AND. PRESENT( cfm_temf ) .AND. &
L01195                  PRESENT( hol      ) ) THEN
L01196               CALL temfpbl(                                              &
L01197                 U3D=u_phytmp,V3D=v_phytmp,TH3D=th_phy,T3D=t_phy      &
L01198                ,QV3D=qv_curr,QC3D=qc_curr,QI3D=qi_curr               &
L01199                ,P3D=p_phy,P3DI=p8w,PI3D=pi_phy,RHO=rho               &
L01200                ,RUBLTEN=rublten,RVBLTEN=rvblten                      &
L01201                ,RTHBLTEN=rthblten,RQVBLTEN=rqvblten                  &
L01202                ,RQCBLTEN=rqcblten,RQIBLTEN=rqiblten                  &
L01203                ,FLAG_QI=flag_qi                                      &
L01204                ,g=g,cp=cp,rcp=rcp,r_d=r_d,r_v=r_v,cpv=cpv                    &
L01205                ,Z=z,XLV=XLV,PSFC=PSFC               &
L01206                ,P_TOP=p_top                                          &
L01207                ,ZNT=znt,HT=ht,UST=ust,ZOL=zol,HOL=hol,HPBL=pblh      &
L01208                ,PSIM=psim,PSIH=psih,XLAND=xland                      &
L01209                ,HFX=hfx,QFX=qfx,TSK=tskold,QSFC=qsfc,GZ1OZ0=gz1oz0   &
L01210                ,U10=u10,V10=v10,T2=t2                                &
L01211                ,WSPD=wspd,BR=br,DT=dtbl,DTMIN=dtmin,KPBL2D=kpbl      &
L01212                ,SVP1=svp1,SVP2=svp2,SVP3=svp3,SVPT0=svpt0            &
L01213                ,EP1=ep_1,EP2=ep_2,KARMAN=karman,EOMEG=eomeg          &
L01214                ,STBOLT=stbolt                                       &
L01215                ,te_temf=te_temf,kh_temf=kh_temf,km_temf=km_temf      &
L01216                ,shf_temf=shf_temf,qf_temf=qf_temf                    &
L01217                ,uw_temf=uw_temf,vw_temf=vw_temf                      &
L01218                ,hd_temf=hd_temf,lcl_temf=lcl_temf,hct_temf=hct_temf  &
L01219                ,wupd_temf=wupd_temf,mf_temf=mf_temf                  &
L01220                ,thup_temf=thup_temf,qtup_temf=qtup_temf,qlup_temf=qlup_temf  &
L01221                ,cf3d_temf=cf3d_temf,cfm_temf=cfm_temf                &
L01222                ,flhc=flhc,flqc=flqc,exch_temf=exch_temf              &
L01223                ,fCor=f                                            &
L01224                ,IDS=ids,IDE=ide,JDS=jds,JDE=jde,KDS=kds,KDE=kde      &
L01225                ,IMS=ims,IME=ime,JMS=jms,JME=jme,KMS=kms,KME=kme      &
L01226                ,ITS=its,ITE=ite,JTS=jts,JTE=jte,KTS=kts,KTE=kte      &
L01227                                                                      )
L01228             ELSE
L01229                 CALL wrf_error_fatal('Lack arguments to call TEMF pbl')
L01230             ENDIF
L01231  
```

> 讲解：OMP 并行 tile 循环——物理 tile 是 OpenMP 线程的并行单元（ch03 架构）。第一个 CASE 是 TEMF（总能量守恒型），PRESENT 守卫的写法是全篇模板：缺任一必需实参就把 PRESENT 逻辑值打成 message 再 fatal——新增方案时建议照抄这套自报家门式报错。

<!-- code_extract code_extract.py v1.2
source: phys/module_pbl_driver.F
ranges: L1232-L1316
file_lines: 2887
file_md5: 1c4ca2a3bd7baa4c31b48527e60a4cad
display: line-numbered (strip L-prefix and !file: line to restore)
range_md5: 7795ebc11ca9054a7bf327e39d96d124
seg_lines: 85
-->

```fortran
!file: phys/module_pbl_driver.F    L1232-L1316
L01232        CASE (YSUSCHEME)
L01233          CALL wrf_debug(100,'in YSU PBL')
L01234             IF ( PRESENT( qv_curr )  .AND. PRESENT( qc_curr )  .AND. &
L01235                  PRESENT( qi_curr )                            .AND. &
L01236                  PRESENT( rqvblten ) .AND. PRESENT( rqcblten ) .AND. &
L01237                  PRESENT( rqiblten )                           .AND. &
L01238                  PRESENT( hol      ) ) THEN
L01239  !
L01240               CALL ysu(                                              &
L01241                 U3D=u_phytmp,V3D=v_phytmp,T3D=t_phy                  &
L01242                ,QV3D=qv_curr,QC3D=qc_curr,QI3D=qi_curr               &
L01243                ,P3D=p_phy,P3DI=p8w,PI3D=pi_phy                       &
L01244                ,RUBLTEN=rublten,RVBLTEN=rvblten                      &
L01245                ,RTHBLTEN=rthblten,RQVBLTEN=rqvblten                  &
L01246                ,RQCBLTEN=rqcblten,RQIBLTEN=rqiblten                  &
L01247                ,FLAG_QI=flag_qi,FLAG_QC=flag_qc                      &
L01248                ,CP=cp,G=g,ROVCP=rcp,RD=r_D,ROVG=rovg                 &
L01249                ,DZ8W=dz8w,XLV=XLV,RV=r_v,PSFC=PSFC                   &
L01250                ,ZNT=znt,UST=ust,HPBL=pblh                            &
L01251                ,PSIM=fm,PSIH=fhh,XLAND=xland                         &
L01252                ,HFX=hfx,QFX=qfx                                      &
L01253                ,U10=u10,V10=v10                                      &
L01254                ,UOCE=uoce,VOCE=voce                                  &
L01255  ! paj
L01256                ,CTOPO=ctopo,CTOPO2=ctopo2                            &
L01257                ,YSU_TOPDOWN_PBLMIX=ysu_topdown_pblmix                &
L01258                ,WSPD=wspd,BR=br,DT=dtbl,KPBL2D=kpbl                  &
L01259                ,EP1=ep_1,EP2=ep_2,KARMAN=karman                      &
L01260                ,EXCH_H=exch_h,EXCH_M=exch_m                          &
L01261                ,RTHRATEN=RTHRATEN                                    &
L01262  ! for multilayer UCM
L01263                ,IDIFF=idiff,FLAG_BEP=flag_bep,FRC_URB2D=frc_urb2d    &
L01264                ,A_U_BEP=a_u_bep,A_V_BEP=a_v_bep,A_T_BEP=a_t_bep      &
L01265                ,A_Q_BEP=a_q_bep                                      &
L01266                ,A_E_BEP=a_e_bep,B_U_BEP=b_u_bep,B_V_BEP=b_v_bep      &
L01267                ,B_T_BEP=b_t_bep,B_Q_BEP=b_q_bep                      &
L01268                ,B_E_BEP=b_e_bep,DLG_BEP=dlg_bep                      &
L01269                ,DL_U_BEP=dl_u_bep,SF_BEP=sf_bep,VL_BEP=vl_bep        &
L01270  ! for grims shallow convection with ysupbl
L01271                ,WSTAR=wstar,DELTA=delta                              &
L01272                ,errmsg=errmsg,errflg=errflg                          &
L01273                ,IDS=ids,IDE=ide,JDS=jds,JDE=jde,KDS=kds,KDE=kde      &
L01274                ,IMS=ims,IME=ime,JMS=jms,JME=jme,KMS=kms,KME=kme      &
L01275                ,ITS=its,ITE=ite,JTS=jts,JTE=jte,KTS=kts,KTE=kte      &
L01276                                                                     )
L01277  !
L01278  ! FASDAS
L01279  !
L01280                IF( fasdas == 1 ) THEN
L01281                    DO j=j_start(ij),j_end(ij)
L01282                    DO i=i_start(ij),i_end(ij)
L01283                       scrp1 = rqvblten(i,1,j)
L01284                       scrp1 = scrp1*(2.0*DT)/qv_curr(i,1,j)
L01285                       scrp1 = scrp1*100.0
L01286                       scrp1 = amax1(0.0,scrp1)
L01287                       scrp1 = amin1(5.0,scrp1)
L01288                       QNORM(I,J)= scrp1/100.0
L01289                    ENDDO
L01290                    ENDDO
L01291                ENDIF
L01292  !
L01293  ! END FASDAS
L01294  !
L01295  
L01296             ELSE
L01297                 WRITE ( message , FMT = '(A,7(L1,1X))' )             &
L01298                   'present: '//                                      &
L01299                   'qv_curr, '//                                      &
L01300                   'qc_curr, '//                                      &
L01301                   'qi_curr, '//                                      &
L01302                   'rqvblten, '//                                     &
L01303                   'rqcblten, '//                                     &
L01304                   'rqiblten, '//                                     &
L01305                   'hol = ' ,                                         &
L01306                    PRESENT( qv_curr ) ,                              &
L01307                    PRESENT( qc_curr ) ,                              &
L01308                    PRESENT( qi_curr ) ,                              &
L01309                    PRESENT( rqvblten ) ,                             &
L01310                    PRESENT( rqcblten ) ,                             &
L01311                    PRESENT( rqiblten ) ,                             &
L01312                    PRESENT( hol      )
L01313                 CALL wrf_debug(0,message)
L01314                 CALL wrf_error_fatal('Lack arguments to call YSU pbl')
L01315             ENDIF
L01316  
```

> 讲解：YSU（1 阶非局地 K 扩散+夹卷稳定度修正）：传参注意 PSIM=fm、PSIH=fhh——面层阻抗在 pbl driver 的实参表里换了名（fm/fhh 是 surface driver 传来的相似性阻抗，不是 ψ 函数值本身）；尾接 FASDAS 同化段：用最低层水汽倾向归一出 QNORM∈[0,5%]（土壤湿度同化的归一化因子，钳位防溢出）。

<!-- code_extract code_extract.py v1.2
source: phys/module_pbl_driver.F
ranges: L1317-L1385
file_lines: 2887
file_md5: 1c4ca2a3bd7baa4c31b48527e60a4cad
display: line-numbered (strip L-prefix and !file: line to restore)
range_md5: 618c6ef3427b48b791dbb1a467518e83
seg_lines: 69
-->

```fortran
!file: phys/module_pbl_driver.F    L1317-L1385
L01317        CASE (SHINHONGSCHEME)
L01318          CALL wrf_debug(100,'in SHINHONG PBL')
L01319             IF ( PRESENT( qv_curr )  .AND. PRESENT( qc_curr )  .AND. &
L01320                  PRESENT( qi_curr )                            .AND. &
L01321                  PRESENT( rqvblten ) .AND. PRESENT( rqcblten ) .AND. &
L01322                  PRESENT( rqiblten )                           .AND. &
L01323                  PRESENT( hol      ) ) THEN
L01324  !
L01325               CALL shinhong(                                         &
L01326                 U3D=u_phytmp,V3D=v_phytmp,T3D=t_phy                  &
L01327                ,QV3D=qv_curr,QC3D=qc_curr,QI3D=qi_curr               &
L01328                ,P3D=p_phy,P3DI=p8w,PI3D=pi_phy                       &
L01329                ,RUBLTEN=rublten,RVBLTEN=rvblten                      &
L01330                ,RTHBLTEN=rthblten,RQVBLTEN=rqvblten                  &
L01331                ,RQCBLTEN=rqcblten,RQIBLTEN=rqiblten                  &
L01332                ,FLAG_QI=flag_qi,FLAG_QC=flag_qc                      &
L01333                ,CP=cp,G=g,ROVCP=rcp,RD=r_D,ROVG=rovg                 &
L01334                ,DZ8W=dz8w,XLV=XLV,RV=r_v,PSFC=PSFC                   &
L01335                ,ZNT=znt,UST=ust,HPBL=pblh                            &
L01336                ,PSIM=fm,PSIH=fhh,XLAND=xland                         &
L01337                ,HFX=hfx,QFX=qfx                                      &
L01338                ,U10=u10,V10=v10                                      &
L01339                ,UOCE=uoce,VOCE=voce                                  &
L01340  ! paj
L01341                ,shinhong_nonlocal_flux=shinhong_nonlocal_flux        &
L01342                ,shinhong_scu_mixing=shinhong_scu_mixing              &
L01343                ,shinhong_dissi_heating=shinhong_ke_dissipation       &
L01344                ,tke=tke_pbl,el=el_pbl,corf=f                         &
L01345                ,CTOPO=ctopo,CTOPO2=ctopo2,dx=dx2d                    &
L01346                ,WSPD=wspd,BR=br,DT=dtbl,KPBL2D=kpbl                  &
L01347                ,EP1=ep_1,EP2=ep_2,KARMAN=karman                      &
L01348                ,EXCH_H=exch_h,EXCH_M=exch_m                          &
L01349                ,RTHRATEN=RTHRATEN                                    &
L01350  ! for multilayer UCM
L01351                ,IDIFF=idiff,FLAG_BEP=flag_bep,FRC_URB2D=frc_urb2d    &
L01352                ,A_U_BEP=a_u_bep,A_V_BEP=a_v_bep,A_T_BEP=a_t_bep      &
L01353                ,A_Q_BEP=a_q_bep                                      &
L01354                ,A_E_BEP=a_e_bep,B_U_BEP=b_u_bep,B_V_BEP=b_v_bep      &
L01355                ,B_T_BEP=b_t_bep,B_Q_BEP=b_q_bep                      &
L01356                ,B_E_BEP=b_e_bep,DLG_BEP=dlg_bep                      &
L01357                ,DL_U_BEP=dl_u_bep,SF_BEP=sf_bep,VL_BEP=vl_bep        &
L01358  ! for grims shallow convection
L01359                ,WSTAR=wstar,DELTA=delta                              &
L01360                ,errmsg=errmsg,errflg=errflg                          &
L01361                ,IDS=ids,IDE=ide,JDS=jds,JDE=jde,KDS=kds,KDE=kde      &
L01362                ,IMS=ims,IME=ime,JMS=jms,JME=jme,KMS=kms,KME=kme      &
L01363                ,ITS=its,ITE=ite,JTS=jts,JTE=jte,KTS=kts,KTE=kte      &
L01364                                                                      )
L01365             ELSE
L01366                 WRITE ( message , FMT = '(A,7(L1,1X))' )             &
L01367                   'present: '//                                      &
L01368                   'qv_curr, '//                                      &
L01369                   'qc_curr, '//                                      &
L01370                   'qi_curr, '//                                      &
L01371                   'rqvblten, '//                                     &
L01372                   'rqcblten, '//                                     &
L01373                   'rqiblten, '//                                     &
L01374                   'hol = ' ,                                         &
L01375                    PRESENT( qv_curr ) ,                              &
L01376                    PRESENT( qc_curr ) ,                              &
L01377                    PRESENT( qi_curr ) ,                              &
L01378                    PRESENT( rqvblten ) ,                             &
L01379                    PRESENT( rqcblten ) ,                             &
L01380                    PRESENT( rqiblten ) ,                             &
L01381                    PRESENT( hol      )
L01382                 CALL wrf_debug(0,message)
L01383                 CALL wrf_error_fatal('Lack arguments to call SHINHONG pbl')
L01384             ENDIF
L01385  
```

> 讲解：ShinHong（YSU 的 TKE 扩展）：比 YSU 多传 shinhong_nonlocal_flux/scu_mixing/ke_dissipation 三个 namelist 开关与 tke_pbl/el_pbl——它复用 YSU 骨架、增加 TKE 诊断。BEP 数组同样传入（多城市实验可配 ShinHong）。

<!-- code_extract code_extract.py v1.2
source: phys/module_pbl_driver.F
ranges: L1386-L1473
file_lines: 2887
file_md5: 1c4ca2a3bd7baa4c31b48527e60a4cad
display: line-numbered (strip L-prefix and !file: line to restore)
range_md5: 103714b5053fbfc442106a7627f84cce
seg_lines: 88
-->

```fortran
!file: phys/module_pbl_driver.F    L1386-L1473
L01386        CASE (MRFSCHEME)
L01387             IF ( PRESENT( qv_curr )  .AND. PRESENT( qc_curr )  .AND. &
L01388                  PRESENT( rqvblten ) .AND. PRESENT( rqcblten ) .AND. &
L01389                  PRESENT( hol      )                           .AND. &
L01390                                                          .TRUE.  ) THEN
L01391  
L01392               CALL wrf_debug(100,'in MRF')
L01393               CALL mrf(                                              &
L01394                 U3D=u_phytmp,V3D=v_phytmp,TH3D=th_phy,T3D=t_phy      &
L01395                ,QV3D=qv_curr                                         &
L01396                ,QC3D=qc_curr                                         &
L01397                ,QI3D=qi_curr                                         &
L01398                ,P3D=p_phy,PI3D=pi_phy                                &
L01399                ,RUBLTEN=rublten,RVBLTEN=rvblten                      &
L01400                ,RTHBLTEN=rthblten,RQVBLTEN=rqvblten                  &
L01401                ,RQCBLTEN=rqcblten,RQIBLTEN=rqiblten                  &
L01402                ,CP=cp,G=g,ROVCP=rcp,R=r_d,ROVG=rovg                  &
L01403                ,DZ8W=dz8w,Z=z,XLV=xlv,RV=r_v,PSFC=psfc               &
L01404                ,P1000MB=p1000mb                                      &
L01405                ,ZNT=znt,UST=ust,ZOL=zol,HOL=hol                      &
L01406                ,PBL=pblh,PSIM=psim,PSIH=psih                         &
L01407                ,XLAND=xland,HFX=hfx,QFX=qfx,TSK=tskold               &
L01408                ,GZ1OZ0=gz1oz0,WSPD=wspd,BR=br                        &
L01409                ,DT=dtbl,DTMIN=dtmin,KPBL2D=kpbl                      &
L01410                ,SVP1=svp1,SVP2=svp2,SVP3=svp3,SVPT0=svpt0            &
L01411                ,EP1=ep_1,EP2=ep_2,KARMAN=karman,EOMEG=eomeg          &
L01412                ,STBOLT=stbolt,REGIME=regime                          &
L01413                ,FLAG_QI=flag_qi                                      &
L01414                ,IDS=ids,IDE=ide,JDS=jds,JDE=jde,KDS=kds,KDE=kde      &
L01415                ,IMS=ims,IME=ime,JMS=jms,JME=jme,KMS=kms,KME=kme      &
L01416                ,ITS=its,ITE=ite,JTS=jts,JTE=jte,KTS=kts,KTE=kte      &
L01417                                                                      ) 
L01418             ELSE
L01419                 WRITE ( message , FMT = '(A,5(L1,1X))' )             &
L01420                   'present: '//                                      &
L01421                   'qv_curr, '//                                      &
L01422                   'qc_curr, '//                                      &
L01423                   'rqvblten, '//                                     &
L01424                   'rqcblten, '//                                     &
L01425                   'hol = ' ,                                         &
L01426                    PRESENT( qv_curr ) ,                              &
L01427                    PRESENT( qc_curr ) ,                              &
L01428                    PRESENT( rqvblten ) ,                             &
L01429                    PRESENT( rqcblten ) ,                             &
L01430                    PRESENT( hol      )
L01431                 CALL wrf_debug(0,message)
L01432                 CALL wrf_error_fatal('Lack arguments to call MRF pbl')
L01433             ENDIF
L01434  
L01435        CASE (GFSSCHEME)
L01436             IF ( PRESENT( qv_curr )  .AND. PRESENT( qc_curr )  .AND. &
L01437                  PRESENT( rqvblten ) .AND. PRESENT( rqcblten ) .AND. &
L01438                                                          .TRUE.  ) THEN
L01439               CALL wrf_debug(100,'in GFS')
L01440               CALL bl_gfs(                                           &
L01441                 U3D=u_phytmp,V3D=v_phytmp                            &
L01442                ,TH3D=th_phy,T3D=t_phy                                &
L01443                ,QV3D=qv_curr,QC3D=qc_curr,QI3D=qi_curr               &
L01444                ,P3D=p_phy,PI3D=pi_phy                                &
L01445                ,RUBLTEN=rublten,RVBLTEN=rvblten,RTHBLTEN=rthblten    &
L01446                ,RQVBLTEN=rqvblten,RQCBLTEN=rqcblten                  &
L01447                ,RQIBLTEN=rqiblten                                    &
L01448                ,CP=cp,G=g,ROVCP=rcp,R=r_d,ROVG=rovg                  &
L01449                ,DZ8W=dz8w,z=z,PSFC=psfc                              &
L01450                ,UST=ust,PBL=pblh,PSIM=psim,PSIH=psih                 &
L01451                ,HFX=hfx,QFX=qfx,TSK=tskold,GZ1OZ0=gz1oz0             &
L01452                ,WSPD=wspd,BR=br                                      &
L01453                ,DT=dtbl,KPBL2D=kpbl,EP1=ep_1,KARMAN=karman           &
L01454                ,P_QI=p_qi,P_FIRST_SCALAR=param_first_scalar          &
L01455                ,IDS=ids,IDE=ide,JDS=jds,JDE=jde,KDS=kds,KDE=kde      &
L01456                ,IMS=ims,IME=ime,JMS=jms,JME=jme,KMS=kms,KME=kme      &
L01457                ,ITS=its,ITE=ite,JTS=jts,JTE=jte,KTS=kts,KTE=kte      &
L01458                                                                      )
L01459             ELSE
L01460                 WRITE ( message , FMT = '(A,4(L1,1X))' )             &
L01461                   'present: '//                                      &
L01462                   'qv_curr, '//                                      &
L01463                   'qc_curr, '//                                      &
L01464                   'rqvblten, '//                                     &
L01465                   'rqcblten = ',                                     &
L01466                    PRESENT( qv_curr ) ,                              &
L01467                    PRESENT( qc_curr ) ,                              &
L01468                    PRESENT( rqvblten ) ,                             &
L01469                    PRESENT( rqcblten )
L01470                 CALL wrf_debug(0,message)
L01471                 CALL wrf_error_fatal('Lack arguments to call GFS pbl')
L01472             ENDIF
L01473  
```

> 讲解：MRF（99，遗留）与 GFS（3）：两者是 1.5 阶闭合普及前的经典局地扩散方案，实参表明显短——无 tke/el、无 BEP、无城市。GFS 分支只要求 qv/qc 两个倾向在场（连 hol 都不要）。这两支是「最小依赖」参照组。

<!-- code_extract code_extract.py v1.2
source: phys/module_pbl_driver.F
ranges: L1474-L1548
file_lines: 2887
file_md5: 1c4ca2a3bd7baa4c31b48527e60a4cad
display: line-numbered (strip L-prefix and !file: line to restore)
range_md5: ea2271a7f5d8ba0f5536880fea6286c6
seg_lines: 75
-->

```fortran
!file: phys/module_pbl_driver.F    L1474-L1548
L01474        CASE (MYJPBLSCHEME)
L01475             IF ( PRESENT( qv_curr )  .AND. PRESENT( qc_curr )  .AND. &
L01476                  PRESENT( rqvblten ) .AND. PRESENT( rqcblten ) .AND. &
L01477                                                          .TRUE.  ) THEN
L01478  
L01479               CALL wrf_debug(100,'in MYJPBL')
L01480              IF ( .not.flag_bep .and. idiff.ne.1) THEN
L01481               CALL myjpbl(DT=dt,STEPBL=stepbl,HT=ht,DZ=dz8w          &
L01482                ,PMID=p_phy,PINT=p8w,TH=th_phy,T=t_phy,EXNER=pi_phy   &
L01483                ,QV=qv_curr,QCW=qc_curr,QCI=qi_curr,QCS=qs_curr       & !BSF
L01484                ,QCR=qr_curr,QCG=qg_curr                              & !BSF
L01485                ,U=u_phy,V=v_phy,RHO=rho                              &
L01486                ,TSK=tsk,QSFC=qsfc,CHKLOWQ=chklowq,THZ0=thz0          &
L01487                ,QZ0=qz0,UZ0=uz0,VZ0=vz0                              &
L01488                ,LOWLYR=lowlyr                                        &
L01489                ,XLAND=xland,SICE=xice,SNOW=snow                      &
L01490                ,TKE_MYJ=tke_pbl,EXCH_H=exch_h,USTAR=ust,ZNT=znt      &
L01491                ,EL_MYJ=el_pbl,PBLH=pblh,KPBL=kpbl,CT=ct              &
L01492                ,AKHS=akhs,AKMS=akms,ELFLX=lh,MIXHT=mixht             &  
L01493                ,RUBLTEN=rublten,RVBLTEN=rvblten,RTHBLTEN=rthblten    &
L01494                ,RQVBLTEN=rqvblten,RQCBLTEN=rqcblten                  &
L01495                ,RQIBLTEN=rqiblten,RQSBLTEN=rqsblten                  & !BSF
L01496                ,RQRBLTEN=rqrblten,RQGBLTEN=rqgblten                  & !BSF
L01497                ,IDS=ids,IDE=ide,JDS=jds,JDE=jde,KDS=kds,KDE=kde      &
L01498                ,IMS=ims,IME=ime,JMS=jms,JME=jme,KMS=kms,KME=kme      &
L01499                ,ITS=its,ITE=ite,JTS=jts,JTE=jte,KTS=kts,KTE=kte      &
L01500                                                                      )
L01501              ELSE !(SF_URBAN_PHYSICS.EQ.2)
L01502  ! Bep changes begin
L01503  
L01504               CALL myjurb(IDIFF=idiff,FLAG_BEP=flag_bep              &
L01505                ,DT=dtbl,STEPBL=stepbl,HT=ht,DZ=dz8w                  &
L01506                ,PMID=p_phy,PINT=p8w,TH=th_phy,T=t_phy,EXNER=pi_phy   &
L01507                ,QV=qv_curr, CWM=qc_curr                              &
L01508                ,U=u_phy,V=v_phy,RHO=rho                              &
L01509                ,TSK=tsk,QSFC=qsfc,CHKLOWQ=chklowq,THZ0=thz0          &
L01510                ,QZ0=qz0,UZ0=uz0,VZ0=vz0                              &
L01511                ,LOWLYR=lowlyr                                        &
L01512                ,XLAND=xland,SICE=xice,SNOW=snow                      &
L01513                ,TKE_MYJ=tke_pbl,EXCH_H=exch_h,EXCH_M=exch_m          &
L01514                ,USTAR=ust,ZNT=znt                                    &
L01515                ,EL_MYJ=el_pbl,PBLH=pblh,KPBL=kpbl,CT=ct              &
L01516                ,AKHS=akhs,AKMS=akms,ELFLX=lh                         &
L01517                ,RUBLTEN=rublten,RVBLTEN=rvblten,RTHBLTEN=rthblten    &
L01518                ,RQVBLTEN=rqvblten,RQCBLTEN=rqcblten                  &
L01519  ! Multi-layer UCM
L01520                ,FRC_URB2D=frc_urb2d                                  &
L01521                ,A_U_BEP=a_u_bep,A_V_BEP=a_v_bep,A_T_BEP=a_t_bep      &
L01522                ,A_Q_BEP=a_q_bep                                      &
L01523                ,A_E_BEP=a_e_bep,B_U_BEP=b_u_bep,B_V_BEP=b_v_bep      &
L01524                ,B_T_BEP=b_t_bep,B_Q_BEP=b_q_bep                      &
L01525                ,B_E_BEP=b_e_bep,DLG_BEP=dlg_bep                      &
L01526                ,DL_U_BEP=dl_u_bep,SF_BEP=sf_bep,VL_BEP=vl_bep        &
L01527  ! UCM end
L01528                ,IDS=ids,IDE=ide,JDS=jds,JDE=jde,KDS=kds,KDE=kde      &
L01529                ,IMS=ims,IME=ime,JMS=jms,JME=jme,KMS=kms,KME=kme      &
L01530                ,ITS=its,ITE=ite,JTS=jts,JTE=jte,KTS=kts,KTE=kte      &
L01531                                                                      )
L01532              ENDIF
L01533  
L01534             ELSE
L01535                 WRITE ( message , FMT = '(A,4(L1,1X))' )             &
L01536                   'present: '//                                      &
L01537                   'qv_curr, '//                                      &
L01538                   'qc_curr, '//                                      &
L01539                   'rqvblten, '//                                     &
L01540                   'rqcblten = ' ,                                    &
L01541                    PRESENT( qv_curr ) ,                              &
L01542                    PRESENT( qc_curr ) ,                              &
L01543                    PRESENT( rqvblten ) ,                             &
L01544                    PRESENT( rqcblten )
L01545                 CALL wrf_debug(0,message)
L01546                 CALL wrf_error_fatal('Lack arguments to call MYJ pbl')
L01547             ENDIF
L01548   
```

> 讲解：MYJ（2）：if(.not.flag_bep .and. idiff.ne.1) 走原版 myjpbl（注意它要 DT=dt 而非 DTBL——MYJ 自己管节拍），否则走 myjurb（多城市版本，BEP 数组全量传入）。MYJ 的 akhs/akms 在场——它是「面层-PBL 一体化」方案，交换系数由 PBL 侧算好后回传 surface driver（与 MYNN 的 CHS 分工相反）。

<!-- code_extract code_extract.py v1.2
source: phys/module_pbl_driver.F
ranges: L1549-L1618
file_lines: 2887
file_md5: 1c4ca2a3bd7baa4c31b48527e60a4cad
display: line-numbered (strip L-prefix and !file: line to restore)
range_md5: a26371d4bdce2559d2ad0efa79f3eb50
seg_lines: 70
-->

```fortran
!file: phys/module_pbl_driver.F    L1549-L1618
L01549        CASE (QNSEPBLSCHEME)
L01550             IF ( PRESENT( qv_curr )  .AND. PRESENT( qc_curr )  .AND. &
L01551                  PRESENT( rqvblten ) .AND. PRESENT( rqcblten ) .AND. &
L01552                                                          .TRUE.  ) THEN
L01553                 IF ( MFSHCONV.EQ.1 )THEN
L01554                 CALL wrf_debug(100,'in MFSHCONVPBL')
L01555                 CALL mfshconvpbl(DT=dt,STEPBL=stepbl,HT=ht,DZ=dz8w         &
L01556                      ,RHO=rho,PMID=p_phy,PINT=p8w,TH=th_phy,EXNER=pi_phy   &
L01557                      ,QV=qv_curr, QC=qc_curr                    &
L01558                      ,U=u_phy,V=v_phy                                      &
L01559                      ,HFX=hfx, QFX=qfx,TKE=tke_pbl                         &
L01560                      ,RUBLTEN=rublten,RVBLTEN=rvblten,RTHBLTEN=rthblten    &
L01561                      ,RQVBLTEN=rqvblten,RQCBLTEN=rqcblten                  &
L01562                      ,IDS=IDS,IDE=IDE,JDS=JDS,JDE=JDE,KDS=KDS,KDE=KDE      &
L01563                      ,IMS=IMS,IME=IME,JMS=JMS,JME=JME,KMS=KMS,KME=KME      &
L01564                      ,ITS=ITS,ITE=ITE,JTS=JTS,JTE=JTE,KTS=KTS,KTE=KTE      &
L01565                      ,KRR=2,MASSFLUX_EDKF=massflux_EDKF                    &
L01566                      ,ENTR_EDKF=entr_EDKF, DETR_EDKF=detr_EDKF             & 
L01567                      ,THL_UP=thl_up, THV_UP=thv_up, RT_UP=rt_up            &
L01568                      ,RV_UP=rv_up,RC_UP=rc_up, U_UP=u_up, V_UP=v_up        &
L01569                      ,FRAC_UP=frac_up, RC_MF=rc_mf,WTHV=u_phytmp           &
L01570                      ,PLM_BL89=v_phytmp   ) 
L01571                 ENDIF   
L01572  
L01573               CALL wrf_debug(100,'in QNSEPBL')
L01574               CALL qnsepbl(                                           &
L01575                 DT=dt,STEPBL=stepbl,HT=ht,DZ=dz8w                    &
L01576                ,PMID=p_phy,PINT=p8w,TH=th_phy,T=t_phy,EXNER=pi_phy   &
L01577                ,QV=qv_curr, CWM=qc_curr                              &
L01578                ,U=u_phy,V=v_phy,RHO=rho                              &
L01579                ,TSK=tsk,QSFC=qsfc,CHKLOWQ=chklowq,THZ0=thz0          &
L01580                ,QZ0=qz0,UZ0=uz0,VZ0=vz0,CORF=f                       &
L01581                ,LOWLYR=lowlyr                                        &
L01582                ,XLAND=xland,SICE=xice,SNOW=snow                      &
L01583                ,TKE=tke_pbl,EXCH_H=exch_h,EXCH_M=exch_m,USTAR=ust,ZNT=znt      &
L01584                ,EL_MYJ=el_pbl,PBLH=pblh,KPBL=kpbl,CT=ct              &
L01585                ,AKHS=akhs,AKMS=akms,ELFLX=lh                         &
L01586                ,HFX=hfx,WTHV_MF=u_phytmp,LM_BL89=v_phytmp            & 
L01587                ,RUBLTEN=rublten,RVBLTEN=rvblten,RTHBLTEN=rthblten    &
L01588                ,RQVBLTEN=rqvblten,RQCBLTEN=rqcblten                  &
L01589                ,IDS=ids,IDE=ide,JDS=jds,JDE=jde,KDS=kds,KDE=kde      &
L01590                ,IMS=ims,IME=ime,JMS=jms,JME=jme,KMS=kms,KME=kme      &
L01591                ,ITS=its,ITE=ite,JTS=jts,JTE=jte,KTS=kts,KTE=kte      &
L01592                                                                      )
L01593  ! note the tendencies have been added inside qnse 
L01594  !            IF ( PRESENT (MFSHCONV) )THEN
L01595  !              IF (MFSHCONV.EQ.1)THEN
L01596  !              rublten(:,:,:)=rublten(:,:,:)+rumften(:,:,:)
L01597  !              rvblten(:,:,:)=rvblten(:,:,:)+rvmften(:,:,:)
L01598  !              rthblten(:,:,:)=rthblten(:,:,:)+rthmften(:,:,:)
L01599  !              rqvblten(:,:,:)=rqvblten(:,:,:)+rqvmften(:,:,:)
L01600  !              rqcblten(:,:,:)=rqcblten(:,:,:)+rqcmften(:,:,:)
L01601  !              ENDIF   
L01602  !            ENDIF   
L01603  
L01604              ELSE
L01605                 WRITE ( message , FMT = '(A,4(L1,1X))' )             &
L01606                   'present: '//                                      &
L01607                   'qv_curr, '//                                      &
L01608                   'qc_curr, '//                                      &
L01609                   'rqvblten, '//                                     &
L01610                   'rqcblten = ' ,                                    &
L01611                    PRESENT( qv_curr ) ,                              &
L01612                    PRESENT( qc_curr ) ,                              &
L01613                    PRESENT( rqvblten ) ,                             &
L01614                    PRESENT( rqcblten )
L01615                 CALL wrf_debug(0,message)
L01616                 CALL wrf_error_fatal('Lack arguments to call QNSE pbl')
L01617             ENDIF
L01618  
```

> 讲解：QNSE（4）：先有 MFSHCONV=1 时的浅对流质量流支路 mfshconvpbl（EDKF 夹卷/卷出谱），再进 qnsepbl 主体；注释掉的 tendency 累加段说明「方案内部已加」。QNSE 是驱动层里唯一「一个 CASE 可发两次调用」的方案。

<!-- code_extract code_extract.py v1.2
source: phys/module_pbl_driver.F
ranges: L1619-L1660
file_lines: 2887
file_md5: 1c4ca2a3bd7baa4c31b48527e60a4cad
display: line-numbered (strip L-prefix and !file: line to restore)
range_md5: 6de8a8b5a4d9383c5ef22f27a0dd5897
seg_lines: 42
-->

```fortran
!file: phys/module_pbl_driver.F    L1619-L1660
L01619        CASE (ACMPBLSCHEME)
L01620             
L01621             !!  These are values that are not supplied to pbl driver, but are required by ACM
L01622             IF ( PRESENT( qv_curr )  .AND. PRESENT( qc_curr )  .AND. &
L01623                  PRESENT( rqvblten ) .AND. PRESENT( rqcblten ) .AND. &
L01624                                                          .TRUE.  ) THEN
L01625               CALL wrf_debug(100,'in ACM PBL')
L01626  
L01627               CALL ACMPBL(                                                        &
L01628                 XTIME=itimestep, DTPBL=dtbl,U3D=u_phytmp, V3D=v_phytmp          &
L01629                ,PP3D=p_phy, DZ8W=dz8w, TH3D=th_phy, T3D=t_phy                   &
L01630                ,QV3D=qv_curr, QC3D=qc_curr, QI3D=qi_curr, RR3D=rho                &
L01631  #if (WRF_CHEM == 1)
L01632                ,CHEM3D=CHEM,   VD3D=VD,  NCHEM=nchem, KDVEL=kdvel              &
L01633                ,NDVEL=ndvel, NUM_VERT_MIX=num_vert_mix                         &
L01634  #endif
L01635                ,UST=UST, HFX=HFX, QFX=QFX, TSK=tsk                               &
L01636                ,PSFC=PSFC, EP1=EP_1, G=g, ROVCP=rcp,RD=r_D,CPD=cp                 &
L01637                ,PBLH=pblh, KPBL2D=kpbl, EXCH_H=exch_h, EXCH_M=exch_m              &
L01638                ,REGIME=regime                                                     &
L01639                ,GZ1OZ0=gz1oz0,WSPD=wspd,PSIM=psim, MUT=mut, RMOL=rmol             &
L01640                ,RUBLTEN=rublten,RVBLTEN=rvblten,RTHBLTEN=rthblten                 &
L01641                ,RQVBLTEN=rqvblten,RQCBLTEN=rqcblten,RQIBLTEN=rqiblten             &
L01642                ,IDS=ids,IDE=ide,JDS=jds,JDE=jde,KDS=kds,KDE=kde                   &
L01643                ,IMS=ims,IME=ime,JMS=jms,JME=jme,KMS=kms,KME=kme                   &
L01644                ,ITS=its,ITE=ite,JTS=jts,JTE=jte,KTS=kts,KTE=kte                   &   
L01645                                                                        )
L01646             ELSE
L01647                 WRITE ( message , FMT = '(A,4(L1,1X))' )             &
L01648                   'present: '//                                      &
L01649                   'qv_curr, '//                                      &
L01650                   'qc_curr, '//                                      &
L01651                   'rqvblten, '//                                     &
L01652                   'rqcblten = ' ,                                    &
L01653                    PRESENT( qv_curr ) ,                              &
L01654                    PRESENT( qc_curr ) ,                              &
L01655                    PRESENT( rqvblten ) ,                             &
L01656                    PRESENT( rqcblten )
L01657                 CALL wrf_debug(0,message)
L01658                 CALL wrf_error_fatal('Lack arguments to call ACM2 pbl')
L01659             ENDIF
L01660  
```

> 讲解：ACM2（7）：非局地向上输送+局地扩散混合方案，E-ε 闭合的简化替代；WRF-Chem 下额外传化学物种垂直扩散数组（#if WRF_CHEM==1 包裹——驱动层的条件编译样板）。

**MYNN 分支**（本文库 09 篇方案的入口）：

<!-- code_extract code_extract.py v1.2
source: phys/module_pbl_driver.F
ranges: L1661-L1868
file_lines: 2887
file_md5: 1c4ca2a3bd7baa4c31b48527e60a4cad
display: line-numbered (strip L-prefix and !file: line to restore)
range_md5: 59b0dc60839a446dcb19a8c66402a329
seg_lines: 208
-->

```fortran
!file: phys/module_pbl_driver.F    L1661-L1868
L01661  #if (EM_CORE==1)
L01662  
L01663          CASE (MYNNPBLSCHEME)
L01664  
L01665             IF ( PRESENT( qv_curr )  .AND. PRESENT( qc_curr )  .AND. &
L01666                  PRESENT( rqvblten ) .AND. PRESENT( rqcblten ) .AND. &
L01667                  PRESENT( qi_curr ) .AND. PRESENT( rqiblten ) .AND.  &
L01668                  PRESENT( rqniblten ) .AND. PRESENT( qni_curr ) .AND.&
L01669                  PRESENT(qke) .AND. PRESENT(tsq) .AND.               &
L01670                  PRESENT(qsq) .AND. PRESENT(cov) .AND.               &
L01671                  PRESENT(ch) .AND.                                   &
L01672                  PRESENT(tke_budget) .AND. PRESENT(qke_adv) .AND.    &
L01673                  PRESENT(bl_mynn_tkeadvect)  ) THEN
L01674  
L01675                CALL wrf_debug(100,'in MYNNPBL')
L01676  
L01677                IF (itimestep==1) THEN
L01678                   initflag=1
L01679                ELSE
L01680                   initflag=0
L01681                ENDIF
L01682                
L01683                if (pert_mynn .and. multi_perturb == 1) then
L01684                  allocate (qke_tmp(its:ite, kts:kte, jts:jte))
L01685  
L01686                  call Add_multi_perturb_pbl_perturbations (               &
L01687                    perts_qvapor, perts_qcloud, perts_th, perts_tke,       &
L01688                    pert_mynn_qv, pert_mynn_qc, pert_mynn_t, pert_mynn_qke,&
L01689                    th_phy, qke, qke_adv, qv_curr, qc_curr,                &
L01690                    bl_mynn_tkeadvect, qke_tmp, its, ite, jts, jte,        &
L01691                    ims, ime, jms, jme, kms, kme, kts, kte)
L01692                end if
L01693  
L01694                CALL mynnedmf_driver(                                      &
L01695                     &initflag=initflag,restart=restart,cycling=cycling,   &
L01696                     &delt=dtbl,dz=dz8w,dxc=dx,znt=znt,                    &
L01697                     &u=u_phy,v=v_phy,w=w,th=th_phy,qv=qv_curr,            &
L01698                     &qc=qc_curr,qi=qi_curr,qs=qs_curr,                    &
L01699                     &qnc=qnc_curr,qni=qni_curr,                           &
L01700                     &QNWFA=qnwfa_curr,QNIFA=qnifa_curr,QNBCA=qnbca_curr,  &
L01701  !                   &ozone=ozone,                                         &
L01702                     &p=p_phy,exner=pi_phy,rho=rho,T3D=t_phy,              &
L01703                     &xland=xland,ts=tsk,qsfc=qsfc,ps=psfc,                &
L01704                     &ust=ust,ch=ch,hfx=hfx,qfx=qfx,wspd=wspd,             &
L01705                     &uoce=uoce,voce=voce,                                 & !Ocean currents
L01706                     &Qke=qke,qke_adv=qke_adv,Sh3d=Sh3d,Sm3d=Sm3d,         &
L01707  #if (WRF_CHEM == 1)
L01708                     &mix_chem=mynn_chem_vertmx,                           &
L01709                     &chem3d=chem,vd3d=vd,nchem=nchem,kdvel=kdvel,         &
L01710                     &ndvel=ndvel,num_vert_mix=num_vert_mix,               &
L01711  !                   &FRP_MEAN=FRP_MEAN,EMIS_ANT_NO=EMIS_ANT_NO,           & !to be included soon
L01712  !                   &fire_turb=enh_vermix,                                & !to be included soon
L01713  #endif
L01714                     &Tsq=tsq,Qsq=qsq,Cov=cov,                             &
L01715                     &RUBLTEN=rublten,RVBLTEN=rvblten,RTHBLTEN=rthblten,   &
L01716                     &RQVBLTEN=rqvblten,RQCBLTEN=rqcblten,RQIBLTEN=rqiblten,&
L01717                     &RQNCBLTEN=rqncblten,RQNIBLTEN=rqniblten,             &
L01718                     &RQSBLTEN=rqsblten,                                   &
L01719                     &RQNWFABLTEN=rqnwfablten,RQNIFABLTEN=rqnifablten,     &
L01720                     &RQNBCABLTEN=rqnbcablten,                             &
L01721  !                   &Ro3BLTEN=ro3blten,                                   &
L01722                     &EXCH_H=exch_h,EXCH_M=exch_m,                         &
L01723                     &pblh=pblh,KPBL=KPBL,                                 &
L01724                     &el_pbl=el_pbl,                                       &
L01725                     &dqke=dqke,                                           &
L01726                     &qWT=qWT,qSHEAR=qSHEAR,qBUOY=qBUOY,qDISS=qDISS,       &
L01727                     &qc_bl=qc_bl,qi_bl=qi_bl,cldfra_bl=cldfra_bl,         &
L01728                     &edmf_a=edmf_a,edmf_w=edmf_w,edmf_qt=edmf_qt,         &
L01729                     &edmf_thl=edmf_thl,edmf_ent=edmf_ent,edmf_qc=edmf_qc, &
L01730                     &sub_thl3D=sub_thl3D,sub_sqv3D=sub_sqv3D,             &
L01731                     &det_thl3D=det_thl3D,det_sqv3D=det_sqv3D,             &
L01732                     &maxwidth=maxwidth,maxMF=maxMF,                       &
L01733                     &ztop_plume=ztop_plume,maxmf_dd=maxmf_dd,             &
L01734                     &maxtkeprod=maxtkeprod,cldtop_cooling=cldtop_cooling, &
L01735                     &ent_eff=ent_eff,maxwidth_dd=maxwidth_dd,             &
L01736                     &excess_h=excess_h,excess_q=excess_q,                 &
L01737                     &RTHRATEN=RTHRATEN,                                   &
L01738                     &bl_mynn_tkeadvect=bl_mynn_tkeadvect,                 &
L01739                     &tke_budget=tke_budget,                               &
L01740                     &bl_mynn_cloudpdf=bl_mynn_cloudpdf,                   &
L01741                     &bl_mynn_mixlength=bl_mynn_mixlength,                 &
L01742                     &bl_mynn_edmf=bl_mynn_edmf,                           &
L01743                     &bl_mynn_edmf_dd=bl_mynn_edmf_dd,                     &
L01744                     &bl_mynn_edmf_mom=bl_mynn_edmf_mom,                   &
L01745                     &bl_mynn_edmf_tke=bl_mynn_edmf_tke,                   &
L01746                     &bl_mynn_mixscalars=bl_mynn_mixscalars,               &
L01747                     &bl_mynn_mixaerosols=bl_mynn_mixaerosols,             &
L01748                     &bl_mynn_mixnumcon=bl_mynn_mixnumcon,                 &
L01749                     &bl_mynn_output=bl_mynn_output,                       &
L01750                     &bl_mynn_cloudmix=bl_mynn_cloudmix,                   &
L01751                     &bl_mynn_mixqt=bl_mynn_mixqt,                         &
L01752                     &bl_mynn_closure=bl_mynn_closure,                     &
L01753                     &bl_mynn_ess=bl_mynn_ess,                             &
L01754                     &spp_pbl=spp_pbl,pattern_spp_pbl=pattern_spp_pbl,     &
L01755                     &FLAG_QC=flag_qc,FLAG_QI=flag_qi,FLAG_QS=flag_qs,     &
L01756                     &FLAG_QNC=flag_qnc,FLAG_QNI=flag_qni,                 &
L01757                     &FLAG_QNWFA=flag_qnwfa,FLAG_QNIFA=flag_qnifa,         &
L01758                     &FLAG_QNBCA=flag_qnbca,                               &
L01759                     &IDS=ids,IDE=ide,JDS=jds,JDE=jde,KDS=kds,KDE=kde,     &
L01760                     &IMS=ims,IME=ime,JMS=jms,JME=jme,KMS=kms,KME=kme,     &
L01761                     &ITS=its,ITE=ite,JTS=jts,JTE=jte,KTS=kts,KTE=kte      )
L01762  
L01763                if (pert_mynn .and. multi_perturb == 1) then
L01764                  call Remove_multi_perturb_pbl_perturbations (            &
L01765                    perts_qvapor, perts_qcloud, perts_th, perts_tke,       &
L01766                    pert_mynn_qv, pert_mynn_qc, pert_mynn_t, pert_mynn_qke,&
L01767                    th_phy, qke, qke_adv, qv_curr, qc_curr,                &
L01768                    bl_mynn_tkeadvect, qke_tmp, its, ite, jts, jte,        &
L01769                    ims, ime, jms, jme, kms, kme, kts, kte)
L01770  
L01771                    deallocate (qke_tmp)
L01772                end if
L01773             ELSE
L01774                 WRITE ( message , FMT = '(A,16(L1,1X))' )            &
L01775                   'present: '//                                      &
L01776                   'qv_curr, '//                                      &
L01777                   'qc_curr, '//                                      &
L01778                   'qi_curr, '//                                      &
L01779                   'qni_curr, '//                                     &
L01780                   'rqvblten, '//                                     &
L01781                   'rqcblten, '//                                     &
L01782                   'rqiblten, '//                                     &
L01783                   'rqniblten, '//                                    &
L01784                   'qke, '//                                          &
L01785                   'tsq, '//                                          &
L01786                   'qsq, '//                                          &
L01787                   'cov, '//                                          &
L01788                   'ch, '//                                           &
L01789                   'tke_budget, '//                                   &
L01790                   'qke_adv, '//                                      &
L01791                   'bl_mynn_tkeadvect ' ,                             &
L01792                    PRESENT( qv_curr ) ,                              &
L01793                    PRESENT( qc_curr ) ,                              &
L01794                    PRESENT( qi_curr ) ,                              &
L01795                    PRESENT( qni_curr ) ,                             &
L01796                    PRESENT( rqvblten ) ,                             &
L01797                    PRESENT( rqcblten ) ,                             &
L01798                    PRESENT( rqiblten ) ,                             &
L01799                    PRESENT( rqniblten ) ,                            &
L01800                    PRESENT( qke      ) ,                             &
L01801                    PRESENT( tsq      ) ,                             &
L01802                    PRESENT( qsq      ) ,                             &
L01803                    PRESENT( cov      ) ,                             &
L01804                    PRESENT( ch       ) ,                             &
L01805                    PRESENT( tke_budget) ,                            &
L01806                    PRESENT( qke_adv  ) ,                             &
L01807                    PRESENT( bl_mynn_tkeadvect)
L01808                 CALL wrf_debug(0,message)
L01809                CALL wrf_error_fatal('Lack arguments to call MYNN pbl')
L01810             ENDIF
L01811  
L01812             !fill scalar_tend array. The RQN*BLTEN arrays are no longer
L01813             !passed to module_physics_addtendc.F (for MYNN)
L01814             IF (bl_mynn_mixnumcon .eq. 1) THEN
L01815                IF (PRESENT( qni_curr ) .AND. Flag_qni) THEN
L01816                  !print*,"Updating qni after mynn-edmf",P_QNI
L01817                  DO j=j_start(ij),j_end(ij)
L01818                  DO k=kts,kte 
L01819                  DO i=i_start(ij),i_end(ij)
L01820                     scalar_tend(i,k,j,P_QNI)=RQNIBLTEN(i,k,j)
L01821                  enddo
L01822                  enddo
L01823                  enddo
L01824                ENDIF
L01825                IF (PRESENT( qnc_curr ) .AND. Flag_qnc) THEN
L01826                  !print*,"Updating qnc after mynn-edmf",P_QNC
L01827                  DO j=j_start(ij),j_end(ij)
L01828                  DO k=kts,kte
L01829                  DO i=i_start(ij),i_end(ij)
L01830                     scalar_tend(i,k,j,P_QNC)=RQNCBLTEN(i,k,j)
L01831                  enddo
L01832                  enddo
L01833                  enddo
L01834                ENDIF
L01835             endif
L01836             if (bl_mynn_mixaerosols .eq. 1) then
L01837                IF (PRESENT( qnwfa_curr ) .AND. Flag_qnwfa) THEN
L01838                  !print*,"Updating qnwfa after mynn-edmf",P_QNWFA
L01839                  DO j=j_start(ij),j_end(ij)
L01840                  DO k=kts,kte
L01841                  DO i=i_start(ij),i_end(ij)
L01842                     scalar_tend(i,k,j,P_QNWFA)=RQNWFABLTEN(i,k,j)
L01843                  enddo
L01844                  enddo
L01845                  enddo
L01846                ENDIF
L01847                IF (PRESENT( qnifa_curr ) .AND. Flag_qnifa) THEN
L01848                  !print*,"Updating qnifa after mynn-edmf",P_QNIFA
L01849                  DO j=j_start(ij),j_end(ij)
L01850                  DO k=kts,kte
L01851                  DO i=i_start(ij),i_end(ij)
L01852                     scalar_tend(i,k,j,P_QNIFA)=RQNIFABLTEN(i,k,j)
L01853                  enddo
L01854                  enddo
L01855                  enddo
L01856                ENDIF
L01857                IF (PRESENT( qnbca_curr ) .AND. Flag_qnbca) THEN
L01858                  !print*,"Updating qnbca after mynn-edmf",P_QNBCA
L01859                  DO j=j_start(ij),j_end(ij)
L01860                  DO k=kts,kte
L01861                  DO i=i_start(ij),i_end(ij)
L01862                     scalar_tend(i,k,j,P_QNBCA)=RQNBCABLTEN(i,k,j)
L01863                  enddo
L01864                  enddo
L01865                  enddo
L01866                ENDIF
L01867             ENDIF
L01868  
```

> 讲解：①PRESENT 守卫升级为 16 项——qke/tsq/qsq/cov（TKE 及其通量-方差二阶矩）、ch（面层热交换系数，来自 code_10 的 surface driver）、tke_budget/qke_adv/bl_mynn_tkeadvect 缺一不可：这正是「切到 MYNN 必须 real 重跑」的根源；②initflag=首步标记传给 mynnedmf_driver；③**SPP 包裹**：pert_mynn 且 multi_perturb=1 时，先 Add_multi_perturb 把乘性扰动打在 qv/qc/th/qke 上再调方案、方案返回后 Remove 还原——扰动只在 PBL 方案作用域内生效（WRF-Solar EPS 集合技术）；④主体调用把 bl_mynn_* 十余个 namelist 开关原样透传（清单见 code_09a 篇首）；⑤**收尾回填**：bl_mynn_mixnumcon/mixaerosols=1 时把 RQNIBLTEN/RQNCBLTEN/RQNWFA… 从专设倾向数组搬进 scalar_tend 数组的对应物种位——注释明言「RQN*BLTEN 不再传给 module_physics_addtendc.F」：数浓度与气溶胶的 PBL 倾向绕过了通用倾向累加器，直接在 driver 内完成（改 MYNN 混合行为时别在 addtendc 里白找）。

<!-- code_extract code_extract.py v1.2
source: phys/module_pbl_driver.F
ranges: L1869-L1916
file_lines: 2887
file_md5: 1c4ca2a3bd7baa4c31b48527e60a4cad
display: line-numbered (strip L-prefix and !file: line to restore)
range_md5: ac6dadde6ccc5201bec4d28136a5885e
seg_lines: 48
-->

```fortran
!file: phys/module_pbl_driver.F    L1869-L1916
L01869          CASE (EEPSSCHEME)
L01870  
L01871                IF ( PRESENT( qv_curr )  .AND. PRESENT( qc_curr )  .AND. &
L01872                     PRESENT( qi_curr )                            .AND. &
L01873                     PRESENT( rqvblten ) .AND. PRESENT( rqcblten ) .AND. &
L01874                     PRESENT( rqiblten )                           .AND. &
L01875                     PRESENT( pek )      .AND. PRESENT( pep)       .AND. &
L01876                     PRESENT( pek_adv )  .AND. PRESENT( pep_adv ) ) THEN
L01877  
L01878                  CALL wrf_debug(100,'in EEPSPBL')
L01879  
L01880                  CALL  eeps(&
L01881                     U3D=u_phytmp,V3D=v_phytmp,T3D=t_phy                  &
L01882                    ,QV3D=qv_curr,QC3D=qc_curr,QI3D=qi_curr               &
L01883                    ,QR3D=qr_curr,QS3D=qs_curr,QG3D=qg_curr               &
L01884                    ,P3D=p_phy,PI3D=pi_phy,PEK=pek,PEP=pep                &
L01885                    ,RHO3D=rho,RTHRATEN=rthraten                          &
L01886                    ,RUBLTEN=rublten,RVBLTEN=rvblten                      &
L01887                    ,RTHBLTEN=rthblten,RQVBLTEN=rqvblten                  &
L01888                    ,RQCBLTEN=rqcblten,RQIBLTEN=rqiblten,KPBL=kpbl        &
L01889                    ,DZ8W=dz8w,PSFC=psfc,TSK=tsk,QSFC=qsfc,WSPD=wspd      &
L01890                    ,UST=ust,XLAND=xland,HFX=hfx,QFX=qfx,RMOL=rmol        &
L01891                    ,DT=dtbl,DX=dx,EXCH_H=exch_h,EXCH_M=exch_m,PBLH=pblh  &
L01892                    ,ITIMESTEP=itimestep,PEK_ADV=pek_adv,PEP_ADV=pep_adv   &
L01893                     ,IDS=ids,IDE=ide,JDS=jds,JDE=jde,KDS=kds,KDE=kde      &
L01894                     ,IMS=ims,IME=ime,JMS=jms,JME=jme,KMS=kms,KME=kme      &
L01895                     ,ITS=its,ITE=ite,JTS=jts,JTE=jte,KTS=kts,KTE=kte      &
L01896                     )
L01897                ELSE
L01898                 WRITE ( message , FMT = '(A,6(L1,1X))' )             &
L01899                   'present: '//                                      &
L01900                   'qv_curr, '//                                      &
L01901                   'qc_curr, '//                                      &
L01902                   'qi_curr, '//                                      &
L01903                   'rqvblten, '//                                     &
L01904                   'rqcblten, '//                                     &
L01905                   'rqiblten, ' ,                                     &
L01906                    PRESENT( qv_curr ) ,                              &
L01907                    PRESENT( qc_curr ) ,                              &
L01908                    PRESENT( qi_curr ) ,                              &
L01909                    PRESENT( rqvblten ) ,                             &
L01910                    PRESENT( rqcblten ) ,                             &
L01911                    PRESENT( rqiblten )
L01912                 CALL wrf_debug(0,message)
L01913                 CALL wrf_error_fatal('Lack arguments to call EEPS pbl')
L01914             ENDIF
L01915  
L01916  
```

> 讲解：EEPS（16）：集合型 PBL——pek/pep（两组扰动集合的能量谱）作 state 携带，pek_adv/pep_adv 为 advect 标志；与 MYNN 的 SPP 同属「随机物理」家族但实现为显式集合。

<!-- code_extract code_extract.py v1.2
source: phys/module_pbl_driver.F
ranges: L1917-L1947
file_lines: 2887
file_md5: 1c4ca2a3bd7baa4c31b48527e60a4cad
display: line-numbered (strip L-prefix and !file: line to restore)
range_md5: 3c8c299fe0093d049b629eb562aafc8b
seg_lines: 31
-->

```fortran
!file: phys/module_pbl_driver.F    L1917-L1947
L01917                 CASE (KEPSSCHEME)
L01918  
L01919               CALL wrf_debug(100,'in keps')
L01920               CALL KEPS(TSK=tsk,MOL=mol,XTIME=itimestep,FRC_URB2D=frc_urb2d            &
L01921                , FLAG_BEP=flag_bep  &
L01922                ,DZ8W=dz8w,DT=dt,U_PHY=u_phytmp                                  &
L01923                ,V_PHY=v_phytmp,TH_PHY=th_phy                                    &
L01924                ,PI_PHY=pi_phy,RTHRATEN=RTHRATEN,P8W=p8w                         &
L01925                ,RHO=rho,QV_CURR=qv_curr,QC_CURR=qc_curr,HFX=hfx                 &
L01926                ,QFX=qfx,USTAR=ust,CP=cp,G=g                                     &
L01927                ,RUBLTEN=rublten,RVBLTEN=rvblten,RTHBLTEN=rthblten               &
L01928                ,RQVBLTEN=rqvblten,RQCBLTEN=rqcblten                             &
L01929                ,TKE_PBL=tke_pbl,DISS_PBL=diss_pbl,TPE_PBL=tpe_pbl               &
L01930                ,TKE_ADV=tke_adv,DISS_ADV=diss_adv,TPE_ADV=tpe_adv               &
L01931                ,PR_PBL=pr_pbl                                                   &
L01932                ,WU=wu_tur,WV=wv_tur,WT=wt_tur,WQ=wq_tur                         &
L01933                ,EXCH_H=exch_h,EXCH_M=exch_m,PBLH=pblh                           &
L01934                ,A_U_BEP=a_u_bep,A_V_BEP=a_v_bep,A_T_BEP=a_t_bep                 &
L01935                ,A_Q_BEP=a_q_bep                                                 &
L01936                ,B_U_BEP=b_u_bep,B_V_BEP=b_v_bep                                 &
L01937                ,B_T_BEP=b_t_bep                                                 &
L01938                ,B_Q_BEP=b_q_bep                                                 &
L01939                ,B_E_BEP=b_e_bep                                                 &
L01940                ,SF_BEP=sf_bep,VL_BEP=vl_bep                                     &
L01941                ,BR=br,ZNT=znt                                                   &
L01942                ,PSIM=fm,PSIH=fhh                                             &
L01943                ,IDS=ids,IDE=ide,JDS=jds,JDE=jde,KDS=kds,KDE=kde                 &
L01944                ,IMS=ims,IME=ime,JMS=jms,JME=jme,KMS=kms,KME=kme                 &
L01945                ,ITS=its,ITE=ite,JTS=jts,JTE=jte,KTS=kts,KTE=kte  )
L01946  
L01947  
```

> 讲解：KEPS（17）：k-ε 双方程闭合，专为 BEP/BEM 城市冠层设计（a_e_bep/b_e_bep 是建筑内 TKE 源项）——sf_urban_physics=3（论文 2）配 bl_pbl_physics=17 是官方推荐组合；BouLac=8 与 MYJ=2 是 BEP 兼容的另外两支。

<!-- code_extract code_extract.py v1.2
source: phys/module_pbl_driver.F
ranges: L1949-L1971
file_lines: 2887
file_md5: 1c4ca2a3bd7baa4c31b48527e60a4cad
display: line-numbered (strip L-prefix and !file: line to restore)
range_md5: 1a554fb3dfbb2f2e0c312e61494e0e07
seg_lines: 23
-->

```fortran
!file: phys/module_pbl_driver.F    L1949-L1971
L01949          CASE (BOULACSCHEME)
L01950  
L01951               CALL wrf_debug(100,'in boulac')
L01952  
L01953               CALL BOULAC(FRC_URB2D=frc_urb2d,IDIFF=idiff,FLAG_BEP=flag_bep     &
L01954                ,DZ8W=dz8w,DT=dt,U_PHY=u_phytmp                                  &
L01955                ,V_PHY=v_phytmp,TH_PHY=th_phy                                    &
L01956                ,RHO=rho,QV_CURR=qv_curr,QC_CURR=qc_curr,HFX=hfx                 &
L01957                ,QFX=qfx,USTAR=ust,CP=cp,G=g                                     &
L01958                ,RUBLTEN=rublten,RVBLTEN=rvblten,RTHBLTEN=rthblten               &
L01959                ,RQVBLTEN=rqvblten,RQCBLTEN=rqcblten                             &
L01960                ,TKE=tke_pbl,DLK=el_pbl,WU=wu_tur,WV=wv_tur,WT=wt_tur,WQ=wq_tur  &
L01961                ,EXCH_H=exch_h,EXCH_M=exch_m,PBLH=pblh                           &
L01962                ,A_U_BEP=a_u_bep,A_V_BEP=a_v_bep,A_T_BEP=a_t_bep                 &
L01963                ,A_Q_BEP=a_q_bep                                                 &
L01964                ,A_E_BEP=a_e_bep,B_U_BEP=b_u_bep,B_V_BEP=b_v_bep                 &
L01965                ,B_T_BEP=b_t_bep,B_E_BEP=b_e_bep,DLG_BEP=dlg_bep                 &
L01966                ,B_Q_BEP=b_q_bep                                                 &
L01967                ,DL_U_BEP=dl_u_bep,SF_BEP=sf_bep,VL_BEP=vl_bep                   &
L01968                ,IDS=ids,IDE=ide,JDS=jds,JDE=jde,KDS=kds,KDE=kde                 &
L01969                ,IMS=ims,IME=ime,JMS=jms,JME=jme,KMS=kms,KME=kme                 &
L01970                ,ITS=its,ITE=ite,JTS=jts,JTE=jte,KTS=kts,KTE=kte  )
L01971  
```

> 讲解：BouLac（8）：TKE-l 阶 1.5 闭合 + Bougeault–Lacarrère 混合长（方案实体精读见 code_09a 篇的 boulac 双长度对照节）；wu/wv/wt/wq_tur 湍流通量诊断全套传出。论文 2 的边界层首选。

<!-- code_extract code_extract.py v1.2
source: phys/module_pbl_driver.F
ranges: L1972-L2028
file_lines: 2887
file_md5: 1c4ca2a3bd7baa4c31b48527e60a4cad
display: line-numbered (strip L-prefix and !file: line to restore)
range_md5: 00fc2758c82859a370c840abf505f14a
seg_lines: 57
-->

```fortran
!file: phys/module_pbl_driver.F    L1972-L2028
L01972             CASE (CAMUWPBLSCHEME)
L01973                
L01974                CALL wrf_debug(100,'in camuwpbl')
L01975                IF ( PRESENT( qv_curr  )  .AND. PRESENT( qc_curr   )  .AND. &
L01976                     PRESENT( qi_curr  )  .AND. PRESENT( qnc_curr  )  .AND. &
L01977                     PRESENT( qni_curr )  .AND.                             &
L01978                     PRESENT( rqvblten )  .AND. PRESENT( rqcblten  )  .AND. &
L01979                     PRESENT( rqiblten )  .AND. PRESENT( rqniblten )        &                   
L01980                   )THEN
L01981                   CALL CAMUWPBL(DT=dt,U_PHY=u_phy,V_PHY=v_phy,TH_PHY=th_phy,RHO=rho   &
L01982                        ,QV_CURR=qv_curr,HFX=hfx,QFX=qfx,USTAR=ust,P8W=p8w,P_PHY=p_phy &
L01983                        ,Z=z,T_PHY=t_phy,QC_CURR=qc_curr,QI_CURR=qi_curr,Z_AT_W=z_at_w &
L01984                        ,CLDFRA_OLD_mp=cldfra_old_mp,CLDFRA=cldfra,HT=ht               &
L01985                        ,RTHRATENLW=rthratenlw,EXNER=pi_phy                            &
L01986                        ,is_CAMMGMP_used=is_CAMMGMP_used                               &
L01987                        ,ITIMESTEP=itimestep,QNC_CURR=qnc_curr,QNI_CURR=qni_curr       &
L01988                        ,WSEDL3D=wsedl3d                                               &
L01989  
L01990                        ,IDS=ids,IDE=ide, JDS=jds,JDE=jde, KDS=kds,KDE=kde             &
L01991                        ,IMS=ims,IME=ime, JMS=jms,JME=jme, KMS=kms,KME=kme             &
L01992                        ,ITS=its,ITE=ite, JTS=jts,JTE=jte, KTS=kts,KTE=kte             &
L01993  !Intent-inout 
L01994                        ,TAURESX2D=tauresx2d,TAURESY2D=tauresy2d                       &
L01995                        ,RUBLTEN=rublten,RVBLTEN=rvblten,RTHBLTEN=rthblten             &
L01996                        ,RQIBLTEN=rqiblten,RQNIBLTEN=rqniblten,RQVBLTEN=rqvblten       &
L01997                        ,RQCBLTEN=rqcblten,KVM3D=exch_m,KVH3D=exch_h                   &
L01998  !Intent-out
L01999                        ,TPERT2D=tpert2d,QPERT2D=qpert2d,WPERT2D=wpert2d,SMAW3D=smaw3d &
L02000                        ,TURBTYPE3D=turbtype3d                                         &
L02001                        ,TKE_pbl=tke_pbl,PBLH2D=pblh,KPBL2D=kpbl                       )
L02002                ELSE
L02003                   WRITE ( message , FMT = '(A,8(L1,1X))' )            &
L02004                        'present: '//                                      &
L02005                        'qv_curr, '//                                      &
L02006                        'qc_curr, '//                                      &
L02007                        'qi_curr, '//                                      &
L02008                        'qnc_curr, '//                                     &
L02009                        'qni_curr, '//                                     &
L02010                        'rqvblten, '//                                     &
L02011                        'rqcblten, '//                                     &
L02012                        'rqiblten, '//                                     &
L02013                        'rqniblten= ',                                     &
L02014                        PRESENT( qv_curr ) ,                              &
L02015                        PRESENT( qc_curr ) ,                              &
L02016                        PRESENT( qi_curr ) ,                              &
L02017                        PRESENT( qnc_curr ) ,                             &
L02018                        PRESENT( qni_curr ) ,                             &
L02019                        PRESENT( rqvblten ) ,                             &
L02020                        PRESENT( rqcblten ) ,                             &
L02021                        PRESENT( rqiblten ) ,                             &
L02022                        PRESENT( rqniblten ) 
L02023  
L02024                   CALL wrf_debug(0,message)
L02025                   CALL wrf_error_fatal('Lack arguments to call CAMUWPBL pbl')
L02026                ENDIF
L02027                
L02028  #endif
```

> 讲解：CAMUW（9）：CAM 垂直扩散型（社区大气模式移植），带湍流界面类型 turbtype3d、Galperin 稳定度函数 smaw3d 等精细诊断；要求 qnc/qni 数浓度在场。

<!-- code_extract code_extract.py v1.2
source: phys/module_pbl_driver.F
ranges: L2030-L2084
file_lines: 2887
file_md5: 1c4ca2a3bd7baa4c31b48527e60a4cad
display: line-numbered (strip L-prefix and !file: line to restore)
range_md5: f71dd5f5f250974102c0725e6db28944
seg_lines: 55
-->

```fortran
!file: phys/module_pbl_driver.F    L2030-L2084
L02030             CASE (GBMPBLSCHEME)
L02031                 CALL wrf_debug(100,'in gbmpbl') 
L02032                 IF ( PRESENT( qv_curr )  .AND. PRESENT( qc_curr )  .AND.&
L02033                 PRESENT( qi_curr )                            .AND. &
L02034                 PRESENT( rqvblten ) .AND. PRESENT( rqcblten ) .AND. &
L02035                 PRESENT( rqiblten )                           .AND. &
L02036                 PRESENT( hol      )                           .AND. &
L02037                                         .TRUE.  ) THEN
L02038               CALL gbmpbl(                                           &
L02039                 U3D=u_phytmp,V3D=v_phytmp,TH3D=th_phy,T3D=t_phy      &
L02040                ,QV3D=qv_curr,QC3D=qc_curr,QI3D=qi_curr               &
L02041                ,P3D=p_phy,PI3D=pi_phy                                &
L02042                ,RUBLTEN=rublten,RVBLTEN=rvblten                      &
L02043                ,RTHBLTEN=rthblten,RQVBLTEN=rqvblten                  &
L02044                ,RQCBLTEN=rqcblten,RQIBLTEN=rqiblten                  &
L02045                ,KZM_GBM=exch_m,KTH_GBM=exch_h,KETHL_GBM=exch_tke     & 
L02046                ,EL_GBM=el_pbl,DZ8W=dz8w,Z=z,PSFC=PSFC                &
L02047                ,TKE_PBL=tke_pbl,RTHRATEN=rthraten                    & 
L02048                ,ZNT=znt,UST=ust,ZOL=zol,HOL=hol,PBL=pblh             & 
L02049                ,KPBL2D=kpbl,REGIME=regime                            & 
L02050                ,PSIM=psim,PSIH=psih,XLAND=xland                      &
L02051                ,HFX=hfx,QFX=qfx,TSK=tskold,GZ1OZ0=gz1oz0             &
L02052                ,WSPD=wspd,BR=br,DT=dtbl,DTMIN=dtmin                  &
L02053                ,IDS=ids,IDE=ide,JDS=jds,JDE=jde,KDS=kds,KDE=kde      &
L02054                ,IMS=ims,IME=ime,JMS=jms,JME=jme,KMS=kms,KME=kme      &
L02055                ,ITS=its,ITE=ite,JTS=jts,JTE=jte,KTS=kts,KTE=kte      &
L02056                                                                      )
L02057                ELSE
L02058                 CALL wrf_error_fatal('Lack arguments to call GBM pbl')
L02059                ENDIF
L02060  
L02061  #if ( WRFPLUS == 1 )
L02062  ! this scheme is for WRFPlus only
L02063  !-----------------------------------
L02064          CASE (SURFDRAGSCHEME)
L02065  
L02066             CALL wrf_debug(100,'in SURFDRAG scheme')
L02067  
L02068             CALL surface_drag(                                     &
L02069               RUBLTEN=rublten,RVBLTEN=rvblten                      &  !
L02070              ,U_PHY=u_phy, V_PHY=v_phy, Z=z                                &  !
L02071              ,XLAND=xland, HT=ht, KPBL2D=kpbl                      &  !
L02072              ,IDS=ids,IDE=ide,JDS=jds,JDE=jde,KDS=kds,KDE=kde      &
L02073              ,IMS=ims,IME=ime,JMS=jms,JME=jme,KMS=kms,KME=kme      &
L02074              ,ITS=its,ITE=ite,JTS=jts,JTE=jte,KTS=kts,KTE=kte      &
L02075                                                                    )
L02076  #endif
L02077  
L02078       CASE DEFAULT
L02079  
L02080         WRITE( message , * ) 'The pbl option does not exist: bl_pbl_physics = ', bl_pbl_physics
L02081         CALL wrf_error_fatal ( message )
L02082  
L02083     END SELECT pbl_select
L02084  
```

> 讲解：GBM（12）与 SURFDRAG（98，仅 WRFPLUS）收尾；CASE DEFAULT 报「方案号不存在」。END SELECT 带命名标签 pbl_select——长 SELECT CASE 的可读性写法。

### 3.6 CASE 之外的四个附加模块

<!-- code_extract code_extract.py v1.2
source: phys/module_pbl_driver.F
ranges: L2085-L2174
file_lines: 2887
file_md5: 1c4ca2a3bd7baa4c31b48527e60a4cad
display: line-numbered (strip L-prefix and !file: line to restore)
range_md5: 7872b5da1aaa9ef7b44aabba5d9735db
seg_lines: 90
-->

```fortran
!file: phys/module_pbl_driver.F    L2085-L2174
L02085  #if (EM_CORE==1)
L02086  !
L02087  ! ... paj: wind farm ...
L02088  !
L02089      windfarm_select: SELECT CASE(windfarm_opt)
L02090  
L02091        CASE (fitchscheme)
L02092  
L02093                    IF (PRESENT(id) .AND.                                  &
L02094                       PRESENT(z_at_w) ) THEN
L02095  !
L02096                       CALL wrf_debug(100,'in phys/module_wind_fitch.F')
L02097                       CALL dragforce(                                  &
L02098                       & ID=id                                             &
L02099                       &,Z_AT_W=z_at_w,u=u_phy,v=v_phy                     &
L02100                       &,DX=dx,DZ=dz8w,DT=dt                               &
L02101                       &,QKE=qke                                           &
L02102                       &,DU=rublten,DV=rvblten                             &
L02103                       &,WINDFARM_OPT=windfarm_opt,POWER=power             &
L02104                       ! THE FOLLOWING LINES OF CODE ARE LICENSED UNDER doc/licenses/fraunhofer_license.txt
L02105                       &,THRUST=thrust                                     &
L02106                       ! END LICENSE
L02107                       &,IDS=ids,IDE=ide,JDS=jds,JDE=jde,KDS=kds,KDE=kde   &
L02108                       &,IMS=ims,IME=ime,JMS=jms,JME=jme,KMS=kms,KME=kme   &
L02109                       &,ITS=its,ITE=ite,JTS=jts,JTE=jte,KTS=kts,KTE=kte   &
L02110                       &)
L02111  
L02112                      IF (bl_mynn_tkeadvect) THEN
L02113                         qke_adv=qke
L02114                      ENDIF
L02115  
L02116                    ELSE
L02117                       WRITE ( message , FMT = '(A,6(L1,1X))' )           &
L02118                       'present: '//                                      &
L02119                       'ID, '//                                           &
L02120                       'z_at_w, '//                                       &
L02121                       'xlat_u, '//                                       &
L02122                       'xlong_u, '//                                      &
L02123                       'xlat_v, '//                                       &
L02124                       'xlong_v = ' ,                                     &
L02125                        PRESENT( id ) ,                                   &
L02126                        PRESENT( z_at_w ) 
L02127                       CALL wrf_debug(0,message)
L02128                       CALL wrf_error_fatal('Lack arguments to call turbine_drag')
L02129                    ENDIF
L02130  
L02131        ! Yulong add new wind farm schemes with wind turbine loss effect
L02132        CASE (mavscheme)
L02133                    IF (PRESENT(id) .AND.                                  &
L02134                       PRESENT(z_at_w) ) THEN
L02135                       CALL wrf_debug(100,'in phys/module_wind_mav.F')
L02136                       CALL dragforce_mav(itimestep                     &
L02137                       &,ID=id                                             &
L02138                       &,Z_AT_W=z_at_w,z_at_m=z,u=u_phy,v=v_phy            &
L02139                       &,DX=dx,DZ=dz8w,DT=dt                               &
L02140                       &,TKE=TKE_windfarm                                  &
L02141                       &,DU=rublten,DV=rvblten                             &
L02142                       &,WINDFARM_OPT=windfarm_opt,POWER=power             &
L02143                       &,windfarm_wake_model=windfarm_wake_model           &
L02144                       &,windfarm_overlap_method=windfarm_overlap_method   &
L02145                       &,xland=xland                                       &
L02146                       &,cosa=cosa,sina=sina                               &
L02147                       &,IDS=ids,IDE=ide,JDS=jds,JDE=jde,KDS=kds,KDE=kde   &
L02148                       &,IMS=ims,IME=ime,JMS=jms,JME=jme,KMS=kms,KME=kme   &
L02149                       &,ITS=its,ITE=ite,JTS=jts,JTE=jte,KTS=kts,KTE=kte   &
L02150                       &)
L02151  
L02152                       IF (bl_mynn_tkeadvect) THEN
L02153                          QKE = QKE + 2.*TKE_windfarm
L02154                          qke_adv=qke
L02155                       ENDIF
L02156  
L02157                    ELSE
L02158                       WRITE ( message , FMT = '(A,6(L1,1X))' )           &
L02159                       'present: '//                                      &
L02160                       'ID, '//                                           &
L02161                       'z_at_w, '//                                       &
L02162                       'xlat_u, '//                                       &
L02163                       'xlong_u, '//                                      &
L02164                       'xlat_v, '//                                       &
L02165                       'xlong_v = ' ,                                     &
L02166                        PRESENT( id ) ,                                   &
L02167                        PRESENT( z_at_w )
L02168                       CALL wrf_debug(0,message)
L02169                       CALL wrf_error_fatal('Lack arguments to call dragforce_mav')
L02170                    ENDIF                 
L02171  
L02172     END SELECT windfarm_select
L02173  #endif
L02174  
```

> 讲解：**风机场参数化**独立成第二个 SELECT（windfarm_opt）：FITCH（16）与 MAV 两族风机拖曳方案直接把动量汇写进 rublten/rvblten——风机与 PBL 方案解耦、可任意组合；bl_mynn_tkeadvect 打开时把风机 TKE 源并回 qke（MAV 支路乘 2：QKE=2·TKE 的约定，见 code_09a）。

<!-- code_extract code_extract.py v1.2
source: phys/module_pbl_driver.F
ranges: L2176-L2236
file_lines: 2887
file_md5: 1c4ca2a3bd7baa4c31b48527e60a4cad
display: line-numbered (strip L-prefix and !file: line to restore)
range_md5: 213003da0df5d4f83f5fb53acfe78ef7
seg_lines: 61
-->

```fortran
!file: phys/module_pbl_driver.F    L2176-L2236
L02176     IF (PRESENT(GWD_opt)) THEN
L02177       IF (GWD_opt .EQ. 1) THEN
L02178         IF (PRESENT(dtaux3d)) THEN
L02179               CALL gwdo(                                             &
L02180                 U3D=u_phy,V3D=v_phy,T3D=t_phy                        &
L02181                ,QV3D=qv_curr                                         &
L02182                ,P3D=p_phy,P3DI=p8w,PI3D=pi_phy,Z=z                   &
L02183                ,RUBLTEN=rublten,RVBLTEN=rvblten                      &
L02184                ,DTAUX3D=dtaux3d,DTAUY3D=dtauy3d                      &
L02185                ,DUSFCG=dusfcg,DVSFCG=dvsfcg                          &
L02186                ,VAR2D=var2d,OC12D=oc12d                              &
L02187                ,OA2D1=oa1,OA2D2=oa2,OA2D3=oa3,OA2D4=oa4              &
L02188                ,OL2D1=ol1,OL2D2=ol2,OL2D3=ol3,OL2D4=ol4              &
L02189                ,elvmax=elvmax,SINA=sina,COSA=cosa                    &
L02190                ,ZNU=znu,ZNW=znw,P_TOP=p_top                          &
L02191                ,CP=cp,G=g,RD=r_d                                     &
L02192                ,RV=r_v,EP1=ep_1,PI=3.141592653                       &
L02193                ,DT=dtbl,DX=dx2d,KPBL2D=kpbl,ITIMESTEP=itimestep      &
L02194                ,errmsg=errmsg,errflg=errflg                          &
L02195                ,dx_factor = dx_factor, if_nonhyd = if_nonhyd         &
L02196                ,IDS=ids,IDE=ide,JDS=jds,JDE=jde,KDS=kds,KDE=kde      &
L02197                ,IMS=ims,IME=ime,JMS=jms,JME=jme,KMS=kms,KME=kme      &
L02198                ,ITS=its,ITE=ite,JTS=jts,JTE=jte,KTS=kts,KTE=kte      )
L02199         ENDIF
L02200       ELSEIF(gwd_opt .EQ. 3) THEN
L02201               CALL gwdo_gsl(                                         &
L02202                 U3D=u_phy,V3D=v_phy,T3D=t_phy                        &
L02203                ,QV3D=qv_curr                                         &
L02204                ,P3D=p_phy,P3DI=p8w,PI3D=pi_phy,Z=z                   &
L02205                ,RUBLTEN=rublten,RVBLTEN=rvblten,RTHBLTEN=rthblten    &
L02206                ,DTAUX3D_ls=dtaux3d_ls,DTAUY3D_ls=dtauy3d_ls          &
L02207                ,DTAUX3D_bl=dtaux3d_bl,DTAUY3D_bl=dtauy3d_bl          &
L02208                ,DTAUX3D_ss=dtaux3d_ss,DTAUY3D_ss=dtauy3d_ss          &
L02209                ,DTAUX3D_fd=dtaux3d_fd,DTAUY3D_fd=dtauy3d_fd          &
L02210                ,DUSFCG_ls=dusfcg_ls,DVSFCG_ls=dvsfcg_ls              &
L02211                ,DUSFCG_bl=dusfcg_bl,DVSFCG_bl=dvsfcg_bl              &
L02212                ,DUSFCG_ss=dusfcg_ss,DVSFCG_ss=dvsfcg_ss              &
L02213                ,DUSFCG_fd=dusfcg_fd,DVSFCG_fd=dvsfcg_fd              &
L02214                ,xland=xland,br=br                                    &
L02215                ,VAR2D=var2dls,OC12D=oc12dls                          &
L02216                ,OA2D1=oa1ls,OA2D2=oa2ls,OA2D3=oa3ls,OA2D4=oa4ls      &
L02217                ,OL2D1=ol1ls,OL2D2=ol2ls,OL2D3=ol3ls,OL2D4=ol4ls      &
L02218                ,VAR2Dss=var2dss,OC12Dss=oc12dss                      &
L02219                ,OA2D1ss=oa1ss,OA2D2ss=oa2ss,OA2D3ss=oa3ss            &
L02220                ,OA2D4ss=oa4ss,OL2D1ss=ol1ss,OL2D2ss=ol2ss            &
L02221                ,OL2D3ss=ol3ss,OL2D4ss=ol4ss                          &
L02222                ,SINA=sina,COSA=cosa                                  &
L02223                ,ZNU=znu,ZNW=znw,P_TOP=p_top                          &
L02224                ,DZ=dz8w,PBLH=PBLH                                    &
L02225                ,CP=cp,G=g,RD=r_d                                     &
L02226                ,RV=r_v,EP1=ep_1,PI=3.141592653                       &
L02227                ,DT=dtbl,DX=dx,KPBL2D=kpbl                            &
L02228                ,ITIMESTEP=itimestep,gwd_opt=gwd_opt                  &
L02229                ,gwd_diags=gwd_diags                                  &
L02230                ,spp_pbl=spp_pbl,pattern_spp_pbl=pattern_spp_pbl      &
L02231                ,IDS=ids,IDE=ide,JDS=jds,JDE=jde,KDS=kds,KDE=kde      &
L02232                ,IMS=ims,IME=ime,JMS=jms,JME=jme,KMS=kms,KME=kme      &
L02233                ,ITS=its,ITE=ite,JTS=jts,JTE=jte,KTS=kts,KTE=kte      )
L02234       ENDIF
L02235     ENDIF
L02236  
```

> 讲解：**重力波拖曳**挂在本 driver 的末尾（GWD_opt=1 经典 gwdo / =3 GSL 扩展版）：次网格地形对动量的吸收/破碎项与 PBL 湍流应力同量纲、同出口（rublten/rvblten），故共用此驱动入口；GSL 版还接受 SPP 扰动场。

<!-- code_extract code_extract.py v1.2
source: phys/module_pbl_driver.F
ranges: L2237-L2255
file_lines: 2887
file_md5: 1c4ca2a3bd7baa4c31b48527e60a4cad
display: line-numbered (strip L-prefix and !file: line to restore)
range_md5: 9278c4ee76ab94f839772a6b5f33764c
seg_lines: 19
-->

```fortran
!file: phys/module_pbl_driver.F    L2237-L2255
L02237  #if (EM_CORE==1)                                                                                                                                                                             
L02238  !JOE-added - fog (cloud) water deposition calculation
L02239     IF (grav_settling .GE. 1) THEN
L02240        IF ( PRESENT(vdfg) .AND. PRESENT(qc_curr)) THEN
L02241           !NOTE 1: vdfg is calculated in the surface driver.
L02242           !NOTE 2: as of now, only qc_curr settles, not # conc.
L02243  
L02244            CALL bl_fogdes(                                        &
L02245                 vdfg,qc_curr,dtbl,rho,dz8w,grav_settling,RQCBLTEN,&
L02246                 ids,ide, jds,jde, kds,kde,                        &
L02247                 ims,ime, jms,jme, kms,kme,                        &
L02248                 i_start(ij),i_end(ij),                            &
L02249                 j_start(ij),j_end(ij),kts,kte                     )
L02250        ELSE
L02251            CALL wrf_error_fatal('Missing args for bl_fogdes in pbl driver')
L02252        ENDIF
L02253     ENDIF
L02254  !JOE-END
L02255  #endif
```

> 讲解：**雾水沉降** bl_fogdes：grav_settling≥1（MYNN 面层 namelist 开关）时把云水重力沉降加进 RQCBLTEN；注释点明 vdfg（沉降速度）由 surface driver 算——跨 driver 的隐式数据流。

<!-- code_extract code_extract.py v1.2
source: phys/module_pbl_driver.F
ranges: L2257-L2332
file_lines: 2887
file_md5: 1c4ca2a3bd7baa4c31b48527e60a4cad
display: line-numbered (strip L-prefix and !file: line to restore)
range_md5: d9fc500a69c291e00747026e2ee48afb
seg_lines: 76
-->

```fortran
!file: phys/module_pbl_driver.F    L2257-L2332
L02257       IF (idiff.eq.1) THEN
L02258  
L02259  !Alberto: here we call the general routine to solve the diffusion
L02260  ! + all the source/sink terms.
L02261  ! the only thing that should be passed from the PBL schemes is the value of the exch_h, and exch_m 
L02262  ! (and the non local terms, if present, through the b).
L02263  ! So, this routine can be used by any of the previous schemes. We only need to pass the right variables
L02264  ! (and eliminate the computation of the tendencies from the previous routines, to avoid doing twice the job).
L02265  ! As I explain below, in the routine, here we could extract the vertical turbulent 
L02266  ! fluxes (something that will be general for all the routines).
L02267  !!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!
L02268      
L02269              
L02270            CALL diff3d  (DT=dtbl,CP=cp,DZ=dz8w,TH=th_phy,QV=qv_curr,QC=qc_curr,T=t_phy  &
L02271                ,U=u_phy,V=v_phy,RHO=rho,EXCH_H=exch_h                  &
L02272                ,EXCH_M=exch_m                                          &
L02273                ,RUBLTEN=rublten,RVBLTEN=rvblten,RTHBLTEN=rthblten      &
L02274                ,WU=wu_tur,WV=wv_tur,WT=wt_tur,WQ=wq_tur                &
L02275                ,RQVBLTEN=rqvblten,RQCBLTEN=rqcblten                    &
L02276                ,A_U=a_u,A_V=a_v,A_T=a_t,A_Q=a_q        &
L02277                ,B_U=b_u,B_V=b_v,B_T=b_t,B_Q=b_q        &
L02278                ,SF=sf,VL=vl            &
L02279                ,IDS=ids,IDE=ide,JDS=jds,JDE=jde,KDS=kds,KDE=kde        &
L02280                ,IMS=ims,IME=ime,JMS=jms,JME=jme,KMS=kms,KME=kme        &
L02281                ,ITS=its,ITE=ite,JTS=jts,JTE=jte,KTS=kts,KTE=kte)
L02282  
L02283            DEALLOCATE (a_u)       ! Implicit component for the momemtum in X-direction
L02284            DEALLOCATE (a_v)       ! Implicit component for the momemtum in Y-direction
L02285            DEALLOCATE (a_t)       ! Implicit component for the Pot. Temp.
L02286            DEALLOCATE (a_q)       ! Implicit component for the water vapor
L02287            DEALLOCATE (b_u)       ! Explicit component for the momemtum in X-direction
L02288            DEALLOCATE (b_v)       ! Explicit component for the momemtum in Y-direction
L02289            DEALLOCATE (b_t)       ! Explicit component for the Pot. Temp.
L02290            DEALLOCATE (b_q)       ! Explicit component for the water vapor
L02291            DEALLOCATE (sf )       ! surfaces
L02292            DEALLOCATE (vl )       ! volumes
L02293       ENDIF       !idiff
L02294        
L02295            IF(scalar_pblmix .GT. 0)THEN
L02296              CALL diff4d  (DT=dtbl,DZ=dz8w, SCALAR=scalar, is_scalar=.true.  &
L02297                ,RHO=rho,EXCH_H=exch_h        &
L02298                ,EXCH_M=exch_m                &
L02299                ,SCALAR_TEND=scalar_tend      &
L02300                ,NUM_SCALAR=num_scalar, PARAM_FIRST_SCALAR=param_first_scalar &
L02301                ,IDS=ids,IDE=ide,JDS=jds,JDE=jde,KDS=kds,KDE=kde        &
L02302                ,IMS=ims,IME=ime,JMS=jms,JME=jme,KMS=kms,KME=kme        &
L02303                ,ITS=its,ITE=ite,JTS=jts,JTE=jte,KTS=kts,KTE=kte)
L02304            ENDIF
L02305            IF(tracer_pblmix .GT. 0)THEN
L02306              CALL diff4d  (DT=dtbl,DZ=dz8w, SCALAR=tracer, is_scalar=.false.  &
L02307                ,RHO=rho,EXCH_H=exch_h        &
L02308                ,EXCH_M=exch_m                &
L02309                ,SCALAR_TEND=tracer_tend      &
L02310                ,NUM_SCALAR=num_tracer, PARAM_FIRST_SCALAR=param_first_scalar &
L02311                ,IDS=ids,IDE=ide,JDS=jds,JDE=jde,KDS=kds,KDE=kde        &
L02312                ,IMS=ims,IME=ime,JMS=jms,JME=jme,KMS=kms,KME=kme        &
L02313                ,ITS=its,ITE=ite,JTS=jts,JTE=jte,KTS=kts,KTE=kte)
L02314            ENDIF
L02315  
L02316       IF (distributed_ahe_opt == 1) THEN
L02317         call cal_mon_day(julday, julyr, jmonth, jday)
L02318         ihour = (jmonth - 1) * 24 + MOD(INT(gmt + xtime / 60.0), 24)
L02319         DO j = jts, jte
L02320         DO i = its, ite
L02321           ! Volumetric heat capacity of air = 1200 J/(K m3)
L02322           RTHBLTEN(i, 1, j) = RTHBLTEN(i, 1, j) + ahe(i, ihour, j) / 1200 / DZ8W(i, 1, j)
L02323         END DO
L02324         END DO
L02325       END IF
L02326  
L02327     ENDDO
L02328     !$OMP END PARALLEL DO
L02329  
L02330     ENDIF
L02331  
L02332     END SUBROUTINE pbl_driver
```

> 讲解：①idiff=1 的统一隐式扩散出口 diff3d（当前休眠——L1021 硬编码 idiff=0）；②scalar_pblmix/tracer_pblmix>0 时对化学物种/示踪物调用 diff4d 做「用 PBL 交换系数的垂直混合」——WRF-Chem 与通用 tracer 的零额外物理复用；③**分布式人为热 AHE**（distributed_ahe_opt=1）：cal_mon_day 把日期折算成 ahe 数组的月-时索引，把小时级人为热通量除以空气容积热容 1200 J/(K·m³) 与最低层厚度，直接加进最低层 RTHBLTEN——论文 2 的 ahe 数据集（geog y2050_ahe）正是走这个开关进场；④END SUBROUTINE 前的ENDIF 闭合 run_param——本步未触发时全部逻辑被跳过。

## 四、SPP 与通用扩散辅助件

<!-- code_extract code_extract.py v1.2
source: phys/module_pbl_driver.F
ranges: L2334-L2384
file_lines: 2887
file_md5: 1c4ca2a3bd7baa4c31b48527e60a4cad
display: line-numbered (strip L-prefix and !file: line to restore)
range_md5: 88b35ce6cf3cd55eb9e31cc3c57cdbf5
seg_lines: 51
label: subroutine Add_multi_perturb_pbl_perturbations
-->

```fortran
!file: phys/module_pbl_driver.F    L2334-L2384    (subroutine Add_multi_perturb_pbl_perturbations)
L02334     subroutine  Add_multi_perturb_pbl_perturbations (perts_qvapor, perts_qcloud, &
L02335                    perts_th, perts_tke, pert_mynn_qv, pert_mynn_qc, pert_mynn_t, pert_mynn_qke, &
L02336                    th_phy, qke, qke_adv, qv_curr, qc_curr, bl_mynn_tkeadvect, qke_tmp, its, ite, jts, jte, &
L02337                    ims, ime, jms, jme, kms, kme, kts, kte)
L02338  
L02339  
L02340       implicit none
L02341  
L02342       integer, intent(in) :: its, ite, jts, jte, ims, ime, jms, jme, kms, kme, kts, kte
L02343       logical, optional, intent(in) :: bl_mynn_tkeadvect
L02344       real, intent(in) :: pert_mynn_qv, pert_mynn_qc, pert_mynn_t, pert_mynn_qke
L02345       real, dimension(ims:ime, kms:kme, jms:jme), optional, intent (in) :: perts_qvapor, &
L02346         perts_qcloud, perts_th, perts_tke
L02347       real, dimension(ims:ime, kms:kme, jms:jme), intent (inout) :: th_phy, qke, qv_curr, qc_curr
L02348       real, optional, dimension (ims:ime, kms:kme, jms:jme), intent(inout) :: qke_adv
L02349       real, dimension (its:ite, kts:kte, jts:jte), intent(out) :: qke_tmp
L02350  
L02351       integer :: i, j, k
L02352  
L02353  
L02354       do j = jts, jte
L02355         do k = kts, kte 
L02356           do i = its, ite 
L02357             qc_curr(i, k, j) = max (QCLOUD_MIN, (1.0 + perts_qcloud(i, k, j) * pert_mynn_qc) * qc_curr(i, k, j))
L02358             qv_curr(i, k, j) = max (QVAPOR_MIN, (1.0 + perts_qvapor(i, k, j) * pert_mynn_qv) * qv_curr(i, k, j))
L02359             th_phy(i, k, j) = (1.0 + perts_th(i, k, j) * pert_mynn_t) * th_phy(i, k, j)
L02360           end do
L02361         end do
L02362       end do
L02363  
L02364       if (bl_mynn_tkeadvect) then
L02365         do j = jts, jte
L02366           do k = kts, kte
L02367             do i = its, ite
L02368               qke_tmp(i, k, j) = qke_adv(i, k, j)
L02369               qke_adv(i, k, j) = max (QKE_MIN, (1.0 + perts_tke(i, k, j) * pert_mynn_qke) * qke_adv(i, k, j))
L02370             end do
L02371           end do
L02372         end do
L02373       else
L02374         do j = jts, jte
L02375           do k = kts, kte
L02376             do i = its, ite
L02377               qke_tmp(i, k, j) = qke(i, k, j)
L02378               qke(i, k, j) = max (QKE_MIN, (1.0 + perts_tke(i, k, j) * pert_mynn_qke) * qke(i, k, j))
L02379             end do
L02380           end do
L02381         end do
L02382       end if
L02383  
L02384     end subroutine  Add_multi_perturb_pbl_perturbations
```

<!-- code_extract code_extract.py v1.2
source: phys/module_pbl_driver.F
ranges: L2386-L2435
file_lines: 2887
file_md5: 1c4ca2a3bd7baa4c31b48527e60a4cad
display: line-numbered (strip L-prefix and !file: line to restore)
range_md5: 3abd1bfbba86a16763bfa3026c81669d
seg_lines: 50
label: subroutine Remove_multi_perturb_pbl_perturbations
-->

```fortran
!file: phys/module_pbl_driver.F    L2386-L2435    (subroutine Remove_multi_perturb_pbl_perturbations)
L02386     subroutine  Remove_multi_perturb_pbl_perturbations (perts_qvapor, perts_qcloud, &
L02387                    perts_th, perts_tke, pert_mynn_qv, pert_mynn_qc, pert_mynn_t, pert_mynn_qke, &
L02388                    th_phy, qke, qke_adv, qv_curr, qc_curr, bl_mynn_tkeadvect, qke_tmp, its, ite, jts, jte, &
L02389                    ims, ime, jms, jme, kms, kme, kts, kte)
L02390  
L02391  
L02392       implicit none
L02393  
L02394       integer, intent(in) :: its, ite, jts, jte, ims, ime, jms, jme, kms, kme, kts, kte
L02395       logical, optional, intent(in) :: bl_mynn_tkeadvect
L02396       real, intent(in) :: pert_mynn_qv, pert_mynn_qc, pert_mynn_t, pert_mynn_qke
L02397       real, dimension(ims:ime, kms:kme, jms:jme), optional, intent (in) :: perts_qvapor, &
L02398         perts_qcloud, perts_th, perts_tke
L02399       real, dimension(ims:ime, kms:kme, jms:jme), intent (inout) :: th_phy, qke, qv_curr, qc_curr
L02400       real, optional, dimension (ims:ime, kms:kme, jms:jme), intent(inout) :: qke_adv
L02401       real, dimension (its:ite, kts:kte, jts:jte), intent(in) :: qke_tmp
L02402  
L02403       integer :: i, j, k
L02404  
L02405  
L02406       do j = jts, jte
L02407         do k = kts, kte
L02408           do i = its, ite
L02409             qc_curr(i, k, j) = max (QCLOUD_MIN, qc_curr(i, k, j) / (1.0 + perts_qcloud(i, k, j) * pert_mynn_qc))
L02410             qv_curr(i, k, j) = max (QVAPOR_MIN, qv_curr(i, k, j) / (1.0 + perts_qvapor(i, k, j) * pert_mynn_qv))
L02411             th_phy(i, k, j) = th_phy(i, k, j) / (1.0 + perts_th(i, k, j) * pert_mynn_t)
L02412           end do
L02413         end do
L02414       end do
L02415  
L02416       if (bl_mynn_tkeadvect) then
L02417         do j = jts, jte
L02418           do k = kts, kte
L02419             do i = its, ite
L02420               qke_adv(i, k, j) = max (QKE_MIN, qke_adv(i, k, j) - perts_tke(i, k, j) * pert_mynn_qke * qke_tmp(i, k, j))
L02421               qke(i, k, j) = qke_adv(i, k, j)
L02422             end do
L02423           end do
L02424         end do
L02425       else
L02426         do j = jts, jte
L02427           do k = kts, kte
L02428             do i = its, ite
L02429               qke(i, k, j) = max (QKE_MIN, qke(i, k, j) - perts_tke(i, k, j) * pert_mynn_qke * qke_tmp(i, k, j))
L02430             end do
L02431           end do
L02432         end do
L02433       end if
L02434  
L02435     end subroutine  Remove_multi_perturb_pbl_perturbations
```

> 讲解：SPP 乘性扰动的成对实现：Add 把 (1+pattern·幅度) 乘在 qv/qc/th 上（下限钳到 QCLOUD_MIN/QVAPOR_MIN），qke/qke_adv 同法但多存一份 qke_tmp；Remove 对 qv/qc/th 用**除法**还原、对 qke 用**减法**（qke−pattern·幅度·qke_tmp）——除法在扰动为负时可能把 qke 打到 0 以下，减法加 max(QKE_MIN,·) 保证非负。这是「同一物理量两套还原公式」的活教材：改 SPP 幅度时两处语义都要顾。

<!-- code_extract code_extract.py v1.2
source: phys/module_pbl_driver.F
ranges: L2438-L2639
file_lines: 2887
file_md5: 1c4ca2a3bd7baa4c31b48527e60a4cad
display: line-numbered (strip L-prefix and !file: line to restore)
range_md5: ced0b53f9a124852dc2ff4dee0cb4c43
seg_lines: 202
label: subroutine diff3d
-->

```fortran
!file: phys/module_pbl_driver.F    L2438-L2639    (subroutine diff3d)
L02438            SUBROUTINE diff3d(DT,CP,DZ,TH ,QV,QC,T,U,V,RHO                              &
L02439                ,EXCH_H,EXCH_M                   &  
L02440                ,RUBLTEN,RVBLTEN,RTHBLTEN    &
L02441                ,RQVBLTEN,RQCBLTEN                  &
L02442                ,WU,WV,WT,WQ                 &
L02443                ,A_U,A_V,A_T,A_Q      &
L02444                ,B_U,B_V,B_T,B_Q      &
L02445                ,SF,VL        &
L02446                ,IDS,IDE,JDS,JDE,KDS,KDE      &
L02447                ,IMS,IME,JMS,JME,KMS,KME      &
L02448                ,ITS,ITE,JTS,JTE,KTS,KTE      &
L02449                                                                      )
L02450  !!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!
L02451  !    Subroutine written by Alberto Martilli, CIEMAT, Spain,
L02452  !    e-mail:alberto_martilli@ciemat.es
L02453  !    August 2008.
L02454  !!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!
L02455  ! ALberto
L02456  ! This routine solves the vertical diffusion 
L02457  ! + other source/sink terms (surface fluxes, building drag, non local terms, etc.)
L02458  ! for U,V, potential temperature and moisture. The equation should be written 
L02459  ! as follow, for a generic variable M:
L02460  ! 
L02461  !      dM      1     d      dM
L02462  !     ---- =----  ---(rho*K----)+AM+B
L02463  !      dt     rho    dz     dz  
L02464  ! where A and B are the implict and explcit coefficients of the source/sink terms
L02465  ! (at the lowest level the surface fluxes should go in these terms)
L02466  !!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!
L02467  !-----------------------------------------------------------------------
L02468  
L02469        IMPLICIT NONE
L02470  !
L02471  !----------------------------------------------------------------------
L02472        INTEGER,INTENT(IN) :: IDS,IDE,JDS,JDE,KDS,KDE                    &
L02473       &                     ,IMS,IME,JMS,JME,KMS,KME                    &
L02474       &                     ,ITS,ITE,JTS,JTE,KTS,KTE
L02475  
L02476  ! INputs
L02477        real DT,CP
L02478        REAL,DIMENSION(IMS:IME,KMS:KME,JMS:JME),INTENT(IN) :: DZ ! Depth of vertical levels
L02479        REAL,DIMENSION(IMS:IME,KMS:KME,JMS:JME),INTENT(IN) :: TH ! Potential Temperature
L02480        REAL,DIMENSION(IMS:IME,KMS:KME,JMS:JME),INTENT(IN) :: QV ! water vapor mixing ratio (kg/kg)
L02481        REAL,DIMENSION(IMS:IME,KMS:KME,JMS:JME),INTENT(IN) :: QC ! cloud water mixing ratio (kg/kg)
L02482        REAL,DIMENSION(IMS:IME,KMS:KME,JMS:JME),INTENT(IN) :: T  ! temperature
L02483        REAL,DIMENSION(IMS:IME,KMS:KME,JMS:JME),INTENT(IN) :: U ! X-compnent of the wind
L02484        REAL,DIMENSION(IMS:IME,KMS:KME,JMS:JME),INTENT(IN) :: V ! Y-compnent of the wind
L02485        REAL,DIMENSION(IMS:IME,KMS:KME,JMS:JME),INTENT(IN) :: RHO ! Air Density
L02486        REAL,DIMENSION(IMS:IME,KMS:KME,JMS:JME),INTENT(IN) :: EXCH_H ! Turbulent coefficient for heat
L02487        REAL,DIMENSION(IMS:IME,KMS:KME,JMS:JME),INTENT(IN) :: EXCH_M ! Turbulent coefficient for momentum 
L02488        
L02489        REAL,DIMENSION(IMS:IME,KMS:KME,JMS:JME),INTENT(IN) :: A_U ! Implicit coefficient for DRAG (x -component)
L02490        REAL,DIMENSION(IMS:IME,KMS:KME,JMS:JME),INTENT(IN) :: B_U ! Explicit coefficient for DRAG (x -component)
L02491        REAL,DIMENSION(IMS:IME,KMS:KME,JMS:JME),INTENT(IN) :: A_V ! Implicit coefficient for DRAG (y -component)
L02492        REAL,DIMENSION(IMS:IME,KMS:KME,JMS:JME),INTENT(IN) :: B_V ! Explicit coefficient for DRAG (y -component)
L02493        REAL,DIMENSION(IMS:IME,KMS:KME,JMS:JME),INTENT(IN) :: A_T ! Implicit coefficient for Heat flux from buildings
L02494        REAL,DIMENSION(IMS:IME,KMS:KME,JMS:JME),INTENT(IN) :: B_T ! Explicit coefficient for Heat flux from buildings
L02495        REAL,DIMENSION(IMS:IME,KMS:KME,JMS:JME),INTENT(IN) :: A_Q ! Implicit coefficient for moisture flux
L02496        REAL,DIMENSION(IMS:IME,KMS:KME,JMS:JME),INTENT(IN) :: B_Q ! Explicit coefficient for moisture flux 
L02497      
L02498        REAL,DIMENSION(IMS:IME,KMS:KME,JMS:JME),INTENT(IN) :: VL ! fraction of air volume in the grid cell
L02499        REAL,DIMENSION(IMS:IME,KMS:KME,JMS:JME),INTENT(IN) :: SF ! fraction of air at the face of the grid cell
L02500  !outputs
L02501        REAL,DIMENSION(IMS:IME,KMS:KME,JMS:JME),INTENT(OUT) :: RUBLTEN ! tendency for x-wind component
L02502        REAL,DIMENSION(IMS:IME,KMS:KME,JMS:JME),INTENT(OUT) :: RVBLTEN ! tendency for y-wind component
L02503        REAL,DIMENSION(IMS:IME,KMS:KME,JMS:JME),INTENT(OUT) :: RTHBLTEN ! tendency for Potential Temperature
L02504        REAL,DIMENSION(IMS:IME,KMS:KME,JMS:JME),INTENT(OUT) :: RQVBLTEN ! tendency for water vapor mixing ratio (kg/kg)
L02505        REAL,DIMENSION(IMS:IME,KMS:KME,JMS:JME),INTENT(OUT) :: RQCBLTEN ! tendency for cloud water mixing ratio (kg/kg)
L02506        REAL,DIMENSION(IMS:IME,KMS:KME,JMS:JME),INTENT(OUT) :: WU ! turbulent flux of momentum (x)
L02507        REAL,DIMENSION(IMS:IME,KMS:KME,JMS:JME),INTENT(OUT) :: WV ! turbulent flux of momentum (y)
L02508        REAL,DIMENSION(IMS:IME,KMS:KME,JMS:JME),INTENT(OUT) :: WT ! turbulent flux of potential temperature
L02509        REAL,DIMENSION(IMS:IME,KMS:KME,JMS:JME),INTENT(OUT) :: WQ ! turbulent flux of water vapor
L02510  ! Parameters
L02511       REAL ELOCP 
L02512  ! locals (same meaning as above, but 1D)
L02513  
L02514        real u1d(kms:kme),v1d(kms:kme),exch_h1d(kms:kme)
L02515        real the1d(kms:kme) ! Equivalent potential temperature
L02516        real exch_m1d(kms:kme),qv1d(kms:kme),qc1d(kms:kme)
L02517        real dz1d(kms:kme),rho1d(kms:kme),rhoz1d(kms:kme)
L02518        real sf1d(kms:kme),vl1d(kms:kme)   
L02519        real a_u1d(kms:kme),b_u1d(kms:kme)
L02520        real a_v1d(kms:kme),b_v1d(kms:kme)
L02521        real a_t1d(kms:kme),b_t1d(kms:kme)
L02522        real a_q1d(kms:kme),b_q1d(kms:kme)
L02523        real a_qc1d(kms:kme),b_qc1d(kms:kme)
L02524        real wu1d(kms:kme),wv1d(kms:kme),wt1d(kms:kme),wq1d(kms:kme),wqc1d(kms:kme)
L02525        real thnew
L02526  !
L02527        integer i,k,j  
L02528  !----------------------------------------------------------------------
L02529        ELOCP=2.72E6/CP
L02530        u1d=0.
L02531        v1d=0.
L02532        exch_h1d=0.
L02533        exch_m1d=0.
L02534        qv1d=0.
L02535        qc1d=0.
L02536        dz1d=0.
L02537        rho1d=0.
L02538        rhoz1d=0.
L02539        sf1d=0.
L02540        vl1d=0.
L02541        a_u1d=0.
L02542        a_v1d=0.
L02543        a_t1d=0.
L02544        a_q1d=0.
L02545        a_qc1d=0.
L02546        b_u1d=0.
L02547        b_v1d=0.
L02548        b_t1d=0.
L02549        b_q1d=0.
L02550        b_qc1d=0.
L02551         
L02552        do j=jts,jte
L02553        do i=its,ite
L02554  
L02555  ! put three D variables in temporary 1D variables
L02556  
L02557         do k=kts,kte
L02558          u1d(k)=U(i,k,j)
L02559          v1d(k)=V(i,k,j)
L02560          the1d(k)=TH(i,k,j)*(QC(i,k,j)*(-ELOCP/T(i,k,j))+1)
L02561          qv1d(k)=qv(i,k,j)
L02562          dz1d(k)=dz(i,k,j)
L02563          rho1d(k)=rho(i,k,j) 
L02564          a_u1d(k)=a_u(i,k,j)
L02565          b_u1d(k)=b_u(i,k,j)
L02566          a_v1d(k)=a_v(i,k,j)
L02567          b_v1d(k)=b_v(i,k,j)
L02568          a_t1d(k)=a_t(i,k,j)
L02569          b_t1d(k)=b_t(i,k,j)
L02570          a_q1d(k)=a_q(i,k,j)
L02571          b_q1d(k)=b_q(i,k,j)
L02572          a_qc1d(k)=0.
L02573          b_qc1d(k)=0.
L02574          vl1d(k)=vl(i,k,j)
L02575          sf1d(k)=sf(i,k,j)
L02576         enddo
L02577         sf1d(kte+1)=1. 
L02578         do k=kts,kte    
L02579          exch_h1d(k)=exch_h(i,k,j)
L02580          exch_m1d(k)=exch_m(i,k,j)
L02581         enddo
L02582         exch_h1d(kts)=0.
L02583  !       exch_h1d(kte+1)=0  
L02584         exch_m1d(kts)=0.
L02585  !       exch_m1d(kte+1)=0
L02586          rhoz1d(kts)=rho1d(kts)
L02587          do k=kts+1,kte
L02588           rhoz1d(k)=(rho1d(k)*dz1d(k-1)+rho1d(k-1)*dz1d(k))/       &
L02589       &                      (dz1d(k-1)+dz1d(k))
L02590          enddo
L02591          rhoz1d(kte+1)=rho1d(kte)
L02592  
L02593  
L02594  ! solve the diffusion for x-component of the wind   
L02595            
L02596         call diff(kms,kme,kts,kte,dt,u1d,rho1d,rhoz1d,exch_m1d,a_u1d,b_u1d,sf1d, &
L02597       &            vl1d,dz1d,wu1d) 
L02598  
L02599  ! solve the diffusion for y-component of the wind              
L02600  
L02601         call diff(kms,kme,kts,kte,dt,v1d,rho1d,rhoz1d,exch_m1d,a_v1d,b_v1d,sf1d, &
L02602       &            vl1d,dz1d,wv1d) 
L02603  
L02604  ! solve the diffusion for equivalent potential temperature
L02605  
L02606         call diff(kms,kme,kts,kte,dt,the1d,rho1d,rhoz1d,exch_h1d,a_t1d,b_t1d,sf1d, &
L02607       &            vl1d,dz1d,wt1d) 
L02608  
L02609  ! solve the diffusion for the water vapor mixing ratio
L02610  
L02611         call diff(kms,kme,kts,kte,dt,qv1d,rho1d,rhoz1d,exch_h1d,a_q1d,b_q1d,sf1d, &
L02612       &            vl1d,dz1d,wq1d) 
L02613  
L02614  ! solve the diffusion for the cloud water mixing ratio
L02615  
L02616         call diff(kms,kme,kts,kte,dt,qc1d,rho1d,rhoz1d,exch_h1d,a_qc1d,b_qc1d,sf1d, &
L02617       &            vl1d,dz1d,wqc1d)        
L02618  
L02619  !     
L02620  ! compute the tendencies
L02621  
L02622          do k=kts,kte
L02623            rublten(i,k,j)=(u1d(k)-u(i,k,j))/dt
L02624            rvblten(i,k,j)=(v1d(k)-v(i,k,j))/dt
L02625            thnew=the1d(k)/(QC(i,k,j)*(-ELOCP/T(i,k,j))+1)
L02626            rthblten(i,k,j)=(thnew-th(i,k,j))/dt
L02627            rqvblten(i,k,j)=(qv1d(k)-qv(i,k,j))/dt
L02628            rqcblten(i,k,j)=(qc1d(k)-qc(i,k,j))/dt
L02629            wu(i,k,j)=wu1d(k)
L02630            wv(i,k,j)=wv1d(k)
L02631            wt(i,k,j)=wt1d(k)
L02632            wq(i,k,j)=wq1d(k)
L02633          enddo
L02634        enddo
L02635        enddo 
L02636  !!!!!!!!!!!!
L02637  
L02638          
L02639        END SUBROUTINE diff3d
```

> 讲解：Martilli 2008 写的通用隐式扩散求解器（为 BEP 设计，driver 层共用）：解 ∂M/∂t=(1/ρ)∂(ρK∂M/∂z)/∂z+AM+B——A/B 是源汇的隐式/显式系数（最低层放地表通量、中层放建筑拖曳），sf/vl 是城市建筑对格点面积/体积的占用比。逐列降维后调 diff 组三对角、invert 解算。

<!-- code_extract code_extract.py v1.2
source: phys/module_pbl_driver.F
ranges: L2642-L2770
file_lines: 2887
file_md5: 1c4ca2a3bd7baa4c31b48527e60a4cad
display: line-numbered (strip L-prefix and !file: line to restore)
range_md5: 7008259882f7c56598fdef0645524967
seg_lines: 129
label: subroutine diff4d
-->

```fortran
!file: phys/module_pbl_driver.F    L2642-L2770    (subroutine diff4d)
L02642            SUBROUTINE diff4d(DT,DZ,SCALAR,IS_SCALAR,RHO              &
L02643                ,EXCH_H,EXCH_M  &  
L02644                ,SCALAR_TEND    &
L02645                ,NUM_SCALAR, PARAM_FIRST_SCALAR     &
L02646                ,IDS,IDE,JDS,JDE,KDS,KDE      &
L02647                ,IMS,IME,JMS,JME,KMS,KME      &
L02648                ,ITS,ITE,JTS,JTE,KTS,KTE      &
L02649                                                                      )
L02650  !!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!
L02651  !    Based on subroutine written by Alberto Martilli, CIEMAT, Spain,
L02652  !    e-mail:alberto_martilli@ciemat.es
L02653  !    August 2008.
L02654  !!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!
L02655  ! ALberto
L02656  ! This routine solves the vertical diffusion 
L02657  ! + other source/sink terms (surface fluxes, building drag, non local terms, etc.)
L02658  ! for U,V, potential temperature and moisture. The equation should be written 
L02659  ! as follow, for a generic variable M:
L02660  ! 
L02661  !      dM      1     d      dM
L02662  !     ---- =----  ---(rho*K----)+AM+B
L02663  !      dt     rho    dz     dz  
L02664  ! where A and B are the implict and explcit coefficients of the source/sink terms
L02665  ! (at the lowest level the surface fluxes should go in these terms)
L02666  !!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!
L02667  !-----------------------------------------------------------------------
L02668        USE module_state_description, ONLY: &
L02669                    P_QNS, P_QNR, P_QNG, P_QT, P_QNH, P_QVOLG, P_QKE_ADV
L02670  
L02671  
L02672        IMPLICIT NONE
L02673  !
L02674  !----------------------------------------------------------------------
L02675        INTEGER,INTENT(IN) :: NUM_SCALAR, PARAM_FIRST_SCALAR
L02676        INTEGER,INTENT(IN) :: IDS,IDE,JDS,JDE,KDS,KDE                    &
L02677       &                     ,IMS,IME,JMS,JME,KMS,KME                    &
L02678       &                     ,ITS,ITE,JTS,JTE,KTS,KTE
L02679  
L02680  ! inputs
L02681        REAL, INTENT(IN)   :: DT
L02682        LOGICAL,INTENT(IN) :: IS_SCALAR
L02683        REAL,DIMENSION(IMS:IME,KMS:KME,JMS:JME),INTENT(IN) :: DZ ! Depth of vertical levels
L02684        REAL,DIMENSION(IMS:IME,KMS:KME,JMS:JME,NUM_SCALAR),INTENT(IN) :: SCALAR ! 4d scalar mixing ratio
L02685        REAL,DIMENSION(IMS:IME,KMS:KME,JMS:JME),INTENT(IN) :: RHO ! Air Density
L02686        REAL,DIMENSION(IMS:IME,KMS:KME,JMS:JME),INTENT(IN) :: EXCH_H ! Turbulent coefficient for heat
L02687        REAL,DIMENSION(IMS:IME,KMS:KME,JMS:JME),INTENT(IN) :: EXCH_M ! Turbulent coefficient for momentum 
L02688        
L02689  ! outputs
L02690        REAL,DIMENSION(IMS:IME,KMS:KME,JMS:JME,NUM_SCALAR),INTENT(INOUT) :: SCALAR_TEND ! 4d scalar mixing ratio tendency
L02691  ! locals (same meaning as above, but 1D)
L02692  
L02693        real s1d(kms:kme),exch_h1d(kms:kme)
L02694        real exch_m1d(kms:kme)
L02695        real dz1d(kms:kme),rho1d(kms:kme),rhoz1d(kms:kme)
L02696        real sf1d(kms:kme),vl1d(kms:kme)   
L02697        real a_s1d(kms:kme),b_s1d(kms:kme)
L02698        real ws1d(kms:kme)
L02699  !
L02700        integer i,k,j,im  
L02701  !----------------------------------------------------------------------
L02702        s1d=0.
L02703        exch_h1d=0.
L02704        exch_m1d=0.
L02705        rho1d=0.
L02706        rhoz1d=0.
L02707        sf1d=0.
L02708        vl1d=0.
L02709        a_s1d=0.
L02710        b_s1d=0.
L02711         
L02712        DO im=PARAM_FIRST_SCALAR,NUM_SCALAR
L02713  ! need to avoid mixing scalars associated with precipitating species (e.g. Nr)
L02714          IF((IS_SCALAR .AND. im.NE.P_QNS .AND. im.NE.P_QNR .AND. im.NE.P_QNG &
L02715            .AND. im.NE.P_QNH .AND. im.NE.P_QT .AND. im.NE.P_QVOLG .AND. im.NE.P_QKE_ADV) &
L02716            .OR. (.not. IS_SCALAR)) THEN
L02717          do j=jts,jte
L02718          do i=its,ite
L02719  
L02720  ! put three D variables in temporary 1D variables
L02721  
L02722         do k=kts,kte
L02723          s1d(k)=SCALAR(i,k,j,im)
L02724          dz1d(k)=dz(i,k,j)
L02725          rho1d(k)=rho(i,k,j) 
L02726  !        a_s1d(k)=a_s(i,k,j)   ! implicit source
L02727  !        b_s1d(k)=b_s(i,k,j)   ! explicit source
L02728          vl1d(k)=1.
L02729          sf1d(k)=1.
L02730         enddo
L02731         sf1d(kte+1)=1. 
L02732         do k=kts,kte    
L02733          exch_h1d(k)=exch_h(i,k,j)
L02734          exch_m1d(k)=exch_m(i,k,j)
L02735         enddo
L02736         exch_h1d(kts)=0.
L02737  !       exch_h1d(kte+1)=0  
L02738         exch_m1d(kts)=0.
L02739  !       exch_m1d(kte+1)=0
L02740          rhoz1d(kts)=rho1d(kts)
L02741          do k=kts+1,kte
L02742           rhoz1d(k)=(rho1d(k)*dz1d(k-1)+rho1d(k-1)*dz1d(k))/       &
L02743       &                      (dz1d(k-1)+dz1d(k))
L02744          enddo
L02745          rhoz1d(kte+1)=rho1d(kte)
L02746  
L02747  
L02748  ! solve the diffusion for scalar
L02749            
L02750         call diff(kms,kme,kts,kte,dt,s1d,rho1d,rhoz1d,exch_h1d,a_s1d,b_s1d,sf1d, &
L02751       &            vl1d,dz1d,ws1d) 
L02752  
L02753  !     
L02754  ! compute the tendencies
L02755  
L02756          do k=kts,kte
L02757            scalar_tend(i,k,j,im)=(s1d(k)-scalar(i,k,j,im))/dt
L02758  !          ws(i,k,j)=ws1d(k)   ! output fluxes
L02759          enddo
L02760          enddo
L02761          enddo 
L02762        ELSE
L02763  !      print *,'scalar skipped im=',im, is_scalar
L02764        ENDIF
L02765        
L02766        ENDDO ! im loop
L02767  !!!!!!!!!!!!
L02768  
L02769          
L02770        END SUBROUTINE diff4d
```

<!-- code_extract code_extract.py v1.2
source: phys/module_pbl_driver.F
ranges: L2774-L2848
file_lines: 2887
file_md5: 1c4ca2a3bd7baa4c31b48527e60a4cad
display: line-numbered (strip L-prefix and !file: line to restore)
range_md5: 26c953eff94c7ef4acd9ea9b832c5dd8
seg_lines: 75
label: subroutine diff
-->

```fortran
!file: phys/module_pbl_driver.F    L2774-L2848    (subroutine diff)
L02774         subroutine diff(kms,kme,kts,kte,dt,co,da,daz,cd,aa,bb,sf,vl,dz,fc)
L02775  
L02776  !------------------------------------------------------------------------
L02777  !           Calculation of the diffusion in 1D
L02778  !------------------------------------------------------------------------
L02779  !  - Input:
L02780  !       nz    : number of points
L02781  !       iz1   : first calculated point
L02782  !       co    : concentration of the variable of interest
L02783  !       dz    : vertical levels
L02784  !       cd    : diffusion coefficients
L02785  !       da    : density of the air at the center
L02786  !       daz   : density of the air at the face
L02787  !       dt    : diffusion time step
L02788  !  - Output:
L02789  !       co :concentration of the variable of interest
L02790  
L02791  !  - Internal:
L02792  !       cddz  : constant terms in the equations
L02793  !---------------------------------------------------------------------
L02794  
L02795          implicit none
L02796          integer iz,iz1,izf
L02797          integer kms,kme,kts,kte
L02798          real dt,dzv
L02799          real co(kms:kme),cd(kms:kme),dz(kms:kme)
L02800          real da(kms:kme),daz(kms:kme)
L02801          real cddz(kms:kme),fc(kms:kme),df(kms:kme)
L02802          real a(kms:kme,3),c(kms:kme)
L02803          real sf(kms:kme),vl(kms:kme)
L02804          real aa(kms:kme),bb(kms:kme)
L02805  
L02806          
L02807  ! Compute cddz=2*cd/dz
L02808  
L02809          cddz(kts)=sf(kts)*daz(kts)*cd(kts)/dz(kts)
L02810          do iz=kts+1,kte
L02811           cddz(iz)=2.*sf(iz)*daz(iz)*cd(iz)/(dz(iz)+dz(iz-1))
L02812          enddo
L02813          cddz(kte+1)=sf(kte+1)*daz(kte+1)*cd(kte+1)/dz(kte)
L02814  
L02815            iz1=1
L02816            izf=1
L02817  
L02818            do iz=iz1,kte-1
L02819  
L02820             dzv=vl(iz)*dz(iz)
L02821             a(iz,1)=-cddz(iz)*dt/dzv/da(iz)
L02822             a(iz,2)=1+dt*(cddz(iz)+cddz(iz+1))/dzv/da(iz)-aa(iz)*dt
L02823             a(iz,3)=-cddz(iz+1)*dt/dzv/da(iz)
L02824             c(iz)=co(iz)+bb(iz)*dt
L02825            enddo
L02826  
L02827            do iz=kte-(izf-1),kte
L02828             a(iz,1)=0.
L02829             a(iz,2)=1
L02830             a(iz,3)=0.
L02831             c(iz)=co(iz)
L02832            enddo
L02833            call invert (kms,kme,kts,kte,a,c,co)
L02834             
L02835  !let compute the fluxes, as diagnostic variable
L02836  
L02837            do iz=kts,iz1
L02838             fc(iz)=0.
L02839            enddo
L02840  
L02841            do iz=iz1+1,kte
L02842             fc(iz)=-(cddz(iz)*(co(iz)-co(iz-1)))/da(iz)
L02843            enddo
L02844  
L02845  
L02846  
L02847         return
L02848         end subroutine diff
```

<!-- code_extract code_extract.py v1.2
source: phys/module_pbl_driver.F
ranges: L2851-L2883
file_lines: 2887
file_md5: 1c4ca2a3bd7baa4c31b48527e60a4cad
display: line-numbered (strip L-prefix and !file: line to restore)
range_md5: c883c6a19f9decd21b6176b0b6eecec2
seg_lines: 33
label: subroutine invert
-->

```fortran
!file: phys/module_pbl_driver.F    L2851-L2883    (subroutine invert)
L02851         subroutine invert(kms,kme,kts,kte,a,c,x)
L02852  
L02853  !ccccccccccccccccccccccccccccccc
L02854  ! Aim: Inversion and resolution of a tridiagonal matrix
L02855  !          A X = C
L02856  ! Input:
L02857  !  a(*,1) lower diagonal (Ai,i-1)
L02858  !  a(*,2) principal diagonal (Ai,i)
L02859  !  a(*,3) upper diagonal (Ai,i+1)
L02860  !  c
L02861  ! Output
L02862  !  x     results
L02863  !ccccccccccccccccccccccccccccccc
L02864  
L02865         implicit none
L02866         integer kms,kme,kts,kte,in
L02867         real a(kms:kme,3),c(kms:kme),x(kms:kme)
L02868  
L02869          do in=kte-1,kts,-1
L02870           c(in)=c(in)-a(in,3)*c(in+1)/a(in+1,2)
L02871           a(in,2)=a(in,2)-a(in,3)*a(in+1,1)/a(in+1,2)
L02872          enddo
L02873  
L02874          do in=kts+1,kte
L02875           c(in)=c(in)-a(in,1)*c(in-1)/a(in-1,2)
L02876          enddo
L02877  
L02878          do in=kts,kte
L02879           x(in)=c(in)/a(in,2)
L02880          enddo
L02881  
L02882          return
L02883          end subroutine invert
```

> 讲解：diff4d 是 diff3d 的标量/示踪物通用版（is_scalar 区分两类池，系数仍是 exch_h/exch_m）。diff 组装三对角矩阵：cddz=2·sf·ρ_face·cd/(dz_iz+dz_iz−1)（面在层间，几何平均厚度），隐式对角占优保证无条件稳定；顶部两层把系数置为单位阵（零通量边界）。invert 是托马斯消元的紧凑实现：自上而下消上对角、自下而上回代。三对角家族在 WRF 物理层至少还有 code_09b 讲过的 mynn tridiag 三兄弟——语义差异（是否破坏输入）是复用时的第一检查点，本 invert 原地破坏 a/c。

## 五、改造入口

1. **新增一个 PBL 方案**（ch20 第一级改造的完整案例）：①Registry：package 行绑定新 bl_pbl_physics 值 + state 清单；②module_state_description 生成方案常量；③本 driver：USE 方案模块 + 新 CASE 分支（照抄 PRESENT 守卫模板）；④方案实体文件（ch20 案例走 MYNN 家族路径）。
2. **改 MYNN 行为**：先读 code_09a/09b——本 driver 的 MYNN 分支只是传参与 SPP 包裹；改 namelist 透传清单时 driver 与 mynnedmf_driver 实参表必须同步。
3. **城市实验组合速查**（论文 2）：BEP/BEM（sf_urban_physics=3）× 边界层 {BouLac=8 / MYJ=2 / KEPS=17（k-ε 全耦合）/ QNSE-ShinHong 部分}；风机实验叠加 windfarm_opt；人为热走 distributed_ahe_opt=1。
4. **增量编译**：只改本文件时直接编译（无需 touch Registry）；新增 namelist 变量则必须（ch04 教训）。

## 六、上下游链接

- 上游：dyn_em/module_first_rk_step_part1.F（编号 31 篇，待交付）在 RK 第一步调用本 driver。
- 下游（方案实体）：MYNN-EDMF → [code_09a_module_bl_mynnedmf.md](code_09a_module_bl_mynnedmf.md) / [code_09b_module_bl_mynnedmf.md](code_09b_module_bl_mynnedmf.md)；面层 MYNN → [code_10_module_sf_mynnsfc.md](code_10_module_sf_mynnsfc.md)；其余方案（YSU/MYJ/BouLac/…）编号 05–08 段待交付。
- 教材正文：[ch14_pbl_family.md](../ch14_pbl_family.md)（方案族总览）、[ch17_urban_canopy.md](../ch17_urban_canopy.md)（BEP 旗标与城市组合）、[ch19_lanzhou_heatwave.md](../ch19_lanzhou_heatwave.md)（namelist 实配）、[ch20_modifying_wrf.md](../ch20_modifying_wrf.md)（新增方案四级步骤）、[ch21_solve_em_dynamics.md](../ch21_solve_em_dynamics.md)（调用时序）。
