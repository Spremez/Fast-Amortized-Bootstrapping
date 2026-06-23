# Stage 13 PVW Post-processing Profile Log

Date: 2026-06-23

## Codex Goal

Advance the PVW/MAT-SAB optimization loop beyond MAT-only tuning by measuring
and reducing the full-output post-processing tail:

```text
bootstrap_wo_extract -> extract/materialize TLWE lanes -> packing KS -> HW-KS
```

The scalar SAB path and the Stage 10 clear-elision PVW/MAT-SAB result must stay
runnable. Any performance statement from this stage is smoke-level unless it
uses repeated process runs.

## Direct Lane Extraction Variant

Old full-output PVW SAB post-processing:

```text
sab_pvw_bootstrap_wo_extract_binary(acc, in, tv)
sab_pvw_extract_pvwtlwe(extracted, acc)       // shared mask + r bodies
for lane in 0..r-1:
  for idx in 0..in_N-1:
    lane_extracted[lane][idx].a = extracted[idx].a
    lane_extracted[lane][idx].b = extracted[idx].b[lane]
  trlwe_full_packing_keyswitch(...)
  trlwe_keyswitch(...)
```

New full-output path:

```text
sab_pvw_bootstrap_wo_extract_binary(acc, in, tv)
for lane in 0..r-1:
  for idx in 0..in_N-1:
    lane_extracted[lane][idx] = extract coefficient 0 from acc[idx] body lane
  trlwe_full_packing_keyswitch(...)
  trlwe_keyswitch(...)
```

The important invariant is that each `acc[idx]` is extracted at coefficient
`0`. The array index `idx` is not the extraction index. An initial direct
implementation used `idx` as the extraction coefficient and failed the staged
full-output check; that failure log is preserved.

This variant removes the intermediate `PVW_TLWE` write/read pass from the hot
full-output path. It does not change packing KS or HW-KS complexity.

## New Repro Tooling

`SAB_PVW_POSTPROC_PROFILE=true` prints one timing line for every
`sab_pvw_bootstrap_binary()` call:

```text
SAB_PVW_POSTPROC_PROFILE sample lanes=...
  bootstrap_wo_extract_us=...
  direct_extract_us=...
  packing_ks_us=...
  hw_ks_us=...
  full_us=...
```

The wrapper script is:

```text
scripts/run_stage13_postproc_profile.sh
```

It records raw logs plus:

- `postproc_profile.csv`
- `bench_summary.csv`

## Correctness Gates

| gate | backend | status | artifact |
|---|---|---:|---|
| initial direct extraction staged gate | `spqlios` | FAIL | `repro/stage13_kernel_spqlios_direct_extract.log` |
| fixed direct extraction staged gate | `spqlios` | PASS | `repro/stage13_kernel_spqlios_direct_extract_fixed.log` |
| fixed direct extraction target full gate | `spqlios` | PASS | `repro/stage13_target_full_spqlios_direct_extract.log` |

The failure was caused by the wrong extraction coefficient and was fixed before
any performance interpretation.

## Profile Results

Profiled one-run calls with `FFT_LIB=spqlios`, `KEY=BINARY`,
`PARAM=SET_2_3_2048`, and `SAB_PVW_BENCH_REPS=1`.

Timed-call profile:

| r | full us | bootstrap_wo_extract us | direct_extract us | packing_ks us | hw_ks us |
|---:|---:|---:|---:|---:|---:|
| 2 | 24,260,660 | 24,029,081 | 15,097 | 216,192 | 290 |
| 4 | 43,988,199 | 43,336,910 | 167,309 | 483,378 | 601 |

Percent of full call:

| r | bootstrap_wo_extract | direct_extract | packing_ks | hw_ks |
|---:|---:|---:|---:|---:|
| 2 | 99.045% | 0.062% | 0.891% | 0.001% |
| 4 | 98.519% | 0.380% | 1.099% | 0.001% |

Interpretation:

```text
Direct extraction removes an unnecessary intermediate PVW_TLWE pass, but the
measured full-output post-processing tail is not the dominant full SAB cost at
the current target shape. Packing KS is visible but still about 1% of the full
PVW call in these smokes. The main optimization target remains the
bootstrap_wo_extract / sparse blind-rotation body.
```

## Full SAB Smoke

Unprofiled one-run smokes:

| r | PVW us | scalar repeated us | speedup | status |
|---:|---:|---:|---:|---|
| 2 | 21,479,066 | 32,446,940 | 1.511x | smoke only |
| 4 | 50,504,921 | 66,543,945 | 1.318x | smoke only |

Stats sanity label:

```text
[engineering smoke only]
```

These one-run values confirm the path is runnable and positive in this run, but
they do not replace the Stage 10 accepted three-run clear-elision evidence.

## Next Decision

Direct lane extraction should stay because it is simpler in the full-output
path and avoids needless intermediate storage. It is not enough to create a
new multi-fold SAB acceleration claim.

Next high-value work:

1. Design a `trlwe_full_packing_keyswitch` variant that reads directly from
   `PVW_TMLWE` lane bodies and generated extraction masks, only if the expected
   1% tail reduction is worth the code complexity.
2. Prioritize SAB-specific sparse/fused variants around
   `RGSW_monomial_mul`, `CMUX/NCMUX`, and `sparse_mul`, because profile data
   shows those dominate full runtime.
3. Use three process runs before promoting any speedup beyond smoke evidence.
