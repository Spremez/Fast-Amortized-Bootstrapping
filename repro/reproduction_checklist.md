# Reproduction Checklist

- [x] Record stage commit hash registry through Stage 9.
- [x] Record WSL/Linux compiler and CPU platform.
- [x] Keep scalar SAB baseline command registered.
- [x] Record Stage 5 PVW API sparse correctness command.
- [x] Add Stage 5 PVW no-extract bootstrap correctness command.
- [x] Add extract-aware PVW correctness run.
- [x] Add FFNT portability smoke result for this stage.
- [x] Add scalar baseline smoke result for this stage.
- [x] Add packing/HW-KS-aware PVW correctness run.
- [x] Add target-size `SET_2_3_2048` PVW full SAB correctness run.
- [x] Add initial target-size full SAB A/B benchmark run.
- [x] Add paired benchmark run with mean/stddev output.
- [x] Add initial target-shape correctness/noise gate run.
- [x] Add deterministic RNG seed switch and fixed-seed smoke.
- [x] Add Stage 6 seed-sweep automation and 3-seed smoke log.
- [x] Add Stage 6 10-seed correctness/noise run log.
- [x] Add Stage 6 50+ seed correctness/noise campaign log.
- [x] Add Stage 6 `r=4` target-shape smoke log.
- [x] Add Stage 6 `r=4` 10-seed correctness/noise campaign log.
- [x] Add Stage 9 initial stage-level noise probe logs for `r=2`/`r=4`.
- [x] Add Stage 7 `r=4` target-shape full SAB A/B benchmark run.
- [x] Add Stage 7 `r=2`/`r=4` full SAB benchmark summary table.
- [x] Add Stage 7 keygen/key-size/RSS resource metrics for `r=2`/`r=4`.
- [x] Add Stage 7 repeated process-level benchmark sweep for `r=2`/`r=4`.
- [x] Add Stage 7 portable FFNT target-shape backend smoke.
- [x] Add full bootstrapping A/B performance tables with backend separated from algorithmic gain.
- [x] Add Stage 8 `r=1` full-output negative-control log.
- [x] Add Stage 8 initial backend/SIMD sensitivity smoke.
- [x] Add Stage 8 repeated backend/SIMD sensitivity matrix.
- [x] Add Stage 8 implementation-variant decision record.
- [x] Add Stage 8 clear-elision kernel and correctness gates.
- [x] Add Stage 8 clear-elision repeated `r=4` full-output A/B benchmark.
- [x] Add Stage 8 clear-elision `r=2` repeated full-output A/B benchmark.
- [x] Add Stage 8 clear-elision Stage 6-style noise smoke.
- [x] Add Stage 8 clear-elision initial deterministic 10-seed noise sweeps for `r=2`/`r=4`.
- [x] Expand Stage 8 clear-elision `r=2` noise sweep to 50 seeds if used for final claim.
- [x] Add Stage 8 clear-elision `r=4` 50-seed noise campaign.
- [x] Record Stage 8 engineering exit assessment.
- [x] Add Stage 9 initial literature/novelty scan.
- [x] Add Stage 9 statistical evidence check for 50-seed zero-failure sweeps.
- [x] Add Stage 9 stage-level noise smoke summary.
- [x] Add Stage 10 engineering claim-to-evidence matrix.
- [x] Add Stage 11 hypothesis register and candidate variant cards.
- [x] Add Stage 11 PVW/MAT-SAB complexity and loop-engineering notes.
- [x] Add explicit experimental AVX512 small-r MAT compile flag.
- [x] Preserve Stage 11 explicit-flag failed staged kernel gate log as negative evidence.
- [x] Add Stage 11 explicit-flag target correctness replay.
- [x] Add Stage 11 `r=2` three-run full SAB benchmark summary.
- [x] Add Stage 11 `r=4` incomplete long-run/timeout evidence.
- [x] Add Stage 11 explicit-flag one-run replay smokes for `r=2` and `r=4`.
- [x] Add Stage 12 next-goal document with task matrix and gate policy.
- [x] Localize default AVX512 staged crash to the small-N sparse/bootstrap helper path.
- [x] Add AVX512 small-N staged sparse/bootstrap skip policy with explicit log message.
- [x] Re-run default AVX512 staged gate after the skip policy.
- [x] Re-run ordinary `spqlios` staged regression with full small sparse/bootstrap coverage.
- [x] Implement second-generation hand-unrolled `r=2`/`r=4` AVX512 MAT kernels after staged gate root-cause analysis.
- [x] Add Stage 12 explicit v2 staged kernel and microbench log.
- [x] Add Stage 12 explicit v2 target full-output correctness log.
- [x] Add Stage 12 explicit v2 one-run full SAB smokes for `r=2` and `r=4`.
- [x] Close Stage 12 v2 three-process sweep as condition-not-active under the current promoted path.
- [x] Close Stage 12 v2 noise/seed gate as condition-not-active because v2 was not promoted beyond kernel/smoke evidence.
- [x] Add Stage 13 PVW post-processing goal, algorithm card, and validation plan.
- [x] Preserve Stage 13 failed direct extraction staged gate as negative evidence.
- [x] Implement fixed direct lane extraction in full-output `sab_pvw_bootstrap_binary`.
- [x] Add `SAB_PVW_POSTPROC_PROFILE` timing gate.
- [x] Add Stage 13 fixed direct extraction staged gate log.
- [x] Add Stage 13 fixed direct extraction target full-output correctness log.
- [x] Add Stage 13 `r=2`/`r=4` post-processing profile smokes.
- [x] Add Stage 13 `r=2`/`r=4` unprofiled one-run full SAB smokes.
- [x] Close Stage 13 direct extraction three-process sweep as condition-not-active beyond cleanup.
- [x] Defer PVW-aware direct-to-packing KS because Stage 24 tail remains below the implementation threshold.
- [x] Add Stage 14 algorithm-to-paper goal and MAT AVX512 completeness boundary.
- [x] Add `SAB_PVW_BODY_PROFILE` profile switch for PVW no-extract body.
- [x] Add Stage 14 `r=2`/`r=4` target body profile smokes and parseable CSV.
- [x] Verify Stage 14 structural counts for MAT EP, CMUX/NCMUX, RGSW monomial, `sub_a`, and copy-back.
- [x] Record Stage 14 decision that CMUX/RGSW/sparse fusion precedes AVX512-only promotion.
- [x] Implement Stage 15 AVX512 MAT FMA-accumulate addmul helper.
- [x] Add Stage 15 AVX512 MAT repeated gate script and 3-run CSV outputs.
- [x] Add Stage 15 target full-output correctness gate for the AVX512 MAT variant.
- [x] Add Stage 15 r=2/r=4 full SAB smokes for the AVX512 MAT variant.
- [x] Record Stage 15 scoped dense-MAT expectation decision and rejected r=4 pointer-array sub-variant.
- [x] Add Stage 16+ execution plan and audit gates.
- [x] Add Stage 16 full SAB repeated audit script.
- [x] Run Stage 16 AVX512 MAT repeated full SAB audit for `r=2` and `r=4`.
- [x] Add Stage 17 perf-counter/objdump attribution probe for the accepted Stage 16 path.
- [x] Run Stage 17 perf-counter/objdump attribution probe for the accepted Stage 16 path.
- [x] Define Stage 18 CMUX/NCMUX scratch-fusion implementation plan and gates.
- [x] Add Stage 18 CMUX/NCMUX fine-grained profile counters and script.
- [x] Run Stage 18 CMUX/NCMUX fine-grained profile for `r=2` and `r=4`.
- [x] Add Stage 18 explicit `SAB_PVW_FUSED_FROM_DFT_ADD` candidate.
- [x] Run Stage 18 fused from-DFT-add correctness and smoke gates.
- [x] Run Stage 18 fused from-DFT-add repeated full SAB sweep for `r=4`.
- [x] Record Stage 18 fused from-DFT-add as neutral rather than promotable.
- [x] Add project-level maximum-acceleration goal and claim guardrails.
- [x] Add Stage 19+ roadmap after Stage 18 neutral result.
- [x] Add PVW/MAT-SAB loop-engineering contract for future candidates.
- [x] Add MAT-aware AVX512 memory/load-store theory check.
- [x] Add Stage 19 sparse schedule audit experiment plan.
- [x] Register H5-H9 for active-buffer fusion, sub_a rotation, MAT AVX512 limit audit, parameter generalization, and paper novelty.
- [x] Implement Stage 19 exact sparse schedule counters for per-bit CMUX/NCMUX and copy/sub_a attribution.
- [x] Run Stage 19 sparse schedule audit for `r=2` and `r=4`.
- [x] Record Stage 19 schedule-audit log and decision.
- [x] Implement Stage 20 active-buffer RGSW monomial/sparse_mul candidate after Stage 19 counters matched theory.
- [x] Run Stage 20 target correctness and default target regression gates.
- [x] Run Stage 20 active-buffer profile gate and verify copyback 40 -> 0.
- [x] Run Stage 20 repeated full SAB A/B gates for `r=2` and `r=4`.
- [x] Implement Stage 21 sub_a output-fusion candidate behind an explicit flag after post-Stage-20 profile showed measurable sub_a cost.
- [x] Run Stage 21 default target regression to confirm guarded code did not change the non-Stage-21 path.
- [x] Run Stage 21 target correctness and profile count gates for `r=2` and `r=4`.
- [x] Run Stage 21 sequential unprofiled full SAB smokes and record the candidate as neutral versus Stage 20.
- [x] Complete Stage 22 MAT AVX512 promotion audit with generic-vs-specialized microbench, objdump attribution, and r=4 full SAB sweep.
- [ ] Re-run Stage 22 hardware perf-counter attribution on native Linux if a theoretical load/store claim is needed; tracked by conditional backlog audit CB5.
- [x] Implement Stage 23 CMUX/NCMUX schedule-fused epilogue candidate behind `SAB_PVW_SCHEDULE_FUSED_CMUX`.
- [x] Run Stage 23 target correctness and default target regression gates.
- [x] Run Stage 23 schedule count profile for `r=2` and `r=4`.
- [x] Run Stage 23 sequential repeated full SAB A/B for `r=2` and `r=4`.
- [x] Record the Stage 23 schedule-fused CMUX candidate as neutral and not promoted.
- [x] Run Stage 24 conditional post-processing profile after the promoted body path.
- [x] Record Stage 24 post-processing direct-to-packing KS as deferred because tail is below threshold.
- [x] Add Stage 25 final-output noise, stage-noise, and resource scripts for the current promoted explicit path.
- [x] Run Stage 25 initial smoke matrix for `r=1/2/4`.
- [x] Record Stage 25 resource costs: keygen time, public key estimate, internal HWM, and max RSS.
- [x] Expand Stage 25 promoted-path final-output correctness/noise to 50 seeds for `r=2` and `r=4`.
- [x] Expand stage-level noise beyond smoke through the Stage 36 10-seed stage-noise campaign.
- [x] Re-run consolidated target full SAB A/B evidence through the Stage 36 10-run target-performance campaign.
- [x] Parameterize PVW target harness so `PARAM=SET_*` affects PVW gates.
- [x] Run Stage 26 initial binary parameter target smoke.
- [x] Record non-binary PVW branch as unsupported while keeping scalar TERNARY buildable.
- [x] Run Stage 26 initial performance/noise smoke for added binary parameters.
- [x] Expand Stage 26 `SET_4_5_2048` r=4 to 3-run/3-seed repeated smoke.
- [x] Expand Stage 26 `SET_2_3_4096` r=4 to 3-run/3-seed repeated smoke.
- [x] Expand Stage 26 added binary r=2 parameters to 3-run/3-seed repeated smoke.
- [x] Expand Stage 26 added binary r=2/r=4 parameters to 5-run/5-seed small-sample support.
- [x] Increase added-parameter evidence beyond 5 runs/seeds through the Stage 36 10-run/20-seed added-binary campaign.
- [x] Add Stage 27 initial related-work and claim-boundary matrix.
- [x] Record Stage 27 full-source access attempt and claim boundary.
- [x] Re-run final consolidated full-SAB performance table for promoted r=2/r=4 target path after Stage 26 harness changes.
- [x] Refresh Stage 27 related-work source access after Stage 26 5-run/5-seed evidence.
- [x] Add Stage 27 claim-support matrix separating allowed and blocked manuscript wording.
- [x] Assemble Stage 27 final scoped engineering performance/noise/resource package.
- [x] Add reproducible Stage 27 citation-access probe for 2025/686 full-text availability.
- [x] Add Stage 27 completion-readiness audit for scoped engineering claim.
- [x] Add Stage 27 final scoped engineering report.
- [x] Add and run Stage 28 lightweight native perf-counter gate; current WSL2 platform is blocked because `perf` is missing.
- [x] Add generated final goal completion audit separating scoped engineering readiness from stronger blocked claims.
- [x] Add and run final lightweight recheck runner for Stage 27 package, Stage 28 perf gate, and Stage 29 audit.
- [x] Add and run external evidence intake for optional 2025/686 full text and native/perf summaries.
- [x] Run Stage 32 citation refresh with network full-text probe enabled.
- [x] Run Stage 33 current-commit scalar/PVW target smoke.
- [x] Add and run Stage 34 final recheck option for refreshing current-commit smoke.
- [x] Generate Stage 35 completion blocker matrix from the final audit.
- [x] Generate Stage 36 high-statistics expansion budget matrix.
- [x] Execute Stage 36 high-stat target performance campaign.
- [x] Execute Stage 36 stage-level noise 10-seed campaign.
- [x] Execute Stage 36 resource 3-run scalar/PVW matrix.
- [x] Add and run Stage 37 native perf-counter audit; current WSL2 platform remains blocked because `perf` is missing.
- [x] Add and run Stage 38 full-text review gate; current environment remains blocked because `FAB686_FULLTEXT_PATH` is missing.
- [x] Generate Stage 39 optional variant triage matrix.
- [x] Generate Stage 40 final scoped freeze package.
- [x] Add SHA-256 hashes to the Stage 40 freeze manifest.
- [x] Run Stage 40 post-freeze verifier from a clean worktree input.
- [x] Verify Stage 40 freeze manifest SHA-256 hashes.
- [x] Run final recheck with Stage 40 post-freeze verifier enabled.
- [x] Separate post-freeze-only final recheck output from ordinary final recheck output.
- [x] Generate Stage 41 external-unlock packet for full-text/native-perf continuation gates.
- [x] Generate Stage 42 machine-checkable evidence-closure audit for Stage 19-44.
- [x] Run Stage 43 post-closure current-head scalar/PVW smoke refresh.
- [x] Integrate Stage 42 evidence-closure audit into the final recheck runner.
- [x] Run default final recheck with Stage 42 closure enabled.
- [x] Add SHA-256 manifest for stable Stage 42 post-freeze control-plane artifacts.
- [x] Run Stage 42 read-only closure verifier from a clean worktree input.
- [x] Add and run Stage 44 external full-text/native-perf unlock re-probe.
- [x] Integrate Stage 44 external unlock re-probe into the final recheck runner.
- [x] Execute Stage 36 added-parameter 10-run/20-seed campaign for added binary r=2/r=4 parameters.
- [x] Execute Stage 36 target-noise 50-seed campaign for target binary r=2/r=4.
- [x] Add and run Stage 55 external paper probe with Crossref DOI metadata and official full-text route blocking evidence.
- [x] Add and run Stage 56 explicit final recheck path for refreshing Stage55 before blocker/frontier/unlock/closure regeneration.
- [x] Add and run Stage 57 scope-label consistency audit so current control files track the latest Stage19+ closure range.
- [x] Add and run Stage 58 explicit final recheck path for refreshing Stage57 before Stage42 closure regeneration.
- [x] Add and run Stage 59 completion-route readiness so the post-Stage58 route to final completion is machine-checkable.
- [x] Add and run Stage 60 explicit final recheck path for refreshing Stage59 before Stage42 closure regeneration.
- [x] Add and run Stage 61 native perf unlock probe; current WSL2 remains blocked because `perf` is missing.
- [x] Add and run Stage 62 full-text unlock probe; current direct routes remain Cloudflare/403 blocked and no local `FAB686_FULLTEXT_PATH` is registered.
- [x] Add and run Stage64A post-variant refresh after Stage65A; current-head scalar/PVW smoke, repeated full-SAB A/B, final-output noise smoke, and Stage50 matrix pass.
- [x] Add and run Stage65A r=4 row-unrolled AVX512 optional variant; correctness passed but performance was negative, so the variant is not promoted.
- [x] Add and run Stage66A post-variant final recheck; lightweight final-recheck control plane remains refreshable after Stage64A/Stage65A while stronger blockers stay preserved.
- [x] Add and run Stage67 final-recheck Stage66A integration; unified final recheck can run Stage66A before Stage42 closure through an explicit switch.
- [x] Add and run Stage68 frontier/closure consistency audit; Stage42, Stage51 G6, Stage57, and Stage59 agree on the latest control-plane closure label.
- [x] Add and run Stage69 local variant feasibility audit; remaining local H2/H3/H4/H7/H8 candidates are not ready for new code without external unlocks or a new hypothesis.
- [x] Add and run Stage70 external unlock preflight; native-perf, full-text, novelty, and local-variant next actions are machine-checkable.
- [x] Add and run Stage71 final-recheck integration for Stage70; unified final recheck can refresh Stage70 before Stage42 closure.
- [x] Add and run Stage72 external source refresh; author metadata, DOI metadata, and code route are reachable while reviewed 2025/686 full text remains blocked.
- [x] Add and run Stage73 final-recheck integration for Stage72; unified final recheck refreshes current external-source state before blocker/frontier/closure rebuilds.
- [x] Add and run Stage74 r-scaling boundary; r=6/r=8 complete-SAB smoke passes correctness but direct r>4 scaling is not promoted versus r=4 evidence.
- [x] Add and run Stage75 r>4 profile boundary; r=6/r=8 keep exact SAB counts and profile evidence attributes the boundary to MAT/body cost, so direct r>4 remains not promoted.
- [x] Add and run Stage76 r>4 kernel feasibility; current generic r=6/r=8 MAT path is correct but DFT-output speedup is below repeated scalar, so it remains diagnostic and not promoted.
- [x] Add and run Stage77 r>4 fused MAT kernel smoke; fused r=6/r=8 beats same-stage generic in kernel and one-run full-SAB smoke, but repeated/noise/resource gates are still required.
- [x] Add and run Stage78 r>4 fused repeated gates; r=6 is a promotion candidate with three passing full-SAB samples, zero three-seed noise failures, and recorded resource overhead, but Stage79 high-stat confirmation is required before default/path promotion.
- [x] Add and run Stage79 r>4 fused high-stat confirmation for r=6; complete-SAB/noise/resource pass, but performance is review-required rather than automatic promotion versus the r=4 reference.
- [x] Add and run Stage80 explicit keep/reject integration audit; H11 r=6 fused MAT is kept behind an explicit experimental flag and is not promoted or made default.
- [x] Add and run Stage81 next-variant triage; no immediate new hot-path code variant is selected, and local continuation must start with post-H11 fused r=6 profile attribution.
- [x] Add and run Stage82 post-H11 fused r=6 profile attribution; exact schedule counts pass and MAT body remains the primary single profile target.
- [x] Add and run Stage83 MAT body theory/design check; H13-C1 r=6 full-output tile sweep is selected as the next explicit preflight, and sparse selector skipping remains key-format/security blocked.
- [x] Add and run Stage84 H13 r=6 MAT tile-sweep preflight behind `MAT_TRGSW_AVX512_R6_FULLTILE`; correctness and MAT microbench are positive, but complete-SAB smoke is not, so it is not promoted.
- [x] Run Stage86 secondary CMUX/materialization candidate routing; H14-C1 backend `FromDFT+add` callback preflight is selected, with no code promotion.
- [x] Implement and run Stage87 H14-C1 backend `FromDFT+add` materialization preflight behind `SAB_PVW_BACKEND_FROM_DFT_ADD`; correctness passes and one-run r=6 full-SAB smoke is positive, but the flag is not promoted.
- [x] Run Stage88 repeated complete-SAB/noise/resource gates for the Stage87 H14-C1 promotion candidate; backend-vs-wrapper repeated mean/min is `1.035516x`/`1.024476x`, backend-vs-scalar mean/min is `1.437x`/`1.435x`, final-output noise has zero 3-seed failures, and resource key/RSS/keygen ratios are recorded.
- [x] Run Stage89 H14 promotion-policy integration; H14-C1 backend is promoted as the preferred explicit r=6 local engineering path, while scalar/default paths and paper-level claims remain unchanged.
- [x] Run Stage90 external claim unlock probe; native perf, reviewed 2025/686 full text, and novelty/source review remain blocked, so stronger claims stay out of scope.
- [x] Run Stage91 final scoped SAB optimization package; final engineering package is assembled while native-perf, full-text, novelty, non-binary, all-parameter, and theory claims remain blocked.
- [x] Run Stage92 external unlock execution packet; native-perf, 2025/686 full-text, novelty-review, registration, and final-refresh commands plus acceptance gates are recorded while stronger claims remain blocked.
- [x] Run Stage93 external lane attempt; current WSL2/local environment still lacks usable native perf and recognized 2025/686 full text, so stronger claims remain blocked.
- [x] Run Stage94 local frontier audit; no unblocked local hot-path candidate remains under current evidence and H14-C1 stays the preferred explicit r=6 path.
- [x] Run Stage95 public source reprobe; public metadata/code routes are visible but direct full-text routes still do not provide a reviewed local artifact.
- [x] Run Stage96 upstream delta audit; `origin/main` is the current merge-base, local HEAD is ahead-only, local deltas are classified, and tracked PVW/MAT-SAB flags remain default-false.
- [x] Run Stage97 source delta guard; source deltas are classified, scalar/default SAB files remain symbol-isolated from PVW/MAT-SAB, tracked experiment flags remain default-false and gated, and Stage33/Stage89 scalar/default smoke evidence remains passing.
- [x] Run Stage98 current-head smoke refresh; scalar binary full run, explicit active-buffer PVW target gate, explicit H14 backend PVW target gate, and scalar ternary build all pass on the current head.
- [x] Run Stage99 external blocker reprobe; native perf remains unavailable in WSL2, public 2025/686 PDF routes remain blocked/metadata-only, a local 2025/686 PDF artifact is found and registered by Stage38, and final status moves to scoped-ready with external review required.
- [x] Run Stage100 full-text anchor prefill; candidate-only page anchors are generated for all six Stage38 review rows without storing full paper text or upgrading claims.
- [x] Run Stage101 CB5 remote native perf evidence; native Linux Stage28 hardware-counter gate, complete-SAB correctness, retired load/store counters, AVX512 FP counters, and r=4 one-run speedup evidence are recorded.
- [x] Run Stage102 2025/686 source-anchor review; all Stage38 checklist rows are upgraded from candidate-only anchors to reviewed source anchors with claim limits.
- [x] Run Stage103 related-work and novelty boundary review; real sources are recorded, broad novelty claims are rejected, and scoped systems/engineering wording is allowed.
- [x] Run Stage104 post-external final package refresh; Stage91 performance/noise/resource evidence is repackaged with Stage101-103 external-review evidence and scoped claim boundaries.
- [x] Run Stage105 goal completion audit; all scoped objective requirements are mapped to direct evidence and stronger claims remain blocked.
- [x] Run Stage106 MAT-RLWE SAB research-loop reset; primary endpoint is fixed to `T_complete_bootstrap(r)/r`, existing equal-lane speedups are reinterpreted as amortized evidence, and theoretical optimality remains open pending lower-bound/counter/complete-SAB gates.
- [x] Run Stage107 MAT kernel structure audit; current MAT AVX512 kernels are specialized/tiled but still dense `(r+1)^2` row-output paths, so Stage108 starts with V106-D layout/locality and keeps V106-B body-linear external product behind invariant proof.
- [x] Run Stage142 AVX512 FMA-order fix gate; Stage141 small-r/r4-unrolled exact-equivalence failures are repaired and r4-unrolled closed full-MAT kernel is promoted only to full-SAB rerun.
- [x] Run Stage143 complete-SAB r=4 r4-unrolled smoke with primary endpoint `T_bootstrap/r`; one-run correctness passes and the signal is positive, but final throughput evidence remains pending repeated Stage144.
- [x] Run Stage144 repeated complete-SAB A/B for r=4 generic-active versus r4-unrolled-active with confidence intervals, noise/resource checks, and decision `WEAK_STAGE144_R4_UNROLLED_POSITIVE_STATS_REVIEW_REQUIRED`.
- [ ] Run Stage85 repeated complete-SAB/noise/resource promotion gates only if a future preflight is full-SAB positive.
- [x] Review full related-work papers before promoting any novelty claim; resolved by Stage103 as scoped novelty wording, with broad claims still blocked.
- [x] Fill Stage38 source-anchor review checklist before theorem-level 2025/686 manuscript citations; resolved by Stage102 for scoped citations.
- [x] Run Stage145 r4-unrolled promotion-policy audit; decision `WEAK_STAGE145_POLICY_KEEP_EXPLICIT_DO_NOT_PROMOTE` keeps the path explicit-only unless future repeated evidence becomes stable.
- [x] Stage146 r4-unrolled variance-attribution pack recorded.
- [x] Stage147 H14 r=6 current-head route pack recorded.
- [x] Stage148 H14 r=6 repeated/noise/resource refresh pack recorded.
- [x] Stage149 H14 r=6 claim-policy pack recorded.
- [x] Stage150 final-package refresh pack recorded.
- [x] Stage151 H14 r=6 fulltile backend smoke pack recorded.
- [x] Stage152 dual-sub kernel gate pack recorded.
- [x] Stage153 dual-sub full-SAB gate pack recorded.
- [x] Stage154 bodymajor full-SAB closeout pack recorded.
- [x] Stage155 same-format frontier refresh generated from measured Stage153/148/151/153/154 evidence.
- [x] Stage156 lazy-DFT closure gate generated from source API scan and finite decomposition tests.
- [x] Stage157 sub-decompose fusion standalone C microbench generated and recorded.
- [x] Stage158 sub-decompose fusion full-SAB WSL gate generated and recorded.
- [x] Stage159 sub-decompose fusion repeated/noise/resource gate pack recorded.
- [x] Stage160 post-fusion profile/frontier pack recorded.
- [x] Stage160 post-fusion profile/frontier pack recorded.
- [x] Stage161 post-fusion attribution pack recorded.
- [x] Stage162 materialization-count feasibility pack recorded.
- [x] Stage163 from_DFT backend batching microbench pack recorded.
- [x] Stage164 representation closure route pack recorded.
- [x] Stage165 closed full-MAT streaming microbench pack recorded.
- [x] Stage166 shared-output compact algebra gate pack recorded.
- [x] Stage167 CB5 native r=6 counter refresh pack recorded.
- [x] Stage168 native counter frontier pack recorded.
- [x] Stage169 CB5 native repeated r=6 gate pack recorded.
- [x] Stage170 native split counter microbench pack recorded.
- [x] Stage171 structured compact keygen feasibility pack recorded.
- [x] Stage172 frontier closeout pack recorded.
- [x] Stage174 from_DFT direct-scale gate pack recorded.
- [x] Stage175 post-Stage174 frontier refresh pack recorded.
- [x] Stage173 structured compact phase/noise toy pack recorded.
- [x] Stage176 structured compact security/API gate pack recorded.
- [x] Stage177 verified literature/novelty gate pack recorded.
- [x] Stage178 full-MAT per-bit frontier pack recorded.
- [x] Stage179 MAT EP microarchitecture audit pack recorded.
- [x] Stage180 MAT EP split probe pack recorded.
- [x] Stage181 AVX512 sub-decompose gate pack recorded.
- [x] Stage182 exact path negative frontier pack recorded.
- [x] Stage183 addmul dataflow screen pack recorded.
- [x] Stage184 exact-route closeout claim refresh pack recorded.
- [x] Stage185 research/repro package refresh recorded.
- [x] Stage186 compact proof unlock audit recorded.
- [x] Stage187 compact proof obligation draft recorded.
- [x] Stage188 scoped manuscript skeleton recorded.
- [x] Stage189 closed-state linear probe recorded.
- [x] Stage190 selector distribution distinguisher recorded.
- [x] Stage191 secret-correction noise/resource gate recorded.
- [x] Stage192 compact admission and route selection recorded.
- [x] Stage193 exact addmul dataflow preflight recorded.
- [x] Stage194 exact DFT/conversion preflight recorded.
- [x] Stage195 scoped paper/repro refresh recorded.
- [x] Stage196 public source refresh recorded.
- [x] Stage197 metadata-safe citation bank recorded.
- [x] Stage198 metadata-safe manuscript refresh recorded.
- [x] Stage199 active goal verifier recorded.
- [x] Stage200 formal gap model with probe recorded.
- [x] Stage201 structured selector distribution probe recorded.
- [x] Stage202 dummy padding semantic probe recorded.
- [x] Stage203 production selector equation probe recorded.
- [x] Stage204 source anchor intake records real-source metadata only and blocks theorem/equation overclaim.
- [x] Stage205 current platform probe records WSL smoke, small-sample A/B, and invalid parallel-run rejection.
- [x] Stage206 current-head high-stat A/B and noise evidence recorded with claim boundary.
- [x] Stage207 current-head resource refresh links r=2/r=4 key-size, keygen,
  and RSS costs to Stage206 `T_bootstrap/r` throughput evidence.
- [x] Stage208 current-head profile attribution records r=2/r=4 schedule
  counts, CMUX component shares, active-buffer copyback elimination, and
  post-processing deferral.
- [x] Stage209 current-head MAT-EP split preflight records r=2/r=4
  sub_decompose, torus_to_DFT, addmul, combined timing, correctness, and
  projection gates.
- [x] Stage210 candidate admission denies speculative hot-path code and routes
  only to a bounded new DFT/FFT dataflow preflight.
- [x] Stage211 FFT/DFT dataflow preflight records the current single-row DFT
  API boundary, denies old DFT route reopenings, and routes only to a bounded
  Stage212 backend/API probe or native counter refresh.
- [x] Stage212 multirow FFT API probe records correctness, microbench,
  promotion decision, and next queue. Decision: `PASS_STAGE212_MULTIROW_WRAPPER_PROMOTE_STAGE213`.
- [x] Stage213 DFT wrapper integration preflight records guarded integration
  correctness, split timing, and next queue. Decision: `PASS_STAGE213_DFT_WRAPPER_COMPONENT_ONLY`.
- [x] Stage214 frontier native counter handoff records route ledger, access
  status, credential-free native runner, and next queue. Decision: `PASS_STAGE214_FRONTIER_NATIVE_COUNTER_HANDOFF_READY`.
- [x] Stage215 native counter execution records decision `PASS_STAGE215_NATIVE_COUNTERS_NO_HOTPATH_REOPEN`.
- [x] Stage216 post-counter frontier recorded.
- [x] Stage217 compact keygen/security preflight recorded.
- [x] Stage218 compact key-object/noise prototype recorded.
- [x] Stage219 MOSFHET compact key API skeleton recorded.
- [x] Stage220 encrypted compact keygen prototype recorded.
- [x] Stage221 compact keygen noise recurrence recorded.
- [x] Stage222 isolated compact EP integration recorded.
- [x] Stage223 route selection recorded.
- [x] Stage224 exact PVW/MAT AVX refresh recorded.
- [x] Stage225 exact refresh noise/resource recorded.
- [x] Stage226 exact counter attribution records decision `PASS_STAGE226_COUNTERS_RECORDED_TIMING_NEUTRAL`.
- [x] Stage227 exact route claim boundary records decision `PASS_STAGE227_EXACT_ROUTE_CLAIM_BOUNDARY_FIXED`.
- [x] Stage228 counter-driven backend kernel search records decision `PASS_STAGE228_NO_NEW_HOTPATH_CODE_SELECT_PARAMETER_MATRIX`.
- [x] Stage229 parameter generalization matrix records decision `PASS_STAGE229_SCOPED_BINARY_MATRIX_RECORDED_NONBINARY_BLOCKED`.
- [x] Stage230 source-verified literature novelty audit records decision `PASS_STAGE230_SOURCE_VERIFIED_SCOPED_NOVELTY_BOUNDARY`.
- [x] Stage231 current-head added-parameter refresh records decision `PASS_STAGE231_CURRENT_HEAD_ADDED_PARAM_SMOKE_FULL_STATS_RESOURCE_PENDING`.
- [x] Stage232 selected-subset full-stat/resource preflight records decision `PASS_STAGE232_SELECTED_SUBSET_PREFLIGHT_RESOURCE_RECORDED_FULL_MATRIX_PENDING`.
- [x] Stage233 first high-stat added-parameter slice records decision `PASS_STAGE233_FIRST_HIGHSTAT_SLICE_RESOURCE_RECORDED_MATRIX_PENDING`.
- [x] Stage234 second high-stat added-parameter slice records decision `PASS_STAGE234_SECOND_HIGHSTAT_SLICE_SET_4_5_2048_COMPLETE_MATRIX_PENDING`.
- [x] Stage235 third high-stat added-parameter slice records decision `PASS_STAGE235_THIRD_HIGHSTAT_SLICE_SET_2_3_4096_R4_HIGHSTAT_PENDING`.
- [x] Stage236 selected binary added-parameter matrix records decision `PASS_STAGE236_SELECTED_BINARY_ADDED_PARAMETER_MATRIX_COMPLETE`.
- [x] Stage236 selected binary added-parameter matrix records decision `PASS_STAGE236_SELECTED_BINARY_ADDED_PARAMETER_MATRIX_COMPLETE`.
- [x] Stage237 scoped manuscript package records decision `PASS_STAGE237_SCOPED_MANUSCRIPT_PACKAGE_READY_CLAIM_BOUNDED`.
- [x] Stage238 source-verified citation package records decision `PASS_STAGE238_SOURCE_VERIFIED_CITATION_PACKAGE_READY_NO_BIBTEX_HALLUCINATION`.
- [x] Stage239 verified BibTeX retrieval and LaTeX stub records decision `PASS_STAGE239_PARTIAL_VERIFIED_BIBTEX_LATEX_STUB_READY_TODOS_REMAIN`.
- [x] Stage240 scoped LaTeX draft records claim and citation gates `PASS_STAGE240_SCOPED_LATEX_DRAFT_READY_CLAIMS_AUDITED`.
- [x] Stage241 LaTeX compile package records compile and citation gates `PASS_STAGE241_LATEX_COMPILE_PACKAGE_READY`.
- [x] Stage242 unresolved BibTeX follow-up records reduced TODO set `PASS_STAGE242_BIBTEX_TODO_REDUCED_BATCHBOOT_REMAINS`.
- [x] Stage243 apply LW citations and recompile records 11-citation compile gates `PASS_STAGE243_LW_CITATIONS_APPLIED_RECOMPILED_BATCHBOOT_TODO`.
- [x] Stage244 BatchBoot BibTeX monitor records no verified BibTeX route `PASS_STAGE244_BATCHBOOT_MONITOR_RECORDED_NO_VERIFIED_BIBTEX`.
- [x] Stage245 current-head counter bridge records attribution-only reuse `PASS_STAGE245_COUNTER_REUSE_BRIDGED_NO_HOTPATH_DELTA`.
- [x] Stage246 broader algorithm admission gate records proof-prototype-only promotion `PASS_STAGE246_BROADER_ALGORITHM_GATE_RECORDED_PROOF_PROTOTYPES_ONLY`.
- [x] Stage248 structured compact finite probe records algebra pass/security blocked `PASS_STAGE248_STRUCTURED_COMPACT_FINITE_ALGEBRA_PASS_SECURITY_BLOCKED`.
- [x] Stage249 structured compact distribution/security preflight freezes production route `PASS_STAGE249_COMPACT_SECURITY_PREFLIGHT_FREEZE_PRODUCTION_ROUTE`.
- [x] Stage250 exact dense lower-bound gap keeps optimality open `PASS_STAGE250_EXACT_DENSE_GAP_REFRESH_OPTIMALITY_OPEN`.
- [x] Stage251 non-binary selector semantics blocks production implementation `PASS_STAGE251_NONBINARY_SELECTOR_SEMANTICS_PREFLIGHT_BLOCKS_IMPLEMENTATION`.
- [x] Stage252 non-binary MAT selector key skeleton ready for isolated equivalence `PASS_STAGE252_NONBINARY_MAT_SELECTOR_KEY_SKELETON_READY_ISOLATED_EQUIVALENCE`.
- [x] Stage253 isolated non-binary sub_a equivalence ready for keygen/noise preflight `PASS_STAGE253_ISOLATED_NONBINARY_SUBA_EQUIVALENCE_READY_KEYGEN_NOISE_PREFLIGHT`.
- [x] Stage254 non-binary keygen/noise preflight admits isolated prototype `PASS_STAGE254_NONBINARY_KEYGEN_NOISE_PREFLIGHT_READY_MOSFHET_ISOLATED_PROTOTYPE`.
- [x] Stage255 MOSFHET non-binary selector keygen/noise passes isolated gate `PASS_STAGE255_MOSFHET_SELECTOR_KEYGEN_NOISE_READY_NONBINARY_SPARSEMUL_PREFLIGHT`.
- [x] Stage256 non-binary sparse_mul preflight admits explicit implementation `PASS_STAGE256_NONBINARY_SPARSEMUL_PREFLIGHT_READY_EXPLICIT_IMPLEMENTATION`.

- [x] Stage257 non-binary sparse_mul implementation

- [x] Stage258 non-binary sparse_mul correctness/noise

- [x] Stage259 non-binary full SAB smoke

- [x] Stage260 non-binary full SAB noise/resource

- [x] Stage261 non-binary target `T_bootstrap/r` performance preflight

- [x] Stage262 non-binary target repeated `T_bootstrap/r` statistics

- [x] Stage263 non-binary target profile attribution

- [x] Stage264 MAT-AVX512 counter/assembly preflight proxy-only audit

- [ ] Run native/perf-backed MAT-AVX512 retired load/store/FMA attribution before any theoretical-optimality claim
- [x] Stage265 current-head counter reuse audit records `PASS_STAGE265_CURRENT_HEAD_COUNTER_REUSE_AUDIT_REFRESH_REQUIRED` and selects fresh current-head non-binary native-counter attribution as the next executable route.
- [x] Stage266 current-head non-binary native counter handoff records `PASS_STAGE266_NATIVE_COUNTER_HANDOFF_READY_AUTH_REQUIRED`.
- [x] Stage267 local split projection records `PASS_STAGE267_LOCAL_SPLIT_PROJECTION_SELECT_STAGE268_BACKEND_SMOKE` and selects bounded Stage268 backend FromDFT-add smoke.
<!-- stage268-backend-from-dft-add-smoke-checklist -->
- [x] Stage268 backend FromDFT-add smoke records `PASS_STAGE268_BACKEND_FROM_DFT_ADD_SMOKE_POSITIVE_REPEAT_REQUIRED` with primary metric `T_bootstrap/r`.
<!-- stage269-backend-from-dft-add-repeated-noise-resource-checklist -->
- [x] Stage269 backend FromDFT-add repeated/noise/resource records `NEUTRAL_STAGE269_BACKEND_FROM_DFT_ADD_REPEATED_NO_PROMOTION` with primary metric `T_bootstrap/r`.
<!-- stage270-candidate-closeout-next-selection-checklist -->
- [x] Stage270 closes backend FromDFT-add as neutral and records `PASS_STAGE270_FROM_DFT_ADD_CLOSED_SELECT_SUBA_SPLIT_PROFILE`.
<!-- stage271-nonbinary-sub-a-split-profile-checklist -->
- [x] Stage271 records `PASS_STAGE271_NONBINARY_SUB_A_SPLIT_PROFILE` as profile-only sub_a split attribution.
<!-- stage272-sub-a-selector-materialization-design-checklist -->
- [x] Stage272 records `PASS_STAGE272_SUB_A_SELECTOR_MATERIALIZATION_DESIGN_GATE` and selects Stage273 alias-safety microtest before implementation.
<!-- stage273-sub-a-from-dft-add-alias-microtest-checklist -->
- [x] Stage273 records `PASS_STAGE273_SUB_A_ALIAS_MICROTEST_ENABLES_FLAGGED_SMOKE` with raw logs, parsed gates, and claim boundaries.
<!-- stage274-sub-a-fused-materialization-smoke-checklist -->
- [x] Stage274 fused sub_a smoke records `NEUTRAL_STAGE274_SUB_A_FUSED_SMOKE_NO_PROMOTION` with primary metric `T_bootstrap/r`.
<!-- stage275-close-s272a-select-next-candidate-checklist -->
- [x] Stage275 records `PASS_STAGE275_CLOSE_S272A_SELECT_INCLUDE_ZERO_COEFF_ONE_FAST_PATH` and selects Stage276 guarded include-zero coeff-one fast path.
<!-- stage276-include-zero-coeff-one-fast-path-checklist -->
- [x] Stage276 include-zero coeff-one fast-path smoke records `PASS_STAGE276_INCLUDE_ZERO_FAST_SMOKE_POSITIVE_REPEAT_REQUIRED` with primary metric `T_bootstrap/r`.
<!-- stage277-include-zero-fast-repeated-resource-checklist -->
- [x] Stage277 include-zero fast repeated/resource records `PASS_STAGE277_INCLUDE_ZERO_FAST_REPEATED_RESOURCE_PROMOTE_NATIVE_STATS_REQUIRED` and keeps final claims gated.
<!-- stage278-native-larger-stats-include-zero-fast-checklist -->
- [x] Stage278 records `PASS_STAGE278_LOCAL_LARGER_STATS_NATIVE_REQUIRED` with reps>=5 local timing, resource/noise proxy, and native status separated.
<!-- stage279-native-access-residual-profile-checklist -->
- [x] Stage279 records `PASS_STAGE279_NATIVE_ACCESS_MISSING_PROFILE_SELECT_RESIDUAL` with native access status and fast-path residual profile.
<!-- stage280-cmux-mat-ep-residual-screen-checklist -->
- [x] Stage280 records `PASS_STAGE280_RESIDUAL_CANDIDATE_SELECTED_REPEAT_REQUIRED` with unprofiled T_bootstrap/r and separate profile attribution.
<!-- stage281-cmux-residual-repeated-gate-checklist -->
- [x] Stage281 records `PASS_STAGE281_REPEATED_POSITIVE_NOISE_RESOURCE_REQUIRED` for the selected CMUX residual candidate with repeated unprofiled T_bootstrap/r.
<!-- stage282-cmux-residual-noise-resource-checklist -->
- [x] Stage282 records `PASS_STAGE282_NOISE_RESOURCE_LOCAL_PASS_NATIVE_REQUIRED` for selected CMUX residual candidate noise/resource smoke.
<!-- stage283-native-target-repeated-gate-checklist -->
- [x] Stage283 records `PASS_STAGE283_NATIVE_ACCESS_MISSING_HANDOFF_READY` for native target repeated-gate status.
<!-- stage284-frontier-gap-ledger-checklist -->
- [x] Stage284 records `PASS_STAGE284_FRONTIER_GAP_LEDGER_READY_NATIVE_OR_MAT_EP_SPLIT_NEXT` for the current T_bootstrap/r frontier gap ledger.
<!-- stage286-mat-ep-split-counter-gate-checklist -->
- [x] Stage286 records `PASS_STAGE286_MAT_EP_SPLIT_PROXY_READY_NATIVE_COUNTER_REQUIRED` for MAT EP split/counter admission.
<!-- stage288-mat-ep-split-profile-checklist -->
- [x] Stage288 records `PASS_STAGE288_MAT_EP_SPLIT_PROFILE_RECORDED_MICROBENCH_NEXT` for MAT EP split profiling.

<!-- stage289-mat-dft-array-microbench-checklist -->
- [x] Stage289 records `NEUTRAL_STAGE289_DFT_ARRAY_WRAPPER_NO_PROMOTION` for isolated torus-to-DFT array-wrapper microbench.

<!-- stage290-dft-direct-output-microbench-checklist -->
- [x] Stage290 records `NEUTRAL_STAGE290_DFT_DIRECT_OUTPUT_NO_PROMOTION` for the direct-output DFT array microbench.

<!-- stage291-sub-decomp-dft-direct-microbench-checklist -->
- [x] Stage291 records `PASS_STAGE291_SUB_DECOMP_DFT_DIRECT_MICRO_POSITIVE_FULL_SAB_REQUIRED` for the sub-decompose direct-DFT candidate.
<!-- stage292-fullsab-direct-dft-ab-checklist -->
- [x] Stage292 records `PASS_STAGE292_DIRECT_DFT_FULLSAB_POSITIVE_NOISE_RESOURCE_REQUIRED` for direct sub-decompose-to-DFT under complete SAB `T_bootstrap/r`.
<!-- stage293-direct-dft-noise-resource-checklist -->
- [x] Stage293 records `PASS_STAGE293_DIRECT_DFT_TARGET_CORRECT_RESOURCE_SMOKE_NOISE_PENDING` for direct DFT target correctness/resource smoke; high-stat noise remains pending.
<!-- stage294-direct-dft-target-noise-checklist -->
- [x] Stage294 records `PASS_STAGE294_DIRECT_DFT_TARGET_NOISE_FINAL_OUTPUT` for direct DFT target final-output noise.
<!-- stage295-direct-dft-stats-refresh-checklist -->
- [x] Stage295 records `PASS_STAGE295_DIRECT_DFT_STATS_REFRESH_HIGHSTAT_PENDING` for direct DFT repeated performance plus target final-output noise refresh.
<!-- stage296-direct-dft-highstat-checklist -->
- [x] Stage296 records `PASS_STAGE296_DIRECT_DFT_HIGHSTAT_LOCAL` for direct DFT high-stat local complete-SAB evidence.
<!-- stage297-direct-dft-resource-sidecondition-checklist -->
- [x] Stage297 records `PASS_STAGE297_DIRECT_DFT_RESOURCE_SIDECONDITION_LOCAL` for direct DFT local resource side conditions.
<!-- stage298-direct-dft-target-stage-noise-checklist -->
- [x] Stage298 records `PASS_STAGE298_DIRECT_DFT_TARGET_STAGE_NOISE_LOCAL` for direct DFT target include-zero stage-wise noise.
<!-- stage299-direct-dft-param-preflight-checklist -->
- [x] Stage299 records `PASS_STAGE299_DIRECT_DFT_PARAM_PREFLIGHT_LOCAL` for direct DFT added-parameter preflight.

- [x] Stage300 current-head counter route audit recorded with local perf probe and claim boundary.
- [x] Stage301 current-head direct-DFT native counter refresh recorded without storing secrets.
- [x] Stage302 counter interpretation recorded.
<!-- stage303-param-matrix-highstat-checklist -->
- [x] Stage303 records `PASS_STAGE303_PARAM_MATRIX_HIGHSTAT_LOCAL` for SET_4_5_2048 direct DFT high-stat local complete-SAB evidence.
<!-- stage304-parameter-claim-matrix-checklist -->
- [x] Stage304 records `PASS_STAGE304_TWO_PARAMETER_LOCAL_GENERALIZATION_WITH_COUNTER_MECHANISM` and claim boundaries.
<!-- stage305-materialization-split-probe-checklist -->
- [x] Stage305 records `PASS_STAGE305_MATERIALIZATION_SPLIT_PROFILE_RECORDED` and a component-specific next target.
<!-- stage306-torus-to-dft-micro-hypothesis-checklist -->
- [x] Stage306 records `PASS_STAGE306_TORUS_TO_DFT_DIRECT_LIFECYCLE_TARGET_ADMITTED` and routes Stage307 to direct-path lifecycle split profiling.
<!-- stage307-direct-ifft-lifecycle-split-profile-checklist -->
- [x] Stage307 records `PASS_STAGE307_DIRECT_IFFT_LIFECYCLE_PROFILE_RECORDED` and routes Stage308 to `ifft`.
<!-- stage308-spqlios-ifft-feasibility-audit-checklist -->
- [x] Stage308 records `FAIL_STAGE308_IFFT_FEASIBILITY_AUDIT_INCOMPLETE` and routes Stage309/310.
<!-- stage309-digit-rowbatch-microbench-checklist -->
- [x] Stage309 records `NEUTRAL_STAGE309_DIGIT_ROWBATCH_NO_PROMOTION` for the rowbatch digit candidate.
<!-- stage310-ifft-rows-scaling-bench-checklist -->
- [x] Stage310 records `PASS_STAGE310_IFFT_ROWS_SCALING_BACKEND_REQUIRED` for SPQLIOS IFFT row scaling.
<!-- stage311-digit-narrow32-microbench-checklist -->
- [x] Stage311 records `PASS_STAGE311_DIGIT_NARROW32_MICRO_POSITIVE_FULLSAB_REQUIRED` for the narrow32 digit candidate.
<!-- stage312-digit-narrow32-fullsab-ab-checklist -->
- [x] Stage312 records `NEUTRAL_STAGE312_DIGIT_NARROW32_FULLSAB_NO_PROMOTION` for complete SAB narrow32 A/B.
<!-- stage313-narrow32-profile-attribution-checklist -->
- [x] Stage313 records `PASS_STAGE313_NARROW32_PROFILE_ATTRIBUTION_RECORDED` for narrow32 no-promotion attribution.
<!-- stage314-local-digit-closeout-checklist -->
- [x] Stage314 records `PASS_STAGE314_LOCAL_DIGIT_MICROVARIANTS_CLOSED_BACKEND_OR_SCHEDULE_NEXT` and next-candidate admission rules.
<!-- stage315-backend-ifft-admission-checklist -->
- [x] Stage315 records `PASS_STAGE315_BACKEND_IFFT_ADMISSION_SELECT_STAGE316_ABI_PREFLIGHT` and Stage316 admission gate.
<!-- stage316-spqlios-ifft-abi-preflight-checklist -->
- [x] Stage316 records `PASS_STAGE316_BACKEND_IFFT_ABI_PREFLIGHT_SELECT_ASM_BATCH5_SKETCH` and Stage317 isolated batch5 gate.
<!-- stage317-spqlios-ifft-batch5-skeleton-checklist -->
- [x] Stage317 records `PASS_STAGE317_IFFT_BATCH5_TILE32_SKELETON_STAGE318_MICRO_REQUIRED` and the Stage318 isolated gate.
<!-- stage318-ifft-batch5-intrinsics-checklist -->
- [x] Stage318 records `FAIL_STAGE318_INTRINSIC_BATCH5_CORRECT_BUT_SLOW_BLOCK_SAB_INTEGRATION` and blocks SAB integration for the
  intrinsics candidate.
