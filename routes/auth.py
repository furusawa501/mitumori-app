from fastapi import APIRouter, Depends, Form, Request
from fastapi.responses import RedirectResponse
from passlib.context import CryptContext
from sqlalchemy.orm import Session

from database import get_db
from models import User
from utils import flash, render

router = APIRouter()
_pwd = CryptContext(schemes=["bcrypt"], deprecated="auto")


@router.get("/register")
def register_form(request: Request):
    if request.session.get("user_id"):
        return RedirectResponse("/", status_code=302)
    return render(request, "auth/register.html")


@router.post("/register")
def register(
    request: Request,
    db: Session = Depends(get_db),
    email: str = Form(...),
    password: str = Form(...),
    password_confirm: str = Form(...),
):
    if password != password_confirm:
        flash(request, "パスワードが一致しません", "error")
        return render(request, "auth/register.html")
    if len(password) < 8:
        flash(request, "パスワードは8文字以上で設定してください", "error")
        return render(request, "auth/register.html")
    if db.query(User).filter(User.email == email).first():
        flash(request, "このメールアドレスはすでに登録されています", "error")
        return render(request, "auth/register.html")
    user = User(email=email, password_hash=_pwd.hash(password))
    db.add(user)
    db.commit()
    request.session["user_id"] = user.id
    request.session["user_email"] = user.email
    flash(request, "アカウントを作成しました。ようこそ！", "success")
    return RedirectResponse("/", status_code=303)


@router.get("/login")
def login_form(request: Request):
    if request.session.get("user_id"):
        return RedirectResponse("/", status_code=302)
    return render(request, "auth/login.html")


@router.post("/login")
def login(
    request: Request,
    db: Session = Depends(get_db),
    email: str = Form(...),
    password: str = Form(...),
):
    user = db.query(User).filter(User.email == email).first()
    if not user or not _pwd.verify(password, user.password_hash):
        flash(request, "メールアドレスまたはパスワードが正しくありません", "error")
        return render(request, "auth/login.html")
    request.session["user_id"] = user.id
    request.session["user_email"] = user.email
    return RedirectResponse("/", status_code=303)


@router.post("/logout")
def logout(request: Request):
    request.session.clear()
    return RedirectResponse("/login", status_code=303)
