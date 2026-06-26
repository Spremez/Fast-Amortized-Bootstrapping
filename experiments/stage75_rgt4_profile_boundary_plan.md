# Stage75 R>4 Profile Boundary Plan

Date: 2026-06-26

## Goal

Diagnose the Stage74 r>4 lane-scaling boundary with exact SAB body-profile
evidence. The purpose is to decide whether direct r=6/r=8 underperformance is
caused by a schedule/count mismatch or by per-update MAT/body cost growth.

## Hypothesis

For `BINARY SET_2_3_2048`, the SAB schedule should remain invariant as r
changes:

```text
rgsw_monomial_calls = h + 1 = 40
cmux/mat_ep calls   = 40 * r_prec * in_N = 40 * 7 * 2048 = 573440
ncmux calls         = 40 * (2^7 - 1) = 5080
sub_a calls         = h = 39
copyback calls      = 0 with active-buffer fusion
```

If those counts hold for r=6/r=8, then the Stage74 boundary should be
attributed to dense MAT body cost, generic large-r loops, cache traffic, and
register pressure rather than to an accidental extra SAB schedule.

## Commands

The WSL/PowerShell quoting path misparsed a space-separated r list, so r=6 and
r=8 are run as separate profile jobs:

```bash
STAGE20_ACTIVE_PROFILE_R_VALUES=6 \
STAGE20_ACTIVE_PROFILE_RUNS=1 \
SAB_PVW_BENCH_REPS=1 \
STAGE20_ACTIVE_PROFILE_OUT_DIR=repro/stage75_rgt4_profile_boundary/body_profile_r6 \
FFT_LIB=spqlios_avx512 \
MAT_TRGSW_AVX512_SMALLR_SPECIALIZED=true \
SAB_PVW_ACTIVE_BUFFER_FUSION=true \
JOBS=$(nproc) \
bash scripts/run_stage20_active_buffer_profile.sh

STAGE20_ACTIVE_PROFILE_R_VALUES=8 \
STAGE20_ACTIVE_PROFILE_RUNS=1 \
SAB_PVW_BENCH_REPS=1 \
STAGE20_ACTIVE_PROFILE_OUT_DIR=repro/stage75_rgt4_profile_boundary/body_profile_r8 \
FFT_LIB=spqlios_avx512 \
MAT_TRGSW_AVX512_SMALLR_SPECIALIZED=true \
SAB_PVW_ACTIVE_BUFFER_FUSION=true \
JOBS=$(nproc) \
bash scripts/run_stage20_active_buffer_profile.sh

python scripts/build_stage75_rgt4_profile_boundary.py
```

## Gates

- r=6 and r=8 complete SAB correctness must pass.
- `cmux_calls == mat_ep_calls == expected_cmux == 573440`.
- `ncmux_calls == 5080`, `sub_a_calls == 39`, and active-buffer
  `copyback_calls == 0`.
- If Stage74 remains not promoted and Stage75 counts are invariant, the next
  r>4 work must be a new r>4-specific MAT layout/kernel or sparse/structured
  MAT hypothesis, not another direct lane-count increase.

## Failure Handling

- If count gates fail, fix the SAB schedule model before any r>4 optimization.
- If correctness fails, record r>4 unsupported under the current
  implementation.
- If counts and correctness pass but r>4 still trails r=4, keep the result as
  a profile-backed boundary and do not promote direct r>4.
