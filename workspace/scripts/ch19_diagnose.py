# -*- coding: utf-8 -*-
"""ch19 诊断（轻轨）：
  A) 城市/乡村格点 T2 对比与热岛强度（exp2=CTRL vs exp3=BEP+BEM；exp1=SLUCM）
  B) 城市方案效应图（exp3 − exp2 的 T2 空间差，夜/昼）
  C) T-lnP 假绝热图（含 LCL/LFC/CAPE，MetPy）
  D) T2 vs ERA5（城市点日最高气温序列）

输入：workspace/data/ch19/stage/<case>_d02_{surf,prof}.nc（集群端 ncks 子集）
输出：doc/figs/ch19_*.png；日志 workspace/logs/ch19_diagnose.log
环境：D:\\Code\\miniforge3\\envs\\WRFlearn\\python.exe
"""
import os
import glob
import numpy as np

STAGE = r"d:\Code\Learn\WRF\workspace\data\ch19\stage"
LOGDIR = r"d:\Code\Learn\WRF\workspace\logs"
FIGDIR = r"d:\Code\Learn\WRF\doc\figs"
ERA5 = r"d:\Code\Learn\WRF\workspace\data\t2m_202507_lz.nc"
os.makedirs(LOGDIR, exist_ok=True)
os.makedirs(FIGDIR, exist_ok=True)
_logf = open(os.path.join(LOGDIR, "ch19_diagnose.log"), "w", encoding="utf-8")


def log(*a):
    s = " ".join(str(x) for x in a)
    print(s)
    _logf.write(s + "\n")
    _logf.flush()


def _concat(vals):
    return np.concatenate(vals, axis=0) if len(vals) > 1 else vals[0]


def _times_of(d, n):
    """取 Times；若子集里没带 Times，则用 START_DATE + 逐帧 1 小时推。"""
    if "Times" in d.variables:
        return ["".join(np.char.decode(x)) for x in d.variables["Times"][:]]
    sd = getattr(d, "START_DATE", "2025-07-12_00:00:00")
    import datetime as _dt
    t0 = _dt.datetime.strptime(sd.replace("_", " "), "%Y-%m-%d %H:%M:%S")
    return [(t0 + _dt.timedelta(hours=i)).strftime("%Y-%m-%d_%H:%M:%S") for i in range(n)]


def load_surf(case):
    """拼接 stage/<case>_surf_*.nc（逐文件抽取的产物）。"""
    from netCDF4 import Dataset
    fs = sorted(glob.glob(os.path.join(STAGE, "%s_surf_*.nc" % case)))
    if not fs:
        return None
    keys = ["T2", "TSK", "PSFC", "HFX", "LH", "U10", "V10", "RAINC", "RAINNC",
            "IVGTYP", "LU_INDEX", "XLAT", "XLONG", "HGT"]
    acc = {k: [] for k in keys}
    times = []
    for f in fs:
        d = Dataset(f)
        n = len(d.dimensions["Time"])
        for k in keys:
            if k in d.variables:
                acc[k].append(np.asarray(d.variables[k][:]))
        times += _times_of(d, n)
        d.close()
    out = {k: _concat(v) for k, v in acc.items() if v}
    out["_times"] = times
    return out


def load_prof(case):
    """拼接 stage/<case>_prof_*.nc。"""
    from netCDF4 import Dataset
    fs = sorted(glob.glob(os.path.join(STAGE, "%s_prof_*.nc" % case)))
    if not fs:
        return None
    keys = ["T", "QVAPOR", "P", "PB", "U", "V"]
    acc = {k: [] for k in keys}
    times = []
    for f in fs:
        d = Dataset(f)
        n = len(d.dimensions["Time"])
        for k in keys:
            if k in d.variables:
                acc[k].append(np.asarray(d.variables[k][:]))
        times += _times_of(d, n)
        d.close()
    out = {k: _concat(v) for k, v in acc.items() if v}
    out["_times"] = times
    return out


def load_mask():
    """城市掩膜：取自本地 wrfinput_d02（FRC_URB2D），按 ncks 窗口裁剪。
    ncks 用 1-based 下标 (-d west_east,45,75 -d south_north,40,70)
    → numpy 0-based: west_east 44:75, south_north 39:70
    """
    from netCDF4 import Dataset
    p = r"d:\Code\Learn\WRF\workspace\data\ch19\wrfinput\sf1_wrfinput_d02"
    d = Dataset(p)
    frc = np.asarray(d.variables["FRC_URB2D"][0])[39:70, 44:75]
    lu = np.asarray(d.variables["LU_INDEX"][0]).astype(int)[39:70, 44:75]
    d.close()
    return frc, lu


def load_p14(case="sf0"):
    """优先读专用单帧文件 <case>_p14.nc（2025-07-16 06 UTC = 14 LT）"""
    from netCDF4 import Dataset
    f = os.path.join(STAGE, "%s_p14.nc" % case)
    if os.path.exists(f):
        d = Dataset(f)
        out = {k: np.asarray(d.variables[k][:]) for k in ["T", "QVAPOR", "P", "PB"]}
        out["_times"] = ["".join(np.char.decode(x)) for x in d.variables["Times"][:]]
        d.close()
        return out
    return None


# ---------------------------------------------------------------- A + B
def part_AB():
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    plt.rcParams["font.sans-serif"] = ["SimHei"]
    plt.rcParams["axes.unicode_minus"] = False

    cases = [c for c in ["base0", "sf0", "sf1", "sf3"] if load_surf(c)]
    data = {c: load_surf(c) for c in cases}
    if not data:
        log("A/B: 无 stage 数据，跳过")
        return None
    log("A/B: 可用算例 = %s" % cases)
    for c in cases:
        d = data[c]
        log("  %s: %d 帧, T2 shape=%s" % (c, len(d["_times"]), d["T2"].shape))

    frc, lu = load_mask()
    log("  掩膜（来自 wrfinput_d02 窗口）: shape=%s, FRC max=%.2f" % (frc.shape, frc.max()))
    urban = frc > 0.5
    rural = (frc <= 0.0) & np.isin(lu, [10, 12, 14])
    log("  城市格点 %d，乡村格点 %d（窗口 %dx%d）"
        % (int(urban.sum()), int(rural.sum()), frc.shape[1], frc.shape[0]))
    if urban.sum() == 0 or rural.sum() == 0:
        log("  掩膜为空，跳过 A/B")
        return None

    tt = data[cases[0]]["_times"]
    # UTC → 地方时（兰州 ~UTC+7）
    hours = np.array([int(t[11:13]) for t in tt]) + 7
    hours = hours % 24
    day = np.array([t[8:10] for t in tt]).astype(int)
    m = (day >= 13) & (day <= 16)
    night = m & ((hours <= 6) | (hours >= 22))
    dayt = m & (hours >= 12) & (hours <= 17)

    LAB = {"base0": "CTRL-A(=0,MYNN)", "sf1": "SLUCM(=1,MYNN)",
           "sf0": "CTRL-B(=0,YSU)", "sf3": "BEP+BEM(=3,YSU)"}
    COL = {"base0": "C0", "sf1": "C2", "sf0": "C1", "sf3": "C3"}

    series = {}
    for c in cases:
        t2 = data[c]["T2"]
        tu = t2[:, urban].mean(axis=1)
        tr = t2[:, rural].mean(axis=1)
        series[c] = (tu, tr, tu - tr)
        log("  %s: 热岛 ΔT2 夜 %.2f K / 昼 %.2f K（最大 %.2f K）"
            % (LAB[c], series[c][2][night].mean(), series[c][2][dayt].mean(),
               series[c][2][m].max()))

    fig, axes = plt.subplots(1, 3, figsize=(15.5, 4.6))
    ax = axes[0]
    x = np.arange(len(tt)) / 24.0
    for c in cases:
        ax.plot(x, series[c][2], lw=1.5, color=COL[c], label=LAB[c])
    ax.axhline(0, color="gray", lw=0.8)
    ax.set_xlabel("模拟时间（天，自 2025-07-12 00 UTC）"); ax.set_ylabel(r"$\Delta T_2$ = 城市 − 乡村 (K)")
    ax.set_title("(a) 城市热岛强度日循环（四档）", fontsize=11)
    ax.legend(fontsize=8); ax.grid(alpha=0.3)

    ax = axes[1]
    pairs = [(("base0", "sf1"), "SLUCM(=1) − CTRL-A", "C2"),
             (("sf0", "sf3"), "BEP+BEM(=3) − CTRL-B", "C3")]
    xp = np.arange(len(tt)) / 24.0
    for (a, b), lab, col in pairs:
        if a in series and b in series:
            d = series[b][2] - series[a][2]
            ax.plot(xp, d, lw=1.6, color=col, label=lab)
            log("  %s: 夜 %.3f K / 昼 %.3f K（最大 %.3f K）"
                % (lab, d[night].mean(), d[dayt].mean(), d[m].max()))
    ax.axhline(0, color="gray", lw=0.8)
    ax.set_xlabel("模拟时间（天）"); ax.set_ylabel(r"城市方案对热岛的增量 (K)")
    ax.set_title("(b) 城市方案的效应（两对单变量对照）", fontsize=11)
    ax.legend(fontsize=8); ax.grid(alpha=0.3)

    ax = axes[2]
    labs, nv, dv = [], [], []
    for c in cases:
        labs.append(LAB[c]); nv.append(series[c][2][night].mean()); dv.append(series[c][2][dayt].mean())
    xb = np.arange(len(labs))
    ax.bar(xb - 0.2, nv, 0.4, label="夜间 (22-06 LT)", color="C0")
    ax.bar(xb + 0.2, dv, 0.4, label="午后 (12-17 LT)", color="C3")
    ax.set_xticks(xb); ax.set_xticklabels(["A=0", "SLUCM=1", "B=0", "BEP=3"], fontsize=9)
    ax.set_ylabel(r"$\Delta T_2$ (K)")
    ax.set_title("(c) 热岛的夜/昼分解（07-13~16）", fontsize=11)
    ax.legend(fontsize=8); ax.grid(alpha=0.3, axis="y")
    plt.tight_layout()
    out = os.path.join(FIGDIR, "ch19_uhi_diurnal.png")
    plt.savefig(out, dpi=150); plt.close()
    log("  图: %s" % out)

    # ---- B: 空间差图（夜/昼各一帧；帧数以最短算例为准） ----
    if "sf3" in data and "sf0" in data:
        nmax = min(data["sf0"]["T2"].shape[0], data["sf3"]["T2"].shape[0])
        i_night = None
        i_day = None
        for k in range(nmax):
            t, h, dd = tt[k], hours[k], day[k]
            if dd == 15 and h == 4 and i_night is None:
                i_night = k
            if dd == 15 and h == 14 and i_day is None:
                i_day = k
        i_night = i_night if i_night is not None else nmax // 2
        i_day = i_day if i_day is not None else min(nmax - 1, nmax // 2 + 8)
        fig, axes = plt.subplots(1, 2, figsize=(11.5, 4.8))
        for ax, k, ttl in [(axes[0], i_night, "夜间 04 LT"), (axes[1], i_day, "午后 14 LT")]:
            diff = data["sf3"]["T2"][k] - data["sf0"]["T2"][k]
            lon = data["sf0"]["XLONG"][0]; lat = data["sf0"]["XLAT"][0]
            vmax = float(np.abs(diff).max()) or 1.0
            m = ax.pcolormesh(lon, lat, diff, cmap="RdBu_r",
                              vmin=-vmax, vmax=vmax, shading="auto")
            ax.contour(lon, lat, np.asarray(frc), levels=[0.5], colors="k", linewidths=0.8)
            plt.colorbar(m, ax=ax, label=r"$\Delta T_2$(=3 - 0) (K)", shrink=0.85)
            ax.set_title("%s（%s，黑线=城市分数 0.5）" % (ttl, tt[k]), fontsize=11)
            ax.set_xlabel("经度"); ax.set_ylabel("纬度")
            log("  %s 帧 %d (%s): ΔT2 min=%.2f max=%.2f K"
                % (ttl, k, tt[k], diff.min(), diff.max()))
        plt.tight_layout()
        out = os.path.join(FIGDIR, "ch19_uhi_maps.png")
        plt.savefig(out, dpi=150); plt.close()
        log("  图: %s" % out)
    return series


# ---------------------------------------------------------------- C
def part_C():
    prof = load_p14("sf0") or load_prof("sf0")
    if prof is None:
        log("C: 无 prof 数据，跳过")
        return
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    plt.rcParams["font.sans-serif"] = ["SimHei"]
    plt.rcParams["axes.unicode_minus"] = False

    # 城市点：窗口中心（45..75 → i=15 对应全域名 ~60）
    j0, i0 = prof["T"].shape[2] // 2, prof["T"].shape[3] // 2
    it = 0
    for k, t in enumerate(prof["_times"]):
        if "2025-07-16_06" in t:
            it = k
            break
    log("C: prof 帧时刻（前 24 个）= %s" % prof["_times"][:24])
    log("C: 使用帧 %d（%s）城市点 (j,i)=(%d,%d)" % (it, prof["_times"][it], j0, i0))

    R, cp, eps = 287.04, 1004.6, 0.622
    kappa = R / cp
    p = (prof["P"][0, :, j0, i0] + prof["PB"][0, :, j0, i0]) / 100.0   # hPa
    # ★ WRF 的 T 是"扰动位温"：θ = T_field + base_temp（本案例 namelist: base_temp = 290）
    th = prof["T"][0, :, j0, i0] + 290.0
    T = th * (p / 1000.0) ** kappa          # 由位温反解绝对温度
    qv = prof["QVAPOR"][0, :, j0, i0]
    log("  θ(近地)=%.2f K  T(近地)=%.2f C  qv=%.2f g/kg  p=%.1f hPa"
        % (th[0], T[0] - 273.15, qv[0] * 1000, p[0]))
    # 露点（Bolton 反解）
    e = np.maximum(qv * p / (eps + qv), 1e-6)
    ln = np.log(e / 6.112)
    Td = (243.5 * ln / (17.67 - ln)) + 273.15

    try:
        import metpy.calc as mpcalc
        from metpy.units import units
        P = p * units.hPa
        Tk = T * units.K
        Tdk = Td * units.K
        lcl_p, lcl_t = mpcalc.lcl(P[0], Tk[0], Tdk[0])
        prof_p = mpcalc.parcel_profile(P, Tk[0], Tdk[0])
        cape, cin = mpcalc.cape_cin(P, Tk, Tdk, prof_p)
        lfc_p, lfc_t = mpcalc.lfc(P, Tk, Tdk)
        el_p, el_t = mpcalc.el(P, Tk, Tdk)
        log("  MetPy: LCL=%.1f hPa   LFC=%.1f   EL=%.1f   CAPE=%.0f J/kg   CIN=%.0f J/kg"
            % (lcl_p.m, lfc_p.m, el_p.m, cape.m, cin.m))
    except Exception as ex:
        log("  MetPy 计算失败：%s（改用手写判据）" % ex)

    fig, ax = plt.subplots(figsize=(7.4, 8.4))
    yof = lambda pp: np.log(1000.0 / pp)

    def Td_sat(Tc):
        es = 6.112 * np.exp(17.67 * Tc / (Tc + 243.5))
        return es

    # 干绝热线
    for t0c in range(-30, 45, 10):
        pp = np.linspace(1000, 200, 80)
        th = (t0c + 273.15) * (1000.0 / pp) ** (R / cp)
        ax.plot(th - 273.15, yof(pp), color="0.75", lw=0.8, zorder=1)
    # 饱和比湿线
    for qs_g in [1, 2, 4, 8, 16]:
        Tc = np.linspace(-30, 40, 200)
        e = Td_sat(Tc)
        pp = 0.622 * e / (qs_g / 1000.0) / 100.0 + e / 100.0  # hPa
        m = (pp <= 1050) & (pp >= 200)
        ax.plot(Tc[m], yof(pp[m]), color="0.45", lw=0.8, ls=":", zorder=1)

    ax.plot(T - 273.15, yof(p), "k-", lw=2.0, label="温度层结")
    ax.plot(Td - 273.15, yof(p), "k--", lw=1.6, label="露点层结")
    try:
        ax.plot(np.asarray(prof_p) - 273.15, yof(p), "r-", lw=2.0, label="气块路径")
        ax.plot([lcl_t.m - 273.15], [yof(lcl_p.m)], "bs", ms=8)
        ax.annotate("LCL %.0f hPa" % lcl_p.m, (lcl_t.m - 273.15, yof(lcl_p.m)),
                    xytext=(-70, 8), textcoords="offset points", fontsize=9)
        if lfc_p is not None:
            ax.plot([lfc_t.m - 273.15], [yof(lfc_p.m)], "g^", ms=9)
            ax.annotate("LFC %.0f hPa" % lfc_p.m, (lfc_t.m - 273.15, yof(lfc_p.m)),
                        xytext=(-70, -14), textcoords="offset points", fontsize=9)
        ax.set_title("兰州城市点 T-lnP（2025-07-16 14 LT，CTRL-B=0）\nCAPE=%.0f J/kg，CIN=%.0f J/kg"
                     % (cape.m, cin.m), fontsize=11)
    except Exception:
        ax.set_title("兰州城市点 T-lnP（2025-07-16 14 LT）", fontsize=11)
    for ppp in [1000, 900, 850, 800, 700, 600, 500, 400, 300, 200]:
        ax.axhline(yof(ppp), color="k", lw=0.4, alpha=0.35)
    ax.set_yticks([yof(x) for x in [1000, 900, 850, 800, 700, 600, 500, 400, 300, 200]])
    ax.set_yticklabels(["1000", "900", "850", "800", "700", "600", "500", "400", "300", "200"])
    ax.set_ylabel(r"$p$ / hPa（纵坐标 = $\ln(p_{00}/p)$）"); ax.set_xlabel("温度 / ℃")
    ax.set_ylim(yof(200), yof(1030))
    ax.legend(loc="lower left", fontsize=9); ax.grid(alpha=0.25)
    plt.tight_layout()
    out = os.path.join(FIGDIR, "ch19_tlnp.png")
    plt.savefig(out, dpi=150); plt.close()
    log("  图: %s" % out)


# ---------------------------------------------------------------- D
def part_D():
    """模式 T2（城市格点）与 ERA5 t2m 的日最高对比。"""
    if not os.path.exists(ERA5):
        log("D: 无 ERA5 子集，跳过")
        return
    from netCDF4 import Dataset
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    plt.rcParams["font.sans-serif"] = ["SimHei"]; plt.rcParams["axes.unicode_minus"] = False

    cases = [c for c in ["base0", "sf0", "sf1", "sf3"] if load_surf(c)]
    frc, lu = load_mask()
    urban = frc > 0.5

    # ---- ERA5：城市格点日最高 ----
    d = Dataset(ERA5)
    lat = np.asarray(d.variables["latitude"][:]); lon = np.asarray(d.variables["longitude"][:])
    t2m = np.asarray(d.variables["t2m"][:])          # (time, lat, lon) K
    vt = np.asarray(d.variables["valid_time"][:])
    d.close()
    jl = int(np.argmin(np.abs(lat - 36.0))); il = int(np.argmin(np.abs(lon - 103.75)))
    ts = t2m[:, jl, il] - 273.15
    import datetime as _dt
    days = np.array([_dt.datetime.utcfromtimestamp(int(t)).strftime("%m-%d") for t in vt])
    era_days, era_max = [], []
    for dd in ["07-12", "07-13", "07-14", "07-15", "07-16", "07-17"]:
        m = days == dd
        if m.any():
            era_days.append(dd); era_max.append(float(ts[m].max()))
    log("D: ERA5 城市格点日最高 = %s"
        % ", ".join("%s:%.1f" % (a, b) for a, b in zip(era_days, era_max)))

    # ---- 模式：城市格点平均的日最高 ----
    LAB = {"base0": "CTRL-A(=0,MYNN)", "sf1": "SLUCM(=1)", "sf0": "CTRL-B(=0,YSU)", "sf3": "BEP+BEM(=3)"}
    fig, axes = plt.subplots(1, 2, figsize=(13, 4.6))
    ax = axes[0]
    ax.plot(range(len(era_days)), era_max, "ko-", lw=2.0, label="ERA5（36.0N,103.75E）")
    for c in cases:
        dd = data_t2 = None
        sd = load_surf(c)
        t2 = sd["T2"][:, urban].mean(axis=1) - 273.15
        tt = sd["_times"]
        by_day = {}
        for k, t in enumerate(tt):
            by_day.setdefault(t[5:10], []).append(t2[k])
        xs, ys = [], []
        for n, dd in enumerate(era_days):
            if dd in by_day:
                xs.append(n); ys.append(max(by_day[dd]))
        ax.plot(xs, ys, "o--", lw=1.5, label=LAB[c])
        log("D: %s 城市格点日最高 = %s" % (LAB[c], ", ".join("%.1f" % y for y in ys)))
    ax.set_xticks(range(len(era_days))); ax.set_xticklabels(era_days)
    ax.set_ylabel("日最高 2 m 气温 (℃)"); ax.set_xlabel("日期（2025 年）")
    ax.set_title("(a) 日最高气温：模式（城市格点均值）vs ERA5", fontsize=11)
    ax.legend(fontsize=8); ax.grid(alpha=0.3)

    # ---- 7 月 15 日逐时对比（地方时） ----
    ax = axes[1]
    m = days == "07-15"
    hr = np.array([_dt.datetime.utcfromtimestamp(int(t)).hour for t in vt[m]]) + 7
    ax.plot(hr % 24, ts[m], "k-", lw=2.0, label="ERA5")
    for c in cases:
        sd = load_surf(c)
        t2 = sd["T2"][:, urban].mean(axis=1) - 273.15
        tt = sd["_times"]
        hh = np.array([int(t[11:13]) for t in tt]) + 7
        dd = np.array([t[5:10] for t in tt])
        k = np.where(dd == "07-15")[0]
        ax.plot(hh[k] % 24, t2[k], lw=1.4, label=LAB[c])
    ax.set_xlabel("地方时 (h)"); ax.set_ylabel("2 m 气温 (℃)")
    ax.set_title("(b) 2025-07-15 逐时气温（城市格点均值）", fontsize=11)
    ax.legend(fontsize=8); ax.grid(alpha=0.3)
    plt.tight_layout()
    out = os.path.join(FIGDIR, "ch19_t2_vs_era5.png")
    plt.savefig(out, dpi=150); plt.close()
    log("  图: %s" % out)


if __name__ == "__main__":
    log("=== ch19 诊断开始 ===")
    part_AB()
    part_C()
    part_D()
    log("=== 完成 ===")