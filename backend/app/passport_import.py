"""Parse PASSPort invoice exports (FR1: data ingestion).

Pure functions with no database access, like app/rules.py. The parser returns every row
that parsed and one error per row that didn't, so a finance director can fix the file and
re-upload instead of guessing which line broke.

Expected columns (header names are matched case-insensitively, ignoring extra spaces):

    Contract Number, Invoice Number, Amount, Status, Submitted Date

Extra columns are ignored. "Submitted Date" may be blank (draft invoices have none).

Note: these headers are our working assumption. Check them against a real PASSPort
export (with made-up data) and update REQUIRED_COLUMNS if they differ.
"""

import csv
import io
from dataclasses import dataclass, field
from datetime import date, datetime
from decimal import Decimal, InvalidOperation

REQUIRED_COLUMNS = ("contract number", "invoice number", "amount", "status", "submitted date")
DATE_FORMATS = ("%m/%d/%Y", "%Y-%m-%d")


@dataclass(frozen=True)
class InvoiceRow:
    contract_number: str
    invoice_number: str
    amount: Decimal
    status: str
    submitted_date: date | None


@dataclass(frozen=True)
class RowError:
    # Line number in the file as a spreadsheet would show it: the header is line 1.
    line: int
    message: str


@dataclass
class ImportResult:
    invoices: list[InvoiceRow] = field(default_factory=list)
    errors: list[RowError] = field(default_factory=list)

    @property
    def ok(self) -> bool:
        return not self.errors


def parse_invoice_csv(data: str | bytes) -> ImportResult:
    """Parse a PASSPort invoice export.

    Accepts the raw file contents. Bytes are decoded as UTF-8, with or without the byte
    order mark Excel adds.
    """
    if isinstance(data, bytes):
        try:
            data = data.decode("utf-8-sig")
        except UnicodeDecodeError:
            return ImportResult(errors=[RowError(1, "File is not UTF-8 text. Save it as CSV.")])
    data = data.removeprefix("﻿")

    reader = csv.reader(io.StringIO(data))
    header = next(reader, None)
    if header is None:
        return ImportResult(errors=[RowError(1, "File is empty.")])

    columns = [_normalize(name) for name in header]
    missing = [name for name in REQUIRED_COLUMNS if name not in columns]
    if missing:
        names = ", ".join(name.title() for name in missing)
        return ImportResult(errors=[RowError(1, f"Missing column(s): {names}.")])
    index = {name: columns.index(name) for name in REQUIRED_COLUMNS}

    result = ImportResult()
    for line, cells in enumerate(reader, start=2):
        if not any(cell.strip() for cell in cells):
            continue  # skip blank lines
        row = {name: (cells[i].strip() if i < len(cells) else "") for name, i in index.items()}
        problems, invoice = _parse_row(row)
        if problems:
            result.errors.append(RowError(line, " ".join(problems)))
        else:
            result.invoices.append(invoice)
    return result


def _parse_row(row: dict[str, str]) -> tuple[list[str], InvoiceRow | None]:
    problems: list[str] = []

    for name in ("contract number", "invoice number", "status"):
        if not row[name]:
            problems.append(f"{name.title()} is blank.")

    amount = _parse_amount(row["amount"], problems)
    submitted = _parse_date(row["submitted date"], problems)

    if problems:
        return problems, None
    return [], InvoiceRow(
        contract_number=row["contract number"],
        invoice_number=row["invoice number"],
        amount=amount,
        status=row["status"].lower(),
        submitted_date=submitted,
    )


def _parse_amount(raw: str, problems: list[str]) -> Decimal | None:
    if not raw:
        problems.append("Amount is blank.")
        return None
    cleaned = raw.replace("$", "").replace(",", "").strip()
    try:
        amount = Decimal(cleaned)
    except InvalidOperation:
        problems.append(f"Amount {raw!r} is not a number.")
        return None
    if not amount.is_finite():
        problems.append(f"Amount {raw!r} is not a number.")
        return None
    if amount < 0:
        problems.append(f"Amount {raw!r} is negative.")
        return None
    if amount != amount.quantize(Decimal("0.01")):
        problems.append(f"Amount {raw!r} has more than two decimal places.")
        return None
    return amount.quantize(Decimal("0.01"))


def _parse_date(raw: str, problems: list[str]) -> date | None:
    if not raw:
        return None
    for fmt in DATE_FORMATS:
        try:
            return datetime.strptime(raw, fmt).date()
        except ValueError:
            continue
    problems.append(f"Submitted Date {raw!r} is not a date (use MM/DD/YYYY).")
    return None


def _normalize(name: str) -> str:
    return " ".join(name.strip().lower().split())
