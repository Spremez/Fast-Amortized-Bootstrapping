# Stage124 MOSFHET Type/API Skeleton

Date: 2026-07-03

## Decision

`PASS_STAGE124_MOSFHET_TYPE_API_SKELETON_READY_GADGET_DECOMPOSITION_GATE_REQUIRED`

Stage124 compiles and runs a standalone MOSFHET-adjacent skeleton for
vector-shared lane-local accumulators and compact selector DFT rows. It
does not modify production MOSFHET headers or `sab_pvw_*`.

## Gates

| gate | status | metric | value | detail |
|---|---|---|---|---|
| stage124_mosfhet_static_build | PASS | make_static_spqlios | true | MOSFHET static library build using FFT_LIB=spqlios. |
| stage124_probe_compile | PASS | gcc_probe_compile | true | Standalone type/API skeleton probe linked against libmosfhet.a. |
| stage124_probe_run | PASS | probe_returncode | 0 | Standalone MOSFHET-adjacent type/API skeleton probe executed. |
| stage124_component_ownership | PASS | component_failures | 0;0;0;0;0;0 | All allocated torus/DFT polynomial coefficient buffers are non-null and non-aliased inside the skeleton scope. |
| stage124_metadata_and_lane_coverage | PASS | metadata_failures;selector_coverage_failures | 0;0;0;0;0;0;0;0;0;0;0;0 | Accumulator, DFT accumulator, and selector rows preserve k/r/N/T metadata and lane-local shared/body indexing. |
| stage124_acc_dft_roundtrip | PASS_WITH_TOLERANCE | roundtrip_mismatches;max_gap;tolerance | 0;0;0;0;0;0;1;1024 | Vector-shared accumulator torus->DFT->torus lifecycle survives production MOSFHET conversion. |
| stage124_layout_model | PASS | min_selector_ratio;min_total_ratio;max_acc_overhead | 1.125000;1.100000;1.714286 | Compact selector DFT storage beats current dense selector and total accumulator+selector polynomial count despite accumulator overhead. |
| stage124_decision | PASS_STAGE124_MOSFHET_TYPE_API_SKELETON_READY_GADGET_DECOMPOSITION_GATE_REQUIRED | next_gate_policy |  | MOSFHET-adjacent vector-shared type/API skeleton is compile-checked outside `sab_pvw_*`. |

## API Rows

| backend | r | N | T | k | component failures | metadata failures | coverage failures | roundtrip mismatches | max gap | tolerance | status |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---|
| spqlios | 2 | 1024 | 7 | 1 | 0 | 0 | 0 | 0 | 1 | 1024 | PASS_TYPE_API_SKELETON |
| spqlios | 4 | 1024 | 7 | 1 | 0 | 0 | 0 | 0 | 1 | 1024 | PASS_TYPE_API_SKELETON |
| spqlios | 6 | 1024 | 7 | 1 | 0 | 0 | 0 | 0 | 1 | 1024 | PASS_TYPE_API_SKELETON |
| spqlios | 2 | 2048 | 7 | 1 | 0 | 0 | 0 | 0 | 1 | 1024 | PASS_TYPE_API_SKELETON |
| spqlios | 4 | 2048 | 7 | 1 | 0 | 0 | 0 | 0 | 1 | 1024 | PASS_TYPE_API_SKELETON |
| spqlios | 6 | 2048 | 7 | 1 | 0 | 0 | 0 | 0 | 1 | 1024 | PASS_TYPE_API_SKELETON |

## Layout Rows

| r | N | T | current acc | vector acc | acc overhead | current selector | vector selector | selector ratio | current total | vector total | total ratio | status |
|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---|
| 2 | 1024 | 7 | 3 | 4 | 1.333333 | 63 | 56 | 1.125000 | 66 | 60 | 1.100000 | PASS_LAYOUT_MODEL |
| 4 | 1024 | 7 | 5 | 8 | 1.600000 | 175 | 112 | 1.562500 | 180 | 120 | 1.500000 | PASS_LAYOUT_MODEL |
| 6 | 1024 | 7 | 7 | 12 | 1.714286 | 343 | 168 | 2.041667 | 350 | 180 | 1.944444 | PASS_LAYOUT_MODEL |
| 2 | 2048 | 7 | 3 | 4 | 1.333333 | 63 | 56 | 1.125000 | 66 | 60 | 1.100000 | PASS_LAYOUT_MODEL |
| 4 | 2048 | 7 | 5 | 8 | 1.600000 | 175 | 112 | 1.562500 | 180 | 120 | 1.500000 | PASS_LAYOUT_MODEL |
| 6 | 2048 | 7 | 7 | 12 | 1.714286 | 343 | 168 | 2.041667 | 350 | 180 | 1.944444 | PASS_LAYOUT_MODEL |

## Interpretation

The skeleton preserves MOSFHET allocation and production DFT lifecycle
while keeping lane-local selector coverage explicit. It opens only the
next gadget-decomposition gate; it is not complete-SAB acceleration
evidence.
