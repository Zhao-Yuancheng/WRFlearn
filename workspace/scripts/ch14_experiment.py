# -*- coding: utf-8 -*-
"""
ch14_experiment.py —— ch14 边界层族轻轨实验（本地 WRFlearn，无需集群）

E1 稳定度判据表（书习题 7 探空；(6.8.10)–(6.8.15)）
E2 CAPE/CIN（含虚温订正的浮力积分；(6.8.16)(6.8.17)）
E3 混合层 θ 守恒（wrfinput 兰州柱；(6.5.6)）
E4 薄层法判据 (6.8.21) 数值演示（积云密度扫描）

输出：doc/figs/ch14_stability.png、ch14_cape.png、ch14_mixed_layer.png
日志：workspace/logs/ch14_experiment.log
"""
import os
import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

plt.rcParams["font.sans-serif"] = ["SimHei"]
plt.rcParams["axes.unicode_minus"] = False

ROOT = r"d:\Code\Learn\WRF"
FIGD = os.path.join(ROOT, "doc", "figs")
LOGD = os.path.join(ROOT, "workspace", "logs")
LOG = open(os.path.join(LOGD, "ch14_experiment.log"), "w", encoding="utf-8")


def log(*a):
    s = " ".join(str(x) for x in a)
    print(s)
    LOG.write(s + "\n")


Rd, Rv, cpd, eps, g = 287.04, 461.6, 1004.0, 0.622, 9.81
kappa = Rd / cpd
gammad = g / cpd * 1000.0
psat, TTP = 610.78, 273.16
cpv, cliq, hvap = 4 * Rv, 4190.0, 2.5e6
XA = (cliq - cpv) / Rv
XB = XA + hvap / (Rv * TTP)


def es_w(T):
    tr = TTP / T
    return psat * tr ** XA * np.exp(XB * (1 - tr))


def rs_w(T, p):
    e = np.minimum(es_w(T), 0.99 * np.asarray(p, dtype=float))
    return eps * e / (p - e)


def Lv(T):
    return 2.5e6 - 2323.0 * (T - 273.15)


def desdT(T):
    return Lv(T) * es_w(T) / (Rv * T * T)


def dTdlnp_moist(T, p):
    e = min(es_w(T), 0.99 * p)
    rs = eps * e / (p - e)
    num = Rd * T + Lv(T) * rs * p / (p - e)
    den = cpd + Lv(T) * eps * p * desdT(T) / (p - e) ** 2
    return num / den


def pseudo(T0, p0, p_end, n=600):
    lns = np.linspace(np.log(p0), np.log(p_end), n + 1)
    T = T0
    Ts = [T]
    for i in range(n):
        ln, ln_ = lns[i], lns[i + 1]
        h = ln_ - ln
        p = np.exp(ln)
        k1 = dTdlnp_moist(T, p)
        k2 = dTdlnp_moist(T + .5 * h * k1, np.exp(ln + .5 * h))
        k3 = dTdlnp_moist(T + .5 * h * k2, np.exp(ln + .5 * h))
        k4 = dTdlnp_moist(T + h * k3, np.exp(ln_))
        T += h / 6 * (k1 + 2 * k2 + 2 * k3 + k4)
        Ts.append(T)
    return np.array(Ts), np.exp(lns)


def theta(T, p):
    return T * (1e5 / np.asarray(p)) ** kappa


def gs_closed(T, p):
    e = es_w(T)
    rs = eps * e / (p - e)
    return gammad * (1 + Lv(T) * rs / (Rd * T)) / (1 + eps * Lv(T) ** 2 * rs / (cpd * Rd * T ** 2))


log("=" * 72)
log("ch14 实验：边界层族轻轨实验")
log("=" * 72)

# ---------------- 探空（书习题 7） ----------------
P = np.array([1000, 900, 850, 800, 700, 600, 500, 400, 300, 200]) * 100.0
T = np.array([23.0, 20.5, 17.0, 12.0, 4.5, -4.0, -12.1, -23.0, -32.5, -45.3]) + 273.15
TD = np.array([19.0, 10.4, 7.6, 6.8, -1.1, -8.5, -19.2, -29.5, -45.0, -59.5]) + 273.15

# 层厚（静力，用层平均环境温度）
z = np.zeros_like(P)
for i in range(1, len(P)):
    Tm = .5 * (T[i] + T[i - 1])
    z[i] = z[i - 1] - Rd * Tm / g * (np.log(P[i]) - np.log(P[i - 1]))

log("\n### E1 稳定度判据表（书 6.8；γd=%.2f K/km）" % gammad)
log("层（hPa）        Γ(K/km)  γs(K/km)  θ(K)    θe(K)   ∂θ/∂z  ∂θe/∂z  判据(6.8.10-12)        θ/θe 判据")
cats = []
for i in range(len(P) - 1):
    dz = z[i + 1] - z[i]
    Gam = (T[i] - T[i + 1]) / dz * 1000.0
    Tm = .5 * (T[i] + T[i + 1])
    pm = .5 * (P[i] + P[i + 1])
    gam_s = gs_closed(Tm, pm)
    th1, th2 = theta(T[i], P[i]), theta(T[i + 1], P[i + 1])
    # θe 用实测比湿口径（θ·exp(Lv q/(cpd T))）
    e1 = es_w(TD[i]) * 1.0
    q1 = eps * e1 / (P[i] - e1)
    e2 = es_w(TD[i + 1]) * 1.0
    q2 = eps * e2 / (P[i + 1] - e2)
    te1 = th1 * np.exp(Lv(T[i]) * q1 / (cpd * T[i]))
    te2 = th2 * np.exp(Lv(T[i + 1]) * q2 / (cpd * T[i + 1]))
    dth = (th2 - th1) / dz * 1000.0
    dte = (te2 - te1) / dz * 1000.0
    if Gam > gammad:
        cat = "绝对不稳定(6.8.10)"
    elif Gam > gam_s:
        cat = "条件性不稳定(6.8.11)"
    else:
        cat = "绝对稳定(6.8.12)"
    if dth < 0:
        cat2 = "θ↓ 绝对不稳定"
    elif dte < 0:
        cat2 = "θ↑且θe↓ 条件性不稳定"
    else:
        cat2 = "θe↑ 绝对稳定"
    cats.append((P[i], P[i + 1], Gam, gam_s, cat, cat2))
    log("%4d-%4d        %6.2f   %6.2f    %6.1f  %6.1f  %5.2f  %5.2f  %-22s %s"
        % (P[i] / 100, P[i + 1] / 100, Gam, gam_s, th1, te1, dth, dte, cat, cat2))

# ---------------- E2 CAPE/CIN（虚温订正） ----------------
log("\n### E2 CAPE/CIN（含虚温订正；(6.8.16)(6.8.17)）")
T0, p0 = T[0], P[0]
Td0 = TD[0]
q0 = rs_w(Td0, p0)
# LCL
lo, hi = p0, 200e2
for _ in range(300):
    mid = .5 * (lo + hi)
    if rs_w(T0 * (mid / p0) ** kappa, mid) > q0:
        lo = mid
    else:
        hi = mid
p_lcl = .5 * (lo + hi)
T_lcl = T0 * (p_lcl / p0) ** kappa
# 气块路径
lnp = np.linspace(np.log(p0), np.log(200e2), 800)
pp = np.exp(lnp)
Tp = np.where(pp >= p_lcl, T0 * (pp / p0) ** kappa, np.nan)
Ts_m, ps_m = pseudo(T_lcl, p_lcl, 200e2, n=700)
Tp = np.where(pp >= p_lcl, T0 * (pp / p0) ** kappa,
              np.interp(np.log(pp), np.log(ps_m[::-1]), Ts_m[::-1]))
qp = np.where(pp >= p_lcl, q0, rs_w(Tp, pp))
# 环境（含虚温，用实测露点）
Te_ = np.exp(np.interp(np.log(pp), np.log(P[::-1]), np.log(T[::-1])))
Tde_ = np.exp(np.interp(np.log(pp), np.log(P[::-1]), np.log(TD[::-1])))
qenv = np.where(Tde_ < 150, 0.0, eps * np.minimum(es_w(Tde_), .99 * pp) / (pp - np.minimum(es_w(Tde_), .99 * pp)))
Tve = Te_ * (1 + 0.608 * qenv)
Tvp = Tp * (1 + 0.608 * qp)
B = g * (Tvp - Tve) / Tve
# 高度
zz = np.zeros_like(pp)
for i in range(1, len(pp)):
    Tm = .5 * (Te_[i] + Te_[i - 1])
    zz[i] = zz[i - 1] - Rd * Tm / g * (np.log(pp[i]) - np.log(pp[i - 1]))
# LFC / EL
lfc = el = None
pos = 0
for i in range(1, len(pp)):
    if lfc is None and B[i] > 0:
        lfc = i
    if lfc is not None and el is None and B[i] < 0:
        el = i
        break
cape = np.trapz(B[lfc:el], zz[lfc:el]) if (lfc and el) else np.nan
cin = np.trapz(B[:lfc], zz[:lfc]) if lfc else np.nan
log("LCL=%.1f hPa; LFC=%s; EL=%s" % (p_lcl / 100,
                                   ("%.1f hPa (z=%.0f m)" % (pp[lfc] / 100, zz[lfc])) if lfc else "无",
                                   ("%.1f hPa (z=%.0f m)" % (pp[el] / 100, zz[el])) if el else "无"))
log("CAPE=%.0f J/kg（正面积）；CIN=%.0f J/kg（负面积，地面→LFC）" % (cape, cin))
log("对照 ch13（未虚温订正）：正 711 / 负 −1330 J/kg")

# 图 ch14_cape.png
fig, axes = plt.subplots(1, 2, figsize=(12, 5.6))
ax = axes[0]
ax.plot(Tp - 273.15, np.log(1000.0 / (pp / 100)), "r-", lw=2, label="气块 Tv")
ax.plot(Tve - 273.15, np.log(1000.0 / (pp / 100)), "k-", lw=1.6, label="环境 Tv")
if lfc and el:
    sel = slice(lfc, el)
    ax.fill_betweenx(np.log(1000.0 / (pp[sel] / 100)), Tve[sel] - 273.15, Tp[sel] - 273.15,
                     color="tab:red", alpha=0.25, label="CAPE 正面积")
    sel2 = slice(0, lfc)
    ax.fill_betweenx(np.log(1000.0 / (pp[sel2] / 100)), Tp[sel2] - 273.15, Tve[sel2] - 273.15,
                     color="tab:blue", alpha=0.2, label="CIN 负面积")
ax.set_ylim(np.log(1000 / 200), np.log(1000 / 1000))
ax.set_xlabel("温度 / ℃")
ax.set_ylabel("ln(p00/p)")
ax.set_title("气块与环境虚温（含 CAPE/CIN 面积）")
ax.legend(fontsize=8)
ax.grid(alpha=0.3)
ax2 = axes[1]
ax2.plot(B, zz / 1000.0, "k-", lw=2)
ax2.fill_betweenx(zz / 1000.0, 0, B, where=B > 0, color="tab:red", alpha=0.3)
ax2.fill_betweenx(zz / 1000.0, 0, B, where=B <= 0, color="tab:blue", alpha=0.25)
ax2.set_xlabel("净浮力 B / (m s$^{-2}$)")
ax2.set_ylabel("z / km")
ax2.set_title("净浮力剖面（CAPE=%.0f, CIN=%.0f J/kg）" % (cape, cin))
ax2.grid(alpha=0.3)
fig.tight_layout()
fig.savefig(os.path.join(FIGD, "ch14_cape.png"), dpi=150)
plt.close(fig)
log("已出图 doc/figs/ch14_cape.png")

# E1 图
fig, axes = plt.subplots(1, 2, figsize=(12, 5.6))
th_prof = theta(T, P)
te_prof = th_prof * np.exp(Lv(T) * (eps * es_w(TD) / (P - es_w(TD))) / (cpd * T))
ax = axes[0]
ax.plot(th_prof, z / 1000.0, "o-", lw=2, label=r"$\theta$")
ax.plot(te_prof, z / 1000.0, "s--", lw=2, label=r"$\theta_e$（实测比湿口径）")
ax.set_xlabel("K")
ax.set_ylabel("z / km")
ax.set_title("书习题 7 探空：θ 与 θe 廓线")
ax.legend()
ax.grid(alpha=0.3)
ax2 = axes[1]
mids = [(P[i] + P[i + 1]) / 200.0 for i in range(len(P) - 1)]
gams = [c[2] for c in cats]
gams_s = [c[3] for c in cats]
yy = np.arange(len(gams))
ax2.barh(yy - 0.18, gams, height=0.36, label="Γ", color="tab:orange")
ax2.barh(yy + 0.18, gams_s, height=0.36, label="γs（闭合式）", color="tab:green")
ax2.axvline(gammad, color="k", ls="--", lw=1, label="γd=%.2f" % gammad)
ax2.set_yticks(yy)
ax2.set_yticklabels(["%d-%d" % (c[0] / 100, c[1] / 100) for c in cats], fontsize=8)
ax2.set_xlabel("K/km")
ax2.set_title("逐层 Γ vs γs：判定条件性不稳定层")
ax2.legend(fontsize=8)
ax2.grid(alpha=0.3, axis="x")
fig.tight_layout()
fig.savefig(os.path.join(FIGD, "ch14_stability.png"), dpi=150)
plt.close(fig)
log("已出图 doc/figs/ch14_stability.png")

# ---------------- E3 混合层（wrfinput 剖面） ----------------
log("\n### E3 混合层 θ 守恒（模型剖面；(6.5.6)）")
try:
    from netCDF4 import Dataset
    nc = Dataset(os.path.join(ROOT, "workspace", "data", "ch10", "wrfinput_d01.nc"))
    lat = nc.variables["XLAT"][0]
    lon = nc.variables["XLONG"][0]
    d2 = (lat - 36.0) ** 2 + (lon - 103.75) ** 2
    jj, ii = np.unravel_index(np.argmin(d2), d2.shape)
    th_f = nc.variables["T"][0, :, jj, ii] + 300.0
    ph = nc.variables["PH"][0, :, jj, ii] + nc.variables["PHB"][0, :, jj, ii]
    zz_f = 0.5 * (ph[1:] + ph[:-1]) / 9.81
    # 质量加权平均 θ（用 ρ 近似按 dz 权重；p 权重法）
    pp_f = nc.variables["P"][0, :, jj, ii] + nc.variables["PB"][0, :, jj, ii]
    nc.close()
    # 0-500 m 与 0-1000 m 层的 (6.5.6) 式：θ̄ = −∫θdp/(p1−p2)
    def theta_bar(z_lo, z_hi):
        m = (zz_f >= z_lo) & (zz_f <= z_hi)
        zs_ = zz_f[m]
        ths_ = th_f[m]
        ps_ = pp_f[m]
        # 按高度排序（升序）后对 p 积分
        order = np.argsort(zs_)
        zs_, ths_, ps_ = zs_[order], ths_[order], ps_[order]
        return -np.trapz(ths_, ps_) / (ps_[0] - ps_[-1])
    tb500 = theta_bar(zz_f[0], zz_f[0] + 500)
    tb1000 = theta_bar(zz_f[0], zz_f[0] + 1000)
    tb2000 = theta_bar(zz_f[0], zz_f[0] + 2000)
    log("格点 (%.2fN, %.2fE)；z0=%.0f m" % (lat[jj, ii], lon[jj, ii], zz_f[0]))
    log("质量加权平均 θ：0–500 m %.2f K；0–1000 m %.2f K；0–2000 m %.2f K" % (tb500, tb1000, tb2000))
    fig, ax = plt.subplots(figsize=(6.4, 7))
    ax.plot(th_f, zz_f / 1000.0, "o-", ms=3, lw=1.6, label=r"$\theta$（T+300）")
    ax.axvline(tb500, color="tab:red", ls="--", lw=1.2, label=r"0–500 m 平均 $\bar{\theta}$=%.2f K" % tb500)
    ax.axvline(tb1000, color="tab:blue", ls=":", lw=1.2, label=r"0–1000 m 平均 $\bar{\theta}$=%.2f K" % tb1000)
    ax.set_xlabel("θ / K")
    ax.set_ylabel("z / km")
    ax.set_ylim(0, 16)
    ax.set_title("wrfinput 兰州柱：θ 剖面与混合层平均（(6.5.6)）")
    ax.legend(fontsize=8)
    ax.grid(alpha=0.3)
    fig.tight_layout()
    fig.savefig(os.path.join(FIGD, "ch14_mixed_layer.png"), dpi=150)
    plt.close(fig)
    log("已出图 doc/figs/ch14_mixed_layer.png")
    # 近地面 θ 梯度判据（(6.8.13)）
    sel = zz_f < zz_f[0] + 300
    dthdz = np.gradient(th_f[sel], zz_f[sel])
    log("近地面 300 m 内 ∂θ/∂z 范围：%.4f ~ %.4f K/m（>0 → 稳定；<0 → 超绝热）"
        % (dthdz.min(), dthdz.max()))
except Exception as ex:
    log("E3 失败：", ex)

# ---------------- E4 薄层法判据 (6.8.21) ----------------
log("\n### E4 薄层法判据 (6.8.21)（条件性不稳定层的积云密度调节）")
Gam = 6.0        # K/km（γd>Γ>γs）
gs_rep = 4.2     # K/km 代表值
ratio = (Gam - gs_rep) / (gammad - Gam)
log("取 Γ=%.1f、γs=%.1f K/km → (Γ−γs)/(γd−Γ) = %.3f" % (Gam, gs_rep, ratio))
log("判据：该比值 > A1/A2=w2/w1 → 不稳定；= → 中性；< → 稳定")
for a in [0.1, 0.3, 0.5, 1.0, 2.0, 5.0]:
    verdict = "不稳定（少而强的积云：有利发展）" if ratio > a else ("中性" if abs(ratio - a) < 1e-6 else "稳定（积云密集：抑制发展）")
    log("  A1/A2 = w2/w1 = %.1f → %s" % (a, verdict))

log("\n全部实验完成。")
LOG.close()