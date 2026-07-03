# Stage127 Isolated Compact EP Kernel Gate

Date: 2026-07-03

## Decision

`PASS_STAGE127_ISOLATED_COMPACT_EP_KERNEL_READY_API_BOUNDARY_REQUIRED`

Stage127 factors compact selector external product into a reusable
`compact_ep_kernel_dft` in a standalone generated C probe. It remains
outside MOSFHET production headers and `sab_pvw_*`.

## Gates

| gate | status | metric | value | detail |
|---|---|---|---|---|
| stage127_mosfhet_static_build | PASS | make_static_spqlios | true | MOSFHET static library build using FFT_LIB=spqlios. |
| stage127_probe_compile | PASS | gcc_probe_compile | true | Standalone isolated compact EP kernel probe linked against libmosfhet.a. |
| stage127_probe_run | PASS | probe_returncode | 0 | Isolated compact EP kernel probe executed. |
| stage127_kernel_component_equivalence | PASS_WITH_TOLERANCE | component_mismatches;max_component_gap;tolerance | 0;0;0;0;0;0;0;0;0;14645;131072 | DFT compact kernel output components match coefficient reference within tolerance. |
| stage127_kernel_phase_noise | PASS_WITH_TOLERANCE | phase_mismatches;noise_model_mismatches;max_phase_gap;tolerance | 0;0;0;0;0;0;0;0;0;0;0;0;0;0;0;0;0;0;14653;131072 | DFT compact kernel phase equals modeled noisy reference while coefficient noise model remains exact. |
| stage127_negative_control | PASS_REJECTS_BODY_ONLY_KERNEL | negative_failures | 1024;1024;2048;2048;3072;3072;2048;4096;6144 | Body-only compact EP kernel remains rejected. |
| stage127_complexity_model | PASS | min_dft_term_ratio;min_total_term_ratio | 1.125000;1.000000 | Isolated compact EP kernel preserves positive DFT-term ratio and non-negative total-term ratio. |
| stage127_decision | PASS_STAGE127_ISOLATED_COMPACT_EP_KERNEL_READY_API_BOUNDARY_REQUIRED | next_gate_policy |  | Reusable isolated compact EP DFT kernel passes outside `sab_pvw_*`. |

## Kernel Rows

| backend | r | N | seed | component mismatches | phase mismatches | noise mismatches | negative failures | max component gap | max phase gap | DFT ratio | total ratio | status |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---|
| spqlios | 2 | 512 | 0 | 0 | 0 | 0 | 1024 | 10301 | 10301 | 1.125000 | 1.000000 | PASS_ISOLATED_COMPACT_EP_KERNEL |
| spqlios | 2 | 512 | 1 | 0 | 0 | 0 | 1024 | 10142 | 10141 | 1.125000 | 1.000000 | PASS_ISOLATED_COMPACT_EP_KERNEL |
| spqlios | 4 | 512 | 0 | 0 | 0 | 0 | 2048 | 11651 | 11647 | 1.562500 | 1.250000 | PASS_ISOLATED_COMPACT_EP_KERNEL |
| spqlios | 4 | 512 | 1 | 0 | 0 | 0 | 2048 | 14645 | 14653 | 1.562500 | 1.250000 | PASS_ISOLATED_COMPACT_EP_KERNEL |
| spqlios | 6 | 512 | 0 | 0 | 0 | 0 | 3072 | 11028 | 11014 | 2.041667 | 1.555556 | PASS_ISOLATED_COMPACT_EP_KERNEL |
| spqlios | 6 | 512 | 1 | 0 | 0 | 0 | 3072 | 11103 | 11089 | 2.041667 | 1.555556 | PASS_ISOLATED_COMPACT_EP_KERNEL |
| spqlios | 2 | 1024 | 0 | 0 | 0 | 0 | 2048 | 13359 | 13358 | 1.125000 | 1.000000 | PASS_ISOLATED_COMPACT_EP_KERNEL |
| spqlios | 4 | 1024 | 0 | 0 | 0 | 0 | 4096 | 12069 | 12087 | 1.562500 | 1.250000 | PASS_ISOLATED_COMPACT_EP_KERNEL |
| spqlios | 6 | 1024 | 0 | 0 | 0 | 0 | 6144 | 12742 | 12730 | 2.041667 | 1.555556 | PASS_ISOLATED_COMPACT_EP_KERNEL |

## Interpretation

The compact EP arithmetic has now been isolated behind a reusable kernel
shape. The result is still a generated probe, so the next step is an API
boundary stage before any production MOSFHET or SAB hot-path changes.
