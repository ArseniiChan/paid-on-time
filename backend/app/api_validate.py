"""POST /invoices/validate: check a draft invoice against its contract terms."""

from datetime import date
from decimal import Decimal

from fastapi import APIRouter
from pydantic import BaseModel, Field

from app.invoice_validator import ContractTerms, DraftInvoice, validate_invoice

router = APIRouter()


class ContractTermsIn(BaseModel):
    contract_number: str
    term_start: date
    term_end: date
    budget_lines: dict[str, Decimal]
    invoice_window_days: int | None = Field(default=None, ge=0)
    window_source: str | None = None
    required_documents: list[str] = []


class DraftInvoiceIn(BaseModel):
    contract_number: str
    period_start: date
    period_end: date
    lines: dict[str, Decimal]
    attached_documents: list[str] = []


class ValidateRequest(BaseModel):
    contract: ContractTermsIn
    invoice: DraftInvoiceIn
    billed_to_date: dict[str, Decimal] = {}
    budget_change_pending: bool = False
    submit_on: date | None = None


class IssueOut(BaseModel):
    code: str
    severity: str
    message: str
    source: str | None


class ValidateResponse(BaseModel):
    ok: bool
    issues: list[IssueOut]


@router.post("/invoices/validate", response_model=ValidateResponse)
def validate(request: ValidateRequest) -> ValidateResponse:
    c, i = request.contract, request.invoice
    terms = ContractTerms(
        contract_number=c.contract_number,
        term_start=c.term_start,
        term_end=c.term_end,
        budget_lines=c.budget_lines,
        invoice_window_days=c.invoice_window_days,
        window_source=c.window_source,
        required_documents=tuple(c.required_documents),
    )
    invoice = DraftInvoice(
        contract_number=i.contract_number,
        period_start=i.period_start,
        period_end=i.period_end,
        lines=i.lines,
        attached_documents=frozenset(i.attached_documents),
    )
    result = validate_invoice(
        invoice,
        terms,
        billed_to_date=request.billed_to_date,
        budget_change_pending=request.budget_change_pending,
        submit_on=request.submit_on,
    )
    return ValidateResponse(
        ok=result.ok,
        issues=[IssueOut(**vars(issue)) for issue in result.issues],
    )
