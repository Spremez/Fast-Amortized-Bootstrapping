# Stage90 External Claim Unlock Plan

Date: 2026-06-26

## Goal

Turn the remaining stronger-claim blockers into a fresh, auditable Stage90
probe after Stage89 promoted H14-C1 as the preferred explicit r=6 local
engineering path.

Stage90 does not change scalar SAB, does not change `sab_pvw_*` defaults, and
does not run a new complete-SAB benchmark. It only answers whether the project
now has enough external evidence to upgrade any of these claims:

- MAT-AVX512 hardware-counter-backed load/store/FMA attribution;
- theorem-level or algorithm/table/figure citation claims from 2025/686;
- novelty wording beyond the currently safe scoped engineering claim.

## Inputs

- Stage89 H14 promotion-policy decision.
- Fresh Stage27-style 2025/686 citation/full-text route probe.
- Fresh Stage28 native perf-counter gate.
- External evidence intake registry.
- Stage62 full-text unlock summary.
- Stage72 author/DOI/code/full-text source refresh.
- Remaining blocker dashboard rows CB5, CB6, and CB7.

## Commands

```bash
STAGE90_OUT_DIR=repro/stage90_external_claim_unlock \
STAGE90_RUN_NATIVE_BENCH=1 \
bash scripts/run_stage90_external_claim_unlock.sh
```

## Correctness Gate

There is no SAB arithmetic correctness gate in Stage90 because it is an
external-claim control-plane stage. The correctness condition is evidence
integrity:

- Stage89 precondition is present and passing.
- Fresh citation probe output exists.
- Fresh native-perf gate output exists.
- External evidence intake output exists.
- Stage90 summary records a decision without upgrading blocked claims unless
  the required external artifacts are actually present.

## Claim Gate

Stage90 may only unlock stronger wording if all required evidence is present:

- Native perf gate reports usable hardware counters and a benchmark run, or an
  externally registered Stage28 summary reports counter attribution.
- A local or directly accessible 2025/686 full text is registered.
- Novelty/source review is explicitly marked review-ready with source anchors.

Otherwise Stage90 must keep stronger claims blocked.

## Failure Handling

- If Stage89 is missing or failed, stop and repair the local route first.
- If network probes fail transiently, preserve the raw logs and rerun the
  Stage90 runner.
- If only metadata/code routes are reachable, keep theorem-level and novelty
  claims blocked.
- If native perf is missing, keep MAT-AVX512 theoretical optimality claims
  blocked.

## Expected Current Outcome

Under the current WSL2 environment, Stage90 is expected to record a passing
probe with stronger claims still blocked:

```text
PASS_STAGE90_EXTERNAL_CLAIM_UNLOCK_PROBE_RECORDED_STRONGER_CLAIMS_BLOCKED
```
