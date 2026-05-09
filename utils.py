from fastapi import Depends, Request
from fastapi.templating import Jinja2Templates
from fastapi.responses import HTMLResponse
from sqlalchemy.orm import Session

from database import get_db

templates = Jinja2Templates(directory="templates")


class NotAuthenticated(Exception):
    pass


def require_login(request: Request, db: Session = Depends(get_db)):
    from models import User
    user_id = request.session.get("user_id")
    if not user_id:
        raise NotAuthenticated()
    user = db.get(User, user_id)
    if not user:
        request.session.clear()
        raise NotAuthenticated()
    return user


def flash(request: Request, message: str, category: str = "info") -> None:
    request.session.setdefault("_flash", []).append({"text": message, "category": category})


def render(request: Request, template: str, **ctx) -> HTMLResponse:
    ctx["request"] = request
    ctx["messages"] = request.session.pop("_flash", [])
    return templates.TemplateResponse(template, ctx)
