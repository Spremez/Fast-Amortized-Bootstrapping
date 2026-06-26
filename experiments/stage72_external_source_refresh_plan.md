# Stage72 External Source Refresh Plan

Date: 2026-06-26

## Goal

Refresh the current external source state for 2025/686 after Stage71 so the
project can distinguish:

- visible metadata/code routes;
- direct full-text routes still blocked by HTTP/Cloudflare state;
- claim boundaries that must remain blocked until a local reviewed full-text
  artifact exists.

## Commands

```bash
python scripts/build_stage72_external_source_refresh.py
python scripts/build_remaining_blocker_dashboard.py
python scripts/build_stage42_evidence_closure_audit.py
python scripts/build_stage51_goal_completion_frontier.py
python scripts/build_stage57_scope_label_audit.py
python scripts/build_stage68_frontier_closure_consistency.py
python scripts/build_stage42_evidence_closure_audit.py
```

## Gates

- author publication page and BibTeX metadata are reachable;
- Crossref DOI metadata is reachable;
- author-linked implementation route is reachable;
- ePrint/ACM direct PDF routes are either accessible or explicitly recorded as
  blocked;
- `stage72_decision` is
  `PASS_EXTERNAL_SOURCE_REFRESH_STRONGER_CLAIMS_BLOCKED`;
- Stage42 closure and verifier remain passed;
- no SAB code, speedup claim, novelty claim, theorem-level claim, or
  MAT-AVX512 optimality claim is upgraded.

## Failure Handling

- If metadata routes fail, keep CB6/CB7 blocked and record the failed route.
- If a direct PDF route becomes accessible, do not upgrade claims immediately;
  register the artifact through the full-text review gate first.
- If Stage42 closure fails, repair closure/manifest registration before
  relying on Stage72.
