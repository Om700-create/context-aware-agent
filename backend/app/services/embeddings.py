"""
Local embedding function.

To keep the project runnable with zero internet access / model downloads,
we implement a deterministic hashing-based bag-of-words embedder by default
(EMBEDDING_PROVIDER=local). This is sufficient for the RAG pipeline to retrieve
relevant chunks for the demo. If you have `sentence-transformers` /
`nomic-embed-text` available, switch EMBEDDING_PROVIDER and plug it in here.
"""
import hashlib
import re
import math
from typing import List

VECTOR_DIM = 384


def _tokenize(text: str) -> List[str]:
    return re.findall(r"[a-zA-Z0-9]+", text.lower())


def embed_text(text: str) -> List[float]:
    vec = [0.0] * VECTOR_DIM
    tokens = _tokenize(text)
    if not tokens:
        return vec
    for tok in tokens:
        h = int(hashlib.md5(tok.encode()).hexdigest(), 16)
        idx = h % VECTOR_DIM
        sign = 1.0 if (h // VECTOR_DIM) % 2 == 0 else -1.0
        vec[idx] += sign

    norm = math.sqrt(sum(v * v for v in vec)) or 1.0
    return [v / norm for v in vec]


class LocalEmbeddingFunction:
    """Conforms to chromadb's EmbeddingFunction protocol."""

    def __call__(self, input: List[str]) -> List[List[float]]:
        return [embed_text(t) for t in input]

    def name(self) -> str:
        return "local-hashing-embedder"
