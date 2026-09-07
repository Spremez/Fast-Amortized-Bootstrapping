# 矩阵外积理论框架（补全）：PVW-TMLWE × MAT-TRGSW 的正确性、噪声与计数定理

> 定位：补全路径A/矩阵自举的理论层。三个定理（M1 lane 正确性 / M2 噪声传播 / M3 计数与摊销结构）+ 与 1711、Bergerat 的定位。实码锚点：`src/sab_pvw.c`（PVW-TMLWE、stock r-lane）、`src/mosfhet/src/mattrgsw.c`（MAT-TRGSW、MV-EP）、`src/sab_pvw_sq.c`（SQ 侧集成、7 融合旗标）。

---

## 一、形式化定义

**PVW-TMLWE 样本**（r 体共享掩码）：在输出环 $R=\mathbb{Z}[X]/(X^{N}{+}1)$、输出密钥 $s\in R^{k}$ 下，
$$\mathbf{c} = (a;\ b_1,\dots,b_r),\qquad b_j = a\cdot s_j\text{-结构} + m_j + e_j,$$
即**一个掩码多项式 $a$ 同时携带 $r$ 个体**（体 $j$ 加密消息 $m_j$，误差 $e_j$）。实现为 `PVW_TMLWE`；密钥 `pvmtmlwe_new_binary_key`。与 1711 的 Vec-MLWE（$r$ 槽向量）**结构同构**：其 $(\mu_1,\dots,\mu_r)^\top$ 即我们的 $(b_1,\dots,b_r)$。

**MAT-TRGSW 选择子**：$(1{+}r)\ell$ 行的矩阵型 GSW，加密**分块对角**消息 $\mathrm{Diag}(\mu_0;\mu_1,\dots,\mu_r)$（$\mu_0$ 掩码行、$\mu_j$ 体 $j$ 行；$\ell$ 为 gadget 级数，stock/路径A $B_g{=}2^{23},\ell{=}1$）。实现为 `MAT_TRGSW_DFT`（`mattrgsw.c`）；1711 的 $BK_i\in$ Mat-MGSW(Diag(b_1..b_r)) 同构。

**MV-EP**（矩阵外积）：$\mathrm{MV\text{-}EP}(\mathbf{c}, C) = \langle \mathrm{Dec}(\mathbf{c}), C\rangle$——把整个 PVW 样本的分解与选择子的 $(1{+}r)\ell$ 行做一次外积，输出仍为 PVW-TMLWE。

---

## 二、定理 M1（MV-EP 的 lane 正确性与独立性）

**定理 M1**。设选择子加密分块对角 $\mathrm{Diag}(\mu_0;\mu_1,\dots,\mu_r)$（非对角块为零），输入 $\mathbf{c}=(a;b_1..b_r)$ 为 $s$ 下的合法 PVW-TMLWE。则 $\mathrm{MV\text{-}EP}(\mathbf{c},C)$ 输出
$$a' = \mu_0\cdot a + \epsilon_0,\qquad b'_j = \mu_0\cdot b_j\text{-行耦合修正} + \mu_j\cdot(\cdot) + \epsilon_j,$$
精确形式：输出仍为 $s$ 下合法 PVW-TMLWE，加密消息 $(\mu_0 m_0\text{-结构}; \mu_1 m_1,\dots,\mu_r m_r)$，且**体 $j$ 的输出只依赖体 $j$ 的输入与共享掩码演化**——无跨体消息串扰。

**证明**。外积对输入是 $\mathbb{Z}$-线性的：把 $\mathbf{c}$ 的分解向量记为列块 $[\tilde a;\tilde b_1;\dots;\tilde b_r]$（每块 $\ell$ 行），选择子为行块矩阵。分块乘积的第 $j$ 体输出行 = $\sum_i C_{ji}\cdot\tilde c_i$。由分块对角性 $C_{ji}=0\ (j\ne i,\ j\ne 0)$，得
$$b'_j\text{-行} = C_{jj}\cdot\tilde b_j + C_{j0}\cdot\tilde a = \mu_j\cdot b_j\text{-贡献} + \mu_0\cdot a\text{-共享耦合} + \epsilon_j .$$
关键点在于**掩码共享耦合项 $C_{j0}\cdot\tilde a$ 恰好重组出输出体所需的掩码部分**（合法 PVWE 结构要求 $b'_j - a'\cdot s = \mu_j m_j + e'_j$），因为选择子的第 0 行与各体行在密钥展开下满足同一线性关系——这正是"共享掩码"的含义：掩码只演化一次（第 0 行），所有体复用。非对角消息为零 ⇒ 跨体消息项不存在；误差项 $\epsilon_j$ 只来自体 $j$ 自身与共享行的选择子误差（见 M2）。$\square$

**推论（门测试语义）**：逐 lane 抽取（`sab_pvw_sq_extract_tlwe_lane`）后每 lane 独立 decrypt；实测全 r 门 0 失配（r∈{1..8}，2048/4096）即 M1 的实验形态。

---

## 三、定理 M2（噪声传播：无跨体放大）

**定理 M2**。MV-EP 后体 $j$ 的误差 = 共享行误差贡献 + 体 $j$ 行误差贡献，与逐 lane 独立做 stock 外积的误差**同分布阶**：
$$\|e'_j\| \lesssim \|\mu_0\|\cdot\|e^{(0)}\|\text{-项} + \|\mu_j\|\cdot\|e^{(j)}\|\text{-项} + \text{分解舍入项},$$
且体间误差不相关（分块对角 ⇒ 无 $e_i e_j$ 交叉项）。

**证明**。由 M1 的分块展开，误差项只经过对角块与第 0 列块；两个体 $i\ne j$ 的输出误差不共享任何随机源（各自行的选择子误差独立采样）。共享项（掩码行）对每个体是**同一次**噪声实现，但其幅度与单 lane 情形相同（不乘 $r$ 次）。$\square$

**实测对账**：r-lane 噪声与标量同档（SQ 57.6 / stock ~57.7，r=4）；S7 十次目标噪声审计 81,920 点 pair 失败 0、门 Pass——无跨体噪声异常。

---

## 四、定理 M3（计数与摊销结构——为何墙钟是 1.2–1.3× 而非 1/r）

**定理 M3**。一次矩阵盲旋转（蝶形 MonomialMul × $(h{+}1)$ 稀疏步）的
- **MV-EP 计数**：$(h{+}1)\rho n = 43\cdot7\cdot2048 = 616{,}448$（与 $r$ 无关）——对 686 独立执行 $r$ 次标量（$r(h{+}1)\rho n$）是 **EP 粒度上的 $1/r$**；
- **行积计数**：每 MV-EP 含 $(1{+}r)\ell$ 行-多项式积，总计 $(h{+}1)\rho n(1{+}r)\ell$；按输出摊派 $=\ (h{+}1)\rho n\ell\cdot\frac{1+r}{r}$——**比 686×r 的每输出 $(h{+}1)\rho n\ell$ 只省 $\frac{r}{1+r}$**（$r{=}4$ 时 $1.25\times$）。

**理论-实验闭环**：$\frac{r}{1+r}$（r=4: 1.25×）+ packing/KS 尾声摊销 ⇒ 预测墙钟 $\approx1.2$–$1.3\times$，实测 vs 686×4：stock/SQ r-lane $1.21\times$、路径A $1.28\times$。**早前"结构 $1/r$"的表述必须在 EP 粒度与行积粒度之间区分**：1/r 是外积次数，$\frac{r}{1+r}$ 才是乘法次数的摊销上限（共享掩码行的 $(1{+}r)/r$ 开销是结构性的，不可通过调度消除——它是"一次掩码演化服务 r 体"的直接代价）。

**边际 lane**：$T(r{+}1)-T(r)$ 的行积增量 $=(h{+}1)\rho n\ell$（每加一体加一组行），实测 r=4→8 边际 16.2 s > 独立标量 13.10 s ⇒ 超线性来自缓存/工作集，非结构。$\square$

---

## 五、定位：与 1711 / Bergerat 的边界

| 维度 | 1711（Mat-MGSW(Diag) × Vec-MLWE） | Bergerat 等 TCHES'25（Sharing the Mask） | 本工作（PVW×MAT-TRGSW） |
|---|---|---|---|
| 共享掩码多输出形式 | 有（Vec-MLWE r 槽，Thm 4.2 出 r 个） | 有（打包消息共掩码） | 有（同族形式） |
| 选择子形式 | Diag 矩阵 GSW | （待全文审） | $(1{+}r)\ell$ 行 MAT-TRGSW |
| 输入密钥域 | 稠密三元（GINX，$n$ 步） | — | **稀疏二值 $h{=}42$、间隙条件 RS、$(h{+}1)$ 步** |
| 调度 | GINX 累积 | — | 686 蝶形（每精度位 wrap/direct + DualSubCMUX 双亚共享旋转，$k{=}2$ 拓扑上限证明） |
| 安全口径 | 108-bit 经典 | — | CRYPTO'26 组合 min 131.8（输入层）+ 条件熵 T3′ |
| 工程基底 | OpenFHE/tfhe NTT | — | MOSFHET/spqlios AVX-512 + 7 融合旗标 |

**结论**：矩阵/共享掩码形式本身**不是首创**（1711 已有同构形式并给出 Lemma 3.4/Thm 4.1-4.2 的噪声分析；Bergerat 需全文审后定稿措辞）。本工作矩阵侧的可主张增量：**稀疏小钥匙域的整套适配**（$(h{+}1)$ 步调度、间隙条件密钥、条件熵安全定案）+ **DualSubCMUX 蝶形调度及其 $k{=}2$ 拓扑上限证明** + **行积粒度摊销定律（定理 M3）与实测闭环** + **修正安全下的全量实测**。与 SQ 相同的纪律：论文写 "instantiate/adapt/prove"，不写 "propose the matrix form"。

---

## 六、勘误衔接与遗留

- v4 PDF 中"结构上 $1/r$"表述将在 v5 按 M3 精化为"EP 粒度 $1/r$、行积粒度 $\frac{r}{1+r}$、实测 $1.2$–$1.3\times$"。
- 路径A（MV-EP + 7 旗标）在 $r\le8$ 未反超同构建 stock r-lane（+5%~16%，随 r 收窄，交叉外推 r≈9–12）——其价值主张 = 矩阵形式与 M3 结构，而非对 stock 核的反超。
- stage369 B–F（4096 补全/8192/r 细扫/BSK 选项A/扩样）在途；M1/M2 的 8192 域验证随之。

---

## 勘误（2026-09-07，stage380 触发）：M3 行账的 (k+1) 因子

本文件 §四"结构上限 1.25×"的标量每输出行数误记为 ℓ（漏 (k+1) 因子）。
正确行工作上限 = 2(k+1)r/(1+r)，k=1、r=4 时 **1.6×**。实测总时 1.81×
（stage380，include-zero 全旗标）超出行上限的部分 = 旗标消除的非行开销
+ 选择子行读取摊销（与 stage373 分量账自洽）。详见
`stage380_a3_verdict.md` §4。所有引用"1.25× 上限"的下游文档以本勘误为准。
