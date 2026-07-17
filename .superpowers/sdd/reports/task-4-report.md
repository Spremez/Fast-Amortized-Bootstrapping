# Task 4 Report: Candidate A Adversarial Mechanism Gate

## Status

- Task status: COMPLETE
- Computed decision:
  `REJECT_CANDIDATE_A_STANDARD_PVW_RANDOMIZATION_ROUTE_TO_B`
- Production code permission: `false`
- State application: intentionally deferred to Task 5
- Implementation commit:
  `06a35339bdcfdb5529aa28dc6f3be19cdae0271d`
  (`Execute Candidate A star-cycle mechanism gate`)

## Scope And Boundaries

Task 4 added only the evaluator, research tests, generated evidence, and
gate documentation named in the brief. It did not modify
`research_state.yaml`, C sources or headers, `main.c`, `Makefile`, or the
Task 3 theory file.

The finite-field checker is a mechanism and key-format preflight. It does not
claim RLWE security, a noise bound, production readiness, or a complete-SAB
performance improvement.

## TDD Evidence

### RED

Command:

```powershell
python -m unittest tests.research.test_candidate_a_gate -v
```

Result before the evaluator existed: exit code 1, one loader error, and the
expected root cause:

```text
ModuleNotFoundError: No module named 'scripts.run_candidate_a_star_cycle_gate'
Ran 1 test in 0.000s
FAILED (errors=1)
```

### GREEN

Focused command:

```powershell
python -m unittest tests.research.test_candidate_a_gate -v
```

Result after implementation:

```text
Ran 4 tests in 0.187s
OK
```

Fresh post-commit full discovery:

```powershell
python -m unittest discover -s tests/research -p "test_*.py" -v
```

Result:

```text
Ran 32 tests in 0.209s
OK
```

The pre-change baseline was 28 tests, all passing.

## Computed Gates

| Gate | Status | Evidence |
| --- | --- | --- |
| Source and support | PASS | All five source tokens resolve; Stage203 active support equals the `4r` star-cycle support for `r=2,4,6`. |
| Phase zero/one | PASS | All six `(r, mu)` rows are consistent with zero nonzero residuals. |
| Dense control | PASS | Dense column dimensions are all one for every tested `r`. |
| Negative controls | PASS | Generic dense randomizers have entries outside the star support, and every `r` has both consistent and inconsistent one-term-removal outcomes. |
| Standard PVW randomization | FAIL | Star-cycle support loses at least one per-column kernel-randomization degree for every tested `r`. |
| Production code | FAIL | Later security, noise, and Amdahl gates remain required. |

Phase rows:

| r | mu values | support terms | affine dimension | residual nonzero | status |
| --- | --- | --- | --- | --- | --- |
| 2 | 0, 1 | 8 | 2 | 0 | PASS |
| 4 | 0, 1 | 16 | 0 | 0 | PASS |
| 6 | 0, 1 | 24 | 0 | 0 | PASS |

Randomization rows:

| r | star-cycle dimensions | star status | dense dimensions | dense status |
| --- | --- | --- | --- | --- |
| 2 | `0;1;1` | FAIL | `1;1;1` | PASS |
| 4 | `0;0;0;0;0` | FAIL | `1;1;1;1;1` | PASS |
| 6 | `0;0;0;0;0;0;0` | FAIL | `1;1;1;1;1;1;1` | PASS |

Negative-control rows record generic outside-support nonzero counts of 1, 9,
and 25 for `r=2,4,6`. One-term-removal outcomes contain both `consistent` and
`inconsistent` for each tested lane count.

The decision is diagnostic rather than hard-coded:

```python
admitted = support_gate and phase_gate and dense_control_gate and negative_gate and randomization_gate
```

The first four mechanism gates pass, but the standard-PVW randomization gate
fails. The conjunction therefore rejects the direct sparse route and selects
the Candidate B factorized route.

## Artifact Verification

CSV schemas and row counts were checked exactly:

| CSV | Rows |
| --- | --- |
| `summary.csv` | 1 |
| `phase_constraints.csv` | 6 |
| `randomization_dimension.csv` | 6 |
| `negative_controls.csv` | 51 |
| `source_mapping.csv` | 5 |
| `proof_gate.csv` | 6 |
| `artifact_index.csv` | 10 |

Every one of the 10 indexed artifacts was recomputed with
`Get-FileHash -Algorithm SHA256`; all byte counts and lowercase SHA-256
values matched `artifact_index.csv`.

An external pre/post hash check covered all 13 Task 4 files around:

```powershell
python scripts/run_candidate_a_star_cycle_gate.py
```

It reported:

```text
decision=REJECT_CANDIDATE_A_STANDARD_PVW_RANDOMIZATION_ROUTE_TO_B
checked_files=13
changed_files=0
```

The post-commit generator rerun printed the same decision and
`git diff --exit-code` returned zero. `git status --short` contained only the
pre-existing untracked `.superpowers/` tree.

`research_state.yaml` retained SHA-256:

```text
F2AFE1DF99BE701986FC1C9D79B6AD9BF2341E91C8D89E2E3C3538E3CAAD51E5
```

## Files

- `scripts/run_candidate_a_star_cycle_gate.py`
- `tests/research/test_candidate_a_gate.py`
- `algorithm_variants/candidate_a_star_cycle_sparse_mat_ggsw.md`
- `experiments/candidate_a_star_cycle_gate_plan.md`
- `docs/candidate_a_star_cycle_mechanism_gate.md`
- `repro/candidate_a_star_cycle_gate/summary.csv`
- `repro/candidate_a_star_cycle_gate/phase_constraints.csv`
- `repro/candidate_a_star_cycle_gate/randomization_dimension.csv`
- `repro/candidate_a_star_cycle_gate/negative_controls.csv`
- `repro/candidate_a_star_cycle_gate/source_mapping.csv`
- `repro/candidate_a_star_cycle_gate/proof_gate.csv`
- `repro/candidate_a_star_cycle_gate/artifact_index.csv`
- `repro/candidate_a_star_cycle_gate/reproduction_commands.md`

## Self-Review

- Confirmed the evaluator consumes the Task 3 model and Stage203 equation map.
- Confirmed exactly one decision is selected from the five-gate conjunction.
- Confirmed all source, phase, dense, negative, and randomization rows are
  computed from model outputs.
- Confirmed artifact field order matches the brief.
- Confirmed generated text is ASCII and deterministic.
- Confirmed exact reproduction commands are present for the complete evidence
  set.
- Confirmed no security or performance overclaim.
- Confirmed no protected or out-of-scope tracked file changed.

## Controller Follow-Up

The original `proof_gate.csv` paired a `FAIL` status for
`standard_pvw_randomization` with the contradictory interpretation
`star support retains one PVW kernel degree per column`.

A regression test now reads the generated proof CSV and requires the failed
row to state:

```text
star support fails to retain one PVW kernel degree per column
```

The test was run before the generator fix and failed with the exact
`retains` versus `fails to retain` mismatch. After changing only the
generator interpretation and regenerating evidence:

```text
python -m unittest tests.research.test_candidate_a_gate -v
Ran 5 tests in 0.227s
OK

python -m unittest discover -s tests/research -p "test_*.py" -v
Ran 33 tests in 0.318s
OK
```

The refreshed `proof_gate.csv` is 475 bytes with SHA-256
`a08a7c1fa199a1449eab0d15016e099eb7d026b8b5dea87b9a4f974b8591c171`;
the corresponding `artifact_index.csv` entry matches. The computed rejection
and all other gate evidence remain unchanged. `research_state.yaml` retains
its original SHA-256, and no C or build file changed.

## Concerns

One verification attempt ran full discovery and a second generator invocation
concurrently. Both write the same deterministic artifacts, so Windows raised
a transient sharing `PermissionError`. No code change was made in response.
All verification commands were rerun sequentially and passed.

The substantive limitation is intentional: finite prime-field evidence does
not establish the security, noise, or performance properties reserved for
later gates.
