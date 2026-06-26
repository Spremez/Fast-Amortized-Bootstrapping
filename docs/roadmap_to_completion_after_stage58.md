# PVW/MAT-SAB Route To Completion After Stage 58

This document is the execution route after the Stage19-58 scoped evidence
closure. It keeps the original goal intact: maximize and audit PVW/MAT-SAB
acceleration without breaking the scalar SAB baseline. It also keeps the
current claim boundary intact: the scoped engineering chain is ready, but
stronger claims remain blocked until native-perf, full-text, and manual-review
evidence is supplied.

| planned stage | lane | objective | gate | current status |
|---|---|---|---|---|
| Stage 59 | completion-route readiness | Convert the post-Stage58 state into a machine-checkable route to completion. | Stage59 CSV decision must be `PASS_COMPLETION_ROUTE_READY__STRONGER_CLAIMS_BLOCKED`. | passed |
| Stage 60 | final-recheck integration | Add Stage59 to the unified final recheck so route readiness cannot become stale before Stage42 closure. | Stage59, Stage57, Stage51, Stage52, and Stage42 must pass in one isolated recheck. | passed |
| Stage 61 | native perf unlock | Run Stage28 with hardware counters on native Linux or perf-enabled WSL. | `hardware_counter_gate=PASS` and `bench_correctness=PASS`. | blocked on current WSL2: `perf` missing |
| Stage 62 | 2025/686 full-text review | Register the 2025/686 full text and map protocol, complexity, noise/security, and citation claims to concrete anchors. | Stage38 must report reviewed full text and claim support must be manually checked. | externally blocked |
| Stage 63 | novelty review | Re-run related-work access and manually map novelty/distinction wording to source anchors. | Novelty gate must no longer be `BLOCK_NOVELTY_CLAIM_PENDING_MANUAL_REVIEW`. | externally blocked |
| Stage 64 | implementation-refresh campaign | After any new code variant, rerun current-head scalar/PVW smoke, repeated full-SAB A/B, and final-output noise gates. | Stage33/47/48/49 and Stage50 must pass; scalar baseline output remains unchanged. | local after code change |
| Stage 65 | optional variant loop | Evaluate a concrete new algorithmic or AVX/layout variant from the hypothesis register. | promote/neutral/reject with full correctness, full SAB A/B, noise, resource, and claim-policy rows. | optional local |
| Stage 66 | release/paper package | Freeze the final allowed claim package after external blockers are resolved or the scope is explicitly narrowed. | final recheck, closure audit, verifier, artifact manifest, and reproduction checklist all pass. | waiting |

Execution policy:

- Do not replace the scalar `sab_rlwe_bootstrap` path.
- Do not claim theoretical MAT-AVX512 optimality without native perf-counter
  evidence.
- Do not cite 2025/686 theorem, algorithm, table, figure, or experiment
  numbers without a registered and reviewed full text.
- Do not claim novelty without manual source-anchor review.
- Treat optional local variants as hypotheses until full SAB A/B and
  correctness/noise/resource gates pass.
