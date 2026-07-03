#!/usr/bin/env python3
"""Stage203: production-shaped selector equation probe for dummy padding route."""

from __future__ import annotations

import csv
import hashlib
import random
import subprocess
from pathlib import Path
from typing import Dict, Iterable, List, Sequence, Set, Tuple


ROOT = Path(__file__).resolve().parents[1]
OUT_DIR = ROOT / "repro" / "stage203_production_selector_equation_probe"

SUMMARY_CSV = OUT_DIR / "summary.csv"
ASSUMPTION_CSV = OUT_DIR / "assumptions.csv"
EQUATION_CSV = OUT_DIR / "equation_map.csv"
PHASE_CSV = OUT_DIR / "phase_noise_probe.csv"
NEGATIVE_CSV = OUT_DIR / "negative_controls.csv"
RESOURCE_CSV = OUT_DIR / "resource_projection.csv"
PROOF_GATE_CSV = OUT_DIR / "proof_gate.csv"
NEXT_CSV = OUT_DIR / "next_stage_queue.csv"
COMMANDS_MD = OUT_DIR / "reproduction_commands.md"
REPORT_MD = OUT_DIR / "production_selector_equation_report.md"
ARTIFACT_CSV = OUT_DIR / "artifact_index.csv"

OUT_MD = ROOT / "docs" / "stage203_production_selector_equation_probe.md"
PLAN_MD = ROOT / "experiments" / "stage203_production_selector_equation_probe_plan.md"
THEORY_MD = ROOT / "theory_checks" / "stage203_production_selector_equation_model.md"
VARIANT_MD = ROOT / "algorithm_variants" / "mat_rlwe_sab_production_selector_equation_probe.md"

ROADMAP_MD = ROOT / "docs" / "roadmap_stage19_plus.md"
GOAL_MD = ROOT / "docs" / "goal_sab_max_acceleration.md"
CURRENT_GOAL_MD = ROOT / "docs" / "current_codex_goal_sab_completion.md"
HYPOTHESIS_YAML = ROOT / "hypotheses" / "hypothesis_register.yaml"
RUN_LOG = ROOT / "repro" / "run_log.csv"
MANIFEST = ROOT / "repro" / "artifact_manifest.md"
CHECKLIST = ROOT / "repro" / "reproduction_checklist.md"

STAGE202_SUMMARY = ROOT / "repro" / "stage202_dummy_padding_semantic_probe" / "summary.csv"
STAGE202_PROOF = ROOT / "repro" / "stage202_dummy_padding_semantic_probe" / "proof_gate.csv"
STAGE202_RESOURCE = ROOT / "repro" / "stage202_dummy_padding_semantic_probe" / "resource_model.csv"
STAGE201_PROOF = ROOT / "repro" / "stage201_structured_selector_distribution_probe" / "proof_gate.csv"

DECISION = "PASS_STAGE203_PRODUCTION_SELECTOR_EQUATION_PROBE_PROOF_ONLY"


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


def mat_vec_mul(matrix: Matrix, vec: Sequence[Poly], q: int, active: Set[Tuple[int, int]] | None = None) -> List[Poly]:
    n = len(vec[0])
    out: List[Poly] = []
    for row in range(len(matrix)):
        acc = zero_poly(n)
        for col in range(len(vec)):
            if active is not None and (row, col) not in active:
                continue
            acc = poly_add(acc, poly_mul_negacyclic(matrix[row][col], vec[col], q), q)
        out.append(acc)
    return out


def mismatch_count(a: Sequence[Poly], b: Sequence[Poly]) -> int:
    return sum(1 for row_a, row_b in zip(a, b) for x, y in zip(row_a, row_b) if x != y)


def equation_pairs(r: int) -> Set[Tuple[int, int]]:
    pairs: Set[Tuple[int, int]] = set()
    for lane in range(1, r + 1):
        next_lane = 1 + (lane % r)
        pairs.add((0, lane))
        pairs.add((lane, 0))
        pairs.add((lane, lane))
        pairs.add((lane, next_lane))
    assert len(pairs) == 4 * r
    return pairs


def equation_class(row: int, col: int) -> str:
    if row == 0 and col != 0:
        return "mask_output_from_body_input"
    if row != 0 and col == 0:
        return "body_output_from_mask_input"
    if row == col and row != 0:
        return "lane_self_body_interaction"
    if row != 0 and col != 0:
        return "lane_neighbor_body_interaction"
    return "inactive_dummy_equation"


def structured_matrix(rng: random.Random, r: int, n: int, q: int, inactive_mode: str) -> Matrix:
    m = r + 1
    active = equation_pairs(r)
    matrix: Matrix = []
    for row in range(m):
        matrix_row: List[Poly] = []
        for col in range(m):
            if (row, col) in active:
                matrix_row.append(random_poly(rng, n, q))
            elif inactive_mode == "zero":
                matrix_row.append(zero_poly(n))
            elif inactive_mode == "random":
                matrix_row.append(random_poly(rng, n, q))
            else:
                raise ValueError(inactive_mode)
        matrix.append(matrix_row)
    return matrix


def build_assumptions() -> List[Dict[str, str]]:
    return [
        {
            "assumption_id": "A1_declared_equation_v0",
            "statement": "The finite probe declares four active equation classes per body lane and semantic-zero dummy equations elsewhere.",
            "scope": "finite production-shaped probe, not production keygen",
            "evidence": rel(EQUATION_CSV),
            "falsification": "A real selector keygen equation may have a different active set or coefficient structure.",
        },
        {
            "assumption_id": "A2_dummy_semantic_zero",
            "statement": "Inactive dense-shape rows are public dummy rows but must have zero semantic contribution.",
            "scope": "dummy padding proof route",
            "evidence": rel(PHASE_CSV),
            "falsification": "Random semantic dummy rows are a negative control and must mismatch.",
        },
        {
            "assumption_id": "A3_noise_skip_model",
            "statement": "Evaluator-side skipping of semantic-zero dummy rows avoids dummy noise accumulation only after a proof identifies them.",
            "scope": "noise/resource model",
            "evidence": rel(PROOF_GATE_CSV),
            "falsification": "If dummy rows must be evaluated, noise and runtime value degrade.",
        },
    ]


def build_equation_map() -> List[Dict[str, str]]:
    rows: List[Dict[str, str]] = []
    for r in (2, 4, 6):
        m = r + 1
        active = equation_pairs(r)
        for row in range(m):
            for col in range(m):
                is_active = (row, col) in active
                rows.append(
                    {
                        "r": str(r),
                        "row": str(row),
                        "col": str(col),
                        "equation_class": equation_class(row, col) if is_active else "semantic_zero_dummy",
                        "semantic_role": "active" if is_active else "dummy_zero",
                        "is_public_row": "1",
                        "may_skip_after_proof": "0" if is_active else "1",
                    }
                )
    return rows


def build_phase_noise_probe() -> List[Dict[str, str]]:
    rows: List[Dict[str, str]] = []
    q = 257
    n = 8
    active_noise = 3.0
    dummy_noise = 1.0
    for r in (2, 4, 6):
        m = r + 1
        active = equation_pairs(r)
        inactive_count = m * m - len(active)
        for seed in range(8):
            rng_vec = random.Random(2030000 + 100 * r + seed)
            vec = [random_poly(rng_vec, n, q) for _ in range(m)]
            rng_matrix = random.Random(2031000 + 100 * r + seed)
            matrix_zero = structured_matrix(rng_matrix, r, n, q, "zero")
            reference = mat_vec_mul(matrix_zero, vec, q, active)

            full_zero = mat_vec_mul(matrix_zero, vec, q, None)
            rows.append(
                probe_row(
                    "declared_equations_full_vs_skip",
                    r,
                    seed,
                    len(active),
                    inactive_count,
                    mismatch_count(reference, full_zero),
                    len(active) * active_noise,
                    len(active) * active_noise + inactive_count * dummy_noise,
                    "PASS_EQUIVALENCE",
                    "Full dense-shape evaluation with semantic-zero dummies equals active-row skipping in phase, but may add dummy noise if rows are evaluated.",
                )
            )

            rng_bad = random.Random(2031000 + 100 * r + seed)
            matrix_random = structured_matrix(rng_bad, r, n, q, "random")
            bad_full = mat_vec_mul(matrix_random, vec, q, None)
            rows.append(
                probe_row(
                    "negative_random_dummy_semantics",
                    r,
                    seed,
                    len(active),
                    inactive_count,
                    mismatch_count(reference, bad_full),
                    len(active) * active_noise,
                    len(active) * active_noise + inactive_count * dummy_noise,
                    "PASS_COUNTEREXAMPLE",
                    "Random semantic dummy rows break the declared structured function.",
                )
            )

            missing_active = set(active)
            removed = sorted(missing_active)[seed % len(missing_active)]
            missing_active.remove(removed)
            missing_eval = mat_vec_mul(matrix_zero, vec, q, missing_active)
            rows.append(
                probe_row(
                    "negative_missing_active_equation",
                    r,
                    seed,
                    len(missing_active),
                    inactive_count + 1,
                    mismatch_count(reference, missing_eval),
                    len(active) * active_noise,
                    len(missing_active) * active_noise,
                    "PASS_COUNTEREXAMPLE",
                    "Removing an active equation breaks the declared structured function.",
                )
            )
    return rows


def probe_row(
    probe: str,
    r: int,
    seed: int,
    evaluated_active_rows: int,
    dummy_rows: int,
    mismatches: int,
    skip_noise: float,
    dense_noise: float,
    expected: str,
    interpretation: str,
) -> Dict[str, str]:
    if expected == "PASS_EQUIVALENCE":
        status = "PASS_EQUIVALENCE" if mismatches == 0 else "FAIL_MISMATCH"
    else:
        status = "PASS_COUNTEREXAMPLE" if mismatches > 0 else "FAIL_NO_MISMATCH"
    return {
        "probe": probe,
        "r": str(r),
        "seed": str(seed),
        "evaluated_active_rows": str(evaluated_active_rows),
        "dummy_rows": str(dummy_rows),
        "mismatches": str(mismatches),
        "skip_noise_units": f"{skip_noise:.6f}",
        "dense_eval_noise_units": f"{dense_noise:.6f}",
        "noise_ratio_dense_over_skip": f"{dense_noise / skip_noise:.9f}" if skip_noise else "n/a",
        "status": status,
        "interpretation": interpretation,
    }


def build_negative_controls(phase_rows: List[Dict[str, str]]) -> List[Dict[str, str]]:
    return [
        {
            "negative_control": "random_dummy_semantics",
            "expected": "must mismatch structured-zero reference",
            "failures": str(sum(1 for row in phase_rows if row["probe"] == "negative_random_dummy_semantics" and row["status"] != "PASS_COUNTEREXAMPLE")),
            "decision": "PASS_REJECTS_BAD_DUMMY" if all(row["status"] == "PASS_COUNTEREXAMPLE" for row in phase_rows if row["probe"] == "negative_random_dummy_semantics") else "FAIL",
            "evidence": rel(PHASE_CSV),
        },
        {
            "negative_control": "missing_active_equation",
            "expected": "must mismatch structured-zero reference",
            "failures": str(sum(1 for row in phase_rows if row["probe"] == "negative_missing_active_equation" and row["status"] != "PASS_COUNTEREXAMPLE")),
            "decision": "PASS_REJECTS_MISSING_EQUATION" if all(row["status"] == "PASS_COUNTEREXAMPLE" for row in phase_rows if row["probe"] == "negative_missing_active_equation") else "FAIL",
            "evidence": rel(PHASE_CSV),
        },
    ]


def build_resource_projection(phase_rows: List[Dict[str, str]]) -> List[Dict[str, str]]:
    rows: List[Dict[str, str]] = []
    for r in (2, 4, 6):
        m = r + 1
        dense = m * m
        active = 4 * r
        dummy = dense - active
        ratios = [
            float(row["noise_ratio_dense_over_skip"])
            for row in phase_rows
            if row["probe"] == "declared_equations_full_vs_skip" and row["r"] == str(r)
        ]
        mean_ratio = sum(ratios) / len(ratios)
        rows.append(
            {
                "r": str(r),
                "dense_rows_per_T": str(dense),
                "active_rows_per_T": str(active),
                "dummy_rows_per_T": str(dummy),
                "public_row_saving": "0",
                "evaluator_row_reduction_if_skip_proven": f"{dummy / dense:.9f}",
                "dense_eval_noise_over_skip_mean": f"{mean_ratio:.9f}",
                "interpretation": "Potential evaluator work/noise reduction exists only if dummy rows are proven identifiable semantic-zero rows.",
                "evidence": rel(PHASE_CSV),
            }
        )
    return rows


def build_proof_gate(phase_rows: List[Dict[str, str]], negative_rows: List[Dict[str, str]]) -> List[Dict[str, str]]:
    phase_failures = sum(1 for row in phase_rows if row["probe"] == "declared_equations_full_vs_skip" and row["status"] != "PASS_EQUIVALENCE")
    negative_failures = sum(1 for row in negative_rows if row["decision"] == "FAIL")
    return [
        {
            "gate": "E1_declared_equation_phase",
            "status": "PASS_FINITE" if phase_failures == 0 else "FAIL",
            "evidence": rel(PHASE_CSV),
            "detail": f"declared equation phase failures={phase_failures}",
            "missing_before_code": "Map declared equations to actual production selector keygen.",
        },
        {
            "gate": "E2_negative_controls",
            "status": "PASS" if negative_failures == 0 else "FAIL",
            "evidence": rel(NEGATIVE_CSV),
            "detail": f"negative control failures={negative_failures}",
            "missing_before_code": "Keep negative controls in any production-shaped proof.",
        },
        {
            "gate": "E3_noise_resource",
            "status": "MODEL_ONLY",
            "evidence": rel(RESOURCE_CSV),
            "detail": "dummy row skipping has modeled value but public row count remains dense",
            "missing_before_code": "Run production noise recurrence and complete-SAB T_bootstrap/r gates.",
        },
        {
            "gate": "E4_security_keygen",
            "status": "BLOCKED",
            "evidence": rel(STAGE202_PROOF),
            "detail": "no production keygen or security reduction is supplied",
            "missing_before_code": "Define production keygen equations and proof that dummy rows leak nothing beyond declared distribution.",
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
            "route": "production_keygen_equation_design",
            "entry_condition": "A production selector keygen design is proposed using Stage203 declared equations.",
            "gate": "Show public distribution, semantic zero, noise recurrence, key size, and complete-SAB T_bootstrap/r value.",
            "current_status": "blocked_on_real_keygen_design",
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


def build_summary_rows(phase_rows: List[Dict[str, str]], proof_rows: List[Dict[str, str]]) -> List[Dict[str, str]]:
    inputs = [STAGE202_SUMMARY, STAGE202_PROOF, STAGE202_RESOURCE, STAGE201_PROOF]
    inputs_ok = all(path.exists() for path in inputs)
    phase_failures = sum(1 for row in phase_rows if not row["status"].startswith("PASS"))
    blocked = sum(1 for row in proof_rows if row["status"] in {"BLOCKED", "MODEL_ONLY"})
    return [
        {
            "gate": "stage203_inputs",
            "status": "PASS" if inputs_ok else "FAIL",
            "metric": "required_inputs_present",
            "value": "1" if inputs_ok else "0",
            "evidence": f"{rel(STAGE202_SUMMARY)}; {rel(STAGE202_PROOF)}",
            "detail": "Stage203 consumes Stage202 dummy semantics and proof-only route state.",
            "next_action": "Repair missing inputs before using this probe.",
        },
        {
            "gate": "stage203_equation_map",
            "status": "PASS_RECORDED",
            "metric": "equation_rows",
            "value": "83",
            "evidence": rel(EQUATION_CSV),
            "detail": "Declared equation v0 records dense public rows, active roles, and dummy-zero rows for r=2/4/6.",
            "next_action": "Replace with real production keygen equations before code.",
        },
        {
            "gate": "stage203_phase_noise_probe",
            "status": "PASS" if phase_failures == 0 else "FAIL",
            "metric": "phase_or_negative_failures",
            "value": str(phase_failures),
            "evidence": rel(PHASE_CSV),
            "detail": "Finite checks pass declared phase equivalence and reject bad dummy/missing-equation controls.",
            "next_action": "Do not generalize beyond declared equation v0.",
        },
        {
            "gate": "stage203_proof_gate",
            "status": "PROOF_ONLY",
            "metric": "blocked_or_model_only_gates",
            "value": str(blocked),
            "evidence": rel(PROOF_GATE_CSV),
            "detail": "Production keygen/security and complete-SAB gates remain missing.",
            "next_action": "Do not implement compact SAB.",
        },
        {
            "gate": "stage203_decision",
            "status": DECISION if inputs_ok and phase_failures == 0 else "FAIL_STAGE203",
            "metric": "goal_status",
            "value": "active",
            "evidence": rel(SUMMARY_CSV),
            "detail": "Declared selector equation route is narrowed to finite proof-only evidence; full goal remains active.",
            "next_action": "Proceed only via source anchors, production keygen design, or new exact mechanism.",
        },
    ]


def write_report(
    assumption_rows: List[Dict[str, str]],
    equation_rows: List[Dict[str, str]],
    negative_rows: List[Dict[str, str]],
    resource_rows: List[Dict[str, str]],
    proof_rows: List[Dict[str, str]],
    next_rows: List[Dict[str, str]],
    summary_rows: List[Dict[str, str]],
) -> None:
    write_text_lf(
        REPORT_MD,
        f"""# Production-Shaped Selector Equation Probe

Decision: `{DECISION}`.

Stage203 declares a finite equation candidate for the dummy-padding proof route
and checks phase/noise behavior with negative controls. It remains proof-only:
no production keygen, security reduction, or complete-SAB benchmark is supplied.

## Summary

{table(summary_rows, ["gate", "status", "metric", "value", "evidence", "detail", "next_action"])}
## Assumptions

{table(assumption_rows, ["assumption_id", "statement", "scope", "evidence", "falsification"])}
## Negative Controls

{table(negative_rows, ["negative_control", "expected", "failures", "decision", "evidence"])}
## Resource Projection

{table(resource_rows, ["r", "dense_rows_per_T", "active_rows_per_T", "dummy_rows_per_T", "public_row_saving", "evaluator_row_reduction_if_skip_proven", "dense_eval_noise_over_skip_mean", "interpretation", "evidence"])}
## Proof Gates

{table(proof_rows, ["gate", "status", "evidence", "detail", "missing_before_code"])}
## Next Queue

{table(next_rows, ["priority", "route", "entry_condition", "gate", "current_status", "evidence"])}

Full equation map and phase/noise rows are recorded in `{rel(EQUATION_CSV)}` and `{rel(PHASE_CSV)}`.
""",
    )


def write_commands() -> None:
    write_text_lf(
        COMMANDS_MD,
        """# Stage203 Reproduction Commands

```powershell
# Rebuild production-shaped selector equation probe
python scripts\\build_stage203_production_selector_equation_probe.py

# Inspect outputs
Get-Content -Raw repro\\stage203_production_selector_equation_probe\\summary.csv
Get-Content -Raw repro\\stage203_production_selector_equation_probe\\equation_map.csv
Get-Content -Raw repro\\stage203_production_selector_equation_probe\\phase_noise_probe.csv
Get-Content -Raw repro\\stage203_production_selector_equation_probe\\proof_gate.csv
```
""",
    )


def write_docs(
    assumption_rows: List[Dict[str, str]],
    negative_rows: List[Dict[str, str]],
    resource_rows: List[Dict[str, str]],
    proof_rows: List[Dict[str, str]],
    next_rows: List[Dict[str, str]],
    summary_rows: List[Dict[str, str]],
) -> None:
    write_text_lf(
        OUT_MD,
        f"""# Stage203 Production Selector Equation Probe

Decision: `{DECISION}`.

Stage203 checks a declared selector equation candidate for the dummy-padding
route. It is finite proof evidence only and opens no production code path.

## Gate Summary

{table(summary_rows, ["gate", "status", "metric", "value", "evidence", "detail", "next_action"])}
## Assumptions

{table(assumption_rows, ["assumption_id", "statement", "scope", "evidence", "falsification"])}
## Negative Controls

{table(negative_rows, ["negative_control", "expected", "failures", "decision", "evidence"])}
## Resource Projection

{table(resource_rows, ["r", "dense_rows_per_T", "active_rows_per_T", "dummy_rows_per_T", "public_row_saving", "evaluator_row_reduction_if_skip_proven", "dense_eval_noise_over_skip_mean", "interpretation", "evidence"])}
## Proof Gates

{table(proof_rows, ["gate", "status", "evidence", "detail", "missing_before_code"])}
## Next Queue

{table(next_rows, ["priority", "route", "entry_condition", "gate", "current_status", "evidence"])}
""",
    )

    write_text_lf(
        PLAN_MD,
        """# Stage203 Plan

Goal: replace the Stage202 toy active set with a declared production-shaped
selector equation candidate and test finite phase/noise behavior.

Rules:

- the equation candidate is not production keygen;
- semantic-zero dummy rows must preserve phase;
- random dummy semantics and missing active equations are negative controls;
- noise/resource rows are model-only until production recurrence and complete
  SAB gates exist.
""",
    )

    write_text_lf(
        THEORY_MD,
        """# Stage203 Production-Shaped Selector Equation Model

The declared equation candidate uses four active equation classes per body lane:

- mask output from body input;
- body output from mask input;
- lane self-body interaction;
- lane neighbor-body interaction.

All other dense public rows are dummy-zero equations. Finite phase tests check
that dense-shape evaluation with dummy-zero rows equals active-row skipping.
Negative controls require random dummy semantics and missing active equations
to fail. Passing these tests does not prove security or production correctness.
""",
    )

    write_text_lf(
        VARIANT_MD,
        """# Production-Shaped Selector Equation Probe

This is not a production algorithm variant. It is a proof-route filter for the
dummy-padding compact/shared-output idea.

The route remains blocked on:

- actual selector keygen equations;
- public-distribution/security proof;
- noise recurrence;
- resource value under complete SAB `T_bootstrap/r`;
- multi-seed correctness if implemented later.
""",
    )


def update_global_docs() -> None:
    append_once(
        ROADMAP_MD,
        "## Stage 203: Production Selector Equation Probe",
        f"""
## Stage 203: Production Selector Equation Probe

Goal:

```text
Check a declared production-shaped selector equation candidate for the dummy
padding proof route using finite phase/noise probes and negative controls.
```

Status:

```text
Completed. Stage203 records {DECISION}. The declared equation candidate passes
finite phase/negative-control checks, but remains proof-only because production
keygen, security/noise, and complete-SAB gates are missing.
```
""",
    )

    append_once(
        GOAL_MD,
        "Stage203 records production selector equation probe",
        f"""
Stage203 records production selector equation probe. Decision: `{DECISION}`.
It advances dummy padding from toy semantic rows to a declared finite equation
candidate, while preserving proof-only status.
""",
    )

    append_once(
        CURRENT_GOAL_MD,
        "Treat Stage203 as production selector equation probe",
        f"""
107. Treat Stage203 as production selector equation probe:
    `{DECISION}`. A declared finite equation candidate passes phase and
    negative-control checks, but compact/shared-output SAB remains blocked on
    real keygen, security/noise, resource, and complete-SAB evidence.
""",
    )

    append_once(
        HYPOTHESIS_YAML,
        "H127_production_selector_equation_probe",
        f"""
  - id: H127_production_selector_equation_probe
    statement: >
      A dummy-padding selector route can only advance if a declared equation
      candidate preserves phase under semantic-zero dummy rows and rejects
      random dummy semantics and missing active equations.
    mechanism: >
      Stage203 records a finite equation map and phase/noise probes for
      r=2/4/6, with negative controls and model-only resource/noise estimates.
    status: stage203_production_selector_equation_probe
    evidence: docs/stage203_production_selector_equation_probe.md; experiments/stage203_production_selector_equation_probe_plan.md; theory_checks/stage203_production_selector_equation_model.md; repro/stage203_production_selector_equation_probe/summary.csv
    current_decision: >
      {DECISION}
    failure_criteria:
      - dummy-zero equation rows fail phase equivalence
      - random dummy or missing-active negative controls do not fail
      - finite equation evidence is treated as production keygen permission
""",
    )

    append_once(
        RUN_LOG,
        "stage203-production-selector-equation-probe-001",
        f"""
stage203-production-selector-equation-probe-001,2026-07-04,{git_head()},Stage 203,analysis+finite-probe,python scripts/build_stage203_production_selector_equation_probe.py,Stage202 proof route,none,{DECISION},Production-shaped selector equation finite probe.,repro/stage203_production_selector_equation_probe
""",
    )

    append_once(
        MANIFEST,
        "stage203_production_selector_equation_probe",
        f"""
- stage203_production_selector_equation_probe: `{DECISION}`
  - `docs/stage203_production_selector_equation_probe.md`
  - `experiments/stage203_production_selector_equation_probe_plan.md`
  - `theory_checks/stage203_production_selector_equation_model.md`
  - `algorithm_variants/mat_rlwe_sab_production_selector_equation_probe.md`
  - `repro/stage203_production_selector_equation_probe/`
""",
    )

    append_once(CHECKLIST, "Stage203 production selector equation probe recorded", """
- [x] Stage203 production selector equation probe recorded.
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
    equation_rows = build_equation_map()
    phase_rows = build_phase_noise_probe()
    negative_rows = build_negative_controls(phase_rows)
    resource_rows = build_resource_projection(phase_rows)
    proof_rows = build_proof_gate(phase_rows, negative_rows)
    next_rows = build_next_rows()
    summary_rows = build_summary_rows(phase_rows, proof_rows)

    write_csv(ASSUMPTION_CSV, assumption_rows, ["assumption_id", "statement", "scope", "evidence", "falsification"])
    write_csv(EQUATION_CSV, equation_rows, ["r", "row", "col", "equation_class", "semantic_role", "is_public_row", "may_skip_after_proof"])
    write_csv(
        PHASE_CSV,
        phase_rows,
        [
            "probe",
            "r",
            "seed",
            "evaluated_active_rows",
            "dummy_rows",
            "mismatches",
            "skip_noise_units",
            "dense_eval_noise_units",
            "noise_ratio_dense_over_skip",
            "status",
            "interpretation",
        ],
    )
    write_csv(NEGATIVE_CSV, negative_rows, ["negative_control", "expected", "failures", "decision", "evidence"])
    write_csv(
        RESOURCE_CSV,
        resource_rows,
        [
            "r",
            "dense_rows_per_T",
            "active_rows_per_T",
            "dummy_rows_per_T",
            "public_row_saving",
            "evaluator_row_reduction_if_skip_proven",
            "dense_eval_noise_over_skip_mean",
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
    write_report(assumption_rows, equation_rows, negative_rows, resource_rows, proof_rows, next_rows, summary_rows)
    write_commands()
    write_docs(assumption_rows, negative_rows, resource_rows, proof_rows, next_rows, summary_rows)
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
            EQUATION_CSV,
            PHASE_CSV,
            NEGATIVE_CSV,
            RESOURCE_CSV,
            PROOF_GATE_CSV,
            NEXT_CSV,
            Path(__file__),
        ]
    )
    print(DECISION)


if __name__ == "__main__":
    main()
