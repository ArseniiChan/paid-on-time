from datetime import date
from decimal import Decimal

from app.checkbook import CheckbookContract, CheckbookPayment
from app.payment_lag import first_payment_lags, lag_by_agency

DYCD = "Department of Youth and Community Development"
DHS = "Department of Homeless Services"


def contract(cid: str, agency: str, start: date | None) -> CheckbookContract:
    return CheckbookContract(cid, "EXAMPLE INC", agency, "", Decimal(0), Decimal(0), start, None)


def payment(cid: str, issued: date) -> CheckbookPayment:
    return CheckbookPayment(cid, "EXAMPLE INC", "", Decimal("100.00"), issued, "PV")


def test_lag_uses_the_earliest_payment():
    lags = first_payment_lags(
        [contract("C1", DYCD, date(2025, 7, 1))],
        [payment("C1", date(2026, 3, 1)), payment("C1", date(2026, 1, 28))],
    )
    assert lags[0].days_to_first_payment == 211  # 2025-07-01 to 2026-01-28


def test_unpaid_contract_has_no_lag_and_no_start_date_is_skipped():
    lags = first_payment_lags(
        [contract("C1", DYCD, date(2025, 7, 1)), contract("C2", DYCD, None)], []
    )
    assert [(lag.contract_id, lag.days_to_first_payment) for lag in lags] == [("C1", None)]


def test_payment_before_start_counts_as_day_zero():
    lags = first_payment_lags(
        [contract("C1", DYCD, date(2025, 7, 1))], [payment("C1", date(2025, 6, 15))]
    )
    assert lags[0].days_to_first_payment == 0


def test_agency_summary_sorts_slowest_first_and_counts_unpaid():
    lags = first_payment_lags(
        [
            contract("A", DYCD, date(2025, 7, 1)),
            contract("B", DYCD, date(2025, 7, 1)),
            contract("C", DYCD, date(2025, 7, 1)),
            contract("D", DHS, date(2025, 7, 1)),
        ],
        [
            payment("A", date(2026, 1, 28)),  # 211 days
            payment("B", date(2025, 10, 9)),  # 100 days
            payment("D", date(2025, 8, 20)),  # 50 days
        ],
    )
    dycd, dhs = lag_by_agency(lags)

    assert (dycd.agency, dycd.contracts, dycd.paid) == (DYCD, 3, 2)
    assert dycd.median_days == 155.5
    assert dycd.over_200_days == 1
    assert (dhs.agency, dhs.median_days) == (DHS, 50)
