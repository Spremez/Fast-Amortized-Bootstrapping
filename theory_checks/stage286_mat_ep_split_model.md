# Stage286 MAT EP Split Model

## Object

The selected Stage284 candidate uses the exact dense MAT external product path
inside `mat_trgsw_mul_pvmtmlwe_sub_DFT` for CMUX diff inputs. For the target
r=4, k=1, l=1 setting:

```text
rows = outputs = r + 1 = 5
dense complex products per AVX512 block = rows * outputs = 25
schedule MAT EP calls = 573440
```

The current MAT EP timer includes:

1. diff/sub decomposition over `5` torus polynomials;
2. `5` torus-to-DFT conversions;
3. dense exact MAT multiply/addmul across `25` row/output
   pairs;
4. output stores for `5` DFT polynomials.

## Promotion Boundary

The split model is a planning and admission model. A behavior-changing kernel
optimization is not admitted until a later stage either records native
hardware counters or adds optional split instrumentation that identifies a
specific subcomponent and then passes repeated complete-SAB `T_bootstrap/r`.
