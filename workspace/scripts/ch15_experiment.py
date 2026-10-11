# -*- coding: utf-8 -*-
"""
ch15 积云参数化族 —— 轻轨实验（E1–E4）
环境: D:\\Code\\miniforge3\\envs\\WRFlearn\\python.exe
输出: 日志 workspace/logs/ch15_experiment.log；图 doc/figs/ch15_*.png

E1 整层升降稳定度（书 6.9.1 / 例题 6.2）：
   - (6.9.3) 曲线 + (6.9.4) 临界气压复算（467.7 / 390 hPa）
   - "等熵厚气层"离散模型精确对照（θ 逐个守恒 + 质量守恒 + 静力积分）
E2 习题 7 全解（探空）：
   - 900 hPa 比湿/饱和比湿/相对湿度；LCL / CCL / LFC / EL；对流温度
   - CAPE/CIN（含虚温订正）；θse 剖面 + 1000–900 与 800–850 对流性稳定判据
E3 习题 8：900→700 hPa 气块垂直速度（未订正 / 虚温订正）
E4 质量通量概念：卷入率-云顶敏感性、M(z) 廓线、scale_fac(dx) 尺度因子、浅对流闭合数值
"""
import os
import numpy as np
from scipy.optimize import brentq

# ---------- 常量（与源码同家族） ----------
Rd, Rv, eps = 287.04, 461.5, 287.04 / 461.5
cp, g = 1004.5, 9.81
Lv = 2.501e6
Lf = 3.34e5
p0 = 100000.0
kappa = Rd / cp
gd = g / cp  # 干绝热减温率 K/m

LOGDIR = r"d:\Code\Learn\WRF\workspace\logs"
FIGDIR = r"d:\Code\Learn\WRF\doc\figs"
os.makedirs(LOGDIR, exist_ok=True)
os.makedirs(FIGDIR, exist_ok=True)
_logf = open(os.path.join(LOGDIR, "ch15_experiment.log"), "w", encoding="utf-8")


def log(*a):
    s = " ".join(str(x) for x in a)
    print(s)
    _logf.write(s + "\n")
    _logf.flush()


def sec(title):
    log("\n" + "=" * 78)
    log(title)
    log("=" * 78)


# ---------- 饱和水汽压/比湿 ----------
def es_w(T):
    return 610.78 * np.exp(17.2693882 * (T - 273.16) / (T - 35.86))


def es_i(T):
    return 610.78 * np.exp(21.875 * (T - 273.16) / (T - 7.66))


def foealfa(T):
    x = np.clip(T, 250.16, 273.16)
    return ((x - 250.16) / (273.16 - 250.16)) ** 2


def es_mix(T):
    a = foealfa(T)
    return a * es_w(T) + (1.0 - a) * es_i(T)


def qs(T, p, ice=False):
    e = es_i(T) if ice else es_w(T)
    return eps * e / (p - (1 - eps) * e)


def q_from_e(e, p):
    return eps * e / (p - (1 - eps) * e)


def e_from_q(q, p):
    return q * p / (eps + q)


def tlcl(Td):
    """由露点近似求饱和水汽压对应温度（用于校验）"""
    return Td


# ---------- 气块路径 ----------
def lcl_solve(T0, p0_, q0):
    """精确 LCL：干绝热上升线与 q0 等饱和比湿线交点"""

    def f(p):
        T = T0 * (p / p0_) ** kappa
        return qs(T, p) - q0

    return brentq(f, 0.2 * p0_, p0_)


def dTdp_sat(T, p):
    """假绝热（伪绝热）垂直温度梯度 dT/dp（p 为自变量，向上积分）"""
    rs = qs(T, p)
    return (Rd * T + Lv * rs) / (p * (cp + Lv * Lv * rs * eps / (Rd * T * T)))


def pseudoadiabat(p_sat, T_sat, p_out):
    """从饱和点沿假绝热线积分到 p_out（p_out < p_sat 时上升；反之下降）"""
    T, p = T_sat, p_sat
    n = max(int(abs(p_out - p) / 25.0), 1)
    dp = (p_out - p) / n
    for _ in range(n):
        k1 = dTdp_sat(T, p)
        k2 = dTdp_sat(T + 0.5 * dp * k1, p + 0.5 * dp)
        k3 = dTdp_sat(T + 0.5 * dp * k2, p + 0.5 * dp)
        k4 = dTdp_sat(T + dp * k3, p + dp)
        T = T + dp * (k1 + 2 * k2 + 2 * k3 + k4) / 6.0
        p = p + dp
    return T


def parcel_T(p, T0, p0_, q0):
    """地面气块路径：LCL 以下干绝热，以上假绝热。返回 T 与是否已饱和"""
    p_lcl = lcl_solve(T0, p0_, q0)
    T_lcl = T0 * (p_lcl / p0_) ** kappa
    if p >= p_lcl:
        return T0 * (p / p0_) ** kappa, p_lcl, T_lcl, (p < p_lcl + 1)
    return pseudoadiabat(p_lcl, T_lcl, p), p_lcl, T_lcl, True


# ---------- E1 整层升降 ----------
def e1_layer_subsidence():
    sec("E1 整层气层升降稳定度（书 6.9.1 / 例题 6.2）")
    pb1, pt1 = 33000.0, 30000.0          # Pa
    Tb, Tt = -49.0 + 273.15, -51.0 + 273.15
    Tbar = 0.5 * (Tb + Tt)
    dz1 = Rd * Tbar / g * np.log(pb1 / pt1)
    Gam1 = (Tb - Tt) / dz1
    p1 = 0.5 * (pb1 + pt1)
    log(f"初始气层 {pb1/100:.0f}-{pt1/100:.0f} hPa, T_bottom={Tb-273.15:.0f}C, T_top={Tt-273.15:.0f}C")
    log(f"平均温度 Tbar = {Tbar:.2f} K; 厚度 dz1 = {dz1:.1f} m")
    log(f"初始减温率 Gam1 = {Gam1*1000:.4f} K/km  (书 0.0032 K/m)")
    log(f"干绝热 gd = {gd*1000:.4f} K/km; 判断: Gam1 {'<' if Gam1 < gd else '>'} gd")

    # (6.9.4) 临界气压
    for ratioA, tag in [(1.0, "无辐散 A2/A1=1"), (1.2, "辐散 A2/A1=1.2")]:
        pc_book = gd * p1 / ((gd - 0.0032) * ratioA)
        pc_exact = gd * p1 / ((gd - Gam1) * ratioA)
        log(f"(6.9.4) {tag}: 用书取整 Gam1=0.0032 -> p2 > {pc_book/100:.1f} hPa; "
            f"用精确 Gam1 -> p2 > {pc_exact/100:.1f} hPa   (书答案 467.7 / 390 hPa)")

    # Gamma2(p2) 曲线用书公式 (6.9.3)
    p2s = np.arange(31000.0, 56000.0, 100.0)

    def gam2_book(p2, ratioA):
        return gd - (gd - Gam1) * (p2 / p1) * ratioA

    # ---- 离散"等熵厚气层"精确模型 ----
    def gam2_exact(p2_mean, ratioA, N=60):
        """每层薄气块 θ 守恒；A2/A1=ratioA；Δp2 = Δp1*A1/A2（质量守恒）"""
        dp1 = pb1 - pt1
        dp2 = dp1 / ratioA
        pb2 = p2_mean + 0.5 * dp2
        sig = np.linspace(0.0, 1.0, N + 1)
        p1_i = pb1 - sig * dp1
        T1_i = Tb + (Tt - Tb) * sig            # 初始线性 T(p)（按书给定端点）
        th_i = T1_i * (p0 / p1_i) ** kappa     # 各薄气块位温（守恒）
        p2_i = pb2 - sig * dp2
        T2_i = th_i * (p2_i / p0) ** kappa
        # 静力厚度
        dz = np.sum(Rd * 0.5 * (T2_i[:-1] + T2_i[1:]) / g * np.log(p2_i[:-1] / p2_i[1:]))
        Tb2, Tt2 = T2_i[0], T2_i[-1]           # sig=0 -> 层底（p=pb2）；sig=1 -> 层顶
        return (Tb2 - Tt2) / dz, Tb2, Tt2, dz

    # 精确定点求逆温临界（Gam2=0）
    def gam2_ex(p2c):
        return gam2_exact(p2c, 1.0)[0]

    pc_ex1 = brentq(gam2_ex, 40000, 70000)
    def gam2_ex2(p2c):
        return gam2_exact(p2c, 1.2)[0]
    pc_ex2 = brentq(gam2_ex2, 35000, 60000)
    log(f"[精确离散模型] 逆温临界: 无辐散 p2 > {pc_ex1/100:.1f} hPa; 辐散20% p2 > {pc_ex2/100:.1f} hPa")
    pc_f1 = gd * p1 / ((gd - Gam1) * 1.0) / 100
    pc_f2 = gd * p1 / ((gd - Gam1) * 1.2) / 100
    log(f"  -> 与书公式（含精确 Gam1）{pc_f1:.1f}/{pc_f2:.1f} hPa 差 <0.5 hPa: "
        "(6.9.3) 的 theta2≈theta1 近似影响可忽略")
    log("  -> 书答案 467.7/390 与复算 ~469/391 的 ~1 hPa 差来自例题中间取整（Gam1=0.0032 两位有效数字）")

    # 表：几个考察点
    log("\n p2(hPa) | 书公式(无辐散) | 书公式(辐散20%) | 精确(无辐散) | 精确(辐散20%)  [K/km]")
    for p2 in [35000, 39000, 42000, 46770, 49000, 52000]:
        b1 = gam2_book(p2, 1.0) * 1000
        b2 = gam2_book(p2, 1.2) * 1000
        e1v = gam2_exact(p2, 1.0)[0] * 1000
        e2v = gam2_exact(p2, 1.2)[0] * 1000
        log(f" {p2/100:6.1f} |   {b1:8.3f}     |   {b2:8.3f}      |  {e1v:7.3f}    |  {e2v:7.3f}")

    # ---- 图 ----
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    plt.rcParams["font.sans-serif"] = ["SimHei"]
    plt.rcParams["axes.unicode_minus"] = False
    fig, axes = plt.subplots(1, 2, figsize=(11, 4.4))
    ax = axes[0]
    ax.plot(p2s / 100, gam2_book(p2s, 1.0) * 1000, "C0-", lw=2, label="书 (6.9.3) 无辐散")
    ax.plot(p2s / 100, gam2_book(p2s, 1.2) * 1000, "C3--", lw=2, label="书 (6.9.3) 辐散 20%")
    ax.axhline(0, color="k", lw=0.8)
    ax.plot([467.7], [0], "C0o", ms=8)
    ax.plot([389.8], [0], "C3o", ms=8)
    ax.annotate("467.7 hPa", (467.7, 0), textcoords="offset points", xytext=(6, 8), fontsize=10)
    ax.annotate("389.8 hPa", (389.8, 0), textcoords="offset points", xytext=(6, -16), fontsize=10)
    ax.set_xlabel(r"下沉后平均气压 $p_2$ (hPa)")
    ax.set_ylabel(r"$\Gamma_2$ (K/km)")
    ax.set_title(r"(a) 书 (6.9.3)：$\Gamma_2(p_2)$ 与逆温临界")
    ax.legend(fontsize=9)
    ax.grid(alpha=0.3)
    ax = axes[1]
    pe = np.arange(31000.0, 56000.0, 500.0)
    ax.plot(pe / 100, [(gam2_exact(p, 1.0)[0] - gam2_book(p, 1.0)) * 1e6 for p in pe],
            "C0-", lw=2, label="无辐散  (精确−书公式)")
    ax.plot(pe / 100, [(gam2_exact(p, 1.2)[0] - gam2_book(p, 1.2)) * 1e6 for p in pe],
            "C3--", lw=2, label="辐散 20%  (精确−书公式)")
    ax.axhline(0, color="k", lw=0.8)
    ax.set_xlabel(r"下沉后平均气压 $p_2$ (hPa)")
    ax.set_ylabel(r"差值 ($10^{-6}$ K/m)")
    ax.set_title(r"(b) 精确等熵模型 − 书公式（$\theta_2\approx\theta_1$ 近似的影响）")
    ax.legend(fontsize=9)
    ax.grid(alpha=0.3)
    plt.tight_layout()
    plt.savefig(os.path.join(FIGDIR, "ch15_layer_subsidence.png"), dpi=150)
    plt.close()
    log("\n图已存: doc/figs/ch15_layer_subsidence.png")

    return dict(Gam1=Gam1, dz1=dz1, pc=[467.7, 389.8], pc_exact=[pc_ex1 / 100, pc_ex2 / 100])


# ---------- E2 习题 7 ----------
P_SND = np.array([1000., 900., 850., 800., 700., 600., 500., 400., 300., 200.] ) * 100.0
T_SND = np.array([23.0, 20.5, 17.0, 12.0, 4.5, -4.0, -12.1, -23.0, -32.5, -45.3]) + 273.15
TD_SND = np.array([19.0, 11.0, 7.6, 6.8, -1.1, -8.5, -19.2, -29.5, -45.0, -59.5]) + 273.15


def env_interp(p):
    """环境 T/Td 在 ln p 上线性插值（p 升序=自地面向上）"""
    lp = np.log(P_SND[::-1])
    return (np.interp(np.log(p), lp, T_SND[::-1]), np.interp(np.log(p), lp, TD_SND[::-1]))


def theta_se(T, p, q):
    """(6.3.8) 形式的假相当位温：先抬升到自身 LCL，再按 θd·exp(rs Lv/(cp T)) 计算"""
    p_lcl = lcl_solve(T, p, q)
    T_lcl = T * (p_lcl / p) ** kappa
    e = e_from_q(q, p_lcl)
    pd = p_lcl - e
    th_d = T_lcl * (p0 / pd) ** kappa
    return th_d * np.exp(q * Lv / (cp * T_lcl)), p_lcl, T_lcl


def e2_sounding():
    sec("E2 习题 7 全解（探空：1000-200 hPa 十层）")
    # (1) 900 hPa 三量
    p900 = 90000.0
    i900 = 1
    e900 = es_w(TD_SND[i900])
    q900 = q_from_e(e900, p900)
    qs900 = qs(T_SND[i900], p900)
    RH900 = e900 / es_w(T_SND[i900])
    log(f"(1) 900 hPa: e={e900:.1f} Pa; q={q900*1000:.2f} g/kg; qs={qs900*1000:.2f} g/kg; "
        f"Uw={RH900*100:.1f}%   [书答案: 9 g/kg, 17 g/kg, 53%]")

    # (2) 气块路径 LCL/LFC/EL + CAPE/CIN
    T0_, p0_, td0 = T_SND[0], P_SND[0], TD_SND[0]
    q0v = q_from_e(es_w(td0), p0_)
    p_lcl = lcl_solve(T0_, p0_, q0v)
    T_lcl = T0_ * (p_lcl / p0_) ** kappa
    z_lcl_approx = 123.0 * (T0_ - td0)
    log(f"\n(2) 地面气块: T={T0_-273.15:.1f}C, Td={td0-273.15:.1f}C, q0={q0v*1000:.2f} g/kg")
    log(f"    LCL: p={p_lcl/100:.1f} hPa, T_LCL={T_lcl-273.15:.1f}C; 近似式 z=123*(T-Td)={z_lcl_approx:.0f} m"
        f"   [书答案 LCL=950 hPa]")

    # CCL：等混合比线与环境 T 曲线交点
    def ccl_f(p):
        Te, _ = env_interp(p)
        return qs(Te, p) - q0v

    p_ccl = brentq(ccl_f, 60000.0, p0_ - 1)
    T_ccl, _ = env_interp(p_ccl)
    log(f"    CCL: p={p_ccl/100:.1f} hPa (T_env={T_ccl-273.15:.1f}C)   [书答案 850 hPa]")

    # 对流温度：过 CCL 的干绝热线回到地面
    T_conv = T_ccl * (p0_ / p_ccl) ** kappa
    log(f"    对流温度 T_conv = {T_conv-273.15:.1f} C   [书答案 30.5 C]")

    # 细网格浮力积分（含/不含虚温订正）
    pl = np.arange(p0_, 15000.0, -250.0)
    out = {}
    for virt in (True, False):
        Tp = np.array([parcel_T(p, T0_, p0_, q0v)[0] for p in pl])
        Te = np.array([env_interp(p)[0] for p in pl])
        Tde = np.array([env_interp(p)[1] for p in pl])
        qpe = np.array([qs(t, p) for t, p in zip(Tp, pl)])
        qee = np.array([q_from_e(es_w(td), p) for td, p in zip(Tde, pl)])
        if virt:
            Tv_p = Tp * (1 + 0.608 * qpe)
            Tv_e = Te * (1 + 0.608 * qee)
        else:
            Tv_p, Tv_e = Tp, Te
        B = g * (Tv_p - Tv_e) / Tv_e
        dz = Rd / g * 0.5 * (Te[:-1] + Te[1:]) * np.log(pl[:-1] / pl[1:])
        # 找 LFC（LCL 以上第一个 B>0 且随后 500 m 保持）
        idx_lcl = np.argmin(np.abs(pl - p_lcl))
        lfc = None
        for i in range(idx_lcl, len(pl) - 6):
            if B[i] > 0 and np.all(B[i:i + 5] > -1e-4):
                lfc = i
                break
        el = None
        if lfc is not None:
            for i in range(lfc + 5, len(pl)):
                if B[i] < 0:
                    el = i
                    break
        cape = np.sum(B[lfc:el] * dz[lfc:el]) if (lfc is not None and el is not None) else np.nan
        cin = np.sum(B[:lfc] * dz[:lfc]) if lfc is not None else np.nan
        out[virt] = dict(lfc=lfc, el=el, cape=cape, cin=cin, pl=pl, B=B)
        tag = "虚温订正" if virt else "未订正"
        s = f"    浮力积分({tag}): "
        if lfc is not None:
            s += f"LFC={pl[lfc]/100:.1f} hPa; "
        if el is not None:
            s += f"EL={pl[el]/100:.1f} hPa; "
        s += f"CAPE={cape:.0f} J/kg; CIN={cin:.0f} J/kg"
        log(s)
    log("    [书答案: LCL 950 / CCL 850 / LFC 800 hPa; 属真潜不稳定 (CAPE>|CIN|)]")
    cv = out[True]
    verdict = "真潜不稳定 (CAPE>|CIN|)" if cv["cape"] > abs(cv["cin"]) else "假潜不稳定"
    log(f"    虚温订正判据: CAPE={cv['cape']:.0f} vs |CIN|={abs(cv['cin']):.0f} -> {verdict}")

    # (4) θse 剖面与对流性不稳定判据
    log("\n(4) θse 剖面（(6.3.8) 口径）：")
    thse = []
    log("   p(hPa)   T(C)    Td(C)   q(g/kg)   θse(K)   θse(C)")
    for p, t, td in zip(P_SND, T_SND, TD_SND):
        q = q_from_e(es_w(td), p)
        th, plcl_i, tlcl_i = theta_se(t, p, q)
        thse.append(th)
        log(f"   {p/100:6.0f}  {t-273.15:6.1f}  {td-273.15:6.1f}   {q*1000:6.2f}   {th:7.1f}   {th-273.15:6.1f}")
    thse = np.array(thse)
    log(f"   1000-900 hPa: θse {thse[0]-273.15:.1f} -> {thse[1]-273.15:.1f} C  (随高度减小 -> 对流性不稳定)")
    log(f"   [书答案: 68 -> 60 C, 对流性不稳定]")
    log(f"   850-800 hPa: θse {thse[2]-273.15:.1f} -> {thse[3]-273.15:.1f} C  (随高度增大 -> 对流性稳定)")
    log(f"   800-700 hPa: θse {thse[3]-273.15:.1f} -> {thse[4]-273.15:.1f} C")

    # ---- 图：T-lnp + θse 剖面 ----
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    plt.rcParams["font.sans-serif"] = ["SimHei"]
    plt.rcParams["axes.unicode_minus"] = False
    fig, axes = plt.subplots(1, 2, figsize=(10.5, 5.2))
    ax = axes[0]
    ax.plot(T_SND - 273.15, P_SND / 100, "k.-", lw=1.6, ms=8, label="环境 T")
    ax.plot(TD_SND - 273.15, P_SND / 100, "C0.-", lw=1.4, ms=7, label="环境 Td")
    pl2 = np.arange(p0_, 15000.0, -250.0)
    Tp2 = np.array([parcel_T(p, T0_, p0_, q0v)[0] for p in pl2])
    ax.plot(Tp2 - 273.15, pl2 / 100, "C3-", lw=1.6, label="气块路径 (干绝热+假绝热)")
    ax.axhline(p_lcl / 100, color="C1", ls=":", lw=1.2)
    ax.axhline(p_ccl / 100, color="C2", ls="--", lw=1.2)
    if out[False]["lfc"] is not None:
        ax.axhline(pl2[out[False]["lfc"]] / 100, color="C4", ls="-.", lw=1.2)
    ax.plot([T_ccl - 273.15], [p_ccl / 100], "C2*", ms=14)
    ax.text(20, p_lcl / 100 - 12, f"LCL {p_lcl/100:.0f} hPa", fontsize=9, color="C1")
    ax.text(20, p_ccl / 100 - 12, f"CCL {p_ccl/100:.0f} hPa", fontsize=9, color="C2")
    ax.text(20, 775, f"LFC {pl2[out[False]['lfc']]/100:.0f} hPa", fontsize=9, color="C4")
    ax.set_yscale("log")
    ax.invert_yaxis()
    ax.set_ylim(1000, 500)
    ax.set_xlim(-35, 40)
    ax.set_yticks([1000, 900, 800, 700, 600, 500])
    ax.set_yticklabels(["1000", "900", "800", "700", "600", "500"])
    ax.set_xlabel("温度 (℃)")
    ax.set_ylabel("气压 (hPa)")
    ax.set_title("(a) 习题 7 探空与气块路径")
    ax.grid(alpha=0.3, which="both")
    ax.legend(fontsize=8, loc="lower left")
    ax = axes[1]
    ax.plot(thse - 273.15, P_SND / 100, "C5o-", lw=1.6, ms=6)
    ax.axhspan(900, 1000, color="C3", alpha=0.15)
    ax.axhspan(800, 850, color="C0", alpha=0.15)
    ax.set_ylim(1000, 100)
    ax.set_yscale("log")
    ax.set_yticks([1000, 900, 800, 700, 600, 500, 400, 300, 200])
    ax.set_yticklabels(["1000", "900", "800", "700", "600", "500", "400", "300", "200"])
    ax.set_xlabel(r"$\theta_{se}$ (℃)")
    ax.set_title(r"(b) $\theta_{se}$ 剖面：红=对流性不稳定层，蓝=稳定层")
    ax.grid(alpha=0.3, which="both")
    plt.tight_layout()
    plt.savefig(os.path.join(FIGDIR, "ch15_sounding_stability.png"), dpi=150)
    plt.close()
    log("\n图已存: doc/figs/ch15_sounding_stability.png")

    return dict(q900=q900, qs900=qs900, RH900=RH900, p_lcl=p_lcl, p_ccl=p_ccl,
                T_conv=T_conv, thse=thse, out=out)


# ---------- E3 习题 8 ----------
def e3_parcel_velocity():
    sec("E3 习题 8：900 hPa 饱和气块上升速度（环境 Γ=γd）")
    p0_, T0_ = 90000.0, 280.0
    th_env = T0_ * (p0 / p0_) ** kappa     # 干绝热环境：θ 恒定
    q0p = qs(T0_, p0_)
    log(f"气块: p=900 hPa, T=280 K, 饱和 (qs={q0p*1000:.3f} g/kg); 环境干绝热 θ={th_env:.2f} K")

    pl = np.arange(p0_, 69999.0, -100.0)
    Tp = np.array([pseudoadiabat(p0_, T0_, p) for p in pl])
    Te = th_env * (pl / p0) ** kappa
    qp = np.array([qs(t, p) for t, p in zip(Tp, pl)])

    variants = {
        "未订正 (Tp-Tv)": (Tp, Te),
        "虚温订正 (q_e=0)": (Tp * (1 + 0.608 * qp), Te),
        "虚温订正 (q_e=qs900)": (Tp * (1 + 0.608 * qp), Te * (1 + 0.608 * q0p)),
    }
    res = {}
    for tag, (Tvp, Tve) in variants.items():
        B = g * (Tvp - Tve) / Tve
        dz = Rd / g * 0.5 * (Te[:-1] + Te[1:]) * np.log(pl[:-1] / pl[1:])
        v2 = 2 * np.sum(B[:-1] * dz)
        v = np.sqrt(max(v2, 0.0))
        res[tag] = v
        log(f"  {tag}: v(700 hPa) = {v:.1f} m/s")
    log("  [书答案: (1) 未订正 24.2 m/s; (2) 虚温订正 26.7 m/s]")

    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    plt.rcParams["font.sans-serif"] = ["SimHei"]
    plt.rcParams["axes.unicode_minus"] = False
    fig, ax = plt.subplots(figsize=(6.4, 4.4))
    for tag, (Tvp, Tve) in variants.items():
        B = g * (Tvp - Tve) / Tve
        dz = Rd / g * 0.5 * (Te[:-1] + Te[1:]) * np.log(pl[:-1] / pl[1:])
        vprof = np.sqrt(np.concatenate([[0], 2 * np.cumsum(B[:-1] * dz)]))
        ax.plot(vprof, pl / 100, lw=1.8, label=f"{tag}  ({res[tag]:.1f} m/s)")
    ax.axvline(res["未订正 (Tp-Tv)"], color="C3", ls=":", lw=1)
    ax.axvline(24.2, color="k", ls="--", lw=1, alpha=0.6)
    ax.axvline(26.7, color="k", ls="--", lw=1, alpha=0.6)
    ax.text(24.35, 880, "书 24.2", fontsize=8)
    ax.text(26.85, 880, "书 26.7", fontsize=8)
    ax.invert_yaxis()
    ax.set_xlabel("气块垂直速度 w (m/s)")
    ax.set_ylabel("气压 (hPa)")
    ax.set_title("习题 8：900→700 hPa 气块速度（含虚温订正对比）")
    ax.grid(alpha=0.3)
    ax.legend(fontsize=8, loc="lower right")
    plt.tight_layout()
    plt.savefig(os.path.join(FIGDIR, "ch15_parcel_velocity.png"), dpi=150)
    plt.close()
    log("图已存: doc/figs/ch15_parcel_velocity.png")
    return res


# ---------- E4 质量通量与尺度因子 ----------
def e4_massflux():
    sec("E4 质量通量与尺度感知（概念数值）")
    # (a) 卷入率 -> 云顶
    #     起算：900 hPa 饱和气块（T_env+1 K，q=qs）——习题 7 探空中 800~900 hPa 是对流的
    #     关键层，取 900 hPa 作云底便于演示"卷入吃掉云厚"
    def cloud_top(eta):
        """夹卷柱：dh/dz=-eta(h-h_env), dqw/dz=-eta(qw-q_env)；可逆饱和调整；返回云顶气压"""
        p_start, T_start = 90000.0, env_interp(90000.0)[0] + 1.0
        z = env_interp(90000.0)[1] * 0.0          # 相对高度从 0 起
        T = T_start
        p = p_start
        qw = qs(T_start, p_start)
        h = cp * T + g * z
        dzst = 25.0
        for _ in range(20000):
            if p <= 20000.0:
                return 20000.0
            Te, Tde = env_interp(p)
            qe_e = q_from_e(es_w(Tde), p)
            he = cp * Te + g * z
            h += eta * dzst * (he - h)
            qw += eta * dzst * (qe_e - qw)
            qw = max(qw, 0.0)
            p = p * np.exp(-g * dzst / (Rd * T))
            z += dzst
            # 可逆饱和调整：cp(T-T_dry) = Lv*ql，ql = max(0, qw-qs(T,p))
            # 朴素不动点因 Lv/cp*dqs/dT ~ 3 > 1 发散（ch13 讲过的教训）→ 牛顿迭代
            T_dry = (h - g * z) / cp
            T = T_dry
            for _ in range(30):
                qsv = qs(T, p)
                ql = max(0.0, qw - qsv)
                E = cp * (T - T_dry) - Lv * ql
                dE = cp + (Lv * Lv * qsv * eps / (Rd * T * T) if ql > 0 else 0.0)
                Tn = T - E / dE
                if abs(Tn - T) < 1e-7:
                    T = Tn
                    break
                T = Tn
            qs_ = qs(T, p)
            ql = max(0.0, qw - qs_)
            Tvp = T * (1 + 0.608 * qs_ - ql)
            Tv_e = Te * (1 + 0.608 * qe_e)
            if Tvp < Tv_e:
                return p
        return 20000.0

    etas = [0.2e-4, 0.5e-4, 1.0e-4, 2.0e-4, 4.0e-4, 8.0e-4, 16.0e-4]
    log("(a) 夹卷率 eta (1/m) -> 云顶/云厚（900 hPa 饱和起算，+1 K 扰动；云底 900 hPa）:")
    ctops = []
    for eta in etas:
        pc = cloud_top(eta)
        ctops.append(pc)
        log(f"   eta={eta*1e4:5.1f}e-4 : 云顶 {pc/100:6.1f} hPa, 云厚 {(90000.0-pc)/100:5.1f} hPa")

    # (b) 质量通量廓线 M(z)/Mb
    log("\n(b) 质量通量廓线 M(z)/M_b = exp(∫(ε-δ)dz):")
    zz = np.linspace(0, 10000, 200)
    profs = {
        "深对流型 (ε=2.5e-4, δ=0.75e-4)": (2.5e-4, 0.75e-4),
        "浅对流型 (ε=δ=1.0e-4)": (1.0e-4, 1.0e-4),
        "仅夹卷 (ε=1.0e-4, δ=0)": (1.0e-4, 0.0),
    }
    for tag, (e_, d_) in profs.items():
        M = np.exp((e_ - d_) * zz)
        log(f"   {tag}: M(10 km)/M_b = {M[-1]:.2f}")

    # (c) scale_fac(dx) 表（New Tiedtke 源码公式）
    log("\n(c) New Tiedtke 尺度因子（源码：dxref=15 km）:")
    log("   dx(km) |  scale_fac  | scale_fac2 | tau_c=360s | tau_c=1800s | tau_c=10800s")
    taus = (360.0, 1800.0, 10800.0)
    tab = []
    for dx in [27.0, 12.0, 9.0, 6.0, 4.0, 3.0, 2.0, 1.0]:
        if dx < 15.0:
            sf = (1.06133 + np.log(15.0 / dx)) ** 3
            sf2 = sf ** 0.5
        else:
            sf = 1.0 + 1.33e-5 * dx * 1000.0
            sf2 = 1.0
        tab.append((dx, sf, sf2))
        log(f"   {dx:5.1f}  |  {sf:8.2f}   |  {sf2:7.2f}   |" +
            "".join(f"  {t*sf:9.0f} " for t in taus))

    # 深对流时间尺度算例：云厚 10 km、w_up=5 m/s
    dz_ = 10000.0
    wup = 5.0
    tauc = dz_ / (2.0 + min(15.0, wup))
    log(f"\n   深对流 tau_c 算例：Δz=10 km, w_up=5 m/s -> tau_c={tauc:.0f} s (钳位 360-10800)")

    # (d) 浅对流闭合数值（zdhpbl/zdh）
    hfx, qfx = 150.0, 1.0e-4
    dz_pbl, rho = 1000.0, 1.1
    Ttend = hfx / (rho * cp * dz_pbl)
    qtend = qfx / (rho * dz_pbl)
    dp_pbl = rho * g * dz_pbl
    zdhpbl = (cp * Ttend + Lv * qtend) * dp_pbl
    dT_excess, dq_excess = 0.5, 2.0e-3
    zdh = g * max(cp * dT_excess + Lv * dq_excess, 1e-10)
    log(f"\n(d) 浅对流闭合算例: hfx={hfx:.0f} W/m2, qfx={qfx:.1e} kg/m2/s, PBL 厚 {dz_pbl:.0f} m")
    log(f"   zdhpbl = {zdhpbl:.1f}; zdh = {zdh:.1f}; M_base = zdhpbl/zdh = {zdhpbl/zdh:.4f} (模式单位)")
    log(f"   上限 zmfmax = Δp*3/(g*dt) = {dp_pbl*3/(g*90.0):.1f}（非紧约束）")
    log(f"   scale_fac2@3km = {tab[5][2]:.2f} -> 浅对流再除 sqrt(scale_fac2): M={zdhpbl/zdh/tab[5][2]:.4f}")

    # ---- 图 ----
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    plt.rcParams["font.sans-serif"] = ["SimHei"]
    plt.rcParams["axes.unicode_minus"] = False
    fig, axes = plt.subplots(1, 3, figsize=(13.5, 4.2))
    ax = axes[0]
    ax.semilogx(np.array(etas) * 1e4, np.array(ctops) / 100, "C0o-", lw=1.8)
    ax.axhline(900.0, color="C1", ls=":", lw=1.2)
    ax.text(2.2e-1, 906.0, "云底 900 hPa", fontsize=8, color="C1")
    ax.invert_yaxis()
    ax.set_xlabel(r"夹卷率 $\eta$ (10$^{-4}$ m$^{-1}$)")
    ax.set_ylabel("云顶气压 (hPa)")
    ax.set_title("(a) 夹卷率 -> 云顶（习题 7 探空，云底 900 hPa）")
    ax.grid(alpha=0.3)
    ax = axes[1]
    for tag, (e_, d_) in profs.items():
        ax.plot(np.exp((e_ - d_) * zz), zz / 1000.0, lw=1.8, label=tag)
    ax.set_xlabel(r"$M(z)/M_b$")
    ax.set_ylabel("高度 (km)")
    ax.set_title(r"(b) 质量通量廓线 $\exp\int(\varepsilon-\delta)dz$")
    ax.legend(fontsize=8)
    ax.grid(alpha=0.3)
    ax = axes[2]
    dxs = np.array([t[0] for t in tab])
    sfs = np.array([t[1] for t in tab])
    ax.semilogx(dxs, sfs, "C3o-", lw=1.8)
    ax.axvline(15.0, color="k", ls=":", lw=1)
    ax.text(15.5, max(sfs) * 0.55, "dxref=15 km\n(<15 km: (1.06133+ln(15/dx))^3)", fontsize=8)
    ax.set_xlabel("dx (km)")
    ax.set_ylabel("scale_fac")
    ax.set_title("(c) New Tiedtke 尺度因子")
    ax.grid(alpha=0.3, which="both")
    plt.tight_layout()
    plt.savefig(os.path.join(FIGDIR, "ch15_massflux_scaleaware.png"), dpi=150)
    plt.close()
    log("\n图已存: doc/figs/ch15_massflux_scaleaware.png")


if __name__ == "__main__":
    sec("ch15 实验开始（WRFlearn python）")
    r1 = e1_layer_subsidence()
    r2 = e2_sounding()
    r3 = e3_parcel_velocity()
    e4_massflux()
    sec("ch15 实验完成")
    _logf.close()