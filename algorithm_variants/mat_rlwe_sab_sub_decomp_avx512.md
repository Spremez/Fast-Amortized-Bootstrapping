# AVX512 Sub-Decompose Variant

Production flag: `MAT_TRGSW_AVX512_SUB_DECOMP=true`.

The variant replaces the scalar coefficient loop in `mat_trgsw_sub_decompose`
with AVX512 integer subtract/add/variable-shift/mask/subtract/store operations.
It is default-off and leaves scalar/default SAB unchanged.
