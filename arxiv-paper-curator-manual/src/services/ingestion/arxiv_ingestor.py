from datetime import datetime, timezone
import json

from sqlalchemy import delete, select
from sqlalchemy.orm import Session

from src.models.paper import Paper
from src.models.paper_chunk import PaperChunk
from src.services.indexing.text_chunker import TextChunker
from src.services.metadata_fetcher import ArxivMetadataFetcher
from src.services.opensearch.chunk_indexer import reindex_all_chunks
from src.services.opensearch.indexer import reindex_all_papers
from src.services.opensearch.vector_indexer import reindex_all_chunk_embeddings
from src.services.pdf_parser.parser import make_pdf_parser


def _parse_published(value: str) -> datetime | None:
    if not value:
        return None
    return datetime.fromisoformat(value.replace("Z", "+00:00")).astimezone(timezone.utc)


def ingest_stage_fetch_store(db: Session, max_results: int = 5) -> dict:
    fetcher = ArxivMetadataFetcher(delay_seconds=0.5)
    papers = fetcher.fetch_latest_cs_ai(max_results=max_results)

    created = 0
    updated = 0

    for item in papers:
        existing = db.execute(select(Paper).where(Paper.arxiv_id == item.arxiv_id)).scalar_one_or_none()

        if existing:
            existing.title = item.title
            existing.abstract = item.abstract
            existing.authors = item.authors
            existing.pdf_url = item.pdf_url
            existing.published_at = _parse_published(item.published_at)
            updated += 1
            continue

        db.add(
            Paper(
                arxiv_id=item.arxiv_id,
                title=item.title,
                abstract=item.abstract,
                authors=item.authors,
                pdf_url=item.pdf_url,
                full_text=None,
                published_at=_parse_published(item.published_at),
            )
        )
        created += 1

    db.commit()
    return {
        "stage": "fetch_store",
        "fetched": len(papers),
        "created": created,
        "updated": updated,
        "ingested_ids": [p.arxiv_id for p in papers],
    }


def ingest_stage_parse(db: Session, limit: int = 50) -> dict:
    parser = make_pdf_parser()
    rows = db.execute(select(Paper).order_by(Paper.id.desc()).limit(limit)).scalars().all()

    parsed_count = 0
    fallback_to_abstract = 0
    skipped = 0
    parse_failures = 0

    for paper in rows:
        if paper.full_text and paper.full_text.strip():
            skipped += 1
            continue

        try:
            if hasattr(parser, "parse_document"):
                parsed_document = parser.parse_document(paper.pdf_url)
                parsed_text = (parsed_document.full_text or "").strip()
                metadata_json = parsed_document.model_dump_json()
            else:
                parsed_text = parser.parse_from_url(paper.pdf_url)
                metadata_json = json.dumps(
                    {
                        "provider": "legacy",
                        "status": "ok" if parsed_text else "empty",
                        "sections": [],
                        "references": [],
                    }
                )
        except Exception as exc:
            parse_failures += 1
            parsed_text = ""
            metadata_json = json.dumps(
                {
                    "provider": "unknown",
                    "status": "error",
                    "error": str(exc),
                    "sections": [],
                    "references": [],
                }
            )
            print(f"[parse] paper_id={paper.id} arxiv_id={paper.arxiv_id} error={exc}")

        if parsed_text.strip():
            paper.full_text = parsed_text
            paper.parser_metadata_json = metadata_json
            parsed_count += 1
        else:
            paper.full_text = paper.abstract
            paper.parser_metadata_json = json.dumps(
                {
                    "provider": "fallback",
                    "status": "fallback_to_abstract",
                    "sections": [],
                    "references": [],
                }
            )
            fallback_to_abstract += 1

    db.commit()
    return {
        "stage": "parse",
        "scanned": len(rows),
        "parsed": parsed_count,
        "fallback_to_abstract": fallback_to_abstract,
        "skipped": skipped,
        "parse_failures": parse_failures,
    }


def ingest_stage_chunk(db: Session, limit: int = 200) -> dict:
    chunker = TextChunker(chunk_size=800, overlap=120)
    rows = db.execute(select(Paper).order_by(Paper.id.desc()).limit(limit)).scalars().all()

    papers_processed = 0
    chunks_created = 0
    section_aware_papers = 0

    for paper in rows:
        source_text = (paper.full_text or "").strip() or (paper.abstract or "").strip()
        if not source_text:
            continue

        db.execute(delete(PaperChunk).where(PaperChunk.paper_id == paper.id))

        metadata_sections: list[dict] = []
        metadata_raw = getattr(paper, "parser_metadata_json", None)
        if metadata_raw:
            try:
                parsed_metadata = json.loads(metadata_raw)
                sections = parsed_metadata.get("sections", [])
                if isinstance(sections, list):
                    metadata_sections = [s for s in sections if isinstance(s, dict)]
            except Exception:
                metadata_sections = []

        chunk_index_counter = 1
        running_offset = 0
        if metadata_sections:
            for section in metadata_sections:
                section_text = " ".join(str(section.get("text", "")).split()).strip()
                if not section_text:
                    continue

                section_order = int(section.get("order", 0)) if str(section.get("order", "")).isdigit() else None
                section_title = str(section.get("title", "")).strip() or None
                section_chunks = chunker.chunk_text(section_text)
                for chunk in section_chunks:
                    db.add(
                        PaperChunk(
                            paper_id=paper.id,
                            chunk_index=chunk_index_counter,
                            chunk_text=chunk.text,
                            start_char=running_offset + chunk.start_char,
                            end_char=running_offset + chunk.end_char,
                            section_title=section_title,
                            section_order=section_order,
                        )
                    )
                    chunk_index_counter += 1
                running_offset += len(section_text) + 2

            if chunk_index_counter > 1:
                section_aware_papers += 1
        else:
            chunks = chunker.chunk_text(source_text)
            for chunk in chunks:
                db.add(
                    PaperChunk(
                        paper_id=paper.id,
                        chunk_index=chunk.chunk_id,
                        chunk_text=chunk.text,
                        start_char=chunk.start_char,
                        end_char=chunk.end_char,
                        section_title=None,
                        section_order=None,
                    )
                )
            chunk_index_counter = len(chunks) + 1

        papers_processed += 1
        chunks_created += chunk_index_counter - 1

    db.commit()
    return {
        "stage": "chunk",
        "papers_processed": papers_processed,
        "chunks_created": chunks_created,
        "section_aware_papers": section_aware_papers,
    }


def ingest_stage_index(db: Session) -> dict:
    paper_index_result = reindex_all_papers(db)
    chunk_index_result = reindex_all_chunks(db)

    vector_status = "ok"
    vector_indexed = 0
    vector_error = ""
    try:
        vector_indexed = reindex_all_chunk_embeddings(db).get("indexed", 0)
    except Exception as exc:
        vector_status = "error"
        vector_error = str(exc)

    return {
        "stage": "index",
        "papers_indexed": paper_index_result.get("indexed", 0),
        "chunks_indexed": chunk_index_result.get("indexed", 0),
        "vector_indexed": vector_indexed,
        "vector_status": vector_status,
        "vector_error": vector_error,
    }


def ingest_pipeline(db: Session, max_results: int = 5) -> dict:
    fetch_result = ingest_stage_fetch_store(db=db, max_results=max_results)
    parse_result = ingest_stage_parse(db=db, limit=max_results * 3)
    chunk_result = ingest_stage_chunk(db=db, limit=max_results * 3)
    index_result = ingest_stage_index(db=db)

    return {
        "pipeline": "arxiv_ingest_v2",
        "fetch_store": fetch_result,
        "parse": parse_result,
        "chunk": chunk_result,
        "index": index_result,
    }


def ingest_latest_cs_ai(db: Session, max_results: int = 5) -> dict:
    # Backward-compatible summary for existing endpoint/tests.
    result = ingest_stage_fetch_store(db=db, max_results=max_results)
    return {
        "fetched": result["fetched"],
        "created": result["created"],
        "updated": result["updated"],
        "ingested_ids": result["ingested_ids"],
    }
