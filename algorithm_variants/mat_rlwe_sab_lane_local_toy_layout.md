# Lane-Local Toy Layout Candidate

## Status

`LAYOUT_FEASIBLE_ARITHMETIC_PROTOTYPE_REQUIRED`

## Representation

The candidate replaces one shared accumulator mask plus r bodies with
lane-local mask/body pairs in the toy representation. It also replaces
dense `(1+r)^2` selector storage with the conservative compact model
`2(1+2r)` selector polynomials.

## Current Limits

- This is not a MOSFHET ciphertext type yet.
- This is not a key generation format yet.
- This does not model noise, key switching, or complete SAB scheduling.
- The next valid step is a toy arithmetic equivalence prototype.
