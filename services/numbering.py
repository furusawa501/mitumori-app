from models import Invoice, Quote


def next_quote_number(db, year: int) -> str:
    prefix = f"EST-{year}-"
    count = db.query(Quote).filter(Quote.quote_number.like(f"{prefix}%")).count()
    return f"{prefix}{count + 1:03d}"


def next_invoice_number(db, year: int) -> str:
    prefix = f"INV-{year}-"
    count = db.query(Invoice).filter(Invoice.invoice_number.like(f"{prefix}%")).count()
    return f"{prefix}{count + 1:03d}"
