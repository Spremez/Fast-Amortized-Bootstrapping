# D4 实现计划：隔离加密算子（含批判性接收评审）

日期: 2026-08-20
前置: D0-D3 全准入（`ADMIT_CANDIDATE_D_TO_ISOLATED_ENCRYPTED_OPERATOR_IMPLEMENTATION`，
production_hot_path_permission=yes，controller `efc47d9`，账本 `2c6236c`）
范围: 仅隔离实现；不改 `sab_rlwe_bootstrap` 默认行为；不替换 `sab_pvw_*`

## 0. 批判性接收评审（自评，作为责任作者）

**结论：当前工作不足以被 CCF-A 接收；接收概率的瓶颈是"实测"而非"理论"。**

拒稿风险（按严重性）：
1. 🔴 零加密实现——D 的 1.46× over B1 是投影；
2. 🔴 无同机 B2（BatchBoot）对比——纯速度"与并发工作相当"不构成接收理由；
3. 🟠 无端到端应用（顶会 table stakes）；
4. 🟡 重随机化代价需实测背书；
5. 🟡 安全 hybrid 需论文级展开。

**接收主张定为 Pareto 而非纯速度**：每消息时间达到 BatchBoot 级（目标 ≥2.2×
over scalar）+ 密钥 17.9MB vs 其 59.6–205MB（3.3–11.5× 小）+ r-LUT 单遍语义 +
全套机器验证证明（D2 闭合定理、D3 强制重随机化定理 2⁻¹⁸⁴）。

**硬接收判据（自主负责，不达即按 roadmap 止损线降级 TCHES）**：
- [ ] A. 端到端实测 D/B1 ≥ 1.25×（给 1.46× 投影留 ~15% 实现损耗），即 over scalar ≥ 2.2×，30+ 配对样本、95% CI 下界 >1
- [ ] B. 同机 B2 复现（EMPmul 迁移语义见 docs/f1_mat_empmul_theory.md）对比表
- [ ] C. ≥1 个端到端应用（首选：r-LUT 单遍的 8-bit 指令集或 PSI 数字分解）
- [ ] D. 论文级证明（闭合、噪声 β 定理、安全 hybrid）
- [ ] E. 工件可复现（stage 报告 + 断点续跑脚本）

## 1. 数据结构（include/sab_operator.h 已建）

- `SAB_Operator_Key`: 输入/输出密钥 + **标量** TRGSW 选择子（复用
  `sab_pvw` 的位加密阵列，安全图注册为 existing scalar TRGSW sample）+
  τ₋₁ 自同构 KS（`trlwe_new_automorphism_KS_keyset`，gen = N−1）+
  重随机化 KS key（`pvmtmlwe`/TRLWE KS，σ_flood = 2⁻⁸）。
- `SAB_Operator_State`: in_N 个 slot × g=2 通道的 `PVW_TMLWE`，
  通道 = 普通输出密钥下 TRLWE（安全图: ordinary TRLWE under one output secret）。

## 2. 算子更新律（= D2 已验证的代数，逐条对应 C 函数）

| D2 定律 | C 实现 | 原语 |
|---|---|---|
| setup: U_j=(X^{b_j}, 0) 公开平凡编码 | `sab_operator_setup` | 公开单项式直接写入通道（无加密开销） |
| CMUX 通道仿射 | `sab_operator_cmux` | `trgsw_mul_trlwe_DFT`（标量选择子） |
| NCMUX = −τ∘(通道交换) | `sab_operator_ncmux` | `pvmtmlwe_eval_automorphism`(gen=N−1) + `trlwe_negate` + 通道交换 + CMUX |
| 单项式蝴蝶 | `sab_operator_rgsw_monomial` | 逐 bit 上述 CMUX/NCMUX |
| sub_a 公开单项式乘 | `sab_operator_sub_a` | 系数置换（零噪声、零密钥） |
| 绑定 L_F(U)=F·U_id+τ(F)·U_τ | `sab_operator_bind` | 公开 Torus 多项式乘 + 求和 |
| 强制重随机化 | `sab_operator_rerandomize` | KS + σ_flood 噪声注入（D3 定理要求） |

## 3. 测试与基准（main.c 新增编译期模式，不影响现有模式）

1. `SAB_OPERATOR_EQUIV_TEST`（r=1/2/4）：期望明文等价——解密通道验证
   绑定输出 ≡ 标量 SAB 输出（相位级，含真实噪声下的余量检查）；
   负控制复刻 D2 的 6 个（C 级复验）。
2. `SAB_OPERATOR_MICROBENCH`：kernel 稳定计时（D4 gate: 无热路径分配）。
3. D5 集成: 完整 include-zero 二进制 SAB A/B（vs scalar 与 B1）在服务器跑
   （104 核/251GB；单线程计时，构建 -j32）。

## 4. 执行顺序

1. 纯 C 参考实现（本机 WSL 构建冒烟 + 等价测试）
2. AVX512 路径仅在参考实现等价后（设计 §11 边界）
3. 服务器 D5 全参数 A/B → 判据 A 评估
4. 并行: B2 复现（服务器空闲核）与应用原型
5. 论文骨架随 D4 数据并行推进

## 5. 风险

- τ₋₁ 自同构 KS 的噪声进入递推——D3 的 λ_max 已按独立通道计，
  实测若超界 → 触发 D3 允许的一次参数调整（设计 §9）；
- PVW_TMLWE 通道与 PVW 输出尾部 KS 的兼容性需在等价测试中先验证；
- 若实现损耗 >15% → 判据 A 失败 → 降级评估（TCHES 主轴：证明 + 矩阵 + Pareto）。
