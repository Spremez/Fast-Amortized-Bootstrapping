# Theory Check: MAT-Aware AVX512 Memory Model

Date: 2026-06-25

## Question

Does a MAT-aware AVX512 external product have a theoretical advantage over
reusing a single-polynomial AVX kernel for each output, and has the current
implementation reached that advantage?

## Scope

This note covers the current SAB target shape:

```text
k = 1
l = 1
r in {2,4}
m = k + r = 1 + r
FFT backend = spqlios_avx512
```

It does not claim a general optimum for arbitrary `k`, `l`, `r`, or backend.

## Arithmetic Count

Repeated scalar external products use `2` TRLWE components per scalar body and
are repeated for `r` independent SAB lanes. The simplified dense count for
`k=1,l=1` is:

```text
repeated scalar complex products ~= 4r
MAT complex products             =  (1 + r)^2
```

Therefore:

| r | repeated scalar products | dense MAT products | dense MAT / scalar |
|---:|---:|---:|---:|
| 1 | 4 | 4 | 1.000 |
| 2 | 8 | 9 | 1.125 |
| 4 | 16 | 25 | 1.5625 |

The MAT path is not arithmetically cheaper at r=4. Its potential advantage must
come from shared decomposition, fewer repeated loads/stores, better locality,
and reduced output conversion overhead.

## Memory-Traffic Model

Let `m = 1 + r`. For one AVX512 complex coefficient block, a generic
single-polynomial style MAT loop tends to:

```text
for row in m:
  for output in m:
    load decomposed row
    load selector row/output
    load output accumulator except for initialization
    store output accumulator
```

A coarse vector memory-operation model is:

```text
generic dec loads       ~= 2m^2
generic selector loads  ~= 2m^2
generic output stores   ~= 2m^2
generic output loads    ~= 2m(m - 1)
generic total           ~= 8m^2 - 2m
```

A MAT-aware register-accumulation loop can instead:

```text
for coeff block:
  keep output accumulators in AVX512 registers
  load each decomposed row once
  stream selector rows
  store each output once
```

Coarse model:

```text
MAT-aware dec loads      ~= 2m
MAT-aware selector loads ~= 2m^2
MAT-aware output stores  ~= 2m
MAT-aware output loads   ~= 0
MAT-aware total          ~= 2m^2 + 4m
```

Predicted memory-operation reduction:

| r | m | generic vector ops | MAT-aware vector ops | reduction |
|---:|---:|---:|---:|---:|
| 2 | 3 | 66 | 30 | `2.20x` fewer |
| 4 | 5 | 190 | 70 | `2.71x` fewer |

This supports the intuition that MAT-aware AVX can improve load/write behavior.
It does not imply r-fold full-SAB speedup because arithmetic count, register
pressure, inverse DFT/output conversion, CMUX wrapper work, and SAB schedule
traffic remain.

## Register Pressure

At r=2:

```text
m = 3 outputs
```

Three complex output accumulators can plausibly remain register-resident while
streaming selector rows. This is the strongest case for a small-r specialized
kernel.

At r=4:

```text
m = 5 outputs
```

Five complex outputs require more AVX512 registers, more pointer state, and
more live selector data. Dense MAT also performs `25` complex products versus
`16` repeated scalar products. This can cap the benefit from reduced stores and
loads.

## Current Evidence

Stage 15 repeated microbench evidence under `spqlios_avx512`:

| benchmark | r | scalar repeated us | MAT us | speedup |
|---|---:|---:|---:|---:|
| DFT output | 2 | 12.864 | 9.373 | `1.380x` |
| DFT output | 4 | 28.107 | 22.130 | `1.267x` |
| full output | 2 | 22.660 | 16.031 | `1.416x` |
| full output | 4 | 49.980 | 34.006 | `1.471x` |

Stage 16 full-SAB evidence under `spqlios_avx512`:

| r | full SAB mean speedup | status |
|---:|---:|---|
| 2 | `1.197x` | positive, explicit flag |
| 4 | `1.281x` | positive, explicit flag |

Interpretation:

```text
The current MAT-aware AVX512 implementation captures a real load/store and
output-conversion benefit. It has not been proven theoretically optimal because
no perf-counter-backed comparison has yet shown that the remaining gap is only
dense MAT arithmetic or unavoidable register pressure.
```

## Required Next Checks

Stage 22 must answer the remaining questions:

- generic single-poly AVX path versus MAT-aware AVX path under the same binary;
- retired load/store and FMA evidence where hardware counters are available;
- assembly audit for expected AVX512 FMA instructions and absence of avoidable
  output load/store cycles;
- r=2 register-resident and r=4 lower-pressure tiling comparison;
- full SAB A/B check for any kernel-level win.

## Decision Boundary

Allowed current claim:

```text
MAT-aware AVX512 is theoretically motivated by reduced vector memory traffic
and is experimentally positive at the scoped kernel and complete-SAB levels.
```

Not yet allowed:

```text
The MAT AVX512 path has reached the theoretical optimum.
The AVX512 MAT kernel alone proves multi-fold complete SAB acceleration.
The r=4 dense MAT arithmetic overhead is fully solved.
```
