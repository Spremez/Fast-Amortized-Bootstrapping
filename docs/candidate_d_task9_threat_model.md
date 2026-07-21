# Candidate D Task 9 Finite Threat Model

## Scope

Task 9 authenticates reviewed deterministic execution, not arbitrary
untrusted code. Mandatory code review is a prerequisite for scientific
authority. The review covers the canonical stage runner and its exact
recursive repository-local source closure at `input_commit`.

The trusted computing base is Git, the recorded CPython runtime and standard
library, the commit-pinned Task 9 launcher and controller execution closure at
`controller_commit`, and the reviewed scientific sources in the exact local
execution closure at `input_commit`. The launcher is read as bytes with
`git show <controller_commit>:scripts/candidate_d_task9_launcher.py` and is
executed from stdin under `python -I -S`; a mutable launcher file is never an
authoritative entrypoint.

Before importing repository code, the launcher creates a self-contained
`--no-local` checkout based at `input_commit`, rejects Git alternates, and
overlays the complete controller execution closure from `controller_commit`.
It derives the resulting local import closure and verifies every closure byte
against its designated commit. This composite rule intentionally permits a
reviewed future D1 input commit to change `candidate_d_literature.py` and its
registry without allowing it to replace the frozen Task 9 controller.

The caller working tree, untracked and ignored files, ambient `PYTHONPATH`,
hand-authored CSV or Markdown, output directories, and mutable dependency
resolution outside the declared local closure are untrusted.

The caller repository passed as `--root` remains an untrusted evidence and
output destination. Task 9 checks every decision input used there against its
pinned Git blob. Neither ambient `PYTHONPATH`, a script-directory shadow, nor
mutable caller package initializers or modules enter the composite execution
tree. Plain `python scripts/run_candidate_d_admission.py` and
`python scripts/apply_candidate_d_admission.py` commands are historical and
non-authoritative.

## Defense In Depth

The import-time guard, execution audit, checkout snapshot, strict output tree,
and nonce-bound completion attestation detect accidental contamination and
early termination under the reviewed-code model. These controls are defense
in depth, not a hostile-code sandbox.

The canonical stage child also runs under `python -I -S`. Its execution audit
trusts only the explicit interpreter `stdlib` and `platstdlib` roots, never an
arbitrary initial `sys.path`, site-packages directory, or `.pth` expansion.
The `purelib` and `platlib` subtrees are explicitly excluded even when, as on
Windows, they are nested below the standard-library root.

A malicious commit-pinned Python runner is out of scope. Such a runner can
introspect or mutate same-process Python guards and can attempt to forge a
same-process completion proof. Arbitrary native code, same-user OS attacks,
process introspection, and deliberate writes outside the isolated checkout
are also out of scope. A stronger model requires a separately reviewed OS
sandbox or system-call monitor before D2 replay; Task 9 does not claim one.

## Current Terminal Decision

D1 BLOCK is independent of D2/D3 runtime replay. The missing reviewed D1
source is sufficient to terminate the priority chain before either replay is
invoked. D0 is PASS and D1 is BLOCK. D2 and D3 are SKIPPED / NOT_REACHED.
Production permission is false.
