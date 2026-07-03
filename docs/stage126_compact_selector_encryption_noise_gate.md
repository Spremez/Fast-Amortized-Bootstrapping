# Stage126 Compact Selector Encryption/Noise Gate

Date: 2026-07-03

## Decision

`PASS_STAGE126_COMPACT_SELECTOR_ENCRYPTION_NOISE_READY_ISOLATED_EP_KERNEL_REQUIRED`

Stage126 verifies deterministic compact selector encryption/noise
semantics through MOSFHET polynomial and production DFT operations. It
does not modify `sab_pvw_*`.

## Gates

| gate | status | metric | value | detail |
|---|---|---|---|---|
| stage126_mosfhet_static_build | PASS | make_static_spqlios | true | MOSFHET static library build using FFT_LIB=spqlios. |
| stage126_probe_compile | PASS | gcc_probe_compile | true | Standalone compact selector encryption/noise probe linked against libmosfhet.a. |
| stage126_probe_run | PASS | probe_returncode | 0 | Compact selector encryption/noise probe executed. |
| stage126_phase_equivalence | PASS | coeff_expected_mismatches;noise_model_mismatches | 0;0;0;0;0;0;0;0;0;0;0;0;0;0;0;0;0;0 | Coefficient-domain compact selector encryption phase equals clean reference plus modeled noise. |
| stage126_production_dft_noise_boundary | PASS_WITH_TOLERANCE | dft_expected_mismatches;max_dft_gap;tolerance | 0;0;0;0;0;0;0;0;0;14449;131072 | Production DFT external product phase matches modeled noisy phase within tolerance. |
| stage126_noise_bound | PASS | noise_bound_violations;max_noise_abs;max_bound | 0;0;0;0;0;0;0;0;0;13022;917504 | Modeled selector noise remains inside the declared conservative bound. |
| stage126_negative_control | PASS_REJECTS_BODY_ONLY_ENCRYPTION | negative_failures | 1024;1024;2048;2048;3072;3072;2048;4096;6144 | Body-only encrypted selector rows remain rejected. |
| stage126_layout_noise_terms | PASS | min_per_lane_noise_term_ratio;min_selector_ratio | 1.500000;1.125000 | Compact per-lane selector-noise term count and selector storage remain below current dense counts. |
| stage126_decision | PASS_STAGE126_COMPACT_SELECTOR_ENCRYPTION_NOISE_READY_ISOLATED_EP_KERNEL_REQUIRED | next_gate_policy |  | Compact selector encryption/noise simulator passes outside `sab_pvw_*`. |

## Noise Rows

| backend | r | N | T | seed | coeff mismatches | DFT mismatches | model mismatches | bound violations | negative failures | max DFT gap | max noise | bound | tolerance | status |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---|
| spqlios | 2 | 512 | 7 | 0 | 0 | 0 | 0 | 0 | 1024 | 10810 | 8560 | 458752 | 131072 | PASS_COMPACT_SELECTOR_ENCRYPTION_NOISE |
| spqlios | 2 | 512 | 7 | 1 | 0 | 0 | 0 | 0 | 1024 | 11789 | 8789 | 458752 | 131072 | PASS_COMPACT_SELECTOR_ENCRYPTION_NOISE |
| spqlios | 4 | 512 | 7 | 0 | 0 | 0 | 0 | 0 | 2048 | 9761 | 10794 | 458752 | 131072 | PASS_COMPACT_SELECTOR_ENCRYPTION_NOISE |
| spqlios | 4 | 512 | 7 | 1 | 0 | 0 | 0 | 0 | 2048 | 13844 | 8789 | 458752 | 131072 | PASS_COMPACT_SELECTOR_ENCRYPTION_NOISE |
| spqlios | 6 | 512 | 7 | 0 | 0 | 0 | 0 | 0 | 3072 | 11488 | 10794 | 458752 | 131072 | PASS_COMPACT_SELECTOR_ENCRYPTION_NOISE |
| spqlios | 6 | 512 | 7 | 1 | 0 | 0 | 0 | 0 | 3072 | 11755 | 8892 | 458752 | 131072 | PASS_COMPACT_SELECTOR_ENCRYPTION_NOISE |
| spqlios | 2 | 1024 | 7 | 0 | 0 | 0 | 0 | 0 | 2048 | 12235 | 13022 | 917504 | 131072 | PASS_COMPACT_SELECTOR_ENCRYPTION_NOISE |
| spqlios | 4 | 1024 | 7 | 0 | 0 | 0 | 0 | 0 | 4096 | 11107 | 13022 | 917504 | 131072 | PASS_COMPACT_SELECTOR_ENCRYPTION_NOISE |
| spqlios | 6 | 1024 | 7 | 0 | 0 | 0 | 0 | 0 | 6144 | 14449 | 13022 | 917504 | 131072 | PASS_COMPACT_SELECTOR_ENCRYPTION_NOISE |

## Layout Rows

| r | N | per-lane noise ratio | selector ratio | status |
|---:|---:|---:|---:|---|
| 2 | 512 | 1.500000 | 1.125000 | PASS_NOISE_LAYOUT_MODEL |
| 2 | 512 | 1.500000 | 1.125000 | PASS_NOISE_LAYOUT_MODEL |
| 4 | 512 | 2.500000 | 1.562500 | PASS_NOISE_LAYOUT_MODEL |
| 4 | 512 | 2.500000 | 1.562500 | PASS_NOISE_LAYOUT_MODEL |
| 6 | 512 | 3.500000 | 2.041667 | PASS_NOISE_LAYOUT_MODEL |
| 6 | 512 | 3.500000 | 2.041667 | PASS_NOISE_LAYOUT_MODEL |
| 2 | 1024 | 1.500000 | 1.125000 | PASS_NOISE_LAYOUT_MODEL |
| 4 | 1024 | 2.500000 | 1.562500 | PASS_NOISE_LAYOUT_MODEL |
| 6 | 1024 | 3.500000 | 2.041667 | PASS_NOISE_LAYOUT_MODEL |

## Interpretation

The compact selector encryption/noise simulator preserves the modeled phase
and noise in coefficient domain and through production DFT. This permits
an isolated compact external-product kernel gate next; full SAB noise and
failure-rate statistics remain open.
