# CCS/USENIX MAT-SAB Research Contract Design

Date: 2026-07-16

Status: approved design, implementation plan pending user review

## 1. Research Objective

Design, implement, and validate a new MAT-RLWE/r-body bootstrapping algorithm
for the sparse amortized bootstrapping (SAB) protocol of ePrint 2025/686.
The algorithm must exploit MAT external products at the protocol level, not
only as an AVX512 implementation optimization.

The research goal is successful only when the promoted algorithm:

1. is mathematically specified through its accumulator state, selector/key
   distribution, update equations, correctness invariant, and noise model;
2. has an algorithmic delta beyond the existing exact-dense PVW/MAT-SAB path;
3. beats both repeated scalar SAB and exact-dense PVW/MAT-SAB on complete SAB
   under the same backend and hardware;
4. passes correctness, noise, security-scope, resource, statistical, and
   reproducibility gates; and
5. supports a submission-ready CCS/USENIX Security paper and a source-testable
   repository.

The existing exact-dense result is a baseline and prior positive result. It is
not a successful terminal outcome for this research goal.

Conference acceptance is an external decision. The controllable terminal
state is `PAPER_READY`: a manuscript and artifact package that pass the
internal paper gate defined below. A later external acceptance may be recorded
as `ACCEPTED`, but it is not something the repository can guarantee.

## 2. Current Evidence Boundary

The design starts from the committed Stage346 state.

- Repeated scalar SAB remains the immutable protocol baseline.
- Exact-dense PVW/MAT-SAB is implemented end to end.
- The primary comparison is complete bootstrapping time amortized per lane.
- Six binary r=2/r=4 rows currently report 1.612100x to 1.747647x speedup
  over repeated scalar SAB, with a mean of 1.686741x.
- The current exact-dense path does not establish a new asymptotic SAB
  algorithm or global MAT-SAB optimality.
- Stage138 shows that shared-source compact external products have local
  value, including 1.293981x to 1.491182x r=4 kernel speedup.
- Stage139 shows that the current compact output is not closed as a standard
  shared-mask PVW accumulator.
- Stage134 shows that a generalized lane-pair input restores closure but is
  negative for r=4 because repeated decomposition/DFT work dominates.
- Stage203 records a production-shaped star-cycle selector equation map with
  4r semantically active terms instead of (r+1)^2 dense terms.
- Stage222 verifies the lane-local compact subclass but rejects complete SAB
  integration because neighbor-body terms are missing.
- Stage329 verifies finite semantic-zero equations but leaves production
  keygen, security, noise, and complete-SAB obligations open.
- Broad shared-mask novelty is not available because adjacent packed/common-
  mask bootstrapping work exists. Any novelty claim must be specific to the
  SAB selector, state closure, key distribution, and complete schedule.

These facts define the research bottleneck:

```text
shared decomposition/DFT value
            +
closed r-body SAB state
            +
secure neighbor-capable selector
            +
complete-SAB speedup over exact-dense MAT-SAB
```

No candidate is admissible unless it addresses all four terms.

## 3. Workload And Primary Metric

For each r, define one workload W_r as r independent LUT/SAB lanes evaluated
for the same input/key schedule and the same parameter set.

```text
T_scalar_total(r) = time for r repeated scalar SAB executions
T_dense_total(r)  = time for one exact-dense PVW/MAT-SAB execution
T_new_total(r)    = time for one candidate MAT-SAB execution

L_scalar(r) = T_scalar_total(r) / r
L_dense(r)  = T_dense_total(r)  / r
L_new(r)    = T_new_total(r)    / r

S_new_vs_scalar(r) = T_scalar_total(r) / T_new_total(r)
S_new_vs_dense(r)  = T_dense_total(r)  / T_new_total(r)
```

The primary endpoint is `L_new(r)` together with
`S_new_vs_dense(r)`. `S_new_vs_scalar(r)` remains necessary because it ties
the result to 2025/686, but beating scalar alone is insufficient after the
exact-dense baseline has been established.

Kernel time, AVX instruction counts, or a different FFT backend cannot be
substituted for the complete-SAB endpoint.

## 4. Complexity Model

For k=1, let m=1+r and let T be the gadget decomposition level count. The
current exact-dense MAT external product has:

```text
input decomposition/DFT streams: m*T
dense selector-output products:  m*m*T
output state polynomials:         m
```

The output requirement alone gives an Omega(r) state/write floor. The current
dense selector-output term count is Theta(r^2). This is not a global lower
bound; it is the cost of the current dense representation.

The primary candidate targets a star-cycle support:

```text
x = (a, b_0, ..., b_(r-1))

support = {
  (0,j),
  (j,0),
  (j,j),
  (j,1+(j mod r))
  for j in [1,r]
}
```

This support contains 4r active terms:

| r | dense terms (r+1)^2 | star-cycle terms 4r | dense/star-cycle |
|---:|---:|---:|---:|
| 2 | 9 | 8 | 1.125000 |
| 4 | 25 | 16 | 1.562500 |
| 6 | 49 | 24 | 2.041667 |

If production keygen and closure are valid, selector-output products become
Theta(r), while the m*T input decomposition/DFT and Omega(r) output costs
remain. The resulting external product is expected to be DFT-bound for small
r and increasingly addmul-sensitive as r grows.

This operation-count model is a hypothesis until the production equations are
derived. It must not be used as a theorem or speedup claim before the theory
and experiment gates pass.

## 5. Candidate Portfolio

The project uses a finite A -> B -> C portfolio. A candidate may be revised at
most twice at the equation/checker level, may test at most two kernel layouts,
and may enter complete SAB at most once before a promote/reject decision.

### Candidate A: Star-Cycle Sparse MAT-GGSW

Hypothesis:

> A production selector whose semantic support is the Stage203 star-cycle
> pattern can preserve the r-body SAB phase invariant while reducing selector
> evaluation from dense Theta(r^2) terms to Theta(r) terms.

Required mathematical object:

```text
C = (a, b_0, ..., b_(r-1))
phase_q(C) = b_q - <a, s_q>

For every SAB step F and lane q:
phase_q(F_structured(C)) = phase(F_scalar(C_q)).
```

Required proof/checker scope:

- selector zero/one semantics;
- mask-output/body-input terms;
- body-output/mask-input terms;
- self and cyclic-neighbor body terms;
- CMUX and NCMUX;
- one complete RGSW monomial butterfly;
- sparse_mul and sub_a lifecycle;
- extraction and packing-key-switch boundary;
- negative controls for omitted active terms, invalid shared-output collapse,
  and nonzero dummy semantics.

Production keygen must explain why the evaluator can use the structured
support without exposing secret-dependent information or breaking the
ciphertext phase relation. Security must be reduced to explicitly stated
RLWE/GGSW assumptions. Any circular/KDM-style assumption must be compared
explicitly with the 2025/686 baseline, and any stronger assumption must be
justified; otherwise the candidate is rejected.

Failure conditions:

- the state is not closed after one allowed equation revision;
- production keygen requires secret-dependent public sparsity;
- the security argument needs an unstated stronger assumption;
- noise or resource growth removes the predicted value;
- the isolated kernel cannot beat exact-dense after two layouts; or
- complete SAB does not beat exact-dense under the paper gate.

### Candidate B: Factorized Star-Cycle

Candidate B preserves the same semantic operator but realizes it as four
standard encrypted operator families:

```text
M = M_shared_row + M_shared_column + M_diagonal + M_cycle
```

The purpose is to avoid relying on independently skippable entries inside a
dense PVW ciphertext row. It may use more key objects and more additions than
Candidate A, but its security argument should inherit more directly from
standard encrypted linear operators.

Promotion requires:

- exact equality to the star-cycle oracle;
- a closed r-body accumulator;
- a key distribution whose public shape is independent of secret values;
- Theta(r) active encrypted operators;
- an Amdahl projection that leaves measurable complete-SAB value; and
- complete-SAB improvement over exact-dense MAT-SAB.

Candidate B is rejected if factorization reconstructs the original dense
cost, needs per-lane repeated DFTs equivalent to Stage134, or moves the cost to
an equally expensive key-switch/relinearization step.

### Candidate C: Rank-Bounded Shared-Mask State

Candidate C changes the accumulator representation rather than requiring an
immediately shared output mask.

```text
a_q = a_shared + sum_{t=1..rho} lambda[q,t] * delta_a[t]

state = (a_shared, delta_a[1..rho], lambda, b[0..r-1])
```

The finite checker must measure rank growth under CMUX/NCMUX, RGSW monomial,
sparse_mul, and sub_a. A periodic batched relinearization is allowed only at a
public schedule boundary and must restore rho to the configured bound without
changing any lane phase.

Candidate C is admitted only if a fixed rho <= 2 survives enough schedule
steps for saved compact external products to amortize relinearization. It is
rejected before hot-path implementation if rank reaches r immediately, if a
relinearization is required after every CMUX, or if the cost model is not
positive against exact-dense MAT-SAB.

## 6. Research Loop

Each candidate follows the same state machine:

```text
INTAKE
  -> TECHGRAPH_ANCHORED
  -> EQUATIONS_DEFINED
  -> ADVERSARIAL_CHECKER_PASS
  -> KEY_SECURITY_NOISE_PREFLIGHT_PASS
  -> AMDAHL_PROJECTION_PASS
  -> ISOLATED_KERNEL_PASS
  -> FULL_SAB_PASS
  -> PAPER_GATE_PASS
```

Every transition must add at least one of:

- a source-anchored technical graph edge;
- a mathematical derivation;
- an executable checker with negative controls;
- production code behind an explicit flag/path;
- a real measurement;
- a verified citation/claim row; or
- manuscript content backed by evidence.

A stage that only restates prior conclusions is prohibited.

Failure routing is deterministic:

```text
A rejected -> start B
B rejected -> start C
C rejected -> RESEARCH_CAMPAIGN_EXHAUSTED
```

`RESEARCH_CAMPAIGN_EXHAUSTED` is a blocked research result. It is not Goal
completion, and it does not automatically create another candidate or Stage.
A new campaign requires a genuinely new mechanism, changed theorem
assumption, new paper evidence, or explicit user authorization.

Once one candidate passes the paper gate, algorithm exploration freezes.
Further source changes must serve correctness, reproducibility, measured
performance, artifact quality, or reviewer-critical ablations.

## 7. Correctness, Security, And Noise Gates

Correctness gates:

- symbolic/finite state equivalence for r=2 and r=4;
- stress validation for r=6;
- exact negative controls for each removed or factorized term;
- stepwise phase equivalence through the complete binary SAB schedule;
- deterministic full-SAB output equivalence;
- scalar and exact-dense default behavior unchanged.

Security gates:

- public key shape and metadata do not reveal secret-dependent selector data;
- encrypted zero/dummy handling has an explicit indistinguishability argument;
- any circular/KDM assumption is stated and compared with the baseline;
- no security claim is inferred from a finite arithmetic checker;
- parameter/security estimates are regenerated for changed key material.

Noise gates:

- derive per-external-product and per-schedule-step recurrence;
- compare structured, factorized, or relinearized noise against exact-dense;
- measure stage and final-output noise over registered seeds;
- do not infer cryptographic failure probability from empirical trials alone;
- reject parameter rows whose correctness margin is not justified.

## 8. Performance And Statistical Gates

Baselines:

- B0: repeated scalar SAB;
- B1: exact-dense PVW/MAT-SAB current-head implementation;
- B2: the strongest relevant recent implementation when a runnable fair
  comparison exists; otherwise report a source-backed table comparison.

Fairness requirements:

- same machine, compiler, optimization flags, FFT backend, parameters, and
  workload for B0/B1/candidate;
- interleaved paired execution order;
- warmup separated from recorded runs;
- instrumentation disabled for final latency claims;
- AVX512/backend effects reported separately from algorithm effects.

Primary experiment:

- BINARY SET_2_3_2048, r=4;
- at least 30 paired process-level timing samples;
- paired speedup, mean, median, standard deviation, coefficient of variation,
  and 95% bootstrap confidence interval;
- complete `T_bootstrap/r` as the primary endpoint.

Supporting experiments:

- r=2 and r=6;
- SET_4_5_2048 and SET_2_3_4096 in addition to the primary parameter;
- at least 10 paired samples per supporting row before a scoped claim;
- scaling against r, N, h, r_prec, key size, scratch, and peak RSS;
- correctness/noise seeds registered before execution.

Paper performance promotion is disjunctive:

1. If the candidate proves a leading selector-work reduction from Theta(r^2)
   to Theta(r), the primary-row 95% confidence interval for
   `S_new_vs_dense` must have lower bound greater than 1.0, the mean gain must
   be at least 5%, and at least two supporting rows must be positive.
2. If the contribution is constant-factor only, the primary mean gain over
   exact-dense must be at least 10%, its 95% confidence interval lower bound
   must exceed 1.0, and at least two supporting rows must show at least 5%
   mean gain.

These are promotion thresholds, not promised outcomes. They prevent timing
noise or a backend-only effect from being presented as a new algorithm.

## 9. Resource Gate

Every promoted row reports:

- bootstrapping key bytes;
- key-generation time;
- peak RSS;
- accumulator and scratch bytes;
- final output count;
- latency per lane;
- throughput per second;
- noise margin; and
- compiler/backend/hardware identifiers.

A resource increase is allowed only when it is explicit and the throughput or
algorithmic benefit remains defensible. A hidden key, memory, or keygen
increase invalidates the paper gate.

## 10. Literature And Novelty Gate

The final novelty review must include full-text, claim-level comparison with:

- ePrint 2025/686 and its CCS version;
- prior amortized bootstrapping and ring-packing work;
- recent amortized bootstrapping improvements;
- Sharing the Mask/common-mask packed-message bootstrapping;
- TFHE/GGSW external-product and packed-operation work;
- MOSFHET and relevant AVX/FFT backend work; and
- any paper published before the manuscript search-freeze date that changes
  the star-cycle, sparse selector, low-rank state, or multi-output claim.

The literature search-freeze date is recorded when the manuscript enters
paper freeze. Claims use a sentence-level source ledger. No `first`, `novel`,
`optimal`, or asymptotic comparison enters the manuscript without a verified
source and derivation row.

## 11. Codex Research Roles

Codex work is separated into independently checked roles:

1. Protocol analyst: maintains the 2025/686 technical graph, state equations,
   operation counts, and claim boundaries.
2. Hypothesis author: proposes one candidate card at a time.
3. Adversarial reviewer: constructs counterexamples, negative controls, and
   proof-obligation failures before production integration.
4. Implementer: writes isolated reference code first, then optimized code
   behind explicit paths without changing scalar defaults.
5. Experiment auditor: checks baseline fairness, statistics, environment,
   resources, and reproducibility before promoting a result.
6. Literature verifier: validates real full-text sources and sentence-level
   citation support.
7. Paper reviewer: applies a CCS/USENIX-style internal review rubric and turns
   each criticism into an evidence task or a scoped limitation.

The hypothesis author may not upgrade its own claim without the adversarial,
experiment, and literature gates.

## 12. Repository And Paper Deliverables

The final source-testable repository must provide:

- a stable scalar SAB path;
- a stable exact-dense MAT-SAB baseline;
- a named candidate/new-algorithm path;
- independent correctness and benchmark executables rather than relying only
  on compile-time branches in the monolithic main program;
- one documented correctness smoke command;
- one documented primary benchmark command;
- one paper-table reproduction command;
- machine-readable result output;
- environment, baseline, seed, command, commit, raw-log, and failure records;
- generated tables/figures linked to raw results; and
- a clean public README explaining supported platforms and claims.

The submission-ready paper package must contain:

- compilable LaTeX and bibliography;
- abstract and contribution list constrained by the claim ledger;
- SAB and MAT-RLWE preliminaries;
- the new state/selector/schedule algorithm and pseudocode;
- correctness, complexity, noise, and security analysis;
- implementation and AVX512/backend section;
- experimental methodology and all baselines;
- complete-SAB timing, scaling, resource, and ablation results;
- related work based on verified sources;
- limitations and negative results; and
- artifact/reproduction instructions.

## 13. Terminal States

Allowed terminal states are:

| state | meaning | Goal complete |
|---|---|---|
| PAPER_READY | A/B/C candidate passes every algorithm, experiment, novelty, artifact, and manuscript gate. | yes |
| ACCEPTED | External conference acceptance recorded after PAPER_READY. | yes |
| CANDIDATE_REJECTED | One candidate fails a registered gate and routes to the next candidate. | no |
| RESEARCH_CAMPAIGN_EXHAUSTED | A, B, and C all fail; no automatic new candidate is allowed. | no, blocked |
| EXTERNAL_BLOCKED | Required hardware, source, or reviewer input is unavailable after documented attempts. | no, blocked |

The project must never mark the Goal complete merely because documentation is
extensive, a stage number increased, a kernel microbenchmark improved, or the
exact-dense fallback remains publishable as an engineering result.

## 14. Approved Execution Order

After this design is reviewed, the implementation plan must begin with:

1. freeze and simplify the active Goal/roadmap around this contract;
2. build a source-anchored 2025/686 selector/state technical graph;
3. formalize Candidate A production equations and key distribution;
4. implement an adversarial star-cycle closure checker before SAB hot-path
   changes;
5. execute Candidate A through the fixed research state machine;
6. route to Candidate B or C only on a recorded Candidate A rejection; and
7. enter paper freeze immediately after the first candidate passes the paper
   gate.

No SAB hot-path change is authorized by this design alone. Production changes
start only after the implementation plan is written and reviewed.
