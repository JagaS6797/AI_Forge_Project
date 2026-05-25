"""Ticket model for support triage system."""
from datetime import datetime
from typing import Optional
from uuid import uuid4

from sqlalchemy import Column, String, Text, UUID, text
from sqlalchemy.dialects.postgresql import TIMESTAMP

from app.db.base import Base


class Ticket(Base):
    """Support ticket model - matches Supabase tickets table schema."""

    __tablename__ = "tickets"

    # Primary Key
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid4)
    
    # Unique ticket ID (generated)
    ticket_id = Column(String, unique=True, nullable=False, index=True)

    # Contact Info
    user_email = Column(String, nullable=False, index=True)

    # Issue Details
    issue = Column(Text, nullable=False)
    category = Column(String, nullable=False, default="General", index=True)
    priority = Column(String, nullable=False, default="medium", index=True)
    status = Column(String, nullable=False, default="open", index=True)

    # Related Info
    thread_id = Column(String, nullable=True, index=True)
    assigned_team = Column(String, nullable=True)
    next_action = Column(Text, nullable=True)

    # Timestamps
    created_at = Column(TIMESTAMP(timezone=True), nullable=False, server_default=text("now()"))
    updated_at = Column(TIMESTAMP(timezone=True), nullable=False, server_default=text("now()"))

    def __repr__(self) -> str:
        return f"<Ticket(ticket_id={self.ticket_id}, category={self.category}, priority={self.priority})>"
