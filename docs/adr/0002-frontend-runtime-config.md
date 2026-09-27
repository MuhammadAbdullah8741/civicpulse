# ADR 0002 — same-origin API proxy at container startup

Status: accepted for implementation; verify with the Phase 5 commands.

## Context
Vite substitutes build-time environment values into JavaScript. Baking a backend
URL into the bundle would require a new build for each environment. Browser
secrets would also be exposed. The frontend client already uses relative /api
paths, which should remain unchanged across deployments.

## Decision
nginx serves the compiled application on port 8080 and proxies /api/ to the
BACKEND_UPSTREAM hostname:port supplied at container startup (default backend:8000).
The entrypoint renders only two allowed environment variables into a /tmp config;
nginx variables such as $uri are not expanded by the shell. DNS comes from the
container's resolv.conf and is periodically re-resolved for backend recreation.

The same built JavaScript and image can be deployed with a different upstream.
No API key is accepted by this image. API response headers, including X-Cache,
pass through the same-origin proxy. Thus no cross-origin browser setup is needed.
Vite's local development proxy remains separate and is not used in the image.

## Container choices
A Node 22 Alpine builder uses npm ci and the committed lockfile. The runtime copies
only dist and nginx startup/configuration files, never src or node_modules.
The nginx 1.27 Alpine series follows the assignment's specified base. Both bases are pinned by registry-resolved manifest digest. Run the mandatory
Trivy gate before claiming image security. Upgrade documented base versions if
fixed vulnerabilities require it; do not suppress scanner failures.

Runtime UID/GID 101, unprivileged port 8080 and /tmp paths remove the need for root.
The entrypoint execs nginx; SIGQUIT requests graceful shutdown. A static /health
endpoint checks the frontend itself, independent of database availability.
The proxy read timeout is 60 seconds to accommodate the backend's two bounded
10-second inference attempts plus Redis/database overhead. nginx does not retry
POSTs, avoiding accidental duplicate reports.

The optional Compose overlay attaches frontend only to edge. Database and Redis
remain on internal. This phase's topology must be tested before claiming isolation.

## Trade-offs
An extra proxy hop is accepted for a portable, same-origin browser client.
The demo has no operator authentication and binds to loopback on the laptop.
Production TLS, identity and authorization need a separate deployment decision.
Client IP limiting across reverse proxies requires trusted-proxy configuration;
without it the backend may see the frontend IP and share one limiter bucket among
its users. Complete that integration in the shared backend/Compose phase rather
than trusting arbitrary client-supplied forwarding headers.
