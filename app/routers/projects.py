"""REST endpoints for projects."""

from fastapi import APIRouter, status

from app.deps import AdminUser, CurrentUser, DbSession
from app.schemas import ProjectCreate, ProjectRead
from app.services import projects as service

router = APIRouter(prefix="/api/projects", tags=["Projects"])


@router.get("", response_model=list[ProjectRead], summary="List projects")
def list_projects(db: DbSession, _user: CurrentUser):
    return service.list_projects(db)


@router.get("/{project_id}", response_model=ProjectRead, summary="Read one project")
def get_project(project_id: int, db: DbSession, _user: CurrentUser):
    return service.get_project(db, project_id)


@router.post(
    "",
    response_model=ProjectRead,
    status_code=status.HTTP_201_CREATED,
    summary="Create a project (administrators)",
)
def create_project(data: ProjectCreate, db: DbSession, _admin: AdminUser):
    return service.create_project(db, data)
