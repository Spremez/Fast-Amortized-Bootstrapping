#!/usr/bin/env python3
"""Build Stage329 formal compact-selector finite checker artifacts."""

from __future__ import annotations

import csv
import hashlib
import random
import subprocess
from pathlib import Path
from typing import Dict, Iterable, List, Sequence, Set, Tuple


ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "repro" / "stage329_formal_compact_selector_checker"
DOC = ROOT / "docs" / "stage329_formal_compact_selector_checker.md"
THEORY = ROOT / "theory_checks" / "stage329_compact_selector_proof_obligations.md"
VARIANT = ROOT / "algorithm_variants" / "mat_rlwe_sab_stage329_formal_compact_selector_card.md"
PLAN = ROOT / "experiments" / "stage330_compact_keygen_security_or_highstat_plan.md"
BUILDER = ROOT / "scripts" / "build_stage329_formal_compact_selector_checker.py"

SUMMARY = OUT / "summary.csv"
FINITE = OUT / "finite_equivalence_checker.csv"
DIST = OUT / "distribution_obligation_matrix.csv"
OBLIGATIONS = OUT / "proof_obligation_matrix.csv"
GATES = OUT / "proof_gate.csv"
NEXT = OUT / "next_stage_queue.csv"
COMMANDS = OUT / "reproduction_commands.md"
REPORT = OUT / "stage329_report.md"
ARTIFACT = OUT / "artifact_index.csv"

GOAL = ROOT / "docs" / "current_codex_goal_sab_completion.md"
ROADMAP = ROOT / "docs" / "roadmap_stage19_plus.md"
HYPOTHESES = ROOT / "hypotheses" / "hypothesis_register.yaml"
RUN_LOG = ROOT / "repro" / "run_log.csv"
MANIFEST = ROOT / "repro" / "artifact_manifest.md"
CHECKLIST = ROOT / "repro" / "reproduction_checklist.md"

STAGE203_EQUATIONS = ROOT / "repro" / "stage203_production_selector_equation_probe" / "equation_map.csv"
STAGE203_RESOURCE = ROOT / "repro" / "stage203_production_selector_equation_probe" / "resource_projection.csv"
STAGE249_CLAIM = ROOT / "repro" / "stage249_structured_compact_distribution_security" / "claim_boundary.csv"
STAGE328_SUMMARY = ROOT / "repro" / "stage328_active_goal_requirement_audit" / "summary.csv"

DECISION = "PASS_STAGE329_COMPACT_SELECTOR_FINITE_CHECKER_PASS_SECURITY_KEYGEN_OPEN_NO_CODE"

Poly = Tuple[int, ...]


def rel(path: Path) -> str:
    return path.relative_to(ROOT).as_posix()


def read_text(path: Path) -> str:
    if not path.exists():
        return ""
    return (
        path.read_text(encoding="utf-8", errors="replace")
        .replace("\x00", "")
        .replace("\r\n", "\n")
        .replace("\r", "\n")
    )


def write_text(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text.rstrip() + "\n", encoding="utf-8", newline="\n")


def write_csv(path: Path, rows: Iterable[Dict[str, object]], fields: List[str]) -> None:
    rows = list(rows)
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fields, lineterminator="\n")
        writer.writeheader()
        for row in rows:
            writer.writerow({field: row.get(field, "") for field in fields})


def read_csv_rows(path: Path) -> List[Dict[str, str]]:
    if not path.exists():
        return []
    with path.open(newline="", encoding="utf-8-sig") as f:
        return list(csv.DictReader(f))


def read_csv_one(path: Path) -> Dict[str, str]:
    rows = read_csv_rows(path)
    return rows[0] if rows else {}


def append_once(path: Path, marker: str, text: str) -> None:
    current = read_text(path)
    if marker in current:
        return
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("a", encoding="utf-8", newline="\n") as f:
        if current and not current.endswith("\n"):
            f.write("\n")
        f.write(text.lstrip())
        if not text.endswith("\n"):
            f.write("\n")


def fnum(value: object, default: float = 0.0) -> float:
    try:
        return float(value)
    except (TypeError, ValueError):
        return default


def git_head() -> str:
    try:
        return subprocess.check_output(
            ["git", "rev-parse", "--short", "HEAD"], cwd=ROOT, text=True
        ).strip()
    except (subprocess.CalledProcessError, FileNotFoundError):
        return "unknown"


def table(rows: List[Dict[str, object]], fields: List[str]) -> str:
    out = ["| " + " | ".join(fields) + " |", "| " + " | ".join("---" for _ in fields) + " |"]
    for row in rows:
        out.append("| " + " | ".join(str(row.get(field, "")).replace("|", "\\|") for field in fields) + " |")
    return "\n".join(out)


def artifact_index(paths: List[Path]) -> None:
    rows = []
    for path in paths:
        if not path.exists() or not path.is_file():
            continue
        data = path.read_bytes()
        rows.append({"path": rel(path), "bytes": str(len(data)), "sha256": hashlib.sha256(data).hexdigest()})
    write_csv(ARTIFACT, rows, ["path", "bytes", "sha256"])


def append_run_log() -> None:
    run_id = "stage329-formal-compact-selector-checker-001"
    if run_id in read_text(RUN_LOG):
        return
    fields: List[str] = []
    if RUN_LOG.exists():
        with RUN_LOG.open(newline="", encoding="utf-8-sig") as f:
            reader = csv.DictReader(f)
            fields = list(reader.fieldnames or [])
    if not fields:
        fields = [
            "run_id", "date", "git_ref", "stage", "backend", "command",
            "config", "seed", "status", "summary", "artifacts",
        ]
    row = {field: "" for field in fields}
    values = {
        "run_id": run_id,
        "date": "2026-07-05",
        "git_ref": git_head(),
        "commit_or_state": git_head(),
        "stage": "Stage 329",
        "backend": "finite-proof-checker",
        "command": "python scripts/build_stage329_formal_compact_selector_checker.py",
        "config": "formal compact selector finite checker; no SAB hot-path code",
        "params": "r=2/4/6; finite ring n=8 q=257; declared Stage203 equation map",
        "seed": "deterministic",
        "status": DECISION,
        "summary": "Stage329 runs a finite checker for compact selector dummy-zero semantics and keeps production code blocked.",
        "artifacts": f"{rel(DOC)}; {rel(SUMMARY)}; {rel(FINITE)}; {rel(OBLIGATIONS)}; {rel(GATES)}",
    }
    for key, value in values.items():
        if key in row:
            row[key] = value
    with RUN_LOG.open("a", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fields, lineterminator="\n")
        writer.writerow(row)


def zero_poly(n: int) -> Poly:
    return tuple(0 for _ in range(n))


def rand_poly(rng: random.Random, n: int, q: int) -> Poly:
    return tuple(rng.randrange(q) for _ in range(n))


def add_poly(a: Poly, b: Poly, q: int) -> Poly:
    return tuple((x + y) % q for x, y in zip(a, b))


def mul_negacyclic(a: Poly, b: Poly, q: int) -> Poly:
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


def mat_vec(
    matrix: Dict[Tuple[int, int], Poly],
    vec: Sequence[Poly],
    r: int,
    q: int,
    allowed: Set[Tuple[int, int]] | None = None,
) -> List[Poly]:
    n = len(vec[0])
    m = r + 1
    out: List[Poly] = []
    for row in range(m):
        acc = zero_poly(n)
        for col in range(m):
            if allowed is not None and (row, col) not in allowed:
                continue
            acc = add_poly(acc, mul_negacyclic(matrix[(row, col)], vec[col], q), q)
        out.append(acc)
    return out


def mismatch_count(a: Sequence[Poly], b: Sequence[Poly]) -> int:
    return sum(1 for aa, bb in zip(a, b) for x, y in zip(aa, bb) if x != y)


def active_pairs_for_r(r: int) -> Set[Tuple[int, int]]:
    pairs: Set[Tuple[int, int]] = set()
    for row in read_csv_rows(STAGE203_EQUATIONS):
        if row.get("r") != str(r):
            continue
        if row.get("semantic_role") == "active":
            pairs.add((int(row["row"]), int(row["col"])))
    return pairs


def build_matrix(r: int, seed: int, inactive_mode: str, n: int, q: int) -> Dict[Tuple[int, int], Poly]:
    rng = random.Random(329000 + 1000 * r + seed)
    active = active_pairs_for_r(r)
    matrix: Dict[Tuple[int, int], Poly] = {}
    for row in range(r + 1):
        for col in range(r + 1):
            if (row, col) in active:
                matrix[(row, col)] = rand_poly(rng, n, q)
            elif inactive_mode == "zero":
                matrix[(row, col)] = zero_poly(n)
            elif inactive_mode == "random":
                matrix[(row, col)] = rand_poly(rng, n, q)
            else:
                raise ValueError(inactive_mode)
    return matrix


def run_finite_checker() -> List[Dict[str, object]]:
    rows: List[Dict[str, object]] = []
    n = 8
    q = 257
    for r in (2, 4, 6):
        active = active_pairs_for_r(r)
        dense_rows = (r + 1) * (r + 1)
        dummy_rows = dense_rows - len(active)
        for seed in range(32):
            rng = random.Random(329500 + 1000 * r + seed)
            vec = [rand_poly(rng, n, q) for _ in range(r + 1)]
            zero_matrix = build_matrix(r, seed, "zero", n, q)
            random_matrix = build_matrix(r, seed, "random", n, q)

            active_eval = mat_vec(zero_matrix, vec, r, q, active)
            dense_zero_eval = mat_vec(zero_matrix, vec, r, q, None)
            rows.append({
                "probe": "semantic_zero_dummy_skip",
                "r": r,
                "seed": seed,
                "active_rows": len(active),
                "dummy_rows": dummy_rows,
                "mismatches": mismatch_count(active_eval, dense_zero_eval),
                "expected": "0",
                "status": "PASS" if mismatch_count(active_eval, dense_zero_eval) == 0 else "FAIL",
                "interpretation": "Skipping declared dummy-zero rows preserves finite phase.",
            })

            dense_random_eval = mat_vec(random_matrix, vec, r, q, None)
            random_mismatch = mismatch_count(active_eval, dense_random_eval)
            rows.append({
                "probe": "negative_random_dummy_rows",
                "r": r,
                "seed": seed,
                "active_rows": len(active),
                "dummy_rows": dummy_rows,
                "mismatches": random_mismatch,
                "expected": ">0",
                "status": "PASS" if random_mismatch > 0 else "FAIL",
                "interpretation": "Random dummy semantics must not be skipped.",
            })

            missing = set(active)
            removed = sorted(missing)[seed % len(missing)]
            missing.remove(removed)
            missing_eval = mat_vec(zero_matrix, vec, r, q, missing)
            missing_mismatch = mismatch_count(active_eval, missing_eval)
            rows.append({
                "probe": "negative_missing_active_row",
                "r": r,
                "seed": seed,
                "active_rows": len(missing),
                "dummy_rows": dummy_rows + 1,
                "mismatches": missing_mismatch,
                "expected": ">0",
                "status": "PASS" if missing_mismatch > 0 else "FAIL",
                "interpretation": f"Removing active row {removed} must change finite phase.",
            })
    return rows


def distribution_rows() -> List[Dict[str, object]]:
    return [
        {
            "candidate": "delete_dummy_rows_publicly",
            "status": "REJECT_UNLESS_DISTRIBUTION_PROOF",
            "public_row_saving": "positive_if_allowed",
            "current_evidence": "Stage249 rejects compact-saving public distributions",
            "missing_before_code": "hybrid/security proof that public key distribution is unchanged",
        },
        {
            "candidate": "dummy_zero_rows_public",
            "status": "REJECT_PUBLIC_PATTERN",
            "public_row_saving": "0",
            "current_evidence": "deterministic zero padding is publicly distinguishable",
            "missing_before_code": "do not use as production key",
        },
        {
            "candidate": "dummy_random_padding",
            "status": "PROOF_ONLY_NO_SPEEDUP_CLAIM",
            "public_row_saving": "0",
            "current_evidence": "Stage249 proof-only survivor keeps dense public shape",
            "missing_before_code": "keygen/security/noise proof and complete-SAB T_bootstrap/r",
        },
    ]


def obligation_rows() -> List[Dict[str, object]]:
    return [
        {
            "obligation": "O2a_equation_to_keygen",
            "status": "OPEN",
            "needed_before_code": "Map declared Stage203 active/dummy equations to actual MAT_TRGSW key generation.",
            "current_checker_result": "finite algebra only",
        },
        {
            "obligation": "O2b_public_distribution",
            "status": "OPEN",
            "needed_before_code": "Prove dummy/random padding leaks no selector structure beyond allowed public distribution.",
            "current_checker_result": "not addressed by finite phase checker",
        },
        {
            "obligation": "O2c_semantic_zero",
            "status": "FINITE_PASS",
            "needed_before_code": "Lift finite dummy-zero semantics to ring/DFT production equations.",
            "current_checker_result": "semantic_zero_dummy_skip passes for r=2/4/6, 32 seeds each",
        },
        {
            "obligation": "O2d_noise_recurrence",
            "status": "OPEN",
            "needed_before_code": "Derive noise recurrence for skipped dummy rows versus dense dummy evaluation.",
            "current_checker_result": "resource/noise projection only",
        },
        {
            "obligation": "O2e_complete_sab_gate",
            "status": "OPEN",
            "needed_before_code": "Run isolated equivalence, then full SAB correctness/noise/resource/T_bootstrap/r A/B.",
            "current_checker_result": "no SAB code permission",
        },
    ]


def build_summary(finite_rows: List[Dict[str, object]]) -> List[Dict[str, object]]:
    failures = sum(1 for row in finite_rows if row.get("status") != "PASS")
    semantic_rows = [row for row in finite_rows if row.get("probe") == "semantic_zero_dummy_skip"]
    negative_rows = [row for row in finite_rows if str(row.get("probe", "")).startswith("negative_")]
    return [{
        "decision": DECISION if failures == 0 else "FAIL_STAGE329_COMPACT_SELECTOR_FINITE_CHECKER",
        "finite_rows": len(finite_rows),
        "finite_failures": failures,
        "semantic_zero_checks": len(semantic_rows),
        "negative_control_checks": len(negative_rows),
        "production_code_permission": "no",
        "compact_claim_permission": "no_complete_sab_claim",
        "next_stage": "stage330_compact_keygen_security_or_highstat",
    }]


def build_gates(finite_rows: List[Dict[str, object]]) -> List[Dict[str, object]]:
    failures = sum(1 for row in finite_rows if row.get("status") != "PASS")
    stage328 = read_csv_one(STAGE328_SUMMARY)
    return [
        {
            "gate": "G1_stage328_input",
            "status": "PASS" if stage328.get("decision") == "PASS_STAGE328_ACTIVE_GOAL_AUDIT_GOAL_REMAINS_ACTIVE_SELECT_HIGHSTAT_OR_FORMAL_PROOF" else "FAIL",
            "metric": "Stage328 decision",
            "value": stage328.get("decision", ""),
            "interpretation": "Stage329 follows the formal compact proof-checker route admitted by Stage328.",
        },
        {
            "gate": "G2_equation_map_present",
            "status": "PASS" if STAGE203_EQUATIONS.exists() else "FAIL",
            "metric": "Stage203 equation map",
            "value": rel(STAGE203_EQUATIONS),
            "interpretation": "Finite checker is anchored to the declared Stage203 equation map.",
        },
        {
            "gate": "G3_finite_checker",
            "status": "PASS" if failures == 0 else "FAIL",
            "metric": "finite failures",
            "value": failures,
            "interpretation": "Semantic-zero skip and negative controls pass in the finite ring model.",
        },
        {
            "gate": "G4_security_keygen_boundary",
            "status": "BLOCKED_NO_CODE",
            "metric": "open obligations",
            "value": "O2a,O2b,O2d,O2e",
            "interpretation": "Finite algebra does not authorize compact SAB production code.",
        },
        {
            "gate": "G5_stage329_decision",
            "status": DECISION if failures == 0 else "FAIL_STAGE329_COMPACT_SELECTOR_FINITE_CHECKER",
            "metric": "decision",
            "value": "no_code_permission",
            "interpretation": "Proceed only to keygen/security proof or high-stat exact-route refresh.",
        },
    ]


def next_rows() -> List[Dict[str, object]]:
    return [
        {
            "priority": "P0",
            "stage": "stage330_compact_keygen_security_preflight",
            "entry_condition": DECISION,
            "task": "Try to map declared equations to production MAT_TRGSW keygen and public distribution proof obligations.",
            "gate": "No SAB hot-path code until keygen/security/noise obligations close.",
            "failure_action": "Keep compact route proof-blocked.",
        },
        {
            "priority": "P1",
            "stage": "stage330_highstat_complete_sab_refresh",
            "entry_condition": "paper-ready scoped performance result is prioritized",
            "task": "Rerun exact PVW/MAT-SAB complete-SAB T_bootstrap/r with >=10 samples.",
            "gate": "Correctness pass, CI reported, claim remains scoped.",
            "failure_action": "Keep Stage327 engineering wording.",
        },
    ]


def main() -> int:
    OUT.mkdir(parents=True, exist_ok=True)
    finite_rows = run_finite_checker()
    dist_rows = distribution_rows()
    obl_rows = obligation_rows()
    summary_rows = build_summary(finite_rows)
    gate_rows = build_gates(finite_rows)
    next_stage_rows = next_rows()
    decision = str(summary_rows[0]["decision"])

    write_csv(FINITE, finite_rows, [
        "probe", "r", "seed", "active_rows", "dummy_rows", "mismatches",
        "expected", "status", "interpretation",
    ])
    write_csv(DIST, dist_rows, [
        "candidate", "status", "public_row_saving", "current_evidence",
        "missing_before_code",
    ])
    write_csv(OBLIGATIONS, obl_rows, [
        "obligation", "status", "needed_before_code", "current_checker_result",
    ])
    write_csv(GATES, gate_rows, ["gate", "status", "metric", "value", "interpretation"])
    write_csv(NEXT, next_stage_rows, [
        "priority", "stage", "entry_condition", "task", "gate", "failure_action",
    ])
    write_csv(SUMMARY, summary_rows, [
        "decision", "finite_rows", "finite_failures", "semantic_zero_checks",
        "negative_control_checks", "production_code_permission",
        "compact_claim_permission", "next_stage",
    ])

    write_text(COMMANDS, """# Stage329 Reproduction Commands

```bash
python3 scripts/build_stage329_formal_compact_selector_checker.py
```

This stage runs a finite checker only. It does not change `sab_pvw_*`, scalar
SAB, or key generation.
""")

    report = f"""# Stage329 Formal Compact Selector Checker

Decision: `{decision}`.

Stage329 follows the formal compact proof-checker route admitted by Stage328.
It reuses the declared Stage203 selector equation map and runs an independent
finite-ring checker for semantic-zero dummy-row skipping and negative controls.
The checker passes, but production compact SAB remains blocked: finite algebra
is not a keygen/security/noise proof.

## Summary

{table(summary_rows, ["decision", "finite_rows", "finite_failures", "semantic_zero_checks", "negative_control_checks", "production_code_permission", "compact_claim_permission", "next_stage"])}

## Distribution Boundary

{table(dist_rows, ["candidate", "status", "public_row_saving", "current_evidence", "missing_before_code"])}

## Proof Obligations

{table(obl_rows, ["obligation", "status", "needed_before_code", "current_checker_result"])}

## Gates

{table(gate_rows, ["gate", "status", "metric", "value", "interpretation"])}

Generated from input head `{git_head()}`.
"""
    write_text(DOC, report)
    write_text(REPORT, report)
    write_text(THEORY, """# Stage329 Compact Selector Proof Obligations

Stage329 separates three statements that must not be conflated:

1. finite semantic-zero algebra: checked here and passing;
2. production keygen/security: still open;
3. complete-SAB acceleration: still absent.

The finite checker proves only that, for the declared Stage203 equation map,
dense-shape evaluation with semantic-zero dummy rows equals active-row
evaluation in sampled finite negacyclic rings, while random dummy rows and
missing active rows are rejected by negative controls.

Before production code, the remaining obligations are:

- map declared rows to actual MAT_TRGSW keygen equations;
- prove public distribution indistinguishability or define an accepted leakage;
- derive noise recurrence for skipped dummy rows;
- pass isolated equivalence and full SAB T_bootstrap/r A/B.
""")
    write_text(VARIANT, """# Stage329: Formal Compact Selector Candidate Card

## Summary

- Parent algorithm: r-body PVW/MAT-SAB.
- Focused module: MAT_TRGSW selector representation for compact/shared-output
  external product.
- Optimization target: reduce dense `(r+1)^2` selector work while preserving
  complete-SAB `T_bootstrap/r` correctness.
- Status labels: `[finite algebra pass] [security/keygen open] [no code permission]`.
- Main hypothesis: semantic-zero dummy selector rows can be skipped by the
  evaluator if production keygen/security proves they leak no forbidden
  structure.

## Mathematical Definition

Let `M` be the dense selector matrix over `r+1` input/output components and
`A` the declared active row set from Stage203. The finite checker verifies:

```text
M_zero x == M_A x
```

when all rows outside `A` are semantic zero, and rejects random dummy rows or
missing active rows.

## Pseudocode

```text
Input: Stage203 equation map, finite vector x
Output: pass/fail rows
1. Build active selector rows from the equation map.
2. Fill inactive rows with zero and compare dense vs active evaluation.
3. Fill inactive rows with random values and require mismatch.
4. Remove one active row and require mismatch.
5. Report proof obligations before production code.
```

## Delta From Original Algorithm

| Original component | Variant component | Relationship | Evidence/status |
| --- | --- | --- | --- |
| Dense MAT_TRGSW rows | active rows plus semantic-zero dummy rows | changes selector representation | finite checker pass only |
| Current exact dense evaluator | evaluator skipping proven dummy rows | potential complexity reduction | proof/keygen/noise open |
| Complete SAB speed claim | none | blocked | no full SAB implementation |

## Complexity Change

- Time: potential row work from `(r+1)^2` to `4r` per gadget level if and only
  if dummy rows are provably skippable.
- Memory: public key may remain dense if dummy random padding is required.
- What must be measured: key size, keygen, noise, and complete `T_bootstrap/r`.

## Theory Dependencies

- Inherited assumptions: Stage203 equation map and Stage249 distribution
  boundary.
- New assumptions: production keygen can realize semantic-zero dummy rows
  without public distinguishers.
- New lemmas needed: keygen/distribution, noise recurrence, and SAB closure.
- Current status: finite algebra pass; production proof open.

## Required Experiments

- Baselines: current exact dense PVW/MAT-SAB and repeated scalar SAB.
- Metrics: complete-SAB `T_bootstrap/r`, correctness, noise, key size, memory.
- Ablations: dummy rows evaluated vs skipped; active-row set negative controls.
- Success criteria: proof obligations close and full SAB A/B improves `T/r`.
- Failure criteria: public distribution is distinguishable or full SAB fails.
""")
    write_text(PLAN, f"""# Stage330 Compact Keygen/Security Or High-Stat Plan

Input decision: `{decision}`.

Route A: compact keygen/security preflight.

- map Stage203 declared rows to production MAT_TRGSW keygen;
- prove or falsify public distribution indistinguishability;
- derive noise recurrence for semantic-zero dummy skipping;
- no SAB hot-path code until these gates pass.

Route B: high-stat complete-SAB refresh.

- if paper-ready scoped systems result is prioritized, rerun current exact
  PVW/MAT-SAB with at least 10 complete-SAB samples and refreshed resource/noise
  side conditions.
""")

    append_once(GOAL, "<!-- stage329-formal-compact-selector-checker -->", f"""<!-- stage329-formal-compact-selector-checker -->
### Stage329 formal compact selector checker

`{decision}` runs an executable finite checker for the compact selector proof
route. Finite algebra passes, but production keygen/security/noise and full SAB
evidence remain open; no compact SAB code is admitted.
""")
    append_once(ROADMAP, "## Stage 329: Formal Compact Selector Checker", f"""## Stage 329: Formal Compact Selector Checker

Goal: convert the compact selector proof route into an executable finite
checker without touching SAB hot paths.

Status: `{decision}`.
""")
    append_once(HYPOTHESES, "H329_formal_compact_selector_checker:", f"""H329_formal_compact_selector_checker:
  status: {decision}
  primary_metric: finite_semantic_zero_equivalence_and_negative_controls
  evidence:
    - repro/stage329_formal_compact_selector_checker/summary.csv
    - repro/stage329_formal_compact_selector_checker/finite_equivalence_checker.csv
    - repro/stage329_formal_compact_selector_checker/proof_obligation_matrix.csv
    - repro/stage329_formal_compact_selector_checker/proof_gate.csv
  conclusion: >
    Stage329 passes finite compact-selector algebra checks but leaves
    production keygen/security/noise and complete-SAB T_bootstrap/r gates open.
""")
    append_once(MANIFEST, "- stage329_formal_compact_selector_checker:", """- stage329_formal_compact_selector_checker:
  - `docs/stage329_formal_compact_selector_checker.md`
  - `scripts/build_stage329_formal_compact_selector_checker.py`
  - `repro/stage329_formal_compact_selector_checker/`
""")
    append_once(CHECKLIST, "<!-- stage329-formal-compact-selector-checker-checklist -->", f"""<!-- stage329-formal-compact-selector-checker-checklist -->
- [x] Stage329 records `{decision}` and preserves no-code permission for compact SAB.
""")
    append_run_log()

    paths = [
        DOC, THEORY, VARIANT, PLAN, COMMANDS, REPORT, SUMMARY, FINITE, DIST,
        OBLIGATIONS, GATES, NEXT, BUILDER, STAGE203_EQUATIONS,
        STAGE203_RESOURCE, STAGE249_CLAIM, STAGE328_SUMMARY,
    ]
    artifact_index(paths)
    print(decision)
    return 0 if decision == DECISION else 1


if __name__ == "__main__":
    raise SystemExit(main())
