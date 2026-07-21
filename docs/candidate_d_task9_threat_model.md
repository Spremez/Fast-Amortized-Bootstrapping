# Candidate D Task 9 Finite Threat Model

## Scope

Task 9 authenticates reviewed deterministic execution, not arbitrary
untrusted code. Mandatory code review is a prerequisite for scientific
authority. The review covers the canonical stage runner and its exact
recursive repository-local source closure at `input_commit`.

The trusted computing base is Git, the recorded CPython runtime and standard
library, the Task 9 controller sources at `controller_commit`, and the
reviewed canonical runner plus local source closure at `input_commit`.

The caller working tree, untracked and ignored files, ambient `PYTHONPATH`,
hand-authored CSV or Markdown, output directories, and mutable dependency
resolution outside the declared local closure are untrusted.

## Defense In Depth

The import-time guard, execution audit, checkout snapshot, strict output tree,
and nonce-bound completion attestation detect accidental contamination and
early termination under the reviewed-code model. These controls are defense
in depth, not a hostile-code sandbox.

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
