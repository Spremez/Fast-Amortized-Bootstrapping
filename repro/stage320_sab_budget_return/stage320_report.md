# Stage320 SAB Budget Return

Decision: `PASS_STAGE320_RETURN_TO_MAT_EP_SELECT_R4_UNROLLED_REFRESH`.

Stage320 closes the IFFT-only branch and returns to the complete SAB
`T_bootstrap/r` budget.  The selected next executable candidate is a current
head refresh of the existing explicit r=4 MAT EP unrolled-row implementation:
`MAT_TRGSW_AVX512_R4_UNROLLED_ROWS=true`.

| component | body share | status |
| --- | --- | --- |
| MAT EP lifecycle | 0.585042 | selected target family |
| IFFT | 0.181943 | closed by Stage319 |
| digit conversion | 0.172510 | closed by Stage314 |

The next step must be full-SAB A/B, not another isolated kernel claim.
