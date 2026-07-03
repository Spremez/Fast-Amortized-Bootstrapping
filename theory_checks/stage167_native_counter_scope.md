# Stage167 Native Counter Scope

Native counters answer an implementation-attribution question: whether the
current exact r=6 path appears dominated by memory traffic, FMA work, branch
cost, or cache behavior on the target CPU.

They do not by themselves prove theoretical optimality. A theoretical claim
would still need a lower bound tied to the MAT-RLWE/SAB operation count and a
comparison against all relevant representation/keygen alternatives.
