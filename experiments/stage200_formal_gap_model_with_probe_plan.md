# Stage200 Plan

Goal: improve the R3 formal-gap requirement from Stage199 without entering a
theory loop.

Method:

- state assumptions for the current exact same-format full-MAT path;
- record count lower bounds for input DFT conversions and dense addmul terms;
- run finite probes for component omission and toy decomposition nonlinearity;
- convert rejected shortcuts into proof obligations and next gates.

Failure rule:

- if the finite probes do not find mismatches, the shortcut rejection cannot be
  used;
- if a claim exceeds the assumptions, it must be moved to proof obligations.
