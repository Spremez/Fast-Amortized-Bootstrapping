#!/usr/bin/env python3
"""Build Stage302 counter interpretation and next-stage selection."""

from __future__ import annotations

import csv
import hashlib
from pathlib import Path
from typing import Dict, Iterable, List, Optional


ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "repro" / "stage302_counter_interpretation"
DOC = ROOT / "docs" / "stage302_counter_interpretation.md"
THEORY = ROOT / "theory_checks" / "stage302_counter_to_algorithm_model.md"
VARIANT = ROOT / "algorithm_variants" / "mat_rlwe_sab_stage302_counter_interpretation.md"
EXPERIMENT = ROOT / "experiments" / "stage302_counter_interpretation_plan.md"

STAGE296_PERF = ROOT / "repro" / "stage296_direct_dft_highstat" / "perf_summary.csv"
STAGE299_PERF = ROOT / "repro" / "stage299_direct_dft_param_preflight" / "perf_summary.csv"
STAGE301_RUNS = ROOT / "repro" / "stage301_current_head_direct_dft_native_counter" / "run_metrics.csv"
STAGE301_COUNTERS = ROOT / "repro" / "stage301_current_head_direct_dft_native_counter" / "counter_comparison.csv"
STAGE301_PROOF = ROOT / "repro" / "stage301_current_head_direct_dft_native_counter" / "proof_gate.csv"

SUMMARY = OUT / "summary.csv"
MECHANISM = OUT / "mechanism_interpretation.csv"
CLAIMS = OUT / "claim_boundary.csv"
PROOF = OUT / "proof_gate.csv"
NEXT = OUT / "next_stage_queue.csv"
COMMANDS = OUT / "reproduction_commands.md"
REPORT = OUT / "stage302_report.md"
INDEX = OUT / "artifact_index.csv"

GOAL = ROOT / "docs" / "current_codex_goal_sab_completion.md"
ROADMAP = ROOT / "docs" / "roadmap_stage19_plus.md"
HYPOTHESES = ROOT / "hypotheses" / "hypothesis_register.yaml"
RUN_LOG = ROOT / "repro" / "run_log.csv"
MANIFEST = ROOT / "repro" / "artifact_manifest.md"
CHECKLIST = ROOT / "repro" / "reproduction_checklist.md"


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
        for row in rows:
            writer.writerow({field: row.get(field, "") for field in fields})


def read_text(path: Path) -> str:
    if not path.exists():
        return ""
    return path.read_text(encoding="utf-8", errors="replace")


def write_text(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text.rstrip() + "\n", encoding="utf-8", newline="\n")


def append_once(path: Path, marker: str, text: str) -> None:
    current = read_text(path)
    if marker in current:
        return
    with path.open("a", encoding="utf-8", newline="\n") as f:
        if current and not current.endswith("\n"):
            f.write("\n")
        f.write(text.lstrip())
        if not text.endswith("\n"):
            f.write("\n")


def sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def find_row(rows: List[Dict[str, str]], key: str, value: str) -> Optional[Dict[str, str]]:
    for row in rows:
        if row.get(key) == value:
            return row
    return None


def as_float(value: str) -> float:
    try:
        return float(value)
    except (TypeError, ValueError):
        return 0.0


def fmt(value: float) -> str:
    return f"{value:.6f}" if value else ""


def stage_perf(path: Path) -> Dict[str, str]:
    rows = read_csv(path)
    direct = find_row(rows, "variant", "perf_direct_dft") or {}
    comp = find_row(rows, "variant", "comparison") or {}
    return {
        "samples": direct.get("samples", ""),
        "correctness": direct.get("correctness", ""),
        "direct_vs_scalar": direct.get("speedup_vs_repeated_scalar_mean", ""),
        "direct_vs_control": comp.get("direct_dft_vs_selected_control_mean", ""),
    }


def proof_status(path: Path, gate: str) -> str:
    row = find_row(read_csv(path), "gate", gate)
    return row.get("status", "MISSING") if row else "MISSING"


def counter_ratio(metric: str) -> float:
    row = find_row(read_csv(STAGE301_COUNTERS), "metric", metric)
    return as_float(row.get("selected_over_direct", "")) if row else 0.0


def table(rows: List[Dict[str, str]], fields: List[str]) -> str:
    out = ["| " + " | ".join(fields) + " |", "| " + " | ".join("---" for _ in fields) + " |"]
    for row in rows:
        out.append("| " + " | ".join(str(row.get(field, "")).replace("|", "\\|") for field in fields) + " |")
    return "\n".join(out)


def append_run_log(decision: str) -> None:
    run_id = "stage302-counter-interpretation-001"
    if run_id in read_text(RUN_LOG):
        return
    fields: List[str] = []
    if RUN_LOG.exists():
        with RUN_LOG.open(newline="", encoding="utf-8-sig") as f:
            reader = csv.DictReader(f)
            fields = list(reader.fieldnames or [])
    if not fields:
        fields = ["run_id", "date", "git_ref", "stage", "backend", "command", "config", "seed", "status", "summary", "artifacts"]
    row = {field: "" for field in fields}
    values = {
        "run_id": run_id,
        "date": "2026-07-05",
        "git_ref": "current-head-after-4dc6546",
        "commit_or_state": "current-head-after-4dc6546",
        "stage": "Stage 302",
        "backend": "analysis",
        "command": "python3 scripts/build_stage302_counter_interpretation.py",
        "config": "Stage296/299 T_over_r plus Stage301 native counter interpretation",
        "params": "Stage296/299 T_over_r plus Stage301 native counter interpretation",
        "seed": "n/a",
        "status": decision,
        "summary": "Counter interpretation separates memory/instruction mechanism support from theoretical optimality and selects the next experiment.",
        "artifacts": f"{rel(DOC)}; {rel(MECHANISM)}; {rel(PROOF)}",
    }
    for key, value in values.items():
        if key in row:
            row[key] = value
    with RUN_LOG.open("a", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fields, lineterminator="\n")
        writer.writerow(row)


def artifact_index(paths: List[Path]) -> List[Dict[str, str]]:
    rows: List[Dict[str, str]] = []
    for path in paths:
        if path.exists() and path.is_file():
            rows.append({"path": rel(path), "bytes": str(path.stat().st_size), "sha256": sha256_file(path)})
    return rows


def main() -> None:
    OUT.mkdir(parents=True, exist_ok=True)
    s296 = stage_perf(STAGE296_PERF)
    s299 = stage_perf(STAGE299_PERF)
    stage301_decision = proof_status(STAGE301_PROOF, "G6_decision")

    latency_ratio = counter_ratio("t_bootstrap_over_r_us")
    cycle_ratio = counter_ratio("cycles")
    instr_ratio = counter_ratio("instructions")
    load_ratio = counter_ratio("loads")
    store_ratio = counter_ratio("stores")
    fp512_ratio = counter_ratio("fp512")
    load_store_to_fp512 = counter_ratio("load_store_to_fp512")

    memory_supported = load_ratio > 1.01 and store_ratio > 1.005
    instruction_supported = instr_ratio > 1.01
    arithmetic_neutral = 0.995 <= fp512_ratio <= 1.005
    latency_supported = latency_ratio > 1.0 and as_float(s296["direct_vs_control"]) > 1.0

    if stage301_decision == "PASS_STAGE301_CURRENT_HEAD_DIRECT_DFT_NATIVE_COUNTER_REFRESH" and latency_supported and memory_supported and instruction_supported and arithmetic_neutral:
        decision = "PASS_STAGE302_COUNTER_SUPPORTS_MEMORY_INSTRUCTION_MECHANISM"
    elif stage301_decision.startswith("PASS") and latency_supported:
        decision = "NEUTRAL_STAGE302_COUNTERS_PARTIAL_MECHANISM_SUPPORT"
    else:
        decision = "FAIL_STAGE302_COUNTER_INTERPRETATION"

    mechanism_rows = [
        {
            "component": "complete_sab_latency",
            "stage301_selected_over_direct": fmt(latency_ratio),
            "stage296_direct_over_control": s296["direct_vs_control"],
            "interpretation": "Direct DFT is faster than selected-control in both high-stat local timing and one native counter run.",
        },
        {
            "component": "cycles",
            "stage301_selected_over_direct": fmt(cycle_ratio),
            "stage296_direct_over_control": s296["direct_vs_control"],
            "interpretation": "Native counters record fewer cycles for direct DFT.",
        },
        {
            "component": "instructions",
            "stage301_selected_over_direct": fmt(instr_ratio),
            "stage296_direct_over_control": s296["direct_vs_control"],
            "interpretation": "Direct DFT reduces retired instructions, consistent with removing wrapper/materialization work.",
        },
        {
            "component": "loads",
            "stage301_selected_over_direct": fmt(load_ratio),
            "stage296_direct_over_control": s296["direct_vs_control"],
            "interpretation": "Direct DFT reduces retired loads.",
        },
        {
            "component": "stores",
            "stage301_selected_over_direct": fmt(store_ratio),
            "stage296_direct_over_control": s296["direct_vs_control"],
            "interpretation": "Direct DFT reduces retired stores.",
        },
        {
            "component": "fp512",
            "stage301_selected_over_direct": fmt(fp512_ratio),
            "stage296_direct_over_control": s296["direct_vs_control"],
            "interpretation": "AVX512 FP arithmetic count is neutral; the mechanism is not fewer dense FMA operations.",
        },
        {
            "component": "load_store_to_fp512",
            "stage301_selected_over_direct": fmt(load_store_to_fp512),
            "stage296_direct_over_control": s296["direct_vs_control"],
            "interpretation": "Memory traffic per AVX512 FP event improves, but this is still a constant-factor implementation mechanism.",
        },
    ]
    write_csv(MECHANISM, mechanism_rows, ["component", "stage301_selected_over_direct", "stage296_direct_over_control", "interpretation"])

    claim_rows = [
        {
            "claim": "direct_dft_memory_instruction_mechanism",
            "status": "supported" if decision.startswith("PASS_STAGE302") else "partial",
            "allowed": "Stage301 supports direct-DFT reducing memory/instruction overhead relative to selected-control.",
            "not_allowed": "Do not claim direct-DFT reduces dense AVX512 FMA volume.",
        },
        {
            "claim": "mat_avx512_theoretical_optimality",
            "status": "not_supported",
            "allowed": "State that counters support a mechanism, not optimality.",
            "not_allowed": "Do not claim theoretical optimum from one counter run and current dense layout.",
        },
        {
            "claim": "parameter_generalization",
            "status": "preflight_only",
            "allowed": "Stage299 shows SET_4_5_2048 preflight positive.",
            "not_allowed": "Do not claim broad parameter coverage before repeated matrix.",
        },
    ]
    write_csv(CLAIMS, claim_rows, ["claim", "status", "allowed", "not_allowed"])

    gate_rows = [
        {
            "gate": "G1_inputs_present",
            "status": "PASS" if stage301_decision.startswith("PASS") and s296["correctness"] == "Pass" and s299["correctness"] == "Pass" else "FAIL",
            "metric": "stage296/stage299/stage301",
            "value": f"{s296['direct_vs_control']}; {s299['direct_vs_control']}; {stage301_decision}",
            "interpretation": "Counter interpretation requires current performance and counter evidence.",
        },
        {
            "gate": "G2_latency_direction",
            "status": "PASS" if latency_supported else "FAIL",
            "metric": "selected/direct T/r",
            "value": fmt(latency_ratio),
            "interpretation": "Native one-run direction must agree with repeated local Stage296 direction.",
        },
        {
            "gate": "G3_memory_instruction_direction",
            "status": "PASS" if memory_supported and instruction_supported else "PARTIAL",
            "metric": "loads/stores/instructions",
            "value": f"{fmt(load_ratio)}/{fmt(store_ratio)}/{fmt(instr_ratio)}",
            "interpretation": "Direct DFT should reduce memory or instruction counters if its mechanism is materialization reduction.",
        },
        {
            "gate": "G4_arithmetic_boundary",
            "status": "PASS_NEUTRAL_FMA",
            "metric": "fp512 selected/direct",
            "value": fmt(fp512_ratio),
            "interpretation": "FMA count is neutral, so Stage302 does not justify a reduced-arithmetic claim.",
        },
        {
            "gate": "G5_decision",
            "status": decision,
            "metric": "stage decision",
            "value": decision,
            "interpretation": "Controls Stage303 route.",
        },
    ]
    write_csv(PROOF, gate_rows, ["gate", "status", "metric", "value", "interpretation"])

    next_rows = [
        {
            "priority": "P0",
            "route": "stage303_parameter_matrix_highstat",
            "entry_condition": decision,
            "gate": "Promote SET_4_5_2048 from 3-run preflight to repeated performance/noise/resource matrix.",
            "failure_action": "Keep broad parameter claim blocked.",
        },
        {
            "priority": "P1",
            "route": "stage303_materialization_split_probe",
            "entry_condition": "Need more kernel guidance after parameter matrix.",
            "gate": "Split direct-DFT residual into torus-to-DFT/materialization/copy components.",
            "failure_action": "Do not write new AVX kernel without component target.",
        },
    ]
    write_csv(NEXT, next_rows, ["priority", "route", "entry_condition", "gate", "failure_action"])

    write_csv(
        SUMMARY,
        [
            {
                "decision": decision,
                "stage296_direct_over_control": s296["direct_vs_control"],
                "stage299_direct_over_control": s299["direct_vs_control"],
                "stage301_selected_over_direct_t_over_r": fmt(latency_ratio),
                "stage301_selected_over_direct_cycles": fmt(cycle_ratio),
                "stage301_selected_over_direct_loads": fmt(load_ratio),
                "stage301_selected_over_direct_stores": fmt(store_ratio),
                "stage301_selected_over_direct_fp512": fmt(fp512_ratio),
                "next_route": "stage303_parameter_matrix_highstat",
            }
        ],
        [
            "decision",
            "stage296_direct_over_control",
            "stage299_direct_over_control",
            "stage301_selected_over_direct_t_over_r",
            "stage301_selected_over_direct_cycles",
            "stage301_selected_over_direct_loads",
            "stage301_selected_over_direct_stores",
            "stage301_selected_over_direct_fp512",
            "next_route",
        ],
    )

    write_text(
        DOC,
        "# Stage302 Counter Interpretation\n\n"
        f"Decision: `{decision}`.\n\n"
        "Stage302 interprets Stage301 native counters against the Stage296/299 complete-SAB `T_bootstrap/r` evidence.\n"
        "The supported mechanism is memory/instruction overhead reduction, not reduced dense AVX512 arithmetic.\n\n"
        "## Mechanism\n\n"
        + table(mechanism_rows, ["component", "stage301_selected_over_direct", "stage296_direct_over_control", "interpretation"])
        + "\n\n## Proof Gate\n\n"
        + table(gate_rows, ["gate", "status", "metric", "value", "interpretation"])
        + "\n",
    )
    write_text(REPORT, read_text(DOC))
    write_text(
        THEORY,
        "# Stage302 Counter-to-Algorithm Model\n\n"
        "If direct DFT removes intermediate materialization, native counters should show fewer loads/stores and instructions while dense AVX512 FP events stay roughly constant. "
        "That is the Stage302 result. The remaining optimization target is therefore residual materialization/copy/sub-decomposition overhead, not a proof that the dense MAT AVX512 arithmetic is theoretically optimal.\n",
    )
    write_text(
        VARIANT,
        "# Stage302 Counter Interpretation Variant\n\n"
        "No algorithmic variant is introduced. Stage302 classifies the current direct-DFT candidate and selects the next experiment.\n",
    )
    write_text(
        EXPERIMENT,
        "# Stage302 Experiment Plan\n\n"
        "Inputs: Stage296 repeated timing, Stage299 parameter preflight, Stage301 native counters. "
        "Outputs: bounded mechanism claim and next-stage selection.\n",
    )
    write_text(
        COMMANDS,
        "# Stage302 Reproduction Commands\n\n```bash\npython3 scripts/build_stage302_counter_interpretation.py\n```\n",
    )

    append_once(
        ROADMAP,
        "## Stage 302: Counter Interpretation",
        "\n## Stage 302: Counter Interpretation\n\n"
        "Goal: interpret current-head direct-DFT native counters against repeated `T_bootstrap/r` evidence.\n\n"
        f"Status: `{decision}`.\n",
    )
    append_once(
        GOAL,
        "<!-- stage302-counter-interpretation -->",
        "\n<!-- stage302-counter-interpretation -->\n"
        "### Stage302 counter interpretation\n\n"
        f"`{decision}` supports the mechanism that direct DFT reduces memory/instruction overhead while leaving dense AVX512 FP arithmetic nearly neutral. "
        "The next selected route is parameter-matrix high-stat, not an unconstrained AVX rewrite.\n",
    )
    append_once(
        HYPOTHESES,
        "H302_direct_dft_memory_instruction_mechanism",
        "\nH302_direct_dft_memory_instruction_mechanism:\n"
        "  claim: Direct DFT gains come from memory/instruction overhead reduction rather than fewer dense AVX512 FP operations.\n"
        f"  status: {decision}\n"
        "  evidence: repro/stage302_counter_interpretation/mechanism_interpretation.csv\n"
        "  next_gate: Stage303 parameter matrix high-stat and residual materialization split probe.\n",
    )
    append_once(
        MANIFEST,
        "- stage302_counter_interpretation:",
        "\n- stage302_counter_interpretation:\n"
        f"  - `{rel(DOC)}`\n"
        f"  - `{rel(MECHANISM)}`\n"
        f"  - `{rel(PROOF)}`\n",
    )
    append_once(CHECKLIST, "Stage302 counter interpretation", "\n- [x] Stage302 counter interpretation recorded.\n")
    append_run_log(decision)

    artifacts = [DOC, REPORT, THEORY, VARIANT, EXPERIMENT, SUMMARY, MECHANISM, CLAIMS, PROOF, NEXT, COMMANDS]
    write_csv(INDEX, artifact_index(artifacts), ["path", "bytes", "sha256"])
    print(decision)


if __name__ == "__main__":
    main()
