# PVW/MAT-SAB Final Engineering Report

Date: 2026-06-25

## Scope

This report summarizes the completed scoped engineering evidence chain for the
PVW/MAT-SAB path. It is not a novelty claim and it is not a theorem-level paper
draft. The supported claim is:

```text
For the tested binary 2025/686 SAB implementation and recorded AVX512 backend,
the explicit sab_pvw_* path batches multiple independent LUT/SAB lanes with
PVW/MAT shared-mask multi-body external products and improves complete SAB
throughput over repeated scalar SAB, while preserving the tested correctness,
final-output noise, resource, and reproducibility gates.
```

Blocked claims remain blocked:

- shared-mask or multi-body TFHE batching novelty;
- non-binary PVW-SAB support;
- all-parameter SAB speedup;
- multi-fold SAB speedup;
- MAT-AVX512 theoretical optimality;
- theorem, algorithm, remark, table, or figure citations to 2025/686.

## Implemented Path

The optimized path is an explicit `sab_pvw_*` path beside the scalar SAB path.
It keeps scalar `sab_rlwe_bootstrap` available as the comparison baseline.

Core pieces:

- PVW/MAT shared-mask multi-body state for multiple independent LUT/SAB lanes;
- MAT external product integration into the SAB CMUX/RGSW monomial path;
- `MAT_TRGSW_AVX512_SMALLR_SPECIALIZED=true` for practical small-r AVX512
  kernels;
- `SAB_PVW_ACTIVE_BUFFER_FUSION=true` to carry active ping-pong accumulator
  state across RGSW monomial/sparse schedule boundaries;
- explicit ablation flags for neutral candidates rather than replacing the
  promoted path.

Primary promoted engineering variant:

```text
FFT_LIB=spqlios_avx512
KEY=BINARY
MAT_TRGSW_AVX512_SMALLR_SPECIALIZED=true
SAB_PVW_ACTIVE_BUFFER_FUSION=true
```

## Algorithmic Effect

The implemented batching treats `r` as multiple independent LUT/SAB lanes. The
PVW/MAT path shares the mask-side work and evaluates multiple body lanes
together. At complete-SAB level, this reduces repeated scalar work while still
keeping the sparse SAB schedule semantics lane-equivalent to scalar reference
runs under tested binary parameters.

The strongest promoted schedule-level optimization is active-buffer fusion:

- Stage 19 fixed the target schedule count model;
- Stage 20 removed forced copyback in the promoted PVW body path;
- later schedule/sub_a/post-processing candidates were validated but not
  promoted when full SAB A/B did not improve or when tail cost was too small.

## Performance Summary

Primary endpoint: complete `sab_pvw_*` bootstrapping throughput versus repeated
scalar SAB under the same backend.

| scope | param | r | runs | mean speedup | range | interpretation |
|---|---|---:|---:|---:|---:|---|
| target final rerun | `SET_2_3_2048` | 2 | 3 | `1.171x` | `1.111x-1.285x` | positive but noisy |
| target final rerun | `SET_2_3_2048` | 4 | 3 | `1.401x` | `1.331x-1.472x` | strongest current target evidence |
| added binary | `SET_2_3_4096` | 2 | 5 | `1.224x` | `1.207x-1.233x` | stable small-sample support |
| added binary | `SET_2_3_4096` | 4 | 5 | `1.318x` | `1.272x-1.350x` | stable small-sample support |
| added binary | `SET_4_5_2048` | 2 | 5 | `1.329x` | `1.082x-1.473x` | positive mean, high variance |
| added binary | `SET_4_5_2048` | 4 | 5 | `1.346x` | `1.305x-1.455x` | positive small-sample support |

Source:

```text
repro/stage27_final_evidence_package/performance_scope.csv
```

## Noise and Correctness

Final-output noise gates:

| scope | param | r | seeds | points | PVW failures | scalar failures | pair failures |
|---|---|---:|---:|---:|---:|---:|---:|
| target | `SET_2_3_2048` | 2 | 50 | 204800 | 0 | 0 | 0 |
| target | `SET_2_3_2048` | 4 | 50 | 409600 | 0 | 0 | 0 |
| added binary | `SET_2_3_4096` | 2 | 5 | 40960 | 0 | 0 | 0 |
| added binary | `SET_2_3_4096` | 4 | 5 | 81920 | 0 | 0 | 0 |
| added binary | `SET_4_5_2048` | 2 | 5 | 20480 | 0 | 0 | 0 |
| added binary | `SET_4_5_2048` | 4 | 5 | 40960 | 0 | 0 | 0 |

Source:

```text
repro/stage27_final_evidence_package/noise_scope.csv
```

Stage-level noise remains smoke-level. It should not be used for
stage-by-stage noise claims unless expanded.

## Resource Summary

Target binary resource snapshot:

| r | mode | keygen lane avg us | key bytes ratio vs repeated scalar | max RSS KB |
|---:|---|---:|---:|---:|
| 2 | PVW | `573741.000` | `1.013617` | `383240` |
| 4 | PVW | `599465.000` | `1.065349` | `769388` |

Source:

```text
repro/stage27_final_evidence_package/resource_scope.csv
```

The resource table is a snapshot, not a statistical resource campaign.

## Ablation Decisions

| stage | result | decision |
|---|---|---|
| Stage 20 active-buffer fusion | correctness and full SAB gains passed | promoted explicit path |
| Stage 21 sub_a output fusion | correctness passed, performance below Stage 20 | neutral, not promoted |
| Stage 22 MAT AVX512 specialized kernel | practical same-backend improvement | used, not claimed theoretical-optimal |
| Stage 23 schedule-fused CMUX | correctness passed, full SAB neutral | neutral, not promoted |
| Stage 24 post-processing optimization | tail below threshold | deferred |

This preserves negative and neutral evidence instead of folding it into the
promoted claim.

## Reproducibility Entry Points

Core package:

```text
python scripts/build_stage27_final_package.py
```

Citation gate:

```text
bash scripts/run_stage27_citation_access_probe.sh
python scripts/build_stage27_final_package.py
```

Main artifacts:

```text
docs/stage27_final_evidence_package.md
docs/stage27_completion_readiness_audit.md
repro/stage27_final_evidence_package/manifest.csv
repro/stage27_completion_readiness_audit.csv
repro/stage27_claim_support_matrix.csv
repro/run_log.csv
```

## Claim Boundary

Ready for scoped engineering reporting:

- PVW/MAT-SAB implementation exists beside scalar SAB;
- complete SAB throughput improves over repeated scalar SAB on tested binary
  targets;
- target r=2/r=4 final-output noise has 50-seed support;
- added binary parameters have 5-run/5-seed small-sample support;
- active-buffer fusion is a SAB-specific engineering optimization;
- specialized MAT-AVX512 is practically useful.

Blocked or conditional:

- novelty: blocked by 2025/2112 common-mask/shared-mask prior-art risk;
- 2025/686 theorem-level citations: blocked until full text is provided and
  inspected;
- non-binary PVW-SAB: unsupported;
- broad all-parameter claim: not supported by current evidence;
- theoretical AVX512 optimality: not supported without native perf counters.

## Final Decision

Status:

```text
SCOPED_ENGINEERING_REPORT_READY
SAFE_SCOPED_ENGINEERING_CLAIM_SUPPORTED
NOVELTY_AND_THEOREM_LEVEL_CLAIMS_BLOCKED
```

The current project state is suitable for an engineering report about scoped
PVW/MAT-SAB acceleration. It is not suitable for a novelty-first manuscript
without additional full-paper and prior-art review.
