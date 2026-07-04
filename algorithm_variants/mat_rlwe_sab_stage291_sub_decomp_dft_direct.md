# Stage291 MAT_TRGSW_SUB_DECOMP_DFT_DIRECT

Flag: `MAT_TRGSW_SUB_DECOMP_DFT_DIRECT=true`.

Decision: `PASS_STAGE291_SUB_DECOMP_DFT_DIRECT_MICRO_POSITIVE_FULL_SAB_REQUIRED`.

This is a default-off implementation candidate for the SAB sub-DTF hot path.
It does not change scalar SAB and does not alter selector semantics. It may
enter a full-SAB `T_bootstrap/r` benchmark only after this isolated gate passes.
