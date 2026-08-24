# stage356 计划: SQ 尺度量化 SAB（2025/1711 × 2025/686 × 2026/279）

## 目标

在不触碰 scalar 基线、`sab_pvw_*`（MAT-SAB）与 candidate D（`sab_operator_*`）的前提下，把 eprint 2025/1711 的尺度化（平方 gadget）外积移植进本仓库（eprint 2025/686）的稀疏摊销自举，得到：

1. **等价且可测速** 的盲旋转变体（gate: 全部 in_N slot 消息与 LUT 期望一致）；
2. **噪声预算** 上把密钥噪声项系数从 σ·2^{27.1} 降到 σ·2^{q+3.5}（+2(23−q) bit 的 σ 余量），用于吸收 eprint 2026/279 的稀疏密钥环同构混合攻击安全差（保守 15 bit）；
3. **安全预检表**（逐参数集: 279 差、σ 上调需求、SQ 可吸收量、q 推荐、stock 对照判定）。

## 背景

- 2025/1711: 双模数 (T>Q) 尺度化外积，去掉 gadget 分解；∆=Q²/T 抑制密钥噪声（Lemma 3.4）；ℓ=1 形态与本仓库 MOSFHET l=1/Bg=23 原语同构。
- 2026/279: MLWE→LWE 换算不保守；稀疏 RLWE 上 isometry 混合攻击差最高 15 bit —— 本仓库输入/输出密钥均为稀疏，全部参数集受影响。
- D4 语义探针已确认 DFT 信封 = mod-2^64 整数卷积（`execute_reverse_torus64` 原值有符号 double 契约），是本候选可行性的原语前提。

## 步骤

1. **S0 隔离模块**（本 stage）: `include/sab_sq.h` + `src/sab_sq.c`，`SAB_SQ_EQUIV_TEST` 旗标；构建隔离 `BUILD_DIR=./build_sq` + `main_sq` 目标（与并行 D4/主线构建零共享）。
2. **S1 等价 gate**: SET_2_3_2048 形状（in_N=2048, h=39, ρ=7, b=3），q=16 默认；`SAB_SQ gate: Pass (mismatch 0/2048)` + 噪声偏离 log2 报告。失败则按机制卡回退条款逐层探针。
3. **S2 计时**: 同二进制内 scalar 对照（MEASURE_BOOTSTRAP_TIME, reps=3 预留 10 次高统计到服务器矩阵）；q=23 复测（预期与 stock 重合的噪声/速度参照点）。
4. **S3 安全预检**: `scripts/sq_security_preflight_279.py` 输出 CSV 入 `repro/stage356_sq_scale_sab/`；相对模型显式声明（基线=686 设计级；σ 弹性 0.5–1.0；密度插值 279 差）。
5. **S4 高统计/合并准备**: 服务器矩阵（stage355 基础设施）+ 与 PVW/MAT 后端的组合实验留 stage357+，本 stage 不动 `sab_pvw_*`。

## 通过/失败判据

- 通过: gate Pass；速度与 scalar 差 ≤5%（或如实记录差异并给出解释）；预检表齐全；无对默认路径的行为改动（`test_sab` 在无旗标构建下不变）。
- 失败处理: 速度退化 >5% → 候选降级为安全硬化等价路径；等价失败 → 探针定位，允许一次方程修订（对齐 candidate 纪律）。

## 工件

- 代码: `include/sab_sq.h`, `src/sab_sq.c`, `main.c`（增量测试块）, `Makefile`/`Makefile.def`（增量旗标）
- 文档: 本计划、`theory_checks/stage356_sq_scale_sab_model.md`、`algorithm_variants/sq_scale_sab_card.md`、`docs/stage356_sq_scale_sab_log.md`
- 复现: `repro/stage356_sq_scale_sab/`（构建日志、运行日志、预检 CSV）、`scripts/run_stage356_sq_scale_sab.sh`
- 注册: `repro/stage_commit_registry.csv` 追加行
