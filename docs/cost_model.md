# 阶段 1: SAB 外积复杂度账本

目标: 给当前 scalar SAB baseline 建立可核查的 external product 计数模型，用于判断 `sab_pvw_*` 是否真正替换了主瓶颈。

## 符号

- `N = in_N`
- `h = sab->h`
- `rho = sab->r_prec`
- `E = 1` 次 `trgsw_mul_trlwe_DFT(...)`
- 当前 `sab_blind_rotate` 只支持 `in_k = 1`

## 基本计数

- `CMUX`: 1 次 `E`
- `NCMUX`: 1 次 `E`，外加 automorphism/add/sub
- `RGSW_monomial_mul`: `rho * N` 次 `E`
- binary `sparse_mul`: `(h + 1) * rho * N` 次 `E`
- ternary `sparse_mul`: `(h + 1) * rho * N + h * N` 次 `E`
- gaussian/arbitrary `sparse_mul`: `(h + 1) * rho * N + h * N` 次 `E`

解释:

- `RGSW_monomial_mul` 对每个 precision bit 都遍历 `N` 个 accumulator slot，因此每次 monomial multiplication 固定产生 `rho * N` 次 CMUX/NCMUX。
- `sparse_mul` 对 `h` 个 sparse secret step 调用 `RGSW_monomial_mul`，最后再调用一次 final `RGSW_monomial_mul`，所以 monomial 部分是 `(h+1)*rho*N`。
- ternary 的 `sub_a` 每个 sparse step 额外调用一次 sign selector 外积，总计 `h*N`。
- gaussian/arbitrary 的 `sub_a_ga` 每个 sparse step 额外调用一次 coefficient selector 外积，总计 `h*N`。
- include-zero 当前不是可靠 baseline，因为 keygen 路径仍有未实现断言；不把它纳入通过条件。

## Binary 参数集计数

下表使用 `main.c` 中 binary `target_r_prec` 估算。实际运行时应同时记录 `get_min_prec(input_key)` 输出；若实际 `rho` 与 target 不同，以实际值重算。

| 参数集 | N | h | target rho | 外积次数 |
|---|---:|---:|---:|---:|
| SET_2_3_2048 | 2048 | 39 | 7 | 573,440 |
| SET_2_3_4096 | 4096 | 32 | 8 | 1,081,344 |
| SET_2_3_8192 | 8192 | 25 | 10 | 2,129,920 |
| SET_4_5_2048 | 2048 | 42 | 7 | 616,448 |
| SET_4_5_4096 | 4096 | 34 | 8 | 1,146,880 |
| SET_4_5_8192 | 8192 | 26 | 10 | 2,211,840 |
| SET_6_7_4096 | 4096 | 33 | 9 | 1,253,376 |
| SET_6_7_8192 | 8192 | 27 | 10 | 2,293,760 |
| SET_8_9_4096 | 4096 | 34 | 9 | 1,290,240 |
| SET_8_9_8192 | 8192 | 28 | 10 | 2,375,680 |
| SET_8_9_HIGH_FR | 8192 | 28 | 10 | 2,375,680 |

核验例:

```text
SET_2_3_2048 binary:
(h + 1) * rho * N = 40 * 7 * 2048 = 573,440
```

## Ternary 参数集计数

公式: `total = (h + 1) * rho * N + h * N`

| 参数集 | N | h | target rho | monomial 外积 | sign 外积 | 总外积 |
|---|---:|---:|---:|---:|---:|---:|
| SET_2_3_2048 | 2048 | 35 | 7 | 516,096 | 71,680 | 587,776 |
| SET_2_3_4096 | 4096 | 26 | 9 | 995,328 | 106,496 | 1,101,824 |
| SET_2_3_8192 | 8192 | 23 | 10 | 1,966,080 | 188,416 | 2,154,496 |
| SET_4_5_2048 | 2048 | 38 | 7 | 559,104 | 77,824 | 636,928 |
| SET_4_5_4096 | 4096 | 28 | 9 | 1,069,056 | 114,688 | 1,183,744 |
| SET_4_5_8192 | 8192 | 24 | 10 | 2,048,000 | 196,608 | 2,244,608 |
| SET_6_7_4096 | 4096 | 30 | 9 | 1,142,784 | 122,880 | 1,265,664 |
| SET_6_7_8192 | 8192 | 25 | 10 | 2,129,920 | 204,800 | 2,334,720 |
| SET_8_9_4096 | 4096 | 32 | 9 | 1,216,512 | 131,072 | 1,347,584 |
| SET_8_9_8192 | 8192 | 26 | 10 | 2,211,840 | 212,992 | 2,424,832 |

## Arbitrary / gaussian 参数集计数

公式: `total = (h + 1) * rho * N + h * N`

| 参数集 | N | h | target rho | monomial 外积 | coefficient 外积 | 总外积 |
|---|---:|---:|---:|---:|---:|---:|
| SET_A2 | 4096 | 32 | 9 | 1,216,512 | 131,072 | 1,347,584 |
| SET_A3 | 8192 | 32 | 10 | 2,703,360 | 262,144 | 2,965,504 |
| SET_A4 | 4096 | 32 | 9 | 1,216,512 | 131,072 | 1,347,584 |
| SET_A5 | 8192 | 32 | 10 | 2,703,360 | 262,144 | 2,965,504 |

## 与 PVW/matrix 外积的关系

当前 scalar baseline 的 hot loop 是大量重复的 `TRGSW_DFT x TRLWE -> TRLWE` 外积。`mbfhe-mb` 的 matrix/PVW 形式把 TLWE/TRLWE body 从 1 个扩展为 `r` 个 body，并用 matrix TRGSW FFT external product 同时更新这些 body。

阶段 4 已选择的解释:

- `r` 表示多 LUT / 多 SAB lane。
- 所有 lane 共享同一 `a`、同一 sparse selector schedule、同一 CMUX/NCMUX 控制流。
- 每个 lane 有自己的 accumulator body 与 LUT payload。

因此，理论收益应来自把原本 `r` 条 lane 上重复的分解/FFT/外积调度合并为一次 matrix external product，而不是减少 scalar SAB 的 monomial schedule 数量。阶段 2 必须先用 instrumentation 证明 `E` 及其 surrounding CMUX/NCMUX 成本占主导；阶段 3 再用 microbench 验证 matrix kernel 的 `r=1` 不退化、`r=2/4` 有吞吐扩展。

## 通过/失败判据

阶段 2 通过:

- `trgsw_mul_trlwe_DFT`、CMUX/NCMUX、`RGSW_monomial_mul` 或其合计在完整 `sab_rlwe_bootstrap` 中占主导。
- microbench 中单外积成本稳定，且重复测量方差可解释。

阶段 2 失败处理:

- 若 setup、extract、packing KS、HW reducing KS 或动态分配占主导，则优先优化 tmp pool、DFT 转换复用、extract/KS 路径。
- 在证明 bottleneck 前，不进入大规模 `sab_pvw_*` 集成。
