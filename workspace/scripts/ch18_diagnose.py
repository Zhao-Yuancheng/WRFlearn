# -*- coding: utf-8 -*-
"""
ch18 理想算例诊断（轻轨）
环境: D:\\Code\\miniforge3\\envs\\WRFlearn\\python.exe
输入: workspace/data/ch18/<case>/wrfout_d01_*  （注意：frames_per_outfile 使同一文件含多帧）
输出: doc/figs/ch18_*.png；日志 workspace/logs/ch18_diagnose.log

用法:
  python ch18_diagnose.py probe     # 只探测变量/维度/帧数
  python ch18_diagnose.py           # 全量出图
"""
import os
import sys
import glob
import numpy as np

DATA = r"d:\Code\Learn\WRF\workspace\data\ch18"
LOGDIR = r"d:\Code\Learn\WRF\workspace\logs"
FIGDIR = r"d:\Code\Learn\WRF\doc\figs"
os.makedirs(LOGDIR, exist_ok=True)
os.makedirs(FIGDIR, exist_ok=True)
_logf = open(os.path.join(LOGDIR, "ch18_diagnose.log"), "w", encoding="utf-8")


def log(*a):
    s = " ".join(str(x) for x in a)
    print(s)
    _logf.write(s + "\n")
    _logf.flush()


def frame_index(case):
    """返回 [(path, time_index, label), ...]，按时间排序。"""
    from netCDF4 import Dataset
    out = []
    for f in sorted(glob.glob(os.path.join(DATA, case, "wrfout_d01_*"))):
        ds = Dataset(f)
        nt = len(ds.dimensions["Time"])
        for it in range(nt):
            lab = "".join(np.char.decode(ds.variables["Times"][it])).replace("_", " ")
            out.append((f, it, lab))
        ds.close()
    return out


def probe(case):
    from netCDF4 import Dataset
    fs = sorted(glob.glob(os.path.join(DATA, case, "wrfout_d01_*")))
    log("\n===== %s : %d 个文件 =====" % (case, len(fs)))
    if not fs:
        log("  (无文件)")
        return
    ds = Dataset(fs[0])
    log("  文件: %s" % os.path.basename(fs[0]))
    log("  维度: " + ", ".join("%s=%d" % (k, len(v)) for k, v in ds.dimensions.items()))
    log("  Times: %s" % ["".join(np.char.decode(ds.variables["Times"][i])) for i in range(len(ds.dimensions["Time"]))])
    for v in ["T2", "PSFC", "HFX", "LH", "T", "QVAPOR", "W", "U", "PH", "PHB", "P", "PB",
              "ZNU", "ZNW", "HGT", "RAINC", "RAINNC", "TSK", "QCLOUD", "QRAIN"]:
        if v in ds.variables:
            log("    %-9s %-18s %s" % (v, str(ds.variables[v].dimensions), str(ds.variables[v].shape)))
    log("  全局属性 START_DATE=%s" % ds.getncattr("START_DATE"))
    ds.close()


def main():
    if len(sys.argv) > 1 and sys.argv[1] == "probe":
        for c in ["em_les", "em_quarter_ss", "em_b_wave"]:
            probe(c)
        return

    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    from netCDF4 import Dataset

    plt.rcParams["font.sans-serif"] = ["SimHei"]
    plt.rcParams["axes.unicode_minus"] = False
    g0 = 9.81

    # ================== 1) em_les：CBL 廓线 ==================
    fr = frame_index("em_les")
    if fr:
        log("\n===== em_les：%d 帧 =====" % len(fr))
        th_c, z_c, labels, hfx = [], [], [], []
        for f, it, lab in fr:
            ds = Dataset(f)
            th = ds.variables["T"][it, :, :, :] + 300.0
            ph = ds.variables["PH"][it] + ds.variables["PHB"][it]
            zc = 0.5 * (ph[1:, :, :] + ph[:-1, :, :]) / g0
            th_c.append(th.mean(axis=(1, 2)))
            z_c.append(zc.mean(axis=(1, 2)))
            labels.append(lab[11:16])
            hfx.append(float(ds.variables["HFX"][it].mean()))
            ds.close()
        log("  帧标签: %s" % labels)
        log("  域平均 HFX: %s W/m2" % ["%.1f" % x for x in hfx])
        for th, z, lab in zip(th_c, z_c, labels):
            log("  %s: 近地 θ=%.2f K, CBL 顶(最大 dθ/dz)≈%.0f m" %
                (lab, th[0], z[int(np.argmax(np.gradient(th, z)))]))

        fig, axes = plt.subplots(1, 3, figsize=(14, 4.6))
        ax = axes[0]
        for th, z, lab in zip(th_c, z_c, labels):
            ax.plot(th, z, lw=1.9, label=lab)
        ax.set_xlabel(r"域平均位温 $\bar\theta$ (K)"); ax.set_ylabel("z (m)")
        ax.set_title("(a) 位温廓线：CBL 建立", fontsize=11); ax.legend(fontsize=9); ax.grid(alpha=0.3)
        ax = axes[1]
        for th, z, lab in zip(th_c, z_c, labels):
            ax.plot(np.gradient(th, z) * 1000.0, z, lw=1.9, label=lab)
        ax.axvline(0, color="gray", lw=0.8)
        ax.set_xlabel(r"$\partial\bar\theta/\partial z$ (K km$^{-1}$)"); ax.set_ylabel("z (m)")
        ax.set_title("(b) 层结：混合层近中性（书 6.8）", fontsize=11); ax.legend(fontsize=9); ax.grid(alpha=0.3)
        ax = axes[2]
        ax.bar(range(len(hfx)), hfx, color="C3", alpha=0.8)
        ax.set_xticks(range(len(hfx))); ax.set_xticklabels(labels)
        ax.set_ylabel(r"$H$ (W m$^{-2}$)"); ax.set_xlabel("输出时刻")
        ax.set_title("(c) 地表感热通量（tke_heat_flux 驱动）", fontsize=11); ax.grid(alpha=0.3, axis="y")
        plt.tight_layout()
        out = os.path.join(FIGDIR, "ch18_les_profiles.png")
        plt.savefig(out, dpi=150); plt.close()
        log("  图: %s" % out)
    else:
        log("\nem_les: 无数据")

    # ================== 2) em_quarter_ss：风暴强度 ==================
    # 注：本算例物理全关，PSFC/T2 等诊断量恒为 0（面层/陆面方案未调用），
    #     故改用动力学量（W、θ'）与微物理量（RAINNC）作诊断。
    fr = frame_index("em_quarter_ss")
    if fr:
        log("\n===== em_quarter_ss：%d 帧 =====" % len(fr))
        tt, wmax, thmin_sfc, rf, thmax = [], [], [], [], []
        for f, it, lab in fr:
            ds = Dataset(f)
            w = ds.variables["W"][it]
            th = ds.variables["T"][it]
            rain = ds.variables["RAINNC"][it]
            if "RAINC" in ds.variables:
                rain = rain + ds.variables["RAINC"][it]
            tt.append(lab[11:16])
            wmax.append(float(w.max()))
            thmin_sfc.append(float(th[0].min()))     # 最低模式层位温扰动最小 = 冷池
            thmax.append(float(th.max()))
            rf.append(float(rain.max()))
            ds.close()
        log("  帧: %s" % tt)
        log("  W   max (m/s)     : %s" % ["%.2f" % x for x in wmax])
        log("  θ' 最低层 min (K) : %s" % ["%.2f" % x for x in thmin_sfc])
        log("  θ' 全场 max (K)   : %s" % ["%.2f" % x for x in thmax])
        log("  RAIN max (mm)     : %s" % ["%.2f" % x for x in rf])
        log("  （PSFC/T2 在本算例恒为 0：物理全关时该诊断量不计算——教学点）")

        fig, axes = plt.subplots(1, 3, figsize=(14, 4.6))
        x = np.arange(len(tt))
        ax = axes[0]
        ax.plot(x, wmax, "o-", c="C3", lw=1.9)
        ax.set_xticks(x); ax.set_xticklabels(tt)
        ax.set_xlabel("输出时刻 (UTC)"); ax.set_ylabel("最大上升速度 (m/s)")
        ax.set_title("(a) 对流强度：$w_{max}$", fontsize=11); ax.grid(alpha=0.3)
        ax = axes[1]
        ax.plot(x, thmin_sfc, "o-", c="C0", lw=1.9)
        ax.set_xticks(x); ax.set_xticklabels(tt)
        ax.set_xlabel("输出时刻 (UTC)"); ax.set_ylabel(r"最低层 $\theta'$ 最小值 (K)")
        ax.set_title("(b) 冷池强度：近地位温亏损", fontsize=11); ax.grid(alpha=0.3)
        ax = axes[2]
        ax.plot(x, rf, "o-", c="C2", lw=1.9)
        ax.set_xticks(x); ax.set_xticklabels(tt)
        ax.set_xlabel("输出时刻 (UTC)"); ax.set_ylabel("累计降水最大值 (mm)")
        ax.set_title("(c) Kessler 微物理降水", fontsize=11); ax.grid(alpha=0.3)
        plt.tight_layout()
        out = os.path.join(FIGDIR, "ch18_qss_storm.png")
        plt.savefig(out, dpi=150); plt.close()
        log("  图: %s" % out)
    else:
        log("\nem_quarter_ss: 无数据")

    # ================== 3) em_b_wave：斜压波 ==================
    # 注：物理全关 → PSFC/T2 恒为 0；地面气压改用最低层 (P+PB)，扰动气压用最低层 P。
    fr = frame_index("em_b_wave")
    if fr:
        log("\n===== em_b_wave：%d 帧 =====" % len(fr))
        tt, psmin, psmax, pmin, pmax, umax = [], [], [], [], [], []
        for f, it, lab in fr:
            ds = Dataset(f)
            p = ds.variables["P"][it, 0] / 100.0
            pb = ds.variables["PB"][it, 0] / 100.0
            u = ds.variables["U"][it]
            tt.append(lab[5:16])
            pmin.append(float(p.min())); pmax.append(float(p.max()))
            psmin.append(float((p + pb).min())); psmax.append(float((p + pb).max()))
            umax.append(float(np.abs(u).max()))
            ds.close()
        log("  帧数: %d（首 %s → 末 %s，每 6 h）" % (len(tt), tt[0], tt[-1]))
        log("  地面 P' 扰动 min/max (hPa): ")
        for i in range(len(tt)):
            log("    %s  P'min=%+7.2f  P'max=%+7.2f  |u|max=%.1f" %
                (tt[i], pmin[i], pmax[i], umax[i]))
        log("  （PSFC/T2 恒为 0：物理全关时该诊断量不计算——与 quarter_ss 同）")

        fig, axes = plt.subplots(1, 2, figsize=(13, 4.6))
        x = np.arange(len(tt))
        ax = axes[0]
        ax.fill_between(x, pmin, pmax, color="C3", alpha=0.25)
        ax.plot(x, pmin, "v-", c="C3", lw=1.4, label="P' 最小（低压）")
        ax.plot(x, pmax, "^-", c="C0", lw=1.4, label="P' 最大（高压）")
        ax.axhline(0, color="gray", lw=0.8)
        ax.set_xlabel("输出帧序号（每 6 h）"); ax.set_ylabel(r"地面气压扰动 $P'$ (hPa)")
        ax.set_title("(a) 斜压波发展：地面气压扰动极值带", fontsize=11)
        ax.legend(fontsize=9); ax.grid(alpha=0.3)
        ax = axes[1]
        ax.plot(x, umax, "o-", c="C4", lw=1.7)
        ax.set_xlabel("输出帧序号（每 6 h）"); ax.set_ylabel("|u| 最大值 (m/s)")
        ax.set_title("(b) 急流：水平风极值", fontsize=11); ax.grid(alpha=0.3)
        plt.tight_layout()
        out = os.path.join(FIGDIR, "ch18_bwave.png")
        plt.savefig(out, dpi=150); plt.close()
        log("  图: %s" % out)
    else:
        log("\nem_b_wave: 无数据")

    log("\n完成。")


if __name__ == "__main__":
    main()