# Stage254 Non-Binary Keygen/Noise Preflight Model

The non-binary selector families use the same 0/1 MAT monomial selector shape
as binary distance bits, but are consumed in `sub_a` rather than CMUX
butterfly layers.

For one non-binary family, the extra external-product-class count is:

```text
h * in_N
```

The binary main CMUX external-product-class count is:

```text
(h + 1) * r_prec * in_N
```

The target ratio is therefore `h / ((h + 1) r_prec) = 39/(40*7)`.
Noise is not derived by this count model and must be measured or bounded in
the next stage.
