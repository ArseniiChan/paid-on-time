# User research: payment pain points for NYC-funded nonprofits

## What the professor is asking for

What we have now explains why **the government** pays late: reimbursement models,
contract registration, understaffed agencies, PASSPort. That is the system's side.

User research is the **nonprofit's** side: who deals with late payments, what they do each
week, where they lose time or money, how they cope today, and which of those problems our
tool would actually fix. Our persona (Maria Delgado) is made up. The research has to show
that real people like her exist and have the problems we gave her.

## 1. What the published evidence already says (secondary research)

Grouped by pain point, from the nonprofit's point of view.

### Pain 1: Money arrives months after the work starts

- In FY2024 over 90% of human services contracts were registered late, and nearly 40%
  were more than a year late. At 7 of 8 agencies, the first payment came more than 200
  days (about 6.5 months) after the contract started. DFTA, DOHMH, HPD, SBS and **DYCD**
  made first payments more than a year after the start date. ([NYC Comptroller, *Nonprofit,
  Nonpayment*](https://comptroller.nyc.gov/reports/nonprofit-nonpayment))
- FY2025 was a little better, but 8 in 10 human services contracts were still registered
  late, and over half were six months or more late. ([Comptroller annual contracts report
  2025](https://comptroller.nyc.gov/reports/annual-summary-contracts-report-for-the-city-of-new-york-2025/))
- 32% of NYC nonprofits with government funding were paid more than 90 days late, compared
  with 10% elsewhere in the US. Only 19% were paid on time (47% elsewhere).
  ([Nonprofit Finance Fund, 2025](https://nff.org/insights/survey-nyc-nonprofits-are-enduring-under-strain-of-funding-pullbacks-and-severe-government-payment-delays/))

### Pain 2: They borrow to make payroll, and the interest is never paid back

- In a Human Services Council survey, 90% of respondents were waiting on a combined $365M,
  nearly a third for more than six months. **48% used loans or lines of credit**, paying
  about **$6M in interest the city does not reimburse**.
  ([NYC Bar statement citing HSC](https://www.nycbar.org/reports/statement-urging-the-adams-administration-to-address-chronic-payment-delays-to-nonprofit-legal-services-providers/))
- Providers report taking on debt, considering layoffs and cutting services.
  ([THE CITY, Nov 2024](https://www.thecityreporter.nyc/2024/11/26/nonprofit-debt-layoffs-passport/),
  [Bronx Times](https://www.bxtimes.com/bronx-nonprofits-city-contracts/))
- Statewide: 62% of state-funded nonprofits saw payment delays and 25% used a credit line
  ([NY Council of Nonprofits, cited by the NY Senate](https://www.nysenate.gov/newsroom/in-the-news/2025/shelley-b-mayer/most-ny-nonprofits-have-funding-concerns-slow-state)).
  In Central NY, 43% spent down reserves and 29% borrowed
  ([CNY Community Foundation](https://cnycf.org/payment-pending-cny-nonprofit-funding-delays-from-the-state-level/)).

### Pain 3: Budget changes stop the money

- **85% of contracts** with an approved FY2025 budget were modified at least once. A
  budget change, even a small one for rent or payroll lines, can lock the vendor out of
  invoicing in PASSPort and "often completely stops the flow of money."
  ([Comptroller](https://comptroller.nyc.gov/wp-content/uploads/documents/Nonprofit-Nonpayment-3-1.pdf))
- Providers at a recent Council hearing named blocks during budget changes as a cash-flow
  risk for small providers.
  ([CitizenPortal summary](https://citizenportal.ai/articles/11631684/New-York/New-York-County/New-York-City/New-York-City-Council/Nonprofits-press-council-over-delayed-payments-and-clunky-Passport-workflows))

This is the strongest backing we have for the budget change check. MOCS's FY27 provider
guidance (p. 5) confirms that PASSPort blocks invoices whenever a budget modification is
pending, at any agency, not only DYCD.

### Pain 4: Staff time lost to PASSPort and paperwork

- One council member described a nonprofit spending about half a day of staff time on a
  single invoice (from a news summary of the hearing; confirm in the official transcript
  before quoting it).
- Providers report duplicate submissions and an interface that is still hard to use for
  many of them (same hearing).
- When budgets moved from the old system (HHS Accelerator) to PASSPort, errors made
  invoicing impossible, and most invoices were rejected and had to be re-entered by hand.
  ([Volunteers of America-Greater NY testimony, June 2024](https://voa-gny.org/wp-content/uploads/sites/20/2024/06/Testimony-on-Contracts-June-2024.pdf))
- Finance and executive staff spend time answering repeated requests for information and
  re-signing documents (HSC).

### Pain 5: They can't see what's happening

This one is mostly our assumption. Our journey map says statuses are vague and agency
replies are slow, and Yasmin found that Checkbook NYC has no invoice or budget-change
status. **We have no direct quote from a nonprofit saying this yet.** Arsenii also found
that PASSPort's Detailed Invoice Report already lists each invoice's status and cycle time,
so a status tracker on its own repeats something providers have. It is low priority.

### Open question: why invoices get sent back

Professor Sessa framed our core product as an invoice validator that checks an invoice
against the contract before it is submitted. We know invoices get rejected (see the VOA-GNY
testimony above), but we found no published breakdown of the reasons. This is the most
important thing to learn in interviews.

## 2. What we still don't know (gaps)

Each feature rests on an assumption we haven't checked with a real user:

| Feature | Assumption | How we check it |
|---|---|---|
| CSV upload (Nick) | Finance staff can and will export CSVs from PASSPort | Ask them to show us an export, or describe how they do it |
| Freeze check (Diana) | People don't know a budget change freezes invoicing, or forget to time it | Ask about the last budget change: did they know? What happened? |
| Invoice validator (Arsenii) | Invoices get rejected for fixable reasons (missing documents, wrong line, over budget) | Ask about the last rejected invoice and the reason given. Top question. |
| 90-day forecast | They forecast cash in Excel today, and it's painful | Ask to see the spreadsheet (or describe it): how long does it take, how often? |
| Interest view | They know what the credit line costs them | Ask what they paid in interest last year |
| Who uses it | The user is a finance director at a 20–100 person nonprofit | Ask about job titles, team size, who touches PASSPort |

Also unknown: which agencies are worst for them (it may not be DYCD), what they've already
tried (spreadsheets, consultants, MOCS help desk, Returnable Grant Fund loans), and whether
they would trust a tool with their contract data.

## 3. What to do more of: a plan for real user research

### A. Interviews (most important): 5–8 people, 30 minutes each

**Who:** finance directors, controllers, bookkeepers or executive directors at nonprofits
with city contracts (DYCD, DHS, DFTA, DOHMH). Also try one person on the agency side, or a
MOCS or Mayor's Office of Nonprofit Services staffer.

**Where to find them:**
- CCNY and CUNY connections: professors, career services, alumni at nonprofits, and the
  Colin Powell School (community-engaged programs).
- Nonprofits you already know: after-school programs, youth centers, food pantries.
- Human Services Council, Nonprofit New York, and the NY Council of Nonprofits (ask whether
  they'll share a short request in a newsletter).
- LinkedIn search: "Finance Director" plus "DYCD" or "human services" in NYC.
- Find contract holders in Checkbook NYC and email their finance staff directly.

**Interview guide (ask about stories, not opinions):**
1. What's your role, and who else handles city contracts and invoices?
2. Walk me through the last time you submitted an invoice in PASSPort. How long did it take?
3. Tell me about the last payment that was late. How did you find out? What did you do?
4. Have you ever had to borrow or use a credit line to cover a late payment? Roughly how much,
   and what did it cost?
5. Tell me about your last budget change. Did it affect invoicing? Did you know it would?
6. Has an invoice been sent back? Why? How long did the fix take? What does your contract
   require on an invoice (documents, budget lines)? Could you share a redacted contract and
   invoice we can test with?
7. How do you track what the city owes you today? (Ask to see it, with numbers hidden.)
8. How do you forecast cash for the next few months? Who sees that forecast?
9. If you could fix one thing about getting paid, what would it be?
10. [Show the Figma freeze warning] What would you do with this? What's confusing?

Rules: don't pitch the tool until the last question, ask "tell me about the last time…"
instead of "would you use…", and record (with permission) or take notes word for word.

### B. Mine public testimony (doable this week, no recruiting)

City Council Committee on Contracts hearings have written testimony from dozens of
nonprofits on Legistar. Pull 15–20 testimonies, tag each pain point (late payment,
borrowing, budget change freeze, PASSPort, rejections, lack of visibility), and count them.
This gives real quotes from real nonprofits for the proposal.
Start here: [Legistar Committee on Contracts transcript](https://legistar.council.nyc.gov/View.ashx?GUID=8874D928-8744-44BE-8736-6A3394105D7A&ID=15431519&M=F).

### C. Short survey (optional, after interviews)

5–8 questions in Google Forms, shared through the same channels: agencies, days late,
borrowing (yes/no, cost), budget changes per year, freeze experience, how they forecast
cash today. Use the interviews to write the answer choices.

### D. Write it up for the proposal

- **Affinity map:** sticky notes of quotes grouped into themes (FigJam works).
- **Updated persona:** keep Maria but base her on real interview data, and note which
  details come from which interviews.
- **Updated journey map:** replace assumed pain points with ones people actually told us about.
- **Assumption table** (like the one above) with each one marked confirmed, disproved or
  unclear, and what changed in the design because of it.

## 4. Timeline against the course schedule

| Date | Research milestone |
|---|---|
| 11/17 (today) | WPR: say we're starting user research; describe the plan and the secondary evidence above |
| by 11/19 meeting | Testimony analysis done; interview outreach sent; 1–2 interviews booked |
| 11/19–11/25 | Run interviews (split them: 2 each) |
| 11/26 | First draft proposal: research section with secondary evidence, testimony counts and first interviews |
| 12/1 | WPR: findings and design changes |
| 12/3 dry run | One slide of real quotes and numbers, and one slide on what we changed because of them |
| 12/15 | Final proposal: updated persona, journey map and assumption table |

## 5. Fixes to our existing text

- Replace "Most users on Reddit agree…" with a cited source (Comptroller, HSC, NFF).
  Reddit can be a starting lead, not evidence.
- Add a source for the "$861 million / about 4,000 invoices in April 2025" figure in the
  weekly summary.
- The *Nonprofit, Nonpayment* report is from 2024. Pair it with the FY2025 Comptroller
  report so we don't look out of date.
