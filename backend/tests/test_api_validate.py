from fastapi.testclient import TestClient

from app.main import app

# Made-up contract and invoice. Not real data.
CONTRACT = {
    "contract_number": "CT1-260-20261234567",
    "term_start": "2026-07-01",
    "term_end": "2027-06-30",
    "budget_lines": {"Personnel": "120000.00", "Supplies": "8000.00"},
    "invoice_window_days": 30,
    "window_source": "DOHMH Fiscal Manual for Human Services, s. 4.6",
    "required_documents": ["timesheets"],
}
INVOICE = {
    "contract_number": "CT1-260-20261234567",
    "period_start": "2026-10-01",
    "period_end": "2026-10-31",
    "lines": {"Personnel": "10000.00", "Supplies": "500.00"},
    "attached_documents": ["timesheets"],
}


def post(body):
    with TestClient(app) as client:
        return client.post("/invoices/validate", json=body)


def test_clean_invoice():
    response = post({"contract": CONTRACT, "invoice": INVOICE, "submit_on": "2026-11-17"})
    assert response.status_code == 200
    assert response.json() == {"ok": True, "issues": []}


def test_problems_come_back_with_codes_and_sources():
    invoice = {**INVOICE, "attached_documents": []}
    response = post(
        {
            "contract": CONTRACT,
            "invoice": invoice,
            "budget_change_pending": True,
            "submit_on": "2026-11-17",
        }
    )
    body = response.json()
    assert response.status_code == 200
    assert body["ok"] is False
    assert {issue["code"] for issue in body["issues"]} == {
        "missing_documents",
        "budget_change_pending",
    }
    pending = next(i for i in body["issues"] if i["code"] == "budget_change_pending")
    assert "MOCS" in pending["source"]


def test_bad_input_is_rejected():
    response = post({"contract": CONTRACT, "invoice": {**INVOICE, "period_start": "not a date"}})
    assert response.status_code == 422
