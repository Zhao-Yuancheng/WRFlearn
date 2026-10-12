# code_14b — BEP/BEM 共享底座·下半（module_sf_bep_bem.F：辐射、导热、通量与初始化单元）

## 一、版本指纹

| 源文件 | 行数 | md5（整文件，按字节） |
|---|---|---|
| phys/module_sf_bep_bem.F | 5706 | 8d13861f088e806d2558dd37e31126f2 |

- 抽取工具：workspace/scripts/code_extract.py v1.2，2026-10-12；块首指纹注释自带 range_md5。
- 本篇承接 [code_14a_module_sf_bep_bem.md](code_14a_module_sf_bep_bem.md)（主入口 BEP_BEM、柱求解器 BEP1D、param/interpol/averaging_temp/modif_rad/surf_temp/roof_temp_veg/buildings 九单元）；14b 收录 L2892–L5705 全部单元（A 级全文）。

## 二、城市网格 → 模式网格

<!-- code_extract code_extract.py v1.2
source: phys/module_sf_bep_bem.F
ranges: L2897-L3115
file_lines: 5706
file_md5: 8d13861f088e806d2558dd37e31126f2
display: line-numbered (strip L-prefix and !file: line to restore)
range_md5: 94bf9cd35a2c3963170c5a1342447ef9
seg_lines: 219
label: subroutine urban_meso
-->

```fortran
!file: phys/module_sf_bep_bem.F    L2897-L3115    (subroutine urban_meso)
L02897          subroutine urban_meso(nd,kms,kme,kts,kte,nz_u,z,dz,z_u,pb,ss,bs,ws,sf,vl,    &
L02898                               uva_u,vva_u,uvb_u,vvb_u,tva_u,tvb_u,evb_u, &       
L02899                               uhb_u,vhb_u,thb_u,ehb_u,qhb_u,qvb_u,       &      
L02900                               a_u,a_v,a_t,a_e,b_u,b_v,b_t,b_e,b_q,tvb_ac,b_ac)           
L02901  
L02902  ! ----------------------------------------------------------------------
L02903  !  This routine interpolates the parameters from the "urban grid" to the
L02904  !  "mesoscale grid".
L02905  !  See p300-301 Appendix B.2 of the BLM paper.  
L02906  ! ----------------------------------------------------------------------
L02907  
L02908        implicit none
L02909  
L02910  ! ----------------------------------------------------------------------
L02911  ! INPUT:
L02912  ! ----------------------------------------------------------------------
L02913  ! Data relative to the "mesoscale grid"
L02914        integer kms,kme,kts,kte               
L02915        real z(kms:kme)              ! Altitude above the ground of the cell interface
L02916        real dz(kms:kme)               ! Vertical space steps
L02917  
L02918  ! Data relative to the "uban grid"
L02919        integer nz_u              ! Number of layer in the urban grid
L02920        integer nd                ! Number of street direction for the current urban class
L02921        real bs(ndm)              ! Building widths of the current urban class
L02922        real ws(ndm)              ! Street widths of the current urban class
L02923        real z_u(nz_um)         ! Height of the urban grid levels
L02924        real pb(nz_um)          ! Probability to have a building with an height equal
L02925        real ss(nz_um)          ! Probability to have a building with height h
L02926        real uhb_u(ndm,nz_um)   ! U (x-wind component) Horizontal surfaces, B (explicit) term
L02927        real uva_u(2*ndm,nz_um)   ! U (x-wind component) Vertical surfaces, A (implicit) term
L02928        real uvb_u(2*ndm,nz_um)   ! U (x-wind component) Vertical surfaces, B (explicit) term
L02929        real vhb_u(ndm,nz_um)   ! V (y-wind component) Horizontal surfaces, B (explicit) term
L02930        real vva_u(2*ndm,nz_um)   ! V (y-wind component) Vertical surfaces, A (implicit) term
L02931        real vvb_u(2*ndm,nz_um)   ! V (y-wind component) Vertical surfaces, B (explicit) term
L02932        real thb_u(ndm,nz_um)   ! Temperature        Horizontal surfaces, B (explicit) term
L02933        real tva_u(2*ndm,nz_um)   ! Temperature          Vertical surfaces, A (implicit) term
L02934        real tvb_u(2*ndm,nz_um)   ! Temperature          Vertical surfaces, B (explicit) term
L02935        real tvb_ac(2*ndm,nz_um)
L02936        real ehb_u(ndm,nz_um)   ! Energy (TKE)       Horizontal surfaces, B (explicit) term
L02937        real evb_u(2*ndm,nz_um)   ! Energy (TKE)         Vertical surfaces, B (explicit) term
L02938  !
L02939  !New variables for BEM
L02940  !
L02941        real qhb_u(ndm,nz_um)
L02942        real qvb_u(2*ndm,nz_um)
L02943       
L02944  
L02945  ! ----------------------------------------------------------------------
L02946  ! OUTPUT:
L02947  ! ----------------------------------------------------------------------
L02948  ! Data relative to the "mesoscale grid"
L02949        real sf(kms:kme)             ! Surface of the "mesoscale grid" cells taking into account the buildings
L02950        real vl(kms:kme)               ! Volume of the "mesoscale grid" cells taking into account the buildings
L02951        real a_u(kms:kme)              ! Implicit component of the momentum sources or sinks in the X-direction
L02952        real a_v(kms:kme)              ! Implicit component of the momentum sources or sinks in the Y-direction
L02953        real a_t(kms:kme)              ! Implicit component of the heat sources or sinks
L02954        real a_e(kms:kme)              ! Implicit component of the TKE sources or sinks
L02955        real b_u(kms:kme)              ! Explicit component of the momentum sources or sinks in the X-direction
L02956        real b_v(kms:kme)              ! Explicit component of the momentum sources or sinks in the Y-direction
L02957        real b_t(kms:kme)              ! Explicit component of the heat sources or sinks
L02958        real b_ac(kms:kme)
L02959        real b_e(kms:kme)              ! Explicit component of the TKE sources or sinks
L02960        real b_q(kms:kme)               ! Explicit component of the humidity sources or sinks
L02961  ! ----------------------------------------------------------------------
L02962  ! LOCAL:
L02963  ! ----------------------------------------------------------------------
L02964        real dzz
L02965        real fact
L02966        integer id,iz,iz_u
L02967        real se,sr,st,su,sv,sq
L02968        real uet(kms:kme)                ! Contribution to TKE due to walls
L02969        real veb,vta,vtb,vte,vtot,vua,vub,vva,vvb,vqb,vtb_ac
L02970  
L02971  
L02972  ! ----------------------------------------------------------------------
L02973  ! END VARIABLES DEFINITIONS
L02974  ! ---------------------------------------------------------------------- 
L02975  
L02976  ! initialisation
L02977  
L02978        do iz=kts,kte
L02979           a_u(iz)=0.
L02980           a_v(iz)=0.
L02981           a_t(iz)=0.
L02982           a_e(iz)=0.
L02983           b_u(iz)=0.
L02984           b_v(iz)=0.
L02985           b_e(iz)=0.
L02986           b_t(iz)=0.
L02987           b_ac(iz)=0.
L02988           uet(iz)=0.
L02989           b_q(iz)=0.
L02990        end do
L02991              
L02992  ! horizontal surfaces
L02993        do iz=kts,kte
L02994           sf(iz)=0.
L02995           vl(iz)=0.
L02996        enddo
L02997        sf(kte+1)=0. 
L02998        
L02999        do id=1,nd      
L03000           do iz=kts+1,kte+1
L03001              sr=0.
L03002              do iz_u=2,nz_u
L03003                 if(z(iz).lt.z_u(iz_u).and.z(iz).ge.z_u(iz_u-1))then
L03004                    sr=pb(iz_u)
L03005                 endif
L03006              enddo
L03007              sf(iz)=sf(iz)+((ws(id)+(1.-sr)*bs(id))/(ws(id)+bs(id)))/nd
L03008           enddo
L03009        enddo
L03010  
L03011  ! volume      
L03012        do iz=kts,kte
L03013           do id=1,nd
L03014              vtot=0.
L03015              do iz_u=1,nz_u
L03016                 dzz=max(min(z_u(iz_u+1),z(iz+1))-max(z_u(iz_u),z(iz)),0.)
L03017                 vtot=vtot+pb(iz_u+1)*dzz
L03018              enddo
L03019              vtot=vtot/(z(iz+1)-z(iz))
L03020              vl(iz)=vl(iz)+(1.-vtot*bs(id)/(ws(id)+bs(id)))/nd
L03021           enddo
L03022        enddo
L03023        
L03024  ! horizontal surface impact  
L03025  
L03026        do id=1,nd
L03027        
L03028           fact=1./vl(kts)/dz(kts)*ws(id)/(ws(id)+bs(id))/nd
L03029           b_t(kts)=b_t(kts)+thb_u(id,1)*fact
L03030           b_u(kts)=b_u(kts)+uhb_u(id,1)*fact
L03031           b_v(kts)=b_v(kts)+vhb_u(id,1)*fact 
L03032           b_e(kts)=b_e(kts)+ehb_u(id,1)*fact*(z_u(2)-z_u(1))
L03033           b_q(kts)=b_q(kts)+qhb_u(id,1)*fact         
L03034  
L03035           do iz=kts,kte
L03036              st=0.
L03037              su=0.
L03038              sv=0.
L03039              se=0.
L03040              sq=0.
L03041              do iz_u=2,nz_u
L03042                 if(z(iz).le.z_u(iz_u).and.z(iz+1).gt.z_u(iz_u))then
L03043                    st=st+ss(iz_u)*thb_u(id,iz_u)
L03044                    su=su+ss(iz_u)*uhb_u(id,iz_u)
L03045                    sv=sv+ss(iz_u)*vhb_u(id,iz_u)          
L03046                    se=se+ss(iz_u)*ehb_u(id,iz_u)*(z_u(iz_u+1)-z_u(iz_u))
L03047                    sq=sq+ss(iz_u)*qhb_u(id,iz_u)
L03048                 endif
L03049              enddo
L03050        
L03051              fact=bs(id)/(ws(id)+bs(id))/vl(iz)/dz(iz)/nd
L03052              b_t(iz)=b_t(iz)+st*fact
L03053              b_u(iz)=b_u(iz)+su*fact
L03054              b_v(iz)=b_v(iz)+sv*fact
L03055              b_e(iz)=b_e(iz)+se*fact
L03056              b_q(iz)=b_q(iz)+sq*fact
L03057           enddo
L03058        enddo              
L03059  
L03060  ! vertical surface impact
L03061             
L03062        do iz=kts,kte 
L03063           uet(iz)=0.
L03064           do id=1,nd              
L03065              vtb=0.
L03066              vtb_ac=0.
L03067              vta=0.
L03068              vua=0.
L03069              vub=0.
L03070              vva=0.
L03071              vvb=0.
L03072              veb=0.
L03073  	    vte=0.
L03074              vqb=0.
L03075              do iz_u=1,nz_u
L03076                 dzz=max(min(z_u(iz_u+1),z(iz+1))-max(z_u(iz_u),z(iz)),0.)
L03077                 fact=dzz/(ws(id)+bs(id))
L03078                 vtb=vtb+pb(iz_u+1)*                                  &        
L03079                      (tvb_u(2*id-1,iz_u)+tvb_u(2*id,iz_u))*fact 
L03080                 vtb_ac=vtb_ac+pb(iz_u+1)*                            &        
L03081                      (tvb_ac(2*id-1,iz_u)+tvb_ac(2*id,iz_u))*fact     
L03082                 vta=vta+pb(iz_u+1)*                                  &        
L03083                     (tva_u(2*id-1,iz_u)+tva_u(2*id,iz_u))*fact
L03084                 vua=vua+pb(iz_u+1)*                                  &        
L03085                      (uva_u(2*id-1,iz_u)+uva_u(2*id,iz_u))*fact
L03086                 vva=vva+pb(iz_u+1)*                                  &        
L03087                      (vva_u(2*id-1,iz_u)+vva_u(2*id,iz_u))*fact
L03088                 vub=vub+pb(iz_u+1)*                                  &        
L03089                      (uvb_u(2*id-1,iz_u)+uvb_u(2*id,iz_u))*fact
L03090                 vvb=vvb+pb(iz_u+1)*                                  &        
L03091                      (vvb_u(2*id-1,iz_u)+vvb_u(2*id,iz_u))*fact
L03092                 veb=veb+pb(iz_u+1)*                                  &        
L03093                      (evb_u(2*id-1,iz_u)+evb_u(2*id,iz_u))*fact
L03094                 vqb=vqb+pb(iz_u+1)*                                  &        
L03095                      (qvb_u(2*id-1,iz_u)+qvb_u(2*id,iz_u))*fact   
L03096              enddo
L03097             
L03098              fact=1./vl(iz)/dz(iz)/nd
L03099              b_t(iz)=b_t(iz)+vtb*fact
L03100              b_ac(iz)=b_ac(iz)+vtb_ac*fact
L03101              a_t(iz)=a_t(iz)+vta*fact
L03102              a_u(iz)=a_u(iz)+vua*fact
L03103              a_v(iz)=a_v(iz)+vva*fact
L03104              b_u(iz)=b_u(iz)+vub*fact
L03105              b_v(iz)=b_v(iz)+vvb*fact
L03106              b_e(iz)=b_e(iz)+veb*fact
L03107              uet(iz)=uet(iz)+vte*fact
L03108              b_q(iz)=b_q(iz)+vqb*fact
L03109           enddo              
L03110        enddo
L03111        
L03112  
L03113        
L03114        return
L03115        end subroutine urban_meso
```

> 讲解：BEP 的「升网格」出口（BLM 论文附录 B.2），三件事：①**有效表面积 sf** 与**有效体积 vl**：按 pb（建筑存在概率）与街道几何折算模式格元内的可用空气面积/体积——后续通量归一的几何基数；②**水平表面源**（屋顶/路面）：按 ss（该高度有屋顶的概率）与 bs/(bs+ws) 加权，除以 vl·dz 归一到模式网格单位；③**垂直表面源**（墙面拖曳/加热/加湿）：按 pb 与重叠高度 dzz 累加墙两面的贡献，再除 vl·dz；tva_u（隐式温度项）与 tvb_ac（AC 源项）分账——b_ac 经 BEP_BEM 的 sf_ac 聚合最终成为空调废热诊断量。源项符号约定与 pbl_driver 的隐式求解器（diff3d 及各方案）直接兼容。

<!-- code_extract code_extract.py v1.2
source: phys/module_sf_bep_bem.F
ranges: L3120-L3200
file_lines: 5706
file_md5: 8d13861f088e806d2558dd37e31126f2
display: line-numbered (strip L-prefix and !file: line to restore)
range_md5: 545d8d8f737e572f2b8b29104113b1cb
seg_lines: 81
label: subroutine interp_length
-->

```fortran
!file: phys/module_sf_bep_bem.F    L3120-L3200    (subroutine interp_length)
L03120        subroutine interp_length(nd,kms,kme,kts,kte,nz_u,z_u,z,ss,ws,bs,              &
L03121                               dlg,dl_u)
L03122  
L03123  ! ----------------------------------------------------------------------     
L03124  !    Calculation of the length scales
L03125  !    See p272-274 formula (22) and (24) of the BLM paper    
L03126  ! ----------------------------------------------------------------------     
L03127       
L03128        implicit none
L03129  
L03130  
L03131  ! ----------------------------------------------------------------------     
L03132  ! INPUT:
L03133  ! ----------------------------------------------------------------------     
L03134        integer kms,kme,kts,kte                
L03135        real z(kms:kme)              ! Altitude above the ground of the cell interface
L03136        integer nd                ! Number of street direction for the current urban class
L03137        integer nz_u              ! Number of levels in the "urban grid"
L03138        real z_u(nz_um)         ! Height of the urban grid levels
L03139        real bs(ndm)              ! Building widths of the current urban class
L03140        real ss(nz_um)          ! Probability to have a building with height h
L03141        real ws(ndm)              ! Street widths of the current urban class
L03142  
L03143  
L03144  ! ----------------------------------------------------------------------     
L03145  ! OUTPUT:
L03146  ! ----------------------------------------------------------------------     
L03147        real dlg(kms:kme)              ! Height above ground (L_ground in formula (24) of the BLM paper). 
L03148        real dl_u(kms:kme)             ! Length scale (lb in formula (22) ofthe BLM paper).
L03149  
L03150  ! ----------------------------------------------------------------------
L03151  ! LOCAL:
L03152  ! ----------------------------------------------------------------------
L03153        real dlgtmp
L03154        integer id,iz,iz_u
L03155        real sftot
L03156        real ulu,ssl
L03157  
L03158  ! ----------------------------------------------------------------------
L03159  ! END VARIABLES DEFINITIONS
L03160  ! ----------------------------------------------------------------------
L03161     
L03162          do iz=kts,kte
L03163           ulu=0.
L03164           ssl=0.
L03165           do id=1,nd        
L03166            do iz_u=2,nz_u
L03167             if(z_u(iz_u).gt.z(iz))then
L03168              ulu=ulu+ss(iz_u)/z_u(iz_u)/nd
L03169              ssl=ssl+ss(iz_u)/nd
L03170             endif
L03171            enddo
L03172           enddo
L03173  
L03174          if(ulu.ne.0)then
L03175            dl_u(iz)=ssl/ulu
L03176           else
L03177            dl_u(iz)=0.
L03178           endif
L03179          enddo
L03180         
L03181  
L03182          do iz=kts,kte
L03183           dlg(iz)=0.
L03184            do id=1,nd
L03185             sftot=ws(id)  
L03186             dlgtmp=ws(id)/((z(iz)+z(iz+1))/2.)
L03187             do iz_u=1,nz_u
L03188              if((z(iz)+z(iz+1))/2..gt.z_u(iz_u))then
L03189               dlgtmp=dlgtmp+ss(iz_u)*bs(id)/                           &                
L03190                      ((z(iz)+z(iz+1))/2.-z_u(iz_u))
L03191               sftot=sftot+ss(iz_u)*bs(id)
L03192              endif
L03193             enddo
L03194             dlg(iz)=dlg(iz)+dlgtmp/sftot/nd
L03195           enddo
L03196           dlg(iz)=1./dlg(iz)
L03197          enddo
L03198          
L03199         return
L03200         end subroutine interp_length
```

> 讲解：BEP 的混合长输出（BLM 论文式 22/24——供 PBL 方案的 TKE 闭合用）：dl_u=Σ(ss/z_u)/Σ(ss/z_u⁻¹) 的加权倒数——高于模式层顶的建筑对湍流混合长的贡献；dlg 是「到最近墙面的平均距离」型长度（含路面项 ws/z 与墙面项 ss·bs/(z−z_u) 的调和平均）。MYJ/BouLac/KEPS 的多城市分支用这两个量替换局地混合长。

## 三、峡谷辐射

<!-- code_extract code_extract.py v1.2
source: phys/module_sf_bep_bem.F
ranges: L3205-L3330
file_lines: 5706
file_md5: 8d13861f088e806d2558dd37e31126f2
display: line-numbered (strip L-prefix and !file: line to restore)
range_md5: ca5d470781b021dfa1d6f8ceddf0d078
seg_lines: 126
label: subroutine shadow_mas
-->

```fortran
!file: phys/module_sf_bep_bem.F    L3205-L3330    (subroutine shadow_mas)
L03205        subroutine shadow_mas(nd,nz_u,zr,deltar,ah,drst,ws,ss,pb,z,    &
L03206                             swddir,rsw,rsg,xlat)
L03207          
L03208  ! ----------------------------------------------------------------------
L03209  !         Modification of short wave radiation to take into account
L03210  !         the shadow produced by the buildings
L03211  ! ----------------------------------------------------------------------
L03212  
L03213        implicit none
L03214       
L03215  ! ----------------------------------------------------------------------
L03216  ! INPUT:
L03217  ! ----------------------------------------------------------------------
L03218        integer nd                ! Number of street direction for the current urban class
L03219        integer nz_u              ! number of vertical layers defined in the urban grid
L03220        real ah                   ! Hour angle (it should come from the radiation routine)
L03221        real deltar               ! Declination of the sun
L03222        real drst(ndm)            ! street directions for the current urban class
L03223        real swddir                   ! solar radiation
L03224        real ss(nz_um)          ! probability to have a building with height h
L03225        real pb(nz_um)          ! Probability that a building has an height greater or equal to h
L03226        real ws(ndm)              ! Street width of the current urban class
L03227        real z(nz_um)           ! Height of the urban grid levels
L03228        real zr                   ! zenith angle
L03229        real xlat
L03230        real xlat_r
L03231  ! ----------------------------------------------------------------------
L03232  ! OUTPUT:
L03233  ! ----------------------------------------------------------------------
L03234        real rsg(ndm)             ! Short wave radiation at the ground
L03235        real rsw(2*ndm,nz_um)     ! Short wave radiation at the walls
L03236  
L03237  ! ----------------------------------------------------------------------
L03238  ! LOCAL:
L03239  ! ----------------------------------------------------------------------
L03240        integer id,iz,jz
L03241        real aae,aaw,bbb,phix,rd,rtot,wsd
L03242        
L03243  ! ----------------------------------------------------------------------
L03244  ! END VARIABLES DEFINITIONS
L03245  ! ----------------------------------------------------------------------
L03246  
L03247           xlat_r=xlat*pi/180
L03248  
L03249          if(swddir.eq.0.or.sin(zr).eq.1)then
L03250             do id=1,nd
L03251               rsg(id)=0.
L03252               do iz=1,nz_u
L03253                 rsw(2*id-1,iz)=0.
L03254                 rsw(2*id,iz)=0.
L03255              enddo
L03256           enddo
L03257          else
L03258  !test              
L03259  
L03260          if(abs(sin(zr)).gt.1.e-10)then
L03261            if(cos(deltar)*sin(ah)/sin(zr).ge.1)then
L03262             bbb=pi/2.
L03263            elseif(cos(deltar)*sin(ah)/sin(zr).le.-1)then
L03264             bbb=-pi/2.
L03265            else
L03266             bbb=asin(cos(deltar)*sin(ah)/sin(zr))                !
L03267             if(sin(deltar).lt.(cos(zr)*sin(xlat_r)))then         !
L03268             bbb=pi-bbb                                           !
L03269            endif
L03270            endif
L03271           else
L03272            if(cos(deltar)*sin(ah).ge.0)then
L03273             bbb=pi/2.
L03274            elseif(cos(deltar)*sin(ah).lt.0)then
L03275             bbb=-pi/2.
L03276            endif
L03277           endif
L03278          phix=zr
L03279             
L03280           do id=1,nd
L03281           
L03282              rsg(id)=0.
L03283  
L03284              aae=bbb-drst(id)
L03285              aaw=bbb-drst(id)+pi
L03286  
L03287              do iz=1,nz_u
L03288                 rsw(2*id-1,iz)=0.
L03289                 rsw(2*id,iz)=0.
L03290              if(pb(iz+1).gt.0.)then
L03291                 do jz=1,nz_u
L03292                  if(abs(sin(aae)).gt.1.e-10)then
L03293                    call shade_wall(z(iz),z(iz+1),z(jz+1),phix,aae,   &
L03294                        ws(id),rd)
L03295                    rsw(2*id-1,iz)=rsw(2*id-1,iz)+swddir*rd*ss(jz+1)/pb(iz+1)
L03296                  endif
L03297  
L03298                  if(abs(sin(aaw)).gt.1.e-10)then
L03299                    call shade_wall(z(iz),z(iz+1),z(jz+1),phix,aaw,   &
L03300                        ws(id),rd)
L03301                    rsw(2*id,iz)=rsw(2*id,iz)+swddir*rd*ss(jz+1)/pb(iz+1)
L03302                  endif
L03303                 enddo
L03304              endif
L03305              enddo
L03306          if(abs(sin(aae)).gt.1.e-10)then
L03307              wsd=abs(ws(id)/sin(aae))
L03308  
L03309              do jz=1,nz_u
L03310                 rd=max(0.,wsd-z(jz+1)*tan(phix))
L03311                 rsg(id)=rsg(id)+swddir*rd*ss(jz+1)/wsd
L03312              enddo
L03313              rtot=0.
L03314  
L03315              do iz=1,nz_u
L03316                 rtot=rtot+(rsw(2*id,iz)+rsw(2*id-1,iz))*            &
L03317                           (z(iz+1)-z(iz))
L03318              enddo
L03319              rtot=rtot+rsg(id)*ws(id)
L03320          else
L03321              rsg(id)=swddir
L03322          endif
L03323  
L03324  
L03325              
L03326           enddo
L03327        endif
L03328           
L03329        return
L03330        end subroutine shadow_mas
```

> 讲解：直射阴影：由太阳几何（bbb=太阳方位的几何式，含象限修正）与街道方向 drst 求夹角 aa e/aa w；对每个高度层逐「遮挡层」调 shade_wall 算墙面受照比 rd，按 ss(jz+1)/pb(iz+1) 概率加权累加；地面受照用 wsd=ws/sin(aae) 的投影长度减去建筑遮挡 rd=max(0, wsd−z·tan(phix))。swddir=0（阴天/夜间）全零出口。

<!-- code_extract code_extract.py v1.2
source: phys/module_sf_bep_bem.F
ranges: L3339-L3389
file_lines: 5706
file_md5: 8d13861f088e806d2558dd37e31126f2
display: line-numbered (strip L-prefix and !file: line to restore)
range_md5: 0965ba89590bd80dd84804911c794452
seg_lines: 51
label: subroutine shade_wall
-->

```fortran
!file: phys/module_sf_bep_bem.F    L3339-L3389    (subroutine shade_wall)
L03339        subroutine shade_wall(z1,z2,hu,phix,aa,ws,rd)
L03340  
L03341  ! ----------------------------------------------------------------------
L03342  ! This routine computes the effects of a shadow induced by a building of 
L03343  ! height hu, on a portion of wall between z1 and z2. See equation A10, 
L03344  ! and correction described below formula A11, and figure A1. Basically rd
L03345  ! is the ratio between the horizontal surface illuminated and the portion
L03346  ! of wall. Referring to figure A1, multiplying radiation flux density on 
L03347  ! a horizontal surface (rs) by x1-x2 we have the radiation energy per 
L03348  ! unit time. Dividing this by z2-z1, we obtain the radiation flux 
L03349  ! density reaching the portion of the wall between z2 and z1 
L03350  ! (everything is assumed in 2D)
L03351  ! ----------------------------------------------------------------------
L03352  
L03353        implicit none
L03354        
L03355  ! ----------------------------------------------------------------------
L03356  ! INPUT:
L03357  ! ----------------------------------------------------------------------
L03358        real aa                   ! Angle between the sun direction and the face of the wall (A12)
L03359        real hu                   ! Height of the building that generates the shadow
L03360        real phix                 ! Solar zenith angle
L03361        real ws                   ! Width of the street
L03362        real z1                   ! Height of the level z(iz)
L03363        real z2                   ! Height of the level z(iz+1)
L03364  
L03365  ! ----------------------------------------------------------------------
L03366  ! OUTPUT:
L03367  ! ----------------------------------------------------------------------
L03368        real rd                   ! Ratio between (x1-x2)/(z2-z1), see Fig. 1A. 
L03369                                  ! Multiplying rd by rs (radiation flux 
L03370                                  ! density on a horizontal surface) gives 
L03371                                  ! the radiation flux density on the 
L03372                                  ! portion of wall between z1 and z2. 
L03373  ! ----------------------------------------------------------------------
L03374  ! LOCAL:
L03375  ! ----------------------------------------------------------------------
L03376        real x1,x2                ! x1,x2 see Fig. A1.
L03377  
L03378  ! ----------------------------------------------------------------------
L03379  ! END VARIABLES DEFINITIONS
L03380  ! ----------------------------------------------------------------------
L03381  
L03382        x1=min((hu-z1)*tan(phix),max(0.,ws/sin(aa)))
L03383        
L03384        x2=max((hu-z2)*tan(phix),0.)
L03385  
L03386        rd=max(0.,sin(aa)*(max(0.,x1-x2))/(z2-z1))
L03387        
L03388        return
L03389        end subroutine shade_wall
```

> 讲解：BLM 论文式 A10–A11 的 2D 几何：x1=min((hu−z1)·tan(天顶角), ws/sin(aa))、x2=(hu−z2)·tan(天顶角)，rd=sin(aa)·max(0, x1−x2)/(z2−z1)——「水平受照面能量→墙面通量密度」的转换比，论文配图 A1。

<!-- code_extract code_extract.py v1.2
source: phys/module_sf_bep_bem.F
ranges: L3394-L3545
file_lines: 5706
file_md5: 8d13861f088e806d2558dd37e31126f2
display: line-numbered (strip L-prefix and !file: line to restore)
range_md5: 7ad0cf8f6cba41fd9c535a2280c6cce9
seg_lines: 152
label: subroutine long_rad
-->

```fortran
!file: phys/module_sf_bep_bem.F    L3394-L3545    (subroutine long_rad)
L03394        subroutine long_rad(iurb,nz_u,id,emw,emg,emwin,pwin,twlev,&
L03395                           fwg,fww,fgw,fsw,fsg,tg_av,tw,rlg,rlw,rl,pb)
L03396  
L03397  ! ----------------------------------------------------------------------
L03398  ! This routine computes the effects of the reflections of long-wave 
L03399  ! radiation in the street canyon by solving the system 
L03400  ! of 2*nz_u+1 eqn. in 2*nz_u+1
L03401  ! unkonwn defined in A4, A5 and A6 of the paper (pages 295 and 296).
L03402  ! The system is solved by solving A X= B,
L03403  ! with A matrix B vector, and X solution. 
L03404  ! ----------------------------------------------------------------------
L03405  
L03406        implicit none
L03407  
L03408    
L03409        
L03410  ! ----------------------------------------------------------------------
L03411  ! INPUT:
L03412  ! ----------------------------------------------------------------------
L03413        real emg                        ! Emissivity of ground for the current urban class
L03414        real emw                        ! Emissivity of wall for the current urban class
L03415        real fgw(nz_um,ndm,nurbm)       ! View factors from ground to wall
L03416        real fsg(ndm,nurbm)             ! View factors from sky to ground
L03417        real fsw(nz_um,ndm,nurbm)       ! View factors from sky to wall
L03418        real fwg(nz_um,ndm,nurbm)       ! View factors from wall to ground
L03419        real fww(nz_um,nz_um,ndm,nurbm) ! View factors from wall to wall
L03420        integer id                      ! Current street direction
L03421        integer iurb                    ! Current urban class
L03422        integer nz_u                    ! Number of layer in the urban grid
L03423        real pb(nz_um)                  ! Probability to have a building with an height equal
L03424        real rl                         ! Downward flux of the longwave radiation
L03425        real tg_av(ndm)               ! Temperature in each layer of the ground [K]
L03426        real tw(2*ndm,nz_um)            ! Temperature in each layer of the wall [K]
L03427  !
L03428  !New Variables for BEM
L03429  !
L03430        real twlev(2*ndm,nz_um)         ! Window temperature in BEM [K]
L03431        real emwin                      ! Emissivity of windows
L03432        real pwin                       ! Coverage area fraction of windows in the walls of the buildings (BEM)
L03433        
L03434  
L03435  ! ----------------------------------------------------------------------
L03436  ! OUTPUT:
L03437  ! ----------------------------------------------------------------------
L03438        real rlg(ndm)                   ! Long wave radiation at the ground
L03439        real rlw(2*ndm,nz_um)           ! Long wave radiation at the walls
L03440  
L03441  ! ----------------------------------------------------------------------
L03442  ! LOCAL:
L03443  ! ----------------------------------------------------------------------
L03444        integer i,j
L03445        real aaa(2*nz_um+1,2*nz_um+1)   ! terms of the matrix
L03446        real bbb(2*nz_um+1)             ! terms of the vector
L03447  
L03448  ! ----------------------------------------------------------------------
L03449  ! END VARIABLES DEFINITIONS
L03450  ! ----------------------------------------------------------------------
L03451  
L03452  
L03453  ! west wall
L03454         
L03455        do i=1,nz_u
L03456          
L03457          do j=1,nz_u
L03458           aaa(i,j)=0.
L03459          enddo
L03460          
L03461          aaa(i,i)=1.        
L03462         
L03463          do j=nz_u+1,2*nz_u
L03464           aaa(i,j)=-(1.-emw*(1.-pwin)-emwin*pwin)* &
L03465                    fww(j-nz_u,i,id,iurb)*pb(j-nz_u+1)
L03466          enddo
L03467          
L03468  !!      aaa(i,2*nz_u+1)=-(1.-emg)*fgw(i,id,iurb)*pb(i+1)
L03469          aaa(i,2*nz_u+1)=-(1.-emg)*fgw(i,id,iurb)
L03470          
L03471          bbb(i)=fsw(i,id,iurb)*rl+emg*fgw(i,id,iurb)*sigma*tg_av(id)**4
L03472          do j=1,nz_u
L03473             bbb(i)=bbb(i)+pb(j+1)*sigma*fww(j,i,id,iurb)* &
L03474                   (emw*(1.-pwin)*tw(2*id,j)**4+emwin*pwin*twlev(2*id,j)**4)+ &
L03475                   fww(j,i,id,iurb)*rl*(1.-pb(j+1))
L03476          enddo
L03477          
L03478         enddo
L03479         
L03480  ! east wall
L03481  
L03482         do i=1+nz_u,2*nz_u
L03483          
L03484          do j=1,nz_u
L03485           aaa(i,j)=-(1.-emw*(1.-pwin)-emwin*pwin)*fww(j,i-nz_u,id,iurb)*pb(j+1)
L03486          enddo
L03487          
L03488          do j=1+nz_u,2*nz_u
L03489           aaa(i,j)=0.
L03490          enddo
L03491          
L03492          aaa(i,i)=1.
L03493          
L03494  !!      aaa(i,2*nz_u+1)=-(1.-emg)*fgw(i-nz_u,id,iurb)*pb(i-nz_u+1)
L03495          aaa(i,2*nz_u+1)=-(1.-emg)*fgw(i-nz_u,id,iurb)
L03496          
L03497          bbb(i)=fsw(i-nz_u,id,iurb)*rl+  &     
L03498                 emg*fgw(i-nz_u,id,iurb)*sigma*tg_av(id)**4
L03499  
L03500          do j=1,nz_u
L03501           bbb(i)=bbb(i)+pb(j+1)*sigma*fww(j,i-nz_u,id,iurb)*  &   
L03502                  (emw*(1.-pwin)*tw(2*id-1,j)**4+emwin*pwin*twlev(2*id-1,j)**4)+&   
L03503                  fww(j,i-nz_u,id,iurb)*rl*(1.-pb(j+1))
L03504          enddo
L03505         
L03506         enddo
L03507  
L03508  ! ground
L03509         do j=1,nz_u
L03510          aaa(2*nz_u+1,j)=-(1.-emw*(1.-pwin)-emwin*pwin)* &
L03511                           fwg(j,id,iurb)*pb(j+1)
L03512         enddo
L03513         
L03514         do j=nz_u+1,2*nz_u
L03515          aaa(2*nz_u+1,j)=-(1.-emw*(1.-pwin)-emwin*pwin)* &
L03516                           fwg(j-nz_u,id,iurb)*pb(j-nz_u+1)
L03517         enddo
L03518         
L03519         aaa(2*nz_u+1,2*nz_u+1)=1.
L03520         
L03521         bbb(2*nz_u+1)=fsg(id,iurb)*rl
L03522         
L03523         do i=1,nz_u
L03524          bbb(2*nz_u+1)=bbb(2*nz_u+1)+sigma*fwg(i,id,iurb)*pb(i+1)*         &
L03525                        (emw*(1.-pwin)*(tw(2*id-1,i)**4+tw(2*id,i)**4)+     &
L03526                        emwin*pwin*(twlev(2*id-1,i)**4+twlev(2*id,i)**4))+  &
L03527                        2.*fwg(i,id,iurb)*(1.-pb(i+1))*rl                  
L03528         enddo
L03529     
L03530  
L03531       
L03532         call gaussj(aaa,2*nz_u+1,bbb,2*nz_um+1)
L03533  
L03534         do i=1,nz_u
L03535          rlw(2*id-1,i)=bbb(i)
L03536         enddo
L03537         
L03538         do i=nz_u+1,2*nz_u
L03539          rlw(2*id,i-nz_u)=bbb(i)
L03540         enddo
L03541         
L03542         rlg(id)=bbb(2*nz_u+1)
L03543    
L03544         return
L03545         end subroutine long_rad
```

> 讲解：街道峡谷长波**多次反射**：2·nz+1 元非线性方程组（墙面 i 的辐射平衡：自身发射+反射入射）线性化后用 gaussj 解；窗户按 pwin 混进发射率（emw(1−pwin)+emwin·pwin）与 T⁴ 源项；注释行展示了一个已修正的 bug（fgw 项曾误乘 pb）。输出 rlg/rlw 各面接收的长波。

<!-- code_extract code_extract.py v1.2
source: phys/module_sf_bep_bem.F
ranges: L3551-L3663
file_lines: 5706
file_md5: 8d13861f088e806d2558dd37e31126f2
display: line-numbered (strip L-prefix and !file: line to restore)
range_md5: 78352eb947e1ca99a019c0bd381b8c05
seg_lines: 113
label: subroutine short_rad_dd
-->

```fortran
!file: phys/module_sf_bep_bem.F    L3551-L3663    (subroutine short_rad_dd)
L03551        subroutine short_rad_dd(iurb,nz_u,id,albw,                        & 
L03552                             albg,rsdif,fwg,fww,fgw,fsw,fsg,rsg,rsw,pb)
L03553  
L03554  ! ----------------------------------------------------------------------
L03555  ! This routine computes the effects of the reflections of short-wave 
L03556  ! (solar) radiation in the street canyon by solving the system 
L03557  ! of 2*nz_u+1 eqn. in 2*nz_u+1
L03558  ! unkonwn defined in A4, A5 and A6 of the paper (pages 295 and 296).
L03559  ! The system is solved by solving A X= B,
L03560  ! with A matrix B vector, and X solution. 
L03561  ! ----------------------------------------------------------------------
L03562  
L03563        implicit none
L03564  
L03565    
L03566        
L03567  ! ----------------------------------------------------------------------
L03568  ! INPUT:
L03569  ! ----------------------------------------------------------------------
L03570        real albg                 ! Albedo of the ground for the current urban class
L03571        real albw                 ! Albedo of the wall for the current urban class
L03572        real rsdif                ! diffused short wave radiation
L03573        real fgw(nz_um,ndm,nurbm)       ! View factors from ground to wall
L03574        real fwg(nz_um,ndm,nurbm)       ! View factors from wall to ground
L03575        real fww(nz_um,nz_um,ndm,nurbm) ! View factors from wall to wall
L03576        real fsg(ndm,nurbm)             ! View factors from sky to ground
L03577        real fsw(nz_um,ndm,nurbm)       ! View factors from sky to wall
L03578        integer id                ! current street direction 
L03579        integer iurb              ! current urban class
L03580        integer nz_u              ! Number of layer in the urban grid
L03581        real pb(nz_um)          ! probability to have a building with an height equal
L03582  
L03583  ! ----------------------------------------------------------------------
L03584  ! OUTPUT:
L03585  ! ----------------------------------------------------------------------
L03586        real rsg(ndm)             ! Short wave radiation at the ground
L03587        real rsw(2*ndm,nz_um)     ! Short wave radiation at the walls
L03588  
L03589  ! ----------------------------------------------------------------------
L03590  ! LOCAL:
L03591  ! ----------------------------------------------------------------------
L03592        integer i,j
L03593        real aaa(2*nz_um+1,2*nz_um+1)  ! terms of the matrix
L03594        real bbb(2*nz_um+1)            ! terms of the vector
L03595  
L03596  ! ----------------------------------------------------------------------
L03597  ! END VARIABLES DEFINITIONS
L03598  ! ----------------------------------------------------------------------
L03599  
L03600        
L03601  ! west wall
L03602         
L03603           
L03604          do i=1,nz_u
L03605           do j=1,nz_u
L03606              aaa(i,j)=0.
L03607           enddo
L03608  
L03609           aaa(i,i)=1.
L03610  
L03611           do j=nz_u+1,2*nz_u
L03612              aaa(i,j)=-albw*fww(j-nz_u,i,id,iurb)*pb(j-nz_u+1)
L03613           enddo
L03614  
L03615           aaa(i,2*nz_u+1)=-albg*fgw(i,id,iurb)
L03616           bbb(i)=rsw(2*id-1,i)+fsw(i,id,iurb)*rsdif
L03617  
L03618        enddo
L03619   
L03620  ! east wall
L03621         do i=1+nz_u,2*nz_u
L03622           do j=1,nz_u
L03623              aaa(i,j)=-albw*fww(j,i-nz_u,id,iurb)*pb(j+1)
L03624           enddo
L03625  
L03626           do j=1+nz_u,2*nz_u
L03627              aaa(i,j)=0.
L03628           enddo
L03629  
L03630          aaa(i,i)=1.
L03631          aaa(i,2*nz_u+1)=-albg*fgw(i-nz_u,id,iurb)
L03632          bbb(i)=rsw(2*id,i-nz_u)+fsw(i-nz_u,id,iurb)*rsdif
L03633  
L03634        enddo
L03635  
L03636  
L03637  ! ground
L03638        do j=1,nz_u
L03639           aaa(2*nz_u+1,j)=-albw*fwg(j,id,iurb)*pb(j+1)
L03640        enddo
L03641  
L03642        do j=nz_u+1,2*nz_u
L03643           aaa(2*nz_u+1,j)=-albw*fwg(j-nz_u,id,iurb)*pb(j-nz_u+1)
L03644        enddo
L03645  
L03646        aaa(2*nz_u+1,2*nz_u+1)=1.
L03647        bbb(2*nz_u+1)=rsg(id)+fsg(id,iurb)*rsdif
L03648  
L03649        call gaussj(aaa,2*nz_u+1,bbb,2*nz_um+1)
L03650  
L03651        do i=1,nz_u
L03652           rsw(2*id-1,i)=bbb(i)
L03653        enddo
L03654  
L03655        do i=nz_u+1,2*nz_u
L03656           rsw(2*id,i-nz_u)=bbb(i)
L03657        enddo
L03658  
L03659        rsg(id)=bbb(2*nz_u+1)
L03660  
L03661         
L03662        return
L03663        end subroutine short_rad_dd
```

> 讲解：短波漫射的同一套线性系统（反射率代替发射率）；直射部分不进此系统——shadow_mas 已按几何直接算。两系统共用 gaussj。

<!-- code_extract code_extract.py v1.2
source: phys/module_sf_bep_bem.F
ranges: L3670-L3772
file_lines: 5706
file_md5: 8d13861f088e806d2558dd37e31126f2
display: line-numbered (strip L-prefix and !file: line to restore)
range_md5: f1a48fe0ebebf89ee0d9b3bbdb55f8f5
seg_lines: 103
label: subroutine gaussj
-->

```fortran
!file: phys/module_sf_bep_bem.F    L3670-L3772    (subroutine gaussj)
L03670        subroutine gaussj(a,n,b,np)
L03671  
L03672  ! ----------------------------------------------------------------------
L03673  ! This routine solve a linear system of n equations of the form
L03674  !              A X = B
L03675  !  where  A is a matrix a(i,j)
L03676  !         B a vector and X the solution
L03677  ! In output b is replaced by the solution     
L03678  ! ----------------------------------------------------------------------
L03679  
L03680        implicit none
L03681  
L03682  ! ----------------------------------------------------------------------
L03683  ! INPUT:
L03684  ! ----------------------------------------------------------------------
L03685        integer np
L03686        real a(np,np)
L03687  
L03688  ! ----------------------------------------------------------------------
L03689  ! OUTPUT:
L03690  ! ----------------------------------------------------------------------
L03691        real b(np)
L03692  
L03693  ! ----------------------------------------------------------------------
L03694  ! LOCAL:
L03695  ! ----------------------------------------------------------------------
L03696        integer nmax
L03697        parameter (nmax=150)
L03698  
L03699        real big,dum
L03700        integer i,icol,irow
L03701        integer j,k,l,ll,n
L03702        integer ipiv(nmax)
L03703        real pivinv
L03704  
L03705  ! ----------------------------------------------------------------------
L03706  ! END VARIABLES DEFINITIONS
L03707  ! ----------------------------------------------------------------------
L03708         
L03709        do j=1,n
L03710           ipiv(j)=0.
L03711        enddo
L03712         
L03713        do i=1,n
L03714           big=0.
L03715           do j=1,n
L03716              if(ipiv(j).ne.1)then
L03717                 do k=1,n
L03718                    if(ipiv(k).eq.0)then
L03719                       if(abs(a(j,k)).ge.big)then
L03720                          big=abs(a(j,k))
L03721                          irow=j
L03722                          icol=k
L03723                       endif
L03724                    elseif(ipiv(k).gt.1)then
L03725                       FATAL_ERROR('singular matrix in gaussj')
L03726                    endif
L03727                 enddo
L03728              endif
L03729           enddo
L03730           
L03731           ipiv(icol)=ipiv(icol)+1
L03732           
L03733           if(irow.ne.icol)then
L03734              do l=1,n
L03735                 dum=a(irow,l)
L03736                 a(irow,l)=a(icol,l)
L03737                 a(icol,l)=dum
L03738              enddo
L03739              
L03740              dum=b(irow)
L03741              b(irow)=b(icol)
L03742              b(icol)=dum
L03743            
L03744           endif
L03745           
L03746           if(a(icol,icol).eq.0) FATAL_ERROR('singular matrix in gaussj')
L03747           
L03748           pivinv=1./a(icol,icol)
L03749           a(icol,icol)=1
L03750           
L03751           do l=1,n
L03752              a(icol,l)=a(icol,l)*pivinv
L03753           enddo
L03754           
L03755           b(icol)=b(icol)*pivinv
L03756           
L03757           do ll=1,n
L03758              if(ll.ne.icol)then
L03759                 dum=a(ll,icol)
L03760                 a(ll,icol)=0.
L03761                 do l=1,n
L03762                    a(ll,l)=a(ll,l)-a(icol,l)*dum
L03763                 enddo
L03764                 
L03765                 b(ll)=b(ll)-b(icol)*dum
L03766                 
L03767              endif
L03768           enddo
L03769        enddo
L03770        
L03771        return
L03772        end subroutine gaussj
```

> 讲解：Numerical Recipes 的全主元 Gauss–Jordan 消元（nmax=150 上限对应 2·nz_um+1=37），奇异矩阵直接 FATAL_ERROR。BEP 每步每方向每点都要解两个 37×37 线性系统——城市冠层的计算量大头之一（论文 2 三域 1 km 时注意性能）。

## 四、导热与水分求解器

<!-- code_extract code_extract.py v1.2
source: phys/module_sf_bep_bem.F
ranges: L3779-L3857
file_lines: 5706
file_md5: 8d13861f088e806d2558dd37e31126f2
display: line-numbered (strip L-prefix and !file: line to restore)
range_md5: 4857a18ca3c8c96067d2208829b83c40
seg_lines: 79
label: subroutine soil_moist
-->

```fortran
!file: phys/module_sf_bep_bem.F    L3779-L3857    (subroutine soil_moist)
L03779        subroutine soil_moist(nz,dz,qv,dt,lf,d,k,rainbl,drain,irri_now)
L03780  
L03781  ! ----------------------------------------------------------------------
L03782  ! This routine solves the Fourier diffusion equation for heat in 
L03783  ! the material (wall, roof, or ground). Resolution is done implicitely.
L03784  ! Boundary conditions are: 
L03785  ! - fixed temperature at the interior
L03786  ! - energy budget at the surface
L03787  ! ----------------------------------------------------------------------
L03788  
L03789        implicit none
L03790  
L03791  
L03792  
L03793  ! ----------------------------------------------------------------------
L03794  ! INPUT:
L03795  ! ----------------------------------------------------------------------
L03796        integer nz                ! Number of layers
L03797        real dt                   ! Time step
L03798        real lf                   ! Latent heat flux at the surface
L03799        real qv(nz)               ! Moisture in each layer [K]
L03800        real dz(nz)               ! Layer sizes [m]
L03801        real rainbl               ! Rainfall [mm]
L03802        real d(nz)                ! Soil water diffusivity
L03803        real k(nz)                ! Hydraulic conductivity
L03804        real gr                   ! Dummy variable 
L03805        real drain
L03806        real irri_now
L03807  ! ----------------------------------------------------------------------
L03808  ! OUTPUT:
L03809  ! ----------------------------------------------------------------------
L03810    
L03811  
L03812  ! ----------------------------------------------------------------------
L03813  ! LOCAL:
L03814  ! ----------------------------------------------------------------------
L03815        integer iz
L03816        real a(nz,3)
L03817        real alpha
L03818        real c(nz)
L03819        real cddz(nz+2)
L03820        real dw     !water density Kg/m3
L03821        parameter(dw=1000.)
L03822  !----------------------------------------------------------------------
L03823  ! END VARIABLES DEFINITIONS
L03824  ! ----------------------------------------------------------------------
L03825  
L03826        alpha=rainbl/(dw*dt)+lf/latent/dw+irri_now/dw
L03827        cddz(1)=0.
L03828        do iz=2,nz
L03829           cddz(iz)=2.*d(iz)/(dz(iz)+dz(iz-1))
L03830        enddo
L03831        do iz=1,4
L03832           a(iz,1)=0.
L03833           a(iz,2)=1.
L03834           a(iz,3)=0.
L03835           c(iz)=qv(iz)
L03836        enddo
L03837        do iz=6,nz-1
L03838           a(iz,1)=-cddz(iz)*dt/dz(iz)
L03839           a(iz,2)=1.+dt*(cddz(iz)+cddz(iz+1))/dz(iz)
L03840           a(iz,3)=-cddz(iz+1)*dt/dz(iz)
L03841           c(iz)=qv(iz)+dt*(k(iz+1)-k(iz))/dz(iz)
L03842        enddo
L03843           a(5,1)=0.
L03844           a(5,2)=1.+dt*(cddz(5+1))/dz(5)
L03845           a(5,3)=-cddz(5+1)*dt/dz(5)
L03846           c(5)=qv(5)+dt*(k(5+1)-drain)/dz(5)
L03847        
L03848  
L03849        a(nz,1)=-dt*cddz(nz)/dz(nz)
L03850        a(nz,2)=1.+dt*cddz(nz)/dz(nz)
L03851        a(nz,3)=0.
L03852        c(nz)=qv(nz)+dt*alpha/dz(nz)-dt*k(nz-1)/dz(nz)
L03853  
L03854        call invert(nz,a,c,qv)
L03855  
L03856        return
L03857        end subroutine soil_moist
```

> 讲解：土壤含水量隐式扩散（绿屋顶用）：源项 alpha=降雨/(ρ_w·dt)+蒸发/(L·ρ_w)+灌溉/ρ_w；第 5 层为排水层（k 换 drain）；第 6 层起为 Richards 型扩散项 + 对流项 (k(iz+1)−k(iz))/dz；前 4 层恒等（屋顶建材不含水）；invert 解三对角。

<!-- code_extract code_extract.py v1.2
source: phys/module_sf_bep_bem.F
ranges: L3866-L3959
file_lines: 5706
file_md5: 8d13861f088e806d2558dd37e31126f2
display: line-numbered (strip L-prefix and !file: line to restore)
range_md5: 6c38a7407931a63833bbeec086ad4065
seg_lines: 94
label: subroutine soil_temp_veg
-->

```fortran
!file: phys/module_sf_bep_bem.F    L3866-L3959    (subroutine soil_temp_veg)
L03866        subroutine soil_temp_veg(heflro,nz,dz,temp,pt,ala,cs,                       &
L03867                            rs,rl,press,dt,em,alb,rt,sf,lf,gf,pv_frac_roof,tpv)
L03868  
L03869  ! ----------------------------------------------------------------------
L03870  ! This routine solves the Fourier diffusion equation for heat in 
L03871  ! the material (wall, roof, or ground). Resolution is done implicitely.
L03872  ! Boundary conditions are: 
L03873  ! - fixed temperature at the interior
L03874  ! - energy budget at the surface
L03875  ! ----------------------------------------------------------------------
L03876  
L03877        implicit none
L03878  
L03879       
L03880                  
L03881  ! ----------------------------------------------------------------------
L03882  ! INPUT:
L03883  ! ----------------------------------------------------------------------
L03884        integer nz                ! Number of layers
L03885        real ala(nz)              ! Thermal diffusivity in each layers [m^2 s^-1] 
L03886        real alb                  ! Albedo of the surface
L03887        real cs(nz)               ! Specific heat of the material [J m^3 K^-1]
L03888        real dt                   ! Time step
L03889        real em                   ! Emissivity of the surface
L03890        real press                ! Pressure at ground level
L03891        real rl                   ! Downward flux of the longwave radiation
L03892        real rs                   ! Solar radiation
L03893        real sf                   ! Sensible heat flux at the surface
L03894        real lf                   ! Latent heat flux at the surface
L03895        real temp(nz)             ! Temperature in each layer [K]
L03896        real dz(nz)               ! Layer sizes [m]
L03897        real heflro                ! Heat flux between roof and green roof 
L03898        real rs_eff
L03899        real rl_eff
L03900        real tpv
L03901        real pv_frac_roof
L03902  ! ----------------------------------------------------------------------
L03903  ! OUTPUT:
L03904  ! ----------------------------------------------------------------------
L03905        real gf                   ! Heat flux transferred from the surface toward the interior
L03906        real pt                   ! Potential temperature at the surface
L03907        real rt                   ! Total radiation at the surface (solar+incoming long+outgoing long)
L03908  
L03909  ! ----------------------------------------------------------------------
L03910  ! LOCAL:
L03911  ! ----------------------------------------------------------------------
L03912        integer iz
L03913        real a(nz,3)
L03914        real alpha
L03915        real c(nz)
L03916        real cddz(nz+2)
L03917        real tsig
L03918  
L03919  ! ----------------------------------------------------------------------
L03920  ! END VARIABLES DEFINITIONS
L03921  ! ----------------------------------------------------------------------
L03922       if(pv_frac_roof.gt.0)then 
L03923       rl_eff=(1-pv_frac_roof)*em*rl+em*sigma*tpv**4*pv_frac_roof
L03924        rs_eff=(1.-pv_frac_roof)*rs
L03925       else
L03926        rl_eff=em*rl
L03927        rs_eff=rs
L03928       endif
L03929        tsig=temp(nz)
L03930        alpha=(1.-alb)*rs_eff+rl_eff-em*sigma*(tsig**4)+sf+lf
L03931        cddz(1)=ala(1)/dz(1)
L03932        do iz=2,nz
L03933           cddz(iz)=2.*ala(iz)/(dz(iz)+dz(iz-1))
L03934        enddo
L03935        
L03936        a(1,1)=0.
L03937        a(1,2)=1.
L03938        a(1,3)=0.
L03939        c(1)=temp(1)-heflro*dt/dz(1)
L03940        do iz=2,nz-1
L03941           a(iz,1)=-cddz(iz)*dt/dz(iz)
L03942           a(iz,2)=1.+dt*(cddz(iz)+cddz(iz+1))/dz(iz)          
L03943           a(iz,3)=-cddz(iz+1)*dt/dz(iz)
L03944           c(iz)=temp(iz)
L03945        enddo          
L03946        a(nz,1)=-dt*cddz(nz)/dz(nz)
L03947        a(nz,2)=1.+dt*cddz(nz)/dz(nz)
L03948        a(nz,3)=0.
L03949        c(nz)=temp(nz)+dt*alpha/cs(nz)/dz(nz) 
L03950        
L03951        call invert(nz,a,c,temp)
L03952  
L03953        pt=temp(nz)*(press/1.e+5)**(-rcp_u)
L03954  
L03955        rt=(1.-alb)*rs_eff+rl_eff-em*sigma*(tsig**4.)
L03956                          
L03957        gf=(1.-alb)*rs_eff+rl_eff-em*sigma*(tsig**4.)+sf                                   
L03958        return
L03959        end subroutine soil_temp_veg
```

> 讲解：绿屋顶导热（soil_temp 的植被/PV 扩展）：PV 面板占比 pv_frac_roof 调整有效辐射（rl_eff=(1−pv)·em·rl+em·σ·T_pv⁴·pv——面板当发射体；rs_eff=(1−pv)·rs）；第 1 层加与结构屋顶的耦合热流 heflro（来自 roof_temp_veg 的 hfgroof）；表面能量收支作上边界、深层固定温度作下边界。

<!-- code_extract code_extract.py v1.2
source: phys/module_sf_bep_bem.F
ranges: L3964-L4049
file_lines: 5706
file_md5: 8d13861f088e806d2558dd37e31126f2
display: line-numbered (strip L-prefix and !file: line to restore)
range_md5: 7cec6fa0a0a548e0065f47b060fa1201
seg_lines: 86
label: subroutine soil_temp
-->

```fortran
!file: phys/module_sf_bep_bem.F    L3964-L4049    (subroutine soil_temp)
L03964        subroutine soil_temp(nz,dz,temp,pt,ala,cs,                       &
L03965                            rs,rl,press,dt,em,alb,rt,sf,lf,gf)
L03966  
L03967  ! ----------------------------------------------------------------------
L03968  ! This routine solves the Fourier diffusion equation for heat in 
L03969  ! the material (wall, roof, or ground). Resolution is done implicitely.
L03970  ! Boundary conditions are: 
L03971  ! - fixed temperature at the interior
L03972  ! - energy budget at the surface
L03973  ! ----------------------------------------------------------------------
L03974  
L03975        implicit none
L03976  
L03977       
L03978                  
L03979  ! ----------------------------------------------------------------------
L03980  ! INPUT:
L03981  ! ----------------------------------------------------------------------
L03982        integer nz                ! Number of layers
L03983        real ala(nz)              ! Thermal diffusivity in each layers [m^2 s^-1] 
L03984        real alb                  ! Albedo of the surface
L03985        real cs(nz)               ! Specific heat of the material [J m^3 K^-1]
L03986        real dt                   ! Time step
L03987        real em                   ! Emissivity of the surface
L03988        real press                ! Pressure at ground level
L03989        real rl                   ! Downward flux of the longwave radiation
L03990        real rs                   ! Solar radiation
L03991        real sf                   ! Sensible heat flux at the surface
L03992        real lf                   ! Latent heat flux at the surface
L03993        real temp(nz)             ! Temperature in each layer [K]
L03994        real dz(nz)               ! Layer sizes [m]
L03995  
L03996  ! ----------------------------------------------------------------------
L03997  ! OUTPUT:
L03998  ! ----------------------------------------------------------------------
L03999        real gf                   ! Heat flux transferred from the surface toward the interior
L04000        real pt                   ! Potential temperature at the surface
L04001        real rt                   ! Total radiation at the surface (solar+incoming long+outgoing long)
L04002  
L04003  ! ----------------------------------------------------------------------
L04004  ! LOCAL:
L04005  ! ----------------------------------------------------------------------
L04006        integer iz
L04007        real a(nz,3)
L04008        real alpha
L04009        real c(nz)
L04010        real cddz(nz+2)
L04011        real tsig
L04012  
L04013  ! ----------------------------------------------------------------------
L04014  ! END VARIABLES DEFINITIONS
L04015  ! ----------------------------------------------------------------------
L04016         
L04017        tsig=temp(nz)
L04018        alpha=(1.-alb)*rs+em*rl-em*sigma*(tsig**4)+sf+lf
L04019  ! Compute cddz=2*cd/dz  
L04020        cddz(1)=ala(1)/dz(1)
L04021        do iz=2,nz
L04022           cddz(iz)=2.*ala(iz)/(dz(iz)+dz(iz-1))
L04023        enddo
L04024        
L04025        a(1,1)=0.
L04026        a(1,2)=1.
L04027        a(1,3)=0.
L04028        c(1)=temp(1)
L04029        do iz=2,nz-1
L04030           a(iz,1)=-cddz(iz)*dt/dz(iz)
L04031           a(iz,2)=1.+dt*(cddz(iz)+cddz(iz+1))/dz(iz)          
L04032           a(iz,3)=-cddz(iz+1)*dt/dz(iz)
L04033           c(iz)=temp(iz)
L04034        enddo          
L04035        a(nz,1)=-dt*cddz(nz)/dz(nz)
L04036        a(nz,2)=1.+dt*cddz(nz)/dz(nz)
L04037        a(nz,3)=0.
L04038        c(nz)=temp(nz)+dt*alpha/cs(nz)/dz(nz) 
L04039  
L04040        
L04041        call invert(nz,a,c,temp)
L04042  
L04043        pt=temp(nz)*(press/1.e+5)**(-rcp_u)
L04044  
L04045        rt=(1.-alb)*rs+em*rl-em*sigma*(tsig**4.)
L04046                          
L04047         gf=(1.-alb)*rs+em*rl-em*sigma*(tsig**4.)+sf                                   
L04048        return
L04049        end subroutine soil_temp
```

> 讲解：通用一维 Fourier 导热求解器（墙面/路面/普通屋顶共用）：cddz=2·ala/(dz_iz+dz_iz−1) 的层间调和平均，表面层能量收支 alpha=(1−alb)·rs+em·rl−em·σ·T⁴+sf+lf 作 Neumann 条件，底层固定温度；返回位温 pt、总辐射 rt、向内热流 gf。BEP 所有固体温度演化的核心。

<!-- code_extract code_extract.py v1.2
source: phys/module_sf_bep_bem.F
ranges: L4056-L4102
file_lines: 5706
file_md5: 8d13861f088e806d2558dd37e31126f2
display: line-numbered (strip L-prefix and !file: line to restore)
range_md5: 430c0fbbda4f29d31d44e96921091d0a
seg_lines: 47
label: subroutine invert
-->

```fortran
!file: phys/module_sf_bep_bem.F    L4056-L4102    (subroutine invert)
L04056        subroutine invert(n,a,c,x)
L04057  
L04058  ! ----------------------------------------------------------------------
L04059  !        Inversion and resolution of a tridiagonal matrix
L04060  !                   A X = C
L04061  ! ----------------------------------------------------------------------
L04062  
L04063        implicit none
L04064                  
L04065  ! ----------------------------------------------------------------------
L04066  ! INPUT:
L04067  ! ----------------------------------------------------------------------
L04068         integer n
L04069         real a(n,3)              !  a(*,1) lower diagonal (Ai,i-1)
L04070                                  !  a(*,2) principal diagonal (Ai,i)
L04071                                  !  a(*,3) upper diagonal (Ai,i+1)
L04072         real c(n)
L04073  
L04074  ! ----------------------------------------------------------------------
L04075  ! OUTPUT:
L04076  ! ----------------------------------------------------------------------
L04077         real x(n)    
L04078  
L04079  ! ----------------------------------------------------------------------
L04080  ! LOCAL:
L04081  ! ----------------------------------------------------------------------
L04082         integer i
L04083  
L04084  ! ----------------------------------------------------------------------
L04085  ! END VARIABLES DEFINITIONS
L04086  ! ----------------------------------------------------------------------
L04087                       
L04088         do i=n-1,1,-1                 
L04089            c(i)=c(i)-a(i,3)*c(i+1)/a(i+1,2)
L04090            a(i,2)=a(i,2)-a(i,3)*a(i+1,1)/a(i+1,2)
L04091         enddo
L04092         
L04093         do i=2,n        
L04094            c(i)=c(i)-a(i,1)*c(i-1)/a(i-1,2)
L04095         enddo
L04096          
L04097         do i=1,n
L04098            x(i)=c(i)/a(i,2)
L04099         enddo
L04100  
L04101         return
L04102         end subroutine invert
```

> 讲解：托马斯消元（a(n,3) 三对角存储，原地破坏 a/c——与 pbl_driver 的 invert 同源不同名，与 code_09b tridiag 家族的「是否保留输入」差异一致；复用前必查）。

## 五、通量参数化

<!-- code_extract code_extract.py v1.2
source: phys/module_sf_bep_bem.F
ranges: L4108-L4199
file_lines: 5706
file_md5: 8d13861f088e806d2558dd37e31126f2
display: line-numbered (strip L-prefix and !file: line to restore)
range_md5: ce7f5d5085a17be4e859c2816daa2513
seg_lines: 92
label: subroutine flux_wall
-->

```fortran
!file: phys/module_sf_bep_bem.F    L4108-L4199    (subroutine flux_wall)
L04108        subroutine flux_wall(ua,va,pt,da,ptw,ptwin,uva,vva,uvb,vvb,  &
L04109                             sfw,sfwin,evb,drst,dt,cdrag)         
L04110         
L04111  ! ----------------------------------------------------------------------
L04112  ! This routine computes the surface sources or sinks of momentum, tke,
L04113  ! and heat from vertical surfaces (walls).   
L04114  ! ----------------------------------------------------------------------
L04115        implicit none   
L04116           
L04117  ! INPUT:
L04118  ! -----
L04119        real drst                 ! street directions for the current urban class
L04120        real da                   ! air density
L04121        real pt                   ! potential temperature
L04122        real ptw                  ! Walls potential temperatures 
L04123        real ptwin                ! Windows potential temperatures
L04124        real ua                   ! wind speed
L04125        real va                   ! wind speed
L04126        real dt                   !time step
L04127        real cdrag
L04128  ! OUTPUT:
L04129  ! ------
L04130  ! Explicit and implicit component of the momentum, temperature and TKE sources or sinks on
L04131  ! vertical surfaces (walls).
L04132  ! The fluxes can be computed as follow: Fluxes of X = A*X + B
L04133  ! Example: Momentum fluxes on vertical surfaces = uva_u * ua_u + uvb_u
L04134  
L04135        real uva                  ! U (wind component)   Vertical surfaces, A (implicit) term
L04136        real uvb                  ! U (wind component)   Vertical surfaces, B (explicit) term
L04137        real vva                  ! V (wind component)   Vertical surfaces, A (implicit) term
L04138        real vvb                  ! V (wind component)   Vertical surfaces, B (explicit) term
L04139        real tva                  ! Temperature          Vertical surfaces, A (implicit) term
L04140        real tvb                  ! Temperature          Vertical surfaces, B (explicit) term
L04141        real evb                  ! Energy (TKE)         Vertical surfaces, B (explicit) term
L04142        real sfw                  ! Surfaces fluxes from the walls
L04143        real sfwin                ! Surfaces fluxes from the windows
L04144  
L04145  ! LOCAL:
L04146  ! -----
L04147        real hc
L04148        real hcwin
L04149        real u_ort
L04150        real vett
L04151  
L04152  
L04153  ! -------------------------
L04154  ! END VARIABLES DEFINITIONS
L04155  ! -------------------------
L04156  
L04157        vett=(ua**2+va**2)**.5         
L04158           
L04159        u_ort=abs((cos(drst)*ua-sin(drst)*va))
L04160         
L04161        uva=-cdrag*u_ort/2.*cos(drst)*cos(drst)
L04162        vva=-cdrag*u_ort/2.*sin(drst)*sin(drst)
L04163           
L04164        uvb=cdrag*u_ort/2.*sin(drst)*cos(drst)*va
L04165        vvb=cdrag*u_ort/2.*sin(drst)*cos(drst)*ua         
L04166  
L04167        if (vett.lt.4.88) then   
L04168           hc=5.678*(1.09+0.23*(vett/0.3048))  
L04169        else
L04170           hc=5.678*0.53*((vett/0.3048)**0.78)
L04171        endif 
L04172  
L04173        if (hc.gt.da*cp_u/dt)then
L04174           hc=da*cp_u/dt
L04175        endif
L04176  
L04177         if (vett.lt.4.88) then
L04178            hcwin=5.678*(0.99+0.21*(vett/0.3048))
L04179         else
L04180            hcwin=5.678*0.50*((vett/0.3048)**0.78)
L04181         endif
L04182  
L04183         if (hcwin.gt.da*cp_u/dt) then
L04184             hcwin=da*cp_u/dt
L04185         endif
L04186           
L04187  !         tvb=hc*ptw/da/cp_u
L04188  !         tva=-hc/da/cp_u
L04189  !!!!!!!!!!!!!!!!!!!!
L04190  ! explicit 
L04191  
L04192        sfw=hc*(pt-ptw)
L04193        sfwin=hcwin*(pt-ptwin)  
L04194         
L04195           
L04196        evb=cdrag*(abs(u_ort)**3.)/2.
L04197                
L04198        return
L04199        end subroutine flux_wall
```

> 讲解：墙面通量：①动量——法向风 u_ort=|cos(drst)·ua−sin(drst)·va|，隐式项 uva=−cdrag·u_ort/2·cos²(drst)、uvb=cdrag·u_ort/2·sin·cos·va（正交分解的墙面拖曳，方向投影几何）；②对流换热 hc——**经验分段式**（vett<4.88 m/s 用 McAdams 型线性式 5.678·(1.09+0.23·V/0.3048)，否则湍流幂律 5.678·0.53·(V/0.3048)^0.78），上限钳 da·cp/dt（显式稳定极限）；窗户另用 hcwin（系数 0.99/0.21/0.50）；③TKE 源 evb=cdrag·|u_ort|³/2——墙面湍流产生项。

<!-- code_extract code_extract.py v1.2
source: phys/module_sf_bep_bem.F
ranges: L4204-L4400
file_lines: 5706
file_md5: 8d13861f088e806d2558dd37e31126f2
display: line-numbered (strip L-prefix and !file: line to restore)
range_md5: 32f61ed78a4ae675eda67d0d657d7a06
seg_lines: 197
label: subroutine flux_flat_ground
-->

```fortran
!file: phys/module_sf_bep_bem.F    L4204-L4400    (subroutine flux_flat_ground)
L04204        subroutine flux_flat_ground(dz,z0,ua,va,pt,pt0,ptg,                     &
L04205                            uhb,vhb,sf,ehb,da,qv,pr,rsg,qg,resg,rsveg,f1,f2,f3,f4,fh,ric,utot,gr_type)
L04206                                  
L04207  ! ----------------------------------------------------------------------
L04208  !           Calculation of the flux at the ground 
L04209  !           Formulation of Louis (Louis, 1979)       
L04210  ! ----------------------------------------------------------------------
L04211  
L04212        implicit none
L04213  
L04214        real dz                   ! first vertical level
L04215        real pt                   ! potential temperature
L04216        real pt0                  ! reference potential temperature
L04217        real ptg                  ! ground potential temperature
L04218        real ua                   ! wind speed
L04219        real va                   ! wind speed
L04220        real z0                   ! Roughness length
L04221        real da                   ! air density
L04222        real qv                   ! specific humidity
L04223        real pr                   ! pressure
L04224        real rsg                  ! solar radiation
L04225        real qg(ng_u)         ! Ground Soil Moisture
L04226  
L04227       
L04228  
L04229  ! ----------------------------------------------------------------------
L04230  ! OUTPUT:
L04231  ! ----------------------------------------------------------------------
L04232  ! Explicit component of the momentum, temperature and TKE sources or sinks on horizontal 
L04233  !  surfaces (roofs and street)
L04234  ! The fluxes can be computed as follow: Fluxes of X = B
L04235  !  Example: Momentum fluxes on horizontal surfaces =  uhb_u
L04236        real uhb                  ! U (wind component) Horizontal surfaces, B (explicit) term
L04237        real vhb                  ! V (wind component) Horizontal surfaces, B (explicit) term
L04238  !     real thb                  ! Temperature        Horizontal surfaces, B (explicit) term
L04239        real tva                  ! Temperature          Vertical surfaces, A (implicit) term
L04240        real tvb                  ! Temperature          Vertical surfaces, B (explicit) term
L04241        real ehb                  ! Energy (TKE)       Horizontal surfaces, B (explicit) term
L04242        real sf
L04243        real lf
L04244  
L04245  ! ----------------------------------------------------------------------
L04246  ! LOCAL:
L04247  ! ----------------------------------------------------------------------
L04248        real aa,ah
L04249        real z0t
L04250        real al
L04251        real buu
L04252        real c
L04253        real fbuw
L04254        real fbpt
L04255        real fh
L04256        real fm
L04257        real ric
L04258        real tstar
L04259        real qstar
L04260        real ustar
L04261        real utot
L04262        real wstar
L04263        real zz
L04264        real qvsg,qvs,es,esa,fbqq
L04265        real b,cm,ch,rr,tol
L04266        parameter(b=9.4,cm=7.4,ch=5.3,rr=0.74,tol=.001)
L04267  
L04268        real f
L04269        real f1
L04270        real f2
L04271        real f3
L04272        real f4
L04273        real ta          ! surface air temperature
L04274        real tmp                  ! ground temperature
L04275        real rsveg       ! Stomatal resistance 
L04276        real resg
L04277        real lai         ! leaf area index
L04278        real sdlim       ! radiation limit at which photosyntesis start W/m2
L04279        parameter(sdlim=100.)
L04280        real rsmin ! Minimum stomatal resistance 
L04281        real rsmax ! Maximun stomatal resistance 
L04282        real qw
L04283        parameter(qw=0.06)
L04284        real qref
L04285        parameter(qref=0.37)  
L04286        real hs
L04287        parameter(hs=36.35)
L04288   
L04289        real dzg_u(ng_u)          ! Layer sizes in the ground
L04290  
L04291        data dzg_u /0.2,0.12,0.08,0.05,0.03,0.02,0.02,0.01,0.005,0.0025/
L04292        
L04293        real gx,dzg_tot
L04294        integer gr_type,iz
L04295  ! ----------------------------------------------------------------------
L04296  ! END VARIABLES DEFINITIONS
L04297  ! ----------------------------------------------------------------------
L04298        z0t=z0/10.
L04299        if(gr_type.eq.1)then
L04300        rsmin=40.
L04301        rsmax=5000.
L04302        lai=2.
L04303        elseif(gr_type.eq.2)then
L04304        rsmin=150.
L04305        rsmax=5000.
L04306        lai=3.
L04307        endif
L04308  ! computation of the ground temperature
L04309           
L04310        utot=(ua**2.+va**2.)**.5
L04311          
L04312        
L04313  !!!! Louis formulation
L04314  !
L04315  ! compute the bulk Richardson Number
L04316  
L04317        zz=dz/2.
L04318     
L04319  !        if(tstar.lt.0.)then
L04320  !         wstar=(-ustar*tstar*g*hii/pt)**(1./3.)
L04321  !        else
L04322  !         wstar=0.
L04323  !        endif
L04324  !        
L04325  !      if (utot.le.0.7*wstar) utot=max(0.7*wstar,0.00001)
L04326  
L04327        utot=max(utot,0.01)
L04328            
L04329        ric=2.*g_u*zz*(pt-ptg)/((pt+ptg)*(utot**2))
L04330                
L04331        aa=vk/log(zz/z0)
L04332        ah=vk/log(zz/z0t)
L04333  
L04334  ! determine the parameters fm and fh for stable, neutral and unstable conditions
L04335  
L04336        if(ric.gt.0)then
L04337           fm=1/(1+0.5*b*ric)**2.
L04338           fh=fm
L04339        else
L04340           c=b*cm*aa*aa*(zz/z0)**.5
L04341           fm=1-b*ric/(1+c*(-ric)**.5)
L04342           c=b*cm*aa*ah*(zz/z0t)**.5
L04343           c=c*ch/cm
L04344           fh=1-b*ric/(1+c*(-ric)**.5)
L04345        endif
L04346        
L04347        fbuw=-aa*aa*utot*utot*fm
L04348        fbpt=-aa*ah*utot*(pt-ptg)*fh/rr
L04349        tmp=ptg*(pr/p0)**(rcp_u)-273.15 
L04350        es=6.11*(10.**(tmp*7.5/(237.7+tmp)))
L04351        qvsg=0.62197*es/(0.01*pr-0.378*es)
L04352        
L04353  
L04354        f=0.55*rsg/sdlim*2./lai
L04355        
L04356        f1=(f+rsmin/rsmax)/(1.+f)
L04357  
L04358        ta=pt*(pr/p0)**(rcp_u)-273.15
L04359        esa=6.11*(10**(ta*7.5/(237.7+ta)))
L04360        qvs=0.62197*esa/(0.01*pr-0.378*esa)
L04361  
L04362        f2= 1./(1.+hs*(qvs-qv))
L04363        f3=1.-0.0016*(25.-ta)**2.
L04364        f4=0.
L04365        dzg_tot=0.
L04366        do iz=1,ng_u
L04367         gx=(qg(iz)-qw)/(qref-qw)
L04368         if (gx.gt.1)gx=1.
L04369         if (gx.lt.0)gx=0.
L04370         f4=f4+gx*dzg_u(iz)
L04371         dzg_tot=dzg_tot+dzg_u(iz)
L04372        enddo
L04373        f4=f4/dzg_tot
L04374  
L04375        rsveg=min(rsmin/max(lai*f1*f2*f3*f4,1e-9),rsmax)
L04376        resg= rr/(aa*aa*utot*fh)
L04377  
L04378  
L04379        fbqq=-(qv-qvsg)/(resg+rsveg)
L04380        
L04381                 
L04382        ustar=(-fbuw)**.5
L04383        tstar=-fbpt/ustar
L04384        qstar=-fbqq/ustar
L04385  
L04386        al=(vk*g_u*tstar)/(pt*ustar*ustar)                      
L04387        
L04388        buu=-g_u/pt0*ustar*tstar
L04389         
L04390        uhb=-ustar*ustar*ua/utot
L04391        vhb=-ustar*ustar*va/utot 
L04392        sf= ustar*tstar*da*cp_u   
L04393        lf= ustar*qstar*da*latent
L04394         
L04395  !     thb= 0.      
L04396        ehb=buu
L04397  !!!!!!!!!!!!!!!
L04398           
L04399        return
L04400        end subroutine flux_flat_ground
```

> 讲解：带植被气孔阻抗的地面通量（Louis 1979 骨架 + Jarvis 型 rsveg=f1·f2·f3·f4 四因子：辐射/湿度亏空/温度/土壤含水量），gr_type=1/2 两套 rsmin/LAI。**注意：4.8.0 中本单元无任何调用方**（buildings 只调 flux_flat 与 flux_flat_roof）——gr_type 的植被参数实际经 flux_flat_roof 生效，本单元是遗留入口，改造时勿白改。

<!-- code_extract code_extract.py v1.2
source: phys/module_sf_bep_bem.F
ranges: L4404-L4589
file_lines: 5706
file_md5: 8d13861f088e806d2558dd37e31126f2
display: line-numbered (strip L-prefix and !file: line to restore)
range_md5: 51cff9d73b7b54740a615978648c392e
seg_lines: 186
label: subroutine flux_flat_roof
-->

```fortran
!file: phys/module_sf_bep_bem.F    L4404-L4589    (subroutine flux_flat_roof)
L04404        subroutine flux_flat_roof(dz,z0,ua,va,pt,pt0,ptg,                     &
L04405                            uhb,vhb,sf,lf,ehb,da,qv,pr,rsg,qr,resg,rsveg,f1,f2,f3,f4,gr_type,pv_frac_roof)
L04406  
L04407  ! ----------------------------------------------------------------------
L04408  !           Calculation of the flux at the ground 
L04409  !           Formulation of Louis (Louis, 1979)       
L04410  ! ----------------------------------------------------------------------
L04411  
L04412        implicit none
L04413  
L04414        real dz                   ! first vertical level
L04415        real pt                   ! potential temperature
L04416        real pt0                  ! reference potential temperature
L04417        real ptg                  ! ground potential temperature
L04418        real ua                   ! wind speed
L04419        real va                   ! wind speed
L04420        real z0                   ! Roughness length
L04421        real da                   ! air density
L04422        real qv                   ! specific humidity
L04423        real pr                   ! pressure
L04424        real rsg                  ! solar radiation
L04425        real qr(ngr_u)         ! Ground Soil Moisture
L04426        real pv_frac_roof
L04427        real rs_eff
L04428  
L04429  ! ----------------------------------------------------------------------
L04430  ! OUTPUT:
L04431  ! ----------------------------------------------------------------------
L04432  ! Explicit component of the momentum, temperature and TKE sources or sinks on horizontal 
L04433  !  surfaces (roofs and street)
L04434  ! The fluxes can be computed as follow: Fluxes of X = B
L04435  !  Example: Momentum fluxes on horizontal surfaces =  uhb_u
L04436        real uhb                  ! U (wind component) Horizontal surfaces, B (explicit) term
L04437        real vhb                  ! V (wind component) Horizontal surfaces, B (explicit) term
L04438  !     real thb                  ! Temperature        Horizontal surfaces, B (explicit) term
L04439        real tva                  ! Temperature          Vertical surfaces, A (implicit) term
L04440        real tvb                  ! Temperature          Vertical surfaces, B (explicit) term
L04441        real ehb                  ! Energy (TKE)       Horizontal surfaces, B (explicit) term
L04442        real sf
L04443        real lf
L04444  
L04445  ! ----------------------------------------------------------------------
L04446  ! LOCAL:
L04447  ! ----------------------------------------------------------------------
L04448        real aa,ah
L04449        real al
L04450        real buu
L04451        real c
L04452        real fbuw
L04453        real fbpt
L04454        real fh
L04455        real fm
L04456        real ric
L04457        real tstar
L04458        real qstar
L04459        real ustar
L04460        real utot
L04461        real wstar
L04462        real zz
L04463        real z0t
L04464        real qvsg,qvs,es,esa,fbqq
L04465        real b,cm,ch,rr,tol
L04466        parameter(b=9.4,cm=7.4,ch=5.3,rr=0.74,tol=.001)
L04467  
L04468        real f
L04469        real f1
L04470        real f2
L04471        real f3
L04472        real f4
L04473        real ta          ! surface air temperature
L04474        real tmp                  ! ground temperature
L04475        real rsveg       ! Stomatal resistance 
L04476        real resg
L04477        real lai         ! leaft area index
L04478        real sdlim       ! radiation limit at which photosyntesis start W/m2
L04479        parameter(sdlim=100.)
L04480        real rsmin
L04481        real rsmax ! Maximun stomatal resistance 
L04482        real qw    ! Wilting point
L04483        parameter(qw=0.06) 
L04484        real qref  ! Field capacity
L04485        parameter(qref=0.37)
L04486        real hs
L04487        parameter(hs=36.35)
L04488  
L04489        real dzgr_u(ngr_u)          ! Layer sizes in the ground
L04490  
L04491        data dzgr_u /0.1,0.003,0.06,0.003,0.05,0.04,0.02,0.0125,0.005,0.0025/
L04492  
L04493        real gx,dzgr_tot
L04494        integer gr_type,iz
L04495  ! ----------------------------------------------------------------------
L04496  ! END VARIABLES DEFINITIONS
L04497  
L04498  ! ----------------------------------------------------------------------
L04499        z0t=z0/10.
L04500        if(gr_type.eq.1)then
L04501        rsmin=40.
L04502        rsmax=5000.
L04503        lai=2.
L04504        elseif(gr_type.eq.2)then
L04505        rsmin=150.
L04506        rsmax=5000.
L04507        lai=3.
L04508        endif
L04509       rs_eff=(1-pv_frac_roof)*rsg
L04510  ! computation of the ground temperature
L04511  
L04512        utot=(ua**2.+va**2.)**.5
L04513  
L04514  !!!! Louis formulation
L04515  !
L04516  ! compute the bulk Richardson Number
L04517  
L04518        zz=dz/2.
L04519  
L04520  
L04521        utot=max(utot,0.01)
L04522  
L04523        ric=2.*g_u*zz*(pt-ptg)/((pt+ptg)*(utot**2))
L04524  
L04525        aa=vk/log(zz/z0)
L04526        ah=vk/log(zz/z0t)
L04527  
L04528        if(ric.gt.0.)then
L04529           fm=1./(1.+0.5*b*ric)**2.
L04530           fh=fm
L04531        else
L04532           c=b*cm*aa*aa*(zz/z0)**.5
L04533           fm=1.-b*ric/(1.+c*(-ric)**.5)
L04534           c=b*cm*aa*ah*(zz/z0t)**.5
L04535           c=c*ch/cm
L04536           fh=1.-b*ric/(1+c*(-ric)**.5)
L04537        endif
L04538  
L04539        fbuw=-aa*aa*utot*utot*fm
L04540        fbpt=-aa*ah*utot*(pt-ptg)*fh/rr
L04541        tmp=ptg*(pr/p0)**(rcp_u)-273.15
L04542        es=6.11*(10.**(tmp*7.5/(237.7+tmp)))
L04543        qvsg=0.62197*es/(0.01*pr-0.378*es)
L04544  
L04545  
L04546        f=0.55*rs_eff/sdlim*2./lai
L04547  
L04548        f1=(f+rsmin/rsmax)/(1.+f)
L04549  
L04550        ta=pt*(pr/p0)**(rcp_u)-273.15
L04551        esa=6.11*(10**(ta*7.5/(237.7+ta)))
L04552        qvs=0.62197*esa/(0.01*pr-0.378*esa)
L04553  
L04554        f2= 1./(1.+hs*(qvs-qv))
L04555        f3=1.-0.0016*(25.-ta)**2.
L04556        f4=0.
L04557        dzgr_tot=0.
L04558        do iz=5,ngr_u
L04559         gx=(qr(iz)-qw)/(qref-qw)
L04560         if (gx.gt.1)gx=1.
L04561         if (gx.lt.0)gx=0.
L04562         f4=f4+gx*dzgr_u(iz)
L04563         dzgr_tot=dzgr_tot+dzgr_u(iz)
L04564        enddo
L04565        f4=f4/dzgr_tot
L04566  
L04567        rsveg=min(rsmin/max(lai*f1*f2*f3*f4,1e-9),rsmax)
L04568  
L04569  
L04570        resg= rr/(aa*aa*utot*fh)
L04571  
L04572  
L04573        fbqq=-(qv-qvsg)/(resg+rsveg)
L04574  
L04575        ustar=(-fbuw)**.5
L04576        tstar=-fbpt/ustar
L04577        qstar=-fbqq/ustar
L04578  
L04579        al=(vk*g_u*tstar)/(pt*ustar*ustar)
L04580  
L04581        buu=-g_u/pt0*ustar*tstar
L04582  
L04583        uhb=-ustar*ustar*ua/utot
L04584        vhb=-ustar*ustar*va/utot
L04585        sf= ustar*tstar*da*cp_u
L04586        lf= ustar*qstar*da*latent
L04587  
L04588        ehb=buu
L04589        end subroutine flux_flat_roof
```

> 讲解：绿屋顶通量：Louis 1979 动量/热量 + 气孔阻抗（f4 用第 5 层起的土壤含水量加权，dzgr_u 十层与 roof_temp_veg 一致）；PV 占比缩放有效短波 rs_eff=(1−pv)·rsg。

<!-- code_extract code_extract.py v1.2
source: phys/module_sf_bep_bem.F
ranges: L4596-L4716
file_lines: 5706
file_md5: 8d13861f088e806d2558dd37e31126f2
display: line-numbered (strip L-prefix and !file: line to restore)
range_md5: 319e0b24acf9085250725a5885eab24d
seg_lines: 121
label: subroutine flux_flat
-->

```fortran
!file: phys/module_sf_bep_bem.F    L4596-L4716    (subroutine flux_flat)
L04596        subroutine flux_flat(dz,z0,ua,va,pt,pt0,ptg,qv,                   &
L04597                            uhb,vhb,sf,lf,ehb,da,pr)
L04598                                  
L04599  ! ----------------------------------------------------------------------
L04600  !           Calculation of the flux at the ground 
L04601  !           Formulation of Louis (Louis, 1979)       
L04602  ! ----------------------------------------------------------------------
L04603  
L04604        implicit none
L04605        real pr
L04606        real dz                   ! first vertical level
L04607        real pt                   ! potential temperature
L04608        real pt0                  ! reference potential temperature
L04609        real ptg                  ! ground potential temperature
L04610        real ua                   ! wind speed
L04611        real va                   ! wind speed
L04612        real z0                   ! Roughness length
L04613        real da                   ! air density
L04614        real qv
L04615  ! ----------------------------------------------------------------------
L04616  ! OUTPUT:
L04617  ! ----------------------------------------------------------------------
L04618  ! Explicit component of the momentum, temperature and TKE sources or sinks on horizontal 
L04619  !  surfaces (roofs and street)
L04620  ! The fluxes can be computed as follow: Fluxes of X = B
L04621  !  Example: Momentum fluxes on horizontal surfaces =  uhb_u
L04622        real uhb                  ! U (wind component) Horizontal surfaces, B (explicit) term
L04623        real vhb                  ! V (wind component) Horizontal surfaces, B (explicit) term
L04624  !     real thb                  ! Temperature        Horizontal surfaces, B (explicit) term
L04625        real tva                  ! Temperature          Vertical surfaces, A (implicit) term
L04626        real tvb                  ! Temperature          Vertical surfaces, B (explicit) term
L04627        real ehb                  ! Energy (TKE)       Horizontal surfaces, B (explicit) term
L04628        real sf
L04629        real lf
L04630         
L04631  ! ----------------------------------------------------------------------
L04632  ! LOCAL:
L04633  ! ----------------------------------------------------------------------
L04634        real aa
L04635        real al
L04636        real buu
L04637        real c
L04638        real fbuw
L04639        real fbpt
L04640        real fh
L04641        real fm
L04642        real ric
L04643        real tstar
L04644        real ustar
L04645        real qstar
L04646        real utot
L04647        real wstar
L04648        real zz
L04649        real qvsg,qvs,es,esa,fbqq,tmp,resg
L04650        real b,cm,ch,rr,tol
L04651        parameter(b=9.4,cm=7.4,ch=5.3,rr=0.74,tol=.001)
L04652  
L04653  ! ----------------------------------------------------------------------
L04654  ! END VARIABLES DEFINITIONS
L04655  ! ----------------------------------------------------------------------
L04656  
L04657  
L04658  ! computation of the ground temperature
L04659           
L04660        utot=(ua**2+va**2)**.5
L04661          
L04662        
L04663  !!!! Louis formulation
L04664  !
L04665  ! compute the bulk Richardson Number
L04666  
L04667        zz=dz/2.
L04668     
L04669  
L04670        utot=max(utot,0.01)
L04671            
L04672        ric=2.*g_u*zz*(pt-ptg)/((pt+ptg)*(utot**2))
L04673                
L04674        aa=vk/log(zz/z0)
L04675  
L04676  
L04677       
L04678        tmp=ptg*(pr/(1.e+5))**(rcp_u)-273.15 
L04679        es=6.11*(10**(tmp*7.5/(237.7+tmp)))
L04680        qvsg=0.62197*es/(0.01*pr-0.378*es)
L04681  
L04682  
L04683  
L04684  ! determine the parameters fm and fh for stable, neutral and unstable conditions
L04685  
L04686        if(ric.gt.0.)then
L04687           fm=1./(1.+0.5*b*ric)**2
L04688           fh=fm
L04689        else
L04690           c=b*cm*aa*aa*(zz/z0)**.5
L04691           fm=1.-b*ric/(1.+c*(-ric)**.5)
L04692           c=c*ch/cm
L04693           fh=1.-b*ric/(1.+c*(-ric)**.5)
L04694        endif
L04695  
L04696        resg= rr/(aa*aa*utot*fh)
L04697        fbuw=-aa*aa*utot*utot*fm
L04698        fbpt=-aa*aa*utot*(pt-ptg)*fh/rr
L04699        fbqq=-(qv-qvsg)/(resg)
L04700                 
L04701        ustar=(-fbuw)**.5
L04702        tstar=-fbpt/ustar
L04703        qstar=-fbqq/ustar
L04704        al=(vk*g_u*tstar)/(pt*ustar*ustar)                      
L04705        
L04706        buu=-g_u/pt0*ustar*tstar
L04707         
L04708        uhb=-ustar*ustar*ua/utot
L04709        vhb=-ustar*ustar*va/utot 
L04710        sf= ustar*tstar*da*cp_u  
L04711        lf= ustar*qstar*da*latent 
L04712        ehb=buu
L04713  !!!!!!!!!!!!!!!
L04714           
L04715        return
L04716        end subroutine flux_flat
```

> 讲解：普通路面/屋顶通量（Louis 1979 全套：bulk Ri 分区 fm/fh、稳定 1/(1+0.5·b·Ri)²、不稳定 1−b·Ri/(1+c·(−Ri)^½)；b=9.4、cm=7.4、ch=5.3、rr=0.74 为 Louis 常数）；潜热用水面饱和 qvsg 无阻抗（积水处理在 buildings 的 wfg/wfr 缩放）。module_sf_bep.F 内有同名单独拷贝（改需同步）。

## 六、初始化与视野因子

<!-- code_extract code_extract.py v1.2
source: phys/module_sf_bep_bem.F
ranges: L4721-L4820
file_lines: 5706
file_md5: 8d13861f088e806d2558dd37e31126f2
display: line-numbered (strip L-prefix and !file: line to restore)
range_md5: 21850698249ae3427ca4408ea7539e7d
seg_lines: 100
label: subroutine icBEP
-->

```fortran
!file: phys/module_sf_bep_bem.F    L4721-L4820    (subroutine icBEP)
L04721        subroutine icBEP (nd_u,h_b,d_b,ss_u,pb_u,nz_u,z_u)
L04722  
L04723        implicit none
L04724  
L04725  !    Street parameters
L04726        integer nd_u(nurbm)     ! Number of street direction for each urban class
L04727        real h_b(nz_um,nurbm)   ! Bulding's heights [m]
L04728        real d_b(nz_um,nurbm)   ! The probability that a building has an height h_b
L04729  ! -----------------------------------------------------------------------
L04730  !     Output
L04731  !------------------------------------------------------------------------
L04732  
L04733        real ss_u(nz_um,nurbm)     ! The probability that a building has an height equal to z
L04734        real pb_u(nz_um,nurbm)     ! The probability that a building has an height greater or equal to z
L04735  
L04736  !    Grid parameters
L04737        integer nz_u(nurbm)     ! Number of layer in the urban grid
L04738        real z_u(nz_um)       ! Height of the urban grid levels
L04739  
L04740  
L04741  ! -----------------------------------------------------------------------
L04742  !     Local
L04743  !------------------------------------------------------------------------
L04744  
L04745        integer iz_u,id,ilu,iurb
L04746  
L04747        real dtot
L04748        real hbmax
L04749  
L04750  ! -----------------------------------------------------------------------
L04751  !     This routine initialise the urban paramters for the BEP module
L04752  !------------------------------------------------------------------------
L04753  !
L04754  !Initialize variables
L04755  !
L04756   !
L04757        nz_u=0
L04758        z_u=0.
L04759        ss_u=0.
L04760        pb_u=0.
L04761  
L04762  ! Computation of the urban levels height
L04763  
L04764        z_u(1)=0.
L04765  
L04766        do iz_u=1,nz_um-1
L04767           z_u(iz_u+1)=z_u(iz_u)+dz_u
L04768        enddo
L04769  
L04770  ! Normalisation of the building density
L04771  
L04772        do iurb=1,nurbm
L04773           dtot=0.
L04774           do ilu=1,nz_um
L04775              dtot=dtot+d_b(ilu,iurb)
L04776           enddo
L04777           do ilu=1,nz_um
L04778              d_b(ilu,iurb)=d_b(ilu,iurb)/dtot
L04779           enddo
L04780        enddo
L04781  
L04782  ! Compute the view factors, pb and ss
L04783  
L04784        do iurb=1,nurbm
L04785           hbmax=0.
L04786           nz_u(iurb)=0
L04787           do ilu=1,nz_um
L04788              if(h_b(ilu,iurb).gt.hbmax)hbmax=h_b(ilu,iurb)
L04789           enddo
L04790  
L04791           do iz_u=1,nz_um-1
L04792              if(z_u(iz_u+1).gt.hbmax)go to 10
L04793           enddo
L04794  
L04795   10      continue
L04796            nz_u(iurb)=iz_u+1
L04797  
L04798           do id=1,nd_u(iurb)
L04799  
L04800              do iz_u=1,nz_u(iurb)
L04801                 ss_u(iz_u,iurb)=0.
L04802                 do ilu=1,nz_um
L04803                    if(z_u(iz_u).le.h_b(ilu,iurb)                      &
L04804                      .and.z_u(iz_u+1).gt.h_b(ilu,iurb))then
L04805                          ss_u(iz_u,iurb)=ss_u(iz_u,iurb)+d_b(ilu,iurb)
L04806                    endif
L04807                 enddo
L04808              enddo
L04809  
L04810              pb_u(1,iurb)=1.
L04811              do iz_u=1,nz_u(iurb)
L04812                 pb_u(iz_u+1,iurb)=max(0.,pb_u(iz_u,iurb)-ss_u(iz_u,iurb))
L04813              enddo
L04814  
L04815           enddo
L04816        end do
L04817  
L04818  
L04819        return
L04820        end subroutine icBEP
```

> 讲解：类级初始化：城市网格高度 z_u=5 m 均匀 18 层；建筑高度谱 d_b 归一化；每类从最高楼定 nz_u；按「楼高落在哪层」折算该层有屋顶的概率 ss_u，pb_u=1−累计 ss（pb=该高度以上有建筑的概率——「存在概率」的补集定义）。

<!-- code_extract code_extract.py v1.2
source: phys/module_sf_bep_bem.F
ranges: L4826-L4985
file_lines: 5706
file_md5: 8d13861f088e806d2558dd37e31126f2
display: line-numbered (strip L-prefix and !file: line to restore)
range_md5: fdc4fd10089f29c957ab7f36697f28d0
seg_lines: 160
label: subroutine view_factors
-->

```fortran
!file: phys/module_sf_bep_bem.F    L4826-L4985    (subroutine view_factors)
L04826        subroutine view_factors(iurb,nz_u,id,dxy,z,ws,fww,fwg,fgw,fsg,fsw,fws) 
L04827       
L04828        implicit none
L04829  
L04830   
L04831  
L04832  ! -----------------------------------------------------------------------
L04833  !     Input
L04834  !------------------------------------------------------------------------
L04835  
L04836        integer iurb            ! Number of the urban class
L04837        integer nz_u            ! Number of levels in the urban grid
L04838        integer id              ! Street direction number
L04839        real ws                 ! Street width
L04840        real z(nz_um)         ! Height of the urban grid levels
L04841        real dxy                ! Street lenght
L04842  
L04843  
L04844  ! -----------------------------------------------------------------------
L04845  !     Output
L04846  !------------------------------------------------------------------------
L04847  
L04848  !   fww,fwg,fgw,fsw,fsg are the view factors used to compute the long wave
L04849  !   and the short wave radation. They are the part of radiation from a surface
L04850  !   or from the sky to another surface.
L04851  
L04852        real fww(nz_um,nz_um,ndm,nurbm)            !  from wall to wall
L04853        real fwg(nz_um,ndm,nurbm)                  !  from wall to ground
L04854        real fgw(nz_um,ndm,nurbm)                  !  from ground to wall
L04855        real fsw(nz_um,ndm,nurbm)                  !  from sky to wall
L04856        real fws(nz_um,ndm,nurbm)                  !  from wall to sky
L04857        real fsg(ndm,nurbm)                        !  from sky to ground
L04858  
L04859  
L04860  ! -----------------------------------------------------------------------
L04861  !     Local
L04862  !------------------------------------------------------------------------
L04863  
L04864        integer jz,iz
L04865  
L04866        real hut
L04867        real f1,f2,f12,f23,f123,ftot
L04868        real fprl,fnrm
L04869        real a1,a2,a3,a4,a12,a23,a123
L04870  
L04871  ! -----------------------------------------------------------------------
L04872  !     This routine calculates the view factors
L04873  !------------------------------------------------------------------------
L04874          
L04875        hut=z(nz_u+1)
L04876          
L04877        do jz=1,nz_u      
L04878        
L04879  ! radiation from wall to wall
L04880         
L04881           do iz=1,nz_u
L04882       
L04883              call fprls (fprl,dxy,abs(z(jz+1)-z(iz  )),ws)
L04884              f123=fprl
L04885              call fprls (fprl,dxy,abs(z(jz+1)-z(iz+1)),ws)
L04886              f23=fprl
L04887              call fprls (fprl,dxy,abs(z(jz  )-z(iz  )),ws)
L04888              f12=fprl
L04889              call fprls (fprl,dxy,abs(z(jz  )-z(iz+1)),ws)
L04890              f2 = fprl
L04891         
L04892              a123=dxy*(abs(z(jz+1)-z(iz  )))
L04893              a12 =dxy*(abs(z(jz  )-z(iz  )))
L04894              a23 =dxy*(abs(z(jz+1)-z(iz+1)))
L04895              a1  =dxy*(abs(z(iz+1)-z(iz  )))
L04896              a2  =dxy*(abs(z(jz  )-z(iz+1)))
L04897              a3  =dxy*(abs(z(jz+1)-z(jz  )))
L04898         
L04899              ftot=0.5*(a123*f123-a23*f23-a12*f12+a2*f2)/a1
L04900         
L04901              fww(iz,jz,id,iurb)=ftot*a1/a3
L04902  
L04903           enddo 
L04904  
L04905  ! radiation from ground to wall
L04906         
L04907           call fnrms (fnrm,z(jz+1),dxy,ws)
L04908           f12=fnrm
L04909           call fnrms (fnrm,z(jz)  ,dxy,ws)
L04910           f1=fnrm
L04911         
L04912           a1 = ws*dxy
L04913           
L04914           a12= ws*dxy
L04915         
L04916           a4=(z(jz+1)-z(jz))*dxy
L04917         
L04918           ftot=(a12*f12-a12*f1)/a1
L04919                      
L04920           fgw(jz,id,iurb)=ftot*a1/a4
L04921       
L04922  !  radiation from sky to wall
L04923       
L04924           call fnrms(fnrm,hut-z(jz)  ,dxy,ws)
L04925           f12 = fnrm
L04926           call fnrms (fnrm,hut-z(jz+1),dxy,ws)
L04927           f1 =fnrm
L04928         
L04929           a1 = ws*dxy
L04930         
L04931           a12= ws*dxy
L04932                
L04933           a4 = (z(jz+1)-z(jz))*dxy
L04934         
L04935           ftot=(a12*f12-a12*f1)/a1
L04936          
L04937           fsw(jz,id,iurb)=ftot*a1/a4       
L04938        
L04939        enddo
L04940  
L04941  ! radiation from wall to sky      
L04942         do iz=1,nz_u
L04943         call fnrms(fnrm,ws,dxy,hut-z(iz))
L04944         f12=fnrm
L04945         call fnrms(fnrm,ws,dxy,hut-z(iz+1))
L04946         f1=fnrm
L04947         a1 = (z(iz+1)-z(iz))*dxy
L04948         a2 = (hut-z(iz+1))*dxy
L04949         a12= (hut-z(iz))*dxy
L04950         a4 = ws*dxy
L04951         ftot=(a12*f12-a2*f1)/a1
L04952         fws(iz,id,iurb)=ftot*a1/a4 
L04953   
L04954        enddo
L04955  !!!!!!!!!!!!!
L04956  
L04957  
L04958         do iz=1,nz_u
L04959  
L04960  ! radiation from wall to ground
L04961        
L04962           call fnrms (fnrm,ws,dxy,z(iz+1))
L04963           f12=fnrm
L04964           call fnrms (fnrm,ws,dxy,z(iz  ))
L04965           f1 =fnrm
L04966           
L04967           a1= (z(iz+1)-z(iz) )*dxy
L04968         
L04969           a2 = z(iz)*dxy
L04970           a12= z(iz+1)*dxy
L04971           a4 = ws*dxy
L04972  
L04973           ftot=(a12*f12-a2*f1)/a1        
L04974                      
L04975           fwg(iz,id,iurb)=ftot*a1/a4
L04976          
L04977        enddo
L04978  
L04979  ! radiation from sky to ground
L04980        
L04981        call fprls (fprl,dxy,ws,hut)
L04982        fsg(id,iurb)=fprl
L04983  
L04984        return
L04985        end subroutine view_factors
```

> 讲解：峡谷视野因子全解析计算（BLM 论文附录 A）：fww（墙-墙）用两平行矩形角系数 fprls 的**差分组合** ½(a123·f123−a23·f23−a12·f12+a2·f2)/a1（矩形代数）；fwg/fsw/fws/fwg 用正交面角系数 fnrms 的同样差分技术；fsg（天空-地面）直接 fprls(ws, dxy, hut)。全部几何量解析——不随时间变，icBEP_XY 每点每步重算是因为它们依赖逐点的 ws/strd。

<!-- code_extract code_extract.py v1.2
source: phys/module_sf_bep_bem.F
ranges: L4991-L5016
file_lines: 5706
file_md5: 8d13861f088e806d2558dd37e31126f2
display: line-numbered (strip L-prefix and !file: line to restore)
range_md5: 8450764fa6fbbf853c194461cff4c148
seg_lines: 26
label: subroutine fprls
-->

```fortran
!file: phys/module_sf_bep_bem.F    L4991-L5016    (subroutine fprls)
L04991        SUBROUTINE fprls (fprl,a,b,c)
L04992  
L04993        implicit none
L04994  
L04995       
L04996              
L04997        real a,b,c
L04998        real x,y
L04999        real fprl
L05000  
L05001  
L05002        x=a/c
L05003        y=b/c
L05004        
L05005        if(a.eq.0.or.b.eq.0.)then
L05006         fprl=0.
L05007        else
L05008         fprl=log( ( (1.+x**2)*(1.+y**2)/(1.+x**2+y**2) )**.5)+  &
L05009             y*((1.+x**2)**.5)*atan(y/((1.+x**2)**.5))+          &  
L05010             x*((1.+y**2)**.5)*atan(x/((1.+y**2)**.5))-          &   
L05011             y*atan(y)-x*atan(x)
L05012         fprl=fprl*2./(pi*x*y)
L05013        endif
L05014        
L05015        return
L05016        end subroutine fprls
```

<!-- code_extract code_extract.py v1.2
source: phys/module_sf_bep_bem.F
ranges: L5021-L5049
file_lines: 5706
file_md5: 8d13861f088e806d2558dd37e31126f2
display: line-numbered (strip L-prefix and !file: line to restore)
range_md5: 9fbc43a3b7811126fa69ac91f1b2d631
seg_lines: 29
label: subroutine fnrms
-->

```fortran
!file: phys/module_sf_bep_bem.F    L5021-L5049    (subroutine fnrms)
L05021        SUBROUTINE fnrms (fnrm,a,b,c)
L05022  
L05023        implicit none
L05024  
L05025  
L05026  
L05027        real a,b,c
L05028        real x,y,z,a1,a2,a3,a4,a5,a6
L05029        real fnrm
L05030        
L05031        x=a/b
L05032        y=c/b
L05033        z=x**2+y**2
L05034        
L05035        if(y.eq.0.or.x.eq.0)then
L05036         fnrm=0.
L05037        else
L05038         a1=log( (1.+x*x)*(1.+y*y)/(1.+z) )
L05039         a2=y*y*log(y*y*(1.+z)/z/(1.+y*y) )
L05040         a3=x*x*log(x*x*(1.+z)/z/(1.+x*x) )
L05041         a4=y*atan(1./y)
L05042         a5=x*atan(1./x)
L05043         a6=sqrt(z)*atan(1./sqrt(z))
L05044         fnrm=0.25*(a1+a2+a3)+a4+a5-a6
L05045         fnrm=fnrm/(pi*y)
L05046        endif
L05047        
L05048        return
L05049        end subroutine fnrms
```

> 讲解：两个解析角系数公式：fprls=两平行等长矩形（教科书标准式，atan 组合）；fnrms=垂直矩形对（含 6 项对数/atan）。零面积保护出口。

<!-- code_extract code_extract.py v1.2
source: phys/module_sf_bep_bem.F
ranges: L5052-L5212
file_lines: 5706
file_md5: 8d13861f088e806d2558dd37e31126f2
display: line-numbered (strip L-prefix and !file: line to restore)
range_md5: 0c698a0333efbb313fafb2f84f204b98
seg_lines: 161
label: subroutine init_para
-->

```fortran
!file: phys/module_sf_bep_bem.F    L5052-L5212    (subroutine init_para)
L05052          SUBROUTINE init_para(alag_u,alaw_u,alar_u,csg_u,csw_u,csr_u,&
L05053          twini_u,trini_u,tgini_u,albg_u,albw_u,albr_u,albwin_u,emg_u,emw_u,&
L05054          emr_u,emwind_u,z0g_u,z0r_u,nd_u,strd_u,drst_u,ws_u,bs_u,h_b,d_b,  &
L05055          cop_u,pwin_u,beta_u,sw_cond_u,time_on_u,time_off_u,targtemp_u,    &
L05056          bldac_frc_u,cooled_frc_u,                                         &
L05057          gaptemp_u, targhum_u,gaphum_u,perflo_u,                           &
L05058          gr_frac_roof_u,pv_frac_roof_u,                   &
L05059          hsesf_u,hsequip,irho,gr_flag_u,gr_type_u)
L05060  
L05061   
L05062  ! initialization routine, where the variables from the table are read
L05063  
L05064        implicit none
L05065        integer iurb            ! urban class number
L05066  !    Building parameters      
L05067        real alag_u(nurbm)      ! Ground thermal diffusivity [m^2 s^-1]
L05068        real alaw_u(nurbm)      ! Wall thermal diffusivity [m^2 s^-1]
L05069        real alar_u(nurbm)      ! Roof thermal diffusivity [m^2 s^-1]
L05070        real csg_u(nurbm)       ! Specific heat of the ground material [J m^3 K^-1]
L05071        real csw_u(nurbm)       ! Specific heat of the wall material [J m^3 K^-1]
L05072        real csr_u(nurbm)       ! Specific heat of the roof material [J m^3 K^-1]
L05073        real twini_u(nurbm)     ! Temperature inside the buildings behind the wall [K]
L05074        real trini_u(nurbm)     ! Temperature inside the buildings behind the roof [K]
L05075        real tgini_u(nurbm)     ! Initial road temperature
L05076  
L05077  !    Radiation parameters
L05078        real albg_u(nurbm)      ! Albedo of the ground
L05079        real albw_u(nurbm)      ! Albedo of the wall
L05080        real albr_u(nurbm)      ! Albedo of the roof
L05081        real albwin_u(nurbm)    ! Albedo of the window
L05082        real emg_u(nurbm)       ! Emissivity of ground
L05083        real emw_u(nurbm)       ! Emissivity of wall
L05084        real emr_u(nurbm)       ! Emissivity of roof
L05085        real emwind_u(nurbm)    ! Emissivity of windows
L05086  
L05087  !    Roughness parameters
L05088        real z0g_u(nurbm)       ! The ground's roughness length      
L05089        real z0r_u(nurbm)       ! The roof's roughness length
L05090  
L05091  !    Street parameters
L05092        integer nd_u(nurbm)     ! Number of street direction for each urban class
L05093  
L05094        real strd_u(ndm,nurbm)  ! Street length (fix to greater value to the horizontal length of the cells)
L05095        real drst_u(ndm,nurbm)  ! Street direction [degree]
L05096        real ws_u(ndm,nurbm)    ! Street width [m]
L05097        real bs_u(ndm,nurbm)    ! Building width [m]
L05098        real h_b(nz_um,nurbm)   ! Bulding's heights [m]
L05099        real d_b(nz_um,nurbm)   ! The probability that a building has an height h_b
L05100  
L05101        integer i,iu
L05102        integer nurb ! number of urban classes used
L05103          real, intent(out) :: bldac_frc_u(nurbm)
L05104        real, intent(out) :: cooled_frc_u(nurbm)
L05105        real, intent(out) :: cop_u(nurbm)
L05106        real, intent(out) :: pwin_u(nurbm)
L05107        real, intent(out) :: beta_u(nurbm)
L05108        integer, intent(out) :: sw_cond_u(nurbm)
L05109        real, intent(out) :: time_on_u(nurbm)
L05110        real, intent(out) :: time_off_u(nurbm)
L05111        real, intent(out) :: targtemp_u(nurbm)
L05112        real, intent(out) :: gaptemp_u(nurbm)
L05113        real, intent(out) :: targhum_u(nurbm)
L05114        real, intent(out) :: gaphum_u(nurbm)
L05115        real, intent(out) :: perflo_u(nurbm)
L05116        real, intent(out) :: gr_frac_roof_u(nurbm)
L05117        real, intent(out) :: pv_frac_roof_u(nurbm)
L05118        real, intent(out) :: hsesf_u(nurbm)
L05119        real, intent(out) :: hsequip(24)
L05120        real, intent(out) :: irho(24)
L05121        integer, intent(out) :: gr_flag_u,gr_type_u
L05122  !
L05123  !Initialize some variables
L05124  !  
L05125       
L05126         h_b=0.
L05127         d_b=0.
L05128  
L05129         nurb=ICATE
L05130         do iu=1,nurb                         
L05131            nd_u(iu)=0
L05132         enddo
L05133  
L05134         csw_u=CAPB_TBL / (( 1.0 / 4.1868 ) * 1.E-6)
L05135         csr_u=CAPR_TBL / (( 1.0 / 4.1868 ) * 1.E-6)
L05136         csg_u=CAPG_TBL / (( 1.0 / 4.1868 ) * 1.E-6)
L05137         do i=1,icate
L05138           alaw_u(i)=AKSB_TBL(i) / csw_u(i) / (( 1.0 / 4.1868 ) * 1.E-2)
L05139           alar_u(i)=AKSR_TBL(i) / csr_u(i) / (( 1.0 / 4.1868 ) * 1.E-2)
L05140           alag_u(i)=AKSG_TBL(i) / csg_u(i) / (( 1.0 / 4.1868 ) * 1.E-2)
L05141         enddo
L05142         twini_u=TBLEND_TBL
L05143         trini_u=TRLEND_TBL
L05144         tgini_u=TGLEND_TBL
L05145         albw_u=ALBB_TBL
L05146         albr_u=ALBR_TBL
L05147         albg_u=ALBG_TBL
L05148         emw_u=EPSB_TBL
L05149         emr_u=EPSR_TBL
L05150         emg_u=EPSG_TBL
L05151         z0r_u=Z0R_TBL
L05152         z0g_u=Z0G_TBL
L05153         nd_u=NUMDIR_TBL
L05154  !FS
L05155       !  print*, 'g alla call', gr_frac_roof_u(iurb)
L05156         bldac_frc_u = bldac_frc_tbl
L05157         cooled_frc_u = cooled_frc_tbl
L05158         cop_u = cop_tbl
L05159         pwin_u = pwin_tbl
L05160         beta_u = beta_tbl
L05161         sw_cond_u = sw_cond_tbl
L05162         time_on_u = time_on_tbl
L05163         time_off_u = time_off_tbl
L05164         targtemp_u = targtemp_tbl
L05165         gaptemp_u = gaptemp_tbl
L05166         targhum_u = targhum_tbl
L05167         gaphum_u = gaphum_tbl
L05168         perflo_u = perflo_tbl
L05169         gr_frac_roof_u =gr_frac_roof_tbl
L05170         gr_flag_u=gr_flag_tbl
L05171         pv_frac_roof_u = pv_frac_roof_tbl
L05172         hsesf_u = hsesf_tbl
L05173         hsequip = hsequip_tbl
L05174         irho=irho_tbl
L05175         gr_type_u=gr_type_tbl
L05176         do iu=1,icate
L05177                if(ndm.lt.nd_u(iu))then
L05178                  write(*,*)'ndm too small in module_sf_bep_bem, please increase to at least ', nd_u(iu)
L05179                  write(*,*)'remember also that num_urban_layers should be equal or greater than nz_um*ndm*nwr-u!'
L05180                  stop
L05181                endif
L05182           do i=1,nd_u(iu)
L05183             drst_u(i,iu)=STREET_DIRECTION_TBL(i,iu) * pi/180.
L05184             ws_u(i,iu)=STREET_WIDTH_TBL(i,iu)
L05185             bs_u(i,iu)=BUILDING_WIDTH_TBL(i,iu)
L05186           enddo
L05187         enddo
L05188         do iu=1,ICATE
L05189            if(nz_um.lt.numhgt_tbl(iu)+3)then
L05190                write(*,*)'nz_um too small in module_sf_bep, please increase to at least ',numhgt_tbl(iu)+3
L05191                write(*,*)'remember also that num_urban_layers should be equal or greater than nz_um*ndm*nwr-u!'
L05192                stop
L05193            endif
L05194           do i=1,NUMHGT_TBL(iu)
L05195             h_b(i,iu)=HEIGHT_BIN_TBL(i,iu)
L05196             d_b(i,iu)=HPERCENT_BIN_TBL(i,iu)
L05197           enddo
L05198         enddo
L05199  
L05200         do i=1,ndm
L05201          do iu=1,nurbm
L05202           strd_u(i,iu)=100000.
L05203          enddo
L05204         enddo
L05205  
L05206         do iu=1,nurb  
L05207            emwind_u(iu)=0.9                       
L05208            call albwindow(albwin_u(iu))  
L05209         enddo
L05210         
L05211         return
L05212         end subroutine init_para
```

> 讲解：urban_param.tbl → SI 的换算清单：热容 CAP*_TBL/(4.1868⁻¹·1e−6)（cal·cm⁻³·K⁻¹→J·m⁻³·K⁻¹）、导热率 AKS*_TBL 再除热容得扩散率；BEM 全套开关（cop/pwin/beta/sw_cond/time_on/off/targtemp/gaptemp/targhum/gaphum/perflo/bldac_frc/cooled_frc/gr_frac_roof/pv_frac_roof/hsesf/hsequip 24h 设备热谱/irho 24h 灌溉窗/gr_type）从 TBL 整体搬运；街道方向角转弧度；**emwind 硬编码 0.9**、窗户反照率由 albwindow 数值积分算出。ICATE（实际类数）来自 module_sf_urban。**论文 2 的标定参数（α/ε/λ/d）很多能对应到这些 TBL 量——改造时先在这里建「逐格场」的进场路径。**

## 七、辐射诊断与窗户光学

<!-- code_extract code_extract.py v1.2
source: phys/module_sf_bep_bem.F
ranges: L5218-L5354
file_lines: 5706
file_md5: 8d13861f088e806d2558dd37e31126f2
display: line-numbered (strip L-prefix and !file: line to restore)
range_md5: edd726b2f6009e09ddce28bf08c1de19
seg_lines: 137
label: subroutine upward_rad
-->

```fortran
!file: phys/module_sf_bep_bem.F    L5218-L5354    (subroutine upward_rad)
L05218         subroutine upward_rad(ndu,nzu,ws,bs,sigma,pb,ss,                &
L05219                         tg_av,emg_u,albg_u,rlg,rsg,sfg,lfg,                   & 
L05220                         tw,emw_u,albw_u,rlw,rsw,sfw,                   & 
L05221                         tr_av,emr_u,albr_u,emwind,albwind,twlev,pwin,     &
L05222                         sfwind,rld,rs, sfr,sfrv,lfr,lfrv,                            & 
L05223                         rs_abs,rl_up,emiss,grdflx_urb,gr_frac_roof,tpvlev,pv_frac_roof)
L05224  !
L05225  ! IN this surboutine we compute the upward longwave flux, and the albedo
L05226  ! needed for the radiation scheme
L05227  !
L05228        implicit none
L05229  
L05230  !
L05231  !INPUT VARIABLES
L05232  !
L05233        real rsw(2*ndm,nz_um)        ! Short wave radiation at the wall for a given canyon direction [W/m2]
L05234        real rlw(2*ndm,nz_um)         ! Long wave radiation at the walls for a given canyon direction [W/m2]
L05235        real rsg(ndm)                   ! Short wave radiation at the canyon for a given canyon direction [W/m2]
L05236        real rlg(ndm)                   ! Long wave radiation at the ground for a given canyon direction [W/m2]
L05237        real rs                        ! Short wave radiation at the horizontal surface from the sun [W/m2]  
L05238        real sfw(2*ndm,nz_um)      ! Sensible heat flux from walls [W/m2]
L05239        real sfg(ndm)              ! Sensible heat flux from ground (road) [W/m2]
L05240        real lfg(ndm)
L05241        real sfr(ndm,nz_um)      ! Sensible heat flux from roofs [W/m2]   
L05242        real lfr(ndm,nz_um)
L05243        real lfrv(ndm,nz_um)
L05244        real sfrv(ndm,nz_um)
L05245        real gr_frac_roof
L05246        real rld                        ! Long wave radiation from the sky [W/m2]
L05247        real albg_u                    ! albedo of the ground/street
L05248        real albw_u                    ! albedo of the walls
L05249        real albr_u                    ! albedo of the roof 
L05250        real ws(ndm)                        ! width of the street
L05251        real bs(ndm)
L05252                          ! building size
L05253        real pb(nz_um)                ! Probability to have a building with an height equal or higher   
L05254        integer nzu
L05255        real ss(nz_um)                ! Probability to have a building of a given height
L05256        real sigma                       
L05257        real emg_u                       ! emissivity of the street
L05258        real emw_u                       ! emissivity of the wall
L05259        real emr_u                       ! emissivity of the roof
L05260        real tw(2*ndm,nz_um)  ! Temperature in each layer of the wall [K]
L05261        real tr_av(ndm,nz_um)  ! Temperature in each layer of the roof [K]
L05262        real tpvlev(ndm,nz_um)
L05263        real pv_frac_roof
L05264        real tg_av(ndm)          ! Temperature in each layer of the ground [K]
L05265        integer id ! street direction
L05266        integer ndu ! number of street directions
L05267  !
L05268  !New variables BEM
L05269  !
L05270        real emwind               !Emissivity of the windows
L05271        real albwind              !Albedo of the windows
L05272        real twlev(2*ndm,nz_um)   !Averaged Temperature of the windows 
L05273        real pwin                 !Coverage area fraction of the windows
L05274        real gflwin               !Heat stored for the windows
L05275        real sfwind(2*ndm,nz_um)  !Sensible heat flux from windows [W/m2]
L05276  
L05277  !OUTPUT/INPUT
L05278        real rs_abs  ! absrobed solar radiationfor this street direction
L05279        real rl_up   ! upward longwave radiation for this street direction
L05280        real emiss ! mean emissivity
L05281        real grdflx_urb ! ground heat flux 
L05282  !LOCAL
L05283        integer iz,iw
L05284        real rl_inc,rl_emit
L05285        real gfl
L05286        integer ix,iy,iwrong
L05287  
L05288           iwrong=1
L05289        do iz=1,nzu+1
L05290        do id=1,ndu
L05291        if(tr_av(id,iz).lt.100.)then
L05292                write(203,*) tr_av(id,iz)
L05293                write(*,*)'in upward_rad ',iz,id,iw,tr_av(id,iz)
L05294                iwrong=0
L05295        endif     
L05296        enddo
L05297        enddo
L05298             if(iwrong.eq.0)stop
L05299  
L05300        rl_up=0.
L05301   
L05302        rs_abs=0.
L05303        rl_inc=0.
L05304        emiss=0.
L05305        rl_emit=0.
L05306        grdflx_urb=0.
L05307        do id=1,ndu          
L05308         rl_emit=rl_emit-( emg_u*sigma*(tg_av(id)**4.)+(1-emg_u)*rlg(id))*ws(id)/(ws(id)+bs(id))/ndu
L05309         rl_inc=rl_inc+rlg(id)*ws(id)/(ws(id)+bs(id))/ndu       
L05310         rs_abs=rs_abs+(1.-albg_u)*rsg(id)*ws(id)/(ws(id)+bs(id))/ndu
L05311           gfl=(1.-albg_u)*rsg(id)+emg_u*rlg(id)-emg_u*sigma*(tg_av(id)**4.)+sfg(id)+lfg(id)
L05312           grdflx_urb=grdflx_urb-gfl*ws(id)/(ws(id)+bs(id))/ndu  
L05313   
L05314           do iz=2,nzu
L05315               rl_emit=rl_emit-(emr_u*sigma*(1.-pv_frac_roof)*tr_av(id,iz)**4.+0.79*sigma*pv_frac_roof*tpvlev(id,iz)**4+ &
L05316                       (1-emr_u)*rld*(1.-pv_frac_roof)+(1-0.79)*pv_frac_roof*rld)*ss(iz)*bs(id)/(ws(id)+bs(id))/ndu
L05317               rl_inc=rl_inc+rld*ss(iz)*bs(id)/(ws(id)+bs(id))/ndu
L05318               rs_abs=rs_abs+((1.-albr_u)*rs*(1.-pv_frac_roof)+(1.-0.11)*rs*pv_frac_roof)*ss(iz)*bs(id)/(ws(id)+bs(id))/ndu
L05319               gfl=(1.-albr_u)*rs*(1-pv_frac_roof)+emr_u*rld*(1-pv_frac_roof)+pv_frac_roof*emr_u*sigma*tpvlev(id,iz)**4 &
L05320                  -emr_u*sigma*(tr_av(id,iz)**4.)+(1-gr_frac_roof)*sfr(id,iz)+(sfrv(id,iz)+lfrv(id,iz))*gr_frac_roof+(1.-gr_frac_roof)*lfr(id,iz)
L05321               grdflx_urb=grdflx_urb-gfl*ss(iz)*bs(id)/(ws(id)+bs(id))/ndu  
L05322           enddo
L05323             
L05324           do iz=1,nzu 
L05325             
L05326              rl_emit=rl_emit-(emw_u*(1.-pwin)*sigma*(tw(2*id-1,iz)**4.+tw(2*id,iz)**4.)+ &
L05327                              (emwind*pwin*sigma*(twlev(2*id-1,iz)**4.+twlev(2*id,iz)**4.))+ &
L05328                  ((1.-emw_u)*(1.-pwin)+pwin*(1.-emwind))*(rlw(2*id-1,iz)+rlw(2*id,iz)))* &
L05329                              dz_u*pb(iz+1)/(ws(id)+bs(id))/ndu
L05330  
L05331              rl_inc=rl_inc+((rlw(2*id-1,iz)+rlw(2*id,iz)))*dz_u*pb(iz+1)/(ws(id)+bs(id))/ndu
L05332  
L05333              rs_abs=rs_abs+(((1.-albw_u)*(1.-pwin)+(1.-albwind)*pwin)*(rsw(2*id-1,iz)+rsw(2*id,iz)))*&
L05334                            dz_u*pb(iz+1)/(ws(id)+bs(id))/ndu 
L05335  
L05336              gfl=(1.-albw_u)*(rsw(2*id-1,iz)+rsw(2*id,iz)) +emw_u*( rlw(2*id-1,iz)+rlw(2*id,iz) )   &
L05337               -emw_u*sigma*( tw(2*id-1,iz)**4.+tw(2*id,iz)**4. )+(sfw(2*id-1,iz)+sfw(2*id,iz))   
L05338  
L05339              gflwin=(1.-albwind)*(rsw(2*id-1,iz)+rsw(2*id,iz)) +emwind*(rlw(2*id-1,iz)+rlw(2*id,iz))   &
L05340               -emwind*sigma*( twlev(2*id-1,iz)**4.+twlev(2*id,iz)**4.)+(sfwind(2*id-1,iz)+sfwind(2*id,iz)) 
L05341                 
L05342             
L05343              grdflx_urb=grdflx_urb-(gfl*(1.-pwin)+pwin*gflwin)*dz_u*pb(iz+1)/(ws(id)+bs(id))/ndu
L05344  
L05345           enddo
L05346            
L05347        enddo
L05348          emiss=(emg_u+emw_u+emr_u)/3.
L05349          rl_up=(rl_inc+rl_emit)-rld
L05350         
L05351           
L05352        return
L05353  
L05354        END SUBROUTINE upward_rad
```

> 讲解：给辐射方案的城市等效量：按 ws/(ws+bs)（地面权重）与 ss·bs/(ws+bs)（屋顶权重）与 dz_u·pb/(ws+bs)（墙面权重）对三个方向聚合——rl_emit（发射−反射）、rl_inc（入射）、rs_abs（吸收短波）、grdflx_urb（每表面能量收支残差=储热）；屋顶 PV 部分用常数发射率 0.79/反照率 0.11；emiss=(emg+emw+emr)/3 简单平均。rl_up=rl_inc+rl_emit−rld 为辐射方案所需的向上长波。**开头的 <100 K 哨兵**（write(203)+stop）是调试遗留——生产运行若触发会硬停，改造时建议换成 wrf_error_fatal。

<!-- code_extract code_extract.py v1.2
source: phys/module_sf_bep_bem.F
ranges: L5361-L5437
file_lines: 5706
file_md5: 8d13861f088e806d2558dd37e31126f2
display: line-numbered (strip L-prefix and !file: line to restore)
range_md5: 61fb9a96bfcbcecb0fdb9032af00dddf
seg_lines: 77
label: subroutine albwindow
-->

```fortran
!file: phys/module_sf_bep_bem.F    L5361-L5437    (subroutine albwindow)
L05361           subroutine albwindow(albwin)
L05362  		
L05363  !-------------------------------------------------------------------
L05364  	 implicit none
L05365  
L05366  
L05367  ! -------------------------------------------------------------------
L05368  !Based on the 
L05369  !paper of J.Karlsson and A.Roos(2000):"modelling the angular behaviour
L05370  !of the total solar energy transmittance of windows"
L05371  !Solar Energy Vol.69,No.4,pp. 321-329.      
L05372  ! -------------------------------------------------------------------
L05373  !Input
L05374  !-----	
L05375          
L05376  !Output
L05377  !------
L05378           real albwin	        ! albedo of the window  
L05379  !Local
L05380  !-----
L05381  	 real a,b,c		!Polynomial coefficients
L05382  	 real alfa,delta,gama	!Polynomial powers
L05383  	 real g0	        !transmittance when the angle 
L05384                                  !of incidence is normal to the surface.
L05385           real asup,ainf
L05386  	 real fonc
L05387  
L05388  !Constants
L05389  !--------------------
L05390           
L05391           real epsilon              !accuracy of the integration
L05392           parameter (epsilon=1.e-07) 
L05393           real n1,n2                !Index of refraction for glasses and air
L05394           parameter(n1=1.,n2=1.5)
L05395           integer intg,k
L05396  !--------------------------------------------------------------------		
L05397           if (q_num.eq.0) then
L05398             write(*,*) 'Category parameter of the windows no valid'
L05399             stop
L05400           endif
L05401  
L05402           g0=4.*n1*n2/((n1+n2)*(n1+n2))
L05403  	 a=8.
L05404  	 b=0.25/q_num
L05405           c=1.-a-b	
L05406  	 alfa =5.2 + (0.7*q_num)
L05407  	 delta =2.
L05408  	 gama =(5.26+0.06*p_num)+(0.73+0.04*p_num)*q_num
L05409  
L05410           intg=1
L05411  !----------------------------------------------------------------------
L05412  
L05413  
L05414  100      asup=0.
L05415           ainf=0.
L05416  
L05417           do k=1,intg
L05418            call foncs(fonc,(pi*k/intg),a,b,c,alfa,delta,gama)
L05419            asup=asup+(pi/intg)*fonc
L05420           enddo
L05421  
L05422           intg=intg+1
L05423  
L05424           do k=1,intg
L05425            call foncs(fonc,(pi*k/intg),a,b,c,alfa,delta,gama)
L05426            ainf=ainf+(pi/intg)*fonc
L05427           enddo
L05428  	 
L05429           if(abs(asup-ainf).lt.epsilon) then
L05430             albwin=1-g0+(g0/2.)*asup
L05431           else
L05432             goto 100
L05433           endif
L05434          
L05435  !---------------------------------------------------------------------- 	
L05436  	return
L05437  	end subroutine albwindow
```

<!-- code_extract code_extract.py v1.2
source: phys/module_sf_bep_bem.F
ranges: L5441-L5454
file_lines: 5706
file_md5: 8d13861f088e806d2558dd37e31126f2
display: line-numbered (strip L-prefix and !file: line to restore)
range_md5: 5c4c1b3eeec5b1d31bdf4c25eacb2486
seg_lines: 14
label: subroutine foncs
-->

```fortran
!file: phys/module_sf_bep_bem.F    L5441-L5454    (subroutine foncs)
L05441          subroutine foncs(fonc,x,aa,bb,cc,alf,delt,gam)
L05442  
L05443          implicit none
L05444  !
L05445          real x,aa,bb,cc
L05446          real alf,delt,gam
L05447          real fonc
L05448    
L05449          fonc=(((aa*(x**alf))/(pi**alf))+   &
L05450               ((bb*(x**delt))/(pi**delt))+  &
L05451               ((cc*(x**gam))/(pi**gam)))*sin(x)
L05452          
L05453          return
L05454  	end subroutine foncs
```

> 讲解：Karlsson–Roos 2000 窗户角向反射模型：三段幂多项式（a=8、b=0.25/q_num、c=1−a−b，指数 alfa/delta/gama 由玻璃层数 p_num 与类别 q_num 定）的 sin 加权积分，自适应步长直到相邻两次积分差 <1e-7；g0=4n₁n₂/(n₁+n₂)² 是法向透射（n₁=1 空气、n₂=1.5 玻璃）。只在 init_para 调一次。

<!-- code_extract code_extract.py v1.2
source: phys/module_sf_bep_bem.F
ranges: L5458-L5514
file_lines: 5706
file_md5: 8d13861f088e806d2558dd37e31126f2
display: line-numbered (strip L-prefix and !file: line to restore)
range_md5: 370fc3cd6e8bc82119dff234345e152c
seg_lines: 57
label: subroutine icBEP_XY
-->

```fortran
!file: phys/module_sf_bep_bem.F    L5458-L5514    (subroutine icBEP_XY)
L05458        subroutine icBEP_XY(iurb,fww_u,fwg_u,fgw_u,fsw_u,             &
L05459                            fws_u,fsg_u,ndu,strd,ws,nzu,z_u)                               
L05460  
L05461        implicit none       
L05462          
L05463  !    Street parameters
L05464        integer ndu     ! Number of street direction for each urban class
L05465        integer iurb
L05466  
L05467        real strd(ndm)        ! Street length (fix to greater value to the horizontal length of the cells)
L05468        real ws(ndm)          ! Street width [m]
L05469  
L05470  !    Grid parameters
L05471        integer nzu          ! Number of layer in the urban grid
L05472        real z_u(nz_um)       ! Height of the urban grid levels
L05473  ! -----------------------------------------------------------------------
L05474  !     Output
L05475  !------------------------------------------------------------------------
L05476  
L05477  !   fww_u,fwg_u,fgw_u,fsw_u,fsg_u are the view factors used to compute the long wave
L05478  !   and the short wave radation. They are the part of radiation from a surface
L05479  !   or from the sky to another surface.
L05480  
L05481        real fww_u(nz_um,nz_um,ndm,nurbm)         !  from wall to wall
L05482        real fwg_u(nz_um,ndm,nurbm)               !  from wall to ground
L05483        real fgw_u(nz_um,ndm,nurbm)               !  from ground to wall
L05484        real fsw_u(nz_um,ndm,nurbm)               !  from sky to wall
L05485        real fws_u(nz_um,ndm,nurbm)               !  from sky to wall
L05486        real fsg_u(ndm,nurbm)                     !  from sky to ground
L05487  
L05488  ! -----------------------------------------------------------------------
L05489  !     Local
L05490  !------------------------------------------------------------------------
L05491  
L05492        integer id
L05493  
L05494  ! -----------------------------------------------------------------------
L05495  !     This routine compute the view factors
L05496  !------------------------------------------------------------------------
L05497  !
L05498  !Initialize
L05499  !
L05500        fww_u=0.
L05501        fwg_u=0.
L05502        fgw_u=0.
L05503        fsw_u=0.
L05504        fws_u=0.
L05505        fsg_u=0.
L05506        
L05507        do id=1,ndu
L05508  
L05509              call view_factors(iurb,nzu,id,strd(id),z_u,ws(id),  &    
L05510                                fww_u,fwg_u,fgw_u,fsg_u,fsw_u,fws_u) 
L05511        
L05512        enddo               
L05513        return       
L05514        end subroutine icBEP_XY
```

<!-- code_extract code_extract.py v1.2
source: phys/module_sf_bep_bem.F
ranges: L5517-L5634
file_lines: 5706
file_md5: 8d13861f088e806d2558dd37e31126f2
display: line-numbered (strip L-prefix and !file: line to restore)
range_md5: 34f43bc83cf487a8452c473c034164e4
seg_lines: 118
label: subroutine icBEPHI_XY
-->

```fortran
!file: phys/module_sf_bep_bem.F    L5517-L5634    (subroutine icBEPHI_XY)
L05517        subroutine icBEPHI_XY(iurb,hb_u,hi_urb1D,ss_u,pb_u,nzu,z_u)
L05518  
L05519        implicit none   
L05520  !-----------------------------------------------------------------------
L05521  !    Inputs
L05522  !-----------------------------------------------------------------------
L05523  !    Street parameters
L05524  !
L05525        real hi_urb1D(nz_um)    ! The probability that a building has an height h_b
L05526        integer iurb            ! Number of the urban class
L05527  !
L05528  !     Grid parameters
L05529  !
L05530        real z_u(nz_um)         ! Height of the urban grid levels
L05531  ! -----------------------------------------------------------------------
L05532  !     Output
L05533  !------------------------------------------------------------------------
L05534  
L05535        real ss_u(nz_um,nurbm)  ! The probability that a building has an height equal to z
L05536        real pb_u(nz_um)        ! The probability that a building has an height greater or equal to z
L05537  !        
L05538  !    Grid parameters
L05539  !
L05540        integer nzu                ! Number of layer in the urban grid
L05541  
L05542  ! -----------------------------------------------------------------------
L05543  !     Local
L05544  !------------------------------------------------------------------------
L05545        real hb_u(nz_um)        ! Bulding's heights [m]
L05546        integer iz_u,id,ilu
L05547  
L05548        real dtot
L05549        real hbmax
L05550  
L05551  !------------------------------------------------------------------------
L05552  
L05553  !Initialize variables
L05554  !
L05555        
L05556        nzu=0
L05557        ss_u=0.
L05558        pb_u=0.
L05559        
L05560  ! Normalisation of the building density
L05561  
L05562           dtot=0.
L05563           hb_u=0.
L05564  
L05565           do ilu=1,nz_um
L05566              dtot=dtot+hi_urb1D(ilu)
L05567           enddo
L05568  
L05569           do ilu=1,nz_um
L05570              if (hi_urb1D(ilu)<0.) then
L05571  !              write(*,*) 'WARNING, HI_URB1D(ilu) < 0 IN BEP_BEM'
L05572                 go to 20
L05573              endif
L05574           enddo
L05575  
L05576           if (dtot.gt.0.) then
L05577              continue
L05578           else
L05579  !           write(*,*) 'WARNING, HI_URB1D <= 0 IN BEP_BEM'
L05580              go to 20
L05581           endif
L05582  
L05583           do ilu=1,nz_um
L05584              hi_urb1D(ilu)=hi_urb1D(ilu)/dtot
L05585           enddo
L05586           
L05587           hb_u(1)=dz_u   
L05588           do ilu=2,nz_um
L05589              hb_u(ilu)=dz_u+hb_u(ilu-1)
L05590           enddo
L05591             
L05592  
L05593  ! Compute pb and ss 
L05594        
L05595              
L05596           hbmax=0.
L05597         
L05598           do ilu=1,nz_um
L05599              if (hi_urb1D(ilu)>0.and.hi_urb1D(ilu)<=1.) then
L05600                  hbmax=hb_u(ilu)
L05601              endif
L05602           enddo
L05603           
L05604           do iz_u=1,nz_um-1
L05605              if(z_u(iz_u+1).gt.hbmax)go to 10
L05606           enddo
L05607  
L05608  10       continue 
L05609          
L05610           nzu=iz_u+1
L05611        
L05612           if ((nzu+1).gt.nz_um) then 
L05613               write(*,*) 'error, nz_um has to be increased to at least',nzu+1
L05614               stop
L05615           endif
L05616  
L05617              do iz_u=1,nzu
L05618                 ss_u(iz_u,iurb)=0.
L05619                 do ilu=1,nz_um
L05620                    if(z_u(iz_u).le.hb_u(ilu)                      &    
L05621                      .and.z_u(iz_u+1).gt.hb_u(ilu))then            
L05622                          ss_u(iz_u,iurb)=ss_u(iz_u,iurb)+hi_urb1D(ilu)
L05623                    endif 
L05624                 enddo
L05625              enddo
L05626  
L05627              pb_u(1)=1.
L05628              do iz_u=1,nzu
L05629                 pb_u(iz_u+1)=max(0.,pb_u(iz_u)-ss_u(iz_u,iurb))
L05630              enddo
L05631  
L05632  20     continue    
L05633         return
L05634         end subroutine icBEPHI_XY
```

> 讲解：两个逐点初始化单元：icBEP_XY 逐方向调 view_factors 算该点的视野因子（strd 固定 1e5 m——街道长取超长，即「无限长峡谷」近似）；icBEPHI_XY 把**该格点**的建筑高度直方图 hi_urb2d 归一化（dtot>0 与负值检查，异常静默跳过 goto 20——不重算 ss/pb，沿用类谱），再按楼高折层得 ss/pb。BEF 逐格化（BEP⇄BEM 差异之一）就发生在这里。

<!-- code_extract code_extract.py v1.2
source: phys/module_sf_bep_bem.F
ranges: L5639-L5705
file_lines: 5706
file_md5: 8d13861f088e806d2558dd37e31126f2
display: line-numbered (strip L-prefix and !file: line to restore)
range_md5: 83d1a227a39eacfb84d87bb94b1ea380
seg_lines: 67
-->

```fortran
!file: phys/module_sf_bep_bem.F    L5639-L5705
L05639  ! ===6=8===============================================================72
L05640  ! ===6=8===============================================================72
L05641  
L05642        FUNCTION bep_bem_nurbm () RESULT (bep_bem_val_nurbm)
L05643           USE module_sf_bep_bem
L05644           IMPLICIT NONE
L05645           INTEGER :: bep_bem_val_nurbm
L05646           bep_bem_val_nurbm = nurbm
L05647        END FUNCTION bep_bem_nurbm
L05648  
L05649        FUNCTION bep_bem_ndm () RESULT (bep_bem_val_ndm)
L05650           USE module_sf_bep_bem
L05651           IMPLICIT NONE
L05652           INTEGER :: bep_bem_val_ndm
L05653           bep_bem_val_ndm = ndm
L05654        END FUNCTION bep_bem_ndm
L05655  
L05656        FUNCTION bep_bem_nz_um () RESULT (bep_bem_val_nz_um)
L05657           USE module_sf_bep_bem
L05658           IMPLICIT NONE
L05659           INTEGER :: bep_bem_val_nz_um
L05660           bep_bem_val_nz_um = nz_um
L05661        END FUNCTION bep_bem_nz_um
L05662  
L05663        FUNCTION bep_bem_ng_u () RESULT (bep_bem_val_ng_u)
L05664           USE module_sf_bep_bem
L05665           IMPLICIT NONE
L05666           INTEGER :: bep_bem_val_ng_u
L05667           bep_bem_val_ng_u = ng_u
L05668        END FUNCTION bep_bem_ng_u
L05669  
L05670        FUNCTION bep_bem_nwr_u () RESULT (bep_bem_val_nwr_u)
L05671           USE module_sf_bep_bem
L05672           IMPLICIT NONE
L05673           INTEGER :: bep_bem_val_nwr_u
L05674           bep_bem_val_nwr_u = nwr_u
L05675        END FUNCTION bep_bem_nwr_u
L05676  
L05677        FUNCTION bep_bem_nf_u () RESULT (bep_bem_val_nf_u)
L05678           USE module_sf_bep_bem
L05679           IMPLICIT NONE
L05680           INTEGER :: bep_bem_val_nf_u
L05681           bep_bem_val_nf_u = nf_u
L05682        END FUNCTION bep_bem_nf_u
L05683  
L05684  
L05685        FUNCTION bep_bem_ngb_u () RESULT (bep_bem_val_ngb_u)
L05686           USE module_sf_bep_bem
L05687           IMPLICIT NONE
L05688           INTEGER :: bep_bem_val_ngb_u
L05689           bep_bem_val_ngb_u = ngb_u
L05690        END FUNCTION bep_bem_ngb_u
L05691  
L05692        FUNCTION bep_bem_nbui_max () RESULT (bep_bem_val_nbui_max)
L05693           USE module_sf_bep_bem
L05694           IMPLICIT NONE
L05695           INTEGER :: bep_bem_val_nbui_max
L05696           bep_bem_val_nbui_max = nbui_max
L05697        END FUNCTION bep_bem_nbui_max
L05698  
L05699   
L05700     FUNCTION bep_bem_ngr_u () RESULT (bep_bem_val_ngr_u)
L05701           USE module_sf_bep_bem
L05702           IMPLICIT NONE
L05703           INTEGER :: bep_bem_val_ngr_u
L05704           bep_bem_val_ngr_u = ngr_u
L05705        END FUNCTION bep_bem_ngr_u
```

> 讲解：模块外的九个宿主关联查询函数（bep_bem_nurbm/ndm/nz_um/ng_u/nwr_u/nf_u/ngb_u/nbui_max/ngr_u）——把本模块的 parameter 常量以函数形式暴露给 Registry 生成代码与外部模块做数组维度声明（Fortran 模块变量的跨模块只读访问惯例）。改维度常数（如 nz_um=18）后这组函数自动跟随，但**城市态数组维度在 Registry 的 urban_map_* 尺寸必须同步**（namelist num_urban_layers ≥ nz_um，init_para 的守卫会拦）。

## 八、改造入口

1. **辐射量计算性能**：long_rad/short_rad_dd 的 37×37 线性系统每点每步两解——灰区降尺度或大域时先测这里；可行方向：视野因子按类缓存（ws/strd 逐点变化才被迫逐点算）。
2. **导热分层**：param/surf_temp/roof_temp_veg 三处厚度数组 + soil_temp/soil_temp_veg 的求解器——改墙体结构三处同步。
3. **绿屋顶/PV**：roof_temp_veg 水力参数 + flux_flat_roof 气孔阻抗 + upward_rad 的 PV 常数（0.79/0.11）+ init_para 的 TBL 项。
4. **遗留代码**：flux_flat_ground 无调用方（勿改）；upward_rad 的硬 stop 哨兵建议替换。
5. **论文 2 对接**：ind_* 索引折叠表与 urban_map_* 维度是「标量→逐格场」的先例机制（notes 已录 vbs/br 先例）；BEM 主体改造见 code_16。

## 九、上下游链接

- 上半（主入口与柱求解器）：[code_14a_module_sf_bep_bem.md](code_14a_module_sf_bep_bem.md)
- 同族：[code_15_module_sf_bep.md](code_15_module_sf_bep.md)、[code_16_module_sf_bem.md](code_16_module_sf_bem.md)；参数库 module_sf_urban（code_17 篇待交付）
- 驱动链：[code_22_module_pbl_driver.md](code_22_module_pbl_driver.md)；面层 [code_10_module_sf_mynnsfc.md](code_10_module_sf_mynnsfc.md)
- 教材正文：[ch17_urban_canopy.md](../ch17_urban_canopy.md)、[ch19_lanzhou_heatwave.md](../ch19_lanzhou_heatwave.md)、[ch20_modifying_wrf.md](../ch20_modifying_wrf.md)
