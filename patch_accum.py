"""Add spectral-accumulation test to probe_layer.c via line-based edit."""
PATH = r"D:\codexprograms\whFast-Amortized-Bootstrapping\Fast-Amortized-Bootstrapping\src\probe_layer.c"

lines = open(PATH, encoding="utf-8").read().split("\n")
# find the summary printf (contains 'worst over layers')
idx = None
for i, ln in enumerate(lines):
    if "worst over layers" in ln:
        idx = i
        break
assert idx is not None, "summary printf not found"
# the printf spans until the closing ';' — find it
end = idx
while ";" not in lines[end]:
    end += 1
NL = chr(10)
BSN = chr(92) + "n"
block = [
    "    /* spectral accumulation: both layers in ONE buffer, one inverse */",
    "    {",
    "      int used = 0;",
    "      TorusPolynomial digp = polynomial_new_torus_polynomial(N);",
    "      const Torus dmask = (((Torus) 1) << cbg) - 1;",
    "      for(int d = 0; d < L; d++)",
    "      {",
    "        const double w = 1.0 / (double) (((Torus) 1) << (62 - cbg * d));",
    "        for(int q = 0; q < N; q++)",
    "          digp->coeffs[q] = (Torus)(",
    "              (((int64_t) mask->coeffs[q]) >> (cbg * d)) & (int64_t) dmask);",
    "        polynomial_torus_to_DFT(dft[0], digp);",
    "        polynomial_torus_to_DFT(dft[2], F);",
    "        for(int q = 0; q < dft[2]->N; q++)",
    "          dft[2]->coeffs[q] *= w;",
    "        if(used == 0)",
    "          polynomial_mul_DFT(dft[1], dft[0], dft[2]);",
    "        else",
    "          polynomial_mul_addto_DFT(dft[1], dft[0], dft[2]);",
    "        used++;",
    "      }",
    "      polynomial_DFT_to_torus(res, dft[1]);",
    "      int64_t worst_acc = 0;",
    "      for(int k = 0; k < N; k++)",
    "      {",
    "        __int128 acc = 0;",
    "        for(int j = 0; j < N; j++)",
    "        {",
    "          int src = (k - j + 2 * N) % N;",
    "          int64_t f = (int64_t) F->coeffs[src];",
    "          if(!f) continue;",
    "          int64_t m = (int64_t) mask->coeffs[j];",
    "          int diff = ((k - j) % (2 * N) + 2 * N) % (2 * N);",
    "          if(diff >= N) f = -f;",
    "          acc += (__int128) m * f;",
    "        }",
    "        int64_t exact = (int64_t)(acc >> 62);",
    "        int64_t err = (int64_t) res->coeffs[k] - exact;",
    "        if(err < 0) err = -err;",
    "        if(err > worst_acc) worst_acc = err;",
    "      }",
    '      printf("cfg bg=%2d L=%d: per-layer=%5ld ACCUM=%5ld u2^44 %s\\n",',
    "             cbg, L, (long)(worst_all >> 44), (long)(worst_acc >> 44),",
    '             (worst_acc >> 44) < 16 ? "FEASIBLE" : "BROKEN");',
    "      free_polynomial(digp);",
    "    }",
]
lines[idx:end + 1] = block
open(PATH, "w", encoding="utf-8").write("\n".join(lines))
print("accumulation test installed")
