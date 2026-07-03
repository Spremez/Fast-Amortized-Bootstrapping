#!/usr/bin/env python3
"""Stage177: verified literature and novelty-boundary gate."""

from __future__ import annotations

import csv
import hashlib
import subprocess
from pathlib import Path
from typing import Dict, Iterable, List


ROOT = Path(__file__).resolve().parents[1]
OUT_DIR = ROOT / "repro" / "stage177_verified_literature_novelty_gate"

SUMMARY_CSV = OUT_DIR / "summary.csv"
QUERY_CSV = OUT_DIR / "search_queries.csv"
LITERATURE_CSV = OUT_DIR / "literature_matrix.csv"
RISK_CSV = OUT_DIR / "novelty_risk.csv"
SUPPORT_CSV = OUT_DIR / "citation_support.csv"
POLICY_CSV = OUT_DIR / "claim_policy.csv"
NEXT_CSV = OUT_DIR / "next_stage_queue.csv"
ARTIFACT_CSV = OUT_DIR / "artifact_index.csv"

OUT_MD = ROOT / "docs" / "stage177_verified_literature_novelty_gate.md"
PLAN_MD = ROOT / "experiments" / "stage177_verified_literature_novelty_gate_plan.md"
THEORY_MD = ROOT / "theory_checks" / "stage177_literature_novelty_model.md"
VARIANT_MD = ROOT / "algorithm_variants" / "mat_rlwe_sab_literature_claim_boundary.md"

ROADMAP_MD = ROOT / "docs" / "roadmap_stage19_plus.md"
GOAL_MD = ROOT / "docs" / "goal_sab_max_acceleration.md"
CURRENT_GOAL_MD = ROOT / "docs" / "current_codex_goal_sab_completion.md"
HYPOTHESIS_YAML = ROOT / "hypotheses" / "hypothesis_register.yaml"
RUN_LOG = ROOT / "repro" / "run_log.csv"
MANIFEST = ROOT / "repro" / "artifact_manifest.md"
CHECKLIST = ROOT / "repro" / "reproduction_checklist.md"

STAGE176_SUMMARY = ROOT / "repro" / "stage176_structured_compact_security_api_gate" / "summary.csv"

DECISION = "PASS_STAGE177_VERIFIED_LITERATURE_BOUNDARY_NO_STRONG_NOVELTY_CLAIM"


def rel(path: Path) -> str:
    return path.resolve().relative_to(ROOT.resolve()).as_posix()


def write_text_lf(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(text.encode("utf-8"))


def read_text(path: Path) -> str:
    return path.read_text(encoding="utf-8", errors="replace") if path.exists() else ""


def write_csv(path: Path, rows: Iterable[Dict[str, str]], fields: List[str]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    row_list = list(rows)
    normalized = [{field: row.get(field, "") for field in fields} for row in row_list]
    with path.open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fields, lineterminator="\n")
        writer.writeheader()
        writer.writerows(normalized)


def table(rows: List[Dict[str, str]], fields: List[str]) -> str:
    def cell(value: str) -> str:
        return str(value).replace("|", "\\|").replace("\n", "<br>")

    out = [
        "| " + " | ".join(fields) + " |",
        "| " + " | ".join("---" for _ in fields) + " |",
    ]
    for row in rows:
        out.append("| " + " | ".join(cell(row.get(field, "")) for field in fields) + " |")
    return "\n".join(out) + "\n"


def append_once(path: Path, marker: str, text: str) -> None:
    current = read_text(path)
    if marker in current:
        return
    if current and not current.endswith("\n"):
        current += "\n"
    write_text_lf(path, current + text.lstrip("\n"))


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


def sha256_file(path: Path) -> str:
    if not path.exists():
        return ""
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def build_queries() -> List[Dict[str, str]]:
    return [
        {"axis": "target-paper", "query": "eprint 2025/686 sparse amortized bootstrapping", "purpose": "Verify the baseline target and implementation repository."},
        {"axis": "post-686", "query": "Faster amortized bootstrapping using the incomplete NTT for free 2025/696", "purpose": "Find direct follow-up/neighbor after 2025/686."},
        {"axis": "amortized-history", "query": "Amortized Bootstrapping Revisited 2023/014", "purpose": "Verify the 686 lineage and earlier implementation evidence."},
        {"axis": "ring-automorphism", "query": "Faster Amortized FHEW bootstrapping using Ring Automorphisms 2023/112", "purpose": "Map adjacent NTT/automorphism amortized bootstrapping."},
        {"axis": "functional-batch", "query": "Amortized Functional Bootstrapping less than 7ms 2023/910", "purpose": "Map batch functional bootstrapping and amortized per-ciphertext claims."},
        {"axis": "batch-framework", "query": "Batch Bootstrapping I II SIMD Bootstrapping polynomial modulus EUROCRYPT 2023", "purpose": "Map batch/SIMD bootstrapping alternatives."},
        {"axis": "pvw-packing", "query": "Packed Ciphertexts in LWE-Based Homomorphic Encryption PVW 2012/565", "purpose": "Verify PVW packing ancestry."},
        {"axis": "tfhe-external-product", "query": "TFHE Fast Fully Homomorphic Encryption over the Torus external product 2018/421", "purpose": "Verify TFHE/GSW external-product baseline."},
        {"axis": "fhew-origin", "query": "FHEW bootstrapping homomorphic encryption in less than a second 2014/816", "purpose": "Verify FHEW predecessor."},
        {"axis": "ring-packing", "query": "Ring Packing and Amortized FHEW Bootstrapping ICALP 2018", "purpose": "Verify the original amortized FHEW line."},
    ]


def build_literature() -> List[Dict[str, str]]:
    return [
        {
            "id": "GP2025_686",
            "title": "Fast amortized bootstrapping with small keys and polynomial noise overhead",
            "authors_year": "Antonio Guimaraes; Hilder V. L. Pereira; 2025",
            "venue_or_archive": "IACR ePrint 2025/686; repository states to appear at CCS 2025",
            "url": "https://eprint.iacr.org/2025/686",
            "verified_source": "https://github.com/antoniocgj/Fast-Amortized-Bootstrapping",
            "relation_to_project": "Target baseline; current repository implements and extends this SAB line.",
            "similarity": "Sparse amortized bootstrapping, small keys, polynomial noise overhead, AVX512-oriented implementation.",
            "difference": "Our work changes implementation/representation using PVW/MAT r-body lanes and measures T_bootstrap/r against repeated scalar SAB.",
            "novelty_risk": "HIGH_BASELINE",
            "local_claim_allowed": "Use as baseline and target algorithm only.",
        },
        {
            "id": "PDMHSY2025_696",
            "title": "Faster amortized bootstrapping using the incomplete NTT for free",
            "authors_year": "Thales B. Paiva; Gabrielle De Micheli; Syed Mahbub Hafiz; Marcos A. Simplicio Jr.; Bahattin Yildiz; 2025",
            "venue_or_archive": "IACR ePrint 2025/696",
            "url": "https://eprint.iacr.org/2025/696",
            "verified_source": "https://eprint.iacr.org/2025/696",
            "relation_to_project": "Direct post-686 adjacent work.",
            "similarity": "Improves amortized bootstrapping around the Guimaraes et al. line via NTT strategy and reports speed/DFR tradeoffs.",
            "difference": "Optimizes NTT/amortized algorithm, not PVW/MAT shared-mask r-body external product in this codebase.",
            "novelty_risk": "HIGH_DIRECT_ADJACENT",
            "local_claim_allowed": "Any paper claim must compare or position against this work.",
        },
        {
            "id": "GPL2023_014",
            "title": "Amortized Bootstrapping Revisited: Simpler, Asymptotically-faster, Implemented",
            "authors_year": "Antonio Guimaraes; Hilder V. L. Pereira; Barry van Leeuwen; 2023",
            "venue_or_archive": "IACR ePrint 2023/014; ASIACRYPT 2023",
            "url": "https://eprint.iacr.org/2023/014",
            "verified_source": "https://eprint.iacr.org/2023/014",
            "relation_to_project": "Algorithmic ancestor for practical amortized bootstrapping.",
            "similarity": "Amortized bootstrapping with concrete implementation; double-CRT GSW and shrinking.",
            "difference": "Not the sparse 2025/686 SAB implementation and not our PVW/MAT r-body path.",
            "novelty_risk": "MEDIUM_LINEAGE",
            "local_claim_allowed": "Cite as lineage and complexity context.",
        },
        {
            "id": "DKMS2023_112",
            "title": "Faster Amortized FHEW bootstrapping using Ring Automorphisms",
            "authors_year": "Gabrielle De Micheli; Duhyeong Kim; Daniele Micciancio; Adam Suhl; 2023/PKC 2024",
            "venue_or_archive": "IACR ePrint 2023/112; PKC 2024",
            "url": "https://eprint.iacr.org/2023/112",
            "verified_source": "https://eprint.iacr.org/2023/112",
            "relation_to_project": "Adjacent amortized FHEW algorithmic work.",
            "similarity": "Uses NTT/ring automorphisms and scheme switching to reduce amortized bootstrapping overhead.",
            "difference": "Not 686 SAB and not PVW/MAT shared-mask external product.",
            "novelty_risk": "MEDIUM_ADJACENT",
            "local_claim_allowed": "Cite for amortized bootstrapping landscape.",
        },
        {
            "id": "LW2023_910",
            "title": "Amortized Functional Bootstrapping in less than 7ms, with O~(1) polynomial multiplications",
            "authors_year": "Zeyu Liu; Yunhao Wang; 2023",
            "venue_or_archive": "IACR ePrint 2023/910; ASIACRYPT 2023",
            "url": "https://eprint.iacr.org/2023/910",
            "verified_source": "https://eprint.iacr.org/2023/910",
            "relation_to_project": "Adjacent batch functional bootstrapping.",
            "similarity": "Amortized/batched LWE bootstrapping with concrete implementation and per-ciphertext timing claims.",
            "difference": "Different framework/objective; not sparse 686 SAB and not MAT external-product batching.",
            "novelty_risk": "MEDIUM_ADJACENT",
            "local_claim_allowed": "Cite for amortized functional bootstrapping context.",
        },
        {
            "id": "LW2023_BatchI_II",
            "title": "Batch Bootstrapping I/II",
            "authors_year": "Feng-Hao Liu; Han Wang; 2023",
            "venue_or_archive": "EUROCRYPT 2023",
            "url": "https://link.springer.com/content/pdf/10.1007/978-3-031-30620-4_11.pdf",
            "verified_source": "https://dl.acm.org/doi/10.1007/978-3-031-30620-4_12",
            "relation_to_project": "Alternative SIMD/batch bootstrapping framework.",
            "similarity": "Batch/SIMD bootstrapping in polynomial modulus; relevant to amortized throughput claims.",
            "difference": "Different mathematical framework and not 686 sparse schedule/PVW-MAT path.",
            "novelty_risk": "MEDIUM_ADJACENT",
            "local_claim_allowed": "Cite as adjacent batch bootstrapping prior art.",
        },
        {
            "id": "BGH2012_565",
            "title": "Packed Ciphertexts in LWE-Based Homomorphic Encryption",
            "authors_year": "Zvika Brakerski; Craig Gentry; Shai Halevi; 2012",
            "venue_or_archive": "IACR ePrint 2012/565",
            "url": "https://eprint.iacr.org/2012/565",
            "verified_source": "https://link.springer.com/chapter/10.1007/978-3-642-36362-7_1",
            "relation_to_project": "PVW packing ancestry.",
            "similarity": "Uses Peikert-Vaikuntanathan-Waters packing for SIMD-style LWE ciphertexts.",
            "difference": "Packing primitive/background, not SAB external-product algorithm.",
            "novelty_risk": "LOW_BACKGROUND_HIGH_IF_PACKING_CLAIM",
            "local_claim_allowed": "Cite for PVW packing background; do not claim PVW packing as new.",
        },
        {
            "id": "CGGI2018_421",
            "title": "TFHE: Fast Fully Homomorphic Encryption over the Torus",
            "authors_year": "Ilaria Chillotti; Nicolas Gama; Mariya Georgieva; Malika Izabachene; 2018/2019",
            "venue_or_archive": "IACR ePrint 2018/421; Journal of Cryptology 2019",
            "url": "https://eprint.iacr.org/2018/421",
            "verified_source": "https://eprint.iacr.org/2018/421",
            "relation_to_project": "TFHE/GSW external-product baseline.",
            "similarity": "External product between GSW and LWE/RLWE-like ciphertexts; bootstrapping and packed operations.",
            "difference": "Not amortized 686 SAB and not current MAT/PVW multi-body implementation.",
            "novelty_risk": "BACKGROUND_REQUIRED",
            "local_claim_allowed": "Cite for TFHE/external-product background.",
        },
        {
            "id": "DM2014_816",
            "title": "FHEW: Bootstrapping Homomorphic Encryption in less than a second",
            "authors_year": "Leo Ducas; Daniele Micciancio; 2014/2015",
            "venue_or_archive": "IACR ePrint 2014/816; EUROCRYPT 2015",
            "url": "https://eprint.iacr.org/2014/816",
            "verified_source": "https://eprint.iacr.org/2014/816",
            "relation_to_project": "FHEW predecessor to TFHE/amortized FHEW lines.",
            "similarity": "Bootstrapping of bit operations and FHEW-style lineage.",
            "difference": "Single/sequential bootstrapping baseline, not multi-lane MAT-SAB.",
            "novelty_risk": "BACKGROUND_REQUIRED",
            "local_claim_allowed": "Cite for FHEW background.",
        },
        {
            "id": "MS2018_ICALP",
            "title": "Ring Packing and Amortized FHEW Bootstrapping",
            "authors_year": "Daniele Micciancio; Jessica Sorrell; 2018",
            "venue_or_archive": "ICALP 2018",
            "url": "https://drops.dagstuhl.de/entities/document/10.4230/LIPIcs.ICALP.2018.100",
            "verified_source": "https://drops.dagstuhl.de/entities/document/10.4230/LIPIcs.ICALP.2018.100",
            "relation_to_project": "Original amortized FHEW-style bootstrapping line.",
            "similarity": "Refreshes many messages simultaneously and establishes amortized FHEW bootstrapping context.",
            "difference": "Earlier ring-packing/Nussbaumer-style line, not sparse 686 SAB or PVW/MAT external-product batching.",
            "novelty_risk": "BACKGROUND_REQUIRED",
            "local_claim_allowed": "Cite for original amortized bootstrapping context.",
        },
    ]


def build_risks() -> List[Dict[str, str]]:
    return [
        {
            "claim": "PVW/MAT-SAB exact full path improves repeated scalar SAB throughput on this implementation",
            "risk": "LOW_TO_MEDIUM",
            "reason": "This is an implementation/experimental claim tied to local complete-SAB A/B evidence, not a broad novelty claim.",
            "required_next_evidence": "Stage178 must re-normalize T_bootstrap/r and cite commit/backend/raw logs.",
            "allowed_status": "ENGINEERING_CLAIM_ONLY",
        },
        {
            "claim": "Structured compact MAT-SAB is a new implemented bootstrapping algorithm",
            "risk": "HIGH_BLOCKED",
            "reason": "Stage176 denies implementation permission; literature contains strong adjacent amortized/batch work.",
            "required_next_evidence": "Security/API proof plus full-SAB implementation and comparison to 2025/696.",
            "allowed_status": "FORBIDDEN_NOW",
        },
        {
            "claim": "PVW packing itself is novel",
            "risk": "INVALID",
            "reason": "PVW packing is established prior art; BGH2012 explicitly uses it for LWE-based packed ciphertexts.",
            "required_next_evidence": "None; do not make this claim.",
            "allowed_status": "FORBIDDEN",
        },
        {
            "claim": "AVX512 MAT external product is a paper-level algorithmic contribution",
            "risk": "MEDIUM",
            "reason": "It may be valuable systems work, but must be separated from mathematical SAB algorithm claims and compared at complete-SAB level.",
            "required_next_evidence": "ISA-specific microbench, disassembly/counters, full-SAB A/B, backend separation.",
            "allowed_status": "POSSIBLE_SYSTEMS_ABLATION",
        },
        {
            "claim": "2025/686 SAB can be accelerated by optimizing exact full-MAT r-body batching",
            "risk": "MEDIUM",
            "reason": "Current measurements support some T_bootstrap/r gain, but not theoretical optimality or multi-fold guarantee.",
            "required_next_evidence": "Stage178/179 exact-path component-driven gates and repeated complete-SAB benchmarks.",
            "allowed_status": "ACTIVE_ENGINEERING_ROUTE",
        },
    ]


def build_support_rows() -> List[Dict[str, str]]:
    return [
        {
            "local_claim": "686 is the baseline target and implementation source",
            "supporting_sources": "GP2025_686",
            "support_strength": "STRONG_FOR_BASELINE",
            "needs_cite_verify": "YES_BEFORE_PAPER",
        },
        {
            "local_claim": "2025/696 is direct adjacent/follow-up work after 686",
            "supporting_sources": "PDMHSY2025_696",
            "support_strength": "STRONG_FOR_RELATED_WORK",
            "needs_cite_verify": "YES_BEFORE_PAPER",
        },
        {
            "local_claim": "Amortized bootstrapping has a substantial prior lineage",
            "supporting_sources": "MS2018_ICALP; GPL2023_014; DKMS2023_112; LW2023_910; LW2023_BatchI_II",
            "support_strength": "STRONG",
            "needs_cite_verify": "YES_BEFORE_PAPER",
        },
        {
            "local_claim": "PVW packing is prior art and cannot be claimed as new",
            "supporting_sources": "BGH2012_565",
            "support_strength": "STRONG",
            "needs_cite_verify": "YES_BEFORE_PAPER",
        },
        {
            "local_claim": "TFHE/FHEW external product is background prior art",
            "supporting_sources": "CGGI2018_421; DM2014_816",
            "support_strength": "STRONG",
            "needs_cite_verify": "YES_BEFORE_PAPER",
        },
    ]


def build_policy_rows() -> List[Dict[str, str]]:
    return [
        {
            "scope": "paper_abstract",
            "allowed": "We explore an implementation-level PVW/MAT r-body acceleration path for 2025/686-style SAB.",
            "forbidden": "We introduce a new compact MAT-SAB algorithm.",
        },
        {
            "scope": "performance_claim",
            "allowed": "Report complete-SAB T_bootstrap/r speedups with backend, commit, seed, and CI.",
            "forbidden": "Report kernel-only speedups as bootstrapping acceleration.",
        },
        {
            "scope": "compact_claim",
            "allowed": "Structured compact is a blocked proof route with finite/toy evidence.",
            "forbidden": "Omitted zero encryptions are secure under standard RLWE without proof.",
        },
        {
            "scope": "novelty_claim",
            "allowed": "Claim only after proof, full benchmarks, and explicit comparison to 2025/696 and batch/amortized work.",
            "forbidden": "Use 'novel' based only on local code search or bounded web search.",
        },
    ]


def build_next_rows() -> List[Dict[str, str]]:
    return [
        {
            "priority": "P0",
            "stage": "178",
            "name": "full-MAT exact path per-bit throughput frontier",
            "entry_condition": "Stage176 denies compact implementation; Stage177 denies strong novelty claim.",
            "gate": "Re-normalize all current complete-SAB evidence as T_bootstrap/r and choose the next exact-path implementation candidate from measured component shares.",
            "failure_rule": "No new implementation branch unless the candidate can affect complete-SAB T_bootstrap/r.",
        },
        {
            "priority": "P1",
            "stage": "179",
            "name": "complete-SAB exact-path experiment loop",
            "entry_condition": "Stage178 selects a candidate with plausible complete-SAB impact.",
            "gate": "Run correctness, microbench, full-SAB repeated A/B, attribution, noise/resource.",
            "failure_rule": "Neutral/reject candidates are recorded and not retuned without a new mechanism.",
        },
        {
            "priority": "P2",
            "stage": "180",
            "name": "paper-citation verification",
            "entry_condition": "A manuscript or paper-style claims are drafted.",
            "gate": "Every cited sentence must be checked against source text or official metadata.",
            "failure_rule": "Unsupported statements are removed or downgraded.",
        },
    ]


def build_summary_rows(lit_rows: List[Dict[str, str]], risk_rows: List[Dict[str, str]]) -> List[Dict[str, str]]:
    direct_source_count = str(len(lit_rows))
    strong_claim_allowed = "0"
    return [
        {
            "gate": "stage177_inputs",
            "status": "PASS" if STAGE176_SUMMARY.exists() else "FAIL",
            "metric": "stage176_summary_present",
            "value": "1" if STAGE176_SUMMARY.exists() else "0",
            "evidence": rel(STAGE176_SUMMARY),
            "detail": "Stage177 starts only after Stage176 redirects compact implementation to full-MAT exact path.",
            "next_action": "Repair Stage176 before interpreting literature gate.",
        },
        {
            "gate": "stage177_verified_sources",
            "status": "PASS",
            "metric": "source_rows",
            "value": direct_source_count,
            "evidence": rel(LITERATURE_CSV),
            "detail": "Bounded matrix records target baseline, post-686 work, amortized/batch lineage, PVW packing, TFHE/FHEW background.",
            "next_action": "Use citation-verification before any manuscript sentence.",
        },
        {
            "gate": "stage177_direct_prior_art",
            "status": "NO_DIRECT_COMPACT_MATCH_IN_BOUNDED_SEARCH",
            "metric": "direct_compact_pvw_mat_sab_rows",
            "value": "0",
            "evidence": rel(RISK_CSV),
            "detail": "No verified source in this bounded search directly implements our proposed structured compact PVW/MAT-SAB route.",
            "next_action": "Do not convert this into a novelty claim; bounded search is not exhaustive.",
        },
        {
            "gate": "stage177_adjacent_prior_art",
            "status": "HIGH",
            "metric": "adjacent_rows",
            "value": str(len([r for r in lit_rows if 'ADJACENT' in r['novelty_risk'] or 'BASELINE' in r['novelty_risk']])),
            "evidence": rel(LITERATURE_CSV),
            "detail": "2025/696 and several amortized/batch bootstrapping works create high novelty risk for broad claims.",
            "next_action": "Any paper claim must be narrow and compared against these sources.",
        },
        {
            "gate": "stage177_strong_novelty_permission",
            "status": "DENY",
            "metric": "permission_yes",
            "value": strong_claim_allowed,
            "evidence": rel(POLICY_CSV),
            "detail": "Strong novelty claims are blocked until security/API proof, complete-SAB implementation, and related-work comparison are complete.",
            "next_action": "Proceed to exact full-MAT T_bootstrap/r engineering frontier.",
        },
        {
            "gate": "stage177_decision",
            "status": DECISION,
            "metric": "route",
            "value": "stage178_full_mat_exact_path",
            "evidence": rel(SUMMARY_CSV),
            "detail": "Literature gate supports cautious engineering claims only and routes next to measured exact-path optimization.",
            "next_action": "Run Stage178.",
        },
    ]


def write_docs(summary_rows: List[Dict[str, str]], query_rows: List[Dict[str, str]],
               lit_rows: List[Dict[str, str]], risk_rows: List[Dict[str, str]],
               support_rows: List[Dict[str, str]], policy_rows: List[Dict[str, str]],
               next_rows: List[Dict[str, str]]) -> None:
    write_text_lf(OUT_MD, f"""# Stage177 Verified Literature/Novelty Gate

Decision: `{DECISION}`.

This is a bounded literature gate for the current PVW/MAT-SAB goal. It does
not attempt a broad FHE survey. It verifies enough real adjacent work to decide
which claims are currently allowed.

Result:

- strong novelty claims are denied;
- structured compact MAT-SAB remains blocked by Stage176 proof/API gaps;
- executable work should continue on exact full-MAT `T_bootstrap/r` optimization;
- any paper draft must later run citation-level verification.

## Gate Summary

{table(summary_rows, ["gate", "status", "metric", "value", "evidence", "detail", "next_action"])}
## Targeted Queries

{table(query_rows, ["axis", "query", "purpose"])}
## Related-Work Matrix

{table(lit_rows, ["id", "title", "authors_year", "venue_or_archive", "url", "relation_to_project", "similarity", "difference", "novelty_risk", "local_claim_allowed"])}
## Novelty Risk

{table(risk_rows, ["claim", "risk", "reason", "required_next_evidence", "allowed_status"])}
## Citation Support

{table(support_rows, ["local_claim", "supporting_sources", "support_strength", "needs_cite_verify"])}
## Claim Policy

{table(policy_rows, ["scope", "allowed", "forbidden"])}
## Next Queue

{table(next_rows, ["priority", "stage", "name", "entry_condition", "gate", "failure_rule"])}
""")

    write_text_lf(PLAN_MD, """# Stage177 Plan

Goal: bound novelty risk with real sources before writing any paper-level claim.

Search axes follow the `survey-builder` skill:

- target baseline + proposed mechanism;
- post-baseline adjacent work;
- amortized and batch bootstrapping lineage;
- PVW packing background;
- TFHE/FHEW external-product background;
- implementation bottleneck and full-SAB throughput claims.

Gate:

- Sources must be real and linkable.
- Bounded search cannot prove novelty.
- Strong novelty claims require later citation verification, proof, and full-SAB
  benchmarks.

Decision: strong novelty claims are denied; exact full-MAT engineering proceeds.
""")

    write_text_lf(THEORY_MD, """# Stage177 Literature/Novelty Model

The project has two separable claim families:

1. Exact full-MAT PVW/MAT-SAB throughput:
   This is a systems/implementation claim measured as complete bootstrapping
   time per processed plaintext bit or lane. It can proceed with complete-SAB
   A/B tests and backend attribution.

2. Structured compact MAT-SAB:
   This would be an algorithmic representation/keygen change. Stage176 blocks
   implementation because standard key-distribution and shared-mask API closure
   remain open.

The literature gate therefore does not try to prove novelty. It records that
real adjacent work is dense enough that broad claims are unsafe. The only
allowed route is to keep claims narrow until the proof and complete-SAB evidence
exist.
""")

    write_text_lf(VARIANT_MD, """# Literature Claim Boundary for PVW/MAT-SAB

Allowed current framing:

- engineering exploration of exact full-MAT PVW/MAT-SAB for 2025/686;
- per-bit/lane throughput measured as `T_bootstrap/r`;
- negative/neutral compact proof-route findings.

Forbidden current framing:

- novel compact SAB algorithm;
- theoretical optimality of MAT external product;
- PVW packing as a new idea;
- kernel-only AVX512 speedups as complete bootstrapping acceleration.

Paper-level novelty requires a later proof, citation verification, and complete
SAB benchmark package.
""")


def write_global_updates() -> None:
    append_once(ROADMAP_MD, "## Stage 177: Verified Literature/Novelty Gate", f"""
## Stage 177: Verified Literature/Novelty Gate

Goal:

```text
Verify real related work and decide which novelty/performance claims are allowed
before continuing implementation or paper writing.
```

Status:

```text
Completed. Stage177 records {DECISION}. Strong novelty claims are denied;
the next executable route is Stage178 exact full-MAT `T_bootstrap/r`
frontier selection.
```
""")
    append_once(GOAL_MD, "Stage177 records verified literature boundary", f"""
Stage177 records verified related-work and novelty-risk evidence. Decision:
`{DECISION}`. No broad novelty claim is allowed yet; continue exact full-MAT
complete-SAB engineering and reserve compact work for proof/literature only.
""")
    append_once(CURRENT_GOAL_MD, "Treat Stage177 as the verified literature boundary", f"""
81. Treat Stage177 as the verified literature boundary:
    `{DECISION}`. Real adjacent work includes 2025/696 and prior amortized,
    batch, PVW packing, FHEW/TFHE sources. Strong novelty claims remain
    blocked; proceed to exact full-MAT `T_bootstrap/r` frontier work.
""")
    append_once(HYPOTHESIS_YAML, "H101_verified_literature_novelty_boundary", f"""
  - id: H101_verified_literature_novelty_boundary
    statement: >
      Before paper-level claims, PVW/MAT-SAB must be positioned against real
      2025/686, 2025/696, amortized/batch bootstrapping, PVW packing, and
      FHEW/TFHE external-product prior work; bounded search alone cannot prove
      novelty.
    mechanism: >
      A targeted related-work matrix separates baseline, direct adjacent,
      lineage, background, and implementation-only claims, then assigns claim
      permissions.
    status: stage177_verified_literature_novelty_gate
    evidence: docs/stage177_verified_literature_novelty_gate.md; experiments/stage177_verified_literature_novelty_gate_plan.md; theory_checks/stage177_literature_novelty_model.md; repro/stage177_verified_literature_novelty_gate/summary.csv
    current_decision: >
      {DECISION}
    failure_criteria:
      - broad novelty is claimed from bounded search
      - citations are invented or unsupported
      - 2025/696 and batch/amortized prior work are omitted from paper framing
""")
    append_once(RUN_LOG, "stage177-verified-literature-novelty-gate-001", f"""
stage177-verified-literature-novelty-gate-001,2026-07-04,{git_head()},Stage 177,web+analysis,python scripts/build_stage177_verified_literature_novelty_gate.py,10 targeted source rows,none,{DECISION},Verified related-work and novelty boundary gate.,repro/stage177_verified_literature_novelty_gate
""")
    append_once(MANIFEST, "stage177_verified_literature_novelty_gate", f"""
- stage177_verified_literature_novelty_gate: `{DECISION}`
  - `docs/stage177_verified_literature_novelty_gate.md`
  - `experiments/stage177_verified_literature_novelty_gate_plan.md`
  - `theory_checks/stage177_literature_novelty_model.md`
  - `algorithm_variants/mat_rlwe_sab_literature_claim_boundary.md`
  - `repro/stage177_verified_literature_novelty_gate/`
""")
    append_once(CHECKLIST, "Stage177 verified literature/novelty gate pack recorded", """
- [x] Stage177 verified literature/novelty gate pack recorded.
""")


def write_artifacts(paths: List[Path]) -> None:
    rows = []
    for path in paths:
        rows.append({
            "path": rel(path),
            "exists": "yes" if path.exists() else "no",
            "sha256": sha256_file(path),
            "bytes": str(path.stat().st_size) if path.exists() else "0",
        })
    write_csv(ARTIFACT_CSV, rows, ["path", "exists", "sha256", "bytes"])


def main() -> None:
    query_rows = build_queries()
    lit_rows = build_literature()
    risk_rows = build_risks()
    support_rows = build_support_rows()
    policy_rows = build_policy_rows()
    next_rows = build_next_rows()
    summary_rows = build_summary_rows(lit_rows, risk_rows)

    write_csv(QUERY_CSV, query_rows, ["axis", "query", "purpose"])
    write_csv(LITERATURE_CSV, lit_rows, ["id", "title", "authors_year", "venue_or_archive", "url", "verified_source", "relation_to_project", "similarity", "difference", "novelty_risk", "local_claim_allowed"])
    write_csv(RISK_CSV, risk_rows, ["claim", "risk", "reason", "required_next_evidence", "allowed_status"])
    write_csv(SUPPORT_CSV, support_rows, ["local_claim", "supporting_sources", "support_strength", "needs_cite_verify"])
    write_csv(POLICY_CSV, policy_rows, ["scope", "allowed", "forbidden"])
    write_csv(NEXT_CSV, next_rows, ["priority", "stage", "name", "entry_condition", "gate", "failure_rule"])
    write_csv(SUMMARY_CSV, summary_rows, ["gate", "status", "metric", "value", "evidence", "detail", "next_action"])
    write_docs(summary_rows, query_rows, lit_rows, risk_rows, support_rows, policy_rows, next_rows)
    write_global_updates()
    write_artifacts([
        OUT_MD,
        PLAN_MD,
        THEORY_MD,
        VARIANT_MD,
        SUMMARY_CSV,
        QUERY_CSV,
        LITERATURE_CSV,
        RISK_CSV,
        SUPPORT_CSV,
        POLICY_CSV,
        NEXT_CSV,
        Path(__file__),
    ])
    print(DECISION)


if __name__ == "__main__":
    main()
