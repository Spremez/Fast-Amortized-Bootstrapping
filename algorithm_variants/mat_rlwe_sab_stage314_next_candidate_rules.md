# Stage314 Next Candidate Rules

Decision: `PASS_STAGE314_LOCAL_DIGIT_MICROVARIANTS_CLOSED_BACKEND_OR_SCHEDULE_NEXT`.

No behavior-changing variant is introduced. This is a route gate for future
algorithm work:

- local digit microvariants: closed without a new full-SAB budget;
- backend IFFT: open but high-risk;
- schedule-level SAB reductions: open and algorithmically more relevant;
- dense AVX rewrite: deferred until evidence selects it.
