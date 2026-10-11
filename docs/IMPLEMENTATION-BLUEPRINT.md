# StockSense: Implementation Blueprint (Days 2 to 10)

**Version 1.1.** This is the single source of truth for building StockSense. It works together with `PRD.md` (the what) while this file defines the how, day by day.

> Day 2 refines Sections 0.5 (domain model) and 0.7 (repo structure) into `SCHEMA.md` and `PROJECT-STRUCTURE.md`. If Day 2 changes anything here, this file is updated to **version 1.1** and the change is logged.

---

## How to use this blueprint

Each day begins in a **fresh AI conversation**. Paste, in this order:
1. The **AI Assistant Rules** below
2. **Section 0 (Global Context)**
3. **That day's section**
4. The **latest entry of `docs/PROJECT-LOG.md`** (what actually happened yesterday, including deviations)

### AI Assistant Rules (paste at the top of every daily chat)

You are my co-founder, mentor, and technical lead for the StockSense capstone. I am a beginner (Python and JavaScript basics) with 2 to 3 hours per day.
- Follow this blueprint. **Do not redesign or re-plan.** If you find a critical conflict, explain it and ask me before changing anything.
- For every manual task outside the chat (installing, GitHub, Render, Neon, Resend, terminal commands), give **exact numbered steps using real button, menu, field, and command names**. Then **stop and wait** for my confirmation and a screenshot. Never assume a step is done.
- **Free tools only.** Never suggest paid services.
- Work in the order: **Must, then Should, then Stretch.** Protect me from scope creep. Anything not in this blueprint goes to "Future Scope".
- Explain briefly *why* before each step. Keep code small, readable, and commented.
- All stock changes go through `stock_service` only. Routes stay thin; logic lives in services.
- End each day by helping me commit, push, update the project log, and write the next day's handoff.

---

# SECTION 0: Global Project Context

## 0.1 Product in one paragraph
StockSense is a responsive web app for a single store owner of a small general store (groceries, personal care, stationery, small electronics; prices in ₹). The owner manages products, records multi-item sales as mini bills, and tracks every stock movement in a ledger. The app raises low-stock alerts in the app and by email, shows revenue and profit trends, classifies products as fast, steady, or slow movers, and gives explained restocking recommendations from a rules engine, with an optional small ML demand forecast (gated stretch). It is deployed free and loaded with realistic demo data.

## 0.2 Locked decisions

| Topic | Decision |
|---|---|
| Users | One owner account, created by CLI. No sign-up page. |
| Quantities | Whole numbers only |
| Currency / time | ₹ with Indian digit grouping. Store UTC, display IST (Asia/Kolkata). |
| Sale price | Locked to the product's selling price (no discounts). Snapshot price and cost on each line. |
| Sales | Immutable. Void only. |
| Negative stock | Never allowed |
| Architecture | Server-rendered Flask app, small JSON endpoints for search and charts |
| Database | Neon PostgreSQL. Separate projects for dev and prod. Tests use in-memory SQLite. |
| Email | Triggered when an alert is created (no schedulers, because the free host sleeps) plus a "send summary now" button |
| First migration | Creates **all** tables at once so later days rarely migrate |
| Deploy early | Skeleton goes live on Day 4, not Day 10 |
| Feature freeze | End of Day 9. Day 10 is testing, fixing, and release only. |

## 0.3 Stack and what each piece is for

| Piece | Purpose |
|---|---|
| Python (3.11 or newer) | Language |
| Flask | Web framework (app factory plus blueprints) |
| Flask-SQLAlchemy | ORM for tables and queries |
| Flask-Migrate (Alembic) | Versioned database migrations |
| Flask-Login | Session login |
| Flask-WTF | Forms and CSRF protection |
| `psycopg[binary]` | PostgreSQL driver (connection URL prefix `postgresql+psycopg://`) |
| python-dotenv | Loads `.env` locally |
| gunicorn | Production web server on Render |
| requests | Calls the Resend email REST API |
| pytest | Tests |
| NumPy, scikit-learn | ML forecast (Day 9 stretch only) |
| Bootstrap 5, Bootstrap Icons, Chart.js (CDN) | Responsive UI, icons, charts |
| Vanilla JavaScript | Sale line items, product search box, copy-to-clipboard, chart loading |

Pin the exact versions you install on Day 3 in `requirements.txt`.

## 0.4 Business rules (shortened from the PRD, do not change)

- **R1 Ledger:** every stock change is a `stock_movements` row written together with the `products.current_stock` update in one transaction. Types: `OPENING`, `STOCK_IN`, `SALE`, `ADJUSTMENT`, `SALE_VOID`. Each row stores a signed `quantity_change` and `stock_after`.
- **R2 Single writer:** only `stock_service.apply_movement()` may change `current_stock`.
- **R3 No negative stock:** reject any change that would go below 0.
- **R4 Sales:** one transaction. Lock product rows with `SELECT ... FOR UPDATE` ordered by product id. All lines succeed or none do. Bill number format `B-000123` (zero-padded sale id).
- **R5 Void:** creates `SALE_VOID` movements restoring stock, sets status `VOIDED`, requires a reason, cannot be repeated. Voided sales are excluded from every analytic.
- **R6 Alerts:** after any stock change call `alert_service.sync_alert(product)`. Low means `current_stock <= min_stock`. Out means `current_stock = 0`. Create one OPEN alert (LOW_STOCK) on crossing. Upgrade to OUT_OF_STOCK at zero. RESOLVE when stock is above `min_stock`. At most one OPEN alert per product (partial unique index). Email is attempted only when an alert is created. Failures are recorded and never raised.
- **R7 Revenue and profit:** revenue = sum of completed `sales.total_amount`. Profit = revenue minus `sales.total_cost`.
- **R8 Movers (30 days, completed sales):** rank active products by units sold. Fast = units above 0 and top 20%. Slow = 0 units or bottom 30%. Else Steady.
- **R9 Recommendations (constants in `app/constants.py`):** `DEMAND_WINDOW_DAYS=28`, `SAFETY_DAYS=2`, `TARGET_COVER_DAYS=14`, `DEFAULT_LEAD_TIME_DAYS=3`, `OVERSTOCK_COVER_DAYS=60`.
  `daily_demand = units_28d / 28`. `days_of_cover = stock / daily_demand`. Trigger when `stock <= min_stock` or (`daily_demand > 0` and `days_of_cover <= lead_time + SAFETY_DAYS`). Critical if stock is 0 or `days_of_cover <= lead_time`, else Soon. `suggested_qty = max(1, ceil(daily_demand * (lead_time + TARGET_COVER_DAYS) - stock))`. Hold when (`daily_demand = 0` and stock above 0) or `days_of_cover > OVERSTOCK_COVER_DAYS`.
- **R10 ML (stretch):** per product with at least 28 days of history, fit a small regression (day-of-week plus trend), predict 7 days, and use it only if it beats the 28-day-average baseline in a 14-day backtest. Otherwise use R9 demand. Always label the method used.

## 0.5 Domain model (finalized as `SCHEMA.md` on Day 2)

| Table | Key fields | Notes |
|---|---|---|
| `users` | id, name, email (unique), password_hash, created_at | One row |
| `categories` | id, name (unique) | |
| `suppliers` | id, name (unique), phone, email, lead_time_days (default 3) | |
| `products` | id, sku (unique), name, category_id, supplier_id, cost_price, selling_price, current_stock, min_stock, is_active, created_at, updated_at | CHECKs: prices and stocks at least 0 |
| `sales` | id, bill_no (unique), sold_at, sale_date (IST date), total_amount, total_cost, status (COMPLETED / VOIDED), voided_at, void_reason, created_by | |
| `sale_items` | id, sale_id, product_id, quantity (above 0), unit_price, unit_cost, line_total, line_cost | |
| `stock_movements` | id, product_id, type, quantity_change (not 0), stock_after, reason, note, sale_id (nullable), created_by, created_at | |
| `alerts` | id, product_id, alert_type, stock_at_alert, min_stock_at_alert, status (OPEN / RESOLVED), created_at, resolved_at, email_status (NOT_SENT / SENT / FAILED / SKIPPED), email_sent_at | Partial unique index: one OPEN per product |

Indexes: `products(name)`, `sales(sale_date)`, `sale_items(product_id)`, `stock_movements(product_id, created_at)`, `alerts(product_id, status)`.

## 0.6 Conventions

- **Money:** `Numeric(12,2)`. Format with the Jinja filter `rupees` (for example ₹1,25,000.00).
- **Dates:** store UTC. `sales.sale_date` is the IST calendar date. Show IST everywhere with the `ist` filter.
- **Security:** `CSRFProtect` globally. JSON POSTs send `X-CSRFToken` read from a `<meta>` tag. A global `before_request` requires login except `auth.login`, `healthz`, and `static`. Cookies are `Secure`, `HttpOnly`, and `SameSite=Lax` in production.
- **Errors:** services raise a small `DomainError(message)`. Routes catch it, flash the message, and re-render the form. Friendly 404 and 500 pages.
- **Forms:** Flask-WTF classes in each blueprint's `forms.py`.
- **Naming:** snake_case files and functions, `PascalCase` classes, blueprint names match folder names.
- **Git:** one commit per meaningful step, message style `feat: add product list`, `fix: ...`, `docs: ...`, `test: ...`. Push at the end of every day. Tag `v1.0.0` on Day 10.
- **Tests:** `pytest -q`. Services have unit tests. Core pages have route tests with the Flask test client.

## 0.7 Provisional repository structure (finalized as `PROJECT-STRUCTURE.md` on Day 2)

```
stocksense/
├── app/
│   ├── __init__.py            # create_app()
│   ├── config.py              # Dev / Prod / Test config classes
│   ├── constants.py           # recommendation constants, enums
│   ├── extensions.py          # db, migrate, login_manager, csrf
│   ├── cli.py                 # create-owner, seed-demo, verify-ledger
│   ├── models/                # one file per table group
│   ├── services/              # stock, sales, alert, email, import, analytics,
│   │                          # recommendation, forecast, seed
│   ├── blueprints/            # auth, dashboard, products, lists, stock, sales,
│   │                          # alerts, insights, recommendations, imports, api
│   ├── templates/             # base.html, partials/, one folder per blueprint
│   ├── static/                # css/app.css, js/*.js, img/
│   └── utils/                 # formatting.py, dates.py
├── migrations/                # Alembic (generated)
├── tests/                     # conftest.py, test_*.py
├── data/                      # CSV templates and sample files
├── docs/                      # PRD, blueprint, design docs, PROJECT-LOG, screenshots/
├── .env.example
├── .gitignore
├── requirements.txt
├── wsgi.py                    # gunicorn entry point
└── README.md
```

## 0.8 Environment variables

| Name | Used for |
|---|---|
| `SECRET_KEY` | Session signing |
| `DATABASE_URL` | Neon connection string (convert to `postgresql+psycopg://...` form) |
| `APP_ENV` | `development`, `production`, or `testing` |
| `DEMO_MODE` | `true` shows demo credentials on the login page |
| `RESEND_API_KEY` | Email sending (Day 8) |
| `ALERT_FROM_EMAIL` | Sender (Resend test sender at first) |
| `ALERT_TO_EMAIL` | Owner's alert address |

`.env` is never committed. `.env.example` is.

## 0.9 Time budget, cut order, and freeze

- Each day: **Must (about 2 hours)**, **Should (about 30 minutes)**, **Stretch (only if ahead)**.
- Unfinished Should items roll into Day 9. Unfinished Must items stop all new work until done.
- **Cut order:** ML forecast, supplier grouping and copy list, sales CSV import, dead-stock highlight, email alerts.
- **Never cut:** ledger, sales and void, in-app alerts, dashboard, rule-based recommendations, tests, deployment.
- **Feature freeze:** end of Day 9.

## 0.10 Definition of done
See PRD Section 17.

---

# DAY 2: System Design and Repository Setup

### 🎯 Objective
Turn the plan into a complete technical design (architecture, schema, API, wireframes, structure), create and clone the GitHub repository with the initial structure, and confirm Day 3 can start building immediately. No production code.

### 📖 What I'll learn
- Installing and using Git and GitHub (repo, clone, commit, push)
- Reading and drawing architecture diagrams with Mermaid
- Entity relationship design and constraints
- Designing routes and JSON endpoints before coding
- Low-fidelity wireframing and user-flow thinking
- Requirements traceability (every user story maps to schema, API, and screen)

### 🛠 Features to build
None. This is a design and setup day.
- **Must:** repository created, cloned, and structured. The five design documents. Traceability check. Commit and push.
- **Should:** project log, LinkedIn post.

### 📝 Step-by-step implementation plan
1. Confirm operating system and check for Git, VS Code, and a GitHub account. Install anything missing (guided).
2. Configure Git identity (`git config --global user.name` and `user.email`).
3. Create the GitHub repository `stocksense` (README, Python `.gitignore`, MIT license), then clone it locally.
4. Create the initial folders and placeholder files from `PROJECT-STRUCTURE.md`. Copy `PRD.md` and this blueprint into `docs/`.
5. Finalize the stack (confirm every choice, record the reason).
6. Write `ARCHITECTURE.md`: component diagram, data flow, request lifecycle, external services (Mermaid).
7. Write `SCHEMA.md`: ER diagram, tables, constraints, indexes, and a story-by-story validation table.
8. Write `API.md`: every route and JSON endpoint with purpose, request, response, validation, auth, and errors.
9. Write `UI-WIREFRAMES.md`: user flow, screen flow, navigation, low-fidelity wireframes.
10. Write `PROJECT-STRUCTURE.md`: folder responsibilities and where each future file lives.
11. Run the Day 3 readiness check and update this blueprint if needed (v1.1).
12. Create `docs/PROJECT-LOG.md`, commit, push, and draft the LinkedIn post.

### 📂 Files and folders to create or modify
- Repo root: `README.md` (stub), `.gitignore`, `.env.example`, `requirements.txt` (empty placeholder), `wsgi.py` (empty placeholder)
- `app/`, `tests/`, `data/`, `migrations/` (with `.gitkeep` files)
- `docs/`: `PRD.md`, `IMPLEMENTATION-BLUEPRINT.md`, `ARCHITECTURE.md`, `SCHEMA.md`, `API.md`, `UI-WIREFRAMES.md`, `PROJECT-STRUCTURE.md`, `PROJECT-LOG.md`, `screenshots/`

### 🔗 APIs, libraries, services, or tools to integrate
Git, GitHub, VS Code, Mermaid (GitHub renders it natively in Markdown).

### 🧪 Testing tasks
- Every `mermaid` block renders on GitHub (open each file on github.com after pushing).
- Traceability: all 36 user stories appear in `SCHEMA.md` and `API.md`, and every Must story has a screen in `UI-WIREFRAMES.md`.
- Every endpoint in `API.md` is used by at least one screen.
- Every screen is reachable from the navigation.

### 🐞 Common issues and debugging tips
- `git` is not recognized: reopen the terminal after installing, or restart VS Code.
- Push asks for credentials: sign in through the browser window Git opens (Git Credential Manager), or use a Personal Access Token as the password.
- Mermaid does not render: check the code fence is exactly `mermaid` and there are no tabs.
- Files appear changed on every commit on Windows: line-ending warnings are normal, so ignore them.
- Wrong folder: always confirm with `pwd` (Mac/Linux) or `cd` (Windows) that you are inside the repo.

### ✅ End-of-day checklist
- [ ] Repo exists on GitHub and is cloned locally
- [ ] Initial folder structure committed
- [ ] Five design documents written and committed
- [ ] Traceability check passed
- [ ] Day 3 readiness confirmed
- [ ] Project log updated
- [ ] LinkedIn post drafted

### 📸 Expected project state and screenshots to capture
- `git --version` output, GitHub repo page, local folder in VS Code, GitHub showing `docs/` with rendered Mermaid diagrams, `git log --oneline` output.

### ➡️ Handoff notes for Day 3
- Repo name `stocksense`, local path noted in the log, Git identity configured.
- Final schema, API, wireframes, and structure are in `docs/`. Day 3 implements models exactly as in `SCHEMA.md`.
- Operating system recorded for command syntax.

---

# DAY 3: Foundation (Environment, App Skeleton, Database, Login)

### 🎯 Objective
By the end of today, StockSense runs locally, connects to a Neon dev database, has all tables created by a migration, supports owner login and logout, and shows a responsive base layout with a placeholder dashboard.

### 📖 What I'll learn
- Python virtual environments and `pip`
- Flask application factory and blueprints
- SQLAlchemy models, constraints, and Alembic migrations
- Password hashing, sessions, and CSRF
- Jinja template inheritance and Bootstrap layout
- Writing the first pytest tests

### 🛠 Features to build
- **Must:** local environment, Flask skeleton, Neon dev DB, all models and first migration, `create-owner` command, login/logout, global login requirement, `base.html` with responsive navigation, placeholder dashboard, `/healthz`, `rupees` and `ist` filters, first tests.
- **Must (added in v1.1, from Day 2):** confirm operating system, install or check Git and VS Code, create the GitHub repo `stocksense`, clone it, create the folder skeleton, copy docs into `docs/`, make the first commit.
- **Should:** none (custom 404/500 pages moved to Day 9).
- **Stretch:** none.

### 📝 Step-by-step implementation plan
0. (v1.1) Complete the Day 2 repository setup: check tools, create the repo, clone it, add the folder skeleton and docs, first commit and push.
1. Install Python (3.11 or newer) if missing. Create and activate a virtual environment `.venv` in the repo.
2. Install packages: Flask, Flask-SQLAlchemy, Flask-Migrate, Flask-Login, Flask-WTF, `psycopg[binary]`, python-dotenv, gunicorn, requests, pytest. Freeze to `requirements.txt`.
3. Create a free Neon account and a project named `stocksense-dev`. Copy the connection string. Create `.env` (git-ignored) and `.env.example` (no secrets).
4. Write `config.py` (Development, Production, Testing classes), `extensions.py`, and `create_app()` in `app/__init__.py`.
5. Write `wsgi.py` with `app = create_app()`.
6. Write all models exactly as in `SCHEMA.md`, including CHECK constraints, indexes, and the partial unique index on open alerts.
7. Initialize migrations (`flask db init`), generate the first migration (`flask db migrate -m "initial schema"`), review it, and apply it (`flask db upgrade`).
8. Verify tables in the Neon dashboard (Tables view).
9. Write `cli.py` with `flask create-owner` (prompts for name, email, password) and register it.
10. Build the `auth` blueprint: login form, login route, logout route. Hash with Werkzeug.
11. Add the global `before_request` that requires login except `auth.login`, `healthz`, and `static`.
12. Build `base.html`: top navbar on large screens, collapsing menu on small screens, flash message area, Bootstrap, Bootstrap Icons, Chart.js script tag (unused yet), and the CSRF meta tag.
13. Build the placeholder dashboard and a `/healthz` route that returns `ok` without touching the database.
14. Add `rupees` and `ist` Jinja filters in `utils/formatting.py`.
15. Write the first tests, run `pytest -q`, commit, and push.

### 📂 Files and folders to create or modify
`requirements.txt`, `.env.example`, `wsgi.py`, `app/__init__.py`, `app/config.py`, `app/constants.py`, `app/extensions.py`, `app/cli.py`, `app/models/*`, `app/blueprints/auth/{__init__,routes,forms}.py`, `app/blueprints/dashboard/{__init__,routes}.py`, `app/templates/base.html`, `app/templates/auth/login.html`, `app/templates/dashboard/index.html`, `app/static/css/app.css`, `app/utils/{formatting,dates}.py`, `migrations/*` (generated), `tests/{conftest,test_auth,test_models}.py`

### 🔗 APIs, libraries, services, or tools to integrate
Flask family, SQLAlchemy, Alembic, psycopg, Neon (free), Bootstrap and Chart.js via CDN.

### 🧪 Testing tasks
- `conftest.py` builds the app with a Testing config and in-memory SQLite and creates tables per test.
- Auth tests: login succeeds with correct credentials, fails with wrong ones, protected pages redirect to login, logout works.
- Model tests: negative price rejected, negative stock rejected, duplicate SKU rejected, a second OPEN alert for the same product rejected.
- Manual: log in on a laptop and in a phone-width browser window, confirm the menu collapses.

### 🐞 Common issues and debugging tips
- `ModuleNotFoundError`: the virtual environment is not activated (prompt should show `(.venv)`).
- Connection errors: the SQLAlchemy URL must start with `postgresql+psycopg://`. Neon needs SSL, so keep `sslmode=require` in the URL.
- `flask` command not found or wrong app: set `FLASK_APP=wsgi.py` in `.env`.
- Alembic says "Target database is not up to date": run `flask db upgrade` first.
- "CSRF token missing": every POST form needs `{{ form.hidden_tag() }}`.
- Neon database slow on the first query: it was asleep, so wait a few seconds and retry.
- Never paste real secrets into chat or commit `.env`.

### ✅ End-of-day checklist
- [ ] `flask run` serves the app locally
- [ ] All 8 tables exist in Neon dev
- [ ] `flask create-owner` works and login/logout work
- [ ] Unauthenticated access redirects to login
- [ ] Responsive navbar verified on a narrow window
- [ ] `pytest -q` passes
- [ ] Committed and pushed, project log updated

### 📸 Expected project state and screenshots to capture
Login page, placeholder dashboard after login (desktop and narrow width), Neon Tables view showing 8 tables, terminal showing `pytest` green, GitHub commit list.

### ➡️ Handoff notes for Day 4
- App factory, extensions, and all models exist. Migration `initial schema` is applied to Neon dev.
- Owner account exists locally (credentials stay in `.env` and private notes).
- `base.html`, filters, auth, and tests exist. Next: deploy the skeleton and build catalog CRUD.


---

# DAY 4: Early Deployment, Products, Categories, Suppliers

### 🎯 Objective
Put the skeleton live on Render (the riskiest unknown, so we do it early), then build the catalog: categories, suppliers, and products with search, filter, sort, pagination, add, edit, and archive. Opening stock goes through the stock ledger from day one.

### 📖 What I'll learn
- Deploying a Flask app from GitHub to Render with a production Neon database
- Environment variables per environment
- CRUD with SQLAlchemy and WTForms
- Query-string filtering, sorting, and pagination
- Writing the first service (`stock_service`) and unit-testing it

### 🛠 Features to build
- **Must (about 2 hours):** Render deployment with prod Neon DB and migrations, `stock_service.apply_movement` (OPENING type), Categories and Suppliers page (US-07, US-08), products list with search, filters, sort, pagination (US-05), add product (US-03), edit product (US-04).
- **Should:** archive and restore (US-06), colored status badges.
- **Stretch:** none.

### 📝 Step-by-step implementation plan
1. Create a second Neon project `stocksense-prod`. Copy its connection string.
2. Create a free Render account and a **New Web Service** from the GitHub repo. Build command `pip install -r requirements.txt`. Start command `flask db upgrade && gunicorn wsgi:app --workers 1 --timeout 120`. Instance type **Free**.
3. Set environment variables in Render: `SECRET_KEY`, `DATABASE_URL` (prod, converted to `postgresql+psycopg://`), `APP_ENV=production`, `DEMO_MODE=true`.
4. Deploy, open the live URL, check `/healthz`.
5. Create the prod owner by running `flask create-owner` locally with `DATABASE_URL` temporarily pointed at prod (guided, one terminal session only). Log in on the live site.
6. Build `stock_service.py`: `apply_movement(product, type, quantity_change, reason=None, note=None, sale_id=None)` that locks the product row, rejects negative results, writes the ledger row, updates `current_stock`, then calls `alert_service.sync_alert` (a no-op stub until Day 6).
7. Build the `lists` blueprint: one page with two sections (categories and suppliers), each with an add form and an inline rename or edit, and delete blocked when in use.
8. Build the `products` blueprint: list route with query parameters `q`, `category`, `supplier`, `status`, `sort`, `page` (15 per page).
9. Build the add-product form with validation: unique SKU, prices at least 0, integers for stocks, warning if selling price is below cost.
10. On create, if opening stock is above 0, call `stock_service.apply_movement(type=OPENING)`.
11. Build the edit form (SKU read-only, stock not editable).
12. Add archive and restore with confirmation. Archived products are hidden by default.
13. Add stock status badges: OK, Low, Out (from `current_stock` and `min_stock`).
14. Write tests, commit, push, redeploy, and re-check the live site.

### 📂 Files and folders to create or modify
`app/services/stock_service.py`, `app/services/alert_service.py` (stub), `app/blueprints/lists/{__init__,routes,forms}.py`, `app/blueprints/products/{__init__,routes,forms}.py`, `app/templates/lists/index.html`, `app/templates/products/{list,form}.html`, `app/templates/partials/{pagination,status_badge}.html`, `tests/{test_stock_service,test_products,test_lists}.py`, modify `app/__init__.py` (register blueprints) and the navbar in `base.html`.

### 🔗 APIs, libraries, services, or tools to integrate
Render (free web service), Neon prod project, GitHub integration, Flask-WTF forms.

### 🧪 Testing tasks
- `stock_service`: OPENING creates movement and sets stock, negative result raises `DomainError`, zero change rejected.
- Products: duplicate SKU rejected, negative price rejected, SKU unchanged on edit, archived products hidden from default list, filters and search return expected rows.
- Lists: deleting a category in use is blocked.
- Manual on the live site: add a product, find it by search, edit it, archive and restore it.

### 🐞 Common issues and debugging tips
- Render build fails: check `requirements.txt` is committed and the Python version matches.
- App crashes on start: read Render **Logs**. Usually a missing environment variable or the `postgresql+psycopg://` prefix.
- First load takes a long time: free-tier cold start, so wait up to a minute.
- Migration not applied on prod: confirm the start command includes `flask db upgrade`.
- Pagination shows wrong totals: apply filters before `db.paginate`.
- Never point local development at the prod database except for the one guided `create-owner` command.

### ✅ End-of-day checklist
- [ ] Live URL loads and login works
- [ ] Categories and suppliers can be added, edited, and safely deleted
- [ ] Products list with search, filter, sort, and pagination works
- [ ] Add and edit product work, opening stock creates an OPENING movement
- [ ] Archive and restore work
- [ ] Tests pass, code pushed, redeployed

### 📸 Expected project state and screenshots to capture
Render dashboard showing a successful deploy, the live login page, categories and suppliers page, products list (with a search applied), add-product form with a validation error, GitHub commits.

### ➡️ Handoff notes for Day 5
- Live URL recorded in the project log. Prod owner exists.
- `stock_service.apply_movement` exists and only supports OPENING so far. Day 5 extends type handling.
- `alert_service.sync_alert` is a stub that Day 6 fills in.

---

# DAY 5: Stock Operations and Sales

### 🎯 Objective
Complete the ledger and the heart of the app: stock-in, adjustments, product detail with movement history, the multi-item New Sale screen, sales history, sale detail, and void.

### 📖 What I'll learn
- Database transactions and row locking
- Designing a dynamic form (add and remove line items) with vanilla JavaScript
- JSON endpoints for live product search
- Domain errors and clean error messages
- Why snapshotting price and cost protects history

### 🛠 Features to build
- **Must (about 2 hours):** stock-in (US-09), adjustment (US-10), product detail with movement history (US-11), New Sale (US-12, US-13), sales history (US-14), sale detail (US-15), void (US-16).
- **Should:** confirm dialogs, bill-number polish, quick "Sell" shortcut on a product row.
- **Stretch:** none.

### 📝 Step-by-step implementation plan
1. Extend `stock_service` for `STOCK_IN`, `ADJUSTMENT`, `SALE`, `SALE_VOID` (same rules, reason required for adjustments).
2. Build the product detail page: product info, current stock, status badge, **Stock-in** and **Adjust** modals, paginated movement history.
3. Add the stock-in and adjustment POST routes with validation and flash messages.
4. Build `GET /api/products/search?q=` returning up to 10 active products (id, sku, name, selling price, stock) for the sale screen.
5. Build `sales_service.create_sale(items)`: validate lines, lock product rows ordered by id, check stock, create the sale and items (price and cost snapshots), call `stock_service.apply_movement(type=SALE)` per line, compute totals, set `sale_date` (IST), generate `bill_no`, commit once.
6. Build the New Sale page: search box, results dropdown, line items table with quantity inputs and remove buttons, live total in JavaScript, submit as one POST. The server recomputes everything and ignores client-side prices.
7. Show clear errors naming the product and available quantity when stock is insufficient. Nothing is saved on failure.
8. Build sales history with date range and status filters, paginated.
9. Build sale detail: items, revenue, cost, profit, status, and a **Void** button (reason required, confirm dialog).
10. Build `sales_service.void_sale(sale, reason)`: guard against repeat voids, restore stock with `SALE_VOID` movements, set status, voided time, and reason.
11. Write tests (see below), commit, push, redeploy, and test on the live site.

### 📂 Files and folders to create or modify
`app/services/{stock_service,sales_service}.py`, `app/blueprints/stock/{__init__,routes,forms}.py`, `app/blueprints/sales/{__init__,routes,forms}.py`, `app/blueprints/api/{__init__,routes}.py`, `app/templates/products/detail.html`, `app/templates/sales/{new,list,detail}.html`, `app/static/js/sale_form.js`, `tests/{test_stock_ops,test_sales_service,test_sales_routes}.py`

### 🔗 APIs, libraries, services, or tools to integrate
SQLAlchemy `with_for_update()`, Bootstrap modals, `fetch` for product search (with the CSRF header on any POST).

### 🧪 Testing tasks
- Stock-in raises stock and writes a ledger row. Adjustment without reason is rejected. Adjustment below zero is rejected.
- Sale of 3 items reduces each product, writes 3 SALE movements, stores snapshot price and cost, and computes correct totals and profit.
- Sale with one line over stock fails and changes nothing (check stock and counts).
- Changing a product's price after a sale does not change the old sale's totals.
- Void restores stock, marks the sale, and a second void raises an error.
- Ledger check: for every product, `current_stock` equals the sum of its movement changes.
- Manual: record a 5-item bill and time it (target under 60 seconds).

### 🐞 Common issues and debugging tips
- Totals off by a paisa: always use `Decimal`, never `float`.
- SQLite ignores row locks in tests, which is expected. Real locking happens on Postgres.
- Deadlocks: always lock product rows in ascending id order.
- Duplicate products on one bill: merge lines for the same product before validating.
- Dropdown not appearing: check the browser console for a 400 (missing CSRF header) or a JavaScript error.
- Time zone off by a day on `sale_date`: compute it from the IST time, not UTC.

### ✅ End-of-day checklist
- [ ] Stock-in and adjustment work with reasons and history
- [ ] A multi-item sale reduces stock correctly
- [ ] Over-stock sale is rejected cleanly
- [ ] Sales history, detail, and void work
- [ ] Ledger consistency test passes
- [ ] Tests pass, pushed, redeployed, live site checked

### 📸 Expected project state and screenshots to capture
Product detail with movement history, New Sale with 3 lines and a total, over-stock error message, sale detail with profit, voided sale, passing tests.

### ➡️ Handoff notes for Day 6
- Ledger and sales are complete and tested. `alert_service.sync_alert` is already called after every stock change (still a stub).
- `sales_service` exposes `create_sale` and `void_sale`. Day 6's seeder may insert history in bulk but must keep the ledger consistent.

---

# DAY 6: Demo Data, Products CSV Import, In-App Alerts

### 🎯 Objective
Make the app feel real and alive: a seeder that loads realistic demo data, a products CSV import, and in-app low-stock alerts with a navbar badge.

### 📖 What I'll learn
- Generating realistic synthetic data (popularity curves, weekday effects)
- Parsing and validating CSV files safely
- State machines for alerts (open, upgrade, resolve)
- Context processors for shared template data
- Verifying data integrity with a CLI check

### 🛠 Features to build
- **Must (about 2 hours):** `alert_service.sync_alert` (US-20, US-21), Alerts page with Open and Resolved tabs, navbar badge, seeder `flask seed-demo` (US-19), `flask verify-ledger`.
- **Should:** products CSV import with template download and error report (US-17).
- **Stretch:** begin sales CSV import (otherwise moves to Day 9).

### 📝 Step-by-step implementation plan
1. Implement `alert_service.sync_alert(product)` per rule R6. Handle create, upgrade to OUT_OF_STOCK, resolve, and the one-open-alert guarantee. Leave the email step as a clearly marked hook for Day 8.
2. Build the Alerts page (Open tab with severity styling, Resolved tab, product links) and the navbar badge using a context processor that counts open alerts.
3. Design the demo dataset in `seed_service.py`: 8 categories, 6 suppliers with different lead times, about 60 products with realistic names and ₹ prices, a popularity weight per product (a few very popular, many middling, about 8 nearly dead), weekend uplift, two products trending up and two trending down.
4. Generate 90 days of sales by writing sales, items, and movements in bulk while keeping the ledger consistent. Give products opening stock and periodic stock-ins so that most are healthy, about 6 are low, and 2 are out.
5. Add `flask seed-demo --reset` (clears everything except users, then reseeds) and `flask verify-ledger` (checks each product's stock equals the sum of its movements and the `stock_after` chain is consistent).
6. Run seed locally, then on prod (guided, one-off) and confirm the live app shows data.
7. (Should) Build the Import page: choose file, upload, validate the whole file, either import all rows or show an error table (row, column, message). Provide a downloadable CSV template. Limit 2,000 rows and 1 MB.
8. Auto-create unknown categories and suppliers during import. Opening stock goes through `stock_service`.
9. Write tests, commit, push, redeploy.

### 📂 Files and folders to create or modify
`app/services/{alert_service,seed_service,import_service}.py`, `app/cli.py` (add commands), `app/blueprints/alerts/{__init__,routes}.py`, `app/blueprints/imports/{__init__,routes,forms}.py`, `app/templates/alerts/index.html`, `app/templates/imports/index.html`, `app/templates/partials/alert_badge.html`, `data/products_template.csv`, `data/sample_products.csv`, `tests/{test_alert_service,test_seed,test_import_products}.py`

### 🔗 APIs, libraries, services, or tools to integrate
Python standard library only (`csv`, `random`, `datetime`, `decimal`). Use a fixed random seed so demo data is reproducible.

### 🧪 Testing tasks
- Alerts: falling to the minimum level opens one alert, a second change does not create a duplicate, reaching zero upgrades to OUT_OF_STOCK, stock-in above the minimum resolves.
- Seed: after seeding, `verify-ledger` reports zero issues, product count is about 60, and there are low and out-of-stock products.
- Import: valid file imports, a bad price or duplicate SKU rejects the whole file with a clear row-level error.
- Manual: sell a product down to its minimum and watch the badge change.

### 🐞 Common issues and debugging tips
- Seeder is slow: use bulk inserts and one commit per batch, not per row.
- Ledger check fails after seeding: you updated `current_stock` without writing a movement, or the order of movements is wrong.
- Duplicate open alerts: confirm the partial unique index exists in the migration.
- CSV with a byte-order mark: open with `utf-8-sig`.
- Excel-saved CSVs sometimes use semicolons: show a clear error if the header does not match.
- Seeding prod by mistake on dev data: always print which database host you are about to modify and ask for confirmation.

### ✅ End-of-day checklist
- [ ] Alerts open, upgrade, and resolve correctly with a navbar badge
- [ ] `seed-demo` loads realistic data locally and on prod
- [ ] `verify-ledger` reports zero issues
- [ ] Products CSV import works (or is logged as rolled over)
- [ ] Tests pass, pushed, redeployed

### 📸 Expected project state and screenshots to capture
Alerts page with open items, navbar badge, products list full of demo data, `verify-ledger` output, import error table, live site with data.

### ➡️ Handoff notes for Day 7
- About 60 products and 90 days of history exist on dev and prod.
- Seed has clear tiers (fast, steady, slow, dead) that Day 7 analytics should reveal.
- `alert_service.sync_alert` is complete except the email hook.
- If sales CSV import was not started, it is on the Day 9 Should list.

---

# DAY 7: Dashboard, Charts, Movers, and Insights

### 🎯 Objective
Build the analytics that make the product feel intelligent: dashboard KPIs, revenue and profit trend chart, top sellers, inventory value, and the movers (fast, steady, slow) insights page.

### 📖 What I'll learn
- SQL aggregation with SQLAlchemy (`func.sum`, `group_by`, joins)
- Filling missing dates in a time series
- Percentile-based classification
- Serving chart data as JSON and drawing with Chart.js
- Verifying analytics against hand calculations

### 🛠 Features to build
- **Must (about 2 hours):** dashboard KPI cards (US-24), revenue and profit chart with 7 and 30 day toggle (US-25), top 5 products (US-26), inventory value at cost and retail (US-27), movers classification page (US-28).
- **Should:** dead-stock value list (US-29), open alerts widget on dashboard.
- **Stretch:** none.

### 📝 Step-by-step implementation plan
1. Write `analytics_service.py` functions: `kpis()`, `daily_series(days)`, `top_products(days, limit)`, `inventory_value()`, `mover_classification(days=30)`, `dead_stock()`.
2. All functions use only COMPLETED sales and `sales.sale_date`. Aggregate in SQL, not in Python loops.
3. `daily_series` returns one point per day, filling gaps with zero.
4. `mover_classification` computes units sold per active product over 30 days, ranks them, and applies R8 (fast top 20% with units above 0, slow zero or bottom 30%, else steady).
5. Add JSON endpoints `GET /api/analytics/revenue-profit?days=7|30` and `GET /api/analytics/top-products`.
6. Build the dashboard: KPI cards (today revenue, today profit, 30-day revenue, 30-day profit, inventory value, open alerts, out-of-stock), line chart for revenue and profit, bar chart for top products, a small alerts widget.
7. Add chart loading and empty states in `static/js/dashboard.js` (spinner while loading, friendly message if no data).
8. Build the Insights page with tabs for Fast, Steady, Slow: product, units sold, daily speed, stock, stock value.
9. (Should) Dead stock section: slow movers sorted by stock value at cost.
10. Write tests comparing analytics output with hand-computed values on a tiny fixed dataset. Commit, push, redeploy.

### 📂 Files and folders to create or modify
`app/services/analytics_service.py`, `app/blueprints/dashboard/routes.py` (extend), `app/blueprints/insights/{__init__,routes}.py`, `app/blueprints/api/routes.py` (extend), `app/templates/dashboard/index.html`, `app/templates/insights/index.html`, `app/templates/partials/kpi_card.html`, `app/static/js/dashboard.js`, `tests/{test_analytics_service,test_insights_routes}.py`

### 🔗 APIs, libraries, services, or tools to integrate
Chart.js (CDN), SQLAlchemy aggregation.

### 🧪 Testing tasks
- Tiny dataset (3 products, a handful of sales): revenue, profit, top product, inventory value, and classification all match hand calculation.
- Voided sales are excluded from every number.
- Days without sales appear as zero in the series.
- With demo data, every class (fast, steady, slow) is populated and the dead-stock list is non-empty.
- Manual: toggle 7 and 30 days, resize to phone width, charts stay readable.

### 🐞 Common issues and debugging tips
- Revenue differs between pages: one query forgot to filter out VOIDED.
- Chart looks empty: check the JSON in the browser Network tab and that dates are sorted ascending.
- Chart overflows on mobile: wrap canvas in a container with `position: relative` and a max width.
- Classification with ties: define a stable order (units sold, then name) so results are deterministic.
- Slow dashboard: confirm indexes on `sales(sale_date)` and `sale_items(product_id)` exist.

### ✅ End-of-day checklist
- [ ] Dashboard KPIs and both charts display correct data
- [ ] Movers page shows fast, steady, and slow with sensible products
- [ ] Analytics match hand-calculated test values
- [ ] Looks good on desktop and phone width
- [ ] Tests pass, pushed, redeployed

### 📸 Expected project state and screenshots to capture
Dashboard (desktop and phone width), 7 vs 30 day chart, movers tabs, dead-stock list, test output.

### ➡️ Handoff notes for Day 8
- `analytics_service` and the movers function exist. Day 8 reuses the units-sold query for demand.
- Dashboard has a reserved slot for "Top recommendations" that Day 8 fills.

---

# DAY 8: Recommendation Engine and Email Alerts

### 🎯 Objective
Deliver the headline feature: explained reorder recommendations from the rules engine. Add email alerts through Resend.

### 📖 What I'll learn
- Turning business rules into testable pure functions
- Generating human-readable explanations from numbers
- Calling a REST email API with `requests`
- Handling external failures gracefully
- Managing secrets for a third-party service

### 🛠 Features to build
- **Must (about 2 hours):** `recommendation_service` implementing R9 (US-30), Recommendations page with Critical, Soon, and Hold groups, explanation text, dashboard "Top 5 critical" widget.
- **Should:** email alert on new alert (US-22), "Send low-stock summary now" button (US-23), group by supplier and "Copy order list" (US-31), Hold advice (US-33).
- **Stretch:** none.

### 📝 Step-by-step implementation plan
1. Write pure functions in `recommendation_service.py`: `calculate_demand`, `days_of_cover`, `needs_reorder`, `priority`, `suggested_quantity`, `is_hold`, `build_explanation`. They take plain numbers so they are easy to test.
2. Write `get_recommendations()` that gathers 28-day units per active product in one query, joins supplier lead time, applies the rules, and returns a sorted list (Critical first, then lowest days of cover).
3. Build the Recommendations page with three sections (Critical, Soon, Hold), each row showing product, stock, days of cover, supplier, lead time, suggested quantity, and the explanation text.
4. Add the dashboard widget showing the top 5 Critical items with a link to the full page.
5. (Should) Add a supplier grouping toggle and a **Copy order list** button that copies plain text such as `Sharma Traders: Basmati Rice 5 kg x 40`.
6. Create a free Resend account, create an API key, and add `RESEND_API_KEY`, `ALERT_FROM_EMAIL`, and `ALERT_TO_EMAIL` to `.env` and Render (guided). Check Resend's current free-plan rules and test-sender limits before relying on them.
7. Write `email_service.py`: `send_email(subject, html, text)` using `requests` with a short timeout. Return a status. Never raise to callers.
8. Hook email into `alert_service` when a new alert is created. Record `email_status` and `email_sent_at`. Skip safely if keys are missing (status SKIPPED).
9. Add **Send low-stock summary now** on the Alerts page. It sends one email listing all open alerts and flashes the result.
10. Write tests (mock the HTTP call), commit, push, redeploy, and test an email end to end.

### 📂 Files and folders to create or modify
`app/services/{recommendation_service,email_service,alert_service}.py`, `app/blueprints/recommendations/{__init__,routes}.py`, `app/blueprints/alerts/routes.py` (extend), `app/templates/recommendations/index.html`, `app/templates/emails/{alert,summary}.html`, `app/templates/dashboard/index.html` (widget), `app/static/js/recommendations.js`, `tests/{test_recommendation_service,test_email_service,test_alert_email}.py`

### 🔗 APIs, libraries, services, or tools to integrate
Resend REST API (free plan), `requests`.

### 🧪 Testing tasks
- Rule tests with fixed numbers, including the exact example from the PRD (stock 18, demand 6 per day, lead time 3 gives a Critical recommendation with a computed quantity).
- Edge cases: zero demand, zero stock, demand present but stock high (Hold), minimum level breach with low demand.
- Email: success marks SENT, a failed call marks FAILED and does not break the sale, missing keys mark SKIPPED.
- Manual: sell a product below its minimum level and confirm both the in-app alert and the email arrive.

### 🐞 Common issues and debugging tips
- Email never arrives: check the Resend dashboard logs, the spam folder, and whether the sender or recipient is allowed on the free test setup.
- 401 from Resend: the API key is wrong or missing in the environment.
- Slow sale save: email must have a short timeout and failures must not block. Consider sending after the database commit.
- Recommendations look odd: print the intermediate numbers (demand, cover, lead time) while debugging.
- Division by zero: handle zero demand before computing cover.

### ✅ End-of-day checklist
- [ ] Recommendations page shows Critical, Soon, and Hold with explanations
- [ ] Rule tests pass including edge cases
- [ ] Email alert received for a real low-stock event
- [ ] Summary email button works
- [ ] Pushed and redeployed with Resend variables set on Render

### 📸 Expected project state and screenshots to capture
Recommendations page, a single recommendation explanation, dashboard widget, received email (alert and summary), Resend dashboard showing delivery.

### ➡️ Handoff notes for Day 9
- The rules engine returns `daily_demand` per product through one function that Day 9's forecast can optionally replace.
- Feature freeze begins after Day 9.
- List any Should items still open (supplier grouping, summary email, sales CSV import).

---

# DAY 9: ML Forecast (Gated), Polish, and Responsive Pass

### 🎯 Objective
Attempt the small ML demand forecast only if the gate passes, then spend the rest of the day polishing the entire product. Feature freeze at the end of today.

### 📖 What I'll learn
- Backtesting a forecast against a baseline
- Using scikit-learn for a tiny, honest model
- Falling back safely when ML does not help
- UX polish: empty states, loading states, error pages, responsive design

### 🛠 Features to build
- **Gate:** start ML only if Days 3 to 8 checklists are complete and the live app works. **Time cap: 90 minutes.**
- **Could (US-32):** per-product regression forecast, used only if it beats the baseline in a backtest, with the method shown in the UI.
- **Must:** polish and responsive pass (US-34, US-36).
- **Should:** sales CSV import (US-18) if still open, any leftover Day 4 to 8 Should items.

### 📝 Step-by-step implementation plan
1. Evaluate the gate honestly. If it fails, skip ML and move all time to polish and leftover Should items.
2. If the gate passes, add NumPy and scikit-learn and check the build still fits on the Render free instance.
3. Write `forecast_service.py`: build daily unit series per product for the last 90 days, features are day-of-week one-hot plus a time index, train a small regression, predict the next 7 days.
4. Backtest by training on all but the last 14 days and compare mean absolute error with the 28-day-average baseline.
5. Expose `forecast_demand(product)` returning demand per day and the method (`ML` or `RULES`). In `recommendation_service`, use it only when the method is `ML`.
6. Show a small badge on each recommendation: "Forecast: ML-assisted" or "Based on recent average".
7. Stop at 90 minutes regardless of result. Log what happened.
8. Polish pass: consistent page titles and headers, empty states with next-step buttons, button loading states to prevent double submits, flash message styling, confirm dialogs on destructive actions, favicon, tidy tables.
9. Responsive pass at 375px, 768px, and 1280px widths on every screen. Fix overflow and tap target sizes.
10. Friendly 404 and 500 pages (moved here from Day 3 in v1.1), and form error styling.
11. (Should) Finish sales CSV import with the same all-or-nothing validation.
12. Run the full test suite, commit, push, redeploy, and announce **feature freeze**.

### 📂 Files and folders to create or modify
`app/services/{forecast_service,recommendation_service,import_service}.py`, `requirements.txt`, `app/templates/*` (polish), `app/static/css/app.css`, `app/static/js/*` (loading states), `data/sample_sales.csv`, `tests/{test_forecast_service,test_import_sales}.py`

### 🔗 APIs, libraries, services, or tools to integrate
NumPy, scikit-learn (stretch only).

### 🧪 Testing tasks
- Forecast on a synthetic series with a clear weekly pattern beats the baseline. On a flat or random series it falls back to RULES.
- Forecast failure (too little history, exception) falls back to RULES with no error shown to the user.
- Full manual walkthrough on a phone-width window and a laptop-width window.
- Regression: run the whole test suite.

### 🐞 Common issues and debugging tips
- Render build is slow or runs out of memory: remove ML from the deployed build and keep rules only, and log it as a future-scope item.
- Forecast worse than baseline: this is a valid outcome, so ship with fallback and explain it honestly in the README.
- Training on every page load is slow: compute only for products on the recommendations page and cache the results briefly in memory.
- Horizontal scrolling on mobile: wrap wide tables in `table-responsive`.
- Buttons submit twice: disable the button on submit.

### ✅ End-of-day checklist
- [ ] ML either shipped with fallback and honest labels or formally skipped and documented
- [ ] Every screen verified at three widths
- [ ] Empty, error, and loading states exist
- [ ] Open Should items finished or consciously cut
- [ ] Full test suite passes, redeployed, feature freeze declared

### 📸 Expected project state and screenshots to capture
Recommendation rows with the method badge, before and after polish of one screen, phone-width screenshots of dashboard, new sale, and recommendations, test output.

### ➡️ Handoff notes for Day 10
- Feature freeze is active. Day 10 contains only testing, fixes, documentation, and release.
- Record exactly what shipped, what was cut, and any known bugs.


---

# DAY 10: Testing, Hardening, Release, and Demo

### 🎯 Objective
Ship StockSense v1.0: full regression testing, bug fixing (no new features), final deployment with clean demo data, complete documentation, demo script, pitch deck update, and a tagged GitHub release.

### 📖 What I'll learn
- Writing and running a structured manual test plan
- Final production deployment checks (secrets, debug off, clean data)
- Writing a README that sells and explains a project
- Preparing and rehearsing a product demo
- Tagging a release on GitHub

### 🛠 Features to build
No new features.
- **Must:** full test run, bug fixes, clean prod reset and reseed, README, demo script, release tag, final screenshots.
- **Should:** pitch deck refresh with real screenshots, short demo video script.
- **Stretch:** none.

### 📝 Step-by-step implementation plan
1. Run `pytest -q` locally and fix failures.
2. Walk through the **manual test script** on the live site (below) using a laptop and a phone-width window. Log every bug in the project log.
3. Fix only bugs that break a Must story or look broken. Defer cosmetic items to "known issues".
4. Security sweep: confirm `DEBUG` is off in production, secrets exist only as Render environment variables, signed-out access redirects to login, CSRF is on all forms, no real keys are in Git history.
5. Reset the prod demo data cleanly: `flask seed-demo --reset` (guided), then run `flask verify-ledger`.
6. Verify demo mode shows demo credentials on the login page.
7. Write the README: what it is, screenshots, live link, demo credentials, features, tech stack, architecture diagram (Mermaid), how to run locally, how to run tests, design decisions, known limitations, future scope, and a cold-start note.
8. Write `docs/DEMO-SCRIPT.md`: a 5-minute walkthrough (log in, dashboard, record a sale, watch the alert and email, insights, recommendations with explanations).
9. Update the pitch deck with real screenshots and the final feature list.
10. Rehearse the demo twice, including opening the link two minutes early to wake the free host.
11. Commit, push, create a GitHub **Release** tagged `v1.0.0` with release notes.
12. Update `PROJECT-LOG.md` and write the final LinkedIn post.

### 📂 Files and folders to create or modify
`README.md`, `docs/DEMO-SCRIPT.md`, `docs/PROJECT-LOG.md`, `docs/screenshots/*`, bug-fix changes across `app/`, any missing tests in `tests/`

### 🔗 APIs, libraries, services, or tools to integrate
GitHub Releases, Render dashboard (logs and environment), Resend dashboard (delivery check).

### 🧪 Testing tasks (manual test script)
1. Log in with wrong then correct credentials. Log out.
2. Add a product with opening stock. Edit it. Archive and restore it.
3. Add a category and supplier. Try to delete one in use.
4. Stock in, then adjust with a reason. Check movement history.
5. Record a 5-item sale. Try an over-stock sale. Void a sale. Check stock restored.
6. Reduce a product below its minimum level. Confirm in-app alert and email.
7. Open dashboard, toggle 7 and 30 days, check KPIs against a sale you just made.
8. Check Insights tabs and dead stock.
9. Check Recommendations (explanations, grouping, copy order list).
10. Import a valid and an invalid CSV.
11. Verify the ledger command reports zero issues.
12. Repeat the key flows at 375px width.

### 🐞 Common issues and debugging tips
- Demo data gets messy after testing: reseed with `--reset`.
- Live site slow at demo time: open it 2 minutes early.
- Email missing in the demo: have a backup screenshot of a delivered email.
- Last-minute change breaks deploy: roll back to the last green commit and redeploy from it.
- Do not add features today, however tempting. Write them in Future Scope.

### ✅ End-of-day checklist
- [ ] Tests pass and manual script completed
- [ ] Prod reset, seeded, and ledger verified
- [ ] README, demo script, and screenshots committed
- [ ] `v1.0.0` release published
- [ ] Pitch deck updated
- [ ] Project log finalized and LinkedIn post published

### 📸 Expected project state and screenshots to capture
Final live dashboard, recommendations, alert email, GitHub release page, passing test output, README on GitHub.

### ➡️ Handoff notes for Maintenance (after Day 10)
- Known issues list, future scope list, how to redeploy, how to reseed, how to rotate the Resend key and `SECRET_KEY`.

---

# APPENDIX A: Traceability (user stories to days)

| Stories | Built on |
|---|---|
| US-01, US-02, US-34 (base), US-36 (base) | Day 3 |
| US-03, US-04, US-05, US-06, US-07, US-08, US-35 | Day 4 |
| US-09 to US-16 | Day 5 |
| US-17, US-19, US-20, US-21 | Day 6 |
| US-24 to US-29 | Day 7 |
| US-22, US-23, US-30, US-31, US-33 | Day 8 |
| US-32, US-18, US-34 and US-36 polish | Day 9 |
| Hardening, release | Day 10 |

# APPENDIX B: Known Risks to Watch

1. **Day 4 is the heaviest early day** (deployment plus catalog). If deployment overruns, move archive and restore to Day 9.
2. **Day 6 carries the demo-data seeder**, which is easy to underestimate. Use bulk inserts and a fixed random seed.
3. **Day 9 combines a gated ML stretch and polish.** The 90-minute cap and the freeze are non-negotiable.
4. **Free-tier behavior** (cold starts, scale-to-zero database, email limits) should be re-checked when you set each service up, since provider limits can change.


---

# CHANGELOG

## v1.1 (Day 3 start)
- Day 2 design documents completed: `ARCHITECTURE.md`, `SCHEMA.md`, `API.md`, `UI-WIREFRAMES.md`, `PROJECT-STRUCTURE.md`. These now define the schema, the 40 routes, the screens, and the folder layout.
- **Day 3 now includes the Day 2 repository setup** (tools, GitHub repo, clone, folder skeleton, docs, first commit).
- Custom 404 and 500 pages moved from Day 3 to Day 9.
- Schema refinements: required `products.category_id`, `alerts.email_error`, unique (`sale_id`, `product_id`) on `sale_items`, ledger sign and adjustment CHECKs, `sales.bill_no` assigned right after first insert.
- API: 40 routes finalized (logout, archive, delete, void, stock-in, adjust are all POST).
- Added `app/services/errors.py` for `DomainError`.
- Neon account is created on Day 3 and Render account on Day 4, only when needed.
