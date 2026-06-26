#!/usr/bin/env python3
"""Build the Stage97 source-delta isolation guard."""

from __future__ import annotations

import argparse
import csv
import subprocess
from pathlib import Path
from typing import Dict, Iterable, List, Sequence


ROOT = Path(__file__).resolve().parents[1]
DEFAULT_OUT = ROOT / "repro" / "stage97_source_delta_guard"
OUT_MD = ROOT / "docs" / "stage97_source_delta_guard_log.md"

STAGE96 = ROOT / "repro" / "stage96_upstream_delta_audit" / "summary.csv"
STAGE33_SMOKE = ROOT / "repro" / "stage33_current_smoke" / "summary.csv"
STAGE89_SMOKE = (
    ROOT
    / "repro"
    / "stage89_h14_promotion_policy_integration"
    / "current_smoke"
    / "summary.csv"
)
MAKEFILE_DEF = ROOT / "src" / "mosfhet" / "Makefile.def"

SCALAR_FILES = [
    ROOT / "include" / "sab.h",
    ROOT / "include" / "sab_b.h",
    ROOT / "src" / "sparse_amortized_bootstrap.c",
    ROOT / "src" / "sparse_amortized_bootstrap_b.c",
]

SHARED_BACKEND_FILES = [
    ROOT / "src" / "mosfhet" / "src" / "bootstrap.c",
    ROOT / "src" / "mosfhet" / "src" / "keyswitch.c",
    ROOT / "src" / "mosfhet" / "src" / "trgsw.c",
    ROOT / "src" / "mosfhet" / "src" / "trlwe.c",
    ROOT / "src" / "mosfhet" / "src" / "polynomial.c",
    ROOT / "src" / "mosfhet" / "src" / "misc.c",
]

PVW_MAT_FILES = [
    ROOT / "include" / "sab_pvw.h",
    ROOT / "src" / "sab_pvw.c",
    ROOT / "src" / "mosfhet" / "src" / "mattrgsw.c",
    ROOT / "src" / "mosfhet" / "src" / "pvwtlwe.c",
    ROOT / "src" / "mosfhet" / "src" / "pvwtmlwe.c",
]

DEFAULT_FALSE_FLAGS = [
    "ENABLE_PVW_TMLWE",
    "MAT_TRGSW_AVX512_SMALLR_SPECIALIZED",
    "MAT_TRGSW_AVX512_R4_UNROLLED_ROWS",
    "MAT_TRGSW_AVX512_RGT4_FUSED",
    "MAT_TRGSW_AVX512_R6_FULLTILE",
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
    "SAB_PROFILE",
    "SAB_MICROBENCH",
]

SCALAR_FORBIDDEN_TOKENS = ["SAB_PVW", "sab_pvw", "PVW_TMLWE", "MAT_TRGSW"]
SHARED_BACKEND_FORBIDDEN_TOKENS = ["SAB_PVW", "sab_pvw"]


def rel(path: Path) -> str:
    return path.relative_to(ROOT).as_posix()


def read_csv(path: Path) -> List[Dict[str, str]]:
    if not path.exists():
        return []
    with path.open(newline="", encoding="utf-8-sig") as f:
        return list(csv.DictReader(f))


def write_csv(path: Path, rows: Iterable[Dict[str, str]], fields: Sequence[str]) -> None:
    rows = list(rows)
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=list(fields), lineterminator="\n")
        writer.writeheader()
        writer.writerows(rows)


def git_lines(args: Sequence[str]) -> List[str]:
    proc = subprocess.run(
        ["git", *args],
        cwd=ROOT,
        text=True,
        capture_output=True,
        check=False,
    )
    if proc.returncode != 0:
        return []
    return [line for line in proc.stdout.splitlines() if line.strip()]


def status_of(path: Path, key_field: str, key: str, status_field: str = "status") -> str:
    rows = {row.get(key_field, ""): row for row in read_csv(path)}
    return rows.get(key, {}).get(status_field, "MISSING")


def source_area(path: str) -> str:
    norm = path.replace("\\", "/")
    if norm in {"main.c", "Makefile"}:
        return "top_level_harness"
    if norm in {"include/sab.h", "include/sab_b.h"}:
        return "scalar_sab_api"
    if norm in {"src/sparse_amortized_bootstrap.c", "src/sparse_amortized_bootstrap_b.c"}:
        return "scalar_sab_impl"
    if norm in {"include/sab_pvw.h", "src/sab_pvw.c"}:
        return "pvw_sab_path"
    if "mattrgsw" in norm or "pvw" in norm:
        return "pvw_mat_kernel"
    if norm.startswith("src/mosfhet/src/fft/"):
        return "fft_backend"
    if norm.startswith("src/mosfhet/"):
        return "shared_mosfhet_backend"
    if norm.startswith("include/") or norm.startswith("src/"):
        return "other_source"
    return "other"


def build_source_delta() -> List[Dict[str, str]]:
    name_status = git_lines(["diff", "--name-status", "origin/main..HEAD", "--", "main.c", "include", "src"])
    numstat = git_lines(["diff", "--numstat", "origin/main..HEAD", "--", "main.c", "include", "src"])
    stats: Dict[str, Dict[str, str]] = {}
    for line in numstat:
        parts = line.split("\t")
        if len(parts) >= 3:
            stats[parts[2]] = {"insertions": parts[0], "deletions": parts[1]}

    rows: List[Dict[str, str]] = []
    for line in name_status:
        parts = line.split("\t")
        status = parts[0]
        path = parts[-1] if parts else ""
        stat = stats.get(path, {"insertions": "", "deletions": ""})
        rows.append(
            {
                "path": path,
                "git_status": status,
                "area": source_area(path),
                "insertions": stat["insertions"],
                "deletions": stat["deletions"],
                "guard_relevance": guard_relevance(path),
            }
        )
    return rows


def guard_relevance(path: str) -> str:
    norm = path.replace("\\", "/")
    if norm in {rel(p) for p in SCALAR_FILES}:
        return "scalar_symbol_guarded"
    if norm in {rel(p) for p in SHARED_BACKEND_FILES}:
        return "shared_backend_symbol_guarded"
    if norm in {rel(p) for p in PVW_MAT_FILES}:
        return "explicit_pvw_mat_path"
    if norm == "src/mosfhet/Makefile.def":
        return "build_flag_guarded"
    if norm == "main.c":
        return "harness_guarded_by_smoke"
    return "record_only"


def scan_tokens(paths: Sequence[Path], forbidden_tokens: Sequence[str], scope: str) -> List[Dict[str, str]]:
    rows: List[Dict[str, str]] = []
    for path in paths:
        if not path.exists():
            rows.append(
                {
                    "scope": scope,
                    "file": rel(path),
                    "forbidden_tokens": " ".join(forbidden_tokens),
                    "status": "FAIL_FILE_MISSING",
                    "detail": "file missing",
                }
            )
            continue
        text = path.read_text(encoding="utf-8", errors="ignore")
        hits = [token for token in forbidden_tokens if token in text]
        rows.append(
            {
                "scope": scope,
                "file": rel(path),
                "forbidden_tokens": " ".join(forbidden_tokens),
                "status": "PASS_NO_FORBIDDEN_SYMBOLS" if not hits else "FAIL_FORBIDDEN_SYMBOLS",
                "detail": "no forbidden symbols" if not hits else "hits=" + ",".join(hits),
            }
        )
    return rows


def build_flag_guard() -> List[Dict[str, str]]:
    text = MAKEFILE_DEF.read_text(encoding="utf-8") if MAKEFILE_DEF.exists() else ""
    rows: List[Dict[str, str]] = []
    for flag in DEFAULT_FALSE_FLAGS:
        token = f"{flag} ?= false"
        rows.append(
            {
                "guard": "default_false",
                "flag": flag,
                "status": "PASS_DEFAULT_FALSE" if token in text else "FAIL_DEFAULT_NOT_FALSE",
                "evidence": rel(MAKEFILE_DEF),
                "detail": token if token in text else f"missing token: {token}",
            }
        )

    src_token = "__SRC += pvwtmlwe.c mattrgsw.c"
    enable_token = "ifeq ($(ENABLE_PVW_TMLWE),true)"
    src_pos = text.find(src_token)
    prior_enable = text.rfind(enable_token, 0, src_pos) if src_pos >= 0 else -1
    prior_endif = text.rfind("endif", 0, src_pos) if src_pos >= 0 else -1
    gated = src_pos >= 0 and prior_enable >= 0 and prior_enable > prior_endif
    rows.append(
        {
            "guard": "pvw_sources_gated",
            "flag": "ENABLE_PVW_TMLWE",
            "status": "PASS_PVW_SOURCES_GATED" if gated else "FAIL_PVW_SOURCES_NOT_GATED",
            "evidence": rel(MAKEFILE_DEF),
            "detail": "pvwtmlwe.c/mattrgsw.c appear under ENABLE_PVW_TMLWE"
            if gated
            else "could not prove pvwtmlwe.c/mattrgsw.c are gated by ENABLE_PVW_TMLWE",
        }
    )
    return rows


def build_smoke_evidence() -> List[Dict[str, str]]:
    checks = [
        (
            "stage33_scalar_binary_full_run",
            STAGE33_SMOKE,
            "step",
            "scalar_binary_full_run",
            "PASS",
        ),
        (
            "stage33_scalar_ternary_build",
            STAGE33_SMOKE,
            "step",
            "scalar_ternary_build",
            "PASS",
        ),
        (
            "stage89_scalar_binary_full_run",
            STAGE89_SMOKE,
            "step",
            "scalar_binary_full_run",
            "PASS",
        ),
        (
            "stage89_scalar_ternary_build",
            STAGE89_SMOKE,
            "step",
            "scalar_ternary_build",
            "PASS",
        ),
    ]
    rows = []
    for check_id, path, key_field, key, expected in checks:
        got = status_of(path, key_field, key)
        rows.append(
            {
                "check": check_id,
                "expected_status": expected,
                "actual_status": got,
                "status": "PASS_SMOKE_EVIDENCE" if got == expected else "FAIL_SMOKE_EVIDENCE",
                "evidence": rel(path),
                "detail": f"{key}={got}",
            }
        )
    return rows


def summary_row(gate: str, status: str, evidence: str, detail: str, next_action: str) -> Dict[str, str]:
    return {
        "gate": gate,
        "status": status,
        "evidence": evidence,
        "detail": detail,
        "next_action": next_action,
    }


def build_summary(
    out_dir: Path,
    source_delta: List[Dict[str, str]],
    symbol_guard: List[Dict[str, str]],
    flag_guard: List[Dict[str, str]],
    smoke_evidence: List[Dict[str, str]],
) -> List[Dict[str, str]]:
    stage96_status = status_of(STAGE96, "gate", "stage96_decision")
    stage96_ok = stage96_status == "PASS_STAGE96_UPSTREAM_DELTA_AUDIT_LOCAL_PROVENANCE_RECORDED"
    scalar_ok = all(
        row["status"] == "PASS_NO_FORBIDDEN_SYMBOLS"
        for row in symbol_guard
        if row["scope"] == "scalar_sab"
    )
    backend_ok = all(
        row["status"] == "PASS_NO_FORBIDDEN_SYMBOLS"
        for row in symbol_guard
        if row["scope"] == "shared_backend"
    )
    flags_ok = all(row["status"].startswith("PASS_") for row in flag_guard)
    smoke_ok = all(row["status"] == "PASS_SMOKE_EVIDENCE" for row in smoke_evidence)
    areas = sorted({row["area"] for row in source_delta})
    pvw_changed = sum(1 for row in source_delta if row["area"] in {"pvw_sab_path", "pvw_mat_kernel"})
    scalar_guarded = sum(1 for row in source_delta if row["guard_relevance"] == "scalar_symbol_guarded")

    rows = [
        summary_row(
            "stage97_stage96_precondition",
            "PASS" if stage96_ok else "FAIL_STAGE96_PRECONDITION",
            rel(STAGE96),
            f"stage96_decision={stage96_status}",
            "Refresh Stage96 before interpreting source isolation evidence.",
        ),
        summary_row(
            "stage97_source_delta_inventory",
            "PASS_SOURCE_DELTA_CLASSIFIED" if source_delta else "FAIL_SOURCE_DELTA_EMPTY",
            rel(out_dir / "source_delta.csv"),
            f"changed_source_files={len(source_delta)}; areas={','.join(areas)}; pvw_or_mat_files={pvw_changed}; scalar_guarded_files={scalar_guarded}",
            "Inspect source_delta.csv whenever source or backend files change.",
        ),
        summary_row(
            "stage97_scalar_symbol_guard",
            "PASS_SCALAR_SYMBOLS_ISOLATED" if scalar_ok else "FAIL_SCALAR_SYMBOL_GUARD",
            rel(out_dir / "symbol_guard.csv"),
            "scalar SAB files contain no PVW/MAT-SAB forbidden symbols"
            if scalar_ok
            else "scalar SAB file contains a forbidden PVW/MAT-SAB token",
            "Do not continue optimization until scalar/default route separation is restored.",
        ),
        summary_row(
            "stage97_shared_backend_symbol_guard",
            "PASS_SHARED_BACKEND_SYMBOLS_ISOLATED" if backend_ok else "FAIL_SHARED_BACKEND_SYMBOL_GUARD",
            rel(out_dir / "symbol_guard.csv"),
            "selected shared backend files contain no sab_pvw symbols"
            if backend_ok
            else "selected shared backend file contains a sab_pvw token",
            "Audit shared backend changes and rerun scalar/default smoke.",
        ),
        summary_row(
            "stage97_build_flag_guard",
            "PASS_BUILD_FLAGS_DEFAULT_FALSE_AND_GATED" if flags_ok else "FAIL_BUILD_FLAG_GUARD",
            rel(out_dir / "build_flag_guard.csv"),
            "all tracked flags are default-false and PVW/MAT sources are gated"
            if flags_ok
            else "one or more flags are not default-false or PVW/MAT sources are not gated",
            "Rerun scalar/PVW correctness, performance, noise, and resource gates if any default changes.",
        ),
        summary_row(
            "stage97_smoke_evidence_guard",
            "PASS_SCALAR_SMOKE_EVIDENCE_PRESENT" if smoke_ok else "FAIL_SCALAR_SMOKE_EVIDENCE",
            rel(out_dir / "smoke_evidence.csv"),
            "Stage33 and Stage89 scalar binary/ternary smoke rows are present and passing"
            if smoke_ok
            else "one or more scalar/default smoke evidence rows is missing or failing",
            "Rerun current smoke before claiming source-delta continuity.",
        ),
        summary_row(
            "stage97_claim_guard",
            "PASS_SOURCE_GUARD_ONLY_NO_SPEEDUP_CLAIM",
            "docs/stage97_source_delta_guard_log.md",
            "Stage97 records source isolation and continuity evidence only; it is not a performance, theorem, novelty, or hardware-counter claim.",
            "Keep Stage97 out of speedup tables except as a guardrail/reproducibility row.",
        ),
    ]
    ok = all(row["status"].startswith("PASS") for row in rows)
    rows.append(
        summary_row(
            "stage97_decision",
            "PASS_STAGE97_SOURCE_DELTA_GUARD_SCALAR_DEFAULT_SEPARATED"
            if ok
            else "REVIEW_STAGE97_SOURCE_DELTA_GUARD",
            rel(out_dir / "summary.csv"),
            "Source-delta, symbol, flag, and smoke-evidence guards preserve scalar/default separation under the current local PVW/MAT-SAB evidence chain."
            if ok
            else "Inspect failed Stage97 gates before continuing to source or hot-path changes.",
            "Use Stage97 as the pre-flight guard for subsequent local optimization stages.",
        )
    )
    return rows


def artifact_rows(out_dir: Path) -> List[Dict[str, str]]:
    return [
        {"artifact": rel(out_dir / "summary.csv"), "purpose": "Stage97 gate summary", "producer": "scripts/build_stage97_source_delta_guard.py"},
        {"artifact": rel(out_dir / "source_delta.csv"), "purpose": "Source delta inventory against origin/main", "producer": "scripts/build_stage97_source_delta_guard.py"},
        {"artifact": rel(out_dir / "symbol_guard.csv"), "purpose": "Scalar/shared-backend forbidden symbol scan", "producer": "scripts/build_stage97_source_delta_guard.py"},
        {"artifact": rel(out_dir / "build_flag_guard.csv"), "purpose": "Default-false and source-gating flag guard", "producer": "scripts/build_stage97_source_delta_guard.py"},
        {"artifact": rel(out_dir / "smoke_evidence.csv"), "purpose": "Current scalar/default smoke evidence guard", "producer": "scripts/build_stage97_source_delta_guard.py"},
        {"artifact": rel(out_dir / "artifact_index.csv"), "purpose": "Stage97 artifact index", "producer": "scripts/build_stage97_source_delta_guard.py"},
        {"artifact": rel(OUT_MD), "purpose": "Human-readable Stage97 log", "producer": "scripts/build_stage97_source_delta_guard.py"},
    ]


def esc(value: str) -> str:
    return value.replace("|", "\\|").replace("\n", " ")


def write_md(
    summary: List[Dict[str, str]],
    source_delta: List[Dict[str, str]],
    symbol_guard: List[Dict[str, str]],
    flag_guard: List[Dict[str, str]],
    smoke_evidence: List[Dict[str, str]],
) -> None:
    decision = summary[-1]
    area_counts: Dict[str, int] = {}
    for row in source_delta:
        area_counts[row["area"]] = area_counts.get(row["area"], 0) + 1
    lines = [
        "# Stage97 Source Delta Guard Log",
        "",
        "Date: 2026-06-26",
        "",
        "## Decision",
        "",
        f"`{decision['status']}`",
        "",
        decision["detail"],
        "",
        "Stage97 is a source-isolation and reproducibility guard. It does not",
        "implement a new SAB variant, run a new benchmark, or upgrade any",
        "theorem-level, novelty, speedup, or hardware-counter claim.",
        "",
        "## Gates",
        "",
        "| gate | status | evidence | detail | next action |",
        "|---|---|---|---|---|",
    ]
    for row in summary:
        lines.append(
            f"| {row['gate']} | {row['status']} | {esc(row['evidence'])} | {esc(row['detail'])} | {esc(row['next_action'])} |"
        )
    lines.extend(["", "## Source Delta By Area", "", "| area | changed source files |", "|---|---:|"])
    for area in sorted(area_counts):
        lines.append(f"| {area} | {area_counts[area]} |")
    failed_symbols = [row for row in symbol_guard if not row["status"].startswith("PASS")]
    failed_flags = [row for row in flag_guard if not row["status"].startswith("PASS")]
    failed_smoke = [row for row in smoke_evidence if not row["status"].startswith("PASS")]
    lines.extend(
        [
            "",
            "## Guard Failures",
            "",
            "- symbol guard: " + ("none" if not failed_symbols else ", ".join(row["file"] for row in failed_symbols)),
            "- build flag guard: " + ("none" if not failed_flags else ", ".join(row["flag"] for row in failed_flags)),
            "- smoke evidence guard: " + ("none" if not failed_smoke else ", ".join(row["check"] for row in failed_smoke)),
            "",
        ]
    )
    OUT_MD.parent.mkdir(parents=True, exist_ok=True)
    OUT_MD.write_text("\n".join(lines), encoding="utf-8", newline="\n")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("--out-dir", default=str(DEFAULT_OUT))
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    out_dir = Path(args.out_dir)
    if not out_dir.is_absolute():
        out_dir = ROOT / out_dir

    source_delta = build_source_delta()
    symbol_guard = scan_tokens(SCALAR_FILES, SCALAR_FORBIDDEN_TOKENS, "scalar_sab")
    symbol_guard.extend(
        scan_tokens(SHARED_BACKEND_FILES, SHARED_BACKEND_FORBIDDEN_TOKENS, "shared_backend")
    )
    flag_guard = build_flag_guard()
    smoke_evidence = build_smoke_evidence()
    summary = build_summary(out_dir, source_delta, symbol_guard, flag_guard, smoke_evidence)
    index = artifact_rows(out_dir)

    write_csv(
        out_dir / "source_delta.csv",
        source_delta,
        ["path", "git_status", "area", "insertions", "deletions", "guard_relevance"],
    )
    write_csv(
        out_dir / "symbol_guard.csv",
        symbol_guard,
        ["scope", "file", "forbidden_tokens", "status", "detail"],
    )
    write_csv(
        out_dir / "build_flag_guard.csv",
        flag_guard,
        ["guard", "flag", "status", "evidence", "detail"],
    )
    write_csv(
        out_dir / "smoke_evidence.csv",
        smoke_evidence,
        ["check", "expected_status", "actual_status", "status", "evidence", "detail"],
    )
    write_csv(
        out_dir / "summary.csv",
        summary,
        ["gate", "status", "evidence", "detail", "next_action"],
    )
    write_csv(out_dir / "artifact_index.csv", index, ["artifact", "purpose", "producer"])
    write_md(summary, source_delta, symbol_guard, flag_guard, smoke_evidence)

    decision = summary[-1]["status"]
    print(f"Wrote {rel(out_dir / 'summary.csv')}")
    print(f"Wrote {rel(out_dir / 'source_delta.csv')}")
    print(f"Wrote {rel(OUT_MD)}")
    print(f"Stage97 source delta guard: {decision}")
    return 0 if decision.startswith("PASS_") else 1


if __name__ == "__main__":
    raise SystemExit(main())
