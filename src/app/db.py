# src/app/db.py
"""
Database models and session setup for the Karan bot.

Contains ORM mappings for users, chats, chat memory, and messages.
"""

from __future__ import annotations

from sqlalchemy import (
    JSON,
    TIMESTAMP,
    BigInteger,
    ForeignKey,
    Integer,
    Text,
    create_engine,
    func,
)
from sqlalchemy.orm import (
    DeclarativeBase,
    Mapped,
    mapped_column,
    relationship,
    sessionmaker,
)

from .config.settings import settings


# ---------------------------------------------------------------------------
# Engine / Session
# ---------------------------------------------------------------------------

engine = create_engine(settings.database_url, pool_pre_ping=True, future=True)
SessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False, future=True)


# ---------------------------------------------------------------------------
# Base class
# ---------------------------------------------------------------------------

class Base(DeclarativeBase):
    """Base declarative class for ORM models."""
    pass


# ---------------------------------------------------------------------------
# ORM models
# ---------------------------------------------------------------------------

class User(Base):
    """
    Telegram user entity.
    """
    __tablename__ = "users"

    user_id: Mapped[int] = mapped_column(BigInteger, primary_key=True)
    first_name: Mapped[str | None] = mapped_column(Text)
    last_name: Mapped[str | None] = mapped_column(Text)
    username: Mapped[str | None] = mapped_column(Text)
    created_at: Mapped[str] = mapped_column(TIMESTAMP, server_default=func.now())


class Chat(Base):
    """
    Telegram chat entity (private/group).
    """
    __tablename__ = "chats"

    chat_id: Mapped[int] = mapped_column(BigInteger, primary_key=True)
    chat_type: Mapped[str] = mapped_column(Text)
    title: Mapped[str | None] = mapped_column(Text)
    user_id: Mapped[int | None] = mapped_column(BigInteger)
    created_at: Mapped[str] = mapped_column(TIMESTAMP, server_default=func.now())


class ChatMemory(Base):
    """
    Long-term memory storage per chat.

    Stores summaries and context flags.
    """
    __tablename__ = "chat_memory"

    chat_id: Mapped[int] = mapped_column(BigInteger, primary_key=True)
    last_summary: Mapped[str | None] = mapped_column(Text)
    last_summary_at: Mapped[str | None] = mapped_column(TIMESTAMP)
    persona: Mapped[dict] = mapped_column(JSON, default=dict)
    flags: Mapped[dict] = mapped_column(JSON, default=dict)
    updated_at: Mapped[str] = mapped_column(
        TIMESTAMP, server_default=func.now(), onupdate=func.now()
    )


class ChatMessage(Base):
    """
    Individual message entries for a chat.

    Roles: "user", "assistant", "system".
    """
    __tablename__ = "chat_messages"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    chat_id: Mapped[int] = mapped_column(BigInteger, ForeignKey("chats.chat_id"), index=True)
    role: Mapped[str] = mapped_column(Text)
    content: Mapped[str] = mapped_column(Text)
    created_at: Mapped[str] = mapped_column(TIMESTAMP, server_default=func.now())

    chat: Mapped["Chat"] = relationship("Chat", lazy="joined")
