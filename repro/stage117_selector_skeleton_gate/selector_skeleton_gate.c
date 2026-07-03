#include <inttypes.h>
#include <stdint.h>
#include <stdio.h>
#include <stdlib.h>

enum TermKind {
  TERM_SHARED = 0,
  TERM_LANE_MASK = 1,
  TERM_LANE_BODY = 2
};

typedef struct {
  enum TermKind kind;
  size_t lane;
  size_t source_row;
} SelectorTerm;

static SelectorTerm *build_terms(size_t r, size_t *term_count) {
  *term_count = 1 + 2 * r;
  SelectorTerm *terms = (SelectorTerm *)calloc(*term_count, sizeof(SelectorTerm));
  if (terms == NULL) {
    fprintf(stderr, "calloc failed\n");
    exit(2);
  }
  terms[0].kind = TERM_SHARED;
  terms[0].lane = (size_t)-1;
  terms[0].source_row = 0;
  for (size_t lane = 0; lane < r; lane++) {
    const size_t mask_idx = 1 + 2 * lane;
    const size_t body_idx = mask_idx + 1;
    terms[mask_idx].kind = TERM_LANE_MASK;
    terms[mask_idx].lane = lane;
    terms[mask_idx].source_row = 0;
    terms[body_idx].kind = TERM_LANE_BODY;
    terms[body_idx].lane = lane;
    terms[body_idx].source_row = lane + 1;
  }
  return terms;
}

static int validate(size_t r) {
  size_t term_count = 0;
  SelectorTerm *terms = build_terms(r, &term_count);
  uint64_t shared_terms = 0;
  uint64_t lane_mask_terms = 0;
  uint64_t lane_body_terms = 0;
  uint64_t offlane_body_terms = 0;
  uint64_t missing_lane_terms = 0;

  for (size_t i = 0; i < term_count; i++) {
    if (terms[i].kind == TERM_SHARED) {
      shared_terms++;
      if (terms[i].source_row != 0) missing_lane_terms++;
    } else if (terms[i].kind == TERM_LANE_MASK) {
      lane_mask_terms++;
      if (terms[i].lane >= r || terms[i].source_row != 0) missing_lane_terms++;
    } else if (terms[i].kind == TERM_LANE_BODY) {
      lane_body_terms++;
      if (terms[i].lane >= r) {
        missing_lane_terms++;
      } else if (terms[i].source_row != terms[i].lane + 1) {
        offlane_body_terms++;
      }
    } else {
      missing_lane_terms++;
    }
  }

  for (size_t lane = 0; lane < r; lane++) {
    uint64_t has_mask = 0;
    uint64_t has_body = 0;
    for (size_t i = 0; i < term_count; i++) {
      if (terms[i].lane == lane && terms[i].kind == TERM_LANE_MASK) has_mask++;
      if (terms[i].lane == lane && terms[i].kind == TERM_LANE_BODY) has_body++;
    }
    if (has_mask != 1 || has_body != 1) missing_lane_terms++;
  }

  const uint64_t dense_terms = (uint64_t)(r + 1) * (uint64_t)(r + 1);
  const uint64_t skeleton_terms = (uint64_t)term_count;
  const uint64_t selector_polys = 2 * skeleton_terms;
  const uint64_t accumulator_polys = 2 * (uint64_t)r;
  const double product_ratio = (double)dense_terms / (double)skeleton_terms;
  const int ok = shared_terms == 1 && lane_mask_terms == r && lane_body_terms == r &&
      offlane_body_terms == 0 && missing_lane_terms == 0 && product_ratio > 1.0;

  printf("%zu,%" PRIu64 ",%" PRIu64 ",%" PRIu64 ",%" PRIu64 ",%.6f,"
         "%" PRIu64 ",%" PRIu64 ",%" PRIu64 ",%" PRIu64 ",%" PRIu64 ",%s\n",
      r, dense_terms, skeleton_terms, selector_polys, accumulator_polys,
      product_ratio, shared_terms, lane_mask_terms, lane_body_terms,
      offlane_body_terms, missing_lane_terms, ok ? "PASS_SKELETON" : "FAIL");

  free(terms);
  return ok ? 0 : 1;
}

int main(void) {
  const size_t rs[] = {2, 4, 6, 8};
  int failures = 0;
  for (size_t i = 0; i < sizeof(rs) / sizeof(rs[0]); i++) {
    failures += validate(rs[i]);
  }
  return failures == 0 ? 0 : 1;
}
