# Stage128 Compact EP API Boundary Gate Plan

Date: 2026-07-03

## Objective

Wrap the Stage127 isolated compact EP kernel in MOSFHET-adjacent API
shapes for selector, output, and scratch ownership. This remains a
standalone generated probe and does not modify production headers.

## Command

```bash
python scripts/build_stage128_compact_ep_api_boundary_gate.py
```

## Falsification Criteria

- MOSFHET build or probe compile fails;
- API-owned polynomial buffers are null, aliased, or leaked;
- metadata or invalid-lane guards fail;
- the hot kernel allocates instead of using caller scratch;
- API-bound kernel loses Stage127 component/phase/noise equivalence;
- body-only API kernel does not fail.

Passing this stage permits isolated microbench/profiling only; it still
does not permit SAB hot-path integration.
