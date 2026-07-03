# Stage118 Real-Type Design Gate

Date: 2026-07-03

## Decision

`PASS_STAGE118_REAL_TYPE_DESIGN_READY_OBJECT_PROTOTYPE_REQUIRED`

Stage118 converts the Stage117 selector skeleton into a finite
MOSFHET-adjacent type/key/noise design gate. It does not change source
hot paths.

## Gates

| gate | status | metric | value | detail |
|---|---|---|---|---|
| stage118_compile | PASS | gcc_compile | true | Generated real-type design C probe compiled under WSL gcc. |
| stage118_type_shape | PASS | rows | 8 | Lane-local type shape preserves 2r accumulator polynomials and 2(1+2r) selector polynomials. |
| stage118_key_secret_count | PASS | key_secret_ratio | 1.000000;1.000000;1.000000;1.000000;1.000000;1.000000;1.000000;1.000000 | The design reuses r lane secrets for k=1 rather than increasing secret polynomial count. |
| stage118_target_r4_bytes | PASS_BOUNDED | r4_N2048_dft_byte_ratio | 0.866667 | Target r=4 combined accumulator+selector DFT byte model is bounded. |
| stage118_noise_key_model | RECORDED_NOT_PROVEN | noise_rows | 4 | Noise term count is favorable, but real encryption/noise safety remains unproven. |
| stage118_decision | PASS_STAGE118_REAL_TYPE_DESIGN_READY_OBJECT_PROTOTYPE_REQUIRED | next_gate_policy |  | Real-type design is ready only for object prototype, not SAB integration. |

## Type Layout

| r | N | acc ratio | selector ratio | DFT byte ratio | key ratio | status |
|---:|---:|---:|---:|---:|---:|---|
| 2 | 2048 | 1.333333 | 1.111111 | 1.166667 | 1.000000 | PASS_TYPE_SHAPE |
| 2 | 4096 | 1.333333 | 1.111111 | 1.166667 | 1.000000 | PASS_TYPE_SHAPE |
| 4 | 2048 | 1.600000 | 0.720000 | 0.866667 | 1.000000 | PASS_TYPE_SHAPE |
| 4 | 4096 | 1.600000 | 0.720000 | 0.866667 | 1.000000 | PASS_TYPE_SHAPE |
| 6 | 2048 | 1.714286 | 0.530612 | 0.678571 | 1.000000 | PASS_TYPE_SHAPE |
| 6 | 4096 | 1.714286 | 0.530612 | 0.678571 | 1.000000 | PASS_TYPE_SHAPE |
| 8 | 2048 | 1.777778 | 0.419753 | 0.555556 | 1.000000 | PASS_TYPE_SHAPE |
| 8 | 4096 | 1.777778 | 0.419753 | 0.555556 | 1.000000 | PASS_TYPE_SHAPE |

## Noise/Key Status

| r | lane/dense noise terms | product ratio | status |
|---:|---:|---:|---|
| 2 | 0.555556 | 1.800000 | NOISE_MODEL_RECORDED_NOT_PROVEN |
| 4 | 0.360000 | 2.777778 | NOISE_MODEL_RECORDED_NOT_PROVEN |
| 6 | 0.265306 | 3.769231 | NOISE_MODEL_RECORDED_NOT_PROVEN |
| 8 | 0.209877 | 4.764706 | NOISE_MODEL_RECORDED_NOT_PROVEN |

## Interpretation

The type-shape gate is positive, but the noise/key row is explicitly
`RECORDED_NOT_PROVEN`. The next stage must build a real-object
allocation/phase/noise prototype before any integration with SAB.
