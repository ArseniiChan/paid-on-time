from decimal import Decimal

from app.models import Agency, BudgetModification
from app.rules import invoicing_frozen


def mod(status: str) -> BudgetModification:
    return BudgetModification(amount=Decimal("5000.00"), status=status)


def test_freezing_agency_with_pending_mod_is_frozen():
    dycd = Agency(name="DYCD", freezes_on_budget_mod=True)
    result = invoicing_frozen(dycd, [mod("approved"), mod("pending")])
    assert result.frozen is True
    assert "DYCD" in result.reason
    assert "1 pending" in result.reason


def test_freezing_agency_without_pending_mod_is_not_frozen():
    dycd = Agency(name="DYCD", freezes_on_budget_mod=True)
    assert invoicing_frozen(dycd, [mod("approved")]).frozen is False


def test_non_freezing_agency_is_never_frozen():
    other = Agency(name="Example Agency", freezes_on_budget_mod=False)
    assert invoicing_frozen(other, [mod("pending")]).frozen is False
