# from langchain_openai import OpenAIEmbeddings
# from langchain_chroma import Chroma
# from ..config.settings import settings

# def build_vectorstore(collection: str = "karan_bio"):
#     embeddings = OpenAIEmbeddings(model=settings.openai_embed_model)
#     vs = Chroma(
#         collection_name=collection,
#         embedding_function=embeddings,
#         persist_directory=settings.persist_dir,
#     )
#     return vs

# src/app/adapters/vector_chroma.py
from __future__ import annotations

from langchain_openai import OpenAIEmbeddings
from langchain_chroma import Chroma
from ..config.settings import settings


def build_vectorstore(collection: str = "karan_bio") -> Chroma:
    """
    Build and return a persistent Chroma vector store using OpenAI embeddings.

    Parameters
    ----------
    collection : str, optional
        The collection name to use within the vector store (default: "karan_bio").

    Returns
    -------
    Chroma
        A persistent Chroma instance configured with OpenAI embeddings.
    """
    embeddings = OpenAIEmbeddings(model=settings.openai_embed_model)
    vectorstore = Chroma(
        collection_name=collection,
        embedding_function=embeddings,
        persist_directory=settings.persist_dir,
    )
    return vectorstore
