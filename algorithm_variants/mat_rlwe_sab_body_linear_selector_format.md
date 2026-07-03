# MAT-RLWE SAB Body-Linear Selector Format Candidate

## Status

`DESIGN_OPEN_NEW_FORMAT_REQUIRED`

## Mathematical Definition

The desired body-linear external product must avoid the current
`(k+r)^2` row-output product shape while preserving each lane phase:

```text
phase(body_q(out)) = phase(body_q(reference_dense_out))
```

for every checked lane `q`.

## Required Format Change

A valid candidate must ensure that any mask contribution used for one lane
is either cancelled in every other lane or is not shared with those lanes.
This requires one of:

- lane-local mask accumulations;
- proof-carrying mask partitions;
- another selector/key format with an equivalent phase proof.

## Next Experiment

Before C implementation, build a deterministic r=2 algebraic simulator for
candidate lane-local or proof-carrying formats and compare every lane
against the dense MAT external-product phase.