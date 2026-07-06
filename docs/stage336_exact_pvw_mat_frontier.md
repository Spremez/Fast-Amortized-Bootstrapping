# Stage336 Exact PVW/MAT Frontier

Decision: `PASS_STAGE336_CURRENT_HEAD_SMOKE_SELECT_DIRECT_IFFT_FRONTIER`.

The current compact selector route is blocked for complete SAB, so Stage336
returns to the exact PVW/MAT-SAB path that already has complete `T_bootstrap/r`
evidence.  A current-head FFNT smoke was run only as a correctness/build guard:
it is not used as a performance result.

The selected next candidate is the direct IFFT lifecycle inside the direct
torus-to-DFT path.  This is a closed-path candidate because it preserves the
same PVW/MAT state representation; it only attempts to reduce conversion
lifecycle cost.

## Gates

| gate | status | metric | value | interpretation |
| --- | --- | --- | --- | --- |
| G1_current_head_smoke | PASS | FFNT scalar/PVW smoke | pass | Current head retains scalar and sab_pvw smoke correctness; not a performance claim. |
| G2_primary_metric | PASS | T_bootstrap/r | stage331_highstat | Stage336 keeps per-lane amortized complete SAB as the primary endpoint. |
| G3_compact_boundary | PASS | Stage335 compact route | denied | Compact selector is not the next implementation path. |
| G4_profile_target | PASS | dominant closed-path residual | torus_to_dft/direct_ifft_lifecycle | Stage337 should attack DFT lifecycle under isolated equivalence first. |
| G5_decision | PASS_STAGE336_CURRENT_HEAD_SMOKE_SELECT_DIRECT_IFFT_FRONTIER | stage decision | stage337_direct_ifft_candidate | Move to concrete closed-path microbench/variant design. |
