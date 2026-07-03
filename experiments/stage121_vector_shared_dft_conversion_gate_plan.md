# Stage121 Vector-Shared DFT/Conversion Gate Plan

Date: 2026-07-03

## Objective

Move the Stage120 vector-shared real struct prototype through a frequency
domain conversion gate before any MOSFHET or SAB hot-path integration.
The gate uses an exact modular negacyclic NTT/DFT over modulus 12289
so conversion errors are semantic errors, not floating-point noise.

## Command

```bash
python scripts/build_stage121_vector_shared_dft_conversion_gate.py
```

## Falsification Criteria

- no valid 2N-th root for N=32 or N=64;
- any mask/body/secret round-trip mismatch;
- any DFT-domain phase mismatch versus coefficient-domain phase;
- any noisy phase mismatch or digit-sum noise-bound violation;
- vector-shared DFT polynomial count exceeds dense reference count.

Passing this stage permits only a structured external-product arithmetic
prototype outside `sab_pvw_*`.
