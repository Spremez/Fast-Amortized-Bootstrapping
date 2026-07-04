# Stage251 Non-Binary Selector Semantics

Decision: `PASS_STAGE251_NONBINARY_SELECTOR_SEMANTICS_PREFLIGHT_BLOCKS_IMPLEMENTATION`.

Stage251 prevents non-binary PVW/MAT-SAB work from drifting into unsafe
implementation. It identifies the scalar ternary/include-zero equations,
checks a finite rotation model, audits current PVW source support, and blocks
production implementation until a selector/key skeleton exists.

## Source Fact Matrix

| fact_id | source | expected | observed | status | pass_meaning | evidence |
| --- | --- | --- | --- | --- | --- | --- |
| scalar_has_coff_selector | include/sab.h; src/sparse_amortized_bootstrap.c | TRGSW_DFT ** s_coff and scalar include-zero/gaussian use | yes | present | present | include/sab.h; src/sparse_amortized_bootstrap.c |
| scalar_has_sign_selector | include/sab.h; src/sparse_amortized_bootstrap.c | TRGSW_DFT ** s_sign and scalar ternary use | yes | present | present | include/sab.h; src/sparse_amortized_bootstrap.c |
| scalar_records_branch_flags | include/sab.h; src/sparse_amortized_bootstrap.c | include_zeros, gaussian_secret, ternary_secret branch flags | yes | present | present | include/sab.h; src/sparse_amortized_bootstrap.c |
| scalar_ternary_sign_equation_source | src/sparse_amortized_bootstrap.c | s_sign encrypts coeff == -1 and sub_a consumes s_sign | yes | present | present | src/sparse_amortized_bootstrap.c |
| scalar_include_zero_equation_source | src/sparse_amortized_bootstrap.c | s_coff controls identity versus X^a rotation | yes | present | present | src/sparse_amortized_bootstrap.c |
| pvw_has_binary_selector_matrix | include/sab_pvw.h | MAT_TRGSW_DFT *** s | yes | present | present | include/sab_pvw.h |
| pvw_has_sign_selector | include/sab_pvw.h; src/sab_pvw.c | MAT selector equivalent of s_sign | no | missing | missing | include/sab_pvw.h; src/sab_pvw.c |
| pvw_has_coff_selector | include/sab_pvw.h; src/sab_pvw.c | MAT selector equivalent of s_coff | no | missing | missing | include/sab_pvw.h; src/sab_pvw.c |
| pvw_constructor_rejects_nonbinary_coeff | src/sab_pvw.c | if(coeff != 1) reject | yes | present | present | src/sab_pvw.c |
| pvw_target_harness_binary_guard | main.c | #if !defined(BINARY) guard for SAB_PVW target harness | yes | present | present | main.c |
| pvw_binary_sub_a_only | src/sab_pvw.c; include/sab_pvw.h | sab_pvw_sub_a_binary rotates by X^a without sign/presence selector | yes | present | present | src/sab_pvw.c; include/sab_pvw.h |


## Semantic Equation Matrix

| branch | selector | scalar_update | pvw_required_update | existing_pvw_support | extra_key_material | risk |
| --- | --- | --- | --- | --- | --- | --- |
| binary | implicit nonzero coefficient +1 | p' = X^a p | body[q]' = X^a body[q] for every lane q | yes_binary_only | none beyond binary MAT_TRGSW selector s | covered by existing binary equivalence gates |
| include_zero | s_coff in {0,1} | p' = p + s_coff * ((X^a - 1)p) | body[q]' = body[q] + s_coff * ((X^a - 1)body[q]) | no | MAT_TRGSW_DFT selector family for s_coff | missing selector storage, keygen, noise recurrence, and equivalence tests |
| ternary_positive | s_sign = 0 | p' = X^a p | body[q]' = X^a body[q] | only when sign is known positive; harness disallows ternary | MAT_TRGSW_DFT selector family for sign bits | cannot claim branch support without sign selector and negative case |
| ternary_negative | s_sign = 1 | p' = X^a p + s_sign * ((X^{-2a} - 1)X^a p) = X^{-a}p | body[q]' = X^{-a} body[q] | no | MAT_TRGSW_DFT sign selector and negative-rotation CMUX composition | binary PVW X^a path is wrong for negative coefficients |
| gaussian_or_general | coefficient monomial selector | p' depends on encrypted coefficient monomial, not just sign/presence | general MAT selector/key-format design | no | beyond Stage251 scope | more complex than ternary/include-zero and not admitted |


## Selector Gap Matrix

| gap | required_for | current_scalar | current_pvw | blocking_fact | required_next_evidence | production_permission |
| --- | --- | --- | --- | --- | --- | --- |
| ternary_sign_selector_key_material | ternary negative coefficient support | s_sign TRGSW_DFT family exists | no s_sign equivalent in SAB_PVW_Key | missing | PVW/MAT sign selector key skeleton, isolated phase equivalence, full-SAB A/B, noise/resource | no |
| include_zero_coefficient_selector_key_material | include-zero sparse secret support | s_coff TRGSW_DFT family exists | no s_coff equivalent in SAB_PVW_Key | missing | PVW/MAT coefficient selector key skeleton, isolated phase equivalence, full-SAB A/B, noise/resource | no |
| constructor_and_harness_admission | any non-binary PVW benchmark or target gate | scalar ternary build is preserved by Stage26 | constructor rejects coeff != 1 and target harness requires BINARY | binary guard present | explicit non-binary PVW harness after selector semantics are implemented | no |
| gaussian_general_coefficient_semantics | gaussian/general secret branches | sub_a_ga uses coefficient monomial semantics | no general coefficient selector design | out_of_scope | separate general coefficient MAT selector design and noise proof | no |


## Finite Semantics Probe

The finite probe uses length-16 cyclic rotations as a selector-semantics
sanity check. It is deliberately not a security or full-SAB proof.

Rows: `96`. All rows must start with `PASS`.

## Admission Decision

| route | decision | production_permission | allowed_next_step | required_before_speed_claim |
| --- | --- | --- | --- | --- |
| binary_exact_dense_pvw | already_supported_scoped | yes_existing_explicit_path | continue scoped exact dense binary reporting or counter-backed exact improvements | same-backend complete-SAB T_bootstrap/r, noise, resource |
| ternary_pvw | BLOCKED_KEY_FORMAT_AND_SELECTOR_GAP | no | Stage252 non-production MAT sign-selector key skeleton | selector keygen, isolated equivalence, full-SAB A/B, noise/resource |
| include_zero_pvw | BLOCKED_KEY_FORMAT_AND_SELECTOR_GAP | no | Stage252 non-production MAT coefficient-selector key skeleton | selector keygen, isolated equivalence, full-SAB A/B, noise/resource |
| gaussian_or_general_pvw | OUT_OF_SCOPE_MORE_COMPLEX_COEFFICIENT_MONOMIAL | no | separate theory/design stage only after ternary/include-zero | general coefficient equations, key format, noise recurrence, full-SAB evidence |


## Claim Boundary

| claim | status | allowed_wording | forbidden_wording | evidence |
| --- | --- | --- | --- | --- |
| scalar_nonbinary_semantics_identified | supported_preflight | Scalar SAB has identifiable ternary and include-zero selector semantics through s_sign and s_coff. | Scalar equations alone prove PVW non-binary correctness. | repro/stage251_nonbinary_selector_semantics/semantic_equation_matrix.csv |
| pvw_nonbinary_support | unsupported_blocked | PVW/MAT-SAB non-binary support is not implemented; current target harness is binary-only. | PVW/MAT-SAB supports ternary or include-zero branches. | repro/stage251_nonbinary_selector_semantics/selector_gap_matrix.csv |
| finite_probe_result | toy_semantics_only | Finite rotation probes confirm the selector equations and the binary negative-control failure. | Toy finite equations prove full SAB correctness or security. | repro/stage251_nonbinary_selector_semantics/finite_semantics_probe.csv |
| implementation_permission | denied_for_production | Only non-production selector/key skeleton design is admitted next. | Remove binary guards or route non-binary inputs through sab_pvw_sub_a_binary. | repro/stage251_nonbinary_selector_semantics/admission_decision.csv |


## Proof Gates

| gate | status | metric | value | evidence | interpretation |
| --- | --- | --- | --- | --- | --- |
| G1_inputs | PASS | required inputs | all present | repro/stage251_nonbinary_selector_semantics/input_status.csv | Stage251 consumes Stage26/229/250 branch and claim ledgers plus source files. |
| G2_scalar_semantics | PASS | s_coff/s_sign equations | identified | repro/stage251_nonbinary_selector_semantics/semantic_equation_matrix.csv | Scalar include-zero and ternary semantics are concrete enough for a PVW design target. |
| G3_finite_semantics_probe | PASS | finite rotation rows | 96 | repro/stage251_nonbinary_selector_semantics/finite_semantics_probe.csv | Positive equations pass and binary negative-control fails as expected. |
| G4_pvw_source_gap | PASS_BLOCKED | PVW selector/key gap | no s_sign/s_coff, binary guard present | repro/stage251_nonbinary_selector_semantics/source_fact_matrix.csv | Current PVW code cannot implement non-binary semantics without a new key format. |
| G5_production_admission | PASS_NO_IMPLEMENTATION | production permission | denied | repro/stage251_nonbinary_selector_semantics/admission_decision.csv | Do not remove binary guards or map non-binary into the binary PVW path. |
| G6_stage251_decision | PASS_STAGE251_NONBINARY_SELECTOR_SEMANTICS_PREFLIGHT_BLOCKS_IMPLEMENTATION | decision | PASS_STAGE251_NONBINARY_SELECTOR_SEMANTICS_PREFLIGHT_BLOCKS_IMPLEMENTATION | repro/stage251_nonbinary_selector_semantics/proof_gate.csv | Proceed only to a non-production selector/key skeleton stage. |


## Next Queue

| priority | route | entry_condition | gate | status | failure_action | evidence |
| --- | --- | --- | --- | --- | --- | --- |
| P0 | stage252_nonbinary_mat_selector_key_skeleton | Stage251 identifies scalar equations and blocks current PVW production implementation. | define MAT s_sign/s_coff key/storage/API skeleton without touching sab_pvw hot path | selected_next | keep non-binary PVW unsupported | repro/stage251_nonbinary_selector_semantics/selector_gap_matrix.csv |
| P1 | stage253_isolated_nonbinary_pvw_sub_a_equivalence | Stage252 skeleton compiles and records key/storage semantics. | finite and MOSFHET-adjacent isolated sub_a equivalence for include-zero and ternary negative cases | conditional | reject non-binary PVW branch implementation | repro/stage251_nonbinary_selector_semantics/finite_semantics_probe.csv |
| P2 | stage254_nonbinary_full_sab_ab_noise_resource | isolated equivalence passes and production code is explicitly admitted | same-backend complete-SAB T_bootstrap/r, noise, resource, scalar default isolation | future_gated | do not claim non-binary bootstrapping speedup | repro/stage251_nonbinary_selector_semantics/admission_decision.csv |


Generated from head `727e736`.
