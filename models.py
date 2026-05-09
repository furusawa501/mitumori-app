from datetime import datetime
from sqlalchemy import Column, Integer, Text, DateTime, Date, Float, ForeignKey, UniqueConstraint
from sqlalchemy.orm import relationship
from database import Base


class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, autoincrement=True)
    email = Column(Text, nullable=False, unique=True)
    password_hash = Column(Text, nullable=False)
    plan = Column(Text, nullable=False, default="trial")
    trial_started_at = Column(DateTime, nullable=False, default=datetime.utcnow)
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow)

    customers = relationship("Customer", back_populates="user")
    quotes = relationship("Quote", back_populates="user")
    invoices = relationship("Invoice", back_populates="user")


class Customer(Base):
    __tablename__ = "customers"

    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    company_name = Column(Text, nullable=False)
    contact_name = Column(Text, nullable=False)
    email = Column(Text, nullable=False)
    phone = Column(Text)
    address = Column(Text)
    notes = Column(Text)
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow)
    updated_at = Column(DateTime, nullable=False, default=datetime.utcnow, onupdate=datetime.utcnow)

    user = relationship("User", back_populates="customers")
    quotes = relationship("Quote", back_populates="customer")
    invoices = relationship("Invoice", back_populates="customer")


class Quote(Base):
    __tablename__ = "quotes"
    __table_args__ = (UniqueConstraint("user_id", "quote_number"),)

    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    quote_number = Column(Text, nullable=False)
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

    user = relationship("User", back_populates="quotes")
    customer = relationship("Customer", back_populates="quotes")
    line_items = relationship("LineItem", back_populates="quote", cascade="all, delete-orphan")
    invoices = relationship("Invoice", back_populates="quote")


class Invoice(Base):
    __tablename__ = "invoices"
    __table_args__ = (UniqueConstraint("user_id", "invoice_number"),)

    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    invoice_number = Column(Text, nullable=False)
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

    user = relationship("User", back_populates="invoices")
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
