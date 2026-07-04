# V246-A: selected_binary_exact_dense_baseline

## Summary

- Parent algorithm: 2025/686 sparse amortized bootstrapping with PVW/MAT-SAB.
- Focused module: r-body MAT-RLWE exact dense PVW/MAT-SAB for selected binary parameter rows.
- Optimization target: complete-SAB T_bootstrap/r.
- Status labels: `BASELINE_SUPPORTED_SCOPED`.
- Main hypothesis: not an optimality theorem; dense MAT can scale poorly with r.

## Mathematical Definition

The variant is evaluated against the scalar repeated baseline using the
amortized endpoint:

```text
A_variant(r) = T_variant_complete_bootstrap(r) / r
speedup(r) = A_scalar_repeated(r) / A_variant(r)
```

No candidate may replace this metric with isolated external-product throughput.

## Pseudocode

```text
Input: r scalar lanes or an admitted r-body MAT-RLWE state
Output: r bootstrapped lanes or a proof-prototype decision
1. Check candidate admission status.
2. If status is blocked or rejected, stop before production SAB edits.
3. If proof-prototype-only, run the finite/proof gate against a dense reference.
4. If the proof gate passes, then and only then design a full-SAB A/B test.
```

## Delta From Original Algorithm

| Original component | Variant component | Relationship | Evidence/status |
| --- | --- | --- | --- |
| scalar repeated SAB | r-body MAT-RLWE exact dense PVW/MAT-SAB for selected binary parameter rows | candidate admission | BASELINE_SUPPORTED_SCOPED |

## Complexity Change

- Time: not claimable until the required gate passes.
- Memory: must be reported with key size, keygen time, and RSS for any future speedup.
- Communication or IO: not a separate claim in the current codebase.
- What must be measured: rerun full-SAB A/B if executable hot path or benchmark semantics change.

## Theory Dependencies

- Inherited assumptions: scalar SAB and selected binary exact dense PVW/MAT-SAB gates.
- Relaxed/new assumptions: candidate-specific and currently not fully proven unless marked baseline.
- Proof steps affected: phase equivalence, selector semantics, noise, and lower-bound gap.
- New lemmas needed: see Stage246 proof obligations.
- Current status: BASELINE_SUPPORTED_SCOPED.

## Potential Failure Reasons

- Failure mode: not an optimality theorem; dense MAT can scale poorly with r.
- Trigger condition: required proof or experiment gate fails.
- How to detect: run the candidate's Stage246 experiment gate.
- Mitigation or follow-up: rerun full-SAB A/B if executable hot path or benchmark semantics change.

## Required Experiments

| gate_id | experiment | baseline | metric | success | failure | status |
| --- | --- | --- | --- | --- | --- | --- |
| E246-1 | full-SAB A/B after code changes | repeated scalar SAB same backend and same lane count | T_bootstrap/r, noise failures, key size, keygen, RSS | positive mean speedup with CI lower bound above 1 and no worse failure rate | speedup <= 1, correctness/noise regression, or unreported resource side cost | not_needed_until_code_delta |


## Paper Contribution Candidate

`keep_as_baseline_for_future_variants`. This is not a paper-level broader SAB claim unless the
listed theory, correctness, noise, resource, and complete-SAB gates pass.


# V246-B: nonbinary_exact_pvw_sab

## Summary

- Parent algorithm: 2025/686 sparse amortized bootstrapping with PVW/MAT-SAB.
- Focused module: ternary/include-zero PVW/MAT-SAB exact route.
- Optimization target: not applicable until phase invariant exists.
- Status labels: `BLOCKED_NO_SELECTOR_SEMANTICS`.
- Main hypothesis: scalar ternary branches do not imply PVW selector/key semantics.

## Mathematical Definition

The variant is evaluated against the scalar repeated baseline using the
amortized endpoint:

```text
A_variant(r) = T_variant_complete_bootstrap(r) / r
speedup(r) = A_scalar_repeated(r) / A_variant(r)
```

No candidate may replace this metric with isolated external-product throughput.

## Pseudocode

```text
Input: r scalar lanes or an admitted r-body MAT-RLWE state
Output: r bootstrapped lanes or a proof-prototype decision
1. Check candidate admission status.
2. If status is blocked or rejected, stop before production SAB edits.
3. If proof-prototype-only, run the finite/proof gate against a dense reference.
4. If the proof gate passes, then and only then design a full-SAB A/B test.
```

## Delta From Original Algorithm

| Original component | Variant component | Relationship | Evidence/status |
| --- | --- | --- | --- |
| scalar repeated SAB | ternary/include-zero PVW/MAT-SAB exact route | candidate admission | BLOCKED_NO_SELECTOR_SEMANTICS |

## Complexity Change

- Time: not claimable until the required gate passes.
- Memory: must be reported with key size, keygen time, and RSS for any future speedup.
- Communication or IO: not a separate claim in the current codebase.
- What must be measured: selector semantics preflight: define sign/coefficient mapping, staged phase invariant, noise/resource plan.

## Theory Dependencies

- Inherited assumptions: scalar SAB and selected binary exact dense PVW/MAT-SAB gates.
- Relaxed/new assumptions: candidate-specific and currently not fully proven unless marked baseline.
- Proof steps affected: phase equivalence, selector semantics, noise, and lower-bound gap.
- New lemmas needed: see Stage246 proof obligations.
- Current status: BLOCKED_NO_SELECTOR_SEMANTICS.

## Potential Failure Reasons

- Failure mode: scalar ternary branches do not imply PVW selector/key semantics.
- Trigger condition: required proof or experiment gate fails.
- How to detect: run the candidate's Stage246 experiment gate.
- Mitigation or follow-up: selector semantics preflight: define sign/coefficient mapping, staged phase invariant, noise/resource plan.

## Required Experiments

| gate_id | experiment | baseline | metric | success | failure | status |
| --- | --- | --- | --- | --- | --- | --- |
| E246-2 | non-binary selector semantics staged equivalence | scalar ternary/include-zero SAB branch | per-step phase equivalence and final-output correctness | r=1/2/4 staged phase equivalence plus full-SAB deterministic pass | any undefined selector semantics or phase mismatch | blocked_before_experiment |


## Paper Contribution Candidate

`do_not_implement_hot_path`. This is not a paper-level broader SAB claim unless the
listed theory, correctness, noise, resource, and complete-SAB gates pass.


# V246-C: generic_shared_output_compact_mat

## Summary

- Parent algorithm: 2025/686 sparse amortized bootstrapping with PVW/MAT-SAB.
- Focused module: drop dense MAT rows/off-lane terms with the existing key distribution.
- Optimization target: not admissible.
- Status labels: `REJECT_GENERIC_COMPACT`.
- Main hypothesis: finite-field counterexamples show random dense selectors are not representable by lane-local shared-output compact structure.

## Mathematical Definition

The variant is evaluated against the scalar repeated baseline using the
amortized endpoint:

```text
A_variant(r) = T_variant_complete_bootstrap(r) / r
speedup(r) = A_scalar_repeated(r) / A_variant(r)
```

No candidate may replace this metric with isolated external-product throughput.

## Pseudocode

```text
Input: r scalar lanes or an admitted r-body MAT-RLWE state
Output: r bootstrapped lanes or a proof-prototype decision
1. Check candidate admission status.
2. If status is blocked or rejected, stop before production SAB edits.
3. If proof-prototype-only, run the finite/proof gate against a dense reference.
4. If the proof gate passes, then and only then design a full-SAB A/B test.
```

## Delta From Original Algorithm

| Original component | Variant component | Relationship | Evidence/status |
| --- | --- | --- | --- |
| scalar repeated SAB | drop dense MAT rows/off-lane terms with the existing key distribution | candidate admission | REJECT_GENERIC_COMPACT |

## Complexity Change

- Time: not claimable until the required gate passes.
- Memory: must be reported with key size, keygen time, and RSS for any future speedup.
- Communication or IO: not a separate claim in the current codebase.
- What must be measured: none for generic route; replace with structured keygen design.

## Theory Dependencies

- Inherited assumptions: scalar SAB and selected binary exact dense PVW/MAT-SAB gates.
- Relaxed/new assumptions: candidate-specific and currently not fully proven unless marked baseline.
- Proof steps affected: phase equivalence, selector semantics, noise, and lower-bound gap.
- New lemmas needed: see Stage246 proof obligations.
- Current status: REJECT_GENERIC_COMPACT.

## Potential Failure Reasons

- Failure mode: finite-field counterexamples show random dense selectors are not representable by lane-local shared-output compact structure.
- Trigger condition: required proof or experiment gate fails.
- How to detect: run the candidate's Stage246 experiment gate.
- Mitigation or follow-up: none for generic route; replace with structured keygen design.

## Required Experiments

| gate_id | experiment | baseline | metric | success | failure | status |
| --- | --- | --- | --- | --- | --- | --- |
| E246-3 | generic compact exactness probe | dense MAT selector finite-field action | mismatch count | zero mismatches for required selector family | existing counterexamples remain | rejected_by_existing_counterexamples |


## Paper Contribution Candidate

`rejected_as_algorithm_candidate`. This is not a paper-level broader SAB claim unless the
listed theory, correctness, noise, resource, and complete-SAB gates pass.


# V246-D: structured_compact_keygen_noise_route

## Summary

- Parent algorithm: 2025/686 sparse amortized bootstrapping with PVW/MAT-SAB.
- Focused module: new selector/key distribution that makes compact shared-output/state exact.
- Optimization target: proof prototype first; later full-SAB T_bootstrap/r if admitted.
- Status labels: `ADMIT_PROOF_PROTOTYPE_ONLY`.
- Main hypothesis: new key distribution may break security/noise assumptions or fail phase equivalence.

## Mathematical Definition

The variant is evaluated against the scalar repeated baseline using the
amortized endpoint:

```text
A_variant(r) = T_variant_complete_bootstrap(r) / r
speedup(r) = A_scalar_repeated(r) / A_variant(r)
```

No candidate may replace this metric with isolated external-product throughput.

## Pseudocode

```text
Input: r scalar lanes or an admitted r-body MAT-RLWE state
Output: r bootstrapped lanes or a proof-prototype decision
1. Check candidate admission status.
2. If status is blocked or rejected, stop before production SAB edits.
3. If proof-prototype-only, run the finite/proof gate against a dense reference.
4. If the proof gate passes, then and only then design a full-SAB A/B test.
```

## Delta From Original Algorithm

| Original component | Variant component | Relationship | Evidence/status |
| --- | --- | --- | --- |
| scalar repeated SAB | new selector/key distribution that makes compact shared-output/state exact | candidate admission | ADMIT_PROOF_PROTOTYPE_ONLY |

## Complexity Change

- Time: not claimable until the required gate passes.
- Memory: must be reported with key size, keygen time, and RSS for any future speedup.
- Communication or IO: not a separate claim in the current codebase.
- What must be measured: finite r=2 algebra simulator plus toy phase/noise recurrence; no production SAB edits.

## Theory Dependencies

- Inherited assumptions: scalar SAB and selected binary exact dense PVW/MAT-SAB gates.
- Relaxed/new assumptions: candidate-specific and currently not fully proven unless marked baseline.
- Proof steps affected: phase equivalence, selector semantics, noise, and lower-bound gap.
- New lemmas needed: see Stage246 proof obligations.
- Current status: ADMIT_PROOF_PROTOTYPE_ONLY.

## Potential Failure Reasons

- Failure mode: new key distribution may break security/noise assumptions or fail phase equivalence.
- Trigger condition: required proof or experiment gate fails.
- How to detect: run the candidate's Stage246 experiment gate.
- Mitigation or follow-up: finite r=2 algebra simulator plus toy phase/noise recurrence; no production SAB edits.

## Required Experiments

| gate_id | experiment | baseline | metric | success | failure | status |
| --- | --- | --- | --- | --- | --- | --- |
| E246-4 | finite r=2 structured compact keygen/noise prototype | dense MAT finite algebra reference | phase equivalence, off-lane zero proof rows, toy noise recurrence | proof-prototype passes before production code | cannot satisfy off-lane zero/security/noise obligations | selected_next_executable_gate |


## Paper Contribution Candidate

`allow_stage248_finite_algebra_and_toy_noise_probe`. This is not a paper-level broader SAB claim unless the
listed theory, correctness, noise, resource, and complete-SAB gates pass.


# V246-E: mat_rlwe_optimality_lower_bound_route

## Summary

- Parent algorithm: 2025/686 sparse amortized bootstrapping with PVW/MAT-SAB.
- Focused module: lower-bound and gap model for exact/compact r-body MAT-RLWE SAB.
- Optimization target: gap(r)=A_impl(r)/A_lower(r), with A_impl=T_bootstrap/r.
- Status labels: `ADMIT_MODEL_AND_COUNTER_GAP_ONLY`.
- Main hypothesis: counter attribution does not prove lower-bound tightness.

## Mathematical Definition

The variant is evaluated against the scalar repeated baseline using the
amortized endpoint:

```text
A_variant(r) = T_variant_complete_bootstrap(r) / r
speedup(r) = A_scalar_repeated(r) / A_variant(r)
```

No candidate may replace this metric with isolated external-product throughput.

## Pseudocode

```text
Input: r scalar lanes or an admitted r-body MAT-RLWE state
Output: r bootstrapped lanes or a proof-prototype decision
1. Check candidate admission status.
2. If status is blocked or rejected, stop before production SAB edits.
3. If proof-prototype-only, run the finite/proof gate against a dense reference.
4. If the proof gate passes, then and only then design a full-SAB A/B test.
```

## Delta From Original Algorithm

| Original component | Variant component | Relationship | Evidence/status |
| --- | --- | --- | --- |
| scalar repeated SAB | lower-bound and gap model for exact/compact r-body MAT-RLWE SAB | candidate admission | ADMIT_MODEL_AND_COUNTER_GAP_ONLY |

## Complexity Change

- Time: not claimable until the required gate passes.
- Memory: must be reported with key size, keygen time, and RSS for any future speedup.
- Communication or IO: not a separate claim in the current codebase.
- What must be measured: derive measurable lower-bound rows and attach native counter/assembly evidence.

## Theory Dependencies

- Inherited assumptions: scalar SAB and selected binary exact dense PVW/MAT-SAB gates.
- Relaxed/new assumptions: candidate-specific and currently not fully proven unless marked baseline.
- Proof steps affected: phase equivalence, selector semantics, noise, and lower-bound gap.
- New lemmas needed: see Stage246 proof obligations.
- Current status: ADMIT_MODEL_AND_COUNTER_GAP_ONLY.

## Potential Failure Reasons

- Failure mode: counter attribution does not prove lower-bound tightness.
- Trigger condition: required proof or experiment gate fails.
- How to detect: run the candidate's Stage246 experiment gate.
- Mitigation or follow-up: derive measurable lower-bound rows and attach native counter/assembly evidence.

## Required Experiments

| gate_id | experiment | baseline | metric | success | failure | status |
| --- | --- | --- | --- | --- | --- | --- |
| E246-5 | lower-bound gap table with counter/assembly rows | current exact dense implementation | A_impl/A_lower plus cycles/load/store/FMA attribution | gap terms measurable and conservative; no unsupported optimality claim | lower bound too loose or counters not tied to implementation | analysis_gate |


## Paper Contribution Candidate

`analysis_plus_counter_refresh_only`. This is not a paper-level broader SAB claim unless the
listed theory, correctness, noise, resource, and complete-SAB gates pass.
