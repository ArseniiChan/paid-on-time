"""How long each agency takes to make its first payment on a contract (input to FR3).

Checkbook NYC has contract start dates and payment issue dates, but not invoice dates, so
on its own it can't measure invoice-to-payment lag. What it can measure is the delay from
the day a contract starts to the city's first payment on it. That is the same measure the
NYC Comptroller uses in "Nonprofit, Nonpayment", so our numbers can be checked against
theirs. The forecast uses it as the expected wait for money on a new contract.

Pure functions, no database or network access.
"""

from collections import defaultdict
from dataclasses import dataclass
from statistics import median

from app.checkbook import CheckbookContract, CheckbookPayment


@dataclass(frozen=True)
class ContractLag:
    contract_id: str
    agency: str
    days_to_first_payment: int | None  # None: no payment yet


@dataclass(frozen=True)
class AgencyLag:
    agency: str
    contracts: int  # contracts with a start date
    paid: int  # of those, how many have a payment
    median_days: float | None  # over paid contracts only
    over_200_days: int  # paid contracts whose first payment took more than 200 days


def first_payment_lags(
    contracts: list[CheckbookContract], payments: list[CheckbookPayment]
) -> list[ContractLag]:
    """Days from each contract's start date to its earliest payment.

    Contracts without a start date are skipped. Payments dated before the start date
    (advances, or data errors) count as day 0, not as a negative lag.
    """
    first_paid = {}
    for p in payments:
        current = first_paid.get(p.contract_id)
        if current is None or p.issue_date < current:
            first_paid[p.contract_id] = p.issue_date

    lags = []
    for c in contracts:
        if c.start_date is None:
            continue
        paid_on = first_paid.get(c.contract_id)
        days = None if paid_on is None else max(0, (paid_on - c.start_date).days)
        lags.append(ContractLag(c.contract_id, c.agency, days))
    return lags


def lag_by_agency(lags: list[ContractLag]) -> list[AgencyLag]:
    """Summarize lags per agency, slowest median first.

    Unpaid contracts count toward `contracts` but not the median: a contract that hasn't
    been paid yet has a lag of at least its age, so leaving it out makes the median
    optimistic. `paid` versus `contracts` shows how much was left out.
    """
    groups: dict[str, list[ContractLag]] = defaultdict(list)
    for lag in lags:
        groups[lag.agency].append(lag)

    summary = []
    for agency, items in groups.items():
        days = [i.days_to_first_payment for i in items if i.days_to_first_payment is not None]
        summary.append(
            AgencyLag(
                agency=agency,
                contracts=len(items),
                paid=len(days),
                median_days=median(days) if days else None,
                over_200_days=sum(1 for d in days if d > 200),
            )
        )
    return sorted(summary, key=lambda a: (a.median_days is None, -(a.median_days or 0)))
