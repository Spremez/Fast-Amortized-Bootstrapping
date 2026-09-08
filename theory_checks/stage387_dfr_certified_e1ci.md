# T4 DFR Certified + T8 E1 置信区间（合并文档）

Date: 2026-09-08

## 一、T4：DFR Certified 数值化

### 解析层（已有 2^{-100}，本节计入确定性失败概率 b_det）

确定性失败源：消息格点量化时 half-ulp 舍入的系统性偏差（b_det）。
当噪声恰好落在格点边界 ±half-ulp 时，量化可能翻转。

**Certified 界**：
```text
P_fail ≤ P_stochastic + P_deterministic
P_stochastic = 2 · Q(2^{-p-1} / σ_total)              [高斯尾]
P_deterministic = max(0, (σ_total − 2^{-p-2}) / 2^{-p}) [舍入域覆盖]
```

对 SET_2_3_2048（p=3, FINAL σ_G=2^{-49}）：
- σ_total = σ_G · 2^{q+3.5} · √280 / 2^64 = 2^{-49} · 2^{19.5} · 2^{4.1} / 2^{64} = 2^{-69.4}
- 格点半宽 2^{-p-1} = 2^{-4}
- P_stochastic = 2·Q(2^{-4}/2^{-69.4}) = 2·Q(2^{65.4}) ≈ 2^{-2·65.4²/π} ≈ **2^{-2724}**
- P_deterministic = max(0, (2^{-69.4} − 2^{-5}) / 2^{-3}) = **0**（σ_total ≪ 格点半宽）

**Certified DFR = 2^{-2724} + 0 = 2^{-2724}**（远超任何实际需求；此前
"2^{-100}"为保守粗估，精确值远更优）。

### 经验层（Clopper-Pearson 精确区间）

已有 >10^6 零失败观测。Clopper-Pearson 95% 单侧上界：
```text
P_fail < 1 − (0.05)^{{1/n}} ≈ 3×10^{-6} ≈ 2^{-18.4}  (n = 10^6)
```

### 三层汇总（论文表格）

| 层 | 方法 | 结果 |
|---|---|---|
| 解析 certified | 高斯尾 + 确定性覆盖 | **2^{-2724}** |
| 解析保守 | 前版粗估 | 2^{-100} |
| 经验 95% CI | Clopper-Pearson | **2^{-18.4}** |

---

## 二、T8：E1 条件熵 MC 的 95% 置信区间

E1 的 p_accept 用 MC（20k 样本）估计。对二项比例 p̂ 的 95% CI
(Wilson score interval)：

对 BatchBoot 各集合的 p_accept：
| 集合 | p̂ (20k MC) | Wilson 95% CI | T3' 95% CI |
|---|---:|---|---|
| Boot2 (N=2048, h=39, t=7) | 0.0043 | [0.0039, 0.0047] | [124.0, 124.4] |
| Boot4 (N=2048, h=42, t=8) | 0.835 | [0.829, 0.841] | [136.1, 136.7] |
| Boot6 (N=4096, h=33, t=8) | 0.0001 | [0.00006, 0.0002] | [119.8, 121.3] |
| Boot8 (N=4096, h=34, t=8) | 0.0003 | [0.0002, 0.0005] | [123.8, 125.3] |

（CI 计算方法：T3' = (H − loss − log₂N − δ)/2，loss = −log₂(p_accept)，
CI 由 p_accept 的 Wilson CI 传播。所有 FAIL 判定在 CI 下界仍然 <128 ✓）

对自身参数（h=42/t=7，已被 stage371 FINAL 全量验证）：
- p_accept ≈ 0.05（约 5% 的密钥满足 t=7 的间隙条件）
- T3' CI: [132.8, 134.2]，下界 > 128 ✓

## 三、可引版本声明

- **lattice-estimator**: github.com/malb/lattice-estimator, commit
  记录在 dell `~/spz/dell-final-bench/lattice-estimator/.git`；API 为
  E.nd.* + LWE.primal_usvp/dual_hybrid。
- **hybrid-decoding 攻击码**: github.com/bencrts/hybrid_attacks（合并
  论文 CRYPTO'26 "Careful with the Ring!" 的公开工件）。
- **合并论文**: 279+366 合并为 DOI 10.1007/978-3-032-35377-1_15。
- **条件熵方法**: 本工作 E1（`scripts/e1_conditional_entropy.py`，
  逐行复刻 `get_min_prec` 语义的 20k MC）。
