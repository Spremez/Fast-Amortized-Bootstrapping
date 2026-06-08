# 阶段 2: baseline profiling 初测

日期: 2026-06-08

## profiling 开关

新增构建开关:

```bash
SAB_PROFILE=true
```

默认值为 `false`，因此普通构建不会打印 profile 表，也不会改变 baseline 输出格式。

当前 instrumentation 统计 inclusive time:

- `trgsw_mul_trlwe_DFT`
- `CMUX`
- `NCMUX`
- `RGSW_monomial_mul`
- `sub_a` / `sub_a_ga`
- `sparse_mul`
- `setup_tv_xb`
- `sab_blind_rotate`
- `sab_rlwe_bootstrap_wo_extract`
- extract loop
- packing keyswitch
- HW reducing keyswitch
- `sab_rlwe_bootstrap`

## 构建与运行命令

默认关闭 profile 的 Windows portable smoke build:

```powershell
make -B FFT_LIB=ffnt A_PRNG=none ENABLE_VAES=false PARAM=SET_2_3_2048 ARCH_FLAGS="-march=haswell"
```

结果: 构建通过。仍存在既有 Windows format warning。

WSL/Linux profiling build:

```bash
make -B FFT_LIB=spqlios A_PRNG=none ENABLE_VAES=false PARAM=SET_2_3_2048 SAB_PROFILE=true
```

结果: 构建通过。

WSL/Linux profiling run:

```bash
timeout 240s ./main
```

结果: `Pass`。

## SET_2_3_2048 binary 初测结果

运行参数摘要:

- `N=2048`
- `h=39`
- `rho=7`
- `reps=3`
- `target_r_prec=7`
- 本次 rejection sampling attempts: 385
- benchmark 输出: `Bootstrapping time: 15,190,610 us +- 44,042.792426`

profile 输出摘要:

| event | calls | total_us | avg_us | pct_total |
|---|---:|---:|---:|---:|
| trgsw_mul_trlwe_DFT | 1,720,320 | 16,600,156 | 9.649 | 36.43% |
| CMUX | 1,720,320 | 42,772,639 | 24.863 | 93.86% |
| NCMUX | 15,240 | 731,596 | 48.005 | 1.61% |
| RGSW_monomial_mul | 120 | 44,103,099 | 367,525.825 | 96.78% |
| sub_a | 117 | 914,124 | 7,813.026 | 2.01% |
| sparse_mul | 3 | 45,017,465 | 15,005,821.667 | 98.78% |
| setup_tv_xb | 3 | 49,733 | 16,577.667 | 0.11% |
| sab_blind_rotate | 3 | 45,017,502 | 15,005,834.000 | 98.78% |
| sab_rlwe_bootstrap_wo_extract | 3 | 45,067,236 | 15,022,412.000 | 98.89% |
| extract_tlwe_loop | 3 | 113,906 | 37,968.667 | 0.25% |
| trlwe_full_packing_keyswitch | 3 | 389,868 | 129,956.000 | 0.86% |
| trlwe_keyswitch_hw_reduce | 3 | 817 | 272.333 | 0.00% |
| sab_rlwe_bootstrap | 3 | 45,571,828 | 15,190,609.333 | 100.00% |

## 计数核验

阶段 1 cost model:

```text
per bootstrap = (h + 1) * rho * N
              = 40 * 7 * 2048
              = 573,440
```

本次 `reps=3`，因此预期:

```text
3 * 573,440 = 1,720,320
```

profile 中 `trgsw_mul_trlwe_DFT calls = 1,720,320`，与模型完全一致。

## 初步结论

当前目标参数下，setup、extract、packing KS、HW reducing KS 不是主瓶颈。主瓶颈集中在:

- `sab_blind_rotate`
- `sparse_mul`
- `RGSW_monomial_mul`
- `CMUX` / `NCMUX`

需要注意: 纯 `trgsw_mul_trlwe_DFT` 只占完整 bootstrap 的约 36.43%。因此如果后续只替换单个 scalar external product kernel，理论收益上限有限；PVW/matrix 路线必须利用 `r` 个 lane 共享 selector schedule，在 CMUX/RGSW_monomial 层面做吞吐合并，才符合本项目的加速目标。

## 阶段 2 剩余核验

阶段 2 还不能算完整结束，剩余:

- 独立 microbench: 稳定复现 `trgsw_mul_trlwe_DFT`、CMUX、`RGSW_monomial_mul` 的单层成本。
- 多次 profiling run: 记录方差，确认比例不是偶然 run 的结果。
- 至少一个更大参数集: 例如 `SET_2_3_4096` 或 `SET_4_5_2048`，确认瓶颈结构不只存在于 `SET_2_3_2048`。

进入阶段 3 的最低条件:

- microbench 证明 external-product/CMUX 层成本稳定；
- full-run profile 继续显示 blind-rotation/CMUX/RGSW_monomial 占主导；
- `sab_pvw_*` 设计目标明确为多 lane 吞吐合并，而不是只做 scalar 函数替换。
