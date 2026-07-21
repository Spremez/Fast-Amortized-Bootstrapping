# Candidate D Task 9 Deterministic Replay Contract

## Provenance Boundaries

Task 9 records three distinct commits:

- `input_commit` pins the D0-D3 scientific sources, baseline/profile inputs,
  and canonical stage artifacts being decided.
- `controller_commit` pins the Task 9 runner, closeout controller, research
  state validator, replay executor, and this contract. Runtime bytes must
  exactly equal their blobs in that commit.
- `historical_block_commit` is fixed to
  `fba794ce8820fb2ab167bf928c9cdae67ed508b9`. It is the first corrected
  metadata terminal closeout whose immutable ledger blocks and run row bind
  input `c8221ad0fcd8413753ca4c3072f49460972de454`.

These commits are not interchangeable. In particular, `c8221ad` is the
corrected evidence input, not the commit containing its corrected historical
closeout record.

## Authority Rule

Static CSV parsing is only a consistency check. D2 or D3 may return PASS or
REJECT only when Task 9 executes the canonical, reviewed stage runner and all
of the following hold:

1. The runner, every checker/model source, every required input, and every
   canonical tracked output exactly match `input_commit`.
2. The runner receives an empty temporary `--output-root`, explicit full
   `--input-commit`, and explicit full `--controller-commit`.
3. The runner does not mutate any tracked repository file.
4. The temporary tree contains exactly the canonical stage outputs plus
   `candidate_d_stage_replay.json`; no extra file or symlink is accepted.
5. Every temporary output is byte-identical to the corresponding tracked
   artifact.
6. The manifest has schema `candidate-d-stage-replay-v1`, names the stage,
   both commits, exact output list, one registered decision, and
   `scientific_authority: true`.

If a canonical runner, checker/model, required input, or replay contract is
absent, the stage is BLOCKED. Hand-written or self-consistent CSV files have no
admission authority. Tests may use a `scientific_authority: false` fixture
runner solely to test controller mechanics; production D2/D3 contracts never
accept that flag.

## Runner CLI

Tasks 6 and 8 must implement this exact runner interface:

```text
python <canonical-runner> \
  --root <absolute-repository-root> \
  --output-root <empty-temporary-directory> \
  --input-commit <full-sha> \
  --controller-commit <full-sha>
```

The runner writes only under `output-root`. Paths below it are the same
canonical repository-relative paths declared by Task 9. The replay manifest
is not a scientific artifact; it authenticates one deterministic execution.

## D2 Semantic Ownership

The canonical Task 6 generator/checker owns and must test all semantics. Task
9 does not reproduce or waive them. Its reviewed implementation must cover:

- every intermediate phase and schedule trace after setup, each CMUX/NCMUX,
  each monomial operation, every `sub_a`, and final binding;
- the exact six registered negative controls, each tied to an actual failed
  trace and named invariant;
- closure equations, matrices, representation coefficients, rank, and exact
  basis-vector equality over the registered finite rings;
- explicit evidence that `Gamma_0` failed before the single permitted
  `Gamma_1` revision, when a revision is used.

## D3 Semantic Ownership

The canonical Tasks 7-8 generator/model owns and must test:

- fixed literature/source anchors and source-derived target parameters;
- covariance-aware noise recurrence and deterministic error bounds;
- exactly eight registered standard security objects;
- a verified coefficient-one proof anchor, otherwise the generic
  include-zero count with the additional 79,872 selector events;
- frozen B1 profile binding to the registered Stage 331 and Stage 322 inputs;
- complete Amdahl recomputation including late-binding proxy cost;
- all resource terms, including key generation work and late-binding
  transforms.

## Finite Routing

- D1 REJECT/BLOCK terminates at Task 9; D2 and D3 are not run.
- D1 PASS runs D2 with:

  ```text
  python scripts/run_candidate_d_d2_closure.py \
    --root <absolute-repository-root> \
    --output-root <staging-output-directory> \
    --input-commit <new-D1-commit> \
    --controller-commit <full-controller-sha>
  ```

- D2 REJECT/BLOCK terminates at Task 9; D3 is not run.
- D2 PASS runs D3, then Task 9:

  ```text
  python scripts/run_candidate_d_d3_admission.py \
    --root <absolute-repository-root> \
    --output-root <staging-output-directory> \
    --input-commit <new-D2-commit> \
    --controller-commit <full-controller-sha>
  ```

The stage output is installed only after the replay manifest and canonical
outputs satisfy this contract. The installed outputs and their scientific
sources are committed before Task 9 receives that stage commit as
`--input-commit`.

A BLOCK preserves Candidate D at the last valid gate, keeps Candidate E
reserved, and leaves production permission false. A later terminal run appends
commit-specific ledger markers; the historical BLOCK bytes are never edited.

Run date and execution platform are explicit Task 9 inputs bound into the
decision evidence. They describe evidence-controller execution only and are
not performance claims.
