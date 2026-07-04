#!/usr/bin/env python3
"""Build Stage269 repeated performance and noise/resource artifacts."""

from __future__ import annotations

import csv
import hashlib
import re
import subprocess
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
REPRO = ROOT / "repro" / "stage269_backend_from_dft_add_repeated_noise_resource"
RAW = REPRO / "raw"
DOC = ROOT / "docs" / "stage269_backend_from_dft_add_repeated_noise_resource.md"
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
SAMPLE_RE = re.compile(
    r"SAB_PVW_NONBINARY_BENCH sample target_full "
    r"mode=(?P<mode>\S+) r=(?P<r>\d+) rep=(?P<rep>\d+) "
    r"pvw_us=(?P<pvw_us>\d+) pvw_lane_us=(?P<pvw_lane_us>[0-9.]+) "
    r"scalar_repeated_us=(?P<scalar_repeated_us>\d+) "
    r"scalar_lane_us=(?P<scalar_lane_us>[0-9.]+) "
    r"speedup=(?P<speedup>[0-9.]+)x"
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
NOISE_RE = re.compile(
    r"SAB_PVW_NONBINARY_FULL_NOISE summary mode=(?P<mode>\S+) r=(?P<r>\d+) "
    r"trials=(?P<trials>\d+) points=(?P<points>\d+) "
    r"pvw_failures=(?P<pvw_failures>\d+) scalar_failures=(?P<scalar_failures>\d+) "
    r"pair_failures=(?P<pair_failures>\d+) "
    r"pvw_log2_sigma_torus=(?P<pvw_log2_sigma_torus>-?[0-9.]+) "
    r"scalar_log2_sigma_torus=(?P<scalar_log2_sigma_torus>-?[0-9.]+) "
    r"pair_log2_sigma_torus=(?P<pair_log2_sigma_torus>-?[0-9.]+) "
    r"pair_log2_max_abs_torus=(?P<pair_log2_max_abs_torus>-?[0-9.]+) "
    r"gate=(?P<gate>Pass|Fail)"
)
KEY_BYTES_RE = re.compile(
    r"SAB_PVW_NONBINARY_RESOURCE key_bytes full_smoke mode=(?P<mode>\S+) r=(?P<r>\d+) "
    r"pvw_estimated_key_bytes=(?P<pvw_estimated_key_bytes>\d+) "
    r"scalar_one_estimated_key_bytes=(?P<scalar_one_estimated_key_bytes>\d+) "
    r"scalar_repeated_estimated_key_bytes=(?P<scalar_repeated_estimated_key_bytes>\d+) "
    r"pvw_vs_scalar_repeated_ratio=(?P<pvw_vs_scalar_repeated_ratio>[0-9.]+)"
)
RSS_RE = re.compile(
    r"SAB_PVW_NONBINARY_RESOURCE rss full_smoke mode=(?P<mode>\S+) r=(?P<r>\d+) "
    r"label=(?P<label>\S+) vmrss_kb=(?P<vmrss_kb>\d+) vmhwm_kb=(?P<vmhwm_kb>\d+)"
)
KEYGEN_RE = re.compile(
    r"SAB_PVW_NONBINARY_RESOURCE keygen full_smoke mode=(?P<mode>\S+) r=(?P<r>\d+) "
    r"(?P<key>pvw_sab_keygen_us|scalar_repeated_sab_keygen_us)=(?P<value>[0-9.]+)"
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


def variant_mode_from(path: Path) -> tuple[str, str] | None:
    name = path.name
    if not name.endswith("_r4_reps3_run.log"):
        return None
    if name.startswith("default_"):
        return "default", name.removeprefix("default_").removesuffix("_r4_reps3_run.log")
    if name.startswith("backend_from_dft_add_"):
        return "backend_from_dft_add", name.removeprefix("backend_from_dft_add_").removesuffix("_r4_reps3_run.log")
    return None


def parse_bench_logs() -> tuple[list[dict[str, str]], list[dict[str, str]]]:
    summaries: list[dict[str, str]] = []
    samples: list[dict[str, str]] = []
    for path in sorted(RAW.glob("*_r4_reps3_run.log")):
        parsed = variant_mode_from(path)
        if parsed is None:
            continue
        variant, mode = parsed
        text = path.read_text(encoding="utf-8", errors="replace")
        correctness = CORRECTNESS_RE.search(text)
        summary = SUMMARY_RE.search(text)
        if not correctness or not summary:
            raise SystemExit(f"missing correctness or summary line in {path}")
        for match in SAMPLE_RE.finditer(text):
            row = match.groupdict()
            row.update({"variant": variant, "mode": mode, "log": rel(path)})
            samples.append(row)
        row = summary.groupdict()
        corr = correctness.groupdict()
        cv = float(row["pvw_stddev_us"]) / float(row["pvw_avg_us"]) if float(row["pvw_avg_us"]) else 0.0
        row.update(
            {
                "variant": variant,
                "mode": mode,
                "h": corr["h"],
                "r_prec": corr["r_prec"],
                "correctness_gate": corr["gate"],
                "platform": "WSL2/Linux",
                "backend": "spqlios_avx512",
                "param": "SET_2_3",
                "primary_metric": "T_bootstrap/r",
                "pvw_cv": f"{cv:.6f}",
                "log": rel(path),
            }
        )
        summaries.append(row)
    summaries.sort(key=lambda row: (row["mode"], row["variant"]))
    samples.sort(key=lambda row: (row["mode"], row["variant"], int(row["rep"])))
    return summaries, samples


def parse_noise_resource() -> tuple[list[dict[str, str]], list[dict[str, str]]]:
    rows: list[dict[str, str]] = []
    resource: dict[tuple[str, str], dict[str, str]] = {}
    for path in sorted(RAW.glob("*full_noise_resource*_run.log")):
        text = path.read_text(encoding="utf-8", errors="replace")
        for match in NOISE_RE.finditer(text):
            row = match.groupdict()
            row.update({"variant": "backend_from_dft_add", "log": rel(path)})
            rows.append(row)
        for match in KEY_BYTES_RE.finditer(text):
            row = match.groupdict()
            key = (row["mode"], row["r"])
            resource.setdefault(key, {"mode": row["mode"], "r": row["r"], "variant": "backend_from_dft_add", "log": rel(path)}).update(row)
        for match in RSS_RE.finditer(text):
            row = match.groupdict()
            key = (row["mode"], row["r"])
            target = resource.setdefault(key, {"mode": row["mode"], "r": row["r"], "variant": "backend_from_dft_add", "log": rel(path)})
            target[f"{row['label']}_vmrss_kb"] = row["vmrss_kb"]
            target[f"{row['label']}_vmhwm_kb"] = row["vmhwm_kb"]
        for match in KEYGEN_RE.finditer(text):
            row = match.groupdict()
            key = (row["mode"], row["r"])
            resource.setdefault(key, {"mode": row["mode"], "r": row["r"], "variant": "backend_from_dft_add", "log": rel(path)})[row["key"]] = row["value"]
    rows.sort(key=lambda row: (int(row["r"]), row["mode"]))
    resource_rows = sorted(resource.values(), key=lambda row: (int(row["r"]), row["mode"]))
    return rows, resource_rows


def compare_rows(summary: list[dict[str, str]]) -> list[dict[str, str]]:
    by_key = {(row["variant"], row["mode"]): row for row in summary}
    out = []
    for mode in ["include_zero", "ternary"]:
        base = by_key.get(("default", mode))
        cand = by_key.get(("backend_from_dft_add", mode))
        if not base or not cand:
            out.append({"mode": mode, "status": "MISSING"})
            continue
        base_us = float(base["t_bootstrap_over_r_pvw_us"])
        cand_us = float(cand["t_bootstrap_over_r_pvw_us"])
        speedup = base_us / cand_us if cand_us else 0.0
        delta = (cand_us / base_us - 1.0) * 100.0 if base_us else 0.0
        out.append(
            {
                "mode": mode,
                "r": "4",
                "reps": cand["reps"],
                "default_t_bootstrap_over_r_us": f"{base_us:.3f}",
                "backend_t_bootstrap_over_r_us": f"{cand_us:.3f}",
                "backend_speedup_vs_default": f"{speedup:.6f}",
                "backend_delta_pct": f"{delta:.3f}",
                "default_pvw_cv": base["pvw_cv"],
                "backend_pvw_cv": cand["pvw_cv"],
                "default_correctness": base["correctness_gate"],
                "backend_correctness": cand["correctness_gate"],
                "status": "positive" if speedup >= 1.01 else "neutral_or_negative",
            }
        )
    return out


def decision_from(summary: list[dict[str, str]], comparison: list[dict[str, str]], noise: list[dict[str, str]], resource: list[dict[str, str]]) -> str:
    expected = {
        ("default", "include_zero"),
        ("default", "ternary"),
        ("backend_from_dft_add", "include_zero"),
        ("backend_from_dft_add", "ternary"),
    }
    covered = {(row["variant"], row["mode"]) for row in summary}
    if not expected.issubset(covered):
        return "FAIL_STAGE269_REPEATED_MISSING_COVERAGE"
    if any(row["correctness_gate"] != "Pass" for row in summary):
        return "FAIL_STAGE269_REPEATED_CORRECTNESS"
    if not all(row.get("status") == "positive" for row in comparison):
        return "NEUTRAL_STAGE269_BACKEND_FROM_DFT_ADD_REPEATED_NO_PROMOTION"
    noise_r4 = [row for row in noise if row["r"] == "4" and row["mode"] in {"include_zero", "ternary"}]
    resource_r4 = [row for row in resource if row["r"] == "4" and row["mode"] in {"include_zero", "ternary"}]
    if len(noise_r4) < 2 or len(resource_r4) < 2:
        return "PASS_STAGE269_REPEATED_PERF_NOISE_RESOURCE_PENDING"
    if any(row["gate"] != "Pass" for row in noise_r4):
        return "FAIL_STAGE269_NOISE_GATE"
    return "PASS_STAGE269_BACKEND_FROM_DFT_ADD_REPEATED_NOISE_RESOURCE"


def proof_rows(summary: list[dict[str, str]], comparison: list[dict[str, str]], noise: list[dict[str, str]], resource: list[dict[str, str]], decision: str) -> list[dict[str, str]]:
    min_speedup = min((float(row.get("backend_speedup_vs_default", "0") or "0") for row in comparison), default=0.0)
    max_cv = max((float(row.get("pvw_cv", "0") or "0") for row in summary), default=0.0)
    noise_r4 = [row for row in noise if row["r"] == "4" and row["mode"] in {"include_zero", "ternary"}]
    resource_r4 = [row for row in resource if row["r"] == "4" and row["mode"] in {"include_zero", "ternary"}]
    return [
        {"gate": "G1_repeated_coverage", "status": "PASS" if len(summary) == 4 else "FAIL", "metric": "reps=3 default/backend r=4 modes", "value": str(len(summary)), "evidence": "bench_summary.csv", "interpretation": "Repeated timing covers both non-binary modes and both PVW variants."},
        {"gate": "G2_correctness", "status": "PASS" if all(row["correctness_gate"] == "Pass" for row in summary) else "FAIL", "metric": "PVW/scalar target correctness", "value": f"{sum(row['correctness_gate'] == 'Pass' for row in summary)}/{len(summary)}", "evidence": "bench_summary.csv", "interpretation": "Timing is only interpreted after correctness passes."},
        {"gate": "G3_repeated_speed", "status": "PASS" if min_speedup >= 1.01 else "NEUTRAL", "metric": "minimum backend speedup vs default", "value": f"{min_speedup:.6f}x", "evidence": "variant_compare.csv", "interpretation": "Repeated performance must retain the Stage268 smoke benefit in both modes."},
        {"gate": "G4_variability", "status": "PASS" if max_cv <= 0.05 else "REVIEW", "metric": "max PVW coefficient of variation", "value": f"{max_cv:.6f}", "evidence": "bench_summary.csv; sample_rows.csv", "interpretation": "Small local variation supports, but does not replace, native repeated evidence."},
        {"gate": "G5_noise", "status": "PASS" if len(noise_r4) == 2 and all(row["gate"] == "Pass" for row in noise_r4) else "PENDING", "metric": "r=4 backend full-noise rows", "value": f"{len(noise_r4)}/2", "evidence": "noise_summary.csv", "interpretation": "Noise/resource gate is separate from repeated timing."},
        {"gate": "G6_resource", "status": "PASS" if len(resource_r4) == 2 else "PENDING", "metric": "r=4 backend resource rows", "value": f"{len(resource_r4)}/2", "evidence": "resource_summary.csv", "interpretation": "Key size and RSS evidence must accompany promoted performance."},
        {"gate": "G7_claim_boundary", "status": "PASS", "metric": "claim level", "value": "WSL repeated; trials1 noise if present", "evidence": "claim_boundary.csv", "interpretation": "Still not native paper-grade performance or multi-seed failure-rate evidence."},
        {"gate": "G8_decision", "status": decision, "metric": "stage decision", "value": decision, "evidence": "proof_gate.csv", "interpretation": "Final promotion requires repeated timing plus noise/resource coverage."},
    ]


def claim_rows(decision: str) -> list[dict[str, str]]:
    return [
        {"claim": "backend_from_dft_add_repeated_t_over_r", "status": "supported_wsl_repeated" if decision.startswith("PASS_STAGE269") else "not_promoted", "allowed_wording": "Stage269 reports repeated WSL same-backend T_bootstrap/r for backend FromDFT-add versus default PVW/MAT-SAB.", "forbidden_wording": "This alone is final native Linux paper-grade speedup.", "evidence": "variant_compare.csv; sample_rows.csv"},
        {"claim": "noise_resource", "status": "supported_trials1" if decision == "PASS_STAGE269_BACKEND_FROM_DFT_ADD_REPEATED_NOISE_RESOURCE" else "pending_or_failed", "allowed_wording": "If present, Stage269 full-noise/resource is a one-trial gate for r=4 include-zero/ternary.", "forbidden_wording": "One trial establishes failure-rate bounds.", "evidence": "noise_summary.csv; resource_summary.csv"},
        {"claim": "algorithm_metric", "status": "aligned", "allowed_wording": "The primary metric is T_bootstrap/r, matching the r-body MAT-RLWE intent.", "forbidden_wording": "Use total batch latency alone as the speedup dimension.", "evidence": "bench_summary.csv; variant_compare.csv"},
    ]


def next_rows(decision: str) -> list[dict[str, str]]:
    if decision == "PASS_STAGE269_BACKEND_FROM_DFT_ADD_REPEATED_NOISE_RESOURCE":
        return [
            {"priority": "P0", "route": "stage270_native_counter_or_native_repeated", "entry_condition": "Stage269 repeated timing plus trials1 noise/resource pass.", "gate": "native Linux counters/repeated rows, same metric.", "status": "selected", "failure_action": "Downgrade to WSL evidence only."},
            {"priority": "P1", "route": "stage271_multiseed_noise", "entry_condition": "Need paper-grade reliability.", "gate": "higher seed/trial count and failure-rate report.", "status": "conditional", "failure_action": "No failure-rate claim."},
        ]
    if decision == "PASS_STAGE269_REPEATED_PERF_NOISE_RESOURCE_PENDING":
        return [
            {"priority": "P0", "route": "stage270_backend_noise_resource_completion", "entry_condition": "Repeated timing passed but noise/resource missing.", "gate": "run backend full-noise/resource trials1 at minimum.", "status": "selected", "failure_action": "No promoted performance claim without resource/noise."},
        ]
    return [
        {"priority": "P0", "route": "stage270_candidate_closeout", "entry_condition": "Repeated timing did not promote.", "gate": "record neutral/failed candidate and return to Stage267 queue.", "status": "selected", "failure_action": "Do not use Stage268 smoke as performance evidence."},
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
    append_once(CURRENT_GOAL, "### Stage269 backend FromDFT-add repeated/noise/resource", f"""
### Stage269 backend FromDFT-add repeated/noise/resource

`{decision}` records the repeated timing and optional noise/resource gate for
the existing backend FromDFT-add route. The primary metric remains
`T_bootstrap/r`.
""")
    append_once(HYPOTHESES, "H10_stage269_backend_from_dft_add_repeated_noise_resource:", f"""
H10_stage269_backend_from_dft_add_repeated_noise_resource:
  status: {decision}
  evidence:
    - repro/stage269_backend_from_dft_add_repeated_noise_resource/variant_compare.csv
    - repro/stage269_backend_from_dft_add_repeated_noise_resource/proof_gate.csv
    - docs/stage269_backend_from_dft_add_repeated_noise_resource.md
  conclusion: >
    Stage269 records {decision}. It keeps the metric aligned with MAT-RLWE
    amortization by comparing `T_bootstrap/r` for backend FromDFT-add versus
    default PVW/MAT-SAB under the same backend.
""")
    append_once(RUN_LOG, "stage269-backend-from-dft-add-repeated-noise-resource-001", f"""stage269-backend-from-dft-add-repeated-noise-resource-001,2026-07-04,{head},Stage 269,spqlios_avx512,python scripts/build_stage269_backend_from_dft_add_repeated_noise_resource.py,"backend FromDFT-add repeated timing plus noise/resource if present; primary metric T_bootstrap/r",n/a,{decision},"Promotion requires repeated timing and noise/resource gates; WSL evidence is not native paper-grade.",docs/stage269_backend_from_dft_add_repeated_noise_resource.md; repro/stage269_backend_from_dft_add_repeated_noise_resource/proof_gate.csv
""")
    append_once(MANIFEST, "- stage269_backend_from_dft_add_repeated_noise_resource:", """
- stage269_backend_from_dft_add_repeated_noise_resource:
  - `docs/stage269_backend_from_dft_add_repeated_noise_resource.md`
  - `scripts/run_stage269_backend_from_dft_add_repeated_noise_resource.sh`
  - `scripts/build_stage269_backend_from_dft_add_repeated_noise_resource.py`
  - `repro/stage269_backend_from_dft_add_repeated_noise_resource/`
""")
    append_once(CHECKLIST, "stage269-backend-from-dft-add-repeated-noise-resource-checklist", f"""
<!-- stage269-backend-from-dft-add-repeated-noise-resource-checklist -->
- [x] Stage269 backend FromDFT-add repeated/noise/resource records `{decision}` with primary metric `T_bootstrap/r`.
""")


def main() -> int:
    REPRO.mkdir(parents=True, exist_ok=True)
    summary, samples = parse_bench_logs()
    noise, resource = parse_noise_resource()
    comparison = compare_rows(summary)
    decision = decision_from(summary, comparison, noise, resource)
    proof = proof_rows(summary, comparison, noise, resource, decision)
    claims = claim_rows(decision)
    queue = next_rows(decision)

    write_csv(REPRO / "bench_summary.csv", summary, [
        "platform", "backend", "param", "variant", "mode", "r", "reps", "h", "r_prec",
        "correctness_gate", "pvw_avg_us", "pvw_stddev_us", "pvw_cv", "pvw_lane_avg_us",
        "scalar_repeated_avg_us", "scalar_stddev_us", "scalar_lane_avg_us",
        "speedup_vs_scalar_repeated", "speedup_stddev", "t_bootstrap_over_r_pvw_us",
        "t_bootstrap_over_r_scalar_us", "primary_metric", "log",
    ])
    write_csv(REPRO / "sample_rows.csv", samples, [
        "variant", "mode", "r", "rep", "pvw_us", "pvw_lane_us",
        "scalar_repeated_us", "scalar_lane_us", "speedup", "log",
    ])
    write_csv(REPRO / "variant_compare.csv", comparison, [
        "mode", "r", "reps", "default_t_bootstrap_over_r_us", "backend_t_bootstrap_over_r_us",
        "backend_speedup_vs_default", "backend_delta_pct", "default_pvw_cv", "backend_pvw_cv",
        "default_correctness", "backend_correctness", "status",
    ])
    write_csv(REPRO / "noise_summary.csv", noise, [
        "variant", "mode", "r", "trials", "points", "pvw_failures", "scalar_failures",
        "pair_failures", "pvw_log2_sigma_torus", "scalar_log2_sigma_torus",
        "pair_log2_sigma_torus", "pair_log2_max_abs_torus", "gate", "log",
    ])
    write_csv(REPRO / "resource_summary.csv", resource, [
        "variant", "mode", "r", "pvw_estimated_key_bytes", "scalar_one_estimated_key_bytes",
        "scalar_repeated_estimated_key_bytes", "pvw_vs_scalar_repeated_ratio",
        "pvw_sab_keygen_us", "scalar_repeated_sab_keygen_us",
        "after_pvw_sab_keygen_vmrss_kb", "after_pvw_sab_keygen_vmhwm_kb",
        "after_scalar_repeated_sab_keygen_vmrss_kb", "after_scalar_repeated_sab_keygen_vmhwm_kb",
        "log",
    ])
    write_csv(REPRO / "proof_gate.csv", proof, ["gate", "status", "metric", "value", "evidence", "interpretation"])
    write_csv(REPRO / "claim_boundary.csv", claims, ["claim", "status", "allowed_wording", "forbidden_wording", "evidence"])
    write_csv(REPRO / "next_stage_queue.csv", queue, ["priority", "route", "entry_condition", "gate", "status", "failure_action"])

    report = f"""# Stage269 Backend FromDFT-add Repeated Noise/Resource

Decision: `{decision}`.

Stage269 is the promotion gate after the positive Stage268 smoke. The primary
metric remains the MAT-RLWE amortized metric:

```text
T_bootstrap / r
```

## Variant Comparison

{table(comparison, ["mode", "r", "reps", "default_t_bootstrap_over_r_us", "backend_t_bootstrap_over_r_us", "backend_speedup_vs_default", "backend_delta_pct", "default_pvw_cv", "backend_pvw_cv", "status"])}

## Noise Summary

{table([row for row in noise if row.get("r") == "4"], ["mode", "r", "trials", "points", "pvw_failures", "scalar_failures", "pair_failures", "pair_log2_sigma_torus", "pair_log2_max_abs_torus", "gate"])}

## Resource Summary

{table([row for row in resource if row.get("r") == "4"], ["mode", "r", "pvw_vs_scalar_repeated_ratio", "pvw_sab_keygen_us", "scalar_repeated_sab_keygen_us", "after_pvw_sab_keygen_vmhwm_kb", "after_scalar_repeated_sab_keygen_vmhwm_kb"])}

## Proof Gate

{table(proof, ["gate", "status", "metric", "value", "interpretation"])}

## Claim Boundary

{table(claims, ["claim", "status", "allowed_wording", "forbidden_wording"])}

## Next Queue

{table(queue, ["priority", "route", "entry_condition", "gate", "status", "failure_action"])}

Generated from input head `{git_head()}`.
"""
    write_text(DOC, report)
    write_text(REPRO / "stage269_report.md", report)
    write_text(REPRO / "reproduction_commands.md", """# Stage269 Reproduction Commands

Repeated timing plus noise/resource:

```bash
bash scripts/run_stage269_backend_from_dft_add_repeated_noise_resource.sh
python3 scripts/build_stage269_backend_from_dft_add_repeated_noise_resource.py
```

To split the long run:

```bash
RUN_NOISE_RESOURCE=0 bash scripts/run_stage269_backend_from_dft_add_repeated_noise_resource.sh
RUN_REPEATED=0 bash scripts/run_stage269_backend_from_dft_add_repeated_noise_resource.sh
```
""")
    update_tracking(decision)
    paths = [
        DOC,
        REPRO / "stage269_report.md",
        REPRO / "reproduction_commands.md",
        REPRO / "bench_summary.csv",
        REPRO / "sample_rows.csv",
        REPRO / "variant_compare.csv",
        REPRO / "noise_summary.csv",
        REPRO / "resource_summary.csv",
        REPRO / "proof_gate.csv",
        REPRO / "claim_boundary.csv",
        REPRO / "next_stage_queue.csv",
        ROOT / "scripts" / "run_stage269_backend_from_dft_add_repeated_noise_resource.sh",
        Path(__file__),
    ]
    write_csv(REPRO / "artifact_index.csv", artifacts(paths), ["path", "bytes", "sha256"])
    print(decision)
    return 1 if decision.startswith("FAIL_") else 0


if __name__ == "__main__":
    raise SystemExit(main())
