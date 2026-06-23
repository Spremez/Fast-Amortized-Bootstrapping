# Variant: PVW SAB Direct Lane Extraction

Date: 2026-06-23

## Objective

Remove the intermediate `PVW_TLWE` materialization pass from full-output
`sab_pvw_bootstrap_binary()` while preserving the scalar SAB baseline and the
public `sab_pvw_extract_pvwtlwe()` API used by staged tests.

## Algorithm Delta

Previous full-output post-processing:

```text
for idx in 0..in_N-1:
  extracted[idx] = PVW_TLWE_extract(acc[idx], coeff=0)
for lane in 0..r-1:
  for idx in 0..in_N-1:
    TLWE_lane[idx].a = extracted[idx].a
    TLWE_lane[idx].b = extracted[idx].b[lane]
  packing KS
  HW-KS
```

Direct lane extraction:

```text
for lane in 0..r-1:
  for idx in 0..in_N-1:
    TLWE_lane[idx].a[j] = extracted mask from acc[idx] at coeff=0
    TLWE_lane[idx].b = acc[idx].b[lane][0]
  packing KS
  HW-KS
```

The extracted coefficient is always `0` for each accumulator sample. The
accumulator-array index is not a TLWE extraction coefficient.

## Complexity

Asymptotic complexity is unchanged:

```text
O(r * in_N * out_N) TLWE lane materialization
+ O(r * packing KS)
+ O(r * HW-KS)
```

The constant-factor reduction is the removed intermediate `PVW_TLWE` array
write/read. Packing KS still requires a per-lane `TLWE *` input array in the
current MOSFHET API, so this variant does not remove the per-lane tail.

## Evidence

| gate | status | artifact |
|---|---:|---|
| initial staged gate with wrong extraction coefficient | FAIL | `repro/stage13_kernel_spqlios_direct_extract.log` |
| fixed staged gate | PASS | `repro/stage13_kernel_spqlios_direct_extract_fixed.log` |
| target full correctness | PASS | `repro/stage13_target_full_spqlios_direct_extract.log` |
| r=2 profile smoke | PASS | `repro/stage13_postproc_profile_r2_reps1_runs1/postproc_profile.csv` |
| r=4 profile smoke | PASS | `repro/stage13_postproc_profile_r4_reps1_runs1/postproc_profile.csv` |
| r=2 full SAB smoke | PASS | `repro/stage13_direct_extract_bench_r2_reps1_runs1/summary.csv` |
| r=4 full SAB smoke | PASS | `repro/stage13_direct_extract_bench_r4_reps1_runs1/summary.csv` |

## Decision

Accept as a low-risk implementation cleanup and profiling enabler. Do not claim
it as a standalone full SAB speedup result without repeated process-level
benchmarks.

The profile evidence says the next algorithmic effort should target the
`bootstrap_wo_extract` body, not extraction alone.
