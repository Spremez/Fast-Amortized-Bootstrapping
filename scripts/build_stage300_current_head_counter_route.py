#!/usr/bin/env python3
"""Build Stage300 current-head counter route audit artifacts."""

from __future__ import annotations

import csv
import hashlib
from pathlib import Path
from typing import Dict, Iterable, List, Optional


ROOT = Path(__file__).resolve().parents[1]
OUT_DIR = ROOT / "repro" / "stage300_current_head_counter_route"
LOCAL_STAGE28 = OUT_DIR / "local_stage28_perf_probe" / "summary.csv"
STAGE101 = ROOT / "repro" / "stage101_cb5_remote_native_perf" / "summary.csv"
STAGE226_PROOF = ROOT / "repro" / "stage226_exact_mat_avx_counter_attribution" / "proof_gate.csv"
STAGE226_COUNTERS = ROOT / "repro" / "stage226_exact_mat_avx_counter_attribution" / "counter_comparison.csv"
STAGE296_PERF = ROOT / "repro" / "stage296_direct_dft_highstat" / "perf_summary.csv"
STAGE299_PERF = ROOT / "repro" / "stage299_direct_dft_param_preflight" / "perf_summary.csv"
STAGE299_PROOF = ROOT / "repro" / "stage299_direct_dft_param_preflight" / "proof_gate.csv"

DOC = ROOT / "docs" / "stage300_current_head_counter_route.md"
THEORY = ROOT / "theory_checks" / "stage300_counter_route_claim_model.md"
VARIANT = ROOT / "algorithm_variants" / "mat_rlwe_sab_stage300_counter_route.md"
EXPERIMENT = ROOT / "experiments" / "stage300_current_head_counter_route_plan.md"

SUMMARY = OUT_DIR / "summary.csv"
EVIDENCE = OUT_DIR / "evidence_matrix.csv"
CLAIMS = OUT_DIR / "claim_boundary.csv"
GATES = OUT_DIR / "proof_gate.csv"
NEXT = OUT_DIR / "next_stage_queue.csv"
COMMANDS = OUT_DIR / "reproduction_commands.md"
REPORT = OUT_DIR / "stage300_report.md"
INDEX = OUT_DIR / "artifact_index.csv"

RUN_LOG = ROOT / "repro" / "run_log.csv"
MANIFEST = ROOT / "repro" / "artifact_manifest.md"
CHECKLIST = ROOT / "repro" / "reproduction_checklist.md"
ROADMAP = ROOT / "docs" / "roadmap_stage19_plus.md"
GOAL = ROOT / "docs" / "current_codex_goal_sab_completion.md"
HYPOTHESES = ROOT / "hypotheses" / "hypothesis_register.yaml"


def rel(path: Path) -> str:
    return path.relative_to(ROOT).as_posix()


def read_csv(path: Path) -> List[Dict[str, str]]:
    if not path.exists():
        return []
    with path.open(newline="", encoding="utf-8-sig") as f:
        return list(csv.DictReader(f))


def write_csv(path: Path, rows: Iterable[Dict[str, str]], fields: List[str]) -> None:
    rows = list(rows)
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fields, lineterminator="\n")
        writer.writeheader()
        writer.writerows(rows)


def find_row(rows: List[Dict[str, str]], key: str, value: str) -> Optional[Dict[str, str]]:
    for row in rows:
        if row.get(key) == value:
            return row
    return None


def get_status(rows: List[Dict[str, str]], key: str, value: str, field: str = "status") -> str:
    row = find_row(rows, key, value)
    if not row:
        return "MISSING"
    return row.get(field, "MISSING")


def fmt_float(text: str, default: str = "") -> str:
    if text == "":
        return default
    try:
        return f"{float(text):.6f}"
    except ValueError:
        return text


def sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def append_once(path: Path, marker: str, text: str) -> None:
    old = path.read_text(encoding="utf-8", errors="replace") if path.exists() else ""
    if marker in old:
        return
    with path.open("a", encoding="utf-8") as f:
        if old and not old.endswith("\n"):
            f.write("\n")
        f.write(text)


def append_run_log(decision: str) -> None:
    if not RUN_LOG.exists():
        fields = [
            "run_id",
            "date",
            "git_ref",
            "stage",
            "backend",
            "command",
            "config",
            "seed",
            "status",
            "summary",
            "artifacts",
        ]
        write_csv(RUN_LOG, [], fields)
    run_id = "stage300-current-head-counter-route-001"
    run_log_text = RUN_LOG.read_text(encoding="utf-8", errors="replace") if RUN_LOG.exists() else ""
    if run_id in run_log_text:
        return
    with RUN_LOG.open(newline="", encoding="utf-8-sig") as f:
        reader = csv.DictReader(f)
        fields = list(reader.fieldnames or [])
    if not fields:
        fields = [
            "run_id",
            "date",
            "git_ref",
            "stage",
            "backend",
            "command",
            "config",
            "seed",
            "status",
            "summary",
            "artifacts",
        ]
    new_row = {field: "" for field in fields}
    values = {
        "run_id": run_id,
        "date": "2026-07-05",
        "git_ref": "current-head-after-1f8da2a",
        "commit_or_state": "current-head-after-1f8da2a",
        "stage": "Stage 300",
        "backend": "spqlios_avx512",
        "command": "bash scripts/run_stage300_current_head_counter_route.sh",
        "config": "local Stage28 counter probe plus Stage296/Stage299 direct-DFT evidence audit",
        "params": "local Stage28 counter probe plus Stage296/Stage299 direct-DFT evidence audit",
        "seed": "n/a",
        "status": decision,
        "summary": "Current WSL counter route audited; historical native counters remain context only for the current direct-DFT head unless refreshed.",
        "artifacts": f"{rel(DOC)}; {rel(SUMMARY)}; {rel(EVIDENCE)}; {rel(GATES)}",
    }
    for key, value in values.items():
        if key in new_row:
            new_row[key] = value
    with RUN_LOG.open("a", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fields, lineterminator="\n")
        writer.writerow(new_row)


def perf_direct_summary(path: Path) -> Dict[str, str]:
    rows = read_csv(path)
    direct = find_row(rows, "variant", "perf_direct_dft") or {}
    comparison = find_row(rows, "variant", "comparison") or {}
    return {
        "samples": direct.get("samples", ""),
        "correctness": direct.get("correctness", ""),
        "t_bootstrap_over_r_mean_us": fmt_float(direct.get("t_bootstrap_over_r_mean_us", "")),
        "speedup_vs_repeated_scalar_mean": fmt_float(direct.get("speedup_vs_repeated_scalar_mean", "")),
        "direct_dft_vs_selected_control_mean": fmt_float(
            comparison.get("direct_dft_vs_selected_control_mean", "")
        ),
    }


def write_markdown(decision: str, evidence_rows: List[Dict[str, str]], gate_rows: List[Dict[str, str]]) -> None:
    lines = [
        "# Stage300 Current-Head Counter Route Audit",
        "",
        f"Decision: `{decision}`.",
        "",
        "Stage300 is a routing and claim-boundary audit, not a new speed claim.",
        "It checks whether the current direct-DFT PVW/MAT-SAB head has hardware",
        "counter attribution, and separates current-head evidence from historical",
        "native counter context.",
        "",
        "## Evidence Matrix",
        "",
        "| item | status | evidence | interpretation |",
        "| --- | --- | --- | --- |",
    ]
    for row in evidence_rows:
        lines.append(
            f"| {row['item']} | {row['status']} | {row['evidence']} | {row['interpretation']} |"
        )
    lines.extend(["", "## Proof Gate", "", "| gate | status | value | interpretation |", "| --- | --- | --- | --- |"])
    for row in gate_rows:
        lines.append(
            f"| {row['gate']} | {row['status']} | {row['value']} | {row['interpretation']} |"
        )
    lines.extend(
        [
            "",
            "## Claim Boundary",
            "",
            "The current complete-SAB metric remains `T_bootstrap/r`. Historical native",
            "counter artifacts can guide mechanism hypotheses, but they do not prove",
            "MAT-AVX512 optimality for the current direct-DFT candidate without a",
            "current-head refresh.",
            "",
        ]
    )
    text = "\n".join(lines)
    DOC.write_text(text, encoding="utf-8")
    REPORT.write_text(text, encoding="utf-8")


def artifact_index(paths: List[Path]) -> List[Dict[str, str]]:
    rows: List[Dict[str, str]] = []
    for path in paths:
        if path.exists() and path.is_file():
            rows.append(
                {
                    "path": rel(path),
                    "bytes": str(path.stat().st_size),
                    "sha256": sha256_file(path),
                }
            )
    return rows


def main() -> None:
    OUT_DIR.mkdir(parents=True, exist_ok=True)

    local_rows = read_csv(LOCAL_STAGE28)
    stage101_rows = read_csv(STAGE101)
    stage226_rows = read_csv(STAGE226_PROOF)
    stage296 = perf_direct_summary(STAGE296_PERF)
    stage299 = perf_direct_summary(STAGE299_PERF)
    stage299_gate_rows = read_csv(STAGE299_PROOF)

    local_counter_gate = get_status(local_rows, "probe", "hardware_counter_gate")
    local_perf_command = get_status(local_rows, "probe", "perf_command")
    stage101_decision = get_status(stage101_rows, "gate", "stage101_cb5_decision")
    stage226_decision = get_status(stage226_rows, "gate", "G7_stage226_decision")
    stage299_decision = get_status(stage299_gate_rows, "gate", "G6_decision")

    current_direct_perf_ok = (
        stage296.get("correctness") == "Pass"
        and stage296.get("samples") == "10"
        and stage299_decision == "PASS_STAGE299_DIRECT_DFT_PARAM_PREFLIGHT_LOCAL"
    )
    local_counter_current = local_counter_gate in {"PASS", "READY_FOR_BENCH"}
    historical_counter_context = (
        stage101_decision == "PASS_STAGE101_CB5_NATIVE_PERF_COUNTERS_RECORDED"
        and stage226_decision == "PASS_STAGE226_EXACT_COUNTER_ATTRIBUTION_POSITIVE"
    )

    if local_counter_current:
        decision = "PASS_STAGE300_LOCAL_COUNTER_READY_CURRENT_HEAD_BENCH_PENDING"
    elif current_direct_perf_ok and historical_counter_context:
        decision = "PASS_STAGE300_COUNTER_CONTEXT_CURRENT_HEAD_REFRESH_REQUIRED"
    elif current_direct_perf_ok:
        decision = "PASS_STAGE300_LOCAL_COUNTER_BLOCKED_PARAM_MATRIX_ROUTE"
    else:
        decision = "FAIL_STAGE300_COUNTER_ROUTE_AUDIT"

    evidence_rows = [
        {
            "item": "current_direct_dft_target_highstat",
            "status": "PASS" if stage296.get("correctness") == "Pass" else "MISSING",
            "evidence": rel(STAGE296_PERF),
            "interpretation": (
                f"SET_2_3_2048 direct/control={stage296['direct_dft_vs_selected_control_mean']}; "
                f"direct/scalar={stage296['speedup_vs_repeated_scalar_mean']}; "
                f"samples={stage296['samples']}."
            ),
        },
        {
            "item": "current_direct_dft_added_param_preflight",
            "status": "PASS" if stage299_decision == "PASS_STAGE299_DIRECT_DFT_PARAM_PREFLIGHT_LOCAL" else "MISSING",
            "evidence": rel(STAGE299_PERF),
            "interpretation": (
                f"SET_4_5_2048 direct/control={stage299['direct_dft_vs_selected_control_mean']}; "
                f"direct/scalar={stage299['speedup_vs_repeated_scalar_mean']}; "
                f"samples={stage299['samples']}."
            ),
        },
        {
            "item": "local_counter_capability",
            "status": local_counter_gate,
            "evidence": rel(LOCAL_STAGE28) if LOCAL_STAGE28.exists() else "missing",
            "interpretation": f"local perf_command={local_perf_command}; current host route={local_counter_gate}.",
        },
        {
            "item": "historical_native_counter_context_stage101",
            "status": stage101_decision,
            "evidence": rel(STAGE101),
            "interpretation": "Native counter evidence exists for an earlier PVW/MAT-SAB path; use as context only.",
        },
        {
            "item": "historical_exact_route_counter_context_stage226",
            "status": stage226_decision,
            "evidence": rel(STAGE226_COUNTERS),
            "interpretation": "Exact-route counters record small load/store/cycle direction; not current direct-DFT proof.",
        },
    ]
    write_csv(EVIDENCE, evidence_rows, ["item", "status", "evidence", "interpretation"])

    gate_rows = [
        {
            "gate": "G1_current_direct_perf",
            "status": "PASS" if current_direct_perf_ok else "FAIL",
            "value": "stage296+stage299",
            "interpretation": "Current direct-DFT complete-SAB T/r evidence is available before counter routing.",
        },
        {
            "gate": "G2_local_counter_capability",
            "status": "PASS" if local_counter_current else "BLOCKED",
            "value": local_counter_gate,
            "interpretation": "Local WSL can run current-head counters only if this is PASS or READY_FOR_BENCH.",
        },
        {
            "gate": "G3_historical_counter_context",
            "status": "PASS" if historical_counter_context else "MISSING",
            "value": f"stage101={stage101_decision}; stage226={stage226_decision}",
            "interpretation": "Historical counters inform hypotheses but cannot replace current-head direct-DFT counters.",
        },
        {
            "gate": "G4_claim_boundary",
            "status": "PASS_NO_OPTIMALITY_CLAIM",
            "value": "counter_refresh_required",
            "interpretation": "Do not claim theoretical MAT-AVX512 optimality for direct DFT until current-head counters are recorded.",
        },
        {
            "gate": "G5_decision",
            "status": decision,
            "value": decision,
            "interpretation": "Controls Stage301 route.",
        },
    ]
    write_csv(GATES, gate_rows, ["gate", "status", "value", "interpretation"])

    summary_rows = [
        {
            "decision": decision,
            "local_counter_gate": local_counter_gate,
            "historical_counter_context": "present" if historical_counter_context else "missing",
            "current_direct_dft_perf": "present" if current_direct_perf_ok else "missing",
            "next_route": (
                "current_head_native_counter_refresh"
                if not local_counter_current
                else "local_current_head_counter_bench"
            ),
        }
    ]
    write_csv(
        SUMMARY,
        summary_rows,
        [
            "decision",
            "local_counter_gate",
            "historical_counter_context",
            "current_direct_dft_perf",
            "next_route",
        ],
    )

    claim_rows = [
        {
            "claim": "complete_sab_t_over_r",
            "status": "supported_current_head",
            "allowed": "Use Stage296/Stage299 for scoped complete-SAB amortized performance.",
            "not_allowed": "Do not convert T/r evidence into theoretical AVX optimality.",
        },
        {
            "claim": "hardware_counter_attribution",
            "status": "context_only_until_refresh",
            "allowed": "Use Stage101/Stage226 as historical mechanism context.",
            "not_allowed": "Do not cite historical counters as current direct-DFT counter proof.",
        },
        {
            "claim": "mat_avx512_theoretical_optimality",
            "status": "not_supported",
            "allowed": "State that a current-head counter refresh is required.",
            "not_allowed": "Do not claim optimality from timing alone.",
        },
    ]
    write_csv(CLAIMS, claim_rows, ["claim", "status", "allowed", "not_allowed"])

    next_rows = [
        {
            "priority": "P0",
            "route": "stage301_current_head_native_counter_refresh",
            "entry_condition": decision,
            "gate": "Run current direct-DFT complete-SAB or focused MAT EP probe under native perf counters.",
            "failure_action": "Keep counter claims context-only and continue parameter matrix.",
        },
        {
            "priority": "P1",
            "route": "stage301_parameter_matrix_highstat",
            "entry_condition": "native counter refresh not executable",
            "gate": "Promote SET_4_5_2048 from preflight to repeated performance/noise/resource matrix.",
            "failure_action": "Restrict parameter claim to SET_2_3_2048 plus one preflight.",
        },
    ]
    write_csv(NEXT, next_rows, ["priority", "route", "entry_condition", "gate", "failure_action"])

    COMMANDS.write_text(
        "\n".join(
            [
                "# Stage300 Reproduction Commands",
                "",
                "```bash",
                "STAGE300_OUT_DIR=repro/stage300_current_head_counter_route bash scripts/run_stage300_current_head_counter_route.sh",
                "```",
                "",
            ]
        ),
        encoding="utf-8",
    )

    THEORY.write_text(
        "\n".join(
            [
                "# Stage300 Counter Route Claim Model",
                "",
                "Hardware counters test a mechanism claim, not the complete-SAB speed claim.",
                "The complete-SAB endpoint remains `T_bootstrap/r`. A counter run may support",
                "load/store/FMA attribution for a specific implementation and commit, but it",
                "cannot be transferred from historical variants to the current direct-DFT path",
                "without a current-head refresh.",
                "",
            ]
        ),
        encoding="utf-8",
    )
    VARIANT.write_text(
        "\n".join(
            [
                "# Stage300 Counter Route Audit Variant",
                "",
                "This stage introduces no hot-path algorithm variant. It audits whether the",
                "current direct-DFT PVW/MAT-SAB candidate has native counter attribution and",
                "routes the next experiment accordingly.",
                "",
            ]
        ),
        encoding="utf-8",
    )
    EXPERIMENT.write_text(
        "\n".join(
            [
                "# Stage300 Experiment Plan",
                "",
                "1. Run local Stage28 perf availability probe.",
                "2. Read Stage296 target high-stat and Stage299 added-parameter preflight.",
                "3. Read historical Stage101/Stage226 native counter context.",
                "4. Emit a route decision without upgrading theoretical optimality claims.",
                "",
            ]
        ),
        encoding="utf-8",
    )

    write_markdown(decision, evidence_rows, gate_rows)
    append_once(
        ROADMAP,
        "## Stage 300: Current-Head Counter Route Audit",
        "\n## Stage 300: Current-Head Counter Route Audit\n\n"
        "Goal: separate current direct-DFT complete-SAB evidence from historical native\n"
        "counter context, and route the next executable Stage301 experiment.\n\n"
        f"Status: `{decision}`.\n",
    )
    append_once(
        GOAL,
        "<!-- stage300-current-head-counter-route -->",
        "\n<!-- stage300-current-head-counter-route -->\n"
        "### Stage300 current-head counter route audit\n\n"
        f"`{decision}` records that Stage296/Stage299 support scoped current-head\n"
        "complete-SAB `T_bootstrap/r`, while historical native counters remain\n"
        "context-only until a current-head direct-DFT counter refresh is recorded.\n",
    )
    append_once(
        HYPOTHESES,
        "H300_current_head_counter_refresh",
        "\nH300_current_head_counter_refresh:\n"
        "  claim: Current direct-DFT MAT/PVW-SAB needs native counter attribution before MAT-AVX512 optimality wording.\n"
        f"  status: {decision}\n"
        "  evidence: repro/stage300_current_head_counter_route/proof_gate.csv\n"
        "  next_gate: Stage301 current-head native counter refresh or parameter matrix high-stat.\n",
    )
    append_once(
        MANIFEST,
        "- stage300_current_head_counter_route:",
        "\n- stage300_current_head_counter_route:\n"
        f"  - `{rel(DOC)}`\n"
        f"  - `{rel(SUMMARY)}`\n"
        f"  - `{rel(EVIDENCE)}`\n"
        f"  - `{rel(GATES)}`\n",
    )
    append_once(
        CHECKLIST,
        "Stage300 current-head counter route audit",
        "\n- [x] Stage300 current-head counter route audit recorded with local perf probe and claim boundary.\n",
    )
    append_run_log(decision)

    artifacts = [
        DOC,
        REPORT,
        THEORY,
        VARIANT,
        EXPERIMENT,
        SUMMARY,
        EVIDENCE,
        CLAIMS,
        GATES,
        NEXT,
        COMMANDS,
        OUT_DIR / "environment.log",
        OUT_DIR / "local_stage28_stdout.log",
        OUT_DIR / "local_stage28_stderr.log",
        OUT_DIR / "local_stage28_rc.log",
        LOCAL_STAGE28,
        OUT_DIR / "local_stage28_perf_probe" / "environment.log",
        OUT_DIR / "local_stage28_perf_probe" / "perf_smoke.log",
        OUT_DIR / "local_stage28_perf_probe" / "perf_smoke.err",
    ]
    write_csv(INDEX, artifact_index(artifacts), ["path", "bytes", "sha256"])
    print(decision)


if __name__ == "__main__":
    main()
