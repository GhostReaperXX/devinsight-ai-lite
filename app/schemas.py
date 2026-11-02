"""Pydantic schemas: the exact shape of the data that enters and leaves the API."""

from datetime import UTC, datetime
from typing import Annotated, Literal

from pydantic import (
    BaseModel,
    ConfigDict,
    EmailStr,
    Field,
    PlainSerializer,
    StringConstraints,
    field_validator,
)

Category = Literal["bug", "feature", "documentation", "performance", "security"]
Priority = Literal["low", "medium", "high", "critical"]
Status = Literal["open", "in_progress", "resolved", "closed"]
SortOrder = Literal["newest", "oldest", "priority"]

Title = Annotated[
    str, StringConstraints(strip_whitespace=True, min_length=5, max_length=150)
]
Description = Annotated[
    str, StringConstraints(strip_whitespace=True, min_length=10, max_length=5000)
]
CommentBody = Annotated[
    str, StringConstraints(strip_whitespace=True, min_length=1, max_length=2000)
]
PersonName = Annotated[
    str, StringConstraints(strip_whitespace=True, min_length=2, max_length=100)
]
ProjectKey = Annotated[
    str,
    StringConstraints(
        strip_whitespace=True, to_upper=True, pattern=r"^[A-Za-z][A-Za-z0-9]{1,9}$"
    ),
]


def as_utc_text(value: datetime) -> str:
    """SQLite returns no time zone and PostgreSQL does, so always answer in UTC."""
    if value.tzinfo is None:
        value = value.replace(tzinfo=UTC)
    return value.astimezone(UTC).isoformat().replace("+00:00", "Z")


UtcDateTime = Annotated[datetime, PlainSerializer(as_utc_text, return_type=str)]


class ReadModel(BaseModel):
    """Parent of every response schema: allows reading from table objects."""

    model_config = ConfigDict(from_attributes=True)


class UserRegister(BaseModel):
    full_name: PersonName
    email: EmailStr
    password: Annotated[str, Field(min_length=10, max_length=128)]

    @field_validator("email")
    @classmethod
    def email_in_lower_case(cls, value: str) -> str:
        return value.lower()


class UserRead(ReadModel):
    id: int
    full_name: str
    email: str
    role: str


class UserBrief(ReadModel):
    id: int
    full_name: str


class Token(BaseModel):
    access_token: str
    token_type: str = "bearer"  # noqa: S105 (the name of a scheme, not a secret)


class ProjectCreate(BaseModel):
    key: ProjectKey
    name: PersonName
    description: str = ""


class ProjectRead(ReadModel):
    id: int
    key: str
    name: str
    description: str


class ProjectBrief(ReadModel):
    id: int
    key: str
    name: str


class IssueCreate(BaseModel):
    """No reporter here: the server takes it from the login, never from the client."""

    project_id: int
    assignee_id: int | None = None
    title: Title
    description: Description
    category: Category
    priority: Priority = "medium"


class IssueUpdate(BaseModel):
    """Every field is optional: PATCH changes only the fields that are sent."""

    assignee_id: int | None = None
    title: Title | None = None
    description: Description | None = None
    category: Category | None = None
    priority: Priority | None = None

    @field_validator("title", "description", "category", "priority", mode="before")
    @classmethod
    def only_assignee_may_be_null(cls, value):
        if value is None:
            raise ValueError("this field cannot be empty")
        return value


class StatusChange(BaseModel):
    status: Status
    comment: CommentBody | None = None


class DuplicateMark(BaseModel):
    duplicate_of_id: int


class IssueRead(ReadModel):
    id: int
    title: str
    description: str
    category: str
    priority: str
    status: str
    predicted_category: str | None
    prediction_confidence: float | None
    duplicate_of_id: int | None
    created_at: UtcDateTime
    updated_at: UtcDateTime
    project: ProjectBrief
    reporter: UserBrief
    assignee: UserBrief | None


class IssueFilters(BaseModel):
    """Query parameters of the issue list. An empty value means 'no filter'."""

    project_id: int | None = None
    status: Status | None = None
    category: Category | None = None
    priority: Priority | None = None
    assignee_id: int | None = None
    q: Annotated[str, StringConstraints(strip_whitespace=True, max_length=100)] | None = (
        None
    )
    sort: SortOrder = "newest"
    limit: Annotated[int, Field(ge=1, le=100)] = 20
    offset: Annotated[int, Field(ge=0)] = 0

    @field_validator(
        "project_id", "status", "category", "priority", "assignee_id", "q", mode="before"
    )
    @classmethod
    def blank_means_none(cls, value):
        return None if value == "" else value


class IssuePage(BaseModel):
    items: list[IssueRead]
    total: int
    limit: int
    offset: int


class CommentCreate(BaseModel):
    body: CommentBody


class CommentRead(ReadModel):
    id: int
    body: str
    created_at: UtcDateTime
    author: UserBrief


class ProjectCount(BaseModel):
    key: str
    name: str
    issues: int


class Stats(BaseModel):
    total: int
    active: int
    by_status: dict[str, int]
    by_category: dict[str, int]
    by_priority: dict[str, int]
    per_project: list[ProjectCount]


class AnalyzeRequest(BaseModel):
    title: Annotated[str, StringConstraints(strip_whitespace=True, max_length=150)] = ""
    description: Annotated[
        str, StringConstraints(strip_whitespace=True, max_length=5000)
    ] = ""
    exclude_issue_id: int | None = None


class CategoryScore(BaseModel):
    category: str
    probability: float


class CategorySuggestion(BaseModel):
    category: str
    confidence: float
    is_confident: bool
    alternatives: list[CategoryScore]


class RelatedIssue(BaseModel):
    id: int
    title: str
    status: str
    project_key: str
    score: float


class AnalyzeResponse(BaseModel):
    suggestion: CategorySuggestion | None
    related: list[RelatedIssue]


class DuplicateCandidate(BaseModel):
    first: RelatedIssue
    second: RelatedIssue
    score: float


class InsightSummary(BaseModel):
    model_available: bool
    model_macro_f1: float | None
    predictions_made: int
    agreement_rate: float | None
    duplicate_candidates: int
