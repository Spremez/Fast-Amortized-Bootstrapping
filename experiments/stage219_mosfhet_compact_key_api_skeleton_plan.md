# Stage219 Plan

Goal: compile-check a MOSFHET-adjacent compact key API skeleton after the
Stage218 finite key-object/noise prototype.

Gates:

- current MOSFHET static library builds;
- generated C probe compiles and runs;
- DFT row ownership is non-aliased;
- row roles match Stage203 equations and Stage218 counts;
- invalid guard checks pass;
- hot role scan uses no skeleton allocation;
- no SAB hot-path code is authorized.
