# Phase 3 — operations dashboard

Umar's dashboard uses the existing typed client for GET list and PATCH status.
Category/priority/status selects are filters, not a transition table. Every action
button comes directly from each response's allowed_transitions. Terminal rows
therefore have no action buttons. A 409 displays the exact server detail.

Pagination uses the backend total and a page size of 10. Changing a filter resets
to page one. A response arriving after its request is superseded is ignored.
If writes reduce the result set below the current page, the last valid page is
requested. Background refresh occurs every 15 seconds only in a visible tab and
outside a pending status mutation. Timers are removed on unmount.

A successful status update reloads the filtered list. A failed update preserves
the displayed record and shows the error. The operator can refresh stale state.
Action buttons are disabled while loading or updating. Contact information is
not rendered in the list. Dates use the browser's local display timezone; the
API's timestamps remain UTC.

Verification: npm ci; npm run lint; npm test (expected 25 tests including Phase 2);
npm run build; npm audit; npm run api:check. Tests use mock API results and make
no hosted-model calls. The foundation test now mocks the newly live dashboard.

Manual check: inspect real seeded records, apply all three filters, use Next and
Previous with enough records, advance a synthetic open report to in_progress,
then resolved. Refresh and confirm no further actions. A real 409 can be exercised
with two browser tabs displaying the same open record: resolve it in one tab,
then attempt an old action in the other before its automatic refresh. The
component test also covers the 409 deterministically without timing dependencies.

AI attribution: ChatGPT/Codex supplied these files and proposed tests. Umar must
review/run them and document actual verification and modifications. Do not claim
checks or manual scenarios passed until they have been performed.
