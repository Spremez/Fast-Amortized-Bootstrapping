#!/usr/bin/env python3
"""Build Stage276 include-zero coeff-one fast-path artifacts."""

from __future__ import annotations

import csv
import hashlib
import re
import subprocess
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
REPRO = ROOT / "repro" / "stage276_include_zero_coeff_one_fast_path"
RAW = REPRO / "raw"
DOC = ROOT / "docs" / "stage276_include_zero_coeff_one_fast_path.md"
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
    suffix = "_include_zero_r4_reps1_run.log"
    if not name.endswith(suffix):
        return None
    stem = name.removesuffix(suffix)
    return stem if stem in VARIANTS else None


def parse_logs() -> list[dict[str, str]]:
    rows: list[dict[str, str]] = []
    for path in sorted(RAW.glob("*_run.log")):
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
    backend_vs_default = base_us / backend_us if backend_us else 0.0
    return [
        {
            "mode": "include_zero",
            "r": "4",
            "default_t_bootstrap_over_r_us": f"{base_us:.3f}",
            "backend_t_bootstrap_over_r_us": f"{backend_us:.3f}",
            "fast_t_bootstrap_over_r_us": f"{fast_us:.3f}",
            "backend_speedup_vs_default": f"{backend_vs_default:.6f}",
            "fast_speedup_vs_default": f"{fast_vs_default:.6f}",
            "fast_speedup_vs_backend": f"{fast_vs_backend:.6f}",
            "default_correctness": base["correctness_gate"],
            "backend_correctness": backend["correctness_gate"],
            "fast_correctness": fast["correctness_gate"],
            "status": "positive" if fast_vs_backend >= 1.01 and fast_vs_default >= 1.01 else "neutral_or_negative",
        }
    ]


def decision_from(summary: list[dict[str, str]], comparison: list[dict[str, str]]) -> str:
    expected = {"default", "backend_from_dft_add", "include_zero_coeff_one_fast"}
    covered = {row["variant"] for row in summary}
    if not expected.issubset(covered):
        return "FAIL_STAGE276_INCLUDE_ZERO_FAST_MISSING_COVERAGE"
    if any(row["mode"] != "include_zero" for row in summary):
        return "FAIL_STAGE276_INCLUDE_ZERO_FAST_WRONG_MODE"
    if any(row["correctness_gate"] != "Pass" for row in summary):
        return "FAIL_STAGE276_INCLUDE_ZERO_FAST_CORRECTNESS"
    if comparison and comparison[0].get("status") == "positive":
        return "PASS_STAGE276_INCLUDE_ZERO_FAST_SMOKE_POSITIVE_REPEAT_REQUIRED"
    return "NEUTRAL_STAGE276_INCLUDE_ZERO_FAST_SMOKE_NO_PROMOTION"


def proof_rows(summary: list[dict[str, str]], comparison: list[dict[str, str]], decision: str) -> list[dict[str, str]]:
    covered = ",".join(f"{row['variant']}:{row['mode']}" for row in summary)
    fast_vs_backend = comparison[0].get("fast_speedup_vs_backend", "0") if comparison else "0"
    return [
        {"gate": "G1_coverage", "status": "PASS" if len(summary) == 3 else "FAIL", "metric": "variant coverage", "value": covered, "evidence": "bench_summary.csv", "interpretation": "Covers default, backend direct-add, and include-zero coeff-one fast path."},
        {"gate": "G2_correctness", "status": "PASS" if all(row["correctness_gate"] == "Pass" for row in summary) else "FAIL", "metric": "PVW/scalar target correctness", "value": f"{sum(row['correctness_gate'] == 'Pass' for row in summary)}/{len(summary)}", "evidence": "bench_summary.csv", "interpretation": "Correctness must pass before interpreting timing."},
        {"gate": "G3_primary_metric", "status": "PASS", "metric": "T_bootstrap/r", "value": "fast_vs_backend_and_default", "evidence": "variant_compare.csv", "interpretation": "The fast path must beat both same-backend backend direct-add and default on the amortized per-body metric."},
        {"gate": "G4_smoke_threshold", "status": "PASS" if comparison and comparison[0].get("status") == "positive" else "NEUTRAL", "metric": "fast speedup vs backend", "value": f"{fast_vs_backend}x", "evidence": "variant_compare.csv", "interpretation": "Single-run smoke threshold is 1.01x; repeated/noise/resource is still required for promotion."},
        {"gate": "G5_claim_boundary", "status": "PASS_SMOKE_ONLY", "metric": "scope", "value": "current_pvw_include_zero_only", "evidence": "claim_boundary.csv", "interpretation": "This does not claim a general include-zero SAB shortcut or ternary improvement."},
        {"gate": "G6_decision", "status": decision, "metric": "stage decision", "value": decision, "evidence": "proof_gate.csv", "interpretation": "Promotion requires repeated timing and noise/resource if smoke is positive."},
    ]


def claim_rows(decision: str) -> list[dict[str, str]]:
    return [
        {
            "claim": "include_zero_coeff_one_fast_path",
            "status": "smoke_positive" if decision.startswith("PASS_") else "neutral_or_failed",
            "allowed_wording": "Stage276 tests a guarded current-PVW include-zero coeff-one fast path under an explicit flag.",
            "forbidden_wording": "All include-zero SAB can remove s_coff.",
            "evidence": "variant_compare.csv; proof_gate.csv",
        },
        {
            "claim": "complete_sab_speedup",
            "status": "smoke_only",
            "allowed_wording": "The smoke reports full SAB T_bootstrap/r for include-zero r=4.",
            "forbidden_wording": "The smoke is final repeated evidence or covers ternary.",
            "evidence": "bench_summary.csv",
        },
    ]


def next_rows(decision: str) -> list[dict[str, str]]:
    if decision.startswith("PASS_"):
        return [
            {"priority": "P0", "route": "stage277_include_zero_fast_repeated_noise_resource", "entry_condition": "Stage276 smoke positive.", "gate": "Repeated T_bootstrap/r plus noise/resource for include-zero fast path.", "status": "selected", "failure_action": "Demote if repeated/noise/resource fails."},
            {"priority": "P1", "route": "stage278_generalize_or_selector_kernel", "entry_condition": "Stage277 passes or residual profile suggests selector MAT EP work.", "gate": "Decide whether current-PVW include-zero fast path is paper-claimable or only engineering-specialized.", "status": "conditional", "failure_action": "Keep claim guarded."},
        ]
    return [
        {"priority": "P0", "route": "stage277_selector_mat_ep_kernel_tiling", "entry_condition": "Stage276 neutral or failed.", "gate": "Selector MAT-EP microbench/profile and explicit candidate design.", "status": "selected", "failure_action": "No claim without full SAB A/B."},
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
    append_once(CURRENT_GOAL, "### Stage276 include-zero coeff-one fast path", f"""
### Stage276 include-zero coeff-one fast path

`{decision}` records an explicit-flag smoke for the guarded current-PVW
include-zero coeff-one fast path. The primary metric is `T_bootstrap/r`; the
scope is include-zero only.
""")
    append_once(HYPOTHESES, "H10_stage276_include_zero_coeff_one_fast_path:", f"""
H10_stage276_include_zero_coeff_one_fast_path:
  status: {decision}
  evidence:
    - repro/stage276_include_zero_coeff_one_fast_path/bench_summary.csv
    - repro/stage276_include_zero_coeff_one_fast_path/variant_compare.csv
    - repro/stage276_include_zero_coeff_one_fast_path/proof_gate.csv
    - docs/stage276_include_zero_coeff_one_fast_path.md
  conclusion: >
    Stage276 records {decision}. It tests only the guarded current-PVW
    include-zero coeff-one fast path and keeps claims scoped to full SAB
    smoke evidence until repeated/noise/resource gates pass.
""")
    append_once(RUN_LOG, "stage276-include-zero-coeff-one-fast-path-001", f"""stage276-include-zero-coeff-one-fast-path-001,2026-07-04,{head},Stage 276,spqlios_avx512,bash scripts/run_stage276_include_zero_coeff_one_fast_path.sh; python scripts/build_stage276_include_zero_coeff_one_fast_path.py,"r=4 include-zero default-vs-backend-vs-coeff-one-fast full SAB smoke; primary metric T_bootstrap/r",n/a,{decision},"Single-run smoke; promotion requires repeated/noise/resource if positive.",docs/stage276_include_zero_coeff_one_fast_path.md; repro/stage276_include_zero_coeff_one_fast_path/proof_gate.csv
""")
    append_once(MANIFEST, "- stage276_include_zero_coeff_one_fast_path:", """
- stage276_include_zero_coeff_one_fast_path:
  - `docs/stage276_include_zero_coeff_one_fast_path.md`
  - `scripts/run_stage276_include_zero_coeff_one_fast_path.sh`
  - `scripts/build_stage276_include_zero_coeff_one_fast_path.py`
  - `repro/stage276_include_zero_coeff_one_fast_path/`
""")
    append_once(CHECKLIST, "stage276-include-zero-coeff-one-fast-path-checklist", f"""
<!-- stage276-include-zero-coeff-one-fast-path-checklist -->
- [x] Stage276 include-zero coeff-one fast-path smoke records `{decision}` with primary metric `T_bootstrap/r`.
""")


def main() -> int:
    REPRO.mkdir(parents=True, exist_ok=True)
    summary = parse_logs()
    comparison = compare_rows(summary)
    decision = decision_from(summary, comparison)
    proof = proof_rows(summary, comparison, decision)
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
        "mode", "r", "default_t_bootstrap_over_r_us",
        "backend_t_bootstrap_over_r_us", "fast_t_bootstrap_over_r_us",
        "backend_speedup_vs_default", "fast_speedup_vs_default",
        "fast_speedup_vs_backend", "default_correctness",
        "backend_correctness", "fast_correctness", "status",
    ])
    write_csv(REPRO / "proof_gate.csv", proof, ["gate", "status", "metric", "value", "evidence", "interpretation"])
    write_csv(REPRO / "claim_boundary.csv", claims, ["claim", "status", "allowed_wording", "forbidden_wording", "evidence"])
    write_csv(REPRO / "next_stage_queue.csv", queue, ["priority", "route", "entry_condition", "gate", "status", "failure_action"])

    report = f"""# Stage276 Include-Zero Coeff-One Fast Path

Decision: `{decision}`.

Stage276 implements and screens the explicit
`SAB_PVW_SUBA_INCLUDE_ZERO_COEFF_ONE_FAST` flag. This is guarded to current PVW
include-zero semantics where scanned nonzero coefficients are coefficient-one.

## Bench Summary

{table(summary, ["variant", "mode", "r", "reps", "correctness_gate", "t_bootstrap_over_r_pvw_us", "speedup_vs_scalar_repeated"])}

## Variant Comparison

{table(comparison, ["mode", "r", "default_t_bootstrap_over_r_us", "backend_t_bootstrap_over_r_us", "fast_t_bootstrap_over_r_us", "fast_speedup_vs_default", "fast_speedup_vs_backend", "status"])}

## Proof Gate

{table(proof, ["gate", "status", "metric", "value", "interpretation"])}

## Claim Boundary

{table(claims, ["claim", "status", "allowed_wording", "forbidden_wording"])}

## Next Queue

{table(queue, ["priority", "route", "entry_condition", "gate", "status", "failure_action"])}

Generated from input head `{git_head()}`.
"""
    write_text(DOC, report)
    write_text(REPRO / "stage276_report.md", report)
    write_text(REPRO / "reproduction_commands.md", """# Stage276 Reproduction Commands

```bash
bash scripts/run_stage276_include_zero_coeff_one_fast_path.sh
python3 scripts/build_stage276_include_zero_coeff_one_fast_path.py
```

Stage276 is a single-run full SAB include-zero smoke. Promotion requires
repeated timing and noise/resource gates.
""")
    update_tracking(decision)
    paths = [
        DOC,
        REPRO / "stage276_report.md",
        REPRO / "reproduction_commands.md",
        REPRO / "bench_summary.csv",
        REPRO / "variant_compare.csv",
        REPRO / "proof_gate.csv",
        REPRO / "claim_boundary.csv",
        REPRO / "next_stage_queue.csv",
        Path(__file__),
        ROOT / "scripts" / "run_stage276_include_zero_coeff_one_fast_path.sh",
        ROOT / "src" / "sab_pvw.c",
        ROOT / "src" / "mosfhet" / "Makefile.def",
    ]
    write_csv(REPRO / "artifact_index.csv", artifacts(paths), ["path", "bytes", "sha256"])
    print(decision)
    return 0 if decision.startswith("PASS_") or decision.startswith("NEUTRAL_") else 1


if __name__ == "__main__":
    raise SystemExit(main())
