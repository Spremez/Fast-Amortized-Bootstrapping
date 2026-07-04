# Stage255 MOSFHET Non-Binary Selector Keygen/Noise

Decision: `PASS_STAGE255_MOSFHET_SELECTOR_KEYGEN_NOISE_READY_NONBINARY_SPARSEMUL_PREFLIGHT`.

Stage255 is the first actual MOSFHET-adjacent non-binary selector experiment.
It encrypts MAT `s_coff/s_sign` 0/1 selectors with production
`mat_trgsw_monomial_DFT_sample`, applies `mat_trgsw_mul_pvmtmlwe_DFT` to the
isolated include-zero and ternary `sub_a` equations, and compares rounded phase
against the reference update.

## Probe Results

| branch | r | seed | selector_value | N | prec | a | phase_mismatches | max_phase_gap | mean_phase_gap | selector_keygen_us | external_product_us | status |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| include_zero | 1 | 0 | 0 | 1024 | 3 | 5 | 0 | 22149146288128 | 5228033206827.469 | 133 | 23 | PASS_MOSFHET_SELECTOR_SUBA |
| ternary | 1 | 0 | 0 | 1024 | 3 | 5 | 0 | 18344878964736 | 4782945208567.250 | 187 | 12 | PASS_MOSFHET_SELECTOR_SUBA |
| include_zero | 1 | 0 | 1 | 1024 | 3 | 7 | 0 | 584176755531776 | 271533975013404.250 | 130 | 4 | PASS_MOSFHET_SELECTOR_SUBA |
| ternary | 1 | 0 | 1 | 1024 | 3 | 7 | 0 | 613938194537472 | 305509319568769.500 | 137 | 5 | PASS_MOSFHET_SELECTOR_SUBA |
| include_zero | 1 | 1 | 0 | 1024 | 3 | 15 | 0 | 18208513884160 | 4814708672896.016 | 112 | 5 | PASS_MOSFHET_SELECTOR_SUBA |
| ternary | 1 | 1 | 0 | 1024 | 3 | 15 | 0 | 19465865592832 | 4620705336955.500 | 112 | 5 | PASS_MOSFHET_SELECTOR_SUBA |
| include_zero | 1 | 1 | 1 | 1024 | 3 | 17 | 0 | 594202282901504 | 278500399406573.375 | 112 | 5 | PASS_MOSFHET_SELECTOR_SUBA |
| ternary | 1 | 1 | 1 | 1024 | 3 | 17 | 0 | 586802054191104 | 287973164711713.500 | 112 | 5 | PASS_MOSFHET_SELECTOR_SUBA |
| include_zero | 1 | 2 | 0 | 1024 | 3 | 25 | 0 | 18966575480832 | 4928752843890.188 | 111 | 4 | PASS_MOSFHET_SELECTOR_SUBA |
| ternary | 1 | 2 | 0 | 1024 | 3 | 25 | 0 | 21390010908672 | 4758414299589.688 | 111 | 5 | PASS_MOSFHET_SELECTOR_SUBA |
| include_zero | 1 | 2 | 1 | 1024 | 3 | 27 | 0 | 613944100110336 | 295615903830318.000 | 112 | 6 | PASS_MOSFHET_SELECTOR_SUBA |
| ternary | 1 | 2 | 1 | 1024 | 3 | 27 | 0 | 596291784523776 | 293354574174138.000 | 112 | 4 | PASS_MOSFHET_SELECTOR_SUBA |
| include_zero | 1 | 3 | 0 | 1024 | 3 | 35 | 0 | 18784039436288 | 4726764604075.750 | 110 | 4 | PASS_MOSFHET_SELECTOR_SUBA |
| ternary | 1 | 3 | 0 | 1024 | 3 | 35 | 0 | 19385335119872 | 4485766180094.000 | 112 | 4 | PASS_MOSFHET_SELECTOR_SUBA |
| include_zero | 1 | 3 | 1 | 1024 | 3 | 37 | 0 | 575983031648256 | 278027890063993.000 | 111 | 4 | PASS_MOSFHET_SELECTOR_SUBA |
| ternary | 1 | 3 | 1 | 1024 | 3 | 37 | 0 | 611530328563712 | 294221827277478.500 | 109 | 4 | PASS_MOSFHET_SELECTOR_SUBA |
| include_zero | 1 | 4 | 0 | 1024 | 3 | 45 | 0 | 14396730388480 | 3982973997898.750 | 122 | 4 | PASS_MOSFHET_SELECTOR_SUBA |
| ternary | 1 | 4 | 0 | 1024 | 3 | 45 | 0 | 16789027356672 | 4155432242912.750 | 109 | 6 | PASS_MOSFHET_SELECTOR_SUBA |
| include_zero | 1 | 4 | 1 | 1024 | 3 | 47 | 0 | 574125458239488 | 273815824245621.500 | 109 | 4 | PASS_MOSFHET_SELECTOR_SUBA |
| ternary | 1 | 4 | 1 | 1024 | 3 | 47 | 0 | 598082785968128 | 302150541380958.625 | 110 | 4 | PASS_MOSFHET_SELECTOR_SUBA |
| include_zero | 2 | 0 | 0 | 1024 | 3 | 7 | 0 | 22707492052992 | 5760276234111.062 | 324 | 11 | PASS_MOSFHET_SELECTOR_SUBA |
| ternary | 2 | 0 | 0 | 1024 | 3 | 7 | 0 | 22655952502784 | 5208755671091.812 | 339 | 9 | PASS_MOSFHET_SELECTOR_SUBA |
| include_zero | 2 | 0 | 1 | 1024 | 3 | 9 | 0 | 627941398707200 | 294879677649145.625 | 319 | 11 | PASS_MOSFHET_SELECTOR_SUBA |
| ternary | 2 | 0 | 1 | 1024 | 3 | 9 | 0 | 600526622328832 | 282315011917255.000 | 320 | 10 | PASS_MOSFHET_SELECTOR_SUBA |
| include_zero | 2 | 1 | 0 | 1024 | 3 | 17 | 0 | 22870700851200 | 5994448554234.750 | 381 | 18 | PASS_MOSFHET_SELECTOR_SUBA |
| ternary | 2 | 1 | 0 | 1024 | 3 | 17 | 0 | 29437705977856 | 6931440745755.094 | 433 | 15 | PASS_MOSFHET_SELECTOR_SUBA |
| include_zero | 2 | 1 | 1 | 1024 | 3 | 19 | 0 | 639340241780736 | 304521641973231.750 | 399 | 14 | PASS_MOSFHET_SELECTOR_SUBA |
| ternary | 2 | 1 | 1 | 1024 | 3 | 19 | 0 | 597533030014976 | 284171641009955.188 | 396 | 13 | PASS_MOSFHET_SELECTOR_SUBA |
| include_zero | 2 | 2 | 0 | 1024 | 3 | 27 | 0 | 25065429114880 | 5650522830861.875 | 382 | 12 | PASS_MOSFHET_SELECTOR_SUBA |
| ternary | 2 | 2 | 0 | 1024 | 3 | 27 | 0 | 22840636047360 | 5191994711792.625 | 411 | 42 | PASS_MOSFHET_SELECTOR_SUBA |
| include_zero | 2 | 2 | 1 | 1024 | 3 | 29 | 0 | 622064809543680 | 308397537756644.625 | 394 | 14 | PASS_MOSFHET_SELECTOR_SUBA |
| ternary | 2 | 2 | 1 | 1024 | 3 | 29 | 0 | 560068030455808 | 269858518858907.656 | 416 | 13 | PASS_MOSFHET_SELECTOR_SUBA |
| include_zero | 2 | 3 | 0 | 1024 | 3 | 37 | 0 | 22905060622336 | 5261458662440.938 | 416 | 14 | PASS_MOSFHET_SELECTOR_SUBA |
| ternary | 2 | 3 | 0 | 1024 | 3 | 37 | 0 | 24371792031744 | 5640485338237.812 | 417 | 14 | PASS_MOSFHET_SELECTOR_SUBA |
| include_zero | 2 | 3 | 1 | 1024 | 3 | 39 | 0 | 642252229650432 | 308712463897921.875 | 417 | 13 | PASS_MOSFHET_SELECTOR_SUBA |
| ternary | 2 | 3 | 1 | 1024 | 3 | 39 | 0 | 625574871449600 | 296588472357623.125 | 410 | 12 | PASS_MOSFHET_SELECTOR_SUBA |
| include_zero | 2 | 4 | 0 | 1024 | 3 | 47 | 0 | 20899310911488 | 5354431179826.625 | 396 | 13 | PASS_MOSFHET_SELECTOR_SUBA |
| ternary | 2 | 4 | 0 | 1024 | 3 | 47 | 0 | 33535104630784 | 7464710047658.875 | 422 | 14 | PASS_MOSFHET_SELECTOR_SUBA |
| include_zero | 2 | 4 | 1 | 1024 | 3 | 49 | 0 | 619561917359360 | 284321479411299.625 | 341 | 9 | PASS_MOSFHET_SELECTOR_SUBA |
| ternary | 2 | 4 | 1 | 1024 | 3 | 49 | 0 | 590502168600576 | 271174719251827.375 | 308 | 9 | PASS_MOSFHET_SELECTOR_SUBA |
| include_zero | 4 | 0 | 0 | 1024 | 3 | 11 | 0 | 33861522128896 | 6860923339860.500 | 1064 | 25 | PASS_MOSFHET_SELECTOR_SUBA |
| ternary | 4 | 0 | 0 | 1024 | 3 | 11 | 0 | 30206505074688 | 6898204016283.688 | 1003 | 15 | PASS_MOSFHET_SELECTOR_SUBA |
| include_zero | 4 | 0 | 1 | 1024 | 3 | 13 | 0 | 593620314693632 | 274771114724766.000 | 1014 | 15 | PASS_MOSFHET_SELECTOR_SUBA |
| ternary | 4 | 0 | 1 | 1024 | 3 | 13 | 0 | 600934644269056 | 264209410958770.156 | 1031 | 16 | PASS_MOSFHET_SELECTOR_SUBA |
| include_zero | 4 | 1 | 0 | 1024 | 3 | 21 | 0 | 35757750255616 | 7031675821674.375 | 1142 | 22 | PASS_MOSFHET_SELECTOR_SUBA |
| ternary | 4 | 1 | 0 | 1024 | 3 | 21 | 0 | 38633230786560 | 7715006967917.250 | 1050 | 19 | PASS_MOSFHET_SELECTOR_SUBA |
| include_zero | 4 | 1 | 1 | 1024 | 3 | 23 | 0 | 589922348101632 | 278084802585641.750 | 1034 | 17 | PASS_MOSFHET_SELECTOR_SUBA |
| ternary | 4 | 1 | 1 | 1024 | 3 | 23 | 0 | 624986461077504 | 289415573005719.938 | 1015 | 16 | PASS_MOSFHET_SELECTOR_SUBA |
| include_zero | 4 | 2 | 0 | 1024 | 3 | 31 | 0 | 29570849890304 | 6795686577559.969 | 1038 | 16 | PASS_MOSFHET_SELECTOR_SUBA |
| ternary | 4 | 2 | 0 | 1024 | 3 | 31 | 0 | 33131377655808 | 7401675680806.891 | 1122 | 21 | PASS_MOSFHET_SELECTOR_SUBA |
| include_zero | 4 | 2 | 1 | 1024 | 3 | 33 | 0 | 601295421440000 | 285050406040983.875 | 1096 | 20 | PASS_MOSFHET_SELECTOR_SUBA |
| ternary | 4 | 2 | 1 | 1024 | 3 | 33 | 0 | 639335946797056 | 291523364123479.812 | 1105 | 17 | PASS_MOSFHET_SELECTOR_SUBA |
| include_zero | 4 | 3 | 0 | 1024 | 3 | 41 | 0 | 31194347458560 | 7133153722073.750 | 1061 | 17 | PASS_MOSFHET_SELECTOR_SUBA |
| ternary | 4 | 3 | 0 | 1024 | 3 | 41 | 0 | 29175712907264 | 6456075091734.812 | 1094 | 16 | PASS_MOSFHET_SELECTOR_SUBA |
| include_zero | 4 | 3 | 1 | 1024 | 3 | 43 | 0 | 597077763596288 | 276557689002157.344 | 1031 | 69 | PASS_MOSFHET_SELECTOR_SUBA |
| ternary | 4 | 3 | 1 | 1024 | 3 | 43 | 0 | 617500333053952 | 293561065605158.062 | 1063 | 17 | PASS_MOSFHET_SELECTOR_SUBA |
| include_zero | 4 | 4 | 0 | 1024 | 3 | 51 | 0 | 36659156508672 | 6624250954696.812 | 1738 | 17 | PASS_MOSFHET_SELECTOR_SUBA |
| ternary | 4 | 4 | 0 | 1024 | 3 | 51 | 0 | 35613868883968 | 6836242868640.062 | 1078 | 18 | PASS_MOSFHET_SELECTOR_SUBA |
| include_zero | 4 | 4 | 1 | 1024 | 3 | 53 | 0 | 605070697629696 | 281260249955542.688 | 1015 | 16 | PASS_MOSFHET_SELECTOR_SUBA |
| ternary | 4 | 4 | 1 | 1024 | 3 | 53 | 0 | 600951823906816 | 281939831151714.875 | 1003 | 15 | PASS_MOSFHET_SELECTOR_SUBA |


## Aggregates

| branch | r | samples | phase_mismatches | max_phase_gap | mean_phase_gap_avg | selector_keygen_us_avg | external_product_us_avg | status |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| include_zero | 1 | 10 | 0 | 613944100110336 | 142117522588549.812 | 116.200 | 6.300 | PASS_AGGREGATE |
| include_zero | 2 | 10 | 0 | 642252229650432 | 152885393814971.875 | 376.900 | 12.900 | PASS_AGGREGATE |
| include_zero | 4 | 10 | 0 | 605070697629696 | 143016995272495.688 | 1123.300 | 23.400 | PASS_AGGREGATE |
| ternary | 1 | 10 | 0 | 613938194537472 | 150601269038117.719 | 121.100 | 5.400 | PASS_AGGREGATE |
| ternary | 2 | 10 | 0 | 625574871449600 | 143454574991010.438 | 387.200 | 15.100 | PASS_AGGREGATE |
| ternary | 4 | 10 | 0 | 639335946797056 | 145595644947022.562 | 1056.400 | 17.000 | PASS_AGGREGATE |


## Resource Projection

| r | N | mat_rows | dft_polys_per_selector | double_slots_per_selector | estimated_bytes_per_selector | single_family_target_count_h39 | estimated_target_family_bytes_h39 | interpretation |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 1 | 1024 | 2 | 4 | 4096 | 32768 | 39 | 1277952 | isolated selector DFT storage estimate only |
| 2 | 1024 | 3 | 9 | 9216 | 73728 | 39 | 2875392 | isolated selector DFT storage estimate only |
| 4 | 1024 | 5 | 25 | 25600 | 204800 | 39 | 7987200 | isolated selector DFT storage estimate only |


## Source Isolation

| path | modified_in_stage255 | status | interpretation |
| --- | --- | --- | --- |
| include/sab_pvw.h | no | PASS_UNCHANGED | Stage255 is isolated repro code and must not modify production sources. |
| src/sab_pvw.c | no | PASS_UNCHANGED | Stage255 is isolated repro code and must not modify production sources. |
| src/mosfhet/src/mattrgsw.c | no | PASS_UNCHANGED | Stage255 is isolated repro code and must not modify production sources. |
| src/mosfhet/src/pvwtmlwe.c | no | PASS_UNCHANGED | Stage255 is isolated repro code and must not modify production sources. |


## Admission

| route | decision | production_permission | reason | next_gate |
| --- | --- | --- | --- | --- |
| stage256_nonbinary_sparsemul_preflight | ADMIT_PREFLIGHT | no | actual isolated selector keygen/external-product phase gate passed | design sparse_mul integration boundary and noise/resource recurrence before production code |
| nonbinary_full_sab | BLOCKED | no | no sparse_mul integration, full SAB correctness, multi-seed noise, resource, or T_bootstrap/r benchmark yet | Stage256+ |


## Claim Boundary

| claim | status | allowed_wording | forbidden_wording | evidence |
| --- | --- | --- | --- | --- |
| actual_isolated_selector_keygen | supported_isolated | Actual MOSFHET MAT 0/1 selectors for s_coff/s_sign pass isolated sub_a phase gates. | Non-binary PVW/MAT-SAB production keygen is implemented. | repro/stage255_mosfhet_nonbinary_selector_keygen_noise/selector_noise_probe.csv |
| noise | rounding_phase_gap_only | Stage255 records phase gap statistics under an isolated prototype. | Full non-binary SAB noise is proven acceptable. | repro/stage255_mosfhet_nonbinary_selector_keygen_noise/selector_noise_aggregate.csv |
| speedup | unsupported | No complete-SAB non-binary speedup is claimed. | Non-binary PVW/MAT-SAB accelerates bootstrapping. | repro/stage255_mosfhet_nonbinary_selector_keygen_noise/implementation_admission.csv |


## Proof Gates

| gate | status | metric | value | evidence | interpretation |
| --- | --- | --- | --- | --- | --- |
| G1_inputs_and_stage254 | PASS | inputs;stage254 | true;true | repro/stage255_mosfhet_nonbinary_selector_keygen_noise/input_status.csv; repro/stage254_nonbinary_keygen_noise_preflight/proof_gate.csv | Stage255 is valid only after Stage254 admits isolated prototype. |
| G2_build_compile_run | PASS | build;compile;run | true;true;true | repro/stage255_mosfhet_nonbinary_selector_keygen_noise/mosfhet_static_build.log; repro/stage255_mosfhet_nonbinary_selector_keygen_noise/compile_probe.log; repro/stage255_mosfhet_nonbinary_selector_keygen_noise/run_probe.log | The C probe links and runs against production MOSFHET static library. |
| G3_selector_suba_phase | PASS | probe_rows | 60 | repro/stage255_mosfhet_nonbinary_selector_keygen_noise/selector_noise_probe.csv; repro/stage255_mosfhet_nonbinary_selector_keygen_noise/selector_noise_aggregate.csv | Actual MAT selectors preserve rounded phase for include-zero and ternary isolated updates. |
| G4_source_isolation | PASS | production_source_modified | no | repro/stage255_mosfhet_nonbinary_selector_keygen_noise/source_isolation.csv | Stage255 leaves production SAB/PVW/MOSFHET source unchanged. |
| G5_admission_boundary | PASS_NO_PRODUCTION | production permission | no | repro/stage255_mosfhet_nonbinary_selector_keygen_noise/implementation_admission.csv | Only sparse_mul integration preflight is admitted. |
| G6_stage255_decision | PASS_STAGE255_MOSFHET_SELECTOR_KEYGEN_NOISE_READY_NONBINARY_SPARSEMUL_PREFLIGHT | decision | PASS_STAGE255_MOSFHET_SELECTOR_KEYGEN_NOISE_READY_NONBINARY_SPARSEMUL_PREFLIGHT | repro/stage255_mosfhet_nonbinary_selector_keygen_noise/proof_gate.csv | Proceed to non-binary sparse_mul preflight, not full SAB. |


## Next Queue

| priority | route | entry_condition | gate | status | failure_action | evidence |
| --- | --- | --- | --- | --- | --- | --- |
| P0 | stage256_nonbinary_sparsemul_preflight | Stage255 actual isolated selector keygen/noise gate passes. | design sparse_mul integration boundary, selector family lifecycle, and schedule/noise recurrence | selected_next | keep non-binary PVW unsupported | repro/stage255_mosfhet_nonbinary_selector_keygen_noise/implementation_admission.csv |
| P1 | stage257_nonbinary_sparsemul_implementation | Stage256 admits production-adjacent isolated integration | implement explicit sab_pvw_nonbinary_* path, not default scalar or binary path | conditional | do not modify hot path | repro/stage255_mosfhet_nonbinary_selector_keygen_noise/claim_boundary.csv |
| P2 | stage258_nonbinary_full_sab_ab | sparse_mul integration passes correctness/noise/resource | complete-SAB T_bootstrap/r, multi-seed correctness/noise, resource, scalar default isolation | future_gated | no non-binary speedup claim | repro/stage255_mosfhet_nonbinary_selector_keygen_noise/claim_boundary.csv |


Generated from head `167c2ef`.
