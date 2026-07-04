#!/usr/bin/env python3
"""Build Stage325 selector-transpose resource/microbench artifacts."""

from __future__ import annotations

import csv
import hashlib
import math
import re
import statistics
import subprocess
from pathlib import Path
from typing import Dict, Iterable, List


ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "repro" / "stage325_selector_transpose_resource_probe"
RAW = OUT / "raw"
DOC = ROOT / "docs" / "stage325_selector_transpose_resource_probe.md"
THEORY = ROOT / "theory_checks" / "stage325_selector_transpose_microbench_model.md"
VARIANT = ROOT / "algorithm_variants" / "mat_rlwe_sab_stage325_selector_transpose_probe.md"
PLAN_POSITIVE = ROOT / "experiments" / "stage326_selector_transpose_keyview_prototype_plan.md"
PLAN_CLOSE = ROOT / "experiments" / "stage326_exact_dense_route_closeout_plan.md"
RUNNER = ROOT / "scripts" / "run_stage325_selector_transpose_resource_probe.sh"
BENCH_SRC = ROOT / "scripts" / "stage325_selector_transpose_microbench.c"
BUILDER = ROOT / "scripts" / "build_stage325_selector_transpose_resource_probe.py"

SUMMARY = OUT / "summary.csv"
RUNS = OUT / "microbench_runs.csv"
RESOURCE = OUT / "resource_projection.csv"
PROOF = OUT / "proof_gate.csv"
NEXT = OUT / "next_stage_queue.csv"
COMMANDS = OUT / "reproduction_commands.md"
REPORT = OUT / "stage325_report.md"
ARTIFACT = OUT / "artifact_index.csv"

GOAL = ROOT / "docs" / "current_codex_goal_sab_completion.md"
ROADMAP = ROOT / "docs" / "roadmap_stage19_plus.md"
HYPOTHESES = ROOT / "hypotheses" / "hypothesis_register.yaml"
RUN_LOG = ROOT / "repro" / "run_log.csv"
MANIFEST = ROOT / "repro" / "artifact_manifest.md"
CHECKLIST = ROOT / "repro" / "reproduction_checklist.md"

STAGE324_SUMMARY = ROOT / "repro" / "stage324_selector_layout_mechanism_preflight" / "summary.csv"
STAGE324_VALUE = ROOT / "repro" / "stage324_selector_layout_mechanism_preflight" / "value_projection.csv"

DECISION_POSITIVE = "PASS_STAGE325_SELECTOR_TRANSPOSE_MICRO_POSITIVE_RESOURCE_GATED"
DECISION_NEUTRAL = "NEUTRAL_STAGE325_SELECTOR_TRANSPOSE_MICRO_NO_PROMOTION"
DECISION_FAIL = "FAIL_STAGE325_SELECTOR_TRANSPOSE_MICROBENCH"

LINE_RE = re.compile(r"stage325_selector_transpose_microbench,(?P<body>.*)")
KV_RE = re.compile(r"([A-Za-z0-9_]+)=([^,]+)")


def rel(path: Path) -> str:
    return path.relative_to(ROOT).as_posix()


def read_text(path: Path) -> str:
    if not path.exists():
        return ""
    return (
        path.read_text(encoding="utf-8", errors="replace")
        .replace("\x00", "")
        .replace("\r\n", "\n")
        .replace("\r", "\n")
    )


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


def read_csv_rows(path: Path) -> List[Dict[str, str]]:
    if not path.exists():
        return []
    with path.open(newline="", encoding="utf-8-sig") as f:
        return list(csv.DictReader(f))


def read_csv_one(path: Path) -> Dict[str, str]:
    rows = read_csv_rows(path)
    return rows[0] if rows else {}


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


def fnum(value: object, default: float = 0.0) -> float:
    try:
        return float(value)
    except (TypeError, ValueError):
        return default


def fmt(value: float) -> str:
    return f"{value:.6f}"


def git_head() -> str:
    try:
        return subprocess.check_output(
            ["git", "rev-parse", "--short", "HEAD"], cwd=ROOT, text=True
        ).strip()
    except (subprocess.CalledProcessError, FileNotFoundError):
        return "unknown"


def table(rows: List[Dict[str, object]], fields: List[str]) -> str:
    out = ["| " + " | ".join(fields) + " |", "| " + " | ".join("---" for _ in fields) + " |"]
    for row in rows:
        out.append("| " + " | ".join(str(row.get(field, "")).replace("|", "\\|") for field in fields) + " |")
    return "\n".join(out)


def artifact_index(paths: List[Path]) -> None:
    rows = []
    for path in paths:
        if not path.exists() or not path.is_file():
            continue
        data = path.read_bytes()
        rows.append({"path": rel(path), "bytes": str(len(data)), "sha256": hashlib.sha256(data).hexdigest()})
    write_csv(ARTIFACT, rows, ["path", "bytes", "sha256"])


def parse_runs() -> List[Dict[str, str]]:
    rows: List[Dict[str, str]] = []
    for idx, path in enumerate(sorted(RAW.glob("run_*.log"))):
        text = read_text(path)
        match = LINE_RE.search(text)
        if not match:
            rows.append({"run": str(idx), "source_log": rel(path), "parse_status": "missing"})
            continue
        kv = dict(KV_RE.findall(match.group("body")))
        kv["run"] = str(idx)
        kv["source_log"] = rel(path)
        kv["parse_status"] = "parsed"
        rows.append(kv)
    return rows


def mean(values: List[float]) -> float:
    return statistics.fmean(values) if values else 0.0


def ci95(values: List[float]) -> float:
    if len(values) < 2:
        return 0.0
    return 1.96 * statistics.stdev(values) / math.sqrt(len(values))


def append_run_log(decision: str, speedup: float, projection: float) -> None:
    run_id = "stage325-selector-transpose-resource-probe-001"
    if run_id in read_text(RUN_LOG):
        return
    fields: List[str] = []
    if RUN_LOG.exists():
        with RUN_LOG.open(newline="", encoding="utf-8-sig") as f:
            reader = csv.DictReader(f)
            fields = list(reader.fieldnames or [])
    if not fields:
        fields = [
            "run_id", "date", "git_ref", "stage", "backend", "command",
            "config", "seed", "status", "summary", "artifacts",
        ]
    row = {field: "" for field in fields}
    values = {
        "run_id": run_id,
        "date": "2026-07-05",
        "git_ref": git_head(),
        "commit_or_state": git_head(),
        "stage": "Stage 325",
        "backend": "wsl-avx512-isolated-microbench",
        "command": "STAGE325_RUNS=7 STAGE325_REPS=20000 bash scripts/run_stage325_selector_transpose_resource_probe.sh; python scripts/build_stage325_selector_transpose_resource_probe.py",
        "config": "selector-transpose coefficient-blocked isolated dense addmul probe",
        "params": "r=4; k=1; l=1; N=2048; ROWS=5; OUTS=5",
        "seed": "deterministic-xorshift64",
        "status": decision,
        "summary": f"isolated dense speedup mean={speedup:.6f}; projected full-SAB speedup={projection:.6f}",
        "artifacts": f"{rel(DOC)}; {rel(SUMMARY)}; {rel(RUNS)}; {rel(RESOURCE)}; {rel(PROOF)}",
    }
    for key, value in values.items():
        if key in row:
            row[key] = value
    with RUN_LOG.open("a", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fields, lineterminator="\n")
        writer.writerow(row)


def main() -> int:
    OUT.mkdir(parents=True, exist_ok=True)
    stage324 = read_csv_one(STAGE324_SUMMARY)
    value_rows = read_csv_rows(STAGE324_VALUE)
    dense_share = fnum(stage324.get("stage323_dense_share"))
    required_dense_speedup = fnum(stage324.get("required_dense_speedup_for_1pct_fullsab"))
    required_for_2pct = 0.0
    for row in value_rows:
        if row.get("candidate") == "selector_transposed_key_layout":
            required_for_2pct = fnum(row.get("required_dense_speedup_for_2pct_fullsab"))

    parsed_rows = parse_runs()
    good_rows = [row for row in parsed_rows if row.get("parse_status") == "parsed"]
    speeds = [fnum(row.get("speedup")) for row in good_rows]
    current_ns = [fnum(row.get("current_avg_ns")) for row in good_rows]
    packed_ns = [fnum(row.get("packed_avg_ns")) for row in good_rows]
    build_ns = [fnum(row.get("build_avg_ns")) for row in good_rows]
    max_diffs = [fnum(row.get("max_abs_diff"), 1.0) for row in good_rows]
    selector_bytes = fnum(good_rows[0].get("selector_bytes")) if good_rows else 0.0
    packed_bytes = fnum(good_rows[0].get("packed_bytes")) if good_rows else 0.0
    duplicate_bytes = fnum(good_rows[0].get("duplicate_probe_bytes")) if good_rows else 0.0

    correctness_pass = bool(good_rows) and all(diff == 0.0 for diff in max_diffs)
    speedup_mean = mean(speeds)
    speedup_ci = ci95(speeds)
    speedup_lower = speedup_mean - speedup_ci
    projected_full_speedup = (
        1.0 / (1.0 - dense_share + dense_share / speedup_mean)
        if dense_share and speedup_mean > 0.0 else 0.0
    )
    projected_lower = (
        1.0 / (1.0 - dense_share + dense_share / speedup_lower)
        if dense_share and speedup_lower > 0.0 else 0.0
    )
    replace_ratio = packed_bytes / selector_bytes if selector_bytes else 0.0
    duplicate_ratio = duplicate_bytes / selector_bytes if selector_bytes else 0.0
    build_over_kernel = mean(build_ns) / mean(packed_ns) if mean(packed_ns) else 0.0

    if not good_rows or not correctness_pass:
        decision = DECISION_FAIL
        next_stage = "stage325_repair_microbench"
    elif speedup_mean >= required_dense_speedup and projected_full_speedup >= 1.01:
        decision = DECISION_POSITIVE
        next_stage = "stage326_selector_transpose_keyview_prototype"
    else:
        decision = DECISION_NEUTRAL
        next_stage = "stage326_exact_dense_route_closeout"

    run_fields = [
        "run", "parse_status", "rows", "outputs", "N", "blocks", "reps",
        "build_reps", "current_avg_ns", "packed_avg_ns", "speedup",
        "build_avg_ns", "max_abs_diff", "selector_bytes", "packed_bytes",
        "duplicate_probe_bytes", "checksum", "source_log",
    ]
    write_csv(RUNS, parsed_rows, run_fields)

    resource_rows = [
        {
            "layout": "current_rowpoly_selector",
            "selector_bytes": f"{selector_bytes:.0f}",
            "packed_bytes": "0",
            "total_selector_storage_bytes": f"{selector_bytes:.0f}",
            "storage_ratio_vs_current": "1.000000",
            "build_avg_ns": "0",
            "build_over_candidate_kernel": "0",
            "interpretation": "current production-like row/poly layout",
        },
        {
            "layout": "replace_with_coeffblocked_transpose",
            "selector_bytes": "0",
            "packed_bytes": f"{packed_bytes:.0f}",
            "total_selector_storage_bytes": f"{packed_bytes:.0f}",
            "storage_ratio_vs_current": fmt(replace_ratio),
            "build_avg_ns": f"{mean(build_ns):.3f}",
            "build_over_candidate_kernel": fmt(build_over_kernel),
            "interpretation": "possible future key format; no duplicate selector storage after keygen rewrite",
        },
        {
            "layout": "duplicate_transposed_view_probe",
            "selector_bytes": f"{selector_bytes:.0f}",
            "packed_bytes": f"{packed_bytes:.0f}",
            "total_selector_storage_bytes": f"{duplicate_bytes:.0f}",
            "storage_ratio_vs_current": fmt(duplicate_ratio),
            "build_avg_ns": f"{mean(build_ns):.3f}",
            "build_over_candidate_kernel": fmt(build_over_kernel),
            "interpretation": "safe isolated probe shape; unacceptable as hidden production memory unless justified",
        },
    ]
    write_csv(RESOURCE, resource_rows, [
        "layout", "selector_bytes", "packed_bytes",
        "total_selector_storage_bytes", "storage_ratio_vs_current",
        "build_avg_ns", "build_over_candidate_kernel", "interpretation",
    ])

    summary_rows = [{
        "decision": decision,
        "selected_next_stage": next_stage,
        "runs": len(good_rows),
        "correctness": "PASS" if correctness_pass else "FAIL",
        "current_avg_ns_mean": f"{mean(current_ns):.3f}",
        "packed_avg_ns_mean": f"{mean(packed_ns):.3f}",
        "isolated_dense_speedup_mean": fmt(speedup_mean),
        "isolated_dense_speedup_ci95_halfwidth": fmt(speedup_ci),
        "isolated_dense_speedup_ci95_lower": fmt(speedup_lower),
        "required_dense_speedup_for_1pct_fullsab": fmt(required_dense_speedup),
        "required_dense_speedup_for_2pct_fullsab": fmt(required_for_2pct),
        "projected_fullsab_speedup_mean": fmt(projected_full_speedup),
        "projected_fullsab_speedup_ci95_lower": fmt(projected_lower),
        "duplicate_storage_ratio": fmt(duplicate_ratio),
        "replace_storage_ratio": fmt(replace_ratio),
        "build_over_candidate_kernel": fmt(build_over_kernel),
    }]
    write_csv(SUMMARY, summary_rows, [
        "decision", "selected_next_stage", "runs", "correctness",
        "current_avg_ns_mean", "packed_avg_ns_mean",
        "isolated_dense_speedup_mean", "isolated_dense_speedup_ci95_halfwidth",
        "isolated_dense_speedup_ci95_lower",
        "required_dense_speedup_for_1pct_fullsab",
        "required_dense_speedup_for_2pct_fullsab",
        "projected_fullsab_speedup_mean",
        "projected_fullsab_speedup_ci95_lower", "duplicate_storage_ratio",
        "replace_storage_ratio", "build_over_candidate_kernel",
    ])

    proof_rows = [
        {
            "gate": "G1_stage324_input",
            "status": "PASS" if stage324.get("decision") == "PASS_STAGE324_SELECT_SELECTOR_TRANSPOSE_RESOURCE_PREFLIGHT_COMPACT_REMAINS_FROZEN" else "FAIL",
            "metric": "Stage324 decision",
            "value": stage324.get("decision", ""),
            "interpretation": "Stage325 is valid only as a bounded selector-transpose probe.",
        },
        {
            "gate": "G2_microbench_parse",
            "status": "PASS" if good_rows else "FAIL",
            "metric": "parsed runs",
            "value": str(len(good_rows)),
            "interpretation": "All timing conclusions require parsed raw logs.",
        },
        {
            "gate": "G3_correctness",
            "status": "PASS" if correctness_pass else "FAIL",
            "metric": "max_abs_diff",
            "value": fmt(max(max_diffs) if max_diffs else 1.0),
            "interpretation": "Packed selector layout must be bit-exact for the same dense arithmetic order.",
        },
        {
            "gate": "G4_dense_speed_threshold",
            "status": "PASS" if speedup_mean >= required_dense_speedup else "FAIL",
            "metric": "mean dense speedup",
            "value": f"{fmt(speedup_mean)} required {fmt(required_dense_speedup)}",
            "interpretation": "Below this threshold, isolated selector locality cannot project 1% full-SAB gain.",
        },
        {
            "gate": "G5_fullsab_projection",
            "status": "PASS" if projected_full_speedup >= 1.01 else "FAIL",
            "metric": "projected full-SAB speedup",
            "value": fmt(projected_full_speedup),
            "interpretation": "Projection uses Stage322/323 dense share and is not a complete-SAB timing claim.",
        },
        {
            "gate": "G6_resource_visibility",
            "status": "PASS_REPORTED",
            "metric": "duplicate storage ratio",
            "value": fmt(duplicate_ratio),
            "interpretation": "Duplicate transposed view cost is reported separately from replace-format key layout.",
        },
        {
            "gate": "G7_stage325_decision",
            "status": decision,
            "metric": "selected next",
            "value": next_stage,
            "interpretation": "Only a positive result opens key-view prototype; otherwise close exact dense selector-layout work.",
        },
    ]
    write_csv(PROOF, proof_rows, ["gate", "status", "metric", "value", "interpretation"])

    next_rows = []
    if decision == DECISION_POSITIVE:
        next_rows.append({
            "priority": "P0",
            "stage": "stage326_selector_transpose_keyview_prototype",
            "entry_condition": decision,
            "task": "Prototype a MOSFHET key-view or replacement selector layout outside default keygen, then run isolated equality and full-SAB smoke.",
            "gate": "No production promotion until complete-SAB T_bootstrap/r A/B beats current baseline and resource/noise are reported.",
            "failure_action": "downgrade Stage325 positive to microbench-only.",
        })
        write_text(PLAN_POSITIVE, f"""# Stage326 Selector-Transpose Key-View Prototype Plan

Input decision: `{decision}`.

Goal: convert the isolated selector-transpose microbench into a bounded
MOSFHET key-view prototype without changing scalar SAB or default keygen.

Gates:

- exact equality against current MAT_TRGSW_DFT for r=4;
- key-view memory and build-time accounting;
- full SAB smoke, then repeated `T_bootstrap/r` A/B only if smoke passes;
- resource/noise report before promotion.
""")
    else:
        next_rows.append({
            "priority": "P0",
            "stage": "stage326_exact_dense_route_closeout",
            "entry_condition": decision,
            "task": "Close selector-layout exact dense work under current evidence and refresh claim boundary.",
            "gate": "Do not write key-view or hot-path code unless a new mechanism exceeds Stage324 threshold.",
            "failure_action": "return only with new proof-backed compact route or new hardware-counter mechanism.",
        })
        write_text(PLAN_CLOSE, f"""# Stage326 Exact Dense Route Closeout Plan

Input decision: `{decision}`.

Goal: close the current exact dense selector-layout route unless new evidence
is supplied. Stage325 did not meet the Stage324 dense speedup threshold needed
to project a 1% complete-SAB `T_bootstrap/r` improvement.

Tasks:

- update the final claim boundary;
- keep current exact PVW/MAT-SAB throughput evidence as the supported result;
- reopen only for a new proof-backed compact selector or a new
  hardware-counter-backed layout mechanism.
""")
    write_csv(NEXT, next_rows, ["priority", "stage", "entry_condition", "task", "gate", "failure_action"])

    write_text(COMMANDS, """# Stage325 Reproduction Commands

From WSL/Linux on an AVX512-capable CPU:

```bash
STAGE325_RUNS=7 STAGE325_REPS=20000 bash scripts/run_stage325_selector_transpose_resource_probe.sh
python3 scripts/build_stage325_selector_transpose_resource_probe.py
```

This is an isolated dense-addmul probe. It is not a complete-SAB timing claim.
""")

    report = f"""# Stage325 Selector-Transpose Resource Probe

Decision: `{decision}`.

Stage325 tests the only exact dense route still admitted by Stage324: a
coefficient-blocked selector-transposed layout. The experiment keeps the same
AVX512 complex FMA arithmetic and compares against the current row/poly
selector layout in an isolated r=4, N=2048 dense addmul microbench.

## Summary

{table(summary_rows, ["decision", "selected_next_stage", "runs", "correctness", "isolated_dense_speedup_mean", "required_dense_speedup_for_1pct_fullsab", "projected_fullsab_speedup_mean", "duplicate_storage_ratio"])}

## Resource Projection

{table(resource_rows, ["layout", "storage_ratio_vs_current", "build_avg_ns", "build_over_candidate_kernel", "interpretation"])}

## Proof Gates

{table(proof_rows, ["gate", "status", "metric", "value", "interpretation"])}

Generated from input head `{git_head()}`.
"""
    write_text(DOC, report)
    write_text(REPORT, report)
    write_text(THEORY, f"""# Stage325 Selector-Transpose Microbench Model

The coefficient-blocked selector layout changes only physical storage:

```text
current: selector[row][out][re blocks | im blocks]
packed:  selector[coeff block][row][out][re lanes | im lanes]
```

Both layouts execute the same dense r=4 arithmetic:

```text
rows = 5
outputs = 5
complex vector products per coefficient block = 25
```

Therefore Stage325 can only support a locality/resource claim, not a new
algorithmic product-count claim. The complete-SAB projection uses the measured
dense share `{fmt(dense_share)}`:

```text
full_speedup = 1 / (1 - dense_share + dense_share / dense_speedup)
```

The Stage324 threshold for a 1% complete-SAB projection is
`{fmt(required_dense_speedup)}` isolated dense speedup.
""")
    write_text(VARIANT, f"""# Stage325 Selector-Transpose Probe Variant

Status: `{decision}`.

Measured isolated dense speedup mean: `{fmt(speedup_mean)}`.
Projected complete-SAB speedup: `{fmt(projected_full_speedup)}`.

This variant remains outside production `sab_pvw_*` unless the decision is
positive and a later key-view prototype passes equality, resource, smoke, and
complete-SAB A/B gates.
""")

    append_once(GOAL, "<!-- stage325-selector-transpose-resource-probe -->", f"""<!-- stage325-selector-transpose-resource-probe -->
### Stage325 selector-transpose resource probe

`{decision}` records isolated selector-transpose dense-addmul evidence:
speedup mean `{fmt(speedup_mean)}`, projected complete-SAB speedup
`{fmt(projected_full_speedup)}`.
""")
    append_once(ROADMAP, "## Stage 325: Selector-Transpose Resource Probe", f"""## Stage 325: Selector-Transpose Resource Probe

Goal: run a concrete isolated r=4 selector-transpose dense-addmul experiment
before any SAB hot-path code.

Status: `{decision}`.
""")
    append_once(HYPOTHESES, "H325_selector_transpose_resource_probe:", f"""H325_selector_transpose_resource_probe:
  status: {decision}
  primary_metric: isolated_dense_speedup_and_projected_complete_sab_T_bootstrap_over_r
  evidence:
    - repro/stage325_selector_transpose_resource_probe/summary.csv
    - repro/stage325_selector_transpose_resource_probe/microbench_runs.csv
    - repro/stage325_selector_transpose_resource_probe/resource_projection.csv
    - repro/stage325_selector_transpose_resource_probe/proof_gate.csv
  conclusion: >
    Stage325 tests coefficient-blocked selector-transposed storage as an
    isolated exact dense-addmul locality mechanism. It does not alter scalar
    SAB or default sab_pvw_* behavior.
""")
    append_once(MANIFEST, "- stage325_selector_transpose_resource_probe:", """- stage325_selector_transpose_resource_probe:
  - `docs/stage325_selector_transpose_resource_probe.md`
  - `scripts/stage325_selector_transpose_microbench.c`
  - `scripts/run_stage325_selector_transpose_resource_probe.sh`
  - `scripts/build_stage325_selector_transpose_resource_probe.py`
  - `repro/stage325_selector_transpose_resource_probe/`
""")
    append_once(CHECKLIST, "<!-- stage325-selector-transpose-resource-probe-checklist -->", f"""<!-- stage325-selector-transpose-resource-probe-checklist -->
- [x] Stage325 records `{decision}` from isolated selector-transpose dense-addmul microbench.
""")
    append_run_log(decision, speedup_mean, projected_full_speedup)

    paths = [
        DOC, THEORY, VARIANT, PLAN_POSITIVE, PLAN_CLOSE, COMMANDS, REPORT,
        SUMMARY, RUNS, RESOURCE, PROOF, NEXT, RUNNER, BENCH_SRC, BUILDER,
        OUT / "environment.log", STAGE324_SUMMARY, STAGE324_VALUE,
    ]
    paths.extend(sorted(RAW.glob("run_*.log")))
    artifact_index(paths)
    print(decision)
    return 0 if decision != DECISION_FAIL else 1


if __name__ == "__main__":
    raise SystemExit(main())
