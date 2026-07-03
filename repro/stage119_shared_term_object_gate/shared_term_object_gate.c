#include <inttypes.h>
#include <stdint.h>
#include <stdio.h>
#include <stdlib.h>

static int64_t small(uint64_t salt, uint64_t a, uint64_t b, uint64_t c) {
  uint64_t x = salt * 0x9e3779b97f4a7c15ULL;
  x ^= (a + 0xbf58476d1ce4e5b9ULL) * 0x94d049bb133111ebULL;
  x ^= (b + 0x2545f4914f6cdd1dULL) * 0x9e3779b97f4a7c15ULL;
  x ^= (c + 0x100000001b3ULL) * 0xbf58476d1ce4e5b9ULL;
  x ^= x >> 33;
  int64_t v = (int64_t)(x % 19ULL) - 9;
  return v == 0 ? 1 : v;
}

static int64_t abs64(int64_t x) {
  return x < 0 ? -x : x;
}

static int64_t digit_shared(size_t coeff) {
  return small(1, coeff, 0, 0);
}

static int64_t digit_body(size_t lane, size_t coeff) {
  return small(2, lane, coeff, 0);
}

static int64_t secret(size_t lane, size_t coeff) {
  return small(3, lane, coeff, 0);
}

static int64_t msg_shared(size_t lane, size_t coeff) {
  return small(4, lane, coeff, 0);
}

static int64_t msg_body(size_t lane, size_t coeff) {
  return small(5, lane, coeff, 0);
}

static int64_t mask_shared(size_t lane, size_t coeff) {
  return small(6, lane, coeff, 0);
}

static int64_t mask_body(size_t lane, size_t coeff) {
  return small(7, lane, coeff, 0);
}

static int64_t noise_value(size_t lane, size_t coeff, size_t term) {
  int64_t v = small(8 + term, lane, coeff, 0) % 3;
  if (v < 0) v = -v;
  return v - 1;
}

static int64_t dense_expected(size_t lane, size_t coeff) {
  return digit_shared(coeff) * msg_shared(lane, coeff) +
      digit_body(lane, coeff) * msg_body(lane, coeff);
}

static int64_t vector_shared_phase(size_t lane, size_t coeff, int with_noise) {
  const int64_t s = secret(lane, coeff);
  const int64_t ns = with_noise ? noise_value(lane, coeff, 0) : 0;
  const int64_t nb = with_noise ? noise_value(lane, coeff, 1) : 0;
  const int64_t shared_body = mask_shared(lane, coeff) * s +
      msg_shared(lane, coeff) + ns;
  const int64_t lane_body = mask_body(lane, coeff) * s +
      msg_body(lane, coeff) + nb;
  const int64_t shared_phase = shared_body - mask_shared(lane, coeff) * s;
  const int64_t body_phase = lane_body - mask_body(lane, coeff) * s;
  return digit_shared(coeff) * shared_phase + digit_body(lane, coeff) * body_phase;
}

static int64_t scalar_shared_phase(size_t lane, size_t coeff) {
  const int64_t s = secret(lane, coeff);
  const int64_t shared_body = mask_shared(0, coeff) * s + msg_shared(0, coeff);
  const int64_t lane_body = mask_body(lane, coeff) * s + msg_body(lane, coeff);
  const int64_t shared_phase = shared_body - mask_shared(0, coeff) * s;
  const int64_t body_phase = lane_body - mask_body(lane, coeff) * s;
  return digit_shared(coeff) * shared_phase + digit_body(lane, coeff) * body_phase;
}

static int run_phase_case(size_t r, size_t N, const char *variant) {
  uint64_t mismatches = 0;
  uint64_t negative_control_failures = 0;
  uint64_t noise_violations = 0;
  int64_t max_error = 0;
  int64_t max_noise = 0;
  int64_t noise_bound = 0;

  for (size_t coeff = 0; coeff < N; coeff++) {
    for (size_t lane = 0; lane < r; lane++) {
      const int64_t expected = dense_expected(lane, coeff);
      int64_t got = 0;
      if (variant[0] == 'v') {
        got = vector_shared_phase(lane, coeff, 0);
        const int64_t noisy = vector_shared_phase(lane, coeff, 1);
        const int64_t bound = abs64(digit_shared(coeff)) + abs64(digit_body(lane, coeff));
        const int64_t noise = abs64(noisy - got);
        if (noise > max_noise) max_noise = noise;
        if (bound > noise_bound) noise_bound = bound;
        if (noise > bound) noise_violations++;
      } else {
        got = scalar_shared_phase(lane, coeff);
      }
      const int64_t err = abs64(got - expected);
      if (err != 0) {
        mismatches++;
        if (variant[0] == 's') negative_control_failures++;
      }
      if (err > max_error) max_error = err;
    }
  }

  const int ok = variant[0] == 'v' ?
      (mismatches == 0 && noise_violations == 0) :
      (negative_control_failures > 0);
  printf("%zu,%zu,%s,%" PRIu64 ",%" PRIu64 ",%" PRId64 ",%" PRId64
         ",%" PRId64 ",%" PRIu64 ",%s\n",
      r, N, variant, mismatches, negative_control_failures, max_error,
      max_noise, noise_bound, noise_violations,
      ok ? (variant[0] == 'v' ? "PASS_VECTOR_OBJECT" : "PASS_REJECTED_SCALAR_SHARED") : "FAIL");
  return ok ? 0 : 1;
}

static int run_layout_case(size_t r, size_t N) {
  (void)N;
  const uint64_t dense_terms = (uint64_t)(r + 1) * (uint64_t)(r + 1);
  const uint64_t scalar_terms = 1 + 2 * (uint64_t)r;
  const uint64_t vector_terms = 2 * (uint64_t)r;
  const uint64_t dense_selector_polys = dense_terms;
  const uint64_t stage118_selector_polys = 2 * scalar_terms;
  const uint64_t vector_selector_polys = 2 * vector_terms;
  const uint64_t dense_total = (1 + (uint64_t)r) + dense_selector_polys;
  const uint64_t stage118_total = 2 * (uint64_t)r + stage118_selector_polys;
  const uint64_t vector_total = 2 * (uint64_t)r + vector_selector_polys;
  const double byte_ratio = (double)vector_total / (double)dense_total;
  const double product_ratio = (double)dense_terms / (double)vector_terms;
  const int ok = vector_terms < dense_terms && vector_total <= stage118_total;
  printf("%zu,%zu,%" PRIu64 ",%" PRIu64 ",%" PRIu64 ",%" PRIu64
         ",%" PRIu64 ",%" PRIu64 ",%" PRIu64 ",%" PRIu64 ",%" PRIu64
         ",%.6f,%.6f,%s\n",
      r, N, dense_terms, scalar_terms, vector_terms, dense_selector_polys,
      stage118_selector_polys, vector_selector_polys, dense_total,
      stage118_total, vector_total, byte_ratio, product_ratio,
      ok ? "PASS_LAYOUT_REFINED" : "FAIL");
  return ok ? 0 : 1;
}

int main(void) {
  const size_t rs[] = {2, 4, 6};
  const size_t Ns[] = {64, 256};
  int failures = 0;
  for (size_t i = 0; i < sizeof(rs) / sizeof(rs[0]); i++) {
    for (size_t j = 0; j < sizeof(Ns) / sizeof(Ns[0]); j++) {
      failures += run_phase_case(rs[i], Ns[j], "scalar_shared");
      failures += run_phase_case(rs[i], Ns[j], "vector_shared");
      failures += run_layout_case(rs[i], Ns[j]);
    }
  }
  return failures == 0 ? 0 : 1;
}
