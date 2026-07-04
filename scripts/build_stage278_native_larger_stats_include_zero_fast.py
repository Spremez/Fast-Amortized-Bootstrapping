#!/usr/bin/env python3
"""Build Stage278 native/larger-stats include-zero fast artifacts."""

from __future__ import annotations

import csv
import hashlib
import re
import subprocess
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
REPRO = ROOT / "repro" / "stage278_native_larger_stats_include_zero_fast"
RAW = REPRO / "raw"
DOC = ROOT / "docs" / "stage278_native_larger_stats_include_zero_fast.md"
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


def read_csv(path: Path) -> list[dict[str, str]]:
    if not path.exists():
        return []
    with path.open(newline="", encoding="utf-8-sig") as handle:
        return list(csv.DictReader(handle))


def split_variant(name: str, prefix: str, reps: str) -> str | None:
    suffix = f"_include_zero_r4_reps{reps}_run.log"
    if not name.startswith(prefix) or not name.endswith(suffix):
        return None
    stem = name.removeprefix(prefix).removesuffix(suffix)
    return stem if stem in VARIANTS else None


def parse_bench_logs(prefix: str, platform: str, reps: str) -> list[dict[str, str]]:
    rows: list[dict[str, str]] = []
    for path in sorted(RAW.glob(f"{prefix}*_include_zero_r4_reps{reps}_run.log")):
        variant = split_variant(path.name, prefix, reps)
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
                "platform": platform,
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


def parse_resource_log(prefix: str, platform: str, trials: str) -> tuple[list[dict[str, str]], list[dict[str, str]], list[dict[str, str]]]:
    path = RAW / f"{prefix}include_zero_coeff_one_fast_resource_trials{trials}_run.log"
    if not path.exists():
        return [], [], []
    text = path.read_text(encoding="utf-8", errors="replace")
    key_rows = []
    noise_rows = []
    gate_rows = []
    for match in KEY_BYTES_RE.finditer(text):
        row = match.groupdict()
        row["variant"] = "include_zero_coeff_one_fast"
        row["platform"] = platform
        row["backend"] = "ffnt"
        row["source_log"] = rel(path)
        key_rows.append(row)
    for match in NOISE_SUMMARY_RE.finditer(text):
        row = match.groupdict()
        row["variant"] = "include_zero_coeff_one_fast"
        row["platform"] = platform
        row["backend"] = "ffnt"
        row["source_log"] = rel(path)
        noise_rows.append(row)
    gate = RESOURCE_GATE_RE.search(text)
    if gate:
        gate_rows.append(
            {
                "variant": "include_zero_coeff_one_fast",
                "platform": platform,
                "backend": "ffnt",
                "gate": gate.group("gate"),
                "source_log": rel(path),
            }
        )
    return key_rows, noise_rows, gate_rows


def compare_rows(summary: list[dict[str, str]], label: str) -> list[dict[str, str]]:
    by_variant = {row["variant"]: row for row in summary}
    base = by_variant.get("default")
    backend = by_variant.get("backend_from_dft_add")
    fast = by_variant.get("include_zero_coeff_one_fast")
    if not base or not backend or not fast:
        return [{"scope": label, "mode": "include_zero", "status": "MISSING"}]
    base_us = float(base["t_bootstrap_over_r_pvw_us"])
    backend_us = float(backend["t_bootstrap_over_r_pvw_us"])
    fast_us = float(fast["t_bootstrap_over_r_pvw_us"])
    fast_vs_default = base_us / fast_us if fast_us else 0.0
    fast_vs_backend = backend_us / fast_us if fast_us else 0.0
    return [
        {
            "scope": label,
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


def native_status_rows() -> list[dict[str, str]]:
    status = RAW / "native_handoff_status.csv"
    rows = read_csv(status)
    if rows:
        return rows
    return [{"status": "not_run", "reason": "native_handoff_not_executed", "exit_code": ""}]


def decision_from(local_summary: list[dict[str, str]], local_compare: list[dict[str, str]],
                  local_noise: list[dict[str, str]], local_resource_gates: list[dict[str, str]],
                  native_summary: list[dict[str, str]], native_compare: list[dict[str, str]],
                  native_status: list[dict[str, str]]) -> str:
    expected = {"default", "backend_from_dft_add", "include_zero_coeff_one_fast"}
    covered = {row["variant"] for row in local_summary}
    if not expected.issubset(covered):
        return "FAIL_STAGE278_LOCAL_LARGER_STATS_MISSING_COVERAGE"
    if any(row["correctness_gate"] != "Pass" for row in local_summary):
        return "FAIL_STAGE278_LOCAL_LARGER_STATS_CORRECTNESS"
    if not local_compare or local_compare[0].get("status") != "positive":
        return "NEUTRAL_STAGE278_LOCAL_LARGER_STATS_NO_PROMOTION"
    if not local_noise or any(row.get("gate") != "Pass" for row in local_noise):
        return "FAIL_STAGE278_LOCAL_LARGER_STATS_NOISE"
    if not local_resource_gates or local_resource_gates[0].get("gate") != "Pass":
        return "FAIL_STAGE278_LOCAL_LARGER_STATS_RESOURCE"
    if native_summary and native_compare and native_compare[0].get("status") == "positive":
        return "PASS_STAGE278_NATIVE_LARGER_STATS_INCLUDE_ZERO_FAST_PROMOTED"
    reason = native_status[0].get("reason", "native_missing") if native_status else "native_missing"
    if reason:
        return "PASS_STAGE278_LOCAL_LARGER_STATS_NATIVE_REQUIRED"
    return "PASS_STAGE278_LOCAL_LARGER_STATS_NATIVE_REQUIRED"


def proof_rows(local_summary: list[dict[str, str]], local_compare: list[dict[str, str]],
               local_noise: list[dict[str, str]], local_resource: list[dict[str, str]],
               local_gates: list[dict[str, str]], native_status: list[dict[str, str]],
               native_summary: list[dict[str, str]], decision: str) -> list[dict[str, str]]:
    covered = ",".join(f"{row['variant']}:{row['mode']}:reps{row['reps']}" for row in local_summary)
    speed = local_compare[0].get("fast_speedup_vs_backend", "0") if local_compare else "0"
    noise_gate = local_noise[0].get("gate", "missing") if local_noise else "missing"
    key_ratio = local_resource[0].get("pvw_vs_scalar_repeated_ratio", "missing") if local_resource else "missing"
    resource_gate = local_gates[0].get("gate", "missing") if local_gates else "missing"
    native = native_status[0].get("status", "not_run") if native_status else "not_run"
    return [
        {"gate": "G1_local_reps5_coverage", "status": "PASS" if len(local_summary) == 3 else "FAIL", "metric": "variant coverage", "value": covered, "evidence": "bench_summary.csv", "interpretation": "Local larger-stat timing covers default, backend, and fast include-zero variants with reps>=5."},
        {"gate": "G2_local_correctness", "status": "PASS" if all(row["correctness_gate"] == "Pass" for row in local_summary) else "FAIL", "metric": "PVW/scalar correctness", "value": f"{sum(row['correctness_gate'] == 'Pass' for row in local_summary)}/{len(local_summary)}", "evidence": "bench_summary.csv", "interpretation": "Timing is interpreted only after correctness passes."},
        {"gate": "G3_local_speed", "status": "PASS" if local_compare and local_compare[0].get("status") == "positive" else "NEUTRAL", "metric": "fast speedup vs backend", "value": f"{speed}x", "evidence": "variant_compare.csv", "interpretation": "Fast path must beat default and same-backend baseline on T_bootstrap/r."},
        {"gate": "G4_local_noise", "status": "PASS" if noise_gate == "Pass" else "FAIL", "metric": "noise gate", "value": noise_gate, "evidence": "noise_summary.csv", "interpretation": "Resource/noise run is FFNT proxy evidence, separated from timing."},
        {"gate": "G5_local_resource", "status": "PASS" if resource_gate == "Pass" and key_ratio != "missing" else "FAIL", "metric": "key size ratio vs scalar repeated", "value": key_ratio, "evidence": "resource_summary.csv", "interpretation": "Compute-only fast path does not reduce key size; key size is still reported."},
        {"gate": "G6_native_status", "status": "PASS_NATIVE" if native_summary else "MISSING_NATIVE", "metric": "native evidence", "value": native, "evidence": "native_status.csv", "interpretation": "Native evidence is required before paper-grade performance claim."},
        {"gate": "G7_claim_boundary", "status": "PASS_NOT_FINAL" if decision.endswith("NATIVE_REQUIRED") else "PASS_NATIVE_READY", "metric": "claim scope", "value": decision, "evidence": "claim_boundary.csv", "interpretation": "Local larger-stat pass can promote the candidate, but final paper-grade speed still needs native/larger-seed evidence unless native rows are present."},
        {"gate": "G8_decision", "status": decision, "metric": "stage decision", "value": decision, "evidence": "proof_gate.csv", "interpretation": "Proceed according to native availability and residual-profile queue."},
    ]


def claim_rows(decision: str) -> list[dict[str, str]]:
    return [
        {"claim": "include_zero_fast_local_larger_stats", "status": "supported_local" if "LOCAL_LARGER_STATS" in decision else "native_supported", "allowed_wording": "Stage278 local reps>=5 evidence supports the guarded include-zero fast path on WSL/spqlios_avx512.", "forbidden_wording": "This is final native paper-grade evidence.", "evidence": "variant_compare.csv; proof_gate.csv"},
        {"claim": "backend_separation", "status": "explicit", "allowed_wording": "Timing uses spqlios_avx512; resource/noise uses FFNT proxy evidence.", "forbidden_wording": "FFNT resource/noise is an AVX512 performance result.", "evidence": "resource_summary.csv; raw/*_build.log"},
        {"claim": "native_status", "status": "required" if decision.endswith("NATIVE_REQUIRED") else "present", "allowed_wording": "Native performance claim remains gated unless native rows are present.", "forbidden_wording": "Local WSL reps>=5 alone proves paper-grade performance.", "evidence": "native_status.csv"},
        {"claim": "scope", "status": "guarded_include_zero_only", "allowed_wording": "The algorithmic claim is limited to current PVW include-zero coefficient-one semantics.", "forbidden_wording": "This covers ternary or general scalar include-zero zero-gap semantics.", "evidence": "claim_boundary.csv"},
    ]


def next_rows(decision: str) -> list[dict[str, str]]:
    if decision.endswith("NATIVE_REQUIRED"):
        return [
            {"priority": "P0", "route": "stage279_native_execution_or_access_probe", "entry_condition": "Stage278 local larger-stat pass but native rows missing.", "gate": "Run Stage278 handoff on native Linux/authenticated host or record explicit access result without credentials.", "status": "selected", "failure_action": "Keep as local-only evidence if native remains unavailable."},
            {"priority": "P1", "route": "stage280_residual_profile_under_fast_flag", "entry_condition": "Local larger-stat fast path remains positive.", "gate": "Profile residual hot path under fast flag before selector MAT-EP work.", "status": "conditional", "failure_action": "Do not optimize without residual attribution."},
        ]
    if decision.startswith("PASS_STAGE278_NATIVE"):
        return [
            {"priority": "P0", "route": "stage279_residual_profile_under_fast_flag", "entry_condition": "Native larger-stat pass.", "gate": "Profile residual hot path and decide next kernel/schedule candidate.", "status": "selected", "failure_action": "If residual is not MAT EP, select different candidate."},
        ]
    return [
        {"priority": "P0", "route": "stage279_selector_mat_ep_or_close_fast_path", "entry_condition": "Stage278 failed or neutral.", "gate": "Close/demote fast path and choose selector MAT-EP candidate.", "status": "selected", "failure_action": "No paper claim."},
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
    append_once(CURRENT_GOAL, "### Stage278 native/larger stats include-zero fast", f"""
### Stage278 native/larger stats include-zero fast

`{decision}` records reps>=5 local larger-stat evidence for the guarded
include-zero fast path and records native evidence status separately. It does
not convert WSL results into a paper-grade native claim.
""")
    append_once(HYPOTHESES, "H10_stage278_native_larger_stats_include_zero_fast:", f"""
H10_stage278_native_larger_stats_include_zero_fast:
  status: {decision}
  evidence:
    - repro/stage278_native_larger_stats_include_zero_fast/bench_summary.csv
    - repro/stage278_native_larger_stats_include_zero_fast/variant_compare.csv
    - repro/stage278_native_larger_stats_include_zero_fast/proof_gate.csv
    - docs/stage278_native_larger_stats_include_zero_fast.md
  conclusion: >
    Stage278 records {decision}. It strengthens local repeated evidence for
    the guarded include-zero fast path while keeping native paper-grade
    performance as a separate gate.
""")
    append_once(RUN_LOG, "stage278-native-larger-stats-include-zero-fast-001", f"""stage278-native-larger-stats-include-zero-fast-001,2026-07-04,{head},Stage 278,spqlios_avx512-local,bash scripts/run_stage278_include_zero_fast_local_larger_stats.sh; python scripts/build_stage278_native_larger_stats_include_zero_fast.py,"r=4 include-zero fast reps5 plus FFNT resource/noise trials3; native status separated",n/a,{decision},"Local larger-stat gate; native evidence remains separate unless native rows are present.",docs/stage278_native_larger_stats_include_zero_fast.md; repro/stage278_native_larger_stats_include_zero_fast/proof_gate.csv
""")
    append_once(MANIFEST, "- stage278_native_larger_stats_include_zero_fast:", """
- stage278_native_larger_stats_include_zero_fast:
  - `docs/stage278_native_larger_stats_include_zero_fast.md`
  - `scripts/run_stage278_include_zero_fast_local_larger_stats.sh`
  - `scripts/run_stage278_native_include_zero_fast_handoff.sh`
  - `scripts/build_stage278_native_larger_stats_include_zero_fast.py`
  - `repro/stage278_native_larger_stats_include_zero_fast/`
""")
    append_once(CHECKLIST, "stage278-native-larger-stats-include-zero-fast-checklist", f"""
<!-- stage278-native-larger-stats-include-zero-fast-checklist -->
- [x] Stage278 records `{decision}` with reps>=5 local timing, resource/noise proxy, and native status separated.
""")


def main() -> int:
    REPRO.mkdir(parents=True, exist_ok=True)
    local_summary = parse_bench_logs("local_", "WSL2/Linux", "5")
    native_summary = parse_bench_logs("native_", "native_linux", "5")
    local_compare = compare_rows(local_summary, "local")
    native_compare = compare_rows(native_summary, "native") if native_summary else []
    local_resource, local_noise, local_gates = parse_resource_log("local_", "WSL2/Linux-FFNT-resource", "3")
    native_status = native_status_rows()
    decision = decision_from(
        local_summary, local_compare, local_noise, local_gates,
        native_summary, native_compare, native_status,
    )
    proof = proof_rows(
        local_summary, local_compare, local_noise, local_resource,
        local_gates, native_status, native_summary, decision,
    )
    claims = claim_rows(decision)
    queue = next_rows(decision)

    summary = local_summary + native_summary
    comparison = local_compare + native_compare
    summary_fields = [
        "variant", "mode", "r", "reps", "h", "r_prec", "correctness_gate",
        "pvw_avg_us", "pvw_stddev_us", "scalar_repeated_avg_us",
        "speedup_vs_scalar_repeated", "t_bootstrap_over_r_pvw_us",
        "t_bootstrap_over_r_scalar_us", "platform", "backend", "param",
        "primary_metric", "avx_variant", "log",
    ]
    write_csv(REPRO / "bench_summary.csv", summary, summary_fields)
    write_csv(REPRO / "variant_compare.csv", comparison, [
        "scope", "mode", "r", "reps", "default_t_bootstrap_over_r_us",
        "backend_t_bootstrap_over_r_us", "fast_t_bootstrap_over_r_us",
        "fast_speedup_vs_default", "fast_speedup_vs_backend", "fast_stddev_us",
        "default_correctness", "backend_correctness", "fast_correctness", "status",
    ])
    write_csv(REPRO / "resource_summary.csv", local_resource, [
        "variant", "platform", "backend", "mode", "r", "pvw_estimated_key_bytes",
        "scalar_one_estimated_key_bytes", "scalar_repeated_estimated_key_bytes",
        "pvw_vs_scalar_repeated_ratio", "source_log",
    ])
    write_csv(REPRO / "noise_summary.csv", local_noise, [
        "variant", "platform", "backend", "mode", "r", "trials", "points",
        "pvw_failures", "scalar_failures", "pair_failures",
        "pvw_log2_sigma_torus", "scalar_log2_sigma_torus",
        "pair_log2_sigma_torus", "pair_log2_max_abs_torus", "gate", "source_log",
    ])
    write_csv(REPRO / "resource_gate.csv", local_gates, ["variant", "platform", "backend", "gate", "source_log"])
    write_csv(REPRO / "native_status.csv", native_status, ["status", "reason", "exit_code"])
    write_csv(REPRO / "proof_gate.csv", proof, ["gate", "status", "metric", "value", "evidence", "interpretation"])
    write_csv(REPRO / "claim_boundary.csv", claims, ["claim", "status", "allowed_wording", "forbidden_wording", "evidence"])
    write_csv(REPRO / "next_stage_queue.csv", queue, ["priority", "route", "entry_condition", "gate", "status", "failure_action"])

    report = f"""# Stage278 Native Larger Stats Include-Zero Fast

Decision: `{decision}`.

Stage278 strengthens the guarded include-zero coeff-one fast-path evidence with
local `reps=5` timing and FFNT resource/noise trials. Native Linux evidence is
kept as a separate gate and is not inferred from WSL.

## Bench Summary

{table(summary, ["platform", "variant", "mode", "r", "reps", "correctness_gate", "t_bootstrap_over_r_pvw_us", "pvw_stddev_us", "speedup_vs_scalar_repeated"])}

## Variant Comparison

{table(comparison, ["scope", "mode", "r", "reps", "default_t_bootstrap_over_r_us", "backend_t_bootstrap_over_r_us", "fast_t_bootstrap_over_r_us", "fast_speedup_vs_default", "fast_speedup_vs_backend", "status"])}

## Noise Summary

{table(local_noise, ["platform", "backend", "mode", "r", "trials", "points", "pvw_failures", "scalar_failures", "pair_failures", "gate"])}

## Resource Summary

{table(local_resource, ["platform", "backend", "mode", "r", "pvw_estimated_key_bytes", "scalar_repeated_estimated_key_bytes", "pvw_vs_scalar_repeated_ratio"])}

## Native Status

{table(native_status, ["status", "reason", "exit_code"])}

## Proof Gate

{table(proof, ["gate", "status", "metric", "value", "interpretation"])}

## Claim Boundary

{table(claims, ["claim", "status", "allowed_wording", "forbidden_wording"])}

## Next Queue

{table(queue, ["priority", "route", "entry_condition", "gate", "status", "failure_action"])}

Generated from input head `{git_head()}`.
"""
    write_text(DOC, report)
    write_text(REPRO / "stage278_report.md", report)
    write_text(REPRO / "reproduction_commands.md", """# Stage278 Reproduction Commands

Local larger-stat evidence:

```bash
bash scripts/run_stage278_include_zero_fast_local_larger_stats.sh
python3 scripts/build_stage278_native_larger_stats_include_zero_fast.py
```

Native handoff without storing credentials:

```bash
NATIVE_HOST=<host> NATIVE_USER=<user> NATIVE_WORKDIR=<repo-path> \\
  bash scripts/run_stage278_native_include_zero_fast_handoff.sh
python3 scripts/build_stage278_native_larger_stats_include_zero_fast.py
```

The native handoff uses `ssh -o BatchMode=yes`; configure key-based auth or run
the local runner directly on the native host. Do not place credentials in logs
or scripts.
""")
    update_tracking(decision)
    paths = [
        DOC,
        REPRO / "stage278_report.md",
        REPRO / "reproduction_commands.md",
        REPRO / "bench_summary.csv",
        REPRO / "variant_compare.csv",
        REPRO / "resource_summary.csv",
        REPRO / "noise_summary.csv",
        REPRO / "resource_gate.csv",
        REPRO / "native_status.csv",
        REPRO / "proof_gate.csv",
        REPRO / "claim_boundary.csv",
        REPRO / "next_stage_queue.csv",
        Path(__file__),
        ROOT / "scripts" / "run_stage278_include_zero_fast_local_larger_stats.sh",
        ROOT / "scripts" / "run_stage278_native_include_zero_fast_handoff.sh",
    ]
    write_csv(REPRO / "artifact_index.csv", artifacts(paths), ["path", "bytes", "sha256"])
    print(decision)
    return 0 if decision.startswith("PASS_") or decision.startswith("NEUTRAL_") else 1


if __name__ == "__main__":
    raise SystemExit(main())
