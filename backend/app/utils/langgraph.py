"""
LangGraph integration placeholder.

This module provides a thin client interface and clear extension points to
integrate with a LangGraph-powered workflow for LLM Search. 
Sample usage (after implementing _request):

    from app.services.langgraph import LangChainSearch
    client = LangChainSearch()
    answer = client.qa(
        question="Find Delaware NDA terms",
        context={"doc_ids": [1,2,3]}
    )

"""
from __future__ import annotations

from typing import Any, Dict, Optional, List

from app.db.session import get_session
from app.models.document import Document
from sqlmodel import select

# --- Minimal LangChain-style placeholder for DB + LLM QA ---
class LangChainSearch:
    """Naive DB retriever + optional LLM summarize."""

    def __init__(self) -> None:
        try:
            # Optional import. If missing, we degrade gracefully.
            from langchain_core.prompts import PromptTemplate  # type: ignore
            from langchain_openai import ChatOpenAI  # type: ignore
            self._PromptTemplate = PromptTemplate
            self._ChatOpenAI = ChatOpenAI
            self._has_lc = True
        except Exception:
            self._PromptTemplate = None
            self._ChatOpenAI = None
            self._has_lc = False

    def _retrieve(self, question: str, top_k: int = 3) -> List[Document]:
        # Simple LIKE search over Document.text.
        with get_session() as s:
            q = select(Document).where(Document.text.is_not(None))
            docs = list(s.exec(q))
        question_l = question.lower()
        scored = []
        for d in docs:
            t = (d.text or "").lower()
            score = t.count(question_l) if question_l else 0
            if score > 0:
                scored.append((score, d))
        scored.sort(key=lambda x: x[0], reverse=True)
        return [d for _, d in scored[:top_k]] or docs[:top_k]

    def qa(self, question: str, top_k: int = 3) -> Dict[str, Any]:
        ctx_docs = self._retrieve(question, top_k=top_k)
        context = "\n\n".join(
            f"[{d.id}] {d.filename}\n{(d.text or '')[:1200]}" for d in ctx_docs
        )
        if not self._has_lc:
            return {
                "ok": False,
                "placeholder": True,
                "message": "Install langchain-core and langchain-openai to enable LLM.",
                "question": question,
                "context_preview": context[:2000],
                "doc_ids": [d.id for d in ctx_docs],
            }

        prompt = self._PromptTemplate.from_template(
            "You are a legal assistant. Using the context, answer briefly.\n\nContext:\n{context}\n\nQuestion: {question}"
        )
        chain = prompt | self._ChatOpenAI(temperature=0)  # type: ignore
        resp = chain.invoke({"context": context, "question": question})
        answer = getattr(resp, "content", str(resp))
        return {
            "ok": True,
            "answer": answer,
            "doc_ids": [d.id for d in ctx_docs],
        }


_singleton_lc: Optional[LangChainSearch] = None


def get_langchain_search() -> LangChainSearch:
    global _singleton_lc
    if _singleton_lc is None:
        _singleton_lc = LangChainSearch()
    return _singleton_lc
