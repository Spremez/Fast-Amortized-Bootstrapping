#!/usr/bin/env python3
"""Build Stage307 direct DFT lifecycle split-profile artifacts."""

from __future__ import annotations

import csv
import hashlib
import re
import subprocess
from pathlib import Path
from typing import Dict, Iterable, List


ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "repro" / "stage307_direct_ifft_lifecycle_split_profile"
RAW = OUT / "raw"
DOC = ROOT / "docs" / "stage307_direct_ifft_lifecycle_split_profile.md"
THEORY = ROOT / "theory_checks" / "stage307_direct_ifft_lifecycle_model.md"
VARIANT = ROOT / "algorithm_variants" / "mat_rlwe_sab_stage307_direct_ifft_lifecycle.md"
PLAN = ROOT / "experiments" / "stage307_direct_ifft_lifecycle_split_profile_plan.md"
RUNNER = ROOT / "scripts" / "run_stage307_direct_ifft_lifecycle_split_profile.sh"
BUILDER = ROOT / "scripts" / "build_stage307_direct_ifft_lifecycle_split_profile.py"

SUMMARY = OUT / "stage307_summary.csv"
LIFECYCLE = OUT / "direct_lifecycle_components.csv"
PROOF = OUT / "proof_gate.csv"
NEXT = OUT / "next_stage_queue.csv"
COMMANDS = OUT / "reproduction_commands.md"
REPORT = OUT / "stage307_report.md"
ARTIFACT = OUT / "artifact_index.csv"

GOAL = ROOT / "docs" / "current_codex_goal_sab_completion.md"
ROADMAP = ROOT / "docs" / "roadmap_stage19_plus.md"
HYPOTHESES = ROOT / "hypotheses" / "hypothesis_register.yaml"
RUN_LOG = ROOT / "repro" / "run_log.csv"
MANIFEST = ROOT / "repro" / "artifact_manifest.md"
CHECKLIST = ROOT / "repro" / "reproduction_checklist.md"

DECISION_PASS = "PASS_STAGE307_DIRECT_IFFT_LIFECYCLE_PROFILE_RECORDED"
DECISION_FAIL = "FAIL_STAGE307_DIRECT_IFFT_LIFECYCLE_PROFILE"

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
DIRECT_RE = re.compile(r"MAT_TRGSW_DIRECT_DFT_PROFILE sample (?P<direct>.+)")
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
    path.parent.mkdir(parents=True, exist_ok=True)
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


def git_head() -> str:
    try:
        return subprocess.check_output(["git", "rev-parse", "--short", "HEAD"], cwd=ROOT, text=True).strip()
    except (subprocess.CalledProcessError, FileNotFoundError):
        return "unknown"


def parse_kv(regex: re.Pattern[str], text: str, group: str) -> Dict[str, str]:
    matches = list(regex.finditer(text))
    if not matches:
        return {}
    return dict(KV_RE.findall(matches[-1].group(group)))


def parse_body_rows(text: str) -> List[Dict[str, str]]:
    return [dict(KV_RE.findall(match.group("body"))) for match in BODY_RE.finditer(text)]


def table(rows: List[Dict[str, object]], fields: List[str]) -> str:
    out = ["| " + " | ".join(fields) + " |", "| " + " | ".join("---" for _ in fields) + " |"]
    for row in rows:
        out.append("| " + " | ".join(str(row.get(field, "")).replace("|", "\\|") for field in fields) + " |")
    return "\n".join(out)


def append_run_log(decision: str) -> None:
    run_id = "stage307-direct-ifft-lifecycle-split-profile-001"
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
        "git_ref": git_head(),
        "commit_or_state": git_head(),
        "stage": "Stage 307",
        "backend": "spqlios_avx512-local",
        "command": "FFT_LIB=spqlios_avx512 PARAM=SET_2_3_2048 bash scripts/run_stage307_direct_ifft_lifecycle_split_profile.sh",
        "config": "direct DFT profile-only lifecycle split; r=4 include-zero",
        "params": "BINARY SET_2_3_2048; r=4; include-zero; direct sub-DTF",
        "seed": "n/a",
        "status": decision,
        "summary": "Stage307 splits direct DFT residual into digit-to-double and ifft profile components.",
        "artifacts": f"{rel(DOC)}; {rel(SUMMARY)}; {rel(LIFECYCLE)}; {rel(PROOF)}",
    }
    for key, value in values.items():
        if key in row:
            row[key] = value
    with RUN_LOG.open("a", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fields, lineterminator="\n")
        writer.writerow(row)


def artifact_index(paths: List[Path]) -> None:
    rows = []
    for path in paths:
        if not path.exists() or not path.is_file():
            continue
        data = path.read_bytes()
        rows.append({"path": rel(path), "bytes": str(len(data)), "sha256": hashlib.sha256(data).hexdigest()})
    write_csv(ARTIFACT, rows, ["path", "bytes", "sha256"])


def main() -> None:
    OUT.mkdir(parents=True, exist_ok=True)
    log = RAW / "direct_dft" / "run.log"
    text = read_text(log)
    correct = CORRECT_RE.search(text)
    bench = BENCH_RE.search(text)
    body_rows = parse_body_rows(text)
    split = parse_kv(SPLIT_RE, text, "split")
    direct = parse_kv(DIRECT_RE, text, "direct")

    rows_per_call = int(fnum(direct.get("last_k"))) + int(fnum(direct.get("last_r")))
    expected_direct_rows = int(fnum(split.get("sub_calls"))) * rows_per_call
    direct_rows = int(fnum(direct.get("rows_sum")))
    split_dft_us = fnum(split.get("dft_us"))
    direct_total_us = fnum(direct.get("total_us"))
    digit_us = fnum(direct.get("digit_us"))
    ifft_us = fnum(direct.get("ifft_us"))
    direct_accounted = digit_us + ifft_us
    dominant = "ifft" if ifft_us >= digit_us else "digit_to_double"
    profile_vs_split = direct_total_us / split_dft_us if split_dft_us else 0.0
    accounted_vs_total = direct_accounted / direct_total_us if direct_total_us else 0.0
    correctness = correct.group("status") if correct else "missing"
    row_match = direct_rows == expected_direct_rows and direct_rows > 0
    ratio_ok = 0.80 <= profile_vs_split <= 1.10
    accounted_ok = 0.90 <= accounted_vs_total <= 1.10
    decision = DECISION_PASS if correctness == "Pass" and row_match and ratio_ok and accounted_ok else DECISION_FAIL

    summary_rows = [{
        "decision": decision,
        "correctness": correctness,
        "mode": correct.group("mode") if correct else "",
        "r": correct.group("r") if correct else "",
        "h": correct.group("h") if correct else "",
        "r_prec": correct.group("r_prec") if correct else "",
        "reps": bench.group("reps") if bench else "",
        "t_bootstrap_over_r_pvw_us": bench.group("t_pvw") if bench else "",
        "speedup_vs_scalar": bench.group("speedup") if bench else "",
        "body_profile_rows": len(body_rows),
        "split_normal_calls": split.get("normal_calls", ""),
        "split_sub_calls": split.get("sub_calls", ""),
        "direct_profile_calls": direct.get("calls", ""),
        "direct_rows_sum": direct.get("rows_sum", ""),
        "expected_direct_rows": expected_direct_rows,
        "direct_total_us": direct.get("total_us", ""),
        "split_dft_us": split.get("dft_us", ""),
        "direct_profile_vs_split_dft_ratio": f"{profile_vs_split:.6f}",
        "dominant_direct_subcomponent": dominant,
        "claim": "profile_only_not_latency_claim",
    }]
    write_csv(SUMMARY, summary_rows, [
        "decision", "correctness", "mode", "r", "h", "r_prec", "reps",
        "t_bootstrap_over_r_pvw_us", "speedup_vs_scalar", "body_profile_rows",
        "split_normal_calls", "split_sub_calls", "direct_profile_calls",
        "direct_rows_sum", "expected_direct_rows", "direct_total_us",
        "split_dft_us", "direct_profile_vs_split_dft_ratio",
        "dominant_direct_subcomponent", "claim",
    ])

    lifecycle_rows = []
    for name, us in [("digit_to_double", digit_us), ("ifft", ifft_us)]:
        lifecycle_rows.append({
            "component": name,
            "us": f"{us:.3f}",
            "share_of_direct_profile_total": f"{us / direct_total_us:.6f}" if direct_total_us else "",
            "share_of_accounted_digit_plus_ifft": f"{us / direct_accounted:.6f}" if direct_accounted else "",
            "avg_us_per_direct_call": f"{us / fnum(direct.get('calls')):.6f}" if fnum(direct.get("calls")) else "",
            "avg_us_per_row": f"{us / direct_rows:.6f}" if direct_rows else "",
        })
    lifecycle_rows.append({
        "component": "accounting_gap",
        "us": f"{direct_total_us - direct_accounted:.3f}",
        "share_of_direct_profile_total": f"{(direct_total_us - direct_accounted) / direct_total_us:.6f}" if direct_total_us else "",
        "share_of_accounted_digit_plus_ifft": "",
        "avg_us_per_direct_call": "",
        "avg_us_per_row": "",
    })
    write_csv(LIFECYCLE, lifecycle_rows, [
        "component", "us", "share_of_direct_profile_total",
        "share_of_accounted_digit_plus_ifft", "avg_us_per_direct_call",
        "avg_us_per_row",
    ])

    proof = [
        {"gate": "G1_correctness", "status": "PASS" if correctness == "Pass" else "FAIL", "metric": "target_full correctness", "value": correctness, "interpretation": "Profile-only instrumentation must preserve complete SAB correctness."},
        {"gate": "G2_row_consistency", "status": "PASS" if row_match else "FAIL", "metric": "direct rows vs split sub rows", "value": f"{direct_rows}/{expected_direct_rows}", "interpretation": "Direct profile covers only sub-DTF direct calls, not normal calls."},
        {"gate": "G3_profile_coverage", "status": "PASS" if ratio_ok else "WARN", "metric": "direct profile total / split dft_us", "value": f"{profile_vs_split:.6f}", "interpretation": "Direct profile should explain most split dft_us; the remainder includes normal-call DFT and timer overhead."},
        {"gate": "G4_internal_accounting", "status": "PASS" if accounted_ok else "WARN", "metric": "(digit+ifft)/direct_total", "value": f"{accounted_vs_total:.6f}", "interpretation": "Digit and ifft timers should account for the direct profile block."},
        {"gate": "G5_dominant_subcomponent", "status": "RECORDED", "metric": "dominant", "value": dominant, "interpretation": "Selects the next candidate family."},
        {"gate": "G6_claim_boundary", "status": "PASS_PROFILE_ONLY", "metric": "scope", "value": "instrumented one-run profile", "interpretation": "Do not use Stage307 latency as final speed evidence."},
        {"gate": "G7_decision", "status": decision, "metric": "stage decision", "value": decision, "interpretation": "Controls Stage308 route."},
    ]
    write_csv(PROOF, proof, ["gate", "status", "metric", "value", "interpretation"])

    if dominant == "ifft":
        next_route = "stage308_spqlios_ifft_lifecycle_candidate"
        next_gate = "Inspect whether per-row reverse FFT calls can be batched, fused, or reduced without changing DFT semantics."
        failure = "Keep direct-DFT path; do not rewrite dense AVX until split changes."
    else:
        next_route = "stage308_digit_to_double_avx512_candidate"
        next_gate = "Optimize digit extraction/materialization and prove reduced memory/instruction work."
        failure = "Keep direct-DFT path; avoid FFT work until digit bottleneck is reduced."
    next_rows = [
        {
            "priority": "P0",
            "route": next_route,
            "entry_condition": decision,
            "gate": next_gate,
            "failure_action": failure,
        },
        {
            "priority": "P1",
            "route": "stage308_confirm_profile_on_SET_4_5_2048",
            "entry_condition": "parameter-generalization claim needed",
            "gate": "Repeat Stage307 profile on SET_4_5_2048 before broad parameter wording.",
            "failure_action": "Scope lifecycle split to SET_2_3_2048 only.",
        },
    ]
    write_csv(NEXT, next_rows, ["priority", "route", "entry_condition", "gate", "failure_action"])

    report = (
        "# Stage307 Direct IFFT Lifecycle Split Profile\n\n"
        f"Decision: `{decision}`.\n\n"
        "Stage307 adds profile-only instrumentation under `MAT_TRGSW_DIRECT_DFT_PROFILE=true` and splits the direct sub-DTF materialization block into digit-to-double and reverse-FFT time.\n\n"
        "## Summary\n\n" + table(summary_rows, [
            "decision", "correctness", "t_bootstrap_over_r_pvw_us",
            "split_sub_calls", "direct_profile_calls", "direct_rows_sum",
            "direct_profile_vs_split_dft_ratio", "dominant_direct_subcomponent",
        ]) +
        "\n\n## Lifecycle Components\n\n" + table(lifecycle_rows, [
            "component", "us", "share_of_direct_profile_total",
            "avg_us_per_direct_call", "avg_us_per_row",
        ]) +
        "\n\n## Proof Gate\n\n" + table(proof, ["gate", "status", "metric", "value", "interpretation"]) + "\n"
    )
    write_text(DOC, report)
    write_text(REPORT, report)
    write_text(THEORY, f"""# Stage307 Direct IFFT Lifecycle Model

The Stage305 `torus_to_dft` bucket in the direct sub-DTF path combines two
operations:

1. signed gadget digit extraction from `in2 - in1` directly into a double
   buffer;
2. one SPQLIOS reverse FFT (`ifft`) per MAT row.

Stage307 measures those two operations under a compile-time-only profile flag.
The profile covers `sub_calls` only. Normal MAT external products still use the
ordinary decomposition/DFT path, so their small contribution remains in
`MAT_TRGSW_SPLIT_PROFILE.dft_us` but not in the direct lifecycle profile.

Recorded dominant direct subcomponent: `{dominant}`.

This stage is not a latency claim. It chooses the next implementation target:
if `ifft` dominates, investigate row batching or lifecycle reduction around
SPQLIOS reverse FFT; if digit materialization dominates, investigate AVX512
digit extraction and output layout.
""")
    write_text(VARIANT, f"""# Stage307 MAT_TRGSW_DIRECT_DFT_PROFILE

Flag: `MAT_TRGSW_DIRECT_DFT_PROFILE=true`.

Decision: `{decision}`.

This is instrumentation only. It adds no new ciphertext format and no new
optimized path. The scalar SAB path and default PVW/MAT-SAB path remain
unchanged unless the profile flag is explicitly enabled.
""")
    write_text(PLAN, """# Stage307 Experiment Plan

1. Build the complete include-zero target benchmark with direct sub-DTF enabled.
2. Enable `MAT_TRGSW_SPLIT_PROFILE` and `MAT_TRGSW_DIRECT_DFT_PROFILE`.
3. Require target full correctness to pass.
4. Check direct-profile rows against split-profile sub-call rows.
5. Route Stage308 to the dominant direct lifecycle subcomponent only.
""")
    write_text(COMMANDS, """# Stage307 Reproduction Commands

```bash
FFT_LIB=spqlios_avx512 PARAM=SET_2_3_2048 \\
  bash scripts/run_stage307_direct_ifft_lifecycle_split_profile.sh
python3 scripts/build_stage307_direct_ifft_lifecycle_split_profile.py
```
""")

    append_once(ROADMAP, "## Stage 307: Direct IFFT Lifecycle Split Profile", "\n## Stage 307: Direct IFFT Lifecycle Split Profile\n\nGoal: split the direct sub-DTF materialization profile into digit-to-double and reverse-FFT subcomponents.\n\n" f"Status: `{decision}`.\n")
    append_once(GOAL, "<!-- stage307-direct-ifft-lifecycle-split-profile -->", "\n<!-- stage307-direct-ifft-lifecycle-split-profile -->\n### Stage307 direct IFFT lifecycle split profile\n\n" f"`{decision}` records `{dominant}` as the dominant direct DFT subcomponent under profile-only instrumentation.\n")
    append_once(HYPOTHESES, "H307_direct_ifft_lifecycle_split_profile:", "\nH307_direct_ifft_lifecycle_split_profile:\n" f"  status: {decision}\n  primary_metric: profile_only_direct_digit_vs_ifft_split\n  dominant_subcomponent: {dominant}\n  evidence:\n    - repro/stage307_direct_ifft_lifecycle_split_profile/stage307_summary.csv\n    - repro/stage307_direct_ifft_lifecycle_split_profile/direct_lifecycle_components.csv\n    - repro/stage307_direct_ifft_lifecycle_split_profile/proof_gate.csv\n  conclusion: >\n    Stage307 separates the direct sub-DTF DFT residual into digit-to-double and\n    ifft subcomponents. It is profile-only and routes the next implementation\n    target without creating a new full-SAB speed claim.\n")
    append_once(MANIFEST, "- stage307_direct_ifft_lifecycle_split_profile:", "\n- stage307_direct_ifft_lifecycle_split_profile:\n  - `docs/stage307_direct_ifft_lifecycle_split_profile.md`\n  - `theory_checks/stage307_direct_ifft_lifecycle_model.md`\n  - `algorithm_variants/mat_rlwe_sab_stage307_direct_ifft_lifecycle.md`\n  - `experiments/stage307_direct_ifft_lifecycle_split_profile_plan.md`\n  - `scripts/run_stage307_direct_ifft_lifecycle_split_profile.sh`\n  - `scripts/build_stage307_direct_ifft_lifecycle_split_profile.py`\n  - `repro/stage307_direct_ifft_lifecycle_split_profile/`\n")
    append_once(CHECKLIST, "<!-- stage307-direct-ifft-lifecycle-split-profile-checklist -->", "\n<!-- stage307-direct-ifft-lifecycle-split-profile-checklist -->\n" f"- [x] Stage307 records `{decision}` and routes Stage308 to `{dominant}`.\n")
    append_run_log(decision)

    artifacts = [
        DOC, THEORY, VARIANT, PLAN, RUNNER, BUILDER, SUMMARY, LIFECYCLE, PROOF,
        NEXT, COMMANDS, REPORT, RAW / "variant_plan.csv", RAW / "direct_dft" / "build.log",
        RAW / "direct_dft" / "clean.log", RAW / "direct_dft" / "run.log",
    ]
    artifact_index(artifacts)
    print(decision)


if __name__ == "__main__":
    main()
