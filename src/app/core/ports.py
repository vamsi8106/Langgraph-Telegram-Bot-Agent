
# # src/app/core/ports.py
# from typing import Protocol, Any, Sequence, Callable, Optional, List
# from langchain_core.messages import BaseMessage

# class LLM(Protocol):
#     def invoke(self, messages: Sequence[Any]) -> Any: ...

# class Embeddings(Protocol):
#     def embed_documents(self, texts: list[str]) -> list[list[float]]: ...

# class VectorStore(Protocol):
#     def add_texts(self, texts: list[str], metadatas: list[dict] | None = None) -> None: ...
#     def search(self, query: str, k: int = 3) -> list[Any]: ...
#     def as_retriever(self, k: int = 3): ...

# class TTS(Protocol):
#     def __call__(self, text: str) -> bytes: ...

# class ImageGen(Protocol):
#     def __call__(self, prompt: str, size: str = "1024x1024") -> str: ...

# class ShortTermMemory(Protocol):
#     def append_message(self, chat_id: int, msg: BaseMessage) -> None: ...
#     def get_window(self, chat_id: int, k: int = 30) -> List[BaseMessage]: ...
#     def clear(self, chat_id: int) -> None: ...

# class DurableMemory(Protocol):
#     def set_summary(self, chat_id: int, text: str) -> None: ...
#     def get_summary(self, chat_id: int) -> Optional[str]: ...

# src/app/core/ports.py
from __future__ import annotations

from typing import Any, List, Optional, Protocol, Sequence


class LLM(Protocol):
    """
    Large Language Model interface.

    Implementations must support `.invoke(messages)` and return a model response
    (e.g., a LangChain `AIMessage`).
    """

    def invoke(self, messages: Sequence[Any]) -> Any:
        """Invoke the model with a sequence of messages."""
        ...


class Embeddings(Protocol):
    """
    Text embedding generator interface.
    """

    def embed_documents(self, texts: list[str]) -> list[list[float]]:
        """Embed a list of texts and return a list of vectors."""
        ...


class VectorStore(Protocol):
    """
    Vector database interface with simple add/search APIs.

    This aligns with the small adapter we wrap around Chroma:
    - `add_texts(texts, metadatas)`
    - `search(query, k)`
    - `as_retriever(k)`
    """

    def add_texts(self, texts: list[str], metadatas: Optional[list[dict]] = None) -> None:
        """Insert multiple documents (and optional metadata) into the store."""
        ...

    def search(self, query: str, k: int = 3) -> list[Any]:
        """Return the top-k nearest results for the query."""
        ...

    def as_retriever(self, k: int = 3):
        """Return a retriever object configured to fetch top-k results."""
        ...


class TTS(Protocol):
    """
    Text-to-Speech callable interface.

    Implementations behave like a function: `tts(text) -> bytes`.
    """

    def __call__(self, text: str) -> bytes:
        """Synthesize speech audio for the given text and return raw bytes."""
        ...


class ImageGen(Protocol):
    """
    Image generation callable interface.

    Implementations behave like a function: `image_gen(prompt, size) -> path`.
    """

    def __call__(self, prompt: str, size: str = "1024x1024") -> str:
        """Generate an image and return the saved file path."""
        ...


class ShortTermMemory(Protocol):
    """
    Short-term conversation memory (e.g., Redis rolling window).
    """

    def append_message(self, chat_id: int, msg: Any) -> None:
        """Append a message to the rolling window for a chat."""
        ...

    def get_window(self, chat_id: int, k: int = 30) -> List[Any]:
        """Fetch up to `k` recent messages for a chat (oldest → newest)."""
        ...

    def clear(self, chat_id: int) -> None:
        """Clear the chat’s rolling window."""
        ...


class DurableMemory(Protocol):
    """
    Durable memory (e.g., Postgres) for summaries and history.
    """

    def set_summary(self, chat_id: int, text: str) -> None:
        """Set or update the latest summary for a chat."""
        ...

    def get_summary(self, chat_id: int) -> Optional[str]:
        """Fetch the latest summary for a chat, if any."""
        ...
