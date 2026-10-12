# code_16 — BEM 建筑能量模型（module_sf_bem.F 全文精读）

## 一、版本指纹

| 源文件 | 行数 | md5（整文件，按字节） |
|---|---|---|
| phys/module_sf_bem.F | 2636 | e93033f4eff5816a89e6cf51c65d738a |

- 抽取工具：workspace/scripts/code_extract.py v1.2，2026-10-12；块首指纹注释自带 range_md5。
- 本篇 A 级全文（26 单元全收）。被调方：module_sf_bep_bem.F 的 BEP1D（[code_14a](code_14a_module_sf_bep_bem.md) §五⑨ 的 BEM 循环——每时间步每格点每建筑型调一次）。

## 二、定位

一句话：BEM（Salamanca–Martilli 建筑能量模型）——把每栋「建筑型」当一组多层墙/楼板/窗户围合的空调房间，解室内气温/比湿的演化方程，输出空调废热、耗电、通风热与 PV 发电；它是**论文 2 的直接改造对象**（cal-steel 标定参数 cop/beta/targtemp… 目前是类级标量，改造目标 = 逐格场）。

**物理边界**（BEM 管什么 / 不管什么）：管——室内空气能量与水分收支、围护结构多层导热、室内外辐射交换、通风与空调；不管——城市峡谷气象（BEP 管，14a/14b）、墙外侧温度（来自 BEP 的 wall/roof 状态）。

**六面房间约定**（文件头 ASCII 图）：面 1/2=东西墙（bw·dzlev）、3/4=南北墙（bl·dzlev）、5=地板（bw·bl）、6=天花板（bw·bl）；底层面 5 接楼下地基 tgrd、顶层面 6 接屋顶 trof；窗户按 pwin 占比嵌在四面竖墙上。

## 三、文件头：BEM 物理常数

<!-- code_extract code_extract.py v1.2
source: phys/module_sf_bem.F
ranges: L1-L36
file_lines: 2636
file_md5: e93033f4eff5816a89e6cf51c65d738a
display: line-numbered (strip L-prefix and !file: line to restore)
range_md5: 0fa45c9c80f7d6a206d4088fa5d31e72
seg_lines: 36
-->

```fortran
!file: phys/module_sf_bem.F    L1-L36
L00001  MODULE module_sf_bem
L00002  #if defined(mpas)
L00003  use mpas_atmphys_utilities, only: physics_error_fatal
L00004  #define FATAL_ERROR(M) call physics_error_fatal( M )
L00005  #else
L00006  use module_wrf_error
L00007  #define FATAL_ERROR(M) call wrf_error_fatal( M )
L00008  #endif
L00009  ! -----------------------------------------------------------------------
L00010  !  Variables and constants used in the BEM module
L00011  ! -----------------------------------------------------------------------
L00012           
L00013          real emins		!emissivity of the internal walls
L00014          parameter (emins=0.9) 
L00015          real albins	        !albedo of the internal walls
L00016  !!      parameter (albins=0.5)
L00017          parameter (albins=0.3)
L00018  
L00019          real thickwin           !thickness of the window [m] 
L00020          parameter (thickwin=0.006)
L00021          real cswin		!Specific heat of the windows [J/(m3.K)]
L00022          parameter(cswin= 2.268e+06)
L00023  
L00024          real temp_rat            !power of the A.C. heating/cooling the indoor air [K/s]
L00025          parameter(temp_rat=0.001)
L00026  
L00027          real hum_rat            !power of the A.C. drying/moistening the indoor air [(Kg/kg)/s]
L00028          parameter(hum_rat=1.e-06)
L00029  
L00030          real,parameter :: effpv=0.19  ! Efficiency of PV panels installed at the roofs, typical values [0.10,0.15] 
L00031  
L00032      CONTAINS
L00033  
L00034  !====6================================================================72
L00035  !====6================================================================72	
L00036  	
```

> 讲解：①室内表面发射率 emins=0.9、反照率 albins=0.3（曾被 0.5，注释在案）；②窗户厚 6 mm、热容 2.268e6 J/(m³·K)——窗户按**单层集总热容**演化；③temp_rat=0.001 K/s 与 hum_rat=1e-6 (kg/kg)/s 是空调的**最大调温/调湿速率**（防室内状态突变）；④effpv=0.19 光伏效率（注释给出典型区间 0.10–0.15，实际用了偏高值——论文 2 做 PV 敏感性实验时的第一检查点）。**论文 2 改造提示：这五个 parameter 是模块级硬编码，逐格场化时最先要「参数场化」的就是它们与 cop/beta 族 TBL 标量。**

## 四、主入口 BEM（全文）

<!-- code_extract code_extract.py v1.2
source: phys/module_sf_bem.F
ranges: L37-L820
file_lines: 2636
file_md5: e93033f4eff5816a89e6cf51c65d738a
display: line-numbered (strip L-prefix and !file: line to restore)
range_md5: 51f17017b80681e41faaade8cd496fcc
seg_lines: 784
label: subroutine BEM
-->

```fortran
!file: phys/module_sf_bem.F    L37-L820    (subroutine BEM)
L00037  	subroutine BEM(nzcanm,nlev,nhourday,dt,bw,bl,dzlev,            &
L00038                         nwal,nflo,nrof,ngrd,hswalout,gswal,             &
L00039                         hswinout,hsrof,lsrof,gsrof,hspv,                &
L00040                         latent,sigma,albwal,albwin,albrof,              &
L00041       		       emrof,emwal,emwin,rswal,rlwal,rair,cp,          &
L00042       		       rhoout,tout,humout,press,                       &
L00043       		       rs,swddif,rl,dzwal,cswal,kwal,pwin,cop,beta,sw_cond,   &
L00044                         timeon,timeoff,targtemp,gaptemp,targhum,gaphum, &
L00045                         perflo,gr_frac_roof,pv_frac_roof,gr_flag, & 
L00046                         uout,vout,                                        &
L00047                         hsesf,hsequip,dzflo,                            &
L00048       		       csflo,kflo,dzgrd,csgrd,kgrd,dzrof,csrof,        &
L00049       		       krof,tlev,shumlev,twal,twin,tflo,tgrd,trof,     &
L00050       		       hsout,hlout,consump,eppv,tpv,hsvent,hlvent,hfgr,&
L00051                         tr_av,tpv_print,sfpv,sfr_indoor)
L00052  
L00053  
L00054  
L00055  
L00056  ! ---------------------------------------------------------------------
L00057  	implicit none
L00058  	
L00059  ! ---------------------------------------------------------------------	
L00060  !		       TOP
L00061  !	      ---------------------	
L00062  !	      !	----------------- !--->roof	(-) : level number	
L00063  !	      !	!		! !		rem: the windows are given 
L00064  !	      !	!---------------! !                  with respect to the 
L00065  !	      !	!---------------! !                  vertical walls-->win(2) 
L00066  !	   (n)! !(1)	     (1)!-!(n)
L00067  !	      !	!---------------! !		2D vision of the building
L00068  !   WEST      ! !-------4-------! !	EAST
L00069  !	    I ! ! 1    ilev    2! ! II               ^
L00070  !	      !	!-------3--------! !		     !  	
L00071  !	      ! !---------------! !--->floor 1	     ! 				
L00072  !	      !	!		! !                  !
L00073  !	      ! !		! !                  !
L00074  !	      !	----------------- !          <--------------(n)  	
L00075  !	      ------------------------>ground	------------(1)
L00076  !		     BOTTOM
L00077  !				i(6)			
L00078  !			        i
L00079  !                     +---------v-----+ 
L00080  !                    /|              /|    3D vision of a room	
L00081  !                   / | 4           / |		
L00082  !                  /  |            /  |
L00083  !                 /   |           /   |
L00084  !                /    |          /    |
L00085  !               +---------------+     |
L00086  !               |  1   |        |  2  |
L00087  !               |     +---------|-----+
L00088  !       dzlev   |    /          |    /
L00089  !               |   /    3      |   /
L00090  !               |  /bw          |  /
L00091  !               | /             | /  
L00092  !               |/              |/
L00093  !               +---------------+
L00094  !                     ^ bl
L00095  !		      i          
L00096  !                     i
L00097  !		     (5)	
L00098  !-----------------------------------------------------------------------
L00099  
L00100  
L00101  ! Input:
L00102  ! -----	
L00103  
L00104  	real dt				!time step [s]
L00105                                         
L00106             integer nzcanm                  !Maximum number of vertical levels in the urban grid
L00107  	integer nlev			!number of floors in the building
L00108  	integer nwal                    !number of levels inside the wall
L00109  	integer nrof                    !number of levels inside the roof
L00110  	integer nflo                    !number of levels inside the floor
L00111  	integer ngrd                    !number of levels inside the ground
L00112  	real dzlev			!vertical grid resolution [m]			
L00113  	real bl				!Building length [m]
L00114  	real bw                         !Building width [m]
L00115  	
L00116  	real albwal			!albedo of the walls 				
L00117  	real albwin		 	!albedo of the windows
L00118  	real albrof			!albedo of the roof
L00119  	
L00120  	real emwal 	          	!emissivity of the walls
L00121  	
L00122  	real emrof			!emissivity of the roof
L00123          real emwin                      !emissivity of the windows
L00124  
L00125  	real pwin                       !window proportion
L00126  	real,    intent(in) :: cop      !Coefficient of performance of the A/C systems
L00127  	real,    intent(in) :: beta     !Thermal efficiency of the heat exchanger
L00128          integer, intent(in) :: sw_cond  ! Air Conditioning switch
L00129          real,    intent(in) :: timeon   ! Initial local time of A/C systems
L00130          real,    intent(in) :: timeoff  ! Ending local time of A/C systems
L00131          real,    intent(in) :: targtemp ! Target temperature of A/C systems
L00132          real,    intent(in) :: gaptemp  ! Comfort range of indoor temperature
L00133          real,    intent(in) :: targhum  ! Target humidity of A/C systems
L00134          real,    intent(in) :: gaphum   ! Comfort range of specific humidity
L00135          real,    intent(in) :: perflo   ! Peak number of occupants per unit floor area
L00136          real gr_frac_roof   
L00137          real pv_frac_roof
L00138          integer gr_flag  
L00139          real   uout(nzcanm) 
L00140          real    vout(nzcanm)
L00141          real,    intent(in) :: hsesf    ! 
L00142          real,    intent(in) :: hsequip(24) ! 
L00143  	
L00144  	real cswal(nwal)		!Specific heat of the wall [J/(m3.K)] 
L00145  	
L00146  	real csflo(nflo)		!Specific heat of the floor [J/(m3.K)]
L00147  	real csrof(nrof)		!Specific heat of the roof [J/(m3.K)] 
L00148  	real csgrd(ngrd)		!Specific heat of the ground [J/(m3.K)]
L00149  	
L00150  	real kwal(nwal+1)		!Thermal conductivity in each layers of the walls (face) [W/(m.K)]
L00151  	real kflo(nflo+1)		!Thermal diffusivity in each layers of the floors (face) [W/(m.K)]
L00152  	real krof(nrof+1)		!Thermal diffusivity in each layers of the roof (face) [W/(m.K)]
L00153  	real kgrd(ngrd+1)		!Thermal diffusivity in each layers of the ground (face) [W/(m.K)]
L00154  	
L00155  	real dzwal(nwal)		!Layer sizes of walls [m]
L00156  	real dzflo(nflo)		!Layer sizes of floors [m]
L00157  	real dzrof(nrof)		!Layer sizes of roof [m]
L00158  	real dzgrd(ngrd)		!Layer sizes of ground [m]
L00159  	real tpv
L00160          real tr_av 
L00161  	real latent                      !latent heat of evaporation [J/Kg]	
L00162  
L00163          real swddif
L00164     	real rs				!external short wave radiation [W/m2]
L00165  	real rl				!external long wave radiation [W/m2]
L00166  	real rswal(4,nzcanm)		!short wave radiation reaching the exterior walls [W/m2]
L00167          real rlwal(4,nzcanm)		!long wave radiation reaching the walls [W/m2]	
L00168  	real rhoout(nzcanm)		!exterior air density [kg/m3]
L00169  	real tout(nzcanm)		!external temperature [K]
L00170  	real humout(nzcanm)		!absolute humidity [Kgwater/Kgair]
L00171  	real press(nzcanm)		!external air pressure [Pa]
L00172  	
L00173  	real hswalout(4,nzcanm)	        !outside walls sensible heat flux [W/m2]
L00174  	real hswinout(4,nzcanm)	        !outside window sensible heat flux [W/m2]
L00175  	real hsrof			!Sensible heat flux at the roof [W/m2]
L00176  	real lsrof
L00177          real rair			!ideal gas constant  [J.kg-1.K-1]
L00178  	real sigma			!parameter (wall is not black body) [W/m2.K4]
L00179  	real cp				!specific heat of air [J/kg.K]
L00180          real hfgr       !Green roof heat flux
L00181  	
L00182  !Input-Output
L00183  !------------
L00184  	real tlev(nzcanm)		!temperature of the floors [K] 
L00185  	real shumlev(nzcanm)		!specific humidity of the floor [kg/kg]
L00186  	real twal(4,nwal,nzcanm)	!walls temperatures [K]
L00187  	real twin(4,nzcanm)		!windows temperatures [K]	
L00188  	real tflo(nflo,nzcanm-1)	!floor temperatures [K]
L00189  	real tgrd(ngrd)		        !ground temperature [K]
L00190  	real trof(nrof)		        !roof temperature [K]
L00191  	real hsout(nzcanm)		!sensible heat emitted outside the floor [W]
L00192  	real hlout(nzcanm)		!latent heat emitted outside the floor [W]
L00193          real consump(nzcanm)            !Consumption for the a.c. in each floor [W]
L00194  	real hsvent(nzcanm)		!sensible heat generated by natural ventilation [W]
L00195  	real hlvent(nzcanm)		!latent heat generated by natural ventilation [W] 
L00196          real gsrof                      !heat flux flowing inside the roof [W/m2]
L00197          real hspv			!Sensible heat flux at the roof from the PV panels [W/m2]
L00198          real gswal(4,nzcanm)             !heat flux flowing inside the floors [W/m2]
L00199          real eppv                        !Electricity production of PV panels [W]
L00200          real sfr_indoor,sfpv,tpv_print
L00201  ! Local:
L00202  ! -----
L00203  	integer swwal                   !swich for the physical coefficients calculation
L00204  	integer ilev			!index for rooms	
L00205  	integer iwal			!index for walls
L00206  	integer iflo			!index for floors
L00207  	integer ivw			!index for vertical walls
L00208          integer igrd                    !index for ground
L00209          integer irof                    !index for roof 
L00210          real hseqocc(nzcanm)		!sensible heat generated by equipments and occupants [W]
L00211  	real hleqocc(nzcanm)		!latent heat generated by occupants [W]
L00212          real hscond(nzcanm)		!sensible heat generated by wall conduction [W]
L00213          real hslev(nzcanm)		!sensible heat flux generated inside the room [W]
L00214          real hllev(nzcanm)		!latent heat flux generatd inside the room [W]
L00215  	real surwal(6,nzcanm)	        !Surface of the walls [m2]
L00216  	real surwal1D(6)	        !wall surfaces of a generic room [m2]
L00217  	real rsint(6)		        !short wave radiation reaching the indoor walls[W/m2]
L00218  	real rswalins(6,nzcanm)	        !internal short wave radiation for the building [W/m2]
L00219  	real twin1D(4)		        !temperature of windows for a particular room [K]
L00220  	real twal_int(6)		!temperature of the first internal layers of a room [K]
L00221  	real rlint(6)		        !internal wall long wave radiation [w/m2]
L00222  	real rlwalins(6,nzcanm)	        !internal long wave radiation for the building [W/m2]	
L00223  	real hrwalout(4,nzcanm)	        !external radiative flux to the walls [W/m2]
L00224  	real hrwalins(6,nzcanm)	        !inside radiative flux to the walls [W/m2] 
L00225  	real hrwinout(4,nzcanm)	        !external radiative flux to the window [W/m2]
L00226  	real hrwinins(4,nzcanm)	        !inside radiative flux to the window [W/m2] 
L00227  	real hrrof			!external radiative flux to the roof [W/m2]
L00228  	real hs
L00229          real hsneed(nzcanm)		!sensible heat needed by the room [W]
L00230  	real hlneed(nzcanm)		!latent heat needed by the room [W]	
L00231          real hswalins(6,nzcanm)	        !inside walls sensible heat flux [W/m2]
L00232  	real hswalins1D(6)
L00233  	real hswinins(4,nzcanm)	        !inside window sensible heat flux [W/m2]
L00234  	real hswinins1D(4)	
L00235  	real htot(2)			!total heat flux at the wall [W/m2]
L00236  	real twal1D(nwal)
L00237  	real tflo1D(nflo)	
L00238          real tgrd1D(ngrd)
L00239          real trof1D(nrof)
L00240  	real rswal1D(4)
L00241  	real Qb				!Overall heat capacity of the indoor air [J/K]
L00242  	real vollev			!volume of the room [m3]
L00243  	real rhoint			!density of the internal air [Kg/m3]
L00244  	real cpint			!specific heat of the internal air [J/kg.K]
L00245          real humdry                     !specific humidiy of dry air [kg water/kg dry air]
L00246  	real radflux                    !Function to compute the total radiation budget
L00247  	real consumpbuild               !Energetic consumption for the entire building [KWh/s]
L00248          real hsoutbuild                 !Total sensible heat ejected into the atmosphere[W]
L00249                                          !by the air conditioning system and per building
L00250          real nhourday                   !number of hours from midnight, local time
L00251          real hfgrd                      !Dummy variable to assign hfgr=0 to walls, windows and ground
L00252  
L00253  !
L00254          parameter(hfgrd=0) 
L00255  !--------------------------------------------
L00256  !Initialization
L00257  !--------------------------------------------
L00258         do ilev=1,nzcanm
L00259            hseqocc(ilev)=0.
L00260            hleqocc(ilev)=0.
L00261            hscond(ilev)=0.
L00262            hslev(ilev)=0.
L00263            hllev(ilev)=0.
L00264         enddo	
L00265  
L00266  !Calculation of the surfaces of the building 
L00267  !--------------------------------------------
L00268  	
L00269         
L00270  	do ivw=1,6
L00271  	do ilev=1,nzcanm
L00272  	 surwal(ivw,ilev)=1.   !initialisation
L00273  	end do
L00274  	end do
L00275  
L00276  	do ilev=1,nlev
L00277  	  do ivw=1,2
L00278  	   surwal(ivw,ilev)=dzlev*bw
L00279  	  end do
L00280  	  do ivw=3,4
L00281  	   surwal(ivw,ilev)=dzlev*bl
L00282  	  end do
L00283  	  do ivw=5,6 		
L00284  	   surwal(ivw,ilev)=bw*bl
L00285  	  end do 
L00286  	end do
L00287  
L00288  
L00289  ! Calculation of the short wave radiations at the internal walls
L00290  ! ---------------------------------------------------------------
L00291  	
L00292  
L00293  	do ilev=1,nlev	
L00294  	  
L00295  	  do ivw=1,4
L00296  	    rswal1D(ivw)=rswal(ivw,ilev)
L00297  	  end do	
L00298  
L00299  	  do ivw=1,6
L00300  	    surwal1D(ivw)=surwal(ivw,ilev)
L00301  	  end do 		
L00302  	
L00303  	  call int_rsrad(albwin,albins,pwin,rswal1D,&
L00304                           surwal1D,bw,bl,dzlev,rsint)
L00305  
L00306  	  do ivw=1,6
L00307  	    rswalins(ivw,ilev)=rsint(ivw)
L00308  	  end do
L00309            
L00310  	end do !ilev
L00311  	
L00312  	 
L00313  
L00314  ! Calculation of the long wave radiation at the internal walls
L00315  !-------------------------------------------------------------
L00316  
L00317  
L00318  !Intermediate rooms
L00319         
L00320         if (nlev.gt.2) then
L00321  	do ilev=2,nlev-1
L00322  
L00323  	  do ivw=1,4
L00324  	    twin1D(ivw)=twin(ivw,ilev)
L00325  	    twal_int(ivw)=twal(ivw,1,ilev)
L00326  	  end do
L00327  	    
L00328  	   twal_int(5)=tflo(nflo,ilev-1)
L00329  	   twal_int(6)=tflo(1,ilev)		
L00330  		 
L00331  	   call int_rlrad(emins,emwin,sigma,twal_int,twin1D,&
L00332       			  pwin,bw,bl,dzlev,rlint)
L00333  	  
L00334  	  
L00335  	  do ivw=1,6
L00336  	    rlwalins(ivw,ilev)=rlint(ivw)
L00337  	  end do
L00338  	    
L00339  	end do	!ilev 
L00340        end if	 
L00341  	
L00342  
L00343        if (nlev.ne.1) then  
L00344  
L00345  !bottom room
L00346  
L00347  	  do ivw=1,4
L00348  	    twin1D(ivw)=twin(ivw,1)
L00349  	    twal_int(ivw)=twal(ivw,1,1)
L00350  	  end do
L00351  	  
L00352  	  twal_int(5)=tgrd(ngrd)
L00353  	  twal_int(6)=tflo(1,1)		
L00354  	  
L00355  	  						  	   
L00356  	   call int_rlrad(emins,emwin,sigma,twal_int,twin1D,&
L00357       			  pwin,bw,bl,dzlev,rlint)
L00358  	  
L00359  	  do ivw=1,6
L00360  	    rlwalins(ivw,1)=rlint(ivw)
L00361  	  end do	  
L00362              
L00363  !top room
L00364  	 
L00365  	  do ivw=1,4
L00366  	    twin1D(ivw)=twin(ivw,nlev)
L00367  	    twal_int(ivw)=twal(ivw,1,nlev)
L00368  	  end do
L00369  	  
L00370  	  twal_int(5)=tflo(nflo,nlev-1)
L00371  	  twal_int(6)=trof(1)		
L00372  	  
L00373  					
L00374  	   call int_rlrad(emins,emwin,sigma,twal_int,twin1D,&
L00375       			  pwin,bw,bl,dzlev,rlint)
L00376  	  
L00377  	  do ivw=1,6
L00378  	    rlwalins(ivw,nlev)=rlint(ivw)
L00379  	  end do
L00380  	  
L00381        else   !Top <---> Bottom
L00382  	  
L00383  	  do ivw=1,4
L00384  	    twin1D(ivw)=twin(ivw,1)
L00385  	    twal_int(ivw)=twal(ivw,1,1)
L00386  	  end do
L00387  	  
L00388  	  twal_int(5)=tgrd(ngrd)      
L00389        	  twal_int(6)=trof(1)
L00390  	  
L00391  	  call int_rlrad(emins,emwin,sigma,twal_int,twin1D, &
L00392       			 pwin,bw,bl,dzlev,rlint)
L00393       	  
L00394  	  do ivw=1,6
L00395  	    rlwalins(ivw,1)=rlint(ivw)
L00396  	  end do
L00397  	
L00398        end if  
L00399  	
L00400  
L00401  ! Calculation of the radiative fluxes
L00402  ! -----------------------------------
L00403  
L00404  !External vertical walls and windows
L00405  
L00406          do ilev=1,nlev
L00407  	 do ivw=1,4	 
L00408  	 call radfluxs(radflux,albwal,rswal(ivw,ilev),     &
L00409       	                    emwal,rlwal(ivw,ilev),sigma,   &
L00410                              twal(ivw,nwal,ilev))
L00411  	
L00412           hrwalout(ivw,ilev)=radflux
L00413        	 						
L00414  	 hrwinout(ivw,ilev)=emwin*rlwal(ivw,ilev)- &
L00415       	                    emwin*sigma*(twin(ivw,ilev)**4)
L00416  	 
L00417  	 
L00418  	 end do ! ivw
L00419  	end do  ! ilev
L00420  	
L00421  !Roof and PV panels
L00422          
L00423          if (pv_frac_roof.eq.0.) then
L00424             call radfluxs(radflux,albrof,rs,emrof,rl,sigma,tr_av)
L00425            hrrof=radflux
L00426            else
L00427              call radfluxspv(nzcanm,nlev,albrof,rs,swddif,emrof,rl,tr_av,tout,sigma,radflux,pv_frac_roof,tpv)
L00428              hrrof=radflux
L00429          endif
L00430  
L00431  !Internal walls for intermediate rooms
L00432  
L00433        if(nlev.gt.2) then
L00434         
L00435  	do ilev=2,nlev-1
L00436  	 do ivw=1,4
L00437           
L00438  	 call radfluxs(radflux,albins,rswalins(ivw,ilev),     &
L00439       	                    emins,rlwalins(ivw,ilev),sigma,   &
L00440                              twal(ivw,1,ilev))
L00441  	 
L00442  	 hrwalins(ivw,ilev)=radflux
L00443  
L00444  	 end do !ivw						
L00445  
L00446  	 call radfluxs(radflux,albins,rswalins(5,ilev), &
L00447       	                      emins,rlwalins(5,ilev),sigma,&
L00448                                tflo(nflo,ilev-1))
L00449  
L00450           hrwalins(5,ilev)=radflux
L00451  
L00452           call radfluxs(radflux,albins,rswalins(6,ilev), &
L00453                                emins,rlwalins(6,ilev),sigma,&
L00454                                tflo(1,ilev))
L00455           hrwalins(6,ilev)=radflux
L00456  
L00457         end do !ilev
L00458  
L00459        end if 	
L00460  
L00461  
L00462  !Internal walls for the bottom and the top room	 
L00463  !
L00464        if (nlev.ne.1) then 
L00465  
L00466  !bottom floor
L00467  
L00468  	 do ivw=1,4
L00469  
L00470  	    call radfluxs(radflux,albins,rswalins(ivw,1),  &
L00471       	                    emins,rlwalins(ivw,1),sigma,   &
L00472                              twal(ivw,1,1))
L00473  	
L00474              hrwalins(ivw,1)=radflux
L00475  
L00476  	 end do
L00477  	
L00478  	
L00479  	  call radfluxs(radflux,albins,rswalins(5,1),&
L00480                             emins,rlwalins(5,1),sigma,&    !bottom
L00481                             tgrd(ngrd))
L00482  
L00483            hrwalins(5,1)=radflux
L00484  
L00485  	   
L00486            call radfluxs(radflux,albins,rswalins(6,1),&
L00487       	                   emins,rlwalins(6,1),sigma,&
L00488                             tflo(1,1))  
L00489  	 
L00490            hrwalins(6,1)=radflux
L00491  
L00492  !roof floor
L00493  
L00494           do ivw=1,4
L00495     
L00496            call radfluxs(radflux,albins,rswalins(ivw,nlev),     &
L00497       	                        emins,rlwalins(ivw,nlev),sigma,&
L00498                                  twal(ivw,1,nlev))
L00499  
L00500  	  hrwalins(ivw,nlev)=radflux
L00501  
L00502  	 end do                                          !top
L00503  
L00504  	
L00505           call radfluxs(radflux,albins,rswalins(5,nlev),    &
L00506       	                      emins,rlwalins(5,nlev),sigma,&
L00507                                tflo(nflo,nlev-1))
L00508  
L00509           hrwalins(5,nlev)=radflux
L00510  
L00511  	 call radfluxs(radflux,albins,rswalins(6,nlev), &
L00512                                emins,rlwalins(6,nlev),sigma,&
L00513                                trof(1))
L00514  
L00515           hrwalins(6,nlev)=radflux
L00516        
L00517        else       ! Top <---> Bottom room
L00518        
L00519  	 do ivw=1,4
L00520  
L00521  	    call radfluxs(radflux,albins,rswalins(ivw,1),&
L00522       	                    emins,rlwalins(ivw,1),sigma, &
L00523                              twal(ivw,1,1))
L00524  
L00525              hrwalins(ivw,1)=radflux
L00526  
L00527           end do
L00528       
L00529       	    call radfluxs(radflux,albins,rswalins(5,1),&
L00530                             emins,rlwalins(5,1),sigma,  &
L00531                             tgrd(ngrd))
L00532  
L00533              hrwalins(5,1)=radflux
L00534       
L00535       	    call radfluxs(radflux,albins,rswalins(6,nlev),     &
L00536                                    emins,rlwalins(6,nlev),sigma,&
L00537                                    trof(1))
L00538              hrwalins(6,1)=radflux
L00539  
L00540        end if
L00541        
L00542  		
L00543  !Windows
L00544  
L00545  	 do ilev=1,nlev
L00546  	  do ivw=1,4
L00547  	     hrwinins(ivw,ilev)=emwin*rlwalins(ivw,ilev)-    &
L00548                                  emwin*sigma*(twin(ivw,ilev)**4)
L00549  	  end do
L00550  	 end do
L00551  	
L00552  		
L00553  ! Calculation of the sensible heat fluxes
L00554  ! ---------------------------------------
L00555  
L00556  !Vertical fluxes for walls
L00557  	
L00558  	do ilev=1,nlev
L00559           do ivw=1,4
L00560  		
L00561                 call hsinsflux (2,2,tlev(ilev),twal(ivw,1,ilev),hs)		
L00562  	       
L00563                 hswalins(ivw,ilev)=hs 
L00564           
L00565           end do ! ivw     
L00566          end do ! ilev
L00567         
L00568        
L00569  !Vertical fluxes for windows
L00570  
L00571  	do ilev=1,nlev
L00572                                                                                                                                                                            
L00573           do ivw=1,4
L00574  	 
L00575  	       call hsinsflux (2,1,tlev(ilev),twin(ivw,ilev),hs)
L00576  	       
L00577                 hswinins(ivw,ilev)=hs 
L00578  			
L00579           end do ! ivw	
L00580  	
L00581  	end do !ilev      
L00582  
L00583  !Horizontal fluxes
L00584         
L00585        if (nlev.gt.2) then
L00586         
L00587          do ilev=2,nlev-1
L00588                  
L00589  	       call hsinsflux (1,2,tlev(ilev),tflo(nflo,ilev-1),hs)
L00590  
L00591  	       hswalins(5,ilev)=hs
L00592              
L00593  	       call hsinsflux (1,2,tlev(ilev),tflo(1,ilev),hs)
L00594  
L00595  	       hswalins(6,ilev)=hs
L00596  
L00597          end do ! ilev
L00598         
L00599        end if
L00600         
L00601        if (nlev.ne.1) then
L00602         
L00603         	        call hsinsflux (1,2,tlev(1),tgrd(ngrd),hs)
L00604  
L00605  		hswalins(5,1)=hs				!Bottom room
L00606  		
L00607  		call hsinsflux (1,2,tlev(1),tflo(1,1),hs)
L00608  
L00609  		hswalins(6,1)=hs				
L00610  	 
L00611         	        call hsinsflux (1,2,tlev(nlev),tflo(nflo,nlev-1),hs)
L00612  
L00613  		hswalins(5,nlev)=hs			        !Top room
L00614  
L00615  		call hsinsflux (1,2,tlev(nlev),trof(1),hs)
L00616  
L00617  		hswalins(6,nlev)=hs	       
L00618                  sfr_indoor= hswalins(6,nlev) 
L00619        else  ! Bottom<--->Top 
L00620        
L00621                  call hsinsflux (1,2,tlev(1),tgrd(ngrd),hs)
L00622  		
L00623  		hswalins(5,1)=hs
L00624  		
L00625  		call hsinsflux (1,2,tlev(nlev),trof(1),hs)
L00626  		
L00627  		hswalins(6,nlev)=hs
L00628        
L00629        end if
L00630  !!
L00631  !! Calculation of the sensible heat fluxes from the PV panels & electricity producti
L00632  
L00633  
L00634        if(pv_frac_roof.gt.0)then
L00635        call hsfluxpv(nzcanm,nlev,bl,bw,albrof,rs,swddif,emrof,rl,tr_av,tout,sigma,hspv,eppv,pv_frac_roof,uout,vout,tpv,dt)
L00636        sfpv=hspv
L00637        tpv_print=tpv
L00638        endif       
L00639  
L00640  !Calculation of the temperature for the different surfaces 
L00641  ! --------------------------------------------------------
L00642  
L00643  ! Vertical walls	
L00644          
L00645         swwal=1
L00646         do ilev=1,nlev
L00647          do ivw=1,4  
L00648  
L00649  	   htot(1)=hswalins(ivw,ilev)+hrwalins(ivw,ilev)	
L00650             htot(2)=hswalout(ivw,ilev)+hrwalout(ivw,ilev)
L00651             gswal(ivw,ilev)=htot(2)
L00652  
L00653  	   do iwal=1,nwal
L00654  	      twal1D(iwal)=twal(ivw,iwal,ilev)
L00655  	   end do
L00656  	    
L00657  	   call wall(swwal,nwal,dt,dzwal,kwal,cswal,htot,twal1D)
L00658  	
L00659  	   do iwal=1,nwal
L00660  	      twal(ivw,iwal,ilev)=twal1D(iwal)
L00661  	   end do
L00662             
L00663  	end do ! ivw
L00664         end do ! ilev
L00665         
L00666  ! Windows
L00667  
L00668         do ilev=1,nlev
L00669          do ivw=1,4
L00670         
L00671           htot(1)=hswinins(ivw,ilev)+hrwinins(ivw,ilev)	
L00672           htot(2)=hswinout(ivw,ilev)+hrwinout(ivw,ilev)	
L00673  
L00674           twin(ivw,ilev)=twin(ivw,ilev)+(dt/(cswin*thickwin))* &
L00675                          (htot(1)+htot(2))
L00676  	
L00677  	end do ! ivw
L00678         end do ! ilev   
L00679  
L00680  ! Horizontal floors
L00681  
L00682  
L00683        if (nlev.gt.1) then
L00684         swwal=1
L00685         do ilev=1,nlev-1
L00686   
L00687            htot(1)=hrwalins(6,ilev)+hswalins(6,ilev)
L00688            htot(2)=hrwalins(5,ilev+1)+hswalins(5,ilev+1)	
L00689  
L00690  	  do iflo=1,nflo
L00691  	     tflo1D(iflo)=tflo(iflo,ilev)
L00692  	  end do
L00693          
L00694  	  call wall(swwal,nflo,dt,dzflo,kflo,csflo,htot,tflo1D)
L00695  	
L00696  	 do iflo=1,nflo
L00697  	    tflo(iflo,ilev)=tflo1D(iflo)
L00698  	 end do
L00699  
L00700         end do ! ilev
L00701        end if 
L00702          
L00703  
L00704  ! Ground 	
L00705          
L00706  	swwal=1
L00707  
L00708  	htot(1)=0.	!Diriclet b.c. at the internal boundary    
L00709  	htot(2)=hswalins(5,1)+hrwalins(5,1)   
L00710     
L00711          do igrd=1,ngrd
L00712             tgrd1D(igrd)=tgrd(igrd)
L00713          end do
L00714  
L00715           call wall(swwal,ngrd,dt,dzgrd,kgrd,csgrd,htot,tgrd1D)
L00716  
L00717          do igrd=1,ngrd
L00718             tgrd(igrd)=tgrd1D(igrd)
L00719          end do
L00720  
L00721          
L00722  ! Roof
L00723          
L00724        swwal=1    
L00725  
L00726        htot(1)=hswalins(6,nlev)+hrwalins(6,nlev)     	
L00727        htot(2)=hsrof+hrrof+lsrof 
L00728        gsrof=htot(2)
L00729  
L00730        do irof=1,nrof
L00731           trof1D(irof)=trof(irof)
L00732          
L00733        end do  
L00734  
L00735        if(gr_flag.eq.1)then
L00736        call wall_gr(hfgr,gr_frac_roof,swwal,nrof,dt,dzrof,krof,csrof,htot,trof1D)
L00737        else
L00738         call wall(swwal,nrof,dt,dzrof,krof,csrof,htot,trof1D)
L00739        endif
L00740        do irof=1,nrof
L00741           trof(irof)=trof1D(irof)
L00742  
L00743         end do
L00744        
L00745  
L00746  ! Calculation of the heat fluxes and of the temperature of the rooms
L00747  ! ------------------------------------------------------------------
L00748  
L00749   	do ilev=1,nlev
L00750  	  	  
L00751  	 !Calculation of the heat generated by equipments and occupants
L00752  	 
L00753  	 call fluxeqocc(nhourday,bw,bl,perflo,hsesf,hsequip,hseqocc(ilev),hleqocc(ilev))
L00754  
L00755       	 !Calculation of the heat generated by natural ventilation
L00756  	
L00757  	  vollev=bw*bl*dzlev
L00758            humdry=shumlev(ilev)/(1.-shumlev(ilev))
L00759  	  rhoint=(press(ilev))/(rair*(1.+0.61*humdry)*tlev(ilev))
L00760  	  cpint=cp*(1.+0.84*humdry)
L00761            
L00762   	  
L00763  	  call fluxvent(cpint,rhoint,vollev,tlev(ilev),tout(ilev),     &
L00764                          latent,humout(ilev),rhoout(ilev),shumlev(ilev),&
L00765                          beta,hsvent(ilev),hlvent(ilev))
L00766    
L00767  	      
L00768           !Calculation of the heat generated by conduction
L00769  	  
L00770  	   do iwal=1,6
L00771  	     hswalins1D(iwal)=hswalins(iwal,ilev)
L00772  	     surwal1D(iwal)=surwal(iwal,ilev)
L00773  	  end do
L00774  	  
L00775  	   do iwal=1,4
L00776  	     hswinins1D(iwal)=hswinins(iwal,ilev)
L00777  	   end do
L00778  	
L00779  	  call fluxcond(hswalins1D,hswinins1D,surwal1D,pwin,&
L00780                          hscond(ilev))
L00781  
L00782  	!Calculation of the heat generated inside the room
L00783   	
L00784  	  call fluxroo(hseqocc(ilev),hleqocc(ilev),hsvent(ilev), &
L00785                 hlvent(ilev),hscond(ilev),hslev(ilev),hllev(ilev))
L00786  
L00787  	  
L00788  	!Evolution of the temperature and of the specific humidity 
L00789  
L00790  	  Qb=rhoint*cpint*vollev
L00791  
L00792          ! temperature regulation
L00793  
L00794            call regtemp(sw_cond,nhourday,dt,Qb,hslev(ilev),       &
L00795                         tlev(ilev),timeon,timeoff,targtemp,gaptemp,hsneed(ilev))
L00796  
L00797          ! humidity regulation 
L00798  
L00799  	  call reghum(sw_cond,nhourday,dt,vollev,rhoint,latent, &
L00800                        hllev(ilev),shumlev(ilev),timeon,timeoff,&
L00801                        targhum,gaphum,hlneed(ilev))
L00802  !
L00803  !performance of the air conditioning system for the test
L00804  !	
L00805  	        
L00806            call air_cond(hsneed(ilev),hlneed(ilev),dt, &
L00807                          hsout(ilev),hlout(ilev),consump(ilev), cop)
L00808      	         	
L00809   	  tlev(ilev)=tlev(ilev)+(dt/Qb)*(hslev(ilev)-hsneed(ilev))
L00810            	  	  
L00811  	  shumlev(ilev)=shumlev(ilev)+(dt/(vollev*rhoint*latent))* &
L00812                          (hllev(ilev)-hlneed(ilev))
L00813             
L00814  	end do !ilev
L00815          
L00816          call consump_total(nzcanm,nlev,consumpbuild,hsoutbuild, &
L00817                             hsout,consump)
L00818                  
L00819        return
L00820        end subroutine BEM
```

> 讲解：八步流水线（每房间循环外只做一次的段 + 每房间一段的段）：①**表面积矩阵** surwal(6,ilev)——六面几何；②**室内短波** int_rsrad：窗外辐射透射 transmit=1−albwin 按 pwin 加权进室内，各向同性撒到六面，再解 6×6 多次反射系统（algebra_short）；③**室内长波** int_rlrad：六面 T⁴ 发射+反射 6×6 系统（algebra_long）；底房间面 5 换成楼下地基、顶房间面 6 换成屋顶——室内辐射「看得见」建筑外几何；④**外表面辐射收支** radfluxs（=(1−alb)rs+em·rl−em·σT⁴），屋顶有 PV 时改用 radfluxspv（PV 面板与屋顶间的辐射交换 hrad 串联式）；⑤**室内对流** hsinsflux：Clarke 建筑热工手册系数（竖墙 5.678·1.09、窗 5.678·0.99 W/(m²·K)，光滑/粗糙面区分）；⑥**围护结构导热** wall/wall_gr：墙、楼板、楼下地基、屋顶四类多层材料各自隐式三对角推进（上边界=内外两侧热流和 htot，热流进 temp 的边界行；swwal 开关使 wall_coeff 系数只算一次——save 缓存，材料性质不随时间变）；窗户按 dt/(cswin·thickwin) 集总热容更新；绿屋顶时屋顶用 wall_gr（第 5 层注入 hfgr 绿屋顶耦合热流并按 gr_frac_roof 缩放——与 14a roof_temp_veg 的 hfgr 对接）；⑦**房间空气收支**：fluxeqocc（人员 160 W/人显热 + 1.96e6/86400 W/人潜热 ×perflo×rocc + 设备 hsequip 24h 谱×hsesf）→ fluxvent（自然通风：每小时一次全换气 vollev/3600，换热器效率 beta 打折）→ fluxcond（六面对流进风的合计，符号翻转对齐 Twall−Tindoor）→ fluxroo 求和 → **regtemp/reghum 恒温恒湿调节**（开关 sw_cond、时间窗 timeon/off、目标值±死区 gaptemp/gaphum、越界后算 hsneed 并用 temp_rat/hum_rat 限速）→ **air_cond**（COP 换算：制冷时废热 hsout=(1+1/cop)·|hsneed|+…——注意注释里备选式被注释掉的历史；制热时 hsout=0）→ 室内状态显式推进 tlev+=(dt/Qb)(hslev−hsneed)、shumlev+=(dt/(vol·ρ·L))(hllev−hlneed)；⑧consump_total 全楼汇总（耗电 kW·h/s）。**Qb=ρ_int·cp_int·vol 是室内空气总热容——「室内空气」是零惯量近似之外的唯一惯性，房间响应快于此即失真。**

## 五、PV 单元

<!-- code_extract code_extract.py v1.2
source: phys/module_sf_bem.F
ranges: L823-L905
file_lines: 2636
file_md5: e93033f4eff5816a89e6cf51c65d738a
display: line-numbered (strip L-prefix and !file: line to restore)
range_md5: 2553d4d2e7e1269248a3b641e56d8453
seg_lines: 83
label: subroutine hsfluxpv
-->

```fortran
!file: phys/module_sf_bem.F    L823-L905    (subroutine hsfluxpv)
L00823        subroutine hsfluxpv(nz,n,bl,bw,albr,rs,swddif,emr,rl,tr,tair,sigma,hspv,eppv,pv_frac_roof,uout,vout,tpv,dt)
L00824  !
L00825        implicit none
L00826  !
L00827  ! Input variables
L00828  !
L00829        integer,intent(in) :: nz     !Maximum number of vertical levels in the urban grid
L00830        real,intent(in) :: bl		!Building length [m]
L00831        real,intent(in) :: bw            !Building width [m]
L00832        real,intent(in) :: albr	!albedo of the roof (ext.) 
L00833        real,intent(in) :: emr   !emissivity of the roof (ext.)
L00834        real,intent(in) :: rs    !external short wave radiation [W/m2]
L00835        real,intent(in) :: rl	!external long wave radiation [W/m2]
L00836        real,intent(in) :: tr	!roof surface temperature [K]
L00837        real,intent(in) :: pv_frac_roof ! fraction of PV  []
L00838        real,intent(in) :: sigma !Stefan-Boltzmann constant [W/m2.K4] 
L00839        real,intent(in),dimension(1:nz) :: tair  !external temperature [K] 
L00840        integer,intent(in) :: n  !number of floors in the building
L00841        real,intent(in), dimension(1:nz) :: uout		
L00842        real,intent(in), dimension(1:nz) :: vout
L00843        real,intent(in)  :: dt
L00844        real,intent(in)  :: swddif
L00845  ! Output variables
L00846  !
L00847        real,intent(inout) :: hspv ! Sensible heat flux from the PV panels to the atmosphere [W/m2]
L00848        real,intent(inout) :: eppv ! Electricity production from PV panels [W]
L00849        real,intent(inout) :: tpv       !Temperature of the PV panels [K]
L00850  !
L00851  ! Local variables
L00852  !
L00853        real,parameter :: albpv=0.11 ! albedo of the PV panels
L00854        real,parameter :: empv_down=0.95  ! emissivity of the PV panels
L00855        real,parameter :: empv_up=0.79
L00856        real, parameter :: T_amb=25
L00857        real, parameter :: tiltangle=0.
L00858        real, parameter :: a=3.8
L00859        real, parameter :: b=6.9
L00860  
L00861        real, parameter :: r1=2330.
L00862        real, parameter :: r2=1200.
L00863        real, parameter :: r3=3000.
L00864        real, parameter :: c1=677.
L00865        real, parameter :: c2=1250.
L00866        real, parameter :: c3=500.
L00867        real, parameter :: d1=0.0003
L00868        real, parameter :: d2=0.0005
L00869        real, parameter :: d3=0.003
L00870        real, parameter :: F12=1.
L00871        real :: lwuppv     !Long-wave emitted by the PV panels to the sky [W/m2]
L00872        real :: lwdwr      !Long-wave incoming radiation on the roof [W/m2]
L00873        real :: lwupr      !Long-wave coming up from the roof intercepted by the PV panels [W/m2] 
L00874        real :: enerpv     !Energy produced by PV panels [W/m2]
L00875        real :: hc
L00876        real :: sw_d
L00877        real :: lw_d
L00878        real :: lwpv_out
L00879        real :: tpv_new
L00880        real :: hdown
L00881        real :: hup
L00882        real :: deltat
L00883        real :: uroof
L00884        real :: hrad
L00885        real :: Cm      
L00886        real :: hf
L00887         Cm=r1*c1*d1+r2*c2*d2+r3*c3*d3
L00888         hrad=sigma/((1-empv_down)/empv_down+1/F12+(1-emr)/emr)
L00889         uroof=(uout(n+1)**2+vout(n+1)**2)**0.5
L00890        deltat=tpv-tair(n+1)
L00891      hf=2.5*(40./100.*uroof)**(0.5)
L00892      hc=9.482*abs(deltat)**(1./3.)/(7.238-abs(cos(tiltangle)))
L00893      hup=sqrt(hc**2.+(hf)**2.)
L00894      hc=1.810*abs(deltat)**(1./3.)/(1.382+abs(cos(tiltangle)))
L00895      hdown=sqrt(hc**2.+(hf)**2.)
L00896      enerpv=effpv*rs*min(1.,1.-0.005*(tpv-(T_amb+273.15)))
L00897      sw_d=(1-albpv)*(rs)
L00898      lw_d=empv_up*rl
L00899      lwpv_out=empv_up*sigma*tpv**4.
L00900      lwupr=hrad*(tr**4-tpv**4.)
L00901      hspv=(hup+hdown)*(tpv-tair(n+1))
L00902      tpv=tpv+(sw_d+lw_d-lwpv_out+lwupr-hspv-enerpv)/Cm*dt
L00903      eppv=enerpv*pv_frac_roof*bl*bw
L00904       return
L00905        end subroutine hsfluxpv 
```

> 讲解：屋顶光伏板能量平衡：三层材料集热容 Cm（r/c/d 三组参数=背板/电池/玻璃）；对空对流 hf=2.5·(0.4·V)^0.5 与自然对流 hc 分上下两面（倾角 0 的平板公式）；与屋顶的辐射交换 hrad=σ/((1−ε_pv)/ε_pv+1/F12+(1−ε_r)/ε_r)（两面灰体+视角因子的串联发射率）；发电 enerpv=effpv·rs·min(1, 1−0.005·(T_pv−298.15))——**温度每升 1℃ 效率降 0.5%**；板温显式推进。eppv=enerpv·pv_frac_roof·bl·bw。albpv=0.11/empv_up=0.79/empv_down=0.95 与 14b upward_rad 的常数对齐（两处必须一致）。

## 六、导热求解器族

<!-- code_extract code_extract.py v1.2
source: phys/module_sf_bem.F
ranges: L909-L1033
file_lines: 2636
file_md5: e93033f4eff5816a89e6cf51c65d738a
display: line-numbered (strip L-prefix and !file: line to restore)
range_md5: e3cbe9547daceddfd100b89ce61d20de
seg_lines: 125
label: subroutine wall_gr
-->

```fortran
!file: phys/module_sf_bem.F    L909-L1033    (subroutine wall_gr)
L00909  	subroutine wall_gr(hfgr,gr_frac_roof,swwall,nz,dt,dz,k,cs,flux,temp)
L00910  	
L00911  !______________________________________________________________________
L00912  
L00913  !The aim of this subroutine is to solve the 1D heat fiffusion equation
L00914  !for roof, walls and streets:
L00915  !
L00916  !	dT/dt=d/dz[K*dT/dz] where:
L00917  !
L00918  !	-T is the surface temperature(wall, street, roof)
L00919  !      	-Kz is the heat diffusivity inside the material.
L00920  !
L00921  !The resolution is done implicitly with a FV discretisation along the
L00922  !different layers of the material:
L00923  
L00924  !	____________________________
L00925  !     n             *
L00926  !                   *
L00927  !                   *
L00928  !     	____________________________
L00929  !    i+2
L00930  !              	    I+1                 
L00931  !	____________________________        
L00932  !    i+1        
L00933  !                    I                ==>   [T(I,n+1)-T(I,n)]/DT= 
L00934  !	____________________________        [F(i+1)-F(i)]/DZI
L00935  !    i
L00936  !                   I-1               ==> A*T(n+1)=B where:
L00937  !	____________________________         
L00938  !   i-1              *                   * A is a TRIDIAGONAL matrix.
L00939  !                    *                   * B=T(n)+S takes into account the sources.
L00940  !                    *
L00941  !     1	____________________________
L00942  
L00943  !________________________________________________________________
L00944  
L00945  	implicit none
L00946  		
L00947  !Input:
L00948  !-----
L00949              real hfgr        !Green roof heat flux
L00950              real gr_frac_roof     !Green roof fraction
L00951  
L00952  	integer nz		!Number of layers inside the material
L00953  	real dt			!Time step
L00954  	real dz(nz)		!Layer sizes [m]
L00955  	real cs(nz)		!Specific heat of the material [J/(m3.K)] 
L00956  	real k(nz+1)		!Thermal conductivity in each layers (face) [W/(m.K)]
L00957  	real flux(2)		!Internal and external flux terms.
L00958          
L00959  
L00960  !Input-Output:
L00961  !-------------
L00962  
L00963  	integer swwall          !swich for the physical coefficients calculation
L00964  	real temp(nz)		!Temperature at each layer
L00965  
L00966  !Local:
L00967  !-----	
L00968  
L00969        real a(-1:1,nz)          !  a(-1,*) lower diagonal      A(i,i-1)
L00970                                 !  a(0,*)  principal diagonal  A(i,i)
L00971                                 !  a(1,*)  upper diagonal      A(i,i+1).
L00972        
L00973        real b(nz)	       !Coefficients of the second term.	
L00974        real k1(20)
L00975        real k2(20)
L00976        real kc(20)
L00977        save k1,k2,kc
L00978        integer iz
L00979          	
L00980  !________________________________________________________________
L00981  !
L00982  !Calculation of the coefficients
L00983  	
L00984  	if (swwall.eq.1) then
L00985  	
L00986             if (nz.gt.20) then
L00987                write(*,*) 'number of layers in the walls/roofs too big ',nz
L00988                write(*,*) 'please decrease under of',20
L00989                stop
L00990             endif
L00991  
L00992  	   call wall_coeff(nz,dt,dz,cs,k,k1,k2,kc)
L00993  	   swwall=0
L00994  
L00995  	end if
L00996   	
L00997  !Computation of the first value (iz=1) of A and B:
L00998  	
L00999  		 a(-1,1)=0.
L01000  		 a(0,1)=1+k2(1)
L01001  		 a(1,1)=-k2(1)
L01002                   b(1)=temp(1)+flux(1)*kc(1)
L01003  
L01004  	do iz=2,nz-1
L01005                  a(-1,iz)=-k1(iz)
L01006                  if(iz.eq.5)then
L01007                  a(-1,iz)=-k1(iz)
L01008                  a(0,iz)=1+k1(iz)+(1-gr_frac_roof)*k2(iz)
L01009                  b(iz)=temp(iz)+(gr_frac_roof*hfgr*dt)/dz(iz)
L01010                  a(1,iz)=-k2(iz)*(1-gr_frac_roof)
L01011                  else
L01012                  a(0,iz)=1.+k1(iz)+k2(iz)
L01013                  b(iz)=temp(iz)
L01014                  a(1,iz)=-k2(iz)
L01015                  endif
L01016  
L01017                  
L01018  	end do		
L01019  
L01020  !Computation of the external value (iz=n) of A and B:
L01021  	
L01022  		a(-1,nz)=-k1(nz)
L01023  		a(0,nz)=1.+k1(nz)
L01024  		a(1,nz)=0.
L01025                  b(nz)=temp(nz)+kc(nz)*flux(2)
L01026                   
L01027  !Resolution of the system A*T(n+1)=B
L01028  
L01029  	call tridia(nz,a,b,temp)
L01030  	
L01031  
L01032          return
L01033  	end  subroutine wall_gr	
```

<!-- code_extract code_extract.py v1.2
source: phys/module_sf_bem.F
ranges: L1039-L1151
file_lines: 2636
file_md5: e93033f4eff5816a89e6cf51c65d738a
display: line-numbered (strip L-prefix and !file: line to restore)
range_md5: fa0e2e7064c2df4f3163ca89eb4a9497
seg_lines: 113
label: subroutine wall
-->

```fortran
!file: phys/module_sf_bem.F    L1039-L1151    (subroutine wall)
L01039  	subroutine wall(swwall,nz,dt,dz,k,cs,flux,temp)
L01040  	
L01041  !______________________________________________________________________
L01042  
L01043  !The aim of this subroutine is to solve the 1D heat fiffusion equation
L01044  !for roof, walls and streets:
L01045  !
L01046  !	dT/dt=d/dz[K*dT/dz] where:
L01047  !
L01048  !	-T is the surface temperature(wall, street, roof)
L01049  !      	-Kz is the heat diffusivity inside the material.
L01050  !
L01051  !The resolution is done implicitly with a FV discretisation along the
L01052  !different layers of the material:
L01053  
L01054  !	____________________________
L01055  !     n             *
L01056  !                   *
L01057  !                   *
L01058  !     	____________________________
L01059  !    i+2
L01060  !              	    I+1                 
L01061  !	____________________________        
L01062  !    i+1        
L01063  !                    I                ==>   [T(I,n+1)-T(I,n)]/DT= 
L01064  !	____________________________        [F(i+1)-F(i)]/DZI
L01065  !    i
L01066  !                   I-1               ==> A*T(n+1)=B where:
L01067  !	____________________________         
L01068  !   i-1              *                   * A is a TRIDIAGONAL matrix.
L01069  !                    *                   * B=T(n)+S takes into account the sources.
L01070  !                    *
L01071  !     1	____________________________
L01072  
L01073  !________________________________________________________________
L01074  
L01075  	implicit none
L01076  		
L01077  !Input:
L01078  !-----
L01079   	integer nz		!Number of layers inside the material
L01080  	real dt			!Time step
L01081  	real dz(nz)		!Layer sizes [m]
L01082  	real cs(nz)		!Specific heat of the material [J/(m3.K)] 
L01083  	real k(nz+1)		!Thermal conductivity in each layers (face) [W/(m.K)]
L01084  	real flux(2)		!Internal and external flux terms.
L01085          
L01086  
L01087  !Input-Output:
L01088  !-------------
L01089  
L01090  	integer swwall          !swich for the physical coefficients calculation
L01091  	real temp(nz)		!Temperature at each layer
L01092  
L01093  !Local:
L01094  !-----	
L01095  
L01096        real a(-1:1,nz)          !  a(-1,*) lower diagonal      A(i,i-1)
L01097                                 !  a(0,*)  principal diagonal  A(i,i)
L01098                                 !  a(1,*)  upper diagonal      A(i,i+1).
L01099        
L01100        real b(nz)	       !Coefficients of the second term.	
L01101        real k1(20)
L01102        real k2(20)
L01103        real kc(20)
L01104        save k1,k2,kc
L01105        integer iz
L01106          	
L01107  !________________________________________________________________
L01108  !
L01109  !Calculation of the coefficients
L01110  	
L01111  	if (swwall.eq.1) then
L01112  	
L01113             if (nz.gt.20) then
L01114                write(*,*) 'number of layers in the walls/roofs too big ',nz
L01115                write(*,*) 'please decrease under of',20
L01116                stop
L01117             endif
L01118  
L01119  	   call wall_coeff(nz,dt,dz,cs,k,k1,k2,kc)
L01120  	   swwall=0
L01121  
L01122  	end if
L01123   	
L01124  !Computation of the first value (iz=1) of A and B:
L01125  	
L01126  		 a(-1,1)=0.
L01127  		 a(0,1)=1+k2(1)
L01128  		 a(1,1)=-k2(1)
L01129                     b(1)=temp(1)+flux(1)*kc(1)
L01130  
L01131  	do iz=2,nz-1
L01132                  a(-1,iz)=-k1(iz)
L01133                  a(0,iz)=1+k1(iz)+k2(iz)
L01134                  b(iz)=temp(iz)
L01135                  a(1,iz)=-k2(iz)
L01136  	end do		
L01137  
L01138  !Computation of the external value (iz=n) of A and B:
L01139  	
L01140  		a(-1,nz)=-k1(nz)
L01141  		a(0,nz)=1+k1(nz)
L01142  		a(1,nz)=0.
L01143  		b(nz)=temp(nz)+flux(2)*kc(nz)
L01144                       
L01145  !Resolution of the system A*T(n+1)=B
L01146  
L01147  	call tridia(nz,a,b,temp)
L01148  	
L01149  
L01150          return
L01151  	end  subroutine wall	
```

<!-- code_extract code_extract.py v1.2
source: phys/module_sf_bem.F
ranges: L1156-L1206
file_lines: 2636
file_md5: e93033f4eff5816a89e6cf51c65d738a
display: line-numbered (strip L-prefix and !file: line to restore)
range_md5: 8241706ace9f307ebff1230567a2e46e
seg_lines: 51
label: subroutine wall_coeff
-->

```fortran
!file: phys/module_sf_bem.F    L1156-L1206    (subroutine wall_coeff)
L01156  	subroutine wall_coeff(nz,dt,dz,cs,k,k1,k2,kc)
L01157  
L01158  	implicit none
L01159  	
L01160  !---------------------------------------------------------------------
L01161  !Input
L01162  !-----
L01163  	integer nz		!Number of layers inside the material
L01164  	real dt			!Time step
L01165  	real dz(nz)		!Layer sizes [m]
L01166  	real cs(nz)		!Specific heat of the material [J/(m3.K)] 
L01167  	real k(nz+1)		!Thermal diffusivity in each layers (face) [W/(m.K)]
L01168  
L01169  
L01170  !Input-Output
L01171  !------------
L01172  
L01173  	real flux(2)		!Internal and external flux terms.
L01174  
L01175  
L01176  !Output
L01177  !------
L01178          real k1(20)
L01179          real k2(20)
L01180          real kc(20)
L01181  
L01182  !Local
L01183  !-----	
L01184  	integer iz
L01185  	real kf(nz)
L01186  
L01187  !------------------------------------------------------------------
L01188  
L01189  	do iz=2,nz
L01190  	 kc(iz)=dt/(dz(iz)*cs(iz))
L01191  	 kf(iz)=2*k(iz)/(dz(iz)+dz(iz-1))
L01192  	end do 
L01193  	
L01194  	kc(1)=dt/(dz(1)*cs(1))
L01195          kf(1)=2*k(1)/(dz(1))
L01196  
L01197  	do iz=1,nz
L01198  	 k1(iz)=kc(iz)*kf(iz)
L01199  	end do
L01200  	
L01201  	do iz=1,nz-1
L01202  	 k2(iz)=kc(iz)*kf(iz+1)*cs(iz)/cs(iz+1)
L01203  	end do
L01204  
L01205  	return
L01206  	end subroutine wall_coeff
```

> 讲解：同一套隐式有限体积导热（dT/dt=d/dz(K·dT/dz)）的两个变体 + 系数预计算：wall_coeff 把 dt/(dz·cs) 与层间调和导热 2k/(dz_iz+dz_iz−1) 预乘成 k1/k2/kc（**swwal 开关+save 缓存只算一次**——若论文 2 把材料参数场化，此缓存必须作废或改为逐点缓存，这是标量→场改造的第一个性能陷阱）；wall 是标准版（内边界 flux(1)、外边界 flux(2) 的 Neumann 条件，底层行 b(nz)=temp+kc·flux(2)）；wall_gr 在第 5 层注入绿屋顶耦合热流 hfgr·gr_frac_roof·dt/dz 并把该层向外系数乘 (1−gr_frac_roof)。nz≤20 硬上限。

<!-- code_extract code_extract.py v1.2
source: phys/module_sf_bem.F
ranges: L2366-L2410
file_lines: 2636
file_md5: e93033f4eff5816a89e6cf51c65d738a
display: line-numbered (strip L-prefix and !file: line to restore)
range_md5: e9258353cbfedd0b2344ca8aeccba3d4
seg_lines: 45
label: subroutine tridia
-->

```fortran
!file: phys/module_sf_bem.F    L2366-L2410    (subroutine tridia)
L02366          subroutine tridia(n,a,b,x)
L02367  
L02368  !     ++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++
L02369  !     +    by A. Clappier,     EPFL, CH 1015 Lausanne                  +
L02370  !     +                        phone: ++41-(0)21-693-61-60             +
L02371  !     +                        email:alain.clappier@epfl.ch            +
L02372  !     ++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++
L02373  
L02374  ! ----------------------------------------------------------------------
L02375  !        Resolution of a * x = b    where a is a tridiagonal matrix
L02376  !
L02377  ! ----------------------------------------------------------------------
L02378  
L02379          implicit none
L02380  
L02381  ! Input
L02382          integer n
L02383          real a(-1:1,n)           !  a(-1,*) lower diagonal      A(i,i-1)
L02384                                 !  a(0,*)  principal diagonal  A(i,i)
L02385                                 !  a(1,*)  upper diagonal      A(i,i+1)
L02386          real b(n)
L02387  
L02388  ! Output
L02389          real x(n)
L02390  
L02391  ! Local
L02392          integer i
L02393  
L02394  ! ----------------------------------------------------------------------
L02395  
L02396          do i=n-1,1,-1
L02397             b(i)=b(i)-a(1,i)*b(i+1)/a(0,i+1)
L02398             a(0,i)=a(0,i)-a(1,i)*a(-1,i+1)/a(0,i+1)
L02399          enddo
L02400  
L02401          do i=2,n
L02402             b(i)=b(i)-a(-1,i)*b(i-1)/a(0,i-1)
L02403          enddo
L02404  
L02405          do i=1,n
L02406             x(i)=b(i)/a(0,i)
L02407          enddo
L02408  
L02409          return
L02410          end subroutine tridia    
```

<!-- code_extract code_extract.py v1.2
source: phys/module_sf_bem.F
ranges: L2414-L2516
file_lines: 2636
file_md5: e93033f4eff5816a89e6cf51c65d738a
display: line-numbered (strip L-prefix and !file: line to restore)
range_md5: 89f8d722f453eafd385b6e33d79014fe
seg_lines: 103
label: subroutine gaussjbem
-->

```fortran
!file: phys/module_sf_bem.F    L2414-L2516    (subroutine gaussjbem)
L02414         subroutine gaussjbem(a,n,b,np)
L02415  
L02416  ! ----------------------------------------------------------------------
L02417  ! This routine solve a linear system of n equations of the form
L02418  !              A X = B
L02419  !  where  A is a matrix a(i,j)
L02420  !         B a vector and X the solution
L02421  ! In output b is replaced by the solution     
L02422  ! ----------------------------------------------------------------------
L02423  
L02424         implicit none
L02425  
L02426  ! ----------------------------------------------------------------------
L02427  ! INPUT:
L02428  ! ----------------------------------------------------------------------
L02429         integer np
L02430         real a(np,np)
L02431  
L02432  ! ----------------------------------------------------------------------
L02433  ! OUTPUT:
L02434  ! ----------------------------------------------------------------------
L02435         real b(np)
L02436  
L02437  ! ----------------------------------------------------------------------
L02438  ! LOCAL:
L02439  ! ----------------------------------------------------------------------
L02440        integer nmax
L02441        parameter (nmax=150)
L02442  
L02443        real big,dum
L02444        integer i,icol,irow
L02445        integer j,k,l,ll,n
L02446        integer ipiv(nmax)
L02447        real pivinv
L02448  
L02449  ! ----------------------------------------------------------------------
L02450  ! END VARIABLES DEFINITIONS
L02451  ! ----------------------------------------------------------------------
L02452         
L02453         do j=1,n
L02454            ipiv(j)=0.
L02455         enddo
L02456         
L02457        do i=1,n
L02458           big=0.
L02459           do j=1,n
L02460              if(ipiv(j).ne.1)then
L02461                 do k=1,n
L02462                    if(ipiv(k).eq.0)then
L02463                       if(abs(a(j,k)).ge.big)then
L02464                          big=abs(a(j,k))
L02465                          irow=j
L02466                          icol=k
L02467                       endif
L02468                    elseif(ipiv(k).gt.1)then
L02469                       FATAL_ERROR('singular matrix in gaussjbem')
L02470                    endif
L02471                 enddo
L02472              endif
L02473           enddo
L02474           
L02475           ipiv(icol)=ipiv(icol)+1
L02476           
L02477           if(irow.ne.icol)then
L02478              do l=1,n
L02479                 dum=a(irow,l)
L02480                 a(irow,l)=a(icol,l)
L02481                 a(icol,l)=dum
L02482              enddo
L02483              
L02484              dum=b(irow)
L02485              b(irow)=b(icol)
L02486              b(icol)=dum
L02487            
L02488           endif
L02489           
L02490           if(a(icol,icol).eq.0) FATAL_ERROR('singular matrix in gaussjbem')
L02491           
L02492           pivinv=1./a(icol,icol)
L02493           a(icol,icol)=1
L02494           
L02495           do l=1,n
L02496              a(icol,l)=a(icol,l)*pivinv
L02497           enddo
L02498           
L02499           b(icol)=b(icol)*pivinv
L02500           
L02501           do ll=1,n
L02502              if(ll.ne.icol)then
L02503                 dum=a(ll,icol)
L02504                 a(ll,icol)=0.
L02505                 do l=1,n
L02506                    a(ll,l)=a(ll,l)-a(icol,l)*dum
L02507                 enddo
L02508                 
L02509                 b(ll)=b(ll)-b(icol)*dum
L02510                 
L02511              endif
L02512           enddo
L02513        enddo
L02514        
L02515        return
L02516        end subroutine gaussjbem
```

> 讲解：tridia=A. Clappier 的三对角解器（a(−1:1,n) 存储风格，与 14b invert 同族但签名不同）；gaussjbem=Numerical Recipes gaussj 的 6×6 室内版（解 int_rsrad/int_rlrad 两次反射系统）。

## 七、室内辐射与对流

<!-- code_extract code_extract.py v1.2
source: phys/module_sf_bem.F
ranges: L1261-L1324
file_lines: 2636
file_md5: e93033f4eff5816a89e6cf51c65d738a
display: line-numbered (strip L-prefix and !file: line to restore)
range_md5: e961a27d9ee1a4083acdc7bbaf790853
seg_lines: 64
label: subroutine int_rsrad
-->

```fortran
!file: phys/module_sf_bem.F    L1261-L1324    (subroutine int_rsrad)
L01261  	subroutine int_rsrad(albwin,albwal,pwin,rswal,&
L01262                               surwal,bw,bl,zw,rsint)
L01263  	
L01264  ! ------------------------------------------------------------------
L01265  	implicit none
L01266  ! ------------------------------------------------------------------	
L01267  
L01268  !Input
L01269  !-----
L01270  	real albwin		!albedo of the windows
L01271  	real albwal		!albedo of the internal wall					
L01272  	real rswal(4)		!incoming short wave radiation [W/m2]
L01273              real surwal(6) 		!surface of the indoor walls [m2]
L01274  	real bw,bl		!width of the walls [m]
L01275  	real zw			!height of the wall [m]
L01276  	real pwin               !window proportion
L01277  	
L01278  !Output
L01279  !------
L01280  	real rsint(6)		!internal walls short wave radiation [W/m2]
L01281  
L01282  !Local
L01283  !-----
L01284  	real transmit   !transmittance of the direct/diffused radiation
L01285              real rstr	!solar radiation transmitted through the windows	
L01286              real surtotwal  !total indoor surface of the walls in the room
L01287  	integer iw
L01288  	real b(6)	!second member for the system
L01289  	real a(6,6)	!matrix for the system
L01290  
L01291  !-------------------------------------------------------------------
L01292  
L01293  
L01294  ! Calculation of the solar radiation transmitted through windows
L01295                      
L01296              rstr = 0.
L01297              do iw=1,4
L01298                 transmit=1.-albwin
L01299                 rstr = rstr+(surwal(iw)*pwin)*(transmit*rswal(iw))
L01300              enddo
L01301  
L01302  !We suppose that the radiation is spread isotropically within the
L01303  !room when it passes through the windows, so the flux [W/m2] in every 
L01304  !wall is:
L01305  
L01306              surtotwal=0.
L01307              do iw=1,6
L01308                 surtotwal=surtotwal+surwal(iw)
L01309              enddo
L01310              
L01311              rstr=rstr/surtotwal
L01312   		
L01313  !Computation of the short wave radiation reaching the internal walls
L01314  	
L01315  	    call algebra_short(rstr,albwal,albwin,bw,bl,zw,pwin,a,b)
L01316  		
L01317  	    call gaussjbem(a,6,b,6)
L01318  	
L01319              do iw=1,6
L01320                 rsint(iw)=b(iw)
L01321              enddo
L01322  
L01323  	    return
L01324  	    end subroutine int_rsrad
```

<!-- code_extract code_extract.py v1.2
source: phys/module_sf_bem.F
ranges: L1329-L1374
file_lines: 2636
file_md5: e93033f4eff5816a89e6cf51c65d738a
display: line-numbered (strip L-prefix and !file: line to restore)
range_md5: 2945bad281c1967e81146a8a1c835136
seg_lines: 46
label: subroutine int_rlrad
-->

```fortran
!file: phys/module_sf_bem.F    L1329-L1374    (subroutine int_rlrad)
L01329  	subroutine int_rlrad(emwal,emwin,sigma,twal_int,twin,&
L01330       			     pwin,bw,bl,zw,rlint)
L01331  	
L01332  ! ------------------------------------------------------------------
L01333  	implicit none
L01334  ! ------------------------------------------------------------------	
L01335  
L01336  !Input
L01337  !-----
L01338  
L01339  	real emwal	!emissivity of the internal walls
L01340  	real emwin	!emissivity of the window
L01341  	real sigma	!Stefan-Boltzmann constant [W/m2.K4]
L01342  	real twal_int(6)!temperature of the first internal layers of a room [K]
L01343  	real twin(4)	!temperature of the windows [K]
L01344  	real bw		!width of the wall
L01345  	real bl		!length of the wall
L01346  	real zw		!height of the wall
L01347  	real pwin       !window proportion	
L01348  
L01349  !Output
L01350  !------
L01351  
L01352  	real rlint(6)	!internal walls long wave radiation [W/m2]
L01353  
L01354  !Local
L01355  !------
L01356  	
L01357  	real b(6)	!second member vector for the system
L01358  	real a(6,6)	!matrix for the system
L01359          integer iw
L01360  !----------------------------------------------------------------
L01361  
L01362  !Compute the long wave radiation reachs the internal walls
L01363  
L01364  	call algebra_long(emwal,emwin,sigma,twal_int,twin,pwin,&
L01365                            bw,bl,zw,a,b)
L01366    			  
L01367  	call gaussjbem(a,6,b,6)
L01368  
L01369          do iw=1,6
L01370             rlint(iw)=b(iw)
L01371          enddo
L01372              
L01373  	return
L01374  	end subroutine int_rlrad	
```

<!-- code_extract code_extract.py v1.2
source: phys/module_sf_bem.F
ranges: L1379-L1517
file_lines: 2636
file_md5: e93033f4eff5816a89e6cf51c65d738a
display: line-numbered (strip L-prefix and !file: line to restore)
range_md5: 0a1f519e29b28687846313309e4cef81
seg_lines: 139
label: subroutine algebra_short
-->

```fortran
!file: phys/module_sf_bem.F    L1379-L1517    (subroutine algebra_short)
L01379  	subroutine algebra_short(rstr,albwal,albwin,aw,bw,zw,pwin,a,b)
L01380      
L01381  !--------------------------------------------------------------------
L01382  !This routine calculates the algebraic system that will be solved for 
L01383  !the computation of the total shortwave radiation that reachs every 
L01384  !indoor wall in a floor.
L01385  !Write the matrix system ax=b to solve
L01386  !
L01387  !     -Rs(1)+a(1,2)Rs(2)+.................+a(1,6)Rs(6)=-Rs=b(1)
L01388  !a(2,1)Rs(1)-      Rs(2)+.................+a(2,6)Rs(6)=-Rs=b(2)
L01389  !a(3,1)Rs(1)+a(3,2)Rs(3)-Rs(3)+...........+a(3,6)Rs(6)=-Rs=b(3)
L01390  !a(4,1)Rs(1)+.................-Rs(4)+.....+a(4,6)Rs(6)=-Rs=b(4)
L01391  !a(5,1)Rs(1)+.......................-Rs(5)+a(5,6)Rs(6)=-Rs=b(5)
L01392  !a(6,1)Rs(1)+....................................-R(6)=-Rs=b(6)
L01393  !
L01394  !This version suppose the albedo of the indoor walls is the same.
L01395  !--------------------------------------------------------------------
L01396  	implicit none
L01397  !--------------------------------------------------------------------
L01398  
L01399  !Input
L01400  !-----
L01401  	real rstr	!solar radiation transmitted through the windows		
L01402  	real albwal	!albedo of the internal walls
L01403  	real albwin	!albedo of the windows.
L01404  	real bw		!length of the wall
L01405  	real aw		!width of the wall
L01406  	real zw		!height of the wall
L01407  	real fprl_int	!view factor
L01408  	real fnrm_int	!view factor
L01409  	real pwin       !window proportion
L01410  !Output
L01411  !------
L01412  	real a(6,6)		!Matrix for the system
L01413  	real b(6)		!Second member for the system
L01414  !Local
L01415  !-----
L01416  	integer iw,jw	
L01417  	real albm               !averaged albedo
L01418  !----------------------------------------------------------------
L01419  
L01420  !Initialise the variables
L01421  
L01422  	do iw=1,6
L01423             b(iw)= 0.
L01424  	  do jw=1,6
L01425             a(iw,jw)= 0. 
L01426            enddo
L01427          enddo 
L01428  
L01429  !Calculation of the second member b
L01430  
L01431  	do iw=1,6
L01432  	 b(iw)=-rstr
L01433  	end do	
L01434  
L01435  !Calculation of the averaged albedo
L01436  
L01437  	albm=pwin*albwin+(1-pwin)*albwal
L01438  	
L01439  !Calculation of the matrix a
L01440  
L01441              a(1,1)=-1.
L01442  
L01443              call fprl_ints(fprl_int,aw/bw,zw/bw)
L01444  
L01445              a(1,2)=albm*fprl_int
L01446  
L01447              call fnrm_ints(fnrm_int,aw/zw,bw/zw,(aw*aw+bw*bw)/(zw*zw))
L01448  
L01449              a(1,3)=albm*(bw/aw)*fnrm_int
L01450  
L01451              a(1,4)=a(1,3)
L01452  
L01453              call fnrm_ints(fnrm_int,zw/aw,bw/aw,(bw*bw+zw*zw)/(aw*aw))
L01454  
L01455              a(1,5)=albwal*(bw/zw)*fnrm_int
L01456  
L01457              a(1,6)=a(1,5)
L01458  
L01459  
L01460              a(2,1)=a(1,2)
L01461              a(2,2)=-1.
L01462              a(2,3)=a(1,3)
L01463              a(2,4)=a(1,4)
L01464              a(2,5)=a(1,5)
L01465              a(2,6)=a(1,6)
L01466   
L01467  	
L01468              call fnrm_ints(fnrm_int,bw/zw,aw/zw,(bw*bw+aw*aw)/(zw*zw))
L01469  
L01470              a(3,1)=albm*(aw/bw)*fnrm_int
L01471  	    a(3,2)=a(3,1)
L01472  	    a(3,3)=-1.
L01473  
L01474              call fprl_ints(fprl_int,zw/aw,bw/aw)
L01475  
L01476  	    a(3,4)=albm*fprl_int
L01477  
L01478              call fnrm_ints(fnrm_int,zw/bw,aw/bw,(aw*aw+zw*zw)/(bw*bw))
L01479  
L01480  	    a(3,5)=albwal*(aw/zw)*fnrm_int
L01481              a(3,6)=a(3,5)
L01482  	
L01483  
L01484              a(4,1)=a(3,1)
L01485              a(4,2)=a(3,2)
L01486              a(4,3)=a(3,4)
L01487              a(4,4)=-1.
L01488              a(4,5)=a(3,5)
L01489              a(4,6)=a(3,6)
L01490  
L01491              call fnrm_ints(fnrm_int,bw/aw,zw/aw,(bw*bw+zw*zw)/(aw*aw)) 
L01492  
L01493              a(5,1)=albm*(zw/bw)*fnrm_int
L01494                     
L01495              a(5,2)=a(5,1)
L01496  
L01497              call fnrm_ints(fnrm_int,aw/bw,zw/bw,(aw*aw+zw*zw)/(bw*bw))
L01498  
L01499              a(5,3)=albm*(zw/aw)*fnrm_int
L01500             	   
L01501              a(5,4)=a(5,3)
L01502              a(5,5)=-1.
L01503  
L01504              call fprl_ints(fprl_int,aw/zw,bw/zw)
L01505  
L01506              a(5,6)=albwal*fprl_int
L01507  
L01508  
L01509              a(6,1)=a(5,1)
L01510              a(6,2)=a(5,2)
L01511              a(6,3)=a(5,3)
L01512              a(6,4)=a(5,4)
L01513              a(6,5)=a(5,6)
L01514              a(6,6)=-1.
L01515  	
L01516  	return
L01517  	end subroutine algebra_short
```

<!-- code_extract code_extract.py v1.2
source: phys/module_sf_bem.F
ranges: L1522-L1823
file_lines: 2636
file_md5: e93033f4eff5816a89e6cf51c65d738a
display: line-numbered (strip L-prefix and !file: line to restore)
range_md5: a4f249f0ad90a4bae7fd7010bf878475
seg_lines: 302
label: subroutine algebra_long
-->

```fortran
!file: phys/module_sf_bem.F    L1522-L1823    (subroutine algebra_long)
L01522  	subroutine algebra_long(emwal,emwin,sigma,twalint,twinint,&
L01523       				pwin,aw,bw,zw,a,b)
L01524  
L01525  !--------------------------------------------------------------------
L01526  !This routine computes the algebraic system that will be solved to 
L01527  !compute the longwave radiation that reachs the indoor
L01528  !walls in a floor. 
L01529  !Write the matrix system ax=b to solve
L01530  !
L01531  !a(1,1)Rl(1)+.............................+Rl(6)=b(1)
L01532  !a(2,1)Rl(1)+.................+Rl(5)+a(2,6)Rl(6)=b(2)
L01533  !a(3,1)Rl(1)+.....+Rl(3)+...........+a(3,6)Rl(6)=b(3)
L01534  !a(4,1)Rl(1)+...........+Rl(4)+.....+a(4,6)Rl(6)=b(4)
L01535  !      Rl(1)+.......................+a(5,6)Rl(6)=b(5)
L01536  !a(6,1)Rl(1)+Rl(2)+.................+a(6,6)Rl(6)=b(6)
L01537  !
L01538  !--------------------------------------------------------------------
L01539          implicit none 
L01540  	
L01541  !--------------------------------------------------------------------
L01542  
L01543  !Input
L01544  !-----
L01545  
L01546  	real pwin       !window proportion 
L01547  	real emwal	!emissivity of the internal walls
L01548  	real emwin	!emissivity of the window
L01549  	real sigma	!Stefan-Boltzmann constant [W/m2.K4]
L01550  	real twalint(6) !temperature of the first internal layers of a room [K]
L01551  	real twinint(4)	!temperature of the windows [K]
L01552  	real aw		!width of the wall
L01553  	real bw		!length of the wall
L01554  	real zw		!height of the wall
L01555  	real fprl_int	!view factor
L01556  	real fnrm_int	!view factor	
L01557             real fnrm_intx	!view factor
L01558             real fnrm_inty	!view factor
L01559  
L01560  !Output
L01561  !------
L01562  	real b(6)	!second member vector for the system
L01563  	real a(6,6)	!matrix for the system
L01564  !Local
L01565  !-----
L01566  	integer iw,jw
L01567  	real b_wall(6)	
L01568  	real b_wind(6)
L01569  	real emwal_av		!averadge emissivity of the wall
L01570  	real emwin_av		!averadge emissivity of the window
L01571          real em_av		!averadge emissivity
L01572          real twal_int(6)        !twalint 
L01573  	real twin(4)   		!twinint 
L01574  !------------------------------------------------------------------
L01575  
L01576  !Initialise the variables
L01577  !-------------------------
L01578  
L01579  	 do iw=1,6
L01580              b(iw)= 0.
L01581              b_wall(iw)=0.
L01582              b_wind(iw)=0.
L01583            do jw=1,6
L01584              a(iw,jw)= 0. 
L01585            enddo
L01586           enddo
L01587  
L01588           do iw=1,6
L01589              twal_int(iw)=twalint(iw)
L01590           enddo
L01591  
L01592           do iw=1,4
L01593              twin(iw)=twinint(iw)
L01594           enddo
L01595  	 
L01596  !Calculation of the averadge emissivities
L01597  !-----------------------------------------
L01598  
L01599  	emwal_av=(1-pwin)*emwal
L01600  	emwin_av=pwin*emwin
L01601  	em_av=emwal_av+emwin_av
L01602  	
L01603  !Calculation of the second term for the walls
L01604  !-------------------------------------------
L01605  
L01606              call fprl_ints(fprl_int,aw/zw,bw/zw)
L01607              call fnrm_ints(fnrm_intx,aw/bw,zw/bw,(aw*aw+zw*zw)/(bw*bw))
L01608              call fnrm_ints(fnrm_inty,bw/aw,zw/aw,(bw*bw+zw*zw)/(aw*aw))
L01609  
L01610              b_wall(1)=(emwal*sigma*(twal_int(5)**4)*           &
L01611       	         fprl_int)+                                    &
L01612                   (sigma*(emwal_av*(twal_int(3)**4)+            &
L01613                    emwal_av*(twal_int(4)**4))*                  &
L01614                   (zw/aw)*fnrm_intx)+                           &
L01615                   (sigma*(emwal_av*(twal_int(1)**4)+            &
L01616                    emwal_av*(twal_int(2)**4))*                  & 
L01617                   (zw/bw)*fnrm_inty)
L01618  
L01619              call fprl_ints(fprl_int,aw/zw,bw/zw)
L01620              call fnrm_ints(fnrm_intx,aw/bw,zw/bw,(aw*aw+zw*zw)/(bw*bw))
L01621              call fnrm_ints(fnrm_inty,bw/aw,zw/aw,(bw*bw+zw*zw)/(aw*aw))
L01622  	
L01623              b_wall(2)=(emwal*sigma*(twal_int(6)**4)*           &
L01624                	   fprl_int)+                                  &
L01625                    (sigma*(emwal_av*(twal_int(3)**4)+           &
L01626                    emwal_av*(twal_int(4)**4))*                  & 
L01627                   (zw/aw)*fnrm_intx)+                           &
L01628                   (sigma*(emwal_av*(twal_int(1)**4)+            &
L01629                   emwal_av*(twal_int(2)**4))*                   &
L01630                   (zw/bw)*fnrm_inty)
L01631  
L01632              call fprl_ints(fprl_int,zw/aw,bw/aw)
L01633              call fnrm_ints(fnrm_intx,bw/zw,aw/zw,(bw*bw+aw*aw)/(zw*zw))
L01634              call fnrm_ints(fnrm_inty,zw/bw,aw/bw,(aw*aw+zw*zw)/(bw*bw))
L01635  
L01636              b_wall(3)=(emwal_av*sigma*(twal_int(4)**4)*        &
L01637          	  fprl_int)+                                   &
L01638                   (sigma*(emwal_av*(twal_int(2)**4)+            &
L01639                    emwal_av*(twal_int(1)**4))*                  &
L01640                   (aw/bw)*fnrm_intx)+                           &
L01641                   (sigma*(emwal*(twal_int(5)**4)+               &
L01642                    emwal*(twal_int(6)**4))*                     &
L01643                   (aw/zw)*fnrm_inty)
L01644  
L01645              call fprl_ints(fprl_int,zw/aw,bw/aw)
L01646              call fnrm_ints(fnrm_intx,bw/zw,aw/zw,(bw*bw+aw*aw)/(zw*zw))
L01647              call fnrm_ints(fnrm_inty,zw/bw,aw/bw,(aw*aw+zw*zw)/(bw*bw))
L01648  
L01649              b_wall(4)=(emwal_av*sigma*(twal_int(3)**4)*        &
L01650       	          fprl_int)+                                   &
L01651                   (sigma*(emwal_av*(twal_int(2)**4)+            &
L01652                    emwal_av*(twal_int(1)**4))*                  &
L01653                   (aw/bw)*fnrm_intx)+                           &
L01654                   (sigma*(emwal*(twal_int(5)**4)+               &
L01655                    emwal*(twal_int(6)**4))*                     &
L01656                   (aw/zw)*fnrm_inty)
L01657  
L01658              call fprl_ints(fprl_int,aw/bw,zw/bw)
L01659              call fnrm_ints(fnrm_intx,aw/zw,bw/zw,(aw*aw+bw*bw)/(zw*zw))
L01660              call fnrm_ints(fnrm_inty,zw/aw,bw/aw,(bw*bw+zw*zw)/(aw*aw))
L01661            
L01662              b_wall(5)=(emwal_av*sigma*(twal_int(2)**4)*        &
L01663       	          fprl_int)+                                   &
L01664                   (sigma*(emwal_av*(twal_int(3)**4)+            &
L01665                    emwal_av*(twal_int(4)**4))*                  &
L01666                   (bw/aw)*fnrm_intx)+                           &
L01667                   (sigma*(emwal*(twal_int(5)**4)+               &
L01668                    emwal*(twal_int(6)**4))*                     &
L01669                   (bw/zw)*fnrm_inty)
L01670  
L01671              call fprl_ints(fprl_int,aw/bw,zw/bw)
L01672              call fnrm_ints(fnrm_intx,aw/zw,bw/zw,(aw*aw+bw*bw)/(zw*zw))
L01673              call fnrm_ints(fnrm_inty,zw/aw,bw/aw,(bw*bw+zw*zw)/(aw*aw))
L01674  
L01675              b_wall(6)=(emwal_av*sigma*(twal_int(1)**4)*        &
L01676       	         fprl_int)+                                    &
L01677                   (sigma*(emwal_av*(twal_int(3)**4)+            &
L01678                    emwal_av*(twal_int(4)**4))*                  &
L01679                   (bw/aw)*fnrm_intx)+                           &
L01680                   (sigma*(emwal*(twal_int(5)**4)+               &
L01681                   emwal*(twal_int(6)**4))*                      &
L01682                   (bw/zw)*fnrm_inty)
L01683  	
L01684  !Calculation of the second term for the windows
L01685  !---------------------------------------------
L01686              call fnrm_ints(fnrm_intx,aw/bw,zw/bw,(aw*aw+zw*zw)/(bw*bw))
L01687              call fnrm_ints(fnrm_inty,bw/aw,zw/aw,(bw*bw+zw*zw)/(aw*aw))
L01688  
L01689              b_wind(1)=(sigma*(emwin_av*(twin(3)**4)+          &
L01690                    emwin_av*(twin(4)**4))*                     &
L01691                   (zw/aw)*fnrm_intx)+                          &
L01692                   (sigma*(emwin_av*(twin(1)**4)+               &
L01693                    emwin_av*(twin(2)**4))*                     &
L01694                   (zw/bw)*fnrm_inty)
L01695  
L01696              call fnrm_ints(fnrm_intx,aw/bw,zw/bw,(aw*aw+zw*zw)/(bw*bw))
L01697              call fnrm_ints(fnrm_inty,bw/aw,zw/aw,(bw*bw+zw*zw)/(aw*aw))
L01698  
L01699              b_wind(2)=(sigma*(emwin_av*(twin(3)**4)+          &
L01700                    emwin_av*(twin(4)**4))*                     &
L01701                   (zw/aw)*fnrm_intx)+                          &
L01702                   (sigma*(emwin_av*(twin(1)**4)+               &
L01703                    emwin_av*(twin(2)**4))*                     &
L01704                   (zw/bw)*fnrm_inty)
L01705  
L01706              call fprl_ints(fprl_int,zw/aw,bw/aw)
L01707              call fnrm_ints(fnrm_int,bw/zw,aw/zw,(bw*bw+aw*aw)/(zw*zw))
L01708            
L01709              b_wind(3)=emwin_av*sigma*(twin(4)**4)*            &
L01710                   fprl_int+(sigma*(emwin_av*                   &
L01711                   (twin(2)**4)+emwin_av*(twin(1)**4))*         &
L01712                   (aw/bw)*fnrm_int)
L01713  
L01714              call fprl_ints(fprl_int,zw/aw,bw/aw)
L01715              call fnrm_ints(fnrm_int,bw/zw,aw/zw,(bw*bw+aw*aw)/(zw*zw))
L01716  
L01717              b_wind(4)=emwin_av*sigma*(twin(3)**4)*            &
L01718                   fprl_int+(sigma*(emwin_av*                   &
L01719                    (twin(2)**4)+emwin_av*(twin(1)**4))*        &
L01720                   (aw/bw)*fnrm_int)
L01721  
L01722              call fprl_ints(fprl_int,aw/bw,zw/bw)
L01723              call fnrm_ints(fnrm_int,aw/zw,bw/zw,(aw*aw+bw*bw)/(zw*zw))
L01724            
L01725              b_wind(5)=emwin_av*sigma*(twin(2)**4)*            &
L01726                   fprl_int+(sigma*(emwin_av*                   &
L01727                   (twin(3)**4)+emwin_av*(twin(4)**4))*         &
L01728                   (bw/aw)*fnrm_int)
L01729   
L01730              call fprl_ints(fprl_int,aw/bw,zw/bw)
L01731              call fnrm_ints(fnrm_int,aw/zw,bw/zw,(aw*aw+bw*bw)/(zw*zw))
L01732  
L01733              b_wind(6)=emwin_av*sigma*(twin(1)**4)*            &
L01734                   fprl_int+(sigma*(emwin_av*                   &
L01735                   (twin(3)**4)+emwin_av*(twin(4)**4))*         &
L01736                   (bw/aw)*fnrm_int)
L01737       
L01738  !Calculation of the total b term
L01739  !-------------------------------
L01740  
L01741  	do iw=1,6
L01742  	 b(iw)=b_wall(iw)+b_wind(iw)
L01743  	end do     
L01744  
L01745  
L01746  !Calculation of the matrix of the system
L01747  !----------------------------------------
L01748  
L01749           call fnrm_ints(fnrm_int,bw/aw,zw/aw,(bw*bw+zw*zw)/(aw*aw))         
L01750  
L01751           a(1,1)=(em_av-1.)*(zw/bw)*fnrm_int
L01752       	        
L01753           a(1,2)=a(1,1)
L01754  
L01755           call fnrm_ints(fnrm_int,aw/bw,zw/bw,(aw*aw+zw*zw)/(bw*bw))
L01756  
L01757           a(1,3)=(em_av-1.)*(zw/aw)*fnrm_int
L01758           	 
L01759           a(1,4)=a(1,3)
L01760  
L01761           call fprl_ints(fprl_int,aw/zw,bw/zw)
L01762  
L01763           a(1,5)=(emwal-1.)*fprl_int
L01764           a(1,6)=1.
L01765  
L01766           a(2,1)=a(1,1)
L01767           a(2,2)=a(1,2)
L01768           a(2,3)=a(1,3)
L01769           a(2,4)=a(1,4)
L01770           a(2,5)=1.
L01771           a(2,6)=a(1,5)
L01772  
L01773           call fnrm_ints(fnrm_int,bw/zw,aw/zw,(bw*bw+aw*aw)/(zw*zw))
L01774  
L01775           a(3,1)=(em_av-1.)*(aw/bw)*fnrm_int
L01776       	        
L01777           a(3,2)=a(3,1)
L01778           a(3,3)=1.
L01779  
L01780           call fprl_ints(fprl_int,zw/aw,bw/aw) 
L01781  
L01782           a(3,4)=(em_av-1.)*fprl_int
L01783  
L01784           call fnrm_ints(fnrm_int,zw/bw,aw/bw,(aw*aw+zw*zw)/(bw*bw))
L01785  
L01786           a(3,5)=(emwal-1.)*(aw/zw)*fnrm_int
L01787       	        
L01788           a(3,6)=a(3,5)
L01789  
L01790           a(4,1)=a(3,1)
L01791           a(4,2)=a(3,2)
L01792           a(4,3)=a(3,4)
L01793           a(4,4)=1.
L01794           a(4,5)=a(3,5)
L01795           a(4,6)=a(3,6)
L01796  
L01797           a(5,1)=1.
L01798  
L01799           call fprl_ints(fprl_int,aw/bw,zw/bw)
L01800  
L01801           a(5,2)=(em_av-1.)*fprl_int
L01802  
L01803           call fnrm_ints(fnrm_int,aw/zw,bw/zw,(aw*aw+bw*bw)/(zw*zw))
L01804  
L01805           a(5,3)=(em_av-1.)*(bw/aw)*fnrm_int
L01806       	        
L01807           a(5,4)=a(5,3)
L01808  
L01809           call fnrm_ints(fnrm_int,zw/aw,bw/aw,(bw*bw+zw*zw)/(aw*aw))
L01810  
L01811           a(5,5)=(emwal-1.)*(bw/zw)*fnrm_int
L01812       	        
L01813           a(5,6)=a(5,5)
L01814  
L01815           a(6,1)=a(5,2)
L01816           a(6,2)=1.
L01817           a(6,3)=a(5,3)
L01818           a(6,4)=a(5,4)
L01819           a(6,5)=a(5,5)
L01820           a(6,6)=a(6,5)
L01821  
L01822        return
L01823        end subroutine algebra_long
```

> 讲解：房间内两次反射的 6×6 线性系统：algebra_short 组装 A 矩阵（对角 −1、非对角=视角因子×反照率，窗户面用混合反照率 albm=pwin·albwin+(1−pwin)·albwal），b=−rstr（透射进室内的短波各向同性撒入）；algebra_long 同构但源项是 em·σT⁴（六面第一层温度 twal_int：1..4 面取墙内层、5/6 面取楼板顶/底或地基/屋顶）。视角因子用 fprl_ints/fnrm_ints 的解析矩形公式（房间内两面平行/正交）。**论文 2 视角：这套 6×6 系统对「逐格异质建筑」依然成立——它只依赖每栋楼自己的几何（bw/bl/dzlev/pwin），参数场化不破坏数学结构。**

<!-- code_extract code_extract.py v1.2
source: phys/module_sf_bem.F
ranges: L1210-L1257
file_lines: 2636
file_md5: e93033f4eff5816a89e6cf51c65d738a
display: line-numbered (strip L-prefix and !file: line to restore)
range_md5: 8d5faba7ca08d628a6a88f808cf3dd4b
seg_lines: 48
label: subroutine hsinsflux
-->

```fortran
!file: phys/module_sf_bem.F    L1210-L1257    (subroutine hsinsflux)
L01210  	subroutine hsinsflux(swsurf,swwin,tin,tw,hsins)	
L01211  	
L01212  	implicit none
L01213  	
L01214  ! --------------------------------------------------------------------
L01215  ! This routine computes the internal sensible heat flux.
L01216  ! The swsurf, makes rhe difference between a vertical and a 
L01217  ! horizontal surface. 
L01218  ! The values of the heat conduction coefficients hc are obtained from the book
L01219  ! "Energy Simulation in Building Design". J.A. Clarke. 
L01220  ! Adam Hilger, Bristol, 362 pp.
L01221  ! --------------------------------------------------------------------
L01222  !Input
L01223  !----
L01224  	integer swsurf  !swich for the type of surface (horizontal/vertical) 
L01225              integer swwin   !swich for the type of surface (window/wall)
L01226  	real tin	!Inside temperature [K]
L01227  	real tw		!Internal wall temperature [K]  	
L01228  
L01229  
L01230  !Output
L01231  !------
L01232  	real hsins	!internal sensible heat flux [W/m2]
L01233  !Local
L01234  !-----
L01235  	real hc		!heat conduction coefficient [W/\B0C.m2]
L01236  !--------------------------------------------------------------------
L01237  
L01238  	if (swsurf.eq.2) then	!vertical surface
L01239           if (swwin.eq.1) then
L01240              hc=5.678*0.99        !window surface (smooth surface)
L01241           else
L01242              hc=5.678*1.09        !wall surface (rough surface)
L01243           endif
L01244  	 hsins=hc*(tin-tw)	
L01245  	endif
L01246  	
L01247  	if (swsurf.eq.1)  then   !horizontal surface
L01248           if (swwin.eq.1) then
L01249             hc=5.678*0.99        !window surface (smooth surface)
L01250           else
L01251             hc=5.678*1.09        !wall surface (rough surface)
L01252           endif
L01253           hsins=hc*(tin-tw)
L01254          endif 		
L01255  
L01256  	return
L01257  	end subroutine hsinsflux
```

> 讲解：室内对流系数（Clarke 教材值）：竖墙/水平面、粗糙/光滑两组，swsurf/swwin 两开关目前只区分竖墙 vs 窗（水平分支与竖墙同系数——天花板/地板对流按竖墙处理的简化）。

<!-- code_extract code_extract.py v1.2
source: phys/module_sf_bem.F
ranges: L2521-L2540
file_lines: 2636
file_md5: e93033f4eff5816a89e6cf51c65d738a
display: line-numbered (strip L-prefix and !file: line to restore)
range_md5: 65add106f3d921c16a21fb6c87dbb0da
seg_lines: 20
label: subroutine radfluxs
-->

```fortran
!file: phys/module_sf_bem.F    L2521-L2540    (subroutine radfluxs)
L02521        subroutine radfluxs(radflux,alb,rs,em,rl,sigma,twal)
L02522  
L02523        implicit none
L02524  !-------------------------------------------------------------------
L02525  !This function calculates the radiative fluxe at a surface
L02526  !-------------------------------------------------------------------
L02527  
L02528  	
L02529  	real alb	!albedo of the surface
L02530  	real rs		!shor wave radiation
L02531  	real em		!emissivity of the surface
L02532  	real rl 	!lon wave radiation
L02533  	real sigma	!parameter (wall is not black body) [W/m2.K4]
L02534  	real twal	!wall temperature [K]
L02535  	real radflux
L02536  	
L02537  	 radflux=(1.-alb)*rs+em*rl-em*sigma*twal**4
L02538  	
L02539        return
L02540        end subroutine radfluxs
```

<!-- code_extract code_extract.py v1.2
source: phys/module_sf_bem.F
ranges: L2543-L2586
file_lines: 2636
file_md5: e93033f4eff5816a89e6cf51c65d738a
display: line-numbered (strip L-prefix and !file: line to restore)
range_md5: 4ab80e1678f6801ba7ed6606732b1600
seg_lines: 44
label: subroutine radfluxspv
-->

```fortran
!file: phys/module_sf_bem.F    L2543-L2586    (subroutine radfluxspv)
L02543        subroutine radfluxspv(nz,n,alb,rs,swddif,em,rl,twal,tair,sigma,radflux,pv_frac_roof,tpv)
L02544  !
L02545        implicit none
L02546  !
L02547  ! This routine calculates the radiative fluxes at the surfaces
L02548  !
L02549  !     Integer and real kinds
L02550  !
L02551  !     integer, parameter :: kind_im = selected_int_kind(6)   ! 4 byte integer
L02552  !     integer, parameter :: kind_rb = selected_real_kind(12) ! 8 byte real 
L02553  !
L02554  ! Input Variables
L02555  !	
L02556        integer,intent(in) :: nz !Maximum number of vertical levels in the urban grid
L02557        real,intent(in) :: alb	!albedo of the surface
L02558        real,intent(in) :: rs	!shortwave radiation [W m-2]
L02559        real,intent(in) :: swddif
L02560        real,intent(in) :: em	!emissivity of the surface
L02561        real,intent(in) :: rl 	!longwave radiation [W m-2]
L02562        real,intent(in) :: twal	!surface temperature [K]
L02563        real,intent(in) :: sigma !Stefan-Boltzmann constant [W/m2.K4]
L02564        real,intent(in) :: tpv !Stefan-Boltzmann constant [W/m2.K4]
L02565        real,intent(in),dimension(1:nz) :: tair  !external temperature [K] 
L02566        integer,intent(in) :: n  !number of floors in the building
L02567        real, intent(in) :: pv_frac_roof !
L02568        real :: empv
L02569        real :: hrad
L02570        real :: F12
L02571  ! Output variables
L02572  !
L02573        real,intent(inout) :: radflux !radiative flux at the surface [W m-2]
L02574  !     
L02575  ! Local variables
L02576        F12=1. 
L02577        empv=0.95	
L02578        hrad=sigma/((1-empv)/empv+1/F12+(1-em)/em)
L02579        if ((n+1).gt.nz) then
L02580           write(*,*) 'Increase maximum number of vertical levels in the urban grid'
L02581           stop
L02582        endif
L02583        radflux=(1.-alb)*(1.-pv_frac_roof)*rs+em*(1.-pv_frac_roof)*rl+pv_frac_roof*hrad*(tpv**4-twal**4)- &
L02584                 em*sigma*(1.-pv_frac_roof)*twal**4
L02585        return
L02586        end subroutine radfluxspv
```

<!-- code_extract code_extract.py v1.2
source: phys/module_sf_bem.F
ranges: L2594-L2608
file_lines: 2636
file_md5: e93033f4eff5816a89e6cf51c65d738a
display: line-numbered (strip L-prefix and !file: line to restore)
range_md5: eb037cd3842a4613bb348532c62f8714
seg_lines: 15
label: subroutine fprl_ints
-->

```fortran
!file: phys/module_sf_bem.F    L2594-L2608    (subroutine fprl_ints)
L02594          subroutine fprl_ints(fprl_int,vx,vy)
L02595          
L02596          implicit none
L02597  
L02598  	real vx,vy
L02599  	real fprl_int
L02600          
L02601  	fprl_int=(2./(3.141592653*vx*vy))*                       &
L02602               (log(sqrt((1.+vx*vx)*(1.+vy*vy)/(1.+vx*vx+vy*vy)))+ &
L02603                (vy*sqrt(1.+vx*vx)*atan(vy/sqrt(1.+vx*vx)))+       &
L02604                (vx*sqrt(1.+vy*vy)*atan(vx/sqrt(1.+vy*vy)))-       &
L02605                vy*atan(vy)-vx*atan(vx))
L02606  
L02607          return
L02608          end subroutine fprl_ints
```

<!-- code_extract code_extract.py v1.2
source: phys/module_sf_bem.F
ranges: L2618-L2632
file_lines: 2636
file_md5: e93033f4eff5816a89e6cf51c65d738a
display: line-numbered (strip L-prefix and !file: line to restore)
range_md5: 877f6efff1c42b9bf7f2d11ea2849933
seg_lines: 15
label: subroutine fnrm_ints
-->

```fortran
!file: phys/module_sf_bem.F    L2618-L2632    (subroutine fnrm_ints)
L02618          subroutine fnrm_ints(fnrm_int,wx,wy,wz)
L02619  
L02620          implicit none
L02621          
L02622  	real wx,wy,wz
L02623  	real fnrm_int
L02624  	
L02625          fnrm_int=(1./(3.141592653*wy))*(wy*atan(1./wy)+wx*atan(1./wx)- &
L02626                (sqrt(wz)*atan(1./sqrt(wz)))+                            &
L02627                (1./4.)*(log((1.+wx*wx)*(1.+wy*wy)/(1.+wz))+             &
L02628                wy*wy*log(wy*wy*(1.+wz)/(wz*(1.+wy*wy)))+                &
L02629                wx*wx*log(wx*wx*(1.+wz)/(wz*(1.+wx*wx)))))
L02630          
L02631          return
L02632          end subroutine fnrm_ints
```

> 讲解：radfluxs 是单面辐射收支一行式；radfluxspv 在屋顶面加 PV 板与屋顶的辐射串联项 pv_frac_roof·hrad·(T_pv⁴−T_roof⁴)，两式与 14b upward_rad 的屋顶 PV 常数（0.79/0.11）同源——改 PV 光学参数三处同步。

## 八、室内源与调节

<!-- code_extract code_extract.py v1.2
source: phys/module_sf_bem.F
ranges: L1829-L1864
file_lines: 2636
file_md5: e93033f4eff5816a89e6cf51c65d738a
display: line-numbered (strip L-prefix and !file: line to restore)
range_md5: 60fb5914c0c06474a57a6604b9f459b4
seg_lines: 36
label: subroutine fluxroo
-->

```fortran
!file: phys/module_sf_bem.F    L1829-L1864    (subroutine fluxroo)
L01829  	subroutine fluxroo(hseqocc,hleqocc,hsvent,hlvent, &
L01830                             hscond,hslev,hllev) 
L01831  	
L01832  !-----------------------------------------------------------------------
L01833  !This routine calculates the heat flux generated inside the room
L01834  !and the heat ejected to the atmosphere.
L01835  !----------------------------------------------------------------------	
L01836  
L01837  	implicit none
L01838  
L01839  !-----------------------------------------------------------------------
L01840  
L01841  !Input
L01842  !-----
L01843  	real hseqocc		!sensible heat generated by equipments and occupants [W]
L01844  	real hleqocc		!latent heat generated by occupants [W]
L01845  	real hsvent		!sensible heat generated by natural ventilation [W]
L01846  	real hlvent		!latent heat generated by natural ventilation [W] 
L01847  	real hscond		!sensible heat generated by wall conduction 
L01848  
L01849  !Output
L01850  !------
L01851  	real hslev		!sensible heat flux generated inside the room [W]
L01852  	real hllev		!latent heat flux generatd inside the room
L01853  
L01854  
L01855  !Calculation of the total sensible heat generated inside the room
L01856  
L01857  	hslev=hseqocc+hsvent+hscond 
L01858   
L01859  !Calculation of the total latent heat generated inside the room
L01860  	
L01861  	hllev=hleqocc+hlvent
L01862          
L01863  	return
L01864  	end subroutine fluxroo
```

<!-- code_extract code_extract.py v1.2
source: phys/module_sf_bem.F
ranges: L1869-L1891
file_lines: 2636
file_md5: e93033f4eff5816a89e6cf51c65d738a
display: line-numbered (strip L-prefix and !file: line to restore)
range_md5: b3df177f80f6fb108e91d5b603c17779
seg_lines: 23
label: subroutine phirat
-->

```fortran
!file: phys/module_sf_bem.F    L1869-L1891    (subroutine phirat)
L01869  	subroutine phirat(nhourday,rocc)
L01870  
L01871  !----------------------------------------------------------------------
L01872  !This routine calculates the occupation ratio of a floor
L01873  !By now we suppose a constant value
L01874  !----------------------------------------------------------------------
L01875  
L01876          implicit none
L01877  
L01878  !Input
L01879  !-----
L01880  
L01881  	real nhourday	! number of hours from midnight (local time)
L01882  	
L01883  !Output
L01884  !------
L01885  	real rocc       !value between 0 and 1
L01886  
L01887  !!TEST
L01888          rocc=1.
L01889  
L01890  	return
L01891  	end subroutine phirat
```

<!-- code_extract code_extract.py v1.2
source: phys/module_sf_bem.F
ranges: L1896-L1917
file_lines: 2636
file_md5: e93033f4eff5816a89e6cf51c65d738a
display: line-numbered (strip L-prefix and !file: line to restore)
range_md5: 8905d12ca9329267bff55b485154522a
seg_lines: 22
label: subroutine phiequ
-->

```fortran
!file: phys/module_sf_bem.F    L1896-L1917    (subroutine phiequ)
L01896  	subroutine phiequ(nhourday,hsesf,hsequip,hsequ)
L01897  
L01898  !----------------------------------------------------------------------
L01899  !This routine calculates the sensible heat gain from equipments
L01900  !----------------------------------------------------------------------
L01901          implicit none
L01902  !Input
L01903  !-----
L01904  
L01905  	real nhourday ! number of hours from midnight, Local time
L01906          real, intent(in) :: hsesf
L01907          real, intent(in), dimension(24) :: hsequip
L01908  	
L01909  !Output
L01910  !------
L01911  	real hsequ    !sensible heat gain from equipment [Wm\AF2]
L01912  
L01913  !---------------------------------------------------------------------	
L01914  
L01915          hsequ = hsequip(int(nhourday)+1) * hsesf
L01916          
L01917  	end subroutine phiequ
```

<!-- code_extract code_extract.py v1.2
source: phys/module_sf_bem.F
ranges: L1921-L1977
file_lines: 2636
file_md5: e93033f4eff5816a89e6cf51c65d738a
display: line-numbered (strip L-prefix and !file: line to restore)
range_md5: d63399b90aabcd77daa376ebfe06dcbb
seg_lines: 57
label: subroutine fluxeqocc
-->

```fortran
!file: phys/module_sf_bem.F    L1921-L1977    (subroutine fluxeqocc)
L01921  	subroutine fluxeqocc(nhourday,bw,bl,perflo,hsesf,hsequip,hseqocc,hleqocc)
L01922  	
L01923  	implicit none
L01924  
L01925  !---------------------------------------------------------------------
L01926  !This routine calculates the sensible and the latent heat flux 
L01927  !generated by equipments and occupants
L01928  !---------------------------------------------------------------------	
L01929  
L01930  !Input
L01931  !-----
L01932  	real bw			!Room width [m]
L01933  	real bl			!Room lengzh [m]
L01934  	real nhourday		!number of hours from the beginning of the day
L01935          real, intent(in) :: perflo ! Peak number of occupants per unit floor area
L01936          real, intent(in) :: hsesf
L01937          real, intent(in), dimension(24) :: hsequip
L01938  
L01939  !Output
L01940  !------
L01941  	real hseqocc		!sensible heat generated by equipments and occupants [W]
L01942  	real hleqocc		!latent heat generated by occupants [W]
L01943  !Local
L01944  !-----
L01945  	real Af			!Air conditioned floor area [m2]
L01946  	real rocc		!Occupation ratio of the floor [0,1]
L01947          real hsequ		!Heat generated from equipments 
L01948  
L01949          real hsocc		!Sensible heat generated by a person [W/Person]
L01950                                  !Source Boundary Layer Climates,page 195 (book)
L01951          parameter (hsocc=160.)
L01952  
L01953          real hlocc		!Latent heat generated by a person [W/Person]
L01954                                  !Source Boundary Layer Climates,page 225 (book)
L01955          parameter (hlocc=1.96e6/86400.)
L01956  
L01957  !------------------------------------------------------------------
L01958  !			Sensible heat flux
L01959  !			------------------
L01960  
L01961  	 Af=bw*bl
L01962  
L01963  	 call phirat(nhourday,rocc)
L01964  
L01965           call phiequ(nhourday,hsesf,hsequip,hsequ)
L01966  
L01967           hseqocc=Af*rocc*perflo*hsocc+Af*hsequ
L01968  
L01969  !
L01970  !			Latent heat
L01971  !			-----------
L01972  !
L01973  
L01974           hleqocc=Af*rocc*perflo*hlocc
L01975  
L01976  	return
L01977  	end subroutine fluxeqocc
```

> 讲解：室内热源汇总（hslev=人员设备+通风+围护导热；hllev=人员+通风）；phirat 占用率**硬编码 1.0**（TODO 注释在案——办公昼夜占用曲线是天然扩展点）；phiequ 设备热=24h 谱 hsequip(int(nhourday)+1)×hsesf（谱面积因子）；人员显热 160 W/人（Oke《Boundary Layer Climates》p195）、潜热 1.96e6/86400 W/人（每日 1.96 MJ 水汽折算）。

<!-- code_extract code_extract.py v1.2
source: phys/module_sf_bem.F
ranges: L1982-L2029
file_lines: 2636
file_md5: e93033f4eff5816a89e6cf51c65d738a
display: line-numbered (strip L-prefix and !file: line to restore)
range_md5: b349a363acc3986e36910c4976c0c1d6
seg_lines: 48
label: subroutine fluxvent
-->

```fortran
!file: phys/module_sf_bem.F    L1982-L2029    (subroutine fluxvent)
L01982  	subroutine fluxvent(cpint,rhoint,vollev,tlev,tout,latent,&
L01983                              humout,rhoout,humlev,beta,hsvent,hlvent)
L01984  	
L01985  	implicit none
L01986  
L01987  !---------------------------------------------------------------------
L01988  !This routine calculates the sensible and the latent heat flux 
L01989  !generated by natural ventilation
L01990  !---------------------------------------------------------------------
L01991  
L01992  !Input
L01993  !-----
L01994  	real cpint		!specific heat of the indoor air [J/kg.K]
L01995  	real rhoint		!density of the indoor air [Kg/m3]	
L01996  	real vollev		!volume of the room [m3]
L01997  	real tlev		!Room temperature [K]
L01998  	real tout		!outside air temperature [K]
L01999  	real latent		!latent heat of evaporation [J/Kg]
L02000  	real humout		!outside absolute humidity [Kgwater/Kgair]
L02001  	real rhoout		!air density [kg/m3]
L02002  	real humlev		!Specific humidity of the indoor air [Kgwater/Kgair]
L02003          real, intent(in) :: beta!Thermal efficiency of the heat exchanger 
L02004  	
L02005  !Output
L02006  !------
L02007  	real hsvent		!sensible heat generated by natural ventilation [W]
L02008  	real hlvent		!latent heat generated by natural ventilation [W] 
L02009  
L02010  !Local
L02011  !-----       
L02012          
L02013  !----------------------------------------------------------------------
L02014  
L02015  !			Sensible heat flux
L02016  !			------------------
L02017          
L02018  	hsvent=(1.-beta)*cpint*rhoint*(vollev/3600.)*  &
L02019                 (tout-tlev)
L02020  	
L02021  !			Latent heat flux
L02022  !			----------------
L02023         
L02024  	hlvent=(1.-beta)*latent*rhoint*(vollev/3600.)* &
L02025       	       (humout-humlev)
L02026  
L02027  
L02028  	return
L02029  	end subroutine fluxvent
```

> 讲解：自然通风：**每小时一次全换气**（vollev/3600 m³/s 的隐含假设——既非 ACH 可调也无风压/热压驱动），换热器效率 beta 只对温差折扣；(1−beta) 因子把「回收后」的净通量加给室内。改造点：把 1/3600 换成可调 ACH 或加风压项是最常见的 BEM 扩展。

<!-- code_extract code_extract.py v1.2
source: phys/module_sf_bem.F
ranges: L2034-L2080
file_lines: 2636
file_md5: e93033f4eff5816a89e6cf51c65d738a
display: line-numbered (strip L-prefix and !file: line to restore)
range_md5: 713983c89243a14a15c525ac8023f1ff
seg_lines: 47
label: subroutine fluxcond
-->

```fortran
!file: phys/module_sf_bem.F    L2034-L2080    (subroutine fluxcond)
L02034  	subroutine fluxcond(hswalins,hswinins,surwal,pwin,hscond)
L02035  	
L02036  	implicit none
L02037  
L02038  !---------------------------------------------------------------------
L02039  !This routine calculates the sensible heat flux generated by 
L02040  !wall conduction.
L02041  !---------------------------------------------------------------------
L02042  
L02043  !Input
L02044  !-----
L02045  	real hswalins(6)	!sensible heat at the internal layers of the wall [W/m2]
L02046  	real hswinins(4)	!internal window sensible heat flux [W/m2]
L02047  	real surwal(6)	        !surfaces of the room walls [m2]
L02048  	real pwin               !window proportion	
L02049  
L02050  
L02051  !Output
L02052  !------
L02053  	
L02054  	real hscond		!sensible heat generated by wall conduction [W]
L02055  	
L02056  !Local
L02057  !-----
L02058  
L02059  	integer ivw
L02060  
L02061  !----------------------------------------------------------------------
L02062  
L02063  	  hscond=0.
L02064  
L02065  	do ivw=1,4
L02066  	   hscond=hscond+surwal(ivw)*(1-pwin)*hswalins(ivw)+ &
L02067                    surwal(ivw)*pwin*hswinins(ivw)	         
L02068  	end do
L02069  
L02070  	do ivw=5,6
L02071      	   hscond=hscond+surwal(ivw)*hswalins(ivw)	
L02072  	end do
L02073  !           
L02074  !Finally we must change the sign in hscond to be proportional
L02075  !to the difference (Twall-Tindoor).
L02076  !
L02077          hscond=(-1)*hscond 
L02078  
L02079  	return
L02080  	end subroutine fluxcond
```

> 讲解：围护导热进入房间的合计：四竖墙按 (1−pwin)·墙流+pwin·窗流、地板/天花板全额；末尾符号翻转使 hscond∝(T_wall−T_indoor) 方向一致——调试室内温度符号问题先看这行。

<!-- code_extract code_extract.py v1.2
source: phys/module_sf_bem.F
ranges: L2085-L2165
file_lines: 2636
file_md5: e93033f4eff5816a89e6cf51c65d738a
display: line-numbered (strip L-prefix and !file: line to restore)
range_md5: 17e6101cad3c1c1bf5b621b1d98aad10
seg_lines: 81
label: subroutine regtemp
-->

```fortran
!file: phys/module_sf_bem.F    L2085-L2165    (subroutine regtemp)
L02085  	subroutine regtemp(swcond,nhourday,dt,Qb,hsroo,          &
L02086                             tlev,timeon,timeoff,targtemp,gaptemp,hsneed)
L02087  	
L02088  	implicit none
L02089  
L02090  !---------------------------------------------------------------------
L02091  !This routine calculates the sensible heat fluxes, 
L02092  !after anthropogenic regulation (air conditioning)
L02093  !---------------------------------------------------------------------
L02094  
L02095  !Input:
L02096  !-----.
L02097          integer swcond       !swich air conditioning
L02098  	real nhourday        !number of hours from the beginning of the day real
L02099  	real dt	             !time step [s]
L02100  	real Qb		     !overall heat capacity of the indoor air [J/K]
L02101          real hsroo           !sensible heat flux generated inside the room [W]
L02102          real tlev            !room air temperature [K]
L02103          real, intent(in) :: timeon  ! Initial local time of A/C systems
L02104          real, intent(in) :: timeoff ! Ending local time of A/C systems
L02105          real, intent(in) :: targtemp! Target temperature of A/C systems
L02106          real, intent(in) :: gaptemp ! Comfort range of indoor temperature
L02107          
L02108  
L02109  !Local:
L02110  !-----.
L02111  
L02112          real templev         !hipotetical room air temperature [K]
L02113          real alpha           !variable to control the heating/cooling of 
L02114                               !the air conditining system
L02115  !Output:
L02116  !-----.
L02117  	real hsneed	     !sensible heat extracted to the indoor air [W]
L02118  !---------------------------------------------------------------------
L02119  !initialize variables
L02120  !---------------------
L02121          templev = 0.
L02122          alpha   = 0.
L02123  
L02124          if (swcond.eq.0) then ! there is not air conditioning in the floor
L02125              hsneed = 0.
L02126              goto 100
L02127          else
L02128              if ((nhourday.ge.timeon).and.(nhourday.le.timeoff)) then
L02129                 templev=tlev+(dt/Qb)*hsroo
L02130                 goto 200
L02131              else
L02132                 hsneed = 0.     ! air conditioning is switched off
L02133                 goto 100
L02134              endif
L02135          endif
L02136  
L02137  200     continue
L02138  
L02139          if (abs(templev-targtemp).le.gaptemp) then
L02140             hsneed = 0.
L02141          else 
L02142             if (templev.gt.(targtemp+gaptemp)) then
L02143                hsneed=hsroo-(Qb/dt)*(targtemp+gaptemp-tlev)
L02144                alpha=(abs(hsneed-hsroo)/Qb)
L02145                if (alpha.gt.temp_rat) then
L02146                    hsneed=hsroo+temp_rat*Qb
L02147                    goto 100
L02148                else
L02149                    goto 100
L02150                endif
L02151             else 
L02152                hsneed=hsroo-(Qb/dt)*(targtemp-gaptemp-tlev)
L02153                alpha=(abs(hsneed-hsroo)/Qb)
L02154                if (alpha.gt.temp_rat) then
L02155                    hsneed=hsroo-temp_rat*Qb
L02156                    goto 100
L02157                else
L02158                    goto 100
L02159                endif
L02160             endif
L02161          endif 
L02162  
L02163  100     continue
L02164  	return
L02165  	end subroutine regtemp
```

<!-- code_extract code_extract.py v1.2
source: phys/module_sf_bem.F
ranges: L2170-L2253
file_lines: 2636
file_md5: e93033f4eff5816a89e6cf51c65d738a
display: line-numbered (strip L-prefix and !file: line to restore)
range_md5: d1fed6ed8583fb080ffddd524dd87329
seg_lines: 84
label: subroutine reghum
-->

```fortran
!file: phys/module_sf_bem.F    L2170-L2253    (subroutine reghum)
L02170  	 subroutine reghum(swcond,nhourday,dt,volroo,rhoint,latent, &
L02171                             hlroo,shumroo,timeon,timeoff,targhum,gaphum,hlneed)
L02172  
L02173  	 implicit none
L02174  
L02175  !---------------------------------------------------------------------
L02176  !This routine calculates the latent heat fluxes, 
L02177  !after anthropogenic regulation (air conditioning)
L02178  !---------------------------------------------------------------------
L02179  
L02180  !Input:
L02181  !-----.
L02182          integer swcond    !swich air conditioning
L02183  	real nhourday     !number of hours from the beginning of the day real[h]
L02184  	real dt	          !time step [s]
L02185  	real volroo       !volume of the room [m3]
L02186          real rhoint       !density of the internal air [Kg/m3]
L02187          real latent       !latent heat of evaporation [J/Kg]
L02188          real hlroo        !latent heat flux generated inside the room [W]
L02189          real shumroo      !specific humidity of the indoor air [kg/kg]
L02190          real, intent(in) :: timeon  ! Initial local time of A/C systems
L02191          real, intent(in) :: timeoff ! Ending local time of A/C systems
L02192          real, intent(in) :: targhum ! Target humidity of the A/C systems
L02193          real, intent(in) :: gaphum  ! comfort range of the specific humidity
L02194  
L02195  !Local:
L02196  !-----.
L02197  
L02198          real humlev       !hipotetical specific humidity of the indoor [kg/kg]
L02199          real betha        !variable to control the drying/moistening of
L02200                            !the air conditioning system
L02201  !Output:
L02202  !-----.
L02203  	real hlneed	  !latent heat extracted to the indoor air [W]
L02204  !------------------------------------------------------------------------
L02205  !initialize variables
L02206  !---------------------
L02207          humlev = 0.
L02208          betha  = 0.
L02209  
L02210          if (swcond.eq.0) then ! there is not air conditioning in the floor
L02211              hlneed = 0.
L02212              goto 100
L02213          else
L02214              if ((nhourday.ge.timeon).and.(nhourday.le.timeoff)) then
L02215                 humlev=shumroo+(dt/(latent*rhoint*volroo))*hlroo
L02216                 goto 200
L02217              else
L02218                 hlneed = 0.     ! air conditioning is switched off
L02219                 goto 100
L02220              endif
L02221          endif
L02222  
L02223  200     continue
L02224  
L02225          if (abs(humlev-targhum).le.gaphum) then
L02226             hlneed = 0.
L02227          else 
L02228             if (humlev.gt.(targhum+gaphum)) then
L02229                hlneed=hlroo-((latent*rhoint*volroo)/dt)* &
L02230                            (targhum+gaphum-shumroo)
L02231                betha=abs(hlneed-hlroo)/(latent*rhoint*volroo)
L02232                if (betha.gt.hum_rat) then
L02233                    hlneed=hlroo+hum_rat*(latent*rhoint*volroo)
L02234                    goto 100
L02235                else
L02236                    goto 100
L02237                endif
L02238             else 
L02239                hlneed=hlroo-((latent*rhoint*volroo)/dt)* &
L02240                            (targhum-gaphum-shumroo)
L02241                betha=abs(hlneed-hlroo)/(latent*rhoint*volroo)
L02242                if (betha.gt.hum_rat) then
L02243                    hlneed=hlroo-hum_rat*(latent*rhoint*volroo)
L02244                    goto 100
L02245                else
L02246                    goto 100
L02247                endif
L02248             endif
L02249          endif 
L02250  	
L02251  100     continue
L02252  	return
L02253  	end subroutine reghum
```

> 讲解：恒温器/湿度调节器的完整状态机：①sw_cond=0 或不在时间窗（nhourday∈[timeon,timeoff]）→ need=0；②先算「无空调时的假想温度」templev=tlev+(dt/Qb)·hsroo；③|templev−targ|≤gap（死区）→ need=0；④越上界：need=hsroo−(Qb/dt)(targ+gap−tlev)（一步拉回死区边的热量需求），若需求速率超 temp_rat 则限速 hsneed=hsroo+temp_rat·Qb；⑤越下界对称。reghum 同构（容积×ρ×latent 代替 Qb）。**这套「一步拉回+限速」是空调废热hsout 的唯一来源——标定 targtemp/gaptemp 就是标定空调废热的时空分布（论文 2 CAL-STEAM 的直接抓手）。**

<!-- code_extract code_extract.py v1.2
source: phys/module_sf_bem.F
ranges: L2258-L2312
file_lines: 2636
file_md5: e93033f4eff5816a89e6cf51c65d738a
display: line-numbered (strip L-prefix and !file: line to restore)
range_md5: 9aa7a9d182a779b52346621fcbe65ea4
seg_lines: 55
label: subroutine air_cond
-->

```fortran
!file: phys/module_sf_bem.F    L2258-L2312    (subroutine air_cond)
L02258           subroutine air_cond(hsneed,hlneed,dt,hsout,hlout,consump,cop)
L02259  
L02260           implicit none
L02261  
L02262  !
L02263  !Performance of the air conditioning system        
L02264  !
L02265  !INPUT/OUTPUT VARIABLES
L02266           real, intent(in) :: cop
L02267  !
L02268  !INPUT/OUTPUT VARIABLES
L02269  !       
L02270           real hsneed     !sensible heat that is necessary for cooling/heating
L02271                           !the indoor air temperature [W] 
L02272           real hlneed     !latent heat that is necessary for controling
L02273                           !the humidity of the indoor air [W]
L02274           real dt         !time step [s]
L02275  !
L02276  !OUTPUT VARIABLES
L02277  !
L02278           real hsout      !sensible heat pumped out into the atmosphere [W]
L02279           real hlout      !latent heat pumped out into the atmosphere [W]
L02280           real consump    !Electrical consumption of the air conditioning system [W] 
L02281                           
L02282      
L02283  !
L02284  !Performance of the air conditioning system
L02285  !
L02286           if (hsneed.gt.0) then         ! air conditioning is cooling 
L02287                                         ! and the heat is pumped out into the atmosphere  
L02288  	  hsout=(1/cop)*(abs(hsneed)+abs(hlneed))+hsneed
L02289            hlout=hlneed
L02290            consump=(1./cop)*(abs(hsneed)+abs(hlneed))
L02291  !!        hsout=0.             
L02292  !!        hlout=0.
L02293  
L02294           else if(hsneed.eq.0.) then !air conditioning is not working to regulate the indoor temperature
L02295                 hlneed=0.       !no humidity regulation is considered 
L02296                 hsout=0.        !no output into the atmosphere (sensible heat) 
L02297                 hlout=0.        !no output into the atmosphere (latent heat)
L02298                 consump=0.      !no electrical consumption
L02299  
L02300                else  !! hsneed < 0. !air conditioning is heating 
L02301                 hlneed=0.           !no humidity regulation is considered
L02302                 hlout=0.            !no output into the atmosphere (latent heat) 
L02303                 consump=(1./cop)*(abs(hsneed)+abs(hlneed))
L02304  !
L02305  !!We have two possibilities 
L02306  ! 
L02307  !!             hsout=(1./cop)*(abs(hsneed)+abs(hlneed)) !output into the atmosphere 
L02308                 hsout=0.                            !no output into the atmosphere                        
L02309           end if
L02310  
L02311           return 
L02312           end subroutine air_cond
```

> 讲解：COP 账本：制冷（hsneed>0）：废热 hsout=(1/cop)·(|hsneed|+|hlneed|)+hsneed——压缩机耗电 1/cop 变废热排大气 + 从室内搬出的 hsneed；除湿 hlneed 直接排（冷凝水离开系统）；耗电 consump=(1/cop)(|hsneed|+|hlneed|)。制热（hsneed<0）：耗电同式，废热 hsout=0（注释保留了「废热=耗电」的备选式）。hsneed=0 时全零。

<!-- code_extract code_extract.py v1.2
source: phys/module_sf_bem.F
ranges: L2317-L2363
file_lines: 2636
file_md5: e93033f4eff5816a89e6cf51c65d738a
display: line-numbered (strip L-prefix and !file: line to restore)
range_md5: 5a4f2e872ce26da132970c63f347da38
seg_lines: 47
label: subroutine consump_total
-->

```fortran
!file: phys/module_sf_bem.F    L2317-L2363    (subroutine consump_total)
L02317          subroutine consump_total(nzcanm,nlev,consumpbuild,hsoutbuild, &
L02318                                   hsout,consump)
L02319  
L02320          implicit none
L02321          
L02322  !-----------------------------------------------------------------------
L02323  !Compute the total consumption in kWh/s (1kWh=3.6e+6 J) and sensible heat
L02324  !ejected into the atmosphere per building
L02325  !------------------------------------------------------------------------
L02326  !
L02327  !INPUT VARIABLES
L02328  !
L02329  !
L02330          integer nzcanm            !Maximum number of vertical levels in the urban grid
L02331          real hsout(nzcanm)        !sensible heat emitted outside the room [W]
L02332          real consump(nzcanm)      !Electricity consumption for the a.c. in each floor[W]
L02333  !
L02334  !OUTPUT VARIABLES
L02335  !
L02336  	real consumpbuild         !Energetic consumption for the entire building[kWh/s]
L02337          real hsoutbuild           !Total sensible heat ejected into the atmosphere
L02338                                    !by the air conditioning systems per building [W]        
L02339  !
L02340  !LOCAL  VARIABLES
L02341  !
L02342          integer ilev
L02343  
L02344  !
L02345  !INPUT VARIABLES
L02346  !
L02347          integer nlev     
L02348          
L02349  !
L02350  !INITIALIZE VARIABLES
L02351  !
L02352          consumpbuild=0.
L02353          hsoutbuild=0.
L02354  !
L02355          do ilev=1,nlev
L02356             consumpbuild=consumpbuild+consump(ilev)
L02357             hsoutbuild=hsoutbuild+hsout(ilev)
L02358          enddo !ilev
L02359  
L02360          consumpbuild=consumpbuild/(3.6e+06)
L02361  
L02362          return 
L02363          end subroutine consump_total
```

> 讲解：全楼汇总：consumpbuild=Σconsump/(3.6e6)（W→kWh/s）、hsoutbuild=Σhsout（W）。上游 BEP_BEM 再乘 meso_urb_ac 折算到格点（14a §四⑤）。

## 九、改造入口（论文 2 对接）

1. **标量→逐格场**（论文 2 主线）：cop/beta/sw_cond/timeon/timeoff/targtemp/gaptemp/targhum/gaphum/perflo/hsesf/hsequip/irho 目前全是「每类一标量」（init_para 从 TBL 读，经 BEP1D 的 `*_u(iurb)` 传入）。改造路径：①Registry 增 urban_map_* 维度与 3D 场（先例：ind_* 折叠表+urban_map_zwd，14a §四①）；②module_sf_urban 的 TBL 读入处加 auxinput 通道；③BEP_BEM 主入口的聚合式（meso_urb_ac×类参数）同步改为逐格。**性能陷阱：wall/wall_gr 的 swwal+save 系数缓存按类失效——逐格参数下场化后必须逐点缓存或重算。**
2. **扩展点**：phirat 占用率昼夜曲线；fluxvent 换 ACH/风压驱动；effpv 与 PV 三层材料参数；temp_rat/hum_rat 限速。
3. **验证锚点**：室内温度 tlev/空调耗电 consump/废热 hsout 三诊断量与观测 TG、室内温度（论文 2 W240）对标；单点 sanity 见 ch19/ch17 的对照跑设计（sf_urban_physics=0 vs 3）。

## 十、上下游链接

- 上游调用者：[code_14a_module_sf_bep_bem.md](code_14a_module_sf_bep_bem.md)（BEP1D 的 BEM 循环）——实参表就是本篇 §四的接口契约。
- 同族：[code_15_module_sf_bep.md](code_15_module_sf_bep.md)（BEP 单独版，不调本文件）；共享底座 [code_14b_module_sf_bep_bem.md](code_14b_module_sf_bep_bem.md)（辐射/导热/视野因子）；参数库 module_sf_urban（17 篇待交付）。
- 驱动链：[code_22_module_pbl_driver.md](code_22_module_pbl_driver.md)；面层 [code_10_module_sf_mynnsfc.md](code_10_module_sf_mynnsfc.md)。
- 教材正文：[ch17_urban_canopy.md](../ch17_urban_canopy.md)（BEM 专节）、[ch19_lanzhou_heatwave.md](../ch19_lanzhou_heatwave.md)（城市冠层对照双跑）、[ch20_modifying_wrf.md](../ch20_modifying_wrf.md)（三级改造实录）。
