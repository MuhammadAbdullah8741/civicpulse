"""Create the complaint schema."""

from alembic import op

revision = "0001"
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.execute("""
        CREATE TYPE complaint_category AS ENUM (
            'water', 'electricity', 'sanitation',
            'roads', 'streetlights', 'other'
        )
    """)
    op.execute("""
        CREATE TYPE complaint_priority AS ENUM (
            'high', 'normal', 'low'
        )
    """)
    op.execute("""
        CREATE TYPE complaint_status AS ENUM (
            'open', 'in_progress', 'resolved', 'rejected'
        )
    """)
    op.execute("""
        CREATE TABLE complaints (
            id UUID PRIMARY KEY,
            text TEXT NOT NULL,
            location VARCHAR(200) NOT NULL,
            reporter_contact TEXT,
            category complaint_category NOT NULL,
            priority complaint_priority NOT NULL,
            status complaint_status NOT NULL DEFAULT 'open',
            ai_summary VARCHAR(140),
            triaged_by VARCHAR(64) NOT NULL,
            triage_latency_ms INTEGER NOT NULL,
            created_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
            CONSTRAINT ck_complaint_text_length
                CHECK (char_length(text) BETWEEN 10 AND 2000),
            CONSTRAINT ck_complaint_location_length
                CHECK (char_length(location) BETWEEN 3 AND 200),
            CONSTRAINT ck_complaint_latency
                CHECK (triage_latency_ms >= 0),
            CONSTRAINT ck_complaint_summary_single_line
                CHECK (
                    ai_summary IS NULL OR
                    (position(chr(10) in ai_summary) = 0 AND
                     position(chr(13) in ai_summary) = 0)
                ),
            CONSTRAINT ck_complaint_provider
                CHECK (char_length(triaged_by) > 0)
        )
    """)
    op.create_index(
        "ix_complaints_status_priority",
        "complaints",
        ["status", "priority"],
    )
    op.create_index(
        "ix_complaints_created_at",
        "complaints",
        ["created_at"],
    )


def downgrade() -> None:
    op.drop_table("complaints")
    op.execute("DROP TYPE complaint_status")
    op.execute("DROP TYPE complaint_priority")
    op.execute("DROP TYPE complaint_category")
