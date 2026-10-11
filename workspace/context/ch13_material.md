# ch13 素材底稿（微物理族）——写作时引用

> 生成 2026-10-10（自主会话）。书页换算：印刷页 N → book\page_{N+14:04d}.jpg。
> 第六章范围（目录实读 page_0009）：6.1 p123；6.2 p134；6.3 p138；6.4 p142；6.5 p147；6.6 p149；6.7 p150；6.8 p154；6.9 p164；6.10 p167；思考题 p168；习题 p169；第七章 p170。
> **ch13 用 6.1–6.7**（方案 v2 §3.4 定 6.1–6.5 为主，6.6/6.7 作微物理衔接）；6.8–6.10 留给 ch14。
> 写作状态：书侧已直读 p123–153 + p168–169；**PPT 未到 → 考点节先按书自拟，标注"待 PPT 校准"**。

## 1. 书第 6 章公式清单（编号已实读核对；页码为印刷页）

### 6.1 应用于大气的热力学基本规律（p123–134）

**6.1.1 预备知识（p123–124）**
- 宇宙三大系统分类：未饱和湿空气系统（二元单相系）、含液态水/冰的饱和湿空气系统（多元多相系）
- 开放系/封闭系约定；准静态过程、准静力条件 (6.1.1)：p ≡ pe 且 dp/dz = ∂pe/∂z
- 气块（微团）模型三条假定（均匀、绝热、准静力）

**6.1.2 热力学第一定律（p124–125）**
- (6.1.2) dU = δQ − pdV
- (6.1.3) δQ = cv dT + p dα
- (6.1.4) δQ = (cv + R)dT − α dp = cp dT − RT dp/p
- (6.1.5) δQ = cp dT − α dp = cp dT − (1/ρ)dp ← 大气中第一定律基本形式

**6.1.3 热力学第二定律和态函数（p125–128）**
- (6.1.6) S − S0 = ∫(x0→x) δQ/T（熵差态函数）
- (6.1.7) S − S0 ≥ ∫ δQ/T（第二定律普遍表述）
- (6.1.8) dS ≥ δQ/T；(6.1.9) dS = δQ/T
- (6.1.10) TdS ≥ δQ = dU + pdV；(6.1.11) dU ≤ TdS − pdV
- 焓 H = U + pV：(6.1.12) dH ≤ TdS + Vdp；(6.1.13) cp = (∂Q/∂T)p = (∂H/∂T)p
- 吉布斯函数 G = H − TS = U + pV − TS：(6.1.14) dG ≤ −SdT + Vdp；(6.1.15) dG ≤ 0（等温等压方向判据）
- (6.1.16) dU = δQ + δA′ − pdV（一般形式，δA′ 为其他形式功——汽液相变表面能）
- (6.1.17) dU = TdS − pdV（热力学基本微分方程）
- (6.1.18) dH = TdS + Vdp；(6.1.19) dF = −SdT − pdV（自由能 F = U − TS）；(6.1.20) dG = −SdT + Vdp
- (6.1.21) (∂S/∂p)T = −(∂V/∂T)p（麦克斯韦关系之一；另 3 个从略）
- (6.1.22) ds = (∂s/∂T)p dT + (∂s/∂p)T dp；(6.1.23) dh 同形
- (6.1.24) ds = (1/T)(∂h/∂T)p dT + (1/T)[(∂h/∂p)T − α]dp
- (6.1.25) (∂h/∂T)p = cp；(6.1.26) (∂s/∂T)p = cp/T；(6.1.27) (∂h/∂p)T = α − T(∂α/∂T)p
- (6.1.28) ds = (cp/T)dT − (∂α/∂T)p dp = cp dlnT − αβp dp，βp = (1/α)(∂α/∂T)p（定压膨胀系数）
- (6.1.29) dh = cp dT + α(1 − Tβp)dp
- 未饱和湿空气（理想气体）：(6.1.30) ds = cp dlnT − R dlnp；(6.1.31) dh = cp dT
- (6.1.32) s = cp lnT − R lnp + 常数；(6.1.33) h = cp T + 常数

**6.1.4 含液态水的饱和湿空气系统（p128–132）**
- (6.1.34) L = (u2 − u1) + p(α2 − α1) = h2 − h1（相变潜热=比焓差）
- (6.1.35) μ = u + pα − Ts（化学势）；(6.1.36) dμ = −s dT + α dp
- (6.1.37) 相平衡条件：T1 = T2 = T；p1 = p2 = p；μ1(T,p) = μ2(T,p)（热平衡+力学平衡+相变平衡）
- (6.1.38) dp/dT = (s2 − s1)/(α2 − α1)（相平衡曲线斜率）
- (6.1.39) s2 − s1 = L/T
- (6.1.40a) dp/dT = L/[T(α2 − α1)]；(6.1.40b) dp/dT = Lv/(Tα2)（α1≪α2）
- → 与第二章 (2.2.6) 连接：des/dT = Lv es/(Rv T²)（克拉珀龙-克劳修斯方程，平液面适用；云滴/雨滴需考虑曲率影响 → ch12 前已在 ch11 Kelvin 公式处处理）
- (6.1.41a) dL/dT = cp2 − cp1 + L/T − [(∂α2/∂T) − (∂α1/∂T)]·L/(α2−α1)；(6.1.41b) dLv/dT = cpv − cw（**基尔霍夫方程**）
- (6.1.42) Lv = 2.5×10⁶ − 2323 t（J/kg，t 摄氏温度）；dLv/dT = −2323
- (6.1.43) dX = (∂X/∂T)p,m dT + (∂X/∂p)T,m dp + (xs − xw)dmw（含相变的全微分）
- (6.1.44) ds = (∂s/∂T)p,m dT + (∂s/∂p)T,m dp + (ss − sw)dmw
- (6.1.45) ds = (md cpd + ms cw)dlnT − md Rd dlnpd + d(ms Lv/T)（含液态水饱和湿空气熵）※ ms 记适应复核：书用"水质物"记法，写教材时再查对 p130–131 原页
- (6.1.46) (cpd + rt cw)dlnT − Rd dlnpd + d(rs Lv/T) = 0（等熵过程表达式；6.3 节基础）
- (6.1.47)–(6.1.49) 焓全微分与偏导：(6.1.48) (∂hd/∂T)=cpd、(∂hv/∂T)=cpv；(6.1.49) (∂hd/∂p)T=(∂hv/∂p)T=0
- (6.1.50) dh = (md cpd + ms cpv + mw cw)dT + Lv dmv
- (6.1.51) h = (md cpd + ms cw)T + mv Lv(T) + 常数（积分形式）
- (6.1.52) dh ≈ cp dT + Lv dq（近似式，等压过程常用）

**6.1.5 大气中的能量（p132–134）**
- (6.1.53) Tρ = T (1 + r/ε)/(1 + rt)（**密度温度**，Emanuel 1994）；rt 为水质物总混合比
- (6.1.54) α = (Va + Vw + Vi)/(md + mv + mw + mi)（比容，含凝物）
- (6.1.55) α ≈ αd/(1 + rt)；(6.1.56) α = Rd Tρ/p ⇔ p = ρ Rd Tρ
- (6.1.57) u = cv T（比内能）
- (6.1.58) U = ∫ cv T ρ dz = (cv/g)∫ p dz（单位截面气柱总内能）
- (6.1.59) Φ ≈ gz（位势）；(6.1.60) dΦ/dt ≈ gw
- (6.1.61) Ep = ∫ρgz dz = (R/g)∫ T dp；(6.1.62) Ep ≈ 0.40 U
- (6.1.63) Ek = ½(u²+v²+w²) = ½V²
- (6.1.64) EL = L q（潜热能）；(6.1.65) h = cp T（显热）；(6.1.66) cpT = cvT + RT（内能+压力能）
- (6.1.67) hm = cp T + L q（温湿能）
- (6.1.68) Φd = cpT + gz（干静力能/蒙哥马利势）；(6.1.69) Φm = cpT + gz + Lq（湿静力能）
- (6.1.70) U + Ep = (1/g)∫ cp T dp（总势能，与内能成正比）
- (6.1.71) Ed = cpT + gz + ½V²（干空气总能量）；(6.1.72) Em = cpT + gz + ½V² + Lq（湿空气总能量）
- 全势能中约 5% 转动能（有效势能）

### 6.2 大气中的干绝热过程（p134–137）
- 干绝热过程 = 未饱和湿空气无相变绝热升降（可逆）
- (6.2.1) dT = (RT/cp)(dp/p)（绝热中温度变化完全由气压变化决定）
- (6.2.2) T/T0 = (p/p0)^κ（泊松方程）；κ = R/cp = κd(1+0.608q)/(1+0.86q)
- (6.2.3) κ ≈ κd = 0.286；(6.2.4) T/T0 = (p/p0)^0.286

**6.2.1 干绝热减温率（p135）**
- (6.2.5) γ = −dT/dz = (ρe/ρ)(g/cp)(Te/Tv)（一般式，环境/气块密度比）
- (6.2.6) γ = g/[cpd(1 + 0.86q)]（未饱和湿空气）
- (6.2.7) γd = g/cpd = 9.76 K/km ≈ 9.8 K/km；位势米口径 γd = g0/cpd = 9.76 K/gpkm

**6.2.2 位温（p135–136）**
- (6.2.8) θ = T(p00/p)^κ = T(1000/p)^κ（位温定义）
- (6.2.9) θ = T(1000/p)^0.286（θd − θ ≲ 0.1 K，未饱和湿空气位温常以干空气位温代替）
- (6.2.10) θv = Tv(1000/p)^κ（虚位温）；(6.2.11) θv = θ(1 + 0.608q)
- (6.2.12) dlnθ = dlnT − κ dlnp
- (6.2.13) ds = cp dlnθ；(6.2.14) δQ = cp T dθ/θ = cp T dlnθ
- **结论：干绝热过程是等熵过程，位温守恒**（保守性 → 示踪气块）
- (6.2.15a) ∂θ/∂z = (θ/T)(γ − Γ) ≈ (θ/T)(γd − Γ)；(6.2.15b) ∂lnθ/∂z = (1/T)(γ − Γ)
- (6.2.16) ∂θv/∂z ≈ (θv/Tv)(γd − Γv)

**6.2.3 干绝热上升时的露点变化和抬升凝结高度（p137）**
- (6.2.17) dTd/dz = (dTd/de)(de/dz)（露点随高度的变化 = 水汽压变化 + 露点-水汽压关系）
- (6.2.18) de/dTd = Lv e/(Rv Td²)（用克拉珀龙-克劳修斯）
- (6.2.19) (1/e)(de/dz) = (1/p)(dp/dz)（干绝热中水汽混合比守恒 → 水汽压变化随气压）
- (6.2.20) dTd/dz = −(g Rd Td²)/(Lv Rv Te) ≈ −6.3×10⁻⁶ Td²/Tv；Tv=288K、Td=280K → −0.0017 K/m（露点递减率 ~1.7 K/km）
- (6.2.21) T(z) = T0 − 0.98×10⁻²(z − z0)  （γd≈9.8 K/km）
- (6.2.22) Td(z) = Td0 − 0.17×10⁻²(z − z0)
- (6.2.23) zc ≈ 123 (T0 − Td0)（米，T 摄氏）——**抬升凝结高度 LCL 估算；对流云底高度**

### 6.3 可逆的饱和绝热过程和假绝热过程（p138–141）
- 图 6.1 可逆饱和绝热 vs 假绝热过程（凝结物保留 vs 立即降落）
- (6.3.1) (cpd + rs cw)dlnT − Rd dlnpd + d(rs Lv/T) ≈ 0（假绝热，rw=0）
- (6.3.2) cpd dlnT − Rd dlnpd + d(rs Lv/T) ≈ 0（简化，rs cw ≪ cpd）
- (6.3.3) cpd dT − Rd T dlnpd + Lv drs ≈ 0（**饱和气块上升热量方程**：显热/膨胀功/潜热三项）
- 6.3.1 湿绝热减温率
  - (6.3.4) dT/dz = (1/cpd)[(Rd T/p)(dp/dz) − Lv (drs/dz)]
  - (6.3.5) γs = −dT/dz = γd · [1 + Lv rs/(Rd T)] / [1 + Lv² rs/(cpd Rd T²)]
  - (6.3.6) γs = γd + (Lv/cpd)(drs/dz)（因 drs/dz ≤ 0 → γs ≤ γd）
  - 数值：对流层下部暖湿气层 γs 平均 4℃/km；干冷层 6–7℃/km，近干绝热
- 6.3.2 假相当位温
  - (6.3.7) ds ≈ cpd dlnT − Rd dlnpd + d(rs Lv/T)
  - (6.3.8) θse = θd exp(rs Lv/(cpd T))（**假相当位温定义**）
  - (6.3.9) θd = T(1000/pd)^(Rd/cpd)（湿空气中干空气位温）
  - (6.3.10) ds ≈ cpd dlnθse； (6.3.11) s ≈ cpd lnθse + 积分常量
  - (6.3.12) ∂θse/∂z ≈ (θ/T)(γs − Γ)（Γ=γs 时 θse 守恒）
  - (6.3.13) θe = θ exp(Lv qs/(cp T))（欧美习惯"相当位温"，与 θse 类似）
  - **保守性总结：假相当位温在干、湿绝热过程中都保守** → 气团/锋面分析；未饱和气块先干绝热到饱和再用 (6.3.8) 计算，全过程保持
  - 图 6.2 全球年均温度/位温/相当位温纬向剖面（Peixoto & Oort 1992）
- 6.3.3 焚风（p141 + 图 6.3 原理示意图；焚风定义与实例）

### 6.4 大气热力学图解（p142–146）
- 图解四要求：坐标可测；纵坐标~高度、各线近直线；尺度便于分辨过程；面积=能量
- 6.4.1 温度对数压力图解（埃玛图 Emagram，参考姜达雍 1959）
  - (6.4.1) x = T 或 Td（横坐标）；(6.4.2) y = ln(p00/p) = ln(1000/p)（纵坐标）
  - (6.4.3) y = (1/κd)(lnθ − lnx)（干绝热线=等位温线方程，对数曲线族）
  - (6.4.4) y = 4098(1/(x − 36) − 1/(T0 − 36))（等饱和比湿线，由 (2.2.12b)+(2.2.9a) 积分）
  - (6.4.5) a = ∮(RdT − αdp) = −∮αdp = Rd∮T dln(p00/p) = Rd σ′（**图上面积=循环功**）
  - 1 cm² ≈ 74.5 J/kg（现用埃玛图）
  - 图 6.4 埃玛图略图（干绝热/湿绝热/等比湿线三族）
- 6.4.2 应用（p144–145）
  - 绘大气层结曲线（T 与 Td 折线）
  - (6.4.6) Zgd − Zgl = (Rd/g0)∫Tv dln(p00/p) = (Rd T̄v/g0)ln(p1/p2)（等压面厚度，图 6.5 面积法等温）
  - 绘气块路径曲线（状态曲线；图 6.6：干绝热上升→LCL→湿绝热）
- 6.4.3 斜 T-lnp 图（p145）：(6.4.7) y = ln(p00/p)；(6.4.8) x = T + Cy = T + C ln(1000/p)（C 常数→等温线右倾直线；T-lnp 的 45° 修正；图 6.7）
- 6.4.4 温熵图（p145–146）：x = T（或 Td），y = lnθ；干绝热线=等位温线（与等温线 90°）；等压线对数曲线；缺饱和比湿线；美英常用
- 6.4.5 能量图解一般原理（p146，参考 Iribarne 1981）：dσ′ = J dσ，(6.4.9)(6.4.10) 雅可比行列式 J；J=常数 → 面积=功（能量图，顺时针正）
  - 例题 6.1（p147）：埃玛图雅可比 J = −1/R（"−"表示与 p-α 图面积符号相反，逆时针为正）；温熵图 J = −1/cp

### 6.5 绝热混合过程（p147–149）
- 6.5.1 绝热等压混合（水平混合）：ΔH = m1Δh1 + m2Δh2 = 0
  - (6.5.1) T = [m1T1 + m2T2 + 0.86(m1q1T1 + m2q2T2)] / [m(1 + 0.86q̄)]
  - (6.5.2) q̄ = (m1q1 + m2q2)/m；(6.5.3) T ≈ (m1T1 + m2T2)/m
  - (6.5.4) ē ≈ (m1e1 + m2e2)/m；(6.5.5) θ̄ ≈ (m1θ1 + m2θ2)/m
  - 位温加权平均 → 等位温混合即热量平衡；图 6.10 有凝结时的水平混合 → 凝结/混合雾（蒸汽雾、喷气机尾迹、开水壶）
- 6.5.2 不同高度空气的绝热混合（垂直混合）：三阶段（各自绝热移到 p → 等压混合 → 各自绝热回到原高度）
  - 混合后 θ、q 为质量加权平均；回到原气压后 T1(p1)、T2(p2) 与参考压强无关
  - 注意：不能用 (6.5.3)(6.5.4) 直接算垂直混合温度/水汽压
- 6.5.3 湍流混合层（p148–149）
  - (6.5.6) θ̄ ≈ ∫θdm/m = ∫ρθdz/∫ρdz = −∫θdp/(p1−p2)（整层湍流混合后平均位温）
  - (6.5.7) T(p) = θ̄(p/1000)^κd（混合层温度层结趋于干绝热减温率）
  - 图 6.11 湍流混合层示意（逆温层形成）；图 6.12 近地面气层湍流混合（非绝热变化）
  - 逆温层（绝对稳定）→ 其上水汽经湍流向上输送 → 高湿层 → 凝结成云

### 6.6 等压冷却过程（p149–150）
- 等压冷却达饱和→凝结（夜间辐射冷却→露/霜；平流冷却→平流雾；辐射冷却→辐射雾）
- (6.6.1) δQ = dh ≈ cp dT + Lv dqs（等压冷却焓增量）
- (6.6.2) dqs ≈ d(εes/p) = (ε/p)des = (ε/p)(Lv es/(Rv T²))dT
- (6.6.3) δQ = [cp + εLv²es/(p Rv T²)]dT
- (6.6.4) δQ ≈ [cp Rv T²/(Lv es) + εLv/p]des
- (6.6.5) dρw = −dρv = −(1/Rv)d(es/T) = −(1/Rv)(des/T − es dT/T²)
- (6.6.6) dρw = −(1/(Rv T))es(Lv/(Rv T) − 1)dT
- (6.6.7) dρw ≈ −des/(Rv T)（T=300K，Lv/(RvT)≈20）
- (6.6.8) δQ = −[cp Rv T²/(Lv es) + εLv/p]dρw
- 雾滴含水量与能见度；同样降温幅度下，高温湿空气凝结出更多水量 → 浓雾多出现在暖湿天气

### 6.7 温湿参量（p150–153）
- 6.7.1 相当温度和湿球温度
  - (6.7.1) T + Lv r/cpd ≈ T′ + Lv r′/cpd（等压绝热凝结过程显热↔潜热转换）
  - (6.7.2) cpd T + Lv r ≈ cpd T′ + Lv r′
  - (6.7.3) Te = T + Lv r/cpd = T + ΔT（**相当温度**/等压相当温度，可有过最高温；ΔT = 2490 r，273K 附近 Lv=2.5×10⁶、cpd=1004）
  - θe = Te(1000/p)^0.286（等压相当位温，少用）
  - (6.7.4) T + Lv r/cpd ≈ Tw + Lv rs(Tw)/cpd（**湿球温度** Tw，需迭代；Tw 为等压绝热蒸发达饱和温度）
  - (6.7.5) e = es(Tw) − (cpd p/(ε Lv))(T − Tw) = es(Tw) − Ap(T − Tw)（干湿球测湿公式，A ≈ 6.2×10⁻⁴；A = (1/εLv)(κ/D)，κ 热扩散率、D 水汽扩散系数）
- 6.7.2 假湿球温度和假湿球位温（p152）：图 6.13；Tsw（沿干绝热到 LCL 再沿假绝热回原气压）比 Tw 小但差 ≤0.5℃；θsw = 假湿球位温（降到 1000 hPa）；两者在干/湿绝热过程中保守
- 6.7.3 假相当位温和假相当温度（p153）：θse 定义重述（(=6.3.8)）；(6.7.6) Tse = θse(p/1000)^0.286（**假相当温度**）；图 6.14；θse 与 θsw 全过程保守
  - 关系（图 6.15）：Tsw < Tw < T < Te < Tse；θsw < θ < θse（写教材时再核 p153 原句）

### 思考题（p168–169，全 7 题）
1. 若地球大气由氧组成，则干绝热减温率仍是 9.8 K/km 吗？为什么？（提示：氧的摩尔定容热 Cv = 21.06 J/(mol·K)）
2. 分析一个空气块在绝热（干绝热、饱和绝热和假绝热）的升降过程中哪些量是保守的？哪些变大？哪些变小？
3. 云团（含凝结水滴的饱和气块）在绝热下沉过程中，其温度、压强、比湿、露点、相对湿度、位温及假相当位温将如何变化？
4. 证明：埃玛图上每条干绝热线的位温 θ 和括号内的位温 θ′（与括号内气压值相对应）有 θ′ = Cθ，此处 C = p/p′（同一条等压线上压强 p 与括号内压强 p′ 之比）。（注意：现用埃玛图 κ = 0.288）
5. 根据饱和比湿 qs = 0.622 es/p，能否利用埃玛图估计饱和水汽压？（提示：考虑 p = 622 hPa 时 es 与 qs 数值的关系）
6. 假如以绝热气块模型作为积云的原始模型，分析云内温度、上升气流速度和含水量的垂直分布特点。
7. 什么情况下可用抬升凝结高度估算对流云云底高度？什么情况下可用对流凝结高度估算云底高度？自由对流高度有什么物理意义？

### 习题（p169，全 8 题）
1. 已知 p = 950 hPa，T = 5℃，Uw = 60%，用埃玛图求比湿、露点、虚温和位温。
2. 若 e 为水汽压，证明干绝热上升时 e^0.286 T⁻¹ 之值不变。
3. 设一团湿空气 p = 1000 hPa，t = 20℃，q = 5 g/kg，经干绝热过程升至 850 hPa。问：上升前后相对湿度各为多少？
4. 设某地气压 1000 hPa，气温 t = 25℃，相对湿度 80%。若日落后气温降低 5℃，问：是否会产生雾？雾的含水量是多少？
5. 空气微团比湿 q = 0.007，上升到凝结高度以后继续升到 510 hPa，比湿为 0.0025。求未到凝结高度前及在 510 hPa 处的位温。
6. 气流 p = 950 hPa 时 t = 14℃，q = 0.008，遇山坡抬升，山顶压强 700 hPa，过山后下沉。若凝结水分 70% 在爬坡途中降落，求背风面 950 hPa 处气流的温度、比湿、位温、假相当位温。
7. 探空记录表（p 1000/900/850/800/700/600/500/400/300/200 hPa；t 23.0/20.5/17.0/12.0/4.5/−4.0/−12.1/−23.0/−32.5/−45.3℃；td 19.0/10.4/7.6/6.8/−1.1/−8.5/−19.2/−29.5/−45.0/−59.5℃）：
   (1) 求 900 hPa 处比湿、饱和比湿、相对湿度；
   (2) 标出 LCL、CCL、LFC 高度，分析地面气块绝热上升时不稳定能量垂直分布，确定大气层稳定度；
   (3) 当天最高气温达多少度才有可能出现热雷雨？
   (4) 判断 900–1000 hPa 及 800–850 hPa 是否对流性不稳定？
8. 环境垂直减温率=干绝热，气块在 900 hPa、T=280K、已饱和，做绝热位移得正浮力连续上升。忽略空气阻力与凝结水，按未作/作虚温订正两种情形分别计算气块在 700 hPa 处的速度。

### 参考文献（p169 原列，教材写作时可择要）
姜达雍 1959（气象常用热力学图解）；齐瑛 1993（中尺度山地气候动力学）；王永生 1987（大气物理学）；汪志诚（热力学·统计物理）；Eagleman 1985；Emanuel 1994；Iribarne & Godson 1981；Peixoto & Oort 1992；吴国雄刘还珠译（气候物理学）；Wallace & Hobbs 1977（王鹏飞译，大气科学概观）。

## 2. 源码锚点笔记（写作时扩充）

### module_microphysics_driver.F（phys/）
- `micro_select: SELECT CASE(mp_physics)` 位于文件后部（约 1008 行处），先处理无微物理（mp=0）与各方案分支
- CASE 家族实读（部分）：KESSLERSCHEME、THOMPSONAERO、THOMPSONGH、THOMPSON、TEMPO、MORR_TWO_MOMENT、P3_1CATEGORY/NC、P3_2CATEGORY……（后续补全清单）
- **CASE (THOMPSON) 传参实录**：QV/QC/QR/QI/QS/QG、NI=qni_curr、NR=qnr_curr、TH、PII、P、W、DZ、DT_IN、ITIMESTEP、RAINNC(V)、SNOWNC(V)、GRAUPELNC(V)、SR、REFL_10CM、diagflag、ke_diag、do_radar_ref、re_cloud/re_ice/re_snow、has_reqc/has_reqi/has_reqs（**无 nc/nwfa —— mp=8）**
- CASE (THOMPSONAERO)：含产量的多扰动 perturb 逻辑（pert_thom/multi_perturb）；传参含 qnc/qnwfa 等（写教材时精读 1146–1250 块）

### module_mp_thompson.F（phys/）
- 结构：MODULE → 声明常数区（~48–420）→ CONTAINS → thompson_init（424）→ mp_gt_driver（1070–~5250）→ GAMMCF（5257）/GSER（5293）→ RSLF（5383）/RSIF（5418）→ calc_effectRad（5594–5699）
- 头部注释（1–42）：方案历史（Reisner→Thompson et al. 2008 Part II；v3.1 起双矩雨滴；v3.6 起 aerosol-aware；mp=8 一矩云水 vs mp=28 双矩云滴数；v4.4 三矩 graupel/hail；作者 Greg Thompson NCAR-RAL）
- 常数区要点（教材可引用）：
  - 密度：rho_w=1000、rho_s=100、rho_i=890、rho_g 9 档 50–800（idx_bg1=5 用于 mp=8/28）
  - 云滴谱：Nt_c = 100×10⁶ m⁻³（海洋）/ 300×10⁶（大陆）；Nt_c_max = 1999×10⁶
  - CCN/IN 背景气溶胶：naIN0=1.5E6、naIN1=0.5E6；naCCN0=300E6、naCCN1=50E6；naBC0=150E6、naBC1=25E6（陆/海）
  - 粒子谱 N(D) = N0 D^μ exp(−λD)：μ_r=μ_g=μ_i=0；雪=双伽马（Field et al. 2005）：μ_s=0.6357、Kap0=490.6、Kap1=17.46、Lam0=20.78、Lam1=3.29
  - 质量幂律 m = am D^bm：am_r=πρw/6、bm_r=3；am_s=0.069、bm_s=2；am_g=πρg/6、bm_g=3；am_i=πρi/6、bm_i=3
  - 落速 v = av D^bv exp(−fv D)：雨 Ferrier 1994（av_r=4854、bv_r=1、fv_r=195）；雪（av_s=40、bv_s=0.55、fv_s=100）；graupel 按密度档 av_g/bv_g 数组（Heymsfield Best-Reynolds）；冰 av_i=1493.9、bv_i=1；云滴 av_c=0.316946E8、bv_c=2
  - 容量（capacitance）：C_cube=0.5（球/柱）、C_sqrd=0.15（片/聚合）
  - 收集效率：Ef_si=0.05、Ef_rs=0.95、Ef_rg=0.75、Ef_ri=0.95（Ef_rw/Ef_sw/Ef_gw 与斯托克斯数相关，运行时计算）
  - 最小阈值：R1=1.E-12（数浓度下限）、R2=1.E-6、eps=1.E-15
  - **Cooper 曲线（冰晶数浓度）**：TNO=5.0、ATO=0.304（即 N_i = 5·exp(0.304·(273.15−T))·1000？写教材时精读使用处）
  - rho_not = 101325/(287.05×298)（密度订正），Sc=0.632（施密特数），HGFR=235.16 K（均质冻结温度）
  - 常数：Rv=461.5、R=287.04、Cp=1004.0；k_b、M_w、M_a、N_avo、ma_w、ar_volume（0.025 μm 半径气溶胶体积）
  - 潜热：lsub=2.834E6、lvap0=2.5E6、lfus = lsub − lvap0；xm0i=1.E-12 kg（冰初生质量）
  - 最小直径：D0c=1E-6、D0r=50E-6、D0s=300E-6、D0g=350E-6
  - 查找表维度：nbins=100（各类）；ntb_c=37、ntb_i=64、ntb_r/s/g=37、ntb_i1=55、ntb_t=9、ntb_IN=55、ntb_arc=7（ta_Na 10–10000）、ntb_arw=9（ta_Ww 0.01–100 cm/s）、ntb_art=7（ta_Tk 243.15–303.15K）、ntb_arr=5（ta_Ra 0.01–0.16 μm）、ntb_ark=4（ta_Ka 0.2–0.8）
  - 表内容：r_c 1E-6→1E-2 kg/m³（37 档）；r_i 1E-10→1E-3（64 档）；r_r/r_s/r_g 1E-6→1E-2；N0r_exp 1E6→1E10（37 档）；N0g_exp 1E2→1E6（37 档）；Nt_i 1→1E6；Nt_IN 1→1E6
  - 雪矩换算（Field 2005）：sa/sb 各 10 个系数（5.065339, −0.062659, −3.032362, 0.029469, −0.000285, 0.31255, 0.000204, 0.003199, 0, −0.015952；sb 类似）
  - Tc 表（−0.01 至 −40，5℃ 间隔，ntb_t=9）
  - 大查找表族（allocatable）：tcg_racg、tmr_racg、tcr_gacr、tnr_racg、tnr_gacr、tcs_racs1/2、tmr_racs1/2、tcr_sacr1/2、tms_sacr1/2、tnr_racs1/2、tnr_sacr1/2、tpi_qcfz、tni_qcfz、tpi_qrfz、tpg_qrfz、tni_qrfz、tnr_qrfz、tps_iaus、tni_iaus、tpi_ide、t_Efrw、t_Efsw、tnr_rev、tpc_wev、tnc_wev（R8）；tnccn_act（R4）
  - 伽马函数族：cce/ccg(5,15)、cie/cig(7)、cre/crg(13)、cse/csg(17)、cge/cgg(12,NRHG) + 倒数/半幂系列
  - 预计算速率常数：t1_qr_qc、t1_qr_qi、t2_qr_qi、t1_qg_qc、t1_qs_qc、t1_qs_qi、t1_qr_ev、t2_qr_ev、t1_qs_sd、t2_qs_sd、t1_qg_sd、t2_qg_sd、t1_qs_me、t2_qs_me、t1_qg_me、t2_qg_me
- mp_gt_driver 实参（1070–1147）：qv,qc,qr,qi,qs,qg,ni,nr（INOUT，ims:ime×kms:kme）；TH；可选 nc,nwfa,nifa,nbca,qb,ng + nwfa2d/nifa2d/nbca2d + aer_init_opt/wif_input_opt；pii,p,w,dz（IN）；dt_in；itimestep；RAINNC/RAINNCV/SR（INOUT）；SNOWNC(V)、GRAUPELNC(V)（可选）；refl_10cm；re_cloud/re_ice/re_snow（INOUT）+ has_reqc/has_reqi/has_reqs；tile 维度四组
- **有效半径分支（mp_gt_driver 内 ~1460–1480）**：逐列初始化 re_qc1d=RE_QC_BG、re_qi1d=RE_QI_BG、re_qs1d=RE_QS_BG（module_model_constants 来的背景值）→ call calc_effectRad(...)→ re_cloud=MAX(RE_QC_BG, MIN(re_qc1d, 50.E-6))、re_ice 上限 125E-6、re_snow 上限 999E-6 ← **ch12 留下的 effectRad/has_reqc 接口在此闭环**
- RSLF/RSIF（5383–5444）：饱和混合比函数（.622*ESL/(P−ESL)；RSIF 用 max(1.e-4,(P−ESI))）；ESL/ESI 多项式系数在 5340–5382（写教材时读）
- calc_effectRad（5594–5699）：re_qc1d=MAX(2.51E-6, MIN(0.5(3+inu_c)/lamc, 50E-6))；re_qi1d 用 (3+mu_i)/lami，帽 125E-6；re_qs1d=MAX(5.01E-6, MIN(0.5*(smoc/smob), 999E-6))（雪矩比）
- 待精读：饱和调整段（~2858 注释"If ice supersaturated, ensure sum of depos growth terms..."）；冰核化/Cooper 曲线使用处；均质冻结（HGFR）；冻结/融化/沉积/蒸发计算节；雨滴蒸发；落地通量（pcp_*）；refl_10cm 雷达反射率诊断（module_mp_radar）

### Registry.EM_COMMON（mp_physics 方案号表，实读）
- rconfig：`mp_physics namelist,physics max_domains −1`（默认 −1）
- package 表（号=方案）：
  - 0 passiveqv；1 kesslerscheme；2 linscheme；3 wsm3scheme；4 wsm5scheme；5 fer_mp_hires；6 wsm6scheme；7 nuwrf4icescheme；8 **thompson**（moist qv,qc,qr,qi,qs,qg；scalar qni,qnr；state re_cloud,re_ice,re_snow）；9 milbrandt2mom；10 morr_two_moment；11 cammgmpscheme；13 sbu_ylinscheme；14 wdm5scheme；15 fer_mp_hires_advect；16 wdm6scheme；18 nssl_2mom；24 wsm7scheme；26 wdm7scheme；27 udmscheme；28 **thompsonaero**（scalar qni,qnr,qnc,qnwfa,qnifa,qnbca；state 加 qnwfa2d,qnifa2d,taod5503d,taod5502d）；29 rcon_mp_scheme；38 thompsongh；40 morr_tm_aero；50/51/52/53 **P3 族**（p3_1category、_nc、p3_2category、p3_1cat_3mom）；55 jensen_ishmael；56 ntu；88 tempo；95 etampnew；96 madwrf_mp；97 gsfcgcescheme；106 wsm6rscheme
  - 注：17/19/21/22 deprecated 保留占位
- 其他相关 rconfig：force_read_thompson、write_thompson_tables（默认 .true.）、write_thompson_mp38table（默认 .false.）、mp_physics_dfi

### WSM6 对照（待读）
- 文件：phys/module_mp_wsm6.F 与 phys/physics_mmm/mp_wsm6.F90 + mp_wsm6_effectRad.F90；wrftladj/ 下另有 TL/AD 版本（module_mp_wsm6r_ad/tl）——写教材时核实际编译用哪个

## 3. 实验设计（轻轨，本地 python）

- 目标①：位温/虚位温/相当位温/假相当位温数值复现（书 (6.2.8)(6.2.11)(6.7.3)(6.3.8)），并与 WRF 个例输出对照（wrfrst/wrfout 的 T、P、QVAPOR、THETA 等）
- 目标②：饱和调整（saturation adjustment）数值实验：给定 (T,q)，沿假绝热方程 (6.3.3) 迭代求凝结后 (T′,qv′)，对齐 Thompson 的 satadj 实现思路（写教材时以源码为准）
- 目标③：T-lnP 图原理计算（干绝热线/湿绝热线族绘制；用书习题 7 探空表画层结曲线 + LCL/LFC 判定）
- 数据：workspace\data\（兰州个例 met_em/wrfinput/wrfrst；写教材时清理数据清单）
- 出图：doc/figs/ch13_*.png（干绝热线族 / θse 剖面 / 饱和调整收敛）

## 4. 考点自拟（PPT 未到，先按书要点；到货后补"考点透视"并校准）

待写作时从 6.1–6.7 划：①名词（位温/虚温/密度温度/相当温度/湿球温度/假湿球/假相当位温/湿绝热减温率/LCL/焚风）②简答（保守性对比、焚风原理、混合过程）③计算（位温/θse/(6.2.23)/混合式）④模式视角补题（饱和调整对应哪个方程；微物理方案里哪些量守恒；θse 为什么可用于气团分析）。

## 5. 核验清单（状态）

- [x] (6.1.45)(6.1.46) 记号复核（p130–131）：(6.1.46) = (cpd + rt·cw)dlnT − Rd·dlnpd + d(rs·Lv/T) = 0；rt = rv + rw（总水质物混合比）、rs 饱和混合比；ms 为水质物（水汽+液态水）总质量
- [x] 图 6.15 关系原句（p153）：Tsw < Tw < T < Te < Tse；θsw < θ < θse
- [x] (6.3.5) 分母含 ε：γs = γd·[1+Lv·rs/(Rd·T)]/[1+ε·Lv²·rs/(cpd·Rd·T²)]；数值积分逐点吻合（0.1–1%），**非勘误**（ε/Rd ≡ 1/Rv 为等价写法）
- [x] README.namelist mp_physics 表（0–106 全表已录，见 §6.6）
- [ ] 8 实用编译方案集与差异表印证（写作时并入 13.8 差异表；ch13 精读 Thompson/WSM6 为主）

## 6. 源码精读补记（第二轮，2026-10-10）

### 6.1 Thompson 饱和调整（3411 行上下，核心对照点）
- 触发条件：`(ssatw(k) > eps) .or. (ssatw(k) < −eps .and. L_qc(k))`（只调过饱和/有云水的欠饱和）
- 初值：`clap = (qv − qvs)/(1 + lvt2·qvs)`；**3 次 Newton 迭代**：`fcd = qvs·exp(lvt2·clap) − qv + clap`；`dfcd = qvs·lvt2·exp(lvt2·clap) + 1`；`clap −= fcd/dfcd`
- 其中 `lvt2 = lvap²·ocp/(Rv·T²)`，`ocp = 1/(Cp·(1+0.887·qv))`（湿空气订正热容），`lvap = lvap0 + (2106−4218)·(T−273.15)`（即 slope −2112）
- 数学实质：解 qs(T)·exp(lvt2·ΔT) = qv − Δq（qs 的克劳修斯-克拉珀龙指数线性化）——即书 (6.6.2)/(6.6.3) 线性化 + 牛顿迭代
- 结果写入：`prw_vcd = clap·odt`；`qvten −= prw_vcd`；`qcten += prw_vcd`；**`tten += lvap·ocp·prw_vcd`**（3479–3483 行）
- 液滴核化（同段）：气溶胶感知时 `activ_ncloud(temp,w1d,nwfa)`，否则常数 Nt_c；蒸发用查表 `tpc_wev/tnc_wev`（Dc_star 单步可蒸发最大半径 + 小于 Dc_star 的显式滴数，3423–3469）

### 6.2 Thompson 冰核化三来源（2559–2642，专栏素材）
- 冻结：Bigg 1953（雨滴→霰/冰：tpg_qrfz/tpi_qrfz/tni_qrfz/tnr_qrfz 查表；云水冻结 tpi_qcfz/tni_qcfz；idx_IN 由气溶胶数定档，dustyIce=.false. 时用 1.0/L 默认）
- 均质冻结：T < HGFR(=235.16 K) 直接冻结（雨 2601–2604、云水 2613–2616 行）
- 沉积核化：条件 `ssati ≥ 0.25 .or. (ssatw > eps .and. T < 253.15K)`；气溶胶感知用 DeMott et al.(2010)（`iceDeMott(tempc,qvs,qvsi,rho,nifa)`），否则 **Cooper 1986：xnc = MIN(250.E3, 5.0·exp(0.304·(273.15−T)))**（TNO=5.0, ATO=0.304，上限 250 个/L）
- 气溶胶均质冻结：Koop et al.(2001, Nature)：`is_aerosol_aware .and. homogIce .and. xni ≤ 999E3 .and. T<238K .and. ssati ≥ 0.4` → `iceKoop(...)`
- 冰初生质量 xm0i = 1.E-12 kg；`pri_inu = xm0i·pni_inu`（质量-数浓度耦合）
- 冰→雪自动转化（2665–2678）：xDi > 5·D0s 或 idx_i 顶档 → 99% 质量入雪（tps_iaus/tni_iaus 查表）；xDi < 0.1·D0s → 0
- 冰沉积/升华（Srivastava & Coen 1992）：`pri_ide = C_cube·t1_subl·diffu·ssati·rvs·oig1·cig(5)·ni·ilami`

### 6.3 Thompson 守恒约束与倾向装配（2853–3104）
- 五物种逐一限幅："Ensure we do not deplete more hydrometeor species than exists"：冰沉积总量 ≤ (qv−qvsi)（过饱和时）/ ≥（欠饱和时），云水/云冰/雨/雪/霰各以 `rate_max = −qx·odt` 比例缩放；随后再强制成对项质量守恒（pri_ihm = prs_ihm+prg_ihm；prr_rcg = −prg_rcg 等）
- 倾向装配 + 尺寸/数浓度硬约束：云水质量加权平均直径 1–50 μm、Nt_c_max=1999×10⁶ m⁻³；云冰 5–300 μm、≤999/L；雨滴中值体积直径 37 μm–2.5 mm；霰/雹按 rhog 分档（is_hail_aware，否则恒 idx_bg1=5）
- 温度倾向（3163–3181）：T<0℃：lsub 系数用于凝华/升华/沉积项、lfus2=lsub−lvap 用于冻结/淞附项；T≥0℃：lfus 用于融化、lsub 用于升华项
- 更新后重算：温度、密度、`qvs=rslf(pres,T)`、`ssatw=qv/qvs−1`、扩散率 diffu=2.11E-5·(T/273.15)^1.94·(101325/p)、粘度 visco（分段）、`lvap(T)`、热导 tcond、`ocp`、`lvt2`

### 6.4 有效半径接口（承 ch12；闭环点）
- mp_gt_driver 内逐列：初始化 re_qc1d=RE_QC_BG、re_qi1d=RE_QI_BG、re_qs1d=RE_QS_BG → `call calc_effectRad` → `re_cloud = MAX(RE_QC_BG, MIN(re_qc1d, 50.E-6))`；re_ice 帽 125E-6；re_snow 帽 999E-6
- `calc_effectRad`（5594–5699）：云滴 re = ½(3+νc)/λc（下限 2.51E-6）；云冰 ½(3+μi)/λi；雪 ½·smoc/smob（Field 双伽马矩比），下限 5.01E-6
- 常数（module_model_constants）：RE_QC_BG=2.49E-6、RE_QI_BG=4.99E-6、RE_QS_BG=9.99E-6 m；RE_QC_MAX=50E-6、RE_QI_MAX=125E-6

### 6.5 WSM6 结构（对照对象）
- **双层结构**：`phys/module_mp_wsm6.F` 是薄适配层（`module module_mp_wsm6; use mp_wsm6, only: mp_wsm6_run, refl10cm_wsm6; use mp_wsm6_effectrad, ...`），实体在 `phys/physics_mmm/mp_wsm6.F90`（+ `mp_wsm6_effectRad.F90`）；wrftladj/ 另有 TL/AD 版
- 实体组成：mp_wsm6_init（73–189）、mp_wsm6_run（213–1468）、rgmma（1471）、fpvs（1497）、slope_wsm6/slope_rain/slope_snow/slope_graup（1525/1605/1651/1702）、nislfv_rain_plm 与 plm6（1751/1997，雨/雪的 PLM 平流下沉）、refl10cm_wsm6（2275）
- 句函数（418–431）：`cpmcal(x)=cpd(1−q)+q·cpv`；`xlcal(x)=xlv0−xlv1·(x−t0c)`，**xlv1 = cliq − cpv = 2343.6**；diffus=8.794e-5·x^1.81/y；viscos=1.496e-6·x^1.5/(x+120)/y；xka=1.414e3·viscos·y；`conden(a,b,c,d,e) = (max(b,qmin)−c)/(1 + d²/(rv·e)·c/a²)`
- 饱和调整（1389–1437）：内联 fpvs → `qsat(i,k,1)`（水面）与 `qsat(i,k,2)`（冰/水面分支）；`pcond = conden(T,q,qsat(1),xl,cpm)`，限幅 [−qc/dt, q/dt]；`q −= pcond·dt; qc += pcond·dt; T += pcond·xl/cpm·dt`——**单步解析式（非迭代）**
- fpvs（1497–1522）：es = psat·(ttp/T)^xa·exp(xb·(1−ttp/T))；xa=(cliq−cpv)/rv=5.077、xb=xa+hvap/(rv·ttp)=24.904；冰面 xai=(cice−cpv)/rv=0.562、xbi=23.165（CC 积分式，与 ch11 的 SVP 家族互证）
- 常数：psat=610.78 Pa、cliq=4190、cice=2106、cpv=4·rv=1846.4、r_v=461.6、XLV=2.5E6、XLS=2.85E6（module_model_constants；`XLV1=2370` 仅供 Kessler 族旧的线性化）
- 驱动调用实录（CASE (WSM6SCHEME)）：`wsm6(TH,Q,QC,QR,QI,QS,QG,DEN,PII,P,DELZ,DELT,G,CPD=cp,CPV=cpv,RD=r_d,RV=r_v,T0C=svpt0,EP1,EP2,QMIN,XLS=xls,XLV0=xlv,XLF0=xlf,DEN0=rhoair0,DENR=rhowater,CLIQ,CICE,PSAT,RAIN...,re_*...)`——**常数全部经接口显式传入**（与 Thompson 用模块内部常数形成对照）

### 6.6 mp_physics 方案号表（README.namelist 权威版，与 Registry package 对齐）
0 无；1 Kessler；2 Lin；3 WSM3；4 WSM5；5 Ferrier(HRW)；6 WSM6；7 Goddard 4-ice；8 Thompson；9 Milbrandt-Yau 2-mom；10 Morrison 2-mom；11 CAM5.1；13 SBU-YLin；14 WDM5；16 WDM6；17/19/21/22 旧 NSSL 占位；18 NSSL 2-mom；24 WSM7（雪雹分列）；26 WDM7；27 UDM；28 Thompson aerosol-aware（含 water/ice-friendly 气溶胶气候值、use_aero_icbc、qna_update）；29 RCON（=28+液相反修改）；30/32 HUJI 快速/完整谱二元；38 Thompson 2-mom 霰/雹（4.5 新增）；40 Morrison+CESM-NCSU 气溶胶；50/51/52/53 P3 四变体；55 Jensen-ISHMAEL；56 NTU 多矩；88 TEMPO；95 Ferrier 旧 Eta；96 Madwrf；97 Goddard GCE；106 WSM6r
- 相关 namelist：hail_opt（WSM6/WDM6 雹开关）、mp_zero_out/_thresh/_all、nssl_cccn、wif_input_opt（=2 加黑碳）、num_wif_levels=30

### 6.7 杂项与待读
- Thompson RSLF/RSIF（5383/5418）：qsat = .622·ESL/(P−ESL)；RSIF 用 max(1.e-4,(P−ESI))；ESL/ESI 多项式在 5340–5382（行内引用未精读）
- 文件总长：module_mp_thompson.F ≈ 5700 行（mp_gt_driver 为单巨子程序，1070–~5250）
- Thompson 内 `rho_not = 101325/(287.05·298)`、Sc=0.632、C_cube=0.5/C_sqrd=0.15、Ef_si/Ef_rs/Ef_rg/Ef_ri=0.05/0.95/0.75/0.95、R1=1E-12/R2=1E-6

## 7. 实验记录（ch13_experiment.py，2026-10-10 跑通）

- A 组（埃玛图，书习题 7 探空）：LCL p=942.9 hPa / T=18.06℃ / z=506 m；书 (6.2.23) 估算 123×(23.0−19.0)=492 m（差 +2.8%）；LFC p=343.8 hPa / z≈7972 m；正能区 711 J/kg、负能区 −1330 J/kg（近似，未虚温订正）
- B 组：γs 闭式（含 ε）vs 数值微分——1000hPa 9.740/9.740、850hPa 4.204/4.165、700hPa 3.890/3.846、500hPa 3.411/3.360、300hPa 2.847/2.788 K/km（γd=9.77）；θse 沿假绝热积分漂移 ≤0.54%（(6.3.8) 本身为近似）；**书习题 8：700 hPa 处气块速度 24.1 m/s（未虚温订正）/ 26.5 m/s（虚温订正）**，δT=7.55 K
- C 组（饱和调整，T=25℃/1000hPa 例）：ss=0.002/0.005/0.02 → Thompson dT=0.0249/0.0622/0.2479 K、残差 9.1e-7/2.3e-6/9.0e-6；WSM6 dT=0.0250/0.0624/0.2496 K、残差 1.0e-6/2.6e-6/1.2e-5；定点真值 dT=0.0245/0.0611/0.2436 K。全程 dT 误差：Thompson ≤8.0e-3 K、WSM6 ≤1.15e-2 K（均为二阶小量）；残差随 ss 呈 ~ss² 标度
- D 组：wrfinput_d01 近兰州格点 (35.98N,103.73E)、49 层、最低层 p=790.9 hPa；θ（T+300）与 θse（(6.3.8) 复算）剖面对照出图
- 输出图：`doc/figs/ch13_emagram.png`、`ch13_theta_se.png`、`ch13_satadj.png`；日志 `workspace/logs/ch13_experiment.log`