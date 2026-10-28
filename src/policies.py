import json
from functools import lru_cache
from pathlib import Path

from langchain_core.documents import Document
from langchain_ollama import OllamaEmbeddings

from .config import CATALOG_PATH, OLLAMA_BASE_URL, OLLAMA_EMBED_MODEL, POLICY_DIR, POLICY_TOP_K, USE_SEMANTIC_RETRIEVAL

def load_policy_documents() -> list[Document]:
    catalog = {item["file"]: item for item in json.loads(CATALOG_PATH.read_text(encoding="utf-8"))}
    docs = []
    for relative, metadata in catalog.items():
        path = CATALOG_PATH.parent / relative
        docs.append(Document(page_content=path.read_text(encoding="utf-8"), metadata=metadata))
    return docs

class PolicyRetriever:
    def __init__(self):
        self.docs = load_policy_documents()
        self.store = None
        try:
            if not USE_SEMANTIC_RETRIEVAL:
                raise RuntimeError("Semantic retrieval disabled for fast local mode")
            from langchain_community.vectorstores import Chroma
            embeddings = OllamaEmbeddings(model=OLLAMA_EMBED_MODEL, base_url=OLLAMA_BASE_URL)
            self.store = Chroma.from_documents(self.docs, embeddings, collection_name="ma_policy_library")
        except Exception:
            # The app remains usable with lexical fallback when Ollama is not running.
            self.store = None

    def search(self, query: str) -> list[Document]:
        if self.store:
            try:
                return self.store.similarity_search(query, k=POLICY_TOP_K)
            except Exception:
                pass
        terms = set(query.lower().split())
        scored = []
        for doc in self.docs:
            score = sum(term in doc.page_content.lower() for term in terms)
            scored.append((score, doc))
        return [doc for score, doc in sorted(scored, key=lambda item: item[0], reverse=True)[:POLICY_TOP_K] if score > 0]

@lru_cache(maxsize=1)
def get_policy_retriever() -> PolicyRetriever:
    """Build the policy index once per application process."""
    return PolicyRetriever()
