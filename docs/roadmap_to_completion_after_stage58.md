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
| Stage 62 | 2025/686 full-text review | Register the 2025/686 full text and map protocol, complexity, noise/security, and citation claims to concrete anchors. | Stage38 must report reviewed full text and claim support must be manually checked. | blocked on current network path: direct routes 403/Cloudflare and no local full text |
| Stage 63 | novelty review | Re-run related-work access and manually map novelty/distinction wording to source anchors. | Novelty gate must no longer be `BLOCK_NOVELTY_CLAIM_PENDING_MANUAL_REVIEW`. | externally blocked |
| Stage 64 | implementation-refresh campaign | After any new code variant, rerun current-head scalar/PVW smoke, repeated full-SAB A/B, and final-output noise gates. | Stage33/47/48/49 and Stage50 must pass; scalar baseline output remains unchanged. | passed after Stage65A code change |
| Stage 65 | optional variant loop | Evaluate a concrete new algorithmic or AVX/layout variant from the hypothesis register. | promote/neutral/reject with full correctness, full SAB A/B, noise, resource, and claim-policy rows. | started locally; Stage65A r4 row-unrolled AVX512 is negative/not promoted |
| Stage 66A | post-variant final recheck | Refresh the lightweight final-recheck control plane after Stage65A and Stage64A, then rebuild Stage42 closure with Stage66A registered. | Stage66A summary, Stage42 closure, and verifier must pass while stronger blockers remain preserved. | passed |
| Stage 67 | final-recheck Stage66A integration | Add an explicit final-recheck switch that runs Stage66A without recursion, then rebuild Stage42 closure after the Stage67 summary is finalized. | Stage67 final recheck, post-summary Stage42 closure, and verifier must pass while stronger blockers remain preserved. | passed |
| Stage 68 | frontier/closure consistency | Make Stage42, Stage51 G6, Stage57, and Stage59 agree on the latest control-plane closure label after Stage67. | Stage68 consistency audit, Stage42 closure, and verifier must pass while stronger blockers remain preserved. | passed |
| Stage 69 | local variant feasibility | Decide whether any remaining local H2/H3/H4/H7/H8 candidate is ready for new code after Stage65A and Stage68. | Stage69 CSV decision must be `PASS_LOCAL_VARIANT_FEASIBILITY_AUDIT_STRONGER_CLAIMS_BLOCKED`. | passed |
| Stage 70 | external unlock preflight | Make native-perf, full-text, novelty-review, and local-variant unlock requirements machine-checkable after Stage69. | Stage70 decision must be `PASS_EXTERNAL_UNLOCK_PREFLIGHT_STRONGER_CLAIMS_BLOCKED`. | passed |
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
- After any optional local variant, run Stage64A for current-head continuity,
  Stage66A for final-recheck/control-plane continuity, and Stage67 to verify
  the unified final recheck can refresh that state before relying on updated
  scoped evidence. Run Stage68 after changing closure/frontier labels so the
  completion frontier returns to `LOCAL_READY`.
- Before adding another optional local variant, run Stage69 or an equivalent
  feasibility audit so code work starts from a falsifiable hypothesis rather
  than from a previously neutral or blocked direction.
- After Stage69, run Stage70 to confirm whether external native-perf,
  full-text, novelty-review, or new-hypothesis prerequisites are now available.
