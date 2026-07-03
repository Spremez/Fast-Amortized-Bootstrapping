# Stage189 Plan

Goal: run an isolated proof probe for Stage187 `T2_closed_state`.

Rules:

- do not modify `sab_pvw_*`;
- model only public linear conversion from lane-local masks to one shared mask;
- keep r=1 as a positive control;
- reject direct closure if r>1 systems are inconsistent;
- route remaining work to T1/T4 or a new measured dataflow mechanism.
