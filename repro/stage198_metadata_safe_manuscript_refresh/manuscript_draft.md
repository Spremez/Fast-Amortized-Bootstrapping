# Metadata-Safe Manuscript Refresh: PVW/MAT-SAB

This draft is generated from `repro/stage197_metadata_safe_citation_bank/`.
It is a controlled scoped draft, not a final paper.

## Abstract

We evaluate a PVW/MAT r-body form of the SAB implementation using complete bootstrapping time per processed lane, T_bootstrap/r, as the primary metric. The current exact full-MAT path records mean 1.131666667x speedup, minimum 1.115000000x, and CI-low 1.095041982x on T_bootstrap/r against repeated scalar SAB. The current manuscript artifact is a scoped skeleton and support package, not a final paper. All result language is limited to recorded conditions and local reproducibility artifacts.

## Background and Source Boundary

Public metadata identifies ePrint 2025/686 as 'Fast amortized bootstrapping with small keys and polynomial noise overhead', the target baseline/source line for this implementation study. The public code-route probe for the 2025/686 implementation repository is reachable in the Stage196 source refresh. The draft uses this only as source-line context until a reviewed full text is available.

## Measured Result

We evaluate a PVW/MAT r-body form of the SAB implementation using complete bootstrapping time per processed lane, T_bootstrap/r, as the primary metric. The current exact full-MAT path records mean 1.131666667x speedup, minimum 1.115000000x, and CI-low 1.095041982x on T_bootstrap/r against repeated scalar SAB. The comparison remains complete bootstrapping against repeated scalar SAB and must be reported with backend, parameter, seed, and commit metadata.

## Related-Work Boundary

Public metadata for 2025/696 and 2025/2112 creates adjacent related-work obligations, so novelty wording must remain conservative until full-text comparison is complete. This paragraph is a review obligation, not a final related-work comparison.

## Limitations and Next Gates

Compact/shared-output MAT-SAB remains a proof-only route with recorded T1/T2/T4 blockers and no complete-SAB implementation claim. Current exact addmul and DFT/conversion routes have no promoted local code candidate after Stage193 and Stage194 preflights. The current manuscript artifact is a scoped skeleton and support package, not a final paper. The next valid routes are full-text anchor intake, metadata-safe draft maintenance, or a new mechanism with correctness, noise, resource, and complete-SAB gates.

## Reproduction Entry

Use `repro/stage198_metadata_safe_manuscript_refresh/reproduction_commands.md` to rebuild and audit this draft.
