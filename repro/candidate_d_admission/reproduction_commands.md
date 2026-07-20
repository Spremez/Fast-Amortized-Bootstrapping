# Candidate D D0 Reproduction Commands

These commands are executable correctness and smoke checks. WSL smoke timing
is not formal performance evidence. If WSL cannot execute, record
`ENVIRONMENT_BLOCKED`; do not alter the frozen high-stat rows.

The required Stage 33 command is recorded verbatim below. It writes to
`repro/stage33_current_smoke` by default; do not run it with the tracked Stage 33 output directory
in a source checkout. Use a disposable exact snapshot or override the output
directory:

```text
STAGE33_OUT_DIR=/tmp/candidate-d-stage33-smoke bash scripts/run_stage33_current_smoke.sh
```

The D0 attempt was interrupted after a tracked Stage 33 output write and is
recorded as `ENVIRONMENT_BLOCKED` with
`NO_VALID_ISOLATED_SMOKE_RESULT`. The affected frozen files were restored to
their exact `1164b3f` Git blobs.

```text
python -m unittest discover -s tests/research -v

bash scripts/run_stage33_current_smoke.sh

make FFT_LIB=spqlios_avx512 A_PRNG=none ENABLE_VAES=false \
  KEY=BINARY PARAM=SET_2_3_2048 \
  MAT_TRGSW_AVX512_SMALLR_SPECIALIZED=true \
  MAT_TRGSW_AVX512_SUB_DECOMP=true \
  MAT_TRGSW_SUB_DECOMP_DFT_DIRECT=true \
  SAB_PVW_BACKEND_FROM_DFT_ADD=true \
  SAB_PVW_SUB_DECOMP_FUSION=true \
  SAB_PVW_DUAL_SUB_CMUX=true \
  SAB_PVW_SUBA_INCLUDE_ZERO_COEFF_ONE_FAST=true \
  SAB_PVW_TARGET_TEST=true -j$(nproc)
./main
```

Expected target smoke token:

```text
SAB_PVW target full bootstrap binary lane equivalence ... Pass
```
