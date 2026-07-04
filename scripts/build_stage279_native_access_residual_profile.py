#!/usr/bin/env python3
"""Build Stage279 native access and residual-profile artifacts."""

from __future__ import annotations

import csv
import hashlib
import re
import subprocess
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
REPRO = ROOT / "repro" / "stage279_native_access_residual_profile"
RAW = REPRO / "raw"
DOC = ROOT / "docs" / "stage279_native_access_residual_profile.md"
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

PROFILE_COMPONENTS = [
    ("setup_tv_xb", "setup_tv_xb_us", "setup_tv_xb_calls"),
    ("rgsw_monomial", "rgsw_monomial_us", "rgsw_monomial_calls"),
    ("cmux_total", "cmux_us", "cmux_calls"),
    ("ncmux_total", "ncmux_us", "ncmux_calls"),
    ("cmux_sub", "cmux_sub_us", "cmux_sub_calls"),
    ("cmux_from_dft", "cmux_from_dft_us", "cmux_from_dft_calls"),
    ("cmux_add", "cmux_add_us", "cmux_add_calls"),
    ("ncmux_auto", "ncmux_auto_us", "ncmux_auto_calls"),
    ("mat_ep", "mat_ep_us", "mat_ep_calls"),
    ("sub_a_total", "sub_a_us", "sub_a_calls"),
    ("sub_a_rotate", "sub_a_rotate_us", "sub_a_rotate_calls"),
    ("sub_a_mul_minus_1", "sub_a_mul_minus_1_us", "sub_a_mul_minus_1_calls"),
    ("sub_a_copy", "sub_a_copy_us", "sub_a_copy_calls"),
    ("sub_a_mat_ep", "sub_a_mat_ep_us", "sub_a_mat_ep_calls"),
    ("sub_a_from_dft", "sub_a_from_dft_us", "sub_a_from_dft_calls"),
    ("sub_a_add", "sub_a_add_us", "sub_a_add_calls"),
]


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


def read_csv(path: Path) -> list[dict[str, str]]:
    if not path.exists():
        return []
    with path.open(newline="", encoding="utf-8-sig", errors="replace") as handle:
        return list(csv.DictReader(handle))


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


def parse_profile_logs() -> list[dict[str, str]]:
    rows: list[dict[str, str]] = []
    for path in sorted(RAW.glob("local_*_include_zero_body_profile_run.log")):
        name = path.name
        if name.startswith("local_default_"):
            variant = "default"
        elif name.startswith("local_include_zero_coeff_one_fast_"):
            variant = "include_zero_coeff_one_fast"
        else:
            continue
        text = path.read_text(encoding="utf-8", errors="replace")
        profile_line = None
        correctness = None
        summary = None
        for line in text.splitlines():
            if "SAB_PVW_BODY_PROFILE sample" in line:
                profile_line = line
            match = CORRECTNESS_RE.search(line)
            if match:
                correctness = match.groupdict()
            match = SUMMARY_RE.search(line)
            if match:
                summary = match.groupdict()
        if not profile_line or correctness is None or summary is None:
            raise SystemExit(f"missing profile/correctness/summary line in {path}")
        row = fields_from_line(profile_line)
        row.update(
            {
                "variant": variant,
                "mode": summary["mode"],
                "r": summary["r"],
                "reps": summary["reps"],
                "correctness_gate": correctness["gate"],
                "pvw_avg_us": summary["pvw_avg_us"],
                "scalar_repeated_avg_us": summary["scalar_repeated_avg_us"],
                "speedup_vs_scalar_repeated": summary["speedup_vs_scalar_repeated"],
                "t_bootstrap_over_r_pvw_us": summary["t_bootstrap_over_r_pvw_us"],
                "t_bootstrap_over_r_scalar_us": summary["t_bootstrap_over_r_scalar_us"],
                "platform": "WSL2/Linux",
                "backend": "spqlios_avx512",
                "source_log": rel(path),
            }
        )
        rows.append(row)
    rows.sort(key=lambda row: row["variant"])
    return rows


def profile_component_rows(raw: list[dict[str, str]]) -> list[dict[str, str]]:
    rows: list[dict[str, str]] = []
    for row in raw:
        pvw_us = f(row, "pvw_avg_us")
        body_us = f(row, "full_us")
        for component, us_key, calls_key in PROFILE_COMPONENTS:
            us = f(row, us_key)
            rows.append(
                {
                    "variant": row["variant"],
                    "component": component,
                    "component_us": f"{us:.3f}",
                    "calls": row.get(calls_key, "0"),
                    "share_of_body": pct(us, body_us),
                    "share_of_pvw": pct(us, pvw_us),
                    "source_log": row["source_log"],
                }
            )
    return rows


def compare_rows(raw: list[dict[str, str]]) -> list[dict[str, str]]:
    by_variant = {row["variant"]: row for row in raw}
    default = by_variant.get("default")
    fast = by_variant.get("include_zero_coeff_one_fast")
    if not default or not fast:
        return [{"status": "MISSING"}]
    default_us = f(default, "t_bootstrap_over_r_pvw_us")
    fast_us = f(fast, "t_bootstrap_over_r_pvw_us")
    default_suba = f(default, "sub_a_us")
    fast_suba = f(fast, "sub_a_us")
    return [
        {
            "mode": "include_zero",
            "r": "4",
            "default_t_bootstrap_over_r_us": f"{default_us:.3f}",
            "fast_t_bootstrap_over_r_us": f"{fast_us:.3f}",
            "fast_speedup_vs_profile_default": f"{default_us / fast_us:.6f}" if fast_us else "0.000000",
            "default_sub_a_us": f"{default_suba:.3f}",
            "fast_sub_a_us": f"{fast_suba:.3f}",
            "sub_a_reduction_ratio": f"{default_suba / fast_suba:.6f}" if fast_suba else "0.000000",
            "default_correctness": default["correctness_gate"],
            "fast_correctness": fast["correctness_gate"],
            "status": "positive" if fast_us and default_us / fast_us >= 1.01 else "neutral_or_negative",
        }
    ]


def residual_rows(components: list[dict[str, str]]) -> list[dict[str, str]]:
    fast = [row for row in components if row["variant"] == "include_zero_coeff_one_fast"]
    ranked = sorted(fast, key=lambda row: float(row["share_of_pvw"]), reverse=True)
    return ranked[:10]


def native_rows() -> list[dict[str, str]]:
    rows = read_csv(RAW / "native_access_probe.csv")
    if rows:
        return rows
    return [{"status": "not_run", "host": "", "user": "", "auth_mode": "BatchMode", "exit_code": "", "reason": "probe_not_run"}]


def decision_from(native: list[dict[str, str]], raw: list[dict[str, str]], compare: list[dict[str, str]]) -> str:
    if len(raw) != 2:
        return "FAIL_STAGE279_RESIDUAL_PROFILE_MISSING_COVERAGE"
    if any(row["correctness_gate"] != "Pass" for row in raw):
        return "FAIL_STAGE279_RESIDUAL_PROFILE_CORRECTNESS"
    if not compare or compare[0].get("status") != "positive":
        return "NEUTRAL_STAGE279_FAST_PROFILE_NO_LOCAL_SPEED"
    native_status = native[0].get("status", "not_run") if native else "not_run"
    if native_status == "passed":
        return "PASS_STAGE279_NATIVE_ACCESS_READY_PROFILE_SELECT_RESIDUAL"
    return "PASS_STAGE279_NATIVE_ACCESS_MISSING_PROFILE_SELECT_RESIDUAL"


def proof_rows(native: list[dict[str, str]], raw: list[dict[str, str]],
               compare: list[dict[str, str]], residual: list[dict[str, str]],
               decision: str) -> list[dict[str, str]]:
    native_status = native[0].get("status", "missing") if native else "missing"
    top = residual[0]["component"] if residual else "missing"
    top_share = residual[0]["share_of_pvw"] if residual else "0"
    return [
        {"gate": "G1_native_probe", "status": "PASS_RECORDED" if native else "FAIL", "metric": "BatchMode access", "value": native_status, "evidence": "native_access_probe.csv", "interpretation": "Native access status is recorded without credentials."},
        {"gate": "G2_profile_coverage", "status": "PASS" if len(raw) == 2 else "FAIL", "metric": "profile variants", "value": ",".join(row["variant"] for row in raw), "evidence": "profile_summary.csv", "interpretation": "Residual profile compares default and fast include-zero variants."},
        {"gate": "G3_correctness", "status": "PASS" if all(row["correctness_gate"] == "Pass" for row in raw) else "FAIL", "metric": "profile correctness", "value": f"{sum(row['correctness_gate'] == 'Pass' for row in raw)}/{len(raw)}", "evidence": "profile_summary.csv", "interpretation": "Profile timing is interpreted only after correctness passes."},
        {"gate": "G4_local_speed", "status": "PASS" if compare and compare[0].get("status") == "positive" else "NEUTRAL", "metric": "profile fast speedup", "value": compare[0].get("fast_speedup_vs_profile_default", "0") if compare else "0", "evidence": "profile_compare.csv", "interpretation": "Body-profile run should still show fast path benefit."},
        {"gate": "G5_residual_selection", "status": "PASS", "metric": "top residual component", "value": f"{top}:{top_share}", "evidence": "residual_top_components.csv", "interpretation": "Next algorithm candidate must target the measured residual, not pre-fast assumptions."},
        {"gate": "G6_claim_boundary", "status": "PASS_NOT_FINAL", "metric": "claim scope", "value": decision, "evidence": "claim_boundary.csv", "interpretation": "Native paper-grade claim remains gated; residual profile selects next engineering candidate."},
        {"gate": "G7_decision", "status": decision, "metric": "stage decision", "value": decision, "evidence": "proof_gate.csv", "interpretation": "Proceed to residual-driven next candidate and/or native access resolution."},
    ]


def claim_rows(decision: str) -> list[dict[str, str]]:
    return [
        {"claim": "native_access", "status": "recorded", "allowed_wording": "Stage279 records BatchMode native access status without storing credentials.", "forbidden_wording": "Native performance evidence exists if only the access probe failed.", "evidence": "native_access_probe.csv"},
        {"claim": "residual_profile", "status": "measured", "allowed_wording": "Stage279 selects next candidates from the measured fast-path residual profile.", "forbidden_wording": "Stage279 proves final algorithm optimality.", "evidence": "residual_top_components.csv"},
        {"claim": "include_zero_fast", "status": "still_guarded", "allowed_wording": "Fast path remains scoped to current PVW include-zero coefficient-one semantics.", "forbidden_wording": "The optimization covers ternary or general scalar include-zero.", "evidence": "claim_boundary.csv"},
    ]


def next_rows(residual: list[dict[str, str]], native: list[dict[str, str]]) -> list[dict[str, str]]:
    top = residual[0]["component"] if residual else "unknown"
    native_status = native[0].get("status", "not_run") if native else "not_run"
    if top in {"mat_ep", "cmux_total", "rgsw_monomial"}:
        selected = "stage280_cmux_mat_ep_residual_optimization_design"
        gate = "Design a falsifiable CMUX/MAT-EP residual candidate under fast flag; require microbench and full SAB A/B."
    elif top in {"cmux_from_dft", "cmux_add", "cmux_sub"}:
        selected = "stage280_cmux_materialization_lifecycle_gate"
        gate = "Profile and test CMUX materialization lifecycle fusion under explicit flag."
    else:
        selected = "stage280_residual_candidate_design"
        gate = "Design candidate from measured residual profile."
    return [
        {"priority": "P0", "route": selected, "entry_condition": f"Top residual component is {top}.", "gate": gate, "status": "selected", "failure_action": "No next optimization without full SAB A/B."},
        {"priority": "P1", "route": "stage281_native_execution_resolution", "entry_condition": f"Native probe status is {native_status}.", "gate": "Resolve key-based native access or keep claim local-only.", "status": "conditional", "failure_action": "Do not claim native performance."},
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
    append_once(CURRENT_GOAL, "### Stage279 native access and residual profile", f"""
### Stage279 native access and residual profile

`{decision}` records no-credential native access status and measures the
fast-path residual profile. The next optimization is selected from the measured
residual components rather than pre-fast bottleneck assumptions.
""")
    append_once(HYPOTHESES, "H10_stage279_native_access_residual_profile:", f"""
H10_stage279_native_access_residual_profile:
  status: {decision}
  evidence:
    - repro/stage279_native_access_residual_profile/native_access_probe.csv
    - repro/stage279_native_access_residual_profile/residual_top_components.csv
    - repro/stage279_native_access_residual_profile/proof_gate.csv
    - docs/stage279_native_access_residual_profile.md
  conclusion: >
    Stage279 records {decision}. It keeps native performance gated and selects
    the next candidate from the measured fast-path residual profile.
""")
    append_once(RUN_LOG, "stage279-native-access-residual-profile-001", f"""stage279-native-access-residual-profile-001,2026-07-04,{head},Stage 279,spqlios_avx512-profile,bash scripts/run_stage279_native_access_residual_profile.sh; python scripts/build_stage279_native_access_residual_profile.py,"BatchMode native access probe plus default-vs-fast residual body profile",n/a,{decision},"Native claim remains gated; next optimization selected from residual profile.",docs/stage279_native_access_residual_profile.md; repro/stage279_native_access_residual_profile/proof_gate.csv
""")
    append_once(MANIFEST, "- stage279_native_access_residual_profile:", """
- stage279_native_access_residual_profile:
  - `docs/stage279_native_access_residual_profile.md`
  - `scripts/run_stage279_native_access_residual_profile.sh`
  - `scripts/build_stage279_native_access_residual_profile.py`
  - `repro/stage279_native_access_residual_profile/`
""")
    append_once(CHECKLIST, "stage279-native-access-residual-profile-checklist", f"""
<!-- stage279-native-access-residual-profile-checklist -->
- [x] Stage279 records `{decision}` with native access status and fast-path residual profile.
""")


def main() -> int:
    REPRO.mkdir(parents=True, exist_ok=True)
    native = native_rows()
    raw = parse_profile_logs()
    components = profile_component_rows(raw)
    compare = compare_rows(raw)
    residual = residual_rows(components)
    decision = decision_from(native, raw, compare)
    proof = proof_rows(native, raw, compare, residual, decision)
    claims = claim_rows(decision)
    queue = next_rows(residual, native)

    write_csv(REPRO / "native_access_probe.csv", native, ["status", "host", "user", "auth_mode", "exit_code", "reason"])
    write_csv(REPRO / "profile_summary.csv", raw, [
        "variant", "mode", "r", "reps", "correctness_gate",
        "pvw_avg_us", "t_bootstrap_over_r_pvw_us", "speedup_vs_scalar_repeated",
        "full_us", "sparse_mul_us", "rgsw_monomial_us", "cmux_us",
        "mat_ep_us", "sub_a_us", "source_log",
    ])
    write_csv(REPRO / "profile_components.csv", components, [
        "variant", "component", "component_us", "calls",
        "share_of_body", "share_of_pvw", "source_log",
    ])
    write_csv(REPRO / "profile_compare.csv", compare, [
        "mode", "r", "default_t_bootstrap_over_r_us", "fast_t_bootstrap_over_r_us",
        "fast_speedup_vs_profile_default", "default_sub_a_us", "fast_sub_a_us",
        "sub_a_reduction_ratio", "default_correctness", "fast_correctness", "status",
    ])
    write_csv(REPRO / "residual_top_components.csv", residual, [
        "variant", "component", "component_us", "calls",
        "share_of_body", "share_of_pvw", "source_log",
    ])
    write_csv(REPRO / "proof_gate.csv", proof, ["gate", "status", "metric", "value", "evidence", "interpretation"])
    write_csv(REPRO / "claim_boundary.csv", claims, ["claim", "status", "allowed_wording", "forbidden_wording", "evidence"])
    write_csv(REPRO / "next_stage_queue.csv", queue, ["priority", "route", "entry_condition", "gate", "status", "failure_action"])

    report = f"""# Stage279 Native Access and Residual Profile

Decision: `{decision}`.

Stage279 records native access status with SSH BatchMode and measures the
default-vs-fast include-zero residual profile under `spqlios_avx512`.

## Native Access

{table(native, ["status", "host", "user", "auth_mode", "exit_code", "reason"])}

## Profile Compare

{table(compare, ["mode", "r", "default_t_bootstrap_over_r_us", "fast_t_bootstrap_over_r_us", "fast_speedup_vs_profile_default", "default_sub_a_us", "fast_sub_a_us", "sub_a_reduction_ratio", "status"])}

## Top Residual Components

{table(residual, ["component", "component_us", "calls", "share_of_body", "share_of_pvw"])}

## Proof Gate

{table(proof, ["gate", "status", "metric", "value", "interpretation"])}

## Claim Boundary

{table(claims, ["claim", "status", "allowed_wording", "forbidden_wording"])}

## Next Queue

{table(queue, ["priority", "route", "entry_condition", "gate", "status", "failure_action"])}

Generated from input head `{git_head()}`.
"""
    write_text(DOC, report)
    write_text(REPRO / "stage279_report.md", report)
    write_text(REPRO / "reproduction_commands.md", """# Stage279 Reproduction Commands

```bash
bash scripts/run_stage279_native_access_residual_profile.sh
python3 scripts/build_stage279_native_access_residual_profile.py
```

The native probe uses SSH BatchMode and does not use or store credentials.
Override `NATIVE_HOST` and `NATIVE_USER` as needed.
""")
    update_tracking(decision)
    paths = [
        DOC,
        REPRO / "stage279_report.md",
        REPRO / "reproduction_commands.md",
        REPRO / "native_access_probe.csv",
        REPRO / "profile_summary.csv",
        REPRO / "profile_components.csv",
        REPRO / "profile_compare.csv",
        REPRO / "residual_top_components.csv",
        REPRO / "proof_gate.csv",
        REPRO / "claim_boundary.csv",
        REPRO / "next_stage_queue.csv",
        Path(__file__),
        ROOT / "scripts" / "run_stage279_native_access_residual_profile.sh",
    ]
    write_csv(REPRO / "artifact_index.csv", artifacts(paths), ["path", "bytes", "sha256"])
    print(decision)
    return 0 if decision.startswith("PASS_") or decision.startswith("NEUTRAL_") else 1


if __name__ == "__main__":
    raise SystemExit(main())
