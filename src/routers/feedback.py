from fastapi import APIRouter, Depends
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session

from src.dependencies import get_db, get_tracer_service
from src.errors import StorageError
from src.models.feedback import Feedback
from src.schemas.feedback import FeedbackCreateRequest, FeedbackCreateResponse
from src.services.langfuse.tracer import Tracer

router = APIRouter(prefix="/api/v1/feedback", tags=["feedback"])


@router.post("", response_model=FeedbackCreateResponse)
def create_feedback(
    payload: FeedbackCreateRequest,
    db: Session = Depends(get_db),
    tracer_service: Tracer = Depends(get_tracer_service),
) -> FeedbackCreateResponse:
    feedback = Feedback(
        trace_id=payload.trace_id,
        score=payload.score,
        comment=payload.comment,
        channel=payload.channel,
    )

    try:
        db.add(feedback)
        db.commit()
        db.refresh(feedback)
    except SQLAlchemyError as exc:
        raise StorageError(
            message=f"Failed to store feedback: {exc}",
            code="FEEDBACK_STORE_FAILED",
            context={"trace_id": payload.trace_id},
        ) from exc

    forwarded = tracer_service.submit_feedback(
        trace_id=payload.trace_id,
        score=payload.score,
        comment=payload.comment,
        name="feedback_score",
    )
    print(f"[feedback] forwarded_to_langfuse={forwarded} trace_id={payload.trace_id}")

    return FeedbackCreateResponse(
        id=feedback.id,
        status="recorded",
        trace_id=feedback.trace_id,
        created_at=feedback.created_at,
    )
