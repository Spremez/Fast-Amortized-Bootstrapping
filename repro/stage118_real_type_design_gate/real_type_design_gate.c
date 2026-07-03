#include <inttypes.h>
#include <stdint.h>
#include <stdio.h>
#include <stdlib.h>

typedef struct {
  uint64_t k;
  uint64_t r;
  uint64_t N;
  uint64_t mask_polys;
  uint64_t body_polys;
  uint64_t selector_terms;
  uint64_t selector_polys;
  uint64_t key_secret_polys;
} LaneLocalTypeDesign;

static LaneLocalTypeDesign make_design(uint64_t r, uint64_t N) {
  LaneLocalTypeDesign d;
  d.k = 1;
  d.r = r;
  d.N = N;
  d.mask_polys = r;
  d.body_polys = r;
  d.selector_terms = 1 + 2 * r;
  d.selector_polys = 2 * d.selector_terms;
  d.key_secret_polys = r;
  return d;
}

static int validate(uint64_t r, uint64_t N) {
  LaneLocalTypeDesign d = make_design(r, N);
  const uint64_t current_acc_polys = 1 + r;
  const uint64_t current_selector_polys = (1 + r) * (1 + r);
  const uint64_t lane_acc_polys = d.mask_polys + d.body_polys;
  const uint64_t current_key_secret_polys = r;
  const uint64_t dft_poly_bytes = N * sizeof(double);
  const uint64_t current_dft_bytes =
      (current_acc_polys + current_selector_polys) * dft_poly_bytes;
  const uint64_t lane_dft_bytes =
      (lane_acc_polys + d.selector_polys) * dft_poly_bytes;
  const int ok = d.k == 1 && lane_acc_polys == 2 * r &&
      d.selector_terms == 1 + 2 * r &&
      d.selector_polys == 2 * (1 + 2 * r) &&
      d.key_secret_polys == current_key_secret_polys &&
      current_selector_polys > d.selector_terms;
  printf("%" PRIu64 ",%" PRIu64 ",%" PRIu64 ",%" PRIu64 ",%.6f,"
         "%" PRIu64 ",%" PRIu64 ",%.6f,%" PRIu64 ",%" PRIu64 ",%.6f,"
         "%" PRIu64 ",%" PRIu64 ",%.6f,%s\n",
      r, N, current_acc_polys, lane_acc_polys,
      (double)lane_acc_polys / (double)current_acc_polys,
      current_selector_polys, d.selector_polys,
      (double)d.selector_polys / (double)current_selector_polys,
      current_dft_bytes, lane_dft_bytes,
      (double)lane_dft_bytes / (double)current_dft_bytes,
      current_key_secret_polys, d.key_secret_polys,
      (double)d.key_secret_polys / (double)current_key_secret_polys,
      ok ? "PASS_TYPE_SHAPE" : "FAIL");
  return ok ? 0 : 1;
}

int main(void) {
  const uint64_t rs[] = {2, 4, 6, 8};
  const uint64_t Ns[] = {2048, 4096};
  int failures = 0;
  for (size_t i = 0; i < sizeof(rs) / sizeof(rs[0]); i++) {
    for (size_t j = 0; j < sizeof(Ns) / sizeof(Ns[0]); j++) {
      failures += validate(rs[i], Ns[j]);
    }
  }
  return failures == 0 ? 0 : 1;
}
