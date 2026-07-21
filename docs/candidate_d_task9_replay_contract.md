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

1. Task 9 derives the runner's complete repository-local Python import closure
   recursively from `input_commit`. Normal, `from`, relative, package
   initializer, and literal dynamic imports are included. The sorted unique
   scientific-source registry must match that closure exactly; unresolved,
   non-literal dynamic, ambiguous, shadowed, or undeclared local imports fail.
   Importer callables may be obtained only through the reviewed direct,
   attribute, `getattr`, and simple alias forms. Subscript, `eval`, `exec`,
   wrapper-return, or other unsupported importer recovery fails closed.
2. The runner, every closure source, every required input, and every canonical
   tracked output is a regular committed file read from `input_commit`; mutable
   files in the caller's active worktree are not replay inputs.
3. Task 9 creates a clean detached checkout of the exact `input_commit` and
   executes the committed runner there. The checkout and the separate empty
   temporary `--output-root` are removed on success and failure.
4. The runner executes with isolated Python startup and an external bytecode
   cache. An import-time finder/loader guard validates immutable spec and
   loader origins before each repository-local module body executes, while an
   execution audit rejects unregistered checkout code. Every loaded local
   module must originate at its exact authenticated closure path. The audit
   record survives `sys.modules` removal; mutable `__file__` or `__spec__`
   values cannot authenticate a source. Preloaded, shadowed, or unregistered
   repository-local modules fail.
5. The runner receives an empty temporary `--output-root`, explicit full
   `--input-commit`, and explicit full `--controller-commit`.
6. The child writes a parent-nonce-bound completion attestation through a
   separate control file only after runner return and final import-integrity
   checks. The parent validates its exact schema, nonce, and audited immutable
   origins. Successful early termination, including `os._exit(0)`, has no
   attestation and fails.
7. Before and after execution, both Git status including all untracked files
   and a byte/type snapshot including ignored files and the complete `.git`
   directory must match. Any checkout or Git metadata write fails; the
   caller's active worktree is not changed or cleaned.
8. The temporary output tree contains exactly the canonical stage outputs,
   `candidate_d_stage_replay.json`, and only their necessary parent
   directories. Extra empty directories, symlinks, junctions, FIFOs, sockets,
   devices, and other non-regular nodes fail.
9. Every temporary output is byte-identical to the corresponding regular file
   committed at `input_commit`.
10. The manifest has schema `candidate-d-stage-replay-v1`, names the stage,
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
