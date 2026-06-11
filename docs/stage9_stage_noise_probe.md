# Stage 9 Stage-Level Noise Probe

Date: 2026-06-12

## Objective

Add a test-only probe that compares the clear-elision `sab_pvw_*` path against
repeated scalar SAB at intermediate full-bootstrap boundaries.

This is not a new production path and does not change the default scalar SAB
route. The probe is compiled only with `SAB_PVW_STAGE_NOISE_TEST=true`.

Machine-readable table:

- `repro/stage9_stage_noise_summary.csv`

Raw logs:

- `repro/stage9_stage_noise_r2_trials1/main.log`
- `repro/stage9_stage_noise_r4_trials1/main.log`

## Method

The probe constructs the target `SET_2_3_2048` binary shape and compares PVW
lanes against repeated scalar lanes using the same input, lane LUTs, packing
key, and HW-reducing key.

Measured boundaries:

- `blind_rotate_coeff0`: coefficient 0 of each accumulator after
  `bootstrap_wo_extract`;
- `extract`: PVW TLWE extraction against scalar TLWE extraction;
- `materialize_tlwe`: copied PVW TLWE lane against scalar TLWE;
- `packing_ks`: full packing key switch output;
- `hw_ks`: HW-reducing key switch output.

The gate requires zero quantized pair failures at every measured boundary.

## Commands

```sh
make clean
make FFT_LIB=spqlios SAB_PVW_STAGE_NOISE_TEST=true SAB_PVW_NOISE_R=2 \
  SAB_PVW_NOISE_TRIALS=1 KEY=BINARY PARAM=SET_2_3_2048 -j$(nproc)
stdbuf -o0 ./main 2>&1 | tee repro/stage9_stage_noise_r2_trials1/main.log

make clean
make FFT_LIB=spqlios SAB_PVW_STAGE_NOISE_TEST=true SAB_PVW_NOISE_R=4 \
  SAB_PVW_NOISE_TRIALS=1 KEY=BINARY PARAM=SET_2_3_2048 -j$(nproc)
stdbuf -o0 ./main 2>&1 | tee repro/stage9_stage_noise_r4_trials1/main.log
```

## Results

| r | stage | points | pair failures | pair log2 sigma | pair log2 max abs |
|---:|---|---:|---:|---:|---:|
| 2 | blind_rotate_coeff0 | 4,096 | 0 | -14.932 | -13.023 |
| 2 | extract | 4,096 | 0 | -14.932 | -13.023 |
| 2 | materialize_tlwe | 4,096 | 0 | -14.932 | -13.023 |
| 2 | packing_ks | 4,096 | 0 | -14.932 | -13.026 |
| 2 | hw_ks | 4,096 | 0 | -8.044 | -6.280 |
| 4 | blind_rotate_coeff0 | 8,192 | 0 | -15.142 | -12.944 |
| 4 | extract | 8,192 | 0 | -15.142 | -12.944 |
| 4 | materialize_tlwe | 8,192 | 0 | -15.142 | -12.944 |
| 4 | packing_ks | 8,192 | 0 | -15.142 | -12.963 |
| 4 | hw_ks | 8,192 | 0 | -8.046 | -6.037 |

Both `r=2` and `r=4` passed the stage gate.

## Interpretation

The PVW-vs-scalar pair delta is small and stable through blind rotation,
extract, materialization, and packing KS. The largest pair sigma appears after
HW-KS for both lane counts, so future stage-level analysis should treat HW-KS
as the first boundary where the PVW/scalar difference becomes visibly larger.

This probe strengthens the engineering explanation for the existing final
output correctness/noise evidence, but it is still a `trials=1` stage-local
smoke. It should not be used as a paper-grade failure-rate claim without
multi-seed independent repetitions and a stated statistical model.
