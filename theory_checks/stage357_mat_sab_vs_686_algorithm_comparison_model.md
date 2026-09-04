# Stage357 MAT-SAB vs 2025/686 Algorithm Comparison Model

Date: 2026-09-03

## 目的与范围

给出当前矩阵自举路径（`sab_pvw_*` / MAT_TRGSW 多体外积）与 ePrint 2025/686
（Guimaraes & Pereira, "Fast amortized bootstrapping with small keys and
polynomial noise overhead"）自举算法的逐步理论对比，并整理因数学结构不同而
引入的适配算法（adaptation layer）。本文档是理论描述与既有证据的汇编，
不提出新的定理主张；所有性能/噪声数字引用既有 stage 记录。

代码锚点约定：

- 标量 686 路径: `src/sparse_amortized_bootstrap.c`
- 矩阵路径: `src/sab_pvw.c`, `src/mosfhet/src/mattrgsw.c`
- 结构定义: `src/mosfhet/include/mosfhet.h`
- 既有理论: `theory_checks/pvw_sab_complexity_model.md`,
  `theory_checks/stage346_mat_sab_algorithm_gap_model.md`,
  `docs/mat_to_bootstrap_goal_audit.md`

## 1. 686 的自举算法结构（论文原文视角）

记号（沿用 686）：输入环 `R_Y = Z[Y]/(Y^n + 1)`（n = 输入 LWE 维度），自举钥环
`R = Z[X]/(X^N + 1)`（N = 输出多项式度）。稀疏密钥 `s(Y)` 汉明重 `h`，
非零位置序列 `j~ = idx(s)`，差分 `d := diff(s) ∈ (-n, n]^{h+1}`：
`d[0] = -j~_0`, `d[i] = j~_{i-1} - j~_i`, `d[h] = -j~_{h-1}`。
`B` 为 `|d[i]|` 上界（期望 `B ∈ O(n/h)`）。

### 1.1 核心对象：指数域多项式累加器（"特殊 acc"）

686 的累加器不是单个 RLWE，而是 **n 个 RLWE 密文的列表**
`c = (c_0, ..., c_{n-1})`，其中 `c_i ∈ RLWE_z(X^{u_i})` 加密单项式 `X^{u_i}`，
即多项式 `u(Y) = Σ u_i Y^i` 被"加密在 X 的指数上"。盲旋转 = 同态计算
`b(Y) - a(Y)·s(Y)` 的每个系数值到指数上，再配测试向量 `t_i(X)` 得
`t_i·X^{m_i + e_i}`。

这是 686 摊销复杂度的来源：一次盲旋转刷新 n 条消息
（amortized functional bootstrapping, Algorithm 6）。

### 1.2 Algorithm 1: MPmul（单项式×多项式同态乘）

输入：累加器 `c ∈ RLWE^n`；`v` 的逐比特 GSW 加密 `C_i ∈ GSW(v_i)`（i < log B）；
自同构 KS 钥 `ksk`（`X → X^{-1}`）。对每个比特 i：

```text
for j in [0, 2^i):        c^_j  <- ((Auto(c_{n-2^i+j}, -1) - c_j) ⊙ C_i) + c_j   # NCMUX
for j in [2^i, n - 2^i):  c^_j  <- ((c_{j-2^i}      - c_j) ⊙ C_i) + c_j         # CMUX
```

即把"乘 `Y^{v·2^i}`"分解为逐位 CMUX/NCMUX 蝶形：直 CMUX 选择是否平移数组
下标（旋转 Y 指数），NCMUX 额外用 `X → X^{-1}` 负循环自同构处理绕回位置的
取负。复杂度 O(n·log B) 外积。

噪声（Lemma 3.1）：
`E_out <= sqrt( (log B)(l·N·β²·E_G² + N·l_ksk·β_ksk²·E_ksk²) + E_0² )`。

### 1.3 Algorithm 2/3/4: bin-SAB / tern-SAB / ρ-SAB

同一骨架，只有"减 `a(Y)·s`"一步不同：

```text
1  c_i <- t_i · X^{b_i}                       # 测试向量装配（setup_tv）
2  for i in [0, h):
3      c <- MPmul(c, {C_{i,j}})               # 乘 X^{d[i]}（RGSW_monomial_mul）
4      按 s 的类型减 a(Y)：                     # sub_a
5  c <- MPmul(c, {C_{h,j}})                    # 最后一次乘 X^{d[h]}
```

- **bin-SAB (Alg 2)**：`c_k <- c_k · X^{-a_k}`，明文单项式乘，噪声零增长。
- **tern-SAB (Alg 3)**：加密控制位 `V_k`（`s_j~ = ±1` 的符号），在
  `X^{-a_k}` 与 `X^{+a_k}` 之间 CMUX；代价 +h·n 个外积。
- **ρ-SAB (Alg 4)**：`s_j~ ∈ [-ρ, ρ]` 一般情形，每个系数用两次 RLWE 自同构
  （`X → X^{-a_k^{-1}}` 与 `X → X^{-a_k}`）+ 一次外积实现
  `[BDF18]` 式的同态乘加；要求 `a_k` 为奇（modulus switching 保证）。

复杂度均为 O(h·n·log B) 外积；噪声
`E_out <= sqrt( (h+1)(log B)(l·N·β²·E_G² + N·l_ksk·β_ksk²·E_ksk²) + E_T² )`
（bin 情形，Lemma 4.1）。

### 1.4 Algorithm 5/6: packing KS 与摊销功能自举

Alg 6：`n` 条 LWE → packing KS 打包成单条 RLWE → HW-reducing KS 切到低汉明重
钥 → SAB（Alg 2/3/4 之一）→ 逐系数 extract。Corollary 6.2：摊销
**O(h·log B) 外积/消息**，噪声 `Õ(sqrt(N·h·log B))`；取 `B ∈ O(n/h)` 得
`O(h·log(n/h))` 外积/消息。

### 1.5 686 结构的五个理论性质（后续对比的基准）

- **P1 指数域累加器**：acc 是 RLWE^n 列表，消息在 X 指数上，天然摊销 n 条消息。
- **P2 单项式乘法位分解**：乘 `X^v` = 逐位 CMUX/NCMUX 蝶形，选择子只需加密
  单个 bit 的 GSW。
- **P3 明文单项式乘零代价**：`X^{-a_k}`、`X^{±a_k}` 乘法不增噪声（bin/tern）。
- **P4 噪声只来自 MPmul**：外积 + 自同构 KS 两处，h+1 轮次累加。
- **P5 双重摊销维度**：n（系数槽）× 共享调度；BSK 只需 (h+1)·log B 个 GSW
  （小钥）。

## 2. 本地矩阵自举（MAT-SAB）的理论结构

### 2.1 多体累加器（shared-mask multi-body）

```c
// mosfhet.h:128
typedef struct _PVW_TMLWE {
  TorusPolynomial *a;   // k 个共享 mask 分量（k=1 时单个多项式）
  TorusPolynomial *b;   // r 个体分量 b_0..b_{r-1}，每 lane 一个
  int r, k;
} * PVW_TMLWE;
```

acc 变为 `C = (a, b_0, ..., b_{r-1})` 列表（in_N 个槽位）。lane q 的相位定义

```text
φ_q(C) = b_q - a · s_q        （s_q = PVW_TMLWE_Key 的第 q 列密钥，mosfhet.h:139）
```

**r 的语义**（roadmap 固定设计）：r 条共享同一输入 (a,b)、同一控制/钥调度的
独立 LUT/SAB lane。r **不是**累加器下标打包，与 686 的 n 槽摊销是两个正交
维度（可乘性组合：一次盲旋转刷新 r·n 条消息，见 §6）。

### 2.2 逐步相位不变量（适配的正确性契约）

对标量 lane q 与矩阵多体在第 t 个调度步后要求（roadmap Stage 4）：

```text
I(t):  ∀q, j:  φ(acc_pvw[j].body[q] | t)  ==  φ(acc_scalar[q][j] | t)
```

覆盖 CMUX/NCMUX、RGSW monomial、sub_a、sparse_mul、extract、KS 各边界。
这不是论文级定理，而是设计不变量 + 逐步等价测试与 50 种子噪声对照的工程
证据（roadmap Stage 5/6 记录，PVW-vs-scalar 配对失败 0/409600）。

### 2.3 调度层逐函数镜像

| 686 论文对象 | 标量实现 | 矩阵实现（sab_pvw.c） |
|---|---|---|
| Alg 2 line 1 装配 `t_i·X^{b_i}` | `setup_tv_xb` (sparse_amortized_bootstrap.c:359) | `sab_pvw_setup_tv_xb` (:1214) |
| Alg 1 MPmul 蝶形 | `RGSW_monomial_mul` (:226) | `sab_pvw_RGSW_monomial_mul_state` (:861) |
| CMUX | `CMUX` (:209) | `sab_pvw_CMUX` (:704) |
| NCMUX（`X→X^{-1}` 自同构 + CMUX） | `NCMUX` (:218) | `sab_pvw_NCMUX` (:713) |
| Alg 2 line 5-7 减 a（bin） | `sub_a` binary 分支 (:262) | `sab_pvw_sub_a_binary` (:961) |
| Alg 3 line 5-8（tern 控制位） | `sub_a` ternary 分支 + `s_sign` | `sab_pvw_sub_a_ternary` (:1055) |
| Alg 4 line 5-8（ρ 双自同构+外积） | `sub_a_ga` (:248) | `sab_pvw_sub_a_include_zero` (:987)（结构对应 `V_i∈GSW(X^{s_j~})`）；gaussian/ρ 分支尚未接入 PVW（stage251-260 范围 = include-zero/ternary） |
| Alg 2/3/4 主循环 | `sparse_mul` (:290) | `sab_pvw_sparse_mul_binary/_nonbinary` (:1140/:1177) |
| 盲旋转 + mod switch | `sab_blind_rotate` (:333) | `sab_pvw_blind_rotate_binary/_nonbinary` (:1223/:1234) |
| Alg 6 line 7 extract | `sab_rlwe_bootstrap` 内 extract | `sab_pvw_extract_tlwe_lane`（逐 lane，:280） |
| packing KS / HW-KS | 标量 | 仍标量逐 lane（`sab_pvw_init_full_postproc`, :304） |

外积调度数量完全一致：`(h+1)·ρ·n` 个 CMUX/NCMUX 调度单元
（SET_2_3_2048: 40·7·2048 = 573,440）。矩阵路径不改变调度，只替换单元语义。

### 2.4 多体外积的相位代数（MAT external product）

选择子 `MAT_TRGSW`（mattrgsw.c:238 `mat_trgsw_monomial_sample`）：对 bit 值
`m ∈ {0,1}`、单项式指数 e（CMUX 场合 e=0），共 `(k+r)·l` 行 PVW_TMLWE 样本；
gadget 放置为**对角结构**——行 `(j·l+i)`（j 为分量索引：j<k 是 mask 行块，
j=k+q 是体 q 行块）只在分量 j 上加 `m·h_i·X^e`（h_i 为 gadget 数字）。

外积 `mat_trgsw_mul_pvmtmlwe_DFT`（mattrgsw.c:903，dense 内核 :832-896）：

```text
out = Σ_{rows} G^{-1}(C)_row ⊙ row        （逐分量数字分解，dense 累加）
```

对 lane q 逐行取相位（`φ_q(row) = row.b_q - row.a·s_q`）：

```text
φ_q(out) = Σ_rows G^{-1}(C)_row · φ_q(row)
         = Σ_i dec_{k+q,i}(C)·(m·h_i)          # 体 q 行块：重构 b_q
         - Σ_{j<k} s_q[j]·Σ_i dec_{j,i}(C)·h_i # mask 行块：重构 a·s_q
         + Σ_rows dec_row·e_row
         = m · φ_q(C) + e_q
```

即：**MAT 外积在每条 lane 上同时实现"乘以加密常数 m（或单项式 X^e·m）"**，
外来体分量 `b_q'`（q'≠q）不进入 φ_q，只以噪声形式出现。这正是把 686 的
标量外积 ⊙ 扩展成多体版本所需的全部代数，也是 §2.2 不变量成立的机制。
（此推导是设计代数，由等价测试背书，非形式化定理。）

**mask 共享的保持性**（归纳）：CMUX 的 mask 演化
`α_out = α_1 + EP(δ; selector 的 a 行块)` 只依赖共享差分 `δ = α_2 - α_1` 与
选择子 a 行块，与 lane 秘密无关 → 每步之后 mask 仍是单个多项式，r 个体共用。
前提是所有 lane 共享同一选择子比特（同一 d[i] 调度）；调度分叉则 mask 分叉，
批处理失效（roadmap "Reuse shared schedule"）。

### 2.5 NCMUX 的多体自同构适配

686 的 NCMUX 只需标量 RLWE 自同构 + ksk。多体对象上 `X → X^{-1}` 必须同时
作用于 k+r 个分量并切到自同构钥，因此新增钥型 `pvmtmlwe automorphism KS key`
（`aut_minus1`，指数 2N-1，sab_pvw.c:350/719）。语义：
`φ_q(Auto_{-1}(C)) = Auto_{-1}(φ_q(C)) + e`，噪声结构与标量 ksk 同阶
（Stage 4/5 隔离测试通过）。

## 3. 逐层对比分析

### 3.1 数据结构层

| 维度 | 686 标量 | MAT-SAB | 结构差异的后果 |
|---|---|---|---|
| acc | TRLWE 数组 ×n | PVW_TMLWE 数组 ×n（k+r 多项式） | 相位从 1 个变 r 个，需 §2.2 不变量 |
| 选择子 | TRGSW（(k+1)l 行 TRLWE） | MAT_TRGSW（(k+r)l 行 PVW_TMLWE，对角 gadget） | 一个选择子服务 r lane；钥体积见 §3.5 |
| 自同构 | 标量 ksk | pvmtmlwe aut-KS（新钥型） | 686 框架外的必增钥材料 |
| 密钥 | 输出钥 s | PVW_TMLWE_Key s[k][r]，lane 取列 | 逐 lane 可独立 |

### 3.2 外积成本层（盲旋转每个 CMUX/NCMUX 单元，k=1, l=1）

| 量 | 标量 ×r lane | MAT（r lane 一次） | MAT/标量 |
|---|---|---|---|
| 分解多项式数 | 2r | 1+r | (1+r)/2r |
| 正向 DFT | 2r | 1+r | (1+r)/2r |
| DFT 域乘加 | 4r | (1+r)² | (1+r)²/4r |
| 逆向 DFT | 2r | 1+r | (1+r)/2r |
| 选择子行读取 | 2r | 1+r | (1+r)/2r |

一般 k, l：行数 (k+r)l vs r(k+1)l；乘加 (k+r)²l vs r(k+1)²l。
MAT **不**靠减少 DFT 乘加取胜（该项反而更多），靠共享 mask 的分解/正逆 DFT
节省取胜（docs/mat_to_bootstrap_goal_audit.md 结论一致）。

**一阶胜利条件**（逐单元局部模型，记 D/F/I 为单分量 分解/正向 DFT/逆向 DFT
代价，A 为一次 DFT 域乘加；k=1, l=1）：

```text
MAT < scalar  ⟺  (1+r)(D+F+I) + (1+r)²·A < 2r(D+F+I) + 4r·A
           ⟺  D + F + I > (r - 1)·A
```

即：单分量的分解+双 DFT 管线代价须超过 (r-1) 倍的加乘代价。r=2: 需
`D+F+I > A`（成立，FFT 变换 ≫ 单次乘加）；r=4: `> 3A`（仍成立但余量缩小）；
r=8: `> 7A`（接近失效区）。这与实测的外积层收益曲线一致（r=2 1.27x、r=4
1.34x，再往上 dense (k+r)² 项主导），也解释了 stage346 指出的"远未达到理想
r 倍扩展"。

### 3.3 噪声层

- 结构：每 lane 每外积收集 `(k+r)l` 个选择子行噪声项 + 分解舍入，标量为
  `(k+1)l` 项；分解数字与舍入项相同。次高斯求和的最坏情形放大因子
  `sqrt((k+r)/(k+1))`（r=2: ×1.22 / +0.29 log2；r=4: ×1.58 / +0.66 log2），
  外来体分量的贡献是纯噪声（§2.4 代数）。
- 实测（50 种子 sweep，roadmap Stage 8）：r=2 gap ∈ [-0.470, +0.636]、均值
  -0.0039 log2；r=4 gap ∈ [-0.541, +0.636]、均值 -0.0313 log2 —— 与求和界
  相容、均值中性。
- 调度轮数与 686 完全相同（h+1 次 MPmul），故 686 Lemma 4.1 的
  `sqrt((h+1)·log B·(...))` 轮次结构不变，只有每外积常数行的差异。

### 3.4 复杂度层（相对 686 定理）

- 686 摊销定理（Cor 6.2）不变：MAT 只改吞吐常数与 lane 批处理，不改变
  SAB 渐近（stage102 锚点 FAB_COMPLEXITY_MODEL 的 claim limit 原文）。
- 总外积调度单元数相同 `(h+1)·ρ·n`；每个单元的代价由 §3.2 表刻画。
- 尾部未摊销：`T_pvw = T_setup + M·C_ext_mat + T_extract + r·(T_materialize
  + T_packing + T_hwks)`（pvw_sab_complexity_model.md）——输出侧逐 lane 的
  TLWE 物化、packing KS（回切统一输出钥）与逐 lane LUT packing 仍是标量
  O(r) 尾。
- 已接受的全自举加速（Stage 8/10，spqlios，clear-elision）：r=2 1.269x、
  r=4 1.337x；后续融合头部记录到 1.6x-1.75x（stage346）。

### 3.5 密钥层

- 686 BSK：(h+1)·log B 个 GSW（d[i] 的逐 bit）+ 标量 ksk —— "small keys"。
- MAT BSK：同样 (h+1)·ρ 个 **MAT_TRGSW**（每行是完整 PVW_TMLWE 样本）+
  pvmtmlwe aut-KS。选择子族多项式数比值 `(k+r)² / (r·(k+1)²)`
  （r=2: 1.125；r=4: 1.5625），但整个钥束实测只有 1.0136x（r=2）/1.0653x
  （r=4），因为 packing/HW/输入侧钥材共享；keygen 约 1.24x/1.18x（roadmap
  Stage 7 记录）。

## 4. 适配算法清单（因数学结构不同而必须/引入的部分）

### 已实现（A1-A8）

- **A1 多体状态与逐步相位不变量**（§2.1/§2.2）：686 的正确性是逐 lane 标量
  引理（Lemma 4.1-4.3），批处理需要重新表述为多体对象上 r 个相位各自复现
  标量递推；ping-pong 双缓冲（`SAB_PVW_Accumulator_State`）避免位轮间拷贝。
- **A2 共享 mask MAT 外积内核**（§2.4，mattrgsw.c）：把 686 的 ⊙ 扩展为
  对角 gadget 的多体版本；dense 累加 (k+r)²l；clear-elision（首行 mul 初始化
  +其余 addmul）消掉输出清零遍。
- **A3 多体 `X→X^{-1}` 自同构 + 专用 aut-KS**（sab_pvw.c:713/350）：686 没有
  的钥型；NCMUX 语义保持的关键。
- **A4 MAT 选择子物化**（sab_pvw.c:239 `sab_pvw_encrypt_bits` /
  mattrgsw.c:238）：直接复用 686 的 d[i] 逐 bit 调度，`mat_trgsw_monomial_sample`
  把 bit 加密为对角常数（e=0）；非二进制族 `s_coff`（include-zero，对应
  Alg 4 的 `V_i ∈ GSW(X^{s_j~})` 结构）与 `s_sign`（ternary，对应 Alg 3 控制
  位 `V_k`）由 stage251-260 落地。
- **A5 调度级融合**（不改变代数的三类变换）：
  - dual-sub 配对（`SAB_PVW_DUAL_SUB_CMUX`，sab_pvw.c:761/817）：MPmul 位轮内
    位置 j 的 NCMUX 与位置 j+2^i 的 CMUX 共享三个操作数，两次差分一遍算完；
  - sub_decomp 融合（`SAB_PVW_SUB_DECOMP_FUSION`，mattrgsw.c
    `mat_trgsw_mul_pvmtmlwe_sub_DFT`）：利用分解的逐位线性
    `G^{-1}(x-y) = digits(x-y)`，让外积直接吃差分，省独立减法遍；
  - from_DFT_add 融合（`SAB_PVW_FUSED_FROM_DFT_ADD`）：iDFT 与 "+in1" 合一。
- **A6 逐 lane 提取**（sab_pvw.c:280）：Alg 6 line 7 的提取规则对 lane q 的
  共享 mask + 体 q 逐 lane 应用；`sab_pvw_trlwe_key_from_lane`(:262) 提供
  lane 专属输出钥视图。
- **A7 标量尾部保持**：输入侧 packing/HW-KS 与输出侧逐 lane packing KS 仍走
  686 标量路径（§3.4 尾部），保证输出与标量完全一致。
- **A8 r 专用内核**（mattrgsw.c :321/:393/:465/:625/:687 等）：r=2/4/6/8 的
  AVX512 展开，属工程适配，不改变 §2.4 代数。

### 开放路线（O1-O4，均已在既有文档立项）

- **O1 PVW 感知后处理**：消掉 O(r) 尾（pvw_sab_complexity_model 条件 2）；
  `PVW_LUT_Packing_KS_Key`/`PVW_Generic_KS_Key` 类型已在 mosfhet.h:151-159
  预留，但 `pvmtmlwe_keyswitch` 仍是 aborting stub（goal audit 记录），
  SAB 路径未接入。
- **O2 结构化/紧致选择子**：绕开 dense (k+r)²（stage346 路线 1；stage329
  证明义务清单；条件 1：`C_ext_mat` 降到 (k+r)² 之下）。
- **O3 当前格式下界**：证明 dense 离 lane 工作在所允密钥/状态模型内不可避免
  （stage346 路线 2）。
- **O4 r>4 扩展**：受 §3.2 胜利条件约束，需 O1/O2 先行（h10/h11 记录）。

## 5. 适配的"必要性"小结（为什么 686 框架不能直接用）

1. 686 的正确性/噪声引理全部以单相位 RLWE 为对象；多体对象有 r 个相位，
   必须以不变量 I(t) 重建正确性叙事（A1）。
2. 686 的选择子是"加密一个 bit 的 GSW"；批处理要求同一个加密 bit 同时对
   r 个不同输出钥生效，等价于对角 gadget 的矩阵 GSW（A2/A4），其代价结构
   (k+r)²l 是 686 框架中不存在的新项。
3. 686 的 NCMUX 自同构假设对象是单条 RLWE；多体对象的 X→X^{-1} 需要新的
   多体自同构钥（A3）。
4. 686 的摊销维度是 n（系数槽）；MAT 增加第二个正交维度 r（lane）。两者可
   乘性组合：一次盲旋转同时刷新 r·n 条消息，且 BSK 调度材料不变
   （仍 (h+1)·log B 个位置）。
5. 686 的 packing KS / HW-KS / extract 是标量对象操作；多体输出需逐 lane
   物化回标量（A6/A7），该尾部目前未摊销（O1）。

## 6. 主张边界

- 本文档不主张：MAT 批处理是 686 已提出的内容（stage102：PVW/MAT 是本地
  增量）；不主张 PVW packing 为新想法、MAT 外积理论最优、或新的 SAB 渐近
  （mat_rlwe_sab_literature_claim_boundary 禁止项）。
- §2.4 相位代数与 §3.3 噪声论证是设计代数/启发式界，证据等级为逐步等价
  测试 + 多种子噪声对照，不是论文级定理。
- 性能数字引用 Stage 8/10 已接受记录（r=2 1.269x / r=4 1.337x）与 stage346
  的 1.6x-1.75x 头部记录；未含统计处理的更高主张仍被 stage206 边界约束。
