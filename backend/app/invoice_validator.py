"""Check a draft invoice against its contract before it goes into PASSPort.

The point is to catch the mistakes that get an invoice sent back while the nonprofit can
still fix them, instead of finding out weeks later in review.

Pure functions with no database access, like app/rules.py. The contract's terms come in
as a ContractTerms object. Today those are typed in or loaded from test data; the next step
is filling them by parsing the contract itself. Keeping the parser and the checks apart is
on purpose: if parsing gets a term wrong, the user sees which term and can correct it, and
every flag below still points to the rule it comes from.
"""

from dataclasses import dataclass, field
from datetime import date, timedelta
from decimal import Decimal

ERROR = "error"  # fix before submitting
WARNING = "warning"  # it can go in, but it costs something

# Sources for the flags. Checked 11/17/2026.
MOCS_FY27_GUIDANCE = "MOCS, FY27 Provider Guidance on HHS Contract Advances (Sept. 2026), p. 5"


@dataclass(frozen=True)
class ContractTerms:
    contract_number: str
    term_start: date
    term_end: date
    # Budget line name -> amount budgeted for the year.
    budget_lines: dict[str, Decimal]
    # Days after the end of a service period to submit its invoice. None = no window known.
    invoice_window_days: int | None = None
    window_source: str | None = None
    required_documents: tuple[str, ...] = ()


@dataclass(frozen=True)
class DraftInvoice:
    contract_number: str
    period_start: date
    period_end: date
    # Budget line name -> amount billed on this invoice.
    lines: dict[str, Decimal]
    attached_documents: frozenset[str] = frozenset()


@dataclass(frozen=True)
class Issue:
    code: str
    severity: str
    message: str
    source: str | None = None


@dataclass
class ValidationResult:
    issues: list[Issue] = field(default_factory=list)

    @property
    def ok(self) -> bool:
        """True when nothing would stop the invoice. Warnings don't count."""
        return not any(issue.severity == ERROR for issue in self.issues)


def validate_invoice(
    invoice: DraftInvoice,
    terms: ContractTerms,
    *,
    billed_to_date: dict[str, Decimal] | None = None,
    budget_change_pending: bool = False,
    submit_on: date | None = None,
) -> ValidationResult:
    """Run every check and return all problems at once, not just the first one.

    billed_to_date: amounts already invoiced per budget line this year.
    submit_on: the day the user plans to submit. Defaults to today.
    """
    billed_to_date = billed_to_date or {}
    submit_on = submit_on or date.today()
    issues: list[Issue] = []

    if invoice.contract_number != terms.contract_number:
        issues.append(
            Issue(
                "wrong_contract",
                ERROR,
                f"Invoice is for contract {invoice.contract_number}, but these terms are for "
                f"{terms.contract_number}.",
            )
        )

    issues += _check_period(invoice, terms)
    issues += _check_lines(invoice, terms, billed_to_date)

    missing = [doc for doc in terms.required_documents if doc not in invoice.attached_documents]
    if missing:
        issues.append(
            Issue(
                "missing_documents",
                ERROR,
                "Missing supporting documents the contract requires: " + ", ".join(missing) + ".",
            )
        )

    if budget_change_pending:
        issues.append(
            Issue(
                "budget_change_pending",
                ERROR,
                "A budget change is pending on this contract. PASSPort won't accept new "
                "invoices until it is approved.",
                MOCS_FY27_GUIDANCE,
            )
        )

    issues += _check_window(invoice, terms, submit_on)
    return ValidationResult(issues)


def _check_period(invoice: DraftInvoice, terms: ContractTerms) -> list[Issue]:
    if invoice.period_start > invoice.period_end:
        return [Issue("bad_period", ERROR, "Service period starts after it ends.")]
    if invoice.period_start < terms.term_start or invoice.period_end > terms.term_end:
        return [
            Issue(
                "outside_term",
                ERROR,
                f"Service period {invoice.period_start} to {invoice.period_end} falls outside "
                f"the contract term ({terms.term_start} to {terms.term_end}).",
            )
        ]
    return []


def _check_lines(
    invoice: DraftInvoice, terms: ContractTerms, billed_to_date: dict[str, Decimal]
) -> list[Issue]:
    issues = []
    if not invoice.lines:
        return [Issue("empty_invoice", ERROR, "Invoice has no budget lines.")]

    for line, amount in invoice.lines.items():
        if amount <= 0:
            issues.append(
                Issue("bad_amount", ERROR, f"'{line}' has a zero or negative amount ({amount}).")
            )
            continue
        if line not in terms.budget_lines:
            issues.append(
                Issue("unknown_line", ERROR, f"'{line}' is not a budget line on this contract.")
            )
            continue
        remaining = terms.budget_lines[line] - billed_to_date.get(line, Decimal("0"))
        if amount > remaining:
            issues.append(
                Issue(
                    "over_budget_line",
                    ERROR,
                    f"'{line}' bills ${amount:,.2f} but only ${remaining:,.2f} is left on that "
                    "line. Move money with a budget change first, or bill less.",
                )
            )
    return issues


def _check_window(invoice: DraftInvoice, terms: ContractTerms, submit_on: date) -> list[Issue]:
    if terms.invoice_window_days is None:
        return []
    due = invoice.period_end + timedelta(days=terms.invoice_window_days)
    if submit_on <= due:
        return []
    return [
        Issue(
            "past_window",
            WARNING,
            f"Due {due} ({terms.invoice_window_days} days after the service period ended), "
            f"planned for {submit_on}. If you can't make it, ask the contract manager for a "
            "written extension. MOCS says three or more missed invoices may affect eligibility "
            "for future advances.",
            terms.window_source,
        )
    ]
