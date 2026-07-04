# Stage248 Structured Compact Finite Model

Stage248 models only one algebraic condition:

```text
M[body0, body1] = 0 and M[body1, body0] = 0
```

Under this condition, omitting the two off-lane body-to-body terms is exact in
the finite state model. This is a necessary condition for a compact route, not
a sufficient condition for SAB.

The following remain open:

- whether the constrained selector distribution is secure or publicly hidden;
- whether dummy semantic-zero padding can hide the pattern without losing value;
- whether ring-level SAB rotations and CMUX preserve the same noise recurrence;
- whether complete-SAB `T_bootstrap/r` improves after implementation.
