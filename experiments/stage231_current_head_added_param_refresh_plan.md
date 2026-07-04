# Stage231 Current-Head Added-Parameter Refresh Plan

## Executed Smoke Budget

- Parameters: `SET_4_5_2048`, `SET_2_3_4096`.
- Lanes: r=2 and r=4.
- Performance: 1 complete-SAB A/B run per param/r.
- Noise: 1 deterministic seed per param/r.
- Backend: `spqlios_avx512`.
- Flags: `MAT_TRGSW_AVX512_SMALLR_SPECIALIZED=true`,
  `SAB_PVW_ACTIVE_BUFFER_FUSION=true`.

## Promotion Budget

If these added parameters are used in a main paper table, rerun with at least
10 complete-SAB A/B runs, 20 final-output noise seeds, and resource/keygen/RSS
refresh for the selected param/r set.
