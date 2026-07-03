# Stage164 Representation Closure Model

For a PVW/MAT accumulator with one shared mask and `r` bodies, a generic dense
MAT selector maps `1+r` decomposed input rows to `1+r` output polynomials. This
is a full linear map with `(1+r)^2` independent selector terms per gadget level.

Any compact route using fewer independent terms must either:

1. prove that the key distribution intentionally constrains the selector while
   preserving security and noise bounds; or
2. accept that it is not exact for the generic dense selector.

Stage139 already shows that diagonal compact output is not a direct PVW_TMLWE
state because masks become lane-specific. Stage156 rejects DFT-only persistence
because decomposition is nonlinear. Stage162 closes same-format materialization
count reduction, and Stage163 rejects component-major backend batching as a
production candidate.

Therefore the non-speculative next step is to optimize the valid closed
full-MAT path at the decompose/DFT/addmul boundary, with exact DFT output as
the correctness gate.
