# Stage340 Parameter Matrix Model

The Stage339 primary claim is scoped to one current-head r=4 row. A broader
parameter claim requires current-head evidence for every claimed parameter and
body-lane count.

Hot-code equivalence is checked separately from the Git commit id. If Stage331's
run head differs from HEAD but `src/`, `Makefile`, and `include/` have not
changed, the primary r=4 performance evidence can remain hot-code current. This
does not promote historical r=2 or added-parameter rows; those still require
fresh current-head logs before broader wording.

The primary metric remains complete `T_bootstrap/r` against repeated scalar SAB
under the same backend. Windows or dry-run output is not performance evidence.
