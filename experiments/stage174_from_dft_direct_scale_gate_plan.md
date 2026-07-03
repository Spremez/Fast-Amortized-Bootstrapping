# Stage174 Validation Plan

Goal: test one concrete from_DFT locality/SIMD candidate without repeating
Stage163's rejected component-major batching.

Candidate:

```text
SPQLIOS_AVX512_DIRECT_SCALE=true
```

Protocol:

- build baseline and direct-scale probes on CB5 native Linux;
- correctness: each variant equals separate `DFT_to_torus + add`;
- microbench endpoint: `pvmtmlwe_from_DFT_add` call time for r=6;
- promotion threshold: mean speedup >= 1.02 and min/max guard >= 1.0;
- full-SAB A/B is run only if microbench promotes.

Failure handling:

- correctness failure rejects immediately;
- microbench neutral skips full-SAB and records a neutral result;
- full-SAB neutral prevents any bootstrapping-speedup claim.
