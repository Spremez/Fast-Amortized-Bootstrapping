# stage357 计划: SQ 尺度化外积 × PVW/MAT-SAB 后端（长程桥）

前置: stage356 SQ 候选（`codex/candidate-sq-scale-sab`，0dc69b8/234cb3a/5cad0d5）。目标: 把 q-量化/重缩放外积移植到 r-lane 矩阵后端，使"279 硬化等速"升级为"硬化 + 摊销吞吐"，并给 AVX-512 服务器核上的分解消除×融合留出接口。

## 现状与接口对照（读 `include/sab_pvw.h` 后的映射表）

| SQ（stage356, 单 lane） | PVW/MAT 对应物 | 移植要点 |
|---|---|---|
| `sab_sq_cmux`（点乘+融合重缩放） | `sab_pvw_CMUX` → `mat_trgsw_mul_pvmtmlwe_DFT` | r 个 body 的 (k+r)² 点乘后做**共享一次**的逐系数 `>>（64-q)`；每 lane 的分解环整体消失 |
| 选择子 `TRGSW(Bg_bit=q)` | `MAT_TRGSW_Key mat_key(l, bg_bit)` | mat 键的 bg_bit=q；`mat_trgsw` 采样路径复用 |
| `sab_sq_ncmux` 升/降尺度包裹 | `sab_pvw_NCMUX` + `PVW_TMLWE_KS aut_minus1` | r 个 body 一起升/降；KS gadget 细化旋钮（SQKS_AUT_*）平移 |
| 零拷贝 ping-pong（v3） | `sab_pvw_RGSW_monomial_mul` | 同构改造，消除 N-slot 回拷 |
| slot 数组 slots/p2 | `sab_pvw_tmp_pool.tmlwe_poly2/acc` | 注意 `PVW_TMLWE` body 布局 |

## 步骤

1. **S0 接口冻结**: 复制 `sab_pvw.c` → `src/sab_pvw_sq.c`（不碰原文件），仅替换外积核与重缩放；`SAB_PVW_SQ_TEST` 旗标 + `probe_pvw_sq.c`。
2. **S1 等价 gate**: r=1 lane 与 scalar SAB 消息等价；r=4 与 `sab_pvw_bootstrap_binary` 消息等价（同 tv/同输入）。
3. **S2 计时**: r∈{1,4,8} SQ vs 原版，比值法（同轮背靠背），±5% 判据；AVX-512 服务器恢复后跑 stage355 矩阵旗标组合（`MAT_TRGSW_SUB_DECOMP_FUSION` 等与本核的叠加实验——分解已消失，预期融合点迁移到重缩放 epilogue）。
4. **S3 安全**: `SQKS_AUT_*`/`SQKS_PACK_*` 平移 + σ_out+15 下 r-lane gate；预检表加 r 维度（BK 尺寸 ×r）。
5. **S4 合并评估**: 与 stage356 同法登记 registry/机制卡；若 D4 候选同期合入 main，评估 bind 路径与 SQ 核的正交性（D4 在 LUT-late-binding 轴，SQ 在外积轴，理论正交）。

## 风险

- `mat_trgsw_mul_pvmtmlwe_DFT` 的 AVX512 特化（RGT4/R6 fulltile）深度绑定分解布局；SQ 版需保留标量回退路径先验证正确性，特化重写留服务器阶段。
- PVW body 的 torus 布局假设（`PVW_TMLWE` 系数域）需逐字段核对 q-量化语义（v1 只做了 k=1 TRLWE）。
- r-lane 下 NCMUX 升/降尺度的每 lane 独立性与共享性（消息各自、尺度同步）需单元探针确认。

## 判据

- 通过: S1 双等价 + S2 无退化（≥0% 或解释清楚）+ S3 σ+15 保持。
- 失败处理: r-lane 布局不适配则退回"SQ 单 lane + PVW 原 lane"混合（SQ 只硬化，不抢吞吐），如实记录。
