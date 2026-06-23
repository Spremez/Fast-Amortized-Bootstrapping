# Stage 12 Experiment Validation Plan

Date: 2026-06-23

## Objective

Validate the Stage 12 AVX512 gate fix and second-generation small-r MAT kernel
without turning isolated kernel evidence into an unsupported full SAB claim.

## Primary Endpoint

The only primary performance endpoint remains:

```text
full-output sab_pvw_* SAB bootstrapping throughput
vs repeated scalar sab_rlwe_bootstrap
same backend
same target parameter shape
```

Target shape:

```text
KEY=BINARY
PARAM=SET_2_3_2048
r in {2,4}
WSL/Linux
```

## Gate Order

1. Staged correctness gate.
2. Target-size full-output correctness gate.
3. One-run full SAB smoke only for triage.
4. Three-process full SAB A/B sweep for any accepted speedup claim.
5. Noise/seed sweep if the variant is promoted beyond a kernel experiment.

## Stage 12 Gate Commands

Default AVX512 staged gate after the small-N skip policy:

```bash
make clean
make FFT_LIB=spqlios_avx512 SAB_PVW_KERNEL_TEST=true KEY=BINARY PARAM=SET_2_3 -j$(nproc)
./main
```

Regression gate that must keep full small sparse/bootstrap coverage:

```bash
make clean
make FFT_LIB=spqlios SAB_PVW_KERNEL_TEST=true KEY=BINARY PARAM=SET_2_3 -j$(nproc)
./main
```

V2 explicit small-r staged gate:

```bash
make clean
make FFT_LIB=spqlios_avx512 MAT_TRGSW_AVX512_SMALLR_SPECIALIZED=true SAB_PVW_KERNEL_TEST=true KEY=BINARY PARAM=SET_2_3 -j$(nproc)
./main
```

V2 target full-output correctness gate:

```bash
make clean
make FFT_LIB=spqlios_avx512 MAT_TRGSW_AVX512_SMALLR_SPECIALIZED=true SAB_PVW_TARGET_TEST=true KEY=BINARY PARAM=SET_2_3_2048 -j$(nproc)
./main
```

V2 one-run full SAB smoke:

```bash
STAGE11_BENCH_OUT_DIR=repro/stage12_avx512_smallr_v2_bench_r2_reps1_runs1 SAB_PVW_BENCH_R=2 SAB_PVW_BENCH_REPS=1 STAGE11_BENCH_RUNS=1 bash scripts/run_stage11_avx512_smallr_bench.sh
STAGE11_BENCH_OUT_DIR=repro/stage12_avx512_smallr_v2_bench_r4_reps1_runs1 SAB_PVW_BENCH_R=4 SAB_PVW_BENCH_REPS=1 STAGE11_BENCH_RUNS=1 bash scripts/run_stage11_avx512_smallr_bench.sh
```

## Promotion Criteria

To promote v2 from kernel experiment to candidate full SAB optimization:

- staged gate passes;
- target full-output correctness gate passes;
- three-process full SAB A/B sweep is positive on the same backend;
- repeated result improves or explains its relation to the accepted Stage 10
  clear-elision result;
- no scalar SAB regression is introduced;
- if promoted, run final-output noise/seed gates before any engineering claim.

## Stage 12 Result Label

Current label:

```text
[kernel experiment accepted]
[full SAB acceleration not accepted]
```

Reason:

- v2 improves isolated MAT external-product measurements;
- target full-output correctness passed;
- current full SAB evidence is one-run smoke only;
- smoke speedups `1.137x` at `r=2` and `1.253x` at `r=4` do not supersede the
  accepted Stage 10 result.

## Next Experiment Priority

The next priority is PVW-aware post-processing and SAB-specific sparse/fused
variants. More MAT-only tuning should be run only when it feeds one of those
larger SAB-level changes or when a formal three-run sweep shows a full SAB
benefit worth preserving.
