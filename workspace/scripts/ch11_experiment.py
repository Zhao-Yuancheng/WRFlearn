"""ch11 实验：大气成分、湿度参量与饱和水汽压（书 §2.2 ↔ WRF 源码）

四组核对：
  A. 湿度参量互换闭合性（书 2.2.1–2.2.16：r/q/e/ρv/U/Td）
  B. 饱和水汽压实现对比（书 Tetens/马格纳斯/Bolton/戈夫-格雷奇 vs
     WRF: SVP1-4 Bolton、pq0 Murray、WSM6 fpvs 内联、Thompson RSLF/RSIF 多项式、MM5 三段式）
  C. 虚温/湿空气密度/湿比热（书 2.2.17–2.2.22 vs module_model_constants、module_sf_sfclay）
  D. 兰州实测：met_em（RH 驱动）→ real.exe 路径（rh_to_mxrat1 默认 rh2qv_method=1）
     → 与 wrfinput QVAPOR 对照

数据：workspace/data/ch10/met_em.d01.2025-07-12_00.nc、wrfinput_d01.nc
输出：doc/figs/ch11_es_curves.png、ch11_real_data_check.png、ch11_virtual_temp.png
"""
import numpy as np
from pathlib import Path
from netCDF4 import Dataset

ROOT = Path(r"d:\Code\Learn\WRF")
DATA = ROOT / "workspace" / "data" / "ch10"
FIGS = ROOT / "doc" / "figs"
FIGS.mkdir(parents=True, exist_ok=True)

# ----------------------------------------------------------------------------
# 常数：WRF share/module_model_constants.F（左）与书（右，注明出处）
# ----------------------------------------------------------------------------
RD   = 287.0        # r_d          | 书 Rd = 287.05 J/(kg·K)（印刷页 8）
RV   = 461.6        # r_v          | 由 ε=0.622 反推书值 ≈ 461.5
EPS  = 0.622        # EP_2 = Rd/Rv | 书 ε = Mv/Md = 0.622（印刷页 20）
CP   = 7.*RD/2.     # cp = 1004.5  | 书 c_pd = 1004 J/(kg·K)（印刷页 9）
CPV  = 4.*RV        # cpv = 1846.4
CLIQ = 4190.0       # cliq
CICE = 2106.0       # cice
PSAT = 610.78       # psat [Pa]    | 书 6.1078 hPa（Tetens 系数，印刷页 21）
T0C  = 273.15       # 微物理中的 0℃
SVP1, SVP2, SVP3, SVPT0 = 0.6112, 17.67, 29.65, 273.15   # [kPa] Bolton
PQ0, A2, A3, A4 = 379.90516, 17.2693882, 273.16, 35.86   # Murray（calc_rh）
CM1, CM2, CM3 = 2937.4, 4.9283, 23.5518                  # 马格纳斯（(2.2.8a)）
EP1  = RV/RD - 1.   # 0.608 —— 虚温系数（书 (2.2.20)）
XLV, XLS, XLF = 2.5e6, 2.85e6, 3.5e5                     # 0℃ 潜热

# ============================================================================
# A. 湿度参量互换闭合性（书 §2.2.1）
# ============================================================================
print("="*78)
print("A. 湿度参量互换闭合性（兰州盛夏典型值：T=25℃, p=1000 hPa, q=12 g/kg）")
print("="*78)

def q_to_r(q):  return q/(1.0-q)                    # q=r/(1+r) 之逆（书 (2.2.2)）
def r_to_q(r):  return r/(1.0+r)                    # (2.2.2)
def r_to_e(r,p): return r*p/(EPS+r)                 # 由 (2.2.3) χ=r/(ε+r)
def e_to_r(e,p): return EPS*e/(p-e)                 # (2.2.4)
def e_to_q(e,p): return EPS*e/(p-0.378*e)           # (2.2.5)
def rho_v(e,T):  return e*100.0/(RV*T)              # (2.2.14) e[hPa]->Pa
def rho_v2(e,T): return EPS*e*100.0/(RD*T)          # (2.2.14) 等价写法

T, p, q = 298.15, 1000.0, 0.012
r = q_to_r(q)
e = r_to_e(r, p)
rho1 = rho_v(e, T); rho2 = rho_v2(e, T)

print(f"输入: T={T-273.15:.1f} C, p={p:.1f} hPa, q={q*1000:.2f} g/kg")
print(f"  r  = {r*1000:.4f} g/kg")
print(f"  e  = {e:.4f} hPa")
print(f"  rho_v = {rho1:.4f} g/m3  (两种写法一致: |diff|={abs(rho1-rho2):.2e})")

def es_bolton_hPa(T):
    t = T - 273.15
    return 6.112*np.exp(17.67*t/(t+243.5))          # 书 (2.2.11)

U = e/es_bolton_hPa(T)*100.0
# Td：反转 Bolton —— es(Td)=e
LnU = np.log(e/6.112)
Td = 273.15 + 243.5*LnU/(17.67-LnU)
print(f"  U  = {U:.2f} %")
print(f"  Td = {Td-273.15:.3f} C  （验证 es(Td)={es_bolton_hPa(Td):.5f} hPa vs e={e:.5f} hPa）")

# 闭合性：正逆互换
e_r = r_to_e(e_to_r(e, p), p)          # e -> r -> e
e_q = p*q/(EPS+0.378*q)                # (2.2.5) 之逆
q_e = e_to_q(e_q, p)                   # q -> e -> q
print(f"  (2.2.1/2.2.2) r→q→r 闭合 |err| = {abs((q_to_r(r_to_q(r))-r)/r):.2e}")
print(f"  (2.2.4) e→r→e 闭合 |err| = {abs((e_r-e)/e):.2e}")
print(f"  (2.2.5) q→e→q 闭合 |err| = {abs((q_e-q)/q):.2e}")

# 饱和参量（qs, rs）与 U 近似式核对（书 (2.2.12)、(2.2.16)）
es25 = es_bolton_hPa(T)
qs = EPS*es25/(p-0.378*es25); rs = EPS*es25/(p-es25)
U_from_q = q/qs*100.0
U_from_r = (r/(EPS+r))/(rs/(EPS+rs))*100.0
print(f"  饱和: es(25C)={es25:.4f} hPa, qs={qs*1000:.4f} g/kg, rs={rs*1000:.4f} g/kg")
print(f"  U 三种算法: e/es={U:.3f}%  q/qs={U_from_q:.3f}%  (2.2.16)={U_from_r:.3f}%")

# ============================================================================
# B. 饱和水汽压实现对比（书 §2.2.1 三、四 vs WRF 四处实现）
# ============================================================================
print()
print("="*78)
print("B. 饱和水汽压实现对比（水面 + 冰面）")
print("="*78)

# ---- 书 ----
def es_tetens_water(T):   # (2.2.9a) Murray/Tetens 水面 [hPa]
    return 6.1078*np.exp(17.2693882*(T-273.16)/(T-35.86))
def es_tetens_ice(T):     # (2.2.9b) [hPa]；参考温度 273.16 K（书表 2.5(b) 反证：
    #   0℃ 时 e_si=6.107 hPa、(2.2.9b) 取 273.16 时 e_si(-10℃)=2.593 与表 2.5(b) 2.597 一致）
    return 6.1078*np.exp(21.8745584*(T-273.16)/(T-7.66))

# ---- WRF 实现 1：SVP1-4（Bolton，module_model_constants；sfclay/多数方案）
def es_svp(T):  return 10.0*SVP1*np.exp(SVP2*(T-SVPT0)/(T-SVP3))  # hPa

# ---- WRF 实现 2：pq0/a2/a3/a4（Murray，module_diag_functions:calc_rh）
def es_pq0(T):  return 0.01*610.78*np.exp(A2*(T-A3)/(T-A4))       # hPa

# ---- WRF 实现 3：WSM6 fpvs 内联（CC 方程 + 线性 Lv(T)）
def es_wsm6(T):
    ttp = T0C + 0.01; tr = ttp/T
    xa = -(CPV-CLIQ)/RV;  xb = xa + XLV/(RV*ttp)
    return PSAT*np.exp(np.log(tr)*xa)*np.exp(xb*(1.0-tr))         # Pa
def es_wsm6_ice(T):
    ttp = T0C + 0.01; tr = ttp/T
    xai = -(CPV-CICE)/RV; xbi = xai + XLS/(RV*ttp)
    return PSAT*np.exp(np.log(tr)*xai)*np.exp(xbi*(1.0-tr))       # Pa

# ---- WRF 实现 4：Thompson RSLF/RSIF 八阶多项式（Flatau 拟合）
C_L = [.611583699E03,.444606896E02,.143177157E01,.264224321E-1,.299291081E-3,
       .203154182E-5,.702620698E-8,.379534310E-11,-.321582393E-13]
C_I = [.609868993E03,.499320233E02,.184672631E01,.402737184E-1,.565392987E-3,
       .521693933E-5,.307839583E-7,.105785160E-9,.161444444E-12]
def _poly(c, x):
    y = c[8]
    for k in range(7, -1, -1):
        y = c[k] + x*y
    return y
def es_thomp_water(T):    # Pa
    x = np.maximum(-80.0, T-273.16); return _poly(C_L, x)
def es_thomp_ice(T):
    x = np.maximum(-80.0, T-273.16); return _poly(C_I, x)

# ---- WRF 实现 5：MM5 三段式（rh_to_mxrat1，real.exe 默认路径）
def es_mm5(T):            # t >= 0C: A0..A6 多项式；-47~0C: Bolton；< -47C: 戈夫-格雷奇冰面
    t1 = T - 273.16
    out = np.empty_like(np.asarray(T, dtype=float))
    A = [6.107799961, 4.436518521e-01, 1.428945805e-02, 2.650648471e-04,
         3.031240396e-06, 2.034080948e-08, 6.136820929e-11]
    m0 = t1 >= 0.0
    out[m0] = _poly2(A, t1[m0])
    m1 = (t1 < 0.0) & (t1 >= -47.0)
    out[m1] = 6.1121*np.exp(17.67*t1[m1]/(t1[m1]+243.5))
    m2 = t1 < -47.0
    tf = 273.16; tk = T[m2]
    c1, c2, c3, eis = 9.09718, 3.56654, 0.876793, 6.1071
    rhs = -c1*(tf/tk-1.0) - c2*np.log10(tf/tk) + c3*(1.0-tk/tf) + np.log10(eis)
    out[m2] = 10.0**rhs
    return out
def _poly2(a, x):
    y = a[6]
    for k in range(5, -1, -1):
        y = a[k] + x*y
    return y

# 对比表（水面）
Ts = [273.15+dd for dd in (-40,-30,-20,-12,-10,-5,0,10,20,25,30,40)]
print(f"{'T(C)':>5} | {'书Tetens':>9} {'SVP1-4':>9} {'pq0':>9} {'WSM6':>9} {'Thomp':>9} {'MM5':>9} | 相对书Tetens(spread %)")
print("-"*100)
maxrel = 0.0
for T in Ts:
    vals = [es_tetens_water(T), es_svp(T), es_pq0(T), es_wsm6(T)/100.0,
            es_thomp_water(T)/100.0, float(es_mm5(np.array([T]))[0])]
    rel = [(v-vals[0])/vals[0]*100 for v in vals]
    spread = max(rel)-min(rel)
    maxrel = max(maxrel, spread)
    print(f"{T-273.15:5.0f} | {vals[0]:9.4f} {vals[1]:9.4f} {vals[2]:9.4f} {vals[3]:9.4f} {vals[4]:9.4f} {vals[5]:9.4f} | spread {spread:7.3f}")
print(f"水面各实现最大差异（相对）：{maxrel:.3f} %")

# 冰面 + 贝吉龙（冰水差最大值温度）
print()
print("冰面饱和水汽压（hPa）：书Tetens-ice / WSM6-ice / Thompson-ice / MM5三段式（-47℃ 以下才转戈夫-格雷奇冰面式）")
for T in [273.15+dd for dd in (-50,-30,-20,-15,-12,-10,-5,0)]:
    v = [es_tetens_ice(T), es_wsm6_ice(T)/100.0, es_thomp_ice(T)/100.0,
         float(es_mm5(np.array([T]))[0])]
    print(f"{T-273.15:5.0f} | {v[0]:9.4f} {v[1]:9.4f} {v[2]:9.4f} {v[3]:9.4f}")

tt = np.linspace(233.15, 273.15, 2001)
d_es = es_tetens_water(tt) - es_tetens_ice(tt)
i_max = np.argmax(d_es)
print(f"\n贝吉龙核对（书图 2.6）：冰-水面饱和水汽压之差 Δes 在 T={tt[i_max]-273.15:.1f}℃ 最大"
      f"（Δes={d_es[i_max]:.3f} hPa）")

# ============================================================================
# C. 虚温 / 湿空气密度 / 湿比热（书 §2.2.2）
# ============================================================================
print()
print("="*78)
print("C. 虚温、湿空气密度与湿比热（书 (2.2.17)–(2.2.22) vs WRF 常数）")
print("="*78)

def Tv(T, q):        return (1.0+EP1*q)*T           # 书 (2.2.20) 与 WRF EP_1
def dTv(T, q):       return EP1*q*T                 # 订正量；书等价式 0.378(e/p)T
def rho_moist(T, p, q):    # 书 (2.2.19)
    return p*100.0/(RD*T*(1.0+0.608*q))
def rho_exact(T, p, q):    # 精确式（用 ε 的等价解析式，Thompson 用的 0.622 因子式）
    r = q/(1.0-q)
    return EPS*(1.0+r)*p*100.0/((EPS+r)*RD*T)

for T_c in (270.0, 290.0, 303.15, 313.15):
    for q_g in (5, 20):
        q = q_g/1000.0
        print(f"  T={T_c-273.15:5.1f}C q={q_g:2d} g/kg -> dTv={dTv(T_c,q):6.3f} K, "
              f"Tv={Tv(T_c,q):7.3f} K, rho 书/精确差={abs(rho_moist(T_c,1000.,q)-rho_exact(T_c,1000.,q))/rho_exact(T_c,1000.,q)*100:5.4f}%")

q20 = 0.02
cp_book = CP*(1.0+0.86*q20)      # (2.2.21)
cp_sfclay = 1004.5*(1.0+0.8*q20) # module_sf_sfclay: CPM=CP*(1.+0.8*QX)
cpv_exact = (CP*(1-q20)+CPV*q20)/(1.0)  # 严格加权 (1-q)cpd + q cpv
print(f"  q=20 g/kg 湿比热: 书(2.2.21)={cp_book:.3f}  sfclay(1+0.8q)={cp_sfclay:.3f}  "
      f"严格(1-q)cpd+qcpv={CP*(1-q20)+CPV*q20:.3f} J/(kg K)")

# ============================================================================
# D. 兰州实测：met_em -> real.exe 路径 -> wrfinput QVAPOR 对照
# ============================================================================
print()
print("="*78)
print("D. 兰州实测对照（2025-07-12_00 UTC=08 BJT，met_em d01 -> wrfinput）")
print("="*78)

met = Dataset(DATA/"met_em.d01.2025-07-12_00.nc")
wrfin = Dataset(DATA/"wrfinput_d01.nc")

lat = met.variables["XLAT_M"][0]; lon = met.variables["XLONG_M"][0]
j0, i0 = np.unravel_index(np.argmin((lat-36.0)**2+(lon-103.75)**2), lat.shape)
print(f"格点: j={j0} i={i0} lat={float(lat[j0,i0]):.4f} lon={float(lon[j0,i0]):.4f}")
box = (slice(max(0,j0-2), j0+3), slice(max(0,i0-2), i0+3))

p_met = met.variables["PRES"][0, :, j0, i0]   # Pa
T_met = met.variables["TT"][0, :, j0, i0]     # K
RH_met = met.variables["RH"][0, :, j0, i0]    # %
GHT_met = met.variables["GHT"][0, :, j0, i0]  # m
print(f"met_em PRES: {p_met[0]:.1f}~{p_met[-1]:.1f} Pa, 单位属性='{met.variables['PRES'].units}'")

# real.exe 路径（rh_to_mxrat1，wrt_liquid=.true. 默认；es 用 SVP1-4 Bolton）
def rh2qv_real(rh, t, p_Pa):
    es = 0.01*rh*es_svp(t)              # 先按 RH 折减（hPa）——real.exe 同款写法
    p_hPa = p_Pa/100.0
    q = np.maximum(EPS*es/(p_hPa-es), 1.0e-6)
    return q                           # 混合比 kg/kg

q_met = rh2qv_real(RH_met, T_met, p_met)*1000.0   # g/kg

# wrfinput 列
j = j0; i = i0
latw = wrfin.variables["XLAT"][0]; lonw = wrfin.variables["XLONG"][0]
jw, iw = np.unravel_index(np.argmin((latw-36.0)**2+(lonw-103.75)**2), latw.shape)
print(f"wrfinput 格点: j={jw} i={iw} lat={float(latw[jw,iw]):.4f} lon={float(lonw[jw,iw]):.4f}")

qw  = wrfin.variables["QVAPOR"][0, :, jw, iw]
thw = wrfin.variables["T"][0, :, jw, iw] + 300.0
pw  = ((wrfin.variables["P"][0, :, jw, iw] + wrfin.variables["PB"][0, :, jw, iw]))
phb = wrfin.variables["PHB"][0, :, jw, iw]; ph = wrfin.variables["PH"][0, :, jw, iw]
zw = 0.5*(ph+phb)/9.81
zw = 0.5*(zw[:-1]+zw[1:])   # 中间层高度
Tw = thw*(pw/1.0e5)**(RD/CP)

# 将 wrf 廓线内插到 met_em 层次（log p 线性）
order_w = np.argsort(np.log(pw)); order_m = np.argsort(np.log(p_met))
qs_w = qw*1000.0
q_w_on_m = np.interp(np.log(p_met), np.log(pw)[order_w], qs_w[order_w])
T_w_on_m = np.interp(np.log(p_met), np.log(pw)[order_w], Tw[order_w])
RH_w_on_m = q_w_on_m/1000.0/(EPS*es_svp(T_w_on_m)/(p_met/100.0 - es_svp(T_w_on_m)))*100.0

d_q = q_w_on_m - q_met
psfc_met = float(met.variables["PSFC"][0, j0, i0])
valid = (p_met < psfc_met) & (p_met >= 1.0e4)   # 排除地面伪层与地形以下层
print()
print(f"层次对比（met_em：k=0 为地面伪层，k=1~8 在该点地形以下（PSFC={psfc_met/100:.1f} hPa），已排除）：")
print(f"{'k':>3} {'p(hPa)':>8} {'z(m)':>7} | {'RH_met(%)':>9} {'q_met(g/kg)':>11} {'q_wrf(g/kg)':>11} {'dq(g/kg)':>9} {'RH_wrf(%)':>9}")
for k in (10, 12, 14, 16, 20, 24, 28, 31):
    print(f"{k:3d} {p_met[k]/100.0:8.1f} {GHT_met[k]:7.0f} | {RH_met[k]:9.2f} {q_met[k]:11.4f} {q_w_on_m[k]:11.4f} {d_q[k]:9.4f} {RH_w_on_m[k]:9.2f}")

print(f"\n统计（地面以上、100 hPa 以下，{valid.sum()} 层）：dq 平均 {d_q[valid].mean():+.4f} g/kg，"
      f"RMS {np.sqrt((d_q[valid]**2).mean()):.4f} g/kg，最大 |dq| {abs(d_q[valid]).max():.4f} g/kg；"
      f"q 平均 {q_met[valid].mean():.3f} g/kg")
print(f"RH 对照：met_em RH 最大 {RH_met[valid].max():.1f} %，wrf 内插 RH 最大 {RH_w_on_m[valid].max():.1f} %")

# 场级统计：met_em 地面层 vs wrfinput 2m（在各自网格上取兰州城区附近，避免跨网格点对点比较）
q_sfc_met = rh2qv_real(np.array([RH_met[0]]), np.array([T_met[0]]), np.array([p_met[0]]))[0]*1000.0
print(f"met_em 地面伪层（k=0，=PSFC 层）：T={T_met[0]-273.15:.2f} C, RH={RH_met[0]:.1f}%, q={q_sfc_met:.3f} g/kg")

# wrfinput 自身饱和检查
qsat_w = EPS*es_svp(Tw)/(pw/100.0-es_svp(Tw))
RH_wrf_own = qw/qsat_w*100.0
print(f"wrfinput 自身柱饱和度检查：RH 最大 {RH_wrf_own.max():.2f} %（50 层），"
      f"超饱和层数 {(RH_wrf_own>100).sum()}")

# 地面
T2 = wrfin.variables["T2"][0, jw, iw]; Q2 = wrfin.variables["Q2"][0, jw, iw]
PSFC = wrfin.variables["PSFC"][0, jw, iw]
RH2 = Q2/(EPS*es_svp(T2)/(PSFC/100.0-es_svp(T2)))*100.0
print(f"地面（wrfinput）：T2={T2-273.15:.2f} C, Q2={Q2*1000:.3f} g/kg, PSFC={PSFC/100:.2f} hPa -> "
      f"RH2={RH2:.1f} %；met_em 最低层 RH={RH_met[0]:.1f} %")
met.close(); wrfin.close()

# ============================================================================
# 图
# ============================================================================
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
try:
    plt.rcParams["font.sans-serif"] = ["SimHei", "Microsoft YaHei"]
    plt.rcParams["axes.unicode_minus"] = False
except Exception:
    pass

# --- 图 1：es(T) 曲线 ---
Tc = np.linspace(-60, 40, 801); TT = Tc+273.15
fig, axes = plt.subplots(1, 3, figsize=(14.5, 4.6))
ax = axes[0]
ax.plot(Tc, es_tetens_water(TT), "k-", lw=1.8, label="水面：书 Tetens (2.2.9a)")
ax.plot(Tc, es_tetens_ice(TT), "k--", lw=1.8, label="冰面：书 Tetens (2.2.9b)")
ax.plot(Tc, es_svp(TT), "r-", lw=1.0, label="WRF SVP1-4 (Bolton)")
ax.plot(Tc, es_thomp_water(TT)/100.0, "b:", lw=1.5, label="Thompson RSLF 多项式")
ax.set_yscale("log"); ax.set_xlabel("T (℃)"); ax.set_ylabel("$e_s$ (hPa)")
ax.set_title("(a) 饱和水汽压曲线"); ax.legend(fontsize=7.5); ax.grid(alpha=0.3)

ax = axes[1]
for f, lab, st in [(es_svp, "SVP1-4 (Bolton)", "r-"), (es_pq0, "pq0 (Murray)", "g-"),
                   (lambda T: es_wsm6(T)/100.0, "WSM6 fpvs", "b--"),
                   (lambda T: es_thomp_water(T)/100.0, "Thompson 多项式", "m:"),
                   (es_bolton_hPa, "书 Bolton (2.2.11)", "k-.")]:
    ax.plot(Tc, (f(TT)-es_tetens_water(TT))/es_tetens_water(TT)*100.0, st, lw=1.3, label=lab)
ax.axhline(0, color="k", lw=0.6)
ax.set_xlabel("T (℃)"); ax.set_ylabel("相对偏差 (%)")
ax.set_title("(b) 各实现相对书 Tetens 水面式"); ax.legend(fontsize=7.5); ax.grid(alpha=0.3)
ax.set_ylim(-3, 3)

ax = axes[2]
Tc_ice = np.linspace(-60, 0, 601); TT_ice = Tc_ice+273.15
dabs = es_tetens_water(TT_ice) - es_tetens_ice(TT_ice)
imax_w = np.argmax(dabs)
ax.plot(Tc_ice, dabs, "k-", lw=1.8)
ax.axvline(Tc_ice[imax_w], color="r", ls=":", lw=1)
ax.annotate(f"最大差 {Tc_ice[imax_w]:.1f}℃\n(Δes={dabs[imax_w]:.3f} hPa)",
            (Tc_ice[imax_w], dabs[imax_w]), textcoords="offset points",
            xytext=(10, -12), fontsize=9, color="r")
ax.set_xlabel("T (℃)"); ax.set_ylabel("$e_{sw}-e_{si}$ (hPa)")
ax.set_title("(c) 冰-水面饱和水汽压差（贝吉龙，书图 2.6）"); ax.grid(alpha=0.3)
fig.tight_layout(); fig.savefig(FIGS/"ch11_es_curves.png", dpi=150)
print(f"\n图已存: {FIGS/'ch11_es_curves.png'}")

# --- 图 2：实测廓线 ---
mm = valid.copy(); mm[0] = True   # 保留地面伪层一个点
fig, axes = plt.subplots(1, 3, figsize=(13.5, 5.0), sharey=True)
ax = axes[0]
ax.plot(RH_met[mm], p_met[mm]/100.0, "k-o", ms=3, lw=1.2, label="met_em RH（驱动场）")
ax.plot(RH_w_on_m[mm], p_met[mm]/100.0, "r--s", ms=3, lw=1.2, label="wrf 内插 RH")
ax.plot([RH2], [PSFC/100.0], "r*", ms=11, label="wrfinput 2m")
ax.plot([RH_met[0]], [p_met[0]/100.0], "k*", ms=11, label="met_em 地面层")
ax.set_yscale("log"); ax.invert_yaxis(); ax.set_xlabel("RH (%)"); ax.set_ylabel("p (hPa)")
ax.set_title("(a) 相对湿度廓线（地形以下层已剔除）"); ax.legend(fontsize=7.5); ax.grid(alpha=0.3)
ax = axes[1]
ax.plot(q_met[mm], p_met[mm]/100.0, "k-o", ms=3, lw=1.2, label="met_em → q（real 路径）")
ax.plot(q_w_on_m[mm], p_met[mm]/100.0, "r--s", ms=3, lw=1.2, label="wrfinput QVAPOR")
ax.plot([Q2*1000], [PSFC/100.0], "r*", ms=11, label="wrfinput 2m")
ax.set_xlabel("q (g/kg)"); ax.set_title("(b) 混合比廓线"); ax.legend(fontsize=7.5); ax.grid(alpha=0.3)
ax = axes[2]
e_met = q_met/1000.0*(p_met/100.0)/(EPS+q_met/1000.0)
Ln_e = np.log(e_met/6.112)
Td_met = 243.5*Ln_e/(17.67-Ln_e)
e_w = q_w_on_m/1000.0*(p_met/100.0)/(EPS+q_w_on_m/1000.0)
Ln_ew = np.log(e_w/6.112); Td_w = 243.5*Ln_ew/(17.67-Ln_ew)
ax.plot(Td_met[mm], p_met[mm]/100.0, "k-o", ms=3, lw=1.2, label="met_em Td")
ax.plot(Td_w[mm], p_met[mm]/100.0, "r--s", ms=3, lw=1.2, label="wrf Td")
ax.set_xlabel("Td (℃)"); ax.set_title("(c) 露点廓线（Bolton 反解）"); ax.legend(fontsize=7.5); ax.grid(alpha=0.3)
fig.suptitle("兰州点（36.0N, 103.75E）2025-07-12 00 UTC：met_em 驱动 → wrfinput 水汽", y=0.98)
fig.tight_layout(); fig.savefig(FIGS/"ch11_real_data_check.png", dpi=150)
print(f"图已存: {FIGS/'ch11_real_data_check.png'}")

# --- 图 3：虚温/密度/比热 ---
fig, axes = plt.subplots(1, 3, figsize=(13.5, 4.4))
qq = np.linspace(0, 25, 251)/1000.0
ax = axes[0]
for Tc0, st in [(0, "b-"), (20, "g-"), (30, "r-")]:
    ax.plot(qq*1000, dTv(Tc0+273.15, qq), st, lw=1.5, label=f"T={Tc0}℃")
ax.set_xlabel("q (g/kg)"); ax.set_ylabel("$T_v-T$ (K)")
ax.set_title("(a) 虚温订正量 (2.2.20)"); ax.legend(fontsize=8); ax.grid(alpha=0.3)
ax = axes[1]
err = (rho_moist(300., 1000., qq)-rho_exact(300., 1000., qq))/rho_exact(300., 1000., qq)*100.0
ax.plot(qq*1000, err, "k-", lw=1.5)
ax.set_xlabel("q (g/kg)"); ax.set_ylabel("密度相对误差 (%)")
ax.set_title("(b) 书近似式 (2.2.19) vs 精确式"); ax.grid(alpha=0.3)
ax = axes[2]
cp_b = CP*(1+0.86*qq); cp_s = 1004.5*(1+0.8*qq); cp_e = CP*(1-qq)+CPV*qq
ax.plot(qq*1000, cp_b, "k-", lw=1.5, label="书 (2.2.21) (1+0.86q)")
ax.plot(qq*1000, cp_s, "r--", lw=1.5, label="sfclay (1+0.8q)")
ax.plot(qq*1000, cp_e, "b:", lw=1.5, label="严格加权")
ax.set_xlabel("q (g/kg)"); ax.set_ylabel("$c_p$ (J/kg/K)")
ax.set_title("(c) 湿空气比定压热容"); ax.legend(fontsize=8); ax.grid(alpha=0.3)
fig.tight_layout(); fig.savefig(FIGS/"ch11_virtual_temp.png", dpi=150)
print(f"图已存: {FIGS/'ch11_virtual_temp.png'}")
print("\n完成。")