#!/usr/bin/env python3
"""Build Stage288 MAT EP split profile artifacts."""

from __future__ import annotations

import csv
import hashlib
import re
import subprocess
from pathlib import Path
from typing import Dict, Iterable, List


ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "repro" / "stage288_mat_ep_split_profile"
RAW = OUT / "raw"
DOC = ROOT / "docs" / "stage288_mat_ep_split_profile.md"
THEORY = ROOT / "theory_checks" / "stage288_mat_ep_split_profile_model.md"
VARIANT = ROOT / "algorithm_variants" / "mat_rlwe_sab_stage288_split_profile_result.md"
PLAN = ROOT / "experiments" / "stage288_mat_ep_split_profile_plan.md"
RUNNER = ROOT / "scripts" / "run_stage288_mat_ep_split_profile.sh"
BUILDER = ROOT / "scripts" / "build_stage288_mat_ep_split_profile.py"

CURRENT_GOAL = ROOT / "docs" / "current_codex_goal_sab_completion.md"
HYPOTHESES = ROOT / "hypotheses" / "hypothesis_register.yaml"
RUN_LOG = ROOT / "repro" / "run_log.csv"
MANIFEST = ROOT / "repro" / "artifact_manifest.md"
CHECKLIST = ROOT / "repro" / "reproduction_checklist.md"

SUMMARY = OUT / "split_profile_summary.csv"
COMPONENTS = OUT / "split_component_shares.csv"
CONSISTENCY = OUT / "consistency_checks.csv"
ADMISSION = OUT / "next_candidate_admission.csv"
PROOF = OUT / "proof_gate.csv"
NEXT = OUT / "next_stage_queue.csv"
COMMANDS = OUT / "reproduction_commands.md"
REPORT = OUT / "stage288_report.md"
ARTIFACT = OUT / "artifact_index.csv"

DECISION_PASS = "PASS_STAGE288_MAT_EP_SPLIT_PROFILE_RECORDED_MICROBENCH_NEXT"
DECISION_FAIL = "FAIL_STAGE288_MAT_EP_SPLIT_PROFILE"

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


def git_head() -> str:
    return subprocess.check_output(["git", "rev-parse", "--short", "HEAD"], cwd=ROOT, text=True).strip()


def read_text(path: Path) -> str:
    if not path.exists():
        return ""
    return path.read_text(encoding="utf-8", errors="replace").replace("\x00", "").replace("\r\n", "\n").replace("\r", "\n")


def write_text(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text.rstrip() + "\n", encoding="utf-8", newline="\n")


def write_csv(path: Path, fields: Iterable[str], rows: Iterable[Dict[str, object]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    field_list = list(fields)
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=field_list, lineterminator="\n")
        writer.writeheader()
        for row in rows:
            writer.writerow({field: row.get(field, "") for field in field_list})


def append_once(path: Path, marker: str, text: str) -> None:
    current = read_text(path)
    if marker in current:
        return
    sep = "" if current.endswith("\n") or not current else "\n"
    write_text(path, current + sep + text)


def fnum(value: object, default: float = 0.0) -> float:
    try:
        if value is None or value == "":
            return default
        return float(value)
    except (TypeError, ValueError):
        return default


def parse_kv_payload(regex: re.Pattern[str], text: str, group: str) -> Dict[str, str]:
    matches = list(regex.finditer(text))
    if not matches:
        return {}
    return dict(KV_RE.findall(matches[-1].group(group)))


def parse_all_kv_payloads(regex: re.Pattern[str], text: str, group: str) -> List[Dict[str, str]]:
    return [dict(KV_RE.findall(match.group(group))) for match in regex.finditer(text)]


def parse_summary() -> tuple[List[Dict[str, object]], List[Dict[str, object]], List[Dict[str, object]], str]:
    text = read_text(RAW / "run.log")
    correct = CORRECT_RE.search(text)
    bench = BENCH_RE.search(text)
    body_rows = parse_all_kv_payloads(BODY_RE, text, "body")
    body = body_rows[-1] if body_rows else {}
    split = parse_kv_payload(SPLIT_RE, text, "split")

    correctness = correct.group("status") if correct else "missing"
    mode = correct.group("mode") if correct else bench.group("mode") if bench else "missing"
    r = correct.group("r") if correct else bench.group("r") if bench else "missing"
    reps = bench.group("reps") if bench else "missing"

    split_total = fnum(split.get("total_us"))
    decompose = fnum(split.get("decompose_us"))
    dft = fnum(split.get("dft_us"))
    dense = fnum(split.get("dense_us"))
    split_calls = int(fnum(split.get("normal_calls")) + fnum(split.get("sub_calls")))
    body_mat_calls = int(sum(fnum(row.get("mat_ep_calls")) for row in body_rows))
    body_mat_us = sum(fnum(row.get("mat_ep_us")) for row in body_rows)
    full_us = sum(fnum(row.get("full_us")) for row in body_rows)
    rows_sum = int(fnum(split.get("rows_sum")))
    expected_rows = split_calls * 5
    ratio = split_total / body_mat_us if body_mat_us else 0.0

    summary = [{
        "variant": "backend_sub_decomp_dual",
        "mode": mode,
        "r": r,
        "reps": reps,
        "correctness": correctness,
        "pvw_t_over_r_us": bench.group("t_pvw") if bench else "",
        "scalar_t_over_r_us": bench.group("t_scalar") if bench else "",
        "speedup_vs_scalar": bench.group("speedup") if bench else "",
        "body_profile_rows": len(body_rows),
        "body_full_us_sum": f"{full_us:.3f}" if full_us else "",
        "body_mat_ep_calls": body_mat_calls,
        "body_mat_ep_us_sum": f"{body_mat_us:.3f}" if body_mat_us else "",
        "split_normal_calls": split.get("normal_calls", ""),
        "split_sub_calls": split.get("sub_calls", ""),
        "split_total_calls": split_calls,
        "split_rows_sum": rows_sum,
        "split_total_us": f"{split_total:.3f}" if split_total else "",
        "split_vs_body_mat_ep_ratio": f"{ratio:.6f}" if ratio else "",
        "source_log": rel(RAW / "run.log"),
    }]

    components = []
    for name, value in [
        ("decompose", decompose),
        ("torus_to_dft", dft),
        ("dense_from_dec", dense),
    ]:
        components.append({
            "component": name,
            "us": f"{value:.3f}",
            "share_of_split_total": f"{value / split_total:.6f}" if split_total else "",
            "share_of_body_mat_ep": f"{value / body_mat_us:.6f}" if body_mat_us else "",
            "calls": split_calls,
            "avg_us_per_call": f"{value / split_calls:.6f}" if split_calls else "",
            "status": "measured_profile_only",
        })

    max_component = max(components, key=lambda row: fnum(row["share_of_split_total"])) if components else {}
    dominant = max_component.get("component", "missing")
    decision = DECISION_PASS if correctness == "Pass" and split_calls > 0 and rows_sum == expected_rows else DECISION_FAIL
    checks = [
        {
            "check": "correctness",
            "status": "PASS" if correctness == "Pass" else "FAIL",
            "value": correctness,
            "interpretation": "Profile smoke must preserve target full-SAB correctness.",
        },
        {
            "check": "split_profile_line",
            "status": "PASS" if split_calls > 0 else "FAIL",
            "value": str(split_calls),
            "interpretation": "MAT_TRGSW_SPLIT_PROFILE line must be emitted.",
        },
        {
            "check": "call_count_match",
            "status": "PASS" if split_calls == body_mat_calls and split_calls > 0 else "FAIL",
            "value": f"split={split_calls}; body={body_mat_calls}",
            "interpretation": "Split calls should match the sum of all SAB body-profile mat_ep calls in the process.",
        },
        {
            "check": "rows_sum",
            "status": "PASS" if rows_sum == expected_rows and split_calls > 0 else "FAIL",
            "value": f"rows_sum={rows_sum}; expected={expected_rows}",
            "interpretation": "r=4,k=1,l=1 uses five rows per MAT EP call.",
        },
        {
            "check": "dominant_subcomponent",
            "status": "RECORDED",
            "value": dominant,
            "interpretation": "Dominant split component selects the next microbench candidate.",
        },
        {
            "check": "decision",
            "status": decision,
            "value": decision,
            "interpretation": "Profile evidence is instrumentation-only, not final latency evidence.",
        },
    ]
    return summary, components, checks, decision


def admission_rows(components: List[Dict[str, object]]) -> List[Dict[str, object]]:
    dominant = max(components, key=lambda row: fnum(row["share_of_split_total"])) if components else {}
    dom = dominant.get("component", "missing")
    return [
        {
            "candidate": f"S288-next-{dom}",
            "status": "admitted_to_isolated_microbench_design" if dom != "missing" else "missing",
            "measured_basis": f"dominant split component={dom}; share={dominant.get('share_of_split_total', '')}",
            "allowed_next_action": "Design isolated microbench/equivalence for the dominant subcomponent.",
            "blocked_action": "Promote based on profiled full-SAB timing or split share alone.",
            "required_gate": "unprofiled repeated T_bootstrap/r A/B after implementation candidate",
        }
    ]


def proof_rows(checks: List[Dict[str, object]], decision: str) -> List[Dict[str, object]]:
    by_check = {row["check"]: row for row in checks}
    return [
        {
            "gate": "G1_runner",
            "status": "PASS" if (RAW / "run.log").exists() else "FAIL",
            "metric": "run log",
            "value": rel(RAW / "run.log") if (RAW / "run.log").exists() else "missing",
            "interpretation": "Stage288 must execute the selected candidate with split profiling enabled.",
        },
        {
            "gate": "G2_correctness",
            "status": by_check["correctness"]["status"],
            "metric": "target correctness",
            "value": by_check["correctness"]["value"],
            "interpretation": by_check["correctness"]["interpretation"],
        },
        {
            "gate": "G3_call_count",
            "status": by_check["call_count_match"]["status"],
            "metric": "split/body MAT EP calls",
            "value": by_check["call_count_match"]["value"],
            "interpretation": by_check["call_count_match"]["interpretation"],
        },
        {
            "gate": "G4_rows",
            "status": by_check["rows_sum"]["status"],
            "metric": "rows sum",
            "value": by_check["rows_sum"]["value"],
            "interpretation": by_check["rows_sum"]["interpretation"],
        },
        {
            "gate": "G5_dominant",
            "status": "PASS",
            "metric": "dominant split component",
            "value": by_check["dominant_subcomponent"]["value"],
            "interpretation": by_check["dominant_subcomponent"]["interpretation"],
        },
        {
            "gate": "G6_decision",
            "status": decision,
            "metric": "stage decision",
            "value": decision,
            "interpretation": "Proceed only to isolated microbench design; do not claim final speed from profiled run.",
        },
    ]


def next_rows(admission: List[Dict[str, object]]) -> List[Dict[str, object]]:
    candidate = admission[0]["candidate"] if admission else "missing"
    return [
        {
            "priority": "P0",
            "route": "stage289_isolated_mat_ep_microbench_design",
            "entry_condition": candidate,
            "gate": "Build an isolated correctness/microbench for the dominant split component.",
            "failure_action": "Keep current selected exact path; do not rewrite hot path.",
        },
        {
            "priority": "P1",
            "route": "stage290_unprofiled_full_sab_ab",
            "entry_condition": "isolated candidate passes",
            "gate": "Repeated unprofiled complete SAB T_bootstrap/r A/B plus noise/resource.",
            "failure_action": "Record kernel-only result as neutral or negative.",
        },
    ]


def md_table(rows: List[Dict[str, object]], fields: List[str]) -> str:
    lines = ["| " + " | ".join(fields) + " |", "| " + " | ".join(["---"] * len(fields)) + " |"]
    for row in rows:
        lines.append("| " + " | ".join(str(row.get(field, "")).replace("\n", " ") for field in fields) + " |")
    return "\n".join(lines)


def write_documents(
    summary: List[Dict[str, object]],
    components: List[Dict[str, object]],
    checks: List[Dict[str, object]],
    admission: List[Dict[str, object]],
    proof: List[Dict[str, object]],
    next_queue: List[Dict[str, object]],
    decision: str,
) -> None:
    report = f"""# Stage288 MAT EP Split Profile

Decision: `{decision}`.

Stage288 runs the current selected `backend_sub_decomp_dual` path with
`MAT_TRGSW_SPLIT_PROFILE=true`. This is a profiled smoke, not a final latency
claim. Its purpose is to choose the next isolated MAT EP microbench target.

## Summary

{md_table(summary, ["variant", "mode", "r", "correctness", "body_profile_rows", "body_mat_ep_calls", "split_total_calls", "split_total_us", "split_vs_body_mat_ep_ratio"])}

## Split Components

{md_table(components, ["component", "us", "share_of_split_total", "share_of_body_mat_ep", "avg_us_per_call"])}

## Consistency Checks

{md_table(checks, ["check", "status", "value", "interpretation"])}

## Admission

{md_table(admission, ["candidate", "status", "measured_basis", "allowed_next_action", "blocked_action"])}

## Proof Gate

{md_table(proof, ["gate", "status", "metric", "value", "interpretation"])}

Generated from head `{git_head()}`.
"""
    write_text(DOC, report)
    write_text(REPORT, report)
    write_text(THEORY, """# Stage288 MAT EP Split Profile Model

The split profile partitions the currently selected MAT EP timer into:

1. `decompose`: torus diff/decomposition or normal decomposition;
2. `torus_to_dft`: conversion of decomposed rows to DFT;
3. `dense_from_dec`: exact dense MAT multiplication after decomposition.

The result is instrumentation evidence. It can select an isolated microbench
target, but final acceleration still requires unprofiled complete-SAB
`T_bootstrap/r` A/B and noise/resource gates.
""")
    write_text(VARIANT, """# Stage288 Split Profile Result

The admitted next candidate is whichever split subcomponent dominates the
measured `MAT_TRGSW_SPLIT_PROFILE` total. Any behavior-changing implementation
must first pass an isolated equivalence/microbench gate and then a full SAB
`T_bootstrap/r` A/B gate.
""")
    write_text(PLAN, """# Stage288 Reproduction Plan

```bash
bash scripts/run_stage288_mat_ep_split_profile.sh
python3 scripts/build_stage288_mat_ep_split_profile.py
```

The run is intentionally profiled and must not be used as final latency.
""")
    write_text(COMMANDS, """# Stage288 Reproduction Commands

```bash
bash scripts/run_stage288_mat_ep_split_profile.sh
python3 scripts/build_stage288_mat_ep_split_profile.py
```
""")


def artifact_index() -> None:
    paths = [
        DOC, THEORY, VARIANT, PLAN, RUNNER, BUILDER, COMMANDS, REPORT,
        SUMMARY, COMPONENTS, CONSISTENCY, ADMISSION, PROOF, NEXT,
        RAW / "variant_plan.csv", RAW / "clean.log", RAW / "build.log", RAW / "run.log",
    ]
    rows = []
    for path in paths:
        if path.exists():
            data = path.read_bytes()
            rows.append({"path": rel(path), "bytes": len(data), "sha256": hashlib.sha256(data).hexdigest()})
    write_csv(ARTIFACT, ["path", "bytes", "sha256"], rows)


def main() -> None:
    summary, components, checks, decision = parse_summary()
    admission = admission_rows(components)
    proof = proof_rows(checks, decision)
    next_queue = next_rows(admission)

    write_csv(SUMMARY, [
        "variant", "mode", "r", "reps", "correctness", "pvw_t_over_r_us",
        "scalar_t_over_r_us", "speedup_vs_scalar", "body_profile_rows",
        "body_full_us_sum", "body_mat_ep_calls", "body_mat_ep_us_sum",
        "split_normal_calls",
        "split_sub_calls", "split_total_calls", "split_rows_sum",
        "split_total_us", "split_vs_body_mat_ep_ratio", "source_log",
    ], summary)
    write_csv(COMPONENTS, [
        "component", "us", "share_of_split_total", "share_of_body_mat_ep",
        "calls", "avg_us_per_call", "status",
    ], components)
    write_csv(CONSISTENCY, ["check", "status", "value", "interpretation"], checks)
    write_csv(ADMISSION, [
        "candidate", "status", "measured_basis", "allowed_next_action",
        "blocked_action", "required_gate",
    ], admission)
    write_csv(PROOF, ["gate", "status", "metric", "value", "interpretation"], proof)
    write_csv(NEXT, ["priority", "route", "entry_condition", "gate", "failure_action"], next_queue)
    write_documents(summary, components, checks, admission, proof, next_queue, decision)

    append_once(CURRENT_GOAL, "<!-- stage288-mat-ep-split-profile -->", f"""<!-- stage288-mat-ep-split-profile -->
### Stage288 MAT EP split profile

`{decision}` records a profiled split run for the current selected
`backend_sub_decomp_dual` path. The result is instrumentation-only and selects
the next isolated microbench target; it is not final `T_bootstrap/r` evidence.
""")
    append_once(HYPOTHESES, "H10_stage288_mat_ep_split_profile:", f"""H10_stage288_mat_ep_split_profile:
  status: {decision}
  evidence:
    - repro/stage288_mat_ep_split_profile/split_profile_summary.csv
    - repro/stage288_mat_ep_split_profile/split_component_shares.csv
    - repro/stage288_mat_ep_split_profile/proof_gate.csv
    - docs/stage288_mat_ep_split_profile.md
  conclusion: >
    Stage288 records instrumentation-only MAT EP split evidence for the
    selected path. It selects the next isolated microbench target but does not
    provide final latency or optimality evidence.
""")
    append_once(RUN_LOG, "stage288-mat-ep-split-profile-001", f"""stage288-mat-ep-split-profile-001,2026-07-04,{git_head()},Stage 288,local-profile,bash scripts/run_stage288_mat_ep_split_profile.sh; python scripts/build_stage288_mat_ep_split_profile.py,"profiled MAT EP split for selected backend_sub_decomp_dual path",n/a,{decision},"Profiled smoke only; final latency requires unprofiled repeated T_bootstrap/r.",docs/stage288_mat_ep_split_profile.md; repro/stage288_mat_ep_split_profile/proof_gate.csv
""")
    append_once(MANIFEST, "- stage288_mat_ep_split_profile:", """- stage288_mat_ep_split_profile:
  - `docs/stage288_mat_ep_split_profile.md`
  - `theory_checks/stage288_mat_ep_split_profile_model.md`
  - `algorithm_variants/mat_rlwe_sab_stage288_split_profile_result.md`
  - `experiments/stage288_mat_ep_split_profile_plan.md`
  - `scripts/run_stage288_mat_ep_split_profile.sh`
  - `scripts/build_stage288_mat_ep_split_profile.py`
  - `repro/stage288_mat_ep_split_profile/`
""")
    append_once(CHECKLIST, "<!-- stage288-mat-ep-split-profile-checklist -->", f"""<!-- stage288-mat-ep-split-profile-checklist -->
- [x] Stage288 records `{decision}` for MAT EP split profiling.
""")
    artifact_index()
    print(decision)


if __name__ == "__main__":
    main()
