# Stage158 Full-SAB Model

Stage157 measured only the local sub+decompose loop. Stage158 evaluates the
same mechanism inside complete SAB:

```text
control: pvmtmlwe_sub(tmp, in2, in1); mat_trgsw_mul_pvmtmlwe_DFT(tmp)
fusion:  mat_trgsw_mul_pvmtmlwe_sub_DFT(in1, in2)
```

The sparse schedule count is unchanged. The only intended savings are reduced
temporary sub memory traffic and direct dense decomposition of the difference.
Therefore any observed full-SAB speedup must be smaller than the isolated
microbench speedup and must be confirmed by repeated runs.
