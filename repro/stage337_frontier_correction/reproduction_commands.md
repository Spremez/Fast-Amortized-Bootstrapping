# Stage337 Reproduction Commands

```powershell
python scripts\build_stage337_frontier_correction.py
```

Stage337 is an evidence-correction gate. It intentionally performs no hot-path
code changes because every concrete exact candidate in scope already has a
negative or neutral gate.
