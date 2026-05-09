from datetime import date

from models import Invoice, LineItem, Quote
from services.numbering import next_invoice_number


def convert_quote_to_invoice(db, quote: Quote) -> Invoice:
    invoice = Invoice(
        invoice_number=next_invoice_number(db, date.today().year),
        quote_id=quote.id,
        customer_id=quote.customer_id,
        title=quote.title,
        issue_date=date.today(),
        notes=quote.notes,
        subtotal=quote.subtotal,
        tax_amount=quote.tax_amount,
        total=quote.total,
    )
    db.add(invoice)
    db.flush()

    for item in quote.line_items:
        db.add(LineItem(
            invoice_id=invoice.id,
            sort_order=item.sort_order,
            description=item.description,
            quantity=item.quantity,
            unit=item.unit,
            unit_price=item.unit_price,
            amount=item.amount,
        ))

    quote.status = "converted"
    db.commit()
    return invoice
