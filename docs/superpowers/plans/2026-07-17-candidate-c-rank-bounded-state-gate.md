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
of relying on accidental numeric cancellation. After the support-only
schedule gate, consume one equation revision to synthesize a concrete
gadget-indexed operator tensor or a scoped obstruction, then gate any
secret-dependent relinearization before complete-cost work. Register a finite
set of Candidate C mechanisms and subject each to phase, rank-growth, closure,
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
- Task 3A consumes the one permitted Candidate C equation revision described
  by
  `docs/superpowers/specs/2026-07-17-candidate-c-operator-tensor-revision-design.md`.
  No further equation rewrite, kernel-layout budget, or full-SAB-integration
  budget is permitted.
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
  two independent patterns -> rho=min(2,r-1)
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

### Task 3A: Synthesize Or Obstruct The Concrete C1 Operator Tensor

**Files:**
- Create: `research/mat_sab/candidate_c_operator_tensor.py`
- Create: `tests/research/test_candidate_c_operator_tensor.py`
- Create: `theory_checks/candidate_c_operator_tensor.md`

**Interfaces:**
- Consumes:
  `docs/superpowers/specs/2026-07-17-candidate-c-operator-tensor-revision-design.md`,
  `MaskSpanState`, Task 3's exact schedule metadata, the Stage203
  support-only map, Candidate A's phase solver, the Stage222 lane-local
  compact operator, and the current exact-dense MAT keygen/operator.
- Produces:

  ```text
  PhaseProjection
  OperatorTensor
  EvaluatorSampleRelationAudit
  OperatorGateResult
  build_phase_projection(public_lambda, secrets, mu, modulus)
  build_dense_control_tensor(r, mu, secrets, gadget, n, modulus)
  build_rank_bounded_tensor(
      r, rho, mu, secrets, gadget, n, modulus, public_lambda)
  verify_phase_identity(tensor, projection)
  concatenated_mask_difference_rank(tensor)
  build_evaluator_sample_matrix(tensor)
  audit_evaluator_sample_relations(tensor, projection)
  run_c1_operator_gate(root, r, modulus)
  ```

- [ ] **Step 1: Write equation and source-binding tests**

  Fix `d=rho+1`, one public `Lambda in GF(257)^(r x d)`, the exact surrogate
  ring `GF(257)[X]/(X^8+1)`, and ordered input components

  ```text
  M_0,...,M_(d-1),B_0,...,B_(r-1).
  ```

  Require separate `K_0` and `K_1` tensor objects and

  ```text
  P_Lambda[q,M_u] = -Lambda[q,u] s_q
  P_Lambda[q,B_j] = 1 if q=j and 0 otherwise
  B_mu[t,q,c] - s_q sum_v Lambda[q,v] A_mu[t,v,c]
    = mu h_t P_Lambda[q,c].
  ```

  Require every `A_mu`, `B_mu`, and `s_q` entry to be a length-8 polynomial
  vector and every multiplication to use exact negacyclic convolution.

  Bind the dense control to current MAT keygen/operator source tokens. Bind
  Stage203 as support-only and reject any attempt to read coefficients from
  it.

- [ ] **Step 2: Verify RED**

  Run:

  ```text
  python -m unittest tests.research.test_candidate_c_operator_tensor -v
  ```

  Expected: import failure because the operator module does not exist.

- [ ] **Step 3: Implement exact tensor and phase controls**

  Use exact arithmetic in `GF(257)[X]/(X^8+1)` and test `r=2,4,6`,
  `mu=0,1`, every gadget level, input component, and coefficient basis
  vector. The dense positive control must satisfy the phase identity. A
  phase mutation in one `(mu,t,c,q,coefficient)` entry must fail the same
  verifier.

- [ ] **Step 4: Implement the arbitrary-input rank gate**

  Let `L=I-1e_0^T` and

  ```text
  Abar_mu[t,q,c] = sum_v Lambda[q,v] A_mu[t,v,c].
  ```

  Replace every `A_mu[t,v,c]` polynomial by its `8 x 8` negacyclic
  convolution matrix and concatenate the basis-output blocks into
  `R_mu in GF(257)^(d*8 x ell*(d+r)*8)`. Define
  `T_mu=(Lambda tensor I_8)R_mu`, equivalently the lane-stacked convolution
  matrix of every `Abar`, so
  `T_mu in GF(257)^(r*8 x ell*(d+r)*8)`. Require

  ```text
  ((L tensor I_8) T_mu)
    = ((L Lambda) tensor I_8) R_mu
  rank((L tensor I_8) T_mu) <= min(2,r-1) * 8.
  ```

  Do not call this field rank `rho`; it is the exact finite surrogate of
  module rank `rho`. Do not infer it from Stage203 support. Add a full-rank
  C0 control, a common-`Lambda` rank-two control, and a control where each
  level separately satisfies the field bound but their joint span exceeds
  `rho*8`.

- [ ] **Step 5: Implement the evaluator-sample relation preflight**

  Audit `K_0` and `K_1` separately. For one fixed `mu`, put
  `m=ell*(d+r)`. Build
  `S_mu in GF(257)^(m x d*8)`, whose row `(t,c)` concatenates the
  coefficients of every `A_mu[t,v,c]`, and
  `M_mu,q in GF(257)^(m x 8)`, whose row contains the corresponding
  lane-q phase/message polynomial. For every exact scalar relation
  `z in GF(257)^m` in the left kernel of `S_mu`, compute the retained
  message separately for each secret lane:

  ```text
  z^T S_mu = 0
  z^T M_mu,q for q=0,...,r-1
  ```

  Include:

  ```text
  shared-mask PVW control -> no unsupported insecurity decision
  independent-mask dense control -> no unsupported insecurity decision
  explicit same-secret zero-error cancellation -> decisive synthetic FAIL
  one sample/message mutation -> changed diagnostic
  ```

  For every retained-message relation, record centered coefficients, L1/L2
  norms, retained centered message gap, symbolic error multiplier, and any
  registered sigma/error inequality. Without a registered error distribution
  and decision inequality, emit
  `RELATION_RECORDED_NO_SECURITY_DECISION`; containment failure alone cannot
  reject C1. Only a registered inequality proving distinguishability after
  combined relation error may emit
  `REGISTERED_SHORT_ERROR_RELATION_FAIL`. State that this is a finite
  diagnostic, not an RLWE/PVW security proof or a universal impossibility
  theorem.

- [ ] **Step 6: Count the complete evaluator object**

  Count mask roots, body polynomials, gadget rows, decomposition inputs,
  add-multiplies, transforms, public mixing coefficients, and bytes. A
  factorization that reconstructs `Theta(r^2)` body work cannot pass the
  structural improvement gate.

- [ ] **Step 7: Emit one terminal C1 decision**

  The only decisions are:

  ```text
  ADMIT_C1_OPERATOR_TO_SCHEDULE_REPLAY
  ROUTE_PHASE_CORRECT_HIGH_RANK_OPERATOR_TO_C2
  REJECT_C1_PHASE_IDENTITY_TERMINAL
  REJECT_C1_NONPOSITIVE_STRUCTURAL_COST_TERMINAL
  REJECT_C1_REGISTERED_SHORT_ERROR_RELATION_TERMINAL
  TERMINAL_INCONCLUSIVE_C1_EVIDENCE_EXHAUSTED
  ```

  The C2 route must include a concrete, hash-bound, phase-correct seed tensor.
  A phase failure or nonpositive C1 structural cost is terminal because
  relinearization cannot repair it. The sample-relation record is attached
  but cannot become a security verdict without its missing noise inequality.
  A registered `REGISTERED_SHORT_ERROR_RELATION_FAIL` is terminal and
  explicitly excludes both admission and C2 routing. A decision must be
  derived from phase, joint-rank, relation status, and evaluator counts;
  changing only the decision field must fail.

- [ ] **Step 8: Write the theory record**

  Record equations, matrix orientations, dimensions, exact controls, result
  scope, and the next route. The record must distinguish a concrete tensor
  from support-only and random finite witnesses.

- [ ] **Step 9: Run focused and full tests**

  Expected: all exact controls pass, every C1 result is derived from a
  complete finite tensor or becomes terminal inconclusive, and the full
  research suite remains green.

- [ ] **Step 10: Commit**

  ```text
  git add research/mat_sab/candidate_c_operator_tensor.py \
    tests/research/test_candidate_c_operator_tensor.py \
    theory_checks/candidate_c_operator_tensor.md
  git commit -m "research: gate Candidate C operator tensor"
  ```

### Task 3B: Specify And Gate C2 Secret-Dependent Relinearization

**Files:**
- Create: `research/mat_sab/candidate_c_relinearization.py`
- Create: `tests/research/test_candidate_c_relinearization.py`
- Create: `theory_checks/candidate_c_relinearization.md`

**Interfaces:**
- Consumes: Task 3's exact event stream and only a Task 3A
  `ROUTE_PHASE_CORRECT_HIGH_RANK_OPERATOR_TO_C2` result carrying its
  hash-bound phase-correct seed tensor, projection, sample-relation audit,
  and structural evaluator counts. A phase-invalid or evidence-inconclusive
  C1 result cannot enter Task 3B.
- Produces:

  ```text
  AccumulatorDependencyGraph
  RelinearizationSpec
  ConversionMaterial
  ConversionCost
  build_accumulator_dependency_graph(schedule)
  verify_relinearization_phase(spec)
  derive_conversion_material(spec)
  count_conversion_work(spec, schedule)
  classify_public_block(schedule, B)
  run_c2_relinearization_gate(root, r, B, modulus)
  ```

- [ ] **Step 1: Write dependency-graph tests**

  Assign every selector output an identity

  ```text
  (monomial_call, bit, accumulator_index)
  ```

  and connect it to its exact next consumer. Prove by test that consecutive
  selector events in one loop usually update independent accumulator
  indices; they are not repeated updates of one state.

- [ ] **Step 2: Verify RED**

  Expected: import failure for the relinearization module.

- [ ] **Step 3: Define the phase-preserving conversion**

  Require for every lane:

  ```text
  tilde_b_q = b_q + (tilde_a_q-a_q) s_q
  phase(tilde_a_q,tilde_b_q) = phase(a_q,b_q).
  ```

  A public projection without correction material must fail. A finite
  secret-aware positive control must pass. A correction-sign mutation must
  fail the same phase verifier.

- [ ] **Step 4: Register evaluation material**

  Name every key sample needed to evaluate the secret-dependent correction.
  Record source secret, target mask basis, gadget levels, error term, public
  metadata, and consumer. Missing material is inconclusive, not zero cost.

- [ ] **Step 5: Separate postponement from batching**

  For every `B in {1,2,4,8,16,32,64}`, classify whether the block:

  ```text
  postpones conversion on one live state
  batches B independent states
  crosses a butterfly-bit dependency boundary
  requires conversion before the next selector
  ```

  Do not divide conversion work by `B` unless one registered cryptographic
  product actually serves all `B` states.

- [ ] **Step 6: Count structural conversion cost**

  Count discarded directions, decompositions, forward transforms,
  key-sample products, inverse transforms, additions, key bytes, and scratch.
  Bind dense comparison counts to Task 3A. Reject an omitted correction or
  a denominator that assumes free batching.

- [ ] **Step 7: Emit one terminal C2 decision**

  The only decisions are:

  ```text
  ADMIT_C2_RELINEARIZATION_TO_SCHEDULE_REPLAY
  REJECT_C2_CONVERSION_CLOSURE
  REJECT_C2_NONPOSITIVE_STRUCTURAL_COST
  TERMINAL_INCONCLUSIVE_C2_EVIDENCE_EXHAUSTED
  ```

  Incomplete evidence selects the explicit terminal-inconclusive artifact; it
  cannot be converted to rejection or passed to schedule replay.

- [ ] **Step 8: Run tests and commit**

  ```text
  git add research/mat_sab/candidate_c_relinearization.py \
    tests/research/test_candidate_c_relinearization.py \
    theory_checks/candidate_c_relinearization.md
  git commit -m "research: gate Candidate C relinearization"
  ```

### Task 3C: Replay Only A Registered Candidate C Operator

**Files:**
- Create: `research/mat_sab/candidate_c_registered_replay.py`
- Create: `tests/research/test_candidate_c_registered_replay.py`

**Interfaces:**
- Consumes: Task 3's source-bound event iterator and exactly one terminal
  Task 3A/3B result: an admitted C1 tensor, an admitted C2 tensor plus
  conversion specification, a scoped rejection, or terminal inconclusive
  evidence exhaustion.
- Produces:

  ```text
  RegisteredScheduleTrace
  RegisteredOperatorArtifact
  CandidateCTerminalRecord
  replay_registered_operator(root, operator_result, conversion_result)
  registered_operator_for_task4(root)
  terminal_record_for_task5(root)
  ```

- [ ] **Step 1: Write admission-binding tests**

  Reject support-only Stage203 rows, random Stage329 matrices, a fabricated
  C1 decision, and a C2 decision without conversion material. Accept only an
  object whose recomputed canonical hash binds:

  ```text
  all K_0/K_1 tensor coefficients
  dimensions and GF(257)/n/gadget parameters
  public Lambda and finite secret witnesses
  source-anchor hashes
  exact Task 3 schedule hash
  Task 3A equation/gate result
  all C2 conversion material and structural costs, when present
  terminal decision
  ```

- [ ] **Step 2: Verify RED**

  Expected: import failure for the registered replay module.

- [ ] **Step 3: Replay per-state phase and rank**

  Traverse all `573440` selector events and exact boundaries. Propagate each
  accumulator-state identity separately. Verify phase and rank after every
  operator and every registered conversion; do not extrapolate one state to
  unrelated indices.

- [ ] **Step 4: Add adversarial controls**

  Mutate one tensor coefficient, one state edge, one conversion boundary,
  and one conversion-key identity. Each must fail a distinct recomputed gate.

- [ ] **Step 5: Authorize or block Task 4**

  `registered_operator_for_task4` returns exactly one admitted, hash-bound
  C1/C2 object or raises `NoRegisteredCandidateCOperator`. Task 4 must not run
  on that exception. Rejected and terminal-inconclusive routes instead emit
  one `CandidateCTerminalRecord` for Task 5; neither can be silently converted
  to the other.

- [ ] **Step 6: Run tests and commit**

  ```text
  git add research/mat_sab/candidate_c_registered_replay.py \
    tests/research/test_candidate_c_registered_replay.py
  git commit -m "research: replay registered Candidate C operator"
  ```

### Task 4: Build Complete-Cost And Amdahl Gates

**Files:**
- Create: `research/mat_sab/candidate_c_cost.py`
- Create: `tests/research/test_candidate_c_cost.py`
- Create: `theory_checks/candidate_c_complete_cost.md`

**Interfaces:**
- Consumes: exactly one object returned by
  `registered_operator_for_task4(root)`, including its complete canonical
  object hash. If no registered operator exists, Task 4 is skipped and Task
  3C routes its terminal record directly to Task 5.
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
- Modify: `scripts/mat_sab_research_state.py`
- Modify: `tests/research/test_research_state.py`
- Modify through closeout only: `research_state.yaml`
- Modify through closeout only: `hypotheses/hypothesis_register.yaml`
- Modify through closeout only: `repro/run_log.csv`
- Modify through closeout only: `repro/artifact_manifest.md`
- Modify through closeout only: `repro/reproduction_checklist.md`

**Decision strings:**

```text
ADMIT_CANDIDATE_C_KEY_SECURITY_NOISE_PREFLIGHT
REJECT_CANDIDATE_C_RANK_BOUNDED_STATE_CAMPAIGN_EXHAUSTED
INCONCLUSIVE_CANDIDATE_C_EVIDENCE_EXHAUSTED
```

- [ ] **Step 1: Write gate tests**

  Require source, equation, symbolic independence, phase, schedule, rank,
  compression, complete-cost, and Amdahl fields in one canonical summary.
  When Task 4 is skipped, complete-cost and Amdahl fields remain present with
  exact status `SKIPPED_NO_REGISTERED_OPERATOR` and no fabricated numeric
  values.
  A scoped mechanism failure selects REJECT. Missing evidence selects the
  explicit terminal INCONCLUSIVE decision. Neither may be changed
  independently of its mechanism fields or terminal Task 3C record.

- [ ] **Step 2: Write generator tests**

  Require:

  ```text
  summary.csv
  source_mapping.csv
  schedule_trace.csv
  operator_tensor.csv
  evaluator_sample_relations.csv
  conversion_material.csv
  registered_object_hash.csv
  terminal_record.csv
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
  projection. Select REJECT only for a fully evaluated scoped mechanism
  failure. Select INCONCLUSIVE only for a hash-bound terminal evidence-
  exhaustion record. Task 4 fields are numeric on ADMIT/REJECT-after-cost and
  present with `SKIPPED_NO_REGISTERED_OPERATOR` on a skipped route.

- [ ] **Step 4: Write atomic closeout tests**

  Extend the research-state validator with terminal candidate status
  `INCONCLUSIVE` and goal status `RESEARCH_CAMPAIGN_INCONCLUSIVE`. This state
  is valid only when A and B are `REJECTED`, C is active and
  `INCONCLUSIVE`, paper gate is `BLOCKED`, and production permission is
  false.

  Test ADMIT, REJECT, and INCONCLUSIVE in temporary roots. On ADMIT, C
  advances only to `ADVERSARIAL_CHECKER_PASS`; production permission remains
  false. On REJECT, set:

  ```text
  C = REJECTED
  active_candidate = C
  goal_status = RESEARCH_CAMPAIGN_EXHAUSTED
  paper_gate = BLOCKED
  production_hot_path_permission = false
  ```

  On INCONCLUSIVE, set:

  ```text
  C = INCONCLUSIVE
  active_candidate = C
  goal_status = RESEARCH_CAMPAIGN_INCONCLUSIVE
  paper_gate = BLOCKED
  production_hot_path_permission = false
  ```

  Do not substitute `EXTERNAL_BLOCKED`, which remains reserved for
  unavailable external evidence.

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
- On INCONCLUSIVE: close this finite equation budget without claiming
  mechanism failure. Preserve the exact missing-evidence boundary and do not
  resume Candidate C or invent Candidate D without a separately approved
  research design.
