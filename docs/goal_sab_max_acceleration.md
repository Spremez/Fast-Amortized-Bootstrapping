# Goal: Maximize PVW/MAT-SAB Acceleration

Date: 2026-06-25

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
| Stage 36 high-stat expansion plan | experiment planning | n/a | planned, not executed | optional higher-stat campaigns pre-registered for broader statistical claims |

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
The Stage 36 high-statistics plan pre-registers optional larger campaigns for
broader statistical wording, but no heavy Stage 36 campaign has been executed
or promoted.
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
Stage 36: high-statistics claim expansion. [plan generated; heavy campaigns not executed]
Stage 37: native perf-counter evidence. [blocked until native/perf-enabled platform]
Stage 38: full 2025/686 source review. [blocked until full text is supplied]
Stage 39: optional new algorithmic variants. [only if scope requires beyond current promoted path]
Stage 40: final paper/release freeze. [after selected blockers or expansions are resolved]
```
