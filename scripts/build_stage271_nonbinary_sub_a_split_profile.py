#!/usr/bin/env python3
"""Build Stage271 non-binary sub_a split-profile artifacts."""

from __future__ import annotations

import csv
import hashlib
import re
import subprocess
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
REPRO = ROOT / "repro" / "stage271_nonbinary_sub_a_split_profile"
RAW = REPRO / "raw"
DOC = ROOT / "docs" / "stage271_nonbinary_sub_a_split_profile.md"
CURRENT_GOAL = ROOT / "docs" / "current_codex_goal_sab_completion.md"
HYPOTHESES = ROOT / "hypotheses" / "hypothesis_register.yaml"
RUN_LOG = ROOT / "repro" / "run_log.csv"
MANIFEST = ROOT / "repro" / "artifact_manifest.md"
CHECKLIST = ROOT / "repro" / "reproduction_checklist.md"

SUMMARY_RE = re.compile(
    r"SAB_PVW_NONBINARY_BENCH summary target_full "
    r"mode=(?P<mode>\S+) r=(?P<r>\d+) reps=(?P<reps>\d+) "
    r"pvw_avg_us=(?P<pvw_avg_us>[0-9.]+).*?"
    r"scalar_repeated_avg_us=(?P<scalar_repeated_avg_us>[0-9.]+).*?"
    r"speedup_vs_scalar_repeated=(?P<speedup_vs_scalar_repeated>[0-9.]+)x.*?"
    r"t_bootstrap_over_r_pvw_us=(?P<t_bootstrap_over_r_pvw_us>[0-9.]+) "
    r"t_bootstrap_over_r_scalar_us=(?P<t_bootstrap_over_r_scalar_us>[0-9.]+)"
)
CORRECTNESS_RE = re.compile(
    r"SAB_PVW_NONBINARY_BENCH correctness target_full "
    r"mode=(?P<mode>\S+) r=(?P<r>\d+) h=(?P<h>\d+) "
    r"r_prec=(?P<r_prec>\d+): (?P<gate>Pass|Fail)"
)


def rel(path: Path) -> str:
    return path.relative_to(ROOT).as_posix()


def git_head() -> str:
    return subprocess.check_output(["git", "rev-parse", "--short", "HEAD"], cwd=ROOT, text=True).strip()


def write_csv(path: Path, rows: list[dict[str, str]], fields: list[str]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="\n", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields, lineterminator="\n")
        writer.writeheader()
        for row in rows:
            writer.writerow({field: row.get(field, "") for field in fields})


def write_text(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text.rstrip() + "\n", encoding="utf-8", newline="\n")


def append_once(path: Path, marker: str, text: str) -> None:
    current = path.read_text(encoding="utf-8") if path.exists() else ""
    if marker in current:
        return
    with path.open("a", encoding="utf-8", newline="\n") as handle:
        if current and not current.endswith("\n"):
            handle.write("\n")
        handle.write(text.lstrip())
        if not text.endswith("\n"):
            handle.write("\n")


def sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def table(rows: list[dict[str, str]], fields: list[str]) -> str:
    out = ["| " + " | ".join(fields) + " |"]
    out.append("| " + " | ".join("---" for _ in fields) + " |")
    for row in rows:
        out.append("| " + " | ".join(str(row.get(field, "")).replace("|", "\\|") for field in fields) + " |")
    return "\n".join(out)


def fields_from_line(line: str) -> dict[str, str]:
    fields: dict[str, str] = {}
    for token in line.split():
        if "=" not in token:
            continue
        key, value = token.split("=", 1)
        fields[key] = value.rstrip("x")
    return fields


def f(row: dict[str, str], key: str) -> float:
    try:
        return float(row.get(key, "0") or "0")
    except ValueError:
        return 0.0


def pct(num: float, den: float) -> str:
    return f"{num / den:.6f}" if den else "0.000000"


def parse_logs() -> list[dict[str, str]]:
    rows: list[dict[str, str]] = []
    for path in sorted(RAW.glob("*_suba_profile_run.log")):
        text = path.read_text(encoding="utf-8", errors="replace")
        correctness = None
        summary = None
        profile_line = None
        for line in text.splitlines():
            if "SAB_PVW_BODY_PROFILE sample" in line:
                profile_line = line
            match = CORRECTNESS_RE.search(line)
            if match:
                correctness = match.groupdict()
            match = SUMMARY_RE.search(line)
            if match:
                summary = match.groupdict()
        if correctness is None or summary is None or profile_line is None:
            raise SystemExit(f"missing Stage271 lines in {path}")
        profile = fields_from_line(profile_line)
        profile.update(
            {
                "platform": "WSL2/Linux",
                "backend": "spqlios_avx512",
                "param": "SET_2_3",
                "mode": summary["mode"],
                "r": summary["r"],
                "reps": summary["reps"],
                "correctness_gate": correctness["gate"],
                "pvw_avg_us": summary["pvw_avg_us"],
                "scalar_repeated_avg_us": summary["scalar_repeated_avg_us"],
                "speedup_vs_scalar_repeated": summary["speedup_vs_scalar_repeated"],
                "t_bootstrap_over_r_pvw_us": summary["t_bootstrap_over_r_pvw_us"],
                "t_bootstrap_over_r_scalar_us": summary["t_bootstrap_over_r_scalar_us"],
                "source_log": rel(path),
            }
        )
        rows.append(profile)
    rows.sort(key=lambda row: row["mode"])
    return rows


def profile_rows(raw: list[dict[str, str]]) -> list[dict[str, str]]:
    rows: list[dict[str, str]] = []
    for row in raw:
        sub_a_us = f(row, "sub_a_us")
        full_us = f(row, "full_us")
        pvw_us = f(row, "pvw_avg_us")
        split_keys = [
            ("rotate", "sub_a_rotate_us", "sub_a_rotate_calls"),
            ("mul_minus_1", "sub_a_mul_minus_1_us", "sub_a_mul_minus_1_calls"),
            ("copy", "sub_a_copy_us", "sub_a_copy_calls"),
            ("selector_mat_ep", "sub_a_mat_ep_us", "sub_a_mat_ep_calls"),
            ("from_dft", "sub_a_from_dft_us", "sub_a_from_dft_calls"),
            ("add", "sub_a_add_us", "sub_a_add_calls"),
        ]
        split_sum = sum(f(row, key) for _, key, _ in split_keys)
        for component, us_key, calls_key in split_keys:
            us = f(row, us_key)
            rows.append(
                {
                    "mode": row["mode"],
                    "r": row["r"],
                    "component": component,
                    "component_us": f"{us:.3f}",
                    "calls": row.get(calls_key, "0"),
                    "share_of_sub_a": pct(us, sub_a_us),
                    "share_of_body": pct(us, full_us),
                    "share_of_pvw": pct(us, pvw_us),
                    "source_log": row["source_log"],
                }
            )
        residual = max(0.0, sub_a_us - split_sum)
        rows.append(
            {
                "mode": row["mode"],
                "r": row["r"],
                "component": "residual_or_timer_overhead",
                "component_us": f"{residual:.3f}",
                "calls": "",
                "share_of_sub_a": pct(residual, sub_a_us),
                "share_of_body": pct(residual, full_us),
                "share_of_pvw": pct(residual, pvw_us),
                "source_log": row["source_log"],
            }
        )
    return rows


def summary_rows(raw: list[dict[str, str]], split: list[dict[str, str]]) -> list[dict[str, str]]:
    out = []
    for row in raw:
        sub_components = [item for item in split if item["mode"] == row["mode"] and item["component"] != "residual_or_timer_overhead"]
        dominant = max(sub_components, key=lambda item: float(item["share_of_sub_a"])) if sub_components else {}
        split_sum = sum(float(item["component_us"]) for item in sub_components)
        sub_a_us = f(row, "sub_a_us")
        out.append(
            {
                "mode": row["mode"],
                "r": row["r"],
                "correctness_gate": row["correctness_gate"],
                "in_N": row["in_N"],
                "h": row["h"],
                "r_prec": row["r_prec"],
                "sub_a_calls": row["sub_a_calls"],
                "expected_sub_a_calls": str(int(row["sparse_mul_calls"]) * int(row["h"])),
                "expected_idx_calls": str(int(row["sparse_mul_calls"]) * int(row["h"]) * int(row["in_N"])),
                "sub_a_us": row["sub_a_us"],
                "sub_a_share_of_body": pct(sub_a_us, f(row, "full_us")),
                "sub_a_share_of_pvw": pct(sub_a_us, f(row, "pvw_avg_us")),
                "split_sum_us": f"{split_sum:.3f}",
                "split_sum_over_sub_a": pct(split_sum, sub_a_us),
                "dominant_component": dominant.get("component", ""),
                "dominant_share_of_sub_a": dominant.get("share_of_sub_a", ""),
                "source_log": row["source_log"],
            }
        )
    return out


def call_gate(row: dict[str, str]) -> bool:
    expected_sub_a = int(row["sparse_mul_calls"]) * int(row["h"])
    expected = expected_sub_a * int(row["in_N"])
    mode = row["mode"]
    if int(row["sub_a_calls"]) != expected_sub_a:
        return False
    required = ["sub_a_mul_minus_1_calls", "sub_a_mat_ep_calls", "sub_a_from_dft_calls", "sub_a_add_calls"]
    if mode == "ternary":
        required += ["sub_a_rotate_calls", "sub_a_copy_calls"]
    for key in required:
        if int(row.get(key, "0") or "0") != expected:
            return False
    if mode == "include_zero":
        if int(row.get("sub_a_rotate_calls", "0") or "0") != 0:
            return False
        if int(row.get("sub_a_copy_calls", "0") or "0") != 0:
            return False
    return True


def next_rows(summary: list[dict[str, str]], split: list[dict[str, str]]) -> list[dict[str, str]]:
    dominant = {}
    if split:
        non_residual = [row for row in split if row["component"] != "residual_or_timer_overhead"]
        if non_residual:
            dominant = max(non_residual, key=lambda row: float(row["share_of_sub_a"]))
    component = dominant.get("component", "")
    if component in {"rotate", "copy", "mul_minus_1"}:
        route = "stage272_sub_a_rotation_copy_fusion_smoke"
        gate = "Implement an explicit-flag rotation/copy scratch variant and test staged equivalence plus full SAB T_bootstrap/r smoke."
    elif component in {"selector_mat_ep", "from_dft", "add"}:
        route = "stage272_sub_a_selector_materialization_design_gate"
        gate = "Design a selector materialization variant; do not code until complexity/noise and repeated-gate criteria are fixed."
    else:
        route = "stage272_sub_a_closeout_or_native_counter_return"
        gate = "No dominant actionable subcomponent; return to MAT native counter route."
    return [
        {
            "priority": "P0",
            "route": route,
            "entry_condition": f"dominant_component={component} share={dominant.get('share_of_sub_a', '')}",
            "gate": gate,
            "status": "selected",
            "failure_action": "Record neutral/negative and do not promote without full SAB repeated T_bootstrap/r.",
        }
    ]


def proof_rows(raw: list[dict[str, str]], summary: list[dict[str, str]]) -> list[dict[str, str]]:
    coverage = {row["mode"] for row in raw}
    correctness = all(row["correctness_gate"] == "Pass" for row in raw)
    calls = all(call_gate(row) for row in raw)
    max_split_ratio = max((float(row["split_sum_over_sub_a"]) for row in summary), default=0.0)
    decision = "PASS_STAGE271_NONBINARY_SUB_A_SPLIT_PROFILE" if coverage == {"include_zero", "ternary"} and correctness and calls else "FAIL_STAGE271_NONBINARY_SUB_A_SPLIT_PROFILE"
    return [
        {"gate": "G1_coverage", "status": "PASS" if coverage == {"include_zero", "ternary"} else "FAIL", "metric": "r=4 modes", "value": ",".join(sorted(coverage)), "evidence": "profile_summary.csv", "interpretation": "Covers include-zero and ternary non-binary sub_a."},
        {"gate": "G2_correctness", "status": "PASS" if correctness else "FAIL", "metric": "PVW/scalar correctness", "value": f"{sum(row['correctness_gate'] == 'Pass' for row in raw)}/{len(raw)}", "evidence": "profile_summary.csv", "interpretation": "Profile instrumentation must not break full target correctness."},
        {"gate": "G3_split_call_counts", "status": "PASS" if calls else "FAIL", "metric": "expected sub_a split calls", "value": "; ".join(f"{row['mode']} expected_idx={row['expected_idx_calls']}" for row in summary), "evidence": "profile_summary.csv", "interpretation": "Split counters must match the non-binary SAB schedule."},
        {"gate": "G4_profile_overhead_boundary", "status": "PASS_PROFILE_ONLY", "metric": "max split_sum/sub_a", "value": f"{max_split_ratio:.6f}", "evidence": "sub_a_split.csv", "interpretation": "Stage271 is attribution-only; timing overhead is not used as final latency evidence."},
        {"gate": "G5_decision", "status": decision, "metric": "stage decision", "value": decision, "evidence": "proof_gate.csv", "interpretation": "Proceed only to the next gate selected from split attribution."},
    ]


def claim_rows() -> list[dict[str, str]]:
    return [
        {"claim": "sub_a_split_attribution", "status": "profile_only", "allowed_wording": "Stage271 identifies the internal sub_a component mix under profile instrumentation.", "forbidden_wording": "Stage271 proves a latency speedup.", "evidence": "sub_a_split.csv"},
        {"claim": "full_sab_speed", "status": "not_measured_for_claim", "allowed_wording": "Correctness is checked, but timing is instrumented and used only for attribution.", "forbidden_wording": "Use Stage271 profile timings as final T_bootstrap/r.", "evidence": "claim_boundary.csv"},
        {"claim": "next_optimization", "status": "gate_selected_only", "allowed_wording": "The next route is selected by the dominant profiled subcomponent.", "forbidden_wording": "The selected route is already beneficial.", "evidence": "next_stage_queue.csv"},
    ]


def artifacts(paths: list[Path]) -> list[dict[str, str]]:
    rows = []
    for path in paths:
        if path.exists() and path.is_file():
            rows.append({"path": rel(path), "bytes": str(path.stat().st_size), "sha256": sha256(path)})
    for path in sorted(RAW.glob("*")):
        if path.is_file():
            rows.append({"path": rel(path), "bytes": str(path.stat().st_size), "sha256": sha256(path)})
    return rows


def update_tracking(decision: str) -> None:
    head = git_head()
    append_once(CURRENT_GOAL, "### Stage271 non-binary sub_a split profile", f"""
### Stage271 non-binary sub_a split profile

`{decision}` records profile-only split attribution for r=4 include-zero and
ternary non-binary `sub_a`. It does not claim a latency improvement; it only
selects the next falsifiable optimization gate.
""")
    append_once(HYPOTHESES, "H10_stage271_nonbinary_sub_a_split_profile:", f"""
H10_stage271_nonbinary_sub_a_split_profile:
  status: {decision}
  evidence:
    - repro/stage271_nonbinary_sub_a_split_profile/profile_summary.csv
    - repro/stage271_nonbinary_sub_a_split_profile/sub_a_split.csv
    - repro/stage271_nonbinary_sub_a_split_profile/proof_gate.csv
    - docs/stage271_nonbinary_sub_a_split_profile.md
  conclusion: >
    Stage271 records {decision}. It adds profile-only sub_a split counters and
    keeps timing claims bounded to attribution, not final latency.
""")
    append_once(RUN_LOG, "stage271-nonbinary-sub-a-split-profile-001", f"""stage271-nonbinary-sub-a-split-profile-001,2026-07-04,{head},Stage 271,spqlios_avx512-profile,python scripts/build_stage271_nonbinary_sub_a_split_profile.py,"r=4 include-zero/ternary sub_a split attribution under SAB_PVW_BODY_PROFILE",n/a,{decision},"Profile-only attribution; no final T_bootstrap/r speed claim.",docs/stage271_nonbinary_sub_a_split_profile.md; repro/stage271_nonbinary_sub_a_split_profile/proof_gate.csv
""")
    append_once(MANIFEST, "- stage271_nonbinary_sub_a_split_profile:", """
- stage271_nonbinary_sub_a_split_profile:
  - `docs/stage271_nonbinary_sub_a_split_profile.md`
  - `scripts/run_stage271_nonbinary_sub_a_split_profile.sh`
  - `scripts/build_stage271_nonbinary_sub_a_split_profile.py`
  - `repro/stage271_nonbinary_sub_a_split_profile/`
""")
    append_once(CHECKLIST, "stage271-nonbinary-sub-a-split-profile-checklist", f"""
<!-- stage271-nonbinary-sub-a-split-profile-checklist -->
- [x] Stage271 records `{decision}` as profile-only sub_a split attribution.
""")


def main() -> int:
    REPRO.mkdir(parents=True, exist_ok=True)
    raw = parse_logs()
    split = profile_rows(raw)
    summary = summary_rows(raw, split)
    queue = next_rows(summary, split)
    proof = proof_rows(raw, summary)
    decision = proof[-1]["status"]
    claims = claim_rows()

    write_csv(REPRO / "profile_summary.csv", summary, [
        "mode", "r", "correctness_gate", "in_N", "h", "r_prec", "sub_a_calls",
        "expected_sub_a_calls", "expected_idx_calls", "sub_a_us",
        "sub_a_share_of_body", "sub_a_share_of_pvw", "split_sum_us",
        "split_sum_over_sub_a", "dominant_component",
        "dominant_share_of_sub_a", "source_log",
    ])
    write_csv(REPRO / "sub_a_split.csv", split, [
        "mode", "r", "component", "component_us", "calls", "share_of_sub_a",
        "share_of_body", "share_of_pvw", "source_log",
    ])
    write_csv(REPRO / "proof_gate.csv", proof, ["gate", "status", "metric", "value", "evidence", "interpretation"])
    write_csv(REPRO / "claim_boundary.csv", claims, ["claim", "status", "allowed_wording", "forbidden_wording", "evidence"])
    write_csv(REPRO / "next_stage_queue.csv", queue, ["priority", "route", "entry_condition", "gate", "status", "failure_action"])

    dominant_rows = [row for row in split if row["component"] != "residual_or_timer_overhead"]
    report = f"""# Stage271 Non-Binary Sub_a Split Profile

Decision: `{decision}`.

Stage271 adds profile-only split counters inside non-binary `sub_a` and runs
r=4 include-zero/ternary correctness plus body profile. These timings are
instrumented attribution, not final `T_bootstrap/r` performance evidence.

## Profile Summary

{table(summary, ["mode", "r", "correctness_gate", "sub_a_calls", "expected_idx_calls", "sub_a_share_of_body", "sub_a_share_of_pvw", "split_sum_over_sub_a", "dominant_component", "dominant_share_of_sub_a"])}

## Split Components

{table(dominant_rows, ["mode", "component", "component_us", "calls", "share_of_sub_a", "share_of_body", "share_of_pvw"])}

## Proof Gate

{table(proof, ["gate", "status", "metric", "value", "interpretation"])}

## Claim Boundary

{table(claims, ["claim", "status", "allowed_wording", "forbidden_wording"])}

## Next Queue

{table(queue, ["priority", "route", "entry_condition", "gate", "status", "failure_action"])}

Generated from input head `{git_head()}`.
"""
    write_text(DOC, report)
    write_text(REPRO / "stage271_report.md", report)
    write_text(REPRO / "reproduction_commands.md", """# Stage271 Reproduction Commands

```bash
bash scripts/run_stage271_nonbinary_sub_a_split_profile.sh
python3 scripts/build_stage271_nonbinary_sub_a_split_profile.py
```

The run uses `SAB_PVW_BODY_PROFILE=true`; results are attribution-only.
""")
    update_tracking(decision)
    paths = [
        DOC,
        REPRO / "stage271_report.md",
        REPRO / "reproduction_commands.md",
        REPRO / "profile_summary.csv",
        REPRO / "sub_a_split.csv",
        REPRO / "proof_gate.csv",
        REPRO / "claim_boundary.csv",
        REPRO / "next_stage_queue.csv",
        ROOT / "scripts" / "run_stage271_nonbinary_sub_a_split_profile.sh",
        Path(__file__),
    ]
    write_csv(REPRO / "artifact_index.csv", artifacts(paths), ["path", "bytes", "sha256"])
    print(decision)
    return 0 if decision.startswith("PASS_") else 1


if __name__ == "__main__":
    raise SystemExit(main())
