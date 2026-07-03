# Stage194 Plan

Goal: decide whether exact DFT/conversion has a local implementation candidate
before writing code.

Rules:

- no source changes;
- do not repeat Stage163 component-major batching or Stage174 direct-scale;
- do not claim same-format materialization-count reduction after Stage162;
- require a component mechanism above the Stage180 3% complete-SAB threshold;
- if no candidate is promoted, route to scoped paper/repro refresh.
