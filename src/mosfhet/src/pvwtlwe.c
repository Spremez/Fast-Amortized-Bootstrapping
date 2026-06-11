#include "mosfhet.h"

PVW_TLWE pvwtlwe_alloc_sample(int n, int r){
  PVW_TLWE res;
  res = (PVW_TLWE) safe_malloc(sizeof(*res));
  res->a = (Torus *) safe_aligned_malloc(sizeof(Torus) * n);
  res->b = (Torus *) safe_aligned_malloc(sizeof(Torus) * r);
  res->n = n;
  res->r = r;
  return res;
}

PVW_TLWE * pvwtlwe_alloc_sample_array(int count, int n, int r){
  PVW_TLWE * res = (PVW_TLWE *) safe_malloc(sizeof(PVW_TLWE) * count);
  for (size_t i = 0; i < count; i++){
    res[i] = pvwtlwe_alloc_sample(n, r);
  }
  return res;
}

PVW_TLWE pvwtlwe_new_noiseless_trivial_sample(Torus * m, int n, int r){
  PVW_TLWE res = pvwtlwe_alloc_sample(n, r);
  memset(res->a, 0, sizeof(Torus) * n );
  memcpy(res->b, m, sizeof(Torus) * r);
  return res;
}

void pvwtlwe_noiseless_trivial_sample(PVW_TLWE out, Torus * m){
  memset(out->a, 0, sizeof(Torus) * out->n);
  memcpy(out->b, m, sizeof(Torus) * out->r);
}

void free_pvwtlwe_array(PVW_TLWE * p, int count){
  for (size_t i = 0; i < count; i++){
    free_pvwtlwe(p[i]);
  }  
  free(p);
}

void free_pvwtlwe(PVW_TLWE p){
  free(p->a);
  free(p->b);
  free(p);
}

void pvwtlwe_save_sample(FILE * fd, PVW_TLWE c){
  fwrite(c->a, sizeof(Torus), c->n, fd);
  fwrite(c->b, sizeof(Torus), c->r, fd);
}

PVW_TLWE pvwtlwe_load_new_sample(FILE * fd, int n, int r){
  PVW_TLWE res = pvwtlwe_alloc_sample(n, r);
  fread(res->a, sizeof(Torus), n, fd);
  fread(res->b, sizeof(Torus), r, fd);
  return res;
}

void pvwtlwe_load_sample(FILE * fd, PVW_TLWE c){
  fread(c->a, sizeof(Torus), c->n, fd);
  fread(c->b, sizeof(Torus), c->r, fd);
}

PVW_TLWE_Key pvwtlwe_alloc_key(int n, int r, double sigma){
  PVW_TLWE_Key res;
  res = (PVW_TLWE_Key) safe_malloc(sizeof(*res));
  res->n = n;
  res->r = r;
  res->sigma = sigma;
  res->s = (Integer **) safe_aligned_malloc(sizeof(Integer*) * r);
  for (size_t i = 0; i < r; i++){
    res->s[i] = (Integer *) safe_aligned_malloc(sizeof(Integer) * n);
  }
  return res;
}

PVW_TLWE_Key pvwtlwe_new_binary_key(int n, int r, double sigma){
  PVW_TLWE_Key res = pvwtlwe_alloc_key(n, r, sigma);
  for (size_t i = 0; i < r; i++){
    generate_random_bytes(n * sizeof(Integer), (uint8_t *) res->s[i]);
    for (size_t j = 0; j < n; j++){
      res->s[i][j] &= 1;
    }
  }
  return res;
}

PVW_TLWE_Key pvwtlwe_new_bounded_key(int n, int r, uint64_t bound, double sigma){
  PVW_TLWE_Key res = pvwtlwe_alloc_key(n, r, sigma);
  for (size_t i = 0; i < r; i++){
    generate_random_bytes(n * sizeof(Integer), (uint8_t *) res->s[i]);
    for (size_t j = 0; j < n; j++){
      res->s[i][j] &= (bound - 1);
      res->s[i][j] -= (bound >> 1) - 1;
    }
  }
  return res;
}

void pvwtlwe_save_key(FILE * fd, PVW_TLWE_Key key){
  fwrite(&key->n, sizeof(int), 1, fd);
  fwrite(&key->r, sizeof(int), 1, fd);
  fwrite(&key->sigma, sizeof(double), 1, fd);
  for (size_t i = 0; i < key->r; i++){
    for (size_t j = 0; j < key->n; j++){
      fwrite(&key->s[i][j], sizeof(Integer), 1, fd);
    }
  }
}

PVW_TLWE_Key pvwtlwe_load_new_key(FILE * fd){
  int n, r;
  double sigma;
  fread(&n, sizeof(int), 1, fd);
  fread(&r, sizeof(int), 1, fd);
  fread(&sigma, sizeof(double), 1, fd);
  PVW_TLWE_Key key = pvwtlwe_alloc_key(n, r, sigma);
  for (size_t i = 0; i < r; i++){
    for (size_t j = 0; j < n; j++){
      fread(&key->s[i][j], sizeof(Integer), 1, fd);
    }
  }
  return key;
}

void free_pvwtlwe_key(PVW_TLWE_Key key){
  for (size_t i = 0; i < key->r; i++){
    free(key->s[i]);
  }
  free(key->s);
  free(key);
}

void pvwtlwe_sample(PVW_TLWE out, Torus * m, PVW_TLWE_Key key){
  const int byte_size = sizeof(Torus) * out->n;
  generate_random_bytes(byte_size, (uint8_t *) out->a);
  memcpy(out->b, m, sizeof(Torus) * out->r);
  
  // internal product for each repetition
  for (size_t rep = 0; rep < out->r; rep++){
    for (size_t i = 0; i < out->n; i++){
      out->b[rep] += key->s[rep][i] * out->a[i];
    }
    out->b[rep] += double2torus(generate_normal_random(key->sigma));
  }
}

void pvwtlwe_copy(PVW_TLWE out, PVW_TLWE in){
  memcpy(out->a, in->a, sizeof(Torus) * in->n);
  memcpy(out->b, in->b, sizeof(Torus) * in->r);
}

PVW_TLWE pvwtlwe_new_sample(Torus * m, PVW_TLWE_Key key){
  PVW_TLWE res = pvwtlwe_alloc_sample(key->n, key->r);
  const int byte_size = sizeof(Torus) * res->n;
  generate_random_bytes(byte_size, (uint8_t *) res->a);
  memcpy(res->b, m, sizeof(Torus) * res->r);
  
  // internal product for each repetition
  for (size_t rep = 0; rep < res->r; rep++){
    for (size_t i = 0; i < res->n; i++){
      res->b[rep] += key->s[rep][i] * res->a[i];
    }
    res->b[rep] += double2torus(generate_normal_random(key->sigma));
  }
  return res;
}

void pvwtlwe_phase(Torus * out, PVW_TLWE c, PVW_TLWE_Key key){
  for (size_t rep = 0; rep < c->r; rep++){
    Torus sa = 0;
    for (size_t i = 0; i < c->n; i++){
      sa += key->s[rep][i] * c->a[i];
    }
    out[rep] = c->b[rep] - sa;
  }
}

void pvwtlwe_add(PVW_TLWE out, PVW_TLWE in1, PVW_TLWE in2){
  for (size_t i = 0; i < in1->n; i++){
    out->a[i] = in1->a[i] + in2->a[i];
  }
  for (size_t i = 0; i < in1->r; i++){
    out->b[i] = in1->b[i] + in2->b[i];
  }
}

void pvwtlwe_scale(PVW_TLWE out, PVW_TLWE in1, Torus in2){
  for (size_t i = 0; i < in1->n; i++){
    out->a[i] = in1->a[i] * in2;
  }
  for (size_t i = 0; i < in1->r; i++){
    out->b[i] = in1->b[i] * in2;
  }
}

void pvwtlwe_scale_addto(PVW_TLWE out, PVW_TLWE in1, Torus in2){
  for (size_t i = 0; i < in1->n; i++){
    out->a[i] += in1->a[i] * in2;
  }
  for (size_t i = 0; i < in1->r; i++){
    out->b[i] += in1->b[i] * in2;
  }
}

void pvwtlwe_scale_subto(PVW_TLWE out, PVW_TLWE in1, Torus in2){
  for (size_t i = 0; i < in1->n; i++){
    out->a[i] -= in1->a[i] * in2;
  }
  for (size_t i = 0; i < in1->r; i++){
    out->b[i] -= in1->b[i] * in2;
  }
}

void pvwtlwe_addto(PVW_TLWE out, PVW_TLWE in){
  pvwtlwe_add(out, out, in);
}

void pvwtlwe_sub(PVW_TLWE out, PVW_TLWE in1, PVW_TLWE in2){
  for (size_t i = 0; i < in1->n; i++){
    out->a[i] = in1->a[i] - in2->a[i];
  }
  for (size_t i = 0; i < in1->r; i++){
    out->b[i] = in1->b[i] - in2->b[i];
  }
}

void pvwtlwe_negate(PVW_TLWE out, PVW_TLWE in){
  for (size_t i = 0; i < in->n; i++){
    out->a[i] = -in->a[i];
  }
  for (size_t i = 0; i < in->r; i++){
    out->b[i] = -in->b[i];
  }
}

void pvwtlwe_subto(PVW_TLWE out, PVW_TLWE in){
  pvwtlwe_sub(out, out, in);
}

PVW_TLWE_KS_Key pvwtlwe_new_KS_key(PVW_TLWE_Key out_key, PVW_TLWE_Key in_key, int t, int base_bit){
  const int base = 1 << base_bit, bit_size = sizeof(Torus)*8;
  PVW_TLWE_KS_Key res;
  res = (PVW_TLWE_KS_Key) safe_malloc(sizeof(*res));
  res->base_bit = base_bit;
  res->t = t;
  res->n = in_key->n;
  res->r = in_key->r;

  res->s = (PVW_TLWE ***) safe_malloc(sizeof(PVW_TLWE**) * (in_key->n+in_key->r));
  for (size_t i = 0; i < in_key->n; i++){
    res->s[i] = (PVW_TLWE **) safe_malloc(sizeof(PVW_TLWE*) * t);
    for (size_t j = 0; j < t; j++){
      res->s[i][j] = (PVW_TLWE*) safe_malloc(sizeof(PVW_TLWE) * (base - 1));
      for (size_t k = 0; k < base - 1; k++){
        Torus *m;
        m = (Torus *) safe_malloc(sizeof(Torus)*in_key->r);
        for(size_t rep = 0; rep < in_key->r; rep++){
        m[rep] = in_key->s[rep][i] * (k + 1) * (1ULL << (bit_size - (j + 1) * base_bit));
        }
        res->s[i][j][k] = pvwtlwe_new_sample(m, out_key);
        free(m);
    }
  }
}
  return res;
}
/*
PVW_TLWE_KS_Key_m pvwtlwe_new_KS_key_no_precomp(PVW_TLWE_Key out_key, PVW_TLWE_Key in_key, int t, int base_bit){
  const int bit_size = sizeof(Torus)*8;
  PVW_TLWE_KS_Key_m res;
  res = (PVW_TLWE_KS_Key_m) safe_malloc(sizeof(*res));
  res->base_bit = base_bit;
  res->t = t;
  res->n = in_key->nr;

  res->s = (PVW_TLWE **) safe_malloc(sizeof(PVW_TLWE**) * in_key->nr);
  for (size_t i = 0; i < in_key->nr; i++){
    res->s[i] = (PVW_TLWE *) safe_malloc(sizeof(PVW_TLWE*) * t);
    for (size_t j = 0; j < t; j++){
      Torus m = in_key->s[0][i] * (1ULL << (bit_size - (j + 1) * base_bit));
      res->s[i][j] = pvwtlwe_new_sample(&m, out_key);
    }
  }
  return res;
}
*/

void free_pvwtlwe_ks_key(PVW_TLWE_KS_Key key){
  const int base = 1 << key->base_bit, t = key->t, n = key->n;
  for (size_t i = 0; i < n; i++){
    for (size_t j = 0; j < t; j++){
      for (size_t k = 0; k < base - 1; k++){
        free_pvwtlwe(key->s[i][j][k]);
      }
      free(key->s[i][j]);
    }
    free(key->s[i]);
  }
  free(key->s);
  free(key);
}

PVW_TLWE_KS_Key pvwtlwe_load_new_KS_key(FILE * fd, int n_outkey, int r_outkey){
  int n, t, base_bit;
  fread(&n, 1, sizeof(int), fd);
  fread(&t, 1, sizeof(int), fd);
  fread(&base_bit, 1, sizeof(int), fd);
  const int base = 1 << base_bit;

  PVW_TLWE_KS_Key res;
  res = (PVW_TLWE_KS_Key) safe_malloc(sizeof(*res));
  res->base_bit = base_bit;
  res->t = t;
  res->n = n;

  res->s = (PVW_TLWE ***) safe_malloc(sizeof(PVW_TLWE**) * n);
  for (size_t i = 0; i < n; i++){
    res->s[i] = (PVW_TLWE **) safe_malloc(sizeof(PVW_TLWE*) * t);
    for (size_t j = 0; j < t; j++){
      res->s[i][j] = (PVW_TLWE*) safe_malloc(sizeof(PVW_TLWE) * (base - 1));
      for (size_t k = 0; k < base - 1; k++){
        res->s[i][j][k] = pvwtlwe_load_new_sample(fd, n_outkey, r_outkey);
      }
    }
  }
  return res;
}

void pvwtlwe_save_KS_key(FILE * fd, PVW_TLWE_KS_Key key){
  fwrite(&key->n, 1, sizeof(int), fd);
  fwrite(&key->t, 1, sizeof(int), fd);
  fwrite(&key->base_bit, 1, sizeof(int), fd);
  
  for (size_t i = 0; i < key->n; i++){
    for (size_t j = 0; j < key->t; j++){
      for (size_t k = 0; k < (1 << key->base_bit) - 1; k++){
        pvwtlwe_save_sample(fd, key->s[i][j][k]);
      }
    }
  }
}

void pvwtlwe_keyswitch(PVW_TLWE out, PVW_TLWE in, PVW_TLWE_KS_Key ks_key){
  const int bit_size = sizeof(Torus)*8;
  const Torus prec_offset = 1ULL << (bit_size - (1 + ks_key->base_bit * ks_key->t));
  const Torus mask = (1ULL << ks_key->base_bit) - 1;
  
  pvwtlwe_noiseless_trivial_sample(out, in->b);
  for (size_t i = 0; i < in->n * in->r; i++) {
    const Torus ai = in->a[i] + prec_offset;
    for (size_t j = 0; j < ks_key->t; j++) {
      const Torus aij = (ai >> (bit_size - (j + 1) * ks_key->base_bit)) & mask;
      if (aij != 0) pvwtlwe_subto(out, ks_key->s[i][j][aij - 1]);
    }
  }
}
/*
void pvwtlwe_keyswitch_no_precomp(PVW_TLWE out, PVW_TLWE in, PVW_TLWE_KS_Key_m ks_key){
  const int bit_size = sizeof(Torus)*8;
  const Torus prec_offset = 1ULL << (bit_size - (1 + ks_key->base_bit * ks_key->t));
  const Torus mask = (1ULL << ks_key->base_bit) - 1;
  uint64_t offset = 1ULL << (bit_size - ks_key->t * ks_key->base_bit - 1);

  pvwtlwe_noiseless_trivial_sample(out, in->b);
  for (size_t i = 0; i < in->n * in->r; i++) {
    const Torus ai = in->a[i] + prec_offset;
    for (size_t j = 0; j < ks_key->t; j++) {
      const Torus aij = ((ai+offset) >> (bit_size - (j + 1) * ks_key->base_bit)) & mask;
      pvwtlwe_scale_subto(out, ks_key->s[i][j], aij);
    }
  }
}
*/
