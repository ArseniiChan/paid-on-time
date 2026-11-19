"""Answer the open questions in docs/checkbook-api.md against the live Checkbook NYC API.

Run from the backend folder, with a real contract ID from checkbooknyc.com (search a
DYCD-funded nonprofit there and copy one of its contract IDs):

    python -m scripts.checkbook_probe --contract-id CT1260XXXXXXXXXXX --payee-name "NAME"

It makes about six requests, spaced more than a second apart as the API requires, prints
what it found, and saves each raw XML response under tests/fixtures/checkbook/ so tests
can use real responses. Expect each request to take anywhere from a second to two minutes.
"""

import argparse
from datetime import date, timedelta
from pathlib import Path

from app.checkbook import (
    CONTRACT_COLUMNS,
    SPENDING_COLUMNS,
    CheckbookClient,
    CheckbookError,
    Criterion,
    build_request,
    parse_response,
)

FIXTURES = Path(__file__).resolve().parent.parent / "tests" / "fixtures" / "checkbook"
REGISTERED_EXPENSE = [
    Criterion("status", value="registered"),
    Criterion("category", value="expense"),
]


def run(client: CheckbookClient, label: str, domain: str, criteria, columns, size=100):
    print(f"\n== {label}")
    try:
        text = client.post(build_request(domain, criteria, columns, max_records=size))
    except CheckbookError as exc:
        print(f"   request failed: {exc}")
        return None
    FIXTURES.mkdir(parents=True, exist_ok=True)
    (FIXTURES / f"live_{label.replace(' ', '_')}.xml").write_text(text, encoding="utf-8")
    try:
        page = parse_response(text)
    except CheckbookError as exc:
        print(f"   API said: {exc}")
        return None
    print(f"   {page.total} matching records, {len(page.rows)} returned")
    for row in page.rows[:3]:
        print(f"   {row}")
    return page


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--contract-id", required=True)
    parser.add_argument("--payee-name", help="vendor name exactly as Checkbook shows it")
    args = parser.parse_args()
    client = CheckbookClient()
    contract = Criterion("contract_id", value=args.contract_id)

    # Q: what does a contract record contain? Does it have start and registration dates?
    run(client, "contract by id", "Contracts", REGISTERED_EXPENSE + [contract], CONTRACT_COLUMNS)

    # Q: which response columns exist? An invalid column makes the API list the valid ones.
    # Look for a vendor code and a registration date in the list it prints.
    run(client, "contract columns", "Contracts", REGISTERED_EXPENSE + [contract], ("no_such",))
    run(client, "spending columns", "Spending", [contract], ("no_such",))

    # Q: payments on this contract, and what format are dates and amounts in?
    since = Criterion("issue_date", start="2015-01-01", end=date.today().isoformat())
    run(client, "payments by contract", "Spending", [contract, since], SPENDING_COLUMNS)

    # Q: does payee_name filter citywide spending? Check that every payee printed matches.
    if args.payee_name:
        name = Criterion("payee_name", value=args.payee_name)
        run(client, "payments by payee name", "Spending", [name, since], SPENDING_COLUMNS)

    # Q: how fresh is the data, and is 260 DYCD's agency code? Look at the agency names and
    # the latest issue_date printed.
    recent = Criterion(
        "issue_date",
        start=(date.today() - timedelta(days=14)).isoformat(),
        end=date.today().isoformat(),
    )
    agency = Criterion("agency_code", value="260")
    page = run(client, "recent dycd payments", "Spending", [agency, recent], SPENDING_COLUMNS, 1000)
    if page and page.rows:
        print(f"   latest issue_date returned: {max(r.get('issue_date', '') for r in page.rows)}")

    print(f"\nRaw responses saved in {FIXTURES}")


if __name__ == "__main__":
    main()
