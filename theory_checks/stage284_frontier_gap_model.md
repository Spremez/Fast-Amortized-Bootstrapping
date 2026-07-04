# Stage284 Frontier Gap Model

## Endpoint

The active endpoint is:

```text
A(r) = T_complete_bootstrap_producing_r_outputs / r
speedup(r) = A_repeated_scalar(r) / A_mat(r)
```

Stage284 uses the Stage281 repeated value for the selected candidate and
keeps all native claims blocked by Stage283.

## Residual/Amdahl Model

For a measured component share `s_i` in the selected candidate profile:

```text
A_after_component_reduction(x) = A_current * (1 - s_i * x)
projected_speedup(x) = A_current / A_after_component_reduction(x)
zero_component_ceiling = 1 / (1 - s_i)
```

These are prioritization projections, not speed claims.  A projection becomes
evidence only after isolated correctness, repeated complete-SAB `T_bootstrap/r`,
noise/resource, and backend-fair gates pass.

## Current Interpretation

- The selected candidate is locally repeated-positive against fast control.
- MAT EP remains the largest selected-candidate residual share.
- from_DFT/materialization is also large but prior direct-add-only work was
  not sufficient, so it needs a new alias/lifecycle mechanism.
- sub_a, NCMUX, and tail residuals are not first-order standalone targets under
  the current profile.
- The compact/body-linear term model remains a research route, not an
  admissible exact-dense lower bound.
