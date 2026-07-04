# Stage278 Reproduction Commands

Local larger-stat evidence:

```bash
bash scripts/run_stage278_include_zero_fast_local_larger_stats.sh
python3 scripts/build_stage278_native_larger_stats_include_zero_fast.py
```

Native handoff without storing credentials:

```bash
NATIVE_HOST=<host> NATIVE_USER=<user> NATIVE_WORKDIR=<repo-path> \
  bash scripts/run_stage278_native_include_zero_fast_handoff.sh
python3 scripts/build_stage278_native_larger_stats_include_zero_fast.py
```

The native handoff uses `ssh -o BatchMode=yes`; configure key-based auth or run
the local runner directly on the native host. Do not place credentials in logs
or scripts.
