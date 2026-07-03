# Stage218 Compact Key-Object/Noise Model

The prototype represents compact selector rows as dense public rows with a role
bit: active or semantic-zero dummy. The evaluator may skip dummy rows only if
their semantic contribution is proven zero. Public randomness is not reduced.

This finite model checks phase equivalence and negative controls. It does not
prove standard key distribution, RLWE/LWE security, or production SAB noise.
Those remain separate gates before any `sab_pvw_*` integration.
