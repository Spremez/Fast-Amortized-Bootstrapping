#!/usr/bin/env python3
"""Stage173: structured compact finite phase/noise toy gate."""

from __future__ import annotations

import csv
import hashlib
import random
import statistics
import subprocess
from pathlib import Path
from typing import Dict, Iterable, List, Tuple


ROOT = Path(__file__).resolve().parents[1]
OUT_DIR = ROOT / "repro" / "stage173_structured_compact_phase_noise_toy"

SUMMARY_CSV = OUT_DIR / "summary.csv"
EQUATIONS_CSV = OUT_DIR / "equation_model.csv"
PHASE_CSV = OUT_DIR / "finite_phase_results.csv"
NOISE_CSV = OUT_DIR / "noise_toy_results.csv"
PROOF_CSV = OUT_DIR / "proof_status_update.csv"
NEXT_CSV = OUT_DIR / "next_stage_queue.csv"
ARTIFACT_CSV = OUT_DIR / "artifact_index.csv"

OUT_MD = ROOT / "docs" / "stage173_structured_compact_phase_noise_toy.md"
PLAN_MD = ROOT / "experiments" / "stage173_structured_compact_phase_noise_toy_plan.md"
THEORY_MD = ROOT / "theory_checks" / "stage173_structured_compact_phase_noise_model.md"
VARIANT_MD = ROOT / "algorithm_variants" / "mat_rlwe_sab_structured_compact_phase_noise_toy.md"

ROADMAP_MD = ROOT / "docs" / "roadmap_stage19_plus.md"
GOAL_MD = ROOT / "docs" / "goal_sab_max_acceleration.md"
CURRENT_GOAL_MD = ROOT / "docs" / "current_codex_goal_sab_completion.md"
HYPOTHESIS_YAML = ROOT / "hypotheses" / "hypothesis_register.yaml"
RUN_LOG = ROOT / "repro" / "run_log.csv"
MANIFEST = ROOT / "repro" / "artifact_manifest.md"
CHECKLIST = ROOT / "repro" / "reproduction_checklist.md"

STAGE171_PROOF = ROOT / "repro" / "stage171_structured_compact_keygen_feasibility" / "proof_obligations.csv"
STAGE175_NEXT = ROOT / "repro" / "stage175_post_stage174_frontier_refresh" / "next_stage_queue.csv"

PRIME = 65537
SEED = 173
R_VALUES = (2, 4, 6)
TRIALS = 64
IN_N = 16
R_PREC = 4
INPUT_VAR = 1.0
KEY_VAR = 0.01


Vector = List[int]
Matrix = List[List[int]]


def rel(path: Path) -> str:
    return path.resolve().relative_to(ROOT.resolve()).as_posix()


def write_text_lf(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(text.encode("utf-8"))


def write_csv(path: Path, rows: Iterable[Dict[str, str]], fields: List[str]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    row_list = list(rows)
    normalized = [{field: row.get(field, "") for field in fields} for row in row_list]
    with path.open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fields, lineterminator="\n")
        writer.writeheader()
        writer.writerows(normalized)


def table(rows: List[Dict[str, str]], fields: List[str]) -> str:
    def cell(value: str) -> str:
        return str(value).replace("|", "\\|").replace("\n", "<br>")

    out = [
        "| " + " | ".join(fields) + " |",
        "| " + " | ".join(["---"] * len(fields)) + " |",
    ]
    for row in rows:
        out.append("| " + " | ".join(cell(row.get(field, "")) for field in fields) + " |")
    return "\n".join(out)


def sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def git_head() -> str:
    try:
        return subprocess.check_output(
            ["git", "rev-parse", "--short", "HEAD"],
            cwd=ROOT,
            text=True,
        ).strip()
    except Exception:
        return "unknown"


def append_once(path: Path, marker: str, block: str) -> None:
    text = path.read_text(encoding="utf-8") if path.exists() else ""
    if marker in text:
        return
    if text and not text.endswith("\n"):
        text += "\n"
    write_text_lf(path, text + block.strip("\n") + "\n")


def rand_field(rng: random.Random) -> int:
    return rng.randrange(0, PRIME)


def rand_nonzero(rng: random.Random) -> int:
    return rng.randrange(1, PRIME)


def add_vec(a: Vector, b: Vector) -> Vector:
    return [(x + y) % PRIME for x, y in zip(a, b)]


def sub_vec(a: Vector, b: Vector) -> Vector:
    return [(x - y) % PRIME for x, y in zip(a, b)]


def mat_vec(matrix: Matrix, vector: Vector) -> Vector:
    return [sum((mij * vj) % PRIME for mij, vj in zip(row, vector)) % PRIME for row in matrix]


def structured_matrix(rng: random.Random, r: int) -> Matrix:
    m = 1 + r
    matrix = [[0 for _ in range(m)] for _ in range(m)]
    for col in range(m):
        matrix[0][col] = rand_nonzero(rng)
    for row in range(1, m):
        matrix[row][0] = rand_nonzero(rng)
        matrix[row][row] = rand_nonzero(rng)
    return matrix


def compact_mat_vec(matrix: Matrix, vector: Vector) -> Vector:
    r = len(vector) - 1
    out = [0 for _ in vector]
    out[0] = sum((matrix[0][col] * vector[col]) % PRIME for col in range(r + 1)) % PRIME
    for lane in range(1, r + 1):
        out[lane] = (
            matrix[lane][0] * vector[0] +
            matrix[lane][lane] * vector[lane]
        ) % PRIME
    return out


def rotate_vector(vector: Vector, bit: int, slot: int, trial: int) -> Vector:
    out = []
    for idx, value in enumerate(vector):
        if (idx + bit + slot + trial) & 1:
            out.append((-value) % PRIME)
        else:
            out.append(value)
    return out


def dense_cmux(addend: Vector, rhs: Vector, selector: Matrix) -> Vector:
    return add_vec(addend, mat_vec(selector, sub_vec(rhs, addend)))


def compact_cmux(addend: Vector, rhs: Vector, selector: Matrix) -> Vector:
    return add_vec(addend, compact_mat_vec(selector, sub_vec(rhs, addend)))


def run_schedule(rng: random.Random, r: int, trial: int) -> Tuple[int, int]:
    m = 1 + r
    dense_state = [[rand_field(rng) for _ in range(m)] for _ in range(IN_N)]
    compact_state = [row[:] for row in dense_state]
    dense_next = [[0 for _ in range(m)] for _ in range(IN_N)]
    compact_next = [[0 for _ in range(m)] for _ in range(IN_N)]

    total_mismatches = 0
    for bit in range(R_PREC):
        power = 1 << bit
        selector = structured_matrix(rng, r)
        for j in range(power):
            rhs_dense = rotate_vector(dense_state[IN_N - power + j], bit, j, trial)
            rhs_compact = rotate_vector(compact_state[IN_N - power + j], bit, j, trial)
            dense_next[j] = dense_cmux(dense_state[j], rhs_dense, selector)
            compact_next[j] = compact_cmux(compact_state[j], rhs_compact, selector)
        for j in range(0, IN_N - power):
            dense_next[j + power] = dense_cmux(dense_state[j + power], dense_state[j], selector)
            compact_next[j + power] = compact_cmux(compact_state[j + power], compact_state[j], selector)
        for idx in range(IN_N):
            for comp in range(m):
                if dense_next[idx][comp] != compact_next[idx][comp]:
                    total_mismatches += 1
        dense_state = [row[:] for row in dense_next]
        compact_state = [row[:] for row in compact_next]
    return total_mismatches, IN_N * m * R_PREC


def negative_cross_check(r: int) -> int:
    m = 1 + r
    selector = [[0 for _ in range(m)] for _ in range(m)]
    for col in range(m):
        selector[0][col] = 1
    for row in range(1, m):
        selector[row][0] = 1
        selector[row][row] = 1
    selector[1][2] = 1
    addend = [0 for _ in range(m)]
    rhs = [0 for _ in range(m)]
    rhs[2] = 1
    dense = dense_cmux(addend, rhs, selector)
    compact = compact_cmux(addend, rhs, selector)
    return sum(1 for x, y in zip(dense, compact) if x != y)


def build_phase_results() -> List[Dict[str, str]]:
    rng = random.Random(SEED)
    rows = []
    for r in R_VALUES:
        for trial in range(TRIALS):
            mismatches, checked = run_schedule(rng, r, trial)
            negative_mismatches = negative_cross_check(r)
            rows.append({
                "r": str(r),
                "trial": str(trial),
                "field_prime": str(PRIME),
                "in_N": str(IN_N),
                "r_prec": str(R_PREC),
                "checked_components": str(checked),
                "structured_mismatches": str(mismatches),
                "negative_cross_mismatches": str(negative_mismatches),
                "status": "PASS_PHASE_TOY" if mismatches == 0 and negative_mismatches > 0 else "FAIL",
            })
    return rows


def signed_coeff(rng: random.Random) -> int:
    value = 0
    while value == 0:
        value = rng.randint(-3, 3)
    return value


def build_noise_results() -> List[Dict[str, str]]:
    rng = random.Random(SEED + 1)
    rows = []
    for r in R_VALUES:
        m = 1 + r
        for trial in range(TRIALS):
            shared_coeffs = [signed_coeff(rng) for _ in range(m)]
            body_shared = [signed_coeff(rng) for _ in range(r)]
            body_diag = [signed_coeff(rng) for _ in range(r)]
            shared_signal = sum(c * c * INPUT_VAR for c in shared_coeffs)
            shared_var = shared_signal + m * KEY_VAR
            dense_body_vars = []
            compact_body_vars = []
            for lane in range(r):
                signal = (body_shared[lane] ** 2 + body_diag[lane] ** 2) * INPUT_VAR
                dense_body_vars.append(signal + m * KEY_VAR)
                compact_body_vars.append(signal + 2 * KEY_VAR)
            dense_avg = (shared_var + sum(dense_body_vars)) / m
            compact_avg = (shared_var + sum(compact_body_vars)) / m
            ratio = compact_avg / dense_avg if dense_avg else 0.0
            rows.append({
                "r": str(r),
                "trial": str(trial),
                "input_variance": f"{INPUT_VAR:.6f}",
                "key_noise_variance": f"{KEY_VAR:.6f}",
                "dense_zero_padded_avg_variance": f"{dense_avg:.12f}",
                "compact_omitted_zero_avg_variance": f"{compact_avg:.12f}",
                "compact_over_dense": f"{ratio:.12f}",
                "status": "PASS_NOISE_TOY_COMPACT_LE_DENSE_ZERO_PADDED" if compact_avg <= dense_avg else "FAIL",
            })
    return rows


def build_equations() -> List[Dict[str, str]]:
    return [
        {
            "object": "state",
            "equation": "x = (x_0, x_1, ..., x_r)",
            "meaning": "PVW/MAT-RLWE phase vector: shared component plus r body lanes.",
        },
        {
            "object": "structured_selector",
            "equation": "M[0,*] arbitrary; M[q,0], M[q,q] arbitrary; M[q,j]=0 for q!=j and q,j>0",
            "meaning": "Compact keygen constraint required by Stage171.",
        },
        {
            "object": "CMUX_phase",
            "equation": "out = addend + M * (rhs - addend)",
            "meaning": "Finite-field phase model for one SAB CMUX/NCMUX update.",
        },
        {
            "object": "compact_apply",
            "equation": "out_0=sum_j M[0,j]d_j; out_q=M[q,0]d_0+M[q,q]d_q",
            "meaning": "Compact external product formula for d=rhs-addend.",
        },
        {
            "object": "noise_toy",
            "equation": "dense_zero_padded body variance = signal + (1+r)sigma_key^2; compact body variance = signal + 2sigma_key^2",
            "meaning": "Toy comparison when omitted cross terms are logical zero encryptions.",
        },
    ]


def build_proof_status(phase_rows: List[Dict[str, str]], noise_rows: List[Dict[str, str]]) -> List[Dict[str, str]]:
    phase_pass = all(row["status"] == "PASS_PHASE_TOY" for row in phase_rows)
    noise_pass = all(row["status"] == "PASS_NOISE_TOY_COMPACT_LE_DENSE_ZERO_PADDED" for row in noise_rows)
    return [
        {
            "obligation": "keygen_distribution",
            "stage173_status": "PARTIAL_TOY_EQUATIONS_DEFINED",
            "remaining_gap": "Need formal distribution/hybrid argument for omitted zero encryptions.",
            "implementation_permission": "NO",
        },
        {
            "obligation": "phase_invariant",
            "stage173_status": "TOY_PASS" if phase_pass else "TOY_FAIL",
            "remaining_gap": "Finite-field schedule toy is not a formal polynomial/RLWE proof.",
            "implementation_permission": "NO",
        },
        {
            "obligation": "noise_accounting",
            "stage173_status": "TOY_PASS" if noise_pass else "TOY_FAIL",
            "remaining_gap": "Toy variance ignores correlations, modulus effects, and real bootstrapping-key noise.",
            "implementation_permission": "NO",
        },
        {
            "obligation": "security_reduction",
            "stage173_status": "OPEN",
            "remaining_gap": "Need real reduction or explicit structured assumption before novelty claim.",
            "implementation_permission": "NO",
        },
        {
            "obligation": "closed_state_API",
            "stage173_status": "TOY_PHASE_CLOSED_PVW_VECTOR" if phase_pass else "TOY_FAIL",
            "remaining_gap": "Need API design proving compact key material can feed SAB without dense re-expansion.",
            "implementation_permission": "NO",
        },
    ]


def build_next_queue(decision: str) -> List[Dict[str, str]]:
    if decision.startswith("PASS"):
        return [
            {
                "priority": "P0",
                "stage": "176",
                "name": "structured compact security/API design card",
                "entry_condition": "Stage173 finite phase/noise toy passes but implementation permission remains NO.",
                "gate": "Define keygen distribution, security assumption/reduction, and closed-state API without dense re-expansion.",
                "failure_rule": "If security/API cannot close, compact remains a theoretical upper-bound route only.",
            },
            {
                "priority": "P1",
                "stage": "177",
                "name": "literature matrix refresh",
                "entry_condition": "Before any structured compact novelty claim.",
                "gate": "Verify real related work for compact/multi-output/PVW/MAT bootstrapping.",
                "failure_rule": "No novelty wording without verified sources.",
            },
        ]
    return [
        {
            "priority": "P0",
            "stage": "176",
            "name": "compact route rejection/repair",
            "entry_condition": "Stage173 phase or noise toy failed.",
            "gate": "Explain failed invariant and either repair equations or close compact route.",
            "failure_rule": "No implementation if toy invariants fail.",
        },
    ]


def decide(phase_rows: List[Dict[str, str]], noise_rows: List[Dict[str, str]]) -> str:
    if not STAGE171_PROOF.exists() or not STAGE175_NEXT.exists():
        return "BLOCKED_STAGE173_MISSING_INPUT"
    if any(row["status"] != "PASS_PHASE_TOY" for row in phase_rows):
        return "FAIL_STAGE173_STRUCTURED_COMPACT_PHASE_TOY"
    if any(row["status"] != "PASS_NOISE_TOY_COMPACT_LE_DENSE_ZERO_PADDED" for row in noise_rows):
        return "FAIL_STAGE173_STRUCTURED_COMPACT_NOISE_TOY"
    return "PASS_STAGE173_PHASE_NOISE_TOY_PROOF_STILL_OPEN"


def build_summary(
    decision: str,
    phase_rows: List[Dict[str, str]],
    noise_rows: List[Dict[str, str]],
    proof_rows: List[Dict[str, str]],
) -> List[Dict[str, str]]:
    phase_failures = sum(1 for row in phase_rows if row["status"] != "PASS_PHASE_TOY")
    noise_failures = sum(1 for row in noise_rows if row["status"] != "PASS_NOISE_TOY_COMPACT_LE_DENSE_ZERO_PADDED")
    ratios = [float(row["compact_over_dense"]) for row in noise_rows]
    implementation_yes = sum(1 for row in proof_rows if row["implementation_permission"] == "YES")
    return [
        {
            "gate": "stage173_inputs",
            "status": "PASS" if STAGE171_PROOF.exists() and STAGE175_NEXT.exists() else "BLOCKED",
            "metric": "inputs",
            "value": f"{rel(STAGE171_PROOF)};{rel(STAGE175_NEXT)}",
            "evidence": rel(SUMMARY_CSV),
            "detail": "Stage173 consumes Stage171 proof obligations and Stage175 route decision.",
            "next_action": "Repair missing inputs before interpreting toy results.",
        },
        {
            "gate": "stage173_phase_toy",
            "status": "PASS" if phase_failures == 0 else "FAIL",
            "metric": "phase_failures",
            "value": str(phase_failures),
            "evidence": rel(PHASE_CSV),
            "detail": "Structured compact matches structured dense through SAB-like finite CMUX/NCMUX schedule; cross-term negative control mismatches.",
            "next_action": "If this fails, close or repair compact equations before any code.",
        },
        {
            "gate": "stage173_noise_toy",
            "status": "PASS" if noise_failures == 0 else "FAIL",
            "metric": "max_compact_over_dense;mean_compact_over_dense",
            "value": f"{max(ratios):.12f};{statistics.mean(ratios):.12f}",
            "evidence": rel(NOISE_CSV),
            "detail": "Toy variance for omitted zero cross terms is no larger than dense zero-padded variance.",
            "next_action": "Still require real noise proof/simulation before implementation.",
        },
        {
            "gate": "stage173_implementation_permission",
            "status": "BLOCKED_PROOF",
            "metric": "permission_yes",
            "value": str(implementation_yes),
            "evidence": rel(PROOF_CSV),
            "detail": "Security reduction and closed-state API are still not proven.",
            "next_action": "Do not implement compact SAB yet.",
        },
        {
            "gate": "stage173_decision",
            "status": decision,
            "metric": "structured_compact_route",
            "value": "toy_pass_proof_open" if decision.startswith("PASS") else "toy_failed",
            "evidence": rel(SUMMARY_CSV),
            "detail": "Stage173 advances compact route with finite/toy evidence without granting paper or implementation claims.",
            "next_action": "Proceed to security/API design or literature gate.",
        },
    ]


def artifact_index(paths: List[Path]) -> None:
    fields = ["path", "exists", "sha256", "bytes"]
    rows = []
    for path in paths:
        if path == ARTIFACT_CSV:
            continue
        rows.append({
            "path": rel(path),
            "exists": "yes" if path.exists() else "no",
            "sha256": sha256_file(path) if path.exists() and path.is_file() else "",
            "bytes": str(path.stat().st_size) if path.exists() and path.is_file() else "",
        })
    write_csv(ARTIFACT_CSV, rows, fields)
    rows.append({
        "path": rel(ARTIFACT_CSV),
        "exists": "yes",
        "sha256": sha256_file(ARTIFACT_CSV),
        "bytes": str(ARTIFACT_CSV.stat().st_size),
    })
    write_csv(ARTIFACT_CSV, rows, fields)


def write_docs(
    decision: str,
    summary: List[Dict[str, str]],
    equations: List[Dict[str, str]],
    phase_rows: List[Dict[str, str]],
    noise_rows: List[Dict[str, str]],
    proof_rows: List[Dict[str, str]],
    next_rows: List[Dict[str, str]],
) -> None:
    summary_fields = ["gate", "status", "metric", "value", "evidence", "detail", "next_action"]
    equation_fields = ["object", "equation", "meaning"]
    phase_fields = ["r", "trial", "field_prime", "in_N", "r_prec", "checked_components", "structured_mismatches", "negative_cross_mismatches", "status"]
    noise_fields = ["r", "trial", "input_variance", "key_noise_variance", "dense_zero_padded_avg_variance", "compact_omitted_zero_avg_variance", "compact_over_dense", "status"]
    proof_fields = ["obligation", "stage173_status", "remaining_gap", "implementation_permission"]
    next_fields = ["priority", "stage", "name", "entry_condition", "gate", "failure_rule"]

    write_text_lf(OUT_MD, f"""# Stage173 Structured Compact Phase/Noise Toy

Decision: `{decision}`.

Stage173 is a bounded toy gate for the structured compact route. It checks:

- finite-field phase equivalence between structured dense MAT and compact
  application through a SAB-like CMUX/NCMUX schedule;
- a body-cross negative control that compact must fail to represent;
- a toy variance comparison for omitting logical zero body-cross encryptions.

This does not grant implementation permission. Security reduction and compact
closed-state API remain open.

## Gate Summary

{table(summary, summary_fields)}

## Equation Model

{table(equations, equation_fields)}

## Phase Toy Sample

{table(phase_rows[:12], phase_fields)}

Full phase results are in `{rel(PHASE_CSV)}`.

## Noise Toy Sample

{table(noise_rows[:12], noise_fields)}

Full noise results are in `{rel(NOISE_CSV)}`.

## Proof Status

{table(proof_rows, proof_fields)}

## Next Queue

{table(next_rows, next_fields)}
""")

    write_text_lf(PLAN_MD, f"""# Stage173 Validation Plan

Goal: advance structured compact MAT-SAB without falling into pure theory or
premature implementation.

Protocol:

- field: `{PRIME}`;
- r values: `{','.join(str(r) for r in R_VALUES)}`;
- trials per r: `{TRIALS}`;
- SAB-like toy schedule: `in_N={IN_N}`, `r_prec={R_PREC}`;
- phase gate: compact and structured dense outputs must match exactly;
- negative gate: an injected body-cross term must create a mismatch;
- noise gate: compact omitted-zero toy variance must be no larger than dense
  zero-padded toy variance.

Failure handling:

- phase failure blocks compact route;
- noise failure blocks compact route;
- pass keeps the route alive but does not permit implementation or paper claim.
""")

    write_text_lf(THEORY_MD, """# Stage173 Structured Compact Phase/Noise Model

The toy model uses vector phases over a finite field:

```text
x = (x_0, x_1, ..., x_r)
out = addend + M(rhs - addend)
```

The compact selector is exact only for structured matrices:

```text
M[0,*] arbitrary
M[q,0] and M[q,q] arbitrary
M[q,j] = 0 for q != j and q,j > 0
```

The finite schedule applies CMUX/NCMUX-like updates over `in_N=16` slots and
`r_prec=4` bits. This is enough to catch algebraic cross-lane mistakes, but it
is not a formal proof over torus polynomials or RLWE ciphertext distributions.

The noise toy compares dense zero-padded keys, where encrypted zero cross terms
still contribute key noise, against compact omission of those logical zeros. It
does not prove security of omitting public ciphertext components.
""")

    write_text_lf(VARIANT_MD, f"""# Structured Compact Phase/Noise Toy Variant

Decision:

```text
{decision}
```

Passed scope:

```text
finite-field phase toy
zero-cross negative control
toy variance comparison
```

Still blocked:

```text
security reduction
closed-state production API
full SAB implementation
complete-SAB benchmark
paper-level novelty claim
```
""")


def update_global_docs(decision: str) -> None:
    append_once(ROADMAP_MD, "## Stage 173: Structured Compact Phase/Noise Toy", f"""
## Stage 173: Structured Compact Phase/Noise Toy

Goal:

```text
Run finite-field phase propagation and noise toy gates for the structured
compact MAT-SAB route.
```

Status:

```text
Completed. Stage173 records {decision}. The route passes finite/toy checks but
does not yet have implementation permission because security and API proof
obligations remain open.
```
""")
    append_once(GOAL_MD, "Stage173 records structured compact phase/noise toy", f"""
Stage173 records structured compact phase/noise toy evidence. Decision:
`{decision}`. This keeps the compact route alive as a bounded algorithmic path,
but does not permit implementation or paper claims.
""")
    append_once(CURRENT_GOAL_MD, "79. Treat Stage173 as finite phase/noise toy evidence", f"""
79. Treat Stage173 as finite phase/noise toy evidence:
    `{decision}`. It improves the proof-route evidence for structured compact
    MAT-SAB while keeping security/API/full-SAB claims blocked.
""")
    append_once(HYPOTHESIS_YAML, "id: H99_structured_compact_phase_noise_toy", f"""
  - id: H99_structured_compact_phase_noise_toy
    statement: >
      Under explicit zero body-cross constraints, structured compact MAT-SAB
      should preserve finite-field CMUX/NCMUX phase propagation and should not
      increase toy variance relative to dense zero-padded selectors.
    mechanism: >
      Compact application keeps the shared output row and each body's
      shared-input plus diagonal term; omitted body-cross terms are logical
      zeros. A finite schedule checks phase equivalence and a variance toy
      checks whether omitting zero encryptions can be noise-neutral or better.
    status: stage173_structured_compact_phase_noise_toy
    evidence: docs/stage173_structured_compact_phase_noise_toy.md; experiments/stage173_structured_compact_phase_noise_toy_plan.md; theory_checks/stage173_structured_compact_phase_noise_model.md; repro/stage173_structured_compact_phase_noise_toy/summary.csv
    current_decision: >
      {decision}
    failure_criteria:
      - finite-field structured compact phase differs from structured dense
      - body-cross negative control does not mismatch
      - compact omitted-zero toy variance exceeds dense zero-padded variance
      - toy evidence is used as implementation permission or paper novelty
""")
    append_once(RUN_LOG, "stage173-structured-compact-phase-noise-toy-001", f"""
stage173-structured-compact-phase-noise-toy-001,2026-07-04,{git_head()},Stage 173,analysis,python scripts/build_stage173_structured_compact_phase_noise_toy.py,r=2/4/6; field={PRIME}; trials={TRIALS}; in_N={IN_N}; r_prec={R_PREC},seed-{SEED},{decision},Structured compact finite phase/noise toy gate.,repro/stage173_structured_compact_phase_noise_toy
""")
    append_once(MANIFEST, "stage173_structured_compact_phase_noise_toy", f"""
- stage173_structured_compact_phase_noise_toy: `{decision}`
  - `docs/stage173_structured_compact_phase_noise_toy.md`
  - `experiments/stage173_structured_compact_phase_noise_toy_plan.md`
  - `theory_checks/stage173_structured_compact_phase_noise_model.md`
  - `algorithm_variants/mat_rlwe_sab_structured_compact_phase_noise_toy.md`
  - `repro/stage173_structured_compact_phase_noise_toy/`
""")
    append_once(CHECKLIST, "Stage173 structured compact phase/noise toy pack recorded", """
- [x] Stage173 structured compact phase/noise toy pack recorded.
""")


def main() -> None:
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    equations = build_equations()
    phase_rows = build_phase_results()
    noise_rows = build_noise_results()
    proof_rows = build_proof_status(phase_rows, noise_rows)
    decision = decide(phase_rows, noise_rows)
    next_rows = build_next_queue(decision)
    summary = build_summary(decision, phase_rows, noise_rows, proof_rows)

    write_csv(EQUATIONS_CSV, equations, ["object", "equation", "meaning"])
    write_csv(PHASE_CSV, phase_rows, ["r", "trial", "field_prime", "in_N", "r_prec", "checked_components", "structured_mismatches", "negative_cross_mismatches", "status"])
    write_csv(NOISE_CSV, noise_rows, ["r", "trial", "input_variance", "key_noise_variance", "dense_zero_padded_avg_variance", "compact_omitted_zero_avg_variance", "compact_over_dense", "status"])
    write_csv(PROOF_CSV, proof_rows, ["obligation", "stage173_status", "remaining_gap", "implementation_permission"])
    write_csv(NEXT_CSV, next_rows, ["priority", "stage", "name", "entry_condition", "gate", "failure_rule"])
    write_csv(SUMMARY_CSV, summary, ["gate", "status", "metric", "value", "evidence", "detail", "next_action"])

    write_docs(decision, summary, equations, phase_rows, noise_rows, proof_rows, next_rows)
    update_global_docs(decision)
    artifact_index([
        SUMMARY_CSV,
        EQUATIONS_CSV,
        PHASE_CSV,
        NOISE_CSV,
        PROOF_CSV,
        NEXT_CSV,
        ARTIFACT_CSV,
        OUT_MD,
        PLAN_MD,
        THEORY_MD,
        VARIANT_MD,
    ])
    print(decision)


if __name__ == "__main__":
    main()
