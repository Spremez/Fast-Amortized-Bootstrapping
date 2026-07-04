# MAT-RLWE SAB Stage248 Structured Compact Prototype

## Summary

- Parent algorithm: PVW/MAT-SAB for 2025/686 sparse amortized bootstrapping.
- Focused module: compact representation of MAT selector action.
- Optimization target: future complete-SAB `T_bootstrap/r`; Stage248 itself is
  algebra/noise proof-prototype only.
- Status labels: `algebra_pass`, `toy_noise_pass`, `security_blocked`,
  `no_production_permission`.
- Main hypothesis: if keygen can enforce or hide off-lane body-to-body zero
  terms, compact MAT could remove terms before full-SAB integration.

## Mathematical Definition

For r=2, the shared-mask dense state is:

```text
x = [mask, body0, body1]
```

The compact prototype omits:

```text
M[body0, body1], M[body1, body0]
```

The constrained selector class requires both terms to be zero, making compact
and dense application equivalent in the finite model.

## Delta From Original Algorithm

| Original component | Variant component | Relationship | Evidence/status |
| --- | --- | --- | --- |
| generic dense MAT selector | off-lane-zero structured selector | changes key distribution | algebra pass, security blocked |
| production SAB CMUX | finite r=2 matrix probe | proof prototype | no production permission |

## Required Experiments

- Distribution/security preflight.
- Ring-level noise recurrence.
- Flag-only compact implementation only after proof gates.
- Complete-SAB A/B using `T_bootstrap/r`.
