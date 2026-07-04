# Stage252 Non-Binary MAT Selector Key Skeleton Model

For each input-key component, the current binary PVW/MAT key stores
`(h+1) * r_prec` distance-bit selector objects. Non-binary scalar SAB requires
extra selector families:

- include-zero: `h` selectors for `s_coff`;
- ternary: `h` selectors for `s_sign`.

The MAT extension must provide those selector families as shared-mask,
r-body-compatible `MAT_TRGSW_DFT` objects. This skeleton records the required
object topology and API contracts only. It deliberately does not define
encrypted keygen noise, external-product composition, full sparse schedule
integration, or performance claims.
