# Stage317 IFFT Batch5 Static Model

For r=4 and k=1, MAT direct sub-DTF has rows=k+r=5.  A single tile containing
all five rows is rejected because the offloop needs

```text
2 shared trig zmm + 5 * 8 per-row zmm = 42
```

live vector registers, exceeding the 32 zmm registers available in
AVX512.  The admitted skeleton is `tile3 + tile2`:

```text
2 + 3 * 8 = 26
2 + 2 * 8 = 18
```

The static memory model is not a performance result.  It only shows why the
candidate is measurable: in the trig-loading nnloop, five single-row calls use
50 vector memory operations per abstract butterfly group, while tile3+tile2
uses 44, a 0.120000 static reduction.  Stage318 must measure
whether this reaches the 0.107769 required IFFT component reduction
from Stage315.
