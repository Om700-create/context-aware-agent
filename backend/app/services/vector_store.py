import chromadb
from app.core.config import settings
from app.services.embeddings import LocalEmbeddingFunction

_client = chromadb.PersistentClient(path=settings.CHROMA_PERSIST_DIR)
_embed_fn = LocalEmbeddingFunction()

_collection = _client.get_or_create_collection(
    name=settings.CHROMA_COLLECTION,
    embedding_function=_embed_fn,
    metadata={"hnsw:space": "cosine"},
)


def add_chunks(ids, texts, metadatas):
    _collection.add(ids=ids, documents=texts, metadatas=metadatas)


def query(text: str, n_results: int = 5, where: dict | None = None):
    return _collection.query(query_texts=[text], n_results=n_results, where=where)


def delete_document(document_id: str):
    _collection.delete(where={"document_id": document_id})
