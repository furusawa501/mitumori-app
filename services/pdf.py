from pathlib import Path

import weasyprint
from jinja2 import Environment, FileSystemLoader

_TEMPLATE_DIR = Path(__file__).parent.parent / "templates"
_env = Environment(loader=FileSystemLoader(str(_TEMPLATE_DIR)))


def _render_pdf(template_name: str, **ctx) -> bytes:
    html = _env.get_template(template_name).render(**ctx)
    return weasyprint.HTML(string=html, base_url=str(_TEMPLATE_DIR)).write_pdf()


def generate_quote_pdf(quote) -> bytes:
    return _render_pdf("pdf/quote.html", quote=quote)


def generate_invoice_pdf(invoice) -> bytes:
    return _render_pdf("pdf/invoice.html", invoice=invoice)
