#include "mosfhet.h"

PVW_TMLWE pvmtmlwe_alloc_new_sample(int k, int r, int N){
  PVW_TMLWE res;
  res = (PVW_TMLWE) safe_malloc(sizeof(*res));
  res->a = (TorusPolynomial *) safe_malloc(sizeof(TorusPolynomial) * k);
  for (size_t i = 0; i < k; i++){
    res->a[i] = polynomial_new_torus_polynomial(N);
  }
  res->b = (TorusPolynomial *) safe_malloc(sizeof(TorusPolynomial) * r);
  for (size_t i = 0; i < r; i++){
    res->b[i] = polynomial_new_torus_polynomial(N);
  }
  res->k = k;
  res->r = r;
  return res;
}

PVW_TMLWE * pvmtmlwe_alloc_new_sample_array(int count, int k, int r, int N){
  PVW_TMLWE * res;
  res = (PVW_TMLWE *) safe_malloc(sizeof(PVW_TMLWE) * count);
  for (size_t i = 0; i < count; i++){
    res[i] = pvmtmlwe_alloc_new_sample(k, r, N);
  }
  return res;
}

void pvmtmlwe_save_sample(FILE * fd, PVW_TMLWE c){
  for (size_t i = 0; i < c->k; i++){
    fwrite(c->a[i]->coeffs, sizeof(Torus), c->a[0]->N, fd);
  }
  for (size_t i = 0; i < c->r; i++){
    fwrite(c->b[i]->coeffs, sizeof(Torus), c->b[0]->N, fd);
  }
}

void pvmtmlwe_load_sample(FILE * fd, PVW_TMLWE c){
  const int k = c->k, r = c->r, N = c->b[0]->N;
  for (size_t i = 0; i < k; i++){
    fread(c->a[i]->coeffs, sizeof(Torus), N, fd);
  }
  for (size_t i = 0; i < r; i++){
    fread(c->b[i]->coeffs, sizeof(Torus), N, fd);
  }
}

PVW_TMLWE pvmtmlwe_load_new_sample(FILE * fd, int k, int r, int N){
  PVW_TMLWE res = pvmtmlwe_alloc_new_sample(k, r, N);
  pvmtmlwe_load_sample(fd, res);
  return res;
}

PVW_TMLWE_DFT * pvmtmlwe_alloc_new_DFT_sample_array(int count, int k, int r, int N){
  PVW_TMLWE_DFT * res;
  res = (PVW_TMLWE_DFT *) safe_malloc(sizeof(PVW_TMLWE_DFT) * count);
  for (size_t i = 0; i < count; i++){
    res[i] = pvmtmlwe_alloc_new_DFT_sample(k, r, N);
  }
  return res;
}

PVW_TMLWE_DFT pvmtmlwe_alloc_new_DFT_sample(int k, int r, int N){
  PVW_TMLWE_DFT res;
  res = (PVW_TMLWE_DFT) safe_malloc(sizeof(*res));
  res->a = (DFT_Polynomial *) safe_malloc(sizeof(DFT_Polynomial) * k);
  for (size_t i = 0; i < k; i++){
    res->a[i] = polynomial_new_DFT_polynomial(N);
  }
  res->b = (DFT_Polynomial *) safe_malloc(sizeof(DFT_Polynomial) * r);
  for (size_t i = 0; i < r; i++){
    res->b[i] = polynomial_new_DFT_polynomial(N);
  }
  res->k = k;
  res->r = r;
  return res;
}

void pvmtmlwe_save_DFT_sample(FILE * fd, PVW_TMLWE_DFT c){
  for (size_t i = 0; i < c->k; i++){
    fwrite(c->a[i]->coeffs, sizeof(double), c->a[0]->N, fd);
  }
  for (size_t i = 0; i < c->r; i++){
    fwrite(c->b[i]->coeffs, sizeof(double), c->b[0]->N, fd);
  }
}

PVW_TMLWE_DFT pvmtmlwe_load_new_DFT_sample(FILE * fd, int k, int r, int N){
  PVW_TMLWE_DFT res = pvmtmlwe_alloc_new_DFT_sample(k, r, N);
  pvmtmlwe_load_DFT_sample(fd, res);
  return res;
}

void pvmtmlwe_load_DFT_sample(FILE * fd, PVW_TMLWE_DFT c){
  const int k = c->k, r = c->r, N = c->b[0]->N;
  for (size_t i = 0; i < k; i++){
    fread(c->a[i]->coeffs, sizeof(double), N, fd);
  }
  for (size_t i = 0; i < r; i++){
    fread(c->b[i]->coeffs, sizeof(double), N, fd);
  }
}

void free_pvmtmlwe(void * p_v){
  const PVW_TMLWE p = (PVW_TMLWE) p_v;
  for (size_t i = 0; i < p->k; i++){
    free_polynomial(p->a[i]);
  }
  for (size_t i = 0; i < p->r; i++){
    free_polynomial(p->b[i]);
  }
  free(p->a);
  free(p->b);
  free(p);
}

void free_pvmtmlwe_DFT(void * p_v){
  const PVW_TMLWE_DFT p = (PVW_TMLWE_DFT) p_v;
  for (size_t i = 0; i < p->k; i++){
    free_DFT_polynomial(p->a[i]);
  }
  for (size_t i = 0; i < p->r; i++){
    free_DFT_polynomial(p->b[i]);
  }
  free(p->a);
  free(p->b);
  free(p);
}

void free_pvmtmlwe_array(void * p_v, int count){
  for (size_t i = 0; i < count; i++){
    free_pvmtmlwe(((void **)p_v)[i]);
  } 
  free(p_v);
}

PVW_TMLWE_Key pvmtmlwe_alloc_key(int N, int k, int r, double sigma){
  PVW_TMLWE_Key res;
  res = (PVW_TMLWE_Key) safe_malloc(sizeof(*res));
  res->k = k;
  res->r = r;
  res->sigma = sigma;
  res->s = (IntPolynomial **) safe_malloc(k*sizeof(IntPolynomial *));
  res->s_dft = (DFT_Polynomial **) safe_malloc(k*sizeof(DFT_Polynomial *));
  for (size_t i = 0; i < k; i++){
    res->s[i] = (IntPolynomial *) safe_malloc(r*sizeof(IntPolynomial));
    for (size_t j = 0; j < r; j++){
      res->s[i][j] = polynomial_new_torus_polynomial(N);  
    }
    res->s_dft[i] = (DFT_Polynomial *) safe_malloc(r*sizeof(DFT_Polynomial));
    for (size_t j = 0; j < r; j++){
      res->s_dft[i][j] = polynomial_new_DFT_polynomial(N);  
    }
  }
  return res;
}

// bound must be a power of 2
PVW_TMLWE_Key pvmtmlwe_new_bounded_key(int N, int k, int r, uint64_t bound, double sigma){
  PVW_TMLWE_Key res = pvmtmlwe_alloc_key(N, k, r, sigma);
  for (size_t i = 0; i < k; i++){
    for (size_t j = 0; j < r; j++){
      generate_random_bytes(N*sizeof(Torus), (uint8_t *) res->s[i][j]->coeffs);
      for (size_t l = 0; l < N; l++){
        res->s[i][j]->coeffs[l] &= (bound - 1);
        res->s[i][j]->coeffs[l] -= (bound >> 1) - 1;
      }  
    }
    for (size_t j = 0; j < r; j++){
      polynomial_torus_to_DFT(res->s_dft[i][j], res->s[i][j]);  
    }
  }
  return res;
}

PVW_TMLWE_Key pvmtmlwe_new_binary_key(int N, int k, int r, double sigma){
  return pvmtmlwe_new_bounded_key(N, k, r, 2, sigma);
}

/*Torus固定为uint64_t，有点小问题*/
void pvwtmlwe_gen_sparse_array(uint64_t * out, uint64_t size, uint64_t h, bool ternary, bool gaussian, double key_sigma){
  memset(out, 0, sizeof(uint64_t)*size);
  uint64_t hw = 0, val = 1, * rnd_buffer;
  const uint64_t buffer_size = h*10;
  rnd_buffer = (uint64_t *) safe_aligned_malloc(sizeof(uint64_t)*buffer_size);
  while(hw < h){
    generate_random_bytes(sizeof(uint64_t)*buffer_size, (uint8_t *) rnd_buffer); 
    uint64_t i = 0; 
    while (i < buffer_size && hw < h){
      const uint64_t idx = (rnd_buffer[i++] & (size - 1));
      if(out[idx]) continue;
      if(gaussian) val = (uint64_t)((int64_t) generate_normal_random(key_sigma));
      out[idx] = val;
      if(ternary) val *= -1;
      hw++;
    }
  }
  free(rnd_buffer);
}

PVW_TMLWE_Key pvmtmlwe_new_ternary_key(int N, int k, int r, int h, double sigma){
  PVW_TMLWE_Key res = pvmtmlwe_alloc_key(N, k, r, sigma);
  for (size_t i = 0; i < k; i++){
    for (size_t j = 0; j < r; j++){
      pvwtmlwe_gen_sparse_array(res->s[i][j]->coeffs, N, h, true, false, 0);
    }
    for (size_t j = 0; j < r; j++){
      polynomial_torus_to_DFT(res->s_dft[i][j], res->s[i][j]);
    }
  }
  return res;
}

PVW_TMLWE_Key pvmtmlwe_new_sparse_binary_key(int N, int k, int r, int h, double sigma){
  PVW_TMLWE_Key res = pvmtmlwe_alloc_key(N, k, r, sigma);
  for (size_t i = 0; i < k; i++){
    for (size_t j = 0; j < r; j++){
      pvwtmlwe_gen_sparse_array(res->s[i][j]->coeffs, N, h, false, false, 0);
    }
    for (size_t j = 0; j < r; j++){
      polynomial_torus_to_DFT(res->s_dft[i][j], res->s[i][j]);
    }
  }
  return res;
}

PVW_TMLWE_Key pvmtmlwe_new_sparse_gaussian_key(int N, int k, int r, int h, double key_sigma, double noise_sigma){
  PVW_TMLWE_Key res = pvmtmlwe_new_sparse_binary_key(N, k, r, h, noise_sigma);
  for (size_t i = 0; i < k; i++){
    for (size_t j = 0; j < r; j++){
      for (size_t l = 0; l < N; l++){
        if(res->s[i][j]->coeffs[l] == 1){
          res->s[i][j]->coeffs[l] = (uint64_t)((int64_t) generate_normal_random(key_sigma));
          if(!res->s[i][j]->coeffs[l]) res->s[i][j]->coeffs[l] = 1;
        }
      }
    }
    for (size_t j = 0; j < r; j++){
      polynomial_torus_to_DFT(res->s_dft[i][j], res->s[i][j]);
    }
  }
  return res;
}

// key_bound must be a power of 2
PVW_TMLWE_Key pvmtmlwe_new_sparse_generic_key(int N, int k, int r, int h, uint64_t key_bound, double noise_sigma){
  PVW_TMLWE_Key res = pvmtmlwe_new_sparse_binary_key(N, k, r, h, noise_sigma);
  for (size_t i = 0; i < k; i++){
    for (size_t j = 0; j < r; j++){
      for (size_t l = 0; l < N; l++){
        if(res->s[i][j]->coeffs[l] == 1){
          generate_random_bytes(sizeof(uint64_t), (uint8_t *) &res->s[i][j]->coeffs[l]);
          res->s[i][j]->coeffs[l] &= (key_bound - 1);
          res->s[i][j]->coeffs[l] -= (key_bound >> 1) - 1;
          if(!res->s[i][j]->coeffs[l]) res->s[i][j]->coeffs[l] = 1;
        }
      }
    }
    for (size_t j = 0; j < r; j++){
      polynomial_torus_to_DFT(res->s_dft[i][j], res->s[i][j]);
    }
  }
  return res;
}

PVW_TMLWE_Key pvmtmlwe_new_gaussian_key(int N, int k, int r, double key_sigma, double noise_sigma){
  PVW_TMLWE_Key res = pvmtmlwe_alloc_key(N, k, r, noise_sigma);
  for (size_t i = 0; i < k; i++){
    for (size_t j = 0; j < r; j++){
      for (size_t l = 0; l < N; l++){
        res->s[i][j]->coeffs[l] = (uint64_t)((int64_t) generate_normal_random(key_sigma));
      }
    }
    for (size_t j = 0; j < r; j++){
      polynomial_torus_to_DFT(res->s_dft[i][j], res->s[i][j]);
    }
  }
  return res;
}

void pvmtmlwe_save_key(FILE * fd, PVW_TMLWE_Key key){
  fwrite(&key->k, sizeof(int), 1, fd);
  fwrite(&key->r, sizeof(int), 1, fd);
  fwrite(&key->s[0][0]->N, sizeof(int), 1, fd);
  fwrite(&key->sigma, sizeof(double), 1, fd);
  for (size_t i = 0; i < key->k; i++){
    for (size_t j = 0; j < key->r; j++){
      fwrite(key->s[i][j]->coeffs, sizeof(Torus), key->s[0][0]->N, fd);
    }
  }
}

PVW_TMLWE_Key pvmtmlwe_load_new_key(FILE * fd){
  int k, r, N;
  double sigma;
  fread(&k, sizeof(int), 1, fd);
  fread(&r, sizeof(int), 1, fd);
  fread(&N, sizeof(int), 1, fd);
  fread(&sigma, sizeof(double), 1, fd);
  PVW_TMLWE_Key key = pvmtmlwe_alloc_key(N, k, r, sigma);
  for (size_t i = 0; i < key->k; i++){
    for (size_t j = 0; j < key->r; j++){
      fread(key->s[i][j]->coeffs, sizeof(Torus), key->s[0][0]->N, fd);
    }
    for (size_t j = 0; j < key->r; j++){
      polynomial_torus_to_DFT(key->s_dft[i][j], key->s[i][j]);  
    }
  }
  return key;
}

void free_pvmtmlwe_key(PVW_TMLWE_Key key){
  for (size_t i = 0; i < key->k; i++){
    for (size_t j = 0; j < key->r; j++){
      free_polynomial(key->s[i][j]);
      free_DFT_polynomial(key->s_dft[i][j]);
    }
    free(key->s[i]);
    free(key->s_dft[i]);
  }
  free(key->s);
  free(key->s_dft);
  free(key);
}

void pvmtmlwe_noiseless_trivial_sample(PVW_TMLWE out, TorusPolynomial * m){
  for (size_t i = 0; i < out->k; i++){
    memset(out->a[i]->coeffs, 0, sizeof(Torus)* out->b[0]->N);
  }
  for (size_t i = 0; i < out->r; i++){
    if(m != NULL) memcpy(out->b[i]->coeffs, m[i]->coeffs, sizeof(Torus) * out->b[0]->N);
    else memset(out->b[i]->coeffs, 0, sizeof(Torus) * out->b[0]->N);
  }
}

PVW_TMLWE pvmtmlwe_new_noiseless_trivial_sample(TorusPolynomial * m, int k, int r, int N){
  PVW_TMLWE res = pvmtmlwe_alloc_new_sample(k, r, N);
  pvmtmlwe_noiseless_trivial_sample(res, m);
  return res;
}

void pvmtmlwe_noiseless_trivial_DFT_sample(PVW_TMLWE_DFT out, DFT_Polynomial * m){
  for (size_t i = 0; i < out->k; i++){
    memset(out->a[i]->coeffs, 0, sizeof(double)* out->b[0]->N);
  }
  for (size_t i = 0; i < out->r; i++){
    if(m != NULL) memcpy(out->b[i]->coeffs, m[i]->coeffs, sizeof(double) * out->b[0]->N);
    else memset(out->b[i]->coeffs, 0, sizeof(double) * out->b[0]->N);
  }
}

PVW_TMLWE_DFT pvmtmlwe_new_noiseless_trivial_DFT_sample(DFT_Polynomial * m, int k, int r, int N){
  PVW_TMLWE_DFT res = pvmtmlwe_alloc_new_DFT_sample(k, r, N);
  pvmtmlwe_noiseless_trivial_DFT_sample(res, m);
  return res;
}

void pvmtmlwe_sample(PVW_TMLWE out, TorusPolynomial * m, PVW_TMLWE_Key key){
  const int N = key->s[0][0]->N, byte_size = sizeof(Torus) * N;

  for (size_t i = 0; i < key->k; i++){
    generate_random_bytes(byte_size, (uint8_t *) out->a[i]->coeffs);
  }

  // add error
  for (size_t i = 0; i < key->r; i++){
    generate_torus_normal_random_array(out->b[i]->coeffs, key->sigma, N);
  }

  // internal product
  for (size_t i = 0; i < key->k; i++){
    for (size_t j = 0; j < key->r; j++){
      polynomial_mul_addto_torus(out->b[j], out->a[i], key->s[i][j]);
    }
  }

  if(m != NULL){
    for (size_t i = 0; i < key->r; i++){
      for (size_t j = 0; j < m[i]->N; j++){
        out->b[i]->coeffs[j] += m[i]->coeffs[j];
      }
    }
  }
}

PVW_TMLWE pvmtmlwe_new_sample(TorusPolynomial * m, PVW_TMLWE_Key key){
  PVW_TMLWE res = pvmtmlwe_alloc_new_sample(key->k, key->r, key->s[0][0]->N);
  pvmtmlwe_sample(res, m, key);
  return res;
}

void pvmtmlwe_phase(TorusPolynomial * out, PVW_TMLWE in, PVW_TMLWE_Key key){
  const int N = key->s[0][0]->N, k = in->k, r = in->r, byte_size = sizeof(Torus) * N;
  for (size_t i = 0; i < r; i++){
    memset(out[i]->coeffs, 0, byte_size);
    for (size_t j = 0; j < k; j++){
      polynomial_mul_addto_torus(out[i], in->a[j], key->s[j][i]);
    }
    polynomial_sub_torus_polynomials(out[i], in->b[i], out[i]);
  }
}

void print_pvmtmlwe_msg(PVW_TMLWE in, uint64_t prec, PVW_TMLWE_Key key){
  const uint64_t N = in->b[0]->N, r = in->r;
  TorusPolynomial * tmp = (TorusPolynomial *) safe_malloc(sizeof(TorusPolynomial) * r);
  for (size_t i = 0; i < r; i++){
    tmp[i] = polynomial_new_torus_polynomial(N);
  }
  pvmtmlwe_phase(tmp, in, key);
  for (size_t i = 0; i < r; i++){
    printf("Message %zu: ", i);
    for (size_t j = 0; j < N - 1; j++){
      printf("%lu, ", torus2int(tmp[i]->coeffs[j], prec));
    }
    printf("%lu\n", torus2int(tmp[i]->coeffs[N-1], prec));
  }
  for (size_t i = 0; i < r; i++){
    free_polynomial(tmp[i]);
  }
  free(tmp);
}

uint64_t _debug_pvmtmlwe_decrypt_exp_sample(PVW_TMLWE c, uint64_t prec, PVW_TMLWE_Key key){
  const uint64_t N = key->s[0][0]->N, r = key->r;
  const Torus delta = (1ULL << (sizeof(Torus)*8 - prec - 1));
  TorusPolynomial * poly = (TorusPolynomial *) safe_malloc(sizeof(TorusPolynomial) * r);
  for (size_t i = 0; i < r; i++){
    poly[i] = polynomial_new_torus_polynomial(N);
  }
  pvmtmlwe_phase(poly, c, key);
  int resIdx = -1;
  for (size_t i = 0; i < r; i++){
    for (int j = 0; j < N; j++){
      if((poly[i]->coeffs[j] < -delta) && (poly[i]->coeffs[j] > delta)){
        if(resIdx != -1){
          resIdx = -1;
          break;
        }
        resIdx = j;
      }
    }
    if(resIdx != -1) break;
  }
  for (size_t i = 0; i < r; i++){
    free_polynomial(poly[i]);
  }
  free(poly);
  return resIdx;
}

void pvmtmlwe_DFT_phase(TorusPolynomial * out, PVW_TMLWE_DFT in, PVW_TMLWE_Key key){
  const int N = out[0]->N, k = in->k, r = in->r, byte_size = sizeof(Torus) * N;
  DFT_Polynomial * tmp = (DFT_Polynomial *) safe_malloc(sizeof(DFT_Polynomial) * r);
  for (size_t i = 0; i < r; i++){
    tmp[i] = polynomial_new_DFT_polynomial(N);
    memset(tmp[i]->coeffs, 0, byte_size);
    for (size_t j = 0; j < k; j++){
      polynomial_mul_addto_DFT(tmp[i], in->a[j], key->s_dft[j][i]);
    }
    polynomial_sub_DFT_polynomials(tmp[i], in->b[i], tmp[i]);
    polynomial_DFT_to_torus(out[i], tmp[i]);
    free_DFT_polynomial(tmp[i]);
  }
  free(tmp);
}

#ifndef AVX512_OPT

void pvmtmlwe_add(PVW_TMLWE out, PVW_TMLWE in1, PVW_TMLWE in2){
  for (size_t i = 0; i < in1->k; i++){
    polynomial_add_torus_polynomials(out->a[i], in1->a[i], in2->a[i]);
  }
  for (size_t i = 0; i < in1->r; i++){
    polynomial_add_torus_polynomials(out->b[i], in1->b[i], in2->b[i]);
  }
}

#else 
void pvmtmlwe_add(PVW_TMLWE out, PVW_TMLWE in1, PVW_TMLWE in2){
  __m512i * a1 = (__m512i *) in1->a[0]->coeffs;
  __m512i * b1 = (__m512i *) in2->a[0]->coeffs;
  __m512i * c1 = (__m512i *) out->a[0]->coeffs;
  for (size_t i = 0; i < in2->b[0]->N/8; i++){
    c1[i] = _mm512_add_epi64(a1[i], b1[i]);
  }
  for (size_t i = 0; i < in1->r; i++){
    __m512i * a2 = (__m512i *) in1->b[i]->coeffs;
    __m512i * b2 = (__m512i *) in2->b[i]->coeffs;
    __m512i * c2 = (__m512i *) out->b[i]->coeffs;
    for (size_t j = 0; j < in2->b[0]->N/8; j++){
      c2[j] = _mm512_add_epi64(a2[j], b2[j]);
    }
  }
}
#endif


void pvmtmlwe_copy(PVW_TMLWE out, PVW_TMLWE in){
  for (size_t i = 0; i < in->k; i++){
    polynomial_copy_torus_polynomial(out->a[i], in->a[i]);
  }
  for (size_t i = 0; i < in->r; i++){
    polynomial_copy_torus_polynomial(out->b[i], in->b[i]);
  }
}


void pvmtmlwe_negate(PVW_TMLWE out, PVW_TMLWE in){
  for (size_t i = 0; i < in->k; i++){
    polynomial_negate_torus_polynomial(out->a[i], in->a[i]);
  }
  for (size_t i = 0; i < in->r; i++){
    polynomial_negate_torus_polynomial(out->b[i], in->b[i]);
  }
}

void pvmtmlwe_DFT_copy(PVW_TMLWE_DFT out, PVW_TMLWE_DFT in){
  for (size_t i = 0; i < in->k; i++){
    polynomial_copy_DFT_polynomial(out->a[i], in->a[i]);
  }
  for (size_t i = 0; i < in->r; i++){
    polynomial_copy_DFT_polynomial(out->b[i], in->b[i]);
  }
}

void pvmtmlwe_addto(PVW_TMLWE out, PVW_TMLWE in){
  pvmtmlwe_add(out, out, in);
}

void pvmtmlwe_DFT_add(PVW_TMLWE_DFT out, PVW_TMLWE_DFT in1,  PVW_TMLWE_DFT in2){
  for (size_t i = 0; i < in1->k; i++){
    polynomial_add_DFT_polynomials(out->a[i], in1->a[i], in2->a[i]);
  }
  for (size_t i = 0; i < in1->r; i++){
    polynomial_add_DFT_polynomials(out->b[i], in1->b[i], in2->b[i]);
  }
}

void pvmtmlwe_DFT_sub(PVW_TMLWE_DFT out, PVW_TMLWE_DFT in1,  PVW_TMLWE_DFT in2){
  for (size_t i = 0; i < in1->k; i++){
    polynomial_sub_DFT_polynomials(out->a[i], in1->a[i], in2->a[i]);
  }
  for (size_t i = 0; i < in1->r; i++){
    polynomial_sub_DFT_polynomials(out->b[i], in1->b[i], in2->b[i]);
  }
}

void pvmtmlwe_DFT_addto(PVW_TMLWE_DFT out, PVW_TMLWE_DFT in){
  pvmtmlwe_DFT_add(out, out, in);
}

#ifndef AVX512_OPT

void pvmtmlwe_sub(PVW_TMLWE out, PVW_TMLWE in1, PVW_TMLWE in2){
  for (size_t i = 0; i < in1->k; i++){
    polynomial_sub_torus_polynomials(out->a[i], in1->a[i], in2->a[i]);
  }
  for (size_t i = 0; i < in1->r; i++){
    polynomial_sub_torus_polynomials(out->b[i], in1->b[i], in2->b[i]);
  }
}

#else 
void pvmtmlwe_sub(PVW_TMLWE out, PVW_TMLWE in1, PVW_TMLWE in2){
  __m512i * a1 = (__m512i *) in1->a[0]->coeffs;
  __m512i * b1 = (__m512i *) in2->a[0]->coeffs;
  __m512i * c1 = (__m512i *) out->a[0]->coeffs;
  for (size_t i = 0; i < in2->b[0]->N/8; i++){
    c1[i] = _mm512_sub_epi64(a1[i], b1[i]);
  }
  for (size_t i = 0; i < in1->r; i++){
    __m512i * a2 = (__m512i *) in1->b[i]->coeffs;
    __m512i * b2 = (__m512i *) in2->b[i]->coeffs;
    __m512i * c2 = (__m512i *) out->b[i]->coeffs;
    for (size_t j = 0; j < in2->b[0]->N/8; j++){
      c2[j] = _mm512_sub_epi64(a2[j], b2[j]);
    }
  }
}
#endif
void pvmtmlwe_subto(PVW_TMLWE out, PVW_TMLWE in){
  pvmtmlwe_sub(out, out, in);
}

void pvmtmlwe_DFT_mul_by_polynomial(PVW_TMLWE_DFT out, PVW_TMLWE_DFT in, DFT_Polynomial in2){
  const int k = in->k, r = in->r;
  for (size_t i = 0; i < k; i++){
    polynomial_mul_DFT(out->a[i], in->a[i], in2);
  }
  for (size_t i = 0; i < r; i++){
    polynomial_mul_DFT(out->b[i], in->b[i], in2);
  }
}

void pvmtmlwe_DFT_mul_addto_by_polynomial(PVW_TMLWE_DFT out, PVW_TMLWE_DFT in, DFT_Polynomial in2){
  const int k = in->k, r = in->r;
  for (size_t i = 0; i < k; i++){
    polynomial_mul_addto_DFT(out->a[i], in->a[i], in2);
  }
  for (size_t i = 0; i < r; i++){
    polynomial_mul_addto_DFT(out->b[i], in->b[i], in2);
  }
}

void pvmtmlwe_mul_by_xai(PVW_TMLWE out, PVW_TMLWE in, int a){
  const int k = in->k, r = in->r;
  for (size_t i = 0; i < k; i++){
    torus_polynomial_mul_by_xai(out->a[i], in->a[i], a);
  }
  for (size_t i = 0; i < r; i++){
    torus_polynomial_mul_by_xai(out->b[i], in->b[i], a);
  }
}

void pvmtmlwe_mul_by_xai_addto(PVW_TMLWE out, PVW_TMLWE in, int a){
  const int k = in->k, r = in->r;
  for (size_t i = 0; i < k; i++){
    torus_polynomial_mul_by_xai_addto(out->a[i], in->a[i], a);
  }
  for (size_t i = 0; i < r; i++){
    torus_polynomial_mul_by_xai_addto(out->b[i], in->b[i], a);
  }
}

void pvmtmlwe_mul_by_xai_minus_1(PVW_TMLWE out, PVW_TMLWE in, int a){
  const int k = in->k, r = in->r;
  for (size_t i = 0; i < k; i++){
    torus_polynomial_mul_by_xai_minus_1(out->a[i], in->a[i], a);
  }
  for (size_t i = 0; i < r; i++){
    torus_polynomial_mul_by_xai_minus_1(out->b[i], in->b[i], a);
  }
}

void pvmtmlwe_extract_pvmtlwe_key(PVW_TLWE_Key out, PVW_TMLWE_Key in){
  const int N = in->s[0][0]->N, k = in->k, r = in->r;
  for (size_t i = 0; i < k; i++){
    for (size_t j = 0; j < r; j++){
      for (size_t l = 0; l < N; l++){
        out->s[j][i*N+l] = in->s[i][j]->coeffs[l];
      }
    }
  }
}

void pvmtmlwe_extract_pvmtlwe(PVW_TLWE out, PVW_TMLWE in, int idx){
  const int N = in->b[0]->N, k = in->k, r = in->r;
   for (size_t i = 0; i < k; i++){
    for (size_t j = 0; j <= idx; j++){
      out->a[i*N + j] = in->a[i]->coeffs[idx - j];
    }
    for (size_t j = idx + 1; j < N; j++){
      out->a[i*N + j] = -in->a[i]->coeffs[N + idx - j];
    }
  }
  for (size_t i = 0; i < r; i++){
    out->b[i] = in->b[i]->coeffs[idx];
  }
}

void pvmtmlwe_extract_pvmtlwe_addto(PVW_TLWE out, PVW_TMLWE in, int idx){
  const int N = in->b[0]->N, k = in->k, r = in->r;
   for (size_t i = 0; i < k; i++){
    for (size_t j = 0; j <= idx; j++){
      out->a[i*N + j] += in->a[i]->coeffs[idx - j];
    }
    for (size_t j = idx + 1; j < N; j++){
      out->a[i*N + j] += -in->a[i]->coeffs[N + idx - j];
    }
  }
  for (size_t i = 0; i < r; i++){
    out->b[i] += in->b[i]->coeffs[idx];
  }
}

void pvmtmlwe_extract_pvmtlwe_subto(PVW_TLWE out, PVW_TMLWE in, int idx){
  const int N = in->b[0]->N, k = in->k, r = in->r;
   for (size_t i = 0; i < k; i++){
    for (size_t j = 0; j <= idx; j++){
      out->a[i*N + j] -= in->a[i]->coeffs[idx - j];
    }
    for (size_t j = idx + 1; j < N; j++){
      out->a[i*N + j] -= -in->a[i]->coeffs[N + idx - j];
    }
  }
  for (size_t i = 0; i < r; i++){
    out->b[i] -= in->b[i]->coeffs[idx];
  }
}

/*为何分为两段抽取，且后半段从后向前抽，抽了后还要取反*/
void pvmtmlwe_mv_extract_pvmtlwe(PVW_TLWE * out, PVW_TMLWE in, int amount){
  const int N = in->b[0]->N;
  for (size_t i = 0; i < amount/2; i++){
    pvmtmlwe_extract_pvmtlwe(out[i], in, i);
  }
  for (size_t i = amount/2; i < amount; i++){
    pvmtmlwe_extract_pvmtlwe(out[i], in, N - 1 - (i - amount/2));
    pvwtlwe_negate(out[i], out[i]);
  }
}

void pvmtmlwe_mv_extract_pvmtlwe_scaling(PVW_TLWE out, PVW_TMLWE in, int scale){
  const int N = in->b[0]->N, amount = scale;
  pvmtmlwe_extract_pvmtlwe(out, in, amount/2);
  for (size_t i = amount/2 + 1; i < amount; i++){
    pvmtmlwe_extract_pvmtlwe_subto(out, in, N - 1 - (i - amount/2));
  }
  for (size_t i = 0; i < amount/2; i++){
    pvmtmlwe_extract_pvmtlwe_addto(out, in, i);
  }
}

void pvmtmlwe_mv_extract_pvmtlwe_scaling_addto(PVW_TLWE out, PVW_TMLWE in, int scale){
  const int N = in->b[0]->N, amount = scale;
  for (size_t i = amount/2; i < amount; i++){
    pvmtmlwe_extract_pvmtlwe_subto(out, in, N - 1 - (i - amount/2));
  }
  for (size_t i = 0; i < amount/2; i++){
    pvmtmlwe_extract_pvmtlwe_addto(out, in, i);
  }
}

void pvmtmlwe_mv_extract_pvmtlwe_scaling_subto(PVW_TLWE out, PVW_TMLWE in, int scale){
  const int N = in->b[0]->N, amount = scale;
  for (size_t i = amount/2; i < amount; i++){
    pvmtmlwe_extract_pvmtlwe_addto(out, in, N - 1 - (i - amount/2));
  }
  for (size_t i = 0; i < amount/2; i++){
    pvmtmlwe_extract_pvmtlwe_subto(out, in, i);
  }
}

void pvmtmlwe_to_DFT(PVW_TMLWE_DFT out, PVW_TMLWE in){
  for (size_t i = 0; i < in->k; i++){
    polynomial_torus_to_DFT(out->a[i], in->a[i]);
  }
  for (size_t i = 0; i < in->r; i++){
    polynomial_torus_to_DFT(out->b[i], in->b[i]);
  }
}

void pvmtmlwe_from_DFT(PVW_TMLWE out, PVW_TMLWE_DFT in){
  for (size_t i = 0; i < in->k; i++){
    polynomial_DFT_to_torus(out->a[i], in->a[i]);
  }
  for (size_t i = 0; i < in->r; i++){
    polynomial_DFT_to_torus(out->b[i], in->b[i]);
  }
}

PVW_TMLWE_KS_Key pvmtmlwe_new_KS_key(PVW_TMLWE_Key out_key, PVW_TMLWE_Key in_key, int t, int base_bit){
  const int bit_size = sizeof(Torus) * 8;
  const int N_out = out_key->s[0][0]->N;
  const int N_in = in_key->s[0][0]->N;
  assert(N_out == N_in);
  assert(out_key->r == in_key->r);

  PVW_TMLWE_KS_Key res = (PVW_TMLWE_KS_Key) safe_malloc(sizeof(*res));
  res->base_bit = base_bit;
  res->t = t;
  res->k = in_key->k;

  TorusPolynomial * dec_poly = polynomial_new_array_of_torus_polynomials(N_in, in_key->r);
  PVW_TMLWE tmp = pvmtmlwe_alloc_new_sample(out_key->k, out_key->r, N_out);

  res->s = (PVW_TMLWE_DFT **) safe_malloc(sizeof(PVW_TMLWE_DFT *) * in_key->k);
  for (size_t i = 0; i < (size_t) in_key->k; i++){
    res->s[i] = (PVW_TMLWE_DFT *) safe_malloc(sizeof(PVW_TMLWE_DFT) * t);
    for (size_t j = 0; j < (size_t) t; j++){
      const Torus scale = 1ULL << (bit_size - (j + 1) * base_bit);
      for (size_t lane = 0; lane < (size_t) in_key->r; lane++){
        for (size_t coeff = 0; coeff < (size_t) N_in; coeff++){
          dec_poly[lane]->coeffs[coeff] = in_key->s[i][lane]->coeffs[coeff] * scale;
        }
      }
      pvmtmlwe_sample(tmp, dec_poly, out_key);
      res->s[i][j] = pvmtmlwe_alloc_new_DFT_sample(out_key->k, out_key->r, N_out);
      pvmtmlwe_to_DFT(res->s[i][j], tmp);
    }
  }

  free_pvmtmlwe(tmp);
  free_array_of_polynomials(dec_poly, in_key->r);
  return res;
}

PVW_TMLWE_KS_Key pvmtmlwe_new_automorphism_KS_key(PVW_TMLWE_Key key, uint64_t gen, int t, int base_bit){
  const int N = key->s[0][0]->N;
  PVW_TMLWE_Key key2 = pvmtmlwe_alloc_key(N, key->k, key->r, key->sigma);
  for (size_t i = 0; i < (size_t) key->k; i++){
    for (size_t lane = 0; lane < (size_t) key->r; lane++){
      polynomial_permute(key2->s[i][lane], key->s[i][lane], gen);
      polynomial_torus_to_DFT(key2->s_dft[i][lane], key2->s[i][lane]);
    }
  }
  PVW_TMLWE_KS_Key res = pvmtmlwe_new_KS_key(key, key2, t, base_bit);
  free_pvmtmlwe_key(key2);
  return res;
}

void free_pvmtmlwe_ks_key(PVW_TMLWE_KS_Key key){
  for (size_t i = 0; i < (size_t) key->k; i++){
    for (size_t j = 0; j < (size_t) key->t; j++){
      free_pvmtmlwe_DFT(key->s[i][j]);
    }
    free(key->s[i]);
  }
  free(key->s);
  free(key);
}

void pvmtmlwe_keyswitch(PVW_TMLWE out, PVW_TMLWE in, PVW_TMLWE_KS_Key ks_key){
  const int N = out->b[0]->N;
  assert(out->k == ks_key->s[0][0]->k);
  assert(out->r == ks_key->s[0][0]->r);
  assert(out->b[0]->N == ks_key->s[0][0]->b[0]->N);

  TorusPolynomial dec_in_a = polynomial_new_torus_polynomial(N);
  DFT_Polynomial tmp = polynomial_new_DFT_polynomial(N);
  PVW_TMLWE_DFT acc = pvmtmlwe_alloc_new_DFT_sample(out->k, out->r, N);
  PVW_TMLWE as = pvmtmlwe_alloc_new_sample(out->k, out->r, N);

  pvmtmlwe_noiseless_trivial_DFT_sample(acc, NULL);
  for (size_t i = 0; i < (size_t) in->k; i++){
    for (size_t j = 0; j < (size_t) ks_key->t; j++){
      polynomial_decompose_i(dec_in_a, in->a[i], ks_key->base_bit, ks_key->t, j);
      polynomial_torus_to_DFT(tmp, dec_in_a);
      pvmtmlwe_DFT_mul_addto_by_polynomial(acc, ks_key->s[i][j], tmp);
    }
  }
  pvmtmlwe_from_DFT(as, acc);
  pvmtmlwe_noiseless_trivial_sample(out, in->b);
  pvmtmlwe_subto(out, as);

  free_pvmtmlwe(as);
  free_pvmtmlwe_DFT(acc);
  free_polynomial(tmp);
  free_polynomial(dec_in_a);
}

/*We do NOT use this function in our new algorithm!*/
void pvmtmlwe_decompose(TorusPolynomial * out, PVW_TMLWE in, int Bg_bit, int l){
  const int k = in->k, r = in->r, N = in->b[0]->N;
  const uint64_t half_Bg = (1ULL << (Bg_bit - 1));
  const uint64_t h_mask = (1ULL << Bg_bit) - 1;
  const uint64_t word_size = sizeof(Torus)*8;

  uint64_t offset = 0;
  for (size_t i = 0; i < l; i++){
    offset += (1ULL << (word_size - i * Bg_bit - 1));
  }
  
  for (size_t i = 0; i < l; i++) {
    const uint64_t h_bit = word_size - (i + 1) * Bg_bit;
    for (size_t j = 0; j < k; j++){
      for (size_t c = 0; c < N; c++){
        const uint64_t coeff_off = in->a[j]->coeffs[c] + offset;
        out[j*l + i]->coeffs[c] = ((coeff_off>>h_bit) & h_mask) - half_Bg;
      }
    }
    for (size_t j = 0; j < r; j++){
      for (size_t c = 0; c < N; c++){
        const uint64_t coeff_off = in->b[j]->coeffs[c] + offset;
        out[k*l + j*l + i]->coeffs[c] = ((coeff_off>>h_bit) & h_mask) - half_Bg;
      }
    }
  }
}

void pvmtmlwe_torus_packing(PVW_TMLWE out, Torus ** in, int size){
  pvmtmlwe_noiseless_trivial_sample(out, 0);
  for (size_t i = 0; i < out->b[0]->N; i++){
    for (size_t j = 0; j < out->r; j++){
      out->b[j]->coeffs[i] = in[j][i/(out->b[0]->N/size)];
    }
  }
}

void pvmtmlwe_LUT_packing(PVW_TMLWE out, uint64_t ** in, uint64_t in_prec, uint64_t out_prec){
  const uint64_t size = 1ULL << in_prec;
  pvmtmlwe_noiseless_trivial_sample(out, 0);
  for (size_t i = 0; i < out->b[0]->N; i++){
    for (size_t j = 0; j < out->r; j++){
      out->b[j]->coeffs[i] = int2torus(in[j][i/(out->b[0]->N/size)], out_prec);
    }
  }
}

/* */
void pvmtmlwe_torus_packing_many_LUT(PVW_TMLWE out, Torus ** in, int lut_size, int n_luts){
  pvmtmlwe_noiseless_trivial_sample(out, 0);
  for (size_t i = 0; i < lut_size; i++){
    for (size_t j = 0; j < n_luts; j++){
      for (size_t k = 0; k < out->b[0]->N/(lut_size*n_luts); k++){
        for (size_t l = 0; l < out->r; l++){
          out->b[l]->coeffs[(i*n_luts + j)*out->b[0]->N/(lut_size*n_luts) + k] = in[l][j*lut_size + i];
        }
      }
    }
  }
}




/* PVW_TMLWE tensor product (WIP) 
Useless for now!

void pvmtmlwe_tensor_prod(PVW_TMLWE out, PVW_TMLWE in1, PVW_TMLWE in2, int precision, PVW_TMLWE_KS_Key rl_key){
  const int N = in1->b[0]->N, bit_size = sizeof(Torus)*8;
  assert(in1->k == 1 && in2->k == 1);
  TorusPolynomial tmp = polynomial_new_torus_polynomial(N);
  PVW_TMLWE t = pvmtmlwe_alloc_new_sample(1, in1->r, N);
  // T = A1 * A2
  polynomial_full_mul_with_scale(t->a[0], in1->a[0], in2->a[0], bit_size, bit_size - precision);
  for (size_t i = 0; i < in1->r; i++){
    for (size_t j = 0; j < N; j++){
      t->b[i]->coeffs[j] = 0;
    }
  }
  // A = A1*B2 + B1*A2
  for (size_t i = 0; i < in1->r; i++){
    polynomial_full_mul_with_scale(out->a[0], in1->a[0], in2->b[i], bit_size, bit_size - precision);
    polynomial_full_mul_with_scale(tmp, in1->b[i], in2->a[0], bit_size, bit_size - precision);
    polynomial_addto_torus_polynomial(out->a[0], tmp);
  }
  // B = B1*B2
  for (size_t i = 0; i < in1->r; i++){
    for (size_t j = 0; j < in2->r; j++){
      polynomial_full_mul_with_scale(out->b[i], in1->b[i], in2->b[j], bit_size, bit_size - precision);
    }
  }
  // Relinearization
  pvmtmlwe_keyswitch(t, t, rl_key);
  pvmtmlwe_subto(out, t);
  // Free
  free_polynomial(tmp);
  free_pvmtmlwe(t);
}


void pvmtmlwe_tensor_prod_FFT(PVW_TMLWE out, PVW_TMLWE in1, PVW_TMLWE in2, int precision, PVW_TMLWE_KS_Key rl_key){
  const int N = in1->b[0]->N, half_prec = sizeof(Torus)*8 - (sizeof(Torus)*8 - precision)/2;
  assert(in1->k == 1 && in2->k == 1);
  TorusPolynomial tmp = polynomial_new_torus_polynomial(N);
  DFT_Polynomial tmp_DFT = polynomial_new_DFT_polynomial(N);
  PVW_TMLWE_DFT t = pvmtmlwe_alloc_new_DFT_sample(1, in1->r, N);
  PVW_TMLWE t2 = pvmtmlwe_alloc_new_sample(1, in1->r, N);
  DFT_Polynomial A1 = polynomial_new_DFT_polynomial(N);
  DFT_Polynomial A2 = polynomial_new_DFT_polynomial(N);
  DFT_Polynomial * B1 = (DFT_Polynomial *) safe_malloc(sizeof(DFT_Polynomial) * in1->r);
  DFT_Polynomial * B2 = (DFT_Polynomial *) safe_malloc(sizeof(DFT_Polynomial) * in2->r);
  for (size_t i = 0; i < in1->r; i++){
    B1[i] = polynomial_new_DFT_polynomial(N);
  }
  for (size_t i = 0; i < in2->r; i++){
    B2[i] = polynomial_new_DFT_polynomial(N);
  }
  // T = A1 * A2
  polynomial_torus_scale(tmp, in1->a[0], half_prec);
  polynomial_torus_to_DFT(A1, tmp);
  polynomial_torus_scale(tmp, in2->a[0], half_prec);
  polynomial_torus_to_DFT(A2, tmp);
  polynomial_mul_DFT(t->a[0], A1, A2);
  for (size_t i = 0; i < in1->r; i++){
    for (size_t j = 0; j < N; j++){
      t->b[i]->coeffs[j] = 0.;
    }
  }
  // A = A1*B2 + B1*A2
  for (size_t i = 0; i < in1->r; i++){
    polynomial_torus_scale(tmp, in1->b[i], half_prec);
    polynomial_torus_to_DFT(B1[i], tmp);
  }
  for (size_t i = 0; i < in2->r; i++){
    polynomial_torus_scale(tmp, in2->b[i], half_prec);
    polynomial_torus_to_DFT(B2[i], tmp);
  }
  for (size_t i = 0; i < in1->r; i++){
    polynomial_mul_DFT(tmp_DFT, A1, B2[i]);
    polynomial_mul_addto_DFT(tmp_DFT, B1[i], A2);
    polynomial_DFT_to_torus(out->a[0], tmp_DFT);
  }
  // B = B1*B2
  for (size_t i = 0; i < in1->r; i++){
    for (size_t j = 0; j < in2->r; j++){
      polynomial_mul_DFT(tmp_DFT, B1[i], B2[j]);
      polynomial_DFT_to_torus(out->b[i], tmp_DFT);
    }
  }
  // Relinearization
  pvmtmlwe_from_DFT(t2, t);
  pvmtmlwe_keyswitch(t2, t2, rl_key);
  pvmtmlwe_subto(out, t2);
  // Free
  free_polynomial(tmp);
  free_polynomial(tmp_DFT);
  free_pvmtmlwe(t);
  free_pvmtmlwe(t2);
  free_polynomial(A1);
  free_polynomial(A2);
  for (size_t i = 0; i < in1->r; i++){
    free_polynomial(B1[i]);
  }
  for (size_t i = 0; i < in2->r; i++){
    free_polynomial(B2[i]);
  }
  free(B1);
  free(B2);
}
*/

// EvalAuto
void pvmtmlwe_eval_automorphism(PVW_TMLWE out, PVW_TMLWE in, uint64_t gen, PVW_TMLWE_KS_Key ks_key){
  for (size_t i = 0; i < out->k; i++){
    polynomial_permute(out->a[i], in->a[i], gen);
  }
  for (size_t i = 0; i < out->r; i++){
    polynomial_permute(out->b[i], in->b[i], gen);
  }
  pvmtmlwe_keyswitch(out, out, ks_key);
}
