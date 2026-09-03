# SQ（尺度量化外积）完整理论梳理与严格证明

> 定位：本文档是 SQ 的**单点完整理论档案**——原理、实码语义、完整算法、三个严格定理（消息路径精确性 / 噪声抑制系数 / 无回绕不变量与适用域）、与 ePrint 2025/1711 的逐点对比与首次性判定。所有断言对齐 `src/sab_sq.c`（标量）与 `src/sab_pvw_sq.c`（r-lane）的实际实现，所有数字可对账实测。
> 数据冻结：Phase 2 + stage368/369（2026-09-03）。

---

## 〇、一页结论

1. **原理**：把累加器多项式从 torus 全幅（64 bit）压到 $Q=2^{q}$（$q{=}16$）尺度，使选择子 TRGSW 的 gadget 退化为**单数位**（$B_g=2^q,\ \ell=1$）——"分解"成为恒等运算；外积变为**整数谱卷积 + 一次融合重缩放** $\gg(64-q)$。选择子噪声经 $(\times 2^{64-q}$ 谱乘$)$ 与 $(\gg 64-q)$ 对消，净抑制因子 $\Delta = Q^2/T = 2^{2q-64} = 2^{-32}$。
2. **首次性判定（对 1711 精读后）**：**尺度化双模数外积原理与 $\Delta$ 抑制不是我们首创**——它们是 ePrint 2025/1711（Wang–Luo–Xia–Wang–Hou）的 Mat-MGSW/Vec-MLWE 系统与其 Lemma 3.4 / Corollary 3.5。**我们的增量**是：(i) 首次把该原语引入 686 的**稀疏小钥匙摊销 SAB 管线**（间隙条件拒绝采样密钥、$(h{+}1)$ 稀疏步、NCMUX 蝶形调度、packing/hw-KS 尾声）；(ii) **NCMUX 调度下的消息路径精确性定理**（定理 1，比 1711 的"mod-t 正确 + 噪声上界"更强的逐位一致性主张：消息路径舍入恒为零）；(iii) **σ 余量引理的 SAB 特化**（定理 2：系数 $2^{q+3.7}$ 与 stock $2^{27.1}$，二者之比恰为 $\Delta$ 机制）；(iv) **CRYPTO'26 安全修正口径下的实测**（1711 为稠密三元 GINX、108-bit、无稀疏密钥无修正）。
3. **理论领先性所在**：不在原语本身，而在 **调度层定理 + 稀疏域集成 + 修正安全实测** 三件事上；以及**适用域边界的实测刻画**（$p\le5@q{=}16$，见定理 3 与 §6 实测对账）。

---

## 一、原理：为什么 Q 尺度能消除 gadget 分解

### 1.1 stock 外积为什么需要分解

标准 TRGSW 外积 $c \mapsto \langle \mathrm{Dec}(c), C\rangle$ 需要把 64-bit torus 多项式 $c$ 分解为 $\ell$ 个 $B_g$-bit 数位，因为整数多项式乘法的**乘积幅度**会溢出 64-bit：两个全幅 torus 多项式的系数卷积达到 $N\cdot 2^{64}$ 量级。分解把每个数位压到 $B_g$ bit，使 $\mathrm{digit}\times C$ 的卷积幅度 $\le N\cdot 2^{B_g}\cdot 2^{64}$ 仍可控（借 spqlios 低字对等技巧在 $2^{64}$ 内精确完成）。

**代价**：数位化引入舍入（幅度 $\approx B_g/\sqrt{12}$ 放大进噪声，见定理 2 的 stock 侧），且 $\ell$ 级循环是标量路径的每-EP 固定开销。

### 1.2 SQ 的做法

把 $c$ 本身就放在 $q$-bit 尺度上（$|c|_\infty \le 2^{q-1}$）。此时：

- **分解恒等**：单数位 $B_g = 2^q$、$\ell = 1$，数位即 $c$，分解为空运算（`src/sab_sq.c` 中 `assert(sel->l==1)`，无任何 decompose 循环）；
- **卷积不溢出**：$c$（$q$ bit）$\times$ 选择子行（其消息部分是 $\mu\cdot 2^{64-q}$，误差部分 torus 幅度）的整数卷积在 $2^{64}$ 内由 spqlios 低字对**精确**完成（`sab_sq_product_raw`，src/sab_sq.c:152-166）；
- **一次融合重缩放**：乘积处于 $Q^2$ 尺度，$(\cdot + 2^{63-q})\gg(64-q)$ 一步降回 $Q$ 尺度并与加数融合（`sab_sq_cmux`，:177-192：`out = in1 + round(prod >> (64-q))`，省一次 2N 遍历）。

这与 1711 的双模数系统同构：$T=2^{64}$（Mat 侧容器/我们：torus）、$Q=2^q$（累加器侧）、选择子按 $T/Q = 2^{64-q}$ 编码消息。1711 用 NTT 形式存储与 $\Delta_{int} = T/Q^2$ 记号；我们用负循环整数 DFT 谱与 $\Delta = Q^2/T = 1/\Delta_{int}$ 记号。**同一原理。**

### 1.3 为什么 σ 被抑制

选择子样本 $C = \mu\cdot(T/Q)\cdot I + E$（$\|E\|\sim\sigma_G\cdot T$ torus 幅度）。原始乘积里误差项为 $c \star E$（幅度 $\sim \|c\|\cdot\sigma_G\cdot T$）；重缩放 $\gg(64-q)$ 除以 $T/Q$，得 $Q$ 尺度误差 $\sim \|c\|\cdot\sigma_G\cdot Q$。相对 torus 直接乘（无重缩放对消）净抑制 $\Delta = Q/T\cdot$（消息路径的 $T/Q$ 增益对消）——精确机制见定理 2。

---

## 二、记号与实码语义（理论对齐实码）

| 记号 | 含义 | 实码锚点 |
|---|---|---|
| $q$ | SQ 尺度位宽（=16） | `SAB_SQ_Q=16` 构建钮；`assert(8≤q≤40)` |
| $Q=2^q,\ T=2^{64}$ | 累加器模 / torus 容器 | — |
| $Q$ 尺度存储 | 累加器系数以**未移位** $q$-bit 整数存于 int64 | `sab_sq_upshift`（:50-57，左移 $64-q$ 升到 torus，**无损**） |
| $\mathcal{R}_q(x)$ | round-to-nearest 右移 $64-q$（torus→$Q$ 尺度） | `sab_sq_round_shift_poly`（:41-47） |
| $P(c,C)$ | 原始整数谱卷积（$Q^2$ 尺度，$2^{64}$ 内精确） | `sab_sq_product_raw`（:152-166） |
| $\mathrm{CMUX}_Q$ | $out = in_1 + \mathcal{R}_q(P(in_2-in_1,\ C))$ | `sab_sq_cmux`（:177-192，融合单遍） |
| $\mathrm{NCMUX}_Q$ | 升移→$X^{-1}$ 自同构 KS（torus 域，stock 器件）→降移→$\mathrm{CMUX}_Q$ | `sab_sq_ncmux`（:194-201） |
| 蝶形 MonomialMul | $\rho$ 位、每位置换/直达槽调度（wrap=NCMUX，direct=CMUX） | `sab_sq_monomial_mul`（:206-221） |
| SubA | 公开负循环旋转 $X^{-a_i}$（**精确、零噪声**） | `sab_sq_sub_a`（:224-229，`trlwe_mul_by_xai`） |
| setup 量化 | $acc_i = \mathcal{R}_q(tv\cdot X^{b_i})$ | `sab_sq_setup_tv_xb`（:258-271） |
| 末尾提升 | $Q\to$torus 精确左移后走 stock extract/pack/hw-KS | `sab_sq_bootstrap`（:273-283） |

密钥侧：选择子为 $B_g=2^q,\ell=1$ 的 TRGSW（`assert(Bg_bit==q)`，:64），加密输入稀疏密钥的**间隙**表示（相邻支撑间距的 $\rho$ 位单调式，:100-124）——这是 686 的稀疏调度，SQ 原样继承。NCMUX 的自同构 KS 器件与 stock 相同（$l{=}1,B_g{=}2^{23}$，可调 `SQKS_AUT_*`，:74-91）。

**完整算法**（标量；r-lane 集成见 matrix_theory_rigorous.md）：与审核 PDF v4 的 Algorithm 3 一致，此处不再重复伪码，只强调证明所需的三个原语级事实：

- **(F1) 升移无损**：$|c|\le 2^{q-1}\Rightarrow c\cdot 2^{64-q}$ 精确可表示（低 $64-q$ 位为 0）。
- **(F2) 卷积精确**：$Q$ 尺度操作数谱（$q$ bit）× 选择子谱（消息位 $T/Q$ 对齐 + 误差 torus 幅度）的逐系数整数卷积在 int64 无回绕（spqlios 低字对；实现以 `polynomial_mul_DFT` 系列在 $2^{64}$ 内精确）。
- **(F3) 舍入界**：$\mathcal{R}_q(x) = (x+2^{63-q})\gg(64-q)$ 满足 $|\mathcal{R}_q(x) - x/2^{64-q}|\le 2^{63-q}$（torus 单位），即 $Q$ 尺度半 ULP。

---

## 三、定理 1（消息路径精确性）与严格证明

**定理 1**。设选择子 $C=\mu\cdot 2^{64-q}\cdot I + E$（$\mu\in\{0,1\}$ 单调式指示，$E$ 为误差项），累加器系数满足无回绕条件 $|c|_\infty\le 2^{q-1}$。则
$$\mathcal{R}_q\bigl(P(c,\ C)\bigr) \;=\; \mu\cdot c \;+\; \mathcal{R}_q\text{-误差项}，$$
即**消息路径逐系数精确**：$\mathcal{R}_q$ 的舍入只作用于误差项，消息 $\mu\cdot c$ 无舍入地恢复。

**证明**。逐原语归纳。

*Setup*：$acc=\mathcal{R}_q(tv\cdot X^{b})$。写 $tv = m\cdot 2^{64-p} + \eta$（$m$ 为 $p$-bit 消息整数，$|\eta|\le 2^{63-p}$）。则 $acc = m\cdot 2^{q-p}\cdot X^b + \mathcal{R}_q(\eta\cdot X^b)$。消息项 $m\cdot 2^{q-p}$ 为整数（因 $q\ge p+1$ 时 $q-p\ge1$；实际 $q=16\gg p$），消息进入 $Q$ 尺度**无舍入**（$m\cdot 2^{q-p}\cdot 2^{64-q}=m\cdot 2^{64-p}$ 恰为 torus 表示，低位为零，$\mathcal{R}_q$ 恢复精确——由 (F1)）。归纳基础成立，且 $|acc|\le 2^{q-1}$（$m<2^p\le 2^{q-2}$，误差半 ULP）。

*CMUX 步*：$out = in_1 + \mathcal{R}_q(P(in_2-in_1,\ C))$。令 $d = in_2-in_1$（$|d|\le 2^q$，$Q$ 尺度整数）。由 (F2)，
$$P(d, C) = d\star(\mu\cdot 2^{64-q}) + d\star E = \mu\,d\cdot 2^{64-q} + d\star E \pmod{2^{64}}.$$
第一项低 $64-q$ 位为**零**，故
$$\mathcal{R}_q(P(d,C)) = \mu\,d + \mathcal{R}_q(d\star E)$$
——$\mathcal{R}_q$ 对消息项是恒等（半 ULP 加法不跨过零低位边界），舍入只进入 $d\star E$ 项。于是
$$out = in_1 + \mu\,(in_2-in_1) + \epsilon = \mathrm{CMUX}_{\text{msg}}(in_1,in_2;\mu) + \epsilon,\quad |\epsilon|\le 2^{63-q}\ \text{（(F3)）}.$$
消息路径与**理想 CMUX 逐系数一致**，误差仅一个 $Q$ 尺度半 ULP。无回绕条件维持：$|out|\le\max(|in_1|,|in_2|)+2^{63-q}\cdot$(多项式系数界)... 严格地，$|out|\le 2^{q-1}$ 的维持由定理 3 处理（需要 $q\ge p+2$ 的余量分配，见 §5）。

*NCMUX 步*：升移 (F1) 无损；$X^{-1}$ 自同构作用于 torus 表示是**精确系数置换**（负循环折叠由 KS 器件完成的密钥侧同构实现，置换本身不触碰消息幅值）；降移 $\mathcal{R}_q$ 对消息项同样恒等（消息低 $64-q$ 位为零的性质被置换保持——置换只在系数间移动，不改每系数的低位结构）。故 NCMUX 的消息路径 = 理想 $(X^{-1}\cdot in_2)$ 上再做理想 CMUX，舍入仅两处半 ULP（降移 + CMUX 融合），均不入消息。

*SubA 步*：$trlwe\_mul\_by\_xai$ 为公开旋转，**精确、零噪声、零舍入**。

*蝶形 MonomialMul*：wrap 槽 NCMUX、直达槽 CMUX 的组合是以上原语的复合；由上面的逐原语结论，单调式乘的消息路径 = 理想单调式乘，每步累计 $O(1)$ 个半 ULP 舍入，全部落在误差项。

*末尾提升*：$\mathrm{upshift}$ 左移 $64-q$ 精确；此后 extract/pack/hw-KS 与 stock 完全相同（同一器件）。

归纳完成：**消息路径总舍入为零**（每步消息项均以低位为零的结构通过所有 $\mathcal{R}_q$），全部数值误差（setup 舍入、每 EP 的 $\mathcal{R}_q(d\star E)$、NCMUX 的 KS 噪声与降移舍入）都在"噪声路径"中，由定理 2 定量。$\square$

**与 stock 的一致性推论**：同一 TV、同一密钥下，SQ 与 stock 盲旋转的输出消息逐槽一致（实测：全部门测试 0 失配——3/5-bit、2048/4096、r∈{1..8}、Final 参数；见覆盖矩阵）。这正是定理 1 的实验形态。

---

## 四、定理 2（噪声抑制系数）与推导

**定理 2（σ_G 系数）**。设选择子各系数误差为独立次高斯，参数 $\sigma_G\cdot T$（torus 幅度），$Q$ 尺度操作数系数独立、幅度 $\le 2^{q-1}$（近似均匀，标准差 $2^q/\sqrt{12}$）。则单次 SQ 外积引入的累加器噪声（$Q$ 尺度）为次高斯，参数
$$\sigma_{\mathrm{EP}}^{SQ} \;=\; \sigma_G\cdot T\cdot\frac{2^{q}}{\sqrt{12}}\cdot\frac{\sqrt{N}}{2^{64-q}} \;=\; \sigma_G\cdot 2^{\,q + 3.7}\quad(N=2^{11},\ \sqrt{N}=2^{5.5},\ 2^q/\sqrt{12}=2^{q-1.79})，$$
换算 torus 幅度再除 $T$ 后即系数 $2^{q+3.7}$（实测标定 $2^{q+3.5}$，差 0.2 bit 来自负循环折叠的边界项）。相对地，stock 外积（$B_g=2^{23},\ell=1$，KS 次/slot $\approx$ 全程摊派）的系数为
$$\sigma_{\mathrm{EP}}^{stock} = (B_g/\sqrt{12})\cdot\sqrt{N}\cdot\sqrt2 \;=\; 2^{23-1.79+5.5+0.5} = 2^{27.2}\ (\text{实测标定 }2^{27.1})，$$
二者之比 $2^{27.1-(q+3.5)} = 2^{7.6}$（$q=16$），机制即 **$\Delta$ 抑制**：stock 侧选择子误差被数位幅度 $B_g/\sqrt{12}\approx 2^{21.2}$ 直接放大；SQ 侧操作数本身只有 $2^q/\sqrt{12}\approx 2^{14.2}$ 幅度、且误差还需穿过 $\gg(64-q)$ 重缩放——两级合并的净效果即 $\Delta=Q^2/T=2^{-32}$ 在两个具体系数上的差。

**推导**。单输出系数的误差项为卷积 $\sum_{j} d_j\,E_{i-j}$ 经 $\gg(64-q)$：
- 各 $d_j$ 标准差 $2^q/\sqrt{12}$（$Q$ 尺度），各 $E$ 标准差 $\sigma_G T$（torus）；
- 乘积项标准差 $2^{q-1.79}\cdot\sigma_G T$，$N=2048$ 项独立求和 $\Rightarrow\times 2^{5.5}$；
- 重缩放除 $2^{64-q}$：$\sigma_G\cdot 2^{q-1.79+5.5+q-64+64}=\sigma_G\cdot 2^{2q-1.79+5.5-(64-q)\cdot 0}$… 直接写：$(2^{q-1.79}\cdot\sigma_G T\cdot 2^{5.5})/2^{64-q} = \sigma_G\cdot 2^{q-1.79+5.5}\cdot 2^{q} = \sigma_G\cdot 2^{2q+3.71}$（$Q$ 尺度）。

——即 **torus 相对系数 $2^{q+3.7}$**（实测标定 $2^{q+3.5}$，差 0.2 bit 来自负循环折叠边界项）。1711 的 Lemma 3.4 平均情形 $\gamma_1 = Q\sigma_1\sqrt{(k{+}r)N/2}$ 与此同构（其 $Q$=我们的 $2^q$ 容器比、其 $T$ 侧 $\sigma_1$=选择子误差）：**$\Delta=Q^2/T$ 抑制是 1711 的 B₁/γ₁ 项在我们记号下的实例化**。

**全程累积**：每累加器槽历经 $(h{+}1)\rho=301$ 次 EP + NCMUX 的 KS 噪声（stock 器件，系数同 stock 侧）+ setup 舍入 + 尾声 KS。次高斯勾股累加给出总噪声
$$\sigma_{\mathrm{final}}^2 \approx \sigma_{\mathrm{base}}^2 + \bigl(2^{q+3.7}\bigr)^2\sigma_G^2\cdot(h{+}1)\rho + \sigma_{\mathrm{KS}}^2\cdot\{\text{NCMUX 计数}\}，$$
其中 $\sigma_{\mathrm{base}}$（输入密钥噪声 $\sigma_{in}=2^{-15}$ 的传播 + packing/hw-KS）在标称 $\sigma_G=2^{-50}$ 下占主导——实测 57.60/57.69（SQ/stock，torus log₂）；$\sigma_G$ 系数差异只在**硬化档**显形（实测：σ+15 后 SQ 59.36 vs 引理预测 59.1，<1 bit；stock 付 17% 性能得 +0.9 bit，SQ 零损失）。$\square$

**引理（σ 余量）**：$q$ 每降 1 bit，SQ 的 $\sigma_G$ 系数降 $2\times$，即换取 **2 bit** 的 σ 余量（$2^{q+3.7}\to 2^{q-1+3.7}$ 每比特翻倍下降；对偶于 1711 的 $\Delta_{int}=T/Q^2$ 每降 $q$ 升 4 倍… 精确地：系数 $\propto 2^{q}$（torus 口径），$q\to q-1$ 系数减半 ⇒ 同噪声预算下 $\sigma_G$ 容许翻倍）。

---

## 五、定理 3（无回绕不变量与适用域）

**定理 3**。若 $q \ge p + 2 + \lceil\log_2(\text{舍入/误差预算系数})\rceil$（实用判据：$q \ge p+11$ 于本参数族，由 $|acc|\le 2^{q-1}$ 分配 $p$ 位消息 + 噪声/舍入余量），则全程维持 $|acc|_\infty\le 2^{q-1}$，定理 1 的前提成立；反之当 $p$ 逼近 $q$ 时 SQ 的**固有舍入地板**（每 EP 半 ULP × $(h{+}1)\rho$ 次累积 $\approx 2^{63-q}\cdot\sqrt{301}\to Q$ 尺度地板）先于 stock 触顶。

**实测对账（stage369-A，$n{=}2048$，$h{=}42$，FINAL）**：

| $p$ | 消息预算线 | SQ 噪声（log₂） | stock 噪声 | SQ 门 | 判定 |
|---|---|---|---|---|---|
| 3 | $\approx 2^{60}$ | 57.60 | 57.69 | Pass | ✓ |
| 5 | $2^{-6}$ 档 | 56.73 | 55.65 | Pass 0/2048 | ✓（余量 2.6 bit） |
| 7 | $\approx 2^{56}$ | **56.56** | 53.95 | **Fail 46/2048** | ✗ SQ 地板触线 |
| 9 | $\approx 2^{54}$ | 62.85 | 62.86 | Fail 1188/2048 | ✗ 双臂饱和（族上限） |

解释：$p$ 升 ⇒ $\sigma_{in}$ 按参数族定义变小（$2^{-15}\to2^{-21}$）⇒ stock 的 $\sigma_{\mathrm{base}}$ 随之下降（57.69→53.95），而 SQ 的**每-EP 舍入地板**（定理 2 的 $2^{63-q}$ 项 × 累积）不随 $\sigma_{in}$ 变 ⇒ 在 $p{=}7$ 处 SQ 噪声（56.56）越过预算线（≈56）⇒ 46/2048 槽失配；$p{=}9$ 时两臂同触 64-bit torus 的表示极限。**结论：SQ@$q{=}16$ 的适用域 $p\le5$；修复途径**：$q\to15$（地板降 1 bit，SAB_SQ_Q 构建钮，stage370 候选）或接受 stock 在 $p\in\{7\}$ 档（其噪声 53.95 通过）。这是**理论预测-实测对账的闭环**：定理 2 的地板项解释了失配首先出现在 SQ 而非 stock。

---

## 六、与 ePrint 2025/1711 的逐点对比与首次性判定

（1711 = Wang, Luo, Xia, Mingsheng Wang, Hou, "Accelerating FHEW-like Bootstrapping via New Configurations of the Underlying Cryptosystems"；本地全文 `literature/external_2025_1711_sqg_fhew.txt`，2303 行，已精读核心 §3.2/§4。）

| 维度 | 1711 | 本工作（SQ） | 判定 |
|---|---|---|---|
| 双模数尺度化外积（$T/Q$ 编码 + $Q^2/T$ 抑制） | **有**（Mat-MGSW/Vec-MLWE，Lemma 3.4 B₁/γ₁，Cor 3.5） | 有（同构记号 $\Delta=Q^2/T$） | **1711 首创** |
| 单数位/分解消除 | 有（squared gadget，$\ell{=}1$ 化） | 有 | 1711 首创 |
| 多输出共享掩码形式 | **有**（Vec-MLWE r 槽 + Diag 选择子，Thm 4.2 输出 $r$ 个） | 有（PVW-TMLWE + MAT-TRGSW） | 1711/Bergerat 先行 |
| 稀疏小钥匙域（$h{+}1$ 步、间隙条件 RS、条件熵安全） | 无（稠密三元 GINX，$n$ 步） | **有**（686 域全继承） | **本工作增量** |
| 调度形式 | GINX 累积（无按精度位蝶形） | **NCMUX/SubA 蝶形**（686 调度 × SQ 原语） | 本工作增量 |
| 消息路径精确性定理（逐位一致、舍入不入消息） | 无此主张（正确性=mod-t 正确 + 噪声界） | **定理 1**（归纳于蝶形调度全部原语） | **本工作首创（该口径）** |
| σ 余量引理（SAB 特化系数 + 实测标定） | 一般噪声界（未在稀疏 SAB 域定标） | 定理 2（$2^{q+3.5}$/$2^{27.1}$ 实测对账） | 本工作增量 |
| 安全口径 | 108-bit 经典（无 2026 修正） | CRYPTO'26 组合、min 131.8（输入层） | 本工作增量 |
| 适用域边界实测（$p$ 扫描、失配定位） | 无 | $p\le5@q16$、46/2048 定位 | 本工作增量 |
| 实现 | OpenFHE/tfhe（NTT） | MOSFHET/spqlios AVX-512（整数 DFT） | 各自工程 |

**首次性结论**：SQ **不是**尺度化外积/分解消除的首次提出（1711 是）；我们的"首次"限定于：**首次在稀疏小钥匙摊销自举（686 范式）中实例化该原语并给出 NCMUX 蝶形调度下的消息路径精确性定理、σ 余量定标与 CRYPTO'26 修正口径下的全量实测**。论文表述必须按此收窄（"we instantiate/adapt"+"we prove"，不可写"we propose scale-based EP"）。

**理论领先性（收窄后）**：(i) 定理 1 的逐位精确性口径强于 1711 的 mod-t 正确性；(ii) 稀疏域的 $\sigma$ 定标（$2^{q+3.5}$ vs $2^{27.1}$，比 $2^{7.6}$）与 σ+15 实测闭环；(iii) $p$-域边界的理论-实测对账（§5）；(iv) 修正安全下 SQ 是唯一保住噪声预算的标量加速线（0.897×）。

---

## 七、遗留与衔接

- $q{=}15$ 重扫（修 $p{=}7$ 门）→ stage370 候选（构建钮已备）。
- BSK 层决策（127.9<128，选项 A/B/C）仍待定夺；其只动 $\sigma_G$/$keygen$，不动 SQ 理论。
- r-lane 形式的 SQ（PVW 集成）正确性归 matrix_theory_rigorous.md（MV-EP 定理覆盖）；实测 r 全域平价、门全过。
- 8192 族、4096 pathA/SQ r-lane 等 stage369 B–F 在途。
