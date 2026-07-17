# Candidate B: Factorized Star-Cycle

Status: `REJECT_CANDIDATE_B_EXACT_STANDARD_PVW_FACTORIZATION_ROUTE_TO_C`.

Candidate B tests whether the Stage203 four-family star-cycle semantics can
be realized as a complete Theta(r)-work standard-PVW encrypted operator.
The multiplicative parity-evaluation image rejects exact q<r representation
of a supported full-rank independent-error witness. Generic dense q=r and
noiseless-only variants do not supply the required complete cost reduction.
B2 changes the distribution and requires Candidate C-level analysis.
B3/B4 have no registered complete construction, so B routes to C.

## Primary-Source Boundary

- 2025/686 target SAB, locally reviewed full-text anchors:
  https://eprint.iacr.org/2025/686
- Common-mask ciphertext and CM-GGSW prior art:
  https://eprint.iacr.org/2025/2112
- Packed/PVW and standard TFHE sources are metadata/background scoped:
  https://eprint.iacr.org/2012/565 and
  https://eprint.iacr.org/2018/421

The local Stage102 and Stage335 logs contain the reviewed full-text claim
anchors. The PVW and TFHE rows are used only for background positioning. The
standard common-mask GGSW realization retains a quadratic `(k+r)^2` lane
factor. No checked source supplies the complete Candidate B conjunction.
This is not a general impossibility theorem and is not a novelty proof.

This disposition is not a general impossibility theorem. It changes no
production implementation and makes no complete-SAB performance claim.
