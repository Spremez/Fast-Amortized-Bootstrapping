#define main stage134_original_main
#include "../stage134_generalized_lane_pair_input_ep_gate/generalized_lane_pair_input_ep_gate.c"
#undef main

#ifndef STAGE137_BACKEND
#define STAGE137_BACKEND "unknown"
#endif

static void stage137_decompose_only(TorusPolynomial *digits_shared,
    TorusPolynomial *digits_body, TorusPolynomial *source_shared,
    TorusPolynomial *source_body, int r, int T, int Bg_bit) {
  for (int q = 0; q < r; q++) {
    for (int t = 0; t < T; t++) {
      const int idx = t * r + q;
      polynomial_decompose_i(digits_shared[idx], source_shared[q], Bg_bit, T, t);
      polynomial_decompose_i(digits_body[idx], source_body[q], Bg_bit, T, t);
    }
  }
}

static void stage137_dft_only(DFT_Polynomial *out_shared,
    DFT_Polynomial *out_body, TorusPolynomial *digits_shared,
    TorusPolynomial *digits_body, int r, int T) {
  for (int t = 0; t < T; t++) {
    for (int q = 0; q < r; q++) {
      const int idx = t * r + q;
      polynomial_torus_to_DFT(out_shared[idx], digits_shared[idx]);
      polynomial_torus_to_DFT(out_body[idx], digits_body[idx]);
    }
  }
}

static void stage137_compare_dft(DFT_Polynomial a, DFT_Polynomial b,
    double tol, uint64_t *mismatches, double *max_gap) {
  for (int i = 0; i < a->N; i++) {
    double gap = a->coeffs[i] - b->coeffs[i];
    if (gap < 0) gap = -gap;
    if (gap > tol) (*mismatches)++;
    if (gap > *max_gap) *max_gap = gap;
  }
}

static void stage137_correctness_case(int r, int N, int T, int Bg_bit,
    int seed) {
  const double tol = 0.0;
  TorusPolynomial *source_shared = new_poly_array(r, N);
  TorusPolynomial *source_body = new_poly_array(r, N);
  TorusPolynomial *digits_shared = new_poly_array(T * r, N);
  TorusPolynomial *digits_body = new_poly_array(T * r, N);
  DFT_Polynomial *current_shared = new_dft_array_api(T * r, N);
  DFT_Polynomial *current_body = new_dft_array_api(T * r, N);
  DFT_Polynomial *split_shared = new_dft_array_api(T * r, N);
  DFT_Polynomial *split_body = new_dft_array_api(T * r, N);
  CompactEpScratch scratch = compact_ep_scratch_alloc(N);
  for (int q = 0; q < r; q++) {
    fill_source(source_shared[q], q, 0, seed);
    fill_source(source_body[q], q, 1, seed);
  }
  compact_decomp_dft_only(current_shared, current_body, source_shared,
      source_body, r, T, Bg_bit, scratch);
  stage137_decompose_only(digits_shared, digits_body, source_shared,
      source_body, r, T, Bg_bit);
  stage137_dft_only(split_shared, split_body, digits_shared, digits_body, r, T);
  uint64_t mismatches = 0;
  double max_gap = 0.0;
  for (int i = 0; i < T * r; i++) {
    stage137_compare_dft(current_shared[i], split_shared[i], tol, &mismatches, &max_gap);
    stage137_compare_dft(current_body[i], split_body[i], tol, &mismatches, &max_gap);
  }
  printf("CORRECT137,%s,%d,%d,%d,%d,%d,%" PRIu64 ",%.9f,%.9f,%s\n",
      STAGE137_BACKEND, r, N, T, Bg_bit, seed, mismatches, max_gap, tol,
      mismatches == 0 ? "PASS_SPLIT_DECOMP_DFT_EQUIV" : "FAIL");
  compact_ep_scratch_free(scratch);
  free_dft_array_api(split_body, T * r);
  free_dft_array_api(split_shared, T * r);
  free_dft_array_api(current_body, T * r);
  free_dft_array_api(current_shared, T * r);
  free_poly_array_local(digits_body, T * r);
  free_poly_array_local(digits_shared, T * r);
  free_poly_array_local(source_body, r);
  free_poly_array_local(source_shared, r);
}

static void stage137_print_bench(int r, int N, int T, int Bg_bit, int seed,
    int sample, int reps, int warmups, const char *variant, uint64_t total_ns) {
  const double avg_us = ((double)total_ns / (double)reps) / 1000.0;
  printf("BENCH137,%s,%d,%d,%d,%d,%d,%d,%d,%d,%s,%" PRIu64 ",%.6f,%s\n",
      STAGE137_BACKEND, r, N, T, Bg_bit, seed, sample, reps, warmups,
      variant, total_ns, avg_us, "PASS_BENCH_ROW");
}

static void stage137_bench_case(int r, int N, int T, int Bg_bit, int seed,
    int samples, int reps, int warmups) {
  TorusPolynomial *source_shared = new_poly_array(r, N);
  TorusPolynomial *source_body = new_poly_array(r, N);
  TorusPolynomial *digits_shared = new_poly_array(T * r, N);
  TorusPolynomial *digits_body = new_poly_array(T * r, N);
  DFT_Polynomial *current_shared = new_dft_array_api(T * r, N);
  DFT_Polynomial *current_body = new_dft_array_api(T * r, N);
  DFT_Polynomial *split_shared = new_dft_array_api(T * r, N);
  DFT_Polynomial *split_body = new_dft_array_api(T * r, N);
  CompactEpScratch scratch = compact_ep_scratch_alloc(N);
  for (int q = 0; q < r; q++) {
    fill_source(source_shared[q], q, 0, seed);
    fill_source(source_body[q], q, 1, seed);
  }
  stage137_decompose_only(digits_shared, digits_body, source_shared,
      source_body, r, T, Bg_bit);
  for (int sample = 0; sample < samples; sample++) {
    uint64_t start = 0;
    uint64_t total = 0;
    for (int i = 0; i < warmups; i++) {
      compact_decomp_dft_only(current_shared, current_body, source_shared,
          source_body, r, T, Bg_bit, scratch);
    }
    start = stage129_now_ns();
    for (int i = 0; i < reps; i++) {
      compact_decomp_dft_only(current_shared, current_body, source_shared,
          source_body, r, T, Bg_bit, scratch);
    }
    total = stage129_now_ns() - start;
    consume_dft_array(current_shared, T * r);
    consume_dft_array(current_body, T * r);
    stage137_print_bench(r, N, T, Bg_bit, seed, sample, reps, warmups,
        "current_full_decomp_dft", total);

    for (int i = 0; i < warmups; i++) {
      stage137_decompose_only(digits_shared, digits_body, source_shared,
          source_body, r, T, Bg_bit);
    }
    start = stage129_now_ns();
    for (int i = 0; i < reps; i++) {
      stage137_decompose_only(digits_shared, digits_body, source_shared,
          source_body, r, T, Bg_bit);
    }
    total = stage129_now_ns() - start;
    stage137_print_bench(r, N, T, Bg_bit, seed, sample, reps, warmups,
        "decompose_only", total);

    for (int i = 0; i < warmups; i++) {
      stage137_dft_only(split_shared, split_body, digits_shared, digits_body, r, T);
    }
    start = stage129_now_ns();
    for (int i = 0; i < reps; i++) {
      stage137_dft_only(split_shared, split_body, digits_shared, digits_body, r, T);
    }
    total = stage129_now_ns() - start;
    consume_dft_array(split_shared, T * r);
    consume_dft_array(split_body, T * r);
    stage137_print_bench(r, N, T, Bg_bit, seed, sample, reps, warmups,
        "dft_only", total);
  }
  compact_ep_scratch_free(scratch);
  free_dft_array_api(split_body, T * r);
  free_dft_array_api(split_shared, T * r);
  free_dft_array_api(current_body, T * r);
  free_dft_array_api(current_shared, T * r);
  free_poly_array_local(digits_body, T * r);
  free_poly_array_local(digits_shared, T * r);
  free_poly_array_local(source_body, r);
  free_poly_array_local(source_shared, r);
}

int main(void) {
  const int T = 7;
  const int Bg_bit = 7;
  const int seed = 0;
  const int samples = 5;
  const int reps = 20;
  const int warmups = 2;
  stage137_correctness_case(2, 512, T, Bg_bit, seed);
  stage137_correctness_case(4, 512, T, Bg_bit, seed);
  stage137_correctness_case(6, 512, T, Bg_bit, seed);
  stage137_correctness_case(2, 1024, T, Bg_bit, seed);
  stage137_correctness_case(4, 1024, T, Bg_bit, seed);
  stage137_correctness_case(6, 1024, T, Bg_bit, seed);
  stage137_bench_case(2, 512, T, Bg_bit, seed, samples, reps, warmups);
  stage137_bench_case(4, 512, T, Bg_bit, seed, samples, reps, warmups);
  stage137_bench_case(6, 512, T, Bg_bit, seed, samples, reps, warmups);
  stage137_bench_case(2, 1024, T, Bg_bit, seed, samples, reps, warmups);
  stage137_bench_case(4, 1024, T, Bg_bit, seed, samples, reps, warmups);
  stage137_bench_case(6, 1024, T, Bg_bit, seed, samples, reps, warmups);
  fprintf(stderr, "stage137_sink=%f\n", g_stage129_sink);
  return 0;
}
