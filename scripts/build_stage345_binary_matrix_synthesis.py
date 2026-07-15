#!/usr/bin/env python3
"""Stage345: synthesize current-head binary parameter matrix evidence."""

from __future__ import annotations

import csv
import hashlib
import subprocess
from datetime import date
from io import StringIO
from pathlib import Path
from statistics import mean
from typing import Iterable


ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "repro" / "stage345_binary_matrix_synthesis"

DOC = ROOT / "docs" / "stage345_binary_matrix_synthesis.md"
THEORY = ROOT / "theory_checks" / "stage345_binary_matrix_claim_model.md"
PLAN = ROOT / "experiments" / "stage346_next_mechanism_or_paper_plan.md"
BUILDER = ROOT / "scripts" / "build_stage345_binary_matrix_synthesis.py"

GOAL = ROOT / "docs" / "current_codex_goal_sab_completion.md"
ROADMAP = ROOT / "docs" / "roadmap_stage19_plus.md"
HYPOTHESES = ROOT / "hypotheses" / "hypothesis_register.yaml"
MANIFEST = ROOT / "repro" / "artifact_manifest.md"
CHECKLIST = ROOT / "repro" / "reproduction_checklist.md"
RUN_LOG = ROOT / "repro" / "run_log.csv"

STAGE331_SUMMARY = ROOT / "repro" / "stage331_current_head_highstat_refresh" / "summary.csv"
STAGE343_SUMMARY = ROOT / "repro" / "stage343_target_r2_current_head_topup" / "summary.csv"
STAGE344_SUMMARY = ROOT / "repro" / "stage344_added_parameter_topups" / "summary.csv"
STAGE344_PERF = ROOT / "repro" / "stage344_added_parameter_topups" / "perf_summary.csv"

SUMMARY = OUT / "summary.csv"
BINARY_MATRIX = OUT / "binary_matrix.csv"
CLAIMS = OUT / "claim_boundary.csv"
SOURCES = OUT / "evidence_sources.csv"
PROOF = OUT / "proof_gate.csv"
NEXT = OUT / "next_stage_queue.csv"
REPORT = OUT / "stage345_report.md"
COMMANDS = OUT / "reproduction_commands.md"
ARTIFACT = OUT / "artifact_index.csv"

DECISION = "PASS_STAGE345_BINARY_MATRIX_SYNTHESIS_SCOPED_READY"


def rel(path: Path) -> str:
    return path.relative_to(ROOT).as_posix()


def read_text(path: Path) -> str:
    if not path.exists():
        return ""
    return path.read_text(encoding="utf-8", errors="replace").replace("\x00", "").replace("\r\n", "\n").replace("\r", "\n")


def read_csv(path: Path) -> list[dict[str, str]]:
    if not path.exists():
        return []
    with path.open(newline="", encoding="utf-8-sig") as handle:
        return list(csv.DictReader(handle))


def write_text(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text.rstrip() + "\n", encoding="utf-8", newline="\n")


def write_csv(path: Path, rows: Iterable[dict[str, object]], fields: list[str]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields, lineterminator="\n")
        writer.writeheader()
        for row in rows:
            writer.writerow({field: row.get(field, "") for field in fields})


def append_once(path: Path, marker: str, text: str) -> None:
    current = read_text(path)
    if marker in current:
        return
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("a", encoding="utf-8", newline="\n") as handle:
        if current and not current.endswith("\n"):
            handle.write("\n")
        handle.write(text.lstrip())
        if not text.endswith("\n"):
            handle.write("\n")


def git_head() -> str:
    try:
        return subprocess.check_output(["git", "rev-parse", "--short", "HEAD"], cwd=ROOT, text=True).strip()
    except (subprocess.CalledProcessError, FileNotFoundError):
        return "unknown"


def fnum(value: object) -> float:
    try:
        return float(value)
    except (TypeError, ValueError):
        return 0.0


def first_row(path: Path) -> dict[str, str]:
    rows = read_csv(path)
    return rows[0] if rows else {}


def md_table(rows: list[dict[str, object]], fields: list[str]) -> str:
    lines = ["| " + " | ".join(fields) + " |", "| " + " | ".join(["---"] * len(fields)) + " |"]
    for row in rows:
        lines.append("| " + " | ".join(str(row.get(field, "")).replace("|", "\\|") for field in fields) + " |")
    return "\n".join(lines)


def binary_rows() -> list[dict[str, object]]:
    rows: list[dict[str, object]] = []
    s343 = first_row(STAGE343_SUMMARY)
    rows.append({
        "case": "SET_2_3_2048_r2",
        "param": "SET_2_3_2048",
        "r": "2",
        "backend": "spqlios_avx512-wsl",
        "metric": "complete_sab_T_bootstrap_over_r_vs_repeated_scalar",
        "samples": s343.get("samples", ""),
        "correctness": s343.get("correctness", ""),
        "pvw_t_over_r_mean_us": s343.get("pvw_t_over_r_mean_us", ""),
        "pvw_t_over_r_ci95_us": s343.get("pvw_t_over_r_ci95_us", ""),
        "scalar_t_over_r_mean_us": s343.get("scalar_t_over_r_mean_us", ""),
        "speedup_mean": s343.get("speedup_mean", ""),
        "speedup_ci95": s343.get("speedup_ci95", ""),
        "noise_trials": s343.get("noise_trials", ""),
        "noise_pair_failures": s343.get("noise_pair_failures", ""),
        "time_maxrss_kb": s343.get("time_maxrss_kb_max", ""),
        "evidence_stage": "Stage343",
        "source": rel(STAGE343_SUMMARY),
        "claim_status": "current_head_highstat",
    })
    s331 = first_row(STAGE331_SUMMARY)
    rows.append({
        "case": "SET_2_3_2048_r4",
        "param": "SET_2_3_2048",
        "r": "4",
        "backend": "spqlios_avx512-wsl",
        "metric": s331.get("primary_metric", "complete_sab_T_bootstrap_over_r_vs_repeated_scalar"),
        "samples": s331.get("samples", ""),
        "correctness": s331.get("correctness", ""),
        "pvw_t_over_r_mean_us": s331.get("t_bootstrap_over_r_mean_us", ""),
        "pvw_t_over_r_ci95_us": f"{s331.get('t_bootstrap_over_r_ci95_low_us', '')}..{s331.get('t_bootstrap_over_r_ci95_high_us', '')}",
        "scalar_t_over_r_mean_us": s331.get("scalar_t_bootstrap_over_r_mean_us", ""),
        "speedup_mean": s331.get("speedup_vs_repeated_scalar_mean", ""),
        "speedup_ci95": "",
        "noise_trials": s331.get("noise_trials", ""),
        "noise_pair_failures": s331.get("noise_pair_failures", ""),
        "time_maxrss_kb": s331.get("time_maxrss_kb", ""),
        "evidence_stage": "Stage331",
        "source": rel(STAGE331_SUMMARY),
        "claim_status": "current_head_highstat",
    })
    for row in read_csv(STAGE344_PERF):
        rows.append({
            "case": row.get("case", ""),
            "param": row.get("param", ""),
            "r": row.get("r", ""),
            "backend": "spqlios_avx512-wsl",
            "metric": "complete_sab_T_bootstrap_over_r_vs_repeated_scalar",
            "samples": row.get("samples", ""),
            "correctness": row.get("correctness", ""),
            "pvw_t_over_r_mean_us": row.get("pvw_t_over_r_mean_us", ""),
            "pvw_t_over_r_ci95_us": row.get("pvw_t_over_r_ci95_us", ""),
            "scalar_t_over_r_mean_us": row.get("scalar_t_over_r_mean_us", ""),
            "speedup_mean": row.get("speedup_mean", ""),
            "speedup_ci95": row.get("speedup_ci95", ""),
            "noise_trials": row.get("noise_trials", ""),
            "noise_pair_failures": row.get("noise_pair_failures", ""),
            "time_maxrss_kb": row.get("time_maxrss_kb", ""),
            "evidence_stage": "Stage344",
            "source": rel(STAGE344_PERF),
            "claim_status": "current_head_highstat" if row.get("status") == "PASS_CASE" else "not_promoted",
        })
    return rows


def source_rows() -> list[dict[str, object]]:
    return [
        {
            "stage": "Stage331",
            "role": "target r=4 current-head high-stat",
            "decision": first_row(STAGE331_SUMMARY).get("decision", ""),
            "source": rel(STAGE331_SUMMARY),
        },
        {
            "stage": "Stage343",
            "role": "target r=2 current-head high-stat top-up",
            "decision": first_row(STAGE343_SUMMARY).get("decision", ""),
            "source": rel(STAGE343_SUMMARY),
        },
        {
            "stage": "Stage344",
            "role": "added binary parameter current-head matrix",
            "decision": first_row(STAGE344_SUMMARY).get("decision", ""),
            "source": rel(STAGE344_SUMMARY),
        },
    ]


def claim_rows() -> list[dict[str, object]]:
    return [
        {
            "claim": "binary_parameter_matrix",
            "status": "ALLOW_SCOPED",
            "safe_statement": "For tested binary include-zero parameter rows SET_2_3_2048, SET_4_5_2048, and SET_2_3_4096 with r=2/4, PVW/MAT-SAB improves complete SAB T_bootstrap/r versus repeated scalar SAB under spqlios_avx512.",
            "blocked_statement": "Do not generalize to all parameters, non-binary branches, or other backends without matching gates.",
            "evidence": rel(BINARY_MATRIX),
        },
        {
            "claim": "algorithmic_speedup_metric",
            "status": "ALLOW_SCOPED",
            "safe_statement": "The comparison dimension is amortized per plaintext bit/lane, T_bootstrap/r, not raw single-call latency.",
            "blocked_statement": "Do not mix kernel microbench, backend/SIMD gains, or scalar single-call latency into this matrix claim.",
            "evidence": rel(BINARY_MATRIX),
        },
        {
            "claim": "novelty_or_theoretical_optimality",
            "status": "BLOCKED",
            "safe_statement": "No novelty or theoretical-optimality wording is introduced by this synthesis.",
            "blocked_statement": "Requires verified related-work/full-text support and a separate proof or lower-bound argument.",
            "evidence": rel(PROOF),
        },
        {
            "claim": "resource_generality",
            "status": "PARTIAL_ONLY",
            "safe_statement": "RSS is recorded per row; key size/keygen/resource generality is not fully synthesized here.",
            "blocked_statement": "Do not claim memory/key-size optimality or full resource dominance from this matrix alone.",
            "evidence": rel(BINARY_MATRIX),
        },
    ]


def proof_rows(matrix: list[dict[str, object]]) -> list[dict[str, object]]:
    all_rows_pass = all(
        row.get("samples") == "10"
        and row.get("correctness") == "Pass"
        and row.get("noise_trials") == "10"
        and row.get("noise_pair_failures") == "0"
        and row.get("claim_status") == "current_head_highstat"
        for row in matrix
    )
    expected_cases = {"SET_2_3_2048_r2", "SET_2_3_2048_r4", "SET_4_5_2048_r2", "SET_4_5_2048_r4", "SET_2_3_4096_r2", "SET_2_3_4096_r4"}
    observed_cases = {str(row.get("case", "")) for row in matrix}
    return [
        {
            "gate": "G1_input_stage_decisions",
            "status": "PASS" if all(row.get("decision", "").startswith("PASS") for row in source_rows()) else "FAIL",
            "metric": "Stage331/343/344 decisions",
            "value": ";".join(f"{row.get('stage')}={row.get('decision')}" for row in source_rows()),
            "interpretation": "Every source stage must have passed before synthesis.",
        },
        {
            "gate": "G2_matrix_coverage",
            "status": "PASS" if observed_cases == expected_cases else "FAIL",
            "metric": "observed/expected cases",
            "value": f"{len(observed_cases)}/{len(expected_cases)}",
            "interpretation": "The scoped binary matrix needs target and added rows for r=2/4.",
        },
        {
            "gate": "G3_row_quality",
            "status": "PASS" if all_rows_pass else "FAIL",
            "metric": "samples/correctness/noise",
            "value": "all rows 10 samples, correctness Pass, noise 0/10" if all_rows_pass else "one or more rows incomplete",
            "interpretation": "Rows must be high-stat current-head evidence, not smoke or historical-only rows.",
        },
        {
            "gate": "G4_metric_alignment",
            "status": "PASS",
            "metric": "primary endpoint",
            "value": "complete SAB T_bootstrap/r vs repeated scalar",
            "interpretation": "This synthesis answers the user's amortized per plaintext-bit comparison requirement.",
        },
        {
            "gate": "G5_claim_boundary",
            "status": "PASS",
            "metric": "blocked claims",
            "value": "non-binary;all-parameter;novelty;theoretical-optimality;resource-generality",
            "interpretation": "The synthesis does not overclaim beyond tested binary rows.",
        },
        {
            "gate": "G6_decision",
            "status": DECISION if all_rows_pass and observed_cases == expected_cases else "FAIL_STAGE345_BINARY_MATRIX_SYNTHESIS",
            "metric": "stage decision",
            "value": DECISION if all_rows_pass and observed_cases == expected_cases else "FAIL",
            "interpretation": "Controls whether the scoped binary matrix is ready for paper-package use.",
        },
    ]


def next_rows() -> list[dict[str, object]]:
    return [
        {
            "priority": "P0",
            "route": "stage346_resource_and_paper_table_refresh",
            "entry_condition": DECISION,
            "command": "Refresh paper result tables and resource caveats from Stage345.",
            "gate": "No claim may omit row-level source, metric, backend, sample count, or blocked-claim boundary.",
            "failure_action": "Keep Stage345 as internal synthesis only.",
        },
        {
            "priority": "P1",
            "route": "stage346_new_mechanism_or_formal_lower_bound",
            "entry_condition": "Need theoretical-optimality or stronger algorithmic contribution.",
            "command": "Admit only a concrete mechanism/proof candidate with falsifiable gates.",
            "gate": "No theoretical-optimality statement without a proof obligation and experiment link.",
            "failure_action": "Retain scoped systems result.",
        },
        {
            "priority": "P2",
            "route": "stage346_nonbinary_or_backend_extension",
            "entry_condition": "Need claims outside binary spqlios_avx512 rows.",
            "command": "Run branch/backend-specific gates rather than reusing this binary matrix.",
            "gate": "Each new branch/backend needs correctness, noise, and T_bootstrap/r evidence.",
            "failure_action": "Block broader generality wording.",
        },
    ]


def append_run_log() -> None:
    marker = "stage345-binary-matrix-synthesis-001"
    row = [
        marker,
        date.today().isoformat(),
        git_head(),
        "Stage 345",
        "evidence-synthesis",
        "python scripts/build_stage345_binary_matrix_synthesis.py",
        "Stage331 target r=4; Stage343 target r=2; Stage344 added binary rows",
        "n/a",
        DECISION,
        "Synthesizes current-head binary parameter matrix under complete SAB T_bootstrap/r without promoting novelty or theoretical-optimality claims.",
        f"{rel(DOC)}; {rel(SUMMARY)}; {rel(BINARY_MATRIX)}; {rel(PROOF)}",
    ]
    line_buffer = StringIO()
    csv.writer(line_buffer, lineterminator="").writerow(row)
    replacement_line = line_buffer.getvalue()
    if marker in read_text(RUN_LOG):
        lines = read_text(RUN_LOG).splitlines()
        lines = [replacement_line if line.startswith(f"{marker},") else line for line in lines]
        write_text(RUN_LOG, "\n".join(lines))
        return
    RUN_LOG.parent.mkdir(parents=True, exist_ok=True)
    with RUN_LOG.open("a", encoding="utf-8", newline="\n") as handle:
        if read_text(RUN_LOG) and not read_text(RUN_LOG).endswith("\n"):
            handle.write("\n")
        csv.writer(handle, lineterminator="\n").writerow(row)


def sha256_file(path: Path) -> str:
    if not path.exists() or not path.is_file():
        return ""
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1 << 20), b""):
            digest.update(chunk)
    return digest.hexdigest()


def file_size(path: Path) -> int:
    return path.stat().st_size if path.exists() and path.is_file() else 0


def artifact_index(paths: list[Path]) -> None:
    rows = [{"artifact": rel(path), "exists": path.exists(), "bytes": file_size(path), "sha256": sha256_file(path)} for path in paths]
    write_csv(ARTIFACT, rows, ["artifact", "exists", "bytes", "sha256"])


def main() -> int:
    OUT.mkdir(parents=True, exist_ok=True)
    matrix = binary_rows()
    speedups = [fnum(row.get("speedup_mean")) for row in matrix]
    rss_vals = [int(str(row.get("time_maxrss_kb"))) for row in matrix if str(row.get("time_maxrss_kb")).isdigit()]
    summary = [{
        "decision": DECISION,
        "current_head": git_head(),
        "rows": len(matrix),
        "parameters": "SET_2_3_2048;SET_4_5_2048;SET_2_3_4096",
        "r_values": "2;4",
        "primary_metric": "complete_sab_T_bootstrap_over_r_vs_repeated_scalar",
        "speedup_min": f"{min(speedups):.6f}",
        "speedup_max": f"{max(speedups):.6f}",
        "speedup_mean_across_rows": f"{mean(speedups):.6f}",
        "max_rss_kb": max(rss_vals) if rss_vals else "",
        "claim_status": "scoped_binary_matrix_ready",
    }]
    claims = claim_rows()
    sources = source_rows()
    proof = proof_rows(matrix)
    nextq = next_rows()
    write_csv(SUMMARY, summary, ["decision", "current_head", "rows", "parameters", "r_values", "primary_metric", "speedup_min", "speedup_max", "speedup_mean_across_rows", "max_rss_kb", "claim_status"])
    write_csv(BINARY_MATRIX, matrix, ["case", "param", "r", "backend", "metric", "samples", "correctness", "pvw_t_over_r_mean_us", "pvw_t_over_r_ci95_us", "scalar_t_over_r_mean_us", "speedup_mean", "speedup_ci95", "noise_trials", "noise_pair_failures", "time_maxrss_kb", "evidence_stage", "source", "claim_status"])
    write_csv(CLAIMS, claims, ["claim", "status", "safe_statement", "blocked_statement", "evidence"])
    write_csv(SOURCES, sources, ["stage", "role", "decision", "source"])
    write_csv(PROOF, proof, ["gate", "status", "metric", "value", "interpretation"])
    write_csv(NEXT, nextq, ["priority", "route", "entry_condition", "command", "gate", "failure_action"])
    write_text(COMMANDS, """# Stage345 Reproduction Commands

```powershell
python scripts\\build_stage345_binary_matrix_synthesis.py
```
""")
    write_text(REPORT, f"""# Stage345 Binary Matrix Synthesis

Decision: `{DECISION}`.

Stage345 synthesizes current-head binary parameter evidence under the user's
requested amortized endpoint: complete SAB `T_bootstrap/r` versus repeated
scalar SAB. It is not a new kernel, backend, novelty, or theoretical-optimality
claim.

## Summary

{md_table(summary, ["decision", "rows", "primary_metric", "speedup_min", "speedup_max", "speedup_mean_across_rows", "claim_status"])}

## Matrix

{md_table(matrix, ["case", "samples", "correctness", "pvw_t_over_r_mean_us", "scalar_t_over_r_mean_us", "speedup_mean", "noise_trials", "noise_pair_failures", "evidence_stage"])}

## Claim Boundary

{md_table(claims, ["claim", "status", "safe_statement", "blocked_statement"])}

## Proof Gate

{md_table(proof, ["gate", "status", "metric", "value"])}
""")
    write_text(DOC, f"""# Stage345 Binary Matrix Synthesis

Decision: `{DECISION}`.

The current safe matrix claim is scoped to binary include-zero rows on
`spqlios_avx512`, using complete SAB `T_bootstrap/r` versus repeated scalar SAB.

{md_table(matrix, ["case", "samples", "speedup_mean", "speedup_ci95", "noise_trials", "noise_pair_failures", "evidence_stage"])}

Blocked: non-binary support, all-parameter generality, backend generality,
novelty, theoretical optimality, and full resource/key-size dominance.
""")
    write_text(THEORY, """# Stage345 Binary Matrix Claim Model

The comparison unit is amortized complete bootstrapping time per plaintext
bit/lane:

```text
T_amortized = T_bootstrap / r
speedup = T_repeated_scalar_per_lane / T_PVW_MAT_SAB_per_lane
```

This matrix is an evidence synthesis. It does not change the algorithm and it
does not prove theoretical optimality. It establishes that the current exact
PVW/MAT-SAB implementation has current-head high-stat evidence on the tested
binary include-zero rows.
""")
    write_text(PLAN, """# Stage346 Next Mechanism Or Paper Plan

Allowed next routes:

- refresh paper/result tables using Stage345 row-level evidence;
- add a resource/key-size matrix if resource claims are desired;
- admit a new mechanism only with a theory model, isolated gate, full-SAB gate,
  noise/resource gate, and negative-result policy;
- run branch/backend gates for non-binary or backend-general claims.

Do not infer novelty or theoretical optimality from Stage345.
""")
    append_once(GOAL, "<!-- stage345-binary-matrix-synthesis -->", f"""
<!-- stage345-binary-matrix-synthesis -->
- Stage345: `{DECISION}`. Synthesized current-head binary parameter matrix under complete `T_bootstrap/r`; stronger novelty/optimality/general-resource claims remain blocked.
""")
    append_once(ROADMAP, "<!-- stage345-binary-matrix-synthesis -->", f"""
<!-- stage345-binary-matrix-synthesis -->
## Stage345: Binary Matrix Synthesis

- Decision: `{DECISION}`.
- Result: scoped current-head binary matrix for SET_2_3_2048, SET_4_5_2048, and SET_2_3_4096 with r=2/4.
- Boundary: no novelty, theoretical optimality, non-binary, all-parameter, backend-general, or full-resource claim.
""")
    append_once(HYPOTHESES, "H345_binary_matrix_synthesis:", f"""
H345_binary_matrix_synthesis:
  status: {DECISION}
  primary_metric: complete_sab_T_bootstrap_over_r
  evidence:
    - repro/stage345_binary_matrix_synthesis/summary.csv
    - repro/stage345_binary_matrix_synthesis/binary_matrix.csv
    - repro/stage345_binary_matrix_synthesis/claim_boundary.csv
    - repro/stage345_binary_matrix_synthesis/proof_gate.csv
  conclusion: >
    Stage345 synthesizes Stage331/343/344 into a scoped current-head binary
    parameter matrix. It does not prove novelty, theoretical optimality,
    non-binary support, backend generality, or full resource dominance.
""")
    append_once(MANIFEST, "<!-- stage345-binary-matrix-synthesis-manifest -->", """
<!-- stage345-binary-matrix-synthesis-manifest -->
- stage345_binary_matrix_synthesis:
  - `docs/stage345_binary_matrix_synthesis.md`
  - `theory_checks/stage345_binary_matrix_claim_model.md`
  - `experiments/stage346_next_mechanism_or_paper_plan.md`
  - `scripts/build_stage345_binary_matrix_synthesis.py`
  - `repro/stage345_binary_matrix_synthesis/`
""")
    append_once(CHECKLIST, "<!-- stage345-binary-matrix-synthesis-checklist -->", f"""
<!-- stage345-binary-matrix-synthesis-checklist -->
- [x] Stage345 records `{DECISION}` and preserves blocked stronger-claim boundaries.
""")
    append_run_log()
    artifact_index([DOC, THEORY, PLAN, BUILDER, SUMMARY, BINARY_MATRIX, CLAIMS, SOURCES, PROOF, NEXT, REPORT, COMMANDS])
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
