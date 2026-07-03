# Stage200 R-Body Gap Lower-Bound Model

Under the current exact torus-input PVW_TMLWE state with k=1 and r body lanes,
there are m=r+1 input components. With T gadget levels, a same-format external
product that enters the DFT multiplication domain needs at least m*T input DFT
conversions unless a new closed representation is supplied.

The current production closed full-MAT path reaches that input-conversion
count. The remaining same-format gap is therefore not another shared-mask input
conversion count reduction; it is dense row/output interaction, backend
constant factors, or a representation/keygen proof route.

The finite probe tests two shortcut families:

- omitting any input component from a dense selector;
- treating toy gadget decomposition as additive across an update.

Both are rejected in the sampled finite model. This does not rule out all
future representations; it records what must be proven before they are used.
