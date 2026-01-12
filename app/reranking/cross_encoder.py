"""
Reranking utilities.

Phase 1 constraint:
- Avoid import-time dependency on sentence-transformers/torch.
- Provide a heuristic fallback reranker (deterministic, no GPU).
"""

from __future__ import annotations

import re
from typing import List, Optional

class Reranker:
    def __init__(self, model_name: str = "cross-encoder/ms-marco-MiniLM-L-6-v2"):
        """
        初始化 Cross-Encoder 模型。
        選擇 ms-marco-MiniLM-L-6-v2 是因為它在速度與精度上取得了極佳的平衡。
        """
        self.model_name = model_name
        self._model: Optional[object] = None

        # Lazy import; if it fails, fallback mode is used.
        try:
            from sentence_transformers import CrossEncoder

            self._model = CrossEncoder(model_name)
        except Exception:
            self._model = None

    def rank(self, query: str, documents: List[str], top_k: int = 3) -> List[str]:
        """
        對文檔列表進行重排序。
        """
        if not documents:
            return []

        if self._model is not None:
            pairs = [[query, doc] for doc in documents]
            scores = self._model.predict(pairs)  # type: ignore[attr-defined]
            doc_score_pairs = list(zip(documents, scores))
            doc_score_pairs.sort(key=lambda x: x[1], reverse=True)
            return [doc for doc, _score in doc_score_pairs[:top_k]]
            
        # Heuristic fallback: token overlap + simple negation/exclusion boost
        q = (query or "").lower()
        q_tokens = set(re.findall(r"[\w\u4e00-\u9fff]+", q))
        ask_cover = any(x in q for x in ["涵蓋", "包含", "保固", "是否"])

        def score(doc: str) -> int:
            d = (doc or "").lower()
            d_tokens = set(re.findall(r"[\w\u4e00-\u9fff]+", d))
            base = len(q_tokens & d_tokens)
            if ask_cover and any(x in d for x in ["不涵蓋", "不包括", "排除", "不予"]):
                base += 5
            if ask_cover and any(x in d for x in ["涵蓋", "包括", "包含"]):
                base += 1
            return base

        ranked = sorted(documents, key=score, reverse=True)
        return ranked[:top_k]