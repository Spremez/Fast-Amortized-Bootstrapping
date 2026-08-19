"""Fail-closed full-text novelty gate for Candidate D."""

from __future__ import annotations

from dataclasses import dataclass, replace
from hashlib import sha256
import json
from pathlib import Path
import re
from typing import Any, Iterable


PASS_D1 = "PASS_D1_DISTINCT_SAB_OPERATOR_CLAIM_REMAINS_TESTABLE"
REJECT_D1 = "REJECT_D1_CANDIDATE_D_SUBSUMED_BY_PRIOR_WORK"
BLOCK_D1 = "BLOCK_D1_REQUIRED_FULLTEXT_OR_REVIEW_MISSING"

REQUIRED_SOURCE_IDS = (
    "FAB_2025_686",
    "SHARING_MASK_2025_2112",
    "BATCHBOOT_SEC26",
    "FDFB2_2024_1376",
    "MULTIVALUE_2018_622",
    "MOSFHET_2022_515",
    "NTRU_AMORT_2026_068",
    "BATCH_BOOT_I",
    "BATCH_BOOT_II",
)

REQUIRED_FULLTEXT_URLS = {
    "FAB_2025_686": "https://eprint.iacr.org/2025/686.pdf",
    "SHARING_MASK_2025_2112": "https://eprint.iacr.org/2025/2112.pdf",
    "BATCHBOOT_SEC26": (
        "https://www.usenix.org/system/files/conference/usenixsecurity26/"
        "sec26_prepub_li-zhihao.pdf"
    ),
    "FDFB2_2024_1376": "https://eprint.iacr.org/2024/1376.pdf",
    "MULTIVALUE_2018_622": "https://eprint.iacr.org/2018/622.pdf",
    "MOSFHET_2022_515": "https://eprint.iacr.org/2022/515.pdf",
    "NTRU_AMORT_2026_068": "https://eprint.iacr.org/2026/068.pdf",
    "BATCH_BOOT_I": "https://link.springer.com/content/pdf/10.1007/978-3-031-30620-4_11.pdf",
    "BATCH_BOOT_II": "https://link.springer.com/content/pdf/10.1007/978-3-031-30620-4_12.pdf",
}

# Review contracts are pinned independently from the mutable JSON registry.
# Updating a source or claim review requires an explicit code-reviewed pin change.
REQUIRED_SOURCE_BINDINGS = {
    "FAB_2025_686": "991019a69d620351b61232fa467e20c4c931610d5672ef4a4e3dbf36f151d4e9",
    "SHARING_MASK_2025_2112": "736fc3811971fcac1ae01359ee1453832d8dda0298498cddc2274a40f4590865",
    "BATCHBOOT_SEC26": "ae49ecd4a7554f510750622a94a7333c9f838b932280194c02db31abd197652c",
    "FDFB2_2024_1376": "5cd2ec371cd3c0c259ac3c8a3ebc2fed094545e5f1aedfd11a6060d5aebd6b4f",
    "MULTIVALUE_2018_622": "fb0fc67387d559ec32e773fde6e419caf63128e1ac122dc6e3e2b90dea925d02",
    "MOSFHET_2022_515": "22f944637c3225cca712fbaf873144cff38d6418d8e575cff86a32629019530f",
    "NTRU_AMORT_2026_068": "1c8a79628c6a991b6be2c661174aa0e2d33521b552b50740949eaa0fdcd1f26c",
    "BATCH_BOOT_I": "f74477d28b0cca384135d38fb35d6a3000d5a659facfbab6c725e3fa0f2424ef",
    "BATCH_BOOT_II": "ae2b2af6bab115ac3a6d5191798db928dc4fa75ccb91b3d6e3a5b809a9579677",
}

_SHA256_RE = re.compile(r"[0-9a-f]{64}")


class SourceRegistryError(ValueError):
    """Raised when the authoritative source registry is malformed."""


@dataclass(frozen=True)
class ClaimAnchor:
    page: int
    section: str
    paraphrase: str
    required_terms: tuple[str, ...]

    def canonical_payload(self) -> dict[str, Any]:
        return {
            "page": self.page,
            "section": self.section,
            "paraphrase": self.paraphrase,
            "required_terms": list(self.required_terms),
        }


@dataclass(frozen=True)
class DistinctCandidateClaim:
    status: str
    sab_operator_theorem: str
    complete_complexity_resource_result: str
    falsifiable_full_sab_endpoint: str

    def canonical_payload(self) -> dict[str, str]:
        return {
            "status": self.status,
            "sab_operator_theorem": self.sab_operator_theorem,
            "complete_complexity_resource_result": (
                self.complete_complexity_resource_result
            ),
            "falsifiable_full_sab_endpoint": self.falsifiable_full_sab_endpoint,
        }

    def is_concrete_testable_claim(self) -> bool:
        if self.status != "TESTABLE_NOT_PROVEN":
            return False
        required_terms = (
            (
                self.sab_operator_theorem,
                ("binary", "|Gamma| <= 4", "standard RLWE/GGSW"),
            ),
            (
                self.complete_complexity_resource_result,
                ("B1", "subquadratic in r", "extraction"),
            ),
            (
                self.falsifiable_full_sab_endpoint,
                (
                    "BINARY SET_2_3_2048",
                    "r=4",
                    "T_bootstrap/(r*N_active)",
                    "B1",
                    "B2 BatchBoot",
                ),
            ),
        )
        return all(all(term in text for term in terms) for text, terms in required_terms)


@dataclass(frozen=True)
class SourceRecord:
    id: str
    title: str
    authors: tuple[str, ...]
    year: int
    official_url: str
    fulltext_url: str
    fallback_urls: tuple[str, ...]
    critical_claims: tuple[str, ...]
    review_status: str
    pdf_sha256: str | None
    text_sha256: str | None
    page_range: str | None
    anchors: tuple[ClaimAnchor, ...]
    claim_classification: str
    candidate_d_distinct_claim: DistinctCandidateClaim | None
    same_operator: bool | None
    same_complexity: bool | None
    distinct_sab_theorem: bool
    distinct_complete_result: bool
    falsifiable_full_sab_endpoint: bool
    composition_with_batchboot: str

    def canonical_payload(self) -> dict[str, Any]:
        return {
            "id": self.id,
            "title": self.title,
            "authors": list(self.authors),
            "year": self.year,
            "official_url": self.official_url,
            "fulltext_url": self.fulltext_url,
            "fallback_urls": list(self.fallback_urls),
            "critical_claims": list(self.critical_claims),
            "review_status": self.review_status,
            "pdf_sha256": self.pdf_sha256,
            "text_sha256": self.text_sha256,
            "page_range": self.page_range,
            "anchors": [anchor.canonical_payload() for anchor in self.anchors],
            "claim_classification": self.claim_classification,
            "candidate_d_distinct_claim": (
                self.candidate_d_distinct_claim.canonical_payload()
                if self.candidate_d_distinct_claim is not None
                else None
            ),
            "same_operator": self.same_operator,
            "same_complexity": self.same_complexity,
            "distinct_sab_theorem": self.distinct_sab_theorem,
            "distinct_complete_result": self.distinct_complete_result,
            "falsifiable_full_sab_endpoint": self.falsifiable_full_sab_endpoint,
            "composition_with_batchboot": self.composition_with_batchboot,
        }

    @property
    def binding_sha256(self) -> str:
        encoded = json.dumps(
            self.canonical_payload(),
            ensure_ascii=True,
            sort_keys=True,
            separators=(",", ":"),
        ).encode("ascii")
        return sha256(encoded).hexdigest()


@dataclass(frozen=True)
class FullTextReview:
    source: SourceRecord
    pdf_sha256: str | None
    text_sha256: str | None
    page_range: str | None
    anchors: tuple[ClaimAnchor, ...]
    review_status: str
    same_operator: bool | None
    same_complexity: bool | None
    distinct_sab_theorem: bool
    distinct_complete_result: bool = False
    falsifiable_full_sab_endpoint: bool = False
    candidate_d_distinct_claim: DistinctCandidateClaim | None = None
    source_binding_sha256: str = ""
    validation_errors: tuple[str, ...] = ()

    @classmethod
    def from_record(
        cls,
        record: SourceRecord,
        *,
        review_status: str = "FULLTEXT_REVIEWED",
    ) -> "FullTextReview":
        return cls(
            source=record,
            pdf_sha256=record.pdf_sha256,
            text_sha256=record.text_sha256,
            page_range=record.page_range,
            anchors=record.anchors,
            review_status=review_status,
            same_operator=record.same_operator,
            same_complexity=record.same_complexity,
            distinct_sab_theorem=record.distinct_sab_theorem,
            distinct_complete_result=record.distinct_complete_result,
            falsifiable_full_sab_endpoint=record.falsifiable_full_sab_endpoint,
            candidate_d_distinct_claim=record.candidate_d_distinct_claim,
            source_binding_sha256=record.binding_sha256,
        )

    def missing(self, reason: str = "required full text is missing") -> "FullTextReview":
        return replace(
            self,
            pdf_sha256=None,
            text_sha256=None,
            page_range=None,
            review_status="FULLTEXT_MISSING",
            validation_errors=(reason,),
        )

    def with_overlap(
        self,
        *,
        same_operator: bool,
        same_complexity: bool,
        distinct_sab_theorem: bool,
        distinct_complete_result: bool | None = None,
        falsifiable_full_sab_endpoint: bool | None = None,
    ) -> "FullTextReview":
        resolved_complete_result = (
            distinct_sab_theorem
            if distinct_complete_result is None
            else distinct_complete_result
        )
        resolved_endpoint = (
            distinct_sab_theorem
            if falsifiable_full_sab_endpoint is None
            else falsifiable_full_sab_endpoint
        )
        source = replace(
            self.source,
            same_operator=same_operator,
            same_complexity=same_complexity,
            distinct_sab_theorem=distinct_sab_theorem,
            distinct_complete_result=resolved_complete_result,
            falsifiable_full_sab_endpoint=resolved_endpoint,
            candidate_d_distinct_claim=(
                self.source.candidate_d_distinct_claim
                if distinct_sab_theorem
                else None
            ),
        )
        return replace(
            self,
            source=source,
            source_binding_sha256=source.binding_sha256,
            same_operator=same_operator,
            same_complexity=same_complexity,
            distinct_sab_theorem=distinct_sab_theorem,
            distinct_complete_result=resolved_complete_result,
            falsifiable_full_sab_endpoint=resolved_endpoint,
            candidate_d_distinct_claim=source.candidate_d_distinct_claim,
        )

    def is_bound_to(self, record: SourceRecord | None = None) -> bool:
        expected = self.source if record is None else record
        return (
            self.source.id == expected.id
            and REQUIRED_SOURCE_BINDINGS.get(expected.id)
            == expected.binding_sha256
            and self.source_binding_sha256 == expected.binding_sha256
            and self.source.binding_sha256 == expected.binding_sha256
            and self.anchors == expected.anchors
            and self.same_operator == expected.same_operator
            and self.same_complexity == expected.same_complexity
            and self.distinct_sab_theorem == expected.distinct_sab_theorem
            and self.distinct_complete_result == expected.distinct_complete_result
            and self.falsifiable_full_sab_endpoint
            == expected.falsifiable_full_sab_endpoint
            and self.candidate_d_distinct_claim
            == expected.candidate_d_distinct_claim
        )

    def is_complete_and_bound(self) -> bool:
        return (
            self.review_status == "FULLTEXT_REVIEWED"
            and self.source.review_status == "FULLTEXT_REVIEWED"
            and not self.validation_errors
            and self.is_bound_to()
            and self.pdf_sha256 == self.source.pdf_sha256
            and self.text_sha256 == self.source.text_sha256
            and self.page_range == self.source.page_range
            and bool(self.anchors)
        )


@dataclass(frozen=True)
class ClaimComparison:
    source_id: str
    review_status: str
    same_operator: bool | None
    same_complexity: bool | None
    distinct_sab_theorem: bool
    distinct_complete_result: bool
    falsifiable_full_sab_endpoint: bool
    sab_operator_theorem_claim: str
    complete_complexity_resource_claim: str
    full_sab_endpoint_claim: str
    claim_classification: str
    composition_with_batchboot: str
    conclusion: str
    evidence: str


def _require_string(value: Any, field: str) -> str:
    if not isinstance(value, str) or not value.strip():
        raise SourceRegistryError(f"{field} must be a non-empty string")
    return value


def _require_string_tuple(value: Any, field: str) -> tuple[str, ...]:
    if not isinstance(value, list) or not value:
        raise SourceRegistryError(f"{field} must be a non-empty list")
    return tuple(_require_string(item, field) for item in value)


def _parse_anchor(value: Any, source_id: str) -> ClaimAnchor:
    if not isinstance(value, dict):
        raise SourceRegistryError(f"{source_id}.anchors must contain objects")
    page = value.get("page")
    if not isinstance(page, int) or page < 1:
        raise SourceRegistryError(f"{source_id}.anchor.page must be positive")
    return ClaimAnchor(
        page=page,
        section=_require_string(value.get("section"), f"{source_id}.section"),
        paraphrase=_require_string(
            value.get("paraphrase"), f"{source_id}.paraphrase"
        ),
        required_terms=_require_string_tuple(
            value.get("required_terms"), f"{source_id}.required_terms"
        ),
    )


def _parse_distinct_claim(value: Any, source_id: str) -> DistinctCandidateClaim | None:
    if value is None:
        return None
    if not isinstance(value, dict):
        raise SourceRegistryError(
            f"{source_id}.candidate_d_distinct_claim must be an object or null"
        )
    return DistinctCandidateClaim(
        status=_require_string(value.get("status"), f"{source_id}.claim.status"),
        sab_operator_theorem=_require_string(
            value.get("sab_operator_theorem"),
            f"{source_id}.claim.sab_operator_theorem",
        ),
        complete_complexity_resource_result=_require_string(
            value.get("complete_complexity_resource_result"),
            f"{source_id}.claim.complete_complexity_resource_result",
        ),
        falsifiable_full_sab_endpoint=_require_string(
            value.get("falsifiable_full_sab_endpoint"),
            f"{source_id}.claim.falsifiable_full_sab_endpoint",
        ),
    )


def _parse_source(value: Any) -> SourceRecord:
    if not isinstance(value, dict):
        raise SourceRegistryError("sources must contain objects")
    source_id = _require_string(value.get("id"), "source.id")
    authors = _require_string_tuple(value.get("authors"), f"{source_id}.authors")
    critical_claims = _require_string_tuple(
        value.get("critical_claims"), f"{source_id}.critical_claims"
    )
    fallback_value = value.get("fallback_urls", [])
    if not isinstance(fallback_value, list):
        raise SourceRegistryError(f"{source_id}.fallback_urls must be a list")
    fallback_urls = tuple(
        _require_string(url, f"{source_id}.fallback_urls") for url in fallback_value
    )
    anchor_values = value.get("anchors")
    if not isinstance(anchor_values, list):
        raise SourceRegistryError(f"{source_id}.anchors must be a list")
    anchors = tuple(_parse_anchor(anchor, source_id) for anchor in anchor_values)
    year = value.get("year")
    if not isinstance(year, int) or not 2000 <= year <= 2100:
        raise SourceRegistryError(f"{source_id}.year is invalid")

    record = SourceRecord(
        id=source_id,
        title=_require_string(value.get("title"), f"{source_id}.title"),
        authors=authors,
        year=year,
        official_url=_require_string(
            value.get("official_url"), f"{source_id}.official_url"
        ),
        fulltext_url=_require_string(
            value.get("fulltext_url"), f"{source_id}.fulltext_url"
        ),
        fallback_urls=fallback_urls,
        critical_claims=critical_claims,
        review_status=_require_string(
            value.get("review_status"), f"{source_id}.review_status"
        ),
        pdf_sha256=value.get("pdf_sha256"),
        text_sha256=value.get("text_sha256"),
        page_range=value.get("page_range"),
        anchors=anchors,
        claim_classification=_require_string(
            value.get("claim_classification"),
            f"{source_id}.claim_classification",
        ),
        candidate_d_distinct_claim=_parse_distinct_claim(
            value.get("candidate_d_distinct_claim"), source_id
        ),
        same_operator=value.get("same_operator"),
        same_complexity=value.get("same_complexity"),
        distinct_sab_theorem=value.get("distinct_sab_theorem"),
        distinct_complete_result=value.get("distinct_complete_result"),
        falsifiable_full_sab_endpoint=value.get("falsifiable_full_sab_endpoint"),
        composition_with_batchboot=_require_string(
            value.get("composition_with_batchboot"),
            f"{source_id}.composition_with_batchboot",
        ),
    )
    for field in (
        "distinct_sab_theorem",
        "distinct_complete_result",
        "falsifiable_full_sab_endpoint",
    ):
        if not isinstance(getattr(record, field), bool):
            raise SourceRegistryError(f"{source_id}.{field} must be boolean")
    if record.candidate_d_distinct_claim is not None:
        if source_id != "FDFB2_2024_1376":
            raise SourceRegistryError(
                "only the FDFB2 comparison may carry the Candidate D distinct claim"
            )
        if not record.candidate_d_distinct_claim.is_concrete_testable_claim():
            raise SourceRegistryError(
                "FDFB2 comparison lacks the concrete three-part Candidate D claim"
            )
    for url in (record.official_url, record.fulltext_url, *fallback_urls):
        if not url.startswith("https://"):
            raise SourceRegistryError(f"{source_id} contains a non-HTTPS source URL")
    if record.review_status == "FULLTEXT_REVIEWED":
        for field in ("same_operator", "same_complexity"):
            if not isinstance(getattr(record, field), bool):
                raise SourceRegistryError(f"{source_id}.{field} must be boolean")
        for field_name, digest in (
            ("pdf_sha256", record.pdf_sha256),
            ("text_sha256", record.text_sha256),
        ):
            if not isinstance(digest, str) or not _SHA256_RE.fullmatch(digest):
                raise SourceRegistryError(f"{source_id}.{field_name} is invalid")
        if not isinstance(record.page_range, str) or not re.fullmatch(
            r"1-[1-9][0-9]*", record.page_range
        ):
            raise SourceRegistryError(f"{source_id}.page_range is invalid")
        if not record.anchors:
            raise SourceRegistryError(f"{source_id} has no reviewed anchors")
    elif record.review_status == "FULLTEXT_MISSING":
        if record.same_operator is not None or record.same_complexity is not None:
            raise SourceRegistryError(
                f"{source_id} missing review must not assert overlap comparisons"
            )
        if any(
            value is not None
            for value in (record.pdf_sha256, record.text_sha256, record.page_range)
        ) or record.anchors:
            raise SourceRegistryError(
                f"{source_id} missing review must not claim hashes or anchors"
            )
    else:
        raise SourceRegistryError(f"{source_id}.review_status is unsupported")
    return record


def load_source_registry(path: Path) -> tuple[SourceRecord, ...]:
    raw = path.read_text(encoding="utf-8")
    if "2024/498" in raw:
        raise SourceRegistryError("unrelated ePrint 2024/498 is forbidden")
    try:
        payload = json.loads(raw)
    except json.JSONDecodeError as exc:
        raise SourceRegistryError(f"invalid JSON: {exc}") from exc
    if not isinstance(payload, dict) or payload.get("schema_version") != 1:
        raise SourceRegistryError("registry schema_version must equal 1")
    if payload.get("text_extraction_profile") != {
        "tool": "pdftotext",
        "arguments": ["-layout"],
        "reference_version": "24.02.0",
        "platform": "WSL/Linux",
    }:
        raise SourceRegistryError("text_extraction_profile must match the D1 contract")
    declared_ids = payload.get("required_source_ids")
    if declared_ids != list(REQUIRED_SOURCE_IDS):
        raise SourceRegistryError("required_source_ids must match the D1 contract")
    sources = payload.get("sources")
    if not isinstance(sources, list):
        raise SourceRegistryError("sources must be a list")
    records = tuple(_parse_source(value) for value in sources)
    ids = tuple(record.id for record in records)
    if ids != REQUIRED_SOURCE_IDS:
        raise SourceRegistryError(
            "sources must contain each required ID exactly once in contract order"
        )
    for record in records:
        if record.fulltext_url != REQUIRED_FULLTEXT_URLS[record.id]:
            raise SourceRegistryError(
                f"{record.id}.fulltext_url does not match the D1 contract"
            )
        if record.binding_sha256 != REQUIRED_SOURCE_BINDINGS[record.id]:
            raise SourceRegistryError(
                f"{record.id} does not match the pinned source/review binding"
            )
    return records


def _inside(path: Path, root: Path) -> bool:
    try:
        path.relative_to(root)
    except ValueError:
        return False
    return True


def _normal_text(value: str) -> str:
    return " ".join(value.casefold().split())


def _page_texts(text: str) -> tuple[str, ...]:
    pages = text.split("\f")
    if pages and not pages[-1].strip():
        pages.pop()
    return tuple(pages)


def verify_fulltext(record: SourceRecord, root: Path) -> FullTextReview:
    root = root.resolve()
    pdf_path = (root / f"{record.id}.pdf").resolve()
    text_path = (root / f"{record.id}.txt").resolve()
    review = FullTextReview.from_record(record)
    if record.review_status == "FULLTEXT_MISSING":
        return review.missing(
            "latest second revision full text and claim review are missing"
        )
    if not _inside(pdf_path, root) or not _inside(text_path, root):
        return replace(
            review,
            review_status="FULLTEXT_INVALID",
            validation_errors=("full-text path escapes the configured root",),
        )
    if not pdf_path.is_file() or not text_path.is_file():
        return review.missing()

    pdf_bytes = pdf_path.read_bytes()
    text_bytes = text_path.read_bytes()
    actual_pdf_sha = sha256(pdf_bytes).hexdigest()
    actual_text_sha = sha256(text_bytes).hexdigest()
    text = text_bytes.decode("utf-8", errors="replace")
    pages = _page_texts(text)
    actual_page_range = f"1-{len(pages)}" if pages else None
    errors: list[str] = []
    if not pdf_bytes.startswith(b"%PDF"):
        errors.append("PDF header is not %PDF")
    if not text.strip():
        errors.append("pdftotext output is empty")
    if record.review_status != "FULLTEXT_REVIEWED":
        errors.append("registry has no completed claim-level review")
    if actual_pdf_sha != record.pdf_sha256:
        errors.append("PDF SHA-256 does not match the registry")
    if actual_text_sha != record.text_sha256:
        errors.append("text SHA-256 does not match the registry")
    if actual_page_range != record.page_range:
        errors.append("page range does not match the registry")
    for anchor in record.anchors:
        if anchor.page > len(pages):
            errors.append(f"anchor page {anchor.page} is outside the full text")
            continue
        page_text = _normal_text(pages[anchor.page - 1])
        for term in anchor.required_terms:
            if _normal_text(term) not in page_text:
                errors.append(
                    f"anchor page {anchor.page} is missing required term {term!r}"
                )

    return replace(
        review,
        pdf_sha256=actual_pdf_sha,
        text_sha256=actual_text_sha,
        page_range=actual_page_range,
        review_status=("FULLTEXT_REVIEWED" if not errors else "FULLTEXT_INVALID"),
        validation_errors=tuple(errors),
    )


def _comparison(review: FullTextReview) -> ClaimComparison:
    claim = review.candidate_d_distinct_claim
    triad = (
        review.distinct_sab_theorem
        and review.distinct_complete_result
        and review.falsifiable_full_sab_endpoint
        and claim is not None
        and claim.is_concrete_testable_claim()
    )
    if not review.is_complete_and_bound():
        conclusion = "REQUIRED_FULLTEXT_OR_REVIEW_MISSING"
    elif review.same_operator and review.same_complexity and not triad:
        conclusion = "SUBSUMES_CANDIDATE_D"
    elif review.same_operator:
        conclusion = "OVERLAP_REQUIRES_NARROW_SAB_CLAIM"
    else:
        conclusion = "ADJACENT_OR_BASELINE_SOURCE"
    evidence = "; ".join(
        f"p.{anchor.page} {anchor.section}: {anchor.paraphrase}"
        for anchor in review.anchors
    )
    if review.validation_errors:
        evidence = "; ".join(review.validation_errors)
    comparison_is_known = review.is_complete_and_bound()
    return ClaimComparison(
        source_id=review.source.id,
        review_status=review.review_status,
        same_operator=(review.same_operator if comparison_is_known else None),
        same_complexity=(review.same_complexity if comparison_is_known else None),
        distinct_sab_theorem=review.distinct_sab_theorem,
        distinct_complete_result=review.distinct_complete_result,
        falsifiable_full_sab_endpoint=review.falsifiable_full_sab_endpoint,
        sab_operator_theorem_claim=(claim.sab_operator_theorem if claim else ""),
        complete_complexity_resource_claim=(
            claim.complete_complexity_resource_result if claim else ""
        ),
        full_sab_endpoint_claim=(
            claim.falsifiable_full_sab_endpoint if claim else ""
        ),
        claim_classification=review.source.claim_classification,
        composition_with_batchboot=review.source.composition_with_batchboot,
        conclusion=conclusion,
        evidence=evidence,
    )


def evaluate_candidate_d_novelty(
    reviews: tuple[FullTextReview, ...],
) -> tuple[str, tuple[ClaimComparison, ...]]:
    counts = {source_id: 0 for source_id in REQUIRED_SOURCE_IDS}
    unknown = False
    for review in reviews:
        if review.source.id not in counts:
            unknown = True
        else:
            counts[review.source.id] += 1
    indexed = {review.source.id: review for review in reviews}
    ordered_reviews = tuple(
        indexed[source_id]
        for source_id in REQUIRED_SOURCE_IDS
        if source_id in indexed
    )
    comparisons = tuple(_comparison(review) for review in ordered_reviews)
    exact_source_set = not unknown and all(count == 1 for count in counts.values())
    if not exact_source_set or not all(
        review.is_complete_and_bound() for review in ordered_reviews
    ):
        return BLOCK_D1, comparisons

    for review in ordered_reviews:
        claim = review.candidate_d_distinct_claim
        triad = (
            review.distinct_sab_theorem
            and review.distinct_complete_result
            and review.falsifiable_full_sab_endpoint
            and claim is not None
            and claim.is_concrete_testable_claim()
        )
        if review.same_operator and review.same_complexity and not triad:
            return REJECT_D1, comparisons

    fdfb = indexed["FDFB2_2024_1376"]
    claim = fdfb.candidate_d_distinct_claim
    distinct_claim_is_testable = (
        fdfb.same_operator
        and not fdfb.same_complexity
        and fdfb.distinct_sab_theorem
        and fdfb.distinct_complete_result
        and fdfb.falsifiable_full_sab_endpoint
        and claim is not None
        and claim.is_concrete_testable_claim()
    )
    if not distinct_claim_is_testable:
        return REJECT_D1, comparisons
    return PASS_D1, comparisons


def fetch_manifest_lines(records: Iterable[SourceRecord]) -> tuple[str, ...]:
    lines = []
    for record in records:
        values = (
            record.id,
            record.fulltext_url,
            ";".join(record.fallback_urls) or "-",
            record.pdf_sha256 or "-",
            record.text_sha256 or "-",
            (record.page_range.split("-", 1)[1] if record.page_range else "-"),
        )
        if any("\t" in value or "\n" in value for value in values):
            raise SourceRegistryError("fetch manifest fields may not contain tabs")
        lines.append("\t".join(values))
    return tuple(lines)


def validate_fulltext_output_root(repository_root: Path, output_root: Path) -> None:
    repository_root = repository_root.absolute()
    output_root = output_root.absolute()
    expected_root = (repository_root / "references/candidate_d_fulltext").absolute()
    if output_root != expected_root:
        raise SourceRegistryError("full-text output root is not the contract path")
    if (repository_root / "references").is_symlink() or output_root.is_symlink():
        raise SourceRegistryError("full-text output directory may not be a symlink")
    if not repository_root.is_dir() or not output_root.is_dir():
        raise SourceRegistryError("repository and full-text output roots must exist")
    resolved_repository = repository_root.resolve(strict=True)
    resolved_output = output_root.resolve(strict=True)
    if not _inside(resolved_output, resolved_repository):
        raise SourceRegistryError("full-text output root escapes the repository")
    names = ["source_hashes.csv", "source_hashes.csv.part"]
    for source_id in REQUIRED_SOURCE_IDS:
        names.extend(
            (
                f"{source_id}.pdf",
                f"{source_id}.pdf.part",
                f"{source_id}.txt",
                f"{source_id}.txt.part",
            )
        )
    for name in names:
        if (output_root / name).is_symlink():
            raise SourceRegistryError(f"full-text output entry may not be a symlink: {name}")


def _main() -> int:
    import argparse

    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("command", choices=("fetch-manifest", "validate-output-root"))
    parser.add_argument("path", type=Path)
    parser.add_argument("output_root", type=Path, nargs="?")
    args = parser.parse_args()
    if args.command == "fetch-manifest":
        if args.output_root is not None:
            parser.error("fetch-manifest accepts only the registry path")
        records = load_source_registry(args.path)
        for line in fetch_manifest_lines(records):
            print(line)
    else:
        if args.output_root is None:
            parser.error("validate-output-root requires repository and output roots")
        validate_fulltext_output_root(args.path, args.output_root)
        print("PASS_CANDIDATE_D_FULLTEXT_OUTPUT_ROOT_SAFE")
    return 0


if __name__ == "__main__":
    raise SystemExit(_main())
