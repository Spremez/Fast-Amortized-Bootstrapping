# r=2 Lane-Local Multimask MAT-SAB Candidate

## Status

`PHASE_PLAUSIBLE_RESOURCE_MODEL_REQUIRED`

## Definition

Replace the single shared output mask in the algebraic model with
lane-local mask accumulations. Lane `q` only accumulates mask/body rows
that are required for its own phase.

## Delta From Current PVW_TMLWE

Current PVW_TMLWE uses one shared mask vector and r bodies. This candidate
uses lane-local masks, so it is not a drop-in replacement for the current
`MAT_TRGSW_DFT` hot path.

## Required Next Evidence

- key-size/ciphertext-size model;
- noise model for lane-local masks;
- r=2 toy C representation and dense-reference equivalence;
- only then a complete-SAB performance gate.