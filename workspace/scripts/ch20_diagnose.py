# -*- coding: utf-8 -*-
"""ch20 诊断（改造 WRF 三级实战）：

  L1：T2_PEAK 自检 —— 单调性 / 与逐时 T2 运行最大值的关系 / L1a(基线) 与 L1b(加诊断) 的逐位对照
  L2：MYNN PBLH 阈值三档（delt_thv = 1.25 / 0.5 / 2.5 K）—— PBLH 日循环 + Δ 空间图 + 判据方向核验
  L3：BEM 屋顶反照率 2D 化 —— 注入场核验 / 东(0.8)西(0.2)城区 TS_URB 四线对照 / 单变量证据（SWDOWN 不变）

输入：workspace/data/ch20/stage/{L1a,L1b,L2a,L2b,L3off,L3on}_{d01,d02}_2d.nc
输出：doc/figs/ch20_L1_diag.png / ch20_L2_pblh.png / ch20_L3_albedo.png
日志：workspace/logs/ch20_diagnose.log
环境：D:\\Code\\miniforge3\\envs\\WRFlearn\\python.exe
"""
import os
import sys
import numpy as np

STAGE = r"d:\Code\Learn\WRF\workspace\data\ch20\stage"
LOGDIR = r"d:\Code\Learn\WRF\workspace\logs"
FIGDIR = r"d:\Code\Learn\WRF\doc\figs"
os.makedirs(LOGDIR, exist_ok=True)
os.makedirs(FIGDIR, exist_ok=True)
_logf = open(os.path.join(LOGDIR, "ch20_diagnose.log"), "w", encoding="utf-8")


def log(*a):
    s = " ".join(str(x) for x in a)
    print(s)
    _logf.write(s + "\n")
    _logf.flush()


def _mp():
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    plt.rcParams["font.sans-serif"] = ["SimHei"]
    plt.rcParams["axes.unicode_minus"] = False
    return plt


def load2d(case, dom):
    """读 stage/<case>_<dom>_2d.nc（ncks 抽取：全部时次 + 2D 场 + Times）。"""
    from netCDF4 import Dataset
    f = os.path.join(STAGE, "%s_%s_2d.nc" % (case, dom))
    if not os.path.exists(f):
        return None
    d = Dataset(f)
    out = {}
    for k in d.variables:
        if k == "Times":
            continue
        out[k] = np.asarray(d.variables[k][:])
    if "Times" in d.variables:
        out["_times"] = ["".join(np.char.decode(x)) for x in d.variables["Times"][:]]
    else:
        out["_times"] = []
    out["_file"] = f
    d.close()
    return out


def hours_of(d):
    """Times 的钟点（整数小时），用于挑帧。"""
    return np.array([int(t[11:13]) for t in d["_times"]]) if d["_times"] else None


def frame_at(d, hour, day=None):
    h = hours_of(d)
    for k in range(len(h)):
        if h[k] == hour and (day is None or d["_times"][k][8:10] == day):
            return k
    return None


def maxdiff(a, b, keys):
    """逐变量最大绝对差 + 非零元个数（供"非扰动"类核验）。"""
    rows = []
    for k in keys:
        if k in a and k in b:
            d = np.abs(np.asarray(a[k], dtype=float) - np.asarray(b[k], dtype=float))
            rows.append((k, float(d.max()), int((d > 0).sum()), int(d.size)))
    return rows


# ================================================================= L1
def part_L1():
    plt = _mp()
    A = load2d("L1a", "d02")
    B = load2d("L1b", "d02")
    if A is None or B is None:
        log("L1: 缺 stage 数据（L1a/L1b），跳过")
        return
    log("L1: L1a=%s" % os.path.basename(A["_file"]))
    log("L1: L1b=%s" % os.path.basename(B["_file"]))
    tt = B["_times"]
    log("L1: 帧数=%d  首=%s 末=%s" % (len(tt), tt[0], tt[-1]))

    t2 = np.asarray(B["T2"], dtype=float)
    t2p = np.asarray(B["T2_PEAK"], dtype=float) if "T2_PEAK" in B else None
    if t2p is None:
        log("L1: L1b 输出中无 T2_PEAK —— 检查 Registry io 串（rhd）")
        return

    # --- 自检 1：单调不减（逐格点逐步） ---
    dt = np.diff(t2p, axis=0)
    n_neg = int((dt < -1e-6).sum())
    log("L1 自检①  单调性: 逐格点逐步差值最小 = %.6f K，负步数 = %d / %d" %
        (dt.min(), n_neg, dt.size))

    # --- 自检 2：T2_PEAK vs 逐时 T2 的运行最大值 ---
    rmax = np.maximum.accumulate(t2, axis=0)
    gap = t2p - rmax                      # 应 >= 0；差额来自输出间隔内的次小时峰值
    log("L1 自检②  T2_PEAK − 运行最大T2 : min=%.4f K  max=%.4f K  域均=%.4f K" %
        (gap.min(), gap.max(), gap.mean()))
    n_bad = int((gap < -1e-4).sum())
    log("L1 自检②  违例数（gap<-1e-4）= %d / %d" % (n_bad, gap.size))

    # --- 自检 3：L1a ↔ L1b 逐位对照 ---
    keys = ["T2", "PBLH", "TSK", "PSFC", "HFX", "LH", "QFX", "SWDOWN",
            "RAINC", "RAINNC", "U10", "V10"]
    rows = maxdiff(A, B, keys)
    for k, mx, nz, nn in rows:
        log("L1 对照  %-7s max|Δ|=%.6g  非零元 %d/%d" % (k, mx, nz, nn))

    # --- 图 ---
    fig, axes = plt.subplots(1, 3, figsize=(15.5, 4.4))
    ax = axes[0]
    x = np.arange(len(tt))
    ax.plot(x, t2p.mean(axis=(1, 2)), "C3-", lw=1.6, label=r"T2_PEAK（域均）")
    ax.plot(x, t2.mean(axis=(1, 2)), "C0--", lw=1.4, label=r"T2（域均，逐时）")
    ax.set_xlabel("模拟时间（小时，自 %s）" % tt[0]); ax.set_ylabel("K")
    ax.set_title("(a) 诊断变量 T2_PEAK 与 T2（d02）", fontsize=11)
    ax.legend(fontsize=8); ax.grid(alpha=0.3)

    ax = axes[1]
    ax.plot(x, gap.mean(axis=(1, 2)), "C2-", lw=1.5)
    ax.axhline(0, color="gray", lw=0.8)
    ax.set_xlabel("模拟时间（小时）"); ax.set_ylabel(r"$\langle$T2_PEAK − max$_{t'\leq t}$T2$\rangle$ (K)")
    ax.set_title("(b) 自检②：T2_PEAK 覆盖逐时峰的余量（≥0）", fontsize=11)
    ax.grid(alpha=0.3)

    ax = axes[2]
    lon = np.asarray(B["XLONG"][0]); lat = np.asarray(B["XLAT"][0])
    dT2 = np.asarray(B["T2"][-1], dtype=float) - np.asarray(A["T2"][-1], dtype=float)
    m = ax.pcolormesh(lon, lat, dT2, cmap="RdBu_r", vmin=-0.5, vmax=0.5, shading="auto")
    plt.colorbar(m, ax=ax, label=r"$\Delta T_2$ = L1b − L1a (K)", shrink=0.85)
    ax.set_xlabel("经度"); ax.set_ylabel("纬度")
    ax.set_title("(c) L1b−L1a 末帧 ΔT2（全零 = 加诊断不扰动物理）", fontsize=11)
    plt.tight_layout()
    out = os.path.join(FIGDIR, "ch20_L1_diag.png")
    plt.savefig(out, dpi=150); plt.close()
    log("L1 图: %s" % out)


# ================================================================= L2
def part_L2():
    plt = _mp()
    B = load2d("L1b", "d02")   # delt_thv = 1.25（默认，含 T2_PEAK）
    A = load2d("L2a", "d02")   # = 0.5
    C = load2d("L2b", "d02")   # = 2.5
    if B is None or A is None or C is None:
        log("L2: 缺 stage 数据（L1b/L2a/L2b），跳过")
        return
    tt = B["_times"]
    log("L2: 帧数=%d 首=%s 末=%s" % (len(tt), tt[0], tt[-1]))
    pb = {k: np.asarray(v["PBLH"], dtype=float) for k, v in
          [("1.25", B), ("0.5", A), ("2.5", C)]}
    t2 = {k: np.asarray(v["T2"], dtype=float) for k, v in
          [("1.25", B), ("0.5", A), ("2.5", C)]}

    # --- 判据方向核验：PBLH(大Δ) ≥ PBLH(小Δ) 逐点 ---
    v1 = pb["2.5"] - pb["1.25"]
    v2 = pb["1.25"] - pb["0.5"]
    log("L2 核验  逐点 PBLH(2.5)−PBLH(1.25): min=%.2f m  负值点 %d/%d（%.3f%%）" %
        (v1.min(), int((v1 < -1e-6).sum()), v1.size, 100.0 * (v1 < -1e-6).sum() / v1.size))
    log("L2 核验  逐点 PBLH(1.25)−PBLH(0.5): min=%.2f m  负值点 %d/%d（%.3f%%）" %
        (v2.min(), int((v2 < -1e-6).sum()), v2.size, 100.0 * (v2 < -1e-6).sum() / v2.size))

    # --- 日循环 ---
    x = np.arange(len(tt))
    pm = {k: pb[k].mean(axis=(1, 2)) for k in pb}
    log("L2 域均 PBLH（日最大）: 1.25→%.1f m  0.5→%.1f m  2.5→%.1f m" %
        (pm["1.25"].max(), pm["0.5"].max(), pm["2.5"].max()))
    log("L2 域均 PBLH（时均）  : 1.25→%.1f m  0.5→%.1f m  2.5→%.1f m" %
        (pm["1.25"].mean(), pm["0.5"].mean(), pm["2.5"].mean()))
    for k in ["0.5", "2.5"]:
        dt2 = t2[k].mean(axis=(1, 2)) - t2["1.25"].mean(axis=(1, 2))
        log("L2 ΔT2 域均（%s − 1.25）: min=%.3f K max=%.3f K 时均=%.3f K" %
            (k, dt2.min(), dt2.max(), dt2.mean()))

    k14 = frame_at(B, 14) or (len(tt) // 2)
    lon = np.asarray(B["XLONG"][0]); lat = np.asarray(B["XLAT"][0])

    fig, axes = plt.subplots(2, 2, figsize=(12.2, 8.4))
    ax = axes[0, 0]
    for k, c, lab in [("0.5", "C0", r"$\Delta\theta_v$=0.5 K"), ("1.25", "C1", r"1.25 K（默认）"),
                      ("2.5", "C3", r"2.5 K")]:
        ax.plot(x, pm[k], lw=1.6, color=c, label=lab)
    ax.set_xlabel("模拟时间（小时，自 %s）" % tt[0]); ax.set_ylabel("PBLH (m)")
    ax.set_title("(a) 域均 PBLH 日循环（d02，三档阈值）", fontsize=11)
    ax.legend(fontsize=8); ax.grid(alpha=0.3)

    ax = axes[0, 1]
    for k, c in [("0.5", "C0"), ("2.5", "C3")]:
        dt2 = t2[k].mean(axis=(1, 2)) - t2["1.25"].mean(axis=(1, 2))
        ax.plot(x, dt2, lw=1.6, color=c, label=r"$\Delta T_2$（%s − 1.25）" % k)
    ax.axhline(0, color="gray", lw=0.8)
    ax.set_xlabel("模拟时间（小时）"); ax.set_ylabel(r"$\Delta T_2$ (K)")
    ax.set_title("(b) 2 m 气温的响应（域均）", fontsize=11)
    ax.legend(fontsize=8); ax.grid(alpha=0.3)

    for ax, k, ttl in [(axes[1, 0], "0.5", r"(c) $\Delta$PBLH = (0.5 K) − (1.25 K)，%s 时"),
                       (axes[1, 1], "2.5", r"(d) $\Delta$PBLH = (2.5 K) − (1.25 K)，%s 时")]:
        diff = pb[k][k14] - pb["1.25"][k14]
        vmax = float(np.abs(diff).max()) or 1.0
        m = ax.pcolormesh(lon, lat, diff, cmap="RdBu_r", vmin=-vmax, vmax=vmax, shading="auto")
        plt.colorbar(m, ax=ax, label=r"$\Delta$PBLH (m)", shrink=0.85)
        ax.set_xlabel("经度"); ax.set_ylabel("纬度")
        ax.set_title(ttl % tt[k14][11:16], fontsize=11)
        log("L2 ΔPBLH 图（%s，帧%d %s）: min=%.1f m max=%.1f m" %
            (k, k14, tt[k14], diff.min(), diff.max()))
    plt.tight_layout()
    out = os.path.join(FIGDIR, "ch20_L2_pblh.png")
    plt.savefig(out, dpi=150); plt.close()
    log("L2 图: %s" % out)


# ================================================================= L3
def part_L3():
    plt = _mp()
    off = load2d("L3off", "d02")
    on = load2d("L3on", "d02")
    if off is None or on is None:
        log("L3: 缺 stage 数据（L3off/L3on），跳过")
        return
    tt = on["_times"]
    log("L3: 帧数=%d 首=%s 末=%s（d02，30 min 间隔）" % (len(tt), tt[0], tt[-1]))

    alb = np.asarray(off["ALBROF_2D"], dtype=float)
    a0 = alb[0]
    east = a0 >= 0.5
    west = (a0 > 0) & (a0 < 0.5)
    zero = a0 <= 0
    log("L3 注入场核验（ALBROF_2D，首帧）：东(高反照率) %d 格  西(低反照率) %d 格  其余 %d 格" %
        (int(east.sum()), int(west.sum()), int(zero.sum())))
    log("L3 注入值：东均值=%.3f  西均值=%.3f  其余最大=%.3f" %
        (a0[east].mean() if east.any() else -1, a0[west].mean() if west.any() else -1,
         a0[zero].max() if zero.any() else -1))
    # on / off 输入场应完全一致（同一 wrfinput）
    log("L3 输入一致性：L3on 与 L3off 的 ALBROF_2D max|Δ|=%.6g" %
        np.abs(np.asarray(on["ALBROF_2D"], dtype=float) - alb).max())

    tsu = {("off", "east"): np.asarray(off["TS_URB"], dtype=float)[:, east].mean(axis=1),
           ("off", "west"): np.asarray(off["TS_URB"], dtype=float)[:, west].mean(axis=1),
           ("on", "east"): np.asarray(on["TS_URB"], dtype=float)[:, east].mean(axis=1),
           ("on", "west"): np.asarray(on["TS_URB"], dtype=float)[:, west].mean(axis=1)}
    for k in [("on", "east"), ("on", "west"), ("off", "east"), ("off", "west")]:
        s = tsu[k]
        log("L3 TS_URB[%s/%s]: min=%.2f max=%.2f 时均=%.2f K" % (k[0], k[1], s.min(), s.max(), s.mean()))
    dE = tsu[("on", "east")] - tsu[("off", "east")]
    dW = tsu[("on", "west")] - tsu[("off", "west")]
    log("L3 ΔTS_URB（开−关）: 东 时均=%.3f K（min %.3f / max %.3f）  西 时均=%.3f K（min %.3f / max %.3f）" %
        (dE.mean(), dE.min(), dE.max(), dW.mean(), dW.min(), dW.max()))
    # 单变量证据（分级）：西组 = 表值 0.20 的严格对照，东组 = 处理
    fe = np.asarray(on["TS_URB"], dtype=float) - np.asarray(off["TS_URB"], dtype=float)
    log("L3 逐格 max|ΔTS_URB|: 东=%.3f K  西=%.3f K  全域=%.3f K" %
        (np.abs(fe[:, east]).max(), np.abs(fe[:, west]).max(), np.abs(fe).max()))
    sw = np.abs(np.asarray(on["SWDOWN"], dtype=float) - np.asarray(off["SWDOWN"], dtype=float))
    log("L3 逐格 max|ΔSWDOWN|: 全域=%.6g  东 %.6g / 西 %.6g（辐射输入不因开关而变）" %
        (sw.max(), sw[:, east].max(), sw[:, west].max()))

    # 单变量证据：辐射输入（SWDOWN）不变，只动地表能量平衡
    rows = maxdiff(off, on, ["SWDOWN", "PBLH", "U10", "V10", "PSFC", "RAINC", "RAINNC", "T2", "TSK"])
    for k, mx, nz, nn in rows:
        log("L3 对照  %-7s max|Δ|=%.6g  非零元 %d/%d" % (k, mx, nz, nn))

    k12 = frame_at(on, 6) or frame_at(on, 12) or (len(tt) - 1)   # 06 UTC = 13 LT（白天峰）
    lon = np.asarray(on["XLONG"][0]); lat = np.asarray(on["XLAT"][0])

    fig, axes = plt.subplots(2, 2, figsize=(12.4, 8.6))
    ax = axes[0, 0]
    m = ax.pcolormesh(lon, lat, a0, cmap="magma", vmin=0, vmax=0.9, shading="auto")
    plt.colorbar(m, ax=ax, label="ALBROF_2D（屋顶反照率）", shrink=0.85)
    ax.set_xlabel("经度"); ax.set_ylabel("纬度")
    ax.set_title("(a) 注入的 2D 屋顶反照率场（东 %.1f / 西 %.1f）" %
                 (a0[east].mean() if east.any() else 0, a0[west].mean() if west.any() else 0), fontsize=11)

    ax = axes[0, 1]
    x = np.arange(len(tt))
    ax.plot(x, tsu[("off", "east")], "C3--", lw=1.5, label="东城区 关")
    ax.plot(x, tsu[("on", "east")], "C3-", lw=1.8, label="东城区 开")
    ax.plot(x, tsu[("off", "west")], "C0--", lw=1.5, label="西城区 关")
    ax.plot(x, tsu[("on", "west")], "C0-", lw=1.8, label="西城区 开")
    ax.set_xlabel("模拟时间（小时，自 %s）" % tt[0]); ax.set_ylabel("TS_URB (K)")
    ax.set_title("(b) 城市表皮温度：开关 × 东西城区", fontsize=11)
    ax.legend(fontsize=8); ax.grid(alpha=0.3)

    ax = axes[1, 0]
    diff = np.asarray(on["TS_URB"][k12], dtype=float) - np.asarray(off["TS_URB"][k12], dtype=float)
    vmax = float(np.abs(diff).max()) or 0.1
    m = ax.pcolormesh(lon, lat, diff, cmap="RdBu_r", vmin=-vmax, vmax=vmax, shading="auto")
    plt.colorbar(m, ax=ax, label=r"$\Delta$TS_URB (K)", shrink=0.85)
    ax.set_xlabel("经度"); ax.set_ylabel("纬度")
    ax.set_title("(c) ΔTS_URB（开−关），%s" % tt[k12][11:16], fontsize=11)
    log("L3 ΔTS_URB 图（帧%d %s）: min=%.2f max=%.2f K" % (k12, tt[k12], diff.min(), diff.max()))

    ax = axes[1, 1]
    names = ["SWDOWN", "PBLH", "T2", "TSK"]
    vals = [dict((k, mx) for k, mx, _, _ in rows).get(n, np.nan) for n in names]
    key_tsu = float(np.abs(np.asarray(on["TS_URB"], dtype=float) -
                           np.asarray(off["TS_URB"], dtype=float)).max())
    names.append("TS_URB"); vals.append(key_tsu)
    ax.bar(np.arange(len(names)), vals, color=["C7"] * 4 + ["C3"])
    ax.set_yscale("symlog", linthresh=1e-3)
    ax.set_xticks(np.arange(len(names))); ax.set_xticklabels(names, fontsize=9)
    ax.set_ylabel("max|Δ|（开 − 关，symlog）")
    ax.set_title("(d) 单变量证据：辐射输入不变、目标量变", fontsize=11)
    for i, v in enumerate(vals):
        ax.annotate("%.3g" % v, (i, v), ha="center", va="bottom", fontsize=8)
    ax.grid(alpha=0.3, axis="y")
    plt.tight_layout()
    out = os.path.join(FIGDIR, "ch20_L3_albedo.png")
    plt.savefig(out, dpi=150); plt.close()
    log("L3 图: %s" % out)


if __name__ == "__main__":
    want = sys.argv[1] if len(sys.argv) > 1 else "ALL"
    log("===== ch20 diagnose start（%s）=====" % want)
    if want in ("ALL", "L1"):
        part_L1()
    if want in ("ALL", "L2"):
        part_L2()
    if want in ("ALL", "L3"):
        part_L3()
    log("===== ch20 diagnose done =====")
