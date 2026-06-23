# Theory Check: PVW/MAT-SAB Complexity Model

Date: 2026-06-23

## Baseline

For binary 2025/686 SAB at `SET_2_3_2048`:

```text
N = 2048
h = 39
rho = r_prec = 7
k = 1
l = 1
M = (h + 1) * rho * N = 573440
```

Repeated scalar `r`-lane cost:

```text
T_scalar(r) =
  r * (T_setup + M*C_ext_scalar + T_extract + T_packing + T_hwks)
```

Current PVW/MAT-SAB cost:

```text
T_pvw_current(r) =
  T_setup_pvw
  + M*C_ext_mat(k,l,r)
  + T_extract_pvw
  + r*(T_materialize + T_packing + T_hwks)
```

The current implementation improves the blind-rotation external-product term,
but retains an O(r) post-processing tail.

## MAT External Product Count Model

For `k=1,l=1`:

```text
scalar decomposition/DFT rows = 2r
MAT decomposition/DFT rows    = 1+r

scalar DFT mul/add = 4r
MAT DFT mul/add    = (1+r)^2
```

Therefore MAT wins only when:

```text
savings(decomposition + DFT conversion)
>
extra dense DFT mul/add
```

This explains the observed behavior:

- `r=1`: no stable advantage;
- `r=2`: MAT is useful;
- `r=4`: MAT is useful but dense addmul is already the dominant risk;
- larger `r`: likely loses without a sparse/fused kernel or post-processing
  changes.

## Multi-X Improvement Conditions

A multi-fold full SAB speedup over scalar baseline requires more than the
current MAT substitution.

Necessary conditions:

1. Reduce `C_ext_mat(k,l,r)` below the generic dense `(k+r)^2` behavior.
2. Avoid `r*(T_packing + T_hwks)` post-processing growth.
3. Keep key size and memory overhead close to repeated scalar or explain the
   tradeoff.
4. Preserve lane phase equivalence and noise gates.

The first r-specialized AVX512 variant did not satisfy condition 1 strongly
enough. The next theory target is either a truly hand-unrolled small-r kernel
or a SAB-specific sparse MAT selector formulation.
