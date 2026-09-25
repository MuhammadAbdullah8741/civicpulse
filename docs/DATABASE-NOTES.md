# Database engineering notes

## Schema ownership

Alembic migration 0001 creates the complaint table, PostgreSQL enums,
constraints, and indexes. Application startup does not create the schema.

## Index choices

ix_complaints_status_priority supports the planned dashboard query:
SELECT * FROM complaints WHERE status = 'open' AND priority = 'high'.
The leftmost status column also supports filtering by status alone.

ix_complaints_created_at supports the planned newest-first listing:
SELECT * FROM complaints ORDER BY created_at DESC LIMIT 20.
At this stage these are intended query patterns; API implementation follows.

## Persistence

pgdata preserves PostgreSQL data across container replacement.

redisdata stores Redis AOF data. Although statistics can be recomputed,
retaining Redis state can also preserve cached triage results and rate-limit
counters across restarts. AOF is not a substitute for database durability.

The development backend bind mount allows source edits without rebuilding.
The production configuration must omit this mount.

## Verified locally

Migration: 0001 (head).
First seed: Inserted: 30; total complaints: 30.
Second seed: Inserted: 0; total complaints: 30.
After Compose down/up: Inserted: 0; total complaints: 30.

Stable seed UUIDs and ON CONFLICT DO NOTHING prevent duplicate rows.
Seed categories, summaries, and priorities are preset fixtures.
Seed latency is zero because no live AI call occurs.

## Remaining work

Implement complaint APIs and readiness checks.
Measure database test coverage and expand integration checks.
Complete the eight required engineering-note answers with file references.
