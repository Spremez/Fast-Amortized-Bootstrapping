# 会话状态快照（2026-08-31，防上下文压缩的关键结论固化）

> 本文件是当前会话的"核心记忆"——所有后续工作依赖这些结论。
> 每次上下文压缩后，从本文件恢复关键状态。

## 一、项目定位

**目标**：Eurocrypt 论文（唯一作者），组合 2025/1711（SQ 尺度量化）× 2025/686（本仓库摊销自举）× CRYPTO'26（原 279，稀疏密钥攻击），全部基准以服务器实测为准。

**服务器**：spz (luck@192.168.111.172)，双路 Xeon Gold 6230R，251GB RAM，fab-main 目录。

**分支**：codex/candidate-sq-scale-sab（隔离分支）。

## 二、关键事实（不可遗忘）

### 686 论文 = 只有标量(scalar)自举
- r-lane 矩阵形式是**我们的贡献**（基于 MOSFHET 矩阵外积）
- 正确对比：(1) SQ标量 vs 686标量 (2) 我们的r-lane vs 686标量×r次 (3) 优化r-lane vs 686×r次

### 两个独立安全维度
- **维度A（输入密钥）**：参数(n, h, σ_in)，CRYPTO'26 攻击对象，修正=增加h
- **维度B（自举密钥）**：参数(N, h_out, σ_out)，修正=增加σ_out
- σ_out 修正不修复维度A！两者不可互替！

### h 的安全余量（n=2048）
| h | T3 | 余量 | 判定 |
|---|---|---|---|
| 39 | 128.13 | +0.13 | 不安全（边缘） |
| **41** | **131.75** | **+3.75** | **推荐最优** |
| 42 | 133.53 | +5.53 | 保守 |

### σ 修正量的紧凑性
- 实际差距仅 0.77-6.15 bit（逐参数集不同）
- σ+11 = 旋转轨道天花板 log₂(2048)（紧凑修正）
- σ+15 = 过度保守
- 之前说的 "stock 在σ+15 FAIL" 实际是噪声超阈值，不是解密失败（gate 仍 Pass）

### SQ 的核心价值
- 不是"唯一能硬化的"（stock 也能通过 gate）
- 而是"噪声余量始终多 1-3 bit"（可靠性保障）
- 速度优势 ~10%（在标量路径上）

### r-lane 的性能
- 裸 r-lane（无旗标）vs stock r-lane：SQ 平价（1.008）
- stage355 全优化（9 旗标）：1.52-1.83×（vs 重复标量）
- SQ 与 stage355 旗标不兼容（构建失败，因为都优化同一分解/FFT生命周期）

## 三、论文贡献框架（8 项 × 5 层）

1. MOSFHET 库（实现基础）
2. 686 标量 → 矩阵化实现（1.52-1.83×）
3. 355 阶段工程优化战役
4. SQ 尺度量化外积（Theorem 1 精确性 + Lemma 1 ∆抑制）
5. 理论框架（三定理 + 引理 + 否定性结果）
6. CRYPTO'26 安全修正（首个修正摊销自举参数）
7. 公平多维度基准
8. 否定性结果（对社区有价值）

## 四、关键文件位置

| 文件 | 内容 |
|---|---|
| docs/paper_ccf_a/contribution_framework.md | 贡献框架 |
| docs/paper_ccf_a/comparison_framework_v4.md | 对比框架（最新修正） |
| docs/paper_ccf_a/optimal_h_verification.md | h=41 推荐依据 |
| docs/paper_ccf_a/hsigma_relationship.md | h-σ 关系+安全矩阵结果 |
| docs/paper_ccf_a/sigma_correction_analysis.md | σ 紧凑性分析 |
| docs/paper_ccf_a/theory_experiment_closure.md | 理论-实验闭环 |
| docs/paper_ccf_a/gap_analysis.md | 缺口分析 |
| docs/paper_ccf_a/benchmark_plan.md | 基准计划 |
| docs/paper_ccf_a/algo_and_experiments.md | 算法+实验（欧密体例） |
| docs/paper_ccf_a/paper_draft_v1.md | 论文骨架 |
| docs/paper_ccf_a/comparison_strategy.md | 对比策略 |
| theory_checks/sparse_key_lambda_bounds/ | 理论线（λ界+686复估） |
| repro/stage356_sq_scale_sab/ | 全部实验工件 |

## 五、代码位置

| 文件 | 内容 |
|---|---|
| src/sab_sq.c | SQ 标量自举（完整实现） |
| src/sab_pvw_sq.c | SQ r-lane 自举（矩阵形式） |
| src/probe_sq.c | 标量探针（SQ vs stock 背靠背） |
| src/probe_pvw_sq.c | r-lane 探针（SQ vs stock r-lane） |
| src/mosfhet/src/mattrgsw.c | 矩阵外积核（含 AVX-512 dense 导出） |
| scripts/sq_security_preflight_279.py | 安全预检脚本 |

## 六、实验结果汇总（关键数字）

### 标量（h=42, σ+0, 服务器 9 轮中位）
- SQ: 5.74 ms/msg, stock(686): 6.40 ms/msg, 比值 0.898（SQ 快 10.2%）

### 标量安全矩阵（h=42, 各 3 轮中位）
| σ | SQ(s) | stock(s) | ratio | SQ噪声 | stock噪声 |
|---|---|---|---|---|---|
| +0 | 15.2 | 16.4 | 0.929 | 57.60 | 57.69 |
| +11 | 13.1 | 14.4 | 0.910 | 57.46 | 58.66 |
| +15 | 12.8 | 14.9 | 0.859 | 59.53 | 62.14 |

全部 gate Pass（stock 在 σ+15 噪声超阈值但消息仍正确解密）

### r-lane（h=42, σ+0, AVX-512, 5 轮中位）
| r | SQ/stock | 结论 |
|---|---|---|
| 1 | 0.985 | SQ 快 1.5% |
| 2 | 1.010 | 平价 |
| 4 | 1.001 | 平价 |

### stage355 优化 r-lane（不修正安全）
- r=4: 1.52-1.83×（vs 重复标量×4次，11/11 行×10 采样）

### 密钥大小
- SQ 全管线 RSS: 620 MB
- 优化 r-lane RSS: 310 MB

### 失效概率
- 0/50 次失败（理论 ~2^{-100}+）

## 七、待完成工作

1. **最终实验**：h={39,41,42} × σ+11 × {scalar, r-lane, opt-rlane, SQ r-lane}
2. **路径A测试码**：扩展 probe_pvw_sq.c 支持 stock r-lane 计时
3. **欧密横向对比**：检索相关工作（实测+理论对比）
4. **686论文主张的实测验证**
5. **论文正文撰写**

## 八、用户要求（最新）

1. h=39+σ+11 不能凭猜测判定最优——需要实测+理论分析
2. 686 只给了标量算法，r-lane 是我们的贡献
3. 比较要满足最新 128-bit 安全性
4. 需要横向对比：检索相关工作，无实现的做理论对比
5. 体现工作量和考虑情况的完备性
6. 充分理解欧密会相关工作的要求后扩展
7. 上下文容量接近 1M，需要主动管理防止任务偏移
