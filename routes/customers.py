from fastapi import APIRouter, Depends, Form, HTTPException, Request
from fastapi.responses import RedirectResponse
from sqlalchemy.orm import Session

from database import get_db
from models import Customer, Invoice, Quote, User
from utils import flash, render, require_login

router = APIRouter(prefix="/customers")


def _get_customer_or_404(customer_id: int, user_id: int, db: Session) -> Customer:
    customer = db.query(Customer).filter(
        Customer.id == customer_id, Customer.user_id == user_id
    ).first()
    if not customer:
        raise HTTPException(status_code=404)
    return customer


@router.get("")
def list_customers(
    request: Request,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_login),
):
    customers = (
        db.query(Customer)
        .filter(Customer.user_id == current_user.id)
        .order_by(Customer.company_name).all()
    )
    return render(request, "customers/list.html", customers=customers)


@router.get("/new")
def new_customer_form(
    request: Request,
    current_user: User = Depends(require_login),
):
    return render(request, "customers/form.html", customer=None)


@router.post("")
def create_customer(
    request: Request,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_login),
    company_name: str = Form(...),
    contact_name: str = Form(...),
    email: str = Form(...),
    phone: str = Form(""),
    address: str = Form(""),
    notes: str = Form(""),
):
    customer = Customer(
        user_id=current_user.id,
        company_name=company_name,
        contact_name=contact_name,
        email=email,
        phone=phone or None,
        address=address or None,
        notes=notes or None,
    )
    db.add(customer)
    db.commit()
    flash(request, "顧客を登録しました", "success")
    return RedirectResponse(f"/customers/{customer.id}", status_code=303)


@router.get("/{customer_id}")
def detail_customer(
    customer_id: int,
    request: Request,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_login),
):
    customer = _get_customer_or_404(customer_id, current_user.id, db)
    return render(request, "customers/detail.html", customer=customer)


@router.get("/{customer_id}/edit")
def edit_customer_form(
    customer_id: int,
    request: Request,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_login),
):
    customer = _get_customer_or_404(customer_id, current_user.id, db)
    return render(request, "customers/form.html", customer=customer)


@router.post("/{customer_id}/edit")
def update_customer(
    customer_id: int,
    request: Request,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_login),
    company_name: str = Form(...),
    contact_name: str = Form(...),
    email: str = Form(...),
    phone: str = Form(""),
    address: str = Form(""),
    notes: str = Form(""),
):
    customer = _get_customer_or_404(customer_id, current_user.id, db)
    customer.company_name = company_name
    customer.contact_name = contact_name
    customer.email = email
    customer.phone = phone or None
    customer.address = address or None
    customer.notes = notes or None
    db.commit()
    flash(request, "顧客情報を更新しました", "success")
    return RedirectResponse(f"/customers/{customer_id}", status_code=303)


@router.post("/{customer_id}/delete")
def delete_customer(
    customer_id: int,
    request: Request,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_login),
):
    customer = _get_customer_or_404(customer_id, current_user.id, db)
    has_related = (
        db.query(Quote).filter(Quote.customer_id == customer_id, Quote.user_id == current_user.id).count()
        + db.query(Invoice).filter(Invoice.customer_id == customer_id, Invoice.user_id == current_user.id).count()
    ) > 0
    if has_related:
        flash(request, "見積書または請求書が紐づいているため削除できません", "error")
        return RedirectResponse(f"/customers/{customer_id}", status_code=303)
    db.delete(customer)
    db.commit()
    flash(request, "顧客を削除しました", "success")
    return RedirectResponse("/customers", status_code=303)
