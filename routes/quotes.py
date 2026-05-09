import math
from datetime import date

from fastapi import APIRouter, Depends, Form, HTTPException, Request, Response
from fastapi.responses import RedirectResponse
from sqlalchemy.orm import Session

from sqlalchemy import case
from database import get_db
from models import Customer, LineItem, Quote
from services.conversion import convert_quote_to_invoice
from services.numbering import next_quote_number
from services.pdf import generate_quote_pdf
from utils import flash, render

router = APIRouter(prefix="/quotes")

# 許可されたステータス遷移: (現在, action) → 次のステータス
_TRANSITIONS = {
    ("draft", "send"): "sent",
    ("sent", "accept"): "accepted",
    ("sent", "reject"): "rejected",
}


def _recalc_totals(quote: Quote) -> None:
    subtotal = sum(item.amount for item in quote.line_items)
    quote.subtotal = subtotal
    quote.tax_amount = math.floor(subtotal * 0.10)
    quote.total = quote.subtotal + quote.tax_amount


_QUOTE_STATUS_ORDER = case(
    {"draft": 1, "sent": 2, "accepted": 3, "rejected": 4, "converted": 5},
    value=Quote.status,
)

_QUOTE_SORT_COLS = {
    "customer":   Customer.company_name,
    "title":      Quote.title,
    "status":     _QUOTE_STATUS_ORDER,
    "total":      Quote.total,
    "issue_date": Quote.issue_date,
}

@router.get("")
def list_quotes(
    request: Request,
    status: str | None = None,
    sort: str = "issue_date",
    order: str = "desc",
    db: Session = Depends(get_db),
):
    q = db.query(Quote).join(Customer)
    if status:
        q = q.filter(Quote.status == status)
    col = _QUOTE_SORT_COLS.get(sort, Quote.issue_date)
    q = q.order_by(col.asc() if order == "asc" else col.desc())
    quotes = q.all()
    return render(request, "quotes/list.html",
                  quotes=quotes, current_status=status,
                  current_sort=sort, current_order=order)


@router.get("/new")
def new_quote_form(request: Request, db: Session = Depends(get_db)):
    customers = db.query(Customer).order_by(Customer.company_name).all()
    return render(request, "quotes/form.html", quote=None, customers=customers)


@router.post("")
def create_quote(
    request: Request,
    db: Session = Depends(get_db),
    customer_id: int = Form(...),
    title: str = Form(...),
    issue_date: date = Form(...),
    valid_until: str = Form(""),
    notes: str = Form(""),
):
    valid_until_date = date.fromisoformat(valid_until) if valid_until else None
    quote = Quote(
        quote_number=next_quote_number(db, issue_date.year),
        customer_id=customer_id,
        title=title,
        issue_date=issue_date,
        valid_until=valid_until_date,
        notes=notes or None,
    )
    db.add(quote)
    db.commit()
    flash(request, f"見積書 {quote.quote_number} を作成しました", "success")
    return RedirectResponse(f"/quotes/{quote.id}/edit", status_code=303)


@router.get("/{quote_id}")
def detail_quote(quote_id: int, request: Request, db: Session = Depends(get_db)):
    quote = db.get(Quote, quote_id)
    if not quote:
        raise HTTPException(status_code=404)
    return render(request, "quotes/detail.html", quote=quote)


@router.get("/{quote_id}/edit")
def edit_quote_form(quote_id: int, request: Request, db: Session = Depends(get_db)):
    quote = db.get(Quote, quote_id)
    if not quote:
        raise HTTPException(status_code=404)
    customers = db.query(Customer).order_by(Customer.company_name).all()
    return render(request, "quotes/form.html", quote=quote, customers=customers)


@router.post("/{quote_id}")
def update_quote(
    quote_id: int,
    request: Request,
    db: Session = Depends(get_db),
    customer_id: int = Form(...),
    title: str = Form(...),
    issue_date: date = Form(...),
    valid_until: str = Form(""),
    notes: str = Form(""),
):
    quote = db.get(Quote, quote_id)
    if not quote:
        raise HTTPException(status_code=404)
    if quote.status != "draft":
        raise HTTPException(status_code=403, detail="draft 状態の見積書のみ編集できます")
    quote.customer_id = customer_id
    quote.title = title
    quote.issue_date = issue_date
    quote.valid_until = date.fromisoformat(valid_until) if valid_until else None
    quote.notes = notes or None
    db.commit()
    flash(request, "見積書を更新しました", "success")
    return RedirectResponse(f"/quotes/{quote_id}/edit", status_code=303)


@router.post("/{quote_id}/delete")
def delete_quote(quote_id: int, request: Request, db: Session = Depends(get_db)):
    quote = db.get(Quote, quote_id)
    if not quote:
        raise HTTPException(status_code=404)
    if quote.status != "draft":
        raise HTTPException(status_code=403, detail="draft 状態の見積書のみ削除できます")
    db.delete(quote)
    db.commit()
    flash(request, "見積書を削除しました", "success")
    return RedirectResponse("/quotes", status_code=303)


@router.post("/{quote_id}/status")
def change_status(
    quote_id: int,
    request: Request,
    db: Session = Depends(get_db),
    action: str = Form(...),
):
    quote = db.get(Quote, quote_id)
    if not quote:
        raise HTTPException(status_code=404)
    new_status = _TRANSITIONS.get((quote.status, action))
    if not new_status:
        flash(request, "この操作は現在の状態では実行できません", "error")
        return RedirectResponse(f"/quotes/{quote_id}", status_code=303)
    if action == "send" and not quote.line_items:
        flash(request, "明細行を1件以上追加してから送付済みにしてください", "error")
        return RedirectResponse(f"/quotes/{quote_id}", status_code=303)
    quote.status = new_status
    db.commit()
    flash(request, f"ステータスを更新しました", "success")
    return RedirectResponse(f"/quotes/{quote_id}", status_code=303)


@router.get("/{quote_id}/pdf")
def quote_pdf(quote_id: int, db: Session = Depends(get_db)):
    quote = db.get(Quote, quote_id)
    if not quote:
        raise HTTPException(status_code=404)
    pdf_bytes = generate_quote_pdf(quote)
    return Response(
        content=pdf_bytes,
        media_type="application/pdf",
        headers={"Content-Disposition": f'inline; filename="{quote.quote_number}.pdf"'},
    )


@router.post("/{quote_id}/convert")
def convert_quote(quote_id: int, request: Request, db: Session = Depends(get_db)):
    quote = db.get(Quote, quote_id)
    if not quote:
        raise HTTPException(status_code=404)
    if quote.status != "accepted":
        flash(request, "承認済みの見積書のみ変換できます", "error")
        return RedirectResponse(f"/quotes/{quote_id}", status_code=303)
    invoice = convert_quote_to_invoice(db, quote)
    flash(request, f"請求書 {invoice.invoice_number} を作成しました", "success")
    return RedirectResponse(f"/invoices/{invoice.id}", status_code=303)


@router.post("/{quote_id}/items")
def add_line_item(
    quote_id: int,
    request: Request,
    db: Session = Depends(get_db),
    description: str = Form(...),
    quantity: float = Form(...),
    unit: str = Form(""),
    unit_price: int = Form(...),
    sort_order: int = Form(...),
):
    quote = db.get(Quote, quote_id)
    if not quote:
        raise HTTPException(status_code=404)
    if quote.status != "draft":
        raise HTTPException(status_code=403)
    item = LineItem(
        quote_id=quote_id,
        sort_order=sort_order,
        description=description,
        quantity=quantity,
        unit=unit or None,
        unit_price=unit_price,
        amount=math.floor(quantity * unit_price),
    )
    db.add(item)
    db.flush()
    _recalc_totals(quote)
    db.commit()
    return RedirectResponse(f"/quotes/{quote_id}/edit", status_code=303)


@router.post("/{quote_id}/items/{item_id}")
def update_line_item(
    quote_id: int,
    item_id: int,
    request: Request,
    db: Session = Depends(get_db),
    description: str = Form(...),
    quantity: float = Form(...),
    unit: str = Form(""),
    unit_price: int = Form(...),
    sort_order: int = Form(...),
):
    quote = db.get(Quote, quote_id)
    if not quote:
        raise HTTPException(status_code=404)
    if quote.status != "draft":
        raise HTTPException(status_code=403)
    item = db.get(LineItem, item_id)
    if not item or item.quote_id != quote_id:
        raise HTTPException(status_code=404)
    item.description = description
    item.quantity = quantity
    item.unit = unit or None
    item.unit_price = unit_price
    item.sort_order = sort_order
    item.amount = math.floor(quantity * unit_price)
    _recalc_totals(quote)
    db.commit()
    return RedirectResponse(f"/quotes/{quote_id}/edit", status_code=303)


@router.post("/{quote_id}/items/{item_id}/delete")
def delete_line_item(
    quote_id: int,
    item_id: int,
    request: Request,
    db: Session = Depends(get_db),
):
    quote = db.get(Quote, quote_id)
    if not quote:
        raise HTTPException(status_code=404)
    if quote.status != "draft":
        raise HTTPException(status_code=403)
    item = db.get(LineItem, item_id)
    if not item or item.quote_id != quote_id:
        raise HTTPException(status_code=404)
    db.delete(item)
    db.flush()
    _recalc_totals(quote)
    db.commit()
    return RedirectResponse(f"/quotes/{quote_id}/edit", status_code=303)
