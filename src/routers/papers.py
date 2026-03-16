from fastapi import APIRouter, Depends
from sqlalchemy import select
from sqlalchemy.orm import Session

from src.dependencies import get_db
from src.errors import BadRequestError, ConflictError, NotFoundError
from src.models.paper import Paper
from src.schemas.paper import PaperCreate, PaperCreateResponse, PaperOut

from src.services.ingestion.arxiv_ingestor import ingest_latest_cs_ai
from src.services.ingestion.arxiv_ingestor import (
    ingest_pipeline,
    ingest_stage_chunk,
    ingest_stage_fetch_store,
    ingest_stage_index,
    ingest_stage_parse,
)

router = APIRouter(prefix="/api/v1/papers", tags=["papers"])


@router.get("", response_model=list[PaperOut])
def list_papers(db: Session = Depends(get_db)) -> list[PaperOut]:
    papers = db.execute(select(Paper).order_by(Paper.id.desc())).scalars().all()
    return [
        PaperOut(
            id=p.id,
            arxiv_id=p.arxiv_id,
            title=p.title,
            authors=p.authors,
            published_at=p.published_at,
        )
        for p in papers
    ]

@router.get("/{paper_id}", response_model=PaperOut)
def get_paper(paper_id: int, db: Session = Depends(get_db)) -> PaperOut:
    paper = db.get(Paper, paper_id)
    if not paper:
        raise NotFoundError(
            message="Paper not found",
            code="PAPER_NOT_FOUND",
            context={"paper_id": paper_id},
        )

    return PaperOut(
        id=paper.id,
        arxiv_id=paper.arxiv_id,
        title=paper.title,
        authors=paper.authors,
        published_at=paper.published_at,
    )


@router.post("", response_model=PaperCreateResponse)
def create_paper(payload: PaperCreate, db: Session = Depends(get_db)) -> PaperCreateResponse:
    existing = db.execute(
        select(Paper).where(Paper.arxiv_id == payload.arxiv_id)
    ).scalar_one_or_none()
    if existing:
        raise ConflictError(
            message="Paper with this arxiv_id already exists",
            code="PAPER_ALREADY_EXISTS",
            context={"arxiv_id": payload.arxiv_id},
        )

    paper = Paper(
        arxiv_id=payload.arxiv_id,
        title=payload.title,
        abstract=payload.abstract,
        authors=payload.authors,
        pdf_url=payload.pdf_url,
        full_text=payload.full_text,
        published_at=payload.published_at,
    )
    db.add(paper)
    db.commit()
    db.refresh(paper)

    return PaperCreateResponse(id=paper.id, arxiv_id=paper.arxiv_id, status="created")


@router.post("/ingest")
def ingest_papers(max_results: int = 5, db: Session = Depends(get_db)) -> dict:
    if max_results < 1 or max_results > 50:
        raise BadRequestError(
            message="max_results must be between 1 and 50",
            code="INVALID_MAX_RESULTS",
            context={"max_results": max_results},
        )
    return ingest_latest_cs_ai(db=db, max_results=max_results)


@router.post("/ingest/pipeline")
def ingest_pipeline_route(max_results: int = 5, db: Session = Depends(get_db)) -> dict:
    if max_results < 1 or max_results > 50:
        raise BadRequestError(
            message="max_results must be between 1 and 50",
            code="INVALID_MAX_RESULTS",
            context={"max_results": max_results},
        )
    return ingest_pipeline(db=db, max_results=max_results)


@router.post("/ingest/fetch-store")
def ingest_fetch_store_route(max_results: int = 5, db: Session = Depends(get_db)) -> dict:
    if max_results < 1 or max_results > 50:
        raise BadRequestError(
            message="max_results must be between 1 and 50",
            code="INVALID_MAX_RESULTS",
            context={"max_results": max_results},
        )
    return ingest_stage_fetch_store(db=db, max_results=max_results)


@router.post("/ingest/parse")
def ingest_parse_route(limit: int = 20, db: Session = Depends(get_db)) -> dict:
    if limit < 1 or limit > 500:
        raise BadRequestError(
            message="limit must be between 1 and 500",
            code="INVALID_LIMIT",
            context={"limit": limit},
        )
    return ingest_stage_parse(db=db, limit=limit)


@router.post("/ingest/chunk")
def ingest_chunk_route(limit: int = 20, db: Session = Depends(get_db)) -> dict:
    if limit < 1 or limit > 500:
        raise BadRequestError(
            message="limit must be between 1 and 500",
            code="INVALID_LIMIT",
            context={"limit": limit},
        )
    return ingest_stage_chunk(db=db, limit=limit)


@router.post("/ingest/index")
def ingest_index_route(db: Session = Depends(get_db)) -> dict:
    return ingest_stage_index(db=db)
