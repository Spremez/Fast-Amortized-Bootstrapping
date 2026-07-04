#!/usr/bin/env python3
"""Stage297: bind direct-DFT high-stat speed to target resource side conditions."""

from __future__ import annotations

import csv
import hashlib
import re
import subprocess
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "repro" / "stage297_direct_dft_resource_sidecondition"
RAW = OUT / "raw"
DOC = ROOT / "docs" / "stage297_direct_dft_resource_sidecondition.md"
THEORY = ROOT / "theory_checks" / "stage297_direct_dft_resource_model.md"
VARIANT = ROOT / "algorithm_variants" / "mat_rlwe_sab_stage297_direct_dft_resource_sidecondition.md"
PLAN = ROOT / "experiments" / "stage297_direct_dft_resource_sidecondition_plan.md"
RUNNER = ROOT / "scripts" / "run_stage297_direct_dft_resource_sidecondition.sh"
BUILDER = ROOT / "scripts" / "build_stage297_direct_dft_resource_sidecondition.py"

GOAL = ROOT / "docs" / "current_codex_goal_sab_completion.md"
ROADMAP = ROOT / "docs" / "roadmap_stage19_plus.md"
HYPOTHESES = ROOT / "hypotheses" / "hypothesis_register.yaml"
MANIFEST = ROOT / "repro" / "artifact_manifest.md"
CHECKLIST = ROOT / "repro" / "reproduction_checklist.md"
RUN_LOG = ROOT / "repro" / "run_log.csv"

TARGET_RESOURCE = OUT / "target_resource_probe.csv"
LINKED_RESOURCE = OUT / "linked_resource_summary.csv"
PROOF = OUT / "proof_gate.csv"
CLAIMS = OUT / "claim_boundary.csv"
NEXT = OUT / "next_stage_queue.csv"
COMMANDS = OUT / "reproduction_commands.md"
REPORT = OUT / "stage297_report.md"
ARTIFACT = OUT / "artifact_index.csv"

DECISION_PASS = "PASS_STAGE297_DIRECT_DFT_RESOURCE_SIDECONDITION_LOCAL"
DECISION_FAIL = "FAIL_STAGE297_DIRECT_DFT_RESOURCE_SIDECONDITION"

NOISE_SUMMARY_RE = re.compile(
    r"SAB_PVW_NONBINARY_TARGET_NOISE summary target_full mode=(?P<mode>\S+) "
    r"r=(?P<r>\d+) trials=(?P<trials>\d+) points=(?P<points>\d+) "
    r"expected_model_pvw_failures=(?P<expected_model_pvw_failures>\d+) "
    r"expected_model_scalar_failures=(?P<expected_model_scalar_failures>\d+) "
    r"pair_failures=(?P<pair_failures>\d+) "
    r"expected_model_pvw_log2_sigma_torus=(?P<expected_model_pvw_log2_sigma_torus>-?inf|-?[0-9.]+) "
    r"expected_model_scalar_log2_sigma_torus=(?P<expected_model_scalar_log2_sigma_torus>-?inf|-?[0-9.]+) "
    r"pair_log2_sigma_torus=(?P<pair_log2_sigma_torus>-?inf|-?[0-9.]+) "
    r"pair_log2_max_abs_torus=(?P<pair_log2_max_abs_torus>-?inf|-?[0-9.]+) "
    r"gate=(?P<gate>Pass|Fail)"
)
NOISE_OVERALL_RE = re.compile(r"SAB_PVW_NONBINARY_TARGET_NOISE target full final-output gate: (?P<overall_gate>Pass|Fail)")
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


def write_csv(path: Path, fields: list[str], rows: list[dict[str, object]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields, lineterminator="\n")
        writer.writeheader()
        for row in rows:
            writer.writerow({field: row.get(field, "") for field in fields})


def read_csv(path: Path) -> list[dict[str, str]]:
    if not path.exists():
        return []
    with path.open(newline="", encoding="utf-8") as handle:
        return list(csv.DictReader(handle))


def append_once(path: Path, marker: str, text: str) -> None:
    current = read_text(path)
    if marker in current:
        return
    sep = "" if current.endswith("\n") or not current else "\n"
    write_text(path, current + sep + text)


def append_run_log(row: dict[str, str]) -> None:
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


def parse_variant(variant: str) -> dict[str, object]:
    run_log = RAW / variant / "run.log"
    time_log = RAW / variant / "time.log"
    row: dict[str, object] = {"variant": variant, "source_run_log": rel(run_log), "source_time_log": rel(time_log)}
    text = read_text(run_log)
    match = NOISE_SUMMARY_RE.search(text)
    if match:
        row.update(match.groupdict())
    overall = NOISE_OVERALL_RE.search(text)
    if overall:
        row["overall_gate"] = overall.group("overall_gate")
    time_match = TIME_RSS_RE.search(read_text(time_log))
    if time_match:
        row.update(time_match.groupdict())
    row["status"] = "pass" if row.get("gate") == "Pass" and row.get("overall_gate") == "Pass" and row.get("pair_failures") == "0" else "fail"
    return row


def md_table(rows: list[dict[str, object]], fields: list[str]) -> str:
    out = ["| " + " | ".join(fields) + " |", "| " + " | ".join(["---"] * len(fields)) + " |"]
    for row in rows:
        out.append("| " + " | ".join(str(row.get(field, "")) for field in fields) + " |")
    return "\n".join(out)


def artifact_index(paths: list[Path]) -> None:
    rows = []
    for path in paths:
        if path.exists():
            data = path.read_bytes()
            rows.append({"path": rel(path), "bytes": len(data), "sha256": hashlib.sha256(data).hexdigest()})
    write_csv(ARTIFACT, ["path", "bytes", "sha256"], rows)


def main() -> None:
    OUT.mkdir(parents=True, exist_ok=True)
    target_rows = [parse_variant("selected_control"), parse_variant("direct_dft")]
    for row in target_rows:
        row["rss_vs_selected_ratio"] = ""
    selected_rss = fnum(target_rows[0].get("time_maxrss_kb"))
    direct_rss = fnum(target_rows[1].get("time_maxrss_kb"))
    if selected_rss and direct_rss:
        target_rows[1]["rss_vs_selected_ratio"] = f"{direct_rss / selected_rss:.6f}"
    write_csv(TARGET_RESOURCE, [
        "variant", "status", "mode", "r", "trials", "points",
        "pair_failures", "pair_log2_sigma_torus", "pair_log2_max_abs_torus",
        "gate", "overall_gate", "time_maxrss_kb", "rss_vs_selected_ratio",
        "source_run_log", "source_time_log",
    ], target_rows)

    stage296_rows = read_csv(ROOT / "repro" / "stage296_direct_dft_highstat" / "perf_summary.csv")
    stage293_rows = read_csv(ROOT / "repro" / "stage293_direct_dft_noise_resource" / "resource_summary.csv")
    stage296_comp = next((row for row in stage296_rows if row.get("variant") == "comparison"), {})
    stage296_direct = next((row for row in stage296_rows if row.get("variant") == "perf_direct_dft"), {})
    stage293_resource = stage293_rows[0] if stage293_rows else {}
    linked = [{
        "speedup_vs_selected_control_T_over_r": stage296_comp.get("direct_dft_vs_selected_control_mean", ""),
        "speedup_vs_repeated_scalar_T_over_r": stage296_direct.get("speedup_vs_repeated_scalar_mean", ""),
        "stage293_target_key_ratio": stage293_resource.get("key_ratio", ""),
        "stage293_target_pvw_key_bytes": stage293_resource.get("pvw_key_bytes", ""),
        "stage293_target_scalar_repeated_key_bytes": stage293_resource.get("scalar_repeated_key_bytes", ""),
        "stage293_target_keygen_lane_ratio": stage293_resource.get("keygen_lane_ratio", ""),
        "stage293_target_time_maxrss_kb": stage293_resource.get("time_maxrss_kb", ""),
        "stage297_selected_time_maxrss_kb": target_rows[0].get("time_maxrss_kb", ""),
        "stage297_direct_time_maxrss_kb": target_rows[1].get("time_maxrss_kb", ""),
        "stage297_direct_vs_selected_rss_ratio": target_rows[1].get("rss_vs_selected_ratio", ""),
        "resource_scope": "Stage293 key/keygen/RSS target binary resource plus Stage297 include-zero target final-output RSS probe.",
    }]
    write_csv(LINKED_RESOURCE, [
        "speedup_vs_selected_control_T_over_r",
        "speedup_vs_repeated_scalar_T_over_r",
        "stage293_target_key_ratio",
        "stage293_target_pvw_key_bytes",
        "stage293_target_scalar_repeated_key_bytes",
        "stage293_target_keygen_lane_ratio",
        "stage293_target_time_maxrss_kb",
        "stage297_selected_time_maxrss_kb",
        "stage297_direct_time_maxrss_kb",
        "stage297_direct_vs_selected_rss_ratio",
        "resource_scope",
    ], linked)

    stage296_ok = "PASS_STAGE296_DIRECT_DFT_HIGHSTAT_LOCAL" in read_text(ROOT / "repro" / "stage296_direct_dft_highstat" / "proof_gate.csv")
    target_ok = all(row.get("status") == "pass" for row in target_rows)
    key_ok = fnum(stage293_resource.get("key_ratio")) > 0 and fnum(stage293_resource.get("key_ratio")) <= 1.10
    rss_ok = direct_rss > 0 and selected_rss > 0 and (direct_rss / selected_rss) <= 1.10
    decision = DECISION_PASS if stage296_ok and target_ok and key_ok and rss_ok else DECISION_FAIL
    proof_rows = [
        {"gate": "G1_prior_stage296", "status": "PASS" if stage296_ok else "FAIL", "metric": "Stage296 decision", "value": "positive" if stage296_ok else "missing", "interpretation": "Resource side condition is only meaningful after high-stat speed evidence."},
        {"gate": "G2_target_probe_correctness", "status": "PASS" if target_ok else "FAIL", "metric": "selected/direct target probes", "value": f"{sum(row.get('status') == 'pass' for row in target_rows)}/{len(target_rows)}", "interpretation": "Both target final-output probes must pass scalar-equivalence."},
        {"gate": "G3_key_resource_link", "status": "PASS" if key_ok else "FAIL", "metric": "Stage293 key ratio", "value": stage293_resource.get("key_ratio", "missing"), "interpretation": "Direct DFT adds no key format; PVW target key overhead remains the selected PVW-SAB key overhead."},
        {"gate": "G4_rss_probe", "status": "PASS" if rss_ok else "FAIL", "metric": "direct/selected max RSS", "value": target_rows[1].get("rss_vs_selected_ratio", "missing"), "interpretation": "Direct DFT target final-output probe should not create a large RSS regression."},
        {"gate": "G5_claim_boundary", "status": "PASS", "metric": "scope", "value": "local resource side condition", "interpretation": "This is not native counter attribution or stage-wise noise."},
        {"gate": "G6_decision", "status": decision, "metric": "stage decision", "value": decision, "interpretation": "Controls Stage298 route."},
    ]
    write_csv(PROOF, ["gate", "status", "metric", "value", "interpretation"], proof_rows)
    write_csv(CLAIMS, ["claim", "status", "supported_statement", "not_supported"], [
        {"claim": "resource_side_condition", "status": decision, "supported_statement": "Stage296 speedup is accompanied by target key-ratio evidence and Stage297 selected/direct RSS probes.", "not_supported": "full native memory profiling or all-parameter resource matrix."},
        {"claim": "direct_dft_key_overhead", "status": "no_new_key_format", "supported_statement": "The direct-DFT flag changes decomposition/materialization, not SAB key generation.", "not_supported": "a proof that every future direct-DFT variant has no resource cost."},
        {"claim": "paper_grade", "status": "not_yet", "supported_statement": "Resource side condition is locally positive.", "not_supported": "native counter attribution, stage-wise noise, literature novelty, or parameter generalization."},
    ])
    write_csv(NEXT, ["priority", "route", "entry_condition", "gate", "failure_action"], [
        {"priority": "P0", "route": "stage298_stagewise_noise_or_native_counter", "entry_condition": decision, "gate": "Choose between target stage-wise noise and native counter/resource run.", "failure_action": "Keep Stage297 as local side condition only."},
        {"priority": "P1", "route": "stage298_parameter_generalization", "entry_condition": "after stage-wise/native gate", "gate": "Repeat on at least one additional parameter/branch.", "failure_action": "Limit claim to SET_2_3_2048 include-zero r=4."},
    ])

    write_text(COMMANDS, """# Stage297 Reproduction Commands

```bash
STAGE297_TRIALS=1 FFT_LIB=spqlios_avx512 PARAM=SET_2_3_2048 bash scripts/run_stage297_direct_dft_resource_sidecondition.sh
python3 scripts/build_stage297_direct_dft_resource_sidecondition.py
```

This stage records a target final-output RSS/correctness probe for
selected-control and direct-DFT. It links key/keygen/RSS fields from Stage293
and high-stat throughput from Stage296.
""")
    report = f"""# Stage297 Direct DFT Resource Side Condition

Decision: `{decision}`.

Stage297 binds the Stage296 high-stat `T_bootstrap/r` result to target resource
side conditions. It does not change the algorithm and does not replace native
counter attribution.

## Target Probe

{md_table(target_rows, ["variant", "status", "r", "trials", "pair_failures", "time_maxrss_kb", "rss_vs_selected_ratio"])}

## Linked Resource

{md_table(linked, ["speedup_vs_selected_control_T_over_r", "speedup_vs_repeated_scalar_T_over_r", "stage293_target_key_ratio", "stage293_target_keygen_lane_ratio", "stage297_direct_vs_selected_rss_ratio"])}

## Proof Gate

{md_table(proof_rows, ["gate", "status", "metric", "value", "interpretation"])}

Generated from input head `{git_head()}`.
"""
    write_text(DOC, report)
    write_text(REPORT, report)
    write_text(THEORY, """# Stage297 Resource Model

Direct DFT does not introduce a new SAB key format. Its expected resource risk
is runtime scratch/materialization, not public key size. Therefore Stage297
checks two side conditions:

1. reuse Stage293 target key/keygen/RSS fields for the PVW-SAB representation;
2. run selected-control and direct-DFT target final-output probes under the same
   backend and compare max RSS.

This is a local resource side condition. It is not native hardware-counter
attribution and does not close stage-wise noise.
""")
    write_text(VARIANT, """# Stage297 Direct DFT Resource Side Condition

Variant under resource probe:

```text
MAT_TRGSW_SUB_DECOMP_DFT_DIRECT=true
```

The selected-control probe is identical except for the direct-DFT flag.
""")
    write_text(PLAN, """# Stage297 Experiment Plan

Gates:

- Stage296 high-stat speed evidence must be positive;
- selected-control and direct-DFT target probes must pass pair equivalence;
- linked Stage293 target key ratio must be present and not exceed 1.10;
- direct-DFT max RSS must not exceed selected-control max RSS by more than 10%;
- record claim boundary as local resource side condition only.
""")

    append_once(GOAL, "<!-- stage297-direct-dft-resource-sidecondition -->", f"""<!-- stage297-direct-dft-resource-sidecondition -->
### Stage297 direct DFT resource side condition

`{decision}` binds Stage296 high-stat speed evidence to target resource side
conditions. Direct DFT remains a no-new-key-format implementation variant; the
claim is local and still needs native/stage-wise expansion.
""")
    append_once(ROADMAP, "## Stage 297: Direct DFT Resource Side Condition", f"""## Stage 297: Direct DFT Resource Side Condition

Goal: ensure direct-DFT speed evidence is not hiding unacceptable key/RSS
growth.

Status: `{decision}`.
""")
    append_once(HYPOTHESES, "H297_direct_dft_resource_sidecondition:", f"""H297_direct_dft_resource_sidecondition:
  status: {decision}
  primary_metric: resource_side_condition_for_complete_sab_T_over_r
  evidence:
    - repro/stage297_direct_dft_resource_sidecondition/target_resource_probe.csv
    - repro/stage297_direct_dft_resource_sidecondition/linked_resource_summary.csv
    - repro/stage297_direct_dft_resource_sidecondition/proof_gate.csv
    - docs/stage297_direct_dft_resource_sidecondition.md
  conclusion: >
    Stage297 links the direct-DFT high-stat speedup to local key/RSS side
    conditions. It does not close native counter, stage-wise noise, or
    parameter-generalization gates.
""")
    append_once(MANIFEST, "- stage297_direct_dft_resource_sidecondition:", """- stage297_direct_dft_resource_sidecondition:
  - `docs/stage297_direct_dft_resource_sidecondition.md`
  - `scripts/run_stage297_direct_dft_resource_sidecondition.sh`
  - `scripts/build_stage297_direct_dft_resource_sidecondition.py`
  - `repro/stage297_direct_dft_resource_sidecondition/`
""")
    append_once(CHECKLIST, "<!-- stage297-direct-dft-resource-sidecondition-checklist -->", f"""<!-- stage297-direct-dft-resource-sidecondition-checklist -->
- [x] Stage297 records `{decision}` for direct DFT local resource side conditions.
""")
    append_run_log({
        "run_id": "stage297-direct-dft-resource-sidecondition-001",
        "date": "2026-07-04",
        "git_ref": git_head(),
        "stage": "Stage 297",
        "backend": "spqlios_avx512-local",
        "command": "STAGE297_TRIALS=1 FFT_LIB=spqlios_avx512 PARAM=SET_2_3_2048 bash scripts/run_stage297_direct_dft_resource_sidecondition.sh",
        "parameters": "BINARY SET_2_3_2048 r=4 include-zero selected/direct target RSS probe",
        "rng": "n/a",
        "status": decision,
        "notes": "Local resource side condition for Stage296 direct-DFT evidence.",
        "artifacts": "docs/stage297_direct_dft_resource_sidecondition.md; repro/stage297_direct_dft_resource_sidecondition/proof_gate.csv",
    })

    paths = [DOC, THEORY, VARIANT, PLAN, COMMANDS, REPORT, TARGET_RESOURCE, LINKED_RESOURCE, PROOF, CLAIMS, NEXT, RAW / "variant_plan.csv", RUNNER, BUILDER]
    paths.extend(sorted(RAW.glob("*/*.log")))
    artifact_index(paths)
    print(decision)


if __name__ == "__main__":
    main()
