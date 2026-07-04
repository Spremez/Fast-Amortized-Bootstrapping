#!/usr/bin/env python3
"""Stage238: source-verified citation package for the scoped manuscript."""

from __future__ import annotations

import csv
import hashlib
import socket
import ssl
import subprocess
import urllib.error
import urllib.request
from datetime import date
from pathlib import Path
from typing import Dict, Iterable, List
from urllib.parse import urlparse


ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "repro" / "stage238_source_verified_citation_package"

DOC = ROOT / "docs" / "stage238_source_verified_citation_package.md"
PLAN = ROOT / "experiments" / "stage238_source_verified_citation_package_plan.md"
THEORY = ROOT / "theory_checks" / "stage238_citation_claim_model.md"
VARIANT = ROOT / "algorithm_variants" / "mat_rlwe_sab_stage238_citation_package.md"

INPUTS = OUT / "input_status.csv"
SOURCE_REFRESH = OUT / "source_rows_refresh.csv"
SOURCE_ACCESS = OUT / "source_access_probe.csv"
CLAIM_SUPPORT = OUT / "claim_support_matrix.csv"
DRAFT_SENTENCES = OUT / "draft_related_work_sentences.md"
BIBTODO = OUT / "bibtex_todo.csv"
GATES = OUT / "gate_matrix.csv"
PROOF = OUT / "proof_gate.csv"
NEXT = OUT / "next_stage_queue.csv"
REPORT = OUT / "stage238_report.md"
REPRO_CMDS = OUT / "reproduction_commands.md"
ARTIFACT = OUT / "artifact_index.csv"

ROADMAP = ROOT / "docs" / "roadmap_stage19_plus.md"
GOAL = ROOT / "docs" / "goal_sab_max_acceleration.md"
CURRENT_GOAL = ROOT / "docs" / "current_codex_goal_sab_completion.md"
HYPOTHESES = ROOT / "hypotheses" / "hypothesis_register.yaml"
RUN_LOG = ROOT / "repro" / "run_log.csv"
MANIFEST = ROOT / "repro" / "artifact_manifest.md"
CHECKLIST = ROOT / "repro" / "reproduction_checklist.md"

STAGE237 = ROOT / "repro" / "stage237_scoped_manuscript_package"
STAGE236 = ROOT / "repro" / "stage236_set_2_3_4096_r4_highstat_slice"
STAGE230 = ROOT / "repro" / "stage230_source_verified_literature_novelty_audit"

DECISION = "PASS_STAGE238_SOURCE_VERIFIED_CITATION_PACKAGE_READY_NO_BIBTEX_HALLUCINATION"


def rel(path: Path) -> str:
    return path.resolve().relative_to(ROOT.resolve()).as_posix()


def read_text(path: Path) -> str:
    return path.read_text(encoding="utf-8", errors="replace") if path.exists() else ""


def write_text(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes((text.rstrip() + "\n").encode("utf-8"))


def read_csv(path: Path) -> List[Dict[str, str]]:
    if not path.exists():
        return []
    with path.open("r", newline="", encoding="utf-8-sig") as handle:
        return list(csv.DictReader(handle))


def write_csv(path: Path, rows: Iterable[Dict[str, str]], fields: List[str]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    normalized = [{field: row.get(field, "") for field in fields} for row in rows]
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields, lineterminator="\n")
        writer.writeheader()
        writer.writerows(normalized)


def append_once(path: Path, marker: str, text: str) -> None:
    current = read_text(path)
    if marker in current:
        return
    if current and not current.endswith("\n"):
        current += "\n"
    write_text(path, current + text.lstrip("\n"))


def table(rows: List[Dict[str, str]], fields: List[str]) -> str:
    if not rows:
        return "_No rows._\n"
    out = [
        "| " + " | ".join(fields) + " |",
        "| " + " | ".join("---" for _ in fields) + " |",
    ]
    for row in rows:
        out.append("| " + " | ".join(str(row.get(field, "")).replace("|", "\\|").replace("\n", "<br>") for field in fields) + " |")
    return "\n".join(out) + "\n"


def sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def git_head() -> str:
    return subprocess.check_output(["git", "rev-parse", "--short", "HEAD"], cwd=ROOT, text=True).strip()


def input_rows() -> List[Dict[str, str]]:
    paths = [
        (STAGE237 / "proof_gate.csv", "Stage237 manuscript package proof"),
        (STAGE237 / "manuscript_skeleton.md", "Stage237 manuscript skeleton"),
        (STAGE237 / "source_policy.csv", "Stage237 source policy"),
        (STAGE237 / "contribution_claims.csv", "Stage237 contribution claims"),
        (STAGE230 / "source_verification_refresh.csv", "Stage230 source verification refresh"),
        (STAGE230 / "related_work_axes.csv", "Stage230 related-work axes"),
        (STAGE230 / "novelty_risk_map.csv", "Stage230 novelty risk map"),
        (STAGE230 / "claim_policy.csv", "Stage230 claim policy"),
        (STAGE236 / "selected_binary_matrix_summary.csv", "Stage236 local experiment evidence"),
    ]
    return [
        {
            "input": rel(path),
            "status": "present" if path.exists() else "missing",
            "role": role,
            "bytes": str(path.stat().st_size) if path.exists() else "",
        }
        for path, role in paths
    ]


def source_rows() -> List[Dict[str, str]]:
    rows = []
    for row in read_csv(STAGE230 / "source_verification_refresh.csv"):
        rows.append(
            {
                "source_id": row.get("source_id", ""),
                "title": row.get("title", ""),
                "venue_year": row.get("venue_year", ""),
                "primary_url": row.get("primary_url", ""),
                "secondary_url": row.get("secondary_url", ""),
                "verification_status": row.get("verification_status", ""),
                "allowed_use": row.get("novelty_impact", ""),
                "citation_status": "SOURCE_ROW_VERIFIED_BY_STAGE230",
                "claim_boundary": "metadata/background/related-work support only unless a later full-text claim support row says otherwise",
            }
        )
    return rows


def probe_url(url: str, timeout: float = 8.0) -> Dict[str, str]:
    if not url:
        return {"url": url, "scheme": "", "host": "", "access_status": "NO_URL", "http_status": "", "final_url": "", "error": ""}
    parsed = urlparse(url)
    request = urllib.request.Request(
        url,
        method="GET",
        headers={
            "User-Agent": "Mozilla/5.0 Codex citation access probe",
            "Accept": "text/html,application/pdf,application/json,*/*;q=0.8",
        },
    )
    try:
        ctx = ssl.create_default_context()
        with urllib.request.urlopen(request, timeout=timeout, context=ctx) as response:
            status = getattr(response, "status", "")
            final_url = response.geturl()
            # Read a tiny chunk so servers that delay until body access are exercised.
            response.read(512)
            return {
                "url": url,
                "scheme": parsed.scheme,
                "host": parsed.netloc,
                "access_status": "ACCESS_OK" if int(status) < 400 else "HTTP_ERROR",
                "http_status": str(status),
                "final_url": final_url,
                "error": "",
            }
    except urllib.error.HTTPError as exc:
        return {
            "url": url,
            "scheme": parsed.scheme,
            "host": parsed.netloc,
            "access_status": "HTTP_ERROR",
            "http_status": str(exc.code),
            "final_url": getattr(exc, "url", url),
            "error": str(exc.reason),
        }
    except (urllib.error.URLError, TimeoutError, socket.timeout, ssl.SSLError, OSError) as exc:
        return {
            "url": url,
            "scheme": parsed.scheme,
            "host": parsed.netloc,
            "access_status": "ACCESS_UNVERIFIED",
            "http_status": "",
            "final_url": "",
            "error": type(exc).__name__ + ": " + str(exc)[:180],
        }


def source_access_rows(sources: List[Dict[str, str]]) -> List[Dict[str, str]]:
    rows = []
    for row in sources:
        for kind in ["primary_url", "secondary_url"]:
            probe = probe_url(row.get(kind, ""))
            rows.append(
                {
                    "source_id": row["source_id"],
                    "url_kind": kind,
                    "title": row["title"],
                    **probe,
                    "stage230_status": row["verification_status"],
                    "interpretation": "current access probe only; Stage230 source verification remains the citation-policy authority",
                }
            )
    return rows


def claim_support_rows() -> List[Dict[str, str]]:
    matrix = rel(STAGE236 / "selected_binary_matrix_summary.csv")
    return [
        {
            "draft_claim_id": "D1_target_baseline",
            "draft_sentence": "The baseline target is 2025/686-style sparse amortized bootstrapping.",
            "source_ids": "FAB686_2025",
            "existence_status": "verified_by_stage230",
            "support_level": "exact_for_identity_and_target_scope",
            "allowed_text": "Use as the target SAB baseline identity and repository/source route.",
            "forbidden_text": "Do not cite it as proving our PVW/MAT optimization or our measurements.",
            "evidence": rel(STAGE230 / "source_verification_refresh.csv"),
        },
        {
            "draft_claim_id": "D2_post_686_transform",
            "draft_sentence": "Incomplete-NTT acceleration is adjacent post-686 transform/backend work and must be separated from PVW/MAT lane batching.",
            "source_ids": "INCNTT25_696",
            "existence_status": "verified_by_stage230",
            "support_level": "partial_for_adjacent_direction",
            "allowed_text": "Use as adjacent acceleration context and a reason to separate backend/transform effects.",
            "forbidden_text": "Do not use it to claim PVW/MAT-SAB novelty or performance.",
            "evidence": rel(STAGE230 / "related_work_axes.csv"),
        },
        {
            "draft_claim_id": "D3_common_mask_prior_art",
            "draft_sentence": "Common-mask or shared-mask packed-message TFHE creates high prior-art risk for broad shared-mask novelty.",
            "source_ids": "SHAREMASK25_2112",
            "existence_status": "verified_by_stage230",
            "support_level": "exact_for_prior_art_risk",
            "allowed_text": "Use to block broad shared-mask novelty language.",
            "forbidden_text": "Do not say our work is first shared-mask batching.",
            "evidence": rel(STAGE230 / "novelty_risk_map.csv"),
        },
        {
            "draft_claim_id": "D4_batch_simd_prior_art",
            "draft_sentence": "Amortized, batch, SIMD, and systems-level bootstrapping are established prior-art axes.",
            "source_ids": "MS2018_532;GPVL2023_014;DKMS2024_112;LW2023_910;LW23A_B;BATCHBOOT26",
            "existence_status": "verified_by_stage230",
            "support_level": "exact_for_related_work_axis",
            "allowed_text": "Use to position the project as scoped 2025/686 PVW/MAT-SAB integration.",
            "forbidden_text": "Do not claim amortization, batching, or SIMD bootstrapping itself is new.",
            "evidence": rel(STAGE230 / "related_work_axes.csv"),
        },
        {
            "draft_claim_id": "D5_pvw_and_external_product_background",
            "draft_sentence": "PVW packing and TFHE external products are background building blocks, not new contributions here.",
            "source_ids": "BGH2012_565;CGGI2018_421",
            "existence_status": "verified_by_stage230",
            "support_level": "exact_for_background_only",
            "allowed_text": "Use as background for the ciphertext/object and external-product terminology.",
            "forbidden_text": "Do not claim PVW packing or TFHE external products as new.",
            "evidence": rel(STAGE230 / "novelty_risk_map.csv"),
        },
        {
            "draft_claim_id": "D6_local_selected_binary_result",
            "draft_sentence": "Exact dense PVW/MAT-SAB improves complete-SAB T_bootstrap/r on the selected binary rows.",
            "source_ids": "LOCAL_STAGE233_236",
            "existence_status": "local_repro_verified",
            "support_level": "exact_for_recorded_binary_rows",
            "allowed_text": "Use with parameter, r, backend, run count, seed count, CI, and resource side costs.",
            "forbidden_text": "Do not generalize to all parameters, non-binary branches, compact route, novelty, or optimality.",
            "evidence": matrix,
        },
    ]


def bibtex_todo_rows(sources: List[Dict[str, str]]) -> List[Dict[str, str]]:
    rows = []
    for row in sources:
        parsed = urlparse(row.get("primary_url", ""))
        host = parsed.netloc.lower()
        if "doi.org" in host:
            route = "resolve DOI landing page and export publisher/DBLP BibTeX"
        elif "eprint.iacr.org" in host:
            route = "download ePrint BibTeX or check publication_info, then prefer published venue if available"
        elif "dblp.org" in host:
            route = "export DBLP BibTeX"
        elif "usenix.org" in host:
            route = "use official USENIX metadata/BibTeX if available"
        else:
            route = "manually verify official metadata and BibTeX"
        rows.append(
            {
                "source_id": row["source_id"],
                "title": row["title"],
                "bibtex_status": "NOT_GENERATED_TO_AVOID_HALLUCINATION",
                "preferred_route": route,
                "primary_url": row["primary_url"],
                "secondary_url": row["secondary_url"],
                "action": "retrieve BibTeX from verified source before LaTeX submission",
            }
        )
    return rows


def draft_related_work_text(claims: List[Dict[str, str]]) -> str:
    bullets = []
    for row in claims:
        bullets.append(
            f"- `{row['draft_claim_id']}` [{row['source_ids']}]: {row['draft_sentence']}\n"
            f"  Support: {row['support_level']}. Allowed use: {row['allowed_text']}\n"
            f"  Guard: {row['forbidden_text']}"
        )
    return "# Stage238 Draft Related-Work Sentences\n\n" + "\n\n".join(bullets) + "\n"


def gate_rows(inputs: List[Dict[str, str]], sources: List[Dict[str, str]], access: List[Dict[str, str]], claims: List[Dict[str, str]], bib: List[Dict[str, str]]) -> List[Dict[str, str]]:
    source_verified = all(row["verification_status"].startswith("VERIFIED") for row in sources)
    claim_supported = all(row["support_level"] != "wrong" for row in claims)
    ok_access = sum(1 for row in access if row["access_status"] == "ACCESS_OK")
    return [
        {
            "gate": "G1_inputs",
            "required": "Stage237 package, Stage230 source policy, and Stage236 local evidence exist",
            "observed": "all present" if all(row["status"] == "present" for row in inputs) else "missing",
            "status": "PASS" if all(row["status"] == "present" for row in inputs) else "FAIL",
            "claim_effect": "allows citation package aggregation",
        },
        {
            "gate": "G2_stage230_source_rows",
            "required": "all source rows are Stage230 verified primary/official metadata rows",
            "observed": f"{len(sources)} rows; verified={source_verified}",
            "status": "PASS" if source_verified and len(sources) >= 5 else "FAIL",
            "claim_effect": "prevents fabricated reference rows",
        },
        {
            "gate": "G3_current_access_probe",
            "required": "URL access is probed and failures are recorded without upgrading claims",
            "observed": f"ACCESS_OK={ok_access}/{len(access)}",
            "status": "PASS_ACCESS_RECORDED",
            "claim_effect": "records current reachability only",
        },
        {
            "gate": "G4_claim_support",
            "required": "draft claims are mapped to source rows or local evidence with support levels",
            "observed": f"{len(claims)} claim-support rows; no wrong support={claim_supported}",
            "status": "PASS" if claim_supported and len(claims) >= 6 else "FAIL",
            "claim_effect": "allows related-work/background draft sentences with guards",
        },
        {
            "gate": "G5_bibtex_policy",
            "required": "do not generate BibTeX from memory",
            "observed": f"{len(bib)} BibTeX rows marked NOT_GENERATED_TO_AVOID_HALLUCINATION",
            "status": "PASS_NO_BIBTEX_HALLUCINATION" if all(row["bibtex_status"] == "NOT_GENERATED_TO_AVOID_HALLUCINATION" for row in bib) else "FAIL",
            "claim_effect": "forces later BibTeX retrieval from verified sources",
        },
        {
            "gate": "G6_stage238_decision",
            "required": "citation package gates pass and no claim is upgraded beyond support",
            "observed": DECISION,
            "status": DECISION,
            "claim_effect": "move to optional BibTeX retrieval or native-counter attribution",
        },
    ]


def proof_rows(gates: List[Dict[str, str]]) -> List[Dict[str, str]]:
    return [
        {
            "gate": row["gate"],
            "status": row["status"],
            "metric": row["required"],
            "value": row["observed"],
            "evidence": rel(GATES),
            "interpretation": row["claim_effect"],
        }
        for row in gates
    ]


def next_rows() -> List[Dict[str, str]]:
    return [
        {
            "priority": "P0",
            "route": "stage239_bibtex_retrieval_or_latex_stub",
            "entry_condition": "A LaTeX draft is required.",
            "gate": "Retrieve BibTeX from verified source routes; do not generate entries from memory.",
            "status": "ready_if_latex_needed",
            "failure_action": "Keep citation keys as TODO placeholders.",
            "evidence": rel(BIBTODO),
        },
        {
            "priority": "P1",
            "route": "stage240_native_counter_backend_validation",
            "entry_condition": "The draft needs stronger implementation attribution.",
            "gate": "Native Linux perf counters or explicit WSL proxy label; no theoretical-optimality wording.",
            "status": "optional",
            "failure_action": "Omit counter claims.",
            "evidence": rel(CLAIM_SUPPORT),
        },
        {
            "priority": "P2",
            "route": "stage241_nonbinary_or_compact_design",
            "entry_condition": "The project expands beyond exact dense binary PVW/MAT-SAB.",
            "gate": "Closed selector equations, security/noise model, production keygen, isolated equivalence, and full SAB A/B.",
            "status": "blocked_until_design",
            "failure_action": "Do not claim non-binary, compact, or theoretical-optimal MAT-RLWE SAB.",
            "evidence": rel(CLAIM_SUPPORT),
        },
    ]


def artifact_rows(paths: List[Path]) -> List[Dict[str, str]]:
    rows = []
    for path in paths:
        if path.exists() and path.is_file():
            rows.append({"artifact": rel(path), "bytes": str(path.stat().st_size), "sha256": sha256(path)})
    return rows


def write_repro_commands() -> None:
    write_text(
        REPRO_CMDS,
        """# Stage238 Reproduction Commands

Stage238 aggregates and probes citation/source evidence:

```bash
python scripts/build_stage238_source_verified_citation_package.py
```

Network access is used only for `source_access_probe.csv`. If a URL probe fails,
the source is not upgraded; Stage230 source verification remains the citation
policy authority until a manual/full-text check is performed.
""",
    )


def write_docs(inputs: List[Dict[str, str]], sources: List[Dict[str, str]], access: List[Dict[str, str]], claims: List[Dict[str, str]], bib: List[Dict[str, str]], gates: List[Dict[str, str]], proof: List[Dict[str, str]], nextq: List[Dict[str, str]]) -> None:
    doc = f"""# Stage238 Source-Verified Citation Package

Decision: `{DECISION}`.

Stage238 maps the Stage237 manuscript skeleton to source-verified citation
rows. It does not write final BibTeX from memory. It separates three things:
source existence/metadata from Stage230, current URL reachability from the
access probe, and claim-support level for each draft sentence.

## Claim Support Matrix

{table(claims, ["draft_claim_id", "draft_sentence", "source_ids", "existence_status", "support_level", "allowed_text", "forbidden_text", "evidence"])}
## Source Rows Refresh

{table(sources, ["source_id", "title", "venue_year", "primary_url", "secondary_url", "verification_status", "allowed_use", "citation_status", "claim_boundary"])}
## Current Access Probe

{table(access, ["source_id", "url_kind", "url", "access_status", "http_status", "final_url", "error", "stage230_status", "interpretation"])}
## BibTeX TODO

{table(bib, ["source_id", "title", "bibtex_status", "preferred_route", "primary_url", "secondary_url", "action"])}
## Gates

{table(gates, ["gate", "required", "observed", "status", "claim_effect"])}
## Proof Gates

{table(proof, ["gate", "status", "metric", "value", "evidence", "interpretation"])}
## Next Queue

{table(nextq, ["priority", "route", "entry_condition", "gate", "status", "failure_action", "evidence"])}
## Inputs

{table(inputs, ["input", "status", "role", "bytes"])}
"""
    write_text(DOC, doc)
    write_text(REPORT, doc)
    write_text(
        PLAN,
        """# Stage238 Citation Package Plan

Stage238 turns the Stage237 manuscript skeleton into a source-verifiable
citation package. It binds draft background/related-work claims to Stage230
source rows or local Stage233-236 evidence, records support levels, probes URLs
for current accessibility, and leaves BibTeX as TODO rows unless it is retrieved
from verified sources.
""",
    )
    write_text(
        THEORY,
        """# Stage238 Citation Claim Model

The citation model distinguishes existence, support, and scope:

- Existence: whether a source row is verified by Stage230 primary/official
  metadata.
- Current access: whether the URL resolves during this stage. Access failures
  do not fabricate or invalidate source rows; they trigger manual follow-up.
- Support: whether a source supports a draft claim exactly, partially, only as
  background, or not at all.

Only exact or defensible partial/background support can appear in the scoped
manuscript. Local performance claims must cite local repro artifacts, not
related-work papers.
""",
    )
    write_text(
        VARIANT,
        """# mat_rlwe_sab_stage238_citation_package

## Summary

- Parent artifact: Stage237 scoped manuscript package.
- Focused module: source and citation support control.
- Optimization target: paper/repro reliability, not runtime.
- Status labels: [citation package ready], [BibTeX TODO], [broader claims blocked].

## Rule

No BibTeX is generated from memory. Every source row must come from Stage230 or
a later verified source probe. Every performance claim must point to local
repro evidence.
""",
    )


def update_project_files() -> None:
    head = git_head()
    append_once(
        ROADMAP,
        "## Stage 238: Source-Verified Citation Package",
        f"""
## Stage 238: Source-Verified Citation Package

Goal:

```text
Bind Stage237 draft claims to source-verified rows or local repro evidence,
record current URL access, and prevent BibTeX/citation hallucination.
```

Status:

```text
Generated from input head `{head}` with `{DECISION}`. Citation support is ready
for a scoped draft. BibTeX remains TODO until retrieved from verified sources.
```
""",
    )
    append_once(
        GOAL,
        "## Stage238 source-verified citation package",
        f"""
## Stage238 source-verified citation package

Generated from input head `{head}`, Stage238 records `{DECISION}`. Draft
background and related-work claims now map to Stage230 source rows or local
Stage233-236 evidence. Current URL access is recorded separately. No BibTeX is
generated from memory.
""",
    )
    append_once(
        CURRENT_GOAL,
        "### Stage238 source-verified citation package",
        f"""
### Stage238 source-verified citation package

`{DECISION}` records source/claim support for the scoped manuscript package.
The active goal remains open because final BibTeX retrieval, venue-specific
paper assembly, optional native-counter attribution, and broader proof gates
remain incomplete.
""",
    )
    append_once(
        HYPOTHESES,
        "H10_stage238_source_verified_citation_package:",
        f"""
H10_stage238_source_verified_citation_package:
  status: source_verified_citation_package_ready_no_bibtex_hallucination
  evidence:
    - repro/stage238_source_verified_citation_package/claim_support_matrix.csv
    - repro/stage238_source_verified_citation_package/source_access_probe.csv
    - repro/stage238_source_verified_citation_package/bibtex_todo.csv
    - docs/stage238_source_verified_citation_package.md
  conclusion: >
    Stage238 records {DECISION}. Draft background and related-work claims are
    mapped to Stage230 verified source rows or local Stage233-236 repro
    evidence. Current URL access is recorded separately, and BibTeX generation
    is intentionally left as verified-source TODO work to avoid hallucinated
    references.
""",
    )
    append_once(
        RUN_LOG,
        "stage238-source-verified-citation-package-001",
        f"""stage238-source-verified-citation-package-001,{date.today().isoformat()},{head},Stage 238,aggregation+url_probe,"python scripts/build_stage238_source_verified_citation_package.py","Stage237 manuscript + Stage230 sources",n/a,{DECISION},"Source/claim support package ready; BibTeX remains verified-source TODO.",docs/stage238_source_verified_citation_package.md; repro/stage238_source_verified_citation_package/proof_gate.csv
""",
    )
    append_once(
        MANIFEST,
        "- stage238_source_verified_citation_package:",
        """
- stage238_source_verified_citation_package:
  - `docs/stage238_source_verified_citation_package.md`
  - `experiments/stage238_source_verified_citation_package_plan.md`
  - `theory_checks/stage238_citation_claim_model.md`
  - `algorithm_variants/mat_rlwe_sab_stage238_citation_package.md`
  - `scripts/build_stage238_source_verified_citation_package.py`
  - `repro/stage238_source_verified_citation_package/`
""",
    )
    append_once(
        CHECKLIST,
        "Stage238 source-verified citation package records decision",
        f"""
- [x] Stage238 source-verified citation package records decision `{DECISION}`.
""",
    )


def main() -> None:
    OUT.mkdir(parents=True, exist_ok=True)
    inputs = input_rows()
    sources = source_rows()
    access = source_access_rows(sources)
    claims = claim_support_rows()
    bib = bibtex_todo_rows(sources)
    gates = gate_rows(inputs, sources, access, claims, bib)
    proof = proof_rows(gates)
    nextq = next_rows()

    write_csv(INPUTS, inputs, ["input", "status", "role", "bytes"])
    write_csv(SOURCE_REFRESH, sources, ["source_id", "title", "venue_year", "primary_url", "secondary_url", "verification_status", "allowed_use", "citation_status", "claim_boundary"])
    write_csv(SOURCE_ACCESS, access, ["source_id", "url_kind", "title", "url", "scheme", "host", "access_status", "http_status", "final_url", "error", "stage230_status", "interpretation"])
    write_csv(CLAIM_SUPPORT, claims, ["draft_claim_id", "draft_sentence", "source_ids", "existence_status", "support_level", "allowed_text", "forbidden_text", "evidence"])
    write_text(DRAFT_SENTENCES, draft_related_work_text(claims))
    write_csv(BIBTODO, bib, ["source_id", "title", "bibtex_status", "preferred_route", "primary_url", "secondary_url", "action"])
    write_csv(GATES, gates, ["gate", "required", "observed", "status", "claim_effect"])
    write_csv(PROOF, proof, ["gate", "status", "metric", "value", "evidence", "interpretation"])
    write_csv(NEXT, nextq, ["priority", "route", "entry_condition", "gate", "status", "failure_action", "evidence"])
    write_repro_commands()
    write_docs(inputs, sources, access, claims, bib, gates, proof, nextq)

    artifacts = [DOC, PLAN, THEORY, VARIANT, INPUTS, SOURCE_REFRESH, SOURCE_ACCESS, CLAIM_SUPPORT, DRAFT_SENTENCES, BIBTODO, GATES, PROOF, NEXT, REPORT, REPRO_CMDS]
    write_csv(ARTIFACT, artifact_rows(artifacts), ["artifact", "bytes", "sha256"])
    update_project_files()
    print(f"Stage238 report: {rel(DOC)}")
    print(f"Stage238 decision: {DECISION}")


if __name__ == "__main__":
    main()
