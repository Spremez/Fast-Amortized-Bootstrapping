"""Stage246: broader algorithm admission gate for PVW/MAT-SAB.

This stage decides which broader-than-selected-binary directions may enter
future implementation.  It is intentionally not a speedup stage: candidates are
classified as baseline, blocked, rejected, or admitted only to proof/prototype
gates according to existing evidence.
"""

from __future__ import annotations

import csv
import hashlib
import subprocess
from datetime import date
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "repro" / "stage246_broader_algorithm_admission_gate"

INPUT_FILES = {
    "stage240_claim_audit": ROOT / "repro" / "stage240_scoped_latex_draft" / "claim_audit.csv",
    "stage245_counter_bridge": ROOT / "repro" / "stage245_current_head_counter_bridge" / "proof_gate.csv",
    "stage229_coverage_gaps": ROOT / "repro" / "stage229_parameter_generalization_matrix" / "coverage_gaps.csv",
    "stage229_claim_scope": ROOT / "repro" / "stage229_parameter_generalization_matrix" / "claim_scope.csv",
    "stage236_selected_binary": ROOT / "repro" / "stage236_set_2_3_4096_r4_highstat_slice" / "selected_binary_matrix_summary.csv",
    "stage166_compact_gate": ROOT / "repro" / "stage166_shared_output_compact_algebra_gate" / "summary.csv",
    "stage112_selector_gate": ROOT / "repro" / "stage112_selector_format_gate" / "summary.csv",
    "optimality_model": ROOT / "theory_checks" / "mat_rlwe_sab_amortized_optimality.md",
    "complexity_model": ROOT / "theory_checks" / "pvw_sab_complexity_model.md",
}

DOC = ROOT / "docs" / "stage246_broader_algorithm_admission_gate.md"
PLAN = ROOT / "experiments" / "stage246_broader_algorithm_admission_gate_plan.md"
THEORY = ROOT / "theory_checks" / "stage246_algorithm_admission_boundary.md"
VARIANT = ROOT / "algorithm_variants" / "mat_rlwe_sab_stage246_broader_algorithm_gate.md"

INPUT_STATUS = OUT / "input_status.csv"
CLAIM_BOUNDARY = OUT / "active_claim_boundary.csv"
CANDIDATES = OUT / "candidate_algorithm_matrix.csv"
PROOF_OBLIGATIONS = OUT / "proof_obligation_matrix.csv"
EXPERIMENT_GATES = OUT / "experiment_gate_matrix.csv"
STATS_REPRO = OUT / "stats_repro_gate.csv"
ADMISSION = OUT / "admission_decision.csv"
PROOF_GATE = OUT / "proof_gate.csv"
NEXT = OUT / "next_stage_queue.csv"
REPORT = OUT / "stage246_report.md"
REPRO_CMDS = OUT / "reproduction_commands.md"
ARTIFACT = OUT / "artifact_index.csv"

ROADMAP = ROOT / "docs" / "roadmap_stage19_plus.md"
GOAL = ROOT / "docs" / "goal_sab_max_acceleration.md"
CURRENT_GOAL = ROOT / "docs" / "current_codex_goal_sab_completion.md"
HYPOTHESES = ROOT / "hypotheses" / "hypothesis_register.yaml"
RUN_LOG = ROOT / "repro" / "run_log.csv"
MANIFEST = ROOT / "repro" / "artifact_manifest.md"
CHECKLIST = ROOT / "repro" / "reproduction_checklist.md"

DECISION = "PASS_STAGE246_BROADER_ALGORITHM_GATE_RECORDED_PROOF_PROTOTYPES_ONLY"


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
        for key, path in INPUT_FILES.items()
    ]


def claim_boundary_rows() -> list[dict[str, object]]:
    rows: list[dict[str, object]] = []
    for row in read_csv(INPUT_FILES["stage240_claim_audit"]):
        rows.append({
            "claim_id": row.get("claim_id", ""),
            "stage246_status": row.get("draft_status", ""),
            "safe_wording": row.get("safe_wording", ""),
            "blocked_wording": row.get("blocked_wording", ""),
            "evidence": row.get("evidence", ""),
        })
    rows.extend([
        {
            "claim_id": "C6_broader_algorithm_admission",
            "stage246_status": "DENY_PRODUCTION_PROMOTION_NOW",
            "safe_wording": "Broader routes are separated into proof prototypes and blocked claims.",
            "blocked_wording": "Do not claim non-binary PVW-SAB, compact PVW-SAB, all-parameter support, or theoretical optimality.",
            "evidence": rel(CANDIDATES),
        },
        {
            "claim_id": "C7_next_executable_gate",
            "stage246_status": "ALLOW_PROOF_PROTOTYPE_ONLY",
            "safe_wording": "The next executable route is a finite/toy structured-compact proof prototype, not SAB hot-path integration.",
            "blocked_wording": "Do not edit production SAB for compact/non-binary support before the proof-prototype gate passes.",
            "evidence": rel(NEXT),
        },
    ])
    return rows


def candidate_rows() -> list[dict[str, object]]:
    return [
        {
            "candidate_id": "V246-A",
            "name": "selected_binary_exact_dense_baseline",
            "algorithm_object": "r-body MAT-RLWE exact dense PVW/MAT-SAB for selected binary parameter rows",
            "status": "BASELINE_SUPPORTED_SCOPED",
            "admission": "keep_as_baseline_for_future_variants",
            "primary_metric": "complete-SAB T_bootstrap/r",
            "key_theory_risk": "not an optimality theorem; dense MAT can scale poorly with r",
            "required_next_gate": "rerun full-SAB A/B if executable hot path or benchmark semantics change",
            "evidence": "repro/stage236_set_2_3_4096_r4_highstat_slice/selected_binary_matrix_summary.csv; repro/stage245_current_head_counter_bridge/proof_gate.csv",
        },
        {
            "candidate_id": "V246-B",
            "name": "nonbinary_exact_pvw_sab",
            "algorithm_object": "ternary/include-zero PVW/MAT-SAB exact route",
            "status": "BLOCKED_NO_SELECTOR_SEMANTICS",
            "admission": "do_not_implement_hot_path",
            "primary_metric": "not applicable until phase invariant exists",
            "key_theory_risk": "scalar ternary branches do not imply PVW selector/key semantics",
            "required_next_gate": "selector semantics preflight: define sign/coefficient mapping, staged phase invariant, noise/resource plan",
            "evidence": "repro/stage229_parameter_generalization_matrix/coverage_gaps.csv",
        },
        {
            "candidate_id": "V246-C",
            "name": "generic_shared_output_compact_mat",
            "algorithm_object": "drop dense MAT rows/off-lane terms with the existing key distribution",
            "status": "REJECT_GENERIC_COMPACT",
            "admission": "rejected_as_algorithm_candidate",
            "primary_metric": "not admissible",
            "key_theory_risk": "finite-field counterexamples show random dense selectors are not representable by lane-local shared-output compact structure",
            "required_next_gate": "none for generic route; replace with structured keygen design",
            "evidence": "repro/stage166_shared_output_compact_algebra_gate/summary.csv; repro/stage112_selector_format_gate/summary.csv",
        },
        {
            "candidate_id": "V246-D",
            "name": "structured_compact_keygen_noise_route",
            "algorithm_object": "new selector/key distribution that makes compact shared-output/state exact",
            "status": "ADMIT_PROOF_PROTOTYPE_ONLY",
            "admission": "allow_stage248_finite_algebra_and_toy_noise_probe",
            "primary_metric": "proof prototype first; later full-SAB T_bootstrap/r if admitted",
            "key_theory_risk": "new key distribution may break security/noise assumptions or fail phase equivalence",
            "required_next_gate": "finite r=2 algebra simulator plus toy phase/noise recurrence; no production SAB edits",
            "evidence": "repro/stage166_shared_output_compact_algebra_gate/next_stage_queue.csv",
        },
        {
            "candidate_id": "V246-E",
            "name": "mat_rlwe_optimality_lower_bound_route",
            "algorithm_object": "lower-bound and gap model for exact/compact r-body MAT-RLWE SAB",
            "status": "ADMIT_MODEL_AND_COUNTER_GAP_ONLY",
            "admission": "analysis_plus_counter_refresh_only",
            "primary_metric": "gap(r)=A_impl(r)/A_lower(r), with A_impl=T_bootstrap/r",
            "key_theory_risk": "counter attribution does not prove lower-bound tightness",
            "required_next_gate": "derive measurable lower-bound rows and attach native counter/assembly evidence",
            "evidence": "theory_checks/mat_rlwe_sab_amortized_optimality.md; repro/stage245_current_head_counter_bridge/claim_boundary.csv",
        },
    ]


def proof_obligation_rows() -> list[dict[str, object]]:
    return [
        {
            "obligation_id": "P246-1",
            "applies_to": "all promoted variants",
            "required_statement": "For every checked SAB step and lane q, phase(body_q(acc_mat)) equals the scalar reference phase.",
            "current_status": "satisfied_only_for_selected_binary_exact_dense_tests",
            "evidence_or_gap": "repro/stage236_set_2_3_4096_r4_highstat_slice/selected_binary_matrix_summary.csv",
            "failure_action": "variant cannot enter full-SAB benchmark",
        },
        {
            "obligation_id": "P246-2",
            "applies_to": "nonbinary_exact_pvw_sab",
            "required_statement": "Define selector/key semantics for ternary/include-zero sub_a, sign, coefficient, and noise behavior.",
            "current_status": "missing",
            "evidence_or_gap": "repro/stage229_parameter_generalization_matrix/coverage_gaps.csv",
            "failure_action": "keep non-binary PVW claim unsupported",
        },
        {
            "obligation_id": "P246-3",
            "applies_to": "generic_shared_output_compact_mat",
            "required_statement": "Represent dense selector action with compact shared-output terms under current key distribution.",
            "current_status": "contradicted_by_counterexamples",
            "evidence_or_gap": "repro/stage166_shared_output_compact_algebra_gate/finite_field_counterexamples.csv",
            "failure_action": "reject generic compact route",
        },
        {
            "obligation_id": "P246-4",
            "applies_to": "structured_compact_keygen_noise_route",
            "required_statement": "Prove a constrained selector/key distribution removes off-lane terms while preserving security/noise and phase equivalence.",
            "current_status": "open_proof_prototype_admitted",
            "evidence_or_gap": "repro/stage166_shared_output_compact_algebra_gate/next_stage_queue.csv",
            "failure_action": "do not integrate compact SAB hot path",
        },
        {
            "obligation_id": "P246-5",
            "applies_to": "mat_rlwe_optimality_lower_bound_route",
            "required_statement": "Separate schedule, selector stream, unavoidable body work, memory traffic, and tail lower bounds.",
            "current_status": "model_open_not_proven",
            "evidence_or_gap": "theory_checks/mat_rlwe_sab_amortized_optimality.md",
            "failure_action": "do not claim theoretical optimality",
        },
    ]


def experiment_gate_rows() -> list[dict[str, object]]:
    return [
        {
            "gate_id": "E246-1",
            "candidate_id": "V246-A",
            "experiment": "full-SAB A/B after code changes",
            "baseline": "repeated scalar SAB same backend and same lane count",
            "metric": "T_bootstrap/r, noise failures, key size, keygen, RSS",
            "success": "positive mean speedup with CI lower bound above 1 and no worse failure rate",
            "failure": "speedup <= 1, correctness/noise regression, or unreported resource side cost",
            "status": "not_needed_until_code_delta",
        },
        {
            "gate_id": "E246-2",
            "candidate_id": "V246-B",
            "experiment": "non-binary selector semantics staged equivalence",
            "baseline": "scalar ternary/include-zero SAB branch",
            "metric": "per-step phase equivalence and final-output correctness",
            "success": "r=1/2/4 staged phase equivalence plus full-SAB deterministic pass",
            "failure": "any undefined selector semantics or phase mismatch",
            "status": "blocked_before_experiment",
        },
        {
            "gate_id": "E246-3",
            "candidate_id": "V246-C",
            "experiment": "generic compact exactness probe",
            "baseline": "dense MAT selector finite-field action",
            "metric": "mismatch count",
            "success": "zero mismatches for required selector family",
            "failure": "existing counterexamples remain",
            "status": "rejected_by_existing_counterexamples",
        },
        {
            "gate_id": "E246-4",
            "candidate_id": "V246-D",
            "experiment": "finite r=2 structured compact keygen/noise prototype",
            "baseline": "dense MAT finite algebra reference",
            "metric": "phase equivalence, off-lane zero proof rows, toy noise recurrence",
            "success": "proof-prototype passes before production code",
            "failure": "cannot satisfy off-lane zero/security/noise obligations",
            "status": "selected_next_executable_gate",
        },
        {
            "gate_id": "E246-5",
            "candidate_id": "V246-E",
            "experiment": "lower-bound gap table with counter/assembly rows",
            "baseline": "current exact dense implementation",
            "metric": "A_impl/A_lower plus cycles/load/store/FMA attribution",
            "success": "gap terms measurable and conservative; no unsupported optimality claim",
            "failure": "lower bound too loose or counters not tied to implementation",
            "status": "analysis_gate",
        },
    ]


def stats_repro_rows() -> list[dict[str, object]]:
    return [
        {
            "check_id": "S246-1",
            "topic": "primary endpoint",
            "requirement": "Every performance claim reports complete-SAB T_bootstrap/r and same-r scalar repeated baseline.",
            "status": "enforced",
            "evidence": "repro/stage240_scoped_latex_draft/claim_audit.csv",
        },
        {
            "check_id": "S246-2",
            "topic": "statistics",
            "requirement": "Paper-level performance promotion needs repeated runs and uncertainty; single perf-stat runs are attribution only.",
            "status": "enforced",
            "evidence": "repro/stage245_current_head_counter_bridge/claim_boundary.csv",
        },
        {
            "check_id": "S246-3",
            "topic": "ablation",
            "requirement": "Any new implementation must isolate representation, kernel, schedule, post-processing, and backend effects.",
            "status": "required_for_future_variants",
            "evidence": "experiments/stage246_broader_algorithm_admission_gate_plan.md",
        },
        {
            "check_id": "S246-4",
            "topic": "reproducibility",
            "requirement": "Each future variant must record commit, command, backend, CPU flags, seeds, raw logs, and artifact hashes.",
            "status": "required_for_future_variants",
            "evidence": "repro/stage246_broader_algorithm_admission_gate/reproduction_commands.md",
        },
        {
            "check_id": "S246-5",
            "topic": "negative results",
            "requirement": "Rejected and blocked candidates remain in the matrix and are not deleted from the research record.",
            "status": "enforced",
            "evidence": "repro/stage246_broader_algorithm_admission_gate/candidate_algorithm_matrix.csv",
        },
    ]


def admission_rows(candidates: list[dict[str, object]]) -> list[dict[str, object]]:
    rows = []
    for row in candidates:
        status = str(row["status"])
        if status.startswith("BASELINE"):
            decision = "retain_as_baseline"
            production_permission = "already_existing_scoped_path"
        elif status.startswith("REJECT"):
            decision = "reject"
            production_permission = "no"
        elif status.startswith("BLOCKED"):
            decision = "block_until_preflight"
            production_permission = "no"
        elif "PROOF_PROTOTYPE" in status:
            decision = "admit_proof_prototype"
            production_permission = "no_hot_path_edits"
        else:
            decision = "admit_analysis_only"
            production_permission = "no_speedup_claim"
        rows.append({
            "candidate_id": row["candidate_id"],
            "decision": decision,
            "production_permission": production_permission,
            "next_action": row["required_next_gate"],
            "claim_status": row["status"],
        })
    return rows


def proof_gate_rows(inputs, candidates, claims, stats) -> list[dict[str, object]]:
    inputs_ok = all(row["status"] == "present" for row in inputs)
    generic_rejected = any(row["candidate_id"] == "V246-C" and str(row["status"]).startswith("REJECT") for row in candidates)
    structured_admitted = any(row["candidate_id"] == "V246-D" and "PROOF_PROTOTYPE" in str(row["status"]) for row in candidates)
    no_production_promotion = all(row["claim_id"] != "C6_broader_algorithm_admission" or row["stage246_status"] == "DENY_PRODUCTION_PROMOTION_NOW" for row in claims)
    stats_ok = all(row["status"] in {"enforced", "required_for_future_variants"} for row in stats)
    decision_ok = inputs_ok and generic_rejected and structured_admitted and no_production_promotion and stats_ok
    return [
        {
            "gate": "G1_inputs",
            "status": "PASS" if inputs_ok else "FAIL",
            "metric": "required input files",
            "value": "all present" if inputs_ok else "missing",
            "evidence": rel(INPUT_STATUS),
            "interpretation": "Stage246 consumes existing selected-binary, compact, non-binary, and counter-boundary evidence.",
        },
        {
            "gate": "G2_claim_boundary",
            "status": "PASS_NO_BROADER_PRODUCTION_PROMOTION" if no_production_promotion else "FAIL",
            "metric": "broader claims",
            "value": "denied for production",
            "evidence": rel(CLAIM_BOUNDARY),
            "interpretation": "Selected binary exact dense claim is preserved; broader claims stay gated.",
        },
        {
            "gate": "G3_candidate_classification",
            "status": "PASS",
            "metric": "candidate_count",
            "value": len(candidates),
            "evidence": rel(CANDIDATES),
            "interpretation": "Baseline, non-binary, generic compact, structured compact, and optimality routes are separated.",
        },
        {
            "gate": "G4_generic_compact_guard",
            "status": "PASS_REJECT_GENERIC_COMPACT" if generic_rejected else "FAIL",
            "metric": "existing compact counterexamples",
            "value": "generic route rejected",
            "evidence": "repro/stage166_shared_output_compact_algebra_gate/summary.csv",
            "interpretation": "Counterexamples prevent loop-only/shared-output compact hot-path implementation.",
        },
        {
            "gate": "G5_next_executable_gate",
            "status": "PASS_PROOF_PROTOTYPE_SELECTED" if structured_admitted else "FAIL",
            "metric": "structured compact route",
            "value": "finite/toy proof prototype only",
            "evidence": rel(EXPERIMENT_GATES),
            "interpretation": "The next executable work is a proof prototype, not production SAB integration.",
        },
        {
            "gate": "G6_stats_repro",
            "status": "PASS" if stats_ok else "FAIL",
            "metric": "stats/repro constraints",
            "value": "enforced",
            "evidence": rel(STATS_REPRO),
            "interpretation": "Future speedup claims require repeated complete-SAB timing and reproducible logs.",
        },
        {
            "gate": "G7_stage246_decision",
            "status": DECISION if decision_ok else "FAIL_STAGE246_ADMISSION_GATE",
            "metric": "decision",
            "value": DECISION if decision_ok else "FAIL_STAGE246_ADMISSION_GATE",
            "evidence": rel(PROOF_GATE),
            "interpretation": "Proceed to Stage248 proof prototype; do not expand paper claims now.",
        },
    ]


def next_rows() -> list[dict[str, object]]:
    return [
        {
            "priority": "P0",
            "route": "stage248_structured_compact_keygen_finite_probe",
            "entry_condition": "Stage246 admits V246-D proof prototype only.",
            "gate": "finite r=2 algebra simulator, off-lane zero constraints, toy noise recurrence, dense-reference equivalence",
            "status": "selected_next_executable",
            "failure_action": "freeze compact route and keep exact dense as scoped contribution",
            "evidence": rel(EXPERIMENT_GATES),
        },
        {
            "priority": "P1",
            "route": "stage249_nonbinary_selector_semantics_preflight",
            "entry_condition": "A non-binary PVW claim is needed.",
            "gate": "selector/key semantics for ternary/include-zero, staged phase equivalence, scalar branch preservation",
            "status": "blocked_until_semantics_design",
            "failure_action": "keep non-binary PVW unsupported",
            "evidence": "repro/stage229_parameter_generalization_matrix/coverage_gaps.csv",
        },
        {
            "priority": "P2",
            "route": "stage250_exact_dense_lower_bound_gap_refresh",
            "entry_condition": "Optimality wording is desired.",
            "gate": "measurable lower-bound components plus native counter/assembly tie-in",
            "status": "analysis_gate",
            "failure_action": "state measured engineering improvement only",
            "evidence": "theory_checks/mat_rlwe_sab_amortized_optimality.md",
        },
        {
            "priority": "P3",
            "route": "stage247_batchboot_monitor_rerun",
            "entry_condition": "Before final submission or after citation metadata changes.",
            "gate": "official source route only",
            "status": "future_monitor",
            "failure_action": "leave BatchBoot TODO",
            "evidence": "repro/stage244_batchboot_bibtex_monitor/remaining_todo.csv",
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


def write_docs(inputs, claims, candidates, proof_obligations, experiment_gates, stats, admission, gates, nextq, head: str) -> None:
    write_text(DOC, f"""# Stage246 Broader Algorithm Admission Gate

Decision: `{gates[-1]["status"]}`.

Stage246 takes the PVW/MAT-SAB research loop beyond the selected binary exact
dense result and classifies broader routes. It does not promote new
bootstrapping claims. Its output is an admission decision for future
implementation work.

## Candidate Algorithms

{table(candidates, ["candidate_id", "name", "algorithm_object", "status", "admission", "primary_metric", "key_theory_risk", "required_next_gate", "evidence"])}

## Admission Decision

{table(admission, ["candidate_id", "decision", "production_permission", "next_action", "claim_status"])}

## Proof Obligations

{table(proof_obligations, ["obligation_id", "applies_to", "required_statement", "current_status", "evidence_or_gap", "failure_action"])}

## Experiment Gates

{table(experiment_gates, ["gate_id", "candidate_id", "experiment", "baseline", "metric", "success", "failure", "status"])}

## Stats And Repro Gates

{table(stats, ["check_id", "topic", "requirement", "status", "evidence"])}

## Claim Boundary

{table(claims, ["claim_id", "stage246_status", "safe_wording", "blocked_wording", "evidence"])}

## Proof Gates

{table(gates, ["gate", "status", "metric", "value", "evidence", "interpretation"])}

## Next Queue

{table(nextq, ["priority", "route", "entry_condition", "gate", "status", "failure_action", "evidence"])}

## Inputs

{table(inputs, ["input_id", "path", "status", "bytes"])}

Generated from head `{head}`.
""")
    write_text(REPORT, f"""# Stage246 Report

Decision: `{gates[-1]["status"]}`.

Stage246 admits no broader production SAB hot-path implementation. It preserves
the selected binary exact dense route as the measured baseline, rejects generic
compact shared-output MAT under the existing key distribution, keeps non-binary
PVW unsupported until selector semantics exist, and admits only a structured
compact keygen/noise proof prototype as the next executable gate.
""")
    write_text(PLAN, """# Stage246 Broader Algorithm Admission Gate Plan

## Objective

Classify broader PVW/MAT-SAB routes before implementation.

## Primary Endpoint

Any performance claim must use complete-SAB `T_bootstrap/r` against a same-r
repeated scalar baseline.

## Future Gates

- Structured compact: finite r=2 algebra simulator plus toy noise recurrence.
- Non-binary: selector/key semantics preflight before any hot-path code.
- Optimality: lower-bound gap table tied to counters/assembly.
- Exact dense: remains the baseline for all future A/B tests.

## Stop Rule

No production SAB integration is allowed for compact/non-binary paths until the
corresponding proof-prototype or semantics gate passes.
""")
    write_text(THEORY, """# Stage246 Algorithm Admission Boundary

The Stage246 boundary is:

```text
measured selected-binary exact dense MAT-RLWE SAB != broader MAT-RLWE SAB theorem
```

The existing evidence proves a scoped complete-SAB amortized improvement for
selected binary rows. It does not prove non-binary support, compact exactness,
all-parameter support, or theoretical optimality.

The generic compact route is rejected because existing finite-field
counterexamples show that arbitrary dense selector action cannot be represented
by the proposed lane-local shared-output structure under the current key
distribution. A compact route can re-enter only as a structured keygen/noise
design with new proof obligations.

The anti-theory-loop rule is concrete: the next compact action is a finite r=2
prototype with a dense reference, off-lane zero constraints, and toy noise
recurrence. If that fails, the compact route is frozen rather than repeatedly
reframed in prose.
""")
    write_variant_doc(candidates, proof_obligations, experiment_gates)
    write_text(REPRO_CMDS, f"""# Stage246 Reproduction Commands

```text
python scripts/build_stage246_broader_algorithm_admission_gate.py
python -m py_compile scripts/build_stage246_broader_algorithm_admission_gate.py
```

Decision: `{gates[-1]["status"]}`.
""")


def write_variant_doc(candidates, proof_obligations, experiment_gates) -> None:
    card_sections = []
    for row in candidates:
        cid = row["candidate_id"]
        obligations = [p for p in proof_obligations if p["applies_to"] in {"all promoted variants", row["name"]}]
        gates = [g for g in experiment_gates if g["candidate_id"] == cid]
        card_sections.append(f"""# {cid}: {row["name"]}

## Summary

- Parent algorithm: 2025/686 sparse amortized bootstrapping with PVW/MAT-SAB.
- Focused module: {row["algorithm_object"]}.
- Optimization target: {row["primary_metric"]}.
- Status labels: `{row["status"]}`.
- Main hypothesis: {row["key_theory_risk"]}.

## Mathematical Definition

The variant is evaluated against the scalar repeated baseline using the
amortized endpoint:

```text
A_variant(r) = T_variant_complete_bootstrap(r) / r
speedup(r) = A_scalar_repeated(r) / A_variant(r)
```

No candidate may replace this metric with isolated external-product throughput.

## Pseudocode

```text
Input: r scalar lanes or an admitted r-body MAT-RLWE state
Output: r bootstrapped lanes or a proof-prototype decision
1. Check candidate admission status.
2. If status is blocked or rejected, stop before production SAB edits.
3. If proof-prototype-only, run the finite/proof gate against a dense reference.
4. If the proof gate passes, then and only then design a full-SAB A/B test.
```

## Delta From Original Algorithm

| Original component | Variant component | Relationship | Evidence/status |
| --- | --- | --- | --- |
| scalar repeated SAB | {row["algorithm_object"]} | candidate admission | {row["status"]} |

## Complexity Change

- Time: not claimable until the required gate passes.
- Memory: must be reported with key size, keygen time, and RSS for any future speedup.
- Communication or IO: not a separate claim in the current codebase.
- What must be measured: {row["required_next_gate"]}.

## Theory Dependencies

- Inherited assumptions: scalar SAB and selected binary exact dense PVW/MAT-SAB gates.
- Relaxed/new assumptions: candidate-specific and currently not fully proven unless marked baseline.
- Proof steps affected: phase equivalence, selector semantics, noise, and lower-bound gap.
- New lemmas needed: see Stage246 proof obligations.
- Current status: {row["status"]}.

## Potential Failure Reasons

- Failure mode: {row["key_theory_risk"]}.
- Trigger condition: required proof or experiment gate fails.
- How to detect: run the candidate's Stage246 experiment gate.
- Mitigation or follow-up: {row["required_next_gate"]}.

## Required Experiments

{table(gates, ["gate_id", "experiment", "baseline", "metric", "success", "failure", "status"])}

## Paper Contribution Candidate

`{row["admission"]}`. This is not a paper-level broader SAB claim unless the
listed theory, correctness, noise, resource, and complete-SAB gates pass.
""")
    write_text(VARIANT, "\n\n".join(card_sections))


def update_project_files(head: str, decision: str) -> None:
    append_once(ROADMAP, "## Stage 246: Broader Algorithm Admission Gate", f"""
## Stage 246: Broader Algorithm Admission Gate

Goal:

```text
Classify non-binary, compact, exact-dense, and optimality routes before any
broader production SAB implementation.
```

Status:

```text
Generated from input head `{head}` with `{decision}`. No broader production
claim is promoted. Generic compact is rejected under existing counterexamples;
structured compact is admitted only to a finite/proof prototype; non-binary
PVW remains blocked until selector semantics are defined.
```
""")
    append_once(GOAL, "Stage246 broader algorithm admission gate", f"""
- Stage246 broader algorithm admission gate records `{decision}`: exact dense
  selected-binary PVW/MAT-SAB remains the supported baseline, while generic
  compact and non-binary claims are not promoted. The next executable route is
  a structured-compact proof prototype, not production SAB integration.
""")
    append_once(CURRENT_GOAL, "### Stage246 broader algorithm admission gate", f"""
### Stage246 broader algorithm admission gate

`{decision}` records the admission decision for broader PVW/MAT-SAB routes.
The active goal remains open because structured compact proof prototypes,
non-binary selector semantics, lower-bound optimality, and final bibliography
closure remain incomplete.
""")
    append_once(HYPOTHESES, "H10_stage246_broader_algorithm_admission_gate:", f"""
H10_stage246_broader_algorithm_admission_gate:
  status: broader_algorithm_gate_proof_prototypes_only
  evidence:
    - repro/stage246_broader_algorithm_admission_gate/candidate_algorithm_matrix.csv
    - repro/stage246_broader_algorithm_admission_gate/proof_obligation_matrix.csv
    - repro/stage246_broader_algorithm_admission_gate/experiment_gate_matrix.csv
    - repro/stage246_broader_algorithm_admission_gate/proof_gate.csv
    - docs/stage246_broader_algorithm_admission_gate.md
  conclusion: >
    Stage246 records {decision}. It keeps the exact dense selected-binary
    PVW/MAT-SAB route as the measured baseline, rejects generic compact
    shared-output MAT under existing counterexamples, blocks non-binary PVW
    until selector semantics are defined, and admits only a structured compact
    keygen/noise proof prototype as the next executable route.
""")
    append_once(RUN_LOG, "stage246-broader-algorithm-admission-001", f"""stage246-broader-algorithm-admission-001,{date.today().isoformat()},{head},Stage 246,algorithm_gate,"python scripts/build_stage246_broader_algorithm_admission_gate.py","Stage240/229/166/112/245 evidence",n/a,{decision},"Broader PVW/MAT-SAB routes classified; only proof prototypes admitted.",docs/stage246_broader_algorithm_admission_gate.md; repro/stage246_broader_algorithm_admission_gate/proof_gate.csv
""")
    append_once(MANIFEST, "- stage246_broader_algorithm_admission_gate:", """
- stage246_broader_algorithm_admission_gate:
  - `docs/stage246_broader_algorithm_admission_gate.md`
  - `experiments/stage246_broader_algorithm_admission_gate_plan.md`
  - `theory_checks/stage246_algorithm_admission_boundary.md`
  - `algorithm_variants/mat_rlwe_sab_stage246_broader_algorithm_gate.md`
  - `scripts/build_stage246_broader_algorithm_admission_gate.py`
  - `repro/stage246_broader_algorithm_admission_gate/`
""")
    append_once(CHECKLIST, "Stage246 broader algorithm admission gate records proof-prototype-only promotion", f"""
- [x] Stage246 broader algorithm admission gate records proof-prototype-only promotion `{decision}`.
""")


def main() -> None:
    OUT.mkdir(parents=True, exist_ok=True)
    head = run_git(["rev-parse", "--short", "HEAD"])
    inputs = input_rows()
    claims = claim_boundary_rows()
    candidates = candidate_rows()
    proof_obligations = proof_obligation_rows()
    experiment_gates = experiment_gate_rows()
    stats = stats_repro_rows()
    admission = admission_rows(candidates)
    gates = proof_gate_rows(inputs, candidates, claims, stats)
    nextq = next_rows()

    write_csv(INPUT_STATUS, inputs, ["input_id", "path", "status", "bytes"])
    write_csv(CLAIM_BOUNDARY, claims, ["claim_id", "stage246_status", "safe_wording", "blocked_wording", "evidence"])
    write_csv(CANDIDATES, candidates, ["candidate_id", "name", "algorithm_object", "status", "admission", "primary_metric", "key_theory_risk", "required_next_gate", "evidence"])
    write_csv(PROOF_OBLIGATIONS, proof_obligations, ["obligation_id", "applies_to", "required_statement", "current_status", "evidence_or_gap", "failure_action"])
    write_csv(EXPERIMENT_GATES, experiment_gates, ["gate_id", "candidate_id", "experiment", "baseline", "metric", "success", "failure", "status"])
    write_csv(STATS_REPRO, stats, ["check_id", "topic", "requirement", "status", "evidence"])
    write_csv(ADMISSION, admission, ["candidate_id", "decision", "production_permission", "next_action", "claim_status"])
    write_csv(PROOF_GATE, gates, ["gate", "status", "metric", "value", "evidence", "interpretation"])
    write_csv(NEXT, nextq, ["priority", "route", "entry_condition", "gate", "status", "failure_action", "evidence"])

    write_docs(inputs, claims, candidates, proof_obligations, experiment_gates, stats, admission, gates, nextq, head)
    artifacts = [DOC, PLAN, THEORY, VARIANT, INPUT_STATUS, CLAIM_BOUNDARY, CANDIDATES, PROOF_OBLIGATIONS, EXPERIMENT_GATES, STATS_REPRO, ADMISSION, PROOF_GATE, NEXT, REPORT, REPRO_CMDS]
    write_csv(ARTIFACT, artifact_rows(artifacts), ["artifact", "exists", "sha256", "bytes"])
    update_project_files(head, gates[-1]["status"])
    print(f"Stage246 report: {rel(DOC)}")
    print(f"Stage246 decision: {gates[-1]['status']}")


if __name__ == "__main__":
    main()
