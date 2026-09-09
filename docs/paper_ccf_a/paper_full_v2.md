# Amortized Bootstrapping at the Information-Theoretic Frontier: Combining Packing and Batching with Matching Lower Bounds

**paper_full_v2（装配骨架 v2）** — Date: 2026-09-09
来源（单一事实源，正文段落直接取自）：
§3 = theory_checks/stage406_alg12_paper_section.md；
§4 = theory_checks/stage405_noise_master_theorem.md（N1 章）；
§5 = theory_checks/stage409_lb_paper_section.md；§6-7 素材 =
sq_theory_rigorous / stage371-381 实测系；附录 B/C/D 素材 =
GF(257) 检查器 / 否定性结果目录 / 实现细节。
状态：§1-2 装配完成（P-1）；§3-5 汇入完成（P-2）；§6-8 + 附录 =
P-3/P-4（下一会话）；P-5 = NT-1 记号 lint。

---

## Abstract（草）

We study amortized FHEW-style bootstrapping for sparse-secret exact
bootstrapping and ask how fast one bootstrap per message can be, in the
class of monomial-accumulating blind rotations. We give (i) a complete
combined packing-and-batching algorithm family: r distinct inputs share
one blind rotation over an interleaved ring, with a relative-trace
subtraction operator U_a, a transposition correction Ψ, and a
closed-on-Z_{2^q} final-doubling rescaling protocol — all machine-
verified against scalar oracles over GF(257); (ii) a per-message noise
master theorem with a per-step profiler closing prediction to
measurement within 0.2-0.3 bits at every pipeline stage, built on a new
DC-walk theorem for one-sided gadget-decomposition residuals; (iii) a
matching lower bound for the class (three-layer per-phase bound under
explicit assumptions) with our construction matching at the optimal row
constant (1+k/r → 1 versus k+1 for the 686 baseline), and a time-key
frontier theorem delimiting all known escapes; (iv) the only ≥128-bit
(corrected-attack metric) amortized bootstrapping instantiation among
public competitors (130.4), with 1.66-1.84x system throughput and a
full negative-results catalog.

## 1 Introduction（四贡献 C1-C4，定稿结构）

**C1（理论核心）**：单项式累积盲旋转类的每消息下界定理 LB-F
（三制式前沿；条件 H1-H5 显式；S1 语义定理 + 否定性结果目录支撑
【§5.5】）；标准钥束制式下本工作匹配下界且行常数最优
(1+k/r)→1（686 为 k+1）；批处理轴 Θ(1/r) 渐近（§5.3）。

**C2（算法）**：combined packing and batching 完整算法族（Alg 1'/2'
代数基版【§3】+ Alg 3/4 矩阵版【附录 D 映射】），正确性定理 C1'
（HT-5+M1+S1 组合，逐步归纳），GF(257) 机器验证方法论（附录 B）。

**C3（噪声）**：多项式误差增长主定理 N1（§4）：EP 四项分解恒等式
（整数精确裁决）+ **DC-游走定理**（单边分解残差的确定性阶梯主导项，
rms = μ_ε·N/√12，m=1 事件相干累积）+ 管线递推（相干轨 + 白噪声轨
双轨）；逐步 profiler 紧对账（两参数点 × 6 试全阶段 ≤0.19 bit、
pair ≤0.28 bit）；Z_{2^q} 封闭终倍增协议（HT-7'/8）。

**C4（实验+安全）**：修正安全下唯一 ≥128（130.4；BatchBoot 四集
FAIL 重评）；主矩阵 1.66–1.84×；r 选值；r-input 门（dell 0/512 与
0/1024，6 试 × 2 点）；DFR certified+经验；否定性结果目录（附录 C）。

**论文地图**：§2 Prelim（V2 §1.3 密码系统 + 次高斯工具 + 记号表）；
§3 算法与正确性；§4 噪声；§5 复杂度与下界；§6 安全（修正口径）；
§7 实验；§8 Related/Conclusion；附录 A 证明 / B GF(257) 方法论 /
C 负结果目录 / D 实现细节与参数表。

**1711 定位披露（内层子运算）**：矩阵外积/尺度化 gadget（Mat-MGSW×
Vec-MLWE、Δ=Q²/T 抑制）为本团队前作 ePrint 2025/1711 的内层原语，
如实引用并披露作者重叠；本工作贡献在外层完整自举算法（稀疏间隙
调度、Ψ/U_a/终倍增、噪声-精度域管理、修正安全定参与实测）。

## 2 Preliminaries

### 2.1 记号（stage400 §1 统一表为单一来源）

R_Y=Z[Y]/(Y^n+1) 输入环；R=Z[X]/(X^N+1) 自举环；A=Z[Y]/(Y^d+1)
交织子环（N=r·d）；lane 数 r（r₁ LUT × r₂ input 合成 r=r₁r₂）；
h+1 稀疏相位、ρ=⌈log₂(n/h)⌉、间隙 d_t；Vec-MLWE / Mat-MGSW；
gadget (ℓ,Bg) 双模数 T>Q；CMUX/元数 a 选择门；U_a 相对迹、P_w 权重、
H=Gal(R/A)；Ψ=U_{(0,1)}∘σ₋₁；R₂ 重缩放与 U_{(0,0)} 终倍增；
σ₁,σ₂ 噪声参数（Lemma 1.7 记号）；H1-H5 下界条件。代码映射仅附录 D。

### 2.2–2.4

次高斯工具（V2 §1.2：π-可吸附性、Pythagorean 合成）；尺度化密码
系统与外积（V2 §1.3 = Lemma 1.7 原文域）；稀疏摊销自举设定
（间隙条件 RS 密钥、条件熵安全）。

## 3 The Algorithm（全文 = stage406）

【嵌入 stage406 §3.0–§3.7 全文：Overview / Setting / Alg 1' +
定理 3.2(S1) / Alg 2' + 引理 3.4' + 3.6' + 定理 3.8 / 定理 3.9(C1')
归纳全文 / GF(257) 对应表 / 算子计数 / V2 差异清单】

## 4 Noise（全文 = stage405）

【嵌入 stage405 §1–§7：实现锚定与两种数位化约定 / N-ε、N-EP、
N-DC（DC-游走定理）、N-KS、N-Ψ、N-suba / 定理 N1 双轨递推 /
推论 N1' 两参数点对表（全阶段 ≤0.19 bit）/ HT-6'（M-HT.4 定稿）/
N-S 尺度化统一（Lemma 1.7 形式 → Thm 2 ±0.2 bit）/ N-HYB /
奇尾现象如实注记 / 勘误与一致性核对】

## 5 Complexity and Lower Bounds（全文 = stage409）

【嵌入 stage409 §5.0–§5.6：模型 C0 与双口径 M_lin/M_fft / 三层
每相位下界 + 元数-钥预算 + L4 / LB-F 三制式（F1 匹配+最优行常数、
F2 HYB crossover ρ*≈11、F3 信息地板）/ 推论 5.8 主张措辞 /
A1-A3 摊销定律 / CM 五族覆盖 / 否定性结果目录 / 诚实边界】

## 6 Security Under Corrected Attacks（P-3 装配完成；v1 §4 基底 + r-input 增量）

### 6.1 The correction mechanism

The ring-isomorphism hybrid attacks of [Careful26] exploit the structure
of sparse keys in power-of-two cyclotomic rings. The key generation of
[GP25] uses rejection sampling for bounded position gaps (d_i < B =
O(n/h)), conditioning the secret distribution. The conditional entropy
H(s | accept) = H(s) − log₂(p_accept) is computed by Monte Carlo
(20,000 samples per set, replicating the implementation's gap-check
semantics).

### 6.2 Corrected parameters

Five attack tiers (primal uSVP, dual hybrid — both from the new
lattice estimator; hybrid decoding from the published attack code;
lattice MITM; conditional-entropy closed form T3'); system security =
minimum over tiers:

| Layer | Parameters | uSVP | dual-hybrid | HD | MITM | T3' | min |
|---|---|---|---|---|---|---|---|
| Input | h=42, t=7 | 904.1 | — | — | **131.8** | 133.5 | **131.8** |
| BSK | σ_G=2^{-49} | 133.5 | **130.4** | — | — | — | **130.4** |

System minimum 130.4 ≥ 128 (margin 2.4 bits); the σ_G 2^{-50}→2^{-49}
upgrade costs +0.08 noise bits (measured), zero performance impact.

**r-input key-bundle increment.** The interleaved r-input path adds
exactly two automorphism key-switching keys (σ₋₁ and σ_{1+N}, the
latter shared between sub_a and the Ψ correction — Lemma Ψ-Min); the
attack surface is unchanged in dimension from standard KS keys.

### 6.3 Competitor re-evaluation

Same corrected portfolio applied to published parameters:

| Scheme | Set | Their claim | Corrected min | Deficit |
|---|---|---|---|---|
| SAB [GP25] | h=39 | — | 124.5 | 3.5 |
| BatchBoot | Boot2/4/6/8 | >128 | **124.2 / 124.2 / 120.5 / 124.6** | 3.4–7.5 |

BatchBoot BSK-tier verdicts come from the standard estimator,
independent of our T3' method. TFHE-rs and CKKS schemes use dense
secrets (unaffected by this attack class; noted for fairness).

### 6.4 Decryption failure rate

Analytic Gaussian-tail bound DFR ≤ 2^{-2724}; empirical: >10⁶
zero-failure observations, Clopper-Pearson 95% upper limit 2^{-18.4}.

## 7 Implementation and Experimental Evaluation（P-3 装配完成）

### 7.1 Environment and discipline

Single machine (dual Xeon Gold 6230R, AVX-512 + VAES, spqlios backend;
load-gated <10). All speedups are **same-binary paired comparisons**
(cross-build drift measured at −7%…+23%, declared invalid); ≥3 runs
per point (6 for the noise gates); zero-mismatch correctness is a
prerequisite for any timing. Baseline = SAB's official CCS'25 artifact
(this repository); TFHE-rs v1.8.0 same-machine; BatchBoot has no public
implementation (parameter-level re-evaluation only, §6.3).

**Presentation caliber.** All ratios are reported as baseline-time /
our-time (e.g., 6.34/3.52 ms = 1.80×, i.e., "1.80 times faster").

### 7.2 Main matrix（r = 4, h = 42, corrected σ_G；口径 = 686/我方）

| Set | Prec | n | Ours ms/msg | 686 ms/msg | **686/ours** |
|---|---|---|---|---|---|
| SET_2_3_2048 | 2/3 | 2048 | 3.52 | 6.34 | **1.80×** |
| SET_4_5_2048 | 4/5 | 2048 | 3.75 | 6.90 | **1.84×** |
| SET_2_3_4096 | 2/3 | 4096 | 3.32 | 5.77 | **1.74×** |
| SET_4_5_4096 | 4/5 | 4096 | 3.54 | 6.11 | **1.73×** |
| SET_6_7_4096 | 6/7 | 4096 | 3.94 | 7.15 | **1.81×** |
| SET_8_9_4096 | 8/9 | 4096 | 27.91 | 46.34 | **1.66×** |

（8-bit row: doubled output ring 8192.）安全修正免费：h=39→42 下
两臂同慢 ~7%，比值 1.808→1.806（噪声级）。

### 7.3 r-selection

| r | Speedup (2-bit / 4-bit) | Marginal lane (s) |
|---|---|---|
| 1 | 1.36 / 1.34 | — |
| 2 | 1.80 / 1.81 | 4.86 / 5.04 |
| 4 | 1.80 / 1.84 | −0.02 / −0.09 |
| 8 | 1.23 / 1.23 | +1.94 / +1.99 |

r=2→4 marginal ≈ 0（M3 预测：第 3/4 体近似免费）；r=8 密集项与
cache 效应主导回退。

### 7.4 r-input interleaved bootstrapping（新增行：stage403/405）

Two parameter points (n=256/h=6/rp=7 and n=512/h=8/rp=9, out ring
2048), 6 trials each, all gates PASS:

| Point | Gate | Pair noise rms | Reconciliation | Bench (2×scalar caliber) |
|---|---|---|---|---|
| n=256/h=6 | 6/6 (0/512) | 2^52.6 | per-stage ≤0.17 bit; final −0.01; pair **+0.28** | 1.23× |
| n=512/h=8 | 6/6 (0/1024) | 2^52.7 | per-stage ≤0.19 bit; final −0.00; pair **+0.24** | 1.32× |

The absolute amortized claim for r-input is **semantic** (two distinct
inputs per blind rotation with per-lane oracle equality), not a
speedup over 2×scalar at toy sizes; the noise closes against the N1
master-theorem prediction at every pipeline stage (§4).

### 7.5 Noise-theorem validation（N1，§4 的实验形态）

Primitive closure (derived vs measured, all ≤0.3 bit): ε rms 40.26 vs
40.22; σ_KS 44.19 vs 44.30–44.44; **DC-walk 49.20 vs 49.18–49.21**;
σ_EP(0) 43.4 vs 43.37–43.43; Ψ 44.63 vs 44.40–44.45; sub_a (ks/√2)
vs 43.73–43.76. Pipeline-level: the coherent DC track + white
quadratic track predict every stage of both points within 0.19 bits
(worst |log₂ ratio| over 6×57 stages = 0.186); the mirror pipeline is
asserted bit-identical to the stock rotation (12/12 trials).

### 7.6 Component profile and negative results

Kernel profile (r=4): decomposition 8.6%, forward DFT 39.9%, dense
addmul 51.6%; r-scaling of row counts matches (1+r)/2r exactly.
Closed optimization candidates (all with gates or measured evidence):

1. **Multi-bit scheduling δ=2**: correct, 1.38–1.58× slower.
2. **Joint r-output packing**: epilogue = 3.0% ≪ 15% threshold.
3. **σ-only hardening**: fails without joint KS adjustment.
4. **Naive Hom-Tr (single automorphism)**: incorrect (coefficient
   permutation ≠ monomial shift) — superseded by the relative-trace
   U_a operator, now fully implemented and verified (§3, §7.4).
5. **OS-MPMUL single-shot monomial move**: refuted (GF(257) M1/M2
   240/240 mismatches; butterfly semantics = relabeling + crossing
   σ₋₁, Theorem S1).
6. **Bare σ₋₁ transposition** for interleaved packing: lane-1 twist
   (impossibility Lemma 3.6'/Ψ-Nec; negative control 1280/2560).

### 7.7 Resource usage

Bootstrapping keys ≤ 1.07× scalar (binary mode) vs 3.2–3.5× BatchBoot;
keygen 0.7 s including the odd-exponent automorphism family (2048
keys, N=2048; ρ-SAB); r-input adds exactly 2 KS keys (§6.2). Peak
memory comparable to scalar.

## 8 Related Work and Conclusion（P-3 装配完成）

**Amortized bootstrapping.** [MS18] theoretical framework; [GPV23]
first implementation (63 GB keys); SAB [GP25] practical keys (17–77 MB)
via the MPmul butterfly — our schedule base (the "686" baseline in all
calibers). BatchBoot [BB26]: fastest reported amortized numbers
(2.2–2.4× over SAB) but all four published parameter sets fail the
corrected 128-bit bar (§6.3); no public implementation.

**Inner primitive.** Wang et al. [ePrint 2025/1711] provide the
scale-based Mat-MGSW/Vec-MLWE framework with the Δ = Q²/T suppression
(Lemma 1.7 domain), which we adopt as the inner kernel of the outer
bootstrapping algorithm; the complete outer algorithm (Ψ/U_a/final-
doubling, noise domain management, corrected-security instantiation)
is the contribution of this work. [Ber25] instantiate shared-mask
bootstrapping in the dense GLWE domain. TFHE-rs [Zam22]: fastest
non-amortized baseline (dense keys, unaffected by this attack class).

**Conclusion.** Under corrected ring-isomorphism hybrid attacks the
amortized-bootstrapping landscape changes qualitatively: the published
state of the art falls below 128 bits. We give the only ≥128-bit
instantiation (130.4) at zero performance cost, a complete combined
packing-and-batching algorithm family with per-lane correctness and a
machine-verified semantic layer, a per-step noise master theorem
closing prediction to measurement within 0.2–0.3 bits (built on a
DC-walk theorem for one-sided gadget residuals), and a matching lower
bound for the monomial-accumulating blind-rotation class with the
optimal row constant. A catalog of negative results delimits the
design space. Full open-source implementation and reproducible
experiments accompany the paper.

## Appendices（P-4）

A 证明全文（S1/HT-4'/Ψ-Nec/N-DC/HT-7'7'8/L2 三层/L4/LB-F 组装）；
B GF(257) 方法论（检查器清单 + 输出日志 + 工件化）；C 否定性结果
目录（OS-MPMUL M1/M2、朴素自同构、裸 σ₋₁、δ=2、联合 packing
plain-嵌入、F1）；D 实现细节（7 旗标、DualSubCMUX k=2、参数表、
记号-代码映射）。
