#!/usr/bin/env python3
"""Build Stage277 include-zero fast repeated/resource artifacts."""

from __future__ import annotations

import csv
import hashlib
import re
import subprocess
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
REPRO = ROOT / "repro" / "stage277_include_zero_fast_repeated_resource"
RAW = REPRO / "raw"
DOC = ROOT / "docs" / "stage277_include_zero_fast_repeated_resource.md"
CURRENT_GOAL = ROOT / "docs" / "current_codex_goal_sab_completion.md"
HYPOTHESES = ROOT / "hypotheses" / "hypothesis_register.yaml"
RUN_LOG = ROOT / "repro" / "run_log.csv"
MANIFEST = ROOT / "repro" / "artifact_manifest.md"
CHECKLIST = ROOT / "repro" / "reproduction_checklist.md"

CORRECTNESS_RE = re.compile(
    r"SAB_PVW_NONBINARY_BENCH correctness target_full "
    r"mode=(?P<mode>\S+) r=(?P<r>\d+) h=(?P<h>\d+) "
    r"r_prec=(?P<r_prec>\d+): (?P<gate>Pass|Fail)"
)
SUMMARY_RE = re.compile(
    r"SAB_PVW_NONBINARY_BENCH summary target_full "
    r"mode=(?P<mode>\S+) r=(?P<r>\d+) reps=(?P<reps>\d+) "
    r"pvw_avg_us=(?P<pvw_avg_us>[0-9.]+) "
    r"pvw_stddev_us=(?P<pvw_stddev_us>[0-9.]+) "
    r"pvw_lane_avg_us=(?P<pvw_lane_avg_us>[0-9.]+) "
    r"scalar_repeated_avg_us=(?P<scalar_repeated_avg_us>[0-9.]+) "
    r"scalar_stddev_us=(?P<scalar_stddev_us>[0-9.]+) "
    r"scalar_lane_avg_us=(?P<scalar_lane_avg_us>[0-9.]+) "
    r"speedup_vs_scalar_repeated=(?P<speedup_vs_scalar_repeated>[0-9.]+)x "
    r"speedup_stddev=(?P<speedup_stddev>[0-9.]+) "
    r"t_bootstrap_over_r_pvw_us=(?P<t_bootstrap_over_r_pvw_us>[0-9.]+) "
    r"t_bootstrap_over_r_scalar_us=(?P<t_bootstrap_over_r_scalar_us>[0-9.]+)"
)
KEY_BYTES_RE = re.compile(
    r"SAB_PVW_NONBINARY_RESOURCE key_bytes full_smoke mode=(?P<mode>\S+) r=(?P<r>\d+) "
    r"pvw_estimated_key_bytes=(?P<pvw_estimated_key_bytes>\d+) "
    r"scalar_one_estimated_key_bytes=(?P<scalar_one_estimated_key_bytes>\d+) "
    r"scalar_repeated_estimated_key_bytes=(?P<scalar_repeated_estimated_key_bytes>\d+) "
    r"pvw_vs_scalar_repeated_ratio=(?P<pvw_vs_scalar_repeated_ratio>[0-9.]+)"
)
NOISE_SUMMARY_RE = re.compile(
    r"SAB_PVW_NONBINARY_FULL_NOISE summary mode=(?P<mode>\S+) r=(?P<r>\d+) "
    r"trials=(?P<trials>\d+) points=(?P<points>\d+) "
    r"pvw_failures=(?P<pvw_failures>\d+) scalar_failures=(?P<scalar_failures>\d+) "
    r"pair_failures=(?P<pair_failures>\d+) "
    r"pvw_log2_sigma_torus=(?P<pvw_log2_sigma_torus>-?inf|-?[0-9.]+) "
    r"scalar_log2_sigma_torus=(?P<scalar_log2_sigma_torus>-?inf|-?[0-9.]+) "
    r"pair_log2_sigma_torus=(?P<pair_log2_sigma_torus>-?inf|-?[0-9.]+) "
    r"pair_log2_max_abs_torus=(?P<pair_log2_max_abs_torus>-?inf|-?[0-9.]+) "
    r"gate=(?P<gate>Pass|Fail)"
)
RESOURCE_GATE_RE = re.compile(
    r"SAB_PVW_INCLUDE_ZERO_FAST_RESOURCE full bootstrap gate: (?P<gate>Pass|Fail)"
)

VARIANTS = [
    "include_zero_coeff_one_fast",
    "backend_from_dft_add",
    "default",
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


def split_variant(name: str) -> str | None:
    suffix = "_include_zero_r4_reps2_run.log"
    if not name.endswith(suffix):
        return None
    stem = name.removesuffix(suffix)
    return stem if stem in VARIANTS else None


def parse_bench_logs() -> list[dict[str, str]]:
    rows: list[dict[str, str]] = []
    for path in sorted(RAW.glob("*_include_zero_r4_reps2_run.log")):
        variant = split_variant(path.name)
        if variant is None:
            continue
        text = path.read_text(encoding="utf-8", errors="replace")
        correctness = CORRECTNESS_RE.search(text)
        summary = SUMMARY_RE.search(text)
        if not correctness or not summary:
            raise SystemExit(f"missing correctness or summary line in {path}")
        row = summary.groupdict()
        corr = correctness.groupdict()
        row.update(
            {
                "variant": variant,
                "mode": corr["mode"],
                "h": corr["h"],
                "r_prec": corr["r_prec"],
                "correctness_gate": corr["gate"],
                "platform": "WSL2/Linux",
                "backend": "spqlios_avx512",
                "param": "SET_2_3",
                "primary_metric": "T_bootstrap/r",
                "avx_variant": "MAT_TRGSW_AVX512_SMALLR_SPECIALIZED",
                "log": rel(path),
            }
        )
        rows.append(row)
    rows.sort(key=lambda row: row["variant"])
    return rows


def parse_resource_log() -> tuple[list[dict[str, str]], list[dict[str, str]], list[dict[str, str]]]:
    path = RAW / "include_zero_coeff_one_fast_resource_trials1_run.log"
    if not path.exists():
        return [], [], []
    text = path.read_text(encoding="utf-8", errors="replace")
    key_rows = []
    noise_rows = []
    gate_rows = []
    for match in KEY_BYTES_RE.finditer(text):
        row = match.groupdict()
        row["variant"] = "include_zero_coeff_one_fast"
        row["source_log"] = rel(path)
        key_rows.append(row)
    for match in NOISE_SUMMARY_RE.finditer(text):
        row = match.groupdict()
        row["variant"] = "include_zero_coeff_one_fast"
        row["source_log"] = rel(path)
        noise_rows.append(row)
    gate = RESOURCE_GATE_RE.search(text)
    if gate:
        gate_rows.append(
            {
                "variant": "include_zero_coeff_one_fast",
                "gate": gate.group("gate"),
                "source_log": rel(path),
            }
        )
    return key_rows, noise_rows, gate_rows


def compare_rows(summary: list[dict[str, str]]) -> list[dict[str, str]]:
    by_variant = {row["variant"]: row for row in summary}
    base = by_variant.get("default")
    backend = by_variant.get("backend_from_dft_add")
    fast = by_variant.get("include_zero_coeff_one_fast")
    if not base or not backend or not fast:
        return [{"mode": "include_zero", "status": "MISSING"}]
    base_us = float(base["t_bootstrap_over_r_pvw_us"])
    backend_us = float(backend["t_bootstrap_over_r_pvw_us"])
    fast_us = float(fast["t_bootstrap_over_r_pvw_us"])
    fast_vs_default = base_us / fast_us if fast_us else 0.0
    fast_vs_backend = backend_us / fast_us if fast_us else 0.0
    return [
        {
            "mode": "include_zero",
            "r": "4",
            "reps": fast["reps"],
            "default_t_bootstrap_over_r_us": f"{base_us:.3f}",
            "backend_t_bootstrap_over_r_us": f"{backend_us:.3f}",
            "fast_t_bootstrap_over_r_us": f"{fast_us:.3f}",
            "fast_speedup_vs_default": f"{fast_vs_default:.6f}",
            "fast_speedup_vs_backend": f"{fast_vs_backend:.6f}",
            "fast_stddev_us": fast["pvw_stddev_us"],
            "default_correctness": base["correctness_gate"],
            "backend_correctness": backend["correctness_gate"],
            "fast_correctness": fast["correctness_gate"],
            "status": "positive" if fast_vs_backend >= 1.01 and fast_vs_default >= 1.01 else "neutral_or_negative",
        }
    ]


def decision_from(summary: list[dict[str, str]], comparison: list[dict[str, str]],
                  noise: list[dict[str, str]], resource_gates: list[dict[str, str]]) -> str:
    expected = {"default", "backend_from_dft_add", "include_zero_coeff_one_fast"}
    covered = {row["variant"] for row in summary}
    if not expected.issubset(covered):
        return "FAIL_STAGE277_INCLUDE_ZERO_FAST_MISSING_COVERAGE"
    if any(row["correctness_gate"] != "Pass" for row in summary):
        return "FAIL_STAGE277_INCLUDE_ZERO_FAST_CORRECTNESS"
    if not comparison or comparison[0].get("status") != "positive":
        return "NEUTRAL_STAGE277_INCLUDE_ZERO_FAST_REPEATED_NO_PROMOTION"
    if not noise or any(row.get("gate") != "Pass" for row in noise):
        return "FAIL_STAGE277_INCLUDE_ZERO_FAST_NOISE"
    if any(row.get("pvw_failures") != "0" or row.get("pair_failures") != "0" for row in noise):
        return "FAIL_STAGE277_INCLUDE_ZERO_FAST_FAILURES"
    if not resource_gates or resource_gates[0].get("gate") != "Pass":
        return "FAIL_STAGE277_INCLUDE_ZERO_FAST_RESOURCE_GATE"
    return "PASS_STAGE277_INCLUDE_ZERO_FAST_REPEATED_RESOURCE_PROMOTE_NATIVE_STATS_REQUIRED"


def proof_rows(summary: list[dict[str, str]], comparison: list[dict[str, str]],
               noise: list[dict[str, str]], key_rows: list[dict[str, str]],
               resource_gates: list[dict[str, str]], decision: str) -> list[dict[str, str]]:
    covered = ",".join(f"{row['variant']}:{row['mode']}:reps{row['reps']}" for row in summary)
    fast_vs_backend = comparison[0].get("fast_speedup_vs_backend", "0") if comparison else "0"
    noise_gate = noise[0].get("gate", "missing") if noise else "missing"
    key_ratio = key_rows[0].get("pvw_vs_scalar_repeated_ratio", "missing") if key_rows else "missing"
    resource_gate = resource_gates[0].get("gate", "missing") if resource_gates else "missing"
    return [
        {"gate": "G1_repeated_coverage", "status": "PASS" if len(summary) == 3 else "FAIL", "metric": "variant coverage", "value": covered, "evidence": "bench_summary.csv", "interpretation": "Covers default, backend, and fast include-zero variants with repeated reps."},
        {"gate": "G2_repeated_correctness", "status": "PASS" if all(row["correctness_gate"] == "Pass" for row in summary) else "FAIL", "metric": "PVW/scalar target correctness", "value": f"{sum(row['correctness_gate'] == 'Pass' for row in summary)}/{len(summary)}", "evidence": "bench_summary.csv", "interpretation": "Repeated timing is interpreted only after correctness passes."},
        {"gate": "G3_repeated_speed", "status": "PASS" if comparison and comparison[0].get("status") == "positive" else "NEUTRAL", "metric": "fast speedup vs backend", "value": f"{fast_vs_backend}x", "evidence": "variant_compare.csv", "interpretation": "Fast path must beat default and same-backend baseline on T_bootstrap/r."},
        {"gate": "G4_noise", "status": "PASS" if noise_gate == "Pass" else "FAIL", "metric": "noise gate", "value": noise_gate, "evidence": "noise_summary.csv", "interpretation": "Noise/resource run is scoped to r=4 include-zero fast path."},
        {"gate": "G5_resource", "status": "PASS" if resource_gate == "Pass" and key_ratio != "missing" else "FAIL", "metric": "key size ratio vs scalar repeated", "value": key_ratio, "evidence": "resource_summary.csv", "interpretation": "Fast path changes compute only; key format and estimates remain reported."},
        {"gate": "G6_claim_boundary", "status": "PASS_WSL_NOT_FINAL", "metric": "platform/statistics", "value": "WSL2 spqlios_avx512 reps2; FFNT resource trials1", "evidence": "claim_boundary.csv", "interpretation": "Timing and resource/noise evidence are separated; native Linux and larger repeated/seed matrix are required before paper-grade claim."},
        {"gate": "G7_decision", "status": decision, "metric": "stage decision", "value": decision, "evidence": "proof_gate.csv", "interpretation": "Promote to native/larger-stat gate only if all local gates pass."},
    ]


def claim_rows(decision: str) -> list[dict[str, str]]:
    return [
        {"claim": "include_zero_fast_repeated_local", "status": "promote" if decision.startswith("PASS_") else "not_promoted", "allowed_wording": "Stage277 local repeated/resource evidence supports further promotion of the guarded include-zero fast path.", "forbidden_wording": "Stage277 is final paper-grade evidence.", "evidence": "variant_compare.csv; noise_summary.csv"},
        {"claim": "resource_cost", "status": "reported", "allowed_wording": "Key-size/resource estimates are reported and unchanged by the compute-only fast path.", "forbidden_wording": "The fast path reduces key size.", "evidence": "resource_summary.csv"},
        {"claim": "backend_separation", "status": "explicit", "allowed_wording": "Stage277 timing uses spqlios_avx512, while small-parameter resource/noise uses FFNT proxy evidence.", "forbidden_wording": "FFNT resource/noise output is a spqlios_avx512 performance result.", "evidence": "raw/*_build.log; proof_gate.csv"},
        {"claim": "scope", "status": "guarded_include_zero_only", "allowed_wording": "The claim is limited to current PVW include-zero coefficient-one semantics.", "forbidden_wording": "This covers ternary or scalar include-zero zero-gap semantics.", "evidence": "claim_boundary.csv"},
    ]


def next_rows(decision: str) -> list[dict[str, str]]:
    if decision.startswith("PASS_"):
        return [
            {"priority": "P0", "route": "stage278_native_larger_stats_include_zero_fast", "entry_condition": "Stage277 local repeated/resource pass.", "gate": "Native Linux or authenticated performance host, reps>=5, multi-seed correctness/noise/resource.", "status": "selected", "failure_action": "Demote to local-only optimization if native/repeated gates fail."},
            {"priority": "P1", "route": "stage279_selector_mat_ep_residual_profile", "entry_condition": "After Stage278 or if residual profile remains dominated by MAT EP.", "gate": "Profile residual hot path under fast flag and select next kernel/schedule candidate.", "status": "conditional", "failure_action": "No broad SAB claim without residual A/B."},
        ]
    return [
        {"priority": "P0", "route": "stage278_selector_mat_ep_kernel_tiling", "entry_condition": "Stage277 not promoted.", "gate": "Selector MAT-EP microbench/profile and explicit candidate design.", "status": "selected", "failure_action": "No claim without full SAB A/B."},
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
    append_once(CURRENT_GOAL, "### Stage277 include-zero fast repeated/resource", f"""
### Stage277 include-zero fast repeated/resource

`{decision}` records local repeated timing plus r=4 include-zero fast-path
noise/resource evidence. It remains WSL/local evidence and requires native or
larger-stat promotion before paper-grade speed claims.
""")
    append_once(HYPOTHESES, "H10_stage277_include_zero_fast_repeated_resource:", f"""
H10_stage277_include_zero_fast_repeated_resource:
  status: {decision}
  evidence:
    - repro/stage277_include_zero_fast_repeated_resource/bench_summary.csv
    - repro/stage277_include_zero_fast_repeated_resource/variant_compare.csv
    - repro/stage277_include_zero_fast_repeated_resource/noise_summary.csv
    - docs/stage277_include_zero_fast_repeated_resource.md
  conclusion: >
    Stage277 records {decision}. It promotes the guarded include-zero fast path
    only to a native/larger-stat follow-up gate, not to a final paper claim.
""")
    append_once(RUN_LOG, "stage277-include-zero-fast-repeated-resource-001", f"""stage277-include-zero-fast-repeated-resource-001,2026-07-04,{head},Stage 277,spqlios_avx512,bash scripts/run_stage277_include_zero_fast_repeated_resource.sh; python scripts/build_stage277_include_zero_fast_repeated_resource.py,"r=4 include-zero fast repeated timing reps2 plus resource/noise trial1",n/a,{decision},"Local repeated/resource gate; native/larger-stat promotion required if pass.",docs/stage277_include_zero_fast_repeated_resource.md; repro/stage277_include_zero_fast_repeated_resource/proof_gate.csv
""")
    append_once(MANIFEST, "- stage277_include_zero_fast_repeated_resource:", """
- stage277_include_zero_fast_repeated_resource:
  - `docs/stage277_include_zero_fast_repeated_resource.md`
  - `scripts/run_stage277_include_zero_fast_repeated_resource.sh`
  - `scripts/build_stage277_include_zero_fast_repeated_resource.py`
  - `repro/stage277_include_zero_fast_repeated_resource/`
""")
    append_once(CHECKLIST, "stage277-include-zero-fast-repeated-resource-checklist", f"""
<!-- stage277-include-zero-fast-repeated-resource-checklist -->
- [x] Stage277 include-zero fast repeated/resource records `{decision}` and keeps final claims gated.
""")


def main() -> int:
    REPRO.mkdir(parents=True, exist_ok=True)
    summary = parse_bench_logs()
    comparison = compare_rows(summary)
    key_rows, noise_rows, resource_gates = parse_resource_log()
    decision = decision_from(summary, comparison, noise_rows, resource_gates)
    proof = proof_rows(summary, comparison, noise_rows, key_rows, resource_gates, decision)
    claims = claim_rows(decision)
    queue = next_rows(decision)

    summary_fields = [
        "variant", "mode", "r", "reps", "h", "r_prec", "correctness_gate",
        "pvw_avg_us", "pvw_stddev_us", "scalar_repeated_avg_us",
        "speedup_vs_scalar_repeated", "t_bootstrap_over_r_pvw_us",
        "t_bootstrap_over_r_scalar_us", "platform", "backend", "param",
        "primary_metric", "avx_variant", "log",
    ]
    write_csv(REPRO / "bench_summary.csv", summary, summary_fields)
    write_csv(REPRO / "variant_compare.csv", comparison, [
        "mode", "r", "reps", "default_t_bootstrap_over_r_us",
        "backend_t_bootstrap_over_r_us", "fast_t_bootstrap_over_r_us",
        "fast_speedup_vs_default", "fast_speedup_vs_backend", "fast_stddev_us",
        "default_correctness", "backend_correctness", "fast_correctness", "status",
    ])
    write_csv(REPRO / "resource_summary.csv", key_rows, [
        "variant", "mode", "r", "pvw_estimated_key_bytes",
        "scalar_one_estimated_key_bytes", "scalar_repeated_estimated_key_bytes",
        "pvw_vs_scalar_repeated_ratio", "source_log",
    ])
    write_csv(REPRO / "noise_summary.csv", noise_rows, [
        "variant", "mode", "r", "trials", "points", "pvw_failures",
        "scalar_failures", "pair_failures", "pvw_log2_sigma_torus",
        "scalar_log2_sigma_torus", "pair_log2_sigma_torus",
        "pair_log2_max_abs_torus", "gate", "source_log",
    ])
    write_csv(REPRO / "resource_gate.csv", resource_gates, ["variant", "gate", "source_log"])
    write_csv(REPRO / "proof_gate.csv", proof, ["gate", "status", "metric", "value", "evidence", "interpretation"])
    write_csv(REPRO / "claim_boundary.csv", claims, ["claim", "status", "allowed_wording", "forbidden_wording", "evidence"])
    write_csv(REPRO / "next_stage_queue.csv", queue, ["priority", "route", "entry_condition", "gate", "status", "failure_action"])

    report = f"""# Stage277 Include-Zero Fast Repeated Resource

Decision: `{decision}`.

Stage277 reruns the guarded include-zero coeff-one fast path with repeated
timing (`reps=2`) and an r=4 include-zero noise/resource trial. Timing uses
`spqlios_avx512`; the small-parameter resource/noise run uses FFNT proxy
evidence to avoid tiny-ring DFT issues in the AVX512 backend. This remains
local WSL evidence, not paper-grade final evidence.

## Bench Summary

{table(summary, ["variant", "mode", "r", "reps", "correctness_gate", "t_bootstrap_over_r_pvw_us", "pvw_stddev_us", "speedup_vs_scalar_repeated"])}

## Variant Comparison

{table(comparison, ["mode", "r", "reps", "default_t_bootstrap_over_r_us", "backend_t_bootstrap_over_r_us", "fast_t_bootstrap_over_r_us", "fast_speedup_vs_default", "fast_speedup_vs_backend", "status"])}

## Noise Summary

{table(noise_rows, ["variant", "mode", "r", "trials", "points", "pvw_failures", "scalar_failures", "pair_failures", "gate"])}

## Resource Summary

{table(key_rows, ["variant", "mode", "r", "pvw_estimated_key_bytes", "scalar_repeated_estimated_key_bytes", "pvw_vs_scalar_repeated_ratio"])}

## Proof Gate

{table(proof, ["gate", "status", "metric", "value", "interpretation"])}

## Claim Boundary

{table(claims, ["claim", "status", "allowed_wording", "forbidden_wording"])}

## Next Queue

{table(queue, ["priority", "route", "entry_condition", "gate", "status", "failure_action"])}

Generated from input head `{git_head()}`.
"""
    write_text(DOC, report)
    write_text(REPRO / "stage277_report.md", report)
    write_text(REPRO / "reproduction_commands.md", """# Stage277 Reproduction Commands

```bash
bash scripts/run_stage277_include_zero_fast_repeated_resource.sh
python3 scripts/build_stage277_include_zero_fast_repeated_resource.py
```

Stage277 is local WSL repeated/resource evidence. Native or larger repeated
statistics are required before paper-grade claims.
""")
    update_tracking(decision)
    paths = [
        DOC,
        REPRO / "stage277_report.md",
        REPRO / "reproduction_commands.md",
        REPRO / "bench_summary.csv",
        REPRO / "variant_compare.csv",
        REPRO / "resource_summary.csv",
        REPRO / "noise_summary.csv",
        REPRO / "resource_gate.csv",
        REPRO / "proof_gate.csv",
        REPRO / "claim_boundary.csv",
        REPRO / "next_stage_queue.csv",
        Path(__file__),
        ROOT / "scripts" / "run_stage277_include_zero_fast_repeated_resource.sh",
        ROOT / "main.c",
        ROOT / "src" / "mosfhet" / "Makefile.def",
    ]
    write_csv(REPRO / "artifact_index.csv", artifacts(paths), ["path", "bytes", "sha256"])
    print(decision)
    return 0 if decision.startswith("PASS_") or decision.startswith("NEUTRAL_") else 1


if __name__ == "__main__":
    raise SystemExit(main())
