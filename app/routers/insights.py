"""REST endpoints for the machine learning features."""

from fastapi import APIRouter, HTTPException, status

from app.deps import CurrentUser, DbSession, Predictor
from app.schemas import AnalyzeRequest, AnalyzeResponse, DuplicateCandidate, InsightSummary
from app.services import insights as service

router = APIRouter(prefix="/api/insights", tags=["AI insights"])


@router.post(
    "/analyze",
    response_model=AnalyzeResponse,
    summary="Suggest a category and find related issues",
)
def analyze(data: AnalyzeRequest, db: DbSession, _user: CurrentUser, predictor: Predictor):
    return {
        "suggestion": service.suggest_category(predictor, data.title, data.description),
        "related": service.find_related(
            db, data.title, data.description, data.exclude_issue_id
        ),
    }


@router.get(
    "/duplicates",
    response_model=list[DuplicateCandidate],
    summary="List likely duplicate pairs",
)
def duplicates(db: DbSession, _user: CurrentUser, project_id: int | None = None):
    return service.duplicate_candidates(db, project_id)


@router.get(
    "/summary", response_model=InsightSummary, summary="AI numbers for the dashboard"
)
def summary(db: DbSession, _user: CurrentUser, predictor: Predictor):
    return service.summary(db, predictor)


@router.get("/model", summary="The evaluation results of the deployed model")
def model_metrics(_user: CurrentUser):
    metrics = service.read_model_metrics()
    if metrics is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "No model has been evaluated yet.")
    return metrics
