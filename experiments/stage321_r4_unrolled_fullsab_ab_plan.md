# Stage321 r=4 Unrolled Full-SAB A/B Plan

Input decision: `PASS_STAGE320_RETURN_TO_MAT_EP_SELECT_R4_UNROLLED_REFRESH`.

## Comparison

- control: current selected direct PVW/MAT-SAB path;
- candidate: control plus `MAT_TRGSW_AVX512_R4_UNROLLED_ROWS=true`;
- endpoint: complete SAB `T_bootstrap/r`;
- parameter: `BINARY SET_2_3_2048`, include-zero mode, r=4.

## Gate

- correctness must pass for both variants;
- at least five local samples per variant;
- promote only if mean speedup is at least 1.02x and the candidate high CI is
  below the control low CI;
- weak-positive results require more statistics before noise/resource;
- neutral results close this r4-unrolled refresh and return to SAB schedule
  attribution.

Current decision: `NEUTRAL_STAGE321_R4_UNROLLED_DIRECT_FULLSAB_NO_PROMOTION`.
