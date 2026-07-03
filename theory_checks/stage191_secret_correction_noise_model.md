# Stage191 Secret-Correction Noise Model

After Stage189, direct public collapse from lane-local masks `a_q` to one
shared mask `a*` is rejected. The algebraically possible repair is:

```text
b'_q = b_q + (a* - a_q) * s_q
```

or an equivalent key-switch/re-share. This changes the T4 problem:

1. The correction is secret-dependent and cannot be a public arithmetic update.
2. An evaluation/key-switch mechanism must contribute latency, key material,
   and noise.
3. Repeating this after every CMUX/NCMUX in the SAB schedule adds a new noise
   recurrence.

With normalized baseline step standard deviation `sigma_0` and correction
standard deviation `sigma_c = rho * sigma_0`, the per-step standard deviation
multiplier is bounded below by:

```text
sqrt(1 + (r - 1) * rho^2)
```

for the minimal choice of one existing lane mask as `a*` and correcting the
remaining `r-1` lanes. This model is a sensitivity screen; a real T4 proof
would need concrete key-switch parameters and multi-seed failure/noise
measurements.
