import re
from dataclasses import dataclass


@dataclass
class Chunk:
    text: str
    index: int
    metadata: dict


def chunk_text(text: str, chunk_size: int = 500, overlap: int = 50) -> list[Chunk]:
    sentences = re.split(r"(?<=[.!?])\s+", text.strip())
    chunks: list[Chunk] = []
    current: list[str] = []
    current_len = 0
    idx = 0

    for sent in sentences:
        sent_len = len(sent)
        if current_len + sent_len > chunk_size and current:
            chunks.append(Chunk(text=" ".join(current), index=idx, metadata={}))
            idx += 1
            current = [current[-1]] if overlap > 0 and current else []
            current_len = len(current[0]) if current else 0
        current.append(sent)
        current_len += sent_len + 1

    if current:
        chunks.append(Chunk(text=" ".join(current), index=idx, metadata={}))
    return chunks