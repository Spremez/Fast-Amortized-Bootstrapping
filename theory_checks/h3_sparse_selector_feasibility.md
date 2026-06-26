# H3 Sparse Selector Feasibility Check

Date: 2026-06-26

## Question

Can the SAB-specific monomial selector structure be used to skip dense
MAT_TRGSW external-product work inside the current `sab_pvw_*` path?

## Current Code Facts

- `sab_pvw_new_binary_key()` derives secret-key gap values during key
  generation and encrypts each gap bit with `mat_trgsw_monomial_sample()`.
- The evaluator receives `MAT_TRGSW_DFT` selector ciphertexts, not plaintext
  selector bits.
- `mat_trgsw_mul_pvmtmlwe_DFT()` treats every selector row/output as encrypted
  data. After encryption and DFT conversion, a bit value of zero does not make
  the ciphertext row structurally zero.
- The promoted implementation keeps the scalar SAB path unchanged and uses
  `SAB_PVW_ACTIVE_BUFFER_FUSION=true` only on the explicit PVW path.

## Theory Risk

Skipping MAT row/output products based on plaintext selector bits is not
available in the public evaluation interface. Adding plaintext skip metadata
would reveal secret-dependent SAB gap bits unless a new key-format/security
argument proves that the leaked metadata is public or harmless.

Skipping work by inspecting ciphertext coefficients is also invalid: encrypted
zero and encrypted one selector bits are both dense noisy ciphertext objects,
so ciphertext sparsity is not a semantic invariant.

## Decision

`REJECT_CURRENT_SPARSE_SELECTOR_SHORTCUT`

The current H3 shortcut is not a safe local code task. It can be reopened only
as a new design with:

- an explicit public metadata policy or leakage proof;
- a revised key-format plan that preserves the scalar baseline;
- staged r=1/2/4 correctness gates;
- full SAB A/B, noise, resource, and claim-scope gates.

This does not disprove all SAB-specific sparse-MAT ideas. It only rejects the
direct shortcut "skip encrypted selector work because the underlying bit is
zero" under the current implementation and evidence.
