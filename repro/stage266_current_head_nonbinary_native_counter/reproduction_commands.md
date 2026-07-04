# Stage266 Reproduction Commands

Handoff only:

```bash
python3 scripts/build_stage266_current_head_nonbinary_native_counter.py
```

Remote native execution, with a runtime-only secret:

```bash
STAGE266_REMOTE_SECRET=<runtime-only> python3 scripts/build_stage266_current_head_nonbinary_native_counter.py
```

No secret is written to repository artifacts.
