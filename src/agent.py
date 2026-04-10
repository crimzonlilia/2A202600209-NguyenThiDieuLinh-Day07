from typing import Callable

from .store import EmbeddingStore


class KnowledgeBaseAgent:
    """
    An agent that answers questions using a vector knowledge base.

    Retrieval-augmented generation (RAG) pattern:
        1. Retrieve top-k relevant chunks from the store.
        2. Build a prompt with the chunks as context.
        3. Call the LLM to generate an answer.
    """

    def __init__(self, store: EmbeddingStore, llm_fn: Callable[[str], str]) -> None:
        self.store = store
        self.llm_fn = llm_fn

    def answer(self, question: str, top_k: int = 3) -> str:
        # Retrieve top-k relevant chunks from the store
        candidates = []
        try:
            candidates = self.store.search(question, top_k=top_k)
        except Exception:
            candidates = []

        # Build a simple context from retrieved chunks
        context_parts = []
        for i, c in enumerate(candidates, start=1):
            content = c.get("content", "")
            md = c.get("metadata", {})
            context_parts.append(f"[{i}] {content} -- {md}")

        context = "\n".join(context_parts)
        prompt = f"Use the following context to answer the question.\n\nContext:\n{context}\n\nQuestion: {question}\nAnswer:"

        return self.llm_fn(prompt)
