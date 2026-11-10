"""Database schema. Mirrors docs/data-model.md; change both together."""

from datetime import date
from decimal import Decimal

from sqlalchemy import Boolean, Date, ForeignKey, Numeric, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db import Base

Money = Numeric(14, 2)


class Organization(Base):
    """A nonprofit that holds city contracts."""

    __tablename__ = "organization"

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(255))
    ein: Mapped[str] = mapped_column(String(10), unique=True)

    contracts: Mapped[list["Contract"]] = relationship(back_populates="organization")
    forecasts: Mapped[list["Forecast"]] = relationship(back_populates="organization")


class Agency(Base):
    """A city agency that funds contracts (DYCD, DHS, ...)."""

    __tablename__ = "agency"

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(255), unique=True)
    # True when a pending budget modification stops new invoices (e.g. DYCD).
    freezes_on_budget_mod: Mapped[bool] = mapped_column(Boolean, default=False)

    contracts: Mapped[list["Contract"]] = relationship(back_populates="agency")
    rules: Mapped[list["Rule"]] = relationship(back_populates="agency")


class Contract(Base):
    __tablename__ = "contract"

    id: Mapped[int] = mapped_column(primary_key=True)
    org_id: Mapped[int] = mapped_column(ForeignKey("organization.id"))
    agency_id: Mapped[int] = mapped_column(ForeignKey("agency.id"))
    contract_number: Mapped[str] = mapped_column(String(64), unique=True)
    total_amount: Mapped[Decimal] = mapped_column(Money)

    organization: Mapped[Organization] = relationship(back_populates="contracts")
    agency: Mapped[Agency] = relationship(back_populates="contracts")
    invoices: Mapped[list["Invoice"]] = relationship(back_populates="contract")
    payments: Mapped[list["Payment"]] = relationship(back_populates="contract")
    budget_modifications: Mapped[list["BudgetModification"]] = relationship(
        back_populates="contract"
    )


class Invoice(Base):
    __tablename__ = "invoice"

    id: Mapped[int] = mapped_column(primary_key=True)
    contract_id: Mapped[int] = mapped_column(ForeignKey("contract.id"))
    amount: Mapped[Decimal] = mapped_column(Money)
    status: Mapped[str] = mapped_column(String(32))
    submitted_date: Mapped[date | None] = mapped_column(Date)

    contract: Mapped[Contract] = relationship(back_populates="invoices")
    payments: Mapped[list["Payment"]] = relationship(back_populates="invoice")
    alerts: Mapped[list["Alert"]] = relationship(back_populates="invoice")


class Payment(Base):
    __tablename__ = "payment"

    id: Mapped[int] = mapped_column(primary_key=True)
    contract_id: Mapped[int] = mapped_column(ForeignKey("contract.id"))
    invoice_id: Mapped[int | None] = mapped_column(ForeignKey("invoice.id"))
    amount: Mapped[Decimal] = mapped_column(Money)
    paid_date: Mapped[date] = mapped_column(Date)

    contract: Mapped[Contract] = relationship(back_populates="payments")
    invoice: Mapped[Invoice | None] = relationship(back_populates="payments")


class BudgetModification(Base):
    __tablename__ = "budget_modification"

    id: Mapped[int] = mapped_column(primary_key=True)
    contract_id: Mapped[int] = mapped_column(ForeignKey("contract.id"))
    amount: Mapped[Decimal] = mapped_column(Money)
    # "pending", "approved" or "rejected"
    status: Mapped[str] = mapped_column(String(32))
    submitted_date: Mapped[date | None] = mapped_column(Date)

    contract: Mapped[Contract] = relationship(back_populates="budget_modifications")


class Rule(Base):
    """An agency billing rule, with the citation shown to the user."""

    __tablename__ = "rule"

    id: Mapped[int] = mapped_column(primary_key=True)
    agency_id: Mapped[int] = mapped_column(ForeignKey("agency.id"))
    description: Mapped[str] = mapped_column(Text)
    citation: Mapped[str] = mapped_column(Text)

    agency: Mapped[Agency] = relationship(back_populates="rules")
    alerts: Mapped[list["Alert"]] = relationship(back_populates="rule")


class Alert(Base):
    """A rule violation found on an invoice."""

    __tablename__ = "alert"

    id: Mapped[int] = mapped_column(primary_key=True)
    rule_id: Mapped[int] = mapped_column(ForeignKey("rule.id"))
    invoice_id: Mapped[int] = mapped_column(ForeignKey("invoice.id"))
    message: Mapped[str] = mapped_column(Text)

    rule: Mapped[Rule] = relationship(back_populates="alerts")
    invoice: Mapped[Invoice] = relationship(back_populates="alerts")


class Forecast(Base):
    """One week of projected cash for an organization."""

    __tablename__ = "forecast"

    id: Mapped[int] = mapped_column(primary_key=True)
    org_id: Mapped[int] = mapped_column(ForeignKey("organization.id"))
    week_start: Mapped[date] = mapped_column(Date)
    ending_cash: Mapped[Decimal] = mapped_column(Money)
    interest: Mapped[Decimal] = mapped_column(Money)

    organization: Mapped[Organization] = relationship(back_populates="forecasts")
