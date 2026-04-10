from __future__ import annotations

import math
import re


class FixedSizeChunker:
    """
    Split text into fixed-size chunks with optional overlap.

    Rules:
        - Each chunk is at most chunk_size characters long.
        - Consecutive chunks share overlap characters.
        - The last chunk contains whatever remains.
        - If text is shorter than chunk_size, return [text].
    """

    def __init__(self, chunk_size: int = 500, overlap: int = 50) -> None:
        self.chunk_size = chunk_size
        self.overlap = overlap

    def chunk(self, text: str) -> list[str]:
        if not text:
            return []
        if len(text) <= self.chunk_size:
            return [text]

        step = self.chunk_size - self.overlap
        chunks: list[str] = []
        for start in range(0, len(text), step):
            chunk = text[start : start + self.chunk_size]
            chunks.append(chunk)
            if start + self.chunk_size >= len(text):
                break
        return chunks


class SentenceChunker:
    """
    Split text into chunks of at most max_sentences_per_chunk sentences.

    Sentence detection: split on ". ", "! ", "? " or ".\n".
    Strip extra whitespace from each chunk.
    """

    def __init__(self, max_sentences_per_chunk: int = 3) -> None:
        self.max_sentences_per_chunk = max(1, max_sentences_per_chunk)

    def chunk(self, text: str) -> list[str]:
        if not text:
            return []

        # Capture sentences ending with '. ', '! ', '? ' or '.\n' (or end of text).
        pattern = re.compile(r".*?(?:\. |! |\? |\.\n|$)", re.S)
        raw_sentences = [m.group(0).strip() for m in pattern.finditer(text)]
        sentences = [s for s in raw_sentences if s]

        chunks: list[str] = []
        for i in range(0, len(sentences), self.max_sentences_per_chunk):
            group = sentences[i : i + self.max_sentences_per_chunk]
            # Join with single space and strip extra whitespace
            chunks.append(" ".join(s.strip() for s in group).strip())

        return chunks


class RecursiveChunker:
    """
    Recursively split text using separators in priority order.

    Default separator priority:
        ["\n\n", "\n", ". ", " ", ""]
    """

    DEFAULT_SEPARATORS = ["\n\n", "\n", ". ", " ", ""]

    def __init__(self, separators: list[str] | None = None, chunk_size: int = 500) -> None:
        self.separators = self.DEFAULT_SEPARATORS if separators is None else list(separators)
        self.chunk_size = chunk_size

    def chunk(self, text: str) -> list[str]:
        if not text:
            return []
        return [c for c in self._split(text, list(self.separators)) if c]

    def _split(self, current_text: str, remaining_separators: list[str]) -> list[str]:
        # Base case: short enough or no separators left -> fixed-size slices
        if len(current_text) <= self.chunk_size:
            return [current_text.strip()]

        if not remaining_separators:
            # fallback to fixed-size splitting
            chunks: list[str] = []
            for i in range(0, len(current_text), self.chunk_size):
                chunks.append(current_text[i : i + self.chunk_size].strip())
            return chunks

        sep = remaining_separators[0]
        rest_seps = remaining_separators[1:]

        if sep == "":
            # character-level fallback
            return self._split(current_text, [])

        parts = current_text.split(sep)
        # Reattach separator except for the last part
        fragments: list[str] = []
        for i, p in enumerate(parts):
            frag = p
            if i < len(parts) - 1:
                frag = frag + sep
            if frag:
                fragments.append(frag)

        chunks: list[str] = []
        buffer: str = ""

        for frag in fragments:
            piece = frag
            if len(piece) > self.chunk_size:
                # Too large: recurse using lower-priority separators
                if buffer:
                    chunks.append(buffer.strip())
                    buffer = ""
                sub = self._split(piece, rest_seps)
                for s in sub:
                    chunks.append(s)
                continue

            # Greedy append to buffer
            if not buffer:
                buffer = piece
            elif len(buffer) + len(piece) <= self.chunk_size:
                buffer += piece
            else:
                chunks.append(buffer.strip())
                buffer = piece

        if buffer:
            chunks.append(buffer.strip())

        return chunks


def _dot(a: list[float], b: list[float]) -> float:
    return sum(x * y for x, y in zip(a, b))


def compute_similarity(vec_a: list[float], vec_b: list[float]) -> float:
    """
    Compute cosine similarity between two vectors.

    cosine_similarity = dot(a, b) / (||a|| * ||b||)

    Returns 0.0 if either vector has zero magnitude.
    """
    if not vec_a or not vec_b:
        return 0.0

    dot_prod = _dot(vec_a, vec_b)
    norm_a = math.sqrt(sum(x * x for x in vec_a))
    norm_b = math.sqrt(sum(x * x for x in vec_b))

    if norm_a == 0.0 or norm_b == 0.0:
        return 0.0

    return dot_prod / (norm_a * norm_b)


class ChunkingStrategyComparator:
    """Run all built-in chunking strategies and compare their results."""

    def compare(self, text: str, chunk_size: int = 200) -> dict:
        # Run three chunking strategies and collect simple stats
        fixed = FixedSizeChunker(chunk_size=chunk_size, overlap=0).chunk(text)
        # Derive a reasonable sentences-per-chunk parameter from chunk_size
        sent_per_chunk = max(1, chunk_size // 100)
        by_sent = SentenceChunker(max_sentences_per_chunk=sent_per_chunk).chunk(text)
        rec = RecursiveChunker(chunk_size=chunk_size).chunk(text)

        def stats(chunks: list[str]) -> dict:
            count = len(chunks)
            avg = float(sum(len(c) for c in chunks) / count) if count else 0.0
            return {"count": count, "avg_length": avg, "chunks": chunks}

        return {
            "fixed_size": stats(fixed),
            "by_sentences": stats(by_sent),
            "recursive": stats(rec),
        }
