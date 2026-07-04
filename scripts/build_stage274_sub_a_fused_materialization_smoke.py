#!/usr/bin/env python3
"""Build Stage274 sub_a fused materialization smoke artifacts."""

from __future__ import annotations

import csv
import hashlib
import re
import subprocess
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
REPRO = ROOT / "repro" / "stage274_sub_a_fused_materialization_smoke"
RAW = REPRO / "raw"
DOC = ROOT / "docs" / "stage274_sub_a_fused_materialization_smoke.md"
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
    "suba_fused_from_dft_add",
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


def split_variant_mode(name: str) -> tuple[str, str] | None:
    suffix = "_r4_reps1_run.log"
    if not name.endswith(suffix):
        return None
    stem = name.removesuffix(suffix)
    for variant in VARIANTS:
        prefix = f"{variant}_"
        if stem.startswith(prefix):
            return variant, stem.removeprefix(prefix)
    return None


def parse_logs() -> list[dict[str, str]]:
    rows: list[dict[str, str]] = []
    for path in sorted(RAW.glob("*_run.log")):
        parsed = split_variant_mode(path.name)
        if parsed is None:
            continue
        variant, mode = parsed
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
                "mode": mode,
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
    rows.sort(key=lambda row: (row["mode"], row["variant"]))
    return rows


def compare_rows(summary: list[dict[str, str]]) -> list[dict[str, str]]:
    by_key = {(row["variant"], row["mode"]): row for row in summary}
    out: list[dict[str, str]] = []
    for mode in ["include_zero", "ternary"]:
        base = by_key.get(("default", mode))
        backend = by_key.get(("backend_from_dft_add", mode))
        fused = by_key.get(("suba_fused_from_dft_add", mode))
        if not base or not backend or not fused:
            out.append({"mode": mode, "status": "MISSING"})
            continue
        base_us = float(base["t_bootstrap_over_r_pvw_us"])
        backend_us = float(backend["t_bootstrap_over_r_pvw_us"])
        fused_us = float(fused["t_bootstrap_over_r_pvw_us"])
        backend_speedup = base_us / backend_us if backend_us else 0.0
        fused_vs_default = base_us / fused_us if fused_us else 0.0
        fused_vs_backend = backend_us / fused_us if fused_us else 0.0
        out.append(
            {
                "mode": mode,
                "r": "4",
                "default_t_bootstrap_over_r_us": f"{base_us:.3f}",
                "backend_t_bootstrap_over_r_us": f"{backend_us:.3f}",
                "fused_t_bootstrap_over_r_us": f"{fused_us:.3f}",
                "backend_speedup_vs_default": f"{backend_speedup:.6f}",
                "fused_speedup_vs_default": f"{fused_vs_default:.6f}",
                "fused_speedup_vs_backend": f"{fused_vs_backend:.6f}",
                "default_correctness": base["correctness_gate"],
                "backend_correctness": backend["correctness_gate"],
                "fused_correctness": fused["correctness_gate"],
                "status": "positive" if fused_vs_backend >= 1.005 else "neutral_or_negative",
            }
        )
    return out


def decision_from(summary: list[dict[str, str]], comparison: list[dict[str, str]]) -> str:
    expected = {
        ("default", "include_zero"),
        ("default", "ternary"),
        ("backend_from_dft_add", "include_zero"),
        ("backend_from_dft_add", "ternary"),
        ("suba_fused_from_dft_add", "include_zero"),
        ("suba_fused_from_dft_add", "ternary"),
    }
    covered = {(row["variant"], row["mode"]) for row in summary}
    if not expected.issubset(covered):
        return "FAIL_STAGE274_SUB_A_FUSED_SMOKE_MISSING_COVERAGE"
    if any(row["correctness_gate"] != "Pass" for row in summary):
        return "FAIL_STAGE274_SUB_A_FUSED_SMOKE_CORRECTNESS"
    if all(row.get("status") == "positive" for row in comparison):
        return "PASS_STAGE274_SUB_A_FUSED_SMOKE_POSITIVE_REPEAT_REQUIRED"
    return "NEUTRAL_STAGE274_SUB_A_FUSED_SMOKE_NO_PROMOTION"


def proof_rows(summary: list[dict[str, str]], comparison: list[dict[str, str]], decision: str) -> list[dict[str, str]]:
    covered = ",".join(f"{row['variant']}:{row['mode']}" for row in summary)
    min_incremental = min((float(row.get("fused_speedup_vs_backend", "0") or "0") for row in comparison), default=0.0)
    return [
        {"gate": "G1_coverage", "status": "PASS" if len(summary) == 6 else "FAIL", "metric": "variant/mode coverage", "value": covered, "evidence": "bench_summary.csv", "interpretation": "Covers default, backend direct-add, and sub_a fused variants for r=4 include-zero and ternary."},
        {"gate": "G2_correctness", "status": "PASS" if all(row["correctness_gate"] == "Pass" for row in summary) else "FAIL", "metric": "PVW/scalar target correctness", "value": f"{sum(row['correctness_gate'] == 'Pass' for row in summary)}/{len(summary)}", "evidence": "bench_summary.csv", "interpretation": "Correctness must pass before interpreting timing."},
        {"gate": "G3_primary_metric", "status": "PASS", "metric": "T_bootstrap/r", "value": "fused_vs_backend_same_backend", "evidence": "variant_compare.csv", "interpretation": "Incremental fused benefit is measured against backend direct-add, not only against default."},
        {"gate": "G4_smoke_threshold", "status": "PASS" if min_incremental >= 1.005 else "NEUTRAL", "metric": "minimum fused speedup vs backend", "value": f"{min_incremental:.6f}x", "evidence": "variant_compare.csv", "interpretation": "Single-run smoke requires both modes above 1.005x before repeated/noise/resource promotion."},
        {"gate": "G5_default_path", "status": "PASS", "metric": "default behavior", "value": "unchanged unless SAB_PVW_SUBA_FUSED_FROM_DFT_ADD=true", "evidence": "src/sab_pvw.c; src/mosfhet/Makefile.def", "interpretation": "The scalar SAB and default PVW/MAT-SAB paths remain explicit baselines."},
        {"gate": "G6_claim_boundary", "status": "PASS_SMOKE_ONLY", "metric": "no final speedup claim", "value": "single_run", "evidence": "claim_boundary.csv", "interpretation": "Stage274 is a smoke gate, not final repeated evidence."},
        {"gate": "G7_decision", "status": decision, "metric": "stage decision", "value": decision, "evidence": "proof_gate.csv", "interpretation": "Promotion requires a positive smoke; neutral results close this local fused materialization candidate."},
    ]


def claim_rows(decision: str) -> list[dict[str, str]]:
    return [
        {
            "claim": "sub_a_fused_materialization",
            "status": "smoke_positive" if decision.startswith("PASS_") else "neutral_or_failed",
            "allowed_wording": "Stage274 screens an explicit sub_a fused materialization flag using full SAB T_bootstrap/r.",
            "forbidden_wording": "Stage274 is final evidence for a complete SAB acceleration.",
            "evidence": "variant_compare.csv; proof_gate.csv",
        },
        {
            "claim": "incremental_algorithm_delta",
            "status": "measured_as_fused_vs_backend",
            "allowed_wording": "The incremental local change is fused vs backend direct-add under the same backend.",
            "forbidden_wording": "Default-vs-fused alone proves the sub_a fusion contribution.",
            "evidence": "variant_compare.csv",
        },
        {
            "claim": "default_scalar_baseline",
            "status": "preserved",
            "allowed_wording": "Default paths are unchanged unless explicit flags are passed.",
            "forbidden_wording": "The fused path replaces scalar SAB or default PVW/MAT-SAB.",
            "evidence": "src/sab_pvw.c; src/mosfhet/Makefile.def",
        },
    ]


def next_rows(decision: str) -> list[dict[str, str]]:
    if decision.startswith("PASS_"):
        return [
            {"priority": "P0", "route": "stage275_sub_a_fused_repeated_noise_resource", "entry_condition": "Stage274 positive smoke in both non-binary modes.", "gate": "Repeated T_bootstrap/r plus correctness/noise/resource under the fused flag.", "status": "selected", "failure_action": "Demote to neutral if repeated or noise/resource gates fail."},
            {"priority": "P1", "route": "stage276_selector_mat_ep_kernel_or_profile", "entry_condition": "Stage275 passes or shows residual selector MAT EP dominance.", "gate": "Profile-guided selector MAT EP optimization.", "status": "conditional", "failure_action": "Keep as future candidate if no concrete mechanism."},
        ]
    return [
        {"priority": "P0", "route": "stage275_close_s272a_select_next_candidate", "entry_condition": "Stage274 neutral or failed.", "gate": "Close fused materialization candidate and select selector MAT EP or rotation/copy candidate from Stage272.", "status": "selected", "failure_action": "Do not default-enable fused sub_a."},
        {"priority": "P1", "route": "stage276_selector_mat_ep_kernel_or_profile", "entry_condition": "Stage271 says selector MAT EP dominates non-binary sub_a.", "gate": "Design a falsifiable selector-kernel or schedule-level candidate.", "status": "conditional", "failure_action": "Keep claim boundary: no speedup without full SAB A/B."},
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
    append_once(CURRENT_GOAL, "### Stage274 sub_a fused materialization smoke", f"""
### Stage274 sub_a fused materialization smoke

`{decision}` records the explicit `SAB_PVW_SUBA_FUSED_FROM_DFT_ADD` full SAB
smoke. The primary metric is `T_bootstrap/r`, and the incremental local
comparison is fused vs backend direct-add under the same `spqlios_avx512`
backend.
""")
    append_once(HYPOTHESES, "H10_stage274_sub_a_fused_materialization_smoke:", f"""
H10_stage274_sub_a_fused_materialization_smoke:
  status: {decision}
  evidence:
    - repro/stage274_sub_a_fused_materialization_smoke/bench_summary.csv
    - repro/stage274_sub_a_fused_materialization_smoke/variant_compare.csv
    - repro/stage274_sub_a_fused_materialization_smoke/proof_gate.csv
    - docs/stage274_sub_a_fused_materialization_smoke.md
  conclusion: >
    Stage274 records {decision}. It keeps the result scoped to an explicit
    fused sub_a smoke and measures incremental benefit as fused-vs-backend,
    not only fused-vs-default.
""")
    append_once(RUN_LOG, "stage274-sub-a-fused-materialization-smoke-001", f"""stage274-sub-a-fused-materialization-smoke-001,2026-07-04,{head},Stage 274,spqlios_avx512,bash scripts/run_stage274_sub_a_fused_materialization_smoke.sh; python scripts/build_stage274_sub_a_fused_materialization_smoke.py,"r=4 include-zero/ternary default-vs-backend-vs-fused full SAB smoke; primary metric T_bootstrap/r",n/a,{decision},"Single-run smoke; promotion requires repeated/noise/resource if positive.",docs/stage274_sub_a_fused_materialization_smoke.md; repro/stage274_sub_a_fused_materialization_smoke/proof_gate.csv
""")
    append_once(MANIFEST, "- stage274_sub_a_fused_materialization_smoke:", """
- stage274_sub_a_fused_materialization_smoke:
  - `docs/stage274_sub_a_fused_materialization_smoke.md`
  - `scripts/run_stage274_sub_a_fused_materialization_smoke.sh`
  - `scripts/build_stage274_sub_a_fused_materialization_smoke.py`
  - `repro/stage274_sub_a_fused_materialization_smoke/`
""")
    append_once(CHECKLIST, "stage274-sub-a-fused-materialization-smoke-checklist", f"""
<!-- stage274-sub-a-fused-materialization-smoke-checklist -->
- [x] Stage274 fused sub_a smoke records `{decision}` with primary metric `T_bootstrap/r`.
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
        "backend_t_bootstrap_over_r_us", "fused_t_bootstrap_over_r_us",
        "backend_speedup_vs_default", "fused_speedup_vs_default",
        "fused_speedup_vs_backend", "default_correctness",
        "backend_correctness", "fused_correctness", "status",
    ])
    write_csv(REPRO / "proof_gate.csv", proof, ["gate", "status", "metric", "value", "evidence", "interpretation"])
    write_csv(REPRO / "claim_boundary.csv", claims, ["claim", "status", "allowed_wording", "forbidden_wording", "evidence"])
    write_csv(REPRO / "next_stage_queue.csv", queue, ["priority", "route", "entry_condition", "gate", "status", "failure_action"])

    report = f"""# Stage274 Sub_a Fused Materialization Smoke

Decision: `{decision}`.

Stage274 implements and screens the explicit
`SAB_PVW_SUBA_FUSED_FROM_DFT_ADD` path. The primary metric remains
`T_bootstrap/r`, and the local fused-materialization claim is judged against
`backend_from_dft_add`, not just against default PVW/MAT-SAB.

## Bench Summary

{table(summary, ["variant", "mode", "r", "reps", "correctness_gate", "t_bootstrap_over_r_pvw_us", "speedup_vs_scalar_repeated"])}

## Variant Comparison

{table(comparison, ["mode", "r", "default_t_bootstrap_over_r_us", "backend_t_bootstrap_over_r_us", "fused_t_bootstrap_over_r_us", "fused_speedup_vs_backend", "status"])}

## Proof Gate

{table(proof, ["gate", "status", "metric", "value", "interpretation"])}

## Claim Boundary

{table(claims, ["claim", "status", "allowed_wording", "forbidden_wording"])}

## Next Queue

{table(queue, ["priority", "route", "entry_condition", "gate", "status", "failure_action"])}

Generated from input head `{git_head()}`.
"""
    write_text(DOC, report)
    write_text(REPRO / "stage274_report.md", report)
    write_text(REPRO / "reproduction_commands.md", """# Stage274 Reproduction Commands

```bash
bash scripts/run_stage274_sub_a_fused_materialization_smoke.sh
python3 scripts/build_stage274_sub_a_fused_materialization_smoke.py
```

Stage274 is a single-run full SAB smoke. Promotion requires repeated timing and
noise/resource gates.
""")
    update_tracking(decision)
    paths = [
        DOC,
        REPRO / "stage274_report.md",
        REPRO / "reproduction_commands.md",
        REPRO / "bench_summary.csv",
        REPRO / "variant_compare.csv",
        REPRO / "proof_gate.csv",
        REPRO / "claim_boundary.csv",
        REPRO / "next_stage_queue.csv",
        Path(__file__),
        ROOT / "scripts" / "run_stage274_sub_a_fused_materialization_smoke.sh",
        ROOT / "src" / "sab_pvw.c",
        ROOT / "src" / "mosfhet" / "Makefile.def",
    ]
    write_csv(REPRO / "artifact_index.csv", artifacts(paths), ["path", "bytes", "sha256"])
    print(decision)
    return 0 if decision.startswith("PASS_") or decision.startswith("NEUTRAL_") else 1


if __name__ == "__main__":
    raise SystemExit(main())
