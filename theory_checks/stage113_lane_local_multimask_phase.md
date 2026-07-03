# Stage113 Lane-Local Multimask Phase Check

Date: 2026-07-03

The r=2 simulator separates phase validity from implementation cost.
The lane-local multimask candidate changes the ciphertext shape so that
a row used for lane 0 does not contribute to lane 1's mask. Under that
changed invariant, off-lane body rows can be skipped in the toy model.

This does not prove a full SAB optimization. It only proves that one
new-format direction is phase-plausible enough to justify a resource
model and a toy C representation gate.