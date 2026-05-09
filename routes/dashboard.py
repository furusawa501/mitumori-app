from fastapi import APIRouter, Depends, Request
from sqlalchemy import func
from sqlalchemy.orm import Session

from database import get_db
from models import Invoice, Quote, User
from utils import render, require_login

router = APIRouter()


@router.get("/")
def dashboard(
    request: Request,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_login),
):
    row = db.query(func.count(Quote.id), func.sum(Quote.total)) \
             .filter(Quote.user_id == current_user.id, Quote.status == "sent").one()
    sent_quotes_count = row[0]
    sent_quotes_total = row[1] or 0

    row = db.query(func.count(Invoice.id), func.sum(Invoice.total)) \
             .filter(Invoice.user_id == current_user.id,
                     Invoice.status.in_(["sent", "overdue"])).one()
    pending_invoices_count = row[0]
    pending_invoices_total = row[1] or 0

    recent_quotes = (
        db.query(Quote)
        .filter(Quote.user_id == current_user.id)
        .order_by(Quote.created_at.desc()).limit(5).all()
    )
    recent_invoices = (
        db.query(Invoice)
        .filter(Invoice.user_id == current_user.id)
        .order_by(Invoice.created_at.desc()).limit(5).all()
    )

    return render(request, "dashboard.html",
        sent_quotes_count=sent_quotes_count,
        sent_quotes_total=sent_quotes_total,
        pending_invoices_count=pending_invoices_count,
        pending_invoices_total=pending_invoices_total,
        recent_quotes=recent_quotes,
        recent_invoices=recent_invoices,
    )
