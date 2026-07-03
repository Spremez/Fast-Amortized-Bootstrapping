# Stage202 Dummy Padding Semantic Model

Stage201 found that random-looking dummy rows can preserve simple public
patterns only if dense public shape is retained. Stage202 tests whether those
dummy rows can be semantically harmless in a finite model.

The toy model uses m=r+1 input components and a count-matched active set of 4r
semantic rows. Inactive dummy rows are tested in two ways:

- semantic zero: should match the structured reference;
- random semantics: should fail as a negative control.

This proves only a toy semantic condition. A production route still needs real
selector equations, keygen/security proof, noise recurrence, and complete-SAB
T_bootstrap/r evidence.
