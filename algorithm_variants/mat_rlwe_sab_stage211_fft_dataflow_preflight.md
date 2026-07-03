# MAT-RLWE SAB Stage211 FFT/DFT Dataflow Variant

Stage211 defines no new production variant. It is a code-admission checkpoint
for the current MAT-RLWE/r-body SAB implementation.

Allowed next variant:

```text
stage212_multirow_fft_backend_api_probe
```

This future probe may introduce a standalone reverse-DFT API and compare it
against the current single-row path. It must pass bit/equivalence tests and a
microbench before any `sab_pvw_*` integration.

Denied now:

- reopening same-format DFT batching;
- reopening batched decompose-to-DFT;
- direct lazy DFT accumulator integration;
- production SAB hot-path edits without a new primitive.
