"""Client for the Checkbook NYC API (FR1: data ingestion).

Pulls an organization's contracts and payments from the city's public spending data. See
docs/checkbook-api.md for how the API behaves and why this module is built the way it is.
In short:

- One endpoint, XML in and XML out, no API key.
- At most one request per second and one connection per IP. Going faster can get the
  IP blocked, so every request (retries included) waits until 1.1 seconds have passed
  since the last one.
- Requests can take up to two minutes and fail with 500/503 when the server times out.
  Those are retried with backoff. A 4xx is never retried: it means our request is wrong.
- A response can say "success", count N matching records, and still return no rows. That
  is treated as an error, never as "nothing found".

Uses only the standard library, so it adds no dependency. Network access goes through a
`transport` function that tests replace with canned responses.
"""

import time
import urllib.error
import urllib.request
import xml.etree.ElementTree as ET
from collections.abc import Callable, Iterator
from dataclasses import dataclass
from datetime import date, datetime
from decimal import Decimal, InvalidOperation
from xml.sax.saxutils import escape

API_URL = "https://www.checkbooknyc.com/api"
USER_AGENT = "paid-on-time (CCNY senior design; github.com/ArseniiChan/paid-on-time)"

# The API accepts up to 20,000 records per call. Smaller pages finish faster, which
# matters when a single request can take two minutes.
MAX_PAGE_SIZE = 20_000
DEFAULT_PAGE_SIZE = 1_000
MIN_REQUEST_INTERVAL = 1.1  # seconds; the limit is 1/second, plus headroom for clock skew
REQUEST_TIMEOUT = 150  # seconds; the server gives up at 120

# Response columns we ask for. One invalid name fails the whole request, and valid names
# differ by domain (see docs/checkbook-api.md), so these are fixed lists, not user input.
SPENDING_COLUMNS = (
    "agency",
    "payee_name",
    "contract_id",
    "check_amount",
    "issue_date",
    "document_id",
    "expense_category",
)
# Registered expense contracts, the kind human services providers hold.
CONTRACT_COLUMNS = (
    "prime_contract_id",
    "prime_vendor",
    "prime_contract_purpose",
    "prime_contracting_agency",
    "prime_contract_current_amount",
    "prime_contract_original_amount",
    "prime_contract_start_date",
    "prime_contract_end_date",
)

DATE_FORMATS = ("%Y-%m-%d", "%m/%d/%Y", "%Y-%m-%dT%H:%M:%S")

# (body to send) -> (HTTP status, response text)
Transport = Callable[[bytes], tuple[int, str]]


class CheckbookError(Exception):
    """Any failure talking to Checkbook NYC. Never returned as an empty result."""


@dataclass(frozen=True)
class Criterion:
    """One search filter: an exact value, or a range from `start` to `end`."""

    name: str
    value: str | None = None
    start: str | None = None
    end: str | None = None

    def to_xml(self) -> str:
        if self.value is not None:
            return (
                f"<criteria><name>{self.name}</name><type>value</type>"
                f"<value>{escape(self.value)}</value></criteria>"
            )
        return (
            f"<criteria><name>{self.name}</name><type>range</type>"
            f"<start>{escape(self.start or '')}</start><end>{escape(self.end or '')}</end>"
            "</criteria>"
        )


@dataclass(frozen=True)
class Page:
    total: int  # matching records across all pages
    rows: list[dict[str, str]]


@dataclass(frozen=True)
class CheckbookPayment:
    contract_id: str
    payee_name: str
    agency: str
    amount: Decimal
    issue_date: date
    document_id: str


@dataclass(frozen=True)
class CheckbookContract:
    contract_id: str
    vendor: str
    agency: str
    purpose: str
    current_amount: Decimal
    original_amount: Decimal
    start_date: date | None
    end_date: date | None


def build_request(
    domain: str,
    criteria: list[Criterion],
    columns: tuple[str, ...],
    records_from: int = 1,
    max_records: int = DEFAULT_PAGE_SIZE,
) -> str:
    if not 1 <= max_records <= MAX_PAGE_SIZE:
        raise ValueError(f"max_records must be between 1 and {MAX_PAGE_SIZE}")
    criteria_xml = "".join(c.to_xml() for c in criteria)
    columns_xml = "".join(f"<column>{c}</column>" for c in columns)
    return (
        f"<request><type_of_data>{domain}</type_of_data>"
        f"<records_from>{records_from}</records_from><max_records>{max_records}</max_records>"
        + (f"<search_criteria>{criteria_xml}</search_criteria>" if criteria else "")
        + (f"<response_columns>{columns_xml}</response_columns>" if columns else "")
        + "</request>"
    )


def parse_response(xml_text: str, records_from: int = 1) -> Page:
    """Read one page of results, or raise CheckbookError if the API reported a failure."""
    try:
        root = ET.fromstring(xml_text)
    except ET.ParseError as exc:
        raise CheckbookError(f"Response is not valid XML: {exc}") from exc

    result = root.findtext("status/result", default="").strip()
    if result != "success":
        messages = [(m.findtext("description") or "").strip() for m in root.iter("message")]
        detail = "; ".join(m for m in messages if m) or f"status was {result or 'missing'!r}"
        raise CheckbookError(f"Checkbook NYC reported a failure: {detail}")

    records = root.find("result_records")
    if records is None:
        return Page(total=0, rows=[])
    total = int(records.findtext("record_count", default="0") or 0)
    rows = [
        {child.tag: (child.text or "").strip() for child in txn}
        for txn in records.iter("transaction")
    ]

    if not rows and total > 0 and records_from <= total:
        raise CheckbookError(
            f"Checkbook NYC counted {total} matching records but returned none for "
            f"records_from={records_from}. This is a known API defect, not an empty result."
        )
    return Page(total=total, rows=rows)


def urllib_transport(body: bytes) -> tuple[int, str]:
    request = urllib.request.Request(
        API_URL,
        data=body,
        method="POST",
        headers={"Content-Type": "application/xml", "User-Agent": USER_AGENT},
    )
    try:
        with urllib.request.urlopen(request, timeout=REQUEST_TIMEOUT) as response:
            return response.status, response.read().decode("utf-8", errors="replace")
    except urllib.error.HTTPError as exc:
        return exc.code, exc.read().decode("utf-8", errors="replace")


class CheckbookClient:
    """Sends requests one at a time, paced and retried. Not safe to share across threads."""

    def __init__(
        self,
        transport: Transport = urllib_transport,
        sleep: Callable[[float], None] = time.sleep,
        clock: Callable[[], float] = time.monotonic,
        max_attempts: int = 3,
        backoff: float = 5.0,
    ):
        self._transport = transport
        self._sleep = sleep
        self._clock = clock
        self._max_attempts = max_attempts
        self._backoff = backoff
        self._last_request: float | None = None

    def _pace(self) -> None:
        if self._last_request is not None:
            wait = self._last_request + MIN_REQUEST_INTERVAL - self._clock()
            if wait > 0:
                self._sleep(wait)
        self._last_request = self._clock()

    def post(self, body: str) -> str:
        """Send one request. Retries network errors and 5xx; raises on anything else."""
        last_problem = ""
        for attempt in range(1, self._max_attempts + 1):
            self._pace()
            try:
                status, text = self._transport(body.encode("utf-8"))
            except (urllib.error.URLError, TimeoutError, OSError) as exc:
                last_problem = f"network error: {exc}"
            else:
                if 200 <= status < 300:
                    return text
                if status < 500:
                    raise CheckbookError(
                        f"HTTP {status} from Checkbook NYC. A 403 can mean this IP is being "
                        "rate limited; wait before trying again."
                    )
                last_problem = f"HTTP {status}"
            if attempt < self._max_attempts:
                self._sleep(self._backoff * 2 ** (attempt - 1))
        raise CheckbookError(
            f"Checkbook NYC failed {self._max_attempts} times; last: {last_problem}"
        )

    def search(
        self,
        domain: str,
        criteria: list[Criterion],
        columns: tuple[str, ...],
        page_size: int = DEFAULT_PAGE_SIZE,
    ) -> Iterator[dict[str, str]]:
        """Yield every matching row, fetching one page at a time."""
        records_from = 1
        while True:
            body = build_request(domain, criteria, columns, records_from, page_size)
            page = parse_response(self.post(body), records_from)
            yield from page.rows
            records_from += page_size
            if not page.rows or records_from > page.total:
                return


def _date(text: str) -> date | None:
    text = text.strip()
    if not text:
        return None
    for fmt in DATE_FORMATS:
        try:
            return datetime.strptime(text, fmt).date()
        except ValueError:
            pass
    raise CheckbookError(f"Unrecognized date from Checkbook NYC: {text!r}")


def _money(text: str) -> Decimal:
    cleaned = text.replace("$", "").replace(",", "").strip() or "0"
    try:
        return Decimal(cleaned).quantize(Decimal("0.01"))
    except InvalidOperation as exc:
        raise CheckbookError(f"Unrecognized amount from Checkbook NYC: {text!r}") from exc


def fetch_payments(
    client: CheckbookClient,
    *,
    fiscal_year: int | None = None,
    issued_from: date | None = None,
    issued_to: date | None = None,
    contract_id: str | None = None,
    payee_name: str | None = None,
    agency_code: str | None = None,
) -> list[CheckbookPayment]:
    """Checks and EFTs the city issued. Needs a fiscal year or a start date to bound it."""
    if fiscal_year is None and issued_from is None:
        raise ValueError("Pass fiscal_year or issued_from; an unbounded search is too large.")
    criteria = [
        Criterion(name, value=value)
        for name, value in (
            ("fiscal_year", None if fiscal_year is None else str(fiscal_year)),
            ("contract_id", contract_id),
            ("payee_name", payee_name),
            ("agency_code", agency_code),
        )
        if value
    ]
    if issued_from is not None:
        end = (issued_to or date(2099, 12, 31)).isoformat()
        criteria.append(Criterion("issue_date", start=issued_from.isoformat(), end=end))

    payments = []
    for row in client.search("Spending", criteria, SPENDING_COLUMNS):
        issued = _date(row.get("issue_date", ""))
        if issued is None:
            raise CheckbookError(f"Payment {row.get('document_id', '?')} has no issue date")
        payments.append(
            CheckbookPayment(
                contract_id=row.get("contract_id", ""),
                payee_name=row.get("payee_name", ""),
                agency=row.get("agency", ""),
                amount=_money(row.get("check_amount", "")),
                issue_date=issued,
                document_id=row.get("document_id", ""),
            )
        )
    return payments


def fetch_contracts(
    client: CheckbookClient,
    *,
    vendor_code: str | None = None,
    contract_id: str | None = None,
    agency_code: str | None = None,
) -> list[CheckbookContract]:
    """Registered expense contracts. There is no vendor name or EIN filter in this API."""
    filters = {"vendor_code": vendor_code, "contract_id": contract_id, "agency_code": agency_code}
    if not any(filters.values()):
        raise ValueError("Pass vendor_code, contract_id or agency_code.")
    criteria = [Criterion("status", value="registered"), Criterion("category", value="expense")]
    criteria += [Criterion(name, value=value) for name, value in filters.items() if value]

    return [
        CheckbookContract(
            contract_id=row.get("prime_contract_id", ""),
            vendor=row.get("prime_vendor", ""),
            agency=row.get("prime_contracting_agency", ""),
            purpose=row.get("prime_contract_purpose", ""),
            current_amount=_money(row.get("prime_contract_current_amount", "")),
            original_amount=_money(row.get("prime_contract_original_amount", "")),
            start_date=_date(row.get("prime_contract_start_date", "")),
            end_date=_date(row.get("prime_contract_end_date", "")),
        )
        for row in client.search("Contracts", criteria, CONTRACT_COLUMNS)
    ]
