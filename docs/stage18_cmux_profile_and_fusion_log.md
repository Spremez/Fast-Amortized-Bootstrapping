# Stage 18 CMUX Profile and Fused From-DFT Add Log

Date: 2026-06-25

## Goal

Move from the Stage 14 coarse body profile to actionable CMUX/NCMUX evidence,
then test the first scratch-fusion candidate behind an explicit flag.

## Fine-Grained CMUX Profile

Added counters under `SAB_PVW_BODY_PROFILE=true`:

- `cmux_sub_us`;
- `cmux_from_dft_us`;
- `cmux_add_us`;
- `ncmux_auto_us`.

The profile gate verifies:

```text
cmux_sub_calls == cmux_from_dft_calls == cmux_add_calls == mat_ep_calls == cmux_calls
ncmux_auto_calls == ncmux_calls
```

Commands:

```bash
STAGE18_CMUX_PROFILE_RUNS=1 STAGE18_CMUX_PROFILE_R_VALUES=2 \
STAGE18_CMUX_PROFILE_OUT_DIR=repro/stage18_cmux_profile_avx512_r2_runs1 \
bash scripts/run_stage18_cmux_profile.sh

STAGE18_CMUX_PROFILE_RUNS=1 STAGE18_CMUX_PROFILE_R_VALUES=4 \
STAGE18_CMUX_PROFILE_OUT_DIR=repro/stage18_cmux_profile_avx512_r4_runs1 \
bash scripts/run_stage18_cmux_profile.sh
```

Results:

| r | CMUX us | MAT EP | sub | from_DFT | add | NCMUX auto | other |
|---:|---:|---:|---:|---:|---:|---:|---:|
| 2 | 15,768,395 | 6,217,180 | 3,139,865 | 3,908,322 | 2,380,714 | 111,222 | 122,314 |
| 4 | 28,712,828 | 12,964,028 | 4,165,040 | 7,290,486 | 4,202,202 | 168,891 | 91,072 |

Percent of CMUX time:

| r | MAT EP | sub | from_DFT | add | other |
|---:|---:|---:|---:|---:|---:|
| 2 | 39.43% | 19.91% | 24.79% | 15.10% | 0.78% |
| 4 | 45.15% | 14.51% | 25.39% | 14.64% | 0.32% |

Decision:

```text
The largest non-MAT CMUX component is from_DFT. The next candidate should
target from_DFT + add-back, not NCMUX automorphism.
```

## Fused From-DFT Add Candidate

Implemented:

```text
SAB_PVW_FUSED_FROM_DFT_ADD=true
```

The candidate replaces:

```text
pvmtmlwe_from_DFT(tmp, dft)
pvmtmlwe_add(out, tmp, in1)
```

with:

```text
pvmtmlwe_from_DFT_add(out, dft, in1)
```

when `out != in1`. The original two-step path remains the alias fallback.

Correctness gates:

| gate | command scope | status |
|---|---|---|
| staged kernel/API | `SAB_PVW_KERNEL_TEST=true` | PASS |
| target full-output | `SAB_PVW_TARGET_TEST=true` | PASS |
| default non-fused target regression | no fused flag | PASS |

Smoke results:

| r | PVW us | scalar repeated us | speedup | label |
|---:|---:|---:|---:|---|
| 2 | 16,455,557 | 19,438,748 | 1.181x | smoke only |
| 4 | 29,167,048 | 38,973,246 | 1.336x | smoke only |

Interpretation:

```text
r=2 does not improve over Stage 16 mean speedup 1.197x.
r=4 is promising versus Stage 16 mean speedup 1.281x, but it is still a
single-run smoke and must not be promoted without a three-process sweep.
```

## Fused r=4 Repeated Sweep

Command:

```bash
SAB_PVW_FUSED_FROM_DFT_ADD=true \
STAGE16_FULL_SAB_RUNS=3 STAGE16_FULL_SAB_REPS=1 \
STAGE16_FULL_SAB_R_VALUES=4 \
STAGE16_FULL_SAB_OUT_DIR=repro/stage18_fused_from_dft_add_r4_runs3_reps1 \
bash scripts/run_stage16_full_sab_audit.sh
```

Results:

| r | runs | PVW mean us | scalar repeated mean us | mean speedup | min | max | status |
|---:|---:|---:|---:|---:|---:|---:|---|
| 4 | 3 | 30,098,048.667 | 38,671,331.667 | 1.285x | 1.255x | 1.316x | PASS |

Interpretation:

```text
The fused r=4 path is correct and remains positive, but it does not materially
improve over Stage 16 r=4 mean speedup 1.281x. The observed +0.004x difference
is within normal run variability, so this candidate is neutral rather than
promotable.
```

## Decision

Stage 18 supports:

```text
[profile evidence: from_DFT is the largest non-MAT CMUX component]
[implementation exists: explicit fused from_DFT_add path]
[correctness supported for staged and target gates]
[repeated r=4 performance: neutral, not promotable]
```

Stage 18 does not support:

```text
[repeated full SAB speedup claim for fused path]
[default promotion]
[noise/security claim for fused path]
```

Next gate:

```text
Preserve fused from_DFT_add as a neutral ablation. The next optimization should
move above this local CMUX epilogue and target sparse schedule fusion or
copy/sub_a reduction.
```
