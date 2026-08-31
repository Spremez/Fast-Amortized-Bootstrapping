# 竞品在修正安全标准下的公平对比计划（2026-08-31）

## 用户要求
对有公开实现的竞品，在我们的修正安全标准（h=41, σ+11 = 真 128-bit）下运行实验。

## 有公开实现的竞品清单

| 竞品 | 代码位置 | 语言 | 密钥类型 | 可运行? | 优先级 |
|---|---|---|---|---|---|
| **686/GP25** | 本仓库 | C | 稀疏二值 | ✓ 已跑 | ★★★ |
| **TFHE-rs** | github.com/zama-ai/tfhe-rs | Rust | 稠密 | 需安装 Rust | ★★ |
| **GPV23** | github.com/antoniocgj/Amortized-Bootstrapping | C++ | 稠密 | 需编译 | ★ |
| **MOSFHET** | 本仓库 src/mosfhet | C | 稠密 | ✓ 已用 | ✓ |

## 对比方法

### 层次 1：686（已有完整数据）
- 同机同二进制直接对比
- stock 标量 = 686 的自实现
- 已有 h={39,41,42} × σ+11 的完整数据
- SQ vs stock（核级改进）+ SQ/stock r-lane（矩阵化）

### 层次 2：TFHE-rs（需安装）
```bash
# 在服务器上安装 Rust + TFHE-rs
curl --proto '=https' --tlsv1.2 -sSf https://sh.rustup.rs | sh
cargo install tfhe
# 运行 boolean bootstrapping benchmark
# 注意：TFHE-rs 用稠密密钥，安全模型不同
# 需要找到等价 128-bit 参数集
```

**问题**：TFHE-rs 用稠密密钥，不支持稀疏密钥 → CRYPTO'26 攻击不适用
**解决**：TFHE-rs 的安全声称基于标准 LWE 估计器，不受 279 影响
**对比**：跑 TFHE-rs 的 boolean gate bootstrapping（单 bit），报告单 bit 时间

### 层次 3：GPV23（需编译）
```bash
git clone https://github.com/antoniocgj/Amortized-Bootstrapping
# 编译 + 运行
# 686 论文声称 GPV23 需 ~100GB 密钥
# 安全不受 279 影响（稠密密钥）
```

**问题**：GPV23 的密钥太大（~100GB），可能内存不够
**解决**：如果内存不够，只报告理论对比

### 层次 4：068/BatchBoot（无代码）
- 无法同机运行
- 使用他们论文报告的 686 同机数据（BatchBoot Table 4 / 068 Table 7）
- 标注跨机器 + 未修正安全

## 修正安全下的对比表（目标形态）

| 方案 | 安全模型 | 密钥类型 | 每消息(ms) | 每bit(ms) | 同机? | 安全 |
|---|---|---|---|---|---|---|
| **686 标量** | CRYPTO'26 修正 | 稀疏 h=41 | 6.79 | 2.26 | ✓ | ≥128 |
| **SQ 标量** | CRYPTO'26 修正 | 稀疏 h=41 | **6.20** | **2.07** | ✓ | ≥128 |
| **SQ r-lane r=4** | CRYPTO'26 修正 | 稀疏 h=41 | ??? | ??? | ✓ | ≥128 |
| TFHE-rs | 标准 LWE | 稠密 | ~7-10 | 7-10 | ✓(装后) | ≥128 |
| GPV23 | 标准 LWE | 稠密 | ~100MB keys | ~10-50 | 需编译 | ≥128 |
| BatchBoot | 标准 | 稀疏? | 3.57(引用) | ~1.2(引用) | ✗ | 未修正 |
| 068 NTTRU | 标准+NTRU | 稀疏 | 2.68(引用) | ~0.9(引用) | ✗ | 未修正 |

## 安全修正的正确表述

**TFHE-rs 和 GPV23 用稠密密钥 → 不受 CRYPTO'26 影响 → 它们的安全声称是正确的。**
**686/BatchBoot/068 用稀疏密钥 → 受 CRYPTO'26 影响 → 需要修正。**

论文表述：
> "我们修正了稀疏密钥方案（686/BatchBoot/068）在 CRYPTO'26 攻击模型下的安全参数，
> 并在修正后的安全级上与稠密密钥方案（TFHE-rs）进行公平比较。
> 稠密密钥方案不受等距混合攻击影响，无需修正。"

## 下一步行动

1. ✅ r-lane 实验修正中（服务器 PID 879198）
2. ⏳ TFHE-rs 安装 + 基准（需要 Rust）
3. ⏳ GPV23 编译尝试（可能内存不够）
4. ⏳ 汇总全部对比表
