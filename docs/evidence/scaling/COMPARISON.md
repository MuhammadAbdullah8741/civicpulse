# Measured scaling comparison

Runs: baseline-100 and tuned-100. Offered peak rate: 100 requests/second.

| Metric | Before | After |
|---|---:|---:|
| requests | 17304 | 17636 |
| failed_request_rate | 0 | 0.0015876616012701294 |
| dropped_iterations | 847 | 515 |
| p95_ms | 2514.3734239499945 | 677.3513987499999 |
| peak_replicas | 10 | 7 |
| first_scale_out_seconds | 53.9 | 63.2 |
| first_extra_ready_seconds | 59.4 | 68.8 |

## Resource requests

- baseline-100: `{"cpu": "100m", "memory": "128Mi"}`
- tuned-100: `{"cpu": "163m", "memory": "262144k"}`

## Observed lag

The higher load was scheduled to begin 30 seconds after the load generator launched.
The first increase in desired deployment replicas was observed at 53.9 seconds, and extra ready capacity at 59.4 seconds; a null value means it was not observed.
Measurements have roughly five-second sampling resolution plus API and container startup latency.
Metrics collection, HPA reconciliation and pod startup therefore separate arriving load from usable capacity, so autoscaling does not replace capacity planning.
Compare failed requests and dropped iterations as well as latency before interpreting the peak replica counts.

## Why VPA is Off

HPA uses CPU usage divided by CPU requests. Automatic VPA request changes would alter that denominator while HPA adjusts replicas. Off mode records recommendations without evictions or automatic resource changes; this experiment applies one recorded target manually and repeats the same load.

This is a short local experiment on one laptop. VPA recommendations from a short observation window are provisional, not production sizing.
