# 路径A：修正安全下的完整算法、实测数据与定位（2026-09-01）

> 依据：src/sab_pvw.c（算法事实逐函数核对）、stage358（真 σ+11 实测）、
> stage359（噪声实测，收割中）、eurocrypt_comparison.md（12 方案检索）、
> stage177 novelty 风险登记（主张纪律）。

## 一、修正安全下的参数集与实测数据（279 攻击模型下真 128-bit）

### 参数集（SET_2_3_2048 形状，CRYPTO'26 双维修正）

| 参数 | 值 | 安全角色 |
|---|---|---|
| 输入环 n / in_k | 2048 / 1 | 维度A 攻击面 |
| 输入密钥 | 二值稀疏 **h=41**（原 39）, σ_in=2⁻¹⁵ | T3=(log₂C(2048,41)−11−δ)/2 = **131.75 ≥ 128** |
| 输出环 N / out_k | 2048 / 1 | 维度B 攻击面 |
| 输出密钥（BSK 载体） | h_out=512 ternary, **σ_out=2⁻³⁹**（=2⁻⁵⁰·2¹¹） | 旋转预处理修正 +11 = log₂(2048)，格安全 **≥128** |
| packing 密钥 | h=256, σ=2⁻⁴⁴ | 不随 σ_out 修正（镜像标量协议） |
| 消息精度 / r / r_prec | 3-bit / 4 / 7 | r_prec 由 N/h 推导 |
| gadget | Bg=2²³(l=1), b_pack=2¹⁴(ℓ=2), t_ks=12 | 与 686 相同（未为 SQ 特化） |
| **总安全** | min(组合, 格) = min(131.75, ≥128) = **≥128** | **两维同时修正，真 128-bit** |

### 实测数据（stage358，基准机 Xeon Gold 6230R，探针协议，同场次背靠背）

| 指标 | 数值 | 证据 |
|---|---|---|
| 每 rep 中位（r=4, h=41, σ+11） | **43.5 s** | stage358 run.log t1-t3 |
| **ms/msg/lut** | **5.31**（=43.5s / 8192 slot·lane） | 同上 |
| vs stock r-lane（6.40） | **1.20×** | 同场次内部比值 |
| vs SQ r-lane（6.16） | **1.16×** | 同上 |
| vs 686 scalar ×4（跨场次估算） | ~1.28×（55.6s/43.5s） | ⚠ 跨场次，建议补同场次标量×4 |
| gate | **9/9 rep mism=0**（h=41 σ+11；全 27/27 含 h=39/σ+0） | 路径A↔SQ 交叉一致性 |
| σ 不变性 | pathA/SQ = 1.16×(σ+0) / 1.16×(σ+11, h=41) / 1.13×(σ+11, h=39) | 逐 rep 背靠背比值 |
| 噪声读数 | **stage359 收割中**（10-trial，h=41 σ+11，stock 与 pathA 双构建） | 补完后填入 |
| 内存（密钥 RSS） | ~310 MB（r=4 含 PVW 密钥） | gap_analysis Gap 3 |

外积计数（每次自举）：矩阵外积 (h+1)·ρ·n = 42·7·2048 = **602,112** 次，
每次同时更新 (1+r)=5 个多项式（1 掩码 + 4 lane 体）→ 等效标量外积 4×602,112。

## 二、路径A 完整自举算法（贴 src/sab_pvw.c 实现）

### 记号

- `PVW_TMLWE`：共享掩码累加密文 (a | b₀ | … | b_{r−1})，1 个掩码 + r 个体（每体=1 lane）
- `MAT_TRGSW`：矩阵选择子，(1+r)·ℓ 行，行 = 共享掩码密文下对选择比特的 TRGSW 型加密
- `MV-EP(C, c)`：矩阵外积 = Σ_{i≤r, j<ℓ} decomp_j(cᵢ) ⊗ C[i·ℓ+j]（稠密乘 (1+r)×(1+r)ℓ）

### Algorithm 1 — r-lane 摊销稀疏自举（矩阵形式）

```
输入: in = (a, b) ∈ TRLWEₙ（稀疏二值密钥 s, h=41, σ_in=2⁻¹⁵ 下）
      tv ∈ PVW_TMLWE（r=4 个 LUT 载荷的平凡加密）
      密钥: C[step][bit] MAT_TRGSW（step∈[0,h], bit∈[0,ρ)），aut₋₁ KS，
            packing KS ×r，hw-reducing KS
输出: out[0..r−1] ∈ TRLWEₙ —— n=2048 个槽位 × r 个 LUT 的自举读出

 1  // Setup（每槽位初始旋转）
 2  for i ∈ [0, n):
 3      acc[i] ← X^{torus2int(b[i]+2^{63−p}, log₂2N)} · tv
 4  // 盲旋转（对整个 n 累加器数组做一次）
 5  ā[i] ← torus2int(a[i], log₂2N)  ∀i ∈ [0, n)
 6  for step ∈ [0, h):
 7      acc ← MonomialMul(acc, C[step])          // Algorithm 2
 8      SubA(acc, ā)                              // 减去当前数位贡献
 9                                                // (include-zero 快路径: 数位=0 时跳过整个 MV-EP)
10  acc ← MonomialMul(acc, C[h])                  // 终归一化步
11  // 读出尾声（每 lane 独立）
12  for lane ∈ [0, r):
13      ext[i] ← ExtractConst(acc[i], lane)  ∀i ∈ [0, n)     // 逐槽常数项抽取
14      packed ← FullPackingKS(ext, packing_ks[lane])         // n 个样本 → 1 个多项式（摊销读出）
15      out[lane] ← KeySwitch(packed, hw_reducing_ks)         // 回输入密钥域
```

### Algorithm 2 — MonomialMul（整个累加器数组的蝶形旋转）

```
输入: acc[0..n−1]（乒乓双缓冲），选择子比特片 C[0..ρ−1]（ρ=r_prec=7）
1  for bit ∈ [0, ρ):  power ← 2^bit
2      // 换位槽（负旋转，下标 n−power+j 落在环的负侧）
3      for j ∈ [0, power):
4          rot ← X^{−1}·acc[in][n−power+j]                     // 自同构 + aut₋₁ KS
5          (acc[out][j], acc[out][j+power]) ←
6              DualSubCMUX(acc[in][j], rot, acc[in][j+power], C[bit])
7      // 直达槽（正旋转）
8      for j ∈ [power, n−power):
9          acc[out][j+power] ← CMUX(acc[in][j+power], acc[in][j], C[bit])
10     swap(in, out)

CMUX(x, y, C)      = x + MV-EP(C, y − x)                       // 选择性旋转
DualSubCMUX(p,rot,q,C):
    (rot−p, rot−q) ← DualSub(rot, p, q)                        // 一次 AVX-512 向量化双减
    out₁ ← p   + MV-EP(C, rot−p)                               // 两个输出共享同一次
    out₂ ← q   + MV-EP(C, rot−q)                               // X^{−1} 旋转与调度
```

每 bit 外积数 = n（dual-sub 下 n−power），MonomialMul 共 ρ·n = 14,336 次 MV-EP；
Algorithm 1 全程 (h+1)·ρ·n = 602,112 次。

### 路径A 的 7 个融合旗标（工程贡献层，映射到算法行）

| 旗标 | 优化点 | 算法行 |
|---|---|---|
| `MAT_TRGSW_AVX512_SUB_DECOMP` + `_DFT_DIRECT` | 分解数位行直接生成 DFT 谱（跳过中间环面物化），r 特化 AVX-512 核 | MV-EP 内部 |
| `MAT_TRGSW_AVX512_SMALLR_SPECIALIZED` | 小 r（≤4）专用稠密乘核（全展开） | MV-EP 内部 |
| `SAB_PVW_SUB_DECOMP_FUSION` | 减法 y−x 融进分解输入（CMUX_from_diff） | CMUX |
| `SAB_PVW_DUAL_SUB_CMUX` | 一对蝶形输出共享一次 X⁻¹ 旋转 + 一次向量化双减 | Alg2 L4-6 |
| `SAB_PVW_BACKEND_FROM_DFT_ADD` | 逆 FFT 与 +addend 融合，结果直接落环面 | CMUX 物化 |
| `SAB_PVW_SUBA_INCLUDE_ZERO_COEFF_ONE_FAST` | 数位为 0/1 的已知选择子跳过 MV-EP | Alg1 L8 |

## 三、与 686 scalar 的区别（逐项）

| 维度 | 686 scalar（已发表） | 路径A（本文） |
|---|---|---|
| 累加器 | n 个 TRLWE（单体） | n 个 PVW_TMLWE（1 掩码 + r 体共享） |
| 选择子 | TRGSW（2ℓ 行） | MAT_TRGSW（(1+r)ℓ 行） |
| 外积 | `decomp⊗TRGSW` 标量外积 | 稠密矩阵外积 (1+r)×(1+r)ℓ |
| 一次盲旋转服务 | n=2048 个槽位 × 1 LUT | n=2048 槽位 × **r=4 LUT**（摊销 ×r） |
| 外积次数/自举 | (h+1)ρn = 602,112（标量） | 同为 602,112（矩阵）→ **每 lane 摊销 ÷4** |
| 读出尾声 | 单次 extract/pack/KS | 每 lane: extract + packing KS；共享 hw-KS |
| 数据流工程 | 逐外积物化分解与逆 FFT | 7 旗标融合生命周期（谱域驻留、双减共享、零数位跳过） |
| 噪声结构 | 每 EP 注入选择子噪声 | **逐 lane 等同 scalar**（同选择子、同调度）→ 安全修正同构适用 |
| 修正后速度 | 6.79 ms/msg（h=41 σ+11 复测） | **5.31 ms/msg/lut**（1.20× vs stock r-lane） |

**算法级新东西**：共享掩码累加器使一次选择子分解/一次谱域乘法同时推进 r 个 LUT 体
（外积成本 ∝ (1+r)ℓ 行而非 r×2ℓ 行独立分解）；蝶形 MonomialMul 的 dual-sub 配对代数；
include-zero 稀疏跳过。**算法级不新的东西**（诚实声明，见 novelty 风险登记）：
PVW 打包是既有技术（BGH2012）；"共享掩码 r-body"有先例（Bergerat CM, TCHES'25）——
本文区别是**用矩阵外积批量 686 的摊销稀疏盲旋转**并在修正安全下给出完整实测。

## 四、SQ 的创新性与相关工作

### SQ 是什么（一句话）
把累加器搬到 Q=2^q 尺度、选择子按 Bg_bit=q 加密 → **外积中 gadget 分解被消除**
（消息路径精确 = Theorem 1），选择子噪声以 ∆=Q²/T=2^{2q−64}=2⁻³² 落入累加器（Lemma 1）。

### 创新点（相对最近邻 1711 / Wang, ePrint 2025/1711 squared gadget）
1. **1711 是 gate 级单比特 FHEW-to-FHEW**（4.8 ms/gate，无摊销、无稀疏密钥、无批量）；
   SQ 把尺度量化外积**移植进 686 的摊销稀疏盲旋转**——两者的调度结构完全不同
   （1711 无 (h+1)ρn 外积树、无 n 累加器数组、无 packing KS）。
2. **Theorem 1 + Lemma 1 在摊销设定下重推导**：多累加器数组 + 稀疏调度下的精确性
   与 ∆ 抑制，1711 未涉及。
3. **σ 硬化推论（本文独有）**：∆ 抑制使 SQ 的主导噪声项对 σ_out 不敏感 →
   CRYPTO'26 修正（σ+11）近零代价、σ+15 仍保余量（59.53<60）。**没有任何已检索工作
   把尺度量化外积与安全修正余量联系起来**（12 方案表：全部未修正）。
4. **形态可移植性**：SQ 核在 scalar 与 mat(r-lane) 两种形态都实现并实测
   （SQ r-lane 复用同一 AVX-512 稠密乘核）；速度收益 ∝ 1/r 但硬化收益双形态保持。
5. **否定性结果**：SQ 与融合旗标结构互斥（同一分解/FFT 生命周期，构建验证）——
   对社区有独立价值。

### 相关工作定位表（12 方案检索结论，详见 eurocrypt_comparison.md）

| 最近邻 | 关系 | 本文如何区分 |
|---|---|---|
| 1711 (ePrint'25) | SQ 理论来源（squared gadget） | gate级→摊销稀疏自举；+定理/引理；+σ硬化推论 |
| Bergerat CM (TCHES'25) | 共享掩码 r-body 先例 | 引用并区分：矩阵外积批量 vs 共享掩码格式；不声称首创 |
| 686 (CCS'25) | 基线（仅 scalar 算法） | r-lane 矩阵化是本文贡献；同机复测+首修正其安全 |
| BatchBoot (USENIX'26) | 最快竞品（无代码） | 引用其同机 686 数（8.09）；3.2× 跨机差作方法论论据 |
| 068/NTTRU, Xiang'26 | 稀疏/摊销竞品（无代码） | 引用级+标注未修正安全 |
| De Micheli (PKC'24), Liu-Wang (Asiacrypt'23) | 理论 | 渐近复杂度对比 |
| CRYPTO'26 / ex-279 | 攻击来源 | 本文首个在多攻击模型下修正摊销自举参数 |

### 主张纪律（novelty 风险登记约束）
- ✗ 不声称"首个共享掩码"（Bergerat 先例）　✗ 不声称 PVW 打包新颖（BGH2012）
- ✗ AVX-512 矩阵核作为"数学贡献"（只能是 systems/ablation 主张）
- ✓ 路径A 主张 = "686 摊销自举的首个矩阵形式实现 + 修正安全下的完整实测 + 工程战役"
- ✓ SQ 主张 = "尺度量化外积 × 摊销稀疏自举（首个）+ σ 硬化余量独占（首个）"

## 五、待填项

- stage359 噪声读数（stock r-lane vs pathA，h=41 σ+11，10-trial）→ 填入第一节表格
- 同场次标量×4 计时（免跨场次噪声的 "vs 686×r" 列）
