# Fast amortized bootstrapping with small keys and polynomial noise overhead

## Paper

[eprint 2025/686](https://eprint.iacr.org/2025/686)

```
@inproceedings{guimaraes_fast_2025,
author = {Guimar{\~a}es, Antonio and Pereira, Hilder V. L.},
title = {Fast Amortized Bootstrapping with Small Keys and Polynomial Noise Overhead},
year = {2025},
isbn = {9798400715259},
publisher = {Association for Computing Machinery},
address = {New York, NY, USA},
url = {https://doi.org/10.1145/3719027.3765181},
doi = {10.1145/3719027.3765181},
booktitle = {Proceedings of the 2025 ACM SIGSAC Conference on Computer and Communications Security},
pages = {2967–2981},
numpages = {15},
keywords = {amortized bootstrapping, fully homomorphic encryption, rlwe},
location = {Taipei, Taiwan},
series = {CCS '25}
}
```


## Build

For processors with `AVX-512` and `VAES`:

``` make [parameters]```

For processors with only `AVX2/FMA`:

``` make FFT_LIB=spqlios A_PRNG=none ENABLE_VAES=false [parameters] ```

> [!WARNING]
> The implementation will be slower without [AVX-512](https://en.wikipedia.org/wiki/Advanced_Vector_Extensions). Results in the paper are for an [`r7i.metal-24xl`](https://instances.vantage.sh/aws/ec2/r7i.metal-24xl) instance on AWS.


For other compiling options, see [MOSFHET](https://github.com/antoniocgj/MOSFHET). 

## Available parameters

For each of the parameters below, SET_X_Y_Z refers to the bootstrapping of X-bit messages if the function is arbitrary or Y-bit messages if the function is negacyclic (See Remark 7.1 in the paper) for Z messages.

> [!WARNING]
> Don't forget to add `FFT_LIB=spqlios A_PRNG=none ENABLE_VAES=false` to the `make` command if you don't have AVX512.

### Binary keys
``` make -B PARAM=SET_2_3_2048 && ./main``` 

``` make -B PARAM=SET_2_3_4096 && ./main``` 

``` make -B PARAM=SET_2_3_8192 && ./main``` 

``` make -B PARAM=SET_4_5_2048 && ./main``` 

``` make -B PARAM=SET_4_5_4096 && ./main``` 

``` make -B PARAM=SET_4_5_8192 && ./main``` 

``` make -B PARAM=SET_6_7_4096 && ./main``` 

``` make -B PARAM=SET_6_7_8192 && ./main``` 

``` make -B PARAM=SET_8_9_4096 && ./main``` 

``` make -B PARAM=SET_8_9_8192 && ./main``` 

Result with very high Failure Probability:

``` make -B PARAM=SET_8_9_HIGH_FR && ./main``` 

### Ternary keys

``` make -B KEY=TERNARY PARAM=SET_2_3_2048 && ./main``` 

``` make -B KEY=TERNARY PARAM=SET_2_3_4096 && ./main``` 

``` make -B KEY=TERNARY PARAM=SET_2_3_8192 && ./main``` 

``` make -B KEY=TERNARY PARAM=SET_4_5_2048 && ./main``` 

``` make -B KEY=TERNARY PARAM=SET_4_5_4096 && ./main``` 

``` make -B KEY=TERNARY PARAM=SET_4_5_8192 && ./main``` 

``` make -B KEY=TERNARY PARAM=SET_6_7_4096 && ./main``` 

``` make -B KEY=TERNARY PARAM=SET_6_7_8192 && ./main``` 

``` make -B KEY=TERNARY PARAM=SET_8_9_4096 && ./main``` 

``` make -B KEY=TERNARY PARAM=SET_8_9_8192 && ./main``` 


### Arbitrary keys

``` make -B KEY=ARBITRARY PARAM=SET_A2 && ./main``` 

``` make -B KEY=ARBITRARY PARAM=SET_A3 && ./main``` 

``` make -B KEY=ARBITRARY PARAM=SET_A4 && ./main``` 

``` make -B KEY=ARBITRARY PARAM=SET_A5 && ./main``` 

## Measuring noise

To measure noise, uncomment line 101 of `src/sparse_amortized_bootstrapping.c`.

Performance measurements are unreliable, and correctness checks may fail when measuring noise.

## License

[Apache License Version 2.0](LICENSE)

This repository contains code from:

- [MOSFHET](https://github.com/antoniocgj/MOSFHET): [Apache License Version 2.0](https://github.com/antoniocgj/MOSFHET/blob/main/LICENSE) - Copyright Antonio Guimarães et al. - See their [detailed copyright information](https://github.com/antoniocgj/MOSFHET/tree/main?tab=readme-ov-file#license).
