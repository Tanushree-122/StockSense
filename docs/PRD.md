# StockSense: Product Requirements Document (PRD)

| | |
|---|---|
| **Product** | StockSense, an intelligent inventory and restocking assistant for small retail stores |
| **Version** | 1.0 (approved on Day 1 of the 10-day capstone) |
| **Owner** | Capstone participant, AB Talks 60-Day Claude AI Challenge |
| **Status** | Approved. Source of truth together with `IMPLEMENTATION-BLUEPRINT.md` |
| **Build window** | 10 days, 2 to 3 hours per day (about 20 to 30 hours total) |

---

## 1. Product Overview

StockSense is a responsive web app that helps a small or medium retail store owner answer three questions every day: **What do I have? What is selling? What should I buy next?**

The owner logs in, manages products, records multi-item sales as mini bills, tracks every stock movement, and gets low-stock alerts in the app and by email. A dashboard shows revenue and profit trends and classifies products as fast, steady, or slow movers. A recommendation engine then tells the owner what to reorder, how much, and why, in plain English. A small ML demand-forecast model is a scoped stretch layer on top of the rules.

**Vision:** make data-driven restocking accessible to every small retailer, without spreadsheets, guesswork, or expensive enterprise software.

## 2. Problem Statement

Small retailers typically run inventory from memory, notebooks, or spreadsheets. This causes:

1. **Stock-outs:** popular items run out unnoticed, so sales are lost.
2. **Dead stock:** money is locked in slow-moving products nobody reviews.
3. **Gut-feel restocking:** order quantities are guessed, not calculated from sales speed and supplier lead time.
4. **No profit visibility:** the owner knows turnover but not which products actually make money.
5. **Existing tools are too heavy or too costly:** enterprise inventory systems are complex, and most small shops will not adopt them.

## 3. Target Users

**Primary user: the store owner or manager** of a small or medium general retail shop (grocery, personal care, stationery, small electronics).

**Persona, Ravi Sharma (42), owner of a neighbourhood general store**
- About 60 to 300 products, 1 to 3 staff, buys from 5 to 8 suppliers.
- Uses a notebook and his memory. Discovers stock-outs when customers ask.
- Comfortable with a smartphone and basic web apps. Not technical.
- Wants: "Tell me what to order today and why, in simple words."

**Usage context:** on a laptop at the counter for data entry and review, and on a phone on the shop floor for quick checks.

## 4. Goals and Non-Goals

### Goals (v1.0)
- G1. Maintain an accurate, auditable stock count for every product.
- G2. Make sale entry fast (a 5-item bill in under 60 seconds).
- G3. Warn the owner before and when products run out (in-app and email).
- G4. Show revenue, profit, and product performance clearly.
- G5. Give explainable restocking advice.
- G6. Ship a polished, deployed, responsive product that feels production-ready.

### Non-Goals (intentionally excluded from v1.0)
Expiry dates, batch tracking, size/color variants, multiple users or roles, multiple stores, barcode scanning, discounts, taxes/GST, payment methods, customer records, editing past sales (voiding only), scheduled emails, a native mobile app, purchase orders sent to suppliers, fractional quantities (kg/litres), and full ML-driven recommendations.

## 5. Success Metrics (Day 10)

| # | Metric | Target |
|---|---|---|
| M1 | A reviewer opens the live link, logs in with demo credentials, and completes the full flow (add product, record sale, see alert, read recommendation) | Works without help |
| M2 | Time to record a 5-item sale | Under 60 seconds |
| M3 | Stock integrity: every product's `current_stock` equals the sum of its ledger movements | 100% (verified by a CLI check) |
| M4 | All **Must** user stories pass their acceptance criteria | 100% |
| M5 | Automated tests for services (stock, sales, alerts, analytics, recommendations) | 40+ passing tests |
| M6 | Responsive layout verified at 375px, 768px, and 1280px widths | No horizontal scroll, all actions usable |
| M7 | Warm page load on the deployed app | Under 3 seconds |
| M8 | Reviewer reaction | "This could genuinely help a small retail business make better inventory decisions." |

## 6. Scope Summary

| Area | In v1.0 | Priority |
|---|---|---|
| Access | Single-owner login and logout (no public sign-up) | Must |
| Catalog | Products, categories, suppliers, archive/restore | Must |
| Stock | Stock-in, adjustments, full movement history (ledger) | Must |
| Sales | Multi-item mini bills, sales history, detail, void | Must |
| Data loading | Demo data CLI, products CSV import | Must / Should |
| Data loading | Sales CSV import | Should |
| Alerts | In-app low and out-of-stock alerts | Must |
| Alerts | Email alert on new alert, "send summary now" button | Should |
| Analytics | Dashboard KPIs, revenue/profit trend, top products, inventory value | Must |
| Insights | Fast/steady/slow classification, dead-stock highlight | Must / Should |
| Recommendations | Rule-based, explained reorder advice | Must |
| Recommendations | Supplier grouping and copyable order list | Should |
| Recommendations | ML demand forecast (stretch, rules as fallback) | Could |
| Platform | Responsive UI, deployed live, friendly errors and empty states | Must |

## 7. User Stories and Acceptance Criteria

Priority uses MoSCoW: **M**ust, **S**hould, **C**ould. Story IDs are referenced by the schema, API, and wireframe documents.

### Epic A: Access
| ID | Pri | Story | Acceptance criteria |
|---|---|---|---|
| US-01 | M | As the owner, I want to log in with email and password so only I can see my store data. | Wrong credentials show a clear error. Every page except login and health check redirects to login when signed out. Passwords are stored hashed. |
| US-02 | M | As the owner, I want to log out so my data is safe on shared devices. | Logout ends the session and returns to login. |

### Epic B: Catalog
| ID | Pri | Story | Acceptance criteria |
|---|---|---|---|
| US-03 | M | As the owner, I want to add a product (name, SKU, category, supplier, cost price, selling price, opening stock, minimum stock level). | SKU is unique. Prices are 0 or more. Quantities are whole numbers 0 or more. A warning shows if selling price is below cost. Opening stock above 0 creates an OPENING ledger entry. |
| US-04 | M | As the owner, I want to edit a product's details. | SKU cannot change after creation. Stock cannot be edited here (only via stock-in, adjustment, or sales). |
| US-05 | M | As the owner, I want to search, filter, and sort my products. | Search by name or SKU. Filter by category, supplier, stock status (OK / Low / Out), and active/archived. Paginated. Status badges are colored. |
| US-06 | S | As the owner, I want to archive a product I no longer sell. | Archived products are hidden from sale search, alerts, and recommendations, and can be restored. Products with history are never hard-deleted. |
| US-07 | M | As the owner, I want to manage categories. | Add, rename, delete (delete blocked if products use it). Names unique. |
| US-08 | M | As the owner, I want to manage suppliers, including how many days they take to deliver. | Name unique. Optional phone and email. Lead time in days (default 3). |

### Epic C: Stock
| ID | Pri | Story | Acceptance criteria |
|---|---|---|---|
| US-09 | M | As the owner, I want to record stock received from a supplier. | Quantity above 0. Optional note. Ledger entry STOCK_IN. If this lifts stock above the minimum level, the open alert resolves. |
| US-10 | M | As the owner, I want to correct stock for damage, loss, or count errors. | Reason is required (Damaged, Lost/Theft, Count correction, Returned to supplier, Other). Positive or negative change. Stock can never go below 0. |
| US-11 | M | As the owner, I want to see every stock movement for a product. | History shows date, type, change, stock after, reason or note, linked bill. Newest first, paginated. |

### Epic D: Sales
| ID | Pri | Story | Acceptance criteria |
|---|---|---|---|
| US-12 | M | As the owner, I want to record a sale with several products on one bill. | Search products by name or SKU. Add or remove line items. Live total. Price is the product's selling price at that moment (stored as a snapshot). Saving creates a bill number and one SALE ledger entry per line. |
| US-13 | M | As the owner, I want the app to stop me from selling more than I have. | If any line exceeds stock, nothing is saved and the message names the product and available quantity. |
| US-14 | M | As the owner, I want to browse past sales. | Filter by date range and status (completed or voided). Shows bill number, date, items count, total. Paginated. |
| US-15 | M | As the owner, I want to open a sale and see its items, revenue, cost, and profit. | Uses the price and cost snapshots from the time of sale. |
| US-16 | M | As the owner, I want to void a sale made by mistake. | Reason required. Stock is restored through SALE_VOID ledger entries. The sale is marked VOIDED and excluded from all analytics. Voiding twice is blocked. |

### Epic E: Data loading
| ID | Pri | Story | Acceptance criteria |
|---|---|---|---|
| US-17 | S | As the owner, I want to import products from a CSV file. | A template can be downloaded. The whole file is validated first. If any row is invalid, nothing is imported and a table lists row, column, and error. Limit 2,000 rows and 1 MB. |
| US-18 | S | As the owner, I want to import past sales from a CSV file. | Rows grouped by bill reference become one sale each. Same all-or-nothing validation. Stock rules still apply. |
| US-19 | M | As a reviewer, I want realistic demo data. | One CLI command loads about 60 products, 6 suppliers, 8 categories, and 90 days of sales with clear fast, steady, slow, and low-stock products. A CLI check confirms ledger consistency. |

### Epic F: Alerts
| ID | Pri | Story | Acceptance criteria |
|---|---|---|---|
| US-20 | M | As the owner, I want to be warned in the app when a product reaches its minimum level. | An alert opens when stock falls to or below the minimum level. The navbar shows an open-alert count. The Alerts page lists open and resolved alerts. Only one open alert per product. |
| US-21 | M | As the owner, I want out-of-stock products to stand out. | At zero stock the alert becomes OUT_OF_STOCK and is styled as more urgent. |
| US-22 | S | As the owner, I want an email when a new alert appears. | One email per new alert to the owner's address. Email failure never blocks a sale and is recorded on the alert. |
| US-23 | S | As the owner, I want to send myself a low-stock summary on demand. | A button sends one email listing all open alerts. The result (sent or failed) is shown. |

### Epic G: Analytics
| ID | Pri | Story | Acceptance criteria |
|---|---|---|---|
| US-24 | M | As the owner, I want a dashboard with today's numbers. | Cards show today's revenue and profit, 30-day revenue and profit, open alerts, and out-of-stock count. |
| US-25 | M | As the owner, I want to see revenue and profit trends. | A chart shows daily revenue and profit with a 7-day and 30-day toggle. Days with no sales show as zero. Voided sales are excluded. |
| US-26 | M | As the owner, I want to see my best sellers. | Top 5 products by revenue over the last 30 days. |
| US-27 | M | As the owner, I want to know the value of my inventory. | Total at cost price and at selling price. |
| US-28 | M | As the owner, I want products classified as fast, steady, or slow movers. | Based on units sold in the last 30 days. Each product shows its class, units sold, and daily sales speed. |
| US-29 | S | As the owner, I want to see money tied up in dead stock. | Slow movers show their stock value at cost, sorted highest first. |

### Epic H: Recommendations
| ID | Pri | Story | Acceptance criteria |
|---|---|---|---|
| US-30 | M | As the owner, I want to know what to reorder, how many, and why. | Each recommendation shows priority (Critical or Soon), suggested quantity, days of stock left, supplier lead time, and a plain-English explanation. |
| US-31 | S | As the owner, I want recommendations grouped by supplier with a copyable order list. | Grouped by supplier. A "Copy order list" button copies a plain-text list. |
| US-32 | C | As the owner, I want smarter predictions of future demand. | An ML forecast is used only if it beats the simple-average baseline in a backtest. Otherwise the rules are used. The UI shows which method produced each number. |
| US-33 | S | As the owner, I want to be told when NOT to reorder. | Overstocked or dead-stock products show "Hold, do not reorder" with the reason. |

### Epic I: Platform
| ID | Pri | Story | Acceptance criteria |
|---|---|---|---|
| US-34 | M | As the owner, I want the app to work on my phone and laptop. | Usable from 375px to 1440px widths. Navigation collapses on small screens. Tables scroll inside their container. |
| US-35 | M | As a reviewer, I want a live link with demo login. | Deployed on a free host. The login page shows demo credentials when demo mode is on. |
| US-36 | M | As any user, I want clear feedback when something goes wrong or is empty. | Form errors appear next to fields. Friendly 404 and 500 pages. Empty states explain the next action. Destructive actions ask for confirmation. |

## 8. Functional Requirements and Business Rules

### 8.1 Stock ledger (core rule)
- **BR-1:** Every change to stock is a row in the `stock_movements` ledger. `products.current_stock` is a cached total that is only changed together with a ledger row, inside one database transaction.
- **BR-2:** Movement types: `OPENING`, `STOCK_IN`, `SALE`, `ADJUSTMENT`, `SALE_VOID`. Each stores a signed quantity change and the stock level after the change.
- **BR-3:** Stock can never go below zero. Any operation that would do so is rejected.
- **BR-4:** All quantities are whole numbers.

### 8.2 Sales
- **BR-5:** A sale has one or more line items. Each line stores quantity, unit price, and unit cost as a snapshot, so later price changes never rewrite history.
- **BR-6:** Sales are created in one transaction. Product rows are locked in a consistent order. If any line fails, the whole sale fails.
- **BR-7:** Sales cannot be edited. They can only be voided. Voiding restores stock and excludes the sale from all analytics.
- **BR-8:** Revenue = sum of completed sale totals. Profit = revenue minus the cost snapshot.

### 8.3 Alerts
- **BR-9:** After any stock change, the alert state of that product is re-evaluated.
- **BR-10:** A product is low when `current_stock <= min_stock` and out when `current_stock = 0`.
- **BR-11:** Crossing into low creates one OPEN alert (type LOW_STOCK). Reaching zero upgrades it to OUT_OF_STOCK. Rising above the minimum level marks it RESOLVED. A product never has more than one open alert.
- **BR-12:** An email is attempted once, when an alert is created. Email problems are logged on the alert and never raise errors to the user.

### 8.4 Movers (last 30 days, completed sales only)
- **BR-13:** Rank active products by units sold in the last 30 days.
- **BR-14:** **Fast** = units sold above zero and in the top 20% of products. **Slow** = zero units sold, or in the bottom 30%. Everything else is **Steady**.

### 8.5 Recommendation rules
Constants (configurable in one file): `DEMAND_WINDOW_DAYS = 28`, `SAFETY_DAYS = 2`, `TARGET_COVER_DAYS = 14`, `DEFAULT_LEAD_TIME_DAYS = 3`, `OVERSTOCK_COVER_DAYS = 60`.

- `daily_demand = units sold in the last 28 days / 28`
- `days_of_cover = current_stock / daily_demand` (infinite if demand is 0)
- `lead_time = supplier lead time, or the default`
- **Reorder trigger:** `current_stock <= min_stock` OR (`daily_demand > 0` AND `days_of_cover <= lead_time + SAFETY_DAYS`)
- **Priority:** **Critical** if stock is 0 or `days_of_cover <= lead_time`. Otherwise **Soon**.
- **Suggested quantity:** `ceil(daily_demand * (lead_time + TARGET_COVER_DAYS) - current_stock)`, at least 1.
- **Hold (do not reorder):** `daily_demand = 0` and stock above 0 with no sales in 28 days, or `days_of_cover > OVERSTOCK_COVER_DAYS`.
- **Explanation text** is generated from these numbers, for example: *"Restock 40 units of Basmati Rice 5 kg. It sells about 6 per day, only 3 days of stock remain, and Sharma Traders takes 3 days to deliver."*

### 8.6 ML forecast (stretch, US-32)
- Per product with at least 28 days of sales history, train a small regression model on daily units using day-of-week and a time trend, and predict the next 7 days.
- Backtest on the most recent 14 days against the baseline (28-day average). Use the forecast only if its mean absolute error is lower than the baseline.
- If the model is unavailable, fails, or does not beat the baseline, the rule-based demand is used and the UI says so.
- **Gate:** attempted on Day 9 only if Days 3 to 8 are complete and the deployed app works. Capped at 90 minutes.

### 8.7 CSV formats
- **Products CSV columns:** `sku, name, category, supplier, cost_price, selling_price, opening_stock, min_stock`. Unknown categories and suppliers are created automatically.
- **Sales CSV columns:** `bill_ref, date, sku, quantity`. Rows sharing a `bill_ref` form one bill. Price comes from the product's current selling price.
- UTF-8, comma-separated, header row required, at most 2,000 rows and 1 MB.

## 9. Data Requirements (summary)

Entities: **User**, **Category**, **Supplier**, **Product**, **StockMovement**, **Sale**, **SaleItem**, **Alert**. Full design is produced on Day 2 in `SCHEMA.md` and validated against every story above.

## 10. Screen Inventory

1. Login
2. Dashboard
3. Products list
4. Product add/edit
5. Product detail (info, stock-in and adjust actions, movement history)
6. New Sale
7. Sales history
8. Sale detail (with void)
9. Alerts
10. Insights (movers)
11. Recommendations
12. Import CSV
13. Categories and Suppliers
14. Error pages (404, 500)

## 11. Non-Functional Requirements

| Area | Requirement |
|---|---|
| Performance | Warm pages respond in under 3 seconds. Lists are paginated. Analytics use database aggregation, not loops over all rows. |
| Cold start | The free host sleeps after 15 idle minutes. The README and demo script say to open the link 2 minutes before a demo. |
| Security | Hashed passwords, CSRF protection on every form and JSON POST, secrets only in environment variables, secure cookies in production, no public registration, parameterized queries through the ORM. |
| Reliability | All stock-changing operations are transactional. Email and forecast failures never break core flows. |
| Usability | Mobile-first responsive layout, Indian rupee formatting (₹1,25,000), dates shown in IST, clear empty and error states, confirmation on destructive actions. |
| Accessibility | Semantic HTML, labelled form fields, sufficient color contrast, keyboard-usable forms. |
| Maintainability | Thin routes, business logic in services, tests for all services, documented structure. |
| Cost | Only free tools and free tiers. |

## 12. Technology Stack (approved)

| Layer | Choice |
|---|---|
| Language and framework | Python with Flask, server-rendered Jinja templates |
| Extensions | Flask-SQLAlchemy, Flask-Migrate, Flask-Login, Flask-WTF |
| UI | Bootstrap 5, Bootstrap Icons, Chart.js, small amounts of vanilla JavaScript |
| Database | PostgreSQL on Neon (free plan) |
| Hosting | Render free web service |
| Email | Resend (free plan) |
| ML (stretch) | NumPy and scikit-learn |
| Testing | pytest |
| Version control | Git and GitHub |

## 13. Assumptions and Constraints

- Quantities are whole numbers (pieces or packs).
- One store, one owner account, created by a command-line step (no sign-up page).
- Currency is Indian rupees. Times are stored in UTC and shown in IST.
- The product is demonstrated with sample data for a general store.
- Free-tier limits apply: the host sleeps when idle, the database scales to zero when idle, and the email plan has daily limits. A free email test sender may only deliver to the account owner's own address, which matches the single-owner design.
- The builder is a beginner working 2 to 3 hours per day, so every day has Must, Should, and Stretch work.

## 14. Risks and Mitigations

| Risk | Impact | Mitigation |
|---|---|---|
| Daily work exceeds 2 to 3 hours | Schedule slips | Each day is split into Must, Should, and Stretch. Cut order is defined in Section 16. |
| Concurrency or transaction bugs corrupt stock | Loss of trust | Single stock service as the only writer, row locking, ledger consistency check, tests. |
| Free host cold starts | Slow first load in a demo | Deploy early (Day 4), document pre-warming, show a friendly loading note. |
| Free email limits or sender restrictions | Alerts not delivered | Email is a Should feature, failures are recorded, in-app alerts always work. |
| ML adds complexity or memory use | Blocks release | Gated stretch with strict time cap and automatic rules fallback. |
| Scope creep | Unfinished product | Non-goals list, feature freeze at the end of Day 9, Day 10 is hardening only. |

## 15. Timeline

| Day | Focus |
|---|---|
| 1 | Product discovery, PRD, blueprint, pitch deck |
| 2 | System design (architecture, schema, API, wireframes, structure) and repository setup |
| 3 | Foundation: environment, app skeleton, database models, login, base layout |
| 4 | Early deployment of the skeleton, products, categories, suppliers |
| 5 | Stock-in, adjustments, mini-bill sales, void, sales history |
| 6 | Demo data seeder, products CSV import, in-app alerts |
| 7 | Dashboard, charts, movers and insights |
| 8 | Recommendation engine, email alerts |
| 9 | ML forecast (gated), polish, responsive pass, sales CSV import if pending |
| 10 | Testing, hardening, final deploy, README, demo script, release |

## 16. Contingency: What Gets Cut First

If time runs short, cut in this order:
1. ML forecast (US-32)
2. Supplier grouping and copy order list (US-31)
3. Sales CSV import (US-18)
4. Dead-stock highlight (US-29)
5. Email alerts (US-22, US-23), keeping in-app alerts

**Never cut:** the stock ledger, sales and void, in-app alerts, dashboard, rule-based recommendations, tests, and the live deployment.

## 17. Definition of Done for v1.0

- All **Must** stories pass their acceptance criteria.
- The app is live on a public free URL with demo credentials and demo data.
- The ledger check command reports zero inconsistencies.
- 40 or more automated tests pass.
- The app is usable on a phone-sized screen and on a laptop.
- README, architecture diagram, demo script, screenshots, and project log are in the repository.
- A tagged `v1.0.0` release exists on GitHub.

## 18. Future Scope

Barcode scanning, multiple users and roles, multiple stores, expiry and batch tracking, size/color variants, purchase orders and supplier portals, GST-aware invoicing, scheduled digests, WhatsApp or SMS alerts, a Progressive Web App for offline use, and fuller ML forecasting with seasonality and festival effects.

## 19. Glossary

- **Ledger:** the permanent list of every stock change.
- **Days of cover:** how many days current stock will last at the recent selling speed.
- **Lead time:** days between ordering from a supplier and receiving goods.
- **Fast / Steady / Slow mover:** product classification by recent unit sales.
- **Dead stock:** stock that has not sold recently and ties up money.
- **Mini bill:** one sale containing several products.
