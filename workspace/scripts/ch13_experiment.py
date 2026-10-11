# -*- coding: utf-8 -*-
"""
ch13_experiment.py —— ch13 微物理族轻轨实验（本地 WRFlearn，无需集群）

A 组：书习题 7 探空 → 埃玛图（T-lnP）原理图
      干绝热线族 (6.4.3) / 假绝热线族（数值积分 (6.3.3)）/ 饱和比湿线 (6.4.4 物理式)
      层结曲线 + 气块路径 + LCL（精确解 vs (6.2.23) 估算）+ LFC 判定
B 组：位温/θse 保守性核验 + 潜热 Lv(T) 三口径对照（书 6.1.42 / WRF XLV1 / Thompson）
      + 书习题 8 气块速度复算
C 组：饱和调整三法对照（Thompson Newton 迭代 / WSM6 conden 单步 / 定点迭代"真值"）
D 组：WRF 实际数据（wrfinput_d01）剖面核验：θ 与 θse

输出：doc/figs/ch13_emagram.png、ch13_theta_se.png、ch13_satadj.png
日志：workspace/logs/ch13_experiment.log
"""
import os
import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

plt.rcParams["font.sans-serif"] = ["SimHei"]
plt.rcParams["axes.unicode_minus"] = False

# ---------------- 路径 ----------------
ROOT = r"d:\Code\Learn\WRF"
FIGD = os.path.join(ROOT, "doc", "figs")
LOGD = os.path.join(ROOT, "workspace", "logs")
os.makedirs(FIGD, exist_ok=True)
os.makedirs(LOGD, exist_ok=True)
LOG = open(os.path.join(LOGD, "ch13_experiment.log"), "w", encoding="utf-8")


def log(*a):
    s = " ".join(str(x) for x in a)
    print(s)
    LOG.write(s + "\n")


# ---------------- 物理常数（与源码严格对齐） ----------------
Rd = 287.04          # 干空气气体常数（Thompson）
Rv = 461.6           # 水汽气体常数（WRF module_model_constants r_v）
cpd = 1004.0         # Thompson Cp
kappa = Rd / cpd     # 0.2859 ≈ κd=0.286（书 6.2.3）
eps = 0.622
g = 9.81

# WSM6 fpvs 常数（module_model_constants + mp_wsm6.F90）
psat = 610.78        # Pa
TTP = 273.15 + 0.01
cpv = 4.0 * Rv       # 1846.4（cpv=4*r_v）
cliq = 4190.0
cice = 2106.0
hvap = 2.5e6
hsub = 2.85e6

dl_dt = cpv - cliq
XA = -dl_dt / Rv                       # 2320/461.6 = 5.027
XB = XA + hvap / (Rv * TTP)
dl_dt_i = cpv - cice
XAI = -dl_dt_i / Rv                    # 236.4/461.6 = 0.512
XBI = XAI + hsub / (Rv * TTP)


def es_w(T):
    """饱和水汽压（水面），WSM6 fpvs 积分式，Pa"""
    tr = TTP / T
    return psat * (tr ** XA) * np.exp(XB * (1.0 - tr))


def es_i(T):
    """饱和水汽压（冰面），Pa"""
    tr = TTP / T
    return psat * (tr ** XAI) * np.exp(XBI * (1.0 - tr))


def rs_w(T, p):
    """饱和混合比 qs（水面），kg/kg；p 为气压 Pa"""
    e = es_w(T)
    e = np.minimum(e, 0.99 * p)
    return eps * e / (p - e)


def desdT(T):
    """d(es)/dT（克劳修斯-克拉珀龙，用 Lv(T)）"""
    return Lv_book(T) * es_w(T) / (Rv * T * T)


# --------- 潜热三口径（书 6.1.42 / WRF XLV1 / Thompson 3206 行） ---------
def Lv_book(T):      # Lv = 2.5E6 - 2323 t
    return 2.5e6 - 2323.0 * (T - 273.15)


def Lv_wsm6(T):      # xlcal: xlv0 - xlv1*(t-t0c), xlv1 = cliq-cpv = 2343.6
    return 2.5e6 - 2343.6 * (T - 273.15)


def Lv_thompson(T):  # lvap = lvap0 + (2106.-4218.)*tempc
    return 2.5e6 - 2112.0 * (T - 273.15)


log("=" * 72)
log("ch13 实验：微物理族轻轨实验")
log("常数：Rd=%.2f Rv=%.1f cpd=%.1f kappa=%.4f" % (Rd, Rv, cpd, kappa))
log("rhs: XA=%.4f XB=%.4f XAI=%.4f XBI=%.4f" % (XA, XB, XAI, XBI))
log("=" * 72)

# ================================================================
# A 组：埃玛图（书习题 7 探空）
# ================================================================
log("\n### A 组：埃玛图原理图（书习题 7，印刷页 169）")

P_TAB = np.array([1000, 900, 850, 800, 700, 600, 500, 400, 300, 200]) * 100.0
T_TAB = np.array([23.0, 20.5, 17.0, 12.0, 4.5, -4.0, -12.1, -23.0, -32.5, -45.3]) + 273.15
TD_TAB = np.array([19.0, 10.4, 7.6, 6.8, -1.1, -8.5, -19.2, -29.5, -45.0, -59.5]) + 273.15


def dTdlnp_moist(T, p, Lv_f=Lv_book):
    """假绝热方程 (6.3.3) 求 dT/dlnp：cpd dT - Rd T dlnp + Lv drs = 0"""
    e = es_w(T)
    e = min(e, 0.99 * p)
    rs = eps * e / (p - e)
    es_p = desdT(T)
    num = Rd * T + Lv_f(T) * rs * p / (p - e)
    den = cpd + Lv_f(T) * eps * p * es_p / (p - e) ** 2
    return num / den


def pseudo_adiabat(T0, p0, p_end, n=400, Lv_f=Lv_book):
    """从 (T0,p0) 沿假绝热线积分到 p_end（p_end < p0），返回 T、p 数组"""
    lnp0, lnp1 = np.log(p0), np.log(p_end)
    lns = np.linspace(lnp0, lnp1, n + 1)
    Ts = np.empty(n + 1)
    Ts[0] = T0
    T = T0
    for i in range(n):
        ln, ln_ = lns[i], lns[i + 1]
        h = ln_ - ln
        p = np.exp(ln)
        k1 = dTdlnp_moist(T, p, Lv_f)
        k2 = dTdlnp_moist(T + 0.5 * h * k1, np.exp(ln + 0.5 * h), Lv_f)
        k3 = dTdlnp_moist(T + 0.5 * h * k2, np.exp(ln + 0.5 * h), Lv_f)
        k4 = dTdlnp_moist(T + h * k3, np.exp(ln_), Lv_f)
        T = T + h / 6.0 * (k1 + 2 * k2 + 2 * k3 + k4)
        Ts[i + 1] = T
    return Ts, np.exp(lns)


# --- 气块路径：地面 1000 hPa, 23C, Td=19C ---
T0 = T_TAB[0]
p0 = P_TAB[0]
q0 = rs_w(TD_TAB[0], p0)
Td0 = TD_TAB[0]

# 精确 LCL：干绝热上 T(p) 与 q0 的饱和线相交
def T_dry(p, T_s, p_s):
    return T_s * (p / p_s) ** kappa


def lcl_solve(T_s, p_s, q0):
    """求 p_LCL：rs_w(T_dry(p), p) = q0，二分法"""
    lo, hi = p_s, 50.0 * 100.0
    for _ in range(200):
        mid = 0.5 * (lo + hi)
        f = rs_w(T_dry(mid, T_s, p_s), mid) - q0
        if f > 0:      # 未饱和（qs > q）
            lo = mid
        else:
            hi = mid
    return 0.5 * (lo + hi)


p_lcl = lcl_solve(T0, p0, q0)
T_lcl = T_dry(p_lcl, T0, p0)
log("A1 LCL：p=%.1f hPa, T=%.2f C, q0=%.5f kg/kg" % (p_lcl / 100, T_lcl - 273.15, q0))

# 高度（静力，干绝热段）：z = -(Rd T/g) dlnp
def z_of_p(p, T_s, p_s):
    n = 200
    lns = np.linspace(np.log(p_s), np.log(p), n + 1)
    zs = 0.0
    for i in range(n):
        ln, ln_ = lns[i], lns[i + 1]
        Tm = T_dry(np.exp(0.5 * (ln + ln_)), T_s, p_s)
        zs += -Rd * Tm / g * (ln_ - ln)
    return zs

z_lcl = z_of_p(p_lcl, T0, p0)
z_est = 123.0 * ((T0 - 273.15) - (Td0 - 273.15))
log("A2 LCL 高度：精确 %.0f m；书 (6.2.23) 估算 123*(%.1f-%.1f)=%.0f m；差 %.1f%%"
    % (z_lcl, T0 - 273.15, Td0 - 273.15, z_est, 100.0 * (z_lcl - z_est) / z_est))

# 气块路径全段：LCL 以下干绝热，以上假绝热
p_path = np.exp(np.linspace(np.log(p0), np.log(200 * 100.0), 500))
T_path = np.where(p_path >= p_lcl, T_dry(p_path, T0, p0), np.nan)
Ts_m, ps_m = pseudo_adiabat(T_lcl, p_lcl, 200 * 100.0, n=400)
# 插值到统一 grid
T_path = np.where(p_path >= p_lcl, T_dry(p_path, T0, p0),
                  np.interp(np.log(p_path), np.log(ps_m[::-1]), Ts_m[::-1]))

# LFC：气块温度首次高于环境
T_env_lin = np.interp(np.log(p_path), np.log(P_TAB[::-1]), T_TAB[::-1])
lfc_idx = None
for i in range(len(p_path)):
    if p_path[i] < p_lcl and T_path[i] > T_env_lin[i]:
        lfc_idx = i
if lfc_idx is not None:
    log("A3 LFC：p=%.1f hPa, z=%.0f m（气块首次高于环境）"
        % (p_path[lfc_idx] / 100, z_of_p(p_path[lfc_idx], T0, p0)))

# 正/负能量面积（近似，用 p 坐标近似 E = Rd*∫(Tp-Te) dlnp）
pos, neg = 0.0, 0.0
lns = np.log(p_path)
for i in range(len(p_path) - 1):
    d = -0.5 * ((T_path[i] - T_env_lin[i]) + (T_path[i + 1] - T_env_lin[i + 1])) * (lns[i + 1] - lns[i]) * Rd
    if T_path[i] > T_env_lin[i]:
        pos += d
    else:
        neg += d
log("A4 气块路径净能量：正能区 %.0f J/kg，负能区 %.0f J/kg（近似，未做虚温订正）" % (pos, neg))

# ---------------- 绘图 ----------------
fig, ax = plt.subplots(figsize=(10.5, 8.5))
ylim = (np.log(1000.0 / 1050.0), np.log(1000.0 / 200.0))
xlim = (-80, 45)


def yof(p):
    return np.log(1000.0 / (p / 100.0))


# 干绝热线族 (6.4.3)
for th in range(250, 461, 10):
    p = np.linspace(1050, 200, 200) * 100.0
    T = th * (p / 1.0e5) ** kappa
    m = (T - 273.15 >= -80) & (T - 273.15 <= 45)
    ax.plot(T[m] - 273.15, yof(p[m]), color="0.75", lw=0.6, zorder=1)

# 假绝热线族：1000 hPa 处温度 0..36C（每 4C）
for t0c_val in range(-4, 37, 4):
    Ts, ps = pseudo_adiabat(t0c_val + 273.15, 1000.0 * 100.0, 200 * 100.0, n=300)
    ax.plot(Ts - 273.15, yof(ps), color="0.55", lw=0.9, ls="--", zorder=1)

# 饱和比湿线 (6.4.4 物理式)：qs = 0.5, 1, 2, 4, 8, 16 g/kg
for qs_g in [0.5, 1, 2, 4, 8, 16]:
    qs = qs_g / 1000.0
    T = np.linspace(233, 313, 300)
    e = es_w(T)
    p = eps * e / qs + e
    m = (p <= 1050e2) & (p >= 200e2)
    ax.plot(T[m] - 273.15, yof(p[m]), color="0.4", lw=0.9, ls=":", zorder=1)
    idx = np.argmin(np.abs(np.log(p[m]) - np.log(850e2)))
    if m.sum() > 0:
        ax.annotate("%g" % qs_g, (T[m][idx] - 273.15, yof(p[m][idx])),
                    fontsize=7.5, color="0.35")

# 层结曲线（书习题 7 探空）
ax.plot(T_TAB - 273.15, yof(P_TAB), "k-", lw=2.0, label="温度层结曲线（书习题 7）", zorder=4)
ax.plot(TD_TAB - 273.15, yof(P_TAB), "k--", lw=1.6, label="露点层结曲线", zorder=4)

# 气块路径
ax.plot(T_path - 273.15, yof(p_path), "r-", lw=2.2, label="气块路径（干绝热→假绝热）", zorder=5)
ax.plot(T_dry(p_path[p_path >= p_lcl], T0, p0) - 273.15, yof(p_path[p_path >= p_lcl]),
        "r-", lw=2.2, zorder=5)
ax.plot(Ts_m - 273.15, yof(ps_m), "r-", lw=2.2, zorder=5)

# 标记点
ax.plot([T0 - 273.15], [yof(p0)], "ko", ms=6, zorder=6)
ax.annotate("地面 23.0 C", (T0 - 273.15, yof(p0)), xytext=(6, -14),
            textcoords="offset points", fontsize=9)
ax.plot([T_lcl - 273.15], [yof(p_lcl)], "bs", ms=8, zorder=6)
ax.annotate("LCL  %.0f hPa (%.0f m)" % (p_lcl / 100, z_lcl),
            (T_lcl - 273.15, yof(p_lcl)), xytext=(-96, 6), textcoords="offset points", fontsize=9)
if lfc_idx is not None:
    ax.plot([T_path[lfc_idx] - 273.15], [yof(p_path[lfc_idx])], "g^", ms=9, zorder=6)
    ax.annotate("LFC  %.0f hPa" % (p_path[lfc_idx] / 100),
                (T_path[lfc_idx] - 273.15, yof(p_path[lfc_idx])),
                xytext=(-64, -14), textcoords="offset points", fontsize=9)

# 坐标与刻度：纵轴直接标气压
for p in [1000, 900, 850, 800, 700, 600, 500, 400, 300, 200]:
    y = yof(p * 100.0)
    ax.axhline(y, color="k", lw=0.4, alpha=0.4)
ax.set_yticks([yof(p * 100.0) for p in [1000, 900, 850, 800, 700, 600, 500, 400, 300, 200]])
ax.set_yticklabels(["1000", "900", "850", "800", "700", "600", "500", "400", "300", "200"])
ax.set_ylabel("p / hPa（纵坐标 = $\\ln(p_{00}/p)$）")
ax.set_xlim(xlim)
ax.set_ylim(ylim)
ax.set_xlabel("温度 / C")
ax.set_title("书习题 7 探空的埃玛图（T-lnP）：干绝热线、假绝热线、饱和比湿线（g/kg）与气块路径")
ax.legend(loc="lower left", fontsize=9)
fig.tight_layout()
fig.savefig(os.path.join(FIGD, "ch13_emagram.png"), dpi=150)
plt.close(fig)
log("A5 已出图 doc/figs/ch13_emagram.png")

# ================================================================
# B 组：θ/θse 与潜热口径
# ================================================================
log("\n### B 组：位温-θse 保守性 + Lv(T) 三口径")


def theta(T, p):
    return T * (1.0e5 / p) ** kappa


def theta_se(T, p):
    """书 (6.3.8)：θse = θd exp(rs Lv /(cpd T))，θd = T (1000/pd)^(Rd/cpd)"""
    e = es_w(T)
    pd = np.maximum(p - e, 1.0)
    rs = eps * e / (p - e)
    thd = T * (1.0e5 / pd) ** kappa
    return thd * np.exp(rs * Lv_book(T) / (cpd * T))


# θse 沿假绝热积分（自 LCL 起）
thse0 = theta_se(T_lcl, p_lcl)
thse_arr = np.array([theta_se(t, p) for t, p in zip(Ts_m, ps_m)])
drift = (thse_arr - thse0) / thse0 * 100.0
log("B1 θse 保守性：LCL 处 %.2f K，200 hPa 处 %.2f K，最大漂移 %.2f%%（(6.3.8) 近似式）"
    % (thse0, thse_arr[-1], np.max(np.abs(drift))))

# γs 两种形式对照（6.3.5 闭合式 vs 数值微分）
rows = []
for p_chk in [1000, 850, 700, 500, 300]:
    T_ = np.interp(np.log(1000.0 / p_chk), yof(ps_m[::-1]), Ts_m[::-1])
    e = es_w(T_)
    rs = eps * e / (p_chk * 100.0 - e)
    gd = g / cpd
    Lv_ = Lv_book(T_)
    gs_close = gd * (1 + Lv_ * rs / (Rd * T_)) / (1 + eps * Lv_ ** 2 * rs / (cpd * Rd * T_ ** 2))
    dTdlnp = dTdlnp_moist(T_, p_chk * 100.0)
    # dz = -Rd T/g dlnp（静力）→ γs = (dT/dlnp)·g/(Rd T)
    gs_num = dTdlnp * (g / (Rd * T_))
    rows.append((p_chk, gs_close, gs_num))
    log("B2 p=%4d hPa: γs(6.3.5)=%.3f K/km, γs(数值)=%.3f K/km, γd=%.2f K/km"
        % (p_chk, gs_close * 1000, gs_num * 1000, gd * 1000))

# 习题 8：气块速度（900→700 hPa）
T9, p9 = 280.0, 900 * 100.0
Ts8, ps8 = pseudo_adiabat(T9, p9, 700 * 100.0, n=300)
Tenv = T_dry(ps8, T9, p9)  # 环境=干绝热
Tpar = Ts8
# 几何厚度
z8 = np.zeros_like(ps8)
for i in range(1, len(ps8)):
    Tm = 0.5 * (Tenv[i] + Tenv[i - 1])
    z8[i] = z8[i - 1] + (-Rd * Tm / g) * (np.log(ps8[i]) - np.log(ps8[i - 1]))
# 浮力（未做虚温订正 / 做虚温订正）
qs8 = rs_w(Tpar, ps8)
B1 = g * (Tpar - Tenv) / Tenv
B2 = g * (Tpar * (1 + 0.608 * qs8) - Tenv) / (Tenv * (1 + 0.608 * qs8 * 0.5))
W1 = np.sqrt(2 * np.trapz(B1, z8))
W2 = np.sqrt(2 * np.trapz(B2, z8))
log("B3 习题 8：700 hPa 处气块速度 未订正 %.1f m/s；虚温订正 %.1f m/s（δT=%.2f K）"
    % (W1, W2, Tpar[-1] - Tenv[-1]))

# Lv(T) 三口径图
fig, axes = plt.subplots(1, 3, figsize=(15, 4.6))
tt = np.linspace(233.15, 313.15, 200)
axes[0].plot(tt - 273.15, Lv_book(tt) / 1e6, lw=2, label="书 (6.1.42): -2323")
axes[0].plot(tt - 273.15, Lv_wsm6(tt) / 1e6, lw=2, ls="--", label="WRF WSM6: -2343.6")
axes[0].plot(tt - 273.15, Lv_thompson(tt) / 1e6, lw=2, ls=":", label="Thompson: -2112")
axes[0].set_xlabel("T / C")
axes[0].set_ylabel("Lv / (1e6 J/kg)")
axes[0].set_title("潜热 Lv(T) 三种口径（同一模式版本内）")
axes[0].legend(fontsize=9)
axes[0].grid(alpha=0.3)

axes[1].plot(thse_arr, ps_m / 100.0, lw=2)
axes[1].set_ylim(1000, 200)
axes[1].set_xlim(min(thse_arr) - 1, max(thse_arr) + 1)
axes[1].set_ylabel("p / hPa")
axes[1].set_xlabel(r"$\theta_{se}$ / K（沿假绝热路径）")
axes[1].set_title("θse 沿假绝热上升的近似守恒（(6.3.8) 式）")
axes[1].grid(alpha=0.3)

# D 组数据
try:
    from netCDF4 import Dataset
    nc = Dataset(os.path.join(ROOT, "workspace", "data", "ch10", "wrfinput_d01.nc"))
    lat = nc.variables["XLAT"][0]
    lon = nc.variables["XLONG"][0]
    d2 = (lat - 36.0) ** 2 + (lon - 103.75) ** 2
    jj, ii = np.unravel_index(np.argmin(d2), d2.shape)
    Tp = nc.variables["T"][0, :, jj, ii] + 300.0
    qv = nc.variables["QVAPOR"][0, :, jj, ii]
    pp = nc.variables["P"][0, :, jj, ii] + nc.variables["PB"][0, :, jj, ii]
    ph = nc.variables["PH"][0, :, jj, ii] + nc.variables["PHB"][0, :, jj, ii]
    zz = 0.5 * (ph[1:] + ph[:-1]) / 9.81
    th_field = Tp
    thse_field = np.array([theta_se(Tp[k] * (pp[k] / 1e5) ** kappa, pp[k]) for k in range(len(pp))])
    axes[2].plot(th_field, zz / 1000.0, lw=2, label=r"$\theta$（T+300，模式场）")
    axes[2].plot(thse_field, zz / 1000.0, lw=2, ls="--", label=r"$\theta_{se}$（(6.3.8) 复算）")
    axes[2].set_ylabel("z / km")
    axes[2].set_xlabel("K")
    axes[2].set_ylim(0, 16)
    axes[2].set_title("wrfinput 兰州点(%.2fN,%.2fE) 剖面" % (lat[jj, ii], lon[jj, ii]))
    axes[2].legend(fontsize=9)
    axes[2].grid(alpha=0.3)
    nc.close()
    log("D1 wrfinput 剖面：格点 (%.2fN, %.2fE)，层数 %d，地面 p=%.1f hPa"
        % (lat[jj, ii], lon[jj, ii], len(pp), pp[0] / 100))
except Exception as ex:
    axes[2].text(0.1, 0.5, "wrfinput 读取失败：%s" % ex, transform=axes[2].transAxes)
    log("D1 失败：", ex)

fig.tight_layout()
fig.savefig(os.path.join(FIGD, "ch13_theta_se.png"), dpi=150)
plt.close(fig)
log("B4 已出图 doc/figs/ch13_theta_se.png")

# ================================================================
# C 组：饱和调整三法对照
# ================================================================
log("\n### C 组：饱和调整三法（Thompson Newton vs WSM6 conden vs 定点迭代）")


def adj_truth(T0, p, qv0, Lv_f, cp_f):
    """阻尼定点迭代真值：T' = T0 + Lv(T')·(qv0 - qs(T'))/cp，
    耦合系数 |d/dT'| > 1（约 3~4），必须阻尼；阻尼因子 0.25"""
    Tcur = T0
    for _ in range(600):
        Tn = T0 + Lv_f(Tcur) * (qv0 - rs_w(Tcur, p)) / cp_f
        Tcur = Tcur + 0.25 * (Tn - Tcur)
    clap = qv0 - rs_w(Tcur, p)
    return Tcur, clap


def adj_thompson(T0, p, qv0):
    qvs = rs_w(T0, p)
    ocp = 1.0 / (cpd * (1.0 + 0.887 * qv0))
    lvap = Lv_thompson(T0)
    lvt2 = lvap * lvap * ocp / Rv / T0 / T0
    clap = (qv0 - qvs) / (1.0 + lvt2 * qvs)
    for _ in range(3):
        fcd = qvs * np.exp(lvt2 * clap) - qv0 + clap
        dfcd = qvs * lvt2 * np.exp(lvt2 * clap) + 1.0
        clap = clap - fcd / dfcd
    dT = lvap * clap * ocp
    return T0 + dT, clap


def adj_wsm6(T0, p, qv0):
    qsat = min(rs_w(T0, p), 0.99 * p)
    xl = Lv_wsm6(T0)
    cpm = cpd * (1.0 - qv0) + qv0 * cpv
    pcond = (max(qv0, 1e-15) - qsat) / (1.0 + xl * xl / (Rv * cpm) * qsat / T0 / T0)
    dT = xl * pcond / cpm
    return T0 + dT, pcond


log("T0(C)  p(hPa)  ss      | Thompson=3iter: ss'(残差) dT | WSM6-conden: ss'(残差) dT | 真值 dT")
cases = []
for t0c in [-10.0, 0.0, 25.0]:
    for pchk in [1000, 850, 700]:
        for ss in [5e-4, 2e-3, 5e-3, 2e-2]:
            T0_ = t0c + 273.15
            p_ = pchk * 100.0
            qvs = rs_w(T0_, p_)
            qv0 = qvs * (1.0 + ss)
            Tc_t, cl_t = adj_thompson(T0_, p_, qv0)
            Tc_w, cl_w = adj_wsm6(T0_, p_, qv0)
            Tc_r, cl_r = adj_truth(T0_, p_, qv0, Lv_thompson, cpd)
            Tc_rw, cl_rw = adj_truth(T0_, p_, qv0, Lv_wsm6, cpd * (1 - qv0) + qv0 * cpv)
            res_t = qv0 - cl_t - rs_w(Tc_t, p_)
            res_w = qv0 - cl_w - rs_w(Tc_w, p_)
            res_truth = qv0 - cl_r - rs_w(Tc_r, p_)
            cases.append(dict(t0c=t0c, p=pchk, ss=ss,
                              rest=abs(res_t), resw=abs(res_w),
                              dtt=(Tc_t - T0_), dtw=(Tc_w - T0_), dtr=(Tc_r - T0_),
                              dtrw=(Tc_rw - T0_)))
log("残差单位为 kg/kg；ss'= 调整后 qv'/qs(T')-1")
for c_ in cases:
    if c_["ss"] >= 2e-3 and c_["t0c"] == 25.0:
        log("T=%5.1fC p=%4d ss=%.4f | Thm: |Δq|=%.2e dT=%.4f | WSM6: |Δq|=%.2e dT=%.4f | truth dT=%.4f"
            % (c_["t0c"], c_["p"], c_["ss"], c_["rest"], c_["dtt"], c_["resw"], c_["dtw"], c_["dtr"]))

# 汇总统计
res_t_all = np.array([c_["rest"] for c_ in cases])
res_w_all = np.array([c_["resw"] for c_ in cases])
err_t_all = np.array([c_["dtt"] - c_["dtr"] for c_ in cases])
err_w_all = np.array([c_["dtw"] - c_["dtrw"] for c_ in cases])
log("C 汇总：Thompson 3-iter 残差 max=%.2e mean=%.2e；WSM6 conden 残差 max=%.2e mean=%.2e"
    % (res_t_all.max(), res_t_all.mean(), res_w_all.max(), res_w_all.mean()))
log("C 汇总：dT 误差 Thompson max=%.2e K；WSM6 max=%.2e K"
    % (np.abs(err_t_all).max(), np.abs(err_w_all).max()))

# 图：残差 & dT 误差 vs ss（固定 T=25C, p=1000hPa）
fig, axes = plt.subplots(1, 2, figsize=(11, 4.4))
sel = [(c_) for c_ in cases if c_["t0c"] == 25.0 and c_["p"] == 1000]
ssv = np.array([c_["ss"] for c_ in sel])
axes[0].loglog(ssv, [c_["rest"] for c_ in sel], "o-", label="Thompson Newton(3 次)")
axes[0].loglog(ssv, [c_["resw"] for c_ in sel], "s--", label="WSM6 conden(单步)")
axes[0].loglog(ssv, ssv * 1e-4, ":", color="0.5", label=r"$\propto ss$ 参考")
axes[0].set_xlabel("初始过饱和度 ss")
axes[0].set_ylabel("调整后饱和残差 |qv - qs(T)| / (kg/kg)")
axes[0].set_title("饱和调整残差（T=25C, p=1000 hPa）")
axes[0].legend(fontsize=9)
axes[0].grid(alpha=0.3)

ss_all = np.array([c_["ss"] for c_ in cases])
axes[1].semilogx(ss_all, [abs(c_["dtt"] - c_["dtr"]) for c_ in cases], "o", ms=4, label="Thompson |dT 误差|")
axes[1].semilogx(ss_all, [abs(c_["dtw"] - c_["dtrw"]) for c_ in cases], "s", ms=4, label="WSM6 |dT 误差|")
axes[1].set_xlabel("初始过饱和度 ss")
axes[1].set_ylabel("增温误差 / K")
axes[1].set_title("相对定点迭代真值的增温误差（全用例）")
axes[1].legend(fontsize=9)
axes[1].grid(alpha=0.3)
fig.tight_layout()
fig.savefig(os.path.join(FIGD, "ch13_satadj.png"), dpi=150)
plt.close(fig)
log("C 已出图 doc/figs/ch13_satadj.png")

log("\n全部实验完成。")
LOG.close()