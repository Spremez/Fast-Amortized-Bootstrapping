#!/usr/bin/env python3
"""Generate the deterministic Candidate D D1 novelty audit."""

from __future__ import annotations

import argparse
import csv
from io import StringIO
import os
from pathlib import Path
import sys
import tempfile
from typing import Iterable, Mapping


ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from research.mat_sab.candidate_d_literature import (  # noqa: E402
    BLOCK_D1,
    PASS_D1,
    REJECT_D1,
    ClaimComparison,
    FullTextReview,
    evaluate_candidate_d_novelty,
    load_source_registry,
    verify_fulltext,
)


REGISTRY_PATH = Path("literature/candidate_d_source_registry.json")
FULLTEXT_PATH = Path("references/candidate_d_fulltext")
OUTPUT_PATHS = (
    Path("docs/candidate_d_d1_novelty_audit.md"),
    Path("repro/candidate_d_admission/literature_sources.csv"),
    Path("repro/candidate_d_admission/claim_overlap.csv"),
    Path("repro/candidate_d_admission/novelty_gate.csv"),
)


def _csv_bytes(
    fieldnames: tuple[str, ...], rows: Iterable[Mapping[str, object]]
) -> bytes:
    stream = StringIO(newline="")
    writer = csv.DictWriter(
        stream,
        fieldnames=fieldnames,
        extrasaction="raise",
        lineterminator="\n",
    )
    writer.writeheader()
    for row in rows:
        writer.writerow(row)
    return stream.getvalue().encode("utf-8")


def _bool(value: bool | None) -> str:
    if value is None:
        return ""
    return "yes" if value else "no"


def _source_rows(reviews: tuple[FullTextReview, ...]) -> list[dict[str, object]]:
    rows = []
    for review in reviews:
        source = review.source
        rows.append(
            {
                "source_id": source.id,
                "title": source.title,
                "year": source.year,
                "official_url": source.official_url,
                "fulltext_url": source.fulltext_url,
                "registry_status": source.review_status,
                "verification_status": review.review_status,
                "pdf_sha256": review.pdf_sha256 or "",
                "text_sha256": review.text_sha256 or "",
                "page_range": review.page_range or "",
                "source_binding_sha256": review.source_binding_sha256,
                "validation_errors": " | ".join(review.validation_errors),
            }
        )
    return rows


def _claim_rows(
    comparisons: tuple[ClaimComparison, ...],
) -> list[dict[str, object]]:
    return [
        {
            "source_id": comparison.source_id,
            "review_status": comparison.review_status,
            "same_operator": _bool(comparison.same_operator),
            "same_complete_complexity": _bool(comparison.same_complexity),
            "distinct_sab_theorem": _bool(comparison.distinct_sab_theorem),
            "distinct_complete_result": _bool(
                comparison.distinct_complete_result
            ),
            "falsifiable_full_sab_endpoint": _bool(
                comparison.falsifiable_full_sab_endpoint
            ),
            "sab_operator_theorem_claim": comparison.sab_operator_theorem_claim,
            "complete_complexity_resource_claim": (
                comparison.complete_complexity_resource_claim
            ),
            "full_sab_endpoint_claim": comparison.full_sab_endpoint_claim,
            "claim_classification": comparison.claim_classification,
            "batchboot_composition": comparison.composition_with_batchboot,
            "conclusion": comparison.conclusion,
            "evidence": comparison.evidence,
        }
        for comparison in comparisons
    ]


def _gate_rows(
    decision: str,
    reviews: tuple[FullTextReview, ...],
    comparisons: tuple[ClaimComparison, ...],
) -> list[dict[str, object]]:
    complete = [review for review in reviews if review.is_complete_and_bound()]
    missing = [
        review.source.id for review in reviews if not review.is_complete_and_bound()
    ]
    fdfb = next(
        (row for row in comparisons if row.source_id == "FDFB2_2024_1376"),
        None,
    )
    if fdfb is None:
        fdfb_status = "BLOCK"
        fdfb_evidence = "mandatory FDFB2 comparison is absent"
    elif fdfb.conclusion == "SUBSUMES_CANDIDATE_D":
        fdfb_status = "REJECT"
        fdfb_evidence = fdfb.evidence
    elif fdfb.review_status == "FULLTEXT_REVIEWED":
        fdfb_status = "PASS_NARROW_CLAIM_ONLY"
        fdfb_evidence = (
            "Broad late-bound multi-function novelty overlaps FDFB2; only the "
            "bounded SAB-specific closure, complete cost, and full-SAB endpoint "
            "remain testable."
        )
    else:
        fdfb_status = "BLOCK"
        fdfb_evidence = fdfb.evidence

    if decision == PASS_D1:
        terminal_status = "PASS"
        next_action = "transition D to D1_NOVELTY_AUDIT_PASS and execute D2"
    elif decision == REJECT_D1:
        terminal_status = "REJECT"
        next_action = "skip D2-D8 and execute Task 9 prior-art rejection routing"
    else:
        terminal_status = "BLOCK"
        next_action = (
            "skip D2-D8 and execute Task 9 incomplete-evidence routing; resume "
            "only after the named full text is reviewed"
        )
    return [
        {
            "gate_id": "required_source_registry",
            "status": "PASS" if len(reviews) == 9 else "BLOCK",
            "decision": decision,
            "evidence": f"registered_sources={len(reviews)}; required_sources=9",
            "next_action": "none",
        },
        {
            "gate_id": "fulltext_claim_review",
            "status": "PASS" if not missing else "BLOCK",
            "decision": decision,
            "evidence": (
                f"complete_reviews={len(complete)}; missing_or_invalid="
                + ("|".join(missing) if missing else "none")
            ),
            "next_action": (
                "none"
                if not missing
                else "obtain, hash, anchor, and review every missing source"
            ),
        },
        {
            "gate_id": "fdfb2_operator_overlap",
            "status": fdfb_status,
            "decision": decision,
            "evidence": fdfb_evidence,
            "next_action": "retain only the narrow SAB-specific claim boundary",
        },
        {
            "gate_id": "d1_terminal_decision",
            "status": terminal_status,
            "decision": decision,
            "evidence": "fail-closed priority: missing review precedes overlap verdict",
            "next_action": next_action,
        },
    ]


def render_candidate_d_d1_markdown(
    decision: str,
    reviews: tuple[FullTextReview, ...],
) -> bytes:
    missing = [
        review.source.id for review in reviews if not review.is_complete_and_bound()
    ]
    complete_count = len(reviews) - len(missing)
    reviewed = {
        review.source.id: review.is_complete_and_bound() for review in reviews
    }
    rows = "\n".join(
        "| {id} | {status} | {pages} | {classification} |".format(
            id=review.source.id,
            status=review.review_status,
            pages=review.page_range or "n/a",
            classification=review.source.claim_classification,
        )
        for review in reviews
    )
    missing_text = ", ".join(f"`{source_id}`" for source_id in missing) or "none"
    if decision == PASS_D1:
        decision_effect = (
            "All mandatory reviews are complete and the concrete narrow claim "
            "remains testable. Candidate D may transition to D1 pass and execute "
            "D2; algorithm hot-path work remains prohibited until D3 admission."
        )
        routing_text = (
            "Transition Candidate D from `D0_BASELINE_FROZEN` to "
            "`D1_NOVELTY_AUDIT_PASS`, then execute the finite D2 closure gate."
        )
        closing_text = (
            "This result admits a narrow claim to further falsification. It is not "
            "a proved theorem, a bootstrapping speedup, or a paper claim."
        )
    elif decision == REJECT_D1:
        decision_effect = (
            "The reviewed prior art subsumes the proposed operator and complete "
            "claim. Candidate D does not advance to D2 and Tasks D2-D8 are skipped."
        )
        routing_text = (
            "Execute Task 9 with the prior-art rejection decision, route Candidate "
            "D to `REJECTED`, and start only Candidate E's security/novelty preflight."
        )
        closing_text = (
            "This is a scoped Candidate D prior-art rejection. It is not a general "
            "impossibility theorem and does not change the existing PVW/MAT-SAB result."
        )
    else:
        decision_effect = (
            "Candidate D therefore does not advance to D2, and no algorithm hot-path "
            "change is authorized by this audit."
        )
        routing_text = (
            "Keep Candidate D at `D0_BASELINE_FROZEN` until the atomic Task 9 "
            "admission controller records `BLOCK_CANDIDATE_D_INCOMPLETE_EVIDENCE`. "
            "Tasks D2-D8 are skipped for this run. The finite resume condition is a "
            "locally hash-bound, page-anchored review of every source listed above as "
            "missing; repeated network probing is not part of the loop."
        )
        closing_text = (
            "This result is not a Candidate D rejection on mathematical grounds and "
            "is not a bootstrapping speedup claim. It is a reproducible "
            "evidence-bound stop decision."
        )
    fdfb_answer = (
        "FDFB2 already exposes the broad late-bound multi-function operator: "
        "its reviewed abstract and Section 3 claim an arbitrary number of "
        "functions and multiple functions at the cost of one bootstrap."
        if reviewed.get("FDFB2_2024_1376", False)
        else "The FDFB2 operator-overlap question is unresolved because its bound review is missing."
    )
    sharing_answer = (
        "Sharing the Mask already covers the shared-mask, multiple-body "
        "ciphertext semantics and extension of FHEW/TFHE operations. Common-mask "
        "ciphertexts are prior art, not Candidate D novelty."
        if reviewed.get("SHARING_MASK_2025_2112", False)
        else "The common-mask prior-art boundary is unresolved because the Sharing the Mask review is missing."
    )
    batchboot_answer = (
        "BatchBoot attacks polynomial-multiplication, FFT, and packing costs "
        "through a different batched TFHE mechanism. It is a mandatory "
        "complete-system baseline, not evidence for Candidate D by itself."
        if reviewed.get("BATCHBOOT_SEC26", False)
        else "The BatchBoot cost and composition boundary is unresolved because its bound review is missing."
    )
    fab_answer = (
        "The reviewed 2025/686 anchors bind the binary SAB schedule, amortized "
        "complexity, security accounting, and failure target. They do not prove "
        "the proposed late-binding operator."
        if reviewed.get("FAB_2025_686", False)
        else "The target SAB source boundary is unresolved because the 2025/686 bound review is missing."
    )
    fdfb_review = next(
        (review for review in reviews if review.source.id == "FDFB2_2024_1376"),
        None,
    )
    claim = (
        fdfb_review.candidate_d_distinct_claim if fdfb_review is not None else None
    )
    if claim is None:
        claim_section = "The concrete three-part Candidate D claim is not registered."
    else:
        claim_section = f"""Status: `{claim.status}`

- SAB operator theorem to falsify: {claim.sab_operator_theorem}
- Complete complexity/resource result to falsify: {claim.complete_complexity_resource_result}
- Complete implementation endpoint: {claim.falsifiable_full_sab_endpoint}"""
    text = f"""# Candidate D D1 Full-Text Novelty Audit

## Decision

`{decision}`

The gate is fail closed. {complete_count} of nine mandatory primary sources are locally
hash-bound and claim-anchored. Missing or invalid mandatory sources: {missing_text}.
{decision_effect}

## Source Evidence

| source | local verification | pages | claim classification |
|---|---|---:|---|
{rows}

The PDF and extracted-text files remain outside git under
`references/candidate_d_fulltext/`. Their expected SHA-256 values, page ranges,
claim classes, and short paraphrased anchors are bound by
`literature/candidate_d_source_registry.json`.
The canonical text extraction profile is WSL/Linux Poppler
`pdftotext 24.02.0 -layout`; a different text byte stream does not silently
replace a reviewed extraction.

## Concrete Distinct Claim

{claim_section}

## Claim-Level Answers

1. {fdfb_answer}
2. FDFB2 covers arbitrary functions at constant additional cost at its stated
   abstraction level. Candidate D may not claim that broad idea as novel.
3. A Candidate D contribution remains testable only as a SAB-specific bounded
   semilinear operator closure with a different complete complexity/resource
   result and a falsifiable complete-SAB endpoint.
4. {sharing_answer}
5. {batchboot_answer}
6. Candidate D and BatchBoot may be complementary. That is an experimental
   hypothesis requiring same-backend B2 reproduction or a composed path.
7. The only admissible distinct endpoint is complete
   `T_bootstrap/(r*N_active)`, with standard-object, noise, resource, and B1/B2
   gates. Kernel-only or ciphertext-format-only gains are insufficient.
8. {fab_answer}

## Routing

{routing_text}

{closing_text}
"""
    return text.encode("utf-8")


def build_candidate_d_d1_artifacts(root: Path) -> tuple[str, dict[Path, bytes]]:
    root = root.resolve()
    records = load_source_registry(root / REGISTRY_PATH)
    reviews = tuple(
        verify_fulltext(record, root / FULLTEXT_PATH) for record in records
    )
    decision, comparisons = evaluate_candidate_d_novelty(reviews)
    artifacts = {
        Path("docs/candidate_d_d1_novelty_audit.md"): render_candidate_d_d1_markdown(
            decision, reviews
        ),
        Path("repro/candidate_d_admission/literature_sources.csv"): _csv_bytes(
            (
                "source_id",
                "title",
                "year",
                "official_url",
                "fulltext_url",
                "registry_status",
                "verification_status",
                "pdf_sha256",
                "text_sha256",
                "page_range",
                "source_binding_sha256",
                "validation_errors",
            ),
            _source_rows(reviews),
        ),
        Path("repro/candidate_d_admission/claim_overlap.csv"): _csv_bytes(
            (
                "source_id",
                "review_status",
                "same_operator",
                "same_complete_complexity",
                "distinct_sab_theorem",
                "distinct_complete_result",
                "falsifiable_full_sab_endpoint",
                "sab_operator_theorem_claim",
                "complete_complexity_resource_claim",
                "full_sab_endpoint_claim",
                "claim_classification",
                "batchboot_composition",
                "conclusion",
                "evidence",
            ),
            _claim_rows(comparisons),
        ),
        Path("repro/candidate_d_admission/novelty_gate.csv"): _csv_bytes(
            ("gate_id", "status", "decision", "evidence", "next_action"),
            _gate_rows(decision, reviews, comparisons),
        ),
    }
    return decision, artifacts


def _safe_destination(root: Path, relative: Path) -> Path:
    root = root.resolve()
    lexical_destination = root / relative
    current = root
    for part in relative.parent.parts:
        current = current / part
        if current.is_symlink():
            raise ValueError(f"output parent may not be a symlink: {relative}")
    if lexical_destination.is_symlink():
        raise ValueError(f"output may not be a symlink: {relative}")
    destination = lexical_destination.resolve()
    try:
        destination.relative_to(root)
    except ValueError as exc:
        raise ValueError(f"output escapes repository root: {relative}") from exc
    return destination


def write_candidate_d_d1_artifacts(root: Path, artifacts: dict[Path, bytes]) -> None:
    destinations: list[tuple[Path, Path, bytes]] = []
    for relative in OUTPUT_PATHS:
        if relative not in artifacts:
            raise ValueError(f"missing generated artifact: {relative}")
        destination = _safe_destination(root, relative)
        destination.parent.mkdir(parents=True, exist_ok=True)
        destination = _safe_destination(root, relative)
        destinations.append((relative, destination, artifacts[relative]))

    pending: list[tuple[Path, Path]] = []
    try:
        for _, destination, content in destinations:
            descriptor, temporary_name = tempfile.mkstemp(
                prefix=f".{destination.name}.",
                suffix=".tmp",
                dir=destination.parent,
            )
            temporary = Path(temporary_name)
            try:
                with os.fdopen(descriptor, "wb") as stream:
                    stream.write(content)
                    stream.flush()
                    os.fsync(stream.fileno())
            except BaseException:
                if temporary.exists() and not temporary.is_symlink():
                    temporary.unlink()
                raise
            pending.append((temporary, destination))
        for (relative, _, _), (temporary, destination) in zip(
            destinations, pending, strict=True
        ):
            if _safe_destination(root, relative) != destination:
                raise ValueError(f"output path changed during publication: {relative}")
            os.replace(temporary, destination)
    finally:
        for temporary, _ in pending:
            if temporary.exists() and not temporary.is_symlink():
                temporary.unlink()


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--check",
        action="store_true",
        help="verify that tracked D1 artifacts equal deterministic output",
    )
    args = parser.parse_args(argv)
    decision, artifacts = build_candidate_d_d1_artifacts(ROOT)
    if args.check:
        drift = [
            str(path)
            for path, expected in artifacts.items()
            if not (ROOT / path).is_file() or (ROOT / path).read_bytes() != expected
        ]
        if drift:
            print("D1 artifact drift: " + ", ".join(drift), file=sys.stderr)
            return 1
    else:
        write_candidate_d_d1_artifacts(ROOT, artifacts)
    print(decision)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
