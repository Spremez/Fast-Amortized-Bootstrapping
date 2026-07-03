# Stage222 Isolated Compact EP Integration Model

The production compact API computes, per lane q:

```text
out_a[q] += dec(shared_mask) * shared_a[q] + dec(body[q]) * body_a[q]
out_b[q] += dec(shared_mask) * shared_b[q] + dec(body[q]) * body_b[q]
```

This is a lane-local compact external product. It is not a full dense MAT
linear map because it has no term that consumes `body[j]` and writes to lane
`q != j`. Stage203's `lane_neighbor_body_interaction` rows are therefore not
covered by this API. Stage222 admits the lane-local subclass and blocks complete
SAB integration.
