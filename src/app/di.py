# src/app/di.py
from dataclasses import dataclass
from .adapters.llm_openai import build_llm
from .adapters.vector_chroma import build_vectorstore
from .adapters.tts_elevenlabs import build_tts
from .adapters.image_openai import build_image_gen
from .adapters.memory_redis import RedisMemoryStore
from .adapters.memory_postgres import PgDurableStore

class VSAdapter:
    """Small adapter to present a stable VectorStore interface."""
    def __init__(self, vs):
        self._vs = vs
    def add_texts(self, texts, metadatas=None):
        return self._vs.add_texts(texts=texts, metadatas=metadatas)
    def search(self, query: str, k: int = 3):
        return self._vs.similarity_search(query, k=k)
    def as_retriever(self, k: int = 3):
        return self._vs.as_retriever(search_kwargs={"k": k})

@dataclass
class Container:
    llm: object
    vector: object
    tts: object
    image_gen: object
    short_mem: object
    durable_mem: object

def build_container():
    return Container(
        llm=build_llm(),
        vector=VSAdapter(build_vectorstore()),
        tts=build_tts(),           # callable: tts(text) -> bytes
        image_gen=build_image_gen(),  # callable: image_gen(prompt) -> path
        short_mem=RedisMemoryStore(),
        durable_mem=PgDurableStore(),
    )
