#!/usr/bin/env python3
"""Stage333: verified related-work matrix and novelty-risk map."""

from __future__ import annotations

import csv
import hashlib
import subprocess
from pathlib import Path
from typing import Iterable


ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "repro" / "stage333_literature_novelty_verification"

DOC = ROOT / "docs" / "stage333_literature_novelty_verification.md"
THEORY = ROOT / "theory_checks" / "stage333_novelty_risk_model.md"
PLAN = ROOT / "experiments" / "stage334_fulltext_claim_audit_or_compact_security_plan.md"
BUILDER = ROOT / "scripts" / "build_stage333_literature_novelty_verification.py"
LIT_MATRIX = ROOT / "literature" / "related_literature_matrix.csv"

GOAL = ROOT / "docs" / "current_codex_goal_sab_completion.md"
ROADMAP = ROOT / "docs" / "roadmap_stage19_plus.md"
HYPOTHESES = ROOT / "hypotheses" / "hypothesis_register.yaml"
MANIFEST = ROOT / "repro" / "artifact_manifest.md"
CHECKLIST = ROOT / "repro" / "reproduction_checklist.md"
RUN_LOG = ROOT / "repro" / "run_log.csv"

SUMMARY = OUT / "summary.csv"
SEARCH = OUT / "search_strategy.csv"
MATRIX = OUT / "source_matrix.csv"
RISK = OUT / "novelty_risk_map.csv"
PROOF = OUT / "proof_gate.csv"
NEXT = OUT / "next_stage_queue.csv"
COMMANDS = OUT / "reproduction_commands.md"
REPORT = OUT / "stage333_report.md"
ARTIFACT = OUT / "artifact_index.csv"

DECISION = "PASS_STAGE333_REAL_SOURCE_MATRIX_NOVELTY_CLAIM_OPEN"


def rel(path: Path) -> str:
    return path.relative_to(ROOT).as_posix()


def read_text(path: Path) -> str:
    if not path.exists():
        return ""
    return (
        path.read_text(encoding="utf-8", errors="replace")
        .replace("\x00", "")
        .replace("\r\n", "\n")
        .replace("\r", "\n")
    )


def write_text(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text.rstrip() + "\n", encoding="utf-8", newline="\n")


def write_csv(path: Path, rows: Iterable[dict[str, object]], fields: list[str]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields, lineterminator="\n")
        writer.writeheader()
        for row in rows:
            writer.writerow({field: row.get(field, "") for field in fields})


def append_once(path: Path, marker: str, text: str) -> None:
    current = read_text(path)
    if marker in current:
        return
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("a", encoding="utf-8", newline="\n") as handle:
        if current and not current.endswith("\n"):
            handle.write("\n")
        handle.write(text.lstrip())
        if not text.endswith("\n"):
            handle.write("\n")


def git_head() -> str:
    try:
        return subprocess.check_output(["git", "rev-parse", "--short", "HEAD"], cwd=ROOT, text=True).strip()
    except (subprocess.CalledProcessError, FileNotFoundError):
        return "unknown"


def md_table(rows: list[dict[str, object]], fields: list[str]) -> str:
    out = ["| " + " | ".join(fields) + " |", "| " + " | ".join(["---"] * len(fields)) + " |"]
    for row in rows:
        out.append("| " + " | ".join(str(row.get(field, "")).replace("|", "\\|") for field in fields) + " |")
    return "\n".join(out)


def append_run_log() -> None:
    run_id = "stage333-literature-novelty-verification-001"
    if run_id in read_text(RUN_LOG):
        return
    if RUN_LOG.exists():
        with RUN_LOG.open(newline="", encoding="utf-8-sig") as handle:
            fields = list(csv.DictReader(handle).fieldnames or [])
    else:
        fields = []
    if not fields:
        fields = [
            "run_id", "date", "commit_or_state", "stage", "backend", "command",
            "params", "seed", "status", "summary", "artifacts",
        ]
    row = {field: "" for field in fields}
    values = {
        "run_id": run_id,
        "date": "2026-07-05",
        "commit_or_state": git_head(),
        "git_ref": git_head(),
        "stage": "Stage 333",
        "backend": "web-literature-audit",
        "command": "python scripts/build_stage333_literature_novelty_verification.py",
        "params": "PVW/MAT-SAB related-work axes; source URLs verified by web search/open",
        "seed": "n/a",
        "status": DECISION,
        "summary": "Creates real-source related-work matrix and keeps novelty claim open pending full-text claim audit.",
        "artifacts": f"{rel(DOC)}; {rel(LIT_MATRIX)}; {rel(MATRIX)}; {rel(PROOF)}",
    }
    for key, value in values.items():
        if key in row:
            row[key] = value
    with RUN_LOG.open("a", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields, lineterminator="\n")
        writer.writerow(row)


def artifact_index(paths: list[Path]) -> None:
    rows: list[dict[str, object]] = []
    for path in paths:
        if path.exists() and path.is_file():
            data = path.read_bytes()
            rows.append({"path": rel(path), "bytes": len(data), "sha256": hashlib.sha256(data).hexdigest()})
    write_csv(ARTIFACT, rows, ["path", "bytes", "sha256"])


def main() -> int:
    OUT.mkdir(parents=True, exist_ok=True)

    search_rows = [
        {
            "axis": "target_686_sab",
            "query": "ePrint 2025/686 sparse amortized bootstrapping",
            "source_used": "ePrint search, GitHub repository metadata, ACM DOI page",
            "result": "target protocol/source identified",
        },
        {
            "axis": "amortized_fhew_tfhe",
            "query": "Ring packing amortized FHEW bootstrapping; amortized bootstrapping revisited; incomplete NTT amortized bootstrapping",
            "source_used": "ePrint, DROPS, Springer/DBLP search results",
            "result": "prior and later amortized bootstrapping lines identified",
        },
        {
            "axis": "shared_mask_packed_tfhe",
            "query": "Sharing the Mask TFHE bootstrapping on packed messages; common mask GLWE GGSW",
            "source_used": "DBLP, AskCryptography, ResearchGate text preview",
            "result": "direct high-risk adjacent work identified; full-text audit required",
        },
        {
            "axis": "tfhe_external_product_implementation",
            "query": "TFHE external product; MOSFHET optimized software; faster packed homomorphic operations TFHE",
            "source_used": "ePrint, DOI/publisher metadata, GitHub",
            "result": "implementation/backend prior art identified",
        },
    ]

    matrix_rows = [
        {
            "source_id": "S333-001",
            "citation_key": "guimaraes_pereira_2025_686",
            "title": "Fast amortized bootstrapping with small keys and polynomial noise overhead",
            "authors": "Antonio Guimaraes; Hilder V. L. Pereira",
            "year": "2025",
            "venue_or_status": "IACR ePrint 2025/686; ACM CCS 2025 DOI page found",
            "verified_url": "https://eprint.iacr.org/2025/686 ; https://github.com/antoniocgj/Fast-Amortized-Bootstrapping ; https://dl.acm.org/doi/10.1145/3719027.3765181",
            "axis": "target_686_sab",
            "relation_to_pvw_mat_sab": "baseline target SAB protocol; our result is an r-body/PVW/MAT implementation and scheduling path for this target.",
            "similarity": "same sparse amortized bootstrapping target and complete bootstrapping metric family.",
            "difference": "does not by itself claim PVW/MAT r-body shared-mask implementation speedup measured here.",
            "novelty_risk": "baseline_not_novelty_threat",
            "verification_status": "METADATA_URL_RECORDED_REPOSITORY_ACM",
        },
        {
            "source_id": "S333-002",
            "citation_key": "paiva_et_al_2025_696",
            "title": "Faster amortized bootstrapping using the incomplete NTT for free",
            "authors": "Thales B. Paiva; Gabrielle De Micheli; Syed Mahbub Hafiz; Marcos A. Simplicio Jr.; Bahattin Yildiz",
            "year": "2025",
            "venue_or_status": "IACR ePrint 2025/696",
            "verified_url": "https://eprint.iacr.org/2025/696",
            "axis": "recent_amortized_bootstrapping",
            "relation_to_pvw_mat_sab": "later amortized bootstrapping acceleration line; improves Guimaraes et al. ASIACRYPT 2023 via incomplete NTT.",
            "similarity": "amortized FHEW/TFHE bootstrapping throughput objective.",
            "difference": "NTT algorithmic strategy, not PVW/MAT r-body external-product adaptation of 2025/686.",
            "novelty_risk": "medium",
            "verification_status": "METADATA_URL_RECORDED_EPRINT",
        },
        {
            "source_id": "S333-003",
            "citation_key": "guimaraes_pereira_vanleeuwen_2023_014",
            "title": "Amortized Bootstrapping Revisited: Simpler, Asymptotically-faster, Implemented",
            "authors": "Antonio Guimaraes; Hilder V. L. Pereira; Barry van Leeuwen",
            "year": "2023",
            "venue_or_status": "IACR ePrint 2023/014; ASIACRYPT 2023 metadata found",
            "verified_url": "https://eprint.iacr.org/2023/014",
            "axis": "amortized_bootstrapping_foundation",
            "relation_to_pvw_mat_sab": "prior amortized bootstrapping family and key comparison target for later works.",
            "similarity": "amortized bootstrapping over multiple messages.",
            "difference": "not the 2025/686 sparse small-key target and not this MAT/PVW lane implementation.",
            "novelty_risk": "medium",
            "verification_status": "METADATA_URL_RECORDED_EPRINT",
        },
        {
            "source_id": "S333-004",
            "citation_key": "micciancio_sorrell_2018_ring_packing",
            "title": "Ring Packing and Amortized FHEW Bootstrapping",
            "authors": "Daniele Micciancio; Jessica Sorrell",
            "year": "2018",
            "venue_or_status": "ICALP 2018; DOI 10.4230/LIPIcs.ICALP.2018.100",
            "verified_url": "https://drops.dagstuhl.de/entities/document/10.4230/LIPIcs.ICALP.2018.100",
            "axis": "multi_message_amortized_bootstrapping",
            "relation_to_pvw_mat_sab": "seminal simultaneous-refresh amortization over many FHEW ciphertexts.",
            "similarity": "amortizes bootstrapping over multiple bits/messages.",
            "difference": "ring-packing refresh procedure differs from 2025/686 SAB and our PVW/MAT shared-body path.",
            "novelty_risk": "high_for_broad_multi_message_claims",
            "verification_status": "METADATA_URL_RECORDED_DROPS_DOI",
        },
        {
            "source_id": "S333-005",
            "citation_key": "liu_wang_2023_7ms",
            "title": "Amortized Functional Bootstrapping in Less than 7 ms, with O~(1) Polynomial Multiplications",
            "authors": "Zeyu Liu; Yunhao Wang",
            "year": "2023",
            "venue_or_status": "ASIACRYPT 2023; DOI 10.1007/978-981-99-8736-8_4",
            "verified_url": "https://link.springer.com/chapter/10.1007/978-981-99-8736-8_4",
            "axis": "amortized_functional_bootstrapping",
            "relation_to_pvw_mat_sab": "strong amortized functional bootstrapping baseline and terminology source.",
            "similarity": "amortized functional/bootstrap throughput claim style.",
            "difference": "different algorithmic construction; not 2025/686 sparse SAB PVW/MAT external product.",
            "novelty_risk": "medium_high_for_amortized_functional_claims",
            "verification_status": "METADATA_URL_RECORDED_SPRINGER_DOI",
        },
        {
            "source_id": "S333-006",
            "citation_key": "li_et_al_2025_022",
            "title": "Leveled Functional Bootstrapping via External Product Tree",
            "authors": "Zhihao Li; Xuan Shen; Xianhui Lu; Ruida Wang; Yuan Zhao",
            "year": "2025",
            "venue_or_status": "IACR ePrint 2025/022",
            "verified_url": "https://eprint.iacr.org/2025/022",
            "axis": "external_product_algorithm",
            "relation_to_pvw_mat_sab": "external-product tree is adjacent to external-product-count optimization.",
            "similarity": "external product as primary bootstrapping cost object.",
            "difference": "leveled functional bootstrapping tree, not r-body MAT/SAB complete bootstrapping path.",
            "novelty_risk": "medium",
            "verification_status": "METADATA_URL_RECORDED_EPRINT",
        },
        {
            "source_id": "S333-007",
            "citation_key": "chillotti_et_al_2020_tfhe",
            "title": "TFHE: Fast Fully Homomorphic Encryption over the Torus",
            "authors": "Ilaria Chillotti; Nicolas Gama; Mariya Georgieva; Malika Izabachene",
            "year": "2020",
            "venue_or_status": "Journal of Cryptology; DOI 10.1007/s00145-019-09319-x; ePrint 2018/421",
            "verified_url": "https://eprint.iacr.org/2018/421 ; https://dl.acm.org/doi/10.1007/s00145-019-09319-x",
            "axis": "tfhe_external_product_foundation",
            "relation_to_pvw_mat_sab": "defines core TFHE/TRLWE/TRGSW/external-product context used by implementation.",
            "similarity": "external product and bootstrapping foundations.",
            "difference": "not SAB or MAT/PVW multi-body amortization.",
            "novelty_risk": "foundation_not_threat",
            "verification_status": "METADATA_URL_RECORDED_EPRINT_DOI",
        },
        {
            "source_id": "S333-008",
            "citation_key": "chillotti_gama_georgieva_izabachene_2017_430",
            "title": "Faster Packed Homomorphic Operations and Efficient Circuit Bootstrapping for TFHE",
            "authors": "Ilaria Chillotti; Nicolas Gama; Mariya Georgieva; Malika Izabachene",
            "year": "2017",
            "venue_or_status": "ASIACRYPT 2017; ePrint 2017/430",
            "verified_url": "https://eprint.iacr.org/2017/430 ; https://www.tfhe.com/about",
            "axis": "packed_tfhe_operations",
            "relation_to_pvw_mat_sab": "prior packed TFHE operations and circuit bootstrapping optimization line.",
            "similarity": "packed data and TFHE bootstrapping.",
            "difference": "not the same sparse SAB full-flow r-body direct-DFT implementation.",
            "novelty_risk": "high_for_generic_packed_tfhe_claims",
            "verification_status": "METADATA_URL_RECORDED_EPRINT_PROJECT",
        },
        {
            "source_id": "S333-009",
            "citation_key": "guimaraes_borin_aranha_2024_mosfhet",
            "title": "MOSFHET: Optimized Software for FHE over the Torus",
            "authors": "Antonio Guimaraes; Edson Borin; Diego F. Aranha",
            "year": "2024",
            "venue_or_status": "Journal of Cryptographic Engineering 14(3):577-593; DOI 10.1007/s13389-024-00359-z",
            "verified_url": "https://eprint.iacr.org/2022/515 ; https://github.com/antoniocgj/MOSFHET ; https://pure.au.dk/portal/en/publications/mosfhet-optimized-software-for-fhe-over-the-torus-2/",
            "axis": "implementation_backend",
            "relation_to_pvw_mat_sab": "implementation baseline and AVX/TFHE optimization source; local repo reuses MOSFHET code lineage.",
            "similarity": "same implementation ecosystem and backend optimization concerns.",
            "difference": "not a 2025/686 SAB r-body algorithmic claim by itself.",
            "novelty_risk": "high_for_backend_or_avx_claims",
            "verification_status": "METADATA_URL_RECORDED_EPRINT_DOI_GITHUB",
        },
        {
            "source_id": "S333-010",
            "citation_key": "bergerat_et_al_2025_sharing_mask",
            "title": "Sharing the Mask: TFHE Bootstrapping on Packed Messages",
            "authors": "Loris Bergerat; Charlotte Bonte; Benjamin R. Curtis; Jean-Baptiste Orfila; Pascal Paillier; Samuel Tap",
            "year": "2025",
            "venue_or_status": "IACR TCHES 2025(4):925-971; ePrint 2025/2112 metadata found",
            "verified_url": "https://dblp.org/rec/journals/tches/BergeratBCOPT25 ; https://askcryp.to/tag/2025-2112",
            "axis": "shared_mask_packed_messages",
            "relation_to_pvw_mat_sab": "directly adjacent common-mask packed-message bootstrapping; must be audited before novelty wording around shared masks/r-body lanes.",
            "similarity": "shared-mask/common-mask TFHE bootstrapping on packed messages.",
            "difference": "not yet audited against 2025/686 SAB full-flow direct PVW/MAT path and T_bootstrap/r experiment.",
            "novelty_risk": "critical_for_shared_mask_novelty",
            "verification_status": "METADATA_URL_RECORDED_DBLP_FULLTEXT_PENDING",
        },
    ]

    risk_rows = [
        {
            "claim_area": "complete SAB throughput engineering result",
            "risk_level": "low",
            "supporting_sources": "S333-001; S333-009",
            "decision": "claim allowed only as scoped measured result",
            "required_next": "none for scoped systems result",
        },
        {
            "claim_area": "first/broad multi-message amortized bootstrapping",
            "risk_level": "critical",
            "supporting_sources": "S333-004; S333-005; S333-008; S333-010",
            "decision": "do not claim",
            "required_next": "full-text audit and narrow contribution statement",
        },
        {
            "claim_area": "shared-mask or r-body ciphertext novelty",
            "risk_level": "critical",
            "supporting_sources": "S333-010; S333-008",
            "decision": "novelty open",
            "required_next": "audit common-mask packed-message construction against PVW/MAT-SAB",
        },
        {
            "claim_area": "external-product count reduction",
            "risk_level": "high",
            "supporting_sources": "S333-006; S333-007",
            "decision": "do not claim for current exact dense path",
            "required_next": "compact route proof and full SAB A/B",
        },
        {
            "claim_area": "AVX/backend optimality",
            "risk_level": "high",
            "supporting_sources": "S333-009",
            "decision": "do not claim theoretical optimality",
            "required_next": "native counter/full-SAB backend audit per variant",
        },
    ]

    proof_rows = [
        {
            "gate": "G1_real_sources",
            "status": "PASS",
            "metric": "verified source rows",
            "value": str(len(matrix_rows)),
            "interpretation": "Stage333 uses real URLs/metadata, not fabricated references.",
        },
        {
            "gate": "G2_high_risk_identified",
            "status": "PASS",
            "metric": "critical/high risk claim areas",
            "value": "shared-mask; multi-message; external-product; backend optimality",
            "interpretation": "Novelty is not claimed because direct adjacent work exists.",
        },
        {
            "gate": "G3_claim_boundary",
            "status": "PASS",
            "metric": "novelty claim",
            "value": "OPEN",
            "interpretation": "Stage333 permits scoped systems result only; novelty requires Stage334 full-text audit.",
        },
        {
            "gate": "G4_decision",
            "status": DECISION,
            "metric": "stage decision",
            "value": DECISION,
            "interpretation": "Controls Stage334 full-text claim audit or compact security preflight.",
        },
    ]

    summary_rows = [{
        "decision": DECISION,
        "sources": len(matrix_rows),
        "critical_risk_claims": "shared-mask/r-body novelty; broad multi-message bootstrapping",
        "allowed_claim": "scoped measured PVW/MAT-SAB complete T_bootstrap/r systems result",
        "blocked_claims": "novelty; theoretical optimality; compact selector acceleration; all-parameter generality",
        "selected_next": "stage334_fulltext_claim_audit_or_compact_security_preflight",
    }]

    next_rows = [
        {
            "priority": "P0",
            "route": "stage334_fulltext_claim_audit",
            "entry_condition": DECISION,
            "gate": "download/read high-risk full texts and map exact claims to PVW/MAT-SAB contribution boundaries",
            "failure_action": "Keep novelty wording out of the paper.",
        },
        {
            "priority": "P1",
            "route": "stage334_compact_keygen_security_preflight",
            "entry_condition": "algorithmic gain beyond scoped systems result is prioritized",
            "gate": "keygen distribution, semantic-zero security, noise recurrence",
            "failure_action": "Keep compact production code blocked.",
        },
    ]

    write_csv(SEARCH, search_rows, ["axis", "query", "source_used", "result"])
    write_csv(MATRIX, matrix_rows, [
        "source_id", "citation_key", "title", "authors", "year", "venue_or_status",
        "verified_url", "axis", "relation_to_pvw_mat_sab", "similarity",
        "difference", "novelty_risk", "verification_status",
    ])
    write_csv(LIT_MATRIX, matrix_rows, [
        "source_id", "citation_key", "title", "authors", "year", "venue_or_status",
        "verified_url", "axis", "relation_to_pvw_mat_sab", "similarity",
        "difference", "novelty_risk", "verification_status",
    ])
    write_csv(RISK, risk_rows, ["claim_area", "risk_level", "supporting_sources", "decision", "required_next"])
    write_csv(PROOF, proof_rows, ["gate", "status", "metric", "value", "interpretation"])
    write_csv(SUMMARY, summary_rows, ["decision", "sources", "critical_risk_claims", "allowed_claim", "blocked_claims", "selected_next"])
    write_csv(NEXT, next_rows, ["priority", "route", "entry_condition", "gate", "failure_action"])

    write_text(DOC, f"""# Stage333 Literature Novelty Verification

Decision: `{DECISION}`.

Stage333 creates a real-source related-work matrix for the PVW/MAT-SAB claim.
It does not claim novelty.  The only currently allowed statement remains the
Stage332 scoped measured systems result.

## Summary

{md_table(summary_rows, ["decision", "sources", "allowed_claim", "blocked_claims", "selected_next"])}

## Search Strategy

{md_table(search_rows, ["axis", "query", "source_used", "result"])}

## Related Literature Matrix

{md_table(matrix_rows, ["source_id", "citation_key", "year", "axis", "novelty_risk", "verification_status"])}

## Novelty Risk Map

{md_table(risk_rows, ["claim_area", "risk_level", "supporting_sources", "decision", "required_next"])}

## Proof Gate

{md_table(proof_rows, ["gate", "status", "metric", "value"])}

Generated from input head `{git_head()}`.
""")

    write_text(THEORY, """# Stage333 Novelty Risk Model

Stage333 evaluates novelty risk at the claim level, not by keyword overlap.

Allowed: a scoped measured systems result for the current implementation,
parameter set, backend, and primary metric.

Blocked until full-text audit:

- broad multi-message/amortized bootstrapping novelty;
- shared-mask/r-body ciphertext novelty;
- external-product count reduction;
- AVX/backend theoretical optimality;
- all-parameter generality.

The critical risk source for shared-mask wording is the 2025 "Sharing the Mask"
line.  The critical risk sources for broad multi-message wording include Ring
Packing and packed TFHE operations.  Therefore Stage333 deliberately leaves
novelty open.
""")

    write_text(PLAN, """# Stage334 Full-Text Claim Audit Or Compact Security Plan

Route A: full-text claim audit.

- Acquire/read high-risk sources: Ring Packing, Faster Packed TFHE,
  Sharing the Mask, MOSFHET, 2025/686, 2025/696.
- For each paper, map exact claims to the PVW/MAT-SAB contribution boundary.
- Only after this audit may novelty wording be drafted.

Route B: compact keygen/security preflight.

- Close keygen distribution, semantic-zero security, and noise recurrence.
- No compact SAB code before proof gates pass.
""")

    write_text(COMMANDS, """# Stage333 Reproduction Commands

```sh
python scripts/build_stage333_literature_novelty_verification.py
```

External metadata was checked via web search/open against ePrint, DOI/publisher,
DBLP/DROPS, GitHub, and AskCryptography pages.  Full-text claim audit is deferred
to Stage334.
""")

    write_text(REPORT, read_text(DOC))

    append_once(GOAL, "<!-- stage333-literature-novelty-verification -->", f"""
<!-- stage333-literature-novelty-verification -->
### Stage333 literature novelty verification

`{DECISION}` creates a real-source related-work matrix and keeps novelty open.
The allowed claim remains the Stage332 scoped measured systems result only.
""")

    append_once(ROADMAP, "<!-- stage333-literature-novelty-roadmap -->", f"""
<!-- stage333-literature-novelty-roadmap -->
## Stage 333: Literature Novelty Verification

Goal: build a verified related-work matrix and novelty-risk map for PVW/MAT-SAB.

Status: `{DECISION}`.
""")

    append_once(HYPOTHESES, "H333_literature_novelty_verification:", f"""
H333_literature_novelty_verification:
  status: {DECISION}
  primary_metric: related_work_novelty_risk
  evidence:
    - literature/related_literature_matrix.csv
    - repro/stage333_literature_novelty_verification/source_matrix.csv
    - repro/stage333_literature_novelty_verification/novelty_risk_map.csv
    - repro/stage333_literature_novelty_verification/proof_gate.csv
  conclusion: >
    Stage333 verifies real related sources and blocks broad novelty wording
    until Stage334 full-text claim audit closes high-risk adjacent work.
""")

    append_once(MANIFEST, "<!-- stage333-literature-novelty-manifest -->", """
<!-- stage333-literature-novelty-manifest -->
- stage333_literature_novelty_verification:
  - `docs/stage333_literature_novelty_verification.md`
  - `literature/related_literature_matrix.csv`
  - `theory_checks/stage333_novelty_risk_model.md`
  - `experiments/stage334_fulltext_claim_audit_or_compact_security_plan.md`
  - `scripts/build_stage333_literature_novelty_verification.py`
  - `repro/stage333_literature_novelty_verification/`
""")

    append_once(CHECKLIST, "<!-- stage333-literature-novelty-checklist -->", f"""
<!-- stage333-literature-novelty-checklist -->
- [x] Stage333 records `{DECISION}` with real sources and no novelty claim.
""")

    append_run_log()

    artifact_index([DOC, THEORY, PLAN, BUILDER, LIT_MATRIX, SUMMARY, SEARCH, MATRIX, RISK, PROOF, NEXT, COMMANDS, REPORT])
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
