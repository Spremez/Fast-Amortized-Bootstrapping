#!/usr/bin/env python3
"""Build Stage305 selected/direct materialization split probe artifacts."""

from __future__ import annotations

import csv
import hashlib
import re
from pathlib import Path
from typing import Dict, Iterable, List


ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "repro" / "stage305_materialization_split_probe"
RAW = OUT / "raw"
DOC = ROOT / "docs" / "stage305_materialization_split_probe.md"
THEORY = ROOT / "theory_checks" / "stage305_materialization_split_model.md"
VARIANT = ROOT / "algorithm_variants" / "mat_rlwe_sab_stage305_materialization_split_probe.md"
EXPERIMENT = ROOT / "experiments" / "stage305_materialization_split_probe_plan.md"

SUMMARY = OUT / "split_summary.csv"
COMPONENTS = OUT / "split_components.csv"
COMPARISON = OUT / "split_comparison.csv"
CLAIMS = OUT / "claim_boundary.csv"
PROOF = OUT / "proof_gate.csv"
NEXT = OUT / "next_stage_queue.csv"
COMMANDS = OUT / "reproduction_commands.md"
REPORT = OUT / "stage305_report.md"
INDEX = OUT / "artifact_index.csv"

GOAL = ROOT / "docs" / "current_codex_goal_sab_completion.md"
ROADMAP = ROOT / "docs" / "roadmap_stage19_plus.md"
HYPOTHESES = ROOT / "hypotheses" / "hypothesis_register.yaml"
RUN_LOG = ROOT / "repro" / "run_log.csv"
MANIFEST = ROOT / "repro" / "artifact_manifest.md"
CHECKLIST = ROOT / "repro" / "reproduction_checklist.md"

CORRECT_RE = re.compile(
    r"SAB_PVW_NONBINARY_BENCH correctness target_full mode=(?P<mode>\w+) "
    r"r=(?P<r>\d+) h=(?P<h>\d+) r_prec=(?P<r_prec>\d+): (?P<status>\w+)"
)
BENCH_RE = re.compile(
    r"SAB_PVW_NONBINARY_BENCH summary target_full mode=(?P<mode>\w+) "
    r"r=(?P<r>\d+) reps=(?P<reps>\d+) "
    r"pvw_avg_us=(?P<pvw_avg_us>[0-9.]+).*?"
    r"scalar_repeated_avg_us=(?P<scalar_repeated_avg_us>[0-9.]+).*?"
    r"speedup_vs_scalar_repeated=(?P<speedup>[0-9.]+)x.*?"
    r"t_bootstrap_over_r_pvw_us=(?P<t_pvw>[0-9.]+) "
    r"t_bootstrap_over_r_scalar_us=(?P<t_scalar>[0-9.]+)"
)
BODY_RE = re.compile(r"SAB_PVW_BODY_PROFILE sample (?P<body>.+)")
SPLIT_RE = re.compile(r"MAT_TRGSW_SPLIT_PROFILE sample (?P<split>.+)")
KV_RE = re.compile(r"([A-Za-z0-9_]+)=([^ ]+)")


def rel(path: Path) -> str:
    return path.relative_to(ROOT).as_posix()


def read_text(path: Path) -> str:
    if not path.exists():
        return ""
    return path.read_text(encoding="utf-8", errors="replace").replace("\x00", "").replace("\r\n", "\n").replace("\r", "\n")


def write_text(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text.rstrip() + "\n", encoding="utf-8", newline="\n")


def read_csv(path: Path) -> List[Dict[str, str]]:
    if not path.exists():
        return []
    with path.open(newline="", encoding="utf-8-sig") as f:
        return list(csv.DictReader(f))


def write_csv(path: Path, rows: Iterable[Dict[str, object]], fields: List[str]) -> None:
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


def fnum(value: object) -> float:
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


def parse_kv_all(regex: re.Pattern[str], text: str, group: str) -> List[Dict[str, str]]:
    return [dict(KV_RE.findall(match.group(group))) for match in regex.finditer(text)]


def parse_variant(variant: str) -> tuple[Dict[str, object], List[Dict[str, object]]]:
    log = RAW / variant / "run.log"
    text = read_text(log)
    correct = CORRECT_RE.search(text)
    bench = BENCH_RE.search(text)
    body_rows = parse_kv_all(BODY_RE, text, "body")
    split_rows = parse_kv_all(SPLIT_RE, text, "split")
    split = split_rows[-1] if split_rows else {}
    body_mat_ep_us = sum(fnum(row.get("mat_ep_us")) for row in body_rows)
    body_full_us = sum(fnum(row.get("full_us")) for row in body_rows)
    body_mat_ep_calls = int(sum(fnum(row.get("mat_ep_calls")) for row in body_rows))
    normal_calls = int(fnum(split.get("normal_calls")))
    sub_calls = int(fnum(split.get("sub_calls")))
    total_calls = normal_calls + sub_calls
    rows_sum = int(fnum(split.get("rows_sum")))
    expected_rows = total_calls * 5
    split_total = fnum(split.get("total_us"))
    decompose = fnum(split.get("decompose_us"))
    dft = fnum(split.get("dft_us"))
    dense = fnum(split.get("dense_us"))
    summary = {
        "variant": variant,
        "correctness": correct.group("status") if correct else "missing",
        "mode": correct.group("mode") if correct else "",
        "r": correct.group("r") if correct else "",
        "h": correct.group("h") if correct else "",
        "r_prec": correct.group("r_prec") if correct else "",
        "reps": bench.group("reps") if bench else "",
        "t_bootstrap_over_r_pvw_us": bench.group("t_pvw") if bench else "",
        "speedup_vs_scalar": bench.group("speedup") if bench else "",
        "body_profile_rows": len(body_rows),
        "body_full_us_sum": f"{body_full_us:.3f}",
        "body_mat_ep_calls": body_mat_ep_calls,
        "body_mat_ep_us_sum": f"{body_mat_ep_us:.3f}",
        "split_normal_calls": normal_calls,
        "split_sub_calls": sub_calls,
        "split_total_calls": total_calls,
        "split_rows_sum": rows_sum,
        "split_expected_rows": expected_rows,
        "split_total_us": f"{split_total:.3f}",
        "split_vs_body_mat_ep_ratio": f"{split_total / body_mat_ep_us:.6f}" if body_mat_ep_us else "",
        "source_log": rel(log),
    }
    components = []
    for name, value in [("decompose", decompose), ("torus_to_dft", dft), ("dense_from_dec", dense)]:
        components.append({
            "variant": variant,
            "component": name,
            "us": f"{value:.3f}",
            "share_of_split_total": f"{value / split_total:.6f}" if split_total else "",
            "share_of_body_mat_ep": f"{value / body_mat_ep_us:.6f}" if body_mat_ep_us else "",
            "calls": total_calls,
            "avg_us_per_call": f"{value / total_calls:.6f}" if total_calls else "",
        })
    return summary, components


def ratio(control: float, direct: float) -> str:
    return f"{control / direct:.6f}" if direct else ""


def component_value(rows: List[Dict[str, object]], variant: str, component: str, field: str = "us") -> float:
    for row in rows:
        if row.get("variant") == variant and row.get("component") == component:
            return fnum(row.get(field))
    return 0.0


def table(rows: List[Dict[str, object]], fields: List[str]) -> str:
    out = ["| " + " | ".join(fields) + " |", "| " + " | ".join("---" for _ in fields) + " |"]
    for row in rows:
        out.append("| " + " | ".join(str(row.get(field, "")).replace("|", "\\|") for field in fields) + " |")
    return "\n".join(out)


def append_run_log(decision: str) -> None:
    run_id = "stage305-materialization-split-probe-001"
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
        "git_ref": "current-head-after-bd2b439",
        "commit_or_state": "current-head-after-bd2b439",
        "stage": "Stage 305",
        "backend": "spqlios_avx512-local",
        "command": "FFT_LIB=spqlios_avx512 PARAM=SET_2_3_2048 bash scripts/run_stage305_materialization_split_probe.sh",
        "config": "selected-control vs direct-DFT target split profile",
        "params": "selected-control vs direct-DFT target split profile",
        "seed": "n/a",
        "status": decision,
        "summary": "Residual split profile identifies the next component target before new AVX work.",
        "artifacts": f"{rel(DOC)}; {rel(SUMMARY)}; {rel(COMPARISON)}; {rel(PROOF)}",
    }
    for key, value in values.items():
        if key in row:
            row[key] = value
    with RUN_LOG.open("a", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fields, lineterminator="\n")
        writer.writerow(row)


def artifact_index(paths: List[Path]) -> List[Dict[str, str]]:
    rows = []
    for path in paths:
        if path.exists() and path.is_file():
            rows.append({"path": rel(path), "bytes": str(path.stat().st_size), "sha256": sha256_file(path)})
    return rows


def main() -> None:
    OUT.mkdir(parents=True, exist_ok=True)
    summaries: List[Dict[str, object]] = []
    components: List[Dict[str, object]] = []
    for variant in ["selected_control", "direct_dft"]:
        summary, component_rows = parse_variant(variant)
        summaries.append(summary)
        components.extend(component_rows)

    write_csv(SUMMARY, summaries, [
        "variant", "correctness", "mode", "r", "h", "r_prec", "reps",
        "t_bootstrap_over_r_pvw_us", "speedup_vs_scalar", "body_profile_rows",
        "body_full_us_sum", "body_mat_ep_calls", "body_mat_ep_us_sum",
        "split_normal_calls", "split_sub_calls", "split_total_calls",
        "split_rows_sum", "split_expected_rows", "split_total_us",
        "split_vs_body_mat_ep_ratio", "source_log",
    ])
    write_csv(COMPONENTS, components, ["variant", "component", "us", "share_of_split_total", "share_of_body_mat_ep", "calls", "avg_us_per_call"])

    by_variant = {row["variant"]: row for row in summaries}
    control = by_variant["selected_control"]
    direct = by_variant["direct_dft"]
    comparison = [
        {"metric": "t_bootstrap_over_r_pvw_us", "selected_control": control["t_bootstrap_over_r_pvw_us"], "direct_dft": direct["t_bootstrap_over_r_pvw_us"], "selected_over_direct": ratio(fnum(control["t_bootstrap_over_r_pvw_us"]), fnum(direct["t_bootstrap_over_r_pvw_us"]))},
        {"metric": "body_mat_ep_us_sum", "selected_control": control["body_mat_ep_us_sum"], "direct_dft": direct["body_mat_ep_us_sum"], "selected_over_direct": ratio(fnum(control["body_mat_ep_us_sum"]), fnum(direct["body_mat_ep_us_sum"]))},
        {"metric": "split_total_us", "selected_control": control["split_total_us"], "direct_dft": direct["split_total_us"], "selected_over_direct": ratio(fnum(control["split_total_us"]), fnum(direct["split_total_us"]))},
    ]
    for comp in ["decompose", "torus_to_dft", "dense_from_dec"]:
        cv = component_value(components, "selected_control", comp)
        dv = component_value(components, "direct_dft", comp)
        comparison.append({"metric": comp, "selected_control": f"{cv:.3f}", "direct_dft": f"{dv:.3f}", "selected_over_direct": ratio(cv, dv)})
    write_csv(COMPARISON, comparison, ["metric", "selected_control", "direct_dft", "selected_over_direct"])

    correctness_pass = all(row["correctness"] == "Pass" for row in summaries)
    row_match = all(int(row["split_rows_sum"]) == int(row["split_expected_rows"]) and int(row["split_total_calls"]) == int(row["body_mat_ep_calls"]) for row in summaries)
    direct_components = [row for row in components if row["variant"] == "direct_dft"]
    dominant = max(direct_components, key=lambda row: fnum(row["share_of_split_total"])) if direct_components else {}
    dominant_name = str(dominant.get("component", "missing"))
    decision = "PASS_STAGE305_MATERIALIZATION_SPLIT_PROFILE_RECORDED" if correctness_pass and row_match else "FAIL_STAGE305_MATERIALIZATION_SPLIT_PROFILE"

    proof = [
        {"gate": "G1_correctness", "status": "PASS" if correctness_pass else "FAIL", "metric": "variants", "value": "selected_control;direct_dft", "interpretation": "Both profiled variants must pass target correctness."},
        {"gate": "G2_profile_consistency", "status": "PASS" if row_match else "FAIL", "metric": "calls/rows", "value": "matched" if row_match else "mismatch", "interpretation": "Split calls and rows must match body-profile MAT EP calls."},
        {"gate": "G3_dominant_direct_component", "status": "RECORDED", "metric": "component", "value": dominant_name, "interpretation": "Dominant direct residual component selects the next micro-hypothesis."},
        {"gate": "G4_claim_boundary", "status": "PASS_PROFILE_ONLY", "metric": "scope", "value": "instrumented one-run profile", "interpretation": "Do not use instrumented latency as final speed claim."},
        {"gate": "G5_decision", "status": decision, "metric": "stage decision", "value": decision, "interpretation": "Controls Stage306 route."},
    ]
    write_csv(PROOF, proof, ["gate", "status", "metric", "value", "interpretation"])

    claims = [
        {"claim": "residual_component_target", "status": "recorded", "allowed": f"Use `{dominant_name}` as the next measured component target.", "not_allowed": "Do not start a broad AVX rewrite without a component-specific hypothesis."},
        {"claim": "performance", "status": "profile_only", "allowed": "Use Stage296/303 for performance claims.", "not_allowed": "Do not use instrumented Stage305 timings as final latency claims."},
    ]
    write_csv(CLAIMS, claims, ["claim", "status", "allowed", "not_allowed"])

    next_rows = [
        {"priority": "P0", "route": f"stage306_{dominant_name}_micro_hypothesis", "entry_condition": decision, "gate": "Define a component-specific optimization or prove it is not worth changing.", "failure_action": "Keep direct-DFT path without new AVX rewrite."},
        {"priority": "P1", "route": "stage306_branch_coverage", "entry_condition": "paper branch claim needed", "gate": "Add ternary/include-zero branch coverage if claim expands.", "failure_action": "Scope to tested include-zero branch."},
    ]
    write_csv(NEXT, next_rows, ["priority", "route", "entry_condition", "gate", "failure_action"])

    report = (
        "# Stage305 Materialization Split Probe\n\n"
        f"Decision: `{decision}`.\n\n"
        "Stage305 compares selected-control and direct-DFT with body and MAT-EP split profiling enabled. Instrumented times are used for component attribution only.\n\n"
        "## Summary\n\n" + table(summaries, ["variant", "correctness", "t_bootstrap_over_r_pvw_us", "body_mat_ep_us_sum", "split_total_us", "split_vs_body_mat_ep_ratio"]) +
        "\n\n## Components\n\n" + table(components, ["variant", "component", "us", "share_of_split_total", "avg_us_per_call"]) +
        "\n\n## Comparison\n\n" + table(comparison, ["metric", "selected_control", "direct_dft", "selected_over_direct"]) +
        "\n\n## Proof Gate\n\n" + table(proof, ["gate", "status", "metric", "value", "interpretation"]) + "\n"
    )
    write_text(DOC, report)
    write_text(REPORT, report)
    write_text(THEORY, "# Stage305 Materialization Split Model\n\nThe split profile partitions MAT external product time into sub-decomposition, torus-to-DFT materialization, and dense-from-decomposition work. Stage305 is attribution-only and selects the next component-specific hypothesis.\n")
    write_text(VARIANT, "# Stage305 Materialization Split Probe\n\nNo new algorithmic variant is introduced. The stage profiles selected-control and direct-DFT under existing flags.\n")
    write_text(EXPERIMENT, "# Stage305 Experiment Plan\n\nRun selected-control and direct-DFT once each with `SAB_PVW_BODY_PROFILE=true` and `MAT_TRGSW_SPLIT_PROFILE=true`; parse component shares and choose the next micro-hypothesis.\n")
    write_text(COMMANDS, "# Stage305 Reproduction Commands\n\n```bash\nFFT_LIB=spqlios_avx512 PARAM=SET_2_3_2048 bash scripts/run_stage305_materialization_split_probe.sh\n```\n")

    append_once(ROADMAP, "## Stage 305: Materialization Split Probe", "\n## Stage 305: Materialization Split Probe\n\nGoal: profile selected-control vs direct-DFT split components before new AVX work.\n\n" f"Status: `{decision}`.\n")
    append_once(GOAL, "<!-- stage305-materialization-split-probe -->", "\n<!-- stage305-materialization-split-probe -->\n### Stage305 materialization split probe\n\n" f"`{decision}` records split-profile attribution and selects `{dominant_name}` as the next measured component target.\n")
    append_once(HYPOTHESES, "H305_materialization_split_probe:", "\nH305_materialization_split_probe:\n" f"  status: {decision}\n  dominant_direct_component: {dominant_name}\n  evidence: repro/stage305_materialization_split_probe/split_components.csv\n")
    append_once(MANIFEST, "- stage305_materialization_split_probe:", "\n- stage305_materialization_split_probe:\n  - `docs/stage305_materialization_split_probe.md`\n  - `repro/stage305_materialization_split_probe/`\n")
    append_once(CHECKLIST, "<!-- stage305-materialization-split-probe-checklist -->", "\n<!-- stage305-materialization-split-probe-checklist -->\n" f"- [x] Stage305 records `{decision}` and a component-specific next target.\n")
    append_run_log(decision)

    artifacts = [DOC, REPORT, THEORY, VARIANT, EXPERIMENT, SUMMARY, COMPONENTS, COMPARISON, CLAIMS, PROOF, NEXT, COMMANDS, RAW / "variant_plan.csv"]
    artifacts.extend(sorted(RAW.glob("*/*.log")))
    write_csv(INDEX, artifact_index(artifacts), ["path", "bytes", "sha256"])
    print(decision)


if __name__ == "__main__":
    main()
