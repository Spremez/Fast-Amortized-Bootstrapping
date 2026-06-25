# Stage 26 Parameter Performance/Noise Log

Date: 2026-06-25

## Goal

Move Stage 26 from binary target correctness smoke toward parameter
generalization by adding complete-SAB performance and final-output noise smoke
for additional binary parameters.

## Script

Added:

```text
scripts/run_stage26_parameter_perf_noise.sh
```

The script reuses the existing Stage 20 active-buffer full-SAB benchmark and
Stage 25 final-output noise sweep. It writes per-case summaries and aggregate
CSV files under a caller-selected `repro/` directory.

The first r=2 invocation completed the raw performance/noise gates but failed
at the final summary step because WSL exposed `python3` rather than `python`.
The script now uses `${PYTHON:-python3}`, and the r=2 summaries were rebuilt
from the already generated raw CSV artifacts. The r=4 invocation completed
end-to-end with the fixed script.

## Commands

```sh
bash -lc "STAGE26_PERF_RUNS=1 STAGE26_NOISE_SEED_COUNT=1 STAGE26_PERF_NOISE_R_VALUES=2 STAGE26_PERF_NOISE_PARAMS='SET_4_5_2048 SET_2_3_4096' STAGE26_PERF_NOISE_OUT_DIR=repro/stage26_parameter_perf_noise_avx512_added_r2_smoke bash scripts/run_stage26_parameter_perf_noise.sh"
```

```sh
bash -lc "STAGE26_PERF_RUNS=1 STAGE26_NOISE_SEED_COUNT=1 STAGE26_PERF_NOISE_R_VALUES=4 STAGE26_PERF_NOISE_PARAMS='SET_4_5_2048' STAGE26_PERF_NOISE_OUT_DIR=repro/stage26_parameter_perf_noise_avx512_set_4_5_2048_r4_smoke bash scripts/run_stage26_parameter_perf_noise.sh"
```

## Performance Smoke

| param | r | runs | correctness | PVW mean us | scalar repeated mean us | speedup | decision |
|---|---:|---:|---|---:|---:|---:|---|
| `SET_4_5_2048` | 2 | 1 | Pass | `15749718.000` | `20636153.000` | `1.310x` | positive smoke |
| `SET_2_3_4096` | 2 | 1 | Pass | `27217323.000` | `34057297.000` | `1.251x` | positive smoke |
| `SET_4_5_2048` | 4 | 1 | Pass | `27891598.000` | `40071936.000` | `1.437x` | positive smoke |

## Final-Output Noise Smoke

| param | r | seeds | points | PVW failures | scalar failures | pair failures | PVW-minus-scalar log2 | status |
|---|---:|---:|---:|---:|---:|---:|---:|---|
| `SET_4_5_2048` | 2 | 1 | `4096` | 0 | 0 | 0 | `-0.151` | Pass |
| `SET_2_3_4096` | 2 | 1 | `8192` | 0 | 0 | 0 | `0.014` | Pass |
| `SET_4_5_2048` | 4 | 1 | `8192` | 0 | 0 | 0 | `0.059` | Pass |

## Interpretation

The added binary parameters now have initial performance/noise smoke beyond
target correctness:

- `SET_4_5_2048` has r=2 and r=4 smoke support.
- `SET_2_3_4096` has r=2 and r=4 smoke support.

This strengthens the binary-parameter generalization story, but it is not a
broad performance claim. The evidence has one process run and one noise seed
per case, so final wording must remain smoke-level unless repeated full-SAB
A/B and multi-seed noise are added. PVW+TERNARY remains explicitly unsupported.

## Repeated r=4 Follow-up

`SET_4_5_2048` r=4 and `SET_2_3_4096` r=4 were then expanded to small repeated
gates:

| param | r | runs | correctness | PVW mean us | scalar repeated mean us | mean speedup | min speedup | max speedup |
|---|---:|---:|---|---:|---:|---:|---:|---:|
| `SET_4_5_2048` | 4 | 3 | Pass | `28571625.333` | `38872191.333` | `1.360x` | `1.352x` | `1.376x` |
| `SET_2_3_4096` | 4 | 3 | Pass | `50609387.333` | `66607445.000` | `1.317x` | `1.270x` | `1.346x` |

Noise for the same case used 3 deterministic seeds:

| param | r | seeds | points | PVW failures | scalar failures | pair failures | min gap | max gap | avg gap |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| `SET_4_5_2048` | 4 | 3 | `24576` | 0 | 0 | 0 | `-0.082` | `0.059` | `-0.008000` |
| `SET_2_3_4096` | 4 | 3 | `49152` | 0 | 0 | 0 | `-0.117` | `0.280` | `0.085000` |

This is stronger than the first one-run smoke for that parameter and supports a
scoped repeated-smoke claim for `SET_4_5_2048` r=4 and `SET_2_3_4096` r=4. It
is still not equivalent to the main-target 50-seed noise gate.

## Repeated r=2 Follow-up

The added-parameter r=2 cases were also expanded to 3-run/3-seed repeated
smoke gates:

| param | r | runs | correctness | PVW mean us | scalar repeated mean us | mean speedup | min speedup | max speedup |
|---|---:|---:|---|---:|---:|---:|---:|---:|
| `SET_4_5_2048` | 2 | 3 | Pass | `15246375.667` | `18744766.333` | `1.238x` | `1.086x` | `1.434x` |
| `SET_2_3_4096` | 2 | 3 | Pass | `26769817.000` | `32847150.333` | `1.227x` | `1.219x` | `1.235x` |

Noise for the same r=2 cases used 3 deterministic seeds:

| param | r | seeds | points | PVW failures | scalar failures | pair failures | min gap | max gap | avg gap |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| `SET_4_5_2048` | 2 | 3 | `12288` | 0 | 0 | 0 | `-0.175` | `0.464` | `0.046000` |
| `SET_2_3_4096` | 2 | 3 | `24576` | 0 | 0 | 0 | `-0.172` | `0.014` | `-0.093000` |

Together with the r=4 follow-up above, the added binary parameters now have
3-run/3-seed repeated-smoke evidence for r=2 and r=4. This supports scoped
binary parameter repeated-smoke language, but it is still below the target
parameter's 50-seed final-output noise gate and should not be described as a
broad statistical claim.

## 5-Run/5-Seed Added-Binary Expansion

The added binary parameters were then consolidated into a single r=2/r=4
matrix with 5 full-SAB A/B runs and 5 final-output noise seeds per case:

```sh
bash -lc "STAGE26_PERF_RUNS=5 STAGE26_NOISE_SEED_COUNT=5 STAGE26_PERF_NOISE_R_VALUES='2 4' STAGE26_PERF_NOISE_PARAMS='SET_4_5_2048 SET_2_3_4096' STAGE26_PERF_NOISE_OUT_DIR=repro/stage26_parameter_perf_noise_avx512_added_binary_r2_r4_runs5_seeds5 bash scripts/run_stage26_parameter_perf_noise.sh"
```

Performance:

| param | r | runs | correctness | PVW mean us | scalar repeated mean us | mean speedup | min speedup | max speedup |
|---|---:|---:|---|---:|---:|---:|---:|---:|
| `SET_4_5_2048` | 2 | 5 | Pass | `14731630.200` | `19438672.400` | `1.329x` | `1.082x` | `1.473x` |
| `SET_4_5_2048` | 4 | 5 | Pass | `28681374.000` | `38560527.200` | `1.346x` | `1.305x` | `1.455x` |
| `SET_2_3_4096` | 2 | 5 | Pass | `26922941.200` | `32955929.400` | `1.224x` | `1.207x` | `1.233x` |
| `SET_2_3_4096` | 4 | 5 | Pass | `50153785.800` | `66084384.600` | `1.318x` | `1.272x` | `1.350x` |

Small-sample speedup dispersion:

| param | r | speedup stddev | 95% CI half-width, t(df=4) | interpretation |
|---|---:|---:|---:|---|
| `SET_4_5_2048` | 2 | `0.173682` | `0.215620` | positive mean, high run-to-run variance |
| `SET_4_5_2048` | 4 | `0.062496` | `0.077586` | positive small-sample support |
| `SET_2_3_4096` | 2 | `0.011389` | `0.014139` | stable positive small-sample support |
| `SET_2_3_4096` | 4 | `0.031675` | `0.039323` | stable positive small-sample support |

Noise:

| param | r | seeds | points | PVW failures | scalar failures | pair failures | min gap | max gap | avg gap |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| `SET_4_5_2048` | 2 | 5 | `20480` | 0 | 0 | 0 | `-0.196` | `0.464` | `0.025400` |
| `SET_4_5_2048` | 4 | 5 | `40960` | 0 | 0 | 0 | `-0.183` | `0.059` | `-0.048400` |
| `SET_2_3_4096` | 2 | 5 | `40960` | 0 | 0 | 0 | `-0.308` | `0.014` | `-0.177600` |
| `SET_2_3_4096` | 4 | 5 | `81920` | 0 | 0 | 0 | `-0.299` | `0.414` | `0.074000` |

This improves Stage 26 from 3-run/3-seed repeated-smoke to 5-run/5-seed
small-sample support for the two added binary parameters and r=2/r=4. It still
does not match the main target's 50-seed final-output noise gate. In final
paper wording, `SET_4_5_2048` r=2 should be reported with its high variance
rather than only its mean.

## Next Work

- Increase added-parameter r=2/r=4 noise and performance repetitions beyond
  5 seeds/runs if these parameters appear in a broad final paper claim.
- Decide whether Stage 26 should stay as parameter repeated-smoke support or be
  promoted to a larger statistical campaign.
- Keep PVW+TERNARY out of scope unless a separate implementation and gate are
  added.
