
#include "mosfhet.h"
#include <inttypes.h>
#include <stdint.h>
#include <stdio.h>
#include <stdlib.h>

#ifndef STAGE220_BACKEND
#define STAGE220_BACKEND "unknown"
#endif

typedef enum {
  STAGE220_ROLE_ACTIVE = 1,
  STAGE220_ROLE_DUMMY_ZERO = 2
} Stage220Role;

typedef struct {
  int row;
  int col;
  int role;
  int may_skip;
} Stage220EquationRow;

static const Stage220EquationRow stage220_r2_rows[] = {
  {0, 0, STAGE220_ROLE_DUMMY_ZERO, 1},
  {0, 1, STAGE220_ROLE_ACTIVE, 0},
  {0, 2, STAGE220_ROLE_ACTIVE, 0},
  {1, 0, STAGE220_ROLE_ACTIVE, 0},
  {1, 1, STAGE220_ROLE_ACTIVE, 0},
  {1, 2, STAGE220_ROLE_ACTIVE, 0},
  {2, 0, STAGE220_ROLE_ACTIVE, 0},
  {2, 1, STAGE220_ROLE_ACTIVE, 0},
  {2, 2, STAGE220_ROLE_ACTIVE, 0},
};
static const Stage220EquationRow stage220_r4_rows[] = {
  {0, 0, STAGE220_ROLE_DUMMY_ZERO, 1},
  {0, 1, STAGE220_ROLE_ACTIVE, 0},
  {0, 2, STAGE220_ROLE_ACTIVE, 0},
  {0, 3, STAGE220_ROLE_ACTIVE, 0},
  {0, 4, STAGE220_ROLE_ACTIVE, 0},
  {1, 0, STAGE220_ROLE_ACTIVE, 0},
  {1, 1, STAGE220_ROLE_ACTIVE, 0},
  {1, 2, STAGE220_ROLE_ACTIVE, 0},
  {1, 3, STAGE220_ROLE_DUMMY_ZERO, 1},
  {1, 4, STAGE220_ROLE_DUMMY_ZERO, 1},
  {2, 0, STAGE220_ROLE_ACTIVE, 0},
  {2, 1, STAGE220_ROLE_DUMMY_ZERO, 1},
  {2, 2, STAGE220_ROLE_ACTIVE, 0},
  {2, 3, STAGE220_ROLE_ACTIVE, 0},
  {2, 4, STAGE220_ROLE_DUMMY_ZERO, 1},
  {3, 0, STAGE220_ROLE_ACTIVE, 0},
  {3, 1, STAGE220_ROLE_DUMMY_ZERO, 1},
  {3, 2, STAGE220_ROLE_DUMMY_ZERO, 1},
  {3, 3, STAGE220_ROLE_ACTIVE, 0},
  {3, 4, STAGE220_ROLE_ACTIVE, 0},
  {4, 0, STAGE220_ROLE_ACTIVE, 0},
  {4, 1, STAGE220_ROLE_ACTIVE, 0},
  {4, 2, STAGE220_ROLE_DUMMY_ZERO, 1},
  {4, 3, STAGE220_ROLE_DUMMY_ZERO, 1},
  {4, 4, STAGE220_ROLE_ACTIVE, 0},
};
static const Stage220EquationRow stage220_r6_rows[] = {
  {0, 0, STAGE220_ROLE_DUMMY_ZERO, 1},
  {0, 1, STAGE220_ROLE_ACTIVE, 0},
  {0, 2, STAGE220_ROLE_ACTIVE, 0},
  {0, 3, STAGE220_ROLE_ACTIVE, 0},
  {0, 4, STAGE220_ROLE_ACTIVE, 0},
  {0, 5, STAGE220_ROLE_ACTIVE, 0},
  {0, 6, STAGE220_ROLE_ACTIVE, 0},
  {1, 0, STAGE220_ROLE_ACTIVE, 0},
  {1, 1, STAGE220_ROLE_ACTIVE, 0},
  {1, 2, STAGE220_ROLE_ACTIVE, 0},
  {1, 3, STAGE220_ROLE_DUMMY_ZERO, 1},
  {1, 4, STAGE220_ROLE_DUMMY_ZERO, 1},
  {1, 5, STAGE220_ROLE_DUMMY_ZERO, 1},
  {1, 6, STAGE220_ROLE_DUMMY_ZERO, 1},
  {2, 0, STAGE220_ROLE_ACTIVE, 0},
  {2, 1, STAGE220_ROLE_DUMMY_ZERO, 1},
  {2, 2, STAGE220_ROLE_ACTIVE, 0},
  {2, 3, STAGE220_ROLE_ACTIVE, 0},
  {2, 4, STAGE220_ROLE_DUMMY_ZERO, 1},
  {2, 5, STAGE220_ROLE_DUMMY_ZERO, 1},
  {2, 6, STAGE220_ROLE_DUMMY_ZERO, 1},
  {3, 0, STAGE220_ROLE_ACTIVE, 0},
  {3, 1, STAGE220_ROLE_DUMMY_ZERO, 1},
  {3, 2, STAGE220_ROLE_DUMMY_ZERO, 1},
  {3, 3, STAGE220_ROLE_ACTIVE, 0},
  {3, 4, STAGE220_ROLE_ACTIVE, 0},
  {3, 5, STAGE220_ROLE_DUMMY_ZERO, 1},
  {3, 6, STAGE220_ROLE_DUMMY_ZERO, 1},
  {4, 0, STAGE220_ROLE_ACTIVE, 0},
  {4, 1, STAGE220_ROLE_DUMMY_ZERO, 1},
  {4, 2, STAGE220_ROLE_DUMMY_ZERO, 1},
  {4, 3, STAGE220_ROLE_DUMMY_ZERO, 1},
  {4, 4, STAGE220_ROLE_ACTIVE, 0},
  {4, 5, STAGE220_ROLE_ACTIVE, 0},
  {4, 6, STAGE220_ROLE_DUMMY_ZERO, 1},
  {5, 0, STAGE220_ROLE_ACTIVE, 0},
  {5, 1, STAGE220_ROLE_DUMMY_ZERO, 1},
  {5, 2, STAGE220_ROLE_DUMMY_ZERO, 1},
  {5, 3, STAGE220_ROLE_DUMMY_ZERO, 1},
  {5, 4, STAGE220_ROLE_DUMMY_ZERO, 1},
  {5, 5, STAGE220_ROLE_ACTIVE, 0},
  {5, 6, STAGE220_ROLE_ACTIVE, 0},
  {6, 0, STAGE220_ROLE_ACTIVE, 0},
  {6, 1, STAGE220_ROLE_ACTIVE, 0},
  {6, 2, STAGE220_ROLE_DUMMY_ZERO, 1},
  {6, 3, STAGE220_ROLE_DUMMY_ZERO, 1},
  {6, 4, STAGE220_ROLE_DUMMY_ZERO, 1},
  {6, 5, STAGE220_ROLE_DUMMY_ZERO, 1},
  {6, 6, STAGE220_ROLE_ACTIVE, 0},
};

typedef struct _Stage220EncryptedRow {
  TorusPolynomial a;
  TorusPolynomial b;
  TorusPolynomial semantic;
  TorusPolynomial noise;
  DFT_Polynomial a_dft;
  DFT_Polynomial b_dft;
  int matrix_row;
  int matrix_col;
  int secret_lane;
  int role;
  int may_skip;
} *Stage220EncryptedRow;

typedef struct _Stage220EncryptedKey {
  Stage220EncryptedRow * rows;
  int row_count;
  int active_count;
  int dummy_count;
  int r;
  int N;
} *Stage220EncryptedKey;

static uint64_t mix64(uint64_t salt, uint64_t a, uint64_t b, uint64_t c){
  uint64_t x = salt * 0x9e3779b97f4a7c15ULL;
  x ^= (a + 0xbf58476d1ce4e5b9ULL) * 0x94d049bb133111ebULL;
  x ^= (b + 0x2545f4914f6cdd1dULL) * 0x9e3779b97f4a7c15ULL;
  x ^= (c + 0x100000001b3ULL) * 0xbf58476d1ce4e5b9ULL;
  x ^= x >> 33;
  x *= 0xff51afd7ed558ccdULL;
  x ^= x >> 33;
  return x;
}

static Torus signed_torus(int64_t value){
  return (Torus)value;
}

static uint64_t abs_gap(Torus a, Torus b){
  const uint64_t d = (uint64_t)(a - b);
  if(d <= (1ULL << 63)) return d;
  return (~d) + 1ULL;
}

static const Stage220EquationRow * rows_for_r(int r, int * count){
  if(r == 2){
    *count = (int)(sizeof(stage220_r2_rows) / sizeof(stage220_r2_rows[0]));
    return stage220_r2_rows;
  }
  if(r == 4){
    *count = (int)(sizeof(stage220_r4_rows) / sizeof(stage220_r4_rows[0]));
    return stage220_r4_rows;
  }
  if(r == 6){
    *count = (int)(sizeof(stage220_r6_rows) / sizeof(stage220_r6_rows[0]));
    return stage220_r6_rows;
  }
  *count = 0;
  return NULL;
}

static void zero_poly(TorusPolynomial p){
  for(int i = 0; i < p->N; i++) p->coeffs[i] = 0;
}

static void copy_addto(TorusPolynomial out, TorusPolynomial in){
  for(int i = 0; i < out->N; i++) out->coeffs[i] += in->coeffs[i];
}

static void copy_subto(TorusPolynomial out, TorusPolynomial in){
  for(int i = 0; i < out->N; i++) out->coeffs[i] -= in->coeffs[i];
}

static void fill_secret(TorusPolynomial out, int lane, int seed){
  for(int i = 0; i < out->N; i++){
    out->coeffs[i] = (Torus)(mix64(220100ULL + (uint64_t)seed,
        (uint64_t)lane, 0, (uint64_t)i) & 1ULL);
  }
}

static void fill_mask(TorusPolynomial out, int row, int col, int seed){
  for(int i = 0; i < out->N; i++){
    const int64_t value = (int64_t)(mix64(220200ULL + (uint64_t)seed,
        (uint64_t)row, (uint64_t)col, (uint64_t)i) % 3ULL) - 1;
    out->coeffs[i] = signed_torus(value);
  }
}

static void fill_noise(TorusPolynomial out, int row, int col, int seed){
  for(int i = 0; i < out->N; i++){
    const int64_t value = (int64_t)(mix64(220300ULL + (uint64_t)seed,
        (uint64_t)row, (uint64_t)col, (uint64_t)i) % 3ULL) - 1;
    out->coeffs[i] = signed_torus(value);
  }
}

static void fill_active_semantic(TorusPolynomial out, int row, int col,
    int seed){
  zero_poly(out);
  const int idx = (13 * row + 17 * col + seed) & (out->N - 1);
  const int64_t sign = ((row + col + seed) & 1) ? -1 : 1;
  out->coeffs[idx] = signed_torus(sign * (int64_t)(1 + ((row + col) % 5)));
}

static void fill_random_dummy_semantic(TorusPolynomial out, int row, int col,
    int seed){
  zero_poly(out);
  const int idx = (19 * row + 23 * col + seed + 7) & (out->N - 1);
  out->coeffs[idx] = signed_torus(3);
}

static Stage220EncryptedRow row_alloc(int N){
  Stage220EncryptedRow row = (Stage220EncryptedRow)safe_malloc(sizeof(*row));
  row->a = polynomial_new_torus_polynomial(N);
  row->b = polynomial_new_torus_polynomial(N);
  row->semantic = polynomial_new_torus_polynomial(N);
  row->noise = polynomial_new_torus_polynomial(N);
  row->a_dft = polynomial_new_DFT_polynomial(N);
  row->b_dft = polynomial_new_DFT_polynomial(N);
  return row;
}

static void row_free(Stage220EncryptedRow row){
  if(row == NULL) return;
  free_polynomial(row->a);
  free_polynomial(row->b);
  free_polynomial(row->semantic);
  free_polynomial(row->noise);
  free_DFT_polynomial(row->a_dft);
  free_DFT_polynomial(row->b_dft);
  free(row);
}

static Stage220EncryptedKey key_alloc(int r, int N){
  int row_count = 0;
  const Stage220EquationRow * eq = rows_for_r(r, &row_count);
  if(eq == NULL || row_count == 0) return NULL;
  Stage220EncryptedKey key = (Stage220EncryptedKey)safe_malloc(sizeof(*key));
  key->rows = (Stage220EncryptedRow *)safe_malloc(sizeof(Stage220EncryptedRow) * row_count);
  key->row_count = row_count;
  key->active_count = 0;
  key->dummy_count = 0;
  key->r = r;
  key->N = N;
  for(int i = 0; i < row_count; i++){
    key->rows[i] = row_alloc(N);
    key->rows[i]->matrix_row = eq[i].row;
    key->rows[i]->matrix_col = eq[i].col;
    key->rows[i]->secret_lane = (eq[i].row + eq[i].col) % r;
    key->rows[i]->role = eq[i].role;
    key->rows[i]->may_skip = eq[i].may_skip;
    if(eq[i].role == STAGE220_ROLE_ACTIVE) key->active_count++;
    if(eq[i].role == STAGE220_ROLE_DUMMY_ZERO) key->dummy_count++;
  }
  return key;
}

static void key_free(Stage220EncryptedKey key){
  if(key == NULL) return;
  for(int i = 0; i < key->row_count; i++) row_free(key->rows[i]);
  free(key->rows);
  free(key);
}

static void encrypt_row(Stage220EncryptedRow row, TorusPolynomial secret,
    int seed){
  fill_mask(row->a, row->matrix_row, row->matrix_col, seed);
  fill_noise(row->noise, row->matrix_row, row->matrix_col, seed);
  if(row->role == STAGE220_ROLE_ACTIVE){
    fill_active_semantic(row->semantic, row->matrix_row, row->matrix_col, seed);
  } else {
    zero_poly(row->semantic);
  }
  zero_poly(row->b);
  polynomial_naive_mul_addto_torus(row->b, row->a, secret);
  copy_addto(row->b, row->semantic);
  copy_addto(row->b, row->noise);
  polynomial_torus_to_DFT(row->a_dft, row->a);
  polynomial_torus_to_DFT(row->b_dft, row->b);
}

static void phase(TorusPolynomial out, TorusPolynomial a, TorusPolynomial b,
    TorusPolynomial secret){
  TorusPolynomial prod = polynomial_new_torus_polynomial(secret->N);
  zero_poly(prod);
  polynomial_naive_mul_addto_torus(prod, a, secret);
  for(int i = 0; i < secret->N; i++) out->coeffs[i] = b->coeffs[i] - prod->coeffs[i];
  free_polynomial(prod);
}

static void compare_poly(TorusPolynomial a, TorusPolynomial b, uint64_t tol,
    uint64_t * mismatches, uint64_t * max_gap){
  for(int i = 0; i < a->N; i++){
    const uint64_t gap = abs_gap(a->coeffs[i], b->coeffs[i]);
    if(gap > tol) (*mismatches)++;
    if(gap > *max_gap) *max_gap = gap;
  }
}

static uint64_t max_abs_poly(TorusPolynomial p){
  uint64_t out = 0;
  for(int i = 0; i < p->N; i++){
    const uint64_t gap = abs_gap(p->coeffs[i], 0);
    if(gap > out) out = gap;
  }
  return out;
}

static uint64_t public_pattern_failures(Stage220EncryptedKey key){
  uint64_t failures = 0;
  for(int i = 0; i < key->row_count; i++){
    int nonzero = 0;
    for(int c = 0; c < key->N; c++){
      if(key->rows[i]->a->coeffs[c] != 0) {
        nonzero = 1;
        break;
      }
    }
    if(!nonzero) failures++;
    for(int j = i + 1; j < key->row_count; j++){
      int equal = 1;
      for(int c = 0; c < key->N; c++){
        if(key->rows[i]->a->coeffs[c] != key->rows[j]->a->coeffs[c]) {
          equal = 0;
          break;
        }
      }
      if(equal) failures++;
    }
  }
  return failures;
}

static void run_case(int r, int N, int seed){
  const uint64_t tolerance = 2048;
  const uint64_t noise_bound = (uint64_t)(2 * N * (r + 1));
  Stage220EncryptedKey key = key_alloc(r, N);
  TorusPolynomial * secrets = (TorusPolynomial *)safe_malloc(sizeof(TorusPolynomial) * r);
  TorusPolynomial row_phase = polynomial_new_torus_polynomial(N);
  TorusPolynomial dft_a = polynomial_new_torus_polynomial(N);
  TorusPolynomial dft_b = polynomial_new_torus_polynomial(N);
  TorusPolynomial dft_phase = polynomial_new_torus_polynomial(N);
  TorusPolynomial expected = polynomial_new_torus_polynomial(N);
  TorusPolynomial active_clean = polynomial_new_torus_polynomial(N);
  TorusPolynomial missing_active_clean = polynomial_new_torus_polynomial(N);
  TorusPolynomial random_dummy_clean = polynomial_new_torus_polynomial(N);
  uint64_t phase_mismatches = 0;
  uint64_t dft_mismatches = 0;
  uint64_t dummy_semantic_failures = 0;
  uint64_t max_dft_gap = 0;
  uint64_t max_noise_abs = 0;

  for(int q = 0; q < r; q++){
    secrets[q] = polynomial_new_torus_polynomial(N);
    fill_secret(secrets[q], q, seed);
  }
  for(int i = 0; i < key->row_count; i++){
    encrypt_row(key->rows[i], secrets[key->rows[i]->secret_lane], seed);
  }

  const uint64_t pattern_failures = public_pattern_failures(key);
  zero_poly(active_clean);
  zero_poly(missing_active_clean);
  zero_poly(random_dummy_clean);
  int skipped_active = 0;

  for(int i = 0; i < key->row_count; i++){
    Stage220EncryptedRow row = key->rows[i];
    zero_poly(expected);
    copy_addto(expected, row->semantic);
    copy_addto(expected, row->noise);
    phase(row_phase, row->a, row->b, secrets[row->secret_lane]);
    compare_poly(row_phase, expected, 0, &phase_mismatches, &max_dft_gap);

    polynomial_DFT_to_torus(dft_a, row->a_dft);
    polynomial_DFT_to_torus(dft_b, row->b_dft);
    phase(dft_phase, dft_a, dft_b, secrets[row->secret_lane]);
    compare_poly(dft_phase, expected, tolerance, &dft_mismatches, &max_dft_gap);

    if(row->role == STAGE220_ROLE_DUMMY_ZERO){
      for(int c = 0; c < N; c++){
        if(row->semantic->coeffs[c] != 0) dummy_semantic_failures++;
      }
      TorusPolynomial random_sem = polynomial_new_torus_polynomial(N);
      fill_random_dummy_semantic(random_sem, row->matrix_row, row->matrix_col, seed);
      copy_addto(random_dummy_clean, random_sem);
      free_polynomial(random_sem);
    } else {
      copy_addto(active_clean, row->semantic);
      if(skipped_active){
        copy_addto(missing_active_clean, row->semantic);
      } else {
        skipped_active = 1;
      }
    }
    const uint64_t row_noise = max_abs_poly(row->noise);
    if(row_noise > max_noise_abs) max_noise_abs = row_noise;
  }

  uint64_t dummy_gap = 0;
  uint64_t missing_active_negative_failures = 0;
  uint64_t random_dummy_negative_failures = 0;
  compare_poly(active_clean, missing_active_clean, 0, &missing_active_negative_failures, &dummy_gap);
  compare_poly(active_clean, random_dummy_clean, 0, &random_dummy_negative_failures, &dummy_gap);

  const int ok = pattern_failures == 0 && phase_mismatches == 0 &&
      dft_mismatches == 0 && dummy_semantic_failures == 0 &&
      missing_active_negative_failures > 0 && random_dummy_negative_failures > 0 &&
      max_noise_abs <= noise_bound;

  printf("KEYGEN,%s,%d,%d,%d,%d,%d,%d,%" PRIu64 ",%" PRIu64 ",%" PRIu64
         ",%" PRIu64 ",%" PRIu64 ",%" PRIu64 ",%" PRIu64 ",%" PRIu64
         ",%" PRIu64 ",%s\n",
      STAGE220_BACKEND, r, N, seed, key->row_count, key->active_count,
      key->dummy_count, pattern_failures, phase_mismatches, dft_mismatches,
      dummy_semantic_failures, missing_active_negative_failures,
      random_dummy_negative_failures, max_dft_gap, max_noise_abs, noise_bound,
      ok ? "PASS_ENCRYPTED_COMPACT_KEYGEN_PROTOTYPE" : "FAIL");

  const double active_over_dense = (double)key->active_count / (double)key->row_count;
  const double dummy_over_dense = (double)key->dummy_count / (double)key->row_count;
  const int layout_ok = key->row_count == (r + 1) * (r + 1) &&
      key->active_count + key->dummy_count == key->row_count;
  printf("LAYOUT,%d,%d,%d,%d,%d,%d,%.9f,%.9f,%s\n",
      r, N, key->row_count, key->active_count, key->dummy_count,
      key->row_count, active_over_dense, dummy_over_dense,
      layout_ok ? "PASS_ENCRYPTED_KEYGEN_LAYOUT" : "FAIL");

  for(int q = 0; q < r; q++) free_polynomial(secrets[q]);
  free(secrets);
  free_polynomial(row_phase);
  free_polynomial(dft_a);
  free_polynomial(dft_b);
  free_polynomial(dft_phase);
  free_polynomial(expected);
  free_polynomial(active_clean);
  free_polynomial(missing_active_clean);
  free_polynomial(random_dummy_clean);
  key_free(key);
}

int main(void){
  run_case(2, 1024, 0);
  run_case(2, 1024, 1);
  run_case(4, 1024, 0);
  run_case(4, 1024, 1);
  run_case(6, 1024, 0);
  run_case(6, 1024, 1);
  run_case(2, 2048, 0);
  run_case(4, 2048, 0);
  run_case(6, 2048, 0);
  return 0;
}
