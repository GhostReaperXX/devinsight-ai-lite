"""Browser pages: routes that answer with HTML built from Jinja2 templates."""

from typing import Annotated
from urllib.parse import urlencode

from fastapi import APIRouter, Form, Query, Request
from fastapi.responses import HTMLResponse, RedirectResponse
from pydantic import ValidationError

from app.deps import DbSession
from app.errors import ConflictError
from app.schemas import IssueCreate, IssueFilters, IssueUpdate, ProjectCreate
from app.services import issues as issue_service
from app.services import projects as project_service
from app.services import users as user_service
from app.templating import templates

router = APIRouter(include_in_schema=False)

FLASH_MESSAGES = {
    "created": "The issue was created.",
    "updated": "The issue was updated.",
    "deleted": "The issue was deleted.",
    "project_created": "The project was created.",
}


def field_errors(error: ValidationError) -> dict[str, str]:
    """Turn a Pydantic error into {field name: readable message}."""
    return {str(item["loc"][0]): item["msg"] for item in error.errors()}


def redirect(url: str) -> RedirectResponse:
    """Answer a successful form with 303, so a refresh does not resubmit it."""
    return RedirectResponse(url, status_code=303)


@router.get("/", response_class=HTMLResponse)
def dashboard(request: Request, db: DbSession):
    return templates.TemplateResponse(
        request,
        "dashboard.html",
        {
            "projects": project_service.list_projects(db),
            "stats": issue_service.get_stats(db),
        },
    )


@router.get("/issues", response_class=HTMLResponse)
def issue_list(
    request: Request,
    db: DbSession,
    filters: Annotated[IssueFilters, Query()],
    msg: str = "",
):
    issues, total = issue_service.list_issues(db, filters)
    active_filters = {
        name: value
        for name, value in filters.model_dump(exclude={"limit", "offset"}).items()
        if value not in (None, "newest")
    }
    query_string = urlencode(active_filters)
    return templates.TemplateResponse(
        request,
        "issues/list.html",
        {
            "issues": issues,
            "total": total,
            "filters": filters,
            "query_string": query_string,
            "projects": project_service.list_projects(db),
            "flash": FLASH_MESSAGES.get(msg),
        },
    )


def form_context(db, form: dict, errors: dict | None = None, issue=None) -> dict:
    """Everything the new-issue and edit-issue form needs to display."""
    return {
        "form": form,
        "errors": errors or {},
        "issue": issue,
        "projects": project_service.list_projects(db),
        "users": user_service.list_users(db),
    }


@router.get("/issues/new", response_class=HTMLResponse)
def new_issue_form(request: Request, db: DbSession):
    form = {"priority": "medium"}
    return templates.TemplateResponse(request, "issues/form.html", form_context(db, form))


@router.post("/issues/new", response_class=HTMLResponse)
def new_issue_submit(
    request: Request,
    db: DbSession,
    project_id: Annotated[str, Form()] = "",
    reporter_id: Annotated[str, Form()] = "",
    assignee_id: Annotated[str, Form()] = "",
    title: Annotated[str, Form()] = "",
    description: Annotated[str, Form()] = "",
    category: Annotated[str, Form()] = "",
    priority: Annotated[str, Form()] = "medium",
):
    form = {
        "project_id": project_id,
        "reporter_id": reporter_id,
        "assignee_id": assignee_id or None,
        "title": title,
        "description": description,
        "category": category,
        "priority": priority,
    }
    try:
        issue = issue_service.create_issue(db, IssueCreate(**form))
    except ValidationError as error:
        return templates.TemplateResponse(
            request,
            "issues/form.html",
            form_context(db, form, field_errors(error)),
            status_code=422,
        )
    return redirect(f"/issues/{issue.id}?msg=created")


@router.get("/issues/{issue_id}", response_class=HTMLResponse)
def issue_detail(request: Request, issue_id: int, db: DbSession, msg: str = ""):
    issue = issue_service.get_issue(db, issue_id)
    return templates.TemplateResponse(
        request,
        "issues/detail.html",
        {
            "issue": issue,
            "transitions": sorted(issue_service.allowed_next_statuses(issue)),
            "users": user_service.list_users(db),
            "flash": FLASH_MESSAGES.get(msg),
        },
    )


@router.get("/issues/{issue_id}/edit", response_class=HTMLResponse)
def edit_issue_form(request: Request, issue_id: int, db: DbSession):
    issue = issue_service.get_issue(db, issue_id)
    form = {
        "project_id": issue.project_id,
        "reporter_id": issue.reporter_id,
        "assignee_id": issue.assignee_id,
        "title": issue.title,
        "description": issue.description,
        "category": issue.category,
        "priority": issue.priority,
    }
    return templates.TemplateResponse(
        request, "issues/form.html", form_context(db, form, issue=issue)
    )


@router.post("/issues/{issue_id}/edit", response_class=HTMLResponse)
def edit_issue_submit(
    request: Request,
    issue_id: int,
    db: DbSession,
    assignee_id: Annotated[str, Form()] = "",
    title: Annotated[str, Form()] = "",
    description: Annotated[str, Form()] = "",
    category: Annotated[str, Form()] = "",
    priority: Annotated[str, Form()] = "medium",
):
    issue = issue_service.get_issue(db, issue_id)
    form = {
        "assignee_id": assignee_id or None,
        "title": title,
        "description": description,
        "category": category,
        "priority": priority,
    }
    try:
        issue_service.update_issue(db, issue_id, IssueUpdate(**form))
    except ValidationError as error:
        form |= {"project_id": issue.project_id, "reporter_id": issue.reporter_id}
        return templates.TemplateResponse(
            request,
            "issues/form.html",
            form_context(db, form, field_errors(error), issue),
            status_code=422,
        )
    return redirect(f"/issues/{issue_id}?msg=updated")


@router.post("/issues/{issue_id}/delete")
def delete_issue_submit(issue_id: int, db: DbSession):
    issue_service.delete_issue(db, issue_id)
    return redirect("/issues?msg=deleted")


def project_page_context(db, form: dict, errors: dict, flash: str | None = None) -> dict:
    per_project = issue_service.get_stats(db)["per_project"]
    return {
        "projects": project_service.list_projects(db),
        "issue_counts": {row["key"]: row["issues"] for row in per_project},
        "form": form,
        "errors": errors,
        "flash": flash,
    }


@router.get("/projects", response_class=HTMLResponse)
def project_list(request: Request, db: DbSession, msg: str = ""):
    return templates.TemplateResponse(
        request, "projects.html", project_page_context(db, {}, {}, FLASH_MESSAGES.get(msg))
    )


@router.post("/projects", response_class=HTMLResponse)
def project_create_submit(
    request: Request,
    db: DbSession,
    key: Annotated[str, Form()] = "",
    name: Annotated[str, Form()] = "",
    description: Annotated[str, Form()] = "",
):
    form = {"key": key, "name": name, "description": description}
    try:
        project_service.create_project(db, ProjectCreate(**form))
    except ValidationError as error:
        errors = field_errors(error)
    except ConflictError as error:
        errors = {"key": str(error)}
    else:
        return redirect("/projects?msg=project_created")
    return templates.TemplateResponse(
        request, "projects.html", project_page_context(db, form, errors), status_code=422
    )
