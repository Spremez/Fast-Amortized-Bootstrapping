# 外层完整矩阵自举算法：形式化（T1 定稿候选）

Date: 2026-09-04
义务来源：`outer_layer_execution_plan.md` WS-A/T1。本文档给出外层算法的
论文级伪代码、逐行层归属与实码锚点，作为论文 §5 的骨架。正确性/噪声/
成本三合一引用既有定理（M1–M3、命题 2.2、定理 3.1、686 Lemma 4.1），
不新增加班主张；G-ρ 分支以虚线标注（未实现）。

---

## 1. 记号（对齐 686 §2 与本仓 FINAL 参数）

```text
输入环 R_Y = Z[Y]/(Y^n+1)，n = in_N ∈ {2048,4096,8192}；输入密钥 s ∈ S_{n,h}（binary）
输出环 R = Z[X]/(X^N+1)，N = out_N；输出密钥族 S = (s^(0),...,s^(r-1))（PVW_TMLWE_Key 列）
d = diff(s) ∈ (-n,n]^{h+1}；ρ = r_prec（B = 2^ρ 为 |d_t| 上界）；gap 条件参数 t
累加器 C_j ∈ Mul-LWE（= PVW_TMLWE：(a; b_0..b_{r-1})，k=1）
选择子 M_{t,i} ∈ Mul-GSW（= MAT_TRGSW，对角 gadget，(1+r)ℓ 行）
K_aut：多体 τ₋₁ 自同构 KS 钥；PCK/KSK：packing/HW KS（标量侧）
测试向量 TV = (tv_0..tv_{n-1})，tv_j 为 r 体平凡样本（每 lane 一个 LUT）
核参数：ℓ=1；标准核 Bg=2^23，或 SQ(q)，q* = max(p+10, 23−m_sec/2)
```

## 2. 抽象外积契约（L3 接口）

```text
⊡ : Mul-GSW × Mul-LWE → Mul-LWE
    φ_q(M ⊡ C) = m_q · φ_q(C) + ε_q        （M1；对角消息 m=(m_0..m_{r-1})）
    ‖ε_q‖ ≤ 噪声界（M2：无跨体放大；标准核 686 §2.1 界 / SQ 定理 2）
实现 A（标准）：(1/p)·M·C = Σ_row G^{-1}(C)_row ⊙ M_row    [G⁻¹ = 数字分解]
实现 B（SQ）  ：Q 尺度不变量 + 整数卷积 + 融合重缩放        [无分解]
选择规则：q* = max(p+10, 23−m_sec/2)；q*≤23 ⇒ SQ(q*)，否则标准核
```

## 3. 算法 O1：Matrix-SAB（外层主算法）

```text
Algorithm O1  Matrix-SAB —— r-lane 稀疏摊销自举（binary 密钥）
Input : RLWE (a,b) ∈ R_Y²（r 条 lane 共享输入），d 的逐位 Mul-GSW 选择子
        {M_{t,i}}（0≤t≤h, 0≤i<ρ），K_aut，TV，PCK/KSK
Output: lane q 的 n 条 LWE(f^{(q)}_j(m_j)+ε)，0≤q<r

 1  for j <- 0..n-1:  C_j <- X^{⌊b_j + 2^{-(bp+1)}⌉} · TV_j          [L2|setup]
 2  for t <- 0..h-1:
 3      C <- MonomialMul^r(C, (M_{t,i})_i, K_aut)                    [L1|O2]
 4      C <- SubA^r(C, ã)                                            [L1|O3]
 5  C <- MonomialMul^r(C, (M_{h,i})_i, K_aut)                        [L1|O2|终旋]
 6  for q <- 0..r-1:  lane_q <- (Extract_0(C_j).b_q)_j               [L2|提取]
 7  lane_q <- PackingKS(lane_q)（逐 lane，标量）                       [尾声|待C5]
 8  return (lane_0, ..., lane_{r-1})
```

实码锚点：1↔`sab_pvw_setup_tv_xb`(:1214)；2-5↔`sab_pvw_sparse_mul_binary`
(:1140)；6↔`sab_pvw_extract_tlwe_lane`(:280)；7↔`sab_pvw_init_full_postproc`
的逐 lane packing（:304）。

## 4. 算法 O2：MonomialMul^r（矩阵蝶形，L1 核心）

```text
Algorithm O2  MonomialMul^r —— 同态乘 X^e（e = Σ e_i·2^i）
Input : 槽阵列 P = (P_0..P_{n-1})，P_j ∈ Mul-LWE；位选择子 M_i
Output: P′，φ_q(P′_{(j+e) mod n}) = X^e·φ_q(P_j)，回绕经 τ₋₁ 吸收 X^N=−1

 1  for i <- 0..ρ-1:                       /* 位序 LSB 起，乒乓缓冲 [L4] */
 2      p <- 2^i
 3      for j <- 0..p-1:                    /* 环绕槽 [L1] */
 4          P′_j <- MatNCMUX(P_j, P_{n-p+j}, M_i)
                = MatCMUX(P_j, τ₋₁(P_{n-p+j}), M_i)      [τ₋₁=多体自同构+K_aut]
 5      for j <- p..n-1:                    /* 直达槽 [L1] */
 6          P′_j <- MatCMUX(P_j, P_{j-p}, M_i)
 7      P <- P′
 8  return P
其中 MatCMUX(y, x, M) = y + M ⊡ (x − y)                      [L3|契约调用]
可选 [L4]：DualSubCMUX 配对（j 与 j+p 两步共享三操作数差分，k=2 拓扑上限已证）
```

锚点：:861 `sab_pvw_RGSW_monomial_mul_state`；MatCMUX :704；MatNCMUX :713
（τ₋₁ = `pvmtmlwe_eval_automorphism` + `aut_minus1` 钥）。

## 5. 算法 O3：SubA^r（减 a·s 的矩阵化，三分支）

```text
Algorithm O3  SubA^r —— 公开单项式减 a（按秘密类分支）
 1  binary:      for j: P_j <- X^{-ã_j} · P_j                [明文乘，零噪声，作用 k+r 分量]
 2  ternary:     for j: P_j <- MatCMUX(X^{-ã_j}·P_j, X^{+ã_j}·P_j, M^{sign}_j)   [s_sign 族]
 3  include-zero:for j: P_j <- (X^{ã_j}−1)·P_j 的差分形 + M^{coeff} ⊡ ·          [s_coff 族]
 4  ρ-SAB(虚线,未实现,G-ρ): for j: Auto(P_j,−ã_j^{-1}) → M^{V}⊡· → Auto(·,−ã_j)
                [两次多体自同构 + 一次 ⊡；对应 686 Alg 4 / 标量 sub_a_ga]
```

锚点：binary :961；include-zero :987；ternary :1055；标量 ρ 参照
`sparse_amortized_bootstrap.c:248 sub_a_ga`。

## 6. 三合一结果（引用既有定理）

- **正确性（命题 F1 = 命题 2.2/定理 3.1）**：逐步骤 lane 相位不变式归纳
  （setup/sub_a 明文乘与 lane 分解交换；MatCMUX 由 M1；提取线性）⇒ 全部
  r·n 输出与"同输入跑 r 遍 686"逐点相等。证据：r=1..8 全门 0 失配
  （stage369/371）。
- **噪声（定理 F3）**：每 lane 满足 686 Lemma 4.1 同式界（调度轮数相同，
  h+1 次 MPmul）；M2 保证跨体无放大。证据：50-seed pair 0、S7 81,920 点
  pair 0、σ_G=2⁻⁴⁹ 下 +0.08 bit（stage371）。
- **成本（定理 F2 = M3 统一陈述）**：事件数 (h+1)(ρn−B+1) 与 r 无关
  （对 686×r 为 EP 粒度 1/r）；行积每输出 (1+1/r)×（r=4 结构上限
  1.25×，实测 1.21×）；radix-δ 推广见执行计划 T2（胜利条件
  D+F+I > (1+r)A·(2^δ−1−δ)/(δ−1)）。

## 7. 层归属总表（论文"内外层边界图"的数据源）

| 伪代码行 | 层 | 现实现 | 可替换项 |
|---|---|---|---|
| O2 行 1-7 循环几何 | L1 | 686 蝶形 | radix-δ（C1/F1）、mixed-radix（C2）、共享（C3） |
| O2 MatCMUX 内的 ⊡ | L3 | 标准/SQ 双核 | (l,Bg/q) 族 + q* 规则 |
| O2/O3 的多体类型 | L2 | PVW_TMLWE/MAT_TRGSW | per-lane 对角（C6 使能） |
| O2 乒乓缓冲/DualSub、O3 快路径 | L4 | 7 旗标 | 工程层，语义不变 |
| O1 行 7 尾声 | 尾声 | 逐 lane 标量 | C5 联合 packing |
