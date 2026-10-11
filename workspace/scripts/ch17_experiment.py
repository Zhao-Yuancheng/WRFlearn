# -*- coding: utf-8 -*-
"""
ch17 城市冠层专章 —— 轻轨实验（E1–E3）
环境: D:\\Code\\miniforge3\\envs\\WRFlearn\\python.exe
输出: 日志 workspace/logs/ch17_experiment.log；图 doc/figs/ch17_*.png

E1 城市等效表面 vs 乡村（同强迫单柱对比）：
   - 城市路面柱（SLUCM 口径 ALBG/EPSG/CAPG/AKSG，BOUNDG=1 零通量底）+ beta=0（不透水）
   - 乡村 loam（ch16 口径，beta 由 theta 定）
   - 同强迫（S/LWDN/T2/RH）下 T_s、Rn/H/LE/G 对比
E2 人为热：AH=AHDIUPRF(t)*AH_base 加入感热项（AHOPTION=1 口径）
   - AH on/off 的 T_s 差；三类城市 AH 强度（20/50/90 W/m2）
   - 绿化敏感性（FVG 有效 beta）
E3 URBPARM.TBL 敏感性：实读 USGS 三类（Low/Hi/Commercial）字段
   - ZR/SIGMA_ZED/ROOF_WIDTH/AH/ALH 表值；AH/ALH 日剖面；表面物性常数
"""
import os
import re
import numpy as np
from scipy.optimize import brentq

# ---------- 常量 ----------
Rd, Rv = 287.04, 461.5
eps_mw = Rd / Rv
cp = 1004.6
Lv = 2.501e6
sigma = 5.67e-8
A2B, A4B = 17.67, 29.65
PSURF = 100000.0
CH = 0.008
ALBEDO_RURAL = 0.20
CSOIL = 2.0e6
CH2O, CICE, CAIR = 4.2e6, 2.106e6, 1004.0

WRF_RUN = r"d:\Code\Learn\WRF\source\WRFv4.8.0\WRFV4.8.0\run"
LOGDIR = r"d:\Code\Learn\WRF\workspace\logs"
FIGDIR = r"d:\Code\Learn\WRF\doc\figs"
os.makedirs(LOGDIR, exist_ok=True)
os.makedirs(FIGDIR, exist_ok=True)
_logf = open(os.path.join(LOGDIR, "ch17_experiment.log"), "w", encoding="utf-8")


def log(*a):
    s = " ".join(str(x) for x in a)
    print(s)
    _logf.write(s + "\n")
    _logf.flush()


def sec(title):
    log("\n" + "=" * 78)
    log(title)
    log("=" * 78)


def es_bolton(T):
    return 611.2 * np.exp(A2B * (T - 273.15) / (T - A4B))


def qsat(T, p=PSURF):
    e = es_bolton(T)
    return eps_mw * e / (p - (1.0 - eps_mw) * e)


def tdfcnd_loam(smc, smcmax=0.439, qz=0.40):
    """ch16 版 TDFCND（loam，未冻）"""
    thkice, thkw, thko, thkqz = 2.2, 0.57, 2.0, 7.7
    satratio = smc / smcmax
    thks = thkqz ** qz * thko ** (1.0 - qz)
    thksat = thks ** (1.0 - smcmax) * thkice ** (smcmax - smc) * thkw ** smc
    gammd = (1.0 - smcmax) * 2700.0
    thkdry = (0.135 * gammd + 64.7) / (2700.0 - 0.947 * gammd)
    akel = np.log10(satratio) + 1.0 if satratio > 0.1 else 0.0
    return akel * (thksat - thkdry) + thkdry


def hcpct(smc, smcmax=0.439, sh2o=None):
    sh2o = smc if sh2o is None else sh2o
    return sh2o * CH2O + (1.0 - smcmax) * CSOIL + (smcmax - smc) * CAIR


def forcing(t_sec):
    h = (t_sec / 3600.0) % 24.0
    soldn = 880.0 * np.sin(np.pi * (h - 6.0) / 12.0) if 6.0 < h < 18.0 else 0.0
    lwdn = 285.0
    T2 = 291.0 + 5.0 * np.cos(2.0 * np.pi * (h - 15.0) / 24.0)
    q2 = 0.50 * qsat(T2)
    return soldn, lwdn, T2, q2


# ---------- URBPARM.TBL 解析（USGS 首段） ----------
def parse_urbparm(path):
    with open(path, "r", encoding="utf-8", errors="ignore") as f:
        lines = f.readlines()
    docs = []
    fields = {}
    started = False
    for ln in lines:
        s = ln.strip()
        if s.startswith("Number of urban categories"):
            if started:
                break                      # 只取首段（USGS）
            started = True
            continue
        if not started:
            continue
        m = re.match(r"^([A-Za-z_]+):\s*(.+)$", s)
        if m:
            key = m.group(1)
            parts = [p for p in re.split(r"[,\s]+", m.group(2).strip().rstrip(",")) if p]
            try:
                nums = [float(v) for v in parts]
            except ValueError:
                nums = None
            fields.setdefault(key, nums if nums is not None else parts)
    return fields


# ---------- 单柱模型（ch16 框架；城市 = 不透水 + AH） ----------
def run_column(tag, lam0, cap0, albedo, emiss, dzs, t_init, beta, ah_profile=None,
               ah_base=0.0, nspin_days=3, bottom_const=None, bottom_depth=1.0, ch=None):
    """显式多层柱 + brentq 精确表皮温度；ah_profile(h) 为 24 值小时剖面（01h 起）；
    bottom_const=None → 零通量底；否则底层与 bottom_const 交换（深度 bottom_depth）"""
    CHL = CH if ch is None else ch
    dt = 300.0
    nspin, nday = int(nspin_days * 86400 / dt), int(86400 / dt)
    dzs = np.asarray(dzs, dtype=float)
    n = len(dzs)
    stc = np.array(t_init, dtype=float)
    rec = {k: [] for k in ["t", "T1", "stc1", "stc2", "Rn", "H", "LE", "G", "AH"]}

    def ah_now(t):
        if ah_profile is None or ah_base == 0.0:
            return 0.0
        h = int((t / 3600.0) % 24.0)
        return ah_base * ah_profile[h % 24]

    def step(t, stc):
        soldn, lwdn, T2, q2 = forcing(t)
        rho = PSURF / (Rd * T2 * (1.0 + 0.61 * q2))
        fdown = soldn * (1.0 - albedo) + lwdn
        AH = ah_now(t)

        def bal(T1):
            H = rho * cp * CHL * (T1 - T2)
            LE = Lv * beta * rho * CHL * (qsat(T1) - q2)
            G = lam0 * (T1 - stc[0]) / (0.5 * dzs[0])
            Rn = fdown - emiss * sigma * T1 ** 4
            return Rn + AH - H - LE - G

        T1 = brentq(bal, T2 - 40.0, T2 + 95.0, xtol=1e-12, rtol=1e-15)
        H = rho * cp * CHL * (T1 - T2)
        LE = Lv * beta * rho * CHL * (qsat(T1) - q2)
        G = lam0 * (T1 - stc[0]) / (0.5 * dzs[0])
        Rn = fdown - emiss * sigma * T1 ** 4
        return T1, H, LE, G, Rn, AH

    def advance(stc, G_top, dt):
        cap = np.full(n, cap0)
        F = np.zeros(n + 1)
        F[0] = G_top
        for k in range(n - 1):
            dzif = 0.5 * (dzs[k] + dzs[k + 1])
            F[k + 1] = lam0 * (stc[k] - stc[k + 1]) / dzif
        if bottom_const is None:
            F[n] = 0.0
        else:
            F[n] = lam0 * (stc[n - 1] - bottom_const) / bottom_depth
        dstc = (F[:-1] - F[1:]) / (cap * dzs) * dt
        return stc + dstc

    for it in range(nspin + nday):
        t = it * dt
        T1, H, LE, G, Rn, AH = step(t, stc)
        stc = advance(stc, G, dt)
        if it >= nspin:
            rec["t"].append(((it - nspin) * dt) / 3600.0)
            for key, val in [("T1", T1), ("Rn", Rn), ("H", H), ("LE", LE),
                             ("G", G), ("AH", AH)]:
                rec[key].append(val)
            for k in range(min(n, 2)):
                rec["stc%d" % (k + 1)].append(stc[k])
    out = {k: np.array(v) for k, v in rec.items()}
    out["tag"] = tag
    return out


# ==================================================================
if __name__ == "__main__":
    urb = parse_urbparm(os.path.join(WRF_RUN, "URBPARM.TBL"))
    sec("E3 前置：URBPARM.TBL 实读（USGS 三类）")
    for k in ["ZR", "SIGMA_ZED", "ROOF_WIDTH", "ROAD_WIDTH", "AH", "ALH"]:
        log("  %-14s %s" % (k, urb.get(k)))
    log("  表面物性（三类同值）：ALBR/B/G=0.20；EPSR/B=0.90 EPSG=0.95；"
        "CAPR/B=1.0e6 CAPG=1.4e6; AKSR/B=0.67 AKSG=0.4004; Z0R/G=0.01 Z0B=1e-4 m；"
        "TRL/B/GLEND=293 K")
    log("  AHOPTION=%s（0 默认）  CH_SCHEME=%s  TS_SCHEME=%s  BOUNDG=%s  FVG=%s" % (
        urb.get("AHOPTION"), urb.get("CH_SCHEME"), urb.get("TS_SCHEME"),
        urb.get("BOUNDG"), urb.get("FVG")))
    ahd = urb.get("AHDIUPRF")
    log("  AHDIUPRF(24h,01h 起) 峰值 %.2f@%dh，谷 %.2f@%dh，日均 %.3f" % (
        max(ahd), int(np.argmax(ahd)) + 1, min(ahd), int(np.argmin(ahd)) + 1, np.mean(ahd)))
    alh = urb.get("ALHSEASON")
    log("  ALHSEASON(MAM/JJA/SON/DJF)=%s；ALH(三类)=%s；AH(三类)=%s" % (alh, urb.get("ALH"), urb.get("AH")))

    # ---------- 公共配置 ----------
    DZ_URB = [0.05, 0.25, 0.50, 0.75]        # SLUCM DDZG
    T_WAIT = 295.0
    lam_urb, cap_urb = 0.4004, 1.4e6          # AKSG / CAPG
    lam_rural = tdfcnd_loam(0.30)
    cap_rural = hcpct(0.30)
    T0 = [295.0, 294.0, 293.5, 293.0]

    sec("E1 城市等效表面 vs 乡村（同强迫，24 h）")
    log("  城市：ALBG=0.20 EPSG=0.95 AKSG=%.4f CAPG=%.1e（4 层 0.05/0.25/0.50/0.75，零通量底）" %
        (lam_urb, cap_urb))
    log("  乡村：loam theta=0.30，lam=%.3f cap=%.3e，beta=0.89" % (lam_rural, cap_rural))
    city = run_column("city0", lam_urb, cap_urb, 0.20, 0.95, DZ_URB, T0, beta=0.0,
                      ah_profile=None, ah_base=0.0)
    rural = run_column("rural", lam_rural, cap_rural, 0.20, 0.97, [0.1, 0.3, 0.6, 1.0],
                       [295.0, 294.0, 293.5, 293.0], beta=0.89)
    t = city["t"]
    day = (t > 6) & (t < 18)
    for run in (city, rural):
        Rn, H, LE, G = run["Rn"], run["H"], run["LE"], run["G"]
        log("\n[%s] 白天均 Rn/H/LE/G=%7.1f/%7.1f/%7.1f/%7.1f；夜间均=%7.1f/%7.1f/%7.1f/%7.1f" %
            (run["tag"], Rn[day].mean(), H[day].mean(), LE[day].mean(), G[day].mean(),
             Rn[~day].mean(), H[~day].mean(), LE[~day].mean(), G[~day].mean()))
        log("    T_s 最高 %.2f K (%.1f℃)  最低 %.2f K (%.1f℃)" %
            (run["T1"].max(), run["T1"].max() - 273.15, run["T1"].min(), run["T1"].min() - 273.15))
    dT = city["T1"] - rural["T1"]
    log("\n  城市-乡村 T_s 差：白天均 %+.2f K，夜间均 %+.2f K，全天最大 %+.2f K（%02.1fh）" % (
        dT[day].mean(), dT[~day].mean(),
        dT[np.argmax(np.abs(dT))], t[np.argmax(np.abs(dT))]))
    log("  **表温差的结构昼强夜弱**：白天城市无蒸发潜热、路面低热传导 → 能量全部转为感热与储热，"
        "T_s 冲高；夜间城市靠储热（CAPG=1.4e6）与低发射冷却（EPSG=0.95 vs 乡村 0.97）少降温，"
        "而乡村辐射冷却 + 蒸发继续 → 仍差 %+.2f K。注意：这是**表皮温度**口径；"
        "2 m 气温的城市热岛通常夜强昼弱（稳定边界层抑制通风 + 人为热释放），需要真实边界层模式，"
        "ch19 的集群双跑将给出 T2/HFX 口径（呼应论文2 的 UHI 评估）" % dT[~day].mean())
    log("  夜间 G 差（城市-乡村）：%+.1f W/m2（城市储热放热）" %
        (city["G"][~day].mean() - rural["G"][~day].mean()))
    city_ch2 = run_column("city_ch2", lam_urb, cap_urb, 0.20, 0.95, DZ_URB, T0, beta=0.0,
                          ah_profile=None, ah_base=0.0, ch=0.016)
    log("  通风敏感性：CH 加倍（0.008→0.016）后城市 T_s 最高 %.1f℃（降 %.1f K）——"
        "简化柱用常数 CH、无夜间稳定边界层封盖效应，故夜间 ΔT 偏小（同 2 m 气温口径的已知差异）" %
        (city_ch2["T1"].max() - 273.15, city["T1"].max() - city_ch2["T1"].max()))

    sec("E2 人为热（AHOPTION=1 口径：AH 加入感热项）与绿化敏感性")
    ah24 = np.array(ahd)
    for name, base in [("Low-dens Res", urb["AH"][0]), ("Hi-dens Res", urb["AH"][1]),
                       ("Commercial", urb["AH"][2])]:
        c_ah = run_column("city_ah", lam_urb, cap_urb, 0.20, 0.95, DZ_URB, T0, beta=0.0,
                          ah_profile=ah24, ah_base=base)
        dTAH = c_ah["T1"] - city["T1"]
        log("  %-13s AH=%.0f W/m2（日均 %.1f）→ ΔT_s 白天均 %+.2f K，夜间均 %+.2f K，日均 %+.2f K" %
            (name, base, base * ah24.mean(), dTAH[day].mean(), dTAH[~day].mean(), dTAH.mean()))
        if abs(base - 50.0) < 1e-6:
            city_ah = c_ah
    log("\n  绿量敏感性（FVG=0.2 口径：beta_eff=FVG*beta_veg=0.2*0.89=0.18）：")
    c_veg = run_column("city_veg", lam_urb, cap_urb, 0.20, 0.95, DZ_URB, T0, beta=0.18,
                       ah_profile=ah24, ah_base=50.0)
    dTv = c_veg["T1"] - city_ah["T1"]
    log("    城市+绿量（beta=0.18）相对纯不透水：ΔT_s 白天均 %+.2f K，夜间均 %+.2f K" %
        (dTv[day].mean(), dTv[~day].mean()))
    log("    夏季 ALH=25 W/m2（Hi-dens）若开启（ALHOPTION=1）等效潜热冷却 ~%.1f K 量级（%s）" %
        (25.0 / 28.0, "按有效导纳 ~28 W/m2/K 量级估算"))

    # ================= 出图 =================
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    plt.rcParams["font.sans-serif"] = ["SimHei"]
    plt.rcParams["axes.unicode_minus"] = False

    fig, axes = plt.subplots(2, 2, figsize=(11.5, 8.0))
    ax = axes[0, 0]
    ax.plot(t, city["T1"] - 273.15, "C3-", lw=2, label="城市（不透水）")
    ax.plot(t, rural["T1"] - 273.15, "C2-", lw=2, label="乡村（loam 湿）")
    ax.plot(t, 291.0 + 5.0 * np.cos(2 * np.pi * (t - 15) / 24) - 273.15, "k--", lw=1.3, label="2 m 气温")
    ax.set_xlabel("地方时 (h)"); ax.set_ylabel("表皮温度 (℃)")
    ax.set_title("(a) 城市 vs 乡村：表皮温度日循环", fontsize=11)
    ax.legend(fontsize=9); ax.grid(alpha=0.25)
    ax = axes[0, 1]
    for v, lab, c in [(city["Rn"], r"$R_n$", "k"), (city["H"], r"$H$", "C3"),
                      (city["LE"], r"$LE$", "C0"), (city["G"], r"$G$", "C2")]:
        ax.plot(t, v, c, lw=1.8, label=lab)
    ax.axhline(0, color="gray", lw=0.8)
    ax.set_xlabel("地方时 (h)"); ax.set_ylabel(r"通量 (W m$^{-2}$)")
    ax.set_title("(b) 城市表面能量分量（beta=0 无潜热）", fontsize=11)
    ax.legend(fontsize=9, ncol=4)
    ax = axes[1, 0]
    ax.plot(t, city_ah["T1"] - city["T1"], "C3-", lw=2, label=r"AH=50 W m$^{-2}$ 的 $\Delta T_s$")
    ax.plot(t, c_veg["T1"] - city_ah["T1"], "C2--", lw=2, label=r"绿量 FVG=0.2 的 $\Delta T_s$")
    ax.axhline(0, color="gray", lw=0.8)
    ax.set_xlabel("地方时 (h)"); ax.set_ylabel("温度差 (K)")
    ax.set_title("(c) 人为热与绿量的增温/降温贡献", fontsize=11)
    ax.legend(fontsize=9); ax.grid(alpha=0.25)
    ax = axes[1, 1]
    hh = np.arange(1, 25)
    for base, name, c in [(20.0, "Low-dens", "C0"), (50.0, "Hi-dens", "C3"),
                          (90.0, "Commercial", "C5")]:
        ax.plot(hh, base * ah24, c + "-", lw=2, label="%s（AH=%.0f）" % (name, base))
    ax.set_xlabel("地方时 (h)"); ax.set_ylabel(r"$AH(t)$ (W m$^{-2}$)")
    ax.set_title("(d) 人为热日剖面 AH×AHDIUPRF（URBPARM 实值）", fontsize=11)
    ax.legend(fontsize=9); ax.grid(alpha=0.25)
    fig.tight_layout()
    fig.savefig(os.path.join(FIGDIR, "ch17_urban_energy.png"), dpi=150)
    plt.close(fig)

    fig, axes = plt.subplots(1, 2, figsize=(11.0, 4.2))
    ax = axes[0]
    ax.step(hh, ah24, where="mid", color="C3", lw=2)
    ax.set_xlabel("地方时 (h)"); ax.set_ylabel("AHDIUPRF (-)")
    ax.set_title("(a) 人为热归一化日剖面（峰值 17h）", fontsize=11)
    ax.grid(alpha=0.25)
    ax = axes[1]
    ax.plot(hh, 20 * ah24, "C0-", lw=2, label="Low-dens Res")
    ax.plot(hh, 50 * ah24, "C3-", lw=2, label="Hi-dens Res")
    ax.plot(hh, 90 * ah24, "C5-", lw=2, label="Commercial")
    ax.set_xlabel("地方时 (h)"); ax.set_ylabel(r"$AH(t)$ (W m$^{-2}$)")
    ax.set_title("(b) 三类城市人为热日循环", fontsize=11)
    ax.legend(fontsize=9); ax.grid(alpha=0.25)
    fig.tight_layout()
    fig.savefig(os.path.join(FIGDIR, "ch17_ah_profile.png"), dpi=150)
    plt.close(fig)

    log("\n图已输出：ch17_urban_energy.png / ch17_ah_profile.png")
    _logf.close()