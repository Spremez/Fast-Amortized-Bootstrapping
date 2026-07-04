#!/usr/bin/env python3
"""Stage293: direct-DFT target correctness/resource smoke with noise-harness audit."""

from __future__ import annotations

import csv
import hashlib
import re
import subprocess
from pathlib import Path
from typing import Dict, Iterable, List


ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "repro" / "stage293_direct_dft_noise_resource"
RAW = OUT / "raw"
DOC = ROOT / "docs" / "stage293_direct_dft_noise_resource.md"
THEORY = ROOT / "theory_checks" / "stage293_direct_dft_noise_resource_model.md"
VARIANT = ROOT / "algorithm_variants" / "mat_rlwe_sab_stage293_direct_dft_noise_resource.md"
PLAN = ROOT / "experiments" / "stage293_direct_dft_noise_resource_plan.md"
RUNNER = ROOT / "scripts" / "run_stage293_direct_dft_noise_resource.sh"
BUILDER = ROOT / "scripts" / "build_stage293_direct_dft_noise_resource.py"

GOAL = ROOT / "docs" / "current_codex_goal_sab_completion.md"
ROADMAP = ROOT / "docs" / "roadmap_stage19_plus.md"
HYPOTHESES = ROOT / "hypotheses" / "hypothesis_register.yaml"
MANIFEST = ROOT / "repro" / "artifact_manifest.md"
CHECKLIST = ROOT / "repro" / "reproduction_checklist.md"
RUN_LOG = ROOT / "repro" / "run_log.csv"

SUMMARY = OUT / "stage293_summary.csv"
RESOURCE = OUT / "resource_summary.csv"
NOISE_ATTEMPT = OUT / "noise_harness_attempt.csv"
PROOF = OUT / "proof_gate.csv"
NEXT = OUT / "next_stage_queue.csv"
COMMANDS = OUT / "reproduction_commands.md"
REPORT = OUT / "stage293_report.md"
ARTIFACT = OUT / "artifact_index.csv"

DECISION_PASS = "PASS_STAGE293_DIRECT_DFT_TARGET_CORRECT_RESOURCE_SMOKE_NOISE_PENDING"
DECISION_FAIL = "FAIL_STAGE293_DIRECT_DFT_TARGET_CORRECT_RESOURCE"

TARGET_CORRECT_RE = re.compile(r"SAB_PVW target full bootstrap gate: (?P<gate>Pass|Fail)")
TARGET_LANE_RE = re.compile(
    r"SAB_PVW target full bootstrap binary lane equivalence r=(?P<r>\d+) "
    r"h=(?P<h>\d+) r_prec=(?P<r_prec>\d+): (?P<lane_gate>Pass|Fail)"
)
RESOURCE_GATE_RE = re.compile(r"SAB_PVW_RESOURCE target_full gate: (?P<gate>Pass|Fail)")
KEY_BYTES_RE = re.compile(
    r"SAB_PVW_RESOURCE key_bytes target_full r=(?P<r>\d+) "
    r"pvw_estimated_key_bytes=(?P<pvw_key_bytes>\d+) "
    r"scalar_one_estimated_key_bytes=(?P<scalar_one_key_bytes>\d+) "
    r"scalar_repeated_estimated_key_bytes=(?P<scalar_repeated_key_bytes>\d+) "
    r"pvw_vs_scalar_repeated_ratio=(?P<key_ratio>[0-9.]+)"
)
PVW_KEYGEN_RE = re.compile(
    r"SAB_PVW_RESOURCE keygen target_full r=(?P<r>\d+) mode=pvw "
    r"pvw_sab_keygen_us=(?P<pvw_keygen_us>\d+)"
)
SCALAR_KEYGEN_RE = re.compile(
    r"SAB_PVW_RESOURCE keygen target_full r=(?P<r>\d+) mode=scalar "
    r"scalar_repeated_sab_keygen_us=(?P<scalar_keygen_us>\d+) "
    r"scalar_lane_avg_keygen_us=(?P<scalar_lane_keygen_us>[0-9.]+)"
)
RSS_RE = re.compile(
    r"SAB_PVW_RESOURCE rss target_full r=(?P<r>\d+) mode=(?P<mode>\S+) "
    r"label=(?P<label>\S+) vmrss_kb=(?P<vmrss_kb>\d+) vmhwm_kb=(?P<vmhwm_kb>\d+)"
)
TIME_RSS_RE = re.compile(r"Maximum resident set size \(kbytes\): (?P<time_maxrss_kb>\d+)")


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
    path.write_text("\n".join(line.rstrip() for line in text.strip().splitlines()) + "\n", encoding="utf-8", newline="\n")


def write_csv(path: Path, fields: Iterable[str], rows: Iterable[Dict[str, object]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(fields), lineterminator="\n")
        writer.writeheader()
        for row in rows:
            writer.writerow({field: row.get(field, "") for field in writer.fieldnames})


def append_once(path: Path, marker: str, text: str) -> None:
    current = read_text(path)
    if marker in current:
        return
    sep = "" if current.endswith("\n") or not current else "\n"
    write_text(path, current + sep + text)


def append_run_log(row: Dict[str, str]) -> None:
    current = read_text(RUN_LOG)
    if row["run_id"] in current:
        return
    with RUN_LOG.open("a", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(
            handle,
            fieldnames=["run_id", "date", "git_ref", "stage", "backend", "command", "parameters", "rng", "status", "notes", "artifacts"],
            lineterminator="\n",
        )
        writer.writerow(row)


def fnum(value: object) -> float:
    try:
        return float(value)
    except (TypeError, ValueError):
        return 0.0


def parse_target_correctness() -> Dict[str, object]:
    run_log = RAW / "target_correctness" / "run.log"
    text = read_text(run_log)
    lane = TARGET_LANE_RE.search(text)
    gate = TARGET_CORRECT_RE.search(text)
    return {
        "case": "target_correctness",
        "status": "pass" if gate and gate.group("gate") == "Pass" else "fail",
        "gate": gate.group("gate") if gate else "MISSING",
        "r": lane.group("r") if lane else "",
        "h": lane.group("h") if lane else "",
        "r_prec": lane.group("r_prec") if lane else "",
        "lane_gate": lane.group("lane_gate") if lane else "",
        "source_log": rel(run_log),
    }


def parse_resource() -> Dict[str, object]:
    run_log = RAW / "target_resource" / "run.log"
    time_log = RAW / "target_resource" / "time.log"
    text = read_text(run_log)
    time_text = read_text(time_log)
    row: Dict[str, object] = {"case": "target_resource", "source_log": rel(run_log), "source_time_log": rel(time_log)}
    for regex in [RESOURCE_GATE_RE, KEY_BYTES_RE, PVW_KEYGEN_RE, SCALAR_KEYGEN_RE]:
        match = regex.search(text)
        if match:
            row.update(match.groupdict())
    for match in RSS_RE.finditer(text):
        label = match.group("label")
        mode = match.group("mode")
        row[f"{mode}_{label}_vmrss_kb"] = match.group("vmrss_kb")
        row[f"{mode}_{label}_vmhwm_kb"] = match.group("vmhwm_kb")
    time_match = TIME_RSS_RE.search(time_text)
    if time_match:
        row.update(time_match.groupdict())
    row["pvw_keygen_lane_us"] = f"{fnum(row.get('pvw_keygen_us')) / fnum(row.get('r')):.3f}" if fnum(row.get("r")) else ""
    row["keygen_lane_ratio"] = (
        f"{fnum(row.get('pvw_keygen_lane_us')) / fnum(row.get('scalar_lane_keygen_us')):.6f}"
        if fnum(row.get("scalar_lane_keygen_us")) else ""
    )
    row["status"] = "pass" if row.get("gate") == "Pass" and row.get("key_ratio") and row.get("time_maxrss_kb") else "fail"
    return row


def parse_noise_attempts() -> List[Dict[str, object]]:
    rows: List[Dict[str, object]] = []
    for path in sorted(RAW.glob("*/time.log")):
        case = path.parent.name
        if case in {"target_correctness", "target_resource"}:
            continue
        text = read_text(path)
        status = "unknown"
        if "Command terminated by signal 11" in text:
            status = "segfault_signal_11"
        elif "Exit status: 0" in text:
            status = "completed"
        rows.append({"case": case, "status": status, "source_time_log": rel(path), "source_run_log": rel(path.parent / "run.log")})
    return rows


def md_table(rows: List[Dict[str, object]], fields: List[str]) -> str:
    out = ["| " + " | ".join(fields) + " |", "| " + " | ".join(["---"] * len(fields)) + " |"]
    for row in rows:
        out.append("| " + " | ".join(str(row.get(field, "")) for field in fields) + " |")
    return "\n".join(out)


def artifact_index(paths: List[Path]) -> None:
    rows = []
    for path in paths:
        if not path.exists():
            continue
        data = path.read_bytes()
        rows.append({"path": rel(path), "bytes": len(data), "sha256": hashlib.sha256(data).hexdigest()})
    write_csv(ARTIFACT, ["path", "bytes", "sha256"], rows)


def main() -> None:
    OUT.mkdir(parents=True, exist_ok=True)
    correctness = parse_target_correctness()
    resource = parse_resource()
    noise_attempts = parse_noise_attempts()
    stage292_ok = "PASS_STAGE292_DIRECT_DFT_FULLSAB_POSITIVE_NOISE_RESOURCE_REQUIRED" in read_text(
        ROOT / "repro" / "stage292_fullsab_direct_dft_ab" / "proof_gate.csv"
    )
    decision = DECISION_PASS if stage292_ok and correctness["status"] == "pass" and resource["status"] == "pass" else DECISION_FAIL

    summary_rows = [
        {"case": "stage292_input", "status": "pass" if stage292_ok else "fail", "value": "positive_full_sab_ab" if stage292_ok else "missing"},
        {"case": "target_correctness", "status": correctness["status"], "value": correctness.get("gate", "")},
        {"case": "target_resource", "status": resource["status"], "value": resource.get("gate", "")},
        {"case": "full_noise_highstat", "status": "pending", "value": "spqlios full-noise harness requires repair or native alternative"},
        {"case": "decision", "status": decision, "value": decision},
    ]
    write_csv(SUMMARY, ["case", "status", "value"], summary_rows)
    write_csv(RESOURCE, [
        "case", "status", "r", "pvw_key_bytes", "scalar_repeated_key_bytes",
        "key_ratio", "pvw_keygen_us", "pvw_keygen_lane_us",
        "scalar_keygen_us", "scalar_lane_keygen_us", "keygen_lane_ratio",
        "pvw_after_pvw_sab_keygen_vmhwm_kb",
        "scalar_after_scalar_repeated_sab_keygen_vmhwm_kb",
        "time_maxrss_kb", "source_log", "source_time_log",
    ], [resource])
    write_csv(NOISE_ATTEMPT, ["case", "status", "source_time_log", "source_run_log"], noise_attempts)

    proof_rows = [
        {"gate": "G1_stage292_input", "status": "PASS" if stage292_ok else "FAIL", "metric": "Stage292 decision", "value": "positive_full_sab_ab" if stage292_ok else "missing_or_not_positive", "interpretation": "Side-condition smoke follows only after full-SAB T/r improvement."},
        {"gate": "G2_target_correctness", "status": "PASS" if correctness["status"] == "pass" else "FAIL", "metric": "target full bootstrap gate", "value": correctness.get("gate", ""), "interpretation": "Direct DFT candidate must preserve target lane equivalence."},
        {"gate": "G3_target_resource", "status": "PASS" if resource["status"] == "pass" else "FAIL", "metric": "key/RSS resource", "value": f"key_ratio={resource.get('key_ratio', '')};rss={resource.get('time_maxrss_kb', '')}", "interpretation": "Key size/keygen/RSS are recorded for the target parameter."},
        {"gate": "G4_noise_boundary", "status": "PENDING", "metric": "full-noise high-stat", "value": "not_claimed", "interpretation": "SPQLIOS full-noise harness is not used as a pass gate until repaired; no high-stat noise claim is made."},
        {"gate": "G5_decision", "status": decision, "metric": "stage decision", "value": decision, "interpretation": "Positive smoke supports continued work; final noise closure remains open."},
    ]
    write_csv(PROOF, ["gate", "status", "metric", "value", "interpretation"], proof_rows)
    write_csv(NEXT, ["priority", "route", "entry_condition", "gate", "failure_action"], [
        {"priority": "P0", "route": "stage294_spqlios_noise_harness_repair", "entry_condition": decision, "gate": "Repair or replace full-noise harness under SPQLIOS for direct DFT.", "failure_action": "Keep noise claim pending."},
        {"priority": "P1", "route": "stage294_direct_dft_highstat_perf", "entry_condition": decision, "gate": "Run 10-run T/r refresh for direct DFT if time/platform budget allows.", "failure_action": "Keep Stage292 as 3-run local evidence."},
    ])

    write_text(COMMANDS, """# Stage293 Reproduction Commands

```bash
FFT_LIB=spqlios_avx512 PARAM=SET_2_3_2048 bash scripts/run_stage293_direct_dft_noise_resource.sh
python3 scripts/build_stage293_direct_dft_noise_resource.py
```

This stage records target correctness and target resource smoke for the direct
DFT candidate. It does not claim high-stat noise closure.
""")
    report = f"""# Stage293 Direct DFT Target Correctness/Resource Smoke

Decision: `{decision}`.

Stage293 validates the Stage292 direct-DFT candidate on target correctness and
target resource reporting under `spqlios_avx512`. The full-noise/high-stat
claim remains pending because the older SPQLIOS full-noise harness is not a
reliable pass gate in this configuration.

## Summary

{md_table(summary_rows, ["case", "status", "value"])}

## Resource

{md_table([resource], ["case", "status", "r", "key_ratio", "pvw_keygen_lane_us", "scalar_lane_keygen_us", "keygen_lane_ratio", "time_maxrss_kb"])}

## Noise Harness Attempts

{md_table(noise_attempts, ["case", "status", "source_time_log"])}

## Proof Gate

{md_table(proof_rows, ["gate", "status", "metric", "value", "interpretation"])}

Generated from input head `{git_head()}`.
"""
    write_text(DOC, report)
    write_text(REPORT, report)
    write_text(THEORY, """# Stage293 Direct DFT Side-Condition Model

Direct DFT changes a hot-path representation conversion:

```text
DFT(decompose(in2 - in1))
```

It should not change key material, selector distribution, or key size. Stage293
therefore records target full-bootstrap equivalence and target key/RSS
resource rows. High-stat noise remains a separate proof obligation because the
legacy SPQLIOS full-noise harness is not stable enough to serve as a pass gate
for this candidate.
""")
    write_text(VARIANT, """# Stage293 Direct DFT Target Smoke Variant

Candidate flag:

```text
MAT_TRGSW_SUB_DECOMP_DFT_DIRECT=true
```

Companion selected-path flags:

```text
SAB_PVW_SUB_DECOMP_FUSION=true
MAT_TRGSW_AVX512_SUB_DECOMP=true
SAB_PVW_BACKEND_FROM_DFT_ADD=true
SAB_PVW_DUAL_SUB_CMUX=true
SAB_PVW_SUBA_INCLUDE_ZERO_COEFF_ONE_FAST=true
```
""")
    write_text(PLAN, """# Stage293 Experiment Plan

Goal: keep the Stage292 positive result disciplined by checking target
correctness and target resource side conditions before any stronger claim.

Gates:

- target full bootstrap equivalence must pass;
- target key/RSS resource rows must be present;
- high-stat noise is explicitly pending, not assumed from performance.
""")

    append_once(GOAL, "<!-- stage293-direct-dft-noise-resource -->", f"""<!-- stage293-direct-dft-noise-resource -->
### Stage293 direct DFT target correctness/resource smoke

`{decision}` records target correctness and resource side conditions for the
Stage292 direct-DFT candidate. High-stat noise remains pending because the
SPQLIOS full-noise harness needs repair or replacement before it can support a
noise claim.
""")
    append_once(ROADMAP, "## Stage 293: Direct DFT Target Correctness/Resource Smoke", f"""## Stage 293: Direct DFT Target Correctness/Resource Smoke

Goal: validate Stage292 direct DFT target correctness and resource reporting.

Status: `{decision}`. High-stat noise remains pending.
""")
    append_once(HYPOTHESES, "H293_direct_dft_noise_resource:", f"""H293_direct_dft_noise_resource:
  status: {decision}
  primary_metric: target_correctness_resource_smoke
  evidence:
    - repro/stage293_direct_dft_noise_resource/stage293_summary.csv
    - repro/stage293_direct_dft_noise_resource/resource_summary.csv
    - repro/stage293_direct_dft_noise_resource/proof_gate.csv
    - docs/stage293_direct_dft_noise_resource.md
  conclusion: >
    Stage293 records target correctness/resource smoke for the direct-DFT
    candidate. Noise high-stat closure is pending and must not be inferred.
""")
    append_once(MANIFEST, "- stage293_direct_dft_noise_resource:", """- stage293_direct_dft_noise_resource:
  - `docs/stage293_direct_dft_noise_resource.md`
  - `scripts/run_stage293_direct_dft_noise_resource.sh`
  - `scripts/build_stage293_direct_dft_noise_resource.py`
  - `repro/stage293_direct_dft_noise_resource/`
""")
    append_once(CHECKLIST, "<!-- stage293-direct-dft-noise-resource-checklist -->", f"""<!-- stage293-direct-dft-noise-resource-checklist -->
- [x] Stage293 records `{decision}` for direct DFT target correctness/resource smoke; high-stat noise remains pending.
""")
    append_run_log({
        "run_id": "stage293-direct-dft-noise-resource-001",
        "date": "2026-07-04",
        "git_ref": git_head(),
        "stage": "Stage 293",
        "backend": "spqlios_avx512-local",
        "command": "FFT_LIB=spqlios_avx512 PARAM=SET_2_3_2048 bash scripts/run_stage293_direct_dft_noise_resource.sh",
        "parameters": "BINARY SET_2_3_2048 r=4 direct DFT",
        "rng": "n/a",
        "status": decision,
        "notes": "Target correctness/resource smoke; high-stat noise remains pending.",
        "artifacts": "docs/stage293_direct_dft_noise_resource.md; repro/stage293_direct_dft_noise_resource/proof_gate.csv",
    })

    paths = [DOC, THEORY, VARIANT, PLAN, COMMANDS, REPORT, SUMMARY, RESOURCE, NOISE_ATTEMPT, PROOF, NEXT, RAW / "variant_plan.csv", RUNNER, BUILDER]
    paths.extend(sorted(RAW.glob("*/*.log")))
    artifact_index(paths)
    print(decision)


if __name__ == "__main__":
    main()
