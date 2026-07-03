# Stage197 Citation Support Model

The support model has four levels:

- `ALLOW`: local repro evidence supports the sentence under stated scope.
- `ALLOW_SCOPED`: local repro supports a quantitative statement only with
  backend, parameter, seed, and baseline qualifications.
- `ALLOW_METADATA_ONLY`: public metadata supports bibliographic/source
  existence, not paper-specific theorem or experiment claims.
- `ALLOW_BLOCKED_ROUTE`: local evidence supports a blocked-route statement,
  not an implemented algorithm claim.

The support bank is a guard against overclaiming; it is not evidence for
algorithmic completion.
