# Stage323 Reproduction Commands

```bash
python3 scripts/build_stage323_dense_mat_counter_preflight.py
```

If native Linux `perf` is available, rerun on that platform to upgrade the
counter row from proxy-only to measured. Without counters, Stage323 remains a
static/source preflight and cannot admit new exact dense loop code.
