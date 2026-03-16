from dataclasses import dataclass


@dataclass
class TextChunk:
    chunk_id: int
    text: str
    start_char: int
    end_char: int


class TextChunker:
    def __init__(self, chunk_size: int = 800, overlap: int = 120) -> None:
        if chunk_size <= 0:
            raise ValueError("chunk_size must be > 0")
        if overlap < 0:
            raise ValueError("overlap must be >= 0")
        if overlap >= chunk_size:
            raise ValueError("overlap must be < chunk_size")
        self.chunk_size = chunk_size
        self.overlap = overlap

    def chunk_text(self, text: str) -> list[TextChunk]:
        cleaned = " ".join(text.split()).strip()
        if not cleaned:
            return []

        chunks: list[TextChunk] = []
        start = 0
        chunk_id = 1

        while start < len(cleaned):
            end = min(start + self.chunk_size, len(cleaned))
            chunk_text = cleaned[start:end].strip()

            if chunk_text:
                chunks.append(
                    TextChunk(
                        chunk_id=chunk_id,
                        text=chunk_text,
                        start_char=start,
                        end_char=end,
                    )
                )
                chunk_id += 1

            if end == len(cleaned):
                break

            start = max(0, end - self.overlap)

        return chunks
