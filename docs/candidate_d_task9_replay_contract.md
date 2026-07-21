# Candidate D Task 9 Deterministic Replay Contract

## Provenance Boundaries

Task 9 records three distinct commits:

- `input_commit` pins the D0-D3 scientific sources, baseline/profile inputs,
  and canonical stage artifacts being decided.
- `controller_commit` pins the Task 9 runner, closeout controller, research
  state validator, replay executor, package initializers, commit-pinned
  launcher, and this contract. Runtime bytes must exactly equal their blobs in
  that commit.
- `historical_block_commit` is fixed to
  `fba794ce8820fb2ab167bf928c9cdae67ed508b9`. It is the first corrected
  metadata terminal closeout whose immutable ledger blocks and run row bind
  input `c8221ad0fcd8413753ca4c3072f49460972de454`.
- Erratum supersession independently pins predecessor evidence commit
  `2e2508a4716f83a92d9b53e7b716569c642c1033`, its direct-parent controller
  `fd5043edb7128e4b5f7bb86ddfdd948c88f53fd0`, and decision-evidence SHA-256
  `48ac5ee01f3a24037a5ea0a9781c7528158498c4605f81985b8a722482f4277e`.
  The predecessor evidence, commit parent, source hashes, runtime hashes,
  artifact index, and ancestry to the current controller are verified before
  an existing erratum can be replaced. The old controller is never inferred
  solely from the block being replaced.

Erratum state is a two-ledger atomic pair. Both ledgers must contain either
the exact current blocks or the exact blocks reproduced from independently
authenticated predecessor evidence. A missing, deleted, tampered, or mixed
pair fails closed. Only a complete authenticated predecessor pair is replaced.

Current decision evidence has schema
`candidate-d-task9-decision-evidence-v4`; normal artifact validation rejects
all other schemas. Legacy v3 parsing is a private compatibility path used only
after a predecessor evidence commit and blob hash have been independently
fixed and authenticated.

These commits are not interchangeable. In particular, `c8221ad` is the
corrected evidence input, not the commit containing its corrected historical
closeout record.

## Finite Threat Model

The normative trust boundary is
`docs/candidate_d_task9_threat_model.md`. Task 9 authenticates reviewed
deterministic execution, not arbitrary untrusted code. Mandatory review of the
canonical stage runner and its exact recursive repository-local source closure
is a prerequisite for scientific authority. It is not a hostile-code sandbox.

The import guard, execution audit, checkout snapshot, strict output tree, and
completion attestation are defense in depth against accidental contamination
and early termination. A malicious commit-pinned runner, arbitrary native
code, same-user OS attacks, process introspection, and deliberate writes
outside the checkout are out of scope. A stronger claim requires a separately
reviewed OS sandbox or system-call monitor before D2.

D1 BLOCK is independent of D2/D3 runtime replay. For the current terminal
result, D2 and D3 are absent and `SKIPPED / NOT_REACHED`; no replay defense is
used to establish the D1 decision.

## Authoritative Task 9 Launcher

Task 9 run and apply are authoritative only through the launcher blob at the
full `controller_commit`:

```text
git show <controller_commit>:scripts/candidate_d_task9_launcher.py | python -I -S - --mode run --root . --input-commit <input_commit> --controller-commit <controller_commit> --run-date <YYYY-MM-DD> --execution-platform <audited-evidence-platform>
git show <controller_commit>:scripts/candidate_d_task9_launcher.py | python -I -S - --mode apply --root . --input-commit <input_commit> --controller-commit <controller_commit> --run-date <YYYY-MM-DD> --execution-platform <audited-evidence-platform>
```

Plain execution of the mutable worktree run/apply scripts is historical and
non-authoritative. The launcher uses only the standard library before
repository authentication. It creates a self-contained `--no-local` clone
with no alternates, checks out `input_commit`, then overlays the controller
paths from `controller_commit`. The recorded run closure is:

```text
research/__init__.py
research/mat_sab/__init__.py
research/mat_sab/candidate_d_baseline.py
research/mat_sab/candidate_d_literature.py
research/mat_sab/candidate_d_stage_replay.py
scripts/__init__.py
scripts/mat_sab_research_state.py
scripts/run_candidate_d_admission.py
scripts/run_candidate_d_d1_literature.py
```

Apply adds `scripts/apply_candidate_d_admission.py`. The launcher itself and
the three package initializers are included in controller runtime evidence.
Every executable or transitively imported local path must match this closure
and its designated commit before the child starts. The child then runs under
`python -I -S`; `--root` names only the caller's untrusted evidence/output
destination, whose participating bytes are checked against pinned Git blobs.

## Authority Rule

Static CSV parsing is only a consistency check. Under the finite threat model,
D2 or D3 may return PASS or REJECT only after mandatory source review and when
Task 9 executes the canonical stage runner and all of the following hold:

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
3. Task 9 creates a self-contained `--no-local` detached checkout of the exact
   `input_commit`, verifies that it has no Git alternates file, and executes
   the committed runner there. The checkout and the separate empty temporary
   `--output-root` are removed on success and failure.
4. The runner executes under `python -I -S` with isolated, no-site Python
   startup and an external bytecode
   cache. An import-time finder/loader guard validates immutable spec and
   loader origins before each repository-local module body executes, while an
   execution audit rejects unregistered checkout code. Every loaded local
   module must originate at its exact authenticated closure path. The audit
   record survives `sys.modules` removal; mutable `__file__` or `__spec__`
   values cannot authenticate a source. Executed code outside the checkout is
   accepted only from the interpreter's explicitly identified `stdlib` and
   `platstdlib` roots. Initial arbitrary `sys.path`, site-packages, and `.pth`
   paths are never trusted.
   Preloaded, shadowed, or unregistered repository-local modules fail.
5. The runner receives an empty temporary `--output-root`, explicit full
   `--input-commit`, and explicit full `--controller-commit`.
6. As defense in depth, the child writes a parent-nonce-bound completion
   attestation through a
   separate control file only after runner return and final import-integrity
   checks. The parent validates its exact schema, nonce, and audited immutable
   origins. Control configuration is consumed once from stdin and is absent
   from child command-line arguments. Successful early termination, including
   `os._exit(0)`, has no attestation and fails.
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
    `scientific_authority: true`. That flag means reviewed deterministic
    execution under this finite model; it does not claim malicious-runner
    containment.

If a canonical runner, checker/model, required input, or replay contract is
absent, the stage is BLOCKED. Hand-written or self-consistent CSV files have no
admission authority. Tests may use a `scientific_authority: false` fixture
runner solely to test controller mechanics; production D2/D3 contracts never
accept that flag.

## Runner CLI

Tasks 6 and 8 must implement this exact internal runner interface. Calling it
directly does not establish Task 9 authority; the authenticated Task 9
controller invokes it inside the replay boundary:

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
