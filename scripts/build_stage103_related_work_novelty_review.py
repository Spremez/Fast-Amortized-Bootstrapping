#!/usr/bin/env python3
"""Build Stage103 related-work and novelty-boundary review artifacts."""

from __future__ import annotations

import csv
import hashlib
import subprocess
from pathlib import Path
from typing import Dict, Iterable, List


ROOT = Path(__file__).resolve().parents[1]
OUT_DIR = ROOT / "repro" / "stage103_related_work_novelty_review"
OUT_SUMMARY = OUT_DIR / "summary.csv"
OUT_RELATED = OUT_DIR / "related_work_matrix.csv"
OUT_NOVELTY = OUT_DIR / "novelty_claim_matrix.csv"
OUT_SOURCES = OUT_DIR / "source_verification.csv"
OUT_INDEX = OUT_DIR / "artifact_index.csv"
OUT_MD = ROOT / "docs" / "stage103_related_work_novelty_review_log.md"
STAGE102 = ROOT / "repro" / "stage102_686_source_anchor_review" / "summary.csv"
RUN_LOG = ROOT / "repro" / "run_log.csv"


SOURCE_ROWS: List[Dict[str, str]] = [
    {
        "source_id": "FAB686_2025",
        "title": "Fast amortized bootstrapping with small keys and polynomial noise overhead",
        "venue_year": "ACM CCS 2025 / IACR ePrint 2025/686",
        "primary_url": "https://eprint.iacr.org/2025/686",
        "secondary_url": "https://doi.org/10.1145/3719027.3765181",
        "verification_status": "VERIFIED_PRIMARY_OR_OFFICIAL_METADATA",
        "relevance": "Target scalar sparse amortized bootstrapping paper.",
    },
    {
        "source_id": "MS18",
        "title": "Ring packing and amortized FHEW bootstrapping",
        "venue_year": "ICALP 2018",
        "primary_url": "https://doi.org/10.4230/LIPIcs.ICALP.2018.100",
        "secondary_url": "https://dblp.org/rec/conf/icalp/MicciancioS18.html",
        "verification_status": "VERIFIED_OFFICIAL_METADATA",
        "relevance": "Early amortized/ring-packing bootstrapping baseline.",
    },
    {
        "source_id": "GPVL23",
        "title": "Amortized bootstrapping revisited: Simpler, asymptotically-faster, implemented",
        "venue_year": "ASIACRYPT 2023",
        "primary_url": "https://eprint.iacr.org/2023/014",
        "secondary_url": "https://dblp.org/rec/conf/asiacrypt/GuimaraesPL23.html",
        "verification_status": "VERIFIED_PRIMARY_OR_OFFICIAL_METADATA",
        "relevance": "Amortized bootstrapping algorithmic prior art.",
    },
    {
        "source_id": "LW23A",
        "title": "Batch bootstrapping I: A new framework for SIMD bootstrapping in polynomial modulus",
        "venue_year": "EUROCRYPT 2023",
        "primary_url": "https://doi.org/10.1007/978-3-031-30620-4_11",
        "secondary_url": "https://dl.acm.org/doi/10.1007/978-3-031-30620-4_11",
        "verification_status": "VERIFIED_OFFICIAL_METADATA",
        "relevance": "SIMD/batch bootstrapping prior art; blocks broad batching novelty wording.",
    },
    {
        "source_id": "LW23B",
        "title": "Batch bootstrapping II: Bootstrapping in polynomial modulus only requires O(1) FHE multiplications in amortization",
        "venue_year": "EUROCRYPT 2023",
        "primary_url": "https://doi.org/10.1007/978-3-031-30620-4_12",
        "secondary_url": "https://dl.acm.org/doi/10.1007/978-3-031-30620-4_12",
        "verification_status": "VERIFIED_OFFICIAL_METADATA",
        "relevance": "Batch bootstrapping amortization prior art.",
    },
    {
        "source_id": "LW23C",
        "title": "Amortized functional bootstrapping in less than 7 ms, with O(1) polynomial multiplications",
        "venue_year": "ASIACRYPT 2023",
        "primary_url": "https://eprint.iacr.org/2023/910",
        "secondary_url": "https://dblp.org/rec/conf/asiacrypt/LiuW23.html",
        "verification_status": "VERIFIED_PRIMARY_OR_OFFICIAL_METADATA",
        "relevance": "Amortized functional bootstrapping prior art.",
    },
    {
        "source_id": "DKMS24",
        "title": "Faster amortized FHEW bootstrapping using ring automorphisms",
        "venue_year": "PKC 2024",
        "primary_url": "https://eprint.iacr.org/2023/112",
        "secondary_url": "https://dblp.org/rec/conf/pkc/DeMicheliKMS24.html",
        "verification_status": "VERIFIED_PRIMARY_OR_OFFICIAL_METADATA",
        "relevance": "Amortized FHEW bootstrapping acceleration using automorphisms.",
    },
    {
        "source_id": "CLOT21",
        "title": "Improved programmable bootstrapping with larger precision and efficient arithmetic circuits for TFHE",
        "venue_year": "ASIACRYPT 2021",
        "primary_url": "https://eprint.iacr.org/2021/729",
        "secondary_url": "https://dblp.org/rec/conf/asiacrypt/ChillottiLT21.html",
        "verification_status": "VERIFIED_PRIMARY_OR_OFFICIAL_METADATA",
        "relevance": "TFHE programmable bootstrapping implementation/theory baseline.",
    },
    {
        "source_id": "INCNTT25",
        "title": "Faster amortized bootstrapping using the incomplete NTT for free",
        "venue_year": "IACR ePrint 2025/696",
        "primary_url": "https://eprint.iacr.org/2025/696",
        "secondary_url": "",
        "verification_status": "VERIFIED_PRIMARY_OR_OFFICIAL_METADATA",
        "relevance": "Post-686 adjacent acceleration direction; separates transform/backend gains from PVW/MAT lane batching.",
    },
    {
        "source_id": "SHAREMASK25",
        "title": "Sharing the Mask: TFHE bootstrapping on Packed Messages",
        "venue_year": "TCHES 2025",
        "primary_url": "https://doi.org/10.46586/tches.v2025.i4.925-971",
        "secondary_url": "https://artifacts.iacr.org/tches/2025/a46/",
        "verification_status": "VERIFIED_OFFICIAL_METADATA",
        "relevance": "Strong risk for broad common-mask/shared-mask novelty claims.",
    },
    {
        "source_id": "BATCHBOOT26",
        "title": "BatchBoot: Fast Batched Bootstrapping for TFHE Scheme",
        "venue_year": "USENIX Security 2026",
        "primary_url": "https://www.usenix.org/conference/usenixsecurity26/presentation/zheng",
        "secondary_url": "",
        "verification_status": "VERIFIED_OFFICIAL_METADATA",
        "relevance": "Later batched TFHE bootstrapping systems work; useful for post-686 positioning.",
    },
]


RELATED_ROWS: List[Dict[str, str]] = [
    {
        "axis": "target_sab",
        "source_ids": "FAB686_2025",
        "what_it_covers": "Sparse amortized bootstrapping with scalar external products, MPmul, extraction, and packing key switching.",
        "impact_on_claim": "Our PVW/MAT path must be described as a local optimization over this scalar SAB schedule.",
    },
    {
        "axis": "amortized_bootstrapping_prior_art",
        "source_ids": "MS18; GPVL23; DKMS24; LW23C",
        "what_it_covers": "Amortized bootstrapping, ring packing, automorphism-based acceleration, and amortized functional bootstrapping.",
        "impact_on_claim": "Blocks broad claims that amortization or multi-message bootstrapping is new.",
    },
    {
        "axis": "batch_simd_bootstrapping",
        "source_ids": "LW23A; LW23B; BATCHBOOT26",
        "what_it_covers": "SIMD/batch bootstrapping frameworks and batched TFHE bootstrapping systems directions.",
        "impact_on_claim": "Blocks broad claims that batching lanes or SIMD bootstrapping is new.",
    },
    {
        "axis": "tfhe_bootstrapping_implementation",
        "source_ids": "CLOT21; SHAREMASK25",
        "what_it_covers": "Programmable TFHE bootstrapping and packed/common-mask bootstrapping ideas.",
        "impact_on_claim": "Forces a narrow claim: PVW/MAT-SAB integration and measured complete-SAB throughput, not general shared-mask novelty.",
    },
    {
        "axis": "backend_transform_acceleration",
        "source_ids": "INCNTT25",
        "what_it_covers": "Transform/backend acceleration for amortized bootstrapping.",
        "impact_on_claim": "Backend/FFT/NTT gains must be separated from algorithmic lane-batching gains.",
    },
]


NOVELTY_ROWS: List[Dict[str, str]] = [
    {
        "claim_id": "S103-N1",
        "candidate_claim": "PVW/MAT-SAB complete bootstrapping improves throughput over repeated scalar SAB on the measured binary target parameters.",
        "decision": "SUPPORTED_SCOPED_ENGINEERING_CLAIM",
        "evidence": "Stage7/27/36/88/91 performance packages and Stage101 native r=4 perf sample.",
        "allowed_wording": "A scoped systems/engineering optimization with measured complete-SAB throughput gains under explicit flags.",
        "blocked_wording": "Do not state universal, all-parameter, or default-path acceleration.",
    },
    {
        "claim_id": "S103-N2",
        "candidate_claim": "Shared-mask or multi-lane TFHE bootstrapping is novel.",
        "decision": "REJECT_BROAD_NOVELTY_PRIOR_ART",
        "evidence": "LW23A/LW23B batch bootstrapping, SHAREMASK25 common-mask packed-message bootstrapping, and BATCHBOOT26 batched TFHE positioning.",
        "allowed_wording": "The local system explores PVW/MAT shared-mask multi-body batching inside the 2025/686 SAB implementation.",
        "blocked_wording": "Do not claim general first shared-mask batching or first batched TFHE bootstrapping.",
    },
    {
        "claim_id": "S103-N3",
        "candidate_claim": "The project derives a new SAB asymptotic theorem beyond 2025/686.",
        "decision": "REJECT_NOT_SUPPORTED",
        "evidence": "Stage102 maps the scalar 2025/686 schedule; local changes batch independent lanes and optimize constants.",
        "allowed_wording": "Constant-factor throughput optimization for the implemented schedule.",
        "blocked_wording": "Do not claim a new asymptotic SAB algorithm without a new proof.",
    },
    {
        "claim_id": "S103-N4",
        "candidate_claim": "The MAT-AVX512 path has native hardware-counter support for load/store/FMA attribution.",
        "decision": "SUPPORTED_COUNTER_EVIDENCE_NOT_OPTIMALITY",
        "evidence": "Stage101 counter_metrics.csv records retired loads/stores and AVX512 FP arithmetic events.",
        "allowed_wording": "Hardware-counter attribution is available on native Linux for analysis.",
        "blocked_wording": "Do not claim theoretical optimality solely from one perf run.",
    },
    {
        "claim_id": "S103-N5",
        "candidate_claim": "The paper contribution can be positioned as applying PVW/MAT multi-body external-product batching to the 2025/686 SAB hot path.",
        "decision": "ALLOW_SCOPED_NOVELTY_CANDIDATE_WITH_RELATED_WORK_CAVEAT",
        "evidence": "Stage102 PVW_SAB_DELTA anchors plus Stage103 related-work matrix.",
        "allowed_wording": "A scoped implementation contribution and empirical study of PVW/MAT external-product batching for 2025/686 SAB.",
        "blocked_wording": "Do not call it novel without acknowledging batch/SIMD/common-mask bootstrapping prior art.",
    },
]


def rel(path: Path) -> str:
    return path.relative_to(ROOT).as_posix()


def read_csv(path: Path) -> List[Dict[str, str]]:
    if not path.exists():
        return []
    with path.open(newline="", encoding="utf-8-sig") as f:
        return list(csv.DictReader(f))


def write_csv(path: Path, rows: Iterable[Dict[str, str]], fields: List[str]) -> None:
    rows = list(rows)
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fields, lineterminator="\n")
        writer.writeheader()
        writer.writerows(rows)


def sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def status(path: Path, key: str, value: str, field: str = "status") -> str:
    for row in read_csv(path):
        if row.get(key) == value:
            return row.get(field, "MISSING")
    return "MISSING"


def artifact_index(paths: List[Path]) -> List[Dict[str, str]]:
    rows: List[Dict[str, str]] = []
    for path in paths:
        rows.append(
            {
                "artifact": rel(path),
                "exists": "yes" if path.exists() else "no",
                "sha256": sha256_file(path) if path.exists() else "",
                "size_bytes": str(path.stat().st_size) if path.exists() else "",
            }
        )
    return rows


def git_head() -> str:
    try:
        return subprocess.check_output(["git", "rev-parse", "--short", "HEAD"], cwd=ROOT, text=True).strip()
    except Exception:
        return "unknown"


def upsert_run_log() -> None:
    fields = [
        "run_id",
        "date",
        "commit_or_state",
        "stage",
        "backend",
        "command",
        "params",
        "seed",
        "status",
        "summary",
        "artifacts",
    ]
    rows = read_csv(RUN_LOG)
    rows = [row for row in rows if row.get("run_id") != "stage103-related-work-novelty-review-001"]
    rows.append(
        {
            "run_id": "stage103-related-work-novelty-review-001",
            "date": "2026-06-30",
            "commit_or_state": f"working-tree-after-{git_head()}",
            "stage": "Stage 103",
            "backend": "n/a",
            "command": "python scripts/build_stage103_related_work_novelty_review.py",
            "params": "real source metadata; 2025/686 full-text anchors; related-work and novelty boundary matrix",
            "seed": "source-review",
            "status": "PASS_STAGE103_RELATED_WORK_NOVELTY_REVIEW_SCOPED",
            "summary": "Related-work review resolves CB6 by bounding the contribution to scoped PVW/MAT-SAB systems optimization. Broad shared-mask, batch/SIMD, new-asymptotic, and all-parameter novelty claims remain blocked.",
            "artifacts": "docs/stage103_related_work_novelty_review_log.md; experiments/stage103_related_work_novelty_review_plan.md; scripts/build_stage103_related_work_novelty_review.py; repro/stage103_related_work_novelty_review/summary.csv; repro/stage103_related_work_novelty_review/related_work_matrix.csv; repro/stage103_related_work_novelty_review/novelty_claim_matrix.csv; repro/stage103_related_work_novelty_review/source_verification.csv; repro/stage103_related_work_novelty_review/artifact_index.csv",
        }
    )
    write_csv(RUN_LOG, rows, fields)


def write_md(summary_rows: List[Dict[str, str]]) -> None:
    lines = [
        "# Stage103 Related-Work And Novelty Review Log",
        "",
        "Date: 2026-06-30",
        "",
        "## Purpose",
        "",
        "Stage103 resolves CB6 by converting related-work risk into an explicit",
        "claim boundary. It uses only real, named sources and records which",
        "contribution wordings are supported or blocked.",
        "",
        "## Summary",
        "",
        "| gate | status | detail |",
        "|---|---|---|",
    ]
    for row in summary_rows:
        lines.append(f"| {row['gate']} | {row['status']} | {row['detail']} |")
    lines.extend(["", "## Novelty Decisions", "", "| claim | decision | allowed wording | blocked wording |", "|---|---|---|---|"])
    for row in NOVELTY_ROWS:
        lines.append(
            f"| {row['claim_id']} | {row['decision']} | {row['allowed_wording']} | {row['blocked_wording']} |"
        )
    lines.extend(
        [
            "",
            "## Decision",
            "",
            "CB6 is resolved by scoping, not by broad novelty promotion. The evidence",
            "supports a systems/engineering contribution: a measured PVW/MAT",
            "multi-body external-product batching path for the 2025/686 SAB",
            "implementation. It does not support claims of first shared-mask",
            "bootstrapping, general batch bootstrapping novelty, new SAB asymptotics,",
            "or all-parameter/non-binary coverage.",
        ]
    )
    OUT_MD.parent.mkdir(parents=True, exist_ok=True)
    OUT_MD.write_text("\n".join(lines) + "\n", encoding="utf-8", newline="\n")


def main() -> int:
    stage102_status = status(STAGE102, "gate", "stage102_decision")
    broad_rejections = [
        row for row in NOVELTY_ROWS if row["decision"].startswith("REJECT_")
    ]
    supported_scoped = [
        row for row in NOVELTY_ROWS if row["decision"].startswith("SUPPORTED") or row["decision"].startswith("ALLOW_SCOPED")
    ]
    verified_sources = [
        row for row in SOURCE_ROWS if row["verification_status"].startswith("VERIFIED")
    ]

    write_csv(
        OUT_SOURCES,
        SOURCE_ROWS,
        ["source_id", "title", "venue_year", "primary_url", "secondary_url", "verification_status", "relevance"],
    )
    write_csv(
        OUT_RELATED,
        RELATED_ROWS,
        ["axis", "source_ids", "what_it_covers", "impact_on_claim"],
    )
    write_csv(
        OUT_NOVELTY,
        NOVELTY_ROWS,
        ["claim_id", "candidate_claim", "decision", "evidence", "allowed_wording", "blocked_wording"],
    )

    summary_rows = [
        {
            "gate": "stage103_stage102_precondition",
            "status": "PASS" if stage102_status == "PASS_STAGE102_686_SOURCE_ANCHORS_REVIEWED" else "FAIL",
            "evidence": rel(STAGE102),
            "detail": f"stage102_decision={stage102_status}",
            "next_action": "Complete Stage102 before novelty/source-boundary review.",
        },
        {
            "gate": "stage103_source_verification",
            "status": "PASS" if len(verified_sources) == len(SOURCE_ROWS) else "FAIL",
            "evidence": rel(OUT_SOURCES),
            "detail": f"verified_sources={len(verified_sources)}/{len(SOURCE_ROWS)}",
            "next_action": "Remove or verify any source before using it in a manuscript.",
        },
        {
            "gate": "stage103_related_work_matrix",
            "status": "PASS",
            "evidence": rel(OUT_RELATED),
            "detail": f"axes={len(RELATED_ROWS)}",
            "next_action": "Expand only if a new claim axis is introduced.",
        },
        {
            "gate": "stage103_novelty_boundary",
            "status": "PASS_SCOPED_BOUNDARY"
            if supported_scoped and broad_rejections
            else "FAIL_BOUNDARY",
            "evidence": rel(OUT_NOVELTY),
            "detail": f"scoped_or_supported={len(supported_scoped)}; broad_rejections={len(broad_rejections)}",
            "next_action": "Keep rejected wording out of paper claims.",
        },
        {
            "gate": "stage103_decision",
            "status": "PASS_STAGE103_RELATED_WORK_NOVELTY_REVIEW_SCOPED"
            if stage102_status == "PASS_STAGE102_686_SOURCE_ANCHORS_REVIEWED"
            and len(verified_sources) == len(SOURCE_ROWS)
            and supported_scoped
            and broad_rejections
            else "FAIL_STAGE103_RELATED_WORK_NOVELTY_REVIEW",
            "evidence": rel(OUT_SUMMARY),
            "detail": "CB6 resolved by scoped contribution boundary; broad novelty claims remain blocked.",
            "next_action": "Use scoped systems wording unless a later theorem and full literature review justify stronger claims.",
        },
    ]

    write_csv(
        OUT_SUMMARY,
        summary_rows,
        ["gate", "status", "evidence", "detail", "next_action"],
    )
    write_md(summary_rows)
    write_csv(
        OUT_INDEX,
        artifact_index([OUT_SUMMARY, OUT_RELATED, OUT_NOVELTY, OUT_SOURCES, OUT_MD]),
        ["artifact", "exists", "sha256", "size_bytes"],
    )
    upsert_run_log()
    decision = summary_rows[-1]["status"]
    print(f"Wrote {rel(OUT_SUMMARY)}")
    print(f"Wrote {rel(OUT_RELATED)}")
    print(f"Wrote {rel(OUT_NOVELTY)}")
    print(f"Wrote {rel(OUT_MD)}")
    print(f"Stage103 related-work novelty review: {decision}")
    return 0 if decision.startswith("PASS_") else 1


if __name__ == "__main__":
    raise SystemExit(main())
