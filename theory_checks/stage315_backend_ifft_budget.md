# Stage315 Backend IFFT Budget

The project comparison dimension is `T_bootstrap/r`, not raw one-call latency
alone.  For r independent LUT/SAB lanes, the scalar baseline is repeated scalar
SAB and the PVW/MAT endpoint is one r-body SAB call divided by r.

The current r=4 direct path already includes backend FromDFT-add materialization
and direct sub-DTF.  Stage313 attributes the direct profile as:

- MAT EP lifecycle share of body: 0.585042
- digit-to-double share of body: 0.172510
- SPQLIOS IFFT share of body: 0.181943
- dense MAT addmul share of body: 0.215408

For a component with body share `s`, reducing only that component by `x` gives
`speedup = 1 / (1 - s*x)`.  To clear the Stage314 admission gate of 1.02x body
budget, the SPQLIOS IFFT component must shrink by at least
0.107769.  A 10% IFFT reduction projects to
1.018531, while a 25% reduction
projects to 1.047653.

Therefore Stage316 is admitted only as a backend ABI/prototype preflight:
produce isolated correctness and IFFT microbench evidence before touching the
full SAB path.  If the backend cannot plausibly clear the IFFT reduction gate,
stop and return to higher-level schedule candidates with an explicit
materialization-count proof.
