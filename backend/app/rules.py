"""Billing rule checks.

Pure functions with no database access, so they are easy to test and reuse from the
API, background jobs, or the forecast.
"""

from dataclasses import dataclass, field
from decimal import Decimal

from app.models import Agency, BudgetModification, Invoice


@dataclass(frozen=True)
class FreezeCheck:
    frozen: bool
    reason: str | None = None


def invoicing_frozen(agency: Agency, budget_mods: list[BudgetModification]) -> FreezeCheck:
    """Is invoicing on a contract blocked by a pending budget modification?

    Some agencies stop accepting new invoices on a contract while a budget change on it is
    pending approval. DYCD: "Once a POCR is initiated in PASSPort, Providers will not be
    allowed to submit invoices" (DYCD FY27 Fiscal Manual for PASSPort Users, p. 43).
    """
    if not agency.freezes_on_budget_mod:
        return FreezeCheck(frozen=False)

    pending = [mod for mod in budget_mods if mod.status == "pending"]
    if not pending:
        return FreezeCheck(frozen=False)

    return FreezeCheck(
        frozen=True,
        reason=(
            f"{agency.name} does not accept new invoices while a budget modification is "
            f"pending ({len(pending)} pending on this contract)."
        ),
    )


@dataclass(frozen=True)
class FreezeImpact:
    blocks_billing: bool
    blocked_invoices: list[Invoice] = field(default_factory=list)
    blocked_amount: Decimal = Decimal("0.00")
    reason: str | None = None


def budget_change_impact(agency: Agency, invoices: list[Invoice]) -> FreezeImpact:
    """If a budget change were submitted now, which invoices would it block?

    Answers the "Check impact" step before the user submits a budget change in PASSPort
    (wireframe screens 7a "Safe to submit" and 7b "Billing freeze warning"). At an agency
    that freezes invoicing while a budget change is pending, any invoice not yet submitted
    can't be submitted until the change is approved. Invoices already submitted keep moving.
    """
    if not agency.freezes_on_budget_mod:
        return FreezeImpact(blocks_billing=False)

    blocked = [invoice for invoice in invoices if invoice.submitted_date is None]
    if not blocked:
        return FreezeImpact(blocks_billing=False)

    total = sum((invoice.amount for invoice in blocked), Decimal("0.00"))
    return FreezeImpact(
        blocks_billing=True,
        blocked_invoices=blocked,
        blocked_amount=total,
        reason=(
            f"{agency.name} does not accept new invoices while a budget modification is "
            f"pending. Submitting now would hold {len(blocked)} unsubmitted invoice(s) "
            f"worth ${total:,.2f} until it is approved."
        ),
    )
