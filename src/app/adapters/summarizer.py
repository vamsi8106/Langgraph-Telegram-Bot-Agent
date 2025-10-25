# # src/app/adapters/summarizer.py
# from langchain_core.messages import HumanMessage, BaseMessage
# from typing import Sequence

# def summarize_window(llm, window: Sequence[BaseMessage]) -> str:
#     prompt = HumanMessage(
#         content="Summarize the conversation above in ~3 concise lines, preserving key context and names."
#     )
#     resp = llm.invoke(list(window[-20:]) + [prompt])
#     return getattr(resp, "content", "").strip()


# src/app/adapters/summarizer.py
from typing import Sequence
from langchain_core.messages import BaseMessage, HumanMessage


def summarize_window(llm, window: Sequence[BaseMessage]) -> str:
    """
    Summarize the recent conversation context into a short paragraph.

    Parameters
    ----------
    llm : object
        The language model instance supporting `.invoke(messages)`.
    window : Sequence[BaseMessage]
        The list of conversation messages (typically from Redis memory).

    Returns
    -------
    str
        A concise 2–3 line summary of the conversation.
    """
    prompt = HumanMessage(
        content=(
            "Summarize the conversation above in about 3 concise lines, "
            "preserving important context, entities, and names."
        )
    )
    # use last ~20 turns for efficiency
    resp = llm.invoke(list(window[-20:]) + [prompt])
    return getattr(resp, "content", "").strip()
