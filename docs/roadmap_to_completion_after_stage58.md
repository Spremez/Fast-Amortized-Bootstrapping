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
| Stage 65 | optional variant loop | Evaluate a concrete new algorithmic or AVX/layout variant from the hypothesis register. | promote/neutral/reject with full correctness, full SAB A/B, noise, resource, and claim-policy rows. | passed for Stage65A; r4 row-unrolled AVX512 is negative/not promoted |
| Stage 66A | post-variant final recheck | Refresh the lightweight final-recheck control plane after Stage65A and Stage64A, then rebuild Stage42 closure with Stage66A registered. | Stage66A summary, Stage42 closure, and verifier must pass while stronger blockers remain preserved. | passed |
| Stage 67 | final-recheck Stage66A integration | Add an explicit final-recheck switch that runs Stage66A without recursion, then rebuild Stage42 closure after the Stage67 summary is finalized. | Stage67 final recheck, post-summary Stage42 closure, and verifier must pass while stronger blockers remain preserved. | passed |
| Stage 68 | frontier/closure consistency | Make Stage42, Stage51 G6, Stage57, and Stage59 agree on the latest control-plane closure label through the Stage71 refresh. | Stage68 consistency audit, Stage42 closure, and verifier must pass while stronger blockers remain preserved. | passed |
| Stage 69 | local variant feasibility | Decide whether any remaining local H2/H3/H4/H7/H8 candidate is ready for new code after Stage65A and Stage68. | Stage69 CSV decision must be `PASS_LOCAL_VARIANT_FEASIBILITY_AUDIT_STRONGER_CLAIMS_BLOCKED`. | passed |
| Stage 70 | external unlock preflight | Make native-perf, full-text, novelty-review, and local-variant unlock requirements machine-checkable after Stage69. | Stage70 decision must be `PASS_EXTERNAL_UNLOCK_PREFLIGHT_STRONGER_CLAIMS_BLOCKED`. | passed |
| Stage 71 | final-recheck Stage70 integration | Make Stage70 refreshable through the unified final recheck before Stage42 closure. | Stage71 decision must be `PASS_FINAL_RECHECK_STAGE70_INTEGRATION`. | passed |
| Stage 72 | external source refresh | Refresh current author/DOI/code/full-text routes for 2025/686 after Stage71. | Stage72 decision must be `PASS_EXTERNAL_SOURCE_REFRESH_STRONGER_CLAIMS_BLOCKED`. | passed |
| Stage 73 | final-recheck Stage72 integration | Make Stage72 refreshable through the unified final recheck before blocker/frontier/closure rebuilds. | Stage73 decision must be `PASS_FINAL_RECHECK_STAGE72_INTEGRATION`. | passed |
| Stage 74 | r-scaling boundary | Test direct r=6/r=8 lane-count expansion under the current active-buffer MAT path. | Stage74 decision must be `PASS_R_GT4_BOUNDARY_RECORDED_NOT_PROMOTED` unless a full-gate promotion candidate emerges. | passed as negative/not promoted |
| Stage 75 | r>4 profile boundary | Attribute the Stage74 r>4 boundary with exact body-profile counts and component timing. | Stage75 decision must be `PASS_RGT4_PROFILE_BOUNDARY_RECORDED_NOT_PROMOTED` unless profile evidence opens a new promotion candidate. | passed as profile-backed negative/not promoted |
| Stage 76 | r>4 kernel feasibility | Test whether the current generic r=6/r=8 MAT external-product kernel is promotable or whether large-r work needs a fused MAT multiply/layout hypothesis. | Stage76 decision must be `PASS_RGT4_KERNEL_FEASIBILITY_RECORDED_NO_PROMOTION` unless DFT-output and full-output evidence justify new full-SAB gates. | passed as kernel-level negative/not promoted |
| Stage 77 | r>4 fused MAT kernel smoke | Implement H11 behind `MAT_TRGSW_AVX512_RGT4_FUSED` and check whether r=6/r=8 kernel gains propagate to complete SAB smoke. | Stage77 decision must be `PASS_RGT4_FUSED_SMOKE_RECORDED_REPEATED_GATES_REQUIRED` before any repeated promotion campaign starts. | passed as positive smoke/not promoted |
| Stage 78 | r>4 fused repeated gates | Repeat full-SAB, correctness/noise, and resource gates for the Stage77 fused candidate. | Promote only if repeated full-SAB, noise, and resource evidence beat the relevant r=4/r>4 baselines under the same backend. | passed as r=6 promotion candidate; defaults unchanged |
| Stage 79 | r>4 fused high-stat confirmation | Confirm or reject the Stage78 r=6 promotion candidate with 10-run style complete-SAB evidence and expanded noise/resource gates. | r=6 fused must pass correctness/noise/resource and retain a practical advantage over the r=4 reference with enough statistics. | passed as review-required, not automatic promotion |
| Stage 80 | promotion integration or rejection audit | Decide whether the Stage79 r=6 fused review-required result is kept as an explicit experimental path or rejected from the promoted line. | scalar SAB and existing r=2/r=4 path remain unchanged; current-head refresh and closure/verifier pass. | passed as keep experimental/not promoted |
| Stage 81 | next variant triage | Select the next local optimization only after H11 is explicitly kept or rejected by Stage80. | new variants require hypothesis, theory check, staged correctness, full-SAB A/B, noise/resource, and promote/neutral/reject decision. | passed as profile-first/no code promotion |
| Stage 82 | post-H11 fused r=6 profile attribution | Run the profile-only attribution required by Stage81 before any new local implementation hypothesis. | profile correctness and exact schedule counts pass; component shares are recorded as attribution only. | passed as MAT-body-primary/no code promotion |
| Stage 83 | external claim unlock | Resolve native perf, 2025/686 full-text, and novelty-review blockers for stronger paper/theory claims. | native counters, reviewed full text, and related-work source anchors exist. | externally blocked |
| Stage 84 | final SAB optimization package | Freeze the final allowed engineering/paper package after promoted variants and external claim decisions are settled. | final recheck, closure audit, verifier, artifact manifest, and reproduction checklist all pass. | waiting |

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
- After Stage70, run Stage71 so the unified final recheck refreshes Stage70
  before relying on Stage42 closure.
- After Stage71, run Stage72 when external source availability may have
  changed; metadata/code visibility alone does not unlock theorem-level or
  novelty claims without reviewed full text.
- After Stage72, run Stage73 so the unified final recheck refreshes current
  source-route state before relying on blocker, frontier, or closure evidence.
- After Stage74, do not reopen direct r>4 lane-count expansion without a new
  r>4 kernel/layout/sparse-MAT hypothesis and full staged/full-SAB gates.
- After Stage75, treat the r>4 boundary as profile-backed: schedule counts are
  invariant for r=6/r=8, so future large-r work must target MAT/body cost with
  a dedicated layout, register/cache-blocking, or sparse/structured-MAT design.
- After Stage76, treat the current generic r>4 MAT kernel as diagnostic only:
  it is correct, but DFT-output speedup is below repeated scalar and the path
  is multiply dominated. Future r>4 code must start from H11 or another
  explicit fused MAT multiply/layout/register-blocking hypothesis, then pass
  kernel, complete-SAB, correctness, noise, resource, and closure gates.
- After Stage77, treat H11 as a positive smoke candidate only. The fused
  r=6/r=8 kernel improves same-stage generic r>4, and one-run full-SAB
  improves for both r values, but defaults and claims must not change until
  Stage78 repeated full-SAB/noise/resource gates pass.
- After Stage78, treat H11 r=6 as a promotion candidate, not a default change.
  The repeated r=6 full-SAB mean reaches the r=4 reference region and
  noise/resource gates pass, but Stage79 high-stat confirmation must run before
  changing defaults or upgrading claim strength. r=8 remains diagnostic.
- After Stage79, treat H11 r=6 as review-required rather than automatically
  promoted: correctness/noise/resource pass, but 10-run mean 1.367x is below
  the Stage36 r=4 mean 1.377x. Stage80 must explicitly keep it behind a
  non-default experimental policy or reject it from the promoted line before
  Stage81 variant triage.
- After Stage80, keep H11 r=6 fused MAT as explicit experimental evidence
  only. It is not the promoted path, does not change defaults, and cannot be
  used to upgrade r=6 claims without a new current-head promotion campaign.
  Stage81 should select a fresh falsifiable optimization hypothesis.
- After Stage81, do not add another local hot-path variant from the current
  evidence. H3 remains key-format/security blocked, r>4/r=8 tiling is not
  selected, and post-processing remains below threshold. If local optimization
  continues before external unlocks, run profile-only post-H11 fused r=6
  attribution first and open a new hypothesis only from that profile.
- After Stage82, treat the explicit H11 fused r=6 profile as attribution only:
  schedule counts still match the target model, instrumented speedup is not a
  final latency claim, and MAT EP remains the primary single component at
  47.6916% of full body time. Future local code must start from a MAT body
  theory/design check and then pass staged correctness, non-instrumented
  full-SAB A/B, noise/resource, and claim-policy gates.
