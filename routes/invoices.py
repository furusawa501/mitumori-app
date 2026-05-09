import math
from datetime import date

from fastapi import APIRouter, Depends, Form, HTTPException, Request
from fastapi.responses import RedirectResponse
from sqlalchemy.orm import Session

from database import get_db
from models import Invoice, LineItem
from utils import flash, render

router = APIRouter(prefix="/invoices")

# 許可されたステータス遷移: (現在, action) → 次のステータス
_TRANSITIONS = {
    ("draft", "send"): "sent",
    ("sent", "pay"): "paid",
    ("sent", "overdue"): "overdue",
    ("overdue", "pay"): "paid",
}


def _recalc_totals(invoice: Invoice) -> None:
    subtotal = sum(item.amount for item in invoice.line_items)
    invoice.subtotal = subtotal
    invoice.tax_amount = math.floor(subtotal * 0.10)
    invoice.total = invoice.subtotal + invoice.tax_amount


@router.get("")
def list_invoices(request: Request, status: str | None = None, db: Session = Depends(get_db)):
    q = db.query(Invoice)
    if status:
        q = q.filter(Invoice.status == status)
    invoices = q.order_by(Invoice.created_at.desc()).all()
    return render(request, "invoices/list.html", invoices=invoices, current_status=status)


@router.get("/{invoice_id}")
def detail_invoice(invoice_id: int, request: Request, db: Session = Depends(get_db)):
    invoice = db.get(Invoice, invoice_id)
    if not invoice:
        raise HTTPException(status_code=404)
    return render(request, "invoices/detail.html", invoice=invoice)


@router.get("/{invoice_id}/edit")
def edit_invoice_form(invoice_id: int, request: Request, db: Session = Depends(get_db)):
    invoice = db.get(Invoice, invoice_id)
    if not invoice:
        raise HTTPException(status_code=404)
    return render(request, "invoices/form.html", invoice=invoice)


@router.post("/{invoice_id}")
def update_invoice(
    invoice_id: int,
    request: Request,
    db: Session = Depends(get_db),
    title: str = Form(...),
    issue_date: date = Form(...),
    due_date: str = Form(""),
    notes: str = Form(""),
):
    invoice = db.get(Invoice, invoice_id)
    if not invoice:
        raise HTTPException(status_code=404)
    if invoice.status != "draft":
        raise HTTPException(status_code=403, detail="draft 状態の請求書のみ編集できます")
    invoice.title = title
    invoice.issue_date = issue_date
    invoice.due_date = date.fromisoformat(due_date) if due_date else None
    invoice.notes = notes or None
    db.commit()
    flash(request, "請求書を更新しました", "success")
    return RedirectResponse(f"/invoices/{invoice_id}/edit", status_code=303)


@router.post("/{invoice_id}/status")
def change_status(
    invoice_id: int,
    request: Request,
    db: Session = Depends(get_db),
    action: str = Form(...),
):
    invoice = db.get(Invoice, invoice_id)
    if not invoice:
        raise HTTPException(status_code=404)
    new_status = _TRANSITIONS.get((invoice.status, action))
    if not new_status:
        flash(request, "この操作は現在の状態では実行できません", "error")
        return RedirectResponse(f"/invoices/{invoice_id}", status_code=303)
    if action == "send" and not invoice.line_items:
        flash(request, "明細行を1件以上追加してから送付済みにしてください", "error")
        return RedirectResponse(f"/invoices/{invoice_id}", status_code=303)
    invoice.status = new_status
    db.commit()
    flash(request, "ステータスを更新しました", "success")
    return RedirectResponse(f"/invoices/{invoice_id}", status_code=303)


@router.post("/{invoice_id}/items")
def add_line_item(
    invoice_id: int,
    request: Request,
    db: Session = Depends(get_db),
    description: str = Form(...),
    quantity: float = Form(...),
    unit: str = Form(""),
    unit_price: int = Form(...),
    sort_order: int = Form(...),
):
    invoice = db.get(Invoice, invoice_id)
    if not invoice:
        raise HTTPException(status_code=404)
    if invoice.status != "draft":
        raise HTTPException(status_code=403)
    item = LineItem(
        invoice_id=invoice_id,
        sort_order=sort_order,
        description=description,
        quantity=quantity,
        unit=unit or None,
        unit_price=unit_price,
        amount=math.floor(quantity * unit_price),
    )
    db.add(item)
    db.flush()
    _recalc_totals(invoice)
    db.commit()
    return RedirectResponse(f"/invoices/{invoice_id}/edit", status_code=303)


@router.post("/{invoice_id}/items/{item_id}")
def update_line_item(
    invoice_id: int,
    item_id: int,
    request: Request,
    db: Session = Depends(get_db),
    description: str = Form(...),
    quantity: float = Form(...),
    unit: str = Form(""),
    unit_price: int = Form(...),
    sort_order: int = Form(...),
):
    invoice = db.get(Invoice, invoice_id)
    if not invoice:
        raise HTTPException(status_code=404)
    if invoice.status != "draft":
        raise HTTPException(status_code=403)
    item = db.get(LineItem, item_id)
    if not item or item.invoice_id != invoice_id:
        raise HTTPException(status_code=404)
    item.description = description
    item.quantity = quantity
    item.unit = unit or None
    item.unit_price = unit_price
    item.sort_order = sort_order
    item.amount = math.floor(quantity * unit_price)
    _recalc_totals(invoice)
    db.commit()
    return RedirectResponse(f"/invoices/{invoice_id}/edit", status_code=303)


@router.post("/{invoice_id}/items/{item_id}/delete")
def delete_line_item(
    invoice_id: int,
    item_id: int,
    request: Request,
    db: Session = Depends(get_db),
):
    invoice = db.get(Invoice, invoice_id)
    if not invoice:
        raise HTTPException(status_code=404)
    if invoice.status != "draft":
        raise HTTPException(status_code=403)
    item = db.get(LineItem, item_id)
    if not item or item.invoice_id != invoice_id:
        raise HTTPException(status_code=404)
    db.delete(item)
    db.flush()
    _recalc_totals(invoice)
    db.commit()
    return RedirectResponse(f"/invoices/{invoice_id}/edit", status_code=303)
