# Candidate B Factorized Mechanism Gate Implementation Plan

Status: `COMPLETED` with
`REJECT_CANDIDATE_B_EXACT_STANDARD_PVW_FACTORIZATION_ROUTE_TO_C`.

> **Execution:** Use subagent-driven development task by task. Every task
> requires tests before implementation, a focused review, and a clean
> research-suite run before commit.

**Goal:** Decide whether the complete current standard-PVW MAT_TRGSW selector
admits a closed Theta(r)-work factorized realization, record the decision, and
route the finite A/B/C campaign without changing SAB or MOSFHET C hot paths.

**Architecture:** Add a dependency-free coefficient-wise algebra model for
the exact current selector matrix, an adversarial rank/cost gate with positive
and negative controls, deterministic evidence generation, and an idempotent
closeout tool. Treat semantic phase correctness, distribution support, output
closure, and complete cost as separate gates.

**Tech stack:** Python 3 standard library, `unittest`, Markdown, CSV, JSON-valid
YAML, existing source and reproducibility artifacts as read-only anchors.

## Global Constraints

- Controlling design:
  `docs/superpowers/specs/2026-07-17-candidate-b-factorized-gate-design.md`.
- Primary metric remains complete-SAB `T_bootstrap/r`; this gate reports no
  speedup.
- No production or development dependency may be added.
- Do not modify any C/C++ source, header, `main.c`, or `Makefile`.
- `production_hot_path_permission` remains `false`.
- Candidate B consumes no kernel-layout or full-SAB-integration budget.
- Candidate B may be rejected from `EQUATIONS_DEFINED` if its exact complete
  representation fails.
- Generated evidence must be deterministic and idempotent.
- Run all research tests with:

```powershell
python -m unittest discover -s tests/research -p "test_*.py" -v
```

## Task 1: Anchor Candidate B Intake And Equations

**Create:**

- `paper_techgraphs/candidate_b_factorized_selector.yaml`
- `paper_techgraphs/candidate_b_factorized_selector_graph.md`
- `paper_techgraphs/candidate_b_factorized_selector_gaps.md`
- `theory_checks/candidate_b_factorized_standard_pvw_model.md`
- `tests/research/test_candidate_b_techgraph.py`

**Steps:**

- [x] Write tests that require source anchors for `PVW_TMLWE`,
  `pvmtmlwe_sample`, `pvmtmlwe_phase`, `mat_trgsw_monomial_sample`, the dense
  external product, and `sab_pvw_CMUX`.
- [x] Require the graph to distinguish semantic star-cycle support from the
  complete encrypted selector distribution.
- [x] Require the equations document to contain the general-`k` matrix, the
  target `k=1` reduction, phase identity, error-rank boundary, and complete
  work-count policy.
- [x] Implement the artifacts.
- [x] Run the focused tests.
- [x] Transition an in-memory Candidate B state through
  `TECHGRAPH_ANCHORED` and `EQUATIONS_DEFINED`; do not mutate repository state
  until the closeout gate validates all evidence.

**Gate:** All source tokens and all required equation obligations are present.

## Task 2: Implement The Exact Selector And Factor-Rank Model

**Create:**

- `research/mat_sab/factorized_selector_model.py`
- `tests/research/test_factorized_selector_model.py`

**Interfaces:**

```text
standard_selector(secret, mu, masks, errors, modulus, gadget=1)
external_product(digits, selector, modulus)
phase(vector, secret, modulus)
expected_phase(digits, errors, secret, mu, modulus, gadget=1)
constant_error_homomorphic_image(polynomial_matrix)
full_rank_homomorphic_image(r)
low_rank_homomorphic_image_control(r, q)
homomorphic_image_rank(image)
homomorphic_image_fits_inner_dimension(image, q)
factor_cost(r, q)
```

**Steps:**

- [x] Write tests for shape validation and ragged-input rejection.
- [x] Write phase-identity tests for `r=2,4,6`, `mu=0,1`, and deterministic
  nonzero masks, digits, and errors.
- [x] Add a mutation test that changes one body error and requires the expected
  phase to change.
- [x] Write a full-rank positive control for the multiplicative map
  `phi(f)=f(1) mod 2`, with image rank exactly `r`.
- [x] Write low-rank image controls with rank exactly `q` for every
  `q<r`.
- [x] Require the image-rank gate to reject each full-rank witness for `q<r`
  and admit each constructed rank-`q` image control.
- [x] Require one hard-coded hand-derived selector/output/phase oracle.
- [x] Require the cost model to count polynomial components, not only vector
  objects, and label dense two-sided factor counts as generic implementation
  counts rather than universal lower bounds.
- [x] Implement the minimum model that passes the tests.
- [x] Run focused and full research tests.

**Gate:** Algebra, rank, mutation, and cost controls all pass.

## Task 3: Build The Adversarial Candidate B Gate

**Create:**

- `scripts/run_candidate_b_factorized_gate.py`
- `tests/research/test_candidate_b_gate.py`
- `docs/candidate_b_factorized_mechanism_gate.md`
- `algorithm_variants/candidate_b_factorized_star_cycle.md`
- `experiments/candidate_b_factorized_gate_plan.md`
- `repro/candidate_b_factorized_gate/`

**Evidence files:**

```text
summary.csv
source_mapping.csv
literature_claims.csv
sampler_support.csv
phase_identity.csv
rank_controls.csv
factor_cost.csv
mechanism_matrix.csv
proof_gate.csv
input_manifest.csv
environment.csv
artifact_index.csv
reproduction_commands.md
```

**Steps:**

- [x] Write tests that recompute every decision field from source and model
  evidence.
- [x] Require missing source anchors or failed positive/negative controls to
  raise an inconclusive evidence error, never an admit/reject result.
- [x] Require coverage of `r=2,4,6`, `mu=0,1`, and every `q<r`.
- [x] Require B0 exact-standard factorization to fail when a supported
  full-rank homomorphic image cannot be represented with `q=O(1)`.
- [x] Require B1 noiseless-only factorization to fail the complete-cost gate
  when dense error work remains.
- [x] Record B2 as a changed-distribution route to C, not as standard-PVW
  admission.
- [x] Require B3/B4 to stay unregistered unless a concrete complete mechanism
  and cost accounting artifact exists, is hash-bound, and passes a
  mechanism-specific semantic checker registered in code.
- [x] Generate all human- and machine-readable artifacts.
- [x] Verify byte-identical output on two consecutive runs.

**Decision:** With current evidence, either

```text
ADMIT_CANDIDATE_B_KEY_DISTRIBUTION_PREFLIGHT
```

or

```text
REJECT_CANDIDATE_B_EXACT_STANDARD_PVW_FACTORIZATION_ROUTE_TO_C
```

No other terminal string is accepted.

## Task 4: Apply The Decision Atomically And Idempotently

**Create:**

- `scripts/apply_candidate_b_factorized_gate.py`
- `tests/research/test_candidate_b_closeout.py`

**Modify through the closeout tool only:**

- `research_state.yaml`
- `hypotheses/hypothesis_register.yaml`
- `repro/run_log.csv`
- `repro/artifact_manifest.md`
- `repro/reproduction_checklist.md`

**Steps:**

- [x] Write temporary-root tests for both admitted and rejected outcomes.
- [x] Require the repository pre-state to be Candidate B `INTAKE`, Candidate A
  `REJECTED`, Candidate C `QUEUED`, Goal `ACTIVE`, and permission `false`.
- [x] Recompute gate evidence before any mutation.
- [x] Validate source/equation prerequisites, then transition B in memory
  through `TECHGRAPH_ANCHORED` and `EQUATIONS_DEFINED`.
- [x] On rejection, set B `REJECTED`, C `INTAKE`, active candidate C, Goal
  `ACTIVE`, paper gate `BLOCKED`, and permission `false`.
- [x] On admission, set B `ADVERSARIAL_CHECKER_PASS` and leave C queued.
- [x] Reject malformed, duplicated, fabricated, stale, or path-escaping
  summaries before mutation.
- [x] Append bounded ledger blocks and one run-log row.
- [x] Verify a second closeout run changes no bytes.

**Gate:** State and ledgers agree exactly with recomputed evidence.

## Task 5: Final Verification And Freeze Record

**Steps:**

- [x] Run the Candidate B generator twice and compare checksums.
- [x] Run the Candidate B closeout twice and verify idempotence.
- [x] Run all research tests.
- [x] Run `python scripts/mat_sab_research_state.py validate`.
- [x] Verify no C/C++ source, header, `main.c`, or `Makefile` changed from
  Candidate A's terminal commit.
- [x] Verify `production_hot_path_permission` remains `false`.
- [x] Update the concise active Goal with B's disposition and Candidate C's
  exact next question if B is rejected.
- [x] Run a final branch review focused on overclaiming, state-machine
  consistency, deterministic artifacts, and test independence.

**Completion:** Candidate B has one reproducible disposition. If rejected,
Candidate C is the only active next candidate; no unbounded Stage A/B loop is
allowed.
