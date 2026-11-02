"""Pydantic schemas: the exact shape of the data that enters and leaves the API."""

from datetime import datetime
from typing import Annotated, Literal

from pydantic import (
    BaseModel,
    ConfigDict,
    EmailStr,
    Field,
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
ProjectKey = Annotated[
    str,
    StringConstraints(
        strip_whitespace=True, to_upper=True, pattern=r"^[A-Za-z][A-Za-z0-9]{1,9}$"
    ),
]


class ReadModel(BaseModel):
    """Parent of every response schema: allows reading from table objects."""

    model_config = ConfigDict(from_attributes=True)


class UserCreate(BaseModel):
    full_name: Annotated[
        str, StringConstraints(strip_whitespace=True, min_length=2, max_length=100)
    ]
    email: EmailStr
    role: Literal["admin", "member"] = "member"


class UserRead(ReadModel):
    id: int
    full_name: str
    email: str
    role: str


class UserBrief(ReadModel):
    id: int
    full_name: str


class ProjectCreate(BaseModel):
    key: ProjectKey
    name: Annotated[
        str, StringConstraints(strip_whitespace=True, min_length=2, max_length=100)
    ]
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
    project_id: int
    reporter_id: int
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


class StatusChange(BaseModel):
    status: Status
    comment: CommentBody | None = None
    author_id: int | None = None


class IssueRead(ReadModel):
    id: int
    title: str
    description: str
    category: str
    priority: str
    status: str
    created_at: datetime
    updated_at: datetime
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
    author_id: int
    body: CommentBody


class CommentRead(ReadModel):
    id: int
    body: str
    created_at: datetime
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
