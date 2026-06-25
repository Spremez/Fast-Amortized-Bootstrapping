#!/usr/bin/env python3
"""Build the Stage 27 final engineering evidence package.

The package is an aggregation of already-recorded Stage 25/26/27 artifacts.
It does not rerun benchmarks and it does not upgrade claim strength.
"""

from __future__ import annotations

import csv
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
OUT_DIR = ROOT / "repro" / "stage27_final_evidence_package"
DOC_PATH = ROOT / "docs" / "stage27_final_evidence_package.md"


TARGET_PERF = ROOT / "repro" / "stage27_final_full_sab_summary.csv"
TARGET_NOISE = ROOT / "repro" / "stage25_final_noise_avx512_r2_r4_seeds50" / "aggregate.csv"
RESOURCE = ROOT / "repro" / "stage25_resource_avx512" / "summary.csv"
ADDED_PERF = ROOT / "repro" / "stage26_parameter_perf_noise_avx512_added_binary_r2_r4_runs5_seeds5" / "performance_summary.csv"
ADDED_PERF_STATS = ROOT / "repro" / "stage26_parameter_perf_noise_avx512_added_binary_r2_r4_runs5_seeds5" / "performance_stats.csv"
ADDED_NOISE = ROOT / "repro" / "stage26_parameter_perf_noise_avx512_added_binary_r2_r4_runs5_seeds5" / "noise_summary.csv"
CLAIMS = ROOT / "repro" / "stage27_claim_support_matrix.csv"
CITATION_PROBE = ROOT / "repro" / "stage27_citation_access_probe" / "summary.csv"


def read_csv(path: Path) -> list[dict[str, str]]:
    with path.open(newline="", encoding="utf-8") as f:
        return list(csv.DictReader(f))


def write_csv(path: Path, fieldnames: list[str], rows: list[dict[str, str]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames, lineterminator="\n")
        writer.writeheader()
        writer.writerows(rows)


def rel(path: Path | str) -> str:
    p = Path(path)
    if p.is_absolute():
        return p.relative_to(ROOT).as_posix()
    return p.as_posix().replace("\\", "/")


def speed_note(row: dict[str, str], stats: dict[tuple[str, str], dict[str, str]] | None = None) -> str:
    key = (row.get("param", "SET_2_3_2048"), row["r"])
    if stats and key in stats:
        stat = stats[key]
        ci = float(stat["ci95_halfwidth_t_df4"])
        if ci >= 0.10:
            return "positive mean; high timing variance, report range/CI"
        return "positive small-sample support"
    if row["r"] == "4":
        return "strongest current target evidence"
    return "positive but noisy target evidence"


def build_performance() -> list[dict[str, str]]:
    rows: list[dict[str, str]] = []
    for row in read_csv(TARGET_PERF):
        rows.append(
            {
                "scope": "target_binary_final_rerun",
                "param": "SET_2_3_2048",
                "r": row["r"],
                "runs": row["runs"],
                "status": row["status"],
                "pvw_mean_us": row["pvw_mean_us"],
                "scalar_repeated_mean_us": row["scalar_repeated_mean_us"],
                "mean_speedup": row["mean_speedup"],
                "min_speedup": row["min_speedup"],
                "max_speedup": row["max_speedup"],
                "stddev_speedup": "",
                "ci95_low": "",
                "ci95_high": "",
                "evidence_label": "scoped_target_complete_sab",
                "interpretation": speed_note(row),
                "source_csv": row["source_csv"],
            }
        )

    stats = {(row["param"], row["r"]): row for row in read_csv(ADDED_PERF_STATS)}
    for row in read_csv(ADDED_PERF):
        stat = stats[(row["param"], row["r"])]
        rows.append(
            {
                "scope": "added_binary_small_sample",
                "param": row["param"],
                "r": row["r"],
                "runs": row["runs"],
                "status": row["status"],
                "pvw_mean_us": row["pvw_mean_us"],
                "scalar_repeated_mean_us": row["scalar_repeated_mean_us"],
                "mean_speedup": row["mean_speedup"],
                "min_speedup": row["min_speedup"],
                "max_speedup": row["max_speedup"],
                "stddev_speedup": stat["stddev_speedup"],
                "ci95_low": stat["ci95_low_t_df4"],
                "ci95_high": stat["ci95_high_t_df4"],
                "evidence_label": "small_sample_parameter_support",
                "interpretation": speed_note(row, stats),
                "source_csv": row["source_csv"],
            }
        )
    return rows


def build_noise() -> list[dict[str, str]]:
    rows: list[dict[str, str]] = []
    for row in read_csv(TARGET_NOISE):
        rows.append(
            {
                "scope": "target_binary_50_seed",
                "param": "SET_2_3_2048",
                "r": row["r"],
                "seeds": row["seeds"],
                "points": row["points"],
                "pvw_failures": row["pvw_failures"],
                "scalar_failures": row["scalar_failures"],
                "pair_failures": row["pair_failures"],
                "min_gap": row["min_pvw_minus_scalar_log2"],
                "max_gap": row["max_pvw_minus_scalar_log2"],
                "avg_gap": row["avg_pvw_minus_scalar_log2"],
                "status": row["status"],
                "evidence_label": "target_noise_supported",
                "source_csv": rel(TARGET_NOISE),
            }
        )
    for row in read_csv(ADDED_NOISE):
        rows.append(
            {
                "scope": "added_binary_5_seed",
                "param": row["param"],
                "r": row["r"],
                "seeds": row["seeds"],
                "points": row["points"],
                "pvw_failures": row["pvw_failures"],
                "scalar_failures": row["scalar_failures"],
                "pair_failures": row["pair_failures"],
                "min_gap": row["min_pvw_minus_scalar_log2"],
                "max_gap": row["max_pvw_minus_scalar_log2"],
                "avg_gap": row["avg_pvw_minus_scalar_log2"],
                "status": row["status"],
                "evidence_label": "small_sample_noise_support",
                "source_csv": row["source_csv"],
            }
        )
    return rows


def build_resource() -> list[dict[str, str]]:
    rows: list[dict[str, str]] = []
    for row in read_csv(RESOURCE):
        rows.append(
            {
                "scope": "target_binary_resource_smoke",
                "backend": row["backend"],
                "r": row["r"],
                "mode": row["mode"],
                "keygen_us": row["keygen_us"],
                "keygen_lane_avg_us": row["keygen_lane_avg_us"],
                "estimated_key_bytes": row["estimated_key_bytes"],
                "estimated_key_bytes_ratio_vs_scalar_repeated": row["estimated_key_bytes_ratio_vs_scalar_repeated"],
                "internal_vmhwm_kb": row["internal_vmhwm_kb"],
                "time_max_rss_kb": row["time_max_rss_kb"],
                "evidence_label": "resource_smoke_report_not_optimization_claim",
                "source_log": row["source_log"],
                "time_log": row["time_log"],
            }
        )
    return rows


def build_claims() -> list[dict[str, str]]:
    rows: list[dict[str, str]] = []
    for row in read_csv(CLAIMS):
        blocked = row["status_label"].startswith("BLOCKED")
        rows.append(
            {
                "claim_id": row["claim_id"],
                "claim": row["claim"],
                "status_label": row["status_label"],
                "manuscript_action": "block_or_limit" if blocked else "allowed_if_scoped",
                "allowed_wording": row["allowed_wording"],
                "blocked_wording": row["blocked_wording"],
                "primary_evidence": row["primary_evidence"],
                "external_sources": row["external_sources"],
            }
        )
    return rows


def build_citation_gate() -> list[dict[str, str]]:
    if not CITATION_PROBE.exists():
        return [
            {
                "gate": "citation_access_probe",
                "status": "NOT_RUN",
                "detail": "Run scripts/run_stage27_citation_access_probe.sh before theorem-level citation claims.",
            }
        ]
    return read_csv(CITATION_PROBE)


def markdown_table(rows: list[dict[str, str]], columns: list[str]) -> str:
    header = "| " + " | ".join(columns) + " |"
    sep = "| " + " | ".join(["---"] * len(columns)) + " |"
    body = []
    for row in rows:
        body.append("| " + " | ".join(row.get(col, "") for col in columns) + " |")
    return "\n".join([header, sep] + body)


def build_doc(
    performance: list[dict[str, str]],
    noise: list[dict[str, str]],
    resource: list[dict[str, str]],
    claims: list[dict[str, str]],
    citation_gate: list[dict[str, str]],
) -> str:
    perf_cols = ["scope", "param", "r", "runs", "mean_speedup", "min_speedup", "max_speedup", "interpretation"]
    noise_cols = ["scope", "param", "r", "seeds", "points", "pvw_failures", "scalar_failures", "pair_failures", "status"]
    claim_cols = ["claim_id", "status_label", "manuscript_action", "claim"]
    citation_cols = ["gate", "status", "detail"]

    pvw_resource = [
        row
        for row in resource
        if row["mode"] == "pvw" and row["r"] in {"2", "4"}
    ]
    resource_cols = [
        "r",
        "mode",
        "keygen_lane_avg_us",
        "estimated_key_bytes_ratio_vs_scalar_repeated",
        "time_max_rss_kb",
    ]

    return "\n".join(
        [
            "# Stage 27 Final Evidence Package",
            "",
            "Date: 2026-06-25",
            "",
            "## Scope",
            "",
            "This package aggregates already-recorded Stage 25/26/27 evidence for the",
            "explicit PVW/MAT-SAB path. It supports a scoped engineering claim only.",
            "It does not support novelty, non-binary PVW-SAB, all-parameter speedup,",
            "or theoretical-optimal AVX512 claims.",
            "",
            "Primary endpoint: complete `sab_pvw_*` bootstrapping throughput versus",
            "repeated scalar SAB under the same backend and parameter scope.",
            "",
            "## Performance",
            "",
            markdown_table(performance, perf_cols),
            "",
            "## Final-Output Noise",
            "",
            markdown_table(noise, noise_cols),
            "",
            "## Resource Snapshot",
            "",
            markdown_table(pvw_resource, resource_cols),
            "",
            "## Claim Boundary",
            "",
            markdown_table(claims, claim_cols),
            "",
            "## Citation Gate",
            "",
            markdown_table(citation_gate, citation_cols),
            "",
            "## Decision",
            "",
            "```text",
            "FINAL_ENGINEERING_EVIDENCE_PACKAGE_ASSEMBLED",
            "SAFE_SCOPED_ENGINEERING_CLAIM_SUPPORTED",
            "NOVELTY_CLAIM_BLOCKED_PENDING_FULL_2025_686_AND_PRIOR_ART_REVIEW",
            "NON_BINARY_AND_ALL_PARAMETER_CLAIMS_BLOCKED",
            "```",
            "",
            "Source CSVs are listed in `repro/stage27_final_evidence_package/manifest.csv`.",
            "",
        ]
    )


def main() -> None:
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    performance = build_performance()
    noise = build_noise()
    resource = build_resource()
    claims = build_claims()
    citation_gate = build_citation_gate()

    write_csv(
        OUT_DIR / "performance_scope.csv",
        [
            "scope",
            "param",
            "r",
            "runs",
            "status",
            "pvw_mean_us",
            "scalar_repeated_mean_us",
            "mean_speedup",
            "min_speedup",
            "max_speedup",
            "stddev_speedup",
            "ci95_low",
            "ci95_high",
            "evidence_label",
            "interpretation",
            "source_csv",
        ],
        performance,
    )
    write_csv(
        OUT_DIR / "noise_scope.csv",
        [
            "scope",
            "param",
            "r",
            "seeds",
            "points",
            "pvw_failures",
            "scalar_failures",
            "pair_failures",
            "min_gap",
            "max_gap",
            "avg_gap",
            "status",
            "evidence_label",
            "source_csv",
        ],
        noise,
    )
    write_csv(
        OUT_DIR / "resource_scope.csv",
        [
            "scope",
            "backend",
            "r",
            "mode",
            "keygen_us",
            "keygen_lane_avg_us",
            "estimated_key_bytes",
            "estimated_key_bytes_ratio_vs_scalar_repeated",
            "internal_vmhwm_kb",
            "time_max_rss_kb",
            "evidence_label",
            "source_log",
            "time_log",
        ],
        resource,
    )
    write_csv(
        OUT_DIR / "claim_scope.csv",
        [
            "claim_id",
            "claim",
            "status_label",
            "manuscript_action",
            "allowed_wording",
            "blocked_wording",
            "primary_evidence",
            "external_sources",
        ],
        claims,
    )
    write_csv(OUT_DIR / "citation_gate.csv", ["gate", "status", "detail"], citation_gate)
    manifest_rows = [
        {"artifact": "performance_scope", "path": rel(OUT_DIR / "performance_scope.csv"), "source": rel(TARGET_PERF) + "; " + rel(ADDED_PERF) + "; " + rel(ADDED_PERF_STATS)},
        {"artifact": "noise_scope", "path": rel(OUT_DIR / "noise_scope.csv"), "source": rel(TARGET_NOISE) + "; " + rel(ADDED_NOISE)},
        {"artifact": "resource_scope", "path": rel(OUT_DIR / "resource_scope.csv"), "source": rel(RESOURCE)},
        {"artifact": "claim_scope", "path": rel(OUT_DIR / "claim_scope.csv"), "source": rel(CLAIMS)},
        {"artifact": "citation_gate", "path": rel(OUT_DIR / "citation_gate.csv"), "source": rel(CITATION_PROBE)},
        {"artifact": "markdown_summary", "path": rel(DOC_PATH), "source": "generated from final package CSVs"},
    ]
    write_csv(OUT_DIR / "manifest.csv", ["artifact", "path", "source"], manifest_rows)

    DOC_PATH.write_text(build_doc(performance, noise, resource, claims, citation_gate), encoding="utf-8", newline="\n")
    print(f"Wrote {rel(DOC_PATH)}")
    print(f"Wrote {rel(OUT_DIR / 'manifest.csv')}")


if __name__ == "__main__":
    main()
