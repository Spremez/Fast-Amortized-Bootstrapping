# Candidate D LUT-Late-Binding Operator SAB Roadmap

Date: 2026-07-20

Controlling design:
`docs/superpowers/specs/2026-07-20-lut-late-binding-operator-sab-design.md`

Current status: design approved; written specification pending user review;
implementation plan not started.

## Objective

Replace the exact-dense r-body selector hot path with a LUT-independent
operator state whose encrypted cost is independent of `r` or subquadratic in
`r`, then bind `r` public LUTs after the sparse SAB schedule.

The primary endpoint is complete:

```text
T_complete_bootstrap / (r * N_active)
```

Kernel-only, backend-only, or key-cache-only improvements do not complete the
objective.

## Immutable Baselines

| ID | Baseline | Role |
|---|---|---|
| B0a | Current repeated scalar SAB | Protocol baseline |
| B0b | Shared-output-key repeated scalar control | Key/cache control |
| B1 | Current exact-dense PVW/MAT-SAB | Main internal baseline |
| B2 | Local BatchBoot reproduction or equivalent relevant port | Latest direct 2025/686 successor |

## Stages

| Stage | Goal | Correctness/Theory Gate | Performance/Resource Gate | Output |
|---|---|---|---|---|
| D0 | Freeze current evidence and repair state drift | A/B/C terminal records unchanged; B0/B1 commands reproduce | No new claim | Frozen baseline manifest |
| D1 | Full-text novelty audit | Claim-level comparison with BatchBoot, Sharing the Mask, multi-value bootstrapping, FDFB^2 (2024/1376), MOSFHET, and Batch Bootstrapping I/II | N/A | Related-work matrix and claim ledger |
| D2 | Infer finite operator closure | Ideal-phase basis-vector equivalence for N=8/16; all negative controls fail; `|Gamma|<=4` | Structural count must be below B1 | Exact checker and terminal verdict |
| D3 | Prove and price Candidate D | Correctness theorem, bounded integer LUT/Torus-scale proof, standard RLWE/GGSW hybrid, covariance-aware noise bound | Complete r=4 Amdahl projection >=10% over B1; legal memory/key model | Admission report |
| D4 | Implement isolated encrypted operators | r=1/2/4 phase and expected-plaintext equivalence | Stable microbench; no hot-path allocation | Experimental key/state and isolated tests |
| D5 | Integrate complete binary/include-zero SAB | Deterministic full output plus multi-seed absolute correctness | Positive complete `T/(r*N_active)` smoke | Complete experimental path |
| D6 | Optimize one measured implementation mechanism | D5 behavior unchanged | At most one layout revision; full-SAB promotion only | Promoted or rejected implementation |
| D7 | Build final evidence matrix | >=50 seeds and >=1e6 observed output coefficients | >=30 paired primary runs; resource and parameter matrix | Paper tables and raw repro pack |
| D8 | Build and audit paper/artifact | Every theorem and claim linked to evidence and real sources | Reproduction commands pass | `PAPER_READY` or scoped rejection |

## Candidate D Stop Rules

Candidate D is rejected when any one of the following remains true after its
single permitted equation revision:

- the operator closure requires more than four channels;
- a required update is not representable using standard RLWE/GGSW objects;
- late binding violates the decoding/noise margin;
- late binding requires Torus-by-Torus multiplication or an unbounded integer
  LUT representation;
- complete r=4 projection is less than 10% better than B1;
- isolated implementation cannot preserve expected plaintext semantics;
- complete SAB has no stable positive result over B1; or
- the complete mechanism is already covered by prior work.

In particular, D1 must reject Candidate D as the primary novelty claim if it
is only a SAB specialization or implementation of the arbitrary-function
amortization already claimed by FDFB^2. Continuing would require a distinct
SAB operator theorem, complexity separation, or complementary composition
whose full-system benefit can be falsified experimentally.

Candidate D permits one state-equation revision, one kernel-layout revision,
and one complete-SAB integration attempt.

## Fallback And Terminal Routing

```text
D passes paper gate
  -> PAPER_READY

D rejected
  -> Candidate E security/novelty preflight

E passes paper gate
  -> PAPER_READY

E rejected
  -> NEW_ALGORITHM_CAMPAIGN_EXHAUSTED
  -> freeze systems result and decide scoped TCHES/systems package
```

Candidate E is an extension-ring or tensor lane-packed SAB. It is reserved,
not active, and receives the same finite revision and integration budget.

## Paper Promotion Threshold

The primary `SET_2_3_2048`, r=4 row must:

- use complete `T/(r*N_active)`;
- have at least 30 paired process samples;
- have a paired 95% confidence interval whose lower bound represents at
  least 5% improvement over B1;
- pass expected-LUT correctness and the parameter-level noise bound;
- report key size, keygen, peak RSS, scratch, and backend;
- separate algorithm, BatchBoot, and AVX512 contributions; and
- include B2 locally or evaluate a combined `D + BatchBoot` path.

## Immediate Next Action

After user review of the written design:

1. invoke the writing-plans workflow;
2. produce an executable D0-D3 implementation/research plan;
3. review that plan before editing algorithm code; and
4. begin with D0 evidence freeze and D1/D2, not with `sab_pvw.c`.
