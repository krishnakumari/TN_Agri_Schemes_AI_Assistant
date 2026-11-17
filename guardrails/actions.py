import sys
import os
from typing import Optional
from nemoguardrails.actions import action

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from rag_engine import ask_rag


@action(name="call_rag_engine")
async def call_rag_engine(question: str, context: Optional[dict] = None) -> str:
    """
    Calls our FAISS + LangChain RAG engine with the selected response language.
    """
    language = "Auto"
    if context and "language" in context:
        language = context["language"]

    result = ask_rag(question=question, language=language)
    return result["answer"]