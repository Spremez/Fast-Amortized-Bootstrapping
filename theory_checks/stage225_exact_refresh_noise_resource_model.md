# Stage225 Exact Refresh Noise/Resource Model

Stage225 does not change the latency numerator. It supplies side conditions for
the Stage224 exact PVW/MAT full-SAB performance refresh:

```text
correctness: final-output failures must remain 0
noise: pvw_minus_scalar_log2 must stay within configured bound
resource: key-size and RSS ratios must be reported with any T_bootstrap/r claim
```

This is still an exact dense MAT/PVW engineering path, not a compact complete-SAB
or theoretical-optimality proof.
