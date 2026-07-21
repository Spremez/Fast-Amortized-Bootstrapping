import csv
from io import StringIO
import json
import os
from contextlib import contextmanager
from dataclasses import replace
from hashlib import sha256
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

from research.mat_sab.candidate_d_literature import (
    BLOCK_D1,
    PASS_D1,
    REJECT_D1,
    ClaimAnchor,
    FullTextReview,
    REQUIRED_FULLTEXT_URLS,
    REQUIRED_SOURCE_BINDINGS,
    REQUIRED_SOURCE_IDS,
    SourceRegistryError,
    evaluate_candidate_d_novelty,
    load_source_registry,
    verify_fulltext,
    validate_fulltext_output_root,
)
from scripts.run_candidate_d_d1_literature import (
    build_candidate_d_d1_artifacts,
    render_candidate_d_d1_markdown,
    write_candidate_d_d1_artifacts,
)


ROOT = Path(__file__).resolve().parents[2]
REGISTRY = ROOT / "literature/candidate_d_source_registry.json"


def complete_fixture_reviews() -> dict[str, FullTextReview]:
    reviews = {}
    for record in load_source_registry(REGISTRY):
        if record.review_status != "FULLTEXT_REVIEWED":
            anchor = ClaimAnchor(
                page=1,
                section="fixture",
                paraphrase="Synthetic completed review for decision tests.",
                required_terms=("fixture",),
            )
            record = replace(
                record,
                review_status="FULLTEXT_REVIEWED",
                pdf_sha256="1" * 64,
                text_sha256="2" * 64,
                page_range="1-1",
                anchors=(anchor,),
                same_operator=False,
                same_complexity=False,
                distinct_sab_theorem=True,
                distinct_complete_result=True,
                falsifiable_full_sab_endpoint=True,
            )
        reviews[record.id] = FullTextReview.from_record(record)
    return reviews


@contextmanager
def pinned_fixture_contract(
    reviews: dict[str, FullTextReview] | list[FullTextReview],
):
    rows = list(reviews.values()) if isinstance(reviews, dict) else reviews
    bindings = {review.source.id: review.source.binding_sha256 for review in rows}
    with patch.dict(REQUIRED_SOURCE_BINDINGS, bindings, clear=True):
        yield rows


def evaluate_fixture_reviews(
    reviews: dict[str, FullTextReview] | list[FullTextReview],
):
    with pinned_fixture_contract(reviews) as rows:
        return evaluate_candidate_d_novelty(tuple(rows))


class CandidateDLiteratureTests(unittest.TestCase):
    def test_registry_is_the_exact_primary_source_contract(self):
        records = load_source_registry(REGISTRY)
        self.assertEqual(tuple(row.id for row in records), REQUIRED_SOURCE_IDS)
        self.assertEqual(
            {row.id: row.fulltext_url for row in records},
            REQUIRED_FULLTEXT_URLS,
        )
        self.assertNotIn("2024/498", REGISTRY.read_text(encoding="utf-8"))

    def test_registry_binds_the_canonical_text_extraction_profile(self):
        payload = json.loads(REGISTRY.read_text(encoding="utf-8"))
        payload["text_extraction_profile"]["reference_version"] = "changed"
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "registry.json"
            path.write_text(json.dumps(payload), encoding="utf-8")
            with self.assertRaises(SourceRegistryError):
                load_source_registry(path)

    def test_missing_ntru_source_uses_official_title_and_unknown_comparisons(self):
        records = load_source_registry(REGISTRY)
        ntru = next(row for row in records if row.id == "NTRU_AMORT_2026_068")
        self.assertEqual(
            ntru.title,
            "Practical Amortized Bootstrapping for NTRU-Based FHE",
        )
        self.assertEqual(ntru.review_status, "FULLTEXT_MISSING")
        self.assertIsNone(ntru.same_operator)
        self.assertIsNone(ntru.same_complexity)

        _, artifacts = build_candidate_d_d1_artifacts(ROOT)
        rows = csv.DictReader(
            StringIO(
                artifacts[
                    Path("repro/candidate_d_admission/claim_overlap.csv")
                ].decode("utf-8")
            )
        )
        rendered = next(
            row for row in rows if row["source_id"] == "NTRU_AMORT_2026_068"
        )
        self.assertEqual(rendered["same_operator"], "")
        self.assertEqual(rendered["same_complete_complexity"], "")

    def test_fetch_script_uses_registry_and_preserves_verified_cache(self):
        script = (ROOT / "scripts/fetch_candidate_d_primary_sources.sh").read_text(
            encoding="utf-8"
        )
        self.assertIn("fetch-manifest", script)
        self.assertIn("validate-output-root", script)
        self.assertIn("CACHE_VERIFIED", script)
        self.assertNotIn('rm -f "${pdf}"', script)
        for url in REQUIRED_FULLTEXT_URLS.values():
            self.assertNotIn(url, script)

    def test_fdfb2_is_a_mandatory_novelty_kill_gate(self):
        records = load_source_registry(REGISTRY)
        fdfb = next(row for row in records if row.id == "FDFB2_2024_1376")
        self.assertIn("arbitrary number of functions", fdfb.critical_claims)
        self.assertTrue(fdfb.same_operator)
        self.assertFalse(fdfb.same_complexity)

    def test_complete_distinct_fixture_passes_d1(self):
        decision, comparisons = evaluate_fixture_reviews(complete_fixture_reviews())
        self.assertEqual(decision, PASS_D1)
        self.assertEqual(len(comparisons), len(REQUIRED_SOURCE_IDS))

    def test_missing_batchboot_fulltext_blocks_d1(self):
        reviews = complete_fixture_reviews()
        reviews["BATCHBOOT_SEC26"] = reviews["BATCHBOOT_SEC26"].missing()
        decision, _ = evaluate_fixture_reviews(reviews)
        self.assertEqual(decision, BLOCK_D1)

    def test_subsumed_operator_claim_rejects_d(self):
        reviews = complete_fixture_reviews()
        reviews["FDFB2_2024_1376"] = reviews[
            "FDFB2_2024_1376"
        ].with_overlap(
            same_operator=True,
            same_complexity=True,
            distinct_sab_theorem=False,
        )
        decision, _ = evaluate_fixture_reviews(reviews)
        self.assertEqual(decision, REJECT_D1)

    def test_missing_duplicate_or_unknown_source_blocks_before_overlap(self):
        reviews = complete_fixture_reviews()
        ordered = list(reviews.values())
        cases = {
            "missing": ordered[:-1],
            "duplicate": ordered + [ordered[0]],
            "unknown": ordered
            + [replace(ordered[0], source=replace(ordered[0].source, id="OTHER"))],
        }
        for name, rows in cases.items():
            with self.subTest(name=name):
                decision, _ = evaluate_fixture_reviews(rows)
                self.assertEqual(decision, BLOCK_D1)

    def test_missing_source_precedes_otherwise_rejecting_overlap(self):
        reviews = complete_fixture_reviews()
        reviews["FDFB2_2024_1376"] = reviews[
            "FDFB2_2024_1376"
        ].with_overlap(
            same_operator=True,
            same_complexity=True,
            distinct_sab_theorem=False,
        )
        reviews["BATCHBOOT_SEC26"] = reviews["BATCHBOOT_SEC26"].missing()
        decision, _ = evaluate_fixture_reviews(reviews)
        self.assertEqual(decision, BLOCK_D1)

    def test_every_review_binding_component_is_mutation_sensitive(self):
        reviews = complete_fixture_reviews()
        original = reviews["FDFB2_2024_1376"]
        anchor = original.source.anchors[0]
        mutations = {
            "title": replace(original.source, title=original.source.title + " changed"),
            "official_url": replace(
                original.source, official_url="https://example.invalid/changed"
            ),
            "fulltext_url": replace(
                original.source, fulltext_url="https://example.invalid/changed.pdf"
            ),
            "pdf_sha256": replace(original.source, pdf_sha256="a" * 64),
            "text_sha256": replace(original.source, text_sha256="b" * 64),
            "page_range": replace(original.source, page_range="1-999"),
            "anchor": replace(
                original.source,
                anchors=(
                    replace(anchor, paraphrase=anchor.paraphrase + " changed"),
                    *original.source.anchors[1:],
                ),
            ),
            "claim_classification": replace(
                original.source,
                claim_classification="MUTATED_CLASSIFICATION",
            ),
        }
        for name, source in mutations.items():
            with self.subTest(name=name):
                changed = dict(reviews)
                changed[original.source.id] = replace(original, source=source)
                decision, _ = evaluate_fixture_reviews(changed)
                self.assertEqual(decision, BLOCK_D1)

    def test_review_hash_and_page_mutations_block(self):
        reviews = complete_fixture_reviews()
        original = reviews["FDFB2_2024_1376"]
        for field, value in (
            ("pdf_sha256", "c" * 64),
            ("text_sha256", "d" * 64),
            ("page_range", "1-999"),
            ("anchors", original.anchors[:-1]),
        ):
            with self.subTest(field=field):
                changed = dict(reviews)
                changed[original.source.id] = replace(
                    original, **{field: value}
                )
                decision, _ = evaluate_fixture_reviews(changed)
                self.assertEqual(decision, BLOCK_D1)

    def test_regenerated_mutation_cannot_self_authenticate(self):
        original = complete_fixture_reviews()["FDFB2_2024_1376"]
        for name, source in (
            ("title", replace(original.source, title="Changed title")),
            (
                "official_url",
                replace(original.source, official_url="https://example.invalid/paper"),
            ),
            (
                "classification",
                replace(original.source, claim_classification="CHANGED"),
            ),
            ("overlap", replace(original.source, same_complexity=True)),
        ):
            with self.subTest(name=name):
                regenerated = FullTextReview.from_record(source)
                self.assertFalse(regenerated.is_complete_and_bound())

    def test_bare_distinctness_booleans_cannot_pass_without_concrete_claim(self):
        reviews = complete_fixture_reviews()
        original = reviews["FDFB2_2024_1376"]
        source = replace(original.source, candidate_d_distinct_claim=None)
        reviews["FDFB2_2024_1376"] = replace(
            original,
            source=source,
            source_binding_sha256=source.binding_sha256,
            candidate_d_distinct_claim=None,
        )
        decision, _ = evaluate_fixture_reviews(reviews)
        self.assertEqual(decision, REJECT_D1)

    def test_registry_rejects_url_drift_and_duplicate_source(self):
        payload = json.loads(REGISTRY.read_text(encoding="utf-8"))
        cases = []
        url_drift = json.loads(json.dumps(payload))
        url_drift["sources"][0]["fulltext_url"] = (
            "https://example.invalid/not-primary.pdf"
        )
        cases.append(url_drift)
        duplicate = json.loads(json.dumps(payload))
        duplicate["sources"][-1] = duplicate["sources"][0]
        cases.append(duplicate)
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "registry.json"
            for index, case in enumerate(cases):
                with self.subTest(index=index):
                    path.write_text(json.dumps(case), encoding="utf-8")
                    with self.assertRaises(SourceRegistryError):
                        load_source_registry(path)

    def test_registry_rejects_regenerated_metadata_and_review_mutations(self):
        payload = json.loads(REGISTRY.read_text(encoding="utf-8"))
        fdfb_index = REQUIRED_SOURCE_IDS.index("FDFB2_2024_1376")
        batch_i_index = REQUIRED_SOURCE_IDS.index("BATCH_BOOT_I")
        mutations = []
        for field, value in (
            ("title", "Changed FDFB2 title"),
            ("official_url", "https://example.invalid/fdfb2"),
            ("claim_classification", "CHANGED_CLASSIFICATION"),
            ("same_complexity", True),
            ("page_range", "1-999"),
        ):
            changed = json.loads(json.dumps(payload))
            changed["sources"][fdfb_index][field] = value
            mutations.append((field, changed))
        changed_doi = json.loads(json.dumps(payload))
        changed_doi["sources"][batch_i_index]["official_url"] = (
            "https://doi.org/10.1007/not-the-reviewed-chapter"
        )
        mutations.append(("doi", changed_doi))
        changed_claim = json.loads(json.dumps(payload))
        changed_claim["sources"][fdfb_index]["candidate_d_distinct_claim"][
            "falsifiable_full_sab_endpoint"
        ] = "A non-specific endpoint"
        mutations.append(("concrete_claim", changed_claim))
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "registry.json"
            for name, changed in mutations:
                with self.subTest(name=name):
                    path.write_text(json.dumps(changed), encoding="utf-8")
                    with self.assertRaises(SourceRegistryError):
                        load_source_registry(path)

    def test_verify_fulltext_checks_header_hash_page_and_anchor(self):
        record = load_source_registry(REGISTRY)[0]
        pdf = b"%PDF synthetic test\n"
        text = b"Synthetic anchor term\n\f"
        anchor = ClaimAnchor(
            page=1,
            section="fixture",
            paraphrase="Synthetic anchor.",
            required_terms=("anchor term",),
        )
        record = replace(
            record,
            pdf_sha256=sha256(pdf).hexdigest(),
            text_sha256=sha256(text).hexdigest(),
            page_range="1-1",
            anchors=(anchor,),
        )
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            (root / f"{record.id}.pdf").write_bytes(pdf)
            (root / f"{record.id}.txt").write_bytes(text)
            with patch.dict(
                REQUIRED_SOURCE_BINDINGS,
                {record.id: record.binding_sha256},
                clear=False,
            ):
                review = verify_fulltext(record, root)
                self.assertTrue(review.is_complete_and_bound())

                (root / f"{record.id}.pdf").write_bytes(
                    b"<html>challenge</html>"
                )
                invalid = verify_fulltext(record, root)
                self.assertEqual(invalid.review_status, "FULLTEXT_INVALID")
                self.assertIn("PDF header is not %PDF", invalid.validation_errors)

    def test_missing_registry_source_is_reported_as_missing(self):
        missing_record = next(
            row
            for row in load_source_registry(REGISTRY)
            if row.id == "NTRU_AMORT_2026_068"
        )
        with tempfile.TemporaryDirectory() as directory:
            review = verify_fulltext(missing_record, Path(directory))
        self.assertEqual(review.review_status, "FULLTEXT_MISSING")

    def test_missing_registry_source_ignores_archived_first_revision_cache(self):
        record = next(
            row
            for row in load_source_registry(REGISTRY)
            if row.id == "NTRU_AMORT_2026_068"
        )
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            (root / f"{record.id}.pdf").write_bytes(b"%PDF archived first revision")
            (root / f"{record.id}.txt").write_text(
                "Revisiting Polynomial NTRU first revision\n",
                encoding="utf-8",
            )
            review = verify_fulltext(record, root)
        self.assertEqual(review.review_status, "FULLTEXT_MISSING")
        self.assertIsNone(review.pdf_sha256)
        self.assertIsNone(review.text_sha256)
        self.assertIn("latest second revision", review.validation_errors[0])

    def test_output_root_rejects_directory_and_file_symlinks(self):
        with tempfile.TemporaryDirectory() as directory:
            repository = Path(directory) / "repo"
            references = repository / "references"
            output = references / "candidate_d_fulltext"
            output.mkdir(parents=True)
            validate_fulltext_output_root(repository, output)

            outside = Path(directory) / "outside"
            outside.mkdir()
            output.rmdir()
            try:
                os.symlink(outside, output, target_is_directory=True)
            except OSError as exc:
                self.skipTest(f"directory symlinks unavailable: {exc}")
            with self.assertRaises(SourceRegistryError):
                validate_fulltext_output_root(repository, output)
            output.unlink()
            output.mkdir()

            target = outside / "hash-target"
            os.symlink(target, output / "source_hashes.csv.part")
            with self.assertRaises(SourceRegistryError):
                validate_fulltext_output_root(repository, output)

    def test_markdown_routing_matches_pass_reject_and_block(self):
        pass_reviews = complete_fixture_reviews()
        with pinned_fixture_contract(pass_reviews) as rows:
            pass_decision, _ = evaluate_candidate_d_novelty(tuple(rows))
            pass_text = render_candidate_d_d1_markdown(
                pass_decision, tuple(rows)
            ).decode("utf-8")
        self.assertIn("D1_NOVELTY_AUDIT_PASS", pass_text)
        self.assertIn("9 of nine", pass_text)
        self.assertIn("Missing or invalid mandatory sources: none", pass_text)
        self.assertNotIn("BLOCK_CANDIDATE_D_INCOMPLETE_EVIDENCE", pass_text)

        reject_reviews = complete_fixture_reviews()
        reject_reviews["FDFB2_2024_1376"] = reject_reviews[
            "FDFB2_2024_1376"
        ].with_overlap(
            same_operator=True,
            same_complexity=True,
            distinct_sab_theorem=False,
        )
        with pinned_fixture_contract(reject_reviews) as rows:
            reject_decision, _ = evaluate_candidate_d_novelty(tuple(rows))
            reject_text = render_candidate_d_d1_markdown(
                reject_decision, tuple(rows)
            ).decode("utf-8")
        self.assertIn("prior-art rejection", reject_text)
        self.assertIn("Candidate E", reject_text)
        self.assertIn("9 of nine", reject_text)
        self.assertNotIn("question is unresolved", reject_text)
        self.assertNotIn("not a Candidate D rejection", reject_text)

        block_reviews = complete_fixture_reviews()
        block_reviews["BATCHBOOT_SEC26"] = block_reviews[
            "BATCHBOOT_SEC26"
        ].missing()
        with pinned_fixture_contract(block_reviews) as rows:
            block_decision, _ = evaluate_candidate_d_novelty(tuple(rows))
            block_text = render_candidate_d_d1_markdown(
                block_decision, tuple(rows)
            ).decode("utf-8")
        self.assertIn("BLOCK_CANDIDATE_D_INCOMPLETE_EVIDENCE", block_text)
        self.assertIn("8 of nine", block_text)
        self.assertNotIn("start only Candidate E", block_text)

    def test_artifact_writer_does_not_follow_legacy_temp_symlink(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory) / "repo"
            paths = (
                Path("docs/candidate_d_d1_novelty_audit.md"),
                Path("repro/candidate_d_admission/literature_sources.csv"),
                Path("repro/candidate_d_admission/claim_overlap.csv"),
                Path("repro/candidate_d_admission/novelty_gate.csv"),
            )
            artifacts = {path: f"content:{path}\n".encode() for path in paths}
            for path in paths:
                (root / path).parent.mkdir(parents=True, exist_ok=True)
            victim = Path(directory) / "victim"
            victim.write_text("unchanged", encoding="utf-8")
            legacy_temp = root / paths[0].with_name(paths[0].name + ".tmp")
            try:
                os.symlink(victim, legacy_temp)
            except OSError as exc:
                self.skipTest(f"file symlinks unavailable: {exc}")

            write_candidate_d_d1_artifacts(root, artifacts)
            self.assertEqual(victim.read_text(encoding="utf-8"), "unchanged")
            self.assertFalse((root / paths[0]).is_symlink())
            self.assertEqual((root / paths[0]).read_bytes(), artifacts[paths[0]])

    def test_d1_artifact_builder_is_byte_deterministic(self):
        first_decision, first = build_candidate_d_d1_artifacts(ROOT)
        second_decision, second = build_candidate_d_d1_artifacts(ROOT)
        self.assertEqual(first_decision, second_decision)
        self.assertEqual(first, second)
        self.assertEqual(first_decision, BLOCK_D1)
        for content in first.values():
            self.assertNotIn(str(ROOT).encode("utf-8"), content)


if __name__ == "__main__":
    unittest.main()
