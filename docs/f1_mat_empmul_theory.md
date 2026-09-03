# F1 理论文档：MAT-EMPmul — 多 lane 矩阵 SAB 与多比特 CMux/FFT 域融合的复合构造

日期: 2026-08-19
状态: 机制提案（纸面级，未实现；未获任何 hot-path 权限）
数据依据: `repro/stage322_schedule_profile_attribution/`（真实 profile）、
`repro/stage345_binary_matrix_synthesis/`（B1 六行基线）、
BatchBoot USENIX Sec'26 prepub（`literature/external_batchboot_usenix26/`）
配套治理: `docs/roadmap_topconf_post686.md` §4 F1；Candidate D D2 已另线通过
（`theory_checks/candidate_d_operator_closure.md`，worktree）

---

## 1. 定位

F1 回答一个问题：**当前 exact-dense PVW/MAT-SAB（B1，1.6121×–1.7476×）能否通过
吸收 BatchBoot 的 selector 侧优化，达到对 BatchBoot 本身的反超？**

两条成本轴的正交性：

| 轴 | 优化对象 | 来源 | 当前状态 |
|---|---|---|---|
| accumulator 侧 | r 条 lane 共享一次矩阵外积 | 本仓库 MAT-SAB | B1 已实测 |
| selector 侧 | 每 MPmul 步的 FFT 计数 | BatchBoot EMPmul | 未吸收 |

D2 刚验证的算子闭合定理表明 accumulator 侧更新律在 Γ={id, τ₋₁} 下封闭；
F1 改造的是 selector 步本身（每步消化 2 个位置差 bit），二者正交可复合。

## 2. 构造

### 2.1 现状（B1 的 selector 步）

对标量二进制 SAB，稀疏调度第 t 步对位置差 v_t 做逐 bit 条件旋转：

```text
bit i, offset 2^i, 选择子 bit v_{t,i}:
  非环绕 slot j ≥ 2^i:  c'_j = CMUX(c_j, c_{j-2^i}; v_{t,i})
  环绕 slot j < 2^i:    c'_j = NCMUX(c_j, -τ₋₁(c_{n-2^i+j}); v_{t,i})
```

MAT 形式下所有 lane 共享同一选择子调度，选择子为 (r+1)² 结构的矩阵
TRGSW；`docs/cost_model.md` 给出单步 = ρ·N 次 CMUX/NCMUX 级外积。

### 2.2 EMPmul 步（δ=2 多比特矩阵 CMux）

BatchBoot §4.1 的 EMPmul 把每步消化 2 个 bit（v_{2t}, v_{2t+1}）合并为一次
四路选择。迁移到矩阵选择子：

```text
步 t（bit 对 i=2t, 2t+1, 偏移 a=2^{2t}, b=2^{2t+1}）:
  非环绕 j ≥ a+b:
    U'_j = U_{j-a} ⊡ B⁺_{t,0} + U_{j-b} ⊡ B⁺_{t,1}
         + U_{j-a-b} ⊡ B⁺_{t,2} + U_j ⊡ B⁺_{t,3}
  中间段与环绕段（三段区间分解）:
    以 -τ₋₁ 变换后的源槽经参数化外积 ⊡_{τ₋₁} 与 B⁻_{t,·} 相乘
```

其中 `B⁺_{t,m}`/`B⁻_{t,m}`（m=0..3）为四路矩阵选择子钥匙，明文值为
0/1 指示（对应 (v_{2t},v_{2t+1}) 的四种取值，环绕行存放 τ₋₁ 变换版本）。

### 2.3 FFT 域 automorphism 融合（hoisting）

关键观察（BatchBoot Eq.8）：τ₋₁ 可穿透 gadget 分解与 FFT——对已变换的
accumulator 系数，automorphism 表现为 DFT 域中与 B⁻ 钥匙的 Hadamard 乘
融合，不再需要独立的 automorphism KS/FFT。本仓库已有
`SAB_PVW_BACKEND_FROM_DFT_ADD`（accumulator 常驻 DFT 域）与
`SAB_PVW_SUB_DECOMP_FUSION`，是该迁移的现有落点。

### 2.4 与 D2 算子闭合律的衔接

D2 检查器验证的通道更新律（单项式乘→通道各自乘单项式；NCMUX 环绕
源→通道交换并取 τ 再取负；CMUX→通道仿射）只依赖"每步实现的是同一个
环旋转 X^{v_t}"这一语义。EMPmul 是同一语义的重新打包
（X^{v} = Π_t X^{v_{2t}·2^{2t} + v_{2t+1}·2^{2t+1}}），因此：

> **引理 F1-1（闭合不变式）**：EMPmul 步序列与逐 bit 步序列在 Γ={id, τ₋₁}
> 算子代数下诱导同一个复合算子；D2 的 basis-vector 等价对 EMPmul 调度
> 自动成立。
> **验证状态（2026-08-19）**：`scripts/check_f1_empmul_equivalence.py` 在
> GF(257)[X]/(X^N+1)（N∈{8,16}）上对全部 bit 对、全部 (v_a,v_b)∈{0,1}²、
> 全部 slot 验证了 BatchBoot 三区间融合步（以 −τ₋₁ 环绕语义）与两步顺序
> 组合的逐系数相等：**160 项检查 0 失败**。结合 D2 已验证的通道追踪性质，
> F1-1 在有限检查层级成立。

## 3. 代价模型

### 3.1 selector 侧 FFT 计数（BatchBoot Table 2，δ=2）

```text
逐 bit:  FFT 次数 ≈ 2(2d+2)·n·ℓ      （d = gadget 长度, ℓ = 位置差 bit 数）
EMPmul:  FFT 次数 ≈ (d+1)·n·ℓ        （约 1/(2d+4)·(d+1) ≈ 1/4 ~ 1/3 缩减）
Hadamard: 4dn·ℓ（廉价，O(n) vs FFT 的 O(n log n)）
```

### 3.2 与 B1 的复合（真实 profile 依据）

`stage322` 组件画像（SET_2_3_2048, r=4, include_zero，profile_full
49.54s，T_bootstrap/r=6.19s）：

| 组件 | 份额 | F1 作用 |
|---|---:|---|
| mat_ep_lifecycle（分解+FFT+Hadamard+IFFT） | 57.62% | 直接缩减 ~1/3–1/2 |
| cmux_from_dft（物化残差） | 38.08% | 部分缩减（合并物化） |
| dense_from_dec（最大未闭合子件） | 21.24% | 直接缩减 |
| sub_a / ncmux_auto | 2.69% / 0.77% | 不变 |

保守投影（仅 mat_ep_lifecycle 缩减 45%，其余不变）：

```text
新 profile ≈ 49.54s × (1 − 0.576 × 0.45) ≈ 36.7s
完整 SAB 相对 scalar ≈ 1.747× × (49.54/36.7) ≈ 2.36×
乐观投影（连 cmux_from_dft 一半并入）: ≈ 2.5–2.6× over scalar
```

对照：BatchBoot 自报 2.2×/2.4×（2/4-bit，同 scalar 基线），密钥 3.2–3.5×。
F1 若达成 ≥2.3× over scalar 且密钥 ≤2× scalar（见 §5），则在
"每消息时间 × 密钥规模" Pareto 上同时压倒 B1 与 BatchBoot。

## 4. 噪声引理（MAT 形式，证明义务）

对标 BatchBoot Lemma 4.1（V_EMP < Var + 2ℓ·V_EP）：

> **引理 F1-2（MAT-EMPmul 噪声）**：设 r-lane 矩阵外积噪声方差为 V_EP^MAT
> （四把钥匙中恰有一把明文为 1，其余为 0；0-选择子的外积仅引入分解噪声
> ×mask 项）。δ=2 步序列输出满足
> V_EMP^MAT < Var_in + 2ℓ·V_EP^MAT + 2ℓ·V_auto^fuse，
> 其中 V_auto^fuse 为 FFT 域 τ₋₁ 融合的残余（无独立 KS 噪声项）。

证明义务：四路和中三项是 0-选择子外积，其噪声贡献按现有 MAT 噪声模型
（Stage331 实测 log₂σ=−2.213 torus）重新推导上界；include-zero 行的 0/10
pair-failure 余量必须复验（多 bit 步每步外积次数不变、单次噪声结构变化）。

## 5. 密钥与资源

- 四路钥匙/步 vs 现一把/bit：selector 钥匙材料 ≈ 2×（同共享结构，不随 r
  增长），预估 B1 的 ≤1.07× → ≤2.2× scalar，仍远低于 BatchBoot 3.2–3.5×。
- RSS：钥匙增长 ≤2.2×，B1 的 2.4GB → ≤5.3GB（r=4, 2048 行），需在 7GB
  WSL 预算内核算 4096 行。

## 6. Gate（映射仓库机制）

| Gate | 内容 | 通道 |
|---|---|---|
| G1 机制门 | 引理 F1-1：δ=2 调度过 D2 式有限检查器（GF(257), N∈{8,16}, 6 负控制复用） | 纸面 finite checker 扩展 |
| G2 噪声门 | 引理 F1-2 推导 + 与 Stage331 实测噪声对照（预测/实测 <1.3） | theory_checks + stage 化 |
| G3 Amdahl 门 | 完整 SAB 投影 ≥ B1 + 30%（即 ≥2.27× over scalar） | §3.2 模型 + kernel microbench |
| G4 资源门 | key 比 ≤2.5× scalar；RSS ≤ B1×1.3××参数规模因子 | kernel 原型计量 |

止损：G1 失败 → F1 关闭（调度语义不保）；G3 投影 < +30% → 降级为 TCHES
组件优化；G2 余量不足 → δ 回退 1（等价现状）。

## 7. 与 D 路线的组合

D（late-binding 算子通道）替换 accumulator 侧的 lane 结构；F1 压缩
selector 步成本。二者作用于同一调度的不同侧，可叠加：D 的通道更新由
选择子驱动，把驱动步换成 EMPmul 步即得 D+F1 复合。顺序建议：D3 完成后
（D 的 Amdahl 门 ≥+10%），若 F1 的 G1/G3 独立成立，评估复合投影；若 D3
拒绝，F1 独立成文（系统论文主轴 + 密钥 Pareto）。

## 8. 明确的非声明

- 本文全部性能数字为**投影**（除引用的 stage322/345 实测外），无任何
  新实测主张。
- 未实现任何 kernel；production hot-path 权限不变（false）。
- 对 BatchBoot 的引用数字均来自其 prepub PDF（SHA256
  `a1d1d694...01ca403`），同机 head-to-head 前不得写成对比结论。
