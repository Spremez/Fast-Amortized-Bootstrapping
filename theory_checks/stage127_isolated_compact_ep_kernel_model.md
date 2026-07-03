# Stage127 Isolated Compact EP Kernel Model

Date: 2026-07-03

Stage127 factors Stage126's inline external-product computation into a
reusable isolated DFT kernel:

```text
compact_ep_kernel_dft(out_a, out_b, source_shared_q, source_body_q, selector, q, scratch)
```

For each lane q and gadget level t, the kernel decomposes the lane-local
shared/body source polynomials, converts those digits to DFT, and applies
the compact selector rows `shared[t,q]` and `body[t,q]`. It compares output
components with a coefficient reference and compares decrypted phase with
the modeled noisy reference.

## Kernel Rows

| backend | r | N | seed | component mismatches | phase mismatches | noise mismatches | negative failures | max component gap | max phase gap | DFT ratio | total ratio | status |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---|
| spqlios | 2 | 512 | 0 | 0 | 0 | 0 | 1024 | 10301 | 10301 | 1.125000 | 1.000000 | PASS_ISOLATED_COMPACT_EP_KERNEL |
| spqlios | 2 | 512 | 1 | 0 | 0 | 0 | 1024 | 10142 | 10141 | 1.125000 | 1.000000 | PASS_ISOLATED_COMPACT_EP_KERNEL |
| spqlios | 4 | 512 | 0 | 0 | 0 | 0 | 2048 | 11651 | 11647 | 1.562500 | 1.250000 | PASS_ISOLATED_COMPACT_EP_KERNEL |
| spqlios | 4 | 512 | 1 | 0 | 0 | 0 | 2048 | 14645 | 14653 | 1.562500 | 1.250000 | PASS_ISOLATED_COMPACT_EP_KERNEL |
| spqlios | 6 | 512 | 0 | 0 | 0 | 0 | 3072 | 11028 | 11014 | 2.041667 | 1.555556 | PASS_ISOLATED_COMPACT_EP_KERNEL |
| spqlios | 6 | 512 | 1 | 0 | 0 | 0 | 3072 | 11103 | 11089 | 2.041667 | 1.555556 | PASS_ISOLATED_COMPACT_EP_KERNEL |
| spqlios | 2 | 1024 | 0 | 0 | 0 | 0 | 2048 | 13359 | 13358 | 1.125000 | 1.000000 | PASS_ISOLATED_COMPACT_EP_KERNEL |
| spqlios | 4 | 1024 | 0 | 0 | 0 | 0 | 4096 | 12069 | 12087 | 1.562500 | 1.250000 | PASS_ISOLATED_COMPACT_EP_KERNEL |
| spqlios | 6 | 1024 | 0 | 0 | 0 | 0 | 6144 | 12742 | 12730 | 2.041667 | 1.555556 | PASS_ISOLATED_COMPACT_EP_KERNEL |

## Boundary

This is still an isolated generated probe. It does not add production
MOSFHET structs, AVX512 specialization, SAB schedule integration,
multi-seed randomized failure-rate evidence, or complete `T_bootstrap/r`
performance.
