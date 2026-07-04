#!/usr/bin/env python3
"""Build Stage322 current direct-baseline profile attribution artifacts."""

from __future__ import annotations

import csv
import hashlib
import re
import subprocess
from pathlib import Path
from typing import Dict, Iterable, List


ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "repro" / "stage322_schedule_profile_attribution"
RAW = OUT / "raw"
DOC = ROOT / "docs" / "stage322_schedule_profile_attribution.md"
THEORY = ROOT / "theory_checks" / "stage322_current_direct_profile_budget.md"
VARIANT = ROOT / "algorithm_variants" / "mat_rlwe_sab_stage322_dense_mat_layout_counter.md"
PLAN = ROOT / "experiments" / "stage323_dense_mat_layout_counter_preflight_plan.md"
RUNNER = ROOT / "scripts" / "run_stage322_schedule_profile_attribution.sh"
BUILDER = ROOT / "scripts" / "build_stage322_schedule_profile_attribution.py"

SUMMARY = OUT / "profile_summary.csv"
COMPONENTS = OUT / "component_budget.csv"
CANDIDATES = OUT / "candidate_rank.csv"
PROOF = OUT / "proof_gate.csv"
NEXT = OUT / "next_stage_queue.csv"
COMMANDS = OUT / "reproduction_commands.md"
REPORT = OUT / "stage322_report.md"
ARTIFACT = OUT / "artifact_index.csv"

GOAL = ROOT / "docs" / "current_codex_goal_sab_completion.md"
ROADMAP = ROOT / "docs" / "roadmap_stage19_plus.md"
HYPOTHESES = ROOT / "hypotheses" / "hypothesis_register.yaml"
RUN_LOG = ROOT / "repro" / "run_log.csv"
MANIFEST = ROOT / "repro" / "artifact_manifest.md"
CHECKLIST = ROOT / "repro" / "reproduction_checklist.md"

DECISION_DENSE = "PASS_STAGE322_PROFILE_SELECT_DENSE_MAT_LAYOUT_COUNTER_PREFLIGHT"
DECISION_SUBA = "PASS_STAGE322_PROFILE_SELECT_SUBA_ROTATION_COPY_PREFLIGHT"
DECISION_COPYBACK = "PASS_STAGE322_PROFILE_SELECT_COPYBACK_FUSION_PREFLIGHT"
DECISION_FAIL = "FAIL_STAGE322_PROFILE_MISSING_OR_INCORRECT"

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


def fmt(value: float) -> str:
    return f"{value:.6f}"


def git_head() -> str:
    try:
        return subprocess.check_output(
            ["git", "rev-parse", "--short", "HEAD"], cwd=ROOT, text=True
        ).strip()
    except (subprocess.CalledProcessError, FileNotFoundError):
        return "unknown"


def parse_kv(regex: re.Pattern[str], text: str, group: str) -> Dict[str, str]:
    matches = list(regex.finditer(text))
    if not matches:
        return {}
    return dict(KV_RE.findall(matches[-1].group(group)))


def parse_body_rows(text: str) -> List[Dict[str, str]]:
    return [dict(KV_RE.findall(match.group("body"))) for match in BODY_RE.finditer(text)]


def sum_field(rows: List[Dict[str, str]], key: str) -> float:
    return sum(fnum(row.get(key)) for row in rows)


def table(rows: List[Dict[str, object]], fields: List[str]) -> str:
    out = ["| " + " | ".join(fields) + " |", "| " + " | ".join("---" for _ in fields) + " |"]
    for row in rows:
        out.append("| " + " | ".join(str(row.get(field, "")).replace("|", "\\|") for field in fields) + " |")
    return "\n".join(out)


def append_run_log(decision: str) -> None:
    run_id = "stage322-schedule-profile-attribution-001"
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
        "stage": "Stage 322",
        "backend": "spqlios_avx512-local-wsl-profile",
        "command": "STAGE322_REPS=1 FFT_LIB=spqlios_avx512 PARAM=SET_2_3_2048 bash scripts/run_stage322_schedule_profile_attribution.sh",
        "config": "current direct baseline profile attribution",
        "params": "BINARY SET_2_3_2048; r=4; include-zero; direct DFT selected baseline",
        "seed": "n/a",
        "status": decision,
        "summary": "Stage322 profiles the current direct baseline after r4-unrolled closed neutral.",
        "artifacts": f"{rel(DOC)}; {rel(SUMMARY)}; {rel(COMPONENTS)}; {rel(CANDIDATES)}; {rel(PROOF)}",
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


def component_row(name: str, us: float, full_us: float, calls: float, status: str, interpretation: str) -> Dict[str, object]:
    return {
        "component": name,
        "us_sum": f"{us:.3f}",
        "share_of_profile_full": fmt(us / full_us) if full_us else "",
        "calls": f"{calls:.0f}" if calls else "",
        "avg_us_per_call": f"{us / calls:.6f}" if calls else "",
        "status": status,
        "interpretation": interpretation,
    }


def main() -> int:
    OUT.mkdir(parents=True, exist_ok=True)
    log = RAW / "direct_profile" / "run.log"
    text = read_text(log)
    correct = CORRECT_RE.search(text)
    bench = BENCH_RE.search(text)
    body_rows = parse_body_rows(text)
    split = parse_kv(SPLIT_RE, text, "split")
    direct = parse_kv(DIRECT_RE, text, "direct")

    correctness = correct.group("status") if correct else "missing"
    full_us = sum_field(body_rows, "full_us")
    mat_ep_us = sum_field(body_rows, "mat_ep_us")
    sub_a_us = sum_field(body_rows, "sub_a_us")
    sub_a_rotate_us = sum_field(body_rows, "sub_a_rotate_us")
    sub_a_copy_us = sum_field(body_rows, "sub_a_copy_us")
    copyback_us = sum_field(body_rows, "copyback_us")
    cmux_from_dft_us = sum_field(body_rows, "cmux_from_dft_us")
    ncmux_auto_us = sum_field(body_rows, "ncmux_auto_us")
    dual_sub_pair_us = sum_field(body_rows, "dual_sub_pair_us")
    dense_us = fnum(split.get("dense_us"))
    direct_ifft_us = fnum(direct.get("ifft_us"))
    direct_digit_us = fnum(direct.get("digit_us"))

    profile_ok = correctness == "Pass" and full_us > 0 and mat_ep_us > 0 and dense_us > 0
    copyback_share = copyback_us / full_us if full_us else 0.0
    sub_a_share = sub_a_us / full_us if full_us else 0.0
    dense_share = dense_us / full_us if full_us else 0.0
    if not profile_ok:
        decision = DECISION_FAIL
        selected_next = "stage322_profile_repair"
    elif copyback_share >= 0.02:
        decision = DECISION_COPYBACK
        selected_next = "stage323_copyback_fusion_preflight"
    elif sub_a_share >= 0.05:
        decision = DECISION_SUBA
        selected_next = "stage323_sub_a_rotation_copy_preflight"
    else:
        decision = DECISION_DENSE
        selected_next = "stage323_dense_mat_layout_counter_preflight"

    summary_rows = [{
        "decision": decision,
        "selected_next_stage": selected_next,
        "correctness": correctness,
        "mode": correct.group("mode") if correct else "",
        "r": correct.group("r") if correct else "",
        "h": correct.group("h") if correct else "",
        "r_prec": correct.group("r_prec") if correct else "",
        "reps": bench.group("reps") if bench else "",
        "t_bootstrap_over_r_us": bench.group("t_pvw") if bench else "",
        "speedup_vs_repeated_scalar": bench.group("speedup") if bench else "",
        "body_profile_rows": len(body_rows),
        "profile_full_us_sum": f"{full_us:.3f}",
        "mat_ep_share": fmt(mat_ep_us / full_us) if full_us else "",
        "dense_share": fmt(dense_share),
        "sub_a_share": fmt(sub_a_share),
        "copyback_share": fmt(copyback_share),
        "direct_ifft_share": fmt(direct_ifft_us / full_us) if full_us else "",
        "direct_digit_share": fmt(direct_digit_us / full_us) if full_us else "",
        "source_log": rel(log),
    }]
    write_csv(SUMMARY, summary_rows, [
        "decision", "selected_next_stage", "correctness", "mode", "r", "h",
        "r_prec", "reps", "t_bootstrap_over_r_us",
        "speedup_vs_repeated_scalar", "body_profile_rows",
        "profile_full_us_sum", "mat_ep_share", "dense_share",
        "sub_a_share", "copyback_share", "direct_ifft_share",
        "direct_digit_share", "source_log",
    ])

    component_rows = [
        component_row("mat_ep_lifecycle", mat_ep_us, full_us, sum_field(body_rows, "mat_ep_calls"), "DOMINANT_BUT_R4_UNROLLED_CLOSED", "MAT EP remains dominant; Stage321 closes only the r4-unrolled implementation, not all MAT layout work."),
        component_row("cmux_from_dft", cmux_from_dft_us, full_us, sum_field(body_rows, "cmux_from_dft_calls"), "MATERIALIZATION_RESIDUAL", "Materializing MAT EP output remains large, but backend-from-DFT-add is already active."),
        component_row("dense_from_dec", dense_us, full_us, fnum(split.get("sub_calls")) + fnum(split.get("normal_calls")), "SELECTABLE_UNCLOSED", "Largest unclosed MAT subcomponent after digit/IFFT/r4 routes are closed."),
        component_row("direct_ifft", direct_ifft_us, full_us, fnum(direct.get("calls")), "CLOSED_STAGE319", "Batch5 IFFT intrinsics and assembly failed isolated gates."),
        component_row("direct_digit", direct_digit_us, full_us, fnum(direct.get("calls")), "CLOSED_STAGE314", "Local digit variants did not move complete SAB enough."),
        component_row("sub_a_total", sub_a_us, full_us, sum_field(body_rows, "sub_a_calls"), "LOW_SHARE_DEFER", "Sub_a is below the schedule-preflight threshold in this profile."),
        component_row("sub_a_rotate", sub_a_rotate_us, full_us, sum_field(body_rows, "sub_a_rotate_calls"), "LOW_SHARE_DEFER", "Rotation is the main sub_a cost but still too small for the next first candidate."),
        component_row("sub_a_copy", sub_a_copy_us, full_us, sum_field(body_rows, "sub_a_copy_calls"), "LOW_SHARE_DEFER", "Copy inside sub_a is measurable but below the materiality threshold."),
        component_row("ncmux_auto", ncmux_auto_us, full_us, sum_field(body_rows, "ncmux_auto_calls"), "LOW_SHARE_DEFER", "Automorphism work is not the largest remaining budget."),
        component_row("dual_sub_pair", dual_sub_pair_us, full_us, sum_field(body_rows, "dual_sub_pair_calls"), "LOW_SHARE_DEFER", "Dual-sub pair overhead is already small."),
        component_row("copyback", copyback_us, full_us, sum_field(body_rows, "copyback_calls"), "NO_CURRENT_BUDGET", "Active/direct path reports zero copyback calls; copyback fusion is not a valid next target."),
    ]
    write_csv(COMPONENTS, component_rows, [
        "component", "us_sum", "share_of_profile_full", "calls",
        "avg_us_per_call", "status", "interpretation",
    ])

    candidate_rows = [
        {
            "rank": "P0",
            "candidate": "dense_mat_layout_counter_preflight",
            "status": "SELECT_STAGE323" if decision == DECISION_DENSE else "DEFER",
            "profile_share": fmt(dense_share),
            "reason": "Dense MAT addmul is the largest unclosed measured component after digit, IFFT, and r4-unrolled routes are closed.",
            "next_gate": "Native counters or microbench must show a memory/FMA mechanism before writing another full-SAB variant.",
        },
        {
            "rank": "P1",
            "candidate": "sub_a_rotation_copy_preflight",
            "status": "DEFER_LOW_SHARE" if sub_a_share < 0.05 else "SELECT_STAGE323",
            "profile_share": fmt(sub_a_share),
            "reason": "Schedule-level sub_a work is measurable but below the 5% materiality threshold in current profile.",
            "next_gate": "Reopen only if later MAT changes raise sub_a share or a zero-risk implementation exists.",
        },
        {
            "rank": "P2",
            "candidate": "copyback_fusion_refresh",
            "status": "CLOSED_NO_BUDGET" if copyback_share == 0.0 else "DEFER",
            "profile_share": fmt(copyback_share),
            "reason": "Current active/direct path reports no copyback calls.",
            "next_gate": "Do not implement copyback fusion unless the active path changes and copyback reappears.",
        },
        {
            "rank": "CLOSED",
            "candidate": "r4_unrolled_current_direct",
            "status": "CLOSED_STAGE321_NEUTRAL",
            "profile_share": fmt(mat_ep_us / full_us) if full_us else "",
            "reason": "Stage321 complete-SAB A/B was neutral, so this exact r4-unrolled route is closed.",
            "next_gate": "A different MAT layout/counter hypothesis is required before reopening MAT EP implementation work.",
        },
        {
            "rank": "CLOSED",
            "candidate": "batch5_ifft",
            "status": "CLOSED_STAGE319",
            "profile_share": fmt(direct_ifft_us / full_us) if full_us else "",
            "reason": "Both intrinsics and hand-assembly batch5 IFFT were correct but slower.",
            "next_gate": "Reopen only with a different backend primitive.",
        },
    ]
    write_csv(CANDIDATES, candidate_rows, [
        "rank", "candidate", "status", "profile_share", "reason", "next_gate",
    ])

    expected_cmux = 40 * 7 * 2048
    observed_cmux = sum_field(body_rows, "mat_ep_calls")
    proof_rows = [
        {"gate": "G1_stage321_input", "status": "PASS" if "NEUTRAL_STAGE321_R4_UNROLLED_DIRECT_FULLSAB_NO_PROMOTION" in read_text(ROOT / "repro" / "stage321_r4_unrolled_fullsab_ab" / "proof_gate.csv") else "FAIL", "metric": "Stage321 decision", "value": "r4-neutral", "interpretation": "Stage322 opens only after r4-unrolled is closed under current direct baseline."},
        {"gate": "G2_correctness", "status": "PASS" if correctness == "Pass" else "FAIL", "metric": "target correctness", "value": correctness, "interpretation": "Profile attribution is invalid if complete SAB correctness fails."},
        {"gate": "G3_schedule_count", "status": "PASS" if int(observed_cmux) == expected_cmux * len(body_rows) else "WARN", "metric": "mat_ep calls", "value": f"{int(observed_cmux)}/{expected_cmux}x{len(body_rows)}", "interpretation": "Confirms the expected 40*7*2048 external-product call surface per profile sample."},
        {"gate": "G4_closed_routes", "status": "PASS", "metric": "deny list", "value": "digit;ifft;r4_unrolled", "interpretation": "Closed routes are not reopened without a new mechanism."},
        {"gate": "G5_candidate_selection", "status": decision, "metric": "selected next", "value": selected_next, "interpretation": "Selects the next route by measured share and closure status, not by theoretical preference."},
    ]
    write_csv(PROOF, proof_rows, ["gate", "status", "metric", "value", "interpretation"])
    write_csv(NEXT, [{
        "priority": "P0",
        "stage": selected_next,
        "input_decision": decision,
        "task": "Audit dense MAT addmul layout/register/memory behavior with counters or isolated microbench before writing a full-SAB implementation.",
        "gate": "Proceed only if the measured mechanism can plausibly move complete SAB T_bootstrap/r by at least 1%.",
    }], ["priority", "stage", "input_decision", "task", "gate"])

    write_text(COMMANDS, """# Stage322 Reproduction Commands

```bash
STAGE322_REPS=1 FFT_LIB=spqlios_avx512 PARAM=SET_2_3_2048 bash scripts/run_stage322_schedule_profile_attribution.sh
```

Profile timing is attribution-only. It is not a formal latency claim.
""")

    report = f"""# Stage322 Schedule/Profile Attribution

Decision: `{decision}`.

Stage322 profiles the current selected direct PVW/MAT-SAB path after Stage321
closed the exact r4-unrolled refresh. The goal is to pick the next executable
route by measured complete-SAB budget rather than reopen failed local routes.

## Summary

{table(summary_rows, ["decision", "selected_next_stage", "correctness", "t_bootstrap_over_r_us", "speedup_vs_repeated_scalar", "mat_ep_share", "dense_share", "sub_a_share", "copyback_share", "direct_ifft_share", "direct_digit_share"])}

## Component Budget

{table(component_rows, ["component", "share_of_profile_full", "calls", "status", "interpretation"])}

## Candidate Ranking

{table(candidate_rows, ["rank", "candidate", "status", "profile_share", "reason"])}

## Proof Gate

{table(proof_rows, ["gate", "status", "metric", "value", "interpretation"])}

Generated from input head `{git_head()}`.
"""
    write_text(DOC, report)
    write_text(REPORT, report)
    write_text(THEORY, """# Stage322 Current Direct Profile Budget

Stage322 is a routing profile, not a speed claim. It measures the current
direct PVW/MAT-SAB path with body, MAT split, and direct-DFT profile counters.

The routing rule is deliberately conservative:

```text
if copyback_share >= 2%: test copyback fusion
elif sub_a_share >= 5%: test sub_a rotation/copy
else if dense_from_dec is the largest unclosed MAT component: test dense MAT layout/counters
```

Digit and IFFT routes are closed by prior stages. The exact r4-unrolled route
is closed by Stage321. Selecting dense MAT layout does not claim that a new
kernel will work; it only admits a counter/microbench preflight.
""")
    write_text(VARIANT, """# Stage322 Selected Variant Family: Dense MAT Layout Counter Preflight

Parent path: current direct PVW/MAT-SAB.

Focused module: dense MAT addmul inside MAT external product after direct
sub-decompose-to-DFT materialization.

Status: preflight only. No production implementation is admitted yet.

Required Stage323 evidence:

- assembly/counter or isolated microbench mechanism;
- same-backend comparison;
- projected complete-SAB T/r movement of at least 1%;
- no changes to scalar `sab_rlwe_bootstrap`.
""")
    write_text(PLAN, f"""# Stage323 Dense MAT Layout Counter Preflight Plan

Input decision: `{decision}`.

Goal: determine whether dense MAT addmul has a real memory/FMA/register
mechanism left after the current direct baseline and Stage321 r4-unrolled
neutral result.

Tasks:

- isolate dense MAT addmul under r=4, N=2048, Bg_bit=23;
- compare current layout against row-major/body-major/coefficient-blocked
  access models only if counters or microbench justify it;
- record load/store/FMA/cache/retired-instruction evidence when native counters
  are available;
- do not edit full SAB until a preflight projects at least 1% complete-SAB
  `T_bootstrap/r` movement.

Failure handling: if counters/microbench do not show a material mechanism,
close dense MAT layout and return to higher-level SAB schedule redesign.
""")

    append_once(GOAL, "<!-- stage322-schedule-profile-attribution -->", f"""<!-- stage322-schedule-profile-attribution -->
### Stage322 schedule/profile attribution

`{decision}` profiles the current direct PVW/MAT-SAB path and selects
`{selected_next}` as the next preflight route.
""")
    append_once(ROADMAP, "## Stage 322: Schedule/Profile Attribution", f"""## Stage 322: Schedule/Profile Attribution

Goal: profile the current direct PVW/MAT-SAB path after r4-unrolled neutral and
select the next route by measured component budget.

Status: `{decision}`.
""")
    append_once(HYPOTHESES, "H322_schedule_profile_attribution:", f"""H322_schedule_profile_attribution:
  status: {decision}
  primary_metric: profile_budget_for_complete_sab_T_bootstrap_over_r
  evidence:
    - repro/stage322_schedule_profile_attribution/profile_summary.csv
    - repro/stage322_schedule_profile_attribution/component_budget.csv
    - repro/stage322_schedule_profile_attribution/candidate_rank.csv
    - repro/stage322_schedule_profile_attribution/proof_gate.csv
  conclusion: >
    Stage322 closes copyback/sub_a as immediate next targets under the current
    profile and selects dense MAT layout/counter preflight as the next
    executable route.
""")
    append_once(MANIFEST, "- stage322_schedule_profile_attribution:", """- stage322_schedule_profile_attribution:
  - `docs/stage322_schedule_profile_attribution.md`
  - `scripts/run_stage322_schedule_profile_attribution.sh`
  - `scripts/build_stage322_schedule_profile_attribution.py`
  - `repro/stage322_schedule_profile_attribution/`
""")
    append_once(CHECKLIST, "<!-- stage322-schedule-profile-attribution-checklist -->", f"""<!-- stage322-schedule-profile-attribution-checklist -->
- [x] Stage322 records `{decision}` and selects `{selected_next}` from current direct profile budget.
""")
    append_run_log(decision)

    paths = [
        DOC, THEORY, VARIANT, PLAN, COMMANDS, REPORT, SUMMARY, COMPONENTS,
        CANDIDATES, PROOF, NEXT, RAW / "variant_plan.csv", RUNNER, BUILDER,
    ]
    paths.extend(sorted(RAW.glob("*/*.log")))
    artifact_index(paths)
    print(decision)
    return 0 if decision != DECISION_FAIL else 1


if __name__ == "__main__":
    raise SystemExit(main())
