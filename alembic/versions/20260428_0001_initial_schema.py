"""initial schema"""

from alembic import op
import sqlalchemy as sa


revision = "20260428_0001"
down_revision = None
branch_labels = None
depends_on = None


appointment_status = sa.Enum("booked", "cancelled", "modified", name="appointment_status")
session_status = sa.Enum("created", "active", "ended", "failed", name="session_status")
event_type = sa.Enum(
    "user_transcript",
    "agent_transcript",
    "tool_started",
    "tool_succeeded",
    "tool_failed",
    "system",
    name="event_type",
)
intent_type = sa.Enum("book", "retrieve", "cancel", "modify", "general", "end", name="intent_type")


def upgrade() -> None:
    bind = op.get_bind()
    if bind.dialect.name != "sqlite":
        appointment_status.create(bind, checkfirst=True)
        session_status.create(bind, checkfirst=True)
        event_type.create(bind, checkfirst=True)
        intent_type.create(bind, checkfirst=True)

    op.create_table(
        "users",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("name", sa.String(length=255), nullable=True),
        sa.Column("phone_number", sa.String(length=32), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_users_phone_number"), "users", ["phone_number"], unique=True)

    op.create_table(
        "conversation_sessions",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("user_id", sa.Uuid(), nullable=True),
        sa.Column("livekit_room_name", sa.String(length=255), nullable=False),
        sa.Column("status", session_status, nullable=False),
        sa.Column("started_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("ended_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("latest_intent", intent_type, nullable=True),
        sa.Column("extracted_entities_json", sa.JSON(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"]),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("livekit_room_name"),
    )

    op.create_table(
        "appointments",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("user_id", sa.Uuid(), nullable=False),
        sa.Column("appointment_date", sa.Date(), nullable=False),
        sa.Column("appointment_time", sa.Time(), nullable=False),
        sa.Column("status", appointment_status, nullable=False),
        sa.Column("source_session_id", sa.Uuid(), nullable=True),
        sa.Column("notes", sa.String(length=500), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["source_session_id"], ["conversation_sessions.id"]),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        "uq_appointments_active_slot",
        "appointments",
        ["appointment_date", "appointment_time"],
        unique=True,
    )

    op.create_table(
        "conversation_events",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("session_id", sa.Uuid(), nullable=False),
        sa.Column("event_type", event_type, nullable=False),
        sa.Column("event_name", sa.String(length=255), nullable=True),
        sa.Column("payload_json", sa.JSON(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["session_id"], ["conversation_sessions.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_conversation_events_session_id"), "conversation_events", ["session_id"], unique=False)
    op.create_index(
        "ix_conversation_events_session_id_created_at",
        "conversation_events",
        ["session_id", "created_at"],
        unique=False,
    )

    op.create_table(
        "conversation_summaries",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("session_id", sa.Uuid(), nullable=False),
        sa.Column("summary_text", sa.Text(), nullable=False),
        sa.Column("appointments_json", sa.JSON(), nullable=False),
        sa.Column("preferences_json", sa.JSON(), nullable=False),
        sa.Column("generated_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("model_name", sa.String(length=255), nullable=True),
        sa.ForeignKeyConstraint(["session_id"], ["conversation_sessions.id"]),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("session_id"),
    )
    op.create_index("ix_conversation_summaries_session_id", "conversation_summaries", ["session_id"], unique=False)


def downgrade() -> None:
    op.drop_index("ix_conversation_summaries_session_id", table_name="conversation_summaries")
    op.drop_table("conversation_summaries")
    op.drop_index("ix_conversation_events_session_id_created_at", table_name="conversation_events")
    op.drop_index(op.f("ix_conversation_events_session_id"), table_name="conversation_events")
    op.drop_table("conversation_events")
    op.drop_index("uq_appointments_active_slot", table_name="appointments")
    op.drop_table("appointments")
    op.drop_table("conversation_sessions")
    op.drop_index(op.f("ix_users_phone_number"), table_name="users")
    op.drop_table("users")

    bind = op.get_bind()
    if bind.dialect.name != "sqlite":
        intent_type.drop(bind, checkfirst=True)
        event_type.drop(bind, checkfirst=True)
        session_status.drop(bind, checkfirst=True)
        appointment_status.drop(bind, checkfirst=True)
