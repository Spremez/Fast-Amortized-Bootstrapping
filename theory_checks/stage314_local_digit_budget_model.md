# Stage314 Local Digit Budget Model

Stage314 applies an Amdahl-style budget to the measured Stage313 profile. The
direct digit component is 0.172510 of the profiled body time.
The observed narrow32 digit speedup is 1.044719, which
projects to only 1.007439 body-level speedup
before considering schedule variance and unchanged IFFT/dense costs.

Therefore local digit microvariants are closed unless a future candidate has a
pre-implementation full-SAB budget of at least 1.02x and then passes complete
`T_bootstrap/r` A/B. Larger opportunities now require backend IFFT work or a
SAB schedule-level reduction in call/materialization count.
