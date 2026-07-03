# Closed Full-MAT Row-Streaming Candidate

This candidate preserves the PVW_TMLWE shared-mask state and dense MAT selector
semantics. It does not reduce the SAB schedule count or `from_DFT` count.

Implementation tested:

```text
for each decomposed row:
    compute decompose(in2 - in1)[row]
    torus_to_DFT(row)
    addmul row into output DFT
```

Decision: `REJECT_STAGE165_STREAMING_LOSES_TO_CURRENT_TILED_AVX`.

The result is microbench-only. A positive result would still require a guarded
production path and complete SAB `T_bootstrap/r` A/B.
