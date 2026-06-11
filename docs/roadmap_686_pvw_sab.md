# Roadmap: Accelerating 2025/686 SAB with PVW/MAT_TRGSW Lanes

Date: 2026-06-08

## Overall Objective

Accelerate the sparse amortized bootstrapping (SAB) algorithm used for the
2025/686 target by adding a new `sab_pvw_*` path that batches multiple
independent LUT/bootstrap lanes with a PVW/MAT_TRGSW external-product layout
inspired by `D:\projects\mbfhe-mb`.

The scalar SAB path must remain intact. All PVW work is added beside the
existing implementation until correctness, noise, and performance evidence are
strong enough to compare against the scalar baseline.

## Research Hypothesis

Status: experimental.

For workloads where several LUT/SAB lanes share the same input mask/control
schedule, replacing repeated scalar CMUX/external-product work with a
multi-body PVW/MAT_TRGSW path should improve throughput. The expected gain is
not from changing the SAB monomial schedule, but from batching lane bodies and
sharing decomposition/FFT/control-flow overhead across `r` lanes.

This hypothesis is falsifiable:

- If `r=2/4/8` PVW lanes do not improve throughput on WSL/Linux `spqlios` or
  AVX paths, the algorithmic change is not useful for 686 acceleration.
- If PVW correctness or noise degrades relative to scalar SAB beyond the target
  parameter tolerance, the optimization is not acceptable.
- If the main bottleneck moves to allocation, key size, extract, or packing KS,
  the next optimization target must change before claiming SAB acceleration.

## Fixed Design Choices

- Performance platform: WSL/Linux. Windows + FFNT is correctness smoke only.
- Optimization target: throughput for multiple LUT/SAB lanes.
- Meaning of `r`: number of independent LUT/SAB lanes sharing one control/key
  schedule. It is not accumulator-index packing.
- Integration style: add `sab_pvw_*` APIs; do not replace
  `sab_rlwe_bootstrap(...)` until all gates pass.
- Kernel style: use MOSFHET-native structures first. Import mbfhe-mb semantics,
  not its memory model.

## Non-Goals

- Do not claim paper-level novelty before literature and ablation checks.
- Do not optimize Windows FFNT timing.
- Do not rely on existing PVW TLWE code paths with known layout risks unless
  they receive dedicated tests.
- Do not enable include-zero or arbitrary-key paths as primary targets before
  binary/ternary target paths are stable.

## Stage 0: Baseline and Platform

Goal:

Fix the current project enough to build and establish the performance platform.

Why:

All later speedup claims require a stable scalar baseline and a fixed platform.

Artifacts:

- Baseline commit.
- Build commands.
- Parameter records.
- WSL/Linux toolchain snapshot.

Verification:

- Windows: `make FFT_LIB=ffnt ...` builds and can run smoke tests.
- WSL/Linux: `make FFT_LIB=spqlios ...` builds and full `main` passes.

Current status:

- Complete.
- Baseline commits exist through `4537798`.
- Later WSL/Linux `spqlios` full SAB smoke also passes.

## Stage 1: 686 SAB Protocol and Cost Map

Goal:

Write the current SAB call graph, external-product count model, and parameter
bookkeeping.

Why:

PVW batching must target the actual repeated unit. Without the call graph and
cost model, it is easy to replace the wrong layer.

Artifacts:

- `docs/protocol_map.md`
- `docs/cost_model.md`

Verification:

- External-product counts match instrumentation. Example:
  `SET_2_3_2048` binary uses `(h+1)*rho*N = 40*7*2048 = 573440`
  scalar TRGSW external products per bootstrap.

Current status:

- Complete enough for engineering.
- Some old Chinese docs are mojibake, so future summaries should use ASCII or
  UTF-8-verified files.

## Stage 2: Bottleneck Measurement

Goal:

Prove the target bottleneck is blind rotation / sparse multiplication /
RGSW monomial multiplication / CMUX rather than setup, extract, packing KS, or
memory allocation.

Why:

PVW batching is only justified if external-product and CMUX/RGSW inclusive cost
dominates.

Artifacts:

- `docs/profile_baseline.md`
- `docs/stage2_measurements.md`
- Profiling instrumentation in `sab_profile.*`
- `SAB_MICROBENCH=true`

Verification:

- Full profile call counts match the cost model.
- CMUX/RGSW inclusive time dominates full `sab_rlwe_bootstrap`.
- Setup/extract/KS are not primary bottlenecks.

Current status:

- Complete enough to proceed.
- Measurement showed raw `trgsw_mul_trlwe_DFT` is important but insufficient
  alone; PVW must batch at CMUX/RGSW layer.

## Stage 3: Independent PVW/MAT_TRGSW Kernel

Goal:

Implement and validate a MOSFHET-native matrix external-product kernel before
touching SAB hot paths.

Why:

SAB integration must not be mixed with low-level kernel bring-up. The kernel
needs its own correctness and performance evidence.

Artifacts:

- `src/mosfhet/src/mattrgsw.c`
- `MAT_TRGSW_MUL_SCRATCH`
- `SAB_PVW_KERNEL_TEST=true`
- `docs/stage3_pvw_kernel_status.md`

Verification gates:

- `ENABLE_PVW_TMLWE=true` links.
- Identity selector passes for `r=1/2/4`.
- `r=1` scalar equivalence against `trgsw_mul_trlwe_DFT(...)`.
- PVW external-product microbench for `r=1/2/4`, no allocation in timed loop.

Current status:

- Complete for kernel bring-up and external-product performance analysis.
- Implemented identity tests and WSL/Linux `spqlios` smoke.
- Added `r=1` scalar-equivalence coverage and repeated-scalar-vs-MAT
  microbenching for `r=1/2/4`.
- Added full-output external-product timing and same-level AVX/FMA comparison
  against mbfhe MAT.
- Detailed results are recorded in `docs/mat_external_product_breakdown.md`.
- Remaining work is no longer Stage 3 kernel bring-up; the next engineering
  step is Stage 4 state design and isolated CMUX/NCMUX lane tests.

## Stage 4: SAB-PVW State Design

Goal:

Design the lane state and invariants for `sab_pvw_*`.

Why:

The SAB accumulator is currently an array of scalar TRLWE samples. PVW needs a
multi-body state where each body represents one independent lane, while the
selector schedule remains shared.

Artifacts:

- `docs/sab_pvw_state_design.md`
- New structs for PVW SAB temporary state.
- No behavioral change to scalar SAB.

Required invariant:

For every CMUX/NCMUX step `t` and lane `q`:

```text
phase(acc_pvw.body[q] after step t)
==
phase(acc_scalar[q] after the same scalar SAB step t)
```

Verification:

- Deterministic isolated CMUX/NCMUX tests for `r=1/2/4`.
- No changes in scalar SAB outputs.

Current status:

- Complete for isolated lane-state validation.
- Implemented under `SAB_PVW_KERNEL_TEST`, so the scalar SAB default route is
  unchanged.
- Verified `r=1/2/4` for:
  - encrypted-input isolated CMUX with selector `0/1`;
  - trivial-input isolated NCMUX raw `X -> X^{-1}` branch with selector `0/1`.
- WSL/Linux `spqlios` Stage 4 gate passes.
- FFNT/portable Stage 4 smoke passes.
- Default scalar SAB WSL/Linux `spqlios` smoke still passes.

Remaining limitation:

- Full encrypted NCMUX still needs a PVW automorphism/key-switch strategy. The
  current isolated NCMUX check intentionally avoids the unimplemented
  `pvmtmlwe_keyswitch(...)` path and only validates the lane/body invariant for
  the raw automorphism branch on trivial inputs.

Decision gate:

- Choose first integration granularity:
  - isolated CMUX only;
  - `RGSW_monomial_mul` lane batching;
  - full `sparse_mul` lane batching.

Recommended decision:

Start with isolated CMUX, then RGSW monomial, then sparse_mul.

## Stage 5: `sab_pvw_*` Hot-Path Integration

Goal:

Add a new PVW SAB route that batches `r` independent LUT/SAB lanes under the
same sparse input/control schedule.

Why:

This is the first stage that can demonstrate practical SAB throughput
improvement.

Artifacts:

- `sab_pvw_*` API and implementation files.
- PVW selector/key generation from scalar selector schedule.
- PVW versions of CMUX/NCMUX and RGSW monomial multiplication.
- Per-lane extract/output support.

Verification:

- Small deterministic tests pass before target parameters.
- For each lane, PVW SAB output matches scalar SAB output under identical key,
  input, and LUT.
- Existing `sab_rlwe_bootstrap(...)` output remains unchanged.

Current status:

- Complete through the first `sab_pvw_*` API skeleton for the binary sparse
  hot path.
- Added `include/sab_pvw.h` and `src/sab_pvw.c`; the file is compiled only
  when `ENABLE_PVW_TMLWE=true`, so the default scalar build does not link the
  PVW SAB code.
- The scalar `RGSW_monomial_mul`, `sparse_mul`, and `sab_rlwe_bootstrap`
  implementations are unchanged.
- Verified `r=1/2/4` for:
  - `r_prec=1` encrypted selector bit `0/1`;
  - `r_prec=3` trivial-selector multibit schedule `{1,0,1}`;
  - `r_prec=3` full encrypted multibit schedule `{1,0,1}`.
- Added PVW TMLWE automorphism/key-switch support for NCMUX.
- Verified `sab_pvw_*` API binary `sparse_mul` lane equivalence for `r=1/2/4`,
  `h=2`, `r_prec=3`, `in_N=16`.
- The binary sparse test now materializes MAT selectors from a deterministic
  binary input-key schedule instead of hand-built PVW selectors.
- Added and verified small `sab_pvw_bootstrap_wo_extract_binary(...)`
  correctness for `r=1/2/4`, `h=2`, `r_prec=3`, `in_N=16`, `out_N=1024`.
- Added and verified PVW TLWE extraction correctness for the same small shape.
- Added and verified per-lane PVW TLWE materialization plus existing scalar
  full packing KS and HW-reducing KS correctness for the same small shape.
- Added callable full-output binary API:
  - `sab_pvw_new_binary_full_key(...)`;
  - `sab_pvw_bootstrap_binary(...)`.
- Verified full-output PVW binary bootstrap correctness for the small skeleton
  shape with `r=1/2/4`.
- Added explicit target-shape gate under `SAB_PVW_TARGET_TEST=true` and
  verified `SET_2_3_2048`-style `in_N=2048`, `out_N=2048`, `h=39`,
  `r_prec=7`, `r=2` full-output equivalence against repeated scalar
  `sab_rlwe_bootstrap(...)`.
- Fixed `PVW_TLWE` shared-mask arithmetic helpers so they process `n` mask
  coefficients, not `n*r`, avoiding out-of-bounds writes on multi-lane TLWE
  operations.
- Detailed results are recorded in `docs/stage5_pvw_rgsw_monomial_log.md`.
- Binary sparse results are recorded in `docs/stage5_pvw_sparse_mul_log.md`.
- No-extract bootstrap results are recorded in
  `docs/stage5_pvw_bootstrap_wo_extract_log.md`.
- Extract results are recorded in `docs/stage5_pvw_extract_log.md`.
- Packing/HW-KS results are recorded in
  `docs/stage5_pvw_packing_hwks_log.md`.
- Full-output API and target-shape results are recorded in
  `docs/stage5_pvw_full_bootstrap_log.md`.

Remaining limitation:

- The full `sab_pvw_*` binary bootstrap path is now connected for correctness,
  but it still materializes lanes and uses scalar full packing/HW KS per lane.
- Target shape is verified for one deterministic `r=2` binary gate, not yet for
  multi-seed correctness/noise or full performance A/B.
- Ternary/include-zero/gaussian `sub_a` branches remain out of scope for the
  current binary target.

Failure handling:

- If isolated CMUX passes but RGSW fails, debug monomial schedule and
  lane-state rotation.
- If RGSW passes but full sparse_mul fails, debug `sub_a` and final monomial
  step.

## Stage 6: Noise and Correctness Evaluation

Goal:

Prove that PVW speed does not come from unacceptable correctness degradation.

Why:

Bootstrapping changes are invalid if failure probability or noise growth
becomes worse without explanation.

Artifacts:

- Noise measurement hooks.
- Multi-seed correctness logs.
- Failure records for each parameter set.

Verification:

- Same LUT, input, key, and seed schedule: scalar and PVW lane outputs agree.
- Noise per stage is comparable or explained.
- Multi-seed failure rate is not worse than baseline within the accepted
  target threshold.

Decision gate:

- Define the minimum seed count and accepted failure threshold before claiming
  any final result.

Current status:

- Initial target-shape final-output correctness/noise gate has been added under
  `SAB_PVW_NOISE_TEST=true`.
- The gate is configurable through `SAB_PVW_NOISE_R`,
  `SAB_PVW_NOISE_TRIALS`, and `SAB_PVW_NOISE_MAX_LOG2_GAP`.
- The test uses valid per-lane LUTs packed through existing scalar
  `sab_LUT_packing(...)`, then copies each packed body into the matching PVW
  TV lane. This checks PVW and scalar against an explicit LUT expectation,
  not only against each other.
- Latest WSL/Linux `spqlios` target-shape result for `r=2`, `trials=3`,
  `SET_2_3_2048` shape:
  - PVW final-output failures: `0 / 12288`;
  - scalar final-output failures: `0 / 12288`;
  - PVW-vs-scalar quantized pair failures: `0 / 12288`;
  - PVW aggregate `log2_sigma_torus = -8.469`;
  - scalar aggregate `log2_sigma_torus = -8.162`;
  - `pvw_minus_scalar_log2 = -0.307`, within the loose engineering gate
    `SAB_PVW_NOISE_MAX_LOG2_GAP=4.0`.
- Windows FFNT target-shape smoke also passes with `ARCH_FLAGS=` and
  `trials=1`; Windows remains correctness/portability only.
- A test-only deterministic RNG switch is now available through
  `MOSFHET_DETERMINISTIC_RNG=true` and `MOSFHET_TEST_RNG_SEED=...`.
  A fixed-seed WSL/Linux `spqlios` smoke with seed `6862025` produced
  byte-for-byte identical output across two process restarts.
- Added `scripts/run_stage6_seed_sweep.sh` and
  `scripts/run_stage6_seed_sweep_range.sh` so one deterministic build can run
  multiple runtime seeds. Latest WSL/Linux `spqlios` sweep over seeds
  `6862025` through `6862074` passed with:
  - PVW final-output failures: `0 / 204800`;
  - scalar final-output failures: `0 / 204800`;
  - PVW-vs-scalar quantized pair failures: `0 / 204800`;
  - largest observed positive PVW-minus-scalar final-output noise gap:
    `0.636` log2 units, below the current engineering gate `4.0`;
  - smallest observed gap: `-0.470` log2 units;
  - average PVW-minus-scalar final-output noise gap: `-0.00386`
    log2 units.
- Detailed result is recorded in `docs/stage6_pvw_noise_log.md`.
- A 10-seed WSL/Linux `spqlios` target-shape sweep for `r=4` also passed:
  - PVW final-output failures: `0 / 81920`;
  - scalar final-output failures: `0 / 81920`;
  - PVW-vs-scalar quantized pair failures: `0 / 81920`;
  - PVW-minus-scalar final-output noise gap range: `[-0.541, 0.510]`
    log2 units;
  - average PVW-minus-scalar final-output noise gap: `-0.2026`
    log2 units.

Remaining limitation:

- The 50-seed campaign is enough for the planned `r=2` engineering gate, but it
  is not a formal paper-grade failure-rate claim.
- Noise is currently measured at final output. Stage-level noise probes before
  and after blind rotation, extract, packing KS, and HW KS remain open.
- `r=4` target-shape correctness/noise has a 10-seed engineering sweep, but
  not a paper-grade failure-rate campaign.

Recommended starting point:

- Correctness: at least 50 seeds for engineering signal.
- Paper-grade evidence: more seeds, confidence intervals, and clear failure
  model.

## Stage 7: Performance Evaluation

Goal:

Measure whether PVW SAB actually accelerates 2025/686 on the target platform.

Metrics:

- Bootstrap latency.
- Throughput per lane.
- Scaling over `r`.
- Key size.
- Memory peak.
- Key generation time.
- External-product microbench.
- CMUX/RGSW/sparse_mul profile breakdown.

Verification:

- WSL/Linux `spqlios` or explicit AVX path.
- Same parameters, comparable compiler flags, same instrumentation mode.
- Report median/mean/stddev and repeat count.

Minimum success:

- Stable throughput improvement for target parameter sets.
- No correctness/noise regression.

Current status:

- Initial target-shape full-output A/B benchmark added under
  `SAB_PVW_BENCH=true`.
- Benchmark is now configurable with `SAB_PVW_BENCH_R` and
  `SAB_PVW_BENCH_REPS`, and prints per-pair samples plus mean/stddev.
- Latest WSL/Linux `spqlios` result for `SET_2_3_2048` shape, `r=2`,
  `h=39`, `r_prec=7`, paired `reps=5`:
  - PVW full bootstrap average: `20,407,053.000 us` for 2 lanes
    (`673,527.822 us` stddev);
  - repeated scalar full bootstrap average: `24,304,453.600 us` for 2 lanes
    (`693,984.847 us` stddev);
  - throughput speedup: `1.191x`, speedup stddev `0.067`.
- Latest WSL/Linux `spqlios` result for `SET_2_3_2048` shape, `r=4`,
  `h=39`, `r_prec=7`, paired `reps=3`:
  - PVW full bootstrap average: `35,637,187.667 us` for 4 lanes
    (`194,931.465 us` stddev);
  - repeated scalar full bootstrap average: `46,330,045.333 us` for 4 lanes
    (`730,057.630 us` stddev);
  - throughput speedup: `1.300x`, speedup stddev `0.028`.
- Resource metrics are now recorded for `r=2` and `r=4`:
  - `r=2`: PVW estimated key bytes are `1.013617x` repeated scalar; PVW
    keygen is about `1.236x` repeated scalar; peak RSS is comparable
    (`382,740 KB` PVW vs `387,268 KB` scalar by `/usr/bin/time -v`).
  - `r=4`: PVW estimated key bytes are `1.065349x` repeated scalar; PVW
    keygen is about `1.179x` repeated scalar; peak RSS is comparable
    (`769,208 KB` PVW vs `771,208 KB` scalar by `/usr/bin/time -v`).
- A process-level repeated benchmark sweep is now recorded for `r=2` and
  `r=4`, with three independent `./main` runs per lane count and two paired
  timing repetitions inside each process:
  - `r=2`: all runs passed; mean speedup `1.188x`, sample stddev `0.066`,
    range `1.132x-1.261x`;
  - `r=4`: all runs passed; mean speedup `1.312x`, sample stddev `0.014`,
    range `1.302x-1.328x`.
- Detailed result is recorded in `docs/stage7_pvw_full_bench_log.md`.
- This is not final performance evidence yet because backend separation,
  larger benchmark matrices, and paper-grade statistics remain open.

Failure handling:

- If raw kernel is faster but full SAB is not, inspect allocation, conversion,
  extract, and memory bandwidth.
- If scaling saturates early, measure memory bandwidth and DFT conversion reuse.

## Stage 8: Ablation and Variant Analysis

Goal:

Understand why PVW succeeds or fails and whether variants are worth pursuing.

Candidate variants:

- `r=2/4/8` lane counts.
- Shared scratch pools vs per-call scratch.
- Batch only CMUX, batch RGSW monomial, or batch full sparse_mul.
- Different FFT backends.
- Compressed key or PRNG variants after correctness is stable.

Verification:

- One variable changed per ablation.
- Same parameter set and seed policy.
- Record negative results.

## Stage 9: Literature and Novelty Check

Goal:

Decide whether the result is a paper contribution or an engineering
optimization.

Why:

The implementation idea comes from mbfhe-mb/PVW-style matrix external products,
so novelty must be checked carefully.

Artifacts:

- Related-work matrix focused on multi-body/PVW external products and amortized
  bootstrapping.
- Claim support map.
- Contribution statements with evidence tags.

Verification:

- No paper claim is marked ready until supported by literature, theory, and
  experiment records.

Decision gate:

- If novelty is weak but engineering speedup is real, position it as an
  implementation/system optimization.
- If a new SAB-specific batching invariant or complexity improvement is
  demonstrably novel, prepare paper-grade evidence.

## Stage 10: Final Paper/Report Package

Goal:

Produce a reproducible report or paper section from validated artifacts.

Artifacts:

- Reproducibility pack.
- Final result tables.
- Method description.
- Limitations and failure cases.
- Claim-to-evidence mapping.

Verification:

- Every result has command, commit hash, platform, parameters, and log pointer.
- Every claim has supporting evidence.

## Immediate Execution Plan

The next executable step remains inside Stage 5:

1. Add PVW setup for multiple independent lane accumulators without replacing
   `setup_tv_xb`. Done for the small no-extract gate.
2. Add a small `sab_pvw_bootstrap_wo_extract` or equivalent test-only wrapper
   using the existing `SAB_PVW_Key` and binary sparse path. Done for binary.
3. Move from small no-extract correctness to per-lane extract/output comparison.
   Done for extracted TLWE phase comparison.

```text
phase(out_pvw_lane[q])
==
phase(out_scalar[q])
```

4. Add packing/HW-KS-aware comparison. Done on the small binary skeleton by
   materializing each PVW TLWE lane and reusing existing scalar full packing KS
   plus HW-reducing KS.
5. Scale the PVW binary path to target `SET_2_3_2048`. Done for a deterministic
   `r=2` full-output correctness gate.
6. Run broader Stage 6 correctness/noise checks, then repeat Stage 7 full
   performance A/B with the stronger correctness/noise evidence attached.
