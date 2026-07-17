# Candidate A Star-Cycle Gate Registration

- Field: prime 257
- Lane counts: r=2, r=4, r=6
- Selector semantics: mu=0 and mu=1
- Secrets: deterministic nonzero vectors registered in the gate source
- Positive control: unrestricted dense support
- Negative control: generic dense kernel randomizer outside star support
- Omitted-term oracle: mask-input body removal is inconsistent; body-column
  mask-row and cycle-predecessor removals are consistent; body-column diagonal removal is consistent for r=2 and inconsistent for r=4/6
- Negative-control gate: every observed outcome must equal its registered oracle
- Primary gate: at least one kernel-randomization degree per input column
- Failure action: reject the direct sparse standard-PVW route and activate B
- C hot-path changes: prohibited
