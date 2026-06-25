# Stage 39 Optional Algorithmic Variant Triage Plan

Date: 2026-06-26

## Goal

Decide whether a new PVW/MAT-SAB algorithmic variant should be implemented
after the promoted active-buffer MAT-SAB path, without destabilizing the scalar
baseline or retesting neutral directions without new evidence.

Stage 39 is a gate before new algorithmic work. It is not itself a speedup
claim.

## Command

```bash
python3 scripts/build_stage39_variant_triage.py
```

## Candidate Classes

- non-binary PVW-SAB branch support;
- deeper sparse-schedule fusion beyond the neutral Stage 23 result;
- MAT key/layout experiments for r=4 dense-matrix pressure;
- direct post-processing/extract/packing KS work;
- AVX512 r-specific kernels backed by native counters.

## Gate

A candidate may move from triage to implementation only if:

- it has a concrete bottleneck or scope requirement;
- the scalar SAB path remains unchanged;
- implementation is behind an explicit flag or new `sab_pvw_*` path;
- correctness, full-SAB performance, noise, and resource gates are pre-defined;
- prior neutral/blocked evidence is addressed instead of ignored.

## Failure Handling

- If the candidate is blocked by full text or native perf counters, keep it
  blocked and do not implement speculative code.
- If prior evidence says the tail or schedule cost is too small, defer until a
  new profile changes the cost model.
- If a variant only supports a broader claim the user has not selected, keep it
  optional.

## Artifacts

- `repro/stage39_variant_triage.csv`
- `docs/stage39_variant_triage_log.md`
