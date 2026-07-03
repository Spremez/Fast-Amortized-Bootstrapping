#!/usr/bin/env python3
"""Stage171: structured compact keygen feasibility card."""

from __future__ import annotations

import csv
import hashlib
import random
import subprocess
from pathlib import Path
from typing import Dict, Iterable, List


ROOT = Path(__file__).resolve().parents[1]
OUT_DIR = ROOT / "repro" / "stage171_structured_compact_keygen_feasibility"

SUMMARY_CSV = OUT_DIR / "summary.csv"
CONSTRAINTS_CSV = OUT_DIR / "algebraic_constraints.csv"
PHASE_LEVELS_CSV = OUT_DIR / "phase_claim_levels.csv"
FINITE_CSV = OUT_DIR / "finite_field_structured_checks.csv"
PROOF_CSV = OUT_DIR / "proof_obligations.csv"
PROJECTION_CSV = OUT_DIR / "speed_projection.csv"
NEXT_CSV = OUT_DIR / "next_stage_queue.csv"
ARTIFACT_CSV = OUT_DIR / "artifact_index.csv"

OUT_MD = ROOT / "docs" / "stage171_structured_compact_keygen_feasibility.md"
PLAN_MD = ROOT / "experiments" / "stage171_structured_compact_keygen_feasibility_plan.md"
THEORY_MD = ROOT / "theory_checks" / "stage171_structured_compact_keygen_model.md"
VARIANT_MD = ROOT / "algorithm_variants" / "mat_rlwe_sab_structured_compact_keygen_feasibility.md"

ROADMAP_MD = ROOT / "docs" / "roadmap_stage19_plus.md"
GOAL_MD = ROOT / "docs" / "goal_sab_max_acceleration.md"
CURRENT_GOAL_MD = ROOT / "docs" / "current_codex_goal_sab_completion.md"
HYPOTHESIS_YAML = ROOT / "hypotheses" / "hypothesis_register.yaml"
RUN_LOG = ROOT / "repro" / "run_log.csv"
MANIFEST = ROOT / "repro" / "artifact_manifest.md"
CHECKLIST = ROOT / "repro" / "reproduction_checklist.md"

STAGE170_RUN = ROOT / "repro" / "stage170_native_split_counter_microbench" / "run_metrics.csv"

PRIME = 65537
SEED = 171
TRIALS = 16
R_VALUES = (2, 4, 6, 8)
TARGET_R = 6


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


def read_csv(path: Path) -> List[Dict[str, str]]:
    if not path.exists():
        return []
    with path.open(newline="", encoding="utf-8-sig") as f:
        return list(csv.DictReader(f))


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


def build_constraints() -> List[Dict[str, str]]:
    rows = []
    for r in R_VALUES:
        m = 1 + r
        dense_terms = m * m
        structured_terms = 1 + 3 * r
        omitted = r * (r - 1)
        rows.append({
            "r": str(r),
            "state_polys": str(m),
            "dense_terms": str(dense_terms),
            "structured_terms": str(structured_terms),
            "omitted_body_cross_terms": str(omitted),
            "term_reduction_factor": f"{dense_terms / structured_terms:.9f}",
            "required_constraint": "M[q,j]=0 for q!=j and q,j>0 at the logical selector level",
            "status": "STRUCTURED_ONLY_NOT_GENERIC",
        })
    return rows


def structured_matrix(rng: random.Random, r: int) -> List[List[int]]:
    m = 1 + r
    matrix = [[0 for _ in range(m)] for _ in range(m)]
    for col in range(m):
        matrix[0][col] = rng.randrange(1, PRIME)
    for row in range(1, m):
        matrix[row][0] = rng.randrange(1, PRIME)
        matrix[row][row] = rng.randrange(1, PRIME)
    return matrix


def dense_matrix(rng: random.Random, r: int) -> List[List[int]]:
    m = 1 + r
    return [[rng.randrange(1, PRIME) for _ in range(m)] for _ in range(m)]


def compact_projection(matrix: List[List[int]]) -> List[List[int]]:
    m = len(matrix)
    out = [[0 for _ in range(m)] for _ in range(m)]
    for col in range(m):
        out[0][col] = matrix[0][col]
    for row in range(1, m):
        out[row][0] = matrix[row][0]
        out[row][row] = matrix[row][row]
    return out


def mismatches(a: List[List[int]], b: List[List[int]]) -> int:
    return sum(1 for i in range(len(a)) for j in range(len(a)) if a[i][j] != b[i][j])


def build_finite_checks() -> List[Dict[str, str]]:
    rng = random.Random(SEED)
    rows = []
    for r in R_VALUES:
        for trial in range(TRIALS):
            structured = structured_matrix(rng, r)
            structured_projected = compact_projection(structured)
            dense = dense_matrix(rng, r)
            dense_projected = compact_projection(dense)
            structured_mismatch = mismatches(structured, structured_projected)
            dense_mismatch = mismatches(dense, dense_projected)
            rows.append({
                "r": str(r),
                "trial": str(trial),
                "field_prime": str(PRIME),
                "structured_mismatches": str(structured_mismatch),
                "dense_mismatches": str(dense_mismatch),
                "expected_dense_missing": str(r * (r - 1)),
                "status": "PASS_STRUCTURED_EXACT_DENSE_BLOCKED" if structured_mismatch == 0 and dense_mismatch == r * (r - 1) else "FAIL",
            })
    return rows


def build_phase_levels() -> List[Dict[str, str]]:
    return [
        {
            "level": "ciphertext_exact_dense_MAT",
            "claim": "Compact lane-local data equals the existing dense MAT ciphertext map.",
            "status": "BLOCKED_BY_STAGE166",
            "reason": "Generic dense encrypted selector includes body-to-body cross terms.",
            "allowed_next": "Do not replace dense MAT with compact storage under this claim.",
        },
        {
            "level": "logical_selector_exact",
            "claim": "A new structured keygen enforces zero logical body cross terms.",
            "status": "FINITE_FIELD_FEASIBLE",
            "reason": "Stage171 finite checks show compact projection is exact under explicit structural constraints.",
            "allowed_next": "Write formal keygen, phase, and noise equations before implementation.",
        },
        {
            "level": "phase_correct_under_decryption",
            "claim": "Omitting encryptions of logical zero cross terms preserves decrypted message and changes only noise/distribution.",
            "status": "PROOF_REQUIRED",
            "reason": "Dropping encrypted zero samples changes bootstrapping-key distribution and noise accounting.",
            "allowed_next": "Run finite/noise toy checks only after equations specify the distribution.",
        },
        {
            "level": "complete_SAB_speedup",
            "claim": "Structured compact keygen accelerates full SAB.",
            "status": "BLOCKED_IMPLEMENTATION",
            "reason": "No structured keygen, SAB integration, correctness/noise, or full A/B benchmark exists.",
            "allowed_next": "Keep complete-SAB speedup claims tied to Stage169 until this route is implemented and measured.",
        },
    ]


def build_proof_obligations() -> List[Dict[str, str]]:
    return [
        {
            "obligation": "keygen_distribution",
            "required_result": "Define a bootstrapping-key distribution with zero logical body cross terms and compact public representation.",
            "blocking_question": "Are omitted zero-encryption samples safely public zeros, or must they be simulated under RLWE?",
            "gate": "formal equations plus toy sampler; no SAB code before this passes",
            "status": "OPEN",
        },
        {
            "obligation": "phase_invariant",
            "required_result": "For every CMUX/NCMUX step, prove each output lane decrypts to the same logical phase as scalar SAB for independent LUT lanes.",
            "blocking_question": "Does RGSW monomial rotation preserve the structured selector constraint at every sparse schedule step?",
            "gate": "symbolic phase derivation plus finite-field phase test",
            "status": "OPEN",
        },
        {
            "obligation": "noise_accounting",
            "required_result": "Bound noise after deleting or resampling cross zero terms and compare with dense MAT baseline.",
            "blocking_question": "Does the structured distribution reduce noise, leave it comparable, or introduce correlations that hurt correctness?",
            "gate": "multi-seed noise simulation before full SAB benchmark",
            "status": "OPEN",
        },
        {
            "obligation": "security_reduction",
            "required_result": "State whether security follows from standard RLWE samples, a hybrid replacing zero encryptions, or a new structured assumption.",
            "blocking_question": "Can a distinguisher exploit missing body-to-body ciphertext components in the public bootstrapping key?",
            "gate": "written reduction or explicit assumption before paper-level novelty claim",
            "status": "OPEN",
        },
        {
            "obligation": "closed_state_API",
            "required_result": "Specify whether compact state remains a PVW_TMLWE-compatible closed state through SAB sparse_mul and extract.",
            "blocking_question": "Can from_DFT/extract consume the compact output without re-expanding to dense MAT?",
            "gate": "interface design and isolated phase equivalence test",
            "status": "OPEN",
        },
    ]


def stage170_us(variant: str) -> float:
    for row in read_csv(STAGE170_RUN):
        if row.get("variant") == variant and row.get("per_call_us"):
            return float(row["per_call_us"])
    return 0.0


def build_projection(constraints: List[Dict[str, str]]) -> List[Dict[str, str]]:
    mat_us = stage170_us("mat_ep_subdecomp")
    from_dft_us = stage170_us("from_dft_materialize")
    rows = []
    for row in constraints:
        r = int(row["r"])
        dense_terms = float(row["dense_terms"])
        structured_terms = float(row["structured_terms"])
        term_scale = structured_terms / dense_terms
        ideal_mat_us = mat_us * term_scale if r == TARGET_R else 0.0
        baseline_pair = mat_us + from_dft_us if r == TARGET_R else 0.0
        ideal_pair = ideal_mat_us + from_dft_us if r == TARGET_R else 0.0
        rows.append({
            "r": str(r),
            "dense_terms": row["dense_terms"],
            "structured_terms": row["structured_terms"],
            "term_reduction_factor": row["term_reduction_factor"],
            "stage170_mat_ep_us": f"{mat_us:.9f}" if r == TARGET_R else "",
            "stage170_from_dft_us": f"{from_dft_us:.9f}" if r == TARGET_R else "",
            "ideal_structured_mat_us": f"{ideal_mat_us:.9f}" if r == TARGET_R else "",
            "component_baseline_us": f"{baseline_pair:.9f}" if r == TARGET_R else "",
            "ideal_component_us": f"{ideal_pair:.9f}" if r == TARGET_R else "",
            "upper_component_speedup": f"{baseline_pair / ideal_pair:.9f}" if r == TARGET_R and ideal_pair else "",
            "scope": "upper-bound model only; excludes proof, keygen, from_DFT count, extract/KS, memory layout, and full SAB effects",
        })
    return rows


def build_next_queue() -> List[Dict[str, str]]:
    return [
        {
            "priority": "P0",
            "stage": "172",
            "name": "frontier closeout after Stage169/170/171",
            "entry_condition": "Stage171 keeps structured compact as proof route, not implementation-ready code.",
            "gate": "Refresh allowed claims, next engineering route, and proof-route decision boundary.",
            "failure_rule": "No final theoretical-optimality or compact-SAB claim without proof and full benchmark.",
        },
        {
            "priority": "P1",
            "stage": "173",
            "name": "structured compact formal phase/noise toy",
            "entry_condition": "Only if the project chooses to pursue a new keygen/security route.",
            "gate": "Write exact equations and finite/noise toy sampler for the structured compact distribution.",
            "failure_rule": "If equations do not close, reject compact route before implementation.",
        },
        {
            "priority": "P2",
            "stage": "174",
            "name": "from_DFT locality experiment",
            "entry_condition": "Stage170 shows from_DFT has high cache-miss and load/store pressure.",
            "gate": "Bounded microbench with layout/scratch changes and full-SAB A/B only if microbench wins.",
            "failure_rule": "Do not promote a backend-only improvement without complete-SAB endpoint.",
        },
    ]


def decide(finite_rows: List[Dict[str, str]], projection_rows: List[Dict[str, str]]) -> str:
    if not STAGE170_RUN.exists():
        return "BLOCKED_STAGE171_MISSING_STAGE170_INPUT"
    if any(row.get("status") != "PASS_STRUCTURED_EXACT_DENSE_BLOCKED" for row in finite_rows):
        return "FAIL_STAGE171_STRUCTURED_FINITE_CHECK"
    target_projection = next((row for row in projection_rows if row["r"] == str(TARGET_R)), {})
    if not target_projection.get("upper_component_speedup"):
        return "FAIL_STAGE171_PROJECTION_MISSING_TARGET_R"
    return "PASS_STAGE171_STRUCTURED_COMPACT_PROOF_ROUTE_NOT_IMPLEMENTATION_READY"


def build_summary(decision: str, finite_rows: List[Dict[str, str]], proof_rows: List[Dict[str, str]], projection_rows: List[Dict[str, str]]) -> List[Dict[str, str]]:
    target_projection = next((row for row in projection_rows if row["r"] == str(TARGET_R)), {})
    finite_pass = all(row.get("status") == "PASS_STRUCTURED_EXACT_DENSE_BLOCKED" for row in finite_rows)
    open_proofs = sum(1 for row in proof_rows if row.get("status") == "OPEN")
    return [
        {
            "gate": "stage171_inputs",
            "status": "PASS" if STAGE170_RUN.exists() else "BLOCKED",
            "metric": "stage170_run_metrics",
            "value": "present" if STAGE170_RUN.exists() else "missing",
            "evidence": rel(STAGE170_RUN),
            "detail": "Stage171 uses Stage170 component timings for bounded speed projection.",
            "next_action": "Do not compute projection without Stage170.",
        },
        {
            "gate": "stage171_structured_finite_check",
            "status": "PASS" if finite_pass else "FAIL",
            "metric": "finite_trials",
            "value": str(len(finite_rows)),
            "evidence": rel(FINITE_CSV),
            "detail": "Structured matrices project exactly; random dense matrices still expose missing cross terms.",
            "next_action": "Only structured keygen can reopen compact SAB.",
        },
        {
            "gate": "stage171_projection",
            "status": "PASS" if target_projection.get("upper_component_speedup") else "FAIL",
            "metric": "r6_upper_component_speedup",
            "value": target_projection.get("upper_component_speedup", ""),
            "evidence": rel(PROJECTION_CSV),
            "detail": "Projection assumes MAT EP scales with term count and from_DFT remains unchanged.",
            "next_action": "Treat as upper-bound routing evidence, not a benchmark result.",
        },
        {
            "gate": "stage171_proof_obligations",
            "status": "BLOCKED_PROOF",
            "metric": "open_obligations",
            "value": str(open_proofs),
            "evidence": rel(PROOF_CSV),
            "detail": "Keygen distribution, phase invariant, noise, security, and closed-state API remain open.",
            "next_action": "No compact SAB implementation or paper claim before these are resolved.",
        },
        {
            "gate": "stage171_decision",
            "status": decision,
            "metric": "structured_compact_route",
            "value": "proof_route_only",
            "evidence": rel(SUMMARY_CSV),
            "detail": "Stage171 converts compact optimization into bounded proof obligations instead of theory drift.",
            "next_action": "Run Stage172 closeout or explicitly choose Stage173 proof work.",
        },
    ]


def artifact_index(paths: List[Path]) -> None:
    rows = []
    for path in paths:
        rows.append({
            "path": rel(path),
            "exists": "yes" if path.exists() else "no",
            "sha256": sha256_file(path) if path.exists() and path.is_file() else "",
            "bytes": str(path.stat().st_size) if path.exists() and path.is_file() else "",
        })
    write_csv(ARTIFACT_CSV, rows, ["path", "exists", "sha256", "bytes"])


def write_docs(
    decision: str,
    summary: List[Dict[str, str]],
    constraints: List[Dict[str, str]],
    phase_levels: List[Dict[str, str]],
    finite_rows: List[Dict[str, str]],
    proof_rows: List[Dict[str, str]],
    projection_rows: List[Dict[str, str]],
    next_rows: List[Dict[str, str]],
) -> None:
    summary_fields = ["gate", "status", "metric", "value", "evidence", "detail", "next_action"]
    constraint_fields = ["r", "state_polys", "dense_terms", "structured_terms", "omitted_body_cross_terms", "term_reduction_factor", "required_constraint", "status"]
    phase_fields = ["level", "claim", "status", "reason", "allowed_next"]
    finite_fields = ["r", "trial", "field_prime", "structured_mismatches", "dense_mismatches", "expected_dense_missing", "status"]
    proof_fields = ["obligation", "required_result", "blocking_question", "gate", "status"]
    projection_fields = ["r", "dense_terms", "structured_terms", "term_reduction_factor", "stage170_mat_ep_us", "stage170_from_dft_us", "ideal_structured_mat_us", "component_baseline_us", "ideal_component_us", "upper_component_speedup", "scope"]
    next_fields = ["priority", "stage", "name", "entry_condition", "gate", "failure_rule"]

    write_text_lf(OUT_MD, f"""# Stage171 Structured Compact Keygen Feasibility

Decision: `{decision}`.

Stage171 is a bounded research gate. It does not implement compact SAB. It
separates three claims that were previously easy to mix:

- ciphertext-exact replacement of dense MAT: still blocked;
- structured logical selector compactness: finite-field feasible under explicit
  zero-cross constraints;
- secure/noise-bounded bootstrapping key distribution: open proof work.

The practical reason to keep this route alive is that r=6 dense MAT uses 49
selector terms while a structured compact map would use 19 logical terms. Using
Stage170's current component timings, the idealized r=6 component-only upper
bound is recorded in `speed_projection.csv`; it is not a benchmark.

## Gate Summary

{table(summary, summary_fields)}

## Algebraic Constraints

{table(constraints, constraint_fields)}

## Claim Levels

{table(phase_levels, phase_fields)}

## Finite Check Sample

{table(finite_rows[:12], finite_fields)}

Full finite checks are in `{rel(FINITE_CSV)}`.

## Proof Obligations

{table(proof_rows, proof_fields)}

## Speed Projection

{table(projection_rows, projection_fields)}

## Next Queue

{table(next_rows, next_fields)}
""")

    write_text_lf(PLAN_MD, """# Stage171 Validation Plan

Goal: decide whether compact/shared-output MAT-SAB is an implementation route
or only a new-proof route.

Procedure:

1. Restate the dense MAT versus structured compact term model.
2. Run finite-field checks showing structured matrices are compact-exact while
   random dense matrices remain blocked.
3. Split claim levels into ciphertext exactness, logical selector exactness,
   phase correctness, and complete-SAB speedup.
4. List proof obligations before any implementation.
5. Use Stage170 timings only for an upper-bound component projection.

Acceptance:

- structured finite checks pass for r=2/4/6/8;
- dense counterexamples remain nonzero;
- all proof obligations are explicit and blocking;
- no complete-SAB or theoretical-optimality claim is made.
""")

    write_text_lf(THEORY_MD, """# Stage171 Structured Compact Keygen Model

Let `m = 1 + r`. The current dense MAT external product represents a generic
`m x m` encrypted selector map. A compact structured map keeps:

```text
shared output: M[0, 0..r]
body q output: M[q,0] and M[q,q]
omitted: M[q,j] for q != j and q,j > 0
```

Thus the compact map is exact only when the logical selector satisfies:

```text
M[q,j] = 0 for q != j and q,j > 0.
```

This is not a drop-in replacement for the current dense encrypted selector.
It is a different keygen/distribution claim. The unresolved question is whether
omitted body-cross zero encryptions can be removed or simulated without
weakening security and while preserving SAB phase and noise bounds.

The Stage171 speed projection is deliberately limited. It assumes MAT EP cost
scales with selector term count and from_DFT cost stays fixed. That produces a
component upper bound, not a complete-SAB benchmark or lower bound.
""")

    write_text_lf(VARIANT_MD, f"""# Structured Compact Keygen Feasibility Route

This route is not implementation-ready.

Decision:

```text
{decision}
```

Allowed:

```text
Use structured compact as a proof-driven future algorithm route.
Use the r=6 term reduction and Stage170 projection as motivation.
```

Blocked:

```text
Replacing dense MAT production code.
Claiming full SAB acceleration from compact keygen.
Claiming theoretical optimality.
Claiming paper novelty without literature and proof.
```
""")


def update_global_docs(decision: str) -> None:
    append_once(ROADMAP_MD, "## Stage 171: Structured Compact Keygen Feasibility", f"""
## Stage 171: Structured Compact Keygen Feasibility

Goal:

```text
Decide whether shared-output/compact MAT-SAB is an implementation-ready route
or a bounded proof route requiring new keygen, phase, noise, and security work.
```

Status:

```text
Completed. Stage171 records {decision}. Structured compact is finite-field
feasible under zero-cross logical constraints but remains blocked for
production SAB until proof obligations close.
```
""")
    append_once(GOAL_MD, "Stage171 records structured compact keygen feasibility", f"""
Stage171 records structured compact keygen feasibility after Stage170.
Decision: `{decision}`. It keeps compact MAT-SAB as a proof-driven possible
algorithmic improvement and blocks implementation/claim escalation until
keygen, phase, noise, security, and closed-state API obligations are resolved.
""")
    append_once(CURRENT_GOAL_MD, "75. Treat Stage171 as structured compact proof-route gate", f"""
75. Treat Stage171 as structured compact proof-route gate:
    `{decision}`. It provides a bounded algebraic and Stage170-informed
    projection, not an implementation or final speedup claim.
""")
    append_once(HYPOTHESIS_YAML, "id: H95_structured_compact_keygen_feasibility", f"""
  - id: H95_structured_compact_keygen_feasibility
    statement: >
      A compact shared-output MAT-SAB route can only be exact under explicit
      structured logical selector constraints, and therefore remains a new
      keygen/security/noise proof route rather than a drop-in implementation
      optimization.
    mechanism: >
      The compact map keeps the shared output row plus each body's shared-input
      and diagonal terms, omitting body-to-body cross terms. Finite-field tests
      show exactness under zero-cross constraints and failure for generic dense
      selectors; Stage170 timings give only an upper-bound component projection.
    status: stage171_structured_compact_keygen_feasibility
    evidence: docs/stage171_structured_compact_keygen_feasibility.md; experiments/stage171_structured_compact_keygen_feasibility_plan.md; theory_checks/stage171_structured_compact_keygen_model.md; repro/stage171_structured_compact_keygen_feasibility/summary.csv
    current_decision: >
      {decision}
    failure_criteria:
      - structured finite-field matrices do not project exactly
      - compact route is implemented before keygen/phase/noise/security proof
      - Stage171 projection is reported as complete-SAB benchmark speedup
""")
    append_once(RUN_LOG, "stage171-structured-compact-keygen-feasibility-001", f"""
stage171-structured-compact-keygen-feasibility-001,2026-07-04,{git_head()},Stage 171,analysis,python scripts/build_stage171_structured_compact_keygen_feasibility.py,r=2/4/6/8; finite_field_prime={PRIME}; trials={TRIALS}; Stage170 projection,seed-{SEED},{decision},Structured compact keygen feasibility/proof-route gate.,repro/stage171_structured_compact_keygen_feasibility
""")
    append_once(MANIFEST, "stage171_structured_compact_keygen_feasibility", f"""
- stage171_structured_compact_keygen_feasibility: `{decision}`
  - `docs/stage171_structured_compact_keygen_feasibility.md`
  - `experiments/stage171_structured_compact_keygen_feasibility_plan.md`
  - `theory_checks/stage171_structured_compact_keygen_model.md`
  - `algorithm_variants/mat_rlwe_sab_structured_compact_keygen_feasibility.md`
  - `repro/stage171_structured_compact_keygen_feasibility/`
""")
    append_once(CHECKLIST, "Stage171 structured compact keygen feasibility pack recorded", """
- [x] Stage171 structured compact keygen feasibility pack recorded.
""")


def main() -> None:
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    constraints = build_constraints()
    finite_rows = build_finite_checks()
    phase_levels = build_phase_levels()
    proof_rows = build_proof_obligations()
    projection_rows = build_projection(constraints)
    next_rows = build_next_queue()
    decision = decide(finite_rows, projection_rows)
    summary = build_summary(decision, finite_rows, proof_rows, projection_rows)

    write_csv(CONSTRAINTS_CSV, constraints, ["r", "state_polys", "dense_terms", "structured_terms", "omitted_body_cross_terms", "term_reduction_factor", "required_constraint", "status"])
    write_csv(PHASE_LEVELS_CSV, phase_levels, ["level", "claim", "status", "reason", "allowed_next"])
    write_csv(FINITE_CSV, finite_rows, ["r", "trial", "field_prime", "structured_mismatches", "dense_mismatches", "expected_dense_missing", "status"])
    write_csv(PROOF_CSV, proof_rows, ["obligation", "required_result", "blocking_question", "gate", "status"])
    write_csv(PROJECTION_CSV, projection_rows, ["r", "dense_terms", "structured_terms", "term_reduction_factor", "stage170_mat_ep_us", "stage170_from_dft_us", "ideal_structured_mat_us", "component_baseline_us", "ideal_component_us", "upper_component_speedup", "scope"])
    write_csv(NEXT_CSV, next_rows, ["priority", "stage", "name", "entry_condition", "gate", "failure_rule"])
    write_csv(SUMMARY_CSV, summary, ["gate", "status", "metric", "value", "evidence", "detail", "next_action"])

    write_docs(decision, summary, constraints, phase_levels, finite_rows, proof_rows, projection_rows, next_rows)
    update_global_docs(decision)
    artifact_index([
        SUMMARY_CSV,
        CONSTRAINTS_CSV,
        PHASE_LEVELS_CSV,
        FINITE_CSV,
        PROOF_CSV,
        PROJECTION_CSV,
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
