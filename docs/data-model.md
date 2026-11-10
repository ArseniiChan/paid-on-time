# Data model

The schema lives in `backend/app/models.py`. Keep this page and that file in sync.

```mermaid
erDiagram
    ORGANIZATION ||--o{ CONTRACT : holds
    ORGANIZATION ||--o{ FORECAST : has
    AGENCY ||--o{ CONTRACT : funds
    AGENCY ||--o{ RULE : sets
    CONTRACT ||--o{ INVOICE : billed_by
    CONTRACT ||--o{ PAYMENT : paid_by
    CONTRACT ||--o{ BUDGET_MODIFICATION : changed_by
    INVOICE ||--o{ PAYMENT : settled_by
    INVOICE ||--o{ ALERT : flagged_by
    RULE ||--o{ ALERT : triggers

    ORGANIZATION {
        int id PK
        string name
        string ein
    }
    AGENCY {
        int id PK
        string name
        bool freezes_on_budget_mod
    }
    CONTRACT {
        int id PK
        int org_id FK
        int agency_id FK
        string contract_number
        decimal total_amount
    }
    INVOICE {
        int id PK
        int contract_id FK
        decimal amount
        string status
        date submitted_date
    }
    PAYMENT {
        int id PK
        int contract_id FK
        int invoice_id FK
        decimal amount
        date paid_date
    }
    BUDGET_MODIFICATION {
        int id PK
        int contract_id FK
        decimal amount
        string status
        date submitted_date
    }
    RULE {
        int id PK
        int agency_id FK
        string description
        string citation
    }
    ALERT {
        int id PK
        int rule_id FK
        int invoice_id FK
        string message
    }
    FORECAST {
        int id PK
        int org_id FK
        date week_start
        decimal ending_cash
        decimal interest
    }
```

Original diagram:

![ER diagram](images/er-diagram.png)

## Notes

- Money is stored as `NUMERIC(14, 2)`, never floats, so cents don't drift.
- `payment.invoice_id` is optional so a payment can be stored before it's matched to an
  invoice.
- `agency.freezes_on_budget_mod` drives the freeze warning in `app/rules.py`.
