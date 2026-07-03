# Exact DFT/Conversion Preflight Candidate

This is a preflight card, not an implementation.

Rejected local candidates:

- same-format materialization-count reduction;
- component-major from_DFT batching;
- direct-scale/fused-add variants;
- batched decompose-to-DFT;
- naive lazy-DFT accumulator.

Open only externally:

- a new backend torus_to_DFT/from_DFT primitive with exact equivalence and
  measured component speedup above the Stage180 threshold.

Next route: scoped paper/repro refresh.
