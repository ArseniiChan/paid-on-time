"""Checkbook NYC client tests. No network: a fake transport returns canned XML.

The response layout (status/result, result_records/record_count, then a list of
<transaction> elements) follows the API documentation and BetaNYC's nyc-checkbook-mcp
client. All names, IDs and amounts below are made up. Replace or add fixtures saved from
the live API once scripts/checkbook_probe.py has been run.
"""

from datetime import date
from decimal import Decimal

import pytest

from app.checkbook import (
    CheckbookClient,
    CheckbookError,
    Criterion,
    build_request,
    fetch_contracts,
    fetch_payments,
    parse_response,
)


def response_xml(rows: list[dict[str, str]], total: int | None = None) -> str:
    txns = "".join(
        "<transaction>" + "".join(f"<{k}>{v}</{k}>" for k, v in row.items()) + "</transaction>"
        for row in rows
    )
    count = len(rows) if total is None else total
    return (
        "<response><status><result>success</result><messages><message><code>1</code>"
        "<description>No Results Found</description></message></messages></status>"
        f"<result_records><record_count>{count}</record_count>"
        f"<spending_transactions>{txns}</spending_transactions></result_records></response>"
    )


ERROR_XML = (
    "<response><status><result>failure</result><messages><message><code>1106</code>"
    "<description>Provided response column 'year' value is not allowed.</description>"
    "</message></messages></status></response>"
)


class FakeTransport:
    """Returns queued (status, text) replies and records every request body."""

    def __init__(self, *replies: tuple[int, str]):
        self.replies = list(replies)
        self.bodies: list[str] = []

    def __call__(self, body: bytes) -> tuple[int, str]:
        self.bodies.append(body.decode())
        return self.replies.pop(0)


class FakeClock:
    def __init__(self):
        self.now = 0.0
        self.sleeps: list[float] = []

    def clock(self) -> float:
        return self.now

    def sleep(self, seconds: float) -> None:
        self.sleeps.append(seconds)
        self.now += seconds


def make_client(*replies: tuple[int, str]) -> tuple[CheckbookClient, FakeTransport, FakeClock]:
    transport, clock = FakeTransport(*replies), FakeClock()
    client = CheckbookClient(transport=transport, sleep=clock.sleep, clock=clock.clock)
    return client, transport, clock


PAYMENT = {
    "agency": "Department of Youth and Community Development",
    "payee_name": "EXAMPLE YOUTH SERVICES INC",
    "contract_id": "CT126020261234567",
    "check_amount": "95000.00",
    "issue_date": "2026-01-20",
    "document_id": "PV-0001",
    "expense_category": "CONTRACTUAL SERVICES",
}


def test_request_xml_has_filters_columns_and_paging():
    xml = build_request(
        "Spending",
        [
            Criterion("fiscal_year", value="2026"),
            Criterion("issue_date", start="2026-07-01", end="2026-12-31"),
        ],
        ("contract_id", "check_amount"),
        records_from=1001,
        max_records=1000,
    )
    assert "<type_of_data>Spending</type_of_data>" in xml
    assert "<records_from>1001</records_from><max_records>1000</max_records>" in xml
    assert "<name>fiscal_year</name><type>value</type><value>2026</value>" in xml
    assert "<type>range</type><start>2026-07-01</start>" in xml
    assert "<column>contract_id</column><column>check_amount</column>" in xml


def test_request_values_are_xml_escaped():
    xml = build_request("Spending", [Criterion("payee_name", value="A & B <Inc>")], ())
    assert "A &amp; B &lt;Inc&gt;" in xml


def test_page_size_over_api_limit_is_rejected():
    with pytest.raises(ValueError):
        build_request("Spending", [], (), max_records=20_001)


def test_parse_response_reads_rows_and_count():
    page = parse_response(response_xml([PAYMENT], total=1))
    assert page.total == 1
    assert page.rows[0]["contract_id"] == "CT126020261234567"


def test_api_failure_raises_with_its_message():
    with pytest.raises(CheckbookError, match="'year' value is not allowed"):
        parse_response(ERROR_XML)


def test_count_without_rows_is_an_error_not_an_empty_result():
    with pytest.raises(CheckbookError, match="counted 12293"):
        parse_response(response_xml([], total=12293))


def test_true_zero_and_page_past_the_end_are_empty():
    assert parse_response(response_xml([], total=0)).rows == []
    assert parse_response(response_xml([], total=5), records_from=1001).rows == []


def test_fetch_payments_parses_types():
    client, transport, _ = make_client((200, response_xml([PAYMENT])))
    [payment] = fetch_payments(client, fiscal_year=2026, contract_id="CT126020261234567")

    assert payment.amount == Decimal("95000.00")
    assert payment.issue_date == date(2026, 1, 20)
    assert "<name>contract_id</name>" in transport.bodies[0]


def test_fetch_payments_needs_a_bound():
    client, _, _ = make_client()
    with pytest.raises(ValueError):
        fetch_payments(client, payee_name="EXAMPLE YOUTH SERVICES INC")


def test_amounts_and_us_dates_are_normalized():
    row = dict(PAYMENT, check_amount="$1,250.5", issue_date="01/20/2026")
    client, _, _ = make_client((200, response_xml([row])))
    [payment] = fetch_payments(client, fiscal_year=2026)
    assert payment.amount == Decimal("1250.50")
    assert payment.issue_date == date(2026, 1, 20)


def test_search_pages_until_all_records_are_read():
    rows = [dict(PAYMENT, document_id=f"PV-{i}") for i in range(5)]
    client, transport, _ = make_client(
        (200, response_xml(rows[:2], total=5)),
        (200, response_xml(rows[2:4], total=5)),
        (200, response_xml(rows[4:], total=5)),
    )
    found = list(client.search("Spending", [], ("document_id",), page_size=2))

    assert [r["document_id"] for r in found] == [f"PV-{i}" for i in range(5)]
    assert "<records_from>5</records_from>" in transport.bodies[2]


def test_requests_are_spaced_at_least_1_1_seconds():
    client, _, clock = make_client((200, response_xml([])), (200, response_xml([])))
    client.post("<request/>")
    clock.now += 0.3  # the caller spent 0.3 s before the next request
    client.post("<request/>")
    assert clock.sleeps == [pytest.approx(0.8)]


def test_server_errors_are_retried_with_backoff():
    client, transport, clock = make_client((503, ""), (500, ""), (200, response_xml([])))
    client.post("<request/>")
    assert len(transport.bodies) == 3
    assert 5.0 in clock.sleeps and 10.0 in clock.sleeps


def test_client_errors_are_not_retried():
    client, transport, _ = make_client((403, "Forbidden"), (200, response_xml([])))
    with pytest.raises(CheckbookError, match="HTTP 403"):
        client.post("<request/>")
    assert len(transport.bodies) == 1


def test_gives_up_after_max_attempts():
    client, _, _ = make_client((503, ""), (503, ""), (503, ""))
    with pytest.raises(CheckbookError, match="failed 3 times"):
        client.post("<request/>")


def test_fetch_contracts_asks_for_registered_expense_contracts():
    row = {
        "prime_contract_id": "CT126020261234567",
        "prime_vendor": "EXAMPLE YOUTH SERVICES INC",
        "prime_contracting_agency": "Department of Youth and Community Development",
        "prime_contract_purpose": "AFTER SCHOOL PROGRAM",
        "prime_contract_current_amount": "1,200,000.00",
        "prime_contract_original_amount": "1,000,000.00",
        "prime_contract_start_date": "2025-07-01",
        "prime_contract_end_date": "",
    }
    client, transport, _ = make_client((200, response_xml([row])))
    [contract] = fetch_contracts(client, vendor_code="0000012345")

    assert contract.current_amount == Decimal("1200000.00")
    assert contract.start_date == date(2025, 7, 1)
    assert contract.end_date is None
    body = transport.bodies[0]
    assert "<value>registered</value>" in body and "<value>expense</value>" in body
    assert "<name>vendor_code</name>" in body


def test_fetch_contracts_needs_a_filter():
    client, _, _ = make_client()
    with pytest.raises(ValueError):
        fetch_contracts(client)
