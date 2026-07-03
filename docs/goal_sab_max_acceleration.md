# Goal: Maximize PVW/MAT-SAB Acceleration

Date: 2026-06-25

Current control-plane closure label: `Stage 19-120`. This label tracks the
latest Stage19+ roadmap entry for reproducibility audits; it does not upgrade
the scoped engineering claim.

## Codex Goal

Starting from commit `b007c0c`, continue the PVW/MAT-SAB optimization path for
2025/686 sparse amortized bootstrapping without weakening the existing scalar
SAB baseline.

The final target is complete `sab_pvw_*` bootstrapping throughput, not an
isolated external-product microbenchmark. The work should maximize practical
speedup subject to correctness, noise, resource, and reproducibility gates. No
fixed speedup multiple is required; the accepted result is the best scoped,
evidence-backed implementation that survives the full validation loop.

## Current Foundation

The project already has a complete PVW/MAT-SAB path and repeated full-SAB
evidence.

| evidence | backend | r | status | result |
|---|---|---:|---|---|
| Stage 8/10 clear-elision | `spqlios` | 2 | accepted engineering evidence | `1.269x` throughput |
| Stage 8/10 clear-elision | `spqlios` | 4 | accepted engineering evidence | `1.337x` throughput |
| Stage 16 AVX512 MAT full SAB | `spqlios_avx512` | 2 | positive, explicit flag | mean `1.197x`, range `1.155x-1.248x` |
| Stage 16 AVX512 MAT full SAB | `spqlios_avx512` | 4 | positive, explicit flag | mean `1.281x`, range `1.231x-1.324x` |
| Stage 18 fused from-DFT-add | `spqlios_avx512` | 4 | neutral ablation | mean `1.285x`, not materially above Stage 16 |
| Stage 20 active-buffer fusion | `spqlios_avx512` | 2 | current explicit baseline | mean `1.270x`, range `1.173x-1.349x` |
| Stage 20 active-buffer fusion | `spqlios_avx512` | 4 | current explicit baseline | mean `1.346x`, range `1.323x-1.384x` |
| Stage 21 sub_a output fusion | `spqlios_avx512` | 2/4 | neutral ablation | one-run `1.136x`/`1.308x`, not above Stage 20 |
| Stage 22 specialized vs generic MAT-AVX | `spqlios_avx512` | 4 | implementation audit | specialized/generic PVW `1.040x`, full-SAB speedup `1.373x` |
| Stage 23 schedule-fused CMUX | `spqlios_avx512` | 2 | neutral ablation | mean `1.273x`, essentially tied with Stage 20 `1.270x` |
| Stage 23 schedule-fused CMUX | `spqlios_avx512` | 4 | neutral ablation | mean `1.335x`, below Stage 20 `1.346x` and Stage 22 `1.373x` |
| Stage 24 post-processing tail | `spqlios_avx512` | 2/4 | deferred | max tail `1.261%`, below `2.0%` implementation threshold |
| Stage 25 final/stage noise smoke | `spqlios_avx512` | 1/2/4 | smoke support | one deterministic seed; zero final-output failures and zero stage pair failures |
| Stage 25 final-noise expansion | `spqlios_avx512` | 2/4 | 50-seed target support | zero PVW/scalar/pair failures; r=2 gap `[-0.446,0.619]`, r=4 gap `[-0.555,0.682]` |
| Stage 25 resource matrix | `spqlios_avx512` | 1/2/4 | smoke support | PVW key bytes ratio `1.000029x`/`1.013617x`/`1.065349x`; PVW keygen slower per lane |
| Stage 26 binary parameter smoke | `spqlios_avx512` | 2 | initial scope expansion | `SET_2_3_2048`, `SET_4_5_2048`, `SET_2_3_4096` target gates pass |
| Stage 26 parameter perf/noise smoke | `spqlios_avx512` | 2/4 | smoke support | added parameters pass initial full-SAB A/B and final-output noise smoke: `SET_4_5_2048` r=2/r=4, `SET_2_3_4096` r=2/r=4 |
| Stage 26 `SET_4_5_2048` r=4 repeated smoke | `spqlios_avx512` | 4 | repeated smoke support | 3-run full-SAB mean `1.360x`, range `1.352x-1.376x`; 3 noise seeds, zero failures |
| Stage 26 `SET_2_3_4096` r=4 repeated smoke | `spqlios_avx512` | 4 | repeated smoke support | 3-run full-SAB mean `1.317x`, range `1.270x-1.346x`; 3 noise seeds, zero failures |
| Stage 26 added-parameter r=2 repeated smoke | `spqlios_avx512` | 2 | repeated smoke support | `SET_4_5_2048` mean `1.238x`, range `1.086x-1.434x`; `SET_2_3_4096` mean `1.227x`, range `1.219x-1.235x`; both 3 noise seeds, zero failures |
| Stage 26 added-binary 5-run/5-seed matrix | `spqlios_avx512` | 2/4 | small-sample parameter support | `SET_4_5_2048`: r=2 `1.329x`, r=4 `1.346x`; `SET_2_3_4096`: r=2 `1.224x`, r=4 `1.318x`; all zero noise failures |
| Stage 26 non-binary branch scope | `spqlios_avx512` | n/a | explicit unsupported | PVW+TERNARY rejected; scalar TERNARY build still passes |
| Stage 27 novelty audit | external scan | n/a | started | safe engineering claim available; novelty claim blocked by related-work risk |
| Stage 27 related-work refresh | external scan | n/a | scoped claim matrix available | 2025/2112 strengthens shared-mask novelty block; 2025/686 full text still required for theorem-level citations |
| Stage 27 citation access probe | metadata/full-text gate | n/a | theorem-level citation blocked | ePrint/ACM/ResearchGate full-text routes blocked; Semantic Scholar/DBLP metadata available |
| Stage 27 final full-SAB rerun | `spqlios_avx512` | 2/4 | scoped performance support | r=2 mean `1.171x` with higher variance; r=4 mean `1.401x`, range `1.331x-1.472x` |
| Stage 27 final evidence package | aggregation | n/a | scoped engineering package assembled | performance, noise, resource, and claim-boundary matrices generated from recorded artifacts |
| Stage 27 completion readiness audit | aggregation | n/a | scoped engineering chain ready | Final standards and Stage 19-27 items mapped to evidence, scope, and remaining actions |
| Stage 27 final engineering report | report | n/a | scoped engineering report ready | User-facing technical report generated without novelty or theorem-level overclaim |
| Stage 28 native perf-counter gate | WSL2 probe | n/a | blocked, reproducible | `perf` missing in current WSL2 PATH; MAT-AVX512 theoretical load/store claim remains blocked |
| Stage 29 final goal completion audit | generated audit | n/a | scoped ready, stronger blocked | `SCOPED_ENGINEERING_CHAIN_READY__STRONGER_CLAIMS_BLOCKED` |
| Stage 30 final goal recheck runner | orchestration | n/a | reproducible recheck available | default lightweight recheck regenerates final package/audit and preserves stronger-claim blocks |
| Stage 31 external evidence intake | artifact intake | n/a | missing, reproducible | no full-text or native perf external evidence supplied; final audit records A8b |
| Stage 32 citation refresh recheck | network gate | n/a | full text still blocked | 2026-06-26 refresh: ePrint/ACM/ResearchGate direct routes blocked; metadata only elsewhere |
| Stage 33 current commit smoke | `spqlios_avx512` | n/a | current smoke passed | scalar binary full run, PVW target full gate, and scalar ternary build all pass |
| Stage 34 current-smoke final recheck | orchestration | n/a | passed | final recheck refreshed Stage 33 current smoke before rebuilding the final audit |
| Stage 35 completion blocker matrix | audit synthesis | n/a | passed | remaining work classified into scoped-complete, optional expansion, claim guardrail, external blocker, and overall decision lanes |
| Stage 36 target high-stat performance/noise/resource | `spqlios_avx512` | 1/2/4 | 10-run/10-seed/3-run target support | performance r=2 mean `1.191x` CI `[1.075307,1.306693]`, r=4 mean `1.377x` CI `[1.314893,1.438107]`; stage-noise 10 seeds, zero pair failures; resource scalar/PVW r=1/2/4 has 3-run support |
| Stage 36 target final-output noise rerun | `spqlios_avx512` | 2/4 | 50-seed target support | `SET_2_3_2048`: r=2 50 seeds, 204800 points, zero PVW/scalar/pair failures, gap `[-0.446,0.619]`; r=4 50 seeds, 409600 points, zero PVW/scalar/pair failures, gap `[-0.555,0.682]` |
| Stage 36 added-binary parameter expansion | `spqlios_avx512` | 2/4 | 10-run/20-seed added-parameter support | `SET_4_5_2048`: r=2 mean `1.286x` CI `[1.255799,1.315601]`, r=4 mean `1.351x` CI `[1.329122,1.372278]`; `SET_2_3_4096`: r=2 mean `1.235x` CI `[1.210553,1.259647]`, r=4 mean `1.346x` CI `[1.285926,1.406474]`; all 20-seed noise gates have zero PVW/scalar/pair failures |
| Stage 37 native perf-counter audit | WSL2 probe | n/a | blocked, reproducible | requested heavy Stage 28 counter gate with `STAGE28_RUN_BENCH=1`; `perf` missing in PATH, so MAT-AVX512 hardware-counter attribution remains blocked |
| Stage 38 full 2025/686 source-review gate | artifact gate | n/a | blocked, reproducible | `FAB686_FULLTEXT_PATH` not supplied; theorem-level base-paper citations and novelty review remain blocked |
| Stage 39 optional variant triage | audit synthesis | n/a | no new variant promoted | non-binary and AVX/layout work blocked by full-text/perf prerequisites; schedule/post-processing variants deferred by prior neutral/small-tail evidence |
| Stage 40 final scoped freeze | report/freeze | n/a | scoped freeze ready | freeze package is ready for scoped engineering claim; SHA-256 manifest and post-freeze verifier pass; stronger claims remain blocked |
| Stage 41 external unlock packet | audit synthesis | n/a | generated | current readiness is WAIT_EXTERNAL_FULLTEXT, WAIT_NATIVE_PERF, WAIT_EXTERNAL_ARTIFACTS, and WAIT_UNLOCKS; stronger claims still require external evidence plus manual review |
| Stage 42 evidence closure audit | audit synthesis | n/a | passed and recheck-integrated | Stage 19-62 scoped evidence chain is internally closed under current artifacts; closure-only final recheck passes; stronger claims remain blocked |
| Stage 42 closure verifier | read-only audit | n/a | passed from clean input | no-regenerate verifier confirmed final audit, Stage 41 readiness, Stage 42 closure, Stage 43 smoke, final recheck closure, run-log rows, and manifest registration |
| Stage 43 post-closure current smoke | `spqlios_avx512` | n/a | passed | current-head scalar binary full run, explicit PVW target gate, and scalar ternary build all pass; smoke only |
| Stage 44 external unlock re-probe | network/native gate | n/a | waiting external unlocks | citation/full-text probe and native perf probe rerun; direct full text and hardware-counter evidence remain unavailable; final-recheck integration passes without upgrading claims |
| Stage 64A post-variant refresh | `spqlios_avx512` | 2/4 | current-head continuity | after Stage65A, scalar/PVW smoke passed; r=2/r=4 repeated full-SAB mean `1.269x`/`1.445x`; final-output noise smoke zero failures |
| Stage 65A r4 row-unrolled AVX512 | `spqlios_avx512` | 4 | negative ablation | correctness passed, but MAT/full-SAB ratios versus specialized baseline are `0.930815x`/`0.986900x`/`0.803554x`; not promoted |
| Stage 66A post-variant final recheck | n/a | n/a | control-plane continuity | lightweight final recheck after Stage65A/64A passes and preserves scoped-ready/stronger-blocked claim boundary |
| Stage 67 final-recheck Stage66A integration | n/a | n/a | final-recheck integration | explicit unified final-recheck switch runs Stage66A; Stage42 closure is rebuilt after the Stage67 summary is finalized |
| Stage 68 frontier/closure consistency | n/a | n/a | control-plane consistency | Stage42, Stage51 G6, Stage57, and Stage59 agree on the latest control-plane closure label |
| Stage 69 local variant feasibility | n/a | n/a | routing/theory control | remaining H2/H3/H4/H7/H8 local candidates are deferred, rejected, neutral, or externally blocked under current evidence |
| Stage 70 external unlock preflight | n/a | n/a | external prerequisite routing | native-perf, full-text, novelty, and local-variant unlock actions are machine-checkable |
| Stage 71 final-recheck Stage70 integration | n/a | n/a | final-recheck integration | unified final recheck can refresh Stage70 before Stage42 closure |
| Stage 72 external source refresh | n/a | n/a | external-source evidence | author metadata, DOI metadata, and code route are reachable; reviewed full text remains blocked |
| Stage 73 final-recheck Stage72 integration | n/a | n/a | final-recheck integration | unified final recheck can refresh Stage72 before blocker/frontier/closure rebuilds |
| Stage 74 r-scaling boundary | `spqlios_avx512` | 6/8 | negative boundary | r=6/r=8 complete-SAB smoke passed correctness with `1.251x`/`1.199x`, below the Stage36 r=4 CI lower bound; direct r>4 not promoted |
| Stage 75 r>4 profile boundary | `spqlios_avx512` | 6/8 | profile-backed boundary | exact schedule counts hold for r=6/r=8: CMUX/MAT EP `573440`, NCMUX `5080`, sub_a `39`, copyback `0`; MAT EP is about `55%` of full body time, so direct r>4 remains not promoted |
| Stage 76 r>4 kernel feasibility | `spqlios_avx512` | 6/8 | kernel boundary | identity-lane correctness passes, but DFT-output MAT is `0.984x`/`0.912x`; full-output smoke is only `1.168x`/`1.044x`; MAT shared-mask multiply share rises to `55.72%`/`61.20%`, so current r>4 kernel is not promoted |
| Stage 77 r>4 fused MAT kernel | `spqlios_avx512` | 6/8 | positive smoke, not promoted | `MAT_TRGSW_AVX512_RGT4_FUSED` beats generic r>4 kernel: DFT-output `1.582x`/`1.431x`, full-output `1.510x`/`1.370x`; full-SAB one-run fused/generic is `1.120x`/`1.102x`, but repeated/noise/resource gates are still required |
| Stage 78 r>4 fused repeated gates | `spqlios_avx512` | 6/8 | r=6 promotion candidate, defaults unchanged | r=6 complete-SAB repeated A/B has 3 passing samples with mean `1.408x`, min `1.361x`; r=8 stress is `1.350x`; r=6/r=8 three-seed final-output noise has zero failures; resource key ratios are `1.122537`/`1.181090` and RSS ratios `1.030750`/`1.071251` |
| Stage 79 r>4 fused high-stat confirmation | `spqlios_avx512` | 6 | high-stat review required, defaults unchanged | 10-run complete-SAB mean `1.367x`, CI `[1.341302,1.392098]`, min `1.314x`; 20-seed final-output noise zero failures; 3-run key ratio `1.122537`, RSS ratio mean `1.030715`; performance lands in r=4 reference region but below Stage36 r=4 mean `1.377x`, so no automatic promotion |
| Stage 80 promotion policy audit | `spqlios_avx512` | 6 | keep experimental, not promoted | Stage80 reads Stage79, passes current-head scalar/PVW smoke and static default-path guards, and records `PASS_RGT4_FUSED_KEEP_EXPERIMENTAL_NOT_PROMOTED`; `MAT_TRGSW_AVX512_RGT4_FUSED` remains explicit only, scalar/default paths unchanged |
| Stage 81 next-variant triage | audit synthesis | n/a | profile first, no code promotion | no immediate new hot-path code variant is justified; H3 remains security/key-format blocked, r>4/r=8 tiling is not selected, post-processing remains below threshold, and the next local step is post-H11 fused r=6 profile attribution |
| Stage 82 post-H11 fused r=6 profile | `spqlios_avx512` | 6 | MAT body primary, no code promotion | profile-only run preserves CMUX/MAT EP `573440`, NCMUX `5080`, sub_a `39`, copyback `0`; instrumented speedup `1.405x` is attribution-only; MAT EP is `47.6916%` of full body time and remains the primary single target |
| Stage 83 MAT body design check | audit synthesis | 6 | Stage84 preflight selected, no code promotion | H13-C1 r=6 full-output tile sweep is selected as the next explicit preflight; sparse selector skipping remains blocked by key-format/security requirements; Amdahl bounds and full-SAB gates are recorded before any implementation claim |
| Stage 84 H13 r=6 tile-sweep preflight | `spqlios_avx512` | 6 | kernel-only, not promoted | `MAT_TRGSW_AVX512_R6_FULLTILE` passes correctness and improves r=6 MAT microbench by `1.036x` DFT-output and `1.021x` full-output versus tile4, but complete-SAB smoke is `0.974x` versus tile4, so Stage85 is not opened |
| Stage 86 secondary CMUX materialization | audit synthesis | 6 | backend materialization preflight selected, no code promotion | Stage82 non-MAT body share remains material (`52.31%`), with `from_DFT+add=35.41%` and `sub=13.41%`; Stage86 rejects repeating Stage18/23 epilogue fusion and selects H14-C1 backend `FromDFT+add` callback as the next explicit preflight |
| Stage 87 H14 backend FromDFT-add preflight | `spqlios_avx512` | 6 | promotion candidate, not promoted | `SAB_PVW_BACKEND_FROM_DFT_ADD` passes staged and target correctness; r=6 one-run complete-SAB backend latency is `38284667.000 us` versus wrapper `40196035.000 us`, a `1.049925x` backend-vs-wrapper latency ratio; Stage88 later repeated this candidate |
| Stage 88 H14 backend repeated gates | `spqlios_avx512` | 6 | promotion candidate, not promoted | repeated backend-vs-wrapper latency ratio is `1.035516x` mean and `1.024476x` min over 3 paired runs; backend-vs-repeated-scalar speedup is `1.437x` mean and `1.435x` min; 3-seed final-output noise has zero failures; key/RSS/keygen ratios are `1.122537x`/`1.030722x`/`1.301382x`; Stage89 policy integration is required before changing defaults or claims |
| Stage 89 H14 promotion policy integration | `spqlios_avx512` | 6 | explicit path promoted, defaults unchanged | current-head scalar binary full run, explicit backend PVW target gate, and scalar ternary build pass; `SAB_PVW_BACKEND_FROM_DFT_ADD` remains explicit/default false; policy decision is `PASS_STAGE89_H14_BACKEND_PROMOTE_EXPLICIT_PATH_NOT_DEFAULT`, so H14-C1 is the preferred explicit r=6 local engineering path but not a scalar/default or paper-level claim |
| Stage 90 external claim unlock | WSL2/network probe | n/a | external probe completed, stronger claims blocked | fresh full-text route probe records ePrint/ACM/ResearchGate blocked, no reviewed `FAB686_FULLTEXT_PATH` is registered, current WSL2 lacks `perf`, and novelty/source review remains blocked; decision `PASS_STAGE90_EXTERNAL_CLAIM_UNLOCK_PROBE_RECORDED_STRONGER_CLAIMS_BLOCKED` |
| Stage 91 final SAB package | aggregation/claim freeze | n/a | scoped final package ready, stronger claims blocked | final package decision `PASS_STAGE91_FINAL_SCOPED_PACKAGE_STRONGER_CLAIMS_BLOCKED`; records Stage36 r=2/r=4 high-stat performance, Stage88/89 preferred explicit r=6 path, Stage36/88 noise/resource, reproduction commands, and blocked claim boundaries |
| Stage 92 external unlock execution packet | external handoff | n/a | unlock commands recorded, stronger claims blocked | final external-unlock packet decision `PASS_STAGE92_EXTERNAL_UNLOCK_PACKET_RECORDED_STRONGER_CLAIMS_BLOCKED`; records exact native-perf, 2025/686 full-text, novelty-review, external-registration, and final-refresh commands plus acceptance/failure criteria |
| Stage 93 external lane attempt | current environment probe | n/a | local attempts recorded, stronger claims blocked | current WSL2 attempt records `perf` missing and `hardware_counter_gate=BLOCKED`; local full-text filename search finds no 2025/686 candidate; external intake remains missing; decision `PASS_STAGE93_EXTERNAL_LANE_ATTEMPT_RECORDED_STRONGER_CLAIMS_BLOCKED` |
| Stage 94 local frontier audit | post-Stage93 local routing | n/a | no new hot-path code justified | H14-C1 remains the preferred explicit r=6 local engineering path; H14-C3 half-sub body ceiling is `1.071890`; H13 tile is full-SAB neutral/negative; post-processing tail remains small; sparse selector, AVX512 layout, and non-binary branches remain rejected/deferred/blocked; decision `PASS_STAGE94_LOCAL_FRONTIER_AUDIT_NO_NEW_HOTPATH` |
| Stage 95 public source reprobe | current public-source refresh | n/a | metadata/code visible, full text still blocked | author page, author BibTeX, DOI metadata, and GitHub code route remain visible; ePrint PDF and ACM PDF routes return `403`, author guessed PDF returns `404`; decision `PASS_STAGE95_PUBLIC_SOURCE_REPROBE_STRONGER_CLAIMS_BLOCKED` |
| Stage 96 upstream delta audit | public code provenance | n/a | local delta boundary recorded | `origin/main=d251d06` is the merge-base of `HEAD=986f42f`, local branch is ahead `255` and behind `0`; 1681 changed files are classified, including 5 PVW/MAT-SAB source files; tracked PVW/MAT-SAB flags remain default-false; decision `PASS_STAGE96_UPSTREAM_DELTA_AUDIT_LOCAL_PROVENANCE_RECORDED` |
| Stage 97 source delta guard | source isolation guard | n/a | scalar/default separation recorded | 26 source/hot-path files are classified; 4 scalar SAB files contain no forbidden PVW/MAT-SAB tokens; selected shared backend files contain no `sab_pvw` tokens; tracked PVW/MAT-SAB/AVX512/profile/microbench flags remain default-false and PVW/MAT sources remain gated; Stage33/Stage89 scalar binary/ternary smoke evidence remains passing; decision `PASS_STAGE97_SOURCE_DELTA_GUARD_SCALAR_DEFAULT_SEPARATED` |
| Stage 98 current-head smoke refresh | `spqlios_avx512` | n/a | current-head continuity passed | On `HEAD=e89b76f`, scalar binary full run, explicit active-buffer PVW target gate, explicit H14 backend PVW target gate, and scalar ternary build all pass; raw logs are preserved; decision `PASS_STAGE98_CURRENT_HEAD_SMOKE_REFRESH` |

Current conclusion:

```text
PVW/MAT-SAB exists and is correct for the tested target path.
The project has complete SAB speedup evidence, but not a multi-fold result.
The current best explicit variant remains Stage 20 active-buffer fusion with
the specialized MAT-AVX512 kernel. Stage 21 was validated but not promoted.
Stage 22 confirms the specialized kernel is useful but does not justify a
theoretical-optimality claim. Stage 23 schedule-fused CMUX/NCMUX was validated
but not promoted. The next work should move to conditional post-processing
tail profiling and then noise/resource validation rather than repeating the
same CMUX epilogue fusion. Stage 24 measured the tail below the implementation
threshold, so the next promoted-path work is Stage 25 correctness, noise, and
resource validation. Stage 25 now has smoke-level r=1/2/4 stage-noise and
resource evidence, plus 50-seed final-output noise support for promoted r=2
and r=4. Stage 26 now has initial binary parameter-smoke support and an
explicit non-binary PVW unsupported boundary. Stage 26 now also has
performance/noise smoke for added binary parameters, but not repeated or
large-seed generalization evidence. `SET_4_5_2048` and `SET_2_3_4096` now
have small 5-run/5-seed parameter-support gates for r=2 and r=4; `SET_4_5_2048`
r=2 is positive but visibly high variance. Stage 27 starts the paper package
and now has a related-work refresh plus claim-support matrix, but novelty
claims remain blocked because shared-mask/multiple-body batching is prior-art
risky and the full 2025/686 paper is still needed for theorem-level citation
checks. The Stage 27 final full-SAB performance rerun confirms the current
promoted explicit path after the Stage 26 harness refactor; r=4 is the
strongest current target evidence, while r=2 remains positive but noisier.
The Stage 27 final evidence package now assembles performance/noise/resource
and claim-boundary evidence for the safe engineering claim. The remaining open
work is not another engineering smoke result; it is manual full-paper citation
review if novelty or theorem-level manuscript claims are desired. The
reproducible citation probe confirms metadata is available for 2025/686, but
direct full text remains blocked in this environment.
The completion-readiness audit marks the scoped engineering evidence chain
ready, while keeping novelty, all-parameter, non-binary, theoretical-optimality,
and theorem-level citation claims blocked or conditional.
The final engineering report now provides the scoped, non-overclaiming
technical summary for the current result.
The Stage 28 native perf-counter gate makes the remaining MAT-AVX512
theoretical-optimality gap explicit: the current WSL2 environment records
AVX512 CPU flags but does not provide Linux `perf`, so hardware-counter-backed
load/store attribution still requires a native/perf-enabled run.
The Stage 29 generated goal audit now machine-checks the scoped engineering
evidence chain and records the overall state as scoped-ready with stronger
claims still blocked.
The Stage 30 recheck runner provides one command to refresh the current gate
state and final audit when external citation or perf conditions change.
The Stage 31 external-evidence intake records missing or supplied full-text and
native/perf artifacts with hashes, while preserving manual review requirements
before claim upgrades.
The Stage 32 citation refresh reran the full-text probe and confirmed that
theorem-level 2025/686 citations still cannot be upgraded in this environment.
The Stage 33 current-commit smoke refresh confirms that the scalar baseline,
explicit PVW target correctness gate, and scalar non-binary build guard remain
runnable after the evidence-chain tooling work.
The Stage 34 recheck integration makes that current smoke refreshable through
the unified final-goal recheck runner so future audit refreshes can include
current scalar/PVW build-correctness evidence on demand.
The Stage 35 blocker matrix makes the remaining completion boundary explicit:
the local scoped engineering chain is ready, while MAT-AVX512 theoretical
load/store attribution and theorem-level 2025/686 review still require external
native/perf and full-text evidence.
The Stage 36 target-performance, stage-noise, and resource campaigns
strengthen the target binary complete-SAB evidence with 10 same-backend
performance samples, 10 deterministic stage-noise seeds for r=2 and r=4, and
3 resource snapshots for scalar/PVW r=1/2/4. They do not change the remaining
external blockers for novelty, theorem-level 2025/686 review, non-binary
support, all-parameter claims, or MAT-AVX512 hardware-counter attribution.
The Stage 36 target final-output noise rerun now also gives the current
promoted target path a refreshed 50-seed target-noise campaign for r=2 and r=4
under the same promoted flags, with zero PVW, scalar, and pair failures. This
strengthens target-noise statistical wording but does not change any stronger
claim boundary.
The Stage 36 added-binary parameter campaign then raises the prior Stage 26
5-run/5-seed support to 10 complete-SAB performance samples and 20 final-output
noise seeds for `SET_4_5_2048` and `SET_2_3_4096`, r=2/r=4. All four added
binary parameter/r cases remain positive and have zero reported PVW, scalar,
and pair noise failures. This strengthens binary parameter-generalization
wording, but still does not support non-binary, all-parameter, novelty,
theorem-level citation, or hardware-counter claims.
The Stage 37 native perf-counter audit then requested the heavy hardware
counter gate but confirmed the current WSL2 environment still lacks `perf` in
PATH. This records a stronger reproducible blocker for MAT-AVX512
load/store/FMA attribution, not a negative result about the kernel itself.
The Stage 38 full-text review gate records the other remaining external
blocker: no 2025/686 full-text artifact is available through
`FAB686_FULLTEXT_PATH`, so theorem-level protocol citations and base-paper
novelty review cannot be upgraded.
The Stage 39 optional-variant triage records that no new algorithmic variant
should be promoted under current evidence. New code work is justified only if
one of the explicit blocked prerequisites is supplied or a new profile changes
the prior neutral/deferred cost model.
The Stage 40 final scoped freeze package records the current release boundary:
the engineering acceleration claim can be reported under tested scope, while
theory, novelty, non-binary, and all-parameter claims remain outside the
freeze. The freeze manifest records SHA-256 hashes for required artifacts, and
a post-freeze verifier confirms the committed freeze package is internally
consistent without regenerating freeze artifacts.
The Stage 41 external-unlock packet then turns the remaining A8/A8b blockers
into executable gates. It records exact commands and review policies for
2025/686 full-text intake, native perf-counter intake, external evidence
registration, and final recheck. It does not upgrade any claim by itself.
The Stage 42 evidence-closure audit machine-checks that the Stage 19-62 route,
final audit labels, Stage 40 hashes, Stage 41 readiness, Stage 43 current
smoke, run log, artifact manifest, and claim guardrails are mutually
consistent. It passes under the current scoped-ready/stronger-blocked state.
The Stage 42 closure audit now emits a SHA-256 manifest for stable
post-freeze control-plane artifacts. It is callable through the unified final
recheck runner and has passed in both a closure-only output directory and the
ordinary default recheck path, so evidence-chain closure can be refreshed
without special handling.
The Stage 42 read-only closure verifier then checked that package from a clean
input worktree without regenerating the closure audit. It confirmed the final
audit label, Stage 41 waiting state, Stage 42 closure result, Stage 43 smoke,
default and closure-only final recheck entries, required run-log rows, and
artifact-manifest registration. This strengthens reproducibility of the scoped
closure package, but it still does not upgrade any blocked full-text,
native-perf, novelty, or theoretical-optimality claim.
The Stage 43 post-closure current smoke then refreshes build/correctness
evidence at the current repository head. Scalar binary full run, explicit PVW
target gate, and scalar ternary build all pass under `spqlios_avx512`; this is
smoke evidence only and does not upgrade performance or novelty claims.
The Stage 44 external-unlock re-probe then reruns the remaining external gates
in isolated outputs. It confirms that direct 2025/686 full text and native
hardware-counter evidence are still unavailable in the current environment.
The stage therefore records `WAIT_EXTERNAL_UNLOCKS` and preserves the current
scoped engineering boundary. The unified final recheck runner can now execute
this re-probe before final-audit and Stage 42 closure refreshes by setting
`FINAL_RECHECK_STAGE44_REPROBE=1`.
Stage65A then tested a concrete optional local variant,
`MAT_TRGSW_AVX512_R4_UNROLLED_ROWS=true`, to check whether explicit r=4 row
unrolling and row-pointer hoisting improves MAT external-product behavior.
The variant preserved correctness but was slower at kernel and complete-SAB
levels, so it is recorded as a negative ablation and the promoted explicit path
remains Stage20 active-buffer plus the existing specialized MAT-AVX512 kernel.
Stage64A then refreshed the default promoted path after that code change:
current smoke, r=2/r=4 repeated full-SAB A/B, final-output noise smoke, and
Stage50 matrix all pass. This is continuity evidence and does not promote the
Stage65A variant.
Stage66A then checks that the post-variant evidence state can still be
refreshed by the lightweight final-recheck control plane and registered by
Stage42 closure/verifier. It is reproducibility evidence only.
Stage67 then integrates that Stage66A refresh into the unified final recheck
runner through an explicit switch, then rebuilds Stage42 closure after the
Stage67 summary is finalized.
Stage68 then repairs and verifies the closure/frontier label propagation so
Stage51 G6 remains `LOCAL_READY` through the Stage71 closure refresh.
Stage69 then audits the remaining local variant space and rejects the direct
H3 sparse-selector shortcut under the current encrypted-selector/key-format
boundary, leaving further code work gated on native perf, full-text review, or
a new falsifiable hypothesis.
Stage70 then consolidates the remaining native-perf, full-text, novelty, and
local-variant unlock requirements into a machine-checkable preflight artifact.
Stage71 then integrates that Stage70 preflight into the unified final recheck
runner so Stage42 closure cannot depend on a stale external-unlock preflight.
Stage72 then refreshes current author, DOI, code, and direct full-text source
routes for 2025/686; metadata/code routes are reachable, but reviewed local
full text remains unavailable, so stronger paper claims stay blocked.
Stage73 integrates that Stage72 source-refresh route into the unified final
recheck, so blocker dashboards, frontier labels, and Stage42 closure can be
rebuilt after current source availability is refreshed. This is control-plane
evidence only and does not upgrade speedup, novelty, theorem-level, or
hardware-counter claims.
Stage74 then tests direct `r>4` lane-count expansion as a local falsifiable
hypothesis. The r=6 and r=8 complete-SAB smoke runs pass correctness and remain
faster than repeated scalar SAB, but they are below the current r=4 promoted
evidence. Direct larger-r scaling is therefore a recorded negative boundary,
not a promoted optimization.
Stage75 then profiles that boundary and confirms it is not caused by extra
SAB schedule iterations: r=6 and r=8 keep CMUX/MAT EP at 573440, NCMUX at
5080, sub_a at 39, and active-buffer copyback at 0. MAT EP accounts for about
55% of full body time in both profile samples. Future large-r work therefore
needs a dedicated r>4 MAT layout/kernel or sparse/structured-MAT hypothesis,
not another direct lane-count increase.
Stage76 then tests the current r>4 MAT external-product kernel directly. The
generic r=6/r=8 path is functionally usable, but DFT-output MAT does not beat
repeated scalar external products and the full-output signal is too narrow to
promote. The r>4 phase breakdown is multiply dominated, so the next local
large-r hypothesis is a fused MAT multiply/layout/register-blocking kernel,
not current-kernel scaling.
Stage77 implements that H11 fused MAT kernel behind an explicit flag. The
kernel and one-run full-SAB smoke are positive versus same-stage generic r>4,
but the result is not a final promotion: r=8 remains weaker than the current
r=4 reference and no repeated/noise/resource gates have been run for the new
flag.
Stage78 runs those repeated/noise/resource gates. r=6 becomes a promotion
candidate because its three-sample complete-SAB mean speedup is 1.408x, above
the Stage36 r=4 mean 1.377x, with zero final-output noise failures in the
three-seed gate and recorded resource overhead. This still does not change
defaults: Stage79 must run high-stat confirmation before any claim upgrade or
path promotion.
Stage79 runs that high-stat confirmation. The r=6 fused path remains correct
and resource-bounded in the tested scope, but the 10-run mean speedup 1.367x
does not exceed the Stage36 r=4 mean 1.377x. H11 is therefore recorded as
review-required rather than automatically promoted. Stage80 then makes the
policy decision: keep H11 available only as an explicit experimental flag,
do not promote it, and do not alter scalar/default paths. Stage81 is the next
local variant-triage entry. Stage81 then records that no immediate new
hot-path implementation is justified from the current evidence. The next local
engineering action, before any new code variant, is profile-only post-H11
fused r=6 attribution to identify the actual remaining bottleneck. Stage82
runs that profile and records MAT body as the primary single target without
promoting new code or changing default paths. Stage83 then converts that
profile into the H13 MAT-body design route: the next local executable
candidate is an explicit r=6 full-output tile preflight, while sparse selector
skipping remains blocked and no speedup, default-path, theorem-level, or
novelty claim is upgraded. Stage84 implements that preflight behind
`MAT_TRGSW_AVX512_R6_FULLTILE`; the kernel-level signal is mildly positive,
but the complete-SAB r=6 smoke is not positive, so the candidate is kept as a
kernel-only ablation and not promoted. Stage86 then routes the next local
work away from MAT tiling and toward a backend-level CMUX materialization
preflight: H14-C1 `FromDFT+add` callback, still with no code promotion or
complete-SAB speedup claim.
```

## Invariants

All later stages must preserve these rules:

- scalar `sab_rlwe_bootstrap` remains callable and comparable;
- new implementations stay behind explicit flags or `sab_pvw_*` entry points
  until promoted by full gates;
- same-backend comparisons are the primary algorithmic speedup evidence;
- backend/SIMD absolute gains are reported separately from algorithmic gains;
- correctness failures stop promotion immediately;
- neutral and negative ablations remain recorded;
- no isolated kernel result may be described as final bootstrapping
  acceleration.

## Claim Levels

Use these labels consistently in docs, hypothesis records, and reports.

| label | meaning | allowed claim |
|---|---|---|
| `[implementation exists]` | code or script exists behind an explicit gate | runnable candidate only |
| `[correctness supported]` | staged and target correctness gates pass | semantic compatibility under tested scope |
| `[performance smoke only]` | one-run or low-repetition timing evidence | direction finding only |
| `[statistically supported engineering claim]` | repeated full SAB A/B plus correctness/noise/resource gates | scoped engineering speedup |
| `[paper-ready claim pending literature/theory]` | strong experiments exist, but prior art or proof work remains | candidate paper contribution |
| `[paper-ready claim]` | literature, theory, correctness, noise, resource, and full SAB evidence align | scoped manuscript claim |

## Final Completion Standard

The project reaches the current goal only if all conditions below hold:

1. A promoted `sab_pvw_*` full bootstrapping path matches repeated scalar SAB
   output under the target parameter sets.
2. Multi-seed correctness and noise gates pass for promoted variants.
3. Complete bootstrapping benchmark evidence shows stable throughput gain over
   repeated scalar SAB under the same backend.
4. Scalar baseline behavior and benchmarkability remain intact.
5. Algorithmic gains and backend/SIMD gains are separated.
6. Key size, keygen time, memory peak, and scratch overhead are reported.
7. Reproducibility artifacts contain commit, command, backend, CPU flags, raw
   logs, summaries, and decisions.
8. Paper-level claims are made only after a literature/novelty audit.

## Immediate Direction

The next implementation loop starts at Stage 19:

```text
Stage 19: exact sparse schedule audit. [completed]
Stage 20: active-buffer/copyback fusion. [completed, current explicit baseline]
Stage 21: sub_a and polynomial rotation optimization. [completed, neutral]
Stage 22: MAT-aware AVX512 theoretical-limit audit. [completed, practical path confirmed]
Stage 23: CMUX/NCMUX schedule fusion. [completed, neutral]
Stage 24: conditional post-processing optimization. [completed, deferred]
Stage 25: correctness/noise/resource matrix. [50-seed final-output expansion completed for r=2/r=4; stage/resource smoke completed]
Stage 26: parameter and branch generalization. [initial binary smoke plus added-parameter perf/noise smoke completed; non-binary PVW unsupported]
Stage 27: novelty and paper package. [engineering evidence package assembled; novelty claim blocked pending full-paper review]
Stage 28: native perf-counter gate for MAT-AVX512 theoretical load/store attribution. [lightweight probe completed; blocked on current WSL2 platform]
Stage 29: final goal completion audit. [generated; scoped engineering chain ready, stronger claims blocked]
Stage 30: final goal recheck runner. [generated and run; current decision unchanged]
Stage 31: external evidence intake. [generated and run; no external artifacts supplied]
Stage 32: citation refresh recheck. [run with network citation probe; direct full text still blocked]
Stage 33: current commit smoke. [scalar/PVW target smoke passed; no performance claim]
Stage 34: current-smoke final recheck integration. [completed; explicit refresh mode passed]
Stage 35: completion blocker matrix. [completed; local scoped-ready and external blockers separated]
Stage 36: high-statistics claim expansion. [target_perf 10-run, stage_noise 10-seed, and resource 3-run campaigns completed; target_noise and added_params remain optional]
Stage 37: native perf-counter evidence. [executed in current WSL2; blocked until native/perf-enabled platform]
Stage 38: full 2025/686 source review. [executed artifact gate; blocked until full text is supplied]
Stage 39: optional new algorithmic variants. [triaged; no new variant promoted under current evidence]
Stage 40: final paper/release freeze. [scoped engineering freeze ready; hash manifest and post-freeze verifier passed; stronger claims blocked]
Stage 41: external unlock packet. [generated; waiting for full-text/native-perf evidence before stronger claim upgrade]
Stage 42: evidence closure audit. [passed; scoped evidence chain is internally closed through Stage 19-62, no-regenerate verifier passed, stronger claims remain blocked]
Stage 43: post-closure current smoke. [passed; current-head scalar/PVW smoke refreshed without changing claim scope]
Stage 44: external unlock re-probe. [completed; still waiting for full-text/native-perf unlocks]
Stage 45: active-state refactor. [completed; correctness-preserving maintenance]
Stage 46: WSL active-state target smoke. [passed]
Stage 47: WSL active-state full-SAB smoke. [passed; positive smoke]
Stage 48: WSL active-state noise smoke. [passed]
Stage 49: WSL repeated full-SAB stability. [passed; speedup_min > 1]
Stage 50: performance evidence matrix. [generated; claim boundaries preserved]
Stage 51: goal completion frontier. [generated; local scoped-ready, stronger blocked]
Stage 52: external unlock readiness. [generated; commands and gates recorded]
Stage 53: final-recheck integration for Stage50-52. [passed]
Stage 54: default final recheck. [passed]
Stage 55: external paper probe. [metadata found; full text still blocked]
Stage 56: final-recheck integration for Stage55. [passed]
Stage 57: scope-label audit. [passed]
Stage 58: final-recheck integration for Stage57. [passed]
Stage 59: completion-route readiness. [passed]
Stage 60: final-recheck integration for Stage59. [passed]
Stage 61: native perf unlock probe. [blocked on current WSL2 because perf is missing]
Stage 62: 2025/686 full-text unlock probe. [blocked by direct-route 403/Cloudflare and no local full text]
Stage 63: novelty review. [externally blocked until source-anchor review]
Stage 64: implementation-refresh campaign. [completed after Stage65A; current-head continuity passed]
Stage 65: optional variant loop. [started; Stage65A r4 row-unrolled AVX512 negative/not promoted]
Stage 66A: post-variant final-recheck integration. [passed]
Stage 67: final-recheck Stage66A integration. [passed]
Stage 68: frontier/closure consistency. [passed]
Stage 69: local variant feasibility. [passed]
Stage 70: external unlock preflight. [passed]
Stage 71: final-recheck Stage70 integration. [passed; waiting for external unlocks or new hypothesis]
Stage 72: external source refresh. [passed; metadata/code reachable, reviewed full text still blocked]
Stage 73: final-recheck Stage72 integration. [passed; Stage72 source refresh is now covered by unified final recheck]
Stage 74: r-scaling boundary. [passed as negative/not promoted; direct r=6/r=8 does not beat r=4 evidence]
Stage 75: r>4 profile boundary. [passed as profile-backed negative/not promoted; r=6/r=8 keep exact SAB counts and expose MAT/body cost as the boundary]
Stage 76: r>4 kernel feasibility. [passed as kernel-level negative/not promoted; current generic r>4 MAT is correct but DFT-output speedup is below scalar]
Stage 77: r>4 fused MAT kernel. [positive smoke candidate; fused r=6/r=8 beats generic r>4 kernel and one-run full-SAB, repeated gates required]
Stage 78: r>4 fused repeated gates. [passed as r=6 promotion candidate; high-stat confirmation required before defaults or claims change]
Stage 79: r>4 fused high-stat confirmation. [completed; review required, not automatically promoted]
Stage 80: promotion integration or rejection audit. [completed; H11 r=6 fused kept experimental, not promoted]
Stage 81: next variant triage. [completed; profile-first, no code promotion]
Stage 82: post-H11 fused r=6 profile attribution. [completed; MAT body primary, no code promotion]
Stage 83: MAT body reduction theory/design check. [completed; H13-C1 r=6 tile-sweep preflight selected, no code promotion]
Stage 84: H13 r=6 MAT tile-sweep preflight. [completed; kernel-only positive but full-SAB not promoted]
Stage 85: H13 full-SAB promotion gate. [not opened after Stage84; requires future full-SAB-positive preflight]
Stage 86: secondary CMUX materialization pass. [completed design gate; H14-C1 backend FromDFT+add callback preflight selected, no code promotion]
Stage 87: H14 backend FromDFT-add preflight. [completed; one-run promotion candidate, not promoted]
Stage 88: H14 repeated/noise/resource gate. [completed; promotion candidate, not promoted]
Stage 89: H14 promotion policy integration. [completed; H14 backend is preferred explicit r=6 path, defaults unchanged]
Stage 90: external claim unlock. [completed as probe; stronger claims remain blocked on native perf, full text, and manual novelty review]
Stage 91: final SAB optimization package. [completed; scoped final package ready, stronger claims remain blocked]
Stage 92: external unlock execution packet. [completed; executable external lanes recorded, stronger claims remain blocked]
Stage 93: external lane attempt. [completed; current local environment still lacks native perf and 2025/686 full text]
Stage 99: external blocker reprobe. [completed; local 2025/686 PDF registered, manual review required]
Stage 100: full-text anchor prefill. [completed; candidate anchors generated, manual review required]
Stage 101: CB5 remote native perf evidence. [completed; native Linux Stage28 hardware-counter gate, complete-SAB correctness, load/store, and AVX512 FP counters recorded]
Stage 102: 2025/686 source-anchor review. [completed; all Stage38 checklist rows reviewed with concrete page/section anchors and claim limits]
Stage 103: related-work and novelty boundary review. [completed; real-source related-work matrix generated, broad novelty rejected, scoped systems claim allowed]
Stage 104: post-external final package refresh. [completed; Stage91 final package refreshed with Stage101-103 evidence and scoped claim boundaries]
Stage 105: goal completion audit. [completed; all scoped requirements proven and stronger claims remain blocked]
Stage 106: MAT-RLWE SAB research-loop reset. [completed as process reset; primary endpoint T_total/r fixed, existing evidence reinterpreted as amortized, theoretical optimality remains open]
Stage 107: MAT kernel structure audit. [completed; current MAT kernels remain dense row-output `(r+1)^2`, Stage108 starts with V106-D layout/locality while V106-B body-linear remains proof-gated]
Stage 108: V106-D body-major layout gate. [completed; r=6 body-major kernel correctness passed but performance was negative/neutral versus existing tile4/fulltile layouts, not promoted]
Stage 109: V106-B body-linear invariant gate. [completed; loop-only body-linear skipping is blocked by current MAT_TRGSW_DFT selector/key format, new format gate required]
Stage 110: r=6 fulltile complete-SAB gate. [completed as one-run smoke; fulltile beat tile4 by 1.026x total/per-lane but is not promoted without repeated/noise/resource gates]
Stage 111: r=6 fulltile repeated gate. [completed; 3-run complete-SAB gate rejects fulltile promotion, repeated PVW ratio 0.974x versus tile4]
Stage 112: selector/key-format gate. [completed; shared-mask counterexample rejects current-format loop-only body-linear skipping, new-format r=2 simulator required]
Stage 113: r=2 selector simulator. [completed; lane-local multimask is phase-equivalent in toy algebra with 9 vs 5 product model, resource/noise model required]
Stage 114: lane-local resource model. [completed; symbolic resource screen not fatal, min coarse product-over-accumulator ratio 1.350, toy representation required]
Stage 115: lane-local toy C representation gate. [completed; generated C layout probe passed, r=4/N=2048 requested-byte ratio 1.100, next gate is toy arithmetic equivalence only]
Stage 116: toy arithmetic equivalence gate. [completed; dense-vs-lane mismatches zero for r=2/4/6, current-format drop-offlane negative control fails, selector/key skeleton required]
Stage 117: selector skeleton invariant gate. [completed; `1+2r` term-map skeleton passes for r=2/4/6/8 with zero off-lane and missing terms, real type/noise/key design required]
Stage 118: real-type design gate. [completed; lane-local type shape passes for r=2/4/6/8 and N=2048/4096, r=4/N=2048 DFT byte ratio 0.866667, noise remains recorded-not-proven]
Stage 119: shared-term object semantics gate. [completed; scalar-shared rejected, vector-shared selected with zero phase mismatches and r=4 vector/dense byte ratio 0.800000]
Stage 120: real C struct phase/noise gate. [completed; vector-shared polynomial structs pass 30 phase/noise rows, zero mismatches and zero noise-bound violations, DFT/conversion prototype required]
```

## Current Closure Label

Current scoped engineering closure range: `Stage 19-105`.

Stage106 is a new research-loop reset layered on top of that closed package,
not a regenerated Stage42 engineering-closure range.

Stage101-103 resolve the previous external blockers: CB5 has native Linux
hardware-counter evidence, CB7 has reviewed 2025/686 source anchors, and CB6
has a real-source related-work/novelty boundary. The current final-audit state
is `SCOPED_ENGINEERING_CHAIN_READY__EXTERNAL_REVIEWED_STRONGER_CLAIMS_SCOPED`.
Stage104 packages those facts into the current post-external final scoped
evidence bundle. Stage105 then audits the active objective requirement by
requirement and records
`PASS_STAGE105_SCOPED_GOAL_COMPLETE_STRONGER_CLAIMS_BLOCKED`. This allows
scoped systems/engineering wording for the PVW/MAT-SAB optimization, while
broad novelty, all-parameter, non-binary, and theoretical MAT-AVX512 optimality
claims remain blocked without new evidence.

Stage106 opens the next research track without changing the completed scoped
package: PVW/MAT-SAB is now treated as an r-body MAT-RLWE SAB algorithmic
object with primary endpoint `T_complete_bootstrap(r)/r`. Existing Stage36
r=2/r=4 speedups are valid amortized evidence because they compare equal
processed lane counts, but theoretical MAT-RLWE SAB optimality remains open
until lower-bound gap, counter/assembly attribution, correctness/noise/resource,
and complete-SAB statistical gates are all recorded.

Stage107 grounds that research track in the current implementation: the
existing generic, r=2, r=4, r=6, and r=8 MAT kernels are specialized/tiled but
still dense row-output accumulations. Therefore the immediate runnable path is
V106-D layout/locality measurement, while the theory-critical V106-B body-linear
MAT external product requires a selector/key invariant proof before code.

Stage108 executes that V106-D gate. The explicit
`MAT_TRGSW_AVX512_R6_BODYMAJOR` path preserves scalar/default behavior and
passes the r>4 MAT/PVW kernel identity gate, but it is not a promotion
candidate: r=6 full-output body-major is faster than tile4 but slower than
fulltile, and r=6 DFT-output is slower than both tile4 and fulltile. This
closes the blind body-major layout branch as a negative ablation and sends the
next research step to V106-B invariant analysis or counter-backed attribution.

Stage109 executes the V106-B invariant analysis as a source-backed gate. It
finds that current `MAT_TRGSW_DFT` rows are full `PVW_TMLWE_DFT` encryptions
with diagonal gadget injection, not proof-carrying sparse selector rows. A
loop-only body-linear implementation that skips off-lane ciphertext products
would break the encrypted-zero relation unless a new selector/key format proves
otherwise. Therefore theoretical MAT-RLWE SAB optimality remains open and now
has a concrete next gate: design and verify a new body-linear selector/key
format before AVX512 kernel work.

Stage110 returns to an executable performance gate to avoid theory-only
iteration. It tests whether the existing r=6 fulltile kernel signal transfers
to complete SAB. The one-run result is positive but small: 1.026x total and
per-lane improvement over tile4. This is useful routing evidence for a future
3+ run confirmation, not a promotion or paper-level claim.

Stage111 runs that 3-run confirmation and rejects the fulltile route. Although
all correctness gates pass, fulltile is slower than tile4 in repeated
complete-SAB PVW time: 43.337s versus 42.220s on average, or 0.974x. This is a
negative ablation and closes the Stage110 one-run candidate unless a different
profile-backed hypothesis reopens r=6 layout work.

Stage112 makes the body-linear route precise. A concrete shared-mask phase
counterexample shows that dropping an off-lane body term while retaining the
shared mask contribution changes an expected zero phase into `-70` in the toy
model. Therefore body-linear MAT-SAB cannot be implemented as current-format
loop tuning; it needs a new selector/key or ciphertext format, with an r=2
algebraic simulator as the next finite gate.

Stage113 runs that r=2 simulator. It preserves dense reference phases
`(73, 121)`, confirms current-format loop-only skipping fails with
`(-362, -224)`, and shows lane-local multimask can match `(73, 121)` in the
toy algebra. The arithmetic model is 9 dense products versus 5 lane-local
target products, but this is not a complete-SAB claim; the next gate is
resource/key/noise modeling for the changed ciphertext format.

Stage114 performs the first symbolic resource screen for that changed format.
The accumulator component overhead is real, but the raw product-count advantage
is not immediately erased: the minimum coarse product-over-accumulator ratio is
1.350 at r=2. This only justifies a toy representation and measured allocation
gate; it does not justify hot-path integration.

Stage115 runs that measured representation gate with a generated C layout
probe. It passes under WSL gcc for r=2/4/6/8 and N=2048/4096. The target
r=4,N=2048 requested-byte ratio is 1.100 while product terms drop from 25 to
9; the r=2,N=2048 control row has requested-byte ratio 1.333. This keeps the
lane-local branch alive only for a toy arithmetic equivalence prototype. It is
not MOSFHET hot-path, noise, AVX512, or complete-SAB performance evidence.

Stage116 runs that toy arithmetic equivalence prototype. Dense shared-mask
reference and lane-local compact arithmetic match exactly for all tested
r=2/4/6 and N=64/256 coefficients, while the current-format drop-offlane
negative control fails in every row. This validates only the finite arithmetic
invariant and opens a selector/key skeleton gate; it still does not prove
encryption, noise, DFT layout, AVX512 performance, or complete-SAB speedup.

Stage117 validates that selector/key skeleton as a finite C term map. For
r=2/4/6/8, skeleton terms are 5/9/13/17, selector polynomials are
10/18/26/34, accumulator polynomials are 4/8/12/16, and off-lane/missing terms
are all zero. This opens only real MOSFHET-adjacent type, noise, and key-design
gates outside the SAB hot path.

Stage118 converts the skeleton into a MOSFHET-adjacent real-type design gate.
For r=4,N=2048, the combined accumulator+selector DFT byte model is 0.866667x
the current dense design, while the key-secret polynomial ratio remains
1.000000. The noise/key model is explicitly `RECORDED_NOT_PROVEN`, so the next
valid work is a real-object allocation/phase/noise prototype, not SAB
integration.

Stage119 refines the object semantics before writing real structs. It rejects
the scalar-shared interpretation because a single shared term cannot encode
independent lane shared-row messages. The vector-shared lane-local object has
zero phase mismatches and zero toy-noise bound violations for r=2/4/6 and
N=64/256. The valid route now uses `2r` phase terms and `4r` selector
polynomials for k=1; for r=4, the vector/dense byte ratio is 0.800000.

Stage120 implements the first standalone real C struct prototype for that
valid route. It allocates vector-shared polynomial objects, uses negacyclic
mask-secret multiplication for phase, and runs r=2/4/6, N=32/64, seeds 0..4.
All 30 phase/noise rows have zero noiseless mismatches and zero noise-bound
violations. This supports proceeding to DFT/conversion prototyping only; it is
not a MOSFHET torus/FFT external product or SAB integration result.

Stage121 runs that DFT/conversion prototype as an exact modular negacyclic
NTT/DFT gate over modulus 12289. It verifies roots, round-trip conversion for
mask/body/secret polynomials, DFT-domain phase `DFT(b)-DFT(a)*DFT(s)`, noisy
phase, and digit-sum noise bounds across r=2/4/6, N=32/64, seeds 0..4. All 30
conversion rows pass, and vector/dense DFT polynomial ratios remain 0.666667
for r=2, 0.533333 for r=4, and 0.428571 for r=6. This removes the exact
conversion semantic blocker but is still not production FFT, AVX512, external
product, SAB schedule, or complete `T_bootstrap/r` evidence.
