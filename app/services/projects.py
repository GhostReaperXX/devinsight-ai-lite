"""Project operations."""

from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.errors import ConflictError, NotFoundError
from app.models import Project
from app.schemas import ProjectCreate


def list_projects(db: Session) -> list[Project]:
    return list(db.scalars(select(Project).order_by(Project.key)))


def get_project(db: Session, project_id: int) -> Project:
    project = db.get(Project, project_id)
    if project is None:
        raise NotFoundError(f"project {project_id} does not exist")
    return project


def create_project(db: Session, data: ProjectCreate) -> Project:
    project = Project(**data.model_dump())
    db.add(project)
    try:
        db.commit()
    except IntegrityError:
        db.rollback()
        raise ConflictError(f"project key {data.key} is already taken") from None
    return project
