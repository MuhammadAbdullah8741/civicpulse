# Phase 2 — citizen complaint submission

The submission page uses the typed API client and displays the actual server
category, priority, summary, provider, latency and reference. No classification
or status-transition rules are duplicated in the browser.

Validation trims input and counts Unicode code points for the 10–2000 description
and 3–200 location bounds. The backend remains authoritative. Empty contact is
sent as null. Inputs and submit are disabled while a request is pending; a ref
also guards repeated submit events. Successful submissions offer an explicit
new-report action. Transport failures retain input and warn that a request may
already have persisted; automatically retrying POST could duplicate reports.

The API error includes validated field-error entries. The form maps them to
accessible field messages and renders Retry-After on HTTP 429. No request-body
logging or API keys are added. Use synthetic data only.

Run from frontend: npm ci; npm run lint; npm test; npm run build; npm run api:check.
Expected test count with Phase 1: 17 (previous 9 plus 8 new tests). Tests mock API
calls and do not call Groq/Ollama. The API contract check needs a running backend.
The existing shared CI still needs frontend jobs added before final submission.

Manual test: open npm run dev, navigate to Submit report, try invalid fields,
then submit a synthetic water complaint. Confirm the returned fields and that
GET /api/complaints/{id} retrieves the same saved complaint. Do not claim the
manual test passed until you perform it. A real 429 requires the backend rate
limiter; the component test verifies rendering independently.

AI attribution: ChatGPT/Codex supplied this implementation and proposed tests.
Umar reviews and runs the work, records actual changes and results, and must be
able to explain validation, async states, API errors and test isolation at viva.
