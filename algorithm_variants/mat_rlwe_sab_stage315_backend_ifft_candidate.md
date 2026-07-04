# Stage315 Candidate: SPQLIOS Batch IFFT ABI

Status: `PASS_STAGE315_BACKEND_IFFT_ADMISSION_SELECT_STAGE316_ABI_PREFLIGHT`.

## Candidate

`H315-C1-spqlios-batch-ifft-abi` targets the rows=k+r=5 direct sub-DTF path in
`mat_trgsw_sub_decompose_DFT_direct`.  The candidate is not another digit
conversion tweak and not another wrapper around `pvmtmlwe_from_DFT_add`; those
routes are either closed or already part of the current direct baseline.

## Algorithmic Delta

The algebra is unchanged.  The implementation should replace:

```text
for row in rows:
    digit[row] = gadget_decompose(lhs[row], rhs[row])
    ifft(tables_reverse, digit[row])
```

with an isolated backend routine that returns the same transformed rows:

```text
batch_digit_ifft_rows5(tables_reverse, rows)
```

or proves that no such backend API can meet the budget on this backend.

## Admission Gate For Implementation

- isolated correctness against the current per-row `ifft`;
- at least 0.107769 reduction in the IFFT component, or an
  equivalent full-SAB budget above 1.02 before SAB integration;
- full SAB `T_bootstrap/r` A/B only after the isolated gate passes;
- scalar SAB default path unchanged.
