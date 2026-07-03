#!/usr/bin/env python3
"""Stage196: public-source citation refresh for PVW/MAT-SAB claims."""

from __future__ import annotations

import csv
import hashlib
import re
import subprocess
from pathlib import Path
from typing import Dict, Iterable, List, Tuple
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen


ROOT = Path(__file__).resolve().parents[1]
OUT_DIR = ROOT / "repro" / "stage196_public_source_refresh"

SUMMARY_CSV = OUT_DIR / "summary.csv"
SOURCE_CSV = OUT_DIR / "source_probe.csv"
CITATION_CSV = OUT_DIR / "citation_gate.csv"
CLAIM_CSV = OUT_DIR / "claim_policy.csv"
NEXT_CSV = OUT_DIR / "next_stage_queue.csv"
ARTIFACT_CSV = OUT_DIR / "artifact_index.csv"

OUT_MD = ROOT / "docs" / "stage196_public_source_refresh.md"
PLAN_MD = ROOT / "experiments" / "stage196_public_source_refresh_plan.md"
THEORY_MD = ROOT / "theory_checks" / "stage196_citation_claim_model.md"
VARIANT_MD = ROOT / "algorithm_variants" / "mat_rlwe_sab_public_source_boundary.md"

ROADMAP_MD = ROOT / "docs" / "roadmap_stage19_plus.md"
GOAL_MD = ROOT / "docs" / "goal_sab_max_acceleration.md"
CURRENT_GOAL_MD = ROOT / "docs" / "current_codex_goal_sab_completion.md"
HYPOTHESIS_YAML = ROOT / "hypotheses" / "hypothesis_register.yaml"
RUN_LOG = ROOT / "repro" / "run_log.csv"
MANIFEST = ROOT / "repro" / "artifact_manifest.md"
CHECKLIST = ROOT / "repro" / "reproduction_checklist.md"

STAGE177_LIT = ROOT / "repro" / "stage177_verified_literature_novelty_gate" / "literature_matrix.csv"
STAGE188_SUMMARY = ROOT / "repro" / "stage188_scoped_manuscript_skeleton" / "summary.csv"
STAGE195_SUMMARY = ROOT / "repro" / "stage195_scoped_paper_repro_refresh" / "summary.csv"

DECISION = "PASS_STAGE196_PUBLIC_SOURCE_REFRESH_METADATA_VISIBLE_FULLTEXT_REVIEW_BLOCKED"

SOURCES: List[Dict[str, str]] = [
    {
        "id": "GP2025_686_HTML",
        "role": "target_baseline_metadata",
        "url": "https://eprint.iacr.org/2025/686",
    },
    {
        "id": "GP2025_686_PDF",
        "role": "target_baseline_fulltext_candidate",
        "url": "https://eprint.iacr.org/2025/686.pdf",
    },
    {
        "id": "GP2025_686_CODE",
        "role": "target_baseline_code_route",
        "url": "https://github.com/antoniocgj/Fast-Amortized-Bootstrapping",
    },
    {
        "id": "PDMHSY2025_696_HTML",
        "role": "direct_adjacent_metadata",
        "url": "https://eprint.iacr.org/2025/696",
    },
    {
        "id": "PDMHSY2025_696_PDF",
        "role": "direct_adjacent_fulltext_candidate",
        "url": "https://eprint.iacr.org/2025/696.pdf",
    },
    {
        "id": "COMMONMASK2025_2112_HTML",
        "role": "shared_mask_related_metadata",
        "url": "https://eprint.iacr.org/2025/2112",
    },
    {
        "id": "COMMONMASK2025_2112_PDF",
        "role": "shared_mask_related_fulltext_candidate",
        "url": "https://eprint.iacr.org/2025/2112.pdf",
    },
]


def rel(path: Path) -> str:
    return path.resolve().relative_to(ROOT.resolve()).as_posix()


def read_text(path: Path) -> str:
    return path.read_text(encoding="utf-8", errors="replace") if path.exists() else ""


def write_text_lf(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes((text.rstrip() + "\n").encode("utf-8"))


def write_csv(path: Path, rows: Iterable[Dict[str, str]], fields: List[str]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    normalized = [{field: row.get(field, "") for field in fields} for row in rows]
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


def sha256_bytes(data: bytes) -> str:
    h = hashlib.sha256()
    h.update(data)
    return h.hexdigest()


def sha256_file(path: Path) -> str:
    if not path.exists():
        return ""
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def clean_title(text: str) -> str:
    match = re.search(r"<title[^>]*>(.*?)</title>", text, flags=re.IGNORECASE | re.DOTALL)
    if not match:
        return ""
    title = re.sub(r"\s+", " ", match.group(1)).strip()
    return title.replace("&amp;", "&").replace("&quot;", '"')


def probe_url(source: Dict[str, str]) -> Dict[str, str]:
    url = source["url"]
    req = Request(
        url,
        headers={
            "User-Agent": "Codex-PVW-MAT-SAB-source-refresh/1.0",
            "Range": "bytes=0-4095",
        },
    )
    try:
        with urlopen(req, timeout=20) as response:
            data = response.read(4096)
            decoded = data.decode("utf-8", errors="replace")
            return {
                "id": source["id"],
                "role": source["role"],
                "url": url,
                "http_status": str(getattr(response, "status", "")),
                "reachable": "1",
                "content_type": response.headers.get("content-type", ""),
                "bytes_read": str(len(data)),
                "prefix_sha256": sha256_bytes(data),
                "title_or_marker": clean_title(decoded),
                "error": "",
            }
    except HTTPError as exc:
        data = exc.read(4096)
        return {
            "id": source["id"],
            "role": source["role"],
            "url": url,
            "http_status": str(exc.code),
            "reachable": "0",
            "content_type": exc.headers.get("content-type", ""),
            "bytes_read": str(len(data)),
            "prefix_sha256": sha256_bytes(data),
            "title_or_marker": "",
            "error": f"HTTPError:{exc.code}",
        }
    except URLError as exc:
        return {
            "id": source["id"],
            "role": source["role"],
            "url": url,
            "http_status": "",
            "reachable": "0",
            "content_type": "",
            "bytes_read": "0",
            "prefix_sha256": "",
            "title_or_marker": "",
            "error": f"URLError:{exc.reason}",
        }
    except Exception as exc:
        return {
            "id": source["id"],
            "role": source["role"],
            "url": url,
            "http_status": "",
            "reachable": "0",
            "content_type": "",
            "bytes_read": "0",
            "prefix_sha256": "",
            "title_or_marker": "",
            "error": f"{type(exc).__name__}:{exc}",
        }


def by_id(rows: List[Dict[str, str]], source_id: str) -> Dict[str, str]:
    for row in rows:
        if row.get("id") == source_id:
            return row
    return {}


def build_citation_rows(source_rows: List[Dict[str, str]]) -> List[Dict[str, str]]:
    target_html = by_id(source_rows, "GP2025_686_HTML")
    target_pdf = by_id(source_rows, "GP2025_686_PDF")
    code = by_id(source_rows, "GP2025_686_CODE")
    adjacent = by_id(source_rows, "PDMHSY2025_696_HTML")
    common_mask = by_id(source_rows, "COMMONMASK2025_2112_HTML")
    return [
        {
            "gate": "target_686_metadata",
            "status": "PASS" if target_html.get("reachable") == "1" else "FAIL",
            "evidence": rel(SOURCE_CSV),
            "claim_allowed": "Bibliographic/source-existence metadata only.",
            "claim_blocked": "Theorem-level statements, exact algorithm-step citations, and proof claims until reviewed full text is available.",
        },
        {
            "gate": "target_686_fulltext_review",
            "status": "BLOCKED" if target_pdf.get("http_status") == "403" else "REVIEW_REQUIRED",
            "evidence": rel(SOURCE_CSV),
            "claim_allowed": "No full-text-derived claim from the live PDF route in this environment.",
            "claim_blocked": "Do not cite specific 2025/686 theorem, equation, or experiment text from metadata alone.",
        },
        {
            "gate": "target_686_code_route",
            "status": "PASS" if code.get("reachable") == "1" else "FAIL",
            "evidence": rel(SOURCE_CSV),
            "claim_allowed": "Code-route visibility and implementation provenance checks.",
            "claim_blocked": "Do not treat repository visibility as proof of paper claims.",
        },
        {
            "gate": "post_686_adjacent_metadata",
            "status": "PASS" if adjacent.get("reachable") == "1" else "FAIL",
            "evidence": rel(SOURCE_CSV),
            "claim_allowed": "Related-work existence and novelty-risk reminder.",
            "claim_blocked": "Do not claim dominance or detailed comparison without reviewed text and reproduced benchmarks.",
        },
        {
            "gate": "shared_mask_related_metadata",
            "status": "PASS" if common_mask.get("reachable") == "1" else "FAIL",
            "evidence": rel(SOURCE_CSV),
            "claim_allowed": "Related-work risk exists for shared/common-mask multiple-body ideas.",
            "claim_blocked": "Do not use this metadata alone to assert exact overlap or novelty defeat.",
        },
    ]


def build_claim_rows() -> List[Dict[str, str]]:
    return [
        {
            "claim_scope": "implemented_exact_full_mat_speedup",
            "allowed_wording": "The local exact full-MAT PVW/MAT-SAB path has scoped complete-SAB T_bootstrap/r evidence under recorded conditions.",
            "forbidden_wording": "This proves final MAT-RLWE SAB optimality.",
            "required_evidence": "repro/stage178_fullmat_perbit_frontier/per_bit_throughput.csv; repro/stage195_scoped_paper_repro_refresh/final_claim_ledger.csv",
        },
        {
            "claim_scope": "2025_686_base_algorithm",
            "allowed_wording": "2025/686 is the target baseline/source line by public metadata and code-route evidence.",
            "forbidden_wording": "Specific theorem, equation, proof, or experiment claims from 2025/686 without reviewed full text.",
            "required_evidence": rel(SOURCE_CSV),
        },
        {
            "claim_scope": "related_work_novelty",
            "allowed_wording": "Adjacent public metadata requires conservative novelty framing and later full-text comparison.",
            "forbidden_wording": "Broad novelty or superiority over related work from metadata-only probes.",
            "required_evidence": f"{rel(STAGE177_LIT)}; {rel(SOURCE_CSV)}",
        },
        {
            "claim_scope": "compact_shared_output",
            "allowed_wording": "Compact/shared-output MAT-SAB remains a proof-only route with recorded blockers.",
            "forbidden_wording": "Compact/shared-output MAT-SAB is implemented or benchmarked as complete SAB.",
            "required_evidence": "repro/stage192_compact_admission_route_selection/summary.csv",
        },
    ]


def build_next_rows(source_rows: List[Dict[str, str]]) -> List[Dict[str, str]]:
    pdf_blocked = by_id(source_rows, "GP2025_686_PDF").get("http_status") == "403"
    return [
        {
            "priority": "P0",
            "next_stage": "external_fulltext_intake",
            "entry_condition": "A reviewed 2025/686 PDF or accepted manuscript is supplied by path.",
            "gate": "Extract theorem/algorithm/experiment anchors and verify each manuscript statement against source text.",
            "failure_rule": "If no full text is supplied or text cannot be inspected, keep theorem-level citations blocked.",
            "current_status": "blocked_by_live_pdf_403" if pdf_blocked else "review_required",
        },
        {
            "priority": "P1",
            "next_stage": "scoped_manuscript_citation_support_bank",
            "entry_condition": "Use only metadata, local experimental artifacts, and already verified claim boundaries.",
            "gate": "Every paragraph label must be supported by source_probe, local repro evidence, or explicitly marked unsupported.",
            "failure_rule": "Any theorem-level or novelty sentence without full-text source support is removed.",
            "current_status": "ready_as_metadata_only",
        },
        {
            "priority": "P2",
            "next_stage": "implementation_resume_gate",
            "entry_condition": "A new addmul/DFT/backend mechanism or compact proof evidence is supplied.",
            "gate": "Run correctness, noise/resource, complete-SAB T_bootstrap/r, and claim-policy gates before promotion.",
            "failure_rule": "No code branch opens from citation metadata alone.",
            "current_status": "waiting_new_mechanism_or_proof",
        },
    ]


def build_summary_rows(source_rows: List[Dict[str, str]], citation_rows: List[Dict[str, str]]) -> List[Dict[str, str]]:
    reachable = sum(1 for row in source_rows if row.get("reachable") == "1")
    pdf_403 = sum(1 for row in source_rows if row.get("role", "").endswith("fulltext_candidate") and row.get("http_status") == "403")
    inputs_ok = STAGE177_LIT.exists() and STAGE188_SUMMARY.exists() and STAGE195_SUMMARY.exists()
    fulltext_pass = any(row["gate"] == "target_686_fulltext_review" and row["status"] == "PASS" for row in citation_rows)
    return [
        {
            "gate": "stage196_inputs",
            "status": "PASS" if inputs_ok else "FAIL",
            "metric": "required_prior_artifacts_present",
            "value": "1" if inputs_ok else "0",
            "evidence": f"{rel(STAGE177_LIT)}; {rel(STAGE188_SUMMARY)}; {rel(STAGE195_SUMMARY)}",
            "detail": "Stage196 refreshes public-source status after the scoped paper/repro package.",
            "next_action": "Repair missing prior artifacts before using this stage.",
        },
        {
            "gate": "stage196_public_metadata",
            "status": "PASS" if reachable >= 4 else "WEAK",
            "metric": "reachable_sources",
            "value": str(reachable),
            "evidence": rel(SOURCE_CSV),
            "detail": "Public metadata/code routes were probed with bounded byte reads.",
            "next_action": "Use as source-existence evidence only.",
        },
        {
            "gate": "stage196_fulltext_review",
            "status": "BLOCKED" if not fulltext_pass else "PASS",
            "metric": "fulltext_candidates_http403",
            "value": str(pdf_403),
            "evidence": rel(CITATION_CSV),
            "detail": "The live direct PDF route does not provide reviewed full text in this environment.",
            "next_action": "Supply a local reviewed PDF path before theorem-level citation work.",
        },
        {
            "gate": "stage196_decision",
            "status": DECISION,
            "metric": "goal_status",
            "value": "active",
            "evidence": rel(SUMMARY_CSV),
            "detail": "Source metadata refreshed; stronger paper claims remain blocked by full-text review.",
            "next_action": "Build only metadata-safe citation support or ingest a full-text artifact.",
        },
    ]


def write_docs(
    source_rows: List[Dict[str, str]],
    citation_rows: List[Dict[str, str]],
    claim_rows: List[Dict[str, str]],
    next_rows: List[Dict[str, str]],
    summary_rows: List[Dict[str, str]],
) -> None:
    write_text_lf(
        OUT_MD,
        f"""# Stage196 Public Source Refresh

Decision: `{DECISION}`.

Stage196 refreshes the public-source boundary after Stage195. It records which
metadata/code routes are reachable now and which paper claims remain blocked.
The result is deliberately conservative: public metadata can support source
existence and related-work risk, but it cannot support theorem-level citations.

## Gate Summary

{table(summary_rows, ["gate", "status", "metric", "value", "evidence", "detail", "next_action"])}
## Source Probe

{table(source_rows, ["id", "role", "url", "http_status", "reachable", "content_type", "bytes_read", "title_or_marker", "error"])}
## Citation Gate

{table(citation_rows, ["gate", "status", "evidence", "claim_allowed", "claim_blocked"])}
## Claim Policy

{table(claim_rows, ["claim_scope", "allowed_wording", "forbidden_wording", "required_evidence"])}
## Next Queue

{table(next_rows, ["priority", "next_stage", "entry_condition", "gate", "failure_rule", "current_status"])}
""",
    )

    write_text_lf(
        PLAN_MD,
        """# Stage196 Plan

Goal: refresh public sources without converting metadata into unsupported
paper claims.

Method:

- probe target 2025/686 metadata, PDF candidate, and code route;
- probe direct adjacent 2025/696 metadata/PDF candidate;
- probe shared-mask related metadata/PDF candidate;
- record byte-prefix hashes and HTTP status for reproducibility;
- update the claim ledger so only metadata-safe statements are allowed.

Gate:

- source existence can be supported by reachable metadata or code pages;
- theorem/equation/proof/experiment citations require reviewed full text;
- no implementation branch opens from citation metadata alone.
""",
    )

    write_text_lf(
        THEORY_MD,
        """# Stage196 Citation Claim Model

There are three evidence levels:

1. Metadata visible:
   supports title/source existence and related-work risk only.
2. Full text reviewed:
   required before citing theorem, algorithm, equation, proof, or experiment
   statements from the paper.
3. Local reproduction evidence:
   required for any PVW/MAT-SAB performance, noise, resource, or implementation
   claim.

Stage196 reaches level 1 for public metadata/code routes and preserves the
level-2 blocker for 2025/686 theorem-level citation work.
""",
    )

    write_text_lf(
        VARIANT_MD,
        """# Public Source Boundary for MAT-RLWE SAB

This is not a new algorithm variant. It is the source boundary used by the
MAT-RLWE/r-body SAB research loop:

- exact full-MAT speedup claims must cite local complete-SAB `T_bootstrap/r`
  artifacts;
- 2025/686 baseline statements may use public metadata only at a bibliographic
  level until full text is reviewed;
- compact/shared-output MAT-SAB remains proof-only;
- related-work novelty wording remains conservative.
""",
    )


def update_global_docs() -> None:
    append_once(
        ROADMAP_MD,
        "## Stage 196: Public Source Refresh",
        f"""
## Stage 196: Public Source Refresh

Goal:

```text
Refresh public source and citation status after the scoped Stage195 paper/repro
package, without upgrading metadata into theorem-level claims.
```

Status:

```text
Completed. Stage196 records {DECISION}. Public metadata/code routes are
visible, but reviewed full-text citation work for 2025/686 remains blocked in
the current environment.
```
""",
    )

    append_once(
        GOAL_MD,
        "Stage196 records public source refresh",
        f"""
Stage196 records public source refresh. Decision: `{DECISION}`. It preserves
the current scoped `T_bootstrap/r` implementation claim while blocking
theorem-level 2025/686 citations until reviewed full text is supplied.
""",
    )

    append_once(
        CURRENT_GOAL_MD,
        "Treat Stage196 as public source refresh",
        f"""
100. Treat Stage196 as public source refresh:
    `{DECISION}`. Public metadata/code routes are visible, but theorem-level
    2025/686 citation review remains blocked by unavailable reviewed full text.
    No implementation branch opens from metadata alone.
""",
    )

    append_once(
        HYPOTHESIS_YAML,
        "H120_public_source_refresh",
        f"""
  - id: H120_public_source_refresh
    statement: >
      Public metadata can support source-existence and related-work-risk
      statements, but cannot support theorem-level 2025/686 claims or new
      implementation branches.
    mechanism: >
      Stage196 probes target baseline, adjacent, shared-mask, and code routes
      with bounded byte reads, then maps each source status to allowed and
      blocked claim scopes.
    status: stage196_public_source_refresh
    evidence: docs/stage196_public_source_refresh.md; experiments/stage196_public_source_refresh_plan.md; theory_checks/stage196_citation_claim_model.md; repro/stage196_public_source_refresh/summary.csv
    current_decision: >
      {DECISION}
    failure_criteria:
      - metadata-only source probes are used for theorem, equation, proof, or experiment citations
      - related-work metadata is used as novelty proof
      - citation refresh opens a code branch without correctness/performance gates
""",
    )

    append_once(
        RUN_LOG,
        "stage196-public-source-refresh-001",
        f"""
stage196-public-source-refresh-001,2026-07-04,{git_head()},Stage 196,network+analysis,python scripts/build_stage196_public_source_refresh.py,public metadata/source probe,none,{DECISION},Public source refresh and citation boundary gate.,repro/stage196_public_source_refresh
""",
    )

    append_once(
        MANIFEST,
        "stage196_public_source_refresh",
        f"""
- stage196_public_source_refresh: `{DECISION}`
  - `docs/stage196_public_source_refresh.md`
  - `experiments/stage196_public_source_refresh_plan.md`
  - `theory_checks/stage196_citation_claim_model.md`
  - `algorithm_variants/mat_rlwe_sab_public_source_boundary.md`
  - `repro/stage196_public_source_refresh/`
""",
    )

    append_once(CHECKLIST, "Stage196 public source refresh recorded", """
- [x] Stage196 public source refresh recorded.
""")


def write_artifacts(paths: List[Path]) -> None:
    rows = []
    for path in paths:
        rows.append(
            {
                "path": rel(path),
                "exists": "yes" if path.exists() else "no",
                "sha256": sha256_file(path),
                "bytes": str(path.stat().st_size) if path.exists() else "0",
            }
        )
    write_csv(ARTIFACT_CSV, rows, ["path", "exists", "sha256", "bytes"])


def main() -> None:
    source_rows = [probe_url(source) for source in SOURCES]
    citation_rows = build_citation_rows(source_rows)
    claim_rows = build_claim_rows()
    next_rows = build_next_rows(source_rows)
    summary_rows = build_summary_rows(source_rows, citation_rows)

    write_csv(
        SOURCE_CSV,
        source_rows,
        ["id", "role", "url", "http_status", "reachable", "content_type", "bytes_read", "prefix_sha256", "title_or_marker", "error"],
    )
    write_csv(
        CITATION_CSV,
        citation_rows,
        ["gate", "status", "evidence", "claim_allowed", "claim_blocked"],
    )
    write_csv(
        CLAIM_CSV,
        claim_rows,
        ["claim_scope", "allowed_wording", "forbidden_wording", "required_evidence"],
    )
    write_csv(
        NEXT_CSV,
        next_rows,
        ["priority", "next_stage", "entry_condition", "gate", "failure_rule", "current_status"],
    )
    write_csv(
        SUMMARY_CSV,
        summary_rows,
        ["gate", "status", "metric", "value", "evidence", "detail", "next_action"],
    )
    write_docs(source_rows, citation_rows, claim_rows, next_rows, summary_rows)
    update_global_docs()
    write_artifacts(
        [
            OUT_MD,
            PLAN_MD,
            THEORY_MD,
            VARIANT_MD,
            SUMMARY_CSV,
            SOURCE_CSV,
            CITATION_CSV,
            CLAIM_CSV,
            NEXT_CSV,
            Path(__file__),
        ]
    )
    print(DECISION)


if __name__ == "__main__":
    main()
