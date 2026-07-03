# Stage165 Closed Full-MAT Streaming Microbench

Decision: `REJECT_STAGE165_STREAMING_LOSES_TO_CURRENT_TILED_AVX`.

Stage165 tests the Stage164 P0 route without modifying production SAB code.
The current baseline is `mat_trgsw_mul_pvmtmlwe_sub_DFT` compiled with the
r>4 tiled AVX512 path. The candidate streams one decomposed row through DFT and
generic DFT addmul at a time, reducing scratch lifetime but potentially losing
the MAT-aware tiled AVX accumulation.

## Gate Summary

| gate | status | metric | value | evidence | detail | next_action |
| --- | --- | --- | --- | --- | --- | --- |
| stage165_platform | PASS | avx512f | present | repro/stage165_closed_fullmat_streaming_microbench/environment.log | Stage165 compares against the current r=6 tiled AVX512 MAT path. | Use AVX512 platform before interpreting timing. |
| stage165_build_static | PASS | make_static_rc | 0 | repro/stage165_closed_fullmat_streaming_microbench/build_static.log | Build MOSFHET with MAT_TRGSW_AVX512_RGT4_FUSED=true. | Fix build before using timing evidence. |
| stage165_compile_probe | PASS | gcc_rc | 0 | repro/stage165_closed_fullmat_streaming_microbench/compile_probe.log | Compile standalone streaming/full-MAT probe against libmosfhet.a. | Fix compile/link before using timing evidence. |
| stage165_correctness | PASS | torus_mismatches | 0 | repro/stage165_closed_fullmat_streaming_microbench/correctness.csv | Row-streamed DFT output must materialize to the same torus PVW_TMLWE as current all-row MAT EP. | Do not use streaming if torus equivalence fails. |
| stage165_microbench | NEUTRAL_OR_REJECT | current_over_streaming_mean_min | 0.882552056;0.822280730 | repro/stage165_closed_fullmat_streaming_microbench/comparison.csv | Ratio is current_allrow_tiled_avx per-call time divided by streaming_row_generic per-call time. | Only productionize if streaming clearly wins. |
| stage165_decision | REJECT_STAGE165_STREAMING_LOSES_TO_CURRENT_TILED_AVX | closed_fullmat_streaming_route | microbench_only | repro/stage165_closed_fullmat_streaming_microbench/summary.csv | Stage165 decides whether row-streaming deserves production integration. | If rejected, keep current tiled AVX path and move to compact keygen proof or native counters. |

## Correctness

| case | dft_mismatches | max_dft_gap | torus_mismatches | max_torus_gap | status |
| --- | --- | --- | --- | --- | --- |
| streaming_vs_current | 0 | 0.000000000000e+00 | 0 | 0 | PASS_TORUS_EQUIV |

## Benchmark Aggregate

| variant | samples | mean_per_call_us | median_per_call_us | min_per_call_us | max_per_call_us | stdev_per_call_us |
| --- | --- | --- | --- | --- | --- | --- |
| current_allrow_tiled_avx | 5 | 44.190184375 | 46.126117188 | 38.605617188 | 46.201773438 | 3.274498233 |
| streaming_row_generic | 5 | 50.314109375 | 52.934265625 | 43.609554688 | 55.784031250 | 5.258999510 |

## Comparison

| metric | samples | mean | min | max | stdev | meaning |
| --- | --- | --- | --- | --- | --- | --- |
| current_over_streaming | 5 | 0.882552056 | 0.822280730 | 1.005612972 | 0.073925608 | >1 means row-streaming beats current all-row tiled AVX. |
