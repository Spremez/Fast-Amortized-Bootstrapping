# Stage109 Body-Linear MAT External Product Check

Date: 2026-07-03

## Result

`PASS_STAGE109_BODY_LINEAR_BLOCKED_CURRENT_SELECTOR_FORMAT`

For k=1,l=1, the current MAT external product has `(r+1)^2` encrypted
row-output polynomial products. A body-linear target would need a product
shape closer to `O(r)`, but the present key format does not expose a safe
way to omit off-lane encrypted-zero components.

The important distinction is:

- plaintext gadget injection is diagonal;
- ciphertext carrier rows are still full PVW_TMLWE encryptions;
- PVW phase uses the shared mask against every body secret column;
- omitting off-lane body ciphertexts changes the zero-encryption relation.

Therefore V106-B is not rejected as an algorithmic idea, but it is blocked
as a local loop-only optimization. It requires a new selector/key-format
design gate with a correctness proof before implementation.