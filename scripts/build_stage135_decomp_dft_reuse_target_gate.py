#!/usr/bin/env python3
"""Build Stage135 decompose/DFT reuse target gate from Stage134 timings."""

from __future__ import annotations

import csv
import hashlib
import subprocess
from pathlib import Path
from typing import Dict, Iterable, List


ROOT = Path(__file__).resolve().parents[1]
STAGE134_RATIO = ROOT / "repro" / "stage134_generalized_lane_pair_input_ep_gate" / "ratio_summary.csv"
STAGE134_SUMMARY = ROOT / "repro" / "stage134_generalized_lane_pair_input_ep_gate" / "summary.csv"
OUT_DIR = ROOT / "repro" / "stage135_decomp_dft_reuse_target_gate"
SUMMARY_CSV = OUT_DIR / "summary.csv"
TARGET_CSV = OUT_DIR / "target_matrix.csv"
ROUTE_CSV = OUT_DIR / "route_matrix.csv"
ARTIFACT_INDEX = OUT_DIR / "artifact_index.csv"
OUT_MD = ROOT / "docs" / "stage135_decomp_dft_reuse_target_gate.md"
PLAN_MD = ROOT / "experiments" / "stage135_decomp_dft_reuse_target_gate_plan.md"
THEORY_MD = ROOT / "theory_checks" / "stage135_decomp_dft_reuse_target_model.md"
VARIANT_MD = ROOT / "algorithm_variants" / "mat_rlwe_sab_decomp_dft_reuse_target.md"
RUN_LOG = ROOT / "repro" / "run_log.csv"
GLOBAL_MANIFEST = ROOT / "repro" / "artifact_manifest.md"
HYPOTHESIS_YAML = ROOT / "hypotheses" / "hypothesis_register.yaml"
ROADMAP_MD = ROOT / "docs" / "roadmap_stage19_plus.md"
GOAL_MD = ROOT / "docs" / "goal_sab_max_acceleration.md"
CURRENT_GOAL_MD = ROOT / "docs" / "current_codex_goal_sab_completion.md"


SUMMARY_FIELDS = ["gate", "status", "metric", "value", "evidence", "detail", "next_action"]
TARGET_FIELDS = [
    "backend",
    "r",
    "N",
    "dense_all_us",
    "generalized_all_us",
    "generalized_decomp_dft_us",
    "generalized_addmul_us",
    "observed_full_speedup",
    "observed_decomp_speedup",
    "observed_addmul_speedup",
    "break_even_decomp_target_us",
    "break_even_decomp_reduction_us",
    "required_decomp_speedup_break_even",
    "fivepct_decomp_target_us",
    "fivepct_decomp_reduction_us",
    "required_decomp_speedup_5pct",
    "predicted_speedup_if_decomp_matches_dense",
    "decision",
]
ROUTE_FIELDS = ["route", "status", "stage", "target", "risk", "gate"]


def rel(path: Path) -> str:
    return path.relative_to(ROOT).as_posix()


def write_text_lf(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(text.encode("utf-8"))


def read_csv(path: Path) -> List[Dict[str, str]]:
    if not path.exists():
        return []
    with path.open(newline="", encoding="utf-8-sig") as f:
        return list(csv.DictReader(f))


def write_csv(path: Path, rows: Iterable[Dict[str, str]], fields: List[str]) -> None:
    normalized = [{field: row.get(field, "") for field in fields} for row in rows]
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fields, lineterminator="\n")
        writer.writeheader()
        writer.writerows(normalized)


def sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def git_head() -> str:
    try:
        return subprocess.check_output(
            ["git", "rev-parse", "--short", "HEAD"], cwd=ROOT, text=True
        ).strip()
    except Exception:
        return "unknown"


def append_once(path: Path, heading: str, block: str) -> None:
    text = path.read_text(encoding="utf-8") if path.exists() else ""
    if heading in text:
        return
    if text and not text.endswith("\n"):
        text += "\n"
    write_text_lf(path, text + "\n" + block.strip() + "\n")


def compute_targets(ratio_rows: List[Dict[str, str]]) -> List[Dict[str, str]]:
    rows: List[Dict[str, str]] = []
    for row in ratio_rows:
        dense_all = float(row["dense_all_mean_us"])
        gen_all = float(row["compact_all_mean_us"])
        gen_decomp = float(row["compact_decomp_dft_mean_us"])
        gen_addmul = float(row["compact_addmul_mean_us"])
        dense_decomp = float(row["dense_decomp_dft_mean_us"])
        observed_full = float(row["full_speedup"])
        gap = max(0.0, gen_all - dense_all)
        fivepct_target_total = dense_all / 1.05
        fivepct_gap = max(0.0, gen_all - fivepct_target_total)
        break_even_target = max(0.0, gen_decomp - gap)
        fivepct_target = max(0.0, gen_decomp - fivepct_gap)
        required_break_even = gen_decomp / break_even_target if break_even_target > 0 else 999.0
        required_fivepct = gen_decomp / fivepct_target if fivepct_target > 0 else 999.0
        predicted_if_dense_decomp = dense_all / max(0.000001, gen_all - gen_decomp + dense_decomp)
        if row["r"] == "4" and required_break_even <= 1.20:
            decision = "R4_BREAK_EVEN_TARGET_PLAUSIBLE"
        elif observed_full >= 1.0:
            decision = "ALREADY_POSITIVE_DECOMP_STILL_DOMINANT"
        else:
            decision = "TARGET_HIGH_RISK"
        rows.append(
            {
                "backend": row["backend"],
                "r": row["r"],
                "N": row["N"],
                "dense_all_us": f"{dense_all:.6f}",
                "generalized_all_us": f"{gen_all:.6f}",
                "generalized_decomp_dft_us": f"{gen_decomp:.6f}",
                "generalized_addmul_us": f"{gen_addmul:.6f}",
                "observed_full_speedup": f"{observed_full:.6f}",
                "observed_decomp_speedup": row["decomp_dft_speedup"],
                "observed_addmul_speedup": row["addmul_speedup"],
                "break_even_decomp_target_us": f"{break_even_target:.6f}",
                "break_even_decomp_reduction_us": f"{gap:.6f}",
                "required_decomp_speedup_break_even": f"{required_break_even:.6f}",
                "fivepct_decomp_target_us": f"{fivepct_target:.6f}",
                "fivepct_decomp_reduction_us": f"{fivepct_gap:.6f}",
                "required_decomp_speedup_5pct": f"{required_fivepct:.6f}",
                "predicted_speedup_if_decomp_matches_dense": f"{predicted_if_dense_decomp:.6f}",
                "decision": decision,
            }
        )
    return rows


def build_routes(target_rows: List[Dict[str, str]]) -> List[Dict[str, str]]:
    r4_rows = [row for row in target_rows if row["r"] == "4"]
    max_r4_break_even = max((float(row["required_decomp_speedup_break_even"]) for row in r4_rows), default=0.0)
    max_r4_5pct = max((float(row["required_decomp_speedup_5pct"]) for row in r4_rows), default=0.0)
    return [
        {
            "route": "lane_pair_decomp_dft_reuse_or_batching",
            "status": "PRIMARY_NEXT",
            "stage": "Stage136",
            "target": f"r=4 break-even decomp speedup >= {max_r4_break_even:.3f}; 5pct target >= {max_r4_5pct:.3f}",
            "risk": "DFT conversion may dominate and resist reuse if every CMUX input is unique.",
            "gate": "microbench must improve Stage134 compact_decomp_dft for both r=4 N=512/1024.",
        },
        {
            "route": "r4_specialized_decompose_to_dft_kernel",
            "status": "SECONDARY_NEXT",
            "stage": "Stage136_variant",
            "target": "remove per-lane/per-t digit overhead without changing selector semantics",
            "risk": "constant-factor gain may be below required 1.16x break-even.",
            "gate": "same correctness plus decomp-only microbench, no full-SAB claim.",
        },
        {
            "route": "proceed_to_rgsw_lane_state",
            "status": "REJECTED_UNTIL_DECOMP_GATE",
            "stage": "none",
            "target": "requires positive r=4/r=6 Stage134-style full EP timing first",
            "risk": "RGSW integration would multiply a negative r=4 kernel signal.",
            "gate": "must pass Stage136 before reopening.",
        },
        {
            "route": "shared_source_first_step_only",
            "status": "REFERENCE_ONLY",
            "stage": "none",
            "target": "keep Stage130 as upper-bound first-step evidence",
            "risk": "not iterative after Stage132 lane-pair state.",
            "gate": "cannot be used for full SAB closure claims.",
        },
    ]


def build_summary(stage134_status: str, target_rows: List[Dict[str, str]]) -> List[Dict[str, str]]:
    rows_ok = len(target_rows) == 6
    r4_rows = [row for row in target_rows if row["r"] == "4"]
    max_r4_break_even = max((float(row["required_decomp_speedup_break_even"]) for row in r4_rows), default=0.0)
    max_r4_5pct = max((float(row["required_decomp_speedup_5pct"]) for row in r4_rows), default=0.0)
    plausible = rows_ok and 1.0 < max_r4_break_even <= 1.20
    decision = (
        "PASS_STAGE135_DECOMP_DFT_REUSE_TARGETS_READY_STAGE136"
        if plausible
        else "NEUTRAL_STAGE135_DECOMP_DFT_TARGETS_HIGH_RISK"
    )
    return [
        {
            "gate": "stage135_stage134_input",
            "status": "PASS" if stage134_status else "FAIL",
            "metric": "stage134_decision",
            "value": stage134_status,
            "evidence": rel(STAGE134_SUMMARY),
            "detail": "Stage135 derives targets only from Stage134 measured timings.",
            "next_action": "",
        },
        {
            "gate": "stage135_target_rows",
            "status": "PASS" if rows_ok else "FAIL",
            "metric": "target_rows",
            "value": str(len(target_rows)),
            "evidence": rel(TARGET_CSV),
            "detail": "Break-even and 5pct decompose/DFT targets generated for all Stage134 rows.",
            "next_action": "",
        },
        {
            "gate": "stage135_r4_break_even_target",
            "status": "PLAUSIBLE" if plausible else "HIGH_RISK",
            "metric": "max_required_decomp_speedup_break_even_r4",
            "value": f"{max_r4_break_even:.6f}",
            "evidence": rel(TARGET_CSV),
            "detail": "Required r=4 decompose/DFT improvement to reach full-kernel break-even.",
            "next_action": "Implement only decompose/DFT-targeted variants before RGSW.",
        },
        {
            "gate": "stage135_r4_5pct_target",
            "status": "RECORDED",
            "metric": "max_required_decomp_speedup_5pct_r4",
            "value": f"{max_r4_5pct:.6f}",
            "evidence": rel(TARGET_CSV),
            "detail": "Required r=4 decompose/DFT improvement for a 5pct full-kernel speedup.",
            "next_action": "",
        },
        {
            "gate": "stage135_decision",
            "status": decision,
            "metric": "promotion_policy",
            "value": "",
            "evidence": f"{rel(SUMMARY_CSV)}; {rel(TARGET_CSV)}; {rel(ROUTE_CSV)}",
            "detail": "Stage135 sets the quantitative target for the next implementation gate.",
            "next_action": "Stage136 should implement and benchmark lane-pair decompose/DFT reuse or batching.",
        },
    ]


def table(rows: List[Dict[str, str]], fields: List[str]) -> List[str]:
    lines = ["| " + " | ".join(fields) + " |", "|" + "|".join(["---"] * len(fields)) + "|"]
    for row in rows:
        lines.append("| " + " | ".join(row.get(field, "") for field in fields) + " |")
    return lines


def write_docs(
    summary: List[Dict[str, str]],
    target_rows: List[Dict[str, str]],
    route_rows: List[Dict[str, str]],
) -> None:
    decision = summary[-1]["status"]
    r4_rows = [row for row in target_rows if row["r"] == "4"]
    max_r4_break_even = max((float(row["required_decomp_speedup_break_even"]) for row in r4_rows), default=0.0)
    max_r4_5pct = max((float(row["required_decomp_speedup_5pct"]) for row in r4_rows), default=0.0)
    write_text_lf(
        PLAN_MD,
        "\n".join(
            [
                "# Stage135 Decompose/DFT Reuse Target Gate Plan",
                "",
                "Date: 2026-07-03",
                "",
                "## Objective",
                "",
                "Use Stage134 measured timings to calculate the exact decompose/DFT",
                "improvement required before generalized lane-pair input EP is worth",
                "integrating into RGSW/sparse SAB.",
                "",
                "## Command",
                "",
                "```bash",
                "python scripts/build_stage135_decomp_dft_reuse_target_gate.py",
                "```",
                "",
                "## Falsification Criteria",
                "",
                "- Stage134 ratio rows are missing;",
                "- required r=4 decompose/DFT improvement is too large to be a focused",
                "  implementation target;",
                "- RGSW integration proceeds without a decompose/DFT gate.",
            ]
        )
        + "\n",
    )
    write_text_lf(
        THEORY_MD,
        "\n".join(
            [
                "# Stage135 Decompose/DFT Reuse Target Model",
                "",
                "Date: 2026-07-03",
                "",
                "Let `D` be Stage134 generalized compact decompose/DFT time, `A` the",
                "generalized addmul time, `C = D + A + overhead` the measured full",
                "compact time, and `B` the dense proxy full time. Break-even requires",
                "`C - reduction <= B`, so the required decompose/DFT reduction is",
                "`max(0, C - B)`. A 5pct target requires `C - reduction <= B/1.05`.",
                "",
                f"For r=4, the maximum required break-even decompose/DFT speedup is {max_r4_break_even:.6f}.",
                f"The maximum required 5pct speedup is {max_r4_5pct:.6f}.",
                "",
                "## Target Matrix",
                "",
                *table(target_rows, TARGET_FIELDS),
                "",
                "## Route Matrix",
                "",
                *table(route_rows, ROUTE_FIELDS),
            ]
        )
        + "\n",
    )
    write_text_lf(
        VARIANT_MD,
        "\n".join(
            [
                "# V135: Decompose/DFT Reuse Target",
                "",
                "## Summary",
                "",
                "- Parent algorithm: PVW/MAT-SAB r-body research track.",
                "- Focused module: generalized lane-pair input decompose/DFT.",
                "- Optimization target: make closure-capable EP positive for r=4.",
                "- Status labels: `[target-gate]`, `[not-rgsw]`, `[performance-blocker]`.",
                f"- Decision: `{decision}`.",
                "",
                "## Required Experiments",
                "",
                "Stage136 must implement a decompose/DFT-targeted variant and compare it",
                "against Stage134 for r=4 N=512/1024. RGSW integration remains rejected",
                "until this kernel-level blocker is removed.",
            ]
        )
        + "\n",
    )
    md = [
        "# Stage135 Decompose/DFT Reuse Target Gate",
        "",
        "Date: 2026-07-03",
        "",
        "## Decision",
        "",
        f"`{decision}`",
        "",
        "Stage135 converts Stage134's neutral performance result into a concrete",
        "implementation target for the next gate.",
        "",
        "## Gates",
        "",
        "| gate | status | metric | value | detail |",
        "|---|---|---|---|---|",
    ]
    for row in summary:
        md.append(
            f"| {row['gate']} | {row['status']} | {row['metric']} | "
            f"{row['value']} | {row['detail']} |"
        )
    md += ["", "## Target Matrix", "", *table(target_rows, TARGET_FIELDS)]
    md += ["", "## Route Matrix", "", *table(route_rows, ROUTE_FIELDS)]
    md += [
        "",
        "## Interpretation",
        "",
        "The r=4 blocker is not the addmul part; addmul is already positive. The",
        "next finite implementation target is decompose/DFT reuse or batching that",
        "beats Stage134's compact_decomp_dft timing by the recorded target factors.",
    ]
    write_text_lf(OUT_MD, "\n".join(md) + "\n")


def update_longform_docs(status: str, target_rows: List[Dict[str, str]]) -> None:
    r4_rows = [row for row in target_rows if row["r"] == "4"]
    max_r4_break_even = max((float(row["required_decomp_speedup_break_even"]) for row in r4_rows), default=0.0)
    max_r4_5pct = max((float(row["required_decomp_speedup_5pct"]) for row in r4_rows), default=0.0)
    stage_block = f"""
## Stage 135: Decompose/DFT Reuse Target Gate

Goal:

```text
Turn Stage134's neutral closure-capable EP result into concrete decompose/DFT
optimization targets before any RGSW/sparse integration.
```

Status:

```text
Completed. Stage135 records {status}. For r=4, the required decompose/DFT
speedup is {max_r4_break_even:.6f} for break-even and {max_r4_5pct:.6f} for a
5pct full-kernel gain. The next valid stage is a decompose/DFT reuse or
batching implementation gate.
```
"""
    append_once(ROADMAP_MD, "## Stage 135: Decompose/DFT Reuse Target Gate", stage_block)
    goal_block = f"""
Stage135 sets the quantitative implementation target created by Stage134:
generalized lane-pair input is arithmetically closed, but r=4 needs up to
{max_r4_break_even:.6f} decompose/DFT speedup just to break even and
{max_r4_5pct:.6f} for a 5pct full-kernel gain. This keeps the loop empirical:
the next code work must beat these targets before RGSW integration.
"""
    append_once(GOAL_MD, "Stage135 sets the quantitative implementation target", goal_block)
    current_goal_block = f"""
39. Treat Stage135 as the current decompose/DFT reuse target gate:
    `{status}`. The r=4 generalized lane-pair input path needs up to
    {max_r4_break_even:.6f} decompose/DFT speedup to break even and
    {max_r4_5pct:.6f} for a 5pct full-kernel gain. RGSW/sparse integration
    remains rejected until Stage136 improves this measured blocker.
"""
    append_once(CURRENT_GOAL_MD, "39. Treat Stage135 as the current decompose", current_goal_block)


def upsert_hypothesis(status: str, target_rows: List[Dict[str, str]]) -> None:
    r4_rows = [row for row in target_rows if row["r"] == "4"]
    max_r4_break_even = max((float(row["required_decomp_speedup_break_even"]) for row in r4_rows), default=0.0)
    block = f"""  - id: H59_decomp_dft_reuse_target
    statement: >
      Generalized lane-pair input compact EP should not be integrated into
      RGSW/sparse SAB until its decompose/DFT cost is reduced enough to make
      r=4 full-kernel timing positive.
    mechanism: >
      Stage135 derives break-even and 5pct-gain targets from Stage134 measured
      dense, generalized full, decompose/DFT, and addmul timings. It shows the
      addmul path is already positive while decompose/DFT remains the blocker.
    status: stage135_decomp_dft_reuse_targets_ready_stage136
    evidence: docs/stage135_decomp_dft_reuse_target_gate.md; experiments/stage135_decomp_dft_reuse_target_gate_plan.md; theory_checks/stage135_decomp_dft_reuse_target_model.md; algorithm_variants/mat_rlwe_sab_decomp_dft_reuse_target.md; scripts/build_stage135_decomp_dft_reuse_target_gate.py; repro/stage135_decomp_dft_reuse_target_gate/summary.csv; repro/stage135_decomp_dft_reuse_target_gate/target_matrix.csv; repro/stage135_decomp_dft_reuse_target_gate/route_matrix.csv; repro/stage135_decomp_dft_reuse_target_gate/artifact_index.csv
    current_decision: >
      Stage135 records {status}. The maximum required r=4 decompose/DFT
      speedup for break-even is {max_r4_break_even:.6f}. Stage136 must target
      decompose/DFT reuse or batching before any RGSW/sparse integration.
    failure_criteria:
      - RGSW/sparse integration starts before decompose/DFT timing improves
      - addmul-only gains are used to claim full EP or full SAB speedup
      - targets are evaluated without same-backend Stage134 comparison
      - complete `T_bootstrap/r` acceleration is claimed before full SAB gates
"""
    text = HYPOTHESIS_YAML.read_text(encoding="utf-8")
    marker = "  - id: H59_decomp_dft_reuse_target"
    if marker in text:
        text = text[: text.index(marker)].rstrip() + "\n"
    if text and not text.endswith("\n"):
        text += "\n"
    write_text_lf(HYPOTHESIS_YAML, text + block)


def write_artifact_index(paths: List[Path]) -> None:
    rows = []
    for path in paths:
        if path == ARTIFACT_INDEX:
            rows.append({"artifact": rel(path), "exists": "self", "sha256": "", "size_bytes": ""})
            continue
        rows.append(
            {
                "artifact": rel(path),
                "exists": "yes" if path.exists() else "no",
                "sha256": sha256_file(path) if path.exists() else "",
                "size_bytes": str(path.stat().st_size) if path.exists() else "0",
            }
        )
    write_csv(ARTIFACT_INDEX, rows, ["artifact", "exists", "sha256", "size_bytes"])


def upsert_run_log(status: str) -> None:
    fields = [
        "run_id",
        "date",
        "commit_or_state",
        "stage",
        "backend",
        "command",
        "params",
        "seed",
        "status",
        "summary",
        "artifacts",
    ]
    run_id = "stage135-decomp-dft-reuse-target-001"
    rows = [row for row in read_csv(RUN_LOG) if row.get("run_id") != run_id]
    artifacts = [OUT_MD, PLAN_MD, THEORY_MD, VARIANT_MD, SUMMARY_CSV, TARGET_CSV, ROUTE_CSV, ARTIFACT_INDEX, Path(__file__).resolve()]
    rows.append(
        {
            "run_id": run_id,
            "date": "2026-07-03",
            "commit_or_state": f"working-tree-after-{git_head()}",
            "stage": "Stage 135",
            "backend": "derived from Stage134 spqlios timings",
            "command": "python scripts/build_stage135_decomp_dft_reuse_target_gate.py",
            "params": "Stage134 r=2,4,6 N=512,1024",
            "seed": "0 subset inherited",
            "status": status,
            "summary": "Stage135 derives decompose/DFT improvement targets before RGSW integration.",
            "artifacts": "; ".join(rel(p) for p in artifacts),
        }
    )
    write_csv(RUN_LOG, rows, fields)


def upsert_global_manifest() -> None:
    block = """
## Stage 135 Decompose/DFT Reuse Target Gate

- `docs/stage135_decomp_dft_reuse_target_gate.md`
- `experiments/stage135_decomp_dft_reuse_target_gate_plan.md`
- `theory_checks/stage135_decomp_dft_reuse_target_model.md`
- `algorithm_variants/mat_rlwe_sab_decomp_dft_reuse_target.md`
- `scripts/build_stage135_decomp_dft_reuse_target_gate.py`
- `repro/stage135_decomp_dft_reuse_target_gate/summary.csv`
- `repro/stage135_decomp_dft_reuse_target_gate/target_matrix.csv`
- `repro/stage135_decomp_dft_reuse_target_gate/route_matrix.csv`
- `repro/stage135_decomp_dft_reuse_target_gate/artifact_index.csv`
"""
    append_once(GLOBAL_MANIFEST, "## Stage 135 Decompose/DFT Reuse Target Gate", block)


def main() -> int:
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    stage134_summary = read_csv(STAGE134_SUMMARY)
    stage134_status = stage134_summary[-1]["status"] if stage134_summary else ""
    ratio_rows = read_csv(STAGE134_RATIO)
    target_rows = compute_targets(ratio_rows)
    route_rows = build_routes(target_rows)
    summary = build_summary(stage134_status, target_rows)
    write_csv(TARGET_CSV, target_rows, TARGET_FIELDS)
    write_csv(ROUTE_CSV, route_rows, ROUTE_FIELDS)
    write_csv(SUMMARY_CSV, summary, SUMMARY_FIELDS)
    status = summary[-1]["status"]
    write_docs(summary, target_rows, route_rows)
    update_longform_docs(status, target_rows)
    upsert_hypothesis(status, target_rows)
    artifacts = [OUT_MD, PLAN_MD, THEORY_MD, VARIANT_MD, SUMMARY_CSV, TARGET_CSV, ROUTE_CSV, ARTIFACT_INDEX, Path(__file__).resolve()]
    write_artifact_index(artifacts)
    upsert_run_log(status)
    upsert_global_manifest()
    print(f"Stage135 decompose/DFT reuse target gate: {status}")
    print(f"Wrote {rel(SUMMARY_CSV)}")
    return 0 if not status.startswith("FAIL_") else 1


if __name__ == "__main__":
    raise SystemExit(main())
