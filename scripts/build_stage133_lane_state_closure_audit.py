#!/usr/bin/env python3
"""Build Stage133 lane-state closure audit from Stage132 evidence."""

from __future__ import annotations

import csv
import hashlib
import subprocess
from pathlib import Path
from typing import Dict, Iterable, List


ROOT = Path(__file__).resolve().parents[1]
STAGE132_DIR = ROOT / "repro" / "stage132_lane_pair_cmux_consumption_gate"
STAGE132_SUMMARY = STAGE132_DIR / "summary.csv"
STAGE132_API = STAGE132_DIR / "api_results.csv"
OUT_DIR = ROOT / "repro" / "stage133_lane_state_closure_audit"
SUMMARY_CSV = OUT_DIR / "summary.csv"
CLOSURE_CSV = OUT_DIR / "closure_matrix.csv"
ROUTE_CSV = OUT_DIR / "route_matrix.csv"
ARTIFACT_INDEX = OUT_DIR / "artifact_index.csv"
OUT_MD = ROOT / "docs" / "stage133_lane_state_closure_audit.md"
PLAN_MD = ROOT / "experiments" / "stage133_lane_state_closure_audit_plan.md"
THEORY_MD = ROOT / "theory_checks" / "stage133_lane_state_closure_model.md"
VARIANT_MD = ROOT / "algorithm_variants" / "mat_rlwe_sab_lane_state_closure.md"
RUN_LOG = ROOT / "repro" / "run_log.csv"
GLOBAL_MANIFEST = ROOT / "repro" / "artifact_manifest.md"
HYPOTHESIS_YAML = ROOT / "hypotheses" / "hypothesis_register.yaml"
ROADMAP_MD = ROOT / "docs" / "roadmap_stage19_plus.md"
GOAL_MD = ROOT / "docs" / "goal_sab_max_acceleration.md"
CURRENT_GOAL_MD = ROOT / "docs" / "current_codex_goal_sab_completion.md"


SUMMARY_FIELDS = ["gate", "status", "metric", "value", "evidence", "detail", "next_action"]
CLOSURE_FIELDS = ["candidate", "status", "evidence", "reason", "next_action"]
ROUTE_FIELDS = [
    "route",
    "next_stage",
    "status",
    "correctness_gate",
    "performance_gate",
    "risk",
]


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


def stage132_correct(api_rows: List[Dict[str, str]]) -> bool:
    return len(api_rows) == 6 and all(
        row.get("status") == "PASS_LANE_PAIR_CMUX_DELTA_CONSUMPTION"
        and row.get("component_mismatches") == "0"
        and row.get("delta_phase_mismatches") == "0"
        and row.get("consumer_phase_mismatches") == "0"
        and row.get("noise_model_mismatches") == "0"
        and int(row.get("shared_output_negative_failures", "0")) > 0
        for row in api_rows
    )


def build_matrices(api_rows: List[Dict[str, str]]) -> tuple[List[Dict[str, str]], List[Dict[str, str]]]:
    neg_min = min((int(row["shared_output_negative_failures"]) for row in api_rows), default=0)
    neg_max = max((int(row["shared_output_negative_failures"]) for row in api_rows), default=0)
    max_gap = max(
        (
            max(
                int(row["max_component_gap"]),
                int(row["max_delta_phase_gap"]),
                int(row["max_consumer_phase_gap"]),
            )
            for row in api_rows
        ),
        default=0,
    )
    closure_rows = [
        {
            "candidate": "lane_pair_accumulator_state",
            "status": "PASS_AS_INTERNAL_STATE",
            "evidence": rel(STAGE132_API),
            "reason": (
                "Stage132 has zero component, delta-phase, consumer-phase, and "
                f"noise-model mismatches; max observed gap is {max_gap} under tolerance 131072."
            ),
            "next_action": "Define an explicit lane-pair accumulator object with one mask/body pair per lane.",
        },
        {
            "candidate": "standard_pvw_shared_output_state",
            "status": "REJECTED_BY_NEGATIVE_CONTROL",
            "evidence": rel(STAGE132_API),
            "reason": (
                "Collapsing lane-pair masks into one shared output mask fails for r>1; "
                f"negative failures range from {neg_min} to {neg_max}."
            ),
            "next_action": "Do not store Stage131 output as PVW_TMLWE_DFT without a separate proof gate.",
        },
        {
            "candidate": "stage131_shared_source_compact_ep_direct_iteration",
            "status": "BLOCKED_BY_STATE_SHAPE",
            "evidence": f"{rel(STAGE132_API)}; {rel(THEORY_MD)}",
            "reason": (
                "The Stage131 kernel accepts one shared source mask and r bodies, "
                "but after one compact CMUX update the accumulator has per-lane masks."
            ),
            "next_action": "Choose generalized lane-pair input EP, re-share/key-switch, or prove a shared-output selector invariant.",
        },
        {
            "candidate": "existing_dense_mat_trgsw_path",
            "status": "AVAILABLE_REFERENCE_NOT_TARGET",
            "evidence": "src/sab_pvw.c; include/sab_pvw.h",
            "reason": (
                "The dense MAT path is already iterative because it uses standard PVW_TMLWE state, "
                "but it does not use the Stage130 shared-source compact mechanism."
            ),
            "next_action": "Keep as correctness/performance reference, not as the compact-path solution.",
        },
        {
            "candidate": "generalized_lane_pair_input_compact_ep",
            "status": "NEXT_REQUIRED_GATE",
            "evidence": "Stage129 neutral 2r-source evidence plus Stage132 lane-pair state evidence.",
            "reason": (
                "A generalized input kernel can consume per-lane masks and bodies, preserving lane-state closure, "
                "but it reintroduces more decomposition streams."
            ),
            "next_action": "Build a Stage134 generated generalized-input compact EP correctness and microbench gate.",
        },
        {
            "candidate": "reshare_or_keyswitch_to_shared_mask",
            "status": "OPEN_HIGH_RISK",
            "evidence": rel(CLOSURE_CSV),
            "reason": "Re-sharing may restore Stage131 input shape but can add latency, memory, noise, and key material.",
            "next_action": "Analyze only if generalized-input EP loses full-SAB amortized throughput.",
        },
        {
            "candidate": "prove_selector_shared_output_structure",
            "status": "OPEN_THEORY_GATE",
            "evidence": rel(CLOSURE_CSV),
            "reason": "A stronger selector invariant could preserve shared output masks, but Stage132 negative control rejects the current form.",
            "next_action": "Do not implement until a finite algebraic selector proof candidate exists.",
        },
    ]
    route_rows = [
        {
            "route": "generalized_lane_pair_input_compact_ep",
            "next_stage": "Stage134",
            "status": "PRIMARY_NEXT",
            "correctness_gate": "component/phase/noise equivalence for lane-pair input and output, r=2/4/6",
            "performance_gate": "same-backend microbench versus dense MAT and Stage131 shared-source first-step proxy",
            "risk": "more decomposition/DFT streams may erase compact addmul gains for r=4",
        },
        {
            "route": "lane_pair_rgsw_monomial_state",
            "next_stage": "Stage135_after_Stage134",
            "status": "CONDITIONAL",
            "correctness_gate": "one RGSW monomial step preserves lane-pair phase against scalar lane references",
            "performance_gate": "RGSW step timing and copyback profile under r=4/r=6",
            "risk": "state conversion or buffer normalization may dominate",
        },
        {
            "route": "direct_stage131_shared_source_iteration",
            "next_stage": "none",
            "status": "REJECTED_UNTIL_NEW_PROOF",
            "correctness_gate": "requires true shared-output-mask invariant, absent here",
            "performance_gate": "not applicable",
            "risk": "would silently compare wrong phases after the first CMUX",
        },
        {
            "route": "reshare_to_shared_mask",
            "next_stage": "deferred",
            "status": "DEFERRED_HIGH_COST",
            "correctness_gate": "phase/noise equivalence plus key-switch or re-encryption security accounting",
            "performance_gate": "full-SAB T_bootstrap/r including re-share overhead",
            "risk": "likely adds too much latency/noise/key material",
        },
    ]
    return closure_rows, route_rows


def build_summary(api_rows: List[Dict[str, str]]) -> List[Dict[str, str]]:
    summary132 = read_csv(STAGE132_SUMMARY)
    stage132_status = summary132[-1]["status"] if summary132 else "missing"
    correctness = stage132_correct(api_rows)
    neg_min = min((int(row["shared_output_negative_failures"]) for row in api_rows), default=0)
    decision = (
        "PASS_STAGE133_CLOSURE_AUDIT_DIRECT_SHARED_SOURCE_ITERATION_BLOCKED"
        if stage132_status.startswith("PASS_") and correctness and neg_min > 0
        else "FAIL_STAGE133_CLOSURE_AUDIT"
    )
    return [
        {
            "gate": "stage133_stage132_input_evidence",
            "status": "PASS" if stage132_status.startswith("PASS_") else "FAIL",
            "metric": "stage132_decision",
            "value": stage132_status,
            "evidence": rel(STAGE132_SUMMARY),
            "detail": "Closure audit starts only from a passed Stage132 consumer gate.",
            "next_action": "",
        },
        {
            "gate": "stage133_lane_pair_state_valid",
            "status": "PASS" if correctness else "FAIL",
            "metric": "stage132_rows",
            "value": str(len(api_rows)),
            "evidence": rel(STAGE132_API),
            "detail": "Lane-pair state is valid as an internal accumulator representation.",
            "next_action": "",
        },
        {
            "gate": "stage133_shared_output_closure",
            "status": "BLOCKED_AS_EXPECTED" if neg_min > 0 else "FAIL",
            "metric": "min_shared_output_negative_failures",
            "value": str(neg_min),
            "evidence": rel(STAGE132_API),
            "detail": "Current compact output is not closed as a standard shared-output PVW ciphertext.",
            "next_action": "Do not directly iterate Stage131 shared-source EP after a CMUX update.",
        },
        {
            "gate": "stage133_decision",
            "status": decision,
            "metric": "promotion_policy",
            "value": "",
            "evidence": f"{rel(SUMMARY_CSV)}; {rel(CLOSURE_CSV)}; {rel(ROUTE_CSV)}",
            "detail": "The correct next implementation target is generalized lane-pair input EP.",
            "next_action": "Stage134 should build a generalized-input compact EP correctness and microbench gate.",
        },
    ]


def table(rows: List[Dict[str, str]], fields: List[str]) -> List[str]:
    lines = ["| " + " | ".join(fields) + " |", "|" + "|".join(["---"] * len(fields)) + "|"]
    for row in rows:
        lines.append("| " + " | ".join(row.get(field, "") for field in fields) + " |")
    return lines


def write_docs(
    summary: List[Dict[str, str]],
    closure_rows: List[Dict[str, str]],
    route_rows: List[Dict[str, str]],
) -> None:
    decision = summary[-1]["status"]
    write_text_lf(
        PLAN_MD,
        "\n".join(
            [
                "# Stage133 Lane-State Closure Audit Plan",
                "",
                "Date: 2026-07-03",
                "",
                "## Objective",
                "",
                "Decide whether the Stage131/132 compact lane-pair output is closed",
                "under repeated SAB CMUX/RGSW use, and select the next implementation",
                "route without overclaiming full bootstrapping acceleration.",
                "",
                "## Command",
                "",
                "```bash",
                "python scripts/build_stage133_lane_state_closure_audit.py",
                "```",
                "",
                "## Falsification Criteria",
                "",
                "- Stage132 evidence is missing or failed;",
                "- lane-pair consumer mismatches are nonzero;",
                "- shared-output negative-control failures are zero;",
                "- direct Stage131 iteration is promoted despite state-shape mismatch.",
            ]
        )
        + "\n",
    )
    write_text_lf(
        THEORY_MD,
        "\n".join(
            [
                "# Stage133 Lane-State Closure Model",
                "",
                "Date: 2026-07-03",
                "",
                "A complete compact SAB path needs repeated updates. Stage131 accepts",
                "a `PVW_TMLWE`-shaped source with one shared mask and r bodies. Stage132",
                "shows the output after compact CMUX consumption is valid only as",
                "lane-pair state: one mask/body pair per lane.",
                "",
                "Therefore direct iteration of the Stage131 shared-source kernel is",
                "not closed after one CMUX update. The next finite implementation gate",
                "must either consume lane-pair input directly, re-share/key-switch back",
                "to a shared mask, or prove a stronger selector invariant that makes",
                "shared output valid. The first route is the primary next experiment.",
                "",
                "## Closure Matrix",
                "",
                *table(closure_rows, CLOSURE_FIELDS),
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
                "# V133: Lane-State Closure Audit",
                "",
                "## Summary",
                "",
                "- Parent algorithm: PVW/MAT-SAB r-body research track.",
                "- Focused module: state representation after compact CMUX.",
                "- Optimization target: complete-SAB amortized `T_bootstrap/r`.",
                "- Status labels: `[closure-audit]`, `[direct-shared-source-blocked]`,",
                "  `[generalized-input-next]`.",
                f"- Decision: `{decision}`.",
                "",
                "## Key Result",
                "",
                "Lane-pair state is a valid internal accumulator representation, but",
                "it is not the same as the shared-source input required by the",
                "Stage131 compact EP API. Direct repeated shared-source iteration is",
                "therefore rejected until a new proof or state-conversion gate exists.",
            ]
        )
        + "\n",
    )
    md = [
        "# Stage133 Lane-State Closure Audit",
        "",
        "Date: 2026-07-03",
        "",
        "## Decision",
        "",
        f"`{decision}`",
        "",
        "Stage133 turns the Stage132 consumer result into a route decision for",
        "the next compact SAB implementation step.",
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
    md += ["", "## Closure Matrix", "", *table(closure_rows, CLOSURE_FIELDS)]
    md += ["", "## Route Matrix", "", *table(route_rows, ROUTE_FIELDS)]
    md += [
        "",
        "## Interpretation",
        "",
        "The compact lane-pair output can be used as an internal accumulator",
        "state, but it cannot be silently converted to standard PVW shared-mask",
        "state. The next concrete implementation work is a generalized-input",
        "compact EP gate that consumes lane-pair masks directly.",
    ]
    write_text_lf(OUT_MD, "\n".join(md) + "\n")


def update_longform_docs(status: str) -> None:
    stage_block = """
## Stage 133: Lane-State Closure Audit

Goal:

```text
Determine whether the Stage131 shared-source compact EP can be directly
iterated after Stage132 CMUX consumption, or whether a different state/input
kernel is required.
```

Theory basis:

Stage131 consumes one shared source mask and r bodies. Stage132 validates an
output with one mask/body pair per lane and rejects collapse to one shared
output mask. Therefore a repeated SAB schedule cannot feed the post-CMUX
lane-pair accumulator back into the Stage131 shared-source kernel without a new
invariant or conversion.

Status:

```text
Completed. Stage133 records
PASS_STAGE133_CLOSURE_AUDIT_DIRECT_SHARED_SOURCE_ITERATION_BLOCKED. Lane-pair
state is valid as an internal accumulator representation, but direct
Stage131 shared-source compact EP iteration is blocked by state shape. The
primary next route is a generalized lane-pair input compact EP correctness and
microbench gate.
```
"""
    append_once(ROADMAP_MD, "## Stage 133: Lane-State Closure Audit", stage_block)
    goal_block = """
Stage133 fixes the next research boundary: Stage132 is not enough for full SAB
because the lane-pair output is not closed under the Stage131 shared-source
input type. Direct repeated shared-source iteration is blocked. The next
productive implementation target is a generalized lane-pair input compact EP
gate, with re-share/key-switch and selector-proof routes deferred.
"""
    append_once(GOAL_MD, "Stage133 fixes the next research boundary", goal_block)
    current_goal_block = f"""
37. Treat Stage133 as the current lane-state closure audit:
    `{status}`. Lane-pair compact output is valid as internal accumulator
    state, but direct iteration of the Stage131 shared-source compact EP is
    blocked because the next source would have per-lane masks rather than one
    shared mask. The next valid implementation stage is generalized lane-pair
    input compact EP, followed only later by RGSW/sparse schedule integration.
"""
    append_once(CURRENT_GOAL_MD, "37. Treat Stage133 as the current lane-state", current_goal_block)


def upsert_hypothesis(status: str) -> None:
    block = f"""  - id: H57_lane_state_closure
    statement: >
      Stage132 lane-pair compact CMUX output is a valid internal accumulator
      state but is not closed under direct reuse by the Stage131 shared-source
      compact external-product input API.
    mechanism: >
      Stage133 audits Stage132 evidence: per-lane consumer correctness passes,
      while shared-output-mask collapse fails for r>1. Because the Stage131
      kernel consumes one shared source mask and r bodies, a post-CMUX
      lane-pair accumulator with per-lane masks cannot be fed back directly.
    status: stage133_closure_audit_direct_shared_source_iteration_blocked
    evidence: docs/stage133_lane_state_closure_audit.md; experiments/stage133_lane_state_closure_audit_plan.md; theory_checks/stage133_lane_state_closure_model.md; algorithm_variants/mat_rlwe_sab_lane_state_closure.md; scripts/build_stage133_lane_state_closure_audit.py; repro/stage133_lane_state_closure_audit/summary.csv; repro/stage133_lane_state_closure_audit/closure_matrix.csv; repro/stage133_lane_state_closure_audit/route_matrix.csv; repro/stage133_lane_state_closure_audit/artifact_index.csv
    current_decision: >
      Stage133 records {status}. It promotes lane-pair accumulator state only
      as an internal representation, rejects direct shared-output PVW collapse,
      and selects generalized lane-pair input compact EP as the next finite
      implementation gate.
    failure_criteria:
      - later stages feed lane-pair accumulator state into the Stage131
        shared-source kernel without conversion or generalized input support
      - direct shared-source iteration is used for full SAB timing claims
      - generalized-input overhead is ignored in `T_bootstrap/r`
      - re-share/key-switch or selector-proof routes are claimed without their
        own correctness, noise, and performance gates
"""
    text = HYPOTHESIS_YAML.read_text(encoding="utf-8")
    marker = "  - id: H57_lane_state_closure"
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
    run_id = "stage133-lane-state-closure-audit-001"
    rows = [row for row in read_csv(RUN_LOG) if row.get("run_id") != run_id]
    artifacts = [
        OUT_MD,
        PLAN_MD,
        THEORY_MD,
        VARIANT_MD,
        SUMMARY_CSV,
        CLOSURE_CSV,
        ROUTE_CSV,
        ARTIFACT_INDEX,
        Path(__file__).resolve(),
    ]
    rows.append(
        {
            "run_id": run_id,
            "date": "2026-07-03",
            "commit_or_state": f"working-tree-after-{git_head()}",
            "stage": "Stage 133",
            "backend": "evidence audit from Stage132 spqlios gate",
            "command": "python scripts/build_stage133_lane_state_closure_audit.py",
            "params": "Stage132 k=1 T=7 Bg_bit=7 r=2,4,6 N=512,1024",
            "seed": "0 subset inherited",
            "status": status,
            "summary": "Stage133 audits closure and selects generalized lane-pair input EP as next route.",
            "artifacts": "; ".join(rel(p) for p in artifacts),
        }
    )
    write_csv(RUN_LOG, rows, fields)


def upsert_global_manifest() -> None:
    block = """
## Stage 133 Lane-State Closure Audit

- `docs/stage133_lane_state_closure_audit.md`
- `experiments/stage133_lane_state_closure_audit_plan.md`
- `theory_checks/stage133_lane_state_closure_model.md`
- `algorithm_variants/mat_rlwe_sab_lane_state_closure.md`
- `scripts/build_stage133_lane_state_closure_audit.py`
- `repro/stage133_lane_state_closure_audit/summary.csv`
- `repro/stage133_lane_state_closure_audit/closure_matrix.csv`
- `repro/stage133_lane_state_closure_audit/route_matrix.csv`
- `repro/stage133_lane_state_closure_audit/artifact_index.csv`
"""
    append_once(GLOBAL_MANIFEST, "## Stage 133 Lane-State Closure Audit", block)


def main() -> int:
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    api_rows = read_csv(STAGE132_API)
    summary = build_summary(api_rows)
    closure_rows, route_rows = build_matrices(api_rows)
    write_csv(SUMMARY_CSV, summary, SUMMARY_FIELDS)
    write_csv(CLOSURE_CSV, closure_rows, CLOSURE_FIELDS)
    write_csv(ROUTE_CSV, route_rows, ROUTE_FIELDS)
    write_docs(summary, closure_rows, route_rows)
    status = summary[-1]["status"]
    update_longform_docs(status)
    upsert_hypothesis(status)
    artifacts = [
        OUT_MD,
        PLAN_MD,
        THEORY_MD,
        VARIANT_MD,
        SUMMARY_CSV,
        CLOSURE_CSV,
        ROUTE_CSV,
        ARTIFACT_INDEX,
        Path(__file__).resolve(),
    ]
    write_artifact_index(artifacts)
    upsert_run_log(status)
    upsert_global_manifest()
    print(f"Stage133 lane-state closure audit: {status}")
    print(f"Wrote {rel(SUMMARY_CSV)}")
    return 0 if status.startswith("PASS_") else 1


if __name__ == "__main__":
    raise SystemExit(main())
