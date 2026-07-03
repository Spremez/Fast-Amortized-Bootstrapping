#define main stage138_original_main
#include "../stage138_shared_mask_compact_gate/shared_mask_compact_gate.c"
#undef main

#ifndef STAGE139_BACKEND
#define STAGE139_BACKEND "unknown"
#endif

static void stage139_compare_mask_lanes(MAT_TRGSW_COMPACT_OUTPUT_DFT out,
    uint64_t *mismatches, double *max_gap) {
  for (int lane = 1; lane < out->r; lane++) {
    compare_dft(out->a[0], out->a[lane], mismatches, max_gap);
  }
}

static void stage139_closure_case(int r, int N, int T, int Bg_bit, int seed) {
  PVW_TMLWE in = pvmtmlwe_alloc_new_sample(1, r, N);
  MAT_TRGSW_COMPACT_DFT selector =
      mat_trgsw_compact_alloc_new_DFT_sample(T, Bg_bit, 1, r, N);
  MAT_TRGSW_COMPACT_OUTPUT_DFT out =
      mat_trgsw_compact_alloc_new_output_DFT(r, N);
  MAT_TRGSW_COMPACT_MUL_SCRATCH scratch =
      mat_trgsw_compact_alloc_mul_scratch(N);

  fill_case(in, selector, r, N, T, Bg_bit, seed);
  mat_trgsw_compact_mul_pvmtmlwe_DFT(out, in, selector, scratch);

  uint64_t mismatches = 0;
  double max_gap = 0.0;
  stage139_compare_mask_lanes(out, &mismatches, &max_gap);
  const char *status = "EXPECTED_NONCLOSED_COMPACT_OUTPUT";
  if (r <= 1) status = mismatches == 0 ? "TRIVIAL_R1_CLOSED" : "FAIL_R1";
  else if (mismatches == 0) status = "UNEXPECTED_SHARED_MASK_CLOSED";

  printf("CLOSURE139,%s,%d,%d,%d,%d,%d,%" PRIu64 ",%.9f,%s\n",
      STAGE139_BACKEND, r, N, T, Bg_bit, seed, mismatches, max_gap, status);

  free_mat_trgsw_compact_mul_scratch(scratch);
  free_mat_trgsw_compact_output_DFT(out);
  free_mat_trgsw_compact_DFT(selector);
  free_pvmtmlwe(in);
}

int main(void) {
  const int T = 7;
  const int Bg_bit = 7;
  const int seed = 0;
  stage139_closure_case(2, 512, T, Bg_bit, seed);
  stage139_closure_case(4, 512, T, Bg_bit, seed);
  stage139_closure_case(6, 512, T, Bg_bit, seed);
  stage139_closure_case(2, 1024, T, Bg_bit, seed);
  stage139_closure_case(4, 1024, T, Bg_bit, seed);
  stage139_closure_case(6, 1024, T, Bg_bit, seed);
  fprintf(stderr, "stage139_sink=%f\n", g_stage138_sink);
  return 0;
}
