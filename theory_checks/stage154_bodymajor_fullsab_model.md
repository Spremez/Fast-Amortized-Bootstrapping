# Stage154 Bodymajor Full-SAB Model

Body-major changes MAT external-product loop order and locality only. It does
not change the `(h+1) * r_prec * N` SAB update count, key format, security
argument, or scalar/default SAB path.

Therefore a kernel-level result is insufficient: the only meaningful gate is
whether the full complete-SAB `T_bootstrap/r` endpoint improves over the same
H14 r=6 backend tile4 control.
