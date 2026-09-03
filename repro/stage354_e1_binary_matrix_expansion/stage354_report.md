# Stage354 Report: E1 Binary Parameter-Matrix Expansion

Date: 2026-08-19/20
Driver: `scripts/run_stage354_e1_binary_matrix_expansion.sh` (protocol identical
to Stage340: same build flags, 10 perf runs per row, 10-trial target-noise run
under `/usr/bin/time -v`; r=2 tail runs launched inline with correctness and
noise-gate checks).
Parser: `scripts/build_stage354_summary.py` → `stage354_summary.csv`.
Platform: WSL2, 16 cores, 12 GB (raised from the ~7 GB default via
`C:\Users\spremez\.wslconfig`; see the resource-bound note below).
Backend: `spqlios_avx512`, binary keys, include-zero mode.

## Decision

`PASS_STAGE354_E1_EXPANSION_3_PLUS_1_ROWS_ONE_ROW_RESOURCE_BOUND`

## Results (all rows: 10 samples, correctness Pass, noise gate Pass, 0/10 pair failures)

| case | T_bootstrap/r speedup vs repeated scalar (mean) | per-run range | peak RSS |
|---|---:|---:|---:|
| SET_4_5_4096 r=2 | **1.6115×** | 1.512–1.767 | 2,350,152 KB |
| SET_4_5_4096 r=4 | **1.6507×** | 1.607–1.700 | 4,581,880 KB |
| SET_6_7_4096 r=4 (Boot6-aligned: n=4096, h=33) | **1.6461×** | 1.617–1.684 | 4,648,368 KB |
| SET_8_9_4096 r=2 (Boot8-aligned: n=4096, h=34) | **1.5693×** | 1.500–1.618 | 9,343,840 KB |

Combined with the Stage345 six-row matrix, the supported binary include-zero
range is now **1.5693×–1.7476×** over ten rows.

## Resource-bound row

`SET_8_9_4096 r=4` (out_N=8192) is memory-bound on this platform: the process
was OOM-killed at anon-RSS 7.51 GB under the 7 GB default and again at
11.73 GB (total-vm 18.5 GB) under the raised 12 GB budget
(`dmesg`: `Out of memory: Killed process ... (main)`). r=2 at the same
parameter set peaks at 9.34 GB and completes. A ≥16 GB-class machine is
required for the r=4 row; this bound is itself evidence for the paper's
resource matrix.

## Noise detail (final rows)

- SET_6_7_4096 r=4: points=163,840; pair_log2_sigma −10.224 vs model −2.287.
- SET_8_9_4096 r=2: points=81,920; pair_log2_sigma −13.913 vs model −2.292.

Both hold the Stage331-style margin (pair noise far below the model bound),
with 0 pair failures.

## Claim boundaries

- Metric: complete-SAB `T_bootstrap/r` vs repeated scalar SAB, same backend
  and flags — not single-call latency, not an external-baseline comparison.
- BatchBoot (USENIX Sec'26) reports 2.2×/2.4×/1.05×/2.27× over the same
  scalar line at 2/4/6/8-bit on different hardware; the Boot6/Boot8-aligned
  rows above are NOT a head-to-head (no shared machine; BatchBoot has no
  public artifact). See roadmap E0 for the reproduction plan.
- The 8-bit row (1.5693×) narrows the MAT advantage at the highest tested
  precision — consistent with BatchBoot's own 6-bit saturation observation
  (1.05×) being a different mechanism, but requiring the F1/D3 paths to close
  the gap at high precision.

## Reproduction

```sh
# full driver (4 rows; SET_8_9_4096_r4 requires >=16 GB)
STAGE354_PERF_RUNS=10 STAGE354_NOISE_TRIALS=10 \
  bash scripts/run_stage354_e1_binary_matrix_expansion.sh
# summary
python scripts/build_stage354_summary.py
```

Raw logs: `raw/<case>/{perf,noise}/`; driver log `raw/driver.log`
(git head recorded in `raw/run_git_head.txt`).
