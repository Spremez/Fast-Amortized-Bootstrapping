# stage356 P0-a 服务器复测结果（spz, AVX-512, spqlios_avx512, 2026-08-27 定时收割）

环境: luck-Precision-7920-Tower (Xeon Gold 6230R), fab-main @ candidate-sq-scale-sab e77f502, `-march=native`, MOSFHET_DETERMINISTIC_RNG（种子固定，可复现）。完整 stage 日志在 SQ 分支 `docs/stage356_sq_scale_sab_log.md`，本文件为 main 侧收割记录。

## 速度（9 轮同二进制背靠背, SET_2_3_2048, 每自举 ~11–12s）

| 指标 | SQ(q=16) v3 vs scalar |
|---|---|
| **中位比值** | **0.9025（快 ~9.7%）** |
| min-of-9 | 0.8929 |
| 均值 | 0.9027 |
| 全距 | 0.893–0.918（极稳定，每轮 CI < 1.5%） |
| q=23 参照 | 0.906（快 9.4%） |

相对本地 ffnt/haswell 的 −4.5%：AVX-512 核上分解消除 + 融合内核优势放大。

## 正确性 / 噪声（最大相位偏离 log2，预算 60）

- q=16: 9/9 gate **Pass（0/2048）**，噪声 57.45 vs scalar 57.43（持平）
- q=23: **Pass**，57.79 vs 57.43

## 279 硬化（σ_out+15bit, aut-KS l=4/Bg=2^16）

- **SQ gate Pass, 噪声 59.36; 同参数 stock scalar 62.09（2^-2.0，失效）**——服务器复现本地硬化闭环
- 硬化开销仅 **+1.1%**（11.06s vs 10.93s）

## 论文影响

SQ 候选在目标硬件上的主张升级为：**≈10% faster + 完整恢复 15-bit 稀疏密钥安全边际（代价 +1%）**。P0-a 关闭。工件：`repro/stage356_sq_scale_sab/server_*.log|csv|txt`。
