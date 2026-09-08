# T9：Bergerat et al. TCHES'25（Sharing the Mask）全文审

Date: 2026-09-08（8387 行全文精读）
对象：`references/stage335_fulltext_acquisition/text/sharing_mask_2025_2112_tches.txt`

## 1. 核心结构（与我们工作的逐项对比）

| 维度 | Bergerat CM | 本工作 PVW-TMLWE × MAT-TRGSW | 异同判定 |
|---|---|---|---|
| 共享掩码密文形式 | CM-LWE：(a; b₁..b_w)，w 体共享 mask | PVW_TMLWE：(a; b₁..b_r)，r 体共享 mask | **同构**（1711 已有 Vec-MLWE 同构，两家均继承） |
| 选择子形式 | CM-GGSW：分块对角 | MAT_TRGSW：分块对角 | **同构** |
| 外积定义 | CM-GGSW × CM-LWE → CM-LWE | Mul-GSW × Mul-LWE → Mul-LWE | **同构** |
| FFT/乘法计数 | n(k+w)(ℓ+1) FFTs vs w·n(k+1)(ℓ+1) | (1+r)ℓ 行/事件 vs r·(k+1)ℓ 行/事件 | **同构**（M3 的 (1+r)/r 摊销 = 他们的 k+w/w） |
| 域 | 稠密秘密（GLWE，GINX 消息编码） | **稀疏二值/三值/一般稀疏** | **我们独有**——稀疏域整套适配 |
| 调度 | GINX 逐系数累积 | 686 蝶形 + DualSubCMUX | **我们独有** |
| 安全口径 | Matrix-LWE 假设（稠密） | 稀疏密钥 + CRYPTO'26 修正 | **我们独有** |
| 每体独立 LUT | ✓（f_i 可不同） | ✓（TV 多体） | 同 |
| 私有线性操作 | ✓（CM 外积中的 slot 置换） | — | 他们独有 |
| 压缩 | ✓ w(n+1)→(n+w) | — | 他们独有 |
| 性能 | 51% 提升@8 体（2⁻¹²⁸, p=2） | 1.80×（=80% 提升）@r=4, FINAL | 量级同域（他们的基线含 pfail 差异） |

## 2. 措辞定稿判定

**"共享掩码多体外积/批处理盲旋转"不是本工作首创**——Bergerat CM
（TCHES'25）以 CM-LWE/CM-GGSW 实现了同一机制，1711（本团队前作）以
Vec-MLWE/Mat-MGSW 给出了同一代数形式。本工作论文措辞**必须**：

- ✅ "在稀疏小钥匙域（h ≤ 42 稀疏二值密钥）实例化共享掩码批处理
  摊销自举，并给出 CRYPTO'26 修正安全下的完整参数定案"
- ❌ "提出/首次提出共享掩码多体外积形式"
- ❌ "首创矩阵批处理盲旋转"

**与 Bergerat 的差异化定位**（论文 §7 相关工作段落的措辞）：
> Bergerat et al. [TCHES'25] 在稠密 GLWE 域以 CM 密文实现共享掩码
> 批处理自举；Guimarães–Pereira [CCS'25] 在稀疏密钥域给出摊销自举
> 的 MPmul 调度。本工作将共享掩码矩阵外积（形式上同构于两家）迁移
> 至**稀疏小钥匙域**，给出完整的 (h+1)ρn 步适配、间隙条件 RS 密钥、
> DualSubCMUX 蝶形调度及其 k=2 拓扑上限证明、CRYPTO'26 修正安全下
> 的参数定案与全量实测——这些在两家前作中均不存在。

## 3. 性能对比的公平性注记

Bergerat 的 51% 提升（w=8, p=2, pfail<2⁻¹²⁸）与我们的 1.80×（=80%
提升, r=4, p=2-3, FINAL σ_G=2⁻⁴⁹）**不可直接比较**的原因：
1. 秘密分布不同（稠密 GLWE vs 稀疏二值）→ 安全参数不同；
2. 基线不同（TFHE-rs 单条 vs 686 标量重复 r 次）；
3. 实现库不同（TFHE-rs C++/Rust vs MOSFHET C/gcc）。

论文中**不并列**两者的加速比数字；可并列的是 FFT/乘法计数公式
（同构的 (k+w) vs (k+1)w 摊销）。

## 4. Bergerat 的附加功能（如实披露）

- **slot 置换**（CM 外积中的私有线性操作）——我们的形式在 T4 引理
  中对角单项式版 M1 已含理论支持但未实现；
- **密文压缩** w(n+1)→(n+w)——与我们的 ≤1.07× 钥尺寸不冲突（他们
  压的是密文不是钥），但值得在论文中提及为正交贡献。

## 5. 审计结论

- TCHES'25 正式发表（DOI 10.46586/tches.v2025.i4.925-971），不可回避；
- 措辞纪律已确定（§2），写入 expert_delivery_document.md §7 定稿段；
- Bergerat 引用条目已在本仓 related_literature_matrix.csv 登记
  （S333-010），全文 PDF/txt 已 SHA256 绑定。
