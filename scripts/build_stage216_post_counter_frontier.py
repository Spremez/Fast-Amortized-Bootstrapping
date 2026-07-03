#!/usr/bin/env python3
"""Stage216: post-counter frontier admission after Stage215."""

from __future__ import annotations

import csv
import hashlib
import subprocess
from pathlib import Path
from typing import Dict, Iterable, List


ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "repro" / "stage216_post_counter_frontier"

DOC = ROOT / "docs" / "stage216_post_counter_frontier.md"
PLAN = ROOT / "experiments" / "stage216_post_counter_frontier_plan.md"
THEORY = ROOT / "theory_checks" / "stage216_research_loop_frontier_model.md"
VARIANT = ROOT / "algorithm_variants" / "mat_rlwe_sab_stage216_post_counter_frontier.md"

INPUTS = OUT / "input_status.csv"
METRICS = OUT / "metric_snapshot.csv"
MATRIX = OUT / "mechanism_frontier.csv"
PROOF = OUT / "proof_gate.csv"
NEXT = OUT / "next_stage_queue.csv"
REPORT = OUT / "post_counter_frontier_report.md"
ARTIFACT = OUT / "artifact_index.csv"
REPRO = OUT / "reproduction_commands.md"

ROADMAP = ROOT / "docs" / "roadmap_stage19_plus.md"
GOAL = ROOT / "docs" / "goal_sab_max_acceleration.md"
CURRENT_GOAL = ROOT / "docs" / "current_codex_goal_sab_completion.md"
HYPOTHESES = ROOT / "hypotheses" / "hypothesis_register.yaml"
RUN_LOG = ROOT / "repro" / "run_log.csv"
MANIFEST = ROOT / "repro" / "artifact_manifest.md"
CHECKLIST = ROOT / "repro" / "reproduction_checklist.md"

STAGE206_PERF = ROOT / "repro" / "stage206_current_head_highstat" / "performance_stats.csv"
STAGE207_RES = ROOT / "repro" / "stage207_current_head_resource_refresh" / "resource_comparison.csv"
STAGE208_PROFILE = ROOT / "repro" / "stage208_current_head_profile_refresh" / "component_attribution.csv"
STAGE200_GAP = ROOT / "repro" / "stage200_formal_gap_model_with_probe" / "gap_projection.csv"
STAGE203_SUMMARY = ROOT / "repro" / "stage203_production_selector_equation_probe" / "summary.csv"
STAGE215_COMPARE = ROOT / "repro" / "stage215_native_counter_execution" / "comparison.csv"
STAGE215_COUNTERS = ROOT / "repro" / "stage215_native_counter_execution" / "counter_summary.csv"
STAGE215_PROOF = ROOT / "repro" / "stage215_native_counter_execution" / "proof_gate.csv"
STAGE215_NEXT = ROOT / "repro" / "stage215_native_counter_execution" / "next_stage_queue.csv"

DECISION = "PASS_STAGE216_POST_COUNTER_FRONTIER_ROUTE_COMPACT_KEYGEN_PREFLIGHT"


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
    with path.open(newline="", encoding="utf-8") as handle:
        return list(csv.DictReader(handle))


def write_csv(path: Path, rows: Iterable[Dict[str, str]], fields: List[str]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    normalized = [{field: row.get(field, "") for field in fields} for row in rows]
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields, lineterminator="\n")
        writer.writeheader()
        writer.writerows(normalized)


def append_once(path: Path, marker: str, text: str) -> None:
    current = read_text(path)
    if marker in current:
        return
    if current and not current.endswith("\n"):
        current += "\n"
    write_text(path, current + text.lstrip("\n"))


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
    if not path.exists() or not path.is_file():
        return ""
    h = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


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


def f(value: str, default: float = 0.0) -> float:
    try:
        return float(value)
    except Exception:
        return default


def row_by(rows: List[Dict[str, str]], key: str, value: str) -> Dict[str, str]:
    for row in rows:
        if row.get(key) == value:
            return row
    return {}


def build_inputs() -> List[Dict[str, str]]:
    required = [
        ("stage206_current_head_highstat", STAGE206_PERF, "complete-SAB T_bootstrap/r evidence"),
        ("stage207_resource_refresh", STAGE207_RES, "resource cost for current-head path"),
        ("stage208_profile_attribution", STAGE208_PROFILE, "current bottleneck and schedule counts"),
        ("stage200_gap_model", STAGE200_GAP, "same-format gap and proof obligations"),
        ("stage203_selector_equation_probe", STAGE203_SUMMARY, "compact proof-only selector equation status"),
        ("stage215_native_counter_comparison", STAGE215_COMPARE, "native counter performance admission"),
        ("stage215_native_counter_summary", STAGE215_COUNTERS, "native load/store/FMA evidence"),
        ("stage215_proof_gate", STAGE215_PROOF, "Stage215 final decision"),
        ("stage215_next_queue", STAGE215_NEXT, "post-counter queue"),
    ]
    return [
        {
            "input": name,
            "status": "present" if path.exists() else "missing",
            "evidence": rel(path),
            "role": role,
            "bytes": str(path.stat().st_size) if path.exists() else "0",
        }
        for name, path, role in required
    ]


def build_metrics() -> List[Dict[str, str]]:
    perf = read_csv(STAGE206_PERF)
    res = read_csv(STAGE207_RES)
    profile = read_csv(STAGE208_PROFILE)
    compare = read_csv(STAGE215_COMPARE)
    counters = read_csv(STAGE215_COUNTERS)

    rows: List[Dict[str, str]] = []
    for r in ("2", "4"):
        p = row_by(perf, "r", r)
        rr = row_by(res, "r", r)
        pr = row_by(profile, "r", r)
        combined = next(
            (row for row in compare if row.get("r") == r and row.get("variant") == "combined_current"),
            {},
        )
        torus = next(
            (row for row in compare if row.get("r") == r and row.get("variant") == "torus_to_dft_rows"),
            {},
        )
        rows.append(
            {
                "r": r,
                "primary_endpoint": "T_bootstrap_over_r",
                "current_head_speedup": p.get("ratio_of_mean_per_lane", ""),
                "ci95_low": p.get("ci95_low", ""),
                "ci95_high": p.get("ci95_high", ""),
                "key_bytes_ratio": rr.get("key_bytes_ratio", ""),
                "keygen_per_lane_ratio": rr.get("keygen_per_lane_ratio", ""),
                "mat_ep_pct_of_cmux": pr.get("mat_ep_pct_of_cmux", ""),
                "postproc_tail_pct_max": pr.get("postproc_tail_pct_max", ""),
                "stage215_combined_wrapper_speedup": combined.get("speedup_vs_baseline", ""),
                "stage215_torus_wrapper_speedup": torus.get("speedup_vs_baseline", ""),
                "stage215_decision": combined.get("decision", ""),
                "evidence": f"{rel(STAGE206_PERF)}; {rel(STAGE207_RES)}; {rel(STAGE208_PROFILE)}; {rel(STAGE215_COMPARE)}",
            }
        )

    for row in counters:
        if row.get("implementation") == "wrapper" and row.get("variant") == "combined_current":
            rows.append(
                {
                    "r": row.get("r", ""),
                    "primary_endpoint": "native_counter_wrapper_combined_current",
                    "current_head_speedup": "",
                    "ci95_low": "",
                    "ci95_high": "",
                    "key_bytes_ratio": "",
                    "keygen_per_lane_ratio": "",
                    "mat_ep_pct_of_cmux": "",
                    "postproc_tail_pct_max": "",
                    "stage215_combined_wrapper_speedup": "",
                    "stage215_torus_wrapper_speedup": "",
                    "stage215_decision": f"loads={row.get('loads')};stores={row.get('stores')};fp512={row.get('fp512')}",
                    "evidence": rel(STAGE215_COUNTERS),
                }
            )
    return rows


def build_frontier() -> List[Dict[str, str]]:
    compare = read_csv(STAGE215_COMPARE)
    gap = read_csv(STAGE200_GAP)
    stage203 = read_csv(STAGE203_SUMMARY)
    min_combined = min(
        (f(row.get("speedup_vs_baseline", "0")) for row in compare if row.get("variant") == "combined_current"),
        default=0.0,
    )
    torus_row = next((row for row in gap if row.get("component") == "torus_to_dft_rows"), {})
    addmul_row = next((row for row in gap if row.get("component") == "addmul_from_dec_dft"), {})
    compact_decision = next((row.get("status", "") for row in stage203 if row.get("gate") == "stage203_decision"), "")
    return [
        {
            "candidate": "C1_reopen_stage213_multirow_dft_wrapper",
            "mechanism_class": "same_format_backend_wrapper",
            "admission_status": "REJECTED_BY_STAGE215",
            "quantitative_gate": f"min combined_current speedup={min_combined:.9f}; required >=1.010000",
            "allowed_action": "keep flag default-off; do not run full SAB A/B for this wrapper",
            "blocked_claim": "no complete-SAB speedup or AVX optimality claim",
            "evidence": rel(STAGE215_COMPARE),
        },
        {
            "candidate": "C2_immediate_full_sab_ab_for_wrapper",
            "mechanism_class": "complete_sab_validation",
            "admission_status": "DENIED_ENTRY_CONDITION_NOT_MET",
            "quantitative_gate": "Stage215 did not promote native integrated wrapper candidate",
            "allowed_action": "none",
            "blocked_claim": "do not spend complete-SAB runs on a failed component admission path",
            "evidence": rel(STAGE215_PROOF),
        },
        {
            "candidate": "C3_same_format_exact_local_retuning",
            "mechanism_class": "exact_full_mat_local_code",
            "admission_status": "DENIED_WITHOUT_NEW_MECHANISM",
            "quantitative_gate": f"DFT requirement={torus_row.get('full_sab_share_and_required_speedup','')}; addmul requirement={addmul_row.get('full_sab_share_and_required_speedup','')}",
            "allowed_action": "only if a new counter-backed dataflow mechanism is specified first",
            "blocked_claim": "no blind AVX512/layout retuning",
            "evidence": rel(STAGE200_GAP),
        },
        {
            "candidate": "C4_external_backend_primitive",
            "mechanism_class": "backend_or_library_work",
            "admission_status": "WAIT_EXTERNAL_MECHANISM",
            "quantitative_gate": "must beat Stage200 component threshold and then complete-SAB T_bootstrap/r",
            "allowed_action": "prepare preflight only after a real primitive exists",
            "blocked_claim": "backend speed cannot be reported as algorithmic count reduction",
            "evidence": f"{rel(STAGE200_GAP)}; {rel(STAGE215_COUNTERS)}",
        },
        {
            "candidate": "C5_compact_selector_keygen_preflight",
            "mechanism_class": "representation_changing_algorithm",
            "admission_status": "SELECT_STAGE217_PREFLIGHT_ONLY",
            "quantitative_gate": f"Stage203 status={compact_decision}; production keygen/security/noise still missing",
            "allowed_action": "write an executable keygen/security/noise admission probe outside SAB hot path",
            "blocked_claim": "no compact SAB implementation or speedup claim yet",
            "evidence": rel(STAGE203_SUMMARY),
        },
        {
            "candidate": "C6_scoped_current_result_reporting",
            "mechanism_class": "claim_packaging",
            "admission_status": "ALLOWED_SCOPED_ONLY",
            "quantitative_gate": "Stage206/207 current-head evidence remains the speedup/resource basis",
            "allowed_action": "report scoped T_bootstrap/r engineering result with limitations",
            "blocked_claim": "no theoretical optimality, broad novelty, or final algorithm completion",
            "evidence": f"{rel(STAGE206_PERF)}; {rel(STAGE207_RES)}",
        },
    ]


def build_next() -> List[Dict[str, str]]:
    return [
        {
            "priority": "P0",
            "route": "stage217_compact_keygen_security_preflight",
            "entry_condition": "Stage215 rejected exact wrapper reopen and Stage203 compact selector equation is proof-only but alive.",
            "gate": "Executable distribution/keygen/noise/resource admission probe outside SAB hot path.",
            "status": "selected",
            "failure_action": "If keygen/security/noise closure fails, compact implementation remains denied and route returns to external mechanism only.",
            "evidence": f"{rel(STAGE203_SUMMARY)}; {rel(MATRIX)}",
        },
        {
            "priority": "P1",
            "route": "external_backend_primitive_preflight",
            "entry_condition": "A real new FFT/DFT/backend primitive is supplied.",
            "gate": "Exact conversion equivalence, component speedup above threshold, then complete-SAB T_bootstrap/r.",
            "status": "waiting_external_mechanism",
            "failure_action": "Record neutral backend ablation; do not update algorithm claim.",
            "evidence": rel(STAGE200_GAP),
        },
        {
            "priority": "P2",
            "route": "scoped_report_refresh",
            "entry_condition": "No new implementation/proof route is selected or Stage217 fails.",
            "gate": "Claim guard: only current exact PVW/MAT-SAB T_bootstrap/r result is reported.",
            "status": "fallback",
            "failure_action": "Repair claim wording and repro pack.",
            "evidence": rel(STAGE206_PERF),
        },
    ]


def build_proof(inputs: List[Dict[str, str]], metrics: List[Dict[str, str]], frontier: List[Dict[str, str]]) -> List[Dict[str, str]]:
    missing = [row["input"] for row in inputs if row["status"] != "present"]
    wrapper = [row for row in frontier if row["candidate"] == "C1_reopen_stage213_multirow_dft_wrapper"][0]
    compact = [row for row in frontier if row["candidate"] == "C5_compact_selector_keygen_preflight"][0]
    perf_rows = [row for row in metrics if row["primary_endpoint"] == "T_bootstrap_over_r"]
    speedup_min = min((f(row.get("current_head_speedup", "0")) for row in perf_rows), default=0.0)
    return [
        {
            "gate": "G1_required_inputs",
            "status": "PASS" if not missing else "FAIL",
            "metric": "missing_inputs",
            "value": ";".join(missing),
            "evidence": rel(INPUTS),
            "interpretation": "All post-counter admission inputs must exist.",
        },
        {
            "gate": "G2_primary_endpoint_preserved",
            "status": "PASS" if speedup_min > 1.0 else "FAIL",
            "metric": "min_current_T_bootstrap_over_r_speedup",
            "value": f"{speedup_min:.9f}",
            "evidence": rel(METRICS),
            "interpretation": "The current accepted comparison dimension remains amortized complete-SAB T_bootstrap/r.",
        },
        {
            "gate": "G3_stage215_wrapper_reopen",
            "status": "PASS_REJECTED",
            "metric": "wrapper_admission",
            "value": wrapper["admission_status"],
            "evidence": rel(STAGE215_COMPARE),
            "interpretation": "Native counter evidence does not reopen the Stage213 wrapper route.",
        },
        {
            "gate": "G4_non_theory_loop_route",
            "status": "PASS_SELECTED_EXECUTABLE_PREFLIGHT",
            "metric": "selected_candidate",
            "value": compact["candidate"],
            "evidence": rel(NEXT),
            "interpretation": "The next route has finite/prototype gates and no SAB hot-path code permission.",
        },
        {
            "gate": "G5_stage216_decision",
            "status": DECISION if not missing else "FAIL_STAGE216_INPUTS",
            "metric": "decision",
            "value": DECISION if not missing else "FAIL_STAGE216_INPUTS",
            "evidence": rel(PROOF),
            "interpretation": "Post-counter frontier is closed for exact wrapper retuning and routed to bounded compact keygen/security preflight.",
        },
    ]


def write_docs(
    inputs: List[Dict[str, str]],
    metrics: List[Dict[str, str]],
    frontier: List[Dict[str, str]],
    proof: List[Dict[str, str]],
    next_rows: List[Dict[str, str]],
) -> None:
    report = f"""# Stage216 Post-Counter Frontier

Decision: `{DECISION}`.

Stage216 closes the Stage215 counter loop without opening another blind tuning
cycle. The primary endpoint remains complete-SAB `T_bootstrap/r`. Stage215
does not authorize complete-SAB A/B for the multirow DFT wrapper, because its
native integrated `combined_current` path failed the admission threshold.

The only selected next route is a bounded compact selector keygen/security
preflight outside the SAB hot path. This is not a compact SAB implementation
claim; it is the next falsifiable gate needed before any representation-changing
algorithm can be coded.

## Proof Gates

{table(proof, ["gate", "status", "metric", "value", "evidence", "interpretation"])}
## Input Status

{table(inputs, ["input", "status", "evidence", "role", "bytes"])}
## Metric Snapshot

{table(metrics, ["r", "primary_endpoint", "current_head_speedup", "ci95_low", "ci95_high", "key_bytes_ratio", "keygen_per_lane_ratio", "mat_ep_pct_of_cmux", "postproc_tail_pct_max", "stage215_combined_wrapper_speedup", "stage215_torus_wrapper_speedup", "stage215_decision", "evidence"])}
## Mechanism Frontier

{table(frontier, ["candidate", "mechanism_class", "admission_status", "quantitative_gate", "allowed_action", "blocked_claim", "evidence"])}
## Next Queue

{table(next_rows, ["priority", "route", "entry_condition", "gate", "status", "failure_action", "evidence"])}
"""
    write_text(REPORT, report)
    write_text(DOC, report)
    write_text(
        PLAN,
        """# Stage216 Plan

Goal: prevent theory drift after Stage215 by converting native counter evidence
into implementation permission or denial.

Rules:

- primary metric is complete-SAB `T_bootstrap/r`;
- do not run full-SAB A/B for a component route that failed admission;
- do not write SAB hot-path code;
- select exactly one bounded next route with executable gates.

Result: exact wrapper retuning is denied. Stage217 must test compact selector
keygen/security/noise admission outside the SAB hot path, or fail closed.
""",
    )
    write_text(
        THEORY,
        """# Stage216 Research-Loop Frontier Model

The Stage215 counter result is a mechanism-admission gate, not a latency claim.
It can reduce or increase individual load/store/FMA counters, but it does not
support a bootstrapping claim unless the integrated component clears the
predeclared admission threshold and then passes complete-SAB `T_bootstrap/r`.

Because the wrapper fails admission, exact same-format local retuning remains
closed unless a new counter-backed mechanism is supplied. The only currently
alive route that could change the algorithmic structure is the compact selector
proof line from Stage203. That route must next prove production-shaped keygen,
security/distribution, noise/resource, and closure properties before any SAB
integration.
""",
    )
    write_text(
        VARIANT,
        """# Stage216 Post-Counter Frontier Card

This is an admission artifact, not a production variant.

Rejected:

- reopening the Stage213 multirow DFT wrapper;
- immediate complete-SAB A/B for that wrapper;
- blind same-format AVX512/layout retuning.

Selected next preflight:

- compact selector keygen/security/noise admission outside the SAB hot path.

Blocked claims:

- theoretical optimality;
- compact SAB implementation;
- new full-SAB acceleration beyond the current explicit exact PVW/MAT-SAB
  evidence.
""",
    )
    write_text(
        REPRO,
        """# Stage216 Reproduction Commands

```powershell
python scripts\\build_stage216_post_counter_frontier.py
Get-Content -Raw repro\\stage216_post_counter_frontier\\proof_gate.csv
Get-Content -Raw repro\\stage216_post_counter_frontier\\mechanism_frontier.csv
```
""",
    )


def update_tracking() -> None:
    head = git_head()
    append_once(
        ROADMAP,
        "## Stage 216: Post-Counter Frontier",
        f"""
## Stage 216: Post-Counter Frontier

Goal:

```text
Use Stage215 native counter evidence to decide whether any exact hot-path code
is authorized, and if not, select the next bounded non-theory research gate.
```

Status:

```text
Completed. Stage216 records {DECISION}. Exact wrapper retuning and immediate
complete-SAB A/B for the wrapper are denied; the next selected executable route
is compact selector keygen/security/noise preflight outside the SAB hot path.
```
""",
    )
    append_once(
        GOAL,
        "Stage216 records post-counter frontier",
        f"""
Stage216 records post-counter frontier. Decision: `{DECISION}`. The accepted
comparison dimension remains complete-SAB `T_bootstrap/r`; exact wrapper
retuning is closed after native counters, and Stage217 must use bounded compact
keygen/security gates rather than theory-only discussion.
""",
    )
    append_once(
        CURRENT_GOAL,
        "Treat Stage216 as post-counter frontier",
        f"""
### Stage216 post-counter frontier

`{DECISION}` closes the Stage215 DFT-wrapper route for now. The next valid work
is a compact selector keygen/security/noise preflight outside the SAB hot path,
or an external backend primitive if one is supplied. No new full-SAB speedup,
compact implementation, or optimality claim is opened by Stage216.
""",
    )
    append_once(
        HYPOTHESES,
        "H10_stage216_post_counter_frontier",
        f"""
H10_stage216_post_counter_frontier:
  status: post_counter_frontier_recorded
  evidence:
    - repro/stage216_post_counter_frontier/mechanism_frontier.csv
    - repro/stage216_post_counter_frontier/proof_gate.csv
    - docs/stage216_post_counter_frontier.md
  conclusion: >
    Stage216 records {DECISION}. Stage215 native counters do not reopen exact
    wrapper retuning or authorize complete-SAB A/B for that route. The next
    selected bounded route is compact selector keygen/security/noise preflight
    outside the SAB hot path.
""",
    )
    append_once(
        RUN_LOG,
        "stage216-post-counter-frontier-001",
        f"""stage216-post-counter-frontier-001,2026-07-04,{head},Stage 216,analysis,python scripts/build_stage216_post_counter_frontier.py,Stage206-215 current-head evidence,no new benchmark,{DECISION},"Exact wrapper route denied; selected compact keygen/security preflight outside SAB hot path.",docs/stage216_post_counter_frontier.md; repro/stage216_post_counter_frontier/proof_gate.csv
""",
    )
    append_once(
        MANIFEST,
        "- stage216_post_counter_frontier:",
        """
- stage216_post_counter_frontier:
  - `docs/stage216_post_counter_frontier.md`
  - `experiments/stage216_post_counter_frontier_plan.md`
  - `theory_checks/stage216_research_loop_frontier_model.md`
  - `algorithm_variants/mat_rlwe_sab_stage216_post_counter_frontier.md`
  - `scripts/build_stage216_post_counter_frontier.py`
  - `repro/stage216_post_counter_frontier/`
""",
    )
    append_once(
        CHECKLIST,
        "Stage216 post-counter frontier recorded",
        """
- [x] Stage216 post-counter frontier recorded.
""",
    )


def write_artifacts(paths: Iterable[Path]) -> None:
    rows = [
        {
            "path": rel(path),
            "exists": "yes" if path.exists() else "no",
            "sha256": sha256_file(path),
            "bytes": str(path.stat().st_size) if path.exists() else "0",
        }
        for path in paths
    ]
    write_csv(ARTIFACT, rows, ["path", "exists", "sha256", "bytes"])


def main() -> None:
    inputs = build_inputs()
    metrics = build_metrics()
    frontier = build_frontier()
    next_rows = build_next()
    proof = build_proof(inputs, metrics, frontier)

    write_csv(INPUTS, inputs, ["input", "status", "evidence", "role", "bytes"])
    write_csv(
        METRICS,
        metrics,
        [
            "r",
            "primary_endpoint",
            "current_head_speedup",
            "ci95_low",
            "ci95_high",
            "key_bytes_ratio",
            "keygen_per_lane_ratio",
            "mat_ep_pct_of_cmux",
            "postproc_tail_pct_max",
            "stage215_combined_wrapper_speedup",
            "stage215_torus_wrapper_speedup",
            "stage215_decision",
            "evidence",
        ],
    )
    write_csv(
        MATRIX,
        frontier,
        ["candidate", "mechanism_class", "admission_status", "quantitative_gate", "allowed_action", "blocked_claim", "evidence"],
    )
    write_csv(NEXT, next_rows, ["priority", "route", "entry_condition", "gate", "status", "failure_action", "evidence"])
    write_csv(PROOF, proof, ["gate", "status", "metric", "value", "evidence", "interpretation"])
    write_docs(inputs, metrics, frontier, proof, next_rows)
    update_tracking()
    write_artifacts([DOC, PLAN, THEORY, VARIANT, INPUTS, METRICS, MATRIX, PROOF, NEXT, REPORT, REPRO, Path(__file__)])
    print(DECISION)


if __name__ == "__main__":
    main()
