# Stage190 Selector Distribution Model

The current dense MAT_TRGSW selector uses public rows shaped as full PVW_TMLWE
encryptions. Compact/shared-output candidates try to reduce rows or force
relations that would help Stage189's shared-mask closure problem.

Three shortcuts are publicly distinguishable:

1. Deleting rows changes the public key size.
2. Replacing rows with deterministic zeros creates a zero-mask relation.
3. Forcing equal/shared masks creates equality relations across rows.

Therefore these shortcuts cannot be called standard dense-key distribution
equivalent. A future compact selector must be introduced as a new structured
public key distribution with an explicit assumption or reduction and a leakage
analysis.
