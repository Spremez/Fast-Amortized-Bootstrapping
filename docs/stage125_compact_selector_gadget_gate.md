# Stage125 Compact Selector Gadget Gate

Date: 2026-07-03

## Decision

`PASS_STAGE125_COMPACT_SELECTOR_GADGET_READY_ENCRYPTION_NOISE_GATE_REQUIRED`

Stage125 checks lane-local gadget decomposition and compact diagonal
injection through MOSFHET production DFT. It remains outside selector
encryption and `sab_pvw_*`.

## Gates

| gate | status | metric | value | detail |
|---|---|---|---|---|
| stage125_mosfhet_static_build | PASS | make_static_spqlios | true | MOSFHET static library build using FFT_LIB=spqlios. |
| stage125_probe_compile | PASS | gcc_probe_compile | true | Standalone compact selector gadget probe linked against libmosfhet.a. |
| stage125_probe_run | PASS | probe_returncode | 0 | Compact selector gadget decomposition probe executed. |
| stage125_compact_gadget_dft | PASS_WITH_TOLERANCE | coeff_dft_mismatches;max_gap;tolerance | 0;0;0;0;0;0;0;0;0;10240;16384 | Lane-local decomposition plus compact diagonal gadget injection matches coefficient reference through production DFT. |
| stage125_negative_control | PASS_REJECTS_BODY_ONLY_SELECTOR | negative_failures | 2048;2048;4096;4096;6144;6144;4096;8192;12288 | Omitting shared-mask gadget rows remains rejected. |
| stage125_layout_model | PASS | min_selector_ratio;min_selector_plus_dec_ratio;max_dec_overhead | 1.125000;1.000000;1.714286 | Selector storage advantage survives while decomposition stream overhead is recorded. |
| stage125_decision | PASS_STAGE125_COMPACT_SELECTOR_GADGET_READY_ENCRYPTION_NOISE_GATE_REQUIRED | next_gate_policy |  | Compact selector gadget decomposition and diagonal injection are smoke-validated outside `sab_pvw_*`. |

## Gadget Rows

| backend | r | N | T | Bg | seed | DFT mismatches | negative failures | max gap | tolerance | status |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---|
| spqlios | 2 | 1024 | 7 | 7 | 0 | 0 | 2048 | 8192 | 16384 | PASS_COMPACT_SELECTOR_GADGET |
| spqlios | 2 | 1024 | 7 | 7 | 1 | 0 | 2048 | 8192 | 16384 | PASS_COMPACT_SELECTOR_GADGET |
| spqlios | 4 | 1024 | 7 | 7 | 0 | 0 | 4096 | 7680 | 16384 | PASS_COMPACT_SELECTOR_GADGET |
| spqlios | 4 | 1024 | 7 | 7 | 1 | 0 | 4096 | 8192 | 16384 | PASS_COMPACT_SELECTOR_GADGET |
| spqlios | 6 | 1024 | 7 | 7 | 0 | 0 | 6144 | 10240 | 16384 | PASS_COMPACT_SELECTOR_GADGET |
| spqlios | 6 | 1024 | 7 | 7 | 1 | 0 | 6144 | 9216 | 16384 | PASS_COMPACT_SELECTOR_GADGET |
| spqlios | 2 | 2048 | 7 | 7 | 0 | 0 | 4096 | 9216 | 16384 | PASS_COMPACT_SELECTOR_GADGET |
| spqlios | 4 | 2048 | 7 | 7 | 0 | 0 | 8192 | 9216 | 16384 | PASS_COMPACT_SELECTOR_GADGET |
| spqlios | 6 | 2048 | 7 | 7 | 0 | 0 | 12288 | 8192 | 16384 | PASS_COMPACT_SELECTOR_GADGET |

## Layout Rows

| r | N | selector ratio | dec overhead | selector+dec ratio | status |
|---:|---:|---:|---:|---:|---|
| 2 | 1024 | 1.125000 | 1.333333 | 1.000000 | PASS_LAYOUT_MODEL |
| 2 | 1024 | 1.125000 | 1.333333 | 1.000000 | PASS_LAYOUT_MODEL |
| 4 | 1024 | 1.562500 | 1.600000 | 1.250000 | PASS_LAYOUT_MODEL |
| 4 | 1024 | 1.562500 | 1.600000 | 1.250000 | PASS_LAYOUT_MODEL |
| 6 | 1024 | 2.041667 | 1.714286 | 1.555556 | PASS_LAYOUT_MODEL |
| 6 | 1024 | 2.041667 | 1.714286 | 1.555556 | PASS_LAYOUT_MODEL |
| 2 | 2048 | 1.125000 | 1.333333 | 1.000000 | PASS_LAYOUT_MODEL |
| 4 | 2048 | 1.562500 | 1.600000 | 1.250000 | PASS_LAYOUT_MODEL |
| 6 | 2048 | 2.041667 | 1.714286 | 1.555556 | PASS_LAYOUT_MODEL |

## Interpretation

The compact selector can express the needed diagonal gadget injection in a
production DFT smoke model. Decomposition-stream overhead is now explicit:
r=2 is only break-even for selector+decomposition counts, while r=4 and
r=6 retain positive count ratios.
