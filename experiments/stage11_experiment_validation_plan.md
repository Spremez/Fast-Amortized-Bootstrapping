# Stage 11 Experiment Validation Plan

Date: 2026-06-23

## Primary Endpoint

Full-output SAB throughput speedup over repeated scalar SAB on the same
backend and parameter shape.

Primary target:

```text
binary SET_2_3_2048
WSL/Linux
FFT_LIB=spqlios or spqlios_avx512
r in {2,4}
```

## Gates

Correctness gate:

- small staged API gate passes for `r=1/2/4`;
- target-shape full-output gate passes;
- scalar default smoke remains runnable.

Noise gate:

- final-output PVW/scalar/pair failures are zero for the engineering seed set;
- stage-level probe is rerun if arithmetic changes affect noise.

Performance gate:

- at least three process runs for accepted speedup claims;
- same backend for scalar repeated and PVW;
- report mean, stddev, min, max;
- preserve negative and timed-out runs.

Statistical label:

- one-run smoke: `[engineering smoke only]`;
- three-run speedup: `[engineering evidence]`;
- paper-grade claim: requires larger randomized timing matrix and declared
  failure-rate target.

## Current Stage 11 Result

Variant:

```text
MAT_TRGSW_AVX512_SMALLR_SPECIALIZED=true
FFT_LIB=spqlios_avx512
```

Outcome:

- target `r=2` correctness replay passed;
- explicit-flag one-run benchmark replays passed for `r=2` and `r=4`;
- `r=2` full SAB speedup mean over three runs: `1.253x`;
- `r=4` one completed run: `1.189x`;
- explicit replay smokes: `1.109x` for `r=2`, `1.353x` for `r=4`;
- explicit-flag staged kernel run segfaulted after the `r=1`
  full-encrypted RGSW-monomial case and before any `r=2` RGSW-monomial result,
  so the variant is not accepted.

Conclusion:

```text
[experiment not supported] The first fused row/output AVX512 variant does not
establish an improvement over the existing clear-elision PVW/MAT-SAB path.
```

Stats sanity note:

- The three-run `r=2` result is engineering evidence but not a positive
  improvement because it does not beat the existing accepted path.
- The `r=4` result is smoke only because only one complete long-run summary
  exists; one incomplete timed-out run fragment is preserved as a failure
  artifact.
- The explicit replay rows validate reproducibility of the compile flag and
  script, not a new performance claim.

Next experiment:

- implement separate hand-unrolled `r=2` and `r=4` kernels without pointer
  arrays in the coefficient loop;
- require staged kernel correctness before any full SAB benchmark;
- compare against default AVX512 and `spqlios` clear-elision baselines.
