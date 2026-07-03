# Stage139 Compact Closure Model

Date: 2026-07-03

A PVW/MAT-RLWE ciphertext state used by SAB has one shared mask polynomial `a` and r body polynomials.
Stage138's compact diagonal output stores one output mask per lane. This can accelerate repeated independent lane-pair work, but it is not automatically a PVW_TMLWE state.
If output masks differ across lanes, converting them to one shared mask while preserving phase would require secret-key-dependent correction, so direct SAB integration is invalid.

## Closure Rows

| backend | r | N | T | Bg_bit | seed | mask_mismatches | max_mask_gap | status |
|---|---|---|---|---|---|---|---|---|
| spqlios | 2 | 512 | 7 | 7 | 0 | 512 | 1162068678945864163524608.000000000 | EXPECTED_NONCLOSED_COMPACT_OUTPUT |
| spqlios | 4 | 512 | 7 | 7 | 0 | 1536 | 1329579791263764056113152.000000000 | EXPECTED_NONCLOSED_COMPACT_OUTPUT |
| spqlios | 6 | 512 | 7 | 7 | 0 | 2560 | 1375229237205484026462208.000000000 | EXPECTED_NONCLOSED_COMPACT_OUTPUT |
| spqlios | 2 | 1024 | 7 | 7 | 0 | 1024 | 2905355668607332614406144.000000000 | EXPECTED_NONCLOSED_COMPACT_OUTPUT |
| spqlios | 4 | 1024 | 7 | 7 | 0 | 3072 | 2905355668607332614406144.000000000 | EXPECTED_NONCLOSED_COMPACT_OUTPUT |
| spqlios | 6 | 1024 | 7 | 7 | 0 | 5120 | 2905355668607332614406144.000000000 | EXPECTED_NONCLOSED_COMPACT_OUTPUT |
