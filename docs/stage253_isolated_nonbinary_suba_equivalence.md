# Stage253 Isolated Non-Binary Sub_A Equivalence

Decision: `PASS_STAGE253_ISOLATED_NONBINARY_SUBA_EQUIVALENCE_READY_KEYGEN_NOISE_PREFLIGHT`.

Stage253 validates the Stage252 selector/key skeleton in a finite negacyclic
multi-lane model. It checks include-zero and ternary `sub_a` equations for
r=1/2/4 independent body lanes and records binary-naive negative controls.

## Equation Model

| branch | selector_family | scalar_equation | lane_equation | selector_values | negative_control |
| --- | --- | --- | --- | --- | --- |
| include_zero | s_coff | p' = p + c((X^a - 1)p) | body[q]' = body[q] + c((X^a - 1)body[q]) | c=0 identity; c=1 X^a | binary X^a must fail on c=0 nonfixed states |
| ternary | s_sign | p1=X^a p; p'=p1 + s((X^{-2a}-1)p1) | body[q]' equals X^a body[q] when s=0 and X^-a body[q] when s=1 | s=0 positive; s=1 negative | binary X^a must fail on s=1 nonfixed states |


## Lane Equivalence Probe

| branch | r | seed | N | steps | positive_mismatches | formula_mismatches | negative_controls_checked | negative_control_unexpected_matches | status |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| include_zero | 1 | 0 | 64 | 16 | 0 | 0 | 8 | 0 | PASS_LANE_EQUIVALENCE |
| include_zero | 1 | 1 | 64 | 16 | 0 | 0 | 8 | 0 | PASS_LANE_EQUIVALENCE |
| include_zero | 1 | 2 | 64 | 16 | 0 | 0 | 8 | 0 | PASS_LANE_EQUIVALENCE |
| include_zero | 1 | 3 | 64 | 16 | 0 | 0 | 8 | 0 | PASS_LANE_EQUIVALENCE |
| include_zero | 1 | 4 | 64 | 16 | 0 | 0 | 8 | 0 | PASS_LANE_EQUIVALENCE |
| include_zero | 1 | 5 | 64 | 16 | 0 | 0 | 8 | 0 | PASS_LANE_EQUIVALENCE |
| include_zero | 1 | 6 | 64 | 16 | 0 | 0 | 8 | 0 | PASS_LANE_EQUIVALENCE |
| include_zero | 1 | 7 | 64 | 16 | 0 | 0 | 8 | 0 | PASS_LANE_EQUIVALENCE |
| include_zero | 1 | 8 | 64 | 16 | 0 | 0 | 8 | 0 | PASS_LANE_EQUIVALENCE |
| include_zero | 1 | 9 | 64 | 16 | 0 | 0 | 8 | 0 | PASS_LANE_EQUIVALENCE |
| include_zero | 2 | 0 | 64 | 16 | 0 | 0 | 16 | 0 | PASS_LANE_EQUIVALENCE |
| include_zero | 2 | 1 | 64 | 16 | 0 | 0 | 16 | 0 | PASS_LANE_EQUIVALENCE |
| include_zero | 2 | 2 | 64 | 16 | 0 | 0 | 16 | 0 | PASS_LANE_EQUIVALENCE |
| include_zero | 2 | 3 | 64 | 16 | 0 | 0 | 16 | 0 | PASS_LANE_EQUIVALENCE |
| include_zero | 2 | 4 | 64 | 16 | 0 | 0 | 16 | 0 | PASS_LANE_EQUIVALENCE |
| include_zero | 2 | 5 | 64 | 16 | 0 | 0 | 16 | 0 | PASS_LANE_EQUIVALENCE |
| include_zero | 2 | 6 | 64 | 16 | 0 | 0 | 16 | 0 | PASS_LANE_EQUIVALENCE |
| include_zero | 2 | 7 | 64 | 16 | 0 | 0 | 16 | 0 | PASS_LANE_EQUIVALENCE |
| include_zero | 2 | 8 | 64 | 16 | 0 | 0 | 16 | 0 | PASS_LANE_EQUIVALENCE |
| include_zero | 2 | 9 | 64 | 16 | 0 | 0 | 16 | 0 | PASS_LANE_EQUIVALENCE |
| include_zero | 4 | 0 | 64 | 16 | 0 | 0 | 32 | 0 | PASS_LANE_EQUIVALENCE |
| include_zero | 4 | 1 | 64 | 16 | 0 | 0 | 32 | 0 | PASS_LANE_EQUIVALENCE |
| include_zero | 4 | 2 | 64 | 16 | 0 | 0 | 32 | 0 | PASS_LANE_EQUIVALENCE |
| include_zero | 4 | 3 | 64 | 16 | 0 | 0 | 32 | 0 | PASS_LANE_EQUIVALENCE |
| include_zero | 4 | 4 | 64 | 16 | 0 | 0 | 32 | 0 | PASS_LANE_EQUIVALENCE |
| include_zero | 4 | 5 | 64 | 16 | 0 | 0 | 32 | 0 | PASS_LANE_EQUIVALENCE |
| include_zero | 4 | 6 | 64 | 16 | 0 | 0 | 32 | 0 | PASS_LANE_EQUIVALENCE |
| include_zero | 4 | 7 | 64 | 16 | 0 | 0 | 32 | 0 | PASS_LANE_EQUIVALENCE |
| include_zero | 4 | 8 | 64 | 16 | 0 | 0 | 32 | 0 | PASS_LANE_EQUIVALENCE |
| include_zero | 4 | 9 | 64 | 16 | 0 | 0 | 32 | 0 | PASS_LANE_EQUIVALENCE |
| ternary | 1 | 0 | 64 | 16 | 0 | 0 | 8 | 0 | PASS_LANE_EQUIVALENCE |
| ternary | 1 | 1 | 64 | 16 | 0 | 0 | 8 | 0 | PASS_LANE_EQUIVALENCE |
| ternary | 1 | 2 | 64 | 16 | 0 | 0 | 8 | 0 | PASS_LANE_EQUIVALENCE |
| ternary | 1 | 3 | 64 | 16 | 0 | 0 | 8 | 0 | PASS_LANE_EQUIVALENCE |
| ternary | 1 | 4 | 64 | 16 | 0 | 0 | 8 | 0 | PASS_LANE_EQUIVALENCE |
| ternary | 1 | 5 | 64 | 16 | 0 | 0 | 8 | 0 | PASS_LANE_EQUIVALENCE |
| ternary | 1 | 6 | 64 | 16 | 0 | 0 | 8 | 0 | PASS_LANE_EQUIVALENCE |
| ternary | 1 | 7 | 64 | 16 | 0 | 0 | 8 | 0 | PASS_LANE_EQUIVALENCE |
| ternary | 1 | 8 | 64 | 16 | 0 | 0 | 8 | 0 | PASS_LANE_EQUIVALENCE |
| ternary | 1 | 9 | 64 | 16 | 0 | 0 | 8 | 0 | PASS_LANE_EQUIVALENCE |
| ternary | 2 | 0 | 64 | 16 | 0 | 0 | 16 | 0 | PASS_LANE_EQUIVALENCE |
| ternary | 2 | 1 | 64 | 16 | 0 | 0 | 16 | 0 | PASS_LANE_EQUIVALENCE |
| ternary | 2 | 2 | 64 | 16 | 0 | 0 | 16 | 0 | PASS_LANE_EQUIVALENCE |
| ternary | 2 | 3 | 64 | 16 | 0 | 0 | 16 | 0 | PASS_LANE_EQUIVALENCE |
| ternary | 2 | 4 | 64 | 16 | 0 | 0 | 16 | 0 | PASS_LANE_EQUIVALENCE |
| ternary | 2 | 5 | 64 | 16 | 0 | 0 | 16 | 0 | PASS_LANE_EQUIVALENCE |
| ternary | 2 | 6 | 64 | 16 | 0 | 0 | 16 | 0 | PASS_LANE_EQUIVALENCE |
| ternary | 2 | 7 | 64 | 16 | 0 | 0 | 16 | 0 | PASS_LANE_EQUIVALENCE |
| ternary | 2 | 8 | 64 | 16 | 0 | 0 | 16 | 0 | PASS_LANE_EQUIVALENCE |
| ternary | 2 | 9 | 64 | 16 | 0 | 0 | 16 | 0 | PASS_LANE_EQUIVALENCE |
| ternary | 4 | 0 | 64 | 16 | 0 | 0 | 32 | 0 | PASS_LANE_EQUIVALENCE |
| ternary | 4 | 1 | 64 | 16 | 0 | 0 | 32 | 0 | PASS_LANE_EQUIVALENCE |
| ternary | 4 | 2 | 64 | 16 | 0 | 0 | 32 | 0 | PASS_LANE_EQUIVALENCE |
| ternary | 4 | 3 | 64 | 16 | 0 | 0 | 32 | 0 | PASS_LANE_EQUIVALENCE |
| ternary | 4 | 4 | 64 | 16 | 0 | 0 | 32 | 0 | PASS_LANE_EQUIVALENCE |
| ternary | 4 | 5 | 64 | 16 | 0 | 0 | 32 | 0 | PASS_LANE_EQUIVALENCE |
| ternary | 4 | 6 | 64 | 16 | 0 | 0 | 32 | 0 | PASS_LANE_EQUIVALENCE |
| ternary | 4 | 7 | 64 | 16 | 0 | 0 | 32 | 0 | PASS_LANE_EQUIVALENCE |
| ternary | 4 | 8 | 64 | 16 | 0 | 0 | 32 | 0 | PASS_LANE_EQUIVALENCE |
| ternary | 4 | 9 | 64 | 16 | 0 | 0 | 32 | 0 | PASS_LANE_EQUIVALENCE |


## Negative Controls

| branch | r | seed | negative_controls_checked | unexpected_matches | status |
| --- | --- | --- | --- | --- | --- |
| include_zero | 1 | 0 | 8 | 0 | PASS_NEGATIVE_CONTROL |
| include_zero | 1 | 1 | 8 | 0 | PASS_NEGATIVE_CONTROL |
| include_zero | 1 | 2 | 8 | 0 | PASS_NEGATIVE_CONTROL |
| include_zero | 1 | 3 | 8 | 0 | PASS_NEGATIVE_CONTROL |
| include_zero | 1 | 4 | 8 | 0 | PASS_NEGATIVE_CONTROL |
| include_zero | 1 | 5 | 8 | 0 | PASS_NEGATIVE_CONTROL |
| include_zero | 1 | 6 | 8 | 0 | PASS_NEGATIVE_CONTROL |
| include_zero | 1 | 7 | 8 | 0 | PASS_NEGATIVE_CONTROL |
| include_zero | 1 | 8 | 8 | 0 | PASS_NEGATIVE_CONTROL |
| include_zero | 1 | 9 | 8 | 0 | PASS_NEGATIVE_CONTROL |
| include_zero | 2 | 0 | 16 | 0 | PASS_NEGATIVE_CONTROL |
| include_zero | 2 | 1 | 16 | 0 | PASS_NEGATIVE_CONTROL |
| include_zero | 2 | 2 | 16 | 0 | PASS_NEGATIVE_CONTROL |
| include_zero | 2 | 3 | 16 | 0 | PASS_NEGATIVE_CONTROL |
| include_zero | 2 | 4 | 16 | 0 | PASS_NEGATIVE_CONTROL |
| include_zero | 2 | 5 | 16 | 0 | PASS_NEGATIVE_CONTROL |
| include_zero | 2 | 6 | 16 | 0 | PASS_NEGATIVE_CONTROL |
| include_zero | 2 | 7 | 16 | 0 | PASS_NEGATIVE_CONTROL |
| include_zero | 2 | 8 | 16 | 0 | PASS_NEGATIVE_CONTROL |
| include_zero | 2 | 9 | 16 | 0 | PASS_NEGATIVE_CONTROL |
| include_zero | 4 | 0 | 32 | 0 | PASS_NEGATIVE_CONTROL |
| include_zero | 4 | 1 | 32 | 0 | PASS_NEGATIVE_CONTROL |
| include_zero | 4 | 2 | 32 | 0 | PASS_NEGATIVE_CONTROL |
| include_zero | 4 | 3 | 32 | 0 | PASS_NEGATIVE_CONTROL |
| include_zero | 4 | 4 | 32 | 0 | PASS_NEGATIVE_CONTROL |
| include_zero | 4 | 5 | 32 | 0 | PASS_NEGATIVE_CONTROL |
| include_zero | 4 | 6 | 32 | 0 | PASS_NEGATIVE_CONTROL |
| include_zero | 4 | 7 | 32 | 0 | PASS_NEGATIVE_CONTROL |
| include_zero | 4 | 8 | 32 | 0 | PASS_NEGATIVE_CONTROL |
| include_zero | 4 | 9 | 32 | 0 | PASS_NEGATIVE_CONTROL |
| ternary | 1 | 0 | 8 | 0 | PASS_NEGATIVE_CONTROL |
| ternary | 1 | 1 | 8 | 0 | PASS_NEGATIVE_CONTROL |
| ternary | 1 | 2 | 8 | 0 | PASS_NEGATIVE_CONTROL |
| ternary | 1 | 3 | 8 | 0 | PASS_NEGATIVE_CONTROL |
| ternary | 1 | 4 | 8 | 0 | PASS_NEGATIVE_CONTROL |
| ternary | 1 | 5 | 8 | 0 | PASS_NEGATIVE_CONTROL |
| ternary | 1 | 6 | 8 | 0 | PASS_NEGATIVE_CONTROL |
| ternary | 1 | 7 | 8 | 0 | PASS_NEGATIVE_CONTROL |
| ternary | 1 | 8 | 8 | 0 | PASS_NEGATIVE_CONTROL |
| ternary | 1 | 9 | 8 | 0 | PASS_NEGATIVE_CONTROL |
| ternary | 2 | 0 | 16 | 0 | PASS_NEGATIVE_CONTROL |
| ternary | 2 | 1 | 16 | 0 | PASS_NEGATIVE_CONTROL |
| ternary | 2 | 2 | 16 | 0 | PASS_NEGATIVE_CONTROL |
| ternary | 2 | 3 | 16 | 0 | PASS_NEGATIVE_CONTROL |
| ternary | 2 | 4 | 16 | 0 | PASS_NEGATIVE_CONTROL |
| ternary | 2 | 5 | 16 | 0 | PASS_NEGATIVE_CONTROL |
| ternary | 2 | 6 | 16 | 0 | PASS_NEGATIVE_CONTROL |
| ternary | 2 | 7 | 16 | 0 | PASS_NEGATIVE_CONTROL |
| ternary | 2 | 8 | 16 | 0 | PASS_NEGATIVE_CONTROL |
| ternary | 2 | 9 | 16 | 0 | PASS_NEGATIVE_CONTROL |
| ternary | 4 | 0 | 32 | 0 | PASS_NEGATIVE_CONTROL |
| ternary | 4 | 1 | 32 | 0 | PASS_NEGATIVE_CONTROL |
| ternary | 4 | 2 | 32 | 0 | PASS_NEGATIVE_CONTROL |
| ternary | 4 | 3 | 32 | 0 | PASS_NEGATIVE_CONTROL |
| ternary | 4 | 4 | 32 | 0 | PASS_NEGATIVE_CONTROL |
| ternary | 4 | 5 | 32 | 0 | PASS_NEGATIVE_CONTROL |
| ternary | 4 | 6 | 32 | 0 | PASS_NEGATIVE_CONTROL |
| ternary | 4 | 7 | 32 | 0 | PASS_NEGATIVE_CONTROL |
| ternary | 4 | 8 | 32 | 0 | PASS_NEGATIVE_CONTROL |
| ternary | 4 | 9 | 32 | 0 | PASS_NEGATIVE_CONTROL |


## Trace Sample

| branch | r | seed | step | lane | a | selector | before_head | after_head | status |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| include_zero | 1 | 0 | 0 | 0 | 4 | 0 | 184 218 254 35 | 184 218 254 35 | PASS |
| include_zero | 1 | 0 | 1 | 0 | 11 | 1 | 184 218 254 35 | 141 1 116 229 | PASS |
| include_zero | 1 | 0 | 2 | 0 | 18 | 0 | 141 1 116 229 | 141 1 116 229 | PASS |
| include_zero | 1 | 0 | 3 | 0 | 25 | 1 | 141 1 116 229 | 164 74 239 145 | PASS |
| include_zero | 1 | 0 | 4 | 0 | 32 | 0 | 164 74 239 145 | 164 74 239 145 | PASS |
| include_zero | 1 | 0 | 5 | 0 | 39 | 1 | 164 74 239 145 | 116 256 141 28 | PASS |
| include_zero | 1 | 0 | 6 | 0 | 46 | 0 | 116 256 141 28 | 116 256 141 28 | PASS |
| include_zero | 1 | 0 | 7 | 0 | 53 | 1 | 116 256 141 28 | 184 218 254 35 | PASS |
| include_zero | 1 | 0 | 8 | 0 | 60 | 0 | 184 218 254 35 | 184 218 254 35 | PASS |
| include_zero | 1 | 0 | 9 | 0 | 67 | 1 | 184 218 254 35 | 7 163 64 73 | PASS |
| include_zero | 1 | 0 | 10 | 0 | 74 | 0 | 7 163 64 73 | 7 163 64 73 | PASS |
| include_zero | 1 | 0 | 11 | 0 | 81 | 1 | 7 163 64 73 | 26 161 37 168 | PASS |
| include_zero | 1 | 0 | 12 | 0 | 88 | 0 | 26 161 37 168 | 26 161 37 168 | PASS |
| include_zero | 1 | 0 | 13 | 0 | 95 | 1 | 26 161 37 168 | 11 71 133 197 | PASS |
| include_zero | 1 | 0 | 14 | 0 | 102 | 0 | 11 71 133 197 | 11 71 133 197 | PASS |
| include_zero | 1 | 0 | 15 | 0 | 109 | 1 | 11 71 133 197 | 208 49 149 251 | PASS |
| include_zero | 1 | 1 | 0 | 0 | 17 | 1 | 199 236 18 59 | 12 138 5 127 | PASS |
| include_zero | 1 | 1 | 1 | 0 | 24 | 0 | 12 138 5 127 | 12 138 5 127 | PASS |
| include_zero | 1 | 1 | 2 | 0 | 31 | 1 | 12 138 5 127 | 254 185 114 41 | PASS |
| include_zero | 1 | 1 | 3 | 0 | 38 | 0 | 254 185 114 41 | 254 185 114 41 | PASS |
| include_zero | 1 | 1 | 4 | 0 | 45 | 1 | 254 185 114 41 | 114 221 73 184 | PASS |
| include_zero | 1 | 1 | 5 | 0 | 52 | 0 | 114 221 73 184 | 114 221 73 184 | PASS |
| include_zero | 1 | 1 | 6 | 0 | 59 | 1 | 114 221 73 184 | 102 242 123 2 | PASS |
| include_zero | 1 | 1 | 7 | 0 | 66 | 0 | 102 242 123 2 | 102 242 123 2 | PASS |


## Source Isolation

| path | modified_in_stage253 | status | interpretation |
| --- | --- | --- | --- |
| include/sab_pvw.h | no | PASS_UNCHANGED | Stage253 must remain an isolated equivalence model. |
| src/sab_pvw.c | no | PASS_UNCHANGED | Stage253 must remain an isolated equivalence model. |
| include/sab.h | no | PASS_UNCHANGED | Stage253 must remain an isolated equivalence model. |
| src/sparse_amortized_bootstrap.c | no | PASS_UNCHANGED | Stage253 must remain an isolated equivalence model. |


## Admission

| route | decision | production_permission | allowed_next_step | blocked_before |
| --- | --- | --- | --- | --- |
| isolated_suba_equivalence | PASSED_FINITE_MODEL | no | Stage254 encrypted selector keygen/noise/resource preflight | production keygen; full sparse_mul; full SAB; speed claim |
| include_zero_pvw | EQUIVALENCE_MODEL_ONLY | no | MAT s_coff keygen/noise design | MOSFHET encrypted keygen and complete SAB |
| ternary_pvw | EQUIVALENCE_MODEL_ONLY | no | MAT s_sign keygen/noise design | MOSFHET encrypted keygen and complete SAB |


## Claim Boundary

| claim | status | allowed_wording | forbidden_wording | evidence |
| --- | --- | --- | --- | --- |
| isolated_sub_a_equivalence | supported_finite_model | Finite negacyclic lane model matches scalar include-zero and ternary sub_a equations for r=1/2/4. | Full non-binary PVW-SAB correctness is proven. | repro/stage253_isolated_nonbinary_suba_equivalence/lane_equivalence_probe.csv |
| binary_negative_control | supported | Naive binary X^a update fails on required c=0/sign=1 controls. | Binary sab_pvw_sub_a can be reused unchanged for non-binary branches. | repro/stage253_isolated_nonbinary_suba_equivalence/negative_control_matrix.csv |
| nonbinary_speedup | unsupported | No non-binary speedup is claimed. | Non-binary PVW/MAT-SAB accelerates complete bootstrapping. | repro/stage253_isolated_nonbinary_suba_equivalence/admission_decision.csv |


## Proof Gates

| gate | status | metric | value | evidence | interpretation |
| --- | --- | --- | --- | --- | --- |
| G1_inputs_and_stage252 | PASS | inputs;stage252 | true;true | repro/stage253_isolated_nonbinary_suba_equivalence/input_status.csv; repro/stage252_nonbinary_mat_selector_key_skeleton/proof_gate.csv | Stage253 is valid only after Stage252 selector/key skeleton passes. |
| G2_lane_equivalence | PASS | probe_rows | 60 | repro/stage253_isolated_nonbinary_suba_equivalence/lane_equivalence_probe.csv | Every include-zero/ternary lane-state row matches scalar reference. |
| G3_negative_controls | PASS | negative_rows | 60 | repro/stage253_isolated_nonbinary_suba_equivalence/negative_control_matrix.csv | Naive binary update fails where non-binary selectors require identity or inverse rotation. |
| G4_source_isolation | PASS | production_source_modified | no | repro/stage253_isolated_nonbinary_suba_equivalence/source_isolation.csv | No production SAB/PVW source changes are made. |
| G5_admission_boundary | PASS_NO_PRODUCTION | production_permission | no | repro/stage253_isolated_nonbinary_suba_equivalence/admission_decision.csv | Equivalence model admits keygen/noise preflight only. |
| G6_stage253_decision | PASS_STAGE253_ISOLATED_NONBINARY_SUBA_EQUIVALENCE_READY_KEYGEN_NOISE_PREFLIGHT | decision | PASS_STAGE253_ISOLATED_NONBINARY_SUBA_EQUIVALENCE_READY_KEYGEN_NOISE_PREFLIGHT | repro/stage253_isolated_nonbinary_suba_equivalence/proof_gate.csv | Proceed to encrypted selector keygen/noise preflight, not full SAB implementation. |


## Next Queue

| priority | route | entry_condition | gate | status | failure_action | evidence |
| --- | --- | --- | --- | --- | --- | --- |
| P0 | stage254_nonbinary_selector_keygen_noise_preflight | Stage253 finite lane equivalence and negative controls pass. | define encrypted MAT s_coff/s_sign keygen, noise/resource model, and source admission policy | selected_next | keep non-binary PVW unsupported | repro/stage253_isolated_nonbinary_suba_equivalence/lane_equivalence_probe.csv |
| P1 | stage255_nonbinary_mosfhet_isolated_suba | Stage254 keygen/noise preflight admits production-adjacent code | MOSFHET-adjacent isolated sub_a with actual MAT_TRGSW selectors | conditional | no full SAB integration | repro/stage253_isolated_nonbinary_suba_equivalence/admission_decision.csv |
| P2 | stage256_nonbinary_full_sab | actual selector keygen and isolated MOSFHET equivalence pass | complete-SAB T_bootstrap/r, multi-seed correctness/noise, resource | future_gated | no non-binary speedup claim | repro/stage253_isolated_nonbinary_suba_equivalence/claim_boundary.csv |


Generated from head `3dac5c7`.
