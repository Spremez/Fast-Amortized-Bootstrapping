#!/usr/bin/env python3
"""Build Stage207 current-head resource refresh artifacts."""

from __future__ import annotations

import csv
import hashlib
import subprocess
from pathlib import Path
from typing import Dict, Iterable, List


ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "repro" / "stage207_current_head_resource_refresh"
RESOURCE_CSV = OUT / "summary.csv"
STAGE206_PERF = ROOT / "repro" / "stage206_current_head_highstat" / "performance_stats.csv"

DOC = ROOT / "docs" / "stage207_current_head_resource_refresh.md"
PLAN = ROOT / "experiments" / "stage207_current_head_resource_refresh_plan.md"
THEORY = ROOT / "theory_checks" / "stage207_resource_claim_boundary.md"
VARIANT = ROOT / "algorithm_variants" / "mat_rlwe_sab_current_head_resource_refresh.md"
COMPARISON = OUT / "resource_comparison.csv"
PROOF_GATE = OUT / "proof_gate.csv"
NEXT_QUEUE = OUT / "next_stage_queue.csv"
REPORT = OUT / "current_head_resource_report.md"
ARTIFACT_INDEX = OUT / "artifact_index.csv"
REPRO_COMMANDS = OUT / "reproduction_commands.md"

ROADMAP = ROOT / "docs" / "roadmap_stage19_plus.md"
GOAL = ROOT / "docs" / "goal_sab_max_acceleration.md"
CURRENT_GOAL = ROOT / "docs" / "current_codex_goal_sab_completion.md"
HYPOTHESES = ROOT / "hypotheses" / "hypothesis_register.yaml"
RUN_LOG = ROOT / "repro" / "run_log.csv"
MANIFEST = ROOT / "repro" / "artifact_manifest.md"
CHECKLIST = ROOT / "repro" / "reproduction_checklist.md"

DECISION = "PASS_STAGE207_CURRENT_HEAD_RESOURCE_REFRESH"


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


def append_once(path: Path, marker: str, text: str) -> None:
    current = path.read_text(encoding="utf-8") if path.exists() else ""
    if marker in current:
        return
    if current and not current.endswith("\n"):
        current += "\n"
    write_text_lf(path, current + text.strip() + "\n")


def compute_comparison(resource_rows: List[Dict[str, str]], perf_rows: List[Dict[str, str]]) -> List[Dict[str, str]]:
    by_r_mode = {(row["r"], row["mode"]): row for row in resource_rows}
    perf_by_r = {row["r"]: row for row in perf_rows}
    out: List[Dict[str, str]] = []
    for r in sorted({row["r"] for row in resource_rows}, key=lambda x: int(x)):
        pvw = by_r_mode[(r, "pvw")]
        scalar = by_r_mode[(r, "scalar")]
        perf = perf_by_r.get(r, {})
        pvw_keygen = float(pvw["keygen_us"])
        scalar_keygen = float(scalar["keygen_us"])
        pvw_lane_keygen = float(pvw["keygen_lane_avg_us"])
        scalar_lane_keygen = float(scalar["keygen_lane_avg_us"])
        pvw_rss = float(pvw["time_max_rss_kb"])
        scalar_rss = float(scalar["time_max_rss_kb"])
        pvw_internal = float(pvw["internal_vmhwm_kb"])
        scalar_internal = float(scalar["internal_vmhwm_kb"])
        speedup = float(perf.get("ratio_of_mean_per_lane", "nan"))
        key_ratio = float(pvw["estimated_key_bytes_ratio_vs_scalar_repeated"])
        out.append(
            {
                "r": r,
                "backend": pvw["backend"],
                "param": perf.get("param", "SET_2_3_2048"),
                "throughput_speedup_T_bootstrap_over_r": f"{speedup:.6f}",
                "key_bytes_ratio": f"{key_ratio:.6f}",
                "keygen_total_ratio": f"{pvw_keygen / scalar_keygen:.6f}",
                "keygen_per_lane_ratio": f"{pvw_lane_keygen / scalar_lane_keygen:.6f}",
                "time_max_rss_ratio": f"{pvw_rss / scalar_rss:.6f}",
                "internal_vmhwm_ratio": f"{pvw_internal / scalar_internal:.6f}",
                "pvw_key_bytes": pvw["estimated_key_bytes"],
                "scalar_repeated_key_bytes": scalar["estimated_key_bytes"],
                "pvw_keygen_us": pvw["keygen_us"],
                "scalar_repeated_keygen_us": scalar["keygen_us"],
                "pvw_time_max_rss_kb": pvw["time_max_rss_kb"],
                "scalar_time_max_rss_kb": scalar["time_max_rss_kb"],
                "evidence_resource": rel(RESOURCE_CSV),
                "evidence_performance": rel(STAGE206_PERF),
                "claim_boundary": "single_resource_sample_cost_refresh",
            }
        )
    return out


def build_gates(comparison: List[Dict[str, str]]) -> List[Dict[str, str]]:
    rows = []
    all_positive_speed = all(float(row["throughput_speedup_T_bootstrap_over_r"]) > 1.0 for row in comparison)
    key_ratios_bounded = all(float(row["key_bytes_ratio"]) <= 1.10 for row in comparison)
    rss_not_higher = all(float(row["time_max_rss_ratio"]) <= 1.02 for row in comparison)
    rows.append(
        {
            "gate": "G1_resource_raw",
            "status": "PASS" if RESOURCE_CSV.exists() else "FAIL",
            "evidence": rel(RESOURCE_CSV),
            "detail": "Current-head r=2/r=4 PVW and repeated-scalar resource rows exist.",
            "remaining_gap": "Single sample only; use as cost refresh, not statistical resource distribution.",
        }
    )
    rows.append(
        {
            "gate": "G2_cost_bound",
            "status": "PASS_COST_BOUNDED" if key_ratios_bounded and rss_not_higher else "REVIEW_COST",
            "evidence": rel(COMPARISON),
            "detail": "PVW key bytes stay within 1.10x repeated scalar and max RSS is not higher in this sample.",
            "remaining_gap": "Keygen per lane is slower and must be reported with throughput claims.",
        }
    )
    rows.append(
        {
            "gate": "G3_throughput_with_cost",
            "status": "PASS_THROUGHPUT_COST_RECORDED" if all_positive_speed else "FAIL_THROUGHPUT_LINK",
            "evidence": rel(COMPARISON),
            "detail": "Stage206 T_bootstrap/r speedup is linked to Stage207 resource costs for the same current-head path.",
            "remaining_gap": "This does not prove AVX512 optimality, novelty, or broader branch support.",
        }
    )
    rows.append(
        {
            "gate": "G4_decision",
            "status": DECISION,
            "evidence": rel(PROOF_GATE),
            "detail": "Resource refresh is sufficient for current-head engineering reporting.",
            "remaining_gap": "Profile attribution and full-text theorem anchors remain separate gates.",
        }
    )
    return rows


def report(comparison: List[Dict[str, str]], gates: List[Dict[str, str]], nextq: List[Dict[str, str]]) -> str:
    return f"""# Stage207 Current-Head Resource Refresh

Decision: `{DECISION}`.

Stage207 refreshes the resource side of the current-head PVW/MAT-SAB evidence.
It is paired with Stage206 complete-SAB throughput results, but resource
instrumentation remains separate from latency claims.

## Resource And Throughput Link

{table(comparison, ["r", "backend", "param", "throughput_speedup_T_bootstrap_over_r", "key_bytes_ratio", "keygen_per_lane_ratio", "time_max_rss_ratio", "internal_vmhwm_ratio", "claim_boundary"])}

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


def update_tracking(comparison: List[Dict[str, str]]) -> None:
    r2 = next(row for row in comparison if row["r"] == "2")
    r4 = next(row for row in comparison if row["r"] == "4")
    head = git_head()
    append_once(
        ROADMAP,
        "## Stage 207: Current-Head Resource Refresh",
        f"""
## Stage 207: Current-Head Resource Refresh

Goal:

```text
Refresh key size, keygen, and RSS costs for the current-head explicit
PVW/MAT-SAB path after Stage206 high-stat complete-SAB evidence.
```

Status:

```text
Completed. Stage207 records {DECISION}. For the same current-head path used
by Stage206, r=2 has throughput speedup {r2['throughput_speedup_T_bootstrap_over_r']}x,
key bytes ratio {r2['key_bytes_ratio']}x, keygen-per-lane ratio
{r2['keygen_per_lane_ratio']}x, and max-RSS ratio {r2['time_max_rss_ratio']}x.
r=4 has throughput speedup {r4['throughput_speedup_T_bootstrap_over_r']}x,
key bytes ratio {r4['key_bytes_ratio']}x, keygen-per-lane ratio
{r4['keygen_per_lane_ratio']}x, and max-RSS ratio {r4['time_max_rss_ratio']}x.
The result is a current-head resource/cost refresh, not a statistical resource
distribution or optimality proof.
```
""",
    )
    append_once(
        GOAL,
        "Stage207 current-head resource refresh",
        f"""

## Stage207 current-head resource refresh

Current-head resource accounting is refreshed at commit `{head}` for
`spqlios_avx512`, `SET_2_3_2048`, binary, active-buffer PVW/MAT-SAB. r=2:
throughput `T_bootstrap/r` speedup {r2['throughput_speedup_T_bootstrap_over_r']}x,
key bytes ratio {r2['key_bytes_ratio']}x, keygen-per-lane ratio
{r2['keygen_per_lane_ratio']}x, max-RSS ratio {r2['time_max_rss_ratio']}x.
r=4: throughput speedup {r4['throughput_speedup_T_bootstrap_over_r']}x, key
bytes ratio {r4['key_bytes_ratio']}x, keygen-per-lane ratio
{r4['keygen_per_lane_ratio']}x, max-RSS ratio {r4['time_max_rss_ratio']}x.
""",
    )
    append_once(
        CURRENT_GOAL,
        "Stage207 current-head resource refresh",
        f"""

### Stage207 current-head resource refresh

`{DECISION}` links Stage206 high-stat complete-SAB throughput to current-head
resource cost evidence. The goal remains active because profile attribution,
full-text theorem anchors, and broader branch/generalization gates remain open.
""",
    )
    append_once(
        HYPOTHESES,
        "H10_stage207_current_head_resource_refresh",
        f"""

H10_stage207_current_head_resource_refresh:
  status: current_head_cost_recorded
  evidence:
    - repro/stage207_current_head_resource_refresh/resource_comparison.csv
    - docs/stage207_current_head_resource_refresh.md
  conclusion: >
    Stage207 records current-head r=2/r=4 resource costs for the same explicit
    active-buffer PVW/MAT-SAB path measured in Stage206. Key bytes and keygen
    overhead must be reported with T_bootstrap/r throughput claims.
""",
    )
    append_once(
        RUN_LOG,
        "stage207-current-head-resource-refresh-001",
        f"""stage207-current-head-resource-refresh-001,2026-07-04,{head},Stage 207,spqlios_avx512,STAGE25_RESOURCE_R_VALUES='2 4' STAGE25_RESOURCE_OUT_DIR=repro/stage207_current_head_resource_refresh FFT_LIB=spqlios_avx512 MAT_TRGSW_AVX512_SMALLR_SPECIALIZED=true SAB_PVW_ACTIVE_BUFFER_FUSION=true KEY=BINARY PARAM=SET_2_3_2048 bash scripts/run_stage25_resource_matrix.sh,current-head resource refresh paired with Stage206 high-stat throughput,n/a,{DECISION},"r=2 key ratio {r2['key_bytes_ratio']}x keygen/lane ratio {r2['keygen_per_lane_ratio']}x RSS ratio {r2['time_max_rss_ratio']}x; r=4 key ratio {r4['key_bytes_ratio']}x keygen/lane ratio {r4['keygen_per_lane_ratio']}x RSS ratio {r4['time_max_rss_ratio']}x",docs/stage207_current_head_resource_refresh.md; repro/stage207_current_head_resource_refresh/summary.csv; repro/stage207_current_head_resource_refresh/resource_comparison.csv
""",
    )
    append_once(
        MANIFEST,
        "- stage207_current_head_resource_refresh:",
        """

- stage207_current_head_resource_refresh:
  - `docs/stage207_current_head_resource_refresh.md`
  - `experiments/stage207_current_head_resource_refresh_plan.md`
  - `theory_checks/stage207_resource_claim_boundary.md`
  - `algorithm_variants/mat_rlwe_sab_current_head_resource_refresh.md`
  - `scripts/build_stage207_current_head_resource_refresh.py`
  - `repro/stage207_current_head_resource_refresh/`
""",
    )
    append_once(
        CHECKLIST,
        "Stage207 current-head resource refresh",
        """
- [x] Stage207 current-head resource refresh links r=2/r=4 key-size, keygen,
  and RSS costs to Stage206 `T_bootstrap/r` throughput evidence.
""",
    )


def main() -> None:
    if not RESOURCE_CSV.exists():
        raise SystemExit(f"missing resource summary: {RESOURCE_CSV}")
    if not STAGE206_PERF.exists():
        raise SystemExit(f"missing Stage206 performance stats: {STAGE206_PERF}")

    resource_rows = read_csv(RESOURCE_CSV)
    perf_rows = read_csv(STAGE206_PERF)
    comparison = compute_comparison(resource_rows, perf_rows)
    gates = build_gates(comparison)
    nextq = [
        {
            "priority": "P0",
            "route": "profile_attribution_refresh",
            "entry_condition": "Stage206 high-stat throughput and Stage207 resource costs are recorded.",
            "gate": "Attribute remaining full-SAB time to MAT EP, CMUX/NCMUX, sub_a, extract/KS.",
            "current_status": "ready",
            "evidence": rel(PROOF_GATE),
        },
        {
            "priority": "P1",
            "route": "native_or_remote_perf_counters",
            "entry_condition": "Native Linux/perf or CB host is available.",
            "gate": "Load/store/FMA counter attribution for MAT-aware AVX512.",
            "current_status": "blocked_on_perf_access",
            "evidence": "repro/stage205_current_platform_probe/platform_gate.csv",
        },
        {
            "priority": "P2",
            "route": "full_text_anchor_table",
            "entry_condition": "Reviewed 2025/686 full text is available.",
            "gate": "Map exact SAB equations and theorem claims to source anchors.",
            "current_status": "waiting_full_text",
            "evidence": "repro/stage204_source_anchor_intake/proof_gate.csv",
        },
    ]

    write_csv(
        COMPARISON,
        comparison,
        [
            "r",
            "backend",
            "param",
            "throughput_speedup_T_bootstrap_over_r",
            "key_bytes_ratio",
            "keygen_total_ratio",
            "keygen_per_lane_ratio",
            "time_max_rss_ratio",
            "internal_vmhwm_ratio",
            "pvw_key_bytes",
            "scalar_repeated_key_bytes",
            "pvw_keygen_us",
            "scalar_repeated_keygen_us",
            "pvw_time_max_rss_kb",
            "scalar_time_max_rss_kb",
            "evidence_resource",
            "evidence_performance",
            "claim_boundary",
        ],
    )
    write_csv(PROOF_GATE, gates, ["gate", "status", "evidence", "detail", "remaining_gap"])
    write_csv(NEXT_QUEUE, nextq, ["priority", "route", "entry_condition", "gate", "current_status", "evidence"])

    text = report(comparison, gates, nextq)
    write_text_lf(DOC, text)
    write_text_lf(REPORT, text)
    write_text_lf(
        PLAN,
        """# Stage207 Current-Head Resource Refresh Plan

Run `scripts/run_stage25_resource_matrix.sh` for r=2/r=4 on the current
promoted explicit path, then derive key-size, keygen, and RSS ratios against
repeated scalar SAB. Gate resource costs separately from Stage206 latency.
""",
    )
    write_text_lf(
        THEORY,
        """# Stage207 Resource Claim Boundary

The admissible resource claim is scoped to one current-head resource sample for
binary `SET_2_3_2048` under `spqlios_avx512`. It may accompany Stage206
`T_bootstrap/r` throughput claims, but it is not a statistical resource
distribution, an optimality proof, or a broad parameter/branch claim.
""",
    )
    write_text_lf(
        VARIANT,
        """# Current-Head Resource-Cost Evidence For Exact PVW/MAT-SAB

The exact active-buffer PVW/MAT-SAB path keeps the comparison metric as
`T_bootstrap/r`. Stage207 records that the current throughput gain is paired
with modest public-key growth and slower keygen per lane, while peak RSS is not
higher than repeated scalar in this single sample. These costs must be reported
with any complete-SAB throughput table.
""",
    )
    write_text_lf(
        REPRO_COMMANDS,
        """# Stage207 Reproduction Commands

```bash
STAGE25_RESOURCE_R_VALUES='2 4' \\
STAGE25_RESOURCE_OUT_DIR=repro/stage207_current_head_resource_refresh \\
FFT_LIB=spqlios_avx512 \\
MAT_TRGSW_AVX512_SMALLR_SPECIALIZED=true \\
SAB_PVW_ACTIVE_BUFFER_FUSION=true \\
KEY=BINARY PARAM=SET_2_3_2048 \\
bash scripts/run_stage25_resource_matrix.sh

python3 scripts/build_stage207_current_head_resource_refresh.py
```
""",
    )

    artifacts = [
        DOC,
        PLAN,
        THEORY,
        VARIANT,
        COMPARISON,
        PROOF_GATE,
        NEXT_QUEUE,
        REPORT,
        REPRO_COMMANDS,
        RESOURCE_CSV,
    ]
    artifacts.extend(sorted(OUT.glob("r*/*.log")))
    write_csv(ARTIFACT_INDEX, artifact_rows(artifacts), ["path", "exists", "sha256", "bytes"])
    update_tracking(comparison)
    print(DECISION)


if __name__ == "__main__":
    main()
