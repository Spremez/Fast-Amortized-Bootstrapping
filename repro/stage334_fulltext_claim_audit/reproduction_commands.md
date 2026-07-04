# Stage334 Reproduction Commands

```sh
python scripts/build_stage334_fulltext_claim_audit.py
```

Optional local extraction used before this builder:

```sh
pdftotext -layout references/stage334_fulltext_claim_audit/pdf/micciancio_sorrell_2018_ring_packing.pdf \
  references/stage334_fulltext_claim_audit/text/micciancio_sorrell_2018_ring_packing.txt
```

Full paper PDF/text files under `references/stage334_fulltext_claim_audit/` are
ignored by Git; the repro pack records hashes and line anchors only.
