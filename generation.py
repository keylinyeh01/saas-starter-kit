"""
Generation layer for Enterprise Contract Sentinel.

Design goals (Phase 1):
- Import-time must not pull heavyweight optional deps (torch/transformers/ollama).
- `ContractAnalyst.analyze()` must be stable: always returns a dict with a predictable schema.
- REAL LOGIC ONLY: No hardcoded fallback answers or synonym hacking.
"""

from __future__ import annotations

import os
import re
from dataclasses import dataclass
from typing import Any, Dict, Literal, Tuple


Backend = Literal["ollama", "dummy"]


@dataclass(frozen=True)
class AnalystResult:
    """A normalized, structured result for downstream UI/tests."""

    status: Literal["REPORT", "CONSULT", "ERROR"]
    content: str
    risk: Literal["HIGH_RISK", "NORMAL"] | None = None
    meta: Dict[str, Any] | None = None

    def to_dict(self) -> Dict[str, Any]:
        out: Dict[str, Any] = {"status": self.status, "content": self.content}
        if self.risk is not None:
            out["risk"] = self.risk
        if self.meta:
            out["meta"] = self.meta
        return out


class ContractAnalyst:
    def __init__(
        self,
        *,
        backend: Backend | None = None,
        ollama_model: str | None = None,
        temperature: float = 0.0, # TDD: Set to 0.0 for deterministic output
    ):
        """
        Args:
            backend: "ollama" or "dummy". Default follows `ECS_LLM_BACKEND`.
            ollama_model: Ollama model name. Default follows `ECS_OLLAMA_MODEL`.
            temperature: LLM temperature.
        """

        self._backend: Backend = (backend or os.getenv("ECS_LLM_BACKEND", "dummy")).lower()  # type: ignore[assignment]
        self._ollama_model = ollama_model or os.getenv("ECS_OLLAMA_MODEL", "qwen2.5:14b")
        self._temperature = temperature

        # Lazy-initialized chain
        self._chain = None

    def _extract_thresholds(self, text: str) -> list[str]:
        """Extract unique percentage thresholds like '30%'."""
        return sorted(set(re.findall(r"(\d+(?:\.\d+)?%)", text)))

    def _format_consultation_msg(self, thresholds: list[str]) -> str:
        """
        Format a disambiguation message for ambiguous thresholds.
        
        IMPORTANT: This function uses NO hardcoded business scenarios. It dynamically
        presents the extracted thresholds and asks the user to clarify, making it
        suitable for global random companies and random documents.
        """
        # Sort thresholds numerically for better presentation
        sorted_thresholds = sorted(thresholds, key=lambda x: float(x.strip('%')))
        min_threshold = sorted_thresholds[0] if sorted_thresholds else thresholds[0]
        max_threshold = sorted_thresholds[-1] if sorted_thresholds else thresholds[-1]
        
        return (
            "📢 **潛在法律歧義偵測**\n\n"
            f"合約中存在多個門檻定義（{', '.join(thresholds)}）。\n"
            "請確認您關注的具體情境，以利精確判斷風險：\n\n"
            f"1️⃣ **較低門檻**：{min_threshold}（可能適用於特定情境）\n"
            f"2️⃣ **較高門檻**：{max_threshold}（可能適用於其他情境）\n\n"
            "建議：請參考合約原文中每個門檻對應的具體條款，以確定適用情境。"
        )

    def _normalize_inputs(self, a: str, b: str) -> Tuple[str, str]:
        """
        Input normalization to ensure (question, context) order.
        """
        a = (a or "").strip()
        b = (b or "").strip()

        def looks_like_question(x: str) -> bool:
            return (len(x) <= 200 and x.endswith("?")) or ("？" in x and len(x) <= 200)

        if looks_like_question(a) and not looks_like_question(b):
            return a, b
        if looks_like_question(b) and not looks_like_question(a):
            return b, a
        # Fallback: treat the longer one as context.
        if len(a) >= len(b):
            return b, a # b is question
        return a, b # a is question

    def _ensure_chain(self):
        if self._chain is not None:
            return
        
        # Lazy import
        from langchain_core.output_parsers import StrOutputParser
        from langchain_core.prompts import ChatPromptTemplate

        if self._backend == "ollama":
            from langchain_community.chat_models import ChatOllama
            llm = ChatOllama(model=self._ollama_model, temperature=self._temperature)
        else:
            llm = None

        # TDD: Strict prompt to prevent hallucination
        prompt = ChatPromptTemplate.from_template(
            """
你是一位專業的合約審查 AI 律師。請僅根據提供的【合約條款】回答【使用者問題】。

【合約條款】：
{context}

【使用者問題】：
{question}

嚴格指令：
1. 你的任務是從條款中提取事實。如果條款中沒有提到問題的答案，請直接回答「合約中未提及相關資訊」，**絕對不要**編造或引用外部常識。
2. 回覆時必須嚴格遵守以下格式，標籤必須完整：

[現況]: (描述從合約中找到的具體條文內容)
[風險]: (根據上述條文進行風險判定，若無條文則寫「無法評估」)
[建議]: (基於風險的行動建議)

注意：若找不到相關資訊，三個欄位請誠實反映，不要給出通用建議。
""".strip()
        )

        if llm is None:
            self._chain = None
        else:
            self._chain = prompt | llm | StrOutputParser()

    def analyze(self, a: str, b: str) -> Dict[str, Any]:
        """
        Analyze a question against retrieved context.
        """
        question, context = self._normalize_inputs(a, b)
        thresholds = self._extract_thresholds(context)

        # CONSULT mode: ambiguity check (Keep this logic as it relies on extracted data, not hardcodes)
        if len(thresholds) > 1 and ("change of control" in question.lower() or "控制權" in question):
            return AnalystResult(
                status="CONSULT",
                content=self._format_consultation_msg(thresholds),
                meta={"thresholds": thresholds},
            ).to_dict()

        # Risk heuristic (Only if we have data)
        is_high_risk = any(float(t.strip("%")) < 50 for t in thresholds)
        risk_level: Literal["HIGH_RISK", "NORMAL"] = "HIGH_RISK" if is_high_risk else "NORMAL"

        # Dummy backend: NO fake answers. Just extraction.
        if self._backend == "dummy":
            highlights = _extract_relevant_sentences(question, context, max_sentences=3)
            
            if not highlights:
                content = (
                    "[現況]: 未在提供的文本中找到關鍵字匹配的句子。\n"
                    "[風險]: 無法評估。\n"
                    "[建議]: 請檢查索引內容或使用更精確的關鍵字。"
                )
            else:
                evidence = "；".join(highlights)
                content = (
                    f"[現況]: 根據關鍵字匹配找到：{evidence}\n"
                    f"[風險]: (Dummy模式不進行語意分析)\n"
                    f"[建議]: 請切換至真實 LLM 以獲得完整分析。"
                )
            
            return AnalystResult(status="REPORT", risk=risk_level, content=content).to_dict()

        # Real LLM backend
        try:
            self._ensure_chain()
            if self._chain is None:
                raise RuntimeError("LLM backend not initialized")
            response = self._chain.invoke({"context": context, "question": question})
            return AnalystResult(status="REPORT", risk=risk_level, content=str(response)).to_dict()
        except Exception as e:
            return AnalystResult(status="ERROR", content=f"LLM 呼叫失敗: {e}", meta={"backend": self._backend}).to_dict()


def _extract_relevant_sentences(question: str, context: str, *, max_sentences: int = 3) -> list[str]:
    """
    Simple extractive logic for dummy mode. 
    REMOVED: All heuristic query expansions (net60, synonyms).
    """
    q = (question or "").strip()
    c = (context or "").strip()
    if not q or not c:
        return []

    # Split context into sentences
    parts = re.split(r"[。！？!?]\s*|\n+", c)
    parts = [p.strip() for p in parts if p and p.strip()]

    # Simple token set from question
    q_low = q.lower()
    q_words = set(re.findall(r"[a-z0-9%\-]+", q_low))
    q_cjk = re.findall(r"[\u4e00-\u9fff]", q)
    for ch in q_cjk:
        q_words.add(ch)
    # Add bigrams for CJK
    for i in range(len(q_cjk) - 1):
        q_words.add(q_cjk[i] + q_cjk[i + 1])

    scored: list[tuple[int, str]] = []
    for s in parts:
        s_low = s.lower()
        s_words = set(re.findall(r"[a-z0-9%\-]+", s_low))
        s_cjk = re.findall(r"[\u4e00-\u9fff]", s)
        for ch in s_cjk:
            s_words.add(ch)
        for i in range(len(s_cjk) - 1):
            s_words.add(s_cjk[i] + s_cjk[i + 1])
            
        inter = q_words & s_words
        # Simple overlap score
        score = sum(2 if len(t) >= 2 else 1 for t in inter)
        if score > 0:
            scored.append((score, s))

    scored.sort(key=lambda x: x[0], reverse=True)
    return [s for _score, s in scored[:max_sentences]]