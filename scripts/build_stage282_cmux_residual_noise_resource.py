#!/usr/bin/env python3
"""Build Stage282 noise/resource artifacts for the selected CMUX residual candidate."""

from __future__ import annotations

import csv
import hashlib
import re
import subprocess
from pathlib import Path
from typing import Dict, Iterable, List


ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "repro" / "stage282_cmux_residual_noise_resource"
RAW = OUT / "raw"
DOC = ROOT / "docs" / "stage282_cmux_residual_noise_resource.md"
RUNNER = ROOT / "scripts" / "run_stage282_cmux_residual_noise_resource.sh"
BUILDER = ROOT / "scripts" / "build_stage282_cmux_residual_noise_resource.py"
CURRENT_GOAL = ROOT / "docs" / "current_codex_goal_sab_completion.md"
HYPOTHESES = ROOT / "hypotheses" / "hypothesis_register.yaml"
RUN_LOG = ROOT / "repro" / "run_log.csv"
MANIFEST = ROOT / "repro" / "artifact_manifest.md"
CHECKLIST = ROOT / "repro" / "reproduction_checklist.md"

SUMMARY = OUT / "noise_resource_summary.csv"
PROOF = OUT / "proof_gate.csv"
QUEUE = OUT / "next_stage_queue.csv"
COMMANDS = OUT / "reproduction_commands.md"
REPORT = OUT / "stage282_report.md"
ARTIFACT_INDEX = OUT / "artifact_index.csv"

VARIANTS = ["fast_control", "backend_sub_decomp_dual"]

KEY_BYTES_RE = re.compile(
    r"SAB_PVW_NONBINARY_RESOURCE key_bytes full_smoke mode=(?P<mode>\S+) r=(?P<r>\d+) "
    r"pvw_estimated_key_bytes=(?P<pvw_key_bytes>\d+) "
    r"scalar_one_estimated_key_bytes=(?P<scalar_one_key_bytes>\d+) "
    r"scalar_repeated_estimated_key_bytes=(?P<scalar_repeated_key_bytes>\d+) "
    r"pvw_vs_scalar_repeated_ratio=(?P<key_ratio>[0-9.]+)"
)
PVW_KEYGEN_RE = re.compile(
    r"SAB_PVW_NONBINARY_RESOURCE keygen full_smoke mode=(?P<mode>\S+) r=(?P<r>\d+) "
    r"pvw_sab_keygen_us=(?P<pvw_keygen_us>\d+)"
)
SCALAR_KEYGEN_RE = re.compile(
    r"SAB_PVW_NONBINARY_RESOURCE keygen full_smoke mode=(?P<mode>\S+) r=(?P<r>\d+) "
    r"scalar_repeated_sab_keygen_us=(?P<scalar_keygen_us>\d+) "
    r"scalar_lane_avg_keygen_us=(?P<scalar_lane_keygen_us>[0-9.]+)"
)
RSS_RE = re.compile(
    r"SAB_PVW_NONBINARY_RESOURCE rss full_smoke mode=(?P<mode>\S+) r=(?P<r>\d+) "
    r"label=(?P<label>\S+) vmrss_kb=(?P<vmrss_kb>\d+) vmhwm_kb=(?P<vmhwm_kb>\d+)"
)
NOISE_RE = re.compile(
    r"SAB_PVW_NONBINARY_FULL_NOISE summary mode=(?P<mode>\S+) r=(?P<r>\d+) "
    r"trials=(?P<trials>\d+) points=(?P<points>\d+) "
    r"pvw_failures=(?P<pvw_failures>\d+) scalar_failures=(?P<scalar_failures>\d+) "
    r"pair_failures=(?P<pair_failures>\d+) "
    r"pvw_log2_sigma_torus=(?P<pvw_log2_sigma_torus>-?inf|-?[0-9.]+) "
    r"scalar_log2_sigma_torus=(?P<scalar_log2_sigma_torus>-?inf|-?[0-9.]+) "
    r"pair_log2_sigma_torus=(?P<pair_log2_sigma_torus>-?inf|-?[0-9.]+) "
    r"pair_log2_max_abs_torus=(?P<pair_log2_max_abs_torus>-?inf|-?[0-9.]+) "
    r"gate=(?P<noise_gate>Pass|Fail)"
)
GATE_RE = re.compile(r"SAB_PVW_INCLUDE_ZERO_FAST_RESOURCE full bootstrap gate: (?P<resource_gate>Pass|Fail)")
TIME_RSS_RE = re.compile(r"Maximum resident set size \(kbytes\): (?P<time_maxrss_kb>\d+)")


def rel(path: Path) -> str:
    return path.relative_to(ROOT).as_posix()


def git_head() -> str:
    try:
        return subprocess.check_output(["git", "rev-parse", "--short", "HEAD"], cwd=ROOT, text=True).strip()
    except Exception:
        return "unknown"


def read_text(path: Path) -> str:
    if not path.exists():
        return ""
    return path.read_text(encoding="utf-8", errors="replace").replace("\x00", "").replace("\r\n", "\n").replace("\r", "\n")


def write_text(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text.rstrip() + "\n", encoding="utf-8", newline="\n")


def write_csv(path: Path, fields: Iterable[str], rows: Iterable[Dict[str, object]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=list(fields), lineterminator="\n")
        writer.writeheader()
        for row in rows:
            writer.writerow({field: row.get(field, "") for field in writer.fieldnames})


def append_once(path: Path, marker: str, text: str) -> None:
    current = read_text(path)
    if marker in current:
        return
    sep = "" if current.endswith("\n") or not current else "\n"
    write_text(path, current + sep + text)


def parse_variant(variant: str) -> Dict[str, object]:
    run_text = read_text(RAW / f"{variant}_run.log")
    time_text = read_text(RAW / f"{variant}_time.log")
    row: Dict[str, object] = {
        "variant": variant,
        "source_run_log": rel(RAW / f"{variant}_run.log"),
        "source_time_log": rel(RAW / f"{variant}_time.log"),
    }
    for regex in [KEY_BYTES_RE, PVW_KEYGEN_RE, SCALAR_KEYGEN_RE, NOISE_RE, GATE_RE]:
        match = regex.search(run_text)
        if match:
            row.update(match.groupdict())
    rss_rows = RSS_RE.findall(run_text)
    for mode, r, label, vmrss, vmhwm in rss_rows:
        row[f"{label}_vmrss_kb"] = vmrss
        row[f"{label}_vmhwm_kb"] = vmhwm
    time_match = TIME_RSS_RE.search(time_text)
    if time_match:
        row.update(time_match.groupdict())
    failures = int(row.get("pvw_failures", 1)) + int(row.get("scalar_failures", 1)) + int(row.get("pair_failures", 1))
    row["status"] = "pass" if row.get("noise_gate") == "Pass" and row.get("resource_gate") == "Pass" and failures == 0 else "fail"
    return row


def artifact_hash(path: Path) -> Dict[str, object]:
    data = path.read_bytes()
    return {"path": rel(path), "bytes": len(data), "sha256": hashlib.sha256(data).hexdigest()}


def build_index() -> None:
    paths = [DOC, REPORT, COMMANDS, SUMMARY, PROOF, QUEUE, RAW / "variant_plan.csv", RUNNER, BUILDER]
    paths.extend(sorted(RAW.glob("*.log")))
    write_csv(ARTIFACT_INDEX, ["path", "bytes", "sha256"], [artifact_hash(path) for path in paths if path.exists()])


def main() -> None:
    OUT.mkdir(parents=True, exist_ok=True)
    rows = [parse_variant(variant) for variant in VARIANTS]
    fields = [
        "variant", "status", "mode", "r", "trials", "points",
        "pvw_failures", "scalar_failures", "pair_failures", "noise_gate",
        "resource_gate", "pvw_log2_sigma_torus", "scalar_log2_sigma_torus",
        "pair_log2_sigma_torus", "pair_log2_max_abs_torus",
        "pvw_key_bytes", "scalar_repeated_key_bytes", "key_ratio",
        "pvw_keygen_us", "scalar_keygen_us", "scalar_lane_keygen_us",
        "after_pvw_sab_keygen_vmrss_kb", "after_scalar_repeated_sab_keygen_vmrss_kb",
        "time_maxrss_kb", "source_run_log", "source_time_log",
    ]
    write_csv(SUMMARY, fields, rows)

    all_pass = all(row["status"] == "pass" for row in rows)
    decision = "PASS_STAGE282_NOISE_RESOURCE_LOCAL_PASS_NATIVE_REQUIRED" if all_pass else "FAIL_STAGE282_NOISE_RESOURCE"
    proof_rows = [
        {"gate": "G1_input", "status": "PASS", "metric": "input commit", "value": git_head(), "interpretation": "Stage282 starts after Stage281 repeated positive gate."},
        {"gate": "G2_noise_resource", "status": "PASS" if all_pass else "FAIL", "metric": "variant pass count", "value": f"{sum(row['status'] == 'pass' for row in rows)}/{len(rows)}", "interpretation": "Both fast control and selected candidate must pass."},
        {"gate": "G3_failures", "status": "PASS" if all(int(row.get(key, 1)) == 0 for row in rows for key in ["pvw_failures", "scalar_failures", "pair_failures"]) else "FAIL", "metric": "failures", "value": "0 required", "interpretation": "No PVW/scalar/pair failures accepted."},
        {"gate": "G4_resource_reporting", "status": "PASS" if all(row.get("key_ratio") and row.get("time_maxrss_kb") for row in rows) else "FAIL", "metric": "key/RSS rows", "value": "present" if all(row.get("key_ratio") and row.get("time_maxrss_kb") for row in rows) else "missing", "interpretation": "Resource costs are reported, not hidden."},
        {"gate": "G5_decision", "status": decision, "metric": "stage decision", "value": decision, "interpretation": "Native target-parameter confirmation remains separate."},
    ]
    write_csv(PROOF, ["gate", "status", "metric", "value", "interpretation"], proof_rows)
    queue_rows = [
        {"priority": "P0", "route": "stage283_native_target_repeated_gate", "entry_condition": decision, "gate": "Run selected candidate on native target platform with target parameters.", "failure_action": "Keep local-only claim if native access remains unavailable."},
        {"priority": "P1", "route": "stage284_target_resource_refresh", "entry_condition": "native or local target run available", "gate": "Refresh target-size resource/keygen impact.", "failure_action": "Report resource caveat with speedup."},
    ]
    write_csv(QUEUE, ["priority", "route", "entry_condition", "gate", "failure_action"], queue_rows)

    write_text(COMMANDS, """# Stage282 Reproduction Commands

```bash
bash scripts/run_stage282_cmux_residual_noise_resource.sh
python3 scripts/build_stage282_cmux_residual_noise_resource.py
```

This is a small full-path include-zero noise/resource gate using `ffnt` as a
correctness/resource proxy; it is not target-parameter AVX512 performance
evidence.
""")
    table_rows = "\n".join(
        f"| {row['variant']} | {row['status']} | {row.get('trials','')} | {row.get('pvw_failures','')} | {row.get('scalar_failures','')} | {row.get('pair_failures','')} | {row.get('key_ratio','')} | {row.get('time_maxrss_kb','')} |"
        for row in rows
    )
    report = f"""# Stage282 CMUX Residual Noise/Resource Gate

Decision: `{decision}`.

Stage282 checks the selected `backend_sub_decomp_dual` candidate against the
guarded fast control on the existing include-zero full-smoke noise/resource
harness. This run uses `ffnt` as a correctness/resource proxy because the
small full-smoke harness is not stable under `spqlios_avx512`; it is not
target-parameter AVX512 latency evidence.

| variant | status | trials | pvw failures | scalar failures | pair failures | key ratio | max RSS KB |
| --- | --- | ---: | ---: | ---: | ---: | ---: | ---: |
{table_rows}

## Proof Gate

| gate | status | metric | value | interpretation |
| --- | --- | --- | --- | --- |
""" + "\n".join(
        f"| {row['gate']} | {row['status']} | {row['metric']} | {row['value']} | {row['interpretation']} |"
        for row in proof_rows
    ) + f"""

Generated from input head `{git_head()}`.
"""
    write_text(DOC, report)
    write_text(REPORT, report)

    append_once(CURRENT_GOAL, "<!-- stage282-cmux-residual-noise-resource -->", f"""<!-- stage282-cmux-residual-noise-resource -->
### Stage282 CMUX residual noise/resource

`{decision}` runs the selected `backend_sub_decomp_dual` candidate and fast
control through the include-zero full-smoke noise/resource proxy. Native
target-parameter evidence remains open.
""")
    append_once(HYPOTHESES, "H10_stage282_cmux_residual_noise_resource:", f"""H10_stage282_cmux_residual_noise_resource:
  status: {decision}
  evidence:
    - repro/stage282_cmux_residual_noise_resource/noise_resource_summary.csv
    - repro/stage282_cmux_residual_noise_resource/proof_gate.csv
    - docs/stage282_cmux_residual_noise_resource.md
  conclusion: >
    Stage282 checks selected candidate correctness/noise/resource on the
    include-zero full-smoke proxy harness. Native target-parameter evidence remains required.
""")
    append_once(RUN_LOG, "stage282-cmux-residual-noise-resource-001", f"""stage282-cmux-residual-noise-resource-001,2026-07-04,{git_head()},Stage 282,ffnt-local-proxy,bash scripts/run_stage282_cmux_residual_noise_resource.sh; python scripts/build_stage282_cmux_residual_noise_resource.py,"include-zero selected CMUX residual candidate small full-path noise/resource gate",n/a,{decision},"Small full-path noise/resource proxy; native target evidence still required.",docs/stage282_cmux_residual_noise_resource.md; repro/stage282_cmux_residual_noise_resource/proof_gate.csv
""")
    append_once(MANIFEST, "- stage282_cmux_residual_noise_resource:", """- stage282_cmux_residual_noise_resource:
  - `docs/stage282_cmux_residual_noise_resource.md`
  - `scripts/run_stage282_cmux_residual_noise_resource.sh`
  - `scripts/build_stage282_cmux_residual_noise_resource.py`
  - `repro/stage282_cmux_residual_noise_resource/`
""")
    append_once(CHECKLIST, "<!-- stage282-cmux-residual-noise-resource-checklist -->", f"""<!-- stage282-cmux-residual-noise-resource-checklist -->
- [x] Stage282 records `{decision}` for selected CMUX residual candidate noise/resource smoke.
""")
    build_index()
    print(decision)


if __name__ == "__main__":
    main()
