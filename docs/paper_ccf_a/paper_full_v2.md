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

## 6 Security Under Corrected Attacks（P-3 装配；素材 = 现行 §4）

修正机制（CRYPTO'26 口径）；定参（min 130.4 ≥128，σ_G 2^−49）；
竞品重评（BatchBoot 四集 124.2/124.2/120.5/124.6 全 FAIL）；DFR
certified+经验；条件熵/间隙密钥安全（sab_pvw_state_design）。
新增：r-input 路径钥束增量 = 2 把 aut-KS（Ψ-Min，stage408），安全
估计攻击面不变。

## 7 Implementation and Experimental Evaluation（P-3 装配）

环境与纪律（同构建内部对照、6 试、dell AVX-512）；主矩阵六行
1.66–1.84×（686 时间/我方时间口径）；r 选值 8 点；r-input 门 +
噪声对账（stage403/405：0/512、0/1024，pair ≤+0.28 bit）+ benchmark
（1.23-1.44× of 2×scalar @toy，语义收益为主张）；DFR；否定性结果
实验形态。

## 8 Related Work and Conclusion

1711（内层原语，作者重叠披露）；686/TFHE/FHEW/BatchBoot（CM 类
成员 + 成本比较）；Bergerat TCHES'25（共享掩码，措辞按补审定稿）；
王晗草稿（Alg 1/2 原稿，本工作三修正件 = stage406 §3.7 差异表，
D-1 确认后定稿归属）。

## Appendices（P-4）

A 证明全文（S1/HT-4'/Ψ-Nec/N-DC/HT-7'7'8/L2 三层/L4/LB-F 组装）；
B GF(257) 方法论（检查器清单 + 输出日志 + 工件化）；C 否定性结果
目录（OS-MPMUL M1/M2、朴素自同构、裸 σ₋₁、δ=2、联合 packing
plain-嵌入、F1）；D 实现细节（7 旗标、DualSubCMUX k=2、参数表、
记号-代码映射）。
