# Stage330 High-Stat Reconciliation Model

## Research Question

Can Stage296's 10-run direct-DFT complete-SAB result be used to close the
Stage328 high-stat gap for the current PVW/MAT-SAB claim?

## Decision Logic

Let `M` be the endpoint `T_bootstrap/r`, where `r` is the number of MAT/RLWE
body lanes and the baseline is repeated scalar SAB over the same number of
plaintext bits.  Evidence can be bridged only if the following are true:

1. parameter, backend, branch, `r`, and direct-DFT flags match;
2. both campaigns measure complete SAB `M`, not an isolated kernel;
3. the source boundary is explicit.

Stage296 and Stage321 pass the metric/flag check.  Stage296 provides the
stronger statistical campaign, but it is historical-source evidence because
hot-code files changed after `60350e3`.  Stage321 is current-hot-code evidence
because no hot SAB/MAT source files changed between `e193b30` and `318e92e`
under the checked source set.

## Consequence

Safe claim: the selected direct-DFT PVW/MAT-SAB mechanism has high-stat
historical support and current-hot-code engineering support with matching
amortized complete-SAB metric.

Unsafe claim: exact current-head paper table with >=10 samples, unless Stage331
reruns current-head performance/noise/resource gates.
