# Stage180 Split-Probe Model

Stage178 showed the combined MAT EP/subdecomp block is hot, but Stage179
denied code permission because the block was not internally split.

Stage180 makes the split explicit:

```text
combined_current ~= sub_decompose + row torus_to_DFT + tiled addmul
```

The split probes are isolated microbenchmarks, so their sum is not expected to
match the combined path perfectly. They are used for routing: only a large
subcomponent with a plausible speedup mechanism can open implementation work.
