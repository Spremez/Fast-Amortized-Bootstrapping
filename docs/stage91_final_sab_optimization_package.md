# Stage91 Final SAB Optimization Package

Date: 2026-06-26

## Decision

`PASS_STAGE91_FINAL_SCOPED_PACKAGE_STRONGER_CLAIMS_BLOCKED`

Final scoped SAB optimization package is assembled; stronger native-perf/full-text/novelty claims remain blocked.

## Algorithm Scope

The final scoped path is an explicit `sab_pvw_*` implementation beside
the scalar `sab_rlwe_bootstrap` baseline. It batches multiple independent
LUT/SAB lanes with PVW/MAT shared-mask multi-body external products.
For the target binary `SET_2_3_2048` schedule, the Stage19 audit fixed
the main external-product-class count at `(h+1)*r_prec*N = 40*7*2048 =
573440`, with NCMUX `5080`; active-buffer fusion keeps copyback at zero
in the promoted body path.

The package distinguishes two evidence lanes:

- target `r=2/4` high-stat scoped engineering evidence from Stage36;
- preferred explicit `r=6` H14 backend evidence from Stage88/89, not a
  default-path or paper-level claim.

## Gates

| gate | status | detail |
| --- | --- | --- |
| stage91_smoke_current_code_guard | PASS_CURRENT_SMOKE_INHERITED_SOURCE_UNCHANGED | stage89_smoke=PASS; stage89_anchor=8422cf5; sab_source_changes_after_stage89=none |
| stage91_performance_gate | PASS_SCOPED_COMPLETE_SAB_PERFORMANCE | Stage36 r=2/r=4 high-stat complete-SAB performance passes; Stage88 records preferred explicit r=6 H14 backend path. |
| stage91_noise_resource_gate | PASS_SCOPED_NOISE_RESOURCE | Stage36 r=2/r=4 target noise/resource and Stage88 r=6 explicit-path noise/resource gates pass under their recorded scopes. |
| stage91_stage89_policy_gate | PASS_EXPLICIT_R6_POLICY_RECORDED | stage89_decision=PASS_STAGE89_H14_BACKEND_PROMOTE_EXPLICIT_PATH_NOT_DEFAULT |
| stage91_external_claim_gate | PASS_STRONGER_CLAIMS_BLOCKED | decision=PASS_STAGE90_EXTERNAL_CLAIM_UNLOCK_PROBE_RECORDED_STRONGER_CLAIMS_BLOCKED; native=WAIT_NATIVE_PERF; fulltext=WAIT_FULLTEXT_ARTIFACT; novelty=WAIT_FULLTEXT_OR_MANUAL_REVIEW |
| stage91_existing_closure_gate | PASS_PRE_STAGE91_CLOSURE_READY | Pre/post-Stage91 closure/frontier/route consistency is ready. |
| stage91_decision | PASS_STAGE91_FINAL_SCOPED_PACKAGE_STRONGER_CLAIMS_BLOCKED | Final scoped SAB optimization package is assembled; stronger native-perf/full-text/novelty claims remain blocked. |

## Performance Claims

| lane | param | r | evidence_level | mean_speedup | min_speedup | max_speedup | ci95_low | ci95_high | claim_level |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| target_binary_high_stat | SET_2_3_2048 | 2 | 10_run_complete_sab | 1.191 | 1.021 | 1.454 | 1.075307 | 1.306693 | scoped_engineering_supported |
| target_binary_high_stat | SET_2_3_2048 | 4 | 10_run_complete_sab | 1.377 | 1.305 | 1.585 | 1.314893 | 1.438107 | scoped_engineering_supported |
| preferred_explicit_r6_h14_backend | SET_2_3_2048 | 6 | 3_run_complete_sab_plus_stage89_policy | 1.437 | 1.435 | 1.439 |  |  | preferred_explicit_engineering_path_not_default |

## Claim Boundary

| claim_id | status | allowed_wording | blocked_wording |
| --- | --- | --- | --- |
| C1 | ENGINEERING_SUPPORTED | Scoped engineering throughput improvement under tested binary parameters and same backend. | Universal, all-parameter, novelty, or theoretical-optimality claim. |
| C2 | ENGINEERING_SUPPORTED_EXPLICIT_NOT_DEFAULT | Preferred explicit r=6 local engineering path with 3-run/noise/resource support. | Default path promotion or high-stat/paper-level r=6 claim. |
| C3 | final_A8=BLOCKED_EXTERNAL; cb5=BLOCKED_EXTERNAL; stage44_perf=BLOCKED; external_perf=MISSING | Practical implementation evidence only. | Theoretical optimality or hardware-counter-backed memory-operation superiority. |
| C4 | cb6=BLOCKED_EXTERNAL_REVIEW; related=SCOPED_RELATED_WORK_REFRESHED__NOVELTY_STILL_BLOCKED; novelty_gate=BLOCK_NOVELTY_CLAIM_PENDING_MANUAL_REVIEW | Novelty remains unclaimed. | New shared-mask/multiple-body batching invention claim. |
| C5 | final_A8b=MISSING_OPTIONAL_EXTERNAL_EVIDENCE; cb7=BLOCKED_EXTERNAL_FULLTEXT; stage44_fulltext=BLOCKED; stage55_fulltext=BLOCKED; stage55_metadata=PASS; stage55_decision=WAIT_FULLTEXT_ARTIFACT_MANUAL_REVIEW; stage72_fulltext=WAIT_FULLTEXT_ARTIFACT; stage72_author=PASS; stage72_decision=PASS_EXTERNAL_SOURCE_REFRESH_STRONGER_CLAIMS_BLOCKED; related_fulltext=BLOCKED_FULLTEXT; external_fulltext=MISSING | Metadata and implementation context only. | Specific theorem/algorithm/table/figure citations from unreviewed full text. |

## Reproduction

The reproduction commands are recorded in
`repro/stage91_final_package/reproduction_commands.csv`. The package
does not rerun heavy benchmarks; it freezes the current audited evidence
and requires reruns only when source code, backend, platform, or claim
scope changes.
## Stage150 Current-Head Refresh

Stage150 supersedes the older r=6 wording with the current Stage148/149
evidence. The primary endpoint is `T_complete_bootstrap(r)/r`, not raw total
runtime. For the explicit H14 r=6 backend path, Stage148 reports
1.432667x per-lane speedup over
repeated scalar SAB and Stage149 allows only scoped explicit engineering
wording. Default-path, all-parameter, novelty, and theoretical-optimality
claims remain blocked.
