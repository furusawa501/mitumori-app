from fastapi import Request
from fastapi.templating import Jinja2Templates
from fastapi.responses import HTMLResponse

templates = Jinja2Templates(directory="templates")


def flash(request: Request, message: str, category: str = "info") -> None:
    request.session.setdefault("_flash", []).append({"text": message, "category": category})


def render(request: Request, template: str, **ctx) -> HTMLResponse:
    ctx["request"] = request
    ctx["messages"] = request.session.pop("_flash", [])
    return templates.TemplateResponse(template, ctx)
