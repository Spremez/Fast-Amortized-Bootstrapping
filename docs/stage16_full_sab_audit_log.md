# Stage 16 Full SAB AVX512 Audit Log

Date: 2026-06-25

## Goal

Turn the Stage 15 full SAB AVX512 MAT smoke results into repeated
complete-bootstrapping evidence.

The audited variant is:

```text
FFT_LIB=spqlios_avx512
MAT_TRGSW_AVX512_SMALLR_SPECIALIZED=true
KEY=BINARY
PARAM=SET_2_3_2048
r in {2,4}
```

## Command

```bash
STAGE16_FULL_SAB_RUNS=3 STAGE16_FULL_SAB_REPS=1 \
STAGE16_FULL_SAB_OUT_DIR=repro/stage16_avx512_full_sab_audit_runs3_reps1 \
bash scripts/run_stage16_full_sab_audit.sh
```

## Audit Gates

Correctness:

```text
Every process run must pass SAB_PVW_BENCH correctness target_full.
```

Performance:

```text
Every process run must have speedup > 1.0x.
Mean speedup must be >= 1.10x for the variant to remain promotable.
```

Claim boundary:

```text
The comparator is repeated scalar SAB in the same spqlios_avx512 binary.
This stage does not compare against a different backend as the primary claim.
```

## Results

Aggregate:

| r | runs | PVW mean us | scalar repeated mean us | mean speedup | min | max | status |
|---:|---:|---:|---:|---:|---:|---:|---|
| 2 | 3 | 16,122,491.667 | 19,301,498.333 | 1.197x | 1.155x | 1.248x | PASS |
| 4 | 3 | 31,004,970.000 | 39,674,916.333 | 1.281x | 1.231x | 1.324x | PASS |

Per-run r=2:

| run | PVW us | scalar repeated us | speedup |
|---:|---:|---:|---:|
| 0 | 15,840,098 | 19,776,267 | 1.248x |
| 1 | 16,163,639 | 19,220,208 | 1.189x |
| 2 | 16,363,738 | 18,908,020 | 1.155x |

Per-run r=4:

| run | PVW us | scalar repeated us | speedup |
|---:|---:|---:|---:|
| 0 | 29,787,924 | 39,427,857 | 1.324x |
| 1 | 32,529,288 | 40,031,536 | 1.231x |
| 2 | 30,697,698 | 39,565,356 | 1.289x |

## Decision

Stage 16 passes the repeated full SAB audit for the scoped AVX512 MAT variant:

```text
[correctness supported]
[same-backend complete-SAB throughput supported]
```

The supported claim is deliberately narrow:

```text
Under spqlios_avx512 with MAT_TRGSW_AVX512_SMALLR_SPECIALIZED=true,
complete PVW/MAT-SAB is faster than repeated scalar SAB on BINARY
SET_2_3_2048 for r=2 and r=4.
```

The unsupported claims remain:

```text
Not a multi-fold SAB speedup.
Not proof that AVX512 MAT should be enabled by default.
Not proof that the current dense MAT formulation has reached the final
algorithmic limit.
Not broader than BINARY SET_2_3_2048.
```

Comparison to earlier accepted engineering evidence:

```text
Stage 10/Stage 8 spqlios clear-elision evidence remains stronger for the
existing paper-level engineering claim:
r=2 1.269x, r=4 1.337x with 50-seed correctness/noise evidence.

Stage 16 AVX512 evidence is positive and repeated, but its speedups
r=2 1.197x and r=4 1.281x are lower than the accepted spqlios clear-elision
numbers. Therefore Stage 16 supports backend-specific completeness of the
AVX512 MAT path, not a new top-line speedup claim.
```

## Next Stage

Proceed to Stage 17:

```text
Perf-counter, objdump, and phase-counter audit to decide whether the next
optimization should target MAT arithmetic, CMUX wrapper/scratch traffic, or
sparse schedule fusion.
```
