"""Browser pages: routes that answer with HTML built from Jinja2 templates."""

from typing import Annotated
from urllib.parse import urlencode

from fastapi import APIRouter, Form, Query, Request
from fastapi.responses import HTMLResponse, RedirectResponse
from pydantic import ValidationError

from app.config import get_settings
from app.deps import SESSION_COOKIE, DbSession, OptionalUser, PageUser, Predictor
from app.errors import AuthenticationError, ConflictError, PermissionDeniedError
from app.schemas import IssueCreate, IssueFilters, IssueUpdate, ProjectCreate, UserRegister
from app.security import create_access_token
from app.services import insights as insight_service
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
    "registered": "Your account is ready. Please log in.",
}


def field_errors(error: ValidationError) -> dict[str, str]:
    """Turn a Pydantic error into {field name: readable message}."""
    return {str(item["loc"][0]): item["msg"] for item in error.errors()}


def redirect(url: str) -> RedirectResponse:
    """Answer a successful form with 303, so a refresh does not resubmit it."""
    return RedirectResponse(url, status_code=303)


def safe_next_path(target: str) -> str:
    """Only redirect inside this site, so a crafted link cannot send users elsewhere."""
    if target.startswith("/") and not target.startswith(("//", "/\\")):
        return target
    return "/"


@router.get("/login", response_class=HTMLResponse)
def login_form(request: Request, user: OptionalUser, next: str = "/", msg: str = ""):
    if user is not None:
        return redirect(safe_next_path(next))
    return templates.TemplateResponse(
        request,
        "auth/login.html",
        {"next": next, "email": "", "error": None, "flash": FLASH_MESSAGES.get(msg)},
    )


@router.post("/login", response_class=HTMLResponse)
def login_submit(
    request: Request,
    db: DbSession,
    email: Annotated[str, Form()] = "",
    password: Annotated[str, Form()] = "",
    next: Annotated[str, Form()] = "/",
):
    try:
        user = user_service.authenticate(db, email, password)
    except AuthenticationError as error:
        return templates.TemplateResponse(
            request,
            "auth/login.html",
            {"next": next, "email": email, "error": str(error), "flash": None},
            status_code=401,
        )
    settings = get_settings()
    response = redirect(safe_next_path(next))
    # HttpOnly: page scripts cannot read it. SameSite=Lax: other sites cannot post with it.
    # Secure: in production the browser sends it over HTTPS only.
    response.set_cookie(
        SESSION_COOKIE,
        create_access_token(user.id),
        max_age=settings.access_token_minutes * 60,
        httponly=True,
        samesite="lax",
        secure=settings.is_production,
    )
    return response


@router.post("/logout")
def logout():
    response = redirect("/login")
    response.delete_cookie(SESSION_COOKIE)
    return response


@router.get("/register", response_class=HTMLResponse)
def register_form(request: Request, _user: OptionalUser):
    return templates.TemplateResponse(
        request, "auth/register.html", {"form": {}, "errors": {}}
    )


@router.post("/register", response_class=HTMLResponse)
def register_submit(
    request: Request,
    db: DbSession,
    full_name: Annotated[str, Form()] = "",
    email: Annotated[str, Form()] = "",
    password: Annotated[str, Form()] = "",
):
    form = {"full_name": full_name, "email": email}
    try:
        user_service.register_user(
            db, UserRegister(full_name=full_name, email=email, password=password)
        )
    except ValidationError as error:
        errors = field_errors(error)
    except ConflictError as error:
        errors = {"email": str(error)}
    else:
        return redirect("/login?msg=registered")
    return templates.TemplateResponse(
        request, "auth/register.html", {"form": form, "errors": errors}, status_code=422
    )


@router.get("/", response_class=HTMLResponse)
def dashboard(request: Request, db: DbSession, _user: PageUser):
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
    _user: PageUser,
    filters: Annotated[IssueFilters, Query()],
    msg: str = "",
):
    issues, total = issue_service.list_issues(db, filters)
    active_filters = {
        name: value
        for name, value in filters.model_dump(exclude={"limit", "offset"}).items()
        if value not in (None, "newest")
    }
    return templates.TemplateResponse(
        request,
        "issues/list.html",
        {
            "issues": issues,
            "total": total,
            "filters": filters,
            "query_string": urlencode(active_filters),
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
def new_issue_form(request: Request, db: DbSession, _user: PageUser):
    return templates.TemplateResponse(
        request, "issues/form.html", form_context(db, {"priority": "medium"})
    )


@router.post("/issues/new", response_class=HTMLResponse)
def new_issue_submit(
    request: Request,
    db: DbSession,
    user: PageUser,
    predictor: Predictor,
    project_id: Annotated[str, Form()] = "",
    assignee_id: Annotated[str, Form()] = "",
    title: Annotated[str, Form()] = "",
    description: Annotated[str, Form()] = "",
    category: Annotated[str, Form()] = "",
    priority: Annotated[str, Form()] = "medium",
):
    form = {
        "project_id": project_id,
        "assignee_id": assignee_id or None,
        "title": title,
        "description": description,
        "category": category,
        "priority": priority,
    }
    try:
        issue = issue_service.create_issue(
            db, IssueCreate(**form), reporter=user, predictor=predictor
        )
    except ValidationError as error:
        return templates.TemplateResponse(
            request,
            "issues/form.html",
            form_context(db, form, field_errors(error)),
            status_code=422,
        )
    return redirect(f"/issues/{issue.id}?msg=created")


@router.get("/issues/{issue_id}", response_class=HTMLResponse)
def issue_detail(
    request: Request, issue_id: int, db: DbSession, user: PageUser, msg: str = ""
):
    issue = issue_service.get_issue(db, issue_id)
    return templates.TemplateResponse(
        request,
        "issues/detail.html",
        {
            "issue": issue,
            "can_change": issue_service.can_change(user, issue),
            "transitions": sorted(issue_service.allowed_next_statuses(issue)),
            "related": insight_service.find_related(
                db, issue.title, issue.description, issue.id
            ),
            "flash": FLASH_MESSAGES.get(msg),
        },
    )


@router.get("/issues/{issue_id}/edit", response_class=HTMLResponse)
def edit_issue_form(request: Request, issue_id: int, db: DbSession, user: PageUser):
    issue = issue_service.get_issue(db, issue_id)
    if not issue_service.can_change(user, issue):
        raise PermissionDeniedError(
            "Only the reporter, the assignee or an administrator can edit this issue."
        )
    form = {
        "project_id": issue.project_id,
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
    user: PageUser,
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
        issue_service.update_issue(db, issue_id, IssueUpdate(**form), actor=user)
    except ValidationError as error:
        form["project_id"] = issue.project_id
        return templates.TemplateResponse(
            request,
            "issues/form.html",
            form_context(db, form, field_errors(error), issue),
            status_code=422,
        )
    return redirect(f"/issues/{issue_id}?msg=updated")


@router.post("/issues/{issue_id}/delete")
def delete_issue_submit(issue_id: int, db: DbSession, user: PageUser):
    if user.role != "admin":
        raise PermissionDeniedError("Only an administrator can delete an issue.")
    issue_service.delete_issue(db, issue_id)
    return redirect("/issues?msg=deleted")


@router.get("/duplicates", response_class=HTMLResponse)
def duplicates_page(request: Request, db: DbSession, _user: PageUser):
    return templates.TemplateResponse(
        request,
        "duplicates.html",
        {"candidates": insight_service.duplicate_candidates(db)},
    )


@router.get("/model", response_class=HTMLResponse)
def model_page(request: Request, _user: PageUser, predictor: Predictor):
    return templates.TemplateResponse(
        request,
        "model.html",
        {
            "metrics": insight_service.read_model_metrics(),
            "model_loaded": predictor is not None,
        },
    )


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
def project_list(request: Request, db: DbSession, _user: PageUser, msg: str = ""):
    return templates.TemplateResponse(
        request, "projects.html", project_page_context(db, {}, {}, FLASH_MESSAGES.get(msg))
    )


@router.post("/projects", response_class=HTMLResponse)
def project_create_submit(
    request: Request,
    db: DbSession,
    user: PageUser,
    key: Annotated[str, Form()] = "",
    name: Annotated[str, Form()] = "",
    description: Annotated[str, Form()] = "",
):
    if user.role != "admin":
        raise PermissionDeniedError("Only an administrator can create a project.")
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
