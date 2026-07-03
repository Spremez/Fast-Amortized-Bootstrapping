
#include "mosfhet.h"
#include <inttypes.h>
#include <stdint.h>
#include <stdio.h>
#include <stdlib.h>

#ifndef STAGE219_BACKEND
#define STAGE219_BACKEND "unknown"
#endif

typedef enum {
  STAGE219_ROLE_ACTIVE = 1,
  STAGE219_ROLE_DUMMY_ZERO = 2
} Stage219Role;

typedef struct {
  int row;
  int col;
  int role;
  int may_skip;
} Stage219EquationRow;

static const Stage219EquationRow stage219_r2_rows[] = {
  {0, 0, STAGE219_ROLE_DUMMY_ZERO, 1},
  {0, 1, STAGE219_ROLE_ACTIVE, 0},
  {0, 2, STAGE219_ROLE_ACTIVE, 0},
  {1, 0, STAGE219_ROLE_ACTIVE, 0},
  {1, 1, STAGE219_ROLE_ACTIVE, 0},
  {1, 2, STAGE219_ROLE_ACTIVE, 0},
  {2, 0, STAGE219_ROLE_ACTIVE, 0},
  {2, 1, STAGE219_ROLE_ACTIVE, 0},
  {2, 2, STAGE219_ROLE_ACTIVE, 0},
};
static const Stage219EquationRow stage219_r4_rows[] = {
  {0, 0, STAGE219_ROLE_DUMMY_ZERO, 1},
  {0, 1, STAGE219_ROLE_ACTIVE, 0},
  {0, 2, STAGE219_ROLE_ACTIVE, 0},
  {0, 3, STAGE219_ROLE_ACTIVE, 0},
  {0, 4, STAGE219_ROLE_ACTIVE, 0},
  {1, 0, STAGE219_ROLE_ACTIVE, 0},
  {1, 1, STAGE219_ROLE_ACTIVE, 0},
  {1, 2, STAGE219_ROLE_ACTIVE, 0},
  {1, 3, STAGE219_ROLE_DUMMY_ZERO, 1},
  {1, 4, STAGE219_ROLE_DUMMY_ZERO, 1},
  {2, 0, STAGE219_ROLE_ACTIVE, 0},
  {2, 1, STAGE219_ROLE_DUMMY_ZERO, 1},
  {2, 2, STAGE219_ROLE_ACTIVE, 0},
  {2, 3, STAGE219_ROLE_ACTIVE, 0},
  {2, 4, STAGE219_ROLE_DUMMY_ZERO, 1},
  {3, 0, STAGE219_ROLE_ACTIVE, 0},
  {3, 1, STAGE219_ROLE_DUMMY_ZERO, 1},
  {3, 2, STAGE219_ROLE_DUMMY_ZERO, 1},
  {3, 3, STAGE219_ROLE_ACTIVE, 0},
  {3, 4, STAGE219_ROLE_ACTIVE, 0},
  {4, 0, STAGE219_ROLE_ACTIVE, 0},
  {4, 1, STAGE219_ROLE_ACTIVE, 0},
  {4, 2, STAGE219_ROLE_DUMMY_ZERO, 1},
  {4, 3, STAGE219_ROLE_DUMMY_ZERO, 1},
  {4, 4, STAGE219_ROLE_ACTIVE, 0},
};
static const Stage219EquationRow stage219_r6_rows[] = {
  {0, 0, STAGE219_ROLE_DUMMY_ZERO, 1},
  {0, 1, STAGE219_ROLE_ACTIVE, 0},
  {0, 2, STAGE219_ROLE_ACTIVE, 0},
  {0, 3, STAGE219_ROLE_ACTIVE, 0},
  {0, 4, STAGE219_ROLE_ACTIVE, 0},
  {0, 5, STAGE219_ROLE_ACTIVE, 0},
  {0, 6, STAGE219_ROLE_ACTIVE, 0},
  {1, 0, STAGE219_ROLE_ACTIVE, 0},
  {1, 1, STAGE219_ROLE_ACTIVE, 0},
  {1, 2, STAGE219_ROLE_ACTIVE, 0},
  {1, 3, STAGE219_ROLE_DUMMY_ZERO, 1},
  {1, 4, STAGE219_ROLE_DUMMY_ZERO, 1},
  {1, 5, STAGE219_ROLE_DUMMY_ZERO, 1},
  {1, 6, STAGE219_ROLE_DUMMY_ZERO, 1},
  {2, 0, STAGE219_ROLE_ACTIVE, 0},
  {2, 1, STAGE219_ROLE_DUMMY_ZERO, 1},
  {2, 2, STAGE219_ROLE_ACTIVE, 0},
  {2, 3, STAGE219_ROLE_ACTIVE, 0},
  {2, 4, STAGE219_ROLE_DUMMY_ZERO, 1},
  {2, 5, STAGE219_ROLE_DUMMY_ZERO, 1},
  {2, 6, STAGE219_ROLE_DUMMY_ZERO, 1},
  {3, 0, STAGE219_ROLE_ACTIVE, 0},
  {3, 1, STAGE219_ROLE_DUMMY_ZERO, 1},
  {3, 2, STAGE219_ROLE_DUMMY_ZERO, 1},
  {3, 3, STAGE219_ROLE_ACTIVE, 0},
  {3, 4, STAGE219_ROLE_ACTIVE, 0},
  {3, 5, STAGE219_ROLE_DUMMY_ZERO, 1},
  {3, 6, STAGE219_ROLE_DUMMY_ZERO, 1},
  {4, 0, STAGE219_ROLE_ACTIVE, 0},
  {4, 1, STAGE219_ROLE_DUMMY_ZERO, 1},
  {4, 2, STAGE219_ROLE_DUMMY_ZERO, 1},
  {4, 3, STAGE219_ROLE_DUMMY_ZERO, 1},
  {4, 4, STAGE219_ROLE_ACTIVE, 0},
  {4, 5, STAGE219_ROLE_ACTIVE, 0},
  {4, 6, STAGE219_ROLE_DUMMY_ZERO, 1},
  {5, 0, STAGE219_ROLE_ACTIVE, 0},
  {5, 1, STAGE219_ROLE_DUMMY_ZERO, 1},
  {5, 2, STAGE219_ROLE_DUMMY_ZERO, 1},
  {5, 3, STAGE219_ROLE_DUMMY_ZERO, 1},
  {5, 4, STAGE219_ROLE_DUMMY_ZERO, 1},
  {5, 5, STAGE219_ROLE_ACTIVE, 0},
  {5, 6, STAGE219_ROLE_ACTIVE, 0},
  {6, 0, STAGE219_ROLE_ACTIVE, 0},
  {6, 1, STAGE219_ROLE_ACTIVE, 0},
  {6, 2, STAGE219_ROLE_DUMMY_ZERO, 1},
  {6, 3, STAGE219_ROLE_DUMMY_ZERO, 1},
  {6, 4, STAGE219_ROLE_DUMMY_ZERO, 1},
  {6, 5, STAGE219_ROLE_DUMMY_ZERO, 1},
  {6, 6, STAGE219_ROLE_ACTIVE, 0},
};

typedef struct _Stage219CompactKey {
  DFT_Polynomial * rows;
  int * roles;
  int * may_skip;
  int row_count;
  int active_count;
  int dummy_count;
  int skippable_count;
  int r;
  int N;
} *Stage219CompactKey;

static uint64_t stage219_alloc_counter = 0;

static void * stage219_checked_malloc(size_t bytes){
  stage219_alloc_counter++;
  void * p = safe_malloc(bytes);
  return p;
}

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

static Torus small_torus(uint64_t salt, uint64_t row, uint64_t col, uint64_t idx){
  return (Torus)(mix64(salt, row, col, idx) % 31ULL);
}

static uint64_t abs_gap(Torus a, Torus b){
  const uint64_t d = (uint64_t)(a - b);
  if(d <= (1ULL << 63)) return d;
  return (~d) + 1ULL;
}

static const Stage219EquationRow * rows_for_r(int r, int * count){
  if(r == 2){
    *count = (int)(sizeof(stage219_r2_rows) / sizeof(stage219_r2_rows[0]));
    return stage219_r2_rows;
  }
  if(r == 4){
    *count = (int)(sizeof(stage219_r4_rows) / sizeof(stage219_r4_rows[0]));
    return stage219_r4_rows;
  }
  if(r == 6){
    *count = (int)(sizeof(stage219_r6_rows) / sizeof(stage219_r6_rows[0]));
    return stage219_r6_rows;
  }
  *count = 0;
  return NULL;
}

static Stage219CompactKey stage219_compact_key_alloc(int r, int N){
  int row_count = 0;
  const Stage219EquationRow * eq = rows_for_r(r, &row_count);
  if(eq == NULL || row_count <= 0) return NULL;
  Stage219CompactKey key = (Stage219CompactKey)stage219_checked_malloc(sizeof(*key));
  key->rows = (DFT_Polynomial *)stage219_checked_malloc(sizeof(DFT_Polynomial) * row_count);
  key->roles = (int *)stage219_checked_malloc(sizeof(int) * row_count);
  key->may_skip = (int *)stage219_checked_malloc(sizeof(int) * row_count);
  key->row_count = row_count;
  key->active_count = 0;
  key->dummy_count = 0;
  key->skippable_count = 0;
  key->r = r;
  key->N = N;
  for(int i = 0; i < row_count; i++){
    key->rows[i] = polynomial_new_DFT_polynomial(N);
    key->roles[i] = eq[i].role;
    key->may_skip[i] = eq[i].may_skip;
    if(eq[i].role == STAGE219_ROLE_ACTIVE) key->active_count++;
    if(eq[i].role == STAGE219_ROLE_DUMMY_ZERO) key->dummy_count++;
    if(eq[i].may_skip) key->skippable_count++;
  }
  return key;
}

static void stage219_compact_key_free(Stage219CompactKey key){
  if(key == NULL) return;
  for(int i = 0; i < key->row_count; i++) free_DFT_polynomial(key->rows[i]);
  free(key->rows);
  free(key->roles);
  free(key->may_skip);
  free(key);
}

static int stage219_set_row_from_torus(Stage219CompactKey key, int idx, TorusPolynomial row){
  if(key == NULL || idx < 0 || idx >= key->row_count) return -1;
  if(row == NULL) return -2;
  if(row->N != key->N) return -3;
  polynomial_torus_to_DFT(key->rows[idx], row);
  return 0;
}

static int stage219_hot_role_scan(Stage219CompactKey key, int * active, int * skip){
  int active_count = 0;
  int skip_count = 0;
  for(int i = 0; i < key->row_count; i++){
    if(key->roles[i] == STAGE219_ROLE_ACTIVE) active[active_count++] = i;
    if(key->may_skip[i]) skip[skip_count++] = i;
  }
  return active_count * 1000 + skip_count;
}

static void fill_poly(TorusPolynomial p, uint64_t salt, int row, int col){
  for(int i = 0; i < p->N; i++) p->coeffs[i] = small_torus(salt, (uint64_t)row, (uint64_t)col, (uint64_t)i);
}

static uint64_t pointer_failures(Stage219CompactKey key){
  uint64_t failures = 0;
  for(int i = 0; i < key->row_count; i++){
    if(key->rows[i] == NULL || key->rows[i]->coeffs == NULL) failures++;
    for(int j = i + 1; j < key->row_count; j++){
      if(key->rows[i]->coeffs == key->rows[j]->coeffs) failures++;
    }
  }
  return failures;
}

static void run_case(int r, int N){
  int eq_count = 0;
  const Stage219EquationRow * eq = rows_for_r(r, &eq_count);
  const uint64_t tolerance = 2048;
  Stage219CompactKey key = stage219_compact_key_alloc(r, N);
  TorusPolynomial tmp = polynomial_new_torus_polynomial(N);
  TorusPolynomial wrong = polynomial_new_torus_polynomial(N / 2);
  TorusPolynomial round = polynomial_new_torus_polynomial(N);
  uint64_t guard_failures = 0;
  uint64_t role_failures = 0;
  uint64_t roundtrip_mismatches = 0;
  uint64_t max_gap = 0;

  if(stage219_set_row_from_torus(key, -1, tmp) != -1) guard_failures++;
  if(stage219_set_row_from_torus(key, key->row_count, tmp) != -1) guard_failures++;
  if(stage219_set_row_from_torus(key, 0, NULL) != -2) guard_failures++;
  if(stage219_set_row_from_torus(key, 0, wrong) != -3) guard_failures++;

  int active_expected = 0;
  int dummy_expected = 0;
  int skip_expected = 0;
  for(int i = 0; i < eq_count; i++){
    if(eq[i].role == STAGE219_ROLE_ACTIVE) active_expected++;
    if(eq[i].role == STAGE219_ROLE_DUMMY_ZERO) dummy_expected++;
    if(eq[i].may_skip) skip_expected++;
    if(key->roles[i] != eq[i].role || key->may_skip[i] != eq[i].may_skip) role_failures++;
    fill_poly(tmp, 219000ULL + (uint64_t)N, eq[i].row, eq[i].col);
    if(stage219_set_row_from_torus(key, i, tmp) != 0) guard_failures++;
    polynomial_DFT_to_torus(round, key->rows[i]);
    for(int c = 0; c < N; c++){
      const uint64_t gap = abs_gap(tmp->coeffs[c], round->coeffs[c]);
      if(gap > tolerance) roundtrip_mismatches++;
      if(gap > max_gap) max_gap = gap;
    }
  }
  if(key->active_count != active_expected) role_failures++;
  if(key->dummy_count != dummy_expected) role_failures++;
  if(key->skippable_count != skip_expected) role_failures++;

  int * active = (int *)safe_malloc(sizeof(int) * key->row_count);
  int * skip = (int *)safe_malloc(sizeof(int) * key->row_count);
  const uint64_t alloc_before = stage219_alloc_counter;
  const int scan = stage219_hot_role_scan(key, active, skip);
  const uint64_t alloc_after = stage219_alloc_counter;
  const int active_scan = scan / 1000;
  const int skip_scan = scan % 1000;
  const uint64_t hot_alloc_delta = alloc_after - alloc_before;
  if(active_scan != active_expected) role_failures++;
  if(skip_scan != skip_expected) role_failures++;

  const uint64_t ptr_failures = pointer_failures(key);
  const int api_ok = ptr_failures == 0 && role_failures == 0 &&
      guard_failures == 0 && roundtrip_mismatches == 0 && hot_alloc_delta == 0;
  const double active_over_dense = (double)key->active_count / (double)key->row_count;
  const double dummy_over_dense = (double)key->dummy_count / (double)key->row_count;
  const int layout_ok = key->row_count == (r + 1) * (r + 1) &&
      key->dummy_count == key->skippable_count &&
      key->active_count + key->dummy_count == key->row_count;

  printf("API,%s,%d,%d,%d,%d,%d,%" PRIu64 ",%" PRIu64 ",%" PRIu64
         ",%" PRIu64 ",%" PRIu64 ",%" PRIu64 ",%" PRIu64 ",%s\n",
      STAGE219_BACKEND, r, N, key->row_count, key->active_count,
      key->dummy_count, ptr_failures, role_failures, guard_failures,
      roundtrip_mismatches, max_gap, tolerance, hot_alloc_delta,
      api_ok ? "PASS_COMPACT_KEY_API_SKELETON" : "FAIL");
  printf("LAYOUT,%d,%d,%d,%d,%d,%d,%.9f,%.9f,%s\n",
      r, N, key->row_count, key->active_count, key->dummy_count,
      key->skippable_count, active_over_dense, dummy_over_dense,
      layout_ok ? "PASS_ROLE_LAYOUT" : "FAIL");

  free(active);
  free(skip);
  free_polynomial(round);
  free_polynomial(wrong);
  free_polynomial(tmp);
  stage219_compact_key_free(key);
}

int main(void){
  run_case(2, 1024);
  run_case(4, 1024);
  run_case(6, 1024);
  run_case(2, 2048);
  run_case(4, 2048);
  run_case(6, 2048);
  return 0;
}
