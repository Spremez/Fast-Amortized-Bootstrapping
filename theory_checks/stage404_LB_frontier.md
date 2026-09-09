# OB-3 执行：时间-密钥前沿定理 LB-F 完整成稿

Date: 2026-09-09
义务：stage400 WS-A / OB-3；取代 stage399 §7.2 的乘积式草稿（该形式
有量纲问题，弃用——自我勘误入册）。底稿：stage398 §1.4/§3.3、
stage399 §7.1（HYB 见证）、stage401（L1/L2/L3 证明）。

---

## 一、三制式前沿定理（定稿形式）

### 1.1 记号

每消息时间 T（M_fft 口径：N 维负循环卷积 = Θ(N log N)）；
每消息分摊密钥束 K（以选择钥份数 × 单钥尺寸 s₀(λ) 计，或以
大环选择子的环尺寸计）；h+1 相位、槽数 n、间隙位宽 ρ、环维 N、
lane 数 r、gadget 深度 ℓ。H1/H3/H4/H5 同 stage401；**H2（密钥束
规模）按制式显式给出**。

### 1.2 定理 LB-F（前沿三制式）

在 H1（单项式累积）+ H3（M_fft）+ H4（间隙密钥）+ H5（均匀性）
下，按密钥预算分三制式，每制式给出匹配的上下界：

**制式 F1（标准密钥束 K = O((h+1)·ρ·s₀)，与 686 同预算）**
- 下界（stage401 定理 LB-per-phase + L3）：每消息
  T ≥ (h+1)·⌈log_a min(2^ρ,n)⌉·ℓ·N·log N，元数 a = O(1)（引理 3.4）。
- 上界（本工作构造）：T = (h+1)·ρ·ℓ·N·log N·(1+k/r)。
- **匹配至行常数 (1+k/r) → 1（r→∞）；686 为 (k+1)。**

**制式 F2（线性密钥束 K = Θ((h+1)·n·N)——大环选择子）**
- 下界：每相位 ≥ n 个门（L1 触碰，与密钥无关）⟹ 每消息
  T = Ω((h+1)·ℓ·N·log N·1)（ρ 因子消失）。
- 上界（HYB 见证，§二）：T = (h+1)·(1+log n/log N+c_ks)·ℓ·N·log N·(1+k/r)。
- 制式内匹配至常数 (1+log n/log N+c_ks)；**HYB 胜 F1 当且仅当
  ρ > 1 + log n/log N + c_ks**（§二 crossover 计算）。

**制式 F3（平方密钥束 K = Θ(n·(h+1)·s₀·n)——per-(槽,行)选择子）**
- 下界：每相位每槽 ≥ 1 门（触碰）⟹ T = Ω(ℓ·N·log N·1)——信息地板。
- 上界（构造）：keygen 为每 (槽 t, 相位 step) 预加密选择子（消息 =
  该相位的公开搬移/符号），运行时 n·(h+1) 次 EP：T = Θ((h+1)·ℓ·N·log N·1)。
  更极端：per-行选择子（把 h+1 个相位合并为单一行变换选择子，
  密钥 Θ(n²)）：T = Θ(ℓ·N·log N)——达地板。
- **F3 对所有方案对称开放（非分离轴，引理 S3'）；实用参数下密钥
  不可行（n/ρ ≈ 341× 膨胀）。**

### 1.3 推论（本工作的复杂度主张，定稿措辞）

> 在标准密钥束制式（F1，与 686 直接可比）下，本工作匹配类下界
> 且行常数最优 (1+k/r)→1；批处理轴上每消息代价 Θ(1/r) 递降至
> 1/(k+1) of 686。离开 F1 的权衡前沿（F2/F3）对所有类内方案
> 对称开放，不构成任何单方优势。

## 二、HYB 见证的完整成本账与 crossover

### 2.1 HYB（大环混合）构造回顾（stage398 §1.4）

槽变量环化：累加器 = 单个大环密文（R' = R[Z]/(Z^n+1)，维 nN，
Z 负循环 ⟹ 跨界符号自动 = S1 语义）。每间隙相位：
1. 移动 = 乘秘密单项式 Z^{v_t}：**单次大环 EP**（选择子消息为
   keygen 已知单项式——OS-MPMUL 在槽变量层的正确形态；M1 驳倒
   只适用槽阵列表示）；
2. 抽取（大环 → n 个槽 TLWE）：免费（系数抽取，同样本抽取）；
3. sub_a 扭转：n 次明文单项式乘（免费）；
4. 重打包（n 个 TLWE → 大环密文）：packing-KS，
   成本 c_ks·n·N·log N（c_ks 为钥束/数字常数）。

### 2.2 成本对比与 crossover（严格计算）

每相位（M_fft）：
- F1 蝶形：ρ·n 次 EP × N log N = ρ·n·N·log N。
- HYB：nN·log(nN) + c_ks·n·N·log N = n·N·log N·(1 + log n/log N + c_ks)。

**HYB 胜 ⟺ 1 + log n/log N + c_ks < ρ。**

c_ks 标定（I-4 部分，来自尾声实测）：full-packing KS ≈ 全管线的
3%（stage322 时代数据）⟹ c_ks ≈ 0.03·(h+1)·ρ ≈ 9（FINAL h=42,ρ=7）。

实用判定（n = N，c_ks = 9）：crossover ρ* = 2 + 9 = 11 ⟹
n/h > 2^11 = 2048 ⟹ h < n/2048：
- n = 2048: h < 1 —— 不可达；
- n = 2^15, h = 42: ρ = 9.6 < 11 —— HYB 慢；
- n = 2^17, h = 42: ρ = 11.6 > 11 —— HYB 胜（天文参数）。

**结论：实用全域 HYB 恒慢；渐近域 (n→∞, h 固定) HYB 快 Θ(ρ)
——但密钥 ∝ nN 违反 H2，作为前沿见证而非竞争构造。**

### 2.3 噪声注记（HYB 的噪声账，完整性）

HYB 每相位噪声 = 大环 EP 噪声（N 维 EP 的 n 倍系数集，每系数同
Lemma 1.7 分布）+ packing-KS 噪声：与 F1 的每槽 EP 噪声同阶
（逐系数分布相同），故 F1 的噪声分析（Lemma 1.7 × 管线递推）
对 HYB 平移适用，无新的噪声类。

## 三、与既有件的一致性核对（自检清单）

| 件 | 一致性 |
|---|---|
| stage401 LB-per-phase | F1 下界即其直接推论 ✓ |
| stage399 §7.2 乘积式 | **弃用**（量纲问题：T·K 乘积把"钥份数"与"环尺寸"两种 K 混一；本文件的三制式形式取代之）|
| stage398 A1/A2 | F1 上界 = A1；批处理渐近 = A2 ✓ |
| stage402 CM 覆盖 | 五族均 F1 制式 ✓（686/TFHE/FHEW/BatchBoot/本工作）|
| GF(257) 检查器 | S1 语义定理支撑 HYB 的"跨界符号自动"声明 ✓ |
| L1 触碰 | F2/F3 下界的唯一来源，与密钥无关 ✓ |

## 四、论文 §5.3 底稿段落（直接可并入）

*The standard-key regime (F1) captures all known implementations —
686, TFHE, FHEW, BatchBoot, and ours (Lemma CM) — and is where our
matching result lives. Dropping the key constraint reveals a two-step
frontier: pre-computed monomial selectors over the big ring (F2)
remove the log(n/h) factor at linear key cost, always losing at
practical parameters (crossover ρ* ≈ 11, i.e. n > 2^17 at h=42) but
winning asymptotically; per-row selectors (F3) reach the information
floor at quadratic key cost. Both escapes are symmetric across the
class — they bound the model, not any single scheme.*
