# Stage128 Compact EP API Boundary Gate

Date: 2026-07-03

## Decision

`PASS_STAGE128_COMPACT_EP_API_BOUNDARY_READY_MICROBENCH_REQUIRED`

Stage128 wraps the isolated compact EP kernel in MOSFHET-adjacent
selector/output/scratch API shapes. It remains a standalone generated
probe outside production headers and `sab_pvw_*`.

## Gates

| gate | status | metric | value | detail |
|---|---|---|---|---|
| stage128_mosfhet_static_build | PASS | make_static_spqlios | true | MOSFHET static library build using FFT_LIB=spqlios. |
| stage128_probe_compile | PASS | gcc_probe_compile | true | Standalone compact EP API boundary probe linked against libmosfhet.a. |
| stage128_probe_run | PASS | probe_returncode | 0 | Compact EP API boundary probe executed. |
| stage128_api_ownership_metadata | PASS | ownership_failures;metadata_failures;guard_failures | 0;0;0;0;0;0;0;0;0;0;0;0;0;0;0;0;0;0;0;0;0;0;0;0;0;0;0 | Selector/output/scratch ownership, metadata, and invalid-lane guards are valid. |
| stage128_no_allocation_hot_kernel | PASS | kernel_allocations | 0;0;0;0;0;0;0;0;0 | Kernel API uses caller-provided scratch and performs no API-owned allocations in the hot call. |
| stage128_api_kernel_equivalence | PASS_WITH_TOLERANCE | component_mismatches;phase_mismatches;noise_model_mismatches;max_gaps;tolerance | 0;0;0;0;0;0;0;0;0;0;0;0;0;0;0;0;0;0;0;0;0;0;0;0;0;0;0;14605;14608;131072 | API-boundary kernel preserves component, phase, and modeled-noise equivalence. |
| stage128_negative_control | PASS_REJECTS_BODY_ONLY_API | negative_failures | 1024;1024;2048;2048;3072;3072;2048;4096;6144 | Body-only API kernel remains rejected. |
| stage128_complexity_model | PASS | min_dft_term_ratio;min_total_term_ratio | 1.125000;1.000000 | API boundary preserves the isolated kernel count model. |
| stage128_decision | PASS_STAGE128_COMPACT_EP_API_BOUNDARY_READY_MICROBENCH_REQUIRED | next_gate_policy |  | MOSFHET-adjacent compact EP API boundary passes outside `sab_pvw_*`. |

## API Rows

| backend | r | N | seed | ownership | metadata | guards | kernel allocs | component mismatches | phase mismatches | noise mismatches | negative failures | max component gap | max phase gap | DFT ratio | total ratio | status |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---|
| spqlios | 2 | 512 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 1024 | 11267 | 11269 | 1.125000 | 1.000000 | PASS_COMPACT_EP_API_BOUNDARY |
| spqlios | 2 | 512 | 1 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 1024 | 8922 | 8914 | 1.125000 | 1.000000 | PASS_COMPACT_EP_API_BOUNDARY |
| spqlios | 4 | 512 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 2048 | 11570 | 11572 | 1.562500 | 1.250000 | PASS_COMPACT_EP_API_BOUNDARY |
| spqlios | 4 | 512 | 1 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 2048 | 11364 | 11371 | 1.562500 | 1.250000 | PASS_COMPACT_EP_API_BOUNDARY |
| spqlios | 6 | 512 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 3072 | 14605 | 14608 | 2.041667 | 1.555556 | PASS_COMPACT_EP_API_BOUNDARY |
| spqlios | 6 | 512 | 1 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 3072 | 10412 | 10418 | 2.041667 | 1.555556 | PASS_COMPACT_EP_API_BOUNDARY |
| spqlios | 2 | 1024 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 2048 | 12598 | 12623 | 1.125000 | 1.000000 | PASS_COMPACT_EP_API_BOUNDARY |
| spqlios | 4 | 1024 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 4096 | 12921 | 12909 | 1.562500 | 1.250000 | PASS_COMPACT_EP_API_BOUNDARY |
| spqlios | 6 | 1024 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 6144 | 12921 | 12936 | 2.041667 | 1.555556 | PASS_COMPACT_EP_API_BOUNDARY |

## Interpretation

The compact EP kernel now has an API-shaped ownership and scratch boundary
suitable for isolated microbench/profiling. It still has not been added to
MOSFHET production headers or integrated into SAB.
