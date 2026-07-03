# V131: Shared-Source Compact EP Production API

## Summary

- Parent algorithm: PVW/MAT-SAB r-body research track.
- Focused module: production API/header boundary for shared-source compact EP.
- Optimization target: eventual complete-SAB `T_bootstrap/r`.
- Status labels: `[production-api]`, `[not-sab-integrated]`, `[not-full-bootstrap]`.
- Decision: `PASS_STAGE131_SHARED_SOURCE_PRODUCTION_API_READY_SAB_INTEGRATION_DESIGN`.

## Output Semantics

The API returns `MAT_TRGSW_COMPACT_OUTPUT_DFT`, one DFT mask/body pair
per lane. Compressing this into a single shared-output-mask
`PVW_TMLWE_DFT` is not part of this stage and must be separately tested.
