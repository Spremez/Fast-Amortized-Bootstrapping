# Stage162 Materialization-Count Feasibility Plan

Date: 2026-07-03

Goal: decide whether the current exact same-format PVW/MAT-SAB path can reduce the 573440 `from_DFT` materializations.

Primary distinction: call-count reduction is algorithmic; batched/materialization backend tuning is implementation-level unless the count changes.
