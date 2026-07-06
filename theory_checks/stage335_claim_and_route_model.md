# Stage335 Claim And Route Model

The model separates three objects:

1. Existing exact PVW/MAT-SAB: a closed r-body ciphertext state that has complete
   SAB evidence under `T_bootstrap/r`.
2. Common-mask/shared-mask prior art: real adjacent work that already studies
   shared masks and multiple bodies for TFHE bootstrapping.
3. Compact selector variant: an attempted row-skipping improvement whose current
   lane-local kernel is correct in isolation, but whose state is not closed for
   the full 2025/686 selector equations.

Promotion rule:

- exact PVW/MAT-SAB may be optimized and measured at full SAB level;
- compact selector may not enter SAB hot paths until a closed state supports
  neighbor/cross-body equations and passes encrypted keygen/noise/phase gates;
- novelty wording must remain scoped unless every high-risk adjacent full text is
  audited and distinguishes the claim.
