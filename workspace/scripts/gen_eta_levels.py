# -*- coding: utf-8 -*-
"""生成兰州教学个例的 50 层 eta_levels（低层加密，参照 liuyl17/haidian2024 风格）。

设计：
- 49 个 Δη 区间，从底(η=1.000)到顶(η=0.000)；
- 底部 Δη0 = 0.002（兰州 psfc≈850 hPa 时约 16 m），按比例因子 growth 递增；
- 中上部达到上限 cap 后保持等厚；
- 用二分法调整 cap 使 ΣΔη 恰为 1.0；
- 输出：eta 列表（50 个值，6 位小数）+ 各层近似厚度（按 psfc=850 hPa, ρ=1.0 kg/m^3 估算，仅供直觉）。
"""
import sys

N_LEV = 50
DELTA0 = 0.002
GROWTH = 1.12
PSFC = 85000.0   # Pa（兰州城区典型地面气压）
PTOP = 5000.0    # Pa（p_top_requested）
RHO = 1.0        # kg/m^3（近地面近似）
G = 9.81

def deltas(cap):
    d = []
    for i in range(N_LEV - 1):
        d.append(min(DELTA0 * GROWTH ** i, cap))
    return d

# 二分法求 cap 使总和为 1（注意：cap 越大、截断越少、总和 越大，单调递增）
lo, hi = 0.001, 0.5
for _ in range(200):
    mid = 0.5 * (lo + hi)
    s = sum(deltas(mid))
    if s > 1.0:
        hi = mid
    else:
        lo = mid
cap = 0.5 * (lo + hi)
d = deltas(cap)
# 由于 min 截断，微调最后一个区间使总和精确为 1
s = sum(d)
d[-1] += 1.0 - s
d[-1] = round(d[-1], 6)

etas = [1.0]
for dd in d[:-1]:
    etas.append(etas[-1] - dd)
etas.append(0.0)  # 顶层固定为 0.000000

print("cap =", round(cap, 6))
print("n_eta =", len(etas))
# 厚度估算
scale = (PSFC - PTOP) / (RHO * G)
print("scale (m per unit eta) ~", round(scale, 1))
ths = [dd * scale for dd in d]
print("first 8 layer dz (m):", [round(t, 1) for t in ths[:8]])
print("last 5 layer dz (m):", [round(t, 1) for t in ths[-5:]])

# 输出 eta 列表（每行 5 个，6 位小数）
lines = []
for i in range(0, N_LEV, 5):
    lines.append(", ".join("%.6f" % e for e in etas[i:i+5]) + ",")
print("\n".join(lines))

# 校验单调性
assert all(etas[i] > etas[i+1] for i in range(len(etas)-1)), "非单调!"
assert abs(sum(d) - 1.0) < 1e-6, "不均匀!"
print("monotone OK, sum OK")

out = r"d:\Code\Learn\WRF\workspace\cases\lanzhou2025\eta_levels_50.txt"
with open(out, "w", encoding="utf-8") as f:
    f.write("! 兰州教学个例 50 层 eta_levels（首层约 %.0f m，cap=%.4f）\n" % (ths[0], cap))
    for i in range(0, N_LEV, 5):
        f.write(", ".join("%.6f" % e for e in etas[i:i+5]) + ",\n")
print("written:", out)