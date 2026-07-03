# V130: Shared-Source Compact EP

## Summary

- Parent algorithm: PVW/MAT-SAB r-body research track.
- Focused module: shared source/mask plus r body external product.
- Optimization target: eventual complete-SAB `T_bootstrap/r`.
- Status labels: `[shared-source]`, `[microbench]`, `[not-production-header]`, `[not-hot-path]`.
- Decision: `PASS_STAGE130_SHARED_SOURCE_COMPACT_EP_POSITIVE_PRODUCTION_API_REQUIRED`.

## Next Rule

A positive Stage130 result permits a production API design gate only.
It still does not permit changing scalar/default SAB or claiming full
bootstrapping acceleration.
