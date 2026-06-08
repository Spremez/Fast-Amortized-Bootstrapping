# Stage 2 Measurements

Date: 2026-06-08

This file records the second Stage 2 pass after the initial
`docs/profile_baseline.md` run. The goal is to decide whether the next
implementation stage should target the SAB external-product/CMUX/RGSW hot path.

## New Build Switch

`SAB_MICROBENCH=true` selects a standalone SAB microbenchmark in `main.c`.
It is disabled by default.

Recommended profiling microbench command:

```bash
make -B FFT_LIB=spqlios A_PRNG=none ENABLE_VAES=false \
  PARAM=SET_2_3_2048 SAB_PROFILE=true SAB_MICROBENCH=true
timeout 180s ./main
```

## Microbench: SET_2_3_2048 Shape

Shape:

- `N=2048`
- `h=39`
- `rho=7`
- `l=1`
- `Bg_bit=23`
- `external_product reps=2000`
- `CMUX reps=2000`
- `RGSW_monomial_mul reps=5`
- rejection sampling attempts: 182

Results:

| bench | calls | total_us | avg_us | timing output |
|---|---:|---:|---:|---|
| `trgsw_mul_trlwe_DFT` | 2,000 | 19,677 | 9.838 | `9 us +- 3.294769` |
| `CMUX` | 2,000 | 37,774 | 18.887 | `18 us +- 7.211969` |
| `RGSW_monomial_mul` | 5 | 2,100,764 | 420,152.800 | `420,155 us +- 48,057.933060` |

Nested counts from the `RGSW_monomial_mul` microbench:

| nested event | calls | avg_us |
|---|---:|---:|
| `trgsw_mul_trlwe_DFT` | 71,680 | 11.129 |
| `CMUX` | 71,680 | 28.487 |
| `NCMUX` | 635 | 50.726 |

Count checks:

```text
RGSW_monomial_mul external products:
5 * rho * N = 5 * 7 * 2048 = 71,680

RGSW_monomial_mul NCMUX calls:
5 * (1 + 2 + 4 + 8 + 16 + 32 + 64) = 635
```

The microbench confirms that the local cost is not only the raw
`trgsw_mul_trlwe_DFT` kernel. The surrounding CMUX work roughly doubles the
raw external-product time in this run, and the full monomial layer is the
dominant repeated unit.

## Full Run: SET_2_3_4096 Binary

Command:

```bash
make -B FFT_LIB=spqlios A_PRNG=none ENABLE_VAES=false \
  PARAM=SET_2_3_4096 SAB_PROFILE=true SAB_MICROBENCH=false
timeout 360s ./main
```

Result: `Pass`

Shape:

- `N=4096`
- `h=32`
- `rho=8`
- `reps=3`
- rejection sampling attempts: 2367
- benchmark output: `Bootstrapping time: 29,366,720 us +- 1,791,619.096051`

Profile summary:

| event | calls | total_us | avg_us | pct_total |
|---|---:|---:|---:|---:|
| `trgsw_mul_trlwe_DFT` | 3,244,032 | 33,251,393 | 10.250 | 37.74% |
| `CMUX` | 3,244,032 | 85,178,054 | 26.257 | 96.68% |
| `NCMUX` | 25,245 | 1,210,447 | 47.948 | 1.37% |
| `RGSW_monomial_mul` | 99 | 85,949,892 | 868,180.727 | 97.56% |
| `sub_a` | 96 | 1,533,971 | 15,978.865 | 1.74% |
| `sparse_mul` | 3 | 87,484,100 | 29,161,366.667 | 99.30% |
| `setup_tv_xb` | 3 | 74,687 | 24,895.667 | 0.08% |
| `sab_blind_rotate` | 3 | 87,484,199 | 29,161,399.667 | 99.30% |
| `sab_rlwe_bootstrap_wo_extract` | 3 | 87,558,887 | 29,186,295.667 | 99.39% |
| `extract_tlwe_loop` | 3 | 52,926 | 17,642.000 | 0.06% |
| `trlwe_full_packing_keyswitch` | 3 | 487,526 | 162,508.667 | 0.55% |
| `trlwe_keyswitch_hw_reduce` | 3 | 795 | 265.000 | 0.00% |
| `sab_rlwe_bootstrap` | 3 | 88,100,137 | 29,366,712.333 | 100.00% |

Count check:

```text
per bootstrap = (h + 1) * rho * N
              = 33 * 8 * 4096
              = 1,081,344

3 repetitions = 3,244,032
```

The observed `trgsw_mul_trlwe_DFT` call count is exactly `3,244,032`.

## Stage 2 Decision

The Stage 2 decision is now strong enough to proceed to Stage 3:

- Full-run profiles for `SET_2_3_2048` and `SET_2_3_4096` both show that
  `sab_blind_rotate`, `sparse_mul`, `RGSW_monomial_mul`, and `CMUX` dominate.
- Setup, extract, packing KS, and final KS are not the primary bottleneck on
  the WSL/Linux `spqlios` path.
- Raw `trgsw_mul_trlwe_DFT` is important but not sufficient as a standalone
  target: it is about 36-38% of full bootstrap time in these two runs, while
  CMUX/RGSW inclusive time is above 96%.

Implementation implication:

`sab_pvw_*` should batch lane work at the CMUX/RGSW layer, not only replace the
scalar external-product function. This matches the selected `r = multi LUT /
multi SAB lane` interpretation.
