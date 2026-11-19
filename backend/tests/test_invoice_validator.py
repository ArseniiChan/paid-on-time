from datetime import date
from decimal import Decimal

from app.invoice_validator import (
    ERROR,
    WARNING,
    ContractTerms,
    DraftInvoice,
    validate_invoice,
)

# Made-up contract and invoice for testing. Not real data.
TERMS = ContractTerms(
    contract_number="CT1-260-20261234567",
    term_start=date(2026, 7, 1),
    term_end=date(2027, 6, 30),
    budget_lines={"Personnel": Decimal("120000.00"), "Supplies": Decimal("8000.00")},
    invoice_window_days=30,
    window_source="DOHMH Fiscal Manual for Human Services, s. 4.6",
    required_documents=("timesheets",),
)

GOOD = DraftInvoice(
    contract_number="CT1-260-20261234567",
    period_start=date(2026, 10, 1),
    period_end=date(2026, 10, 31),
    lines={"Personnel": Decimal("10000.00"), "Supplies": Decimal("500.00")},
    attached_documents=frozenset({"timesheets"}),
)


def codes(result):
    return {issue.code for issue in result.issues}


def test_clean_invoice_passes():
    result = validate_invoice(GOOD, TERMS, submit_on=date(2026, 11, 17))
    assert result.ok
    assert result.issues == []


def test_reports_every_problem_at_once():
    bad = DraftInvoice(
        contract_number="CT1-260-20261234567",
        period_start=date(2026, 10, 1),
        period_end=date(2026, 10, 31),
        lines={"Personnel": Decimal("10000.00"), "Travel": Decimal("300.00")},
        attached_documents=frozenset(),
    )
    result = validate_invoice(bad, TERMS, submit_on=date(2026, 11, 17))
    assert not result.ok
    assert codes(result) == {"unknown_line", "missing_documents"}


def test_over_remaining_budget_line():
    result = validate_invoice(
        GOOD,
        TERMS,
        billed_to_date={"Supplies": Decimal("7800.00")},
        submit_on=date(2026, 11, 17),
    )
    assert codes(result) == {"over_budget_line"}
    assert "$200.00" in result.issues[0].message


def test_exactly_remaining_is_allowed():
    result = validate_invoice(
        GOOD,
        TERMS,
        billed_to_date={"Supplies": Decimal("7500.00")},
        submit_on=date(2026, 11, 17),
    )
    assert result.ok


def test_period_outside_contract_term():
    early = DraftInvoice(
        contract_number=GOOD.contract_number,
        period_start=date(2026, 6, 1),
        period_end=date(2026, 6, 30),
        lines=GOOD.lines,
        attached_documents=GOOD.attached_documents,
    )
    assert codes(validate_invoice(early, TERMS, submit_on=date(2026, 7, 15))) == {"outside_term"}


def test_period_backwards():
    backwards = DraftInvoice(
        contract_number=GOOD.contract_number,
        period_start=date(2026, 10, 31),
        period_end=date(2026, 10, 1),
        lines=GOOD.lines,
        attached_documents=GOOD.attached_documents,
    )
    assert "bad_period" in codes(validate_invoice(backwards, TERMS, submit_on=date(2026, 11, 1)))


def test_pending_budget_change_blocks():
    result = validate_invoice(GOOD, TERMS, budget_change_pending=True, submit_on=date(2026, 11, 17))
    assert not result.ok
    (issue,) = result.issues
    assert issue.code == "budget_change_pending"
    assert issue.source and "MOCS" in issue.source


def test_late_is_a_warning_not_an_error():
    # Period ends 10/31, window is 30 days, so due 11/30. Planned 12/2.
    result = validate_invoice(GOOD, TERMS, submit_on=date(2026, 12, 2))
    assert result.ok
    (issue,) = result.issues
    assert issue.severity == WARNING
    assert issue.code == "past_window"
    assert "2026-11-30" in issue.message


def test_last_day_of_window_is_on_time():
    assert validate_invoice(GOOD, TERMS, submit_on=date(2026, 11, 30)).issues == []


def test_no_window_known_means_no_window_check():
    terms = ContractTerms(
        contract_number=TERMS.contract_number,
        term_start=TERMS.term_start,
        term_end=TERMS.term_end,
        budget_lines=TERMS.budget_lines,
    )
    invoice = DraftInvoice(
        contract_number=GOOD.contract_number,
        period_start=GOOD.period_start,
        period_end=GOOD.period_end,
        lines=GOOD.lines,
    )
    assert validate_invoice(invoice, terms, submit_on=date(2027, 3, 1)).ok


def test_wrong_contract_and_bad_amounts():
    bad = DraftInvoice(
        contract_number="CT1-999-00000000000",
        period_start=GOOD.period_start,
        period_end=GOOD.period_end,
        lines={"Personnel": Decimal("0.00")},
        attached_documents=GOOD.attached_documents,
    )
    result = validate_invoice(bad, TERMS, submit_on=date(2026, 11, 17))
    assert codes(result) == {"wrong_contract", "bad_amount"}
    assert all(issue.severity == ERROR for issue in result.issues)


def test_empty_invoice():
    empty = DraftInvoice(
        contract_number=GOOD.contract_number,
        period_start=GOOD.period_start,
        period_end=GOOD.period_end,
        lines={},
        attached_documents=GOOD.attached_documents,
    )
    assert codes(validate_invoice(empty, TERMS, submit_on=date(2026, 11, 17))) == {"empty_invoice"}
