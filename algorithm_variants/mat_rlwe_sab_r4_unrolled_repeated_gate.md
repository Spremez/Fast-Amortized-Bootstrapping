# V144: r4-Unrolled Repeated Full-SAB Candidate

## Summary

- Parent algorithm: PVW/MAT-SAB.
- Focused module: complete r=4 SAB bootstrapping with active-buffer schedule and r4-unrolled MAT external product.
- Optimization target: amortized `T_bootstrap/r`.
- Status labels: `[repeated gate]`, `[noise/resource checked]`, `[promotion policy pending]`.
- Main hypothesis: the Stage142 r4-unrolled closed full-MAT kernel yields a stable complete-SAB per-lane benefit over generic active PVW without correctness, noise, or resource regressions that would invalidate the path.
