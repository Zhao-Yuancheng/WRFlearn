# 文库 code_07b：module_mp_thompson.F 下半——建表族、物理函数族与诊断接口

<!-- 本文件为骨架：CODE 占位符由 workspace/scripts/code_extract.py 注入保真块。
     组装命令：
     D:\Code\miniforge3\envs\WRFlearn\python.exe workspace\scripts\code_extract.py assemble source\WRFv4.8.0\WRFV4.8.0\phys\module_mp_thompson.F workspace\code_library\skel_code_07b.md doc\code\code_07b_module_mp_thompson.md -->

## 07b.0 版本指纹与阅读说明

- **源文件**：`phys/module_mp_thompson.F`（WRF 4.8.0）；本篇覆盖 L4091–L6192——碰撞/冻结/活化**建表族**（10 个）、不完全 Γ 函数族（5 个）、饱和比函数（2 个）、冰核化物理函数（3 个）、辐射与雷达接口（2 个）、Bolton 热力学函数族（5 个），共 27 个子程序/函数。模块声明、`thompson_init`、`mp_gt_driver` 与主实体 `mp_thompson` 见 code_07a。
- **保真承诺**：同 code_07a——所有代码块由 `code_extract.py` 按字节抽取并附 md5 指纹，`verify` 可复核。
- **符号口径**：同 code_07a。
- **阅读方式**：本篇是“工具箱”性质，按需查阅；但 §07b.2 建表族建议顺序读——它们的表结构在 code_07a 主实体的用法里已反复出现。

## 07b.1 建表族：离线算什么、在线省什么

 主实体的速率方程处处是 `∫∫(碰撞截面)·|v差|·m(D)·N(D)dD` 型二重积分。对雨-雪、雨-霰这类**双方都有复杂谱形且相对速度可正可负**的组合，解析积分不存在或误差大——Thompson 的对策是把二重积分在初始化时按谱参数网格**离线积一遍存表**，运行时只查表。本节逐个走读 10 个建表子程序。

### 07b.2.1 `qr_acr_qg`：雨-霰碰撞并合五维表

<!-- code_extract code_extract.py v1.1
source: phys/module_mp_thompson.F
ranges: L4091-L4184
file_lines: 6192
file_md5: f4ec64c511d6656277c4d1f9346813d1
display: line-numbered (strip L-prefix and !file: line to restore)
range_md5: 8fa56b435922803f621d5567530d28dc
seg_lines: 94
-->

```fortran
!file: phys/module_mp_thompson.F    L4091-L4184
L04091        subroutine qr_acr_qg(NRHGtable)
L04092  
L04093        USE module_timing
L04094        implicit none
L04095        
L04096        INTEGER, INTENT(IN) ::NRHGtable
L04097  
L04098  !..Local variables
L04099        INTEGER:: i, j, k, m, n, n2, n3, idx_bg
L04100        INTEGER:: km, km_s, km_e
L04101        DOUBLE PRECISION, DIMENSION(nbg):: N_g
L04102        DOUBLE PRECISION, DIMENSION(nbg,NRHGtable):: vg
L04103        DOUBLE PRECISION, DIMENSION(nbr):: vr, N_r
L04104        DOUBLE PRECISION:: N0_r, N0_g, lam_exp, lamg, lamr
L04105        DOUBLE PRECISION:: massg, massr, dvg, dvr, t1, t2, z1, z2, y1, y2
L04106        LOGICAL force_read_thompson, write_thompson_tables, write_thompson_mp38table
L04107        LOGICAL lexist,lopen
L04108        INTEGER good
L04109        LOGICAL, EXTERNAL :: wrf_dm_on_monitor
L04110        CHARACTER (LEN=20):: qr_acr_qg_name
L04111  !+---+
L04112  
L04113        CALL nl_get_force_read_thompson(1,force_read_thompson)
L04114        CALL nl_get_write_thompson_tables(1,write_thompson_tables)
L04115        CALL nl_get_write_thompson_mp38table(1,write_thompson_mp38table)
L04116  
L04117        if (is_hail_aware) then
L04118           ! Table for mp=38
L04119           ! V1: new table dimension (NRHG), computes all, rho_g(1:NRHG)
L04120           qr_acr_qg_name="qr_acr_qg_mp38V1.dat"
L04121        else
L04122           ! Table for mp=8 or mp=28
L04123           ! V4: new table dimension (NRHG), computes only rho_g(idx_bg1)
L04124           qr_acr_qg_name="qr_acr_qg_V4.dat" 
L04125     endif
L04126  
L04127        good = 0
L04128        IF ( wrf_dm_on_monitor() ) THEN
L04129          INQUIRE(FILE=qr_acr_qg_name,EXIST=lexist)
L04130          IF ( lexist ) THEN
L04131            CALL wrf_message("ThompMP: read "//qr_acr_qg_name//" instead of computing")
L04132            OPEN(63,file=qr_acr_qg_name,form="unformatted",err=1234)
L04133            READ(63,err=1234) tcg_racg
L04134            READ(63,err=1234) tmr_racg
L04135            READ(63,err=1234) tcr_gacr
L04136            !READ(63,err=1234) tmg_gacr
L04137            READ(63,err=1234) tnr_racg
L04138            READ(63,err=1234) tnr_gacr
L04139            good = 1
L04140   1234     CONTINUE
L04141            IF ( good .NE. 1 ) THEN
L04142              INQUIRE(63,opened=lopen)
L04143              IF (lopen) THEN
L04144                IF( force_read_thompson ) THEN
L04145                  CALL wrf_error_fatal("Error reading "//qr_acr_qg_name//". Aborting because force_read_thompson is .true.")
L04146                ENDIF
L04147                CLOSE(63)
L04148              ELSE
L04149                IF( force_read_thompson ) THEN
L04150                  CALL wrf_error_fatal("Error opening "//qr_acr_qg_name//". Aborting because force_read_thompson is .true.")
L04151                ENDIF
L04152              ENDIF
L04153            ELSE
L04154              INQUIRE(63,OPENED=lopen)
L04155              IF (lopen) THEN
L04156                CLOSE(63)
L04157              ENDIF
L04158            ENDIF
L04159          ELSE
L04160            IF( force_read_thompson ) THEN
L04161              CALL wrf_error_fatal("Non-existent "//qr_acr_qg_name//". Aborting because force_read_thompson is .true.")
L04162            ENDIF
L04163            IF( (is_hail_aware) .AND. (.NOT. write_thompson_mp38table)) THEN
L04164              CALL wrf_error_fatal("Non-existent "//qr_acr_qg_name//". Aborting because write_thompson_mp38table is .false.")
L04165            ENDIF
L04166          ENDIF
L04167        ENDIF
L04168  #if defined(DM_PARALLEL) && !defined(STUBMPI)
L04169        CALL wrf_dm_bcast_integer(good,1)
L04170  #endif
L04171  
L04172        IF ( good .EQ. 1 ) THEN
L04173  #if defined(DM_PARALLEL) && !defined(STUBMPI)
L04174          CALL wrf_dm_bcast_double(tcg_racg,SIZE(tcg_racg))
L04175          CALL wrf_dm_bcast_double(tmr_racg,SIZE(tmr_racg))
L04176          CALL wrf_dm_bcast_double(tcr_gacr,SIZE(tcr_gacr))
L04177          !CALL wrf_dm_bcast_double(tmg_gacr,SIZE(tmg_gacr))
L04178          CALL wrf_dm_bcast_double(tnr_racg,SIZE(tnr_racg))
L04179          CALL wrf_dm_bcast_double(tnr_gacr,SIZE(tnr_gacr))
L04180  #endif
L04181        ELSE
L04182          CALL wrf_message("ThompMP: computing qr_acr_qg table: "//qr_acr_qg_name)
L04183  !+---+-----------------------------------------------------------------+
L04184          CALL start_timing
```

> - **namelist 三开关**（`nl_get_*` 是 Registry 生成的 namelist 读取例程，对应 `&physics` 里的 `force_read_thompson`、`write_thompson_tables`、`write_thompson_mp38table`——namelist 全表见教材 ch13 §13.6.4）：`force_read_thompson=.true.` 时表文件缺失/损坏**直接 fatal**（业务运行锁定表版本用）；`write_thompson_tables=.true.` 时算完写盘供下次读。
> - **表文件缓存**：hail-aware 用 `qr_acr_qg_mp38V1.dat`（mp_physics=38，九档密度全算），否则 `qr_acr_qg_V4.dat`（只算 500 kg/m³ 档）。**表名带版本号是刻意的防呆**——谱参数改了而旧表还在，读旧表就是静默错误。
> - **并行建表纪律**：`wrf_dm_on_monitor()` 判定只有 monitor 进程读文件/算表，结果用 `wrf_dm_bcast_*` 广播全体——27 张大表若每进程各算一遍既慢又可能因浮点求和顺序不同而**进程间不一致**。
> - `USE module_timing` 在这里（code_07a §07a.3 说的“藏在子程序内部”的依赖）。

<!-- code_extract code_extract.py v1.1
source: phys/module_mp_thompson.F
ranges: L4185-L4305
file_lines: 6192
file_md5: f4ec64c511d6656277c4d1f9346813d1
display: line-numbered (strip L-prefix and !file: line to restore)
range_md5: 54aa49100de298e150a0fd0ddbe61616
seg_lines: 121
-->

```fortran
!file: phys/module_mp_thompson.F    L4185-L4305
L04185  
L04186          do n2 = 1, nbr
L04187  !        vr(n2) = av_r*Dr(n2)**bv_r * DEXP(-fv_r*Dr(n2))
L04188           vr(n2) = -0.1021 + 4.932E3*Dr(n2) - 0.9551E6*Dr(n2)*Dr(n2)     &
L04189                + 0.07934E9*Dr(n2)*Dr(n2)*Dr(n2)                          &
L04190                - 0.002362E12*Dr(n2)*Dr(n2)*Dr(n2)*Dr(n2)
L04191          enddo
L04192          do n3 = 1, NRHGtable
L04193          do n = 1, nbg
L04194           ! idx_bg indexes module coefficients, not vg
L04195           if (.not. is_hail_aware) idx_bg = idx_bg1
L04196           if (is_hail_aware) idx_bg = n3              
L04197           vg(n,n3) = av_g(idx_bg)*Dg(n)**bv_g(idx_bg)
L04198          enddo
L04199          enddo
L04200  
L04201  !..Note values returned from wrf_dm_decomp1d are zero-based, add 1 for
L04202  !.. fortran indices.  J. Michalakes, 2009Oct30.
L04203  
L04204  #if ( defined( DM_PARALLEL ) && ( ! defined( STUBMPI ) ) )
L04205          CALL wrf_dm_decomp1d ( ntb_r*ntb_r1, km_s, km_e )
L04206  #else
L04207          km_s = 0
L04208          km_e = ntb_r*ntb_r1 - 1
L04209  #endif
L04210  
L04211          do km = km_s, km_e
L04212           m = km / ntb_r1 + 1
L04213           k = mod( km , ntb_r1 ) + 1
L04214  
L04215           lam_exp = (N0r_exp(k)*am_r*crg(1)/r_r(m))**ore1
L04216           lamr = lam_exp * (crg(3)*org2*org1)**obmr
L04217           N0_r = N0r_exp(k)/(crg(2)*lam_exp) * lamr**cre(2)
L04218           do n2 = 1, nbr
L04219              N_r(n2) = N0_r*Dr(n2)**mu_r *DEXP(-lamr*Dr(n2))*dtr(n2)
L04220           enddo
L04221  
L04222           do n3 = 1, NRHGtable
L04223            if (.not. is_hail_aware) idx_bg = idx_bg1
L04224            if (is_hail_aware) idx_bg = n3              
L04225  
L04226           do j = 1, ntb_g
L04227           do i = 1, ntb_g1
L04228              lam_exp = (N0g_exp(i)*am_g(idx_bg)*cgg(1,1)/r_g(j))**oge1
L04229              lamg = lam_exp * (cgg(3,1)*ogg2*ogg1)**obmg
L04230              N0_g = N0g_exp(i)/(cgg(2,1)*lam_exp) * lamg**cge(2,1)
L04231              do n = 1, nbg
L04232                 N_g(n) = N0_g*Dg(n)**mu_g * DEXP(-lamg*Dg(n))*dtg(n)
L04233              enddo
L04234  
L04235              t1 = 0.0d0
L04236              t2 = 0.0d0
L04237              z1 = 0.0d0
L04238              z2 = 0.0d0
L04239              y1 = 0.0d0
L04240              y2 = 0.0d0
L04241              do n2 = 1, nbr
L04242                 massr = am_r * Dr(n2)**bm_r
L04243                 do n = 1, nbg
L04244                    massg = am_g(idx_bg) * Dg(n)**bm_g
L04245  
L04246                    dvg = 0.5d0*((vr(n2) - vg(n,n3)) + DABS(vr(n2)-vg(n,n3)))
L04247                    dvr = 0.5d0*((vg(n,n3) - vr(n2)) + DABS(vg(n,n3)-vr(n2)))
L04248  
L04249                    t1 = t1+ PI*.25*Ef_rg*(Dg(n)+Dr(n2))*(Dg(n)+Dr(n2)) &
L04250                        *dvg*massg * N_g(n)* N_r(n2)
L04251                    z1 = z1+ PI*.25*Ef_rg*(Dg(n)+Dr(n2))*(Dg(n)+Dr(n2)) &
L04252                        *dvg*massr * N_g(n)* N_r(n2)
L04253                    y1 = y1+ PI*.25*Ef_rg*(Dg(n)+Dr(n2))*(Dg(n)+Dr(n2)) &
L04254                        *dvg       * N_g(n)* N_r(n2)
L04255  
L04256                    t2 = t2+ PI*.25*Ef_rg*(Dg(n)+Dr(n2))*(Dg(n)+Dr(n2)) &
L04257                        *dvr*massr * N_g(n)* N_r(n2)
L04258                    y2 = y2+ PI*.25*Ef_rg*(Dg(n)+Dr(n2))*(Dg(n)+Dr(n2)) &
L04259                        *dvr       * N_g(n)* N_r(n2)
L04260                    z2 = z2+ PI*.25*Ef_rg*(Dg(n)+Dr(n2))*(Dg(n)+Dr(n2)) &
L04261                        *dvr*massg * N_g(n)* N_r(n2)
L04262                 enddo
L04263   97            continue
L04264              enddo
L04265              tcg_racg(i,j,n3,k,m) = t1
L04266              tmr_racg(i,j,n3,k,m) = DMIN1(z1, r_r(m)*1.0d0)
L04267              tcr_gacr(i,j,n3,k,m) = t2
L04268              !tmg_gacr(i,j,n3,k,m) = DMIN1(z2, r_g(j)*1.0d0)
L04269              tnr_racg(i,j,n3,k,m) = y1
L04270              tnr_gacr(i,j,n3,k,m) = y2
L04271           enddo
L04272           enddo
L04273           enddo
L04274          enddo
L04275  
L04276  !..Note wrf_dm_gatherv expects zero-based km_s, km_e (J. Michalakes, 2009Oct30).
L04277  
L04278  #if ( defined( DM_PARALLEL ) && ( ! defined( STUBMPI ) ) )
L04279          CALL wrf_dm_gatherv(tcg_racg, ntb_g*ntb_g1*NRHGtable, km_s, km_e, R8SIZE)
L04280          CALL wrf_dm_gatherv(tmr_racg, ntb_g*ntb_g1*NRHGtable, km_s, km_e, R8SIZE)
L04281          CALL wrf_dm_gatherv(tcr_gacr, ntb_g*ntb_g1*NRHGtable, km_s, km_e, R8SIZE)
L04282         !CALL wrf_dm_gatherv(tmg_gacr, ntb_g*ntb_g1*NRHGtable, km_s, km_e, R8SIZE)
L04283          CALL wrf_dm_gatherv(tnr_racg, ntb_g*ntb_g1*NRHGtable, km_s, km_e, R8SIZE)
L04284          CALL wrf_dm_gatherv(tnr_gacr, ntb_g*ntb_g1*NRHGtable, km_s, km_e, R8SIZE)
L04285  #endif
L04286          CALL end_timing ( TRIM("table computation "//qr_acr_qg_name//"") )
L04287  !+---+-----------------------------------------------------------------+
L04288  
L04289  
L04290          IF ( write_thompson_tables .AND. wrf_dm_on_monitor() ) THEN
L04291            CALL wrf_message("Writing "//qr_acr_qg_name//" in Thompson MP init")
L04292            OPEN(63,file=qr_acr_qg_name,form="unformatted",err=9234)
L04293            WRITE(63,err=9234) tcg_racg
L04294            WRITE(63,err=9234) tmr_racg
L04295            WRITE(63,err=9234) tcr_gacr
L04296            !WRITE(63,err=9234) tmg_gacr
L04297            WRITE(63,err=9234) tnr_racg
L04298            WRITE(63,err=9234) tnr_gacr
L04299            CLOSE(63)
L04300            RETURN    ! ----- RETURN
L04301   9234     CONTINUE
L04302            CALL wrf_error_fatal("Error writing "//qr_acr_qg_name//"")
L04303          ENDIF
L04304        ENDIF
L04305  
```

> - **雨落速是四阶多项式**（L4187 起）：`vr = -0.1021 + 4.932e3·D − 0.9551e6·D² + 0.07934e9·D³ − 0.002362e12·D⁴`——**不是**模块常数段的 `av_r·D^bv·exp(-fv·D)` 幂律！建表用更高精度的多项式落速（幂律是大滴端压制近似），被 `!` 掉的幂律行是历史痕迹。同一个文件里两套落速并存，改落速参数时**必须两处同步**——改造陷阱。
> - **方向判定用半绝对值**：`dvg = 0.5·(Δv+|Δv|)`（Δv=vr−vg）取正部、`dvr` 取反部——雨比霰快则雨收霰（dvg>0 计入 t1/z1/y1 组），霰比雨快则霰收雨（dvr>0 计入 t2/z2/y2 组）。**一张表同时存双向碰撞**。
> - **五张表的账目**（L4264–L4269）：`tcg_racg`=霰收雨的霰质量增；`tmr_racg`=雨质量的转移量（**DMIN1 钳位不超雨含量 r_r(m)**——质量账封顶）；`tcr_gacr`=霰收雨时雨的损失；`tnr_racg/tnr_gacr`=数浓度转移（不带质量权重）。主实体 L2526–L2531 把它们组合成 `prg_rcg/prr_rcg/pnr_rcg`。
> - **积分核**：`π/4·(Dg+Dr)²·Δv·m(D)·N(D)`——圆柱碰并截面（直径和为碰撞直径）×相对速度×质量×双方谱密度；`N_g/N_r` 是各 bin 的谱密度（`N0·D^mu·exp(-λD)·dtD`）。
> - `wrf_dm_decomp1d/gatherv` 把 (ntb_r×ntb_r1) 个 (m,k) 组合均分给各进程（Michalakes 2009 注释：**返回值零基**，Fortran 侧加 1——并行改造里最容易踩的索引坑，注释连年份都写了）。

### 07b.2.2 `qr_acr_qs`：雨-雪碰撞四维表（12 张小表）

<!-- code_extract code_extract.py v1.1
source: phys/module_mp_thompson.F
ranges: L4312-L4400
file_lines: 6192
file_md5: f4ec64c511d6656277c4d1f9346813d1
display: line-numbered (strip L-prefix and !file: line to restore)
range_md5: 364a883db852f8b436e1618d8fabe96d
seg_lines: 89
-->

```fortran
!file: phys/module_mp_thompson.F    L4312-L4400
L04312  
L04313        subroutine qr_acr_qs
L04314  
L04315        implicit none
L04316  
L04317  !..Local variables
L04318        INTEGER:: i, j, k, m, n, n2
L04319        INTEGER:: km, km_s, km_e
L04320        DOUBLE PRECISION, DIMENSION(nbr):: vr, D1, N_r
L04321        DOUBLE PRECISION, DIMENSION(nbs):: vs, N_s
L04322        DOUBLE PRECISION:: loga_, a_, b_, second, M0, M2, M3, Mrat, oM3
L04323        DOUBLE PRECISION:: N0_r, lam_exp, lamr, slam1, slam2
L04324        DOUBLE PRECISION:: dvs, dvr, masss, massr
L04325        DOUBLE PRECISION:: t1, t2, t3, t4, z1, z2, z3, z4
L04326        DOUBLE PRECISION:: y1, y2, y3, y4
L04327        LOGICAL force_read_thompson, write_thompson_tables
L04328        LOGICAL lexist,lopen
L04329        INTEGER good
L04330        LOGICAL, EXTERNAL :: wrf_dm_on_monitor
L04331  
L04332  !+---+
L04333  
L04334        CALL nl_get_force_read_thompson(1,force_read_thompson)
L04335        CALL nl_get_write_thompson_tables(1,write_thompson_tables)
L04336  
L04337        good = 0
L04338        IF ( wrf_dm_on_monitor() ) THEN
L04339          INQUIRE(FILE="qr_acr_qsV2.dat",EXIST=lexist)
L04340          IF ( lexist ) THEN
L04341            CALL wrf_message("ThompMP: read qr_acr_qsV2.dat instead of computing")
L04342            OPEN(63,file="qr_acr_qsV2.dat",form="unformatted",err=1234)
L04343            READ(63,err=1234)tcs_racs1
L04344            READ(63,err=1234)tmr_racs1
L04345            READ(63,err=1234)tcs_racs2
L04346            READ(63,err=1234)tmr_racs2
L04347            READ(63,err=1234)tcr_sacr1
L04348            READ(63,err=1234)tms_sacr1
L04349            READ(63,err=1234)tcr_sacr2
L04350            READ(63,err=1234)tms_sacr2
L04351            READ(63,err=1234)tnr_racs1
L04352            READ(63,err=1234)tnr_racs2
L04353            READ(63,err=1234)tnr_sacr1
L04354            READ(63,err=1234)tnr_sacr2
L04355            good = 1
L04356   1234     CONTINUE
L04357            IF ( good .NE. 1 ) THEN
L04358              INQUIRE(63,opened=lopen)
L04359              IF (lopen) THEN
L04360                IF( force_read_thompson ) THEN
L04361                  CALL wrf_error_fatal("Error reading qr_acr_qsV2.dat. Aborting because force_read_thompson is .true.")
L04362                ENDIF
L04363                CLOSE(63)
L04364              ELSE
L04365                IF( force_read_thompson ) THEN
L04366                  CALL wrf_error_fatal("Error opening qr_acr_qsV2.dat. Aborting because force_read_thompson is .true.")
L04367                ENDIF
L04368              ENDIF
L04369            ELSE
L04370              INQUIRE(63,opened=lopen)
L04371              IF (lopen) THEN
L04372                CLOSE(63)
L04373              ENDIF
L04374            ENDIF
L04375          ELSE
L04376            IF( force_read_thompson ) THEN
L04377              CALL wrf_error_fatal("Non-existent qr_acr_qsV2.dat. Aborting because force_read_thompson is .true.")
L04378            ENDIF
L04379          ENDIF
L04380        ENDIF
L04381  #if defined(DM_PARALLEL) && !defined(STUBMPI)
L04382        CALL wrf_dm_bcast_integer(good,1)
L04383  #endif
L04384  
L04385        IF ( good .EQ. 1 ) THEN
L04386  #if defined(DM_PARALLEL) && !defined(STUBMPI)
L04387          CALL wrf_dm_bcast_double(tcs_racs1,SIZE(tcs_racs1))
L04388          CALL wrf_dm_bcast_double(tmr_racs1,SIZE(tmr_racs1))
L04389          CALL wrf_dm_bcast_double(tcs_racs2,SIZE(tcs_racs2))
L04390          CALL wrf_dm_bcast_double(tmr_racs2,SIZE(tmr_racs2))
L04391          CALL wrf_dm_bcast_double(tcr_sacr1,SIZE(tcr_sacr1))
L04392          CALL wrf_dm_bcast_double(tms_sacr1,SIZE(tms_sacr1))
L04393          CALL wrf_dm_bcast_double(tcr_sacr2,SIZE(tcr_sacr2))
L04394          CALL wrf_dm_bcast_double(tms_sacr2,SIZE(tms_sacr2))
L04395          CALL wrf_dm_bcast_double(tnr_racs1,SIZE(tnr_racs1))
L04396          CALL wrf_dm_bcast_double(tnr_racs2,SIZE(tnr_racs2))
L04397          CALL wrf_dm_bcast_double(tnr_sacr1,SIZE(tnr_sacr1))
L04398          CALL wrf_dm_bcast_double(tnr_sacr2,SIZE(tnr_sacr2))
L04399  #endif
L04400        ELSE
```

> 与 `qr_acr_qg` 完全同构的“读缓存→广播→否则计算”框架；表名 `qr_acr_qsV2.dat`。四维 `(雪含量, 温度, 雨截距, 雨含量)`——雪没有数浓度预报量，温度维（`ntb_t=9`，0 到 −40 °C 每 5 度）替代了霰表的截距维。**12 张表 = 12 个“来源×去向”账本**，主实体 L2488–L2508 按湿球温度分叉组合。

<!-- code_extract code_extract.py v1.1
source: phys/module_mp_thompson.F
ranges: L4401-L4590
file_lines: 6192
file_md5: f4ec64c511d6656277c4d1f9346813d1
display: line-numbered (strip L-prefix and !file: line to restore)
range_md5: 2b985a6c0801da4caed491bb8c73b020
seg_lines: 190
-->

```fortran
!file: phys/module_mp_thompson.F    L4401-L4590
L04401          CALL wrf_message("ThompMP: computing qr_acr_qs")
L04402          do n2 = 1, nbr
L04403  !        vr(n2) = av_r*Dr(n2)**bv_r * DEXP(-fv_r*Dr(n2))
L04404           vr(n2) = -0.1021 + 4.932E3*Dr(n2) - 0.9551E6*Dr(n2)*Dr(n2)     &
L04405                + 0.07934E9*Dr(n2)*Dr(n2)*Dr(n2)                          &
L04406                - 0.002362E12*Dr(n2)*Dr(n2)*Dr(n2)*Dr(n2)
L04407           D1(n2) = (vr(n2)/av_s)**(1./bv_s)
L04408          enddo
L04409          do n = 1, nbs
L04410           vs(n) = 1.5*av_s*Ds(n)**bv_s * DEXP(-fv_s*Ds(n))
L04411          enddo
L04412  
L04413  !..Note values returned from wrf_dm_decomp1d are zero-based, add 1 for
L04414  !.. fortran indices.  J. Michalakes, 2009Oct30.
L04415  
L04416  #if ( defined( DM_PARALLEL ) && ( ! defined( STUBMPI ) ) )
L04417          CALL wrf_dm_decomp1d ( ntb_r*ntb_r1, km_s, km_e )
L04418  #else
L04419          km_s = 0
L04420          km_e = ntb_r*ntb_r1 - 1
L04421  #endif
L04422  
L04423          do km = km_s, km_e
L04424           m = km / ntb_r1 + 1
L04425           k = mod( km , ntb_r1 ) + 1
L04426  
L04427           lam_exp = (N0r_exp(k)*am_r*crg(1)/r_r(m))**ore1
L04428           lamr = lam_exp * (crg(3)*org2*org1)**obmr
L04429           N0_r = N0r_exp(k)/(crg(2)*lam_exp) * lamr**cre(2)
L04430           do n2 = 1, nbr
L04431              N_r(n2) = N0_r*Dr(n2)**mu_r * DEXP(-lamr*Dr(n2))*dtr(n2)
L04432           enddo
L04433  
L04434           do j = 1, ntb_t
L04435              do i = 1, ntb_s
L04436  
L04437  !..From the bm_s moment, compute plus one moment.  If we are not
L04438  !.. using bm_s=2, then we must transform to the pure 2nd moment
L04439  !.. (variable called "second") and then to the bm_s+1 moment.
L04440  
L04441                 M2 = r_s(i)*oams *1.0d0
L04442                 if (bm_s.gt.2.0-1.E-3 .and. bm_s.lt.2.0+1.E-3) then
L04443                    loga_ = sa(1) + sa(2)*Tc(j) + sa(3)*bm_s &
L04444                       + sa(4)*Tc(j)*bm_s + sa(5)*Tc(j)*Tc(j) &
L04445                       + sa(6)*bm_s*bm_s + sa(7)*Tc(j)*Tc(j)*bm_s &
L04446                       + sa(8)*Tc(j)*bm_s*bm_s + sa(9)*Tc(j)*Tc(j)*Tc(j) &
L04447                       + sa(10)*bm_s*bm_s*bm_s
L04448                    a_ = 10.0**loga_
L04449                    b_ = sb(1) + sb(2)*Tc(j) + sb(3)*bm_s &
L04450                       + sb(4)*Tc(j)*bm_s + sb(5)*Tc(j)*Tc(j) &
L04451                       + sb(6)*bm_s*bm_s + sb(7)*Tc(j)*Tc(j)*bm_s &
L04452                       + sb(8)*Tc(j)*bm_s*bm_s + sb(9)*Tc(j)*Tc(j)*Tc(j) &
L04453                       + sb(10)*bm_s*bm_s*bm_s
L04454                    second = (M2/a_)**(1./b_)
L04455                 else
L04456                    second = M2
L04457                 endif
L04458  
L04459                 loga_ = sa(1) + sa(2)*Tc(j) + sa(3)*cse(1) &
L04460                    + sa(4)*Tc(j)*cse(1) + sa(5)*Tc(j)*Tc(j) &
L04461                    + sa(6)*cse(1)*cse(1) + sa(7)*Tc(j)*Tc(j)*cse(1) &
L04462                    + sa(8)*Tc(j)*cse(1)*cse(1) + sa(9)*Tc(j)*Tc(j)*Tc(j) &
L04463                    + sa(10)*cse(1)*cse(1)*cse(1)
L04464                 a_ = 10.0**loga_
L04465                 b_ = sb(1)+sb(2)*Tc(j)+sb(3)*cse(1) + sb(4)*Tc(j)*cse(1) &
L04466                    + sb(5)*Tc(j)*Tc(j) + sb(6)*cse(1)*cse(1) &
L04467                    + sb(7)*Tc(j)*Tc(j)*cse(1) + sb(8)*Tc(j)*cse(1)*cse(1) &
L04468                    + sb(9)*Tc(j)*Tc(j)*Tc(j)+sb(10)*cse(1)*cse(1)*cse(1)
L04469                 M3 = a_ * second**b_
L04470  
L04471                 oM3 = 1./M3
L04472                 Mrat = M2*(M2*oM3)*(M2*oM3)*(M2*oM3)
L04473                 M0   = (M2*oM3)**mu_s
L04474                 slam1 = M2 * oM3 * Lam0
L04475                 slam2 = M2 * oM3 * Lam1
L04476  
L04477                 do n = 1, nbs
L04478                    N_s(n) = Mrat*(Kap0*DEXP(-slam1*Ds(n)) &
L04479                        + Kap1*M0*Ds(n)**mu_s * DEXP(-slam2*Ds(n)))*dts(n)
L04480                 enddo
L04481  
L04482                 t1 = 0.0d0
L04483                 t2 = 0.0d0
L04484                 t3 = 0.0d0
L04485                 t4 = 0.0d0
L04486                 z1 = 0.0d0
L04487                 z2 = 0.0d0
L04488                 z3 = 0.0d0
L04489                 z4 = 0.0d0
L04490                 y1 = 0.0d0
L04491                 y2 = 0.0d0
L04492                 y3 = 0.0d0
L04493                 y4 = 0.0d0
L04494                 do n2 = 1, nbr
L04495                    massr = am_r * Dr(n2)**bm_r
L04496                    do n = 1, nbs
L04497                       masss = am_s * Ds(n)**bm_s
L04498        
L04499                       dvs = 0.5d0*((vr(n2) - vs(n)) + DABS(vr(n2)-vs(n)))
L04500                       dvr = 0.5d0*((vs(n) - vr(n2)) + DABS(vs(n)-vr(n2)))
L04501  
L04502                       if (massr .gt. 1.5*masss) then
L04503                       t1 = t1+ PI*.25*Ef_rs*(Ds(n)+Dr(n2))*(Ds(n)+Dr(n2)) &
L04504                           *dvs*masss * N_s(n)* N_r(n2)
L04505                       z1 = z1+ PI*.25*Ef_rs*(Ds(n)+Dr(n2))*(Ds(n)+Dr(n2)) &
L04506                           *dvs*massr * N_s(n)* N_r(n2)
L04507                       y1 = y1+ PI*.25*Ef_rs*(Ds(n)+Dr(n2))*(Ds(n)+Dr(n2)) &
L04508                           *dvs       * N_s(n)* N_r(n2)
L04509                       else
L04510                       t3 = t3+ PI*.25*Ef_rs*(Ds(n)+Dr(n2))*(Ds(n)+Dr(n2)) &
L04511                           *dvs*masss * N_s(n)* N_r(n2)
L04512                       z3 = z3+ PI*.25*Ef_rs*(Ds(n)+Dr(n2))*(Ds(n)+Dr(n2)) &
L04513                           *dvs*massr * N_s(n)* N_r(n2)
L04514                       y3 = y3+ PI*.25*Ef_rs*(Ds(n)+Dr(n2))*(Ds(n)+Dr(n2)) &
L04515                           *dvs       * N_s(n)* N_r(n2)
L04516                       endif
L04517  
L04518                       if (massr .gt. 1.5*masss) then
L04519                       t2 = t2+ PI*.25*Ef_rs*(Ds(n)+Dr(n2))*(Ds(n)+Dr(n2)) &
L04520                           *dvr*massr * N_s(n)* N_r(n2)
L04521                       y2 = y2+ PI*.25*Ef_rs*(Ds(n)+Dr(n2))*(Ds(n)+Dr(n2)) &
L04522                           *dvr       * N_s(n)* N_r(n2)
L04523                       z2 = z2+ PI*.25*Ef_rs*(Ds(n)+Dr(n2))*(Ds(n)+Dr(n2)) &
L04524                           *dvr*masss * N_s(n)* N_r(n2)
L04525                       else
L04526                       t4 = t4+ PI*.25*Ef_rs*(Ds(n)+Dr(n2))*(Ds(n)+Dr(n2)) &
L04527                           *dvr*massr * N_s(n)* N_r(n2)
L04528                       y4 = y4+ PI*.25*Ef_rs*(Ds(n)+Dr(n2))*(Ds(n)+Dr(n2)) &
L04529                           *dvr       * N_s(n)* N_r(n2)
L04530                       z4 = z4+ PI*.25*Ef_rs*(Ds(n)+Dr(n2))*(Ds(n)+Dr(n2)) &
L04531                           *dvr*masss * N_s(n)* N_r(n2)
L04532                       endif
L04533  
L04534                    enddo
L04535                 enddo
L04536                 tcs_racs1(i,j,k,m) = t1
L04537                 tmr_racs1(i,j,k,m) = DMIN1(z1, r_r(m)*1.0d0)
L04538                 tcs_racs2(i,j,k,m) = t3
L04539                 tmr_racs2(i,j,k,m) = z3
L04540                 tcr_sacr1(i,j,k,m) = t2
L04541                 tms_sacr1(i,j,k,m) = z2
L04542                 tcr_sacr2(i,j,k,m) = t4
L04543                 tms_sacr2(i,j,k,m) = z4
L04544                 tnr_racs1(i,j,k,m) = y1
L04545                 tnr_racs2(i,j,k,m) = y3
L04546                 tnr_sacr1(i,j,k,m) = y2
L04547                 tnr_sacr2(i,j,k,m) = y4
L04548              enddo
L04549           enddo
L04550          enddo
L04551  
L04552  !..Note wrf_dm_gatherv expects zero-based km_s, km_e (J. Michalakes, 2009Oct30).
L04553  
L04554  #if ( defined( DM_PARALLEL ) && ( ! defined( STUBMPI ) ) )
L04555          CALL wrf_dm_gatherv(tcs_racs1, ntb_s*ntb_t, km_s, km_e, R8SIZE)
L04556          CALL wrf_dm_gatherv(tmr_racs1, ntb_s*ntb_t, km_s, km_e, R8SIZE)
L04557          CALL wrf_dm_gatherv(tcs_racs2, ntb_s*ntb_t, km_s, km_e, R8SIZE)
L04558          CALL wrf_dm_gatherv(tmr_racs2, ntb_s*ntb_t, km_s, km_e, R8SIZE)
L04559          CALL wrf_dm_gatherv(tcr_sacr1, ntb_s*ntb_t, km_s, km_e, R8SIZE)
L04560          CALL wrf_dm_gatherv(tms_sacr1, ntb_s*ntb_t, km_s, km_e, R8SIZE)
L04561          CALL wrf_dm_gatherv(tcr_sacr2, ntb_s*ntb_t, km_s, km_e, R8SIZE)
L04562          CALL wrf_dm_gatherv(tms_sacr2, ntb_s*ntb_t, km_s, km_e, R8SIZE)
L04563          CALL wrf_dm_gatherv(tnr_racs1, ntb_s*ntb_t, km_s, km_e, R8SIZE)
L04564          CALL wrf_dm_gatherv(tnr_racs2, ntb_s*ntb_t, km_s, km_e, R8SIZE)
L04565          CALL wrf_dm_gatherv(tnr_sacr1, ntb_s*ntb_t, km_s, km_e, R8SIZE)
L04566          CALL wrf_dm_gatherv(tnr_sacr2, ntb_s*ntb_t, km_s, km_e, R8SIZE)
L04567  #endif
L04568  
L04569          IF ( write_thompson_tables .AND. wrf_dm_on_monitor() ) THEN
L04570            CALL wrf_message("Writing qr_acr_qsV2.dat in Thompson MP init")
L04571            OPEN(63,file="qr_acr_qsV2.dat",form="unformatted",err=9234)
L04572            WRITE(63,err=9234)tcs_racs1
L04573            WRITE(63,err=9234)tmr_racs1
L04574            WRITE(63,err=9234)tcs_racs2
L04575            WRITE(63,err=9234)tmr_racs2
L04576            WRITE(63,err=9234)tcr_sacr1
L04577            WRITE(63,err=9234)tms_sacr1
L04578            WRITE(63,err=9234)tcr_sacr2
L04579            WRITE(63,err=9234)tms_sacr2
L04580            WRITE(63,err=9234)tnr_racs1
L04581            WRITE(63,err=9234)tnr_racs2
L04582            WRITE(63,err=9234)tnr_sacr1
L04583            WRITE(63,err=9234)tnr_sacr2
L04584            CLOSE(63)
L04585            RETURN    ! ----- RETURN
L04586   9234     CONTINUE
L04587            CALL wrf_error_fatal("Error writing qr_acr_qsV2.dat")
L04588          ENDIF
L04589        ENDIF
L04590  
```

> - **质量分界 1.5**（L4501/L4517）：`massr > 1.5·masss` 时雨是收集者（t1/z1/y1 组存 `*racs1`），否则雪是收集者（t3/z3/y3 组存 `*racs2`）——**谁大谁收**的物理直觉直接编码为表的分列存储。
> - **雪落速乘 1.5**（L4409）：`vs = 1.5·av_s·D^bv·exp(−fv·D)`——**源码无注释解释**。可对照的线索：主实体沉降用的雪落速是矩量积分（无此系数），此处 1.5 只影响碰撞方向判定。读代码读到这种“裸经验系数”时，文库的态度是标注出来而非硬解释——改造者若动雪落速，此处是否跟随是必须自查的问题。
> - **雪谱再入**（L4440–L4478）：由雪含量先换算第 2 矩 `M2 = rs·oams`，经 `sa/sb` 多项式得到 `M3`（bm_s+1 矩），再出 `Mrat/M0/slam1/slam2`——与 Field 双伽马谱的完整重建；bin 密度 `N_s(n)` 按双伽马两项直接求和。**这是 Field 谱“离线积分”的样板**：运行时不可承受的双谱二重积分，在此以四维网格预积。
> - 小瑕疵：`D1` 数组（L4319/L4406）赋值后从未使用——死代码，读时不必纠结。

### 07b.2.3 `freezeH2O`：Bigg 冻结表与尘埃订正

<!-- code_extract code_extract.py v1.1
source: phys/module_mp_thompson.F
ranges: L4599-L4676
file_lines: 6192
file_md5: f4ec64c511d6656277c4d1f9346813d1
display: line-numbered (strip L-prefix and !file: line to restore)
range_md5: 52f56b55d45c6efcd2940ff3bd4c8bf6
seg_lines: 78
-->

```fortran
!file: phys/module_mp_thompson.F    L4599-L4676
L04599  
L04600        subroutine freezeH2O
L04601  
L04602        implicit none
L04603  
L04604  !..Local variables
L04605        INTEGER:: i, j, k, m, n, n2
L04606        INTEGER:: km, km_s, km_e
L04607        DOUBLE PRECISION:: N_r, N_c
L04608        DOUBLE PRECISION, DIMENSION(nbr):: massr
L04609        DOUBLE PRECISION, DIMENSION(nbc):: massc
L04610        DOUBLE PRECISION:: sum1, sum2, sumn1, sumn2, &
L04611                           prob, vol, Texp, orho_w, &
L04612                           lam_exp, lamr, N0_r, lamc, N0_c, y
L04613        INTEGER:: nu_c
L04614        REAL:: T_adjust
L04615        LOGICAL force_read_thompson, write_thompson_tables
L04616        LOGICAL lexist,lopen
L04617        INTEGER good
L04618        LOGICAL, EXTERNAL :: wrf_dm_on_monitor
L04619  
L04620  !+---+
L04621        CALL nl_get_force_read_thompson(1,force_read_thompson)
L04622        CALL nl_get_write_thompson_tables(1,write_thompson_tables)
L04623  
L04624        good = 0
L04625        IF ( wrf_dm_on_monitor() ) THEN
L04626          INQUIRE(FILE="freezeH2O.dat",EXIST=lexist)
L04627          IF ( lexist ) THEN
L04628            CALL wrf_message("ThompMP: read freezeH2O.dat instead of computing")
L04629            OPEN(63,file="freezeH2O.dat",form="unformatted",err=1234)
L04630            READ(63,err=1234)tpi_qrfz
L04631            READ(63,err=1234)tni_qrfz
L04632            READ(63,err=1234)tpg_qrfz
L04633            READ(63,err=1234)tnr_qrfz
L04634            READ(63,err=1234)tpi_qcfz
L04635            READ(63,err=1234)tni_qcfz
L04636            good = 1
L04637   1234     CONTINUE
L04638            IF ( good .NE. 1 ) THEN
L04639              INQUIRE(63,opened=lopen)
L04640              IF (lopen) THEN
L04641                IF( force_read_thompson ) THEN
L04642                  CALL wrf_error_fatal("Error reading freezeH2O.dat. Aborting because force_read_thompson is .true.")
L04643                ENDIF
L04644                CLOSE(63)
L04645              ELSE
L04646                IF( force_read_thompson ) THEN
L04647                  CALL wrf_error_fatal("Error opening freezeH2O.dat. Aborting because force_read_thompson is .true.")
L04648                ENDIF
L04649              ENDIF
L04650            ELSE
L04651              INQUIRE(63,opened=lopen)
L04652              IF (lopen) THEN
L04653                CLOSE(63)
L04654              ENDIF
L04655            ENDIF
L04656          ELSE
L04657            IF( force_read_thompson ) THEN
L04658              CALL wrf_error_fatal("Non-existent freezeH2O.dat. Aborting because force_read_thompson is .true.")
L04659            ENDIF
L04660          ENDIF
L04661        ENDIF
L04662  
L04663  #if defined(DM_PARALLEL) && !defined(STUBMPI)
L04664        CALL wrf_dm_bcast_integer(good,1)
L04665  #endif
L04666  
L04667        IF ( good .EQ. 1 ) THEN
L04668  #if defined(DM_PARALLEL) && !defined(STUBMPI)
L04669          CALL wrf_dm_bcast_double(tpi_qrfz,SIZE(tpi_qrfz))
L04670          CALL wrf_dm_bcast_double(tni_qrfz,SIZE(tni_qrfz))
L04671          CALL wrf_dm_bcast_double(tpg_qrfz,SIZE(tpg_qrfz))
L04672          CALL wrf_dm_bcast_double(tnr_qrfz,SIZE(tnr_qrfz))
L04673          CALL wrf_dm_bcast_double(tpi_qcfz,SIZE(tpi_qcfz))
L04674          CALL wrf_dm_bcast_double(tni_qcfz,SIZE(tni_qcfz))
L04675  #endif
L04676        ELSE
```

> 缓存文件 `freezeH2O.dat`，六张表：雨冻结的 `tpi/tni_qrfz`（→冰晶）、`tpg/tnr_qrfz`（→霰）与云滴冻结的 `tpi/tni_qcfz`。四维 `(含量, 截距, 温度, IN 浓度)`——**第四维就是尘埃**。

<!-- code_extract code_extract.py v1.1
source: phys/module_mp_thompson.F
ranges: L4677-L4791
file_lines: 6192
file_md5: f4ec64c511d6656277c4d1f9346813d1
display: line-numbered (strip L-prefix and !file: line to restore)
range_md5: cb9369aea3db37b263137cef98704172
seg_lines: 115
-->

```fortran
!file: phys/module_mp_thompson.F    L4677-L4791
L04677          CALL wrf_message("ThompMP: computing freezeH2O")
L04678  
L04679          orho_w = 1./rho_w
L04680  
L04681          do n2 = 1, nbr
L04682           massr(n2) = am_r*Dr(n2)**bm_r
L04683          enddo
L04684          do n = 1, nbc
L04685           massc(n) = am_r*Dc(n)**bm_r
L04686          enddo
L04687  
L04688  ! Need to split loops between MPI processes to speedup
L04689  ! (2017Jul26, Jason Do)
L04690  #if ( defined( DM_PARALLEL ) && ( ! defined( STUBMPI ) ) )
L04691          CALL wrf_dm_decomp1d ( ntb_IN*45, km_s, km_e )
L04692  #else
L04693          km_s = 0
L04694          km_e = ntb_IN*45 - 1
L04695  #endif
L04696  
L04697  !..Freeze water (smallest drops become cloud ice, otherwise graupel).
L04698          do km = km_s, km_e
L04699           m = km / 45 + 1
L04700           k = mod( km , 45 ) + 1
L04701           T_adjust = MAX(-3.0, MIN(3.0 - ALOG10(Nt_IN(m)), 3.0))
L04702  !         print*, ' Freezing water for temp = ', -k
L04703           Texp = DEXP( DFLOAT(k) - T_adjust*1.0D0 ) - 1.0D0
L04704  #ifdef THOMPSON_OMP
L04705  !$OMP PARALLEL DO SCHEDULE(dynamic) &
L04706  !$OMP PRIVATE(j,i,lam_exp,lamr,N0_r,sum1,sum2,sumn1,sumn2,n2,N_r,vol,prob)
L04707  #endif
L04708           do j = 1, ntb_r1
L04709              do i = 1, ntb_r
L04710                 lam_exp = (N0r_exp(j)*am_r*crg(1)/r_r(i))**ore1
L04711                 lamr = lam_exp * (crg(3)*org2*org1)**obmr
L04712                 N0_r = N0r_exp(j)/(crg(2)*lam_exp) * lamr**cre(2)
L04713                 sum1 = 0.0d0
L04714                 sum2 = 0.0d0
L04715                 sumn1 = 0.0d0
L04716                 sumn2 = 0.0d0
L04717                 do n2 = nbr, 1, -1
L04718                    N_r = N0_r*Dr(n2)**mu_r*DEXP(-lamr*Dr(n2))*dtr(n2)
L04719                    vol = massr(n2)*orho_w
L04720                    prob = MAX(0.0D0, 1.0D0 - DEXP(-120.0D0*vol*5.2D-4 * Texp))
L04721                    if (massr(n2) .lt. xm0g) then
L04722                       sumn1 = sumn1 + prob*N_r
L04723                       sum1 = sum1 + prob*N_r*massr(n2)
L04724                    else
L04725                       sumn2 = sumn2 + prob*N_r
L04726                       sum2 = sum2 + prob*N_r*massr(n2)
L04727                    endif
L04728                    if ((sum1+sum2).ge.r_r(i)) EXIT
L04729                 enddo
L04730                 tpi_qrfz(i,j,k,m) = sum1
L04731                 tni_qrfz(i,j,k,m) = sumn1
L04732                 tpg_qrfz(i,j,k,m) = sum2
L04733                 tnr_qrfz(i,j,k,m) = sumn2
L04734              enddo
L04735           enddo
L04736  #ifdef THOMPSON_OMP
L04737  !$OMP END PARALLEL DO
L04738  
L04739  !$OMP PARALLEL DO SCHEDULE(dynamic) &
L04740  !$OMP PRIVATE(j,i,nu_c,lamc,N0_c,sum1,sumn2,vol,prob,N_c)
L04741  #endif
L04742           do j = 1, nbc
L04743              nu_c = MIN(15, NINT(1000.E6/t_Nc(j)) + 2)
L04744              do i = 1, ntb_c
L04745                 lamc = (t_Nc(j)*am_r* ccg(2,nu_c) * ocg1(nu_c) / r_c(i))**obmr
L04746                 N0_c = t_Nc(j)*ocg1(nu_c) * lamc**cce(1,nu_c)
L04747                 sum1 = 0.0d0
L04748                 sumn2 = 0.0d0
L04749                 do n = nbc, 1, -1
L04750                    vol = massc(n)*orho_w
L04751                    prob = MAX(0.0D0, 1.0D0 - DEXP(-120.0D0*vol*5.2D-4 * Texp))
L04752                    N_c = N0_c*Dc(n)**nu_c*EXP(-lamc*Dc(n))*dtc(n)
L04753                    sumn2 = MIN(t_Nc(j), sumn2 + prob*N_c)
L04754                    sum1 = sum1 + prob*N_c*massc(n)
L04755                    if (sum1 .ge. r_c(i)) EXIT
L04756                 enddo
L04757                 tpi_qcfz(i,j,k,m) = sum1
L04758                 tni_qcfz(i,j,k,m) = sumn2
L04759              enddo
L04760           enddo
L04761  #ifdef THOMPSON_OMP
L04762  !$OMP END PARALLEL DO
L04763  #endif
L04764          enddo
L04765  
L04766  #if ( defined( DM_PARALLEL ) && ( ! defined( STUBMPI ) ) )
L04767          CALL wrf_dm_gatherv(tpi_qrfz, ntb_r*ntb_r1, km_s, km_e, R8SIZE)
L04768          CALL wrf_dm_gatherv(tni_qrfz, ntb_r*ntb_r1, km_s, km_e, R8SIZE)
L04769          CALL wrf_dm_gatherv(tpg_qrfz, ntb_r*ntb_r1, km_s, km_e, R8SIZE)
L04770          CALL wrf_dm_gatherv(tnr_qrfz, ntb_r*ntb_r1, km_s, km_e, R8SIZE)
L04771          CALL wrf_dm_gatherv(tpi_qcfz, ntb_c*nbc, km_s, km_e, R8SIZE)
L04772          CALL wrf_dm_gatherv(tni_qcfz, ntb_c*nbc, km_s, km_e, R8SIZE)
L04773  #endif
L04774  
L04775          IF ( write_thompson_tables .AND. wrf_dm_on_monitor() ) THEN
L04776            CALL wrf_message("Writing freezeH2O.dat in Thompson MP init")
L04777            OPEN(63,file="freezeH2O.dat",form="unformatted",err=9234)
L04778            WRITE(63,err=9234)tpi_qrfz
L04779            WRITE(63,err=9234)tni_qrfz
L04780            WRITE(63,err=9234)tpg_qrfz
L04781            WRITE(63,err=9234)tnr_qrfz
L04782            WRITE(63,err=9234)tpi_qcfz
L04783            WRITE(63,err=9234)tni_qcfz
L04784            CLOSE(63)
L04785            RETURN    ! ----- RETURN
L04786   9234     CONTINUE
L04787            CALL wrf_error_fatal("Error writing freezeH2O.dat")
L04788          ENDIF
L04789        ENDIF
L04790  
L04791        end subroutine freezeH2O
```

> - **Bigg (1954) 冻结概率**（L4720）：`prob = 1 − exp(−120·vol·5.2e-4·Texp)`——`vol` 是水滴体积（m³），`5.2e-4` 与 `120` 合起来是 Bigg 单位体积冻结率 J(T) 的离散化（J 随过冷度指数上升）；`Texp = exp(k − T_adjust) − 1`，`k` 是过冷度（1 度步进，1–45 K）。**从大滴往小滴积分**（`do n2 = nbr, 1, -1`）并在累计冻结量达到含量时 `EXIT`——概率虽小但含量账封顶。
> - **尘埃订正 `T_adjust`**（L4701）：`T_adjust = clamp(3 − log10(Nt_IN), −3, 3)`——IN 浓度 1/L 时 T_adjust=3（冻结温度等效上移 3 K），IN 越少订正越负（冻结推迟，最多 3 K）。**`dustyIce` 的全部机制就在这一行**：冰核浓度通过“等效过冷度”调节冻结概率，主实体按 `(含量,截距,温度,IN)` 四维索引查表。
> - **冻结产物分流**（L4721–L4727）：雨滴质量 < `xm0g`（霰出生质量）的冻结成**冰晶**（sum1/sumn1），≥ 的直接成**霰**（sum2/sumn2）——冻结的产物归属由粒子尺寸决定，与主实体 `pri_rfz/prg_rfz` 的分账对应。
> - **OpenMP**（`THOMPSON_OMP` 宏，Jason Do 2017 注释）：两个内层 j 循环并行——建表是初始化期的大计算量，能并行则并行。

### 07b.2.4 `qi_aut_qs`：冰晶→雪自动转化表

<!-- code_extract code_extract.py v1.1
source: phys/module_mp_thompson.F
ranges: L4806-L4849
file_lines: 6192
file_md5: f4ec64c511d6656277c4d1f9346813d1
display: line-numbered (strip L-prefix and !file: line to restore)
range_md5: 4ff2689e57218f6a11fb6d9443f936bd
seg_lines: 44
-->

```fortran
!file: phys/module_mp_thompson.F    L4806-L4849
L04806        subroutine qi_aut_qs
L04807  
L04808        implicit none
L04809  
L04810  !..Local variables
L04811        INTEGER:: i, j, n2
L04812        DOUBLE PRECISION, DIMENSION(nbi):: N_i
L04813        DOUBLE PRECISION:: N0_i, lami, Di_mean, t1, t2
L04814        REAL:: xlimit_intg
L04815  
L04816  !+---+
L04817  
L04818        do j = 1, ntb_i1
L04819           do i = 1, ntb_i
L04820              lami = (am_i*cig(2)*oig1*Nt_i(j)/r_i(i))**obmi
L04821              Di_mean = (bm_i + mu_i + 1.) / lami
L04822              N0_i = Nt_i(j)*oig1 * lami**cie(1)
L04823              t1 = 0.0d0
L04824              t2 = 0.0d0
L04825              if (SNGL(Di_mean) .gt. 5.*D0s) then
L04826               t1 = r_i(i)
L04827               t2 = Nt_i(j)
L04828               tpi_ide(i,j) = 0.0D0
L04829              elseif (SNGL(Di_mean) .lt. D0i) then
L04830               t1 = 0.0D0
L04831               t2 = 0.0D0
L04832               tpi_ide(i,j) = 1.0D0
L04833              else
L04834               xlimit_intg = lami*D0s
L04835               tpi_ide(i,j) = GAMMP(mu_i+2.0, xlimit_intg) * 1.0D0
L04836               do n2 = 1, nbi
L04837                 N_i(n2) = N0_i*Di(n2)**mu_i * DEXP(-lami*Di(n2))*dti(n2)
L04838                 if (Di(n2).ge.D0s) then
L04839                    t1 = t1 + N_i(n2) * am_i*Di(n2)**bm_i
L04840                    t2 = t2 + N_i(n2)
L04841                 endif
L04842               enddo
L04843              endif
L04844              tps_iaus(i,j) = t1
L04845              tni_iaus(i,j) = t2
L04846           enddo
L04847        enddo
L04848  
L04849        end subroutine qi_aut_qs
```

> - **判定逻辑**：把冰晶谱按 bin 离散，直径 ≥ `D0s`（300 μm）的部分质量/数量计入转雪表 `tps_iaus/tni_iaus`——**自动转化在这里不是经验阈值公式，而是“谱尾积分”**。
> - **不完全 Γ 函数出马**（L4835）：`tpi_ide = GAMMP(mu_i+2, lami·D0s)`——直径小于 D0s 的冰晶占谱的份额（对谱密度 N0·D^mu·exp(−λD) 从 0 积到 D0s，换元后恰是不完全 Γ 函数 P(a,x)）。主实体用它把冰晶凝华增长**分账**：小粒径端留冰晶、大粒径端归雪（Harrington et al. 1995 思想，模块头注释写明）。Γ 函数族在 §07b.3。
> - 两端特判：平均径 > 5×D0s 全转雪（`tpi_ide=0`），< D0i 全不转（`tpi_ide=1`）。

### 07b.2.5 `table_Efrw` / `table_Efsw`：碰并效率表

<!-- code_extract code_extract.py v1.1
source: phys/module_mp_thompson.F
ranges: L4857-L4913
file_lines: 6192
file_md5: f4ec64c511d6656277c4d1f9346813d1
display: line-numbered (strip L-prefix and !file: line to restore)
range_md5: 2f7a32a1547745c54ccad649a02ae063
seg_lines: 57
-->

```fortran
!file: phys/module_mp_thompson.F    L4857-L4913
L04857        subroutine table_Efrw
L04858  
L04859        implicit none
L04860  
L04861  !..Local variables
L04862        DOUBLE PRECISION:: vtr, stokes, reynolds, Ef_rw
L04863        DOUBLE PRECISION:: p, yc0, F, G, H, z, K0, X
L04864        INTEGER:: i, j
L04865  
L04866        do j = 1, nbc
L04867        do i = 1, nbr
L04868           Ef_rw = 0.0
L04869           p = Dc(j)/Dr(i)
L04870           if (Dr(i).lt.50.E-6 .or. Dc(j).lt.3.E-6) then
L04871            t_Efrw(i,j) = 0.0
L04872           elseif (p.gt.0.25) then
L04873            X = Dc(j)*1.D6
L04874            if (Dr(i) .lt. 75.e-6) then
L04875               Ef_rw = 0.026794*X - 0.20604
L04876            elseif (Dr(i) .lt. 125.e-6) then
L04877               Ef_rw = -0.00066842*X*X + 0.061542*X - 0.37089
L04878            elseif (Dr(i) .lt. 175.e-6) then
L04879               Ef_rw = 4.091e-06*X*X*X*X - 0.00030908*X*X*X               &
L04880                     + 0.0066237*X*X - 0.0013687*X - 0.073022
L04881            elseif (Dr(i) .lt. 250.e-6) then
L04882               Ef_rw = 9.6719e-5*X*X*X - 0.0068901*X*X + 0.17305*X        &
L04883                     - 0.65988
L04884            elseif (Dr(i) .lt. 350.e-6) then
L04885               Ef_rw = 9.0488e-5*X*X*X - 0.006585*X*X + 0.16606*X         &
L04886                     - 0.56125
L04887            else
L04888               Ef_rw = 0.00010721*X*X*X - 0.0072962*X*X + 0.1704*X        &
L04889                     - 0.46929
L04890            endif
L04891           else
L04892            vtr = -0.1021 + 4.932E3*Dr(i) - 0.9551E6*Dr(i)*Dr(i) &
L04893                + 0.07934E9*Dr(i)*Dr(i)*Dr(i) &
L04894                - 0.002362E12*Dr(i)*Dr(i)*Dr(i)*Dr(i)
L04895            stokes = Dc(j)*Dc(j)*vtr*rho_w/(9.*1.718E-5*Dr(i))
L04896            reynolds = 9.*stokes/(p*p*rho_w)
L04897  
L04898            F = DLOG(reynolds)
L04899            G = -0.1007D0 - 0.358D0*F + 0.0261D0*F*F
L04900            K0 = DEXP(G)
L04901            z = DLOG(stokes/(K0+1.D-15))
L04902            H = 0.1465D0 + 1.302D0*z - 0.607D0*z*z + 0.293D0*z*z*z
L04903            yc0 = 2.0D0/PI * ATAN(H)
L04904            Ef_rw = (yc0+p)*(yc0+p) / ((1.+p)*(1.+p))
L04905  
L04906           endif
L04907  
L04908           t_Efrw(i,j) = MAX(0.0, MIN(SNGL(Ef_rw), 0.95))
L04909  
L04910        enddo
L04911        enddo
L04912  
L04913        end subroutine table_Efrw
```

> - **两段式物理**：①小滴比 `p = Dc/Dr < 0.25` 走 **Beard & Grover (1974) 半解析式**——Stokes 数与 Reynolds 数算出后经 `G/K0/z/H/yc0` 四步拟合成 `yc0 = 2/π·atan(H)`，效率 `(yc0+p)²/(1+p)²`（Langmuir 流场小滴轨迹积分的标准拟合）；②大滴比走 **Pruppacher & Klett 图 14-9 的六段多项式**（按雨径分 50–75–125–175–250–350 μm+ 六段，每段是云滴径 X 的二/三/四次式）——**理论式与实验拟合拼接**是碰撞效率建模的常态。
> - 端点零效率：雨径 < 50 μm 或云滴 < 3 μm；上限钳 0.95。

<!-- code_extract code_extract.py v1.1
source: phys/module_mp_thompson.F
ranges: L4921-L4957
file_lines: 6192
file_md5: f4ec64c511d6656277c4d1f9346813d1
display: line-numbered (strip L-prefix and !file: line to restore)
range_md5: f6e03f62f7e4187fb016a539b54d920d
seg_lines: 37
-->

```fortran
!file: phys/module_mp_thompson.F    L4921-L4957
L04921        subroutine table_Efsw
L04922  
L04923        implicit none
L04924  
L04925  !..Local variables
L04926        DOUBLE PRECISION:: Ds_m, vts, vtc, stokes, reynolds, Ef_sw
L04927        DOUBLE PRECISION:: p, yc0, F, G, H, z, K0
L04928        INTEGER:: i, j
L04929  
L04930        do j = 1, nbc
L04931        vtc = 1.19D4 * (1.0D4*Dc(j)*Dc(j)*0.25D0)
L04932        do i = 1, nbs
L04933           vts = av_s*Ds(i)**bv_s * DEXP(-fv_s*Ds(i)) - vtc
L04934           Ds_m = (am_s*Ds(i)**bm_s / am_r)**obmr
L04935           p = Dc(j)/Ds_m
L04936           if (p.gt.0.25 .or. Ds(i).lt.D0s .or. Dc(j).lt.6.E-6 &
L04937                 .or. vts.lt.1.E-3) then
L04938            t_Efsw(i,j) = 0.0
L04939           else
L04940            stokes = Dc(j)*Dc(j)*vts*rho_w/(9.*1.718E-5*Ds_m)
L04941            reynolds = 9.*stokes/(p*p*rho_w)
L04942  
L04943            F = DLOG(reynolds)
L04944            G = -0.1007D0 - 0.358D0*F + 0.0261D0*F*F
L04945            K0 = DEXP(G)
L04946            z = DLOG(stokes/(K0+1.D-15))
L04947            H = 0.1465D0 + 1.302D0*z - 0.607D0*z*z + 0.293D0*z*z*z
L04948            yc0 = 2.0D0/PI * ATAN(H)
L04949            Ef_sw = (yc0+p)*(yc0+p) / ((1.+p)*(1.+p))
L04950  
L04951            t_Efsw(i,j) = MAX(0.0, MIN(SNGL(Ef_sw), 0.95))
L04952           endif
L04953  
L04954        enddo
L04955        enddo
L04956  
L04957        end subroutine table_Efsw
```

> - **雪的等效水球径**（L4934）：`Ds_m = (am_s·D^bm_s/am_r)^(1/bm_r)`——把非球形的雪按质量换算成同质量水球，才能进 Stokes 判据；`vtc` 是云滴 Stokes 流落速、`vts` 是雪落速减去云滴落速（相对速度）。
> - 其余与 `table_Efrw` 同构（Wang & Ji 2000 方法，模块头注释）。

### 07b.2.6 `Eff_aero`：气溶胶清除效率（运行时函数）

<!-- code_extract code_extract.py v1.1
source: phys/module_mp_thompson.F
ranges: L4965-L5001
file_lines: 6192
file_md5: f4ec64c511d6656277c4d1f9346813d1
display: line-numbered (strip L-prefix and !file: line to restore)
range_md5: 18ce4c3cd71ea90b67403dd08dff2d41
seg_lines: 37
-->

```fortran
!file: phys/module_mp_thompson.F    L4965-L5001
L04965        real function Eff_aero(D, Da, visc,rhoa,Temp,species)
L04966  
L04967        implicit none
L04968        real:: D, Da, visc, rhoa, Temp
L04969        character(LEN=1):: species
L04970        real:: aval, Cc, diff, Re, Sc, St, St2, vt, Eff
L04971        real, parameter:: boltzman = 1.3806503E-23
L04972        real, parameter:: meanPath = 0.0256E-6
L04973  
L04974        vt = 1.
L04975        if (species .eq. 'r') then
L04976           vt = -0.1021 + 4.932E3*D - 0.9551E6*D*D                        &
L04977                + 0.07934E9*D*D*D - 0.002362E12*D*D*D*D
L04978        elseif (species .eq. 's') then
L04979           vt = av_s*D**bv_s
L04980        elseif (species .eq. 'g') then
L04981           vt = av_g(idx_bg1)*D**bv_g(idx_bg1)
L04982        endif
L04983  
L04984        Cc    = 1. + 2.*meanPath/Da *(1.257+0.4*exp(-0.55*Da/meanPath))
L04985        diff  = boltzman*Temp*Cc/(3.*PI*visc*Da)
L04986  
L04987        Re    = 0.5*rhoa*D*vt/visc
L04988        Sc    = visc/(rhoa*diff)
L04989  
L04990        St    = Da*Da*vt*1000./(9.*visc*D)
L04991        aval  = 1.+LOG(1.+Re)
L04992        St2   = (1.2 + 1./12.*aval)/(1.+aval)
L04993  
L04994        Eff = 4./(Re*Sc) * (1. + 0.4*SQRT(Re)*Sc**0.3333                  &
L04995                               + 0.16*SQRT(Re)*SQRT(Sc))                  &
L04996                 + 4.*Da/D * (0.02 + Da/D*(1.+2.*SQRT(Re)))
L04997  
L04998        if (St.gt.St2) Eff = Eff  + ( (St-St2)/(St-St2+0.666667))**1.5
L04999        Eff_aero = MAX(1.E-5, MIN(Eff, 1.0))
L05000  
L05001        end function Eff_aero
```

> 这是建表族里唯一的**运行时**函数（主实体每个收集过程都调）。Slinn (1983) 框架（Wang et al. 2010, ACP 实现）：三项之和——
> - **布朗扩散** `4/(Re·Sc)·(1 + 0.4·√Re·Sc^{1/3} + 0.16·√Re·√Sc)`（小粒子主导）；
> - **截留** `4·Da/D·(0.02 + Da/D·(1+2√Re))`（粒径比主导）；
> - **惯性撞击** `((St−St2)/(St−St2+2/3))^{3/2}`，仅当 `St > St2`（大粒子主导），临界 Stokes 数 `St2 = (1.2 + ln(1+Re)/12)/(1+ln(1+Re))`。
> - Cunningham 滑移修正 `Cc`（气溶胶小到接近分子平均自由程时扩散增强）；`vt` 按收集者物种选落速式（雨多项式/雪霰幂律）。钳位 [1e-5, 1]。
> - 主实体用法（code_07a §07a.8.5）：对 CCN 用 0.04 μm、IN 用 0.8 μm、黑碳用 0.0236 μm 的代表性粒径——**一个函数服务三类气溶胶，差异全在调用参数**。

### 07b.2.7 `table_dropEvap`：蒸发的累积分布表

<!-- code_extract code_extract.py v1.1
source: phys/module_mp_thompson.F
ranges: L5011-L5099
file_lines: 6192
file_md5: f4ec64c511d6656277c4d1f9346813d1
display: line-numbered (strip L-prefix and !file: line to restore)
range_md5: e8cc2fab8046665297424120be9b66aa
seg_lines: 89
-->

```fortran
!file: phys/module_mp_thompson.F    L5011-L5099
L05011        subroutine table_dropEvap
L05012  
L05013        implicit none
L05014  
L05015  !..Local variables
L05016        INTEGER:: i, j, k, n
L05017        DOUBLE PRECISION, DIMENSION(nbc):: N_c, massc
L05018        DOUBLE PRECISION:: summ, summ2, lamc, N0_c
L05019        INTEGER:: nu_c
L05020  !      DOUBLE PRECISION:: Nt_r, N0, lam_exp, lam
L05021  !      REAL:: xlimit_intg
L05022  
L05023        do n = 1, nbc
L05024           massc(n) = am_r*Dc(n)**bm_r
L05025        enddo
L05026  
L05027        do k = 1, nbc
L05028           nu_c = MIN(15, NINT(1000.E6/t_Nc(k)) + 2)
L05029           do j = 1, ntb_c
L05030              lamc = (t_Nc(k)*am_r* ccg(2,nu_c)*ocg1(nu_c) / r_c(j))**obmr
L05031              N0_c = t_Nc(k)*ocg1(nu_c) * lamc**cce(1,nu_c)
L05032              do i = 1, nbc
L05033  !-GT           tnc_wev(i,j,k) = GAMMP(nu_c+1., SNGL(Dc(i)*lamc))*t_Nc(k)
L05034                 N_c(i) = N0_c* Dc(i)**nu_c*EXP(-lamc*Dc(i))*dtc(i)
L05035  !     if(j.eq.18 .and. k.eq.50) print*, ' N_c = ', N_c(i)
L05036                 summ = 0.
L05037                 summ2 = 0.
L05038                 do n = 1, i
L05039                    summ = summ + massc(n)*N_c(n)
L05040                    summ2 = summ2 + N_c(n)
L05041                 enddo
L05042  !      if(j.eq.18 .and. k.eq.50) print*, '  DEBUG-TABLE: ', r_c(j), t_Nc(k), summ2, summ
L05043                 tpc_wev(i,j,k) = summ
L05044                 tnc_wev(i,j,k) = summ2
L05045              enddo
L05046           enddo
L05047        enddo
L05048  
L05049  !
L05050  !..To do the same thing for rain.
L05051  !
L05052  !     do k = 1, ntb_r
L05053  !     do j = 1, ntb_r1
L05054  !        lam_exp = (N0r_exp(j)*am_r*crg(1)/r_r(k))**ore1
L05055  !        lam = lam_exp * (crg(3)*org2*org1)**obmr
L05056  !        N0 = N0r_exp(j)/(crg(2)*lam_exp) * lam**cre(2)
L05057  !        Nt_r = N0 * crg(2) / lam**cre(2)
L05058  !        do i = 1, nbr
L05059  !           xlimit_intg = lam*Dr(i)
L05060  !           tnr_rev(i,j,k) = GAMMP(mu_r+1.0, xlimit_intg) * Nt_r
L05061  !        enddo
L05062  !     enddo
L05063  !     enddo
L05064  
L05065  ! TO APPLY TABLE ABOVE
L05066  !..Rain lookup table indexes.
L05067  !         Dr_star = DSQRT(-2.D0*DT * t1_evap/(2.*PI) &
L05068  !                 * 0.78*4.*diffu(k)*xsat*rvs/rho_w)
L05069  !         idx_d = NINT(1.0 + FLOAT(nbr) * DLOG(Dr_star/D0r)             &
L05070  !               / DLOG(Dr(nbr)/D0r))
L05071  !         idx_d = MAX(1, MIN(idx_d, nbr))
L05072  !
L05073  !         nir = NINT(ALOG10(rr(k)))
L05074  !         do nn = nir-1, nir+1
L05075  !            n = nn
L05076  !            if ( (rr(k)/10.**nn).ge.1.0 .and. &
L05077  !                 (rr(k)/10.**nn).lt.10.0) goto 154
L05078  !         enddo
L05079  !154      continue
L05080  !         idx_r = INT(rr(k)/10.**n) + 10*(n-nir2) - (n-nir2)
L05081  !         idx_r = MAX(1, MIN(idx_r, ntb_r))
L05082  !
L05083  !         lamr = (am_r*crg(3)*org2*nr(k)/rr(k))**obmr
L05084  !         lam_exp = lamr * (crg(3)*org2*org1)**bm_r
L05085  !         N0_exp = org1*rr(k)/am_r * lam_exp**cre(1)
L05086  !         nir = NINT(DLOG10(N0_exp))
L05087  !         do nn = nir-1, nir+1
L05088  !            n = nn
L05089  !            if ( (N0_exp/10.**nn).ge.1.0 .and. &
L05090  !                 (N0_exp/10.**nn).lt.10.0) goto 155
L05091  !         enddo
L05092  !155      continue
L05093  !         idx_r1 = INT(N0_exp/10.**n) + 10*(n-nir3) - (n-nir3)
L05094  !         idx_r1 = MAX(1, MIN(idx_r1, ntb_r1))
L05095  !
L05096  !         pnr_rev(k) = MIN(nr(k)*odts, SNGL(tnr_rev(idx_d,idx_r1,idx_r) &   ! RAIN2M
L05097  !                    * odts))
L05098  
L05099        end subroutine table_dropEvap
```

> - **表内容**：`tpc_wev/tnx_wev(i,j,k)` = 直径 ≤ `Dc(i)` 的云滴**累积**质量/数量——三维索引是 (直径上界, 云水含量, 云滴数)。主实体蒸发分支算出“单步内全蒸发最大径 `Dc_star`”后按它索引，直接取“这批全蒸发的小滴”的质量与数（code_07a §07a.8.14 蒸发段）。
> - **开发史痕迹**（L5033 起的大段注释）：被 `!` 掉的 `GAMMP` 版本（解析累积分布）与完整的雨侧应用代码——**表实现与解析实现的对照现场**；最终雨蒸发用了解析积分（主实体 `t1_qr_ev` 系数），云滴蒸发用本表。读 WRF 源码要习惯这种“注释里埋着另一条实现路径”的写法。

### 07b.2.8 `table_ccnAct` 与 `activ_ncloud`：气溶胶活化

<!-- code_extract code_extract.py v1.1
source: phys/module_mp_thompson.F
ranges: L5110-L5166
file_lines: 6192
file_md5: f4ec64c511d6656277c4d1f9346813d1
display: line-numbered (strip L-prefix and !file: line to restore)
range_md5: a57c5c470b025c40b078e84b34f41f56
seg_lines: 57
-->

```fortran
!file: phys/module_mp_thompson.F    L5110-L5166
L05110        subroutine table_ccnAct
L05111  
L05112        USE module_domain
L05113        USE module_dm
L05114        implicit none
L05115  
L05116        LOGICAL, EXTERNAL:: wrf_dm_on_monitor
L05117  
L05118  !..Local variables
L05119        INTEGER:: iunit_mp_th1, i
L05120        LOGICAL:: opened
L05121        CHARACTER*64 errmess
L05122  
L05123        iunit_mp_th1 = -1
L05124        IF ( wrf_dm_on_monitor() ) THEN
L05125          DO i = 20,99
L05126            INQUIRE ( i , OPENED = opened )
L05127            IF ( .NOT. opened ) THEN
L05128              iunit_mp_th1 = i
L05129              GOTO 2010
L05130            ENDIF
L05131          ENDDO
L05132   2010   CONTINUE
L05133        ENDIF
L05134  #if defined(DM_PARALLEL) && !defined(STUBMPI)
L05135        CALL wrf_dm_bcast_bytes ( iunit_mp_th1 , IWORDSIZE )
L05136  #endif
L05137        IF ( iunit_mp_th1 < 0 ) THEN
L05138          CALL wrf_error_fatal ( 'module_mp_thompson: table_ccnAct: '//   &
L05139             'Can not find unused fortran unit to read in lookup table.')
L05140        ENDIF
L05141  
L05142        IF ( wrf_dm_on_monitor() ) THEN
L05143          WRITE(errmess, '(A,I2)') 'module_mp_thompson: opening CCN_ACTIVATE.BIN on unit ',iunit_mp_th1
L05144          CALL wrf_debug(150, errmess)
L05145          OPEN(iunit_mp_th1,FILE='CCN_ACTIVATE.BIN',                      &
L05146               FORM='UNFORMATTED',STATUS='OLD',ERR=9009)
L05147        ENDIF
L05148  
L05149  #define DM_BCAST_MACRO(A) CALL wrf_dm_bcast_bytes(A, size(A)*R4SIZE)
L05150  
L05151        IF ( wrf_dm_on_monitor() ) READ(iunit_mp_th1,ERR=9010) tnccn_act
L05152  #if defined(DM_PARALLEL) && !defined(STUBMPI)
L05153        DM_BCAST_MACRO(tnccn_act)
L05154  #endif
L05155  
L05156  
L05157        RETURN
L05158   9009 CONTINUE
L05159        WRITE( errmess , '(A,I2)' ) 'module_mp_thompson: error opening CCN_ACTIVATE.BIN on unit ',iunit_mp_th1
L05160        CALL wrf_error_fatal(errmess)
L05161        RETURN
L05162   9010 CONTINUE
L05163        WRITE( errmess , '(A,I2)' ) 'module_mp_thompson: error reading CCN_ACTIVATE.BIN on unit ',iunit_mp_th1
L05164        CALL wrf_error_fatal(errmess)
L05165  
L05166        end subroutine table_ccnAct
```

> - **数据来源**：`CCN_ACTIVATE.BIN` 是 Eidhammer 气团模式（parcel model）预计算的**五维活化概率表**（轴定义见模块常数段 `ta_Na/ta_Ww/ta_Tk/ta_Ra/ta_Ka`）。建表不是“算”而是“读”——**物理复杂度最高的一张表反而是外部数据**。
> - **单元号扫描**（20–99 找空闲 Fortran unit）+ `wrf_dm_bcast_bytes` 广播；`DM_BCAST_MACRO` 用 `#define` 宏简化重复的广播调用——C 预处理器在 Fortran 代码里的罕见用例（`.F` 大写后缀的含义正在于此）。

<!-- code_extract code_extract.py v1.1
source: phys/module_mp_thompson.F
ranges: L5178-L5252
file_lines: 6192
file_md5: f4ec64c511d6656277c4d1f9346813d1
display: line-numbered (strip L-prefix and !file: line to restore)
range_md5: 21535c97e7518058a19b187c9f771d5a
seg_lines: 75
-->

```fortran
!file: phys/module_mp_thompson.F    L5178-L5252
L05178        real function activ_ncloud(Tt, Ww, NCCN)
L05179  
L05180        implicit none
L05181        REAL, INTENT(IN):: Tt, Ww, NCCN
L05182        REAL:: n_local, w_local
L05183        INTEGER:: i, j, k, l, m, n
L05184        REAL:: A, B, C, D, t, u, x1, x2, y1, y2, nx, wy, fraction
L05185  
L05186  
L05187  !     ta_Na = (/10.0, 31.6, 100.0, 316.0, 1000.0, 3160.0, 10000.0/)  ntb_arc
L05188  !     ta_Ww = (/0.01, 0.0316, 0.1, 0.316, 1.0, 3.16, 10.0, 31.6, 100.0/)  ntb_arw
L05189  !     ta_Tk = (/243.15, 253.15, 263.15, 273.15, 283.15, 293.15, 303.15/)  ntb_art
L05190  !     ta_Ra = (/0.01, 0.02, 0.04, 0.08, 0.16/)  ntb_arr
L05191  !     ta_Ka = (/0.2, 0.4, 0.6, 0.8/)  ntb_ark
L05192  
L05193        n_local = NCCN * 1.E-6
L05194        w_local = Ww
L05195  
L05196        if (n_local .ge. ta_Na(ntb_arc)) then
L05197           n_local = ta_Na(ntb_arc) - 1.0
L05198        elseif (n_local .le. ta_Na(1)) then
L05199           n_local = ta_Na(1) + 1.0
L05200        endif
L05201        do n = 2, ntb_arc
L05202           if (n_local.ge.ta_Na(n-1) .and. n_local.lt.ta_Na(n)) goto 8003
L05203        enddo
L05204   8003 continue
L05205        i = n
L05206        x1 = LOG(ta_Na(i-1))
L05207        x2 = LOG(ta_Na(i))
L05208  
L05209        if (w_local .ge. ta_Ww(ntb_arw)) then
L05210           w_local = ta_Ww(ntb_arw) - 1.0
L05211        elseif (w_local .le. ta_Ww(1)) then
L05212           w_local = ta_Ww(1) + 0.001
L05213        endif
L05214        do n = 2, ntb_arw
L05215           if (w_local.ge.ta_Ww(n-1) .and. w_local.lt.ta_Ww(n)) goto 8005
L05216        enddo
L05217   8005 continue
L05218        j = n
L05219        y1 = LOG(ta_Ww(j-1))
L05220        y2 = LOG(ta_Ww(j))
L05221  
L05222        k = MAX(1, MIN( NINT( (Tt - ta_Tk(1))*0.1) + 1, ntb_art))
L05223  
L05224  !..The next two values are indexes of mean aerosol radius and
L05225  !.. hygroscopicity.  Currently these are constant but a future version
L05226  !.. should implement other variables to allow more freedom such as
L05227  !.. at least simple separation of tiny size sulfates from larger
L05228  !.. sea salts.
L05229        l = 3
L05230        m = 2
L05231  
L05232        A = tnccn_act(i-1,j-1,k,l,m)
L05233        B = tnccn_act(i,j-1,k,l,m)
L05234        C = tnccn_act(i,j,k,l,m)
L05235        D = tnccn_act(i-1,j,k,l,m)
L05236        nx = LOG(n_local)
L05237        wy = LOG(w_local)
L05238  
L05239        t = (nx-x1)/(x2-x1)
L05240        u = (wy-y1)/(y2-y1)
L05241  
L05242  !     t = (n_local-ta(Na(i-1))/(ta_Na(i)-ta_Na(i-1))
L05243  !     u = (w_local-ta_Ww(j-1))/(ta_Ww(j)-ta_Ww(j-1))
L05244  
L05245        fraction = (1.0-t)*(1.0-u)*A + t*(1.0-u)*B + t*u*C + (1.0-t)*u*D
L05246  
L05247  !     if (NCCN*fraction .gt. 0.75*Nt_c_max) then
L05248  !        write(*,*) ' DEBUG-GT ', n_local, w_local, Tt, i, j, k
L05249  !     endif
L05250  
L05251        activ_ncloud = NCCN*fraction
L05252  
```

> - **五维查表**：气溶胶数与垂直速度**对数双线性**（物理量跨四个量级、表在对数轴上等距）、温度线性索引、平均半径 `l=3`（0.04 μm）与吸湿性 `m=2`（kappa=0.4）**写死**——原注释自承“未来版本应放开，至少把硫酸盐与海盐分开”。改造气溶胶敏感性实验时，`l/m` 这两个死值是第一个要动的。
> - **双线性插值**（A/B/C/D 四角 + t/u 权重）后 `activ_ncloud = NCCN·fraction`——返回“实际活化出的云滴数”。

## 07b.3 不完全 Γ 函数族（Numerical Recipes）

<!-- code_extract code_extract.py v1.1
source: phys/module_mp_thompson.F
ranges: L5256-L5290
file_lines: 6192
file_md5: f4ec64c511d6656277c4d1f9346813d1
display: line-numbered (strip L-prefix and !file: line to restore)
range_md5: e97a60618d5ee7da1bb5c72f9912a69b
seg_lines: 35
-->

```fortran
!file: phys/module_mp_thompson.F    L5256-L5290
L05256  !+---+-----------------------------------------------------------------+
L05257        SUBROUTINE GCF(GAMMCF,A,X,GLN)
L05258  !     --- RETURNS THE INCOMPLETE GAMMA FUNCTION Q(A,X) EVALUATED BY ITS
L05259  !     --- CONTINUED FRACTION REPRESENTATION AS GAMMCF.  ALSO RETURNS
L05260  !     --- LN(GAMMA(A)) AS GLN.  THE CONTINUED FRACTION IS EVALUATED BY
L05261  !     --- A MODIFIED LENTZ METHOD.
L05262  !     --- USES GAMMLN
L05263        IMPLICIT NONE
L05264        INTEGER, PARAMETER:: ITMAX=100
L05265        REAL, PARAMETER:: gEPS=3.E-7
L05266        REAL, PARAMETER:: FPMIN=1.E-30
L05267        REAL, INTENT(IN):: A, X
L05268        REAL:: GAMMCF,GLN
L05269        INTEGER:: I
L05270        REAL:: AN,B,C,D,DEL,H
L05271        GLN=GAMMLN(A)
L05272        B=X+1.-A
L05273        C=1./FPMIN
L05274        D=1./B
L05275        H=D
L05276        DO 11 I=1,ITMAX
L05277          AN=-I*(I-A)
L05278          B=B+2.
L05279          D=AN*D+B
L05280          IF(ABS(D).LT.FPMIN)D=FPMIN
L05281          C=B+AN/C
L05282          IF(ABS(C).LT.FPMIN)C=FPMIN
L05283          D=1./D
L05284          DEL=D*C
L05285          H=H*DEL
L05286          IF(ABS(DEL-1.).LT.gEPS)GOTO 1
L05287   11   CONTINUE
L05288        PRINT *, 'A TOO LARGE, ITMAX TOO SMALL IN GCF'
L05289   1    GAMMCF=EXP(-X+A*LOG(X)-GLN)*H
L05290        END SUBROUTINE GCF
```

> **版权提示**：`GCF/GSER/GAMMLN/GAMMP` 四件是 Numerical Recipes Software 1986–92 的例程（每段尾部保留版权行）。WRF 主体是 public domain，但这四个函数是受版权的历史遗留——本篇按“学习性引用”收录并明确标注；改造复用时注意其许可状态。
>
> `GCF` 用连分式（modified Lentz 法）算 Q(A,X)=Γ(A,X)/Γ(A)，迭代上限 ITMAX=100、收敛 3e-7、`FPMIN=1e-30` 防下溢。

<!-- code_extract code_extract.py v1.1
source: phys/module_mp_thompson.F
ranges: L5292-L5322
file_lines: 6192
file_md5: f4ec64c511d6656277c4d1f9346813d1
display: line-numbered (strip L-prefix and !file: line to restore)
range_md5: 146a920f9038d0c78d99f57df9fcd880
seg_lines: 31
-->

```fortran
!file: phys/module_mp_thompson.F    L5292-L5322
L05292  !+---+-----------------------------------------------------------------+
L05293        SUBROUTINE GSER(GAMSER,A,X,GLN)
L05294  !     --- RETURNS THE INCOMPLETE GAMMA FUNCTION P(A,X) EVALUATED BY ITS
L05295  !     --- ITS SERIES REPRESENTATION AS GAMSER.  ALSO RETURNS LN(GAMMA(A)) 
L05296  !     --- AS GLN.
L05297  !     --- USES GAMMLN
L05298        IMPLICIT NONE
L05299        INTEGER, PARAMETER:: ITMAX=100
L05300        REAL, PARAMETER:: gEPS=3.E-7
L05301        REAL, INTENT(IN):: A, X
L05302        REAL:: GAMSER,GLN
L05303        INTEGER:: N
L05304        REAL:: AP,DEL,SUM
L05305        GLN=GAMMLN(A)
L05306        IF(X.LE.0.)THEN
L05307          IF(X.LT.0.) PRINT *, 'X < 0 IN GSER'
L05308          GAMSER=0.
L05309          RETURN
L05310        ENDIF
L05311        AP=A
L05312        SUM=1./A
L05313        DEL=SUM
L05314        DO 11 N=1,ITMAX
L05315          AP=AP+1.
L05316          DEL=DEL*X/AP
L05317          SUM=SUM+DEL
L05318          IF(ABS(DEL).LT.ABS(SUM)*gEPS)GOTO 1
L05319   11   CONTINUE
L05320        PRINT *,'A TOO LARGE, ITMAX TOO SMALL IN GSER'
L05321   1    GAMSER=SUM*EXP(-X+A*LOG(X)-GLN)
L05322        END SUBROUTINE GSER
```

> `GSER` 用级数算 P(A,X)；`x≤0` 特判（负 x 报错、零返回 0）。

<!-- code_extract code_extract.py v1.1
source: phys/module_mp_thompson.F
ranges: L5324-L5347
file_lines: 6192
file_md5: f4ec64c511d6656277c4d1f9346813d1
display: line-numbered (strip L-prefix and !file: line to restore)
range_md5: a3face55684bcd6ba2a7237f7b38a740
seg_lines: 24
-->

```fortran
!file: phys/module_mp_thompson.F    L5324-L5347
L05324  !+---+-----------------------------------------------------------------+
L05325        REAL FUNCTION GAMMLN(XX)
L05326  !     --- RETURNS THE VALUE LN(GAMMA(XX)) FOR XX > 0.
L05327        IMPLICIT NONE
L05328        REAL, INTENT(IN):: XX
L05329        DOUBLE PRECISION, PARAMETER:: STP = 2.5066282746310005D0
L05330        DOUBLE PRECISION, DIMENSION(6), PARAMETER:: &
L05331                 COF = (/76.18009172947146D0, -86.50532032941677D0, &
L05332                         24.01409824083091D0, -1.231739572450155D0, &
L05333                        .1208650973866179D-2, -.5395239384953D-5/)
L05334        DOUBLE PRECISION:: SER,TMP,X,Y
L05335        INTEGER:: J
L05336  
L05337        X=XX
L05338        Y=X
L05339        TMP=X+5.5D0
L05340        TMP=(X+0.5D0)*LOG(TMP)-TMP
L05341        SER=1.000000000190015D0
L05342        DO 11 J=1,6
L05343          Y=Y+1.D0
L05344          SER=SER+COF(J)/Y
L05345  11    CONTINUE
L05346        GAMMLN=TMP+LOG(STP*SER/X)
L05347        END FUNCTION GAMMLN
```

> `GAMMLN` 用 Lanczos 逼近算 ln Γ(x)（六系数 `COF` + 常数 STP=√(2π)）——**先取对数再指数**是 Γ 函数数值稳定的标准手法（Γ(15)≈4.4e10 已接近单精度上限）。

<!-- code_extract code_extract.py v1.1
source: phys/module_mp_thompson.F
ranges: L5349-L5377
file_lines: 6192
file_md5: f4ec64c511d6656277c4d1f9346813d1
display: line-numbered (strip L-prefix and !file: line to restore)
range_md5: 4e595584310d5e98dcf94c7c884c0713
seg_lines: 29
-->

```fortran
!file: phys/module_mp_thompson.F    L5349-L5377
L05349  !+---+-----------------------------------------------------------------+
L05350        REAL FUNCTION GAMMP(A,X)
L05351  !     --- COMPUTES THE INCOMPLETE GAMMA FUNCTION P(A,X)
L05352  !     --- SEE ABRAMOWITZ AND STEGUN 6.5.1
L05353  !     --- USES GCF,GSER
L05354        IMPLICIT NONE
L05355        REAL, INTENT(IN):: A,X
L05356        REAL:: GAMMCF,GAMSER,GLN
L05357        GAMMP = 0.
L05358        IF((X.LT.0.) .OR. (A.LE.0.)) THEN
L05359          PRINT *, 'BAD ARGUMENTS IN GAMMP'
L05360          RETURN
L05361        ELSEIF(X.LT.A+1.)THEN
L05362          CALL GSER(GAMSER,A,X,GLN)
L05363          GAMMP=GAMSER
L05364        ELSE
L05365          CALL GCF(GAMMCF,A,X,GLN)
L05366          GAMMP=1.-GAMMCF
L05367        ENDIF
L05368        END FUNCTION GAMMP
L05369  !  (C) Copr. 1986-92 Numerical Recipes Software 2.02
L05370  !+---+-----------------------------------------------------------------+
L05371        REAL FUNCTION WGAMMA(y)
L05372  
L05373        IMPLICIT NONE
L05374        REAL, INTENT(IN):: y
L05375  
L05376        WGAMMA = EXP(GAMMLN(y))
L05377  
```

> `GAMMP` 按 `x < a+1` 分派：小 x 用级数（GSER）、大 x 用 1−连分式（GCF）——两式收敛域的标准分工。`WGAMMA = exp(GAMMLN(y))` 是 Γ(y) 的安全包装，模块常数段预计算全部经它。

## 07b.4 饱和混合比函数：RSLF / RSIF

<!-- code_extract code_extract.py v1.1
source: phys/module_mp_thompson.F
ranges: L5379-L5412
file_lines: 6192
file_md5: f4ec64c511d6656277c4d1f9346813d1
display: line-numbered (strip L-prefix and !file: line to restore)
range_md5: 6bf58ca9ac4e40e848cc671c210be717
seg_lines: 34
-->

```fortran
!file: phys/module_mp_thompson.F    L5379-L5412
L05379  !+---+-----------------------------------------------------------------+
L05380  ! THIS FUNCTION CALCULATES THE LIQUID SATURATION VAPOR MIXING RATIO AS
L05381  ! A FUNCTION OF TEMPERATURE AND PRESSURE
L05382  !
L05383        REAL FUNCTION RSLF(P,T)
L05384  
L05385        IMPLICIT NONE
L05386        REAL, INTENT(IN):: P, T
L05387        REAL:: ESL,X
L05388        REAL, PARAMETER:: C0= .611583699E03
L05389        REAL, PARAMETER:: C1= .444606896E02
L05390        REAL, PARAMETER:: C2= .143177157E01
L05391        REAL, PARAMETER:: C3= .264224321E-1
L05392        REAL, PARAMETER:: C4= .299291081E-3
L05393        REAL, PARAMETER:: C5= .203154182E-5
L05394        REAL, PARAMETER:: C6= .702620698E-8
L05395        REAL, PARAMETER:: C7= .379534310E-11
L05396        REAL, PARAMETER:: C8=-.321582393E-13
L05397  
L05398        X=MAX(-80.,T-273.16)
L05399  
L05400  !      ESL=612.2*EXP(17.67*X/(T-29.65))
L05401        ESL=C0+X*(C1+X*(C2+X*(C3+X*(C4+X*(C5+X*(C6+X*(C7+X*C8)))))))
L05402        ESL=MIN(ESL, P*0.15)        ! Even with P=1050mb and T=55C, the sat. vap. pres only contributes to ~15% of total pres.
L05403        RSLF=.622*ESL/(P-ESL)
L05404  
L05405  !    ALTERNATIVE
L05406  !  ; Source: Murphy and Koop, Review of the vapour pressure of ice and
L05407  !             supercooled water for atmospheric applications, Q. J. R.
L05408  !             Meteorol. Soc (2005), 131, pp. 1539-1565.
L05409  !    ESL = EXP(54.842763 - 6763.22 / T - 4.210 * ALOG(T) + 0.000367 * T
L05410  !        + TANH(0.0415 * (T - 218.8)) * (53.878 - 1331.22
L05411  !        / T - 9.44523 * ALOG(T) + 0.014025 * T))
L05412  
```

> - **Flatau et al. (1992) 九阶多项式**：`es(T)` 直接拟合（单位 Pa，`C0=611.2` 是 0 °C 值）——相比积分式（书 (2.2.6)/(2.2.7) 的 Clausius–Clapeyron 积分）多项式在过冷水区（−80~0 °C）更准；`X = MAX(-80, T−273.16)` 设下限。
> - **物理钳位** `ESL = MIN(ESL, 0.15·P)`：注释给出理由——P=1050 hPa、T=55 °C 时 es 也只占总压 ~15%，超出即非物理（防数值爆表）。
> - **被注释的两个替代口径**：Bolton 指数式（`612.2·exp(17.67X/(T−29.65))`）与 Murphy & Koop (2005)——加上现行多项式，**同一个饱和比三套公式共存于 20 行内**。教材 ch11 的“三口径”结论在源码里就是这么写的；三口径的数值差异对照实验见教材 ch13 §13.9.2。
> - `RSLF = 0.622·es/(p−es)`——比湿分母的口式（书 (2.2.11) 的混合比形态）。

<!-- code_extract code_extract.py v1.1
source: phys/module_mp_thompson.F
ranges: L5414-L5443
file_lines: 6192
file_md5: f4ec64c511d6656277c4d1f9346813d1
display: line-numbered (strip L-prefix and !file: line to restore)
range_md5: 20d6ab68920d210ab2e4c27d3c34cd39
seg_lines: 30
-->

```fortran
!file: phys/module_mp_thompson.F    L5414-L5443
L05414  !+---+-----------------------------------------------------------------+
L05415  ! THIS FUNCTION CALCULATES THE ICE SATURATION VAPOR MIXING RATIO AS A
L05416  ! FUNCTION OF TEMPERATURE AND PRESSURE
L05417  !
L05418        REAL FUNCTION RSIF(P,T)
L05419  
L05420        IMPLICIT NONE
L05421        REAL, INTENT(IN):: P, T
L05422        REAL:: ESI,X
L05423        REAL, PARAMETER:: C0= .609868993E03
L05424        REAL, PARAMETER:: C1= .499320233E02
L05425        REAL, PARAMETER:: C2= .184672631E01
L05426        REAL, PARAMETER:: C3= .402737184E-1
L05427        REAL, PARAMETER:: C4= .565392987E-3
L05428        REAL, PARAMETER:: C5= .521693933E-5
L05429        REAL, PARAMETER:: C6= .307839583E-7
L05430        REAL, PARAMETER:: C7= .105785160E-9
L05431        REAL, PARAMETER:: C8= .161444444E-12
L05432  
L05433        X=MAX(-80.,T-273.16)
L05434        ESI=C0+X*(C1+X*(C2+X*(C3+X*(C4+X*(C5+X*(C6+X*(C7+X*C8)))))))
L05435        ESI=MIN(ESI, P*0.15)
L05436        RSIF=.622*ESI/max(1.e-4,(P-ESI))
L05437  
L05438  !    ALTERNATIVE
L05439  !  ; Source: Murphy and Koop, Review of the vapour pressure of ice and
L05440  !             supercooled water for atmospheric applications, Q. J. R.
L05441  !             Meteorol. Soc (2005), 131, pp. 1539-1565.
L05442  !     ESI = EXP(9.550426 - 5723.265/T + 3.53068*ALOG(T) - 0.00728332*T)
L05443  
```

> 冰面版 `RSIF` 同构（系数不同）；**多了 `max(1.e-4, P−ESI)` 防除零**——极低温下 es→0 会使分母→p（无危险），此保护防的是输入 p 本身异常的情况。Murphy & Koop 冰面替代式同样以注释形式在场。

## 07b.5 冰核化物理函数：iceDeMott / iceKoop / delta_p

<!-- code_extract code_extract.py v1.1
source: phys/module_mp_thompson.F
ranges: L5446-L5513
file_lines: 6192
file_md5: f4ec64c511d6656277c4d1f9346813d1
display: line-numbered (strip L-prefix and !file: line to restore)
range_md5: eb805f62de3cd89067be8539c82dc7ef
seg_lines: 68
-->

```fortran
!file: phys/module_mp_thompson.F    L5446-L5513
L05446  !+---+-----------------------------------------------------------------+
L05447        real function iceDeMott(tempc, qv, qvs, qvsi, rho, nifa)
L05448        implicit none
L05449  
L05450        REAL, INTENT(IN):: tempc, qv, qvs, qvsi, rho, nifa
L05451  
L05452  !..Local vars
L05453        REAL:: satw, sati, siw, p_x, si0x, dtt, dsi, dsw, dab, fc, hx
L05454        REAL:: ntilde, n_in, nmax, nhat, mux, xni, nifa_cc
L05455        REAL, PARAMETER:: p_c1    = 1000.
L05456        REAL, PARAMETER:: p_rho_c = 0.76
L05457        REAL, PARAMETER:: p_alpha = 1.0
L05458        REAL, PARAMETER:: p_gam   = 2.
L05459        REAL, PARAMETER:: delT    = 5.
L05460        REAL, PARAMETER:: T0x     = -40.
L05461        REAL, PARAMETER:: Sw0x    = 0.97
L05462        REAL, PARAMETER:: delSi   = 0.1
L05463        REAL, PARAMETER:: hdm     = 0.15
L05464        REAL, PARAMETER:: p_psi   = 0.058707*p_gam/p_rho_c
L05465        REAL, PARAMETER:: aap     = 1.
L05466        REAL, PARAMETER:: bbp     = 0.
L05467        REAL, PARAMETER:: y1p     = -35.
L05468        REAL, PARAMETER:: y2p     = -25.
L05469        REAL, PARAMETER:: rho_not0 = 101325./(287.05*273.15)
L05470  
L05471  !+---+
L05472  
L05473        xni = 0.0
L05474  !     satw = qv/qvs
L05475  !     sati = qv/qvsi
L05476  !     siw = qvs/qvsi
L05477  !     p_x = -1.0261+(3.1656e-3*tempc)+(5.3938e-4*(tempc*tempc))         &
L05478  !                +  (8.2584e-6*(tempc*tempc*tempc))
L05479  !     si0x = 1.+(10.**p_x)
L05480  !     if (sati.ge.si0x .and. satw.lt.0.985) then
L05481  !        dtt = delta_p (tempc, T0x, T0x+delT, 1., hdm)
L05482  !        dsi = delta_p (sati, Si0x, Si0x+delSi, 0., 1.)
L05483  !        dsw = delta_p (satw, Sw0x, 1., 0., 1.)
L05484  !        fc = dtt*dsi*0.5
L05485  !        hx = min(fc+((1.-fc)*dsw), 1.)
L05486  !        ntilde = p_c1*p_gam*((exp(12.96*(sati-1.1)))**0.3) / p_rho_c
L05487  !        if (tempc .le. y1p) then
L05488  !           n_in = ntilde
L05489  !        elseif (tempc .ge. y2p) then
L05490  !           n_in = p_psi*p_c1*exp(12.96*(sati-1.)-0.639)
L05491  !        else
L05492  !           if (tempc .le. -30.) then
L05493  !              nmax = p_c1*p_gam*(exp(12.96*(siw-1.1)))**0.3/p_rho_c
L05494  !           else
L05495  !              nmax = p_psi*p_c1*exp(12.96*(siw-1.)-0.639)
L05496  !           endif
L05497  !           ntilde = MIN(ntilde, nmax)
L05498  !           nhat = MIN(p_psi*p_c1*exp(12.96*(sati-1.)-0.639), nmax)
L05499  !           dab = delta_p (tempc, y1p, y2p, aap, bbp)
L05500  !           n_in = MIN(nhat*(ntilde/nhat)**dab, nmax)
L05501  !        endif
L05502  !        mux = hx*p_alpha*n_in*rho
L05503  !        xni = mux*((6700.*nifa)-200.)/((6700.*5.E5)-200.)
L05504  !     elseif (satw.ge.0.985 .and. tempc.gt.HGFR-273.15) then
L05505           nifa_cc = MAX(0.5, nifa*RHO_NOT0*1.E-6/rho)
L05506  !        xni  = 3.*nifa_cc**(1.25)*exp((0.46*(-tempc))-11.6)              !  [DeMott, 2015]
L05507           xni = (5.94e-5*(-tempc)**3.33)                                 & !  [DeMott, 2010]
L05508                      * (nifa_cc**((-0.0264*(tempc))+0.0033))
L05509           xni = xni*rho/RHO_NOT0 * 1000.
L05510  !     endif
L05511  
L05512        iceDeMott = MAX(0., xni)
L05513  
```

> - **大段注释代码 = Phillips et al. (2008) 完整实现**（`delta_p` 辅助函数就是为它写的）——现行代码只保留 DeMott (2010)。**两个时代的冰核化参数化叠在同一函数里**，读时注意 `!` 的范围。
> - **现行式**（L5506–L5508）：`xni = 5.94e-5·(−Tc)^3.33 · nifa_cc^(−0.0264·Tc+0.0033)`——温度三次方幂律 × 气溶胶数的**温度依赖指数**（越冷对气溶胶越敏感，这是 DeMott 2010 对 Cooper 纯温度式的本质升级——把“尘埃越多冰核越多”定量化）；`nifa_cc` 是换算到标准态的气溶胶数（cm⁻³）。
> - 被注释的 `[DeMott, 2015]` 更新式（3·nifa^1.25·exp(0.46·(−T)−11.6)）——**论文谱系 2010→2015→(被弃的 2008) 三代同堂**。
> - 返回前单位还原：`xni·ρ/ρ_not0·1000`（cm⁻³→m⁻³ 的密度订正）。

<!-- code_extract code_extract.py v1.1
source: phys/module_mp_thompson.F
ranges: L5516-L5545
file_lines: 6192
file_md5: f4ec64c511d6656277c4d1f9346813d1
display: line-numbered (strip L-prefix and !file: line to restore)
range_md5: 6a7f049de1c082b7bff718971a5c5c4b
seg_lines: 30
-->

```fortran
!file: phys/module_mp_thompson.F    L5516-L5545
L05516  !+---+-----------------------------------------------------------------+
L05517  !..Newer research since Koop et al (2001) suggests that the freezing
L05518  !.. rate should be lower than original paper, so J_rate is reduced
L05519  !.. by two orders of magnitude.
L05520  
L05521        real function iceKoop(temp, qv, qvs, naero, dt)
L05522        implicit none
L05523  
L05524        REAL, INTENT(IN):: temp, qv, qvs, naero, DT
L05525        REAL:: mu_diff, a_w_i, delta_aw, log_J_rate, J_rate, prob_h, satw
L05526        REAL:: xni
L05527  
L05528        xni = 0.0
L05529        satw = qv/qvs
L05530        mu_diff    = 210368.0 + (131.438*temp) - (3.32373E6/temp)         &
L05531       &           - (41729.1*alog(temp))
L05532        a_w_i      = exp(mu_diff/(R_uni*temp))
L05533        delta_aw   = satw - a_w_i
L05534        log_J_rate = -906.7 + (8502.0*delta_aw)                           &
L05535       &           - (26924.0*delta_aw*delta_aw)                          &
L05536       &           + (29180.0*delta_aw*delta_aw*delta_aw)
L05537        log_J_rate = MIN(20.0, log_J_rate)
L05538        J_rate     = 10.**log_J_rate                                       ! cm-3 s-1
L05539        prob_h     = MIN(1.-exp(-J_rate*ar_volume*DT), 1.)
L05540        if (prob_h .gt. 0.) then
L05541           xni     = MIN(prob_h*naero, 1000.E3)
L05542        endif
L05543  
L05544        iceKoop = MAX(0.0, xni)
L05545  
```

> - **Koop (2001, Nature) 均质冻结**：核心变量是**水活度差** `delta_aw = satw − a_w_i`——过冷水滴相对冰的水活度超出量（`a_w_i` 由冰的化学势差多项式 `mu_diff` 算）。冻结率 `log_J = −906.7 + 8502Δaw − 26924Δaw² + 29180Δaw³`（cm⁻³s⁻¹）——**J 对 Δaw 的立方多项式在 Δaw≈0.25–0.35 区间跨越十几个量级**，这就是“极冷+强过饱和才均质成冰”的定量来源。
> - **两处调参如实读**：①模块头注释声明“新研究（2001 后）认为原论文冻结率应低两个量级”——现行多项式系数即已调低后的版本（源码未再乘 0.01，调低藏在系数里）；②`MIN(20, log_J_rate)` 纯数值防溢出。
> - **泊松冻结**（L5538）：`prob = 1 − exp(−J·ar_volume·dt)`——单滴体积 `ar_volume` 用模块常数段的 2.5 μm 半径假设；`prob·naero` 即本步冻结的气溶胶数，上限 1000/L。

<!-- code_extract code_extract.py v1.1
source: phys/module_mp_thompson.F
ranges: L5548-L5579
file_lines: 6192
file_md5: f4ec64c511d6656277c4d1f9346813d1
display: line-numbered (strip L-prefix and !file: line to restore)
range_md5: f7b48505dc783532972a52c8307cc39e
seg_lines: 32
-->

```fortran
!file: phys/module_mp_thompson.F    L5548-L5579
L05548  !+---+-----------------------------------------------------------------+
L05549  !.. Helper routine for Phillips et al (2008) ice nucleation.  Trude
L05550  
L05551        REAL FUNCTION delta_p (yy, y1, y2, aa, bb)
L05552        IMPLICIT NONE
L05553  
L05554        REAL, INTENT(IN):: yy, y1, y2, aa, bb
L05555        REAL:: dab, A, B, a0, a1, a2, a3
L05556  
L05557        A   = 6.*(aa-bb)/((y2-y1)*(y2-y1)*(y2-y1))
L05558        B   = aa+(A*y1*y1*y1/6.)-(A*y1*y1*y2*0.5)
L05559        a0  = B
L05560        a1  = A*y1*y2
L05561        a2  = -A*(y1+y2)*0.5
L05562        a3  = A/3.
L05563  
L05564        if (yy.le.y1) then 
L05565           dab = aa
L05566        else if (yy.ge.y2) then
L05567           dab = bb
L05568        else
L05569           dab = a0+(a1*yy)+(a2*yy*yy)+(a3*yy*yy*yy)
L05570        endif
L05571  
L05572        if (dab.lt.aa) then 
L05573           dab = aa
L05574        endif
L05575        if (dab.gt.bb) then 
L05576           dab = bb
L05577        endif
L05578        delta_p = dab
L05579  
```

> `delta_p` 是**平滑阶跃函数**（y1→y2 区间内从 aa 到 bb 的三次多项式插值、区间外取端值、钳位单调）——Phillips (2008) 方案的开关平滑器。现行活跃代码不再调用它（调用点全在被注释的 Phillips 块里），但函数本体保留——**孤儿函数**，读代码时知道其用途即可。

## 07b.6 辐射与雷达接口

<!-- code_extract code_extract.py v1.1
source: phys/module_mp_thompson.F
ranges: L5585-L5698
file_lines: 6192
file_md5: f4ec64c511d6656277c4d1f9346813d1
display: line-numbered (strip L-prefix and !file: line to restore)
range_md5: 208c46a29fd4c569781f805bf28d51fd
seg_lines: 114
-->

```fortran
!file: phys/module_mp_thompson.F    L5585-L5698
L05585  !+---+-----------------------------------------------------------------+
L05586  !..Compute _radiation_ effective radii of cloud water, ice, and snow.
L05587  !.. These are entirely consistent with microphysics assumptions, not
L05588  !.. constant or otherwise ad hoc as is internal to most radiation
L05589  !.. schemes.  Since only the smallest snowflakes should impact
L05590  !.. radiation, compute from first portion of complicated Field number
L05591  !.. distribution, not the second part, which is the larger sizes.
L05592  !+---+-----------------------------------------------------------------+
L05593  
L05594        subroutine calc_effectRad (t1d, p1d, qv1d, qc1d, nc1d, qi1d, ni1d, qs1d,   &
L05595       &                re_qc1d, re_qi1d, re_qs1d, kts, kte)
L05596  
L05597        IMPLICIT NONE
L05598  
L05599  !..Sub arguments
L05600        INTEGER, INTENT(IN):: kts, kte
L05601        REAL, DIMENSION(kts:kte), INTENT(IN)::                            &
L05602       &                    t1d, p1d, qv1d, qc1d, nc1d, qi1d, ni1d, qs1d
L05603        REAL, DIMENSION(kts:kte), INTENT(INOUT):: re_qc1d, re_qi1d, re_qs1d
L05604  !..Local variables
L05605        INTEGER:: k
L05606        REAL, DIMENSION(kts:kte):: rho, rc, nc, ri, ni, rs
L05607        REAL:: smo2, smob, smoc
L05608        REAL:: tc0, loga_, a_, b_
L05609        DOUBLE PRECISION:: lamc, lami
L05610        LOGICAL:: has_qc, has_qi, has_qs
L05611        INTEGER:: inu_c
L05612        real, dimension(15), parameter:: g_ratio = (/24,60,120,210,336,   &
L05613       &                504,720,990,1320,1716,2184,2730,3360,4080,4896/)
L05614  
L05615        has_qc = .false.
L05616        has_qi = .false.
L05617        has_qs = .false.
L05618  
L05619        re_qc1d(:) = RE_QC_BG
L05620        re_qi1d(:) = RE_QI_BG
L05621        re_qs1d(:) = RE_QS_BG
L05622  
L05623        do k = kts, kte
L05624           rho(k) = 0.622*p1d(k)/(R*t1d(k)*(qv1d(k)+0.622))
L05625           rc(k) = MAX(R1, qc1d(k)*rho(k))
L05626           nc(k) = MAX(2., MIN(nc1d(k)*rho(k), Nt_c_max))
L05627           if (.NOT. is_aerosol_aware) nc(k) = Nt_c
L05628           if (rc(k).gt.R1 .and. nc(k).gt.R2) has_qc = .true.
L05629           ri(k) = MAX(R1, qi1d(k)*rho(k))
L05630           ni(k) = MAX(R2, ni1d(k)*rho(k))
L05631           if (ri(k).gt.R1 .and. ni(k).gt.R2) has_qi = .true.
L05632           rs(k) = MAX(R1, qs1d(k)*rho(k))
L05633           if (rs(k).gt.R1) has_qs = .true.
L05634        enddo
L05635  
L05636        if (has_qc) then
L05637        do k = kts, kte
L05638           if (rc(k).le.R1 .or. nc(k).le.R2) CYCLE
L05639           if (nc(k).lt.100) then
L05640              inu_c = 15
L05641           elseif (nc(k).gt.1.E10) then
L05642              inu_c = 2
L05643           else
L05644              inu_c = MIN(15, NINT(1000.E6/nc(k)) + 2)
L05645           endif
L05646           lamc = (nc(k)*am_r*g_ratio(inu_c)/rc(k))**obmr
L05647           re_qc1d(k) = MAX(2.51E-6, MIN(SNGL(0.5D0 * DBLE(3.+inu_c)/lamc), 50.E-6))
L05648        enddo
L05649        endif
L05650  
L05651        if (has_qi) then
L05652        do k = kts, kte
L05653           if (ri(k).le.R1 .or. ni(k).le.R2) CYCLE
L05654           lami = (am_i*cig(2)*oig1*ni(k)/ri(k))**obmi
L05655           re_qi1d(k) = MAX(2.51E-6, MIN(SNGL(0.5D0 * DBLE(3.+mu_i)/lami), 125.E-6))
L05656        enddo
L05657        endif
L05658  
L05659        if (has_qs) then
L05660        do k = kts, kte
L05661           if (rs(k).le.R1) CYCLE
L05662           tc0 = MIN(-0.1, t1d(k)-273.15)
L05663           smob = rs(k)*oams
L05664  
L05665  !..All other moments based on reference, 2nd moment.  If bm_s.ne.2,
L05666  !.. then we must compute actual 2nd moment and use as reference.
L05667           if (bm_s.gt.(2.0-1.e-3) .and. bm_s.lt.(2.0+1.e-3)) then
L05668              smo2 = smob
L05669           else
L05670              loga_ = sa(1) + sa(2)*tc0 + sa(3)*bm_s &
L05671       &         + sa(4)*tc0*bm_s + sa(5)*tc0*tc0 &
L05672       &         + sa(6)*bm_s*bm_s + sa(7)*tc0*tc0*bm_s &
L05673       &         + sa(8)*tc0*bm_s*bm_s + sa(9)*tc0*tc0*tc0 &
L05674       &         + sa(10)*bm_s*bm_s*bm_s
L05675              a_ = 10.0**loga_
L05676              b_ = sb(1) + sb(2)*tc0 + sb(3)*bm_s &
L05677       &         + sb(4)*tc0*bm_s + sb(5)*tc0*tc0 &
L05678       &         + sb(6)*bm_s*bm_s + sb(7)*tc0*tc0*bm_s &
L05679       &         + sb(8)*tc0*bm_s*bm_s + sb(9)*tc0*tc0*tc0 &
L05680       &         + sb(10)*bm_s*bm_s*bm_s
L05681              smo2 = (smob/a_)**(1./b_)
L05682           endif
L05683  !..Calculate bm_s+1 (th) moment.  Useful for diameter calcs.
L05684           loga_ = sa(1) + sa(2)*tc0 + sa(3)*cse(1) &
L05685       &         + sa(4)*tc0*cse(1) + sa(5)*tc0*tc0 &
L05686       &         + sa(6)*cse(1)*cse(1) + sa(7)*tc0*tc0*cse(1) &
L05687       &         + sa(8)*tc0*cse(1)*cse(1) + sa(9)*tc0*tc0*tc0 &
L05688       &         + sa(10)*cse(1)*cse(1)*cse(1)
L05689           a_ = 10.0**loga_
L05690           b_ = sb(1)+ sb(2)*tc0 + sb(3)*cse(1) + sb(4)*tc0*cse(1) &
L05691       &        + sb(5)*tc0*tc0 + sb(6)*cse(1)*cse(1) &
L05692       &        + sb(7)*tc0*tc0*cse(1) + sb(8)*tc0*cse(1)*cse(1) &
L05693       &        + sb(9)*tc0*tc0*tc0 + sb(10)*cse(1)*cse(1)*cse(1)
L05694           smoc = a_ * smo2**b_
L05695           re_qs1d(k) = MAX(5.01E-6, MIN(0.5*(smoc/smob), 999.E-6))
L05696        enddo
L05697        endif
L05698  
```

> - **设计原则**（模块注释原文）：“entirely consistent with microphysics assumptions, not constant or otherwise ad hoc”——多数辐射方案的有效半径是内部 ad hoc 常数，Thompson 从谱假设直接算，闭合教材 ch12 埋下的接口伏笔（对应讨论见教材 ch13 §13.7.6）。
> - **云水有效半径**（L5645–L5646）：`re = 0.5·(3+nu_c)/lamc`——gamma 谱的有效半径解析式 `r_eff = ∫r³N dr / ∫r²N dr = Γ(4+mu)/(Γ(3+mu)·λ)·(1/2)`（直径→半径乘 0.5）；`g_ratio` 是预存的 Γ 比值整数列。下限 2.51 μm、上限 50 μm。
> - **冰晶**：`mu_i=0` 退化为 `0.5·3/lami`，上限 125 μm；**雪**：`0.5·smoc/smob`（bm_s+1 矩/2 矩即质量加权有效径，Field 谱矩量法再现），下限 5.01 μm、上限 999 μm。**三物种同一公式思想、各自谱形实现**——对照主实体谱参数化段（code_07a §07a.8.2）阅读。
> - `has_qc/has_qi/has_qs` 三标志先扫描再分支——整柱无该物种时整段跳过（与主实体 `no_micro` 同思路）。

<!-- code_extract code_extract.py v1.1
source: phys/module_mp_thompson.F
ranges: L5701-L6027
file_lines: 6192
file_md5: f4ec64c511d6656277c4d1f9346813d1
display: line-numbered (strip L-prefix and !file: line to restore)
range_md5: 1f5f6f989ad76f21181383cc99b0a1f8
seg_lines: 327
-->

```fortran
!file: phys/module_mp_thompson.F    L5701-L6027
L05701  !+---+-----------------------------------------------------------------+
L05702  !..Compute radar reflectivity assuming 10 cm wavelength radar and using
L05703  !.. Rayleigh approximation.  Only complication is melted snow/graupel
L05704  !.. which we treat as water-coated ice spheres and use Uli Blahak's
L05705  !.. library of routines.  The meltwater fraction is simply the amount
L05706  !.. of frozen species remaining from what initially existed at the
L05707  !.. melting level interface.
L05708  !+---+-----------------------------------------------------------------+
L05709  
L05710        subroutine calc_refl10cm (qv1d, qc1d, qr1d, nr1d, qs1d, qg1d,     &
L05711                            ng1d, qb1d, t1d, p1d, dBZ, kts, kte, ii, jj, ke_diag)
L05712  
L05713        IMPLICIT NONE
L05714  
L05715  !..Sub arguments
L05716        INTEGER, INTENT(IN):: kts, kte, ii, jj, ke_diag
L05717        REAL, DIMENSION(kts:kte), INTENT(IN)::                            &
L05718                  qv1d, qc1d, qr1d, nr1d, qs1d, qg1d, ng1d, qb1d, t1d, p1d
L05719        REAL, DIMENSION(kts:kte), INTENT(INOUT):: dBZ
L05720  !     REAL, DIMENSION(kts:kte), INTENT(INOUT):: vt_dBZ
L05721  
L05722  !..Local variables
L05723        REAL, DIMENSION(kts:kte):: temp, pres, qv, rho, rhof
L05724        REAL, DIMENSION(kts:kte):: rc, rr, nr, rs, rg, ng, rb
L05725  
L05726        DOUBLE PRECISION, DIMENSION(kts:kte):: ilamr, ilamg, N0_r, N0_g
L05727        REAL, DIMENSION(kts:kte):: mvd_r
L05728        REAL, DIMENSION(kts:kte):: smob, smo2, smoc, smoz
L05729        REAL:: oM3, M0, Mrat, slam1, slam2, xDs
L05730        REAL:: ils1, ils2, t1_vts, t2_vts, t3_vts, t4_vts
L05731        REAL:: vtr_dbz_wt, vts_dbz_wt, vtg_dbz_wt
L05732  
L05733        REAL, DIMENSION(kts:kte):: ze_rain, ze_snow, ze_graupel
L05734        INTEGER, DIMENSION(kts:kte):: idx_bg
L05735  
L05736        DOUBLE PRECISION:: N0_exp, N0_min, lam_exp, lamr, lamg
L05737        REAL:: a_, b_, loga_, tc0
L05738        DOUBLE PRECISION:: fmelt_s, fmelt_g
L05739  
L05740        INTEGER:: i, k, k_0, kbot, n, ktop
L05741        LOGICAL:: melti
L05742        LOGICAL, DIMENSION(kts:kte):: L_qr, L_qs, L_qg
L05743  
L05744        DOUBLE PRECISION:: cback, x, eta, f_d
L05745        REAL:: xslw1, ygra1, zans1
L05746        INTEGER :: k_0loop
L05747  
L05748  !+---+
L05749  
L05750        do k = kts, kte
L05751           dBZ(k) = -35.0
L05752        enddo
L05753  
L05754  !+---+-----------------------------------------------------------------+
L05755  !..Put column of data into local arrays.
L05756  !+---+-----------------------------------------------------------------+
L05757  
L05758        do k = kts, kte
L05759           temp(k) = t1d(k)
L05760           qv(k) = MAX(1.E-10, qv1d(k))
L05761           pres(k) = p1d(k)
L05762           rho(k) = 0.622*pres(k)/(R*temp(k)*(qv(k)+0.622))
L05763           rhof(k) = SQRT(RHO_NOT/rho(k))
L05764           rc(k) = MAX(R1, qc1d(k)*rho(k))
L05765           if (qr1d(k) .gt. R1) then
L05766              rr(k) = qr1d(k)*rho(k)
L05767              nr(k) = MAX(R2, nr1d(k)*rho(k))
L05768              lamr = (am_r*crg(3)*org2*nr(k)/rr(k))**obmr
L05769              ilamr(k) = 1./lamr
L05770              N0_r(k) = nr(k)*org2*lamr**cre(2)
L05771              mvd_r(k) = (3.0 + mu_r + 0.672) * ilamr(k)
L05772              L_qr(k) = .true.
L05773           else
L05774              rr(k) = R1
L05775              nr(k) = R1
L05776              mvd_r(k) = 50.E-6
L05777              L_qr(k) = .false.
L05778           endif
L05779           if (qs1d(k) .gt. R2) then
L05780              rs(k) = qs1d(k)*rho(k)
L05781              L_qs(k) = .true.
L05782           else
L05783              rs(k) = R1
L05784              L_qs(k) = .false.
L05785           endif
L05786           if (qg1d(k) .gt. R2) then
L05787              rg(k) = qg1d(k)*rho(k)
L05788              ng(k) = MAX(R2, ng1d(k)*rho(k))
L05789              rb(k) = MAX(qg1d(k)/rho_g(NRHG), qb1d(k))
L05790              rb(k) = MIN(qg1d(k)/rho_g(1), rb(k))
L05791              idx_bg(k) = MAX(1,MIN(NINT(qg1d(k)/rb(k) *0.01)+1,NRHG))
L05792              if (.not. is_hail_aware) idx_bg(k) = idx_bg1
L05793              L_qg(k) = .true.
L05794           else
L05795              rg(k) = R1
L05796              ng(k) = R2
L05797              idx_bg(k) = idx_bg1
L05798              L_qg(k) = .false.
L05799           endif
L05800        enddo
L05801  
L05802  !+---+-----------------------------------------------------------------+
L05803  !..Calculate y-intercept, slope, and useful moments for snow.
L05804  !+---+-----------------------------------------------------------------+
L05805        do k = kts, kte
L05806           smo2(k) = 0.
L05807           smob(k) = 0.
L05808           smoc(k) = 0.
L05809           smoz(k) = 0.
L05810        enddo
L05811        if ( ( ke_diag > kts .and. ANY(L_qs .eqv. .true.) ) .or.  &
L05812              (ke_diag == kts .and. L_qs(kts) .eqv. .true. ) ) then
L05813        do k = kts, ke_diag ! kte
L05814           if (.not. L_qs(k)) CYCLE
L05815           tc0 = MIN(-0.1, temp(k)-273.15)
L05816           smob(k) = rs(k)*oams
L05817  
L05818  !..All other moments based on reference, 2nd moment.  If bm_s.ne.2,
L05819  !.. then we must compute actual 2nd moment and use as reference.
L05820           if (bm_s.gt.(2.0-1.e-3) .and. bm_s.lt.(2.0+1.e-3)) then
L05821              smo2(k) = smob(k)
L05822           else
L05823              loga_ = sa(1) + sa(2)*tc0 + sa(3)*bm_s &
L05824       &         + sa(4)*tc0*bm_s + sa(5)*tc0*tc0 &
L05825       &         + sa(6)*bm_s*bm_s + sa(7)*tc0*tc0*bm_s &
L05826       &         + sa(8)*tc0*bm_s*bm_s + sa(9)*tc0*tc0*tc0 &
L05827       &         + sa(10)*bm_s*bm_s*bm_s
L05828              a_ = 10.0**loga_
L05829              b_ = sb(1) + sb(2)*tc0 + sb(3)*bm_s &
L05830       &         + sb(4)*tc0*bm_s + sb(5)*tc0*tc0 &
L05831       &         + sb(6)*bm_s*bm_s + sb(7)*tc0*tc0*bm_s &
L05832       &         + sb(8)*tc0*bm_s*bm_s + sb(9)*tc0*tc0*tc0 &
L05833       &         + sb(10)*bm_s*bm_s*bm_s
L05834              smo2(k) = (smob(k)/a_)**(1./b_)
L05835           endif
L05836  
L05837  !..Calculate bm_s+1 (th) moment.  Useful for diameter calcs.
L05838           loga_ = sa(1) + sa(2)*tc0 + sa(3)*cse(1) &
L05839       &         + sa(4)*tc0*cse(1) + sa(5)*tc0*tc0 &
L05840       &         + sa(6)*cse(1)*cse(1) + sa(7)*tc0*tc0*cse(1) &
L05841       &         + sa(8)*tc0*cse(1)*cse(1) + sa(9)*tc0*tc0*tc0 &
L05842       &         + sa(10)*cse(1)*cse(1)*cse(1)
L05843           a_ = 10.0**loga_
L05844           b_ = sb(1)+ sb(2)*tc0 + sb(3)*cse(1) + sb(4)*tc0*cse(1) &
L05845       &        + sb(5)*tc0*tc0 + sb(6)*cse(1)*cse(1) &
L05846       &        + sb(7)*tc0*tc0*cse(1) + sb(8)*tc0*cse(1)*cse(1) &
L05847       &        + sb(9)*tc0*tc0*tc0 + sb(10)*cse(1)*cse(1)*cse(1)
L05848           smoc(k) = a_ * smo2(k)**b_
L05849  
L05850  !..Calculate bm_s*2 (th) moment.  Useful for reflectivity.
L05851           loga_ = sa(1) + sa(2)*tc0 + sa(3)*cse(3) &
L05852       &         + sa(4)*tc0*cse(3) + sa(5)*tc0*tc0 &
L05853       &         + sa(6)*cse(3)*cse(3) + sa(7)*tc0*tc0*cse(3) &
L05854       &         + sa(8)*tc0*cse(3)*cse(3) + sa(9)*tc0*tc0*tc0 &
L05855       &         + sa(10)*cse(3)*cse(3)*cse(3)
L05856           a_ = 10.0**loga_
L05857           b_ = sb(1)+ sb(2)*tc0 + sb(3)*cse(3) + sb(4)*tc0*cse(3) &
L05858       &        + sb(5)*tc0*tc0 + sb(6)*cse(3)*cse(3) &
L05859       &        + sb(7)*tc0*tc0*cse(3) + sb(8)*tc0*cse(3)*cse(3) &
L05860       &        + sb(9)*tc0*tc0*tc0 + sb(10)*cse(3)*cse(3)*cse(3)
L05861           smoz(k) = a_ * smo2(k)**b_
L05862        enddo
L05863        endif
L05864  
L05865  !+---+-----------------------------------------------------------------+
L05866  !..Calculate y-intercept, slope values for graupel.
L05867  !+---+-----------------------------------------------------------------+
L05868  
L05869        if (ANY(L_qg .eqv. .true.)) then
L05870        do k = kte, kts, -1
L05871           lamg = (am_g(idx_bg(k))*cgg(3,1)*ogg2*ng(k)/rg(k))**obmg
L05872           ilamg(k) = 1./lamg
L05873           N0_g(k) = ng(k)*ogg2*lamg**cge(2,1)
L05874        enddo
L05875        else
L05876           ilamg(:) = 0.
L05877           N0_g(:) = 0.
L05878        endif
L05879  
L05880  !+---+-----------------------------------------------------------------+
L05881  !..Locate K-level of start of melting (k_0 is level above).
L05882  !+---+-----------------------------------------------------------------+
L05883        melti = .false.
L05884        k_0 = kts
L05885        do k = kte-1, kts, -1
L05886           if ( (temp(k).gt.273.15) .and. L_qr(k)                         &
L05887       &                            .and. (L_qs(k+1).or.L_qg(k+1)) ) then
L05888              k_0 = MAX(k+1, k_0)
L05889              melti=.true.
L05890              goto 195
L05891           endif
L05892        enddo
L05893   195  continue
L05894  
L05895  ! Set loop limit for wet ice according to whether the full 3D field is needed or just k=1
L05896        k_0loop = Min(k_0, ke_diag+1)
L05897  
L05898  !+---+-----------------------------------------------------------------+
L05899  !..Do not do the so-called bright band if using the variable density
L05900  !.. graupel-hail category since the density increases during melting and
L05901  !.. will account for bright band behavior explicitly.
L05902  !+---+-----------------------------------------------------------------+
L05903  !     if (is_hail_aware) melti = .false.
L05904  
L05905  !+---+-----------------------------------------------------------------+
L05906  !..Assume Rayleigh approximation at 10 cm wavelength. Rain (all temps)
L05907  !.. and non-water-coated snow and graupel when below freezing are
L05908  !.. simple. Integrations of m(D)*m(D)*N(D)*dD.
L05909  !+---+-----------------------------------------------------------------+
L05910  
L05911        do k = kts, ke_diag ! kte
L05912           ze_rain(k) = 1.e-22
L05913           ze_snow(k) = 1.e-22
L05914           ze_graupel(k) = 1.e-22
L05915           if (L_qr(k)) ze_rain(k) = N0_r(k)*crg(4)*ilamr(k)**cre(4)
L05916           if (L_qs(k)) ze_snow(k) = (0.176/0.93) * (6.0/PI)*(6.0/PI)     &
L05917       &                           * (am_s/900.0)*(am_s/900.0)*smoz(k)
L05918           if (L_qg(k)) ze_graupel(k) = (0.176/0.93) * (6.0/PI)*(6.0/PI)  &
L05919       &               * (am_g(idx_bg(k))/900.0)*(am_g(idx_bg(k))/900.0)  &
L05920       &               * N0_g(k)*cgg(4,1)*ilamg(k)**cge(4,1)
L05921        enddo
L05922  
L05923  !+---+-----------------------------------------------------------------+
L05924  !..Special case of melting ice (snow/graupel) particles.  Assume the
L05925  !.. ice is surrounded by the liquid water.  Fraction of meltwater is
L05926  !.. extremely simple based on amount found above the melting level.
L05927  !.. Uses code from Uli Blahak (rayleigh_soak_wetgraupel and supporting
L05928  !.. routines).
L05929  !+---+-----------------------------------------------------------------+
L05930  
L05931        if (.not. iiwarm .and. melti .and. k_0.ge.2) then
L05932         do k = k_0loop-1, kts, -1
L05933  
L05934  !..Reflectivity contributed by melting snow
L05935            if (L_qs(k) .and. L_qs(k_0) ) then
L05936             fmelt_s = MAX(0.05d0, MIN(1.0d0-rs(k)/rs(k_0), 0.99d0))
L05937             eta = 0.d0
L05938             oM3 = 1./smoc(k)
L05939             M0 = (smob(k)*oM3)
L05940             Mrat = smob(k)*M0*M0*M0
L05941             slam1 = M0 * Lam0
L05942             slam2 = M0 * Lam1
L05943             do n = 1, nrbins
L05944                x = am_s * xxDs(n)**bm_s
L05945                call rayleigh_soak_wetgraupel (x, DBLE(ocms), DBLE(obms), &
L05946       &              fmelt_s, melt_outside_s, m_w_0, m_i_0, lamda_radar, &
L05947       &              CBACK, mixingrulestring_s, matrixstring_s,          &
L05948       &              inclusionstring_s, hoststring_s,                    &
L05949       &              hostmatrixstring_s, hostinclusionstring_s)
L05950                f_d = Mrat*(Kap0*DEXP(-slam1*xxDs(n))                     &
L05951       &              + Kap1*(M0*xxDs(n))**mu_s * DEXP(-slam2*xxDs(n)))
L05952                eta = eta + f_d * CBACK * simpson(n) * xdts(n)
L05953             enddo
L05954             ze_snow(k) = SNGL(lamda4 / (pi5 * K_w) * eta)
L05955            endif
L05956  
L05957  !..Reflectivity contributed by melting graupel
L05958  
L05959  !         if (L_qg(k) .and. L_qg(k_0) ) then
L05960  !          fmelt_g = MAX(0.05d0, MIN(1.0d0-rg(k)/rg(k_0), 0.99d0))
L05961  !          eta = 0.d0
L05962  !          lamg = 1./ilamg(k)
L05963  !          do n = 1, nrbins
L05964  !             x = am_g(idx_bg(k)) * xxDg(n)**bm_g
L05965  !             call rayleigh_soak_wetgraupel (x, DBLE(ocmg(idx_bg(k))), DBLE(obmg), &
L05966  !    &              fmelt_g, melt_outside_g, m_w_0, m_i_0, lamda_radar, &
L05967  !    &              CBACK, mixingrulestring_g, matrixstring_g,          &
L05968  !    &              inclusionstring_g, hoststring_g,                    &
L05969  !    &              hostmatrixstring_g, hostinclusionstring_g)
L05970  !             f_d = N0_g(k)*xxDg(n)**mu_g * DEXP(-lamg*xxDg(n))
L05971  !             eta = eta + f_d * CBACK * simpson(n) * xdtg(n)
L05972  !          enddo
L05973  !          ze_graupel(k) = SNGL(lamda4 / (pi5 * K_w) * eta)
L05974  !         endif
L05975  
L05976         enddo
L05977        endif
L05978  
L05979        do k = ke_diag, kts, -1
L05980           dBZ(k) = 10.*log10((ze_rain(k)+ze_snow(k)+ze_graupel(k))*1.d18)
L05981        enddo
L05982  
L05983  
L05984  !..Reflectivity-weighted terminal velocity (snow, rain, graupel, mix).
L05985  !     do k = kte, kts, -1
L05986  !        vt_dBZ(k) = 1.E-3
L05987  !        if (rs(k).gt.R2) then
L05988  !         Mrat = smob(k) / smoc(k)
L05989  !         ils1 = 1./(Mrat*Lam0 + fv_s)
L05990  !         ils2 = 1./(Mrat*Lam1 + fv_s)
L05991  !         t1_vts = Kap0*csg(5)*ils1**cse(5)
L05992  !         t2_vts = Kap1*Mrat**mu_s*csg(11)*ils2**cse(11)
L05993  !         ils1 = 1./(Mrat*Lam0)
L05994  !         ils2 = 1./(Mrat*Lam1)
L05995  !         t3_vts = Kap0*csg(6)*ils1**cse(6)
L05996  !         t4_vts = Kap1*Mrat**mu_s*csg(12)*ils2**cse(12)
L05997  !         vts_dbz_wt = rhof(k)*av_s * (t1_vts+t2_vts)/(t3_vts+t4_vts)
L05998  !         if (temp(k).ge.273.15 .and. temp(k).lt.275.15) then
L05999  !            vts_dbz_wt = vts_dbz_wt*1.5
L06000  !         elseif (temp(k).ge.275.15) then
L06001  !            vts_dbz_wt = vts_dbz_wt*2.0
L06002  !         endif
L06003  !        else
L06004  !         vts_dbz_wt = 1.E-3
L06005  !        endif
L06006  
L06007  !        if (rr(k).gt.R1) then
L06008  !         lamr = 1./ilamr(k)
L06009  !         vtr_dbz_wt = rhof(k)*av_r*crg(13)*(lamr+fv_r)**(-cre(13))      &
L06010  !    &               / (crg(4)*lamr**(-cre(4)))
L06011  !        else
L06012  !         vtr_dbz_wt = 1.E-3
L06013  !        endif
L06014  
L06015  !        if (rg(k).gt.R2) then
L06016  !         lamg = 1./ilamg(k)
L06017  !         vtg_dbz_wt = rhof(k)*av_g(idx_bg(k))*cgg(5,idx_bg(k))*lamg**(-cge(5,idx_bg(k)))               &
L06018  !    &               / (cgg(4,1)*lamg**(-cge(4,1)))
L06019  !        else
L06020  !         vtg_dbz_wt = 1.E-3
L06021  !        endif
L06022  
L06023  !        vt_dBZ(k) = (vts_dbz_wt*ze_snow(k) + vtr_dbz_wt*ze_rain(k)      &
L06024  !    &                + vtg_dbz_wt*ze_graupel(k))                        &
L06025  !    &                / (ze_rain(k)+ze_snow(k)+ze_graupel(k))
L06026  !     enddo
L06027  
```

> - **Rayleigh 近似**（L5910–L5920）：`ze ∝ ∫D⁶·N(D)dD`——雨直接积分（`cre(4)=7`，D⁶ 的谱矩）；雪/霰乘三组修正：`0.176/0.93`（冰与水的介电因子比 |K_i|²/|K_w|²）、`(6/π)²`（质量→直径的球化换算）、`am/900`（密度归一）。**Rayleigh 10 cm 近似对小滴精确、对大雹欠准**——注释明说这是工程折中。
> - **融化亮带**（L5882–L5892 定位 + L5930–L5976 计算）：融化层判定 `k_0` =“暖层有雨且其上一层有雪/霰”的最高层；融水份额 `fmelt_s = 1 − rs(k)/rs(k_0)`（**用雪含量沿程损耗定义融化进度**——含量守恒的巧妙用法，初值钳 0.05 下限）；然后按 Field 双伽马谱逐 bin 调 `rayleigh_soak_wetgraupel`（Uli Blahak 库，`module_mp_radar` 提供——水包冰核的 Maxwell-Garnett 混合介质后向散射），Simpson 权重积分成 η，`ze = λ⁴/(π⁵·|K_w|²)·η`。**亮带（雷达回波融化增强）是雷达气象的经典现象**，此处是它的模式内模拟。
> - 被注释的霰亮带块（L5958 起）与 `is_hail_aware` 时关闭亮带的开关（L5902）——三矩方案密度随融化演变，亮带效应“已显式包含”，无需参数化。
> - **ke_diag**：诊断层上限（只算需要输出的层）——`calc_refl10cm` 是诊断量，裁剪计算量全靠它。
> - 大段注释的 `vt_dBZ`（反射率加权末速度）：完整实现已在注释里，含雪落速的融化层增强（1.5×/2×）——**又一个“注释里埋着完整功能”的例子**。

## 07b.7 Bolton (1980) 热力学函数族

 湿球温度反演链 `t_dew → t_lcl → theta_e → compT_fr_The`（主实体融化分支用，code_07a §07a.8.3）的五个函数——**教材 ch13 §13.5.3 温湿参量的直接源码对应**。

<!-- code_extract code_extract.py v1.1
source: phys/module_mp_thompson.F
ranges: L6031-L6061
file_lines: 6192
file_md5: f4ec64c511d6656277c4d1f9346813d1
display: line-numbered (strip L-prefix and !file: line to restore)
range_md5: 24062d3c8ce2b77edcfc3c211f07461a
seg_lines: 31
-->

```fortran
!file: phys/module_mp_thompson.F    L6031-L6061
L06031  !
L06032        real function theta_e(pres_Pa,temp_K,w_non,tlcl_K)
L06033  !..
L06034  !..         The following code was based on Bolton (1980) eqn #43
L06035  !..         and claims to have 0.3 K maximum error within -35 < T < 35 C
L06036  !..            pres_Pa = Pressure in Pascals
L06037  !..            temp_K  = Temperature in Kelvin
L06038  !..            w_non   = mixing ratio (non-dimensional = kg/kg)
L06039  !..            tlcl_K  = Temperature at Lifting Condensation Level (K)
L06040  !..
L06041        IMPLICIT NONE
L06042  
L06043        real:: pres_Pa, temp_K, w_non, tlcl_K
L06044        real:: pp, tt, rr, tlc, power, xx, p1, p2
L06045  
L06046  !+---+
L06047  
L06048        pp = pres_Pa
L06049        tt = temp_K
L06050        rr = w_non + 1.e-8
L06051        tlc = tlcl_K
L06052  
L06053        power=(0.2854*(1.0 - (0.28*rr) ))
L06054        xx = tt * (100000.0/pp)**power
L06055  
L06056        p1 = (3.376/tlc) - 0.00254
L06057        p2 = (rr*1000.0) * (1.0 + 0.81*rr)
L06058        
L06059        theta_e = xx * exp(p1*p2)
L06060  
L06061        return
```

> `theta_e`：Bolton (1980) **式 (43)**，假相当位温的 0.3 K 精度近似——`θe = T·(1e5/p)^(0.2854(1−0.28r))·exp((3.376/T_LCL − 0.00254)·r·1000·(1+0.81r))`。对照书 (6.3.8) 的定义式（指针见教材 ch13 §13.3）： Bolton 式是“含过饱和修正项”的工作公式，系数 0.2854 = R_d/c_pd、0.28r 修正湿空气、0.81r 修正水汽对热容的贡献。

<!-- code_extract code_extract.py v1.1
source: phys/module_mp_thompson.F
ranges: L6065-L6085
file_lines: 6192
file_md5: f4ec64c511d6656277c4d1f9346813d1
display: line-numbered (strip L-prefix and !file: line to restore)
range_md5: 34f5af01b4f5ff2f1d3b94943c3ccba6
seg_lines: 21
-->

```fortran
!file: phys/module_mp_thompson.F    L6065-L6085
L06065  !
L06066        real function t_lcl(temp_K,tdew_K)
L06067  !..
L06068  !..         The following code was based on Bolton (1980) eqn #15
L06069  !..         and claims to have 0.1 K maximum error within -35 < T < 35 C
L06070  !..            temp_K  = Temperature in Kelvin
L06071  !..            tdew_K  = Dewpoint T at Lifting Condensation Level (K)
L06072  !..
L06073        IMPLICIT NONE
L06074  
L06075        real:: temp_K, tdew_K
L06076        real:: tt, tttd, denom
L06077  
L06078  !+---+
L06079  
L06080        tt = temp_K
L06081        tttd= tdew_K
L06082        denom= ( 1.0/(tttd-56.0) ) + (log(tt/tttd)/800.)
L06083        t_lcl = ( 1.0 / denom ) + 56.0
L06084        return
L06085        end
```

> `t_lcl`：Bolton **式 (15)**——由 (T, Td) 解析反解 LCL 温度（0.1 K 精度），`denom = 1/(Td−56) + ln(T/Td)/800` 的倒数结构来自 Clausius–Clapeyron 在 LCL 邻域的线性化。

<!-- code_extract code_extract.py v1.1
source: phys/module_mp_thompson.F
ranges: L6089-L6106
file_lines: 6192
file_md5: f4ec64c511d6656277c4d1f9346813d1
display: line-numbered (strip L-prefix and !file: line to restore)
range_md5: aeb75be21121b6ed28aa5810dbdb7fb3
seg_lines: 18
-->

```fortran
!file: phys/module_mp_thompson.F    L6089-L6106
L06089        real function t_dew(pres_Pa,w_non)
L06090  !..
L06091  !..            pres_Pa = Pressure in Pascals
L06092  !..            w_non   = mixing ratio (non-dimensional = kg/kg)
L06093  !..
L06094        IMPLICIT NONE
L06095  
L06096        real:: pres_Pa, w_non
L06097        real:: p, RR, ES, ESLN
L06098  
L06099  !+---+
L06100  
L06101        p = pres_Pa
L06102        RR=w_non+1e-8
L06103        ES=P*RR/(.622+RR)
L06104        ESLN=LOG(ES)
L06105        T_Dew=(35.86*ESLN-4947.2325)/(ESLN-23.6837)
L06106        return
```

> `t_dew`：由混合比反解露点——先 `es = p·r/(0.622+r)`（水汽分压，书 (2.2.10) 的形态），再 Magnus 型反演 `(35.86·ln es − 4947.2325)/(ln es − 23.6837)`。

<!-- code_extract code_extract.py v1.1
source: phys/module_mp_thompson.F
ranges: L6110-L6145
file_lines: 6192
file_md5: f4ec64c511d6656277c4d1f9346813d1
display: line-numbered (strip L-prefix and !file: line to restore)
range_md5: f8ec3df22ed40007f4c48ea6772dd358
seg_lines: 36
-->

```fortran
!file: phys/module_mp_thompson.F    L6110-L6145
L06110  !
L06111        real function theta_wetb(thetae_K)
L06112  !..
L06113  !..              Eqn below was gotten from polynomial fit to data in
L06114  !..              Smithsonian Meteorological Tables showing Theta-e
L06115  !..              and Theta-w
L06116  !..
L06117        IMPLICIT NONE
L06118  
L06119        real:: thetae_K
L06120        real:: x, answer
L06121  
L06122  !+---+
L06123  
L06124        real*8 c(0:6), d(0:6)
L06125        data c/-1.00922292e-10, -1.47945344e-8, -1.7303757e-6             &
L06126       &      ,-0.00012709,      1.15849867e-6, -3.518296861e-9           &
L06127       &      ,3.5741522e-12/
L06128        data d/0.00000000,   -3.5223513e-10, -5.7250807e-8                &
L06129       &     ,-5.83975422e-6, 4.72445163e-8, -1.13402845e-10              &
L06130       &     ,8.729580402e-14/
L06131  
L06132        x=min(475.0,thetae_K)
L06133             
L06134        if( x .le. 335.5 ) then
L06135           answer = c(0)+x*(c(1)+x*(c(2)+x*(c(3)+x*(c(4)+x*(c(5)+         &
L06136       &            x*c(6) )))))
L06137        else
L06138           answer = d(0)+x*(d(1)+x*(d(2)+x*(d(3)+x*(d(4)+x*(d(5)+         &
L06139       &            x*d(6) )))))
L06140        endif
L06141  
L06142        theta_wetb = answer + 273.15
L06143  
L06144        return
L06145        end
```

> `theta_wetb`：θe→θw（湿球位温）的**两段七次多项式**（Smithsonian 气象表拟合；335.5 K 分段、上限 475 K 截断）。主实体用它做 `compT_fr_The` 不收敛时的回退估算。

<!-- code_extract code_extract.py v1.1
source: phys/module_mp_thompson.F
ranges: L6148-L6187
file_lines: 6192
file_md5: f4ec64c511d6656277c4d1f9346813d1
display: line-numbered (strip L-prefix and !file: line to restore)
range_md5: 7744d5b9cfb40c8a68920bafd7be8a2c
seg_lines: 40
-->

```fortran
!file: phys/module_mp_thompson.F    L6148-L6187
L06148  !
L06149        real function compT_fr_The(thelcl_K,pres_Pa)
L06150  !..
L06151  !..            pres_Pa = Pressure in Pascals
L06152  !..            thelcl  = Theta-e at LCL (units in Kelvin)
L06153  !..
L06154  !..            Temperature (K) is returned given Theta-e at LCL
L06155  !..            and a pressure.  This describes a moist-adiabat.
L06156  !..            This temperature is the parcel temp at level Pres
L06157  !..            along moist adiabat described by theta-e.
L06158  !..
L06159        IMPLICIT NONE
L06160  
L06161        real:: thelcl_K, pres_Pa
L06162        real:: guess, epsilon, w1, w2, tenu, tenup, cor, thwlcl_K
L06163        integer:: iter
L06164  
L06165  !+---+
L06166  
L06167        guess= (thelcl_K - 0.5 * ( max(thelcl_K-270., 0.))**1.05)         &
L06168       &     * (pres_Pa/100000.0)**.2
L06169        epsilon=0.01
L06170        do iter=1,100
L06171           w1 = rslf(pres_Pa,guess)
L06172           w2 = rslf(pres_Pa,guess+1.)
L06173           tenu = theta_e(pres_Pa,guess,w1,guess)
L06174           tenup = theta_e(pres_Pa,guess+1,w2,guess+1.)
L06175           cor = (thelcl_K - tenu) / (tenup - tenu)
L06176           guess = guess + cor
L06177           if( (cor.lt.epsilon) .and. (-cor.lt.epsilon) ) then
L06178              compT_fr_The=guess
L06179              return
L06180           endif
L06181        enddo
L06182  !     print*, '  convergence not reached '
L06183        thwlcl_K=theta_wetb(thelcl_K)
L06184        compT_fr_The = thwlcl_K*((pres_Pa/100000.0)**0.286)
L06185  
L06186        return
L06187        end
```

> `compT_fr_The`：由 θe 与气压反解气块温度——“沿湿绝热线迭代”。**读这段必须知道一个源码事实**：L6172–L6173 调用 `theta_e(pres, guess, w1, guess)` 时**第四参数（应是 TLCL）传的是 guess 本身**——这不是笔误：饱和气块的 TLCL 就是自身温度，迭代过程把当前 guess 当饱和气块处理，“θe 沿湿绝热线不变”的隐式方程 `theta_e(p, T, w_s(T), T) = θe_given` 用割线法解（`cor = (目标−当前)/相邻差`）。100 次不收敛则退回 `θw·(p/p0)^0.286` 的干绝热外推——**低气压端（厚云顶）的兜底**。
> 收敛阈值 `epsilon=0.01`（0.01 K）；初值 `guess = (θe − 0.5·max(θe−270,0)^1.05)·(p/1e5)^0.2` 是经验初估。

## 07b.8 改造入口（→ 教材 ch20/ch21 案索引）

| 想改什么 | 动哪里 | 注意 |
|---|---|---|
| 碰并效率参数 | `table_Efrw/table_Efsw` 多项式段 | 改后必须删 `.dat` 缓存或开 `write_thompson_tables` 重新生成 |
| Bigg 冻结温度灵敏度 | `freezeH2O` 的 `T_adjust` 行 | 表四维含 IN，动订正即动全表 |
| 冰核化参数化换代 | `iceDeMott`（2010→2015 注释已留） | 注意返回单位换算 |
| 气溶胶活化敏感性 | `activ_ncloud` 的 `l/m` 死值 | 换 κ/半径需重做 CCN_ACTIVATE.BIN |
| 有效半径口径 | `calc_effectRad` 的三段 | 影响辐射方案（ch12 接口） |
| 雷达模拟 | `calc_refl10cm` | 亮带块依赖 `module_mp_radar` 的 Blahak 库 |
| 谱形改造 | 回 code_07a §07a.4.2 + 本篇各建表 | **表与谱参数必须成对改**——最高风险项 |

## 07b.9 上下游链接

- **上游（本模块内）**：code_07a——模块常数（各表维度与预存系数的出处）、主实体（各表运行时的用法）。
- **外部依赖**：`module_mp_radar`（`radar_init`、`rayleigh_soak_wetgraupel`、`nrbins/xxDs/xdts/simpson` 等反射率积分设施）；`CCN_ACTIVATE.BIN`（run 目录随附数据文件）。
- **教材**：ch11（饱和水汽压口径、气溶胶）、ch13（Thompson 精读、三口径对照、有效半径接口）、ch15（湿球温度与温湿参量的热力学基础）。
