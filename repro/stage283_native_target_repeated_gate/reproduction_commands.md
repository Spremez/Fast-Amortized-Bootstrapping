# Stage283 Reproduction Commands

Key-based SSH path:

```bash
python3 scripts/build_stage283_native_target_repeated_gate.py
```

Environment-auth path:

```bash
STAGE283_REMOTE_AUTH='<provided out of band>' python3 scripts/build_stage283_native_target_repeated_gate.py
```

No credential is stored in repository artifacts. The target directory is
`/home/delld/spz/Fast-Amortized-Bootstrapping-stage283-4bd3d04` and the primary endpoint is native `T_bootstrap/r`.
