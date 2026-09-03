# Research Roadmap: 以 2025/686 之后的工作为 Baseline 通向安全顶会论文

日期: 2026-08-19
状态: 提案（待按 Stage347+/Candidate D 治理流程审定）
范围: 主工作树规划文档；不改变任何 production hot-path 权限设定

## 执行进度（2026-08-19 当日更新）

| 项 | 状态 | 证据 |
|---|---|---|
| D1 审计重跑 | **PASS_D1_DISTINCT_SAB_OPERATOR_CLAIM_REMAINS_TESTABLE**（worktree 提交 `0d444d6`） | 2026/068 rev.2 已哈希绑定登记（旧文件为 1 月初版，系阻塞根因） |
| D2 算子闭合 | **PASS_D2_OPERATOR_CLOSURE_G_LE_4，权威重放通过**（`d2_replay_authenticated=yes`，账本提交 `b3cf1e9`） | 4 个新研究模块 + 运行器；γ=2，修订 1 次（Γ₀ 失败证据：N=8/binary_all_one/basis0/slot4）；256 phase 行 + 168 trace 行全 PASS；6 负控制全 DETECTED |
| Candidate D 总状态 | `BLOCK_CANDIDATE_D_INCOMPLETE_EVIDENCE`，**仅等待 D3** | resume_condition 已指向 Tasks 7-8（D3） |
| F1 理论 + G1 | `docs/f1_mat_empmul_theory.md`；**引理 F1-1 机器验证**（160 检查 0 失败） | `scripts/check_f1_empmul_equivalence.py`；Amdahl 投影 2.36–2.6× over scalar（stage322 真实画像） |
| E1 扩测 | **stage354 完成（4 行有效 + 1 行资源受限）**，报告见 `repro/stage354_e1_binary_matrix_expansion/stage354_report.md` | **SET_4_5_4096 r=2 = 1.6115×、r=4 = 1.6507×、SET_6_7_4096 r=4 = 1.6461×（Boot6 对标）、SET_8_9_4096 r=2 = 1.5693×（Boot8 对标，新矩阵最低值）**；均 10 样本全 Pass、噪声门 Pass、0 pair 失败；十行矩阵范围 **1.5693×–1.7476×**；SET_8_9_4096 r=4 资源受限（RSS>11.7GB 双档 OOM，需 ≥16GB 机型，dmesg 在案） |
| E1 服务器矩阵 | **stage355 运行中**（`ssh autovoice-delld`，104 核/251GB/Xeon Gold 6230R，AVX-512，与 BatchBoot 的 6258R 同代） | **规范目录 `/home/spz/Fast-Amortized-Bootstrapping-stage355-e1-server/`**（操作者 sudo 建目录 chown 后已迁移，断点续跑生效：行内 3/10 样本保留、从 run 3 续跑；旧 `~/spz` 位置已清理）；11 行全矩阵按价值序 nohup 运行（首行 = 资源受限的 SET_8_9_4096 r=4，单次 ~42min，RSS ~12.4GB）；冒烟 SET_2_3_2048 r=4 单样本 1.826× Pass；runner/迁移/续跑脚本见 `repro/stage355_server_e1_matrix/` |
| D3 下一步 | 见 §4-F4 与下文 | — |

### D3（Tasks 7-8）实施方案要点

按 `run_candidate_d_admission.py` 的 `D3_REPLAY_CONTRACT` 与 `D3_OUTPUTS`：

1. **模块**: `research/mat_sab/candidate_d_admission.py`（沿用 D2 的
   source-map/closure 模块），运行器 `scripts/run_candidate_d_d3_admission.py`。
2. **规范输出**（9 个文件）: `theory_checks/candidate_d_security_noise.md`、
   `theory_checks/candidate_d_complete_cost.md`、
   `repro/candidate_d_admission/{binding_domain,security_object_map,noise_bound,structural_cost,amdahl_projection,resource_projection,d3_summary}.*`
3. **必备输入**（已存在）: D2 输出 + `repro/stage331_current_head_highstat_refresh/summary.csv` +
   `repro/stage322_schedule_profile_attribution/{profile_summary,component_budget}.csv` + 5 个源文件。
4. **语义要点**（契约 §D3 Semantic Ownership）: 8 个注册标准安全对象；
   协方差感知噪声递推与确定性误差界；系数一证明锚点或含零计数 +79,872
   选择子事件；B1 profile 绑定；含 late-binding 代理成本的完整 Amdahl
   重算（≥10% over B1 @ r=4 才 PASS）；全部资源项含 keygen。
5. **噪声引理 F1-2 与 D3 的关系**: D3 的噪声界针对 D 的双通道算子
   （λ_max(Σ_U)·Σ‖γ(F_Z)‖² 形）；F1 的多比特噪声是独立义务，二者不可互替。

---

## 0. 目标

最终目标（用户定义）:

> 形成一个相对 baseline 有可测量性能提升的算法和实验体系，形成一篇安全顶会文章（CCS / USENIX Security 级别）。

约束（沿用仓库既有治理）:

- 只允许标准密码学对象（RLWE/TRGSW/GGSW 系），不引入非标准假设（见 Candidate D stop rules）。
- 主指标 `T_complete_bootstrap/(r·N_active)`，与 Stage345 的 B1 基线可比。
- `PAPER_READY` 定义见 `docs/superpowers/specs/2026-07-16-ccs-usenix-mat-sab-research-contract-design.md`。

## 1. 结论摘要（TL;DR）

1. **竞争格局已经变化**。BatchBoot（USENIX Security'26，蚂蚁集团）**以本仓库（AmortBoot = ePrint 2025/686 的开源实现）为直接 baseline**，单线程下宣称 2.2×（2-bit）、2.4×（4-bit）、2.27×（8-bit）加速，仅 6-bit 为 1.05×。当前 MAT-SAB 的 1.6121×–1.7476×（vs 自身标量路线）**不足以单独支撑顶会性能声明**。
2. **两条路线的成本结构正交，可乘法融合**。BatchBoot 优化的是 selector schedule 侧的 FFT 计数（多比特 CMux + FFT 域 automorphism 融合）；MAT-SAB 优化的是 accumulator 侧的 r-lane 摊销。融合投影 ≈ 2.2× × 1.75× ≈ **3.8× over scalar**（2-bit 行），且 MAT 的密钥比 ≤1.07× vs BatchBoot 的 3.2–3.5×。这是本 roadmap 的主推方向 F1。
3. **Candidate D 的新颖性空间被 BatchBoot 压缩**。BatchBoot 的 BatchCBoot（Half.BatchCBS）已经是"LUT 无关的批量盲旋转 + 事后经 external product tree 绑定 LUT"结构。D1 审计的强制源列表必须加入 BatchBoot（当前它只是草稿引用 TODO）；D 的声明必须收窄为"多 lane 矩阵设定下的选择子工作消除"。
4. **D1 的外部输入阻塞已在本轮解除**：ePrint 2026/068 rev.2（2026-07-16）全文已下载并 SHA256 绑定至 `literature/external_2026_068/`，BatchBoot prepub PDF 同样入库 `literature/external_batchboot_usenix26/`。

## 2. 外部 Baseline 矩阵（2025/686 之后）

按对本项目威胁/可借鉴程度排序。全部数字为论文自报，硬件口径各不相同，直接对比见 §3。

### 2.1 BatchBoot — USENIX Security 2026（头号竞品）

- 论文: *BatchBoot: Fast Batched Bootstrapping for TFHE scheme and Practical Applications*，Zhihao Li 等（Ant Group / 山西大学 / 中科院信息工程所），Cycle 1 录用，2026-08-12 报告。
- 全文: `literature/external_batchboot_usenix26/batchboot_usenix26_prepub.pdf`（SHA256 `a1d1d694...01ca403`，20 页已提取文本）。
- 三个技术点:
  1. **EMPmul**：δ=2 多比特 CMux（每步消化 v 的 2 个 bit，4 把 RGSW 钥匙/步），把 FFT 从 `2(2d+2)·nℓ` 降到 `(d+1)·nℓ`；
  2. **FFT 域 automorphism 融合**（parametrized external product + hoisting 思想），消除 automorphism 的额外 FFT；
  3. **稀疏打包**：RLWE→MLWE extraction，复杂度 `O((h+k)·n'·log n')`，n'<n。
- **与我们的参数一一对应**（Table 10 vs `docs/cost_model.md`）: Boot2 ↔ SET_2_3_2048（同 h=39）、Boot4 ↔ SET_4_5_2048（同 h=42）、Boot6 ↔ SET_6_7_4096（同 h=33）、Boot8 ↔ SET_8_9_4096（同 h=34）。head-to-head 不需要参数换算。
- 性能（单线程，Xeon Gold 6258R，MOSFHE 库即本仓库同源库）:

| 参数集 | 消息数 | AmortBoot(本仓库) 总时/摊销 | BatchBoot 总时/摊销 | 相对加速 | BatchBoot 密钥 |
|---|---:|---:|---:|---:|---:|
| Boot2 (2-bit) | 2048 | 16.57s / 8.09ms | 7.32s / 3.57ms | 2.2× | 59.6 MB |
| Boot4 (4-bit) | 2048 | 17.72s / 8.65ms | 7.39s / 3.60ms | 2.4× | 64.1 MB |
| Boot6 (6-bit) | 4096 | 36.53s / 8.92ms | 34.57s / 8.43ms | 1.05× | 120.1 MB |
| Boot8 (8-bit) | 4096 | 234.88s / 57.34ms | 102.86s / 25.11ms | 2.27× | 205.3 MB |

- 代价: **密钥比 AmortBoot 大 3.2–3.5×**（多比特 CMux 每步 4 把钥匙）；8-bit 峰值内存 3.7GB；多线程 8 线程 102.8s→19s。
- 应用（顶会 table stakes 的标尺）: TFHE-based unbalanced PSI（通信 294×↓、4.1×↑ vs PEPSI）+ 8-bit FHE 指令集（3.3–6.5×↑）。
- **工件状态: 未公开自有代码**（论文脚注只链接 baseline 仓库）。head-to-head 需自行复现 EMPmul 或联系作者。

### 2.2 Sharing the Mask — TCHES 2025(4)，Zama

- Bergerat 等，`eprint.iacr.org/2025/2112`。Common-mask（CM）密文：一个共享 mask + 多个 message body；boolean 下打包 8 消息改进 ≤51%；支持"单条 CM 密文内对不同消息施加不同 LUT"与跨消息私有线性操作。
- 对本项目的意义: (a) 候选 B 拒绝时已识别其 `(k+r)²` 型成本为先验风险；(b) 其"每消息不同 LUT"能力与 MAT-SAB 的 r-lane 多 LUT 语义部分重叠，论文 related work 必须精确划界。

### 2.3 Paiva 等 — TCHES 2025（`2025/696`）

- *Faster amortized bootstrapping using the incomplete NTT for free*。改进的是 Guimarães ASIACRYPT'23 **两段式 NTT 线**（不是 2025/686 的 MPMul/SAB 线）：2.12× over ASIACRYPT'23，1.12× over TFHE-rs；DFR≈2⁻³²（7-bit）。
- 对本项目: incomplete-NTT 思想可移植到 MAT 外积 kernel 的 key 侧变换（F1 的备选子件），但属 TCHES 级别的组件优化。

### 2.4 Lin & Wu — ePrint 2026/068（NTRU 转移，Candidate D 的 D1 阻塞源）

- *Practical Amortized Bootstrapping for NTRU-Based FHE*，NTU，rev.2 2026-07-16。全文已入库 `literature/external_2026_068/`（SHA256 `8083db16...4cbda84`，22 页已提取）。
- 核心: 把 FINAL 重写为多项式环形式，将 GP25（=2025/686）的 MPMul 摊销 bootstrapping 迁移到 NTRU 稀疏三值密钥；per-coefficient 成本 `O(nℓ_Q)→O(hℓ_pos)`。
- 关键数字（c8a.xlarge 单线程）: 2.68ms/msg-coefficient @n=8192（2.65× vs TFHE-rs）；**GP25 被其测得 2.53/2.36/2.29 ms/msg @n=2048/4096/8192**；BSK 11.28MB 不随 n 增长；~8 bytes/bit。
- **D1 审计六个问题的答案（从全文直接核验）**:
  1. 算法结构: 标量 accumulator 链表（n 个 EncS），MPMul = ℓ_pos 步条件 2^i 旋转 + 自同构 KS；差分向量编码稀疏位置。
  2. 与 GP25 差异: NTRU `g/f` 单环元素 accumulator、coefficient-wise 内积改写、NTRU fatigue + estimator 安全验证。
  3. **无任何多 lane / matrix-TRGSW 打包**（每 coefficient 独立 accumulator，无共享 selector）。
  4. 性能表: 见上（Table 7/8/9，pfail 2⁻⁶⁴ 目标，实测 2⁻⁶⁹·⁸–2⁻¹¹⁰·⁵）。
  5. **LUT 绑定时机: 盲旋转前**（Algorithm 2 第 2 行 test vector 预装），无 late binding。
  6. 自述开放问题: "GP25 的 two-key accumulator 技术能否迁移到 polynomial-NTRU"（明确留白）、KSK 压缩、多线程/GPU。
- 结论: 2026/068 对 MAT-SAB 核心（多 lane 矩阵 accumulator）**不构成先验覆盖**，但其"两密钥/多输出 accumulator 留白"正是 F3（NTRU 融合）的入口。

### 2.5 其他相关（次要）

- 2025/1711（CAS）: squared-gadget GSW 重构，blind rotation 内核 ~2×（26.2ms vs OpenFHE ring GSW 84ms；4.8ms vs TFHE 11.4ms）。preprint，未评审。
- 2024/1667（FC'25）: overlapped bootstrapping（相邻 bit 测试区间重叠），多 bit 门方向。
- Sub-millisecond gate bootstrapping（Lu 等，AsiaCCS'26）: 标量侧 SOTA 参考，用于论文背景定价。
- Liu–Wang CRYPTO'23（Batch Bootstrapping I/II）: 理论 Õ(1) 摊销线，BatchBoot 的理论上游。

## 3. 竞争定位分析（诚实口径）

三个口径分开说，不允许混用:

1. **相对口径（公平）**: 同一 scalar baseline（本仓库）下，BatchBoot 2.2–2.4×（2/4-bit）vs MAT-SAB 1.61–1.75×。**当前 MAT-SAB 落后于 BatchBoot 的相对提升**。
2. **绝对口径（目前不可比）**: BatchBoot 3.57ms/msg（Boot2，6258R）vs MAT-SAB 2.99ms/(msg·lane)（SET_2_3_2048 r=4，本机）。硬件、pfail 目标（其 2⁻¹²⁰）与 LUT 语义（其每消息单 LUT vs 我们 r lane 共享输入）均不同。**必须做同机 head-to-head 才能写进论文**。
3. **密钥口径（我们的结构性优势）**: BatchBoot 3.2–3.5× scalar（59.6–205MB）vs MAT-SAB ≤1.07×（Stage243 草稿 keygen 比 ≤1.358、key 比 ≤1.069）。2026/068 亦强调 key 不随 n 增长。**"每消息时间与密钥规模的联合 Pareto 前沿"是可守住的论文主轴之一**。

顶会门槛分解（以 BatchBoot 为标尺）: 机制新颖性 + 证明 ✓/✗、性能优势、应用（PSI/指令集）、安全分析（sparse-key estimator + 标准假设）。当前仓库只有"工程加速 + 证据包"，缺后三项的顶会级形态。

## 4. 融合候选方向与 gate

### F1（主推）: MAT-EMPmul — 多 lane 矩阵外积 × 多比特 CMux/FFT 域融合

- 机制: 在 `sab_pvw_blind_rotate_*` 的稀疏调度中，把单 bit selector 步替换为 δ=2 多比特矩阵 CMux 步（选择子矩阵 4 路选择），并将 wrapped-entry 的 automorphism 融合进 FFT 域外积（BatchBoot Eq.8 的矩阵版）。r lane 共享同一选择子调度（`docs/cost_model.md:83-93`），故 selector 侧优化与 accumulator 侧摊销天然复合。
- 投影: 2.2×（EMPmul，2-bit）× 1.747×（现有 r=4）≈ **3.8× over scalar**；密钥增长可控目标 ≤1.5×（多比特矩阵钥匙 4 路/lane，但共享调度与 body 结构，低于 BatchBoot 的 3.5×；需核算）。
- Gate（映射到 Stage347 机制门）:
  - G1 有限检查器: 多比特矩阵选择子的代数闭合（N=8/16 上 basis-vector 等价 + 负控制），照 D2 模板。
  - G2 噪声引理: BatchBoot Lemma 4.1 的 MAT 形式（`V_EMP^MAT < Var + 2ℓ·V_EP^MAT`），乘 r-lane 噪声界。
  - G3 Amdahl: 完整 SAB 投影 ≥ B1 + 30%（比 Candidate D 的 10% 门槛更严，因为要追 BatchBoot）。
  - G4 密钥/资源: key 比 ≤1.5× scalar，RSS 不高于当前 2.4GB 的 1.3×。
- 风险: 6-bit 行 BatchBoot 只有 1.05×（FFT 削减饱和），F1 在 6/8-bit 的收益要单独投影；多比特 CMux 噪声增长可能吃掉 include-zero 行的 0/N 噪声余量。

### F2: 稀疏打包 × include-zero/非二进制扩展

- RLWE→MLWE extraction（BatchBoot §4.2）迁移到 MAT-SAB 的 include-zero/ternary 通路；同时解锁 `main.c:619` 的 binary-only 限制与未测参数行（SET_4_5_4096、全部 8192、SET_6_7、SET_8_9、ternary）。
- 定位: 证据扩展（E1），不是机制新颖性；让参数矩阵覆盖 BatchBoot 的 Boot2–Boot8 全部对应行。

### F3: NTRU 转移（2026/068 留白）

- 2026/068 明确把"two-key/multi-output accumulator 迁移到 polynomial-NTRU"留为 open problem。MAT-SAB 的 r-lane accumulator 正是 multi-output 结构。
- 定位: 高差异化、高成本。作为论文第二贡献（"我们的多 lane 结构在 NTRU 域同样成立"）或 future work，取决于 D1 后的排期余量。**不在第一阶段排期**。

### F4: Candidate D 重定位（D1 重跑）

- 新增强制审计源: **BatchBoot/BatchCBoot**（Half.BatchCBS = LUT 无关批量盲旋转 + 事后 EP-tree 绑定）+ EP-CBS [LSL+40] + 多值 bootstrapping 线。它们不覆盖"MAT 选择子 Θ(r²) 工作消除"，但覆盖"late binding"本身。
- D 的合法声明收窄为: *"late-bound lane operators that eliminate dense selector work in the multi-lane matrix setting"*。若 D2 闭合检查在该收窄声明下仍过不了，按 stop rules 拒绝并转 F1。
- D1 恢复程序: 按 `candidate_d_admission_report.md:63-65`——用 `literature/external_2026_068/eprint_2026_068_rev20260716.pdf`（SHA256 已绑定）更新 source registry，重跑 `run_candidate_d_d1_literature.py`，然后 Task 9 controller。

### F5: 工程债务（支撑性，不构成论文贡献）

- `src/mosfhet/src/mattrgsw.c`: k>1/l>1 走通用回退（`:871-884`），AVX512 特化仅 k=1,l=1——F1 kernel 化时一并处理。
- `copy_SAB_key()` `assert(false)`（`src/sparse_amortized_bootstrap.c:204-207`）与 k>1 的 `mul X^N` TODO（`:337`）。
- Makefile 无统一 `test` 目标/CI；worktree 目录名与实际内容不符；`.git/config` 的 `core.worktree` 指向失效 WSL 路径；README 构建默认值过期。
- Stage243 草稿合入 Stage345 六行新数（1.6121–1.7476×）并消解 BATCHBOOT26 引用（BibTeX 已备好，见附录 A）。

## 5. 实验矩阵与 gate

| 编号 | 实验 | 判定 |
|---|---|---|
| E0 | 同机 head-to-head 协议: 单台 AVX-512/VAES 机器，Boot2/4/6/8 ↔ SET 对应行，单线程为主 + 8 线程一行，pfail 对齐（统一 2⁻⁶⁴ 或 2⁻¹²⁰，二选一并全程一致），记录 key/RSS | 报告绝对 ms/msg + 密钥 Pareto 图 |
| E1 | 现有 6 行扩到 10 行 binary 矩阵（补 SET_4_5_4096 r2/r4、SET_2_3_8192 r2/r4 等），沿用 Stage340–345 流程与 10 样本 CI | 每行 0/N 噪声失败，CI 下界 >1 |
| E2 | F1（MAT-EMPmul）实现后 vs scalar vs BatchBoot 相对数 | 每行 ≥2.2× over scalar 且 ≥1.1× over BatchBoot 相对提升；6/8-bit 单独说明 |
| E3 | 噪声/正确性: 高样本噪声分布 + pfail 预测 vs 实测（对标 2026/068 Table 9 的做法） | 预测/实测比 <1.3，0 失败 |
| E4 | 应用: r-LUT-per-bootstrap（共享输入、r 个 LUT 一次通过）→ 复刻 BatchCBoot 的 8-bit 擎集之一（AND/ADD/MUL）与 PSI digit 分解（ℓ 子表 = ℓ lane） | 至少 1 个端到端应用对比表 |
| E5 | 安全: sparse-key lattice estimator 重跑（对齐 2026/068 §5.3 的 rejection-sampling 损失 δ 口径），标准假设清单 | ≥128-bit 全行 |

Go/no-go（论文层）: F1 的 G1–G4 任一失败 → 论文降级为 TCHES 系统论文（用 E1 全矩阵 + 密钥 Pareto 主轴）；F1 通过但 E2 追不上 BatchBoot → 转"密钥/内存受限场景"定位（CCS/USENIX 仍可投，主声明改为 Pareto 优势 + 多 LUT 语义）。

## 6. 论文结构（CCS/USENIX 模板）

- 题目方向: *Multi-Lane Matrix Bootstrapping: Amortized TFHE Bootstrapping with Small Keys*（占位）。
- Contributions: (1) MAT-EMPmul 机制 + 噪声引理与正确性证明；(2) 密钥规模 Pareto 优势的形式化+实测（vs BatchBoot 3.5×）；(3) r-LUT 语义与两个应用；(4) 开源工件。
- Sections: Intro / Prelim / Multi-lane matrix SAB（构造+证明）/ MAT-EMPmul fusion / params+security / eval（E0–E5）/ applications / related-work 划界（BatchBoot、StM、2025/696、2026/068、Liu–Wang、多值 FBS）/ conclusion。
- Claim matrix 红线（继承 Stage339 审计）: 不主张 all-parameter、不主张理论最优、不主张首个 late-binding（只主张 MAT 设定下选择子工作消除）、非二进制结果未测前不写。

## 7. 时间线（建议，2 论文周期内）

1. **周 1–2**: D1 重跑（源已入库）→ D 去留定案；同时 E1 补行启动（纯实验，不动 hot path）。
2. **周 2–4**: F1 的 G1/G2 纸面机制门（finite checker，无生产代码）。
3. **周 4–8**: F1 kernel 原型（isolated microbench，走 Stage350 通道）→ G3/G4。
4. **周 8–12**: 完整 SAB 集成 + E2/E3；E0 head-to-head（BatchBoot 无工件，预算复现 EMPmul 的工时或邮件作者）。
5. **周 12–16**: E4 应用 + 论文成稿 + E5 安全节 + 工件打包（`PAPER_READY` 门）。

## 8. 本轮已完成的一次性行动记录

- `literature/external_2026_068/`: ePrint 2026/068 rev.2 PDF（SHA256 `8083db16cd43613968e02846ad16d3f4e2c4d8dd0c64692300e31bc184cbda84`）+ 全文提取 `extracted_text.txt`。
- `literature/external_batchboot_usenix26/`: USENIX'26 prepub PDF（SHA256 `a1d1d694a239976f7cbc42dfa0ba6f2d7b770690a3c08b3e1689cb8f701ca403`）+ 提取文本 + 本文档附录 A 的 BibTeX。
- 以上直接解除 `EXTERNAL_BLOCKED` 的物理输入条件；正式 D1 解锁仍需按 worktree 内脚本流程登记哈希。

## 附录 A: BatchBoot BibTeX（解除 Stage243 草稿 `:57` 的 BATCHBOOT26 TODO）

见 `literature/external_batchboot_usenix26/batchboot_usenix26.bib`。作者序按 PDF 页 1；venue 按 USENIX 官网 metadata；prepub 状态已在 note 标注。

## 附录 B: 关键文件索引

- 仓库证据头: `6a5f113`；六行基线 `repro/stage345_binary_matrix_synthesis/stage345_report.md`；当前结果 `docs/current_pvw_mat_sab_result.md`。
- 既有计划: Stage346 报告 `repro/stage346_algorithm_redesign_audit/stage346_report.md`（P0=Stage347 机制门）；Candidate D 路线 `.worktrees/candidate-a-star-cycle-gate/docs/candidate_d_lut_late_binding_roadmap.md`。
- 成本模型与 lane 语义: `docs/cost_model.md:83-93`。
