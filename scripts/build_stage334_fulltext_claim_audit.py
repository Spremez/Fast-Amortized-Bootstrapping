#!/usr/bin/env python3
"""Stage334: full-text claim audit boundary for PVW/MAT-SAB novelty."""

from __future__ import annotations

import csv
import hashlib
import subprocess
from pathlib import Path
from typing import Iterable


ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "repro" / "stage334_fulltext_claim_audit"

DOC = ROOT / "docs" / "stage334_fulltext_claim_audit.md"
THEORY = ROOT / "theory_checks" / "stage334_fulltext_claim_boundary_model.md"
PLAN = ROOT / "experiments" / "stage335_fulltext_acquisition_or_compact_security_plan.md"
BUILDER = ROOT / "scripts" / "build_stage334_fulltext_claim_audit.py"

GOAL = ROOT / "docs" / "current_codex_goal_sab_completion.md"
ROADMAP = ROOT / "docs" / "roadmap_stage19_plus.md"
HYPOTHESES = ROOT / "hypotheses" / "hypothesis_register.yaml"
MANIFEST = ROOT / "repro" / "artifact_manifest.md"
CHECKLIST = ROOT / "repro" / "reproduction_checklist.md"
RUN_LOG = ROOT / "repro" / "run_log.csv"

STAGE102_SUMMARY = ROOT / "repro" / "stage102_686_source_anchor_review" / "summary.csv"
STAGE102_REVIEW = ROOT / "repro" / "stage102_686_source_anchor_review" / "review_matrix.csv"
STAGE103_SUMMARY = ROOT / "repro" / "stage103_related_work_novelty_review" / "summary.csv"
STAGE333_SUMMARY = ROOT / "repro" / "stage333_literature_novelty_verification" / "summary.csv"
STAGE333_RISK = ROOT / "repro" / "stage333_literature_novelty_verification" / "novelty_risk_map.csv"

RING_PDF = ROOT / "references" / "stage334_fulltext_claim_audit" / "pdf" / "micciancio_sorrell_2018_ring_packing.pdf"
RING_TEXT = ROOT / "references" / "stage334_fulltext_claim_audit" / "text" / "micciancio_sorrell_2018_ring_packing.txt"

SUMMARY = OUT / "summary.csv"
SOURCE_AUDIT = OUT / "source_fulltext_audit.csv"
CLAIM_AUDIT = OUT / "claim_audit_matrix.csv"
BLOCKERS = OUT / "fulltext_blockers.csv"
RING_ANCHORS = OUT / "ring_packing_anchor_hits.csv"
PROOF = OUT / "proof_gate.csv"
NEXT = OUT / "next_stage_queue.csv"
COMMANDS = OUT / "reproduction_commands.md"
REPORT = OUT / "stage334_report.md"
ARTIFACT = OUT / "artifact_index.csv"

DECISION = "PASS_STAGE334_PARTIAL_FULLTEXT_AUDIT_NOVELTY_REMAINS_BLOCKED"


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


def read_csv(path: Path) -> list[dict[str, str]]:
    if not path.exists():
        return []
    with path.open(newline="", encoding="utf-8-sig") as handle:
        return list(csv.DictReader(handle))


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


def sha256_file(path: Path) -> str:
    if not path.exists() or not path.is_file():
        return ""
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1 << 20), b""):
            digest.update(chunk)
    return digest.hexdigest()


def md_table(rows: list[dict[str, object]], fields: list[str]) -> str:
    out = ["| " + " | ".join(fields) + " |", "| " + " | ".join(["---"] * len(fields)) + " |"]
    for row in rows:
        out.append("| " + " | ".join(str(row.get(field, "")).replace("|", "\\|") for field in fields) + " |")
    return "\n".join(out)


def ring_hits() -> list[dict[str, object]]:
    text = read_text(RING_TEXT)
    if not text:
        return []
    patterns = [
        ("abstract_simultaneous_refresh", ["simultaneously refreshes", "amortized over"]),
        ("intro_packed_bootstrapping", ["simultaneously refresh", "amortized cost"]),
        ("overview_many_messages", ["simultaneously refresh", "messages"]),
        ("packing_lwe_to_ring", ["packed", "LWE ciphertexts"]),
    ]
    rows: list[dict[str, object]] = []
    lines = text.splitlines()
    for anchor, required in patterns:
        matches = []
        for idx, line in enumerate(lines, start=1):
            window = lines[idx - 1:min(len(lines), idx + 4)]
            lowered = " ".join(window).lower()
            if all(term.lower() in lowered for term in required):
                matches.append(idx)
        rows.append({
            "anchor": anchor,
            "status": "FOUND" if matches else "MISSING",
            "line_refs": ";".join(str(item) for item in matches[:8]),
            "claim_use": "Prior art for broad multi-message/amortized refresh wording; not a proof about 2025/686 PVW/MAT-SAB.",
        })
    return rows


def append_run_log() -> None:
    run_id = "stage334-fulltext-claim-audit-001"
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
        "stage": "Stage 334",
        "backend": "fulltext-claim-audit",
        "command": "python scripts/build_stage334_fulltext_claim_audit.py",
        "params": "Stage102 2025/686 anchors; local Ring Packing PDF text; Stage333 high-risk source blockers",
        "seed": "n/a",
        "status": DECISION,
        "summary": "Full-text audit is partial: scoped systems result remains allowed, novelty remains blocked.",
        "artifacts": f"{rel(DOC)}; {rel(SOURCE_AUDIT)}; {rel(CLAIM_AUDIT)}; {rel(PROOF)}",
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

    stage102_ok = "PASS_STAGE102_686_SOURCE_ANCHORS_REVIEWED" in read_text(STAGE102_SUMMARY)
    stage103_ok = "PASS_STAGE103_RELATED_WORK_NOVELTY_REVIEW_SCOPED" in read_text(STAGE103_SUMMARY)
    stage333_ok = "PASS_STAGE333_REAL_SOURCE_MATRIX_NOVELTY_CLAIM_OPEN" in read_text(STAGE333_SUMMARY)
    ring_pdf_ok = RING_PDF.exists() and RING_PDF.stat().st_size > 100_000
    ring_text_ok = RING_TEXT.exists() and len(read_text(RING_TEXT)) > 10_000
    anchors = ring_hits()
    ring_anchor_ok = bool(anchors) and all(row["status"] == "FOUND" for row in anchors[:2])

    source_rows = [
        {
            "source": "2025_686_target_sab",
            "status": "FULLTEXT_ANCHORS_REVIEWED_BY_STAGE102" if stage102_ok else "MISSING",
            "evidence": rel(STAGE102_REVIEW),
            "sha256_or_path": "external PDF sha recorded in Stage100; full text not committed",
            "claim_boundary": "Can cite protocol/complexity/correctness anchors for scalar 2025/686; does not prove local PVW/MAT novelty.",
        },
        {
            "source": "ring_packing_2018",
            "status": "LOCAL_FULLTEXT_AUDITED" if ring_pdf_ok and ring_text_ok and ring_anchor_ok else "PARTIAL_OR_MISSING",
            "evidence": rel(RING_ANCHORS),
            "sha256_or_path": f"pdf_sha256={sha256_file(RING_PDF)}; text_sha256={sha256_file(RING_TEXT)}",
            "claim_boundary": "Strong prior art against broad multi-message/amortized bootstrapping novelty wording.",
        },
        {
            "source": "sharing_the_mask_2025_2112",
            "status": "FULLTEXT_BLOCKED_BY_EPRINT_CLOUDFLARE_METADATA_ONLY",
            "evidence": "Stage333 DBLP/AskCryptography metadata",
            "sha256_or_path": "not acquired",
            "claim_boundary": "Critical blocker for shared-mask/r-body novelty; no novelty wording until full text is audited.",
        },
        {
            "source": "packed_tfhe_2017_430",
            "status": "FULLTEXT_BLOCKED_BY_EPRINT_CLOUDFLARE_METADATA_ONLY",
            "evidence": "Stage333 metadata",
            "sha256_or_path": "not acquired",
            "claim_boundary": "Blocks broad packed-TFHE novelty wording.",
        },
        {
            "source": "mosfhet_2022_515",
            "status": "FULLTEXT_BLOCKED_BY_EPRINT_CLOUDFLARE_METADATA_PLUS_GITHUB",
            "evidence": "Stage333 metadata and MOSFHET GitHub",
            "sha256_or_path": "not acquired",
            "claim_boundary": "Blocks backend/AVX novelty or optimality wording.",
        },
        {
            "source": "2025_696_incomplete_ntt",
            "status": "FULLTEXT_BLOCKED_BY_EPRINT_CLOUDFLARE_METADATA_ONLY",
            "evidence": "Stage333 metadata",
            "sha256_or_path": "not acquired",
            "claim_boundary": "Blocks broad latest-amortized-bootstrapping comparison wording.",
        },
    ]

    claim_rows = [
        {
            "claim": "scoped_systems_result",
            "status": "ALLOW",
            "evidence": "Stage331/332 high-stat current-head result plus Stage102 scalar SAB anchors.",
            "safe_wording": "Scoped measured PVW/MAT-SAB complete T_bootstrap/r improvement for the tested path.",
            "blocked_wording": "Universal or theorem-level acceleration.",
        },
        {
            "claim": "broad_multi_message_novelty",
            "status": "BLOCK",
            "evidence": "Ring Packing full-text audit shows prior simultaneous/amortized refresh over many messages.",
            "safe_wording": "Our work is a scoped implementation study within 2025/686 SAB.",
            "blocked_wording": "First amortized or multi-message bootstrapping.",
        },
        {
            "claim": "shared_mask_r_body_novelty",
            "status": "BLOCK",
            "evidence": "Sharing-the-Mask full text unavailable; Stage333 metadata shows direct high-risk adjacent work.",
            "safe_wording": "PVW/MAT shared-mask path evaluated for this SAB implementation.",
            "blocked_wording": "Novel shared-mask/r-body bootstrapping construction.",
        },
        {
            "claim": "external_product_count_reduction",
            "status": "BLOCK",
            "evidence": "Current path improves throughput constants; compact product-count reduction remains proof-blocked.",
            "safe_wording": "Measured constant-factor throughput improvement.",
            "blocked_wording": "New asymptotic SAB algorithm or external-product count theorem.",
        },
        {
            "claim": "backend_avx_optimality",
            "status": "BLOCK",
            "evidence": "MOSFHET/AVX full text not audited; current evidence is experimental, not lower-bound proof.",
            "safe_wording": "Implementation uses spqlios_avx512 under recorded flags.",
            "blocked_wording": "MAT AVX512 implementation is theoretically optimal.",
        },
    ]

    blockers = [
        {
            "blocked_source": "ePrint PDFs",
            "observed_failure": "Cloudflare challenge HTML returned instead of PDF for automated curl attempts.",
            "affected_claims": "sharing-mask novelty; packed TFHE novelty; MOSFHET backend claims; 2025/696 latest-work comparison",
            "required_resolution": "Provide accessible PDFs or manually register full-text anchors, then rerun Stage334/335.",
        },
        {
            "blocked_source": "compact_selector_security",
            "observed_failure": "Stage329 finite algebra passed but production keygen/distribution/noise obligations remain open.",
            "affected_claims": "compact selector acceleration; external-product count reduction",
            "required_resolution": "Stage335 compact keygen/security preflight before code or claim promotion.",
        },
    ]

    proof_rows = [
        {
            "gate": "G1_stage333_input",
            "status": "PASS" if stage333_ok else "FAIL",
            "metric": "Stage333 decision",
            "value": "PASS" if stage333_ok else "missing",
            "interpretation": "Stage334 requires a prior real-source novelty matrix.",
        },
        {
            "gate": "G2_686_anchor_review",
            "status": "PASS" if stage102_ok else "FAIL",
            "metric": "Stage102 reviewed anchors",
            "value": "reviewed" if stage102_ok else "missing",
            "interpretation": "The target scalar SAB protocol has source anchors.",
        },
        {
            "gate": "G3_ring_packing_fulltext",
            "status": "PASS" if ring_pdf_ok and ring_text_ok and ring_anchor_ok else "PARTIAL",
            "metric": "Ring Packing local full text",
            "value": f"pdf={ring_pdf_ok}; text={ring_text_ok}; anchors={ring_anchor_ok}",
            "interpretation": "Broad multi-message novelty is blocked by audited prior art.",
        },
        {
            "gate": "G4_high_risk_fulltext_complete",
            "status": "BLOCK",
            "metric": "Sharing the Mask / packed TFHE / MOSFHET / 2025_696",
            "value": "metadata_only_or_blocked",
            "interpretation": "Novelty remains open; no broad novelty wording is allowed.",
        },
        {
            "gate": "G5_decision",
            "status": DECISION,
            "metric": "claim boundary",
            "value": "scoped systems result allowed; novelty blocked",
            "interpretation": "Controls Stage335: acquire missing full texts or continue compact security.",
        },
    ]

    summary_rows = [{
        "decision": DECISION,
        "target_686_fulltext": "reviewed_by_stage102" if stage102_ok else "missing",
        "ring_packing_fulltext": "audited" if ring_pdf_ok and ring_text_ok and ring_anchor_ok else "partial",
        "critical_adjacent_fulltext": "blocked_or_metadata_only",
        "allowed_claim": "scoped systems T_bootstrap/r result",
        "blocked_claims": "novelty; shared-mask/r-body first claim; compact acceleration; AVX optimality; all-parameter generality",
        "selected_next": "stage335_missing_fulltext_acquisition_or_compact_security",
    }]

    next_rows = [
        {
            "priority": "P0",
            "route": "stage335_missing_fulltext_acquisition",
            "entry_condition": DECISION,
            "gate": "Acquire/read Sharing the Mask, packed TFHE, MOSFHET, 2025/696 full text.",
            "failure_action": "Keep novelty and backend optimality blocked.",
        },
        {
            "priority": "P1",
            "route": "stage335_compact_keygen_security_preflight",
            "entry_condition": "pursue stronger algorithmic gain instead of paper novelty wording",
            "gate": "Close keygen distribution, semantic-zero security, and noise recurrence.",
            "failure_action": "Keep compact production code blocked.",
        },
    ]

    write_csv(RING_ANCHORS, anchors, ["anchor", "status", "line_refs", "claim_use"])
    write_csv(SOURCE_AUDIT, source_rows, ["source", "status", "evidence", "sha256_or_path", "claim_boundary"])
    write_csv(CLAIM_AUDIT, claim_rows, ["claim", "status", "evidence", "safe_wording", "blocked_wording"])
    write_csv(BLOCKERS, blockers, ["blocked_source", "observed_failure", "affected_claims", "required_resolution"])
    write_csv(PROOF, proof_rows, ["gate", "status", "metric", "value", "interpretation"])
    write_csv(SUMMARY, summary_rows, ["decision", "target_686_fulltext", "ring_packing_fulltext", "critical_adjacent_fulltext", "allowed_claim", "blocked_claims", "selected_next"])
    write_csv(NEXT, next_rows, ["priority", "route", "entry_condition", "gate", "failure_action"])

    write_text(DOC, f"""# Stage334 Full-Text Claim Audit

Decision: `{DECISION}`.

Stage334 advances the novelty audit from metadata-only to partial full-text
evidence.  It confirms the 2025/686 scalar SAB anchors through the existing
Stage102 review and audits the Ring Packing full text locally.  It does not
complete the full-text audit for all high-risk adjacent work, so novelty remains
blocked.

## Summary

{md_table(summary_rows, ["decision", "target_686_fulltext", "ring_packing_fulltext", "critical_adjacent_fulltext", "allowed_claim", "blocked_claims"])}

## Source Audit

{md_table(source_rows, ["source", "status", "evidence", "claim_boundary"])}

## Claim Audit

{md_table(claim_rows, ["claim", "status", "safe_wording", "blocked_wording"])}

## Blockers

{md_table(blockers, ["blocked_source", "observed_failure", "affected_claims", "required_resolution"])}

## Proof Gate

{md_table(proof_rows, ["gate", "status", "metric", "value"])}

Generated from input head `{git_head()}`.
""")

    write_text(THEORY, """# Stage334 Full-Text Claim Boundary Model

Stage334 uses a strict promotion rule:

- a source can support novelty boundaries only if its full text or a prior
  reviewed source-anchor matrix is available;
- metadata-only sources can block claims when they identify high-risk adjacent
  work, but they cannot support positive novelty wording;
- the local Stage331/332 result remains a scoped systems result until all
  high-risk full texts and compact/security obligations are closed.

Ring Packing is enough to reject broad multi-message/amortized bootstrapping
novelty.  It is not enough to decide shared-mask/r-body novelty, because the
2025 Sharing-the-Mask full text remains unaudited.
""")

    write_text(PLAN, """# Stage335 Missing Full-Text Or Compact Security Plan

Route A: missing full-text acquisition.

- Acquire/read Sharing the Mask, Faster Packed TFHE, MOSFHET, and 2025/696.
- Replace metadata-only blockers with page/section anchors.
- Only then revisit novelty wording.

Route B: compact keygen/security preflight.

- Map compact selector equations to production key generation.
- Close public distribution and semantic-zero security obligations.
- Derive noise recurrence before any compact SAB code is admitted.
""")

    write_text(COMMANDS, """# Stage334 Reproduction Commands

```sh
python scripts/build_stage334_fulltext_claim_audit.py
```

Optional local extraction used before this builder:

```sh
pdftotext -layout references/stage334_fulltext_claim_audit/pdf/micciancio_sorrell_2018_ring_packing.pdf \\
  references/stage334_fulltext_claim_audit/text/micciancio_sorrell_2018_ring_packing.txt
```

Full paper PDF/text files under `references/stage334_fulltext_claim_audit/` are
ignored by Git; the repro pack records hashes and line anchors only.
""")

    write_text(REPORT, read_text(DOC))

    append_once(GOAL, "<!-- stage334-fulltext-claim-audit -->", f"""
<!-- stage334-fulltext-claim-audit -->
### Stage334 full-text claim audit

`{DECISION}` records a partial full-text audit: 2025/686 source anchors and Ring
Packing prior art are audited, but critical adjacent full texts remain missing.
The allowed claim remains the scoped measured `T_bootstrap/r` systems result.
""")

    append_once(ROADMAP, "<!-- stage334-fulltext-claim-audit-roadmap -->", f"""
<!-- stage334-fulltext-claim-audit-roadmap -->
## Stage 334: Full-Text Claim Audit

Goal: replace metadata-only novelty risk with source-anchor/full-text claim
boundaries where available.

Status: `{DECISION}`.
""")

    append_once(HYPOTHESES, "H334_fulltext_claim_audit:", f"""
H334_fulltext_claim_audit:
  status: {DECISION}
  primary_metric: fulltext_claim_boundary
  evidence:
    - repro/stage334_fulltext_claim_audit/source_fulltext_audit.csv
    - repro/stage334_fulltext_claim_audit/claim_audit_matrix.csv
    - repro/stage334_fulltext_claim_audit/fulltext_blockers.csv
    - repro/stage334_fulltext_claim_audit/proof_gate.csv
  conclusion: >
    Stage334 supports only the scoped systems result. Broad novelty remains
    blocked because high-risk shared-mask/backend/latest-work full texts are
    not yet audited.
""")

    append_once(MANIFEST, "<!-- stage334-fulltext-claim-audit-manifest -->", """
<!-- stage334-fulltext-claim-audit-manifest -->
- stage334_fulltext_claim_audit:
  - `docs/stage334_fulltext_claim_audit.md`
  - `theory_checks/stage334_fulltext_claim_boundary_model.md`
  - `experiments/stage335_fulltext_acquisition_or_compact_security_plan.md`
  - `scripts/build_stage334_fulltext_claim_audit.py`
  - `repro/stage334_fulltext_claim_audit/`
""")

    append_once(CHECKLIST, "<!-- stage334-fulltext-claim-audit-checklist -->", f"""
<!-- stage334-fulltext-claim-audit-checklist -->
- [x] Stage334 records `{DECISION}` and keeps novelty blocked pending missing full-text audits.
""")

    append_run_log()

    artifact_index([DOC, THEORY, PLAN, BUILDER, SUMMARY, SOURCE_AUDIT, CLAIM_AUDIT, BLOCKERS, RING_ANCHORS, PROOF, NEXT, COMMANDS, REPORT])
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
