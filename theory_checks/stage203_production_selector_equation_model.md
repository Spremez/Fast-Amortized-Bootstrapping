# Stage203 Production-Shaped Selector Equation Model

The declared equation candidate uses four active equation classes per body lane:

- mask output from body input;
- body output from mask input;
- lane self-body interaction;
- lane neighbor-body interaction.

All other dense public rows are dummy-zero equations. Finite phase tests check
that dense-shape evaluation with dummy-zero rows equals active-row skipping.
Negative controls require random dummy semantics and missing active equations
to fail. Passing these tests does not prove security or production correctness.
