# code_24 — 表面驱动器（module_surface_driver.F 两族 CASE 选段）

## 一、版本指纹

| 源文件 | 行数 | md5（整文件，按字节） |
|---|---|---|
| phys/module_surface_driver.F | 7428 | e86f31fb163f96f7b7f958865de1085c |

- 抽取工具：workspace/scripts/code_extract.py v1.2，2026-10-12；块首指纹注释自带 range_md5。
- 本篇 B 级两族选段：主入口 surface_driver（L7–4619）中只收「面层方案族 sfclay_select 全 CASE」与「陆面方案族 sfc_select 的 SLAB+Noah 代表段」，加前处理、收尾与 MYNN 海冰 wrapper；不收 L7–2066 的哑元声明区（各方案的完整实参表即 CASE 内的 CALL 本身）与其余六个 LSM CASE（NoahMP/RUC/PX/CLM/CTSM/SSIB，结构同 Noah，教材 [ch16_land_surface_family.md](../ch16_land_surface_family.md) 差异表覆盖）。

## 二、定位

一句话：五大 physics driver 之一——面层方案（sf_sfclay_physics）与陆面方案（sf_surface_physics）两族 CASE 的总调度，外加海冰/SST/湖泊/海洋混合层/坡地辐射/人为热等「近地面杂项」的枢纽。

**谁在调它**：dyn_em/module_first_rk_step_part1.F 在 pbl_driver **之前**调用（物理时序：surface → pbl，[ch21_solve_em_dynamics.md](../ch21_solve_em_dynamics.md)）。下游两族：面层 → [code_10_module_sf_mynnsfc.md](code_10_module_sf_mynnsfc.md)（MYNN）等；陆面 → Noah（12/13 篇待交付）等；城市冠层经 pbl_driver 的 BEP 路径（[code_14a_module_sf_bep_bem.md](code_14a_module_sf_bep_bem.md)）。

**两族 SELECT CASE 方案号对照**（Registry 实测）：

| sf_sfclay_physics | 方案 | sf_surface_physics | 方案 |
|---|---|---|---|
| 1 | SFCLAY（旧） | 1 | 5-layer thermal diffusion（SLAB） |
| 2 | MYJ | 2 | Noah（LSMSCHEME） |
| 3 | GFS | 3 | NoahMP |
| 4 | QNSE | 4 | RUC |
| 5 | MYNN（[code_10](code_10_module_sf_mynnsfc.md)） | 7 | PX |
| 7 | PX | 8 | CLM4 |
| 10 | TEMF | 9 | CTSM |
| 11 | ShinHong | 6 | SSIB |
| 91 | SFCLAY（rev） | 0 | off |

## 三、前处理：耦合、灌溉、SST 与海冰

<!-- code_extract code_extract.py v1.2
source: phys/module_surface_driver.F
ranges: L1570-L1780
file_lines: 7428
file_md5: e86f31fb163f96f7b7f958865de1085c
display: line-numbered (strip L-prefix and !file: line to restore)
range_md5: f16138652fefcc062daefaba1b2a2877
seg_lines: 211
-->

```fortran
!file: phys/module_surface_driver.F    L1570-L1780
L01570    IF ( coupler_on .and. present(cplmask) .and. present(sst_input) ) THEN
L01571       
L01572       CALL cpl_rcv( id, 'SST',            &
L01573          &              ids, ide, jds, jde, kds, kde, &
L01574          &              ims, ime, jms, jme, kms, kme, &
L01575          &              ips, ipe, jps, jpe, kps, kpe, &
L01576          &              max_edom, cplmask, SST, SST_INPUT )
L01577       
L01578       CALL cpl_rcv( id, 'UOCE',            &
L01579          &              ids, ide, jds, jde, kds, kde, &
L01580          &              ims, ime, jms, jme, kms, kme, &
L01581          &              ips, ipe, jps, jpe, kps, kpe, &
L01582          &              max_edom, cplmask, UOCE )
L01583       
L01584       CALL cpl_rcv( id, 'VOCE',            &
L01585          &              ids, ide, jds, jde, kds, kde, &
L01586          &              ims, ime, jms, jme, kms, kme, &
L01587          &              ips, ipe, jps, jpe, kps, kpe, &
L01588          &              max_edom, cplmask, VOCE )
L01589       
L01590    END IF
L01591  
L01592  #if (EM_CORE==1)
L01593       spp_lsm_loc = spp_lsm
L01594  #else
L01595       spp_lsm_loc = 0
L01596  #endif
L01597  
L01598    
L01599  !$OMP PARALLEL DO &
L01600  !$OMP PRIVATE (ij, i, j, k)
L01601    DO ij = 1,num_tiles
L01602      DO j = j_start(ij),j_end(ij)
L01603        DO k = kms,kme
L01604          DO i = i_start(ij),i_end(ij)
L01605            v_phytmp(i, k, j) = 0.
L01606            u_phytmp(i, k, j) = 0.
L01607          ENDDO
L01608        ENDDO
L01609        DO i = i_start(ij),i_end(ij)
L01610           QGH(i,j) = 0.
L01611           CHS(i,j) = 0.
L01612           CPM(i,j) = 0.
L01613           CHS2(i,j) = 0.
L01614        ENDDO
L01615      ENDDO
L01616    ENDDO
L01617    DTMIN = 0.
L01618    DTBL = 0.
L01619  
L01620  ! RAINBL in mm (Accumulation between PBL calls)
L01621  
L01622    IF ( PRESENT( rainncv ) .AND. PRESENT( rainbl ) ) THEN
L01623      !$OMP PARALLEL DO   &
L01624      !$OMP PRIVATE ( ij, i, j, k )
L01625      DO ij = 1 , num_tiles
L01626        DO j=j_start(ij),j_end(ij)
L01627        DO i=i_start(ij),i_end(ij)
L01628           RAINBL(i,j) = RAINBL(i,j) + RAINCV(i,j) + RAINNCV(i,j)
L01629           IF ( PRESENT( rainshv ))RAINBL(i,j) = RAINBL(i,j) + RAINSHV(i,j)
L01630           RAINBL(i,j) = MAX (RAINBL(i,j), 0.0)
L01631  #if (EM_CORE==1)
L01632           IRRIGATION_CHANNEL(i,j) = 0.
L01633           sf_surf_irr: SELECT CASE(sf_surf_irr_scheme)
L01634              CASE(DRIP)
L01635                 CALL drip_irrigation(                                     &
L01636                  &  julian_in,IRRIGATION(i,j),sf_surf_irr_scheme,         &
L01637                  &  irr_daily_amount,irr_start_hour,irr_num_hours,        &
L01638                  &  irr_start_julianday,irr_end_julianday,                &
L01639                  &  irr_freq,irr_ph,i,j,RAINBL(i,j),                      &
L01640                  &  IRRIGATION_CHANNEL(i,j),gmt,xtime,dt,                 &
L01641                  &  irr_rand_field(i,j)                                   &
L01642                     )
L01643              CASE(CHANNEL)
L01644                 CALL channel_irrigation(                                  &
L01645                  &  julian_in,IRRIGATION(i,j),sf_surf_irr_scheme,         &
L01646                  &  irr_daily_amount,irr_start_hour,irr_num_hours,        &
L01647                  &  irr_start_julianday,irr_end_julianday,                &
L01648                  &  irr_freq,irr_ph,i,j,RAINBL(i,j),                      &
L01649                  &  IRRIGATION_CHANNEL(i,j),gmt,xtime,dt,                 &
L01650                  &  irr_rand_field(i,j)                                   &
L01651                     )
L01652             END SELECT sf_surf_irr
L01653  #endif
L01654        ENDDO
L01655        ENDDO
L01656      ENDDO
L01657      !$OMP END PARALLEL DO
L01658    ELSE IF ( PRESENT( rainbl ) ) THEN
L01659      !$OMP PARALLEL DO   &
L01660      !$OMP PRIVATE ( ij, i, j, k )
L01661      DO ij = 1 , num_tiles
L01662        DO j=j_start(ij),j_end(ij)
L01663        DO i=i_start(ij),i_end(ij)
L01664           RAINBL(i,j) = RAINBL(i,j) + RAINCV(i,j)
L01665           IF ( PRESENT( rainshv ))RAINBL(i,j) = RAINBL(i,j) + RAINSHV(i,j)
L01666           RAINBL(i,j) = MAX (RAINBL(i,j), 0.0)
L01667  
L01668  #if (EM_CORE==1)
L01669            sf_surf_irr1: SELECT CASE(sf_surf_irr_scheme)
L01670               CASE(DRIP)
L01671                 CALL drip_irrigation(                                     &
L01672                  &  julian_in,IRRIGATION(i,j),sf_surf_irr_scheme,         &
L01673                  &  irr_daily_amount,irr_start_hour,irr_num_hours,        &
L01674                  &  irr_start_julianday,irr_end_julianday,                &
L01675                  &  irr_freq,irr_ph,i,j,RAINBL(i,j),                      &
L01676                  &  IRRIGATION_CHANNEL(i,j),gmt,xtime,dt,                 &
L01677                  &  irr_rand_field(i,j)                                   &
L01678                     )
L01679  
L01680              CASE(CHANNEL)
L01681                 CALL channel_irrigation(                                  &
L01682                  &  julian_in,IRRIGATION(i,j),sf_surf_irr_scheme,         &
L01683                  &  irr_daily_amount,irr_start_hour,irr_num_hours,        &
L01684                  &  irr_start_julianday,irr_end_julianday,                &
L01685                  &  irr_freq,irr_ph,i,j,RAINBL(i,j),                      &
L01686                  &  IRRIGATION_CHANNEL(i,j),gmt,xtime,dt,                 &
L01687                  &  irr_rand_field(i,j)                                   &
L01688                     )
L01689          END SELECT sf_surf_irr1
L01690  #endif
L01691  
L01692        ENDDO
L01693        ENDDO
L01694      ENDDO
L01695      !$OMP END PARALLEL DO
L01696    ENDIF
L01697  ! Update SST
L01698    IF (sst_update .EQ. 1) THEN
L01699      CALL wrf_debug( 100, 'SST_UPDATE is on' )
L01700      !$OMP PARALLEL DO   &
L01701      !$OMP PRIVATE ( ij, i, j, k )
L01702      DO ij = 1 , num_tiles
L01703        DO j=j_start(ij),j_end(ij)
L01704        DO i=i_start(ij),i_end(ij)
L01705   ! check for lake model 
L01706  #if (EM_CORE==1)
L01707            if ( lakemodel==1) then
L01708              if(lakemask(i,j).eq.1.) then
L01709                if ( xice(i,j).gt.xice_threshold) then   !mchen
L01710                     xice(i,j)=0.0
L01711                 endif
L01712               endif
L01713            endif 
L01714  #else
L01715            if ( lakemodel==1) then
L01716              if(ht(i,j)>=lake_min_elev) then
L01717                if ( xice(i,j).gt.xice_threshold) then   !mchen
L01718                     xice(i,j)=0.0
L01719                 endif
L01720               endif
L01721            endif 
L01722  #endif
L01723  ! end check lake model    
L01724           XICE_save(I,J) = XICEM(I,J) 
L01725  
L01726           IF ( FRACTIONAL_SEAICE == 1 ) then
L01727              IF ( ( XICE(I,J) .NE. XICEM(I,J) ) .AND. ( XICEM(I,J) .GT. XICE_THRESHOLD ) ) THEN
L01728                 ! Fractional values of ALBEDO and EMISSIVITY are valid according to the 
L01729                 ! earlier fractional seaice value, XICEM.  Recompute them for the new 
L01730                 ! seaice value XICE.
L01731                  IF ( SEAICE_ALBEDO_OPT ==2 ) THEN
L01732                      IF ( ALBSI(I,J) < -1.E6 ) THEN
L01733                          call wrf_error_fatal("Field ALBSI not found in input.  Field ALBSI is required if SEAICE_ALBEDO_OPT=2")
L01734                      ENDIF
L01735                      ALBEDO(I,J) = 0.08 + XICE(I,J)/XICEM(I,J) * ( ALBSI(I,J) - 0.08 )
L01736                  ELSE
L01737                      ALBEDO(I,J) = 0.08 + XICE(I,J)/XICEM(I,J) * ( ALBEDO(I,J) - 0.08 )
L01738                  ENDIF
L01739                  EMISS (I,J) = 0.98 + XICE(I,J)/XICEM(I,J) * ( EMISS (I,J) - 0.98 )
L01740  ! use old tsk from seaice part
L01741                  TSK(I,J) = TSK_SAVE(I,J)*XICE(I,J) + (1.-XICE(I,J))*SST(I,J)
L01742              ENDIF
L01743           ENDIF
L01744  
L01745          IF ( XLAND(i,j) .GT. 1.5 .AND. XICE(I,J) .GE. XICE_THRESHOLD .AND. XICEM(I,J) .LT. XICE_THRESHOLD ) THEN
L01746            ! water point turns to sea-ice point
L01747            XICEM(I,J) = XICE(I,J)
L01748            XLAND(I,J) = 1.
L01749            IVGTYP(I,J) = ISICE
L01750            ISLTYP(I,J) = 16
L01751            VEGFRA(I,J) = 0.
L01752            TMN(I,J) = 271.4
L01753  
L01754            ! Over new ice, initial guesses of ALBEDO and EMISS are
L01755            ! based on default water and ice values for albedo and
L01756            ! emissivity.  The land-surface schemes can update these
L01757            ! values
L01758  
L01759            SELECT CASE ( SEAICE_ALBEDO_OPT )
L01760            CASE ( 0, 1 )
L01761  
L01762                ALBEDO(I,J) = SEAICE_ALBEDO_DEFAULT * XICE(I,J) + 0.08 * ( 1.0-XICE(I,J) )
L01763                ALBBCK(I,J) = SEAICE_ALBEDO_DEFAULT
L01764  
L01765            CASE ( 2 ) 
L01766                
L01767                IF ( ALBSI(I,J) < -1.E6 ) THEN
L01768                    call wrf_error_fatal("Field ALBSI not found in input.  Field ALBSI is required if SEAICE_ALBEDO_OPT=2")
L01769                ENDIF
L01770  
L01771                ALBEDO(I,J) = ALBSI(I,J) * XICE(I,J) + 0.08 * ( 1.0-XICE(I,J) )
L01772                ALBBCK(I,J) = ALBSI(I,J)
L01773  
L01774            END SELECT
L01775  
L01776            EMISS(I,J)  = 0.98 * XICE(I,J) + 0.98 * ( 1.0-XICE(I,J) )
L01777            EMBCK(I,J)  = 0.98
L01778            DO nk = 1, num_soil_layers
L01779              TSLB(I,NK,J) = TSK(I,J)
L01780              SMOIS(I,NK,J) = 1.0
```

> 讲解：①**区域耦合器**（coupler_on）：cpl_rcv 收 OASIS 型外部 SST/海流——区域气候嵌套场景的进场口；②**灌溉**：sf_surf_irr 两级 SELECT（drip_irrigation/channel_irrigation），RAINBL 在此先累加对流+大尺度降水（RAINBL=RAINNCV+RAINSHV——陆面方案的水量输入在此结账）；③**SST_UPDATE=1**：从 wrfbdy/wrfinput 读逐时 SST，分数海冰（FRACTIONAL_SEAICE=1）时 XICEM 新冰出现/消失触发 TSK 与反照率重算，SEAICE_ALBEDO_OPT 三选。这一段是「下边界外源」的全部进场通道——做 SST/海冰敏感性实验（论文 2 的 lake/river 处理同源）改这里。

## 四、面层方案族 sfclay_select（全 CASE）

<!-- code_extract code_extract.py v1.2
source: phys/module_surface_driver.F
ranges: L2067-L2555
file_lines: 7428
file_md5: e86f31fb163f96f7b7f958865de1085c
display: line-numbered (strip L-prefix and !file: line to restore)
range_md5: 0021b9ded4eed5a8b6029349764e2e04
seg_lines: 489
-->

```fortran
!file: phys/module_surface_driver.F    L2067-L2555
L02067       CASE (SFCLAYSCHEME)
L02068  ! DX varies spatially in NMM, therefore, SFCLAY cannot be called
L02069  ! because it takes a scalar DX. NMM passes in a dummy value for this
L02070  ! scalar.  NEEDS FURTHER ATTENTION. JM 20050215
L02071         IF(PRESENT(SCM_FORCE_FLUX))THEN
L02072           IF (scm_force_flux .EQ. 1) THEN
L02073  ! surface forcing by observed fluxes
L02074           CALL scmflux(u_phytmp, v_phytmp, t_phy, qv_curr, p_phy, dz8w,   &
L02075                       cp, rcp, xlv, psfc, cpm, xland,                     &
L02076                       psim, psih, hfx, qfx, lh, tsk, flhc, flqc,          &
L02077                       znt, gz1oz0, wspd,                                  &
L02078                       julian_in, karman, p1000mb,                         &
L02079                       itimestep,chklowq,                                  &
L02080                       ids, ide, jds, jde, kds, kde,                       &
L02081                       ims, ime, jms, jme, kms, kme,                       &
L02082                       i_start(ij),i_end(ij), j_start(ij),j_end(ij), kts,kte   )
L02083           ENDIF
L02084         ENDIF
L02085         IF(PRESENT(SCM_FORCE_SKINTEMP))THEN
L02086           IF (scm_force_skintemp .EQ. 1) THEN
L02087  ! surface forcing by observed skin temperature
L02088           CALL scmskintemp(tsk, julian_in, itimestep,                     &
L02089                       ids, ide, jds, jde, kds, kde,                       &
L02090                       ims, ime, jms, jme, kms, kme,                       &
L02091                       i_start(ij),i_end(ij), j_start(ij),j_end(ij), kts,kte   )
L02092           ENDIF
L02093  !         IF (scm_force_skintemp .EQ. 2) THEN
L02094  ! surface forcing by gabls2 skin temperature
L02095  !         CALL scmgabls2(tsk, itimestep, dt,                              &
L02096  !                     ids, ide, jds, jde, kds, kde,                       &
L02097  !                     ims, ime, jms, jme, kms, kme,                       &
L02098  !                     i_start(ij),i_end(ij), j_start(ij),j_end(ij), kts,kte   )
L02099  !         ENDIF
L02100         ENDIF
L02101         IF (PRESENT(qv_curr)                            .AND.    &
L02102             PRESENT(mol)        .AND.  PRESENT(regime)  .AND.    &
L02103                                                        .TRUE. ) THEN
L02104           CALL wrf_debug( 100, 'in SFCLAY' )
L02105           IF ( FRACTIONAL_SEAICE == 1 ) THEN
L02106              CALL SFCLAY_SEAICE_WRAPPER(u_phytmp,v_phytmp,t_phy,qv_curr,&
L02107                   p_phy,dz8w,cp,g,rcp,r_d,xlv,psfc,chs,chs2,cqs2,cpm, &
L02108                   znt,ust,pblh,mavail,zol,mol,regime,psim,psih,fm,fhh, &
L02109                   xland,hfx,qfx,lh,tsk,flhc,flqc,qgh,qsfc,rmol,       &
L02110                   u10,v10,th2,t2,q2,                                  &
L02111                   gz1oz0,wspd,br,isfflx,dx2d,                         &
L02112                   svp1,svp2,svp3,svpt0,ep_1,ep_2,karman,eomeg,stbolt, &
L02113                   P1000mb,lakemask,                                   &
L02114                   XICE,SST,TSK_SEA,                                                  &
L02115                   CHS2_SEA,CHS_SEA,CPM_SEA,CQS2_SEA,FLHC_SEA,FLQC_SEA,               &
L02116                   HFX_SEA,LH_SEA,QFX_SEA,QGH_SEA,QSFC_SEA,ZNT_SEA,                   &
L02117                   ITIMESTEP,TICE2TSK_IF2COLD,XICE_THRESHOLD,                         &
L02118                   ids,ide, jds,jde, kds,kde,                          &
L02119                   ims,ime, jms,jme, kms,kme,                          &
L02120                   i_start(ij),i_end(ij), j_start(ij),j_end(ij), kts,kte,    &
L02121                   ustm,ck,cka,cd,cda,isftcflx,iz0tlnd,scm_force_flux, &
L02122                   sf_surface_physics  )
L02123           ELSE
L02124           CALL SFCLAY(u_phytmp,v_phytmp,t_phy,qv_curr,              &
L02125                 p_phy,dz8w,cp,g,rcp,r_d,xlv,psfc,chs,chs2,cqs2,cpm, &
L02126                 znt,ust,pblh,mavail,zol,mol,regime,psim,psih,fm,fhh, &
L02127                 xland,hfx,qfx,lh,tsk,flhc,flqc,qgh,qsfc,rmol,       &
L02128                 u10,v10,th2,t2,q2,                                  &
L02129                 gz1oz0,wspd,br,isfflx,dx2d,                         &
L02130                 svp1,svp2,svp3,svpt0,ep_1,ep_2,karman,eomeg,stbolt, &
L02131                 P1000mb,lakemask,                                   &
L02132                 ids,ide, jds,jde, kds,kde,                          &
L02133                 ims,ime, jms,jme, kms,kme,                          &
L02134                 i_start(ij),i_end(ij), j_start(ij),j_end(ij), kts,kte,    &
L02135                 ustm,ck,cka,cd,cda,isftcflx,iz0tlnd,scm_force_flux  ) 
L02136  #if ( EM_CORE==1)
L02137             DO j = j_start(ij),j_end(ij)
L02138             DO i = i_start(ij),i_end(ij)
L02139               ch(i,j) = chs (i,j)
L02140  !!             ch(i,j) = flhc(i,j)/( cpm(i,j)*rho(i,kts,j) )
L02141             end do
L02142             end do
L02143  #endif
L02144           ENDIF
L02145         ELSE
L02146           CALL wrf_error_fatal('Lacking arguments for SFCLAY in surface driver')
L02147         ENDIF
L02148  
L02149       CASE (SFCLAYREVSCHEME)
L02150  ! DX varies spatially in NMM, therefore, SFCLAY cannot be called
L02151  ! because it takes a scalar DX. NMM passes in a dummy value for this
L02152  ! scalar.  NEEDS FURTHER ATTENTION. JM 20050215
L02153         IF (PRESENT(qv_curr)                            .AND.    &
L02154             PRESENT(mol)        .AND.  PRESENT(regime)  .AND.    &
L02155                                                        .TRUE. ) THEN
L02156           CALL wrf_debug( 100, 'in SFCLAY' )
L02157  
L02158           IF ( FRACTIONAL_SEAICE == 1 ) THEN
L02159              CALL SFCLAYREV_SEAICE_WRAPPER(u_phytmp,v_phytmp,t_phy,qv_curr,&
L02160                   p_phy,dz8w,cp,g,rcp,r_d,xlv,psfc,chs,chs2,cqs2,cpm, &
L02161                   znt,ust,pblh,mavail,zol,mol,regime,psim,psih,fm,fhh, &
L02162                   xland,hfx,qfx,lh,tsk,flhc,flqc,qgh,qsfc,rmol,       &
L02163                   u10,v10,th2,t2,q2,                                  &
L02164                   gz1oz0,wspd,br,isfflx,dx2d,                         &
L02165                   svp1,svp2,svp3,svpt0,ep_1,ep_2,karman,              &
L02166                   P1000mb,lakemask,                                   &
L02167                   kim_tofd, tofd_factor, var2d,                       &
L02168                   XICE,SST,TSK_SEA,                                                  &
L02169                   CHS2_SEA,CHS_SEA,CPM_SEA,CQS2_SEA,FLHC_SEA,FLQC_SEA,               &
L02170                   HFX_SEA,LH_SEA,QFX_SEA,QGH_SEA,QSFC_SEA,ZNT_SEA,                   &
L02171                   ITIMESTEP,TICE2TSK_IF2COLD,XICE_THRESHOLD,                         &
L02172                   ids,ide, jds,jde, kds,kde,                          &
L02173                   ims,ime, jms,jme, kms,kme,                          &
L02174                   i_start(ij),i_end(ij), j_start(ij),j_end(ij), kts,kte,    &
L02175                   ustm,ck,cka,cd,cda,isftcflx,iz0tlnd,                &
L02176                   shalwater_z0,water_depth,                           & 
L02177                   scm_force_flux,sf_surface_physics,errmsg,errflg     )
L02178           ELSE
L02179           CALL SFCLAYREV(u_phytmp,v_phytmp,t_phy,qv_curr,&
L02180                 p_phy,dz8w,cp,g,rcp,r_d,xlv,psfc,chs,chs2,cqs2,cpm, &
L02181                 znt,ust,pblh,mavail,zol,mol,regime,psim,psih,fm,fhh, &
L02182                 xland,hfx,qfx,lh,tsk,flhc,flqc,qgh,qsfc,rmol,       &
L02183                 u10,v10,th2,t2,q2,                                  &
L02184                 gz1oz0,wspd,br,isfflx,dx2d,                         &
L02185                 svp1,svp2,svp3,svpt0,ep_1,ep_2,karman,              &
L02186                 P1000mb,lakemask,                                   &
L02187                 kim_tofd, tofd_factor, var2d,                       &
L02188                 ids,ide, jds,jde, kds,kde,                          &
L02189                 ims,ime, jms,jme, kms,kme,                          &
L02190                 i_start(ij),i_end(ij), j_start(ij),j_end(ij), kts,kte,    &
L02191                 ustm,ck,cka,cd,cda,isftcflx,iz0tlnd,                &
L02192                 shalwater_z0,water_depth,                           & 
L02193                 scm_force_flux,errmsg,errflg                        ) 
L02194  #if ( EM_CORE==1)
L02195             DO j = j_start(ij),j_end(ij)
L02196             DO i = i_start(ij),i_end(ij)
L02197               ch(i,j) = chs (i,j)
L02198  !!             ch(i,j) = flhc(i,j)/( cpm(i,j)*rho(i,kts,j) )
L02199             end do
L02200             end do
L02201  #endif
L02202           ENDIF
L02203         ELSE
L02204           CALL wrf_error_fatal('Lacking arguments for SFCLAY in surface driver')
L02205         ENDIF
L02206  
L02207       CASE (PXSFCSCHEME)
L02208         IF (PRESENT(qv_curr)                            .AND.    &
L02209             PRESENT(mol)        .AND.  PRESENT(regime)  .AND.    &
L02210                                                        .TRUE. ) THEN
L02211           CALL wrf_debug( 100, 'in PX Surface Layer scheme' )
L02212           IF ( FRACTIONAL_SEAICE == 1 ) THEN
L02213              CALL PXSFCLAY_SEAICE_WRAPPER(u_phytmp,v_phytmp,t_phy,th_phy,qv_curr,&
L02214                   p_phy,dz8w,cp,g,rcp,r_d,xlv,psfc,chs,chs2,cqs2,cpm, &
L02215                   znt,ust,pblh,mavail,zol,mol,regime,psim,psih,       &
L02216                   xland,hfx,qfx,lh,tsk,flhc,flqc,qgh,qsfc,rmol,       &
L02217                   u10,v10,                                            &
L02218                   gz1oz0,wspd,br,isfflx,dx,                           &
L02219                   svp1,svp2,svp3,svpt0,ep_1,ep_2,karman,              &
L02220                   XICE, SST, ITIMESTEP, TICE2TSK_IF2COLD,XICE_THRESHOLD, &
L02221                   CHS_SEA, CHS2_SEA, CPM_SEA, CQS2_SEA,FLHC_SEA,FLQC_SEA,&
L02222                   HFX_SEA, LH_SEA, QFX_SEA, QGH_SEA, QSFC_SEA, TSK_SEA,  &
L02223                   ids,ide, jds,jde, kds,kde,                          &
L02224                   ims,ime, jms,jme, kms,kme,                          &
L02225                   i_start(ij),i_end(ij), j_start(ij),j_end(ij), kts,kte    )
L02226           ELSE
L02227           CALL PXSFCLAY(u_phytmp,v_phytmp,t_phy,th_phy,qv_curr,&
L02228                 p_phy,dz8w,cp,g,rcp,r_d,xlv,psfc,chs,chs2,cqs2,cpm, &
L02229                 znt,ust,pblh,mavail,zol,mol,regime,psim,psih,       &
L02230                 xland,hfx,qfx,lh,tsk,flhc,flqc,qgh,qsfc,rmol,       &
L02231                 u10,v10,                                            &
L02232                 gz1oz0,wspd,br,isfflx,dx,                           &
L02233                 svp1,svp2,svp3,svpt0,ep_1,ep_2,karman,itimestep,    &
L02234                 ids,ide, jds,jde, kds,kde,                          &
L02235                 ims,ime, jms,jme, kms,kme,                          &
L02236                 i_start(ij),i_end(ij), j_start(ij),j_end(ij), kts,kte    )
L02237           ENDIF
L02238         ELSE
L02239           CALL wrf_error_fatal('Lacking arguments for PX Surface Layer in surface driver')
L02240         ENDIF
L02241  
L02242        CASE (MYJSFCSCHEME)
L02243         IF (PRESENT(qv_curr)    .AND.  PRESENT(qc_curr) .AND.    &
L02244                                                        .TRUE. ) THEN
L02245  
L02246          CALL wrf_debug(100,'in MYJSFC')
L02247          IF ( FRACTIONAL_SEAICE == 1 ) THEN
L02248             CALL MYJSFC_SEAICE_WRAPPER(itimestep,ht,dz8w,             &
L02249                  p_phy,p8w,th_phy,t_phy,                              &
L02250                  qv_curr,qc_curr,                                     &
L02251                  u_phy,v_phy,tke_pbl,                                 &
L02252                  tsk,qsfc,thz0,qz0,uz0,vz0,                           &
L02253                  lowlyr,                                              &
L02254                  xland,ivgtyp,isurban,iz0tlnd,                        &
L02255                  TICE2TSK_IF2COLD,                                    & ! Extra for wrapper.
L02256                  XICE_THRESHOLD,                                      & ! Extra for wrapper.
L02257                  XICE, SST,                                           & ! Extra for wrapper.
L02258                  CHS_SEA, CHS2_SEA, CQS2_SEA, CPM_SEA,            &
L02259                  FLHC_SEA, FLQC_SEA, QSFC_SEA, &
L02260                  QGH_SEA, QZ0_SEA, HFX_SEA, QFX_SEA, LH_SEA,         &
L02261                  TSK_SEA,                                             &
L02262                  ust,znt,z0,pblh,mavail,rmol,                         &
L02263                  akhs,akms,                                           &
L02264                  br,                                                 &
L02265                  chs,chs2,cqs2,hfx,qfx,lh,flhc,flqc,qgh,cpm,ct,       &
L02266                  u10,v10,t2,th2,tshltr,th10,q2,qshltr,q10,pshltr,               &
L02267                  p1000mb,u10e,v10e,                                   &
L02268                  ids,ide, jds,jde, kds,kde,                           &
L02269                  ims,ime, jms,jme, kms,kme,                           &
L02270                  i_start(ij),i_end(ij), j_start(ij),j_end(ij), kts,kte    )
L02271          ELSE
L02272              CALL MYJSFC(itimestep,ht,dz8w,                         &
L02273                p_phy,p8w,th_phy,t_phy,                              &
L02274                qv_curr,qc_curr,                                      &
L02275                u_phy,v_phy,tke_pbl,                                 &
L02276                tsk,qsfc,thz0,qz0,uz0,vz0,                           &
L02277                lowlyr,                                              &
L02278                xland,ivgtyp,isurban,iz0tlnd,                        &
L02279                ust,znt,z0,pblh,mavail,rmol,                         &
L02280                akhs,akms,                                           &
L02281                br,                                                 &
L02282                chs,chs2,cqs2,hfx,qfx,lh,flhc,flqc,qgh,cpm,ct,       &
L02283                u10,v10,t2,th2,tshltr,th10,q2,qshltr,q10,pshltr,               &
L02284                p1000mb,u10e,v10e,                                   &
L02285                ids,ide, jds,jde, kds,kde,                           &
L02286                ims,ime, jms,jme, kms,kme,                           &
L02287                i_start(ij),i_end(ij), j_start(ij),j_end(ij), kts,kte    )
L02288          ENDIF
L02289  !       ustm is needed for LES tke calculation (ustm is ust used in friction)
L02290           DO j = j_start(ij),j_end(ij)
L02291              DO i = i_start(ij),i_end(ij)
L02292                 ustm(i,j) = ust(i,j)
L02293                 wspd(i,j) = MAX(SQRT(u_phy(i,kts,j)**2+v_phy(i,kts,j)**2),0.001)
L02294                 ch(i,j) = chs (i,j)
L02295              END DO
L02296           END DO
L02297         ELSE
L02298           CALL wrf_error_fatal('Lacking arguments for MYJSFC in surface driver')
L02299         ENDIF
L02300  
L02301        CASE (QNSESFCSCHEME)
L02302         IF(PRESENT(SCM_FORCE_FLUX))THEN
L02303           IF (scm_force_flux .EQ. 1) THEN
L02304  ! surface forcing by observed fluxes
L02305           CALL scmflux(u_phytmp, v_phytmp, t_phy, qv_curr, p_phy, dz8w,   &
L02306                       cp, rcp, xlv, psfc, cpm, xland,                     &
L02307                       psim, psih, hfx, qfx, lh, tsk, flhc, flqc,          &
L02308                       znt, gz1oz0, wspd,                                  &
L02309                       julian_in, karman, p1000mb,                         &
L02310                       itimestep,chklowq,                                  &
L02311                       ids, ide, jds, jde, kds, kde,                       &
L02312                       ims, ime, jms, jme, kms, kme,                       &
L02313                       i_start(ij),i_end(ij), j_start(ij),j_end(ij), kts,kte   )
L02314           ENDIF
L02315         ENDIF
L02316         IF(PRESENT(SCM_FORCE_SKINTEMP))THEN
L02317           IF (scm_force_skintemp .EQ. 1) THEN
L02318  ! surface forcing by observed skin temperature
L02319           CALL scmskintemp(tsk, julian_in, itimestep,                     &
L02320                       ids, ide, jds, jde, kds, kde,                       &
L02321                       ims, ime, jms, jme, kms, kme,                       &
L02322                       i_start(ij),i_end(ij), j_start(ij),j_end(ij), kts,kte   )
L02323           ENDIF
L02324         ENDIF
L02325  
L02326         IF (PRESENT(qv_curr)    .AND.  PRESENT(qc_curr) .AND.    &
L02327                                                        .TRUE. ) THEN
L02328              CALL wrf_debug(100,'in QNSESFC')
L02329               IF ( FRACTIONAL_SEAICE == 1 ) THEN
L02330             CALL QNSESFC_SEAICE_WRAPPER(itimestep,ht,dz8w,             &
L02331                  p_phy,p8w,th_phy,t_phy,                              &
L02332                  qv_curr,qc_curr,                                     &
L02333                  u_phy,v_phy,tke_pbl,                                 &
L02334                  tsk,qsfc,thz0,qz0,uz0,vz0,                           &
L02335                  lowlyr,                                              &
L02336                  xland,                                               &
L02337                  TICE2TSK_IF2COLD,                                    & ! Extra for wrapper.
L02338                  XICE_THRESHOLD,                                      & ! Extra for wrapper.
L02339                  XICE, SST,                                           & ! Extra for wrapper.
L02340                  CHS_SEA, CHS2_SEA, CQS2_SEA, CPM_SEA,            &
L02341                  FLHC_SEA, FLQC_SEA, QSFC_SEA, &
L02342                  QGH_SEA, QZ0_SEA, HFX_SEA, QFX_SEA, LH_SEA,         &
L02343                  TSK_SEA,                                             &
L02344                  ust,znt,z0,pblh,mavail,rmol,                         &
L02345                  akhs,akms,                                           &
L02346                  br,                                                 &
L02347                  chs,chs2,cqs2,hfx,qfx,lh,flhc,flqc,qgh,cpm,ct,       &
L02348                  u10,v10,t2,th2,tshltr,th10,q2,qshltr,q10,pshltr,     &
L02349                  u10e,v10e,                                           &
L02350                  ids,ide, jds,jde, kds,kde,                           &
L02351                  ims,ime, jms,jme, kms,kme,                           &
L02352                  i_start(ij),i_end(ij), j_start(ij),j_end(ij), kts,kte,SCM_FORCE_FLUX    )
L02353             ELSE
L02354              CALL QNSESFC(itimestep,ht,dz8w,                         &
L02355                p_phy,p8w,th_phy,t_phy,                              &
L02356                qv_curr,qc_curr,                                     &
L02357                u_phy,v_phy,tke_pbl,                                 &
L02358                tsk,qsfc,thz0,qz0,uz0,vz0,                           &
L02359                lowlyr,                                              &
L02360                xland,                                               &
L02361                ust,znt,z0,pblh,mavail,rmol,                         &
L02362                akhs,akms,                                           &
L02363                br,                                                 &
L02364                chs,chs2,cqs2,hfx,qfx,lh,flhc,flqc,qgh,cpm,ct,       &
L02365                u10,v10,t2,th2,tshltr,th10,q2,qshltr,q10,pshltr,     &
L02366                u10e,v10e,                                           &
L02367                ids,ide, jds,jde, kds,kde,                           &
L02368                ims,ime, jms,jme, kms,kme,                           &
L02369                i_start(ij),i_end(ij), j_start(ij),j_end(ij),     &
L02370                kts,kte,scm_force_flux    )
L02371             ENDIF
L02372  #if ( EM_CORE==1)
L02373           DO j = j_start(ij),j_end(ij)
L02374              DO i = i_start(ij),i_end(ij)
L02375                 wspd(i,j) = MAX(SQRT(u_phy(i,kts,j)**2+v_phy(i,kts,j)**2),0.001)
L02376                 ch(i,j) = chs (i,j)
L02377  !!           ch(i,j) = flhc(i,j)/( cpm(i,j)*rho(i,kts,j) )
L02378              END DO
L02379           END DO
L02380  #endif         
L02381         ELSE
L02382           CALL wrf_error_fatal('Lacking arguments for QNSESFC in surface driver')
L02383         ENDIF
L02384  
L02385       CASE (GFSSFCSCHEME)
L02386         IF (PRESENT(qv_curr) .AND. .TRUE. ) THEN
L02387         CALL wrf_debug( 100, 'in GFSSFC' )
L02388         IF (FRACTIONAL_SEAICE == 1) THEN
L02389            CALL SF_GFS_SEAICE_WRAPPER(u_phytmp,v_phytmp,t_phy,qv_curr, &
L02390                 p_phy,CP,RCP,R_d,XLV,PSFC,CHS,CHS2,CQS2,CPM,        &
L02391                 ZNT,UST,PSIM,PSIH,                                  &
L02392                 XLAND,HFX,QFX,LH,TSK,FLHC,FLQC,                     &
L02393                 QGH,QSFC,U10,V10,                                   &
L02394                 GZ1OZ0,WSPD,BR,ISFFLX,                              &
L02395                 EP_1,EP_2,KARMAN,itimestep,                         &
L02396                 TICE2TSK_IF2COLD,                            &
L02397                 XICE_THRESHOLD,                              &
L02398                 CHS_SEA, CHS2_SEA, CPM_SEA, CQS2_SEA,        &
L02399                 FLHC_SEA, FLQC_SEA,                          &
L02400                 HFX_SEA, LH_SEA, QFX_SEA, QGH_SEA, QSFC_SEA, &
L02401                 UST_SEA, ZNT_SEA, SST, XICE,                 &
L02402                 ids,ide, jds,jde, kds,kde,                          &
L02403                 ims,ime, jms,jme, kms,kme,                          &
L02404                 i_start(ij),i_end(ij), j_start(ij),j_end(ij), kts,kte    )
L02405        ELSE
L02406           CALL SF_GFS(u_phytmp,v_phytmp,t_phy,qv_curr,              &
L02407                 p_phy,CP,RCP,R_d,XLV,PSFC,CHS,CHS2,CQS2,CPM,        &
L02408                 ZNT,UST,PSIM,PSIH,                                  &
L02409                 XLAND,HFX,QFX,LH,TSK,FLHC,FLQC,                     &
L02410                 QGH,QSFC,U10,V10,                                   &
L02411                 GZ1OZ0,WSPD,BR,ISFFLX,                              &
L02412                 EP_1,EP_2,KARMAN,itimestep,                         &
L02413                 ids,ide, jds,jde, kds,kde,                          &
L02414                 ims,ime, jms,jme, kms,kme,                          &
L02415                 i_start(ij),i_end(ij), j_start(ij),j_end(ij), kts,kte    )
L02416        ENDIF
L02417          CALL wrf_debug(100,'in SFCDIAGS')
L02418         ELSE
L02419           CALL wrf_error_fatal('Lacking arguments for SF_GFS in surface driver')
L02420        ENDIF
L02421  
L02422  #if ( EM_CORE==1)
L02423      CASE(MYNNSFCSCHEME)
L02424  
L02425         IF (PRESENT(qv_curr)    .AND.  PRESENT(qc_curr)     &
L02426              & .AND.  PRESENT(qcg) ) THEN
L02427  
L02428            CALL wrf_debug(100,'in MYNNSFC')
L02429  
L02430           IF (FRACTIONAL_SEAICE == 1) THEN
L02431            CALL MYNN_SEAICE_WRAPPER(                                  &
L02432                 u3d=u_phytmp,v3d=v_phytmp,t3d=t_phy,qv3d=qv_curr,     &
L02433                 p3d=p_phy,dz8w=dz8w,th3d=th_phy,rho=rho,              &
L02434                 psfc=psfc,chs=chs,chs2=chs2,cqs=cqs,cqs2=cqs2,cpm=cpm,&
L02435                 znt=znt,ust=ust,pblh=pblh,mavail=mavail,zol=zol,      &
L02436                 mol=mol,psim=psim,psih=psih,qgh=qgh,                  &
L02437                 xland=xland,hfx=hfx,qfx=qfx,lh=lh,tsk=tsk,            &
L02438                 flhc=flhc,flqc=flqc,qsfc=qsfc,rmol=rmol,              &
L02439                 u10=u10,v10=v10,th2=th2,t2=t2,q2=q2,snowh=snowh,      &
L02440                 gz1oz0=gz1oz0,wspd=wspd,br=br,dx=dx2d,                &
L02441                 itimestep=itimestep,ch=ch,                            &
L02442                 spp_pbl=spp_pbl,pattern_spp_pbl=pattern_spp_pbl,      &
L02443                 xice=XICE,sst=SST,tsk_sea=TSK_SEA,qgh_sea=QGH_SEA,    &
L02444                 chs2_sea=CHS2_SEA,chs_sea=CHS_SEA,cpm_sea=CPM_SEA,    &
L02445                 cqs2_sea=CQS2_SEA,flhc_sea=FLHC_SEA,                  &
L02446                 flqc_sea=FLQC_SEA,hfx_sea=HFX_SEA,lh_sea=LH_SEA,      &
L02447                 qfx_sea=QFX_SEA,qsfc_sea=QSFC_SEA,                    &
L02448                 znt_sea=ZNT_SEA,tice2tsk_if2cold=TICE2TSK_IF2COLD,    &
L02449                 xice_threshold=XICE_THRESHOLD,                        &
L02450                 ids=ids,ide=ide, jds=jds,jde=jde, kds=kds,kde=kde,    &
L02451                 ims=ims,ime=ime, jms=jms,jme=jme, kms=kms,kme=kme,    &
L02452                 its=i_start(ij),ite=i_end(ij),                        &
L02453                 jts=j_start(ij),jte=j_end(ij),kts=kts,kte=kte,        &
L02454                 ustm=ustm,ck=ck,cka=cka,cd=cd,cda=cda,                &
L02455                 sf_mynn_sfcflux_land=sf_mynn_sfcflux_land,            &
L02456                 sf_mynn_sfcflux_water=sf_mynn_sfcflux_water,          &
L02457                 isfflx=isfflx,shalwater_z0=shalwater_z0,              &
L02458                 water_depth=water_depth,lakemask=lakemask,            &
L02459                 flag_lsm=sf_surface_physics,restart=restart_flag,     &
L02460                 errmsg=errmsg,errflg=errflg                           ) 
L02461           ELSE
L02462            CALL mynnsfc_driver(u3d=u_phytmp,v3d=v_phytmp,t3d=t_phy, &
L02463                 qv3d=qv_curr,p3d=p_phy,dz8w=dz8w,th3d=th_phy,       &
L02464                 rho3d=rho,psfcpa=psfc,                              &
L02465                 chs=chs,chs2=chs2,cqs=cqs,cqs2=cqs2,cpm=cpm,        &
L02466                 znt=znt,ust=ust,pblh=pblh,mavail=mavail,zol=zol,    &
L02467                 mol=mol,psim=psim,psih=psih,qgh=qgh,                &
L02468                 xland=xland,hfx=hfx,qfx=qfx,lh=lh,tsk=tsk,          &
L02469                 flhc=flhc,flqc=flqc,qsfc=qsfc,rmol=rmol,            &
L02470                 u10=u10,v10=v10,th2=th2,t2=t2,q2=q2,snowh=snowh,    &
L02471                 gz1oz0=gz1oz0,wspd=wspd,br=br,dx=dx2d,              &
L02472                 itimestep=itimestep,ch=ch,                          &
L02473                 spp_pbl=spp_pbl,pattern_spp_pbl=pattern_spp_pbl,    &
L02474                 ids=ids,ide=ide, jds=jds,jde=jde, kds=kds,kde=kde,  &
L02475                 ims=ims,ime=ime, jms=jms,jme=jme, kms=kms,kme=kme,  &
L02476                 its=i_start(ij),ite=i_end(ij),jts=j_start(ij),      &
L02477                 jte=j_end(ij), kts=kts,kte=kte,                     &
L02478                 ustm=ustm,ck=ck,cka=cka,cd=cd,cda=cda,              &
L02479                 xice=xice,xice_threshold=xice_threshold,            &
L02480                 sf_mynn_sfcflux_land=sf_mynn_sfcflux_land,          &
L02481                 sf_mynn_sfcflux_water=sf_mynn_sfcflux_water,        &
L02482                 isfflx=isfflx,shalwater_z0=shalwater_z0,            &
L02483                 water_depth=water_depth,lakemask=lakemask,          &
L02484                 flag_lsm=sf_surface_physics,restart=restart_flag,   &
L02485                 errmsg=errmsg,errflg=errflg                         )
L02486           ENDIF
L02487         ELSE
L02488            CALL wrf_error_fatal('Lacking arguments for SFCLAY_mynn in surface driver')
L02489         ENDIF
L02490  #endif
L02491  
L02492  #if ( EM_CORE==1)
L02493       CASE (TEMFSFCSCHEME)
L02494         IF (PRESENT(qv_curr).and.PRESENT(hd_temf)) THEN
L02495           CALL wrf_debug( 100, 'in TEMFSFCLAY' )
L02496  ! WA 9/7/09 must initialize Z0 and ZNT for TEMF in ideal cases
L02497         ! DO J=j_start(ij),j_end(ij)
L02498         ! DO I=i_start(ij),i_end(ij)
L02499         !    CHKLOWQ(i,j) = 1.0
L02500         !    Z0(i,j) = 0.03      ! For GABLS2
L02501         !    ZNT(i,j) = 0.03     ! For GABLS2
L02502         ! ENDDO
L02503         ! ENDDO
L02504           CALL TEMFSFCLAY(u3d=u_phytmp,v3d=v_phytmp,th3d=th_phy,    &
L02505                 qv3d=qv_curr,p3d=p_phy,pi3d=pi_phy,rho=rho,z=z,ht=ht, &
L02506                 CP=cp,G=g,ROVCP=rcp,R=r_d,XLV=xlv,psfc=psfc,chs=chs,&
L02507                 chs2=chs2,cqs2=cqs2,CPM=cpm,znt=znt,ust=ust,        &
L02508                 MAVAIL=mavail,XLAND=xland,HFX=hfx,QFX=qfx,LH=lh,   &
L02509                 TSK=tsk,FLHC=flhc,FLQC=flqc,QGH=qgh,qsfc=qsfc,      &
L02510                 U10=u10,V10=v10,TH2=th2,T2=t2,Q2=q2,                &
L02511                 SVP1=svp1,SVP2=svp2,SVP3=svp3,SVPT0=svpt0,EP1=ep_1, &
L02512                 EP2=ep_2,KARMAN=karman,fCor=fCor,te_temf=te_temf,   &
L02513                 hd_temf=hd_temf,exch_temf=exch_temf,wm_temf=wm_temf,&
L02514                 ids=ids,ide=ide, jds=jds,jde=jde, kds=kds,kde=kde,  &
L02515                 ims=ims,ime=ime, jms=jms,jme=jme, kms=kms,kme=kme,  &
L02516                 its=i_start(ij),ite=i_end(ij),                      &
L02517                 jts=j_start(ij),jte=j_end(ij), kts=kts,kte=kte )
L02518         ELSE
L02519           CALL wrf_error_fatal('Lacking arguments for TEMFSFCLAY in surface driver')
L02520         ENDIF
L02521  
L02522       CASE (IDEALSCMSFCSCHEME)
L02523         IF (PRESENT(qv_curr)) THEN
L02524           CALL wrf_debug( 100, 'in IDEALSCMSFCLAY' )
L02525           CALL IDEALSCMSFCLAY(u3d=u_phytmp,v3d=v_phytmp,th3d=th_phy,    &
L02526                 qv3d=qv_curr,p3d=p_phy,pi3d=pi_phy,rho=rho,z=z,ht=ht, &
L02527                 CP=cp,G=g,ROVCP=rcp,R=r_d,XLV=xlv,psfc=psfc,chs=chs,  &
L02528                 chs2=chs2,cqs2=cqs2,CPM=cpm,znt=znt,ust=ust,        &
L02529                 MAVAIL=mavail,XLAND=xland,HFX=hfx,QFX=qfx,LH=lh,   &
L02530                 TSK=tsk,FLHC=flhc,FLQC=flqc,QGH=qgh,qsfc=qsfc,      &
L02531                 U10=u10,V10=v10,TH2=th2,T2=t2,Q2=q2,                &
L02532                 SVP1=svp1,SVP2=svp2,SVP3=svp3,SVPT0=svpt0,EP1=ep_1, &
L02533                 EP2=ep_2,KARMAN=karman,fCor=fCor,   &
L02534                 exch_temf=exch_temf,                &
L02535                 hfx_force=hfx_force,lh_force=lh_force,tsk_force=tsk_force, &
L02536                 hfx_force_tend=hfx_force_tend,                      &
L02537                 lh_force_tend=lh_force_tend,                        &
L02538                 tsk_force_tend=tsk_force_tend,                      &
L02539                 dt=dt,itimestep=itimestep,                          &
L02540                 ids=ids,ide=ide, jds=jds,jde=jde, kds=kds,kde=kde,  &
L02541                 ims=ims,ime=ime, jms=jms,jme=jme, kms=kms,kme=kme,  &
L02542                 its=i_start(ij),ite=i_end(ij),                      &
L02543                 jts=j_start(ij),jte=j_end(ij), kts=kts,kte=kte )
L02544         ELSE
L02545           CALL wrf_error_fatal('Lacking arguments for IDEALSCMSFCLAY in surface driver')
L02546         ENDIF
L02547  #endif
L02548  
L02549       CASE DEFAULT
L02550  
L02551         WRITE( message , * )                                &
L02552     'The sfclay option does not exist: sf_sfclay_physics = ', sf_sfclay_physics
L02553         CALL wrf_error_fatal ( message )
L02554  
L02555       END SELECT sfclay_select
```

> 讲解：九个面层方案的调用分派，逐案看三个维度：①**实参口径**——SFCLAY/MRF/GFS 族要 SVP1/SVP2/…/STBOLT 常数组、MYJ 要 CHKLOWQ/THZ0/QZ0/UZ0/VZ0（面层-PBL 一体化回传）、MYNN 走 mynnsfc_driver 新接口（errmsg/errflg，[code_10](code_10_module_sf_mynnsfc.md) §3.4）；②**海冰前置**——MYJ/QNSE/GFS/MYNN 四案有 seaice_wrapper（本篇 §六收 MYNN 版），在 CASE 内先调 wrapper 处理 xice>xice_threshold 的点再调方案主体；③**TSK 语义**——方案实参统一传 tskold（本步开始时的旧地温）：面层通量用旧地温、LSM 更新后地温，避免同一步内自馈。CASE DEFAULT 报错。每案 CALL 前的 PRESENT 守卫与 [code_22](code_22_module_pbl_driver.md) 同款。

## 五、陆面方案族 sfc_select：SLAB 与 Noah 代表段

<!-- code_extract code_extract.py v1.2
source: phys/module_surface_driver.F
ranges: L2629-L3133
file_lines: 7428
file_md5: e86f31fb163f96f7b7f958865de1085c
display: line-numbered (strip L-prefix and !file: line to restore)
range_md5: 02439a6c28ba1b30e6c7c8fa48012fab
seg_lines: 505
-->

```fortran
!file: phys/module_surface_driver.F    L2629-L3133
L02629       CASE (SLABSCHEME)
L02630  
L02631         IF (PRESENT(qv_curr)                            .AND.    &
L02632             PRESENT(capg)        .AND.    &
L02633                                                        .TRUE. ) THEN
L02634             DO j=j_start(ij),j_end(ij)
L02635             DO i=i_start(ij),i_end(ij)
L02636  !          CQS2 ACCOUNTS FOR MAVAIL FOR SFCDIAGS 2M Q
L02637                CQS2(I,J)= CQS2(I,J)*MAVAIL(I,J)
L02638             ENDDO
L02639             ENDDO
L02640  
L02641          CALL wrf_debug(100,'in SLAB')
L02642            CALL SLAB(t_phy,qv_curr,p_phy,flhc,flqc,  &
L02643               psfc,xland,tmn,hfx,qfx,lh,tsk,qsfc,chklowq,          &
L02644               gsw,glw,capg,thc,snowc,emiss,mavail,                 &
L02645               dtbl,rcp,xlv,dtmin,ifsnow,                           &
L02646               svp1,svp2,svp3,svpt0,ep_2,karman,eomeg,stbolt,       &
L02647               tslb,zs,dzs,num_soil_layers,radiation,               &
L02648               p1000mb,                                             &
L02649               ids,ide, jds,jde, kds,kde,                           &
L02650               ims,ime, jms,jme, kms,kme,                           &
L02651               i_start(ij),i_end(ij), j_start(ij),j_end(ij), kts,kte)
L02652  
L02653             DO j=j_start(ij),j_end(ij)
L02654             DO i=i_start(ij),i_end(ij)
L02655                SFCEVP(I,J)= SFCEVP(I,J) + QFX(I,J)*DTBL
L02656                IF(PRESENT(ACHFX))ACHFX(I,J)=ACHFX(I,J) + HFX(I,J)*DT
L02657                IF(PRESENT(ACLHF))ACLHF(I,J)=ACLHF(I,J) + LH(I,J)*DT
L02658             ENDDO
L02659             ENDDO
L02660  
L02661          CALL wrf_debug(100,'in SFCDIAGS')
L02662            CALL SFCDIAGS(hfx,qfx,tsk,qsfc,chs2,cqs2,t2,th2,q2,      &
L02663                       psfc,cp,r_d,rcp,CHS,t_phy,qv_curr,ua_phys,    &
L02664                       ids,ide, jds,jde, kds,kde,                    &
L02665                       ims,ime, jms,jme, kms,kme,                    &
L02666               i_start(ij),i_end(ij), j_start(ij),j_end(ij), kts,kte    )
L02667  
L02668         ENDIF
L02669  
L02670       CASE (LSMSCHEME)
L02671  
L02672         IF (PRESENT(qv_curr)    .AND.  PRESENT(rainbl)        .AND.    &
L02673  !          PRESENT(emiss)      .AND.  PRESENT(t2)            .AND.    &
L02674  !          PRESENT(declin) .AND.  PRESENT(coszen)    .AND.    &
L02675  !          PRESENT(hrang)  .AND. PRESENT( xlat_urb2d)    .AND.    &
L02676  !          PRESENT(dzr)       .AND.    &
L02677  !          PRESENT( dzb)            .AND. PRESENT(dzg)       .AND.    &
L02678  !          PRESENT(tr_urb2d) .AND. PRESENT(tb_urb2d)         .AND.    &
L02679  !          PRESENT(tg_urb2d) .AND. PRESENT(tc_urb2d) .AND.            &
L02680  !          PRESENT(qc_urb2d) .AND. PRESENT(uc_urb2d) .AND.            &
L02681  !          PRESENT(xxxr_urb2d) .AND. PRESENT(xxxb_urb2d) .AND.        &
L02682  !          PRESENT(xxxg_urb2d) .AND.                                  &
L02683  !          PRESENT(xxxc_urb2d) .AND. PRESENT(trl_urb3d) .AND.         &
L02684  !          PRESENT(tbl_urb3d)   .AND. PRESENT(tgl_urb3d)  .AND.       &
L02685  !          PRESENT(sh_urb2d) .AND. PRESENT(lh_urb2d)  .AND.           &
L02686  !          PRESENT(g_urb2d)   .AND. PRESENT(rn_urb2d) .AND.           &
L02687  !          PRESENT(ts_urb2d)                          .AND.           &
L02688  !          PRESENT(frc_urb2d) .AND. PRESENT(utype_urb2d)   .AND.      &
L02689                                                        .TRUE. ) THEN
L02690  !------------------------------------------------------------------
L02691           IF( PRESENT(sr) ) THEN
L02692             frpcpn=.true.
L02693           ENDIF
L02694           IF ( FRACTIONAL_SEAICE == 1) THEN
L02695              ! The fields passed to LSM need to represent the full ice values, not
L02696              ! the fractional values.  Convert ALBEDO and EMISS from the blended value 
L02697              ! to a value representing only the sea-ice portion.   Albedo over open 
L02698              ! water is taken to be 0.08. Emissivity over open water is taken to be 0.98
L02699              DO j = j_start(ij) , j_end(ij)
L02700                 DO i = i_start(ij) , i_end(ij)
L02701                    IF ( ( XICE(I,J) .GE. XICE_THRESHOLD ) .AND. ( XICE(i,j) .LE. 1 ) ) THEN
L02702                       ALBEDO(I,J) = (ALBEDO(I,J)-(1.-XICE(I,J))*0.08)/XICE(I,J)
L02703                       EMISS(I,J) = (EMISS(I,J)-(1.-XICE(I,J))*0.98)/XICE(I,J)
L02704                    ENDIF
L02705                 ENDDO
L02706              ENDDO
L02707  
L02708              IF ( isisfc ) THEN
L02709                 ! Use surface layer routine values from the ice portion of grid point
L02710              ELSE
L02711                 !
L02712                 ! We don't have surface layer routine values at this time, so
L02713                 ! just use what we have.  Use ice component of TSK
L02714                 !
L02715                 CALL get_local_ice_tsk( ims, ime, jms, jme,                   &
L02716                                         i_start(ij), i_end(ij),               & 
L02717                                         j_start(ij), j_end(ij),               &
L02718                                         itimestep, .false., tice2tsk_if2cold, &
L02719                                         XICE, XICE_THRESHOLD,                 &
L02720                                         SST, TSK, TSK_SEA, TSK_LOCAL )
L02721  
L02722                 DO j = j_start(ij) , j_end(ij)
L02723                    DO i = i_start(ij) , i_end(ij)
L02724                       TSK(i,j) = TSK_LOCAL(i,j)
L02725                    ENDDO
L02726                 ENDDO
L02727              ENDIF
L02728           ENDIF
L02729  
L02730  !added for WRF_HYDRO
L02731  #ifdef WRF_HYDRO
L02732           if(HYDRO_dt .ge. 0) HYDRO_dt = dtbl
L02733  #endif
L02734  
L02735  ! added RA population for WRF/Noah-CMAQ RS Consistency
L02736  ! following Garland et al. (1977) and Nemitz et al., 2009
L02737           IF ( PRESENT(RA) ) THEN
L02738           DO j=j_start(ij),j_end(ij)
L02739           DO i=i_start(ij),i_end(ij)
L02740              RA(I,J) = WSPD(I,J)/UST(I,J)**2.0
L02741           ENDDO
L02742           ENDDO
L02743           END IF
L02744  
L02745           CALL wrf_debug(100,'in NOAH DRV')
L02746                  
L02747           IF (sf_surface_mosaic == 1) THEN
L02748            
L02749             IF ( PRESENT( TSK_mosaic ) .AND. PRESENT( HFX_mosaic ) ) THEN
L02750               CALL lsm_mosaic(dz8w,qv_curr,p8w,t_phy,tsk,                 &
L02751                  hfx,qfx,lh,grdflx,qgh,gsw,swdown,glw,smstav,smstot,    &
L02752                  sfcrunoff,udrunoff,ivgtyp,isltyp,isurban,isice,vegfra,        &
L02753                  albedo,albbck,znt,z0, tmn,xland,xice,emiss, embck,    &
L02754                  snowc,qsfc,rainbl,                              &
L02755                  mminlu,                                         &
L02756                  num_soil_layers,dtbl,dzs,itimestep,             &
L02757                  smois,tslb,snow,canwat,                         &
L02758                  chs, chs2, cqs2, cpm,rcp,SR,chklowq,lai,qz0,    &
L02759                  myj,frpcpn,                                     &
L02760  		sh2o,snowh,                                     & !h
L02761                  u_phy,v_phy,                                    & !I
L02762                  snoalb,shdmin,shdmax,shdavg,                    & !i
L02763                  snotime,                                        & !o
L02764                  acsnom,acsnow,                                  & !o
L02765                  snopcx,                                         & !o
L02766                  potevp,                                         & !o
L02767                  smcrel,                                         & !o
L02768                  xice_threshold,                                 &
L02769                  rdlai2d,usemonalb,                              &
L02770                  br,                                             & !?
L02771                  NOAHRES,opt_thcnd,                              &
L02772                  NLCAT,landusef,landusef2,                       & ! danli mosaic
L02773                  sf_surface_mosaic,mosaic_cat,mosaic_cat_index,  & ! danli mosaic 
L02774                  TSK_mosaic,QSFC_mosaic,                         & ! danli mosaic 
L02775                  TSLB_mosaic,SMOIS_mosaic,SH2O_mosaic,           & ! danli mosaic 
L02776                  CANWAT_mosaic,SNOW_mosaic,                      & ! danli mosaic
L02777                  SNOWH_mosaic,SNOWC_mosaic,                      & ! danli mosaic 
L02778                  ALBEDO_mosaic,ALBBCK_mosaic,                    & ! danli mosaic
L02779                  EMISS_mosaic, EMBCK_mosaic,                     & ! danli mosaic
L02780                  ZNT_mosaic, Z0_mosaic,                          & ! danli mosaic 
L02781                  HFX_mosaic,QFX_mosaic,                          & ! danli mosaic
L02782                  LH_mosaic, GRDFLX_mosaic, SNOTIME_mosaic,       & ! danli mosaic
L02783                  RS_mosaic, LAI_mosaic,                          & ! mosaic
L02784                  ua_phys,flx4,fvb,fbur,fgsn,                     &
L02785                  ids,ide, jds,jde, kds,kde,                      &
L02786                  ims,ime, jms,jme, kms,kme,                      &
L02787                  i_start(ij),i_end(ij), j_start(ij),j_end(ij), kts,kte,    &
L02788                  sf_urban_physics                                &
L02789  !Optional urban
L02790                  ,cmr_sfcdif,chr_sfcdif,cmc_sfcdif,chc_sfcdif    &
L02791                  ,cmgr_sfcdif,chgr_sfcdif                        &
L02792                  ,tr_urb2d,tb_urb2d,tg_urb2d,tc_urb2d,qc_urb2d,  & !H urban
L02793                  uc_urb2d,                                       & !H urban
L02794                  xxxr_urb2d,xxxb_urb2d,xxxg_urb2d,xxxc_urb2d,    & !H urban
L02795                  trl_urb3d,tbl_urb3d,tgl_urb3d,                  & !H urban
L02796                  sh_urb2d,lh_urb2d,g_urb2d,rn_urb2d,ts_urb2d,    & !H urban
L02797                  TR_URB2D_mosaic,TB_URB2D_mosaic,                & !H urban  danli mosaic
L02798                  TG_URB2D_mosaic,TC_URB2D_mosaic,                & !H urban  danli mosaic
L02799                  QC_URB2D_mosaic,UC_URB2D_mosaic,                & !H urban  danli mosaic                  
L02800                  TRL_URB3D_mosaic,TBL_URB3D_mosaic,              & !H urban  danli mosaic
L02801                  TGL_URB3D_mosaic,                               & !H urban  danli mosaic
L02802                  SH_URB2D_mosaic,LH_URB2D_mosaic,                & !H urban  danli mosaic
L02803                  G_URB2D_mosaic,RN_URB2D_mosaic,                 & !H urban  danli mosaic
L02804                  TS_URB2D_mosaic,                                & !H urban  danli mosaic
L02805                  TS_RUL2D_mosaic,                                & !H urban  danli mosaic                
L02806                  psim_urb2d,psih_urb2d,u10_urb2d,v10_urb2d,      & !O urban
L02807                  GZ1OZ0_urb2d, AKMS_URB2D,                       & !O urban
L02808                  th2_urb2d,q2_urb2d,ust_urb2d,                   & !O urban
L02809                  declin,coszen,hrang,                            & !I solar
L02810                  xlat_urb2d,                                     & !I urban
L02811                  num_roof_layers, num_wall_layers,               & !I urban
L02812                  num_road_layers, DZR, DZB, DZG,                 & !I urban
L02813                  CMCR_URB2D,TGR_URB2D,TGRL_URB3D,SMR_URB3D,      & !H urban
L02814                  julian,julyr,                                   & !H urban
L02815                  DRELR_URB2D,DRELB_URB2D,DRELG_URB2D,            & !H urban
L02816                  FLXHUMR_URB2D,FLXHUMB_URB2D,FLXHUMG_URB2D,      & !H urban
L02817                  ! added by Chenghao Wang
L02818                  TVG_URB2D,XXXVG_URB2D,TVGL_URB3D,SMG_URB3D,TT_URB2D,CMCG_URB2D, & !H urban
L02819                  FLXHUMVG_URB2D,FLXHUMT_URB2D,                   & !H urban
L02820                  FRC_URB2D, UTYPE_URB2D,                         & !I urban
L02821                  num_urban_ndm,                                  & !I multi-layer urban
L02822                  urban_map_zrd,                                  & !I multi-layer urban
L02823                  urban_map_zwd,                                  & !I multi-layer urban
L02824                  urban_map_gd,                                   & !I multi-layer urban
L02825                  urban_map_zd,                                   & !I multi-layer urban
L02826                  urban_map_zdf,                                  & !I multi-layer urban
L02827                  urban_map_bd,                                   & !I multi-layer urban
L02828                  urban_map_wd,                                   & !I multi-layer urban
L02829                  urban_map_gbd,                                  & !I multi-layer urban
L02830                  urban_map_fbd,                                  & !I multi-layer urban
L02831                  urban_map_zgrd,                                 & !I multi-layer urban
L02832                  num_urban_hi,                                   & !I multi-layer urban
L02833                  use_wudapt_lcz,                                 & !I wudapt
L02834                  slucm_distributed_drag,                         & !I SLUCM
L02835                  tsk_rural,                                      & !H multi-layer urban
L02836                  trb_urb4d,tw1_urb4d,tw2_urb4d,tgb_urb4d,        & !H multi-layer urban
L02837                  tlev_urb3d,qlev_urb3d,                          & !H multi-layer urban
L02838                  tw1lev_urb3d,tw2lev_urb3d,                      & !H multi-layer urban
L02839                  tglev_urb3d,tflev_urb3d,                        & !H multi-layer urban
L02840                  sf_ac_urb3d,lf_ac_urb3d,cm_ac_urb3d,            & !H multi-layer urban
L02841                  sfvent_urb3d,lfvent_urb3d,                      & !H multi-layer urban
L02842                  sfwin1_urb3d,sfwin2_urb3d,                      & !H multi-layer urban
L02843                  sfw1_urb3d,sfw2_urb3d,sfr_urb3d,sfg_urb3d,      & !H multi-layer urban
L02844                   ep_pv_urb3d,t_pv_urb3d,                         & !GRZ
L02845                  trv_urb4d,qr_urb4d,qgr_urb3d,tgr_urb3d,         & !GRZ
L02846                  drain_urb4d,draingr_urb3d,sfrv_urb3d,           & !GRZ
L02847                  lfrv_urb3d,dgr_urb3d,dg_urb3d,lfr_urb3d,lfg_urb3d,& !GRZ
L02848                  lp_urb2d,hi_urb2d,lb_urb2d,hgt_urb2d,           & !H multi-layer urban
L02849                  mh_urb2d,stdh_urb2D,lf_urb2d,                   & !SLUCM
L02850                  lf_urb2d_s, z0_urb2d,                           & !SLUCM
L02851                  th_phy,rho,p_phy,ust,                           & !I multi-layer urban
L02852                  gmt,julday,xlong,xlat,                          & !I multi-layer urban
L02853                  a_u_bep,a_v_bep,a_t_bep,a_q_bep,                & !O multi-layer urban
L02854                  a_e_bep,b_u_bep,b_v_bep,                        & !O multi-layer urban
L02855                  b_t_bep,b_q_bep,b_e_bep,dlg_bep,                & !O multi-layer urban
L02856                  dl_u_bep,sf_bep,vl_bep                          & !O multi-layer urban
L02857  #ifdef WRF_HYDRO
L02858                  ,sfcheadrt,INFXSRT, soldrain                    & !hydro
L02859  #endif
L02860                  ,SDA_HFX, SDA_QFX, HFX_BOTH, QFX_BOTH, QNORM, fasdas    & ! fasdas
L02861                  ,RS,XLAIDYN,IRRIGATION_CHANNEL)
L02862             ELSE
L02863                 CALL wrf_error_fatal('Lack arguments to call lsm_mosaic')
L02864             ENDIF
L02865  
L02866  	  ELSEIF (sf_surface_mosaic == 0) THEN
L02867  	                  
L02868  !
L02869  !  FASDAS
L02870  !
L02871               IF( fasdas == 1 ) THEN
L02872                 DO j=j_start(ij),j_end(ij)
L02873                 DO i=i_start(ij),i_end(ij)
L02874  
L02875  !ckay2015 only do indirect nudging over land areas 
L02876                       IF(XLAND(i,j) .GT. 1.5) then
L02877                        SDA_QFX(I,J) = 0.0
L02878                        SDA_HFX(I,J) = 0.0
L02879                       END IF
L02880  
L02881  ! TWG2015 Removed lines that update fluxes to ensure this section only defines
L02882  ! the output
L02883                      QFXOLD(I,J)=QFX(I,J)
L02884                      QFX_KAY = SDA_QFX(I,J)*RHO(I,1,J)*DZ8W(I,1,J)
L02885                      QFX_KAY = QFX_KAY * QNORM(I,J)
L02886                      QFX_BOTH(I,J)=QFX(I,J)+QFX_KAY
L02887  
L02888                      HFXOLD(I,J)=HFX(I,J)
L02889                      HFX_KAY = SDA_HFX(I,J)*RHO(I,1,J)*CPM(I,J)*DZ8W(I,1,J)
L02890                      HFX_BOTH(I,J)=HFX(I,J)+HFX_KAY
L02891  
L02892                 ENDDO
L02893                 ENDDO
L02894               END IF
L02895  !
L02896  !  END FASDAS
L02897  !
L02898                 if (pert_noah .and. multi_perturb == 1) then
L02899                   allocate (tslb_tmp(i_start(ij):i_end(ij), 1:num_soil_layers, j_start(ij):j_end(ij)))
L02900                   allocate (smois_tmp(i_start(ij):i_end(ij), 1:num_soil_layers, j_start(ij):j_end(ij)))
L02901  
L02902                   call Add_multi_perturb_lsm_perturbations (perts_qvapor, perts_th, perts_smois, perts_tsoil, &
L02903                     pert_noah_qv, pert_noah_t, pert_noah_smois, pert_noah_tslb, t_phy, qv_curr, tslb, smois, &
L02904                     tslb_tmp, smois_tmp, num_soil_layers, i_start(ij), i_end(ij), j_start(ij), j_end(ij), ims, &
L02905                     ime, jms, jme, kms, kme, kts, kte)
L02906                 end if
L02907  
L02908                 CALL lsm(dz8w,qv_curr,p8w,t_phy,tsk,                 &
L02909                  hfx,qfx,lh,grdflx,qgh,gsw,swdown,swddir,swddif,     &
L02910                  glw,smstav,smstot,    &
L02911                  sfcrunoff,udrunoff,ivgtyp,isltyp,isurban,isice,vegfra,        &
L02912                  albedo,albbck,znt,z0, tmn,xland,xice,emiss, embck,    &
L02913                  snowc,qsfc,rainbl,                              &
L02914                  mminlu,                                         &
L02915                  num_soil_layers,dtbl,dzs,itimestep,             &
L02916                  smois,tslb,snow,canwat,                         &
L02917                  chs, chs2, cqs2, cpm,rcp,SR,chklowq,lai,qz0,    &
L02918                  myj,frpcpn,                                     &
L02919  		sh2o,snowh,                                     & !h
L02920                  u_phy,v_phy,                                    & !I
L02921                  snoalb,shdmin,shdmax,                           & !i
L02922                  snotime,                                        & !o
L02923                  acsnom,acsnow,                                  & !o
L02924                  snopcx,                                         & !o
L02925                  potevp,                                         & !o
L02926                  smcrel,                                         & !o
L02927                  xice_threshold,                                 &
L02928                  rdlai2d,usemonalb,                              &
L02929                  br,                                             & !?
L02930                  NOAHRES,opt_thcnd,                              &
L02931                  ua_phys,flx4,fvb,fbur,fgsn,                     &
L02932                  ids,ide, jds,jde, kds,kde,                      &
L02933                  ims,ime, jms,jme, kms,kme,                      &
L02934                  i_start(ij),i_end(ij), j_start(ij),j_end(ij), kts,kte,    &
L02935                  sf_urban_physics                                &
L02936  !Optional urban
L02937                  ,cmr_sfcdif,chr_sfcdif,cmc_sfcdif,chc_sfcdif    &
L02938                  ,cmgr_sfcdif,chgr_sfcdif                        &
L02939                  ,tr_urb2d,tb_urb2d,tg_urb2d,tc_urb2d,qc_urb2d,  & !H urban
L02940                  uc_urb2d,                                       & !H urban
L02941                  xxxr_urb2d,xxxb_urb2d,xxxg_urb2d,xxxc_urb2d,    & !H urban
L02942                  trl_urb3d,tbl_urb3d,tgl_urb3d,                  & !H urban
L02943                  sh_urb2d,lh_urb2d,g_urb2d,rn_urb2d,ts_urb2d,    & !H urban
L02944                  psim_urb2d,psih_urb2d,u10_urb2d,v10_urb2d,      & !O urban
L02945                  GZ1OZ0_urb2d, AKMS_URB2D,                       & !O urban
L02946                  th2_urb2d,q2_urb2d,ust_urb2d,                   & !O urban
L02947                  declin,coszen,hrang,                            & !I solar
L02948                  xlat_urb2d,                                     & !I urban
L02949                  num_roof_layers, num_wall_layers,               & !I urban
L02950                  num_road_layers, DZR, DZB, DZG,                 & !I urban
L02951                  CMCR_URB2D,TGR_URB2D,TGRL_URB3D,SMR_URB3D,      & !H urban
L02952                  DRELR_URB2D,DRELB_URB2D,DRELG_URB2D,            & !H urban
L02953                  FLXHUMR_URB2D,FLXHUMB_URB2D,FLXHUMG_URB2D,      & !H urban
L02954                  TVG_URB2D,XXXVG_URB2D,TVGL_URB3D,SMG_URB3D,TT_URB2D,CMCG_URB2D, & !H urban
L02955                  FLXHUMVG_URB2D,FLXHUMT_URB2D,                   & !H urban
L02956                  julian, julyr,                                  & !H urban
L02957                  FRC_URB2D, UTYPE_URB2D,                         & !I urban
L02958                  num_urban_ndm,                                  & !I multi-layer urban
L02959                  urban_map_zrd,                                  & !I multi-layer urban
L02960                  urban_map_zwd,                                  & !I multi-layer urban
L02961                  urban_map_gd,                                   & !I multi-layer urban
L02962                  urban_map_zd,                                   & !I multi-layer urban
L02963                  urban_map_zdf,                                  & !I multi-layer urban
L02964                  urban_map_bd,                                   & !I multi-layer urban
L02965                  urban_map_wd,                                   & !I multi-layer urban
L02966                  urban_map_gbd,                                  & !I multi-layer urban
L02967                  urban_map_fbd,                                  & !I multi-layer urban
L02968                  urban_map_zgrd,                                 & !I multi-layer urban
L02969                  num_urban_hi,                                   & !I multi-layer urban
L02970                  tsk_rural,                                      & !H multi-layer urban
L02971                  trb_urb4d,tw1_urb4d,tw2_urb4d,tgb_urb4d,        & !H multi-layer urban
L02972                  tlev_urb3d,qlev_urb3d,                          & !H multi-layer urban
L02973                  tw1lev_urb3d,tw2lev_urb3d,                      & !H multi-layer urban
L02974                  tglev_urb3d,tflev_urb3d,                        & !H multi-layer urban
L02975                  sf_ac_urb3d,lf_ac_urb3d,cm_ac_urb3d,            & !H multi-layer urban
L02976                  sfvent_urb3d,lfvent_urb3d,                      & !H multi-layer urban
L02977                  sfwin1_urb3d,sfwin2_urb3d,                      & !H multi-layer urban
L02978                  sfw1_urb3d,sfw2_urb3d,sfr_urb3d,sfg_urb3d,      & !H multi-layer urban
L02979                  ep_pv_urb3d,t_pv_urb3d,                         & !GRZ
L02980                  trv_urb4d,qr_urb4d,qgr_urb3d,tgr_urb3d,         & !GRZ
L02981                  drain_urb4d,draingr_urb3d,sfrv_urb3d,           & !GRZ
L02982                  lfrv_urb3d,dgr_urb3d,dg_urb3d,lfr_urb3d,lfg_urb3d,& !GRZ
L02983                  lp_urb2d,hi_urb2d,lb_urb2d,hgt_urb2d,           & !H multi-layer urban
L02984                  mh_urb2d,stdh_urb2D,lf_urb2d,                   & !SLUCM
L02985                  lf_urb2d_s, z0_urb2d,                           & !SLUCM
L02986                  th_phy,rho,p_phy,ust,                           & !I multi-layer urban
L02987                  gmt,julday,xlong,xlat,                          & !I multi-layer urban
L02988                  a_u_bep,a_v_bep,a_t_bep,a_q_bep,                & !O multi-layer urban
L02989                  a_e_bep,b_u_bep,b_v_bep,                        & !O multi-layer urban
L02990                  b_t_bep,b_q_bep,b_e_bep,dlg_bep,                & !O multi-layer urban
L02991                  dl_u_bep,sf_bep,vl_bep                          & !O multi-layer urban
L02992  #ifdef WRF_HYDRO
L02993                  ,sfcheadrt,INFXSRT, soldrain                    &
L02994  #endif
L02995                  ,SDA_HFX, SDA_QFX, HFX_BOTH, QFX_BOTH, QNORM, fasdas    &
L02996                  ,RS,XLAIDYN,IRRIGATION_CHANNEL)
L02997           ENDIF
L02998  
L02999           if (pert_noah .and. multi_perturb == 1) then
L03000             call Remove_multi_perturb_lsm_perturbations (perts_qvapor, perts_th, perts_smois, perts_tsoil, &
L03001                 pert_noah_qv, pert_noah_t, pert_noah_smois, pert_noah_tslb, t_phy, qv_curr, tslb, smois, &
L03002                 tslb_tmp, smois_tmp, num_soil_layers, i_start(ij), i_end(ij), j_start(ij), j_end(ij), ims, &
L03003                 ime, jms, jme, kms, kme, kts, kte)
L03004             deallocate (tslb_tmp)
L03005             deallocate (smois_tmp)
L03006           end if
L03007  
L03008           call seaice_noah( SEAICE_ALBEDO_OPT, SEAICE_ALBEDO_DEFAULT, SEAICE_THICKNESS_OPT, &
L03009                &            SEAICE_THICKNESS_DEFAULT, SEAICE_SNOWDEPTH_OPT,             &
L03010                &            SEAICE_SNOWDEPTH_MAX, SEAICE_SNOWDEPTH_MIN,                 &
L03011                &            t_phy, qv_curr, p8w, dz8w, num_soil_layers, dt, frpcpn, sr, &
L03012                &            glw, swdown, rainbl, snoalb, qgh, xice, xice_threshold,     &
L03013                &            albsi, icedepth, snowsi,                                    &
L03014                &            tslb, emiss, albedo, z0, tsk, snow, snowc, snowh,           &
L03015                &            chs, chs2, cqs2,                                            &
L03016                &            br, znt, lh, hfx, qfx, potevp, grdflx, qsfc, acsnow,        &
L03017                &            acsnom, snopcx, sfcrunoff, noahres,                         &
L03018                &            sf_urban_physics, b_t_bep, b_q_bep, rho,                    &
L03019                &            ids,ide, jds,jde, kds,kde,                                  &
L03020                &            ims,ime, jms,jme, kms,kme,                                  &
L03021                &            i_start(ij),i_end(ij), j_start(ij),j_end(ij), kts,kte )
L03022  
L03023           IF ( FRACTIONAL_SEAICE == 1 ) THEN
L03024              ! LSM Returns full land/ice values, no fractional values.
L03025              ! We return to a fractional component here.  SFLX currently hard-wires
L03026              ! emissivity over sea ice to 0.98, the same value as over open water, so
L03027              ! the fractional consideration doesn't have any effect for emissivity.
L03028              DO j=j_start(ij),j_end(ij)
L03029                 DO i=i_start(ij),i_end(ij)
L03030                    IF ( ( XICE(I,J) .GE. XICE_THRESHOLD) .AND. ( XICE(i,j) .LE. 1.0 ) ) THEN
L03031                       albedo(i,j) = ( albedo(i,j) * XICE(i,j) ) + ( (1.0-XICE(i,j)) * 0.08  )
L03032                       emiss(i,j) = ( emiss(i,j) * XICE(i,j) ) + ( (1.0-XICE(i,j)) * 0.98  )
L03033                    ENDIF
L03034                 ENDDO
L03035              ENDDO
L03036  
L03037              IF ( isisfc ) THEN
L03038                 DO j=j_start(ij),j_end(ij)
L03039                    DO i=i_start(ij),i_end(ij)
L03040                       IF ( ( XICE(I,J) .GE. XICE_THRESHOLD) .AND. ( XICE(i,j) .LE. 1.0 ) ) THEN
L03041                          !  Weighted average of fields between ice-cover values and open-water values.
L03042                          flhc(i,j) = ( flhc(i,j) * XICE(i,j) ) + ( (1.0-XICE(i,j)) * flhc_sea(i,j) )
L03043                          flqc(i,j) = ( flqc(i,j) * XICE(i,j) ) + ( (1.0-XICE(i,j)) * flqc_sea(i,j) )
L03044                          cpm(i,j)  = ( cpm(i,j)  * XICE(i,j) ) + ( (1.0-XICE(i,j)) * cpm_sea(i,j)  )
L03045                          cqs2(i,j) = ( cqs2(i,j) * XICE(i,j) ) + ( (1.0-XICE(i,j)) * cqs2_sea(i,j) )
L03046                          chs2(i,j) = ( chs2(i,j) * XICE(i,j) ) + ( (1.0-XICE(i,j)) * chs2_sea(i,j) )
L03047                          chs(i,j)  = ( chs(i,j)  * XICE(i,j) ) + ( (1.0-XICE(i,j)) * chs_sea(i,j)  )
L03048                          qsfc(i,j) = ( qsfc(i,j) * XICE(i,j) ) + ( (1.0-XICE(i,j)) * qsfc_sea(i,j) )
L03049                          qgh(i,j)  = ( qgh(i,j)  * XICE(i,j) ) + ( (1.0-XICE(i,j)) * qgh_sea(i,j)  )
L03050                          qz0(i,j)  = ( qz0(i,j)  * XICE(i,j) ) + ( (1.0-XICE(i,j)) * qz0_sea(i,j)  )
L03051                                                              !  print *,'hfx =',hfx_sea(170,20)
L03052                                                              !   print *,'XICE =',XICE(170,20)
L03053                                                              !    print *,'QSFC =',QSFC(170,20)
L03054                          hfx(i,j)  = ( hfx(i,j)  * XICE(i,j) ) + ( (1.0-XICE(i,j)) * hfx_sea(i,j)  )
L03055                          qfx(i,j)  = ( qfx(i,j)  * XICE(i,j) ) + ( (1.0-XICE(i,j)) * qfx_sea(i,j)  )
L03056                          lh(i,j)   = ( lh(i,j)   * XICE(i,j) ) + ( (1.0-XICE(i,j)) * lh_sea(i,j)   )
L03057  !save old tsk_ice
L03058                          tsk_save(i,j)  = tsk(i,j)
L03059                          tsk(i,j)  = ( tsk(i,j)  * XICE(i,j) ) + ( (1.0-XICE(i,j)) * tsk_sea(i,j)  )
L03060                       ENDIF
L03061                    ENDDO
L03062                 ENDDO
L03063              ELSE
L03064                 DO j = j_start(ij) , j_end(ij)
L03065                    DO i = i_start(ij) , i_end(ij)
L03066                       IF ( ( XICE(I,J) .GE. XICE_THRESHOLD ) .AND. ( XICE(i,j) .LE. 1.0 ) ) THEN
L03067                          ! Compute TSK as the open-water and ice-cover average
L03068                          tsk(i,j) = ( tsk(i,j) * XICE(i,j) ) + ( (1.0-XICE(i,j)) * tsk_sea(i,j) )
L03069                       ENDIF
L03070                    ENDDO
L03071                 ENDDO
L03072              ENDIF
L03073           ENDIF
L03074             DO j=j_start(ij),j_end(ij)
L03075             DO i=i_start(ij),i_end(ij)
L03076  !              CHKLOWQ(I,J)= 1.0
L03077                 SFCEVP(I,J)= SFCEVP(I,J) + QFX(I,J)*DTBL
L03078                 SFCEXC(I,J)= CHS(I,J)
L03079                 IF(PRESENT(ACHFX))ACHFX(I,J)=ACHFX(I,J) + HFX(I,J)*DT
L03080                 IF(PRESENT(ACLHF))ACLHF(I,J)=ACLHF(I,J) + LH(I,J)*DT
L03081                 IF(PRESENT(ACGRDFLX))ACGRDFLX(I,J)=ACGRDFLX(I,J) + GRDFLX(I,J)*DT
L03082             ENDDO
L03083             ENDDO
L03084  
L03085            CALL SFCDIAGS(HFX,QFX,TSK,QSFC,CHS2,CQS2,T2,TH2,Q2,      &
L03086                       PSFC,CP,R_d,RCP,CHS,t_phy,qv_curr,ua_phys,    &
L03087                       ids,ide, jds,jde, kds,kde,                    &
L03088                       ims,ime, jms,jme, kms,kme,                    &
L03089               i_start(ij),i_end(ij), j_start(ij),j_end(ij), kts,kte    )
L03090  !urban
L03091       IF(SF_URBAN_PHYSICS.eq.1) THEN
L03092         DO j=j_start(ij),j_end(ij)                             !urban
L03093           DO i=i_start(ij),i_end(ij)                           !urban
L03094             IF(IVGTYP(I,J) == ISURBAN   .or. IVGTYP(I,J) == LCZ_1 .or. IVGTYP(I,J) == LCZ_2 .or. &
L03095               IVGTYP(I,J) == LCZ_3      .or. IVGTYP(I,J) == LCZ_4 .or. IVGTYP(I,J) == LCZ_5 .or. &
L03096               IVGTYP(I,J) == LCZ_6      .or. IVGTYP(I,J) == LCZ_7 .or. IVGTYP(I,J) == LCZ_8 .or. &
L03097               IVGTYP(I,J) == LCZ_9      .or. IVGTYP(I,J) == LCZ_10 .or. IVGTYP(I,J) == LCZ_11 )THEN
L03098               U10(I,J)  = U10_URB2D(I,J)                       !urban
L03099               V10(I,J)  = V10_URB2D(I,J)                       !urban
L03100               PSIM(I,J) = PSIM_URB2D(I,J)                      !urban
L03101               PSIH(I,J) = PSIH_URB2D(I,J)                      !urban
L03102               GZ1OZ0(I,J) = GZ1OZ0_URB2D(I,J)                  !urban
L03103  !m             AKHS(I,J) = AKHS_URB2D(I,J)                    !urban
L03104               AKHS(I,J) = CHS(I,J)                             !urban
L03105               AKMS(I,J) = AKMS_URB2D(I,J)                      !urban
L03106             END IF                                             !urban
L03107           ENDDO                                                !urban
L03108         ENDDO                                                  !urban
L03109       ENDIF
L03110  ! urban BEP
L03111       IF((SF_URBAN_PHYSICS.eq.2).OR.(SF_URBAN_PHYSICS.eq.3)) THEN
L03112         DO j=j_start(ij),j_end(ij)                             !urban
L03113           DO i=i_start(ij),i_end(ij)                           !urban
L03114              IF( IVGTYP(I,J) == ISURBAN    .or. IVGTYP(I,J) == LCZ_1 .or. IVGTYP(I,J) == LCZ_2 .or. &
L03115               IVGTYP(I,J) == LCZ_3      .or. IVGTYP(I,J) == LCZ_4 .or. IVGTYP(I,J) == LCZ_5 .or. &
L03116               IVGTYP(I,J) == LCZ_6      .or. IVGTYP(I,J) == LCZ_7 .or. IVGTYP(I,J) == LCZ_8 .or. &
L03117               IVGTYP(I,J) == LCZ_9      .or. IVGTYP(I,J) == LCZ_10 .or. IVGTYP(I,J) == LCZ_11 )THEN
L03118              T2(I,J)   = TH_PHY(i,1,j)/((1.E5/PSFC(I,J))**RCP) !urban
L03119              TH2(I,J) = TH_PHY(i,1,j) !urban
L03120              Q2(I,J)   = qv_curr(i,1,j)  !urban
L03121              U10(I,J)  = U_phy(I,1,J)                       !urban
L03122              V10(I,J)  = V_phy(I,1,J)                       !urban
L03123             END IF                                             !urban
L03124           ENDDO                                                !urban
L03125         ENDDO                                                  !urban
L03126       ENDIF
L03127  
L03128  !------------------------------------------------------------------
L03129  
L03130         ELSE
L03131           CALL wrf_error_fatal('Lacking arguments for LSM in surface driver')
L03132         ENDIF
L03133  
```

> 讲解：①**SLAB**（sf_surface_physics=1）：能量平衡单层地温 + 五层热扩散，实参最短——「最小陆面」参照；②**Noah**（=2，教材 16 章主角）：先 **lsm_mosaic**（mosaic_opt=1 时按植被类型分片多次调用——城市格点的自然片/人造片分离就在这里）再 CALL lsm（module_sf_noahdrv 的主入口，12/13 篇全文精读）；实参含 TSLB/ZS/DZS 土壤态、SFCEVP/FLXPOP 调试开关、海洋/湖面点跳过逻辑。其余六案（NoahMP=3/RUC=4/PX=7/CLM=8/CTSM=9/SSIB=6）结构同款：PRESENT 守卫→CALL→L4478 收口，不重复收录；CLM/Lake 的耦合变量（h2osoi_*3d 等）在收尾段的 Lake 调用可见。

## 六、收尾：海洋/湖泊/诊断限幅/人为热

<!-- code_extract code_extract.py v1.2
source: phys/module_surface_driver.F
ranges: L4478-L4619
file_lines: 7428
file_md5: e86f31fb163f96f7b7f958865de1085c
display: line-numbered (strip L-prefix and !file: line to restore)
range_md5: f3d011fd0c4a33a50706b34538ee55d1
seg_lines: 142
-->

```fortran
!file: phys/module_surface_driver.F    L4478-L4619
L04478       END SELECT sfc_select
L04479  
L04480       ENDDO
L04481       !$OMP END PARALLEL DO
L04482  
L04483   430 CONTINUE
L04484  
L04485  #if ( EM_CORE==1)
L04486     IF (sf_ocean_physics .EQ. OMLSCHEME .or. sf_ocean_physics .EQ. PWP3DSCHEME) THEN
L04487  ! simple ocean mixed layer model based Pollard, Rhines and Thompson (1973)
L04488       CALL wrf_debug( 100, 'Call OCEANML' )
L04489       !$OMP PARALLEL DO   &
L04490       !$OMP PRIVATE ( ij )
L04491       DO ij = 1 , num_tiles
L04492          CALL ocean_driver(tml,t0ml,hml,h0ml,huml,hvml,ust,u_phy,v_phy, &
L04493                       tmoml,f,g,oml_gamma,                         &
L04494                       xland,hfx,lh,tsk,gsw,glw,emiss,              &
L04495                       dtbl,STBOLT,oml_relaxation_time,             &
L04496                       ids,ide, jds,jde, kds,kde,                   &
L04497                       ims,ime, jms,jme, kms,kme,                   &
L04498                       i_start(ij),i_end(ij), j_start(ij),j_end(ij), kts,kte, & 
L04499                       sf_ocean_physics,okms, okme,                 & !cyl
L04500                       om_tmp,om_s,om_u, om_v,  om_depth, om_ml,    & !cyl
L04501                       om_lat, om_lon,                              & !cyl
L04502                       QFX,                                         & !cyl 
L04503                       rdx, rdy, msfu, msfv, msft,xtime,            & !cyl 
L04504                       om_tini,om_sini,id,omdt,                     & !cyl 
L04505                       itimestep )                                    !cyl
L04506       ENDDO
L04507       !$OMP END PARALLEL DO
L04508     ENDIF
L04509  #endif
L04510  ! adding a lake model -- 07/02/2010
L04511     IF ( LakeModel == 1 ) THEN
L04512   
L04513        CALL wrf_debug( 100, 'Call LakeModel' )
L04514   
L04515        DO ij = 1 , num_tiles
L04516   
L04517           CALL Lake(  t_phy        ,p8w            ,dz8w         ,qv_curr         ,&  !i
L04518                       u_phy        ,v_phy          , glw         ,emiss           ,&
L04519                       rainbl       ,dtbl           ,swdown       ,albedo          ,&
L04520                       xlat_urb2d   ,z_lake3d       ,dz_lake3d    ,lakedepth2d     ,&
L04521                       watsat3d     ,csol3d         ,tkmg3d       ,tkdry3d         ,&
L04522                       tksatu3d     ,ivgtyp         ,ht           ,xland           ,&
L04523                       iswater      ,xice           ,xice_threshold, lake_min_elev    ,&
L04524                       ids          ,ide            ,jds          ,jde             ,&
L04525                       kds          ,kde            ,ims          ,ime             ,&
L04526                       jms          ,jme            ,kms          ,kme             ,&
L04527                       i_start(ij)  ,i_end(ij)      ,j_start(ij)  ,j_end(ij)       ,&
L04528                       kts          ,kte                                           ,&
L04529                       h2osno2d     ,snowdp2d       ,snl2d        ,z3d             ,&  !h
L04530                       dz3d         ,zi3d           ,h2osoi_vol3d ,h2osoi_liq3d    ,&
L04531                       h2osoi_ice3d ,t_grnd2d       ,t_soisno3d   ,t_lake3d        ,&
L04532                       savedtke12d  ,lake_icefrac3d                                ,&
L04533  #if ( EM_CORE==1)
L04534    !                   lakemask  ,lakeflag                                         ,&
L04535                       lakemask                                           ,&
L04536  #endif
L04537                       hfx          ,lh             ,grdflx       ,tsk             ,&  !o
L04538                       qfx          ,t2             ,th2          ,q2 )
L04539   
L04540   
L04541        ENDDO
L04542   
L04543     ENDIF
L04544  
L04545  ! Reset RAINBL in mm (Accumulation between PBL calls)
L04546  
L04547       IF ( PRESENT( rainbl ) ) THEN
L04548         !$OMP PARALLEL DO   &
L04549         !$OMP PRIVATE ( ij, i, j, k )
L04550         DO ij = 1 , num_tiles
L04551           DO j=j_start(ij),j_end(ij)
L04552           DO i=i_start(ij),i_end(ij)
L04553              RAINBL(i,j) = 0.
L04554           ENDDO
L04555           ENDDO
L04556         ENDDO
L04557         !$OMP END PARALLEL DO
L04558       ENDIF
L04559  
L04560  ! Limit Q2 diagnostic to no more than 5 per cent higher than lowest level value
L04561  !     This prevents unrealistic values when QFX is not mostly surface flux 
L04562  !          because calculation is based on surface flux only
L04563  !     Problems occurred in transition periods and weak winds and vegetation source
L04564         !$OMP PARALLEL DO   &
L04565         !$OMP PRIVATE ( ij, i, j, k )
L04566         DO ij = 1 , num_tiles
L04567           DO j=j_start(ij),j_end(ij)
L04568           DO i=i_start(ij),i_end(ij)
L04569              IF (XLAND(I,J).LT.1.5) THEN
L04570              Q2(i,j) = MIN(Q2(i,j),1.05*QV_CURR(i,1,j))
L04571              END IF
L04572           ENDDO
L04573           ENDDO
L04574         ENDDO
L04575         !$OMP END PARALLEL DO
L04576  
L04577       IF( PRESENT(slope_rad).AND. radiation )THEN
L04578  ! topographic slope effects removed from SWDOWN and GSW here for output
L04579         IF (slope_rad .EQ. 1) THEN
L04580  
L04581         !$OMP PARALLEL DO   &
L04582         !$OMP PRIVATE ( ij, i, j, k )
L04583         DO ij = 1 , num_tiles
L04584           DO j=j_start(ij),j_end(ij)
L04585           DO i=i_start(ij),i_end(ij)
L04586           IF(SWNORM(I,J) .GT. 1.E-3)THEN  ! daytime
L04587              SWSAVE = SWDOWN(i,j)
L04588  ! SWDOWN contains unaffected SWDOWN in output
L04589              SWDOWN(i,j) = SWNORM(i,j)
L04590  ! SWNORM contains slope-affected SWDOWN in output
L04591              SWNORM(i,j) = SWSAVE
L04592              GSW(i,j) = GSWSAVE(i,j)
L04593           ENDIF
L04594           ENDDO
L04595           ENDDO
L04596         ENDDO
L04597         !$OMP END PARALLEL DO
L04598  
L04599         ENDIF
L04600       ENDIF
L04601  
L04602       IF (distributed_ahe_opt == 2) THEN
L04603         call cal_mon_day(julday, julyr, jmonth, jday)
L04604         ihour = (jmonth - 1) * 24 + MOD(INT(gmt + xtime / 60.0), 24)
L04605         !$OMP PARALLEL DO   &
L04606         !$OMP PRIVATE ( ij, i, j, k )
L04607         DO ij = 1, num_tiles
L04608           DO j = j_start(ij), j_end(ij)
L04609           DO i = i_start(ij), i_end(ij)
L04610             HFX(i, j) = HFX(i, j) + ahe(i, ihour, j)
L04611           END DO
L04612           END DO
L04613         END DO
L04614         !$OMP END PARALLEL DO
L04615       END IF
L04616  
L04617     ENDIF run_param_if
L04618  
L04619     END SUBROUTINE surface_driver
```

> 讲解：两族 SELECT 之后的五件事：①**海洋混合层** sf_ocean_physics∈{OML,PWP3D}：ocean_driver 用 Pollard–Rhines–Thompson 型夹卷更新 TML/HML——海温反馈的简单化替身；②**湖泊模型** LakeModel=1：CLM-Lake（三维湖体分层的完整调用——水体温盐态 h2osoi_*/t_lake3d 直接覆盖 tsk/hfx）；③RAINBL 清零（本次陆面步的水账结清，下个 PBL 步重新累计）；④**Q2 限幅** min(Q2, 1.05·QV(1))——注释解释了原因：2 m 比湿由表面通量外插，弱风/植被蒸腾时段会失真，全 driver 统一兜底（与 [code_10](code_10_module_sf_mynnsfc.md) §4.3 S10 的方案内限幅双保险）；⑤**坡地辐射 SWDOWN/SWNORM 互换**（slope_rad=1 时输出用坡地修正值）与 **distributed_ahe_opt=2：AHE 直接加进 HFX**——对照 [code_22](code_22_module_pbl_driver.md) 的 =1 路径（加最低层 RTHBLTEN）：两条人为热进场线，=1 走动力倾向（PBL 感受）、=2 走面层通量（LSM/PBL 同时感受），论文 2 选择时注意口径差异。

## 七、MYNN 海冰 wrapper（全文）

<!-- code_extract code_extract.py v1.2
source: phys/module_surface_driver.F
ranges: L5361-L5695
file_lines: 7428
file_md5: e86f31fb163f96f7b7f958865de1085c
display: line-numbered (strip L-prefix and !file: line to restore)
range_md5: 3d90a5a11a31f052dd8586c535a22718
seg_lines: 335
label: subroutine mynn_seaice_wrapper
-->

```fortran
!file: phys/module_surface_driver.F    L5361-L5695    (subroutine mynn_seaice_wrapper)
L05361     SUBROUTINE mynn_seaice_wrapper(U3D,V3D,T3D,QV3D,                &
L05362                P3D,dz8w,th3d,rho,                                   &
L05363                PSFC,CHS,CHS2,CQS,CQS2,CPM,                          &
L05364                ZNT,UST,PBLH,MAVAIL,ZOL,MOL,PSIM,PSIH,               &
L05365                XLAND,HFX,QFX,LH,TSK,FLHC,FLQC,QSFC,RMOL,QGH,        &
L05366                U10,V10,TH2,T2,Q2,SNOWH,                             &
L05367                GZ1OZ0,WSPD,BR,ISFFLX,DX,                            &
L05368                &itimestep,ch,                                       &
L05369                &spp_pbl,pattern_spp_pbl,                            &
L05370                XICE,SST,TSK_SEA,QGH_SEA,                            &
L05371                CHS2_SEA,CHS_SEA,CPM_SEA,CQS2_SEA,FLHC_SEA,FLQC_SEA, &
L05372                HFX_SEA,LH_SEA,QFX_SEA,QSFC_SEA,ZNT_SEA,             &
L05373                TICE2TSK_IF2COLD,XICE_THRESHOLD,                     &
L05374                ids,ide, jds,jde, kds,kde,                           &
L05375                ims,ime, jms,jme, kms,kme,                           &
L05376                its,ite, jts,jte, kts,kte,                           &
L05377                ustm,ck,cka,cd,cda,                                  &
L05378                sf_mynn_sfcflux_land,sf_mynn_sfcflux_water,          &
L05379                flag_lsm,restart,                                    &
L05380                shalwater_z0,water_depth,lakemask,                   &
L05381                errmsg,errflg                                        )
L05382  
L05383       USE module_sf_mynnsfc_driver
L05384  
L05385       implicit none
L05386  
L05387       !--- ccpp arguments:
L05388       character(len=*), intent(inout) :: errmsg
L05389       integer,          intent(inout) :: errflg
L05390  
L05391       INTEGER,  INTENT(IN )   ::       ids,ide, jds,jde, kds,kde,  &
L05392                                        ims,ime, jms,jme, kms,kme,  &
L05393                                        its,ite, jts,jte, kts,kte
L05394       INTEGER,  INTENT(IN )   ::       itimestep, ISFFLX
L05395       INTEGER,  INTENT(IN ), optional ::  sf_mynn_sfcflux_land,    &
L05396                                           sf_mynn_sfcflux_water,   &
L05397                                           flag_lsm,                &
L05398                                           shalwater_z0
L05399       LOGICAL,  INTENT(IN)    ::        restart
L05400       INTEGER,  INTENT(IN), optional      ::     spp_pbl
L05401       REAL,     DIMENSION( ims:ime, kms:kme, jms:jme ),            &
L05402                 INTENT(IN), OPTIONAL      ::   pattern_spp_pbl
L05403  
L05404       REAL,     DIMENSION( ims:ime, kms:kme, jms:jme )           , &
L05405                 INTENT(IN   )   ::                           dz8w, &
L05406                                                              QV3D, &
L05407                                                               P3D, &
L05408                                                               T3D, &
L05409                                                               U3D, &
L05410                                                               V3D, &
L05411                                                          rho,th3d
L05412  
L05413       REAL,     DIMENSION( ims:ime, jms:jme )                    , &
L05414                 INTENT(IN   )               ::             MAVAIL, &
L05415                                                             XLAND, &
L05416                                                       water_depth, &
L05417                                                          lakemask, &
L05418                                                              PSFC, &
L05419                                                             SNOWH, &
L05420                                                               TSK, &
L05421                                                                dx
L05422  
L05423       REAL,     DIMENSION( ims:ime, jms:jme )                    , &
L05424                 INTENT(OUT  )               ::                U10, &
L05425                                                               V10, &
L05426                                                               TH2, &
L05427                                                                T2, &
L05428                                                                Q2
L05429  
L05430       REAL,     DIMENSION( ims:ime, jms:jme )                    , &
L05431                 INTENT(INOUT)               ::               PBLH, &
L05432                                                               HFX, &
L05433                                                               QFX, &
L05434                                                                LH, &
L05435                                                          MOL,RMOL, &
L05436                                                              QSFC, &
L05437                                                               QGH, &
L05438                                                               ZNT, &
L05439                                                               ZOL, &
L05440                                                               UST, &
L05441                                                               CPM, &
L05442                                                              CHS2, &
L05443                                                               CQS, &
L05444                                                              CQS2, &
L05445                                                               CHS, &
L05446                                                                CH, &
L05447                                                         FLHC,FLQC, &
L05448                                                    GZ1OZ0,WSPD,BR, &
L05449                                                         PSIM,PSIH
L05450  
L05451       REAL,     DIMENSION( ims:ime, jms:jme )                    , &
L05452                 INTENT(OUT), OPTIONAL  ::      ck,cka,cd,cda,ustm
L05453  
L05454  !--------------------------------------------------------------------
L05455  !    New for wrapper
L05456  !--------------------------------------------------------------------
L05457       LOGICAL,  INTENT(IN)               ::      TICE2TSK_IF2COLD
L05458       REAL,     INTENT(IN)               ::      XICE_THRESHOLD
L05459       REAL,     DIMENSION( ims:ime, jms:jme ),                     &
L05460                 INTENT(IN)               ::      XICE
L05461       REAL,     DIMENSION( ims:ime, jms:jme ),                     &
L05462                 INTENT(INOUT)            ::      SST
L05463       REAL,     DIMENSION( ims:ime, jms:jme ), OPTIONAL,           &
L05464                 INTENT(OUT)              ::      TSK_SEA,          &
L05465                                                  CHS2_SEA,         &
L05466                                                  CHS_SEA,          &
L05467                                                  CPM_SEA,          &
L05468                                                  CQS2_SEA,         &
L05469                                                  FLHC_SEA,         &
L05470                                                  FLQC_SEA,         &
L05471                                                  HFX_SEA,          &
L05472                                                  LH_SEA,           &
L05473                                                  QFX_SEA,          &
L05474                                                  QGH_SEA,          &
L05475                                                  QSFC_SEA,         &
L05476                                                  ZNT_SEA
L05477  
L05478  !--------------------------------------------------------------------
L05479  !    Local
L05480  !--------------------------------------------------------------------
L05481       INTEGER :: I, J
L05482       REAL,     DIMENSION( ims:ime, jms:jme ) :: TSK_LOCAL,        &
L05483                   XLAND_SEA,                                       &
L05484                   MAVAIL_sea,                                      &
L05485                   BR_SEA,                        BR_HOLD,          &
L05486                                                  FLHC_HOLD,        &
L05487                                                  FLQC_HOLD,        &
L05488                   GZ1OZ0_SEA,                    GZ1OZ0_HOLD,      &
L05489                                                  HFX_HOLD,         &
L05490                                                  LH_HOLD,          &
L05491                   CH_SEA,                                          &
L05492                   MOL_SEA,                       MOL_HOLD,         &
L05493                   PSIH_SEA,                      PSIH_HOLD,        &
L05494                   PSIM_SEA,                      PSIM_HOLD,        &
L05495                                                  QFX_HOLD,         &
L05496                                                  QGH_HOLD,         &
L05497                                                  CPM_HOLD,         &
L05498                   RMOL_SEA,                      RMOL_HOLD,        &
L05499                   UST_SEA,                       UST_HOLD,         &
L05500                   WSPD_SEA,                      WSPD_HOLD,        &
L05501                                                  ZNT_HOLD,         &
L05502                   ZOL_SEA,                       ZOL_HOLD,         &
L05503                   Q2_SEA,                                          &
L05504                   T2_SEA,                                          &
L05505                   TH2_SEA,                                         &
L05506                   U10_SEA,                                         &
L05507                   V10_SEA,                                         &
L05508                   CD_SEA,                                          &
L05509                   CDA_SEA,                                         &
L05510                   CK_SEA,                                          &
L05511                   CKA_SEA,                                         &
L05512                   USTM_SEA,                      USTM_HOLD
L05513  
L05514  
L05515      CALL get_local_ice_tsk( ims, ime, jms, jme, its, ite, jts, jte,  &
L05516                              itimestep, .true., tice2tsk_if2cold,     &
L05517                              XICE, XICE_THRESHOLD,                    &
L05518                              SST, TSK, TSK_SEA, TSK_LOCAL )
L05519  
L05520  
L05521  ! DFS 8/25/10 Set TSK to ice value
L05522  !    DO j = JTS , JTE
L05523  !        DO i = ITS , ITE
L05524  !            TSK(i,j) = TSK_LOCAL(i,j)
L05525  !        ENDDO
L05526  !    ENDDO
L05527        
L05528  ! Save the variables before the first call
L05529  ! (for land/frozen water) to SFCLAY_mynn.
L05530       BR_HOLD(its:ite,jts:jte)   = BR(its:ite,jts:jte)
L05531       CPM_HOLD(its:ite,jts:jte)  = CPM(its:ite,jts:jte)
L05532       FLHC_HOLD(its:ite,jts:jte) = FLHC(its:ite,jts:jte)
L05533       FLQC_HOLD(its:ite,jts:jte) = FLQC(its:ite,jts:jte)
L05534       GZ1OZ0_HOLD(its:ite,jts:jte) = GZ1OZ0(its:ite,jts:jte)
L05535       HFX_HOLD(its:ite,jts:jte)  = HFX(its:ite,jts:jte)
L05536       LH_HOLD(its:ite,jts:jte)   = LH(its:ite,jts:jte)
L05537       MOL_HOLD(its:ite,jts:jte)  = MOL(its:ite,jts:jte)
L05538       PSIH_HOLD(its:ite,jts:jte) = PSIH(its:ite,jts:jte)
L05539       PSIM_HOLD(its:ite,jts:jte) = PSIM(its:ite,jts:jte)
L05540       QFX_HOLD(its:ite,jts:jte)  = QFX(its:ite,jts:jte)
L05541       QGH_HOLD(its:ite,jts:jte)  = QGH(its:ite,jts:jte)
L05542       RMOL_HOLD(its:ite,jts:jte) = RMOL(its:ite,jts:jte)
L05543       UST_HOLD(its:ite,jts:jte)  = UST(its:ite,jts:jte)
L05544       USTM_HOLD(its:ite,jts:jte) = USTM(its:ite,jts:jte)
L05545       WSPD_HOLD(its:ite,jts:jte) = WSPD(its:ite,jts:jte)
L05546       ZNT_HOLD(its:ite,jts:jte)  = ZNT(its:ite,jts:jte)
L05547       ZOL_HOLD(its:ite,jts:jte)  = ZOL(its:ite,jts:jte)
L05548  
L05549       ! We'll want to save the ouput
L05550       ! for weighting after the second call to SFCLAY.
L05551  
L05552       ! land/frozen-water call
L05553            CALL mynnsfc_driver(u3d=u3d,v3d=v3d,t3d=t3d,         &
L05554                 qv3d=qv3d,p3d=p3d,dz8w=dz8w,th3d=th3d,          &
L05555                 rho3d=rho,psfcpa=psfc,                          &
L05556                 chs=chs,chs2=chs2,cqs=cqs,cqs2=cqs2,cpm=cpm,    &
L05557                 znt=znt,ust=ust,pblh=pblh,mavail=mavail,zol=zol,&
L05558                 mol=mol,psim=psim,psih=psih,qgh=qgh,            &
L05559                 xland=xland,hfx=hfx,qfx=qfx,lh=lh,tsk=tsk_local,&
L05560                 flhc=flhc,flqc=flqc,qsfc=qsfc,rmol=rmol,        &
L05561                 u10=u10,v10=v10,th2=th2,t2=t2,q2=q2,snowh=snowh,&
L05562                 gz1oz0=gz1oz0,wspd=wspd,br=br,dx=dx,            &
L05563                 itimestep=itimestep,ch=ch,                      &
L05564                 spp_pbl=spp_pbl,pattern_spp_pbl=pattern_spp_pbl,&
L05565                 ids=ids,ide=ide,jds=jds,jde=jde,kds=kds,kde=kde,&
L05566                 ims=ims,ime=ime,jms=jms,jme=jme,kms=kms,kme=kme,&
L05567                 its=its,ite=ite,jts=jts,jte=jte,kts=kts,kte=kte,&
L05568                 ustm=ustm,ck=ck,cka=cka,cd=cd,cda=cda,          &
L05569                 xice=xice,xice_threshold=xice_threshold,        &
L05570                 sf_mynn_sfcflux_land=sf_mynn_sfcflux_land,      &
L05571                 sf_mynn_sfcflux_water=sf_mynn_sfcflux_water,    &
L05572                 isfflx=isfflx,shalwater_z0=shalwater_z0,        &
L05573                 water_depth=water_depth,lakemask=lakemask,      &
L05574                 flag_lsm=flag_lsm,restart=restart,              &
L05575                 errmsg=errmsg,errflg=errflg                     )
L05576  
L05577       ! Set up lower boundary conditions to force an open-water call
L05578        DO j = JTS , JTE
L05579          DO i = ITS , ITE
L05580             IF ( ( XICE(i,j) .GE. XICE_THRESHOLD ) .and. ( XICE(i,j) .LE. 1.0 ) ) THEN
L05581                XLAND_SEA(i,j) = 2. !water
L05582                MAVAIL_SEA(i,j)= 1.
L05583                ZNT_SEA(i,j)   = 0.0001 !will be recalculated anyway
L05584                TSK_SEA(i,j)   = SST(i,j)
L05585                IF ( SST(i,j) .LT. 271.4 ) THEN
L05586                   SST(i,j)    = 271.4
L05587                   TSK_SEA(i,j)= SST(i,j)
L05588                ENDIF
L05589                QSFC_SEA(i,j)  = QSFC(i,j) !will be recalculated anyway
L05590             ELSE
L05591                !keep original values
L05592                XLAND_SEA(i,j) = XLAND(i,j)
L05593                MAVAIL_SEA(i,j)= MAVAIL(i,j)
L05594                ZNT_SEA(i,j)   = ZNT_HOLD(i,j)
L05595                TSK_SEA(i,j)   = TSK_LOCAL(i,j)
L05596                QSFC_SEA(i,j)  = QSFC(i,j)
L05597             ENDIF
L05598          ENDDO
L05599       ENDDO
L05600  
L05601       ! Restore the values from before the land/frozen-water call
L05602       BR_SEA(its:ite,jts:jte)   = BR_HOLD(its:ite,jts:jte)
L05603       CPM_SEA(its:ite,jts:jte)  = CPM_HOLD(its:ite,jts:jte)
L05604       FLHC_SEA(its:ite,jts:jte) = FLHC_HOLD(its:ite,jts:jte)
L05605       FLQC_SEA(its:ite,jts:jte) = FLQC_HOLD(its:ite,jts:jte)
L05606       GZ1OZ0_SEA(its:ite,jts:jte) = GZ1OZ0_HOLD(its:ite,jts:jte)
L05607       HFX_SEA(its:ite,jts:jte)  = HFX_HOLD(its:ite,jts:jte)
L05608       LH_SEA(its:ite,jts:jte)   = LH_HOLD(its:ite,jts:jte)
L05609       MOL_SEA(its:ite,jts:jte)  = MOL_HOLD(its:ite,jts:jte)
L05610       PSIH_SEA(its:ite,jts:jte) = PSIH_HOLD(its:ite,jts:jte)
L05611       PSIM_SEA(its:ite,jts:jte) = PSIM_HOLD(its:ite,jts:jte)
L05612       QFX_SEA(its:ite,jts:jte)  = QFX_HOLD(its:ite,jts:jte)
L05613       QGH_SEA(its:ite,jts:jte)  = QGH_HOLD(its:ite,jts:jte)
L05614       RMOL_SEA(its:ite,jts:jte) = RMOL_HOLD(its:ite,jts:jte)
L05615       UST_SEA(its:ite,jts:jte)  = UST_HOLD(its:ite,jts:jte)
L05616       USTM_SEA(its:ite,jts:jte) = USTM_HOLD(its:ite,jts:jte)
L05617       WSPD_SEA(its:ite,jts:jte) = WSPD_HOLD(its:ite,jts:jte)
L05618       ZOL_SEA(its:ite,jts:jte)  = ZOL_HOLD(its:ite,jts:jte)
L05619  
L05620  
L05621       ! open-water call
L05622        CALL mynnsfc_driver(u3d=u3d,v3d=v3d,t3d=t3d,                             &
L05623             qv3d=qv3d,p3d=p3d,dz8w=dz8w,th3d=th3d,rho3d=rho,psfcpa=psfc,        &
L05624             chs=chs_sea,chs2=chs2_sea,cqs=cqs,cqs2=cqs2_sea,cpm=cpm_sea,        &
L05625             znt=znt_sea,ust=ust_sea,pblh=pblh,mavail=mavail_sea,zol=zol_sea,    &
L05626             mol=mol_sea,psim=psim_sea,psih=psih_sea,qgh=qgh_sea,                &
L05627             xland=xland_sea,hfx=hfx_sea,qfx=qfx_sea,lh=lh_sea,tsk=tsk_sea,      &
L05628             flhc=flhc_sea,flqc=flqc_sea,qsfc=qsfc_sea,rmol=rmol_sea,            &
L05629             u10=u10_sea,v10=v10_sea,th2=th2_sea,t2=t2_sea,q2=q2_sea,snowh=snowh,&
L05630             gz1oz0=gz1oz0_sea,wspd=wspd_sea,br=br_sea,dx=dx,                    &
L05631             itimestep=itimestep,ch=ch,                                          &
L05632             spp_pbl=spp_pbl,pattern_spp_pbl=pattern_spp_pbl,                    &
L05633             ids=ids,ide=ide, jds=jds,jde=jde, kds=kds,kde=kde,                  &
L05634             ims=ims,ime=ime, jms=jms,jme=jme, kms=kms,kme=kme,                  &
L05635             its=its,ite=ite, jts=jts,jte=jte, kts=kts,kte=kte,                  &
L05636             ustm=ustm_sea,ck=ck_sea,cka=cka_sea,cd=cd_sea,cda=cda_sea,          &
L05637             xice=xice,xice_threshold=xice_threshold,                            &
L05638             sf_mynn_sfcflux_land=sf_mynn_sfcflux_land,                          &
L05639             sf_mynn_sfcflux_water=sf_mynn_sfcflux_water,isfflx=isfflx,          &
L05640             flag_lsm=flag_lsm,restart=restart,                                  &
L05641             errmsg=errmsg,errflg=errflg                                         )
L05642                 
L05643       DO j = JTS , JTE
L05644          DO i = ITS, ITE
L05645             IF ( ( XICE(I,J) .GE. XICE_THRESHOLD )  .and.( XICE(i,j) .LE. 1.0 ) ) THEN
L05646                ! weighted average for sea ice points
L05647                br(i,j)     = br(i,j)     * XICE(i,j) + (1.0-XICE(i,j)) * br_sea(i,j)
L05648                ! CHS2 -- wait
L05649                ! CHS  -- wait
L05650                ! CPM  -- wait
L05651                ! CQS2 -- wait
L05652                !FLHC(i,j)   = FLHC(i,j)   * XICE(i,j) + (1.0-XICE(i,j)) * FLHC_SEA (i,j)
L05653                !FLQC(i,j)   = FLQC(i,j)   * XICE(i,j) + (1.0-XICE(i,j)) * FLQC_SEA (i,j)
L05654                gz1oz0(i,j) = gz1oz0(i,j) * XICE(i,j) + (1.0-XICE(i,j)) * gz1oz0_sea(i,j)
L05655                ! HFX  -- wait
L05656                ! LH   -- wait
L05657                mol(i,j)    = mol(i,j)    * XICE(i,j) + (1.0-XICE(i,j)) * mol_sea(i,j)
L05658                psih(i,j)   = psih(i,j)   * XICE(i,j) + (1.0-XICE(i,j)) * psih_sea(i,j)
L05659                psim(i,j)   = psim(i,j)   * XICE(i,j) + (1.0-XICE(i,j)) * psim_sea(i,j)
L05660                ! QFX  -- wait
L05661                ! QGH  -- wait
L05662                rmol(i,j)   = rmol(i,j)   * XICE(i,j) + (1.0-XICE(i,j)) * rmol_sea(i,j)
L05663                ust(i,j)    = ust(i,j)    * XICE(i,j) + (1.0-XICE(i,j)) * ust_sea(i,j)
L05664                wspd(i,j)   = wspd(i,j)   * XICE(i,j) + (1.0-XICE(i,j)) * wspd_sea(i,j)
L05665                zol(i,j)    = zol(i,j)    * XICE(i,j) + (1.0-XICE(i,j)) * zol_sea(i,j)
L05666                ch(i,j)     = ch(i,j)     * XICE(i,j) + (1.0-XICE(i,j)) * ch_sea(i,j)
L05667                ! INTENT(OUT)
L05668                ! --------------------------------------------------------------------
L05669                IF ( PRESENT ( CD ) ) THEN
L05670                   CD(i,j)  = CD(i,j)  * XICE(i,j) + (1.0-XICE(i,j)) * CD_sea(i,j)
L05671                ENDIF
L05672                IF ( PRESENT ( CDA ) ) THEN
L05673                   CDA(i,j) = CDA(i,j) * XICE(i,j) + (1.0-XICE(i,j)) * CDA_sea(i,j)
L05674                ENDIF
L05675                IF ( PRESENT ( CK ) ) THEN
L05676                   CK(i,j)  = CK(i,j)  * XICE(i,j) + (1.0-XICE(i,j)) * CK_sea(i,j)
L05677                ENDIF
L05678                IF ( PRESENT ( CKA ) ) THEN
L05679                   CKA(i,j) = CKA(i,j) * XICE(i,j) + (1.0-XICE(i,j)) * CKA_sea(i,j)
L05680                ENDIF
L05681                q2(i,j)     = q2(i,j)  * XICE(i,j) + (1.0-XICE(i,j)) * q2_sea(i,j)
L05682                ! QSFC -- wait
L05683                t2(i,j)     = t2(i,j)  * XICE(i,j) + (1.0-XICE(i,j)) * t2_sea(i,j)
L05684                th2(i,j)    = th2(i,j) * XICE(i,j) + (1.0-XICE(i,j)) * th2_sea(i,j)
L05685                u10(i,j)    = u10(i,j) * XICE(i,j) + (1.0-XICE(i,j)) * u10_sea(i,j)
L05686                IF ( PRESENT ( USTM ) ) THEN
L05687                   USTM(i,j)= USTM(i,j)* XICE(i,j) + (1.0-XICE(i,j)) * USTM_sea(i,j)
L05688                ENDIF
L05689                v10(i,j)    = v10(i,j) * XICE(i,j) + (1.0-XICE(i,j)) * v10_sea(i,j)
L05690             ENDIF
L05691          END DO
L05692        END DO
L05693  
L05694  
L05695     END SUBROUTINE mynn_seaice_wrapper
```

> 讲解：MYNNSFCSCHEME CASE 的前置件（主入口 L2431 调用）：对 xice≥xice_threshold 的点，把海冰点的水面状态冻结（TSK 置冰点附近、ZNT 用冰粗糙度、QSFC 按冰面饱和）后调 mynnsfc_driver——**海冰点不另走 ice 方案文件，而是在 wrapper 里先改下边界状态**。与 [code_10](code_10_module_sf_mynnsfc.md) §三的「mynnsfc_driver 三路分派」衔接：wrapper 改的是 driver 的输入而非分派逻辑。七个 *_seaice_wrapper（myj/qnse/gfs/sfclayrev/sfclay/px/mynn）是各面层方案对部分海冰的各自应对——改造海冰处理时七处都要排查。

## 八、改造入口

1. **新增面层方案**：sfclay_select 加 CASE + USE + Registry package（三步同 [code_22](code_22_module_pbl_driver.md) §五）；海冰点需同步写 *_seaice_wrapper。
2. **新增陆面方案/耦合外源**：sfc_select 加 CASE；SST/海冰/湖泊通道见 §三/§六。
3. **人为热**：distributed_ahe_opt=1（pbl driver）vs =2（本文件）的口径选择。
4. **诊断口径**：Q2 双重限幅（方案内+driver 兜底）——改 MYNN 诊断时两处一致性要查。

## 九、上下游链接

- 上游：dyn_em/module_first_rk_step_part1.F（31 篇待交付，先于 pbl_driver 调用）。
- 下游：面层族 [code_10_module_sf_mynnsfc.md](code_10_module_sf_mynnsfc.md)（MYNN）；陆面族 Noah（12/13 篇待交付）；城市冠层经 pbl driver（[code_14a](code_14a_module_sf_bep_bem.md)/[code_16](code_16_module_sf_bem.md)）。
- 教材正文：[ch16_land_surface_family.md](../ch16_land_surface_family.md)、[ch14_pbl_family.md](../ch14_pbl_family.md)、[ch17_urban_canopy.md](../ch17_urban_canopy.md)、[ch19_lanzhou_heatwave.md](../ch19_lanzhou_heatwave.md)、[ch21_solve_em_dynamics.md](../ch21_solve_em_dynamics.md)。
