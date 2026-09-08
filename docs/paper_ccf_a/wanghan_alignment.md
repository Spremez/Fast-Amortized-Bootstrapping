# 与 Wang Han 的工作对齐文档

Date: 2026-09-08
目的：双方对齐进度，确认融合论文的分工与就绪度。
你提供：`20260908V1.pdf`（9 页理论草稿）。我们提供：完整 C 实现 + 安全定案 + 六行实测 + 论文草稿 v1。

---

## 一、你的 PDF 与我们实现的逐项映射

### 1.1 密码系统层（你的 §1.3 ↔ 我们的 L3 核）

| 你的概念/记号 | 我们的实现 | 状态 |
|---|---|---|
| Vec-MLWE：**(b; a)** ∈ R^{k+r}，r 体共享 mask | `PVW_TMLWE`（`mosfhet.h:128`） | ✅ 已实现，逐 lane 正确性门全过 |
| Mat-MGSW：(k+r)×(k+r) 分块对角 | `MAT_TRGSW`（`mosfhet.h:179`） | ✅ 已实现 |
| 尺度化外积 ⊡ = ⌊C·c·Q/T⌉ | SQ 核（`sab_sq.c`，Q=2^16, T=2^64） | ✅ 已实现，消息路径精确（Thm 1） |
| 双模数 T > Q | SQ 的 q=16 / torus 2^64 | ✅ 同构 |
| gadget 分解消除 | SQ 同样消除 | ✅ 一致 |
| 密钥 sk = (I; S) | `PVW_TMLWE_Key` s[k][r] | ✅ 同构 |

### 1.2 噪声分析（你的 Lemma 1.7/Cor 1.8 ↔ 我们的 Thm 2/Thm 4-6）

| 你的结果 | 我们的对应 | 关系 |
|---|---|---|
| **Lemma 1.7**：γ' = √(Q²/T²·γ₁² + γ₂² + Q²/T²·γ₃² + γ₄²) | Thm 2：σ·2^{q+3.5}（实测标定） | **互补**：你给一般次高斯框架，我们给具体指数 + 三档 σ 对账 |
| **Cor 1.8**：monomial + 三元 + 均匀 + ∆Q²<T | Thm 5/6：p 域 + 精度边界 | **互补**：你的应用特化 + 我们的 Thm 6 常数闭合 |
| Q²/T² 抑制因子 | ∆ = Q²/T = 2^{2q-64} | **同一机制** |
| 条件 ∆·Q² < T | q ≥ p + 10（我们推导） | 你给一般条件，我们给具体判据 |

**论文融合方案**：你的 Lemma 1.7 作为 §3.5 主引理，我们的 Thm 2 作为实测验证。

### 1.3 蝶形调度（你的 Algorithm 1 ↔ 我们的 sab_pvw）

| 你的 Algorithm 1 (P-MPMUL) | 我们的实现 | 状态 |
|---|---|---|
| 逐位蝶形 for i = 1 to log B-1 | `sab_pvw_RGSW_monomial_mul_state`（`sab_pvw.c:861`） | ✅ 逐行同构 |
| 环绕槽 j < 2^i: NCMUX | `sab_pvw_NCMUX`（`sab_pvw.c:713`） | ✅ |
| 直达槽 j ≥ 2^i: CMUX | `sab_pvw_CMUX`（`sab_pvw.c:704`） | ✅ |
| (candidate − current) ⊠ Enc(bit) + current | `mat_trgsw_mul_pvmtmlwe_DFT` + 融合旗标 | ✅ + **我们新增 DualSubCMUX**（k=2 拓扑上限证明） |

**我们新增（你的 PDF 未涉及）**：
- DualSubCMUX：配对共享三操作数减法（代数保持，k=2 最优）
- SUB_DECOMP_FUSION：外积内嵌减法
- COEFF_ONE_FAST：include-zero 快路径
- 7 融合旗标整体：include-zero 路径 1.5× 加速

### 1.4 完整自举（你的 Algorithm 2 ↔ 我们的 O1）

| 你的 Algorithm 2 | 我们的实现 | 状态 |
|---|---|---|
| 初始 setup：tⱼ·X^{bⱼ} | `sab_pvw_setup_tv_xb`（`sab_pvw.c:1214`） | ✅ |
| h+1 次 P-MPMUL | `sab_pvw_sparse_mul_*` 系列 | ✅ |
| **Hom-Tr**（第 9 行） | **见 §二（下方专门分析）** | ⚠️ 语义待你确认 |
| 提取 + 输出 | `sab_pvw_extract_tlwe_lane` + packing KS | ✅ |

**我们新增（你的 PDF 未涉及）**：
- **三种秘密类完整支持**：binary（明文乘，零噪声）、ternary（s_sign CMUX）、
  一般稀疏 ρ-SAB 含负系数（sub_a_ga 双自同构 + 外积 [BDF18]）
- 逐步 oracle 等价验证（r=1..8 全域 0 失配）
- G-ρ 多体版 FINAL 门 0/4096

### 1.5 你有而我们没有的

| 项 | 内容 | 论文价值 |
|---|---|---|
| **Lemma 1.7 完整噪声推导** | 四项次高斯分解 + 显式 γ₁..γ₄ | **高**——作为主噪声引理 |
| **Cor 1.8 应用特化** | monomial + 三元 + 均匀闭式 | **中**——直接引用 |
| **Hom-Tr 理论构造** | §2 Alg 2 第 9 行的代数设计 | **需确认语义后实现** |
| **RNS ModUp/ModDown** | §1.4 框架性提及 | 低（实现层） |
| **Slot 置换** | CM 外积中的私有线性操作 | **正交贡献**，论文引用 |

### 1.6 我们有而你的 PDF 没有的

| 项 | 内容 |
|---|---|
| **完整 C 实现** | MOSFHET + spqlios AVX-512 + 7 融合旗标 |
| **修正安全定案** | CRYPTO'26 五臂组合 min 130.4 ≥ 128 + BSK 选项 A 落地 |
| **BatchBoot 重评** | 四集全 FAIL（120.5-124.6）的翻盘数据 |
| **六行主矩阵** | 修正安全 1.66-1.84×，跨精度 2-8 bit / 环维 2048-8192 |
| **r 选值 benchmark** | 边际 lane 成本 + 甜点 r=2-4 + M3 精确验证 |
| **M3/M3' 摊销定律** | 行粒度解析上限 1.6× + 总账推论 + 六行对账 ≤ 1.004 |
| **M1/M2 投稿级证明** | 完整分块对角归纳 + 无串扰 + 方差分解 |
| **Thm 3 常数闭合** | q ≥ p+4+6 = p+10，p7 实测精确验证 |
| **DFR certified** | 解析 2^{-2724} + Clopper-Pearson 2^{-18.4} |
| **G-ρ（一般稀疏）** | ρ-SAB 矩阵化 + 负系数 + FINAL 门 0/4096 |
| **DualSubCMUX** | k=2 拓扑上限证明 |
| **SQ p 域边界** | p ≤ 5@q16 定理-实测闭环 |
| **否定性结果** | F1(δ=2)、C5(联合 packing)、σ 单旋钮 三组闭环 |
| **TFHE-rs 同机锚点** | 9.560 ms/PBS，满占用 1.91× |
| **Bergerat 全文审** | TCHES'25 CM 形式同构但域不同 |

---

## 二、Hom-Tr 专门分析（需要你确认的核心问题）

### 2.1 我们尝试了什么

朴素实现（commit 6f72c5e）：`pvmtmlwe_eval_automorphism(p[i], w, aut_family[w])`
——对累加器槽施加一次环自同构 X→X^w。

### 2.2 为什么失败

独立 agent 分析（已入册 stage391）证明了：
```text
自同构：σ_w(X^i) = X^{wi mod 2N}    （置换指数）
单项式乘：M_v(X^i) = X^{(i-v) mod 2N}（移位指数）
反例：f=1 → σ_w(1)=1 但 X^{-v}·1 ≠ 1（除非 v≡0 mod 2N）
```

实测：FAIL 452/512，noise 2^63（全 torus 范围）。

### 2.3 独立 agent 推导的正确 Hom-Tr 参考变体

```text
环分解：N = r·d，Y = X^r，A = Z[Y]/(Y^d+1)
打包：  m = Σⱼ X^j · mⱼ(Y)
目标：  L_a(m) = Σⱼ X^j · Y^{-aⱼ} · mⱼ(Y)
固定子群：H = {σ_{1+2dℓ} : 0 ≤ ℓ < r}  （不随 a 变化）
迹提取：T_H(X^{-j}·m) = r·mⱼ(Y)
整数版：U_a(m) = Σ_{w∈H} P_w·σ_w(m) = r·L_a(m)
Torus 上 r^{-1}：预置 Q_in = r·Q_out，每步消耗 log₂(r) 模数比特
```

### 2.4 需要你确认的 8 个问题（独立 agent 提出）

1. αⱼ, α∨ⱼ, βⱼ 分别属于哪个环/张量因子？对偶是迹配对、内积还是 CRT 幂等元？
2. Hom-Tr 是绝对迹、相对迹还是广义线性变换？源/目标环与密钥输出类型？
3. βⱼ 与旋转单项式为何可放入迹内？由哪个固定子环条件保证？
4. 迹是否归一化？若含 1/r，在二幂 torus 上如何实现？
5. Algorithm 2 第 8-11 行应更新 c_k 还是 c_i？返回值赋给谁？
6. P-MPMUL 的最低位为何从 i=1 开始？位重与边界定义？
7. diff(s) 的 h 是支撑大小还是差分项数？索引是否有排版错误？
8. 参数与安全是否覆盖中间 KS 密钥和相同评估钥重复使用？

---

## 三、融合论文分工（已确定的架构）

| 论文节 | 你提供 | 我们提供 | 状态 |
|---|---|---|---|
| §1 Introduction | — | 4 贡献声明 + 叙事 | ✅ paper_full_v1 已写 |
| §2 Preliminaries | 记号/MLWE/次高斯/Lemma 1-2 | — | 你的 PDF §1 直接映射 |
| §3.1 密码系统 | Mat-MGSW/Vec-MLWE/⊡/Lemma 3 | 实现验证 | 你的 §1.3 |
| §3.2 蝶形 | Alg 1 框架 | DualSubCMUX + 证明 + 实现 | 融合 |
| §3.3 完整自举 | Alg 2 框架 | 三秘密类 + G-ρ + 实现 | 融合 |
| §3.4 sub_a 空间 | Hom-Tr 理论 | 明文/sub_a_ga/负对照/参考变体 | **待你确认 Hom-Tr** |
| §3.5 噪声 | Lemma 1.7/Cor 1.8 主引理 | Thm 2 标定 + Thm 4-6 | 融合 |
| §3.6-3.9 摊销/精度/G-ρ | — | M3/M3'/Thm 6-7/Prop 2/Thm 3 | **全部我们** |
| §4 Security | — | 修正定案 + BatchBoot 重评 + DFR + CI | **全部我们** |
| §5 Experiments | — | 六行矩阵 + r 选值 + 竞品 + 否定性 | **全部我们** |
| §6 Related Work | — | 定位表 + Bergerat 审计 | 我们 |
| §7 Conclusion | — | — | 我们 |

**结论**：除 §2 和 §3.1/3.5 的理论层由你的 PDF 提供外，其余全部由我们完成。

---

## 四、就绪度评估

| 维度 | 状态 | 阻塞项 |
|---|---|---|
| 理论 | **95%** | Hom-Tr 语义确认（§二 的 8 个问题） |
| 实现 | **95%** | Hom-Tr C 实现（确认语义后 1 会话） |
| 安全 | **100%** | 无 |
| 实验 | **100%** | 无 |
| 论文 | **80%** | v1 已写，待融合你的形式化 + Hom-Tr 确认 |
| 投稿就绪 | **~85%** | 确认 Hom-Tr → 补实现 → v2 → 投 |

**建议**：你回答 §二 的 8 个问题后，我们 1-2 个会话内即可完成融合 v2 并启动内部评审。

---

## 五、工件索引（供你核查）

| 文件 | 内容 |
|---|---|
| `docs/paper_ccf_a/paper_full_v1.md` | 论文完整草稿 v1（7 节） |
| `docs/paper_ccf_a/expert_delivery_document.md` | 全部数据单一事实源（v5.1 + 附录 A） |
| `theory_checks/stage389_wanghan_fusion_and_homtr.md` | 你的 PDF 分析 + Hom-Tr 实现计划 |
| `theory_checks/stage390_homtr_benchmark_result.md` | Hom-Tr 失败记录 |
| `theory_checks/stage391_homtr_agent_correction.md` | 独立 agent 修正 + 正确 Hom-Tr 推导 |
| `theory_checks/stage384_m3prime_total_accounting.md` | M3' 摊销推论 |
| `theory_checks/stage385_m1m2_upgrade.md` | M1/M2 投稿级证明 |
| `src/sab_sq.c` | SQ 核实现 |
| `src/sab_pvw.c` | 多体路径实现（含 G-ρ） |
| `repro/stage382_final_matrix/` | 六行矩阵 runner |
| `repro/stage383_r_selection/` | r 选值 runner |
