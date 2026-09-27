# Probe adjustment after the tuned experiment

The tuned-100 run recorded 28 failed HTTP requests and 515 dropped
iterations. A backend pod restarted during that run after three
liveness probe timeouts. Its previous process exited cleanly with
code 0; Kubernetes explicitly recorded a liveness-triggered restart.

This establishes the restart cause, but does not prove that all
28 request failures had the same cause.

After completing the before/after resource comparison, liveness was
changed to timeoutSeconds=5, periodSeconds=10 and failureThreshold=6.
Readiness remains unchanged. This tolerates longer transient overload
while retaining restart detection for sustained unresponsiveness.

The original baseline and tuned evidence remains unchanged.
The following rolling-update experiment uses this adjusted configuration.
