# r-Input Batching + Hom-Tr 实现计划

Date: 2026-09-08
用户确认：需要实现"两种正交 batching 维度"（r-LUT + r-input）。

---

## 一、核心数学约束（为什么不能简单修改现有代码）

### 1.1 共享 mask 的限制

当前 PVW_TMLWE 的共享 mask 结构：
```text
密文：(a; b₀,...,b_{r-1})，密钥 (s₀,...,s_{r-1})
lane q 相位：φ_q = b_q − a·s_q
```

统一旋转 X^v 保持不变量：φ_q' = X^v·φ_q（mask 和全部 body 同时旋转）。

**r-input 需要的差异旋转**：
```text
lane j 需要：φ_j' = X^{-a_j[k]}·φ_j
要求：      b_j' = X^{-a_j[k]}·b_j 且 mask' = X^{-a_j[k]}·a
矛盾：      mask' 对不同 j 不同 → 共享 mask 不变量被破坏
```

**这是数学约束，不是实现问题**。body-packing + 共享 mask 结构性不支持
per-lane 差异公开旋转。

### 1.2 Wang Han 的解决方案：交织打包 + 迹提取

```text
N = r·d，Y = X^r，R = Z[X]/(X^N+1) 为 A = Z[Y]/(Y^d+1) 的秩 r 扩张

交织打包：m = Σⱼ X^j · mⱼ(Y)     （lane j 占 X 的 j mod r 位置）
目标变换：L_a(m) = Σⱼ X^j·Y^{-aⱼ}·mⱼ(Y)

固定子群：H = {σ_{1+2dℓ} : 0 ≤ ℓ < r}   （不随 a 变化）
迹提取：  T_H(X^{-j}·m) = r·mⱼ(Y)
整数版：  U_a(m) = Σ_{w∈H} P_w·σ_w(m) = r·L_a(m)
```

**关键优势**：迹子群 H 固定（≤ r-1 个非平凡自同构，不随 a 变化），
只有公开权重 P_w 随 a 重算。

---

## 二、模数消耗的定量约束

### 2.1 问题

除以 r 在二幂 torus Z_{2^64} 上无逆元。参考方案：预置 Q_in = r·Q_out，
每步消耗 log₂(r) bit。

### 2.2 参数下的可行性

| 参数 | h | r | 总消耗 h·log₂(r) | q_start = q_final + 消耗 | 64-bit 内？ |
|---|---|---|---|---|---|
| SET_2_3_2048, r=2 | 42 | 2 | 42 | 16+42=58 | ✅（余量 6 bit） |
| SET_2_3_2048, r=4 | 42 | 4 | 84 | 16+84=100 | ❌（超 36 bit） |
| SET_4_5_2048, r=2 | 42 | 2 | 42 | 16+42=58 | ✅ |
| 任意, r=4 | 42 | 4 | 84 | 100 | ❌ |

### 2.3 r=4 的解决方案

**方案 A：分步执行 Hom-Tr，中间降尺度**
- 每 log₂(64/q) 步做一次"模数恢复"（重新量化到 q 位）
- 相当于周期性地把中间结果从高精度降回工作精度
- 引入额外舍入噪声，需重新推导噪声界

**方案 B：使用 Wang Han 的显式双模数 T > Q**
- T 可以 > 64 bit（如 T = 2^128，用双精度或 RNS）
- 外积在 T 模下计算，降回 Q 模时自然消耗模数
- 需要实现 ModUp/ModDown 操作（Wang Han 的 §1.4）

**方案 C：r=2 先行，r=4 作为扩展**
- r=2 的模数消耗在 64-bit 内可行（58 bit < 64）
- 先实现并验证 r=2 的 r-input batching
- r=4 需要方案 A 或 B，作为后续扩展

**建议**：方案 C（r=2 先行），理由：
1. r=2 已足以验证 Hom-Tr 的正确性和性能
2. 避免引入多精度算术的复杂度
3. r=2 的结果可以直接与 r-LUT r=2 对比
4. r=4 扩展是增量工作（方案 A 或 B）

---

## 三、实现架构（方案 C：r=2 先行）

### 3.1 新增/修改组件

| 组件 | 类型 | 内容 |
|---|---|---|
| **交织打包/解包** | 新增 | body-packing ↔ interleaved-packing 转换 |
| **迹操作** | 新增 | 固定子群 H 的迹 T_H（用现有 aut_family） |
| **权重计算** | 新增 | P_w 公开多项式（每步根据 a 重算） |
| **尺度管理** | 新增 | q 位跟踪 + 右移除 r + 舍入 |
| **multi-input sub_a** | 新增 | Hom-Tr 版 sub_a（替代明文乘） |
| **multi-input setup** | 新增 | r 个输入密文的初始装配 |
| **bootstrap_multi_input** | 新增 | 完整自举管线（r-input 版） |

### 3.2 与现有代码的关系

```text
共用（不修改）：
  - sab_pvw_RGSW_monomial_mul_state（蝶形，统一旋转）
  - MAT_TRGSW 选择子物化
  - mat_trgsw_mul_pvmtmlwe_DFT（矩阵外积）
  - 提取 + packing KS

新增（并行路径）：
  - 交织打包/解包（body ↔ interleaved 转换）
  - 迹操作（复用 aut_family 基础设施）
  - Hom-Tr sub_a（替代明文乘，处理不同 a_j）
  - multi-input setup + bootstrap wrapper
```

### 3.3 r=2 的具体参数

```text
N = 2048（现有 out_N）
r = 2 → d = N/r = 1024
Y = X^2
H = {σ₁, σ_{1+2d}} = {identity, σ_{2049}}  （1 个非平凡自同构）
P_w 对 w=σ₁：X^{0 - 2·a₀} + X^{(1-1) - 2·a₁} = X^{-2a₀} + X^{-2a₁}
P_w 对 w=σ_{2049}：X^{(1-2049) - 2·a₀} + X^{(2049-1) - 2·a₁}  mod 2N

模数管理：
  q_start = 16 + 42 = 58
  每步右移 1 bit（除以 r=2）
  最终 q = 16
```

### 3.4 预估工作量

| 阶段 | 内容 | 会话 |
|---|---|---|
| Phase 1 | 交织打包数学验证（GF(257) 小参数检查器） | 0.5 |
| Phase 2 | C 实现（打包/迹/Hom-Tr sub_a/bootstrap） | 1.5 |
| Phase 3 | 正确性门（vs r 个独立标量 oracle） | 0.5 |
| Phase 4 | 噪声对账 + benchmark | 0.5 |
| **合计** | | **3 会话** |

---

## 四、正确性验证方案

### 4.1 Oracle

r 个独立标量 SAB 自举（每个用自己的输入密文），逐 slot 比较：
```text
φ_lane_j(matrix_output) == φ(scalar_SAB_j(output))
```

### 4.2 中间验证

- 单步 Hom-Tr 正确性（交织打包 + 迹提取 + 重组合）
- 单步蝶形 + Hom-Tr 链
- 完整自举

### 4.3 噪声门

- Hom-Tr 引入的 aut-KS 噪声 + 舍入噪声
- 与 r-LUT 路径的噪声对比（应同阶，Hom-Tr 多 aut-KS 项）
