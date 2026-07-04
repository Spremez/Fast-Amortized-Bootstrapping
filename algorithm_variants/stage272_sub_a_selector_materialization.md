# Stage272 Candidate: Non-Binary Sub_a Selector Materialization

Status: design-only, preimplementation.

## Delta

Candidate S272-A targets the current non-binary `sub_a` sequence:

```text
selector MAT external product -> from_DFT(tmp) -> addto(p[idx], tmp)
```

The proposed family explores an alias-safe fused materialization/add path.
The first executable gate is not a speed test; it is an isolated alias-safety
and phase-equivalence microtest.

## Complexity

The selector MAT external-product count is unchanged at `39 * 2048 = 79872`
for r=4 target non-binary SAB. Therefore this candidate can reduce only
constant factors in materialization/add, not the SAB schedule length.

## Promotion Rule

Only after alias/equivalence passes may an explicit flag be added for a full
SAB `T_bootstrap/r` smoke. Repeated performance is required for promotion.
