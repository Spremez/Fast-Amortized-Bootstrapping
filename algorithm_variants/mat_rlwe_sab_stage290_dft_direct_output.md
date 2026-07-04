# Stage290 DFT Direct-Output Variant

Flag: `MAT_TRGSW_DFT_ARRAY_DIRECT_OUTPUT=true`.

Decision: `NEUTRAL_STAGE290_DFT_DIRECT_OUTPUT_NO_PROMOTION`.

The path is explicit and default-off. It changes only the multi-row DFT array
implementation used by MAT external-product experiments. It must pass full-SAB
`T_bootstrap/r` A/B before becoming a SAB optimization claim.
