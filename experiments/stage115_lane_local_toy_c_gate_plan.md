# Stage115 Lane-Local Toy C Gate Plan

Date: 2026-07-03

## Objective

Convert the Stage114 symbolic resource screen into a measured toy C
layout/allocation/RSS gate for the lane-local multimask body-linear
candidate.

## Command

```bash
python scripts/build_stage115_lane_local_toy_c_gate.py
```

## Gates

- The generated toy C layout probe must compile.
- Current and lane-local layouts must run for r=2/4/6/8 and N=2048/4096.
- `product_over_requested_ratio` must remain above 1.0.
- Target r=4, N=2048 requested-byte ratio must be at most 1.25.

Passing this stage only permits a toy arithmetic prototype. It does not
permit full SAB integration or a speedup claim.
