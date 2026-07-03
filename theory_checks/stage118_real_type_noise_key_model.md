# Stage118 Real-Type Noise/Key Model

Date: 2026-07-03

For k=1, the current shared-mask PVW_TMLWE accumulator has `1+r`
polynomial components. The lane-local design requires one mask/body pair
per lane, or `2r` components. The current dense MAT selector stores
`(1+r)^2` DFT polynomials, while the conservative lane-local selector
stores `2(1+2r)` DFT polynomials.

The key secret polynomial count remains `r` for k=1 because each lane
already has a lane secret in the current PVW key model. This is a design
claim that must be verified by a real object phase/noise prototype.

## Layout Rows

| r | N | acc ratio | selector ratio | DFT byte ratio | key ratio |
|---:|---:|---:|---:|---:|---:|
| 2 | 2048 | 1.333333 | 1.111111 | 1.166667 | 1.000000 |
| 2 | 4096 | 1.333333 | 1.111111 | 1.166667 | 1.000000 |
| 4 | 2048 | 1.600000 | 0.720000 | 0.866667 | 1.000000 |
| 4 | 4096 | 1.600000 | 0.720000 | 0.866667 | 1.000000 |
| 6 | 2048 | 1.714286 | 0.530612 | 0.678571 | 1.000000 |
| 6 | 4096 | 1.714286 | 0.530612 | 0.678571 | 1.000000 |
| 8 | 2048 | 1.777778 | 0.419753 | 0.555556 | 1.000000 |
| 8 | 4096 | 1.777778 | 0.419753 | 0.555556 | 1.000000 |

## Noise Rows

| r | dense terms | lane terms | lane/dense term ratio | status |
|---:|---:|---:|---:|---|
| 2 | 9 | 5 | 0.555556 | NOISE_MODEL_RECORDED_NOT_PROVEN |
| 4 | 25 | 9 | 0.360000 | NOISE_MODEL_RECORDED_NOT_PROVEN |
| 6 | 49 | 13 | 0.265306 | NOISE_MODEL_RECORDED_NOT_PROVEN |
| 8 | 81 | 17 | 0.209877 | NOISE_MODEL_RECORDED_NOT_PROVEN |
