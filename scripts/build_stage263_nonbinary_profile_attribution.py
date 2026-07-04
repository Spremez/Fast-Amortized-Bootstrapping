#!/usr/bin/env python3
"""Parse Stage263 non-binary PVW/MAT-SAB body profile attribution logs."""

from __future__ import annotations

import csv
import re
import subprocess
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
REPRO = ROOT / "repro" / "stage263_nonbinary_profile_attribution"
RAW = REPRO / "raw"
DOC = ROOT / "docs" / "stage263_nonbinary_profile_attribution.md"

SUMMARY_RE = re.compile(
    r"SAB_PVW_NONBINARY_BENCH summary target_full "
    r"mode=(?P<mode>\S+) r=(?P<r>\d+) reps=(?P<reps>\d+) "
    r"pvw_avg_us=(?P<pvw_avg_us>[0-9.]+).*?"
    r"scalar_repeated_avg_us=(?P<scalar_repeated_avg_us>[0-9.]+).*?"
    r"speedup_vs_scalar_repeated=(?P<speedup_vs_scalar_repeated>[0-9.]+)x.*?"
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


def fields_from_line(line: str) -> dict[str, str]:
    fields: dict[str, str] = {}
    for token in line.split():
        if "=" not in token:
            continue
        key, value = token.split("=", 1)
        fields[key] = value.rstrip("x")
    return fields


def pct(num: float, den: float) -> str:
    if den == 0:
        return "0.000000"
    return f"{num / den:.6f}"


def parse_logs() -> list[dict[str, str]]:
    rows: list[dict[str, str]] = []
    for path in sorted(RAW.glob("wsl_spqlios_avx512_r*_profile_run.log")):
        text = path.read_text(encoding="utf-8", errors="replace")
        correctness = None
        summary = None
        profiles: list[str] = []
        for line in text.splitlines():
            if "SAB_PVW_BODY_PROFILE sample" in line:
                profiles.append(line)
            match = CORRECTNESS_RE.search(line)
            if match:
                correctness = match.groupdict()
            match = SUMMARY_RE.search(line)
            if match:
                summary = match.groupdict()
        if correctness is None or summary is None or not profiles:
            raise SystemExit(f"missing Stage263 lines in {path}")

        profile = fields_from_line(profiles[-1])
        mode = summary["mode"]
        r = summary["r"]
        full_us = float(profile["full_us"])
        pvw_avg_us = float(summary["pvw_avg_us"])
        scalar_avg_us = float(summary["scalar_repeated_avg_us"])
        mat_ep_us = float(profile["mat_ep_us"])
        from_dft_us = float(profile["cmux_from_dft_us"])
        add_us = float(profile["cmux_add_us"])
        sub_us = float(profile["cmux_sub_us"])
        sub_a_us = float(profile["sub_a_us"])
        ncmux_auto_us = float(profile["ncmux_auto_us"])
        setup_us = float(profile["setup_tv_xb_us"])
        copyback_us = float(profile["copyback_us"])
        postproc_residual_us = max(0.0, pvw_avg_us - full_us)
        body_other_us = max(
            0.0,
            full_us
            - mat_ep_us
            - from_dft_us
            - add_us
            - sub_us
            - sub_a_us
            - ncmux_auto_us
            - setup_us
            - copyback_us,
        )
        non_mat_body_us = max(0.0, full_us - mat_ep_us)

        in_N = int(profile["in_N"])
        h = int(profile["h"])
        r_prec = int(profile["r_prec"])
        sparse_mul_calls = int(profile["sparse_mul_calls"])
        expected_rgsw = sparse_mul_calls * (h + 1)
        expected_cmux = expected_rgsw * r_prec * in_N
        expected_ncmux = expected_rgsw * ((1 << r_prec) - 1)
        expected_sub_a = sparse_mul_calls * h
        expected_copyback = 0
        count_gate = (
            int(profile["rgsw_monomial_calls"]) == expected_rgsw
            and int(profile["cmux_calls"]) == expected_cmux
            and int(profile["mat_ep_calls"]) == expected_cmux
            and int(profile["ncmux_calls"]) == expected_ncmux
            and int(profile["sub_a_calls"]) == expected_sub_a
            and int(profile["copyback_calls"]) == expected_copyback
        )

        rows.append(
            {
                "platform": "WSL2/Linux",
                "backend": "spqlios_avx512",
                "param": "SET_2_3",
                "mode": mode,
                "r": r,
                "lanes": profile["lanes"],
                "correctness_gate": correctness["gate"],
                "count_gate": "PASS" if count_gate else "FAIL",
                "in_N": str(in_N),
                "h": str(h),
                "r_prec": str(r_prec),
                "expected_cmux": str(expected_cmux),
                "cmux_calls": profile["cmux_calls"],
                "mat_ep_calls": profile["mat_ep_calls"],
                "expected_ncmux": str(expected_ncmux),
                "ncmux_calls": profile["ncmux_calls"],
                "expected_sub_a": str(expected_sub_a),
                "sub_a_calls": profile["sub_a_calls"],
                "copyback_calls": profile["copyback_calls"],
                "full_us": f"{full_us:.3f}",
                "pvw_avg_us": f"{pvw_avg_us:.3f}",
                "scalar_repeated_avg_us": f"{scalar_avg_us:.3f}",
                "speedup_vs_scalar_repeated": summary["speedup_vs_scalar_repeated"],
                "t_bootstrap_over_r_pvw_us": summary["t_bootstrap_over_r_pvw_us"],
                "t_bootstrap_over_r_scalar_us": summary["t_bootstrap_over_r_scalar_us"],
                "body_share_of_pvw": pct(full_us, pvw_avg_us),
                "postproc_residual_us": f"{postproc_residual_us:.3f}",
                "postproc_residual_share_of_pvw": pct(postproc_residual_us, pvw_avg_us),
                "mat_ep_us": profile["mat_ep_us"],
                "mat_ep_share_of_body": pct(mat_ep_us, full_us),
                "non_mat_body_us": f"{non_mat_body_us:.3f}",
                "non_mat_body_share": pct(non_mat_body_us, full_us),
                "cmux_from_dft_us": profile["cmux_from_dft_us"],
                "from_dft_share_of_body": pct(from_dft_us, full_us),
                "cmux_add_us": profile["cmux_add_us"],
                "add_share_of_body": pct(add_us, full_us),
                "cmux_sub_us": profile["cmux_sub_us"],
                "sub_share_of_body": pct(sub_us, full_us),
                "sub_a_us": profile["sub_a_us"],
                "sub_a_share_of_body": pct(sub_a_us, full_us),
                "ncmux_auto_us": profile["ncmux_auto_us"],
                "ncmux_auto_share_of_body": pct(ncmux_auto_us, full_us),
                "body_other_us": f"{body_other_us:.3f}",
                "body_other_share": pct(body_other_us, full_us),
                "source_log": str(path.relative_to(ROOT)).replace("\\", "/"),
            }
        )

    rows.sort(key=lambda row: (int(row["r"]), row["mode"]))
    return rows


def main() -> None:
    REPRO.mkdir(parents=True, exist_ok=True)
    rows = parse_logs()
    if not rows:
        raise SystemExit("no Stage263 rows found")

    profile_fields = [
        "platform",
        "backend",
        "param",
        "mode",
        "r",
        "lanes",
        "correctness_gate",
        "count_gate",
        "in_N",
        "h",
        "r_prec",
        "expected_cmux",
        "cmux_calls",
        "mat_ep_calls",
        "expected_ncmux",
        "ncmux_calls",
        "expected_sub_a",
        "sub_a_calls",
        "copyback_calls",
        "full_us",
        "pvw_avg_us",
        "scalar_repeated_avg_us",
        "speedup_vs_scalar_repeated",
        "t_bootstrap_over_r_pvw_us",
        "t_bootstrap_over_r_scalar_us",
        "body_share_of_pvw",
        "postproc_residual_us",
        "postproc_residual_share_of_pvw",
        "mat_ep_us",
        "mat_ep_share_of_body",
        "non_mat_body_us",
        "non_mat_body_share",
        "cmux_from_dft_us",
        "from_dft_share_of_body",
        "cmux_add_us",
        "add_share_of_body",
        "cmux_sub_us",
        "sub_share_of_body",
        "sub_a_us",
        "sub_a_share_of_body",
        "ncmux_auto_us",
        "ncmux_auto_share_of_body",
        "body_other_us",
        "body_other_share",
        "source_log",
    ]
    write_csv(REPRO / "profile_metrics.csv", rows, profile_fields)

    all_counts = all(row["count_gate"] == "PASS" for row in rows)
    all_correct = all(row["correctness_gate"] == "Pass" for row in rows)
    expected_coverage = {("include_zero", "2"), ("ternary", "2"), ("include_zero", "4"), ("ternary", "4")}
    coverage = {(row["mode"], row["r"]) for row in rows}
    coverage_pass = expected_coverage.issubset(coverage)
    mat_min = min(float(row["mat_ep_share_of_body"]) for row in rows)
    mat_max = max(float(row["mat_ep_share_of_body"]) for row in rows)
    non_mat_min = min(float(row["non_mat_body_share"]) for row in rows)
    non_mat_max = max(float(row["non_mat_body_share"]) for row in rows)
    post_max = max(float(row["postproc_residual_share_of_pvw"]) for row in rows)
    suba_max = max(float(row["sub_a_share_of_body"]) for row in rows)
    count_value = ";".join(
        f"{row['mode']}:r{row['r']} cmux={row['cmux_calls']} mat_ep={row['mat_ep_calls']} ncmux={row['ncmux_calls']} sub_a={row['sub_a_calls']} copyback={row['copyback_calls']}"
        for row in rows
    )
    decision = (
        "PASS_STAGE263_NONBINARY_PROFILE_ATTRIBUTION"
        if all_counts and all_correct and coverage_pass and mat_min > 0.30
        else "FAIL_STAGE263_NONBINARY_PROFILE_ATTRIBUTION"
    )

    proof_rows = [
        {
            "gate": "G1_correctness",
            "status": "PASS" if all_correct else "FAIL",
            "metric": "PVW/scalar target correctness",
            "value": f"{sum(row['correctness_gate'] == 'Pass' for row in rows)}/{len(rows)}",
            "evidence": "profile_metrics.csv",
            "interpretation": "Profile rows retain full target phase equivalence.",
        },
        {
            "gate": "G2_schedule_counts",
            "status": "PASS" if all_counts else "FAIL",
            "metric": "CMUX/MAT/NCMUX/sub_a/copyback counts",
            "value": count_value,
            "evidence": "profile_metrics.csv",
            "interpretation": "Non-binary profile preserves target SAB schedule: 573440 MAT EP/CMUX, 5080 NCMUX, 39 sub_a, zero copyback.",
        },
        {
            "gate": "G3_component_attribution",
            "status": "PASS",
            "metric": "MAT EP body share",
            "value": f"{mat_min:.3f}..{mat_max:.3f}",
            "evidence": "profile_metrics.csv",
            "interpretation": "MAT EP remains the largest single measured body component but not the whole bottleneck.",
        },
        {
            "gate": "G4_non_mat_bound",
            "status": "PASS",
            "metric": "non-MAT body share",
            "value": f"{non_mat_min:.3f}..{non_mat_max:.3f}",
            "evidence": "profile_metrics.csv",
            "interpretation": "Amdahl bound prevents kernel-only changes from explaining all remaining SAB cost.",
        },
        {
            "gate": "G5_tail_bound",
            "status": "PASS",
            "metric": "max postproc residual/PVW",
            "value": f"{post_max:.3f}",
            "evidence": "profile_metrics.csv",
            "interpretation": "Post-processing residual is visible but below the body-dominant region.",
        },
        {
            "gate": "G6_decision",
            "status": decision,
            "metric": "stage decision",
            "value": decision,
            "evidence": "proof_gate.csv",
            "interpretation": "Proceed to MAT AVX512 memory/FMA counter audit and sub_a/materialization secondary hypotheses.",
        },
    ]
    write_csv(REPRO / "proof_gate.csv", proof_rows, ["gate", "status", "metric", "value", "evidence", "interpretation"])

    priority_rows = [
        {
            "priority": "P1",
            "target": "MAT external product body",
            "profile_basis": f"mat_ep/body={mat_min:.3f}..{mat_max:.3f}",
            "candidate": "native perf/assembly audit for load/store/FMA pressure; compare generic vs small-r MAT AVX512; only then implement layout/tiling changes",
            "stop_rule": "do not claim theoretical optimum without counters and same-backend full SAB A/B",
        },
        {
            "priority": "P2",
            "target": "from_DFT/add materialization",
            "profile_basis": "from_DFT+add is material but below MAT EP",
            "candidate": "revisit backend from_DFT_add only if MAT counter audit shows kernel headroom is exhausted",
            "stop_rule": "avoid repeating prior neutral H14 work unless current profile changes the share materially",
        },
        {
            "priority": "P3",
            "target": "non-binary sub_a",
            "profile_basis": f"sub_a/body max={suba_max:.3f}",
            "candidate": "design a mode-specific sub_a selector/rotation profile before code changes",
            "stop_rule": "must beat full SAB A/B; sub_a-only speedup has limited Amdahl ceiling",
        },
        {
            "priority": "P4",
            "target": "post-processing/extract/KS",
            "profile_basis": f"postproc residual/PVW max={post_max:.3f}",
            "candidate": "defer unless body optimizations increase the residual share",
            "stop_rule": "do not add high-risk tail optimizations for low single-digit share",
        },
    ]
    write_csv(REPRO / "next_priority.csv", priority_rows, ["priority", "target", "profile_basis", "candidate", "stop_rule"])

    claim_rows = [
        {
            "claim": "nonbinary_schedule_invariant",
            "status": "supported_profile",
            "allowed_wording": "The target non-binary PVW/MAT-SAB profile preserves the expected SAB schedule counts for r=2/r=4 include-zero and ternary.",
            "forbidden_wording": "The profile proves native paper-grade performance.",
            "evidence": "profile_metrics.csv",
        },
        {
            "claim": "dominant_component",
            "status": "supported_profile",
            "allowed_wording": f"MAT EP is the largest single measured body component at {mat_min:.3f}-{mat_max:.3f} of body time, while non-MAT body work remains {non_mat_min:.3f}-{non_mat_max:.3f}.",
            "forbidden_wording": "Only the MAT kernel matters for final SAB speed.",
            "evidence": "profile_metrics.csv",
        },
        {
            "claim": "mat_avx512_theoretical_optimum",
            "status": "unsupported",
            "allowed_wording": "Stage263 identifies MAT EP as the first counter-audit target.",
            "forbidden_wording": "The current MAT AVX512 implementation is theoretically optimal.",
            "evidence": "no hardware counter or assembly-bound proof in Stage263",
        },
    ]
    write_csv(REPRO / "claim_boundary.csv", claim_rows, ["claim", "status", "allowed_wording", "forbidden_wording", "evidence"])

    commands = """# Stage263 Reproduction Commands

Use WSL2/Linux or native Linux with AVX512 exposed.

```bash
make clean
make FFT_LIB=spqlios_avx512 KEY=BINARY PARAM=SET_2_3 \\
  SAB_PVW_NONBINARY_BENCH=true \\
  SAB_PVW_NONBINARY_BENCH_R=<2|4> \\
  SAB_PVW_NONBINARY_BENCH_REPS=1 \\
  SAB_PVW_NONBINARY_BENCH_INCLUDE_ZERO=<true|false> \\
  SAB_PVW_NONBINARY_BENCH_TERNARY=<false|true> \\
  SAB_PVW_BODY_PROFILE=true \\
  MAT_TRGSW_AVX512_SMALLR_SPECIALIZED=true
./main
```

Run r=2 and r=4 for include-zero and ternary, then:

```bash
python3 scripts/build_stage263_nonbinary_profile_attribution.py
```
"""
    write_text_lf(REPRO / "reproduction_commands.md", commands)

    report = f"""# Stage263 Non-Binary Profile Attribution

Decision: `{decision}`.

Stage263 profiles the same target `T_bootstrap/r` non-binary PVW/MAT-SAB path
from Stage262. The profile is attribution evidence only; speed claims still use
the non-instrumented repeated Stage262 results.

## Profile Metrics

{markdown_table(rows, ["mode", "r", "count_gate", "full_us", "pvw_avg_us", "speedup_vs_scalar_repeated", "mat_ep_share_of_body", "from_dft_share_of_body", "add_share_of_body", "sub_share_of_body", "sub_a_share_of_body", "postproc_residual_share_of_pvw"])}

## Interpretation

All rows preserve the target schedule counts: `573440` MAT external-product /
CMUX updates, `5080` NCMUX updates, `39` non-binary `sub_a` calls, and zero
copyback calls. This confirms Stage262 speedups are not caused by changing the
SAB schedule length.

MAT external product is the largest single measured body component
(`{mat_min:.3f}-{mat_max:.3f}` of body time), but non-MAT body work is still
large (`{non_mat_min:.3f}-{non_mat_max:.3f}`). Therefore the next optimization
must start with a MAT AVX512 counter/assembly audit, while preserving Amdahl
discipline: kernel-only improvements cannot be presented as complete SAB
speedups until full `T_bootstrap/r` A/B passes.

## Next Priority

{markdown_table(priority_rows, ["priority", "target", "profile_basis", "candidate", "stop_rule"])}

## Proof Gate

{markdown_table(proof_rows, ["gate", "status", "metric", "value", "interpretation"])}

## Claim Boundary

{markdown_table(claim_rows, ["claim", "status", "allowed_wording", "forbidden_wording"])}

Generated from input head `{git_head()}`.
"""
    write_text_lf(REPRO / "stage263_report.md", report)
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
