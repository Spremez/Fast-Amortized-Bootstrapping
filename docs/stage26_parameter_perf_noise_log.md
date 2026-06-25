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
- `SET_2_3_4096` has r=2 smoke support.

This strengthens the binary-parameter generalization story, but it is not a
broad performance claim. The evidence has one process run and one noise seed
per case, so final wording must remain smoke-level unless repeated full-SAB
A/B and multi-seed noise are added. PVW+TERNARY remains explicitly unsupported.

## Repeated r=4 Follow-up

`SET_4_5_2048` r=4 was then expanded to a small repeated gate:

| param | r | runs | correctness | PVW mean us | scalar repeated mean us | mean speedup | min speedup | max speedup |
|---|---:|---:|---|---:|---:|---:|---:|---:|
| `SET_4_5_2048` | 4 | 3 | Pass | `28571625.333` | `38872191.333` | `1.360x` | `1.352x` | `1.376x` |

Noise for the same case used 3 deterministic seeds:

| param | r | seeds | points | PVW failures | scalar failures | pair failures | min gap | max gap | avg gap |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| `SET_4_5_2048` | 4 | 3 | `24576` | 0 | 0 | 0 | `-0.082` | `0.059` | `-0.008000` |

This is stronger than the first one-run smoke for that parameter and supports a
scoped repeated-smoke claim for `SET_4_5_2048` r=4. It is still not equivalent
to the main-target 50-seed noise gate.

## Next Work

- Add repeated runs for any added parameter that appears in the final paper
  claim.
- Increase `SET_4_5_2048` r=4 noise beyond 3 seeds if the r=4 scaling claim is
  generalized beyond `SET_2_3_2048`.
- Decide whether `SET_2_3_4096` r=4 is worth the cost before running it.
