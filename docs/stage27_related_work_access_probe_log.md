# Stage 27 Related-Work Access Probe Log

Date: 2026-06-26

## Purpose

This probe refreshes related-work source access for the PVW/MAT-SAB
novelty boundary. It records access state only; it does not perform
manual claim-to-source verification and does not upgrade novelty,
theorem-level 2025/686 citations, or all-parameter claims.

## Summary

| gate | status | detail |
|---|---|---|
| base_2025_686_fulltext | BLOCKED_FULLTEXT | FAB686_EPRINT_PDF=BLOCKED_403; FAB686_ACM_PDF=BLOCKED_403 |
| base_2025_686_metadata | PASS_METADATA_AVAILABLE | FAB686_AUTHOR_PUBLICATION=METADATA_OR_HTML_ONLY; FAB686_GITHUB=METADATA_OR_HTML_ONLY |
| shared_mask_prior_art_visibility | PASS_PRIOR_ART_RISK_VISIBLE | CM2112_ASKCRYPTO=METADATA_OR_HTML_ONLY; CM2112_DBLP=METADATA_OR_HTML_ONLY; CM2112_EPRINT_PDF=BLOCKED_403 |
| adjacent_incomplete_ntt_visibility | PASS_ADJACENT_VISIBLE | INTT696_USP_PDF=PDF_ACCESSIBLE; INTT696_GITHUB=METADATA_OR_HTML_ONLY |
| amortized_bs_lineage_visibility | PASS_LINEAGE_VISIBLE | GPVL23_COSIC_PDF=PDF_ACCESSIBLE |
| novelty_claim_gate | BLOCK_NOVELTY_CLAIM_PENDING_MANUAL_REVIEW | Shared-mask prior-art visibility is recorded, but manual full-text claim-to-source review is still required before any novelty upgrade. |
| related_work_decision | SCOPED_RELATED_WORK_REFRESHED__NOVELTY_STILL_BLOCKED | Machine source-access refresh completed; base full text remains blocked in this environment and novelty claims remain blocked. |

## Access Matrix

| source | role | status | url |
|---|---|---|---|
| FAB686_AUTHOR_PUBLICATION | base_metadata | METADATA_OR_HTML_ONLY | https://antonioguimaraes.org/publication/guimaraes-fast-2025/ |
| FAB686_GITHUB | base_code_metadata | METADATA_OR_HTML_ONLY | https://github.com/antoniocgj/Fast-Amortized-Bootstrapping |
| FAB686_EPRINT_PDF | base_fulltext_candidate | BLOCKED_403 | https://eprint.iacr.org/2025/686.pdf |
| FAB686_ACM_PDF | base_fulltext_candidate | BLOCKED_403 | https://dl.acm.org/doi/pdf/10.1145/3719027.3765181 |
| CM2112_ASKCRYPTO | shared_mask_prior_art_metadata | METADATA_OR_HTML_ONLY | https://askcryp.to/t/resource-topic-2025-2112-sharing-the-mask-tfhe-bootstrapping-on-packed-messages/25443 |
| CM2112_DBLP | shared_mask_prior_art_metadata | METADATA_OR_HTML_ONLY | https://dblp.org/rec/journals/iacr/BergeratBCOPT25.html |
| CM2112_EPRINT_PDF | shared_mask_prior_art_fulltext_candidate | BLOCKED_403 | https://eprint.iacr.org/2025/2112.pdf |
| INTT696_USP_PDF | adjacent_acceleration_fulltext | PDF_ACCESSIBLE | https://repositorio.usp.br/directbitstream/69b0ba87-a92a-40e3-94ed-ecdb8ee395ec/Faster_amortized_bootstrapping_using_the_incomplete_NTT_for_free.pdf |
| INTT696_GITHUB | adjacent_acceleration_code | METADATA_OR_HTML_ONLY | https://github.com/thalespaiva/incomplete_ntt_amortized_bt |
| GPVL23_COSIC_PDF | amortized_bs_lineage_fulltext | PDF_ACCESSIBLE | https://www.esat.kuleuven.be/cosic/publications/article-3610.pdf |
| BOOT_SURVEY_2026_RG | secondary_survey_candidate | BLOCKED_403 | https://www.researchgate.net/publication/390905714_Bootstrapping_in_FHEW-like_cryptosystems_A_survey |

## Decision

The safe claim remains a scoped engineering/systems claim. The probe
records visible shared-mask prior-art risk and adjacent amortized
bootstrapping sources, while keeping novelty and theorem-level
citation claims blocked until full texts are manually reviewed.
