#!/usr/bin/env python3
"""Stage223: route selection after compact EP expressiveness denial."""

from __future__ import annotations

import csv
import hashlib
import subprocess
from pathlib import Path
from typing import Dict, Iterable, List


ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "repro" / "stage223_route_selection"

DOC = ROOT / "docs" / "stage223_route_selection.md"
PLAN = ROOT / "experiments" / "stage223_route_selection_plan.md"
THEORY = ROOT / "theory_checks" / "stage223_route_selection_model.md"
VARIANT = ROOT / "algorithm_variants" / "mat_rlwe_sab_stage223_route_selection.md"

INPUTS = OUT / "input_status.csv"
EVIDENCE = OUT / "evidence_summary.csv"
ROUTES = OUT / "route_matrix.csv"
PROOF = OUT / "proof_gate.csv"
NEXT = OUT / "next_stage_queue.csv"
REPORT = OUT / "route_selection_report.md"
ARTIFACT = OUT / "artifact_index.csv"
REPRO = OUT / "reproduction_commands.md"

ROADMAP = ROOT / "docs" / "roadmap_stage19_plus.md"
GOAL = ROOT / "docs" / "goal_sab_max_acceleration.md"
CURRENT_GOAL = ROOT / "docs" / "current_codex_goal_sab_completion.md"
HYPOTHESES = ROOT / "hypotheses" / "hypothesis_register.yaml"
RUN_LOG = ROOT / "repro" / "run_log.csv"
MANIFEST = ROOT / "repro" / "artifact_manifest.md"
CHECKLIST = ROOT / "repro" / "reproduction_checklist.md"

STAGE222_PROOF = ROOT / "repro" / "stage222_isolated_compact_ep_integration" / "proof_gate.csv"
STAGE222_EXPRESS = ROOT / "repro" / "stage222_isolated_compact_ep_integration" / "expressiveness_results.csv"
STAGE134_RATIO = ROOT / "repro" / "stage134_generalized_lane_pair_input_ep_gate" / "ratio_summary.csv"
STAGE139_SUMMARY = ROOT / "repro" / "stage139_compact_closure_audit" / "summary.csv"
STAGE166_SUMMARY = ROOT / "repro" / "stage166_shared_output_compact_algebra_gate" / "summary.csv"
STAGE144_PERF = ROOT / "repro" / "stage144_full_sab_repeated_r4_unrolled_gate" / "perf_comparison.csv"
STAGE148_PERF = ROOT / "repro" / "stage148_h14_r6_repeated_refresh" / "perf_comparison.csv"
STAGE148_SUMMARY = ROOT / "repro" / "stage148_h14_r6_repeated_refresh" / "summary.csv"
STAGE150_MODEL = ROOT / "theory_checks" / "stage150_claim_scope_model.md"

DECISION = "PASS_STAGE223_ROUTE_EXACT_PVW_MAT_REFRESH_SELECTED_COMPACT_COMPLETE_DENIED"

INPUT_FIELDS = ["input", "status", "evidence", "role", "bytes"]
EVIDENCE_FIELDS = ["source", "status", "metric", "value", "evidence", "interpretation"]
ROUTE_FIELDS = ["route", "status", "reason", "evidence", "next_action"]


def rel(path: Path) -> str:
    return path.resolve().relative_to(ROOT.resolve()).as_posix()


def read_text(path: Path) -> str:
    return path.read_text(encoding="utf-8", errors="replace") if path.exists() else ""


def write_text(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes((text.rstrip() + "\n").encode("utf-8"))


def read_csv(path: Path) -> List[Dict[str, str]]:
    if not path.exists():
        return []
    with path.open("r", encoding="utf-8", newline="") as f:
        return list(csv.DictReader(f))


def write_csv(path: Path, rows: Iterable[Dict[str, str]], fields: List[str]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    normalized = [{field: row.get(field, "") for field in fields} for row in rows]
    with path.open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fields, lineterminator="\n")
        writer.writeheader()
        writer.writerows(normalized)


def append_once(path: Path, marker: str, text: str) -> None:
    current = read_text(path)
    if marker in current:
        return
    if current and not current.endswith("\n"):
        current += "\n"
    write_text(path, current + text.lstrip("\n"))


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


def sha256_file(path: Path) -> str:
    if not path.exists():
        return ""
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
            stderr=subprocess.DEVNULL,
        ).strip()
    except Exception:
        return "unknown"


def first(path: Path) -> Dict[str, str]:
    rows = read_csv(path)
    return rows[0] if rows else {}


def proof_status(path: Path, gate: str) -> str:
    for row in read_csv(path):
        if row.get("gate") == gate or row.get("stage") == gate:
            return row.get("status", "")
    return ""


def build_inputs() -> List[Dict[str, str]]:
    inputs = [
        ("stage222_proof", STAGE222_PROOF, "compact production EP boundary"),
        ("stage222_expressiveness", STAGE222_EXPRESS, "neighbor/cross-body denial source"),
        ("stage134_generalized_ep_ratio", STAGE134_RATIO, "closure-capable compact EP performance evidence"),
        ("stage139_closure_audit", STAGE139_SUMMARY, "direct compact non-closure evidence"),
        ("stage166_algebra_gate", STAGE166_SUMMARY, "generic compact exactness denial"),
        ("stage144_r4_full_sab", STAGE144_PERF, "r=4 full SAB per-lane evidence"),
        ("stage148_r6_full_sab", STAGE148_PERF, "r=6 full SAB per-lane evidence"),
        ("stage148_summary", STAGE148_SUMMARY, "noise/resource side conditions"),
        ("stage150_claim_scope", STAGE150_MODEL, "T_bootstrap/r metric definition"),
    ]
    rows = []
    for name, path, role in inputs:
        rows.append(
            {
                "input": name,
                "status": "present" if path.exists() else "missing",
                "evidence": rel(path),
                "role": role,
                "bytes": str(path.stat().st_size) if path.exists() else "0",
            }
        )
    return rows


def build_evidence() -> List[Dict[str, str]]:
    stage144 = first(STAGE144_PERF)
    stage148 = first(STAGE148_PERF)
    key_ratio = ""
    vmhwm_ratio = ""
    for row in read_csv(STAGE148_SUMMARY):
        if row.get("gate") == "stage148_resource":
            parts = row.get("value", "").split(";")
            if len(parts) == 2:
                key_ratio, vmhwm_ratio = parts
    stage134 = read_csv(STAGE134_RATIO)
    min_r4_r6 = min(
        (float(row.get("full_speedup", "0")) for row in stage134 if row.get("r") in {"4", "6"}),
        default=0.0,
    )
    max_stage134 = max((float(row.get("full_speedup", "0")) for row in stage134), default=0.0)
    return [
        {
            "source": "Stage222",
            "status": proof_status(STAGE222_PROOF, "G7_stage222_decision"),
            "metric": "complete_selector_status",
            "value": "DENY_COMPLETE_SELECTOR_INTEGRATION",
            "evidence": rel(STAGE222_PROOF),
            "interpretation": "Production compact EP is lane-local correct but cannot cover current Stage203/SAB selector.",
        },
        {
            "source": "Stage134",
            "status": "NEUTRAL_OR_NEGATIVE",
            "metric": "min_full_speedup_r4_r6;max_full_speedup_all",
            "value": f"{min_r4_r6:.6f};{max_stage134:.6f}",
            "evidence": rel(STAGE134_RATIO),
            "interpretation": "Closure-capable generalized compact EP is correct but not a stable r=4/r=6 performance route.",
        },
        {
            "source": "Stage139/166",
            "status": "COMPACT_DIRECT_ROUTE_BLOCKED",
            "metric": "closure;generic_exactness",
            "value": "not_pvw_closed;cross_body_missing",
            "evidence": f"{rel(STAGE139_SUMMARY)}; {rel(STAGE166_SUMMARY)}",
            "interpretation": "Direct compact output and generic compact exactness are both denied without a new state/proof.",
        },
        {
            "source": "Stage144",
            "status": stage144.get("decision", ""),
            "metric": "r4_T_bootstrap_per_lane_speedup_vs_scalar",
            "value": stage144.get("r4_mean_speedup_vs_scalar", ""),
            "evidence": rel(STAGE144_PERF),
            "interpretation": "r=4 exact MAT/PVW full-SAB evidence is weak-positive but CI crosses one for incremental kernel change.",
        },
        {
            "source": "Stage148",
            "status": stage148.get("decision", ""),
            "metric": "r6_T_bootstrap_per_lane_speedup_vs_scalar;key_bytes_ratio;vmhwm_ratio",
            "value": f"{stage148.get('backend_mean_speedup_vs_scalar', '')};{key_ratio};{vmhwm_ratio}",
            "evidence": f"{rel(STAGE148_PERF)}; {rel(STAGE148_SUMMARY)}",
            "interpretation": "r=6 exact MAT/PVW backend has the strongest complete-SAB T_bootstrap/r evidence so far.",
        },
    ]


def build_routes() -> List[Dict[str, str]]:
    return [
        {
            "route": "compact_lane_local_current_api",
            "status": "KEEP_AS_ISOLATED_SUBCLASS_ONLY",
            "reason": "Stage222 lane-local oracle passes but cross-body negative control rejects complete selector.",
            "evidence": rel(STAGE222_PROOF),
            "next_action": "Do not connect to SAB hot path.",
        },
        {
            "route": "new_closed_neighbor_capable_compact_state",
            "status": "PROOF_ONLY_HIGH_RISK",
            "reason": "Would need a state shape that consumes/writes neighbor body equations while remaining closed and secure.",
            "evidence": f"{rel(STAGE222_EXPRESS)}; {rel(STAGE166_SUMMARY)}",
            "next_action": "Only start if explicitly choosing a new algebra/proof research branch.",
        },
        {
            "route": "exact_closed_dense_mat_pvw",
            "status": "SELECT_EXECUTABLE_MAINLINE",
            "reason": "Already valid for complete SAB and has r=6 per-lane full-SAB speedup evidence.",
            "evidence": f"{rel(STAGE148_PERF)}; {rel(STAGE150_MODEL)}",
            "next_action": "Run Stage224 exact PVW/MAT AVX resource refresh under T_bootstrap/r.",
        },
        {
            "route": "paper_claim",
            "status": "ENGINEERING_CLAIM_ONLY_FOR_NOW",
            "reason": "No compact complete-SAB algorithm is admitted; theoretical optimality remains unproved.",
            "evidence": rel(STAGE150_MODEL),
            "next_action": "Report exact MAT/PVW acceleration with resource/noise side conditions; keep compact as negative/blocked result.",
        },
    ]


def build_proof(inputs: List[Dict[str, str]], evidence: List[Dict[str, str]], routes: List[Dict[str, str]]) -> List[Dict[str, str]]:
    missing = [row["input"] for row in inputs if row["status"] != "present"]
    stage222_denied = any(row["source"] == "Stage222" and "DENY" in row["value"] for row in evidence)
    exact_selected = any(row["route"] == "exact_closed_dense_mat_pvw" and row["status"] == "SELECT_EXECUTABLE_MAINLINE" for row in routes)
    r6_value = next((row["value"].split(";")[0] for row in evidence if row["source"] == "Stage148"), "")
    ready = not missing and stage222_denied and exact_selected
    return [
        {
            "gate": "G1_required_inputs",
            "status": "PASS" if not missing else "FAIL",
            "metric": "missing_inputs",
            "value": ";".join(missing),
            "evidence": rel(INPUTS),
            "interpretation": "Stage223 route selection consumes compact denial and exact full-SAB evidence.",
        },
        {
            "gate": "G2_compact_complete_route",
            "status": "DENY_COMPACT_COMPLETE_SAB_ROUTE" if stage222_denied else "FAIL",
            "metric": "stage222_complete_selector",
            "value": "DENY_COMPLETE_SELECTOR_INTEGRATION" if stage222_denied else "",
            "evidence": rel(EVIDENCE),
            "interpretation": "Current compact route cannot be connected to SAB without a new closed state/proof.",
        },
        {
            "gate": "G3_exact_mat_route",
            "status": "SELECT_EXACT_PVW_MAT_MAINLINE" if exact_selected else "FAIL",
            "metric": "best_current_complete_sab_speedup_per_lane",
            "value": r6_value,
            "evidence": rel(ROUTES),
            "interpretation": "The valid executable route is exact closed dense MAT/PVW optimization under T_bootstrap/r.",
        },
        {
            "gate": "G4_claim_boundary",
            "status": "PASS_ENGINEERING_SCOPE_ONLY",
            "metric": "paper_claim_boundary",
            "value": "no_theoretical_optimality;no_compact_complete_sab_claim",
            "evidence": rel(DOC),
            "interpretation": "Stage223 prevents unsupported compact algorithm or optimality claims.",
        },
        {
            "gate": "G5_stage223_decision",
            "status": DECISION if ready else "FAIL_STAGE223",
            "metric": "decision",
            "value": DECISION if ready else "FAIL_STAGE223",
            "evidence": rel(PROOF),
            "interpretation": "Proceed to exact PVW/MAT AVX/resource refresh; keep compact complete-SAB blocked.",
        },
    ]


def build_next(decision: str) -> List[Dict[str, str]]:
    selected = decision == DECISION
    return [
        {
            "priority": "P0",
            "route": "stage224_exact_pvw_mat_avx_resource_refresh",
            "entry_condition": "Stage223 selects exact closed dense MAT/PVW as executable mainline.",
            "gate": "Rerun full-SAB T_bootstrap/r, AVX/backend attribution, resource/noise side conditions.",
            "status": "selected" if selected else "blocked",
            "failure_action": "Keep Stage148 as current best evidence and do not claim further gains.",
            "evidence": rel(PROOF),
        },
        {
            "priority": "P1",
            "route": "stage225_neighbor_capable_compact_state_proof",
            "entry_condition": "User explicitly chooses a new compact algebra/proof branch.",
            "gate": "Define and falsify a closed neighbor-capable compact state before any code.",
            "status": "proof_only_deferred",
            "failure_action": "Do not touch SAB hot path.",
            "evidence": rel(STAGE222_EXPRESS),
        },
        {
            "priority": "P2",
            "route": "paper_claim_boundary_update",
            "entry_condition": "After Stage224 refresh or if native platform remains unavailable.",
            "gate": "Separate exact MAT/PVW engineering claim from blocked compact route.",
            "status": "future",
            "failure_action": "No novelty/optimality claim.",
            "evidence": rel(STAGE150_MODEL),
        },
    ]


def write_docs(inputs: List[Dict[str, str]], evidence: List[Dict[str, str]], routes: List[Dict[str, str]], proof: List[Dict[str, str]], next_rows: List[Dict[str, str]]) -> None:
    decision = proof[-1]["status"]
    doc = f"""# Stage223 Route Selection

Decision: `{decision}`.

Stage223 closes the current compact-production route for complete SAB: the
lane-local compact EP subclass remains valid, but Stage222 denies complete
selector integration. The executable mainline is therefore the already valid
closed dense MAT/PVW path, measured by `T_bootstrap/r`.

## Proof Gates

{table(proof, ["gate", "status", "metric", "value", "evidence", "interpretation"])}
## Evidence Summary

{table(evidence, EVIDENCE_FIELDS)}
## Route Matrix

{table(routes, ROUTE_FIELDS)}
## Next Queue

{table(next_rows, ["priority", "route", "entry_condition", "gate", "status", "failure_action", "evidence"])}
"""
    write_text(DOC, doc)
    write_text(REPORT, doc)
    write_text(
        THEORY,
        """# Stage223 Route Selection Model

The primary metric remains `T_bootstrap/r`, i.e. time per processed plaintext
bit or independent SAB lane. A route may enter the executable mainline only if
it is closed under the SAB accumulator state and has complete-SAB evidence.

Stage222 denies the current compact lane-local state for complete selector
integration. Therefore the next executable route is exact closed dense MAT/PVW
optimization, while any neighbor-capable compact state is a separate proof-only
branch.
""",
    )
    write_text(
        PLAN,
        """# Stage223 Experiment Plan

1. Consume Stage222 compact EP denial and Stage148 complete-SAB evidence.
2. Select exactly one executable mainline route.
3. Preserve compact as an isolated/blocked result unless a new proof branch is
   explicitly chosen.
4. Route Stage224 to exact PVW/MAT AVX/resource refresh under `T_bootstrap/r`.
""",
    )
    write_text(
        VARIANT,
        """# MAT-RLWE SAB Stage223 Route Selection

The compact lane-local API is not the full MAT-RLWE SAB algorithmic route. The
current complete-SAB optimization target is the closed dense MAT/PVW path,
reported per processed bit as `T_bootstrap/r`. Compact work can restart only
with a new closed neighbor-capable state proof.
""",
    )
    write_text(
        REPRO,
        f"""# Stage223 Reproduction Commands

```powershell
python scripts\\build_stage223_route_selection.py
Get-Content {rel(PROOF)}
Get-Content {rel(ROUTES)}
```
""",
    )


def update_tracking(status: str) -> None:
    head = git_head()
    append_once(
        ROADMAP,
        "## Stage 223: Route Selection After Compact EP Denial",
        f"""
## Stage 223: Route Selection After Compact EP Denial

Goal:

```text
Select the next executable route after Stage222 proves lane-local compact EP is
not enough for complete SAB selector integration.
```

Status:

```text
Completed. Stage223 records {status}. The exact closed dense MAT/PVW path is
selected for Stage224 AVX/resource refresh under T_bootstrap/r; compact
complete-SAB integration remains denied.
```
""",
    )
    append_once(
        GOAL,
        "Stage223 route selection",
        f"""
- Stage223 route selection: `{status}`. Mainline execution returns to exact
  closed dense MAT/PVW; compact complete-SAB remains blocked without a new
  closed neighbor-capable state proof.
""",
    )
    append_once(
        CURRENT_GOAL,
        "Stage223 route selection",
        f"""
- Stage223 route selection completed with `{status}`. Next selected stage:
  Stage224 exact PVW/MAT AVX/resource refresh measured by `T_bootstrap/r`.
""",
    )
    append_once(
        HYPOTHESES,
        "H10_stage223_route_selection",
        f"""
H10_stage223_route_selection:
  status: exact_pvw_mat_mainline_selected
  evidence:
    - repro/stage223_route_selection/proof_gate.csv
    - repro/stage223_route_selection/route_matrix.csv
    - docs/stage223_route_selection.md
  conclusion: >
    Stage223 records {status}. Current compact complete-SAB integration remains
    denied; exact closed dense MAT/PVW is the executable mainline for further
    T_bootstrap/r optimization.
""",
    )
    append_once(
        RUN_LOG,
        "stage223-route-selection-001",
        f"""stage223-route-selection-001,2026-07-04,{head},Stage 223,model,python scripts/build_stage223_route_selection.py,Stage222 compact denial and Stage148 complete-SAB evidence,no new benchmark,{status},"Route selection: exact PVW/MAT mainline, compact complete-SAB denied.",docs/stage223_route_selection.md; repro/stage223_route_selection/proof_gate.csv
""",
    )
    append_once(
        MANIFEST,
        "- stage223_route_selection:",
        """
- stage223_route_selection:
  - `docs/stage223_route_selection.md`
  - `experiments/stage223_route_selection_plan.md`
  - `theory_checks/stage223_route_selection_model.md`
  - `algorithm_variants/mat_rlwe_sab_stage223_route_selection.md`
  - `scripts/build_stage223_route_selection.py`
  - `repro/stage223_route_selection/`
""",
    )
    append_once(
        CHECKLIST,
        "Stage223 route selection recorded",
        """
- [x] Stage223 route selection recorded.
""",
    )


def write_artifacts(paths: Iterable[Path]) -> None:
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
    write_csv(ARTIFACT, rows, ["path", "exists", "sha256", "bytes"])


def main() -> int:
    OUT.mkdir(parents=True, exist_ok=True)
    inputs = build_inputs()
    evidence = build_evidence()
    routes = build_routes()
    proof = build_proof(inputs, evidence, routes)
    next_rows = build_next(proof[-1]["status"])
    write_csv(INPUTS, inputs, INPUT_FIELDS)
    write_csv(EVIDENCE, evidence, EVIDENCE_FIELDS)
    write_csv(ROUTES, routes, ROUTE_FIELDS)
    write_csv(PROOF, proof, ["gate", "status", "metric", "value", "evidence", "interpretation"])
    write_csv(NEXT, next_rows, ["priority", "route", "entry_condition", "gate", "status", "failure_action", "evidence"])
    write_docs(inputs, evidence, routes, proof, next_rows)
    status = proof[-1]["status"]
    update_tracking(status)
    write_artifacts([DOC, PLAN, THEORY, VARIANT, INPUTS, EVIDENCE, ROUTES, PROOF, NEXT, REPORT, REPRO, Path(__file__)])
    print(status)
    return 0 if status == DECISION else 1


if __name__ == "__main__":
    raise SystemExit(main())
