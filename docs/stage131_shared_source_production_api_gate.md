# Stage131 Shared-Source Production API Gate

Date: 2026-07-03

## Decision

`PASS_STAGE131_SHARED_SOURCE_PRODUCTION_API_READY_SAB_INTEGRATION_DESIGN`

Stage131 adds the shared-source compact EP public API to MOSFHET and
validates it with an external probe linked through `mosfhet.h`.

## Gates

| gate | status | metric | value | detail |
|---|---|---|---|---|
| stage131_mosfhet_static_build | PASS | make_static_spqlios_enable_pvw | true | MOSFHET static library build includes production compact EP API. |
| stage131_probe_compile | PASS | public_header_link | true | Standalone probe compiles against mosfhet.h and libmosfhet.a. |
| stage131_probe_run | PASS | probe_returncode | 0 | Production API probe executed. |
| stage131_public_api_correctness | PASS | rows;max_component_gap;max_phase_gap | 6;13481;13475 | Public API preserves component, phase, noise, and negative-control gates. |
| stage131_decision | PASS_STAGE131_SHARED_SOURCE_PRODUCTION_API_READY_SAB_INTEGRATION_DESIGN | promotion_policy |  | Stage131 permits SAB integration design only, not full SAB claims. |

## API Rows

| r | N | seed | guards | component mismatches | phase mismatches | noise mismatches | negative failures | max component gap | max phase gap | status |
|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---|
| 2 | 512 | 0 | 0 | 0 | 0 | 0 | 1024 | 9654 | 9656 | PASS_SHARED_SOURCE_PRODUCTION_API |
| 4 | 512 | 0 | 0 | 0 | 0 | 0 | 2048 | 13481 | 13475 | PASS_SHARED_SOURCE_PRODUCTION_API |
| 6 | 512 | 0 | 0 | 0 | 0 | 0 | 3072 | 11352 | 11350 | PASS_SHARED_SOURCE_PRODUCTION_API |
| 2 | 1024 | 0 | 0 | 0 | 0 | 0 | 2048 | 12372 | 12397 | PASS_SHARED_SOURCE_PRODUCTION_API |
| 4 | 1024 | 0 | 0 | 0 | 0 | 0 | 4096 | 12190 | 12202 | PASS_SHARED_SOURCE_PRODUCTION_API |
| 6 | 1024 | 0 | 0 | 0 | 0 | 0 | 6144 | 12807 | 12817 | PASS_SHARED_SOURCE_PRODUCTION_API |

## Interpretation

The production API preserves the Stage130 correctness invariant. It still
does not integrate with SAB or prove complete bootstrapping speedup.
