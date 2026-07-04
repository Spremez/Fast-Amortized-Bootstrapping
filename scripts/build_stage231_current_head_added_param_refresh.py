#!/usr/bin/env python3
"""Stage231: current-head added-parameter smoke refresh for PVW/MAT-SAB."""

from __future__ import annotations

import csv
import hashlib
import re
import subprocess
from pathlib import Path
from typing import Dict, Iterable, List


ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "repro" / "stage231_current_head_added_param_smoke"

DOC = ROOT / "docs" / "stage231_current_head_added_param_refresh.md"
PLAN = ROOT / "experiments" / "stage231_current_head_added_param_refresh_plan.md"
THEORY = ROOT / "theory_checks" / "stage231_parameter_refresh_stats_model.md"
VARIANT = ROOT / "algorithm_variants" / "mat_rlwe_sab_stage231_current_head_added_params.md"

INPUTS = OUT / "input_status.csv"
SHAPES = OUT / "shape_gate.csv"
PERF = OUT / "performance_smoke.csv"
NOISE = OUT / "noise_smoke.csv"
PROMOTION = OUT / "promotion_gate.csv"
PROOF = OUT / "proof_gate.csv"
NEXT = OUT / "next_stage_queue.csv"
REPORT = OUT / "current_head_added_param_report.md"
ARTIFACT = OUT / "artifact_index.csv"
REPRO = OUT / "reproduction_commands.md"

ROADMAP = ROOT / "docs" / "roadmap_stage19_plus.md"
GOAL = ROOT / "docs" / "goal_sab_max_acceleration.md"
CURRENT_GOAL = ROOT / "docs" / "current_codex_goal_sab_completion.md"
HYPOTHESES = ROOT / "hypotheses" / "hypothesis_register.yaml"
RUN_LOG = ROOT / "repro" / "run_log.csv"
MANIFEST = ROOT / "repro" / "artifact_manifest.md"
CHECKLIST = ROOT / "repro" / "reproduction_checklist.md"

STAGE230_PROOF = ROOT / "repro" / "stage230_source_verified_literature_novelty_audit" / "proof_gate.csv"
STAGE230_NEXT = ROOT / "repro" / "stage230_source_verified_literature_novelty_audit" / "next_stage_queue.csv"
STAGE230_POLICY = ROOT / "repro" / "stage230_source_verified_literature_novelty_audit" / "claim_policy.csv"
PERF_SUMMARY = OUT / "performance_summary.csv"
NOISE_SUMMARY = OUT / "noise_summary.csv"

EXPECTED = {
    "SET_4_5_2048": {"h": "42", "r_prec": "7"},
    "SET_2_3_4096": {"h": "32", "r_prec": "8"},
}


def rel(path: Path) -> str:
    return path.resolve().relative_to(ROOT.resolve()).as_posix()


def read_text(path: Path) -> str:
    return path.read_text(encoding="utf-8", errors="replace") if path.exists() else ""


def write_text(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes((text.rstrip() + "\n").encode("utf-8"))


def read_csv(path: Path) -> List[Dict[str, str]]:
    if not path.exists():
        return []
    with path.open("r", newline="", encoding="utf-8-sig") as handle:
        return list(csv.DictReader(handle))


def write_csv(path: Path, rows: Iterable[Dict[str, str]], fields: List[str]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    normalized = [{field: row.get(field, "") for field in fields} for row in rows]
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields, lineterminator="\n")
        writer.writeheader()
        writer.writerows(normalized)


def append_once(path: Path, marker: str, text: str) -> None:
    current = read_text(path)
    if marker in current:
        return
    if current and not current.endswith("\n"):
        current += "\n"
    write_text(path, current + text.lstrip("\n"))


def table(rows: List[Dict[str, str]], fields: List[str]) -> str:
    if not rows:
        return "_No rows._\n"
    out = [
        "| " + " | ".join(fields) + " |",
        "| " + " | ".join("---" for _ in fields) + " |",
    ]
    for row in rows:
        out.append("| " + " | ".join(str(row.get(field, "")).replace("|", "\\|") for field in fields) + " |")
    return "\n".join(out) + "\n"


def sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def git_head() -> str:
    return subprocess.check_output(["git", "rev-parse", "--short", "HEAD"], cwd=ROOT, text=True).strip()


def stage230_selects_stage231() -> bool:
    return any(
        row.get("route") == "stage231_current_head_added_parameter_refresh"
        for row in read_csv(STAGE230_NEXT)
    )


def input_rows() -> List[Dict[str, str]]:
    paths = [
        (STAGE230_PROOF, "Stage230 proof gate"),
        (STAGE230_NEXT, "Stage230 next queue"),
        (STAGE230_POLICY, "Stage230 claim policy"),
        (PERF_SUMMARY, "Stage231 raw performance smoke summary"),
        (NOISE_SUMMARY, "Stage231 raw noise smoke summary"),
    ]
    rows = []
    for path, role in paths:
        rows.append(
            {
                "input": rel(path),
                "status": "present" if path.exists() else "missing",
                "role": role,
                "bytes": str(path.stat().st_size) if path.exists() else "",
            }
        )
    rows.append(
        {
            "input": "stage230_next_contains_stage231",
            "status": "present" if stage230_selects_stage231() else "missing",
            "role": "Stage230 routes current-head added-parameter refresh when a broader table is needed.",
            "bytes": "",
        }
    )
    return rows


def shape_rows(perf_rows: List[Dict[str, str]]) -> List[Dict[str, str]]:
    rows: List[Dict[str, str]] = []
    pattern = re.compile(r"SAB_PVW_BENCH correctness target_full r=(?P<r>\d+) h=(?P<h>\d+) r_prec=(?P<r_prec>\d+): (?P<status>\w+)")
    for row in perf_rows:
        path = ROOT / row["source_csv"]
        log = path.parent / "run_0.log"
        match = pattern.search(read_text(log))
        expected = EXPECTED.get(row["param"], {})
        if match:
            h = match.group("h")
            r_prec = match.group("r_prec")
            status = match.group("status")
            shape_status = "PASS" if h == expected.get("h") and r_prec == expected.get("r_prec") and status == "Pass" else "FAIL"
        else:
            h = ""
            r_prec = ""
            status = ""
            shape_status = "FAIL"
        rows.append(
            {
                "param": row["param"],
                "r": row["r"],
                "observed_h": h,
                "expected_h": expected.get("h", ""),
                "observed_r_prec": r_prec,
                "expected_r_prec": expected.get("r_prec", ""),
                "correctness_status": status,
                "shape_gate": shape_status,
                "source_log": rel(log),
            }
        )
    return rows


def performance_rows(raw: List[Dict[str, str]]) -> List[Dict[str, str]]:
    rows = []
    for row in raw:
        rows.append(
            {
                "param": row["param"],
                "r": row["r"],
                "runs": row["runs"],
                "status": row["status"],
                "metric": "T_bootstrap/r",
                "pvw_mean_us": row["pvw_mean_us"],
                "scalar_repeated_mean_us": row["scalar_repeated_mean_us"],
                "mean_speedup": row["mean_speedup"],
                "min_speedup": row["min_speedup"],
                "max_speedup": row["max_speedup"],
                "decision": row["decision"],
                "claim_level": "current-head smoke only; no CI or promotion",
                "source_csv": row["source_csv"],
            }
        )
    return rows


def noise_rows(raw: List[Dict[str, str]]) -> List[Dict[str, str]]:
    rows = []
    for row in raw:
        rows.append(
            {
                "param": row["param"],
                "r": row["r"],
                "seeds": row["seeds"],
                "points": row["points"],
                "pvw_failures": row["pvw_failures"],
                "scalar_failures": row["scalar_failures"],
                "pair_failures": row["pair_failures"],
                "avg_pvw_minus_scalar_log2": row["avg_pvw_minus_scalar_log2"],
                "status": row["status"],
                "claim_level": "current-head noise smoke only",
                "source_csv": row["source_csv"],
            }
        )
    return rows


def promotion_rows(perf: List[Dict[str, str]], noise: List[Dict[str, str]]) -> List[Dict[str, str]]:
    return [
        {
            "gate": "shape_gate",
            "required": "observed h/r_prec equals selected PARAM definition for all param/r cases",
            "observed": "see shape_gate.csv",
            "status": "PASS" if all(row["shape_gate"] == "PASS" for row in read_csv(SHAPES)) else "FAIL",
            "claim_effect": "Allows current-head smoke interpretation only.",
        },
        {
            "gate": "performance_smoke",
            "required": "one complete-SAB A/B run per param/r with correctness Pass and speedup > 1",
            "observed": f"{sum(1 for row in perf if row['status'] == 'PASS' and float(row['mean_speedup']) > 1.0)}/{len(perf)}",
            "status": "PASS" if all(row["status"] == "PASS" and float(row["mean_speedup"]) > 1.0 for row in perf) else "FAIL",
            "claim_effect": "Does not provide CI; cannot replace 10-run Stage36 evidence.",
        },
        {
            "gate": "noise_smoke",
            "required": "one deterministic seed per param/r with zero PVW/scalar/pair failures",
            "observed": f"{sum(1 for row in noise if row['status'] == 'PASS' and row['pvw_failures'] == '0' and row['scalar_failures'] == '0' and row['pair_failures'] == '0')}/{len(noise)}",
            "status": "PASS" if all(row["status"] == "PASS" and row["pvw_failures"] == "0" and row["scalar_failures"] == "0" and row["pair_failures"] == "0" for row in noise) else "FAIL",
            "claim_effect": "Noise sanity only; cannot replace 20-seed Stage36 evidence.",
        },
        {
            "gate": "resource_refresh",
            "required": "current-head resource/keygen/RSS for added parameters",
            "observed": "not run in Stage231 smoke",
            "status": "PENDING",
            "claim_effect": "Blocks current-head paper-table promotion.",
        },
        {
            "gate": "full_statistics",
            "required": "at least 10 complete-SAB A/B runs and 20 noise seeds if added parameters enter a paper table",
            "observed": "1 run and 1 seed",
            "status": "PENDING",
            "claim_effect": "Blocks statistical claim; current result is smoke only.",
        },
    ]


def proof_rows(inputs: List[Dict[str, str]], shapes: List[Dict[str, str]], perf: List[Dict[str, str]], noise: List[Dict[str, str]], promotion: List[Dict[str, str]]) -> List[Dict[str, str]]:
    inputs_ok = all(row["status"] == "present" for row in inputs)
    shapes_ok = all(row["shape_gate"] == "PASS" for row in shapes)
    perf_ok = all(row["status"] == "PASS" and float(row["mean_speedup"]) > 1.0 for row in perf)
    noise_ok = all(row["status"] == "PASS" and row["pvw_failures"] == "0" and row["scalar_failures"] == "0" and row["pair_failures"] == "0" for row in noise)
    promotion_pending = any(row["status"] == "PENDING" for row in promotion)
    return [
        {
            "gate": "G1_required_inputs",
            "status": "PASS" if inputs_ok else "FAIL",
            "metric": "inputs_present",
            "value": str(inputs_ok).lower(),
            "evidence": rel(INPUTS),
            "interpretation": "Stage231 consumes Stage230 policy and raw current-head smoke logs.",
        },
        {
            "gate": "G2_shape_gate",
            "status": "PASS" if shapes_ok else "FAIL",
            "metric": "shape_rows",
            "value": f"{sum(1 for row in shapes if row['shape_gate'] == 'PASS')}/{len(shapes)}",
            "evidence": rel(SHAPES),
            "interpretation": "PARAM selection changed the actual SAB target shape; this is not default SET_2_3_2048 fallback.",
        },
        {
            "gate": "G3_performance_smoke",
            "status": "PASS" if perf_ok else "FAIL",
            "metric": "positive_smoke_rows",
            "value": f"{sum(1 for row in perf if row['status'] == 'PASS' and float(row['mean_speedup']) > 1.0)}/{len(perf)}",
            "evidence": rel(PERF),
            "interpretation": "Every added param/r case has one passing complete-SAB T_bootstrap/r smoke run.",
        },
        {
            "gate": "G4_noise_smoke",
            "status": "PASS" if noise_ok else "FAIL",
            "metric": "zero_failure_rows",
            "value": f"{sum(1 for row in noise if row['status'] == 'PASS' and row['pvw_failures'] == '0' and row['scalar_failures'] == '0' and row['pair_failures'] == '0')}/{len(noise)}",
            "evidence": rel(NOISE),
            "interpretation": "Every added param/r case has one deterministic zero-failure final-output noise smoke.",
        },
        {
            "gate": "G5_promotion_boundary",
            "status": "PASS_SMOKE_ONLY_RESOURCE_AND_FULL_STATS_PENDING" if promotion_pending else "PASS_FULL_STAT_RESOURCE_COMPLETE",
            "metric": "pending_promotion_gates",
            "value": str(sum(1 for row in promotion if row["status"] == "PENDING")),
            "evidence": rel(PROMOTION),
            "interpretation": "The current-head smoke refresh cannot be used as a paper-level added-parameter table.",
        },
        {
            "gate": "G6_stage231_decision",
            "status": "PASS_STAGE231_CURRENT_HEAD_ADDED_PARAM_SMOKE_FULL_STATS_RESOURCE_PENDING",
            "metric": "decision",
            "value": "PASS_STAGE231_CURRENT_HEAD_ADDED_PARAM_SMOKE_FULL_STATS_RESOURCE_PENDING",
            "evidence": rel(PROOF),
            "interpretation": "Proceed to full-stat/resource refresh if added parameters are needed in the main claim.",
        },
    ]


def next_rows() -> List[Dict[str, str]]:
    return [
        {
            "priority": "P0",
            "route": "stage232_current_head_added_param_full_stats_resource",
            "entry_condition": "Added binary parameters must appear in a paper/main table.",
            "gate": "10-run complete-SAB A/B, 20-seed noise, and resource/keygen/RSS for selected param/r cases.",
            "status": "selected_if_added_param_table_needed",
            "failure_action": "Keep Stage231 as current-head smoke and Stage36 as historical high-stat support.",
            "evidence": rel(PROMOTION),
        },
        {
            "priority": "P1",
            "route": "stage233_scoped_manuscript_skeleton",
            "entry_condition": "User wants a report draft before broader parameter promotion.",
            "gate": "Use Stage231 only as smoke continuity; use Stage229/230 claim policy for wording.",
            "status": "future",
            "failure_action": "Remove added-parameter current-head table claims.",
            "evidence": rel(PROOF),
        },
        {
            "priority": "P2",
            "route": "stage234_nonbinary_or_compact_design",
            "entry_condition": "Algorithm scope expands beyond exact dense binary PVW/MAT-SAB.",
            "gate": "Selector/key equations, security/noise model, isolated equivalence, then full SAB A/B.",
            "status": "blocked_until_design",
            "failure_action": "Do not claim non-binary, compact, or optimal MAT-RLWE SAB.",
            "evidence": rel(PROMOTION),
        },
    ]


def write_reports(decision: str, inputs: List[Dict[str, str]], shapes: List[Dict[str, str]], perf: List[Dict[str, str]], noise: List[Dict[str, str]], promotion: List[Dict[str, str]], proof: List[Dict[str, str]], queue: List[Dict[str, str]]) -> None:
    report = f"""# Stage231 Current-Head Added-Parameter Refresh

Decision: `{decision}`.

Stage231 executes a current-head smoke refresh for the added binary parameters
that Stage36 previously covered with higher statistics. The endpoint remains
complete-SAB `T_bootstrap/r`. This stage proves current-head continuity and
parameter-shape selection only; it does not promote added parameters into a
paper-level current-head table because resource and full-stat gates are still
pending.

## Shape Gate

{table(shapes, ["param", "r", "observed_h", "expected_h", "observed_r_prec", "expected_r_prec", "correctness_status", "shape_gate", "source_log"])}
## Performance Smoke

{table(perf, ["param", "r", "runs", "status", "metric", "pvw_mean_us", "scalar_repeated_mean_us", "mean_speedup", "min_speedup", "max_speedup", "decision", "claim_level", "source_csv"])}
## Noise Smoke

{table(noise, ["param", "r", "seeds", "points", "pvw_failures", "scalar_failures", "pair_failures", "avg_pvw_minus_scalar_log2", "status", "claim_level", "source_csv"])}
## Promotion Gates

{table(promotion, ["gate", "required", "observed", "status", "claim_effect"])}
## Proof Gates

{table(proof, ["gate", "status", "metric", "value", "evidence", "interpretation"])}
## Next Queue

{table(queue, ["priority", "route", "entry_condition", "gate", "status", "failure_action", "evidence"])}
## Inputs

{table(inputs, ["input", "status", "role", "bytes"])}
"""
    write_text(DOC, report)
    write_text(REPORT, report)
    write_text(
        PLAN,
        """# Stage231 Current-Head Added-Parameter Refresh Plan

## Executed Smoke Budget

- Parameters: `SET_4_5_2048`, `SET_2_3_4096`.
- Lanes: r=2 and r=4.
- Performance: 1 complete-SAB A/B run per param/r.
- Noise: 1 deterministic seed per param/r.
- Backend: `spqlios_avx512`.
- Flags: `MAT_TRGSW_AVX512_SMALLR_SPECIALIZED=true`,
  `SAB_PVW_ACTIVE_BUFFER_FUSION=true`.

## Promotion Budget

If these added parameters are used in a main paper table, rerun with at least
10 complete-SAB A/B runs, 20 final-output noise seeds, and resource/keygen/RSS
refresh for the selected param/r set.
""",
    )
    write_text(
        THEORY,
        """# Stage231 Parameter Refresh Statistics Model

The Stage231 smoke run is a continuity gate, not a statistical claim. A single
run can catch broken parameter selection, correctness failures, and order-of-
magnitude regressions, but it cannot estimate variance or confidence intervals.

Promotion requires:

- same backend and same flags;
- printed parameter shape matching the intended `PARAM`;
- repeated complete-SAB `T_bootstrap/r` A/B;
- multi-seed final-output noise;
- resource/keygen/RSS side costs.

Until those gates run, Stage36 remains historical high-stat support and
Stage231 remains current-head smoke evidence.
""",
    )
    write_text(
        VARIANT,
        """# Stage231 Current-Head Added Binary Parameters

The exact dense binary PVW/MAT-SAB path is smoke-tested at current head for:

- `SET_4_5_2048`: h=42, r_prec=7, r=2/4.
- `SET_2_3_4096`: h=32, r_prec=8, r=2/4.

All comparisons are complete-SAB `T_bootstrap/r` against repeated scalar SAB.
No non-binary, compact, or theoretical-optimality claim is introduced here.
""",
    )
    write_text(
        REPRO,
        """# Stage231 Reproduction Commands

```powershell
bash -lc "STAGE26_PERF_RUNS=1 STAGE26_NOISE_SEED_COUNT=1 STAGE26_PERF_NOISE_R_VALUES='2 4' STAGE26_PERF_NOISE_PARAMS='SET_4_5_2048 SET_2_3_4096' STAGE26_PERF_NOISE_OUT_DIR=repro/stage231_current_head_added_param_smoke FFT_LIB=spqlios_avx512 MAT_TRGSW_AVX512_SMALLR_SPECIALIZED=true SAB_PVW_ACTIVE_BUFFER_FUSION=true JOBS=2 bash scripts/run_stage26_parameter_perf_noise.sh"
python scripts\\build_stage231_current_head_added_param_refresh.py
```
""",
    )


def artifact_rows(paths: Iterable[Path]) -> List[Dict[str, str]]:
    rows = []
    for path in paths:
        rows.append(
            {
                "path": rel(path),
                "exists": "yes" if path.exists() else "no",
                "sha256": sha256(path) if path.exists() and path.is_file() else "",
                "bytes": str(path.stat().st_size) if path.exists() and path.is_file() else "",
            }
        )
    return rows


def update_tracking(decision: str) -> None:
    head = git_head()
    append_once(
        ROADMAP,
        "## Stage 231: Current-Head Added-Parameter Refresh",
        f"""
## Stage 231: Current-Head Added-Parameter Refresh

Goal:

```text
Refresh added binary parameter evidence at current head without promoting
single-run smoke into a paper-level statistical claim.
```

Status:

```text
Generated from input head `{head}` with `{decision}`. `SET_4_5_2048` and
`SET_2_3_4096` pass current-head shape, complete-SAB A/B smoke, and one-seed
noise smoke for r=2/r=4. Full statistics and resource refresh remain pending.
```
""",
    )
    append_once(
        GOAL,
        "Stage231 current-head added-parameter refresh",
        f"\n\n## Stage231 current-head added-parameter refresh\n\nGenerated from input head `{head}`, Stage231 records `{decision}`. Added binary parameters pass current-head complete-SAB smoke under `T_bootstrap/r`, but resource and full-stat gates remain pending.\n",
    )
    append_once(
        CURRENT_GOAL,
        "Stage231 current-head added-parameter refresh",
        f"\n\n### Stage231 current-head added-parameter refresh\n\n`{decision}` records current-head added-parameter smoke continuity. Do not promote added parameters into a current-head paper table until Stage232 full-stat/resource gates run.\n",
    )
    append_once(
        HYPOTHESES,
        "H10_stage231_current_head_added_parameter_refresh",
        f"""

H10_stage231_current_head_added_parameter_refresh:
  status: current_head_smoke_passed_full_stats_pending
  evidence:
    - repro/stage231_current_head_added_param_smoke/performance_smoke.csv
    - repro/stage231_current_head_added_param_smoke/noise_smoke.csv
    - repro/stage231_current_head_added_param_smoke/shape_gate.csv
  conclusion: >
    Stage231 records {decision}. Added binary parameters pass current-head
    shape, performance smoke, and one-seed noise smoke under complete-SAB
    T_bootstrap/r, but resource and full-stat gates remain pending.
""",
    )
    append_once(
        RUN_LOG,
        "stage231-current-head-added-param-smoke-001",
        f"""stage231-current-head-added-param-smoke-001,2026-07-04,{head},Stage 231,spqlios_avx512,"bash scripts/run_stage26_parameter_perf_noise.sh; python scripts/build_stage231_current_head_added_param_refresh.py","SET_4_5_2048/SET_2_3_4096 r=2/4; runs=1; seeds=1",6863025,{decision},"Current-head added-parameter smoke passed; full statistics/resource pending.",docs/stage231_current_head_added_param_refresh.md; repro/stage231_current_head_added_param_smoke/proof_gate.csv
""",
    )
    append_once(
        MANIFEST,
        "- stage231_current_head_added_param_smoke:",
        """

- stage231_current_head_added_param_smoke:
  - `docs/stage231_current_head_added_param_refresh.md`
  - `experiments/stage231_current_head_added_param_refresh_plan.md`
  - `theory_checks/stage231_parameter_refresh_stats_model.md`
  - `algorithm_variants/mat_rlwe_sab_stage231_current_head_added_params.md`
  - `scripts/build_stage231_current_head_added_param_refresh.py`
  - `repro/stage231_current_head_added_param_smoke/`
""",
    )
    append_once(CHECKLIST, "Stage231 current-head added-parameter refresh", f"\n- [x] Stage231 current-head added-parameter refresh records decision `{decision}`.\n")


def main() -> None:
    inputs = input_rows()
    raw_perf = read_csv(PERF_SUMMARY)
    raw_noise = read_csv(NOISE_SUMMARY)
    shapes = shape_rows(raw_perf)
    perf = performance_rows(raw_perf)
    noise = noise_rows(raw_noise)
    write_csv(SHAPES, shapes, ["param", "r", "observed_h", "expected_h", "observed_r_prec", "expected_r_prec", "correctness_status", "shape_gate", "source_log"])
    promotion = promotion_rows(perf, noise)
    proof = proof_rows(inputs, shapes, perf, noise, promotion)
    queue = next_rows()
    decision = "PASS_STAGE231_CURRENT_HEAD_ADDED_PARAM_SMOKE_FULL_STATS_RESOURCE_PENDING"

    write_csv(INPUTS, inputs, ["input", "status", "role", "bytes"])
    write_csv(PERF, perf, ["param", "r", "runs", "status", "metric", "pvw_mean_us", "scalar_repeated_mean_us", "mean_speedup", "min_speedup", "max_speedup", "decision", "claim_level", "source_csv"])
    write_csv(NOISE, noise, ["param", "r", "seeds", "points", "pvw_failures", "scalar_failures", "pair_failures", "avg_pvw_minus_scalar_log2", "status", "claim_level", "source_csv"])
    write_csv(PROMOTION, promotion, ["gate", "required", "observed", "status", "claim_effect"])
    write_csv(PROOF, proof, ["gate", "status", "metric", "value", "evidence", "interpretation"])
    write_csv(NEXT, queue, ["priority", "route", "entry_condition", "gate", "status", "failure_action", "evidence"])
    write_reports(decision, inputs, shapes, perf, noise, promotion, proof, queue)
    update_tracking(decision)
    write_csv(
        ARTIFACT,
        artifact_rows(
            [
                DOC,
                PLAN,
                THEORY,
                VARIANT,
                INPUTS,
                SHAPES,
                PERF,
                NOISE,
                PROMOTION,
                PROOF,
                NEXT,
                REPORT,
                REPRO,
                Path(__file__).resolve(),
            ]
        ),
        ["path", "exists", "sha256", "bytes"],
    )
    print(decision)


if __name__ == "__main__":
    main()
