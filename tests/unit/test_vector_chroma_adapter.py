from app.adapters.vector_chroma import build_vectorstore

def test_build_vectorstore_monkeypatched(monkeypatch):
    class DummyEmb:
        def __init__(self, model=None): self.model=model
    class DummyVS:
        def __init__(self, collection_name=None, embedding_function=None, persist_directory=None):
            self.collection_name = collection_name
            self.embedding_function = embedding_function
            self.persist_directory = persist_directory

    monkeypatch.setattr("app.adapters.vector_chroma.OpenAIEmbeddings", lambda model=None: DummyEmb(model=model))
    monkeypatch.setattr("app.adapters.vector_chroma.Chroma",
                        lambda collection_name=None, embedding_function=None, persist_directory=None:
                            DummyVS(collection_name, embedding_function, persist_directory))

    vs = build_vectorstore("test_coll")
    assert vs.collection_name == "test_coll"
    assert vs.embedding_function is not None
    assert vs.persist_directory is not None
