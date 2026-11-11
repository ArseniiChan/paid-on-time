# Checkbook NYC API: research notes

Answers the open questions about Checkbook NYC in `docs/requirements.md` (FR1) and
`docs/architecture.md`. Everything here comes from the published docs and from people who
have used the API; nothing has been tested against the live API yet. Items marked
**To verify** are next on the list.

## How the API works

| | |
|---|---|
| Endpoint | `POST https://www.checkbooknyc.com/api` |
| Format | XML request body, XML response. No JSON. |
| Auth | None. No API key. |
| Domains | `type_of_data`: Spending, Contracts, Budget, Payroll, Revenue (plus `_OGE` / `_NYCHA` variants for other government entities) |
| Paging | `records_from` (start row) and `max_records` |
| Records per call | The general page says up to 20,000 by default; the Spending page says `max_records` must be under 1,000. **To verify.** Plan for 1,000. |
| Rate limit | 1 request per second, 1 concurrent session per IP. Going over can return HTTP 403 or a connection reset, and the block can persist. |
| Response time | Up to about 2 minutes per request. Server timeout is 120 seconds. |
| Errors | Intermittent HTTP 500/503, and HTTP 200 bodies containing a database timeout message. Retry later; the Checkbook team suggests running jobs 5–8 pm Eastern. |

Example request (Spending, one agency, one fiscal year):

```xml
<request>
  <type_of_data>Spending</type_of_data>
  <records_from>1</records_from>
  <max_records>1000</max_records>
  <search_criteria>
    <criteria><name>fiscal_year</name><type>value</type><value>2026</value></criteria>
    <criteria><name>agency_code</name><type>value</type><value>260</value></criteria>
  </search_criteria>
  <response_columns>
    <column>contract_id</column>
    <column>payee_name</column>
    <column>check_amount</column>
    <column>issue_date</column>
  </response_columns>
</request>
```

`260` should be DYCD's agency code (it also appears in the contract numbers in our test
fixtures). **To verify.**

## Answers to our open questions

**Can we look up an organization by EIN?** No. Neither the Spending nor the Contracts API
has an EIN or tax ID filter, and none of the community tools offer one. FR1 and the
architecture doc both say "by vendor name or EIN"; that needs to change.

**Can we look it up by name?** Not reliably.
- Contracts: filter by `vendor_code` only. BetaNYC's client notes there is no
  name-to-code lookup in the API.
- Spending (citywide): the official docs list `payee_code` (vendor code) as the citywide
  filter and `payee_name` as NYCEDC-only, matching on the first three letters. BetaNYC's
  client does send `payee_name` for citywide spending. **To verify** which is right.
- One project that used the Contracts API matched vendors by normalized name and found
  truncated and duplicate vendor names in the city's records.

**So how does a user identify their organization?** Most likely: the user enters one of
their contract IDs (they see these in PASSPort), we fetch that contract, read the vendor
code from it, then pull all contracts and payments by vendor code. Contract ID is a
supported filter in both domains. **To verify** that the contract response includes the
vendor code.

**What do we get for payments?** Each spending row is a check or EFT with `contract_id`,
`payee_name`, `check_amount`, `issue_date`, `agency`, `expense_category` and sub-vendor
fields. This maps onto our `Payment` model (`contract_id`, `amount`, `paid_date`).

**Can we see invoice status or budget modification status?** No. Checkbook has issued
payments and registered contracts, not invoices or budget change requests. That data
still has to come from PASSPort exports (Nick's parser), as the architecture doc already
assumes.

**Can we measure payment lag?** Not from Checkbook alone. Checkbook has the date a payment
was issued but not the date the invoice was submitted. To get invoice-to-payment lag we
have to join Checkbook payments to PASSPort invoices by contract ID. What Checkbook *can*
show on its own is how late contracts are registered: comparing a contract's start date
with its registration date. **To verify** that both fields come back for expense
contracts.

**How fresh is the data?** Not documented. **To verify** by checking the most recent
`issue_date` returned for a busy agency.

## Design implications

- One background job, one request at a time, at least 1.1 seconds apart, with retries and
  backoff. Never call Checkbook from a user's page load; cache results in our database.
- Page with `records_from` in chunks of 1,000.
- Ask for an explicit `response_columns` list. One invalid column name fails the whole
  request, and valid columns differ between expense and revenue contracts.
- Use Python's standard XML parser (`xml.etree.ElementTree`) or `defusedxml`; no extra
  service needed.
- Store `contract_id` exactly as Checkbook returns it so PASSPort rows can join on it.

## Still to verify (next week)

1. Make a real Spending request for one DYCD-funded nonprofit and save the XML as a test
   fixture.
2. Confirm the records-per-call limit (1,000 vs 20,000).
3. Confirm whether `payee_name` works for citywide spending.
4. Read the Contracts API page (it would not load during this research) and confirm the
   filters and response columns, especially vendor code, start date and registration date.
5. Check data freshness.

## Sources

- [Checkbook NYC API: general information](https://www.checkbooknyc.com/api-page)
- [Checkbook NYC Spending API](https://www.checkbooknyc.com/node/304)
- [Checkbook NYC Google Group: querying issues and best practices](https://groups.google.com/g/checkbooknyc/c/hgU1niDG00Y) (official reply on rate limits, Jan 2024)
- [BetaNYC nyc-checkbook-mcp](https://github.com/BetaNYC/nyc-checkbook-mcp) and [issue #42](https://github.com/BetaNYC/nyc-checkbook-mcp/issues/42)
- [nyc-vendor-ledger methodology](https://github.com/joshgreenman1973/nyc-vendor-ledger/blob/main/METHODOLOGY.md)
