# MAT-RLWE SAB Lazy DFT State Variant

Variant tested:

```text
Keep each PVW/MAT-SAB accumulator in DFT form across CMUX/RGSW steps, hoping to
avoid per-update materialization.
```

Stage156 decision:

```text
REJECT naive DFT-only state.
```

Reason:

- production MAT EP requires torus input and decomposes inside the EP;
- no current EP API accepts a DFT/decomposed accumulator input;
- gadget decomposition is not linear under addition, subtraction, negation, or
  negacyclic sign rotations.

Allowed successor variants:

- exact torus plus decomposition cache;
- compact/shared-source representation with proven closure;
- native-counter analysis to decide whether implementation work should target
  materialization, decomposition, or dense addmul.
