# StockSense: Route and API Design

Version 1.0 (Day 2 design). No implementation yet. StockSense is server-rendered, so most "endpoints" are page routes that return HTML or redirect. Only three endpoints return JSON.

## 1. Conventions

| Topic | Rule |
|---|---|
| Authentication | **Every route requires a signed-in owner** except `GET/POST /login`, `GET /healthz`, and static files. Signed-out requests redirect to `/login?next=...` (HTML) or return `401` (JSON). |
| CSRF | Every `POST` requires a CSRF token. Forms include a hidden field. JSON POSTs would send `X-CSRFToken`. Missing or bad token returns `400`. |
| Methods | `GET` reads. `POST` changes data. Logout, archive, delete, and void are `POST` (never `GET`). |
| Success (HTML) | Redirect to a sensible page with a green flash message (Post/Redirect/Get). |
| Validation failure (HTML) | Re-render the same form with `400`-style error messages next to fields and the user's input kept. |
| Domain error (HTML) | A `DomainError` from a service (for example not enough stock) becomes a red flash message and the form re-renders. |
| Pagination | Query `page` (default 1), 15 rows per page. |
| Dates | Query dates are `YYYY-MM-DD` in IST. |
| JSON errors | `{ "error": { "code": "VALIDATION_ERROR", "message": "..." } }` with the right HTTP status. |
| Common error cases | `404` unknown id (friendly page), `400` validation or CSRF, `401` signed out (JSON), `500` unexpected (friendly page, error logged). |

CLI commands (not HTTP): `flask create-owner`, `flask seed-demo [--reset]`, `flask verify-ledger`.

## 2. Auth and System

| Route | Purpose | Request | Response | Validation | Auth | Error cases |
|---|---|---|---|---|---|---|
| `GET /login` | Show login form (demo credentials banner when `DEMO_MODE=true`) | none | HTML | none | Public | none |
| `POST /login` | Sign in | form: `email`, `password`, optional `remember` | Redirect to `next` or `/dashboard` | email format, password present | Public | Wrong credentials: re-render with "Invalid email or password" (no hint which) |
| `POST /logout` | Sign out | CSRF only | Redirect to `/login` | none | Required | Signed out: redirect to login |
| `GET /healthz` | Uptime check, does not touch the database | none | `200` text `ok` | none | Public | none |
| `GET /` | Convenience redirect | none | Redirect to `/dashboard` | none | Required | none |

## 3. Dashboard

| Route | Purpose | Request | Response | Validation | Auth | Error cases |
|---|---|---|---|---|---|---|
| `GET /dashboard` | KPIs, charts, alerts widget, top recommendations widget | none | HTML (KPI values computed server-side, charts load via JSON) | none | Required | Database error: 500 page |

## 4. Categories and Suppliers (`/lists`)

| Route | Purpose | Request | Response | Validation | Auth | Error cases |
|---|---|---|---|---|---|---|
| `GET /lists` | Show categories and suppliers with add forms | none | HTML | none | Required | none |
| `POST /lists/categories` | Add a category | form: `name` | Redirect to `/lists` | required, max 80, unique (case-insensitive) | Required | Duplicate name |
| `POST /lists/categories/<id>/rename` | Rename | form: `name` | Redirect | same as above | Required | 404, duplicate |
| `POST /lists/categories/<id>/delete` | Delete unused category | CSRF | Redirect | must have zero products | Required | 404, "in use by N products" |
| `POST /lists/suppliers` | Add a supplier | form: `name`, `phone?`, `email?`, `lead_time_days` | Redirect | name required and unique, email format if given, lead time integer 0 to 60 | Required | Duplicate name |
| `POST /lists/suppliers/<id>/edit` | Edit a supplier | same fields | Redirect | same | Required | 404, duplicate |
| `POST /lists/suppliers/<id>/delete` | Delete unused supplier | CSRF | Redirect | must have zero products | Required | 404, "in use by N products" |

## 5. Products

| Route | Purpose | Request | Response | Validation | Auth | Error cases |
|---|---|---|---|---|---|---|
| `GET /products` | List, search, filter, sort | query: `q`, `category`, `supplier`, `status` (`ok`, `low`, `out`), `active` (`1` default or `0`), `sort` (`name`, `stock`, `price`), `page` | HTML table with badges and pagination | `page` positive integer, unknown filter values ignored | Required | none |
| `GET /products/new` | Add form | none | HTML | none | Required | none |
| `POST /products/new` | Create product (and OPENING movement) | form: `sku`, `name`, `category_id`, `supplier_id?`, `cost_price`, `selling_price`, `opening_stock`, `min_stock` | Redirect to product detail | sku required, max 40, unique, uppercased. Prices decimal 0 or more (2 places). Stocks integers 0 or more. Category must exist. Warn (not block) if selling below cost | Required | Duplicate SKU, invalid number, missing category |
| `GET /products/<id>` | Detail, stock actions, movement history | query: `page` for history | HTML | none | Required | 404 |
| `GET /products/<id>/edit` | Edit form | none | HTML | none | Required | 404 |
| `POST /products/<id>/edit` | Update details (not SKU, not stock) | form: `name`, `category_id`, `supplier_id?`, `cost_price`, `selling_price`, `min_stock` | Redirect to detail | same rules as create | Required | 404, invalid number |
| `POST /products/<id>/archive` | Archive | CSRF | Redirect to list | none | Required | 404, already archived |
| `POST /products/<id>/restore` | Restore | CSRF | Redirect to detail | none | Required | 404, already active |
| `POST /products/<id>/stock-in` | Record stock received | form: `quantity`, `note?` | Redirect to detail | quantity integer above 0, note max 255 | Required | 404, archived product, invalid quantity |
| `POST /products/<id>/adjust` | Correct stock | form: `direction` (`add` or `remove`), `quantity`, `reason`, `note?` | Redirect to detail | quantity integer above 0, reason in allowed list, result must not go below 0 | Required | 404, "only N in stock", missing reason |

## 6. Sales

| Route | Purpose | Request | Response | Validation | Auth | Error cases |
|---|---|---|---|---|---|---|
| `GET /sales/new` | New sale screen | none | HTML | none | Required | none |
| `POST /sales/new` | Save a mini bill | form: repeated `product_id[]` and `quantity[]` (server recomputes prices from the database) | Redirect to `/sales/<id>` | at least 1 line, quantities integers above 0, products exist and are active, duplicate products merged, each line within stock | Required | "Only 3 of Basmati Rice 5 kg in stock" (nothing saved), empty bill |
| `GET /sales` | History | query: `from`, `to`, `status` (`completed`, `voided`, or all), `page` | HTML | `from` not after `to`, valid dates | Required | invalid date range: message and defaults |
| `GET /sales/<id>` | Detail with items, revenue, cost, profit | none | HTML | none | Required | 404 |
| `POST /sales/<id>/void` | Void a sale | form: `reason` | Redirect to detail | reason required, max 255, sale must be COMPLETED | Required | 404, already voided |

## 7. Alerts

| Route | Purpose | Request | Response | Validation | Auth | Error cases |
|---|---|---|---|---|---|---|
| `GET /alerts` | Open and Resolved tabs | query: `tab` (`open` default, `resolved`), `page` | HTML | none | Required | none |
| `POST /alerts/send-summary` | Email a summary of all open alerts | CSRF | Redirect to `/alerts` with result flash | at least one open alert | Required | No open alerts ("nothing to send"), email not configured (SKIPPED message), provider error (FAILED message) |

The navbar badge count comes from a context processor (no endpoint).

## 8. Insights and Recommendations

| Route | Purpose | Request | Response | Validation | Auth | Error cases |
|---|---|---|---|---|---|---|
| `GET /insights` | Fast, Steady, Slow movers and dead stock | query: `tab` (`fast`, `steady`, `slow`) | HTML | unknown tab falls back to `fast` | Required | none |
| `GET /recommendations` | Critical, Soon, and Hold lists with explanations | query: `group` (`priority` default or `supplier`) | HTML | unknown value falls back to `priority` | Required | Forecast failure falls back to rules silently |

## 9. CSV Import

| Route | Purpose | Request | Response | Validation | Auth | Error cases |
|---|---|---|---|---|---|---|
| `GET /import` | Import page with both upload forms and template links | none | HTML | none | Required | none |
| `GET /import/template/products.csv` | Download template | none | CSV file | none | Required | none |
| `GET /import/template/sales.csv` | Download template | none | CSV file | none | Required | none |
| `POST /import/products` | Import products | multipart: `file` | HTML result page: success count, or table of errors (row, column, message) | `.csv`, max 1 MB, max 2,000 rows, header must match, whole file validated first, all or nothing | Required | Wrong header, bad number, duplicate SKU in file or database, too large |
| `POST /import/sales` | Import sales (Should) | multipart: `file` | Same style of result page | same limits. `date` is `YYYY-MM-DD`, SKU must exist, quantities above 0, stock must cover rows processed in date order | Required | Unknown SKU, insufficient stock, bad date |

## 10. JSON Endpoints

All three are `GET`, require a signed-in session, and return `401` JSON when signed out.

### `GET /api/products/search?q=<text>`
- **Purpose:** live product lookup on the New Sale screen.
- **Validation:** `q` at least 1 character, trimmed, max 50.
- **Response `200`:**
```json
{ "results": [
  { "id": 12, "sku": "RICE-5KG", "name": "Basmati Rice 5 kg",
    "selling_price": "485.00", "current_stock": 18 }
] }
```
- Up to 10 active products matching name or SKU. Empty `q` returns an empty list.
- **Errors:** `400` if `q` is longer than 50.

### `GET /api/analytics/revenue-profit?days=7|30`
- **Purpose:** feed the dashboard line chart.
- **Validation:** `days` must be `7` or `30` (default 30).
- **Response `200`:**
```json
{ "days": 30,
  "points": [
    { "date": "2026-09-10", "revenue": "12450.00", "profit": "3120.00" }
  ] }
```
- One point per day, zero-filled, oldest first. Completed sales only.
- **Errors:** `400` for any other `days` value.

### `GET /api/analytics/top-products?days=30&limit=5`
- **Purpose:** feed the top sellers bar chart.
- **Validation:** `days` 7 or 30 (default 30), `limit` 1 to 10 (default 5).
- **Response `200`:**
```json
{ "days": 30,
  "products": [
    { "id": 12, "name": "Basmati Rice 5 kg", "units": 140, "revenue": "67900.00" }
  ] }
```
- **Errors:** `400` for out-of-range values.

## 11. Route Count and Coverage

| Group | Routes |
|---|---|
| Auth and system | 5 |
| Dashboard | 1 |
| Lists | 7 |
| Products | 10 |
| Sales | 5 |
| Alerts | 2 |
| Insights and recommendations | 2 |
| Import | 5 |
| JSON | 3 |
| **Total** | **40** |

Every route is used by at least one screen in `UI-WIREFRAMES.md`, and every Must user story has at least one route.
