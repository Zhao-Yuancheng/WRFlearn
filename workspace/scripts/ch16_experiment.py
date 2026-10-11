# -*- coding: utf-8 -*-
"""
ch16 陆面过程族 —— 轻轨实验（E1–E3）
环境: D:\\Code\\miniforge3\\envs\\WRFlearn\\python.exe
输出: 日志 workspace/logs/ch16_experiment.log；图 doc/figs/ch16_*.png

E1 地表能量平衡日循环（陆面单柱，全显式土层 + 精确表皮温度解）：
   - 理想化太阳角日循环 + 湿土/干土两个算例（β 蒸发效率法）
   - Rn = H + LE + G 瞬时闭合核验（brentq 精确解）
   - 柱能量收支核验（显式步 telescoping）
   - Noah 手册线性化解（PENMAN + YY/ZZ1）与精确解对照 → 线性化误差实测
E2 土壤-海洋热传导阻尼深度：
   - 一维热扩散数值解（隐式三对角）验证解析 D=sqrt(2k/omega)、相位滞后 z/D
   - 土壤（loam 实测 lambda/HCPCT）vs 纯水分子热扩散 vs 海洋有效扩散
   - 对照书 4.3：土壤 0.1 m / 2-3 m；海洋 15-20 m / 200-300 m
E3 SOILPARM.TBL 敏感性：
   - 读实际 TBL（STAS 节），核验四条派生式（F11/SATDW/REFSMC/WLTSMC）
   - 沙/壤/黏土 的持水、beta(theta)、lambda(theta)、kappa、阻尼深度、KDT 入渗
"""
import os
import numpy as np
from scipy.optimize import brentq

# ---------- 常量（与 Noah 源码同源） ----------
Rd, Rv = 287.04, 461.5
eps_mw = Rd / Rv                      # 0.622
cp, g = 1004.6, 9.81
Lv, Lf = 2.501e6, 3.335e5
sigma = 5.67e-8
CSOIL = 2.0e6      # 干土基质体积热容 J/m3/K (GENPARM CSOIL_DATA)
CH2O, CICE, CAIR = 4.2e6, 2.106e6, 1004.0    # HRT 内参数（体积热容）
A2B, A4B = 17.67, 29.65                      # Bolton 1980：driver 侧饱和式常数
A23M4 = A2B * (273.15 - A4B)                 # 4302.65

PSURF = 100000.0   # 试验定常气压（海平面口径）
CH = 0.008         # 交换系数（定常，简化；微风口径）
EMISS = 0.97
ALBEDO = 0.20
DZS = np.array([0.1, 0.3, 0.6, 1.0])         # Noah 四层厚度 (module_soil_pre init_soil_depth_2)
ZS = np.array([0.05, 0.25, 0.70, 1.50])      # 层中深度
ZBOT = 8.0                                   # 深层边界 ZBOT_DATA
TBOT = 288.0                                 # 深层温度（语义：局地年均地表气温）

WRF_RUN = r"d:\Code\Learn\WRF\source\WRFv4.8.0\WRFV4.8.0\run"
LOGDIR = r"d:\Code\Learn\WRF\workspace\logs"
FIGDIR = r"d:\Code\Learn\WRF\doc\figs"
os.makedirs(LOGDIR, exist_ok=True)
os.makedirs(FIGDIR, exist_ok=True)
_logf = open(os.path.join(LOGDIR, "ch16_experiment.log"), "w", encoding="utf-8")


def log(*a):
    s = " ".join(str(x) for x in a)
    print(s)
    _logf.write(s + "\n")
    _logf.flush()


def sec(title):
    log("\n" + "=" * 78)
    log(title)
    log("=" * 78)


# ---------- 饱和函数（module_sf_noahdrv.F：Bolton 1980 形式） ----------
def es_bolton(T):
    return 611.2 * np.exp(A2B * (T - 273.15) / (T - A4B))


def qsat(T, p=PSURF):
    e = es_bolton(T)
    return eps_mw * e / (p - (1.0 - eps_mw) * e)


def dqsatdT(T, p=PSURF):
    """DQSDT2 = Q2SAT*A23M4/(T-A4)^2（module_sf_noahdrv.F 实测公式）"""
    return qsat(T, p) * A23M4 / (T - A4B) ** 2


# ---------- TDFCND（module_sf_noahlsm.F：Peters-Lidard 1998 / Johansen 1975） ----------
def tdfcnd(smc, smcmax, sh2o, qz, soilt=6, opt=1, psisat=0.355, bexp=5.25):
    """返回土壤热传导率 lambda [W/m/K]"""
    if opt == 1 or (opt == 2 and soilt not in (3, 4)):
        thkice, thkw, thko, thkqz = 2.2, 0.57, 2.0, 7.7
        satratio = smc / smcmax
        thks = thkqz ** qz * thko ** (1.0 - qz)
        xunfroz = sh2o / smc
        xu = xunfroz * smcmax
        thksat = thks ** (1.0 - smcmax) * thkice ** (smcmax - xu) * thkw ** xu
        gammd = (1.0 - smcmax) * 2700.0
        thkdry = (0.135 * gammd + 64.7) / (2700.0 - 0.947 * gammd)
        akei = satratio
        akel = np.log10(satratio) + 1.0 if satratio > 0.1 else 0.0
        ake = ((smc - sh2o) * akei + sh2o * akel) / smc
        return ake * (thksat - thkdry) + thkdry
    else:  # McCumber & Pielke（silt loam / sandy loam）
        psif = psisat * 100.0 * (smcmax / smc) ** bexp
        pf = np.log10(abs(psif))
        return 420.0 * np.exp(-(pf + 2.7)) if pf <= 5.1 else 0.1744


def hcpct(smc, smcmax, sh2o):
    """HRT 顶层热容公式（体积热容 J/m3/K）"""
    return sh2o * CH2O + (1.0 - smcmax) * CSOIL + (smcmax - smc) * CAIR \
        + (smc - sh2o) * CICE


# ---------- SOILPARM.TBL 解析（STAS 节 = Noah 用） ----------
FIELDS = ["BB", "DRYSMC", "F11", "MAXSMC", "REFSMC", "SATPSI",
          "SATDK", "SATDW", "WLTSMC", "QTZ"]


def parse_soilparm(path):
    with open(path, "r", encoding="utf-8", errors="ignore") as f:
        lines = f.readlines()
    soil = {}
    i = 0
    while i < len(lines):
        if lines[i].strip() == "STAS":
            i += 2  # 跳过节名与表头
            while i < len(lines):
                tok = [t.strip() for t in lines[i].split(",")]
                if len(tok) < 11:
                    break
                try:
                    rec = {"name": tok[18].strip().strip("'") if len(tok) > 18 else "?"}
                    for k, key in enumerate(FIELDS):
                        rec[key] = float(tok[k + 1])
                    soil[int(tok[0])] = rec
                except (ValueError, IndexError):
                    break
                i += 1
            break
        i += 1
    return soil


# ==================================================================
# E1：地表能量平衡日循环（陆面单柱）
# ==================================================================
def forcing(t_sec):
    """理想化日循环强迫：返回 SOLDN, LWDN, T2, q2"""
    h = (t_sec / 3600.0) % 24.0
    soldn = 880.0 * np.sin(np.pi * (h - 6.0) / 12.0) if 6.0 < h < 18.0 else 0.0
    lwdn = 285.0
    T2 = 291.0 + 5.0 * np.cos(2.0 * np.pi * (h - 15.0) / 24.0)
    rh2 = 0.50
    q2 = rh2 * qsat(T2)
    return soldn, lwdn, T2, q2


def run_e1(soil, theta_init, tag, beta_floor=0.02, nspin_days=3):
    """陆面单柱积分（spin-up + 记录 1 天）。返回记录段时序"""
    smcmax, wltsmc, refsmc = soil["MAXSMC"], soil["WLTSMC"], soil["REFSMC"]
    qz = soil["QTZ"]

    dt = 300.0
    nspin, nday = int(nspin_days * 86400 / dt), int(86400 / dt)
    stc = np.array([292.0, 290.5, 289.5, 288.5])
    th1 = theta_init
    beta = float(np.clip((th1 - wltsmc) / (refsmc - wltsmc), beta_floor, 1.0))

    keys = ["t", "soldn", "T2", "T1", "stc1", "stc2", "stc3", "stc4",
            "Rn", "H", "LE", "G", "beta", "resid", "T1_noah", "T1_noahex",
            "R_lin", "theta1", "Fbot", "Ecol"]
    rec = {k: [] for k in keys}
    ssoil_prev = 0.0

    def step(t, stc, th1):
        soldn, lwdn, T2, q2 = forcing(t)
        rho = PSURF / (Rd * T2 * (1.0 + 0.61 * q2))
        lam1 = tdfcnd(th1, smcmax, th1, qz)
        beta = float(np.clip((th1 - wltsmc) / (refsmc - wltsmc), beta_floor, 1.0))
        fdown = soldn * (1.0 - ALBEDO) + lwdn

        def bal(T1):
            H = rho * cp * CH * (T1 - T2)
            LE = Lv * beta * rho * CH * (qsat(T1) - q2)
            G = lam1 * (T1 - stc[0]) / (0.5 * DZS[0])
            Rn = fdown - EMISS * sigma * T1 ** 4
            return Rn - H - LE - G

        T1 = brentq(bal, T2 - 40.0, T2 + 90.0, xtol=1e-12, rtol=1e-15, maxiter=200)
        H = rho * cp * CH * (T1 - T2)
        LE = Lv * beta * rho * CH * (qsat(T1) - q2)
        G = lam1 * (T1 - stc[0]) / (0.5 * DZS[0])
        Rn = fdown - EMISS * sigma * T1 ** 4
        resid = Rn - H - LE - G
        # 简化口径：本章实验不做土壤水分预报（SMFLX 的职责，见 16.5.3），
        # 土壤湿度冻结为初值，β 由 θ 经 β=(θ-θw)/(θref-θw) 给定，不随时间变
        th1_new = th1

        # ------ Noah 手册线性化解（PENMAN + YY/ZZ1；TH2≡T2 口径） ------
        RR = 1.0 + EMISS * T2 ** 4 * 6.48e-8 / (PSURF * CH)
        DELTA = (Lv / cp) * dqsatdT(T2)
        A = (Lv / cp) * (qsat(T2) - q2)
        RCH = rho * cp * CH
        FNET = fdown - EMISS * sigma * T2 ** 4 - ssoil_prev
        RAD = FNET / RCH
        EPSCA = (A * RR + RAD * DELTA) / (DELTA + RR)
        YYNUM = fdown - EMISS * sigma * T2 ** 4
        YY = T2 + (YYNUM / RCH - beta * EPSCA) / RR
        ZZ1 = lam1 / (0.5 * DZS[0] * RCH * RR) + 1.0
        T1_lin = (YY + (ZZ1 - 1.0) * stc[0]) / ZZ1

        def bal_noah(T1x):
            """Noah 自身通量公式口径的收支（LE = BETA*EPSCA*RCH 不依赖 T1）"""
            Hx = RCH * (T1x - T2)
            LEx = beta * EPSCA * RCH
            Gx = lam1 * (T1x - stc[0]) / (0.5 * DZS[0])
            Rnx = fdown - EMISS * sigma * T1x ** 4
            return Rnx - Hx - LEx - Gx

        T1_noahex = brentq(bal_noah, T2 - 40.0, T2 + 90.0, xtol=1e-12, rtol=1e-15)
        R_lin = bal_noah(T1_lin)     # 纯线性化残差（同公式口径）

        def resid_full(T1x):
            Hx = rho * cp * CH * (T1x - T2)
            LEx = Lv * beta * rho * CH * (qsat(T1x) - q2)
            Gx = lam1 * (T1x - stc[0]) / (0.5 * DZS[0])
            Rnx = fdown - EMISS * sigma * T1x ** 4
            return Rnx - Hx - LEx - Gx

        return dict(T1=T1, H=H, LE=LE, G=G, Rn=Rn, resid=resid, beta=beta,
                    T1_noah=T1_lin, T1_noahex=T1_noahex, R_lin=R_lin,
                    soldn=soldn, T2=T2, th1_new=th1_new, lam1=lam1,
                    cap=hcpct(th1, smcmax, th1), bal_noah=bal_noah)

    dbg = []

    def advance_soil(stc, G_top, th1, dt):
        """全显式四层：顶通量 = SSOIL；底通量 = TBOT@ZBOT。柱收支 telescoping 精确"""
        lam = np.full(4, tdfcnd(th1, smcmax, th1, qz))
        cap = np.full(4, hcpct(th1, smcmax, th1))
        F = np.zeros(5)
        F[0] = G_top
        dzif = 0.5 * (DZS[:-1] + DZS[1:])
        for k in range(3):
            lam_i = 0.5 * (lam[k] + lam[k + 1])
            F[k + 1] = lam_i * (stc[k] - stc[k + 1]) / dzif[k]
        dz_bot = ZBOT - ZS[3]
        F[4] = lam[3] * (stc[3] - TBOT) / dz_bot
        dstc = (F[:-1] - F[1:]) / (cap * DZS) * dt
        return stc + dstc, F[4], cap

    for n in range(nspin + nday):
        t = n * dt
        out = step(t, stc, th1)
        stc, Fbot, cap = advance_soil(stc, out["G"], th1, dt)
        th1 = out["th1_new"]
        ssoil_prev = out["G"]
        if n >= nspin:
            rec["t"].append(((n - nspin) * dt) / 3600.0)
            for key in ["soldn", "T2", "T1", "Rn", "H", "LE", "G", "beta",
                        "resid", "T1_noah", "T1_noahex", "R_lin", "theta1"]:
                rec[key].append(out[key] if key != "theta1" else th1)
            rec["Fbot"].append(Fbot)
            eco = float(np.sum(cap * DZS * stc))
            rec["Ecol"].append(eco)
            if n in (nspin, nspin + nday // 2, nspin + nday - 1):
                dbg.append((n, ((n - nspin) * dt) / 3600.0, stc.copy(), eco, Fbot, th1))
            for kk in range(4):
                rec["stc%d" % (kk + 1)].append(stc[kk])
    out = {k: np.array(v) for k, v in rec.items()}
    H, LE = out["H"], out["LE"]
    out["EF"] = LE / np.where(np.abs(H + LE) > 30.0, H + LE, np.nan)
    out["tag"] = tag
    out["dbg"] = dbg
    return out


# ==================================================================
# E2：一维热扩散（隐式三对角，表面正弦强迫）
# ==================================================================
def diffusion_run(kappa, period_s, amp, depth, ndz, dt, nper):
    z = np.linspace(0, depth, ndz)
    dz = z[1] - z[0]
    omega = 2.0 * np.pi / period_s
    r = kappa * dt / dz ** 2
    nstep = int(round(nper * period_s / dt))
    nsamp = int(round(period_s / dt))          # 恰好一个周期的采样
    n = ndz - 2
    A = np.zeros((n, n))
    for i in range(n):
        A[i, i] = 1.0 + 2.0 * r
        if i > 0:
            A[i, i - 1] = -r
        if i < n - 1:
            A[i, i + 1] = -r
    A[n - 1, n - 1] = 1.0 + r                  # 底部 zero-flux
    # 初值：解析稳态解（消除瞬态；否则深节点需数年才平衡）
    D_ana = np.sqrt(2.0 * kappa / omega)
    T = -amp * np.exp(-z / D_ana) * np.sin(z / D_ana)
    sample = np.zeros((nsamp, ndz))
    for it in range(nstep):
        t = (it + 1) * dt
        Ts = amp * np.sin(omega * t)
        rhs = T[1:-1].copy()
        rhs[0] += r * Ts
        T[1:-1] = np.linalg.solve(A, rhs)
        T[0] = Ts
        T[-1] = T[-2]
        if it >= nstep - nsamp:
            sample[it - (nstep - nsamp)] = T.copy()
    tt = np.arange(nstep - nsamp, nstep) * dt
    wt = omega * tt
    S = (2.0 / nsamp) * (sample * np.sin(wt)[:, None]).sum(axis=0)
    C = (2.0 / nsamp) * (sample * np.cos(wt)[:, None]).sum(axis=0)
    Amp = np.sqrt(S ** 2 + C ** 2)
    Pha = -np.arctan2(C, S)                    # 滞后量：T=A*sin(wt-z/D) -> phi=+z/D（rad）
    return z, Amp, Pha, sample, tt


def fit_D(z, Amp, A0):
    m = (Amp > 0.03 * A0) & (Amp < 0.80 * A0)
    p = np.polyfit(z[m], np.log(Amp[m]), 1)
    return -1.0 / p[0]


# ==================================================================
if __name__ == "__main__":
    soil_all = parse_soilparm(os.path.join(WRF_RUN, "SOILPARM.TBL"))
    loam = soil_all[6]

    # ---------------- E1 ----------------
    sec("E1 地表能量平衡日循环（单柱；湿土 θ=0.30 / 干土 θ=0.15，loam STAS-6）")
    log("参数：p=100000 Pa, CH=%.4f, emiss=%.2f, albedo=%.2f, LWDN=285 W/m2, 4 层土层显式步" %
        (CH, EMISS, ALBEDO))
    log("LOAM: BB=%.2f MAXSMC=%.3f REFSMC=%.3f WLTSMC=%.3f QTZ=%.2f" % (
        loam["BB"], loam["MAXSMC"], loam["REFSMC"], loam["WLTSMC"], loam["QTZ"]))
    wet = run_e1(loam, 0.30, "湿土 θ=0.30")
    dry = run_e1(loam, 0.15, "干土 θ=0.15")
    for run in (wet, dry):
        t = run["t"]; day = (t > 6) & (t < 18)
        Rn, H, LE, G = run["Rn"], run["H"], run["LE"], run["G"]
        log("\n[%s]" % run["tag"])
        log("  白天均(6-18h)：Rn=%7.1f  H=%7.1f  LE=%7.1f  G=%7.1f W/m2" %
            (Rn[day].mean(), H[day].mean(), LE[day].mean(), G[day].mean()))
        log("  夜间均(18-6h)：Rn=%7.1f  H=%7.1f  LE=%7.1f  G=%7.1f W/m2" %
            (Rn[~day].mean(), H[~day].mean(), LE[~day].mean(), G[~day].mean()))
        efd = np.trapz(LE[day], t[day]) / np.trapz(H[day] + LE[day], t[day])
        log("  白天蒸发份额 LE/(H+LE)=%.3f（能量加权）" % efd)
        log("  夜间：Rn=%+.1f（辐射亏损）H=%+.1f（向下感热）LE=%+.1f（蒸发仍正）G=%+.1f（土壤放热）" %
            (Rn[~day].mean(), H[~day].mean(), LE[~day].mean(), G[~day].mean()))
        log("  表皮 T1：最高 %.2f K (%.1f℃)，最低 %.2f K (%.1f℃)" %
            (run["T1"].max(), run["T1"].max() - 273.15,
             run["T1"].min(), run["T1"].min() - 273.15))
        log("  夜间逆温最强 T2-T1=%.2f K（辐射逆温，对照书 6.10）" %
            (run["T2"] - run["T1"])[~day].max())
        log("  瞬时闭合残差 max|Rn-H-LE-G| = %.3e W/m2（brentq 精确解）" %
            np.abs(run["resid"]).max())
        dlin = run["T1_noah"] - run["T1_noahex"]
        dform = run["T1_noahex"] - run["T1"]
        log("  Noah 线性化解（同公式口径）：max|T1_lin-T1_noah_exact|=%.4f K；"
            "线性化残差 max|R|=%.3f W/m2" %
            (np.abs(dlin).max(), np.abs(run["R_lin"]).max()))
        log("  公式口径差（Penman-BETA 形式 vs 精确 qsat(T1)）：max|ΔT1|=%.3f K（正午 %+.3f K）" %
            (np.abs(dform).max(), np.interp(12.0, t, dform)))
        log("  柱收支检查（记录日）：")
        for (nn, hh, stc_d, eco, fbot, th1_d) in run["dbg"]:
            log("    %5.2f h  STC=[%.3f %.3f %.3f %.3f]  Ecol=%.1f kJ/m2  Fbot=%+.2f W/m2  θ1=%.4f" %
                (hh, stc_d[0], stc_d[1], stc_d[2], stc_d[3], eco / 1e3, fbot, th1_d))
        iRn = np.trapz(Rn, t) * 3.6; iH = np.trapz(H, t) * 3.6
        iLE = np.trapz(LE, t) * 3.6; iG = np.trapz(G, t) * 3.6
        log("  日累计(MJ/m2)：∫Rn=%.2f ∫H=%.2f ∫LE=%.2f ∫G=%.2f；"
            "失配=%.3e MJ/m2（=%.1e W/m2 均）" %
            (iRn / 1e3, iH / 1e3, iLE / 1e3, iG / 1e3,
             (iRn - iH - iLE - iG) / 1e3, abs(np.trapz(run["resid"], t))))
        dEcol = (run["Ecol"][-1] - run["Ecol"][0]) / 1e3
        # 与 Ecol 区间对齐的矩形和（步 n 的通量驱动 Ecol(n-1)->Ecol(n)）
        net = np.sum(run["G"][1:] - run["Fbot"][1:]) * 300.0 / 1e3
        log("  柱收支一阶差(MJ/m2)：Δ(ΣC·dz·T)=%+.4f   Σ(G-Fbot)·dt=%+.4f   "
            "差=%.2e%%（显式步 telescoping 应至机器精度）" %
            (dEcol / 1e3, net / 1e3, 100 * abs(dEcol - net) / max(abs(net), 1e-9)))

    # ---------------- E2 ----------------
    sec("E2 土壤-海洋热传导阻尼深度（一维扩散数值解 vs 解析 D=sqrt(2k/omega)）")
    lam_loam = tdfcnd(0.30, loam["MAXSMC"], 0.30, loam["QTZ"])
    cap_loam = hcpct(0.30, loam["MAXSMC"], 0.30)
    k_soil = lam_loam / cap_loam
    k_water_mol = 1.4e-7
    k_ocean_eff = 8.5e-3
    log("loam(θ=0.30)：lambda=%.3f W/m/K, C=%.3e J/m3/K -> k_soil=%.2e m2/s" %
        (lam_loam, cap_loam, k_soil))
    omega_d = 2.0 * np.pi / 86400.0
    omega_a = 2.0 * np.pi / (365.0 * 86400.0)
    for name, k in [("土壤(loam)", k_soil), ("纯水(分子)", k_water_mol), ("海洋(有效)", k_ocean_eff)]:
        Dd, Da = np.sqrt(2 * k / omega_d), np.sqrt(2 * k / omega_a)
        log("  %s: k=%.2e m2/s -> D_日=%.3f m  D_年=%.2f m" % (name, k, Dd, Da))
    log("\n数值验证（表面正弦强迫，末周期最小二乘拟合）：")
    cases = [
        ("土壤-日循环", k_soil, 86400.0, 10.0, 1.0, 400, 300.0, 5),
        ("纯水-日循环", k_water_mol, 86400.0, 10.0, 0.5, 250, 300.0, 5),
        ("海洋-日循环", k_ocean_eff, 86400.0, 10.0, 120.0, 400, 600.0, 4),
        ("土壤-年循环", k_soil, 365 * 86400.0, 10.0, 15.0, 300, 21600.0, 4),
        ("纯水-年循环", k_water_mol, 365 * 86400.0, 10.0, 8.0, 320, 21600.0, 4),
        ("海洋-年循环", k_ocean_eff, 365 * 86400.0, 10.0, 3000.0, 300, 43200.0, 4),
    ]
    e2_store = {}
    for tag, k, per, amp, depth, ndz, dt, nper in cases:
        om = 2.0 * np.pi / per
        D_ana = np.sqrt(2 * k / om)
        z, A, Ph, sample, tt = diffusion_run(k, per, amp, depth, ndz, dt, nper)
        D_num = fit_D(z, A, amp)
        m = z <= 2.8 * D_ana
        pslope = np.polyfit(z[m], Ph[m], 1)[0] if m.sum() > 3 else np.nan
        log("  %-12s D_解析=%7.3f m  D_数值(振幅)=%7.3f m (%+.2f%%)  相位斜率=%7.5f vs 1/D=%7.5f" %
            (tag, D_ana, D_num, 100 * (D_num - D_ana) / D_ana, pslope, 1.0 / D_ana))
        e2_store[tag] = (z, A, Ph, D_ana, sample, tt)
    log("\n对照书 4.3（土壤 0.1 m / 2-3 m；海洋 15-20 m / 200-300 m）：")
    log("  由书值反演有效扩散：D=17.5 m -> k=%.2e；D=250 m -> k=%.2e m2/s" %
        (0.5 * 17.5 ** 2 * omega_d, 0.5 * 250.0 ** 2 * omega_a))
    log("  纯水分子热扩散只有 6 cm / 1.2 m：海洋 15-20 m 的深度靠风浪混合（有效扩散放大 ~5 万倍）")
    lag_h = lambda zz, k: (zz / np.sqrt(2 * k / omega_d)) / omega_d / 3600.0
    log("  海洋日循环相位滞后：z=15 m 为 %.2f h；z=30 m 为 %.2f h（1/e 深度处 = T/2pi = 3.82 h）" %
        (lag_h(15.0, k_ocean_eff), lag_h(30.0, k_ocean_eff)))

    # ---------------- E3 ----------------
    sec("E3 SOILPARM.TBL 敏感性（读取实际 TBL 并与四条派生式互核）")
    log("派生式核验（源码注释：F11=log10(SATPSI)+BB*log10(MAXSMC)+2；"
        "SATDW=BB*SATDK*(SATPSI/MAXSMC)；REFSMC/WLTSMC 两式）：")
    maxerr = {k: 0.0 for k in ["F11", "SATDW", "REFSMC", "WLTSMC"]}
    maxerr_sp = {k: 0.0 for k in ["F11", "SATDW", "REFSMC", "WLTSMC"]}
    outliers = []
    for i, s in soil_all.items():
        if s["MAXSMC"] <= 0 or s["SATPSI"] <= 0 or s["SATDK"] <= 0:
            continue   # WATER(14) 等不参与（水点不由 TDFCND/入渗链驱动）
        f11 = np.log10(s["SATPSI"]) + s["BB"] * np.log10(s["MAXSMC"]) + 2.0
        satdw = s["BB"] * s["SATDK"] * (s["SATPSI"] / s["MAXSMC"])
        refsmc1 = s["MAXSMC"] * (5.79e-9 / s["SATDK"]) ** (1.0 / (2 * s["BB"] + 3))
        refsmc = refsmc1 + (1.0 / 3.0) * (s["MAXSMC"] - refsmc1)
        wltsmc1 = s["MAXSMC"] * (200.0 / s["SATPSI"]) ** (-1.0 / s["BB"])
        wltsmc = wltsmc1 - 0.5 * wltsmc1
        tgt = maxerr_sp if i in (17, 18, 19) else maxerr   # 17-19 为源码注释明言的人工特殊设定
        for k, ref in [("F11", f11), ("SATDW", satdw), ("REFSMC", refsmc), ("WLTSMC", wltsmc)]:
            err = abs(ref - s[k]) / s[k] if k == "SATDW" else abs(ref - s[k])
            tgt[k] = max(tgt[k], err)
            if err > 2e-3 and i not in (17, 18, 19) and k != "SATDW":
                outliers.append((i, s["name"], k, ref, s[k]))
    log("  常规类（1-16）最大偏差：F11=%.5f  REFSMC=%.5f  WLTSMC=%.5f；SATDW 相对=%.4f%%" %
        (maxerr["F11"], maxerr["REFSMC"], maxerr["WLTSMC"], 100 * maxerr["SATDW"]))
    log("  偏差超阈值清单（表值 vs 式算）：")
    for (i, nm, k, ref, tab) in outliers:
        log("    类 %2d %-14s %s：表值 %.4g，式算 %.4g" % (i, nm, k, tab, ref))
    log("  人工特殊类（PLAYA 17/LAVA 18/WHITE SAND 19）最大偏差：F11=%.2f  REFSMC=%.3f  WLTSMC=%.3f"
        "——源码注释明言按'导热似沙、导水似黏土'设定，不满足派生式" %
        (maxerr_sp["F11"], maxerr_sp["REFSMC"], maxerr_sp["WLTSMC"]))

    log("\n类间对照（θ=0.25，未冻结）：")
    log("  %-14s %6s %7s %7s %7s %6s %8s %9s %8s %8s %8s" % (
        "soil", "BB", "MAXSMC", "REFSMC", "WLTSMC", "beta", "lambda", "kappa",
        "D_day", "D_year", "KDT"))
    pick = [1, 3, 4, 6, 8, 12, 13, 15]
    refkdt, refdk = 3.0, 2.0e-6
    e3_rows = []
    for i in pick:
        s = soil_all[i]
        th = 0.25
        beta = float(np.clip((th - s["WLTSMC"]) / (s["REFSMC"] - s["WLTSMC"]), 0.0, 1.0)) \
            if s["REFSMC"] > s["WLTSMC"] else 0.0
        lam = tdfcnd(th, s["MAXSMC"], th, s["QTZ"], soilt=i) if s["MAXSMC"] > 0 else 0.0
        cap = hcpct(th, s["MAXSMC"], th) if s["MAXSMC"] > 0 else 1.0
        kap = lam / cap if cap > 0 else 0.0
        Dd = np.sqrt(2 * kap / omega_d) if kap > 0 else 0.0
        Da = np.sqrt(2 * kap / omega_a) if kap > 0 else 0.0
        kdt = refkdt * s["SATDK"] / refdk
        log("  %-14s %6.2f %7.3f %7.3f %7.3f %6.3f %8.3f %9.2e %8.3f %8.2f %8.2f" % (
            s["name"], s["BB"], s["MAXSMC"], s["REFSMC"], s["WLTSMC"], beta, lam, kap, Dd, Da, kdt))
        e3_rows.append((s, lam, kap, Dd, Da, kdt))
    log("\n  可行性水量(0-0.1 m)：%s" % "，".join(
        "%s=%.1f mm" % (r[0]["name"][:8], (r[0]["MAXSMC"] - r[0]["WLTSMC"]) * 100)
        for r in e3_rows if r[0]["MAXSMC"] > 0))
    log("  注：SAND 高 λ（石英 QTZ=0.92 主导）；CLAY 导水极弱（SATDK=9.7e-7 -> KDT 比沙小 48 倍）；"
        "WATER(14) 只作对照（水点走 ISLTYP=14，SATDK=0 且不参与 TDFCND）")

    # ---------------- E4 ----------------
    sec("E4 书第四章习题 3/5 数值复算（下边界章的书内题回看）")
    g_std, g_book = 9.80665, 9.78
    p_s, p_850 = 100000.0, 85000.0
    T_s, Td_s = 283.15, 278.15
    e_d = es_bolton(Td_s)
    q_e = eps_mw * e_d / (p_s - (1.0 - eps_mw) * e_d)
    Tv_e = T_s * (1.0 + 0.61 * q_e)
    rho_e = p_s / (Rd * Tv_e)
    log("习题 3(1)：e(td=5℃)=%.1f Pa -> q=%.4f kg/kg=%.2f g/kg（书 5.4 g/kg）" %
        (e_d, q_e, q_e * 1000))
    log("           Tv=%.2f K（书 284.08 K）；rho=p/(Rd*Tv)=%.4f kg/m3（书 1.23）" % (Tv_e, rho_e))
    Z_iso = Rd * Tv_e / g_std * np.log(p_s / p_850)
    log("习题 3(2)：等温层 Z=(Rd*Tv/g)*ln(p0/p)=%.1f gpm（书 1351.4；若 g=9.78 则 %.1f）" %
        (Z_iso, Rd * Tv_e / g_book * np.log(p_s / p_850)))
    m_w = q_e * (p_s - p_850) / g_std
    log("习题 3(3)：水汽柱质量=q*dp/g=%.2f kg/m2（书 8.3）；折液态水深=%.3f cm（书 0.83）" %
        (m_w, m_w / 1000 * 100))
    m_trop = (p_s - 20000.0) / g_book
    m_atm = 1013.25 * 100.0 / g_book
    log("习题 5：对流层柱质量=(1000-200)hPa/g=%.0f kg/m2（书 8179，取整差 1）；"
        "占大气总质量 %.1f%%（书 ~80%%）" % (m_trop, 100.0 * m_trop / m_atm))

    # ================= 出图 =================
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt

    # ---- fig1: 能量平衡 ----
    plt.rcParams["font.sans-serif"] = ["SimHei"]
    plt.rcParams["axes.unicode_minus"] = False
    fig, axes = plt.subplots(2, 2, figsize=(11.5, 8.0))
    t = wet["t"]
    ax = axes[0, 0]
    for v, lab, c in [(wet["Rn"], r"$R_n$", "k"), (wet["H"], r"$H$", "C3"),
                      (wet["LE"], r"$LE$", "C0"), (wet["G"], r"$G$", "C2")]:
        ax.plot(t, v, c, lw=1.8, label=lab)
    ax.axhline(0, color="gray", lw=0.8)
    ax.set_xlabel("地方时 (h)"); ax.set_ylabel(r"通量 (W m$^{-2}$)")
    ax.set_title("(a) 湿土 θ=0.30：地表能量分量日循环", fontsize=11)
    ax.legend(fontsize=9, ncol=4)
    ax.text(0.02, 0.05, "闭合残差 max = %.1e W m$^{-2}$" % np.abs(wet["resid"]).max(),
            transform=ax.transAxes, fontsize=8.5, color="C4")
    ax = axes[0, 1]
    ax.plot(t, wet["T1"] - 273.15, "C3-", lw=2, label="表皮 T1")
    ax.plot(t, wet["T2"] - 273.15, "k--", lw=1.4, label="2 m 气温 T2")
    for kk, st in enumerate(["stc1", "stc2", "stc3", "stc4"]):
        ax.plot(t, wet[st] - 273.15, lw=1.2, alpha=0.85,
                label="STC%d (%.2f m)" % (kk + 1, ZS[kk]))
    ax.set_xlabel("地方时 (h)"); ax.set_ylabel("温度 (℃)")
    ax.set_title("(b) 温度日循环：表皮/土层的阻尼与滞后", fontsize=11)
    ax.legend(fontsize=8, ncol=2)
    ax = axes[1, 0]
    ax.plot(t, wet["T1"] - 273.15, "C3-", lw=2, label=r"湿土 $T_1$")
    ax.plot(t, dry["T1"] - 273.15, "C1-", lw=2, label=r"干土 $T_1$")
    ax.set_xlabel("地方时 (h)"); ax.set_ylabel("表皮温度 (℃)")
    ax2 = ax.twinx()
    ax2.plot(t, wet["EF"], "C0:", lw=1.8, label="湿土 EF")
    ax2.plot(t, dry["EF"], "C5:", lw=1.8, label="干土 EF")
    ax2.set_ylabel("蒸发比 EF = LE/(H+LE)")
    ax2.set_ylim(-0.2, 1.2)
    ax.set_title("(c) 湿土 vs 干土：表皮温度与蒸发比", fontsize=11)
    lns = ax.get_lines() + ax2.get_lines()
    ax.legend(lns, [ln.get_label() for ln in lns], fontsize=8, loc="upper left")
    ax = axes[1, 1]
    ax.plot(t, wet["T1_noah"] - wet["T1_noahex"], "C0-", lw=1.6,
            label=r"线性化误差 $T_{1,lin}-T_{1,exact}$ (K)")
    ax.plot(t, wet["T1_noahex"] - wet["T1"], "C2--", lw=1.6,
            label=r"公式口径差 $T_{1,exact}^{noah}-T_{1,*}$ (K)")
    ax.axhline(0, color="gray", lw=0.8, label="_nolegend_")
    ax.set_xlabel("地方时 (h)"); ax.set_ylabel("温度差 (K)")
    ax2 = ax.twinx()
    ax2.plot(t, wet["R_lin"], "C3-", lw=1.2, alpha=0.8,
             label=r"线性化残差 (W m$^{-2}$)")
    ax2.set_ylabel(r"线性化残差 (W m$^{-2}$)", color="C3")
    ax.set_title("(d) Noah 线性化解的两类误差分解", fontsize=11)
    lns = ax.get_lines() + ax2.get_lines()
    ax.legend(lns, [ln.get_label() for ln in lns], fontsize=8, loc="upper left")
    fig.tight_layout()
    fig.savefig(os.path.join(FIGDIR, "ch16_energy_balance.png"), dpi=150)
    plt.close(fig)

    # ---- fig2: 土壤扩散 ----
    fig, axes = plt.subplots(2, 2, figsize=(11.5, 8.0))
    ax = axes[0, 0]
    colors = {"土壤(loam)": "C2", "纯水(分子)": "C0", "海洋(有效)": "C1"}
    for name, k in [("土壤(loam)", k_soil), ("纯水(分子)", k_water_mol), ("海洋(有效)", k_ocean_eff)]:
        Dd = np.sqrt(2 * k / omega_d)
        zz = np.linspace(0, min(3.2 * Dd, 60), 200)
        ax.semilogy(zz, np.exp(-zz / Dd), colors[name], lw=2, label="%s  D=%.2f m" % (name, Dd))
        ax.plot([Dd], [np.exp(-1)], "ko", ms=4)
    ax.axvspan(15, 20, color="C1", alpha=0.12)
    ax.text(0.55, 0.80, "书 4.3：海洋日变化 15-20 m", fontsize=8, color="C1",
            transform=ax.transAxes)
    ax.set_xlabel("深度 z (m)"); ax.set_ylabel(r"振幅比 $A(z)/A_0$（日循环）")
    ax.set_title("(a) 解析阻尼剖面与 1/e 深度", fontsize=11)
    ax.legend(fontsize=9, loc="lower left")
    ax.grid(alpha=0.25, which="both")
    ax = axes[0, 1]
    for tag, c, ls in [("土壤-日循环", "C2", "-"), ("纯水-日循环", "C0", "-"),
                       ("海洋-日循环", "C1", "-"), ("土壤-年循环", "C2", "--"),
                       ("纯水-年循环", "C0", "--"), ("海洋-年循环", "C1", "--")]:
        z, A, Ph, D_ana, sample, tt = e2_store[tag]
        m = z <= 2.8 * D_ana
        ax.plot(z[m] / D_ana, Ph[m], color=c, lw=1.4, ls=ls, alpha=0.9)
    ax.plot([0, 2.8], [0, 2.8], "k:", lw=1.2, label=r"解析 $\phi = z/D$")
    ax.set_xlim(0, 2.9); ax.set_ylim(0, 2.9)
    ax.set_xlabel(r"$z/D$"); ax.set_ylabel("相位滞后 (rad)")
    ax.set_title("(b) 相位滞后验证（实线日循环/虚线年循环）", fontsize=11)
    ax.legend(fontsize=8)
    ax.grid(alpha=0.25)
    ax = axes[1, 0]
    z, A, Ph, D_ana, sample, tt = e2_store["土壤-日循环"]
    for zfrac, c in [(0.0, "C3"), (0.05, "C1"), (0.10, "C2"), (0.20, "C0"), (0.50, "C4")]:
        j = int(round(zfrac / z[1]))
        ax.plot(tt / 3600.0, sample[:, j], color=c, lw=1.6, label="z=%.0f cm" % (100 * z[j]))
    ax.set_xlabel("一个周期内的时间 (h)"); ax.set_ylabel("温度扰动 (K)")
    ax.set_title("(c) 土壤日循环：0-50 cm 的阻尼与滞后", fontsize=11)
    ax.legend(fontsize=8, ncol=2)
    ax = axes[1, 1]
    z, A, Ph, D_ana, sample, tt = e2_store["海洋-日循环"]
    for zfrac, c in [(0.0, "C3"), (0.5, "C1"), (1.0, "C0"), (2.0, "C4")]:
        j = min(int(round(zfrac * D_ana / z[1])), len(z) - 1)
        ax.plot(tt / 3600.0, sample[:, j], color=c, lw=1.6,
                label="z=%.0f m（滞后 %.1f h）" % (z[j], zfrac * 3.82))
    ax.set_xlabel("一个周期内的时间 (h)"); ax.set_ylabel("温度扰动 (K)")
    ax.set_title(r"(d) 海洋有效扩散日循环（$\kappa_{eff}=8.5\times10^{-3}$ m$^2$s$^{-1}$）", fontsize=11)
    ax.legend(fontsize=8)
    fig.tight_layout()
    fig.savefig(os.path.join(FIGDIR, "ch16_soil_diffusion.png"), dpi=150)
    plt.close(fig)

    # ---- fig3: SOILPARM ----
    fig, axarr = plt.subplots(2, 2, figsize=(11.5, 8.0))
    ax = axarr[0, 0]
    names = [r[0]["name"] for r in e3_rows]
    x = np.arange(len(names))
    ax.bar(x - 0.25, [r[0]["MAXSMC"] for r in e3_rows], 0.25, label="MAXSMC 孔隙度", color="C0")
    ax.bar(x, [r[0]["REFSMC"] for r in e3_rows], 0.25, label="REFSMC 参考", color="C2")
    ax.bar(x + 0.25, [r[0]["WLTSMC"] for r in e3_rows], 0.25, label="WLTSMC 凋萎", color="C3")
    ax.set_xticks(x); ax.set_xticklabels([n[:11] for n in names], rotation=30, fontsize=8)
    ax.set_ylabel(r"体积含水量 (m$^3$ m$^{-3}$)")
    ax.set_title("(a) 三类临界含水量（实际 TBL 值）", fontsize=11)
    ax.legend(fontsize=8)
    ax = axarr[0, 1]
    ths = np.linspace(0.05, 0.46, 80)
    for i, c in [(1, "C1"), (6, "C2"), (12, "C3")]:
        s = soil_all[i]
        lam = [tdfcnd(th, s["MAXSMC"], th, s["QTZ"], soilt=i) for th in ths]
        ax.plot(ths, lam, c, lw=2, label="%s (QTZ=%.2f)" % (s["name"], s["QTZ"]))
    ax.set_xlabel(r"体积含水量 $\theta$"); ax.set_ylabel(r"$\lambda$ (W m$^{-1}$ K$^{-1}$)")
    ax.set_title("(b) TDFCND 热传导率随湿度", fontsize=11)
    ax.legend(fontsize=8); ax.grid(alpha=0.25)
    ax = axarr[1, 0]
    for i, c in [(1, "C1"), (6, "C2"), (12, "C3"), (13, "C4")]:
        s = soil_all[i]
        ths2 = np.linspace(s["WLTSMC"] * 1.02, s["MAXSMC"] * 0.999, 80)
        beta = np.clip((ths2 - s["WLTSMC"]) / (s["REFSMC"] - s["WLTSMC"]), 0, 1)
        ax.plot(ths2, beta, c, lw=2, label=s["name"])
    ax.axvline(0.25, color="gray", ls=":", lw=1)
    ax.text(0.252, 0.03, r"$\theta$=0.25", fontsize=8, color="gray")
    ax.set_xlabel(r"体积含水量 $\theta$")
    ax.set_ylabel(r"蒸发效率 $\beta=(\theta-\theta_w)/(\theta_{ref}-\theta_w)$")
    ax.set_title("(c) β(θ)：土壤质地控制的蒸发效率", fontsize=11)
    ax.legend(fontsize=8); ax.grid(alpha=0.25)
    ax = axarr[1, 1]
    Dd = [r[3] for r in e3_rows]; Da = [r[4] for r in e3_rows]
    ax.bar(x - 0.2, Dd, 0.4, label="D_日循环", color="C0")
    ax.bar(x + 0.2, Da, 0.4, label="D_年循环", color="C1")
    ax.set_yscale("log")
    ax.set_xticks(x); ax.set_xticklabels([n[:11] for n in names], rotation=30, fontsize=8)
    ax.set_ylabel("阻尼深度 (m)")
    ax.set_title("(d) 阻尼深度（θ=0.25；对照书 4.3 土壤 0.1/2-3 m）", fontsize=11)
    ax.legend(fontsize=8)
    fig.tight_layout()
    fig.savefig(os.path.join(FIGDIR, "ch16_soilparam.png"), dpi=150)
    plt.close(fig)

    log("\n图已输出：ch16_energy_balance.png / ch16_soil_diffusion.png / ch16_soilparam.png")
    _logf.close()