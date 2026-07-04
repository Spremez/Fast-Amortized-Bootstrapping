#!/usr/bin/env python3
"""Build Stage304 parameter claim matrix from high-stat and counter evidence."""

from __future__ import annotations

import csv
import hashlib
from pathlib import Path
from typing import Dict, Iterable, List, Optional


ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "repro" / "stage304_parameter_claim_matrix"
DOC = ROOT / "docs" / "stage304_parameter_claim_matrix.md"
THEORY = ROOT / "theory_checks" / "stage304_parameter_claim_model.md"
VARIANT = ROOT / "algorithm_variants" / "mat_rlwe_sab_stage304_parameter_claim_matrix.md"
EXPERIMENT = ROOT / "experiments" / "stage304_parameter_claim_matrix_plan.md"

STAGE296_PERF = ROOT / "repro" / "stage296_direct_dft_highstat" / "perf_summary.csv"
STAGE296_NOISE = ROOT / "repro" / "stage296_direct_dft_highstat" / "noise_summary.csv"
STAGE303_PERF = ROOT / "repro" / "stage303_param_matrix_highstat" / "perf_summary.csv"
STAGE303_NOISE = ROOT / "repro" / "stage303_param_matrix_highstat" / "noise_summary.csv"
STAGE301_COUNTER = ROOT / "repro" / "stage301_current_head_direct_dft_native_counter" / "counter_comparison.csv"
STAGE302_SUMMARY = ROOT / "repro" / "stage302_counter_interpretation" / "summary.csv"

SUMMARY = OUT / "summary.csv"
PARAM_MATRIX = OUT / "parameter_evidence_matrix.csv"
MECHANISM = OUT / "mechanism_bridge.csv"
CLAIMS = OUT / "claim_boundary.csv"
PROOF = OUT / "proof_gate.csv"
NEXT = OUT / "next_stage_queue.csv"
COMMANDS = OUT / "reproduction_commands.md"
REPORT = OUT / "stage304_report.md"
INDEX = OUT / "artifact_index.csv"

GOAL = ROOT / "docs" / "current_codex_goal_sab_completion.md"
ROADMAP = ROOT / "docs" / "roadmap_stage19_plus.md"
HYPOTHESES = ROOT / "hypotheses" / "hypothesis_register.yaml"
RUN_LOG = ROOT / "repro" / "run_log.csv"
MANIFEST = ROOT / "repro" / "artifact_manifest.md"
CHECKLIST = ROOT / "repro" / "reproduction_checklist.md"


def rel(path: Path) -> str:
    return path.relative_to(ROOT).as_posix()


def read_text(path: Path) -> str:
    if not path.exists():
        return ""
    return path.read_text(encoding="utf-8", errors="replace")


def write_text(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text.rstrip() + "\n", encoding="utf-8", newline="\n")


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


def sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def perf_record(param: str, perf_path: Path, noise_path: Path) -> Dict[str, str]:
    perf = read_csv(perf_path)
    direct = find_row(perf, "variant", "perf_direct_dft") or {}
    comp = find_row(perf, "variant", "comparison") or {}
    noise = (read_csv(noise_path) or [{}])[0]
    return {
        "param": param,
        "samples": direct.get("samples", ""),
        "correctness": direct.get("correctness", ""),
        "direct_t_over_r_mean_us": direct.get("t_bootstrap_over_r_mean_us", ""),
        "direct_t_over_r_ci95_low_us": direct.get("t_bootstrap_over_r_ci95_low_us", ""),
        "direct_t_over_r_ci95_high_us": direct.get("t_bootstrap_over_r_ci95_high_us", ""),
        "direct_over_repeated_scalar": direct.get("speedup_vs_repeated_scalar_mean", ""),
        "direct_over_selected_control": comp.get("direct_dft_vs_selected_control_mean", ""),
        "ci_separated": comp.get("direct_dft_ci_separated_from_control", ""),
        "noise_trials": noise.get("trials", ""),
        "pair_failures": noise.get("pair_failures", ""),
        "noise_gate": noise.get("overall_gate", ""),
        "evidence": f"{rel(perf_path)}; {rel(noise_path)}",
    }


def counter_metric(metric: str) -> str:
    row = find_row(read_csv(STAGE301_COUNTER), "metric", metric)
    return row.get("selected_over_direct", "") if row else ""


def table(rows: List[Dict[str, str]], fields: List[str]) -> str:
    out = ["| " + " | ".join(fields) + " |", "| " + " | ".join("---" for _ in fields) + " |"]
    for row in rows:
        out.append("| " + " | ".join(str(row.get(field, "")).replace("|", "\\|") for field in fields) + " |")
    return "\n".join(out)


def append_run_log(decision: str) -> None:
    run_id = "stage304-parameter-claim-matrix-001"
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
        "git_ref": "current-head-after-9f8b041",
        "commit_or_state": "current-head-after-9f8b041",
        "stage": "Stage 304",
        "backend": "analysis",
        "command": "python3 scripts/build_stage304_parameter_claim_matrix.py",
        "config": "Stage296+Stage303 parameter matrix with Stage301/302 mechanism evidence",
        "params": "Stage296+Stage303 parameter matrix with Stage301/302 mechanism evidence",
        "seed": "n/a",
        "status": decision,
        "summary": "Two tested 2048-out parameter sets support scoped local direct-DFT improvement; broad parameter and optimality claims remain blocked.",
        "artifacts": f"{rel(DOC)}; {rel(PARAM_MATRIX)}; {rel(CLAIMS)}; {rel(PROOF)}",
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
    param_rows = [
        perf_record("SET_2_3_2048", STAGE296_PERF, STAGE296_NOISE),
        perf_record("SET_4_5_2048", STAGE303_PERF, STAGE303_NOISE),
    ]
    write_csv(
        PARAM_MATRIX,
        param_rows,
        [
            "param",
            "samples",
            "correctness",
            "direct_t_over_r_mean_us",
            "direct_t_over_r_ci95_low_us",
            "direct_t_over_r_ci95_high_us",
            "direct_over_repeated_scalar",
            "direct_over_selected_control",
            "ci_separated",
            "noise_trials",
            "pair_failures",
            "noise_gate",
            "evidence",
        ],
    )

    mechanism_rows = [
        {"metric": "native_t_over_r_selected_over_direct", "value": counter_metric("t_bootstrap_over_r_us"), "interpretation": "Stage301 one-run native latency direction agrees with local high-stat direction."},
        {"metric": "cycles_selected_over_direct", "value": counter_metric("cycles"), "interpretation": "Direct DFT records fewer cycles than selected-control in Stage301."},
        {"metric": "instructions_selected_over_direct", "value": counter_metric("instructions"), "interpretation": "Direct DFT records fewer instructions, supporting materialization-wrapper removal."},
        {"metric": "loads_selected_over_direct", "value": counter_metric("loads"), "interpretation": "Direct DFT records fewer loads."},
        {"metric": "stores_selected_over_direct", "value": counter_metric("stores"), "interpretation": "Direct DFT records fewer stores."},
        {"metric": "fp512_selected_over_direct", "value": counter_metric("fp512"), "interpretation": "AVX512 FP arithmetic is neutral; this is not an arithmetic-volume reduction claim."},
        {"metric": "stage302_decision", "value": (read_csv(STAGE302_SUMMARY) or [{}])[0].get("decision", ""), "interpretation": "Stage302 classifies the mechanism boundary."},
    ]
    write_csv(MECHANISM, mechanism_rows, ["metric", "value", "interpretation"])

    param_pass = all(
        row["correctness"] == "Pass"
        and int(row["samples"] or 0) >= 10
        and as_float(row["direct_over_selected_control"]) > 1.02
        and row["pair_failures"] == "0"
        and int(row["noise_trials"] or 0) >= 10
        for row in param_rows
    )
    counter_pass = as_float(counter_metric("cycles")) > 1.0 and as_float(counter_metric("loads")) > 1.0
    decision = (
        "PASS_STAGE304_TWO_PARAMETER_LOCAL_GENERALIZATION_WITH_COUNTER_MECHANISM"
        if param_pass and counter_pass
        else "FAIL_STAGE304_PARAMETER_CLAIM_MATRIX"
    )

    proof_rows = [
        {"gate": "G1_two_parameter_highstat", "status": "PASS" if param_pass else "FAIL", "metric": "params", "value": "SET_2_3_2048;SET_4_5_2048", "interpretation": "Both tested parameters need 10-run/10-trial local complete-SAB evidence."},
        {"gate": "G2_counter_mechanism", "status": "PASS" if counter_pass else "FAIL", "metric": "cycles/loads", "value": f"{counter_metric('cycles')}/{counter_metric('loads')}", "interpretation": "Native counters must support the memory/instruction mechanism direction."},
        {"gate": "G3_claim_boundary", "status": "PASS_SCOPED_ONLY", "metric": "scope", "value": "two local binary include-zero 2048-output parameter sets", "interpretation": "This is not universal parameter coverage or theoretical optimality."},
        {"gate": "G4_decision", "status": decision, "metric": "stage decision", "value": decision, "interpretation": "Controls Stage305 route."},
    ]
    write_csv(PROOF, proof_rows, ["gate", "status", "metric", "value", "interpretation"])

    claim_rows = [
        {
            "claim": "two_parameter_local_complete_sab_speedup",
            "status": "supported" if decision.startswith("PASS") else "not_supported",
            "allowed": "For SET_2_3_2048 and SET_4_5_2048, direct DFT improves complete-SAB T_bootstrap/r over selected-control under the recorded local protocol.",
            "not_allowed": "Do not claim all parameter sets, all branches, or single-output latency improvement.",
        },
        {
            "claim": "mechanism",
            "status": "counter_supported",
            "allowed": "Stage301/302 support memory/instruction overhead reduction as the mechanism.",
            "not_allowed": "Do not claim fewer dense AVX512 FMA operations or theoretical optimality.",
        },
        {
            "claim": "paper_grade_generalization",
            "status": "not_yet",
            "allowed": "Use as strong engineering evidence for two tested parameters.",
            "not_allowed": "Do not write broad novelty or theorem-level claims without literature/proof/branch coverage.",
        },
    ]
    write_csv(CLAIMS, claim_rows, ["claim", "status", "allowed", "not_allowed"])

    next_rows = [
        {"priority": "P0", "route": "stage305_materialization_split_probe", "entry_condition": decision, "gate": "Measure residual direct-DFT materialization/copy/sub-decomposition split before new AVX work.", "failure_action": "Keep direct-DFT as promoted engineering path without new kernel rewrite."},
        {"priority": "P1", "route": "stage305_branch_coverage", "entry_condition": "paper claim needs more branch coverage", "gate": "Repeat include-zero/ternary or other supported branches if claiming beyond binary include-zero.", "failure_action": "Scope final claim to tested branch."},
    ]
    write_csv(NEXT, next_rows, ["priority", "route", "entry_condition", "gate", "failure_action"])

    write_csv(
        SUMMARY,
        [
            {
                "decision": decision,
                "tested_parameters": "SET_2_3_2048;SET_4_5_2048",
                "set_2_3_direct_over_control": param_rows[0]["direct_over_selected_control"],
                "set_4_5_direct_over_control": param_rows[1]["direct_over_selected_control"],
                "stage301_cycles_selected_over_direct": counter_metric("cycles"),
                "stage301_loads_selected_over_direct": counter_metric("loads"),
                "claim_scope": "two local binary include-zero 2048-output parameters",
                "next_route": "stage305_materialization_split_probe",
            }
        ],
        [
            "decision",
            "tested_parameters",
            "set_2_3_direct_over_control",
            "set_4_5_direct_over_control",
            "stage301_cycles_selected_over_direct",
            "stage301_loads_selected_over_direct",
            "claim_scope",
            "next_route",
        ],
    )

    report = (
        "# Stage304 Parameter Claim Matrix\n\n"
        f"Decision: `{decision}`.\n\n"
        "Stage304 combines the two high-stat local complete-SAB campaigns with the current-head native counter mechanism evidence.\n\n"
        "## Parameter Evidence\n\n"
        + table(param_rows, ["param", "samples", "direct_over_selected_control", "direct_over_repeated_scalar", "noise_trials", "pair_failures", "ci_separated"])
        + "\n\n## Mechanism Bridge\n\n"
        + table(mechanism_rows, ["metric", "value", "interpretation"])
        + "\n\n## Proof Gate\n\n"
        + table(proof_rows, ["gate", "status", "metric", "value", "interpretation"])
        + "\n"
    )
    write_text(DOC, report)
    write_text(REPORT, report)
    write_text(THEORY, "# Stage304 Parameter Claim Model\n\nTwo positive parameter rows support a scoped engineering generalization over the tested 2048-output binary include-zero parameter sets. They do not prove universal parameter coverage, branch coverage, or MAT-AVX512 theoretical optimality.\n")
    write_text(VARIANT, "# Stage304 Parameter Claim Matrix\n\nNo new algorithmic variant is introduced. Stage304 classifies evidence for the existing direct-DFT PVW/MAT-SAB path.\n")
    write_text(EXPERIMENT, "# Stage304 Experiment Plan\n\nRead Stage296, Stage303, Stage301 and Stage302 artifacts; emit scoped claim boundaries and next-stage selection.\n")
    write_text(COMMANDS, "# Stage304 Reproduction Commands\n\n```bash\npython3 scripts/build_stage304_parameter_claim_matrix.py\n```\n")

    append_once(
        ROADMAP,
        "## Stage 304: Parameter Claim Matrix",
        "\n## Stage 304: Parameter Claim Matrix\n\nGoal: merge two-parameter high-stat evidence with native counter mechanism evidence.\n\n"
        f"Status: `{decision}`.\n",
    )
    append_once(
        GOAL,
        "<!-- stage304-parameter-claim-matrix -->",
        "\n<!-- stage304-parameter-claim-matrix -->\n### Stage304 parameter claim matrix\n\n"
        f"`{decision}` supports a scoped two-parameter local engineering claim for direct-DFT PVW/MAT-SAB. "
        "The next route is residual materialization split before any new AVX rewrite.\n",
    )
    append_once(
        HYPOTHESES,
        "H304_two_parameter_local_generalization:",
        "\nH304_two_parameter_local_generalization:\n"
        f"  status: {decision}\n"
        "  primary_metric: complete_sab_T_bootstrap_over_r\n"
        "  evidence: repro/stage304_parameter_claim_matrix/parameter_evidence_matrix.csv\n"
        "  claim_scope: two local binary include-zero 2048-output parameter sets\n",
    )
    append_once(MANIFEST, "- stage304_parameter_claim_matrix:", "\n- stage304_parameter_claim_matrix:\n  - `docs/stage304_parameter_claim_matrix.md`\n  - `repro/stage304_parameter_claim_matrix/`\n")
    append_once(CHECKLIST, "<!-- stage304-parameter-claim-matrix-checklist -->", f"\n<!-- stage304-parameter-claim-matrix-checklist -->\n- [x] Stage304 records `{decision}` and claim boundaries.\n")
    append_run_log(decision)

    artifacts = [DOC, REPORT, THEORY, VARIANT, EXPERIMENT, SUMMARY, PARAM_MATRIX, MECHANISM, CLAIMS, PROOF, NEXT, COMMANDS]
    write_csv(INDEX, artifact_index(artifacts), ["path", "bytes", "sha256"])
    print(decision)


if __name__ == "__main__":
    main()
