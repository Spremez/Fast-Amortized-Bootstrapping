# Stage181 Plan

Goal: test the default-off AVX512 integer sub-decompose candidate without
changing scalar/default behavior.

Gates:

- baseline and AVX512 sinks must match;
- sub-decompose and combined-current timings must be recorded;
- full-SAB promotion requires projected complete-SAB gain, not local speedup
  alone.
