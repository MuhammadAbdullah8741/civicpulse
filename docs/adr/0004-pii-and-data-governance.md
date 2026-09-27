# ADR 0004: Minimise disclosure; use synthetic demonstration data

Status: accepted for the assignment demonstration, not approval for public use.

## Data flow and decision

The hosted provider sends a system prompt and a redacted complaint body to
Groq's HTTPS chat-completions endpoint. `prompt.py` replaces matching email
addresses and phone-like strings. The separate location and reporter_contact
fields are not sent by either LLM implementation. Names and addresses embedded
in complaint text may remain: regex redaction is not anonymisation.

Use only synthetic complaints for this project. For an offline demonstration,
Ollama processes requests in its local container after model download. Rules and
simulated providers make no outbound inference request.

PostgreSQL retains original text, location and optional contact. Redis retains
summaries in its 24-hour cache; SHA-256 keys are not encryption. AOF/PVC backups
can retain older data beyond logical TTL expiry. Provider history holds only
provider, latency, fallback, cache-hit and timestamp. Fallback logs include IDs
and error classes, not API keys or complaint bodies. A rules summary may repeat
PII from the original text, so synthetic-only use also applies to local output.

## Provider policy checked 26 September 2026

Groq says ordinary inference content is not retained by default, but reliability
and abuse investigations can retain it for up to 30 days, subject to legal
exceptions. Usage metadata is retained. Zero Data Retention is an account
setting; this project does not claim that the team's account has enabled it.
See https://console.groq.com/docs/your-data .

## Credentials and unresolved production needs

Secrets belong in ignored local .env, GitHub Secrets and Kubernetes Secrets,
never committed examples. Credentials previously shared in chat must be rotated;
completion of that rotation has not been independently verified. This document
contains no credentials and does not claim a Git-history leak occurred.

Public deployment requires operator authentication/authorisation, TLS, retention
and deletion policy, access controls on complaint data and backups, and a review
of actual provider/account controls. The assignment demo is not a public
municipal service and must not process real citizen personal information.
