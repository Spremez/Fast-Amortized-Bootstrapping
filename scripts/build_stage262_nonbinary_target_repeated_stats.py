#!/usr/bin/env python3
"""Build Stage262 repeated-stat repro artifacts for non-binary PVW/MAT-SAB."""

from __future__ import annotations

import csv
import re
import subprocess
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
REPRO = ROOT / "repro" / "stage262_nonbinary_target_repeated_stats"
RAW = REPRO / "raw"
DOC = ROOT / "docs" / "stage262_nonbinary_target_repeated_stats.md"

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


def git_head() -> str:
    try:
        return subprocess.check_output(
            ["git", "rev-parse", "--short", "HEAD"],
            cwd=ROOT,
            text=True,
            stderr=subprocess.DEVNULL,
        ).strip()
    except Exception:
        return "unknown"


def read_log(path: Path) -> str:
    return path.read_text(encoding="utf-8", errors="replace")


def write_csv(path: Path, rows: list[dict[str, str]], fields: list[str]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="\n", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields, lineterminator="\n")
        writer.writeheader()
        for row in rows:
            writer.writerow({field: row.get(field, "") for field in fields})


def write_text_lf(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="\n", encoding="utf-8") as handle:
        handle.write(text)


def markdown_table(rows: list[dict[str, str]], fields: list[str]) -> str:
    out = ["| " + " | ".join(fields) + " |"]
    out.append("| " + " | ".join("---" for _ in fields) + " |")
    for row in rows:
        out.append("| " + " | ".join(str(row.get(field, "")) for field in fields) + " |")
    return "\n".join(out)


def parse_logs() -> tuple[list[dict[str, str]], list[dict[str, str]]]:
    correctness: dict[tuple[str, str], dict[str, str]] = {}
    samples: list[dict[str, str]] = []
    summaries: list[dict[str, str]] = []

    for path in sorted(RAW.glob("wsl_spqlios_avx512_r*_reps3_run.log")):
        text = read_log(path)
        for match in CORRECTNESS_RE.finditer(text):
            row = match.groupdict()
            correctness[(row["mode"], row["r"])] = row
        for match in SAMPLE_RE.finditer(text):
            row = match.groupdict()
            row["platform"] = "WSL2/Linux"
            row["backend"] = "spqlios_avx512"
            row["param"] = "SET_2_3"
            row["log"] = str(path.relative_to(ROOT)).replace("\\", "/")
            samples.append(row)
        for match in SUMMARY_RE.finditer(text):
            row = match.groupdict()
            corr = correctness.get((row["mode"], row["r"]), {})
            row["correctness_gate"] = corr.get("gate", "MISSING")
            row["h"] = corr.get("h", "")
            row["r_prec"] = corr.get("r_prec", "")
            row["platform"] = "WSL2/Linux"
            row["backend"] = "spqlios_avx512"
            row["param"] = "SET_2_3"
            row["avx_variant"] = "MAT_TRGSW_AVX512_SMALLR_SPECIALIZED"
            row["log"] = str(path.relative_to(ROOT)).replace("\\", "/")
            summaries.append(row)

    samples.sort(key=lambda row: (int(row["r"]), row["mode"], int(row["rep"])))
    summaries.sort(key=lambda row: (int(row["r"]), row["mode"]))
    return samples, summaries


def main() -> None:
    REPRO.mkdir(parents=True, exist_ok=True)
    samples, summaries = parse_logs()
    if not samples or not summaries:
        raise SystemExit("no Stage262 rows found")

    sample_fields = [
        "platform",
        "backend",
        "param",
        "mode",
        "r",
        "rep",
        "pvw_us",
        "pvw_lane_us",
        "scalar_repeated_us",
        "scalar_lane_us",
        "speedup",
        "log",
    ]
    summary_fields = [
        "platform",
        "backend",
        "param",
        "mode",
        "r",
        "reps",
        "h",
        "r_prec",
        "correctness_gate",
        "pvw_avg_us",
        "pvw_stddev_us",
        "pvw_lane_avg_us",
        "scalar_repeated_avg_us",
        "scalar_stddev_us",
        "scalar_lane_avg_us",
        "speedup_vs_scalar_repeated",
        "speedup_stddev",
        "t_bootstrap_over_r_pvw_us",
        "t_bootstrap_over_r_scalar_us",
        "avx_variant",
        "log",
    ]
    write_csv(REPRO / "sample_rows.csv", samples, sample_fields)
    write_csv(REPRO / "bench_summary.csv", summaries, summary_fields)

    expected = {
        ("include_zero", "1"),
        ("ternary", "1"),
        ("include_zero", "2"),
        ("ternary", "2"),
        ("include_zero", "4"),
        ("ternary", "4"),
    }
    covered = {(row["mode"], row["r"]) for row in summaries}
    all_pass = all(row["correctness_gate"] == "Pass" for row in summaries)
    r1 = [row for row in summaries if row["r"] == "1"]
    target = [row for row in summaries if row["r"] in {"2", "4"}]
    r1_max_gap = max(abs(float(row["speedup_vs_scalar_repeated"]) - 1.0) for row in r1)
    target_min_speedup = min(float(row["speedup_vs_scalar_repeated"]) for row in target)
    target_max_speedup = max(float(row["speedup_vs_scalar_repeated"]) for row in target)
    max_speedup_stddev = max(float(row["speedup_stddev"]) for row in summaries)
    coverage_pass = expected.issubset(covered)
    negative_control_pass = r1_max_gap <= 0.05
    target_speed_pass = target_min_speedup > 1.20
    variability_pass = max_speedup_stddev <= 0.03
    decision = (
        "PASS_STAGE262_NONBINARY_TARGET_REPEATED_STATS"
        if all_pass and coverage_pass and negative_control_pass
        and target_speed_pass and variability_pass
        else "FAIL_STAGE262_NONBINARY_TARGET_REPEATED_STATS"
    )

    proof_rows = [
        {
            "gate": "G1_correctness",
            "status": "PASS" if all_pass else "FAIL",
            "metric": "target full PVW/scalar phase equivalence",
            "value": f"{sum(row['correctness_gate'] == 'Pass' for row in summaries)}/{len(summaries)}",
            "evidence": "bench_summary.csv",
            "interpretation": "Every repeated-stat row performs a correctness comparison before timing.",
        },
        {
            "gate": "G2_coverage",
            "status": "PASS" if coverage_pass else "FAIL",
            "metric": "mode/r coverage",
            "value": ",".join(f"{mode}:r{r}" for mode, r in sorted(covered)),
            "evidence": "bench_summary.csv",
            "interpretation": "Covers r=1/2/4 for include-zero and ternary.",
        },
        {
            "gate": "G3_negative_control",
            "status": "PASS" if negative_control_pass else "FAIL",
            "metric": "max abs(r=1 speedup - 1)",
            "value": f"{r1_max_gap:.3f}",
            "evidence": "bench_summary.csv",
            "interpretation": "r=1 remains near parity, supporting the lane-amortization interpretation.",
        },
        {
            "gate": "G4_target_speed",
            "status": "PASS" if target_speed_pass else "FAIL",
            "metric": "r=2/4 speedup range",
            "value": f"{target_min_speedup:.3f}x..{target_max_speedup:.3f}x",
            "evidence": "bench_summary.csv",
            "interpretation": "Repeated WSL same-backend target rows retain amortized speedup.",
        },
        {
            "gate": "G5_variability",
            "status": "PASS" if variability_pass else "FAIL",
            "metric": "max speedup stddev",
            "value": f"{max_speedup_stddev:.3f}",
            "evidence": "bench_summary.csv; sample_rows.csv",
            "interpretation": "Three-repetition rows show low local variation; still not native paper-grade evidence.",
        },
        {
            "gate": "G6_decision",
            "status": decision,
            "metric": "stage decision",
            "value": decision,
            "evidence": "proof_gate.csv",
            "interpretation": "Proceed to profile attribution and MAT AVX512 limit analysis.",
        },
    ]
    write_csv(REPRO / "proof_gate.csv", proof_rows, ["gate", "status", "metric", "value", "evidence", "interpretation"])

    claim_rows = [
        {
            "claim": "target_repeated_t_bootstrap_over_r",
            "status": "supported_wsl_repeated",
            "allowed_wording": f"On WSL2/Linux spqlios_avx512, repeated target measurements show r=2/4 non-binary PVW/MAT-SAB T_bootstrap/r speedup of {target_min_speedup:.3f}x-{target_max_speedup:.3f}x.",
            "forbidden_wording": "This is the final native Linux or paper-grade performance claim.",
            "evidence": "bench_summary.csv; sample_rows.csv",
        },
        {
            "claim": "lane_amortization_interpretation",
            "status": "supported_by_negative_control",
            "allowed_wording": f"r=1 stays within {r1_max_gap:.3f} of parity, while r=2/4 shows stable speedup, supporting the multi-body amortization interpretation.",
            "forbidden_wording": "The MAT path is intrinsically faster for a single scalar body.",
            "evidence": "bench_summary.csv",
        },
        {
            "claim": "mat_avx512_theoretical_optimum",
            "status": "unsupported",
            "allowed_wording": "Stage262 measures the current small-r AVX512 implementation in full SAB.",
            "forbidden_wording": "Stage262 proves the AVX512 MAT kernel is at its theoretical optimum.",
            "evidence": "no perf-counter or assembly audit in Stage262",
        },
    ]
    write_csv(REPRO / "claim_boundary.csv", claim_rows, ["claim", "status", "allowed_wording", "forbidden_wording", "evidence"])

    commands = """# Stage262 Reproduction Commands

All rows use `FFT_LIB=spqlios_avx512 KEY=BINARY PARAM=SET_2_3
MAT_TRGSW_AVX512_SMALLR_SPECIALIZED=true SAB_PVW_NONBINARY_BENCH=true
SAB_PVW_NONBINARY_BENCH_REPS=3`.

Run each `r in {1,2,4}` twice:

```bash
make clean
make FFT_LIB=spqlios_avx512 KEY=BINARY PARAM=SET_2_3 \\
  SAB_PVW_NONBINARY_BENCH=true \\
  SAB_PVW_NONBINARY_BENCH_R=<1|2|4> \\
  SAB_PVW_NONBINARY_BENCH_REPS=3 \\
  SAB_PVW_NONBINARY_BENCH_INCLUDE_ZERO=true \\
  SAB_PVW_NONBINARY_BENCH_TERNARY=false \\
  MAT_TRGSW_AVX512_SMALLR_SPECIALIZED=true
./main
```

Then rerun with `SAB_PVW_NONBINARY_BENCH_INCLUDE_ZERO=false` and
`SAB_PVW_NONBINARY_BENCH_TERNARY=true`.

```bash
python3 scripts/build_stage262_nonbinary_target_repeated_stats.py
```
"""
    write_text_lf(REPRO / "reproduction_commands.md", commands)

    report = f"""# Stage262 Non-Binary Target Repeated Stats

Decision: `{decision}`.

Stage262 repeats the Stage261 target benchmark with `reps=3` and adds r=1 as a
negative control. The metric remains:

```text
T_bootstrap / r
```

The comparison is still complete SAB PVW/MAT with r output bodies against r
repeated scalar SAB bootstraps on the same backend.

## Summary

{markdown_table(summaries, ["mode", "r", "reps", "correctness_gate", "t_bootstrap_over_r_pvw_us", "t_bootstrap_over_r_scalar_us", "speedup_vs_scalar_repeated", "speedup_stddev"])}

## Interpretation

The r=1 rows remain near parity: maximum absolute distance from 1.0 speedup is
`{r1_max_gap:.3f}`. The r=2/r=4 rows retain stable same-backend amortized
speedup of `{target_min_speedup:.3f}x-{target_max_speedup:.3f}x` with maximum
reported speedup standard deviation `{max_speedup_stddev:.3f}`.

This supports the intended interpretation: PVW/MAT-SAB is improving amortized
time per output body/lane, not single-body latency. It is still WSL2 evidence;
the next research gate must attribute the speedup with native Linux profiling
and MAT AVX512 memory/FMA counters.

## Proof Gate

{markdown_table(proof_rows, ["gate", "status", "metric", "value", "interpretation"])}

## Claim Boundary

{markdown_table(claim_rows, ["claim", "status", "allowed_wording", "forbidden_wording"])}

Generated from input head `{git_head()}`.
"""
    write_text_lf(REPRO / "stage262_report.md", report)
    write_text_lf(DOC, report)

    artifact_rows = []
    for path in sorted(REPRO.glob("*")) + sorted(RAW.glob("*")):
        if path.is_file():
            artifact_rows.append({"path": str(path.relative_to(ROOT)).replace("\\", "/"), "bytes": str(path.stat().st_size)})
    artifact_rows.append({"path": str(DOC.relative_to(ROOT)).replace("\\", "/"), "bytes": str(DOC.stat().st_size)})
    write_csv(REPRO / "artifact_index.csv", artifact_rows, ["path", "bytes"])

    print(decision)


if __name__ == "__main__":
    main()
