# Dummy Padding Semantic Probe

This is a proof probe, not an algorithm implementation.

Retained route:

- dense public shape with random-looking dummy rows;
- inactive dummy rows must be semantic zero;
- evaluator-side semantic skipping would need a declared structured keygen.

Blocked:

- key-size claim, because public row count is unchanged;
- complete-SAB speedup claim, because no production path is benchmarked;
- security/noise claim, because no production keygen/noise proof is supplied.
