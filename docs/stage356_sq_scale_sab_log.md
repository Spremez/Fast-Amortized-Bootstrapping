# stage356 日志: SQ 尺度量化 SAB（scale-quantized SAB）

日期: 2026-08-24 · 候选: SQ/SQS · 分支: codex/candidate-sq-scale-sab（隔离）

## 结论（TL;DR）

1. **正确性 gate 通过**: q=16 与 q=23 下 `SAB_SQ gate: Pass (mismatch 0/2048)`——2025/1711 的尺度化（平方 gadget）外积成功移植进 2025/686 的稀疏摊销盲旋转，DFT 域点乘 + 逐系数 `>>（64-q)` 重缩放完全替代 gadget 分解。
2. **噪声与 stock 统计级一致**: q=16 最大相位偏离 log2 = 57.55 vs scalar 57.54（同一随机源），验证理论账本中共有 KS/输入噪声地板主导、σ 项在 q=16 被完全抑制的预测。
3. **速度（v3 内核，最终）**: **SQ 快于 scalar**——9 轮同二进制背靠背比值（WSL ffnt/haswell，负载扰动下）: 中位 **−4.5%**、min-of-9 **−7.3%**（28.89s vs 31.16s）、均值 −2.8%，9 轮中 7 轮更快；且 SQ 每轮先测（含冷启动劣势，结论偏保守）。v3 = 融合重缩放+重组（每 CMUX 省一次 2N 遍历）+ 零拷贝 ping-pong（每次自举消除 ~2.7GB 回拷）。v1 内核为 −1~−1.7%（等速）；服务器 AVX-512 高统计确认留 stage357。噪声/正确性不变（57.55/57.54，Pass），σ+15 硬化配置在 v3 下同样 Pass。
4. **安全侧**: 2026/279 预检表落地（见下）；SQ(q=16) 提供 2(23−16)=14 bit 的 σ 上调余量，等速吸收稀疏密钥环同构混合攻击差的主体；stock 方案在 σ+15 bit 时盲旋转噪声吃满预算（理论 §2）。

## 交付物

- `include/sab_sq.h` + `src/sab_sq.c`（隔离模块，仅 `SAB_SQ_EQUIV_TEST` 旗标编译）
- `src/probe_sq.c`（独立验证载体，自带 main，仓库 probe 惯例）
- `Makefile` 增量: `main_sq.exe`/`probe_sq.exe` 目标 + `SAB_SQ_EQUIV_TEST`/`SAB_SQ_Q` 旗标（Makefile.def）
- `scripts/sq_security_preflight_279.py` + `scripts/run_stage356_sq_scale_sab.sh`
- 理论: `theory_checks/stage356_sq_scale_sab_model.md`；机制卡: `algorithm_variants/sq_scale_sab_card.md`；计划: `experiments/stage356_sq_scale_sab_plan.md`
- 工件: `repro/stage356_sq_scale_sab/`

## 关键实现契约（供后续合并者）

- `trgsw_monomial_sample` 的消息尺度 = `m·2^{64-Bg_bit}`: 选择子密钥直接用 `Bg_bit=q` 采样即得 1711 尺度形态，**零原语改动**。
- DFT 信封 = 原值有符号整数卷积 mod 2^64（`execute_reverse_torus64`/`execute_direct_torus64`，与 D4 语义探针结论一致）: 消息路径 `(bit·2^{64-q})⋆c >>（64-q) = bit·c` 严格精确（不回绕: c ≤ 2^{q-1}）。
- NCMUX: 升尺度 `<<（64-q)` → 标准 aut-KS（torus 域，语义/噪声不变）→ 舍入右移回 Q 尺度。
- 盲旋转结束时 slot 升尺度回 torus，extract/packing/HW KS 链零改动复用。

## 过程记录

1. Windows 原生构建（LLVM-MinGW PE）首次运行偶发通过、随后随机段错误。逐层定位: 密钥系数读到 double 位型垃圾 → 两个逻辑缓冲别名 → **上游发现: `PORTABLE_BUILD` 的 `generate_rnd_seed` 走 `fopen("/dev/urandom")`，Windows 上返回 NULL 后 `fread(p,1,32,NULL)` 未定义行为，非确定性破坏堆**。`MOSFHET_DETERMINISTIC_RNG=true`（splitmix）规避 RNG 半个问题后堆损坏仍存（三元密钥 keygen 期间 input 缓冲被复用，机理未彻底定位，疑似 NULL-fread 对 CRT 堆状态的持续性破坏）。**结论: Windows 原生便携路径不可用于本阶段验证；规范环境 Linux/WSL 下 3/3 稳定**。上游修复建议（另行报告）: PORTABLE_BUILD 下检测 fopen 失败回退确定性 RNG。
2. main.c 受 candidate-D 线程并发回写（两次覆盖本 stage 的插桩/构建产物），按仓库 `probe_mul.c`/`probe_v6.c` 先例将验证载体迁至 `src/probe_sq.c`（自带 main），构建走独立 `BUILD_DIR` + `probe_sq.exe` 目标，实现零共享。main.c 中保留的 `SAB_SQ_EQUIV_TEST` 集成块为 D5 式合并预留点。
3. MinGW `-o main_sq` 实际产出 `main_sq.exe`（MSYS ls 隐藏后缀）+ make 时间戳在并发编辑下失真——排查时曾误删/误跑旧二进制；runner 已固化显式 `.exe` 目标名。

## 279 预检要点（保守相对模型，脚本头部声明边界）

- 密度插值差距: input 侧（h/N≈0.01–0.02）取满 15 bit；output 侧（0.25）≈9.2 bit。
- SQ 可吸收 = 2(23−q)，受噪声下限 q ≥ b_prec+10 约束: SET_2_3/4_5 族 q=13–15 即可覆盖 output 侧与（乐观弹性下）input 侧；b≥7 族残余差由 h 补。
- stock 无对应旋钮（操作数尺度钉死 2^23），279 下只能 h/N 硬化（变慢）。

## σ-硬化对照实验（σ_out +15 bit, run_wsl_q16_sigma15.log）

**否定性发现（重要）**: 平抬 σ_out（2^{-50}→2^{-35}）后 SQ(q=16) 与 scalar 双双失效（SQ gate 1774/2048 miss、噪声 2^{-1}；scalar 噪声 57.54→61.90）。定位: 失效不在乘积路径，而在**共享的 NCMUX aut-KS**——KS 噪声 ∝ σ·2^{Bg}，每 slot ~140 次 KS 累计 √140·σ·2^{28.5} ≈ 2^{-1.9}，超出 2^{-4} 预算；SQ 的 Q²/T 抑制只保护外积乘积项。**结论: 完整的 279 硬化参数集必须同时细化 aut-KS（更小 Bg/多层）与 packing KS 链的分解参数**（密钥量小、代价可控，属 stage357 参数工作），σ 单旋钮方案不成立。理论模型 §2 已相应标注。

## 过程教训（工程记录）

- 本仓库 C 源文件为 CRLF；Python 文本模式读写在替换串含 `\\n` 或跨行时会**静默不匹配**（本 stage 两次"清理成功"实为 no-op，靠 Edit 工具兜底）。涉及 C 源的脚本化改写必须带 assert。
- `MOSFHET_DETERMINISTIC_RNG=true` 自动附带 `-DMOSFHET_TEST_RNG_SEED=1`，工件完全可复现。

## 遗留 / 下一步

- [x] σ-硬化对照实验（结论如上: 需 KS 联动细化，非单旋钮）
- [x] **279 硬化参数集 v2（stage357 前置，本分支补做）**: aut-KS gadget 运行时可调（`SQKS_AUT_L`/`SQKS_AUT_BG`/`SQKS_PACK_ELL`/`SQKS_PACK_BG`）。**σ_out+15 bit（=完整恢复 279 保守 15 bit 边际）下 SQ(q=16) gate Pass**:
  - `aut(l=2, Bg=2^19)`: Pass，噪声 57.30→59.30（2^{-4.7}），见 `run_wsl_q16_sigma15_aut2_19.log`
  - `aut(l=4, Bg=2^16)`: Pass，噪声 59.27（2^{-4.7}），见 `run_wsl_q16_sigma15_aut4_16.log`
  - 同 σ 的 stock scalar（aut l=1/Bg=2^23 不可调）: 噪声 62.04（2^{-1.96}）失效
  - 默认配置回归: 无环境变量时与 v1 完全一致（57.55/57.54，Pass）
  - 细化 KS 只作用于 ~0.9% 的 NCMUX 路径与最终 KS 链，密钥量小；本机计时受并行负载扰动不可比，速度结论仍以 §TL;DR runner 数据为准
  - 残余 +1.7 bit 噪声来自 packing KS 链（`SQKS_PACK_*` 已可调，进一步压制留参数扫描）
- [ ] AVX-512 服务器矩阵（stage355 基础设施）上复测核速度与 10 次高统计
- [ ] 与 sab_pvw/MAT 后端组合（stage357）；ternary/gaussian 选择子路径
- [ ] 279 全文 isometry-hybrid 精确代价模型替换保守插值

