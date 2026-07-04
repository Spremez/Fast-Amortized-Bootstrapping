
#include <stdio.h>
#include <stdint.h>
#include <stdlib.h>

typedef enum {
  STAGE252_FAMILY_DISTANCE = 1,
  STAGE252_FAMILY_COFF = 2,
  STAGE252_FAMILY_SIGN = 3
} Stage252Family;

typedef struct {
  int family;
  int step;
  int bit;
  int role;
} Stage252SelectorSlot;

typedef struct {
  int r;
  int h;
  int r_prec;
  int include_zero;
  int ternary;
  int distance_count;
  int coff_count;
  int sign_count;
  int total_count;
  Stage252SelectorSlot *distance;
  Stage252SelectorSlot *coff;
  Stage252SelectorSlot *sign;
} Stage252Key;

static uint64_t stage252_alloc_counter = 0;

static void *stage252_malloc(size_t bytes) {
  stage252_alloc_counter++;
  return calloc(1, bytes);
}

static void stage252_free(Stage252Key *key) {
  if (key == NULL) return;
  free(key->distance);
  free(key->coff);
  free(key->sign);
  free(key);
}

static Stage252Key *stage252_key_alloc(int r, int h, int r_prec, int include_zero, int ternary) {
  if (r <= 0 || h <= 0 || r_prec <= 0) return NULL;
  Stage252Key *key = (Stage252Key *)stage252_malloc(sizeof(*key));
  key->r = r;
  key->h = h;
  key->r_prec = r_prec;
  key->include_zero = include_zero ? 1 : 0;
  key->ternary = ternary ? 1 : 0;
  key->distance_count = (h + 1) * r_prec;
  key->coff_count = include_zero ? h : 0;
  key->sign_count = ternary ? h : 0;
  key->total_count = key->distance_count + key->coff_count + key->sign_count;
  key->distance = (Stage252SelectorSlot *)stage252_malloc(sizeof(Stage252SelectorSlot) * (size_t)key->distance_count);
  key->coff = key->coff_count ? (Stage252SelectorSlot *)stage252_malloc(sizeof(Stage252SelectorSlot) * (size_t)key->coff_count) : NULL;
  key->sign = key->sign_count ? (Stage252SelectorSlot *)stage252_malloc(sizeof(Stage252SelectorSlot) * (size_t)key->sign_count) : NULL;
  for (int step = 0; step < h + 1; step++) {
    for (int bit = 0; bit < r_prec; bit++) {
      int idx = step * r_prec + bit;
      key->distance[idx] = (Stage252SelectorSlot){STAGE252_FAMILY_DISTANCE, step, bit, 1};
    }
  }
  for (int step = 0; step < key->coff_count; step++) {
    key->coff[step] = (Stage252SelectorSlot){STAGE252_FAMILY_COFF, step, -1, 2};
  }
  for (int step = 0; step < key->sign_count; step++) {
    key->sign[step] = (Stage252SelectorSlot){STAGE252_FAMILY_SIGN, step, -1, 3};
  }
  return key;
}

static const Stage252SelectorSlot *stage252_selector_at(const Stage252Key *key, int family, int step, int bit) {
  if (key == NULL) return NULL;
  if (family == STAGE252_FAMILY_DISTANCE) {
    if (step < 0 || step > key->h || bit < 0 || bit >= key->r_prec) return NULL;
    return &key->distance[step * key->r_prec + bit];
  }
  if (family == STAGE252_FAMILY_COFF) {
    if (!key->include_zero || bit != -1 || step < 0 || step >= key->h) return NULL;
    return &key->coff[step];
  }
  if (family == STAGE252_FAMILY_SIGN) {
    if (!key->ternary || bit != -1 || step < 0 || step >= key->h) return NULL;
    return &key->sign[step];
  }
  return NULL;
}

static int stage252_role_mismatches(const Stage252Key *key) {
  int failures = 0;
  for (int step = 0; step < key->h + 1; step++) {
    for (int bit = 0; bit < key->r_prec; bit++) {
      const Stage252SelectorSlot *slot = stage252_selector_at(key, STAGE252_FAMILY_DISTANCE, step, bit);
      if (slot == NULL || slot->family != STAGE252_FAMILY_DISTANCE || slot->step != step || slot->bit != bit) failures++;
    }
  }
  for (int step = 0; step < key->h; step++) {
    const Stage252SelectorSlot *coff = stage252_selector_at(key, STAGE252_FAMILY_COFF, step, -1);
    if (key->include_zero) {
      if (coff == NULL || coff->family != STAGE252_FAMILY_COFF || coff->step != step) failures++;
    } else if (coff != NULL) failures++;
    const Stage252SelectorSlot *sign = stage252_selector_at(key, STAGE252_FAMILY_SIGN, step, -1);
    if (key->ternary) {
      if (sign == NULL || sign->family != STAGE252_FAMILY_SIGN || sign->step != step) failures++;
    } else if (sign != NULL) failures++;
  }
  return failures;
}

static int stage252_guard_failures(const Stage252Key *key) {
  int failures = 0;
  if (stage252_key_alloc(0, key->h, key->r_prec, key->include_zero, key->ternary) != NULL) failures++;
  if (stage252_key_alloc(key->r, 0, key->r_prec, key->include_zero, key->ternary) != NULL) failures++;
  if (stage252_key_alloc(key->r, key->h, 0, key->include_zero, key->ternary) != NULL) failures++;
  if (stage252_selector_at(key, STAGE252_FAMILY_DISTANCE, key->h + 1, 0) != NULL) failures++;
  if (stage252_selector_at(key, STAGE252_FAMILY_DISTANCE, 0, key->r_prec) != NULL) failures++;
  if (stage252_selector_at(key, STAGE252_FAMILY_COFF, key->h, -1) != NULL) failures++;
  if (stage252_selector_at(key, STAGE252_FAMILY_SIGN, key->h, -1) != NULL) failures++;
  if (stage252_selector_at(key, 99, 0, 0) != NULL) failures++;
  return failures;
}

static int stage252_hot_scan(const Stage252Key *key) {
  int total = 0;
  for (int i = 0; i < key->distance_count; i++) total += key->distance[i].role == 1;
  for (int i = 0; i < key->coff_count; i++) total += key->coff[i].role == 2;
  for (int i = 0; i < key->sign_count; i++) total += key->sign[i].role == 3;
  return total;
}

static void run_case(const char *name, int r, int h, int r_prec, int include_zero, int ternary) {
  Stage252Key *key = stage252_key_alloc(r, h, r_prec, include_zero, ternary);
  const int expected_distance = (h + 1) * r_prec;
  const int expected_coff = include_zero ? h : 0;
  const int expected_sign = ternary ? h : 0;
  const int expected_total = expected_distance + expected_coff + expected_sign;
  int role_mismatches = stage252_role_mismatches(key);
  int guard_failures = stage252_guard_failures(key);
  const uint64_t alloc_before = stage252_alloc_counter;
  int hot_total = stage252_hot_scan(key);
  const uint64_t hot_alloc_delta = stage252_alloc_counter - alloc_before;
  if (hot_total != expected_total) role_mismatches++;
  const int count_ok = key->distance_count == expected_distance &&
      key->coff_count == expected_coff &&
      key->sign_count == expected_sign &&
      key->total_count == expected_total;
  const int pass = count_ok && role_mismatches == 0 && guard_failures == 0 && hot_alloc_delta == 0;
  printf("%s,%d,%d,%d,%d,%d,%d,%d,%d,%d,%d,%d,%d,%u,%s\n",
      name, r, h, r_prec, include_zero, ternary,
      key->distance_count, key->coff_count, key->sign_count,
      key->total_count, expected_total, role_mismatches, guard_failures,
      (unsigned)hot_alloc_delta,
      pass ? "PASS_STAGE252_KEY_SKELETON" : "FAIL");
  stage252_free(key);
}

int main(void) {
  run_case("binary_target", 4, 39, 7, 0, 0);
  run_case("include_zero_target", 4, 39, 7, 1, 0);
  run_case("ternary_target", 4, 39, 7, 0, 1);
  run_case("include_zero_ternary_stress", 4, 39, 7, 1, 1);
  run_case("include_zero_r2", 2, 39, 7, 1, 0);
  run_case("ternary_r2", 2, 39, 7, 0, 1);
  run_case("added_2048_r4", 4, 42, 7, 1, 1);
  run_case("added_4096_r4", 4, 32, 8, 1, 1);
  return 0;
}
