from src.services.indexing.text_chunker import TextChunker


def main() -> None:
    sample = (
        "Retrieval-augmented generation systems combine retrieval and generation. "
        "Chunking quality strongly affects downstream retrieval relevance and final answer quality. "
        "Overlapping chunks preserve context continuity between adjacent segments."
    )
    chunker = TextChunker(chunk_size=90, overlap=20)
    chunks = chunker.chunk_text(sample)

    print(f"chunks={len(chunks)}")
    for c in chunks:
        print(f"{c.chunk_id}: {c.start_char}-{c.end_char} :: {c.text}")


if __name__ == "__main__":
    main()
