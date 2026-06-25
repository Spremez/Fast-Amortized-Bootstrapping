# Stage 24 Conditional Post-processing Tail Log

Date: 2026-06-25

## Goal

Re-measure the full-output post-processing tail after the current promoted body
path:

```text
FFT_LIB=spqlios_avx512
MAT_TRGSW_AVX512_SMALLR_SPECIALIZED=true
SAB_PVW_ACTIVE_BUFFER_FUSION=true
```

Stage 23 schedule-fused CMUX was neutral and is not part of this audit.

## Profile Boundary

`SAB_PVW_POSTPROC_PROFILE=true` measures:

```text
bootstrap_wo_extract
direct_extract
packing_ks
hw_ks
full
```

The decision metric is:

```text
tail = direct_extract + packing_ks + hw_ks
tail_pct = tail / full
```

The default Stage 24 implementation threshold is:

```text
max_tail_pct >= 2.0%
```

If the measured maximum tail stays below this threshold, a direct-to-packing KS
implementation is deferred.

## Gates

| gate | artifact | status |
|---|---|---|
| r=2 postproc profile with target correctness | `repro/stage24_postproc_tail_avx512_runs1/r2/run_0.log` | PASS |
| r=4 postproc profile with target correctness | `repro/stage24_postproc_tail_avx512_runs1/r4/run_0.log` | PASS |
| parsed sample CSV | `repro/stage24_postproc_tail_avx512_runs1/postproc_samples.csv` | PASS |
| parsed summary CSV | `repro/stage24_postproc_tail_avx512_runs1/summary.csv` | PASS |

Instrumented benchmark timing is attribution evidence only. It is not used as
a new full SAB speedup claim.

## Results

Per-run summary:

| r | samples | PVW avg us | scalar repeated avg us | smoke speedup | mean tail | max tail | decision |
|---:|---:|---:|---:|---:|---:|---:|---|
| 2 | 2 | 15231927.000 | 17847524.000 | 1.172x | 1.154563% | 1.261195% | defer |
| 4 | 2 | 26861119.000 | 38179424.000 | 1.421x | 1.057103% | 1.211048% | defer |

Per-sample tail breakdown:

| r | call | body pct | direct extract pct | packing KS pct | HW-KS pct | tail pct |
|---:|---:|---:|---:|---:|---:|---:|
| 2 | 0 | 98.738805% | 0.207554% | 1.052207% | 0.001434% | 1.261195% |
| 2 | 1 | 98.952063% | 0.084987% | 0.961979% | 0.000965% | 1.047931% |
| 4 | 0 | 98.788944% | 0.280326% | 0.929529% | 0.001193% | 1.211048% |
| 4 | 1 | 99.096838% | 0.060295% | 0.841962% | 0.000901% | 0.903158% |

Across all four samples:

```text
mean tail_pct = 1.105833%
max tail_pct = 1.261195%
mean packing_pct = 0.946419%
max packing_pct = 1.052207%
mean direct_extract_pct = 0.158291%
```

## Decision

Stage 24 is deferred.

Supported:

```text
[tail profile supported] Post-processing is measurable but small under the
current active-buffer plus specialized MAT-AVX512 path.
```

Not supported:

```text
[implementation not justified] A direct-to-packing KS or batched extract path
is not worth implementing now because the maximum observed post-processing tail
is only 1.261%, below the 2.0% implementation threshold.
```

Next stage:

```text
Proceed to Stage 25 correctness/noise/resource matrix for the current best
explicit path: MAT_TRGSW_AVX512_SMALLR_SPECIALIZED=true plus
SAB_PVW_ACTIVE_BUFFER_FUSION=true.
```
