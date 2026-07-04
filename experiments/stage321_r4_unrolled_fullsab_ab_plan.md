# Stage321 r=4 Unrolled Full-SAB A/B Plan

Input decision: `PASS_STAGE320_RETURN_TO_MAT_EP_SELECT_R4_UNROLLED_REFRESH`.

Run same-backend current-head A/B:

- control: current selected direct MAT/SAB path;
- candidate: add `MAT_TRGSW_AVX512_R4_UNROLLED_ROWS=true`;
- endpoint: complete SAB `T_bootstrap/r`;
- gate: correctness pass and repeated speedup; if positive, run noise/resource.

If Stage321 is neutral or negative, close r=4 unrolled for current head and
move to SAB schedule attribution.
