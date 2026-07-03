#include <inttypes.h>
#include <stdint.h>
#include <stdio.h>
#include <stdlib.h>

static int64_t signed_small(uint64_t salt, uint64_t a, uint64_t b, uint64_t c) {
  uint64_t x = salt * 0x9e3779b97f4a7c15ULL;
  x ^= (a + 0x100000001b3ULL) * 0xbf58476d1ce4e5b9ULL;
  x ^= (b + 0x94d049bb133111ebULL) * 0x94d049bb133111ebULL;
  x ^= (c + 0x2545f4914f6cdd1dULL) * 0x2545f4914f6cdd1dULL;
  x ^= x >> 33;
  x *= 0xff51afd7ed558ccdULL;
  x ^= x >> 33;
  int64_t v = (int64_t)(x % 17ULL) - 8;
  return v == 0 ? 1 : v;
}

static int64_t abs64(int64_t x) {
  return x < 0 ? -x : x;
}

static int64_t digit(size_t row, size_t coeff) {
  return signed_small(1, row, coeff, 0);
}

static int64_t secret(size_t lane, size_t coeff) {
  return signed_small(2, lane, coeff, 0);
}

static int64_t shared_mask(size_t row, size_t coeff) {
  return signed_small(3, row, coeff, 0);
}

static int64_t lane_mask(size_t row, size_t lane, size_t coeff) {
  return signed_small(4, row, lane, coeff);
}

static int64_t message(size_t row, size_t lane, size_t coeff) {
  if (row == 0) {
    return signed_small(5, lane, coeff, 0);
  }
  if (row == lane + 1) {
    return signed_small(6, lane, coeff, row);
  }
  return 0;
}

static int64_t dense_phase(size_t r, size_t lane, size_t coeff) {
  int64_t phase = 0;
  for (size_t row = 0; row < r + 1; row++) {
    const int64_t d = digit(row, coeff);
    const int64_t mask = shared_mask(row, coeff);
    const int64_t sec = secret(lane, coeff);
    const int64_t body = mask * sec + message(row, lane, coeff);
    phase += d * (body - mask * sec);
  }
  return phase;
}

static int64_t current_format_drop_phase(size_t r, size_t lane, size_t coeff) {
  int64_t phase = 0;
  for (size_t row = 0; row < r + 1; row++) {
    const int64_t d = digit(row, coeff);
    const int64_t mask = shared_mask(row, coeff);
    const int64_t sec = secret(lane, coeff);
    const int keep_body = row == 0 || row == lane + 1;
    const int64_t body = keep_body ? mask * sec + message(row, lane, coeff) : 0;
    phase += d * (body - mask * sec);
  }
  return phase;
}

static int64_t lane_local_phase(size_t r, size_t lane, size_t coeff) {
  (void)r;
  int64_t phase = 0;
  const size_t rows[2] = {0, lane + 1};
  for (size_t i = 0; i < 2; i++) {
    const size_t row = rows[i];
    const int64_t d = digit(row, coeff);
    const int64_t mask = lane_mask(row, lane, coeff);
    const int64_t sec = secret(lane, coeff);
    const int64_t body = mask * sec + message(row, lane, coeff);
    phase += d * (body - mask * sec);
  }
  return phase;
}

static int run_case(size_t r, size_t N) {
  uint64_t mismatches = 0;
  uint64_t drop_failures = 0;
  int64_t max_lane_gap = 0;
  int64_t max_drop_gap = 0;

  for (size_t coeff = 0; coeff < N; coeff++) {
    for (size_t lane = 0; lane < r; lane++) {
      const int64_t dense = dense_phase(r, lane, coeff);
      const int64_t lane_local = lane_local_phase(r, lane, coeff);
      const int64_t drop = current_format_drop_phase(r, lane, coeff);
      const int64_t lane_gap = abs64(dense - lane_local);
      const int64_t drop_gap = abs64(dense - drop);
      if (lane_gap != 0) mismatches++;
      if (drop_gap != 0) drop_failures++;
      if (lane_gap > max_lane_gap) max_lane_gap = lane_gap;
      if (drop_gap > max_drop_gap) max_drop_gap = drop_gap;
    }
  }

  const uint64_t dense_terms = (uint64_t)(r + 1) * (uint64_t)(r + 1);
  const uint64_t lane_terms = 1ULL + 2ULL * (uint64_t)r;
  const double ratio = (double)dense_terms / (double)lane_terms;
  const char *status =
      mismatches == 0 && drop_failures > 0 ? "PASS_EQUIV_NEGATIVE_CONTROL" : "FAIL";

  printf("%zu,%zu,%" PRIu64 ",%" PRIu64 ",%.6f,%" PRIu64 ",%" PRIu64
         ",%" PRId64 ",%" PRId64 ",%s\n",
      r, N, dense_terms, lane_terms, ratio, mismatches, drop_failures,
      max_lane_gap, max_drop_gap, status);
  return status[0] == 'P' ? 0 : 1;
}

int main(void) {
  const size_t rs[] = {2, 4, 6};
  const size_t Ns[] = {64, 256};
  int failures = 0;
  for (size_t i = 0; i < sizeof(rs) / sizeof(rs[0]); i++) {
    for (size_t j = 0; j < sizeof(Ns) / sizeof(Ns[0]); j++) {
      failures += run_case(rs[i], Ns[j]);
    }
  }
  return failures == 0 ? 0 : 1;
}
