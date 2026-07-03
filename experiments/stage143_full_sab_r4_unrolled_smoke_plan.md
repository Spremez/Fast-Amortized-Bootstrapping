# Stage143 Full SAB r4-Unrolled Smoke Plan

Date: 2026-07-03

## Objective

Check whether the Stage142 r4-unrolled kernel candidate still gives a positive signal at complete SAB bootstrapping level.

## Primary Endpoint

`T_bootstrap/r`, implemented as `pvw_lane_avg_us` and compared against `scalar_lane_avg_us` from repeated scalar SAB.

## Status Rule

This stage is a smoke gate only. A positive result opens repeated Stage144; it does not establish final throughput speedup.
