"""Stage249: structured compact distribution/security preflight.

This stage consumes the Stage248 finite algebra pass and prior Stage201/202
distribution/semantic probes.  It decides whether structured compact can enter
production SAB implementation.  The expected strict outcome is conservative:
simple compact-saving public patterns are distinguishable, dummy random padding
only reaches proof-only status, and no production compact route is admitted.
"""

from __future__ import annotations

import csv
import hashlib
import subprocess
from datetime import date
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "repro" / "stage249_structured_compact_distribution_security"

INPUTS = {
    "stage248_proof_gate": ROOT / "repro" / "stage248_structured_compact_finite_probe" / "proof_gate.csv",
    "stage248_security_gap": ROOT / "repro" / "stage248_structured_compact_finite_probe" / "security_gap_matrix.csv",
    "stage201_candidate_matrix": ROOT / "repro" / "stage201_structured_selector_distribution_probe" / "candidate_matrix.csv",
    "stage201_distribution_probe": ROOT / "repro" / "stage201_structured_selector_distribution_probe" / "distribution_probe.csv",
    "stage201_proof_gate": ROOT / "repro" / "stage201_structured_selector_distribution_probe" / "proof_gate.csv",
    "stage202_summary": ROOT / "repro" / "stage202_dummy_padding_semantic_probe" / "summary.csv",
    "stage202_resource_model": ROOT / "repro" / "stage202_dummy_padding_semantic_probe" / "resource_model.csv",
    "stage202_semantic_probe": ROOT / "repro" / "stage202_dummy_padding_semantic_probe" / "semantic_probe.csv",
}

DOC = ROOT / "docs" / "stage249_structured_compact_distribution_security.md"
PLAN = ROOT / "experiments" / "stage249_structured_compact_distribution_security_plan.md"
THEORY = ROOT / "theory_checks" / "stage249_structured_compact_security_boundary.md"
VARIANT = ROOT / "algorithm_variants" / "mat_rlwe_sab_stage249_structured_compact_security.md"

INPUT_STATUS = OUT / "input_status.csv"
DISTRIBUTION = OUT / "distribution_security_matrix.csv"
SEMANTIC = OUT / "semantic_security_matrix.csv"
VALUE = OUT / "value_matrix.csv"
CLAIM = OUT / "claim_boundary.csv"
GATES = OUT / "proof_gate.csv"
NEXT = OUT / "next_stage_queue.csv"
REPORT = OUT / "stage249_report.md"
REPRO_CMDS = OUT / "reproduction_commands.md"
ARTIFACT = OUT / "artifact_index.csv"

ROADMAP = ROOT / "docs" / "roadmap_stage19_plus.md"
GOAL = ROOT / "docs" / "goal_sab_max_acceleration.md"
CURRENT_GOAL = ROOT / "docs" / "current_codex_goal_sab_completion.md"
HYPOTHESES = ROOT / "hypotheses" / "hypothesis_register.yaml"
RUN_LOG = ROOT / "repro" / "run_log.csv"
MANIFEST = ROOT / "repro" / "artifact_manifest.md"
CHECKLIST = ROOT / "repro" / "reproduction_checklist.md"

DECISION = "PASS_STAGE249_COMPACT_SECURITY_PREFLIGHT_FREEZE_PRODUCTION_ROUTE"


def rel(path: Path) -> str:
    return path.relative_to(ROOT).as_posix()


def run_git(args: list[str]) -> str:
    proc = subprocess.run(["git", *args], cwd=ROOT, text=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE, check=True)
    return proc.stdout.strip()


def read_csv(path: Path) -> list[dict[str, str]]:
    if not path.exists():
        return []
    with path.open("r", encoding="utf-8-sig", newline="") as f:
        return list(csv.DictReader(f))


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


def distribution_rows() -> list[dict[str, object]]:
    prior = {row["candidate"]: row for row in read_csv(INPUTS["stage201_candidate_matrix"])}
    rows = []
    candidates = [
        ("delete_body_cross_rows", "compact_saving_direct_delete"),
        ("deterministic_zero_padding", "dense_shape_zero_padding"),
        ("forced_shared_masks", "dense_shape_forced_mask_relation"),
        ("dummy_random_padding", "dense_shape_random_padding"),
    ]
    for candidate, label in candidates:
        row = prior.get(candidate, {})
        decision = row.get("decision", "MISSING")
        failures = row.get("public_pattern_failures", "")
        if decision.startswith("REJECT"):
            stage249 = "REJECT_PUBLICLY_DISTINGUISHABLE"
            production = "no"
            explanation = "Stage201 public-pattern distinguisher already rejects this route."
        elif decision.startswith("KEEP_PROOF_ONLY"):
            stage249 = "PROOF_ONLY_PATTERN_PASS"
            production = "no"
            explanation = "Simple public-pattern tests pass only by retaining dense public shape; no hybrid/keygen proof."
        else:
            stage249 = "UNKNOWN_BLOCKED"
            production = "no"
            explanation = "Missing prior distribution evidence."
        rows.append({
            "candidate": candidate,
            "label": label,
            "stage201_decision": decision,
            "public_pattern_failures": failures,
            "stage249_status": stage249,
            "production_permission": production,
            "explanation": explanation,
            "evidence": row.get("evidence", rel(INPUTS["stage201_candidate_matrix"])),
        })
    return rows


def semantic_rows() -> list[dict[str, object]]:
    summary = {row["gate"]: row for row in read_csv(INPUTS["stage202_summary"])}
    semantic_gate = summary.get("stage202_semantic_probe", {})
    resource_gate = summary.get("stage202_resource_gate", {})
    proof_gate = summary.get("stage202_proof_gate", {})
    return [
        {
            "check": "dummy_zero_semantics",
            "status": semantic_gate.get("status", "missing"),
            "meaning": "Toy semantic-zero dummy rows preserve the structured finite function.",
            "production_permission": "no",
            "missing_before_code": "ring-level SAB semantics, security proof, and keygen construction",
            "evidence": "repro/stage202_dummy_padding_semantic_probe/semantic_probe.csv",
        },
        {
            "check": "resource_value",
            "status": resource_gate.get("status", "missing"),
            "meaning": "Dummy padding preserves dense public size, so public key-size saving is not demonstrated.",
            "production_permission": "no",
            "missing_before_code": "complete-SAB T_bootstrap/r value after a proof-backed implementation",
            "evidence": "repro/stage202_dummy_padding_semantic_probe/resource_model.csv",
        },
        {
            "check": "production_proof_gate",
            "status": proof_gate.get("status", "missing"),
            "meaning": "Existing evidence is proof-only and does not authorize production compact SAB.",
            "production_permission": "no",
            "missing_before_code": proof_gate.get("next_action", "formal keygen/security/noise proof"),
            "evidence": "repro/stage202_dummy_padding_semantic_probe/summary.csv",
        },
    ]


def value_rows() -> list[dict[str, object]]:
    resource = read_csv(INPUTS["stage202_resource_model"])
    rows = []
    for row in resource:
        rows.append({
            "r": row.get("r", ""),
            "dense_public_rows_per_T": row.get("dense_public_rows_per_T", ""),
            "active_semantic_rows_per_T": row.get("active_semantic_rows_per_T", ""),
            "inactive_dummy_rows_per_T": row.get("inactive_dummy_rows_per_T", ""),
            "public_row_saving_vs_dense": row.get("public_row_saving_vs_dense", ""),
            "semantic_skip_potential": row.get("semantic_skip_potential", ""),
            "stage249_interpretation": "semantic skip potential exists, but public row count is dense and no production proof/benchmark exists",
            "claim_permission": "no_complete_sab_speedup_claim",
        })
    return rows


def claim_rows() -> list[dict[str, object]]:
    return [
        {
            "claim": "structured_compact_security",
            "status": "blocked",
            "allowed_wording": "Finite algebra and toy semantic probes identify a constrained proof route.",
            "forbidden_wording": "The structured compact route is secure or ready for SAB integration.",
            "evidence": rel(SEMANTIC),
        },
        {
            "claim": "structured_compact_speedup",
            "status": "denied",
            "allowed_wording": "No complete-SAB T_bootstrap/r speedup is claimed for compact routing.",
            "forbidden_wording": "Term-count or semantic-skip potential is a bootstrapping speedup.",
            "evidence": rel(VALUE),
        },
        {
            "claim": "production_permission",
            "status": "freeze_compact_production_route",
            "allowed_wording": "Compact production work is frozen until a formal distribution/keygen/security proof exists.",
            "forbidden_wording": "Implement compact SAB hot path now.",
            "evidence": rel(DISTRIBUTION),
        },
        {
            "claim": "next_research_route",
            "status": "route_to_exact_lower_bound_or_nonbinary_preflight",
            "allowed_wording": "Proceed with exact dense lower-bound gap analysis or non-binary selector semantics.",
            "forbidden_wording": "Continue compact theory without a new proof artifact.",
            "evidence": rel(NEXT),
        },
    ]


def gate_rows(inputs, distribution, semantic, value, claims) -> list[dict[str, object]]:
    inputs_ok = all(row["status"] == "present" for row in inputs)
    rejected_count = sum(1 for row in distribution if row["stage249_status"] == "REJECT_PUBLICLY_DISTINGUISHABLE")
    proof_only_count = sum(1 for row in distribution if row["stage249_status"] == "PROOF_ONLY_PATTERN_PASS")
    semantic_proof_only = any(row["check"] == "production_proof_gate" and row["status"] == "PROOF_ONLY" for row in semantic)
    no_public_saving = all(str(row["public_row_saving_vs_dense"]) == "0" for row in value)
    production_frozen = any(row["claim"] == "production_permission" and row["status"] == "freeze_compact_production_route" for row in claims)
    decision_ok = inputs_ok and rejected_count == 3 and proof_only_count == 1 and semantic_proof_only and no_public_saving and production_frozen
    return [
        {
            "gate": "G1_inputs",
            "status": "PASS" if inputs_ok else "FAIL",
            "metric": "required inputs",
            "value": "all present" if inputs_ok else "missing",
            "evidence": rel(INPUT_STATUS),
            "interpretation": "Stage249 consumes Stage248 plus prior distribution/semantic probes.",
        },
        {
            "gate": "G2_distribution_public_pattern",
            "status": "PASS_BLOCKING_DISTINGUISHERS_RECORDED" if rejected_count == 3 and proof_only_count == 1 else "FAIL",
            "metric": "rejected/proof_only candidates",
            "value": f"rejected={rejected_count};proof_only={proof_only_count}",
            "evidence": rel(DISTRIBUTION),
            "interpretation": "Compact-saving public distributions are distinguishable; dummy random padding is proof-only.",
        },
        {
            "gate": "G3_semantic_security",
            "status": "PASS_PROOF_ONLY_NOT_SECURITY" if semantic_proof_only else "FAIL",
            "metric": "Stage202 proof gate",
            "value": "proof_only",
            "evidence": rel(SEMANTIC),
            "interpretation": "Toy semantic-zero padding does not close keygen/security/ring-noise obligations.",
        },
        {
            "gate": "G4_value_metric",
            "status": "PASS_NO_COMPACT_SPEEDUP_CLAIM" if no_public_saving else "FAIL",
            "metric": "public row saving",
            "value": "0 for recorded r rows",
            "evidence": rel(VALUE),
            "interpretation": "Dummy padding has semantic skip potential but no public key-size saving or complete-SAB timing.",
        },
        {
            "gate": "G5_claim_boundary",
            "status": "PASS_FREEZE_PRODUCTION_COMPACT" if production_frozen else "FAIL",
            "metric": "production permission",
            "value": "no",
            "evidence": rel(CLAIM),
            "interpretation": "No compact production SAB integration is allowed from current evidence.",
        },
        {
            "gate": "G6_stage249_decision",
            "status": DECISION if decision_ok else "FAIL_STAGE249_COMPACT_SECURITY_PREFLIGHT",
            "metric": "decision",
            "value": DECISION if decision_ok else "FAIL_STAGE249_COMPACT_SECURITY_PREFLIGHT",
            "evidence": rel(GATES),
            "interpretation": "Freeze compact production route; proceed to exact lower-bound gap or non-binary semantics.",
        },
    ]


def next_rows() -> list[dict[str, object]]:
    return [
        {
            "priority": "P0",
            "route": "stage250_exact_dense_lower_bound_gap_refresh",
            "entry_condition": "Compact production route is frozen by Stage249; optimality remains open.",
            "gate": "measurable lower-bound components tied to exact dense implementation counters/assembly",
            "status": "selected_next",
            "failure_action": "keep measured engineering improvement wording only",
            "evidence": "theory_checks/mat_rlwe_sab_amortized_optimality.md",
        },
        {
            "priority": "P1",
            "route": "stage251_nonbinary_selector_semantics_preflight",
            "entry_condition": "Non-binary PVW-SAB support is desired.",
            "gate": "ternary/include-zero selector semantics and staged equivalence before implementation",
            "status": "blocked_until_design",
            "failure_action": "keep non-binary PVW unsupported",
            "evidence": "repro/stage229_parameter_generalization_matrix/coverage_gaps.csv",
        },
        {
            "priority": "P2",
            "route": "compact_route_reopen",
            "entry_condition": "A formal distribution/keygen/security proof artifact is supplied.",
            "gate": "hybrid/simulation proof plus ring-level noise recurrence before any code",
            "status": "frozen_until_new_proof",
            "failure_action": "do not spend further theory-only iterations on compact route",
            "evidence": rel(CLAIM),
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


def write_docs(inputs, distribution, semantic, value, claims, gates, nextq, head: str) -> None:
    write_text(DOC, f"""# Stage249 Structured Compact Distribution/Security Preflight

Decision: `{gates[-1]["status"]}`.

Stage249 tests whether Stage248's constrained compact algebra can move toward
production SAB implementation. It cannot: compact-saving public patterns are
distinguishable, and the only public-pattern survivor uses dummy random padding
that keeps dense public size and remains proof-only.

## Distribution Matrix

{table(distribution, ["candidate", "label", "stage201_decision", "public_pattern_failures", "stage249_status", "production_permission", "explanation", "evidence"])}

## Semantic/Security Matrix

{table(semantic, ["check", "status", "meaning", "production_permission", "missing_before_code", "evidence"])}

## Value Matrix

{table(value, ["r", "dense_public_rows_per_T", "active_semantic_rows_per_T", "inactive_dummy_rows_per_T", "public_row_saving_vs_dense", "semantic_skip_potential", "stage249_interpretation", "claim_permission"])}

## Claim Boundary

{table(claims, ["claim", "status", "allowed_wording", "forbidden_wording", "evidence"])}

## Proof Gates

{table(gates, ["gate", "status", "metric", "value", "evidence", "interpretation"])}

## Next Queue

{table(nextq, ["priority", "route", "entry_condition", "gate", "status", "failure_action", "evidence"])}

## Inputs

{table(inputs, ["input_id", "path", "status", "bytes"])}

Generated from head `{head}`.
""")
    write_text(REPORT, f"""# Stage249 Report

Decision: `{gates[-1]["status"]}`.

The structured compact production route is frozen. Three compact-saving
distribution candidates are publicly distinguishable; dummy random padding
passes simple public-pattern tests and toy semantic-zero checks, but it keeps
dense public row count and lacks formal keygen/security/ring-noise proof. The
next non-theory-loop route is exact dense lower-bound gap analysis or a separate
non-binary selector semantics preflight.
""")
    write_text(PLAN, """# Stage249 Structured Compact Distribution/Security Plan

## Objective

Determine whether the structured compact proof prototype can enter production
SAB implementation.

## Gates

- Public distribution: compact-saving candidates must not be distinguishable.
- Semantic correctness: dummy rows must be semantic zero beyond toy finite
  probes.
- Security/keygen: formal distribution and reduction/simulation argument must
  exist.
- Value metric: no complete-SAB `T_bootstrap/r` claim without implementation
  and repeated A/B timing.

## Stop Rule

If all production permissions remain `no`, freeze compact production work and
route to exact dense lower-bound gap or non-binary selector semantics.
""")
    write_text(THEORY, """# Stage249 Structured Compact Security Boundary

Stage248 shows that off-lane-zero compact algebra is internally consistent for
a constrained finite model. Stage249 asks whether that constrained selector
distribution can be used in production.

Current answer: no.

Reasons:

- direct compact-saving public patterns are distinguishable;
- deterministic zero padding and forced mask relations are distinguishable;
- dummy random padding hides simple public patterns only by keeping dense public
  shape;
- toy semantic-zero equivalence does not prove keygen security, ring-level
  noise, or complete-SAB value.

This freezes the compact production route until a new formal distribution and
keygen/security proof artifact exists.
""")
    write_text(VARIANT, """# MAT-RLWE SAB Stage249 Compact Security Preflight

## Summary

- Parent algorithm: PVW/MAT-SAB for 2025/686 sparse amortized bootstrapping.
- Focused module: structured compact selector/key distribution.
- Optimization target: future `T_bootstrap/r`, not measured in Stage249.
- Status labels: `production_frozen`, `proof_only_dummy_padding`,
  `public_distinguishers_recorded`.
- Main hypothesis: structured compact can proceed only if selector distribution
  and keygen security are proven; current evidence does not prove them.

## Pseudocode

```text
Input: Stage201 distribution probes, Stage202 semantic probes, Stage248 algebra proof.
Output: production permission decision.
1. Reject candidates with public distinguishers.
2. Keep dummy random padding as proof-only if semantic toy checks pass.
3. Deny production if keygen/security/ring-noise proofs are absent.
4. Route next work away from compact production implementation.
```

## Paper Contribution Candidate

`[negative result][do not overclaim]` Compact algebra has a constrained proof
route, but current selector distributions do not justify production SAB
integration or bootstrapping speedup claims.
""")
    write_text(REPRO_CMDS, f"""# Stage249 Reproduction Commands

```text
python scripts/build_stage249_structured_compact_distribution_security.py
python -m py_compile scripts/build_stage249_structured_compact_distribution_security.py
```

Decision: `{gates[-1]["status"]}`.
""")


def update_project_files(head: str, decision: str) -> None:
    append_once(ROADMAP, "## Stage 249: Structured Compact Distribution/Security Preflight", f"""
## Stage 249: Structured Compact Distribution/Security Preflight

Goal:

```text
Decide whether Stage248's structured compact proof prototype can enter
production SAB implementation.
```

Status:

```text
Generated from input head `{head}` with `{decision}`. Compact-saving public
distributions are distinguishable, and the only public-pattern survivor uses
dummy random padding with dense public size and proof-only semantics. Compact
production integration is frozen until a formal distribution/keygen/security
proof exists.
```
""")
    append_once(GOAL, "Stage249 structured compact distribution/security preflight", f"""
- Stage249 structured compact distribution/security preflight records
  `{decision}`: Stage248's compact algebra does not authorize production SAB.
  Compact-saving public distributions are distinguishable; dummy random padding
  remains proof-only and has no complete-SAB `T_bootstrap/r` claim.
""")
    append_once(CURRENT_GOAL, "### Stage249 structured compact distribution/security preflight", f"""
### Stage249 structured compact distribution/security preflight

`{decision}` freezes the compact production route until a formal selector
distribution/keygen/security proof exists. The active goal remains open for
exact dense lower-bound gap analysis, non-binary selector semantics, and final
paper/citation closure.
""")
    append_once(HYPOTHESES, "H10_stage249_structured_compact_distribution_security:", f"""
H10_stage249_structured_compact_distribution_security:
  status: compact_production_route_frozen
  evidence:
    - repro/stage249_structured_compact_distribution_security/distribution_security_matrix.csv
    - repro/stage249_structured_compact_distribution_security/semantic_security_matrix.csv
    - repro/stage249_structured_compact_distribution_security/value_matrix.csv
    - repro/stage249_structured_compact_distribution_security/proof_gate.csv
    - docs/stage249_structured_compact_distribution_security.md
  conclusion: >
    Stage249 records {decision}. Direct compact-saving public distributions
    are distinguishable, while dummy random padding remains proof-only, keeps
    dense public size, and lacks keygen/security/ring-noise proofs. No compact
    production SAB implementation or speedup claim is admitted.
""")
    append_once(RUN_LOG, "stage249-structured-compact-distribution-security-001", f"""stage249-structured-compact-distribution-security-001,{date.today().isoformat()},{head},Stage 249,security_preflight,"python scripts/build_stage249_structured_compact_distribution_security.py","Stage248 + Stage201/202 distribution/semantic probes",n/a,{decision},"Compact production route frozen; only proof-only dummy padding remains.",docs/stage249_structured_compact_distribution_security.md; repro/stage249_structured_compact_distribution_security/proof_gate.csv
""")
    append_once(MANIFEST, "- stage249_structured_compact_distribution_security:", """
- stage249_structured_compact_distribution_security:
  - `docs/stage249_structured_compact_distribution_security.md`
  - `experiments/stage249_structured_compact_distribution_security_plan.md`
  - `theory_checks/stage249_structured_compact_security_boundary.md`
  - `algorithm_variants/mat_rlwe_sab_stage249_structured_compact_security.md`
  - `scripts/build_stage249_structured_compact_distribution_security.py`
  - `repro/stage249_structured_compact_distribution_security/`
""")
    append_once(CHECKLIST, "Stage249 structured compact distribution/security preflight freezes production route", f"""
- [x] Stage249 structured compact distribution/security preflight freezes production route `{decision}`.
""")


def main() -> None:
    OUT.mkdir(parents=True, exist_ok=True)
    head = run_git(["rev-parse", "--short", "HEAD"])
    inputs = input_rows()
    distribution = distribution_rows()
    semantic = semantic_rows()
    value = value_rows()
    claims = claim_rows()
    gates = gate_rows(inputs, distribution, semantic, value, claims)
    nextq = next_rows()

    write_csv(INPUT_STATUS, inputs, ["input_id", "path", "status", "bytes"])
    write_csv(DISTRIBUTION, distribution, ["candidate", "label", "stage201_decision", "public_pattern_failures", "stage249_status", "production_permission", "explanation", "evidence"])
    write_csv(SEMANTIC, semantic, ["check", "status", "meaning", "production_permission", "missing_before_code", "evidence"])
    write_csv(VALUE, value, ["r", "dense_public_rows_per_T", "active_semantic_rows_per_T", "inactive_dummy_rows_per_T", "public_row_saving_vs_dense", "semantic_skip_potential", "stage249_interpretation", "claim_permission"])
    write_csv(CLAIM, claims, ["claim", "status", "allowed_wording", "forbidden_wording", "evidence"])
    write_csv(GATES, gates, ["gate", "status", "metric", "value", "evidence", "interpretation"])
    write_csv(NEXT, nextq, ["priority", "route", "entry_condition", "gate", "status", "failure_action", "evidence"])

    write_docs(inputs, distribution, semantic, value, claims, gates, nextq, head)
    artifacts = [DOC, PLAN, THEORY, VARIANT, INPUT_STATUS, DISTRIBUTION, SEMANTIC, VALUE, CLAIM, GATES, NEXT, REPORT, REPRO_CMDS]
    write_csv(ARTIFACT, artifact_rows(artifacts), ["artifact", "exists", "sha256", "bytes"])
    update_project_files(head, gates[-1]["status"])
    print(f"Stage249 report: {rel(DOC)}")
    print(f"Stage249 decision: {gates[-1]['status']}")


if __name__ == "__main__":
    main()
