# MAT-RLWE SAB Stage221 Compact Noise Recurrence

The compact route keeps dense public selector rows for key distribution while
allowing evaluator-side skipping of semantic-zero dummy rows after proof. The
active rows per processed bit are `4` for the current r=2/4/6 selector model,
but public rows per bit still grow as `(r + 1)^2 / r`.

Stage221 therefore supports only a bounded next step: isolated compact external
product correctness/noise testing. Complete SAB integration remains gated.
