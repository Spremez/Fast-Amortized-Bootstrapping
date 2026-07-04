#!/usr/bin/env python3
"""Build Stage268 smoke artifacts for the non-binary backend FromDFT-add gate."""

from __future__ import annotations

import csv
import hashlib
import re
import subprocess
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
REPRO = ROOT / "repro" / "stage268_nonbinary_backend_from_dft_add_smoke"
RAW = REPRO / "raw"
DOC = ROOT / "docs" / "stage268_nonbinary_backend_from_dft_add_smoke.md"
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


def parse_logs() -> list[dict[str, str]]:
    rows: list[dict[str, str]] = []
    for path in sorted(RAW.glob("*_run.log")):
        name = path.name
        if name.startswith("default_"):
            variant = "default"
            mode = name.removeprefix("default_").removesuffix("_r4_reps1_run.log")
        elif name.startswith("backend_from_dft_add_"):
            variant = "backend_from_dft_add"
            mode = name.removeprefix("backend_from_dft_add_").removesuffix("_r4_reps1_run.log")
        else:
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
                "default_t_bootstrap_over_r_us": f"{base_us:.3f}",
                "backend_t_bootstrap_over_r_us": f"{cand_us:.3f}",
                "backend_speedup_vs_default": f"{speedup:.6f}",
                "backend_delta_pct": f"{delta:.3f}",
                "default_correctness": base["correctness_gate"],
                "backend_correctness": cand["correctness_gate"],
                "status": "positive" if speedup >= 1.01 else "neutral_or_negative",
            }
        )
    return out


def decision_from(summary: list[dict[str, str]], comparison: list[dict[str, str]]) -> str:
    expected = {
        ("default", "include_zero"),
        ("default", "ternary"),
        ("backend_from_dft_add", "include_zero"),
        ("backend_from_dft_add", "ternary"),
    }
    covered = {(row["variant"], row["mode"]) for row in summary}
    if not expected.issubset(covered):
        return "FAIL_STAGE268_BACKEND_FROM_DFT_ADD_SMOKE_MISSING_COVERAGE"
    if any(row["correctness_gate"] != "Pass" for row in summary):
        return "FAIL_STAGE268_BACKEND_FROM_DFT_ADD_SMOKE_CORRECTNESS"
    if all(row.get("status") == "positive" for row in comparison):
        return "PASS_STAGE268_BACKEND_FROM_DFT_ADD_SMOKE_POSITIVE_REPEAT_REQUIRED"
    return "NEUTRAL_STAGE268_BACKEND_FROM_DFT_ADD_SMOKE_NO_PROMOTION"


def proof_rows(summary: list[dict[str, str]], comparison: list[dict[str, str]], decision: str) -> list[dict[str, str]]:
    covered = ",".join(f"{row['variant']}:{row['mode']}" for row in summary)
    min_speedup = min((float(row.get("backend_speedup_vs_default", "0") or "0") for row in comparison), default=0.0)
    return [
        {"gate": "G1_coverage", "status": "PASS" if len(summary) == 4 else "FAIL", "metric": "variant/mode coverage", "value": covered, "evidence": "bench_summary.csv", "interpretation": "Covers default and backend FromDFT-add for r=4 include-zero and ternary."},
        {"gate": "G2_correctness", "status": "PASS" if all(row["correctness_gate"] == "Pass" for row in summary) else "FAIL", "metric": "PVW/scalar target correctness", "value": f"{sum(row['correctness_gate'] == 'Pass' for row in summary)}/{len(summary)}", "evidence": "bench_summary.csv", "interpretation": "Correctness must pass before interpreting timing."},
        {"gate": "G3_primary_metric", "status": "PASS", "metric": "T_bootstrap/r", "value": "backend_vs_default_same_backend", "evidence": "variant_compare.csv", "interpretation": "Smoke compares PVW/MAT variants on the requested amortized per-body metric."},
        {"gate": "G4_smoke_threshold", "status": "PASS" if min_speedup >= 1.01 else "NEUTRAL", "metric": "minimum backend speedup vs default", "value": f"{min_speedup:.6f}x", "evidence": "variant_compare.csv", "interpretation": "Single-run smoke requires both modes above 1.01x before repeated/noise/resource promotion."},
        {"gate": "G5_claim_boundary", "status": "PASS_SMOKE_ONLY", "metric": "no final speedup claim", "value": "single_run", "evidence": "claim_boundary.csv", "interpretation": "Stage268 is a screening gate, not final evidence."},
        {"gate": "G6_decision", "status": decision, "metric": "stage decision", "value": decision, "evidence": "proof_gate.csv", "interpretation": "Promotion requires a positive smoke; neutral results close this local materialization candidate."},
    ]


def claim_rows(decision: str) -> list[dict[str, str]]:
    return [
        {"claim": "backend_from_dft_add_smoke", "status": "smoke_positive" if decision.startswith("PASS_") else "neutral_or_failed", "allowed_wording": "Stage268 screens the existing explicit backend FromDFT-add flag against default PVW/MAT-SAB using T_bootstrap/r.", "forbidden_wording": "Stage268 proves final complete SAB speedup.", "evidence": "variant_compare.csv; proof_gate.csv"},
        {"claim": "algorithm_speedup_vs_scalar_sab", "status": "not_remeasured_here", "allowed_wording": "Scalar-repeated numbers in each row remain context; the Stage268 primary comparison is backend PVW/MAT vs default PVW/MAT.", "forbidden_wording": "Mix backend flag deltas with historical scalar-repeated speedup as one claim.", "evidence": "bench_summary.csv"},
        {"claim": "hot_path_change", "status": "no_new_hot_path_code", "allowed_wording": "Stage268 uses an existing explicit flag only.", "forbidden_wording": "Stage268 introduced a new SAB/MAT algorithm.", "evidence": "scripts/run_stage268_nonbinary_backend_from_dft_add_smoke.sh"},
    ]


def next_rows(decision: str) -> list[dict[str, str]]:
    if decision.startswith("PASS_"):
        return [
            {"priority": "P0", "route": "stage269_backend_from_dft_add_repeated_noise_resource", "entry_condition": "Stage268 positive smoke for both non-binary modes.", "gate": "repeated T_bootstrap/r, noise/resource, same backend.", "status": "selected", "failure_action": "If repeated rows lose benefit, demote Stage268 to smoke-only."},
            {"priority": "P1", "route": "stage270_counter_attribution", "entry_condition": "Repeated rows positive.", "gate": "native counters or proxy-labeled assembly audit.", "status": "conditional", "failure_action": "No hardware claim without counters."},
        ]
    return [
        {"priority": "P0", "route": "stage269_materialization_neutral_closeout", "entry_condition": "Stage268 neutral or negative smoke.", "gate": "record neutral result and do not promote backend FromDFT-add.", "status": "selected", "failure_action": "Do not reopen this flag without a new mechanism or changed profile."},
        {"priority": "P1", "route": "stage270_nonbinary_sub_a_or_native_counter", "entry_condition": "Materialization flag not promoted.", "gate": "choose sub_a isolated gate or native counter rerun depending on available platform.", "status": "conditional", "failure_action": "No new hot-path code before an isolated gate."},
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
    append_once(CURRENT_GOAL, "### Stage268 backend FromDFT-add smoke", f"""
### Stage268 backend FromDFT-add smoke

`{decision}` records the r=4 include-zero/ternary smoke for the existing
`SAB_PVW_BACKEND_FROM_DFT_ADD` flag. The primary metric is `T_bootstrap/r`.
This stage is a screening gate and does not by itself create a final SAB
speedup claim.
""")
    append_once(HYPOTHESES, "H10_stage268_backend_from_dft_add_smoke:", f"""
H10_stage268_backend_from_dft_add_smoke:
  status: {decision}
  evidence:
    - repro/stage268_nonbinary_backend_from_dft_add_smoke/bench_summary.csv
    - repro/stage268_nonbinary_backend_from_dft_add_smoke/variant_compare.csv
    - repro/stage268_nonbinary_backend_from_dft_add_smoke/proof_gate.csv
    - docs/stage268_nonbinary_backend_from_dft_add_smoke.md
  conclusion: >
    Stage268 records {decision}. It compares the existing explicit backend
    FromDFT-add route to default PVW/MAT-SAB on the requested amortized
    `T_bootstrap/r` metric for r=4 include-zero and ternary. Promotion depends
    on the smoke threshold and later repeated/noise/resource gates.
""")
    append_once(RUN_LOG, "stage268-backend-from-dft-add-smoke-001", f"""stage268-backend-from-dft-add-smoke-001,2026-07-04,{head},Stage 268,spqlios_avx512,python scripts/build_stage268_nonbinary_backend_from_dft_add_smoke.py,"r=4 include-zero/ternary default-vs-backend FromDFT-add smoke; primary metric T_bootstrap/r",n/a,{decision},"Single-run smoke; promotion requires repeated/noise/resource if positive.",docs/stage268_nonbinary_backend_from_dft_add_smoke.md; repro/stage268_nonbinary_backend_from_dft_add_smoke/proof_gate.csv
""")
    append_once(MANIFEST, "- stage268_nonbinary_backend_from_dft_add_smoke:", """
- stage268_nonbinary_backend_from_dft_add_smoke:
  - `docs/stage268_nonbinary_backend_from_dft_add_smoke.md`
  - `scripts/run_stage268_nonbinary_backend_from_dft_add_smoke.sh`
  - `scripts/build_stage268_nonbinary_backend_from_dft_add_smoke.py`
  - `repro/stage268_nonbinary_backend_from_dft_add_smoke/`
""")
    append_once(CHECKLIST, "stage268-backend-from-dft-add-smoke-checklist", f"""
<!-- stage268-backend-from-dft-add-smoke-checklist -->
- [x] Stage268 backend FromDFT-add smoke records `{decision}` with primary metric `T_bootstrap/r`.
""")


def main() -> int:
    REPRO.mkdir(parents=True, exist_ok=True)
    summary = parse_logs()
    comparison = compare_rows(summary)
    decision = decision_from(summary, comparison)
    proof = proof_rows(summary, comparison, decision)
    claims = claim_rows(decision)
    queue = next_rows(decision)

    write_csv(REPRO / "bench_summary.csv", summary, [
        "platform", "backend", "param", "variant", "mode", "r", "reps", "h", "r_prec",
        "correctness_gate", "pvw_avg_us", "pvw_stddev_us", "pvw_lane_avg_us",
        "scalar_repeated_avg_us", "scalar_stddev_us", "scalar_lane_avg_us",
        "speedup_vs_scalar_repeated", "speedup_stddev", "t_bootstrap_over_r_pvw_us",
        "t_bootstrap_over_r_scalar_us", "primary_metric", "avx_variant", "log",
    ])
    write_csv(REPRO / "variant_compare.csv", comparison, [
        "mode", "r", "default_t_bootstrap_over_r_us", "backend_t_bootstrap_over_r_us",
        "backend_speedup_vs_default", "backend_delta_pct", "default_correctness",
        "backend_correctness", "status",
    ])
    write_csv(REPRO / "proof_gate.csv", proof, ["gate", "status", "metric", "value", "evidence", "interpretation"])
    write_csv(REPRO / "claim_boundary.csv", claims, ["claim", "status", "allowed_wording", "forbidden_wording", "evidence"])
    write_csv(REPRO / "next_stage_queue.csv", queue, ["priority", "route", "entry_condition", "gate", "status", "failure_action"])

    report = f"""# Stage268 Non-Binary Backend FromDFT-add Smoke

Decision: `{decision}`.

Stage268 is the bounded screening gate selected by Stage267. It compares the
existing explicit `SAB_PVW_BACKEND_FROM_DFT_ADD=true` route against default
PVW/MAT-SAB for r=4 include-zero and ternary. The primary metric is the
amortized per-body metric requested for MAT-RLWE:

```text
T_bootstrap / r
```

## Variant Comparison

{table(comparison, ["mode", "r", "default_t_bootstrap_over_r_us", "backend_t_bootstrap_over_r_us", "backend_speedup_vs_default", "backend_delta_pct", "status"])}

## Bench Summary

{table(summary, ["variant", "mode", "r", "reps", "correctness_gate", "t_bootstrap_over_r_pvw_us", "speedup_vs_scalar_repeated", "log"])}

## Proof Gate

{table(proof, ["gate", "status", "metric", "value", "interpretation"])}

## Claim Boundary

{table(claims, ["claim", "status", "allowed_wording", "forbidden_wording"])}

## Next Queue

{table(queue, ["priority", "route", "entry_condition", "gate", "status", "failure_action"])}

Generated from input head `{git_head()}`.
"""
    write_text(DOC, report)
    write_text(REPRO / "stage268_report.md", report)
    write_text(REPRO / "reproduction_commands.md", """# Stage268 Reproduction Commands

Run on WSL2/Linux or native Linux with AVX512 exposed:

```bash
bash scripts/run_stage268_nonbinary_backend_from_dft_add_smoke.sh
python3 scripts/build_stage268_nonbinary_backend_from_dft_add_smoke.py
```

Stage268 is single-run smoke only. It must not be cited as final performance
evidence without a later repeated/noise/resource gate.
""")
    update_tracking(decision)
    paths = [
        DOC,
        REPRO / "stage268_report.md",
        REPRO / "reproduction_commands.md",
        REPRO / "bench_summary.csv",
        REPRO / "variant_compare.csv",
        REPRO / "proof_gate.csv",
        REPRO / "claim_boundary.csv",
        REPRO / "next_stage_queue.csv",
        ROOT / "scripts" / "run_stage268_nonbinary_backend_from_dft_add_smoke.sh",
        Path(__file__),
    ]
    write_csv(REPRO / "artifact_index.csv", artifacts(paths), ["path", "bytes", "sha256"])
    print(decision)
    return 1 if decision.startswith("FAIL_") else 0


if __name__ == "__main__":
    raise SystemExit(main())
