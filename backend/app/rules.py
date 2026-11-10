"""Billing rule checks.

Pure functions with no database access, so they are easy to test and reuse from the
API, background jobs, or the forecast.
"""

from dataclasses import dataclass

from app.models import Agency, BudgetModification


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
