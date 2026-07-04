# Stage324 Selector-Transpose Preflight Variant

Status: selected only for isolated Stage325 resource and microbench probing.

Permitted work:

- build a faithful selector-transposed view or standalone layout probe;
- compare exact dense addmul output against current row/poly layout;
- measure build/copy cost, isolated dense addmul speed, and memory ratio;
- project full-SAB value using Stage322/323 dense share.

Forbidden work:

- changing default MAT_TRGSW_DFT keygen or key loading;
- changing scalar SAB;
- claiming complete SAB acceleration before full `T_bootstrap/r` A/B.
