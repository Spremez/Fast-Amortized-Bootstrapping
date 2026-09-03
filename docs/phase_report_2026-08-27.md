# 阶段性汇报：稀疏摊销自举的加速研究（截至 2026-08-27）

汇报基线 commit：`6bea3a2`（main）；SQ 线分支 `codex/candidate-sq-scale-sab` @ `e77f502`；Candidate D 治理 worktree `candidate-a-star-cycle-gate`（controller `efc47d9`）。
目标 venue：USENIX Security 2027（主）/ CCS 2027（备），降级路线 TCHES。
单一事实源：`docs/paper_ccf_a_master_plan.md`、`docs/goal_ccf_a_paper.md`。

---

## 0. 执行摘要（TL;DR）

本项目在 ePrint 2025/686（Guimarães–Pereira, CCS'25，MOSFHET 实现）的稀疏摊销自举（Sparse Amortized Bootstrapping, SAB）之上做系统加速研究，沿三条技术线推进，论文定位为"实践更快的摊销自举"：

| 线 | 一句话结论 | 状态 |
|---|---|---|
| **A. MAT-SAB（r-lane PVW 矩阵外积）** | 双路 Xeon Gold 6230R 服务器 11/11 参数行全部通过，完整自举摊销吞吐相对重复标量 SAB **1.5152×–1.8271×**（10 样本/行，噪声 0 失败），密钥开销 ≤1.07× | ✅ **收官**（主结果就绪） |
| **B. SQ（尺度量化外积）** | 用 Q=2^q 量化+重缩放取代 gadget 分解，内核比标量快 **−4.5%（中位）/−7.3%（min-of-9）**；在恢复 2026/279 稀疏密钥 15 bit 安全边际的参数下 **SQ 通过而 stock 标量失效**（否定性结果：σ 单旋钮不可行） | ✅ 本地闭环，待服务器确认 |
| **C. D4（LUT 晚绑定算子 SAB）** | D0–D3 治理门全过（含**强制重随机化定理**这一新理论发现）；投影相对 A 线再加速中央 **1.86×** / 悲观 **1.46×**；实现 v11 的 bind 构造已单元级精确，剩 1 个已隔离的噪声触发泄漏（负号乘子 × 通道噪声）距等价 gate 一步 | 🔄 距 gate 1–2 会话 |
| D. F1（MAT-EMPmul 融合） | 纸面投影 2.36–2.6× over scalar | 备胎，B/C 受阻才启动 |

**论文判定**（master plan §四）：A+B 已构成可投稿主体（速度 1.52×+、安全闭环、含诚实否定性结果）；C 闭合则升级为三贡献论文。

---

## 1. 项目定位与背景

### 1.1 基线协议

基线是 ePrint 2025/686 的**稀疏摊销自举**：输入一个 RLWE 密文（含 N 个消息系数），一次"盲旋转式"调度同时把 N 条 LUT 求值做进一个 TRLWE 累加器，再逐槽提取，从而把 N 次独立程序自举摊销为一次调度。上游实现为 MOSFHET 库（AVX-512/VAES 优化）。

参数族 `SET_X_Y_Z`：X-bit 任意函数 / Y-bit negacyclic 函数 / Z 条消息（Z = N），各字段精确含义见 1.2 节。核心调度代价（binary 密钥）为：

> **H = (h+1)·ρ·N 次选择子外积**，h 为稀疏密钥汉明重，ρ = r_prec 为位置差精度位。
> 例：`SET_2_3_2048`（N=2048, h=39, ρ=7）→ H = 40·7·2048 = **573,440**。

上游不可变锚点（`docs/cost_model.md`、`repro/baseline_registry.yaml`）：本地 WSL（i7-11700）标量 SAB 完整自举 `SET_2_3_2048` 为 16.58 s ≈ 5.22 ms/消息；原论文摊销时间（BatchBoot 作者代测，Xeon Gold 6258R）Boot2/4/6/8 = 8.09/8.65/8.92/57.34 ms。

### 1.2 参数与记号速查

**参数集命名 `SET_X_Y_Z_rR`**（README + main.c:1059-1093 target 表）：

- **X**：任意函数（arbitrary LUT）模式下的每条消息位宽（bit）；
- **Y**：negacyclic 函数模式下的消息位宽（= 输出消息精度 prec，见原论文 Remark 7.1）；
- **Z**：一次自举打包的消息条数 = 输入环维 N（in_N）；
- **_rR 后缀**（本仓矩阵行命名）：r = PVW 累加器打包的 lane 数，每 lane 携带一个独立 LUT（R∈{2,4}）。

例：`SET_2_3_2048_r4` = 2-bit 任意函数 / 3-bit negacyclic 函数、N=2048 条消息、r=4 lane。

**E1 矩阵六个参数集的取值**（binary 密钥，来源 `main.c` target 表与 `docs/cost_model.md`）：

| 参数集 | N=in_N | out_N | h | ρ=r_prec | prec | Bg | H=(h+1)·ρ·N | BatchBoot 对标 |
|---|---:|---:|---:|---:|---:|---:|---:|---|
| SET_2_3_2048 | 2048 | 2048 | 39 | 7 | 3 | 2^23 | 573,440 | Boot2 |
| SET_2_3_4096 | 4096 | 2048 | 32 | 8 | 3 | 2^23 | 1,081,344 | — |
| SET_4_5_2048 | 2048 | 2048 | 42 | 7 | 5 | 2^23 | 616,448 | Boot4 |
| SET_4_5_4096 | 4096 | 2048 | 34 | 8 | 5 | 2^23 | 1,146,880 | — |
| SET_6_7_4096 | 4096 | 2048 | 33 | 9 | 7 | 2^23 | 1,253,376 | Boot6 |
| SET_8_9_4096 | 4096 | **8192** | 34 | 9 | 9 | 2^22 | 1,290,240 | Boot8 |

注：仅 SET_8_9_4096 的输出环维 out_N=8192（其余 2048），这是 8-bit 行内存峰值最大（本地 OOM）的来源；其 gadget 基亦降为 2^22。

**算法符号（全报告通用）**：

| 符号 | 含义 |
|---|---|
| r | lane 数（PVW 累加器 body 数，每 lane 一个独立 LUT） |
| N (in_N) / out_N | 输入 RLWE 环维（= 消息条数）/ 输出 TRLWE 环维 |
| h | 输入稀疏秘密钥的汉明重 |
| ρ (r_prec) | 盲旋转位置差精度位；H=(h+1)·ρ·N = binary 完整自举的选择子外积总数 |
| k / l / Bg | TRLWE mask 维（恒 1）/ gadget 分解长度（恒 1）/ gadget 分解基（2^23，8-bit 行 2^22） |
| q | SQ 线尺度量化的量化格位数（Q=2^q），独立设计旋钮 |
| bg / L | D4 v11 bind 的数位分解基（2^32）与层数（2）——注意与选择子 gadget 的 Bg 无关 |
| g (Γ) | 算子通道数（D 线基组 Γ={id, τ₋₁}，g=2）；τ₋₁: X ↦ −X⁻¹ |
| σ_in / σ_out | 输入 / 输出误差标准差（torus 单位，如 2^-50） |
| σ_flood | 绑定后重随机化洪水参数（2^-8） |
| β | 晚绑定噪声放大因子，β=√2·‖ΔF‖₂（N=2048 任意 2-bit LUT 最坏 β=32） |
| Δ | 明文编码尺度（torus 编码 F_Z → Δ·F_Z） |
| KEY=BINARY/TERNARY/ARBITRARY | 输入秘密钥分布（本报告矩阵全部 BINARY；ternary/arbitrary 在 P2） |
| spqlios / spqlios_avx512 / ffnt | FFT 后端：AVX2+FMA / AVX-512+VAES（服务器）/ ffnt 校验后端 |
| 本地 / 服务器 | WSL2 i7-11700@2.5GHz（16 线程 12GB）/ 双路 Xeon Gold 6230R@2.1GHz（104 线程 251GB） |
| T = 2^64 | torus 模（ℤ/2^64），消息经尺度编码进 TRLWE 相位 |

### 1.3 研究治理框架（方法论贡献）

全程执行 commit-pinned 的准入治理（研究契约 `docs/superpowers/specs/2026-07-16-ccs-usenix-mat-sab-research-contract-design.md`）：

- 每个声明必须有确定性重放 runner（隔离 clone + `python -I -S`），输出与 git blob 逐字节比对；
- 文献以 SHA256 哈希绑定入库（`literature/candidate_d_source_registry.json`，9 源全文审计）；
- **负控制强制**：每个被移除/因子化的项必须有精确负控制实验；
- **声明红线**（claim matrix，`docs/pvw_mat_sab_claim_matrix_stage339.md`）：不支持理论最优、compact selector 安全性、全参数泛化、未核文献新颖性；投影数字一律标注"投影"；
- scalar 路径为不可变 oracle，新路径全部走显式 feature flag（默认 false）。

---

## 2. 算法设计（论文级规范：伪代码、命题与证明）

本章以 ePrint 2025/686 的算法风格为准：算法块给 Input/Output 行 + 行号 + 行内注释；每条结果采用 686 的"正确性 + 噪声 + 复杂度"三合一引理模板，并附证明与仓库证据链（标注"依据"）。先精确回顾基线（算法 1–2、引理 2.1），再给出三线改动（算法 3–8，命题/定理 2.2–2.10）。

### 2.0 记号（对齐 686 §2 与本仓实现）

- 686 用整数环 Z_q 记法；本仓 MOSFHET 实现为 64 位 torus T = ℤ/2^64（即 q = 2^64），两者在 q=2^64 下同构，下文混用并注明。
- 多项式环 R = ℤ[X]/(X^N+1)（N 为 2 的幂），T_R = T[X]/(X^N+1)；输入密文环 R_Y = ℤ[Y]/(Y^n+1)，n = in_N。
- TRLWE 样本 (a, b) ∈ T_R^k × T_R，**相位** φ(c) = b − ⟨a, s⟩ = b − Σ_i a_i·s_i；消息经尺度 Δ 编码入相位（对应 686 的集合记法 R_q LWE_s(Δm, E)）。
- TRGSW：gadget 分解基 β = Bg、长度 l，层权重 h_d = 2^{64−(d+1)·Bg}（d < l）；类型记 R_q GSW_s^ℓ(m, E)（686 §2.1）。
- 高层操作（686 §2.1 + 本仓实现）：
  - **CMUX**(y, x, C) = y + C·(x − y)，选择子 C 加密 bit；
  - **自同构** τ₋₁: X ↦ X^{2N−1}（即 X ↦ X^{−1}），实现 = 系数置换 + 密钥切换（FHE.Automorphism）；
  - **明文单项式乘** MultPtxt(X^{±a})：零噪声（‖X^{±a}‖₂ = 1，686 Lemma 4.1 论证）；
  - **提取** Extract_0：取 TRLWE 的 b[0]（与 a[i][0]，含负循环反转）为 TLWE——for free（686 §2.2）。
- 稀疏密钥（686 §2 引 [CHK+17]）：s ∈ S_{n,h,1}（binary），非零位置集 idx(s) = (j̃_0 < … < j̃_{h−1})；**位置差调度** d = diff(s)：d_0 = −j̃_0，d_t = j̃_{t−1} − j̃_t（1 ≤ t ≤ h−1），d_h = −j̃_{h−1}；B = 2^ρ 为 |d_t| 上界（ρ = r_prec 为本仓术语，对应 686 的 log B）。
- **独立性启发式**（686 p.8 命名块）：本文与 686 一致，所有次高斯噪声界挂靠"线性组合中各 RLWE 噪声系数独立且集中"的假设。

### 2.1 基线：盲旋转蝴蝶与 bin-SAB（算法 1–2）

```text
Algorithm 1  MonomialMul —— 同态乘 X^e（盲旋转蝴蝶；标量与 A 线共用同一槽位几何）
Input : 槽阵列 P = (P_0, …, P_{n−1})，P_j 为一个累加器密文（标量：TRLWE）
Input : 位选择子 C_i ∈ R_q GSW(e_i, E_G)，0 ≤ i < ρ，其中 e = Σ_{i<ρ} e_i·2^i
Input : 自同构 KS 密钥 ksk_{−1}（τ₋₁: X ↦ X^{2N−1}）
Output: P′ 满足 φ(P′_{(j+e) mod n}) = X^e·φ(P_j)，回绕项经 τ₋₁ 吸收 X^N = −1
1  for i <- 0 to ρ−1 do            /* 位序 LSB 起；每 bit 换乒乓缓冲 */
2      p <- 2^i
3      for j <- 0 to p−1 do          /* 环绕槽：目标 j < 2^i，源 (j−p) mod n 回绕 */
4          P′_j <- NCMUX(P_j, P_{n−p+j}, C_i)
5      for j <- p to n−1 do          /* 直连槽：内容上移 p */
6          P′_j <- CMUX(P_j, P_{j−p}, C_i)
7      P <- P′
8  return P
   其中 NCMUX(y, x, C) = CMUX(y, τ₋₁(x), C)
```

实现级注记（`src/sparse_amortized_bootstrap.c:226-246`）：(i) 选择子只加密**纯 bit**（`trgsw_monomial_sample(bit, e=0)`），X^{2^i} 的环乘效应完全由槽位几何（源/目标下标差）实现；(ii) 环绕判据 = 目标槽 j < 2^i；(iii) 总位移 = Σ e_i·2^i 逐位条件叠加。686 论文 Algorithm 1（MPmul）与之逐行对应：其环绕分支先做 X ↦ X^{−1} 自同构再 CMUX，与本实现的 NCMUX 同构。

```text
Algorithm 2  bin-SAB —— 稀疏摊销自举基线（binary 密钥；686 Algorithm 2 的实现级精化）
Input : RLWE (a, b) ∈ R_Y²，b(Y) = a(Y)s(Y) + e(Y) + m(Y)  mod ⟨Y^n+1, 2^N⟩，s ∈ S_{n,h,1}
Input : 蝴蝶选择子 C_{t,i} ∈ GSW(bit_i(d_t), E_G)，0 ≤ t ≤ h、0 ≤ i < ρ（d = diff(s)）
Input : ksk_{−1}；test 向量 t_0, …, t_{n−1}（槽 j 的 LUT 编码，686 §2.2）
Output: c_j ∈ LWE(f_j(m_j) + ε_j)，0 ≤ j < n
1  for j <- 0 to n−1 do P_j <- X^{⌊b_j + 2^{−(bp+1)}⌉} · t_j    /* setup：平凡编码 + 半 ulp 偏移 */
2  for t <- 0 to h−1 do
3      P <- MonomialMul(P, (C_{t,i})_i, ksk_{−1})              /* 乘 X^{d_t}：ρ 轮蝴蝶 */
4      for j <- 0 to n−1 do P_j <- X^{−ã_j} · P_j              /* sub_a：公开单项式，零噪声 */
5  P <- MonomialMul(P, (C_{h,i})_i, ksk_{−1})                  /* 最终旋转（后无 sub_a）*/
6  for j <- 0 to n−1 do c_j <- Extract_0(P_j)
7  return (c_0, …, c_{n−1})
   其中 ã_j = ⌊a_j⌉ mod 2N（模切换，src/sparse_amortized_bootstrap.c:333-346）
```

累计效果：每槽相位乘 X^{φ_j}，φ 为 b − a·s 的指数版本（686 Eq.(3) 的链式重写）；setup 的半 ulp 偏移 2^{−(bp+1)} 保证取整偏向一侧（`setup_tv_xb`，SAB.c:359-367）。

**引理 2.1（基线噪声与复杂度；即 686 Lemma 4.1）** 设算法 2 输入的选择子噪声 E_G、KS 噪声 E_ksk、test 向量噪声 E_T，则输出为 E_out-次高斯：

> E_out ≤ √( (h+1)·ρ·( ℓNβ²E_G² + N·ℓ²_ksk·β²_ksk·E²_ksk ) + E_T² )

且共执行 **H = (h+1)·ρ·n 次选择子外积**（binary；SET_2_3_2048 为 573,440）。证明见 686 p.14（h+1 次 MPmul 递推 + 明文乘零增长）；本仓在 MEASURE_NOISE 插桩下逐阶段复现（SAB.c:292-311）。

### 2.2 A 线 MAT-SAB：r-lane PVW 矩阵自举（算法 3–5）

**改动点总述**：算法 5 = 算法 2 的**三处替换**——密文类型（单体 TRLWE → 共享 mask 的 r-body PVW）、选择子原语（标量 TRGSW 外积 → 对角 MAT_TRGSW 矩阵外积）、提取（单系数 → 逐 lane 取系数）；**调度面（循环结构、蝴蝶几何、sub_a、最终旋转）逐位不变**。

**密文与密钥**：PVW_TMLWE c = (a^{(0..k−1)}, b^{(0..r−1)})——全部 lane 共享 mask a，lane-q 相位 φ_q(c) = b^{(q)} − Σ_i a^{(i)}·s_i^{(q)}（`pvmtmlwe_phase`，pvwtmlwe.c:391）。选择子为 (k+r) 体上的 MAT_TRGSW（rows = l·(k+r)，mattrgsw.c:170）。

```text
Algorithm 3  对角 MAT_TRGSW 选择子加密（keygen 核心；mattrgsw.c:238-267）
Input : PVW 输出密钥族 s^{(0..r−1)}；gadget (β = Bg, l)；明文 bit e ∈ {0,1}
Output: M ∈ MAT_TRGSW(e, E_G)（加密 diag(e, …, e)）
1  rows <- l·(k+r)；对每行 M[row] <- fresh PVW_TMLWE(0)        /* 均匀 mask，b = a·s + err */
2  for d <- 0 to l−1, j <- 0 to k−1 do  M[j·l+d].a[j][0] <- M[j·l+d].a[j][0] + e·h_d
3  for d <- 0 to l−1, q <- 0 to r−1 do  M[(k+q)·l+d].b[q][0] <- M[(k+q)·l+d].b[q][0] + e·h_d
4  return M      /* 明文纯 bit 挂指数 0，只出现在对角（分量 j ↔ 行 j）位置；h_d = 2^{64−(d+1)Bg} */
```

```text
Algorithm 4  MatExtProd —— 一次选择子事件（mattrgsw.c:827-927）
Input : C ∈ MAT_TRGSW(m·X^e, E_G)（算法 3 的对角结构）；c ∈ PVW_TMLWE(·, E)
Output: c′，每 lane 满足 φ_q(c′) = m·X^e·φ_q(c) + ε_q
1  for row <- 0 to l(k+r)−1 do dec[row] <- DigitDecomp(c)[row]  /* 分解作用在输入 c 的全部 k+r 个分量 */
2  for row <- 0 to l(k+r)−1 do D̂[row] <- FFT(dec[row])
3  for comp <- 0 to k+r−1 do                                   /* dense 累加：每个输出分量收到全部行的贡献 */
4      Ô_comp <- Σ_row D̂[row] · Ĉ[row][comp]                   /* DFT 域点乘 */
5      c′[comp] <- IFFT(Ô_comp)
6  return c′
```

```text
Algorithm 5  MAT-SAB（主算法）＝ 算法 2 的三处替换（sab_pvw.c:1140-1335）
1  类型替换：for j: P_j <- X^{⌊b_j + 2^{−(bp+1)}⌉} · tv
        tv ∈ PVW_TMLWE 为平凡样本，r 条 body 各装一个 LUT（pvmtmlwe_LUT_packing，pvwtmlwe.c:912）
2  原语替换：CMUX/NCMUX -> MatCMUX/MatNCMUX
        MatCMUX(y, x, C) = y + MatExtProd(C, x − y)
        MatNCMUX(y, x, C) = MatCMUX(y, τ₋₁(x), C)    /* aut-KS 为 PVW 版（pvwtmlwe.c:1047）*/
3  提取替换：for q <- 0 to r−1: lane_q <- (Extract_0(P_j).b[q])_j   /* 一次结构产出 r 组共享 mask 的 TLWE */
   （sub_a：公开单项式乘作用于全部 k+r 个分量，与标量相同；调度循环逐位不变）
```

**命题 2.2（逐 lane 相位不变式）** 对每个 lane q ∈ [0, r) 与算法 5 的每个隔离步骤（setup / 每次 MatCMUX、MatNCMUX / sub_a / 最终旋转 / 提取）：

> φ_q(step(PVW)) = step_scalar(φ_q(PVW))，

其中 step_scalar 为算法 2 对应步骤作用于携带 LUT_q 的标量累加器。

**证明** 对步骤归纳。setup 与 sub_a 是公开单项式乘，作用于全部 k+r 个分量，与 lane 分解交换，且 ‖X^{±a}‖₂ = 1（零噪声）。MatNCMUX 的 τ₋₁ 由系数置换（X^i ↦ ±X^{−i}，polynomial.c:569-577）加逐 lane KS 实现，与标量 `trlwe_eval_automorphism` 相同。核心是 MatExtProd：由算法 3 的对角放置，a-块行 (j, d) 对 lane-q 相位贡献 −e·h_d、b-块行 (k+q, d) 贡献 +e·h_d，其余行对 lane-q 相位为纯噪声，故

> φ_q(c′) = ( Σ_d h_d·( digit_d(b^{(q)}) − digit_d(a) ) )·e + ε_q = e·(b^{(q)} − a·s^{(q)}) + ε_q = e·φ_q(c) + ε_q，

第二个等号用 gadget 重构恒等式（近似分解残差并入 ε_q）。lane q 的相位只经由"自己的 b 行 + 共享 a 行"进入——每 lane 的误差结构与标量外积同形，686 §2.1 ExtProd 界逐 lane 适用。∎

**依据**：结构论证如上；代码级 Stage 4/5 对 r=1/2/4 的隔离步骤逐步 oracle 等价测试全过；`MEASURE_NOISE` 插桩复现引理 2.1 的逐步噪声形态。

**定理 2.3（A 线成本计数）** binary include-zero 下算法 5 的选择子事件数与基线相同（H = (h+1)·ρ·n；stage322 插桩实测 MAT-EP 调用 573,440、NCMUX 5,080、sub_a 39、copyback 0）。每事件计数（k = l = 1）：

| 计数项 | r-lane 标量（跑 r 遍算法 2） | MAT-SAB | r=4 数值 |
|---|---|---|---|
| 分解 + FFT 行 | 2r·l | (k+r)·l | 8 → 5 |
| DFT 点乘（环乘） | 4r·l | (k+r)²·l | 16 → 25 |
| 逆 FFT | 2r | k+r | 8 → 5 |

**推论 2.3.1（收益来源与 r 的最优域）** MAT-SAB 不减少事件数；收益 = 共享 mask 使分解/FFT/IFFT 行数从 2rl 降至 (k+r)l；代价 = dense (k+r)² 环乘随 r 二次增长。break-even 条件：C_{decomp+FFT}(每行) > (r−1)·C_{mul}(每 DFT 多项式)（`docs/mat_external_product_breakdown.md:417-421`）。r=4 时 DFT 乘加已占 scratch 标准化时间约 48%——这解释 r=6/8 的负结果（直接仅 1.251×/1.199×）与 r=4 的实测最优。同后端隔离内核（公平口径）：r=2 1.20–1.27×、r=4 1.22–1.34×（spqlios / spqlios_avx512 / mbfhe 双库一致）；完整 SAB（调度融合 + direct-DFT 路线）本地 1.5693–1.7476×、服务器 1.5152–1.8271×（§5.2–5.3）。

**引理 2.4（A 线噪声同阶性）** 在独立性启发式下，算法 5 每 lane 输出 E_q-次高斯且 E_q 满足引理 2.1 的同式界。论证：命题 2.2 表明每 lane 经历与标量完全相同的调度与外积结构；共享 mask 只引入 lane 间相关，不改变单 lane 边际的次高斯参数。**依据**：50-seed 战役（r=2 共 204,800 点 / r=4 共 409,600 点）pair 失败 0、PVW−scalar log₂σ gap ∈ [−0.555, +0.682]；Stage331 pair log₂σ = −7.664（10 trials × 81,920 点）。

### 2.3 B 线 SQ：尺度量化外积（算法 6）

**改动点总述**：把 CMUX 内部的"gadget 分解外积"原语替换为**量化—卷积—重缩放**三步（2025/1711 平方 gadget 引理移植）；调度、密钥类型、其余原语全部不变。

```text
Algorithm 6  SQ-ExtProd —— 尺度量化外积（分支 codex/candidate-sq-scale-sab: src/sab_sq.c:152-173）
Input : Q 尺度累加器 c = (a, b)，系数为 [−2^{q−1}, 2^{q−1}) 内小整数（Q = 2^q）
Input : 选择子 TRGSW C ∈ GSW^1(m, E_G)，消息 m 挂原始尺度 2^{64−q}（l = 1, Bg = 2^q）
Output: c′，φ(c′) = m·φ(c) + ε，系数回到 Q 尺度
1  (â, b̂) <- FFT(a), FFT(b)                          /* 原始整数谱；不分解累加器 */
2  ô_a <- â·Ĉ[0].a + b̂·Ĉ[1].a ;  ô_b <- â·Ĉ[0].b + b̂·Ĉ[1].b   /* l = 1 的两行密钥 */
3  a′ <- Rescale(IFFT(ô_a)) ;  b′ <- Rescale(IFFT(ô_b))
      /* Rescale(x)_i = ⌊(x_i + 2^{63−q}) / 2^{64−q}⌋ = round(x_i·2^{q−64}) —— ∆ = Q²/T 重缩放 */
```

v3 融合（sab_sq.c:177-192）：CMUX 中 out = in1 + Rescale(RawEP(in2 − in1)) 单遍完成（省一次 2N 系数遍历）；NCMUX 在 KS 前精确升尺度（左移 64−q）、KS 后重缩放——KS 语义与噪声不变；蝴蝶零拷贝 ping-pong（省每次自举约 2.7 GB 回拷）。

**引理 2.5（消息路径精确性）** 设 m ∈ {0,1} 挂尺度 2^{64−q}，c 为 Q 尺度操作数，真卷积幅值 ≤ 2^63（不回绕），则

> Rescale( IFFT( FFT(m·2^{64−q}) · FFT(c) ) ) = m·c

逐系数精确：整数卷积 mod 2^64 低字加一次 2^{64−q} 移位，无舍入误差。**依据**：probe 系列与 probe_bind4 的信封契约判定（`execute_direct_torus64` = 真卷积 mod 2^64 低字，真卷积 ≤ 2^116 时可信；本线乘积 ≤ 2^63 恒满足）。

**引理 2.6（噪声账本与 ∆ 抑制；引 2025/1711 Lemma 3.4）** 每外积噪声项（torus rms，N = 2048，2 行卷积）：

| 项 | stock（Bg = 2^23） | SQ(q) | 推导 |
|---|---|---|---|
| 密钥噪声（σ 项） | σ·2^{27.1} | σ·2^{q+3.5} | e_int × 操作数 rms(2^{q−1}) × √N × 2^{64−q}/2^{64}；两式在 q=23 处一致 |
| 量化/舍入 | 2^{−24}（digit 残差） | 2^{−q−1}（重缩放舍入） | 每外积 |
| FFT 精度 | ~2^{−26.5} | 2^{2q−51} | 点乘相对 2^{−53} |

SET_2_3_2048（R = ρ(h+1) = 280 轮）：stock σ 项合计 σ·2^{31.2}，SQ(q=16) 为 σ·2^{23.6} → **σ 吸收容量差 2(23−q) bit**（q=16 → +14 bit）；q 噪声下限 b_prec + 10。

**命题 2.7（σ 单旋钮否定性结果 + 联动硬化闭环）** 容量差只覆盖外积乘积路径；aut-KS / packing-KS 噪声 ∝ σ·2^{Bg_ks} 随 σ 线性放大（每 slot 约 140 次 aut-KS 累计）。实测 σ_out+15：stock 62.04（超出 2^4 预算，失效）；SQ 配 aut-KS(l=2, Bg=2^19) 59.30 / (l=4, Bg=2^16) 59.27（通过，余量 2^4.7）。**结论：硬化必须 σ+KS 联动；σ 单旋钮对 SQ 与 stock 同时失效**（`repro/stage356_sq_scale_sab/` 实测日志，种子固定可复现）。

### 2.4 C 线 D4：LUT 晚绑定算子（算法 7–8）

**改动点总述**：累加器不再携带 LUT，而是携带 LUT 无关的加密线性算子 O = U_id·id + U_τ·τ₋₁（每 slot 两通道 TRLWE）；选择子**全部沿用标量 TRGSW**（不引入新密文对象）；调度结束后才把 r 个公开 LUT 绑定到输出并强制重随机化。

```text
Algorithm 7  OperatorSAB —— LUT 晚绑定算子自举（include/sab_operator.h 契约）
Input : 算法 2 的输入 1–3（标量 TRGSW 选择子族 + ksk_{−1}，全部沿用）
Input : r 个公开有界整数 LUT 多项式 F^{(0..r−1)} ∈ ℤ[X]/(X^N+1)（编码尺度 Δ）
Input : 重随机化 KS 密钥 rk（洪水 σ_flood = 2^{−8}）
Output: lane q 的输出 ≈ LWE(f^{(q)}_j(m_j))，0 ≤ q < r
1  for j <- 0 to n−1 do U_j <- (X^{s_j mod 2N} 于 1/4 尺度, 0)      /* setup：公开平凡编码，零加密开销 */
2  for t <- 0 to h−1 do
3      U <- OpMonomialMul(U, (C_{t,i})_i, ksk_{−1})                 /* 蝴蝶几何与算法 1 逐位相同 */
4      U <- OpSubA(U, ã_t)                                          /* 两通道同乘 X^{−ã_j}（公开）*/
5  U <- OpMonomialMul(U, (C_{h,i})_i, ksk_{−1})
6  for q <- 0 to r−1 do                                            /* 晚绑定：对每 lane 一次 */
7      for j: v_j <- F^{(q)}·U_j.id + τ₋₁(F^{(q)})·U_j.τ            /* 公开整数多项式乘（bind）*/
8      v <- KeySwitch(v, rk) + Gaussian(σ_flood)                    /* 强制重随机化（定理 2.9）*/
9      lane_q <- ( Extract_0(v_j) )_j
```

通道级原语（D2 更新律；sab_operator.c:121-138）：

- OpCMUX(U, V, C) = ( CMUX(U.id, V.id, C), CMUX(U.τ, V.τ, C) )；
- **OpNCMUX**(U, V, C) = ( NCMUX(U.id, V.τ, C), NCMUX(U.τ, V.id, C) )——环绕源 −τ₋₁ 的通道交换律；
- setup 的 1/4 尺度：1/2 尺度上 +1/2 ≡ −1/2（2^63 ≡ −2^63 mod 2^64）无法编码负环符号，1/4（±2^62）可分（sab_operator.c:106-115）。

```text
Algorithm 8  Bind（D4 v11 实现，bg = 32、L = 2 层；sab_operator.c:234-373）
Input : 调度后通道对 (U_j.id, U_j.τ)（1/4 尺度内容）；公开 F 与 τ₋₁(F)
Output: 绑定输出（定理 2.9 的重随机化之前）
1  for d <- 0 to L−1：预缩放谱  spec_id,d <- FFT(F·2^{bg·d−62})；spec_τ,d <- FFT(τ₋₁(F)·2^{bg·d−62})
2  for 每槽 j、每分量 comp ∈ {a, b}、每通道 g ∈ {id, τ}：
3      for d <- 0 to L−1: dig_d <- (comp >> bg·d) & (2^bg − 1)     /* 数位分解（小侧 ≤ 2^31）*/
4      comp′ <- IFFT( Σ_d FFT(dig_d) · spec_g,d )
5  /* 重建恒等式：Σ_d dig_d·2^{bg·d}·F·2^{−62} = comp·F/2^62 = F·X^pos（对 2^62 类通道内容精确）*/
6  /* τ₋₁(F)_0 = F_0，τ₋₁(F)_{N−j} = −F_j；全部层乘积 ≤ 2^80 < 2^85 mask 死区 */
```

**命题 2.8（算子闭合；D2，机器验证）** 更新律族 {公开单项式旋转（setup/sub_a），CMUX，NCMUX，蝴蝶，sub_a} 在基 Γ = {id, τ₋₁} 下闭合：结构常数 e_id·e_id = e_id、e_id·e_τ = e_τ·e_id = e_τ、e_τ·e_τ = e_id（τ₋₁² = id），斜规则 M·τ₋₁ = τ₋₁·τ₋₁(M)（单项式 M）；且中心不变量

> φ₀(L_F(Update(U))) = φ₀(ScalarUpdate(L_F(U)))

对每个更新律与每个基向量 F = X^e 成立。

**证明（提升论证 + 机器检查）** 更新律与绑定对 U 与 F 均为线性，故在 GF(257)[X]/(X^N+1)（N ∈ {8, 16}）上对每个基向量 F = X^e 的验证即覆盖任意中心系数 ∈ [−128, 128] 的多项式（到 GF(257) 单射）；逐 slot 独立性再提升到 per-slot LUT。检查器（确定性重放，5 个源文件 SHA256 绑定）覆盖：**256 phase 行 + 168 trace 行全 PASS**；Γ₀ = {id} 单通道失败的首次分歧（N=8 / binary_all_one / basis0 / slot4）在案，唯一许可修订 Γ₁ = {id, τ₋₁} 后全过；**6 个负控制全部 DETECTED**（remove_tau_channel / omit_tau_swap / positive_negacyclic_wrap / skip_sub_a / coeff_one_fast_with_zero_selector / wrong_butterfly_source），排除了检查器"碰巧通过"的实现错误路径。∎

**依据**：`repro/candidate_d_admission/{phase_equivalence, schedule_trace, closure_basis, negative_controls}.csv`；`scripts/run_candidate_d_d2_closure.py` 重放认证。

**定理 2.9（强制重随机化；D3）** 设算子通道经完整调度后误差独立、同为 E-次高斯（Σ_U 对角，λ_max = g·E²；686 Lemma 4.1 的调度保持性逐通道直接适用）。则：

- **(i)（放大）** 晚绑定 L_F(U) = F·U_id + τ₋₁(F)·U_τ 的误差为 β-次高斯，**β = √2·‖Δ·F_Z‖₂**；对 N = 2048 任意 2-bit LUT 最坏 β² = 2·N·(1/2)² = 1024，β = 32。
- **(ii)（退化）** 高斯尾指数除以 β²：直接绑定的失败界从标量 2^{−120} 退化为 2^{−120/1024} ≈ 2^{−0.117}，远劣于 2^{−64} 目标——**直接晚绑定不可用**。
- **(iii)（修复）** 绑定后做重随机化 KS 并洪水化 σ_flood = 2^{−8}，则输出失败界由洪水高斯在 t = 16 = 2^{−4}/2^{−8} 处的尾支配：

> Pr[失败] = exp(−t²/2) = exp(−128) ≈ 2^{−184.7} ≤ 2^{−120}（标量/B1 水平）≤ 2^{−64}（目标）。

辅助数字：λ_max = 4.696×10^{−5} ≤ 8.806×10^{−5}（E = 2^{−4}/12.898，12.9σ 分位数锚定 2^{−120}；目标侧 E_lim = 2^{−4}/9.419）；确定性 L₁ = 0.0713 ≤ 0.0884、L_∞ = 0.0504 ≤ 0.0625 = 1/16；并集失败界 2.572×10^{−56} ≤ 7.523×10^{−37}（= 2^{−120}）≤ 5.421×10^{−20}（= 2^{−64}）。

**证明** (i) 调度段：两通道经历与标量相同的更新序列，由 686 Lemma 4.1 每步保持次高斯参数、明文单项式乘零增长；通道误差独立 ⇒ 对角协方差。绑定段：公开多项式乘是系数的线性组合，次高斯参数乘以组合系数的 ℓ₂ 范数 ⇒ 每通道放大 ‖Δ·F_Z‖₂；双通道独立求和贡献 √2。最坏 ‖Δ·F_Z‖₂ = √(N·(1/2)²)（2-bit 任意 LUT 每系数幅值 Δ/2、N 项）。(ii) 次高斯尾 Pr[|X| ≥ tσ] = exp(−t²/2) 的指数被 β² 除。(iii) 洪水后误差 = 独立高斯 σ_flood + 有界残留，尾由洪水支配（标准 noise-flooding 论证）；t = 阈值(2^{−4})/σ_flood(2^{−8}) = 16。∎

**依据**：`theory_checks/candidate_d_security_noise.md`；`repro/candidate_d_admission/noise_bound.csv` 逐行（上述十进制值为精确 2 的幂，exp(−128) = 2^{−184.665}）；安全对象映射 8/8 PASS（security_object_map.csv）。

**定理 2.10（C 线成本）** 选择子侧每事件 4g·l = 8l 次环乘（g = 2 通道，每通道 CMUX = 1 次标量外积 = l(k+1) = 4 环乘 @ k=l=1），**与 r 无关**；总环乘 8lH + 晚绑定 2gr 次公开乘积（一次性）。对比 B1（A 线）的 (1+r)²H = 25H（r=4）。物化分量 2g = 4 vs B1 的 1+r = 5。Amdahl 投影（stage322 实测份额：EP 57.623%、materialization 38.079%、其他 4.298%）：中央 0.5376 → **1.860×**、悲观 0.6850 → **1.460×** over B1（**投影，非实测**；准入门 ≥ 1.10 已过）。

### 2.5 F1 备胎与三线对照

F1（MAT-EMPmul）：在 A 线结构上把逐 bit 选择子换成 δ=2 多比特矩阵 CMux（BatchBoot 的 EMPmul 语义），FFT 域自同构融合（τ₋₁ 穿透 gadget 与 FFT）。等价引理 F1-1 经 160 项机器检查；基于 stage322 画像的保守投影 ≈ 2.36× over scalar（乐观 2.5–2.6×），密钥 ≈2× scalar。仅 G1 门通过，B/C 受阻时启动。

| 维度 | 基线 686 SAB | A 线 MAT-SAB | B 线 SQ | C 线 D |
|---|---|---|---|---|
| 累加器 | 单体 TRLWE | r-body PVW_TMLWE（共享 mask） | 单体（同基线） | LUT 无关算子双通道 TRLWE |
| 选择子密文 | 标量 TRGSW | 对角 MAT_TRGSW（算法 3） | 标量 TRGSW（Bg = 2^q） | **标量 TRGSW（沿用）** |
| 每事件环乘 | 4l（单 lane） | (1+r)²l（定理 2.3） | 4 + 重缩放 2N（无分解环） | 4gl = 8l，**与 r 无关**（定理 2.10） |
| 分解/FFT 行 | 2l | (1+r)l | 2（无 gadget 分解） | 2gl = 4 |
| LUT 进入时刻 | 盲旋转前预装 | 盲旋转前预装 | 盲旋转前预装 | **调度后绑定**（算法 7 第 6–8 行） |
| 新假设 | — | 无（标准 GGSW 对角） | 无（分布不变） | 无（8 对象全既有） |
| 附加安全机制 | — | 无需 | 279 硬化 σ+KS 联动（命题 2.7） | 强制重随机化（定理 2.9） |
| 正确性依据 | 引理 2.1 | 命题 2.2 + 定理 3.1 | 引理 2.5 + 实测 gate | 命题 2.8（D2 机器验证）+ D4 待 gate |

---

## 3. 正确性（定理–证据结构）

**定理 3.1（MAT-SAB 确定性输出等价）** 对全部受测参数行（表 1-1 六集 × r ∈ {2,4}，binary include-zero）与每个确定性输入：算法 5 的全部 r·n 个输出 slot 与"同一输入跑 r 遍算法 2"的对应输出在消息精度（prec 位）上逐点相等（gate = 0 失配）。

**证明骨架**：命题 2.2 的逐步骤 lane 相位不变式对 setup → h 次循环（蝴蝶 + sub_a）→ 最终旋转 → 提取归纳，得每 lane 全程相位轨迹与标量一致；提取取系数 0 为线性映射，保持等式。∎（结构证明）

**证据链（分层落盘 `repro/`）**：

1. 结构证明：命题 2.2（归纳，§2.2）；
2. **代码级逐步 oracle**：Stage 4/5 对 r = 1/2/4 的隔离 CMUX/NCMUX/蝴蝶/sub_a/提取逐步断言（scalar 路径为不可变 oracle）全过；
3. **完整 SAB 确定性 gate**：stage331/343/344/354/355 全部行 0 失配（每行 10 perf 样本 + 10 噪声 trial，行内任一 correctness 非 Pass 即整行失败）；
4. **多种子噪声 pair 统计**：pair_failures := #{ torus2int(φ_pvw) ≠ torus2int(φ_scalar) }（mod-2^64 圆周距离 + prec 位量化解码域比较，main.c:1310-1342），50-seed 战役 r=2/r=4 共 204,800/409,600 点全 0；PVW−scalar log₂σ gap ∈ [−0.555, +0.682] bit——与引理 2.4 的同阶性预测一致（独立性启发式下）；
5. **有限代数交叉检查**：toy dense-vs-lane 等价（r ∈ {2,4,6} 零失配）、D2 检查器对共享调度几何的覆盖。

**声明边界**：binary + include-zero、spqlios / spqlios_avx512 后端、表 1-1 参数集；非二进制与全参数泛化不声明（claim matrix 红线，`docs/pvw_mat_sab_claim_matrix_stage339.md`）。

**SQ 线**：正确性 gate = 全部 2048 slot 消息 == LUT 期望。全部配置（v1/v2/v3 × q ∈ {16,23} × σ+15 硬化 × 两种 aut-KS）0 失配；噪声与 scalar 统计级持平（57.55 vs 57.54，预算 60）。依据：引理 2.5 的精确性 + `repro/stage356_sq_scale_sab/` 日志（种子固定可复现）。

**命题 3.2（D 线实现等价状态；未闭合，如实报告）** D4 等价测试装置有效（构建/执行/插桩全过）；UNIT4（双通道平凡 bind）三项逐位精确——含负环卷积期望修正（X^2043·X^40 = −X^35，越 2048 取负；此前"τ 符号翻转"确认为期望计算错误）；SPEC 调试证实 F 槽 = F 精确、τ 槽 = τ₋₁(F) 精确含负号——**算法 7–8 的代数/谱/重建层全部确认正确**。遗留：真噪声输入下 4 个固定位置（[25][29][41][45]）残留 1/4、1/2 尺度垃圾，已由无密码探针 `probe_bind4.c` 复现并隔离：触发 = 负号乘子 × 通道噪声（缺一不可；正号乘子同噪声 = 精确），泄漏量级 = 噪声高字 ⋆ F·2^{bg·d−62}·√N（三级噪声 2^44/2^49/2^54 全吻合，ffnt/spqlios 双后端逐位一致）；谱域累加被排除（差 2^14 = FFT 地板）。最坏点 k=300 的精确仲裁因探针转储记账瑕疵未定案（预期一次运行闭合）。**在此之前 D 线不作实测正确性/性能声明。**

---

## 4. 安全性（定理–证据结构）

### 4.1 假设层：零新假设（对象级审计）

- **A 线**：全部对象为既有标准对象——MAT_TRGSW = 标准 PVW 密钥下的 GGSW 对角加密（算法 3 的对角放置即标准 gadget 注入）；aut-KS = 标准 RLWE KS。CPA 安全归约到 686 同款 spRLWE/RLWE 假设集（研究契约 §5 登记），与基线显式对比无 circular/KDM 增强。compact/structured 路线被安全阻断（公开分布可区分、dummy 填充仅证明级；Sharing-the-Mask 2025/2112 全文审计）——负结果入档。
- **C 线**：安全对象映射 8/8 PASS（initial_operator_basis 公开平凡编码 / operator_channel 标准 RLWE / selector_bit 既有标量 GGSW / ncmux_automorphism 标准 RLWE KS / rotation 公开线性映射 / late_binding 公开有界整数多项式乘 / extraction_packing 标准 KS / vector_of_outputs 公开后处理 + 洪水钩子）——**零新假设、零新密文对象**。
- **B 线**：密钥分布不变，仅 σ 上调 + KS 参数联动——假设面收窄而非扩张；279 差距的吸收是参数化设计（§4.3）。

### 4.2 C 线：定理 2.9 的安全含义

设计文档预留的 `d4_rerandomization_if_required` 钩子被定理 2.9 实证**激活**：直接绑定不可用（失败界 2^{−0.117}），σ_flood = 2^{−8} 后恢复 2^{−184.7} ≤ 2^{−120} ≤ 2^{−64}。可讲的论文结果：晚绑定的安全代价可量化（β 公式）且可修复（洪水参数化），修复代价已计入定理 2.10 的 2gr 次绑定乘积与一次 KS。

### 4.3 B 线：2026/279 稀疏密钥硬化闭环

279 指出稀疏密钥的环同构混合攻击相对保守插值有差距。本仓预检模型（保守插值）：input 侧密度 ≤ 0.05 → 差距取满 15 bit；output 侧 0.25 → 9.2 bit；SQ 可吸收容量 2(23−q)（引理 2.6），q 下限 b_prec + 10。实证闭环与否定性结果见命题 2.7（σ 单旋钮双败 → σ+KS 联动后 SQ Pass / stock 失效）。边界（诚实记录）：绝对安全数用相对模型（基线 = 686 设计级），279 精确 isometry-hybrid 模型替换在 P1 清单；残余 +1.7 bit 在 packing KS 链。

### 4.4 失败概率口径与声明纪律

- 理论口径（686 §7.1）：Pr[正确自举] = erf((q/2^{k+2})/(σ√2))。
- 经验口径（本仓）：pair 统计作经验上界——50-seed 0 失败 ⇒ 每 seed 失败率 95% 上界 ≈ 6%（rule of three）；不从有限算术检查器推断安全性；投影数字一律标注"投影"。
- 所有论文措辞受 claim matrix 红线约束（`docs/pvw_mat_sab_claim_matrix_stage339.md`）。

---

## 5. Benchmark（多维度）

### 5.1 实验协议与统计口径

- 每行 = 全量重建（make clean + 固定 flags）+ **10 次 perf 配对样本**（speedup 按次配对计算，汇总取 mean/min/max，CI95 为样本 t 区间）+ **10 trial 噪声统计** + `/usr/bin/time -v` 资源记录；行内任一 correctness 非 Pass 即整行失败；
- 主指标 = 完整自举摊销 `T_bootstrap/r`（不是单次延迟）；基线 = 同后端同 flags 的重复标量 SAB；
- 后端：服务器 spqlios_avx512（AVX-512/VAES）；本地 spqlios（AVX2/FMA）；跨后端结论另有 ffnt 校验。

### 5.2 主结果：服务器 E1 矩阵（stage355，11/11 收官）

平台：双路 Xeon Gold 6230R（104 线程/251GB）。来源 `repro/stage355_server_e1_matrix/stage355_summary.csv`（commit `adf8007`）：

| case | 样本 | 加速比均值 | min–max | PVW s/lane | 标量 s/lane | 噪声 |
|---|---:|---:|---|---:|---:|---|
| SET_4_5_2048_r4 | 10 | **1.8271×** | 1.762–2.008 | 7.805 | 14.265 | Pass |
| SET_4_5_2048_r2 | 10 | 1.8248× | 1.800–1.980 | 7.719 | 14.086 | Pass |
| SET_2_3_2048_r4 | 10 | 1.8217× | 1.781–1.998 | 7.408 | 13.496 | Pass |
| SET_2_3_2048_r2 | 10 | 1.8002× | 1.690–1.861 | 7.819 | 14.064 | Pass |
| SET_6_7_4096_r4（Boot6 对标） | 10 | 1.7808× | 1.749–1.802 | 16.055 | 28.589 | Pass |
| SET_4_5_4096_r2 | 10 | 1.7508× | 1.728–1.885 | 14.673 | 25.681 | Pass |
| SET_2_3_4096_r2 | 10 | 1.7384× | 1.696–1.754 | 14.093 | 24.499 | Pass |
| SET_4_5_4096_r4 | 10 | 1.7030× | 1.687–1.720 | 14.555 | 24.787 | Pass |
| SET_2_3_4096_r4 | 10 | 1.6877× | 1.653–1.710 | 14.245 | 24.040 | Pass |
| SET_8_9_4096_r4（Boot8 对标） | 10 | 1.6350× | 1.554–1.732 | 122.524 | 200.005 | Pass |
| SET_8_9_4096_r2 | 10 | 1.5152× | 1.399–1.566 | 127.250 | 192.262 | Pass |

覆盖维度：消息宽度 2/4/6/8 bit × 环维 N ∈ {2048, 4096} × r ∈ {2, 4}，共 11 行全通过。趋势：2048 行最高（单核 2.1GHz 有利），8-bit 行最低（与 BatchBoot 自报 6-bit 饱和 1.05× 趋势同向）。

### 5.3 本地 WSL 十行矩阵 + 跨平台互证

本地（i7-11700，spqlios，Stage331/343/344/345/354）：范围 **1.5693×–1.7476×**，最好行 SET_2_3_2048_r4 = 1.7476×（CI95 [6.07, 6.16] s/lane vs 标量 10.69 s/lane）。逐行对照（本地 vs 服务器同 case）趋势一致、服务器相对加速更高，两平台互证。资源受限记录在案：SET_8_9_4096_r4 本地 12GB 两次 OOM（需 ≥16GB），服务器 251GB 完成。

### 5.4 绝对时间口径

本地 SET_2_3_2048 r=4：MAT-SAB **2.99 ms/消息** vs 标量 5.22 ms/消息；原论文（BatchBoot 代测，不同机器）Boot2 = 8.09 ms——绝对口径跨机不可比，同机 head-to-head（E0/M6）列为必做。

### 5.5 资源维度

- **全量 keygen 实测**（Stage207，SET_2_3_2048）：密钥 bytes 比 r=2 = 1.0136×、r=4 = 1.0653×；keygen 时间比 1.10×/1.20×；峰值 RSS 比 0.99×/0.997×（≈持平）；
- **D3 准入账本口径**（686 Table 5 锚，结构性密钥材料）：B0a 标量 ≈17.1MB，B1 = 19.2MB，**D ≈ 18.77MB ≤ B1**；对比 BatchBoot 59.6–205MB → **小 3.3–11.5×**（论文 Pareto 主张的支点）。

### 5.6 竞品对比（BatchBoot, USENIX Sec'26）

同基线相对口径（BatchBoot 论文数据，单线程 Xeon Gold 6258R）：BatchBoot Boot2/4/6/8 = 2.2×/2.4×/1.05×/2.27×，密钥 3.2–3.5× scalar；本仓 A 线 1.52–1.83×，密钥 ≤1.07×。**诚实定位**：相对加速仍落后 BatchBoot（2-bit 档），结构性优势在密钥规模与 r-LUT 语义；E0 同机复现对比（M6）是论文投稿前必做项。

### 5.7 SQ 线与 D4 判定性实验数据

**SQ（stage356 系列，可复现协议 `MOSFHET_TEST_RNG_SEED=1`）**：

| 维度 | 结果 |
|---|---|
| 内核速度（v3 融合+零拷贝） | 9 轮：中位 **−4.5%**、min-of-9 **−7.3%**、7/9 轮更快（SQ 先测含冷启动，偏保守） |
| 噪声 | 基线 σ：57.55 (q16) vs 标量 57.54（持平）；σ+15 硬化：SQ 59.30 Pass vs 标量 62.04 失效 |
| bind 契约探针 | 预缩 2^{−73}+<<11：相对偏差 2^{−50.2}；¼ 预缩方案代数不可能（\|F\|·\|U\| ≈ 2^125 ≫ 53 位尾数）——直接服务 D4 |

**D4 4-积路径探针（`src/probe_bind4.c`，无密码学、ffnt/spqlios 双后端逐位一致）四项硬结论**：
1. 泄漏可复现：通道噪声 2^44/2^49/2^54 三级全部出现内容尺度泄漏，量级 = 噪声高字 ⋆ F·2^{bg·d−62}·√N（三级吻合）；无噪声 = 精确；
2. 谱域累加无罪：逐层逆变换+整数求和 ≡ 谱域累加（差 2^14 = FFT 地板）；
3. **触发器 = 乘子负号 × 通道噪声（缺一不可）**：同噪声 × F（正号）精确，× τF（负号镜像）泄漏 2^53；乘子对调实验证明泄漏跟随乘子；正号位置镜像 = 精确；
4. **mod-2^64 信封语义统一**：`execute_reverse/direct_torus64` = 真卷积 mod 2^64 低字（双精度经 frac 解析，真卷积 ≲2^116 时可信）——SQ 内核、D4 UNIT4 与全部探针在该语义下自洽，消解三周来"整数卷积 vs 实数积"的表面矛盾。

剩余：最坏点 k=300 的 Python 精确仲裁因探针转储记账瑕疵未定案（预期一次运行闭合）。

### 5.8 负结果与已关闭路线（维度完整性）

| 路线 | 结果 | 处置 |
|---|---|---|
| 直接 r=6/r=8 | 仅 1.251×/1.199×（低于 r=4 CI 下限），dense (1+r)² 份额升至 55.7%/61.2% | 关闭，r>4 需结构变革 |
| fused r=6 内核 | 恢复 1.367× 但不超 r=4 的 1.377× | 保持 experimental 不晋升 |
| selector-transpose | 微基准 1.026× → 完整投影仅 1.005× | 中性关闭 |
| compact/structured selector | 公开分布可区分（安全阻断） | 关闭并全文审计入档 |
| σ 单旋钮硬化 | SQ/stock 双败 | 否定性结果，改为 σ+KS 联动（已闭环） |

---

## 6. 性能预估（全部为**投影**，非实测，标注依据）

| 场景 | 相对基准 | 预估 | 依据 |
|---|---|---|---|
| **C 线 D over B1（A 线）** | B1 = 1.75×（本地）/1.83×（服务器）over scalar | 中央 **1.86×** / 悲观 **1.46×** over B1 | D3 Amdahl（stage322 实测份额：EP 57.6%、materialization 38.1%）；门 ≥1.10 已过 |
| 同上折算 over scalar | 重复标量 SAB | 中央 ≈ **3.2×** / 悲观 ≈ **2.6×** | 上两行相乘（投影的投影，仅作量级参考） |
| 硬接收判据 A | B1 | D/B1 ≥ 1.25×（即 ≥2.2× over scalar），30+ 配对样本，95% CI 下界达标 | D4 计划 §0 批判性接收评审 |
| **SQ 叠加 r-lane（stage357）** | A 线 1.52–1.83× | 内核级 −4.5%~−7.3% 的同向增益（待移植验证） | SQ v3 本地数据；P1 任务 |
| **F1 融合（备胎）** | scalar | 保守 2.36× / 乐观 2.5–2.6×；×A 线组合 ≈ 3.8× | f1_mat_empmul_theory.md 基于 stage322 画像 |
| BatchBoot 对标 | scalar | 2.2×–2.4×（2/4-bit），密钥 3.2–3.5× | 竞品论文数据，非本仓实测 |

风险对冲：若 D 线实现损耗 >15% 或判据 A 失败 → 触发 TCHES 降级评估（roadmap 止损链：D 拒 → Candidate E → 冻结系统结果）。

---

## 7. 相对先前工作的改动与优化清单

### 7.1 算法层（相对 2025/686 与上游 MOSFHET）

1. **A 线**：新增 PVW_TMLWE / PVW_TLWE / MAT_TRGSW 类型族与矩阵外积内核；r-lane 共享 mask 打包 + 矩阵选择子；active-buffer 双缓冲（copyback 0）；direct-DFT 路线（分解/DFT 行 2r→1+r、逆变换 2r→k+r）——完整 SAB 加速从 1.27×（Stage20）演进到 1.83×（服务器）；
2. **B 线**：gadget 分解 → Q=2^q 量化+重缩放（1711 引理移植），q 成为独立旋钮；v3 融合重缩放+重组、零拷贝蝴蝶；首次把 279 稀疏密钥安全差距作为参数化设计约束闭环；
3. **C 线**：LUT 晚绑定算子构造（Γ={id,τ₋₁} 闭合、7 更新律、bind+强制重随机化）——**该方向在 686/NTRU-686/2018-622 中均不存在**（9 源哈希审计），新颖性声明收窄为"多 lane 矩阵设定下消除稠密选择子工作的晚绑定 lane 算子"（FDFB² 2024/1376 已覆盖宽泛晚绑定思想）；
4. **理论**：强制重随机化定理（β=√2·‖ΔF‖₂、σ_flood=2⁻⁸）为全新结果；D2 闭合检查器给出 γ=2 的机器证明。

### 7.2 实现层（文件级，merge-base `origin/main=d251d06`，本地领先 255 提交）

- 新增核心：`src/mosfhet/src/mattrgsw.c`（+1395 行）、`pvwtmlwe.c`（+1055）、`pvwtlwe.c`（+373）、`src/sab_pvw.c`（+1377）+ `include/sab_pvw.h`；C 线 `src/sab_operator.c` + `include/sab_operator.h`；
- 修改：`mosfhet.h`（+261 行类型族）、`polynomial.c`（AVX/FMA 路径）、spqlios AVX512 FFT/IFFT 后端；约 30 个 feature 开关**全部默认 false**（scalar 默认路径不可变的治理不变量）；
- 探针体系：`probe_mul / probe_v6 / probe_layer / probe_bind4`（无密码最小复现，双后端一致）；
- 修复的上游 bug：Windows 原生 `PORTABLE_BUILD` RNG `/dev/urandom` NULL 流 → 堆损坏（建议回退确定性 RNG）。

### 7.3 治理层

commit-pinned 确定性重放、SHA256 文献绑定、强制负控制、claim matrix 红线、D0–D8 阶段门与止损链——论文可信度的骨架，也是工件评审（artifact evaluation）的差异化素材。

---

## 8. 下一阶段规划（至最终成稿）

### 8.1 冲稿缺口清单（master plan §四，按优先级）

| 优先级 | 任务 | 预估 |
|---|---|---|
| **P0** | 服务器 AVX-512 复测 SQ v3（−4.5% 确认）+ σ+15 硬化高统计 | 1 会话 |
| **P0** | D4 仲裁闭合（修 dump 记账 → 一次运行定案）→ `SAB_OPERATOR_EQUIV` gate →（过则入论文第 6 节；不过则降级为案例研究素材，probe 数据已可写） | 1–2 会话 |
| **P1** | stage357 SQ×PVW 移植（B 叠上 A 的 1.52–1.83×）——论文性能上限的最后一跳；含 r∈{1,4} 双等价 gate、σ+15 平移、r∈{1,4,8} 计时 | 2–3 会话 |
| **P1** | 279 精确 isometry-hybrid 代价模型替换保守插值（安全节绝对数值升级） | 1 会话 |
| **P1** | M6/E0：BatchBoot 同机 head-to-head 复现（Boot2/4/6/8 对应行，统一 pfail，报绝对 ms/消息 + 密钥 Pareto） | 服务器窗口 |
| **P2** | ternary/gaussian 选择子路径；packing KS 残余噪声扫描；合并 main；工件打包 | 各 0.2–1 会话 |

### 8.2 里程碑（M4–M8）

| 里程碑 | 内容 | 判据 |
|---|---|---|
| M4 = D4→D6 | D4 隔离实现（r=1/2/4 等价 + microbench，热路径零分配）→ D5 服务器全参数 A/B → D6 一次机制优化 | 判据 A（§6）；τ₋₁ KS 噪声入递推若超界触发 D3 允许的一次参数调整 |
| M5 全矩阵 | ✅ 已完成（stage355） | — |
| M6 BatchBoot 复现 | B2 head-to-head | 服务器空闲窗口 |
| M7 论文全文 | 8 节骨架随数据推进（§9） | 每定理/声明链到证据工件 |
| M8 工件+投稿 | ≥50 seeds、≥1e6 观测系数、≥30 配对主运行、复现命令全通过 | `PAPER_READY` |

**时间线判断**：P0 两项为本周窗口目标；P0+P1 全部完成约需 5–8 个工作会话（服务器可用性是外部依赖）；A+B 主体的写作可与之并行（骨架与证据映射已就位，§9）。若 C 线 gate 通过，论文升级为三贡献，写作增加第 6 节（约 +1 周量级）。

**止损链**：D 拒 → Candidate E（扩张环/张量 lane 打包，保留非激活）→ 拒 → 冻结系统结果、评估 scoped TCHES 包。

### 8.3 硬接收判据（批判性接收评审，D4 计划 §0）

A. 端到端 D/B1 ≥1.25×（over scalar ≥2.2×，30+ 配对样本）；B. 同机 B2 复现对比表；C. ≥1 个端到端应用（8-bit 指令集或 PSI 数位分解）；D. 论文级证明（闭合/β 定理/hybrid）；E. 工件可复现。当前差距按序：零加密实现实测、无同机 B2、无端到端应用、重随机化代价未实测、hybrid 未论文级展开。

---

## 9. 论文骨架与证据映射（已就位）

题向：**"实践更快的摊销自举：尺度量化外积与安全硬化的稀疏密钥参数方法（+LUT 晚绑定算子）"**（A+B 核心，C 闭合则第三轴）：

| 节 | 内容 | 证据映射 |
|---|---|---|
| 1 Intro | 686 摊销自举的实践与安全缺口 | goal 文档、预检表 |
| 2 Prelim | FHEW/TFHE 外积、1711 平方 gadget、686 SAB、279 | 文献矩阵（哈希绑定） |
| 3 尺度量化外积 | 代数（消息挂 2^{64−q}、重缩放、信封契约）、噪声账本 σ·2^{q+3.5} vs σ·2^{27.1} | theory_checks/stage356、bind_contract 探针 |
| 4 安全硬化参数方法 | 279 差距 → σ+KS 联动；否定性结果（σ 单旋钮） | preflight CSV、σ+15 实验组 |
| 5 r-lane 系统集成 | MAT-SAB 后端与调度融合 | stage355 矩阵 1.52–1.83× |
| 6（若闭合）LUT 晚绑定 | 算子通道、bind、强制 rerand；4-积泄漏案例研究 | D4 全链 + probe_bind4 |
| 7 评测 | 服务器矩阵 + SQ 三表 + 9 轮比值统计 | repro/*/ |
| 8 Discussion | 局限（本地 vs 服务器计时、保守 279 模型、binary-only v1） | — |

---

## 10. 诚实的局限声明（论文 Discussion 素材）

1. 本地与服务器计时不可直接互换（单核 2.5GHz vs 2.1GHz），绝对 ms/消息仅同机可比；BatchBoot 对比目前是文献数字，E0 未做；
2. 279 安全差距用保守插值，精确模型替换在 P1；
3. A 线 v1 仅 binary 密钥 + include-zero；ternary/gaussian 在 P2；
4. C 线全部加速数字为 D3 Amdahl 投影，D4 未过 gate 前不作实测声明；4-积泄漏的根因仲裁未最终闭合；
5. SQ −4.5% 为本地 9 轮中位数，服务器高统计确认在 P0；
6. r>4 的 dense 二次效应未解（结构性下界视角已记录，gap(r) 未数值闭合）。

---

## 附：关键证据文件索引

| 主题 | 文件 |
|---|---|
| 服务器主结果 | `repro/stage355_server_e1_matrix/stage355_summary.csv`（adf8007） |
| 本地矩阵 | `repro/stage345_binary_matrix_synthesis/`、`repro/stage354_e1_binary_matrix_expansion/` |
| 单行主声明 | `repro/stage332_paper_result_pack/`（1.747647×，含 claim 边界） |
| 组件画像 | `repro/stage322_schedule_profile_attribution/component_budget.csv` |
| 内核分解 | `docs/mat_external_product_breakdown.md` |
| 成本模型 | `docs/cost_model.md`、`theory_checks/pvw_sab_complexity_model.md` |
| D 治理链 | worktree `docs/candidate_d_{d0_baseline,d1_novelty_audit,admission_report}.md`、`theory_checks/candidate_d_{operator_closure,security_noise,complete_cost}.md`、`repro/candidate_d_admission/` |
| SQ 线 | 分支 `docs/stage356_results_and_roadmap.md`、`src/sab_sq.c`（分支端） |
| 论文规划 | `docs/paper_ccf_a_master_plan.md`、`docs/goal_ccf_a_paper.md` |
| 声明红线 | `docs/pvw_mat_sab_claim_matrix_stage339.md` |
| 算法实现锚点 | `src/sparse_amortized_bootstrap.c`（基线）、`src/sab_pvw.c` + `src/mosfhet/src/mattrgsw.c`（A 线）、分支 `src/sab_sq.c`（B 线）、`src/sab_operator.c`（C 线） |
