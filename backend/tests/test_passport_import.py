from datetime import date
from decimal import Decimal

from app.passport_import import RowError, parse_invoice_csv

HEADER = "Contract Number,Invoice Number,Amount,Status,Submitted Date\n"


def test_valid_rows_parse():
    csv_text = (
        HEADER
        + 'CT1-260-20261234567,INV-001,"$95,000.00",Submitted,07/15/2026\n'
        + "CT1-260-20261234567,INV-002,1250.5,Draft,\n"
    )
    result = parse_invoice_csv(csv_text)

    assert result.ok
    first, second = result.invoices
    assert first.contract_number == "CT1-260-20261234567"
    assert first.amount == Decimal("95000.00")
    assert first.status == "submitted"
    assert first.submitted_date == date(2026, 7, 15)
    assert second.amount == Decimal("1250.50")
    assert second.submitted_date is None


def test_each_bad_row_gets_its_own_error_and_good_rows_still_import():
    csv_text = (
        HEADER
        + "CT1,INV-001,100.00,Submitted,07/15/2026\n"  # line 2: fine
        + "CT1,INV-002,abc,Submitted,07/15/2026\n"  # line 3: bad amount
        + "CT1,INV-003,100.00,Submitted,13/45/2026\n"  # line 4: bad date
        + ",INV-004,100.00,Submitted,07/15/2026\n"  # line 5: no contract
        + "CT1,INV-005,200.00,Approved,2026-08-01\n"  # line 6: fine (ISO date)
    )
    result = parse_invoice_csv(csv_text)

    assert [inv.invoice_number for inv in result.invoices] == ["INV-001", "INV-005"]
    assert [err.line for err in result.errors] == [3, 4, 5]
    assert "not a number" in result.errors[0].message
    assert "not a date" in result.errors[1].message
    assert "Contract Number is blank" in result.errors[2].message


def test_row_with_several_problems_reports_all_of_them():
    result = parse_invoice_csv(HEADER + "CT1,,-5.00,,\n")

    assert result.errors == [
        RowError(2, "Invoice Number is blank. Status is blank. Amount '-5.00' is negative.")
    ]


def test_amount_with_fractional_cents_is_rejected():
    result = parse_invoice_csv(HEADER + "CT1,INV-001,10.005,Submitted,\n")
    assert "more than two decimal places" in result.errors[0].message


def test_short_row_is_reported_not_crashed():
    result = parse_invoice_csv(HEADER + "CT1,INV-001\n")
    assert result.errors[0].line == 2
    assert "Amount is blank" in result.errors[0].message


def test_missing_columns_fail_on_header_line():
    result = parse_invoice_csv("Contract Number,Amount\nCT1,100\n")

    assert result.invoices == []
    assert result.errors == [
        RowError(1, "Missing column(s): Invoice Number, Status, Submitted Date.")
    ]


def test_headers_match_loosely_and_extra_columns_are_ignored():
    csv_text = (
        " contract  NUMBER ,Vendor,invoice number,AMOUNT,status,Submitted Date\n"
        "CT1,Example Youth Services,INV-001,10.00,Submitted,07/15/2026\n"
    )
    result = parse_invoice_csv(csv_text)
    assert result.ok
    assert result.invoices[0].contract_number == "CT1"


def test_excel_bytes_with_bom_and_blank_lines():
    data = ("﻿" + HEADER + "\nCT1,INV-001,10.00,Submitted,07/15/2026\n\n").encode()
    result = parse_invoice_csv(data)
    assert result.ok
    assert len(result.invoices) == 1


def test_empty_and_non_utf8_files():
    assert parse_invoice_csv("").errors == [RowError(1, "File is empty.")]
    assert "not UTF-8" in parse_invoice_csv(b"\xff\xfe\x00bad").errors[0].message
