# Candidate C Rank-Bounded State Gate Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use
> superpowers:subagent-driven-development to implement this plan task by task.
> Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Decide whether a rank-bounded lane-mask accumulator with fixed
`rho<=2` can remain phase-correct and closed across enough of the real SAB
schedule to amortize a public batched relinearization and leave a positive
complete-SAB `T_bootstrap/r` projection.

**Architecture:** Build a source-anchored schedule graph, then a symbolic
finite-field mask-span model that tracks independent mask directions instead
of relying on accidental numeric cancellation. Register a finite set of
Candidate C mechanisms and subject each to phase, rank-growth, closure,
relinearization, complete-cost, and Amdahl gates. This plan changes no C hot
path; a passing mechanism receives a separate key/security/noise and
implementation plan.

**Tech Stack:** Python 3 standard library, `unittest`, JSON-valid YAML,
Markdown, CSV, existing C sources and reproducibility artifacts as read-only
anchors.

## Global Constraints

- Controlling design:
  `docs/superpowers/specs/2026-07-16-ccs-usenix-mat-sab-research-contract-design.md`.
- Repository pre-state is Candidate A `REJECTED`, Candidate B `REJECTED`,
  Candidate C `INTAKE`, Goal `ACTIVE`, paper gate `BLOCKED`, and production
  permission `false`.
- Primary endpoint remains complete-SAB `T_bootstrap/r` against both repeated
  scalar SAB and current exact-dense PVW/MAT-SAB.
- The state is
  `a_q = a_shared + sum_t lambda[q,t] delta_a[t]`; its excess lane-mask rank
  is `rho = rank({a_q-a_0}_{q=1}^{r-1})`.
- Candidate admission requires fixed `rho<=2`; a checker result over a finite
  field is mechanism evidence, not an RLWE security proof.
- Independent symbolic mask directions must remain independent in the model.
  Numeric cancellation from a single random sample cannot establish closure.
- Relinearization/compression is allowed only at a public schedule boundary,
  must preserve every lane phase, and must include key bytes, decomposition,
  transforms, online products, noise, and conversion costs.
- C is rejected before hot-path work if rank reaches the lane maximum
  immediately, if compression is required after every CMUX/NCMUX, or if the
  complete-cost projection is nonpositive.
- At most one Candidate C equation revision may be consumed by this plan.
  No kernel-layout or full-SAB-integration budget is consumed.
- Do not modify C/C++ sources, headers, `main.c`, or `Makefile`.
- Add no dependency.
- Failed evidence is `INCONCLUSIVE`; only a fully evaluated mechanism may be
  admitted or rejected.

---

### Task 1: Anchor The Candidate C State And Real SAB Schedule

**Files:**
- Create:
  `paper_techgraphs/candidate_c_rank_bounded_state.yaml`
- Create:
  `paper_techgraphs/candidate_c_rank_bounded_state_graph.md`
- Create:
  `paper_techgraphs/candidate_c_rank_bounded_state_gaps.md`
- Create:
  `theory_checks/candidate_c_rank_bounded_state_model.md`
- Create:
  `tests/research/test_candidate_c_techgraph.py`

**Interfaces:**
- Consumes:
  `sab_pvw_CMUX`, `sab_pvw_NCMUX`,
  `sab_pvw_RGSW_monomial_mul_state`, `sab_pvw_sparse_mul_binary`,
  `sab_pvw_sub_a_binary_to`, `pvmtmlwe_mul_by_xai`, and
  `mat_trgsw_mul_pvmtmlwe_DFT`.
- Produces: a JSON-valid graph with exact source tokens, state equations,
  schedule edges, candidate variants, and claim gates used by Tasks 2-4.

- [ ] **Step 1: Write source-anchor tests**

  Require one graph anchor for every consumed symbol above, the default
  `out_k=1`, `l=1`, `N=2048` target initializer, Candidate B's terminal
  summary, Stage203 star-cycle equations, and Stage345 exact-dense baseline.

- [ ] **Step 2: Run the source-anchor test and verify RED**

  Run:

  ```text
  python -m unittest tests.research.test_candidate_c_techgraph -v
  ```

  Expected: failure because the Candidate C graph and theory files do not
  exist.

- [ ] **Step 3: Define the state invariant**

  Record, for lane `q`,

  ```text
  a_q = a_shared + sum_(t=1..rho) lambda[q,t] delta_a[t]
  phase_q = b_q - a_q s_q
  rho = rank({a_q-a_0 : q=1,...,r-1})
  ```

  Fix `lambda[0,t]=0` as a representation normalization. State explicitly
  that changing the reference lane does not change `rho`.

- [ ] **Step 4: Map schedule transformations**

  For each CMUX/NCMUX, butterfly, monomial, `sub_a`, and rotation edge, record:

  ```text
  input state
  public linear operation
  newly introduced independent mask directions
  output phase equation
  output rho rule
  next schedule consumer
  ```

  Distinguish current exact-dense PVW closure (`rho=0`) from a proposed
  compact operator that may introduce lane-dependent mask directions.

- [ ] **Step 5: Register exactly three finite variants**

  The graph must define:

  ```text
  C0 = independent_lane_directions
  C1 = rank_two_basis_with_public_lambda
  C2 = rank_two_basis_with_periodic_public_relinearization
  ```

  C0 is a negative control. C1 must close without conversion. C2 may compress
  only after a public block of butterfly steps. No fourth variant is created
  by this plan.

- [ ] **Step 6: Define claim gates**

  Set security, noise, Amdahl, kernel, full-SAB, novelty, and production
  claims to `BLOCKED`. The only allowed Task 1 conclusion is that the current
  state equations and schedule obligations are source anchored.

- [ ] **Step 7: Run focused tests**

  Expected: all Task 1 tests pass and all owned artifacts decode as ASCII.

- [ ] **Step 8: Commit**

  ```text
  git add paper_techgraphs/candidate_c_rank_bounded_state.yaml \
    paper_techgraphs/candidate_c_rank_bounded_state_graph.md \
    paper_techgraphs/candidate_c_rank_bounded_state_gaps.md \
    theory_checks/candidate_c_rank_bounded_state_model.md \
    tests/research/test_candidate_c_techgraph.py
  git commit -m "research: anchor Candidate C rank-bounded state"
  ```

### Task 2: Implement Symbolic Rank-Growth And Phase Controls

**Files:**
- Create: `research/mat_sab/rank_bounded_state_model.py`
- Create: `tests/research/test_rank_bounded_state_model.py`

**Interfaces:**
- Produces:

  ```text
  MaskSpanState
  shared_state(r, modulus)
  lane_difference_matrix(state)
  excess_rank(state)
  append_mask_directions(state, lane_coefficients)
  linear_combine_states(lhs, rhs, lhs_scale, rhs_scale)
  rotate_state(state, exponent)
  phase_vector(state, secrets, modulus)
  compress_state(state, projection)
  schedule_step(state, step)
  ```

  `MaskSpanState` stores a lane-by-symbol coefficient matrix, body constants,
  and a provenance tuple for each independent mask symbol.

- [ ] **Step 1: Write validation tests**

  Reject composite or nonpositive moduli, ragged lane matrices, mismatched
  body/secret counts, a nonzero normalized `lambda[0,*]`, and projections with
  incompatible dimensions.

- [ ] **Step 2: Verify validation tests fail**

  Run:

  ```text
  python -m unittest tests.research.test_rank_bounded_state_model -v
  ```

  Expected: import failure because the model does not exist.

- [ ] **Step 3: Implement shared and independent controls**

  For `r=2,4,6`, require:

  ```text
  shared_state -> rho=0
  one nonshared lane pattern -> rho=1
  two independent patterns -> rho=2
  identity lane patterns -> rho=r-1
  ```

  Use exact Gaussian elimination from
  `research.mat_sab.finite_linear.rank`; do not estimate rank numerically.

- [ ] **Step 4: Implement basis-safe linear combination**

  Symbols from independently randomized operands receive disjoint provenance
  identifiers before combination. Add a mutation test proving that merging
  those identifiers can create a false low-rank result and is rejected.

- [ ] **Step 5: Implement phase controls**

  Build deterministic states over GF(257) and verify

  ```text
  phase_q = body_q - sum_j mask_symbol[j] * coeff[q,j] * secret_q
  ```

  under addition, subtraction, and rotation. Include a hand-derived `r=2`
  oracle and an omitted-direction negative control.

- [ ] **Step 6: Implement compression semantics**

  `compress_state` accepts only a public projection. It must return:

  ```text
  compressed state
  exact phase-preservation result
  discarded independent directions
  online product count
  key component count
  ```

  A projection that discards a phase-active direction must fail. A constructed
  rank-two state projected to its exact span must pass.

- [ ] **Step 7: Run focused and existing research tests**

  Expected: Task 2 tests pass; Candidate A/B tests remain unchanged.

- [ ] **Step 8: Commit**

  ```text
  git add research/mat_sab/rank_bounded_state_model.py \
    tests/research/test_rank_bounded_state_model.py
  git commit -m "research: model Candidate C mask-rank growth"
  ```

### Task 3: Replay The Exact SAB Butterfly Schedule

**Files:**
- Create: `research/mat_sab/candidate_c_schedule.py`
- Create: `tests/research/test_candidate_c_schedule.py`

**Interfaces:**
- Consumes: Task 1 graph and Task 2 model.
- Produces:

  ```text
  load_binary_target_schedule(root)
  replay_variant_schedule(variant, r, modulus)
  ScheduleTrace
  ScheduleTrace.max_rho
  ScheduleTrace.steps_before_compression
  ScheduleTrace.compressions
  ScheduleTrace.phase_gate
  ScheduleTrace.closure_gate
  ```

- [ ] **Step 1: Write exact-count tests**

  For default binary `SET_2_3_2048`, require the replay metadata to record:

  ```text
  h+1 = 40 RGSW monomial calls
  r_prec = 7
  in_N = 2048
  40 * 7 * 2048 = 573440 butterfly selector applications
  ```

  The test must derive `h`, `r_prec`, and `in_N` from `main.c`, not repeat only
  a hard-coded total.

- [ ] **Step 2: Verify schedule tests fail**

  Expected: module import failure.

- [ ] **Step 3: Implement schedule parsing**

  Parse the default target initializer and source control-flow tokens. Reject
  a changed target shape or missing binary schedule branch as inconclusive.
  Do not execute the C implementation in this task.

- [ ] **Step 4: Replay C0**

  Inject independent lane directions at the first compact cycle operation.
  Require the negative control to reach `rho=r-1` for `r=4,6`, proving that
  the checker does not admit every mechanism.

- [ ] **Step 5: Replay C1**

  Use the public two-column `lambda` registered in Task 1. At every
  CMUX/NCMUX and `sub_a` boundary, verify the required lane update lies in the
  current span. The first missing cycle/neighbor term fails closure and names
  the exact graph edge.

- [ ] **Step 6: Replay C2**

  Use the same rank-two span and permit compression only after a public block
  length `B`. Sweep:

  ```text
  B in {1, 2, 4, 8, 16, 32, 64}
  r in {2, 4, 6}
  ```

  Record first rank overflow, maximum `rho`, phase result, number of
  compressions, and completed butterfly count. `B=1` is the
  per-CMUX-relinearization negative control.

- [ ] **Step 7: Add mutation controls**

  Mutate one cycle coefficient, one compression boundary, and one provenance
  identifier. Each mutation must fail a different gate.

- [ ] **Step 8: Run focused and full research tests**

  Expected: exact counts and all negative controls pass.

- [ ] **Step 9: Commit**

  ```text
  git add research/mat_sab/candidate_c_schedule.py \
    tests/research/test_candidate_c_schedule.py
  git commit -m "research: replay Candidate C SAB rank schedule"
  ```

### Task 4: Build Complete-Cost And Amdahl Gates

**Files:**
- Create: `research/mat_sab/candidate_c_cost.py`
- Create: `tests/research/test_candidate_c_cost.py`
- Create: `theory_checks/candidate_c_complete_cost.md`

**Interfaces:**
- Produces:

  ```text
  DenseBaselineCost
  RankBoundedCost
  derive_dense_baseline(root, r)
  cost_rank_bounded(trace, operator_counts, relin_counts)
  minimum_amortizing_block(dense, compact, relin)
  projected_T_bootstrap_over_r(profile, candidate)
  ```

- [ ] **Step 1: Write baseline-source tests**

  Bind the dense operator count to `(r+1)^2` at `out_k=l=1`, bind schedule
  counts to Task 3, and bind measured endpoint/profile inputs to Stage331,
  Stage345, and their artifact hashes. Reject missing or unsupported rows.

- [ ] **Step 2: Verify cost tests fail**

  Expected: import failure.

- [ ] **Step 3: Count complete candidate work**

  Count separately:

  ```text
  decomposition polynomials
  forward DFTs
  external-product add-multiplies
  inverse DFTs/materialization
  state additions/rotations
  compression/relinearization products
  conversion/key-switch products
  evaluation-key bytes
  live scratch bytes
  ```

  Do not convert these counts to latency until a measured per-unit source is
  registered.

- [ ] **Step 4: Compute the amortization threshold**

  For each admitted C2 trace, compute:

  ```text
  B_min = ceil(C_relin / (C_dense_step - C_compact_step))
  ```

  Reject when the denominator is nonpositive or when the trace's valid public
  block length is below `B_min`.

- [ ] **Step 5: Compute bounded Amdahl projections**

  Produce optimistic, measured-central, and pessimistic projections. A
  candidate passes only if measured-central is positive and pessimistic is
  nonnegative against exact-dense `T_bootstrap/r`. Repeated scalar SAB remains
  a reported secondary baseline.

- [ ] **Step 6: Add adversarial controls**

  Inflate compression to dense cost, move one omitted conversion into the
  accounting, and set the optimizable share to zero. All three must reject.

- [ ] **Step 7: Run tests and commit**

  ```text
  git add research/mat_sab/candidate_c_cost.py \
    tests/research/test_candidate_c_cost.py \
    theory_checks/candidate_c_complete_cost.md
  git commit -m "research: gate Candidate C complete cost"
  ```

### Task 5: Generate And Apply The Candidate C Decision

**Files:**
- Create: `scripts/run_candidate_c_rank_bounded_gate.py`
- Create: `tests/research/test_candidate_c_gate.py`
- Create: `scripts/apply_candidate_c_rank_bounded_gate.py`
- Create: `tests/research/test_candidate_c_closeout.py`
- Create: `docs/candidate_c_rank_bounded_mechanism_gate.md`
- Create: `algorithm_variants/candidate_c_rank_bounded_state.md`
- Create: `experiments/candidate_c_rank_bounded_gate_plan.md`
- Create: `repro/candidate_c_rank_bounded_gate/`
- Modify through closeout only: `research_state.yaml`
- Modify through closeout only: `hypotheses/hypothesis_register.yaml`
- Modify through closeout only: `repro/run_log.csv`
- Modify through closeout only: `repro/artifact_manifest.md`
- Modify through closeout only: `repro/reproduction_checklist.md`

**Decision strings:**

```text
ADMIT_CANDIDATE_C_KEY_SECURITY_NOISE_PREFLIGHT
REJECT_CANDIDATE_C_RANK_BOUNDED_STATE_CAMPAIGN_EXHAUSTED
```

- [ ] **Step 1: Write gate tests**

  Require source, equation, symbolic independence, phase, schedule, rank,
  compression, complete-cost, and Amdahl fields in one canonical summary.
  Failed evidence raises an inconclusive error. A decision cannot be changed
  independently of its mechanism fields.

- [ ] **Step 2: Write generator tests**

  Require:

  ```text
  summary.csv
  source_mapping.csv
  schedule_trace.csv
  rank_growth.csv
  compression_gate.csv
  complete_cost.csv
  amdahl_projection.csv
  mechanism_matrix.csv
  proof_gate.csv
  input_manifest.csv
  environment.csv
  artifact_index.csv
  reproduction_commands.md
  ```

  Generate twice and require byte-identical output.

- [ ] **Step 3: Implement the decision rule**

  Admit only if one registered C1/C2 mechanism passes every gate with
  `max_rho<=2`, public compression interval at least `B_min`, exact phase
  preservation, closed next-state consumption, and positive central Amdahl
  projection. Otherwise reject C and exhaust the finite A/B/C campaign.

- [ ] **Step 4: Write atomic closeout tests**

  Test ADMIT and REJECT in temporary roots. On ADMIT, C advances only to
  `ADVERSARIAL_CHECKER_PASS`; production permission remains false. On REJECT,
  set:

  ```text
  C = REJECTED
  active_candidate = C
  goal_status = RESEARCH_CAMPAIGN_EXHAUSTED
  paper_gate = BLOCKED
  production_hot_path_permission = false
  ```

  This is the exact terminal state already enforced by
  `scripts/mat_sab_research_state.py`; do not substitute
  `EXTERNAL_BLOCKED`, which is reserved for unavailable external evidence.

- [ ] **Step 5: Preserve legacy run-log rows safely**

  Reuse Candidate B's canonical-header and exact-marker handling. Preserve
  unrelated historical noncanonical rows, but reject the Candidate C marker
  in any noncanonical field or outside canonical `run_id`.

- [ ] **Step 6: Run generator and closeout twice**

  Require byte-identical artifacts and ledgers on the second run.

- [ ] **Step 7: Run all verification**

  ```text
  python -m unittest discover -s tests/research -p "test_*.py" -v
  python scripts/mat_sab_research_state.py validate
  git diff --check
  ```

- [ ] **Step 8: Commit**

  Commit implementation inputs first, regenerate evidence bound to that
  commit, then commit generated evidence and state separately.

## Completion Boundary

This plan completes one finite mechanism decision, not a bootstrapping
speedup claim.

- On ADMIT: write a separate plan for key distribution, security assumption,
  noise recurrence, and isolated kernel work. Production remains unchanged.
- On REJECT: the finite A/B/C mechanism campaign is exhausted. Preserve the
  exact-dense PVW/MAT-SAB implementation and its scoped measured result; do
  not invent Candidate D automatically.
