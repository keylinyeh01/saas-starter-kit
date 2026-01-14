"""
Retrieval layer for Enterprise Contract Sentinel.

Phase 1 constraints:
- Import-time must be quiet (no debug prints) and must not require transformers/torch.
- Provide a naive in-memory backend for tests/offline usage.
- REAL LOGIC ONLY: No keyword stuffing or synonym hacking.
"""

from __future__ import annotations

import os
import re
from dataclasses import dataclass
from typing import Any, Dict, List, Literal


Backend = Literal["chroma", "naive"]


@dataclass
class SimpleDocument:
    """Lightweight replacement for LangChain `Document` in fallback mode."""
    page_content: str
    metadata: Dict[str, Any] | None = None

class VectorStoreManager:
    def __init__(self, persist_directory: str = "./chroma_db", *, backend: Backend | None = None):
        """
        初始化向量資料庫管理器
        """
        self.persist_directory = persist_directory
        self._backend: Backend = (backend or os.getenv("ECS_VECTORSTORE_BACKEND", "naive")).lower()  # type: ignore[assignment]

        self._docs: List[SimpleDocument] = []
        self._vector_store = None

        if self._backend == "chroma":
            try:
                from langchain_community.embeddings import HuggingFaceEmbeddings
                from langchain_community.vectorstores import Chroma

                embedding_model = os.getenv("ECS_EMBEDDING_MODEL", "BAAI/bge-m3")
                self.embedding_fn = HuggingFaceEmbeddings(model_name=embedding_model)
                self._vector_store = Chroma(
                    persist_directory=self.persist_directory,
                    embedding_function=self.embedding_fn,
                    collection_name="contract_rules",
                )
            except Exception:
                self._backend = "naive"

    def add_documents(self, texts):
        if not texts:
            return

        if self._backend == "chroma" and self._vector_store is not None:
            from langchain_core.documents import Document
            docs = [Document(page_content=t) for t in texts]
            self._vector_store.add_documents(docs)
            return

        # Naive in-memory store
        for t in texts:
            self._docs.append(SimpleDocument(page_content=t))

    def search(self, query, k=10):
        """
        語意檢索：根據 Query 找出最相關的 k 筆資料
        """
        if self._backend == "chroma" and self._vector_store is not None:
            return self._vector_store.similarity_search(query, k=k)

        # Naive scoring (CJK-aware): Just token overlap. NO synonyms.
        q = (query or "").strip()
        q_tokens = _tokenize_for_search(q)
        if not q_tokens:
            return []

        def score(doc: SimpleDocument) -> int:
            d_tokens = _tokenize_for_search(doc.page_content or "")
            inter = q_tokens & d_tokens
            # Simple overlap scoring
            return sum(2 if len(t) >= 2 else 1 for t in inter)

        ranked = sorted(self._docs, key=score, reverse=True)
        return ranked[:k]


def _tokenize_for_search(text: str) -> set[str]:
    """
    Tokenize text for naive fallback retrieval.
    REMOVED: All manual synonym expansions. 
    Only extracts actual words/characters present in the text.
    """
    s = (text or "").lower()
    tokens: set[str] = set()

    # Extract alphanumerics (e.g., "net", "60", "xj-900-z", "30%")
    for w in re.findall(r"[a-z0-9%\-]+", s):
        if w:
            tokens.add(w)

    # Extract CJK characters
    cjk = re.findall(r"[\u4e00-\u9fff]", s)
    for ch in cjk:
        tokens.add(ch)

    # CJK bigrams (improves matching for specific terms)
    for i in range(len(cjk) - 1):
        tokens.add(cjk[i] + cjk[i + 1])

    return tokens