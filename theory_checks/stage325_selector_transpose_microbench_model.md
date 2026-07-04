# Stage325 Selector-Transpose Microbench Model

The coefficient-blocked selector layout changes only physical storage:

```text
current: selector[row][out][re blocks | im blocks]
packed:  selector[coeff block][row][out][re lanes | im lanes]
```

Both layouts execute the same dense r=4 arithmetic:

```text
rows = 5
outputs = 5
complex vector products per coefficient block = 25
```

Therefore Stage325 can only support a locality/resource claim, not a new
algorithmic product-count claim. The complete-SAB projection uses the measured
dense share `0.212353`:

```text
full_speedup = 1 / (1 - dense_share + dense_share / dense_speedup)
```

The Stage324 threshold for a 1% complete-SAB projection is
`1.048905` isolated dense speedup.
