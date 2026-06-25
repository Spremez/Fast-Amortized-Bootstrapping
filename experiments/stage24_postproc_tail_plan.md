# Stage 24 Conditional Post-processing Tail Plan

Date: 2026-06-25

## Objective

Re-measure the full-output PVW/MAT-SAB post-processing tail after the accepted
body-side improvements:

```text
FFT_LIB=spqlios_avx512
MAT_TRGSW_AVX512_SMALLR_SPECIALIZED=true
SAB_PVW_ACTIVE_BUFFER_FUSION=true
```

Stage 23 schedule-fused CMUX was neutral and is not part of the promoted path
for this audit.

## Hypothesis

`H2_full_pvw_postprocessing` predicts that batching or bypassing extract,
packing KS, and HW-KS could improve full bootstrapping only if those phases are
material after body optimization.

The measured tail is:

```text
tail = direct_extract_us + packing_ks_us + hw_ks_us
tail_pct = tail / full_us
```

## Gate

Run:

```bash
STAGE24_POSTPROC_RUNS=1 \
STAGE24_POSTPROC_R_VALUES="2 4" \
STAGE24_POSTPROC_OUT_DIR=repro/stage24_postproc_tail_avx512_runs1 \
bash scripts/run_stage24_postproc_tail_profile.sh
```

Correctness must pass for each profiled r value. Instrumented timing is for
attribution only and is not a final speedup claim.

## Decision Rule

Default threshold:

```text
STAGE24_POSTPROC_TAIL_PROMOTE_THRESHOLD_PCT=2.0
```

If the maximum observed tail percentage remains below the threshold, Stage 24
is recorded as deferred and no direct-to-packing KS implementation is started.

If the tail is above threshold, the next candidate must be designed as an
explicit flag with separate correctness gates:

```text
PVW accumulator lane -> direct packed TRLWE or batched packing KS
```

No post-processing optimization may be promoted unless complete SAB throughput,
correctness, noise, and resource gates improve over the current active-buffer
baseline.
