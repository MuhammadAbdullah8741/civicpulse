# Frontend foundation — Issue #11

Owner: Umar. React 18, Vite and TypeScript. This phase provides navigation,
a render error boundary, a generated typed complaint API client and tests.
Views are intentionally labelled placeholders; submission/dashboard/stats follow.

## Commands (inside frontend)

- `npm ci`
- `npm run lint`
- `npm test` (5 component tests + 4 API client tests)
- `npm run build`
- `npm run dev` (open the address printed by Vite)
- `npm run api:check` (requires the backend on 127.0.0.1:8000)

`openapi.json` is a snapshot of the complaint API contract. `src/api/schema.d.ts`
is generated from it with `npm run api:generate`. `api:check` compares the used
schemas and operation parameters/bodies/responses with a live backend. It ignores
unrelated newly added endpoints. TypeScript types do not perform runtime response
validation. The backend validates its response models.

All browser API paths are relative `/api`. The development proxy is Vite-only
and does not become a baked-in production URL. nginx proxying is a later phase.
No environment secrets belong here. No live API calls are made by these tests.

The existing shared CI does not yet run frontend checks. Local checks must pass
for this PR; shared frontend CI integration is still required before submission.

## AI assistance

OpenAI ChatGPT/Codex generated this foundation package and proposed its tests.
Umar must review, execute, and understand it before committing. Record actual
changes and verification outcomes in the project AI-USAGE record; do not claim
original unaided authorship or test results that have not been observed.
