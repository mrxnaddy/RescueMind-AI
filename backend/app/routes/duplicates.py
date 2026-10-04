from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from app.database import get_db
from app.models.duplicate_candidate import DuplicateCandidate
from app.models.incident import Incident
from app.schemas.duplicate import (
    DuplicateCandidateView,
    EmbeddingTestRequest,
    ReviewRequest,
)
from app.services.duplicate_review_service import (
    ReviewError,
    build_candidate_views,
    confirm_merge,
    reject_candidate,
)
from app.services.duplicate_service import check_for_duplicates
from app.services.embedding_service import (
    EmbeddingError,
    cosine_similarity,
    embed_texts,
    get_model_name,
)

router = APIRouter(
    prefix="/api/duplicates",
    tags=["Duplicate Detection"],
)


@router.post("/embedding-test")
def embedding_test(request: EmbeddingTestRequest):
    try:
        vectors = embed_texts(request.texts)
    except EmbeddingError as exc:
        raise HTTPException(status_code=503, detail=str(exc))

    pairs = []

    for i in range(len(vectors)):
        for j in range(i + 1, len(vectors)):
            pairs.append(
                {
                    "text_a": i,
                    "text_b": j,
                    "similarity": round(
                        cosine_similarity(vectors[i], vectors[j]), 4
                    ),
                }
            )

    return {
        "model": get_model_name(),
        "dimensions": len(vectors[0]),
        "texts": [
            f"{index}: {text[:70]}"
            for index, text in enumerate(request.texts)
        ],
        "pairs": pairs,
    }


@router.post("/incidents/{incident_id}/check")
def check_incident_for_duplicates(
    incident_id: int,
    db: Session = Depends(get_db),
):
    incident = (
        db.query(Incident)
        .filter(Incident.id == incident_id)
        .first()
    )

    if incident is None:
        raise HTTPException(
            status_code=404,
            detail="Incident not found",
        )

    return check_for_duplicates(incident_id, db)


@router.get(
    "/candidates",
    response_model=list[DuplicateCandidateView],
)
def list_candidates(
    status: str = Query(
        default="pending",
        description="pending, confirmed, rejected, superseded or all",
    ),
    skip: int = Query(default=0, ge=0),
    limit: int = Query(default=20, ge=1, le=100),
    db: Session = Depends(get_db),
):
    query = db.query(DuplicateCandidate)

    if status != "all":
        query = query.filter(DuplicateCandidate.status == status)

    candidates = (
        query
        .order_by(
            DuplicateCandidate.similarity.desc(),
            DuplicateCandidate.id.desc(),
        )
        .offset(skip)
        .limit(limit)
        .all()
    )

    return build_candidate_views(candidates, db)


@router.get(
    "/candidates/{candidate_id}",
    response_model=DuplicateCandidateView,
)
def get_candidate(
    candidate_id: int,
    db: Session = Depends(get_db),
):
    candidate = (
        db.query(DuplicateCandidate)
        .filter(DuplicateCandidate.id == candidate_id)
        .first()
    )

    if candidate is None:
        raise HTTPException(
            status_code=404,
            detail="Duplicate candidate not found",
        )

    return build_candidate_views([candidate], db)[0]


@router.post("/candidates/{candidate_id}/confirm")
def confirm_candidate(
    candidate_id: int,
    request: ReviewRequest | None = None,
    db: Session = Depends(get_db),
):
    notes = request.notes if request else None

    try:
        return confirm_merge(candidate_id, notes, db)
    except ReviewError as exc:
        raise HTTPException(status_code=exc.status_code, detail=exc.message)


@router.post("/candidates/{candidate_id}/reject")
def reject_candidate_endpoint(
    candidate_id: int,
    request: ReviewRequest | None = None,
    db: Session = Depends(get_db),
):
    notes = request.notes if request else None

    try:
        return reject_candidate(candidate_id, notes, db)
    except ReviewError as exc:
        raise HTTPException(status_code=exc.status_code, detail=exc.message)