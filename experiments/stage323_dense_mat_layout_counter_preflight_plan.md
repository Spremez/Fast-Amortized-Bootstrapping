# Stage323 Dense MAT Layout Counter Preflight Plan

Input decision: `PASS_STAGE322_PROFILE_SELECT_DENSE_MAT_LAYOUT_COUNTER_PREFLIGHT`.

Goal: determine whether dense MAT addmul has a real memory/FMA/register
mechanism left after the current direct baseline and Stage321 r4-unrolled
neutral result.

Tasks:

- isolate dense MAT addmul under r=4, N=2048, Bg_bit=23;
- compare current layout against row-major/body-major/coefficient-blocked
  access models only if counters or microbench justify it;
- record load/store/FMA/cache/retired-instruction evidence when native counters
  are available;
- do not edit full SAB until a preflight projects at least 1% complete-SAB
  `T_bootstrap/r` movement.

Failure handling: if counters/microbench do not show a material mechanism,
close dense MAT layout and return to higher-level SAB schedule redesign.
