# Wang Han 独有贡献的融合决策分析

Date: 2026-09-08
问题：五项独有贡献各自的融合方式（互补/正交/替代），以及对论文理论与实验的实际影响。

---

## 一、逐项分类与融合方案

### 1. Lemma 1.7 完整次高斯推导 → **互补（必须融合，立即使论文更强）**

**关系**：与我们的 Thm 2 描述**同一对象**（尺度化外积的噪声增长），但深度不同。

| | Wang Han Lemma 1.7 | 我们的 Thm 2 |
|---|---|---|
| 形式 | 一般次高斯框架：γ' = √(Q²/T²·γ₁² + γ₂² + Q²/T²·γ₃² + γ₄²) | 具体指数：σ·2^{q+3.5} |
| 方法 | 纯理论推导（Pythagorean 可加性 + 四项分解） | 实测标定（三档 σ 对账 ±1 bit） |
| 覆盖 | 任意 (k, r, ℓ, 秘密分布) | SET_2_3_2048 具体参数 |

**融合方式**：论文 §3.5 以 Lemma 1.7 为主引理（形式更一般），Thm 2 作为
**推论**（"instantiating Lemma 1.7 at q=16, N=2048 gives σ·2^{q+3.5},
verified within ±1 bit across three σ tiers"）。

**效果**：Thm 2 从"实测标定"升格为"理论推导 + 实测验证"——**论文理论深度
立即提升一个档次**。这是融合的最大单一收益。

### 2. Cor 1.8 应用特化 → **互补（直接引用为推论）**

**关系**：Lemma 1.7 在自举场景（monomial 对角 + 三元秘密 + 均匀分布 +
∆Q²<T）的简化闭式。与我们的 Thm 5（噪声同阶性）和 Thm 6（p 域）覆盖
同一场景。

**融合方式**：论文 §3.5 引用 Cor 1.8 作为噪声界的应用特化，然后我们的
Thm 6（q ≥ p+10）在其上推导精度域边界。

**效果**：省去重复推导，使 §3.5 结构更紧凑。

### 3. Hom-Tr 理论构造 → **替代设计（设计空间的一个选项，非必需）**

**关系**：与我们的明文 sub_a / sub_a_ga 是**同一功能的三种实现**。

| | 明文单项式乘 | sub_a_ga | Hom-Tr |
|---|---|---|---|
| 机制 | 公开系数旋转 | 双自同构+外积 | 固定子群迹提取 |
| 噪声 | **零** | 2 KS + 1 EP | KS + 舍入 + 模数消耗 |
| 速度 | **最快** | 最慢 | 中间（理论） |
| 秘密类 | binary/ternary | **一般稀疏** | 理论最通用 |
| 双模数兼容 | ✓（SQ 已处理） | ✓ | **原生设计** |

**关键判断**：
- 对 **binary 密钥**（我们全部六行主矩阵的设定）：明文乘已最优，Hom-Tr
  **不会带来改善**（引入额外噪声且更慢）
- 对 **一般稀疏**（ρ-SAB）：sub_a_ga 已实现且验证，Hom-Tr 理论上可能
  更优雅但**未证实在 C 实现中更快**
- 对 **双模数 T>Q 场景**：Hom-Tr 原生设计，可能有优势——但我们当前
  不使用显式双模数

**融合方式**：论文 §3.4 的 sub_a 设计空间表已覆盖（4 后端含负对照）。
Hom-Tr 作为理论候选保留在表中，标注 "reference variant derived; C
implementation pending semantic confirmation"。

**是否需要实现**：**非阻塞项**。论文可以只报告已验证的三种路径 +
Hom-Tr 作为 "an alternative design that we leave for future work"。
如果 Wang Han 确认语义且实现后有优势，可在 camera-ready 版本补充。

### 4. Slot 置换（私有线性操作）→ **真正正交（引用即可，无需融合）**

**关系**：这是 Vec-MLWE/CM 格式的一个**能力**（在外积中同时置换 lane），
不影响自举的正确性或性能。我们不使用也不需要此功能。

**应用场景**：私有集合交集（PSI）、安全多方计算中的私密线性变换——
BatchBoot 的 PSI 应用可能用到类似功能。

**融合方式**：论文 §6 相关工作中一段话：
> "The CM format of [Ber25] and the Vec-MLWE of [WLL25] support private
> slot permutation within the external product, enabling applications
> such as PSI. Our matrix bootstrapping does not exploit this capability,
> which is orthogonal to the sparse-key adaptation and security
> recalibration we address."

**效果**：正确引用对方贡献，不混淆为我们的工作。

### 5. RNS ModUp/ModDown → **真正正交（实现层优化，不适用于当前平台）**

**关系**：这是将双模数 T>Q 算术映射到 RNS（Residue Number System）
表示的桥接操作，用于硬件加速。我们的实现用 spqlios FFT（实数域卷积），
不使用 RNS。

**融合方式**：论文不展开（我们的实现路径不同）。可在 §3.1 密码系统
定义后一句话：
> "The dual-moduli arithmetic can be implemented via RNS with ModUp/
> ModDown operations [WLL25, §1.4]; our implementation uses FFT-based
> convolution in the 64-bit torus."

---

## 二、Algorithm 1 和 Algorithm 2 是否已实现？

### 答案：是——但有一个细微差别

**Algorithm 1 (P-MPMUL)**：✅ **完全已实现**。
- Wang Han 的伪代码 ↔ `sab_pvw_RGSW_monomial_mul_state`（`sab_pvw.c:861`）
- 逐位蝶形、环绕/直达槽、(candidate−current)⊙Enc(bit)+current 逐行同构
- 外积原语：他的 ⊡（scale-based）↔ 我们的 `mat_trgsw_mul_pvmtmlwe_DFT`
  （SQ 核，数学同构，实现路径不同）

**Algorithm 2 (Packing BIN-SAB)**：✅ **除第 9 行（Hom-Tr）外完全已实现**。
- 初始 setup ↔ `sab_pvw_setup_tv_xb`
- h+1 次 P-MPMUL ↔ `sab_pvw_sparse_mul_binary` 系列
- 第 9 行 Hom-Tr ↔ 我们用**明文单项式乘**替代（binary 路径，更快）
- 提取 + KS ↔ `sab_pvw_extract_tlwe_lane` + packing KS

**细微差别**：
| | Wang Han 的 ⊡ | 我们的 SQ |
|---|---|---|
| 模数 | 显式 T > Q（两个模数） | 隐式（64-bit torus + q-bit 量化） |
| 外积 | C·c mod T → ⌊·Q/T⌉ mod Q | 整数卷积 mod 2^64 → 移位 >> (64-q) |
| 数学 | 同一机制 | 同一机制 |
| 实现 | 理论框架 | C 代码 + FFT |

即：**算法层面**我们实现了他的 Algorithm 1/2（同一数学结构）；**密码系统
表示层面**我们用了等价但不完全相同的实现路径（隐式 vs 显式双模数）。
论文中用他的形式化记号（T/Q）写理论，用我们的实现细节（SQ/spqlios）写
实验——两者自然衔接。

---

## 三、融合后理论与实验的预期改善

| 贡献 | 融合后理论改善 | 融合后实验改善 |
|---|---|---|
| Lemma 1.7 | **显著**：Thm 2 从实测升格为"推导+验证" | 无直接影响 |
| Cor 1.8 | **中等**：省去重复推导 | 无直接影响 |
| Hom-Tr | **微小**：设计空间表多一个理论选项 | **潜在**：如实现后对某秘密类更快 |
| Slot 置换 | **零**（正交） | **零**（不使用） |
| RNS ModUp/Down | **零**（正交） | **零**（不同实现路径） |

**总结**：融合的最大理论收益来自 Lemma 1.7/Cor 1.8（使噪声分析从工程
级升格为密码学级）。其余三项为正交或替代关系，融合不改变当前结论。

---

## 四、非正交内容的取舍建议

**需要综合讨论的唯一项**：外积原语的表示选择（显式 T/Q vs 隐式 64-bit torus + q-bit 量化）。

**建议**：论文理论层用 Wang Han 的 T/Q 记号（更规范），实验层用我们的
SQ 实现描述（更贴近代码），两者在 §3.1 中明确等价性：

> "The scale-based external product of [WLL25] operates under explicit
> dual moduli T > Q. Our implementation instantiates this at T = 2^64,
> Q = 2^q (q = 16), which is mathematically equivalent: the Q/T rescaling
> corresponds to a right-shift by (64 - q) positions in the 64-bit torus."

这一段消除表示歧义后，全文无其他需要取舍的非正交项。
