# Stage323 Dense MAT Static Load Model

For the target r=4, k=1, l=1 dense MAT external product:

```text
rows = r + 1 = 5
outputs = k + r = 5
vector blocks = N / 16 = 128
complex vector products per block = rows * outputs = 25
```

The current r=4 AVX512 loop is already MAT-aware:

- each decomposed DFT row is loaded once per coefficient block;
- that row is reused across all five outputs;
- all five outputs are accumulated in registers;
- each output is stored once after all rows are processed.

Therefore a local loop rewrite cannot reduce decomposed-row loads or output
stores. It must either reduce selector loads, reduce dense product count, or
change key/selector layout. Those are not local exact-loop edits and require
key-format/resource/noise gates.
