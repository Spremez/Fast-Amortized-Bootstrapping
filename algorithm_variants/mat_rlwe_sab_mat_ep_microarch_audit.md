# MAT EP Microarchitecture Audit Variant

Selected route: split-probe only.

Current facts:

- MAT-aware AVX512 tiled r>4 kernel exists.
- r=6 fulltile/bodymajor variants exist and have negative/neutral complete-SAB
  evidence.
- row streaming lost to the current tiled path.
- compact integration remains blocked.

Next valid implementation candidate, if any, must come from a measured
subcomponent split inside `mat_trgsw_mul_pvmtmlwe_sub_DFT`.
