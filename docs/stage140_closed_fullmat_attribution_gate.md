# Stage140 Closed Full-MAT Attribution Gate

Date: 2026-07-03

## Decision

`PASS_STAGE140_CLOSED_FULLMAT_DFT_COUNT_LOWER_BOUND_READY_STAGE141`

Stage140 measures the production closed full-MAT external product after Stage139 rejects direct diagonal compact insertion.

## Gates

| gate | status | metric | value | detail |
|---|---|---|---|---|
| stage140_mosfhet_static_build | PASS | make_static_spqlios_pvw | true | MOSFHET static build with PVW/MAT objects. |
| stage140_probe_compile | PASS | gcc_probe_compile | true | Standalone closed full-MAT attribution probe compiled. |
| stage140_probe_run | PASS | probe_returncode | 0 | Closed full-MAT attribution probe executed. |
| stage140_correctness | PASS | correctness_rows | 12 | Split decomp/DFT plus addmul equals production full-MAT DFT output. |
| stage140_attribution_rows | PASS | bench_rows;attr_rows | 180;12 | Current, closed decomp/DFT, and closed addmul timings recorded. |
| stage140_closed_dft_lower_bound | PASS | closed_input_dft_conversions | all_at_(r+1)T | Production closed full-MAT path already reaches the input DFT count lower bound for Torus input state. |
| stage140_decision | PASS_STAGE140_CLOSED_FULLMAT_DFT_COUNT_LOWER_BOUND_READY_STAGE141 | route_policy |  | Stage140 decides the next closed full-MAT optimization route. |

## Attribution

| backend | r | N | T | Bg_bit | seed | current_full_us | decomp_dft_us | addmul_us | split_total_us | split_over_current | decomp_dft_fraction | addmul_fraction | closed_input_dft_conversions | closed_lower_bound | lower_bound_status | dominant_component | next_route |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| spqlios | 2 | 1024 | 1 | 23 | 0 | 7.586940 | 4.241610 | 3.251830 | 7.493440 | 0.987676 | 0.566043 | 0.433957 | 3 | 3 | AT_LOWER_BOUND | MIXED | JOINT_DFT_AND_ADDMUL |
| spqlios | 2 | 1024 | 7 | 7 | 0 | 55.414310 | 30.603330 | 20.887030 | 51.490360 | 0.929189 | 0.594351 | 0.405649 | 21 | 21 | AT_LOWER_BOUND | MIXED | JOINT_DFT_AND_ADDMUL |
| spqlios | 2 | 512 | 1 | 23 | 0 | 5.917770 | 2.499530 | 1.664430 | 4.163960 | 0.703637 | 0.600277 | 0.399723 | 3 | 3 | AT_LOWER_BOUND | DECOMP_DFT_DOMINANT | DFT_BACKEND_OR_LAZY_STATE_REPRESENTATION |
| spqlios | 2 | 512 | 7 | 7 | 0 | 21.449070 | 12.252440 | 8.452680 | 20.705120 | 0.965316 | 0.591759 | 0.408241 | 21 | 21 | AT_LOWER_BOUND | MIXED | JOINT_DFT_AND_ADDMUL |
| spqlios | 4 | 1024 | 1 | 23 | 0 | 14.827660 | 6.603610 | 7.973300 | 14.576910 | 0.983089 | 0.453019 | 0.546981 | 5 | 5 | AT_LOWER_BOUND | MIXED | JOINT_DFT_AND_ADDMUL |
| spqlios | 4 | 1024 | 7 | 7 | 0 | 101.079130 | 45.791530 | 54.193690 | 99.985220 | 0.989178 | 0.457983 | 0.542017 | 35 | 35 | AT_LOWER_BOUND | MIXED | JOINT_DFT_AND_ADDMUL |
| spqlios | 4 | 512 | 1 | 23 | 0 | 7.190870 | 2.923840 | 3.639910 | 6.563750 | 0.912789 | 0.445453 | 0.554547 | 5 | 5 | AT_LOWER_BOUND | MIXED | JOINT_DFT_AND_ADDMUL |
| spqlios | 4 | 512 | 7 | 7 | 0 | 50.601390 | 21.593990 | 28.126200 | 49.720190 | 0.982585 | 0.434310 | 0.565690 | 35 | 35 | AT_LOWER_BOUND | MIXED | JOINT_DFT_AND_ADDMUL |
| spqlios | 6 | 1024 | 1 | 23 | 0 | 25.202640 | 9.179230 | 14.837710 | 24.016940 | 0.952953 | 0.382198 | 0.617802 | 7 | 7 | AT_LOWER_BOUND | ADDMUL_DOMINANT | ADDMUL_AVX_OR_MATRIX_LAYOUT |
| spqlios | 6 | 1024 | 7 | 7 | 0 | 169.670370 | 66.122310 | 111.666280 | 177.788590 | 1.047847 | 0.371915 | 0.628085 | 49 | 49 | AT_LOWER_BOUND | ADDMUL_DOMINANT | ADDMUL_AVX_OR_MATRIX_LAYOUT |
| spqlios | 6 | 512 | 1 | 23 | 0 | 12.378680 | 4.319810 | 7.830380 | 12.150190 | 0.981542 | 0.355534 | 0.644466 | 7 | 7 | AT_LOWER_BOUND | ADDMUL_DOMINANT | ADDMUL_AVX_OR_MATRIX_LAYOUT |
| spqlios | 6 | 512 | 7 | 7 | 0 | 89.653330 | 31.426000 | 56.408200 | 87.834200 | 0.979709 | 0.357788 | 0.642212 | 49 | 49 | AT_LOWER_BOUND | ADDMUL_DOMINANT | ADDMUL_AVX_OR_MATRIX_LAYOUT |
