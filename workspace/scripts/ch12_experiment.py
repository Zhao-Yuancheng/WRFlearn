"""ch12 实验：辐射（书第 5 章 ↔ WRF RRTMG）

六组核对：
  A. 四定律数值核验（书 5.2：普朗克/斯特藩-玻尔兹曼/维恩/基尔霍夫常数体系）
  B. RRTMG 谱段 vs 书之吸收带/大气窗（module_ra_rrtmg_lw/sw 16+14 波段）
  C. 太阳几何闭环：端口 radconst/calc_coszen ↔ wrfrst 状态量逐格对照
  D. 相对大气质量与光学厚度（书 5.4.3：m 公式与表 5.5 对照）
  E. 大气上界日总量 Qd（书 (5.4.14)，复现 1.37 倍结论）
  F. 两层温室模型（书 (5.6.4) 与表 5.16）+ CAMtr 温室气体 + O3RAD 实测

数据：workspace/data/wrfrst_d01_2025-07-12_00_05_24.nc（辐射状态量）
      source/WRFv4.8.0/WRFV4.8.0/run/{CAMtr_volume_mixing_ratio, ozone*.formatted}
输出：doc/figs/ch12_planck_bands.png、ch12_solar_geometry.png、ch12_ozone_ghg.png
      workspace/logs/ch12_experiment.log
"""
import numpy as np
from pathlib import Path
from netCDF4 import Dataset

ROOT = Path(r"d:\Code\Learn\WRF")
SRC = ROOT / "source" / "WRFv4.8.0" / "WRFV4.8.0"
RUN = SRC / "run"
DATA = ROOT / "workspace" / "data"
FIGS = ROOT / "doc" / "figs"
LOGS = ROOT / "workspace" / "logs"
FIGS.mkdir(parents=True, exist_ok=True)
LOGS.mkdir(parents=True, exist_ok=True)

log_lines = []
def log(msg=""):
    print(msg)
    log_lines.append(str(msg))

# ============================================================================
# A. 四定律数值核验
# ============================================================================
log("=" * 78)
log("A. 四定律数值核验（常数全部取自书 5.2，印刷页 68–70）")
log("=" * 78)

C1 = 3.7427e-16      # 第一辐射常数 W·m²（书 (5.2.6) 后文）
C2 = 14388.0         # 第二辐射常数 μm·K（书）
SIGMA_BOOK = 5.6696e-8   # σ（书 (5.2.10)）

def FB(lam, T):
    """黑体分光辐出度（书 (5.2.6)），lam 单位 μm，返回 W·m⁻²·μm⁻¹

    注意单位：c1 以 m 制定义（c1/λ⁵ 得到 W·m⁻²·m⁻¹），转 per-μm 需 ×1e-6；
    λ_μm = λ_m×1e6 ⇒ 1/λ_m⁵ = 1e30/λ_μm⁵ ⇒ 净因子 c1×1e24。
    """
    lam = np.asarray(lam, dtype=float)
    x = np.clip(C2 / (lam * T), 1e-8, 700)
    return C1 * 1.0e24 / lam ** 5 / np.expm1(x)

# A1. σ 由书常数导出：σ = π⁴ c1 / (15 c2⁴)（书 (5.2.10)）
sigma_calc = np.pi**4 * C1 / (15.0 * (C2 * 1e-6) ** 4)
log(f"A1  σ(推出) = {sigma_calc:.6e} W·m⁻²·K⁻⁴ ；书给 5.6696e-08")
log(f"    相对偏差 = {abs(sigma_calc - SIGMA_BOOK)/SIGMA_BOOK*100:.4f} %")

# A2. 斯特藩-玻尔兹曼：数值积分 ∫F_B dλ 与 σT⁴ 对比
log("-" * 78)
log("A2  斯特藩-玻尔兹曼检验：∫F_B(λ,T)dλ  （λ∈[0.01, 400] μm，对数网格 4e5 点）")
lam = np.exp(np.linspace(np.log(0.01), np.log(400.0), 400001))
for T in (5777.0, 6000.0, 300.0, 255.0, 220.0):
    integ = np.trapz(FB(lam, T), lam)
    stef = SIGMA_BOOK * T**4
    log(f"    T={T:6.0f} K：∫F_B dλ={integ:12.4e}  σT⁴={stef:12.4e}  相对差={abs(integ-stef)/stef*100:.4f} %")

# A3. 维恩位移：数值 argmax 与 2897.8/T（书 (5.2.13)）及表 5.2 对照
log("-" * 78)
log("A3  维恩位移：数值 λmax vs 2897.8/T vs 书表 5.2")
lam_w = np.linspace(0.05, 60.0, 600001)
tab = {10000: 0.290, 6000: 0.483, 3000: 0.964, 1500: 1.923, 1000: 2.911,
       500: 5.808, 300: 9.638, 280: 10.375, 220: 13.183}
for T in (10000, 6000, 3000, 1500, 1000, 500, 300, 280, 220):
    lm = lam_w[np.argmax(FB(lam_w, T))]
    wien = 2897.8 / T
    book = tab[T]
    log(f"    T={T:6d} K：数值 {lm:6.3f} μm ；2897.8/T {wien:6.3f} ；书表 5.2 {book:6.3f}"
        f"  （数值-书 {abs(lm-book)*1000:.1f} nm）")

# A4. 基尔霍夫/比辐射率：黑体 B=F_B/π（书 (5.2.7)），对照表 5.2 第二列
log("-" * 78)
log("A4  黑体分光辐亮度 B(λmax,T)=F_B/π 与书表 5.2 第二列对照：")
B_tab = {10000: 4.095e8, 6000: 3.185e7, 3000: 9.952e5, 1500: 3.110e4, 1000: 4.095e3,
         500: 1.280e2, 300: 9.852, 280: 7.048, 260: 4.866, 240: 3.261, 220: 2.111}
for T, bbook in B_tab.items():
    lmax = 2897.8 / T
    bcalc = FB(lmax, T) / np.pi
    log(f"    T={T:6d} K：B(λmax)={bcalc:10.4g}  书表 5.2={bbook:10.4g}  "
        f"相对差={abs(bcalc-bbook)/bbook*100:5.2f} %")

# ============================================================================
# B. RRTMG 谱段 vs 书之吸收带/大气窗
# ============================================================================
log()
log("=" * 78)
log("B. RRTMG 谱段（源码实测）vs 书之吸收带/大气窗")
log("=" * 78)

LW_WN1 = np.array([10, 350, 500, 630, 700, 820, 980, 1080, 1180, 1390, 1480,
                   1800, 2080, 2250, 2380, 2600.], dtype=float)
LW_WN2 = np.array([350, 500, 630, 700, 820, 980, 1080, 1180, 1390, 1480, 1800,
                   2080, 2250, 2380, 2600, 3250.], dtype=float)
def wn2um(wn):
    return 1.0e4 / wn
log("长波 16 波段（module_ra_rrtmg_lw.F，cm⁻¹ → μm）：")
for i in range(16):
    log(f"    LW{i+1:02d}: {LW_WN1[i]:5.0f}–{LW_WN2[i]:5.0f} cm⁻¹ = "
        f"{wn2um(LW_WN2[i]):6.2f}–{wn2um(LW_WN1[i]):7.2f} μm")

SW_WN1 = np.array([2600, 3250, 4000, 4650, 5150, 6150, 7700, 8050, 12850,
                   16000, 22650, 29000, 38000, 820.], dtype=float)
SW_WN2 = np.array([3250, 4000, 4650, 5150, 6150, 7700, 8050, 12850, 16000,
                   22650, 29000, 38000, 50000, 2600.], dtype=float)
log("短波 14 波段（module_ra_rrtmg_sw.F）：")
for i in range(14):
    log(f"    SW{i+1:02d}: {SW_WN1[i]:5.0f}–{SW_WN2[i]:5.0f} cm⁻¹ = "
        f"{wn2um(SW_WN2[i]):6.3f}–{wn2um(SW_WN1[i]):7.3f} μm")

log("对照：书 4 μm 短长波分界在 SW 波段带外（SW 短于 3.85 μm 为主，SW14 覆盖 12.2–3.85 μm）；")
log("      书大气窗 8–12 μm ↔ LW6（12.2–10.2）+ LW7（10.2–9.26）+ LW8（9.26–8.47）+ LW9 前段；")
log("      CO2 15 μm ↔ LW4（15.87–14.29）；H2O 6.3 μm ↔ LW11（6.76–5.56）；O3 9.6 μm ↔ LW7/8；")
log("      N2O 7.8/17.0 ↔ LW9/LW3；CH4 7.7 ↔ LW9。")

# ---- 图 1：普朗克曲线 + 谱段 ----
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
plt.rcParams["font.sans-serif"] = ["SimHei", "Microsoft YaHei"]
plt.rcParams["axes.unicode_minus"] = False

ls = np.exp(np.linspace(np.log(0.1), np.log(100.0), 3000))
fig, axes = plt.subplots(1, 2, figsize=(12.5, 5.2))
ax = axes[0]
ax.plot(ls, FB(ls, 6000.0), color="crimson", lw=2, label="太阳黑体 6000 K（书 5.2.3）")
ax.plot(ls, FB(ls, 5777.0), color="orange", lw=1.2, ls="--", label="有效温度 5777 K")
ax.set_xscale("log"); ax.set_yscale("log")
ax.set_xlim(0.1, 100)
ax.set_ylim(1e-1, 3e8)
for i in range(14):
    x1, x2 = wn2um(SW_WN2[i]), wn2um(SW_WN1[i])
    ax.axvspan(min(x1, x2), max(x1, x2), ymin=0.88, ymax=0.99,
               color="steelblue", alpha=0.25)
ax.axvline(4.0, color="k", ls=":", lw=1)
ax.text(4.3, 2e7, "4 μm 分界", fontsize=8)
ax.set_xlabel("波长 (μm)"); ax.set_ylabel(r"分光辐出度 $F_B$ (W m$^{-2}$ μm$^{-1}$)")
ax.set_title("(a) 短波：14 波段覆盖 + 太阳谱"); ax.legend(fontsize=8, loc="lower center")
ax.grid(alpha=0.3, which="both")

ax = axes[1]
ax.plot(ls, FB(ls, 300.0), color="navy", lw=2, label="地球黑体 300 K")
ax.plot(ls, FB(ls, 255.0), color="teal", lw=1.2, ls="--", label="有效温度 255 K")
ax.set_xscale("log"); ax.set_yscale("log")
ax.set_xlim(0.1, 100)
ax.set_ylim(1e-3, 3e2)
for i in range(16):
    x1, x2 = wn2um(LW_WN2[i]), wn2um(LW_WN1[i])
    ax.axvspan(min(x1, x2), max(x1, x2), ymin=0.88, ymax=0.99,
               color="darkorange", alpha=0.3)
ax.axvspan(8, 12, color="green", alpha=0.15)
ax.text(9.3, 3.0, "大气窗\n8–12 μm", fontsize=8, ha="center")
for x, t, yt in [(15, "CO₂ 15", 0.03), (6.3, "H₂O 6.3", 0.06),
                 (9.6, "O₃ 9.6", 0.012), (4.3, "CO₂ 4.3", 0.03)]:
    ax.annotate(t, xy=(x, FB(x, 300.0)), xytext=(x, yt),
                fontsize=8, ha="center", rotation=90,
                arrowprops=dict(arrowstyle="->", lw=0.7))
ax.set_xlabel("波长 (μm)"); ax.set_ylabel(r"分光辐出度 $F_B$ (W m$^{-2}$ μm$^{-1}$)")
ax.set_title("(b) 长波：16 波段 + 地球谱 + 吸收带标注"); ax.legend(fontsize=8, loc="upper right")
ax.grid(alpha=0.3, which="both")
fig.tight_layout()
fig.savefig(FIGS / "ch12_planck_bands.png", dpi=150)
log("图已出：doc/figs/ch12_planck_bands.png")

# ============================================================================
# C. 太阳几何闭环：端口 radconst / calc_coszen ↔ wrfrst
# ============================================================================
log()
log("=" * 78)
log("C. 太阳几何闭环（端口 phys/module_radiation_driver.F 的 radconst/calc_coszen）")
log("=" * 78)

DEGRAD = np.pi / 180.0
DPD = 360.0 / 365.0          # share/module_model_constants.F

def radconst(julian):
    obecl = 23.5 * DEGRAD
    sinob = np.sin(obecl)
    sxlong = DPD * (julian - 80.0) if julian >= 80.0 else DPD * (julian + 285.0)
    sxlong = sxlong * DEGRAD
    declin = np.arcsin(sinob * np.sin(sxlong))
    rjul = (julian * 360.0 / 365.0) * DEGRAD
    eccfac = (1.000110 + 0.034221 * np.cos(rjul) + 0.001280 * np.sin(rjul)
              + 0.000719 * np.cos(2 * rjul) + 0.000077 * np.sin(2 * rjul))
    solcon = 1370.0 * eccfac
    return declin, solcon

def calc_coszen(julian, xtime, gmt, lat, lon, declin):
    da = 2.0 * np.pi * (julian - 0.5) / 365.0
    eot = (0.000075 + 0.001868 * np.cos(da) - 0.032077 * np.sin(da)
           - 0.014615 * np.cos(2 * da) - 0.040849 * np.sin(2 * da)) * 229.18
    xt24 = np.mod(xtime, 1440.0) + eot
    tloctm = gmt + xt24 / 60.0 + lon / 15.0
    hrang = 15.0 * (tloctm - 12.0) * DEGRAD
    xxlat = lat * DEGRAD
    coszen = np.sin(xxlat) * np.sin(declin) + np.cos(xxlat) * np.cos(declin) * np.cos(hrang)
    return np.clip(coszen, -1.0, 1.0), hrang

ds = Dataset(DATA / "wrfrst_d01_2025-07-12_00_05_24.nc")
xlat = np.asarray(ds.variables["XLAT"][0])     # deg
xlon = np.asarray(ds.variables["XLONG"][0])    # deg
cosz_nc = np.asarray(ds.variables["COSZEN"][0])
hrang_nc = np.asarray(ds.variables["HRANG"][0])
declin_nc = float(np.asarray(ds.variables["DECLIN"]).ravel()[0])
solcon_nc = float(np.asarray(ds.variables["SOLCON"]).ravel()[0])
xtime_nc = float(np.asarray(ds.variables["XTIME"]).ravel()[0])
log(f"wrfrst：XTIME={xtime_nc} min，DECLIN={declin_nc:.6f} rad（{declin_nc/DEGRAD:.4f}°），"
    f"SOLCON={solcon_nc:.3f} W·m⁻²")

# WRF 的 JULIAN（grid%julian）来自 ESMF 时钟 currentDayOfYearReal：
# 2025-07-12 → 零基日序 192（1 月 1 日=0），与惯用"日序 193"差 1
julian = 192.0
declin_p, solcon_p = radconst(julian)
log(f"端口 radconst(julian={julian})：DECLIN={declin_p:.6f} rad，SOLCON={solcon_p:.3f} W·m⁻²")
log(f"    ΔDECLIN = {abs(declin_p-declin_nc):.3e} rad ；ΔSOLCON = {abs(solcon_p-solcon_nc):.4f} W·m⁻²")

# COSZEN：辐射调用在 itimestep=1（xtime=0），calc_coszen 用 xtime+radt*0.5=15 min
for xt_probe, tag in [(15.0, "xtime+radt*0.5 = 15 min"), (0.0, "xtime = 0")]:
    cosz_p, hr_p = calc_coszen(julian, xt_probe, 0.0, xlat, xlon, declin_p)
    d_cos = np.abs(cosz_p - cosz_nc)
    d_hr = np.abs(hr_p - hrang_nc)
    log(f"    端口@{tag}：max|ΔCOSZEN|={d_cos.max():.3e}（网格 {cosz_nc.shape}），"
        f"max|ΔHRANG|={d_hr.max():.3e}")
ds.close()

# 兰州点（36.05N, 103.78E）→ 最近格点
ij = np.unravel_index(np.argmin((xlat - 36.05) ** 2 + (xlon - 103.78) ** 2), xlat.shape)
lat0, lon0 = float(xlat[ij]), float(xlon[ij])
log(f"兰州最近格点：({lat0:.3f}N, {lon0:.3f}E) 索引 {ij}")

# 日变化（四个节点日）与日出日落
fig, axes = plt.subplots(1, 3, figsize=(15.5, 4.6))
ax = axes[0]
hours = np.linspace(0, 24, 482)      # 本地太阳时近似（经度订正后）
for jd, name in [(80, "春分 3-21"), (172, "夏至 6-21"), (266, "秋分 9-23"), (355, "冬至 12-21")]:
    dd, _ = radconst(jd)
    cz, hh = calc_coszen(jd, hours * 60.0, 0.0, lat0, lon0, dd)
    ax.plot(hours, cz, lw=1.8, label=f"{name} (δ={dd/DEGRAD:.1f}°)")
ax.axhline(0, color="k", lw=0.8, ls=":")
ax.set_xlabel("时角对应的地方时刻 (h)"); ax.set_ylabel(r"$\cos\theta$")
ax.set_title(f"(a) 兰州 {lat0:.2f}N 太阳天顶角余弦（端口算法）")
ax.legend(fontsize=8); ax.grid(alpha=0.3)

# 日出日落（书 (5.4.4)/(5.4.5)）
dd, _ = radconst(193)
phi = lat0 * DEGRAD
arg = -np.tan(phi) * np.tan(dd)
omega0 = np.arccos(np.clip(arg, -1, 1)) / DEGRAD
log(f"书 (5.4.4)：2025-07-12 兰州 {lat0:.2f}N 日落时角 ω0 = ±{omega0:.2f}° → "
    f"昼长 {2*omega0/15:.3f} h")

ax = axes[1]
cosz_p, hr_p = calc_coszen(julian, 15.0, 0.0, xlat, xlon, declin_p)
ax.scatter(cosz_nc.ravel(), cosz_p.ravel(), s=0.5, alpha=0.3, color="navy")
ax.plot([-1, 1], [-1, 1], "r--", lw=1)
ax.set_xlabel("wrfrst COSZEN"); ax.set_ylabel("端口重算 COSZEN")
ax.set_title(f"(b) 闭环校验：{cosz_nc.size} 格点（max|Δ|={np.abs(cosz_p-cosz_nc).max():.2e}）")
ax.grid(alpha=0.3)

# E. 日总量 Qd（书 (5.4.14)）
S0 = 1366.0
T_SUNDAY = 86400.0
def Qd(phi_deg, delta_deg, dm=1.0):
    ph, de = phi_deg * DEGRAD, delta_deg * DEGRAD
    arg = -np.tan(ph) * np.tan(de)
    if arg <= -1:      # 极昼
        w0 = np.pi
    elif arg >= 1:     # 极夜
        return 0.0
    else:
        w0 = np.arccos(arg)
    return T_SUNDAY / np.pi * dm**2 * S0 * (w0 * np.sin(ph) * np.sin(de)
                                            + np.cos(ph) * np.cos(de) * np.sin(w0))

ax = axes[2]
phis = np.linspace(-90, 90, 361)
for jd, name in [(80, "春分/秋分"), (172, "夏至"), (355, "冬至")]:
    dd, _ = radconst(jd)
    q = np.array([Qd(p, dd / DEGRAD) for p in phis])
    ax.plot(phis, q / 1e6, lw=1.8, label=name)
ax.set_xlabel("纬度 (°)"); ax.set_ylabel(r"$Q_d$ ($10^6$ J m$^{-2}$ d$^{-1}$)")
ax.set_title("(c) 大气上界太阳辐射日总量（书 (5.4.14)）")
ax.legend(fontsize=8); ax.grid(alpha=0.3)
fig.tight_layout()
fig.savefig(FIGS / "ch12_solar_geometry.png", dpi=150)
log("图已出：doc/figs/ch12_solar_geometry.png")

dd_sum, _ = radconst(172)
q_eq = Qd(0.0, dd_sum / DEGRAD)
q_pole = Qd(90.0, dd_sum / DEGRAD)
log(f"书 5.4.2 结论复核（夏至）：Qd(赤道)={q_eq/1e6:.3f}、Qd(90N)={q_pole/1e6:.3f} "
    f"（10⁶ J·m⁻²·d⁻¹），比值 = {q_pole/q_eq:.4f}（书：北极是赤道的 1.37 倍）")

# ============================================================================
# D. 相对大气质量与光学厚度
# ============================================================================
log()
log("=" * 78)
log("D. 相对大气质量 m 与光学厚度（书 5.4.3，印刷页 92–95）")
log("=" * 78)
book_tab = {10: 1.0154, 20: 1.0642, 30: 1.1547, 40: 1.3054, 50: 1.5557,
            60: 2.0000, 65: 2.3662, 70: 2.9238, 75: 3.8637, 80: 5.7588, 85: 11.4739}
log("  θ(°)   secθ      Kasten(5.4.22)   书表5.5(secθ)   书表5.5(蒋龙海)")
for th in book_tab:
    m_sec = 1.0 / np.cos(th * DEGRAD)
    m_kas = 1.0 / (np.cos(th * DEGRAD) + 0.1500 * (93.885 - th) ** (-1.253))
    log(f"  {th:3d}  {m_sec:8.4f}   {m_kas:10.4f}      {book_tab[th]:8.4f}       —")
m60 = 1.0 / (np.cos(60 * DEGRAD) + 0.1500 * (93.885 - 60) ** (-1.253))
log(f"抽查 θ=60°：Kasten={m60:.4f}（书表 5.5 三列：2.0000 / 1.9927 / 1.9939）")
dR = 0.0088 * 0.52 ** (-4.05)
log(f"空气分子垂直光学厚度（Rayleigh，书 (5.4.30)）：λ=0.52 μm → δ_R(0)={dR:.4f}"
    f"（书：0.124，透过率 {np.exp(-dR):.3f}）")
for lam_um in (0.40, 0.52, 0.70):
    log(f"    λ={lam_um:.2f} μm：δ_R(0)={0.0088*lam_um**(-4.05):.4f}（λ⁻⁴.⁰⁵ 律）")

# ============================================================================
# F. 两层温室模型 + CAMtr + O3RAD
# ============================================================================
log()
log("=" * 78)
log("F. 两层温室模式（书 (5.6.3)/(5.6.4) 与表 5.16）")
log("=" * 78)

def two_layer(S0, R, As, Al):
    Tg4 = S0 * (2 * (1 - R) - As) / (4 * SIGMA_BOOK * (2 - Al))
    Ta4 = S0 * (As + Al * (1 - R - As)) / (4 * SIGMA_BOOK * Al * (2 - Al))
    return Tg4 ** 0.25, Ta4 ** 0.25

Te = (S0 * (1 - 0.3) / (4 * SIGMA_BOOK)) ** 0.25
log(f"行星有效温度 Te（书 (5.6.2)，S0=1366, R=0.3）：{Te:.1f} K（书 255 K）")
log(f"地面接收平均短波 S0(1-R)/4 = {S0*0.7/4:.2f} W·m⁻²（书 239.05）")
tg, ta = two_layer(1366.0, 0.3, 0.2, 0.8)
log(f"标准算例 Al=0.8, As=0.2, R=0.3：Tg={tg:.1f} K, Ta={ta:.1f} K（书 278.6 / 247.7）")
cases = [(0.3, 0.2, 0.8, "基准"), (0.32, 0.2, 0.8, "R↑0.32 云量增"),
         (0.28, 0.2, 0.8, "R↓0.28 云量减"), (0.3, 0.2, 0.82, "Al↑0.82 温室气体增"),
         (0.3, 0.2, 0.78, "Al↓0.78 温室气体减"), (0.3, 0.21, 0.8, "As↑0.21 大气吸收增"),
         (0.3, 0.19, 0.8, "As↓0.19 大气吸收减")]
book161 = {1: (278.6, 247.7), 2: (278.3, 245.0), 3: (278.9, 250.5),
           4: (283.2, 247.5), 5: (274.1, 247.9), 6: (276.0, 247.5), 7: (281.2, 247.9)}
log("  复现书表 5.16（S0=1366）：")
for i, (R, As, Al, tag) in enumerate(cases, 1):
    t1, t2 = two_layer(1366.0, R, As, Al)
    b1, b2 = book161[i]
    log(f"    {tag:22s} Tg={t1:6.1f} (书 {b1})  Ta={t2:6.1f} (书 {b2})")

# CAMtr 温室气体
log("-" * 78)
log("F2  CAMtr_volume_mixing_ratio（ghg_input=1 默认读取，module_ra_clWRF_support.F/read_CAMgases）")
ghg = {}
with open(RUN / "CAMtr_volume_mixing_ratio") as f:
    for line in f:
        line = line.strip()
        if not line or line.startswith("#"):
            continue
        parts = line.split()
        try:
            yr = int(parts[0]); ghg[yr] = [float(x) for x in parts[1:6]]
        except ValueError:
            continue
for yr in (2005, 2025):
    co2, n2o, ch4, cfc11, cfc12 = ghg[yr]
    log(f"    {yr}: CO2={co2:.3f} ppmv, N2O={n2o:.3f} ppbv, CH4={ch4:.3f} ppbv, "
        f"CFC11={cfc11:.3f} pptv, CFC12={cfc12:.3f} pptv")
co2, n2o, ch4, cfc11, cfc12 = ghg[2025]
log(f"    RRTMG 常量支路（ghg_input=0，源码注释 2005 IPCC）：ch4={1774e-9} n2o={319e-9} "
    f"cfc11={0.251e-9} cfc12={0.538e-9}（VMR）→ 与 2005 行一致")
log(f"    本个例 2025 年实际取用：CO2={co2*1e-6:.6e}, N2O={n2o*1e-9:.3e}, "
    f"CH4={ch4*1e-9:.3e}（VMR）")

# O3RAD 实测廓线
log("-" * 78)
log("F3  O3RAD（o3input 默认=2 → CAM 臭氧气候学：oznini/ozn_time_int/ozn_p_int）")
ds = Dataset(DATA / "wrfrst_d01_2025-07-12_00_05_24.nc")
p_top_pa = float(np.asarray(ds.variables["P_TOP"]).ravel()[0])
try:
    o3rad = np.asarray(ds.variables["O3RAD"][0])   # (k, j, i)，k=0 为最低层
    p_phys = np.asarray(ds.variables["P"][0]) + np.asarray(ds.variables["PB"][0])
    o3_col = o3rad[:, ij[0], ij[1]]
    p_col = p_phys[:, ij[0], ij[1]] / 100.0
    log(f"    P_TOP={p_top_pa:.0f} Pa（= {p_top_pa/100:.0f} hPa）；模式层数={o3rad.shape[0]}，"
        f"顶层面 p={p_col[-1]:.1f} hPa，最底层 p={p_col[0]:.1f} hPa")
    log(f"    O3RAD 值域 [全域 {o3rad.min():.3e}, {o3rad.max():.3e}]；兰州柱值域 "
        f"[{o3_col.min():.3e}, {o3_col.max():.3e}]（VMR，mol/mol）")
except Exception as e:
    log(f"    O3RAD 读取失败：{e}")
    o3_col, p_col = None, None

# CAM 臭氧气候学（7 月，兰州纬度）
oz_all = np.loadtxt(RUN / "ozone.formatted").reshape(12, 64, 59)  # (month, lat, lev)
lat_oz = np.loadtxt(RUN / "ozone_lat.formatted")
plev_oz = np.loadtxt(RUN / "ozone_plev.formatted")                # hPa，自顶（0.28）到底（~1004），递增
j_lat = int(np.argmin(np.abs(lat_oz - lat0)))
oz_jul = oz_all[6, j_lat, :]     # 7 月（索引 6）
# 按 log(p) 把 7 月气候学插到模式层，量化对照（plev_oz 自顶 0.28 hPa 到底 ~1004 hPa，递增）
oz_on_model = np.interp(np.log(p_col), np.log(plev_oz), oz_jul)
rel = np.abs(o3_col - oz_on_model) / oz_on_model * 100.0
log(f"    CAM 气候学：7 月 @ {lat_oz[j_lat]:.2f}N（59 层，{plev_oz[0]:.2f}–{plev_oz[-1]:.0f} hPa，"
    f"峰值 {oz_jul.max():.3e} @ p={plev_oz[np.argmax(oz_jul)]:.1f} hPa）")
log(f"    气候学 log-p 内插到模式层后与 O3RAD 的对照：中位相对差 {np.median(rel):.1f} %，"
    f"p<650 hPa 段中位 {np.median(rel[24:]):.1f} %，p>650 hPa 段中位 {np.median(rel[:24]):.1f} %")
for kk in (0, 12, 24, 36, 44, 48):
    log(f"      p={p_col[kk]:8.2f} hPa：O3RAD={o3_col[kk]:.3e}，气候学(插值)={oz_on_model[kk]:.3e}"
        f"，差 {rel[kk]:5.1f} %")
ds.close()

# ---- 图 3：O3 廓线 + GHGs ----
fig, axes = plt.subplots(1, 2, figsize=(11.5, 4.6))
ax = axes[0]
if o3_col is not None:
    ax.semilogy(o3_col, p_col, "o-", ms=3, lw=1.4, label="wrfrst O3RAD（兰州格点）")
ax.semilogy(oz_jul, plev_oz, "s--", ms=3, lw=1.2, label=f"CAM 气候学 7 月 {lat_oz[j_lat]:.1f}N")
ax.invert_yaxis()
ax.set_xscale("log")
ax.set_xlabel(r"O$_3$ 体积混合比 (mol/mol)"); ax.set_ylabel("气压 (hPa)")
ax.set_title(r"(a) O$_3$ 垂直廓线：模式实际取值 vs CAM 气候学源数据")
ax.legend(fontsize=8); ax.grid(alpha=0.3, which="both")

ax = axes[1]
labels = ["CO$_2$\n(ppmv)", "CH$_4$\n(ppbv)", "N$_2$O\n(ppbv)", "CFC11\n(pptv)", "CFC12\n(pptv)"]
v2005 = ghg[2005]; v2025 = ghg[2025]
x = np.arange(5)
ax.bar(x - 0.18, v2005, 0.36, label="2005", color="gray")
ax.bar(x + 0.18, v2025, 0.36, label="2025", color="crimson")
for xi, (a, b) in enumerate(zip(v2005, v2025)):
    ax.text(xi - 0.18, a, f"{a:.0f}", ha="center", va="bottom", fontsize=7.5)
    ax.text(xi + 0.18, b, f"{b:.0f}", ha="center", va="bottom", fontsize=7.5)
ax.set_xticks(x); ax.set_xticklabels(labels, fontsize=8)
ax.set_ylabel("混合比（各自单位）")
ax.set_title("(b) CAMtr 温室气体：2005（RRTMG 常量支路）vs 2025（本个例）")
ax.legend(fontsize=8); ax.grid(alpha=0.3, axis="y")
fig.tight_layout()
fig.savefig(FIGS / "ch12_ozone_ghg.png", dpi=150)
log("图已出：doc/figs/ch12_ozone_ghg.png")

# ---------------------------------------------------------------------------
(LOGS / "ch12_experiment.log").write_text("\n".join(log_lines), encoding="utf-8")
print("\n日志已写入 workspace/logs/ch12_experiment.log")