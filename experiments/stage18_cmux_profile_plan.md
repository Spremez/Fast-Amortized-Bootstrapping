# Stage 18 CMUX Profile Plan

Date: 2026-06-25

## Objective

Before implementing scratch-aware CMUX/NCMUX fusion, split the Stage 14
`CMUX minus MAT EP` bucket into directly actionable pieces.

The current CMUX sequence is:

```text
pvmtmlwe_sub
mat_trgsw_mul_pvmtmlwe_DFT
pvmtmlwe_from_DFT
pvmtmlwe_add
```

NCMUX adds:

```text
pvmtmlwe_eval_automorphism
CMUX
```

## Added Counters

Under `SAB_PVW_BODY_PROFILE=true`, Stage 18 records:

- `cmux_sub_us`;
- `cmux_from_dft_us`;
- `cmux_add_us`;
- `ncmux_auto_us`;
- existing `mat_ep_us`, `cmux_us`, `ncmux_us`, `sub_a_us`, and `copyback_us`.

## Gates

Correctness:

- the profile build must pass `SAB_PVW_BENCH correctness target_full`.

Profile integrity:

- `cmux_sub_calls`, `cmux_from_dft_calls`, `cmux_add_calls`, and
  `mat_ep_calls` must equal `cmux_calls`;
- `ncmux_auto_calls` must equal `ncmux_calls`.

Decision:

- if `from_DFT` dominates the non-MAT cost, Stage 18 implementation should
  prioritize fusing inverse DFT/output conversion with add-back;
- if `sub/add` dominates, prioritize scratch and in-place arithmetic;
- if `ncmux_auto` dominates, prioritize automorphism-to-CMUX scratch handoff;
- if none dominates, move to Stage 19 sparse schedule fusion.

## Repro Command

```bash
STAGE18_CMUX_PROFILE_RUNS=1 \
STAGE18_CMUX_PROFILE_R_VALUES="2 4" \
STAGE18_CMUX_PROFILE_OUT_DIR=repro/stage18_cmux_profile_avx512_runs1 \
bash scripts/run_stage18_cmux_profile.sh
```
