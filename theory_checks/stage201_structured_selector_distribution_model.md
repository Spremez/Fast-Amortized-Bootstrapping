# Stage201 Structured Selector Distribution Model

The compact/shared-output route needs a declared selector distribution. Stage190
already rejects row deletion, deterministic zero rows, and forced shared masks
as standard dense-distribution shortcuts. Stage201 repeats the idea with a
candidate that pads omitted rows with random-looking dummy rows.

Result:

- deleted rows, zero padding, and forced shared masks remain publicly
  distinguishable in the finite probe;
- random dummy padding passes only simple public-pattern tests;
- dummy padding keeps dense public row count, so key-size savings are not
  demonstrated;
- semantic correctness and noise/keygen proof remain blocked.
