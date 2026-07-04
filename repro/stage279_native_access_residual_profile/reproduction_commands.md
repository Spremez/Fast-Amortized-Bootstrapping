# Stage279 Reproduction Commands

```bash
bash scripts/run_stage279_native_access_residual_profile.sh
python3 scripts/build_stage279_native_access_residual_profile.py
```

The native probe uses SSH BatchMode and does not use or store credentials.
Override `NATIVE_HOST` and `NATIVE_USER` as needed.
