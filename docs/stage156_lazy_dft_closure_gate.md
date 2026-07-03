# Stage156 Lazy-DFT Closure Gate

Decision: `REJECT_STAGE156_NAIVE_LAZY_DFT_STATE_NOT_CLOSED`

Stage156 tests the most direct representation-changing idea after Stage155:
keep the PVW/MAT-SAB accumulator in DFT form and avoid materializing every
CMUX output. The gate rejects only the naive DFT-only state, not all future
representation changes.

## API Scan

| check | status | evidence | detail |
| --- | --- | --- | --- |
| dense_external_product_signature | PASS | mat_trgsw_mul_pvmtmlwe_DFT takes PVW_TMLWE torus input | src/mosfhet/include/mosfhet.h; src/mosfhet/src/mattrgsw.c |
| compact_external_product_signature | PASS | mat_trgsw_compact_mul_pvmtmlwe_DFT also takes PVW_TMLWE torus input | src/mosfhet/include/mosfhet.h; src/mosfhet/src/mattrgsw.c |
| no_dft_input_external_product_api | PASS | No MAT external-product entry point accepts PVW_TMLWE_DFT as the decomposed input state. | regex_scan=mat_trgsw*_mul*DFT(... PVW_TMLWE_DFT in) |
| dense_decomposition_inside_ep | PASS | Dense MAT EP calls pvmtmlwe_decompose before converting digits to DFT. | src/mosfhet/src/mattrgsw.c:673 |
| compact_decomposition_inside_ep | PASS | Compact MAT EP calls polynomial_decompose_i on shared/body torus components. | src/mosfhet/src/mattrgsw.c:853-860 |

## Decomposition Nonlinearity

| config | trials | addition_nonlinear_trials | negation_nonlinear_trials | negacyclic_rotation_nonlinear_trials | status |
| --- | --- | --- | --- | --- | --- |
| Bg_bit=7;l=1;N=8 | 256 | 252 | 21 | 5 | PASS_NEGATIVE_CONTROL |
| Bg_bit=7;l=2;N=8 | 256 | 256 | 37 | 18 | PASS_NEGATIVE_CONTROL |
| Bg_bit=8;l=2;N=16 | 256 | 256 | 30 | 14 | PASS_NEGATIVE_CONTROL |

The toy model exactly mirrors the 64-bit coefficient formula in
`polynomial_decompose_i`: offset, high-bit extraction, mask, and centered
digit subtraction. The negative-control pass means counterexamples were found:
`decompose(x+y) != decompose(x)+decompose(y)`,
`decompose(-x) != -decompose(x)`, and negacyclic sign rotations are not
linearly maintainable on decomposed digits.

## Gate Result

| gate | status | metric | value | next_action |
| --- | --- | --- | --- | --- |
| stage156_precondition | PASS | stage155_summary_exists | repro/stage155_same_format_frontier_refresh/summary.csv | Restore or rerun Stage155 if missing. |
| stage156_api_boundary | PASS | torus_input_ep;no_dft_input_ep;decomp_inside_ep | PASS | Do not plan lazy DFT insertion without a new EP API. |
| stage156_decomposition_closure | PASS_NEGATIVE_CONTROL | add;neg;negacyclic_rotation | nonlinear_counterexamples_found | Reject naive lazy DFT state; use exact torus/decomp cache or compact-state redesign. |
| stage156_decision | REJECT_STAGE156_NAIVE_LAZY_DFT_STATE_NOT_CLOSED | lazy_dft_state_route | naive_lazy_dft_rejected | Stage157 compact/shared-source production microbench or decomposed-cache feasibility |

## Next Queue

| stage | priority | name | goal | performance_gate |
| --- | --- | --- | --- | --- |
| 157 | P0 | decomposed-cache or compact-state feasibility | Test a representation that stores enough exact coefficient/decomposition state to reduce materialization/decomposition cost without relying on linear DFT-only updates. | T_kernel/r must beat current dense MAT EP after cache update overhead. |
| 158 | P1 | native perf/counter attribution refresh | Measure current H14 r=6 path on native Linux to separate memory traffic, FMA throughput, and spills. | Counters explain whether current AVX512 is FMA-bound or memory-bound. |

Interpretation: a DFT accumulator can represent the polynomial value, but the
next MAT external product needs coefficient-domain gadget digits. Because the
digits are nonlinear under the SAB updates, a DFT-only lazy state is not a
closed iterative representation. Future work must store enough exact torus or
decomposed state, or use a compact/shared-source representation with its own
correctness and performance gates.
