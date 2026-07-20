# Candidate D LUT-Late-Binding Admission Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use
> superpowers:subagent-driven-development (recommended) or
> superpowers:executing-plans to implement this plan task-by-task. Steps use
> checkbox (`- [ ]`) syntax for tracking.

**Goal:** Execute the finite D0-D3 research campaign that either admits a
source-anchored, exact, standard-assumption, noise-feasible, and
complete-cost-positive LUT-late-binding SAB operator to isolated encrypted
implementation, or records a scoped rejection/block and routes according to
the approved design.

**Architecture:** First migrate the research state controller without
rewriting historical A/B/C evidence, then freeze the scalar and exact-dense
PVW/MAT-SAB baselines. Audit the critical primary literature before building
an exact semilinear-operator checker over
`GF(257)[X]/(X^N+1)`. Only a closure that passes source, phase, mutation,
integer-grid, standard-RLWE/GGSW, covariance-aware noise, resource, and
complete Amdahl gates may set implementation permission. This plan creates no
encrypted Candidate D type and modifies no C hot path.

**Tech Stack:** Python 3.12 standard library, `unittest`, JSON-valid YAML,
CSV, Markdown, SHA-256, WSL/Linux, `curl`, `pdftotext`, and existing C source
and reproducibility artifacts as read-only anchors.

## Global Constraints

- Controlling design:
  `docs/superpowers/specs/2026-07-20-lut-late-binding-operator-sab-design.md`.
- Starting branch and commit:
  `codex/candidate-d-lut-late-binding` at `2dc374d`.
- This plan covers D0-D3 only. D4-D6 encrypted implementation requires a
  separate reviewed plan after `D3_ADMISSION_PASS`.
- The primary metric is exactly
  `T_complete_bootstrap / (r * N_active)`.
- Baselines are B0a repeated scalar SAB, B0b shared-output-key independent-mask
  repeated scalar control, B1 exact-dense PVW/MAT-SAB, and B2 local BatchBoot
  or a relevant same-backend composition.
- The first target is binary/include-zero `SET_2_3_2048`; `r=4` is primary,
  `r=2` is supporting, and `r=1` is a degeneration control.
- Generic include-zero `sub_a` contributes `h*N=39*2048=79872`
  additional selector events. It may be removed from the target cost only
  after the coefficient-one fast-path equation and key-generation condition
  are source-anchored and exactly verified.
- The exact checker uses `GF(257)[X]/(X^N+1)` for `N in {8,16}` and centered
  LUT coefficients in `[-128,128]`.
- Late binding is multiplication by a bounded public integer polynomial
  `F_Z`; Torus-by-Torus multiplication is forbidden.
- The ideal invariant is noiseless phase equality. Ciphertext bytes,
  distributions, and sampled errors are not expected to be equal.
- Candidate D requires `|Gamma|<=4`, permits one state-equation revision, and
  must stop after that revision fails.
- Candidate D may enter D4 only if the conservative complete `r=4`
  projection is at least `1.10x` over B1 and the absolute decoding/noise gate
  passes.
- Every cryptographic object must map to standard RLWE/Module-LWE, existing
  scalar GGSW, public automorphism, or standard key switching under the
  explicitly inherited circular-security scope.
- Do not use correlated selector errors, secret-dependent public sparsity,
  publicly removable encrypted-zero rows, or unsupported low-rank mask
  distributions.
- Do not modify `main.c`, `Makefile`, `include/*.h`, `src/*.c`, or
  `src/mosfhet/**` in this plan.
- Add no Python or production dependency. PDF text extraction uses the
  existing WSL `/usr/bin/pdftotext`.
- WSL timing is smoke evidence only. Existing native/high-stat artifacts are
  frozen, not reinterpreted as Candidate D measurements.
- Every generated artifact is ASCII, deterministic, and bound to source
  hashes. Full papers remain under a gitignored `references/` directory.
- A missing full text, source anchor, formula input, or noise parameter is
  `BLOCKED` or `INCONCLUSIVE`, never an assumed pass.
- A terminal result must be derived from gate fields. Editing only a decision
  string must fail verification.

## Campaign Routing

```text
D0 PASS -> D1
D1 PASS -> D2
D1 REJECT/BLOCK -> Task 9 closeout; do not run D2/D3
D2 PASS -> D3
D2 REJECT/BLOCK -> Task 9 closeout; do not run D3
D3 PASS -> Task 9 admission
D3 REJECT/BLOCK -> Task 9 closeout
```

`REJECT` means the registered mechanism is falsified and routes to Candidate
E. `BLOCKED` means required external or author-reviewed evidence is absent;
it leaves Candidate D active with production permission `false`.

## File Ownership Map

- `scripts/mat_sab_research_state.py`: validates and transitions both the
  frozen predecessor campaign and the current D/E campaign.
- `research/mat_sab/candidate_d_baseline.py`: hashes and validates immutable
  D0 baseline evidence.
- `research/mat_sab/candidate_d_literature.py`: validates full-text source
  manifests and computes the D1 novelty-overlap gate.
- `research/mat_sab/candidate_d_source_map.py`: parses the exact SAB source
  schedule and emits source-anchored operations and counts.
- `research/mat_sab/negacyclic_operator.py`: exact ring, automorphism, matrix,
  and semilinear-operator primitives.
- `research/mat_sab/candidate_d_operator_closure.py`: infers `Gamma`, checks
  basis-vector phase equality, replays the schedule, and runs mutations.
- `research/mat_sab/candidate_d_admission.py`: validates LUT scale, security
  object mapping, covariance/noise bounds, resources, and complete cost.
- `scripts/run_candidate_d_d*.py`: deterministic stage runners that write
  only their owned `repro/candidate_d_admission/` artifacts.
- `scripts/apply_candidate_d_admission.py`: verifies all artifacts, then
  atomically updates state and append-only ledgers.

---

### Task 1: Repair And Version The Research State Controller

**Files:**
- Create:
  `tests/research/fixtures/predecessor_research_state.json`
- Modify:
  `scripts/mat_sab_research_state.py`
- Modify:
  `scripts/build_mat_sab_selector_techgraph.py`
- Modify:
  `tests/research/test_research_state.py`
- Modify:
  `tests/research/test_selector_techgraph.py`
- Modify:
  `tests/research/test_candidate_a_closeout.py`
- Modify:
  `tests/research/test_candidate_b_closeout.py`
- Modify:
  `tests/research/test_candidate_c_closeout.py`
- Modify:
  `research_state.yaml`

**Interfaces:**
- Produces:

  ```python
  load_state(path: Path) -> dict[str, object]
  validate_state(state: Mapping[str, object]) -> None
  transition_candidate(
      state: Mapping[str, object],
      candidate: str,
      to_status: str,
      decision: str,
  ) -> dict[str, object]
  activate_candidate_d_plan(
      state: Mapping[str, object],
      decision: str,
  ) -> dict[str, object]
  ```

- Preserves the predecessor contract validator for historical A/B/C fixtures.
- Makes the current D/E contract the repository-default validator.

- [ ] **Step 1: Freeze the predecessor state fixture**

  Inspect the exact pre-Candidate-D state from commit `ba7b2b8`:

  ```text
  git show ba7b2b8:research_state.yaml
  ```

  Add that exact output to
  `tests/research/fixtures/predecessor_research_state.json` with
  `apply_patch`; do not mutate the current state file.

  Verify:

  ```text
  python -m json.tool \
    tests/research/fixtures/predecessor_research_state.json > NUL
  ```

  Expected: exit `0`; A/B/C are present and Candidate C is terminal.

- [ ] **Step 2: Write current-contract state tests**

  Add tests with these exact assertions:

  ```python
  def test_current_repository_state_uses_candidate_d_contract(self):
      state = load_state(ROOT / "research_state.yaml")
      self.assertEqual(
          state["contract"],
          "docs/superpowers/specs/"
          "2026-07-20-lut-late-binding-operator-sab-design.md",
      )
      self.assertEqual(
          state["primary_metric"],
          "complete_sab_T_bootstrap_div_rN_active",
      )
      self.assertEqual(state["candidate_order"], ["A", "B", "C", "D", "E"])
      self.assertEqual(state["active_candidate"], "D")
      self.assertFalse(state["production_hot_path_permission"])

  def test_candidate_d_cannot_skip_d0_d3(self):
      state = candidate_d_state("PLAN_APPROVED")
      with self.assertRaisesRegex(ValueError, "invalid transition"):
          transition_candidate(
              state, "D", "D3_ADMISSION_PASS", "SKIP_D0_D2"
          )

  def test_candidate_d_rejection_routes_only_to_e(self):
      state = candidate_d_state("D2_OPERATOR_CLOSURE_PASS")
      changed = transition_candidate(
          state, "D", "REJECTED", "REJECT_D_ROUTE_E"
      )
      self.assertEqual(changed["active_candidate"], "E")
      self.assertEqual(
          changed["candidates"]["E"]["status"],
          "SECURITY_NOVELTY_PREFLIGHT",
      )
      self.assertFalse(changed["production_hot_path_permission"])
  ```

  Historical A/B/C closeout tests must load
  `predecessor_research_state.json`, not mutate the current D state into an
  impossible predecessor state.

- [ ] **Step 3: Run the state tests and verify the known RED**

  Run:

  ```text
  python -m unittest tests.research.test_research_state -v
  ```

  Expected before implementation: failure headed by `ValueError: contract
  changed`. The pre-plan observation was 23 tests with 74 errors; do not use
  that count as a post-change expectation.

- [ ] **Step 4: Implement dual-contract validation**

  Refactor the state controller around these constants:

  ```python
  PREDECESSOR_CONTRACT = (
      "docs/superpowers/specs/"
      "2026-07-16-ccs-usenix-mat-sab-research-contract-design.md"
  )
  CURRENT_CONTRACT = (
      "docs/superpowers/specs/"
      "2026-07-20-lut-late-binding-operator-sab-design.md"
  )
  CURRENT_ORDER = ("A", "B", "C", "D", "E")
  CURRENT_PRIMARY_METRIC = "complete_sab_T_bootstrap_div_rN_active"
  D_PIPELINE = (
      "PLAN_APPROVED",
      "D0_BASELINE_FROZEN",
      "D1_NOVELTY_AUDIT_PASS",
      "D2_OPERATOR_CLOSURE_PASS",
      "D3_ADMISSION_PASS",
      "D4_ISOLATED_OPERATOR_PASS",
      "D5_FULL_SAB_PASS",
      "D6_OPTIMIZATION_COMPLETE",
      "D7_EVIDENCE_MATRIX_PASS",
      "D8_PAPER_GATE_PASS",
  )
  E_PIPELINE = (
      "SECURITY_NOVELTY_PREFLIGHT",
      "EQUATIONS_DEFINED",
      "ADVERSARIAL_CHECKER_PASS",
      "KEY_SECURITY_NOISE_PREFLIGHT_PASS",
      "AMDAHL_PROJECTION_PASS",
      "ISOLATED_KERNEL_PASS",
      "FULL_SAB_PASS",
      "PAPER_GATE_PASS",
  )
  CURRENT_BASELINES = {
      "B0a": "repeated_scalar_SAB",
      "B0b": (
          "shared_output_key_independent_mask_"
          "repeated_scalar_control_required"
      ),
      "B1": "exact_dense_PVW_MAT_SAB_current_head",
      "B2": "BatchBoot_same_backend_local_reproduction_required",
  }
  ```

  `validate_state` dispatches by exact contract path. Unknown contracts fail.
  The current validator requires A/B/C `REJECTED`, D active, E reserved until
  a D rejection, Candidate C revision count `1`, D/E budget fields in
  `[0,1]`, and permission only at or after `D3_ADMISSION_PASS`.

  `activate_candidate_d_plan` accepts only:

  ```text
  goal_status = CANDIDATE_D_DESIGN_APPROVED_PLAN_BLOCKED
  D.status    = DESIGN_APPROVED_PENDING_WRITTEN_SPEC_REVIEW
  ```

  and returns:

  ```text
  goal_status = ACTIVE
  D.status    = PLAN_APPROVED
  last_decision =
    CANDIDATE_D_WRITTEN_SPEC_AND_IMPLEMENTATION_PLAN_APPROVED
  ```

- [ ] **Step 5: Extend the selector techgraph state view**

  Render all five candidates from `candidate_order`; do not hard-code three
  rows. The current state text must include:

  ```text
  Candidate A: REJECTED
  Candidate B: REJECTED
  Candidate C: REJECTED
  Candidate D: PLAN_APPROVED (active)
  Candidate E: RESERVED_FALLBACK_NOT_STARTED
  ```

  Keep the predecessor graph path working from its fixture.

- [ ] **Step 6: Activate the reviewed plan state**

  Use `activate_candidate_d_plan`, then `write_state`; do not hand-edit only
  the status string. Expected repository values:

  ```text
  goal_status = ACTIVE
  D.status = PLAN_APPROVED
  production_hot_path_permission = false
  equation_revisions_used = 0
  kernel_layouts_used = 0
  full_sab_integrations_used = 0
  ```

- [ ] **Step 7: Run state and historical regression tests**

  Run:

  ```text
  python -m unittest \
    tests.research.test_research_state \
    tests.research.test_selector_techgraph \
    tests.research.test_candidate_a_closeout \
    tests.research.test_candidate_b_closeout \
    tests.research.test_candidate_c_closeout -v
  ```

  Expected: all pass; no historical artifact is regenerated.

- [ ] **Step 8: Commit**

  ```text
  git add scripts/mat_sab_research_state.py \
    scripts/build_mat_sab_selector_techgraph.py \
    tests/research/fixtures/predecessor_research_state.json \
    tests/research/test_research_state.py \
    tests/research/test_selector_techgraph.py \
    tests/research/test_candidate_a_closeout.py \
    tests/research/test_candidate_b_closeout.py \
    tests/research/test_candidate_c_closeout.py \
    research_state.yaml
  git commit -m "research: migrate state controller to Candidate D"
  ```

### Task 2: Freeze D0 Baselines And Reproduction Commands

**Files:**
- Create:
  `research/mat_sab/candidate_d_baseline.py`
- Create:
  `tests/research/test_candidate_d_baseline.py`
- Create:
  `scripts/run_candidate_d_d0_freeze.py`
- Create:
  `docs/candidate_d_d0_baseline.md`
- Create:
  `repro/candidate_d_admission/baseline_manifest.csv`
- Create:
  `repro/candidate_d_admission/environment.csv`
- Create:
  `repro/candidate_d_admission/reproduction_commands.md`

**Interfaces:**
- Produces:

  ```python
  BaselineAnchor(path: str, sha256: str, role: str)
  sha256_file(path: Path) -> str
  validate_baseline_anchors(root: Path) -> tuple[BaselineAnchor, ...]
  parse_target_parameters(root: Path) -> dict[str, int | float]
  validate_terminal_predecessors(root: Path) -> None
  build_d0_artifacts(root: Path, out: Path) -> str
  ```

- The D0 decision is exactly `PASS_D0_CANDIDATE_D_BASELINES_FROZEN`.

- [ ] **Step 1: Write immutable hash tests**

  Register these exact starting hashes:

  ```python
  EXPECTED_ANCHORS = {
      "repro/candidate_a_star_cycle_gate/summary.csv":
          "c7a003c39d8e56f1cc4ca0845cffe7e68f81cd41a8979d661f8a3df525a96d09",
      "repro/candidate_b_factorized_gate/summary.csv":
          "c758785b0ce7d4d6ef56bb44639b381780ef0d529dc17c8f2544ec67ce3b7a91",
      "repro/candidate_c_rank_bounded_gate/terminal_record.csv":
          "7c7e60bd9a201d4ed943d411dbd40be76ece8f4942822ca31ed278d53c8863d7",
      "repro/stage331_current_head_highstat_refresh/summary.csv":
          "23d3c2611329f189a88f6bdc645e9ed1ac237d19159e79401d2fc11b9c03ad56",
      "repro/stage345_binary_matrix_synthesis/binary_matrix.csv":
          "97014b127ad5061dc10fbd3cb3ab53fb06d9ebc69b436011760778425208ea9b",
      "src/sab_pvw.c":
          "6aaabf61f010e0154b826855286137afc39de9b2520ee09e2ca43d5accf5e2ac",
      "src/mosfhet/src/mattrgsw.c":
          "5da51089a748f7f1f54b56f81c2948ced14f0be4dd431bcffb2339af97c527fa",
      "main.c":
          "d402980a203aacbaf6b281a9f7245cf14b72c2c80468e5a05050f35373eb11f8",
  }
  ```

  Test that deleting, changing, or replacing any one file fails the D0 gate.

- [ ] **Step 2: Write baseline semantic tests**

  Require the parsers to recover:

  ```text
  in_N=2048
  out_N=2048
  out_k=1
  l=1
  bg_bit=23
  prec=3
  h=39
  r_prec=7
  sigma_out=2^-50
  H=(h+1)*r_prec*in_N=573440
  B1 r=4 T_total=24468333.700 us
  B1 r=4 T/r=6117083.425 us
  B0a repeated scalar T/r=10690503.200 us
  B1 T/(r*N_active)=2986.857141113 us for N_active=2048
  B0a T/(r*N_active)=5219.972265625 us for N_active=2048
  B1/B0a speedup=1.747647
  B1 pair failures=0/10
  ```

  B0b and B2 must be recorded as `REQUIRED_NOT_YET_LOCAL`, not silently
  treated as measured.

- [ ] **Step 3: Verify RED**

  Run:

  ```text
  python -m unittest tests.research.test_candidate_d_baseline -v
  ```

  Expected: import failure because `candidate_d_baseline.py` does not exist.

- [ ] **Step 4: Implement the deterministic D0 builder**

  Use `hashlib.sha256`, strict CSV parsing, and source token parsing. The
  builder must reject:

  ```text
  changed predecessor decisions
  changed B1 numeric row
  missing target parameter
  a nonzero historical pair-failure count
  a manifest path outside repository root
  duplicate artifact rows
  ```

  Write each CSV with a fixed field order and `lineterminator="\n"`.

- [ ] **Step 5: Record executable smoke commands**

  `reproduction_commands.md` contains these commands without claiming formal
  performance:

  ```text
  python -m unittest discover -s tests/research -v

  bash scripts/run_stage33_current_smoke.sh

  make FFT_LIB=spqlios_avx512 A_PRNG=none ENABLE_VAES=false \
    KEY=BINARY PARAM=SET_2_3_2048 \
    MAT_TRGSW_AVX512_SMALLR_SPECIALIZED=true \
    MAT_TRGSW_AVX512_SUB_DECOMP=true \
    MAT_TRGSW_SUB_DECOMP_DFT_DIRECT=true \
    SAB_PVW_BACKEND_FROM_DFT_ADD=true \
    SAB_PVW_SUB_DECOMP_FUSION=true \
    SAB_PVW_DUAL_SUB_CMUX=true \
    SAB_PVW_SUBA_INCLUDE_ZERO_COEFF_ONE_FAST=true \
    SAB_PVW_TARGET_TEST=true -j$(nproc)
  ./main
  ```

  Expected target smoke token:

  ```text
  SAB_PVW target full bootstrap binary lane equivalence ... Pass
  ```

  A failure to execute WSL is `ENVIRONMENT_BLOCKED`; it does not rewrite
  frozen high-stat numbers.

- [ ] **Step 6: Run D0 and transition state**

  Run:

  ```text
  python scripts/run_candidate_d_d0_freeze.py
  python scripts/mat_sab_research_state.py transition \
    D D0_BASELINE_FROZEN \
    --decision PASS_D0_CANDIDATE_D_BASELINES_FROZEN
  ```

  Expected: deterministic artifacts and D status `D0_BASELINE_FROZEN`.

- [ ] **Step 7: Run focused and full research tests**

  ```text
  python -m unittest tests.research.test_candidate_d_baseline -v
  python -m unittest discover -s tests/research -v
  ```

  Expected: all pass.

- [ ] **Step 8: Commit**

  ```text
  git add research/mat_sab/candidate_d_baseline.py \
    tests/research/test_candidate_d_baseline.py \
    scripts/run_candidate_d_d0_freeze.py \
    docs/candidate_d_d0_baseline.md \
    repro/candidate_d_admission/baseline_manifest.csv \
    repro/candidate_d_admission/environment.csv \
    repro/candidate_d_admission/reproduction_commands.md \
    research_state.yaml
  git commit -m "research: freeze Candidate D admission baselines"
  ```

### Task 3: Execute The D1 Full-Text Novelty Kill Gate

**Files:**
- Create:
  `references/candidate_d_fulltext/.gitignore`
- Create:
  `literature/candidate_d_source_registry.json`
- Create:
  `research/mat_sab/candidate_d_literature.py`
- Create:
  `tests/research/test_candidate_d_literature.py`
- Create:
  `scripts/fetch_candidate_d_primary_sources.sh`
- Create:
  `scripts/run_candidate_d_d1_literature.py`
- Create:
  `docs/candidate_d_d1_novelty_audit.md`
- Create:
  `repro/candidate_d_admission/literature_sources.csv`
- Create:
  `repro/candidate_d_admission/claim_overlap.csv`
- Create:
  `repro/candidate_d_admission/novelty_gate.csv`

**Interfaces:**
- Produces:

  ```python
  SourceRecord
  FullTextReview
  ClaimComparison
  load_source_registry(path: Path) -> tuple[SourceRecord, ...]
  verify_fulltext(record: SourceRecord, root: Path) -> FullTextReview
  evaluate_candidate_d_novelty(
      reviews: tuple[FullTextReview, ...],
  ) -> tuple[str, tuple[ClaimComparison, ...]]
  ```

- D1 decisions:

  ```text
  PASS_D1_DISTINCT_SAB_OPERATOR_CLAIM_REMAINS_TESTABLE
  REJECT_D1_CANDIDATE_D_SUBSUMED_BY_PRIOR_WORK
  BLOCK_D1_REQUIRED_FULLTEXT_OR_REVIEW_MISSING
  ```

- [ ] **Step 1: Register real primary sources**

  The JSON registry contains exactly these required IDs and official source
  or full-text URLs:

  | ID | Official full text |
  |---|---|
  | `FAB_2025_686` | `https://eprint.iacr.org/2025/686.pdf` |
  | `SHARING_MASK_2025_2112` | `https://eprint.iacr.org/2025/2112.pdf` |
  | `BATCHBOOT_SEC26` | `https://www.usenix.org/system/files/conference/usenixsecurity26/sec26_prepub_li-zhihao.pdf` |
  | `FDFB2_2024_1376` | `https://eprint.iacr.org/2024/1376.pdf` |
  | `MULTIVALUE_2018_622` | `https://eprint.iacr.org/2018/622.pdf` |
  | `MOSFHET_2022_515` | `https://eprint.iacr.org/2022/515.pdf` |
  | `NTRU_AMORT_2026_068` | `https://eprint.iacr.org/2026/068.pdf` |
  | `BATCH_BOOT_I` | `https://doi.org/10.1007/978-3-031-30620-4_11` |
  | `BATCH_BOOT_II` | `https://doi.org/10.1007/978-3-031-30620-4_12` |

  Each record has `id`, `title`, `authors`, `year`, `official_url`,
  `fulltext_url`, `critical_claims`, and `review_status`. The registry may not
  contain `2024/498`, which is unrelated to LUT late binding.

- [ ] **Step 2: Write source and mutation tests**

  Require:

  ```python
  def test_fdfb2_is_a_mandatory_novelty_kill_gate(self):
      records = load_source_registry(REGISTRY)
      fdfb = next(row for row in records if row.id == "FDFB2_2024_1376")
      self.assertIn("arbitrary number of functions", fdfb.critical_claims)

  def test_missing_batchboot_fulltext_blocks_d1(self):
      reviews = complete_fixture_reviews()
      reviews["BATCHBOOT_SEC26"] = reviews["BATCHBOOT_SEC26"].missing()
      decision, _ = evaluate_candidate_d_novelty(tuple(reviews.values()))
      self.assertEqual(
          decision, "BLOCK_D1_REQUIRED_FULLTEXT_OR_REVIEW_MISSING"
      )

  def test_subsumed_operator_claim_rejects_d(self):
      reviews = complete_fixture_reviews()
      reviews["FDFB2_2024_1376"] = reviews["FDFB2_2024_1376"].with_overlap(
          same_operator=True,
          same_complexity=True,
          distinct_sab_theorem=False,
      )
      decision, _ = evaluate_candidate_d_novelty(tuple(reviews.values()))
      self.assertEqual(
          decision, "REJECT_D1_CANDIDATE_D_SUBSUMED_BY_PRIOR_WORK"
      )
  ```

  A changed source title, URL, SHA-256, page range, or claim classification
  must invalidate the review.

- [ ] **Step 3: Verify RED**

  ```text
  python -m unittest tests.research.test_candidate_d_literature -v
  ```

  Expected: import failure.

- [ ] **Step 4: Fetch and hash full texts outside git**

  The shell script downloads to
  `references/candidate_d_fulltext/<source-id>.pdf`, verifies that each file
  begins with `%PDF`, records SHA-256, and runs:

  ```text
  pdftotext -layout input.pdf output.txt
  ```

  `.gitignore` contains:

  ```text
  *.pdf
  *.txt
  source_hashes.csv
  ```

  Failed downloads remain explicit in `literature_sources.csv`; do not store
  an HTML challenge as a PDF.

- [ ] **Step 5: Build claim-level review records**

  Record page/section anchors and paraphrases, not long copied passages. The
  comparison must answer:

  ```text
  Does FDFB^2 already expose the same late-bound operator?
  Does it cover arbitrary functions at constant additional cost?
  Is Candidate D only an SAB specialization of that construction?
  Does Sharing the Mask already cover the same ciphertext semantics?
  Does BatchBoot already remove the same CMUX/FFT cost?
  Can Candidate D compose with BatchBoot rather than compete with it?
  What theorem, asymptotic count, or measured endpoint remains distinct?
  What security level and correctness/failure target does 2025/686 use for
  the target parameter row?
  ```

  A `PASS` requires a concrete distinct claim:

  ```text
  SAB-specific bounded semilinear operator closure
  plus a different complete complexity/resource result
  plus a falsifiable full-SAB implementation endpoint.
  ```

- [ ] **Step 6: Run D1 and enforce routing**

  ```text
  python scripts/run_candidate_d_d1_literature.py
  ```

  On `PASS`, transition:

  ```text
  python scripts/mat_sab_research_state.py transition \
    D D1_NOVELTY_AUDIT_PASS \
    --decision PASS_D1_DISTINCT_SAB_OPERATOR_CLAIM_REMAINS_TESTABLE
  ```

  On `REJECT` or `BLOCK`, skip Tasks 4-8 and execute Task 9.

- [ ] **Step 7: Verify focused tests and artifact determinism**

  Run the D1 script twice and compare all tracked D1 artifact hashes.
  Expected: identical output for identical full-text hashes and reviews.

- [ ] **Step 8: Commit**

  ```text
  git add references/candidate_d_fulltext/.gitignore \
    literature/candidate_d_source_registry.json \
    research/mat_sab/candidate_d_literature.py \
    tests/research/test_candidate_d_literature.py \
    scripts/fetch_candidate_d_primary_sources.sh \
    scripts/run_candidate_d_d1_literature.py \
    docs/candidate_d_d1_novelty_audit.md \
    repro/candidate_d_admission/literature_sources.csv \
    repro/candidate_d_admission/claim_overlap.csv \
    repro/candidate_d_admission/novelty_gate.csv \
    research_state.yaml
  git commit -m "research: audit Candidate D novelty boundary"
  ```

### Task 4: Anchor The Candidate D Operator And Exact SAB Schedule

**Files:**
- Create:
  `research/mat_sab/candidate_d_source_map.py`
- Create:
  `tests/research/test_candidate_d_source_map.py`
- Create:
  `paper_techgraphs/candidate_d_lut_late_binding.yaml`
- Create:
  `paper_techgraphs/candidate_d_lut_late_binding_graph.md`
- Create:
  `paper_techgraphs/candidate_d_lut_late_binding_gaps.md`

**Interfaces:**
- Produces:

  ```python
  SourceAnchor
  TargetSchedule
  parse_target_schedule(root: Path) -> TargetSchedule
  validate_source_anchors(root: Path) -> tuple[SourceAnchor, ...]
  operator_event_stream(
      in_n: int, h: int, r_prec: int
  ) -> tuple[dict[str, int | str], ...]
  ```

- `TargetSchedule` exposes:

  ```text
  in_N, out_N, out_k, l, bg_bit, prec, h, r_prec
  monomial_calls, selector_events, ncmux_events, sub_a_calls
  include_zero_selector_events, include_zero_fast_equation_status
  ```

- [ ] **Step 1: Write exact source-anchor tests**

  Require these source tokens:

  ```text
  src/sparse_amortized_bootstrap.c: void CMUX(
  src/sparse_amortized_bootstrap.c: void NCMUX(
  src/sparse_amortized_bootstrap.c: void RGSW_monomial_mul(
  src/sparse_amortized_bootstrap.c: void sparse_mul(
  src/sparse_amortized_bootstrap.c: void setup_tv_xb(
  src/sab_pvw.c: void sab_pvw_CMUX(
  src/sab_pvw.c: void sab_pvw_NCMUX(
  src/sab_pvw.c: static uint64_t sab_pvw_RGSW_monomial_mul_state(
  src/sab_pvw.c: void sab_pvw_sparse_mul_binary(
  src/sab_pvw.c: void sab_pvw_setup_tv_xb(
  src/mosfhet/src/pvwtmlwe.c: void pvmtmlwe_mul_by_xai(
  src/mosfhet/src/mattrgsw.c: void mat_trgsw_mul_pvmtmlwe_DFT(
  main.c: static SAB_PVW_Target_Params sab_pvw_target_params(void)
  ```

  Tests fail if an anchor is present only in a comment or unrelated
  prototype.

- [ ] **Step 2: Write schedule-count tests**

  Derive, rather than hard-code alone:

  ```text
  monomial_calls = h + 1 = 40
  updates_per_monomial = r_prec * in_N = 7 * 2048 = 14336
  selector_events = 40 * 14336 = 573440
  ncmux_per_monomial = 2^r_prec - 1 = 127
  ncmux_events = 40 * 127 = 5080
  sub_a_calls = h = 39
  generic include-zero selector events = h*in_N = 79872
  ```

  Add a mutation test changing one loop bound from `<` to `<=`; the parser
  must fail rather than emit the old counts.

  Parse the generic `sab_pvw_sub_a_include_zero` branch and the
  `SAB_PVW_SUBA_INCLUDE_ZERO_COEFF_ONE_FAST` branch separately. A build flag
  alone cannot prove the fast branch: the source graph must link it to the
  selector/key-generation equation that makes the selector coefficient one.

- [ ] **Step 3: Verify RED**

  ```text
  python -m unittest tests.research.test_candidate_d_source_map -v
  ```

  Expected: import failure.

- [ ] **Step 4: Implement the strict source parser**

  Parse one exact definition for each symbol and one exact target initializer.
  Emit an event stream with:

  ```text
  monomial_call
  bit
  power
  accumulator_index
  kind = CMUX or NCMUX
  selector_family
  next_consumer
  ```

  Reject ambiguous duplicate definitions, missing binary branches, and target
  parameter drift.

- [ ] **Step 5: Define the operator dataflow**

  The graph fixes the intended normal form:

  ```text
  U(F_Z) = sum_(gamma in Gamma) u_gamma * gamma(F_Z)
  Gamma_0 = {id, tau_minus_one}
  tau_minus_one(X) = X^(-1) in R
  ```

  Record setup, rotation, CMUX, NCMUX, butterfly, `sub_a`, final binding,
  extraction, and key-switch edges. Mark security, noise, complete cost,
  implementation, and paper claims `BLOCKED`.

- [ ] **Step 6: Run tests and commit**

  ```text
  python -m unittest tests.research.test_candidate_d_source_map -v
  git add research/mat_sab/candidate_d_source_map.py \
    tests/research/test_candidate_d_source_map.py \
    paper_techgraphs/candidate_d_lut_late_binding.yaml \
    paper_techgraphs/candidate_d_lut_late_binding_graph.md \
    paper_techgraphs/candidate_d_lut_late_binding_gaps.md
  git commit -m "research: anchor Candidate D operator schedule"
  ```

### Task 5: Implement Exact Negacyclic And Semilinear Operator Algebra

**Files:**
- Create:
  `research/mat_sab/negacyclic_operator.py`
- Create:
  `tests/research/test_negacyclic_operator.py`

**Interfaces:**
- Produces:

  ```python
  Polynomial = tuple[int, ...]
  Matrix = tuple[tuple[int, ...], ...]

  NegacyclicRing(n: int, modulus: int)
  NegacyclicRing.add(lhs, rhs) -> Polynomial
  NegacyclicRing.sub(lhs, rhs) -> Polynomial
  NegacyclicRing.mul(lhs, rhs) -> Polynomial
  NegacyclicRing.monomial(exponent: int) -> Polynomial
  NegacyclicRing.automorphism(poly, exponent: int) -> Polynomial
  NegacyclicRing.multiplication_matrix(poly) -> Matrix
  NegacyclicRing.automorphism_matrix(exponent: int) -> Matrix

  SemilinearOperator(ring, channels: Mapping[int, Polynomial])
  SemilinearOperator.apply(poly) -> Polynomial
  SemilinearOperator.matrix() -> Matrix
  SemilinearOperator.add(other) -> SemilinearOperator
  SemilinearOperator.sub(other) -> SemilinearOperator
  SemilinearOperator.rotate_output(exponent) -> SemilinearOperator
  SemilinearOperator.automorphism_output(exponent) -> SemilinearOperator
  SemilinearOperator.select(other, mu: int) -> SemilinearOperator

  fit_semilinear_operator(
      matrix: Matrix,
      ring: NegacyclicRing,
      automorphism_exponents: tuple[int, ...],
  ) -> SemilinearFit
  ```

- [ ] **Step 1: Write ring validation and wrap tests**

  Test `N=8,16`, modulus `257`, every basis monomial, and:

  ```python
  ring.mul(ring.monomial(7), ring.monomial(1)) == (256, 0, ..., 0)
  ring.monomial(8) == (256, 0, ..., 0)
  ring.monomial(16) == (1, 0, ..., 0)  # N=8
  ```

  Reject non-power-of-two `N`, composite modulus, ragged vectors, and even
  automorphism exponents.

- [ ] **Step 2: Write automorphism and normal-form tests**

  For every basis `F=X^j`:

  ```text
  tau(tau(F)) = F
  tau(u*F) = tau(u)*tau(F)
  tau(u*F + v*tau(F)) = tau(v)*F + tau(u)*tau(F)
  ```

  The last identity requires the channel swap. A no-swap mutation must fail.

- [ ] **Step 3: Write exact fitting tests**

  Build matrices for:

  ```text
  M_u
  M_u + M_v Tau
  M_u + M_v Tau + M_w Gamma_3
  ```

  Use `research.mat_sab.finite_linear.solve_affine`; recover exact
  coefficients from all `N^2` equations. A matrix outside the registered
  span returns `consistent=False`.

- [ ] **Step 4: Verify RED**

  ```text
  python -m unittest tests.research.test_negacyclic_operator -v
  ```

  Expected: import failure.

- [ ] **Step 5: Implement exact arithmetic**

  Negacyclic multiplication is:

  ```python
  out = [0] * n
  for i, lhs_value in enumerate(lhs):
      for j, rhs_value in enumerate(rhs):
          degree = i + j
          sign = 1
          if degree >= n:
              degree -= n
              sign = -1
          out[degree] = (
              out[degree] + sign * lhs_value * rhs_value
          ) % modulus
  ```

  Automorphisms reduce exponents modulo `2N`; coefficients crossing degree
  `N` change sign. Canonical channels omit all-zero coefficient
  polynomials and sort by exponent.

- [ ] **Step 6: Run tests and commit**

  ```text
  python -m unittest tests.research.test_finite_linear \
    tests.research.test_negacyclic_operator -v
  git add research/mat_sab/negacyclic_operator.py \
    tests/research/test_negacyclic_operator.py
  git commit -m "research: add exact semilinear operator algebra"
  ```

### Task 6: Run The D2 Closure, Equivalence, And Negative-Control Gate

**Files:**
- Create:
  `research/mat_sab/candidate_d_operator_closure.py`
- Create:
  `tests/research/test_candidate_d_operator_closure.py`
- Create:
  `scripts/run_candidate_d_d2_closure.py`
- Create:
  `theory_checks/candidate_d_operator_closure.md`
- Create:
  `repro/candidate_d_admission/d2_summary.csv`
- Create:
  `repro/candidate_d_admission/closure_basis.csv`
- Create:
  `repro/candidate_d_admission/phase_equivalence.csv`
- Create:
  `repro/candidate_d_admission/negative_controls.csv`
- Create:
  `repro/candidate_d_admission/schedule_trace.csv`

**Interfaces:**
- Consumes: Tasks 4 and 5.
- Produces:

  ```python
  OperatorAccumulator
  ClosureResult
  setup_operator_accumulator(ring, b) -> OperatorAccumulator
  scalar_setup(ring, b, lut) -> tuple[Polynomial, ...]
  operator_cmux(lhs, rhs, mu) -> OperatorAccumulator
  operator_ncmux(lhs, rhs, mu) -> OperatorAccumulator
  operator_rgsw_monomial(state, selector_bits) -> OperatorAccumulator
  operator_sub_a(state, rotations) -> OperatorAccumulator
  operator_sub_a_include_zero(
      state, rotations, coefficient_selectors
  ) -> OperatorAccumulator
  bind_operator(state, lut) -> tuple[Polynomial, ...]
  replay_small_schedule(case: ScheduleCase) -> ClosureResult
  infer_gamma(result, max_channels=4) -> tuple[int, ...]
  derive_d2_decision(result) -> str
  ```

- D2 decisions:

  ```text
  PASS_D2_OPERATOR_CLOSURE_G_LE_4
  REJECT_D2_PHASE_EQUIVALENCE
  REJECT_D2_CLOSURE_GT_4
  REJECT_D2_NEGATIVE_CONTROL
  REJECT_D2_REVISION_EXHAUSTED
  BLOCK_D2_SOURCE_OR_EXACT_CHECKER_INCOMPLETE
  ```

- [ ] **Step 1: Write local CMUX/NCMUX basis tests**

  For `N=8,16`, every basis LUT `F=X^j`, every rotation offset, and
  `mu in {0,1}`, require:

  ```text
  bind(CMUX(U0,U1,mu), F)
    = CMUX(bind(U0,F), bind(U1,F), mu)

  bind(NCMUX(U0,U1,mu), F)
    = CMUX(bind(U0,F), tau(bind(U1,F)), mu)
  ```

  Equality is exact polynomial equality in `GF(257)`, representing noiseless
  phase equality.

- [ ] **Step 2: Write full butterfly and sparse-schedule tests**

  Cases:

  ```text
  N=8,  r_prec=3, h=2
  N=16, r_prec=4, h=2
  ```

  Selector patterns for every RGSW call:

  ```text
  all zero
  all one
  alternating 0/1
  one-hot at each bit
  deterministic source-shaped mixed pattern
  ```

  Check every intermediate accumulator index and every LUT basis vector after
  setup, each CMUX/NCMUX, each monomial call, each `sub_a`, and final binding.

  Repeat the small schedule for:

  ```text
  binary sub_a: X^a * p
  generic include-zero sub_a: p + mu_c * (X^a-1) * p
  coefficient-one fast sub_a: X^a * p, but only with mu_c=1 proof input
  ```

  Exhaust `mu_c in {0,1}` in the generic branch. The fast branch must reject a
  `mu_c=0` fixture.

- [ ] **Step 3: Write mandatory negative controls**

  The checker itself passes only if all mutations are detected:

  ```text
  remove tau_minus_one channel
  omit id/tau swap after tau_minus_one
  use positive rather than negative negacyclic wrap
  skip one sub_a rotation
  enable coefficient-one fast sub_a with selector value zero
  change one butterfly source index
  ```

  Each control must fail a named phase or closure gate. A generic exception
  without the expected failed invariant does not count.

- [ ] **Step 4: Verify RED**

  ```text
  python -m unittest \
    tests.research.test_candidate_d_operator_closure -v
  ```

  Expected: import failure.

- [ ] **Step 5: Implement canonical closure and one finite revision**

  Start with:

  ```text
  Gamma_0 = {1, 2N-1}
  ```

  where `1` is identity and `2N-1` is `tau_minus_one`.

  If `Gamma_0` fails representation but all exact phase oracles remain
  coherent, enumerate the automorphism labels generated by source operations,
  sort them numerically, and search subsets in increasing cardinality up to
  four. The first exact subset is the single permitted `Gamma_1` revision.
  Record `equation_revisions_used=1`. Do not generate a second revision.

  A local phase mismatch, failed negative control, or no exact basis of size
  at most four is terminal.

- [ ] **Step 6: Emit exact D2 evidence**

  Required rows include:

  ```text
  N
  schedule_case
  basis_index
  operation
  accumulator_index
  selector_bit
  gamma_count
  matrix_rank
  expected_hash
  actual_hash
  status
  ```

  `theory_checks/candidate_d_operator_closure.md` states the proven finite
  identity, dimensions, normal form, controls, and scope. It must explicitly
  say the finite result is not a Torus noise or RLWE security proof.

- [ ] **Step 7: Run D2 and transition only on pass**

  ```text
  python scripts/run_candidate_d_d2_closure.py
  python -m unittest \
    tests.research.test_candidate_d_source_map \
    tests.research.test_negacyclic_operator \
    tests.research.test_candidate_d_operator_closure -v
  ```

  On pass:

  ```text
  python scripts/mat_sab_research_state.py transition \
    D D2_OPERATOR_CLOSURE_PASS \
    --decision PASS_D2_OPERATOR_CLOSURE_G_LE_4
  ```

  On reject/block, execute Task 9.

- [ ] **Step 8: Commit**

  ```text
  git add research/mat_sab/candidate_d_operator_closure.py \
    tests/research/test_candidate_d_operator_closure.py \
    scripts/run_candidate_d_d2_closure.py \
    theory_checks/candidate_d_operator_closure.md \
    repro/candidate_d_admission/d2_summary.csv \
    repro/candidate_d_admission/closure_basis.csv \
    repro/candidate_d_admission/phase_equivalence.csv \
    repro/candidate_d_admission/negative_controls.csv \
    repro/candidate_d_admission/schedule_trace.csv \
    research_state.yaml
  git commit -m "research: gate Candidate D operator closure"
  ```

### Task 7: Gate Integer Binding, Security Objects, And Noise

**Files:**
- Create:
  `research/mat_sab/candidate_d_admission.py`
- Create:
  `tests/research/test_candidate_d_admission.py`
- Create:
  `theory_checks/candidate_d_security_noise.md`
- Create:
  `repro/candidate_d_admission/binding_domain.csv`
- Create:
  `repro/candidate_d_admission/security_object_map.csv`
- Create:
  `repro/candidate_d_admission/noise_bound.csv`

**Interfaces:**
- Produces:

  ```python
  LUTDomain
  SecurityObject
  NoiseParameters
  NoiseResult
  centered_integer_lut(values, plaintext_bits) -> tuple[int, ...]
  torus_scale(torus_bits, plaintext_bits) -> int
  validate_binding_domain(domain: LUTDomain) -> str
  audit_security_objects(objects: tuple[SecurityObject, ...]) -> str
  covariance_step(
      covariance: tuple[tuple[float, ...], ...],
      public_operator_norm: float,
      fresh_error_lambda_max: float,
  ) -> tuple[tuple[float, ...], ...]
  binding_variance_bound(
      covariance,
      transformed_lut_norms: tuple[float, ...],
  ) -> float
  decoding_failure_bound(
      variance: float,
      margin: float,
      observations: int,
  ) -> float
  derive_noise_decision(result: NoiseResult) -> str
  ```

- [ ] **Step 1: Write integer-grid and Torus-scale tests**

  For plaintext bits `p in {2,3,5,8}`:

  ```text
  Delta_integer = 2^(64-p)
  Delta_torus = 2^(-p)
  centered coefficients lie in [-2^(p-1), 2^(p-1)-1]
  TV_F = Delta_integer * F_Z mod 2^64
  ```

  Require the target `p=3` domain and the exact finite-checker envelope
  `[-128,128]`. Reject fractional Torus LUT coefficients, mixed scales,
  coefficients outside the registered bound, and a binder classified as
  Torus-by-Torus multiplication.

- [ ] **Step 2: Write security-object mapping tests**

  Require exactly these rows:

  | Object | Allowed realization |
  |---|---|
  | initial operator basis | public trivial RLWE encoding of scaled monomials; no secret is claimed hidden at setup |
  | operator channel | ordinary TRLWE/RLWE under one output secret |
  | selector bit | existing scalar TRGSW/GGSW sample |
  | NCMUX automorphism | existing TRLWE automorphism key switch |
  | rotation | public monomial multiplication |
  | late binding | public bounded integer-polynomial multiplication |
  | extraction/packing | existing standard extraction and key switching |
  | vector of outputs | public post-processing of secure operator channels |

  Reject rows containing correlated selector errors, structured nonuniform
  masks, secret-dependent public metadata, or an unregistered circular/KDM
  assumption.

  The output-vector row must distinguish semantic security from independent
  ciphertext-distribution compatibility. If downstream code requires
  independently randomized outputs, record rerandomization as a D4 cost and
  do not claim standard independent output distribution at D3.

- [ ] **Step 3: Write covariance and mutation tests**

  Use exact small matrices for `g=1,2,4`. Require:

  ```text
  Var(L_F(U))
    <= lambda_max(Sigma_U)
       * sum_gamma ||gamma(F_Z)||_2^2
  ```

  Test a covariance matrix with nonzero off-diagonal entries. A mutation that
  drops off-diagonal covariance must produce a smaller invalid bound and fail.
  Also require deterministic `L1` and `L-infinity` bounds.

- [ ] **Step 4: Verify RED**

  ```text
  python -m unittest tests.research.test_candidate_d_admission -v
  ```

  Expected: import failure.

- [ ] **Step 5: Implement the target recurrence**

  Parse `l=1`, `bg_bit=23`, `sigma_out=2^-50`, `h=39`, `r_prec=7`, and
  `N=2048` from source. For each selector event, use a conservative fresh
  error covariance upper bound derived from:

  ```text
  rows = (out_k + 1) * l
  digit_bound = 2^(bg_bit-1)
  q_ep = rows * N * digit_bound^2 * sigma_out^2
  lambda_max(Q_shared) <= g * q_ep
  ```

  Propagate:

  ```text
  Sigma_(t+1) <= A_t Sigma_t A_t^T + Q_t
  ```

  with rotations and `tau_minus_one` norm one. Do not assume channels remain
  independent after shared selectors.

  At binding, include the actual registered LUT norm, `Delta`, decomposition
  error, extraction, packing key switch, final key switch, the generic
  include-zero selector events unless the fast-path proof passes, and a union
  bound over `r*N_active` outputs. Report both:

  ```text
  sub-Gaussian variance/tail bound
  deterministic L1 worst-case bound
  ```

  If the required external-product error lemma cannot be justified from a
  cited standard result and the local parameters, the gate is
  `BLOCK_D3_NOISE_LEMMA_INCOMPLETE`, not pass.

  The D1 full-text review must provide the target parameter row's stated
  correctness/failure target or an explicitly cited derivation. Candidate D
  passes only if its union-bound failure is no greater than both that target
  and the same-recurrence scalar/B1 bound. If the source does not support a
  numeric target, emit `BLOCK_D3_NOISE_TARGET_UNANCHORED`; do not invent
  `2^-40`, `2^-64`, or another threshold.

- [ ] **Step 6: Write the proof record**

  `theory_checks/candidate_d_security_noise.md` contains:

  ```text
  supported LUT domain and Delta
  ideal correctness theorem
  legal linear late-binding lemma
  standard-object hybrid sequence
  inherited circular-security statement
  covariance recurrence
  deterministic error bound
  decode margin and union-bound calculation
  unsupported output-distribution caveat
  exact assumptions and scope
  ```

  Every theorem labels assumptions, conclusion, and artifact/source anchors.

- [ ] **Step 7: Run focused tests**

  ```text
  python -m unittest tests.research.test_candidate_d_admission -v
  ```

  Expected: all binding, security, covariance, and mutation tests pass. The
  candidate noise verdict may still be reject or block; tests verify correct
  derivation, not a favorable result.

- [ ] **Step 8: Commit**

  ```text
  git add research/mat_sab/candidate_d_admission.py \
    tests/research/test_candidate_d_admission.py \
    theory_checks/candidate_d_security_noise.md \
    repro/candidate_d_admission/binding_domain.csv \
    repro/candidate_d_admission/security_object_map.csv \
    repro/candidate_d_admission/noise_bound.csv
  git commit -m "research: gate Candidate D binding and noise"
  ```

### Task 8: Build The Complete D3 Cost, Resource, And Amdahl Gate

**Files:**
- Modify:
  `research/mat_sab/candidate_d_admission.py`
- Modify:
  `tests/research/test_candidate_d_admission.py`
- Create:
  `scripts/run_candidate_d_d3_admission.py`
- Create:
  `theory_checks/candidate_d_complete_cost.md`
- Create:
  `repro/candidate_d_admission/structural_cost.csv`
- Create:
  `repro/candidate_d_admission/amdahl_projection.csv`
- Create:
  `repro/candidate_d_admission/resource_projection.csv`
- Create:
  `repro/candidate_d_admission/d3_summary.csv`

**Interfaces:**
- Adds:

  ```python
  StructuralCost
  ProfileBudget
  ResourceProjection
  AmdahlProjection
  exact_dense_cost(r, params) -> StructuralCost
  operator_cost(g, r, params) -> StructuralCost
  project_complete_sab(
      b1: ProfileBudget,
      candidate: StructuralCost,
      late_binding_ratio: float,
      pessimistic: bool,
  ) -> AmdahlProjection
  derive_d3_decision(
      closure, novelty, noise, cost, resource
  ) -> str
  ```

- [ ] **Step 1: Write exact structural-count tests**

  For `r=4`, `g=2`, `k=1`, `l=1`, `H=573440`:

  ```text
  B1 products/event = (k+r)^2 = 25
  B1 selector ring products = 25*H = 14336000
  D products/event = 4*l*g = 8
  D selector ring products = 8*H = 4587520
  selector-product reduction = 3.125x
  B1 materialized components/event = k+r = 5
  D materialized components/event = g*(k+1) = 4
  NCMUX events = 5080
  binary sub_a calls = 39
  late-binding component products = g*r*(k+1) = 16
  ```

  Add `r=1,2,8` rows. The D encrypted hot-path selector count must be
  independent of `r`; binding and output-tail counts may be linear in `r`.

  Emit two include-zero rows:

  ```text
  generic: base selector events H plus 79872 sub_a selector events
  coeff-one-fast: base selector events H, with a PASS proof anchor
  ```

  If the coefficient-one proof is absent, the pessimistic admission row must
  use the generic count.

- [ ] **Step 2: Write measured-profile binding tests**

  Parse these existing B1 values from their artifacts:

  ```text
  complete r=4 total = 24468333.700 us
  complete T/r = 6117083.425 us
  complete T/(r*N_active) = 2986.857141113 us
  repeated scalar T/(r*N_active) = 5219.972265625 us
  mat_ep_lifecycle share = 0.576230
  cmux_from_dft share = 0.380787
  ncmux_auto share = 0.007716
  sub_a share = 0.026891
  ```

  Reject overlapping categories whose total is interpreted as disjoint
  without an explicit residual calculation. Record instrumentation shares as
  attribution inputs, not formal latency measurements.

- [ ] **Step 3: Write central and pessimistic projection tests**

  Central structural ratios for `g=2`, `r=4`:

  ```text
  ep_ratio = 8/25 = 0.32
  materialization_ratio = 4/5 = 0.80
  ```

  The pessimistic row uses:

  ```text
  ep_ratio = 0.40
  materialization_ratio = 1.00
  automorphism_ratio = 1.00
  ```

  Both rows add setup, two-channel NCMUX automorphism, all `sub_a`, binding,
  extraction/KS, key-cache effects, and any output rerandomization. Admission
  requires the pessimistic complete ratio `<=1/1.10`.

  Until D4 provides a direct primitive benchmark, use this conservative
  late-binding proxy:

  ```text
  ring_product_us_upper =
    2 * (profile_mat_ep_us / (25 * profiled_selector_events))
  late_binding_us_upper =
    ring_product_us_upper * g * r * (k+1)
  ```

  The factor two is a registered projection safety factor. A mutation setting
  late-binding cost to zero must change the diagnostic but may not bypass the
  requirement that this proxy or a stronger measured bound is present.

- [ ] **Step 4: Implement resource accounting**

  Count:

  ```text
  selector key bytes
  automorphism key bytes
  operator state bytes
  scratch bytes
  r materialized output bytes
  optional rerandomization material
  keygen work
  public late-binding transforms
  ```

  Compare B0a, B0b, B1, and D. B0b and B2 remain
  `REQUIRED_NOT_YET_LOCAL`; they cannot be used as favorable numeric rows.

- [ ] **Step 5: Implement the D3 decision**

  The only passing decision is:

  ```text
  PASS_D3_STANDARD_NOISE_FEASIBLE_COMPLETE_PROJECTION_GE_1_10
  ```

  Rejections and blocks are:

  ```text
  REJECT_D3_ILLEGAL_BINDING_DOMAIN
  REJECT_D3_NONSTANDARD_SECURITY_OBJECT
  REJECT_D3_DECODING_MARGIN
  REJECT_D3_COMPLETE_PROJECTION_LT_1_10
  REJECT_D3_RESOURCE_OVERHEAD
  BLOCK_D3_NOISE_LEMMA_INCOMPLETE
  BLOCK_D3_NOISE_TARGET_UNANCHORED
  BLOCK_D3_COST_INPUT_INCOMPLETE
  ```

  `g=3` or `g=4` is not rejected by name; it is evaluated by the same complete
  cost and noise formulas.

- [ ] **Step 6: Run D3**

  ```text
  python scripts/run_candidate_d_d3_admission.py
  python -m unittest tests.research.test_candidate_d_admission -v
  ```

  Expected: deterministic D3 artifacts and one derived decision. Do not
  transition state yet; Task 9 verifies the whole chain atomically.

- [ ] **Step 7: Commit**

  ```text
  git add research/mat_sab/candidate_d_admission.py \
    tests/research/test_candidate_d_admission.py \
    scripts/run_candidate_d_d3_admission.py \
    theory_checks/candidate_d_complete_cost.md \
    repro/candidate_d_admission/structural_cost.csv \
    repro/candidate_d_admission/amdahl_projection.csv \
    repro/candidate_d_admission/resource_projection.csv \
    repro/candidate_d_admission/d3_summary.csv
  git commit -m "research: project Candidate D complete admission cost"
  ```

### Task 9: Derive And Apply The Atomic D0-D3 Terminal Decision

**Files:**
- Create:
  `scripts/run_candidate_d_admission.py`
- Create:
  `scripts/apply_candidate_d_admission.py`
- Create:
  `tests/research/test_candidate_d_gate.py`
- Create:
  `tests/research/test_candidate_d_closeout.py`
- Create:
  `docs/candidate_d_admission_report.md`
- Create:
  `repro/candidate_d_admission/summary.csv`
- Create:
  `repro/candidate_d_admission/proof_gate.csv`
- Create:
  `repro/candidate_d_admission/decision_evidence.json`
- Create:
  `repro/candidate_d_admission/artifact_index.csv`
- Modify:
  `hypotheses/hypothesis_register.yaml`
- Modify:
  `repro/artifact_manifest.md`
- Modify:
  `repro/run_log.csv`
- Modify:
  `repro/reproduction_checklist.md`
- Modify:
  `research_state.yaml`

**Interfaces:**
- Produces:

  ```python
  evaluate_candidate_d_admission(root: Path) -> AdmissionResult
  canonical_summary_record(result: AdmissionResult) -> dict[str, str]
  verify_candidate_d_artifacts(root: Path) -> AdmissionResult
  apply_candidate_d_decision(root: Path, result: AdmissionResult) -> None
  ```

- Terminal decisions:

  ```text
  ADMIT_CANDIDATE_D_TO_ISOLATED_ENCRYPTED_OPERATOR_IMPLEMENTATION
  REJECT_CANDIDATE_D_PRIOR_ART_SUBSUMPTION_ROUTE_E
  REJECT_CANDIDATE_D_OPERATOR_CLOSURE_ROUTE_E
  REJECT_CANDIDATE_D_BINDING_NOISE_SECURITY_ROUTE_E
  REJECT_CANDIDATE_D_NONPOSITIVE_COMPLETE_COST_ROUTE_E
  BLOCK_CANDIDATE_D_INCOMPLETE_EVIDENCE
  ```

- [ ] **Step 1: Write gate derivation tests**

  Admission requires all:

  ```text
  D0 baseline PASS
  D1 novelty PASS
  D2 closure PASS
  gamma_count <= 4
  all negative controls detected
  integer binding PASS
  standard object map PASS
  absolute noise/decode PASS
  pessimistic complete projection >= 1.10x B1
  resource gate PASS
  production permission was false before application
  ```

  Mutate each field independently and require the corresponding reject or
  block decision.

- [ ] **Step 2: Write artifact and path-safety tests**

  Reject:

  ```text
  duplicate summary row
  summary header drift
  artifact path escaping repository root
  symlinked output outside root
  missing source hash
  stale decision_evidence hash
  changed decision string with unchanged gates
  partial append-only ledger marker
  a second application with different content
  ```

  A second identical application is idempotent.

- [ ] **Step 3: Verify RED**

  ```text
  python -m unittest \
    tests.research.test_candidate_d_gate \
    tests.research.test_candidate_d_closeout -v
  ```

  Expected: import failure.

- [ ] **Step 4: Implement deterministic decision priority**

  Apply this order:

  ```python
  if d0 != "PASS":
      return BLOCK_INCOMPLETE
  if d1 == "REJECT":
      return REJECT_PRIOR_ART
  if d1 != "PASS":
      return BLOCK_INCOMPLETE
  if d2 == "REJECT":
      return REJECT_CLOSURE
  if d2 != "PASS":
      return BLOCK_INCOMPLETE
  if binding_or_security_or_noise == "REJECT":
      return REJECT_BINDING_NOISE_SECURITY
  if binding_or_security_or_noise != "PASS":
      return BLOCK_INCOMPLETE
  if complete_cost_or_resource == "REJECT":
      return REJECT_COMPLETE_COST
  if complete_cost_or_resource != "PASS":
      return BLOCK_INCOMPLETE
  return ADMIT
  ```

  No later positive gate can override an earlier rejection.

- [ ] **Step 5: Apply state and ledgers atomically**

  On `ADMIT`:

  ```text
  D.status = D3_ADMISSION_PASS
  goal_status = ACTIVE
  production_hot_path_permission = true
  last_decision =
    ADMIT_CANDIDATE_D_TO_ISOLATED_ENCRYPTED_OPERATOR_IMPLEMENTATION
  ```

  Permission means a separate opt-in D4 experimental path may be planned. It
  does not permit changing scalar defaults.

  On `REJECT`:

  ```text
  D.status = REJECTED
  E.status = SECURITY_NOVELTY_PREFLIGHT
  active_candidate = E
  production_hot_path_permission = false
  ```

  On `BLOCK`:

  ```text
  active_candidate = D
  goal_status = EXTERNAL_BLOCKED
  production_hot_path_permission = false
  ```

  Append one bounded marker block to each ledger. Record the exact command,
  commit, platform, artifact directory, and scoped conclusion.

- [ ] **Step 6: Run the complete verification suite**

  ```text
  python scripts/run_candidate_d_admission.py
  python scripts/apply_candidate_d_admission.py --check
  python scripts/apply_candidate_d_admission.py
  python scripts/apply_candidate_d_admission.py --check
  python -m unittest discover -s tests/research -v
  python scripts/mat_sab_research_state.py validate
  git diff --check
  ```

  Expected:

  ```text
  one derived Candidate D decision
  second apply is a no-op
  all research tests pass
  PASS_RESEARCH_STATE_VALID
  no whitespace errors
  ```

- [ ] **Step 7: Perform independent internal review**

  Use two independent reviews:

  ```text
  Review A: spec/plan compliance and source/citation support
  Review B: algebra, negative controls, noise, and cost recomputation
  ```

  Reviewers may not rely only on `summary.csv`; they recompute from source
  artifacts. Any material disagreement changes the result to
  `BLOCK_CANDIDATE_D_INCOMPLETE_EVIDENCE` until resolved.

- [ ] **Step 8: Commit the terminal D0-D3 package**

  ```text
  git add scripts/run_candidate_d_admission.py \
    scripts/apply_candidate_d_admission.py \
    tests/research/test_candidate_d_gate.py \
    tests/research/test_candidate_d_closeout.py \
    docs/candidate_d_admission_report.md \
    repro/candidate_d_admission/summary.csv \
    repro/candidate_d_admission/proof_gate.csv \
    repro/candidate_d_admission/decision_evidence.json \
    repro/candidate_d_admission/artifact_index.csv \
    hypotheses/hypothesis_register.yaml \
    repro/artifact_manifest.md \
    repro/run_log.csv \
    repro/reproduction_checklist.md \
    research_state.yaml
  git commit -m "research: close Candidate D admission campaign"
  ```

## Completion Boundary

This plan is complete only when Task 9 records one derived terminal decision.
An `ADMIT` result authorizes a new reviewed D4-D6 plan for isolated encrypted
operators and complete SAB integration. A `REJECT` result starts only
Candidate E's security/novelty preflight. A `BLOCK` result names the exact
missing evidence and command needed to resume; it does not start another
theory or implementation loop.

No outcome from D0-D3 is itself a complete SAB speedup or paper claim.
