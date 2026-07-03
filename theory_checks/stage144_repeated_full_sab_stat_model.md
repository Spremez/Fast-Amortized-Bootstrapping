# Stage144 Repeated Full-SAB Statistical Model

Date: 2026-07-03

The tested claim is scoped to implementation-level MAT-aware AVX512 improvement inside the already valid PVW/MAT-SAB full bootstrapping path.

For each paired run index `i`:

```text
S_i = T_lane(generic_active, i) / T_lane(r4_unrolled_active, i)
T_lane = T_complete_bootstrap(PVW/MAT-SAB, r=4) / 4
```

Stage144 reports mean/min and a t-based 95% interval over paired `S_i`. The interval is descriptive because the run count is still small; it is adequate for promote-candidate routing, not for paper-final claims.
