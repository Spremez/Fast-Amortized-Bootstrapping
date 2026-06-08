# Stage 3 PVW/Matrix Kernel Status

Date: 2026-06-08

## Implemented

- Added MOSFHET-native `MAT_TRGSW` allocation, key wrapper, monomial
  encryption, DFT conversion, and external product in
  `src/mosfhet/src/mattrgsw.c`.
- Added `MAT_TRGSW_MUL_SCRATCH` so `mat_trgsw_mul_pvmtmlwe_DFT(...)` does not
  allocate temporary polynomials on the hot path.
- Added `free_pvmtmlwe_DFT(...)`; `PVW_TMLWE` and `PVW_TMLWE_DFT` have
  different `k/r` field order, so using `free_pvmtmlwe(...)` on DFT samples is
  incorrect when `r > 1`.
- Added `SAB_PVW_KERNEL_TEST=true`, which automatically enables the PVW TMLWE
  sources and runs a standalone matrix-kernel identity test.
- Fixed Windows-incorrect `1UL << high_bit` shifts to `1ULL << high_bit` in
  torus rounding, decomposition, key switching, and bootstrapping helpers.

## Current Semantics

The matrix selector has `(k + r) * l` rows:

- rows `[0, k*l)`: mask gadget rows.
- rows `[k*l, (k+r)*l)`: one body gadget block per lane.

This matches the selected project-level interpretation:

```text
r = number of independent LUT/SAB lanes sharing the same control/key flow
```

## Verification

Windows portable correctness smoke:

```powershell
make FFT_LIB=ffnt ARCH_FLAGS= ENABLE_PVW_TMLWE=true SAB_PVW_KERNEL_TEST=true
.\main.exe
```

Result:

```text
MAT_TRGSW kernel test: Pass
```

Windows default SAB smoke:

```powershell
make FFT_LIB=ffnt ARCH_FLAGS=
.\main.exe
```

Result:

```text
Bootstrapping time: 46,402,617us +- 192907.864434
Pass
```

WSL/Linux spqlios kernel smoke:

```bash
make FFT_LIB=spqlios ENABLE_PVW_TMLWE=true SAB_PVW_KERNEL_TEST=true
./main
```

Result:

```text
MAT_TRGSW kernel test: Pass
```

Updated WSL/Linux spqlios kernel smoke after scalar-equivalence and microbench
were added:

```bash
make FFT_LIB=spqlios ENABLE_PVW_TMLWE=true SAB_PVW_KERNEL_TEST=true
./main
```

Result:

```text
MAT_TRGSW kernel test: Pass
MAT_TRGSW microbench r=1 reps=1000 avg_us=11 lane_avg_us=11
MAT_TRGSW microbench r=2 reps=1000 avg_us=23 lane_avg_us=11
MAT_TRGSW microbench r=4 reps=1000 avg_us=40 lane_avg_us=10
```

WSL/Linux spqlios default SAB smoke:

```bash
make FFT_LIB=spqlios
./main
```

Result:

```text
Bootstrapping time: 14,979,850us +- 265187.920517
Pass
```

Updated default SAB smoke after the Stage 3 test additions:

```text
Bootstrapping time: 13,751,139us +- 88946.746622
Pass
```

The WSL command output also includes host-side localhost/NAT warning text before
or after program output; it is not emitted by this program and did not affect
the exit code.

## Remaining Stage 3 Work

- Improve the microbench report to collect multiple trials and expose median,
  min, max, and standard deviation.
- Add a scalar baseline microbench in the same standalone target so the raw
  `r=1` MAT_TRGSW cost can be compared directly with `trgsw_mul_trlwe_DFT(...)`
  in the same process.
- Keep `pvmtmlwe_keyswitch(...)` as a known aborting stub; the current matrix
  external product path does not call it.

## Stage 4/5 Entry Condition

The project can now start Stage 4 state design and isolated CMUX/NCMUX lane
tests, but should not replace scalar SAB yet. The next change should add PVW
lane state beside the existing SAB state and compare scalar vs PVW lane phase
after each isolated CMUX step.
