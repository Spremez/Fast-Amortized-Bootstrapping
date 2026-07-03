# Stage163 From-DFT Backend Batching Microbench

Decision: `NEUTRAL_STAGE163_BACKEND_ADD_ALREADY_DOMINANT_BATCHING_NOT_PROMOTED`.

Stage163 is deliberately scoped to backend wall-time. It does not reduce the
Stage160/Stage162 `573440` from_DFT materialization count and therefore cannot
be reported as an algorithmic materialization-count reduction.

## Gate Summary

| gate | status | metric | value | evidence | detail | next_action |
| --- | --- | --- | --- | --- | --- | --- |
| stage163_platform | PASS | avx512f | present | repro/stage163_from_dft_batching_microbench/environment.log | Stage163 is a spqlios_avx512 backend microbench. | Use native/WSL AVX512 host before interpreting this gate. |
| stage163_build_static | PASS | make_static_rc | 0 | repro/stage163_from_dft_batching_microbench/build_static.log | Build MOSFHET static library with FFT_LIB=spqlios_avx512. | Fix build before using timing evidence. |
| stage163_compile_probe | PASS | gcc_rc | 0 | repro/stage163_from_dft_batching_microbench/compile_probe.log | Compile a standalone probe linked to current libmosfhet.a. | Fix probe or link flags before using timing evidence. |
| stage163_correctness | PASS | mismatches | backend_current_order=0;backend_component_major=0 | repro/stage163_from_dft_batching_microbench/correctness.csv | Backend-add and component-major batching must match separate DFT-to-torus plus add exactly. | Do not promote any batching variant if correctness fails. |
| stage163_backend_add_microbench | PASS | backend_add_over_separate_mean | 1.052919655 | repro/stage163_from_dft_batching_microbench/comparison.csv | Confirms whether current execute_direct_torus64_add remains useful relative to separate add. | Keep scoped as backend wall-time evidence, not algorithmic count reduction. |
| stage163_batching_microbench | NEUTRAL | component_major_batch_over_backend_current_mean_min | 0.972807930;0.886311773 | repro/stage163_from_dft_batching_microbench/comparison.csv | Tests whether a batched component-major loop order improves over current item-major backend-add order. | Only integrate into full SAB if this gate is clearly positive. |
| stage163_decision | NEUTRAL_STAGE163_BACKEND_ADD_ALREADY_DOMINANT_BATCHING_NOT_PROMOTED | from_dft_backend_batching_route | backend_wall_time_only | repro/stage163_from_dft_batching_microbench/summary.csv | Stage163 separates backend batching from materialization-count reduction. | If neutral/rejected, route to representation-changing exact-state designs rather than repeat backend batching. |

## Benchmark Aggregate

| variant | samples | mean_per_call_us | median_per_call_us | min_per_call_us | max_per_call_us | stdev_per_call_us |
| --- | --- | --- | --- | --- | --- | --- |
| backend_component_major | 7 | 4.939254172 | 4.920389695 | 4.590388021 | 5.362848400 | 0.235850012 |
| backend_current_order | 7 | 4.808909545 | 4.572520089 | 4.452941406 | 5.839283854 | 0.501378938 |
| separate_current_order | 7 | 5.048559497 | 4.926841332 | 4.686420945 | 5.805748884 | 0.398134034 |

## Comparisons

| metric | samples | mean | min | max | stdev | meaning |
| --- | --- | --- | --- | --- | --- | --- |
| backend_add_over_separate | 7 | 1.052919655 | 0.980410621 | 1.127946411 | 0.055198583 | >1 means execute_direct_torus64_add beats DFT_to_torus plus explicit add. |
| component_major_batch_over_backend_current | 7 | 0.972807930 | 0.886311773 | 1.088840000 | 0.075002153 | >1 means component-major batching beats current item-major backend add order. |

## Interpretation

- `backend_add_over_separate > 1` means the existing
  `execute_direct_torus64_add` callback is faster than `DFT_to_torus` followed
  by a separate torus add pass.
- `component_major_batch_over_backend_current > 1` means a component-major
  batched loop order improves over the current item-major backend-add order.
- A positive Stage163 result only authorizes a later full-SAB A/B gate; it
  does not by itself change `sab_pvw_*` production behavior.
