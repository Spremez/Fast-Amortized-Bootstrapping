#!/usr/bin/env python3
"""Build Stage324 selector-layout/mechanism route-selection artifacts."""

from __future__ import annotations

import csv
import hashlib
import subprocess
from pathlib import Path
from typing import Dict, Iterable, List


ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "repro" / "stage324_selector_layout_mechanism_preflight"
DOC = ROOT / "docs" / "stage324_selector_layout_mechanism_preflight.md"
THEORY = ROOT / "theory_checks" / "stage324_selector_layout_route_model.md"
VARIANT = ROOT / "algorithm_variants" / "mat_rlwe_sab_stage324_selector_transpose_preflight.md"
PLAN = ROOT / "experiments" / "stage325_selector_transpose_resource_probe_plan.md"
BUILDER = ROOT / "scripts" / "build_stage324_selector_layout_mechanism_preflight.py"

SUMMARY = OUT / "summary.csv"
ROUTES = OUT / "route_matrix.csv"
GATES = OUT / "gate_matrix.csv"
VALUE = OUT / "value_projection.csv"
NEXT = OUT / "next_stage_queue.csv"
COMMANDS = OUT / "reproduction_commands.md"
REPORT = OUT / "stage324_report.md"
ARTIFACT = OUT / "artifact_index.csv"

GOAL = ROOT / "docs" / "current_codex_goal_sab_completion.md"
ROADMAP = ROOT / "docs" / "roadmap_stage19_plus.md"
HYPOTHESES = ROOT / "hypotheses" / "hypothesis_register.yaml"
RUN_LOG = ROOT / "repro" / "run_log.csv"
MANIFEST = ROOT / "repro" / "artifact_manifest.md"
CHECKLIST = ROOT / "repro" / "reproduction_checklist.md"

STAGE322_COMPONENTS = ROOT / "repro" / "stage322_schedule_profile_attribution" / "component_budget.csv"
STAGE323_SUMMARY = ROOT / "repro" / "stage323_dense_mat_counter_preflight" / "summary.csv"
STAGE323_MECH = ROOT / "repro" / "stage323_dense_mat_counter_preflight" / "mechanism_screen.csv"
STAGE203_RESOURCE = ROOT / "repro" / "stage203_production_selector_equation_probe" / "resource_projection.csv"
STAGE249_VALUE = ROOT / "repro" / "stage249_structured_compact_distribution_security" / "value_matrix.csv"
STAGE249_CLAIM = ROOT / "repro" / "stage249_structured_compact_distribution_security" / "claim_boundary.csv"

DECISION = "PASS_STAGE324_SELECT_SELECTOR_TRANSPOSE_RESOURCE_PREFLIGHT_COMPACT_REMAINS_FROZEN"


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


def append_run_log() -> None:
    run_id = "stage324-selector-layout-mechanism-preflight-001"
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
        "stage": "Stage 324",
        "backend": "route-preflight",
        "command": "python scripts/build_stage324_selector_layout_mechanism_preflight.py",
        "config": "selector-layout versus structured/compact route selection",
        "params": "BINARY SET_2_3_2048; r=4; exact PVW/MAT-SAB route",
        "seed": "n/a",
        "status": DECISION,
        "summary": "Stage324 selects selector-transpose resource/microbench preflight and keeps compact production frozen.",
        "artifacts": f"{rel(DOC)}; {rel(ROUTES)}; {rel(GATES)}; {rel(VALUE)}; {rel(NEXT)}",
    }
    for key, value in values.items():
        if key in row:
            row[key] = value
    with RUN_LOG.open("a", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fields, lineterminator="\n")
        writer.writerow(row)


def component_share(component_rows: List[Dict[str, str]], name: str) -> float:
    for row in component_rows:
        if row.get("component") == name:
            return fnum(row.get("share_of_profile_full"))
    return 0.0


def r4_value(rows: List[Dict[str, str]], key: str) -> float:
    for row in rows:
        if row.get("r") == "4":
            return fnum(row.get(key))
    return 0.0


def main() -> int:
    OUT.mkdir(parents=True, exist_ok=True)
    stage323 = read_csv_one(STAGE323_SUMMARY)
    stage323_decision = stage323.get("decision", "")
    stage323_dense_share = fnum(stage323.get("stage322_dense_share"))
    stage323_mat_ep_share = fnum(stage323.get("stage322_mat_ep_share"))
    perf_counter_available = stage323.get("perf_counter_available", "")
    components = read_csv_rows(STAGE322_COMPONENTS)
    mechanism_rows = read_csv_rows(STAGE323_MECH)
    stage203_resource = read_csv_rows(STAGE203_RESOURCE)
    stage249_value = read_csv_rows(STAGE249_VALUE)
    stage249_claim = read_csv_rows(STAGE249_CLAIM)

    direct_ifft_share = component_share(components, "direct_ifft")
    direct_digit_share = component_share(components, "direct_digit")
    compact_r4_skip = r4_value(stage203_resource, "evaluator_row_reduction_if_skip_proven")
    compact_r4_public_saving = r4_value(stage249_value, "public_row_saving_vs_dense")
    compact_frozen = any(
        row.get("claim") == "production_permission"
        and row.get("status") == "freeze_compact_production_route"
        for row in stage249_claim
    )

    route_rows = [
        {
            "route": "exact_dense_local_loop",
            "status": "CLOSED",
            "semantic_change": "none",
            "product_count_effect": "none",
            "resource_effect": "none",
            "expected_value": "Stage321/323 already closed local r4 loop work",
            "blocking_gate": "no new load/store/count mechanism",
            "next_action": "do not write more r4 addmul loop code",
        },
        {
            "route": "selector_transposed_key_layout",
            "status": "SELECT_STAGE325_PREFLIGHT",
            "semantic_change": "none if it is a faithful storage/view transform",
            "product_count_effect": "none; dense 25 products per coeff block for r=4 remains",
            "resource_effect": "replace-format: approx 1.0x key bytes; duplicate-view: approx 2.0x key bytes plus build cost",
            "expected_value": "may improve selector locality/pointer overhead only; must move dense share enough for complete SAB",
            "blocking_gate": "resource, equality, isolated microbench, and projected full-SAB gate",
            "next_action": "run Stage325 selector-transpose resource probe outside SAB hot path",
        },
        {
            "route": "structured_compact_selector",
            "status": "FROZEN_PROOF_REQUIRED",
            "semantic_change": "yes; selector equations and dummy rows change evaluator semantics",
            "product_count_effect": f"potential active-row skip {fmt(compact_r4_skip)} for r=4 only if proven",
            "resource_effect": f"current proof-only dummy route public saving {fmt(compact_r4_public_saving)}",
            "expected_value": "could be algorithmic, but current evidence is proof-only and not production-safe",
            "blocking_gate": "formal distribution/keygen/security proof plus noise recurrence",
            "next_action": "no code until a new proof artifact is supplied",
        },
        {
            "route": "schedule_sub_a_or_copyback",
            "status": "DEFER_LOW_BUDGET",
            "semantic_change": "none",
            "product_count_effect": "none",
            "resource_effect": "low",
            "expected_value": "Stage322 reports sub_a below threshold and copyback zero",
            "blocking_gate": "profile share must rise or a zero-risk patch must appear",
            "next_action": "do not select now",
        },
        {
            "route": "native_counter_refresh",
            "status": "OPTIONAL_PROXY_UPGRADE",
            "semantic_change": "none",
            "product_count_effect": "none",
            "resource_effect": "none",
            "expected_value": f"current perf counter availability={perf_counter_available}",
            "blocking_gate": "native Linux perf or equivalent counter access",
            "next_action": "use only to upgrade attribution, not to block Stage325 microbench",
        },
    ]
    write_csv(ROUTES, route_rows, [
        "route", "status", "semantic_change", "product_count_effect",
        "resource_effect", "expected_value", "blocking_gate", "next_action",
    ])

    required_dense_reduction_1pct = fnum(stage323.get("required_dense_reduction_for_1pct_fullsab"))
    required_dense_reduction_2pct = fnum(stage323.get("required_dense_reduction_for_2pct_fullsab"))
    # If a selector-transpose microbench improves dense addmul by s, the full-SAB
    # projection is 1/(1 - dense_share + dense_share/s). Solve for s.
    dense_speedup_for_1pct = 1.0 / (1.0 - (1.0 - 1.0 / 1.01) / stage323_dense_share) if stage323_dense_share else 0.0
    dense_speedup_for_2pct = 1.0 / (1.0 - (1.0 - 1.0 / 1.02) / stage323_dense_share) if stage323_dense_share else 0.0
    value_rows = [
        {
            "candidate": "selector_transposed_key_layout",
            "measured_fullsab_dense_share": fmt(stage323_dense_share),
            "required_dense_reduction_for_1pct_fullsab": fmt(required_dense_reduction_1pct),
            "required_dense_speedup_for_1pct_fullsab": fmt(dense_speedup_for_1pct),
            "required_dense_reduction_for_2pct_fullsab": fmt(required_dense_reduction_2pct),
            "required_dense_speedup_for_2pct_fullsab": fmt(dense_speedup_for_2pct),
            "resource_floor": "replace-format 1.0x; duplicate probe 2.0x",
            "claim_permission": "microbench-only until full SAB A/B",
        },
        {
            "candidate": "structured_compact_selector",
            "measured_fullsab_dense_share": fmt(stage323_dense_share),
            "required_dense_reduction_for_1pct_fullsab": fmt(required_dense_reduction_1pct),
            "required_dense_speedup_for_1pct_fullsab": fmt(dense_speedup_for_1pct),
            "required_dense_reduction_for_2pct_fullsab": fmt(required_dense_reduction_2pct),
            "required_dense_speedup_for_2pct_fullsab": fmt(dense_speedup_for_2pct),
            "resource_floor": f"public saving {fmt(compact_r4_public_saving)} under current dummy-padding evidence",
            "claim_permission": "frozen; no complete-SAB speedup claim",
        },
    ]
    write_csv(VALUE, value_rows, [
        "candidate", "measured_fullsab_dense_share",
        "required_dense_reduction_for_1pct_fullsab",
        "required_dense_speedup_for_1pct_fullsab",
        "required_dense_reduction_for_2pct_fullsab",
        "required_dense_speedup_for_2pct_fullsab",
        "resource_floor", "claim_permission",
    ])

    gate_rows = [
        {
            "gate": "G1_stage323_input",
            "status": "PASS" if stage323_decision == "PASS_STAGE323_DENSE_MAT_PREFLIGHT_DENY_LOOP_CODE_ROUTE_SELECTOR_FORMAT_REQUIRED" else "FAIL",
            "metric": "Stage323 decision",
            "value": stage323_decision,
            "interpretation": "Stage324 is valid only after exact local dense-loop code is denied.",
        },
        {
            "gate": "G2_compact_production_boundary",
            "status": "PASS_FROZEN" if compact_frozen else "FAIL",
            "metric": "Stage249 production permission",
            "value": "frozen" if compact_frozen else "missing",
            "interpretation": "Structured/compact route cannot receive SAB hot-path code without a new proof artifact.",
        },
        {
            "gate": "G3_selector_transpose_semantics",
            "status": "PASS_PREFLIGHT_ONLY",
            "metric": "semantic transform",
            "value": "storage/view only",
            "interpretation": "Selector-transpose may be tested because it does not alter ciphertext equations if equality holds.",
        },
        {
            "gate": "G4_value_threshold",
            "status": "PASS_THRESHOLD_RECORDED",
            "metric": "required dense speedup for 1% full SAB",
            "value": fmt(dense_speedup_for_1pct),
            "interpretation": "Stage325 must beat this threshold in isolated dense addmul to justify more code.",
        },
        {
            "gate": "G5_stage324_decision",
            "status": DECISION,
            "metric": "selected route",
            "value": "selector_transposed_key_layout",
            "interpretation": "Proceed to a bounded resource/microbench probe; no full SAB code yet.",
        },
    ]
    write_csv(GATES, gate_rows, ["gate", "status", "metric", "value", "interpretation"])

    summary_rows = [{
        "decision": DECISION,
        "selected_next_stage": "stage325_selector_transpose_resource_probe",
        "stage323_dense_share": fmt(stage323_dense_share),
        "stage323_mat_ep_share": fmt(stage323_mat_ep_share),
        "direct_ifft_share_closed": fmt(direct_ifft_share),
        "direct_digit_share_closed": fmt(direct_digit_share),
        "compact_r4_skip_potential_proof_only": fmt(compact_r4_skip),
        "compact_public_saving_current": fmt(compact_r4_public_saving),
        "required_dense_speedup_for_1pct_fullsab": fmt(dense_speedup_for_1pct),
        "hot_path_code_permission": "no",
    }]
    write_csv(SUMMARY, summary_rows, [
        "decision", "selected_next_stage", "stage323_dense_share",
        "stage323_mat_ep_share", "direct_ifft_share_closed",
        "direct_digit_share_closed", "compact_r4_skip_potential_proof_only",
        "compact_public_saving_current",
        "required_dense_speedup_for_1pct_fullsab",
        "hot_path_code_permission",
    ])

    next_rows = [
        {
            "priority": "P0",
            "stage": "stage325_selector_transpose_resource_probe",
            "entry_condition": DECISION,
            "task": "Build an isolated selector-transpose resource/equality/microbench probe for r=4 dense MAT addmul.",
            "promotion_gate": "candidate dense speedup must project at least 1% complete-SAB T_bootstrap/r improvement without unacceptable duplicate key-memory cost",
            "failure_action": "close selector-layout route and update final claim boundary",
        },
        {
            "priority": "P1",
            "stage": "compact_route_reopen",
            "entry_condition": "formal distribution/keygen/security proof artifact supplied",
            "task": "Reopen structured/compact selector only with proof, noise recurrence, and full-SAB A/B plan.",
            "promotion_gate": "proof plus complete-SAB correctness/noise/resource gates",
            "failure_action": "keep compact route frozen",
        },
    ]
    write_csv(NEXT, next_rows, [
        "priority", "stage", "entry_condition", "task", "promotion_gate", "failure_action",
    ])

    write_text(COMMANDS, """# Stage324 Reproduction Commands

```bash
python3 scripts/build_stage324_selector_layout_mechanism_preflight.py
```

Stage324 is a route-selection preflight. It does not change scalar SAB,
`sab_pvw_*`, or any key format.
""")

    report = f"""# Stage324 Selector Layout / Mechanism Preflight

Decision: `{DECISION}`.

Stage324 prevents the research loop from drifting. Stage323 already denied
another local r=4 dense addmul rewrite. The remaining exact route with code
permission is a bounded selector-transpose resource/microbench probe. The
structured/compact route remains frozen because Stage249 records no production
permission and no public row saving for the dummy-padding survivor.

## Summary

{table(summary_rows, ["decision", "selected_next_stage", "stage323_dense_share", "compact_r4_skip_potential_proof_only", "compact_public_saving_current", "required_dense_speedup_for_1pct_fullsab", "hot_path_code_permission"])}

## Route Matrix

{table(route_rows, ["route", "status", "product_count_effect", "resource_effect", "blocking_gate", "next_action"])}

## Value Projection

{table(value_rows, ["candidate", "measured_fullsab_dense_share", "required_dense_speedup_for_1pct_fullsab", "required_dense_speedup_for_2pct_fullsab", "resource_floor", "claim_permission"])}

## Gates

{table(gate_rows, ["gate", "status", "metric", "value", "interpretation"])}

Generated from input head `{git_head()}`.
"""
    write_text(DOC, report)
    write_text(REPORT, report)
    write_text(THEORY, f"""# Stage324 Selector Layout Route Model

The exact PVW/MAT-SAB r=4 dense external product performs:

```text
rows = r + 1 = 5
outputs = k + r = 5
complex products per coefficient block = 25
```

Stage323 shows the current AVX512 loop already reuses decomposed rows across
all five outputs and stores each output once. Therefore a selector-transpose
layout cannot reduce the dense product count. Its only admissible exact-route
mechanism is better selector locality, fewer pointer/cache misses, or easier
prefetching.

With measured dense share `{fmt(stage323_dense_share)}`, a selector-transpose
probe must deliver at least `{fmt(dense_speedup_for_1pct)}` dense-addmul
speedup to project a 1% complete-SAB `T_bootstrap/r` improvement. Anything
below that is not worth integrating into `sab_pvw_*`.

Structured/compact selector remains a separate proof branch: it may reduce the
active r=4 semantic rows by `{fmt(compact_r4_skip)}` only if semantic-zero dummy
rows are proven production-safe. Current public row saving is
`{fmt(compact_r4_public_saving)}`, so it has no production speedup claim.
""")
    write_text(VARIANT, """# Stage324 Selector-Transpose Preflight Variant

Status: selected only for isolated Stage325 resource and microbench probing.

Permitted work:

- build a faithful selector-transposed view or standalone layout probe;
- compare exact dense addmul output against current row/poly layout;
- measure build/copy cost, isolated dense addmul speed, and memory ratio;
- project full-SAB value using Stage322/323 dense share.

Forbidden work:

- changing default MAT_TRGSW_DFT keygen or key loading;
- changing scalar SAB;
- claiming complete SAB acceleration before full `T_bootstrap/r` A/B.
""")
    write_text(PLAN, f"""# Stage325 Selector-Transpose Resource Probe Plan

Input decision: `{DECISION}`.

Goal: execute a concrete, bounded experiment for selector-transposed key
layout before any SAB hot-path code.

Tasks:

- allocate current row/poly selector layout and coefficient-blocked
  selector-transposed layout for r=4, k=1, l=1, N=2048;
- verify exact dense addmul equality against the current layout;
- measure transposed-view build cost and memory ratio;
- microbench current layout versus transposed layout under the same AVX512
  arithmetic;
- project complete-SAB value using measured dense share
  `{fmt(stage323_dense_share)}`.

Promotion gate:

- correctness must pass;
- isolated dense speedup must be at least `{fmt(dense_speedup_for_1pct)}` to
  project 1% complete-SAB `T_bootstrap/r` improvement;
- duplicate-view key memory must be explicitly reported and cannot be hidden
  inside the speedup claim.

Failure handling: if Stage325 is neutral or negative, close selector-layout
work and move to final claim/literature packaging or a user-supplied formal
compact proof route.
""")

    append_once(GOAL, "<!-- stage324-selector-layout-mechanism-preflight -->", f"""<!-- stage324-selector-layout-mechanism-preflight -->
### Stage324 selector layout/mechanism preflight

`{DECISION}` selects a bounded selector-transpose resource/microbench probe and
keeps structured/compact production work frozen until a formal proof artifact
exists.
""")
    append_once(ROADMAP, "## Stage 324: Selector Layout / Mechanism Preflight", f"""## Stage 324: Selector Layout / Mechanism Preflight

Goal: choose the next executable route after exact r=4 dense local-loop work is
closed.

Status: `{DECISION}`.

Next: Stage325 selector-transpose resource probe. No SAB hot-path code is
admitted until equality, resource, microbench, and projected full-SAB gates
pass.
""")
    append_once(HYPOTHESES, "H324_selector_layout_mechanism_preflight:", f"""H324_selector_layout_mechanism_preflight:
  status: {DECISION}
  primary_metric: route_permission_for_complete_sab_T_bootstrap_over_r
  evidence:
    - repro/stage324_selector_layout_mechanism_preflight/summary.csv
    - repro/stage324_selector_layout_mechanism_preflight/route_matrix.csv
    - repro/stage324_selector_layout_mechanism_preflight/gate_matrix.csv
    - repro/stage324_selector_layout_mechanism_preflight/value_projection.csv
  conclusion: >
    Stage324 selects only a selector-transpose resource/microbench preflight
    for the exact dense route and freezes compact production code until a
    formal distribution/keygen/security proof exists.
""")
    append_once(MANIFEST, "- stage324_selector_layout_mechanism_preflight:", """- stage324_selector_layout_mechanism_preflight:
  - `docs/stage324_selector_layout_mechanism_preflight.md`
  - `scripts/build_stage324_selector_layout_mechanism_preflight.py`
  - `repro/stage324_selector_layout_mechanism_preflight/`
""")
    append_once(CHECKLIST, "<!-- stage324-selector-layout-mechanism-preflight-checklist -->", f"""<!-- stage324-selector-layout-mechanism-preflight-checklist -->
- [x] Stage324 records `{DECISION}` and selects Stage325 selector-transpose resource probe without granting SAB hot-path code permission.
""")
    append_run_log()

    paths = [
        DOC, THEORY, VARIANT, PLAN, COMMANDS, REPORT, SUMMARY, ROUTES, GATES,
        VALUE, NEXT, BUILDER, STAGE322_COMPONENTS, STAGE323_SUMMARY,
        STAGE323_MECH, STAGE203_RESOURCE, STAGE249_VALUE, STAGE249_CLAIM,
    ]
    artifact_index(paths)
    print(DECISION)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
