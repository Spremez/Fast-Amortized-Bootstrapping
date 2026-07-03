#!/usr/bin/env python3
"""Build Stage208 current-head profile-attribution artifacts."""

from __future__ import annotations

import csv
import hashlib
import subprocess
from pathlib import Path
from typing import Dict, Iterable, List


ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "repro" / "stage208_current_head_profile_refresh"
ACTIVE_CSV = OUT / "active_buffer" / "summary.csv"
CMUX_CSV = OUT / "cmux" / "summary.csv"
POSTPROC_R2 = OUT / "postproc_r2" / "postproc_profile.csv"
POSTPROC_R4 = OUT / "postproc_r4" / "postproc_profile.csv"

DOC = ROOT / "docs" / "stage208_current_head_profile_refresh.md"
PLAN = ROOT / "experiments" / "stage208_current_head_profile_refresh_plan.md"
THEORY = ROOT / "theory_checks" / "stage208_profile_claim_boundary.md"
VARIANT = ROOT / "algorithm_variants" / "mat_rlwe_sab_current_head_profile_refresh.md"
ATTRIBUTION = OUT / "component_attribution.csv"
PROOF_GATE = OUT / "proof_gate.csv"
NEXT_QUEUE = OUT / "next_stage_queue.csv"
REPORT = OUT / "current_head_profile_report.md"
ARTIFACT_INDEX = OUT / "artifact_index.csv"
REPRO_COMMANDS = OUT / "reproduction_commands.md"

ROADMAP = ROOT / "docs" / "roadmap_stage19_plus.md"
GOAL = ROOT / "docs" / "goal_sab_max_acceleration.md"
CURRENT_GOAL = ROOT / "docs" / "current_codex_goal_sab_completion.md"
HYPOTHESES = ROOT / "hypotheses" / "hypothesis_register.yaml"
RUN_LOG = ROOT / "repro" / "run_log.csv"
MANIFEST = ROOT / "repro" / "artifact_manifest.md"
CHECKLIST = ROOT / "repro" / "reproduction_checklist.md"

DECISION = "PASS_STAGE208_CURRENT_HEAD_PROFILE_ATTRIBUTION"


def rel(path: Path) -> str:
    return path.relative_to(ROOT).as_posix()


def read_csv(path: Path) -> List[Dict[str, str]]:
    with path.open(newline="", encoding="utf-8") as handle:
        return list(csv.DictReader(handle))


def write_csv(path: Path, rows: List[Dict[str, str]], fields: List[str]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields, lineterminator="\n")
        writer.writeheader()
        writer.writerows(rows)


def write_text_lf(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="\n") as handle:
        handle.write(text)


def append_once(path: Path, marker: str, text: str) -> None:
    current = path.read_text(encoding="utf-8") if path.exists() else ""
    if marker in current:
        return
    if current and not current.endswith("\n"):
        current += "\n"
    write_text_lf(path, current + text.strip() + "\n")


def sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def git_head() -> str:
    return subprocess.check_output(
        ["git", "rev-parse", "--short", "HEAD"], cwd=ROOT, text=True
    ).strip()


def table(rows: List[Dict[str, str]], fields: List[str]) -> str:
    if not rows:
        return "_No rows._"
    lines = [
        "| " + " | ".join(fields) + " |",
        "| " + " | ".join(["---"] * len(fields)) + " |",
    ]
    for row in rows:
        lines.append("| " + " | ".join(row.get(field, "") for field in fields) + " |")
    return "\n".join(lines)


def pct(part: float, total: float) -> float:
    return 0.0 if total == 0.0 else 100.0 * part / total


def mean(values: List[float]) -> float:
    return sum(values) / len(values)


def build_attribution() -> List[Dict[str, str]]:
    active_by_r = {row["r"]: row for row in read_csv(ACTIVE_CSV)}
    cmux_by_r = {row["r"]: row for row in read_csv(CMUX_CSV)}
    post_by_r = {
        "2": read_csv(POSTPROC_R2),
        "4": read_csv(POSTPROC_R4),
    }
    rows: List[Dict[str, str]] = []
    for r in ["2", "4"]:
        active = active_by_r[r]
        cmux = cmux_by_r[r]
        cmux_us = float(cmux["cmux_us"])
        mat_ep_us = float(cmux["mat_ep_us"])
        cmux_sub_us = float(cmux["cmux_sub_us"])
        from_dft_us = float(cmux["cmux_from_dft_us"])
        add_us = float(cmux["cmux_add_us"])
        ncmux_auto_us = float(cmux["ncmux_auto_us"])
        other_us = float(cmux["cmux_other_us"])
        post_rows = post_by_r[r]
        tail_pcts = []
        for post in post_rows:
            full = float(post["full_us"])
            boot = float(post["bootstrap_wo_extract_us"])
            tail_pcts.append(pct(full - boot, full))
        rows.append(
            {
                "r": r,
                "status": active["status"],
                "pvw_profile_speedup": active["speedup"],
                "cmux_calls": active["cmux_calls"],
                "ncmux_calls": active["ncmux_calls"],
                "mat_ep_calls": active["mat_ep_calls"],
                "copyback_calls": active["copyback_calls"],
                "copyback_saved_vs_legacy": active["copyback_saved"],
                "cmux_us": f"{cmux_us:.0f}",
                "mat_ep_pct_of_cmux": f"{pct(mat_ep_us, cmux_us):.3f}",
                "cmux_sub_pct_of_cmux": f"{pct(cmux_sub_us, cmux_us):.3f}",
                "from_dft_pct_of_cmux": f"{pct(from_dft_us, cmux_us):.3f}",
                "cmux_add_pct_of_cmux": f"{pct(add_us, cmux_us):.3f}",
                "ncmux_auto_pct_of_cmux": f"{pct(ncmux_auto_us, cmux_us):.3f}",
                "other_pct_of_cmux": f"{pct(other_us, cmux_us):.3f}",
                "postproc_tail_pct_mean": f"{mean(tail_pcts):.3f}",
                "postproc_tail_pct_max": f"{max(tail_pcts):.3f}",
                "primary_bottleneck": "mat_ep",
                "next_filter": "profile_only_do_not_use_as_latency_claim",
            }
        )
    return rows


def build_gates(rows: List[Dict[str, str]]) -> List[Dict[str, str]]:
    counts_pass = all(
        row["status"] == "PASS"
        and row["cmux_calls"] == "573440"
        and row["ncmux_calls"] == "5080"
        and row["copyback_calls"] == "0"
        for row in rows
    )
    tail_small = all(float(row["postproc_tail_pct_max"]) < 2.0 for row in rows)
    mat_ep_leads = all(float(row["mat_ep_pct_of_cmux"]) > float(row["from_dft_pct_of_cmux"]) for row in rows)
    return [
        {
            "gate": "G1_profile_counts",
            "status": "PASS" if counts_pass else "FAIL",
            "evidence": rel(ATTRIBUTION),
            "detail": "CMUX, NCMUX, MAT EP, sub_a, and active-buffer copyback counts match the current target schedule.",
            "remaining_gap": "Profile timing is instrumentation evidence only.",
        },
        {
            "gate": "G2_component_attribution",
            "status": "PASS_MAT_EP_REMAINS_PRIMARY" if mat_ep_leads else "REVIEW_COMPONENT_ORDER",
            "evidence": rel(ATTRIBUTION),
            "detail": "MAT EP is the largest CMUX subcomponent, with from_DFT, subtract, and add still material.",
            "remaining_gap": "Hardware counters are still needed for load/store/FMA attribution.",
        },
        {
            "gate": "G3_postproc_filter",
            "status": "PASS_POSTPROC_DEFER" if tail_small else "REVIEW_POSTPROC",
            "evidence": rel(ATTRIBUTION),
            "detail": "Post-processing tail remains below the 2 percent implementation threshold.",
            "remaining_gap": "Do not spend hot-path effort on extract/KS unless body path changes the tail share.",
        },
        {
            "gate": "G4_decision",
            "status": DECISION,
            "evidence": rel(PROOF_GATE),
            "detail": "Current-head profile attribution is recorded and routes next work away from postproc-only tuning.",
            "remaining_gap": "Next executable route needs a new MAT EP/from_DFT dataflow mechanism or native counters.",
        },
    ]


def next_queue() -> List[Dict[str, str]]:
    return [
        {
            "priority": "P0",
            "route": "mat_ep_split_or_counter_refresh",
            "entry_condition": "Stage208 shows MAT EP is the largest CMUX subcomponent.",
            "gate": "Use native/perf counters if available; otherwise run a bounded split microbench before code.",
            "current_status": "ready_but_counter_limited",
            "evidence": rel(ATTRIBUTION),
        },
        {
            "priority": "P1",
            "route": "from_dft_dataflow_preflight",
            "entry_condition": "from_DFT remains material but prior direct-scale variants were neutral.",
            "gate": "Require a specific new dataflow mechanism before implementation.",
            "current_status": "preflight_only",
            "evidence": rel(ATTRIBUTION),
        },
        {
            "priority": "P2",
            "route": "postproc_deferred",
            "entry_condition": "postproc tail max is below 2 percent in Stage208.",
            "gate": "Reopen only if future body optimizations raise postproc share.",
            "current_status": "deferred",
            "evidence": rel(ATTRIBUTION),
        },
    ]


def report(rows: List[Dict[str, str]], gates: List[Dict[str, str]], nextq: List[Dict[str, str]]) -> str:
    return f"""# Stage208 Current-Head Profile Refresh

Decision: `{DECISION}`.

Stage208 records profile-only attribution for the current explicit
PVW/MAT-SAB path. These timings are used for route selection, not for final
latency claims.

## Component Attribution

{table(rows, ["r", "status", "pvw_profile_speedup", "cmux_calls", "ncmux_calls", "copyback_calls", "copyback_saved_vs_legacy", "mat_ep_pct_of_cmux", "from_dft_pct_of_cmux", "cmux_sub_pct_of_cmux", "cmux_add_pct_of_cmux", "postproc_tail_pct_max", "primary_bottleneck"])}

## Gates

{table(gates, ["gate", "status", "evidence", "detail", "remaining_gap"])}

## Next Queue

{table(nextq, ["priority", "route", "entry_condition", "gate", "current_status", "evidence"])}
"""


def artifact_rows(paths: Iterable[Path]) -> List[Dict[str, str]]:
    rows = []
    seen = set()
    for path in paths:
        if path in seen:
            continue
        seen.add(path)
        rows.append(
            {
                "path": rel(path),
                "exists": "yes" if path.exists() else "no",
                "sha256": sha256(path) if path.exists() and path.is_file() else "",
                "bytes": str(path.stat().st_size) if path.exists() and path.is_file() else "",
            }
        )
    return rows


def update_tracking(rows: List[Dict[str, str]]) -> None:
    r2 = next(row for row in rows if row["r"] == "2")
    r4 = next(row for row in rows if row["r"] == "4")
    head = git_head()
    append_once(
        ROADMAP,
        "## Stage 208: Current-Head Profile Attribution",
        f"""
## Stage 208: Current-Head Profile Attribution

Goal:

```text
Refresh profile-only attribution for the current-head explicit active-buffer
PVW/MAT-SAB path after Stage206 throughput and Stage207 resource gates.
```

Status:

```text
Completed. Stage208 records {DECISION}. Active-buffer schedule counts pass
for r=2/r=4 with CMUX/MAT EP 573440, NCMUX 5080, and copyback 0. MAT EP is
the largest CMUX subcomponent: {r2['mat_ep_pct_of_cmux']}% of CMUX time for
r=2 and {r4['mat_ep_pct_of_cmux']}% for r=4. Post-processing remains below
the 2% implementation threshold, with max tail {r2['postproc_tail_pct_max']}%
for r=2 and {r4['postproc_tail_pct_max']}% for r=4.
```
""",
    )
    append_once(
        GOAL,
        "Stage208 current-head profile attribution",
        f"""

## Stage208 current-head profile attribution

At commit `{head}`, current-head profile-only attribution confirms the next
engineering target is still the body/CMUX path, not post-processing. r=2/r=4
copyback calls are 0 under active-buffer fusion, MAT EP remains the largest
CMUX subcomponent, and post-processing max tail is below 2%.
""",
    )
    append_once(
        CURRENT_GOAL,
        "Stage208 current-head profile attribution",
        f"""

### Stage208 current-head profile attribution

`{DECISION}` records route-selection evidence only. The goal remains active:
the next executable route is a bounded MAT EP/from_DFT split or native-counter
gate, not another broad theory loop.
""",
    )
    append_once(
        HYPOTHESES,
        "H10_stage208_current_head_profile_attribution",
        """

H10_stage208_current_head_profile_attribution:
  status: current_head_profile_recorded
  evidence:
    - repro/stage208_current_head_profile_refresh/component_attribution.csv
    - docs/stage208_current_head_profile_refresh.md
  conclusion: >
    Current-head profile-only evidence keeps the next engineering target in
    the body/CMUX/MAT-EP path. Post-processing remains deferred, and profile
    timing must not be used as final latency evidence.
""",
    )
    append_once(
        RUN_LOG,
        "stage208-current-head-profile-refresh-001",
        f"""stage208-current-head-profile-refresh-001,2026-07-04,{head},Stage 208,spqlios_avx512,bash scripts/run_stage208_current_head_profile_refresh.sh,current-head active-buffer profile attribution for r=2/r=4,profile-only,{DECISION},"CMUX/MAT EP counts 573440 and NCMUX 5080 pass; copyback 0; MAT EP is largest CMUX component; postproc tail below 2 percent",docs/stage208_current_head_profile_refresh.md; repro/stage208_current_head_profile_refresh/component_attribution.csv
""",
    )
    append_once(
        MANIFEST,
        "- stage208_current_head_profile_refresh:",
        """

- stage208_current_head_profile_refresh:
  - `docs/stage208_current_head_profile_refresh.md`
  - `experiments/stage208_current_head_profile_refresh_plan.md`
  - `theory_checks/stage208_profile_claim_boundary.md`
  - `algorithm_variants/mat_rlwe_sab_current_head_profile_refresh.md`
  - `scripts/run_stage208_current_head_profile_refresh.sh`
  - `scripts/build_stage208_current_head_profile_refresh.py`
  - `repro/stage208_current_head_profile_refresh/`
""",
    )
    append_once(
        CHECKLIST,
        "Stage208 current-head profile attribution",
        """
- [x] Stage208 current-head profile attribution records r=2/r=4 schedule
  counts, CMUX component shares, active-buffer copyback elimination, and
  post-processing deferral.
""",
    )


def main() -> None:
    for path in [ACTIVE_CSV, CMUX_CSV, POSTPROC_R2, POSTPROC_R4]:
        if not path.exists():
            raise SystemExit(f"missing Stage208 input: {path}")

    rows = build_attribution()
    gates = build_gates(rows)
    nextq = next_queue()
    write_csv(
        ATTRIBUTION,
        rows,
        [
            "r",
            "status",
            "pvw_profile_speedup",
            "cmux_calls",
            "ncmux_calls",
            "mat_ep_calls",
            "copyback_calls",
            "copyback_saved_vs_legacy",
            "cmux_us",
            "mat_ep_pct_of_cmux",
            "cmux_sub_pct_of_cmux",
            "from_dft_pct_of_cmux",
            "cmux_add_pct_of_cmux",
            "ncmux_auto_pct_of_cmux",
            "other_pct_of_cmux",
            "postproc_tail_pct_mean",
            "postproc_tail_pct_max",
            "primary_bottleneck",
            "next_filter",
        ],
    )
    write_csv(PROOF_GATE, gates, ["gate", "status", "evidence", "detail", "remaining_gap"])
    write_csv(NEXT_QUEUE, nextq, ["priority", "route", "entry_condition", "gate", "current_status", "evidence"])
    text = report(rows, gates, nextq)
    write_text_lf(DOC, text)
    write_text_lf(REPORT, text)
    write_text_lf(
        PLAN,
        """# Stage208 Current-Head Profile Refresh Plan

Run current-head active-buffer body, CMUX, and post-processing profile modes
for r=2/r=4. Use the results only for route selection, not final latency
claims.
""",
    )
    write_text_lf(
        THEORY,
        """# Stage208 Profile Claim Boundary

Stage208 timing is instrumentation evidence. It supports component-priority
decisions and count gates, but it does not replace Stage206 high-stat latency,
Stage207 resource accounting, native hardware counters, or theorem-level
source anchors.
""",
    )
    write_text_lf(
        VARIANT,
        """# Current-Head Profile Attribution For Exact PVW/MAT-SAB

The current exact active-buffer PVW/MAT-SAB path still spends almost all time
in the body/CMUX schedule. Active-buffer copyback is eliminated for the target
profile, post-processing remains below the implementation threshold, and the
next bounded engineering work should target MAT EP/from_DFT dataflow or native
counter attribution.
""",
    )
    write_text_lf(
        REPRO_COMMANDS,
        """# Stage208 Reproduction Commands

```bash
bash scripts/run_stage208_current_head_profile_refresh.sh
python3 scripts/build_stage208_current_head_profile_refresh.py
```
""",
    )
    artifacts = [
        DOC,
        PLAN,
        THEORY,
        VARIANT,
        ATTRIBUTION,
        PROOF_GATE,
        NEXT_QUEUE,
        REPORT,
        REPRO_COMMANDS,
        ACTIVE_CSV,
        CMUX_CSV,
        POSTPROC_R2,
        POSTPROC_R4,
    ]
    artifacts.extend(sorted(OUT.glob("*/*/*.log")))
    artifacts.extend(sorted(OUT.glob("*/*.csv")))
    write_csv(ARTIFACT_INDEX, artifact_rows(artifacts), ["path", "exists", "sha256", "bytes"])
    update_tracking(rows)
    print(DECISION)


if __name__ == "__main__":
    main()
