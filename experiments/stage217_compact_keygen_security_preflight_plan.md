# Stage217 Plan

Goal: turn the compact selector route into executable keygen/security admission
checks without entering SAB hot-path code.

Gates:

- required Stage201/202/203/216 inputs exist;
- public-pattern negative controls are rejected;
- count-matched random dummy padding is only pattern-only evidence;
- equation/resource value is recorded but not upgraded to implementation
  permission;
- next work is isolated key-object/noise prototype or fail closed.
