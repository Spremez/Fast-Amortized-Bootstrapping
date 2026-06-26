#!/usr/bin/env python3
"""Build the Stage96 upstream/local-delta provenance audit."""

from __future__ import annotations

import argparse
import csv
import subprocess
from collections import Counter
from pathlib import Path
from typing import Dict, Iterable, List


ROOT = Path(__file__).resolve().parents[1]
DEFAULT_OUT = ROOT / "repro" / "stage96_upstream_delta_audit"
OUT_MD = ROOT / "docs" / "stage96_upstream_delta_audit_log.md"

STAGE95 = ROOT / "repro" / "stage95_public_source_reprobe" / "summary.csv"
STAGE91_CLAIMS = ROOT / "repro" / "stage91_final_package" / "claim_boundary.csv"
MAKEFILE_DEF = ROOT / "src" / "mosfhet" / "Makefile.def"

DEFAULT_FALSE_FLAGS = [
    "MAT_TRGSW_AVX512_SMALLR_SPECIALIZED",
    "MAT_TRGSW_AVX512_RGT4_FUSED",
    "SAB_PVW_KERNEL_TEST",
    "SAB_PVW_RGT4_KERNEL_TEST",
    "SAB_PVW_TARGET_TEST",
    "SAB_PVW_BENCH",
    "SAB_PVW_NOISE_TEST",
    "SAB_PVW_STAGE_NOISE_TEST",
    "SAB_PVW_RESOURCE_TEST",
    "SAB_PVW_POSTPROC_PROFILE",
    "SAB_PVW_BODY_PROFILE",
    "SAB_PVW_FUSED_FROM_DFT_ADD",
    "SAB_PVW_BACKEND_FROM_DFT_ADD",
    "SAB_PVW_ACTIVE_BUFFER_FUSION",
    "SAB_PVW_SUBA_OUTPUT_FUSION",
    "SAB_PVW_SCHEDULE_FUSED_CMUX",
]


def read_csv(path: Path) -> List[Dict[str, str]]:
    if not path.exists():
        return []
    with path.open(newline="", encoding="utf-8-sig") as f:
        return list(csv.DictReader(f))


def by_key(path: Path, key: str) -> Dict[str, Dict[str, str]]:
    return {row.get(key, ""): row for row in read_csv(path)}


def rel(path: Path) -> str:
    return path.relative_to(ROOT).as_posix()


def write_csv(path: Path, rows: Iterable[Dict[str, str]], fields: List[str]) -> None:
    rows = list(rows)
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fields, lineterminator="\n")
        writer.writeheader()
        writer.writerows(rows)


def git(args: List[str]) -> str:
    proc = subprocess.run(
        ["git", *args],
        cwd=ROOT,
        text=True,
        capture_output=True,
        check=False,
    )
    if proc.returncode != 0:
        return ""
    return proc.stdout.strip()


def git_lines(args: List[str]) -> List[str]:
    out = git(args)
    return [line.strip() for line in out.splitlines() if line.strip()]


def status_of(rows: Dict[str, Dict[str, str]], key: str) -> str:
    return rows.get(key, {}).get("status", "MISSING")


def category_for(path: str) -> str:
    norm = path.replace("\\", "/")
    if norm in {"main.c", "Makefile", "runall.sh"}:
        return "top_level_build_or_harness"
    if norm.startswith("include/") or norm.startswith("src/"):
        if "sab_pvw" in norm or "pvw" in norm or "mattrgsw" in norm:
            return "pvw_mat_sab_source"
        return "source_or_backend"
    if norm.startswith("docs/"):
        return "docs"
    if norm.startswith("experiments/"):
        return "experiments"
    if norm.startswith("scripts/"):
        return "scripts"
    if norm.startswith("repro/"):
        return "repro"
    if norm.startswith("theory_checks/"):
        return "theory"
    if norm.startswith("algorithm_variants/"):
        return "algorithm_variants"
    if norm.startswith("hypotheses/"):
        return "hypotheses"
    if norm.startswith("external/"):
        return "external"
    return "other"


def build_delta_files() -> List[Dict[str, str]]:
    files = git_lines(["diff", "--name-only", "origin/main..HEAD", "--"])
    return [
        {
            "path": item,
            "area": category_for(item),
            "is_hotpath_source": "yes"
            if item == "main.c"
            or item.startswith("include/")
            or item.startswith("src/")
            else "no",
        }
        for item in files
    ]


def build_delta_by_area(delta_files: List[Dict[str, str]]) -> List[Dict[str, str]]:
    counts = Counter(row["area"] for row in delta_files)
    hot_counts = Counter(row["area"] for row in delta_files if row["is_hotpath_source"] == "yes")
    return [
        {
            "area": area,
            "changed_files": str(counts[area]),
            "hotpath_source_files": str(hot_counts.get(area, 0)),
            "interpretation": interpretation_for_area(area),
        }
        for area in sorted(counts)
    ]


def interpretation_for_area(area: str) -> str:
    if area == "pvw_mat_sab_source":
        return "local PVW/MAT-SAB source delta relative to public upstream"
    if area == "source_or_backend":
        return "non-PVW or shared source/backend delta that may affect reproducibility"
    if area == "top_level_build_or_harness":
        return "top-level harness/build delta for tests and benchmarks"
    if area in {"docs", "experiments", "scripts", "repro"}:
        return "reproducibility/control-plane evidence delta"
    if area in {"theory", "algorithm_variants", "hypotheses"}:
        return "algorithm/theory evidence delta"
    return "miscellaneous local delta"


def build_commit_range() -> List[Dict[str, str]]:
    lines = git_lines(["log", "--format=%h%x09%s", "origin/main..HEAD"])
    rows = []
    for idx, line in enumerate(lines, 1):
        if "\t" in line:
            short_hash, subject = line.split("\t", 1)
        else:
            short_hash, subject = line, ""
        rows.append({"ordinal_from_head": str(idx), "commit": short_hash, "subject": subject})
    return rows


def build_flag_guard() -> List[Dict[str, str]]:
    text = MAKEFILE_DEF.read_text(encoding="utf-8") if MAKEFILE_DEF.exists() else ""
    rows = []
    for flag in DEFAULT_FALSE_FLAGS:
        expected = f"{flag} ?= false"
        present = expected in text
        rows.append(
            {
                "flag": flag,
                "expected_default": "false",
                "status": "PASS_DEFAULT_FALSE" if present else "FAIL_DEFAULT_NOT_FALSE",
                "evidence": rel(MAKEFILE_DEF),
                "detail": expected if present else f"missing token: {expected}",
            }
        )
    return rows


def row(gate: str, status: str, evidence: str, detail: str, next_action: str) -> Dict[str, str]:
    return {
        "gate": gate,
        "status": status,
        "evidence": evidence,
        "detail": detail,
        "next_action": next_action,
    }


def build_summary(
    out_dir: Path,
    delta_files: List[Dict[str, str]],
    delta_by_area: List[Dict[str, str]],
    flag_guard: List[Dict[str, str]],
) -> List[Dict[str, str]]:
    stage95 = by_key(STAGE95, "gate")
    claims = by_key(STAGE91_CLAIMS, "claim_id")
    head = git(["rev-parse", "--short", "HEAD"]) or "MISSING"
    upstream = git(["rev-parse", "--short", "origin/main"]) or "MISSING"
    merge_base_full = git(["merge-base", "HEAD", "origin/main"])
    merge_base = git(["rev-parse", "--short", merge_base_full]) if merge_base_full else "MISSING"
    ahead = git(["rev-list", "--count", "origin/main..HEAD"]) or "MISSING"
    behind = git(["rev-list", "--count", "HEAD..origin/main"]) or "MISSING"
    upstream_ok = upstream != "MISSING"
    relation_ok = upstream_ok and merge_base == upstream and ahead != "0" and behind == "0"
    stage95_ok = (
        status_of(stage95, "stage95_decision")
        == "PASS_STAGE95_PUBLIC_SOURCE_REPROBE_STRONGER_CLAIMS_BLOCKED"
    )
    flags_ok = all(item["status"] == "PASS_DEFAULT_FALSE" for item in flag_guard)
    delta_ok = bool(delta_files) and bool(delta_by_area)
    claim_statuses = [
        claims.get("C3", {}).get("status", "MISSING"),
        claims.get("C4", {}).get("status", "MISSING"),
        claims.get("C5", {}).get("status", "MISSING"),
    ]
    claims_blocked = all("BLOCKED" in item or "MISSING_OPTIONAL" in item for item in claim_statuses)
    pvw_sources = [
        item["path"] for item in delta_files if item["area"] == "pvw_mat_sab_source"
    ]

    rows = [
        row(
            "stage96_stage95_precondition",
            "PASS" if stage95_ok else "FAIL_STAGE95_PRECONDITION",
            rel(STAGE95),
            f"stage95_decision={status_of(stage95, 'stage95_decision')}",
            "Rerun Stage95 before interpreting upstream/code-route provenance.",
        ),
        row(
            "stage96_remote_origin_main",
            "PASS_UPSTREAM_REF_AVAILABLE" if upstream_ok else "FAIL_UPSTREAM_REF_MISSING",
            "git rev-parse --short origin/main",
            f"HEAD={head}; origin/main={upstream}; merge_base={merge_base}",
            "Run `git fetch origin` and inspect remote configuration if this fails.",
        ),
        row(
            "stage96_upstream_relation",
            "PASS_LOCAL_AHEAD_OF_UPSTREAM" if relation_ok else "REVIEW_UPSTREAM_DRIFT",
            "git merge-base HEAD origin/main; git rev-list --count",
            f"ahead={ahead}; behind={behind}; merge_base={merge_base}; upstream={upstream}",
            "If behind>0 or merge-base differs, inspect upstream changes before claiming provenance.",
        ),
        row(
            "stage96_delta_classification",
            "PASS_DELTA_CLASSIFIED" if delta_ok else "FAIL_DELTA_MISSING",
            rel(out_dir / "delta_by_area.csv"),
            f"changed_files={len(delta_files)}; pvw_mat_sab_source_files={len(pvw_sources)}",
            "Review delta_files.csv before changing upstream-vs-local wording.",
        ),
        row(
            "stage96_default_guard",
            "PASS_EXPLICIT_FLAGS_DEFAULT_FALSE" if flags_ok else "FAIL_DEFAULT_FLAG_GUARD",
            rel(out_dir / "flag_guard.csv"),
            "all tracked PVW/MAT-SAB experiment flags remain default-false"
            if flags_ok else "one or more flags are not recorded as default-false",
            "Rerun scalar/PVW smoke and default-path gates if any default changed.",
        ),
        row(
            "stage96_claim_guard",
            "PASS_STRONGER_CLAIMS_BLOCKED" if claims_blocked else "REVIEW_CLAIM_BOUNDARY",
            rel(STAGE91_CLAIMS),
            "C3/C4/C5 remain blocked or missing-optional under Stage91 claim boundary"
            if claims_blocked else f"claim_statuses={claim_statuses}",
            "Do not upgrade theorem-level, novelty, or hardware-counter claims from code-route evidence alone.",
        ),
    ]
    ok = all(item["status"].startswith("PASS") for item in rows)
    rows.append(
        row(
            "stage96_decision",
            "PASS_STAGE96_UPSTREAM_DELTA_AUDIT_LOCAL_PROVENANCE_RECORDED"
            if ok else "REVIEW_STAGE96_UPSTREAM_DELTA_AUDIT",
            rel(out_dir / "summary.csv"),
            "Public upstream provenance and local PVW/MAT-SAB delta boundary are recorded; this supports reproducibility but does not upgrade stronger claims."
            if ok else "Inspect failed Stage96 gates before relying on provenance wording.",
            "Use Stage96 when explaining which artifacts are upstream baseline versus local optimization evidence.",
        )
    )
    return rows


def artifact_rows(out_dir: Path) -> List[Dict[str, str]]:
    return [
        {"artifact": rel(out_dir / "summary.csv"), "purpose": "Stage96 gate summary", "producer": "scripts/build_stage96_upstream_delta_audit.py"},
        {"artifact": rel(out_dir / "delta_by_area.csv"), "purpose": "Changed-file counts by area", "producer": "scripts/build_stage96_upstream_delta_audit.py"},
        {"artifact": rel(out_dir / "delta_files.csv"), "purpose": "Changed-file classification relative to origin/main", "producer": "scripts/build_stage96_upstream_delta_audit.py"},
        {"artifact": rel(out_dir / "commit_range.csv"), "purpose": "Local commit range relative to origin/main", "producer": "scripts/build_stage96_upstream_delta_audit.py"},
        {"artifact": rel(out_dir / "flag_guard.csv"), "purpose": "Default-false PVW/MAT-SAB flag guard", "producer": "scripts/build_stage96_upstream_delta_audit.py"},
        {"artifact": rel(out_dir / "artifact_index.csv"), "purpose": "Stage96 artifact index", "producer": "scripts/build_stage96_upstream_delta_audit.py"},
        {"artifact": rel(OUT_MD), "purpose": "Human-readable Stage96 log", "producer": "scripts/build_stage96_upstream_delta_audit.py"},
    ]


def esc(value: str) -> str:
    return value.replace("|", "\\|").replace("\n", " ")


def write_md(
    out_dir: Path,
    summary: List[Dict[str, str]],
    delta_by_area: List[Dict[str, str]],
    flag_guard: List[Dict[str, str]],
) -> None:
    OUT_MD.parent.mkdir(parents=True, exist_ok=True)
    decision = summary[-1]
    lines = [
        "# Stage96 Upstream Delta Audit Log",
        "",
        "Date: 2026-06-26",
        "",
        "## Decision",
        "",
        f"`{decision['status']}`",
        "",
        decision["detail"],
        "",
        "Stage96 records the provenance boundary between `origin/main` and the",
        "local PVW/MAT-SAB optimization chain. It is not a new benchmark and does",
        "not upgrade novelty, theorem-level 2025/686, or MAT-AVX512 optimality claims.",
        "",
        "## Gates",
        "",
        "| gate | status | evidence | detail | next action |",
        "|---|---|---|---|---|",
    ]
    for item in summary:
        lines.append(
            f"| {item['gate']} | {item['status']} | {esc(item['evidence'])} | {esc(item['detail'])} | {esc(item['next_action'])} |"
        )
    lines.extend([
        "",
        "## Delta By Area",
        "",
        "| area | changed files | hotpath source files | interpretation |",
        "|---|---:|---:|---|",
    ])
    for item in delta_by_area:
        lines.append(
            f"| {item['area']} | {item['changed_files']} | {item['hotpath_source_files']} | {esc(item['interpretation'])} |"
        )
    failed_flags = [item for item in flag_guard if item["status"] != "PASS_DEFAULT_FALSE"]
    lines.extend([
        "",
        "## Flag Guard",
        "",
        "All tracked PVW/MAT-SAB experiment flags remain default-false."
        if not failed_flags else f"Flag guard failures: {', '.join(item['flag'] for item in failed_flags)}",
    ])
    OUT_MD.write_text("\n".join(lines) + "\n", encoding="utf-8", newline="\n")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("--out-dir", default=str(DEFAULT_OUT))
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    out_dir = Path(args.out_dir)
    if not out_dir.is_absolute():
        out_dir = ROOT / out_dir
    delta_files = build_delta_files()
    delta_by_area = build_delta_by_area(delta_files)
    commits = build_commit_range()
    flag_guard = build_flag_guard()
    summary = build_summary(out_dir, delta_files, delta_by_area, flag_guard)
    index = artifact_rows(out_dir)
    write_csv(out_dir / "delta_files.csv", delta_files, ["path", "area", "is_hotpath_source"])
    write_csv(out_dir / "delta_by_area.csv", delta_by_area, [
        "area",
        "changed_files",
        "hotpath_source_files",
        "interpretation",
    ])
    write_csv(out_dir / "commit_range.csv", commits, ["ordinal_from_head", "commit", "subject"])
    write_csv(out_dir / "flag_guard.csv", flag_guard, [
        "flag",
        "expected_default",
        "status",
        "evidence",
        "detail",
    ])
    write_csv(out_dir / "summary.csv", summary, ["gate", "status", "evidence", "detail", "next_action"])
    write_csv(out_dir / "artifact_index.csv", index, ["artifact", "purpose", "producer"])
    write_md(out_dir, summary, delta_by_area, flag_guard)
    decision = summary[-1]["status"]
    print(f"Wrote {rel(out_dir / 'summary.csv')}")
    print(f"Wrote {rel(out_dir / 'delta_by_area.csv')}")
    print(f"Wrote {rel(OUT_MD)}")
    print(f"Stage96 upstream delta audit: {decision}")
    return 0 if decision.startswith("PASS_") else 1


if __name__ == "__main__":
    raise SystemExit(main())
