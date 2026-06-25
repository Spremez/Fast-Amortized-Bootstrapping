# Stage 21 sub_a Output-Fusion Validation Plan

Date: 2026-06-25

## Objective

Use the inactive active-buffer accumulator as the direct output of `sub_a`
rotation, eliminating the current per-sample `tmp -> active` copy inside
`sab_pvw_sub_a_binary`.

## Flags

```text
SAB_PVW_ACTIVE_BUFFER_FUSION=true
SAB_PVW_SUBA_OUTPUT_FUSION=true
```

The sub_a output-fusion flag is meaningful only with active-buffer fusion.
Default scalar SAB, default PVW SAB, and Stage 20 active-buffer baseline remain
separate paths.

## Expected Target Effect

For `BINARY SET_2_3_2048`:

```text
h = 39
r_prec = 7
sub_a calls = 39
sub_a output-fusion calls = 39
Stage 20 final copyback = 0
Stage 21 final copyback = 1
```

The extra final copyback is expected because the 39 direct-output sub_a steps
flip active parity. The intended benefit is removing 39 full accumulator-array
copies inside `sub_a`.

## Correctness Gate

```bash
make clean && make FFT_LIB=spqlios_avx512 \
  MAT_TRGSW_AVX512_SMALLR_SPECIALIZED=true \
  SAB_PVW_ACTIVE_BUFFER_FUSION=true \
  SAB_PVW_SUBA_OUTPUT_FUSION=true \
  SAB_PVW_TARGET_TEST=true KEY=BINARY PARAM=SET_2_3_2048 -j$(nproc) && ./main
```

## Profile Gate

```bash
STAGE21_SUBA_PROFILE_RUNS=1 \
STAGE21_SUBA_PROFILE_R_VALUES="2 4" \
STAGE21_SUBA_PROFILE_OUT_DIR=repro/stage21_suba_output_profile_avx512_runs1 \
bash scripts/run_stage21_suba_output_profile.sh
```

The profile gate must confirm:

- `sub_a_calls == 39`;
- `sub_a_output_fusion_calls == 39`;
- `copyback_calls == 1`;
- CMUX/MAT EP/NCMUX counts remain equal to the Stage 20 schedule.

## Performance Gate

- one-run full SAB smoke for r=2 and r=4;
- three-process full SAB sweep only if smoke suggests improvement over Stage
  20;
- if full SAB is neutral or negative, preserve as an ablation and keep Stage 20
  as the comparison baseline.
