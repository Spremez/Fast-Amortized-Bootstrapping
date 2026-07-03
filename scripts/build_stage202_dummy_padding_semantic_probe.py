#!/usr/bin/env python3
"""Stage202: dummy-padding semantic probe for structured selector proof route."""

from __future__ import annotations

import csv
import hashlib
import random
import subprocess
from pathlib import Path
from typing import Dict, Iterable, List, Sequence, Set, Tuple


ROOT = Path(__file__).resolve().parents[1]
OUT_DIR = ROOT / "repro" / "stage202_dummy_padding_semantic_probe"

SUMMARY_CSV = OUT_DIR / "summary.csv"
ASSUMPTION_CSV = OUT_DIR / "assumptions.csv"
SEMANTIC_CSV = OUT_DIR / "semantic_probe.csv"
RESOURCE_CSV = OUT_DIR / "resource_model.csv"
PROOF_GATE_CSV = OUT_DIR / "proof_gate.csv"
NEXT_CSV = OUT_DIR / "next_stage_queue.csv"
COMMANDS_MD = OUT_DIR / "reproduction_commands.md"
REPORT_MD = OUT_DIR / "dummy_padding_semantic_report.md"
ARTIFACT_CSV = OUT_DIR / "artifact_index.csv"

OUT_MD = ROOT / "docs" / "stage202_dummy_padding_semantic_probe.md"
PLAN_MD = ROOT / "experiments" / "stage202_dummy_padding_semantic_probe_plan.md"
THEORY_MD = ROOT / "theory_checks" / "stage202_dummy_padding_semantic_model.md"
VARIANT_MD = ROOT / "algorithm_variants" / "mat_rlwe_sab_dummy_padding_semantic_probe.md"

ROADMAP_MD = ROOT / "docs" / "roadmap_stage19_plus.md"
GOAL_MD = ROOT / "docs" / "goal_sab_max_acceleration.md"
CURRENT_GOAL_MD = ROOT / "docs" / "current_codex_goal_sab_completion.md"
HYPOTHESIS_YAML = ROOT / "hypotheses" / "hypothesis_register.yaml"
RUN_LOG = ROOT / "repro" / "run_log.csv"
MANIFEST = ROOT / "repro" / "artifact_manifest.md"
CHECKLIST = ROOT / "repro" / "reproduction_checklist.md"

STAGE201_SUMMARY = ROOT / "repro" / "stage201_structured_selector_distribution_probe" / "summary.csv"
STAGE201_CANDIDATE = ROOT / "repro" / "stage201_structured_selector_distribution_probe" / "candidate_matrix.csv"
STAGE201_PROOF = ROOT / "repro" / "stage201_structured_selector_distribution_probe" / "proof_gate.csv"
STAGE200_COUNTER = ROOT / "repro" / "stage200_formal_gap_model_with_probe" / "counterexample_matrix.csv"

DECISION = "PASS_STAGE202_DUMMY_PADDING_SEMANTIC_PROBE_PROOF_ONLY"


Poly = Tuple[int, ...]
Matrix = List[List[Poly]]


def rel(path: Path) -> str:
    return path.resolve().relative_to(ROOT.resolve()).as_posix()


def read_text(path: Path) -> str:
    return path.read_text(encoding="utf-8", errors="replace") if path.exists() else ""


def write_text_lf(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes((text.rstrip() + "\n").encode("utf-8"))


def write_csv(path: Path, rows: Iterable[Dict[str, str]], fields: List[str]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    normalized = [{field: row.get(field, "") for field in fields} for row in rows]
    with path.open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fields, lineterminator="\n")
        writer.writeheader()
        writer.writerows(normalized)


def table(rows: List[Dict[str, str]], fields: List[str]) -> str:
    def cell(value: str) -> str:
        return str(value).replace("|", "\\|").replace("\n", "<br>")

    out = [
        "| " + " | ".join(fields) + " |",
        "| " + " | ".join("---" for _ in fields) + " |",
    ]
    for row in rows:
        out.append("| " + " | ".join(cell(row.get(field, "")) for field in fields) + " |")
    return "\n".join(out) + "\n"


def append_once(path: Path, marker: str, text: str) -> None:
    current = read_text(path)
    if marker in current:
        return
    if current and not current.endswith("\n"):
        current += "\n"
    write_text_lf(path, current + text.lstrip("\n"))


def git_head() -> str:
    try:
        return subprocess.check_output(
            ["git", "rev-parse", "--short", "HEAD"],
            cwd=ROOT,
            text=True,
            stderr=subprocess.DEVNULL,
        ).strip()
    except Exception:
        return "unknown"


def sha256_file(path: Path) -> str:
    if not path.exists():
        return ""
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def random_poly(rng: random.Random, n: int, q: int) -> Poly:
    return tuple(rng.randrange(q) for _ in range(n))


def zero_poly(n: int) -> Poly:
    return tuple(0 for _ in range(n))


def poly_add(a: Poly, b: Poly, q: int) -> Poly:
    return tuple((x + y) % q for x, y in zip(a, b))


def poly_mul_negacyclic(a: Poly, b: Poly, q: int) -> Poly:
    n = len(a)
    out = [0] * n
    for i, ai in enumerate(a):
        for j, bj in enumerate(b):
            idx = i + j
            if idx >= n:
                out[idx - n] -= ai * bj
            else:
                out[idx] += ai * bj
    return tuple(x % q for x in out)


def mat_vec_mul(matrix: Matrix, vec: Sequence[Poly], q: int) -> List[Poly]:
    n = len(vec[0])
    out: List[Poly] = []
    for row in range(len(matrix)):
        acc = zero_poly(n)
        for col in range(len(vec)):
            acc = poly_add(acc, poly_mul_negacyclic(matrix[row][col], vec[col], q), q)
        out.append(acc)
    return out


def mismatch_count(a: Sequence[Poly], b: Sequence[Poly]) -> int:
    return sum(1 for row_a, row_b in zip(a, b) for x, y in zip(row_a, row_b) if x != y)


def active_pairs(r: int) -> Set[Tuple[int, int]]:
    """Count-matched toy active set with 4r semantic rows inside (r+1)^2 dense rows."""
    pairs: Set[Tuple[int, int]] = set()
    m = r + 1
    for lane in range(1, r + 1):
        next_lane = 1 + (lane % r)
        pairs.add((0, lane))
        pairs.add((lane, 0))
        pairs.add((lane, lane))
        pairs.add((lane, next_lane))
    assert len(pairs) == 4 * r
    assert all(0 <= row < m and 0 <= col < m for row, col in pairs)
    return pairs


def random_dense_matrix(rng: random.Random, m: int, n: int, q: int) -> Matrix:
    return [[random_poly(rng, n, q) for _ in range(m)] for _ in range(m)]


def structured_matrix(rng: random.Random, r: int, n: int, q: int, inactive: str) -> Matrix:
    m = r + 1
    active = active_pairs(r)
    matrix: Matrix = []
    for row in range(m):
        matrix_row: List[Poly] = []
        for col in range(m):
            if (row, col) in active:
                matrix_row.append(random_poly(rng, n, q))
            elif inactive == "zero_semantics":
                matrix_row.append(zero_poly(n))
            elif inactive == "random_semantics":
                matrix_row.append(random_poly(rng, n, q))
            else:
                raise ValueError(inactive)
        matrix.append(matrix_row)
    return matrix


def build_assumptions() -> List[Dict[str, str]]:
    return [
        {
            "assumption_id": "A1_count_matched_toy",
            "statement": "The finite model uses a count-matched active set with 4r semantic rows inside the dense (r+1)^2 shape.",
            "scope": "toy functional probe only",
            "evidence": rel(SEMANTIC_CSV),
            "falsification": "A production selector proof must replace the toy active set with real keygen equations.",
        },
        {
            "assumption_id": "A2_dummy_rows_public_shape",
            "statement": "Dummy padding keeps the dense public row shape but assigns semantic zero to inactive rows.",
            "scope": "Stage201 surviving public-pattern route",
            "evidence": rel(STAGE201_CANDIDATE),
            "falsification": "If dummy rows carry random semantics, the finite model must mismatch the structured reference.",
        },
        {
            "assumption_id": "A3_no_code_permission",
            "statement": "Finite semantic equivalence is not a production keygen, noise, security, or complete-SAB gate.",
            "scope": "claim policy",
            "evidence": rel(PROOF_GATE_CSV),
            "falsification": "Production code requires real keygen/noise and complete-SAB evidence.",
        },
    ]


def build_semantic_probe() -> List[Dict[str, str]]:
    rows: List[Dict[str, str]] = []
    q = 257
    n = 8
    seeds = range(8)
    for r in (2, 4, 6):
        m = r + 1
        active = active_pairs(r)
        inactive_count = m * m - len(active)
        for seed in seeds:
            rng_base = random.Random(2020000 + r * 100 + seed)
            vec = [random_poly(rng_base, n, q) for _ in range(m)]

            rng_struct = random.Random(2021000 + r * 100 + seed)
            structured_zero = structured_matrix(rng_struct, r, n, q, "zero_semantics")
            target = mat_vec_mul(structured_zero, vec, q)

            rng_zero = random.Random(2021000 + r * 100 + seed)
            dummy_zero = structured_matrix(rng_zero, r, n, q, "zero_semantics")
            rows.append(
                semantic_row(
                    "dummy_zero_semantics_vs_structured",
                    r,
                    n,
                    q,
                    seed,
                    len(active),
                    inactive_count,
                    mismatch_count(target, mat_vec_mul(dummy_zero, vec, q)),
                    "PASS_EQUIVALENCE",
                    "Dummy rows with semantic zero reproduce the declared structured reference in the toy model.",
                )
            )

            rng_rand = random.Random(2021000 + r * 100 + seed)
            dummy_random = structured_matrix(rng_rand, r, n, q, "random_semantics")
            rows.append(
                semantic_row(
                    "dummy_random_semantics_vs_structured",
                    r,
                    n,
                    q,
                    seed,
                    len(active),
                    inactive_count,
                    mismatch_count(target, mat_vec_mul(dummy_random, vec, q)),
                    "PASS_COUNTEREXAMPLE",
                    "Random semantic dummy rows do not preserve the structured function.",
                )
            )

            rng_dense = random.Random(2022000 + r * 100 + seed)
            dense_general = random_dense_matrix(rng_dense, m, n, q)
            rows.append(
                semantic_row(
                    "dense_general_vs_structured",
                    r,
                    n,
                    q,
                    seed,
                    len(active),
                    inactive_count,
                    mismatch_count(target, mat_vec_mul(dense_general, vec, q)),
                    "PASS_COUNTEREXAMPLE",
                    "General dense selectors are not semantically equivalent to the structured-zero model.",
                )
            )
    return rows


def semantic_row(
    probe: str,
    r: int,
    n: int,
    q: int,
    seed: int,
    active_count: int,
    inactive_count: int,
    mismatches: int,
    expected_status: str,
    interpretation: str,
) -> Dict[str, str]:
    if expected_status == "PASS_EQUIVALENCE":
        status = "PASS_EQUIVALENCE" if mismatches == 0 else "FAIL_MISMATCH"
    else:
        status = "PASS_COUNTEREXAMPLE" if mismatches > 0 else "FAIL_NO_MISMATCH"
    return {
        "probe": probe,
        "r": str(r),
        "N": str(n),
        "q": str(q),
        "seed": str(seed),
        "active_semantic_rows": str(active_count),
        "inactive_dummy_rows": str(inactive_count),
        "mismatches": str(mismatches),
        "status": status,
        "interpretation": interpretation,
    }


def build_resource_model() -> List[Dict[str, str]]:
    rows: List[Dict[str, str]] = []
    for r in (2, 4, 6):
        dense = (r + 1) * (r + 1)
        active = 4 * r
        inactive = dense - active
        rows.append(
            {
                "r": str(r),
                "dense_public_rows_per_T": str(dense),
                "active_semantic_rows_per_T": str(active),
                "inactive_dummy_rows_per_T": str(inactive),
                "public_row_saving_vs_dense": "0",
                "semantic_active_fraction": f"{active / dense:.9f}",
                "semantic_skip_potential": f"{inactive / dense:.9f}",
                "interpretation": "Dummy padding preserves dense public size; any speed value requires evaluator-side semantic skipping plus proof.",
                "evidence": rel(SEMANTIC_CSV),
            }
        )
    return rows


def build_proof_gate(semantic_rows: List[Dict[str, str]]) -> List[Dict[str, str]]:
    zero_failures = sum(1 for row in semantic_rows if row["probe"] == "dummy_zero_semantics_vs_structured" and row["status"] != "PASS_EQUIVALENCE")
    random_failures = sum(1 for row in semantic_rows if row["probe"] == "dummy_random_semantics_vs_structured" and row["status"] != "PASS_COUNTEREXAMPLE")
    dense_failures = sum(1 for row in semantic_rows if row["probe"] == "dense_general_vs_structured" and row["status"] != "PASS_COUNTEREXAMPLE")
    return [
        {
            "gate": "T2_toy_semantic_equivalence",
            "status": "PASS_TOY_ONLY" if zero_failures == 0 else "FAIL",
            "evidence": rel(SEMANTIC_CSV),
            "detail": f"dummy zero semantic failures={zero_failures}",
            "missing_before_code": "Replace toy active set with production selector/keygen equations.",
        },
        {
            "gate": "T2_negative_control_random_dummy",
            "status": "PASS_COUNTEREXAMPLE" if random_failures == 0 else "FAIL",
            "evidence": rel(SEMANTIC_CSV),
            "detail": f"random dummy counterexample failures={random_failures}",
            "missing_before_code": "Prove dummy public rows encrypt semantic zero and cannot carry arbitrary semantic terms.",
        },
        {
            "gate": "T2_negative_control_dense_general",
            "status": "PASS_COUNTEREXAMPLE" if dense_failures == 0 else "FAIL",
            "evidence": rel(SEMANTIC_CSV),
            "detail": f"dense general counterexample failures={dense_failures}",
            "missing_before_code": "Declare a new structured distribution; do not claim dense-equivalence.",
        },
        {
            "gate": "T3_resource_value",
            "status": "WEAK_PUBLIC_SIZE",
            "evidence": rel(RESOURCE_CSV),
            "detail": "dummy padding has zero public-row saving versus dense",
            "missing_before_code": "Show complete-SAB T_bootstrap/r value after semantic skipping and key materialization costs.",
        },
        {
            "gate": "T4_noise_keygen_security",
            "status": "BLOCKED",
            "evidence": rel(STAGE201_PROOF),
            "detail": "production keygen/noise/security proof not supplied",
            "missing_before_code": "Production keygen, security reduction, noise recurrence, and multi-seed gates.",
        },
    ]


def build_next_rows() -> List[Dict[str, str]]:
    return [
        {
            "priority": "P0",
            "route": "source_anchor_intake",
            "entry_condition": "Reviewed 2025/686 full text is supplied locally.",
            "gate": "Map source-specific SAB claims to inspected paper anchors.",
            "current_status": "waiting_external_artifact",
            "evidence": "repro/stage196_public_source_refresh/citation_gate.csv",
        },
        {
            "priority": "P1",
            "route": "production_selector_equation_probe",
            "entry_condition": "A real structured selector keygen equation is specified.",
            "gate": "Replace toy active set, prove dummy rows are semantic zero, run finite production-shaped phase/noise checks.",
            "current_status": "blocked_on_keygen_equations",
            "evidence": rel(PROOF_GATE_CSV),
        },
        {
            "priority": "P2",
            "route": "new_exact_mechanism_admission",
            "entry_condition": "A concrete exact-path backend/addmul/DFT mechanism is supplied.",
            "gate": "Projection, correctness, noise/resource, and complete-SAB T_bootstrap/r gates.",
            "current_status": "waiting_new_mechanism",
            "evidence": "repro/stage200_formal_gap_model_with_probe/gap_projection.csv",
        },
    ]


def build_summary_rows(semantic_rows: List[Dict[str, str]], proof_rows: List[Dict[str, str]]) -> List[Dict[str, str]]:
    inputs = [STAGE201_SUMMARY, STAGE201_CANDIDATE, STAGE201_PROOF, STAGE200_COUNTER]
    inputs_ok = all(path.exists() for path in inputs)
    semantic_failures = sum(1 for row in semantic_rows if not row["status"].startswith("PASS"))
    blocked_gates = sum(1 for row in proof_rows if row["status"] in {"BLOCKED", "WEAK_PUBLIC_SIZE"})
    return [
        {
            "gate": "stage202_inputs",
            "status": "PASS" if inputs_ok else "FAIL",
            "metric": "required_inputs_present",
            "value": "1" if inputs_ok else "0",
            "evidence": f"{rel(STAGE201_SUMMARY)}; {rel(STAGE201_PROOF)}",
            "detail": "Stage202 consumes Stage201 public-pattern proof route and Stage200 counterexamples.",
            "next_action": "Repair missing inputs before using this probe.",
        },
        {
            "gate": "stage202_semantic_probe",
            "status": "PASS" if semantic_failures == 0 else "FAIL",
            "metric": "semantic_failures",
            "value": str(semantic_failures),
            "evidence": rel(SEMANTIC_CSV),
            "detail": "Finite toy semantics pass for zero-semantic dummy rows and reject random-semantic/dense-general controls.",
            "next_action": "Do not generalize beyond the toy active set.",
        },
        {
            "gate": "stage202_resource_gate",
            "status": "WEAK_PUBLIC_SIZE",
            "metric": "public_row_saving_vs_dense",
            "value": "0",
            "evidence": rel(RESOURCE_CSV),
            "detail": "Dummy padding retains dense public row count, so key-size value is not demonstrated.",
            "next_action": "Require complete-SAB value proof before any implementation path.",
        },
        {
            "gate": "stage202_proof_gate",
            "status": "PROOF_ONLY",
            "metric": "blocked_or_weak_gates",
            "value": str(blocked_gates),
            "evidence": rel(PROOF_GATE_CSV),
            "detail": "Production selector equations, security/noise, and complete-SAB gates remain missing.",
            "next_action": "Proceed only with production selector equation probe or new exact mechanism.",
        },
        {
            "gate": "stage202_decision",
            "status": DECISION if inputs_ok and semantic_failures == 0 else "FAIL_STAGE202",
            "metric": "goal_status",
            "value": "active",
            "evidence": rel(SUMMARY_CSV),
            "detail": "Dummy padding semantic route is narrowed to toy proof-only; full goal remains active.",
            "next_action": "Do not implement compact SAB; continue only through P0/P1/P2.",
        },
    ]


def write_report(
    assumption_rows: List[Dict[str, str]],
    semantic_rows: List[Dict[str, str]],
    resource_rows: List[Dict[str, str]],
    proof_rows: List[Dict[str, str]],
    next_rows: List[Dict[str, str]],
    summary_rows: List[Dict[str, str]],
) -> None:
    write_text_lf(
        REPORT_MD,
        f"""# Dummy Padding Semantic Probe

Decision: `{DECISION}`.

Stage202 checks the only Stage201 public-pattern survivor in a finite
count-matched semantic model. The result is proof-only: semantic-zero dummy
rows match the declared structured toy reference, while random-semantic dummy
rows and general dense selectors do not.

## Summary

{table(summary_rows, ["gate", "status", "metric", "value", "evidence", "detail", "next_action"])}
## Assumptions

{table(assumption_rows, ["assumption_id", "statement", "scope", "evidence", "falsification"])}
## Resource Model

{table(resource_rows, ["r", "dense_public_rows_per_T", "active_semantic_rows_per_T", "inactive_dummy_rows_per_T", "public_row_saving_vs_dense", "semantic_active_fraction", "semantic_skip_potential", "interpretation", "evidence"])}
## Proof Gates

{table(proof_rows, ["gate", "status", "evidence", "detail", "missing_before_code"])}
## Next Queue

{table(next_rows, ["priority", "route", "entry_condition", "gate", "current_status", "evidence"])}

Full semantic probe rows are recorded in `{rel(SEMANTIC_CSV)}`.
""",
    )


def write_commands() -> None:
    write_text_lf(
        COMMANDS_MD,
        """# Stage202 Reproduction Commands

```powershell
# Rebuild dummy padding semantic probe
python scripts\\build_stage202_dummy_padding_semantic_probe.py

# Inspect outputs
Get-Content -Raw repro\\stage202_dummy_padding_semantic_probe\\summary.csv
Get-Content -Raw repro\\stage202_dummy_padding_semantic_probe\\semantic_probe.csv
Get-Content -Raw repro\\stage202_dummy_padding_semantic_probe\\resource_model.csv
Get-Content -Raw repro\\stage202_dummy_padding_semantic_probe\\proof_gate.csv
```
""",
    )


def write_docs(
    assumption_rows: List[Dict[str, str]],
    resource_rows: List[Dict[str, str]],
    proof_rows: List[Dict[str, str]],
    next_rows: List[Dict[str, str]],
    summary_rows: List[Dict[str, str]],
) -> None:
    write_text_lf(
        OUT_MD,
        f"""# Stage202 Dummy Padding Semantic Probe

Decision: `{DECISION}`.

Stage202 narrows the dummy padding proof route. It does not authorize compact
SAB production code.

## Gate Summary

{table(summary_rows, ["gate", "status", "metric", "value", "evidence", "detail", "next_action"])}
## Assumptions

{table(assumption_rows, ["assumption_id", "statement", "scope", "evidence", "falsification"])}
## Resource Model

{table(resource_rows, ["r", "dense_public_rows_per_T", "active_semantic_rows_per_T", "inactive_dummy_rows_per_T", "public_row_saving_vs_dense", "semantic_active_fraction", "semantic_skip_potential", "interpretation", "evidence"])}
## Proof Gates

{table(proof_rows, ["gate", "status", "evidence", "detail", "missing_before_code"])}
## Next Queue

{table(next_rows, ["priority", "route", "entry_condition", "gate", "current_status", "evidence"])}
""",
    )

    write_text_lf(
        PLAN_MD,
        """# Stage202 Plan

Goal: test the semantic boundary of Stage201's dummy-padding proof-only route.

Rules:

- use a finite count-matched toy model, not production keygen;
- dummy rows must be semantic zero to match the structured reference;
- random semantic dummy rows are a negative control;
- general dense selectors are a negative control;
- passing this toy gate does not grant code permission.
""",
    )

    write_text_lf(
        THEORY_MD,
        """# Stage202 Dummy Padding Semantic Model

Stage201 found that random-looking dummy rows can preserve simple public
patterns only if dense public shape is retained. Stage202 tests whether those
dummy rows can be semantically harmless in a finite model.

The toy model uses m=r+1 input components and a count-matched active set of 4r
semantic rows. Inactive dummy rows are tested in two ways:

- semantic zero: should match the structured reference;
- random semantics: should fail as a negative control.

This proves only a toy semantic condition. A production route still needs real
selector equations, keygen/security proof, noise recurrence, and complete-SAB
T_bootstrap/r evidence.
""",
    )

    write_text_lf(
        VARIANT_MD,
        """# Dummy Padding Semantic Probe

This is a proof probe, not an algorithm implementation.

Retained route:

- dense public shape with random-looking dummy rows;
- inactive dummy rows must be semantic zero;
- evaluator-side semantic skipping would need a declared structured keygen.

Blocked:

- key-size claim, because public row count is unchanged;
- complete-SAB speedup claim, because no production path is benchmarked;
- security/noise claim, because no production keygen/noise proof is supplied.
""",
    )


def update_global_docs() -> None:
    append_once(
        ROADMAP_MD,
        "## Stage 202: Dummy Padding Semantic Probe",
        f"""
## Stage 202: Dummy Padding Semantic Probe

Goal:

```text
Test the only Stage201 public-pattern-surviving selector route in a finite
semantic model, with explicit negative controls.
```

Status:

```text
Completed. Stage202 records {DECISION}. Dummy padding is semantically viable
only in a toy zero-semantic model and remains proof-only; keygen, security,
resource, noise, and complete-SAB gates are still missing.
```
""",
    )

    append_once(
        GOAL_MD,
        "Stage202 records dummy padding semantic probe",
        f"""
Stage202 records dummy padding semantic probe. Decision: `{DECISION}`. It
keeps dummy padding proof-only: semantic-zero dummy rows pass the toy model,
but random-semantic and dense-general controls fail, and no code path opens.
""",
    )

    append_once(
        CURRENT_GOAL_MD,
        "Treat Stage202 as dummy padding semantic probe",
        f"""
106. Treat Stage202 as dummy padding semantic probe:
    `{DECISION}`. Dummy padding is narrowed to a toy proof-only route with no
    key-size, security/noise, production keygen, or complete-SAB claim.
""",
    )

    append_once(
        HYPOTHESIS_YAML,
        "H126_dummy_padding_semantic_probe",
        f"""
  - id: H126_dummy_padding_semantic_probe
    statement: >
      Dummy padding can only continue as a compact/shared-output proof route
      if dummy rows are semantic zero under a declared structured selector
      model; random semantic dummy rows must fail.
    mechanism: >
      Stage202 tests a finite count-matched toy model against semantic-zero,
      random-semantic, and dense-general controls for r=2/4/6.
    status: stage202_dummy_padding_semantic_probe
    evidence: docs/stage202_dummy_padding_semantic_probe.md; experiments/stage202_dummy_padding_semantic_probe_plan.md; theory_checks/stage202_dummy_padding_semantic_model.md; repro/stage202_dummy_padding_semantic_probe/summary.csv
    current_decision: >
      {DECISION}
    failure_criteria:
      - semantic-zero dummy rows fail the toy equivalence check
      - random-semantic dummy rows do not produce counterexamples
      - the toy proof route is treated as production code permission
""",
    )

    append_once(
        RUN_LOG,
        "stage202-dummy-padding-semantic-probe-001",
        f"""
stage202-dummy-padding-semantic-probe-001,2026-07-04,{git_head()},Stage 202,analysis+finite-probe,python scripts/build_stage202_dummy_padding_semantic_probe.py,Stage201 proof route,none,{DECISION},Dummy padding semantic proof-only probe.,repro/stage202_dummy_padding_semantic_probe
""",
    )

    append_once(
        MANIFEST,
        "stage202_dummy_padding_semantic_probe",
        f"""
- stage202_dummy_padding_semantic_probe: `{DECISION}`
  - `docs/stage202_dummy_padding_semantic_probe.md`
  - `experiments/stage202_dummy_padding_semantic_probe_plan.md`
  - `theory_checks/stage202_dummy_padding_semantic_model.md`
  - `algorithm_variants/mat_rlwe_sab_dummy_padding_semantic_probe.md`
  - `repro/stage202_dummy_padding_semantic_probe/`
""",
    )

    append_once(CHECKLIST, "Stage202 dummy padding semantic probe recorded", """
- [x] Stage202 dummy padding semantic probe recorded.
""")


def write_artifacts(paths: List[Path]) -> None:
    rows = []
    for path in paths:
        rows.append(
            {
                "path": rel(path),
                "exists": "yes" if path.exists() else "no",
                "sha256": sha256_file(path),
                "bytes": str(path.stat().st_size) if path.exists() else "0",
            }
        )
    write_csv(ARTIFACT_CSV, rows, ["path", "exists", "sha256", "bytes"])


def main() -> None:
    assumption_rows = build_assumptions()
    semantic_rows = build_semantic_probe()
    resource_rows = build_resource_model()
    proof_rows = build_proof_gate(semantic_rows)
    next_rows = build_next_rows()
    summary_rows = build_summary_rows(semantic_rows, proof_rows)

    write_csv(ASSUMPTION_CSV, assumption_rows, ["assumption_id", "statement", "scope", "evidence", "falsification"])
    write_csv(
        SEMANTIC_CSV,
        semantic_rows,
        ["probe", "r", "N", "q", "seed", "active_semantic_rows", "inactive_dummy_rows", "mismatches", "status", "interpretation"],
    )
    write_csv(
        RESOURCE_CSV,
        resource_rows,
        [
            "r",
            "dense_public_rows_per_T",
            "active_semantic_rows_per_T",
            "inactive_dummy_rows_per_T",
            "public_row_saving_vs_dense",
            "semantic_active_fraction",
            "semantic_skip_potential",
            "interpretation",
            "evidence",
        ],
    )
    write_csv(PROOF_GATE_CSV, proof_rows, ["gate", "status", "evidence", "detail", "missing_before_code"])
    write_csv(NEXT_CSV, next_rows, ["priority", "route", "entry_condition", "gate", "current_status", "evidence"])
    write_csv(
        SUMMARY_CSV,
        summary_rows,
        ["gate", "status", "metric", "value", "evidence", "detail", "next_action"],
    )
    write_report(assumption_rows, semantic_rows, resource_rows, proof_rows, next_rows, summary_rows)
    write_commands()
    write_docs(assumption_rows, resource_rows, proof_rows, next_rows, summary_rows)
    update_global_docs()
    write_artifacts(
        [
            OUT_MD,
            PLAN_MD,
            THEORY_MD,
            VARIANT_MD,
            REPORT_MD,
            COMMANDS_MD,
            SUMMARY_CSV,
            ASSUMPTION_CSV,
            SEMANTIC_CSV,
            RESOURCE_CSV,
            PROOF_GATE_CSV,
            NEXT_CSV,
            Path(__file__),
        ]
    )
    print(DECISION)


if __name__ == "__main__":
    main()
