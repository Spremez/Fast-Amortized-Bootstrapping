# Stage 20 Active-Buffer Validation Plan

Date: 2026-06-25

## Objective

Test an explicit active-buffer PVW SAB path that carries the RGSW monomial
ping-pong accumulator across sparse steps instead of forcing copyback after
every RGSW monomial.

## Flag

```text
SAB_PVW_ACTIVE_BUFFER_FUSION=true
```

The default scalar SAB and default PVW SAB paths are unchanged.

## Expected Target Effect

For `BINARY SET_2_3_2048`:

```text
h = 39
r_prec = 7
RGSW monomial calls = h + 1 = 40
legacy copyback calls = 40
active-buffer copyback calls = 0
```

This is not expected to reduce MAT external-product count. It only removes
forced accumulator-array normalization between sparse steps.

## Correctness Gates

- target full-output gate:

```bash
make clean && make FFT_LIB=spqlios_avx512 \
  MAT_TRGSW_AVX512_SMALLR_SPECIALIZED=true \
  SAB_PVW_ACTIVE_BUFFER_FUSION=true \
  SAB_PVW_TARGET_TEST=true KEY=BINARY PARAM=SET_2_3_2048 -j$(nproc) && ./main
```

- active-buffer profile gate for `r=2` and `r=4`:

```bash
STAGE20_ACTIVE_PROFILE_RUNS=1 \
STAGE20_ACTIVE_PROFILE_R_VALUES="2 4" \
STAGE20_ACTIVE_PROFILE_OUT_DIR=repro/stage20_active_buffer_profile_avx512_runs1 \
bash scripts/run_stage20_active_buffer_profile.sh
```

## Performance Gates

- one-run uninstrumented full SAB smoke for `r=2` and `r=4`;
- three-process full SAB sweep only if smoke is positive enough to justify
  promotion;
- compare against Stage 16 and Stage 18 means, not against instrumented profile
  timings.

## Failure Handling

- correctness failure: reject and keep logs;
- copyback count not reduced: fix state tracking before timing;
- profile improves but full SAB does not: keep as neutral ablation;
- r-specific improvement: scope the variant to the improving r value.
