# Loop Engineering for PVW/MAT-SAB

Date: 2026-06-25

This file defines the required engineering loop for all future PVW/MAT-SAB
optimization work. It is intentionally stricter than a normal performance
iteration because the project aims to support both engineering decisions and
possible paper claims.

## Loop Contract

Every optimization candidate must pass through the same sequence:

```text
hypothesis
  -> theory and cost model
  -> explicit-flag implementation
  -> staged correctness
  -> target correctness
  -> microbench or profile
  -> complete SAB A/B benchmark
  -> profile attribution
  -> noise/resource gate if positive
  -> promote, neutralize, or reject
  -> update docs, hypotheses, repro pack
```

Skipping a step is allowed only when the candidate is explicitly marked
`deferred`, `neutral`, or `rejected`.

## Required Records

Each candidate needs:

- hypothesis ID in `hypotheses/hypothesis_register.yaml`;
- algorithm or implementation note when the delta changes behavior or layout;
- theory note when the claimed mechanism depends on complexity, memory traffic,
  register pressure, noise, or security assumptions;
- experiment plan before running promoted benchmarks;
- raw logs and summaries under `repro/`;
- final decision in the relevant stage log.

## Correctness Gates

Minimum gates for code candidates:

1. staged small-shape or isolated equivalence test;
2. target-shape full-output equivalence;
3. scalar baseline regression where the change touches shared code;
4. deterministic seed sweep if the candidate is promoted beyond smoke;
5. noise comparison if ciphertext boundaries, extract, KS, or accumulation
   order change.

Correctness failure rule:

```text
Any correctness failure blocks promotion. The candidate may continue only as a
debug branch or recorded negative result.
```

## Performance Gates

Performance must be interpreted in layers:

| layer | evidence allowed |
|---|---|
| kernel | isolated external product or helper microbench |
| body | no-extract PVW body profile |
| full SAB | complete `sab_pvw_*` versus repeated scalar SAB |
| backend | absolute timing under a different FFT/SIMD backend |
| paper | full SAB plus correctness/noise/resource/statistical/literature gates |

Rules:

- same-backend full SAB A/B is the primary speedup metric;
- one-run results are smoke only;
- instrumented profile timing cannot be used as final latency unless labeled;
- backend/SIMD absolute gains are not algorithmic gains;
- a kernel win that does not improve full SAB remains a kernel-only result.

## Statistical Sanity

For any promoted performance claim:

- use repeated process-level runs, not only inner-loop reps;
- report mean, min, max, and sample variability when available;
- include negative and neutral ablations;
- avoid tuning the implementation based on the final benchmark only;
- report practical significance, not just a positive mean;
- keep target `r=4` as the stress case and `r=2` as a stability check.

Default promotion policy:

```text
Promote only if every correctness gate passes, every accepted timing run is
positive, and the full SAB mean improves beyond normal Stage 16/18 variability.
If the evidence is positive but narrow, keep the flag explicit and scope the
claim.
```

## Failure Handling

Use these outcomes:

| outcome | meaning | next action |
|---|---|---|
| `promote` | full gates pass and full SAB improves | make it the next comparison baseline, still behind policy-controlled flags |
| `neutral` | correct but no full SAB improvement | keep as ablation, do not default-enable |
| `reject` | incorrect, unstable, or resource-costly | preserve logs and disable path |
| `defer` | profile says the target is not yet material | record condition for revisit |

## Repro Pack Update Checklist

After each loop:

- add or update the stage log in `docs/`;
- add raw logs and summaries under `repro/`;
- update `repro/run_log.csv`;
- update `repro/reproduction_checklist.md`;
- update `repro/artifact_manifest.md` if files were added;
- update the hypothesis status and current decision;
- commit the result before starting the next independent loop.

## Claim Guardrails

Allowed:

```text
The r=4 PVW/MAT-SAB path improves complete SAB throughput by X under backend B,
parameter P, and validation protocol V.
```

Not allowed unless separately proven:

```text
The MAT external product alone proves SAB bootstrapping is accelerated.
The AVX512 backend result is an algorithmic speedup over another backend.
The result is a new cryptographic contribution without a literature audit.
The result generalizes to untested parameters or branches.
```

## External Evidence Unlock Loop

Stage101-103 close the former external blockers, but only within scoped claim
boundaries:

- Stage101 native perf counters may be used for attribution; they are not a
  standalone proof of theoretical MAT-AVX512 optimality.
- Stage102 2025/686 anchors may be used for protocol, complexity,
  correctness/noise, and parameter citations within the reviewed page/section
  scope; PVW/MAT statements still require local implementation evidence.
- Stage103 novelty review allows scoped systems/engineering wording and rejects
  broad shared-mask, batch/SIMD, new-asymptotic, all-parameter, and non-binary
  novelty wording.

Any future paper-writing loop must cite the exact stage artifact that supports
each claim and label unsupported stronger wording as blocked, not pending.
