# Stage138 Shared-Mask Compact Gate Plan

Date: 2026-07-03

## Objective

Verify the algorithmic MAT-RLWE requirement that one shared mask is reused across r body lanes, instead of repeating lane-pair decompose/DFT work for each lane.

## Falsification Criteria

- production compact shared-mask output differs from repeated lane-pair output;
- performance is reported without dividing by r;
- kernel microbench is reported as full SAB bootstrapping acceleration;
- Stage139 integrates compact selectors without a scalar reference path.
