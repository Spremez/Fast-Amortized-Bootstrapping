# Stage121 Vector-Shared DFT/Conversion Gate

Date: 2026-07-03

## Decision

`PASS_STAGE121_VECTOR_SHARED_DFT_CONVERSION_READY_STRUCTURED_EP_PROTOTYPE_REQUIRED`

Stage121 advances the vector-shared real struct route through an exact
negacyclic NTT/DFT conversion gate. It remains outside `sab_pvw_*` and
outside production MOSFHET FFT/AVX512 code.

## Gates

| gate | status | metric | value | detail |
|---|---|---|---|---|
| stage121_compile | PASS | gcc_compile | true | Generated exact negacyclic NTT/DFT C probe compiled under WSL gcc. |
| stage121_root_availability | PASS | root_status | PASS_ROOT;PASS_ROOT;PASS_ROOT;PASS_ROOT;PASS_ROOT;PASS_ROOT;PASS_ROOT;PASS_ROOT;PASS_ROOT;PASS_ROOT;PASS_ROOT;PASS_ROOT;PASS_ROOT;PASS_ROOT;PASS_ROOT;PASS_ROOT;PASS_ROOT;PASS_ROOT;PASS_ROOT;PASS_ROOT;PASS_ROOT;PASS_ROOT;PASS_ROOT;PASS_ROOT;PASS_ROOT;PASS_ROOT;PASS_ROOT;PASS_ROOT;PASS_ROOT;PASS_ROOT | Modulus 12289 supplies exact 2N-th roots for N=32 and N=64. |
| stage121_roundtrip | PASS | roundtrip_mismatches | 0;0;0;0;0;0;0;0;0;0;0;0;0;0;0;0;0;0;0;0;0;0;0;0;0;0;0;0;0;0 | Vector-shared mask/body/secret polynomials round-trip through exact DFT. |
| stage121_phase_equivalence | PASS | phase_mismatches;noisy_phase_mismatches | 0;0;0;0;0;0;0;0;0;0;0;0;0;0;0;0;0;0;0;0;0;0;0;0;0;0;0;0;0;0|0;0;0;0;0;0;0;0;0;0;0;0;0;0;0;0;0;0;0;0;0;0;0;0;0;0;0;0;0;0 | DFT-domain phase `B - A*S` matches coefficient-domain phase after inverse DFT. |
| stage121_noise_bound | PASS_BOUNDED | noise_bound_violations | 0;0;0;0;0;0;0;0;0;0;0;0;0;0;0;0;0;0;0;0;0;0;0;0;0;0;0;0;0;0 | Injected coefficient noise remains within the digit-sum bound after conversion. |
| stage121_layout_allocation | PASS | r4_N64_vector_over_dense_dft_poly_ratio | 0.533333 | DFT prototype preserves the vector-shared polynomial-count bound. |
| stage121_decision | PASS_STAGE121_VECTOR_SHARED_DFT_CONVERSION_READY_STRUCTURED_EP_PROTOTYPE_REQUIRED | next_gate_policy |  | Exact conversion gate passes outside SAB. |

## Layout Rows

| r | N | dense DFT polys | vector DFT polys | ratio | conversion input polys | status |
|---:|---:|---:|---:|---:|---:|---|
| 2 | 32 | 12 | 8 | 0.666667 | 10 | PASS_LAYOUT |
| 2 | 64 | 12 | 8 | 0.666667 | 10 | PASS_LAYOUT |
| 4 | 32 | 30 | 16 | 0.533333 | 20 | PASS_LAYOUT |
| 4 | 64 | 30 | 16 | 0.533333 | 20 | PASS_LAYOUT |
| 6 | 32 | 56 | 24 | 0.428571 | 30 | PASS_LAYOUT |
| 6 | 64 | 56 | 24 | 0.428571 | 30 | PASS_LAYOUT |

## Conversion Rows

| r | N | seed | root | roundtrip | phase | noisy phase | noise violations | rss KB | status |
|---:|---:|---:|---|---:|---:|---:|---:|---:|---|
| 2 | 32 | 0 | PASS_ROOT | 0 | 0 | 0 | 0 | 1096 | PASS_DFT_CONVERSION |
| 2 | 32 | 1 | PASS_ROOT | 0 | 0 | 0 | 0 | 1096 | PASS_DFT_CONVERSION |
| 2 | 32 | 2 | PASS_ROOT | 0 | 0 | 0 | 0 | 1096 | PASS_DFT_CONVERSION |
| 2 | 32 | 3 | PASS_ROOT | 0 | 0 | 0 | 0 | 1096 | PASS_DFT_CONVERSION |
| 2 | 32 | 4 | PASS_ROOT | 0 | 0 | 0 | 0 | 1096 | PASS_DFT_CONVERSION |
| 2 | 64 | 0 | PASS_ROOT | 0 | 0 | 0 | 0 | 1096 | PASS_DFT_CONVERSION |
| 2 | 64 | 1 | PASS_ROOT | 0 | 0 | 0 | 0 | 1096 | PASS_DFT_CONVERSION |
| 2 | 64 | 2 | PASS_ROOT | 0 | 0 | 0 | 0 | 1096 | PASS_DFT_CONVERSION |
| 2 | 64 | 3 | PASS_ROOT | 0 | 0 | 0 | 0 | 1096 | PASS_DFT_CONVERSION |
| 2 | 64 | 4 | PASS_ROOT | 0 | 0 | 0 | 0 | 1096 | PASS_DFT_CONVERSION |
| 4 | 32 | 0 | PASS_ROOT | 0 | 0 | 0 | 0 | 1096 | PASS_DFT_CONVERSION |
| 4 | 32 | 1 | PASS_ROOT | 0 | 0 | 0 | 0 | 1096 | PASS_DFT_CONVERSION |
| 4 | 32 | 2 | PASS_ROOT | 0 | 0 | 0 | 0 | 1096 | PASS_DFT_CONVERSION |
| 4 | 32 | 3 | PASS_ROOT | 0 | 0 | 0 | 0 | 1096 | PASS_DFT_CONVERSION |
| 4 | 32 | 4 | PASS_ROOT | 0 | 0 | 0 | 0 | 1096 | PASS_DFT_CONVERSION |
| 4 | 64 | 0 | PASS_ROOT | 0 | 0 | 0 | 0 | 1096 | PASS_DFT_CONVERSION |
| 4 | 64 | 1 | PASS_ROOT | 0 | 0 | 0 | 0 | 1096 | PASS_DFT_CONVERSION |
| 4 | 64 | 2 | PASS_ROOT | 0 | 0 | 0 | 0 | 1096 | PASS_DFT_CONVERSION |
| 4 | 64 | 3 | PASS_ROOT | 0 | 0 | 0 | 0 | 1096 | PASS_DFT_CONVERSION |
| 4 | 64 | 4 | PASS_ROOT | 0 | 0 | 0 | 0 | 1096 | PASS_DFT_CONVERSION |
| 6 | 32 | 0 | PASS_ROOT | 0 | 0 | 0 | 0 | 1096 | PASS_DFT_CONVERSION |
| 6 | 32 | 1 | PASS_ROOT | 0 | 0 | 0 | 0 | 1096 | PASS_DFT_CONVERSION |
| 6 | 32 | 2 | PASS_ROOT | 0 | 0 | 0 | 0 | 1096 | PASS_DFT_CONVERSION |
| 6 | 32 | 3 | PASS_ROOT | 0 | 0 | 0 | 0 | 1096 | PASS_DFT_CONVERSION |
| 6 | 32 | 4 | PASS_ROOT | 0 | 0 | 0 | 0 | 1096 | PASS_DFT_CONVERSION |
| 6 | 64 | 0 | PASS_ROOT | 0 | 0 | 0 | 0 | 1096 | PASS_DFT_CONVERSION |
| 6 | 64 | 1 | PASS_ROOT | 0 | 0 | 0 | 0 | 1096 | PASS_DFT_CONVERSION |
| 6 | 64 | 2 | PASS_ROOT | 0 | 0 | 0 | 0 | 1096 | PASS_DFT_CONVERSION |
| 6 | 64 | 3 | PASS_ROOT | 0 | 0 | 0 | 0 | 1096 | PASS_DFT_CONVERSION |
| 6 | 64 | 4 | PASS_ROOT | 0 | 0 | 0 | 0 | 1096 | PASS_DFT_CONVERSION |

## Interpretation

This removes one necessary semantic blocker: the vector-shared object can
be represented across an exact frequency-domain conversion boundary.
It still does not prove production FFT behavior, structured selector
application, SAB schedule integration, or complete-SAB speedup.
