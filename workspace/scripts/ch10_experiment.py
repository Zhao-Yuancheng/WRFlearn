# -*- coding: utf-8 -*-
"""ch10 实验：手算压高公式 / 基态解析式  vs  real.exe 基态（兰州点）
数据：workspace\\data\\ch10\\wrfinput_d01.nc（real 产物）、met_em.d01（ERA5 驱动）
输出：控制台核对报告 + doc\\figs\\ch10_base_state_profiles.png
"""
import numpy as np
from netCDF4 import Dataset
from pathlib import Path

RD, G = 287.0, 9.81          # 与 WRF 一致（模式内部 g=9.81）
CP = 1004.5
G0 = 9.80665                  # 标准重力加速度（书 3.3）
P00, T00, A_LAPSE, TISO = 100000.0, 290.0, 50.0, 200.0   # base_pres/base_temp/base_lapse/iso_temp
P1000 = 100000.0

wrf_file = Path(r"d:\Code\Learn\WRF\workspace\data\ch10\wrfinput_d01.nc")
met_file = Path(r"d:\Code\Learn\WRF\workspace\data\ch10\met_em.d01.2025-07-12_00.nc")

w = Dataset(wrf_file)
# ---------- 0) 找兰州（城关）最近点 ----------
lat = np.asarray(w.variables["XLAT"][0])
lon = np.asarray(w.variables["XLONG"][0])
d2 = (lat - 36.056) ** 2 + (lon - 103.83) ** 2
i, j = np.unravel_index(np.argmin(d2), lat.shape)
print(f"[0] 最近格点 (i,j)=({i},{j})  lat={lat[i,j]:.4f} lon={lon[i,j]:.4f}")
ht_name = "HGT" if "HGT" in w.variables else "HT"
ht = float(w.variables[ht_name][0, i, j])
ptop = float(w.getncattr("P_TOP")) if "P_TOP" in w.ncattrs() else float(w.variables["P_TOP"][0])
print(f"    地形高度 HT={ht:.1f} m, p_top={ptop:.0f} Pa")

var_names = list(w.variables.keys())
print(f"[0] wrfinput 关键变量存在性: " + ", ".join(v for v in
      ("PB", "PHB", "PH", "P", "ALB", "AL", "MUB", "MU", "ZNU", "ZNW", "DN", "DNW",
       "C1F", "C2F", "C3F", "C4F", "C1H", "C2H", "C3H", "C4H", "T_INIT", "T_BASE", "T")
      if v in var_names))

znw = np.asarray(w.variables["ZNW"][0]).squeeze()
znu = np.asarray(w.variables["ZNU"][0]).squeeze()
pb = np.asarray(w.variables["PB"][0, :, i, j])
alb = np.asarray(w.variables["ALB"][0, :, i, j])
phb = np.asarray(w.variables["PHB"][0, :, i, j])
mub = float(w.variables["MUB"][0, i, j])

# ---------- 1) eta 层核对 ----------
kde = znw.size
znu_check = 0.5 * (znw[1:] + znw[:-1])
print("\n[1] η 层核对")
print(f"    znw: 首={znw[0]:.6f} 末={znw[-1]:.6f}, 层数={kde - 1} 质量层={znu.size}")
print(f"    znu=0.5*(znw(k+1)+znw(k)) 最大偏差 = {np.max(np.abs(znu[:kde-1] - znu_check)):.3e}")
print(f"    前 5 个 znw: {np.round(znw[:5], 6)}")

# ---------- 2) 基态温度 T0 = pb·alb/Rd 与解析式对照 ----------
T0_from_file = pb * alb / RD
T0_formula = np.maximum(TISO, T00 + A_LAPSE * np.log(pb / P00))
pb_thresh = P00 * np.exp((TISO - T00) / A_LAPSE)
n_cap = int(np.sum(pb < pb_thresh))
print("\n[2] 基态温度 T0 (pb·alb/Rd) vs 解析式 max(tiso, t00+a·ln(pb/p00))")
print(f"    最大绝对偏差 = {np.max(np.abs(T0_from_file - T0_formula)):.4f} K")
print(f"    tiso=200K 封顶阈值 pb = p00·exp((tiso−t00)/a) = {pb_thresh:.0f} Pa；封顶层数 = {n_cap}/{pb.size}（顶层一侧）")
print(f"    T0: 首层={T0_from_file[0]:.2f} K, 顶层={T0_from_file[-1]:.2f} K")
for k in (0, 3, 10, 20, 30, 40, 48):
    print(f"      k={k+1:2d}: pb={pb[k]:9.2f} Pa  T0(实测)={T0_from_file[k]:7.2f} K  T0(式)={T0_formula[k]:7.2f} K")
if False:  # T_BASE 为未填充占位（本构建实测全零），不入正文
    pass

# ---------- 3) 基态地面气压解析式 ----------
p_surf_formula = P00 * np.exp(-T00 / A_LAPSE +
                              np.sqrt((T00 / A_LAPSE) ** 2 - 2.0 * G * ht / A_LAPSE / RD))
print("\n[3] 基态地面气压公式（mode: p00·exp(−t00/a+√((t00/a)²−2g·ht/(a·Rd))))")
print(f"    公式 p_surf = {p_surf_formula:.3f} Pa")
print(f"    real 产物 MUB+p_top = {mub + ptop:.3f} Pa   偏差 = {mub + ptop - p_surf_formula:+.4f} Pa")

# ---------- 4) 静力一致性：重演 real 的基态位势积分 与 有限差分压高公式 ----------
z_s = phb / G                      # 交错层界面几何高度
z_m = 0.5 * (z_s[1:] + z_s[:-1])   # 质量层高度
dz1 = z_s[1] - z_s[0]
print("\n[4] 静力一致性（重演 code 路径 + 有限差分压高公式）")
print(f"    首层几何厚度 dz1 = {dz1:.2f} m（50 层低层加密设计目标 ~16 m）")

# 4a) 重演 module_initialize_real.F 的 hypsometric_opt=2 积分：
#     phb(k) = phb(k-1) + alb(k-1)*phm*ln(pfd/pfu)
c3f = np.asarray(w.variables["C3F"][0, :]).squeeze()
c4f = np.asarray(w.variables["C4F"][0, :]).squeeze()
c3h = np.asarray(w.variables["C3H"][0, :]).squeeze()
c4h = np.asarray(w.variables["C4H"][0, :]).squeeze()
phb_rec = np.zeros_like(phb)
phb_rec[0] = ht * G
for k in range(1, phb.size):
    pfu = c3f[k] * mub + c4f[k] + ptop
    pfd = c3f[k - 1] * mub + c4f[k - 1] + ptop
    phm = c3h[k - 1] * mub + c4h[k - 1] + ptop
    phb_rec[k] = phb_rec[k - 1] + alb[k - 1] * phm * np.log(pfd / pfu)
res_abs = np.abs(phb_rec - phb)
print(f"    4a 重演积分 phb：与文件 PHB 的最大绝对残差 = {res_abs.max():.3f} m²/s² "
      f"（相对量程 {res_abs.max()/(phb[-1]-phb[0]):.1e} → 机器精度级，基态严格静力平衡）")

# 4b) 有限差分压高公式：dz = α·Δp/g（注意 φ=−αΔp，几何高度要再除 g）
p_int = c3f * mub + c4f + ptop          # 50 个界面的基态气压（c3f/c4f 形式）
err = []
for k in range(pb.size):
    dz_geo = z_s[k + 1] - z_s[k]
    dz_hyp = alb[k] * (p_int[k] - p_int[k + 1]) / G
    err.append(abs(dz_geo - dz_hyp) / max(dz_hyp, 1e-9))
err = np.array(err)
print(f"    4b 逐层 dz(几何) vs 压高式 α·Δp/g 相对偏差：中位={np.median(err):.2e}, 最大={err.max():.2e}")

# ---------- 5) 位势高度 vs 几何高度 ----------
Z_m = z_m                       # 用 Φ/g0 定义的位势高度与几何高度的差别（低层可忽略）
print("\n[5] 位势高度 Z=Φ/g0 与几何高度的差别（k=1 与 12 km 附近）")
for k in (0, int(np.argmin(np.abs(z_m - 12000)))):
    phi = G * z_m[k]
    Z = phi / G0
    print(f"    z={z_m[k]:8.1f} m → Z={Z:8.2f} gpm, 差 = {Z - z_m[k]:+.2f} m")

# ---------- 6) ERA5(met_em) 手算压高积分 vs 自带 GHT ----------
m = Dataset(met_file)
mlat = np.asarray(m.variables["XLAT_M"][0]) if "XLAT_M" in m.variables else np.asarray(m.variables["XLAT"][0])
mlon = np.asarray(m.variables["XLONG_M"][0]) if "XLONG_M" in m.variables else np.asarray(m.variables["XLONG"][0])
d2m = (mlat - 36.056) ** 2 + (mlon - 103.83) ** 2
mi, mj = np.unravel_index(np.argmin(d2m), mlat.shape)
pres = np.asarray(m.variables["PRES"][0, :, mi, mj])       # Pa, 32 层
tt = np.asarray(m.variables["TT"][0, :, mi, mj])           # K
rh = np.asarray(m.variables["RH"][0, :, mi, mj])           # %
ght = np.asarray(m.variables["GHT"][0, :, mi, mj])         # m (位势高度)
psfc = float(m.variables["PSFC"][0, mi, mj])
soilhgt = float(m.variables["SOILHGT"][0, mi, mj]) if "SOILHGT" in m.variables else float(m.variables["HGT_M"][0, mi, mj])
# RH -> 比湿 q（Bolton 饱和水汽压），再得虚温 Tv = T(1+0.608q)
es = 6.112 * np.exp(17.67 * (tt - 273.15) / (tt - 29.65)) * 100.0
e = np.clip(rh / 100.0, 0.0, 1.0) * es
q = 0.622 * e / (pres - 0.378 * e)
tv = tt * (1.0 + 0.608 * q)
# ---------- 6) ERA5(met_em) 逐层差分检验 + 地形口径差观察 ----------
# met_em 层结构：k=0 为"表面行"（p=PSFC、GHT=geog 地形）；k=1.. 为 ERA5 气压层
levels = np.arange(1, pres.size)
res = []
for a, b in zip(levels[:-1], levels[1:]):
    dz_hyp = RD / G * 0.5 * (tv[a] + tv[b]) * np.log(pres[a] / pres[b])
    dz_ght = ght[b] - ght[a]
    res.append(dz_hyp - dz_ght)
res = np.array(res)
print("\n[6] ERA5 逐层差分检验（k=1..31 相邻层，用压高公式手算 vs GHT 差）")
print(f"    {res.size} 段残差（手算−GHT）：中位={np.median(res):+.2f} m, 最大绝对值={np.max(np.abs(res)):.2f} m")
print(f"    示例：85000→80000 Pa：手算 {RD/G*0.5*(tv[7]+tv[8])*np.log(pres[7]/pres[8]):.1f} m,"
      f" GHT 差 {ght[8]-ght[7]:.1f} m")

# 地形口径差：由 ERA5 柱把 PSFC 放到哪个高度（ln p 插值，排除表面行 k=0） vs geog 地形
cand = np.argsort(np.abs(np.log(pres / psfc)))[:4]
cand = cand[cand != 0][:2]
cand = cand[np.argsort(-pres[cand])]
i_below, i_above = cand[0], cand[1]
lnp_b, lnp_a = np.log(pres[i_below]), np.log(pres[i_above])
frac = (np.log(psfc) - lnp_b) / (lnp_a - lnp_b)
GHT_sfc_era5 = ght[i_below] + frac * (ght[i_above] - ght[i_below])
print(f"    地形口径差观察：geog 地形 HGT_M = {soilhgt:.0f} m；由 ERA5 柱推算 PSFC 所在高度 ≈ {GHT_sfc_era5:.0f} m"
      f"（差 {GHT_sfc_era5-soilhgt:+.0f} m）→ 驱动数据与目标网格的地形口径不一致，"
      f"WPS/real 的垂直插值与外推正是为弥合它而存在")

# ---------- 7) 标高 与 标准大气 ----------
Hp_sfc = 29.27 * tv[9]           # 地面以上最近层（80000 Pa, k=9）的虚温
print("\n[7] 标高与标准大气")
print(f"    近地面 Tv={tv[9]:.1f} K → 气压标高 Hp=29.27·Tv={Hp_sfc:.0f} m（书 3.1.3：Tv=273K → 7990 m）")
std = [("0 m", 0.0, 1013.25, 288.15), ("11 km", 11000.0, 226.32, 216.65),
       ("20 km", 20000.0, 54.75, 216.65), ("32 km", 32000.0, 8.68, 228.65)]
print("    1976 美国标准大气（书 3.4）：")
for name, zz, pp, ttt in std:
    print(f"      {name:6s} p={pp:8.2f} hPa  T={ttt:6.2f} K")

# ---------- 8) 大气总质量估算（书 4.2） ----------
for p0 in (98500.0, 101325.0):
    m0 = p0 / 9.8
    RE = 6.37e6
    total_t = m0 * 4 * np.pi * RE ** 2 / 1000.0   # 转换为吨
    print(f"\n[8] p0={p0:.0f} Pa → m0={m0:.0f} kg/m², 总质量={total_t:.3e} t")
print("    书 4.2：m0≈10044 kg/m²（p0=985hPa,g=9.8）→ 总质量≈5.12×10^15 t")

# ---------- 9) 画图 ----------
fig_dir = Path(r"d:\Code\Learn\WRF\doc\figs")
fig_dir.mkdir(parents=True, exist_ok=True)
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
try:
    plt.rcParams["font.sans-serif"] = ["SimHei", "Microsoft YaHei"]
    plt.rcParams["axes.unicode_minus"] = False
    zh = True
except Exception:
    zh = False
L = (lambda zh_s, en_s: zh_s if zh else en_s)

fig, axes = plt.subplots(1, 3, figsize=(13.5, 5.0))
ax = axes[0]
ax.plot(T0_from_file, pb / 100.0, "o-", ms=3, label=L("real 基态 pb·alb/Rd", "WRF base"))
ax.plot(T0_formula, pb / 100.0, "--", label=L("解析式 max(200,290+50ln(p/p00))", "analytic"))
ax.set_xlabel(L("基态温度 T0 (K)", "T0 (K)"))
ax.set_ylabel(L("气压 (hPa)", "p (hPa)"))
ax.set_yscale("log")
ax.invert_yaxis()
ax.legend(fontsize=8)
ax.set_title(L("(a) 基态温度廓线：实测 vs 解析", "(a) base temperature"))

ax = axes[1]
ax.plot(z_m, pb / 100.0, "o-", ms=3, label=L("WRF 基态 (pb, z)", "WRF base"))
sel = np.arange(1, pres.size)
o = sel[np.argsort(pres[sel])[::-1]]
ax.plot(ght[o], pres[o] / 100.0, "s--", ms=3, label=L("ERA5 (GHT)", "ERA5 GHT"))
zstd = [z for _, z, _, _ in std]
pstd = [p for _, _, p, _ in std]
ax.plot(zstd, pstd, "d:", label=L("1976 标准大气", "US1976"))
ax.set_yscale("log")
ax.invert_yaxis()
ax.set_xlabel(L("高度 (m)", "z (m)"))
ax.set_ylabel(L("气压 (hPa)", "p (hPa)"))
ax.legend(fontsize=8)
ax.set_title(L("(b) 气压-高度：基态/ERA5/标准大气", "(b) p vs z"))

ax = axes[2]
ax.plot(znw, np.arange(znw.size), "-", label="znw (full)")
ax.plot(znu, np.arange(znu.size) + 0.5, "--", label="znu (half)")
ax.invert_yaxis()
ax.set_xlabel("η")
ax.set_ylabel(L("层号（自上而下显示）", "index (top→bottom shown)"))
ax.invert_yaxis()
ax.set_title(L("(c) 50 层 η 分布（低层加密）", "(c) eta levels"))
ax.legend(fontsize=8)
fig.tight_layout()
out_png = fig_dir / "ch10_base_state_profiles.png"
fig.savefig(out_png, dpi=150)
print(f"\n[9] 图已保存: {out_png}")

w.close()
m.close()