#!/usr/bin/env python3
"""Register the verified ePrint 2026/068 rev.2 (2026-07-16) full text into the
Candidate D D1 source registry, per the documented resume condition in
docs/candidate_d_admission_report.md (Finite Resume Condition section).

Steps performed:
  1. Update literature/candidate_d_source_registry.json for NTRU_AMORT_2026_068
     (hashes, page range, claim classification, anchors, review status).
  2. Recompute the canonical source binding SHA-256 with the repository's own
     _parse_source logic.
  3. Update REQUIRED_SOURCE_BINDINGS in research/mat_sab/candidate_d_literature.py.

Run from anywhere; paths are resolved from __file__'s drive.
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
WT = HERE.parents[1] / ".worktrees" / "candidate-a-star-cycle-gate"
REGISTRY = WT / "literature" / "candidate_d_source_registry.json"
PIN_FILE = WT / "research" / "mat_sab" / "candidate_d_literature.py"

PDF_SHA = "8083db16cd43613968e02846ad16d3f4e2c4d8dd0c64692300e31bc184cbda84"
TEXT_SHA = "4b94fd8372953d1ef311c7f8d04455d5021ae32c6389d729a3688404a3921cc0"

NEW_ANCHORS = [
    {
        "page": 1,
        "section": "Abstract",
        "paraphrase": (
            "Adapts monomial-by-polynomial amortized bootstrapping to NTRU "
            "ciphertexts with sparse secret keys, reducing dominant "
            "per-coefficient work from O(n*l_Q) to O(h*l_pos) external-product "
            "operations."
        ),
        "required_terms": ["sparse secret keys", "external-product"],
    },
    {
        "page": 2,
        "section": "Introduction",
        "paraphrase": (
            "Credits Guimaraes and Pereira (GP25) as the origin of the adapted "
            "MPMul amortization and states the NTRU adaptation is nontrivial, "
            "achieved through a difference-vector representation of sparse "
            "secret-key positions."
        ),
        "required_terms": ["Guimarães", "nontrivial", "difference-vector"],
    },
    {
        "page": 9,
        "section": "Algorithm 2",
        "paraphrase": (
            "The full amortized bootstrapping algorithm initializes each "
            "accumulator with the test vector before the sparse rotation "
            "schedule; lookup tables are bound before rotation and no "
            "LUT-independent lane-operator state appears."
        ),
        "required_terms": ["Algorithm 2", "test vector"],
    },
    {
        "page": 17,
        "section": "Section 6.4",
        "paraphrase": (
            "Reports the single-threaded benchmark of 2.68 ms per refreshed "
            "message coefficient at n = 8192 against FINAL, TFHE, and GP25 on "
            "identical hardware."
        ),
        "required_terms": ["2.68", "amortized"],
    },
    {
        "page": 19,
        "section": "Conclusion and Future Work",
        "paraphrase": (
            "Leaves whether GP25's two-key accumulator technique applies to "
            "the polynomial-NTRU setting as an open question for future work; "
            "no multi-lane matrix accumulator is constructed."
        ),
        "required_terms": ["two-key accumulator", "future work"],
    },
]


def main() -> None:
    payload = json.loads(REGISTRY.read_text(encoding="utf-8"))
    sources = payload["sources"]
    entry = next(s for s in sources if s["id"] == "NTRU_AMORT_2026_068")

    entry["review_status"] = "FULLTEXT_REVIEWED"
    entry["pdf_sha256"] = PDF_SHA
    entry["text_sha256"] = TEXT_SHA
    entry["page_range"] = "1-22"
    entry["claim_classification"] = (
        "NTRU_TRANSFER_OF_GP25_MPMUL_NO_LATE_BOUND_OPERATOR_"
        "NO_MULTI_LANE_ACCUMULATOR"
    )
    entry["same_operator"] = False
    entry["same_complexity"] = False
    entry["distinct_sab_theorem"] = True
    entry["distinct_complete_result"] = True
    entry["falsifiable_full_sab_endpoint"] = True
    entry["composition_with_batchboot"] = "POSSIBLE_SEPARATE_AXIS"
    entry["anchors"] = NEW_ANCHORS

    REGISTRY.write_text(
        json.dumps(payload, indent=2, ensure_ascii=False) + "\n",
        encoding="utf-8",
    )

    sys.path.insert(0, str(WT))
    from research.mat_sab.candidate_d_literature import _parse_source

    record = _parse_source(entry)
    binding = record.binding_sha256
    print("new NTRU_AMORT_2026_068 binding_sha256:", binding)

    pin_text = PIN_FILE.read_text(encoding="utf-8")
    old_pin = (
        '"NTRU_AMORT_2026_068": '
        '"aa982c2f1ba7751c8702489c4911ebfcb7c59ae58f93a2252c10e6879d483358"'
    )
    new_pin = f'"NTRU_AMORT_2026_068": "{binding}"'
    if old_pin not in pin_text:
        raise SystemExit("old NTRU pin not found verbatim; aborting")
    PIN_FILE.write_text(
        pin_text.replace(old_pin, new_pin), encoding="utf-8"
    )
    print("REQUIRED_SOURCE_BINDINGS pin updated")

    # Round-trip validation with the repository's own strict loader.
    import importlib
    import research.mat_sab.candidate_d_literature as lit

    importlib.reload(lit)
    records = lit.load_source_registry(REGISTRY)
    ntru = next(r for r in records if r.id == "NTRU_AMORT_2026_068")
    assert ntru.binding_sha256 == lit.REQUIRED_SOURCE_BINDINGS[ntru.id]
    print("registry re-loads under the strict pin check: OK")


if __name__ == "__main__":
    main()
