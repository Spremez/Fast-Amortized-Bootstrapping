# Stage126 Compact Selector Encryption/Noise Gate Plan

Date: 2026-07-03

## Objective

Verify that compact selector rows can be represented as encrypted
lane-local mask/body ciphertexts whose external-product phase equals the
clean gadget reference plus modeled noise. The probe is deterministic for
reproducibility and remains outside `sab_pvw_*`.

## Command

```bash
python scripts/build_stage126_compact_selector_encryption_noise_gate.py
```

## Falsification Criteria

- coefficient-domain encrypted phase is not clean reference plus modeled noise;
- production DFT phase exceeds tolerance;
- modeled noise exceeds the declared bound;
- body-only encrypted selector rows do not fail;
- compact noise-term or selector count advantage disappears.

Passing this stage permits only isolated compact external-product kernel
work outside the SAB hot path.
