# stage356: SQ 尺度量化 SAB（scale-quantized SAB）机制卡

- 候选名: SQ / SQS（stage356）
- 来源组合: eprint 2025/1711（平方 gadget / 尺度化外积）× eprint 2025/686（本仓库稀疏摊销自举）× eprint 2026/279（稀疏密钥环同构混合攻击安全差）
- 隔离边界: `include/sab_sq.h` + `src/sab_sq.c`，仅在 `SAB_SQ_EQUIV_TEST` 下编译；不改 scalar `sab_rlwe_bootstrap`、不替换 `sab_pvw_*` / `sab_operator_*`；构建走 `BUILD_DIR=./build_sq` + `main_sq` 链接目标，与并行 D4/主线构建互不干扰。

## 机制

scalar SAB 的盲旋转外积（`trgsw_mul_trlwe_DFT`，l=1, Bg=23）把累加器分解为 23-bit 数字后与密钥行相乘。SQ 变体把累加器本身量化到 Q=2^q 尺度（所有 TRLWE 系数为小有符号整数，u64 符号扩展存储），选择子 TRGSW 直接用 `trgsw_monomial_sample` 的 Bg_bit=q 采样（消息挂在原始尺度 2^{64-q}），外积变为：

```
out = round_{2^q}( rows_DFT ⊙ DFT(acc) )        // 纯点乘 + 逐系数 >> (64-q)
```

DFT 信封契约（`execute_reverse_torus64`/`execute_direct_torus64`：原值有符号 double，mod-2^64 截断）保证点乘 = 负循环整数卷积 mod 2^64；消息路径 (bit·2^{64-q})·c >> (64-q) = bit·c 严格无舍入误差。NCMUX 的自同构 KS 前后做精确升/降尺度（`<<（64-q)` / 四舍五入右移），KS 语义与噪声不变。

## 声明的收益（按实测修正）

1. 噪声侧: 密钥噪声项系数从 σ·2^{27.1}（stock）降到 σ·2^{q+3.5}（每外积，rms，N=2048），等效 σ 余量 +2(23−q) bit —— 用于吸收 2026/279 的稀疏密钥安全差（保守 15 bit），σ 上调在等速下完成。
2. 核侧: 去掉 2×N 系数分解环，换成 2×N 舍入右移；FFT/点乘计数不变（4 FFT + 4 pw / 外积）。速度预期持平 ±5%，以同二进制 scalar 对照实测为准。
3. 参数侧: q 与 Bg 解耦，成为独立设计旋钮（受噪声下限 q ≥ b_prec+10 与 σ-吸收需求共同约束）。

## 风险与回退

- 若等价 gate 失败: 逐层探针（单元外积 → 单调 monomial_mul → 完整盲旋转）定位，方法论同 D4 的 probe 体系。
- 若速度退化 >5%: 记录并降级为"安全硬化等价路径"，速度主张撤回。
- 279 完整代价模型（精确 isometry-hybrid）待全文接入后替换保守插值。
