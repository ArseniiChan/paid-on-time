from datetime import date
from decimal import Decimal

from sqlalchemy import create_engine, select
from sqlalchemy.orm import Session

from app.db import Base
from app.models import Agency, Contract, Invoice, Organization, Payment


def test_contract_invoice_payment_round_trip():
    engine = create_engine("sqlite://")
    Base.metadata.create_all(engine)

    with Session(engine) as session:
        org = Organization(name="Example Youth Services", ein="12-3456789")
        dycd = Agency(name="DYCD", freezes_on_budget_mod=True)
        contract = Contract(
            organization=org,
            agency=dycd,
            contract_number="CT1-260-20261234567",
            total_amount=Decimal("1200000.00"),
        )
        invoice = Invoice(
            contract=contract,
            amount=Decimal("95000.00"),
            status="submitted",
            submitted_date=date(2026, 7, 15),
        )
        Payment(
            contract=contract,
            invoice=invoice,
            amount=Decimal("95000.00"),
            paid_date=date(2026, 11, 2),
        )
        session.add(org)
        session.commit()

        saved = session.scalars(select(Contract)).one()
        assert saved.organization.name == "Example Youth Services"
        assert saved.agency.freezes_on_budget_mod is True
        assert saved.invoices[0].payments[0].amount == Decimal("95000.00")
