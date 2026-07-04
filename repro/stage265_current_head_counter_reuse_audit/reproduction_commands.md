# Stage265 Reproduction Commands

```bash
python3 scripts/build_stage265_current_head_counter_reuse_audit.py
git diff --name-status 0888285..HEAD -- main.c Makefile include src
git diff --name-status 0888285..HEAD -- src/mosfhet/src/mattrgsw.c
```

Decision: `PASS_STAGE265_CURRENT_HEAD_COUNTER_REUSE_AUDIT_REFRESH_REQUIRED`.
