"""Stage248: finite r=2 structured-compact MAT probe.

The probe tests a constrained selector distribution where off-lane body-to-body
terms are structurally zero.  It is a proof prototype only: algebraic equality
for this constrained class does not prove security, public-pattern hiding,
noise safety, or complete-SAB speedup.
"""

from __future__ import annotations

import csv
import hashlib
import random
import subprocess
from datetime import date
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "repro" / "stage248_structured_compact_finite_probe"

INPUTS = {
    "stage246_proof_gate": ROOT / "repro" / "stage246_broader_algorithm_admission_gate" / "proof_gate.csv",
    "stage246_experiment_gate": ROOT / "repro" / "stage246_broader_algorithm_admission_gate" / "experiment_gate_matrix.csv",
    "stage166_counterexamples": ROOT / "repro" / "stage166_shared_output_compact_algebra_gate" / "finite_field_counterexamples.csv",
    "stage166_term_model": ROOT / "repro" / "stage166_shared_output_compact_algebra_gate" / "term_model.csv",
    "stage202_semantic_probe": ROOT / "repro" / "stage202_dummy_padding_semantic_probe" / "summary.csv",
}

DOC = ROOT / "docs" / "stage248_structured_compact_finite_probe.md"
PLAN = ROOT / "experiments" / "stage248_structured_compact_finite_probe_plan.md"
THEORY = ROOT / "theory_checks" / "stage248_structured_compact_finite_model.md"
VARIANT = ROOT / "algorithm_variants" / "mat_rlwe_sab_stage248_structured_compact_finite_probe.md"

INPUT_STATUS = OUT / "input_status.csv"
STRUCTURED_PROBE = OUT / "structured_matrix_probe.csv"
NOISE_PROBE = OUT / "toy_noise_probe.csv"
RESOURCE_MODEL = OUT / "resource_model.csv"
SECURITY_GAP = OUT / "security_gap_matrix.csv"
GATES = OUT / "proof_gate.csv"
NEXT = OUT / "next_stage_queue.csv"
REPORT = OUT / "stage248_report.md"
REPRO_CMDS = OUT / "reproduction_commands.md"
ARTIFACT = OUT / "artifact_index.csv"

ROADMAP = ROOT / "docs" / "roadmap_stage19_plus.md"
GOAL = ROOT / "docs" / "goal_sab_max_acceleration.md"
CURRENT_GOAL = ROOT / "docs" / "current_codex_goal_sab_completion.md"
HYPOTHESES = ROOT / "hypotheses" / "hypothesis_register.yaml"
RUN_LOG = ROOT / "repro" / "run_log.csv"
MANIFEST = ROOT / "repro" / "artifact_manifest.md"
CHECKLIST = ROOT / "repro" / "reproduction_checklist.md"

FIELD = 257
R = 2
STATE_SIZE = 1 + R
SEEDS = list(range(16))
DECISION = "PASS_STAGE248_STRUCTURED_COMPACT_FINITE_ALGEBRA_PASS_SECURITY_BLOCKED"


def rel(path: Path) -> str:
    return path.relative_to(ROOT).as_posix()


def run_git(args: list[str]) -> str:
    proc = subprocess.run(["git", *args], cwd=ROOT, text=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE, check=True)
    return proc.stdout.strip()


def write_csv(path: Path, rows: list[dict[str, object]], fields: list[str]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fields, lineterminator="\n")
        writer.writeheader()
        for row in rows:
            writer.writerow({field: row.get(field, "") for field in fields})


def write_text(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="\n") as f:
        f.write(text.rstrip() + "\n")


def append_once(path: Path, marker: str, text: str) -> None:
    current = path.read_text(encoding="utf-8") if path.exists() else ""
    if marker in current:
        return
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("a", encoding="utf-8", newline="\n") as f:
        if current and not current.endswith("\n"):
            f.write("\n")
        f.write(text.lstrip("\n").rstrip() + "\n")


def sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def table(rows: list[dict[str, object]], fields: list[str]) -> str:
    if not rows:
        return "_No rows._\n"
    lines = ["| " + " | ".join(fields) + " |", "| " + " | ".join(["---"] * len(fields)) + " |"]
    for row in rows:
        lines.append("| " + " | ".join(str(row.get(field, "")).replace("\n", " ") for field in fields) + " |")
    return "\n".join(lines) + "\n"


def input_rows() -> list[dict[str, object]]:
    return [
        {
            "input_id": key,
            "path": rel(path),
            "status": "present" if path.exists() else "missing",
            "bytes": path.stat().st_size if path.exists() else 0,
        }
        for key, path in INPUTS.items()
    ]


def mat_vec(matrix: list[list[int]], vector: list[int]) -> list[int]:
    return [sum((matrix[i][j] * vector[j]) % FIELD for j in range(STATE_SIZE)) % FIELD for i in range(STATE_SIZE)]


def compact_apply(matrix: list[list[int]], vector: list[int]) -> list[int]:
    """Apply compact model that omits body0->body1 and body1->body0 terms."""
    out = []
    for i in range(STATE_SIZE):
        acc = 0
        for j in range(STATE_SIZE):
            if (i, j) in {(1, 2), (2, 1)}:
                continue
            acc = (acc + matrix[i][j] * vector[j]) % FIELD
        out.append(acc)
    return out


def random_matrix(rng: random.Random) -> list[list[int]]:
    return [[rng.randrange(FIELD) for _ in range(STATE_SIZE)] for _ in range(STATE_SIZE)]


def dense_negative_matrix(rng: random.Random) -> list[list[int]]:
    matrix = random_matrix(rng)
    matrix[1][2] = rng.randrange(1, FIELD)
    matrix[2][1] = rng.randrange(1, FIELD)
    return matrix


def structured_matrix(rng: random.Random) -> list[list[int]]:
    matrix = random_matrix(rng)
    matrix[1][2] = 0
    matrix[2][1] = 0
    return matrix


def single_offlane_matrix(rng: random.Random) -> list[list[int]]:
    matrix = structured_matrix(rng)
    matrix[1][2] = rng.randrange(1, FIELD)
    return matrix


def mismatch_count(a: list[int], b: list[int]) -> int:
    return sum(1 for x, y in zip(a, b) if x != y)


def structured_probe_rows() -> list[dict[str, object]]:
    rows: list[dict[str, object]] = []
    for seed in SEEDS:
        rng = random.Random(8800 + seed)
        vector = [rng.randrange(1, FIELD) for _ in range(STATE_SIZE)]
        cases = [
            ("structured_offlane_zero", structured_matrix(rng), "PASS_EQUIVALENCE_EXPECTED"),
            ("random_dense_negative", dense_negative_matrix(rng), "PASS_COUNTEREXAMPLE_EXPECTED"),
            ("single_offlane_nonzero_negative", single_offlane_matrix(rng), "PASS_COUNTEREXAMPLE_EXPECTED"),
        ]
        for case, matrix, expectation in cases:
            dense = mat_vec(matrix, vector)
            compact = compact_apply(matrix, vector)
            mismatches = mismatch_count(dense, compact)
            offlane_values = f"{matrix[1][2]};{matrix[2][1]}"
            if case == "structured_offlane_zero":
                status = "PASS_EQUIVALENCE" if mismatches == 0 else "FAIL_EQUIVALENCE"
            else:
                status = "PASS_COUNTEREXAMPLE" if mismatches > 0 else "FAIL_NEGATIVE_CONTROL"
            rows.append({
                "case": case,
                "seed": seed,
                "field_prime": FIELD,
                "r": R,
                "state_size": STATE_SIZE,
                "offlane_body_terms": offlane_values,
                "mismatches": mismatches,
                "status": status,
                "expectation": expectation,
            })
    return rows


def centered_abs(x: int) -> int:
    y = x % FIELD
    if y > FIELD // 2:
        y -= FIELD
    return abs(y)


def noise_bound(matrix: list[list[int]], noise: list[int], compact: bool) -> list[int]:
    bounds = []
    for i in range(STATE_SIZE):
        acc = 0
        for j in range(STATE_SIZE):
            if compact and (i, j) in {(1, 2), (2, 1)}:
                continue
            acc += centered_abs(matrix[i][j]) * noise[j]
        bounds.append(acc)
    return bounds


def noise_probe_rows() -> list[dict[str, object]]:
    rows: list[dict[str, object]] = []
    for seed in SEEDS:
        rng = random.Random(9900 + seed)
        noise = [rng.randrange(1, 8) for _ in range(STATE_SIZE)]
        structured = structured_matrix(rng)
        dense_random = dense_negative_matrix(rng)
        for case, matrix in [("structured_offlane_zero", structured), ("random_dense_negative", dense_random)]:
            dense_bound = noise_bound(matrix, noise, compact=False)
            compact_bound = noise_bound(matrix, noise, compact=True)
            mismatches = mismatch_count(dense_bound, compact_bound)
            if case == "structured_offlane_zero":
                status = "PASS_TOY_NOISE_EQUIVALENCE" if mismatches == 0 else "FAIL_TOY_NOISE_EQUIVALENCE"
            else:
                status = "PASS_TOY_NOISE_COUNTEREXAMPLE" if mismatches > 0 else "FAIL_NEGATIVE_CONTROL"
            rows.append({
                "case": case,
                "seed": seed,
                "field_prime": FIELD,
                "r": R,
                "state_size": STATE_SIZE,
                "noise_vector": ";".join(map(str, noise)),
                "dense_bound": ";".join(map(str, dense_bound)),
                "compact_bound": ";".join(map(str, compact_bound)),
                "mismatches": mismatches,
                "status": status,
            })
    return rows


def resource_rows() -> list[dict[str, object]]:
    dense_terms = STATE_SIZE * STATE_SIZE
    compact_terms = dense_terms - 2
    return [
        {
            "row_id": "term_count",
            "r": R,
            "state_size": STATE_SIZE,
            "dense_terms": dense_terms,
            "compact_terms_if_offlane_zero": compact_terms,
            "removed_terms": 2,
            "dense_over_compact": f"{dense_terms / compact_terms:.6f}",
            "interpretation": "Term saving is algebraic only; it is not a complete-SAB speedup or security proof.",
        },
        {
            "row_id": "claim_boundary",
            "r": R,
            "state_size": STATE_SIZE,
            "dense_terms": dense_terms,
            "compact_terms_if_offlane_zero": compact_terms,
            "removed_terms": 2,
            "dense_over_compact": f"{dense_terms / compact_terms:.6f}",
            "interpretation": "Any real value must survive keygen/security/noise and full-SAB T_bootstrap/r gates.",
        },
    ]


def security_gap_rows() -> list[dict[str, object]]:
    return [
        {
            "gap_id": "SEC248-1",
            "topic": "selector_distribution",
            "current_status": "blocked",
            "gap": "Off-lane-zero public pattern may distinguish the structured selector distribution.",
            "required_next_evidence": "hybrid or simulation argument, or dummy/padding scheme with semantic-zero proof",
            "production_permission": "no",
        },
        {
            "gap_id": "SEC248-2",
            "topic": "keygen_security",
            "current_status": "blocked",
            "gap": "No proof that constrained selector/keygen preserves the original security assumptions.",
            "required_next_evidence": "formal key distribution and reduction/simulation argument",
            "production_permission": "no",
        },
        {
            "gap_id": "SEC248-3",
            "topic": "noise_recurrence",
            "current_status": "toy_only",
            "gap": "Toy coefficient bound equality is not a ring-LWE noise proof under SAB rotations and CMUX schedule.",
            "required_next_evidence": "ring-level noise recurrence plus multi-seed full-SAB noise if implemented",
            "production_permission": "no",
        },
        {
            "gap_id": "SEC248-4",
            "topic": "complete_sab_value",
            "current_status": "unmeasured",
            "gap": "Term-count reduction is not complete-SAB T_bootstrap/r improvement.",
            "required_next_evidence": "after proof gates, implement behind flag and run same-backend complete-SAB A/B",
            "production_permission": "no",
        },
    ]


def gate_rows(inputs, structured, noise, security) -> list[dict[str, object]]:
    inputs_ok = all(row["status"] == "present" for row in inputs)
    structured_pos_ok = all(row["status"] == "PASS_EQUIVALENCE" for row in structured if row["case"] == "structured_offlane_zero")
    structured_neg_ok = all(str(row["status"]).startswith("PASS_COUNTEREXAMPLE") for row in structured if row["case"] != "structured_offlane_zero")
    noise_pos_ok = all(row["status"] == "PASS_TOY_NOISE_EQUIVALENCE" for row in noise if row["case"] == "structured_offlane_zero")
    noise_neg_ok = all(row["status"] == "PASS_TOY_NOISE_COUNTEREXAMPLE" for row in noise if row["case"] != "structured_offlane_zero")
    security_blocked = all(row["production_permission"] == "no" for row in security)
    decision_ok = inputs_ok and structured_pos_ok and structured_neg_ok and noise_pos_ok and noise_neg_ok and security_blocked
    return [
        {
            "gate": "G1_inputs",
            "status": "PASS" if inputs_ok else "FAIL",
            "metric": "required inputs",
            "value": "all present" if inputs_ok else "missing",
            "evidence": rel(INPUT_STATUS),
            "interpretation": "Stage248 starts from Stage246 admission and prior compact counterexamples.",
        },
        {
            "gate": "G2_structured_algebra_positive",
            "status": "PASS" if structured_pos_ok else "FAIL",
            "metric": "structured off-lane-zero mismatches",
            "value": "0 for all seeds" if structured_pos_ok else "mismatch present",
            "evidence": rel(STRUCTURED_PROBE),
            "interpretation": "Compact omission is algebraically exact for the constrained off-lane-zero class.",
        },
        {
            "gate": "G3_negative_controls",
            "status": "PASS_COUNTEREXAMPLES" if structured_neg_ok else "FAIL",
            "metric": "random/single-offlane dense mismatches",
            "value": "positive mismatches" if structured_neg_ok else "negative control failed",
            "evidence": rel(STRUCTURED_PROBE),
            "interpretation": "The probe still rejects generic dense selectors and single off-lane nonzero terms.",
        },
        {
            "gate": "G4_toy_noise",
            "status": "PASS_TOY_ONLY" if noise_pos_ok and noise_neg_ok else "FAIL",
            "metric": "toy bound equivalence/counterexample",
            "value": "structured equal; random dense differs" if noise_pos_ok and noise_neg_ok else "toy noise failure",
            "evidence": rel(NOISE_PROBE),
            "interpretation": "Toy noise follows algebraic structure only; ring-level SAB noise remains open.",
        },
        {
            "gate": "G5_security_boundary",
            "status": "PASS_SECURITY_BLOCKED_RECORDED" if security_blocked else "FAIL",
            "metric": "production permissions",
            "value": "all no",
            "evidence": rel(SECURITY_GAP),
            "interpretation": "Algebra pass does not permit production compact SAB implementation.",
        },
        {
            "gate": "G6_stage248_decision",
            "status": DECISION if decision_ok else "FAIL_STAGE248_STRUCTURED_COMPACT_PROBE",
            "metric": "decision",
            "value": DECISION if decision_ok else "FAIL_STAGE248_STRUCTURED_COMPACT_PROBE",
            "evidence": rel(GATES),
            "interpretation": "Proceed to distribution/security preflight; no hot-path SAB edits yet.",
        },
    ]


def next_rows() -> list[dict[str, object]]:
    return [
        {
            "priority": "P0",
            "route": "stage249_structured_compact_distribution_security_preflight",
            "entry_condition": "Stage248 algebra and toy noise pass but security/public-pattern gates are blocked.",
            "gate": "formal selector distribution, public-pattern hiding or dummy semantic-zero padding, keygen security argument",
            "status": "selected_next",
            "failure_action": "freeze structured compact route before production implementation",
            "evidence": rel(SECURITY_GAP),
        },
        {
            "priority": "P1",
            "route": "stage250_exact_dense_lower_bound_gap_refresh",
            "entry_condition": "Optimality wording remains desired.",
            "gate": "lower-bound gap model tied to counters/assembly",
            "status": "analysis_gate",
            "failure_action": "state measured engineering improvement only",
            "evidence": "theory_checks/mat_rlwe_sab_amortized_optimality.md",
        },
        {
            "priority": "P2",
            "route": "stage251_nonbinary_selector_semantics_preflight",
            "entry_condition": "Non-binary PVW-SAB claim is needed.",
            "gate": "ternary/include-zero selector semantics and staged equivalence",
            "status": "blocked_until_design",
            "failure_action": "keep non-binary PVW unsupported",
            "evidence": "repro/stage229_parameter_generalization_matrix/coverage_gaps.csv",
        },
    ]


def artifact_rows(paths: list[Path]) -> list[dict[str, object]]:
    rows = []
    for path in paths:
        rows.append({
            "artifact": rel(path),
            "exists": "yes" if path.exists() else "no",
            "sha256": sha256(path) if path.exists() and path.is_file() else "",
            "bytes": path.stat().st_size if path.exists() and path.is_file() else 0,
        })
    return rows


def write_docs(inputs, structured, noise, resources, security, gates, nextq, head: str) -> None:
    write_text(DOC, f"""# Stage248 Structured Compact Finite Probe

Decision: `{gates[-1]["status"]}`.

Stage248 tests the Stage246 structured-compact proof-prototype route in a
finite r=2 model. The compact model omits exactly the two body-to-body off-lane
terms that Stage166 identified as missing from a shared-output compact
representation.

## Model

```text
state = [mask, body0, body1]
missing compact terms = body0 -> body1 and body1 -> body0
structured selector condition = both missing terms are zero
```

For structured off-lane-zero selectors, dense reference and compact application
must match. For random dense selectors and a single nonzero off-lane term, they
must differ.

## Proof Gates

{table(gates, ["gate", "status", "metric", "value", "evidence", "interpretation"])}

## Resource Model

{table(resources, ["row_id", "r", "state_size", "dense_terms", "compact_terms_if_offlane_zero", "removed_terms", "dense_over_compact", "interpretation"])}

## Security Gaps

{table(security, ["gap_id", "topic", "current_status", "gap", "required_next_evidence", "production_permission"])}

## Next Queue

{table(nextq, ["priority", "route", "entry_condition", "gate", "status", "failure_action", "evidence"])}

## Inputs

{table(inputs, ["input_id", "path", "status", "bytes"])}

Generated from head `{head}`. Raw structured probe rows are in
`{rel(STRUCTURED_PROBE)}` and toy noise rows are in `{rel(NOISE_PROBE)}`.
""")
    write_text(REPORT, f"""# Stage248 Report

Decision: `{gates[-1]["status"]}`.

The finite r=2 structured off-lane-zero algebra probe passes: compact omission
matches dense reference on the constrained selector class and fails on the
negative controls. The toy noise bound mirrors this algebraic result. This does
not authorize production compact SAB because selector distribution, keygen
security, ring-level noise, and complete-SAB value are still unproven.
""")
    write_text(PLAN, """# Stage248 Structured Compact Finite Probe Plan

## Objective

Run a finite r=2 proof prototype for the structured compact route selected by
Stage246.

## Gates

- Positive algebra: structured off-lane-zero selectors must match dense
  reference for all seeds.
- Negative controls: random dense and single-offlane-nonzero selectors must
  mismatch.
- Toy noise: structured toy bound must match dense reference and negative
  controls must differ.
- Security boundary: no production implementation permission until selector
  distribution/keygen/security/noise gates are closed.
""")
    write_text(THEORY, """# Stage248 Structured Compact Finite Model

Stage248 models only one algebraic condition:

```text
M[body0, body1] = 0 and M[body1, body0] = 0
```

Under this condition, omitting the two off-lane body-to-body terms is exact in
the finite state model. This is a necessary condition for a compact route, not
a sufficient condition for SAB.

The following remain open:

- whether the constrained selector distribution is secure or publicly hidden;
- whether dummy semantic-zero padding can hide the pattern without losing value;
- whether ring-level SAB rotations and CMUX preserve the same noise recurrence;
- whether complete-SAB `T_bootstrap/r` improves after implementation.
""")
    write_text(VARIANT, """# MAT-RLWE SAB Stage248 Structured Compact Prototype

## Summary

- Parent algorithm: PVW/MAT-SAB for 2025/686 sparse amortized bootstrapping.
- Focused module: compact representation of MAT selector action.
- Optimization target: future complete-SAB `T_bootstrap/r`; Stage248 itself is
  algebra/noise proof-prototype only.
- Status labels: `algebra_pass`, `toy_noise_pass`, `security_blocked`,
  `no_production_permission`.
- Main hypothesis: if keygen can enforce or hide off-lane body-to-body zero
  terms, compact MAT could remove terms before full-SAB integration.

## Mathematical Definition

For r=2, the shared-mask dense state is:

```text
x = [mask, body0, body1]
```

The compact prototype omits:

```text
M[body0, body1], M[body1, body0]
```

The constrained selector class requires both terms to be zero, making compact
and dense application equivalent in the finite model.

## Delta From Original Algorithm

| Original component | Variant component | Relationship | Evidence/status |
| --- | --- | --- | --- |
| generic dense MAT selector | off-lane-zero structured selector | changes key distribution | algebra pass, security blocked |
| production SAB CMUX | finite r=2 matrix probe | proof prototype | no production permission |

## Required Experiments

- Distribution/security preflight.
- Ring-level noise recurrence.
- Flag-only compact implementation only after proof gates.
- Complete-SAB A/B using `T_bootstrap/r`.
""")
    write_text(REPRO_CMDS, f"""# Stage248 Reproduction Commands

```text
python scripts/build_stage248_structured_compact_finite_probe.py
python -m py_compile scripts/build_stage248_structured_compact_finite_probe.py
```

Decision: `{gates[-1]["status"]}`.
""")


def update_project_files(head: str, decision: str) -> None:
    append_once(ROADMAP, "## Stage 248: Structured Compact Finite Probe", f"""
## Stage 248: Structured Compact Finite Probe

Goal:

```text
Run the Stage246 structured compact proof prototype in a finite r=2 model.
```

Status:

```text
Generated from input head `{head}` with `{decision}`. The off-lane-zero
structured compact algebra and toy noise probes pass, but selector
distribution, keygen security, ring-level noise, and complete-SAB value remain
blocked. No production compact SAB implementation is admitted.
```
""")
    append_once(GOAL, "Stage248 structured compact finite probe", f"""
- Stage248 structured compact finite probe records `{decision}`: the constrained
  off-lane-zero compact algebra passes finite r=2 positive and negative
  controls, but the route remains blocked before production SAB integration by
  distribution/security/ring-noise/full-SAB value gates.
""")
    append_once(CURRENT_GOAL, "### Stage248 structured compact finite probe", f"""
### Stage248 structured compact finite probe

`{decision}` records a proof-prototype pass for constrained compact algebra.
The active goal remains open because security/distribution proof, ring-level
noise, complete-SAB implementation, non-binary support, lower-bound optimality,
and final citation closure remain incomplete.
""")
    append_once(HYPOTHESES, "H10_stage248_structured_compact_finite_probe:", f"""
H10_stage248_structured_compact_finite_probe:
  status: structured_compact_algebra_pass_security_blocked
  evidence:
    - repro/stage248_structured_compact_finite_probe/structured_matrix_probe.csv
    - repro/stage248_structured_compact_finite_probe/toy_noise_probe.csv
    - repro/stage248_structured_compact_finite_probe/security_gap_matrix.csv
    - repro/stage248_structured_compact_finite_probe/proof_gate.csv
    - docs/stage248_structured_compact_finite_probe.md
  conclusion: >
    Stage248 records {decision}. A finite r=2 off-lane-zero structured compact
    algebra probe passes positive and negative controls, and the toy noise
    bound mirrors the algebraic result. The route remains proof-only because
    selector distribution, keygen security, ring-level noise, and complete-SAB
    value are not proven.
""")
    append_once(RUN_LOG, "stage248-structured-compact-finite-probe-001", f"""stage248-structured-compact-finite-probe-001,{date.today().isoformat()},{head},Stage 248,finite_algebra_probe,"python scripts/build_stage248_structured_compact_finite_probe.py","Stage246 admission + Stage166 compact counterexamples",n/a,{decision},"Structured compact finite algebra passes; security and production gates remain blocked.",docs/stage248_structured_compact_finite_probe.md; repro/stage248_structured_compact_finite_probe/proof_gate.csv
""")
    append_once(MANIFEST, "- stage248_structured_compact_finite_probe:", """
- stage248_structured_compact_finite_probe:
  - `docs/stage248_structured_compact_finite_probe.md`
  - `experiments/stage248_structured_compact_finite_probe_plan.md`
  - `theory_checks/stage248_structured_compact_finite_model.md`
  - `algorithm_variants/mat_rlwe_sab_stage248_structured_compact_finite_probe.md`
  - `scripts/build_stage248_structured_compact_finite_probe.py`
  - `repro/stage248_structured_compact_finite_probe/`
""")
    append_once(CHECKLIST, "Stage248 structured compact finite probe records algebra pass security blocked", f"""
- [x] Stage248 structured compact finite probe records algebra pass/security blocked `{decision}`.
""")


def main() -> None:
    OUT.mkdir(parents=True, exist_ok=True)
    head = run_git(["rev-parse", "--short", "HEAD"])
    inputs = input_rows()
    structured = structured_probe_rows()
    noise = noise_probe_rows()
    resources = resource_rows()
    security = security_gap_rows()
    gates = gate_rows(inputs, structured, noise, security)
    nextq = next_rows()

    write_csv(INPUT_STATUS, inputs, ["input_id", "path", "status", "bytes"])
    write_csv(STRUCTURED_PROBE, structured, ["case", "seed", "field_prime", "r", "state_size", "offlane_body_terms", "mismatches", "status", "expectation"])
    write_csv(NOISE_PROBE, noise, ["case", "seed", "field_prime", "r", "state_size", "noise_vector", "dense_bound", "compact_bound", "mismatches", "status"])
    write_csv(RESOURCE_MODEL, resources, ["row_id", "r", "state_size", "dense_terms", "compact_terms_if_offlane_zero", "removed_terms", "dense_over_compact", "interpretation"])
    write_csv(SECURITY_GAP, security, ["gap_id", "topic", "current_status", "gap", "required_next_evidence", "production_permission"])
    write_csv(GATES, gates, ["gate", "status", "metric", "value", "evidence", "interpretation"])
    write_csv(NEXT, nextq, ["priority", "route", "entry_condition", "gate", "status", "failure_action", "evidence"])

    write_docs(inputs, structured, noise, resources, security, gates, nextq, head)
    artifacts = [DOC, PLAN, THEORY, VARIANT, INPUT_STATUS, STRUCTURED_PROBE, NOISE_PROBE, RESOURCE_MODEL, SECURITY_GAP, GATES, NEXT, REPORT, REPRO_CMDS]
    write_csv(ARTIFACT, artifact_rows(artifacts), ["artifact", "exists", "sha256", "bytes"])
    update_project_files(head, gates[-1]["status"])
    print(f"Stage248 report: {rel(DOC)}")
    print(f"Stage248 decision: {gates[-1]['status']}")


if __name__ == "__main__":
    main()
