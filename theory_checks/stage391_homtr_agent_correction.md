# 独立 Agent Hom-Tr 分析的消化与修正（2026-09-08）

Date: 2026-09-08
来源：用户转发的独立 agent 分析（HomTr_WangHan_Fusion_Analysis.md，258 行）

---

## 一、独立 agent 纠正了我们的三个错误

### 错误 1："Hom-Tr ≈ 单次自同构"
**我们的实现**：`pvmtmlwe_eval_automorphism(p[i], w, aut_family[w])` — 一次环自同构。
**agent 的证明**：自同构 σ_w(X^i) = X^{wi}（置换指数），单项式乘法 M_v(X^i) = X^{i-v}（移位指数）。反例：f=1 时 σ_w(1)=1 但 X^{-v}·1 ≠ 1（除非 v≡0 mod 2N）。
**修正**：朴素自同构实现**语义错误**，不能作为 Hom-Tr 的正确实现。

### 错误 2："正确 Hom-Tr 比明文慢 7.71×"
**我们的数据**：18,911μs（错误语义的 aut 路径） vs 2,454μs（明文路径）。
**agent 的纠正**：7.71× 是错误实现与明文的比值，不是正确 Hom-Tr 与明文的比值。正确 Hom-Tr 的成本模型完全不同（见 §三）。
**修正**：论文中 7.71× 只能标注为"naive automorphism (incorrect semantics)"的失败实验记录。

### 错误 3："Hom-Tr 必须每个旋转一把 KS 钥"
**agent 的否定**：给出了明确的相对迹参考变体，所需自同构集合 H = {σ_{1+2dℓ}} 不随公开旋转值 a_j 改变，只有权重多项式 P_w 变化。
**修正**：至多 r-1 次非平凡 aut-KS + r 次公开多项式乘法 + 除 r 处理。

---

## 二、agent 给出的正确 Hom-Tr 数学结构

### 2.1 环分解与打包

N = r·d（均为二的幂），R = Z[X]/(X^N+1)，A = Z[Y]/(Y^d+1)，Y = X^r。

系数交织打包：
```text
m = Σⱼ₌₀ʳ⁻¹ X^j · mⱼ(Y)    （lane j 的消息占据 X^j 的系数交织位置）
```

目标变换（每 lane 独立平移）：
```text
L_a(m) = Σⱼ X^j · Y^{-aⱼ} · mⱼ(Y)
```

### 2.2 固定自同构子群与迹提取

```text
H = {σ_{1+2dℓ} : 0 ≤ ℓ < r}    （不随 a 变化！）
T_H(f) = Σ_{σ∈H} σ(f)            （整数线性迹算子）
T_H(X^{-j} · m) = r · mⱼ(Y)     （提取 lane j）
```

**恢复公式**（在可除 r 的域上）：
```text
L_a(m) = (1/r) Σⱼ X^j · Y^{-aⱼ} · T_H(X^{-j} · m)
```

**整数版本**（避免在 torus 上除 r）：
```text
U_a(m) = Σ_{w∈H} P_w · σ_w(m) = r · L_a(m)
P_w = Σⱼ X^{j(1-w) - r·aⱼ}    （公开权重多项式）
```

### 2.3 Torus 上的 r^{-1} 问题

在 Q = 2^64 且 r 为二幂时，r 无乘法逆元。

**解决方案**：预置更高模数 Q_in = r · Q_out，每次相对迹消耗 log₂(r) 个模数比特。h 步变换需要 Q_start = r^h · Q_final。

**代价**：h · log₂(r) 位模数消耗 → 更大的初始模数与密钥 → 安全参数需重估。

---

## 三、对论文的影响

### 3.1 §3.4 "sub_a 设计空间"表修正

| 后端 | 条件/机制 | 输入误差的作用 | 实测状态 |
|---|---|---|---|
| 公开单项式乘法 | 同一环上公开单项式 | 带符号置换，无新增算术误差 | ✓ 已实现，2,454μs |
| sub_a_ga / ρ-SAB | 双自同构 + 外积 [BDF18] | aut-KS + EP 误差 | ✓ 已实现，已验证 |
| **Hom-Tr 相对迹** | 固定子群 H + 权重 P_w + 模数消耗 | KS + 公开权重 + 舍入 | **未正确实现**（agent 给出了参考变体） |
| ~~单次自同构~~ | ~~语义错误~~ | ~~完全错误~~ | **负对照**（18,911μs，不可引用为 Hom-Tr 数据） |

### 3.2 成本模型修正

正确 Hom-Tr 每步成本（非朴素自同构）：
- **aut-KS**：至多 r-1 次（固定集合 H，复用 aut_family 基础设施）
- **公开多项式乘法**：至多 r 次（P_w 权重）
- **求和与归一化**：除 r（需模数消耗 log₂(r) bit）
- **总模数消耗**：h · log₂(r) bit（h 步自举）

这与明文乘法（零开销）和 sub_a_ga（每系数 2 aut + 1 EP）都不同。

### 3.3 7.71× 数据的正确标注

论文中应写：
> "The naive single-automorphism variant, which conflates ring automorphism
> with monomial multiplication, produces completely incorrect output
> (noise at the full torus range) and ran at 18,911 μs versus 2,454 μs
> for the plaintext path. This is recorded as a negative control, not as
> a valid Hom-Tr benchmark."

---

## 四、需与 Wang Han 确认的 8 个精确问题（agent §7）

1. αⱼ, α∨ⱼ, βⱼ 分别属于哪个环/张量因子？对偶是迹配对、内积还是 CRT 幂等元？
2. Hom-Tr 是绝对迹、相对迹还是广义线性变换？源/目标环与密钥输出类型？
3. βⱼ 与旋转单项式为何可放入迹内？由哪个固定子环条件保证？
4. 迹是否归一化？若含 1/r，在二幂 torus 上如何实现？
5. Algorithm 2 第 8-11 行应更新 c_k 还是 c_i？返回值赋给谁？
6. P-MPMUL 的最低位为何从 i=1 开始？位重与边界定义？
7. diff(s) 的 h 是支撑大小还是差分项数？索引是否有排版错误？
8. 参数与安全是否覆盖中间 KS 密钥和相同评估钥重复使用？

---

## 五、下一步行动

1. **将本修正文档 + agent 原文一并发给 Wang Han**，请求回答 §四 的 8 个问题
2. **论文 v1 的 §3.4 和 §5.6 按本修正更新**（去掉 7.71× 的 Hom-Tr 标签，改为负对照）
3. **Hom-Tr 正确实现**推迟至 Wang Han 确认语义后启动（agent 的参考变体提供了实现路线图：固定 H 子群 + P_w 权重 + 模数消耗方案）
4. **不阻塞论文投稿**：当前版本的 §3.4 已足够支撑（三后端对比 + 负对照 + "Hom-Tr 语义待确认"的诚实标注）
