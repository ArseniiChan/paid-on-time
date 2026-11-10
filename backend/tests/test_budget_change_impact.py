from datetime import date
from decimal import Decimal

from app.models import Agency, Invoice
from app.rules import budget_change_impact

DYCD = Agency(name="DYCD", freezes_on_budget_mod=True)


def invoice(amount: str, submitted: date | None) -> Invoice:
    status = "pending" if submitted else "draft"
    return Invoice(amount=Decimal(amount), status=status, submitted_date=submitted)


def test_unsubmitted_invoices_are_blocked_at_freezing_agency():
    invoices = [
        invoice("12500.00", None),
        invoice("8000.50", None),
        invoice("9000.00", date(2026, 10, 1)),
    ]
    result = budget_change_impact(DYCD, invoices)
    assert result.blocks_billing is True
    assert len(result.blocked_invoices) == 2
    assert result.blocked_amount == Decimal("20500.50")
    assert "DYCD" in result.reason
    assert "$20,500.50" in result.reason


def test_all_invoices_submitted_is_safe():
    result = budget_change_impact(DYCD, [invoice("9000.00", date(2026, 10, 1))])
    assert result.blocks_billing is False
    assert result.blocked_invoices == []
    assert result.blocked_amount == Decimal("0.00")


def test_no_invoices_is_safe():
    assert budget_change_impact(DYCD, []).blocks_billing is False


def test_non_freezing_agency_never_blocks():
    other = Agency(name="Example Agency", freezes_on_budget_mod=False)
    result = budget_change_impact(other, [invoice("5000.00", None)])
    assert result.blocks_billing is False
