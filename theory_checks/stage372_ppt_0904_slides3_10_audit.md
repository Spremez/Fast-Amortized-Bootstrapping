# Stage372 Audit: 0904 PPT (20260904.pptx) Slides 3-10 vs 当前矩阵外积实现

Date: 2026-09-04
范围声明：仅核对用户指定的第 3-10 页；其余页不参考。
对象：`C:\Users\spremez\Downloads\20260904.pptx`（686 论文介绍 + 第 10 页
Mul-LWE 批处理外积形式）。实现锚点：`src/sab_pvw.c`、`src/sab_pvw_sq.c`、
`src/mosfhet/src/mattrgsw.c`、`src/mosfhet/src/pvwtmlwe.c`、
`src/sparse_amortized_bootstrap.c`（686 标量）。

## 逐页核对表

| 页 | 内容要求 | 实现状态 | 判定 |
|---|---|---|---|
| 3 | 定位：一次刷新多条 × 多项式噪声 × 小密钥的缺口 | 矩阵自举一次刷新 n·r 条（n 槽 × r lane）；噪声与 686 同阶（M2 + S7 81,920 点 pair 0）；钥 ≤1.07×（Stage207） | ✓ 满足（定位层） |
| 4 | 病根=密文×密文 GSW 乘法；机会=全部替换为外积+自同构 | `sab_pvw.c` 全部热路径操作 = MAT 外积（MV-EP）+ 多体自同构（τ₋₁）+ 明文单项式乘；**无任何密文×密文乘法** | ✓ 满足 |
| 5 | 五步流水线 Packing → 同态解密(MPmul) → FBS/测试向量 → Extraction → 低噪声批量输出；总外积 O(hN·log(N/h))、单条摊余 O(h·log(N/h)) | 五步齐备：LUT packing/打包 KS、`sparse_mul`（MPmul 链）、`setup_tv_xb` 测试向量、逐 lane 提取、输出 KS；外积计数 (h+1)·ρ·n 与 686 完全一致（M3；stage322 实测 616,448@h42） | ✓ 满足 |
| 6 | MPmul 蝶形：位移 v 逐位决策（桶形移位器），每轮 1 次外积 + 1 次自同构，⌈logB⌉ 轮，负循环负号 | `sab_pvw_RGSW_monomial_mul_state`（sab_pvw.c:861）逐位镜像：NCMUX 环绕槽（τ₋₁ 多体自同构带符号翻转）+ CMUX 直达槽；DualSubCMUX 为代数保持的共享减法优化（k=2 拓扑上限已证） | ✓ 满足 |
| 7 | Algorithm 1 拆解：跨界槽自同构取回；内部槽纯 CMUX；n·logB 外积主导、≤B 次自同构、噪声 √(logB) 加性 | 同上逐行对应；自同构换为多体版（`pvmtmlwe_eval_automorphism` + 专用 aut-KS 钥 `aut_minus1`），计数与 686 相同 | ✓ 满足 |
| 8 | 嵌套外部积（Horner 链 h+1 次 MPmul、减 a 明文免费）；三变体 bin/tern/ρ | bin ✓（binary + include-zero 矩阵分支，全量实测）；tern ✓（`sab_pvw_sub_a_ternary` + `s_sign` 控制位，stage251-260 等价门过；但 FINAL 参数下性能未采集）；**ρ-SAB：标量 `sub_a_ga`（双 RLWE 自同构+1 外积，BDF18）已实现，矩阵（PVW）分支未接入**——`sab_pvw_sparse_mul_nonbinary` 仅支持 include-zero/ternary，gaussian 直接 die | ⚠ 部分（1 结构缺口 + 1 数据缺口） |
| 9 | Algorithm 2 bin-SAB：初始化 MultPtxt(t_i, X^{b_i})、主循环 h 次 {MPmul, 减a}+收尾 MPmul、输出 t_i·X^{u_i}（查表一次完成）、BSK = h·⌈logB⌉ GSW + 1 ksk | 矩阵路径逐行对应：`sab_pvw_setup_tv_xb`（TV=PVW 多体平凡样本，r 条 LUT 各占一体）/ `sab_pvw_sparse_mul_binary` / `sab_pvw_sub_a_binary`（明文单项式乘作用于全部 k+r 分量，零噪声）；BSK = (h+1)·ρ 个 MAT_TRGSW + 1 个多体 aut-KS，实测钥束 ≤1.07× | ✓ 满足 |
| 10 | **Mul-LWE 批处理形式**：c=(b,a)∈R_q^{n+r}，b[i]=⟨a,s_i⟩+e[i]+q/2·m[i]，S=(s₁ᵀ,…,s_rᵀ)∈R_q^{r×n}；尺寸账 单条 1⇔n+1 / r 条 r⇔n+r / 摊余 1⇔n/r+1 | `PVW_TMLWE = (a; b_0..b_{r-1})`（mosfhet.h:128，k=1 即 1+r 分量）+ `PVW_TMLWE_Key s[k][r]`（列=各 lane 秘密，即 S 的行）= Mul-LWE 的 RLWE(k=1) 实例化；"n/r+1" 摊余账即 M3 行积定律 (k+r)/r = 1+1/r（r=4 结构上限 1.25×，实测 1.21×）；批处理外积 = 对角 MAT_TRGSW 的 MV-EP（M1 lane 正确性 / M2 无跨体噪声） | ✓ 满足 |

注：第 10 页的 Mul-LWE 形式与 ePrint 2025/1711 的 Vec-MLWE（Thm 4.1/4.2）同构
——按 2026-09-04 两层叙事，属"内层来自 1711（本团队前作）"的引用与实例化，
论文措辞走 instantiate/adapt/prove 纪律。

## 结论

第 3-10 页的内容，当前矩阵外积实现**总体满足**（9/10 页 ✓），唯一结构性缺口：

**G-ρ（第 8 页）**：ρ-SAB（一般稀疏秘密，非零位 ∈ [−ρ,ρ]，Z₈ 等任意取值）的
矩阵分支未实现。修复路径明确：把标量 `sub_a_ga`（两次 RLWE 自同构 + 1 次
外积）矩阵化为"两次 `pvmtmlwe_eval_automorphism` + 1 次 MAT 外积"——多体
自同构 KS 基础设施已有（`aut_minus1` 同族），缺的是逐系数调度与系数选择子族
（对应 686 Alg 4 的 V_i ∈ GSW(X^{s̃_j})）的矩阵物化 + 等价门。建议并入外层
设计文档的"密钥—形式协同"章节统一立项。

**次级缺口（数据层，非结构）**：ternary 矩阵分支仅有 stage251-260 的小规模
等价门，未在 FINAL（h=42/σ_G=2⁻⁴⁹）参数下采集性能/噪声数据；若论文需要
"二元→三元 <10%"的矩阵版主张，需补一次 stage 化实测。

## 与本轮其他指令的衔接

- F1（MAT-EMPmul）已按用户指令纳入外层设计范围（δ=2 多比特步 = radix>2
  蝶形实例，G1 检查器可复用），与本审计互补：本审计核对"是否满足 686 框架
  全语义"，F1 扩展"选择子步本身的形式"。
- 报告口径自本文档起：加速比一律 686/我方；686 原实现直接称 "686"，
  无旗标矩阵路径称"矩阵基线构建"。

## 补遗（2026-09-04 用户指令"关注第 11 页"）：Mul-GSW 与批处理外积定义

第 11 页在第 10 页 Mul-LWE 之上定义**Mul-GSW 密文与外积原语**（OMML 还原）：

```text
Mul-GSW 密文 C：加密向量 m' = (m'_1, ..., m'_r)
  C = [KSK₀ ; KSK₁] = [S·A + E ; A] + [M' ··· ; 0 ···]     # KSK 形式，消息在对角体块
gadget：p ∈ R_q^{(n+r)×(n+r)}
外积：  ⊡ : Mul-GSW × Mul-LWE → Mul-LWE
        (C, c) ↦ C ⊡ c = (1/p)·C·c
结果：  加密 (m'_1·m_1, m'_2·m_2, ..., m'_r·m_r)           # 逐 lane 分量积
```

与实现逐条对照：

| 第 11 页对象 | 实现 | 判定 |
|---|---|---|
| Mul-LWE 密文 c | `PVW_TMLWE`（见上表第 10 页行） | ✓ |
| Mul-GSW C（KSK 形式 [SA+E; A] + 对角消息） | `MAT_TRGSW`：行为多体钥下的新鲜 PVW_TMLWE 样本 + 对角 gadget 消息放置（`mat_trgsw_monomial_sample`）。KSK 显式矩阵形式与"新鲜样本加密"形式是 GSW 的两种等价生成方式，对象相同 | ✓（生成形式等价） |
| gadget p ∈ R_q^{(n+r)×(n+r)} | identity⊗g 结构，h_d = 2^{64−(d+1)Bg}；FINAL 为 l=1/Bg=2^23（n=k=1 ⇒ (1+r)×(1+r)） | ✓ |
| ⊡ = (1/p)·C·c | `mat_trgsw_mul_pvmtmlwe_DFT`：先 G^{-1}(c)（即 1/p 的数字分解实现），再 dense 行积求和 | ✓ |
| 结果加密 (m'_1m_1, …, m'_r m_r) | M1 定理：φ_q(C ⊡ c) = m'_q·φ_q(c) + ε_q；M2 保证无跨体放大 | ✓ |

**判定：第 11 页满足。** 唯一细化口径与第 10 页相同：实现实例化的是
**均匀对角**（m'_1 = … = m'_r = 同一选择子 bit，SAB 共享调度所需）；
一般形式允许每 lane 不同 m'_q，其代数已被 M1 的对角证明覆盖，但
`mat_trgsw_monomial_sample` 只暴露单一 m 参数——**per-lane 采样器变体
（消息向量入参）是约 ~10 行的小扩展**，若外层设计的 C6（lane 级混合精度）
或晚绑定需要每 lane 独立选择子再启用。
