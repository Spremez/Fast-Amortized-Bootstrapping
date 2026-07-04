# Stage273 Sub_a From_DFT_Add Alias Microtest

Decision: `PASS_STAGE273_SUB_A_ALIAS_MICROTEST_ENABLES_FLAGGED_SMOKE`.

Stage273 is an isolated microtest for the Stage272 non-binary `sub_a`
materialization candidate. It does not change the default SAB/PVW hot path and
does not claim full bootstrapping speedup.

## Alias Helper Results

| variant | case | k | r | N | mismatches | gate |
| --- | --- | --- | --- | --- | --- | --- |
| backend_from_dft_add | out_distinct | 1 | 4 | 1024 | 0 | Pass |
| backend_from_dft_add | out_equals_addend | 1 | 4 | 1024 | 0 | Pass |
| default | out_distinct | 1 | 4 | 1024 | 0 | Pass |
| default | out_equals_addend | 1 | 4 | 1024 | 5120 | Fail |

## Sub_a Equivalence

| variant | mode | r | in_N | mismatches | gate |
| --- | --- | --- | --- | --- | --- |
| backend_from_dft_add | include_zero | 4 | 16 | 0 | Pass |
| backend_from_dft_add | ternary | 4 | 16 | 0 | Pass |

## Proof Gate

| gate | status | metric | value | interpretation |
| --- | --- | --- | --- | --- |
| G1_default_distinct | PASS | default out!=addend | 0 | Portable fallback remains correct when output and addend are distinct. |
| G2_default_alias_negative_control | PASS_NEGATIVE_CONTROL | default out==addend | 5120 | Portable fallback is not alias-safe, so in-place sub_a fusion must not use it. |
| G3_backend_alias_helper | PASS | backend out==addend | 0 | Backend direct add helper is alias-safe in this deterministic PVW_TMLWE microtest. |
| G4_backend_include_zero_sub_a | PASS | include-zero sub_a exact equivalence | 0 | Alias materialization preserves include-zero sub_a state for r=4 fixture. |
| G5_backend_ternary_sub_a | PASS | ternary sub_a exact equivalence | 0 | Alias materialization preserves ternary sub_a state for r=4 fixture. |
| G6_exit_codes | PASS | run exit | default=0; backend=0 | Both microtest binaries completed. |
| G7_claim_boundary | PASS_MICROTEST_ONLY | claim scope | no full SAB speed claim | Stage273 only gates a candidate implementation path. |
| G8_decision | PASS_STAGE273_SUB_A_ALIAS_MICROTEST_ENABLES_FLAGGED_SMOKE | stage decision | PASS_STAGE273_SUB_A_ALIAS_MICROTEST_ENABLES_FLAGGED_SMOKE | Proceed only to an explicit-flag Stage274 smoke when this decision is PASS. |

## Claim Boundary

| claim | status | allowed_wording | forbidden_wording |
| --- | --- | --- | --- |
| backend_from_dft_add_alias_safety | microtest_supported | The backend direct-add helper passed deterministic out==addend PVW_TMLWE alias testing. | All from_DFT_add implementations are alias-safe. |
| sub_a_alias_equivalence | microtest_supported | A local alias-materialized sub_a candidate exactly matched reference include-zero and ternary sub_a on the Stage273 r=4 fixture. | The full SAB path is faster or fully correct after this stage. |
| default_fallback_alias | negative_control | The portable fallback failed out==addend alias testing and must not be used in-place. | The default fallback can be used for sub_a in-place fusion. |
| full_bootstrap_speedup | not_tested | Stage274 must test full SAB T_bootstrap/r under an explicit flag. | Stage273 proves a SAB acceleration. |

## Next Queue

| priority | route | entry_condition | gate | status | failure_action |
| --- | --- | --- | --- | --- | --- |
| P0 | stage274_sub_a_fused_materialization_smoke | Stage273 backend alias and sub_a equivalence gates passed. | Add an explicit `SAB_PVW_SUBA_FUSED_FROM_DFT_ADD` flag; run correctness plus r=4 include-zero/ternary full SAB T_bootstrap/r smoke. | selected | If full SAB is neutral or negative, close S272-A as microtest-only and do not default-enable. |
| P1 | stage275_sub_a_fused_repeated_noise_resource | Only if Stage274 smoke is positive. | Repeated timing, noise/resource, and claim-boundary check. | conditional | Demote to neutral if repeated or noise/resource gates fail. |

## Fixture Note

The `sub_a` equivalence fixture uses a Stage273-only sparse secret fixture that
fills the input key coefficients without computing input-key DFT tables. This
keeps the microtest focused on `sub_a` selector materialization and avoids
mixing unsupported tiny input-ring DFT behavior into the alias-safety gate. The
PVW/MAT ciphertext ring used by the tested helper is `N=1024`, `r=4`.

Generated from input head `073641b`.
