# MAT-RLWE SAB Stage259 Non-Binary Full SAB

Stage259 lifts the Stage257/258 non-binary sparse_mul route to an explicit full
SAB API:

```text
sab_pvw_new_nonbinary_full_key
sab_pvw_blind_rotate_nonbinary
sab_pvw_bootstrap_wo_extract_nonbinary
sab_pvw_bootstrap_nonbinary
```

The core algorithmic delta from binary PVW/MAT-SAB is localized to
`blind_rotate_nonbinary`, which calls `sparse_mul_nonbinary`; extraction,
packing key switching, and HW key switching reuse the same lane-wise
post-processing as the binary PVW path.

Stage259 gate: `PASS_STAGE259_NONBINARY_FULL_SAB_SMOKE`.
