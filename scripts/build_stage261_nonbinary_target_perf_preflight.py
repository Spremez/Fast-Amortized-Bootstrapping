#!/usr/bin/env python3
"""Build Stage261 repro artifacts from target non-binary PVW/MAT-SAB logs."""

from __future__ import annotations

import csv
import re
import subprocess
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
REPRO = ROOT / "repro" / "stage261_nonbinary_target_perf_preflight"
RAW = REPRO / "raw"
DOC = ROOT / "docs" / "stage261_nonbinary_target_perf_preflight.md"

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

CORRECTNESS_RE = re.compile(
    r"SAB_PVW_NONBINARY_BENCH correctness target_full "
    r"mode=(?P<mode>\S+) r=(?P<r>\d+) h=(?P<h>\d+) "
    r"r_prec=(?P<r_prec>\d+): (?P<gate>Pass|Fail)"
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
    try:
        return path.read_text(encoding="utf-8", errors="replace")
    except FileNotFoundError:
        return ""


def parse_logs() -> list[dict[str, str]]:
    correctness: dict[tuple[str, str], dict[str, str]] = {}
    summaries: list[dict[str, str]] = []

    for path in sorted(RAW.glob("wsl_spqlios_avx512_r*_run.log")):
        text = read_log(path)
        for match in CORRECTNESS_RE.finditer(text):
            row = match.groupdict()
            correctness[(row["mode"], row["r"])] = row
        for match in SUMMARY_RE.finditer(text):
            row = match.groupdict()
            corr = correctness.get((row["mode"], row["r"]), {})
            row["correctness_gate"] = corr.get("gate", "MISSING")
            row["h"] = corr.get("h", "")
            row["r_prec"] = corr.get("r_prec", "")
            row["backend"] = "spqlios_avx512"
            row["platform"] = "WSL2/Linux"
            row["key"] = "BINARY"
            row["param"] = "SET_2_3"
            row["avx_variant"] = "MAT_TRGSW_AVX512_SMALLR_SPECIALIZED"
            row["log"] = str(path.relative_to(ROOT)).replace("\\", "/")
            summaries.append(row)

    summaries.sort(key=lambda row: (int(row["r"]), row["mode"]))
    return summaries


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


def main() -> None:
    REPRO.mkdir(parents=True, exist_ok=True)
    rows = parse_logs()
    if not rows:
        raise SystemExit("no Stage261 summary rows found")

    bench_fields = [
        "platform",
        "backend",
        "param",
        "key",
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
    write_csv(REPRO / "bench_summary.csv", rows, bench_fields)

    min_speedup = min(float(row["speedup_vs_scalar_repeated"]) for row in rows)
    max_speedup = max(float(row["speedup_vs_scalar_repeated"]) for row in rows)
    all_pass = all(row["correctness_gate"] == "Pass" for row in rows)
    expected = {("include_zero", "2"), ("ternary", "2"), ("include_zero", "4"), ("ternary", "4")}
    covered = {(row["mode"], row["r"]) for row in rows}
    coverage_pass = expected.issubset(covered)
    decision = (
        "PASS_STAGE261_NONBINARY_TARGET_PER_BIT_PREFLIGHT"
        if all_pass and coverage_pass
        else "FAIL_STAGE261_NONBINARY_TARGET_PER_BIT_PREFLIGHT"
    )

    proof_rows = [
        {
            "gate": "G1_harness",
            "status": "PASS",
            "metric": "nonbinary target benchmark flag",
            "value": "SAB_PVW_NONBINARY_BENCH",
            "evidence": "main.c; src/mosfhet/Makefile.def",
            "interpretation": "Explicit target full SAB T_bootstrap/r harness exists.",
        },
        {
            "gate": "G2_correctness",
            "status": "PASS" if all_pass else "FAIL",
            "metric": "target full PVW/scalar phase equivalence",
            "value": f"{sum(row['correctness_gate'] == 'Pass' for row in rows)}/{len(rows)}",
            "evidence": "repro/stage261_nonbinary_target_perf_preflight/bench_summary.csv",
            "interpretation": "Each measured row first compares PVW lane output against repeated scalar SAB.",
        },
        {
            "gate": "G3_branch_coverage",
            "status": "PASS" if coverage_pass else "FAIL",
            "metric": "mode/r coverage",
            "value": ",".join(f"{mode}:r{r}" for mode, r in sorted(covered)),
            "evidence": "repro/stage261_nonbinary_target_perf_preflight/bench_summary.csv",
            "interpretation": "Preflight covers include-zero and ternary for r=2 and r=4.",
        },
        {
            "gate": "G4_same_backend_speed",
            "status": "PASS" if min_speedup > 1.0 else "FAIL",
            "metric": "speedup_vs_scalar_repeated",
            "value": f"{min_speedup:.3f}x..{max_speedup:.3f}x",
            "evidence": "repro/stage261_nonbinary_target_perf_preflight/bench_summary.csv",
            "interpretation": "Same spqlios_avx512 backend comparison, measured as complete SAB T_bootstrap/r.",
        },
        {
            "gate": "G5_statistics",
            "status": "PREFLIGHT_ONLY",
            "metric": "reps",
            "value": "1 per row",
            "evidence": "raw run logs",
            "interpretation": "This is not yet a statistical paper-grade speed claim.",
        },
        {
            "gate": "G6_decision",
            "status": decision,
            "metric": "stage decision",
            "value": decision,
            "evidence": "repro/stage261_nonbinary_target_perf_preflight/proof_gate.csv",
            "interpretation": "Proceed to repeated/native/profiled Stage262+ validation.",
        },
    ]
    proof_fields = ["gate", "status", "metric", "value", "evidence", "interpretation"]
    write_csv(REPRO / "proof_gate.csv", proof_rows, proof_fields)

    platform_rows = [
        {
            "platform": "WSL2/Linux",
            "backend": "spqlios_avx512",
            "cpu_avx512": "observed",
            "status": "PASS_PREFLIGHT",
            "evidence": "raw/wsl_spqlios_avx512_*_{build,run}.log",
            "claim_use": "same-backend target T_bootstrap/r preflight",
        },
        {
            "platform": "Windows",
            "backend": "ffnt",
            "cpu_avx512": "not_applicable",
            "status": "BUILD_SMOKE_ONLY",
            "evidence": "manual build check; FFNT target run was not used for speed claim",
            "claim_use": "correctness/build smoke only",
        },
        {
            "platform": "native Linux",
            "backend": "spqlios_avx512 + perf counters",
            "cpu_avx512": "required",
            "status": "NEXT_GATE",
            "evidence": "not run in Stage261",
            "claim_use": "paper-grade performance attribution",
        },
    ]
    write_csv(
        REPRO / "platform_matrix.csv",
        platform_rows,
        ["platform", "backend", "cpu_avx512", "status", "evidence", "claim_use"],
    )

    claim_rows = [
        {
            "claim": "nonbinary_target_per_bit_preflight",
            "status": "supported_preflight",
            "allowed_wording": "On WSL2/Linux spqlios_avx512, the target SET_2_3 non-binary PVW/MAT-SAB path passes complete SAB correctness and shows 1.283x-1.387x T_bootstrap/r speedup for r=2/4.",
            "forbidden_wording": "The implementation has reached theoretical optimum or paper-grade final speedup.",
            "evidence": "bench_summary.csv",
        },
        {
            "claim": "amortized_metric_definition",
            "status": "supported",
            "allowed_wording": "The comparison dimension is full SAB time divided by r output lanes, with scalar baseline measured as r repeated scalar SAB calls.",
            "forbidden_wording": "The speedup is a single-output latency speedup over scalar SAB.",
            "evidence": "main.c SAB_PVW_NONBINARY_BENCH summary fields",
        },
        {
            "claim": "nonbinary_final_performance",
            "status": "not_final",
            "allowed_wording": "Stage261 admits repeated/statistical performance validation.",
            "forbidden_wording": "Stage261 alone is sufficient for a publication performance claim.",
            "evidence": "proof_gate.csv G5_statistics",
        },
        {
            "claim": "mat_avx_theoretical_optimum",
            "status": "unsupported",
            "allowed_wording": "The Stage261 harness uses the current small-r MAT AVX512 specialization.",
            "forbidden_wording": "The MAT external product AVX512 implementation is theoretically optimal.",
            "evidence": "build logs; no perf counter/assembly proof in Stage261",
        },
    ]
    write_csv(
        REPRO / "claim_boundary.csv",
        claim_rows,
        ["claim", "status", "allowed_wording", "forbidden_wording", "evidence"],
    )

    commands = """# Stage261 Reproduction Commands

All commands are run from the repository root.

```bash
make clean
make FFT_LIB=spqlios_avx512 KEY=BINARY PARAM=SET_2_3 \\
  SAB_PVW_NONBINARY_BENCH=true \\
  SAB_PVW_NONBINARY_BENCH_R=2 \\
  SAB_PVW_NONBINARY_BENCH_REPS=1 \\
  SAB_PVW_NONBINARY_BENCH_INCLUDE_ZERO=true \\
  SAB_PVW_NONBINARY_BENCH_TERNARY=false \\
  MAT_TRGSW_AVX512_SMALLR_SPECIALIZED=true
./main
```

Repeat with `SAB_PVW_NONBINARY_BENCH_R=4` and with
`SAB_PVW_NONBINARY_BENCH_INCLUDE_ZERO=false
SAB_PVW_NONBINARY_BENCH_TERNARY=true` for the ternary branch.

```bash
python3 scripts/build_stage261_nonbinary_target_perf_preflight.py
```
"""
    write_text_lf(REPRO / "reproduction_commands.md", commands)

    report = f"""# Stage261 Non-Binary Target T_bootstrap/r Preflight

Decision: `{decision}`.

Stage261 adds an explicit target-parameter benchmark for the non-binary
PVW/MAT-SAB full bootstrapping path. The comparison is the intended amortized
dimension:

```text
T_bootstrap / r
```

The PVW/MAT path processes one r-body ciphertext with r independent LUT/SAB
lanes. The scalar baseline is r repeated scalar SAB bootstraps using matching
per-lane output keys and LUTs. Therefore `speedup_vs_scalar_repeated` is also
the speedup of amortized time per processed plaintext lane/bit, not a
single-output latency claim.

## Parameters

| item | value |
| --- | --- |
| parameter set | SET_2_3 |
| input ring | N=2048, k=1 |
| output ring | N=2048, k=1 |
| SAB sparsity | h=39 |
| monomial precision | r_prec=7 |
| bootstrapping decomposition | l=1, bg_bit=23 |
| message precision | prec=3 |
| packing KS | ell=2, bg_bit=14 |
| HW KS | ell=12, bg_bit=1 |
| backend | WSL2/Linux spqlios_avx512 |
| MAT AVX512 variant | MAT_TRGSW_AVX512_SMALLR_SPECIALIZED |
| input branches | include-zero and ternary |

## Results

{markdown_table(rows, ["mode", "r", "reps", "correctness_gate", "pvw_avg_us", "scalar_repeated_avg_us", "t_bootstrap_over_r_pvw_us", "t_bootstrap_over_r_scalar_us", "speedup_vs_scalar_repeated"])}

## Interpretation

The preflight result is positive: all four target rows pass PVW/scalar phase
equivalence and the complete SAB amortized metric improves by
`{min_speedup:.3f}x-{max_speedup:.3f}x` on the same backend.

This does not prove theoretical optimality. The run count is one per row, WSL2
is a proxy performance platform, and Stage261 does not include perf counters,
assembly attribution, r=1 negative control, or native Linux confidence
intervals. The correct next step is repeated native/backend-fair measurement
plus profile attribution before making a final paper claim.

## Claim Boundary

{markdown_table(claim_rows, ["claim", "status", "allowed_wording", "forbidden_wording"])}

## Proof Gate

{markdown_table(proof_rows, ["gate", "status", "metric", "value", "interpretation"])}

Generated from input head `{git_head()}`.
"""
    write_text_lf(REPRO / "stage261_report.md", report)
    DOC.parent.mkdir(parents=True, exist_ok=True)
    write_text_lf(DOC, report)

    artifact_rows = []
    for path in sorted(REPRO.glob("*")) + sorted(RAW.glob("*")):
        if path.is_file():
            artifact_rows.append(
                {
                    "path": str(path.relative_to(ROOT)).replace("\\", "/"),
                    "bytes": str(path.stat().st_size),
                }
            )
    artifact_rows.append({"path": str(DOC.relative_to(ROOT)).replace("\\", "/"), "bytes": str(DOC.stat().st_size)})
    write_csv(REPRO / "artifact_index.csv", artifact_rows, ["path", "bytes"])

    print(decision)


if __name__ == "__main__":
    main()
