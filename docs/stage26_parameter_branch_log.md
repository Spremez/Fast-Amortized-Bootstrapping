# Stage 26 Parameter and Branch Generalization Log

Date: 2026-06-25

## Code Change

The PVW target harness is now parameterized by `PARAM=SET_*` for the supported
binary parameter family. Before this change, the `SAB_PVW_TARGET_TEST`,
`SAB_PVW_BENCH`, `SAB_PVW_NOISE_TEST`, `SAB_PVW_STAGE_NOISE_TEST`, and
`SAB_PVW_RESOURCE_TEST` paths all used a hard-coded target:

```text
in_N=2048, out_N=2048, h=39, r_prec=7, msg_prec=3
```

Stage 26 adds `SAB_PVW_Target_Params` and a deterministic sparse-distance
generator so the PVW harness uses the selected binary `SET_*` parameters.
The generated distances split `in_N` into `h+1` bounded gaps, matching the
existing `SET_2_3_2048` pattern of eight `52` gaps and the remaining `51`
gaps.

The PVW target harness now rejects non-binary key modes at compile time:

```text
SAB_PVW target harness currently supports only KEY=BINARY
```

This prevents accidental claims that PVW-SAB supports ternary/include-zero
branches when only the scalar SAB path currently has those semantics.

## Command

```sh
STAGE26_OUT_DIR=repro/stage26_parameter_branch_smoke_avx512 \
bash scripts/run_stage26_parameter_target_smoke.sh
```

Backend and flags:

```text
FFT_LIB=spqlios_avx512
MAT_TRGSW_AVX512_SMALLR_SPECIALIZED=true
SAB_PVW_ACTIVE_BUFFER_FUSION=true
```

## Binary Parameter Smoke

| param | key | r | h | r_prec | status |
|---|---|---:|---:|---:|---|
| `SET_2_3_2048` | `BINARY` | 2 | 39 | 7 | Pass |
| `SET_4_5_2048` | `BINARY` | 2 | 42 | 7 | Pass |
| `SET_2_3_4096` | `BINARY` | 2 | 32 | 8 | Pass |

Interpretation:

- The parameterized harness preserves the original target gate.
- The current PVW binary path can pass correctness smoke under a second
  `N=2048` parameter with different `h` and message precision.
- The path also passes a larger input parameter with `in_N=4096` and
  `r_prec=8`.

## Branch Scope

| param | key | mode | status |
|---|---|---|---|
| `SET_2_3_2048` | `TERNARY` | PVW target | Expected unsupported |
| `SET_2_3_2048` | `TERNARY` | scalar build | Pass |

Interpretation:

- Scalar SAB ternary support is not removed.
- PVW-SAB ternary support is not implemented and must not be claimed.
- Ternary/include-zero PVW support requires a separate design for selector
  sign/coefficient handling in `sab_pvw_*`.

## Decision

Status:

```text
PASS_SMOKE_BINARY_PARAMETERS
NON_BINARY_PVW_UNSUPPORTED
```

Stage 26 now has initial binary parameter generalization evidence. This is not
yet a broad SAB claim because:

- only three binary parameter choices were checked;
- the added parameters have correctness smoke only, not 50-seed noise or
  repeated full SAB performance;
- non-binary PVW-SAB is explicitly unsupported.

## Next Work

1. Add performance/noise sweeps for the additional binary parameters only if
   they remain part of the final claim.
2. Decide whether ternary/include-zero PVW support is in scope; if yes, design
   a separate `sab_pvw_*` key format for sign/coefficient selectors.
3. Move to Stage 27 only after the final claimed parameter set is fixed.
