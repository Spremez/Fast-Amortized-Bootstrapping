#!/usr/bin/env python3
"""Stage155: profile-backed same-format MAT-RLWE SAB frontier refresh.

This stage is deliberately evidence-driven. It consumes the latest full-SAB
and body-profile artifacts, computes schedule/component bounds, and records the
next valid implementation routes without modifying scalar/default SAB code.
"""

from __future__ import annotations

import csv
import hashlib
import re
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, Iterable, List


ROOT = Path(__file__).resolve().parents[1]
OUT_DIR = ROOT / "repro" / "stage155_same_format_frontier_refresh"

PROFILE_LOG = ROOT / "repro" / "stage153_dual_sub_fullsab_gate" / "dual_sub_h14_r6_profile" / "run.log"
STAGE148_SUMMARY = ROOT / "repro" / "stage148_h14_r6_repeated_refresh" / "summary.csv"
STAGE151_SUMMARY = ROOT / "repro" / "stage151_h14_r6_fulltile_backend_smoke" / "summary.csv"
STAGE153_SUMMARY = ROOT / "repro" / "stage153_dual_sub_fullsab_gate" / "summary.csv"
STAGE154_SUMMARY = ROOT / "repro" / "stage154_bodymajor_fullsab_closeout" / "summary.csv"

SUMMARY_CSV = OUT_DIR / "summary.csv"
COMPONENT_CSV = OUT_DIR / "component_shares.csv"
SCHEDULE_CSV = OUT_DIR / "schedule_invariants.csv"
CANDIDATE_CSV = OUT_DIR / "candidate_status.csv"
FRONTIER_CSV = OUT_DIR / "frontier_decision.csv"
NEXT_QUEUE_CSV = OUT_DIR / "next_stage_queue.csv"
ARTIFACT_CSV = OUT_DIR / "artifact_index.csv"

DOC_STAGE = ROOT / "docs" / "stage155_same_format_frontier_refresh.md"
DOC_PLAN = ROOT / "experiments" / "stage155_same_format_frontier_refresh_plan.md"
DOC_THEORY = ROOT / "theory_checks" / "stage155_same_format_frontier_model.md"
DOC_VARIANT = ROOT / "algorithm_variants" / "mat_rlwe_sab_same_format_frontier.md"

ROADMAP = ROOT / "docs" / "roadmap_stage19_plus.md"
GOAL_DOC = ROOT / "docs" / "goal_sab_max_acceleration.md"
CURRENT_GOAL = ROOT / "docs" / "current_codex_goal_sab_completion.md"
HYPOTHESES = ROOT / "hypotheses" / "hypothesis_register.yaml"
RUN_LOG = ROOT / "repro" / "run_log.csv"
MANIFEST = ROOT / "repro" / "artifact_manifest.md"
CHECKLIST = ROOT / "repro" / "reproduction_checklist.md"


PROFILE_RE = re.compile(r"([A-Za-z0-9_]+)=([A-Za-z0-9_.+-]+)")


def read_csv(path: Path) -> List[Dict[str, str]]:
    if not path.exists():
        return []
    with path.open("r", encoding="utf-8", newline="") as handle:
        return list(csv.DictReader(handle))


def write_csv(path: Path, rows: List[Dict[str, object]], fields: List[str]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields, lineterminator="\n")
        writer.writeheader()
        for row in rows:
            writer.writerow({field: row.get(field, "") for field in fields})


def append_once(path: Path, marker: str, text: str) -> None:
    current = path.read_text(encoding="utf-8") if path.exists() else ""
    if marker in current:
        return
    with path.open("a", encoding="utf-8", newline="\n") as handle:
        if current and not current.endswith("\n"):
            handle.write("\n")
        handle.write(text)


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def parse_profile_lines(path: Path) -> List[Dict[str, float]]:
    rows: List[Dict[str, float]] = []
    for line in path.read_text(encoding="ascii", errors="ignore").splitlines():
        if "SAB_PVW_BODY_PROFILE sample" not in line:
            continue
        parsed: Dict[str, float] = {}
        for key, value in PROFILE_RE.findall(line):
            try:
                parsed[key] = float(value)
            except ValueError:
                pass
        if parsed:
            rows.append(parsed)
    return rows


def avg(rows: Iterable[Dict[str, float]], key: str) -> float:
    vals = [row[key] for row in rows if key in row]
    return sum(vals) / len(vals) if vals else 0.0


def row_by_gate(rows: List[Dict[str, str]], gate: str) -> Dict[str, str]:
    for row in rows:
        if row.get("gate") == gate:
            return row
    return {}


def fmt(value: float, digits: int = 6) -> str:
    return f"{value:.{digits}f}"


def speedup_if_component_scaled(share: float, local_speedup: float) -> float:
    if local_speedup <= 0:
        return 0.0
    return 1.0 / ((1.0 - share) + (share / local_speedup))


def build() -> None:
    OUT_DIR.mkdir(parents=True, exist_ok=True)

    profile_rows = parse_profile_lines(PROFILE_LOG)
    if not profile_rows:
        raise RuntimeError(f"No SAB_PVW_BODY_PROFILE rows found in {PROFILE_LOG}")

    full_us = avg(profile_rows, "full_us")
    h = int(avg(profile_rows, "h"))
    r_prec = int(avg(profile_rows, "r_prec"))
    in_n = int(avg(profile_rows, "in_N"))
    lanes = int(avg(profile_rows, "lanes"))
    expected_cmux = (h + 1) * r_prec * in_n
    expected_ncmux = (h + 1) * ((1 << r_prec) - 1)
    expected_sub_a = h

    metrics = {
        "mat_ep": avg(profile_rows, "mat_ep_us"),
        "from_dft": avg(profile_rows, "cmux_from_dft_us"),
        "sub": avg(profile_rows, "cmux_sub_us"),
        "ncmux_auto": avg(profile_rows, "ncmux_auto_us"),
        "sub_a": avg(profile_rows, "sub_a_us"),
        "dual_sub_pair": avg(profile_rows, "dual_sub_pair_us"),
    }
    used_share = sum(metrics.values()) / full_us
    other_share = max(0.0, 1.0 - used_share)
    component_rows: List[Dict[str, object]] = []
    for name, us in metrics.items():
        share = us / full_us if full_us else 0.0
        component_rows.append(
            {
                "component": name,
                "avg_us": fmt(us, 3),
                "share_of_full": fmt(share),
                "ceiling_if_eliminated": fmt(speedup_if_component_scaled(share, 10**9)),
                "ceiling_if_2x_local": fmt(speedup_if_component_scaled(share, 2.0)),
                "interpretation": component_interpretation(name, share),
            }
        )
    component_rows.append(
        {
            "component": "unattributed_or_timer_overlap",
            "avg_us": fmt(other_share * full_us, 3),
            "share_of_full": fmt(other_share),
            "ceiling_if_eliminated": fmt(speedup_if_component_scaled(other_share, 10**9)),
            "ceiling_if_2x_local": fmt(speedup_if_component_scaled(other_share, 2.0)),
            "interpretation": "Profiler overlap and residual body work; do not target without finer instrumentation.",
        }
    )

    schedule_rows = [
        {
            "metric": "cmux_calls",
            "observed_avg": fmt(avg(profile_rows, "cmux_calls"), 0),
            "expected": expected_cmux,
            "status": "PASS" if int(avg(profile_rows, "cmux_calls")) == expected_cmux else "FAIL",
            "detail": "(h+1)*r_prec*in_N",
        },
        {
            "metric": "mat_ep_calls",
            "observed_avg": fmt(avg(profile_rows, "mat_ep_calls"), 0),
            "expected": expected_cmux,
            "status": "PASS" if int(avg(profile_rows, "mat_ep_calls")) == expected_cmux else "FAIL",
            "detail": "one MAT external product per CMUX/NCMUX update",
        },
        {
            "metric": "from_dft_calls",
            "observed_avg": fmt(avg(profile_rows, "cmux_from_dft_calls"), 0),
            "expected": expected_cmux,
            "status": "PASS" if int(avg(profile_rows, "cmux_from_dft_calls")) == expected_cmux else "FAIL",
            "detail": "same-format path materializes every update",
        },
        {
            "metric": "ncmux_calls",
            "observed_avg": fmt(avg(profile_rows, "ncmux_calls"), 0),
            "expected": expected_ncmux,
            "status": "PASS" if int(avg(profile_rows, "ncmux_calls")) == expected_ncmux else "FAIL",
            "detail": "(h+1)*(2^r_prec-1)",
        },
        {
            "metric": "sub_a_calls",
            "observed_avg": fmt(avg(profile_rows, "sub_a_calls"), 0),
            "expected": expected_sub_a,
            "status": "PASS" if int(avg(profile_rows, "sub_a_calls")) == expected_sub_a else "FAIL",
            "detail": "one sparse subtraction per nonzero sparse secret term",
        },
        {
            "metric": "copyback_calls",
            "observed_avg": fmt(avg(profile_rows, "copyback_calls"), 0),
            "expected": 0,
            "status": "PASS" if int(avg(profile_rows, "copyback_calls")) == 0 else "FAIL",
            "detail": "active-buffer fusion remains effective",
        },
        {
            "metric": "dual_sub_pair_calls",
            "observed_avg": fmt(avg(profile_rows, "dual_sub_pair_calls"), 0),
            "expected": expected_ncmux,
            "status": "PASS" if int(avg(profile_rows, "dual_sub_pair_calls")) == expected_ncmux else "FAIL",
            "detail": "only NCMUX/direct pairs can share the dual-sub input",
        },
    ]

    stage148_decision = row_by_gate(read_csv(STAGE148_SUMMARY), "stage148_decision").get("status", "MISSING")
    stage151_decision = row_by_gate(read_csv(STAGE151_SUMMARY), "stage151_decision").get("status", "MISSING")
    stage153_decision = row_by_gate(read_csv(STAGE153_SUMMARY), "stage153_decision").get("status", "MISSING")
    stage154_decision = row_by_gate(read_csv(STAGE154_SUMMARY), "stage154_decision").get("status", "MISSING")

    candidate_rows = [
        {
            "candidate": "H14-C1 backend FromDFT-add r=6",
            "latest_decision": stage148_decision,
            "action": "KEEP_EXPLICIT_CURRENT_HEAD",
            "reason": "Repeated T_bootstrap/r, noise, and resource gates pass; scalar/default unchanged.",
        },
        {
            "candidate": "r6 fulltile layout under H14",
            "latest_decision": stage151_decision,
            "action": "DO_NOT_PRIORITIZE",
            "reason": "Smoke signal is tiny and older repeated fulltile evidence was negative; only rerun if a new profile-backed reason appears.",
        },
        {
            "candidate": "H14-C3 dual-sub shared-input CMUX",
            "latest_decision": stage153_decision,
            "action": "CLOSE_LOCAL_PAIR_ROUTE",
            "reason": "Local kernel is positive, but pairable fraction is too small to move complete SAB.",
        },
        {
            "candidate": "r6 bodymajor layout under H14",
            "latest_decision": stage154_decision,
            "action": "REJECT",
            "reason": "Complete-SAB T_bootstrap/r is 0.977892 versus same-backend tile4.",
        },
        {
            "candidate": "same-format blind MAT layout tuning",
            "latest_decision": "PROFILE_BOUNDED",
            "action": "REQUIRE_NEW_MECHANISM",
            "reason": "MAT EP and FromDFT are still dominant, but prior same-format layout variants do not reliably improve full SAB.",
        },
        {
            "candidate": "representation-changing lazy/DFT or compact-state route",
            "latest_decision": "OPEN_NEXT",
            "action": "SELECT_FOR_STAGE156_FEASIBILITY",
            "reason": "Only a representation change can reduce the 573440 materializations or dense same-format work count.",
        },
    ]

    max_status = "PASS" if all(row["status"] == "PASS" for row in schedule_rows) else "FAIL"
    if max_status != "PASS":
        decision = "FAIL_STAGE155_FRONTIER_SCHEDULE_MISMATCH"
        next_action = "Repair profile/schedule interpretation before any optimization."
    else:
        decision = "PASS_STAGE155_SAME_FORMAT_FRONTIER_ROUTE_TO_REPRESENTATION_GATE"
        next_action = "Stage156 should test DFT/lazy or compact-state feasibility; do not continue blind r=6 layout tuning."

    frontier_rows = [
        {
            "gate": "stage155_schedule_guard",
            "status": max_status,
            "metric": "cmux;from_dft;ncmux;sub_a;copyback",
            "value": f"{expected_cmux};{expected_cmux};{expected_ncmux};{expected_sub_a};0",
            "evidence": rel(SCHEDULE_CSV),
            "detail": "Exact schedule remains unchanged under the current r=6 MAT-RLWE SAB path.",
            "next_action": "Stop if any schedule count differs.",
        },
        {
            "gate": "stage155_component_frontier",
            "status": "PASS",
            "metric": "mat_ep_share;from_dft_share;sub_share;sub_a_share",
            "value": ";".join(
                [
                    fmt(metrics["mat_ep"] / full_us),
                    fmt(metrics["from_dft"] / full_us),
                    fmt(metrics["sub"] / full_us),
                    fmt(metrics["sub_a"] / full_us),
                ]
            ),
            "evidence": rel(COMPONENT_CSV),
            "detail": "The remaining same-format cost is dominated by dense MAT EP and per-update materialization.",
            "next_action": "Only implement a same-format variant if it reduces these dominant counts or has a new measured mechanism.",
        },
        {
            "gate": "stage155_candidate_closeout",
            "status": "PASS",
            "metric": "closed_candidates",
            "value": "dual_sub_pair_route;bodymajor_layout;blind_fulltile_reruns",
            "evidence": rel(CANDIDATE_CSV),
            "detail": "Recent complete-SAB gates close the low-Amdahl local routes.",
            "next_action": "Move to representation-changing feasibility or native-counter attribution.",
        },
        {
            "gate": "stage155_decision",
            "status": decision,
            "metric": "frontier_route",
            "value": "representation_changing_feasibility",
            "evidence": rel(FRONTIER_CSV),
            "detail": "Same-format MAT-RLWE SAB optimization remains useful but bounded; next work must attack materialization count or dense work count.",
            "next_action": next_action,
        },
    ]

    next_rows = [
        {
            "stage": "156",
            "priority": "P0",
            "name": "DFT/lazy-state feasibility gate",
            "goal": "Decide whether a PVW accumulator can remain in DFT/lazy-decomposed state across a SAB monomial update without breaking torus-domain rotations, automorphisms, or phase equality.",
            "correctness_gate": "r=2 toy/probe phase equality for direct CMUX, NCMUX, and one full RGSW monomial step.",
            "performance_gate": "Count reduction must remove materializations or dense addmul work; otherwise reject before full SAB.",
            "failure_handling": "If not closed under SAB operations, record counterexample and route to compact-state or native-counter work.",
        },
        {
            "stage": "157",
            "priority": "P1",
            "name": "compact/shared-source production microbench refresh",
            "goal": "Retest compact/shared-source EP with production N=2048 and decomposition/DFT reuse targets before any SAB integration.",
            "correctness_gate": "component, phase, and noise-model equivalence against dense reference.",
            "performance_gate": "T_kernel/r must beat dense same-format for r=4 and r=6 after decomposition/DFT cost.",
            "failure_handling": "If decomposition/DFT dominates, reject SAB integration and keep as negative ablation.",
        },
        {
            "stage": "158",
            "priority": "P1",
            "name": "native perf/counter refresh",
            "goal": "Use native Linux counters to separate load/store, FMA, cache, and spill limits for the current H14 r=6 path.",
            "correctness_gate": "same full-SAB correctness logs as Stage148/154.",
            "performance_gate": "Counters must explain whether MAT-aware AVX512 is memory-bound or FMA-bound.",
            "failure_handling": "If perf unavailable, mark as blocked and do not claim theoretical AVX optimality.",
        },
    ]

    write_csv(COMPONENT_CSV, component_rows, [
        "component", "avg_us", "share_of_full", "ceiling_if_eliminated",
        "ceiling_if_2x_local", "interpretation",
    ])
    write_csv(SCHEDULE_CSV, schedule_rows, ["metric", "observed_avg", "expected", "status", "detail"])
    write_csv(CANDIDATE_CSV, candidate_rows, ["candidate", "latest_decision", "action", "reason"])
    write_csv(FRONTIER_CSV, frontier_rows, ["gate", "status", "metric", "value", "evidence", "detail", "next_action"])
    write_csv(NEXT_QUEUE_CSV, next_rows, [
        "stage", "priority", "name", "goal", "correctness_gate",
        "performance_gate", "failure_handling",
    ])
    write_csv(SUMMARY_CSV, frontier_rows, ["gate", "status", "metric", "value", "evidence", "detail", "next_action"])

    write_docs(component_rows, schedule_rows, candidate_rows, frontier_rows, next_rows, full_us, lanes, decision)
    update_global_docs(decision)

    artifacts = [
        SUMMARY_CSV, COMPONENT_CSV, SCHEDULE_CSV, CANDIDATE_CSV,
        FRONTIER_CSV, NEXT_QUEUE_CSV, DOC_STAGE, DOC_PLAN, DOC_THEORY,
        DOC_VARIANT,
    ]
    artifact_rows = [
        {"path": rel(path), "sha256": sha256_file(path), "bytes": path.stat().st_size}
        for path in artifacts
    ]
    write_csv(ARTIFACT_CSV, artifact_rows, ["path", "sha256", "bytes"])

    print(f"Stage155 same-format frontier refresh: {decision}")
    print(f"Wrote {rel(SUMMARY_CSV)}")


def component_interpretation(name: str, share: float) -> str:
    if name == "mat_ep":
        return "Largest arithmetic block; same-format dense MAT kernels remain bounded by (r+1)^2 selector work."
    if name == "from_dft":
        return "Large materialization block; backend add fusion removed cmux_add, so further gain needs fewer materializations or faster IFFT."
    if name == "sub":
        return "Material but Stage153 proved local pair-sharing has too little schedule coverage."
    if name == "sub_a":
        return "Small tail; do not prioritize before larger blocks."
    if name == "ncmux_auto":
        return "Small NCMUX automorphism tail; low standalone ceiling."
    if name == "dual_sub_pair":
        return "Explicit pair-sharing work is tiny relative to full SAB."
    return f"Share {share:.3f}; needs finer attribution before targeting."


def write_docs(
    component_rows: List[Dict[str, object]],
    schedule_rows: List[Dict[str, object]],
    candidate_rows: List[Dict[str, object]],
    frontier_rows: List[Dict[str, object]],
    next_rows: List[Dict[str, object]],
    full_us: float,
    lanes: int,
    decision: str,
) -> None:
    component_table = md_table(component_rows, [
        "component", "avg_us", "share_of_full", "ceiling_if_2x_local", "interpretation",
    ])
    schedule_table = md_table(schedule_rows, ["metric", "observed_avg", "expected", "status", "detail"])
    candidate_table = md_table(candidate_rows, ["candidate", "latest_decision", "action", "reason"])
    frontier_table = md_table(frontier_rows, ["gate", "status", "metric", "value", "next_action"])
    next_table = md_table(next_rows, ["stage", "priority", "name", "goal", "performance_gate"])
    per_lane_us = full_us / lanes if lanes else 0.0

    DOC_STAGE.write_text(f"""# Stage155 Same-Format Frontier Refresh

Decision: `{decision}`

Stage155 is a profile-backed route decision after Stage153/154. It does not
change scalar SAB, default PVW flags, or any hot-path code. The metric remains
the MAT-RLWE endpoint `T_complete_bootstrap(r)/r`.

Profile source: `{rel(PROFILE_LOG)}`.

Average instrumented full body time is `{full_us:.3f} us`, or
`{per_lane_us:.3f} us/lane` for r={lanes}. This is attribution-only because
profiling changes timing.

## Schedule Guard

{schedule_table}

## Component Frontier

{component_table}

## Candidate Status

{candidate_table}

## Gate Result

{frontier_table}

## Next Queue

{next_table}

Interpretation: the current same-format r-body PVW/MAT-SAB path has a real
amortized complete-SAB speedup, but the remaining local same-format branches
are now bounded by full-SAB evidence. Further progress should target a
representation-changing gate that can reduce materialization count or dense
work count, not another blind r=6 layout variation.
""", encoding="utf-8", newline="\n")

    DOC_PLAN.write_text(f"""# Stage155 Experiment Plan

Goal: close the post-Stage154 local frontier using existing measured evidence,
then select a concrete Stage156 route.

Inputs:

- `{rel(PROFILE_LOG)}` for r=6 H14 body-profile attribution.
- `{rel(STAGE148_SUMMARY)}` for repeated H14 current-head evidence.
- `{rel(STAGE151_SUMMARY)}` for fulltile smoke status.
- `{rel(STAGE153_SUMMARY)}` for dual-sub full-SAB status.
- `{rel(STAGE154_SUMMARY)}` for bodymajor full-SAB status.

Correctness gate:

- schedule counts must match the expected SAB counts.
- all referenced full-SAB candidate gates must preserve target correctness.

Performance gate:

- promote no same-format local branch unless it has full-SAB `T_bootstrap/r`
  evidence or a new count-reducing mechanism.

Failure handling:

- schedule mismatch blocks optimization.
- negative/neutral local branches are preserved as ablations and not rerun
  without a new profile-backed mechanism.
""", encoding="utf-8", newline="\n")

    DOC_THEORY.write_text(f"""# Stage155 Same-Format Frontier Model

For the current r-body MAT-RLWE SAB path, the sparse schedule still forces:

```text
CMUX/MAT_EP/from_DFT calls = (h+1) * r_prec * N = 40 * 7 * 2048 = 573440
NCMUX calls               = (h+1) * (2^r_prec - 1) = 40 * 127 = 5080
sub_a calls               = h = 39
```

The H14 backend path has already fused the add-back into backend
materialization, so `cmux_add_us=0` in the body profile. The remaining
`from_DFT` cost is therefore not a removable wrapper pass; it is the cost of
materializing every update in the same-format accumulator representation.

Consequences:

- same-format layout variants can only improve constants inside dense MAT EP
  or materialization;
- they do not reduce the schedule count;
- Stage153/154 show that the obvious local constant-factor branches are too
  small or negative at complete-SAB level;
- any larger improvement must change representation or reduce the number of
  materializations/dense terms.

This is not a proof of global optimality. It is a finite frontier bound for the
current code and representation.
""", encoding="utf-8", newline="\n")

    DOC_VARIANT.write_text(f"""# MAT-RLWE SAB Same-Format Frontier

Stage155 classifies the current same-format PVW/MAT-SAB route.

Current valid endpoint:

```text
T_complete_bootstrap(r) / r
```

Allowed claim:

- explicit H14 r=6 backend path has scoped amortized complete-SAB evidence.

Disallowed claims:

- body-major layout is beneficial;
- dual-sub pair sharing provides meaningful full-SAB speedup;
- current MAT AVX512 is theoretically optimal;
- another same-format layout is worth implementing without a new mechanism.

Next algorithmic target:

- a representation-changing feasibility gate for DFT/lazy accumulator state or
  compact/shared-source state, before any SAB hot-path integration.
""", encoding="utf-8", newline="\n")


def md_table(rows: List[Dict[str, object]], fields: List[str]) -> str:
    out = ["| " + " | ".join(fields) + " |", "| " + " | ".join(["---"] * len(fields)) + " |"]
    for row in rows:
        out.append("| " + " | ".join(str(row.get(field, "")).replace("\n", " ") for field in fields) + " |")
    return "\n".join(out)


def update_global_docs(decision: str) -> None:
    append_once(
        ROADMAP,
        "## Stage 155: Same-Format Frontier Refresh",
        f"""## Stage 155: Same-Format Frontier Refresh

Goal:

```text
Use current full-SAB and body-profile evidence to close or route the remaining
same-format MAT-RLWE SAB optimization frontier after Stage154.
```

Status:

```text
Completed. Stage155 records {decision}. The measured profile preserves the
573440 CMUX/MAT_EP/from_DFT schedule count, closes blind r=6 layout tuning,
and routes next to representation-changing feasibility gates.
```
""",
    )
    append_once(
        GOAL_DOC,
        "Stage155 closes the same-format local frontier",
        f"""Stage155 closes the same-format local frontier after Stage154. Decision:
`{decision}`. It uses the Stage153 body profile plus Stage148/151/153/154
full-SAB gates to keep H14 r=6 as the explicit current-head path while routing
future speedup work toward representation-changing materialization/count
reduction rather than blind r=6 layout tuning.
""",
    )
    append_once(
        CURRENT_GOAL,
        "59. Treat Stage155 as the same-format frontier refresh",
        f"""59. Treat Stage155 as the same-format frontier refresh:
    `{decision}`. The current same-format r-body path keeps the scoped H14 r=6
    evidence, rejects blind bodymajor/fulltile/dual-sub continuation, and
    selects a representation-changing feasibility gate as the next valid step.
""",
    )
    append_once(
        HYPOTHESES,
        "H79_same_format_frontier_refresh",
        f"""  - id: H79_same_format_frontier_refresh
    statement: >
      After Stage153/154, further same-format r=6 MAT-RLWE SAB tuning should
      stop unless a new mechanism reduces materialization count or dense
      MAT work count under the complete-SAB T_bootstrap/r endpoint.
    mechanism: >
      The profile preserves 573440 CMUX/MAT_EP/from_DFT calls, while recent
      full-SAB gates reject or neutralize dual-sub, bodymajor, and blind layout
      variants.
    status: stage155_frontier_refresh
    evidence: docs/stage155_same_format_frontier_refresh.md; experiments/stage155_same_format_frontier_refresh_plan.md; theory_checks/stage155_same_format_frontier_model.md; algorithm_variants/mat_rlwe_sab_same_format_frontier.md; repro/stage155_same_format_frontier_refresh/summary.csv
    current_decision: >
      {decision}
    failure_criteria:
      - schedule counts differ from the expected SAB call counts
      - a same-format local branch is promoted without full-SAB T_bootstrap_per_lane evidence
""",
    )
    append_once(
        RUN_LOG,
        "stage155-same-format-frontier-refresh-001",
        f"2026-07-03,stage155-same-format-frontier-refresh-001,analysis,none,SET_2_3_2048,BINARY,{decision},docs/stage155_same_format_frontier_refresh.md;repro/stage155_same_format_frontier_refresh/summary.csv\n",
    )
    append_once(
        MANIFEST,
        "stage155_same_format_frontier_refresh",
        "- `repro/stage155_same_format_frontier_refresh/`: Stage155 profile-backed same-format frontier refresh outputs.\n",
    )
    append_once(
        CHECKLIST,
        "Stage155 same-format frontier refresh",
        "- [x] Stage155 same-format frontier refresh generated from measured Stage153/148/151/153/154 evidence.\n",
    )


def rel(path: Path) -> str:
    return path.resolve().relative_to(ROOT.resolve()).as_posix()


if __name__ == "__main__":
    build()
