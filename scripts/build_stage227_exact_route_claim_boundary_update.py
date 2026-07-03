#!/usr/bin/env python3
"""Stage227: fix claim boundaries after exact-route performance, side conditions, and counters."""

from __future__ import annotations

import csv
import hashlib
import subprocess
from pathlib import Path
from typing import Dict, Iterable, List


ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "repro" / "stage227_exact_route_claim_boundary_update"

DOC = ROOT / "docs" / "stage227_exact_route_claim_boundary_update.md"
PLAN = ROOT / "experiments" / "stage227_exact_route_claim_boundary_update_plan.md"
THEORY = ROOT / "theory_checks" / "stage227_claim_boundary_model.md"
VARIANT = ROOT / "algorithm_variants" / "mat_rlwe_sab_stage227_claim_boundary.md"

INPUTS = OUT / "input_status.csv"
METRICS = OUT / "metric_ledger.csv"
CLAIMS = OUT / "claim_matrix.csv"
PROOF = OUT / "proof_gate.csv"
NEXT = OUT / "next_stage_queue.csv"
REPORT = OUT / "claim_boundary_report.md"
ARTIFACT = OUT / "artifact_index.csv"
REPRO = OUT / "reproduction_commands.md"

ROADMAP = ROOT / "docs" / "roadmap_stage19_plus.md"
GOAL = ROOT / "docs" / "goal_sab_max_acceleration.md"
CURRENT_GOAL = ROOT / "docs" / "current_codex_goal_sab_completion.md"
HYPOTHESES = ROOT / "hypotheses" / "hypothesis_register.yaml"
RUN_LOG = ROOT / "repro" / "run_log.csv"
MANIFEST = ROOT / "repro" / "artifact_manifest.md"
CHECKLIST = ROOT / "repro" / "reproduction_checklist.md"

STAGE224_PROOF = ROOT / "repro" / "stage224_exact_pvw_mat_avx_resource_refresh" / "proof_gate.csv"
STAGE224_PERF = ROOT / "repro" / "stage224_exact_pvw_mat_avx_resource_refresh" / "perf_comparison.csv"
STAGE225_PROOF = ROOT / "repro" / "stage225_exact_refresh_noise_resource_rerun" / "proof_gate.csv"
STAGE225_NOISE = ROOT / "repro" / "stage225_exact_refresh_noise_resource_rerun" / "noise_aggregate.csv"
STAGE225_RESOURCE = ROOT / "repro" / "stage225_exact_refresh_noise_resource_rerun" / "resource_comparison.csv"
STAGE226_PROOF = ROOT / "repro" / "stage226_exact_mat_avx_counter_attribution" / "proof_gate.csv"
STAGE226_ATTR = ROOT / "repro" / "stage226_exact_mat_avx_counter_attribution" / "attribution_summary.csv"
STAGE226_NEXT = ROOT / "repro" / "stage226_exact_mat_avx_counter_attribution" / "next_stage_queue.csv"


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
    with path.open("r", newline="", encoding="utf-8-sig") as handle:
        return list(csv.DictReader(handle))


def write_csv(path: Path, rows: Iterable[Dict[str, str]], fields: List[str]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    rows = [{field: row.get(field, "") for field in fields} for row in rows]
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields, lineterminator="\n")
        writer.writeheader()
        writer.writerows(rows)


def append_once(path: Path, marker: str, text: str) -> None:
    current = read_text(path)
    if marker in current:
        return
    if current and not current.endswith("\n"):
        current += "\n"
    write_text(path, current + text.lstrip("\n"))


def table(rows: List[Dict[str, str]], fields: List[str]) -> str:
    if not rows:
        return "_No rows._\n"
    out = [
        "| " + " | ".join(fields) + " |",
        "| " + " | ".join("---" for _ in fields) + " |",
    ]
    for row in rows:
        out.append("| " + " | ".join(str(row.get(field, "")).replace("|", "\\|") for field in fields) + " |")
    return "\n".join(out) + "\n"


def sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def git_head() -> str:
    return subprocess.check_output(["git", "rev-parse", "--short", "HEAD"], cwd=ROOT, text=True).strip()


def val(rows: List[Dict[str, str]], key: str, key_field: str = "metric", value_field: str = "value") -> str:
    for row in rows:
        if row.get(key_field) == key:
            return row.get(value_field, "")
    return ""


def proof_decision(path: Path) -> str:
    rows = read_csv(path)
    return rows[-1].get("value", "") if rows else ""


def input_rows() -> List[Dict[str, str]]:
    inputs = [
        (STAGE224_PROOF, "Stage224 exact route performance admission"),
        (STAGE224_PERF, "Stage224 repeated complete-SAB timing"),
        (STAGE225_PROOF, "Stage225 fresh side-condition gate"),
        (STAGE225_NOISE, "Stage225 fresh noise/correctness aggregate"),
        (STAGE225_RESOURCE, "Stage225 fresh resource comparison"),
        (STAGE226_PROOF, "Stage226 counter gate"),
        (STAGE226_ATTR, "Stage226 counter attribution summary"),
        (STAGE226_NEXT, "Stage226 selected claim-boundary route"),
    ]
    return [
        {
            "input": rel(path),
            "status": "present" if path.exists() else "missing",
            "role": role,
            "bytes": str(path.stat().st_size) if path.exists() else "",
        }
        for path, role in inputs
    ]


def selected_by_stage226() -> bool:
    return any(row.get("route") == "stage227_exact_route_claim_boundary_update" and row.get("status") == "selected" for row in read_csv(STAGE226_NEXT))


def metric_rows() -> List[Dict[str, str]]:
    perf = read_csv(STAGE224_PERF)
    noise = read_csv(STAGE225_NOISE)
    resource = read_csv(STAGE225_RESOURCE)
    attr = read_csv(STAGE226_ATTR)
    perf_row = perf[0] if perf else {}
    noise_row = noise[0] if noise else {}
    resource_row = resource[0] if resource else {}
    rows = [
        {
            "metric": "primary_metric",
            "value": "T_bootstrap_per_lane",
            "dimension": "complete SAB time divided by r MAT bodies / plaintext lanes",
            "evidence": rel(STAGE224_PERF),
            "interpretation": "All speedup claims must use per-lane amortized throughput, not total one-call latency alone.",
        },
        {
            "metric": "stage224_backend_vs_scalar_repeated",
            "value": perf_row.get("backend_mean_speedup_vs_scalar", ""),
            "dimension": "T_scalar_repeated/r over T_pvw/r",
            "evidence": rel(STAGE224_PERF),
            "interpretation": "Fresh current-head exact backend route speedup under Stage224 protocol.",
        },
        {
            "metric": "stage148_best_backend_vs_scalar_repeated",
            "value": perf_row.get("stage148_backend_speedup_vs_scalar", ""),
            "dimension": "T_scalar_repeated/r over T_pvw/r",
            "evidence": rel(STAGE224_PERF),
            "interpretation": "Best previously recorded exact-route scalar comparison kept as historical best.",
        },
        {
            "metric": "stage224_backend_vs_wrapper",
            "value": perf_row.get("backend_vs_wrapper_mean_speedup", ""),
            "dimension": "wrapper T_pvw/r over backend T_pvw/r",
            "evidence": rel(STAGE224_PERF),
            "interpretation": "Backend from-DFT-add refresh advantage inside exact MAT/PVW route.",
        },
        {
            "metric": "stage225_noise_failures",
            "value": f"{noise_row.get('pvw_failures','')}/{noise_row.get('scalar_failures','')}/{noise_row.get('pair_failures','')}",
            "dimension": "pvw/scalar/pair failures",
            "evidence": rel(STAGE225_NOISE),
            "interpretation": "Fresh side-condition correctness result.",
        },
        {
            "metric": "stage225_avg_noise_gap_log2",
            "value": noise_row.get("avg_pvw_minus_scalar_log2", ""),
            "dimension": "log2 sigma difference",
            "evidence": rel(STAGE225_NOISE),
            "interpretation": "Negative means PVW average final noise was lower in this sample.",
        },
        {
            "metric": "stage225_key_bytes_ratio",
            "value": resource_row.get("key_bytes_ratio", ""),
            "dimension": "PVW key bytes over repeated scalar key bytes",
            "evidence": rel(STAGE225_RESOURCE),
            "interpretation": "Resource cost that must be reported next to throughput.",
        },
        {
            "metric": "stage225_memory_ratio",
            "value": resource_row.get("vmhwm_ratio", ""),
            "dimension": "PVW VmHWM over repeated scalar VmHWM",
            "evidence": rel(STAGE225_RESOURCE),
            "interpretation": "Memory cost that must be reported next to throughput.",
        },
        {
            "metric": "stage226_counter_label",
            "value": val(attr, "attribution_label"),
            "dimension": "mechanism label",
            "evidence": rel(STAGE226_ATTR),
            "interpretation": "Counter support is scoped to exact backend-vs-wrapper mechanism.",
        },
        {
            "metric": "stage226_cycles_wrapper_over_backend",
            "value": val(attr, "stage226_cycles_wrapper_over_backend"),
            "dimension": "counter ratio",
            "evidence": rel(STAGE226_ATTR),
            "interpretation": "Above 1 means backend reduced cycles in the native counter run.",
        },
        {
            "metric": "stage226_loads_wrapper_over_backend",
            "value": val(attr, "stage226_loads_wrapper_over_backend"),
            "dimension": "counter ratio",
            "evidence": rel(STAGE226_ATTR),
            "interpretation": "Above 1 means backend reduced retired loads in the native counter run.",
        },
        {
            "metric": "stage226_stores_wrapper_over_backend",
            "value": val(attr, "stage226_stores_wrapper_over_backend"),
            "dimension": "counter ratio",
            "evidence": rel(STAGE226_ATTR),
            "interpretation": "Above 1 means backend reduced retired stores in the native counter run.",
        },
    ]
    return rows


def claim_rows(metrics: List[Dict[str, str]]) -> List[Dict[str, str]]:
    stage224_speed = val(metrics, "stage224_backend_vs_scalar_repeated")
    stage148_speed = val(metrics, "stage148_best_backend_vs_scalar_repeated")
    counter_label = val(metrics, "stage226_counter_label")
    return [
        {
            "claim_id": "C1_exact_complete_sab_throughput",
            "claim": f"Exact dense MAT/PVW SAB improves tested complete-SAB amortized throughput: current refresh {stage224_speed}x, historical best {stage148_speed}x.",
            "status": "supported_under_tested_protocol",
            "allowed_wording": "Use complete-SAB T_bootstrap/r on BINARY SET_2_3_2048 r=6 with listed backend flags.",
            "blocked_wording": "Do not call this a universal speedup across all parameters.",
            "evidence": f"{rel(STAGE224_PERF)}; {rel(STAGE225_PROOF)}",
        },
        {
            "claim_id": "C2_backend_counter_mechanism",
            "claim": f"Backend from-DFT-add has native counter support for the Stage224 direction: {counter_label}.",
            "status": "supported_as_mechanism_evidence",
            "allowed_wording": "Use as cycles/load/store attribution for exact backend-vs-wrapper.",
            "blocked_wording": "Do not use as proof of theoretical AVX optimality.",
            "evidence": rel(STAGE226_ATTR),
        },
        {
            "claim_id": "C3_side_conditions",
            "claim": "Fresh correctness/noise/resource side conditions pass for the exact route.",
            "status": "supported_under_sampled_protocol",
            "allowed_wording": "Report seed count, failure counts, key bytes and memory ratios.",
            "blocked_wording": "Do not omit key/memory/keygen overhead when claiming throughput.",
            "evidence": f"{rel(STAGE225_NOISE)}; {rel(STAGE225_RESOURCE)}",
        },
        {
            "claim_id": "C4_theoretical_optimality",
            "claim": "MAT/PVW-SAB has a completed r-body optimality proof.",
            "status": "not_supported",
            "allowed_wording": "Open target; current evidence is engineering plus bounded mechanism support.",
            "blocked_wording": "No optimality claim.",
            "evidence": rel(THEORY),
        },
        {
            "claim_id": "C5_compact_or_neighbor_route",
            "claim": "A compact neighbor-capable MAT state has been integrated into complete SAB.",
            "status": "not_supported",
            "allowed_wording": "Compact route remains proof-only/deferred after selector closure denial.",
            "blocked_wording": "Do not state compact SAB path is implemented.",
            "evidence": rel(STAGE226_NEXT),
        },
        {
            "claim_id": "C6_paper_novelty",
            "claim": "This is ready as a novelty claim against the literature.",
            "status": "not_supported_yet",
            "allowed_wording": "Requires related-work matrix and source-verified novelty audit.",
            "blocked_wording": "Do not call it novel without literature support.",
            "evidence": rel(NEXT),
        },
    ]


def decide(metrics: List[Dict[str, str]], claims: List[Dict[str, str]]) -> str:
    if not all(row["status"] == "present" for row in input_rows()):
        return "FAIL_STAGE227_MISSING_INPUTS"
    if not selected_by_stage226():
        return "FAIL_STAGE227_ROUTE_NOT_SELECTED"
    if not val(metrics, "stage224_backend_vs_scalar_repeated"):
        return "FAIL_STAGE227_MISSING_PRIMARY_METRIC"
    if val(metrics, "stage225_noise_failures") != "0/0/0":
        return "FAIL_STAGE227_SIDE_CONDITIONS"
    if val(metrics, "stage226_counter_label") != "COUNTER_SUPPORTS_STAGE224_DIRECTION":
        return "NEUTRAL_STAGE227_COUNTER_BOUNDARY_ONLY"
    if any(row["claim_id"] in {"C4_theoretical_optimality", "C5_compact_or_neighbor_route"} and row["status"] != "not_supported" for row in claims):
        return "FAIL_STAGE227_OVERCLAIM_GUARD"
    return "PASS_STAGE227_EXACT_ROUTE_CLAIM_BOUNDARY_FIXED"


def proof_rows(decision: str, metrics: List[Dict[str, str]], claims: List[Dict[str, str]]) -> List[Dict[str, str]]:
    return [
        {
            "gate": "G1_required_inputs",
            "status": "PASS" if all(row["status"] == "present" for row in input_rows()) else "FAIL",
            "metric": "inputs_present",
            "value": str(all(row["status"] == "present" for row in input_rows())).lower(),
            "evidence": rel(INPUTS),
            "interpretation": "Claim update consumes Stage224, Stage225 and Stage226 evidence.",
        },
        {
            "gate": "G2_metric_dimension",
            "status": "PASS" if val(metrics, "primary_metric") == "T_bootstrap_per_lane" else "FAIL",
            "metric": "primary_metric",
            "value": val(metrics, "primary_metric"),
            "evidence": rel(METRICS),
            "interpretation": "The comparison dimension is amortized time per handled plaintext lane.",
        },
        {
            "gate": "G3_side_conditions",
            "status": "PASS" if val(metrics, "stage225_noise_failures") == "0/0/0" else "FAIL",
            "metric": "noise_failures",
            "value": val(metrics, "stage225_noise_failures"),
            "evidence": rel(STAGE225_NOISE),
            "interpretation": "Throughput claim remains coupled to correctness/noise/resource evidence.",
        },
        {
            "gate": "G4_counter_mechanism",
            "status": "PASS" if val(metrics, "stage226_counter_label") == "COUNTER_SUPPORTS_STAGE224_DIRECTION" else "NEUTRAL",
            "metric": "counter_label",
            "value": val(metrics, "stage226_counter_label"),
            "evidence": rel(STAGE226_ATTR),
            "interpretation": "Counter evidence supports only the exact backend-vs-wrapper mechanism.",
        },
        {
            "gate": "G5_overclaim_guard",
            "status": "PASS",
            "metric": "unsupported_claims",
            "value": ";".join(row["claim_id"] for row in claims if row["status"].startswith("not_supported")),
            "evidence": rel(CLAIMS),
            "interpretation": "Theoretical optimality, compact route, and novelty remain blocked.",
        },
        {
            "gate": "G6_stage227_decision",
            "status": decision,
            "metric": "decision",
            "value": decision,
            "evidence": rel(PROOF),
            "interpretation": "Next work can be targeted implementation or literature audit, not unconstrained theory looping.",
        },
    ]


def next_rows(decision: str) -> List[Dict[str, str]]:
    return [
        {
            "priority": "P0",
            "route": "stage228_counter_driven_backend_kernel_search",
            "entry_condition": "Stage227 fixes exact-route claim boundary and Stage226 counters show small cycle/load/store reductions.",
            "gate": "Generate one or two concrete code hypotheses with microbench and full-SAB promotion gates.",
            "status": "selected" if decision.startswith("PASS_STAGE227") else "blocked",
            "failure_action": "Do not edit hot path without a falsifiable counter-backed hypothesis.",
            "evidence": rel(PROOF),
        },
        {
            "priority": "P1",
            "route": "stage229_parameter_generalization_matrix",
            "entry_condition": "Exact-route claim boundary is fixed.",
            "gate": "Run at least one smaller smoke parameter and target parameter matrix before general claims.",
            "status": "future",
            "failure_action": "Keep claims parameter-scoped.",
            "evidence": rel(CLAIMS),
        },
        {
            "priority": "P2",
            "route": "stage230_literature_novelty_audit",
            "entry_condition": "Before any paper novelty wording.",
            "gate": "Source-verified related-work matrix; no fabricated references.",
            "status": "future",
            "failure_action": "Engineering-only report.",
            "evidence": rel(CLAIMS),
        },
    ]


def write_reports(decision: str, inputs: List[Dict[str, str]], metrics: List[Dict[str, str]], claims: List[Dict[str, str]], gates: List[Dict[str, str]], queue: List[Dict[str, str]]) -> None:
    report = f"""# Stage227 Exact Route Claim Boundary Update

Decision: `{decision}`.

Stage227 fixes the current claim boundary for PVW/MAT-SAB. The object being
compared is complete SAB amortized by the number of handled lanes:
`T_bootstrap/r`. The currently supported route is the exact dense MAT/PVW
route, not a compact neighbor-capable route and not a theoretical optimality
result.

## Metric Ledger

{table(metrics, ["metric", "value", "dimension", "evidence", "interpretation"])}
## Claim Matrix

{table(claims, ["claim_id", "claim", "status", "allowed_wording", "blocked_wording", "evidence"])}
## Proof Gates

{table(gates, ["gate", "status", "metric", "value", "evidence", "interpretation"])}
## Next Queue

{table(queue, ["priority", "route", "entry_condition", "gate", "status", "failure_action", "evidence"])}
## Inputs

{table(inputs, ["input", "status", "role", "bytes"])}
"""
    write_text(DOC, report)
    write_text(REPORT, report)
    write_text(
        PLAN,
        """# Stage227 Claim Boundary Plan

1. Consume Stage224 performance, Stage225 side conditions and Stage226 counters.
2. Fix the primary comparison as complete-SAB `T_bootstrap/r`.
3. Mark supported, unsupported and future claims separately.
4. Select the next implementation stage only if it has a falsifiable gate.
""",
    )
    write_text(
        THEORY,
        """# Stage227 Claim Boundary Model

The exact MAT/PVW route changes the amortization object from one scalar SAB
lane to an r-body MAT-RLWE/PVW state. Therefore the fair primary metric is
complete bootstrapping time divided by handled lanes: `T_bootstrap/r`.

Current evidence supports a tested exact-route throughput improvement and a
small backend counter mechanism. It does not establish theoretical optimality,
parameter-universal behavior, compact-state correctness, or literature novelty.
""",
    )
    write_text(
        VARIANT,
        """# Algorithm Variant: Stage227 Claim-Bounded Exact MAT/PVW-SAB

This is not a new implementation variant. It is the claim boundary for the
existing exact dense MAT/PVW-SAB route after Stage224, Stage225 and Stage226.

Primary metric: complete SAB `T_bootstrap/r`.
""",
    )
    write_text(
        REPRO,
        """# Stage227 Reproduction Commands

```powershell
python scripts\\build_stage227_exact_route_claim_boundary_update.py
Get-Content repro\\stage227_exact_route_claim_boundary_update\\proof_gate.csv
Get-Content repro\\stage227_exact_route_claim_boundary_update\\claim_matrix.csv
```
""",
    )


def artifact_rows(paths: Iterable[Path]) -> List[Dict[str, str]]:
    rows = []
    for path in paths:
        rows.append(
            {
                "path": rel(path),
                "exists": "yes" if path.exists() else "no",
                "sha256": sha256(path) if path.exists() and path.is_file() else "",
                "bytes": str(path.stat().st_size) if path.exists() and path.is_file() else "",
            }
        )
    return rows


def update_tracking(decision: str) -> None:
    head = git_head()
    append_once(
        ROADMAP,
        "## Stage 227: Exact Route Claim Boundary Update",
        f"""
## Stage 227: Exact Route Claim Boundary Update

Goal:

```text
Freeze the supported and blocked claims after Stage224/225/226 so the next
work stays implementation- and evidence-driven.
```

Status:

```text
Completed at `{head}` with `{decision}`. The primary metric is complete-SAB
`T_bootstrap/r`; theoretical optimality and compact-route claims remain blocked.
```
""",
    )
    append_once(
        GOAL,
        "Stage227 exact route claim boundary",
        f"\n\n## Stage227 exact route claim boundary\n\nAt commit `{head}`, Stage227 records `{decision}` and fixes complete-SAB `T_bootstrap/r` as the comparison metric.\n",
    )
    append_once(
        CURRENT_GOAL,
        "Stage227 exact route claim boundary",
        f"\n\n### Stage227 exact route claim boundary\n\n`{decision}` separates supported exact-route results from blocked optimality, compact-route and novelty claims.\n",
    )
    append_once(
        HYPOTHESES,
        "H10_stage227_claim_boundary",
        f"""

H10_stage227_claim_boundary:
  status: claim_boundary_fixed
  evidence:
    - repro/stage227_exact_route_claim_boundary_update/claim_matrix.csv
    - repro/stage227_exact_route_claim_boundary_update/metric_ledger.csv
    - docs/stage227_exact_route_claim_boundary_update.md
  conclusion: >
    Stage227 records {decision}. Complete-SAB T_bootstrap/r is the primary
    metric; theoretical optimality and compact-route claims remain unsupported.
""",
    )
    append_once(
        RUN_LOG,
        "stage227-claim-boundary-001",
        f"""stage227-claim-boundary-001,2026-07-04,{head},Stage 227,spqlios_avx512,python scripts/build_stage227_exact_route_claim_boundary_update.py,claim boundary after exact-route performance/noise/resource/counters,T_bootstrap_per_lane,{decision},"No code hot-path change; fixes supported and blocked claim language.",docs/stage227_exact_route_claim_boundary_update.md; repro/stage227_exact_route_claim_boundary_update/proof_gate.csv
""",
    )
    append_once(
        MANIFEST,
        "- stage227_exact_route_claim_boundary_update:",
        """

- stage227_exact_route_claim_boundary_update:
  - `docs/stage227_exact_route_claim_boundary_update.md`
  - `experiments/stage227_exact_route_claim_boundary_update_plan.md`
  - `theory_checks/stage227_claim_boundary_model.md`
  - `algorithm_variants/mat_rlwe_sab_stage227_claim_boundary.md`
  - `scripts/build_stage227_exact_route_claim_boundary_update.py`
  - `repro/stage227_exact_route_claim_boundary_update/`
""",
    )
    append_once(CHECKLIST, "Stage227 exact route claim boundary", f"\n- [x] Stage227 exact route claim boundary records decision `{decision}`.\n")


def main() -> None:
    OUT.mkdir(parents=True, exist_ok=True)
    inputs = input_rows()
    metrics = metric_rows()
    claims = claim_rows(metrics)
    decision = decide(metrics, claims)
    gates = proof_rows(decision, metrics, claims)
    queue = next_rows(decision)

    write_csv(INPUTS, inputs, ["input", "status", "role", "bytes"])
    write_csv(METRICS, metrics, ["metric", "value", "dimension", "evidence", "interpretation"])
    write_csv(CLAIMS, claims, ["claim_id", "claim", "status", "allowed_wording", "blocked_wording", "evidence"])
    write_csv(PROOF, gates, ["gate", "status", "metric", "value", "evidence", "interpretation"])
    write_csv(NEXT, queue, ["priority", "route", "entry_condition", "gate", "status", "failure_action", "evidence"])
    write_reports(decision, inputs, metrics, claims, gates, queue)
    update_tracking(decision)
    write_csv(
        ARTIFACT,
        artifact_rows([DOC, PLAN, THEORY, VARIANT, INPUTS, METRICS, CLAIMS, PROOF, NEXT, REPORT, REPRO, Path(__file__).resolve()]),
        ["path", "exists", "sha256", "bytes"],
    )
    print(decision)


if __name__ == "__main__":
    main()
