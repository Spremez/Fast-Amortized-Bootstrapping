#define main stage134_original_main
#include "../stage134_generalized_lane_pair_input_ep_gate/generalized_lane_pair_input_ep_gate.c"
#undef main

#ifndef STAGE136_BACKEND
#define STAGE136_BACKEND "unknown"
#endif

static void stage136_exact_decompose_all(TorusPolynomial *out,
    TorusPolynomial in, int Bg_bit, int l) {
  const int N = in->N;
  const int bit_size = (int)(sizeof(Torus) * 8);
  const uint64_t half_Bg = (1ULL << (Bg_bit - 1));
  const uint64_t h_mask = (1ULL << Bg_bit) - 1;
  uint64_t offset = 1ULL << (bit_size - l * Bg_bit - 1);
  for (int t = 0; t < l; t++) {
    offset += (1ULL << (bit_size - t * Bg_bit - 1));
  }
  for (int c = 0; c < N; c++) {
    const uint64_t coeff_off = in->coeffs[c] + offset;
    for (int t = 0; t < l; t++) {
      const uint64_t h_bit = bit_size - (t + 1) * Bg_bit;
      out[t]->coeffs[c] = ((coeff_off >> h_bit) & h_mask) - half_Bg;
    }
  }
}

static void stage136_batched_decomp_dft(DFT_Polynomial *digits_shared,
    DFT_Polynomial *digits_body, TorusPolynomial *source_shared,
    TorusPolynomial *source_body, int r, int T, int Bg_bit,
    TorusPolynomial *scratch_digits) {
  for (int q = 0; q < r; q++) {
    stage136_exact_decompose_all(scratch_digits, source_shared[q], Bg_bit, T);
    for (int t = 0; t < T; t++) {
      polynomial_torus_to_DFT(digits_shared[t * r + q], scratch_digits[t]);
    }
    stage136_exact_decompose_all(scratch_digits, source_body[q], Bg_bit, T);
    for (int t = 0; t < T; t++) {
      polynomial_torus_to_DFT(digits_body[t * r + q], scratch_digits[t]);
    }
  }
}

static void stage136_compare_torus(TorusPolynomial a, TorusPolynomial b,
    uint64_t *mismatches) {
  for (int i = 0; i < a->N; i++) {
    if (a->coeffs[i] != b->coeffs[i]) (*mismatches)++;
  }
}

static void stage136_compare_dft(DFT_Polynomial a, DFT_Polynomial b,
    double tol, uint64_t *mismatches, double *max_gap) {
  for (int i = 0; i < a->N; i++) {
    double gap = a->coeffs[i] - b->coeffs[i];
    if (gap < 0) gap = -gap;
    if (gap > tol) (*mismatches)++;
    if (gap > *max_gap) *max_gap = gap;
  }
}

static void stage136_correctness_case(int r, int N, int T, int Bg_bit,
    int seed) {
  const double tol = 0.0;
  TorusPolynomial *source_shared = new_poly_array(r, N);
  TorusPolynomial *source_body = new_poly_array(r, N);
  TorusPolynomial ref = polynomial_new_torus_polynomial(N);
  TorusPolynomial *batched = new_poly_array(T, N);
  TorusPolynomial *scratch = new_poly_array(T, N);
  DFT_Polynomial *cur_shared = new_dft_array_api(T * r, N);
  DFT_Polynomial *cur_body = new_dft_array_api(T * r, N);
  DFT_Polynomial *bat_shared = new_dft_array_api(T * r, N);
  DFT_Polynomial *bat_body = new_dft_array_api(T * r, N);
  CompactEpScratch ep_scratch = compact_ep_scratch_alloc(N);
  for (int q = 0; q < r; q++) {
    fill_source(source_shared[q], q, 0, seed);
    fill_source(source_body[q], q, 1, seed);
  }
  compact_decomp_dft_only(cur_shared, cur_body, source_shared, source_body,
      r, T, Bg_bit, ep_scratch);
  stage136_batched_decomp_dft(bat_shared, bat_body, source_shared,
      source_body, r, T, Bg_bit, scratch);

  uint64_t torus_mismatches = 0;
  uint64_t dft_mismatches = 0;
  double max_dft_gap = 0.0;
  for (int q = 0; q < r; q++) {
    stage136_exact_decompose_all(batched, source_shared[q], Bg_bit, T);
    for (int t = 0; t < T; t++) {
      polynomial_decompose_i(ref, source_shared[q], Bg_bit, T, t);
      stage136_compare_torus(ref, batched[t], &torus_mismatches);
      stage136_compare_dft(cur_shared[t * r + q], bat_shared[t * r + q],
          tol, &dft_mismatches, &max_dft_gap);
    }
    stage136_exact_decompose_all(batched, source_body[q], Bg_bit, T);
    for (int t = 0; t < T; t++) {
      polynomial_decompose_i(ref, source_body[q], Bg_bit, T, t);
      stage136_compare_torus(ref, batched[t], &torus_mismatches);
      stage136_compare_dft(cur_body[t * r + q], bat_body[t * r + q],
          tol, &dft_mismatches, &max_dft_gap);
    }
  }
  const int ok = torus_mismatches == 0 && dft_mismatches == 0;
  printf("CORRECT,%s,%d,%d,%d,%d,%d,%" PRIu64 ",%" PRIu64 ",%.9f,%.9f,%s\n",
      STAGE136_BACKEND, r, N, T, Bg_bit, seed, torus_mismatches,
      dft_mismatches, max_dft_gap, tol,
      ok ? "PASS_BATCHED_DECOMP_DFT_EQUIV" : "FAIL");

  compact_ep_scratch_free(ep_scratch);
  free_dft_array_api(bat_body, T * r);
  free_dft_array_api(bat_shared, T * r);
  free_dft_array_api(cur_body, T * r);
  free_dft_array_api(cur_shared, T * r);
  free_poly_array_local(scratch, T);
  free_poly_array_local(batched, T);
  free_polynomial(ref);
  free_poly_array_local(source_body, r);
  free_poly_array_local(source_shared, r);
}

static void stage136_print_bench(int r, int N, int T, int Bg_bit, int seed,
    int sample, int reps, int warmups, const char *variant,
    uint64_t total_ns) {
  const double avg_us = ((double)total_ns / (double)reps) / 1000.0;
  printf("BENCH136,%s,%d,%d,%d,%d,%d,%d,%d,%d,%s,%" PRIu64 ",%.6f,%s\n",
      STAGE136_BACKEND, r, N, T, Bg_bit, seed, sample, reps, warmups,
      variant, total_ns, avg_us, "PASS_BENCH_ROW");
}

static void stage136_bench_case(int r, int N, int T, int Bg_bit, int seed,
    int samples, int reps, int warmups) {
  TorusPolynomial *source_shared = new_poly_array(r, N);
  TorusPolynomial *source_body = new_poly_array(r, N);
  DFT_Polynomial *cur_shared = new_dft_array_api(T * r, N);
  DFT_Polynomial *cur_body = new_dft_array_api(T * r, N);
  DFT_Polynomial *bat_shared = new_dft_array_api(T * r, N);
  DFT_Polynomial *bat_body = new_dft_array_api(T * r, N);
  TorusPolynomial *scratch_digits = new_poly_array(T, N);
  CompactEpScratch ep_scratch = compact_ep_scratch_alloc(N);
  for (int q = 0; q < r; q++) {
    fill_source(source_shared[q], q, 0, seed);
    fill_source(source_body[q], q, 1, seed);
  }
  for (int sample = 0; sample < samples; sample++) {
    uint64_t start = 0;
    uint64_t total = 0;
    for (int i = 0; i < warmups; i++) {
      compact_decomp_dft_only(cur_shared, cur_body, source_shared, source_body,
          r, T, Bg_bit, ep_scratch);
    }
    start = stage129_now_ns();
    for (int i = 0; i < reps; i++) {
      compact_decomp_dft_only(cur_shared, cur_body, source_shared, source_body,
          r, T, Bg_bit, ep_scratch);
    }
    total = stage129_now_ns() - start;
    consume_dft_array(cur_shared, T * r);
    consume_dft_array(cur_body, T * r);
    stage136_print_bench(r, N, T, Bg_bit, seed, sample, reps, warmups,
        "current_decomp_dft", total);

    for (int i = 0; i < warmups; i++) {
      stage136_batched_decomp_dft(bat_shared, bat_body, source_shared,
          source_body, r, T, Bg_bit, scratch_digits);
    }
    start = stage129_now_ns();
    for (int i = 0; i < reps; i++) {
      stage136_batched_decomp_dft(bat_shared, bat_body, source_shared,
          source_body, r, T, Bg_bit, scratch_digits);
    }
    total = stage129_now_ns() - start;
    consume_dft_array(bat_shared, T * r);
    consume_dft_array(bat_body, T * r);
    stage136_print_bench(r, N, T, Bg_bit, seed, sample, reps, warmups,
        "batched_decomp_dft", total);
  }
  compact_ep_scratch_free(ep_scratch);
  free_poly_array_local(scratch_digits, T);
  free_dft_array_api(bat_body, T * r);
  free_dft_array_api(bat_shared, T * r);
  free_dft_array_api(cur_body, T * r);
  free_dft_array_api(cur_shared, T * r);
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
  stage136_correctness_case(2, 512, T, Bg_bit, seed);
  stage136_correctness_case(4, 512, T, Bg_bit, seed);
  stage136_correctness_case(6, 512, T, Bg_bit, seed);
  stage136_correctness_case(2, 1024, T, Bg_bit, seed);
  stage136_correctness_case(4, 1024, T, Bg_bit, seed);
  stage136_correctness_case(6, 1024, T, Bg_bit, seed);
  stage136_bench_case(2, 512, T, Bg_bit, seed, samples, reps, warmups);
  stage136_bench_case(4, 512, T, Bg_bit, seed, samples, reps, warmups);
  stage136_bench_case(6, 512, T, Bg_bit, seed, samples, reps, warmups);
  stage136_bench_case(2, 1024, T, Bg_bit, seed, samples, reps, warmups);
  stage136_bench_case(4, 1024, T, Bg_bit, seed, samples, reps, warmups);
  stage136_bench_case(6, 1024, T, Bg_bit, seed, samples, reps, warmups);
  fprintf(stderr, "stage136_sink=%f\n", g_stage129_sink);
  return 0;
}
