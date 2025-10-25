# src/app/adapters/memory_postgres.py
from typing import Iterable, Optional, Tuple

from sqlalchemy import insert, select, update

from ..db import Chat, ChatMemory, ChatMessage, SessionLocal, User


class PgDurableStore:
    """
    Durable storage for identities, summaries, and full message history.

    Uses SQLAlchemy sessions from `SessionLocal` with short-lived context
    managers to keep connections tidy and commits explicit.
    """

    # ------- identity -------

    def ensure_user(
        self,
        *,
        user_id: int,
        first_name: Optional[str],
        last_name: Optional[str],
        username: Optional[str],
    ) -> None:
        """
        Upsert a user by `user_id`.

        Parameters
        ----------
        user_id : int
            Telegram (or external) user id.
        first_name, last_name, username : Optional[str]
            Latest user profile fields to persist.
        """
        with SessionLocal() as s:
            row = s.execute(
                select(User).where(User.user_id == user_id)
            ).scalar_one_or_none()

            if row:
                s.execute(
                    update(User)
                    .where(User.user_id == user_id)
                    .values(
                        first_name=first_name,
                        last_name=last_name,
                        username=username,
                    )
                )
            else:
                s.execute(
                    insert(User).values(
                        user_id=user_id,
                        first_name=first_name,
                        last_name=last_name,
                        username=username,
                    )
                )
            s.commit()

    def ensure_chat(
        self,
        *,
        chat_id: int,
        chat_type: str,
        title: Optional[str],
        user_id: Optional[int],
    ) -> None:
        """
        Upsert a chat by `chat_id`.

        Parameters
        ----------
        chat_id : int
            Telegram chat id.
        chat_type : str
            e.g., "private", "group".
        title : Optional[str]
            Chat title (groups/channels).
        user_id : Optional[int]
            Owner/peer id for private chats.
        """
        with SessionLocal() as s:
            row = s.execute(
                select(Chat).where(Chat.chat_id == chat_id)
            ).scalar_one_or_none()

            if row:
                s.execute(
                    update(Chat)
                    .where(Chat.chat_id == chat_id)
                    .values(
                        chat_type=chat_type,
                        title=title,
                        user_id=user_id,
                    )
                )
            else:
                s.execute(
                    insert(Chat).values(
                        chat_id=chat_id,
                        chat_type=chat_type,
                        title=title,
                        user_id=user_id,
                    )
                )
            s.commit()

    # ------- durable summary -------

    def set_summary(self, chat_id: int, text: str) -> None:
        """
        Set or update the latest conversation summary for a chat.
        """
        with SessionLocal() as s:
            row = s.execute(
                select(ChatMemory).where(ChatMemory.chat_id == chat_id)
            ).scalar_one_or_none()

            if row:
                s.execute(
                    update(ChatMemory)
                    .where(ChatMemory.chat_id == chat_id)
                    .values(last_summary=text)
                )
            else:
                s.execute(
                    insert(ChatMemory).values(
                        chat_id=chat_id,
                        last_summary=text,
                    )
                )
            s.commit()

    def get_summary(self, chat_id: int) -> Optional[str]:
        """
        Fetch the latest stored summary for a chat.

        Returns
        -------
        Optional[str]
            The summary text if present; otherwise None.
        """
        with SessionLocal() as s:
            return s.execute(
                select(ChatMemory.last_summary).where(ChatMemory.chat_id == chat_id)
            ).scalar_one_or_none()

    # ------- durable messages (history) -------

    def add_message(self, *, chat_id: int, role: str, content: str) -> None:
        """
        Append a single message to chat history.

        Parameters
        ----------
        chat_id : int
            Chat id this message belongs to.
        role : str
            "user" | "assistant" | "system".
        content : str
            Raw message text.
        """
        with SessionLocal() as s:
            s.execute(
                insert(ChatMessage).values(
                    chat_id=chat_id,
                    role=role,
                    content=content,
                )
            )
            s.commit()

    def add_messages_bulk(
        self,
        *,
        chat_id: int,
        turns: Iterable[Tuple[str, str]],
    ) -> None:
        """
        Bulk insert multiple messages efficiently.

        Parameters
        ----------
        chat_id : int
            Chat id for all messages.
        turns : Iterable[Tuple[str, str]]
            Iterable of (role, content).
        """
        payload = [
            {"chat_id": chat_id, "role": role, "content": content}
            for role, content in turns
        ]
        if not payload:
            return

        with SessionLocal() as s:
            s.execute(insert(ChatMessage), payload)
            s.commit()
