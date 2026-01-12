"""
Chunking utilities.

Phase 1 constraint:
- Avoid import-time dependency on OpenAI / langchain_experimental.
- Provide a deterministic fallback splitter for tests/offline usage.
"""

from __future__ import annotations

import re
from typing import List

try:
    from langchain_core.documents import Document
except Exception:  # pragma: no cover
    # Minimal fallback shape for tests that only need `page_content`.
    class Document:  # type: ignore[override]
        def __init__(self, page_content: str):
            self.page_content = page_content

class SemanticChunker:
    def __init__(self, threshold_percentile: int = 90):
        """
        初始化語意分塊器。
        
        Args:
            threshold_percentile: 斷點閾值百分位數。數值越高，分塊越少（越傾向於合併）；數值越低，分塊越細。
        """
        self.threshold_percentile = threshold_percentile
        self._splitter = None

        # Lazy init for the "real" semantic chunker.
        try:
            from langchain_experimental.text_splitter import SemanticChunker as LangChainSemanticChunker
            from langchain_openai import OpenAIEmbeddings

            self._splitter = LangChainSemanticChunker(
                OpenAIEmbeddings(),
                breakpoint_threshold_type="percentile",
                breakpoint_threshold_amount=threshold_percentile,
            )
        except Exception:
            # Offline/test fallback will be used.
            self._splitter = None

    def split_text(self, text: str) -> List:
        """
        將文本進行語意分塊。
        """
        if self._splitter is not None:
            return self._splitter.create_documents([text])

        # Fallback: split by blank lines / paragraph breaks.
        raw = (text or "").strip()
        if not raw:
            return []
        parts = [p.strip() for p in re.split(r"\n\s*\n+", raw) if p.strip()]
        return [Document(page_content=p) for p in parts]