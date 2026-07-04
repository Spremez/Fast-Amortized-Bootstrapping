# Stage237 Manuscript Claim Model

The current algorithm object is exact dense PVW/MAT-SAB: an r-body MAT-RLWE
accumulator with one shared mask and r independent body lanes. The scalar
baseline repeats SAB r times. The primary metric is:

```text
speedup = T_scalar_repeated(r lanes) / T_pvw_mat_sab(r body lanes)
lane_time = T_bootstrap / r
```

The selected binary matrix supports scoped empirical throughput claims. It does
not prove a formal lower-bound-tight construction. The present lower-bound
model is practical: output extraction/key switching, encrypted selector
semantics, dense MAT external-product arithmetic, and backend DFT conversion
remain unavoidable or unproven under the current implementation.

Candidate optimal paths are therefore gated separately: exact dense PVW/MAT-SAB
is the promoted empirical route; native counters can refine attribution;
compact/sparse selector MAT requires new security/noise/equation proofs;
non-binary branches need branch-specific full-SAB gates; theoretical optimality
requires a separate theorem.
