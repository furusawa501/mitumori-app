from datetime import datetime
from sqlalchemy import Column, Integer, Text, DateTime, Date, Float, ForeignKey
from sqlalchemy.orm import relationship
from database import Base


class Customer(Base):
    __tablename__ = "customers"

    id = Column(Integer, primary_key=True, autoincrement=True)
    company_name = Column(Text, nullable=False)
    contact_name = Column(Text, nullable=False)
    email = Column(Text, nullable=False)
    phone = Column(Text)
    address = Column(Text)
    notes = Column(Text)
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow)
    updated_at = Column(DateTime, nullable=False, default=datetime.utcnow, onupdate=datetime.utcnow)

    quotes = relationship("Quote", back_populates="customer")
    invoices = relationship("Invoice", back_populates="customer")


class Quote(Base):
    __tablename__ = "quotes"

    id = Column(Integer, primary_key=True, autoincrement=True)
    quote_number = Column(Text, nullable=False, unique=True)
    customer_id = Column(Integer, ForeignKey("customers.id"), nullable=False)
    status = Column(Text, nullable=False, default="draft")
    title = Column(Text, nullable=False)
    issue_date = Column(Date, nullable=False)
    valid_until = Column(Date)
    notes = Column(Text)
    subtotal = Column(Integer, nullable=False, default=0)
    tax_amount = Column(Integer, nullable=False, default=0)
    total = Column(Integer, nullable=False, default=0)
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow)
    updated_at = Column(DateTime, nullable=False, default=datetime.utcnow, onupdate=datetime.utcnow)

    customer = relationship("Customer", back_populates="quotes")
    line_items = relationship("LineItem", back_populates="quote", cascade="all, delete-orphan")
    invoices = relationship("Invoice", back_populates="quote")


class Invoice(Base):
    __tablename__ = "invoices"

    id = Column(Integer, primary_key=True, autoincrement=True)
    invoice_number = Column(Text, nullable=False, unique=True)
    quote_id = Column(Integer, ForeignKey("quotes.id"))
    customer_id = Column(Integer, ForeignKey("customers.id"), nullable=False)
    status = Column(Text, nullable=False, default="draft")
    title = Column(Text, nullable=False)
    issue_date = Column(Date, nullable=False)
    due_date = Column(Date)
    notes = Column(Text)
    subtotal = Column(Integer, nullable=False, default=0)
    tax_amount = Column(Integer, nullable=False, default=0)
    total = Column(Integer, nullable=False, default=0)
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow)
    updated_at = Column(DateTime, nullable=False, default=datetime.utcnow, onupdate=datetime.utcnow)

    customer = relationship("Customer", back_populates="invoices")
    quote = relationship("Quote", back_populates="invoices")
    line_items = relationship("LineItem", back_populates="invoice", cascade="all, delete-orphan")


class LineItem(Base):
    __tablename__ = "line_items"

    id = Column(Integer, primary_key=True, autoincrement=True)
    quote_id = Column(Integer, ForeignKey("quotes.id"))
    invoice_id = Column(Integer, ForeignKey("invoices.id"))
    sort_order = Column(Integer, nullable=False)
    description = Column(Text, nullable=False)
    quantity = Column(Float, nullable=False)
    unit = Column(Text)
    unit_price = Column(Integer, nullable=False)
    amount = Column(Integer, nullable=False)

    quote = relationship("Quote", back_populates="line_items")
    invoice = relationship("Invoice", back_populates="line_items")
