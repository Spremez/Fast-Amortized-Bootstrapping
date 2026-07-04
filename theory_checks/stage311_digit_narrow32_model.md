# Stage311 Digit Narrow32 Model

For the tested SAB parameters, Bg_bit=23 and signed gadget digits fit in int32.
The baseline direct digit path converts signed int64 lanes directly to double.
The Stage311 candidate converts int64 digits to int32 lanes first, then uses
the AVX512 int32-to-double conversion.

The algebra is unchanged if and only if the signed digit range fits in int32.
The implementation therefore keeps a runtime guard and falls back to the
baseline int64-to-double conversion for larger gadget bases.

Promotion requires both the profiled digit component and the sub-DTF microbench
surface to improve in every paired run.
