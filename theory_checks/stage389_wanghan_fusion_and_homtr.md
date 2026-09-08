# Wang Han 20260908V1 融合分析与 Hom-Tr 实现计划

Date: 2026-09-08
决策：融合为一篇投 Eurocrypt；Hom-Tr 在仓中实现并 benchmark。

---

## 一、理论融合方案

### Wang Han 的贡献（论文 §3 的理论骨架）

| 组件 | 内容 | 融合位置 |
|---|---|---|
| Mat-MGSW/Vec-MLWE 定义 | 双模数 T>Q，尺度化外积 ⊡ = ⌊C·c·Q/T⌉ | §3.1 密码系统定义（主引理来源） |
| Lemma 1.7 噪声界 | 完整次高斯分解：γ' = √(Q²/T²·γ₁² + γ₂² + Q²/T²·γ₃² + γ₄²) | §3.5 噪声分析主引理 |
| Corollary 1.8 应用特化 | monomial + 三元 + 均匀闭式 | §3.5 推论 |
| Algorithm 1 P-MPMUL | r-lane 蝶形（= 我们的 sab_pvw_RGSW_monomial_mul） | §3.2 主算法 |
| Algorithm 2 Packing BIN-SAB | 完整自举含 Hom-Tr | §3.3（我们补充 DualSubCMUX + G-ρ） |
| Hom-Tr | 同态变换版 sub_a | **本文件 §二：实现计划** |

### 我们的贡献（论文 §4-§5 的全部数据）

安全（CRYPTO'26 修正定案 130.4 + BatchBoot 全 FAIL + 层审计 + DFR
certified + E1 CI）、实验（六行矩阵 1.66-1.84× + r 选值 + ternary +
组件画像 + 否定性结果 F1/C5）、工程（MOSFHET 实现 + 7 旗标 +
DualSubCMUX k=2 拓扑上限 + G-ρ 一般稀疏 + SQ p 域 + M3/M3' 推论）。

### 融合后的论文结构（更新骨架 v0 → v1）

```text
§1  Introduction                    ← 4 贡献（安全/算法+证明/实测/否定性）
§2  Preliminaries                   ← Wang Han §1（记号/MLWE/次高斯工具）
§3  The Algorithm                   ← Wang Han §1.3-2 + 我们扩展
  3.1  Scale-based external product  ← Wang Han Mat-MGSW/Vec-MLWE + ⊡
  3.2  P-MPMUL butterfly            ← Wang Han Alg 1 + 我们 DualSubCMUX 证明
  3.3  Full bootstrapping           ← Wang Han Alg 2 + 我们 G-ρ / ternary
  3.4  Hom-Tr vs plaintext sub_a    ← 新：对比分析 + benchmark
  3.5  Noise analysis               ← Wang Han Lemma 1.7/Cor 1.8 + 我们 Thm 2 标定
  3.6  Amortization law             ← 我们 M3 + M3'（Wang Han 未涉及）
§4  Security under corrected attacks ← 全部我们
§5  Implementation and experiments  ← 全部我们
§6  Related work
§7  Conclusion
```

---

## 二、Hom-Tr 变体分析与实现计划

### 2.1 Wang Han 的 Hom-Tr 是什么

从 Algorithm 2 第 9 行：
```text
Hom-Tr(ci · ∏ⱼ₌₁ʳ X^{-aj[k]} · α∨ⱼ · βⱼ)
```

**解读**：对累加器槽 c_i 施加**同态旋转变换**，将每个 lane j 的贡献
乘以 X^{-a_j[k]}（减去 a·s 的第 k 个系数贡献），并以 α∨ⱼ·βⱼ 加权。

**与我们 sub_a 的关键区别**：

| | 我们的 sub_a（binary） | 我们的 sub_a_ga（ρ-SAB） | Wang Han 的 Hom-Tr |
|---|---|---|---|
| 机制 | 明文单项式乘 X^{-a_k} | 双自同构 + 外积 | 同态变换 + 密钥切换 |
| 噪声 | **零**（‖X^a‖=1） | 2 aut-KS + 1 EP 噪声 | aut-KS 噪声（量级待实测） |
| 速度 | **最快**（纯 torus 系数旋转） | 最慢 | 中间（每槽一次 aut） |
| 通用性 | 仅 binary（s ∈ {0,1}） | 一般稀疏（ρ-SAB） | 理论上最通用 |
| 双模数兼容 | SQ 已处理（精确升降尺度） | ✓ | ✓（原生设计） |

### 2.2 实现方案

**Hom-Tr 本质上 ≈ 我们的 `pvmtmlwe_eval_automorphism(c_i, w, KSK)`**
（对累加器槽施加同态自同构 X→X^w，再 KS 回原钥），其中 w = -a_j[k]。

**区别**：Hom-Tr 作用于 Vec-MLWE 的**整个多体槽**（一次 aut 同时处理
r 体），而非逐 lane——这正好是 `pvmtmlwe_eval_automorphism` 的行为。

**实现**：
```c
void sab_pvw_sub_a_homtr(PVW_TMLWE *p, const uint64_t *a,
    PVW_TMLWE_KS_Key *aut_family, SAB_PVW_Key sab) {
  for (size_t i = 0; i < sab->in_N; i++) {
    // Hom-Tr: 同态旋转 X^{-a[i]} + KS（对整个多体槽）
    const uint64_t w = (2 * sab->out_N - a[i]) % (2 * sab->out_N); // -a mod 2N
    pvmtmlwe_eval_automorphism(p[i], p[i], w, aut_family[(w-1)>>1]);
  }
}
```

**注意**：这需要 out_N 个奇指数自同构 KS 钥（与 G-ρ 的 aut_family 相同
基础设施）。我们已有该基础设施（stage375 G-ρ 实现中已建）。

### 2.3 Benchmark 判据

| 指标 | 预期 | 判定 |
|---|---|---|
| 正确性 | 0 失配（vs 标量 oracle） | 必须过 |
| 噪声 | 高于明文 sub_a（引入 aut-KS 噪声），低于 sub_a_ga（少一次外积） | 预测/实测 <1.3 |
| 速度 | **慢于明文 sub_a**（每槽一次 aut+KS vs 纯系数旋转），**快于 sub_a_ga**（少一次外积） | 记录实际比值 |
| 论文价值 | "两种 sub_a 设计的权衡表"（明文最快/Hom-Tr 最通用/ρ-SAB 中间） | 定性贡献 |

### 2.4 预估

- 实现：~30 行 C（复用 pvmtmlwe_eval_automorphism + aut_family）
- Benchmark：1 个 dell 会话
- 与现有路径的 A/B：同构建内配对（sub_a_homtr vs sub_a_binary vs sub_a_ga）
