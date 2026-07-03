# V143: r4-Unrolled Full SAB Smoke

## Summary

- Parent algorithm: PVW/MAT-SAB.
- Focused module: full SAB bootstrapping with active buffer plus r4-unrolled closed full-MAT external product.
- Optimization target: amortized `T_bootstrap/r`.
- Status labels: `[smoke positive]`, `[repeated gate pending]`.
- Main hypothesis: r4-unrolled closed full-MAT gains survive enough SAB overhead to improve complete PVW/SAB per-lane time.
