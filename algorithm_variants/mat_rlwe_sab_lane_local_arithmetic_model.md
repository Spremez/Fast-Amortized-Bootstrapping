# Lane-Local Arithmetic Model

## Status

`TOY_ARITHMETIC_EQUIV_SELECTOR_PROTOTYPE_REQUIRED`

## Invariant

For each lane q, dense reference evaluates every row but off-lane body
messages are zero. Lane-local arithmetic is allowed to skip off-lane rows
only because the mask relation is changed to be lane-local.

## Boundary

This model does not define MOSFHET allocation, encryption, noise, key
switching, DFT layout, or AVX512 code. It is a finite arithmetic screen
for the next selector/key-format prototype.
