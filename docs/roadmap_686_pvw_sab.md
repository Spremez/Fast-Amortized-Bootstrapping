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
- Detailed results are recorded in `docs/stage5_pvw_rgsw_monomial_log.md`.
- Binary sparse results are recorded in `docs/stage5_pvw_sparse_mul_log.md`.
- No-extract bootstrap results are recorded in
  `docs/stage5_pvw_bootstrap_wo_extract_log.md`.

Remaining limitation:

- The PVW path is not yet connected to full `sab_pvw_*` bootstrapping.
- Binary `sparse_mul` is verified only on the small API-skeleton test shape,
  not yet on target `h=39, in_N=2048`.
- `setup_tv_xb` and binary blind rotation now have a small PVW gate, but target
  shape, extraction, packing KS, and HW-reducing KS are still not integrated.
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
3. Move from small no-extract correctness to per-lane extract/output comparison:

```text
phase(out_pvw_lane[q])
==
phase(out_scalar[q])
```

4. Only after extract-aware `sab_pvw_*` correctness passes, scale to target
   `SET_2_3_2048`, then run noise and performance A/B.
