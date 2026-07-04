# Stage313 Narrow32 Attribution Model

Stage311 showed a positive isolated digit-conversion microbench. Stage312 showed
no complete-SAB `T_bootstrap/r` promotion. Stage313 reconciles those results by
profiling the same complete SAB path with body, MAT split, and direct DFT
lifecycle counters.

The expected failure mechanism is component dilution: even a visible digit
materialization improvement can be smaller than full-pipeline variation or be
offset by unchanged IFFT/dense/schedule costs. Therefore future local digit
microvariants need a full-SAB component budget before implementation.
