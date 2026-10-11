# -*- coding: utf-8 -*-
"""
ch13_exercises.py —— 书第六章习题 1–8 数值解答（与 ch13_experiment.py 同口径）
输出：workspace/logs/ch13_exercises.log
"""
import os
import numpy as np

ROOT = r"d:\Code\Learn\WRF"
LOG = open(os.path.join(ROOT, "workspace", "logs", "ch13_exercises.log"), "w", encoding="utf-8")


def log(*a):
    s = " ".join(str(x) for x in a)
    print(s)
    LOG.write(s + "\n")


Rd, Rv, cpd, eps, g = 287.04, 461.6, 1004.0, 0.622, 9.81
kappa = Rd / cpd
psat, TTP = 610.78, 273.16
cpv, cliq, cice, hvap, hsub = 4 * Rv, 4190.0, 2106.0, 2.5e6, 2.85e6
XA = (cliq - cpv) / Rv
XB = XA + hvap / (Rv * TTP)
XAI = (cice - cpv) / Rv
XBI = XAI + hsub / (Rv * TTP)


def es_w(T):
    tr = TTP / T
    return psat * tr ** XA * np.exp(XB * (1 - tr))


def rs_w(T, p):
    e = np.minimum(es_w(T), 0.99 * np.asarray(p, dtype=float))
    return eps * e / (p - e)


def e_from_q(q, p):
    return q * p / (eps + q)


def t_from_es(es):
    """由饱和水汽压反解温度（Newton）"""
    T = TTP
    for _ in range(80):
        f = es_w(T) - es
        df = es_w(T) * (XA / T + XB * TTP / T / T)
        T = T - f / df
    return T


def Lv(T):
    return 2.5e6 - 2323.0 * (T - 273.15)


def desdT(T, Lv_=None):
    if Lv_ is None:
        Lv_ = Lv(T)
    return Lv_ * es_w(T) / (Rv * T * T)


def dTdlnp_moist(T, p):
    e = min(es_w(T), 0.99 * p)
    rs = eps * e / (p - e)
    num = Rd * T + Lv(T) * rs * p / (p - e)
    den = cpd + Lv(T) * eps * p * desdT(T) / (p - e) ** 2
    return num / den


def pseudo(T0, p0, p_end, n=800):
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
    return T * (1e5 / p) ** kappa


def theta_se(T, p):
    e = es_w(T)
    pd = max(p - e, 1.0)
    rs = eps * e / (p - e)
    return T * (1e5 / pd) ** kappa * np.exp(rs * Lv(T) / (cpd * T))


log("=" * 70)
log("ch13 习题数值解答（口径：WSM6 fpvs 式 es；Lv=2.5e6-2323t；Rd=287.04 cpd=1004）")
log("=" * 70)

# ---- 习题 1：p=950, t=5C, RH=60% ----
p1, T1 = 950e2, 278.15
es1 = es_w(T1)
e1 = 0.6 * es1
q1 = eps * e1 / (p1 - e1)
Td1 = t_from_es(e1)
th1 = theta(T1, p1)
tv1 = T1 * (1 + 0.608 * q1)
log("【习题 1】es(5C)=%.1f Pa, e=%.1f Pa, q=%.4f kg/kg (%.2f g/kg), Td=%.1f C, θ=%.1f C (%.1f K), Tv=%.2f K"
    % (es1, e1, q1, q1 * 1e3, Td1 - 273.15, th1 - 273.15, th1, tv1))

# ---- 习题 2：证明约定——数值核验 ----
for p_ in [1000e2, 900e2]:
    T_ = 290.0
    val = es_w(T_) ** 0.286 / T_
    log("【习题 2】核验 e^0.286/T：在 (290K, %d hPa) 处 = %.6f；沿干绝热到 800 hPa 后复算见下" % (p_ / 100, val))

# ---- 习题 3：p=1000, t=20C, q=5g/kg, 干绝热到 850 ----
p3, T3, q3 = 1000e2, 293.15, 5e-3
e3 = e_from_q(q3, p3)
RH3a = e3 / es_w(T3)
T3b = T3 * (850e2 / p3) ** kappa
e3b = e_from_q(q3, 850e2)
RH3b = e3b / es_w(T3b)
log("【习题 3】先：e=%.1f Pa, RH=%.1f%%；后：T=%.2f C, e=%.1f Pa, RH=%.1f%%（q 守恒）"
    % (e3, RH3a * 100, T3b - 273.15, e3b, RH3b * 100))

# ---- 习题 4：1000 hPa, t=25C, RH=80%, 降 5C ----
p4, T4 = 1000e2, 298.15
e4 = 0.8 * es_w(T4)
q4 = eps * e4 / (p4 - e4)
Td4 = t_from_es(e4)
T4b = 293.15
qs4b = rs_w(T4b, p4)
rho_air_b = p4 / (Rd * T4)
dw = (q4 - qs4b) * (p4 / (Rd * T4b))  # 按混合比差的近似
log("【习题 4】e=%.1f Pa, Td=%.1f C → 降到 20 C 低于露点：会成雾；凝结水量 ≈ %.2f g/m³（q 差法 %.4f kg/kg）"
    % (e4, Td4 - 273.15, dw * 1e3, q4 - qs4b))

# ---- 习题 5：q0=0.007 上升到 510 hPa 处 q=0.0025 ----
p5b = 510e2
e5b = e_from_q(0.0025, p5b)
T5b = t_from_es(e5b)
th5b = theta(T5b, p5b)
thse5b = theta_se(T5b, p5b)
# 求 LCL 态（Tc, pc）：qs(Tc,pc)=0.007 且 θse 守恒 = thse5b（二分）
def F5(pc):
    e_c = 0.007 * pc / (eps + 0.007)
    Tc = t_from_es(e_c)
    return theta_se(Tc, pc) - thse5b


lo5, hi5 = 1000e2, 500e2
if F5(lo5) * F5(hi5) < 0:
    for _ in range(200):
        mid = .5 * (lo5 + hi5)
        if F5(mid) < 0:
            lo5 = mid
        else:
            hi5 = mid
    pc5 = .5 * (lo5 + hi5)
    e_c5 = 0.007 * pc5 / (eps + 0.007)
    Tc5 = t_from_es(e_c5)
else:
    pc5, Tc5 = np.nan, np.nan
th5c = theta(Tc5, pc5)
log("【习题 5】510 hPa 处：T=%.1f C（es=%.1f Pa）, θ=%.1f K, θse=%.1f K" % (T5b - 273.15, e5b, th5b, thse5b))
log("         LCL 态：pc=%.0f hPa, Tc=%.1f C, θ(=未到凝结高度前的位温)=%.1f K, θse=%.1f K（守恒核对）"
    % (pc5 / 100, Tc5 - 273.15, th5c, theta_se(Tc5, pc5)))

# ---- 习题 6：950 hPa t=14C q=0.008，过山 700 hPa，70% 降水，背风 950 ----
p6a, T6a, q6a = 950e2, 287.15, 0.008
# 上坡：找 LCL
e6 = e_from_q(q6a, p6a)
Td6 = t_from_es(e6)
# 精确 LCL：干绝热上 rs=q6a
lo, hi = p6a, 200e2
for _ in range(200):
    mid = .5 * (lo + hi)
    Tm = T6a * (mid / p6a) ** kappa
    if rs_w(Tm, mid) > q6a:
        lo = mid
    else:
        hi = mid
p_lcl6 = .5 * (lo + hi)
Ts6, ps6 = pseudo(T6a * (p_lcl6 / p6a) ** kappa, p_lcl6, 700e2, n=600)
T6u = Ts6[-1]
qu = rs_w(T6u, 700e2)
C6 = q6a - qu                  # 凝结量
q_carry = 0.3 * C6             # 携带液态水
log("【习题 6】LCL %.1f hPa；山顶(700)：T=%.1f C, qs=%.4f, 凝结量 C=%.4f kg/kg；携水下坡（30C）"
    % (p_lcl6 / 100, T6u - 273.15, qu, C6))
# 下坡：先沿假绝热（保留液态水，缓慢蒸发），到 q=q0-0.7C 或到 950
Ts6d, ps6d = pseudo(T6u, 700e2, 950e2, n=600)  # 下行（lnp 增大）
qs_d = rs_w(Ts6d[-1], 950e2)
T6d = Ts6d[-1]
q_target = q6a - 0.7 * C6
log("        若按伪绝热下到 950：T=%.1f C, qs=%.4f；目标 q=%.4f" % (T6d - 273.15, qs_d, q_target))
if qs_d >= q_target:
    # 到 950 之前携带水已蒸发完 → 之后按干绝热下沉
    idx = int(np.argmin(np.abs(rs_w(Ts6d, ps6d) - q_target)))
    Tt, pt = Ts6d[idx], ps6d[idx]
    T6f = Tt * (950e2 / pt) ** kappa
    q6f = q_target
    log("        蒸发完于 %.0f hPa（T=%.1f C）后转干绝热" % (pt / 100, Tt - 273.15))
else:
    T6f, q6f = T6d, qs_d
th6f = theta(T6f, 950e2)
thse6f = theta_se(T6f, 950e2)
log("         背风 950 hPa：T=%.1f C, q=%.4f kg/kg, θ=%.1f K, θse=%.1f K"
    % (T6f - 273.15, q6f, th6f, thse6f))

# ---- 习题 7：探空表 ----
P7 = np.array([1000, 900, 850, 800, 700, 600, 500, 400, 300, 200]) * 1e2
T7 = np.array([23.0, 20.5, 17.0, 12.0, 4.5, -4.0, -12.1, -23.0, -32.5, -45.3]) + 273.15
TD7 = np.array([19.0, 10.4, 7.6, 6.8, -1.1, -8.5, -19.2, -29.5, -45.0, -59.5]) + 273.15
p900, T900, Td900 = 900e2, T7[1], TD7[1]
e900 = es_w(Td900)
q900 = eps * e900 / (p900 - e900)
qs900 = rs_w(T900, p900)
RH900 = e900 / es_w(T900)
log("【习题 7】(1) 900 hPa: q=%.2f g/kg, qs=%.2f g/kg, RH=%.1f%%" % (q900 * 1e3, qs900 * 1e3, RH900 * 100))
# (2) LCL/LFC
q0_7 = rs_w(TD7[0], P7[0])
lo, hi = P7[0], 200e2
for _ in range(300):
    mid = .5 * (lo + hi)
    Tm = T7[0] * (mid / P7[0]) ** kappa
    if rs_w(Tm, mid) > q0_7:
        lo = mid
    else:
        hi = mid
p_lcl7 = .5 * (lo + hi)
T_lcl7 = T7[0] * (p_lcl7 / P7[0]) ** kappa
log("        (2) LCL: %.1f hPa (T=%.2f C, q0=%.4f)" % (p_lcl7 / 100, T_lcl7 - 273.15, q0_7))
# CCL：q0 的等饱和比湿线（Tsat(p)）与环境温度层结交点（自下而上首次反号）
cc = None
pp = np.linspace(P7[0], P7[-1], 4000)
Tenv_pp = np.exp(np.interp(np.log(pp), np.log(P7[::-1]), np.log(T7[::-1])))
prev = None
for i in range(len(pp)):
    pc = pp[i]
    ec = e_from_q(q0_7, pc)
    Tcc = t_from_es(ec)
    d = Tcc - Tenv_pp[i]
    if prev is not None and prev < 0 <= d:
        cc = (pc, Tcc, Tenv_pp[i])
        break
    prev = d
if cc:
    pcc7, Tcc7, Tcc_env = cc
    Tconv = Tcc7 * (P7[0] / pcc7) ** kappa
    log("        CCL: %.1f hPa (Tsat=%.2f C ≈ 环境 T=%.2f C)；对流温度 Tconv（降到 1000 hPa）= %.1f C"
        % (pcc7 / 100, Tcc7 - 273.15, Tcc_env - 273.15, Tconv - 273.15))
# θe 实用口径（用实测比湿）：θe = θ exp(Lv q /(cpd T))
qe = []
for i in range(len(P7)):
    e_ = es_w(TD7[i])
    q_ = eps * e_ / (P7[i] - e_)
    qe.append(theta(T7[i], P7[i]) * np.exp(Lv(T7[i]) * q_ / (cpd * T7[i])))
log("        (4) θe(实测比湿口径, K): " + ", ".join("%.1f" % x for x in qe))
log("            900-1000: Δθe=%.2f K；800-850: Δθe=%.2f K（<0 对流性不稳定）"
    % (qe[1] - qe[0], qe[2] - qe[3]))

# ---- 习题 8：900 hPa 280K 饱和 → 700 hPa 速度 ----
T8, p8 = 280.0, 900e2
Ts8, ps8 = pseudo(T8, p8, 700e2, n=600)
Tenv8 = 280.0 * (ps8 / 900e2) ** kappa
z8 = np.zeros_like(ps8)
for i in range(1, len(ps8)):
    Tm = .5 * (Tenv8[i] + Tenv8[i - 1])
    z8[i] = z8[i - 1] - Rd * Tm / g * (np.log(ps8[i]) - np.log(ps8[i - 1]))
qs8 = rs_w(Ts8, ps8)
B1 = g * (Ts8 - Tenv8) / Tenv8
B2 = g * (Ts8 * (1 + 0.608 * qs8) - Tenv8) / (Tenv8 * (1 + 0.608 * qs8 * .5))
W1 = np.sqrt(2 * np.trapz(B1, z8))
W2 = np.sqrt(2 * np.trapz(B2, z8))
log("【习题 8】ΔT(700)=%.2f K；速度：未订正 %.1f m/s；虚温订正 %.1f m/s" % (Ts8[-1] - Tenv8[-1], W1, W2))

log("完成。")
LOG.close()